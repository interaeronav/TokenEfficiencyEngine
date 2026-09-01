"""Cutting and design: the operations a pattern maker does with a knife.

Everything here is a boolean on a panel outline, done in shapely, and every
one of them RETURNS NEW PANELS rather than editing in place - because a cut
that half-succeeds is worse than one that refuses, and because the seams that
referenced the old panel have to be re-made deliberately.

  cut          split a panel along a line into two, and tell you which is
               which so the seam between them can be sewn
  dart         take a wedge out and close it - the operation that turns flat
               cloth into a shape
  slash_spread the other half of that trade: open a wedge to add fullness,
               which is how a flare, a gather or a godet is drafted
  pleat        fold volume in and hold it with a line
  notch_at     a balance mark where two pieces have to meet

A cut that would leave a sliver, split a panel into three, or miss it
entirely refuses by name. Those are the three ways a knife goes wrong on
cloth, and none of them is worth discovering later.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import split as shapely_split

from seamkiln.pattern.geometry import Vertex, VertexKind, retag_by_angle, to_array
from seamkiln.pattern.model import InternalLine, LineKind, Mark, MarkKind, Panel

MIN_PIECE_MM2 = 100.0  # smaller than a fingernail is a sliver, not a piece


class CuttingError(ValueError):
    """A cut that would not produce usable pieces."""


@dataclass(slots=True)
class Cut:
    pieces: list[Panel]
    seam_edge_mm: float
    method: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "pieces": [
                {"id": p.id, "area_mm2": round(p.area_mm2, 1), "edges": len(p.edges())}
                for p in self.pieces
            ],
            "cut_length_mm": round(self.seam_edge_mm, 2),
            "method": self.method,
        }


def _polygon(panel: Panel) -> Polygon:
    polygon = Polygon(to_array(panel.outline))
    if not polygon.is_valid:
        polygon = polygon.buffer(0)
    if polygon.geom_type != "Polygon":
        raise CuttingError(f"panel {panel.id} is not a simple closed shape")
    return polygon


def _to_panel(polygon: Polygon, panel: Panel, suffix: str) -> Panel:
    ring = [
        Vertex(float(x), float(y), VertexKind.CURVE) for x, y in list(polygon.exterior.coords)[:-1]
    ]
    return Panel(
        id=f"{panel.id}_{suffix}",
        name=f"{panel.name} {suffix}",
        outline=retag_by_angle(ring),
        marks=[m for m in panel.marks if polygon.contains(_point(m.x, m.y))],
        internals=[
            line
            for line in panel.internals
            if polygon.contains(_point(line.points[0].x, line.points[0].y))
        ],
        seam_allowance_mm=panel.seam_allowance_mm,
        meta={**panel.meta, "cut_from": panel.id},
    )


def _point(x: float, y: float):
    from shapely.geometry import Point

    return Point(x, y)


def cut(panel: Panel, start: tuple[float, float], end: tuple[float, float]) -> Cut:
    """Split a panel along a straight line. Two pieces, or a named refusal."""
    polygon = _polygon(panel)
    line = LineString([start, end])
    if not line.intersects(polygon):
        raise CuttingError(
            f"the cut from {start} to {end} misses panel {panel.id} entirely. "
            f"Its bounding box is {tuple(round(v, 1) for v in panel.bbox)}."
        )
    # extend the line well past the panel so a cut that stops short still
    # separates it - a knife that stops inside the cloth does not cut it
    direction = np.asarray(end, float) - np.asarray(start, float)
    length = float(np.linalg.norm(direction))
    if length < 1e-9:
        raise CuttingError("a cut needs two different points")
    unit = direction / length
    span = float(np.hypot(*(np.asarray(panel.bbox[2:]) - np.asarray(panel.bbox[:2])))) * 1.2
    extended = LineString(
        [np.asarray(start, float) - unit * span, np.asarray(end, float) + unit * span]
    )

    parts = [p for p in shapely_split(polygon, extended).geoms if p.area > MIN_PIECE_MM2]
    if len(parts) < 2:
        raise CuttingError(
            f"the cut left {len(parts)} usable piece(s) of panel {panel.id}: it "
            "grazes the outline rather than crossing it."
        )
    if len(parts) > 2:
        raise CuttingError(
            f"the cut split panel {panel.id} into {len(parts)} pieces. A concave "
            "panel can be crossed more than once - cut it in two steps."
        )
    parts.sort(key=lambda p: p.centroid.x)
    return Cut(
        pieces=[_to_panel(parts[0], panel, "a"), _to_panel(parts[1], panel, "b")],
        seam_edge_mm=float(extended.intersection(polygon).length),
        method="straight cut",
    )


def dart(
    panel: Panel,
    apex: tuple[float, float],
    base_centre: tuple[float, float],
    width_mm: float,
) -> Panel:
    """Take a wedge out and close it - the operation that shapes flat cloth.

    The dart is removed from the outline (so the panel really is smaller) and
    its legs are kept as internal lines, because a sewer needs to see where to
    fold even though the cloth is already gone.
    """
    if width_mm <= 0.0:
        raise CuttingError(f"a dart needs a positive width, got {width_mm}")
    polygon = _polygon(panel)
    apex_p = np.asarray(apex, float)
    base_p = np.asarray(base_centre, float)
    axis = base_p - apex_p
    length = float(np.linalg.norm(axis))
    if length < 1e-6:
        raise CuttingError("a dart's apex and base must differ")
    across = np.array([-axis[1], axis[0]]) / length * (width_mm / 2.0)
    wedge = Polygon([apex_p, base_p + across, base_p - across])
    if not polygon.intersects(wedge):
        raise CuttingError(f"the dart is not on panel {panel.id}")

    remaining = polygon.difference(wedge)
    if remaining.geom_type != "Polygon" or remaining.area < MIN_PIECE_MM2:
        raise CuttingError(
            f"the dart cut panel {panel.id} in two. A dart must open onto exactly "
            "one edge; this one crosses the piece."
        )
    ring = [
        Vertex(float(x), float(y), VertexKind.CURVE)
        for x, y in list(remaining.exterior.coords)[:-1]
    ]
    legs = InternalLine(
        LineKind.DART,
        [
            Vertex(*(base_p + across)),
            Vertex(*apex_p),
            Vertex(*(base_p - across)),
        ],
    )
    return Panel(
        id=panel.id,
        name=panel.name,
        outline=retag_by_angle(ring),
        internals=[*panel.internals, legs],
        marks=[*panel.marks, Mark(MarkKind.NOTCH_V, *apex_p, depth=4.0)],
        seam_allowance_mm=panel.seam_allowance_mm,
        meta={**panel.meta, "dart": f"{width_mm:.1f}mm"},
    )


def slash_spread(
    panel: Panel,
    hinge: tuple[float, float],
    through: tuple[float, float],
    spread_deg: float,
) -> Panel:
    """Open a wedge to ADD fullness - a flare, a gather, a godet.

    The other half of the dart's trade: a dart takes shape out of flat cloth,
    a slash-and-spread puts fullness in. Everything on the far side of the
    slash rotates about the hinge.
    """
    if abs(spread_deg) < 1e-6:
        return panel
    hinge_p = np.asarray(hinge, float)
    axis = np.asarray(through, float) - hinge_p
    if float(np.linalg.norm(axis)) < 1e-6:
        raise CuttingError("a slash needs two different points")
    normal = np.array([-axis[1], axis[0]])
    angle = math.radians(spread_deg)
    rotation = np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])

    def move(x: float, y: float) -> tuple[float, float]:
        point = np.array([x, y]) - hinge_p
        if float(np.dot(point, normal)) <= 0.0:
            return (x, y)
        return tuple(rotation @ point + hinge_p)

    return Panel(
        id=panel.id,
        name=panel.name,
        outline=[Vertex(*move(v.x, v.y), v.kind) for v in panel.outline],
        internals=[
            InternalLine(
                line.kind, [Vertex(*move(v.x, v.y), v.kind) for v in line.points], line.closed
            )
            for line in panel.internals
        ],
        marks=[
            Mark(m.kind, *move(m.x, m.y), depth=m.depth, diameter=m.diameter) for m in panel.marks
        ],
        seam_allowance_mm=panel.seam_allowance_mm,
        meta={**panel.meta, "spread": f"{spread_deg:.1f}deg"},
    )


def pleat(
    panel: Panel,
    at_x: float,
    depth_mm: float,
    *,
    kind: str = "knife",
) -> Panel:
    """Fold volume in and mark where it folds.

    A pleat removes `depth` twice over (it folds back on itself), so the panel
    narrows by 2x depth for a knife pleat and 4x for a box pleat - which is the
    arithmetic people get wrong when drafting one by hand.
    """
    if kind not in ("knife", "box"):
        raise CuttingError(f"no pleat kind {kind!r}; kinds: knife, box.")
    take = depth_mm * (2.0 if kind == "knife" else 4.0)
    minx, miny, maxx, maxy = panel.bbox
    if take >= (maxx - minx) * 0.8:
        raise CuttingError(
            f"a {kind} pleat {depth_mm:g} mm deep removes {take:g} mm from a panel "
            f"{maxx - minx:.0f} mm wide. Reduce the depth or split the pleat."
        )

    def shift(x: float) -> float:
        return x - take if x > at_x else x

    lines = [
        InternalLine(LineKind.PLEAT, [Vertex(at_x, miny), Vertex(at_x, maxy)]),
        InternalLine(
            LineKind.PLEAT, [Vertex(at_x - depth_mm, miny), Vertex(at_x - depth_mm, maxy)]
        ),
    ]
    return Panel(
        id=panel.id,
        name=panel.name,
        outline=[Vertex(shift(v.x), v.y, v.kind) for v in panel.outline],
        internals=[*panel.internals, *lines],
        marks=[
            Mark(m.kind, shift(m.x), m.y, depth=m.depth, diameter=m.diameter) for m in panel.marks
        ],
        seam_allowance_mm=panel.seam_allowance_mm,
        meta={**panel.meta, "pleat": f"{kind} {depth_mm:g}mm"},
    )
