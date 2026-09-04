"""Solids, features, booleans and measurements on OCCT, in millimetres and degrees.

Every function here takes and returns raw `TopoDS_Shape`s; names, selectors
and the document live above this layer (naming.py, features/), and the wire
never sees an OCCT object. Units are mm / deg at this boundary (D4) - angles
are converted to radians here and nowhere else.

Facts this module is built on (A66 P0a, OCP 7.9.3, this Mac, 2026-09-02):

- Counts are UNIQUE sub-shapes via `TopExp.MapShapes_s` (Law 20): F5 has 312
  edges by the map and 624 by `TopExp_Explorer`, which visits shared edges
  twice.
- An n-ary `BRepAlgoAPI_Cut` (`SetArguments`/`SetTools`, no glue, parallel)
  cuts 100 holes in 0.09 s against 0.46 s sequentially, with identical
  topology. `SetGlue(GlueShift)` on the same cut returned the UNCUT plate
  with `IsDone() == True` - glue is only for touching pattern copies, so
  `cut` never glues and `fuse` glues only behind an explicit `touching=True`.
- `LocOpe_DPrism(face, height, angle)` measures `height` ALONG the drafted
  wall: 10 mm at +3 deg reaches z = 9.986. `prism` therefore defaults to the
  vertical meaning (height / cos(taper)) and exposes `along_wall` for the
  raw OCCT number (+3 deg on 100x60x10 -> 59 085.191 mm3, 6 faces; -3 deg ->
  60 756.864, 10 faces incl. 4 conical corners).
- `BRepFilletAPI_MakeFillet` silently accepts a cylinder SEAM edge and
  generates nothing for it (`Generated(seam)` empty) - so every fillet and
  chamfer edge is checked after `Build` and the silent ones are reported in
  `ignored_edges` (Law 11: never silently accepted).
- `BRepBndLib.AddOptimal_s` is the tight box; `Add_s` is enlarged by shape
  tolerances.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from partkiln._errors import KernelError
from partkiln.brep import require_ocp

require_ocp()

from OCP.Bnd import Bnd_Box  # noqa: E402
from OCP.BRep import BRep_Tool  # noqa: E402
from OCP.BRepAdaptor import BRepAdaptor_Surface  # noqa: E402
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse  # noqa: E402
from OCP.BRepBndLib import BRepBndLib  # noqa: E402
from OCP.BRepBuilderAPI import (  # noqa: E402
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_Transform,
)
from OCP.BRepCheck import BRepCheck_Analyzer  # noqa: E402
from OCP.BRepFilletAPI import BRepFilletAPI_MakeChamfer, BRepFilletAPI_MakeFillet  # noqa: E402
from OCP.BRepGProp import BRepGProp  # noqa: E402
from OCP.BRepLProp import BRepLProp_SLProps  # noqa: E402
from OCP.BRepOffsetAPI import (  # noqa: E402
    BRepOffsetAPI_DraftAngle,
    BRepOffsetAPI_MakePipeShell,
    BRepOffsetAPI_MakeThickSolid,
    BRepOffsetAPI_ThruSections,
)
from OCP.BRepPrimAPI import (  # noqa: E402
    BRepPrimAPI_MakeBox,
    BRepPrimAPI_MakeCone,
    BRepPrimAPI_MakeCylinder,
    BRepPrimAPI_MakePrism,
    BRepPrimAPI_MakeRevol,
    BRepPrimAPI_MakeSphere,
)
from OCP.BRepTools import BRepTools, BRepTools_History  # noqa: E402
from OCP.GeomAbs import GeomAbs_Cone, GeomAbs_Cylinder, GeomAbs_Plane  # noqa: E402
from OCP.gp import gp_Ax1, gp_Ax2, gp_Dir, gp_Pln, gp_Pnt, gp_Trsf, gp_Vec  # noqa: E402
from OCP.GProp import GProp_GProps  # noqa: E402
from OCP.LocOpe import LocOpe_DPrism  # noqa: E402
from OCP.ShapeFix import ShapeFix_Shape  # noqa: E402
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain  # noqa: E402
from OCP.TopAbs import (  # noqa: E402
    TopAbs_EDGE,
    TopAbs_FACE,
    TopAbs_REVERSED,
    TopAbs_ShapeEnum,
    TopAbs_SOLID,
    TopAbs_VERTEX,
    TopAbs_WIRE,
)
from OCP.TopExp import TopExp  # noqa: E402
from OCP.TopoDS import (  # noqa: E402
    TopoDS,
    TopoDS_Edge,
    TopoDS_Face,
    TopoDS_Shape,
    TopoDS_Wire,
)
from OCP.TopTools import TopTools_IndexedMapOfShape, TopTools_ListOfShape  # noqa: E402

Vec3 = tuple[float, float, float]

_SURFACE_NAMES = {GeomAbs_Plane: "plane", GeomAbs_Cylinder: "cylinder", GeomAbs_Cone: "cone"}


# --------------------------------------------------------------------------- results


@dataclass(frozen=True)
class FeatureResult:
    """What a builder-API feature returns: the shape plus what history.py needs.

    `algo` is the OCCT builder kept alive so `history.record(algo, inputs)`
    can read its per-sub-shape `Generated/Modified/IsDeleted` (only booleans
    and UnifySameDomain expose a ready `History()`; every other builder does
    not). `status` is the builder's own word where it has one (draft).
    """

    shape: TopoDS_Shape
    algo: object
    inputs: tuple[TopoDS_Shape, ...]
    is_done: bool
    status: str = "ok"


@dataclass(frozen=True)
class EdgeFeatureResult(FeatureResult):
    """A fillet or chamfer: `ignored_edges` are the input indices OCCT accepted
    and then generated NOTHING for (the cylinder seam is the measured case);
    `faulty_contours` is `NbFaultyContours` (fillet only; chamfer has none)."""

    faulty_contours: int = 0
    ignored_edges: tuple[int, ...] = ()


@dataclass(frozen=True)
class BooleanResult:
    """A boolean's result with Law 11 answered: `no_effect` is True when the
    result has the base's unique face AND edge counts AND its volume to 1e-9
    relative - the caller refuses with `pk_no_effect` on it. `history` is the
    algorithm's own `BRepTools_History` (merge it into the feature's map)."""

    shape: TopoDS_Shape
    history: BRepTools_History | None
    is_done: bool
    no_effect: bool
    empty: bool
    counts_before: dict[str, int]
    counts_after: dict[str, int]
    volume_before: float
    volume_after: float


# --------------------------------------------------------------------------- helpers


def _pnt(p: Sequence[float]) -> gp_Pnt:
    return gp_Pnt(float(p[0]), float(p[1]), float(p[2]))


def _dir(d: Sequence[float]) -> gp_Dir:
    if all(abs(float(c)) < 1e-12 for c in d):
        raise KernelError("a direction cannot be the zero vector.", fix="give a non-zero (x, y, z)")
    return gp_Dir(float(d[0]), float(d[1]), float(d[2]))


def _list(shapes: Sequence[TopoDS_Shape]) -> TopTools_ListOfShape:
    lst = TopTools_ListOfShape()
    for s in shapes:
        lst.Append(s)
    return lst


def as_list(lst: TopTools_ListOfShape) -> list[TopoDS_Shape]:
    """A Python list from a `TopTools_ListOfShape` WITHOUT `list(lst)`.

    Measured: pybind's fallback iteration costs 2 ms per call even on an
    empty list (312 ancestor lists made `query.edges(F5)` take 0.7 s);
    copying and popping `First()` costs 2 us.
    """
    out: list[TopoDS_Shape] = []
    if lst.IsEmpty():
        return out
    copy = TopTools_ListOfShape()
    copy.Assign(lst)
    while not copy.IsEmpty():
        out.append(copy.First())
        copy.RemoveFirst()
    return out


def _downcast(shape: TopoDS_Shape, kind: TopAbs_ShapeEnum) -> TopoDS_Shape:
    if kind == TopAbs_FACE:
        return TopoDS.Face_s(shape)
    if kind == TopAbs_EDGE:
        return TopoDS.Edge_s(shape)
    if kind == TopAbs_VERTEX:
        return TopoDS.Vertex_s(shape)
    if kind == TopAbs_SOLID:
        return TopoDS.Solid_s(shape)
    if kind == TopAbs_WIRE:
        return TopoDS.Wire_s(shape)
    return shape


def unique_subshapes(shape: TopoDS_Shape, kind: TopAbs_ShapeEnum) -> list[TopoDS_Shape]:
    """Every sub-shape of `kind`, each ONCE, in OCCT's map order (Law 20).

    `TopExp.MapShapes_s` is the measured basis: 312 edges on F5 where the
    explorer reports 624. The map order is stable for one shape in one
    process; query.py sorts geometrically on top of it so that indices are
    stable ACROSS processes.
    """
    m = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(shape, kind, m)
    return [_downcast(m.FindKey(i), kind) for i in range(1, m.Extent() + 1)]


def is_concave_cylinder(face: TopoDS_Face) -> bool:
    """Does the material lie OUTSIDE this cylindrical face - i.e. is it a hole?

    The outward normal at the face's parametric midpoint points TOWARD the
    axis for a hole (the material is the other way) and AWAY from it for a
    fillet or a boss. Radius alone cannot tell them apart, and counting by
    radius failed a correct part (see the module docstring).
    """
    surface = BRepAdaptor_Surface(face)
    u = 0.5 * (surface.FirstUParameter() + surface.LastUParameter())
    v = 0.5 * (surface.FirstVParameter() + surface.LastVParameter())
    props = BRepLProp_SLProps(surface, u, v, 1, 1e-9)
    if not props.IsNormalDefined():
        return False
    sign = -1.0 if face.Orientation() == TopAbs_REVERSED else 1.0
    normal = props.Normal()
    point = props.Value()
    axis = surface.Cylinder().Axis()
    origin, direction = axis.Location(), axis.Direction()
    delta = (point.X() - origin.X(), point.Y() - origin.Y(), point.Z() - origin.Z())
    along = delta[0] * direction.X() + delta[1] * direction.Y() + delta[2] * direction.Z()
    radial = (
        delta[0] - along * direction.X(),
        delta[1] - along * direction.Y(),
        delta[2] - along * direction.Z(),
    )
    outward = (sign * normal.X(), sign * normal.Y(), sign * normal.Z())
    return sum(a * b for a, b in zip(radial, outward, strict=True)) < 0.0


def cylinder_sweep_deg(face: TopoDS_Face) -> float:
    """How far around its own axis this cylindrical face actually goes, in degrees.

    A drilled hole's wall closes on itself (360 deg, seam included); a corner
    radius does not. Read from the AREA, never from the parametric bounds:
    measured 2026-09-04, a hole split into two half-cylinders by a mirror-join
    reports u bounds 90 deg -> 450 deg (a whole turn) on a face whose area is
    157.080 mm2 - exactly half a turn of r5 x 10. The bounds lie where the
    area does not.

    A cylindrical patch has area = r * sweep * height, and `v` on a cylinder
    IS the distance along the axis, so the height is the face's own v extent.
    A trim that is not a uv rectangle (a hole clipped by a slanted face) holds
    less area than its uv box, so this UNDER-reports: the error can only drop
    a hole from a table, never invent one.
    """
    surface = BRepAdaptor_Surface(face)
    radius = surface.Cylinder().Radius()
    height = abs(surface.LastVParameter() - surface.FirstVParameter())
    if radius <= 0.0 or height <= 0.0:
        return 0.0
    props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(face, props)
    return math.degrees(abs(props.Mass()) / (radius * height))


def counts(shape: TopoDS_Shape) -> dict[str, int]:
    """Unique {solids, faces, edges, vertices} - never explorer visits (Law 20)."""
    out: dict[str, int] = {}
    for name, kind in (
        ("solids", TopAbs_SOLID),
        ("faces", TopAbs_FACE),
        ("edges", TopAbs_EDGE),
        ("vertices", TopAbs_VERTEX),
    ):
        m = TopTools_IndexedMapOfShape()
        TopExp.MapShapes_s(shape, kind, m)
        out[name] = m.Extent()
    return out


def _outer_wire(profile: TopoDS_Shape) -> TopoDS_Wire:
    kind = profile.ShapeType()
    if kind == TopAbs_WIRE:
        return TopoDS.Wire_s(profile)
    if kind == TopAbs_FACE:
        return BRepTools.OuterWire_s(TopoDS.Face_s(profile))
    raise KernelError(
        f"a profile must be a wire or a face, got {kind.name}.",
        fix="pass the sketch's closed wire or the face made from it",
    )


def _surface_kind(face: TopoDS_Face) -> str:
    return _SURFACE_NAMES.get(BRepAdaptor_Surface(face).GetType(), "other")


# --------------------------------------------------------------------------- primitives


def box(x: float, y: float, z: float, at: Sequence[float] = (0.0, 0.0, 0.0)) -> TopoDS_Shape:
    """An axis-aligned box with its min corner at `at` (mm)."""
    if min(x, y, z) <= 0:
        raise KernelError(
            f"box sides must be positive, got ({x}, {y}, {z}).", fix="give three lengths > 0"
        )
    return BRepPrimAPI_MakeBox(_pnt(at), float(x), float(y), float(z)).Shape()


def cylinder(
    r: float,
    h: float,
    at: Sequence[float] = (0.0, 0.0, 0.0),
    direction: Sequence[float] = (0.0, 0.0, 1.0),
) -> TopoDS_Shape:
    """A cylinder of radius `r` and height `h` from base centre `at` along `direction`."""
    if r <= 0 or h <= 0:
        raise KernelError(
            f"cylinder needs r > 0 and h > 0, got r={r}, h={h}.", fix="check the diameter"
        )
    return BRepPrimAPI_MakeCylinder(gp_Ax2(_pnt(at), _dir(direction)), float(r), float(h)).Shape()


def sphere(r: float, at: Sequence[float] = (0.0, 0.0, 0.0)) -> TopoDS_Shape:
    """A full sphere: ONE face with a seam edge, exactly like a cylinder wall."""
    if r <= 0:
        raise KernelError(f"sphere needs r > 0, got {r}.", fix="check the diameter")
    return BRepPrimAPI_MakeSphere(_pnt(at), float(r)).Shape()


def cone(
    r1: float,
    r2: float,
    h: float,
    at: Sequence[float] = (0.0, 0.0, 0.0),
    direction: Sequence[float] = (0.0, 0.0, 1.0),
) -> TopoDS_Shape:
    """A cone (frustum when both radii are > 0) from base radius `r1` to top `r2` over `h`."""
    if h <= 0 or r1 < 0 or r2 < 0 or (r1 == 0 and r2 == 0):
        raise KernelError(
            f"cone needs h > 0 and radii >= 0 (not both 0), got r1={r1}, r2={r2}, h={h}.",
            fix="check the radii",
        )
    return BRepPrimAPI_MakeCone(
        gp_Ax2(_pnt(at), _dir(direction)), float(r1), float(r2), float(h)
    ).Shape()


def make_face_from_points(points: Sequence[Sequence[float]]) -> TopoDS_Face:
    """A planar face bounded by the closed polygon through `points` (>= 3, coplanar).

    The polygon is closed here; the points are taken in the order given, so a
    counter-clockwise ring seen from +normal gives a face whose normal is
    +normal (the direction `prism` extrudes along by default).
    """
    if len(points) < 3:
        raise KernelError(
            f"a face needs at least 3 points, got {len(points)}.", fix="give a closed polygon"
        )
    pg = BRepBuilderAPI_MakePolygon()
    for p in points:
        pg.Add(_pnt(p))
    pg.Close()
    if not pg.IsDone():
        raise KernelError(
            "the points do not form a polygon (repeated or collinear).", fix="check them"
        )
    mk = BRepBuilderAPI_MakeFace(pg.Wire(), True)
    if not mk.IsDone():
        raise KernelError(
            "the polygon is not planar; a face needs coplanar points.", fix="project them"
        )
    return mk.Face()


# --------------------------------------------------------------------------- sweeps


class _DPrismAlgo:
    """`LocOpe_DPrism` exposes `Shapes(s)` (the generated shapes) and nothing
    else; this adapter gives it the `Generated/Modified/IsDeleted` face that
    `history.record` reads from every other builder."""

    def __init__(self, dprism: LocOpe_DPrism) -> None:
        self._d = dprism

    def Generated(self, s: TopoDS_Shape) -> TopTools_ListOfShape:
        return self._d.Shapes(s)

    def Modified(self, s: TopoDS_Shape) -> TopTools_ListOfShape:
        return TopTools_ListOfShape()

    def IsDeleted(self, s: TopoDS_Shape) -> bool:
        return False


def prism(
    face: TopoDS_Face,
    vec: Sequence[float],
    taper_deg: float = 0.0,
    height: str = "vertical",
) -> FeatureResult:
    """Extrude `face` along `vec` (mm), optionally with a draft taper.

    `taper_deg > 0` leans the walls INWARD (the body narrows away from the
    face: +3 deg on 100x60x10 loses 915 mm3); `< 0` flares them and adds
    conical corner faces. Taper uses `LocOpe_DPrism` for a NEW body (measured:
    `BRepFeat_MakeDPrism` is only for join/cut on an existing body), and its
    `height` is measured ALONG the drafted wall - 10 mm at 3 deg reaches
    z = 9.986. `height="vertical"` (the default, what a drawing dimensions)
    divides by cos(taper) so the body reaches |vec|; `height="along_wall"`
    passes |vec| straight through and reproduces the raw OCCT number
    (59 085.191 mm3 for +3 deg).
    """
    length = math.sqrt(sum(float(c) ** 2 for c in vec))
    if length <= 0:
        raise KernelError("extrude distance must be > 0.", fix="give a non-zero vector")
    if abs(taper_deg) < 1e-12:
        algo = BRepPrimAPI_MakePrism(face, gp_Vec(*[float(c) for c in vec]))
        return FeatureResult(algo.Shape(), algo, (face,), algo.IsDone())
    if height not in ("vertical", "along_wall"):
        raise KernelError(
            f"height must be 'vertical' or 'along_wall', got {height!r}.",
            fix="'vertical' is what a drawing dimensions",
        )
    if abs(taper_deg) >= 90:
        raise KernelError(f"taper {taper_deg} deg is not a draft.", fix="use |taper| < 90")
    # DPrism extrudes along the SURFACE normal (measured: reversing the face's
    # orientation changes nothing, and the two-height form flips the taper's
    # sign), so the vector must be parallel to it and an anti-parallel vector
    # is honoured by mirroring the body through the face plane afterwards -
    # same volume, same face count, still valid.
    surface_normal = _surface_normal(face)
    d = [float(c) / length for c in vec]
    dot = sum(a * b for a, b in zip(surface_normal, d, strict=True))
    if abs(abs(dot) - 1.0) > 1e-6:
        raise KernelError(
            "a tapered extrude must be normal to its face.",
            fix="extrude along the face normal, or taper with a draft feature afterwards",
        )
    h = length if height == "along_wall" else length / math.cos(math.radians(taper_deg))
    dprism = LocOpe_DPrism(face, h, math.radians(taper_deg))
    if not dprism.IsDone():
        raise KernelError(
            f"tapered extrude failed (taper {taper_deg} deg over {length} mm).",
            fix="a taper that closes the profile before the height is unreachable; reduce it",
        )
    shape = dprism.Shape()
    if dot < 0:
        props = GProp_GProps()
        BRepGProp.SurfaceProperties_s(face, props)
        mirror = gp_Trsf()
        mirror.SetMirror(gp_Ax2(props.CentreOfMass(), _dir(surface_normal)))
        shape = BRepBuilderAPI_Transform(shape, mirror, True).Shape()
    return FeatureResult(shape, _DPrismAlgo(dprism), (face,), True)


def _surface_normal(face: TopoDS_Face) -> Vec3:
    """The plane's own axis direction (NOT flipped for a reversed face: that
    is the direction `LocOpe_DPrism` extrudes along)."""
    surf = BRepAdaptor_Surface(face)
    if surf.GetType() != GeomAbs_Plane:
        raise KernelError(
            "only a planar face can be extruded with a taper.", fix="pick a planar face"
        )
    n = surf.Plane().Axis().Direction()
    return (n.X(), n.Y(), n.Z())


def revolve(
    face: TopoDS_Shape,
    axis_point: Sequence[float],
    axis_dir: Sequence[float],
    angle_deg: float = 360.0,
) -> FeatureResult:
    """Revolve a face (or wire) about the axis through `axis_point` along `axis_dir`."""
    if angle_deg <= 0 or angle_deg > 360:
        raise KernelError(f"revolve angle must be in (0, 360], got {angle_deg}.", fix="check it")
    algo = BRepPrimAPI_MakeRevol(
        face, gp_Ax1(_pnt(axis_point), _dir(axis_dir)), math.radians(angle_deg)
    )
    return FeatureResult(algo.Shape(), algo, (face,), algo.IsDone())


def sweep(profile: TopoDS_Shape, path: TopoDS_Wire, frenet: bool = False) -> FeatureResult:
    """Sweep a closed profile (wire or face) along `path` into a solid.

    `frenet=False` is OCCT's corrected-Frenet trihedron (`SetMode(False)`),
    the one that does not twist on planar paths; measured: a r3 circle along
    50 mm gives 1 413.717 mm3 = the arithmetic.
    """
    wire = _outer_wire(profile)
    algo = BRepOffsetAPI_MakePipeShell(path)
    algo.SetMode(bool(frenet))
    algo.Add(wire)
    algo.Build()
    if not algo.IsDone():
        raise KernelError(
            f"sweep failed (status {algo.GetStatus().name}).",
            fix="the profile must sit on the path start and the path must be tangent-continuous",
        )
    if not algo.MakeSolid():
        raise KernelError("sweep produced an open shell, not a solid.", fix="close the profile")
    return FeatureResult(algo.Shape(), algo, (wire, path), True)


def loft(wires: Sequence[TopoDS_Wire], ruled: bool = False, solid: bool = True) -> FeatureResult:
    """Loft through >= 2 section wires (`ThruSections` with `CheckCompatibility`)."""
    if len(wires) < 2:
        raise KernelError(f"loft needs at least 2 sections, got {len(wires)}.", fix="add a section")
    algo = BRepOffsetAPI_ThruSections(bool(solid), bool(ruled))
    algo.CheckCompatibility(True)
    for w in wires:
        algo.AddWire(w)
    algo.Build()
    if not algo.IsDone():
        raise KernelError("loft failed to build.", fix="sections must all be closed (or all open)")
    return FeatureResult(algo.Shape(), algo, tuple(wires), True)


# --------------------------------------------------------------------------- booleans


def _boolean_result(algo: object, base: TopoDS_Shape) -> BooleanResult:
    shape = algo.Shape()  # type: ignore[attr-defined]
    before, after = counts(base), counts(shape)
    v0, v1 = volume(base), volume(shape)
    same_counts = before["faces"] == after["faces"] and before["edges"] == after["edges"]
    same_volume = abs(v1 - v0) <= 1e-9 * max(abs(v0), 1e-12)
    return BooleanResult(
        shape=shape,
        history=algo.History(),  # type: ignore[attr-defined]
        is_done=bool(algo.IsDone()),  # type: ignore[attr-defined]
        no_effect=same_counts and same_volume,
        empty=after["solids"] == 0,
        counts_before=before,
        counts_after=after,
        volume_before=v0,
        volume_after=v1,
    )


def cut(base: TopoDS_Shape, tools: Sequence[TopoDS_Shape]) -> BooleanResult:
    """ONE n-ary cut of every tool from `base` - never a loop, never glue.

    Measured: 100 holes as one `SetArguments`/`SetTools` cut take 0.09 s
    against 0.46 s as 100 cuts, with identical topology; `SetGlue` on the same
    cut returned the uncut plate with `IsDone() == True`, so this function has
    no glue flag at all.
    """
    if not tools:
        raise KernelError("cut needs at least one tool.", fix="pass the shapes to subtract")
    algo = BRepAlgoAPI_Cut()
    algo.SetArguments(_list([base]))
    algo.SetTools(_list(list(tools)))
    algo.SetRunParallel(True)
    algo.Build()
    return _boolean_result(algo, base)


def fuse(shapes: Sequence[TopoDS_Shape], touching: bool = False) -> BooleanResult:
    """n-ary fuse of `shapes` (first is the base for the no-effect test).

    `touching=True` enables `SetGlue(BOPAlgo_GlueShift)` - correct ONLY for
    pattern copies that share faces without intersecting; on intersecting
    bodies glue silently returns the unfused input (measured on a cut).
    """
    if len(shapes) < 2:
        raise KernelError(f"fuse needs at least 2 shapes, got {len(shapes)}.", fix="add a shape")
    algo = BRepAlgoAPI_Fuse()
    algo.SetArguments(_list([shapes[0]]))
    algo.SetTools(_list(list(shapes[1:])))
    algo.SetRunParallel(True)
    if touching:
        from OCP.BOPAlgo import BOPAlgo_GlueEnum

        algo.SetGlue(BOPAlgo_GlueEnum.BOPAlgo_GlueShift)
    algo.Build()
    return _boolean_result(algo, shapes[0])


def common(a: TopoDS_Shape, b: TopoDS_Shape) -> BooleanResult:
    """The intersection of two shapes (interference checks: cubes at x=0 and
    x=19 -> 400.000 mm3 at (19.5, 10, 10)); `empty` when they do not meet."""
    algo = BRepAlgoAPI_Common()
    algo.SetArguments(_list([a]))
    algo.SetTools(_list([b]))
    algo.SetRunParallel(True)
    algo.Build()
    return _boolean_result(algo, a)


def unify(shape: TopoDS_Shape) -> tuple[TopoDS_Shape, BRepTools_History]:
    """Merge same-domain faces and edges after a boolean (D6: the face-count
    pins assume it: F2's fuse is 13 faces only after this). Returns the shape
    and the algorithm's own history to merge into the feature's map."""
    algo = ShapeUpgrade_UnifySameDomain(shape, True, True, False)
    algo.Build()
    return algo.Shape(), algo.History()


# --------------------------------------------------------------------------- edge features


def _check_generated(algo: object, edges: Sequence[TopoDS_Edge]) -> tuple[int, ...]:
    ignored = []
    for i, e in enumerate(edges):
        if algo.Generated(e).Extent() == 0:  # type: ignore[attr-defined]
            ignored.append(i)
    return tuple(ignored)


def fillet(
    shape: TopoDS_Shape,
    edges: Sequence[TopoDS_Edge],
    radius: float | tuple[float, float],
) -> EdgeFeatureResult:
    """Constant (r) or linearly varying ((r1, r2)) fillet on `edges`.

    Refuses when OCCT cannot build it, naming `NbFaultyContours` (r=12 on the
    top-front edge of a 10 mm plate is the pinned case). An edge that Built
    fine but generated no face is reported in `ignored_edges` rather than
    accepted: the cylinder seam is the measured example.
    """
    if not edges:
        raise KernelError("fillet needs at least one edge.", fix="select the edges")
    r1, r2 = (radius, radius) if isinstance(radius, int | float) else radius
    if r1 <= 0 or r2 <= 0:
        raise KernelError(f"fillet radius must be > 0, got {radius}.", fix="check it")
    algo = BRepFilletAPI_MakeFillet(shape)
    for e in edges:
        if r1 == r2:
            algo.Add(float(r1), e)
        else:
            algo.Add(float(r1), float(r2), e)
    algo.Build()
    faulty = algo.NbFaultyContours()
    if not algo.IsDone():
        raise KernelError(
            f"fillet r={radius} failed: NbFaultyContours={faulty} of {algo.NbContours()}.",
            fix="the radius must be smaller than the faces it rolls across; reduce it",
        )
    return EdgeFeatureResult(
        algo.Shape(),
        algo,
        (shape,),
        True,
        faulty_contours=faulty,
        ignored_edges=_check_generated(algo, edges),
    )


def chamfer(
    shape: TopoDS_Shape,
    edges: Sequence[TopoDS_Edge],
    distance: float | tuple[float, float],
    face: TopoDS_Face | None = None,
) -> EdgeFeatureResult:
    """Symmetric (d) or two-distance ((d1, d2)) chamfer on `edges`.

    For (d1, d2) OCCT needs the face on which d1 is measured; `face` names it,
    else the first ancestor face of each edge is used. `MakeChamfer` has no
    `NbFaultyContours`; failure is `IsDone() == False` and the silent case is
    the same per-edge `Generated` check as the fillet.
    """
    if not edges:
        raise KernelError("chamfer needs at least one edge.", fix="select the edges")
    d1, d2 = (distance, distance) if isinstance(distance, int | float) else distance
    if d1 <= 0 or d2 <= 0:
        raise KernelError(f"chamfer distance must be > 0, got {distance}.", fix="check it")
    algo = BRepFilletAPI_MakeChamfer(shape)
    if d1 == d2:
        for e in edges:
            algo.Add(float(d1), e)
    else:
        from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape

        anc = TopTools_IndexedDataMapOfShapeListOfShape()
        TopExp.MapShapesAndAncestors_s(shape, TopAbs_EDGE, TopAbs_FACE, anc)
        for e in edges:
            ref = face if face is not None else TopoDS.Face_s(anc.FindFromKey(e).First())
            algo.Add(float(d1), float(d2), e, ref)
    algo.Build()
    if not algo.IsDone():
        raise KernelError(
            f"chamfer d={distance} failed on {len(edges)} edge(s).",
            fix="the distance must be smaller than the faces it cuts across; reduce it",
        )
    return EdgeFeatureResult(
        algo.Shape(), algo, (shape,), True, ignored_edges=_check_generated(algo, edges)
    )


# --------------------------------------------------------------------------- shell / draft


def shell(
    shape: TopoDS_Shape,
    faces_to_remove: Sequence[TopoDS_Face],
    thickness: float,
    direction: str = "in",
) -> FeatureResult:
    """Hollow `shape` to a wall of `thickness`, opening the removed faces.

    `direction="in"` keeps the outer skin (offset -t: a 40x40x20 box opened at
    the top with t=2 leaves 8 672 mm3 = 32 000 - 36*36*18); `"out"` grows the
    wall outward (+t).
    """
    if thickness <= 0:
        raise KernelError(f"shell thickness must be > 0, got {thickness}.", fix="check it")
    if direction not in ("in", "out"):
        raise KernelError(f"direction must be 'in' or 'out', got {direction!r}.", fix="pick one")
    if not faces_to_remove:
        raise KernelError("shell needs at least one face to open.", fix="select the open face")
    offset = -float(thickness) if direction == "in" else float(thickness)
    algo = BRepOffsetAPI_MakeThickSolid()
    algo.MakeThickSolidByJoin(shape, _list(list(faces_to_remove)), offset, 1e-3)
    if not algo.IsDone():
        raise KernelError(
            f"shell t={thickness} {direction} failed.",
            fix="the wall must be thinner than the smallest feature it wraps",
        )
    return FeatureResult(algo.Shape(), algo, (shape,), True)


def draft(
    shape: TopoDS_Shape,
    faces: Sequence[TopoDS_Face],
    angle_deg: float,
    neutral_plane: tuple[Sequence[float], Sequence[float]],
    pull_dir: Sequence[float],
) -> FeatureResult:
    """Tilt `faces` by `angle_deg` about their intersection with the neutral plane.

    `neutral_plane` is (point, normal); `pull_dir` is the side matter is
    removed from for a positive angle (OCCT's `Direction`). Only planar,
    cylindrical and conical faces can be drafted - any other type is refused
    BY NAME before OCCT is asked, because `Add` on a torus does nothing and
    says nothing. `Status()` is surfaced as `result.status`.
    """
    if not faces:
        raise KernelError("draft needs at least one face.", fix="select the faces")
    if abs(angle_deg) >= 90 or abs(angle_deg) < 1e-12:
        raise KernelError(f"draft angle must be in (0, 90), got {angle_deg}.", fix="check it")
    for i, f in enumerate(faces):
        kind = _surface_kind(f)
        if kind == "other":
            actual = BRepAdaptor_Surface(f).GetType().name.removeprefix("GeomAbs_").lower()
            raise KernelError(
                f"draft cannot tilt face {i}: it is a {actual}; only plane, cylinder or cone faces "
                "can be drafted.",
                fix="select the planar side walls instead",
            )
    point, normal = neutral_plane
    plane = gp_Pln(_pnt(point), _dir(normal))
    algo = BRepOffsetAPI_DraftAngle(shape)
    for i, f in enumerate(faces):
        algo.Add(f, _dir(pull_dir), math.radians(angle_deg), plane)
        if not algo.AddDone():
            status = algo.Status().name.removeprefix("Draft_")
            raise KernelError(
                f"draft of face {i} failed while adding ({status}).",
                fix="the face must meet the neutral plane; check the plane and the pull direction",
            )
    algo.Build()
    status = algo.Status().name.removeprefix("Draft_")
    if not algo.IsDone():
        raise KernelError(f"draft failed to build ({status}).", fix="reduce the angle")
    return FeatureResult(algo.Shape(), algo, (shape,), True, status=status)


# --------------------------------------------------------------------------- transform


def transform(
    shape: TopoDS_Shape,
    translation: Sequence[float] = (0.0, 0.0, 0.0),
    rotation: tuple[Sequence[float], Sequence[float], float] | None = None,
) -> FeatureResult:
    """Rotate then translate a COPY of `shape` (`BRepBuilderAPI_Transform(copy=True)`).

    `rotation` is (axis_point, axis_dir, angle_deg). The copy keeps the source
    intact for history (the copy's faces are `Modified` images of the
    source's) and keeps its location identity, so later tessellation and
    exports see world coordinates directly.
    """
    trsf = gp_Trsf()
    if rotation is not None:
        point, axis, angle_deg = rotation
        rot = gp_Trsf()
        rot.SetRotation(gp_Ax1(_pnt(point), _dir(axis)), math.radians(float(angle_deg)))
        trsf = rot
    if any(abs(float(c)) > 0 for c in translation):
        tr = gp_Trsf()
        tr.SetTranslation(gp_Vec(*[float(c) for c in translation]))
        trsf = tr.Multiplied(trsf)
    algo = BRepBuilderAPI_Transform(shape, trsf, True)
    return FeatureResult(algo.Shape(), algo, (shape,), algo.IsDone())


# --------------------------------------------------------------------------- measurement


def volume(shape: TopoDS_Shape) -> float:
    """Exact volume in mm3 (`BRepGProp.VolumeProperties_s`, no triangulation)."""
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    return props.Mass()


def area(shape: TopoDS_Shape) -> float:
    """Exact surface area in mm2."""
    props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(shape, props)
    return props.Mass()


def centre_of_mass(shape: TopoDS_Shape) -> Vec3:
    """Centre of volume (uniform density) in mm."""
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    c = props.CentreOfMass()
    return (c.X(), c.Y(), c.Z())


def inertia(shape: TopoDS_Shape, about: str = "com") -> tuple[Vec3, Vec3, Vec3]:
    """Second moments of volume (mm5; multiply by density for kg mm2) as a 3x3
    matrix about the centre of mass (`about="com"`) or the origin."""
    if about not in ("com", "origin"):
        raise KernelError(f"about must be 'com' or 'origin', got {about!r}.", fix="pick one")
    props = GProp_GProps(_pnt(centre_of_mass(shape))) if about == "com" else GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    m = props.MatrixOfInertia()
    return tuple(tuple(m.Value(i, j) for j in (1, 2, 3)) for i in (1, 2, 3))  # type: ignore[return-value]


def bbox(shape: TopoDS_Shape) -> tuple[float, float, float, float, float, float]:
    """Tight (xmin, ymin, zmin, xmax, ymax, zmax) via `AddOptimal_s` on the
    geometry itself (no triangulation, no tolerance enlargement - `Add_s` pads
    by the shape tolerances)."""
    b = Bnd_Box()
    BRepBndLib.AddOptimal_s(shape, b, False, False)
    return tuple(b.Get())  # type: ignore[return-value]


def is_valid(shape: TopoDS_Shape) -> bool:
    """`BRepCheck_Analyzer` verdict (geometry controls on)."""
    return bool(BRepCheck_Analyzer(shape, True).IsValid())


def fix(shape: TopoDS_Shape) -> TopoDS_Shape:
    """`ShapeFix_Shape` pass: the repair for imported geometry, never for our own."""
    sf = ShapeFix_Shape(shape)
    sf.Perform()
    return sf.Shape()


def is_seam(edge: TopoDS_Edge, face: TopoDS_Face) -> bool:
    """True when `edge` is the seam of `face` (a closed periodic surface)."""
    return bool(BRep_Tool.IsClosed_s(edge, face))


__all__ = [
    "BooleanResult",
    "EdgeFeatureResult",
    "FeatureResult",
    "Vec3",
    "area",
    "as_list",
    "bbox",
    "box",
    "centre_of_mass",
    "chamfer",
    "common",
    "cone",
    "counts",
    "cut",
    "cylinder",
    "cylinder_sweep_deg",
    "draft",
    "fillet",
    "fix",
    "fuse",
    "inertia",
    "is_concave_cylinder",
    "is_seam",
    "is_valid",
    "loft",
    "make_face_from_points",
    "prism",
    "revolve",
    "shell",
    "sphere",
    "sweep",
    "transform",
    "unify",
    "unique_subshapes",
    "volume",
]
