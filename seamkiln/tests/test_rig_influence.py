"""A mapped bone that owns no skin: refused, because the limb tears.

The gap this closes was found by asking `naming`'s ambiguity refusal to hold
its own reasoning consistently. That refusal says a control bone "owns no
vertices, so the limb never moves" and refuses when two bones fold to one
name - but nothing anywhere checked the same fact for a bone that mapped
cleanly. MEASURED 2026-09-04 on this repo's character: moving every
`LeftUpLeg` influence onto `Hips` (2,494 of them) loaded with no note at all.

Why a refusal and not a note. A bone can legitimately own FEW vertices, so
"few" is only ever worth a note - and there is one below. A bone that owns
NONE is different, and not in the way it first looks: its rotation still
reaches its children, so the limb does not freeze, it TEARS. Measured on the
stripped file at `hip_l = 40`, the shin swung 372 mm while the same patch of
thigh skin moved 31 mm, against 104 mm on the honest rig. The garment then
drapes over a shape no body has, and the fit report is confident.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from seamkiln.avatar import Pose
from seamkiln.rig.character import build_character
from seamkiln.rig.gltf_read import read_skinned_gltf
from seamkiln.rig.gltf_write import SkinnedPrimitive, write_glb
from seamkiln.rig.naming import map_joint_names
from seamkiln.rig.skin import (
    _LOPSIDED,
    _MIRROR_PAIRS,
    RiggedAvatar,
    RigSkinError,
    _evaluation_order,
    load_rigged_avatar,
)

H = 1.80
CELLS = 48  # the resolution every number in this file was measured at


@pytest.fixture(scope="module")
def character():
    return build_character(H, cells_tall=CELLS)


@pytest.fixture(scope="module")
def character_glb(tmp_path_factory: pytest.TempPathFactory, character) -> Path:
    path = tmp_path_factory.mktemp("influence") / "body.glb"
    write_glb(path, character.primitive(), character.skeleton)
    return path


def _rewritten(character, path: Path, keep: int) -> Path:
    """The character with all but `keep` of `LeftUpLeg`'s influences moved to `Hips`.

    `keep=0` is the file the defect was measured on: a thigh bone that is
    mapped, named correctly, and carries no skin at all.
    """
    joints = np.array(character.skin_joints, copy=True)
    thigh, hips = character.joint_index("LeftUpLeg"), character.joint_index("Hips")
    rows, columns = np.nonzero(joints == thigh)
    joints[rows[keep:], columns[keep:]] = hips
    write_glb(
        path,
        SkinnedPrimitive(
            positions=character.vertices,
            normals=character.normals,
            indices=character.faces,
            joints=joints,
            weights=character.skin_weights,
        ),
        character.skeleton,
    )
    return path


def _unchecked(path: Path) -> RiggedAvatar:
    """The avatar the loader would have returned before this guard existed.

    Built from the same parts `load_rigged_avatar` assembles, so the damage the
    refusal prevents can be MEASURED rather than asserted from a docstring.
    """
    body = read_skinned_gltf(path)
    joint_map = map_joint_names(body.joint_names)
    weights = body.weights / body.weights.sum(axis=1)[:, None]
    return RiggedAvatar(
        body=body,
        joint_map=joint_map,
        weights=weights,
        scale=1.0,
        offset=np.zeros(3),
        order=_evaluation_order(body.joints),
        slots=joint_map.index_map(body.joint_names),
    )


def _swing(rig: RiggedAvatar, which: np.ndarray, pose: Pose) -> float:
    """How far a patch of skin travels under a pose, in mm.

    The patch is passed in rather than looked up per rig: the whole point is
    to follow the SAME vertices through both files, and in the stripped one
    the thigh bone owns none to look up.
    """
    rest, posed = rig.rest_vertices, rig.posed_vertices(pose)
    return float(np.linalg.norm((posed[which] - rest[which]).mean(axis=0))) * 1000.0


def test_the_character_itself_weights_every_mapped_joint(character_glb: Path) -> None:
    """The guard must not fire on a correct rig - and the pairs' own spread is
    what sets the note's threshold below: 0.89 to 1.00 of each other, never
    exactly 1.00, because the character's Kuhn tessellation is handed."""
    rig = load_rigged_avatar(character_glb)
    mass = {
        joint: float(rig.weights[rig.body.joint_indices == index].sum())
        for joint, index in rig.slots.items()
    }
    assert min(mass.values()) > 0.0
    ratios = [min(mass[a], mass[b]) / max(mass[a], mass[b]) for a, b in _MIRROR_PAIRS]
    assert min(ratios) == pytest.approx(0.89, abs=0.03)
    assert min(ratios) > 3.0 * _LOPSIDED, "the note's threshold has to clear an honest body"
    assert not any("barely move" in note for note in rig.describe()["notes"])


def test_a_mapped_bone_with_no_skin_is_refused_and_the_refusal_is_earned(
    character, character_glb: Path, tmp_path: Path
) -> None:
    """Both halves: what the file does without the guard, and what it does with it."""
    stripped = _rewritten(character, tmp_path / "dead_thigh.glb", keep=0)

    # what was being accepted, measured: the shin swings, the thigh stays
    honest, damaged = _unchecked(character_glb), _unchecked(stripped)
    pose = Pose(hip_l=40.0)
    thigh, shin = honest.vertices_of("LeftUpLeg"), honest.vertices_of("LeftLeg")
    assert _swing(damaged, shin, pose) == pytest.approx(372.0, abs=15.0)
    assert _swing(honest, thigh, pose) == pytest.approx(104.0, abs=10.0)
    assert _swing(damaged, thigh, pose) == pytest.approx(31.0, abs=10.0)
    assert len(damaged.vertices_of("LeftUpLeg")) == 0, "no vertex is weighted to the thigh"

    with pytest.raises(RigSkinError) as caught:
        load_rigged_avatar(stripped)
    message = str(caught.value)
    assert "hip_l -> LeftUpLeg" in message
    assert "whose bone owns no skin" in message
    assert "no vertex in this file is weighted to it" in message
    assert "tears" in message
    assert "overrides= naming a bone that does own skin" in message


def test_an_override_cannot_lift_it_because_it_is_not_a_naming_question(
    character, tmp_path: Path
) -> None:
    """The line this lane draws: an override settles IDENTITY - which bone is
    which - and the laterality and proportion checks step aside for one. This
    check measures a physical fact about the file, and naming a weightless
    bone by hand does not put any skin on it. The route that DOES work is
    naming a different bone, so the message says that instead."""
    stripped = _rewritten(character, tmp_path / "dead_override.glb", keep=0)
    with pytest.raises(RigSkinError, match="whose bone owns no skin"):
        load_rigged_avatar(stripped, overrides={"hip_l": "LeftUpLeg"})
    # ... and the route the message names does work: a bone that owns skin
    rig = load_rigged_avatar(stripped, overrides={"hip_l": "Hips"})
    assert rig.slots["hip_l"] == rig.body.joint_index("Hips")


def test_a_lopsided_pair_is_a_note_and_not_a_refusal(character, tmp_path: Path) -> None:
    """A bone can legitimately own few vertices, so few is a note. The
    threshold is a quarter of the twin's share - well clear of the 0.89 the
    honest pairs measure above - and it is stated as a share so nothing has to
    invent an absolute vertex count."""
    thin = _rewritten(character, tmp_path / "thin_thigh.glb", keep=12)
    rig = load_rigged_avatar(thin)
    mass = {
        joint: float(rig.weights[rig.body.joint_indices == index].sum())
        for joint, index in rig.slots.items()
    }
    ratio = mass["hip_l"] / mass["hip_r"]
    assert 0.0 < ratio < _LOPSIDED
    notes = rig.describe()["notes"]
    assert any("hip_l (LeftUpLeg)" in note and "barely move" in note for note in notes), notes
    assert any(f"{ratio:.0%}" in note for note in notes), notes
