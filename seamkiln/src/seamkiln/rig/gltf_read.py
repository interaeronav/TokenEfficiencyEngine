"""Reading a SKINNED glTF, skeleton and all - by hand, on purpose.

`avatar.custom_avatar` loads a body with `trimesh.load(path, force="mesh")`.
That call flattens a scene graph to ONE mesh and throws the skeleton away:
trimesh 5.1.0 does not read glTF skins at all, it bakes the node transforms
and keeps triangles. Downstream, a body with no joints falls back to a rigid
walk, so the finest rigged character in the world moves as a statue and every
number the gait work bought - the pelvis rising ~50 mm in a walk and ~140 mm
in a run, counter-phase arm swing, trunk lean - is lost on any body a studio
brings. This module exists to stop that.

It is written against `json` + `struct` + `numpy`, all stdlib or already a
dependency. NO new package: `pygltflib` is not installed and must not be
added, and writing the parser here is not a workaround but the only way to
read a real studio file correctly later - the awkward parts of glTF are
exactly the parts a convenience wrapper hides.

What it handles, because real exporters emit all of it:

  * `.glb` containers and `.gltf` + external `.bin` (and `data:` URIs)
  * `JOINTS_0` as unsigned byte OR unsigned short
  * `WEIGHTS_0` as float, or as normalised unsigned byte / short
  * `byteStride` on interleaved buffer views
  * several primitives in one mesh, concatenated with faces re-based
  * a skin whose skeleton root is not the scene root, and joints separated
    by nodes that are not themselves joints (their transforms are composed
    into the joint's local matrix rather than dropped)

What it does NOT handle REFUSES BY NAME - sparse accessors, Draco, mesh
quantization, more than four influences per vertex, a file with no skin at
all. A silent rigless return is the precise failure this module was written
to remove, so there is no path through here that produces one.

Conventions on the way out: matrices are 4x4 ROW-major (`M @ v` with `v` a
column), which is numpy's natural reading and the opposite of the column-major
order glTF stores them in; positions are float64 metres in glTF's own space
(+Y up, right-handed); joint indices index `SkinnedBody.joints`, in the file's
own `skin.joints` order, so `JOINTS_0` needs no remapping.
"""

from __future__ import annotations

import base64
import json
import struct
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

import numpy as np


class RigReadError(ValueError):
    """A glTF this reader will not pretend to understand.

    Every message names what was found AND the exact fix, because the caller
    is usually a model that cannot open the file to look.
    """


# glTF component types -> a little-endian numpy dtype and the divisor that
# turns a normalised integer back into a float (spec: 5.24, accessor.normalized).
_COMPONENT: dict[int, tuple[str, float | None]] = {
    5120: ("<i1", 127.0),
    5121: ("<u1", 255.0),
    5122: ("<i2", 32767.0),
    5123: ("<u2", 65535.0),
    5125: ("<u4", None),
    5126: ("<f4", None),
}
_COMPONENT_NAME = {
    5120: "byte",
    5121: "unsigned byte",
    5122: "short",
    5123: "unsigned short",
    5125: "unsigned int",
    5126: "float",
}
_TYPE_COUNT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}

_GLB_MAGIC = 0x46546C67
_CHUNK_JSON = 0x4E4F534A
_CHUNK_BIN = 0x004E4942

# The only extensions we can honour is none of them: anything a file REQUIRES
# changes how its buffers decode, so requiring one we do not implement is a
# refusal, never a warning.
_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class Joint:
    """One bone of the skeleton, in the file's own `skin.joints` order."""

    name: str
    node: int  # the glTF node index, kept so a refusal can name it
    parent: int | None  # index into `SkinnedBody.joints`, None for a root
    local: np.ndarray  # 4x4, relative to `parent` (or to the scene, for a root)
    rest: np.ndarray  # 4x4, accumulated from the scene root
    inverse_bind: np.ndarray  # 4x4, the file's inverseBindMatrices entry


@dataclass(frozen=True, slots=True)
class SkinnedBody:
    """A mesh that still knows which bone moves which vertex."""

    name: str
    vertices: np.ndarray  # (V, 3) float64
    faces: np.ndarray  # (F, 3) int32
    normals: np.ndarray  # (V, 3) float64, unit length
    joint_indices: np.ndarray  # (V, 4) int32, into `joints`
    weights: np.ndarray  # (V, 4) float64, as the file stored them
    joints: tuple[Joint, ...]
    source: str
    notes: tuple[str, ...] = ()

    @property
    def joint_names(self) -> tuple[str, ...]:
        return tuple(j.name for j in self.joints)

    def joint_index(self, name: str) -> int:
        for i, joint in enumerate(self.joints):
            if joint.name == name:
                return i
        raise RigReadError(
            f"no joint named {name!r} in {self.source}; joints: {', '.join(self.joint_names)}."
        )

    def summary(self) -> str:
        """One line, because a scene dump is the other failure this repo fights."""
        return (
            f"{self.name}: {len(self.vertices)} verts, {len(self.faces)} faces, "
            f"{len(self.joints)} joints, roots "
            f"{', '.join(j.name for j in self.joints if j.parent is None)}"
        )


# --------------------------------------------------------------------------
# container


def _load_glb(raw: bytes, path: Path) -> tuple[dict, dict[int, bytes]]:
    if len(raw) < 12:
        raise RigReadError(f"{path.name} is {len(raw)} bytes: too short to be a GLB.")
    magic, version, length = struct.unpack_from("<III", raw, 0)
    if magic != _GLB_MAGIC:
        raise RigReadError(f"{path.name} does not start with the glTF magic 'glTF'.")
    if version != 2:
        raise RigReadError(
            f"{path.name} is glTF binary version {version}; this reader implements "
            "version 2. Fix: re-export as glTF 2.0 (every current exporter does)."
        )
    if length > len(raw):
        raise RigReadError(
            f"{path.name} declares {length} bytes but is {len(raw)}: the file is truncated."
        )
    doc: dict | None = None
    binary: bytes | None = None
    offset = 12
    while offset + 8 <= length:
        chunk_len, chunk_type = struct.unpack_from("<II", raw, offset)
        offset += 8
        payload = raw[offset : offset + chunk_len]
        if len(payload) < chunk_len:
            raise RigReadError(f"{path.name}: a chunk claims {chunk_len} bytes and is truncated.")
        offset += chunk_len
        if chunk_type == _CHUNK_JSON and doc is None:
            doc = json.loads(payload.decode("utf-8"))
        elif chunk_type == _CHUNK_BIN and binary is None:
            binary = bytes(payload)
        # Unknown chunk types are ignored, which the spec requires.
    if doc is None:
        raise RigReadError(f"{path.name} carries no JSON chunk; it is not a readable GLB.")
    buffers: dict[int, bytes] = {}
    if binary is not None:
        buffers[0] = binary
    return doc, buffers


def _resolve_buffers(doc: dict, path: Path, glb_buffers: dict[int, bytes]) -> list[bytes]:
    out: list[bytes] = []
    for i, buf in enumerate(doc.get("buffers", [])):
        if i in glb_buffers:
            out.append(glb_buffers[i])
            continue
        uri = buf.get("uri")
        if uri is None:
            raise RigReadError(
                f"buffer {i} of {path.name} has no uri and no binary chunk to come from. "
                "Fix: export a self-contained .glb, or ship the .bin beside the .gltf."
            )
        if uri.startswith("data:"):
            _, _, payload = uri.partition(",")
            out.append(base64.b64decode(payload))
            continue
        side = (path.parent / unquote(uri)).resolve()
        if not side.is_file():
            raise RigReadError(
                f"{path.name} references buffer file {uri!r}, which is not next to it "
                f"(looked in {path.parent}). Fix: copy the .bin beside the .gltf, or "
                "re-export as a self-contained .glb."
            )
        out.append(side.read_bytes())
    return out


def _read_document(path: Path) -> tuple[dict, list[bytes]]:
    raw = path.read_bytes()
    if raw[:4] == b"glTF":
        doc, glb_buffers = _load_glb(raw, path)
    else:
        try:
            doc = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RigReadError(
                f"{path.name} is neither a GLB (no 'glTF' magic) nor readable JSON: {exc}."
            ) from exc
        glb_buffers = {}
    asset_version = str(doc.get("asset", {}).get("version", "?"))
    if not asset_version.startswith("2"):
        raise RigReadError(
            f"{path.name} declares glTF asset version {asset_version}; this reader "
            "implements 2.x. Fix: re-export as glTF 2.0."
        )
    required = [e for e in doc.get("extensionsRequired", []) if e not in _SUPPORTED_EXTENSIONS]
    if required:
        hint = ""
        if any("draco" in e.lower() for e in required):
            hint = " Fix: re-export with Draco compression OFF."
        elif any("quantization" in e.lower() for e in required):
            hint = " Fix: re-export with mesh quantization OFF."
        raise RigReadError(
            f"{path.name} requires extension(s) {', '.join(required)}, which this reader "
            f"does not implement; its buffers cannot be decoded without them.{hint}"
        )
    return doc, _resolve_buffers(doc, path, glb_buffers)


# --------------------------------------------------------------------------
# accessors


def _read_accessor(doc: dict, buffers: list[bytes], index: int, *, used_for: str) -> np.ndarray:
    accessors = doc.get("accessors", [])
    if not 0 <= index < len(accessors):
        raise RigReadError(f"{used_for} points at accessor {index}, which does not exist.")
    acc = accessors[index]
    if "sparse" in acc:
        raise RigReadError(
            f"accessor {index} ({used_for}) is SPARSE; this reader does not implement "
            "sparse accessors and will not guess the dense values. Fix: re-export "
            "without sparse accessors (Blender's exporter does not emit them), or "
            "run the file through gltf-transform."
        )
    kind = acc.get("type")
    if kind not in _TYPE_COUNT:
        raise RigReadError(f"accessor {index} ({used_for}) has unknown type {kind!r}.")
    comp = acc.get("componentType")
    if comp not in _COMPONENT:
        raise RigReadError(f"accessor {index} ({used_for}) has unknown componentType {comp!r}.")
    dtype_str, _ = _COMPONENT[comp]
    dtype = np.dtype(dtype_str)
    ncomp = _TYPE_COUNT[kind]
    count = int(acc.get("count", 0))
    if "bufferView" not in acc:
        # The spec says such an accessor reads as zeros. Honest, and rare.
        return np.zeros((count, ncomp), dtype=dtype)
    views = doc.get("bufferViews", [])
    bv_index = int(acc["bufferView"])
    if not 0 <= bv_index < len(views):
        raise RigReadError(f"accessor {index} ({used_for}) points at missing bufferView.")
    view = views[bv_index]
    buf_index = int(view.get("buffer", 0))
    if not 0 <= buf_index < len(buffers):
        raise RigReadError(f"bufferView {bv_index} ({used_for}) points at missing buffer.")
    data = buffers[buf_index]
    elem = ncomp * dtype.itemsize
    stride = int(view.get("byteStride") or elem)
    base = int(view.get("byteOffset", 0)) + int(acc.get("byteOffset", 0))
    need = base + (count - 1) * stride + elem if count else base
    if need > len(data):
        raise RigReadError(
            f"accessor {index} ({used_for}) needs {need} bytes of buffer {buf_index}, "
            f"which holds {len(data)}: the file is truncated."
        )
    if stride == elem:
        flat = np.frombuffer(data, dtype=dtype, count=count * ncomp, offset=base)
        return flat.reshape(count, ncomp).copy()
    # Interleaved: gather each element's bytes, then reinterpret. Doing it in
    # one fancy-index keeps a 100k-vertex body a single numpy pass.
    raw = np.frombuffer(data, dtype=np.uint8)
    rows = base + np.arange(count, dtype=np.int64)[:, None] * stride
    picks = rows + np.arange(elem, dtype=np.int64)[None, :]
    gathered = np.ascontiguousarray(raw[picks])
    return gathered.view(dtype).reshape(count, ncomp)


def _as_float(values: np.ndarray, *, normalized: bool, comp: int) -> np.ndarray:
    out = values.astype(np.float64)
    if normalized:
        divisor = _COMPONENT[comp][1]
        if divisor is None:
            raise RigReadError(
                f"a {_COMPONENT_NAME[comp]} accessor is marked normalized, which the "
                "spec does not allow for that component type."
            )
        out = np.maximum(out / divisor, -1.0)
    return out


# --------------------------------------------------------------------------
# node transforms


def _quat_matrix(q: np.ndarray) -> np.ndarray:
    x, y, z, w = (float(v) for v in q)  # glTF stores xyzw
    m = np.eye(4)
    m[0, 0] = 1 - 2 * (y * y + z * z)
    m[0, 1] = 2 * (x * y - z * w)
    m[0, 2] = 2 * (x * z + y * w)
    m[1, 0] = 2 * (x * y + z * w)
    m[1, 1] = 1 - 2 * (x * x + z * z)
    m[1, 2] = 2 * (y * z - x * w)
    m[2, 0] = 2 * (x * z - y * w)
    m[2, 1] = 2 * (y * z + x * w)
    m[2, 2] = 1 - 2 * (x * x + y * y)
    return m


def _node_matrix(node: dict) -> np.ndarray:
    """A node's local transform, row-major.

    glTF stores `matrix` in COLUMN-major order, so it is transposed on the way
    in; getting that backwards mirrors a character and looks like a rig bug.
    """
    if "matrix" in node:
        return np.asarray(node["matrix"], dtype=np.float64).reshape(4, 4).T.copy()
    out = _quat_matrix(np.asarray(node.get("rotation", (0.0, 0.0, 0.0, 1.0)), dtype=np.float64))
    scale = np.asarray(node.get("scale", (1.0, 1.0, 1.0)), dtype=np.float64)
    out[:3, :3] = out[:3, :3] * scale[None, :]
    out[:3, 3] = np.asarray(node.get("translation", (0.0, 0.0, 0.0)), dtype=np.float64)
    return out


def _parent_map(nodes: list[dict]) -> list[int | None]:
    parents: list[int | None] = [None] * len(nodes)
    for i, node in enumerate(nodes):
        for child in node.get("children", []):
            child = int(child)
            if not 0 <= child < len(nodes):
                raise RigReadError(f"node {i} lists child {child}, which does not exist.")
            if parents[child] is not None:
                raise RigReadError(
                    f"node {child} is a child of both node {parents[child]} and node {i}; "
                    "a glTF node graph must be a forest."
                )
            parents[child] = i
    return parents


def _world_matrices(nodes: list[dict], parents: list[int | None]) -> list[np.ndarray]:
    local = [_node_matrix(n) for n in nodes]
    world: list[np.ndarray | None] = [None] * len(nodes)

    def resolve(i: int, seen: frozenset[int]) -> np.ndarray:
        cached = world[i]
        if cached is not None:
            return cached
        if i in seen:
            raise RigReadError(f"node {i} is its own ancestor; the node graph has a cycle.")
        parent = parents[i]
        out = local[i] if parent is None else resolve(parent, seen | {i}) @ local[i]
        world[i] = out
        return out

    return [resolve(i, frozenset()) for i in range(len(nodes))]


# --------------------------------------------------------------------------
# the read


def _skinned_nodes(doc: dict) -> list[int]:
    return [i for i, node in enumerate(doc.get("nodes", [])) if "skin" in node and "mesh" in node]


def _node_label(nodes: list[dict], index: int) -> str:
    return str(nodes[index].get("name") or f"node{index}")


def _primitive_attributes(prim: dict, index: int, path: Path) -> dict:
    attrs = prim.get("attributes", {})
    mode = int(prim.get("mode", 4))
    if mode != 4:
        raise RigReadError(
            f"primitive {index} of {path.name} uses mode {mode}; only TRIANGLES (4) is "
            "read here. Fix: triangulate on export."
        )
    if "POSITION" not in attrs:
        raise RigReadError(f"primitive {index} of {path.name} has no POSITION attribute.")
    if "JOINTS_1" in attrs or "WEIGHTS_1" in attrs:
        raise RigReadError(
            f"primitive {index} of {path.name} carries JOINTS_1/WEIGHTS_1: more than four "
            "bone influences per vertex. This reader keeps four. Fix: limit the export to "
            "4 influences per vertex (every exporter has that option), which is also what "
            "every real-time engine does."
        )
    for name in ("JOINTS_0", "WEIGHTS_0"):
        if name not in attrs:
            raise RigReadError(
                f"primitive {index} of {path.name} is on a skinned node but has no {name}: "
                "its vertices are bound to no bone, so the body would move as one rigid "
                "piece. Fix: export the mesh with its armature modifier / skinning."
            )
    return attrs


def _face_normals(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """Area-weighted vertex normals, for a file that carried none."""
    normals = np.zeros_like(vertices)
    tri = vertices[faces]
    cross = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    for k in range(3):
        np.add.at(normals, faces[:, k], cross)
    length = np.linalg.norm(normals, axis=1)
    length[length == 0.0] = 1.0
    return normals / length[:, None]


def read_skinned_gltf(path: str | Path, *, node: str | None = None) -> SkinnedBody:
    """Read a skinned `.glb` / `.gltf`, keeping the skeleton.

    `node` picks the skinned node by name when a file has more than one; with
    one skinned node it is unnecessary. Refuses rather than returning a body
    with no rig - see this module's docstring for why that matters.
    """
    path = Path(path)
    if not path.is_file():
        raise RigReadError(f"{path} is not a file.")
    doc, buffers = _read_document(path)
    nodes = list(doc.get("nodes", []))
    skins = list(doc.get("skins", []))
    meshes = list(doc.get("meshes", []))
    notes: list[str] = []

    candidates = _skinned_nodes(doc)
    if not candidates:
        raise RigReadError(
            f"{path.name} contains no skinned node: {len(meshes)} mesh(es), {len(nodes)} "
            f"node(s), {len(skins)} skin(s). A body with no skeleton walks as a statue, so "
            "this is a refusal and not a rigless mesh. Fix: export the character WITH its "
            "armature (Blender: include the Armature object and tick 'Skinning'), or use "
            "`avatar.custom_avatar` if you really do want an unrigged body."
        )
    if node is not None:
        named = [i for i in candidates if _node_label(nodes, i) == node]
        if not named:
            raise RigReadError(
                f"{path.name} has no skinned node named {node!r}; skinned nodes: "
                f"{', '.join(_node_label(nodes, i) for i in candidates)}."
            )
        chosen = named[0]
    elif len(candidates) > 1:
        raise RigReadError(
            f"{path.name} has {len(candidates)} skinned nodes "
            f"({', '.join(_node_label(nodes, i) for i in candidates)}); this reader returns "
            "one body. Fix: pass node='<one of those names>'."
        )
    else:
        chosen = candidates[0]

    skin_index = int(nodes[chosen]["skin"])
    if not 0 <= skin_index < len(skins):
        raise RigReadError(f"node {chosen} of {path.name} points at missing skin {skin_index}.")
    skin = skins[skin_index]
    joint_nodes = [int(j) for j in skin.get("joints", [])]
    if not joint_nodes:
        raise RigReadError(f"skin {skin_index} of {path.name} lists no joints.")

    parents = _parent_map(nodes)
    world = _world_matrices(nodes, parents)

    # A joint's parent is the NEAREST ancestor that is also a joint; the
    # transforms of any plain nodes in between are composed into the local
    # matrix rather than dropped, which is what makes a skeleton root that
    # is not the scene root read correctly.
    position = {n: i for i, n in enumerate(joint_nodes)}
    if len(position) != len(joint_nodes):
        raise RigReadError(f"skin {skin_index} of {path.name} lists the same joint twice.")
    joint_parents: list[int | None] = []
    for n in joint_nodes:
        walk = parents[n]
        while walk is not None and walk not in position:
            walk = parents[walk]
        joint_parents.append(None if walk is None else position[walk])

    ibm_index = skin.get("inverseBindMatrices")
    if ibm_index is None:
        ibms = np.tile(np.eye(4), (len(joint_nodes), 1, 1))
        notes.append("skin carried no inverseBindMatrices; identity assumed (the spec's default)")
    else:
        flat = _read_accessor(doc, buffers, int(ibm_index), used_for="inverseBindMatrices")
        if flat.shape != (len(joint_nodes), 16):
            raise RigReadError(
                f"inverseBindMatrices of {path.name} is {flat.shape[0]}x{flat.shape[1]}, "
                f"not {len(joint_nodes)}x16 for {len(joint_nodes)} joints."
            )
        ibms = flat.astype(np.float64).reshape(-1, 4, 4).transpose(0, 2, 1)

    joints: list[Joint] = []
    for i, n in enumerate(joint_nodes):
        parent = joint_parents[i]
        rest = world[n]
        local = rest if parent is None else np.linalg.inv(world[joint_nodes[parent]]) @ rest
        joints.append(
            Joint(
                name=_node_label(nodes, n),
                node=n,
                parent=parent,
                local=_frozen(local),
                rest=_frozen(rest.copy()),
                inverse_bind=_frozen(ibms[i].copy()),
            )
        )

    mesh_index = int(nodes[chosen]["mesh"])
    if not 0 <= mesh_index < len(meshes):
        raise RigReadError(f"node {chosen} of {path.name} points at missing mesh {mesh_index}.")
    mesh = meshes[mesh_index]

    positions: list[np.ndarray] = []
    normal_blocks: list[np.ndarray] = []
    face_blocks: list[np.ndarray] = []
    index_blocks: list[np.ndarray] = []
    weight_blocks: list[np.ndarray] = []
    offset = 0
    computed_normals = False
    for p, prim in enumerate(mesh.get("primitives", [])):
        attrs = _primitive_attributes(prim, p, path)
        pos_acc = int(attrs["POSITION"])
        pos = _read_accessor(doc, buffers, pos_acc, used_for=f"primitive {p} POSITION")
        pos_comp = int(doc["accessors"][pos_acc].get("componentType", 5126))
        if pos_comp != 5126:
            raise RigReadError(
                f"primitive {p} of {path.name} stores POSITION as {_COMPONENT_NAME[pos_comp]}, "
                "which means the mesh is quantized. Fix: re-export with quantization off."
            )
        pos = pos.astype(np.float64)
        n_vert = len(pos)

        if "indices" in prim:
            idx = _read_accessor(
                doc, buffers, int(prim["indices"]), used_for=f"primitive {p} indices"
            ).reshape(-1)
        else:
            idx = np.arange(n_vert, dtype=np.int64)
        if len(idx) % 3:
            raise RigReadError(
                f"primitive {p} of {path.name} has {len(idx)} indices, not a multiple of 3."
            )
        faces = idx.astype(np.int64).reshape(-1, 3)
        if faces.size and int(faces.max()) >= n_vert:
            raise RigReadError(
                f"primitive {p} of {path.name} indexes vertex {int(faces.max())} of {n_vert}."
            )

        j_acc = int(attrs["JOINTS_0"])
        j_comp = int(doc["accessors"][j_acc].get("componentType", 5121))
        if j_comp not in (5121, 5123):
            raise RigReadError(
                f"primitive {p} of {path.name} stores JOINTS_0 as {_COMPONENT_NAME[j_comp]}; "
                "the spec allows unsigned byte or unsigned short. Fix: re-export."
            )
        joint_ids = _read_accessor(doc, buffers, j_acc, used_for=f"primitive {p} JOINTS_0")
        joint_ids = joint_ids.astype(np.int32)
        if joint_ids.shape[1] != 4:
            raise RigReadError(
                f"primitive {p} of {path.name} has JOINTS_0 of width {joint_ids.shape[1]}, not 4."
            )

        w_acc = int(attrs["WEIGHTS_0"])
        w_meta = doc["accessors"][w_acc]
        w_comp = int(w_meta.get("componentType", 5126))
        if w_comp not in (5126, 5121, 5123):
            raise RigReadError(
                f"primitive {p} of {path.name} stores WEIGHTS_0 as {_COMPONENT_NAME[w_comp]}; "
                "the spec allows float, normalized unsigned byte or normalized unsigned short."
            )
        if w_comp != 5126 and not w_meta.get("normalized", False):
            raise RigReadError(
                f"primitive {p} of {path.name} stores WEIGHTS_0 as {_COMPONENT_NAME[w_comp]} "
                "but does not mark the accessor normalized, so the values have no scale. "
                "Fix: re-export with float weights."
            )
        weights = _as_float(
            _read_accessor(doc, buffers, w_acc, used_for=f"primitive {p} WEIGHTS_0"),
            normalized=bool(w_meta.get("normalized", False)),
            comp=w_comp,
        )
        if weights.shape != joint_ids.shape:
            raise RigReadError(
                f"primitive {p} of {path.name}: WEIGHTS_0 is {weights.shape} and JOINTS_0 is "
                f"{joint_ids.shape}; they must match."
            )
        if joint_ids.size and int(joint_ids.max()) >= len(joints):
            bad = int(joint_ids.max())
            raise RigReadError(
                f"primitive {p} of {path.name} weights a vertex to joint {bad}, but the skin "
                f"lists {len(joints)} joints."
            )

        if "NORMAL" in attrs:
            nrm = _read_accessor(
                doc, buffers, int(attrs["NORMAL"]), used_for=f"primitive {p} NORMAL"
            ).astype(np.float64)
        else:
            nrm = _face_normals(pos, faces)
            computed_normals = True

        positions.append(pos)
        normal_blocks.append(nrm)
        face_blocks.append(faces + offset)
        index_blocks.append(joint_ids)
        weight_blocks.append(weights)
        offset += n_vert

    if not positions:
        raise RigReadError(f"mesh {mesh_index} of {path.name} has no primitives.")
    if len(positions) > 1:
        notes.append(f"{len(positions)} primitives concatenated into one body")
    if computed_normals:
        notes.append("normals computed from the faces (the file carried none)")

    vertices = np.concatenate(positions)
    faces_all = np.concatenate(face_blocks).astype(np.int32)
    normals = np.concatenate(normal_blocks)
    joint_indices = np.concatenate(index_blocks)
    weights = np.concatenate(weight_blocks)

    sums = weights.sum(axis=1)
    dead = np.flatnonzero(sums <= 0.0)
    if dead.size:
        raise RigReadError(
            f"{path.name}: {dead.size} of {len(vertices)} vertices carry NO bone weight "
            f"(first at index {int(dead[0])}); they would be left behind by every pose. "
            "Fix: weight-paint them, or re-export with automatic weights."
        )
    drift = float(np.abs(sums - 1.0).max())
    if drift > 1e-4:
        # Reported, NOT silently corrected: a studio's weights are its own.
        notes.append(f"bone weights are not normalised (max |sum-1| = {drift:.4g})")

    body = SkinnedBody(
        name=_node_label(nodes, chosen),
        vertices=_frozen(vertices),
        faces=_frozen(faces_all),
        normals=_frozen(normals),
        joint_indices=_frozen(joint_indices),
        weights=_frozen(weights),
        joints=tuple(joints),
        source=str(path),
        notes=tuple(notes),
    )
    return body


def _frozen(array: np.ndarray) -> np.ndarray:
    """Hand back an array nobody can edit in place.

    A body read from a file is evidence; a caller that mutates it in place
    turns every later measurement into a mystery.
    """
    out = np.ascontiguousarray(array)
    out.flags.writeable = False
    return out
