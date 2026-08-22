"""Compress Epic's `describe_toolset` payloads (P1: never forward a dump).

Measured live on UE 5.8.1 (2026-08-22): one `describe_toolset` on
`BlueprintTools` is 72,168 chars (~18K tokens) - more than six times TEE's
entire always-loaded tool surface. Nothing in the model's context should ever
carry that.

Where the bytes go, and what this module does about each:

- **refPath boilerplate.** Every UObject/UClass parameter repeats the same
  ~250-char object schema (`title`, "Represents a reference to a UObject or
  UClass.", a `refPath` string property, `required`). Collapsed to
  `ref<Actor>` - the title's last segment, which is the only part that varies.
- **Full JSON Schema per tool, twice** (input + output). Collapsed to a
  one-line signature; the full schema stays server-side and is expanded for a
  single tool on demand.
- **Google-style docstrings.** The `Args:`/`Returns:` blocks restate the
  schema, so only the leading summary line is kept.
"""

from __future__ import annotations

import json
from typing import Any

from tee.kernel.errors import TeeError

_REF_DESC = "Represents a reference to a UObject or UClass."
# Docstring summaries past this are restating the signature; the full
# docstring is one ue_describe_tool call away.
_DOC_CHARS = 90


def parse_toolset(raw: str) -> dict[str, Any]:
    """Parse a `describe_toolset` text payload into its JSON object."""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TeeError(
            "ue_bad_toolset_payload",
            "describe_toolset did not return JSON.",
            fix="The engine's MCP payload shape may have changed; run "
            "`tee doctor` and check the editor's Output Log.",
        ) from exc
    if not isinstance(parsed, dict) or "tools" not in parsed:
        raise TeeError(
            "ue_bad_toolset_payload",
            "describe_toolset returned no 'tools' array.",
            fix="Check the toolset name with ue_toolsets.",
        )
    return parsed


def short_name(qualified: str) -> str:
    """`editor_toolset.toolsets.actor.ActorTools.add_component` -> `add_component`.

    Epic prefixes every tool with its full module path, and `call_tool` wants
    the tool name UNPREFIXED alongside the toolset name.
    """
    return qualified.rsplit(".", 1)[-1]


def type_label(schema: dict[str, Any] | None) -> str:
    """One-token type name for a JSON Schema node."""
    if not isinstance(schema, dict):
        return "any"
    if "enum" in schema:
        return "|".join(str(v) for v in schema["enum"][:6])
    kind = schema.get("type")
    if kind == "array":
        return f"list[{type_label(schema.get('items'))}]"
    if kind == "object":
        props = schema.get("properties") or {}
        if "refPath" in props or schema.get("description") == _REF_DESC:
            title = str(schema.get("title") or "Object")
            return f"ref<{title.rsplit('.', 1)[-1]}>"
        if {"x", "y", "z"} <= set(props):
            return "vec3"
        if {"pitch", "yaw", "roll"} <= set(props):
            return "rot3"
        if {"r", "g", "b"} <= set(props):
            return "color"
        if props:
            return "{" + ",".join(sorted(props)[:4]) + "}"
        return "obj"
    return {"string": "str", "boolean": "bool", "integer": "int", "number": "float"}.get(
        str(kind), str(kind or "any")
    )


def summary_line(description: str | None) -> str:
    """Leading summary sentence of a Google-style docstring; the Args:/Returns:
    blocks only restate the schema we already compress."""
    if not description:
        return ""
    out: list[str] = []
    for line in description.splitlines():
        stripped = line.strip()
        if stripped in ("Args:", "Returns:", "Raises:", "Note:", "Example:"):
            break
        if stripped:
            out.append(stripped)
        elif out:
            break
    return " ".join(out)


def tool_signature(tool: dict[str, Any]) -> str:
    """`add_component(owner: ref<Object>!, name: str) -> ref<ActorComponent>`;
    `!` marks a required argument."""
    schema = tool.get("inputSchema") or {}
    props: dict[str, Any] = schema.get("properties") or {}
    required = set(schema.get("required") or [])
    args = [
        f"{name}: {type_label(spec)}{'!' if name in required else ''}"
        for name, spec in props.items()
    ]
    out = tool.get("outputSchema") or {}
    out_props = out.get("properties") or {}
    # Epic wraps returns as {"returnValue": ...} (and PODs additionally as
    # {"result": ...}); the wrapper carries no information for the caller.
    inner = out_props.get("returnValue") or out_props.get("result") or (out if out_props else None)
    returns = type_label(inner) if inner else "none"
    return f"{short_name(str(tool.get('name', '?')))}({', '.join(args)}) -> {returns}"


def summarize_toolset(
    parsed: dict[str, Any],
    *,
    name_contains: str | None = None,
    docs: bool = True,
) -> dict[str, Any]:
    """Compact, model-facing view of a whole toolset."""
    tools = parsed.get("tools") or []
    if name_contains:
        needle = name_contains.lower()
        tools = [t for t in tools if needle in short_name(str(t.get("name", ""))).lower()]
    lines = []
    for tool in tools:
        doc = summary_line(tool.get("description")) if docs else ""
        if len(doc) > _DOC_CHARS:
            doc = doc[: _DOC_CHARS - 1].rstrip() + "\u2026"
        # One string per tool, not {"sig":...,"doc":...}: the JSON punctuation
        # of a per-tool object costs ~20 chars x N tools for no information.
        lines.append(f"{tool_signature(tool)} | {doc}" if doc else tool_signature(tool))
    return {
        "toolset": parsed.get("name"),
        "about": summary_line(parsed.get("description")),
        "total": len(parsed.get("tools") or []),
        "shown": len(tools),
        "tools": lines,
        "note": "Signatures only ('!' = required). ue_describe_tool(<tool>) "
        "expands one full schema.",
    }


def expand_tool(parsed: dict[str, Any], tool_name: str) -> dict[str, Any]:
    """Full input/output schema for exactly ONE tool (lazy expansion)."""
    wanted = short_name(tool_name).lower()
    for tool in parsed.get("tools") or []:
        if short_name(str(tool.get("name", ""))).lower() == wanted:
            return {
                "toolset": parsed.get("name"),
                "tool": short_name(str(tool["name"])),
                "signature": tool_signature(tool),
                "doc": tool.get("description"),
                "input_schema": tool.get("inputSchema"),
                "output_schema": tool.get("outputSchema"),
            }
    available = sorted(short_name(str(t.get("name", ""))) for t in parsed.get("tools") or [])
    listed = ", ".join(available[:15]) + ("..." if len(available) > 15 else "")
    raise TeeError(
        "ue_unknown_tool",
        f"No tool {short_name(tool_name)!r} in {parsed.get('name')}.",
        fix=f"Available: {listed}",
    )
