"""glTF 2.0 binary (`.glb`), written and read BY HAND - json, struct, numpy.

WHY by hand. `trimesh` is the only mesh library seamkiln depends on, and
trimesh 5.1 **bakes a glTF scene graph into geometry and ignores `skins`
entirely**: load a rigged body through it and the skeleton is gone, which is
exactly the defect A65 P5b exists to fix (`avatar.custom_avatar` loads with
`trimesh.load(force="mesh")`, so the finest rigged character in the world
walks as a statue). `pygltflib` is not installed and is not going to be: glb
is JSON plus a packed buffer plus a twelve-byte header, and the two hundred
lines below are the whole cost. They buy the other half too - `read_glb` and
`accessor_array` are what will let seamkiln open a STUDIO's rigged file
correctly later, rather than flattening it the way trimesh does.

Four facts of the format that a writer gets wrong once, and only once:

* glTF is **+Y up, +Z forward, metres**, by specification (glTF 2.0 §3.5).
  Nothing here rotates or rescales anything. That is seamkiln Law 17 - a
  self-describing format is left alone - and it was paid for: adding "our
  own" rotation once put a jacket on its face through the floor.
* Matrices are **column-major**: sixteen floats in which elements 12, 13, 14
  are the translation. numpy is row-major, so every matrix leaves through
  `column_major()` and nowhere else.
* Every chunk is padded to a **four-byte boundary** - JSON with spaces
  (0x20), BIN with zeros - and the header's length counts the padding.
* An accessor's `byteOffset` must be a multiple of its component size. One
  accessor per bufferView, each view starting four-byte aligned, makes that
  true by construction and makes `byteLength == count * element size` an
  invariant a test can check.
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

GLB_MAGIC = 0x46546C67  # b"glTF"
GLB_VERSION = 2
CHUNK_JSON = 0x4E4F534A  # b"JSON"
CHUNK_BIN = 0x004E4942  # b"BIN\0"

# A fixed generator string: no version, no timestamp, nothing that would make
# two builds of the same body differ by a byte. Determinism is a feature.
GENERATOR = "seamkiln.rig glb writer"

ARRAY_BUFFER = 34962
ELEMENT_ARRAY_BUFFER = 34963

# glTF componentType -> (numpy dtype, bytes per component)
COMPONENT_TYPES: dict[int, tuple[str, int]] = {
    5120: ("int8", 1),
    5121: ("uint8", 1),
    5122: ("int16", 2),
    5123: ("uint16", 2),
    5125: ("uint32", 4),
    5126: ("float32", 4),
}
TYPE_COUNTS: dict[str, int] = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def column_major(matrix: np.ndarray) -> list[float]:
    """A row-major 4x4 as glTF's sixteen column-major floats.

    The ONLY place in seamkiln where a matrix is transposed for the wire. For
    a pure translation the result is `[1,0,0,0, 0,1,0,0, 0,0,1,0, tx,ty,tz,1]`
    - if translation is not in slots 12..14, this is the function that is
    wrong, not the consumer.
    """
    m = np.asarray(matrix, dtype=np.float64)
    if m.shape != (4, 4):
        raise ValueError(f"expected a 4x4 matrix, got {m.shape}; pass a homogeneous transform.")
    return [float(x) for x in m.T.reshape(16)]


@dataclass(frozen=True, slots=True)
class Skeleton:
    """A joint hierarchy in BIND pose: names, parents, and world positions.

    Parents come before children (`validate` enforces it) so a single forward
    pass composes world transforms. Bind rotations are identity - the pose is
    baked into the mesh - so a joint's world bind transform is a translation
    and its inverse bind matrix is the translation negated.
    """

    names: tuple[str, ...]
    parents: tuple[int, ...]
    positions: np.ndarray  # (J, 3) world-space bind positions, metres

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        j = len(self.names)
        if len(self.parents) != j or self.positions.shape != (j, 3):
            raise ValueError(
                f"skeleton mismatch: {j} names, {len(self.parents)} parents, "
                f"positions {self.positions.shape}; all three must describe {j} joints."
            )
        for i, p in enumerate(self.parents):
            if p >= i:
                raise ValueError(
                    f"joint {self.names[i]!r} (index {i}) has parent index {p}: parents must come "
                    "BEFORE their children so world transforms compose in one forward pass."
                )
            if p < -1:
                raise ValueError(f"joint {self.names[i]!r}: parent index {p} < -1 (-1 means root).")

    @property
    def roots(self) -> tuple[int, ...]:
        return tuple(i for i, p in enumerate(self.parents) if p == -1)

    def local_translations(self) -> np.ndarray:
        """Each joint's translation relative to its parent."""
        local = np.array(self.positions, dtype=np.float64, copy=True)
        for i, p in enumerate(self.parents):
            if p >= 0:
                local[i] = self.positions[i] - self.positions[p]
        return local

    def bind_matrices(self) -> np.ndarray:
        """(J, 4, 4) world bind transforms, row-major."""
        out = np.repeat(np.eye(4)[None, :, :], len(self.names), axis=0)
        out[:, :3, 3] = self.positions
        return out

    def inverse_bind_matrices(self) -> np.ndarray:
        """(J, 4, 4) inverses of the above, row-major."""
        out = np.repeat(np.eye(4)[None, :, :], len(self.names), axis=0)
        out[:, :3, 3] = -self.positions
        return out


@dataclass(frozen=True, slots=True)
class SkinnedPrimitive:
    """One glTF mesh primitive: geometry plus its skin binding."""

    positions: np.ndarray  # (N, 3) float
    normals: np.ndarray  # (N, 3) float, unit length
    indices: np.ndarray  # (M, 3) int, triangles
    joints: np.ndarray  # (N, 4) int, joint indices
    weights: np.ndarray  # (N, 4) float, rows summing to 1

    def validate(self, joint_count: int, *, tolerance: float = 1e-6) -> None:
        """Refuse a bad skin HERE, where the fix is one line, not in a viewer."""
        n = len(self.positions)
        for label, array, shape in (
            ("normals", self.normals, (n, 3)),
            ("joints", self.joints, (n, 4)),
            ("weights", self.weights, (n, 4)),
        ):
            if array.shape != shape:
                raise ValueError(
                    f"{label} is {array.shape}, expected {shape} for {n} vertices; "
                    "every per-vertex array must have one row per position."
                )
        if self.indices.ndim != 2 or self.indices.shape[1] != 3:
            raise ValueError(f"indices must be (M, 3) triangles, got {self.indices.shape}.")
        if len(self.indices) and (int(self.indices.max()) >= n or int(self.indices.min()) < 0):
            raise ValueError(
                f"triangle index out of range for {n} vertices "
                f"(min {int(self.indices.min())}, max {int(self.indices.max())})."
            )
        if joint_count and int(self.joints.max(initial=0)) >= joint_count:
            raise ValueError(
                f"JOINTS_0 references joint {int(self.joints.max())} but the skeleton has "
                f"{joint_count} joints; reindex the weights against the skeleton you are writing."
            )
        if joint_count > 255:
            raise ValueError(
                f"{joint_count} joints will not fit JOINTS_0 as unsigned byte; "
                "switch the accessor to componentType 5123 (unsigned short)."
            )
        sums = self.weights.sum(axis=1)
        worst = float(np.max(np.abs(sums - 1.0))) if n else 0.0
        if worst > tolerance:
            bad = int(np.argmax(np.abs(sums - 1.0)))
            raise ValueError(
                f"skin weights must sum to 1: vertex {bad} sums to {sums[bad]:.9f} "
                f"(worst error {worst:.3g} > {tolerance:g}). Normalise before writing: "
                "w /= w.sum(axis=1, keepdims=True)."
            )
        if np.any(self.weights < 0.0):
            raise ValueError("negative skin weight: clamp to zero before normalising.")


def _pad_to_four(blob: bytearray, filler: int = 0) -> None:
    while len(blob) % 4:
        blob.append(filler)


def write_glb(
    path: str | Path,
    primitive: SkinnedPrimitive,
    skeleton: Skeleton,
    *,
    mesh_name: str = "Body",
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write a skinned `.glb` and return a manifest of what went on the wire.

    The manifest is the honest record of the file's contract - units, up axis,
    counts, chunk sizes - because "it exported fine" is not evidence and a
    body imported at the wrong scale fails silently.
    """
    primitive.validate(len(skeleton.names))
    positions = np.ascontiguousarray(primitive.positions, dtype=np.float32)
    normals = np.ascontiguousarray(primitive.normals, dtype=np.float32)
    indices = np.ascontiguousarray(primitive.indices, dtype=np.uint32).reshape(-1)
    joints = np.ascontiguousarray(primitive.joints, dtype=np.uint8)
    weights = np.ascontiguousarray(primitive.weights, dtype=np.float32)
    ibm = np.ascontiguousarray(
        np.stack([column_major(m) for m in skeleton.inverse_bind_matrices()]), dtype=np.float32
    )

    buffer = bytearray()
    views: list[dict[str, Any]] = []

    def add_view(array: np.ndarray, target: int | None) -> int:
        _pad_to_four(buffer)
        offset = len(buffer)
        buffer.extend(array.tobytes())
        view: dict[str, Any] = {
            "buffer": 0,
            "byteOffset": offset,
            "byteLength": int(array.nbytes),
        }
        if target is not None:
            view["target"] = target
        views.append(view)
        return len(views) - 1

    accessors: list[dict[str, Any]] = []

    def add_accessor(
        array: np.ndarray, component: int, kind: str, target: int | None, *, bounds: bool = False
    ) -> int:
        view = add_view(array, target)
        count = len(array) if array.ndim > 1 else int(array.size // TYPE_COUNTS[kind])
        acc: dict[str, Any] = {
            "bufferView": view,
            "componentType": component,
            "count": count,
            "type": kind,
        }
        if bounds:
            acc["min"] = [float(v) for v in array.min(axis=0)]
            acc["max"] = [float(v) for v in array.max(axis=0)]
        accessors.append(acc)
        return len(accessors) - 1

    acc_index = add_accessor(indices, 5125, "SCALAR", ELEMENT_ARRAY_BUFFER)
    acc_position = add_accessor(positions, 5126, "VEC3", ARRAY_BUFFER, bounds=True)
    acc_normal = add_accessor(normals, 5126, "VEC3", ARRAY_BUFFER)
    acc_joints = add_accessor(joints, 5121, "VEC4", ARRAY_BUFFER)
    acc_weights = add_accessor(weights, 5126, "VEC4", ARRAY_BUFFER)
    acc_ibm = add_accessor(ibm, 5126, "MAT4", None)

    local = skeleton.local_translations()
    children: dict[int, list[int]] = {i: [] for i in range(len(skeleton.names))}
    for i, p in enumerate(skeleton.parents):
        if p >= 0:
            children[p].append(i)
    nodes: list[dict[str, Any]] = []
    for i, name in enumerate(skeleton.names):
        node: dict[str, Any] = {"name": name}
        if not np.allclose(local[i], 0.0):
            node["translation"] = [float(v) for v in local[i]]
        if children[i]:
            node["children"] = children[i]
        nodes.append(node)
    mesh_node = len(nodes)
    nodes.append({"name": mesh_name, "mesh": 0, "skin": 0})

    roots = list(skeleton.roots)
    gltf: dict[str, Any] = {
        "asset": {"version": "2.0", "generator": GENERATOR},
        "scene": 0,
        "scenes": [{"nodes": [*roots, mesh_node]}],
        "nodes": nodes,
        "meshes": [
            {
                "name": mesh_name,
                "primitives": [
                    {
                        "attributes": {
                            "POSITION": acc_position,
                            "NORMAL": acc_normal,
                            "JOINTS_0": acc_joints,
                            "WEIGHTS_0": acc_weights,
                        },
                        "indices": acc_index,
                        "mode": 4,
                    }
                ],
            }
        ],
        "skins": [
            {
                "name": f"{mesh_name}Skin",
                "inverseBindMatrices": acc_ibm,
                "skeleton": roots[0],
                "joints": list(range(len(skeleton.names))),
            }
        ],
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(buffer)}],
    }
    if extras:
        gltf["asset"]["extras"] = extras

    json_chunk = bytearray(json.dumps(gltf, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    _pad_to_four(json_chunk, 0x20)
    bin_chunk = bytearray(buffer)
    _pad_to_four(bin_chunk, 0x00)

    total = 12 + 8 + len(json_chunk) + 8 + len(bin_chunk)
    out = bytearray()
    out.extend(struct.pack("<III", GLB_MAGIC, GLB_VERSION, total))
    out.extend(struct.pack("<II", len(json_chunk), CHUNK_JSON))
    out.extend(json_chunk)
    out.extend(struct.pack("<II", len(bin_chunk), CHUNK_BIN))
    out.extend(bin_chunk)

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(bytes(out))
    return {
        "path": str(target),
        "bytes": len(out),
        "json_chunk_bytes": len(json_chunk),
        "bin_chunk_bytes": len(bin_chunk),
        "vertices": len(positions),
        "triangles": int(len(indices) // 3),
        "joints": len(skeleton.names),
        "joint_names": list(skeleton.names),
        "units": "m",
        "up_axis": "+Y",
        "forward_axis": "+Z",
        "convention": "glTF 2.0 is +Y up, +Z forward, metres by specification; nothing rotated",
        "matrix_order": "column-major (translation in elements 12,13,14)",
        "bounds_min": accessors[acc_position]["min"],
        "bounds_max": accessors[acc_position]["max"],
    }


def read_glb(path: str | Path) -> tuple[dict[str, Any], bytes]:
    """Parse a `.glb` into (glTF JSON, BIN chunk). The half trimesh will not do."""
    raw = Path(path).read_bytes()
    if len(raw) < 12:
        raise ValueError(f"{path}: {len(raw)} bytes is shorter than a glb header (12).")
    magic, version, length = struct.unpack_from("<III", raw, 0)
    if magic != GLB_MAGIC:
        raise ValueError(f"{path} is not a glb: magic {magic:#x}, expected {GLB_MAGIC:#x}.")
    if version != GLB_VERSION:
        raise ValueError(f"{path} is glTF version {version}; this reader speaks 2.")
    if length != len(raw):
        raise ValueError(f"{path}: header says {length} bytes, file is {len(raw)}.")
    offset, gltf, blob = 12, None, b""
    while offset < length:
        chunk_len, chunk_type = struct.unpack_from("<II", raw, offset)
        offset += 8
        if chunk_len % 4:
            raise ValueError(
                f"{path}: chunk at {offset - 8} has length {chunk_len}, which is not a multiple "
                "of 4; every glb chunk is padded to a four-byte boundary."
            )
        data = raw[offset : offset + chunk_len]
        offset += chunk_len
        if chunk_type == CHUNK_JSON:
            gltf = json.loads(data.decode("utf-8"))
        elif chunk_type == CHUNK_BIN:
            blob = bytes(data)
    if gltf is None:
        raise ValueError(f"{path}: no JSON chunk.")
    return gltf, blob


def accessor_array(gltf: dict[str, Any], blob: bytes, index: int) -> np.ndarray:
    """One accessor as an (count, components) numpy array, strides honoured."""
    acc = gltf["accessors"][index]
    if "sparse" in acc:
        raise NotImplementedError(
            f"accessor {index} is sparse; densify it before reading (seamkiln writes dense "
            "accessors only, so this can only come from another exporter)."
        )
    dtype, size = COMPONENT_TYPES[acc["componentType"]]
    ncomp = TYPE_COUNTS[acc["type"]]
    count = int(acc["count"])
    element = size * ncomp
    view = gltf["bufferViews"][acc["bufferView"]]
    start = int(view.get("byteOffset", 0)) + int(acc.get("byteOffset", 0))
    stride = int(view.get("byteStride", element)) or element
    if stride == element:
        raw = np.frombuffer(blob, dtype=np.uint8, offset=start, count=count * element)
    else:
        span = (count - 1) * stride + element
        packed = np.frombuffer(blob, dtype=np.uint8, offset=start, count=span)
        take = (np.arange(count) * stride)[:, None] + np.arange(element)[None, :]
        raw = np.ascontiguousarray(packed[take])
    return raw.view(dtype).reshape(count, ncomp)


__all__ = [
    "COMPONENT_TYPES",
    "GENERATOR",
    "TYPE_COUNTS",
    "Skeleton",
    "SkinnedPrimitive",
    "accessor_array",
    "column_major",
    "read_glb",
    "write_glb",
]
