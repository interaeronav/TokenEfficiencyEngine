"""Relational placement: the model plans in relations (~10 tokens/object),
the server solves and validates (A15, Merrell terms as hard validators).

Plan item shape (all lengths meters):
    {"name": "sofa", "class": "sofa", "dims": [2.1, 0.9, 0.8],
     "anchor": "w1", "offset": 1.2}            # against wall w1
    {"name": "table", "class": "table", "dims": [...],
     "location": [x, y], "rotation": deg}      # explicit floor placement

Rooms: {"polygon": [[x, y]…], "walls": [{"id", "a": [x,y], "b": [x,y]}…],
        "doors": [{"id", "hinge": [x,y], "width", "swing_into": true}…]}

Rules come from data/placement_rules.json with code-vs-guideline severity;
code rows are never relaxable, guideline rows may be waived per-check with
a recorded note. Region (US/EU) parameterizes thresholds - pick it from
the project's GPS datum.
"""

from __future__ import annotations

import json
import math
from importlib import resources
from typing import Any

from tee.kernel.errors import TeeError

_RULES: dict[str, Any] | None = None


def rules_table() -> dict[str, Any]:
    global _RULES
    if _RULES is None:
        text = (
            resources.files("tee.assets").joinpath("data/placement_rules.json").read_text()
        )
        _RULES = json.loads(text)["rules"]
    return _RULES


def _require_shapely():
    try:
        from shapely.geometry import Point, Polygon
        from shapely.ops import unary_union
    except ImportError as exc:
        raise TeeError(
            "extract_extra_missing",
            "Placement validation needs shapely (the [extract] extra).",
            fix="uv sync --extra extract",
        ) from exc
    return Point, Polygon, unary_union


# -- solving ----------------------------------------------------------------


def solve_plan(
    plan: list[dict[str, Any]], room: dict[str, Any]
) -> list[dict[str, Any]]:
    """Turn relational plan items into concrete placements
    {name, class, dims, location [x, y], rotation_deg, footprint}."""
    walls = {w["id"]: w for w in room.get("walls", [])}
    placements = []
    for item in plan:
        dims = item.get("dims") or [0.5, 0.5, 0.5]
        if "location" in item:
            x, y = float(item["location"][0]), float(item["location"][1])
            rot = float(item.get("rotation", 0.0))
        elif item.get("anchor") in walls:
            wall = walls[item["anchor"]]
            ax, ay = wall["a"]
            bx, by = wall["b"]
            length = math.hypot(bx - ax, by - ay)
            if length <= 0:
                raise TeeError("bad_wall", f"wall {wall['id']} has zero length")
            t = min(max(float(item.get("offset", length / 2)) / length, 0.0), 1.0)
            px, py = ax + (bx - ax) * t, ay + (by - ay) * t
            # inward normal: assume CCW room polygon, interior to the left
            nx, ny = -(by - ay) / length, (bx - ax) / length
            depth = dims[1]
            x, y = px + nx * (depth / 2 + 0.02), py + ny * (depth / 2 + 0.02)
            rot = math.degrees(math.atan2(by - ay, bx - ax))
        else:
            raise TeeError(
                "bad_plan_item",
                f"'{item.get('name', '?')}' needs either location or a known "
                f"wall anchor (walls: {', '.join(walls) or 'none'}).",
            )
        placements.append(
            {
                "name": item.get("name", item.get("class", "object")),
                "class": item.get("class"),
                "dims": dims,
                "location": [round(x, 4), round(y, 4)],
                "rotation_deg": round(rot, 2),
                "relax": item.get("relax", []),
            }
        )
    return placements


def footprint(place: dict[str, Any]):
    _, polygon_cls, _ = _require_shapely()
    w, d = place["dims"][0] / 2, place["dims"][1] / 2
    angle = math.radians(place.get("rotation_deg", 0.0))
    cx, cy = place["location"]
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    corners = []
    for dx, dy in ((-w, -d), (w, -d), (w, d), (-w, d)):
        corners.append((cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a))
    return polygon_cls(corners)


# -- validation -------------------------------------------------------------


def validate_placement(
    placements: list[dict[str, Any]],
    room: dict[str, Any],
    *,
    region: str = "US",
) -> dict[str, Any]:
    """Run the rule table; returns {violations: […], checked: N}. Each
    violation: {rule, severity, objects, measured_mm?, required_mm?, fix}.
    Guideline rules named in a placement's `relax` list are skipped with a
    recorded note; code rules never relax."""
    point_cls, polygon_cls, unary_union = _require_shapely()
    rules = rules_table()
    room_poly = polygon_cls(room["polygon"])
    feet = {p["name"]: footprint(p) for p in placements}
    union = unary_union(list(feet.values())) if feet else None
    violations: list[dict[str, Any]] = []
    relaxed: list[dict[str, Any]] = []
    checked = 0

    def hit(rule_id: str, objects: list[str], measured=None, required=None, fix=""):
        rule = rules[rule_id]
        severity = rule["severity"]
        entry: dict[str, Any] = {
            "rule": rule_id,
            "severity": severity,
            "objects": objects,
            "source": rule["source"].get(region) or next(iter(rule["source"].values())),
            "fix": fix,
        }
        if measured is not None:
            entry["measured_mm"] = int(measured)
        if required is not None:
            entry["required_mm"] = int(required)
        waivers = {
            r for p in placements if p["name"] in objects for r in p.get("relax", [])
        }
        if severity == "guideline" and rule_id in waivers:
            entry["note"] = "guideline relaxed by plan (recorded)"
            relaxed.append(entry)
        else:
            violations.append(entry)

    # containment + overlap (always on)
    for place in placements:
        checked += 1
        if not room_poly.buffer(0.01).contains(feet[place["name"]]):
            hit(
                "passage_min",
                [place["name"]],
                fix=f"{place['name']} crosses the room boundary - move it inside",
            )
    names = [p["name"] for p in placements]
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            checked += 1
            inter = feet[a].intersection(feet[b]).area
            if inter > 0.005:  # ≤ 5 mm-scale contact tolerated
                hit(
                    "passage_min",
                    [a, b],
                    fix=f"{a} and {b} overlap by {inter:.2f} m^2 - separate them",
                )

    # door swings (code) + front clearance
    for door in room.get("doors", []):
        arc = _swing_arc(point_cls, door)
        for place in placements:
            checked += 1
            if arc.intersection(feet[place["name"]]).area > 1e-4:
                hit(
                    "door_swing_clear",
                    [place["name"], door.get("id", "door")],
                    fix=f"move {place['name']} out of the {door.get('id', 'door')} swing arc",
                )

    # corridor/passage: doors must stay mutually reachable through the
    # free space eroded by half the passage width
    doors = room.get("doors", [])
    if union is not None and len(doors) >= 2:
        required = rules["passage_min"]["min_mm"].get(region, 760)
        free = room_poly.difference(union.buffer(0.005))
        eroded = free.buffer(-required / 2000.0)
        checked += 1
        components = list(getattr(eroded, "geoms", [eroded])) if not eroded.is_empty else []

        def component_of(pt):
            # erosion pulls passage/2 back from every wall, so a hinge ON
            # the wall sits ~required/2 m from its component; allow that
            # plus slack - blocked door VICINITY is the swing rule's job,
            # this rule is about connectivity between the doors
            best, best_d = None, float("inf")
            for idx, geom in enumerate(components):
                d = geom.distance(pt)
                if d < best_d:
                    best, best_d = idx, d
            return best if best_d < required / 1000.0 + 0.35 else None

        comps = [component_of(point_cls(*d["hinge"])) for d in doors]
        if not components or None in comps or len(set(comps)) > 1:
            hit(
                "passage_min",
                [d.get("id", "door") for d in doors],
                required=required,
                fix=f"no {required} mm-wide clear path connects the doors - "
                "widen the gap between furniture",
            )

    # work triangle (kitchen classes present)
    tri = {
        c: next((p for p in placements if p.get("class") == c), None)
        for c in ("sink", "stove", "refrigerator")
    }
    if all(tri.values()):
        checked += 1
        pts = [tri[c]["location"] for c in ("sink", "stove", "refrigerator")]
        legs = [
            math.dist(pts[0], pts[1]),
            math.dist(pts[1], pts[2]),
            math.dist(pts[2], pts[0]),
        ]
        rule = rules["work_triangle"]
        bad_legs = [round(v, 2) for v in legs if v < rule["leg_min_m"] or v > rule["leg_max_m"]]
        if bad_legs or sum(legs) > rule["perimeter_max_m"]:
            hit(
                "work_triangle",
                ["sink", "stove", "refrigerator"],
                fix=f"legs {[round(v, 2) for v in legs]} m (each {rule['leg_min_m']}-"
                f"{rule['leg_max_m']}, sum <= {rule['perimeter_max_m']}) - move the "
                "offending appliance",
            )

    # back-to-wall classes
    wall_rule = rules["back_to_wall"]
    boundary = room_poly.exterior
    for place in placements:
        if place.get("class") in wall_rule["classes"]:
            checked += 1
            gap_mm = feet[place["name"]].distance(boundary) * 1000
            allowed = wall_rule["max_gap_mm"].get(region, 150)
            if gap_mm > allowed:
                hit(
                    "back_to_wall",
                    [place["name"]],
                    measured=gap_mm,
                    required=allowed,
                    fix=f"back {place['name']} toward a wall (gap {gap_mm:.0f} mm)",
                )

    # pairwise clearances by class
    def clearance(rule_id: str, class_a: str, class_b: str | None):
        nonlocal checked
        rule = rules[rule_id]
        required = rule["min_mm"].get(region)
        for place in placements:
            if place.get("class") != class_a:
                continue
            others = [
                p for p in placements
                if p is not place and (class_b is None or p.get("class") == class_b)
            ]
            for other in others:
                checked += 1
                gap = feet[place["name"]].distance(feet[other["name"]]) * 1000
                if 0 < gap < required:
                    hit(
                        rule_id,
                        [place["name"], other["name"]],
                        measured=gap,
                        required=required,
                        fix=f"open the gap to {required} mm",
                    )

    clearance("dining_pullback", "table", None)
    clearance("bed_side_clear", "bed", None)
    clearance("toilet_front", "toilet", None)

    out: dict[str, Any] = {"checked": checked, "violations": violations}
    if relaxed:
        out["relaxed"] = relaxed
    if not violations:
        out["summary"] = f"no placement conflicts detected ({checked} checks)"
    return out


def _swing_arc(point_cls, door: dict[str, Any]):
    """Quarter-circle swing polygon from the hinge; swing_start_deg orients
    the closed-door edge (arc sweeps +90 degrees CCW from it)."""
    from shapely.geometry import Polygon as Poly

    hx, hy = door["hinge"]
    radius = float(door.get("width", 0.86))
    start = math.radians(float(door.get("swing_start_deg", 0.0)))
    pts = [(hx, hy)]
    for i in range(13):
        a = start + (math.pi / 2) * i / 12
        pts.append((hx + radius * math.cos(a), hy + radius * math.sin(a)))
    return Poly(pts)
