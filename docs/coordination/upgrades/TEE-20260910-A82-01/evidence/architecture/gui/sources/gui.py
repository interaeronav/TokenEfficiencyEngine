"""Optional loopback workbench; all authoring uses ArchitectureService.

Importing this module opens nothing. The URL fragment supplies a per-session
secret to the browser; requests carry it in an Authorization header, never a
query string. No arbitrary file-serving endpoint or remote asset is exposed.
"""

from __future__ import annotations

import hmac
import inspect
import json
import secrets
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from .model import ArchitectureError

MAX_BODY = 1_000_000
MAX_RESPONSE = 12_000_000
_GET = {"status", "state", "preview", "check", "candidates", "schedule", "query"}
_POST = {"create", "edit", "undo", "import", "candidates", "promote", "export", "check", "query"}
_WRITE = {"create", "edit", "undo", "import", "promote", "export"}


class ArchitectureGui:
    def __init__(self, service: Any, authorize: Callable[[bool], None]) -> None:
        self.service = service
        self.authorize = authorize
        self._token = secrets.token_urlsafe(32)
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self.url = ""
        self._slots = threading.BoundedSemaphore(8)

    def _call(self, action: str, args: dict[str, Any]) -> Any:
        if action in {"edit", "undo", "promote"} and type(args.get("expected_revision")) is not int:
            raise ArchitectureError("ak_conflict", "Supply the model's current expected_revision.")
        if action == "schedule":
            from .cabinets import schedule

            if set(args) != {"model_id", "entity_id"}:
                raise ArchitectureError(
                    "ak_gui_arguments", "Schedule needs model_id and entity_id."
                )
            entity = self.service.query(**args)
            return {"revision": entity["revision"], **schedule(entity["entity"])}
        method = getattr(self.service, "import_source" if action == "import" else action)
        try:
            inspect.signature(method).bind(**args)
        except TypeError as exc:
            raise ArchitectureError(
                "ak_gui_arguments", "Arguments do not match this operation."
            ) from exc
        return method(**args)

    def start(self) -> None:
        if self._server is not None:
            return
        gui = self
        page = Path(__file__).with_name("gui.html").read_text(encoding="utf-8")

        class Handler(BaseHTTPRequestHandler):
            server_version = "archkiln"
            sys_version = ""

            def setup(self) -> None:
                super().setup()
                self.connection.settimeout(10)

            def log_message(self, _format: str, *args: Any) -> None:
                # Bearer tokens, document contents and owner paths never enter logs.
                pass

            def _send(self, status: int, payload: Any, *, html: bool = False) -> None:
                nonce = secrets.token_urlsafe(18)
                if html:
                    data = payload.replace("__NONCE__", nonce).encode()
                else:
                    data = json.dumps(payload, ensure_ascii=True, allow_nan=False).encode()
                if len(data) > MAX_RESPONSE:
                    status, data = 413, b'{"error":"ak_gui_limit","message":"Response too large."}'
                    html = False
                self.send_response(status)
                self.send_header(
                    "Content-Type", "text/html; charset=utf-8" if html else "application/json"
                )
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("X-Frame-Options", "DENY")
                self.send_header("Connection", "close")
                self.send_header(
                    "Content-Security-Policy",
                    f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'; "
                    "connect-src 'self'; img-src 'self' data:; base-uri 'none'; "
                    "frame-ancestors 'none'; form-action 'none'",
                )
                self.end_headers()
                self.wfile.write(data)
                self.close_connection = True

            def _error(self, status: int, code: str, message: str) -> None:
                self._send(status, {"error": code, "message": message[:400]})

            def _handle(self, method: str) -> None:
                if not gui._slots.acquire(blocking=False):
                    self._error(503, "ak_gui_busy", "Workbench is busy; retry shortly.")
                    return
                try:
                    self._dispatch(method)
                except ArchitectureError as exc:
                    self._error(409 if exc.code == "ak_conflict" else 400, exc.code, str(exc))
                except (ValueError, TypeError, UnicodeError):
                    self._error(
                        400, "ak_gui_request", "Malformed request or invalid operation arguments."
                    )
                except (BrokenPipeError, ConnectionResetError, TimeoutError):
                    pass
                except Exception:
                    self._error(
                        500,
                        "ak_gui_operation",
                        "Operation failed; inspect the selected data or optional dependency.",
                    )
                finally:
                    gui._slots.release()

            def _dispatch(self, method: str) -> None:
                base = gui.url.split("/#", 1)[0]
                host = base.removeprefix("http://")
                hosts = self.headers.get_all("Host", [])
                origins = self.headers.get_all("Origin", [])
                if hosts != [host] or (origins and origins != [base]):
                    self._error(
                        403, "ak_gui_origin", "Host or Origin does not match this workbench."
                    )
                    return
                if len(self.path) > 4096:
                    self._error(414, "ak_gui_path", "Request path is too long.")
                    return
                target = urlsplit(self.path)
                if target.scheme or target.netloc or target.fragment:
                    self._error(400, "ak_gui_path", "Use a local relative request path.")
                    return
                if method == "GET" and target.path == "/" and not target.query:
                    self._send(200, page, html=True)
                    return
                action = target.path.removeprefix("/api/")
                allowed = _GET if method == "GET" else _POST
                if not target.path.startswith("/api/") or action not in allowed:
                    self._error(404, "ak_gui_path", "Unknown workbench endpoint.")
                    return
                auth = self.headers.get_all("Authorization", [])
                if len(auth) != 1 or not hmac.compare_digest(auth[0], "Bearer " + gui._token):
                    self._error(
                        401, "ak_gui_auth", "Open the full session URL returned by ak_open."
                    )
                    return
                if method == "POST" and origins != [base]:
                    self._error(403, "ak_gui_origin", "Mutations require the workbench Origin.")
                    return
                try:
                    gui.authorize(action in _WRITE)
                except Exception:
                    self._error(
                        403,
                        "ak_gui_denied",
                        "Current project authority does not permit this operation.",
                    )
                    return
                if method == "GET":
                    query = parse_qs(target.query, keep_blank_values=True, max_num_fields=16)
                    if any(len(values) != 1 for values in query.values()):
                        raise ValueError("duplicate query fields")
                    args = {key: values[0] for key, values in query.items()}
                else:
                    lengths = self.headers.get_all("Content-Length", [])
                    if (
                        target.query
                        or self.headers.get("Transfer-Encoding") is not None
                        or len(lengths) != 1
                        or not lengths[0].isascii()
                        or not lengths[0].isdigit()
                    ):
                        raise ValueError("invalid length or query")
                    length = int(lengths[0])
                    if not 1 <= length <= MAX_BODY:
                        self._error(
                            413, "ak_gui_limit", "Request body exceeds the workbench limit."
                        )
                        return
                    if self.headers.get("Content-Type", "").split(";", 1)[0] != "application/json":
                        self._error(415, "ak_gui_content", "Send application/json.")
                        return
                    raw = self.rfile.read(length)
                    if len(raw) != length:
                        raise ValueError("incomplete body")
                    args = json.loads(raw)
                    if not isinstance(args, dict):
                        raise ValueError("object required")
                self._send(200, gui._call(action, args))

            def do_GET(self) -> None:
                self._handle("GET")

            def do_POST(self) -> None:
                self._handle("POST")

            def do_OPTIONS(self) -> None:
                self._error(403, "ak_gui_origin", "Cross-origin access is not enabled.")

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._server.daemon_threads = True
        self.url = f"http://127.0.0.1:{self._server.server_port}/#token={self._token}"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def close(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
        self.url = ""
