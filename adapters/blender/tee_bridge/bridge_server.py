# SPDX-License-Identifier: GPL-3.0-or-later
"""TEE bridge socket server, runnable inside Blender.

Wire protocol (identical to the official Blender Lab MCP add-on, so the TEE
server drives either bridge unchanged):

    request:  {"type": "execute", "code": "<python>", "strict_json": bool} \\0
    response: {"status": "ok", "result": {...}} or
              {"status": "error", "message": "<traceback>"} \\0

Threading contract (docs/research/02 and 09 - the single most important
correctness constraint on the Blender side):

- GUI mode: socket I/O runs in ONE daemon thread that only parses frames and
  enqueues them; ONE persistent ``bpy.app.timers`` callback (registered once)
  drains the queue on the main thread, executes, and replies. No bpy call
  ever happens on a worker thread; never one timer per command.
- Background mode: ``run_blocking()`` runs the same I/O loop on the main
  thread and executes each frame inline; deferred work is not supported.
"""

from __future__ import annotations

import io
import json
import queue
import selectors
import socket
import threading
import traceback
from contextlib import redirect_stderr, redirect_stdout

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9876
_MAX_REQUEST_BYTES = 16 * 1024 * 1024
TIMER_INTERVAL = 0.05

# Weak guard, mirroring the official add-on's denylist. Explicitly NOT a
# sandbox (Blender documents VM isolation as the real mitigation).
_DENYLIST = ("wm.quit_blender", "wm.read_factory_settings", "sys.exit(")


def execute_frame(raw: bytes) -> bytes:
    """Parse one request frame, execute it, return the response frame."""
    try:
        request = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _encode({"status": "error", "message": "request frame is not valid JSON"})
    if request.get("type") != "execute":
        return _encode(
            {"status": "error", "message": "unsupported request type %r" % request.get("type")}
        )
    code = request.get("code")
    if not isinstance(code, str):
        return _encode({"status": "error", "message": "'code' must be a string"})
    strict_json = bool(request.get("strict_json", True))
    for banned in _DENYLIST:
        if banned in code:
            return _encode(
                {
                    "status": "error",
                    "message": "refused: %r is blocked by the TEE bridge guard" % banned,
                }
            )

    namespace: dict[str, object] = {"result": {}}
    stdout, stderr = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exec(code, namespace)  # noqa: S102 - the bridge's entire purpose
    except BaseException:
        response: dict[str, object] = {
            "status": "error",
            "message": traceback.format_exc(),
        }
        _attach_streams(response, stdout, stderr)
        return _encode(response)

    result = namespace.get("result")
    if not isinstance(result, dict):
        response = {
            "status": "error",
            "message": "the `result` variable must be a dict, not %s"
            % type(result).__name__,
        }
    elif strict_json:
        try:
            json.dumps(result)
            response = {"status": "ok", "result": result}
        except (TypeError, ValueError):
            response = {
                "status": "error",
                "message": "result is not JSON-serializable (strict_json=true)",
            }
    else:
        result = json.loads(json.dumps(result, default=repr))
        response = {"status": "ok", "result": result}
    _attach_streams(response, stdout, stderr)
    return _encode(response)


def _attach_streams(response: dict[str, object], stdout: io.StringIO, stderr: io.StringIO) -> None:
    if stdout.getvalue():
        response["stdout"] = stdout.getvalue()
    if stderr.getvalue():
        response["stderr"] = stderr.getvalue()


def _encode(response: dict[str, object]) -> bytes:
    return json.dumps(response).encode("utf-8") + b"\0"


class _IOLoop:
    """Selector-based socket loop: accepts clients, assembles null-delimited
    frames, hands (client, frame) pairs to a sink callable."""

    def __init__(self, host: str, port: int, sink):
        self.listener = socket.socket()
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((host, port))
        self.listener.listen(8)
        self.listener.setblocking(False)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.listener, selectors.EVENT_READ, None)
        self.buffers: dict[socket.socket, bytearray] = {}
        self.sink = sink
        self.stop_event = threading.Event()

    @property
    def port(self) -> int:
        return self.listener.getsockname()[1]

    def step(self, timeout: float) -> None:
        for key, _ in self.selector.select(timeout):
            sock = key.fileobj
            if sock is self.listener:
                try:
                    conn, _addr = self.listener.accept()
                except OSError:
                    continue
                conn.setblocking(False)
                self.selector.register(conn, selectors.EVENT_READ, None)
                self.buffers[conn] = bytearray()
                continue
            try:
                data = sock.recv(65536)
            except OSError:
                data = b""
            if not data:
                self._drop(sock)
                continue
            buf = self.buffers[sock]
            buf.extend(data)
            if len(buf) > _MAX_REQUEST_BYTES:
                self._drop(sock)
                continue
            while b"\0" in buf:
                frame, _, rest = bytes(buf).partition(b"\0")
                self.buffers[sock] = buf = bytearray(rest)
                self.sink(sock, frame)

    def run(self) -> None:
        while not self.stop_event.is_set():
            self.step(0.2)

    def _drop(self, sock: socket.socket) -> None:
        try:
            self.selector.unregister(sock)
        except (KeyError, ValueError):
            pass
        self.buffers.pop(sock, None)
        try:
            sock.close()
        except OSError:
            pass

    def close(self) -> None:
        self.stop_event.set()
        for sock in list(self.buffers):
            self._drop(sock)
        try:
            self.selector.unregister(self.listener)
        except (KeyError, ValueError):
            pass
        self.listener.close()
        self.selector.close()


def _send_response(sock: socket.socket, frame: bytes) -> None:
    try:
        sock.settimeout(10.0)
        sock.sendall(frame)
        sock.settimeout(0.0)
    except OSError:
        try:
            sock.close()
        except OSError:
            pass


# -- GUI mode: I/O thread + main-thread timer pump ---------------------------

_gui_state: dict[str, object] = {}


def start_gui(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> int:
    """Start the bridge inside a GUI Blender session. Returns the bound port."""
    import bpy

    if _gui_state:
        raise RuntimeError("TEE bridge already running")
    pending: queue.Queue = queue.Queue()
    try:
        loop = _IOLoop(host, port, lambda sock, frame: pending.put((sock, frame)))
    except OSError as exc:
        # EADDRINUSE is the common first-run failure on real machines:
        # a lingering Blender process, the official MCP add-on on the
        # same port, or an unrelated app. Fail with the fix, not a trace.
        raise RuntimeError(
            f"port {port} is already in use - another Blender instance, the "
            "official MCP add-on, or another app holds it. Quit other "
            "Blender processes, or change Port in the TEE Bridge add-on "
            "preferences (then start TEE with --blender-port "
            f"<new port>). [{exc}]"
        ) from exc
    thread = threading.Thread(target=loop.run, name="tee-bridge-io", daemon=True)

    def pump() -> float | None:
        if not _gui_state:
            return None  # unregistered
        try:
            while True:
                sock, frame = pending.get_nowait()
                _send_response(sock, execute_frame(frame))
        except queue.Empty:
            pass
        return TIMER_INTERVAL

    _gui_state.update({"loop": loop, "thread": thread, "pump": pump})
    thread.start()
    bpy.app.timers.register(pump, first_interval=TIMER_INTERVAL, persistent=True)
    return loop.port


def stop_gui() -> None:
    import bpy

    loop = _gui_state.pop("loop", None)
    pump = _gui_state.pop("pump", None)
    _gui_state.clear()
    if pump is not None and bpy.app.timers.is_registered(pump):
        bpy.app.timers.unregister(pump)
    if loop is not None:
        loop.close()


# -- background mode: everything on the main thread --------------------------


def run_blocking(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    """Serve forever on the main thread (for `blender --background`)."""
    loop = _IOLoop(host, port, lambda sock, frame: _send_response(sock, execute_frame(frame)))
    print("TEE bridge listening on %s:%d" % (host, loop.port), flush=True)
    try:
        loop.run()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
