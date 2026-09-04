"""A mapping that reads as a body, or a refusal: the clavicle case.

Written from a measurement made during the A65 P5b review. `naming` maps by
name and by name ONLY, which is the right law - a fuzzy matcher scores
`LeftShoulder` against `shoulder_l` at nearly 1.0 and pivots every sleeve off
the collarbone. The cost of the law is that a file whose labels are exchanged
is believed, and MEASURED on this repo's own character, exchanging
`LeftShoulder` with `LeftArm` (and the right pair) was accepted in silence:

  * `shoulder_l`'s pivot moved 165.7 mm inboard and up, onto the collarbone;
  * `shoulder_l -> elbow_l` went from 296.4 mm (0.165 of the body's height) to
    419.6 mm (0.233), because the segment now spans the clavicle AND the arm;
  * the forearm still swung 177.5 mm against the honest 180.2, so nothing in
    the motion gave it away.

Length is what the swap cannot hide, so `skin._check_proportions` bands the
mapped segments against seamkiln's OWN reference figure - `figure.py`, whose
every dimension is a fraction of stature. The first test below re-derives the
three reference numbers from `figure.py` so the constant and its source can
never drift apart in silence. They are this repo's figure and NOT an
anthropometric claim; the band is deliberately wide enough that only a gross
mis-mapping trips it.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

import numpy as np
import pytest

from seamkiln import figure as fig
from seamkiln.avatar import Pose
from seamkiln.rig.character import build_character
from seamkiln.rig.gltf_write import Skeleton, write_glb
from seamkiln.rig.skin import (
    _PROPORTION_BAND,
    _SEGMENTS,
    RigSkinError,
    load_rigged_avatar,
)

H = 1.80
CELLS = 32  # the skeleton is what is under test; 2,544 vertices carry it fine

_GLB_MAGIC = 0x46546C67
_CHUNK_JSON = 0x4E4F534A


@pytest.fixture(scope="module")
def character():
    return build_character(H, cells_tall=CELLS)


@pytest.fixture(scope="module")
def character_glb(tmp_path_factory: pytest.TempPathFactory, character) -> Path:
    path = tmp_path_factory.mktemp("proportions") / "body.glb"
    write_glb(path, character.primitive(), character.skeleton)
    return path


def _renamed(source: Path, target: Path, rename: dict[str, str]) -> Path:
    """Rewrite only the node NAMES of a GLB - every buffer byte is left alone."""
    raw = source.read_bytes()
    json_len, _ = struct.unpack_from("<II", raw, 12)
    doc = json.loads(raw[20 : 20 + json_len].decode("utf-8"))
    for node in doc["nodes"]:
        if node.get("name") in rename:
            node["name"] = rename[node["name"]]
    chunk = json.dumps(doc, separators=(",", ":"), sort_keys=True).encode("utf-8")
    chunk += b" " * ((4 - len(chunk) % 4) % 4)
    rest = raw[20 + json_len :]
    header = struct.pack("<III", _GLB_MAGIC, 2, 12 + 8 + len(chunk) + len(rest))
    target.write_bytes(header + struct.pack("<II", len(chunk), _CHUNK_JSON) + chunk + rest)
    return target


CLAVICLE_SWAP = {
    "LeftShoulder": "LeftArm",
    "LeftArm": "LeftShoulder",
    "RightShoulder": "RightArm",
    "RightArm": "RightShoulder",
}


def _fraction(rig, near: str, far: str) -> float:
    """A bone-to-bone distance as a fraction of the body's height, as the check sees it."""
    span = float(rig.body.vertices[:, 1].max() - rig.body.vertices[:, 1].min())
    a = rig.body.joints[rig.body.joint_index(near)].rest[:3, 3]
    b = rig.body.joints[rig.body.joint_index(far)].rest[:3, 3]
    return float(np.linalg.norm(a - b) / span)


# -- the band's provenance ------------------------------------------------------


def test_the_reference_fractions_are_figure_pys_own_and_stay_that_way() -> None:
    """The tie between the constant and its source, asserted rather than trusted.

    `figure.Build` states each dimension as a fraction of NOMINAL stature -
    upper arm 0.170 H, forearm 0.155, thigh 0.245 on the male build. The
    denominator in the rig lane is different: it is the height the MESH spans,
    and the figure's own mesh stands 1.874 m for a nominal 1.80 because the
    skull ball rises past nominal stature. Measured against that, the same
    figure reads 0.163 / 0.149 / 0.235, which is what `_SEGMENTS` carries.
    """
    joints = fig.joints(Pose(), height=H, build=fig.MALE)
    span = float(fig.figure(Pose(), height=H, build=fig.MALE).extents[1])
    assert span == pytest.approx(1.874, abs=0.005), "the figure's mesh is taller than nominal"

    measured = {
        "upper arm": float(np.linalg.norm(joints["elbow_l"] - joints["shoulder_l"]) / span),
        "forearm": float(np.linalg.norm(joints["hand_l"] - joints["elbow_l"]) / span),
        "thigh": float(np.linalg.norm(joints["knee_l"] - joints["hip_l"]) / span),
    }
    assert measured == pytest.approx(
        {"upper arm": 0.1633, "forearm": 0.1489, "thigh": 0.2354}, abs=5e-4
    )
    for segment in _SEGMENTS:
        assert segment.reference == pytest.approx(measured[segment.label], abs=2e-3), segment.label


def test_the_band_admits_both_of_the_figures_builds() -> None:
    """A band that refused the figure's own female build would be a bug in the
    band, not in a rig: the two builds differ by up to 3.5 % here."""
    low, high = _PROPORTION_BAND
    joints = fig.joints(Pose(), height=H, build=fig.FEMALE)
    span = float(fig.figure(Pose(), height=H, build=fig.FEMALE).extents[1])
    female = {
        "upper arm": float(np.linalg.norm(joints["elbow_l"] - joints["shoulder_l"]) / span),
        "forearm": float(np.linalg.norm(joints["hand_l"] - joints["elbow_l"]) / span),
        "thigh": float(np.linalg.norm(joints["knee_l"] - joints["hip_l"]) / span),
    }
    assert female == pytest.approx(
        {"upper arm": 0.1614, "forearm": 0.1442, "thigh": 0.2432}, abs=5e-4
    )
    for segment in _SEGMENTS:
        value = female[segment.label]
        assert low * segment.reference <= value <= high * segment.reference, segment.label


# -- the honest body ------------------------------------------------------------


def test_the_character_is_inside_the_band_with_room_to_spare(character_glb: Path) -> None:
    """The guard must not fire on a correct rig, and by how much matters: the
    swap below lands 10 % outside a band the honest body sits mid-way inside."""
    rig = load_rigged_avatar(character_glb)
    measured = {
        "upper arm": _fraction(rig, "LeftArm", "LeftForeArm"),
        "forearm": _fraction(rig, "LeftForeArm", "LeftHand"),
        "thigh": _fraction(rig, "LeftUpLeg", "LeftLeg"),
    }
    assert measured == pytest.approx(
        {"upper arm": 0.1650, "forearm": 0.1504, "thigh": 0.2378}, abs=1e-3
    )
    low, high = _PROPORTION_BAND
    for segment in _SEGMENTS:
        assert low * segment.reference < measured[segment.label] < high * segment.reference
    assert not any("proportion" in note for note in rig.describe()["notes"])


# -- the defect ----------------------------------------------------------------


def test_a_swapped_clavicle_is_refused_and_the_refusal_says_everything(
    character_glb: Path, tmp_path: Path
) -> None:
    """The measurement this whole file exists for. Before the check, this file
    loaded with no note at all and hung every sleeve off the collarbone."""
    swapped = _renamed(character_glb, tmp_path / "clavicle.glb", CLAVICLE_SWAP)

    # the honest number first, so the refusal below can be read against it. The
    # swap moves no bone, so the segment the mapping now measures is exactly
    # the honest rig's collarbone-to-elbow span.
    honest = load_rigged_avatar(character_glb)
    assert _fraction(honest, "LeftArm", "LeftForeArm") == pytest.approx(0.165, abs=1e-3)
    lied = _fraction(honest, "LeftShoulder", "LeftForeArm")
    assert lied == pytest.approx(0.234, abs=2e-3)

    with pytest.raises(RigSkinError) as caught:
        load_rigged_avatar(swapped)
    message = str(caught.value)
    assert "shoulder_l->elbow_l" in message and "shoulder_r->elbow_r" in message
    assert "LeftArm -> LeftForeArm" in message  # the bones it actually used
    assert f"= {lied:.3f} of this body's height" in message  # what it measured
    assert "0.163" in message and "0.098 to 0.212" in message  # the reference and the band
    assert "CLAVICLE" in message
    # the route it names has to be the WHOLE route: naming one end of a
    # two-joint segment does not lift the check, and the test below takes it
    assert "overrides={'shoulder_l': '<the bone that is that joint>', 'elbow_l':" in message
    assert "naming both ends" in message


def test_the_override_the_refusal_names_actually_lifts_it(
    character_glb: Path, tmp_path: Path
) -> None:
    """A refusal that names a route the caller cannot take is worse than a
    plain no. This is that route, taken: naming BOTH ends of a segment by hand
    is a statement about identity, and the proportion check only ever guesses
    at identity, so it steps aside - and the caller owns what follows.
    """
    swapped = _renamed(character_glb, tmp_path / "clavicle_ok.glb", CLAVICLE_SWAP)
    rig = load_rigged_avatar(
        swapped,
        overrides={
            "shoulder_l": "LeftArm",
            "elbow_l": "LeftForeArm",
            "shoulder_r": "RightArm",
            "elbow_r": "RightForeArm",
        },
    )
    assert rig.slots["shoulder_l"] == rig.body.joint_index("LeftArm")
    assert any("mapped by override" in note for note in rig.describe()["notes"])
    # naming only ONE end is not a statement about the segment, and does not lift it
    with pytest.raises(RigSkinError, match="proportions are not a body's"):
        load_rigged_avatar(swapped, overrides={"shoulder_l": "LeftArm", "shoulder_r": "RightArm"})


def test_a_segment_that_is_too_short_is_caught_from_the_other_side(
    character, character_glb: Path, tmp_path: Path
) -> None:
    """The band's lower half, which is the twist-bone failure: map the joint
    onto a roll bone halfway down the limb and the segment roughly halves.
    Built by moving the two upper-arm joints to the middle of their own bone,
    so only the upper arm changes and the forearm stays honest."""
    skeleton = character.skeleton
    positions = np.array(skeleton.positions, copy=True)
    for side in ("Left", "Right"):
        arm, fore = skeleton.names.index(f"{side}Arm"), skeleton.names.index(f"{side}ForeArm")
        positions[arm] = (positions[arm] + positions[fore]) / 2.0
    path = tmp_path / "halved.glb"
    write_glb(
        path,
        character.primitive(),
        Skeleton(names=skeleton.names, parents=skeleton.parents, positions=positions),
    )
    with pytest.raises(RigSkinError) as caught:
        load_rigged_avatar(path)
    message = str(caught.value)
    halved = _fraction(load_rigged_avatar(character_glb), "LeftArm", "LeftForeArm") / 2.0
    assert halved == pytest.approx(0.0825, abs=1e-3)
    assert f"= {halved:.3f} of this body's height" in message
    assert "twist or roll bone" in message


def test_an_ambiguous_wrist_is_a_note_and_not_a_refusal(character, tmp_path: Path) -> None:
    """The forearm's far end is not one of seamkiln's joints, so it is taken
    from the elbow bone's own child - and only when there is exactly ONE.
    A production rig with a twist bone in the forearm has two, and guessing
    between them is precisely what this module does not do, so the check says
    it skipped rather than inventing an answer."""
    skeleton = character.skeleton
    twist = skeleton.names.index("LeftForeArm")
    names = (*skeleton.names, "LeftForeArmTwist")
    parents = (*skeleton.parents, twist)
    positions = np.vstack([skeleton.positions, skeleton.positions[twist] + [0.0, -0.05, 0.0]])
    path = tmp_path / "twist.glb"
    write_glb(
        path, character.primitive(), Skeleton(names=names, parents=parents, positions=positions)
    )

    rig = load_rigged_avatar(path)
    notes = rig.describe()["notes"]
    assert any("forearm l not proportion-checked" in note for note in notes), notes
    assert any("2 child bones" in note for note in notes), notes
    # the right forearm still has exactly one child, so it is still checked
    assert not any("forearm r" in note for note in notes), notes
