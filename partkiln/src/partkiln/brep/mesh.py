"""Tessellation with an ABSOLUTE deflection, and a hash that pins it.

`BRepMesh_IncrementalMesh(shape, deflection, isRelative=False, angular,
parallel)`: the deflection is millimetres, not a fraction of the shape's
size (build123d's `tolerance` is RELATIVE - a 0.1 there is 10 % of the
bounding box; ours is 0.1 mm). Measured (A66 P0a): F5 at 0.05 mm meshes in
42 ms, and the SHA-256 of the result is identical for `parallel=False` and
`parallel=True` at 0.05 and 0.3 mm - undocumented, so `test_brep_mesh` pins
it.

OCCT caches a triangulation on the shape and keeps an existing FINER one
when a coarser deflection is asked for, which would make "the mesh at 0.3"
depend on what was asked earlier. `tessellate` therefore cleans first by
default (`BRepTools.Clean_s`) so the same request always yields the same
mesh (determinism is a feature); pass `clean=False` to reuse.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from partkiln._errors import KernelError
from partkiln.brep import require_ocp

require_ocp()

from OCP.BRep import BRep_Tool  # noqa: E402
from OCP.BRepMesh import BRepMesh_IncrementalMesh  # noqa: E402
from OCP.BRepTools import BRepTools  # noqa: E402
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED  # noqa: E402
from OCP.TopExp import TopExp  # noqa: E402
from OCP.TopLoc import TopLoc_Location  # noqa: E402
from OCP.TopoDS import TopoDS, TopoDS_Shape  # noqa: E402
from OCP.TopTools import TopTools_IndexedMapOfShape  # noqa: E402

if TYPE_CHECKING:
    import trimesh

Tri = tuple[int, int, int]


@dataclass(frozen=True)
class Tessellation:
    """World-space nodes (mm, rounded 1e-6) and 0-based triangles wound so
    the face normal points OUT of the solid (reversed faces are flipped)."""

    nodes: list[tuple[float, float, float]]
    triangles: list[Tri]
    faces_without_mesh: int


def tessellate(
    shape: TopoDS_Shape,
    deflection_mm: float = 0.1,
    angular: float = 0.5,
    parallel: bool = True,
    clean: bool = True,
) -> TopoDS_Shape:
    """Mesh `shape` in place at an ABSOLUTE `deflection_mm`; returns the shape."""
    if deflection_mm <= 0:
        raise KernelError(f"deflection must be > 0 mm, got {deflection_mm}.", fix="0.1 is typical")
    if angular <= 0:
        raise KernelError(
            f"angular deflection must be > 0 rad, got {angular}.", fix="0.5 is typical"
        )
    if clean:
        BRepTools.Clean_s(shape)
    BRepMesh_IncrementalMesh(shape, float(deflection_mm), False, float(angular), bool(parallel))
    return shape


def _faces(shape: TopoDS_Shape) -> list[TopoDS_Shape]:
    m = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(shape, TopAbs_FACE, m)
    return [m.FindKey(i) for i in range(1, m.Extent() + 1)]


def collect(shape: TopoDS_Shape) -> Tessellation:
    """Gather the existing triangulation of every face into one node/triangle
    list (call `tessellate` first). Nodes are transformed by each face's
    location and rounded to 1e-6 mm before anything hashes them."""
    nodes: list[tuple[float, float, float]] = []
    tris: list[Tri] = []
    missing = 0
    for f in _faces(shape):
        face = TopoDS.Face_s(f)
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face, loc)
        if tri is None:
            missing += 1
            continue
        trsf = loc.Transformation()
        base = len(nodes)
        for i in range(1, tri.NbNodes() + 1):
            p = tri.Node(i).Transformed(trsf)
            nodes.append((round(p.X(), 6) + 0.0, round(p.Y(), 6) + 0.0, round(p.Z(), 6) + 0.0))
        flip = face.Orientation() == TopAbs_REVERSED
        for i in range(1, tri.NbTriangles() + 1):
            a, b, c = tri.Triangle(i).Get()
            t = (
                (base + a - 1, base + c - 1, base + b - 1)
                if flip
                else (base + a - 1, base + b - 1, base + c - 1)
            )
            tris.append(t)
    return Tessellation(nodes, tris, missing)


def mesh_hash(
    shape: TopoDS_Shape, deflection_mm: float = 0.1, angular: float = 0.5, parallel: bool = True
) -> str:
    """sha256 (16 hex) over every rounded node and every triangle at this deflection."""
    tessellate(shape, deflection_mm, angular, parallel)
    t = collect(shape)
    h = hashlib.sha256()
    for n in t.nodes:
        h.update(repr(n).encode())
    for tr in t.triangles:
        h.update(repr(tr).encode())
    return h.hexdigest()[:16]


def triangle_count(shape: TopoDS_Shape) -> int:
    """Triangles in the shape's CURRENT triangulation (0 before `tessellate`)."""
    total = 0
    for f in _faces(shape):
        tri = BRep_Tool.Triangulation_s(TopoDS.Face_s(f), TopLoc_Location())
        if tri is not None:
            total += tri.NbTriangles()
    return total


def to_trimesh(
    shape: TopoDS_Shape, deflection_mm: float = 0.1, angular: float = 0.5, parallel: bool = True
) -> tuple[trimesh.Trimesh, dict[str, object]]:
    """A `trimesh.Trimesh` (duplicate vertices merged so a closed solid comes
    back watertight) and a report {watertight, triangles, vertices,
    faces_without_mesh}; `trimesh` is imported here, lazily."""
    import numpy as np
    import trimesh as _trimesh

    tessellate(shape, deflection_mm, angular, parallel)
    t = collect(shape)
    if not t.triangles:
        raise KernelError("the shape produced no triangles.", fix="it has no faces to mesh")
    mesh = _trimesh.Trimesh(
        vertices=np.asarray(t.nodes, dtype=float),
        faces=np.asarray(t.triangles, dtype=np.int64),
        process=True,
    )
    report: dict[str, object] = {
        "watertight": bool(mesh.is_watertight),
        "triangles": len(mesh.faces),
        "vertices": len(mesh.vertices),
        "faces_without_mesh": t.faces_without_mesh,
    }
    return mesh, report


__all__ = ["Tessellation", "collect", "mesh_hash", "tessellate", "to_trimesh", "triangle_count"]
