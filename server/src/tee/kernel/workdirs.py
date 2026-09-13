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


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:  # exists, owned by someone else
        return True
    except OSError:
        return True  # cannot tell -> assume alive, fail closed
    return True


def claim(path: str | Path) -> Path:
    """Record this process as the owner of `path`. Best effort by design:
    a workdir that cannot be marked simply stays `unverified` forever, which
    is safe. Never let bookkeeping break the lane that needed the directory.
    """
    target = Path(path)
    try:
        pid = os.getpid()
        (target / MARKER).write_text(
            json.dumps(
                {
                    "schema": SCHEMA,
                    "pid": pid,
                    "started": _proc_start(pid),
                    "argv0": os.path.basename(sys.argv[0]) if sys.argv else "",
                }
            )
        )
    except OSError:
        pass
    return target


def state_of(path: str | Path) -> dict[str, Any]:
    """`{state, reason, pid?}` for one candidate directory. Fails closed."""
    target = Path(path)
    marker = target / MARKER
    try:
        raw = json.loads(marker.read_text())
    except FileNotFoundError:
        return {"state": UNVERIFIED, "reason": "no TEE ownership marker"}
    except (OSError, ValueError):
        return {"state": UNVERIFIED, "reason": "ownership marker unreadable"}
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA:
        return {"state": UNVERIFIED, "reason": "ownership marker not recognised"}
    pid = raw.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        return {"state": UNVERIFIED, "reason": "ownership marker names no pid"}
    if not _alive(pid):
        return {"state": RECLAIMABLE, "reason": f"owner pid {pid} is gone", "pid": pid}
    # The pid exists. Only a matching start time proves it is still OUR owner
    # and not a recycled number.
    recorded = raw.get("started") or ""
    current = _proc_start(pid)
    if recorded and current and recorded == current:
        return {"state": ACTIVE, "reason": f"owner pid {pid} is running", "pid": pid}
    if not recorded or not current:
        return {
            "state": UNVERIFIED,
            "reason": f"pid {pid} exists and its identity cannot be confirmed",
            "pid": pid,
        }
    return {
        "state": UNVERIFIED,
        "reason": f"pid {pid} was recycled; the original owner cannot be proven gone",
        "pid": pid,
    }
