"""The skinned-glTF reader and the joint-name table, against files built here.

The fixture is written BY HAND in this module - json + struct + numpy, no new
dependency and no reliance on any other module landing - because the point of
`rig.gltf_read` is that trimesh 5.1.0 ignores glTF skins entirely, so there is
nothing already in the tree that can produce a skinned file to test against.
Building the bytes here also means the awkward cases a real exporter emits
(unsigned-short joint indices, normalised integer weights, an interleaved
buffer view, several primitives, a skeleton that is not the scene root) are
each one keyword away instead of one download away.
"""

from __future__ import annotations

import base64
import hashlib
import json
import struct
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from seamkiln.avatar import JOINTS
from seamkiln.rig.gltf_read import RigReadError, read_skinned_gltf
from seamkiln.rig.naming import (
    ALIASES,
    UNCOVERED,
    UNMAPPABLE,
    JointMap,
    RigNameError,
    map_joint_names,
    normalise,
)

FLOAT = 5126
UBYTE = 5121
USHORT = 5123
UINT = 5125
_NP = {FLOAT: "<f4", UBYTE: "<u1", USHORT: "<u2", UINT: "<u4"}

# A 200 mm box, 8 vertices, 12 triangles. Small enough to check by eye.
VERTS = np.array(
    [
        [-0.1, 0.0, -0.1],
        [0.1, 0.0, -0.1],
        [0.1, 0.0, 0.1],
        [-0.1, 0.0, 0.1],
        [-0.1, 0.45, -0.1],
        [0.1, 0.45, -0.1],
        [0.1, 0.45, 0.1],
        [-0.1, 0.45, 0.1],
    ],
    dtype=np.float64,
)
FACES = np.array(
    [
        [0, 2, 1],
        [0, 3, 2],
        [4, 5, 6],
        [4, 6, 7],
        [0, 1, 5],
        [0, 5, 4],
        [1, 2, 6],
        [1, 6, 5],
        [2, 3, 7],
        [2, 7, 6],
        [3, 0, 4],
        [3, 4, 7],
    ],
    dtype=np.int64,
)

# name, parent index (into this list, None for the scene root), local translation
Bone = tuple[str, "int | None", tuple[float, float, float]]
DEFAULT_BONES: tuple[Bone, ...] = (
    ("Armature", None, (0.0, 0.05, 0.0)),  # NOT a joint: the skin's root is below it
    ("mixamorig:Hips", 0, (0.0, 0.9, 0.0)),
    ("mixamorig:LeftUpLeg", 1, (0.09, 0.0, 0.0)),
    ("mixamorig:LeftLeg", 2, (0.0, -0.45, 0.0)),
)
# Which bones the skin actually lists (indices into the bone list).
DEFAULT_SKIN = (1, 2, 3)

MIXAMO_BONES: tuple[Bone, ...] = (
    ("Armature", None, (0.0, 0.0, 0.0)),
    ("mixamorig:Hips", 0, (0.0, 0.95, 0.0)),
    ("mixamorig:Spine", 1, (0.0, 0.1, 0.0)),
    ("mixamorig:LeftShoulder", 2, (0.04, 0.35, 0.0)),
    ("mixamorig:LeftArm", 3, (0.13, 0.0, 0.0)),
    ("mixamorig:LeftForeArm", 4, (0.0, -0.28, 0.0)),
    ("mixamorig:RightShoulder", 2, (-0.04, 0.35, 0.0)),
    ("mixamorig:RightArm", 6, (-0.13, 0.0, 0.0)),
    ("mixamorig:RightForeArm", 7, (0.0, -0.28, 0.0)),
    ("mixamorig:LeftUpLeg", 1, (0.09, 0.0, 0.0)),
    ("mixamorig:LeftLeg", 9, (0.0, -0.45, 0.0)),
    ("mixamorig:RightUpLeg", 1, (-0.09, 0.0, 0.0)),
    ("mixamorig:RightLeg", 11, (0.0, -0.45, 0.0)),
)
MIXAMO_SKIN = tuple(range(1, len(MIXAMO_BONES)))


# --------------------------------------------------------------------------
# the hand-built writer


class _Blob:
    """Buffer views and accessors, packed 4-byte aligned like a real exporter."""

    def __init__(self) -> None:
        self.data = bytearray()
        self.views: list[dict[str, Any]] = []
        self.accessors: list[dict[str, Any]] = []

    def view(self, raw: bytes, stride: int | None = None) -> int:
        while len(self.data) % 4:
            self.data.append(0)
        entry: dict[str, Any] = {
            "buffer": 0,
            "byteOffset": len(self.data),
            "byteLength": len(raw),
        }
        if stride is not None:
            entry["byteStride"] = stride
        self.data += raw
        self.views.append(entry)
        return len(self.views) - 1

    def accessor(
        self,
        view: int,
        *,
        count: int,
        kind: str,
        component: int,
        byte_offset: int = 0,
        normalized: bool = False,
        bounds: np.ndarray | None = None,
    ) -> int:
        entry: dict[str, Any] = {
            "bufferView": view,
            "componentType": component,
            "count": count,
            "type": kind,
        }
        if byte_offset:
            entry["byteOffset"] = byte_offset
        if normalized:
            entry["normalized"] = True
        if bounds is not None:
            entry["min"] = [float(v) for v in bounds.min(axis=0)]
            entry["max"] = [float(v) for v in bounds.max(axis=0)]
        self.accessors.append(entry)
        return len(self.accessors) - 1

    def packed(self, array: np.ndarray, component: int, kind: str, **kw: Any) -> int:
        raw = np.ascontiguousarray(array, dtype=np.dtype(_NP[component])).tobytes()
        return self.accessor(self.view(raw), count=len(array), kind=kind, component=component, **kw)


def _local_matrix(translation: tuple[float, float, float]) -> np.ndarray:
    m = np.eye(4)
    m[:3, 3] = translation
    return m


def _world(bones: tuple[Bone, ...], index: int) -> np.ndarray:
    _name, parent, translation = bones[index]
    local = _local_matrix(translation)
    return local if parent is None else _world(bones, parent) @ local


def _skin_weights(n_joints: int) -> tuple[np.ndarray, np.ndarray]:
    """Bottom ring on the last bone; top ring shared 0.25/0.75 with bone 1."""
    ids = np.zeros((8, 4), dtype=np.int64)
    weights = np.zeros((8, 4), dtype=np.float64)
    ids[:4, 0] = n_joints - 1
    weights[:4, 0] = 1.0
    ids[4:, 0] = 1
    ids[4:, 1] = n_joints - 1
    weights[4:, 0] = 0.25
    weights[4:, 1] = 0.75
    return ids, weights


def _normals() -> np.ndarray:
    n = VERTS.copy()
    n[:, 1] -= 0.225
    return n / np.linalg.norm(n, axis=1)[:, None]


def assemble(
    *,
    bones: tuple[Bone, ...] = DEFAULT_BONES,
    skin_bones: tuple[int, ...] = DEFAULT_SKIN,
    joint_component: int = UBYTE,
    weight_component: int = FLOAT,
    interleaved: bool = False,
    split_primitives: bool = False,
    include_skin: bool = True,
    include_normals: bool = True,
    include_indices: bool = True,
    weights: np.ndarray | None = None,
    joints_1: bool = False,
    sparse_positions: bool = False,
    extensions_required: list[str] | None = None,
    buffer_uri: str | None = None,
) -> tuple[dict[str, Any], bytes]:
    """Build a glTF document + its binary blob. Deterministic for fixed inputs."""
    blob = _Blob()
    ids, base_weights = _skin_weights(len(skin_bones))
    if weights is not None:
        base_weights = weights
    normals = _normals()

    # An unindexed primitive is a triangle SOUP, so its vertex count must be a
    # multiple of three: six vertices, two triangles.
    keep = 8 if include_indices else 6
    verts = VERTS[:keep]

    def geometry(faces: np.ndarray) -> dict[str, Any]:
        attrs: dict[str, Any] = {}
        if interleaved:
            packed = np.empty((keep, 6), dtype=np.dtype("<f4"))
            packed[:, :3] = verts
            packed[:, 3:] = normals[:keep]
            view = blob.view(packed.tobytes(), stride=24)
            attrs["POSITION"] = blob.accessor(
                view, count=keep, kind="VEC3", component=FLOAT, bounds=verts
            )
            attrs["NORMAL"] = blob.accessor(
                view, count=keep, kind="VEC3", component=FLOAT, byte_offset=12
            )
        else:
            attrs["POSITION"] = blob.packed(verts, FLOAT, "VEC3", bounds=verts)
            if include_normals:
                attrs["NORMAL"] = blob.packed(normals[:keep], FLOAT, "VEC3")
        if sparse_positions:
            blob.accessors[attrs["POSITION"]]["sparse"] = {
                "count": 1,
                "indices": {"bufferView": 0, "componentType": USHORT},
                "values": {"bufferView": 0},
            }
        if include_skin:
            attrs["JOINTS_0"] = blob.packed(ids[:keep], joint_component, "VEC4")
            raw_weights = base_weights[:keep]
            attrs["WEIGHTS_0"] = blob.packed(
                raw_weights
                if weight_component == FLOAT
                else np.rint(raw_weights * (255.0 if weight_component == UBYTE else 65535.0)),
                weight_component,
                "VEC4",
                normalized=weight_component != FLOAT,
            )
            if joints_1:
                attrs["JOINTS_1"] = blob.packed(np.zeros((keep, 4)), UBYTE, "VEC4")
                attrs["WEIGHTS_1"] = blob.packed(np.zeros((keep, 4)), FLOAT, "VEC4")
        prim: dict[str, Any] = {"attributes": attrs}
        if include_indices:
            prim["indices"] = blob.packed(faces.reshape(-1), UINT, "SCALAR")
        return prim

    primitives = (
        [geometry(FACES[:6]), geometry(FACES[6:])] if split_primitives else [geometry(FACES)]
    )

    nodes: list[dict[str, Any]] = []
    for name, _parent, translation in bones:
        nodes.append({"name": name, "translation": list(translation)})
    for i, (_name, parent, _t) in enumerate(bones):
        if parent is not None:
            nodes[parent].setdefault("children", []).append(i)
    body: dict[str, Any] = {"name": "Body", "mesh": 0}
    if include_skin:
        body["skin"] = 0
    body_index = len(nodes)
    nodes.append(body)

    doc: dict[str, Any] = {
        "asset": {"version": "2.0", "generator": "seamkiln tests"},
        "scene": 0,
        "scenes": [{"nodes": [0, body_index]}],
        "nodes": nodes,
        "meshes": [{"name": "Body", "primitives": primitives}],
    }
    if include_skin:
        ibm = np.stack([np.linalg.inv(_world(bones, b)) for b in skin_bones])
        doc["skins"] = [
            {
                "name": "Skin",
                "skeleton": skin_bones[0],
                "joints": list(skin_bones),
                "inverseBindMatrices": blob.packed(
                    ibm.transpose(0, 2, 1).reshape(len(skin_bones), 16), FLOAT, "MAT4"
                ),
            }
        ]
    if extensions_required:
        doc["extensionsRequired"] = list(extensions_required)
    doc["bufferViews"] = blob.views
    doc["accessors"] = blob.accessors
    buffer: dict[str, Any] = {"byteLength": len(blob.data)}
    if buffer_uri:
        buffer["uri"] = buffer_uri
    doc["buffers"] = [buffer]
    return doc, bytes(blob.data)


def glb_bytes(doc: dict[str, Any], blob: bytes) -> bytes:
    js = json.dumps(doc, separators=(",", ":")).encode("utf-8")
    js += b" " * (-len(js) % 4)
    body = blob + b"\x00" * (-len(blob) % 4)
    total = 12 + 8 + len(js) + (8 + len(body) if body else 0)
    out = struct.pack("<III", 0x46546C67, 2, total)
    out += struct.pack("<II", len(js), 0x4E4F534A) + js
    if body:
        out += struct.pack("<II", len(body), 0x004E4942) + body
    return out


def write_glb(path: Path, **kw: Any) -> Path:
    doc, blob = assemble(**kw)
    path.write_bytes(glb_bytes(doc, blob))
    return path


# --------------------------------------------------------------------------
# the reader


def test_round_trip_geometry_weights_and_hierarchy(tmp_path: Path) -> None:
    body = read_skinned_gltf(write_glb(tmp_path / "body.glb"))

    assert np.abs(body.vertices - VERTS).max() < 1e-6
    assert np.array_equal(body.faces, FACES)
    assert np.abs(body.normals - _normals()).max() < 1e-6

    ids, weights = _skin_weights(len(DEFAULT_SKIN))
    assert np.array_equal(body.joint_indices, ids)
    assert np.abs(body.weights - weights).max() < 1e-6

    assert body.joint_names == ("mixamorig:Hips", "mixamorig:LeftUpLeg", "mixamorig:LeftLeg")
    assert [j.parent for j in body.joints] == [None, 0, 1]
    # The skeleton root sits under an "Armature" node that the skin does not
    # list: its 50 mm lift must survive into the rest pose.
    assert body.joints[0].rest[1, 3] == pytest.approx(0.95, abs=1e-9)
    assert body.joints[1].local[0, 3] == pytest.approx(0.09, abs=1e-9)
    assert body.joints[2].rest[1, 3] == pytest.approx(0.50, abs=1e-9)
    for joint in body.joints:
        assert np.abs(joint.inverse_bind @ joint.rest - np.eye(4)).max() < 1e-6
    assert body.notes == ()


@pytest.mark.parametrize("component", [UBYTE, USHORT])
def test_joint_indices_read_as_byte_and_as_short(tmp_path: Path, component: int) -> None:
    body = read_skinned_gltf(write_glb(tmp_path / f"j{component}.glb", joint_component=component))
    assert np.array_equal(body.joint_indices, _skin_weights(len(DEFAULT_SKIN))[0])
    assert body.joint_indices.dtype == np.int32


@pytest.mark.parametrize(
    ("component", "tolerance"),
    [(UBYTE, 1.0e-3), (USHORT, 4.0e-6)],
)
def test_normalised_integer_weights(tmp_path: Path, component: int, tolerance: float) -> None:
    """Quantised weights come back within their own quantisation - measured, not hoped.

    These are the measured maxima and not a comfortable round number. A weight
    of 0.25 stored as a normalised byte is round(63.75)/255 = 64/255 =
    0.2509804, which is 9.804e-4 out; as a normalised short it is
    round(16383.75)/65535 = 16384/65535 = 0.2500038, 3.815e-6 out. The
    round-trip is exact to 1e-6 only for FLOAT weights, and claiming otherwise
    for the integer paths would be a claim about the format that is not true.
    """
    body = read_skinned_gltf(write_glb(tmp_path / "q.glb", weight_component=component))
    _, weights = _skin_weights(len(DEFAULT_SKIN))
    error = float(np.abs(body.weights - weights).max())
    assert error < tolerance, error
    assert error > 0.0  # it really is the quantised path


def test_interleaved_byte_stride_matches_the_tight_layout(tmp_path: Path) -> None:
    tight = read_skinned_gltf(write_glb(tmp_path / "tight.glb"))
    woven = read_skinned_gltf(write_glb(tmp_path / "woven.glb", interleaved=True))
    assert np.abs(woven.vertices - tight.vertices).max() < 1e-6
    assert np.abs(woven.normals - tight.normals).max() < 1e-6


def test_several_primitives_concatenate_with_faces_rebased(tmp_path: Path) -> None:
    body = read_skinned_gltf(write_glb(tmp_path / "split.glb", split_primitives=True))
    assert len(body.vertices) == 16
    assert len(body.faces) == 12
    assert np.array_equal(body.faces[:6], FACES[:6])
    assert np.array_equal(body.faces[6:], FACES[6:] + 8)
    assert "2 primitives concatenated" in " ".join(body.notes)


def test_gltf_plus_external_bin_reads_the_same(tmp_path: Path) -> None:
    doc, blob = assemble(buffer_uri="body.bin")
    (tmp_path / "body.bin").write_bytes(blob)
    (tmp_path / "body.gltf").write_text(json.dumps(doc), encoding="utf-8")
    loose = read_skinned_gltf(tmp_path / "body.gltf")
    packed = read_skinned_gltf(write_glb(tmp_path / "body.glb"))
    assert np.array_equal(loose.vertices, packed.vertices)
    assert loose.joint_names == packed.joint_names


def test_a_data_uri_buffer_reads_the_same(tmp_path: Path) -> None:
    """Blender's "embed buffers" .gltf writes the whole blob as base64."""
    doc, blob = assemble()
    doc["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(
        blob
    ).decode("ascii")
    (tmp_path / "embedded.gltf").write_text(json.dumps(doc), encoding="utf-8")
    embedded = read_skinned_gltf(tmp_path / "embedded.gltf")
    packed = read_skinned_gltf(write_glb(tmp_path / "body.glb"))
    assert np.array_equal(embedded.vertices, packed.vertices)


def test_a_node_matrix_is_read_column_major(tmp_path: Path) -> None:
    """glTF stores `matrix` column-major; transposing it wrongly mirrors a character.

    The same transform written as TRS and as a matrix must give the same rest
    pose to the last bit, so this compares them rather than trusting either.
    """
    doc, blob = assemble()
    node = doc["nodes"][0]
    translation = node.pop("translation")
    matrix = np.eye(4)
    matrix[:3, 3] = translation
    node["matrix"] = list(matrix.T.reshape(-1))  # column-major, as the spec says
    (tmp_path / "matrix.glb").write_bytes(glb_bytes(doc, blob))
    by_matrix = read_skinned_gltf(tmp_path / "matrix.glb")
    by_trs = read_skinned_gltf(write_glb(tmp_path / "trs.glb"))
    for a, b in zip(by_matrix.joints, by_trs.joints, strict=True):
        assert np.abs(a.rest - b.rest).max() < 1e-12
        assert np.abs(a.local - b.local).max() < 1e-12


def test_a_rotated_non_joint_ancestor_composes_into_the_root_joint(tmp_path: Path) -> None:
    """The Armature node is not in `skin.joints`; its rotation must not be dropped.

    A quarter turn about Z sends the hips' +0.9 m Y offset to -0.9 m X. Drop
    the ancestor and the skeleton stands up while the mesh lies down.
    """
    doc, blob = assemble()
    doc["nodes"][0]["rotation"] = [0.0, 0.0, 2.0**-0.5, 2.0**-0.5]
    (tmp_path / "turned.glb").write_bytes(glb_bytes(doc, blob))
    body = read_skinned_gltf(tmp_path / "turned.glb")
    root = body.joints[0].rest
    assert root[0, 3] == pytest.approx(-0.9, abs=1e-9)
    assert root[1, 3] == pytest.approx(0.05, abs=1e-9)
    assert root[0, 1] == pytest.approx(-1.0, abs=1e-9)


def test_missing_side_car_bin_refuses_by_name(tmp_path: Path) -> None:
    doc, _ = assemble(buffer_uri="body.bin")
    (tmp_path / "body.gltf").write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(RigReadError, match=r"body\.bin"):
        read_skinned_gltf(tmp_path / "body.gltf")


def test_normals_are_computed_when_the_file_carries_none(tmp_path: Path) -> None:
    body = read_skinned_gltf(write_glb(tmp_path / "flat.glb", include_normals=False))
    assert np.abs(np.linalg.norm(body.normals, axis=1) - 1.0).max() < 1e-9
    assert "normals computed" in " ".join(body.notes)


def test_unindexed_primitive_reads_as_a_triangle_soup(tmp_path: Path) -> None:
    body = read_skinned_gltf(write_glb(tmp_path / "noidx.glb", include_indices=False))
    assert len(body.vertices) == 6
    assert np.array_equal(body.faces, [[0, 1, 2], [3, 4, 5]])


def test_an_unindexed_primitive_that_is_not_whole_triangles_refuses(tmp_path: Path) -> None:
    doc, blob = assemble()
    doc["meshes"][0]["primitives"][0].pop("indices")
    (tmp_path / "odd.glb").write_bytes(glb_bytes(doc, blob))
    with pytest.raises(RigReadError, match="not a multiple of 3"):
        read_skinned_gltf(tmp_path / "odd.glb")


def test_a_file_with_no_skin_refuses_instead_of_returning_a_rigless_body(
    tmp_path: Path,
) -> None:
    with pytest.raises(RigReadError) as excinfo:
        read_skinned_gltf(write_glb(tmp_path / "statue.glb", include_skin=False))
    message = str(excinfo.value)
    assert "no skinned node" in message
    assert "statue" in message  # says WHY, not just that it failed
    assert "armature" in message.lower()  # and the fix


def test_sparse_accessor_refuses_by_name(tmp_path: Path) -> None:
    with pytest.raises(RigReadError, match="SPARSE"):
        read_skinned_gltf(write_glb(tmp_path / "sparse.glb", sparse_positions=True))


def test_required_extension_refuses_by_name(tmp_path: Path) -> None:
    with pytest.raises(RigReadError) as excinfo:
        read_skinned_gltf(
            write_glb(tmp_path / "draco.glb", extensions_required=["KHR_draco_mesh_compression"])
        )
    assert "KHR_draco_mesh_compression" in str(excinfo.value)
    assert "Draco compression OFF" in str(excinfo.value)


def test_more_than_four_influences_refuses(tmp_path: Path) -> None:
    with pytest.raises(RigReadError, match="JOINTS_1"):
        read_skinned_gltf(write_glb(tmp_path / "eight.glb", joints_1=True))


def test_a_vertex_with_no_bone_weight_refuses(tmp_path: Path) -> None:
    _, weights = _skin_weights(len(DEFAULT_SKIN))
    weights = weights.copy()
    weights[3] = 0.0
    with pytest.raises(RigReadError) as excinfo:
        read_skinned_gltf(write_glb(tmp_path / "dead.glb", weights=weights))
    assert "NO bone weight" in str(excinfo.value)
    assert "index 3" in str(excinfo.value)


def test_two_skinned_nodes_refuse_until_one_is_named(tmp_path: Path) -> None:
    doc, blob = assemble()
    twin = dict(doc["nodes"][-1])
    twin["name"] = "Body2"
    doc["nodes"].append(twin)
    doc["scenes"][0]["nodes"].append(len(doc["nodes"]) - 1)
    (tmp_path / "twins.glb").write_bytes(glb_bytes(doc, blob))
    with pytest.raises(RigReadError, match="Body2"):
        read_skinned_gltf(tmp_path / "twins.glb")
    body = read_skinned_gltf(tmp_path / "twins.glb", node="Body2")
    assert body.name == "Body2"


def test_a_truncated_glb_refuses(tmp_path: Path) -> None:
    raw = glb_bytes(*assemble())
    (tmp_path / "cut.glb").write_bytes(raw[: len(raw) // 2])
    with pytest.raises(RigReadError, match="truncated"):
        read_skinned_gltf(tmp_path / "cut.glb")


def test_the_same_inputs_give_the_same_bytes_and_the_same_arrays(tmp_path: Path) -> None:
    """Law 5: determinism is a feature, and this pins it."""
    first = glb_bytes(*assemble())
    second = glb_bytes(*assemble())
    assert hashlib.sha256(first).hexdigest() == hashlib.sha256(second).hexdigest()
    (tmp_path / "a.glb").write_bytes(first)
    a = read_skinned_gltf(tmp_path / "a.glb")
    b = read_skinned_gltf(tmp_path / "a.glb")
    for name in ("vertices", "faces", "normals", "joint_indices", "weights"):
        left, right = getattr(a, name), getattr(b, name)
        assert hashlib.sha256(left.tobytes()).hexdigest() == (
            hashlib.sha256(right.tobytes()).hexdigest()
        )


def test_the_arrays_come_back_read_only(tmp_path: Path) -> None:
    body = read_skinned_gltf(write_glb(tmp_path / "body.glb"))
    with pytest.raises(ValueError, match="read-only"):
        body.vertices[0, 0] = 1.0


# --------------------------------------------------------------------------
# a file THIS repo did not write


BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"

# Builds a Mixamo-named skeleton, binds a box to it with one weight per vertex
# (deterministic, unlike automatic weights), and exports a GLB. It is a string
# because it has to run inside Blender's own interpreter, not pytest's.
_EXPORT_RIG = """
import sys

import bpy

BONES = [
    ("mixamorig:Hips", (0.0, 0.0, 1.0), (0.0, 0.0, 1.1), None),
    ("mixamorig:Spine", (0.0, 0.0, 1.1), (0.0, 0.0, 1.4), "mixamorig:Hips"),
    ("mixamorig:LeftArm", (0.2, 0.0, 1.4), (0.45, 0.0, 1.4), "mixamorig:Spine"),
    ("mixamorig:LeftForeArm", (0.45, 0.0, 1.4), (0.7, 0.0, 1.4), "mixamorig:LeftArm"),
    ("mixamorig:RightArm", (-0.2, 0.0, 1.4), (-0.45, 0.0, 1.4), "mixamorig:Spine"),
    ("mixamorig:RightForeArm", (-0.45, 0.0, 1.4), (-0.7, 0.0, 1.4), "mixamorig:RightArm"),
    ("mixamorig:LeftUpLeg", (0.1, 0.0, 1.0), (0.1, 0.0, 0.55), "mixamorig:Hips"),
    ("mixamorig:LeftLeg", (0.1, 0.0, 0.55), (0.1, 0.0, 0.1), "mixamorig:LeftUpLeg"),
    ("mixamorig:RightUpLeg", (-0.1, 0.0, 1.0), (-0.1, 0.0, 0.55), "mixamorig:Hips"),
    ("mixamorig:RightLeg", (-0.1, 0.0, 0.55), (-0.1, 0.0, 0.1), "mixamorig:RightUpLeg"),
]

bpy.ops.wm.read_factory_settings(use_empty=True)
data = bpy.data.armatures.new("Rig")
arm = bpy.data.objects.new("Armature", data)
bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
for name, head, tail, parent in BONES:
    bone = data.edit_bones.new(name)
    bone.head, bone.tail = head, tail
    if parent:
        bone.parent = data.edit_bones[parent]
bpy.ops.object.mode_set(mode="OBJECT")

bpy.ops.mesh.primitive_cube_add(size=0.4, location=(0.0, 0.0, 0.9))
body = bpy.context.active_object
body.name = "Body"
body.parent = arm
body.modifiers.new("Armature", "ARMATURE").object = arm
for name, _head, _tail, _parent in BONES:
    body.vertex_groups.new(name=name)
for i, vertex in enumerate(body.data.vertices):
    world = body.matrix_world @ vertex.co
    near = min(BONES, key=lambda b: sum((world[k] - b[1][k]) ** 2 for k in range(3)))
    body.vertex_groups[near[0]].add([i], 1.0, "REPLACE")

bpy.ops.export_scene.gltf(filepath=sys.argv[-1], export_format="GLB", export_skins=True)
"""


@pytest.mark.dcc
@pytest.mark.skipif(not Path(BLENDER).exists(), reason="needs Blender on this machine")
def test_a_real_blender_export_reads_and_maps(tmp_path: Path) -> None:
    """The claim that matters: a file written by something that is not this repo.

    Every other test here reads bytes this module packed, which only proves the
    reader agrees with itself. Blender 5.2's exporter is a second opinion: its
    own accessor layout, the cube's 8 corners split into 24 vertices at the UV
    seams, a skeleton root under an armature node that is NOT the scene root,
    and Z-up converted to glTF's +Y up. All of that has to come back out, and
    the Mixamo names have to resolve to all nine seamkiln joints.
    """
    script = tmp_path / "export_rig.py"
    script.write_text(_EXPORT_RIG, encoding="utf-8")
    glb = tmp_path / "blender_rig.glb"
    proc = subprocess.run(
        [BLENDER, "--background", "--factory-startup", "--python", str(script), "--", str(glb)],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert glb.is_file(), (proc.stdout + proc.stderr)[-2000:]

    body = read_skinned_gltf(glb)
    assert len(body.joints) == 10
    assert body.joints[0].name == "mixamorig:Hips"
    assert body.joints[0].parent is None
    assert len(body.vertices) == 24  # UV seams split the box's 8 corners
    assert len(body.faces) == 12
    # Blender is Z-up and glTF is Y-up: the box sits at 0.9 +- 0.2 m in Y.
    assert body.vertices[:, 1].min() == pytest.approx(0.7, abs=1e-6)
    assert body.vertices[:, 1].max() == pytest.approx(1.1, abs=1e-6)
    assert np.abs(body.weights.sum(axis=1) - 1.0).max() < 1e-6

    mapping = map_joint_names(body.joint_names)
    assert set(mapping.by_joint) == set(JOINTS)
    assert mapping.by_joint["shoulder_l"] == "mixamorig:LeftArm"
    assert mapping.unused == ("mixamorig:Hips",)


# --------------------------------------------------------------------------
# the name table


def test_every_seamkiln_joint_is_mapped_or_declared_unmappable() -> None:
    assert UNCOVERED == (), UNCOVERED
    for joint in JOINTS:
        assert (joint in ALIASES) != (joint in UNMAPPABLE), joint
    assert set(ALIASES) | set(UNMAPPABLE) == set(JOINTS)


def test_a_mixamo_name_set_resolves_completely() -> None:
    names = [name for name, _p, _t in MIXAMO_BONES[1:]]
    mapping = map_joint_names(names)
    assert set(mapping.by_joint) == set(JOINTS)
    assert mapping.by_joint["hip_l"] == "mixamorig:LeftUpLeg"
    assert mapping.by_joint["knee_l"] == "mixamorig:LeftLeg"
    assert mapping.by_joint["shoulder_l"] == "mixamorig:LeftArm"
    assert mapping.by_joint["elbow_r"] == "mixamorig:RightForeArm"
    assert mapping.by_joint["trunk_lean"] == "mixamorig:Spine"
    # The clavicles are found, recognised, and deliberately left out.
    assert set(mapping.unused) == {
        "mixamorig:Hips",
        "mixamorig:LeftShoulder",
        "mixamorig:RightShoulder",
    }


@pytest.mark.parametrize(
    "spelling",
    [
        "mixamorig:LeftUpLeg",
        "LeftUpLeg",
        "Left_Up_Leg",
        "left up leg",
        "LEFTUPLEG",
        "mixamorigLeftUpLeg",
    ],
)
def test_prefix_case_and_separator_variants_fold_together(spelling: str) -> None:
    assert normalise(spelling) == "leftupleg"


def test_other_conventions_resolve() -> None:
    unreal = [
        "thigh_l",
        "thigh_r",
        "calf_l",
        "calf_r",
        "upperarm_l",
        "upperarm_r",
        "lowerarm_l",
        "lowerarm_r",
        "spine_01",
        "pelvis",
        "hand_l",
    ]
    assert set(map_joint_names(unreal).by_joint) == set(JOINTS)
    rigify = [
        "thigh.L",
        "thigh.R",
        "shin.L",
        "shin.R",
        "upper_arm.L",
        "upper_arm.R",
        "forearm.L",
        "forearm.R",
        "spine",
        "DEF-hand.L",
    ]
    assert set(map_joint_names(rigify).by_joint) == set(JOINTS)


def test_the_clavicle_is_never_taken_for_the_shoulder() -> None:
    """The mistake this table exists to prevent, pinned.

    Mixamo's `LeftShoulder` is the collarbone; the joint that swings the arm
    is `LeftArm`. A rig carrying only the collarbone cannot drive `shoulder_l`
    and must say so, not silently pivot the sleeve from the neck.
    """
    names = [name for name, _p, _t in MIXAMO_BONES[1:] if "Arm" not in name]
    with pytest.raises(RigNameError) as excinfo:
        map_joint_names(names)
    message = str(excinfo.value)
    assert "shoulder_l" in message and "shoulder_r" in message
    assert "elbow_l" in message
    assert "LeftShoulder (the CLAVICLE" in message
    assert "LeftArm" in message  # the name it wants
    assert "overrides=" in message  # and the exact fix


def test_a_missing_joint_refuses_naming_that_joint() -> None:
    names = [name for name, _p, _t in MIXAMO_BONES[1:] if name != "mixamorig:LeftForeArm"]
    with pytest.raises(RigNameError) as excinfo:
        map_joint_names(names)
    message = str(excinfo.value)
    assert "cannot drive 1 of seamkiln's 9 joints: elbow_l" in message
    assert "LeftForeArm" in message


def test_overrides_carry_a_convention_nobody_has_met() -> None:
    names = [name for name, _p, _t in MIXAMO_BONES[1:] if name != "mixamorig:LeftForeArm"]
    names.append("bras_gauche_avant")
    mapping = map_joint_names(names, overrides={"elbow_l": "bras_gauche_avant"})
    assert mapping.by_joint["elbow_l"] == "bras_gauche_avant"
    assert set(mapping.by_joint) == set(JOINTS)
    assert "mapped by override" in " ".join(mapping.notes)


def test_an_override_typo_refuses_rather_than_leaving_a_joint_unmapped() -> None:
    names = [name for name, _p, _t in MIXAMO_BONES[1:]]
    with pytest.raises(RigNameError, match="does not have"):
        map_joint_names(names, overrides={"elbow_l": "bras_gauche_avnat"})
    with pytest.raises(RigNameError, match="not seamkiln"):
        map_joint_names(names, overrides={"ellbow_l": "mixamorig:LeftForeArm"})


def test_duplicate_bone_names_refuse() -> None:
    names = [name for name, _p, _t in MIXAMO_BONES[1:]] + ["mixamorig:LeftArm"]
    with pytest.raises(RigNameError, match="more than one bone"):
        map_joint_names(names)


RIGIFY_CONTROLS = [
    "spine",
    "thigh.L",
    "shin.L",
    "thigh.R",
    "shin.R",
    "upper_arm.L",
    "forearm.L",
    "upper_arm.R",
    "forearm.R",
]
RIGIFY_DEFORM = [f"DEF-{bone}" for bone in RIGIFY_CONTROLS[1:]]


def test_a_rig_carrying_both_control_and_deform_bones_refuses_either_way_round() -> None:
    """Measured 2026-09-04, and the reason this refusal exists: Blender's glTF
    exporter writes ALL of an armature's bones as joints unless 'deform bones
    only' is ticked, so a Rigify character's skin lists `thigh.L` AND
    `DEF-thigh.L`. `normalise` strips DEF-/ORG-/MCH-, so both fold to `thighl`
    and taking the first hit made the answer depend on the order the file
    listed them - the same rig mapped hip_l to `thigh.L` one way round and
    `DEF-thigh.L` the other. In a baked export the control bone owns no
    vertices, so that leg silently never moves, which is precisely the failure
    this module claims to make impossible. Both orders must refuse, and the
    message must name the deform bone as the fix.
    """
    forwards = [*RIGIFY_CONTROLS, *RIGIFY_DEFORM]
    backwards = [*RIGIFY_DEFORM, *RIGIFY_CONTROLS]
    for names in (forwards, backwards):
        with pytest.raises(RigNameError) as excinfo:
            map_joint_names(names)
        message = str(excinfo.value)
        assert "MORE THAN ONE bone" in message
        assert "thigh.L" in message and "DEF-thigh.L" in message
        assert "overrides=" in message
    # and the override the message points at is the way through
    mapping = map_joint_names(
        forwards,
        overrides={
            "hip_l": "DEF-thigh.L",
            "hip_r": "DEF-thigh.R",
            "knee_l": "DEF-shin.L",
            "knee_r": "DEF-shin.R",
            "shoulder_l": "DEF-upper_arm.L",
            "shoulder_r": "DEF-upper_arm.R",
            "elbow_l": "DEF-forearm.L",
            "elbow_r": "DEF-forearm.R",
        },
    )
    assert mapping.by_joint["hip_l"] == "DEF-thigh.L"
    assert mapping.by_joint["trunk_lean"] == "spine"


def test_a_deform_only_rigify_export_still_maps_without_an_override() -> None:
    """The refusal above must not punish the correct export: with the deform
    bones alone there is exactly one candidate per joint and it resolves."""
    mapping = map_joint_names(["spine", *RIGIFY_DEFORM])
    assert mapping.by_joint["hip_l"] == "DEF-thigh.L"
    assert len(mapping.by_joint) == 9


# --------------------------------------------------------------------------
# reader and table together - the end the whole task exists for


def test_a_read_character_maps_onto_seamkilns_joints(tmp_path: Path) -> None:
    body = read_skinned_gltf(
        write_glb(tmp_path / "char.glb", bones=MIXAMO_BONES, skin_bones=MIXAMO_SKIN)
    )
    mapping = map_joint_names(body.joint_names)
    assert isinstance(mapping, JointMap)
    assert set(mapping.by_joint) == set(JOINTS)
    index = mapping.index_map(body.joint_names)
    assert set(index) == set(JOINTS)
    for joint, i in index.items():
        assert body.joints[i].name == mapping.by_joint[joint]
    # The left elbow really is below the left shoulder in the hierarchy read
    # from the file - the mapping is not just string agreement.
    elbow, shoulder = index["elbow_l"], index["shoulder_l"]
    assert body.joints[elbow].parent == shoulder
    assert body.joints[shoulder].rest[1, 3] > body.joints[elbow].rest[1, 3]


def test_a_skin_missing_a_needed_joint_refuses_by_name(tmp_path: Path) -> None:
    """The acceptance case: a real file, read fine, that cannot drive a joint."""
    keep = tuple(i for i in MIXAMO_SKIN if MIXAMO_BONES[i][0] != "mixamorig:LeftForeArm")
    body = read_skinned_gltf(
        write_glb(tmp_path / "noelbow.glb", bones=MIXAMO_BONES, skin_bones=keep)
    )
    assert "mixamorig:LeftForeArm" not in body.joint_names
    with pytest.raises(RigNameError) as excinfo:
        map_joint_names(body.joint_names)
    assert "elbow_l" in str(excinfo.value)
