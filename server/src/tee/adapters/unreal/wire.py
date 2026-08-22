"""Streamable-HTTP MCP client for Epic's in-editor server (UE 5.8+).

Protocol facts verified live against UE 5.8.1 on 2026-08-22 (see
docs/PROGRESS.md "Phase 3 discovery"); where they disagree with
docs/research/07 the live engine wins:

- endpoint ``http://127.0.0.1:8000/mcp``, protocol ``2025-06-18``,
  ``Mcp-Session-Id`` handed out by ``initialize``;
- the server may answer a POST with EITHER plain JSON or an SSE stream.
  Doc 07 says ``tools/call`` always answers SSE; 5.8.1 answered plain JSON
  for every call measured. Both shapes are parsed here rather than betting
  on either;
- ``serverInfo.name`` is EMPTY on 5.8.1, so the server is identified by a
  successful handshake, never by name.

Dispatch is strictly serial (Epic runs tools on the game thread; concurrent
calls deadlock the editor), so every request holds ``_lock``. stdlib HTTP
only - the server core deliberately carries no HTTP dependency.
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from typing import Any

from tee.kernel.errors import TeeError

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_PATH = "/mcp"
PROTOCOL_VERSION = "2025-06-18"
_ACCEPT = "application/json, text/event-stream"
_MAX_RESPONSE_BYTES = 64 * 1024 * 1024


class UnrealWire:
    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        path: str = DEFAULT_PATH,
        connect_timeout: float = 3.0,
        call_timeout: float = 120.0,
    ):
        self.host = host
        self.port = port
        self.path = path
        self.connect_timeout = connect_timeout
        self.call_timeout = call_timeout
        self.session_id: str | None = None
        self.server_info: dict[str, Any] = {}
        self._lock = threading.RLock()
        self._next_id = 0

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}{self.path}"

    # -- lifecycle ---------------------------------------------------------

    def connect(self, *, force: bool = False) -> dict[str, Any]:
        """Handshake and cache the session id. Idempotent unless `force`."""
        with self._lock:
            if self.session_id and not force:
                return self.server_info
            self.session_id = None
            result, headers = self._post(
                {
                    "jsonrpc": "2.0",
                    "id": self._ident(),
                    "method": "initialize",
                    "params": {
                        "protocolVersion": PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "tee", "version": "0.1.0"},
                    },
                },
                timeout=self.connect_timeout + 10.0,
            )
            session = headers.get("Mcp-Session-Id") or headers.get("mcp-session-id")
            if not session:
                raise TeeError(
                    "ue_no_session",
                    "The Unreal MCP server did not return an Mcp-Session-Id.",
                    fix="Check the endpoint really is Unreal's MCP server "
                    f"({self.url}); another MCP server may hold that port.",
                )
            self.session_id = session
            self.server_info = result
            # The server expects this notification before normal traffic; it
            # answers 202 with no body, so no result is parsed.
            self._post(
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                timeout=self.connect_timeout + 5.0,
                notification=True,
            )
            return result

    def probe(self) -> bool:
        try:
            self.connect()
            return True
        except TeeError:
            return False

    def close(self) -> None:
        with self._lock:
            self.session_id = None
            self.server_info = {}

    # -- calls -------------------------------------------------------------

    def request(
        self, method: str, params: dict[str, Any] | None = None, *, timeout: float | None = None
    ) -> dict[str, Any]:
        """One JSON-RPC round trip, serialized against every other call."""
        with self._lock:
            self.connect()
            payload = {
                "jsonrpc": "2.0",
                "id": self._ident(),
                "method": method,
                "params": params or {},
            }
            try:
                result, _ = self._post(payload, timeout=timeout or self.call_timeout)
            except TeeError as exc:
                if exc.code != "ue_session_expired":
                    raise
                # The editor restarted or dropped the session: re-handshake
                # once so a long-lived TEE session survives it.
                self.connect(force=True)
                payload["id"] = self._ident()
                result, _ = self._post(payload, timeout=timeout or self.call_timeout)
            return result

    def list_tools(self) -> list[dict[str, Any]]:
        return list(self.request("tools/list").get("tools", []))

    def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None, *, timeout: float | None = None
    ) -> dict[str, Any]:
        return self.request(
            "tools/call", {"name": name, "arguments": arguments or {}}, timeout=timeout
        )

    def call_text(
        self, name: str, arguments: dict[str, Any] | None = None, *, timeout: float | None = None
    ) -> str:
        """Concatenated text content of a tool result - the shape every Epic
        toolset actually returns."""
        result = self.call_tool(name, arguments, timeout=timeout)
        parts = [
            block.get("text", "")
            for block in result.get("content", [])
            if block.get("type") == "text"
        ]
        return "".join(parts)

    # -- transport ---------------------------------------------------------

    def _ident(self) -> int:
        self._next_id += 1
        return self._next_id

    def _post(
        self, payload: dict[str, Any], *, timeout: float, notification: bool = False
    ) -> tuple[dict[str, Any], dict[str, str]]:
        headers = {"Content-Type": "application/json", "Accept": _ACCEPT}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        req = urllib.request.Request(
            self.url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read(_MAX_RESPONSE_BYTES)
                out_headers = dict(resp.headers.items())
                content_type = resp.headers.get("Content-Type", "")
        except urllib.error.HTTPError as exc:
            if exc.code in (400, 404) and self.session_id:
                raise TeeError(
                    "ue_session_expired",
                    f"The Unreal MCP session was rejected (HTTP {exc.code}).",
                    fix="TEE re-handshakes automatically; if this repeats the "
                    "editor probably restarted.",
                ) from exc
            raise TeeError(
                "ue_http_error",
                f"Unreal MCP server returned HTTP {exc.code} for {payload.get('method')}.",
                fix="Check the editor's Output Log for the MCP server's own error.",
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise TeeError(
                "ue_unreachable",
                f"No Unreal MCP server answering at {self.url} ({exc}).",
                fix="Start the editor, then Editor Preferences > Model Context "
                "Protocol > Start Server (or launch with "
                "-ModelContextProtocolStartServer). `tee doctor` checks this.",
            ) from exc

        if notification:
            return {}, out_headers
        message = self._decode(raw, content_type)
        if "error" in message:
            err = message["error"]
            raise TeeError(
                "ue_tool_error",
                str(err.get("message", err))[:500],
                fix="Call ue_describe_tool for the argument schema.",
            )
        return message.get("result", {}), out_headers

    @staticmethod
    def _decode(raw: bytes, content_type: str) -> dict[str, Any]:
        """Accept either a plain JSON body or an SSE stream. 5.8.1 sends JSON;
        doc 07 documents SSE. Sniffing the body is more durable than trusting
        either the Content-Type or the version."""
        text = raw.decode("utf-8", errors="replace").strip()
        if not text:
            return {}
        if text.startswith("{"):
            return _loads(text)
        if "text/event-stream" in content_type or text.startswith(("event:", "data:", ":")):
            last: dict[str, Any] = {}
            for line in text.splitlines():
                if line.startswith("data:"):
                    chunk = line[5:].strip()
                    if chunk and chunk != "[DONE]":
                        last = _loads(chunk)
            return last
        return _loads(text)


def _loads(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TeeError(
            "ue_bad_response",
            f"Unreal MCP server sent a body that is not JSON: {text[:200]!r}",
            fix="Confirm nothing else is bound to that port.",
        ) from exc
    if not isinstance(parsed, dict):
        raise TeeError(
            "ue_bad_response",
            f"Expected a JSON-RPC object, got {type(parsed).__name__}.",
            fix="Confirm nothing else is bound to that port.",
        )
    return parsed
