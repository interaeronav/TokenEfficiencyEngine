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
        if reason == "cancelled":
            self.state = "cancelled"
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


def orphan_check(run_dir: Path) -> dict[str, Any]:
    """What `run.json` says versus what the OS says. `alive` means the pid
    exists AND its command line still names this run directory (a reused
    pid would fail that check, which is why it is made before any signal)."""
    rj = read_json(run_dir / "run.json")
    if not rj or "pid" not in rj:
        return {"known": False, "alive": False}
    pid = int(rj["pid"])
    alive = pid_alive(pid)
    cmd = pid_cmdline(pid) if alive else ""
    matches = bool(cmd) and (
        str(run_dir) in cmd or any(str(run_dir) in a for a in rj.get("argv", []))
    )
    return {
        "known": True,
        "pid": pid,
        "alive": alive and matches,
        "pid_reused": alive and not matches,
        "state": rj.get("state", "running"),
        "started_at": rj.get("started_at"),
        "argv": rj.get("argv", [])[:6],
    }


def kill_orphan(run_dir: Path) -> dict[str, Any]:
    info = orphan_check(run_dir)
    if not info.get("alive"):
        return {**info, "killed": False}
    gone = kill_process_group(int(info["pid"]))
    rj = read_json(run_dir / "run.json") or {}
    rj.update({"state": "cancelled", "finished_at": time.time(), "killed_as_orphan": True})
    atomic_write_json(run_dir / "run.json", rj)
    prog = read_json(run_dir / "progress.json") or {}
    prog.update({"state": "cancelled"})
    atomic_write_json(run_dir / "progress.json", prog)
    return {**info, "killed": gone}


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
