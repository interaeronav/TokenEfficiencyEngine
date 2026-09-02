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

from dataclasses import dataclass, field

import numpy as np
import trimesh

from seamkiln.drape.environment import Environment  # noqa: F401  (re-exported)


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
    # Rigid placement of the SUBJECT, applied at query time. Moving the test
    # subject therefore costs nothing: rebuilding the field is ~1.5 s, and a
    # rotation is a 3x3 multiply. `rotation` maps world -> the field's frame.
    rotation: np.ndarray = field(default_factory=lambda: np.eye(3))
    translation: np.ndarray = field(default_factory=lambda: np.zeros(3))

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

    @property
    def placed(self) -> bool:
        return not (np.allclose(self.rotation, np.eye(3)) and np.allclose(self.translation, 0.0))

    def to_field(self, points: np.ndarray) -> np.ndarray:
        """World points -> the frame the grid was baked in."""
        if not self.placed:
            return np.asarray(points, np.float64)
        return (np.asarray(points, np.float64) - self.translation) @ self.rotation

    def moved(
        self,
        position: tuple[float, float, float] | np.ndarray = (0.0, 0.0, 0.0),
        *,
        rotation_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
        relative: bool = False,
    ) -> BodySDF:
        """The same field, with the subject somewhere else. Cheap and exact."""
        rot = _euler_matrix(rotation_deg)
        offset = np.asarray(position, dtype=np.float64)
        if relative:
            rot = rot @ self.rotation.T
            offset = offset + self.translation
        return BodySDF(
            grid=self.grid,
            origin=self.origin,
            spacing=self.spacing,
            source=f"{self.source} placed",
            rotation=rot.T,  # world -> field
            translation=offset,
        )

    def sample(self, points: np.ndarray) -> np.ndarray:
        """Trilinear signed distance at world points. float64 [n]."""
        return _sample_grid(self.grid, self.origin, self.spacing, self.to_field(points))

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
    mesh: trimesh.Trimesh,
    *,
    voxel_mm: float = 8.0,
    pad_mm: float = 60.0,
    bounds: tuple[np.ndarray, np.ndarray] | np.ndarray | None = None,
    source: str = "",
) -> BodySDF:
    """Bake a watertight mesh into a signed distance grid.

    `bounds` (a `(lo, hi)` pair in metres) bakes the mesh onto a lattice
    that covers those bounds instead of the mesh's own: every frame of a
    moving body baked with the same `bounds` and `voxel_mm` then lands on
    ONE lattice - the same shape, origin and spacing - so two frames' fields
    can be blended cell for cell inside the solver. The embedding is exact:
    trimesh's voxel origin already sits on the pitch lattice, so the mesh's
    own grid is copied into the larger one at an integer offset and the
    distance transform runs on the larger box. A mesh that does not fit the
    bounds is refused rather than clipped.
    """
    if not mesh.is_watertight:
        # not fatal - fill() still does something sensible - but the caller
        # deserves to know the sign may be wrong in a leaky region
        mesh = mesh.copy()
        mesh.fill_holes()

    pitch = voxel_mm / 1000.0
    pad = pad_mm / 1000.0
    voxels = trimesh.voxel.creation.voxelize(mesh, pitch=pitch).fill()
    occupancy = np.asarray(voxels.matrix, dtype=bool)
    own = np.asarray(voxels.transform[:3, 3], dtype=np.float64)

    padding = max(1, int(np.ceil(pad / pitch)))
    if bounds is None:
        padded = np.pad(occupancy, padding, mode="constant", constant_values=False)
        origin = own - padding * pitch
    else:
        lo_b = np.asarray(bounds[0], dtype=np.float64)
        hi_b = np.asarray(bounds[1], dtype=np.float64)
        lo = np.floor(lo_b / pitch) * pitch - padding * pitch
        hi = np.ceil(hi_b / pitch) * pitch + padding * pitch
        shape = np.rint((hi - lo) / pitch).astype(int) + 1
        at_exact = (own - lo) / pitch
        at = np.rint(at_exact).astype(int)
        if np.abs(at_exact - at).max() > 1e-6:
            raise ValueError(
                "the mesh's voxel lattice is not on the bounds' lattice "
                f"(offset {at_exact.tolist()} cells); bake with the same voxel_mm"
            )
        end = at + np.asarray(occupancy.shape)
        if (at < 0).any() or (end > shape).any():
            raise ValueError(
                "the body leaves the lattice it was asked to bake on: mesh bounds "
                f"{np.round(mesh.bounds, 4).tolist()} vs bounds "
                f"{np.round([lo_b, hi_b], 4).tolist()} - widen `bounds` (an animation "
                "should pass the union of every frame's bounds)"
            )
        padded = np.zeros(tuple(int(n) for n in shape), dtype=bool)
        padded[at[0] : end[0], at[1] : end[1], at[2] : end[2]] = occupancy
        origin = lo

    from scipy import ndimage

    outside = ndimage.distance_transform_edt(~padded) * pitch
    inside = ndimage.distance_transform_edt(padded) * pitch
    signed = (outside - inside).astype(np.float32)

    return BodySDF(
        grid=signed,
        origin=origin,
        spacing=pitch,
        source=source or f"mesh {len(mesh.vertices)}v {len(mesh.faces)}f",
    )


@dataclass(slots=True)
class BodyMotion:
    """Where the body is at every substep of ONE drape call.

    The solver's body used to be five constants per call: the field, its
    origin and spacing, and one placement. A body that walks moved between
    calls as a jump - the animator rebaked it and teleported the garment -
    and each jump UP into the cloth resolved as a full push in one substep,
    a kick of tens of metres per second, while nothing on the way down
    pulled the cloth back. Measured: a jersey tee rode up 16 mm per walking
    stride and 40 per running stride, without saturating. This is the
    schedule that replaces the jump: entry `s` is the body after `s`
    substeps, entry 0 is `start`, entry -1 is `end`.

    Two parts. The RIGID part (`rotation`, `translation`) is exact and free:
    travel, the gait's bob, a turn. The DEFORMING part is a second field on
    the same lattice and a blend weight `mix`: the solver reads
    `d = d0 + mix * (d1 - d0)` and takes its normal from that same blended
    interpolant, so a limb that swings between two poses is a surface that
    moves continuously through the frame. `end.grid is start.grid` means no
    blend (a rigid body), and a motion whose schedule never varies is not
    `moving` at all - the solver then executes exactly the static path.
    """

    end: BodySDF
    rotation: np.ndarray  # float64 [S, 3, 3], the stored (field -> world) matrices
    translation: np.ndarray  # float64 [S, 3]
    mix: np.ndarray  # float64 [S]; 0 -> 1 across the call when `blend`
    blend: bool
    moving: bool

    @property
    def steps(self) -> int:
        return int(self.mix.shape[0]) - 1

    @classmethod
    def static(cls, sdf: BodySDF, steps: int) -> BodyMotion:
        """A body that does not move: the static path, spelled as a schedule."""
        count = int(steps) + 1
        return cls(
            end=sdf,
            rotation=np.ascontiguousarray(np.repeat(sdf.rotation[None], count, axis=0)),
            translation=np.ascontiguousarray(np.repeat(sdf.translation[None], count, axis=0)),
            mix=np.zeros(count, dtype=np.float64),
            blend=False,
            moving=False,
        )

    @classmethod
    def between(cls, start: BodySDF, end: BodySDF, steps: int) -> BodyMotion:
        """The body moving from `start` to `end` over `steps` substeps, linearly.

        `end` must share `start`'s lattice (bake both with the same `bounds`);
        when it is the same grid object the motion is rigid and no blend is
        read. The last entries are SET from `end`, not computed, so the next
        call's entry 0 matches this call's entry -1 bit for bit.
        """
        count = int(steps) + 1
        if count < 2:
            raise ValueError("a motion needs at least one substep")
        same_lattice = (
            start.grid.shape == end.grid.shape
            and np.array_equal(start.origin, end.origin)
            and start.spacing == end.spacing
        )
        if not same_lattice:
            raise ValueError(
                "the body's two fields are not on one lattice "
                f"({start.grid.shape} at {np.round(start.origin, 4).tolist()} vs "
                f"{end.grid.shape} at {np.round(end.origin, 4).tolist()}): "
                "bake both with the same `bounds=` and voxel size"
            )
        u = np.linspace(0.0, 1.0, count)
        t0 = np.asarray(start.translation, dtype=np.float64)
        t1 = np.asarray(end.translation, dtype=np.float64)
        translation = t0[None, :] + (t1 - t0)[None, :] * u[:, None]
        translation[0] = t0
        translation[-1] = t1
        r0 = np.asarray(start.rotation, dtype=np.float64)
        r1 = np.asarray(end.rotation, dtype=np.float64)
        if np.allclose(r0, r1):
            rotation = np.repeat(r0[None], count, axis=0)
        else:
            from scipy.spatial.transform import Rotation, Slerp

            keys = Rotation.from_matrix(np.stack([r0, r1]))
            rotation = Slerp([0.0, 1.0], keys)(u).as_matrix()
            rotation[0] = r0
            rotation[-1] = r1
        blend = end.grid is not start.grid
        mix = u.copy() if blend else np.zeros(count, dtype=np.float64)
        moving = bool(
            blend
            or not np.array_equal(translation[0], translation[-1])
            or not np.array_equal(rotation[0], rotation[-1])
        )
        return cls(
            end=end,
            rotation=np.ascontiguousarray(rotation),
            translation=np.ascontiguousarray(translation),
            mix=np.ascontiguousarray(mix),
            blend=blend,
            moving=moving,
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


def _euler_matrix(degrees: tuple[float, float, float]) -> np.ndarray:
    """XYZ Euler angles -> a rotation matrix. Degrees, because a user types
    degrees and a silent radians/degrees mix-up is a whole afternoon."""
    rx, ry, rz = (np.radians(float(a)) for a in degrees)
    cx, sx = np.cos(rx), np.sin(rx)
    cy, sy = np.cos(ry), np.sin(ry)
    cz, sz = np.cos(rz), np.sin(rz)
    return (
        np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]])
        @ np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]])
        @ np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]])
    )


def solid_ball(
    radius_m: float = 0.15,
    centre: tuple[float, float, float] = (0.0, 0.0, 0.0),
    *,
    subdivisions: int = 4,
) -> trimesh.Trimesh:
    """A solid sphere - the honest test subject.

    A ball has no shoulders to blame, no pose to get wrong and no anatomy to
    argue about, so a drape over it is a statement about the SOLVER and the
    FABRIC rather than about the body. It is also the shape textile science
    already uses: the Cusick drape test (BS 5058 / ISO 9073-9) hangs a
    circular specimen over a circular pedestal and measures how far it falls,
    which `cusick_pedestal` sets up exactly.
    """
    if radius_m <= 0.0:
        raise ValueError(f"a ball needs a positive radius, got {radius_m}")
    ball = trimesh.creation.icosphere(subdivisions=subdivisions, radius=radius_m)
    ball.apply_translation(np.asarray(centre, dtype=np.float64))
    return ball


def cusick_pedestal(disc_diameter_m: float = 0.18, height_m: float = 0.30) -> trimesh.Trimesh:
    """The Cusick drapemeter's pedestal: a 0.18 m disc on a stand.

    BS 5058 supports a 0.30 m circular specimen on a 0.18 m disc and reports
    the DRAPE COEFFICIENT - the shadow area minus the disc, over the specimen
    area minus the disc. Higher means stiffer. It is the closest thing this
    field has to a ruler for "does the cloth behave", so seamkiln can be
    checked against it rather than against an opinion.
    """
    disc = trimesh.creation.cylinder(radius=disc_diameter_m / 2.0, height=0.01, sections=96)
    stem = trimesh.creation.cylinder(radius=disc_diameter_m / 6.0, height=height_m, sections=48)
    stem.apply_translation([0.0, 0.0, -height_m / 2.0])
    pedestal = trimesh.util.concatenate([disc, stem])
    pedestal.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1.0, 0.0, 0.0]))
    pedestal.apply_translation([0.0, height_m, 0.0])
    return pedestal


def place(
    mesh: trimesh.Trimesh,
    position: tuple[float, float, float] = (0.0, 0.0, 0.0),
    *,
    rotation_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
    scale: float = 1.0,
) -> trimesh.Trimesh:
    """Move, turn and resize the test subject. Returns a copy."""
    moved = mesh.copy()
    if scale != 1.0:
        moved.apply_scale(float(scale))
    rotation = np.eye(4)
    rotation[:3, :3] = _euler_matrix(rotation_deg)
    moved.apply_transform(rotation)
    moved.apply_translation(np.asarray(position, dtype=np.float64))
    return moved
