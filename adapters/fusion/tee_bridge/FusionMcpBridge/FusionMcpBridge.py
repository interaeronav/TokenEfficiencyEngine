"""
Autodesk Fusion MCP bridge add-in.

Install:
  1. Copy this file and FusionMcpBridge.addinf into one folder, e.g.
      ~/Library/Application Support/Autodesk/Fusion/Addins/FusionMcpBridge/
  2. In Fusion: Utilities > Scripts and Add-ins, or install via the .addinf.
  3. Run the "Start MCP Bridge" command, or let it auto-start (see below).

Auto-start: place `manifest.json` (runOnStartup=true) next to this file, or
drop a copy as a script into MyScripts/Autorun/.

The bridge listens on 127.0.0.1:8766. Jobs are queued by the HTTP server
thread and executed on Fusion's main thread via a registered CustomEvent
(the old transientEvents time-event API was removed from current Fusion).
Assign to `result` to return a value.
"""
import json
import queue
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import adsk.core
import adsk.fusion

HOST = "127.0.0.1"
PORT = 8766
EVENT_ID = "opencode.mcp.bridge"

_server = None
_event = None
_handler = None
_jobs = queue.Queue()
_results = {}


def _safe(value):
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)


def _run_code(code):
    """Runs on the Fusion main thread. `adsk` is available; assign to `result`."""
    namespace = {"adsk": adsk, "result": None}
    try:
        exec(compile(code, "<mcp>", "exec"), namespace)
        return {"ok": True, "result": _safe(namespace.get("result"))}
    except Exception:
        return {"ok": False, "error": traceback.format_exc()}


class _JobHandler(adsk.core.CustomEventHandler):
    """Fired on the main thread when the HTTP thread enqueues a job."""

    def notify(self, event_args):
        processed = 0
        while processed < 20:
            try:
                job_id, code = _jobs.get_nowait()
            except queue.Empty:
                break
            _results[job_id] = _run_code(code)
            processed += 1


class Handler(BaseHTTPRequestHandler):
    def _send(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/status":
            self._send({"ok": True, "app": "Autodesk Fusion", "port": PORT})
        else:
            self._send({"ok": False, "error": "not found"}, 404)

    def do_POST(self):
        if self.path != "/run":
            self._send({"ok": False, "error": "not found"}, 404)
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send({"ok": False, "error": "invalid json"}, 400)
            return
        job_id = uuid.uuid4().hex
        _jobs.put((job_id, data.get("code", "")))
        try:
            adsk.core.Application.get().fireCustomEvent(EVENT_ID)
        except Exception:
            pass
        deadline = time.time() + float(data.get("timeout", 120))
        while job_id not in _results:
            if time.time() > deadline:
                self._send({"ok": False, "error": "timed out waiting for Fusion"}, 504)
                return
            time.sleep(0.05)
        self._send(_results.pop(job_id))

    def log_message(self, format, *args):
        pass


def start():
    global _server, _event, _handler
    if _server is not None:
        return "bridge already running on port %d" % PORT
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as exc:
        return "bridge failed to bind port %d: %s" % (PORT, exc)
    app = adsk.core.Application.get()
    event = app.registerCustomEvent(EVENT_ID)
    if event is None:
        app.unregisterCustomEvent(EVENT_ID)
        event = app.registerCustomEvent(EVENT_ID)
    if event is None:
        server.server_close()
        return "failed to register custom event %s" % EVENT_ID
    handler = _JobHandler()
    if not event.add(handler):
        server.server_close()
        return "failed to attach custom event handler"
    _event = event
    _handler = handler
    _server = server
    threading.Thread(target=_server.serve_forever, daemon=True).start()
    return "bridge started on http://%s:%d" % (HOST, PORT)


def stop(context=None):
    """Stops the bridge. Also the Fusion add-in/script lifecycle hook."""
    global _server, _event, _handler
    if _server is None:
        return "bridge not running"
    _server.shutdown()
    _server = None
    try:
        if _event is not None and _handler is not None:
            _event.remove(_handler)
        adsk.core.Application.get().unregisterCustomEvent(EVENT_ID)
    except Exception:
        pass
    _event = None
    _handler = None
    return "bridge stopped"


def run(context):
    """Fusion entry point. Called at auto-start (no inputItems) and when the
    user invokes the Start MCP Bridge command."""
    try:
        message = start()
    except Exception:
        message = "failed to start bridge:\n" + traceback.format_exc()
    input_items = getattr(context, "inputItems", None)
    if input_items:
        ui = adsk.core.UserInterfaceManager.instance
        inputs = adsk.core.CommandInputs.cast(input_items)
        command = inputs.command
        ui.messageBox(message, "Fusion MCP Bridge")
        command.destroy()
    else:
        print("[FusionMcpBridge] " + message)
