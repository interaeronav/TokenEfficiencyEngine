"""Symmetry sync: mesh half a symmetric panel and mirror the rest.

Most pattern pieces are symmetric about their own centre line - a front, a
back, a sleeve. Meshing the whole thing is doing the same work twice and
getting two DIFFERENT answers: the triangulator's lattice does not land the
same way on both halves, so the left and the right of one piece end up with
different topology, different vertex counts, and different stiffness. The
garment then drapes very slightly asymmetrically for no reason anyone can
point at.

Meshing one half and mirroring it fixes both at once:

  * the topology is exactly balanced - every vertex on the left has a twin,
    so the piece behaves the same either way round;
  * it is faster, because the expensive part (Delaunay plus the containment
    test) runs on half the points.

`detect_axis` finds the mirror line if there is one, `sync` makes a
nearly-symmetric panel exactly symmetric, and `triangulate_symmetric` is the
mesher that uses it.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import numpy as np

from seamkiln.pattern.geometry import Vertex, to_array
from seamkiln.pattern.model import Panel

# How far a panel may be from symmetric and still be called symmetric, as a
# fraction of its own width. Cloth is cut to a millimetre, not a micron.
TOLERANCE = 0.01


@dataclass(slots=True)
class Symmetry:
    axis_x: float
    deviation_mm: float
    symmetric: bool
    tested: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "axis_x_mm": round(self.axis_x, 3),
            "max_deviation_mm": round(self.deviation_mm, 3),
            "symmetric": self.symmetric,
            "points_tested": self.tested,
        }


def detect_axis(panel: Panel, *, tolerance: float = TOLERANCE) -> Symmetry:
    """Is this panel symmetric about a vertical line, and where?

    The axis is the midpoint of the bounding box, not a fitted line: a
    pattern piece is drafted about a centre, and a least-squares axis on a
    piece that is nearly-but-not-quite symmetric would move the centre to
    split the difference, which is the wrong repair.
    """
    points = to_array(panel.outline)
    minx, maxx = float(points[:, 0].min()), float(points[:, 0].max())
    axis = (minx + maxx) / 2.0
    width = max(maxx - minx, 1e-9)

    reflected = points.copy()
    reflected[:, 0] = 2.0 * axis - reflected[:, 0]
    # nearest-neighbour both ways: a point with no twin is what breaks symmetry
    deviation = 0.0
    for probe in (points, reflected):
        other = reflected if probe is points else points
        for point in probe:
            deviation = max(deviation, float(np.linalg.norm(other - point, axis=1).min()))
    return Symmetry(
        axis_x=axis,
        deviation_mm=deviation,
        symmetric=deviation <= tolerance * width,
        tested=int(points.shape[0]),
    )


class SymmetryError(ValueError):
    """A panel that cannot be treated as symmetric."""


def sync(panel: Panel, *, keep: str = "right", axis_x: float | None = None) -> Panel:
    """Make a nearly-symmetric panel exactly symmetric.

    One half is authoritative and the other is replaced by its mirror, so the
    result is symmetric to the last decimal rather than to a tolerance. Which
    half wins is the caller's call, because on a hand-drafted block one side
    is usually the one that was drawn carefully.
    """
    if keep not in ("left", "right"):
        raise SymmetryError(f"keep must be 'left' or 'right', got {keep!r}")
    found = detect_axis(panel)
    axis = found.axis_x if axis_x is None else float(axis_x)

    kept: list[Vertex] = []
    for vertex in panel.outline:
        side = vertex.x - axis
        if (keep == "right" and side >= -1e-9) or (keep == "left" and side <= 1e-9):
            kept.append(vertex)
    if len(kept) < 2:
        raise SymmetryError(
            f"panel {panel.id} has {len(kept)} point(s) on its {keep} side of "
            f"x={axis:.1f}: it is not a half-symmetric piece."
        )

    ordered = sorted(kept, key=lambda v: (v.y, v.x))
    mirrored = [
        Vertex(2.0 * axis - v.x, v.y, v.kind)
        for v in reversed(ordered)
        if abs(v.x - axis) > 1e-9  # a point ON the axis is its own twin
    ]
    outline = [*ordered, *mirrored]
    return Panel(
        id=panel.id,
        name=panel.name,
        outline=outline,
        internals=list(panel.internals),
        marks=list(panel.marks),
        seam_allowance_mm=panel.seam_allowance_mm,
        meta={**panel.meta, "synced": f"{keep} half about x={axis:.1f}"},
    )


def triangulate_symmetric(
    panel: Panel, *, particle_distance: float = 15.0, keep: str = "right", **kwargs: Any
):
    """Mesh half the panel and mirror it - balanced topology, half the work.

    Returns the same `PanelMesh` the ordinary mesher does, so nothing
    downstream needs to know. The seam down the middle is welded: points on
    the axis are shared rather than duplicated, or the piece would split
    along its own centre line the moment it was draped.
    """
    from scipy.spatial import Delaunay
    from shapely.geometry import Point, Polygon, box

    from seamkiln.drape.triangulate import PanelMesh, _lattice, resample_closed

    found = detect_axis(panel)
    if not found.symmetric:
        raise SymmetryError(
            f"panel {panel.id} is not symmetric: its worst point is "
            f"{found.deviation_mm:.1f} mm from its mirror. Run `sync` first, or "
            "mesh it whole with triangulate_panel."
        )

    started = time.perf_counter()
    axis = found.axis_x
    polygon = Polygon(to_array(panel.outline))
    if not polygon.is_valid:
        polygon = polygon.buffer(0)
    minx, miny, maxx, maxy = polygon.bounds
    pad = (maxx - minx) + (maxy - miny)
    half_plane = (
        box(axis, miny - pad, maxx + pad, maxy + pad)
        if keep == "right"
        else box(minx - pad, miny - pad, axis, maxy + pad)
    )
    half_polygon = polygon.intersection(half_plane)
    if half_polygon.geom_type != "Polygon" or half_polygon.is_empty:
        raise SymmetryError(
            f"panel {panel.id}: its {keep} half is {half_polygon.geom_type}, not one "
            "piece - a symmetric panel's half must be a single region."
        )

    boundary, params = resample_closed(panel.outline, particle_distance)
    side = boundary[:, 0] - axis
    keep_mask = side >= -1e-9 if keep == "right" else side <= 1e-9
    half_boundary = boundary[keep_mask]
    half_params = params[keep_mask]

    interior = _lattice(half_polygon, particle_distance, particle_distance * 0.55)
    points = np.vstack([half_boundary, interior]) if interior.size else half_boundary
    if points.shape[0] < 3:
        raise SymmetryError(
            f"panel {panel.id}: only {points.shape[0]} point(s) in its {keep} half at "
            f"particle_distance={particle_distance} mm - use a finer distance."
        )

    # Delaunay the HALF only: this is the expensive step and doing it once
    # instead of over the whole piece is the point of the exercise.
    triangulation = Delaunay(points)
    centroids = points[triangulation.simplices].mean(axis=1)
    inside = np.fromiter(
        (half_polygon.covers(Point(x, y)) for x, y in centroids),
        dtype=bool,
        count=len(centroids),
    )
    half_triangles = triangulation.simplices[inside].astype(np.int32)
    if half_triangles.shape[0] == 0:
        raise SymmetryError(f"panel {panel.id}: no triangle survived in the {keep} half")

    # Mirror the POINTS and the TRIANGLES. Points on the axis are shared, not
    # doubled, or the piece would split down its own centre line the moment it
    # was draped - and the mirrored winding is reversed so both halves face
    # the same way.
    on_axis = np.abs(points[:, 0] - axis) <= 1e-9
    twin_of = np.full(points.shape[0], -1, dtype=np.int32)
    twin_of[on_axis] = np.flatnonzero(on_axis)
    off = np.flatnonzero(~on_axis)
    twin_of[off] = np.arange(off.size, dtype=np.int32) + points.shape[0]

    mirrored_points = points[off].copy()
    mirrored_points[:, 0] = 2.0 * axis - mirrored_points[:, 0]
    full = np.vstack([points, mirrored_points])
    mirrored_triangles = twin_of[half_triangles][:, [0, 2, 1]]
    triangles = np.vstack([half_triangles, mirrored_triangles]).astype(np.int32)

    seconds = time.perf_counter() - started
    # the boundary is the half's boundary plus its mirror, in outline order
    half_boundary_index = np.arange(half_boundary.shape[0], dtype=np.int32)
    mirrored_boundary = twin_of[half_boundary_index]
    keep_mirror = mirrored_boundary != half_boundary_index
    boundary_index = np.concatenate([half_boundary_index, mirrored_boundary[keep_mirror][::-1]])
    boundary_t = np.concatenate([half_params, (1.0 - half_params[keep_mirror])[::-1]])
    order = np.argsort(boundary_t)

    return PanelMesh(
        panel_id=panel.id,
        points=full,
        triangles=triangles,
        boundary=boundary_index[order].astype(np.int32),
        boundary_t=np.clip(boundary_t[order], 0.0, 1.0),
    ), {
        "axis_x_mm": round(axis, 2),
        "half_points": int(points.shape[0]),
        "total_points": int(full.shape[0]),
        "shared_on_axis": int(on_axis.sum()),
        "triangles": int(triangles.shape[0]),
        "seconds": round(seconds, 4),
    }
