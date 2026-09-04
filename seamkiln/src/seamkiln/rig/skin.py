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


# ---------------------------------------------------------------------------
# the guards on a MAPPED skeleton
# ---------------------------------------------------------------------------
#
# `naming` maps by name and by name only, on purpose: nothing is inferred from
# position or from string distance, because a fuzzy matcher pivots sleeves off
# the collarbone. The cost of that law is that a file whose labels lie is
# believed, and the three checks below are what make the lie visible. They all
# obey one rule about `overrides=`:
#
#   an override settles IDENTITY, never physics.
#
# A joint the caller names by hand is their own statement about which bone is
# which, so the checks that only guess at identity - laterality, proportion -
# step aside for it and say so. The checks that measure a physical fact about
# the file - two bones at the same place, a bone with no skin on it - do not,
# because no amount of naming makes a weightless bone deform anything.

# The four left/right joint pairs, for the laterality check below.
_MIRROR_PAIRS: tuple[tuple[str, str], ...] = (
    ("hip_l", "hip_r"),
    ("knee_l", "knee_r"),
    ("shoulder_l", "shoulder_r"),
    ("elbow_l", "elbow_r"),
)


def _check_laterality(body: SkinnedBody, slots: dict[str, int], asserted: frozenset[str]) -> None:
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

    A pair whose BOTH joints are in `asserted` (named by hand through
    `overrides=`) is skipped. MEASURED 2026-09-04, and the reason: a correctly
    labelled rig whose bind pose crosses the arms disagrees with itself here
    and was refused, and the refusal pointed at `overrides=` - which did not
    lift it, because the check ran on positions after the mapping. A refusal
    that names a route the caller cannot take is worse than a plain no. Both
    ends of the pair are needed because it takes two bones to state a side.
    The collapsed-pair refusal above is NOT skipped: no override moves a bone.
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
        if left in asserted and right in asserted:
            continue
        signs[f"{left}/{right}"] = 1.0 if gap > 0.0 else -1.0
    if len(set(signs.values())) > 1:
        min_count = min(list(signs.values()).count(v) for v in signs.values())
        detail = ", ".join(
            f"{pair} {'+x' if sign > 0 else '-x'}" for pair, sign in sorted(signs.items())
        )
        minority = sorted(k for k in signs if list(signs.values()).count(signs[k]) == min_count)
        pair = minority[0].split("/")
        raise RigSkinError(
            f"this rig's left/right bone NAMES disagree with where its bones are: {detail}. "
            "seamkiln's left limbs would end up on both sides of the body and cross during "
            f"the swing. Fix: swap the two bone names of {' or '.join(minority)} on export "
            "(whichever pair is the mislabelled one - this check knows they disagree, not "
            "which is right); or, if the names are right and it is the BIND POSE that "
            f"crosses, pass overrides={{{pair[0]!r}: ..., {pair[1]!r}: ...}} naming BOTH "
            "bones of the pair - naming both is your statement that these really are the "
            "left and right ones, and that pair is then not position-checked. "
            "A rig with ALL its sides swapped is self-consistent and CANNOT be caught here: "
            "no bone carries the fact of which arm is the left one."
        )


@dataclass(frozen=True, slots=True)
class _Segment:
    """One limb segment the proportion check can measure on a mapped skeleton."""

    label: str
    proximal: str  # the seamkiln joint at the near end
    distal: str | None  # the joint at the far end, or None for "its only child"
    reference: float  # length / body height on seamkiln's own reference figure
    climbed: str  # what a segment that is too LONG usually means


# seamkiln's OWN reference figure, and NOT an anthropometric claim: these are
# `seamkiln.figure`'s proportions, the ones that build a deliberately clothable
# body from a single number. `figure.Build` states each as a fraction of
# NOMINAL stature H - upper arm (shoulder -> elbow) 0.170 H on the male build
# and 0.169 on the female, forearm (elbow -> wrist) 0.155 / 0.151, thigh
# (hip -> knee) 0.245 / 0.254. The denominator here is different: it is the
# height the MESH actually spans, and the figure's own mesh stands 1.874 m for
# a nominal 1.80 because the skull ball rises past nominal stature. Measured
# against that, the same figure reads 0.163 / 0.149 / 0.235, and this repo's
# rigged character reads 0.165 / 0.150 / 0.237. `test_rig_proportions.py`
# re-derives all three from `figure.py` so the two cannot drift apart in
# silence.
_SEGMENTS: tuple[_Segment, ...] = tuple(
    _Segment(label, f"{near}_{tag}", f"{far}_{tag}" if far else None, reference, climbed)
    for label, near, far, reference, climbed in (
        (
            "upper arm",
            "shoulder",
            "elbow",
            0.163,
            "`LeftShoulder`/`RightShoulder` is the CLAVICLE in Mixamo, BVH and Unity naming, "
            "not the joint that swings the arm, so a file with those two names exchanged "
            "pivots every sleeve off the collarbone and still swings plausibly",
        ),
        (
            "forearm",
            "elbow",
            None,
            0.149,
            "the elbow may be mapped one link up the chain, onto the upper arm",
        ),
        (
            "thigh",
            "hip",
            "knee",
            0.235,
            "the hip may be mapped onto the pelvis root rather than onto the thigh",
        ),
    )
    for tag in ("l", "r")
)

# How far from the reference figure a rig may be before the MAPPING, rather
# than the character's build, is the likely explanation. Deliberately wide:
# the mis-mappings it exists to catch are not subtle. Taking the clavicle for
# the shoulder makes the upper arm 1.43x the reference (measured on this
# repo's own character: 0.233 against 0.163), and taking a twist or roll bone
# halfway down a limb roughly halves the segment. Stylisation inside the band
# is the character's business and nothing here has an opinion about it.
_PROPORTION_BAND: tuple[float, float] = (0.60, 1.30)


def _children(body: SkinnedBody, index: int) -> tuple[int, ...]:
    return tuple(i for i, joint in enumerate(body.joints) if joint.parent == index)


def _check_proportions(
    body: SkinnedBody, slots: dict[str, int], asserted: frozenset[str]
) -> tuple[str, ...]:
    """Refuse a mapping whose limb segments are not a body's. Notes what it skipped.

    WHY, measured 2026-09-04: exchange `LeftShoulder` and `LeftArm` in a file
    (and the right pair) and every earlier guard passes it in silence. The
    names still map, the sides still agree, the forearm still swings 177.5 mm
    against the honest 180.2 - and `shoulder_l` is now the COLLARBONE, its
    pivot 165.7 mm inboard and up, with every sleeve hung off it. That is the
    exact failure `naming`'s own docstring cites as the reason never to
    fuzzy-match, and it was landing anyway.

    Length is the one thing the swap cannot hide: shoulder -> elbow went from
    296.4 mm (0.165 of the body's height) to 419.6 mm (0.233), because the
    segment now spans the clavicle AND the upper arm. So the check is a
    proportion, banded against this repo's own figure - see `_SEGMENTS`.

    A segment whose joints are all in `asserted` is skipped: the caller has
    named those bones by hand, which is a statement about identity, and this
    check only ever guesses at identity.
    """
    height = float(body.vertices[:, 1].max() - body.vertices[:, 1].min())
    if height <= 0.0:  # pragma: no cover - the height refusal below owns this
        return ()
    low, high = _PROPORTION_BAND
    notes: list[str] = []
    bad: list[tuple[_Segment, str, str, float, float]] = []
    for segment in _SEGMENTS:
        if segment.proximal not in slots:
            continue
        near = slots[segment.proximal]
        if segment.distal is not None:
            if segment.distal not in slots:
                continue
            far: int | None = slots[segment.distal]
            named = segment.proximal in asserted and segment.distal in asserted
        else:
            # The wrist is not one of seamkiln's joints, so the far end is the
            # elbow bone's own child - and only when there is exactly one of
            # them, because with twist bones in the chain "which one is the
            # wrist" is a guess, and guessing is what this module does not do.
            kids = _children(body, near)
            far = kids[0] if len(kids) == 1 else None
            named = segment.proximal in asserted
            if far is None:
                notes.append(
                    f"{segment.label} {segment.proximal[-1]} not proportion-checked: "
                    f"{body.joints[near].name} has {len(kids)} child bones, so which one "
                    "ends the segment is a guess"
                )
                continue
        if named:
            continue
        length = float(np.linalg.norm(body.joints[near].rest[:3, 3] - body.joints[far].rest[:3, 3]))
        fraction = length / height
        if low * segment.reference <= fraction <= high * segment.reference:
            continue
        bad.append((segment, body.joints[near].name, body.joints[far].name, length, fraction))

    if bad:
        detail = "; ".join(
            f"{s.proximal}->{s.distal or 'wrist'} ({near_name} -> {far_name}) is "
            f"{length * 1000:.0f} mm = {fraction:.3f} of this body's height (the {s.label} on "
            f"seamkiln's own reference figure is {s.reference:.3f}, accepted "
            f"{low * s.reference:.3f} to {high * s.reference:.3f})"
            for s, near_name, far_name, length, fraction in bad
        )
        first = bad[0][0]
        why = (
            f"A segment that long is usually the mapping climbing a link: {first.climbed}."
            if bad[0][4] > first.reference
            else "A segment that short is usually a twist or roll bone taken for the joint."
        )
        # The override has to name EVERY joint the segment is measured between,
        # or it does not lift the check - and a fix that does not work is the
        # defect this whole section exists to close, so the message spells the
        # whole thing out rather than one end of it.
        ends = [first.proximal, *([first.distal] if first.distal else [])]
        route = ", ".join(f"{end!r}: '<the bone that is that joint>'" for end in ends)
        raise RigSkinError(
            f"this rig's proportions are not a body's once its bones are mapped: {detail}. "
            f"{why} Fix: check which bone really is each joint, or pass "
            f"overrides={{{route}}} - naming {'both ends' if len(ends) > 1 else 'the joint'} "
            "by hand is taken as your own statement, and a segment you have stated is not "
            "proportion-checked."
        )
    return tuple(notes)


# How lopsided a left/right pair's share of the skin may be before it is worth
# a note. The character's own pairs measure 0.89 to 1.00 of each other (never
# exactly 1.00: its Kuhn tessellation is handed), so a quarter is well clear of
# an honest body and only a stripped weight set reaches it - the file measured
# below, with a dozen influences left on the thigh, lands at 0.008.
_LOPSIDED = 0.25


def _check_influence(
    body: SkinnedBody, weights: np.ndarray, slots: dict[str, int]
) -> tuple[str, ...]:
    """Refuse a mapped joint that owns NO skin; note a pair that owns lopsided skin.

    WHY a refusal and not a note. A bone can legitimately own FEW vertices, so
    "few" is only ever worth a note - but a bone that owns none cannot deform
    the segment it is named for. Its rotation still reaches its children, so
    the failure is not a frozen limb, it is a TORN one: the skin at the joint's
    own segment stays behind with the parent while everything below the joint
    swings. MEASURED 2026-09-04 on this repo's character: moving every
    `LeftUpLeg` influence onto `Hips` (2,494 of them) loaded with no note at
    all, and `hip_l=40` then swung the shin 372 mm while the same patch of
    thigh skin moved 31 mm - against 104 mm on the honest rig. The leg pulls
    apart at the thigh and the fit report stays confident.

    `overrides=` does NOT lift this one. Which bone is which is the caller's
    to state; whether a bone has any skin on it is a fact about the file, and
    the fix - name a bone that does own skin - is a real one either way. It is
    the same reasoning `naming`'s ambiguity refusal already gives for control
    bones, which is where this gap was found.
    """
    owned: dict[str, int] = {}
    mass: dict[str, float] = {}
    for joint, index in slots.items():
        on_this = body.joint_indices == index
        owned[joint] = int((on_this & (weights > 0.0)).sum())
        mass[joint] = float(weights[on_this].sum())
    dead = sorted(joint for joint, count in owned.items() if count == 0)
    if dead:
        named = ", ".join(f"{joint} -> {body.joints[slots[joint]].name}" for joint in dead)
        raise RigSkinError(
            f"{len(dead)} mapped joint(s) whose bone owns no skin - no vertex in this file "
            f"is weighted to it: {named}. Rotating such a joint still swings everything "
            "BELOW it, so the limb does not freeze - it tears: the skin at that segment "
            "stays with the parent while the joint below it swings. Fix: re-export with the "
            "deform weights (a control or IK bone owns none by design), or pass overrides= "
            "naming a bone that does own skin. An override cannot lift this one - naming a "
            "weightless bone by hand does not put any skin on it."
        )
    notes: list[str] = []
    for left, right in _MIRROR_PAIRS:
        if left not in mass or right not in mass:
            continue
        lean, heavy = sorted((mass[left], mass[right]))
        if heavy > 0.0 and lean < _LOPSIDED * heavy:
            thin = left if mass[left] < mass[right] else right
            fat = right if thin == left else left
            notes.append(
                f"{thin} ({body.joints[slots[thin]].name}) is weighted to {lean / heavy:.0%} "
                f"as much skin as {fat} ({body.joints[slots[fat]].name}); that side of the "
                "body will barely move"
            )
    return tuple(notes)


def _plane_of_symmetry(body: SkinnedBody, slots: dict[str, int]) -> float:
    """Where the body's midline is, in the file's own units.

    A body's plane of symmetry is defined by its SKELETON, not by its
    tessellation. `load_rigged_avatar` used to centre on the vertex mean, and
    MEASURED 2026-09-04 that is a different number: this repo's character is
    built on an x-grid so its BOUNDS and its SKELETON are exactly symmetric to
    the last bit, while its Kuhn tetrahedral decomposition is HANDED and puts
    the vertex mean 5.0 mm off the midline. The body then arrived 5.0 mm off
    centre, which `dressing.frame_from_mesh` read as arms at -0.2404 / +0.2304
    - 10.0 mm of asymmetry on a body that has none - against a neck it fixes
    at x = 0. That is exactly the asymmetry `character.build_character`'s
    x-grid was written to remove, put back by the loader.

    So: the midpoint of the mapped left/right pairs, which is what carries the
    laterality the mapping already knows. The bounds midpoint is the fallback
    for a rig with no pair mapped - still a shape's own extremes rather than
    its triangle count's opinion. Never the vertex mean.
    """
    midpoints = [
        (float(body.joints[slots[left]].rest[0, 3]) + float(body.joints[slots[right]].rest[0, 3]))
        / 2.0
        for left, right in _MIRROR_PAIRS
        if left in slots and right in slots
    ]
    if midpoints:
        return float(np.mean(midpoints))
    x = body.vertices[:, 0]
    return float(x.min() + x.max()) / 2.0


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
    rest are here, and each one is a silent wrong answer made loud: an avatar
    whose height is not a body's, a rig whose left and right disagree, a
    mapping whose limb proportions are not a body's, and a joint mapped to a
    bone that owns no skin. A wrongly-scaled or wrongly-mapped avatar produces
    a confident fit report about nothing.
    """
    body = read_skinned_gltf(path, node=node)
    joint_map = map_joint_names(body.joint_names, overrides=overrides)
    slots = joint_map.index_map(body.joint_names)

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
            -_plane_of_symmetry(body, slots) * scale,
            ground_y - float(scaled[:, 1].min()),
            # z is NOT a plane of symmetry - a body is not its own mirror front
            # to back - so there is no skeleton answer to take here, and the
            # mean stays what centres the body fore-aft.
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

    asserted = frozenset(overrides or {})
    _check_laterality(body, slots, asserted)
    notes.extend(_check_proportions(body, slots, asserted))
    notes.extend(_check_influence(body, weights, slots))

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
