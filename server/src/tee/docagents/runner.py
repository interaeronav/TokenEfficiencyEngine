"""Bounded subprocess ownership for documentation agents.

The caller owns policy, provider selection and staging. This is a process-group
lifecycle, not an OS sandbox: a worker can invoke commands available to its user.
Only private log paths and compact completion metadata leave this module.
"""

from __future__ import annotations

import math
import os
import selectors
import signal
import stat
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO

if TYPE_CHECKING:
    from .backends import BackendPlan

MAX_LOG_BYTES = 1024 * 1024
MAX_TIMEOUT_S = 900
READ_BYTES = 64 * 1024
POLL_S = 0.025
TERMINATE_GRACE_S = 0.2


def _private_log(path: Path) -> BinaryIO:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    return os.fdopen(os.open(path, flags, 0o600), "wb", buffering=0)


def _signal_group(proc: subprocess.Popen[bytes], sig: int) -> None:
    try:
        os.killpg(proc.pid, sig)
    except ProcessLookupError:
        pass
    except PermissionError as exc:
        # Darwin returns EPERM, rather than ESRCH, for a group whose remaining
        # members are zombies. Reap the owned leader before classifying this.
        try:
            proc.wait(timeout=TERMINATE_GRACE_S)
        except subprocess.TimeoutExpired:
            raise exc from None


class Worker:
    """One cancellable run. Cancellation stays set, including before spawn.

    The runner reaps its direct children and terminates their process groups on
    every exit path, including success. Descendants that deliberately leave the
    group require OS isolation, which this runner does not claim to provide.
    """

    def __init__(self) -> None:
        self._cancelled = threading.Event()
        self._proc_lock = threading.Lock()
        self._run_lock = threading.Lock()
        self._proc: subprocess.Popen[bytes] | None = None

    def cancel(self) -> None:
        self._cancelled.set()
        with self._proc_lock:
            if self._proc is not None:
                _signal_group(self._proc, signal.SIGTERM)

    def run(self, plan: BackendPlan, run_dir: Path, timeout_s: int = 300) -> dict[str, Any]:
        """Run setup commands, then validate the final command's own output."""
        started = time.monotonic()
        result: dict[str, Any] = {
            "ok": False,
            "backend": plan.backend,
            "model": plan.model,
            "paid": plan.paid,
            "exit_code": None,
            "wall_s": 0.0,
            "log_path": str(run_dir / "worker.log"),
            "reason": "worker_busy",
            "usage": None,
        }
        if not self._run_lock.acquire(blocking=False):
            return result
        try:
            if self._cancelled.is_set():
                result["reason"] = "cancelled"
            elif (
                isinstance(timeout_s, bool)
                or not isinstance(timeout_s, (int, float))
                or not math.isfinite(timeout_s)
                or timeout_s <= 0
            ):
                result["reason"] = "invalid_timeout"
            elif not plan.commands or any(not command for command in plan.commands):
                result["reason"] = "empty_command"
            else:
                deadline = started + min(timeout_s, MAX_TIMEOUT_S)
                self._run_commands(plan, run_dir, deadline, result)
        except (OSError, ValueError, subprocess.SubprocessError):
            # Exception text can contain argv, credentials or model output.
            result.update(ok=False, reason="worker_io_error", usage=None)
        finally:
            # A cancellation received while completion was being parsed wins.
            with self._proc_lock:
                if self._cancelled.is_set():
                    result.update(ok=False, reason="cancelled", usage=None)
                result["wall_s"] = round(time.monotonic() - started, 3)
            self._run_lock.release()
        return result

    def _run_commands(
        self, plan: BackendPlan, run_dir: Path, deadline: float, result: dict[str, Any]
    ) -> None:
        from . import backends

        run_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not stat.S_ISDIR(run_dir.lstat().st_mode):
            raise ValueError("run directory must be a directory")
        run_dir.chmod(0o700)
        final_path = run_dir / "final.log"
        with _private_log(run_dir / "worker.log") as log, _private_log(final_path) as final_log:
            written = 0
            for index, command in enumerate(plan.commands):
                is_final = index == len(plan.commands) - 1
                with tempfile.TemporaryFile(mode="w+b", dir=run_dir) as input_file:
                    if is_final and plan.stdin is not None:
                        input_file.write(plan.stdin.encode("utf-8"))
                        input_file.seek(0)
                    reason, exit_code, written = self._command(
                        command,
                        plan,
                        input_file,
                        log,
                        final_log if is_final else None,
                        written,
                        deadline,
                    )
                result["exit_code"] = exit_code
                if reason is not None:
                    result["reason"] = reason
                    return
                if exit_code != 0:
                    result["reason"] = "worker_failed" if is_final else "setup_failed"
                    return
            # Unbuffered writes make completion visible before reading. Setup
            # output never supplies a final Cline run_result event.
            outcome = backends.final_success(final_path, result["exit_code"], backend=plan.backend)
            if time.monotonic() >= deadline:
                result["reason"] = "timeout"
                return
            if not isinstance(outcome, dict) or not isinstance(outcome.get("ok"), bool):
                result["reason"] = "invalid_completion"
                return
            result.update(
                ok=outcome["ok"],
                reason=outcome.get("reason", "completed" if outcome["ok"] else "incomplete"),
                usage=outcome.get("usage"),
            )

    def _command(
        self,
        command: list[str],
        plan: BackendPlan,
        input_file: BinaryIO,
        log: BinaryIO,
        final_log: BinaryIO | None,
        written: int,
        deadline: float,
    ) -> tuple[str | None, int | None, int]:
        proc = None
        reason = None
        stopped = False
        pipe_input = final_log is not None and plan.stdin is not None
        try:
            with self._proc_lock:
                if self._cancelled.is_set():
                    return "cancelled", None, written
                if time.monotonic() >= deadline:
                    return "timeout", None, written
                proc = subprocess.Popen(
                    command,
                    cwd=plan.cwd,
                    env=plan.env,  # Complete child environment, never merged with the host.
                    stdin=subprocess.PIPE if pipe_input else input_file,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=False,
                    start_new_session=True,
                    close_fds=True,
                )
                self._proc = proc
                if self._cancelled.is_set():
                    _signal_group(proc, signal.SIGTERM)
            assert proc.stdout is not None
            os.set_blocking(proc.stdout.fileno(), False)
            with selectors.DefaultSelector() as selector:
                selector.register(proc.stdout, selectors.EVENT_READ, "output")
                # Cline checks that stdin is a pipe. Feed it from the owned file
                # in bounded, nonblocking chunks alongside output reads: neither
                # a full pipe nor a worker ignoring stdin can block cancellation.
                pending_input = b""
                if proc.stdin is not None:
                    os.set_blocking(proc.stdin.fileno(), False)
                    selector.register(proc.stdin, selectors.EVENT_WRITE, "input")
                parent_finished = False
                while selector.get_map() or not parent_finished:
                    if self._cancelled.is_set():
                        reason = "cancelled"
                        break
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        reason = "timeout"
                        break
                    if not parent_finished and proc.poll() is not None:
                        parent_finished = True
                        # A successful shell/script can leave descendants holding
                        # stdout open. Terminate those before waiting for EOF.
                        self._stop_owned(proc)
                        stopped = True
                    for key, _ in selector.select(min(POLL_S, remaining)):
                        if key.data == "input":
                            if not pending_input:
                                pending_input = input_file.read(READ_BYTES)
                            if pending_input:
                                try:
                                    consumed = os.write(key.fd, pending_input)
                                except BlockingIOError:
                                    continue
                                except BrokenPipeError:
                                    pending_input = b""
                                else:
                                    pending_input = pending_input[consumed:]
                                    continue
                            selector.unregister(key.fileobj)
                            key.fileobj.close()
                            continue
                        try:
                            chunk = os.read(key.fd, READ_BYTES)
                        except BlockingIOError:
                            continue
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        available = MAX_LOG_BYTES - written
                        kept = chunk[:available]
                        if kept:
                            log.write(kept)
                            if final_log is not None:
                                final_log.write(kept)
                            written += len(kept)
                        if len(chunk) > available:
                            reason = "output_limit"
                            break
                    if reason:
                        break
        finally:
            if proc is not None:
                if not stopped:
                    self._stop_owned(proc)
                if proc.stdout is not None:
                    proc.stdout.close()
                if proc.stdin is not None:
                    proc.stdin.close()
                with self._proc_lock:
                    if self._proc is proc:
                        self._proc = None
        return reason, proc.returncode, written

    def _stop_owned(self, proc: subprocess.Popen[bytes]) -> None:
        """Kill the group even when the leader exited; always reap the leader."""
        with self._proc_lock:
            _signal_group(proc, signal.SIGTERM)
        end = time.monotonic() + TERMINATE_GRACE_S
        while time.monotonic() < end:
            try:
                os.killpg(proc.pid, 0)
            except ProcessLookupError:
                break
            except PermissionError as exc:
                # The zero-signal probe has the same Darwin zombie race as a
                # real signal. poll() may still lag that transition: bounded
                # wait reaps the child and preserves timeout/cancel outcomes.
                try:
                    proc.wait(timeout=TERMINATE_GRACE_S)
                except subprocess.TimeoutExpired:
                    raise exc from None
                break
            time.sleep(POLL_S)
        with self._proc_lock:
            _signal_group(proc, signal.SIGKILL)
            proc.wait()
            if self._proc is proc:
                self._proc = None
