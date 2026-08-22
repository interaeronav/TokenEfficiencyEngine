"""The TEE plan schema (`tee-plan/1`) - decision A10.

FML v3-derived (walls as centerline endpoints + thickness, openings
parameterized by t along the wall, rooms as polygons), extended BEFORE the
freeze with per-level heights and a parametric roof (docs/research/17).
Fields are nullable-but-present so cache keys stay stable while extractor
coverage grows. Units are always meters in a drawing model frame (Y up on
plan sheets maps to +Y; Z is vertical).
"""

from __future__ import annotations

import math
from typing import Any

from tee.kernel.errors import TeeError

SCHEMA_ID = "tee-plan/1"
ROOF_TYPES = ("flat", "shed", "gable", "hip", "hipped_gable", "gambrel", "mansard")
OPENING_KINDS = ("door", "window")


def empty_plan(frame: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA_ID,
        "frame": frame,
        "units": "m",
        "scale": None,  # {"method": ..., "confidence": ..., "factor": ...}
        "levels": [],
        "walls": [],
        "openings": [],
        "rooms": [],
        "roof": None,
    }


def wall_length(wall: dict[str, Any]) -> float:
    (ax, ay), (bx, by) = wall["a"], wall["b"]
    return math.hypot(bx - ax, by - ay)


def wall_midpoint(wall: dict[str, Any]) -> tuple[float, float]:
    (ax, ay), (bx, by) = wall["a"], wall["b"]
    return ((ax + bx) / 2.0, (ay + by) / 2.0)


def wall_angle(wall: dict[str, Any]) -> float:
    (ax, ay), (bx, by) = wall["a"], wall["b"]
    return math.atan2(by - ay, bx - ax)


def validate_plan(plan: Any) -> dict[str, Any]:
    """Validate a plan document; returns it. One short error per problem."""
    if not isinstance(plan, dict) or plan.get("schema") != SCHEMA_ID:
        raise TeeError(
            "bad_plan",
            f"Plan must be an object with schema '{SCHEMA_ID}'.",
        )
    if not isinstance(plan.get("frame"), str) or not plan["frame"]:
        raise TeeError("bad_plan", "Plan needs a 'frame' id (see the frame registry).")

    levels = plan.get("levels") or []
    level_indices = set()
    for lvl in levels:
        _require(lvl, "level", ("index", int), ("elevation_z", (int, float)))
        level_indices.add(lvl["index"])

    wall_ids = set()
    for wall in plan.get("walls") or []:
        _require(wall, "wall", ("id", str), ("thickness", (int, float)))
        for key in ("a", "b"):
            pt = wall.get(key)
            if (
                not isinstance(pt, (list, tuple))
                or len(pt) != 2
                or not all(isinstance(v, (int, float)) for v in pt)
            ):
                raise TeeError("bad_plan", f"wall {wall.get('id')}: '{key}' must be [x, y].")
        if wall["id"] in wall_ids:
            raise TeeError("bad_plan", f"duplicate wall id '{wall['id']}'.")
        wall_ids.add(wall["id"])
        if wall_length(wall) <= 0.01:
            raise TeeError("bad_plan", f"wall {wall['id']} is degenerate (< 1 cm).")
        if levels and wall.get("level") not in level_indices:
            raise TeeError(
                "bad_plan", f"wall {wall['id']} references unknown level {wall.get('level')}."
            )
        height = wall.get("height")
        if height is not None and (not isinstance(height, (int, float)) or height <= 0):
            raise TeeError("bad_plan", f"wall {wall['id']}: height must be positive.")

    for opening in plan.get("openings") or []:
        _require(
            opening,
            "opening",
            ("id", str),
            ("wall", str),
            ("t", (int, float)),
            ("width", (int, float)),
        )
        if opening["wall"] not in wall_ids:
            raise TeeError(
                "bad_plan",
                f"opening {opening['id']} references unknown wall '{opening['wall']}'.",
            )
        if not 0.0 <= opening["t"] <= 1.0:
            raise TeeError("bad_plan", f"opening {opening['id']}: t must be in [0, 1].")
        kind = opening.get("kind")
        if kind is not None and kind not in OPENING_KINDS:
            raise TeeError(
                "bad_plan",
                f"opening {opening['id']}: kind must be one of {OPENING_KINDS}.",
            )

    for room in plan.get("rooms") or []:
        _require(room, "room", ("id", str))
        polygon = room.get("polygon")
        if not isinstance(polygon, list) or len(polygon) < 3:
            raise TeeError("bad_plan", f"room {room['id']}: polygon needs >= 3 points.")

    roof = plan.get("roof")
    if roof is not None and roof.get("type") not in ROOF_TYPES:
        raise TeeError(
            "bad_plan",
            f"roof type '{roof.get('type')}' unknown.",
            fix=f"Use one of: {', '.join(ROOF_TYPES)}.",
        )
    return plan


def plan_summary(plan: dict[str, Any]) -> dict[str, Any]:
    """Compact overview the model reads instead of the full plan."""
    walls = plan.get("walls") or []
    return {
        "schema": plan["schema"],
        "frame": plan["frame"],
        "levels": len(plan.get("levels") or []),
        "walls": len(walls),
        "total_wall_length_m": round(sum(wall_length(w) for w in walls), 2),
        "openings": len(plan.get("openings") or []),
        "rooms": [r.get("name") or r["id"] for r in plan.get("rooms") or []][:20],
        "roof": (plan.get("roof") or {}).get("type"),
        "scale": plan.get("scale"),
    }


def _require(obj: dict[str, Any], what: str, *fields: tuple[str, Any]) -> None:
    for name, types in fields:
        if not isinstance(obj.get(name), types):
            raise TeeError(
                "bad_plan",
                f"{what} {obj.get('id', '?')}: '{name}' missing or wrong type.",
            )
