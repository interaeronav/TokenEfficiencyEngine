"""Unreal virtual tools (ue_*) registered into the progressive-disclosure
registry when the Unreal adapter is active. Discoverable via
tee_search_tools; invoked via tee_call.

The shape of this surface is the whole A4 bet: Epic dispatches 830 tools
server-side behind three meta-tools, so TEE does NOT mirror them. It adds the
navigation layer (compact toolset/tool listings), the escape hatch (raw
call/script), and the few macros where Epic's own surface reports success on
a silent failure.
"""

from __future__ import annotations

import json
from typing import Any

from tee.app import TeeApp
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool

from .adapter import UnrealAdapter

_DSL_DOCS_CACHE: dict[str, str] = {}


def register_unreal_tools(app: TeeApp, adapter: UnrealAdapter) -> None:
    catalog = adapter.catalog

    def ue_toolsets(args: dict[str, Any]) -> dict[str, Any]:
        return catalog.list_summary(name_contains=args.get("name_contains"))

    def ue_toolset(args: dict[str, Any]) -> dict[str, Any]:
        return catalog.summary(
            str(args["toolset"]),
            name_contains=args.get("name_contains"),
            docs=bool(args.get("docs", True)),
        )

    def ue_describe_tool(args: dict[str, Any]) -> dict[str, Any]:
        return catalog.describe_tool(str(args["toolset"]), str(args["tool"]))

    def ue_call(args: dict[str, Any]) -> dict[str, Any]:
        raw = catalog.call(
            str(args["toolset"]),
            str(args["tool"]),
            args.get("arguments") or {},
            timeout=float(args["timeout"]) if args.get("timeout") else None,
        )
        return {"result": _maybe_json(raw)}

    def ue_script(args: dict[str, Any]) -> dict[str, Any]:
        if not app.allow_code_exec:
            raise TeeError(
                "code_exec_disabled",
                "Editor script execution is disabled for this project.",
                fix="Set [server].allow_code_exec = true in .tee/config.toml, "
                "or use typed ops via tee_batch / ue_call.",
            )
        checkpoint = app.checkpoints.create(adapter, "auto:ue_script", app.cache("unreal").revision)
        result = adapter._run_script(str(args["script"]), timeout=float(args.get("timeout", 300)))
        app.cache("unreal").resync(adapter)
        return {"checkpoint": checkpoint.id, "result": result}

    def ue_blueprint_function(args: dict[str, Any]) -> dict[str, Any]:
        return adapter.blueprint_function(
            folder=str(args.get("folder", "/Game")),
            asset_name=str(args["asset_name"]),
            function_name=str(args["function_name"]),
            dsl=str(args["dsl"]),
            params=args.get("params"),
            parent_class=str(args.get("parent_class", "/Script/Engine.Actor")),
            warnings_as_errors=bool(args.get("warnings_as_errors", True)),
        )

    def ue_graph_dsl_docs(args: dict[str, Any]) -> dict[str, Any]:
        """~2,166 tokens and identical for the whole session - fetched once."""
        if "docs" not in _DSL_DOCS_CACHE:
            raw = catalog.call("BlueprintTools", "get_graph_dsl_docs", {}, timeout=120)
            _DSL_DOCS_CACHE["docs"] = str(_maybe_json(raw))
        return {"docs": _DSL_DOCS_CACHE["docs"]}

    def ue_entity_detail(args: dict[str, Any]) -> dict[str, Any]:
        ids = args.get("ids") or []
        if not isinstance(ids, list) or not ids:
            raise TeeError(
                "bad_arguments",
                "ue_entity_detail needs a non-empty 'ids' list.",
                fix="Get ids from tee_scene_summary(adapter='unreal').",
            )
        if len(ids) > 25:
            raise TeeError(
                "too_many_ids",
                f"Asked for {len(ids)} actors; each costs ~0.7s on the editor's game thread.",
                fix="Request at most 25 at a time.",
            )
        return {"actors": [e.detailed() for e in adapter.entity_details([str(i) for i in ids])]}

    tools = [
        VirtualTool(
            name="ue_toolsets",
            description=(
                "List Unreal's toolsets (one line each). Epic dispatches ~830 "
                "tools server-side behind 3 meta-tools; this is the map. "
                "Then ue_toolset(<name>) for its signatures."
            ),
            schema={
                "type": "object",
                "properties": {"name_contains": {"type": "string"}},
            },
            handler=ue_toolsets,
            tags=["unreal", "discovery", "toolsets"],
            examples=[{"name_contains": "blueprint"}],
        ),
        VirtualTool(
            name="ue_toolset",
            description=(
                "Compact signatures for one Unreal toolset ('!' marks a "
                "required argument). Never returns Epic's raw describe_toolset "
                "dump, which is ~18K tokens for BlueprintTools alone. Use "
                "name_contains to filter, ue_describe_tool for one full schema."
            ),
            schema={
                "type": "object",
                "properties": {
                    "toolset": {"type": "string"},
                    "name_contains": {"type": "string"},
                    "docs": {"type": "boolean"},
                },
                "required": ["toolset"],
            },
            handler=ue_toolset,
            tags=["unreal", "discovery", "schema"],
            examples=[{"toolset": "ActorTools", "name_contains": "transform"}],
        ),
        VirtualTool(
            name="ue_describe_tool",
            description=(
                "Full input/output JSON Schema for ONE Unreal tool. Use after "
                "ue_toolset when a signature is not enough."
            ),
            schema={
                "type": "object",
                "properties": {"toolset": {"type": "string"}, "tool": {"type": "string"}},
                "required": ["toolset", "tool"],
            },
            handler=ue_describe_tool,
            tags=["unreal", "schema"],
            examples=[{"toolset": "ActorTools", "tool": "set_actor_transform"}],
        ),
        VirtualTool(
            name="ue_call",
            description=(
                "Invoke one Unreal tool by toolset + tool name. Each call costs "
                "~0.37s serialized on the editor's game thread, so prefer "
                "tee_batch or ue_script when doing several."
            ),
            schema={
                "type": "object",
                "properties": {
                    "toolset": {"type": "string"},
                    "tool": {"type": "string"},
                    "arguments": {"type": "object"},
                    "timeout": {"type": "number"},
                },
                "required": ["toolset", "tool"],
            },
            handler=ue_call,
            tags=["unreal", "call", "escape-hatch"],
            examples=[{"toolset": "SceneTools", "tool": "get_current_level"}],
        ),
        VirtualTool(
            name="ue_blueprint_function",
            description=(
                "Author a Blueprint function from graph DSL and VERIFY it "
                "landed. Epic's write_graph_dsl silently drops statements it "
                "cannot resolve and the Blueprint then compiles clean, so a "
                "wrong node id looks like success; this reads the graph back "
                "and fails loudly instead. ue_graph_dsl_docs has the grammar."
            ),
            schema={
                "type": "object",
                "properties": {
                    "folder": {"type": "string"},
                    "asset_name": {"type": "string"},
                    "function_name": {"type": "string"},
                    "dsl": {"type": "string"},
                    "params": {"type": "array"},
                    "parent_class": {"type": "string"},
                    "warnings_as_errors": {"type": "boolean"},
                },
                "required": ["asset_name", "function_name", "dsl"],
            },
            handler=ue_blueprint_function,
            tags=["unreal", "blueprint", "authoring"],
            examples=[
                {
                    "folder": "/Game/Tee",
                    "asset_name": "BP_Math",
                    "function_name": "AddTwo",
                    "dsl": "(fn AddTwo (A B)\n  (return (Utilities|Operators|Add :A A :B B)))",
                    "params": [
                        {"name": "A", "type": "int", "input": True},
                        {"name": "B", "type": "int", "input": True},
                        {"name": "Sum", "type": "int", "input": False},
                    ],
                }
            ],
        ),
        VirtualTool(
            name="ue_graph_dsl_docs",
            description=(
                "Full Blueprint graph-DSL grammar (~2.2K tokens, fetched once "
                "per session). Read before writing a non-trivial graph."
            ),
            schema={"type": "object", "properties": {}},
            handler=ue_graph_dsl_docs,
            tags=["unreal", "blueprint", "docs"],
        ),
        VirtualTool(
            name="ue_entity_detail",
            description=(
                "Labels and transforms for specific actors. Scene listings omit "
                "them because each actor costs ~0.7s on the game thread; this "
                "is the opt-in detail path (max 25 ids)."
            ),
            schema={
                "type": "object",
                "properties": {"ids": {"type": "array", "items": {"type": "string"}}},
                "required": ["ids"],
            },
            handler=ue_entity_detail,
            tags=["unreal", "scene", "detail"],
            examples=[{"ids": ["u1", "u2"]}],
        ),
    ]

    if app.allow_code_exec:
        tools.append(
            VirtualTool(
                name="ue_script",
                description=(
                    "Run one sandboxed Python script inside the editor "
                    "(escape hatch; enabled via --allow-code-exec). Must define "
                    "run() returning a dict; call tools with "
                    "execute_tool(name, json_input). Auto-checkpoints first. "
                    "Allowed imports: json, math, datetime, copy, re, time. "
                    "Tool results are _StrictDict: use d['k'], never "
                    "d.get('k', default)."
                ),
                schema={
                    "type": "object",
                    "properties": {
                        "script": {"type": "string"},
                        "timeout": {"type": "number"},
                    },
                    "required": ["script"],
                },
                handler=ue_script,
                tags=["unreal", "python", "escape-hatch", "script"],
            )
        )

    for tool in tools:
        app.registry.register(tool)


def _maybe_json(raw: str) -> Any:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if isinstance(parsed, dict) and "returnValue" in parsed:
        inner = parsed["returnValue"]
        if isinstance(inner, str):
            try:
                return json.loads(inner)
            except json.JSONDecodeError:
                return inner
        return inner
    return parsed
