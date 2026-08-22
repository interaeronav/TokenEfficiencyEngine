"""The `tee-design/1` spec: versioned, machine-verifiable, the SOURCE OF
TRUTH for a game design (A17). The prose GDD is rendered FROM it, never
written first - LLM prose reads deceptively well; structure does not lie.

Sections (all optional except meta + core_loop; checkers grade what is
present and lint what is missing):
  meta          audience (motivation vector 0-1 per dimension), platform,
                price_usd, min_age, comparables [{name, delta}]
  core_loop     verbs, steps [{action, target_s}], failure_state,
                session_end_hook
  economy       currencies, nodes (faucet/sink/converter), personas
  progression   unlocks [{id, at, teaches, requires, difficulty}],
                pity {base, soft_start, increment, hard, disclosed}
  level_macro   beats [{space, mechanics, exotics, intensity}]
  content_list  [{class, count, reuse, notes}] - feeds Phase 9 + scope
  routine       daily/weekly/season cadences, streak {grace}
  accessibility checklist state for the enforce table
  monetization  model, loot_boxes, currency_hops, odds_disclosed,
                countdown_offers
  open_questions
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

SPEC_VERSION = "tee-design/1"

SECTIONS = (
    "meta",
    "core_loop",
    "economy",
    "progression",
    "level_macro",
    "content_list",
    "routine",
    "accessibility",
    "monetization",
    "open_questions",
)

MOTIVATION_DIMS = (
    # Quantic Foundry-shaped 12 dimensions (6 pairs, 3 clusters) - see
    # data/motivations.json for definitions and encoded findings
    "destruction",
    "excitement",  # Action
    "competition",
    "community",  # Social
    "challenge",
    "strategy",  # Mastery
    "completion",
    "power",  # Achievement
    "fantasy",
    "story",  # Immersion
    "design",
    "discovery",  # Creativity
)

ASSET_CLASSES = (
    # compatible with Phase 9 search/creation + scope weights
    "prop",
    "hero_prop",
    "modular_kit",
    "character",
    "creature",
    "environment_set",
    "material",
    "vfx",
    "sfx",
    "music",
    "ui_screen",
    "level",
    "mechanic_system",
    "cinematic",
)


def _fail(path: str, problem: str, fix: str) -> TeeError:
    return TeeError("invalid_spec", f"{path}: {problem}", fix=fix)


def validate(spec: dict[str, Any]) -> dict[str, Any]:
    """Structural validation: shape, ids, references. Design-QUALITY
    problems are the lint's job (checks.py); this rejects malformed specs
    with the exact fix (P7)."""
    if not isinstance(spec, dict):
        raise _fail("$", "spec must be a JSON object", "wrap the spec in an object")
    if spec.get("spec") != SPEC_VERSION:
        raise _fail(
            "spec",
            f"missing or wrong version tag (got {spec.get('spec')!r})",
            f'set "spec": "{SPEC_VERSION}"',
        )
    unknown = [k for k in spec if k not in (*SECTIONS, "spec", "name") and not k.startswith("_")]
    if unknown:
        raise _fail(
            "$",
            f"unknown section(s) {unknown}",
            f"sections are: {', '.join(SECTIONS)}",
        )
    meta = spec.get("meta")
    if not isinstance(meta, dict):
        raise _fail("meta", "required section missing", "add meta with audience+platform")
    audience = meta.get("audience", {})
    vector = audience.get("motivations", {})
    bad_dims = [d for d in vector if d not in MOTIVATION_DIMS]
    if bad_dims:
        raise _fail(
            "meta.audience.motivations",
            f"unknown dimension(s) {bad_dims}",
            f"dimensions: {', '.join(MOTIVATION_DIMS)}",
        )
    for dim, value in vector.items():
        if not isinstance(value, int | float) or not 0 <= value <= 1:
            raise _fail(
                f"meta.audience.motivations.{dim}",
                f"must be a number in 0..1 (got {value!r})",
                "motivations are continuous dimensions, not types",
            )
    core = spec.get("core_loop")
    if not isinstance(core, dict):
        raise _fail("core_loop", "required section missing", "add core_loop with verbs+steps")
    for i, step in enumerate(core.get("steps", [])):
        if not isinstance(step, dict) or "action" not in step:
            raise _fail(
                f"core_loop.steps[{i}]",
                "each step needs an 'action'",
                'steps: [{"action": "scavenge", "target_s": 40}, …]',
            )
    economy = spec.get("economy") or {}
    currencies = set(economy.get("currencies", []))
    for i, node in enumerate(economy.get("nodes", [])):
        kind = node.get("kind")
        if kind not in ("faucet", "sink", "converter"):
            raise _fail(
                f"economy.nodes[{i}].kind",
                f"unknown kind {kind!r}",
                "kinds: faucet, sink, converter",
            )
        for field in ("currency",) if kind != "converter" else ("from", "to"):
            currency = node.get(field)
            if currency not in currencies:
                raise _fail(
                    f"economy.nodes[{i}].{field}",
                    f"currency {currency!r} not declared",
                    f"declare it in economy.currencies {sorted(currencies)}",
                )
    progression = spec.get("progression") or {}
    ids = [u.get("id") for u in progression.get("unlocks", [])]
    if len(ids) != len(set(ids)):
        raise _fail("progression.unlocks", "duplicate unlock ids", "ids must be unique")
    for i, unlock in enumerate(progression.get("unlocks", [])):
        for req in unlock.get("requires", []):
            if req not in ids:
                raise _fail(
                    f"progression.unlocks[{i}].requires",
                    f"unknown unlock id {req!r}",
                    "requires must reference declared unlock ids",
                )
    for i, entry in enumerate(spec.get("content_list", [])):
        cls = entry.get("class")
        if cls not in ASSET_CLASSES:
            raise _fail(
                f"content_list[{i}].class",
                f"unknown asset class {cls!r}",
                f"classes (Phase 9-compatible): {', '.join(ASSET_CLASSES)}",
            )
    return {"ok": True, "sections": [s for s in SECTIONS if s in spec]}


# -- rendering (prose FROM the spec, never the reverse) ---------------------


def render_one_pager(spec: dict[str, Any]) -> str:
    meta = spec.get("meta", {})
    core = spec.get("core_loop", {})
    lines = [f"# {spec.get('name', 'Untitled design')}", ""]
    platform = meta.get("platform", "?")
    price = meta.get("price_usd")
    positioning = f"{platform}" + (f" · ${price}" if price is not None else "")
    lines += [f"*{positioning}*", ""]
    comparables = meta.get("comparables", [])
    if comparables:
        lines.append(
            "**Like** " + "; ".join(f"{c['name']} — but {c.get('delta', '?')}" for c in comparables)
        )
        lines.append("")
    verbs = core.get("verbs", [])
    if verbs:
        lines.append(
            f"**You** {', '.join(verbs[:-1])} and {verbs[-1]}."
            if len(verbs) > 1
            else f"**You** {verbs[0]}."
        )
    steps = core.get("steps", [])
    if steps:
        loop = " → ".join(s["action"] for s in steps)
        total = sum(s.get("target_s", 0) for s in steps)
        lines.append(f"Loop: {loop} (~{total // 60}:{total % 60:02d}).")
    if core.get("failure_state"):
        lines.append(f"Failure: {core['failure_state']}.")
    if core.get("session_end_hook"):
        lines.append(f"Come back because: {core['session_end_hook']}.")
    lines.append("")
    content = spec.get("content_list", [])
    if content:
        total_items = sum(int(c.get("count", 0)) for c in content)
        lines.append(
            f"**Scope:** {total_items} content items across "
            f"{len({c['class'] for c in content})} classes."
        )
    questions = spec.get("open_questions", [])
    if questions:
        lines += ["", "**Open questions:**"] + [f"- {q}" for q in questions[:5]]
    return "\n".join(lines)


def render_beat_chart(spec: dict[str, Any]) -> str:
    """Cerny-style macro chart as a markdown table."""
    beats = (spec.get("level_macro") or {}).get("beats", [])
    if not beats:
        return "(no level_macro beats)"
    lines = ["| # | space | mechanics | exotics | intensity |", "|---|---|---|---|---|"]
    for i, beat in enumerate(beats, 1):
        lines.append(
            f"| {i} | {beat.get('space', '')} | "
            f"{', '.join(beat.get('mechanics', []))} | "
            f"{', '.join(beat.get('exotics', []))} | {beat.get('intensity', '')} |"
        )
    return "\n".join(lines)


# -- storage (content-addressed revisions; design changes are diffs) --------


class SpecStore:
    def __init__(self, project_root: Path | str):
        self.root = Path(project_root) / ".tee" / "design"

    def save(self, spec: dict[str, Any]) -> dict[str, Any]:
        validate(spec)
        name = str(spec.get("name") or "untitled").replace(" ", "_").lower()
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{name}.json"
        revision = 1
        previous = None
        if path.exists():
            previous = json.loads(path.read_text())
            revision = int(previous.get("_revision", 0)) + 1
        record = {
            **spec,
            "_revision": revision,
            "_saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        if previous is not None:
            history = self.root / "history"
            history.mkdir(exist_ok=True)
            (history / f"{name}.r{previous['_revision']}.json").write_text(
                json.dumps(previous, indent=1)
            )
        path.write_text(json.dumps(record, indent=1))
        out = {"name": name, "revision": revision}
        if previous is not None:
            out["changed_sections"] = diff_sections(previous, record)
        return out

    def load(self, name: str) -> dict[str, Any]:
        path = self.root / f"{str(name).replace(' ', '_').lower()}.json"
        if not path.exists():
            known = [p.stem for p in self.root.glob("*.json")] if self.root.exists() else []
            raise TeeError(
                "unknown_spec",
                f"No stored design spec '{name}'.",
                fix=f"Stored: {', '.join(known) or '(none)'}; save with gd_store.",
            )
        return json.loads(path.read_text())


def diff_sections(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    changed = []
    for section in SECTIONS:
        if json.dumps(old.get(section), sort_keys=True) != json.dumps(
            new.get(section), sort_keys=True
        ):
            changed.append(section)
    return changed
