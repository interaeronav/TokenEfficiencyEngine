"""Structural plausibility (A20): findings, never approvals.

The exposure line: FLAGGING against cited prescriptive tables restates
the code (what plans examiners do daily); APPROVING or SIZING would be
engineering practice. So: findings carry source + severity + the exact
delta; there is no member sizing and no "passes" state - a clean run
reports "no plausibility conflicts detected (N rules evaluated)".

Jurisdiction (A29). `region` selects the legal regime, and the regime
decides both WHICH table applies and HOW MUCH FORCE a finding may claim:

  US (default)        IRC. Unchanged behaviour.
  ZA                  SANS 10400 as the deemed-to-satisfy route under the
                      NBR Act 103 of 1977. CODE severity is legitimate.
  NA-local-authority  Namibia has NO national building act. SANS binds only
  NA-settlement       where that council incorporated it (LAA s 94B), which
  NA-communal         this checker cannot know; on communal land there is no
                      building control at all. So CODE is capped to STD:
                      professional standard of care, not law.
  NA-unresolved       Bare "NA"/"namibia". The regime is the FIRST question
                      and guessing it is the documented failure mode, so
                      nothing above HEUR is emitted until it is resolved.

Capping is visible, never silent: a capped finding carries
`severity_capped_from`, and `jurisdiction.legal_basis` states the reason
once for the whole response (repeating it per finding cost 2.5x the
payload for no added information - see benchmarks/RESULTS.md).

Model contract (assembled from plan facts + scene entities, or passed
directly): {"elements": [{id, class, ...}], "region": "US"}
Element classes and their fields:
  joist          {size: "2x8", span_m}
  slab           {span_m, depth_m}
  beam           {material: concrete|steel, span_m, depth_m}
  wall           {bearing: bool, material?, height_m, thickness_m,
                  stories?, level?, x_range?: [x0, x1], supports?: [ids]}
  opening        {wall: id, width_m, has_header: bool, sill_m?,
                  drop_outside_m?, openable?}
  lintel         {span_m, bearing_mm}
  footing        {width_m, wall: id, soil_bearing_kpa?}
  rafter         {has_tie_or_ridge: bool}
  roof           {covering, pitch_deg}
  stair          {riser_mm, tread_mm, headroom_mm, width_mm,
                  riser_variation_mm?}
  room           {ceiling_m, habitable: bool, area_m2?, min_dimension_m?}
  wet_room       {level, x_range}
  cantilever     {length_m, back_span_m}
  post           {supports: [ids], footing: id?}

The load-path graph (IRC R301.1: a "complete load path… to the
foundation"): elements declare `supports` edges (who carries me);
every bearing element must reach a footing/foundation node.
"""

from __future__ import annotations

import itertools
import json
import math
from functools import cache
from importlib import resources
from typing import Any

from tee.kernel.errors import TeeError

DISCLAIMER = (
    "Findings flag conflicts with cited prescriptive tables; they are not "
    "an engineering review, and absence of findings is not an approval. "
    "Spans or conditions outside prescriptive envelopes require design by "
    "a licensed engineer (IRC R301.1.3)."
)


# CONV < HEUR < STD < CODE. A regime's ceiling caps what any rule may claim.
_SEVERITY_ORDER = ("CONV", "HEUR", "STD", "CODE")

# Accepted spellings -> profile key. Deliberately NOT fuzzy: an unknown region
# is an error, and a bare "namibia" resolves to the unresolved regime rather
# than silently picking one of its three very different answers.
_REGION_ALIASES = {
    "us": "US",
    "usa": "US",
    "irc": "US",
    "": "US",
    "za": "ZA",
    "south-africa": "ZA",
    "south africa": "ZA",
    "rsa": "ZA",
    "sans": "ZA",
    "na": "NA-unresolved",
    "namibia": "NA-unresolved",
    "na-unresolved": "NA-unresolved",
    "na-local-authority": "NA-local-authority",
    "na-local": "NA-local-authority",
    "na-municipal": "NA-local-authority",
    "na-town": "NA-local-authority",
    "na-village": "NA-local-authority",
    "na-settlement": "NA-settlement",
    "na-communal": "NA-communal",
    "communal": "NA-communal",
}


def resolve_jurisdiction(region: Any) -> tuple[str, dict[str, Any]]:
    """Region string -> (profile key, profile). Unknown regions raise rather
    than defaulting: quietly checking a Namibian plan against the IRC is the
    failure this whole mechanism exists to prevent."""
    profiles = rules()["_jurisdiction_profiles"]
    key = _REGION_ALIASES.get(str(region or "US").strip().lower())
    if key is None:
        known = ", ".join(k for k in profiles if not k.startswith("_"))
        raise TeeError(
            "unknown_region",
            f"region '{region}' is not a known jurisdiction.",
            fix=f"Use one of: {known}. Namibia has three different regimes - "
            "'NA' alone resolves to NA-unresolved, which caps findings until "
            "you establish whether the site is in a proclaimed local authority, "
            "a declared settlement, or on communal land.",
        )
    return key, profiles[key]


def _resolved_table(table: dict[str, Any], rule_set: str) -> dict[str, Any]:
    """Fold each rule's `by_jurisdiction[rule_set]` overlay onto its base, and
    drop rules that belong to a different rule set entirely."""
    out: dict[str, Any] = {}
    for key, rule in table.items():
        if key.startswith("_") or not isinstance(rule, dict):
            out[key] = rule
            continue
        if rule.get("rule_set") and rule["rule_set"] != rule_set:
            continue
        variant = (rule.get("by_jurisdiction") or {}).get(rule_set)
        merged = {**rule, **variant} if variant else dict(rule)
        merged.pop("by_jurisdiction", None)
        out[key] = merged
    return out


@cache
def rules() -> dict[str, Any]:
    text = resources.files("tee.physical").joinpath("data/plaus_rules.json").read_text()
    return json.loads(text)


def check(model: dict[str, Any]) -> dict[str, Any]:
    region_key, profile = resolve_jurisdiction(model.get("region", "US"))
    rule_set = profile["rule_set"]
    table = _resolved_table(rules(), rule_set)
    ceiling = profile["max_severity"]
    ceiling_rank = _SEVERITY_ORDER.index(ceiling)
    elements = model.get("elements", [])
    by_id = {e.get("id"): e for e in elements if e.get("id")}
    findings: list[dict[str, Any]] = []
    evaluated = 0

    def hit(rule_key: str, element_id: Any, detail: str, *, severity=None, source=None):
        rule = table[rule_key]
        claimed = severity or rule["severity"]
        finding = {
            "rule": rule_key,
            "severity": claimed,
            "element": element_id,
            "detail": detail,
            "source": source or rule.get("source"),
        }
        findings.append(finding)

    for element in elements:
        cls = element.get("class")
        eid = element.get("id", "?")

        if cls == "joist":
            evaluated += 1
            rule = table["joist_span_max_m"]
            size = str(element.get("size", ""))
            limit = rule["spans"].get(size)
            span = float(element.get("span_m", 0))
            if limit is None:
                if size:
                    hit(
                        "joist_span_max_m",
                        eid,
                        f"size '{size}' not in the encoded table - not checkable",
                        severity="CONV",
                    )
            elif span > limit:
                hit(
                    "joist_span_max_m",
                    eid,
                    f"{size} spans {span:.2f} m; worst-grade envelope is "
                    f"{limit:.2f} m (delta +{span - limit:.2f} m) - "
                    f"{rule['finding']}",
                )

        elif cls == "slab":
            evaluated += 1
            rule = table["concrete_slab_min_depth"]
            span, depth = float(element.get("span_m", 0)), float(element.get("depth_m", 0))
            if depth > 0 and span / depth > rule["ratio_flag_below"]:
                hit(
                    "concrete_slab_min_depth",
                    eid,
                    f"span/depth = {span / depth:.0f} (> {rule['ratio_flag_below']}): "
                    f"{rule['finding']}",
                )

        elif cls == "beam":
            evaluated += 1
            material = element.get("material", "concrete")
            rule_key = "steel_beam_depth" if material == "steel" else "concrete_beam_min_depth"
            rule = table[rule_key]
            span, depth = float(element.get("span_m", 0)), float(element.get("depth_m", 0))
            if depth > 0 and span / depth > rule["ratio_flag_below"]:
                hit(
                    rule_key,
                    eid,
                    f"span/depth = {span / depth:.0f} (> {rule['ratio_flag_below']}): "
                    f"{rule['finding']}",
                )

        elif cls == "wall":
            if element.get("material") in ("brick", "masonry", "brick_masonry"):
                evaluated += 1
                rule = table["masonry_slenderness"]
                height = float(element.get("height_m", 0))
                thickness = float(element.get("thickness_m", 0))
                if thickness > 0 and height / thickness > rule["ratio_max"]:
                    hit(
                        "masonry_slenderness",
                        eid,
                        f"h/t = {height / thickness:.0f} (> {rule['ratio_max']}): "
                        f"{rule['finding']}",
                    )
                evaluated += 1
                rule = table["masonry_min_thickness_mm"]
                stories = int(element.get("stories", 1))
                minimum = rule["multi_story"] if stories > 1 else rule["one_story"]
                if element.get("bearing") and thickness * 1000 < minimum:
                    hit(
                        "masonry_min_thickness_mm",
                        eid,
                        f"{thickness * 1000:.0f} mm < {minimum} mm minimum: {rule['finding']}",
                    )

        elif cls == "opening":
            wall = by_id.get(element.get("wall"), {})
            if wall.get("bearing"):
                evaluated += 1
                if not element.get("has_header"):
                    hit(
                        "header_required",
                        eid,
                        f"opening ({element.get('width_m', '?')} m) in bearing wall "
                        f"'{wall.get('id')}': {table['header_required']['finding']}",
                    )
            if element.get("openable"):
                evaluated += 1
                rule = table["window_fall_protection"]
                sill = float(element.get("sill_m", 1)) * 1000
                drop = float(element.get("drop_outside_m", 0)) * 1000
                if sill < rule["sill_mm"] and drop > rule["drop_mm"]:
                    hit(
                        "window_fall_protection",
                        eid,
                        f"sill {sill:.0f} mm with {drop:.0f} mm drop: {rule['finding']}",
                    )

        elif cls == "lintel":
            evaluated += 1
            rule = table["lintel_bearing_min_mm"]
            span = float(element.get("span_m", 0))
            bearing = float(element.get("bearing_mm", 0))
            required = next((mm for max_span, mm in rule["by_span_m"] if span <= max_span), 200)
            if bearing < required:
                hit(
                    "lintel_bearing_min_mm",
                    eid,
                    f"bearing {bearing:.0f} mm < {required} mm for a "
                    f"{span:.2f} m span: {rule['finding']}",
                )

        elif cls == "footing":
            evaluated += 1
            wall = by_id.get(element.get("wall"), {})
            wall_thickness = float(wall.get("thickness_m", 0))
            if wall_thickness and float(element.get("width_m", 0)) < wall_thickness:
                hit(
                    "footing_width",
                    eid,
                    f"footing {element.get('width_m')} m under a "
                    f"{wall_thickness} m wall: {table['footing_width']['finding']}",
                )
            soil = element.get("soil_bearing_kpa")
            if soil is not None:
                evaluated += 1
                rule = table["soil_bearing_min_kpa"]
                if float(soil) < rule["value"]:
                    hit(
                        "soil_bearing_min_kpa",
                        eid,
                        f"declared {soil} kPa < {rule['value']} kPa: {rule['finding']}",
                    )

        elif cls == "rafter":
            evaluated += 1
            if not element.get("has_tie_or_ridge"):
                hit("rafter_tie_topology", eid, table["rafter_tie_topology"]["finding"])

        elif cls == "roof":
            evaluated += 1
            rule = table["roof_pitch_min_deg"]
            covering = str(element.get("covering", "asphalt_shingle"))
            entry = rule["source_by_covering"].get(covering)
            pitch = float(element.get("pitch_deg", 0))
            if entry and pitch < entry["min_deg"]:
                hit(
                    "roof_pitch_min_deg",
                    eid,
                    f"{covering} at {pitch:.1f} deg < {entry['min_deg']} deg "
                    f"minimum (delta -{entry['min_deg'] - pitch:.1f} deg): "
                    f"{rule['finding']}",
                    source=entry["source"],
                )

        elif cls == "stair":
            rule = table["stairs"]
            riser = float(element.get("riser_mm", 0))
            tread = float(element.get("tread_mm", 999))
            evaluated += 4
            if riser > rule["riser_max_mm"]:
                hit("stairs", eid, f"riser {riser:.0f} mm > {rule['riser_max_mm']} mm")
            if tread < rule["tread_min_mm"]:
                hit("stairs", eid, f"tread {tread:.0f} mm < {rule['tread_min_mm']} mm")
            if float(element.get("headroom_mm", 9999)) < rule["headroom_min_mm"]:
                hit("stairs", eid, f"headroom < {rule['headroom_min_mm']} mm")
            if float(element.get("width_mm", 9999)) < rule["width_min_mm"]:
                hit("stairs", eid, f"width < {rule['width_min_mm']} mm")
            blondel = 2 * riser + tread
            if (
                riser
                and tread
                and not (
                    rule["blondel"]["range_mm"][0] <= blondel <= rule["blondel"]["range_mm"][1]
                )
            ):
                hit(
                    "stairs",
                    eid,
                    f"2R+G = {blondel:.0f} mm outside {rule['blondel']['range_mm']} "
                    "(Blondel comfort convention)",
                    severity="CONV",
                    source=rule["blondel"]["source"],
                )
            variation = element.get("riser_variation_mm")
            if variation is not None and "sans_stair_riser_variation" in table:
                evaluated += 1
                vrule = table["sans_stair_riser_variation"]
                if float(variation) > vrule["max_variation_mm"]:
                    hit(
                        "sans_stair_riser_variation",
                        eid,
                        f"riser/going variation {float(variation):.0f} mm > "
                        f"{vrule['max_variation_mm']} mm within one flight: "
                        f"{vrule['finding']}",
                    )

        elif cls == "room":
            if element.get("habitable", True):
                evaluated += 1
                rule = table["ceiling_min_mm"]
                room_height = float(element.get("ceiling_m", 99)) * 1000
                if room_height < rule["value"]:
                    hit(
                        "ceiling_min_mm",
                        eid,
                        f"ceiling {room_height:.0f} mm < {rule['value']} mm: {rule['finding']}",
                    )
                if "sans_room_min_area" in table:
                    rrule = table["sans_room_min_area"]
                    area = element.get("area_m2")
                    if area is not None:
                        evaluated += 1
                        if float(area) < rrule["min_area_m2"]:
                            hit(
                                "sans_room_min_area",
                                eid,
                                f"habitable room {float(area):.2f} m2 < "
                                f"{rrule['min_area_m2']} m2: {rrule['finding']}",
                            )
                    narrowest = element.get("min_dimension_m")
                    if narrowest is not None:
                        evaluated += 1
                        if float(narrowest) < rrule["min_dimension_m"]:
                            hit(
                                "sans_room_min_area",
                                eid,
                                f"narrowest plan dimension {float(narrowest):.2f} m < "
                                f"{rrule['min_dimension_m']} m: {rrule['finding']}",
                            )

        elif cls == "cantilever":
            evaluated += 1
            rule = table["cantilever_ratio"]
            length = float(element.get("length_m", 0))
            back = float(element.get("back_span_m", 0))
            if back > 0 and length / back > rule["back_span_ratio_max"]:
                hit(
                    "cantilever_ratio",
                    eid,
                    f"cantilever {length:.2f} m over back-span {back:.2f} m "
                    f"(ratio {length / back:.2f} > {rule['back_span_ratio_max']}): "
                    f"{rule['finding']}",
                )

    findings.extend(_load_path(elements, by_id, table))
    evaluated += 1  # the graph check
    findings.extend(_wet_walls(elements, table))
    evaluated += 1

    # Legal force is jurisdictional. Where the regime has adopted no code, a
    # CODE-severity rule is professional standard of care, not law - and the
    # downgrade is stated, never silent. This runs over the assembled list,
    # not inside hit(), because _load_path and _wet_walls build findings
    # directly: capping in hit() alone let load_path claim CODE force on
    # communal land while the same response said nothing above STD applied.
    for finding in findings:
        claimed = finding["severity"]
        if _SEVERITY_ORDER.index(claimed) > ceiling_rank:
            finding["severity"] = ceiling
            finding["severity_capped_from"] = claimed

    jurisdiction: dict[str, Any] = {
        "region": region_key,
        "label": profile["label"],
        "rule_set": rule_set,
        "max_severity": ceiling,
        "legal_basis": profile["legal_basis"],
    }
    if profile.get("advisory"):
        jurisdiction["advisory"] = profile["advisory"]
    if profile.get("source"):
        jurisdiction["source"] = profile["source"]
    capped = sum(1 for f in findings if "severity_capped_from" in f)
    if capped:
        jurisdiction["capped_findings"] = capped

    out: dict[str, Any] = {
        "findings": findings,
        "rules_evaluated": evaluated,
        "jurisdiction": jurisdiction,
        "disclaimer": DISCLAIMER,
    }
    if not findings:
        out["summary"] = f"no plausibility conflicts detected ({evaluated} rules evaluated)"
    return out


def _load_path(
    elements: list[dict[str, Any]], by_id: dict[Any, dict[str, Any]], table: dict[str, Any]
) -> list[dict[str, Any]]:
    """IRC R301.1 reachability: every bearing element must reach a footing
    through `supports` edges (who carries me)."""
    findings = []
    foundations = {e["id"] for e in elements if e.get("class") in ("footing", "foundation")}
    bearing = [
        e
        for e in elements
        if e.get("class") in ("wall", "beam", "post", "joist", "rafter")
        and (e.get("bearing") or e.get("class") in ("beam", "post"))
    ]
    for element in bearing:
        seen: set[Any] = set()
        stack = [element["id"]]
        reached = False
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            if node in foundations:
                reached = True
                break
            for supporter in by_id.get(node, {}).get("supports", []):
                stack.append(supporter)
        # also: anything that supports this element (edges may be stated
        # from either side)
        if not reached:
            carriers = [e["id"] for e in elements if element["id"] in (e.get("carries") or [])]
            stack = carriers
            while stack:
                node = stack.pop()
                if node in seen:
                    continue
                seen.add(node)
                if node in foundations:
                    reached = True
                    break
                stack.extend(e["id"] for e in elements if node in (e.get("carries") or []))
        if not reached and foundations:
            findings.append(
                {
                    "rule": "load_path",
                    "severity": "CODE",
                    "element": element["id"],
                    "detail": "LOAD_PATH_BROKEN: no support chain reaches a "
                    "foundation (IRC R301.1 requires a complete load path to "
                    "the foundation)",
                    "source": "IRC R301.1",
                }
            )
    return findings


def _wet_walls(elements: list[dict[str, Any]], table: dict[str, Any]) -> list[dict[str, Any]]:
    wet = [e for e in elements if e.get("class") == "wet_room"]
    findings = []
    by_level: dict[Any, list[dict[str, Any]]] = {}
    for room in wet:
        by_level.setdefault(room.get("level", 0), []).append(room)
    levels = sorted(by_level)
    for lower, upper in itertools.pairwise(levels):
        for room in by_level[upper]:
            x0, x1 = room.get("x_range", [0, 0])
            aligned = any(
                _ranges_overlap((x0, x1), tuple(other.get("x_range", [0, 0])))
                for other in by_level[lower]
            )
            if not aligned:
                findings.append(
                    {
                        "rule": "wet_wall_stacking",
                        "severity": "CONV",
                        "element": room.get("id"),
                        "detail": table["wet_wall_stacking"]["finding"],
                        "source": table["wet_wall_stacking"]["source"],
                    }
                )
    return findings


def _ranges_overlap(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return min(a[1], b[1]) - max(a[0], b[0]) > -0.5  # within half a meter counts


def pitch_from_rise_run(rise: float, run: float) -> float:
    return math.degrees(math.atan2(rise, run))
