"""Geometric facts about faces and edges: the backend of D6's selectors.

This module answers "what is this face / edge" (type, size, position,
normal, radius, seam, convexity, loop membership, adjacency); the selector
grammar and the names live in naming.py (P2b), which filters these facts.

Ordering: `faces()` and `edges()` sort by (type, rounded centroid, rounded
size) so that index i means the same sub-shape in every process - OCCT's own
map order is stable only within one process. These indices are kernel-
internal bookkeeping for naming.py; **they never leave the kernel** (Law 13:
a sub-shape is addressed by name, never by index).

Facts built on: `BRep_Tool.IsClosed_s(edge, face)` is the seam test - F1's
fifth `dir=Z` edge is the cylinder seam, which OCCT accepts in a fillet and
generates nothing for, so selectors exclude seams by default. Convexity is
the dihedral sign at the edge midpoint: with the edge oriented as it runs in
face A's wire (tangent t) and outward normals nA, nB, `(nA x nB) . t > 0` is
convex (a box edge, the rim of a drilled hole), `< 0` concave (the inside
corner of an L bracket), `|nA . nB - 1| < 1e-6` tangent (a fillet's edges).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

from partkiln.brep import require_ocp

require_ocp()

from OCP.Bnd import Bnd_Box  # noqa: E402
from OCP.BRep import BRep_Tool  # noqa: E402
from OCP.BRepAdaptor import (  # noqa: E402
    BRepAdaptor_Curve,
    BRepAdaptor_Curve2d,
    BRepAdaptor_Surface,
)
from OCP.BRepBndLib import BRepBndLib  # noqa: E402
from OCP.BRepGProp import BRepGProp  # noqa: E402
from OCP.BRepLProp import BRepLProp_SLProps  # noqa: E402
from OCP.BRepTools import BRepTools  # noqa: E402
from OCP.GeomAbs import (  # noqa: E402
    GeomAbs_BezierCurve,
    GeomAbs_BezierSurface,
    GeomAbs_BSplineCurve,
    GeomAbs_BSplineSurface,
    GeomAbs_Circle,
    GeomAbs_Cone,
    GeomAbs_Cylinder,
    GeomAbs_Ellipse,
    GeomAbs_Line,
    GeomAbs_Plane,
    GeomAbs_Sphere,
    GeomAbs_Torus,
)
from OCP.GProp import GProp_GProps  # noqa: E402
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_REVERSED, TopAbs_WIRE  # noqa: E402
from OCP.TopExp import TopExp, TopExp_Explorer  # noqa: E402
from OCP.TopoDS import TopoDS, TopoDS_Edge, TopoDS_Face, TopoDS_Shape  # noqa: E402
from OCP.TopTools import (  # noqa: E402
    TopTools_IndexedDataMapOfShapeListOfShape,
    TopTools_IndexedMapOfShape,
)

from partkiln.brep.shapes import as_list  # noqa: E402

Vec3 = tuple[float, float, float]
Box6 = tuple[float, float, float, float, float, float]

_SURFACE = {
    GeomAbs_Plane: "plane",
    GeomAbs_Cylinder: "cylinder",
    GeomAbs_Cone: "cone",
    GeomAbs_Sphere: "sphere",
    GeomAbs_Torus: "torus",
    GeomAbs_BSplineSurface: "bspline",
    GeomAbs_BezierSurface: "bspline",
}
_CURVE = {
    GeomAbs_Line: "line",
    GeomAbs_Circle: "circle",
    GeomAbs_Ellipse: "ellipse",
    GeomAbs_BSplineCurve: "bspline",
    GeomAbs_BezierCurve: "bspline",
}


@dataclass(frozen=True)
class FaceInfo:
    """One face's facts. `normal` is the OUTWARD unit normal at the parametric
    midpoint honouring the face orientation (exact for planes; a sample for
    curved faces); `radius` is set for cylinder / sphere / cone (its base)."""

    index: int
    surface_type: str
    area: float
    centroid: Vec3
    normal: Vec3 | None
    radius: float | None
    bbox: Box6
    shape: TopoDS_Face = field(repr=False, compare=False)


@dataclass(frozen=True)
class EdgeInfo:
    """One edge's facts. `direction` is the unit line direction with its sign
    canonicalised (first non-zero component positive) so it does not depend
    on the edge's parametrisation; `midpoint` is the curve at mid-parameter
    (a circle's midpoint is ON the circle, unlike its centroid)."""

    index: int
    curve_type: str
    length: float
    midpoint: Vec3
    direction: Vec3 | None
    radius: float | None
    is_seam: bool
    convexity: str
    adjacent_face_indices: tuple[int, ...]
    shape: TopoDS_Edge = field(repr=False, compare=False)


def _round3(v: Sequence[float]) -> tuple[float, ...]:
    return tuple(round(float(c), 3) + 0.0 for c in v)


def _surface_type(face: TopoDS_Face) -> str:
    return _SURFACE.get(BRepAdaptor_Surface(face).GetType(), "other")


def _curve_type(edge: TopoDS_Edge) -> str:
    return _CURVE.get(BRepAdaptor_Curve(edge).GetType(), "other")


def face_normal(face: TopoDS_Face) -> Vec3 | None:
    """Outward unit normal at the parametric midpoint, or None where undefined."""
    surf = BRepAdaptor_Surface(face)
    u = 0.5 * (surf.FirstUParameter() + surf.LastUParameter())
    v = 0.5 * (surf.FirstVParameter() + surf.LastVParameter())
    props = BRepLProp_SLProps(surf, u, v, 1, 1e-9)
    if not props.IsNormalDefined():
        return None
    n = props.Normal()
    sign = -1.0 if face.Orientation() == TopAbs_REVERSED else 1.0
    return (sign * n.X(), sign * n.Y(), sign * n.Z())


def _face_radius(face: TopoDS_Face) -> float | None:
    surf = BRepAdaptor_Surface(face)
    kind = surf.GetType()
    if kind == GeomAbs_Cylinder:
        return surf.Cylinder().Radius()
    if kind == GeomAbs_Sphere:
        return surf.Sphere().Radius()
    if kind == GeomAbs_Cone:
        return surf.Cone().RefRadius()
    return None


def _bbox(shape: TopoDS_Shape) -> Box6:
    b = Bnd_Box()
    BRepBndLib.AddOptimal_s(shape, b, False, False)
    return tuple(b.Get())  # type: ignore[return-value]


def _face_facts(face: TopoDS_Face) -> tuple[str, float, Vec3, Vec3 | None, float | None, Box6]:
    props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(face, props)
    c = props.CentreOfMass()
    return (
        _surface_type(face),
        props.Mass(),
        (c.X(), c.Y(), c.Z()),
        face_normal(face),
        _face_radius(face),
        _bbox(face),
    )


def _unique(shape: TopoDS_Shape, kind: int) -> list[TopoDS_Shape]:
    m = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(shape, kind, m)
    return [m.FindKey(i) for i in range(1, m.Extent() + 1)]


def faces(shape: TopoDS_Shape) -> list[FaceInfo]:
    """Every unique face, in the cross-process-stable order (see module doc)."""
    rows = []
    for f in _unique(shape, TopAbs_FACE):
        face = TopoDS.Face_s(f)
        kind, a, c, n, r, bb = _face_facts(face)
        rows.append((kind, _round3(c), round(a, 3), face, a, c, n, r, bb))
    rows.sort(key=lambda t: t[:3])
    return [
        FaceInfo(i, kind, a, c, n, r, bb, face)
        for i, (kind, _c3, _a3, face, a, c, n, r, bb) in enumerate(rows)
    ]


def _edge_geometry(edge: TopoDS_Edge) -> tuple[str, float, Vec3, Vec3 | None, float | None]:
    curve = BRepAdaptor_Curve(edge)
    props = GProp_GProps()
    BRepGProp.LinearProperties_s(edge, props)
    t0, t1 = curve.FirstParameter(), curve.LastParameter()
    mid = curve.Value(0.5 * (t0 + t1))
    kind = _curve_type(edge)
    direction: Vec3 | None = None
    radius: float | None = None
    if kind == "line":
        d = curve.Line().Direction()
        direction = _canonical((d.X(), d.Y(), d.Z()))
    elif kind == "circle":
        radius = curve.Circle().Radius()
    elif kind == "ellipse":
        radius = curve.Ellipse().MajorRadius()
    return kind, props.Mass(), (mid.X(), mid.Y(), mid.Z()), direction, radius


def _canonical(d: Vec3) -> Vec3:
    for c in d:
        if abs(c) > 1e-9:
            return d if c > 0 else (-d[0] + 0.0, -d[1] + 0.0, -d[2] + 0.0)
    return d


def _edge_tangent_in_face(edge: TopoDS_Edge, face: TopoDS_Face) -> Vec3 | None:
    """Unit tangent at mid-parameter, oriented as the edge runs in `face`'s wire
    (the explorer composes orientations along face -> wire -> edge)."""
    ex = TopExp_Explorer(face, TopAbs_EDGE)
    while ex.More():
        e = ex.Current()
        if e.IsSame(edge):
            curve = BRepAdaptor_Curve(TopoDS.Edge_s(e))
            t = 0.5 * (curve.FirstParameter() + curve.LastParameter())
            v = curve.DN(t, 1)
            if v.Magnitude() < 1e-12:
                return None
            v.Normalize()
            sign = -1.0 if e.Orientation() == TopAbs_REVERSED else 1.0
            return (sign * v.X(), sign * v.Y(), sign * v.Z())
        ex.Next()
    return None


def _normal_at(face: TopoDS_Face, edge: TopoDS_Edge) -> Vec3 | None:
    """Outward normal of `face` at the edge's mid-parameter, through the edge's
    pcurve on the face (same parameter as the 3D curve; no projection)."""
    pcurve = BRepAdaptor_Curve2d(edge, face)
    t = 0.5 * (pcurve.FirstParameter() + pcurve.LastParameter())
    uv = pcurve.Value(t)
    props = BRepLProp_SLProps(BRepAdaptor_Surface(face), uv.X(), uv.Y(), 1, 1e-9)
    if not props.IsNormalDefined():
        return None
    n = props.Normal()
    sign = -1.0 if face.Orientation() == TopAbs_REVERSED else 1.0
    return (sign * n.X(), sign * n.Y(), sign * n.Z())


def _convexity(edge: TopoDS_Edge, adjacent: list[TopoDS_Face]) -> str:
    if len(adjacent) != 2:
        return "unknown"
    fa, fb = adjacent
    na, nb = _normal_at(fa, edge), _normal_at(fb, edge)
    t = _edge_tangent_in_face(edge, fa)
    if na is None or nb is None or t is None:
        return "unknown"
    dot = sum(a * b for a, b in zip(na, nb, strict=True))
    if abs(dot - 1.0) < 1e-6:
        return "tangent"
    cross = (
        na[1] * nb[2] - na[2] * nb[1],
        na[2] * nb[0] - na[0] * nb[2],
        na[0] * nb[1] - na[1] * nb[0],
    )
    s = sum(a * b for a, b in zip(cross, t, strict=True))
    if abs(s) < 1e-9:
        return "unknown"
    return "convex" if s > 0 else "concave"


def edges(shape: TopoDS_Shape, face_infos: Sequence[FaceInfo] | None = None) -> list[EdgeInfo]:
    """Every unique edge with seam, convexity and adjacency, in stable order.

    Pass `face_infos` from `faces(shape)` to reuse it; `adjacent_face_indices`
    are indices into that same list.
    """
    finfos = list(face_infos) if face_infos is not None else faces(shape)
    # hash(TopoDS_Shape) is OCP's TShape+location hash: equal for IsSame shapes.
    face_index = {hash(f.shape): i for i, f in enumerate(finfos)}
    anc = TopTools_IndexedDataMapOfShapeListOfShape()
    TopExp.MapShapesAndAncestors_s(shape, TopAbs_EDGE, TopAbs_FACE, anc)
    rows = []
    for e in _unique(shape, TopAbs_EDGE):
        edge = TopoDS.Edge_s(e)
        kind, length, mid, direction, radius = _edge_geometry(edge)
        adjacent = (
            [TopoDS.Face_s(f) for f in as_list(anc.FindFromKey(edge))] if anc.Contains(edge) else []
        )
        seam = any(BRep_Tool.IsClosed_s(edge, f) for f in adjacent)
        adj_idx = tuple(sorted({_lookup(face_index, finfos, f) for f in adjacent}))
        conv = _convexity(edge, adjacent)
        rows.append(
            (
                kind,
                _round3(mid),
                round(length, 3),
                edge,
                length,
                mid,
                direction,
                radius,
                seam,
                conv,
                adj_idx,
            )
        )
    rows.sort(key=lambda t: t[:3])
    return [
        EdgeInfo(i, kind, length, mid, direction, radius, seam, conv, adj, edge)
        for i, (kind, _m3, _l3, edge, length, mid, direction, radius, seam, conv, adj) in enumerate(
            rows
        )
    ]


def _lookup(index: dict[int, int], finfos: list[FaceInfo], face: TopoDS_Face) -> int:
    i = index.get(hash(face))
    if i is not None and finfos[i].shape.IsSame(face):
        return i
    for j, f in enumerate(finfos):
        if f.shape.IsSame(face):
            return j
    return -1


def loops(face: TopoDS_Face, edge_infos: Sequence[EdgeInfo]) -> dict[str, list[list[int]]]:
    """Which edges bound `face` from its outer wire and from each inner wire
    (`BRepTools.OuterWire_s`); indices are into `edge_infos`."""
    outer = BRepTools.OuterWire_s(face)
    result: dict[str, list[list[int]]] = {"outer": [], "inner": []}
    ex = TopExp_Explorer(face, TopAbs_WIRE)
    while ex.More():
        wire = ex.Current()
        ids = _edge_indices(wire, edge_infos)
        if wire.IsSame(outer):
            result["outer"].append(ids)
        else:
            result["inner"].append(ids)
        ex.Next()
    return result


def _edge_indices(wire: TopoDS_Shape, edge_infos: Sequence[EdgeInfo]) -> list[int]:
    ids = []
    for e in _unique(wire, TopAbs_EDGE):
        for info in edge_infos:
            if info.shape.IsSame(e):
                ids.append(info.index)
                break
    return sorted(ids)


def nearest(
    entities: Sequence[FaceInfo | EdgeInfo], point: Sequence[float]
) -> FaceInfo | EdgeInfo | None:
    """The entity whose centroid / midpoint is closest to `point`; ties go to
    the lower index so the answer is deterministic."""
    best: FaceInfo | EdgeInfo | None = None
    best_d = math.inf
    for ent in entities:
        ref = ent.centroid if isinstance(ent, FaceInfo) else ent.midpoint
        d = math.dist(ref, tuple(float(c) for c in point))
        if d < best_d - 1e-12:
            best, best_d = ent, d
    return best


__all__ = ["EdgeInfo", "FaceInfo", "edges", "face_normal", "faces", "loops", "nearest"]
