"""Linear blend skinning: the step that makes an imported body BEND.

`gltf_read` keeps a studio file's skeleton and `naming` says which bone is
which; this module is what finally moves them. Without it the chain stops one
link short of useful: `avatar.custom_avatar` flattens a scene to one mesh,
`session` falls back to `rigid_factory`, and the finest rigged character in
the world walks as a statue - the pelvis never rises, the arms never counter-
swing, and a garment gets none of what the gait work bought.

Two decisions here are worth more than the arithmetic.

**Rotations are applied about the WORLD X axis, never about a bone's own
axis.** A studio rig's bone frames are whatever its author left them as -
Mixamo's are twisted, Rigify's roll about the bone - so `local[:3, :3]` is not
a sagittal frame and rotating in it bends a knee sideways. seamkiln's nine
joints are all sagittal by definition (`avatar.JOINTS`: positive is flexion,
the limb swings toward +Z), so the rotation is built in world axes about the
joint's rest position and then expressed in the joint's rest frame, which is
`B^-1 R B` for `B` the rotation part of the joint's world rest matrix. It
composes down the hierarchy exactly as a local rotation does, so a knee
inherits its hip's swing the way `avatar.posed_mannequin` has it: the shank's
total flexion is the hip's minus the knee's.

**The signs come from the mannequin, not from taste.** `_swing` in `avatar`
hangs a limb DOWN and swings it toward +Z for positive flexion; a numpy
row-major rotation about +X sends `(0, -1, 0)` to `(0, -cos, -sin)`, so
flexion of theta degrees is a rotation about X of MINUS theta. Knee and elbow
carry the opposite sign because the mannequin subtracts them (`shoulder -
elbow`): they bend the limb back on itself. `trunk_lean` is the third case -
the spine points UP, so leaning forward is a PLUS rotation. Getting any of
these backwards produces a body that walks with its knees in front, which
reads as a solver bug three hours downstream.

Units and grounding are a similarity applied AFTER skinning (scale about the
origin, then a translation), so the file's own inverse bind matrices are never
touched and a centimetre export is caught the way `custom_avatar` catches it
rather than draping a garment on a 170 m body. No rotation is ever applied:
glTF 2.0 states +Y up and metres, and law 17 says a self-describing format is
left alone.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from ..avatar import JOINTS, PLAUSIBLE_HEIGHT_M, Pose, _infer_units
from .gltf_read import Joint, SkinnedBody, read_skinned_gltf
from .naming import JointMap, map_joint_names


class RigSkinError(ValueError):
    """A rigged body this module will not pose, with the fix in the message."""


# seamkiln joint -> the sign of its rotation about the world X axis. See the
# module docstring: flexion is -X, a joint the mannequin SUBTRACTS is +X, and
# the trunk is +X because the spine points the other way from a limb.
JOINT_SIGN: dict[str, float] = {
    "hip_l": -1.0,
    "hip_r": -1.0,
    "knee_l": 1.0,
    "knee_r": 1.0,
    "shoulder_l": -1.0,
    "shoulder_r": -1.0,
    "elbow_l": 1.0,
    "elbow_r": 1.0,
    "trunk_lean": 1.0,
}
if set(JOINT_SIGN) != set(JOINTS):  # pragma: no cover - a guard, not a branch
    raise RuntimeError(
        f"JOINT_SIGN covers {sorted(JOINT_SIGN)} but avatar.JOINTS is {sorted(JOINTS)}; "
        "a joint with no sign would silently never bend."
    )


def _rotation_x(degrees: float) -> np.ndarray:
    """Rotation about +X, row-major, for `M @ v` with `v` a column."""
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=np.float64)


def _evaluation_order(joints: tuple[Joint, ...]) -> tuple[int, ...]:
    """Parents before children. A file may list its joints in any order."""
    order: list[int] = []
    done: set[int] = set()
    pending = list(range(len(joints)))
    while pending:
        remaining = []
        for i in pending:
            parent = joints[i].parent
            if parent is None or parent in done:
                order.append(i)
                done.add(i)
            else:
                remaining.append(i)
        if len(remaining) == len(pending):  # pragma: no cover - the reader refuses cycles
            raise RigSkinError(
                f"joint(s) {[joints[i].name for i in remaining]} have parents that never "
                "resolve; the skeleton is not a tree."
            )
        pending = remaining
    return tuple(order)


@dataclass(frozen=True, slots=True)
class RiggedAvatar:
    """A studio body that still knows how to bend, at seamkiln's scale.

    `scale`/`offset` place the file's own space in seamkiln's world (metres,
    Y up, feet on the ground) and are applied AFTER the skin, so nothing in
    the rig is rewritten and the same avatar can be re-grounded per frame.
    """

    body: SkinnedBody
    joint_map: JointMap
    weights: np.ndarray  # (V, 4) float64, rows normalised to sum to 1
    scale: float
    offset: np.ndarray  # (3,) applied after scaling
    order: tuple[int, ...]
    slots: dict[str, int]  # seamkiln joint -> index into `body.joints`
    notes: tuple[str, ...] = ()

    # -- geometry ------------------------------------------------------------

    @property
    def rest_vertices(self) -> np.ndarray:
        return self.body.vertices * self.scale + self.offset

    @property
    def height_m(self) -> float:
        v = self.rest_vertices[:, 1]
        return float(v.max() - v.min())

    def mesh(self, pose: Pose | None = None) -> Any:
        """The body at a pose, as trimesh sees it. Rest pose when unposed."""
        import trimesh

        vertices = self.rest_vertices if pose is None else self.posed_vertices(pose)
        return trimesh.Trimesh(vertices=vertices, faces=self.body.faces, process=False)

    # -- the skin ------------------------------------------------------------

    def skinning_matrices(self, pose: Pose) -> np.ndarray:
        """(J, 4, 4): what each joint does to a vertex bound to it."""
        rotations = {
            self.slots[name]: _rotation_x(JOINT_SIGN[name] * float(getattr(pose, name)))
            for name in JOINTS
            if abs(float(getattr(pose, name))) > 0.0
        }
        joints = self.body.joints
        world: list[np.ndarray] = [np.eye(4)] * len(joints)
        for i in self.order:
            joint = joints[i]
            local = joint.local
            rotation = rotations.get(i)
            if rotation is not None:
                # B^-1 R B: the world-axis rotation about this joint's rest
                # position, said in the joint's own rest frame so it composes
                # down the hierarchy like any other local rotation.
                basis = joint.rest[:3, :3]
                delta = np.eye(4)
                delta[:3, :3] = np.linalg.solve(basis, rotation @ basis)
                local = local @ delta
            world[i] = local if joint.parent is None else world[joint.parent] @ local
        return np.stack(world) @ np.stack([j.inverse_bind for j in joints])

    def posed_vertices(self, pose: Pose) -> np.ndarray:
        """Linear blend skinning, then the scale and ground placement."""
        matrices = self.skinning_matrices(pose)
        vertices = self.body.vertices
        homogeneous = np.hstack([vertices, np.ones((len(vertices), 1))])
        out = np.zeros_like(vertices)
        for slot in range(self.body.joint_indices.shape[1]):
            picked = matrices[self.body.joint_indices[:, slot]]
            moved = np.einsum("nij,nj->ni", picked, homogeneous)[:, :3]
            out += self.weights[:, slot, None] * moved
        return out * self.scale + self.offset

    # -- what it is ----------------------------------------------------------

    def vertices_of(self, bone: str) -> np.ndarray:
        """Indices of the vertices this bone owns - its HEAVIEST influence.

        For measuring a hand or a foot without guessing at a bounding box,
        which is how "did the limb actually move?" gets answered honestly.
        Taken as the argmax over the four weights rather than as slot 0: glTF
        does not require an exporter to sort them, and a file that does not
        would quietly answer for the wrong bone.
        """
        index = self.body.joint_index(bone)
        rows = np.arange(len(self.weights))
        primary = self.body.joint_indices[rows, self.weights.argmax(axis=1)]
        return np.flatnonzero(primary == index)

    def describe(self) -> dict[str, Any]:
        """One compact record - never a dump; hard rule 1."""
        return {
            "source": self.body.source,
            "name": self.body.name,
            "vertices": len(self.body.vertices),
            "triangles": len(self.body.faces),
            "joints": len(self.body.joints),
            "height_m": round(self.height_m, 4),
            "scale": self.scale,
            "articulated": sorted(self.slots),
            "unused_bones": len(self.joint_map.unused),
            "notes": [*self.body.notes, *self.joint_map.notes, *self.notes],
        }


# The four left/right joint pairs, for the laterality check below.
_MIRROR_PAIRS: tuple[tuple[str, str], ...] = (
    ("hip_l", "hip_r"),
    ("knee_l", "knee_r"),
    ("shoulder_l", "shoulder_r"),
    ("elbow_l", "elbow_r"),
)


def _check_laterality(body: SkinnedBody, slots: dict[str, int]) -> None:
    """Refuse a rig whose LEFT joints are not all on the same side of it.

    MEASURED 2026-09-04. `naming` maps by name and by name only, on purpose -
    nothing is inferred from position - so a file whose `LeftUpLeg` and
    `RightUpLeg` labels are exchanged is accepted and walks mirrored. A FULL
    mirror cannot be caught from a rig alone: no bone carries the anatomical
    fact of which side is left, and the file is simply lying. A PARTIAL swap
    can, and it is the worse failure: swapping only the legs of this character
    put `hip_l` at x = +0.0958 while `shoulder_l` stayed at x = -0.2350, so
    seamkiln's "left" ran diagonally across the body and the limbs crossed
    during the swing.

    The test is each pair against the OTHER pairs, never against x = 0, so a
    character modelled off-centre is not falsely refused.
    """
    signs: dict[str, float] = {}
    for left, right in _MIRROR_PAIRS:
        if left not in slots or right not in slots:
            continue
        gap = float(body.joints[slots[left]].rest[0, 3] - body.joints[slots[right]].rest[0, 3])
        if abs(gap) < 1e-6:
            raise RigSkinError(
                f"{body.joints[slots[left]].name} and {body.joints[slots[right]].name} sit at "
                f"the same x ({gap:+.3g} m apart), so this rig has no left and right to pose. "
                "Fix: check the bind pose was exported, not a collapsed rest."
            )
        signs[f"{left}/{right}"] = 1.0 if gap > 0.0 else -1.0
    if len(set(signs.values())) > 1:
        min_count = min(list(signs.values()).count(v) for v in signs.values())
        detail = ", ".join(
            f"{pair} {'+x' if sign > 0 else '-x'}" for pair, sign in sorted(signs.items())
        )
        minority = sorted(k for k in signs if list(signs.values()).count(signs[k]) == min_count)
        raise RigSkinError(
            f"this rig's left/right bone NAMES disagree with where its bones are: {detail}. "
            "seamkiln's left limbs would end up on both sides of the body and cross during "
            f"the swing. Fix: swap the two bone names of {' or '.join(minority)} on export "
            "(whichever pair is the mislabelled one - this check knows they disagree, not "
            "which is right), or pass overrides= naming the bone that really is each joint. "
            "A rig with ALL its sides swapped is self-consistent and CANNOT be caught here: "
            "no bone carries the fact of which arm is the left one."
        )


def load_rigged_avatar(
    path: str | Path,
    *,
    node: str | None = None,
    overrides: dict[str, str] | None = None,
    units: str = "auto",
    ground_y: float = 0.0,
) -> RiggedAvatar:
    """Read a skinned glTF and get a body that can be POSED, or refuse.

    Refusals come from the two modules underneath: no skin at all, or bones
    that cannot be mapped onto seamkiln's nine joints. Both name the fix. The
    third refusal is here: an avatar whose height is not a body's, because a
    wrongly-scaled avatar produces a confident fit report about nothing.
    """
    body = read_skinned_gltf(path, node=node)
    joint_map = map_joint_names(body.joint_names, overrides=overrides)

    notes: list[str] = []
    span = float(body.vertices[:, 1].max() - body.vertices[:, 1].min())
    if units == "auto":
        scale, units = _infer_units(span)
        if scale != 1.0:
            notes.append(f"scaled by {scale:g}: {span:.3g} reads as {units}, not metres")
    else:
        scale = {"m": 1.0, "cm": 0.01, "mm": 0.001, "in": 0.0254}.get(units, 0.0)
        if scale == 0.0:
            raise RigSkinError(f"unknown units {units!r}. Known: m, cm, mm, in, auto.")
    height = span * scale
    low, high = PLAUSIBLE_HEIGHT_M
    if not low <= height <= high:
        raise RigSkinError(
            f"this rigged avatar is {height:.3g} m tall, which is not a body. Either the "
            f"units are wrong (pass units='cm'/'mm') or the file is not an avatar. "
            f"Refusing rather than draping a garment onto it."
        )

    scaled = body.vertices * scale
    offset = np.array(
        [
            -float(scaled[:, 0].mean()),
            ground_y - float(scaled[:, 1].min()),
            -float(scaled[:, 2].mean()),
        ]
    )

    # The file's weights are used as it stored them, normalised: a quantised
    # WEIGHTS_0 sums to 1 only to about 1e-3 (unsigned byte), and an
    # un-normalised blend shrinks a limb toward the origin by that fraction.
    totals = body.weights.sum(axis=1)
    drift = float(np.abs(totals - 1.0).max())
    if drift > 1e-9:
        notes.append(f"weights renormalised; they summed to 1 +- {drift:.3g} as stored")
    weights = body.weights / totals[:, None]

    slots = joint_map.index_map(body.joint_names)
    _check_laterality(body, slots)

    return RiggedAvatar(
        body=body,
        joint_map=joint_map,
        weights=weights,
        scale=float(scale),
        offset=offset,
        order=_evaluation_order(body.joints),
        slots=slots,
        notes=tuple(notes),
    )


__all__ = [
    "JOINT_SIGN",
    "RigSkinError",
    "RiggedAvatar",
    "load_rigged_avatar",
]
