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


# -- A71: the SECOND transport - the FusionMcpBridge add-in the owner's Mac already runs --

DEFAULT_HTTP_PORT = (
    8766  # adapters/fusion/tee_bridge/FusionMcpBridge/ (HTTP, auto-starts with Fusion)
)

START_FIX_ANY = (
    "Start Autodesk Fusion with a TEE bridge add-in running - either "
    "adapters/fusion/tee_bridge/TEE (Utilities > Add-Ins > Scripts and Add-Ins > + > Run; "
    "127.0.0.1:9881) or adapters/fusion/tee_bridge/FusionMcpBridge (copied into "
    "'~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/'; auto-starts "
    "with Fusion on 127.0.0.1:8766) - docs/fusion-lane.md."
)

# The primary thread's own answer - the same program and keys the TEE add-in
# runs for a ping (adapters/fusion/tee_bridge/TEE/TEE.py PING_CODE). Kept here
# because the FusionMcpBridge has no ping of its own: its GET /status is
# answered by the HTTP thread, which says nothing about a primary thread held
# by a modal dialog (the FreeCAD SI-B12 lesson), so a ping must run code.
PING_PROGRAM = """\
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
    "ids": (len(_tee.get("ids", {})) if _doc is not None
            and _tee.get("design") == str(getattr(_doc, "creationId", None) or "") else 0),
}
"""

# The FusionMcpBridge execs every job in a FRESH namespace ({adsk, result}), so
# the `_tee` dict the codegen's prelude expects would be lost between calls.
# This prelude keeps it in a process-lifetime module instead: the id map
# survives exactly as long as it does behind the TEE add-in (the bridge's
# life), and nothing else is shared between jobs.
STATE_PRELUDE = (
    "import sys as _tee_sys, types as _tee_types\n"
    "_tee = _tee_sys.modules.setdefault('_tee_fusion_state', "
    "_tee_types.ModuleType('_tee_fusion_state')).__dict__.setdefault('tee', {})\n"
)


class FusionHttpWire(FusionWire):
    """The FusionMcpBridge add-in (`adapters/fusion/tee_bridge/FusionMcpBridge/`),
    HTTP on 127.0.0.1:8766 - the bridge the owner's machine already runs, verified
    live against Fusion 2704.1.53 on 2026-09-06:

        GET  /status                   -> {"ok": true, "app": "Autodesk Fusion", "port": 8766}
        POST /run {"code", "timeout"}  -> {"ok": true, "result": <value of `result`>}
                                       -> {"ok": false, "error": "<traceback>"}

    The code runs on Fusion's primary thread, queued through a registered
    CustomEvent. HTTP 504 means the primary thread did not finish within
    `timeout` - and the job KEEPS RUNNING inside Fusion (the CERES 50 lesson:
    a nine-minute build became three "timeouts" while it was working the whole
    time), so every timeout travels explicitly and the refusal says so.

    `strict_json` is advisory here: the bridge reprs a result it cannot
    serialise, and a result that is then not a dict is refused as a bad reply.
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_HTTP_PORT,
        connect_timeout: float = 2.0,
        call_timeout: float = 120.0,
    ):
        super().__init__(host, port, connect_timeout, call_timeout)

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def ping(self) -> dict[str, Any]:
        return self.execute(PING_PROGRAM, timeout=8.0)

    def execute(
        self, code: str, *, strict_json: bool = True, timeout: float | None = None
    ) -> dict[str, Any]:
        import urllib.error
        import urllib.request

        deadline = float(timeout or self.call_timeout)
        body = json.dumps({"code": STATE_PRELUDE + code, "timeout": deadline}).encode("utf-8")
        request = urllib.request.Request(
            self.url + "/run",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=deadline + 10.0) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 504:
                raise TeeError(
                    "fusion_wire_failed",
                    f"Fusion's primary thread did not finish within {deadline:.0f} s - the job "
                    "is STILL RUNNING inside Fusion.",
                    fix="Do not resend it blindly: read the design first "
                    "(tee_scene_summary adapter=fusion refresh=true), then retry with a larger "
                    "timeout or split the batch. A modal dialog may be holding Fusion's "
                    "primary thread - check the Fusion window.",
                ) from exc
            raise TeeError(
                "fusion_bridge_error",
                f"The FusionMcpBridge answered HTTP {exc.code}.",
                fix="Restart the add-in inside Fusion (Utilities > Add-Ins > Fusion MCP Bridge "
                "> Run) and retry.",
            ) from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise TeeError(
                    "fusion_wire_failed",
                    f"The FusionMcpBridge accepted the request but did not answer within "
                    f"{deadline + 10:.0f} s.",
                    fix="A modal dialog may be holding Fusion's primary thread - check the "
                    "Fusion window; the job may still be running.",
                ) from exc
            raise TeeError(
                "fusion_unreachable",
                f"No FusionMcpBridge at {self.host}:{self.port} ({exc.reason}).",
                fix=START_FIX_ANY,
            ) from exc
        except TimeoutError as exc:
            raise TeeError(
                "fusion_wire_failed",
                f"The FusionMcpBridge did not answer within {deadline + 10:.0f} s.",
                fix="A modal dialog may be holding Fusion's primary thread - check the Fusion "
                "window; the job may still be running.",
            ) from exc
        except OSError as exc:
            raise TeeError(
                "fusion_wire_failed",
                f"The FusionMcpBridge dropped the call: {exc}",
                fix="Check the add-in is still running (Utilities > Add-Ins) and retry.",
            ) from exc
        try:
            reply = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise TeeError(
                "fusion_bad_reply",
                f"Unparseable reply from the FusionMcpBridge: {raw[:200]!r}",
                fix="This is a bridge bug; retry once, then restart the add-in.",
            ) from exc
        if not isinstance(reply, dict):
            raise TeeError(
                "fusion_bad_reply",
                "The FusionMcpBridge sent a non-object reply.",
                fix="Retry once; if it persists the add-in is broken.",
            )
        if not reply.get("ok"):
            message = str(reply.get("error") or "the bridge refused the request")
            tail = "\n".join(message.strip().splitlines()[-4:])
            raise TeeError(
                "fusion_bridge_error",
                tail[:600],
                fix="The message is Fusion's own (the last lines of the traceback); fix what "
                "it names and resend the batch.",
            )
        result = reply.get("result")
        if not isinstance(result, dict):
            raise TeeError(
                "fusion_bad_reply",
                f"The program's `result` was not a dict (the bridge sent {type(result).__name__}; "
                "it reprs what it cannot serialise).",
                fix="Every TEE program assigns a JSON-safe dict to `result`; this is a codegen "
                "bug if a typed batch produced it.",
            )
        return result


class FusionAutoWire(FusionWire):
    """Whichever bridge add-in answers: the TEE add-in (NUL-framed TCP, 9881)
    first, then the FusionMcpBridge (HTTP, 8766). Detection is a ping - the
    primary thread's own answer - and the transport that answered is kept
    until it stops answering, so a lane served before Fusion is open finds the
    bridge when it appears. `port` reports the transport in use."""

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        http_port: int = DEFAULT_HTTP_PORT,
        connect_timeout: float = 2.0,
        call_timeout: float = 120.0,
    ):
        self.active: FusionWire | None = None
        self.candidates: tuple[FusionWire, ...] = (
            FusionWire(host, port, connect_timeout, call_timeout),
            FusionHttpWire(host, http_port, connect_timeout, call_timeout),
        )
        super().__init__(host, port, connect_timeout, call_timeout)

    @property  # type: ignore[override]
    def port(self) -> int:
        return self.active.port if self.active is not None else self._port

    @port.setter
    def port(self, value: int) -> None:
        self._port = value

    @property
    def transport(self) -> str | None:
        if self.active is None:
            return None
        return "FusionMcpBridge" if isinstance(self.active, FusionHttpWire) else "TEE add-in"

    def _detect(self) -> FusionWire:
        reasons = []
        for wire in self.candidates:
            try:
                wire.ping()
            except TeeError as exc:
                reasons.append(f":{wire.port} {exc.code}")
                continue
            self.active = wire
            return wire
        raise TeeError(
            "fusion_unreachable",
            "No Fusion bridge answered a ping (" + "; ".join(reasons) + ").",
            fix=START_FIX_ANY,
        )

    def ping(self) -> dict[str, Any]:
        if self.active is not None:
            try:
                return self.active.ping()
            except TeeError as exc:
                if exc.code != "fusion_unreachable":
                    raise
                self.active = None
        return self._detect().ping()

    def execute(
        self, code: str, *, strict_json: bool = True, timeout: float | None = None
    ) -> dict[str, Any]:
        wire = self.active or self._detect()
        try:
            return wire.execute(code, strict_json=strict_json, timeout=timeout)
        except TeeError as exc:
            if exc.code != "fusion_unreachable" or wire is not self.active:
                raise
            self.active = None
            raise
