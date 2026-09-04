"""The authored character and the hand-written `.glb`: every claim measured.

`avatar.custom_avatar` loads a body with `trimesh.load(path, force="mesh")`,
which flattens a scene to one mesh and throws the SKELETON away, so a walk
moves a studio body as a statue. Fixing that needs a rigged fixture to fix it
against - and the fixture cannot be downloaded: the owner's asset folder holds
only obfuscated CLO `.avt` payloads, and SMPL / SMPL-X / STAR are
non-commercial (research doc 67 §2). So the character is authored in code and
tested here, where "it exported fine" is not evidence.

The numbers below are MEASURED on this machine at stature 1.80 m, not
inherited from anywhere: 18,404 triangles, one shell, Euler characteristic 2,
height exact to float64 and to 5e-5 mm through float32, upper arm 104.6 mm
across, trunk 1.4059 wide-to-deep. Tolerances are tight on purpose; a number
that moves should be read, not widened.
"""

from __future__ import annotations

import hashlib
import json
import struct

import numpy as np
import pytest
import trimesh

from seamkiln.figure import TORSO_SQUASH
from seamkiln.rig.character import JOINT_NAMES, JOINT_PARENTS, build_character
from seamkiln.rig.gltf_write import (
    Skeleton,
    SkinnedPrimitive,
    accessor_array,
    column_major,
    read_glb,
    write_glb,
)

STATURE = 1.80
COMPONENT_SIZE = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
TYPE_COUNT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


@pytest.fixture(scope="module")
def character():
    return build_character(STATURE)


@pytest.fixture(scope="module")
def written(character, tmp_path_factory):
    path = tmp_path_factory.mktemp("rig") / "body.glb"
    manifest = character.to_glb(path)
    gltf, blob = read_glb(path)
    return path, manifest, gltf, blob


# ---------------------------------------------------------------------------
# the body
# ---------------------------------------------------------------------------


def test_the_body_is_one_watertight_manifold_shell(character):
    """One surface, not thirty solids sharing space.

    `figure.figure()` concatenates closed cones and balls - 34 shells that
    interpenetrate - which is fine for a collider and impossible for a skin: a
    vertex inside another shell has nowhere sane to go when the joint bends.
    """
    mesh = character.mesh()
    assert mesh.is_watertight
    assert mesh.body_count == 1
    assert mesh.euler_number == 2  # genus 0: no handles, no holes
    assert mesh.volume > 0.0  # positive volume means the winding is outward
    # Winding is settled topologically, not face by face against the field's
    # gradient: judging each face alone got six of 18,404 wrong - all in the
    # crease of an armpit, where the gradient at a triangle's centre leans
    # across the surface - and twelve inconsistent edges is a black patch in
    # a viewer and inward normals in a collider.
    assert mesh.is_winding_consistent


def test_triangle_count_is_ci_sized(character):
    """Dense enough to drape against, small enough to build in a test.

    `figure.figure()` at this stature is 9,760 triangles in 34
    interpenetrating shells (measured 2026-09-04); this is 18,404 in one.
    """
    assert len(character.faces) == 18404
    assert len(character.vertices) == 9204
    assert len(character.faces) > 9760  # denser than figure.figure()'s mesh


def test_no_triangle_is_degenerate(character):
    """A face with no normal is a NaN in a collider, not a contact.

    Marching tetrahedra puts a vertex wherever the field crosses zero on a
    grid edge; when it crosses AT a corner, several edges meet there and the
    triangles between them come out with zero area. The polygoniser nudges the
    crossing off the ends of the edge, which is why this holds.
    """
    tri = character.vertices[character.faces]
    area = 0.5 * np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    assert float(area.min()) > 1e-11


def test_height_is_exactly_the_requested_stature():
    """One number scales the whole body, and it is honoured to the micron.

    A body silently 1 mm short is the same class of error as one silently in
    centimetres: every garment drafted for it is drafted for something else.
    """
    for stature in (1.50, 1.80, 2.05):
        built = build_character(stature)
        assert abs(built.measurements()["height_m"] - stature) < 1e-9
        assert abs(float(built.vertices[:, 1].min())) < 1e-12  # feet on y = 0


def test_the_body_is_clothable(character):
    """Law 20: an unclothable body reads as a broken cloth solver.

    `figure.py`'s first cut had a 194 mm upper arm on a 1.8 m body where a
    real one is about 100, and no sleeve drafted to a matching armhole could
    go round it. Measured here: 104.6 mm, against `figure.py`'s own 122.4 mm
    (its `upper_r` is 0.034 of stature, so 0.034 x 2 x 1.8).
    """
    m = character.measurements()
    assert 0.095 < m["upper_arm_width_m"] < 0.115
    assert m["upper_arm_width_m"] < 0.034 * 2 * STATURE  # slimmer than figure.py's arm
    assert 0.44 < m["shoulder_span_m"] < 0.50


def test_the_trunk_is_elliptical_not_a_body_of_revolution(character):
    """A round trunk lets a zipped jacket yaw 15-20 degrees a stride.

    Measured on the walk in A65: it also drifted 32 mm sideways in two
    seconds, because nothing on the body resisted a garment turning about it.
    `figure.TORSO_SQUASH` is 1.10 wide by 0.78 deep, a ratio of 1.4103; this
    body measures 1.4059 at the waist, 0.3 % under.
    """
    m = character.measurements()
    target = TORSO_SQUASH[0] / TORSO_SQUASH[1]
    assert m["trunk_width_m"] > m["trunk_depth_m"]
    assert abs(m["trunk_width_depth_ratio"] - target) < 0.02
    assert abs(m["trunk_width_depth_ratio"] - 1.4059) < 0.005


def test_two_builds_of_the_same_stature_are_identical(tmp_path):
    """Determinism is a feature: same inputs, same BYTES.

    Not "same geometry" - the same file, hash for hash. A fixture whose bytes
    move cannot be a regression baseline for anything downstream.
    """
    first, second = tmp_path / "a.glb", tmp_path / "b.glb"
    build_character(STATURE).to_glb(first)
    build_character(STATURE).to_glb(second)
    assert first.read_bytes() == second.read_bytes()
    assert hashlib.sha256(first.read_bytes()).hexdigest() == (
        hashlib.sha256(second.read_bytes()).hexdigest()
    )


def test_build_refuses_nonsense_with_the_fix_in_the_message():
    with pytest.raises(ValueError, match="must be positive"):
        build_character(0.0)
    with pytest.raises(ValueError, match="cannot resolve a hand"):
        build_character(STATURE, cells_tall=8)


# ---------------------------------------------------------------------------
# the rig
# ---------------------------------------------------------------------------


def test_joint_names_are_the_studio_convention_not_seamkilns(character):
    """The fixture must force the name-mapping layer to exist.

    A real studio file will never use seamkiln's `pelvis` / `shoulder_l`. If
    the fixture used them, the mapping would be satisfied by an accidental
    match and would never be written - so the names here are glTF/Mixamo's
    and are asserted to be DISJOINT from seamkiln's own.
    """
    from seamkiln.avatar import JOINTS
    from seamkiln.figure import JOINT_NAMES as SEAMKILN_JOINTS

    assert character.skeleton.names == JOINT_NAMES
    assert "Hips" in JOINT_NAMES and "LeftUpLeg" in JOINT_NAMES and "RightForeArm" in JOINT_NAMES
    assert not set(JOINT_NAMES) & set(SEAMKILN_JOINTS)
    assert not set(JOINT_NAMES) & set(JOINTS)
    assert not any(name.islower() for name in JOINT_NAMES)


def test_the_hierarchy_is_a_single_rooted_tree_in_parents_first_order(character):
    """Parents before children: world transforms compose in one forward pass."""
    skeleton = character.skeleton
    assert skeleton.roots == (0,)
    assert skeleton.names[0] == "Hips"
    for i, parent in enumerate(skeleton.parents):
        assert parent < i
    assert JOINT_PARENTS[JOINT_NAMES.index("LeftForeArm")] == JOINT_NAMES.index("LeftArm")
    assert JOINT_PARENTS[JOINT_NAMES.index("LeftUpLeg")] == JOINT_NAMES.index("Hips")
    # A left joint's mirror sits at the same height and EXACTLY the opposite
    # x - not approximately. The grid is built with a line on the body's plane
    # of symmetry for this reason: left to fall where it liked, its lines sat
    # 0.79 mm off centre, and recentring the mesh on its own bounds then
    # dragged the skeleton 1.6 mm off the mirror. A left/right asymmetry the
    # body does not have is one every graded garment inherits.
    left = skeleton.positions[JOINT_NAMES.index("LeftArm")]
    right = skeleton.positions[JOINT_NAMES.index("RightArm")]
    assert float(left[0] + right[0]) == 0.0
    assert float(left[1] - right[1]) == 0.0


def test_the_body_is_centred_on_its_own_plane_of_symmetry():
    """x = 0 is the mirror, at every stature, to the last bit.

    The grid the surface is polygonised on carries a line on x = 0 and the
    same number of cells either side, so the body cannot drift off centre by
    a fraction of a cell and take the skeleton with it.
    """
    for stature in (1.50, 1.80, 2.05):
        v = build_character(stature).vertices
        assert float(v[:, 0].min() + v[:, 0].max()) == 0.0


def test_weights_are_normalised_and_at_most_four_per_vertex(character):
    sums = character.skin_weights.sum(axis=1)
    assert float(np.max(np.abs(sums - 1.0))) < 1e-6
    assert character.skin_weights.shape[1] == 4
    assert int((character.skin_weights > 0.0).sum(axis=1).max()) <= 4
    assert float(character.skin_weights.min()) >= 0.0
    assert int(character.skin_joints.max()) < len(JOINT_NAMES)


def test_no_vertex_is_bound_to_a_joint_more_than_two_hops_away(character):
    """A chest vertex dragged by a hand is a garment pulled off a body.

    The binding rule is the nearest bone plus everything within two hops of it
    in the hierarchy; this measures the rule rather than trusting it.
    """
    names = list(JOINT_NAMES)
    hand = names.index("LeftHand")
    chest_y = character.skeleton.positions[names.index("Chest")][1]
    chest = np.abs(character.vertices[:, 1] - chest_y) < 0.03
    influenced = character.skin_joints[chest][character.skin_weights[chest] > 0.0]
    assert hand not in set(influenced.tolist())


def test_the_armpit_and_the_crotch_survive_an_extreme_angle(character):
    """A collapsed region traps cloth, and no test of the weights alone sees it.

    Measured by POSING the body with linear blend skinning: arms swung down
    from the A-pose to vertical (a 40 degree adduction, the worst case for the
    armpit) and elbows folded to 120 degrees. Volume is the collapse detector -
    the candy-wrapper failure destroys it locally - and the smallest triangle
    is the crease detector.

    Measured here, as a fraction of bind area: **0.3744** arms, **0.2394**
    elbows, **0.6133** legs. The bar is 0.20 because the kernel decides it,
    and the difference is large: a `(1/d - 1/R)^2` falloff is singular at the
    bone and left the inner elbow at **0.0929**, while the bounded
    `(1 - d/R)^2` at the same R gives the 0.2394 above. If this test drops
    back towards a tenth, the skin has gone singular again.
    """
    bind = character.mesh()
    tri = character.vertices[character.faces]
    bind_area = 0.5 * np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    cases = {
        "arms adducted to vertical": {
            "LeftArm": ((0.0, 0.0, 1.0), -40.0),
            "RightArm": ((0.0, 0.0, 1.0), 40.0),
        },
        "elbows folded 120": {
            "LeftForeArm": ((1.0, 0.0, 0.0), 120.0),
            "RightForeArm": ((1.0, 0.0, 0.0), 120.0),
        },
        "legs adducted 20": {
            "LeftUpLeg": ((0.0, 0.0, 1.0), -20.0),
            "RightUpLeg": ((0.0, 0.0, 1.0), 20.0),
        },
    }
    for label, rotations in cases.items():
        posed = character.posed_vertices(rotations)
        mesh = trimesh.Trimesh(vertices=posed, faces=character.faces, process=False)
        assert mesh.is_watertight, label
        assert mesh.volume > 0.92 * bind.volume, label
        t = posed[character.faces]
        area = 0.5 * np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1)
        assert float((area / np.maximum(bind_area, 1e-15)).min()) > 0.20, label


def test_posing_an_unknown_joint_refuses_by_name(character):
    with pytest.raises(KeyError, match="unknown joint"):
        character.posed_vertices({"pelvis": ((1.0, 0.0, 0.0), 10.0)})
    with pytest.raises(KeyError, match="Mixamo"):
        character.joint_index("shoulder_l")


# ---------------------------------------------------------------------------
# the writer
# ---------------------------------------------------------------------------


def test_the_glb_container_is_valid_and_padded(written):
    """Twelve-byte header, then chunks on four-byte boundaries.

    JSON pads with spaces and BIN with zeros; the header's length counts the
    padding. A viewer that reads a mis-padded file at all reads it wrong.
    """
    path, _, _, _ = written
    raw = path.read_bytes()
    magic, version, length = struct.unpack_from("<III", raw, 0)
    assert magic == 0x46546C67  # b"glTF"
    assert version == 2
    assert length == len(raw)

    offset, seen = 12, []
    while offset < length:
        chunk_len, chunk_type = struct.unpack_from("<II", raw, offset)
        offset += 8
        data = raw[offset : offset + chunk_len]
        offset += chunk_len
        assert chunk_len % 4 == 0
        seen.append(chunk_type)
        if chunk_type == 0x4E4F534A:  # JSON
            assert data.rstrip(b"\x20") == data.strip()
            json.loads(data.decode("utf-8"))
        else:
            assert chunk_type == 0x004E4942  # BIN
    assert seen == [0x4E4F534A, 0x004E4942]
    assert offset == length


def test_every_accessor_matches_its_buffer_view(written):
    """byteLength == count x components x component size, and aligned.

    One accessor per bufferView, each view four-byte aligned, makes this an
    invariant rather than a coincidence - and it is the check that catches a
    writer that packed VEC3 as VEC4 or forgot a count.
    """
    _, _, gltf, blob = written
    for index, acc in enumerate(gltf["accessors"]):
        view = gltf["bufferViews"][acc["bufferView"]]
        size = COMPONENT_SIZE[acc["componentType"]] * TYPE_COUNT[acc["type"]]
        assert view["byteLength"] == acc["count"] * size, index
        assert view["byteOffset"] % 4 == 0, index
        assert view["byteOffset"] + view["byteLength"] <= len(blob), index
    assert gltf["buffers"][0]["byteLength"] <= len(blob)


def test_position_min_max_are_the_meshs_real_bounds(character, written):
    """min/max are a contract, not decoration: importers cull and frame on them."""
    _, _, gltf, _ = written
    attributes = gltf["meshes"][0]["primitives"][0]["attributes"]
    acc = gltf["accessors"][attributes["POSITION"]]
    positions = character.vertices.astype(np.float32)
    assert np.allclose(acc["min"], positions.min(axis=0), atol=0.0, rtol=0.0)
    assert np.allclose(acc["max"], positions.max(axis=0), atol=0.0, rtol=0.0)
    assert acc["min"][1] == pytest.approx(0.0, abs=1e-6)
    assert acc["max"][1] == pytest.approx(STATURE, abs=1e-3)


def test_the_primitive_carries_the_four_skinning_attributes(written):
    _, _, gltf, blob = written
    primitive = gltf["meshes"][0]["primitives"][0]
    attributes = primitive["attributes"]
    assert set(attributes) == {"POSITION", "NORMAL", "JOINTS_0", "WEIGHTS_0"}
    assert primitive["mode"] == 4  # triangles
    assert gltf["accessors"][attributes["JOINTS_0"]]["componentType"] in (5121, 5123)
    assert gltf["accessors"][attributes["WEIGHTS_0"]]["componentType"] == 5126
    weights = accessor_array(gltf, blob, attributes["WEIGHTS_0"])
    assert float(np.max(np.abs(weights.sum(axis=1) - 1.0))) < 1e-6
    joints = accessor_array(gltf, blob, attributes["JOINTS_0"])
    assert int(joints.max()) < len(gltf["skins"][0]["joints"])
    normals = accessor_array(gltf, blob, attributes["NORMAL"])
    assert np.allclose(np.linalg.norm(normals, axis=1), 1.0, atol=1e-5)


def test_the_skin_and_the_node_hierarchy_are_written(written):
    _, _, gltf, _ = written
    skin = gltf["skins"][0]
    assert skin["joints"] == list(range(len(JOINT_NAMES)))
    assert gltf["nodes"][skin["skeleton"]]["name"] == "Hips"
    for index, name in enumerate(JOINT_NAMES):
        assert gltf["nodes"][index]["name"] == name
    hips = gltf["nodes"][0]
    assert set(hips["children"]) == {
        JOINT_NAMES.index("Spine"),
        JOINT_NAMES.index("LeftUpLeg"),
        JOINT_NAMES.index("RightUpLeg"),
    }
    mesh_node = next(n for n in gltf["nodes"] if "mesh" in n)
    assert mesh_node["skin"] == 0
    assert gltf["scenes"][0]["nodes"] == [0, gltf["nodes"].index(mesh_node)]


def test_matrices_go_out_column_major(character, written):
    """glTF stores a matrix as sixteen COLUMN-major floats.

    numpy is row-major, so translation lands in elements 12, 13, 14 only if
    the transpose happened. Read the inverse bind matrix of a joint back and
    check it against the joint's own world position - if this passes, an
    importer puts the skeleton where the mesh is; if it fails, the body turns
    inside out and nothing else in the file will tell you why.
    """
    _, _, gltf, blob = written
    flat = column_major(np.array([[1, 0, 0, 7.0], [0, 1, 0, 8.0], [0, 0, 1, 9.0], [0, 0, 0, 1]]))
    assert flat[12:15] == [7.0, 8.0, 9.0]
    assert flat[:12] == [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0]

    ibm = accessor_array(gltf, blob, gltf["skins"][0]["inverseBindMatrices"])
    assert ibm.shape == (len(JOINT_NAMES), 16)
    for index, name in enumerate(JOINT_NAMES):
        expected = -character.skeleton.positions[index]
        assert np.allclose(ibm[index][12:15], expected, atol=1e-6), name
    with pytest.raises(ValueError, match="4x4"):
        column_major(np.eye(3))


def test_the_manifest_states_the_units_and_the_up_axis(written):
    """Law 17: a self-describing format is left alone, and SAYS so.

    glTF 2.0 is +Y up, +Z forward, metres by specification. Adding "our own"
    rotation once put a jacket on its face through the floor.
    """
    _, manifest, gltf, _ = written
    assert manifest["units"] == "m"
    assert manifest["up_axis"] == "+Y"
    assert manifest["forward_axis"] == "+Z"
    assert "column-major" in manifest["matrix_order"]
    assert manifest["triangles"] == 18404
    assert manifest["joints"] == len(JOINT_NAMES)
    assert manifest["joint_names"] == list(JOINT_NAMES)
    assert gltf["asset"]["version"] == "2.0"
    assert gltf["asset"]["extras"]["seamkiln"]["stature_m"] == STATURE


def test_trimesh_reads_the_geometry_back_watertight(written):
    """The independent check, and the reason this package exists.

    trimesh loads the GEOMETRY of a `.glb` perfectly well and ignores the
    `skins` array entirely - so it is an honest referee for the mesh and no
    use at all for the rig. Both halves of that are asserted here.
    """
    path, _, gltf, _ = written
    mesh = trimesh.load(str(path), force="mesh")
    assert isinstance(mesh, trimesh.Trimesh)
    assert mesh.is_watertight
    assert mesh.body_count == 1
    assert len(mesh.faces) == 18404
    assert float(mesh.extents[1]) == pytest.approx(STATURE, abs=1e-3)
    assert "skins" in gltf  # written, and invisible to the loader above
    assert not hasattr(mesh, "skin")


def test_the_writer_refuses_a_broken_skin(character, tmp_path):
    """Fail loud and cheap, with the fix in the message - not in a viewer."""
    skeleton = character.skeleton
    good = character.primitive()
    bad = SkinnedPrimitive(
        positions=good.positions,
        normals=good.normals,
        indices=good.indices,
        joints=good.joints,
        weights=good.weights * 0.5,
    )
    with pytest.raises(ValueError, match="sum to 1"):
        write_glb(tmp_path / "bad.glb", bad, skeleton)

    stray = SkinnedPrimitive(
        positions=good.positions,
        normals=good.normals,
        indices=good.indices,
        joints=np.full_like(good.joints, len(skeleton.names)),
        weights=good.weights,
    )
    with pytest.raises(ValueError, match="JOINTS_0 references joint"):
        write_glb(tmp_path / "stray.glb", stray, skeleton)

    with pytest.raises(ValueError, match="parents must come BEFORE"):
        Skeleton(names=("A", "B"), parents=(1, -1), positions=np.zeros((2, 3)))
