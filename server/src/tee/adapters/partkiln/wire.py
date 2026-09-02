"""`SidecarKernel`: partkiln's kernel in the interpreter that survives the wipe.

The production route for the mechanical CAD lane (A66 D2). The Claude Desktop
extension venv is Python 3.13 with no OCP and is rebuilt on every upgrade;
the sidecar venv under `~/TEE/.tee/sidecars/partkiln` is neither, and it
outlives `tee_purge` too. So the kernel runs there, as
`python -m partkiln.worker`, and this class is the other end of its pipe:
the same thirteen methods as `partkiln.client.LocalKernel`, each one
request/reply with a deadline.

Copied from `gateway/wire.py` (`StdioBackendWire`) on purpose: `Popen(bufsize=0)`
so `select()` and `os.read()` agree on readiness, newline-JSON, a 1 s
`select()` tick that notices a dead process between ticks, the non-JSON-line
skip, and `_dead()` closing the process before naming its exit code and
stderr log. What is new is the deadline's consequence: OCCT offers no
cancellation from Python (P0a: `Message_ProgressIndicator` has no
trampoline), so a request that overruns is answered by KILLING the worker;
the adapter then respawns it and replays the script (0.09-0.46 s per 100
cuts), which is why the timeout's fix says "rolled back".

Timing that shaped the defaults: the worker's ready line arrives before any
OCP import (~0.1 s after spawn); `warm` costs 0.29 s warm and 26 s cold
(P0a), so it gets its own deadline; a steady round trip is about a
millisecond. Imports nothing from partkiln: the wire must not care whether
the server's own interpreter has the kernel.
"""

from __future__ import annotations

import contextlib
import json
import os
import select
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

# `fleet/cad.py:206` discovery, one directory over: the venv that survives.
SIDECAR_PY = Path.home() / "TEE" / ".tee" / "sidecars" / "partkiln" / "bin" / "python"
WORKER_MODULE = "partkiln.worker"
# Kept textually identical to `partkiln.brep.INSTALL_LINE`, which this file
# cannot import.
INSTALL_LINE = (
    "uv venv --python 3.11 ~/TEE/.tee/sidecars/partkiln && "
    "uv pip install --python ~/TEE/.tee/sidecars/partkiln/bin/python -e <repo>/partkiln[brep]"
)
DEFAULT_TIMEOUT_S = 60.0  # `[partkiln] batch_timeout_s`, under kernel/script.py's MAX_SECONDS=120
READY_TIMEOUT_S = 30.0  # the ready line needs no OCP; 30 s is a stuck interpreter, not a slow one
WARM_TIMEOUT_S = 120.0  # 26 s cold measured; a cold run under load gets headroom, not a kill
SHUTDOWN_GRACE_S = 5.0


class SidecarKernel:
    """One worker process, one lock, one request in flight.

    `python` defaults to `SIDECAR_PY`; tests pass `sys.executable` to spawn
    the worker from their own venv (with `env={"PYTHONPATH": ...}` when
    partkiln is not installed there). `env` is MERGED over `os.environ`, not
    substituted for it, so a caller adding one variable keeps PATH and HOME.
    """

    def __init__(
        self,
        python: str | Path | None = None,
        *,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        stderr_path: Path | None = None,
        env: dict[str, str] | None = None,
        warm: bool = False,
    ) -> None:
        self.python = Path(python).expanduser() if python else SIDECAR_PY
        self.timeout_s = float(timeout_s)
        self.stderr_path = Path(stderr_path) if stderr_path is not None else None
        self.env = dict(env) if env else None
        self.warm_on_start = bool(warm)
        self.ready: dict[str, Any] = {}
        self.spawn_s: float | None = None
        self.proc: subprocess.Popen | None = None
        self._buffer = b""
        self._id = 0
        self._lock = threading.Lock()
        self._stderr_handle = None

    # -- lifecycle ---------------------------------------------------------------------

    def start(self) -> dict[str, Any]:
        """Spawn the worker and wait for its ready line; returns that line.

        Already alive: returns the stored ready line without respawning.
        """
        if not self.python.is_file():
            raise TeeError(
                "pk_kernel_absent",
                f"No partkiln sidecar interpreter at {self.python}.",
                fix=f"Create it once (it survives upgrades and tee_purge): {INSTALL_LINE}",
            )
        with self._lock:
            if self.alive():
                return dict(self.ready)
            stderr: Any = subprocess.DEVNULL
            if self.stderr_path is not None:
                self.stderr_path.parent.mkdir(parents=True, exist_ok=True)
                self._stderr_handle = open(self.stderr_path, "ab")  # noqa: SIM115 - closed in close()
                stderr = self._stderr_handle
            env = None if self.env is None else {**os.environ, **self.env}
            command = [str(self.python), "-m", WORKER_MODULE]
            if self.warm_on_start:
                command.append("--warm")
            started = time.monotonic()
            try:
                self.proc = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=stderr,
                    env=env,
                    bufsize=0,  # raw pipes: select() and os.read() agree on readiness
                )
            except (OSError, ValueError) as exc:
                self._close_stderr()
                raise TeeError(
                    "pk_worker_spawn_failed",
                    f"The partkiln worker failed to spawn from {self.python}: {exc}",
                    fix=f"Check the interpreter; recreate it with: {INSTALL_LINE}",
                ) from exc
            self._buffer = b""
            budget = READY_TIMEOUT_S + (WARM_TIMEOUT_S if self.warm_on_start else 0.0)
            deadline = started + budget
            while True:
                message = self._read_message(deadline, "start", budget)
                if message.get("event") == "ready":
                    break
            self.ready = message
            self.spawn_s = round(time.monotonic() - started, 4)
            return dict(message)

    def alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def close(self) -> None:
        """Stop the worker: EOF on its stdin (it exits 0), then SIGTERM, then SIGKILL."""
        self._close_stderr()
        proc, self.proc = self.proc, None
        self._buffer = b""
        if proc is None:
            return
        with contextlib.suppress(OSError):
            if proc.stdin is not None:
                proc.stdin.close()
        try:
            proc.terminate()
            proc.wait(timeout=SHUTDOWN_GRACE_S)
        except (OSError, subprocess.TimeoutExpired):
            with contextlib.suppress(OSError):
                proc.kill()
            with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                proc.wait(timeout=1.0)
        with contextlib.suppress(OSError):
            if proc.stdout is not None:
                proc.stdout.close()

    def restart(self) -> dict[str, Any]:
        """Kill and respawn. The adapter replays the script afterwards; this
        only hands back a fresh ready line."""
        self.close()
        return self.start()

    # -- the KernelClient method set ---------------------------------------------------

    def probe(self) -> bool:
        """Alive, without a round trip: a worker mid-`warm` must not stall a probe."""
        return self.alive()

    def info(self) -> dict[str, Any]:
        return dict(self.request("info", {}))

    def warm(self) -> dict[str, Any]:
        return dict(self.request("warm", {}, timeout_s=WARM_TIMEOUT_S))

    def apply(self, commands: list[dict[str, Any]]) -> dict[str, Any]:
        return dict(self.request("apply", {"commands": commands}))

    def entities(self) -> list[dict[str, Any]]:
        return list(self.request("entities", {}) or [])

    def detail(self, entity_id: str) -> dict[str, Any]:
        return dict(self.request("detail", {"id": entity_id}))

    def call(self, method: str, params: dict[str, Any]) -> Any:
        return self.request(method, dict(params or {}))

    def script(self) -> dict[str, Any]:
        return dict(self.request("script", {}))

    def fingerprint(self) -> str:
        return str(self.request("fingerprint", {}))

    def snapshot(self, label: str, dir: str | Path) -> dict[str, Any]:
        return dict(self.request("snapshot", {"label": label, "dir": str(dir)}))

    def restore(self, payload: dict[str, Any]) -> None:
        self.request("restore", {"payload": payload})

    def discard(self, payload: dict[str, Any]) -> None:
        self.request("discard", {"payload": payload})

    def shutdown(self) -> None:
        """Ask the worker to exit (it replies, then returns 0), then close."""
        if self.alive():
            with contextlib.suppress(TeeError):
                self.request("shutdown", {}, timeout_s=SHUTDOWN_GRACE_S)
            proc = self.proc
            if proc is not None:
                with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                    proc.wait(timeout=SHUTDOWN_GRACE_S)
        self.close()

    # -- plumbing -------------------------------------------------------------------------

    def request(
        self, method: str, params: dict[str, Any], *, timeout_s: float | None = None
    ) -> Any:
        """One request, one reply, under the lock and a deadline."""
        seconds = self.timeout_s if timeout_s is None else float(timeout_s)
        with self._lock:
            if self.proc is None:
                raise TeeError(
                    "pk_worker_down",
                    "The partkiln worker is not running.",
                    fix="start() it (the adapter does on first use), or restart() after a death.",
                )
            self._id += 1
            ident = self._id
            self._write({"id": ident, "method": method, "params": params}, method)
            deadline = time.monotonic() + seconds
            while True:
                message = self._read_message(deadline, method, seconds)
                if message.get("id") != ident:
                    continue  # an event (a late ready line) or a stray: skipped
                if "error" in message:
                    err = message.get("error") or {}
                    raise TeeError(
                        str(err.get("code") or "pk_op_failed"),
                        str(err.get("message") or f"the worker refused {method}"),
                        fix=str(err.get("fix") or "") or None,
                    )
                return message.get("result")

    def _write(self, message: dict[str, Any], during: str) -> None:
        if not self.alive() or self.proc is None or self.proc.stdin is None:
            raise self._dead(during)
        try:
            self.proc.stdin.write(json.dumps(message).encode() + b"\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise self._dead(during) from exc

    def _read_message(self, deadline: float, during: str, seconds: float) -> dict[str, Any]:
        while True:
            newline = self._buffer.find(b"\n")
            if newline >= 0:
                line, self._buffer = self._buffer[:newline], self._buffer[newline + 1 :]
                if not line.strip():
                    continue
                try:
                    parsed = json.loads(line)
                except json.JSONDecodeError:
                    continue  # a non-protocol line on stdout: data, skipped
                if isinstance(parsed, dict):
                    return parsed
                continue
            if self.proc is None or self.proc.stdout is None:
                raise self._dead(during)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._kill()
                raise self._timeout(during, seconds)
            ready, _, _ = select.select([self.proc.stdout], [], [], min(remaining, 1.0))
            if not ready:
                if not self.alive():
                    raise self._dead(during)
                continue
            chunk = os.read(self.proc.stdout.fileno(), 65536)
            if not chunk:
                raise self._dead(during)
            self._buffer += chunk

    def _timeout(self, during: str, seconds: float) -> TeeError:
        log = self.stderr_path or "not captured"
        if during == "start":
            return TeeError(
                "pk_worker_timeout",
                f"The partkiln worker printed no ready line within {seconds:.0f} s.",
                fix=f"Its stderr log is {log}; run `{self.python} -m {WORKER_MODULE}` by hand "
                "to see why.",
            )
        return TeeError(
            "pk_worker_timeout",
            f"The partkiln worker gave no answer to {during} within {seconds:.0f} s.",
            fix=f"the batch was killed after {seconds:.0f} s; it is rolled back by the kernel "
            "checkpoint; split it or pass job=true",
        )

    def _kill(self) -> None:
        """SIGKILL, because OCCT cannot be interrupted any other way."""
        proc = self.proc
        if proc is not None and proc.poll() is None:
            with contextlib.suppress(OSError):
                proc.kill()
            with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                proc.wait(timeout=2.0)
        self.close()

    def _dead(self, during: str) -> TeeError:
        proc = self.proc
        code = None
        if proc is not None:
            code = proc.poll()
            if code is None:
                with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                    code = proc.wait(timeout=1.0)
        log = self.stderr_path or "not captured"
        self.close()
        return TeeError(
            "pk_worker_dead",
            f"The partkiln worker died (exit {code}) during {during}.",
            fix=f"restart() respawns it and the adapter replays the script; its stderr log: {log}.",
        )

    def _close_stderr(self) -> None:
        if self._stderr_handle is not None:
            with contextlib.suppress(OSError):
                self._stderr_handle.close()
            self._stderr_handle = None


__all__ = [
    "DEFAULT_TIMEOUT_S",
    "INSTALL_LINE",
    "READY_TIMEOUT_S",
    "SIDECAR_PY",
    "WARM_TIMEOUT_S",
    "SidecarKernel",
]
