"""Ownership and liveness for the `tee-*` scratch directories TEE creates.

A52's purge lane found these by NAME and deleted them, on the stated grounds
that "these belong to processes that have exited". Nothing established that.
The long-lived producers - the blender, fusion, godot and freecad adapters and
the asset library - hold their `mkdtemp` directory open for the whole life of a
running server, so a name match says nothing about whether anyone is using it.
Measured 2026-09-13: a confirmed purge run from the test suite deleted a live
review export, its log and a build in progress.

So a directory is only reclaimable when TEE can PROVE it owns it and that the
owner is gone. The three states are deliberately asymmetric:

    active       a marker we wrote, and its process is still running
    reclaimable  a marker we wrote, and its process is gone
    unverified   anything else - no marker, unreadable, malformed, or a
                 shape we do not recognise

`unverified` is never a deletion candidate. That leaves legacy directories
unreclaimed forever, which is the correct trade: their existence is not
permission to delete them, and a wrong deletion is unrecoverable while a
leftover directory costs disk.

PID reuse is why the marker records the owner's START TIME as well as its pid.
A recycled pid has a different start time, so it reads as `unverified` (we
cannot prove the owner is gone) rather than `reclaimable`.
"""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

MARKER = ".tee-workdir.json"
SCHEMA = "tee-workdir-v1"

ACTIVE = "active"
RECLAIMABLE = "reclaimable"
UNVERIFIED = "unverified"


def _proc_start(pid: int) -> str:
    """A stable per-process token that changes when a pid is recycled.

    Empty string means "cannot tell", which callers must treat as ambiguous
    and therefore not reclaimable.
    """
    try:  # Linux: field 22 of /proc/<pid>/stat is starttime in clock ticks
        with open(f"/proc/{pid}/stat", "rb") as fh:
            return fh.read().rsplit(b")", 1)[1].split()[19].decode()
    except (OSError, IndexError):
        pass
    try:  # macOS/BSD
        out = subprocess.run(
            ["ps", "-o", "lstart=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _alive(pid: int) -> bool | None:
    """True alive, False provably gone, **None cannot tell**.

    The third value is the whole point. An earlier version returned a bool and
    folded "cannot tell" into "alive", which reads safe but is not: the caller
    then had no way to distinguish a proven exit from a failed probe, and a
    failed probe must never license a deletion.

    `OverflowError` is why this is not just `except OSError`. A marker naming
    10**100 makes `os.kill` raise it, and it is NOT an OSError - so one
    malformed marker used to abort discovery for every directory in the call.
    """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False  # the only proof of exit we accept
    except PermissionError:
        return True  # exists, owned by someone else
    except (OverflowError, ValueError):
        return None  # unrepresentable pid: cannot tell, so do not guess
    except OSError:
        return None  # cannot tell
    return True


def claim(path: str | Path) -> Path:
    """Record this process as the owner of `path`. Best effort by design:
    a workdir that cannot be marked simply stays `unverified` forever, which
    is safe. Never let bookkeeping break the lane that needed the directory.
    """
    target = Path(path)
    pid = os.getpid()
    started = _proc_start(pid)
    if not started:
        # No identity means no provable ownership. Writing the marker anyway
        # would create a record that later reads as "owner gone" the moment the
        # pid disappears, which is TEE manufacturing its own fail-open. Leave
        # the directory unmarked: unverified forever is the safe end.
        return target
    with contextlib.suppress(OSError):
        (target / MARKER).write_text(
            json.dumps(
                {
                    "schema": SCHEMA,
                    "pid": pid,
                    "started": started,
                    "argv0": os.path.basename(sys.argv[0]) if sys.argv else "",
                }
            )
        )
    return target


def state_of(path: str | Path) -> dict[str, Any]:
    """`{state, reason, pid?}` for one candidate directory. Fails closed.

    ORDER MATTERS, and getting it wrong is how the first version fell over: it
    returned `reclaimable` as soon as the pid was gone, BEFORE it had validated
    the rest of the marker. A record with no `started`, an empty one, or an
    object where a string belongs therefore licensed a deletion. The marker is
    now validated COMPLETELY before any reclaimable return - a dead pid is a
    necessary condition, never a sufficient one.
    """
    target = Path(path)
    marker = target / MARKER

    # A symlinked marker is not evidence about THIS directory: it is evidence
    # about wherever it points, which an attacker or an accident chooses. The
    # containment check in purge validates the directory, not the marker.
    try:
        if marker.is_symlink() or not marker.is_file():
            if marker.is_symlink():
                return {"state": UNVERIFIED, "reason": "ownership marker is a symlink"}
            return {"state": UNVERIFIED, "reason": "no TEE ownership marker"}
    except OSError:
        return {"state": UNVERIFIED, "reason": "ownership marker unreadable"}

    try:
        raw = json.loads(marker.read_text())
    except (OSError, ValueError):
        return {"state": UNVERIFIED, "reason": "ownership marker unreadable"}
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA:
        return {"state": UNVERIFIED, "reason": "ownership marker not recognised"}

    # `type(...) is int` rather than isinstance: bool is a subclass of int, and
    # `pid: true` would otherwise probe pid 1.
    pid = raw.get("pid")
    if type(pid) is not int or pid <= 0:
        return {"state": UNVERIFIED, "reason": "ownership marker names no usable pid"}

    # The recorded identity must be complete BEFORE liveness is consulted.
    started = raw.get("started")
    if not isinstance(started, str) or not started.strip():
        return {
            "state": UNVERIFIED,
            "reason": "ownership marker records no process identity",
            "pid": pid,
        }

    alive = _alive(pid)
    if alive is None:
        return {
            "state": UNVERIFIED,
            "reason": f"pid {pid} could not be probed; exit is not established",
            "pid": pid,
        }
    if not alive:
        return {"state": RECLAIMABLE, "reason": f"owner pid {pid} is gone", "pid": pid}

    # The pid exists. Only a matching start time proves it is still OUR owner
    # and not a recycled number.
    current = _proc_start(pid)
    if not current:
        return {
            "state": UNVERIFIED,
            "reason": f"pid {pid} exists and its identity cannot be confirmed",
            "pid": pid,
        }
    if current == started:
        return {"state": ACTIVE, "reason": f"owner pid {pid} is running", "pid": pid}
    return {
        "state": UNVERIFIED,
        "reason": f"pid {pid} was recycled; the original owner cannot be proven gone",
        "pid": pid,
    }
