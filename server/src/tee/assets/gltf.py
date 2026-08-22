"""glTF/GLB header probe: exact extents and tri counts from the JSON alone.

glTF stores per-primitive POSITION accessor min/max, so a scene AABB needs
only the JSON chunk and node-transform composition - no geometry decode, no
DCC, no third-party dependency (a .glb header is 12 bytes + chunked JSON).
glTF units are meters, normatively - the reason glTF is the preferred probe
format (research 25 R1-R4).
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

Mat4 = list[float]  # column-major 16 floats, glTF convention

_IDENTITY: Mat4 = [
    1, 0, 0, 0,
    0, 1, 0, 0,
    0, 0, 1, 0,
    0, 0, 0, 1,
]


def load_gltf_json(path: Path) -> dict[str, Any]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".gltf":
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            raise TeeError("bad_gltf", f"{path.name}: not valid glTF JSON ({exc}).") from exc
    if suffix != ".glb":
        raise TeeError(
            "bad_gltf",
            f"{path.name}: not a .gltf/.glb file.",
            fix="The probe reads glTF; other formats import via the DCC.",
        )
    with open(path, "rb") as fh:
        header = fh.read(12)
        if len(header) < 12 or header[:4] != b"glTF":
            raise TeeError("bad_gltf", f"{path.name}: missing glTF magic header.")
        _version, total = struct.unpack("<II", header[4:12])
        while fh.tell() < total:
            chunk_header = fh.read(8)
            if len(chunk_header) < 8:
                break
            length, kind = struct.unpack("<I4s", chunk_header)
            data = fh.read(length)
            if kind == b"JSON":
                return json.loads(data)
    raise TeeError("bad_gltf", f"{path.name}: no JSON chunk found.")


def _trs_matrix(node: dict[str, Any]) -> Mat4:
    if "matrix" in node:
        return list(node["matrix"])
    t = node.get("translation", [0.0, 0.0, 0.0])
    r = node.get("rotation", [0.0, 0.0, 0.0, 1.0])  # xyzw quaternion
    s = node.get("scale", [1.0, 1.0, 1.0])
    x, y, z, w = r
    # rotation matrix from quaternion (row values), then scale columns
    rot = [
        1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w),
        2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w),
        2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y),
    ]
    return [
        rot[0] * s[0], rot[1] * s[0], rot[2] * s[0], 0.0,
        rot[3] * s[1], rot[4] * s[1], rot[5] * s[1], 0.0,
        rot[6] * s[2], rot[7] * s[2], rot[8] * s[2], 0.0,
        t[0], t[1], t[2], 1.0,
    ]


def _mat_mul(a: Mat4, b: Mat4) -> Mat4:
    out = [0.0] * 16
    for col in range(4):
        for row in range(4):
            out[col * 4 + row] = sum(a[k * 4 + row] * b[col * 4 + k] for k in range(4))
    return out


def _transform_point(m: Mat4, p: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = p
    return (
        m[0] * x + m[4] * y + m[8] * z + m[12],
        m[1] * x + m[5] * y + m[9] * z + m[13],
        m[2] * x + m[6] * y + m[10] * z + m[14],
    )


def probe(path: Path) -> dict[str, Any]:
    """Compact facts for one glTF/GLB: triangle count, world-space extents
    in meters, mesh/material/texture counts."""
    doc = load_gltf_json(path)
    accessors = doc.get("accessors", [])
    meshes = doc.get("meshes", [])
    nodes = doc.get("nodes", [])

    tri_total = 0
    for mesh in meshes:
        for prim in mesh.get("primitives", []):
            mode = prim.get("mode", 4)  # 4 = TRIANGLES
            if mode != 4:
                continue
            if "indices" in prim:
                count = accessors[prim["indices"]].get("count", 0)
            else:
                pos = prim.get("attributes", {}).get("POSITION")
                count = accessors[pos].get("count", 0) if pos is not None else 0
            tri_total += count // 3

    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3

    def visit(node_index: int, parent: Mat4) -> None:
        node = nodes[node_index]
        world = _mat_mul(parent, _trs_matrix(node))
        mesh_index = node.get("mesh")
        if mesh_index is not None:
            for prim in meshes[mesh_index].get("primitives", []):
                pos = prim.get("attributes", {}).get("POSITION")
                if pos is None:
                    continue
                acc = accessors[pos]
                if "min" not in acc or "max" not in acc:
                    continue
                mn, mx = acc["min"], acc["max"]
                for corner in range(8):
                    p = (
                        mx[0] if corner & 1 else mn[0],
                        mx[1] if corner & 2 else mn[1],
                        mx[2] if corner & 4 else mn[2],
                    )
                    wx, wy, wz = _transform_point(world, p)
                    lo[0], lo[1], lo[2] = min(lo[0], wx), min(lo[1], wy), min(lo[2], wz)
                    hi[0], hi[1], hi[2] = max(hi[0], wx), max(hi[1], wy), max(hi[2], wz)
        for child in node.get("children", []):
            visit(child, world)

    scenes = doc.get("scenes", [])
    scene = scenes[doc.get("scene", 0)] if scenes else {"nodes": list(range(len(nodes)))}
    for root in scene.get("nodes", []):
        visit(root, _IDENTITY)

    out: dict[str, Any] = {
        "format": "glb" if path.suffix.lower() == ".glb" else "gltf",
        "units": "m",  # normative in glTF
        "triangles": tri_total,
        "meshes": len(meshes),
        "materials": len(doc.get("materials", [])),
        "textures": len(doc.get("textures", [])),
    }
    if lo[0] != float("inf"):
        # glTF is Y-up; report [x, y, z] extents as-authored plus the
        # Z-up interpretation the DCC adapters use (Blender importer maps
        # glTF Y-up to Blender Z-up).
        out["extents_m"] = [round(hi[i] - lo[i], 6) for i in range(3)]
        out["dims_zup_m"] = [
            round(hi[0] - lo[0], 6),
            round(hi[2] - lo[2], 6),
            round(hi[1] - lo[1], 6),
        ]
    return out
