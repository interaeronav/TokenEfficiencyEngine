"""Wire client for the Blender bridge socket.

Protocol (identical to the official Blender Lab MCP add-on, verified against
its source and a live Blender 5.2 session):

    request:  {"type": "execute", "code": "<python>", "strict_json": bool} + "\\0"
    response: {"status": "ok"|"error", "result": {...}} or
              {"status": "error", "message": "<traceback>"}, optional
              "stdout"/"stderr" keys, + "\\0"

The executed code communicates back by assigning a dict to a variable named
``result``. Connections are per-call: the bridge evicts idle clients after
~10s anyway, and a fresh localhost connection costs microseconds - this keeps
the client stateless and immune to half-open sockets (fail fast, P7).
"""

from __future__ import annotations

import json
import socket
from typing import Any

from tee.kernel.errors import TeeError

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9876
_MAX_RESPONSE_BYTES = 64 * 1024 * 1024  # hard stop against a runaway bridge
_RECV_CHUNK = 65536


class BlenderWire:
    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        connect_timeout: float = 2.0,
        call_timeout: float = 30.0,
    ):
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self.call_timeout = call_timeout

    def execute(
        self,
        code: str,
        *,
        strict_json: bool = True,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """One request/response round-trip. Raises TeeError fast when the
        bridge is down or the response cannot be parsed."""
        request = json.dumps({"type": "execute", "code": code, "strict_json": strict_json})
        try:
            with socket.create_connection(
                (self.host, self.port), timeout=self.connect_timeout
            ) as conn:
                conn.settimeout(timeout or self.call_timeout)
                conn.sendall(request.encode("utf-8") + b"\0")
                raw = self._read_frame(conn)
        except (ConnectionRefusedError, socket.gaierror) as exc:
            raise TeeError(
                "blender_unreachable",
                f"No Blender bridge on {self.host}:{self.port}.",
                fix=(
                    "Start Blender with the MCP bridge add-on enabled, or run "
                    "'blender --background --command blender_mcp' / the TEE bridge."
                ),
            ) from exc
        except TimeoutError as exc:
            raise TeeError(
                "blender_timeout",
                f"Blender did not answer within {timeout or self.call_timeout:.0f}s.",
                fix=(
                    "Long operations must go through async job tools; "
                    "if Blender shows a modal dialog, dismiss it."
                ),
            ) from exc
        except OSError as exc:
            raise TeeError(
                "blender_io_error",
                f"Bridge I/O failed: {type(exc).__name__}: {exc}",
                fix="Check tee_status; reconnect happens automatically on the next call.",
            ) from exc
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TeeError(
                "blender_bad_response",
                f"Bridge sent an unparseable frame ({len(raw)} bytes).",
                fix="Retry once; if it persists the bridge add-on is broken.",
            ) from exc

    def probe(self) -> bool:
        """Cheap liveness check; never raises, never hangs."""
        try:
            response = self.execute("result = {'ok': True}", timeout=5.0)
        except TeeError:
            return False
        return response.get("status") == "ok"

    @staticmethod
    def _read_frame(conn: socket.socket) -> bytes:
        buf = bytearray()
        while True:
            chunk = conn.recv(_RECV_CHUNK)
            if not chunk:
                raise TeeError(
                    "blender_disconnected",
                    "Bridge closed the connection mid-response.",
                    fix="Retry; check that Blender did not crash (tee_status).",
                )
            buf.extend(chunk)
            if len(buf) > _MAX_RESPONSE_BYTES:
                raise TeeError(
                    "blender_response_too_large",
                    f"Bridge response exceeded {_MAX_RESPONSE_BYTES // 1024 // 1024}MB.",
                    fix="Narrow the query; never return bulk data through the bridge.",
                )
            if buf.endswith(b"\0"):
                return bytes(buf[:-1])
