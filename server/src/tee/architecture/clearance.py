"""Analytic vertical stair clearance to authored slab/roof solids, without sampling.

The walking surface is the full-width line through leading tread nosings, then
the horizontal last tread/landing. This is a design observation, not a code rule.
Linear extrema occur on clipped polygon boundaries, including narrow obstructions.
"""

from __future__ import annotations

import math
from itertools import pairwise
from typing import Any

EPS = 1e-7  # mm numerical support-contact tolerance, not a construction allowance.


def _vertices(shape: Any) -> list[tuple]:
    if shape.is_empty:
        return []
    if shape.geom_type == "Polygon":
        return list(shape.exterior.coords)[:-1] + [
            p for ring in shape.interiors for p in list(ring.coords)[:-1]
        ]
    return [p for part in getattr(shape, "geoms", []) for p in _vertices(part)]


def _value(plane: tuple, point: tuple) -> float:
    return plane[0] * point[0] + plane[1] * point[1] + plane[2]


def _subtract(a: tuple, b: tuple) -> tuple:
    return tuple(a[i] - b[i] for i in range(3))


def _above(shape: Any, plane: tuple) -> Any:
    """Clip to plane(x,y)>=0 using a half-plane clipped to the shape's bounds."""
    from shapely.geometry import Polygon

    x0, y0, x1, y1 = shape.bounds
    ring = [(x0 - 1, y0 - 1), (x1 + 1, y0 - 1), (x1 + 1, y1 + 1), (x0 - 1, y1 + 1)]
    output = []
    for a, b in zip(ring, ring[1:] + ring[:1], strict=True):
        va, vb = _value(plane, a), _value(plane, b)
        if va >= 0:
            output.append(a)
        if (va >= 0) != (vb >= 0):
            t = va / (va - vb)
            output.append(tuple(a[i] + t * (b[i] - a[i]) for i in range(2)))
    return shape.intersection(Polygon(output)) if len(output) >= 3 else Polygon()


def _plane(points: list[list[float]]) -> tuple:
    a = points[0]
    for b, c in pairwise(points[1:]):
        ux, uy, uz = [b[i] - a[i] for i in range(3)]
        vx, vy, vz = [c[i] - a[i] for i in range(3)]
        det = ux * vy - uy * vx
        if abs(det) > EPS:
            px, py = (uz * vy - uy * vz) / det, (ux * vz - uz * vx) / det
            return px, py, a[2] - px * a[0] - py * a[1]
    raise ValueError("Roof footprint has no noncollinear plane points.")


def stair_clearance(stair: dict, entities: dict) -> dict:
    from shapely import affinity
    from shapely.geometry import Polygon, box

    from .penetrations import slab_shape
    from .spatial import base_elevation
    from .systems import roof_meshes, stair_dimensions

    dims = stair_dimensions(stair, entities)
    angle = math.radians(stair["direction_deg"])
    c, s = math.cos(angle), math.sin(angle)
    ox, oy = stair["start"]
    base = dims["bottom_world_mm"]

    def local(point: list) -> list:
        x, y = point[0] - ox, point[1] - oy
        return [c * x + s * y, -s * x + c * y, point[2] - base]

    def local_shape(shape: Any) -> Any:
        return affinity.rotate(
            affinity.translate(shape, -ox, -oy), -stair["direction_deg"], origin=(0, 0)
        )

    obstacles = []
    for identifier, entity in sorted(entities.items()):
        if entity["kind"] == "slab":
            top = base_elevation(entity, entities) - base
            obstacles.append(
                (
                    identifier,
                    "slab",
                    local_shape(slab_shape(entity, entities)),
                    (0, 0, top - entity["thickness"]),
                    (0, 0, top),
                )
            )
        elif entity["kind"] == "roof":
            for mesh in roof_meshes(entity, entities[entity["storey"]]["elevation"]):
                count = len(mesh["vertices"]) // 2
                bottom = [local(p) for p in mesh["vertices"][:count]]
                top = [local(p) for p in mesh["vertices"][count:]]
                obstacles.append(
                    (
                        identifier,
                        str(mesh["part"]),
                        Polygon([p[:2] for p in bottom]),
                        _plane(bottom),
                        _plane(top),
                    )
                )

    nosing_run = dims["flight_run_mm"] - stair["going"]
    patches = [
        (
            "nosing_line",
            box(0, 0, nosing_run, stair["width"]),
            (dims["riser_height_mm"] / stair["going"], 0, dims["riser_height_mm"]),
        ),
        (
            "upper_tread_landing",
            box(nosing_run, 0, dims["flight_run_mm"] + stair["landing_depth"], stair["width"]),
            (0, 0, dims["total_rise_mm"]),
        ),
    ]
    limiting = None
    supports: set[str] = set()
    examined: set[str] = set()
    for identifier, part, footprint, bottom, top in obstacles:
        for walk_part, area, walking in patches:
            overlap = footprint.intersection(area)
            if overlap.is_empty or overlap.area <= 1e-9:
                continue
            examined.add(identifier)
            upper = _subtract(top, walking)
            values = [_value(upper, p) for p in _vertices(overlap)]
            if max(values) <= EPS:
                if min(values) >= -EPS:
                    supports.add(identifier)
                continue  # Entire solid is below, or its top supports this walking patch.
            overlap = _above(overlap, upper)
            candidates = _vertices(overlap)
            if not candidates:
                continue
            delta = _subtract(bottom, walking)
            point = min(candidates, key=lambda p: (_value(delta, p), p[0], p[1]))
            signed = _value(delta, point)
            if signed < -EPS:
                # Choose a witness inside the intersection, not on the support
                # boundary where the upper slab face merely touches a tread.
                penetration = _above(overlap, _subtract(walking, bottom))
                if penetration.area > 1e-9:
                    witness = penetration.representative_point()
                    point = (witness.x, witness.y)
                    signed = _value(delta, point)
            clearance = max(0.0, signed)
            row = {
                "obstacle_id": identifier,
                "obstacle_part": part,
                "walking_part": walk_part,
                "clearance_mm": clearance,
                "solid_intersects_walking_envelope": signed < -EPS,
                "walking_point_world_mm": [
                    ox + c * point[0] - s * point[1],
                    oy + s * point[0] + c * point[1],
                    base + _value(walking, point),
                ],
                "underside_world_mm": base + _value(bottom, point),
            }
            if limiting is None or clearance < limiting["clearance_mm"]:
                limiting = row
    target = stair.get("headroom_target_mm")
    measured = limiting["clearance_mm"] if limiting else None
    return {
        "target_mm": target,
        "minimum_clearance_mm": measured,
        "status": "target_unset"
        if target is None
        else "no_overhead_in_scope"
        if measured is None
        else "below_target"
        if measured + EPS < target
        else "meets_target_in_scope",
        "limiting": limiting,
        "support_contact_ids": sorted(supports),
        "examined_obstacle_count": len(examined),
        "basis": (
            "Vertical clearance above full-width nosing pitch line and upper tread/landing; "
            "analytic polygon/plane extrema."
        ),
        "scope": (
            "Authored slabs and roofs only. Walls, beams, services, railings and imported "
            "references are not assessed; no code approval."
        ),
    }
