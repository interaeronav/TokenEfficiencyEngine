"""A rigged character, authored in code: one watertight skin, one skeleton.

WHY this exists. `avatar.custom_avatar` loads a studio body with
`trimesh.load(force="mesh")`, which flattens a scene to a single mesh and
throws the SKELETON away; `session` then falls back to a rigid body and the
walk moves it as a statue. Fixing that needs a test fixture that actually HAS
a skeleton - and the owner's asset folder holds only CLO `.avt` containers
with obfuscated payloads, while SMPL / SMPL-X / STAR are non-commercial
(research doc 67 §2) and cannot ship. So the character is AUTHORED HERE: it
is deterministic, licence-clean, and it runs in CI. It is a fixture and a
worked reference, not a replacement for a production body (Anny, Apache-2.0
over CC0 assets, remains that route).

WHY the joint names are Mixamo's and not seamkiln's. `Hips`, `Spine`,
`LeftUpLeg` ... A real studio file will never use seamkiln's `pelvis` /
`shoulder_l`, so if the fixture used seamkiln's own names the name-mapping
layer would be satisfied by an accidental match and would never be written.
The fixture forces the mapping to exist.

HOW the body is built, and why not the way `figure.py` builds one. `figure`
concatenates closed cones and balls: fast, and fine for a collider, but the
shells INTERPENETRATE - it is one mesh made of thirty solids sharing space.
A skinned body cannot be that, because a vertex inside another shell has
nowhere sane to go when the joint bends. So this is a single implicit
surface: exact round-cone distance fields, smooth-unioned (which is also what
keeps the armpit and crotch open rather than creased), polygonised by
MARCHING TETRAHEDRA. Tetrahedra, not cubes, because the tetrahedral case
table has no ambiguous cases: every output is manifold by construction, and
the 6-tetrahedron Freudenthal decomposition is conforming across cell
boundaries, so the surface is watertight with no cracks. It also fits in
sixty lines instead of a 256-entry table.

The proportions are `figure.py`'s, and they are a garment's numbers before
they are a comic's - Law 20, an unclothable body reads as a broken cloth
solver. Two of them are load-bearing:

* The upper arm is ~0.033 of stature in radius. `figure.py`'s first cut was
  194 mm across on a 1.8 m body where a real one is about 100, and no sleeve
  drafted to a matching armhole could go round it.
* The trunk is ELLIPTICAL, 1.10 wide by 0.78 deep (`figure.TORSO_SQUASH`),
  never a body of revolution. Measured on the walk, a round trunk let a
  zipped jacket yaw 15-20 degrees per stride and drift 32 mm sideways in two
  seconds, because nothing on the body resisted a garment turning about it.

Everything scales from one number, `stature_m`, and the finished mesh is
scaled so its height is EXACTLY that: a polygonised isosurface misses the
apex of the skull by a fraction of a cell, and a body silently 1 mm short is
the same class of error as one silently in centimetres.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import trimesh

from .gltf_write import Skeleton, SkinnedPrimitive, write_glb

# The glTF / Mixamo humanoid convention. Parents come before children.
JOINT_NAMES: tuple[str, ...] = (
    "Hips",
    "Spine",
    "Chest",
    "Neck",
    "Head",
    "LeftShoulder",
    "LeftArm",
    "LeftForeArm",
    "LeftHand",
    "RightShoulder",
    "RightArm",
    "RightForeArm",
    "RightHand",
    "LeftUpLeg",
    "LeftLeg",
    "LeftFoot",
    "RightUpLeg",
    "RightLeg",
    "RightFoot",
)
JOINT_PARENTS: tuple[int, ...] = (
    -1,  # Hips
    0,  # Spine
    1,  # Chest
    2,  # Neck
    3,  # Head
    2,  # LeftShoulder
    5,  # LeftArm
    6,  # LeftForeArm
    7,  # LeftHand
    2,  # RightShoulder
    9,  # RightArm
    10,  # RightForeArm
    11,  # RightHand
    0,  # LeftUpLeg
    13,  # LeftLeg
    14,  # LeftFoot
    0,  # RightUpLeg
    16,  # RightLeg
    17,  # RightFoot
)

# `figure.TORSO_SQUASH`, repeated rather than imported so this module has no
# dependency on the figure - but it is the SAME number, and it is the number
# that stops a jacket yawing on a walk.
TORSO_SQUASH: tuple[float, float] = (1.10, 0.78)

MAX_INFLUENCES = 4

# A round cone needs two ends; a BALL is one whose ends are a hair apart. A
# hair and not zero, because a zero-length axis has no direction to build a
# distance from.
_UP_HAIR = np.array([0.0, 1.0e-4, 0.0])


# ---------------------------------------------------------------------------
# signed distance fields
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _Limb:
    """A round cone (capsule with two radii), optionally squashed in place.

    `scale` is applied in the field's own frame, so the trunk parts become
    elliptical without moving off the body's axis. Dividing the query point
    by the scale and multiplying the distance by the smallest component keeps
    the ZERO SET exact and the field conservative, which is what smooth-union
    needs to blend sanely.
    """

    a: tuple[float, float, float]
    b: tuple[float, float, float]
    ra: float
    rb: float
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0)

    def distance(self, points: np.ndarray) -> np.ndarray:
        s = np.asarray(self.scale, dtype=np.float64)
        p = points / s
        a = np.asarray(self.a, dtype=np.float64) / s
        b = np.asarray(self.b, dtype=np.float64) / s
        return _round_cone(p, a, b, self.ra, self.rb) * float(s.min())


def _round_cone(p: np.ndarray, a: np.ndarray, b: np.ndarray, r1: float, r2: float) -> np.ndarray:
    """Exact distance to a cone capped by spheres of radius r1 at a, r2 at b.

    Inigo Quilez's closed form, vectorised. Exact matters: smooth-union of two
    fields that only BOUND the distance blends by the wrong amount and puts
    lumps where a body has none.
    """
    ba = b - a
    l2 = float(ba @ ba)
    rr = r1 - r2
    a2 = l2 - rr * rr
    il2 = 1.0 / l2
    pa = p - a
    y = pa @ ba
    z = y - l2
    cross = pa * l2 - ba[None, :] * y[:, None]
    x2 = np.einsum("ij,ij->i", cross, cross)
    y2 = y * y * l2
    z2 = z * z * l2
    k = np.sign(rr) * rr * rr * x2
    far = np.sqrt(np.maximum(x2 + z2, 0.0)) * il2 - r2
    near = np.sqrt(np.maximum(x2 + y2, 0.0)) * il2 - r1
    side = (np.sqrt(np.maximum(x2 * a2 * il2, 0.0)) + y * rr) * il2 - r1
    out = np.where(np.sign(y) * a2 * y2 < k, near, side)
    return np.where(np.sign(z) * a2 * z2 > k, far, out)


def _smooth_union(d1: np.ndarray, d2: np.ndarray, k: float) -> np.ndarray:
    """Polynomial smooth minimum. The blend is what keeps the armpit open."""
    h = np.clip(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0)
    return d2 * (1.0 - h) + d1 * h - k * h * (1.0 - h)


# ---------------------------------------------------------------------------
# marching tetrahedra
# ---------------------------------------------------------------------------


def _kuhn_tetrahedra() -> np.ndarray:
    """The six tetrahedra of a unit cell, as corner indices (x + 2y + 4z).

    The Freudenthal/Kuhn decomposition: the same six for every cell, which is
    why neighbouring cells agree on the triangulation of their shared face and
    the polygonised surface has no cracks. Each tet is reordered to positive
    orientation so the case table below produces outward-facing triangles.
    """
    axes = np.eye(3, dtype=np.int64)
    tets: list[list[int]] = []
    for first in range(3):
        for second in range(3):
            if second == first:
                continue
            o0 = np.zeros(3, dtype=np.int64)
            o1 = axes[first]
            o2 = axes[first] + axes[second]
            o3 = np.ones(3, dtype=np.int64)
            corners = [o0, o1, o2, o3]
            volume = np.linalg.det(np.stack([o1 - o0, o2 - o0, o3 - o0]).astype(float))
            if volume < 0:
                corners[1], corners[2] = corners[2], corners[1]
            tets.append([int(c[0] + 2 * c[1] + 4 * c[2]) for c in corners])
    return np.asarray(tets, dtype=np.int64)


# Local tetrahedron edges, indexed 0..5.
_TET_EDGES: tuple[tuple[int, int], ...] = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
# case (bitmask of corners inside) -> triangles as edge indices.
_TET_CASES: dict[int, tuple[tuple[int, int, int], ...]] = {
    0b0001: ((0, 1, 2),),
    0b0010: ((0, 4, 3),),
    0b0011: ((1, 2, 4), (1, 4, 3)),
    0b0100: ((1, 3, 5),),
    0b0101: ((0, 3, 5), (0, 5, 2)),
    0b0110: ((0, 4, 5), (0, 5, 1)),
    0b0111: ((2, 4, 5),),
    0b1000: ((2, 5, 4),),
    0b1001: ((0, 1, 5), (0, 5, 4)),
    0b1010: ((0, 5, 3), (0, 2, 5)),
    0b1011: ((1, 5, 3),),
    0b1100: ((1, 3, 4), (1, 4, 2)),
    0b1101: ((0, 3, 4),),
    0b1110: ((0, 2, 1),),
}


def _marching_tetrahedra(
    values: np.ndarray, axes: list[np.ndarray]
) -> tuple[np.ndarray, np.ndarray]:
    """Polygonise `values <= 0` on a regular grid. Returns (vertices, faces).

    Every output vertex lives on one grid edge and is keyed by that edge's two
    corners, so the mesh is welded as it is built - which is what makes it
    watertight rather than a soup that has to be merged afterwards.

    `axes` is the three coordinate arrays the values were sampled on, and a
    vertex reads its corner coordinates straight out of them rather than
    recomputing `origin + index * spacing`. That is not tidiness: the x axis
    is built symmetric about the body's own plane of symmetry, and only
    indexing it preserves the exact +-x mirror that arithmetic on an origin
    would round away.
    """
    shape = np.asarray(values.shape, dtype=np.int64)
    if np.any(shape < 2):
        raise ValueError(f"grid {values.shape} is too small to polygonise; need 2+ on every axis.")
    ny, nz = int(shape[1]), int(shape[2])
    flat = values.reshape(-1)
    cells = shape - 1
    base = (
        np.arange(cells[0])[:, None, None] * (ny * nz)
        + np.arange(cells[1])[None, :, None] * nz
        + np.arange(cells[2])[None, None, :]
    ).reshape(-1)
    corner_gid = np.empty((8, base.size), dtype=np.int64)
    for c in range(8):
        ox, oy, oz = c & 1, (c >> 1) & 1, (c >> 2) & 1
        corner_gid[c] = base + ox * ny * nz + oy * nz + oz

    ga_parts: list[np.ndarray] = []
    gb_parts: list[np.ndarray] = []
    for tet in _kuhn_tetrahedra():
        gid = corner_gid[tet]  # (4, cells)
        inside = (flat[gid] <= 0.0).astype(np.int64)
        case = inside[0] | (inside[1] << 1) | (inside[2] << 2) | (inside[3] << 3)
        for code, triangles in _TET_CASES.items():
            hit = np.flatnonzero(case == code)
            if not hit.size:
                continue
            for tri in triangles:
                for edge in tri:
                    ea, eb = _TET_EDGES[edge]
                    ga_parts.append(gid[ea][hit])
                    gb_parts.append(gid[eb][hit])
    if not ga_parts:
        raise ValueError("the field never crosses zero inside the grid: nothing to polygonise.")
    # triangles were emitted corner-by-corner per case; restack into (M, 3)
    ga = np.concatenate(ga_parts)
    gb = np.concatenate(gb_parts)
    lengths = np.array([len(part) for part in ga_parts], dtype=np.int64)
    order = _triangle_order(lengths)
    ga, gb = ga[order], gb[order]

    lo = np.minimum(ga, gb)
    hi = np.maximum(ga, gb)
    key = lo * flat.size + hi
    uniq, inverse = np.unique(key, return_inverse=True)
    faces = inverse.reshape(-1, 3).astype(np.int64)
    ulo, uhi = uniq // flat.size, uniq % flat.size
    fa, fb = flat[ulo], flat[uhi]
    t = np.where(np.abs(fa - fb) > 1e-30, fa / (fa - fb), 0.5)
    # Never put a vertex EXACTLY on a grid corner. When the field is within
    # rounding of zero at a corner, several of that corner's edges cross at the
    # same point and the triangles between them come out with zero area - a
    # face with no normal, which a collider turns into a NaN rather than a
    # contact. Nudging t off the ends by a thousandth of a cell moves the
    # surface by ~20 micrometres and leaves the topology untouched, because
    # each vertex is still keyed by its own edge.
    t = np.clip(t, 1.0e-3, 1.0 - 1.0e-3)
    pa = _grid_points(ulo, ny, nz, axes)
    pb = _grid_points(uhi, ny, nz, axes)
    vertices = pa + t[:, None] * (pb - pa)
    return vertices, faces


def _triangle_order(lengths: np.ndarray) -> np.ndarray:
    """Reorder corner-major emission back into triangle-major (3 per row).

    The polygoniser emits corner 0 of every triangle of one case, then corner
    1, then corner 2. This turns that back into (t0c0, t0c1, t0c2, t1c0, ...).
    """
    offsets = np.concatenate([[0], np.cumsum(lengths)])
    blocks: list[np.ndarray] = []
    for i in range(0, len(lengths), 3):
        n = int(lengths[i])
        cols = [np.arange(offsets[i + c], offsets[i + c] + n) for c in range(3)]
        blocks.append(np.stack(cols, axis=1).reshape(-1))
    return np.concatenate(blocks)


def _grid_points(gid: np.ndarray, ny: int, nz: int, axes: list[np.ndarray]) -> np.ndarray:
    """Flat grid ids back to coordinates, by INDEXING the axes."""
    k = gid % nz
    j = (gid // nz) % ny
    i = gid // (ny * nz)
    return np.stack([axes[0][i], axes[1][j], axes[2][k]], axis=1)


# ---------------------------------------------------------------------------
# the body
# ---------------------------------------------------------------------------


def _skeleton_points(abduction_deg: float) -> dict[str, np.ndarray]:
    """Joint positions as fractions of nominal stature. Y up, +Z forward."""
    hips = np.array([0.0, 0.480, 0.0])
    spine = np.array([0.0, 0.595, 0.0])
    chest = np.array([0.0, 0.727, 0.0])
    neck = np.array([0.0, 0.790, 0.0])
    head = np.array([0.0, 0.875, 0.0])
    out: dict[str, np.ndarray] = {
        "Hips": hips,
        "Spine": spine,
        "Chest": chest,
        "Neck": neck,
        "Head": head,
    }
    ab = math.radians(abduction_deg)
    fore_ab = math.radians(abduction_deg * 0.35)
    for side, tag in ((-1.0, "Left"), (1.0, "Right")):
        clavicle = np.array([side * 0.040, 0.775, 0.0])
        shoulder = np.array([side * 0.135, 0.778, 0.0])
        upper = np.array([side * math.sin(ab), -math.cos(ab), 0.0]) * 0.170
        elbow = shoulder + upper
        wrist = elbow + np.array([side * math.sin(fore_ab), -math.cos(fore_ab), 0.0]) * 0.155
        hip = np.array([side * 0.055, 0.480, 0.0])
        knee = hip + np.array([0.0, -0.245, 0.0])
        ankle = knee + np.array([0.0, -0.230, 0.0])
        out.update(
            {
                f"{tag}Shoulder": clavicle,
                f"{tag}Arm": shoulder,
                f"{tag}ForeArm": elbow,
                f"{tag}Hand": wrist,
                f"{tag}UpLeg": hip,
                f"{tag}Leg": knee,
                f"{tag}Foot": ankle,
            }
        )
    return out


def _bone_tails(points: dict[str, np.ndarray], head_top: float) -> dict[str, np.ndarray]:
    """Where each bone ENDS. A bone with several children needs one tail."""
    tails: dict[str, np.ndarray] = {
        "Hips": points["Spine"],
        "Spine": points["Chest"],
        "Chest": points["Neck"],
        "Neck": points["Head"],
        "Head": np.array([0.0, head_top, 0.0]),
    }
    for tag in ("Left", "Right"):
        wrist = points[f"{tag}Hand"]
        direction = wrist - points[f"{tag}ForeArm"]
        direction = direction / max(float(np.linalg.norm(direction)), 1e-9)
        tails[f"{tag}Shoulder"] = points[f"{tag}Arm"]
        tails[f"{tag}Arm"] = points[f"{tag}ForeArm"]
        tails[f"{tag}ForeArm"] = wrist
        tails[f"{tag}Hand"] = wrist + direction * 0.090
        tails[f"{tag}UpLeg"] = points[f"{tag}Leg"]
        tails[f"{tag}Leg"] = points[f"{tag}Foot"]
        tails[f"{tag}Foot"] = points[f"{tag}Foot"] + np.array([0.0, -0.012, 0.078])
    return tails


def _limbs(points: dict[str, np.ndarray]) -> list[_Limb]:
    """The solids the body is blended from, in nominal (stature = 1) units."""
    sx, sz = TORSO_SQUASH
    trunk = (sx, 1.0, sz)
    chest_r, waist_r, pelvis_r = 0.096, 0.068, 0.086
    limbs: list[_Limb] = [
        _Limb(tuple(points["Hips"]), tuple(points["Spine"]), pelvis_r, waist_r, trunk),
        _Limb(tuple(points["Spine"]), tuple(points["Chest"]), waist_r, chest_r, trunk),
        _Limb(tuple(points["Chest"]), tuple(points["Neck"]), chest_r, chest_r * 0.80, trunk),
        _Limb(tuple(points["Neck"]), tuple(points["Head"]), 0.046, 0.044),
    ]
    crown = np.array([0.0, points["Head"][1] + 0.72 * 0.072, 0.0])
    limbs.append(_Limb(tuple(crown), tuple(crown + _UP_HAIR), 0.072, 0.072, (0.94, 1.10, 1.02)))
    face = crown + np.array([0.0, -0.010, 0.030])
    limbs.append(_Limb(tuple(face), tuple(face + _UP_HAIR), 0.056, 0.056, (0.94, 1.06, 1.10)))
    for tag in ("Left", "Right"):
        shoulder = points[f"{tag}Arm"]
        elbow = points[f"{tag}ForeArm"]
        wrist = points[f"{tag}Hand"]
        deltoid = shoulder + (elbow - shoulder) * 0.06
        cap = tuple(deltoid + _UP_HAIR)
        limbs.append(_Limb(tuple(deltoid), cap, 0.040, 0.040, (1.06, 0.94, 1.0)))
        limbs.append(_Limb(tuple(shoulder), tuple(elbow), 0.033, 0.026))
        limbs.append(_Limb(tuple(elbow), tuple(wrist), 0.026, 0.021))
        hand_dir = wrist - elbow
        hand_dir = hand_dir / max(float(np.linalg.norm(hand_dir)), 1e-9)
        limbs.append(
            _Limb(tuple(wrist), tuple(wrist + hand_dir * 0.085), 0.023, 0.017, (1.0, 1.0, 0.62))
        )
        hip = points[f"{tag}UpLeg"]
        knee = points[f"{tag}Leg"]
        ankle = points[f"{tag}Foot"]
        limbs.append(_Limb(tuple(hip), tuple(knee), 0.058, 0.037))
        limbs.append(_Limb(tuple(knee), tuple(ankle), 0.037, 0.030))
        toe = ankle + np.array([0.0, -0.012, 0.078])
        heel = ankle + np.array([0.0, -0.008, -0.030])
        limbs.append(_Limb(tuple(ankle), tuple(toe), 0.030, 0.022, (0.90, 0.70, 1.0)))
        limbs.append(_Limb(tuple(heel), tuple(heel + _UP_HAIR), 0.028, 0.028, (0.90, 0.72, 1.0)))
    return limbs


def _field(limbs: list[_Limb], blend: float, points: np.ndarray) -> np.ndarray:
    d = limbs[0].distance(points)
    for limb in limbs[1:]:
        d = _smooth_union(d, limb.distance(points), blend)
    return d


def _segment_distance(points: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    ab = b - a
    denom = float(ab @ ab)
    if denom < 1e-18:
        return np.linalg.norm(points - a, axis=1)
    t = np.clip((points - a) @ ab / denom, 0.0, 1.0)
    return np.linalg.norm(points - (a[None, :] + t[:, None] * ab[None, :]), axis=1)


@dataclass(frozen=True, slots=True)
class Character:
    """A skinned humanoid: one manifold surface, one skeleton, one skin."""

    stature_m: float
    vertices: np.ndarray  # (N, 3) metres, Y up, +Z forward, feet on y = 0
    faces: np.ndarray  # (M, 3)
    normals: np.ndarray  # (N, 3) unit
    skeleton: Skeleton
    bone_tails: np.ndarray  # (J, 3), the far end of each bone
    skin_joints: np.ndarray  # (N, 4) uint8
    skin_weights: np.ndarray  # (N, 4) float32
    build: dict[str, Any]

    def mesh(self) -> trimesh.Trimesh:
        """The geometry as trimesh sees it - an INDEPENDENT check, not the source."""
        return trimesh.Trimesh(vertices=self.vertices, faces=self.faces, process=False)

    def primitive(self) -> SkinnedPrimitive:
        return SkinnedPrimitive(
            positions=self.vertices,
            normals=self.normals,
            indices=self.faces,
            joints=self.skin_joints,
            weights=self.skin_weights,
        )

    def joint_index(self, name: str) -> int:
        try:
            return self.skeleton.names.index(name)
        except ValueError:
            raise KeyError(
                f"no joint {name!r}; this skeleton uses the glTF/Mixamo names: "
                f"{', '.join(self.skeleton.names)}."
            ) from None

    def posed_vertices(
        self, rotations: dict[str, tuple[tuple[float, float, float], float]]
    ) -> np.ndarray:
        """Linear blend skinning: `{joint: (axis, degrees)}` -> deformed vertices.

        Here so the skin can be JUDGED - a weight set is only sane if the
        armpit and the crotch survive an extreme angle, and that is measured
        by posing the thing, not by reading the weights.
        """
        unknown = set(rotations) - set(self.skeleton.names)
        if unknown:
            raise KeyError(
                f"unknown joint(s) {sorted(unknown)}; this skeleton has "
                f"{', '.join(self.skeleton.names)}."
            )
        count = len(self.skeleton.names)
        local = np.repeat(np.eye(4)[None, :, :], count, axis=0)
        translations = self.skeleton.local_translations()
        for i, name in enumerate(self.skeleton.names):
            spec = rotations.get(name)
            if spec is not None:
                axis, degrees = spec
                local[i, :3, :3] = trimesh.transformations.rotation_matrix(
                    math.radians(degrees), list(axis)
                )[:3, :3]
            local[i, :3, 3] = translations[i]
        world = np.empty_like(local)
        for i, parent in enumerate(self.skeleton.parents):
            world[i] = local[i] if parent < 0 else world[parent] @ local[i]
        skinning = world @ self.skeleton.inverse_bind_matrices()
        homo = np.hstack([self.vertices, np.ones((len(self.vertices), 1))])
        out = np.zeros((len(self.vertices), 3))
        for slot in range(self.skin_joints.shape[1]):
            m = skinning[self.skin_joints[:, slot]]
            moved = np.einsum("nij,nj->ni", m, homo)[:, :3]
            out += self.skin_weights[:, slot, None] * moved
        return out

    def measurements(self) -> dict[str, float]:
        """The numbers that decide whether a garment can be drafted for it.

        The trunk is measured AT THE WAIST, and by which bone each vertex is
        bound to rather than by a box around the spine. Both choices were
        forced by a wrong answer: a box at chest height reported the trunk as
        569 mm wide and 2.04 wide-to-deep, because at that height the box
        catches the deltoid and the top of the arm, not the ribcage. The waist
        is the one section of the trunk that nothing else shadows - the arms
        are out and above it, the thighs are below it - so it is where the
        squash can be read honestly.
        """
        v = self.vertices
        names = self.skeleton.names
        shoulder = self.skeleton.positions[names.index("LeftArm")]
        elbow = self.skeleton.positions[names.index("LeftForeArm")]
        mid = (shoulder + elbow) * 0.5
        band = np.abs(v[:, 1] - mid[1]) < self.stature_m * 0.010
        arm = band & (v[:, 0] < (mid[0] + shoulder[0]) * 0.5)
        waist_y = float(self.skeleton.positions[names.index("Spine")][1])
        trunk_bones = [names.index(n) for n in ("Hips", "Spine", "Chest")]
        trunk = np.isin(self.skin_joints[:, 0], trunk_bones) & (
            np.abs(v[:, 1] - waist_y) < self.stature_m * 0.008
        )
        width = float(v[trunk, 0].max() - v[trunk, 0].min())
        depth = float(v[trunk, 2].max() - v[trunk, 2].min())
        return {
            "stature_m": float(self.stature_m),
            "height_m": float(v[:, 1].max() - v[:, 1].min()),
            "upper_arm_width_m": float(v[arm, 2].max() - v[arm, 2].min()),
            "trunk_width_m": width,
            "trunk_depth_m": depth,
            "trunk_width_depth_ratio": width / depth,
            "trunk_section_y_m": waist_y,
            "shoulder_span_m": float(
                np.linalg.norm(
                    self.skeleton.positions[names.index("LeftArm")]
                    - self.skeleton.positions[names.index("RightArm")]
                )
            ),
        }

    def manifest(self) -> dict[str, Any]:
        mesh = self.mesh()
        out: dict[str, Any] = {
            "vertices": len(self.vertices),
            "triangles": len(self.faces),
            "joints": len(self.skeleton.names),
            "joint_names": list(self.skeleton.names),
            "watertight": bool(mesh.is_watertight),
            "shells": int(mesh.body_count),
            "euler_number": int(mesh.euler_number),
            "volume_m3": float(mesh.volume),
            "units": "m",
            "up_axis": "+Y",
            "forward_axis": "+Z",
            "max_influences": int((self.skin_weights > 0.0).sum(axis=1).max()),
        }
        out.update(self.measurements())
        out.update(self.build)
        return out

    def to_glb(self, path: str | Path) -> dict[str, Any]:
        """Write the character as a skinned glTF 2.0 binary."""
        extras = {
            "seamkiln": {
                "generated_by": "seamkiln.rig.character.build_character",
                "stature_m": float(self.stature_m),
                "note": (
                    "authored in code so the fixture is deterministic and licence-clean; "
                    "glTF 2.0 is +Y up, +Z forward, metres by specification"
                ),
            }
        }
        manifest = write_glb(path, self.primitive(), self.skeleton, mesh_name="Body", extras=extras)
        manifest.update(self.measurements())
        return manifest


def build_character(
    stature_m: float = 1.80,
    *,
    cells_tall: int = 60,
    arm_abduction_deg: float = 40.0,
    blend: float = 0.021,
    falloff_m: float | None = None,
) -> Character:
    """Author a rigged humanoid from one number: its stature, in metres.

    `cells_tall` is the polygonisation resolution (grid cells over the body's
    height). It buys triangles, and triangles are only worth what they cost in
    CI. Measured on this machine at stature 1.80 m: 48 cells -> 11,756
    triangles in 0.09 s, 60 -> 18,404 in 0.14 s, 86 -> 38,280 in 0.29 s. The
    default is 60: 31.3 mm between grid lines, 1.89x the triangle count of
    `figure.figure()`'s body (9,760 at the same stature) and spent where cloth
    makes contact - shoulders, chest, hips - while still small enough to
    build, skin and write inside a CI test.
    """
    if stature_m <= 0.0:
        raise ValueError(f"stature_m must be positive, got {stature_m}.")
    if cells_tall < 24:
        raise ValueError(
            f"cells_tall={cells_tall} cannot resolve a hand or a neck; use 48 or more "
            "(60 is the default and gives ~18k triangles)."
        )
    points = _skeleton_points(arm_abduction_deg)
    head_top = points["Head"][1] + 0.72 * 0.072 + 1.10 * 0.072
    tails = _bone_tails(points, head_top)
    limbs = _limbs(points)

    lows, highs = [], []
    for limb in limbs:
        ends = np.array([limb.a, limb.b], dtype=np.float64)
        reach = max(limb.ra, limb.rb) * np.asarray(limb.scale) + blend
        lows.append(ends.min(axis=0) - reach)
        highs.append(ends.max(axis=0) + reach)
    low = np.min(np.stack(lows), axis=0)
    high = np.max(np.stack(highs), axis=0)
    spacing = float(high[1] - low[1]) / float(cells_tall)
    low -= 2.0 * spacing
    high += 2.0 * spacing
    counts = np.maximum(np.ceil((high - low) / spacing).astype(int) + 1, 2)
    # The x axis is built symmetric about x = 0 - a grid line ON the body's
    # plane of symmetry and the same number of cells either side - because the
    # grid decides where the surface lands. Left to fall where it liked, its
    # lines sat 0.79 mm off centre, the polygonised body inherited that, and
    # recentring the mesh on its own bounds then dragged the SKELETON off the
    # mirror by 1.6 mm: LeftArm and RightArm no longer at +-x. A left/right
    # asymmetry a body does not have is one every graded garment inherits.
    half_x = math.ceil(max(-float(low[0]), float(high[0])) / spacing)
    x_axis = np.arange(-half_x, half_x + 1) * spacing
    counts[0] = len(x_axis)
    axes = [x_axis] + [low[i] + np.arange(counts[i]) * spacing for i in (1, 2)]
    grid = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1).reshape(-1, 3)
    values = _field(limbs, blend, grid).reshape(tuple(int(c) for c in counts))
    # the field must be strictly outside on the boundary or the surface is cut
    values[0, :, :] = np.maximum(values[0, :, :], spacing)
    values[-1, :, :] = np.maximum(values[-1, :, :], spacing)
    values[:, 0, :] = np.maximum(values[:, 0, :], spacing)
    values[:, -1, :] = np.maximum(values[:, -1, :], spacing)
    values[:, :, 0] = np.maximum(values[:, :, 0], spacing)
    values[:, :, -1] = np.maximum(values[:, :, -1], spacing)

    vertices, faces = _marching_tetrahedra(values, axes)
    try:
        faces = _orient_outward(vertices, faces)
    except ValueError as broken:
        # MEASURED 2026-09-04, stature 1.80 m: cells_tall 25, 26, 27, 28 and 30
        # polygonise into more than one piece while 24, 29 and every value from
        # 31 up give a single shell. The grid is too coarse to bridge the wrist
        # and the neck at those spacings, and the surface pinches off there.
        # The shell check is right to refuse; on its own it blames the limbs,
        # which is a dead end for a caller whose only mistake was the number
        # they passed.
        raise ValueError(
            f"{broken} At cells_tall={cells_tall} the grid is probably too coarse to bridge "
            "the wrist and the neck: measured on this machine at stature 1.80 m, 25-28 and 30 "
            "break apart while 24, 29 and 31 upward do not. Fix: raise cells_tall (48 and 60 "
            "are the measured working sizes)."
        ) from broken

    # exact stature: a polygonised isosurface misses the apex of the skull by
    # a fraction of a cell, and a body silently short is a silent unit error.
    span = float(vertices[:, 1].max() - vertices[:, 1].min())
    scale = stature_m / span
    vertices = vertices * scale
    joint_positions = np.stack([points[name] for name in JOINT_NAMES]) * scale
    bone_tails = np.stack([tails[name] for name in JOINT_NAMES]) * scale

    # Only y moves: the body is already centred on x = 0 by construction (the
    # limbs are mirrored and the grid is), and z is where the figure's own
    # origin puts it. Solving x from the mesh's bounds would import a sub-cell
    # polygonisation artefact into the skeleton.
    ground = np.array([0.0, -float(vertices[:, 1].min()), 0.0])
    vertices = vertices + ground
    joint_positions = joint_positions + ground
    bone_tails = bone_tails + ground

    eps = spacing * scale * 0.30
    normals = _surface_normals(limbs, blend, (vertices - ground) / scale, eps / scale)

    skeleton = Skeleton(names=JOINT_NAMES, parents=JOINT_PARENTS, positions=joint_positions)
    radius_m = falloff_m if falloff_m is not None else stature_m * 0.16
    skin_joints, skin_weights = _skin(vertices, skeleton, bone_tails, radius_m)

    build = {
        "cells_tall": int(cells_tall),
        "grid_spacing_m": float(spacing * scale),
        "blend_m": float(blend * scale),
        "arm_abduction_deg": float(arm_abduction_deg),
        "skin_falloff_m": float(radius_m),
        "stature_scale": float(scale),
    }
    return Character(
        stature_m=float(stature_m),
        vertices=vertices,
        faces=faces,
        normals=normals,
        skeleton=skeleton,
        bone_tails=bone_tails,
        skin_joints=skin_joints,
        skin_weights=skin_weights,
        build=build,
    )


def _orient_outward(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """Wind the whole surface one way, then decide which way that is.

    The case table only has to TILE the surface; which way round each triangle
    faces is settled here. Judging each face on its own - against the field's
    gradient at its centroid, which is what this did first - is wrong six
    times in eighteen thousand: in the crease of an armpit the gradient at a
    triangle's centre leans across the surface rather than through it, and six
    stray faces are twelve inconsistent edges and `is_winding_consistent`
    False on an otherwise perfect mesh. A viewer lights those six black and a
    collider reads their normals inward.

    Winding is TOPOLOGICAL, so it is settled topologically: two faces sharing
    an edge agree exactly when they traverse that edge in opposite directions,
    and on a closed orientable surface that constraint propagates from one
    seed face to every other. Only the last question - in or out - is
    geometric, and the signed volume of a closed surface answers it in one
    number.
    """
    f = np.asarray(faces, dtype=np.int64)
    count = len(f)
    ends = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]], axis=0)
    face_of = np.tile(np.arange(count, dtype=np.int64), 3)
    lo, hi = ends.min(axis=1), ends.max(axis=1)
    forward = ends[:, 0] == lo  # does this face run the edge low -> high?
    key = lo * len(vertices) + hi
    order = np.lexsort((face_of, key))
    key, face_of, forward = key[order], face_of[order], forward[order]
    if len(key) % 2 or np.any(key[0::2] != key[1::2]):
        raise ValueError(
            "the polygonised surface is not closed: some edge is shared by other than two "
            "triangles. Raise `cells_tall`, or widen `blend` so no limb is thinner than a cell."
        )
    left, right = face_of[0::2], face_of[1::2]
    # both faces running the shared edge the same way means one of them is
    # wound against the other
    conflict = forward[0::2] == forward[1::2]

    owner = np.concatenate([left, right])
    other = np.concatenate([right, left])
    clash = np.concatenate([conflict, conflict])
    by_owner = np.argsort(owner, kind="stable")
    owner, other, clash = owner[by_owner], other[by_owner], clash[by_owner]
    start = np.searchsorted(owner, np.arange(count + 1))

    flip = np.zeros(count, dtype=bool)
    seen = np.zeros(count, dtype=bool)
    seen[0] = True
    stack = [0]
    while stack:
        here = stack.pop()
        for slot in range(int(start[here]), int(start[here + 1])):
            there = int(other[slot])
            if seen[there]:
                continue
            seen[there] = True
            flip[there] = flip[here] ^ bool(clash[slot])
            stack.append(there)
    if not bool(seen.all()):
        raise ValueError(
            f"the polygonised surface is in more than one piece: {int((~seen).sum())} of {count} "
            "triangles are unreachable from the first. The body must be a single shell - check "
            "that every limb overlaps its neighbour."
        )

    out = f.copy()
    out[flip] = out[flip][:, ::-1]
    tri = vertices[out]
    volume = float(np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum())
    return out[:, ::-1] if volume < 0.0 else out


def _field_gradient(limbs: list[_Limb], blend: float, points: np.ndarray, eps: float) -> np.ndarray:
    grad = np.empty_like(points)
    for axis in range(3):
        step = np.zeros(3)
        step[axis] = eps
        grad[:, axis] = _field(limbs, blend, points + step) - _field(limbs, blend, points - step)
    return grad


def _surface_normals(
    limbs: list[_Limb], blend: float, points: np.ndarray, eps: float
) -> np.ndarray:
    """Normals from the FIELD's gradient, not from face areas.

    The field is the truth here; averaging face normals would inherit the
    polygoniser's cell pattern, which shows up as facets across the shoulder.
    """
    grad = _field_gradient(limbs, blend, points, eps)
    length = np.linalg.norm(grad, axis=1)
    length[length < 1e-12] = 1.0
    return grad / length[:, None]


def _skin(
    vertices: np.ndarray, skeleton: Skeleton, tails: np.ndarray, falloff: float
) -> tuple[np.ndarray, np.ndarray]:
    """Bind every vertex to at most four nearby bones, weights summing to one.

    Two rules, and both are about not TRAPPING CLOTH. (1) Candidates are the
    nearest bone and everything within two hops of it in the hierarchy, so a
    chest vertex can never be dragged by a hand, and the transition across a
    joint is shared rather than a hard edge. (2) The falloff is `(1 - d/R)^2`,
    which reaches zero smoothly at R and is BOUNDED at the bone.

    The bound is the load-bearing half, and it was measured. The obvious
    kernel, `(1/d - 1/R)^2`, is singular where d -> 0: a vertex a hair nearer
    one bone than the next takes nearly all its weight from that bone, so the
    blend across a joint collapses into a hard edge exactly where the skin has
    to fold. Posed at the extremes in `test_rig_character.py` - arms adducted
    40 degrees, elbows folded 120, legs adducted 20 - the singular kernel left
    a triangle at **9.3 % of its bind area** in the inner elbow, against
    **23.9 %** for the bounded one at the same R. A face crushed to a tenth of
    itself is a crease, and a crease in an elbow or an armpit is where a
    sleeve gets pinched and never comes out.
    """
    count = len(skeleton.names)
    distances = np.empty((count, len(vertices)))
    for j in range(count):
        distances[j] = _segment_distance(vertices, skeleton.positions[j], tails[j])
    nearest = np.argmin(distances, axis=0)

    hops = _hop_matrix(skeleton.parents)
    allowed = hops[nearest] <= 2  # (N, J)
    strength = np.clip(1.0 - distances.T / falloff, 0.0, None) ** 2
    strength = np.where(allowed, strength, 0.0)
    # the nearest bone always keeps a voice, even inside a fat limb
    strength[np.arange(len(vertices)), nearest] = np.maximum(
        strength[np.arange(len(vertices)), nearest], 1e-9
    )

    order = np.argsort(-strength, axis=1, kind="stable")[:, :MAX_INFLUENCES]
    picked = np.take_along_axis(strength, order, axis=1)
    total = picked.sum(axis=1, keepdims=True)
    weights = picked / total
    joints = order.astype(np.uint8)
    # a zero weight must not point at an arbitrary joint: park it on the first
    joints = np.where(weights > 0.0, joints, joints[:, :1])
    return joints, weights.astype(np.float32)


def _hop_matrix(parents: tuple[int, ...]) -> np.ndarray:
    """Hierarchy distance between every pair of joints (edges traversed)."""
    n = len(parents)
    big = n + 1
    hops = np.full((n, n), big, dtype=np.int64)
    np.fill_diagonal(hops, 0)
    for i, p in enumerate(parents):
        if p >= 0:
            hops[i, p] = hops[p, i] = 1
    for k in range(n):
        hops = np.minimum(hops, hops[:, k][:, None] + hops[k][None, :])
    return hops


__all__ = [
    "JOINT_NAMES",
    "JOINT_PARENTS",
    "MAX_INFLUENCES",
    "TORSO_SQUASH",
    "Character",
    "build_character",
]
