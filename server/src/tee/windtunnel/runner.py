"""One solver process, owned end to end: started in its own session, its
output streamed to a log file, a small `progress.json` refreshed every two
seconds for `wt_status` to read, killed by process group on cancel, and
findable again after a server restart through `run.json`.

Why a process group: `mpirun` and the OpenFOAM entry script both fork, so a
plain `terminate()` on the parent would strand the actual solver. Why a
progress FILE: the model polls through `tee_job`/`wt_status`, and a
few-dozen-token JSON file is the cheapest thing to read; the solver log
itself (measured 736 bytes per iteration for simpleFoam) never reaches the
model. Why `run.json`: the job manager forgets jobs across restarts but the
child does not die with the server, so the pid, the argv and the case path
are written down before the first byte of output - `wt_status` can then say
`orphan` and `wt_case stop` can kill it after checking that the pid still
runs that argv.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROGRESS_EVERY_S = 2.0
TAIL_BYTES = 64 * 1024
TERMINATE_GRACE_S = 5.0

ProgressFn = Callable[[Path, str], dict[str, Any]]


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=1, default=str))
    os.replace(tmp, path)


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def tail_text(path: Path, nbytes: int = TAIL_BYTES) -> str:
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - nbytes))
            return fh.read().decode("utf-8", "replace")
    except OSError:
        return ""


@dataclass
class RunSpec:
    run_id: str
    case_id: str
    engine: str
    argv: list[str]
    cwd: Path
    log_name: str
    timeout_s: float = 600.0
    env: dict[str, str] = field(default_factory=dict)
    label: str = ""


class SolverRun:
    """Start with `start()`, block with `wait()` (or both with `run()`),
    stop with `terminate()`. The reader thread keeps `progress.json` fresh."""

    def __init__(self, spec: RunSpec, progress_fn: ProgressFn | None = None) -> None:
        self.spec = spec
        self.progress_fn = progress_fn
        self.proc: subprocess.Popen[bytes] | None = None
        self.started_at = 0.0
        self.finished_at = 0.0
        self.state = "queued"
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._log: Any = None
        self.cancelled = False
        self.stop_failed = False  # a stop was attempted and the process survived
        self.stop_recovered = False  # ...and a later stop confirmed the exit

    # -- paths ---------------------------------------------------------------
    @property
    def run_dir(self) -> Path:
        return self.spec.cwd

    @property
    def log_path(self) -> Path:
        return self.spec.cwd / self.spec.log_name

    @property
    def progress_path(self) -> Path:
        return self.spec.cwd / "progress.json"

    @property
    def run_json_path(self) -> Path:
        return self.spec.cwd / "run.json"

    # -- lifecycle -----------------------------------------------------------
    def start(self) -> None:
        self.spec.cwd.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ)
        env.update(self.spec.env)
        self._log = open(self.log_path, "wb")  # noqa: SIM115 - closed in _finish
        self.started_at = time.time()
        self.proc = subprocess.Popen(
            self.spec.argv,
            cwd=str(self.spec.cwd),
            stdout=self._log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            env=env,
            start_new_session=True,
        )
        self.state = "running"
        atomic_write_json(
            self.run_json_path,
            {
                "run_id": self.spec.run_id,
                "case_id": self.spec.case_id,
                "engine": self.spec.engine,
                "pid": self.proc.pid,
                "pgid": self.proc.pid,
                "argv": self.spec.argv,
                "cwd": str(self.spec.cwd),
                "log": self.spec.log_name,
                "started_at": self.started_at,
                "timeout_s": self.spec.timeout_s,
                "label": self.spec.label,
            },
        )
        self._write_progress()
        self._thread = threading.Thread(
            target=self._reader, name=f"wt-progress-{self.spec.run_id}", daemon=True
        )
        self._thread.start()

    def _reader(self) -> None:
        while not self._stop.wait(PROGRESS_EVERY_S):
            self._write_progress()

    def _write_progress(self, final: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {
            "run_id": self.spec.run_id,
            "case_id": self.spec.case_id,
            "engine": self.spec.engine,
            "state": self.state,
            "elapsed_s": round((self.finished_at or time.time()) - self.started_at, 1),
            "pid": self.proc.pid if self.proc else None,
        }
        if self.progress_fn is not None:
            try:
                payload.update(self.progress_fn(self.spec.cwd, tail_text(self.log_path)))
            except Exception as exc:  # a parse error must never kill the reader
                payload["progress_error"] = str(exc)[:200]
        if final:
            payload.update(final)
        atomic_write_json(self.progress_path, payload)

    def wait(self) -> int:
        assert self.proc is not None
        try:
            rc = self.proc.wait(timeout=self.spec.timeout_s)
            if self.cancelled:
                self.state = "cancelled"
            else:
                self.state = "done" if rc == 0 else "error"
        except subprocess.TimeoutExpired:
            self.terminate(reason="timeout")
            rc = self.proc.wait()
            self.state = "timeout"
        self._finish(rc)
        return rc

    def _finish(self, rc: int) -> None:
        self.finished_at = time.time()
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=PROGRESS_EVERY_S + 1)
        if self._log is not None:
            self._log.close()
        self._write_progress(
            {
                "rc": rc,
                "finished_at": self.finished_at,
                "wall_s": round(self.finished_at - self.started_at, 2),
            }
        )
        try:
            rj = read_json(self.run_json_path) or {}
            rj.update({"state": self.state, "rc": rc, "finished_at": self.finished_at})
            atomic_write_json(self.run_json_path, rj)
        except OSError:
            pass

    def run(self) -> dict[str, Any]:
        self.start()
        rc = self.wait()
        return {
            "rc": rc,
            "state": self.state,
            "wall_s": round(self.finished_at - self.started_at, 2),
            "log": str(self.log_path),
        }

    def terminate(self, reason: str = "cancelled") -> bool:
        """SIGTERM the whole process group, SIGKILL after the grace period.
        Returns True when the process is gone."""
        if self.proc is None or self.proc.poll() is not None:
            return True
        self.cancelled = reason == "cancelled"
        gone = kill_process_group(self.proc.pid)
        # Only a confirmed exit is a cancellation. The same false-completion
        # shape as kill_orphan's: this used to set `cancelled` whatever
        # `kill_process_group` returned, so a surviving solver reported a state
        # it had not reached.
        if gone:
            # A confirmed exit RETIRES an earlier failed attempt. Setting the
            # flag and never clearing it meant a successful retry still
            # reported stop_failed, in memory and through every merge that
            # carried it into the store.
            if self.stop_failed:
                self.stop_failed = False
                self.stop_recovered = True
            if reason == "cancelled":
                self.state = "cancelled"
        else:
            self.stop_failed = True
        return gone


def kill_process_group(pid: int, grace_s: float = TERMINATE_GRACE_S) -> bool:
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    deadline = time.time() + grace_s
    while time.time() < deadline:
        if not pid_alive(pid):
            return True
        time.sleep(0.05)
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        return True
    except PermissionError:
        # macOS answers EPERM (not ESRCH) when every member of the group is
        # already a zombie - measured 2026-09-06 on Darwin 25.6; treat it as
        # the aliveness check's problem, not a crash.
        return not pid_alive(pid)
    deadline = time.time() + 2.0
    while time.time() < deadline:
        if not pid_alive(pid):
            return True
        time.sleep(0.05)
    return not pid_alive(pid)


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    # a zombie answers kill(0) but is not running
    try:
        with open(f"/proc/{pid}/stat") as fh:
            state = fh.read().rsplit(")", 1)[1].split()[0]
            return state != "Z"
    except OSError:
        pass
    # no /proc (macOS): ps prints a stat starting with Z for a zombie
    try:
        out = subprocess.run(
            ["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, timeout=5
        )
        state = out.stdout.strip()
        return bool(state) and not state.startswith("Z")
    except (OSError, subprocess.SubprocessError):
        return True


def pid_cmdline(pid: int) -> str:
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as fh:
            return fh.read().replace(b"\0", b" ").decode("utf-8", "replace")
    except OSError:
        try:
            out = subprocess.run(
                ["ps", "-o", "command=", "-p", str(pid)], capture_output=True, text=True, timeout=5
            )
            return out.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""


# ---------------------------------------------------------------------------
# Orphans: a solver whose server is gone
# ---------------------------------------------------------------------------


def pid_cwd(pid: int) -> Path | None:
    """The working directory of a RUNNING process, or None if it cannot be read.

    Live evidence, unlike the saved argv. The lane launches every solver with
    `cwd=run_dir`, so this identifies the run even for the argv shapes that do
    not carry `-case` - and None means "cannot tell", which callers must treat
    as no evidence rather than as a match.
    """
    try:  # Linux
        return Path(os.readlink(f"/proc/{pid}/cwd"))
    except OSError:
        pass
    try:  # macOS/BSD: lsof is the only portable route to another process's cwd
        out = subprocess.run(
            ["lsof", "-a", "-d", "cwd", "-p", str(pid), "-Fn"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    for line in out.stdout.splitlines():
        if line.startswith("n"):
            return Path(line[1:])
    return None


def _norm(path: str | Path) -> str:
    """A comparable absolute path, with symlinks resolved.

    `realpath`, not just `normpath`: on macOS `/var` IS `/private/var` and
    `/tmp` IS `/private/tmp`, so `lsof` reports a cwd of
    `/private/var/folders/.../run_001` for a directory the lane knows as
    `/var/folders/.../run_001`. Comparing the unresolved forms made every
    exact-cwd match fail here - which would have silently disabled orphan
    stopping on the machine this ships to. It also collapses `..`, so an
    argument like `<run>/../different-run` cannot masquerade as the run.
    """
    return os.path.realpath(os.path.abspath(os.path.expanduser(str(path))))


def _argv_macos(pid: int) -> list[str] | None:
    """Real, NUL-separated argv on macOS via `sysctl KERN_PROCARGS2`.

    Assuming macOS could only offer a flattened string is what left this lane
    unsafe: `ps -o args=` loses the argument boundaries the identity decision
    needs. The kernel keeps the real vector and reading it costs nothing but
    stdlib ctypes - no new dependency.

    Layout: 4-byte argc, the exec path, NUL padding, then argc arguments.
    """
    import ctypes
    import ctypes.util

    ctl_kern, kern_procargs2, kern_argmax = 1, 49, 8
    try:
        libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
        cap = ctypes.c_int(0)
        cap_size = ctypes.c_size_t(ctypes.sizeof(cap))
        mib2 = (ctypes.c_int * 2)(ctl_kern, kern_argmax)
        if libc.sysctl(mib2, 2, ctypes.byref(cap), ctypes.byref(cap_size), None, 0) != 0:
            return None
        buf = ctypes.create_string_buffer(cap.value)
        size = ctypes.c_size_t(cap.value)
        mib3 = (ctypes.c_int * 3)(ctl_kern, kern_procargs2, pid)
        if libc.sysctl(mib3, 3, buf, ctypes.byref(size), None, 0) != 0:
            return None
        raw = buf.raw[: size.value]
        if len(raw) < 4:
            return None
        argc = int.from_bytes(raw[:4], sys.byteorder)
        parts = raw[4:].split(b"\0")
        i = 1  # skip the exec path
        while i < len(parts) and parts[i] == b"":
            i += 1  # skip NUL padding
        return [q.decode("utf-8", "replace") for q in parts[i : i + argc]] or None
    except (OSError, ValueError, AttributeError):
        return None


def pid_argv(pid: int) -> list[str] | None:
    """The RUNNING process's argv as REAL TOKENS, or None if they cannot be had.

    Tokens are the whole point. A flattened command string cannot say where one
    argument ends, so `<run>/../different-run`, `<run> copy` and a path sitting
    inside a `python -c` source comment all looked like the run they are not -
    and each reached the kill. With real tokens every candidate is normalized
    and compared whole.

    None means "cannot tell", never "no match".
    """
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as fh:
            parts = [q.decode("utf-8", "replace") for q in fh.read().split(b"\0") if q]
        if parts:
            return parts
    except OSError:
        pass
    if sys.platform == "darwin":
        return _argv_macos(pid)
    return None


def _cmd_names_run(cmd: str, run_dir: Path) -> bool:
    """Does this command line name THIS run directory, at path boundaries?

    Plain `in` is what let `run_001` match its sibling `run_001-copy` and
    `run_100` match `run_1000` - both reached the termination call. A path only
    counts when the character after it ends the component: nothing, a
    separator (a supported file BENEATH the run, like `log.simpleFoam`), or
    whitespace. The character before must likewise start a token, so a longer
    path merely ending in ours does not count.
    """
    target = _norm(run_dir)
    start = 0
    while True:
        i = cmd.find(target, start)
        if i < 0:
            return False
        start = i + 1
        before = cmd[i - 1] if i else " "
        after = cmd[i + len(target) :]
        if before not in " \t=\"'":
            continue
        if after == "" or after[0] in " \t\"'" or after.startswith(os.sep):
            return True


def _argv_names_run(argv: list[str], run_dir: Path) -> bool:
    """Exact per-token comparison, where the OS gave us real tokens."""
    target = _norm(run_dir)
    for token in argv:
        if not token:
            continue
        # a bare path, or the value half of `--flag=/path`
        for candidate in (token, token.split("=", 1)[1] if "=" in token else ""):
            if not candidate:
                continue
            norm = _norm(candidate)
            if norm == target or norm.startswith(target + os.sep):
                return True
    return False


def orphan_check(run_dir: Path) -> dict[str, Any]:
    """What `run.json` says versus what the OS says.

    `alive` means the pid exists AND the RUNNING process is identifiably this
    run - never that a saved record says so. The previous version also accepted
    a match against `run.json`'s own argv, which names the run directory in
    every record ever written, so any live process occupying that pid passed
    identity and `kill_orphan` would hand it to `kill_process_group`. The
    docstring claimed "a reused pid would fail that check"; the fallback it sat
    next to defeated exactly that. Found by GPT-6, 2026-09-13.

    Two independent pieces of LIVE evidence, because the lane has two launch
    shapes: OpenFOAM passes `-case <run_dir>` so the run directory appears in
    the command line (through the wrapper and through `mpirun` alike), while
    every RunSpec also sets `cwd=run_dir`. Either proves identity. Neither
    readable means we cannot tell, and cannot-tell never authorises a signal.
    """
    rj = read_json(run_dir / "run.json")
    if not rj or "pid" not in rj:
        return {"known": False, "alive": False}
    try:
        pid = int(rj["pid"])
    except (TypeError, ValueError):
        return {"known": False, "alive": False, "identity": "run.json names no usable pid"}
    running = pid_alive(pid)
    argv = pid_argv(pid) if running else None
    cmd = pid_cmdline(pid) if running else ""
    cwd = pid_cwd(pid) if running else None
    # Component boundaries, not substrings. `run_001` used to match the sibling
    # `run_001-copy` and `run_100` matched `run_1000`, by cwd and by command
    # line alike, and both reached the kill.
    # Identity comes from REAL argv tokens or an exact cwd. The flattened
    # command string is reporting only: it cannot establish ownership, and
    # treating it as though it could is what authorised three wrong kills.
    by_cmd = bool(argv) and _argv_names_run(argv, run_dir)
    by_cwd = cwd is not None and _norm(cwd) == _norm(run_dir)
    evidence_readable = argv is not None or cwd is not None
    matches = by_cmd or by_cwd
    if not running:
        identity = "the pid is gone"
    elif matches:
        identity = (
            "live command line names this run" if by_cmd else "live working directory is this run"
        )
    elif not evidence_readable:
        identity = "the process exists but no live evidence could be read; identity unconfirmed"
    else:
        identity = "a live process holds this pid but is not this run"
    return {
        "known": True,
        "pid": pid,
        "alive": running and matches,
        "pid_reused": running and evidence_readable and not matches,
        "identity_unknown": running and not evidence_readable,
        "identity": identity,
        # Reporting only. Deliberately NOT consulted for identity: a flattened
        # command string has no argument boundaries, which is what let three
        # wrong processes look like this run.
        "observed_cmd": cmd[:200] if cmd else "",
        "state": rj.get("state", "running"),
        "started_at": rj.get("started_at"),
        "argv": rj.get("argv", [])[:6],
    }


def kill_orphan(run_dir: Path) -> dict[str, Any]:
    """Stop a verified orphan, and record only what actually happened.

    Two corrections, both found by GPT-6 on 2026-09-13:

    Identity is revalidated IMMEDIATELY before the signal. The first check
    decides whether to try at all; between the two the pid can be recycled, and
    a stale decision is not a licence to signal.

    A failed stop is no longer written as a completed cancellation. The previous
    version stamped `state: cancelled`, `finished_at` and
    `killed_as_orphan: true` whatever `kill_process_group` returned, so a solver
    that survived was recorded as cancelled - the run then LOOKED finished while
    it was still burning CPU, and `wt_status` believed the record.
    """
    info = orphan_check(run_dir)
    if not info.get("alive"):
        return {**info, "killed": False, "signalled": False}

    # Revalidate at the signal boundary, not from the decision above.
    now = orphan_check(run_dir)
    if not now.get("alive") or now.get("pid") != info.get("pid"):
        return {
            **now,
            "killed": False,
            "signalled": False,
            "why": "identity changed between the check and the signal; nothing was sent",
        }

    gone = kill_process_group(int(now["pid"]))
    rj = read_json(run_dir / "run.json") or {}
    if gone:
        rj.update({"state": "cancelled", "finished_at": time.time(), "killed_as_orphan": True})
        # A confirmed stop retires an earlier failed attempt on the same run.
        if rj.pop("stop_failed", None):
            rj["stop_recovered"] = True
    else:
        # An attempt, not an outcome. The process is still there.
        rj.update(
            {
                "state": "running",
                "stop_attempted_at": time.time(),
                "stop_failed": True,
                "killed_as_orphan": False,
            }
        )
    atomic_write_json(run_dir / "run.json", rj)
    prog = read_json(run_dir / "progress.json") or {}
    if gone:
        prog.update({"state": "cancelled"})
        if prog.pop("stop_failed", None):
            prog["stop_recovered"] = True
    else:
        prog.update({"state": "running", "stop_failed": True})
    atomic_write_json(run_dir / "progress.json", prog)
    return {**now, "killed": gone, "signalled": True}


# ---------------------------------------------------------------------------
# A registry of the runs this process owns (for cancel hooks)
# ---------------------------------------------------------------------------

RUNS: dict[str, SolverRun] = {}


def _key(case_id: str, run_id: str) -> str:
    return f"{case_id}/{run_id}"  # run ids restart at run_001 in every case


def register(run: SolverRun) -> None:
    RUNS[_key(run.spec.case_id, run.spec.run_id)] = run


def forget(case_id: str, run_id: str) -> None:
    RUNS.pop(_key(case_id, run_id), None)


def live_run_for_case(case_id: str) -> SolverRun | None:
    for run in RUNS.values():
        if run.spec.case_id == case_id and run.state == "running":
            return run
    return None
