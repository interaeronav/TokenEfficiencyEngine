"""Panel geometry: tagged polylines, because that is what the standard stores.

A pattern piece could be modelled as parametric curves and flattened on
export. It is not, and the reason is interchange: ASTM D6673 stores a piece
boundary as a POLYLINE whose vertices are tagged **turn point** (a corner)
or **curve point** (a smooth sample). Keeping that as the canonical form
means a DXF round-trip is lossless by construction rather than by tolerance,
and a corner stays a corner instead of becoming three points that nearly
agree.

Curve constructors (arc, cubic) exist for authoring; they emit tagged
vertices. Everything downstream - area, allowance, plotting, sewing - reads
the tagged polyline.

Units are millimetres everywhere inside seamkiln. The DXF reader converts
on the way in and records what it converted from.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

import numpy as np

TAU = 2.0 * math.pi


class VertexKind(StrEnum):
    TURN = "turn"  # a corner: the boundary changes direction here
    CURVE = "curve"  # a sample along a smooth run


@dataclass(frozen=True, slots=True)
class Vertex:
    x: float
    y: float
    kind: VertexKind = VertexKind.TURN

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


Polyline = list[Vertex]


def to_array(outline: Polyline) -> np.ndarray:
    return np.asarray([(v.x, v.y) for v in outline], dtype=np.float64)


def signed_area(outline: Polyline) -> float:
    """Shoelace, mm^2. Positive when the outline runs counter-clockwise."""
    points = to_array(outline)
    if points.shape[0] < 3:
        return 0.0
    x, y = points[:, 0], points[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))


def area(outline: Polyline) -> float:
    return abs(signed_area(outline))


def perimeter(outline: Polyline, *, closed: bool = True) -> float:
    points = to_array(outline)
    if points.shape[0] < 2:
        return 0.0
    if closed:
        points = np.vstack([points, points[:1]])
    return float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())


def is_counter_clockwise(outline: Polyline) -> bool:
    return signed_area(outline) > 0.0


def ensure_counter_clockwise(outline: Polyline) -> Polyline:
    """CCW is seamkiln's canonical winding: it makes a positive seam
    allowance an outward offset without a sign test at every call site."""
    return outline if is_counter_clockwise(outline) else list(reversed(outline))


def cumulative_length(outline: Polyline, *, closed: bool = False) -> np.ndarray:
    points = to_array(outline)
    if closed:
        points = np.vstack([points, points[:1]])
    steps = np.linalg.norm(np.diff(points, axis=0), axis=1)
    return np.concatenate([[0.0], np.cumsum(steps)])


def point_at(outline: Polyline, t: float) -> tuple[float, float]:
    """Position at normalised arc length t in [0, 1] along an open run."""
    if not outline:
        raise ValueError("empty polyline has no points")
    if len(outline) == 1:
        return outline[0].as_tuple()
    lengths = cumulative_length(outline)
    total = lengths[-1]
    if total <= 0.0:
        return outline[0].as_tuple()
    target = min(max(t, 0.0), 1.0) * total
    index = int(np.searchsorted(lengths, target, side="right")) - 1
    index = min(max(index, 0), len(outline) - 2)
    span = lengths[index + 1] - lengths[index]
    local = 0.0 if span <= 0.0 else (target - lengths[index]) / span
    a, b = outline[index], outline[index + 1]
    return (a.x + (b.x - a.x) * local, a.y + (b.y - a.y) * local)


def slice_run(outline: Polyline, t0: float, t1: float) -> Polyline:
    """The sub-run between two normalised arc-length parameters.

    Endpoints are inserted exactly, so `perimeter(slice_run(o, 0, 1))` equals
    `perimeter(o, closed=False)` and a seam that covers half an edge really
    covers half its length - which is what makes N:1 seams measurable.
    """
    if t1 < t0:
        t0, t1 = t1, t0
    lengths = cumulative_length(outline)
    total = lengths[-1]
    if total <= 0.0:
        return list(outline)
    start, end = t0 * total, t1 * total
    out: Polyline = [Vertex(*point_at(outline, t0), VertexKind.TURN)]
    for index, vertex in enumerate(outline):
        if start < lengths[index] < end:
            out.append(vertex)
    out.append(Vertex(*point_at(outline, t1), VertexKind.TURN))
    return out


# -- authoring helpers: parametric curves that emit tagged vertices ----------


def line(start: tuple[float, float], end: tuple[float, float]) -> Polyline:
    return [Vertex(*start, VertexKind.TURN), Vertex(*end, VertexKind.TURN)]


def arc(
    centre: tuple[float, float],
    radius: float,
    start_deg: float,
    end_deg: float,
    *,
    tolerance: float = 0.1,
) -> Polyline:
    """Circular arc sampled so the chord never sags more than `tolerance` mm.

    Sagitta-driven, not a fixed segment count: a 2 mm neckline curve and a
    900 mm hem get the accuracy they each need, and neither gets a thousand
    points it does not need. Over-faceted curves are a named cause of bad
    DXF imports.
    """
    sweep = math.radians(end_deg - start_deg)
    if radius <= 0.0 or abs(sweep) < 1e-12:
        point = (
            centre[0] + radius * math.cos(math.radians(start_deg)),
            centre[1] + radius * math.sin(math.radians(start_deg)),
        )
        return [Vertex(*point, VertexKind.TURN)]
    ratio = max(-1.0, min(1.0, 1.0 - tolerance / radius))
    step = 2.0 * math.acos(ratio) if ratio < 1.0 else abs(sweep)
    count = max(2, math.ceil(abs(sweep) / max(step, 1e-6)) + 1)
    angles = np.linspace(math.radians(start_deg), math.radians(start_deg) + sweep, count)
    out = [
        Vertex(centre[0] + radius * math.cos(a), centre[1] + radius * math.sin(a), VertexKind.CURVE)
        for a in angles
    ]
    return [
        Vertex(out[0].x, out[0].y, VertexKind.TURN),
        *out[1:-1],
        Vertex(out[-1].x, out[-1].y, VertexKind.TURN),
    ]


def cubic(
    p0: tuple[float, float],
    c1: tuple[float, float],
    c2: tuple[float, float],
    p3: tuple[float, float],
    *,
    tolerance: float = 0.1,
) -> Polyline:
    """Cubic Bezier, adaptively sampled against the same sag tolerance."""
    control = np.array([p0, c1, c2, p3], dtype=np.float64)
    chord = float(np.linalg.norm(control[3] - control[0]))
    net = float(
        np.linalg.norm(control[1] - control[0])
        + np.linalg.norm(control[2] - control[1])
        + np.linalg.norm(control[3] - control[2])
    )
    slack = max(net - chord, 0.0)
    count = max(2, math.ceil(math.sqrt(slack / max(tolerance, 1e-6)) * 4) + 1)
    t = np.linspace(0.0, 1.0, count)[:, None]
    points = (
        (1 - t) ** 3 * control[0]
        + 3 * (1 - t) ** 2 * t * control[1]
        + 3 * (1 - t) * t**2 * control[2]
        + t**3 * control[3]
    )
    out = [Vertex(float(x), float(y), VertexKind.CURVE) for x, y in points]
    return [
        Vertex(out[0].x, out[0].y, VertexKind.TURN),
        *out[1:-1],
        Vertex(out[-1].x, out[-1].y, VertexKind.TURN),
    ]


def join(*runs: Polyline) -> Polyline:
    """Concatenate runs, dropping the duplicated joint vertex.

    The joint keeps the STRONGER tag: a corner shared with a curve run is
    still a corner, and losing that is how an edge boundary quietly moves.
    """
    out: Polyline = []
    for run in runs:
        if not run:
            continue
        if (
            out
            and math.isclose(out[-1].x, run[0].x, abs_tol=1e-9)
            and math.isclose(out[-1].y, run[0].y, abs_tol=1e-9)
        ):
            if run[0].kind is VertexKind.TURN:
                out[-1] = Vertex(out[-1].x, out[-1].y, VertexKind.TURN)
            out.extend(run[1:])
        else:
            out.extend(run)
    return out


def bounding_box(outline: Polyline) -> tuple[float, float, float, float]:
    points = to_array(outline)
    return (
        float(points[:, 0].min()),
        float(points[:, 1].min()),
        float(points[:, 0].max()),
        float(points[:, 1].max()),
    )


def turn_angles(outline: Polyline, *, closed: bool = True) -> np.ndarray:
    """Interior turn at each vertex, in degrees. 0 = straight through."""
    points = to_array(outline)
    if points.shape[0] < 3:
        return np.zeros(points.shape[0])
    previous = np.roll(points, 1, axis=0) if closed else np.vstack([points[:1], points[:-1]])
    following = np.roll(points, -1, axis=0) if closed else np.vstack([points[1:], points[-1:]])
    incoming = points - previous
    outgoing = following - points
    angle = np.arctan2(outgoing[:, 1], outgoing[:, 0]) - np.arctan2(incoming[:, 1], incoming[:, 0])
    return np.abs(np.degrees((angle + math.pi) % TAU - math.pi))


def retag_by_angle(outline: Polyline, *, corner_deg: float = 20.0) -> Polyline:
    """Reconstruct turn/curve tags from shape alone.

    Needed after any operation that runs the outline through a library which
    does not carry the tags - shapely offsets, in practice. It is a
    reconstruction, not a recovery: a genuinely smooth corner under
    `corner_deg` becomes a curve point, and a heavily faceted curve whose
    facets exceed it becomes a run of corners. Callers that still hold the
    original tags should keep them instead of calling this.
    """
    angles = turn_angles(outline, closed=True)
    return [
        Vertex(v.x, v.y, VertexKind.TURN if angles[i] >= corner_deg else VertexKind.CURVE)
        for i, v in enumerate(outline)
    ]
