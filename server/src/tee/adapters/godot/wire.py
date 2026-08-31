"""Wire client for the Godot bridge socket.

Framing is deliberately identical to the Blender bridge - NUL-terminated
JSON, one request per connection - because a second wire shape would be a
second thing to get subtly wrong. What differs is the payload: Blender
ships Python source, Godot ships DECLARATIVE ops, because the escape hatch
belongs behind its own capability rather than in the default path.

    request  {"type": "commands", "ops": [...]}  + "\\0"
    reply    {"status": "ok", "result": {...}}   + "\\0"
             {"status": "error", "message": "..."} + "\\0"
"""

from __future__ import annotations

import json
import socket
from typing import Any

from tee.kernel.errors import TeeError

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9879  # 9876/9877 belong to Blender


class GodotWire:
    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        connect_timeout: float = 2.0,
        call_timeout: float = 60.0,
    ):
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self.call_timeout = call_timeout

    def probe(self) -> bool:
        try:
            self.request({"type": "ping"}, timeout=self.connect_timeout + 2.0)
            return True
        except TeeError:
            return False

    def request(self, payload: dict[str, Any], timeout: float | None = None) -> dict[str, Any]:
        deadline = timeout or self.call_timeout
        try:
            conn = socket.create_connection((self.host, self.port), self.connect_timeout)
        except OSError as exc:
            raise TeeError(
                "godot_unreachable",
                f"No Godot bridge at {self.host}:{self.port} ({exc}).",
                fix="Start it: godot --headless --path <project> -s "
                "adapters/godot/tee_bridge/bridge.gd -- --port "
                f"{self.port}. A project that has never been imported must be "
                "opened once with `godot --headless --path <project> --import` "
                "first, or the launch hangs with no output.",
            ) from exc
        try:
            conn.settimeout(deadline)
            conn.sendall(json.dumps(payload).encode("utf-8") + b"\0")
            buffer = bytearray()
            while b"\0" not in buffer:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                buffer.extend(chunk)
        except OSError as exc:
            raise TeeError(
                "godot_wire_failed",
                f"The Godot bridge dropped the call: {exc}",
                fix="Check the bridge process is still running; it exits after "
                "15 minutes idle by design.",
            ) from exc
        finally:
            conn.close()

        raw = bytes(buffer).split(b"\0")[0].decode("utf-8", errors="replace")
        if not raw.strip():
            raise TeeError(
                "godot_wire_failed",
                "The Godot bridge returned nothing.",
                fix="Look at the bridge's stdout for a GDScript parse error.",
            )
        try:
            reply = json.loads(raw)
        except ValueError as exc:
            raise TeeError(
                "godot_wire_failed", f"Unparseable reply: {raw[:200]}", fix="Check the bridge log."
            ) from exc
        if reply.get("status") != "ok":
            raise TeeError(
                "godot_refused",
                str(reply.get("message") or "the bridge refused the request"),
                fix="The message names the allowed values.",
            )
        return reply.get("result") or {}
