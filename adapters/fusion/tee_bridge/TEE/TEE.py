# SPDX-License-Identifier: MIT
"""TEE bridge add-in for Autodesk Fusion (A69).

A localhost socket that runs TEE's batches on Fusion's primary thread.

Wire protocol - identical framing to the Blender bridge, so `FusionWire` on
the server side is the Blender wire's shape: NUL-terminated JSON, one
request per connection.

    request:  {"type": "execute", "code": "<python>", "strict_json": bool} \\0
              {"type": "ping"} \\0
    response: {"status": "ok", "result": {...}} \\0
              {"status": "error", "message": "<traceback or reason>"} \\0
              (optional "stdout" / "stderr" keys on either)

The executed code communicates back by assigning a dict to a variable named
``result``; a dict named ``_tee`` persists across requests for the bridge's
life (the adapter keeps its short-id -> entityToken map there).

Threading contract (the one that matters in Fusion, doc 71 section 3 rows
1-3): the API may be touched ONLY from the primary thread. So the socket
loop runs in one daemon thread that never imports adsk beyond firing an
event; each request is parked in a task table and announced with
``Application.fireCustomEvent(EVENT_ID, task_id)``; Fusion services the
event on the primary thread when it is idle, where ``CustomEventHandler.
notify`` executes the frame and releases the waiting socket thread. A ping
takes the same hop on purpose: a bridge whose primary thread is held by a
modal dialog must look down, not up (the FreeCAD SI-B12 lesson).

Everything that is not adsk is plain Python at module level, so the
protocol and the hop are tested on any machine (tests/test_fusion_bridge.py)
and only the ``run``/``stop`` glue needs Fusion. This file is TEE's own and
MIT; the Blender bridge's selector loop is GPL and is not copied.

Not a sandbox: like the Blender bridge, this executes what it is sent, and
binds 127.0.0.1 only. The typed batches TEE compiles are the default path;
arbitrary code reaches it through ``fu_execute_python`` behind the
``exec-code`` capability.
"""

from __future__ import annotations

import io
import json
import os
import socket
import threading
import traceback
import uuid
from contextlib import redirect_stderr, redirect_stdout, suppress

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9881  # 9875 FreeCAD, 9876/9877 Blender, 9879 Godot
EVENT_ID = "tee.bridge.execute"
CALL_DEADLINE_S = 120.0
PING_DEADLINE_S = 5.0
_MAX_REQUEST_BYTES = 16 * 1024 * 1024
_ACCEPT_POLL_S = 0.5
_CLIENT_TIMEOUT_S = 30.0

# A weak guard against taking the host down, mirroring the Blender bridge's
# denylist. Explicitly NOT a sandbox.
_DENYLIST = ("sys.exit(", "os._exit(", "adsk.terminate(")

# The ping is answered by the primary thread from Fusion's own state; the
# names it reads are doc 71 section 3 rows 4 and 5 (plus DesignTypes).
PING_CODE = """\
import adsk.core, adsk.fusion
_app = adsk.core.Application.get()
_doc = _app.activeDocument
_design = adsk.fusion.Design.cast(_app.activeProduct)
_kind = None
if _design is not None:
    _kind = ("parametric" if _design.designType == adsk.fusion.DesignTypes.ParametricDesignType
             else "direct")
result = {
    "product": "Fusion",
    "version": str(_app.version),
    "document": _doc.name if _doc is not None else None,
    "design": _kind,
    "ids": len(_tee.get("ids", {})),
}
"""


# -- the frame: pure Python, runs on whatever thread calls it -----------------


def encode(response: dict) -> bytes:
    return json.dumps(response).encode("utf-8") + b"\0"


def _attach_streams(response: dict, stdout: io.StringIO, stderr: io.StringIO) -> None:
    if stdout.getvalue():
        response["stdout"] = stdout.getvalue()[-4000:]
    if stderr.getvalue():
        response["stderr"] = stderr.getvalue()[-4000:]


def execute_frame(raw: bytes, namespace: dict) -> bytes:
    """Parse one request frame, execute it, return the response frame.

    ``namespace`` is the bridge's persistent state: its ``_tee`` dict is
    handed to every execution; every other name is fresh per frame.
    """
    try:
        request = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return encode({"status": "error", "message": "request frame is not valid JSON"})
    if not isinstance(request, dict):
        return encode({"status": "error", "message": "request frame must be a JSON object"})
    kind = request.get("type")
    if kind == "ping":
        code, strict_json = PING_CODE, True
    elif kind == "execute":
        code = request.get("code")
        if not isinstance(code, str):
            return encode({"status": "error", "message": "'code' must be a string"})
        strict_json = bool(request.get("strict_json", True))
        for banned in _DENYLIST:
            if banned in code:
                return encode(
                    {
                        "status": "error",
                        "message": f"refused: {banned!r} is blocked by the TEE bridge guard",
                    }
                )
    else:
        return encode({"status": "error", "message": f"unsupported request type {kind!r}"})

    shared = namespace.setdefault("_tee", {})
    scope: dict = {"result": {}, "_tee": shared}
    stdout, stderr = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exec(code, scope)
    except BaseException:
        response: dict = {"status": "error", "message": traceback.format_exc()[-6000:]}
        _attach_streams(response, stdout, stderr)
        return encode(response)

    result = scope.get("result")
    if not isinstance(result, dict):
        response = {
            "status": "error",
            "message": f"the `result` variable must be a dict, not {type(result).__name__}",
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
        response = {"status": "ok", "result": json.loads(json.dumps(result, default=repr))}
    _attach_streams(response, stdout, stderr)
    return encode(response)


def frame_deadline(raw: bytes) -> float:
    """A ping must answer quickly or count as down; a batch may take a while."""
    try:
        if json.loads(raw.decode("utf-8")).get("type") == "ping":
            return PING_DEADLINE_S
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        pass
    return CALL_DEADLINE_S


# -- the hop: I/O thread parks a task, the primary thread runs it -------------


class _Task:
    __slots__ = ("done", "frame", "id", "reply")

    def __init__(self, frame: bytes):
        self.id = uuid.uuid4().hex
        self.frame = frame
        self.reply: bytes | None = None
        self.done = threading.Event()


class Marshaller:
    """Parks a frame, announces it with ``fire(task_id)``, waits for the
    primary thread to call ``run(task_id)``. ``fire`` is
    ``app.fireCustomEvent(EVENT_ID, task_id)`` in Fusion and a stub in tests."""

    def __init__(self, fire, *, namespace: dict | None = None):
        self._fire = fire
        self._tasks: dict[str, _Task] = {}
        self._lock = threading.Lock()
        self.namespace: dict = namespace if namespace is not None else {"_tee": {}}

    def submit(self, frame: bytes, deadline_s: float | None = None) -> bytes:
        deadline = frame_deadline(frame) if deadline_s is None else deadline_s
        task = _Task(frame)
        with self._lock:
            self._tasks[task.id] = task
        try:
            queued = self._fire(task.id)
        except Exception as exc:  # fireCustomEvent raising is a bridge fault, not a batch fault
            queued = False
            reason = f"{type(exc).__name__}: {exc}"
        else:
            reason = "fireCustomEvent returned false"
        if not queued:
            with self._lock:
                self._tasks.pop(task.id, None)
            return encode(
                {
                    "status": "error",
                    "message": f"could not queue the request on Fusion's primary thread ({reason})",
                }
            )
        if not task.done.wait(deadline):
            with self._lock:
                self._tasks.pop(task.id, None)
            return encode(
                {
                    "status": "error",
                    "message": "Fusion's primary thread did not service the request within "
                    f"{deadline:.0f} s - a modal dialog may be holding it; check the Fusion "
                    "window.",
                }
            )
        return task.reply or encode({"status": "error", "message": "empty reply"})

    def run(self, task_id: str) -> bool:
        """PRIMARY THREAD. Execute the parked frame and release its waiter."""
        with self._lock:
            task = self._tasks.pop(task_id, None)
        if task is None:
            return False  # timed out and withdrawn, or an unknown id
        try:
            task.reply = execute_frame(task.frame, self.namespace)
        finally:
            task.done.set()
        return True

    def pending(self) -> int:
        with self._lock:
            return len(self._tasks)


# -- the socket loop: one daemon thread, one request per connection ----------


class Listener:
    def __init__(self, marshaller: Marshaller, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.marshaller = marshaller
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen(8)
        self.sock.settimeout(_ACCEPT_POLL_S)
        self.host = host
        self.port = self.sock.getsockname()[1]
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._serve, name="tee-fusion-io", daemon=True)

    def start(self) -> None:
        self.thread.start()

    def _serve(self) -> None:
        while not self._stop.is_set():
            try:
                conn, _addr = self.sock.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            try:
                self._handle(conn)
            finally:
                with suppress(OSError):
                    conn.close()

    def _handle(self, conn: socket.socket) -> None:
        conn.settimeout(_CLIENT_TIMEOUT_S)
        buf = bytearray()
        try:
            while b"\0" not in buf:
                chunk = conn.recv(65536)
                if not chunk:
                    return
                buf.extend(chunk)
                if len(buf) > _MAX_REQUEST_BYTES:
                    conn.sendall(encode({"status": "error", "message": "request frame too large"}))
                    return
            frame = bytes(buf).partition(b"\0")[0]
            conn.sendall(self.marshaller.submit(frame))
        except OSError:
            return

    def close(self, timeout: float = 2.0) -> None:
        self._stop.set()
        with suppress(OSError):
            self.sock.close()
        if self.thread.is_alive() and self.thread is not threading.current_thread():
            self.thread.join(timeout)


# -- the Fusion side: run/stop, the custom event and its handler ---------------

_STATE: dict = {}


def _make_handler(core, marshaller: Marshaller, log=None):
    """A CustomEventHandler whose notify runs the parked task. Built inside
    a function because the base class lives in adsk.core."""

    class _Handler(core.CustomEventHandler):
        def __init__(self):
            super().__init__()

        def notify(self, args):
            try:
                marshaller.run(str(args.additionalInfo))
            except Exception:
                if log is not None:
                    log("TEE bridge: handler failed\n" + traceback.format_exc())

    return _Handler()


def configured_port() -> int:
    raw = os.environ.get("TEE_FUSION_PORT", "")
    try:
        port = int(raw) if raw else DEFAULT_PORT
    except ValueError:
        port = DEFAULT_PORT
    return port if 1024 <= port <= 65535 else DEFAULT_PORT


def start(core, *, host: str = DEFAULT_HOST, port: int | None = None, log=None) -> dict:
    """Register the event, add the handler, start the listener. ``core`` is
    adsk.core (or a fake in tests); ``log`` is app.log when there is one."""
    if _STATE:
        raise RuntimeError("TEE bridge already running")
    app = core.Application.get()
    marshaller = Marshaller(lambda task_id: bool(app.fireCustomEvent(EVENT_ID, task_id)))
    event = app.registerCustomEvent(EVENT_ID)
    if event is None:
        raise RuntimeError(
            f"registerCustomEvent({EVENT_ID!r}) returned null - is another TEE bridge add-in "
            "running?"
        )
    handler = _make_handler(core, marshaller, log)
    event.add(handler)
    try:
        listener = Listener(marshaller, host, configured_port() if port is None else port)
    except OSError as exc:
        event.remove(handler)
        app.unregisterCustomEvent(EVENT_ID)
        wanted = port if port is not None else configured_port()
        raise RuntimeError(
            f"port {wanted} is already in use - another TEE bridge, or an unrelated app, holds "
            f"it; set TEE_FUSION_PORT and start TEE with --fusion-port <port>. [{exc}]"
        ) from exc
    listener.start()
    # Fusion drops handlers that nothing references: keep them alive here.
    _STATE.update({"app": app, "event": event, "handler": handler, "listener": listener})
    if log is not None:
        log(f"TEE bridge listening on {listener.host}:{listener.port}")
    return _STATE


def shutdown() -> None:
    state = dict(_STATE)
    _STATE.clear()
    listener = state.get("listener")
    if listener is not None:
        listener.close()
    event, handler, app = state.get("event"), state.get("handler"), state.get("app")
    if event is not None and handler is not None:
        with suppress(Exception):
            event.remove(handler)
    if app is not None:
        with suppress(Exception):
            app.unregisterCustomEvent(EVENT_ID)


def run(context):  # Fusion's add-in entry point
    import adsk.core

    app = adsk.core.Application.get()
    try:
        start(adsk.core, log=app.log)
    except Exception as exc:
        app.log(f"TEE bridge failed to start: {exc}")


def stop(context):  # Fusion's add-in exit point
    with suppress(Exception):
        shutdown()
