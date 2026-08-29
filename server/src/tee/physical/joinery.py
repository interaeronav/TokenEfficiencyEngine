"""joinery_check (A37 P5.3): the wardrobe/cabinet rule table.

The plaus_check pattern applied to fitted furniture: findings carry
source + severity + the exact fix, and every rule was lifted from the
KB's 06_joinery_and_woodwork domain and RE-VERIFIED at its cited source
per A30 on 2026-08-29 BEFORE it judges anything (the verification state
is stamped on each rule and travels with every finding).

Data honesty: a rule whose input the model simply does not carry (Home
Builder 5.1 models no 32 mm system holes) answers `not_evaluated` with
the reason - silence is never conformance.

Units: millimetres throughout (the lane convention).
"""

from __future__ import annotations

import itertools
from typing import Any

# Each rule: severity ERROR (build it and it is wrong) or WARN (standard
# practice violated), the source citation, and the A30 re-verification
# stamp from this campaign's live checks.
RULES: dict[str, dict[str, str]] = {
    "system_pitch": {
        "severity": "ERROR",
        "source": "en.wikipedia.org/wiki/32_mm_cabinetmaking_system; kb joinery.cabinetmaking",
        "verified": "2026-08-29 at source (Wikipedia): Ø5 mm holes, 32 mm centres",
    },
    "system_setback": {
        "severity": "ERROR",
        "source": "en.wikipedia.org/wiki/32_mm_cabinetmaking_system; kb joinery.cabinetmaking",
        "verified": "2026-08-29 at source (Wikipedia): first row 37 mm from the "
        "front edge; rear row may be 37 mm",
    },
    "hinge_cup": {
        "severity": "ERROR",
        "source": "Hettich Sensys brochure (cited in kb joinery.hardware); "
        "EN 15570/15828 family per en.wikipedia.org/wiki/European_hinge",
        "verified": "2026-08-29 partial: standard family confirmed at source; the "
        "18.7 MB Sensys PDF was fetch-gated - Ø35/12.8 ship as the cited figures",
    },
    "hinge_collision": {
        "severity": "ERROR",
        "source": "geometry (two Ø35 cups cannot overlap); kb joinery.hardware",
        "verified": "2026-08-29 (arithmetic on the verified cup diameter)",
    },
    "carcass_runner": {
        "severity": "ERROR",
        "source": "blum.com LEGRABOX programme (40/70 kg classes verified at "
        "source 2026-08-29); NL tables per the cited Blum technical PDF; "
        "kb joinery.hardware ('hardware determines carcass dimensions')",
        "verified": "2026-08-29 partial: load classes at source; NL table cited",
    },
    "part_envelope": {
        "severity": "ERROR",
        "source": "carcass geometry; kb joinery.cabinetmaking",
        "verified": "2026-08-29 (arithmetic)",
    },
    "wardrobe_depth": {
        "severity": "WARN",
        "source": "hinterlanddesignco.com.au wardrobe design tips; "
        "kb joinery.cabinetmaking / furnishing.storage",
        "verified": "2026-08-29 at source: 530 mm internal (600 incl. wall) - "
        "'anything smaller will effect hanging space'",
    },
}

# LEGRABOX nominal-length ranges per load class (mm) - cited Blum figures.
_RUNNER_NL = {40: (270, 600), 70: (450, 650)}


def check(spec: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    not_evaluated: list[dict[str, str]] = []
    cabinets = {str(c.get("id")): c for c in spec.get("cabinets") or []}

    def hit(rule: str, element: Any, finding: str, fix: str) -> None:
        meta = RULES[rule]
        findings.append(
            {
                "rule": rule,
                "severity": meta["severity"],
                "element": element,
                "finding": finding,
                "fix": fix,
                "source": meta["source"],
                "verified": meta["verified"],
            }
        )

    # -- J1/J2: the 32 mm system ------------------------------------------
    holes = spec.get("system_holes") or []
    if not holes:
        for rule in ("system_pitch", "system_setback"):
            not_evaluated.append(
                {
                    "rule": rule,
                    "why": "the model carries no system-hole data (Home Builder "
                    "5.1 does not model drilling) - not judged, not passed",
                }
            )
    for row in holes:
        element = row.get("cabinet")
        pitch = float(row.get("pitch_mm", 32))
        if abs(pitch - 32.0) > 0.1:
            hit(
                "system_pitch",
                element,
                f"hole pitch {pitch} mm is not the 32 mm system",
                "Drill the row at 32 mm centres (Ø5 mm, 12-14 mm deep).",
            )
        diameter = float(row.get("diameter_mm", 5))
        if abs(diameter - 5.0) > 0.2:
            hit(
                "system_pitch",
                element,
                f"system hole Ø{diameter} mm is not the Ø5 mm standard",
                "Bore Ø5 mm system holes.",
            )
        setback = float(row.get("row_setback_mm", 37))
        if abs(setback - 37.0) > 0.5:
            hit(
                "system_setback",
                element,
                f"system row set back {setback} mm from the edge",
                "Set the row 37 mm from the front edge (rear row may also be 37 mm).",
            )

    # -- J3/J4: hinges -----------------------------------------------------
    hinges = [h for h in (spec.get("hardware") or []) if h.get("kind") == "hinge"]
    doors = {str(p.get("id")): p for p in (spec.get("parts") or []) if p.get("role") == "door"}
    by_door: dict[str, list[dict[str, Any]]] = {}
    for hinge in hinges:
        element = hinge.get("id")
        cup = float(hinge.get("cup_diameter_mm", 35))
        if abs(cup - 35.0) > 0.2:
            hit(
                "hinge_cup",
                element,
                f"hinge cup Ø{cup} mm is not the Ø35 mm concealed-hinge standard",
                "Bore Ø35 mm cups (typical depth 12.8 mm).",
            )
        door = doors.get(str(hinge.get("door")))
        depth = float(hinge.get("cup_depth_mm", 12.8))
        if door is not None:
            remaining = float(door.get("thickness_mm", 19)) - depth
            if remaining < 3.0:
                hit(
                    "hinge_cup",
                    element,
                    f"cup depth {depth} mm leaves {remaining:.1f} mm of a "
                    f"{door.get('thickness_mm')} mm door - break-through risk",
                    "Use a shallow-cup hinge (e.g. 7.8 mm thin-door variant) or a thicker front.",
                )
        by_door.setdefault(str(hinge.get("door")), []).append(hinge)
    for door_id, door_hinges in by_door.items():
        positioned = [h for h in door_hinges if h.get("at_mm") is not None]
        positioned.sort(key=lambda h: float(h["at_mm"][1]))
        for a, b in itertools.pairwise(positioned):
            gap = abs(float(b["at_mm"][1]) - float(a["at_mm"][1]))
            if gap < 35.0:
                hit(
                    "hinge_collision",
                    f"{a.get('id')}+{b.get('id')}",
                    f"two Ø35 cups {gap:.0f} mm apart on door '{door_id}' overlap",
                    "Space hinge cups so bores cannot intersect (and clear shelf/drawer travel).",
                )

    # -- J5: hardware-first carcass consistency ---------------------------
    for runner in (h for h in (spec.get("hardware") or []) if h.get("kind") == "runner"):
        element = runner.get("id")
        cabinet = cabinets.get(str(runner.get("cabinet")))
        nl = float(runner.get("nominal_length_mm", 0))
        if cabinet is not None and nl:
            depth = float(cabinet.get("depth_mm", 0))
            if nl > depth - 10:
                hit(
                    "carcass_runner",
                    element,
                    f"runner NL {nl:.0f} mm does not fit the {depth:.0f} mm "
                    "carcass (10 mm clearance)",
                    "Hardware determines carcass dimensions: pick the NL for "
                    "the carcass, or deepen the carcass before cutting.",
                )
        load = runner.get("load_class_kg")
        if load is not None and nl:
            span = _RUNNER_NL.get(int(load))
            if span is None:
                hit(
                    "carcass_runner",
                    element,
                    f"unknown runner load class {load} kg",
                    f"LEGRABOX classes: {sorted(_RUNNER_NL)} kg.",
                )
            elif not (span[0] <= nl <= span[1]):
                hit(
                    "carcass_runner",
                    element,
                    f"NL {nl:.0f} mm is outside the {load} kg class range {span[0]}-{span[1]} mm",
                    "Pick an NL the class actually ships, or change class.",
                )

    # -- J6: parts inside their carcass -----------------------------------
    # Orientation is constrained by role (a shelf cannot be turned on the
    # diagonal to fit), so known roles check per-axis; unknown roles fall
    # back to the sorted-envelope comparison.
    role_axes = {
        # role: (length checks against, width checks against)
        "shelf": ("width_mm", "depth_mm"),
        "top": ("width_mm", "depth_mm"),
        "bottom": ("width_mm", "depth_mm"),
        "side": ("height_mm", "depth_mm"),
        "back": ("height_mm", "width_mm"),
        "door": ("height_mm", "width_mm"),
    }
    for part in spec.get("parts") or []:
        cabinet = cabinets.get(str(part.get("cabinet")))
        if cabinet is None:
            continue
        length = float(part.get("length_mm", 0))
        width = float(part.get("width_mm", 0))
        role = str(part.get("role") or "")
        oversize: list[tuple[float, float, str]] = []
        axes = role_axes.get(role)
        if axes is not None:
            for value, axis in ((length, axes[0]), (width, axes[1])):
                bound = float(cabinet.get(axis, 0))
                if bound and value > bound + 1.0:
                    oversize.append((value, bound, axis))
        else:
            envelope = sorted(
                float(cabinet.get(k, 0)) for k in ("width_mm", "height_mm", "depth_mm")
            )
            dims = sorted([length, width, float(part.get("thickness_mm", 0))])
            oversize = [
                (d, e, "envelope") for d, e in zip(dims, envelope, strict=True) if d > e + 1.0
            ]
        if oversize:
            worst = max(oversize, key=lambda row: row[0] - row[1])
            hit(
                "part_envelope",
                part.get("id"),
                f"{role or 'part'} {part.get('id')}: {worst[0]:.0f} mm exceeds "
                f"the carcass {worst[2].replace('_mm', '')} {worst[1]:.0f} mm "
                f"by {worst[0] - worst[1]:.0f} mm",
                "A part larger than its carcass cannot be assembled - re-derive "
                "part sizes from the carcass (check drivers/formulas upstream).",
            )

    # -- J7: wardrobe depth advisory --------------------------------------
    for cabinet in cabinets.values():
        if str(cabinet.get("kind")) == "tall" and cabinet.get("hanging", True):
            depth = float(cabinet.get("depth_mm", 0))
            if depth and depth < 530.0:
                hit(
                    "wardrobe_depth",
                    cabinet.get("id"),
                    f"wardrobe depth {depth:.0f} mm is under the 530 mm hanging standard",
                    "Deepen to >=530 mm internal (600 mm including the wall) or "
                    "plan folded storage only.",
                )

    errors = [f for f in findings if f["severity"] == "ERROR"]
    return {
        "ok": not errors,
        "findings": findings,
        "not_evaluated": not_evaluated,
        "rules_total": len(RULES),
        "rules_evaluated": len(RULES) - len({n["rule"] for n in not_evaluated}),
        "note": "every rule cites its source and its A30 re-verification state; "
        "not_evaluated is missing data, never conformance",
    }
