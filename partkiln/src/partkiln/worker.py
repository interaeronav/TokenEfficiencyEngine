"""`python -m partkiln.worker`: the persistent kernel process behind `SidecarKernel`.

One `LocalKernel` over one `Document`, driven by NDJSON on stdin/stdout for
the life of the TEE server (A66 D2). It exists because of one number: the
OCP import costs 26 s COLD and 0.29 s warm (P0a), and the interpreter that
can pay it is not the one TEE runs in - the Claude Desktop extension venv is
Python 3.13 with no OCP and is wiped on every upgrade, while the sidecar venv
under `~/TEE/.tee/sidecars/partkiln` survives both. So the kernel lives here,
warm, and TEE talks to it down a pipe at ~1 ms a round trip.

The wire, in full:

    -> {"id": 1, "method": "apply", "params": {"commands": [...]}}
    <- {"id": 1, "result": {...}, "meta": {"rss_mb": 251.3, "wall_ms": 4.2}}
    <- {"id": 2, "error": {"code": "pk_bad_op", "message": "...", "fix": "..."}, "meta": {...}}

The first line out is `{"event": "ready", ...}`; OCP is NOT imported before
it unless `--warm` is passed, so a spawn is ready in the time it takes to
import the pure-Python core, and the 26 s land in the `warm` method, which
the adapter runs as a job (Law 17).

stdout is the protocol and nothing else: every dispatch runs with fd 1
swapped onto a temp file (the `fleet/_cad_worker.py` pattern), so native
OCCT chatter - or a stray `print` - lands there and is forwarded to stderr,
never into a reply. Between dispatches only this loop runs, which is why a
per-dispatch swap is enough. Nothing here imports `tee`, on purpose: the
parent invokes this module by name from any interpreter that has partkiln.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import tempfile
import time
from typing import Any

_MODULE_STARTED = time.perf_counter()

from partkiln import __version__  # noqa: E402 - the clock starts before the imports it times
from partkiln.client import (  # noqa: E402
    LocalKernel,
    occt_version,
    ocp_loaded,
    register_method,
    rss_mb,
)
from partkiln.document import CommandError  # noqa: E402

PROTOCOL = 1
_CHATTER_CAP = 4000  # bytes of forwarded native chatter per dispatch


def _json_default(value: Any) -> Any:
    """numpy scalars, paths, sets and tuples become plain JSON; nothing else does."""
    item = getattr(value, "item", None)
    if callable(item):
        return item()
    if isinstance(value, set | frozenset | tuple):
        return list(value)
    if isinstance(value, os.PathLike):
        return os.fspath(value)
    raise TypeError(f"{type(value).__name__} is not JSON-able")


def _encode(message: dict[str, Any]) -> bytes:
    return json.dumps(message, default=_json_default, separators=(",", ":")).encode() + b"\n"


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        view = view[written:]


def _error_payload(exc: BaseException) -> dict[str, Any]:
    """`{code, message, fix}`: a `CommandError`'s own fields, or `pk_internal`
    for anything else - one short line, never a traceback (hard rule 6)."""
    if isinstance(exc, CommandError):
        message = getattr(exc, "message", None) or str(exc)
        return {
            "code": getattr(exc, "code", "pk_op_failed"),
            "message": str(message)[:2000],
            "fix": str(getattr(exc, "fix", "") or ""),
        }
    return {
        "code": "pk_internal",
        "message": f"{type(exc).__name__}: {exc}"[:400],
        "fix": "The document is unchanged (a failed command restores itself); report this "
        "with the request that caused it.",
    }


class Worker:
    """The loop: read a line, dispatch under the fd swap, write one line back."""

    def __init__(self, kernel: LocalKernel) -> None:
        self.kernel = kernel
        # Lives as long as the process; the OS reclaims it with the fd.
        self._chatter = tempfile.TemporaryFile(mode="w+b")  # noqa: SIM115
        self._stop = False

    def dispatch(self, method: str, params: dict[str, Any]) -> Any:
        """Run one method with fd 1 pointed at the chatter file.

        `sys.stdout.flush()` before the swap-back pushes any Python-buffered
        `print` into the chatter file too; the restore is unconditional so a
        refusal inside the kernel can never leave stdout redirected.
        """
        saved = os.dup(1)
        try:
            os.dup2(self._chatter.fileno(), 1)
            try:
                return self.kernel.call(method, params)
            finally:
                sys.stdout.flush()
                os.dup2(saved, 1)
        finally:
            os.close(saved)
            self._forward_chatter(method)

    def _forward_chatter(self, method: str) -> None:
        """What landed on the swapped fd goes to stderr, capped, then the file is reset."""
        try:
            size = os.fstat(self._chatter.fileno()).st_size
            if size:
                self._chatter.seek(0)
                chatter = self._chatter.read(_CHATTER_CAP)
                self._chatter.seek(0)
                self._chatter.truncate(0)
                sys.stderr.write(
                    f"[partkiln.worker] {method}: {size} B on stdout, swallowed:\n"
                    + chatter.decode("utf-8", "replace")
                    + ("\n" if not chatter.endswith(b"\n") else "")
                )
                sys.stderr.flush()
        except OSError:
            pass

    def serve(self, stdin: Any, out_fd: int = 1) -> int:
        """Until EOF, `shutdown`, or a signal. Blank lines are the only thing skipped."""
        while not self._stop:
            line = stdin.readline()
            if not line:
                return 0  # EOF: the parent is gone or done
            if not line.strip():
                continue
            self._handle(line, out_fd)
        return 0

    def _handle(self, line: bytes, out_fd: int) -> None:
        started = time.perf_counter()
        ident: Any = None
        reply: dict[str, Any]
        try:
            request = json.loads(line)
        except ValueError as exc:
            reply = {
                "id": None,
                "error": {
                    "code": "pk_bad_request",
                    "message": f"not a JSON line: {str(exc)[:120]}",
                    "fix": 'send one JSON object per line: {"id", "method", "params"}',
                },
            }
        else:
            if not isinstance(request, dict):
                reply = {
                    "id": None,
                    "error": {
                        "code": "pk_bad_request",
                        "message": f"a request is an object, not {type(request).__name__}",
                        "fix": 'send {"id", "method", "params"}',
                    },
                }
            else:
                ident = request.get("id")
                reply = self._dispatch_request(ident, request)
        reply["meta"] = {
            "rss_mb": rss_mb(),
            "wall_ms": round((time.perf_counter() - started) * 1000, 2),
        }
        try:
            payload = _encode(reply)
        except (TypeError, ValueError) as exc:
            payload = _encode(
                {
                    "id": ident,
                    "error": {
                        "code": "pk_internal",
                        "message": f"the result of the request is not JSON-able: {exc}"[:300],
                        "fix": "report this with the request that caused it",
                    },
                    "meta": reply["meta"],
                }
            )
        _write_all(out_fd, payload)

    def _dispatch_request(self, ident: Any, request: dict[str, Any]) -> dict[str, Any]:
        method = request.get("method")
        params = request.get("params")
        if not isinstance(method, str) or not method:
            return {
                "id": ident,
                "error": {
                    "code": "pk_bad_request",
                    "message": "the request names no method",
                    "fix": 'send {"id", "method", "params"}',
                },
            }
        if params is None:
            params = {}
        if not isinstance(params, dict):
            return {
                "id": ident,
                "error": {
                    "code": "pk_bad_request",
                    "message": f"{method}: params must be an object",
                    "fix": 'send "params": {...}',
                },
            }
        try:
            result = self.dispatch(method, params)
        except Exception as exc:  # an exception is an error reply, never a crash
            return {"id": ident, "error": _error_payload(exc)}
        if method == "shutdown":
            self._stop = True
        return {"id": ident, "result": result}


# -- test hooks: hidden, so no refusal advertises them ----------------------------------


@register_method("echo_stdout", hidden=True)
def _m_echo_stdout(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    """Write to fd 1 the way native code does, AND through Python's buffer,
    inside the swap. The test asserts neither reaches the protocol."""
    text = str(params.get("text", "chatter"))
    os.write(1, f"native:{text}\n".encode())
    print(f"python:{text}")  # deliberately unflushed: the swap-back must flush it
    return {"echoed": text}


@register_method("sleep", hidden=True)
def _m_sleep(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    """Block for the deadline test: the wire must kill us, not wait."""
    seconds = float(params.get("seconds", 5.0))
    time.sleep(seconds)
    return {"slept": seconds}


@register_method("boom", hidden=True)
def _m_boom(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    """An unhandled exception inside a dispatch."""
    raise RuntimeError(str(params.get("text", "boom")))


# -- entry --------------------------------------------------------------------------------


def _ready_line(kernel: LocalKernel, import_s: float) -> dict[str, Any]:
    return {
        "event": "ready",
        "protocol": PROTOCOL,
        "pid": os.getpid(),
        "python": ".".join(str(part) for part in sys.version_info[:3]),
        "partkiln": __version__,
        "ocp": kernel.info()["ocp"],
        "warm": ocp_loaded(),
        "occt": occt_version(),
        "import_s": round(import_s, 3),
        "rss_mb": rss_mb(),
    }


def _install_signal_handlers() -> None:
    def _exit_clean(signum: int, frame: Any) -> None:
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _exit_clean)
    signal.signal(signal.SIGINT, _exit_clean)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m partkiln.worker", description=__doc__)
    parser.add_argument(
        "--warm",
        action="store_true",
        help="import OCP BEFORE the ready line (26 s cold / 0.3 s warm) instead of on 'warm'",
    )
    args = parser.parse_args(argv)
    _install_signal_handlers()
    worker = Worker(LocalKernel(mode="sidecar"))
    try:
        if args.warm:
            worker.dispatch("warm", {})
        _write_all(1, _encode(_ready_line(worker.kernel, time.perf_counter() - _MODULE_STARTED)))
        return worker.serve(sys.stdin.buffer)
    except (BrokenPipeError, KeyboardInterrupt):
        return 0
    except SystemExit as exc:
        return int(exc.code or 0)


if __name__ == "__main__":
    raise SystemExit(main())
