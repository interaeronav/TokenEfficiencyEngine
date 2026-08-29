"""XML-RPC wire to the FreeCAD MCP addon (the P0-decided one bridge).

stdlib xmlrpc.client with a real socket timeout; every failure is a
rule-6 TeeError naming the fix. `py`/`py_json` are the read-back
channel: the addon's execute_code captures stdout, so a code snippet
prints one line and the wire hands it back parsed.
"""

from __future__ import annotations

import json
import xmlrpc.client
from typing import Any

from tee.kernel.errors import TeeError

DEFAULT_URL = "http://127.0.0.1:9875"
_START_FIX = (
    "Start FreeCAD with the MCP addon's RPC server (workbench 'MCP Addon' "
    "-> Start RPC Server, or its Auto-Start setting) - docs/setup-freecad.md."
)
_OUTPUT_MARKER = "Output: "


class _TimeoutTransport(xmlrpc.client.Transport):
    def __init__(self, timeout: float):
        super().__init__()
        self._timeout = timeout

    def make_connection(self, host):
        connection = super().make_connection(host)
        connection.timeout = self._timeout
        return connection


class FreeCADWire:
    """One RPC endpoint; methods mirror the addon's surface 1:1."""

    def __init__(self, url: str = DEFAULT_URL, *, timeout_s: float = 60.0):
        self.url = url
        self._proxy = xmlrpc.client.ServerProxy(
            url, allow_none=True, transport=_TimeoutTransport(timeout_s)
        )

    def _call(self, method: str, *args: Any) -> Any:
        try:
            return getattr(self._proxy, method)(*args)
        except (TimeoutError, ConnectionError, OSError) as exc:
            raise TeeError(
                "freecad_unreachable", f"No FreeCAD RPC at {self.url} ({exc}).", fix=_START_FIX
            ) from exc
        except xmlrpc.client.Fault as exc:
            raise TeeError(
                "freecad_rpc_error",
                f"FreeCAD RPC {method} faulted: {str(exc.faultString)[:200]}",
                fix="The addon logged the full error in FreeCAD's Report view.",
            ) from exc

    @staticmethod
    def _checked(result: Any, what: str) -> dict[str, Any]:
        if isinstance(result, dict) and result.get("success"):
            return result
        message = (result or {}).get("error") if isinstance(result, dict) else result
        raise TeeError(
            "freecad_op_failed",
            f"{what}: {str(message)[:250]}",
            fix="The message above is FreeCAD's own; fix what it names and retry.",
        )

    # -- the addon surface -------------------------------------------------

    def ping(self) -> bool:
        try:
            return bool(self._proxy.ping())
        except Exception:
            return False

    def create_document(self, name: str) -> str:
        res = self._checked(self._call("create_document", name), "create_document")
        return str(res.get("document_name") or name)

    def create_object(self, doc: str, obj_data: dict[str, Any]) -> str:
        res = self._checked(self._call("create_object", doc, obj_data), "create_object")
        return str(res.get("object_name") or obj_data.get("Name"))

    def edit_object(self, doc: str, name: str, properties: dict[str, Any]) -> None:
        self._checked(
            self._call("edit_object", doc, name, {"Properties": properties}),
            f"edit_object {name}",
        )

    def delete_object(self, doc: str, name: str) -> None:
        self._checked(self._call("delete_object", doc, name), f"delete_object {name}")

    def get_objects(self, doc: str) -> list[dict[str, Any]]:
        rows = self._call("get_objects", doc)
        return rows if isinstance(rows, list) else []

    def list_documents(self) -> list[str]:
        docs = self._call("list_documents")
        return [str(d) for d in docs] if isinstance(docs, list) else []

    def py(self, code: str) -> str:
        """execute_code; returns the captured stdout (possibly empty)."""
        res = self._checked(self._call("execute_code", code), "execute_code")
        message = str(res.get("message") or "")
        marker = message.find(_OUTPUT_MARKER)
        return message[marker + len(_OUTPUT_MARKER) :] if marker >= 0 else ""

    def py_json(self, code: str) -> Any:
        """Run code that prints ONE json line; returns it parsed."""
        out = self.py(code).strip().splitlines()
        for line in reversed(out):
            line = line.strip()
            if line.startswith(("{", "[")):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        raise TeeError(
            "freecad_bad_readback",
            f"execute_code printed no JSON line (got: {' / '.join(out[-3:]) or 'nothing'}).",
            fix="This is a TEE codegen bug - the snippet must print one JSON line.",
        )
