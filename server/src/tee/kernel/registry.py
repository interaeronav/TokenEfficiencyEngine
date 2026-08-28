"""Progressive-disclosure tool registry (principle P4, decision A6).

The always-loaded MCP surface stays tiny; the long tail of DCC-specific
capability lives here as *virtual tools*, reachable through three client-
agnostic meta-tools: tee_search_tools / tee_describe_tool / tee_call. This
works identically on every MCP client (no reliance on tools/list_changed).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from tee.kernel.errors import TeeError

_TYPE_CHECKS: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
}


@dataclass
class VirtualTool:
    name: str
    description: str  # first line = one-line summary used in search results
    schema: dict[str, Any]  # JSON-schema subset: {"type":"object","properties":...,"required":...}
    handler: Callable[[dict[str, Any]], dict[str, Any]]
    tags: list[str] = field(default_factory=list)
    examples: list[dict[str, Any]] = field(default_factory=list)

    @property
    def one_line(self) -> str:
        """First line of the description, capped to roughly a sentence.

        Search results pay this per hit; authors drift toward paragraph-long
        'first lines', so the cap - not the author - holds the search row
        price. The full text stays one tee_describe_tool away."""
        line = self.description.strip().splitlines()[0]
        if len(line) <= 150:
            return line
        cut = line.rfind(". ", 0, 150)
        if cut > 40:
            return line[: cut + 1]
        return line[:147].rstrip() + "..."


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, VirtualTool] = {}
        self.disabled: set[str] = set()  # per-project profile (.tee/config.toml)

    def register(self, tool: VirtualTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"duplicate virtual tool: {tool.name}")
        if tool.schema.get("type") != "object":
            raise ValueError(f"{tool.name}: schema must be a plain object schema (A6)")
        props = tool.schema.get("properties", {})
        missing = [key for key in tool.schema.get("required", []) if key not in props]
        if missing:
            raise ValueError(
                f"{tool.name}: required keys {missing} are not in properties - "
                "the tool would be permanently uncallable"
            )
        self._tools[tool.name] = tool

    def __len__(self) -> int:
        return len(self._tools)

    def names(self) -> list[str]:
        return sorted(self._tools)

    # -- meta-tool backends ------------------------------------------------

    def search(self, query: str, limit: int = 10) -> dict[str, Any]:
        """Rank by word overlap against name, tags, and description.

        Returns {"items": [...]} plus a "note" when nothing scored well, so
        a weak result is distinguishable from a good one without spending
        describe round-trips to find out (SI-B2)."""
        words = [w for w in re.split(r"[^a-z0-9]+", query.lower()) if w]
        scored: list[tuple[float, str]] = []
        for name, tool in self._tools.items():
            if name in self.disabled:
                continue
            haystacks = (
                (name.lower(), 3.0),
                (" ".join(tool.tags).lower(), 2.0),
                (tool.description.lower(), 1.0),
            )
            score = 0.0
            for word in words:
                for text, weight in haystacks:
                    if word in text:
                        score += weight
                        break
            if score > 0 or not words:
                scored.append((score, name))
        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        result: dict[str, Any] = {
            "items": [
                {"name": name, "summary": self._tools[name].one_line} for _, name in scored[:limit]
            ]
        }
        top = scored[0][0] if scored else 0.0
        if words and top < 2.0:
            result["note"] = (
                "no strong match (name/tag hits: none) - the capability may "
                "not exist or may be adapter-gated; try other words"
            )
        return result

    def describe(self, name: str) -> dict[str, Any]:
        tool = self._require(name)
        payload: dict[str, Any] = {
            "name": tool.name,
            "description": tool.description,
            "schema": tool.schema,
        }
        if tool.examples:
            payload["examples"] = tool.examples
        return payload

    def call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        tool = self._require(name)
        self._validate(tool, args or {})
        return tool.handler(args or {})

    # -- internals ---------------------------------------------------------

    def _require(self, name: str) -> VirtualTool:
        if name in self.disabled:
            raise TeeError(
                "tool_disabled",
                f"'{name}' is disabled for this project.",
                fix="Remove it from [tools].disabled in .tee/config.toml to re-enable.",
            )
        tool = self._tools.get(name)
        if tool is None:
            suggestions = self.search(name, limit=3)["items"]
            hint = ", ".join(s["name"] for s in suggestions) or "tee_search_tools"
            raise TeeError(
                "unknown_tool",
                f"No tool named '{name}'.",
                fix=f"Closest matches: {hint}.",
            )
        return tool

    def _validate(self, tool: VirtualTool, args: dict[str, Any]) -> None:
        """Minimal JSON-schema subset validation: required keys + basic types.
        One short error naming the exact problem (P7)."""
        props: dict[str, Any] = tool.schema.get("properties", {})
        for key in tool.schema.get("required", []):
            if key not in args:
                raise TeeError(
                    "missing_argument",
                    f"{tool.name}: required argument '{key}' is missing.",
                    fix=f"Schema: tee_describe_tool(name='{tool.name}').",
                )
        for key, value in args.items():
            spec = props.get(key)
            if spec is None:
                raise TeeError(
                    "unknown_argument",
                    f"{tool.name}: unknown argument '{key}'.",
                    fix=f"Known arguments: {', '.join(sorted(props)) or '(none)'}.",
                )
            expected = spec.get("type")
            check = _TYPE_CHECKS.get(expected) if expected else None
            if check is not None and value is not None:
                ok = isinstance(value, check)
                # bool is an int subclass; don't accept True for integer/number
                if ok and isinstance(value, bool) and expected in ("integer", "number"):
                    ok = False
                if not ok:
                    raise TeeError(
                        "bad_argument_type",
                        f"{tool.name}: '{key}' must be {expected}, got {type(value).__name__}.",
                    )
