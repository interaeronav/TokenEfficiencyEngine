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

from tee.kernel import lanes, trust, trustctx
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
    # A43 L4: the capability this tool needs. Left None, it is resolved from
    # the trust table AT REGISTRATION - and a tool the table does not know
    # fails at STARTUP. That is what makes kernel coverage structural rather
    # than a habit: a new tool cannot silently escape the check, because the
    # server refuses to boot until someone tables it.
    capability: str | None = None
    # A68: the served lane this tool touches - an adapter name, lanes.ADAPTER_ARG
    # for a tool that routes by its own adapter= argument, a proxy label, or
    # None for an adapter-agnostic tool. Left None, it is resolved from the
    # lane table AT REGISTRATION, and a scene-writing tool the table does not
    # know fails at STARTUP (kernel/lanes.py).
    lane: str | None = None

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
        # A43 L1/L4: what this project may do. Default = no grants, which
        # leaves the read tier and the baseline verbs working and refuses
        # everything else - a new project is useful immediately and cannot
        # do anything irreversible.
        self._grants = trust.Grants()
        # A45 P0a: when set, the owner's config file is re-read on change so
        # a widening takes effect on the NEXT CALL rather than the next
        # restart. Assigning `.grants` directly still works (tests, fakes).
        self.grants_watcher: Any = None
        self.trust_denials: list[dict[str, Any]] = []  # shadow band, for tee_trust
        self.audit_log = None  # set by the app: side-effecting calls are logged
        # A68: the served lanes, for search's tie-break; set by the app. None
        # means "no app": every lane counts as served.
        self.served: Callable[[], set[str]] | None = None

    @property
    def grants(self) -> trust.Grants:
        if self.grants_watcher is not None:
            return self.grants_watcher()
        return self._grants

    @grants.setter
    def grants(self, value: trust.Grants) -> None:
        self._grants = value
        self.grants_watcher = None  # an explicit set wins over the watcher

    def register(self, tool: VirtualTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"duplicate virtual tool: {tool.name}")
        if tool.capability is None:
            # Raises trust_untabled_tool at STARTUP for an unknown tool.
            tool.capability = trust.capability_for(tool.name)
        elif tool.capability not in trust.CAPABILITIES:
            raise ValueError(
                f"{tool.name}: '{tool.capability}' is not a known capability "
                f"(kernel/trust.py owns the list)"
            )
        if tool.lane is None:
            tool.lane = lanes.lane_for(tool.name)
        lanes.check(tool)  # a scene-writing tool says which scene, or the server does not boot
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

    def unregister(self, name: str) -> None:
        """Remove one virtual tool; silently a no-op when absent. Exists for
        surfaces that re-pin at runtime (the gateway re-registers a fronted
        backend's tools after an accepted fingerprint drift)."""
        self._tools.pop(name, None)

    def __len__(self) -> int:
        return len(self._tools)

    def names(self) -> list[str]:
        return sorted(self._tools)

    def lane_of(self, name: str) -> str | None:
        """The lane a registered tool touches (A68); None for an unknown or
        adapter-agnostic tool."""
        tool = self._tools.get(name)
        return None if tool is None else tool.lane

    # -- meta-tool backends ------------------------------------------------

    def search(self, query: str, limit: int = 5) -> dict[str, Any]:
        """Rank by word overlap against name, tags, and description.

        Returns {"items": [...]} plus a "note" when nothing scored well, so
        a weak result is distinguishable from a good one without spending
        describe round-trips to find out (SI-B2).

        The default was 10 and is now 5, measured rather than guessed, and
        RE-MEASURED whenever the corpus grows - a bigger registry is a
        different measurement, not a broken one. Re-baselined 2026-09-04
        (A66) over 29 realistic queries (21 direct, 8 deliberately vague)
        against an 81-tool registry (67 before the partkiln lane's 14
        `pk_*` tools):

            limit 3   28/29      limit 5   29/29
            limit 8   29/29      limit 10  29/29

        Five finds everything ten finds. Three does not - "size from an
        image" wants `ex_estimate` and lands at rank 4, behind three tools
        that merely mention a size or an image - so this is the measured
        floor, not the smallest number that looked defensible. (A50's
        witness was "check the drawing"; `pk_check` and `pk_drawing` now
        own both content words by NAME, so the query was reassigned to its
        honest owner rather than tagged away.) The reply is ~237 tokens
        against ~488 at a limit of 10, a 51% cut on EVERY search, which is
        the most frequent call TEE makes on its own behalf.

        Re-baselined again 2026-09-05 (A68) on the registry a Desktop server
        actually serves - 173 tools, 38 cases: limit 3 finds 35, limit 5
        finds all 38. The 85-tool fixture had hidden one miss at 5.

        `tests/test_search_budget.py::test_the_rebaselined_recall_table_holds`
        EXECUTES that table, so the next lane cannot let it go stale here.

        `more` names how many were suppressed, so a caller who genuinely
        needs the tail can ask instead of guessing that the tail is empty.
        """
        # Words of one or two letters are dropped: matching is by SUBSTRING,
        # so "a" in "add a watermark to a document" scores against every
        # tool whose name merely contains an 'a' - which outranked the tool
        # that actually stamps watermarks (A48). Short tokens carry no
        # topic and, being substrings, carry maximum noise.
        words = [w for w in re.split(r"[^a-z0-9]+", query.lower()) if len(w) > 2]
        # A68: at equal score a tool whose lane is served outranks one whose
        # lane is not (it would only refuse); agnostic tools count as served.
        served = self.served() if self.served is not None else None
        scored: list[tuple[float, int, str]] = []
        for name, tool in self._tools.items():
            if name in self.disabled:
                continue
            haystacks = (
                (name.lower(), 3.0),
                (" ".join(tool.tags).lower(), 2.0),
                (tool.description.lower(), 1.0),
                # the lane name LAST: it counts only when nothing else matched
                # the word, so "blender render" still ranks bl_render by name
                ((tool.lane or "").lower(), 1.0),
            )
            score = 0.0
            for word in words:
                for text, weight in haystacks:
                    if word in text:
                        score += weight
                        break
            if score > 0 or not words:
                unserved = int(
                    served is not None
                    and tool.lane not in (None, lanes.ADAPTER_ARG)
                    and tool.lane
                    in {"blender", "unreal", "freecad", "godot", "partkiln", "seamkiln", "fake"}
                    and tool.lane not in served
                )
                scored.append((score, unserved, name))
        scored.sort(key=lambda row: (-row[0], row[1], row[2]))
        result: dict[str, Any] = {
            "items": [
                {"name": name, "summary": self._tools[name].one_line}
                for _, _, name in scored[:limit]
            ]
        }
        if len(scored) > limit:
            result["more"] = len(scored) - limit
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
        if tool.lane is not None:
            payload["lane"] = tool.lane  # A68: which served lane it touches
        if tool.examples:
            payload["examples"] = tool.examples
        return payload

    def call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        tool = self._require(name)
        self._validate(tool, args or {})
        self._trust(tool)
        result = tool.handler(args or {})
        if self.audit_log is not None:
            self.audit_log.record(
                f"virtual:{name}",
                result,
                capability=tool.capability,
                caller=trustctx.caller(),
                taint=trustctx.taint(),
            )
        # A capability whose RESULTS are untrusted content taints this task
        # from here on: a KB passage or a fetched page may inform an answer,
        # but it may never go on to cause a side effect (research 62).
        if tool.capability in trust.TAINT_SOURCES:
            trustctx.add_taint(f"{tool.capability}:{name}")
        return result

    def _trust(self, tool: VirtualTool) -> None:
        """The ONE check (L4). Denials that are safety-critical raise now;
        the taint-vs-quality band is recorded and allowed until the owner
        signs the flip (L6/L7) - the scheduler's shadow discipline, applied
        ONLY where it cannot open a door (research 64 FP-2)."""
        decision = trust.check(
            tool.capability or "read-session",
            caller=trustctx.caller(),
            grants=self.grants,
            taint=trustctx.taint(),
        )
        if decision.allowed:
            return
        if decision.enforced or self.grants.enforce_quality_band:
            decision.raise_if_denied(tool.name)
        trust.record_shadow_denial(
            {
                "tool": tool.name,
                "capability": decision.capability,
                "caller": decision.caller,
            }
        )
        self.trust_denials.append(
            {
                "tool": tool.name,
                "capability": decision.capability,
                "caller": decision.caller,
                "reason": decision.reason,
                "shadow": True,
            }
        )

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
                        fix=f"Schema: tee_describe_tool(name='{tool.name}'). An "
                        "array argument is a LIST of values, never one string "
                        "containing them.",
                    )
