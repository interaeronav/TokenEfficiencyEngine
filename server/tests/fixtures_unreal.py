"""A fake Epic MCP server good enough to test the connector offline.

Shapes are copied from a live UE 5.8.1 probe (2026-08-22): tool-search mode
with three meta-tools, `describe_toolset` returning a JSON document as a
single text block, and the refPath boilerplate that dominates its size.
"""

from __future__ import annotations

import json
from typing import Any

REF_DESC = "Represents a reference to a UObject or UClass."


def ref_schema(title: str) -> dict[str, Any]:
    return {
        "type": "object",
        "title": title,
        "description": REF_DESC,
        "properties": {
            "refPath": {
                "type": "string",
                "description": "The reference stored as a soft path string.",
            }
        },
        "required": ["refPath"],
    }


TOOLSETS: dict[str, dict[str, Any]] = {
    "editor_toolset.toolsets.actor.ActorTools": {
        "name": "editor_toolset.toolsets.actor.ActorTools",
        "version": "1.0",
        "description": (
            "Provides tools for inspecting and modifying actors,\n    including transforms."
        ),
        "tools": [
            {
                "name": "editor_toolset.toolsets.actor.ActorTools.add_component",
                "description": (
                    "Adds a component to an actor.\n\n        Args:\n"
                    "            owner: The actor.\n\n        Returns:\n"
                    "            The component."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "owner": ref_schema("/Script/CoreUObject.Object"),
                        "name": {"type": "string"},
                        "container_type": {"type": "string", "enum": ["ARRAY", "SET", "MAP"]},
                    },
                    "required": ["owner", "name"],
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {"returnValue": ref_schema("/Script/Engine.ActorComponent")},
                    "required": ["returnValue"],
                },
            },
            {
                "name": "editor_toolset.toolsets.actor.ActorTools.set_actor_transform",
                "description": "Sets an actor's transform.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "actor": ref_schema("/Script/Engine.Actor"),
                        "location": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "number"},
                                "y": {"type": "number"},
                                "z": {"type": "number"},
                            },
                        },
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["actor"],
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {"returnValue": {"type": "boolean"}},
                },
            },
        ],
    }
}


class FakeUnrealWire:
    """Stands in for UnrealWire: same call surface, no HTTP."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.session_id = "fake-session"

    def connect(self, *, force: bool = False) -> dict[str, Any]:
        return {"protocolVersion": "2025-06-18", "serverInfo": {"name": "", "title": ""}}

    def probe(self) -> bool:
        return True

    def call_text(self, name: str, arguments: dict[str, Any] | None = None, **kw: Any) -> str:
        arguments = arguments or {}
        self.calls.append((name, arguments))
        if name == "list_toolsets":
            # Real payloads interleave description bullet lists, which look
            # exactly like entries unless the parser is strict (live 5.8.1
            # reported 67 "toolsets" that way where there are 55).
            lines = []
            for q, ts in TOOLSETS.items():
                lines.append(f"- {q}: {ts['description'].splitlines()[0]}")
                lines.append("- Enum value lookups")
                lines.append("- FX-related operations in levels or blueprints")
                lines.append("")
            return "\n".join(lines)
        if name == "describe_toolset":
            return json.dumps(TOOLSETS[arguments["toolset_name"]])
        if name == "call_tool":
            return json.dumps({"returnValue": {"refPath": "/Game/X.X:PersistentLevel.Y"}})
        raise AssertionError(f"unexpected meta-tool {name}")
