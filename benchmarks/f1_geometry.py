"""Filled-polygon distances and a continuous rigid-rotation clearance bound.

This is a two-dimensional geometry check, not a surface/solid collision test.
Coordinates share any one length unit; returned gaps use that same unit. Sweep
coverage is exactly the closed interval between its first and last samples.
"""

from __future__ import annotations

import math
import sys
from collections.abc import Sequence
from fractions import Fraction
from itertools import pairwise
from typing import Any

Point = tuple[float, float]
Polygon = Sequence[Sequence[float]]


def _orientation(a: Point, b: Point, c: Point) -> int:
    """Orientation with an exact fallback for cancellation/collinearity.

    Fractions describe the supplied binary floats exactly; the fallback does
    not turn a narrow real gap into a crossing because of a fixed tolerance.
    """
    ux, uy = b[0] - a[0], b[1] - a[1]
    vx, vy = c[0] - a[0], c[1] - a[1]
    p, q = ux * vy, uy * vx
    determinant = p - q
    error = 8 * sys.float_info.epsilon * (abs(p) + abs(q))
    if math.isfinite(determinant) and abs(determinant) > error:
        return 1 if determinant > 0 else -1
    ax, ay = map(Fraction, a)
    bx, by = map(Fraction, b)
    cx, cy = map(Fraction, c)
    exact = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    return (exact > 0) - (exact < 0)


def _segments_intersect(a: Point, b: Point, c: Point, d: Point) -> bool:
    # The inclusive box check also rejects disjoint collinear segments.
    if any(
        max(min(a[i], b[i]), min(c[i], d[i])) > min(max(a[i], b[i]), max(c[i], d[i]))
        for i in (0, 1)
    ):
        return False
    return (
        _orientation(a, b, c) * _orientation(a, b, d) <= 0
        and _orientation(c, d, a) * _orientation(c, d, b) <= 0
    )


def _edges(points: Sequence[Point]) -> list[tuple[Point, Point]]:
    return list(zip(points, [*points[1:], points[0]], strict=True))


def _polygon(points: Polygon) -> list[Point]:
    try:
        result = [tuple(float(value) for value in point) for point in points]
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("A polygon needs finite pairs of coordinates.") from exc
    if any(len(point) != 2 or not all(map(math.isfinite, point)) for point in result):
        raise ValueError("A polygon needs finite pairs of coordinates.")
    if len(result) > 1 and result[0] == result[-1]:
        result.pop()  # Accept both common closed-ring conventions.
    if len(result) < 3:
        raise ValueError("A polygon needs at least three distinct vertices.")
    typed = [(point[0], point[1]) for point in result]
    edges = _edges(typed)
    if any(a == b for a, b in edges):
        raise ValueError("A polygon cannot have a zero-length edge.")
    # Exact area avoids cancellation for a small polygon far from the origin.
    twice_area = sum(
        Fraction(a[0]) * Fraction(b[1]) - Fraction(a[1]) * Fraction(b[0]) for a, b in edges
    )
    if twice_area == 0:
        raise ValueError("A polygon must enclose a nonzero area.")
    for i, (a, b) in enumerate(edges):
        for j in range(i + 1, len(edges)):
            if j == i + 1 or (i == 0 and j == len(edges) - 1):
                continue
            if _segments_intersect(a, b, *edges[j]):
                raise ValueError(
                    "A polygon must be simple: nonadjacent edges cannot touch or cross."
                )
    return typed


def _inside(point: Point, edges: list[tuple[Point, Point]]) -> bool:
    winding = 0
    for a, b in edges:
        if a[1] <= point[1] < b[1] and _orientation(a, b, point) > 0:
            winding += 1
        elif b[1] <= point[1] < a[1] and _orientation(a, b, point) < 0:
            winding -= 1
    return winding != 0


def _point_segment(point: Point, a: Point, b: Point) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    if not math.isfinite(length):
        raise ValueError("Coordinate differences exceed floating-point range.")
    ux, uy = dx / length, dy / length
    projection = (point[0] - a[0]) * ux + (point[1] - a[1]) * uy
    along = min(length, max(0.0, projection))
    return math.hypot(point[0] - (a[0] + along * ux), point[1] - (a[1] + along * uy))


def _gap(a: list[Point], b: list[Point]) -> float:
    ae, be = _edges(a), _edges(b)
    best = math.inf
    for ap, aq in ae:
        for bp, bq in be:
            if _segments_intersect(ap, aq, bp, bq):
                return 0.0
            best = min(
                best,
                _point_segment(ap, bp, bq),
                _point_segment(aq, bp, bq),
                _point_segment(bp, ap, aq),
                _point_segment(bq, ap, aq),
            )
    if _inside(a[0], be) or _inside(b[0], ae):
        return 0.0
    if not math.isfinite(best):
        raise ValueError("Polygon distance exceeds floating-point range.")
    return best


def polygon_gap(a: Polygon, b: Polygon) -> float:
    """Minimum separation of filled simple polygons, including every edge pair.

    Crossing, touching, collinear overlap and full containment all return zero.
    A polygon's winding and whether its last vertex repeats the first do not
    change the answer. Holes and self-intersecting polygons are unsupported.
    """
    return _gap(_polygon(a), _polygon(b))


def rotate(points: Polygon, deg: float) -> list[list[float]]:
    """Rotate a simple polygon counterclockwise about (0, 0), in degrees."""
    polygon = _polygon(points)
    angle = float(deg)
    if not math.isfinite(angle):
        raise ValueError("A rotation angle must be finite.")
    radians = math.radians(angle % 360)
    cosine, sine = math.cos(radians), math.sin(radians)
    return [[x * cosine - y * sine, x * sine + y * cosine] for x, y in polygon]


def sweep_clearance(fixed: Polygon, moving: Polygon, angles_deg: Sequence[float]) -> dict[str, Any]:
    """Bound clearance continuously over a uniformly sampled angular interval.

    Samples must be finite, strictly increasing, and uniformly spaced. Both
    endpoints are included. The caller must check that those endpoints equal
    the intended sweep; no coverage outside [first, last] is inferred.

    A moving point at radius <= R travels at most 2R*sin(step/4) between any
    angle and its nearest sample. Distance to a fixed filled polygon is
    1-Lipschitz, so min(sample gaps) minus that displacement bounds the entire
    sweep. A nonpositive bound is inconclusive, never a clearance pass.
    """
    a, b = _polygon(fixed), _polygon(moving)
    try:
        angles = [float(angle) for angle in angles_deg]
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Sweep samples must be finite angles.") from exc
    if len(angles) < 2 or not all(map(math.isfinite, angles)):
        raise ValueError("A sweep needs at least two finite endpoint samples.")
    steps = [right - left for left, right in pairwise(angles)]
    if any(step <= 0 or not math.isfinite(step) for step in steps):
        raise ValueError("Sweep angles must be strictly increasing, with both endpoints included.")
    step = max(steps)
    if step > 360:
        raise ValueError("Adjacent sweep samples must be at most 360 degrees apart.")
    if any(not math.isclose(delta, step, rel_tol=1e-12, abs_tol=0.0) for delta in steps):
        raise ValueError("Sweep angles must be uniformly spaced, including both endpoints.")
    samples = []
    for angle in angles:
        radians = math.radians(angle % 360)
        cosine, sine = math.cos(radians), math.sin(radians)
        transformed = [(x * cosine - y * sine, x * sine + y * cosine) for x, y in b]
        samples.append({"angle_deg": angle, "gap": _gap(a, transformed)})
    radius = max(math.hypot(x, y) for x, y in b)
    penalty = 2 * radius * math.sin(math.radians(step) / 4)
    minimum = min(sample["gap"] for sample in samples)
    # Account conservatively for double-precision rotation/distance arithmetic
    # in addition to the geometric sampling penalty, especially at tangency.
    scale = max(radius, minimum, *(abs(value) for point in a for value in point))
    allowance = 128 * math.ulp(scale)
    lower = minimum - penalty - allowance
    return {
        "interval_deg": [angles[0], angles[-1]],
        "samples": samples,
        "sample_count": len(samples),
        "radius": radius,
        "max_step_deg": step,
        "min_sample_gap": minimum,
        "sampling_penalty": penalty,
        "roundoff_allowance": allowance,
        "lower_bound": lower,
        "certified_clearance": lower > 0,
        "method": "all edge pairs, containment, nearest-sample rotation displacement bound",
    }
