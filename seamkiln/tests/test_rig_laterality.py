"""A rig whose left/right bone NAMES disagree with where its bones are.

Written during the A65 P5b review, from a measurement rather than a worry.
`naming` maps bones by name and by name ONLY - nothing is inferred from
position, which is the right law, because a fuzzy or positional matcher
pivots sleeves off the collarbone. The cost of that law is that a file which
labels its limbs wrongly is believed.

Two cases, and they are not the same:

* ALL sides exchanged. Self-consistent; no bone anywhere carries the
  anatomical fact of which arm is the left one, so it CANNOT be caught from
  the rig, and this file pins that it is accepted rather than pretending
  otherwise. The garment cost is nil for a symmetric block and real for an
  asymmetric one.
* SOME sides exchanged. Measured on this repo's own character with only the
  legs swapped: `hip_l` landed at x = +0.0958 m while `shoulder_l` stayed at
  x = -0.2350 m, so seamkiln's "left" ran diagonally across the body and the
  limbs crossed on the swing. That is detectable without any anatomical
  knowledge - the four pairs simply have to agree on which way round they
  are - and `skin._check_laterality` now refuses it.

And a third case, added 2026-09-04 after the guard above was measured against
a file it should not have refused. A rig whose LABELS are right and whose BIND
POSE crosses the arms disagrees with itself here in exactly the same way, and
was refused with a message pointing at `overrides=` - which did not lift it,
because the check runs on positions after the mapping. A refusal that names a
route the caller cannot take is worse than a plain no, so naming BOTH bones of
a pair by hand is now taken as the statement it is, and that pair is not
position-checked. It takes both because it takes two bones to state a side.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

import numpy as np
import pytest

from seamkiln.rig.character import build_character
from seamkiln.rig.gltf_write import Skeleton, write_glb
from seamkiln.rig.skin import RigSkinError, load_rigged_avatar

_GLB_MAGIC = 0x46546C67
_CHUNK_JSON = 0x4E4F534A


def _renamed(source: Path, target: Path, rename: dict[str, str]) -> Path:
    """Rewrite only the node NAMES of a GLB, leaving every buffer byte alone.

    The point of the fixture is a file whose geometry and skeleton are correct
    and whose labels lie, so nothing but the JSON chunk may change.
    """
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


def _mirror(names: tuple[str, ...]) -> dict[str, str]:
    def flip(n: str) -> str:
        return n.replace("Left", "Right") if "Left" in n else n.replace("Right", "Left")

    return {n: flip(n) for n in names}


@pytest.fixture(scope="module")
def character():
    return build_character(1.80, cells_tall=32)


@pytest.fixture(scope="module")
def character_glb(tmp_path_factory: pytest.TempPathFactory, character) -> Path:
    path = tmp_path_factory.mktemp("laterality") / "body.glb"
    write_glb(path, character.primitive(), character.skeleton)
    return path


@pytest.fixture(scope="module")
def crossed_glb(tmp_path_factory: pytest.TempPathFactory, character) -> Path:
    """A rig whose labels are RIGHT and whose bind pose puts each arm on the
    other side of the body - the folded-arms bind a studio really does export.

    Only the arm chain's bind positions are mirrored, so the file stays
    internally consistent (`write_glb` derives the inverse bind matrices from
    the skeleton it is given). The mesh does not follow the bones, which is of
    no consequence to the guard under test: it reads bind positions and
    nothing else.
    """
    path = tmp_path_factory.mktemp("laterality") / "crossed.glb"
    skeleton = character.skeleton
    positions = np.array(skeleton.positions, copy=True)
    for side in ("Left", "Right"):
        for bone in ("Shoulder", "Arm", "ForeArm", "Hand"):
            positions[skeleton.names.index(f"{side}{bone}"), 0] *= -1.0
    write_glb(
        path,
        character.primitive(),
        Skeleton(names=skeleton.names, parents=skeleton.parents, positions=positions),
    )
    return path


def test_the_character_itself_has_consistent_sides(character_glb: Path) -> None:
    """The guard must not fire on a correct rig - measured left at -x here."""
    rig = load_rigged_avatar(character_glb)
    left = rig.body.joints[rig.slots["hip_l"]].rest[0, 3]
    right = rig.body.joints[rig.slots["hip_r"]].rest[0, 3]
    shoulder_l = rig.body.joints[rig.slots["shoulder_l"]].rest[0, 3]
    assert left < right
    assert shoulder_l < 0.0 and left < 0.0
    assert left + right == pytest.approx(0.0, abs=1e-9)


def test_swapping_only_the_legs_refuses_and_names_the_disagreement(
    character_glb: Path, tmp_path: Path
) -> None:
    """The detectable half: four pairs that do not agree which way round they are."""
    swapped = _renamed(
        character_glb,
        tmp_path / "legs_swapped.glb",
        _mirror(("LeftUpLeg", "RightUpLeg", "LeftLeg", "RightLeg")),
    )
    with pytest.raises(RigSkinError) as excinfo:
        load_rigged_avatar(swapped)
    message = str(excinfo.value)
    assert "left/right bone NAMES disagree" in message
    assert "hip_l/hip_r +x" in message and "shoulder_l/shoulder_r -x" in message
    assert "overrides=" in message


def test_swapping_every_side_is_accepted_and_that_is_stated(
    character_glb: Path, tmp_path: Path
) -> None:
    """The undetectable half, pinned so nobody claims a guard that is not there.

    A fully mirrored rig is self-consistent, so it is ACCEPTED. What that costs
    is exact and is asserted here: seamkiln's `hip_l` now drives the bone on the
    body's +x side, i.e. its physical RIGHT leg. Nothing downstream can tell,
    because a symmetric body walking a mirrored gait is the same silhouette -
    measured below as each named foot landing where the honest rig's
    same-named foot lands, 600 mm from the other one.

    MEASURED 2026-09-04, correcting an earlier version of this test that
    compared LeftFoot against RightFoot and failed: the feet do NOT exchange
    their z. The label swap exchanges which physical leg does the work, and on
    a body that is symmetric about x = 0 the named bone therefore arrives at
    the same place. The 4 mm bound is the character's own tessellation, not
    the skinning: the Kuhn decomposition is handed, so at `cells_tall=32` a
    vertex and its mirror sit up to 42.6 mm apart (6.8 mm mean) and a foot's
    centroid inherits 3.0 mm of that.
    """
    from seamkiln import avatar as av

    honest = load_rigged_avatar(character_glb)
    mirrored = _mirror(honest.body.joint_names)
    lying = load_rigged_avatar(_renamed(character_glb, tmp_path / "all.glb", mirrored))

    # the lie itself, stated as a number: left is now on the body's right
    assert honest.body.joints[honest.slots["hip_l"]].rest[0, 3] < 0.0
    assert lying.body.joints[lying.slots["hip_l"]].rest[0, 3] > 0.0

    track = av.gait("walk", cycles=1.0, samples_per_cycle=8)
    stride = max(track.poses, key=lambda p: abs(p.hip_l - p.hip_r))

    def foot_z(rig: object, bone: str) -> float:
        posed = rig.posed_vertices(stride)  # type: ignore[attr-defined]
        return float(posed[rig.vertices_of(bone)].mean(axis=0)[2])  # type: ignore[attr-defined]

    for bone in ("LeftFoot", "RightFoot"):
        assert foot_z(lying, bone) == pytest.approx(foot_z(honest, bone), abs=4e-3), bone
    assert abs(foot_z(honest, "LeftFoot") - foot_z(honest, "RightFoot")) > 0.3, (
        "the stride is wide enough that landing on the wrong foot would show"
    )


def test_a_rig_whose_pairs_sit_at_the_same_x_refuses(character_glb: Path, tmp_path: Path) -> None:
    """A collapsed rest pose has no sides at all, and says so rather than
    dividing by a zero-width body later."""
    raw = character_glb.read_bytes()
    json_len, _ = struct.unpack_from("<II", raw, 12)
    doc = json.loads(raw[20 : 20 + json_len].decode("utf-8"))
    for node in doc["nodes"]:
        if node.get("name") in {"LeftUpLeg", "RightUpLeg"} and "translation" in node:
            node["translation"] = [0.0, *node["translation"][1:]]
    chunk = json.dumps(doc, separators=(",", ":"), sort_keys=True).encode("utf-8")
    chunk += b" " * ((4 - len(chunk) % 4) % 4)
    rest = raw[20 + json_len :]
    target = tmp_path / "collapsed.glb"
    target.write_bytes(
        struct.pack("<III", _GLB_MAGIC, 2, 12 + 8 + len(chunk) + len(rest))
        + struct.pack("<II", len(chunk), _CHUNK_JSON)
        + chunk
        + rest
    )
    with pytest.raises(RigSkinError, match="no left and right to pose"):
        load_rigged_avatar(target)


def test_the_guard_is_translation_invariant(character_glb: Path, tmp_path: Path) -> None:
    """A body modelled off-centre must not be refused: the check compares each
    pair with the OTHER pairs, never with x = 0."""
    raw = character_glb.read_bytes()
    json_len, _ = struct.unpack_from("<II", raw, 12)
    doc = json.loads(raw[20 : 20 + json_len].decode("utf-8"))
    root = doc["skins"][0]["skeleton"]
    was = doc["nodes"][root].get("translation", [0.0, 0.0, 0.0])
    doc["nodes"][root]["translation"] = [5.0, *was[1:]]
    chunk = json.dumps(doc, separators=(",", ":"), sort_keys=True).encode("utf-8")
    chunk += b" " * ((4 - len(chunk) % 4) % 4)
    rest = raw[20 + json_len :]
    target = tmp_path / "offset.glb"
    target.write_bytes(
        struct.pack("<III", _GLB_MAGIC, 2, 12 + 8 + len(chunk) + len(rest))
        + struct.pack("<II", len(chunk), _CHUNK_JSON)
        + chunk
        + rest
    )
    rig = load_rigged_avatar(target)
    assert np.all(rig.body.joints[rig.slots["hip_l"]].rest[0, 3] > 4.0)


ARMS = {
    "shoulder_l": "LeftArm",
    "shoulder_r": "RightArm",
    "elbow_l": "LeftForeArm",
    "elbow_r": "RightForeArm",
}


def test_a_crossed_bind_pose_is_refused_and_the_route_it_names_works(crossed_glb: Path) -> None:
    """The third case. The refusal is right to fire - four pairs that disagree
    look the same whether the names lie or the pose crosses, and this check
    cannot tell which - but the way out it offers has to be real."""
    with pytest.raises(RigSkinError) as caught:
        load_rigged_avatar(crossed_glb)
    message = str(caught.value)
    assert "left/right bone NAMES disagree" in message
    assert "shoulder_l/shoulder_r +x" in message and "hip_l/hip_r -x" in message
    assert "BIND POSE" in message and "naming BOTH" in message

    rig = load_rigged_avatar(crossed_glb, overrides=ARMS)
    assert rig.slots["shoulder_l"] == rig.body.joint_index("LeftArm")
    assert float(rig.body.joints[rig.slots["shoulder_l"]].rest[0, 3]) > 0.0
    assert float(rig.body.joints[rig.slots["hip_l"]].rest[0, 3]) < 0.0


def test_naming_one_end_of_a_pair_is_not_a_statement_about_the_pair(crossed_glb: Path) -> None:
    """It takes two bones to state a side, so one override leaves the pair
    position-checked - and a pair still in the check still disagrees."""
    for partial in ({"shoulder_l": "LeftArm"}, {"shoulder_l": "LeftArm", "elbow_l": "LeftForeArm"}):
        with pytest.raises(RigSkinError, match="left/right bone NAMES disagree"):
            load_rigged_avatar(crossed_glb, overrides=partial)


def test_consenting_to_a_pair_costs_the_evidence_that_pair_carried(
    character_glb: Path, tmp_path: Path
) -> None:
    """The price of the consent rule, pinned rather than hidden.

    This check works by DISAGREEMENT between pairs - it never asks where x = 0
    is - so vouching for the arms takes the arms out of the comparison. A file
    whose LEGS are the mislabelled ones then has nothing left to disagree with
    and is accepted: refused with no overrides, accepted with the arms named.
    That is the same blind spot the fully mirrored rig has above, reached on
    purpose this time, and it is the honest outcome - the caller has stated
    that the arms are right, and half a body cannot contradict itself.
    """
    swapped = _renamed(
        character_glb,
        tmp_path / "legs_swapped_with_arms_named.glb",
        _mirror(("LeftUpLeg", "RightUpLeg", "LeftLeg", "RightLeg")),
    )
    with pytest.raises(RigSkinError, match="left/right bone NAMES disagree"):
        load_rigged_avatar(swapped)

    rig = load_rigged_avatar(swapped, overrides=ARMS)
    # the cost, as a number: hip_l now drives the bone on the body's +x side
    assert float(rig.body.joints[rig.slots["hip_l"]].rest[0, 3]) > 0.0
    assert float(rig.body.joints[rig.slots["shoulder_l"]].rest[0, 3]) < 0.0
