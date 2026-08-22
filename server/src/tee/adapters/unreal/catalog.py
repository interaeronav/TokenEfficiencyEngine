"""Session-scoped catalog of Epic's toolsets: name resolution + summary cache.

Two friction sources this removes, both from docs/research/07 and both
confirmed live on 5.8.1:

- **Fully-qualified toolset paths drift between point builds.** The model
  should say `BlueprintTools`, not
  `editor_toolset.toolsets.blueprint.BlueprintTools`. Resolution is by
  suffix against the live `list_toolsets`, never hardcoded.
- **`describe_toolset` is enormous and stable within a session.** It is
  fetched at most once per toolset per session; the raw payload is held
  server-side for lazy single-tool expansion and never returned.
"""

from __future__ import annotations

from typing import Any

from tee.kernel.errors import TeeError

from . import summarize as S


class ToolsetCatalog:
    def __init__(self, wire: Any):
        self.wire = wire
        self._toolsets: dict[str, str] = {}  # short name -> qualified name
        self._descriptions: dict[str, str] = {}
        self._raw: dict[str, dict[str, Any]] = {}  # qualified -> parsed payload
        self.fetches = 0  # describe_toolset round-trips actually spent
        self.defaulted_params: dict[str, list[str]] = {}

    # -- toolset names -----------------------------------------------------

    def load_toolsets(self, *, refresh: bool = False) -> dict[str, str]:
        if self._toolsets and not refresh:
            return self._toolsets
        text = self.wire.call_text("list_toolsets")
        toolsets: dict[str, str] = {}
        descriptions: dict[str, str] = {}
        for line in text.splitlines():
            if not line.startswith("- "):
                continue
            head, sep, desc = line[2:].partition(":")
            qualified = head.strip()
            # Toolset DESCRIPTIONS contain their own "- " bullet lists, so a
            # bare startswith("- ") invents toolsets that do not exist (it
            # reported 67 where there are 55). A real entry is
            # "- <qualified.name>: <description>": no spaces before the colon.
            if not qualified or not sep or " " in qualified:
                continue
            toolsets[S.short_name(qualified)] = qualified
            descriptions[S.short_name(qualified)] = desc.strip()
        self._toolsets, self._descriptions = toolsets, descriptions
        return toolsets

    def resolve(self, name: str) -> str:
        """Accept a short name, a qualified name, or a case-insensitive match."""
        toolsets = self.load_toolsets()
        if name in toolsets.values():
            return name
        short = S.short_name(name)
        if short in toolsets:
            return toolsets[short]
        lowered = {k.lower(): v for k, v in toolsets.items()}
        if short.lower() in lowered:
            return lowered[short.lower()]
        near = sorted(k for k in toolsets if short.lower() in k.lower())
        raise TeeError(
            "ue_unknown_toolset",
            f"No toolset matching {name!r} on this engine.",
            fix=f"Close matches: {', '.join(near[:8])}" if near else "List them with ue_toolsets.",
        )

    def list_summary(self, *, name_contains: str | None = None) -> dict[str, Any]:
        toolsets = self.load_toolsets()
        items = sorted(toolsets)
        if name_contains:
            needle = name_contains.lower()
            items = [n for n in items if needle in n.lower()]
        return {
            "total": len(toolsets),
            "shown": len(items),
            "toolsets": [f"{n} | {self._descriptions.get(n, '')}"[:160] for n in items],
            "note": "Call ue_toolset(<name>) for its tool signatures.",
        }

    # -- toolset contents --------------------------------------------------

    def parsed(self, name: str) -> dict[str, Any]:
        """Parsed describe_toolset payload, fetched at most once per session."""
        qualified = self.resolve(name)
        if qualified not in self._raw:
            raw = self.wire.call_text("describe_toolset", {"toolset_name": qualified})
            self._raw[qualified] = S.parse_toolset(raw)
            self.fetches += 1
        return self._raw[qualified]

    def summary(
        self, name: str, *, name_contains: str | None = None, docs: bool = True
    ) -> dict[str, Any]:
        return S.summarize_toolset(self.parsed(name), name_contains=name_contains, docs=docs)

    def describe_tool(self, toolset: str, tool: str) -> dict[str, Any]:
        return S.expand_tool(self.parsed(toolset), tool)

    def call(
        self, toolset: str, tool: str, arguments: dict[str, Any] | None = None, **kw: Any
    ) -> str:
        """Dispatch through Epic's `call_tool` meta-tool, which wants the
        toolset's qualified name and the tool name UNPREFIXED.

        Self-heals the "needs a default value" rejection: the server demands a
        materialised value for object-typed parameters even when their own
        description calls them optional, and it names the offending parameter,
        so the missing one is built from its schema and the call retried
        rather than handed back to the caller as a dead end.
        """
        qualified = self.resolve(toolset)
        args = dict(arguments or {})
        defaulted: list[str] = []
        for _attempt in range(6):
            payload = {
                "toolset_name": qualified,
                "tool_name": S.short_name(tool),
                "arguments": args,
            }
            result = self.wire.call_text("call_tool", payload, **kw)
            missing = S.missing_default_param(result)
            if missing is None or missing in args:
                self.defaulted_params[f"{S.short_name(toolset)}.{S.short_name(tool)}"] = defaulted
                return result
            schema = self._param_schema(qualified, tool, missing)
            args[missing] = S.default_for(schema)
            defaulted.append(missing)
        return result

    def _param_schema(self, toolset: str, tool: str, param: str) -> dict[str, Any] | None:
        try:
            expanded = self.describe_tool(toolset, tool)
        except TeeError:
            return None
        props = (expanded.get("input_schema") or {}).get("properties") or {}
        return props.get(param)
