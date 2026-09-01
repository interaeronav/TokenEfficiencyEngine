"""The body as a signed distance field, and a stand-in body to drape on.

Cloth collision needs one question answered a few hundred million times per
drape: *how far is this particle from the body, and which way is out?* A
mesh query cannot answer that fast enough in Python, so the body is baked
once into a signed distance grid and every query is a trilinear lookup - O(1),
allocation-free, and callable from inside a numba kernel.

The grid is built from a MESH, not from the primitives that happen to make
the stand-in mannequin, so that P3 can hand it an Anny body and change
nothing else. Construction is voxelize -> fill -> Euclidean distance
transform inside and out; the two transforms are subtracted to get the sign.
Accuracy is about half a voxel, so the voxel size is the honest knob and it
is reported in the field's own summary rather than left implicit.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import trimesh


@dataclass(slots=True)
class BodySDF:
    """Signed distance to the body on a regular grid. Metres throughout.

    Negative inside, positive outside. Queries outside the grid return the
    clamped edge value plus the distance travelled to get there, which keeps
    a particle that has flown far away from reading as "inside the body".
    """

    grid: np.ndarray  # float32 [nx, ny, nz]
    origin: np.ndarray  # float64 [3] - world position of grid[0,0,0]
    spacing: float  # metres per cell
    source: str = ""

    @property
    def shape(self) -> tuple[int, int, int]:
        return tuple(int(n) for n in self.grid.shape)  # type: ignore[return-value]

    def summary(self) -> dict[str, object]:
        return {
            "source": self.source,
            "cells": [int(n) for n in self.grid.shape],
            "voxel_mm": round(self.spacing * 1000.0, 3),
            "accuracy_mm": round(self.spacing * 500.0, 3),  # ~half a voxel
            "bounds_m": [
                [round(float(v), 4) for v in self.origin],
                [
                    round(float(v), 4)
                    for v in self.origin + np.array(self.grid.shape) * self.spacing
                ],
            ],
            "memory_mb": round(self.grid.nbytes / 1e6, 2),
        }

    def sample(self, points: np.ndarray) -> np.ndarray:
        """Trilinear signed distance at world points. float64 [n]."""
        return _sample_grid(self.grid, self.origin, self.spacing, np.asarray(points, np.float64))

    def gradient(self, points: np.ndarray, *, epsilon: float | None = None) -> np.ndarray:
        """Outward normal, by central differences. float64 [n, 3]."""
        h = epsilon if epsilon is not None else self.spacing
        out = np.empty((len(points), 3), dtype=np.float64)
        for axis in range(3):
            step = np.zeros(3)
            step[axis] = h
            out[:, axis] = self.sample(points + step) - self.sample(points - step)
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.maximum(norms, 1e-12)


def _sample_grid(
    grid: np.ndarray, origin: np.ndarray, spacing: float, points: np.ndarray
) -> np.ndarray:
    local = (points - origin) / spacing
    shape = np.array(grid.shape) - 1
    clamped = np.clip(local, 0.0, shape)
    outside = np.linalg.norm((local - clamped) * spacing, axis=1)

    base = np.floor(clamped).astype(np.int64)
    base = np.minimum(base, shape - 1)
    frac = clamped - base
    value = np.zeros(len(points))
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                weight = (
                    (frac[:, 0] if dx else 1 - frac[:, 0])
                    * (frac[:, 1] if dy else 1 - frac[:, 1])
                    * (frac[:, 2] if dz else 1 - frac[:, 2])
                )
                value += weight * grid[base[:, 0] + dx, base[:, 1] + dy, base[:, 2] + dz]
    # a point outside the grid is at least as far out as the trip to its edge
    return value + outside


def body_shell(mesh: trimesh.Trimesh, *, min_extent: float = 0.06) -> trimesh.Trimesh:
    """The body, without the loose shells that come inside a real model.

    Anny ships eyeballs and a tongue as SEPARATE closed shells inside the
    head - 140 to 448 faces each, completely invisible, and they broke
    landmark detection outright: "the highest slice where the body has two or
    more cross-sections" fired at EYE height, so the shoulder was placed on
    top of the head and every garment was sized from a 1,289 mm "chest".

    Keeping only the LARGEST shell was the first fix and it was worse: the
    stand-in mannequin is assembled from overlapping capsules that never
    share vertices, so "largest" kept the torso and threw away the arms, the
    head and the legs. The right test is size relative to the whole body -
    an eye is 2% of a body's diagonal, an arm is 43%.
    """
    parts = mesh.split(only_watertight=False)
    if len(parts) <= 1:
        return mesh
    whole = float(np.linalg.norm(mesh.bounds[1] - mesh.bounds[0]))
    kept = [
        part
        for part in parts
        if float(np.linalg.norm(part.bounds[1] - part.bounds[0])) / max(whole, 1e-9) >= min_extent
    ]
    if not kept:
        return max(parts, key=lambda part: len(part.faces))
    if len(kept) == len(parts):
        return mesh
    merged = trimesh.util.concatenate(kept)
    merged.merge_vertices()
    return merged


def sdf_from_mesh(
    mesh: trimesh.Trimesh, *, voxel_mm: float = 8.0, pad_mm: float = 60.0, source: str = ""
) -> BodySDF:
    """Bake a watertight mesh into a signed distance grid."""
    if not mesh.is_watertight:
        # not fatal - fill() still does something sensible - but the caller
        # deserves to know the sign may be wrong in a leaky region
        mesh = mesh.copy()
        mesh.fill_holes()

    pitch = voxel_mm / 1000.0
    pad = pad_mm / 1000.0
    voxels = trimesh.voxel.creation.voxelize(mesh, pitch=pitch).fill()
    occupancy = np.asarray(voxels.matrix, dtype=bool)

    padding = max(1, int(np.ceil(pad / pitch)))
    padded = np.pad(occupancy, padding, mode="constant", constant_values=False)

    from scipy import ndimage

    outside = ndimage.distance_transform_edt(~padded) * pitch
    inside = ndimage.distance_transform_edt(padded) * pitch
    signed = (outside - inside).astype(np.float32)

    origin = np.asarray(voxels.transform[:3, 3], dtype=np.float64) - padding * pitch
    return BodySDF(
        grid=signed,
        origin=origin,
        spacing=pitch,
        source=source or f"mesh {len(mesh.vertices)}v {len(mesh.faces)}f",
    )


def _capsule_between(a: np.ndarray, b: np.ndarray, radius: float, segments: int = 20):
    """A capsule spanning two points.

    Built from endpoints rather than translate-plus-rotate on purpose: the
    first version of this mannequin used height/rotation/offset triples and
    produced a body with a floating neck, buried hips and arms pointing at
    the ceiling. Nobody caught it from the numbers - the render caught it.
    Endpoints are checkable by reading them.
    """
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    axis = b - a
    length = float(np.linalg.norm(axis))
    if length < 1e-9:
        return trimesh.creation.icosphere(subdivisions=2, radius=radius).apply_translation(a)
    mesh = trimesh.creation.capsule(height=length, radius=radius, count=[segments, segments])
    # MEASURED: trimesh's capsule is CENTRED on the origin along +Z, spanning
    # height + 2*radius in total - it does not start at the origin. Translating
    # to `a` therefore extends the limb half its length BACKWARDS, which put
    # this mannequin's arms above its shoulders and merged them into the chest
    # section, so the measured chest girth came back 1.83 m for a 1.00 m body.
    # The midpoint is the correct target.
    transform = trimesh.geometry.align_vectors([0.0, 0.0, 1.0], axis / length)
    mesh.apply_transform(transform)
    mesh.apply_translation((a + b) / 2.0)
    return mesh


def mannequin(
    *, height: float = 1.75, chest: float = 1.00, pose: str = "a-pose"
) -> trimesh.Trimesh:
    """A stand-in body, in seamkiln's own Y-up world. Metres.

    Deliberately crude and deliberately a MESH: P2 needs something to drape
    on that is reproducible and needs no download, and P3 replaces it with
    Anny (Apache-2.0) without touching anything downstream, because
    everything downstream only ever sees `sdf_from_mesh`.

    `chest` is a circumference, so the number a pattern maker already has is
    the one that goes in - and `body_landmarks` measures it back out, which
    is how this stays honest (1.00 in, 0.99 measured).
    """
    if pose != "a-pose":
        raise ValueError(f"only 'a-pose' is modelled, got {pose!r}")

    torso_r = chest / (2 * np.pi)
    shoulder_y = height * 0.82
    hip_y = height * 0.53
    # Biacromial (shoulder) width is WIDER than the chest radius on a real
    # body, and that ledge is the only thing holding up a t-shirt. The first
    # version of this mannequin was a plain capsule torso - a smooth dome
    # with nothing to catch on - and the drape slid off and landed on the
    # floor, where it scored a perfect zero for body interpenetration.
    shoulder_half = max(torso_r * 1.28, height * 0.112)
    parts = [
        _capsule_between(
            [-shoulder_half, shoulder_y, 0], [shoulder_half, shoulder_y, 0], torso_r * 0.62
        ),
        _capsule_between([0, hip_y, 0], [0, shoulder_y, 0], torso_r),  # torso
        # Hips WIDER than the chest, which is what a real body does and what
        # a t-shirt actually catches on. With narrower hips the garment slid
        # over them and onto the floor - correctly, because there was nothing
        # there to stop it.
        _capsule_between([0, height * 0.47, 0], [0, hip_y, 0], torso_r * 1.06),  # hips
        _capsule_between([0, shoulder_y, 0], [0, height * 0.87, 0], torso_r * 0.34),  # neck
        trimesh.creation.icosphere(subdivisions=2, radius=height * 0.066).apply_translation(
            [0.0, height * 0.93, 0.0]
        ),
    ]

    # arms hang DOWN and out at 35 degrees from vertical - the A-pose a
    # garment is draped over. Down, not up: the first version had the sign
    # wrong and the render made it obvious in one look.
    reach = height * 0.42
    tilt = np.radians(35.0)
    for side in (-1.0, 1.0):
        shoulder = np.array([side * shoulder_half, shoulder_y - height * 0.015, 0.0])
        hand = shoulder + np.array([side * reach * np.sin(tilt), -reach * np.cos(tilt), 0.0])
        parts.append(_capsule_between(shoulder, hand, torso_r * 0.30))

    leg_reach = height * 0.47
    for side in (-1.0, 1.0):
        hip = np.array([side * torso_r * 0.45, height * 0.48, 0.0])
        parts.append(_capsule_between(hip, hip - np.array([0.0, leg_reach, 0.0]), torso_r * 0.42))

    body = trimesh.util.concatenate(parts)
    body.merge_vertices()
    return body


def measure_penetration(points: np.ndarray, sdf: BodySDF) -> dict[str, float]:
    """How far inside the body anything got. The drape's pass/fail number.

    Reported in millimetres and never as a boolean: "0.4 mm inside" is a
    float32 grid rounding, "40 mm inside" is a solver that tunnelled, and a
    boolean cannot tell those apart.
    """
    distances = sdf.sample(points)
    worst = float(distances.min())
    return {
        "min_distance_mm": round(worst * 1000.0, 3),
        "penetrating_points": int((distances < 0.0).sum()),
        "deepest_penetration_mm": round(max(-worst, 0.0) * 1000.0, 3),
        "voxel_mm": round(sdf.spacing * 1000.0, 3),
    }


def measure_contact(points: np.ndarray, sdf: BodySDF, *, near_mm: float = 12.0) -> dict[str, float]:
    """Is the garment actually ON the body?

    Written because a drape that fell off scored a PERFECT zero for
    interpenetration - the one metric the acceptance criteria named - while
    lying on the floor. "Nothing inside the body" and "worn" are different
    claims and a drape report has to make both.
    """
    distances = sdf.sample(points)
    near = float((np.abs(distances) < near_mm / 1000.0).mean())
    return {
        "touching_fraction": round(near, 4),
        "mean_distance_mm": round(float(distances.mean()) * 1000.0, 2),
        "max_distance_mm": round(float(distances.max()) * 1000.0, 2),
        "worn": bool(near > 0.15),
    }
