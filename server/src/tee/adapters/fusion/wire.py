"""Wire client for the Fusion bridge add-in (A69).

The Blender wire's shape and framing - NUL-terminated JSON, one request per
connection, the executed code answering through a ``result`` dict - with
Fusion's own refusals. The add-in (`adapters/fusion/tee_bridge/TEE/`) runs
every request on Fusion's primary thread, so a bridge whose primary thread
is held by a modal dialog answers nothing: the call timeout is the guard and
the refusal names the window.

    request:  {"type": "execute", "code": "<python>", "strict_json": bool} + "\\0"
              {"type": "ping"} + "\\0"
    response: {"status": "ok", "result": {...}} or
              {"status": "error", "message": "..."}, optional stdout/stderr, + "\\0"
"""

from __future__ import annotations

import json
import socket
from typing import Any

from tee.kernel.errors import TeeError

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9881  # 9875 FreeCAD, 9876/9877 Blender, 9879 Godot
_MAX_RESPONSE_BYTES = 64 * 1024 * 1024
_RECV_CHUNK = 65536
START_FIX = (
    "In Fusion: Utilities > Add-Ins > Scripts and Add-Ins, add the folder "
    "adapters/fusion/tee_bridge/TEE (or copy it into Fusion's API/AddIns folder) and Run "
    "it; the Text Commands palette then shows 'TEE bridge listening on 127.0.0.1:9881'. "
    "Then tee serve --adapter fusion [--fusion-port N] - docs/fusion-lane.md."
)


class FusionWire:
    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        connect_timeout: float = 2.0,
        call_timeout: float = 120.0,
    ):
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self.call_timeout = call_timeout

    # -- the two requests --------------------------------------------------

    def probe(self) -> bool:
        try:
            self.ping()
            return True
        except TeeError:
            return False

    def ping(self) -> dict[str, Any]:
        """The add-in's own state, answered from the primary thread: product,
        version, active document, design type, id-map size."""
        return self._request({"type": "ping"}, timeout=8.0)

    def execute(
        self, code: str, *, strict_json: bool = True, timeout: float | None = None
    ) -> dict[str, Any]:
        """One request/response round trip; returns the code's ``result``."""
        return self._request(
            {"type": "execute", "code": code, "strict_json": strict_json}, timeout=timeout
        )

    # -- internals -----------------------------------------------------------

    def _request(self, payload: dict[str, Any], *, timeout: float | None) -> dict[str, Any]:
        deadline = timeout or self.call_timeout
        try:
            conn = socket.create_connection((self.host, self.port), self.connect_timeout)
        except OSError as exc:
            raise TeeError(
                "fusion_unreachable",
                f"No TEE bridge at {self.host}:{self.port} ({exc}).",
                fix=START_FIX,
            ) from exc
        try:
            conn.settimeout(deadline)
            conn.sendall(json.dumps(payload).encode("utf-8") + b"\0")
            raw = self._read_frame(conn)
        except TimeoutError as exc:
            raise TeeError(
                "fusion_wire_failed",
                f"Fusion accepted the connection but did not answer within {deadline:.0f} s.",
                fix="A modal dialog may be holding Fusion's primary thread - check the Fusion "
                "window; a long feature computation raises the limit with tee_batch's job path.",
            ) from exc
        except OSError as exc:
            raise TeeError(
                "fusion_wire_failed",
                f"The Fusion bridge dropped the call: {exc}",
                fix="Check the add-in is still running (Scripts and Add-Ins) and retry.",
            ) from exc
        finally:
            conn.close()
        try:
            reply = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise TeeError(
                "fusion_bad_reply",
                f"Unparseable reply from the bridge: {raw[:200]!r}",
                fix="This is a bridge bug; the add-in's log (app.log) has the frame.",
            ) from exc
        if reply.get("status") != "ok":
            message = str(reply.get("message") or "the bridge refused the request")
            tail = "\n".join(message.strip().splitlines()[-4:])
            extra = ""
            if reply.get("stderr"):
                extra = f" stderr: {str(reply['stderr']).strip()[-300:]}"
            raise TeeError(
                "fusion_bridge_error",
                f"{tail[:600]}{extra}",
                fix="The message is Fusion's own (the last lines of the traceback); fix what "
                "it names and resend the batch.",
            )
        result = reply.get("result")
        return result if isinstance(result, dict) else {}

    @staticmethod
    def _read_frame(conn: socket.socket) -> bytes:
        buf = bytearray()
        while True:
            chunk = conn.recv(_RECV_CHUNK)
            if not chunk:
                break
            buf.extend(chunk)
            if buf.endswith(b"\0"):
                break
            if len(buf) > _MAX_RESPONSE_BYTES:
                raise OSError("response exceeds the 64 MiB hard stop")
        return bytes(buf).split(b"\0")[0]
