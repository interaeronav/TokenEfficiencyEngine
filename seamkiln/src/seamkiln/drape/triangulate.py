"""Panel -> triangle mesh, at a chosen particle distance. No Triangle.

Shewchuk's Triangle is the obvious library for constrained Delaunay and it
**may not be included in a commercial product** without an arrangement with
its author; `meshpy` and the `triangle` wheel wrap it and inherit that. The
licence gate in tests/test_licences.py fails the build if either appears, so
this is the implementation that lets the gate stay closed:

  1. resample the boundary at the target spacing, keeping every corner;
  2. fill the interior with a TRIANGULAR lattice (rows offset by half a
     step, row pitch step*sqrt(3)/2), which is equilateral by construction -
     so the mesh starts well-shaped instead of being smoothed into shape;
  3. unconstrained Delaunay over boundary + interior points (scipy/Qhull);
  4. drop triangles whose centroid is outside the panel.

Step 4 is what makes it conforming: the boundary points are all present, so
no triangle can cross the outline without a centroid outside it. Concave
panels, notch bites and internal cutouts all fall out of the same test.

"Particle distance" is the incumbents' name for the target edge length, and
it is the single knob that trades drape detail for solve time.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

import numpy as np
from scipy.spatial import Delaunay
from shapely.geometry import Point, Polygon

from seamkiln.pattern.geometry import Polyline, cumulative_length, to_array
from seamkiln.pattern.model import LineKind, Panel


@dataclass(slots=True)
class PanelMesh:
    """A triangulated panel, still in 2D pattern space (millimetres)."""

    panel_id: str
    points: np.ndarray  # float64 [n, 2]
    triangles: np.ndarray  # int32 [m, 3]
    boundary: np.ndarray  # int32 [b] - indices into points, in outline order
    boundary_t: np.ndarray  # float64 [b] - normalised arc length of each

    @property
    def n_points(self) -> int:
        return int(self.points.shape[0])

    def edge_pairs(self) -> np.ndarray:
        """Unique undirected edges as an int32 [k, 2] array."""
        tri = self.triangles
        edges = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
        edges = np.sort(edges, axis=1)
        return np.unique(edges, axis=0).astype(np.int32)

    def quality(self) -> dict[str, float]:
        """Smallest angle and area spread - a mesh health report, not a dump."""
        p = self.points
        a, b, c = p[self.triangles[:, 0]], p[self.triangles[:, 1]], p[self.triangles[:, 2]]
        sides = np.stack(
            [
                np.linalg.norm(b - c, axis=1),
                np.linalg.norm(a - c, axis=1),
                np.linalg.norm(a - b, axis=1),
            ],
            axis=1,
        )
        areas = 0.5 * np.abs(
            (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1])
        )
        longest = sides.max(axis=1)
        # smallest angle, from the law of cosines on the shortest side
        order = np.sort(sides, axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            cos_min = (order[:, 1] ** 2 + order[:, 2] ** 2 - order[:, 0] ** 2) / (
                2 * order[:, 1] * order[:, 2]
            )
        angles = np.degrees(np.arccos(np.clip(cos_min, -1.0, 1.0)))
        return {
            "triangles": int(self.triangles.shape[0]),
            "points": self.n_points,
            "min_angle_deg": round(float(angles.min()), 2),
            "mean_angle_deg": round(float(angles.mean()), 2),
            "min_area_mm2": round(float(areas.min()), 4),
            "max_edge_mm": round(float(longest.max()), 3),
        }


MERGE_FRACTION = 0.5


def resample_closed(
    outline: Polyline, spacing: float, *, merge_fraction: float = MERGE_FRACTION
) -> tuple[np.ndarray, np.ndarray]:
    """Boundary points at `spacing`, with every corner kept.

    Original vertices are kept rather than replaced because they carry the
    outline's shape - drop a corner and the panel changes. Extra points are
    inserted between them where the gap is larger than the target.

    `merge_fraction` drops a CURVE vertex that lies closer than that
    fraction of `spacing` to the last kept point; corners are never
    dropped. At 0 every original vertex is kept, and an outline sampled
    every 5 mm on a 12 mm mesh leaves a fringe of short edges round every
    piece: on the tee block 678 edges under a quarter of the spacing and
    1,015 more under three quarters, which the strain report could not
    exclude (it printed 31 % for sleeves carrying 7) and which were the
    amplifier in the run's tunnelling. At the default 0.5 the block keeps
    four of the first and 408 of the second, its worst seam closes from
    12.6 mm to 5.1 and the report reads 9.2 % against a fringe-free 8.3,
    while every bundled fabric's Cusick coefficient stays within 0.001 of
    where it was; 0.7 removes the rest of the fringe but moves chiffon's
    coefficient 0.016. Measured 2026-09-04.
    """
    from seamkiln.pattern.geometry import VertexKind

    ring = to_array(outline)
    lengths = cumulative_length([*outline, outline[0]])
    total = float(lengths[-1])
    if total <= 0.0:
        raise ValueError("degenerate outline: zero perimeter")

    keep = [0]
    if merge_fraction > 0.0:
        floor = merge_fraction * spacing
        for index in range(1, len(ring)):
            corner = getattr(outline[index], "kind", VertexKind.TURN) is VertexKind.TURN
            gap = float(np.linalg.norm(ring[index] - ring[keep[-1]]))
            closing = float(np.linalg.norm(ring[index] - ring[0]))
            if corner or (gap >= floor and closing >= floor):
                keep.append(index)
    else:
        keep = list(range(len(ring)))

    points: list[np.ndarray] = []
    params: list[float] = []
    kept = [*keep, keep[0]]
    for a, b in pairwise(kept):
        start, end = ring[a], ring[b]
        span = float(np.linalg.norm(end - start))
        steps = max(1, int(np.ceil(span / spacing)))
        # arc-length parameters stay the outline's own, so seams keep
        # their place on it whether or not a vertex between was merged
        length_a = float(lengths[a])
        length_b = float(lengths[b]) if b != keep[0] else total
        for k in range(steps):
            fraction = k / steps
            points.append(start + (end - start) * fraction)
            params.append((length_a + (length_b - length_a) * fraction) / total)
    return np.asarray(points, dtype=np.float64), np.asarray(params, dtype=np.float64)


def _lattice(polygon: Polygon, spacing: float, inset: float) -> np.ndarray:
    """Interior points on a triangular lattice, kept clear of the boundary.

    The inset stops lattice points landing a hair inside the outline and
    producing slivers next to the boundary points that are already there.
    """
    minx, miny, maxx, maxy = polygon.bounds
    pitch = spacing * np.sqrt(3.0) / 2.0
    rows = int(np.ceil((maxy - miny) / pitch)) + 1
    shrunk = polygon.buffer(-inset)
    if shrunk.is_empty:
        return np.zeros((0, 2), dtype=np.float64)

    out: list[tuple[float, float]] = []
    for row in range(rows):
        y = miny + row * pitch
        offset = 0.0 if row % 2 == 0 else spacing / 2.0
        count = int(np.ceil((maxx - minx) / spacing)) + 1
        for column in range(count):
            x = minx + offset + column * spacing
            if shrunk.covers(Point(x, y)):
                out.append((x, y))
    return np.asarray(out, dtype=np.float64) if out else np.zeros((0, 2), dtype=np.float64)


def _relax(points: np.ndarray, triangles: np.ndarray, fixed: int, passes: int) -> np.ndarray:
    """Laplacian smoothing of interior points only; boundary points never move.

    Slivers appear where the resampled boundary and the lattice interleave
    badly. Averaging each interior point toward its neighbours pulls those
    apart. The boundary is held because moving it would change the panel.
    """
    if passes <= 0 or points.shape[0] <= fixed:
        return points
    edges = np.vstack([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]])
    both = np.vstack([edges, edges[:, ::-1]])
    relaxed = points.copy()
    for _ in range(passes):
        total = np.zeros_like(relaxed)
        count = np.zeros(relaxed.shape[0])
        np.add.at(total, both[:, 0], relaxed[both[:, 1]])
        np.add.at(count, both[:, 0], 1.0)
        moving = count > 0
        moving[:fixed] = False
        relaxed[moving] = total[moving] / count[moving, None]
    return relaxed


def triangulate_panel(
    panel: Panel,
    *,
    particle_distance: float = 20.0,
    include_cutouts: bool = True,
    relax_passes: int = 2,
    merge_fraction: float = MERGE_FRACTION,
) -> PanelMesh:
    """Triangulate one panel at the given particle distance (mm).

    `merge_fraction` merges outline curve vertices closer than that
    fraction of the particle distance (see `resample_closed`)."""
    if particle_distance <= 0.0:
        raise ValueError(f"particle_distance must be > 0 mm, got {particle_distance}")

    minx, miny, maxx, maxy = panel.bbox
    narrowest = min(maxx - minx, maxy - miny)
    if particle_distance > narrowest / 4.0:
        raise ValueError(
            f"panel {panel.id}: particle_distance {particle_distance:g} mm is too coarse "
            f"for a piece {narrowest:.0f} mm across - use {narrowest / 8:.0f} mm or finer. "
            "A garment meshed this coarsely does not merely look blocky: its shoulder "
            "and armhole seams get three or four points each, which is not enough "
            "structure to hold the garment on the body, and it slides off."
        )

    boundary_points, boundary_t = resample_closed(
        panel.outline, particle_distance, merge_fraction=merge_fraction
    )
    polygon = Polygon(to_array(panel.outline))
    if not polygon.is_valid:
        polygon = polygon.buffer(0)
    if include_cutouts:
        for internal in panel.internals:
            if internal.kind is LineKind.CUTOUT and internal.closed:
                polygon = polygon.difference(Polygon(to_array(internal.points)))
    if polygon.geom_type != "Polygon":
        raise ValueError(
            f"panel {panel.id}: cutouts split it into {polygon.geom_type}; "
            "triangulate the pieces separately"
        )

    interior = _lattice(polygon, particle_distance, particle_distance * 0.55)
    points = np.vstack([boundary_points, interior]) if interior.size else boundary_points
    if points.shape[0] < 3:
        raise ValueError(
            f"panel {panel.id}: only {points.shape[0]} points at "
            f"particle_distance={particle_distance} mm - use a finer distance"
        )

    triangulation = Delaunay(points)
    if relax_passes:
        points = _relax(points, triangulation.simplices, boundary_points.shape[0], relax_passes)
        triangulation = Delaunay(points)
    centroids = points[triangulation.simplices].mean(axis=1)
    # `covers` rather than `contains`: a centroid exactly on the boundary of a
    # sliver is inside the panel, and rejecting it would punch a hole.
    keep = np.fromiter(
        (polygon.covers(Point(x, y)) for x, y in centroids), dtype=bool, count=len(centroids)
    )
    triangles = triangulation.simplices[keep].astype(np.int32)
    if triangles.shape[0] == 0:
        raise ValueError(f"panel {panel.id}: no triangle survived the containment test")

    return PanelMesh(
        panel_id=panel.id,
        points=points,
        triangles=triangles,
        boundary=np.arange(boundary_points.shape[0], dtype=np.int32),
        boundary_t=boundary_t,
    )
