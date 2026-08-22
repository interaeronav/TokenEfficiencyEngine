"""The verification battery (A17): deterministic checkers, cost-ordered.

LLM proposes, this module verifies. Every finding is one line + the fix.
The only token-spending checker (bounded self-play) is split into a
prepare/score pair so the transcript is produced in-band by the host
model and scored deterministically here.
"""

from __future__ import annotations

import itertools
from typing import Any

from tee.design import tables

Finding = dict[str, Any]


def _finding(code: str, message: str, fix: str, **extra: Any) -> Finding:
    return {"code": code, "message": message, "fix": fix, **extra}


# -- 1. design lint ---------------------------------------------------------


def lint(spec: dict[str, Any]) -> dict[str, Any]:
    findings: list[Finding] = []
    core = spec.get("core_loop", {})
    if not core.get("verbs"):
        findings.append(_finding(
            "no_verbs", "core loop defines no player verbs",
            "add core_loop.verbs (what does the player DO?)",
        ))
    if not core.get("steps"):
        findings.append(_finding(
            "no_loop_steps", "core loop has no steps",
            "add core_loop.steps with target durations",
        ))
    if not core.get("failure_state"):
        findings.append(_finding(
            "no_failure_state", "core loop lacks a failure state",
            "state what failure means and what it costs (keep retry <30 s)",
        ))
    if not core.get("session_end_hook"):
        findings.append(_finding(
            "no_session_end_hook", "no session-end hook",
            "add core_loop.session_end_hook - the reason to come back "
            "(the first session is the funnel: day-0 average is 1.65 sessions)",
        ))

    economy = spec.get("economy") or {}
    nodes = economy.get("nodes", [])
    for currency in economy.get("currencies", []):
        has_faucet = any(
            n for n in nodes
            if (n["kind"] == "faucet" and n.get("currency") == currency)
            or (n["kind"] == "converter" and n.get("to") == currency)
        )
        has_sink = any(
            n for n in nodes
            if (n["kind"] == "sink" and n.get("currency") == currency)
            or (n["kind"] == "converter" and n.get("from") == currency)
        )
        if has_faucet and not has_sink:
            findings.append(_finding(
                "dead_currency", f"currency '{currency}' has faucets but no sink",
                f"add a sink for '{currency}' (consumables are intrinsic sinks) "
                "or remove the currency",
            ))
        if has_sink and not has_faucet:
            findings.append(_finding(
                "starved_currency", f"currency '{currency}' has sinks but no faucet",
                f"add a faucet for '{currency}' or remove it",
            ))

    taught, teach_order = _teach_map(spec)
    beats = (spec.get("level_macro") or {}).get("beats", [])
    composed: set[str] = set()
    for i, beat in enumerate(beats):
        mechanics = beat.get("mechanics", [])
        if len(mechanics) >= 2:
            composed.update(mechanics)
        for mechanic in mechanics:
            if mechanic in taught and teach_order[mechanic] > i + 1:
                findings.append(_finding(
                    "used_before_taught",
                    f"beat {i + 1} uses '{mechanic}' taught only at unlock "
                    f"position {teach_order[mechanic]}",
                    f"move the '{mechanic}' unlock before beat {i + 1} or the "
                    "beat later (teach-test-compose)",
                ))
    for mechanic in sorted(taught - composed):
        if beats:
            findings.append(_finding(
                "taught_never_composed",
                f"mechanic '{mechanic}' is taught but never composed with another",
                f"add a beat combining '{mechanic}' with another mechanic "
                "(isolate then combine - the Portal pattern)",
            ))
    for i in range(1, len(beats)):
        prev = float(beats[i - 1].get("intensity", 0) or 0)
        cur = float(beats[i].get("intensity", 0) or 0)
        if cur - prev > 3:
            findings.append(_finding(
                "intensity_spike",
                f"intensity jumps {prev:g}->{cur:g} at beat {i + 1}",
                "smooth the curve or insert a teaching/breather beat",
            ))
    content_classes = {c.get("class") for c in spec.get("content_list", [])}
    for i, beat in enumerate(beats):
        for cls in beat.get("content_classes", []):
            if cls not in content_classes:
                findings.append(_finding(
                    "missing_content_class",
                    f"beat {i + 1} references content class '{cls}' absent from "
                    "content_list",
                    f"add a content_list entry for '{cls}' or drop the reference",
                ))

    meta = spec.get("meta", {})
    comparables = meta.get("comparables", [])
    if len(comparables) < 3:
        findings.append(_finding(
            "underdifferentiated",
            f"only {len(comparables)} comparable(s) named (3 required)",
            "name 3 comparables from the market tables and state each delta "
            "(differentiation is forced, not hoped for)",
        ))
    elif any(not c.get("delta") for c in comparables):
        findings.append(_finding(
            "comparable_without_delta",
            "a comparable lacks its delta ('like X but ...')",
            "state what this design does differently from each comparable",
        ))
    motivations = meta.get("audience", {}).get("motivations", {})
    age = meta.get("audience", {}).get("age_range", [])
    if (
        motivations.get("competition", 0) >= 0.7
        and age and age[0] >= 35
        and not meta.get("audience", {}).get("depth_note")
    ):
        findings.append(_finding(
            "audience_contradiction",
            "competitive core aimed at 35+ (competition declines steepest 13->35; "
            "age explains >2x gender's variance)",
            "lower the competition weight, target younger, or add "
            "audience.depth_note explaining the age-tolerant depth "
            "(strategy is the age-stable dimension)",
        ))
    return {"findings": findings, "checked": True}


def _teach_map(spec: dict[str, Any]) -> tuple[set[str], dict[str, int]]:
    taught: set[str] = set()
    order: dict[str, int] = {}
    for unlock in (spec.get("progression") or {}).get("unlocks", []):
        mechanic = unlock.get("teaches")
        if mechanic:
            taught.add(mechanic)
            position = unlock.get("at")
            order[mechanic] = int(position) if isinstance(position, int | float) else 1
    return taught, order


# -- 2. scope estimate ------------------------------------------------------


def scope_estimate(
    spec: dict[str, Any], *, team_size: int | None = None, weeks: int | None = None
) -> dict[str, Any]:
    weights = tables.scope_weights()
    low = high = 0.0
    rows = []
    for entry in spec.get("content_list", []):
        cls = entry.get("class")
        count = int(entry.get("count", 0))
        reuse = float(entry.get("reuse", 0.0))  # 0..1 share reused/instanced
        band = weights.get(cls, [1, 2])
        effective = count * (1.0 - 0.7 * reuse)  # reuse discounts, never zeroes
        row_low, row_high = effective * band[0], effective * band[1]
        low += row_low
        high += row_high
        rows.append({"class": cls, "count": count, "days": [round(row_low, 1), round(row_high, 1)]})
    out: dict[str, Any] = {
        "person_days": [round(low, 1), round(high, 1)],
        "rows": rows,
        "note": "bands are estimated practitioner ranges (economy_archetypes.json)",
    }
    meta_team = (spec.get("meta") or {}).get("team_size")
    team = team_size or meta_team
    if team and weeks:
        capacity = team * weeks * 5
        out["capacity_days"] = capacity
        if low > capacity:
            out["flag"] = (
                f"even the LOW estimate ({low:.0f} pd) exceeds capacity "
                f"({capacity} pd) - cut content_list or extend the schedule"
            )
        elif high > capacity * 1.5:
            out["flag"] = (
                f"HIGH estimate ({high:.0f} pd) is >1.5x capacity - scope risk"
            )
    return out


# -- 3. economy simulation --------------------------------------------------


def economy_sim(spec: dict[str, Any], *, days: int = 90) -> dict[str, Any]:
    economy = spec.get("economy") or {}
    currencies = list(economy.get("currencies", []))
    nodes = economy.get("nodes", [])
    personas = economy.get("personas") or tables.personas_default()
    flags: list[Finding] = []
    per_currency: dict[str, Any] = {}
    archetype_name = economy.get("archetype")
    band = None
    if archetype_name:
        band = tables.archetype(archetype_name).get("sink_faucet_ratio_band")

    for currency in currencies:
        series_by_persona = {}
        ratio_by_persona = {}
        for persona_name, persona in personas.items():
            sessions_per_day = persona.get("sessions_per_week", 7) / 7.0
            engagement = float(persona.get("engagement", 1.0))
            supply = 0.0
            series = []
            total_faucet = total_sink = 0.0
            for _day in range(days):
                inflow = outflow = 0.0
                for node in nodes:
                    rate = float(node.get("rate", 0)) * sessions_per_day * engagement
                    if node["kind"] == "faucet" and node.get("currency") == currency:
                        inflow += rate
                    elif node["kind"] == "sink" and node.get("currency") == currency:
                        outflow += rate
                    elif node["kind"] == "converter":
                        if node.get("from") == currency:
                            outflow += rate
                        elif node.get("to") == currency:
                            inflow += rate * float(node.get("ratio", 1.0))
                outflow = min(outflow, supply + inflow)  # cannot spend what you lack
                supply += inflow - outflow
                total_faucet += inflow
                total_sink += outflow
                series.append(supply)
            series_by_persona[persona_name] = series
            ratio_by_persona[persona_name] = (
                total_sink / total_faucet if total_faucet > 0 else None
            )
        # inflation: second-half accumulation rate vs first half
        for persona_name, series in series_by_persona.items():
            half = days // 2
            first = series[half - 1] - series[0]
            second = series[-1] - series[half]
            if second > 0 and first > 0 and second > first * 1.3:
                flags.append(_finding(
                    "inflation",
                    f"'{currency}' supply accelerates for persona "
                    f"'{persona_name}' ({first:.0f} -> {second:.0f} per half)",
                    f"add or strengthen a '{currency}' sink (consumables, "
                    "upkeep, resets) - faucets are outrunning sinks",
                ))
                break
        ratios = [r for r in ratio_by_persona.values() if r is not None]
        mean_ratio = sum(ratios) / len(ratios) if ratios else None
        if band and mean_ratio is not None and not (band[0] <= mean_ratio <= band[1]):
            direction = "below" if mean_ratio < band[0] else "above"
            flags.append(_finding(
                "archetype_band",
                f"'{currency}' sink/faucet ratio {mean_ratio:.2f} is {direction} "
                f"the {archetype_name} band {band}",
                f"add/strengthen a '{currency}' sink or reduce its faucets "
                f"toward the {archetype_name} band"
                if direction == "below"
                else f"loosen '{currency}' sinks or raise its faucets toward "
                f"the {archetype_name} band",
            ))
        per_currency[currency] = {
            "final_supply": {
                p: round(s[-1], 1) for p, s in series_by_persona.items()
            },
            "sink_faucet_ratio": {
                p: round(r, 3) if r is not None else None
                for p, r in ratio_by_persona.items()
            },
        }
    return {"days": days, "currencies": per_currency, "flags": flags}


# -- 4. progression validator ----------------------------------------------


def progression_check(spec: dict[str, Any]) -> dict[str, Any]:
    progression = spec.get("progression") or {}
    unlocks = progression.get("unlocks", [])
    findings: list[Finding] = []
    ordered = [u for u in unlocks if isinstance(u.get("at"), int | float)]
    ordered.sort(key=lambda u: u["at"])
    for prev, cur in itertools.pairwise(ordered):
        d_prev = float(prev.get("difficulty", 0) or 0)
        d_cur = float(cur.get("difficulty", 0) or 0)
        if d_cur < d_prev - 1:
            findings.append(_finding(
                "difficulty_regression",
                f"difficulty drops {d_prev:g}->{d_cur:g} at '{cur.get('id')}'",
                "reorder unlocks or adjust difficulty (monotone within -1)",
            ))
        if d_cur - d_prev > 3:
            findings.append(_finding(
                "difficulty_spike",
                f"difficulty jumps {d_prev:g}->{d_cur:g} at '{cur.get('id')}'",
                "insert an intermediate unlock or smooth the ramp",
            ))
    gaps = [b["at"] - a["at"] for a, b in itertools.pairwise(ordered)]
    if gaps:
        median_gap = sorted(gaps)[len(gaps) // 2]
        for a, b, gap in zip(ordered, ordered[1:], gaps, strict=False):
            if median_gap > 0 and gap > 5 * median_gap:
                findings.append(_finding(
                    "unlock_desert",
                    f"gap {gap:g} between '{a.get('id')}' and '{b.get('id')}' "
                    f"is >5x the median gap ({median_gap:g})",
                    "add an unlock/reward inside the desert",
                ))
    pity = progression.get("pity")
    if pity:
        expected = _pity_expected(pity)
        findings.extend(_pity_findings(pity, expected))
    return {"findings": findings, "unlocks": len(unlocks)}


def _pity_expected(pity: dict[str, Any]) -> float | None:
    base = float(pity.get("base", 0))
    soft = pity.get("soft_start")
    increment = float(pity.get("increment", 0))
    hard = pity.get("hard")
    if not hard or base <= 0:
        return None
    survive = 1.0
    expected = 0.0
    for n in range(1, int(hard) + 1):
        p = base
        if soft is not None and n >= int(soft):
            p = min(1.0, base + increment * (n - int(soft) + 1))
        if n == int(hard):
            p = 1.0
        expected += n * survive * p
        survive *= 1 - p
    return expected


def _pity_findings(pity: dict[str, Any], expected: float | None) -> list[Finding]:
    findings: list[Finding] = []
    if not pity.get("hard"):
        findings.append(_finding(
            "pity_no_hard", "pity system has no hard ceiling",
            "add a hard pity (guaranteed at N) - unbounded bad-luck tails "
            "are a documented harm vector",
        ))
    if expected is not None:
        findings_note = pity.get("expected_pulls")
        if findings_note and abs(expected - float(findings_note)) > 0.2 * expected:
            findings.append(_finding(
                "pity_math",
                f"declared expected_pulls {findings_note} vs computed "
                f"{expected:.1f} from the hazard function",
                "fix the parameters or the declaration",
            ))
    if not pity.get("disclosed"):
        findings.append(_finding(
            "pity_undisclosed", "pity parameters not disclosed to players",
            "set progression.pity.disclosed=true and publish rates "
            "(guideline; odds disclosure itself is code-severity in ethics)",
        ))
    return findings


# -- 5. ethics / dark patterns ---------------------------------------------


def ethics_check(spec: dict[str, Any]) -> dict[str, Any]:
    rules = tables.load("dark_patterns")["rules"]
    monetization = spec.get("monetization") or {}
    meta = spec.get("meta") or {}
    routine = spec.get("routine") or {}
    min_age = meta.get("min_age")
    minors_reachable = min_age is None or int(min_age) < 18

    violations: list[Finding] = []
    warnings: list[Finding] = []

    def hit(rule_id: str, detail: str):
        rule = rules[rule_id]
        entry = _finding(
            rule_id, detail, rule["fix"],
            severity=rule["severity"], jurisdictions=rule["jurisdictions"],
        )
        (violations if rule["severity"] == "code" else warnings).append(entry)

    loot = bool(monetization.get("loot_boxes"))
    if loot and minors_reachable:
        hit(
            "loot_box_minors",
            f"paid loot boxes with min_age={min_age!r} (minors reachable)",
        )
    if loot and not monetization.get("odds_disclosed"):
        hit("odds_disclosure", "paid random rewards without disclosed odds")
    if loot:
        hit("loot_box_spend_link", "paid loot boxes present (general-audience risk)")
    if int(monetization.get("currency_hops", 0) or 0) > 1:
        hit(
            "multi_hop_currency",
            f"{monetization['currency_hops']} conversions between money and item",
        )
    if monetization.get("virtual_currency") and not monetization.get("real_price_display"):
        hit("real_price_display", "virtual-currency prices without real-money display")
    if monetization.get("countdown_offers") and minors_reachable:
        hit("countdown_minors", "countdown offers with minors reachable")
    streak = routine.get("streak")
    if streak is not None and (
        int(streak.get("grace_days", 0) or 0) < 1 or streak.get("paid_repair_only")
    ):
        hit("streak_no_grace", "streak without free grace/repair")
    if routine.get("absence_penalty"):
        hit("absence_punishment", f"absence penalty: {routine['absence_penalty']}")
    if monetization.get("binge_offers"):
        hit("binge_upsell", "offers triggered by long-session detection")
    pity = (spec.get("progression") or {}).get("pity")
    if pity and not pity.get("disclosed"):
        hit("gacha_pity_hidden", "pity parameters hidden from players")

    return {
        "hard_fail": bool(violations),
        "violations": violations,
        "warnings": warnings,
        "note": "code rows are grounded in live enforcement and are never "
        "relaxable; guideline rows need a recorded justification",
    }


# -- 6. bounded self-play (prepare in-band, score deterministically) --------


def selfplay_prepare(spec: dict[str, Any], *, turns: int = 8) -> dict[str, Any]:
    core = spec.get("core_loop", {})
    verbs = core.get("verbs", [])
    steps = [s["action"] for s in core.get("steps", [])]
    return {
        "turns": turns,
        "verbs": verbs,
        "loop": steps,
        "failure_state": core.get("failure_state"),
        "instructions": (
            f"Play {turns} turns of this design as a new player. Each turn, "
            "pick ONE verb from `verbs`, say what you do and what you expect "
            "to happen, then note whether you faced a real decision "
            "(alternatives you weighed) or a forced move. Output JSON: "
            '[{"turn": 1, "verb": "...", "action": "...", '
            '"decision": true|false, "alternatives": ["..."]}]. Be honest - '
            "a spec with no decisions must read as boring here."
        ),
    }


def selfplay_score(spec: dict[str, Any], transcript: list[dict[str, Any]]) -> dict[str, Any]:
    verbs = set((spec.get("core_loop") or {}).get("verbs", []))
    used = [t.get("verb") for t in transcript if t.get("verb")]
    distinct = {v for v in used if v in verbs}
    off_spec = sorted({v for v in used if v not in verbs})
    decisions = sum(1 for t in transcript if t.get("decision"))
    findings: list[Finding] = []
    if len(distinct) < 2:
        findings.append(_finding(
            "no_decision_loop",
            f"self-play used {len(distinct)} distinct spec verb(s) over "
            f"{len(transcript)} turns",
            "the loop offers no meaningful choice - add a second viable verb "
            "or interleave loop steps with choices",
        ))
    if transcript and decisions < len(transcript) * 0.4:
        findings.append(_finding(
            "forced_moves",
            f"only {decisions}/{len(transcript)} turns involved a real decision",
            "add resource tension or alternative routes so turns are choices",
        ))
    if off_spec:
        findings.append(_finding(
            "off_spec_verbs",
            f"self-play invented verbs not in the spec: {off_spec}",
            "either add them to core_loop.verbs or tighten the spec",
        ))
    return {
        "turns": len(transcript),
        "distinct_verbs": sorted(distinct),
        "decision_share": round(decisions / len(transcript), 2) if transcript else 0.0,
        "findings": findings,
    }


# -- the battery ------------------------------------------------------------


def run_battery(spec: dict[str, Any], *, days: int = 90) -> dict[str, Any]:
    """Cost-ordered: lint -> scope -> economy -> progression -> ethics.
    (Self-play is prepare/score, driven by the host model.) Stops nothing:
    all results come back at once - one round-trip."""
    from tee.design.spec import validate

    validate(spec)
    lint_result = lint(spec)
    scope = scope_estimate(spec)
    economy = economy_sim(spec, days=days)
    progression = progression_check(spec)
    ethics = ethics_check(spec)
    total = (
        len(lint_result["findings"]) + len(economy["flags"])
        + len(progression["findings"]) + len(ethics["violations"])
        + len(ethics["warnings"])
    )
    return {
        "lint": lint_result["findings"],
        "scope": scope,
        "economy": economy,
        "progression": progression["findings"],
        "ethics": ethics,
        "hard_fail": ethics["hard_fail"],
        "total_findings": total,
        "verdict": (
            "HARD FAIL (code-severity ethics violations)" if ethics["hard_fail"]
            else f"{total} finding(s)" if total else "all checkers pass"
        ),
    }
