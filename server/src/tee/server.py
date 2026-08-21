"""MCP tool surface: a thin, budgeted layer over TeeApp.

Client-compatibility floor (decision A6):
- every tool returns plain JSON-text content (no outputSchema is emitted -
  return annotations are deliberately absent from tool functions);
- images are inline base64 JPEG only, never resource links;
- the always-loaded surface stays small (<= 15 tools, enforced by test);
- descriptions stay under 2 KB each (enforced by test).
"""

from __future__ import annotations

import functools
import json
from collections.abc import Callable
from typing import Any

from mcp.server.mcpserver import Image, MCPServer

from tee.app import TeeApp
from tee.kernel.budget import enforce_budget
from tee.kernel.errors import TeeError, internal_error_payload

_CAPTURE_DEFAULT_KB = 16
_CAPTURE_MAX_KB = 256

_DESC = {
    "tee_status": (
        "Server, adapter and scene status: connected DCCs, scene revision stamps, "
        "active jobs, recent checkpoints."
    ),
    "tee_recall": (
        "Recall persistent project memory (versions, conventions, recent notes) "
        "as a compact preamble. Call once at session start instead of re-asking "
        "the user."
    ),
    "tee_remember": (
        "Store durable project memory: a fact (key+value) and/or a dated "
        "free-form note. Facts overwrite by key; notes append."
    ),
    "tee_scene_summary": (
        "Compact scene summary: entity counts by kind plus a paged entity list "
        "(ids, names, kinds). Filter with kind=/name_contains=, page with "
        "limit=/offset=. refresh=true rebuilds the cache from the DCC (new "
        "epoch). response_format='detailed' adds per-entity summary fields."
    ),
    "tee_entity_detail": (
        "Full cached detail for one entity by id (from tee_scene_summary or a diff)."
    ),
    "tee_diff": (
        "What changed since a known (epoch, revision) stamp: "
        "created/modified/deleted ids with compact details, flagged user_edits if "
        "a human edited concurrently. Answers 'resync_required' when history "
        "broke (rollback/reload) - then call tee_scene_summary(refresh=true)."
    ),
    "tee_batch": (
        "Apply a batch of typed operations atomically-ish with an automatic "
        "checkpoint first. Ops: {op:'create',kind,name,props} | "
        "{op:'set',id,props} | {op:'delete',id}. Returns the checkpoint id and "
        "the diff (never the full scene). One batch of N ops costs one round-trip "
        "- prefer it over N calls."
    ),
    "tee_checkpoint": (
        "Create a named checkpoint of the current DCC state for later tee_rollback."
    ),
    "tee_rollback": (
        "Roll the DCC back to a checkpoint (by id like 'cp3' or by label). Later "
        "checkpoints are discarded; the scene cache re-syncs (new epoch)."
    ),
    "tee_job": (
        "Status of an async job (bake/render/import) by id; cancel=true requests "
        "cancellation. Poll this instead of waiting on long operations."
    ),
    "tee_capture": (
        "Viewport capture as a small inline JPEG (default budget 16KB). Expensive "
        "relative to text: prefer tee_scene_summary / geometric checks first "
        "(P3). max_kb caps the image budget (<=256)."
    ),
    "tee_search_tools": (
        "Search the long tail of DCC-specific tools by keywords (e.g. 'blender "
        "material', 'bake physics'). Returns names + one-line summaries; then "
        "tee_describe_tool for the schema and tee_call to invoke."
    ),
    "tee_describe_tool": (
        "Full description, argument schema and examples for one virtual tool "
        "found via tee_search_tools."
    ),
    "tee_call": (
        "Invoke a virtual tool by name with a JSON object of arguments (schema "
        "from tee_describe_tool). Arguments are validated before execution; "
        "errors name the exact fix."
    ),
}


def _tool(app: TeeApp, name: str) -> Callable:
    """Wrap a tool body: serialized on app.lock (the SDK dispatches tool
    calls on concurrent worker threads; kernel state and the DCC bridges are
    serial), TeeError -> compact payload, unexpected exception -> compact
    internal error, results budgeted + size-logged, and returned as a compact
    JSON *string* - the SDK pretty-prints dict returns (indent=2), roughly
    doubling wire size, but passes strings through verbatim."""

    def deco(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any):
            with app.lock:
                try:
                    result = fn(*args, **kwargs)
                except TeeError as exc:
                    result = exc.to_payload()
                except Exception as exc:
                    result = internal_error_payload(exc)
                if isinstance(result, dict):
                    result = enforce_budget(result)
                    app.response_log.record(name, result)
                    return json.dumps(result, separators=(",", ":"), default=str)
                return result

        return wrapper

    return deco


def build_server(app: TeeApp) -> MCPServer:
    mcp = MCPServer(
        name="tee",
        instructions=(
            "Token Efficiency Engine: drives Unreal Engine and Blender with "
            "minimal tokens. Reads return compact summaries and diffs, never "
            "full scene dumps; mutations run as batches with automatic "
            "checkpoints. Search the long tail of DCC-specific tools with "
            "tee_search_tools, inspect one with tee_describe_tool, invoke it "
            "with tee_call. Track (epoch, revision) from responses and use "
            "tee_diff to see what changed instead of re-reading the scene."
        ),
    )

    # -- status / memory ---------------------------------------------------

    @mcp.tool(structured_output=False, description=_DESC["tee_status"])
    @_tool(app, "tee_status")
    def tee_status():
        return app.status()

    @mcp.tool(structured_output=False, description=_DESC["tee_recall"])
    @_tool(app, "tee_recall")
    def tee_recall():
        return {"ok": True, **app.memory.preamble()}

    @mcp.tool(structured_output=False, description=_DESC["tee_remember"])
    @_tool(app, "tee_remember")
    def tee_remember(
        key: str | None = None,
        value: str | float | int | bool | None = None,
        note: str | None = None,
    ):
        if key is not None:
            app.memory.remember(key, value)
        if note:
            app.memory.note(note)
        if key is None and not note:
            raise TeeError("nothing_to_store", "Provide key+value and/or note.")
        return {"ok": True}

    # -- scene reads -------------------------------------------------------

    @mcp.tool(structured_output=False, description=_DESC["tee_scene_summary"])
    @_tool(app, "tee_scene_summary")
    def tee_scene_summary(
        adapter: str = "fake",
        limit: int = 50,
        offset: int = 0,
        kind: str | None = None,
        name_contains: str | None = None,
        refresh: bool = False,
        response_format: str = "concise",
    ):
        if adapter not in app.caches:
            app.adapter(adapter)  # raises with the known-adapter hint
        cache = app.cache(adapter)
        if refresh:
            cache.resync(app.adapter(adapter))
        else:
            app.warm(adapter)
        return {
            "ok": True,
            **cache.summary(
                limit=limit,
                offset=offset,
                kind=kind,
                name_contains=name_contains,
                detailed=response_format == "detailed",
            ),
        }

    @mcp.tool(structured_output=False, description=_DESC["tee_entity_detail"])
    @_tool(app, "tee_entity_detail")
    def tee_entity_detail(entity_id: str, adapter: str = "fake"):
        app.adapter(adapter)
        ent = app.cache(adapter).get(entity_id)
        if ent is None:
            raise TeeError(
                "unknown_entity",
                f"No entity '{entity_id}' in the {adapter} scene cache.",
                fix="List ids with tee_scene_summary; refresh=true if the cache is stale.",
            )
        return {"ok": True, "entity": ent.detailed(), **app.cache(adapter).stamp()}

    @mcp.tool(structured_output=False, description=_DESC["tee_diff"])
    @_tool(app, "tee_diff")
    def tee_diff(epoch: int, revision: int, adapter: str = "fake"):
        app.adapter(adapter)
        app.warm(adapter)
        return {"ok": True, **app.cache(adapter).diff_since(epoch, revision)}

    # -- mutations ---------------------------------------------------------

    @mcp.tool(structured_output=False, description=_DESC["tee_batch"])
    @_tool(app, "tee_batch")
    def tee_batch(ops: list[dict[str, Any]], adapter: str = "fake", label: str | None = None):
        if not ops:
            raise TeeError("empty_batch", "ops is empty.", fix="Send at least one operation.")
        return app.run_batch(adapter, ops, label)

    @mcp.tool(structured_output=False, description=_DESC["tee_checkpoint"])
    @_tool(app, "tee_checkpoint")
    def tee_checkpoint(label: str, adapter: str = "fake"):
        cp = app.checkpoints.create(app.adapter(adapter), label, app.cache(adapter).revision)
        return {"ok": True, "checkpoint": cp.to_payload()}

    @mcp.tool(structured_output=False, description=_DESC["tee_rollback"])
    @_tool(app, "tee_rollback")
    def tee_rollback(ref: str, adapter: str = "fake"):
        return app.rollback(adapter, ref)

    # -- jobs --------------------------------------------------------------

    @mcp.tool(structured_output=False, description=_DESC["tee_job"])
    @_tool(app, "tee_job")
    def tee_job(job_id: str, cancel: bool = False):
        if cancel:
            return {"ok": True, **app.jobs.cancel(job_id)}
        return {"ok": True, **app.jobs.status(job_id)}

    # -- vision ------------------------------------------------------------

    @mcp.tool(structured_output=False, description=_DESC["tee_capture"])
    def tee_capture(
        adapter: str = "fake", view: str = "viewport", max_kb: int = _CAPTURE_DEFAULT_KB
    ):
        with app.lock:
            try:
                max_bytes = max(1, min(int(max_kb), _CAPTURE_MAX_KB)) * 1024
                data = app.adapter(adapter).capture(view, max_bytes)
            except TeeError as exc:
                return json.dumps(exc.to_payload())
            except Exception as exc:
                return json.dumps(internal_error_payload(exc))
            app.response_log.record("tee_capture", {"bytes": len(data)})
            return Image(data=data, format="jpeg")

    # -- progressive disclosure (meta-tools) --------------------------------

    @mcp.tool(structured_output=False, description=_DESC["tee_search_tools"])
    @_tool(app, "tee_search_tools")
    def tee_search_tools(query: str, limit: int = 10):
        return {"ok": True, "tools": app.registry.search(query, limit)}

    @mcp.tool(structured_output=False, description=_DESC["tee_describe_tool"])
    @_tool(app, "tee_describe_tool")
    def tee_describe_tool(name: str):
        return {"ok": True, **app.registry.describe(name)}

    @mcp.tool(structured_output=False, description=_DESC["tee_call"])
    @_tool(app, "tee_call")
    def tee_call(name: str, args: dict[str, Any] | None = None):
        result = app.registry.call(name, args or {})
        if isinstance(result, dict) and "ok" not in result:
            result = {"ok": True, **result}
        if isinstance(result, dict):
            # per-virtual-tool size log so the median alert works per tool
            app.response_log.record(f"virtual:{name}", result)
        return result

    return mcp
