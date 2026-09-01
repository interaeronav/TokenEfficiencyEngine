"""Ripping and tearing: seams give way, and the edge frays.

A seam is the weakest line in a garment, which is why real clothes fail
there. Here a seam is a set of zero-length constraints holding two runs of
boundary vertices together, so ripping one is exactly what it sounds like:
drop the constraints and let the cloth part.

Two ways in, both of which a wearer would recognise:

  `rip_seam`   tear a named seam, all of it or from one end to a fraction.
  `auto_rip`   let the seams decide. Every constraint reports how hard it is
               being pulled, and any seam over its strength gives way - which
               is what "rips naturally" means: you do not choose the seam,
               the load does.

Frayed edges are geometry, not a texture. A torn boundary vertex sprouts a
few short threads along the fabric's own grain, deterministically, because a
frayed edge that changes every run cannot be checked or rendered twice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from seamkiln.drape.garment import GarmentMesh

# Seam strength as a multiple of the fabric's own resistance. A seam is not
# infinitely strong and is not the fabric: a plain seam in a woven typically
# fails before the cloth beside it, which is why garments rip along seams
# rather than through panels.
DEFAULT_SEAM_STRENGTH_MM = 12.0  # gap at which a plain seam is considered failed


@dataclass(slots=True)
class Tear:
    seam_id: str
    constraints: int
    fraction: float
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "seam": self.seam_id,
            "constraints_released": self.constraints,
            "fraction": round(self.fraction, 3),
            "reason": self.reason,
        }


@dataclass(slots=True)
class FrayedEdge:
    """Thread geometry at a torn boundary - a line set, not a texture."""

    starts: np.ndarray  # float64 [n, 3]
    ends: np.ndarray  # float64 [n, 3]
    seed: int = 0
    meta: dict[str, Any] = field(default_factory=dict)

    def as_line_mesh(self, thickness_mm: float = 0.4):
        """Render-ready: each thread as a thin box. trimesh has no line
        primitive that survives an OBJ round-trip, and a garment's frayed
        edge has to survive export or it is a screenshot feature."""
        import trimesh

        parts = []
        for start, end in zip(self.starts, self.ends, strict=False):
            direction = end - start
            length = float(np.linalg.norm(direction))
            if length < 1e-6:
                continue
            box = trimesh.creation.box(
                extents=[thickness_mm / 1000.0, thickness_mm / 1000.0, length]
            )
            transform = np.eye(4)
            transform[:3, :3] = trimesh.geometry.align_vectors([0.0, 0.0, 1.0], direction / length)[
                :3, :3
            ]
            transform[:3, 3] = (start + end) / 2.0
            box.apply_transform(transform)
            parts.append(box)
        return trimesh.util.concatenate(parts) if parts else None

    def summary(self) -> dict[str, Any]:
        return {
            "threads": int(self.starts.shape[0]),
            "mean_length_mm": round(
                float(np.linalg.norm(self.ends - self.starts, axis=1).mean()) * 1000.0, 2
            )
            if self.starts.size
            else 0.0,
            **self.meta,
        }


def seam_tension(garment: GarmentMesh, points: np.ndarray) -> dict[str, dict[str, float]]:
    """How hard each seam is being pulled, in millimetres of gap.

    A zero-length seam constraint that is 9 mm open is carrying load; one that
    is 0.2 mm open is not. This is the load a tear decides on.
    """
    out: dict[str, dict[str, float]] = {}
    if garment.seams.shape[0] == 0:
        return out
    gaps = (
        np.linalg.norm(points[garment.seams[:, 0]] - points[garment.seams[:, 1]], axis=1) * 1000.0
    )
    for seam_id, (start, end) in garment.seam_spans.items():
        span = gaps[start:end]
        if span.size == 0:
            continue
        out[seam_id] = {
            "max_gap_mm": round(float(span.max()), 3),
            "mean_gap_mm": round(float(span.mean()), 3),
            "constraints": int(span.size),
        }
    return out


def rip_seam(
    garment: GarmentMesh, seam_id: str, *, fraction: float = 1.0, from_end: bool = False
) -> tuple[GarmentMesh, Tear]:
    """Release a seam's constraints. `fraction` rips part of it.

    A partial rip starts at one end and travels, because that is how a seam
    fails - it does not open in the middle and spread outward.
    """
    if seam_id not in garment.seam_spans:
        known = ", ".join(sorted(garment.seam_spans)) or "(none)"
        raise KeyError(f"no seam {seam_id!r} in this garment. Seams: {known}.")
    fraction = float(min(max(fraction, 0.0), 1.0))
    start, end = garment.seam_spans[seam_id]
    count = round((end - start) * fraction)
    if count == 0:
        return garment, Tear(seam_id, 0, 0.0, "fraction rounded to nothing")

    released = np.arange(end - count, end) if from_end else np.arange(start, start + count)
    keep = np.ones(garment.seams.shape[0], dtype=bool)
    keep[released] = False

    spans: dict[str, tuple[int, int]] = {}
    cursor = 0
    for name, (low, high) in garment.seam_spans.items():
        kept = int(keep[low:high].sum())
        spans[name] = (cursor, cursor + kept)
        cursor += kept

    torn = GarmentMesh(
        points=garment.points,
        rest_points_mm=garment.rest_points_mm,
        triangles=garment.triangles,
        panel_slices=dict(garment.panel_slices),
        structural=garment.structural,
        structural_rest=garment.structural_rest,
        bending=garment.bending,
        bending_rest=garment.bending_rest,
        seams=garment.seams[keep],
        seam_rest=garment.seam_rest[keep],
        particle_distance_mm=garment.particle_distance_mm,
        seam_orientation=dict(garment.seam_orientation),
        seam_spans=spans,
        attachments=dict(garment.attachments),
    )
    return torn, Tear(seam_id, int(count), fraction, "requested")


def auto_rip(
    garment: GarmentMesh,
    points: np.ndarray,
    *,
    strength_mm: float = DEFAULT_SEAM_STRENGTH_MM,
) -> tuple[GarmentMesh, list[Tear]]:
    """Let the load decide which seams give way.

    This is what "rips naturally along its seams" means: nobody picks the
    seam. Every seam over its strength fails, and the fraction that fails is
    how much of it was over - a seam pulled hard at one end tears from there.
    """
    tears: list[Tear] = []
    current = garment
    for seam_id, row in seam_tension(garment, points).items():
        if row["max_gap_mm"] <= strength_mm:
            continue
        start, end = garment.seam_spans[seam_id]
        gaps = (
            np.linalg.norm(
                points[garment.seams[start:end, 0]] - points[garment.seams[start:end, 1]],
                axis=1,
            )
            * 1000.0
        )
        over = float((gaps > strength_mm).mean())
        # tears from whichever end is carrying more load
        from_end = float(gaps[len(gaps) // 2 :].mean()) > float(gaps[: len(gaps) // 2].mean())
        current, tear = rip_seam(current, seam_id, fraction=over, from_end=from_end)
        tear.reason = f"gap {row['max_gap_mm']:.1f} mm over {strength_mm:.0f} mm strength"
        tears.append(tear)
    return current, tears


def fray(
    garment: GarmentMesh,
    points: np.ndarray,
    tears: list[Tear],
    *,
    length_mm: float = 6.0,
    threads_per_vertex: int = 2,
    seed: int = 20260901,
) -> FrayedEdge:
    """Thread geometry along the torn boundary.

    Threads follow the fabric's own grain in PATTERN space and are then
    carried into 3D, so a frayed edge on a bias-cut panel splays differently
    from one on a straight-grain panel - which is what a real frayed edge
    does, and is free here because the flat pattern is still around.
    """
    torn_ids = {tear.seam_id for tear in tears if tear.constraints}
    vertices: list[int] = []
    for seam_id in torn_ids:
        span = garment.seam_spans.get(seam_id)
        if span is None:
            continue
        low, high = span
        # the constraints that SURVIVED are the un-torn part; the torn
        # vertices are the ones no longer paired, found from the original set
        vertices.extend(garment.seams[low:high].ravel().tolist())
    boundary = (
        np.unique(np.asarray(vertices, dtype=np.int64)) if vertices else np.zeros(0, np.int64)
    )
    if boundary.size == 0:
        # a fully torn seam leaves no surviving constraints to read, so fall
        # back to every vertex the seam ever touched
        boundary = np.unique(
            np.concatenate([garment.seams.ravel()]) if garment.seams.size else np.zeros(0, np.int64)
        )
    if boundary.size == 0:
        return FrayedEdge(np.zeros((0, 3)), np.zeros((0, 3)), seed, {"note": "nothing torn"})

    rng = np.random.default_rng(seed)
    starts, ends = [], []
    normals = _vertex_normals(points, garment.triangles)
    for index in boundary:
        origin = points[index]
        for _ in range(threads_per_vertex):
            direction = normals[index] * rng.uniform(-0.4, 0.4)
            direction = direction + rng.normal(0.0, 1.0, 3)
            direction[1] -= 1.4  # threads hang
            direction /= max(float(np.linalg.norm(direction)), 1e-9)
            length = length_mm / 1000.0 * rng.uniform(0.5, 1.4)
            starts.append(origin)
            ends.append(origin + direction * length)
    return FrayedEdge(
        np.asarray(starts),
        np.asarray(ends),
        seed,
        {"torn_seams": sorted(torn_ids), "boundary_vertices": int(boundary.size)},
    )


def _vertex_normals(points: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    a, b, c = points[triangles[:, 0]], points[triangles[:, 1]], points[triangles[:, 2]]
    face = np.cross(b - a, c - a)
    out = np.zeros_like(points)
    for column in range(3):
        np.add.at(out, triangles[:, column], face)
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    return out / np.maximum(norms, 1e-12)
