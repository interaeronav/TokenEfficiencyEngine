"""Hidden-line removal: a body's edges as 2D segments, arcs and polylines in a view.

Facts this module is built on (A66 P0a/P5a, OCP 7.9.3, this Mac, 2026-09-02):

- `HLRBRep_Algo` + `HLRAlgo_Projector(gp_Ax2)` + `Update()` + `Hide()` + `HLRBRep_HLRToShape`
  answers in SIX compounds, and the counts are per compound under a NAMED projector, never
  guessed: F1 front (eye at -Y) `VCompound` 4 | `HCompound` 9 + `OutLineHCompound` 1; top
  5 | 5; right (eye at +X) 4 | 10 + 2. On a filleted part the sharp compound can be nearly
  empty while the tangent lines live in `Rg1LineVCompound` (W3, the 12-hole/96-fillet plate:
  V 9 + Rg1V 17 | H 91 + Rg1H 63 + OutH 36) - so a view is the UNION of the three visible
  compounds and the union of the three hidden ones; `PolyAlgo` was slower (105 ms vs 91) and
  fragmented 10x, so exact HLR is the only path. 0.2-3 ms per F1 view, 22 ms for W3.
- The projector's Z axis points TOWARD the eye (measured: a boss on the top of a box is
  visible under `gp_Dir(0, 0, 1)` and hidden under `(0, 0, -1)`), so `direction` here is
  "from the part to the viewer": front = (0, -1, 0), top = (0, 0, 1). The Ax2 is built with
  X = `right` = up x direction, which makes Y = direction x right = `up`, and the edges
  `HLRToShape` returns are ALREADY in that frame with z = 0: their X is the sheet's
  horizontal, their Y the sheet's vertical, in model millimetres.
- Projected edges keep a curve type: lines stay lines, a circle seen along its axis is a
  `GeomAbs_Circle` (full or split into arcs), a circle seen edge-on is a degree-1 B-spline
  through 15 collinear poles (collapsed here to ONE segment), an ellipse (iso views) is a
  `GeomAbs_Ellipse`; everything that is not a line or a circle becomes a polyline at
  `CHORD_MM` = 0.05 mm through `GCPnts_QuasiUniformDeflection`.
- A section is the body with one half-space removed (`BRepBuilderAPI_MakeFace(gp_Pln)` sized
  to the bounding box, `BRepPrimAPI_MakePrism`, one `BRepAlgoAPI_Cut`), then HLR of the cut
  body; the faces lying ON the plane are what gets hatched and their exact area is the
  `checks.section` number (F1 at x = 50: 500.000 mm2 in TWO faces; the stepped shaft
  lengthwise: 2 700.000 in one).

Determinism (rule 7): every primitive list is sorted on rounded coordinates, so the same
model in another process gives the same list and the writers can be byte-identical. OCP is
imported inside functions only.
"""

from __future__ import annotations

import itertools
import math
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from partkiln.document import CommandError

Vec3 = tuple[float, float, float]
Pt2 = tuple[float, float]
Box4 = tuple[float, float, float, float]

CHORD_MM = 0.05
VISIBLE_COMPOUNDS = ("VCompound", "Rg1LineVCompound", "OutLineVCompound")
HIDDEN_COMPOUNDS = ("HCompound", "Rg1LineHCompound", "OutLineHCompound")


# --------------------------------------------------------------------------- vectors


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Sequence[float], b: Sequence[float]) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _unit(v: Sequence[float], what: str) -> Vec3:
    n = math.sqrt(_dot(v, v))
    if n < 1e-12:
        raise CommandError(f"{what} is the zero vector; give a direction.", code="pk_needs")
    return (v[0] / n, v[1] / n, v[2] / n)


def _r6(x: float) -> float:
    return round(float(x), 6) + 0.0


# --------------------------------------------------------------------------- primitives


@dataclass(frozen=True)
class Segment:
    """A straight edge in view millimetres."""

    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def length(self) -> float:
        return math.hypot(self.x1 - self.x0, self.y1 - self.y0)

    @property
    def midpoint(self) -> Pt2:
        return (0.5 * (self.x0 + self.x1), 0.5 * (self.y0 + self.y1))

    @property
    def direction(self) -> Pt2:
        n = self.length
        return ((self.x1 - self.x0) / n, (self.y1 - self.y0) / n) if n > 0 else (0.0, 0.0)

    def bbox(self) -> Box4:
        return (
            min(self.x0, self.x1),
            min(self.y0, self.y1),
            max(self.x0, self.x1),
            max(self.y0, self.y1),
        )


@dataclass(frozen=True)
class Arc:
    """A circular arc, counter-clockwise from `a0` to `a1` degrees (y up); `a1 - a0 == 360`
    is a full circle."""

    cx: float
    cy: float
    r: float
    a0: float
    a1: float

    @property
    def full(self) -> bool:
        return self.a1 - self.a0 >= 360.0 - 1e-9

    @property
    def sweep(self) -> float:
        return self.a1 - self.a0

    def point(self, angle_deg: float) -> Pt2:
        a = math.radians(angle_deg)
        return (self.cx + self.r * math.cos(a), self.cy + self.r * math.sin(a))

    @property
    def start(self) -> Pt2:
        return self.point(self.a0)

    @property
    def end(self) -> Pt2:
        return self.point(self.a1)

    def contains_angle(self, angle_deg: float) -> bool:
        return (angle_deg - self.a0) % 360.0 <= self.sweep + 1e-9

    def bbox(self) -> Box4:
        pts = [self.start, self.end]
        for quadrant in (0.0, 90.0, 180.0, 270.0):
            if self.contains_angle(quadrant):
                pts.append(self.point(quadrant))
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))


@dataclass(frozen=True)
class Polyline:
    """A curve that is neither a line nor a circle, sampled at `CHORD_MM`."""

    points: tuple[Pt2, ...]

    def bbox(self) -> Box4:
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))

    def segments(self) -> list[Segment]:
        return [
            Segment(a[0], a[1], b[0], b[1])
            for a, b in zip(self.points, self.points[1:], strict=False)
        ]


Prim = Segment | Arc | Polyline


def prim_bbox(prims: Iterable[Prim]) -> Box4 | None:
    """The bounding box of a primitive list, or None when it is empty."""
    box: list[float] | None = None
    for p in prims:
        b = p.bbox()
        if box is None:
            box = list(b)
        else:
            box = [min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3])]
    return None if box is None else (box[0], box[1], box[2], box[3])


def _key(prim: Prim) -> tuple[Any, ...]:
    if isinstance(prim, Segment):
        return (0, _r6(prim.x0), _r6(prim.y0), _r6(prim.x1), _r6(prim.y1))
    if isinstance(prim, Arc):
        return (1, _r6(prim.cx), _r6(prim.cy), _r6(prim.r), _r6(prim.a0), _r6(prim.a1))
    return (2, tuple((_r6(x), _r6(y)) for x, y in prim.points))


def canonical(prim: Prim) -> Prim:
    """The same primitive with a direction that does not depend on the edge's parametrisation."""
    if isinstance(prim, Segment):
        a = (_r6(prim.x0), _r6(prim.y0))
        b = (_r6(prim.x1), _r6(prim.y1))
        return Segment(prim.x1, prim.y1, prim.x0, prim.y0) if b < a else prim
    if isinstance(prim, Polyline):
        first = (_r6(prim.points[0][0]), _r6(prim.points[0][1]))
        last = (_r6(prim.points[-1][0]), _r6(prim.points[-1][1]))
        return Polyline(tuple(reversed(prim.points))) if last < first else prim
    return prim


def sort_prims(prims: Iterable[Prim]) -> list[Prim]:
    return sorted((canonical(p) for p in prims), key=_key)


# --------------------------------------------------------------------------- the view frame


@dataclass(frozen=True)
class ViewFrame:
    """`direction` points from the part to the eye; `right`/`up` span the sheet."""

    direction: Vec3
    up: Vec3
    right: Vec3

    def to_view(self, p: Sequence[float]) -> Pt2:
        return (_dot(p, self.right), _dot(p, self.up))

    def vector(self, v: Sequence[float]) -> Pt2:
        """A model direction projected into the view plane (not normalised)."""
        return (_dot(v, self.right), _dot(v, self.up))

    def depth(self, p: Sequence[float]) -> float:
        return _dot(p, self.direction)

    def as_dict(self) -> dict[str, list[float]]:
        return {
            "direction": [round(c, 6) + 0.0 for c in self.direction],
            "up": [round(c, 6) + 0.0 for c in self.up],
            "right": [round(c, 6) + 0.0 for c in self.right],
        }


def view_frame(direction: Sequence[float], up: Sequence[float] = (0.0, 0.0, 1.0)) -> ViewFrame:
    """Orthonormalise (direction, up) into a right-handed frame: right = up x direction.

    `up` is projected into the view plane first, so a nearly-vertical iso direction still
    keeps world Z "up" on the sheet; an `up` parallel to the direction has no projection and
    is refused naming the fix.
    """
    n = _unit(direction, "the view direction")
    u = _unit(up, "the up vector")
    d = _dot(u, n)
    flat = (u[0] - d * n[0], u[1] - d * n[1], u[2] - d * n[2])
    if math.sqrt(_dot(flat, flat)) < 1e-9:
        raise CommandError(
            f"up {list(up)} is parallel to the view direction {list(direction)}; give an up "
            "vector that is not along the line of sight (for a top view use [0, 1, 0]).",
            code="pk_needs",
        )
    u = _unit(flat, "the up vector")
    right = _unit(_cross(u, n), "the right vector")
    return ViewFrame(n, u, right)


# --------------------------------------------------------------------------- projection


@dataclass
class Projection:
    """One HLR result: primitives in the view frame plus the per-compound counts."""

    frame: ViewFrame
    visible: list[Prim]
    hidden: list[Prim]
    compounds: dict[str, int]
    wall_ms: float

    @property
    def visible_edges(self) -> int:
        return sum(self.compounds[k] for k in VISIBLE_COMPOUNDS)

    @property
    def hidden_edges(self) -> int:
        return sum(self.compounds[k] for k in HIDDEN_COMPOUNDS)

    def bbox(self, include_hidden: bool = True) -> Box4 | None:
        return prim_bbox([*self.visible, *(self.hidden if include_hidden else [])])


def _edges(compound: Any) -> list[Any]:
    """Unique edges of an HLR compound (Law 20: `TopExp.MapShapes_s`, never explorer visits)."""
    from OCP.TopAbs import TopAbs_EDGE
    from OCP.TopExp import TopExp
    from OCP.TopoDS import TopoDS
    from OCP.TopTools import TopTools_IndexedMapOfShape

    if compound is None or compound.IsNull():
        return []
    m = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(compound, TopAbs_EDGE, m)
    return [TopoDS.Edge_s(m.FindKey(i)) for i in range(1, m.Extent() + 1)]


def _simplify(points: list[Pt2], tol: float = 1e-7) -> list[Pt2]:
    """Drop repeated points and interior points that are collinear with their neighbours
    (the edge-on circle's 15 collinear poles become two points)."""
    out: list[Pt2] = []
    for p in points:
        if out and math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) < 1e-9:
            continue
        if len(out) >= 2:
            a, b = out[-2], out[-1]
            ux, uy = b[0] - a[0], b[1] - a[1]
            vx, vy = p[0] - b[0], p[1] - b[1]
            lu, lv = math.hypot(ux, uy), math.hypot(vx, vy)
            straight = lu > 0 and lv > 0 and abs(ux * vy - uy * vx) / (lu * lv) < tol
            if straight and ux * vx + uy * vy > 0:
                out[-1] = p
                continue
        out.append(p)
    return out


def _sample(curve: Any, first: float, last: float, chord: float) -> list[Pt2]:
    from OCP.GCPnts import GCPnts_QuasiUniformDeflection

    d = GCPnts_QuasiUniformDeflection(curve, chord, first, last)
    if d.IsDone() and d.NbPoints() >= 2:
        pts = [(d.Value(i).X(), d.Value(i).Y()) for i in range(1, d.NbPoints() + 1)]
    else:  # a curve the deflection walker refuses: 32 uniform samples, still deterministic
        pts = []
        for i in range(33):
            p = curve.Value(first + (last - first) * i / 32.0)
            pts.append((p.X(), p.Y()))
    return _simplify(pts)


def _arc_of(curve: Any, first: float, last: float) -> Arc:
    circle = curve.Circle()
    loc = circle.Location()
    cx, cy, r = loc.X(), loc.Y(), circle.Radius()
    if last - first >= 2.0 * math.pi - 1e-9:
        return Arc(cx, cy, r, 0.0, 360.0)
    p0, p1, pm = curve.Value(first), curve.Value(last), curve.Value(0.5 * (first + last))
    a0 = math.degrees(math.atan2(p0.Y() - cy, p0.X() - cx)) % 360.0
    a1 = math.degrees(math.atan2(p1.Y() - cy, p1.X() - cx)) % 360.0
    am = math.degrees(math.atan2(pm.Y() - cy, pm.X() - cx)) % 360.0
    sweep = (a1 - a0) % 360.0
    if (am - a0) % 360.0 > sweep + 1e-9:
        # The parametrisation runs clockwise in the view (a circle whose axis points away
        # from the eye): the counter-clockwise arc starts at the other end.
        a0, a1 = a1, a0
        sweep = (a1 - a0) % 360.0
    if sweep < 1e-9:
        sweep = 360.0
    return Arc(cx, cy, r, a0, a0 + sweep)


def prim_of_edge(edge: Any, chord: float = CHORD_MM) -> Prim | None:
    """One projected edge as a Segment, an Arc or a Polyline (None for a degenerate edge)."""
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.GeomAbs import GeomAbs_Circle, GeomAbs_Line

    curve = BRepAdaptor_Curve(edge)
    first, last = curve.FirstParameter(), curve.LastParameter()
    kind = curve.GetType()
    if kind == GeomAbs_Line:
        p0, p1 = curve.Value(first), curve.Value(last)
        seg = Segment(p0.X(), p0.Y(), p1.X(), p1.Y())
        return seg if seg.length > 1e-9 else None
    if kind == GeomAbs_Circle:
        return _arc_of(curve, first, last)
    pts = _sample(curve, first, last, chord)
    if len(pts) < 2:
        return None
    if len(pts) == 2:
        seg = Segment(pts[0][0], pts[0][1], pts[1][0], pts[1][1])
        return seg if seg.length > 1e-9 else None
    return Polyline(tuple(pts))


def prims_of(compound: Any, chord: float = CHORD_MM) -> list[Prim]:
    out = [p for p in (prim_of_edge(e, chord) for e in _edges(compound)) if p is not None]
    return sort_prims(out)


def project(
    shape: Any,
    direction: Sequence[float],
    up: Sequence[float] = (0.0, 0.0, 1.0),
    chord: float = CHORD_MM,
) -> Projection:
    """Exact HLR of `shape` seen from `direction` (part -> eye) with `up` on the sheet.

    Visible = VCompound + Rg1LineVCompound + OutLineVCompound, hidden = the H triple; the
    per-compound unique edge counts are reported unchanged so a test can pin them under a
    named projector.
    """
    from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt
    from OCP.HLRAlgo import HLRAlgo_Projector
    from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape

    frame = view_frame(direction, up)
    started = time.perf_counter()
    algo = HLRBRep_Algo()
    algo.Add(shape)
    axes = gp_Ax2(gp_Pnt(0.0, 0.0, 0.0), gp_Dir(*frame.direction), gp_Dir(*frame.right))
    algo.Projector(HLRAlgo_Projector(axes))
    algo.Update()
    algo.Hide()
    to_shape = HLRBRep_HLRToShape(algo)
    compounds = {
        "VCompound": to_shape.VCompound(),
        "Rg1LineVCompound": to_shape.Rg1LineVCompound(),
        "OutLineVCompound": to_shape.OutLineVCompound(),
        "HCompound": to_shape.HCompound(),
        "Rg1LineHCompound": to_shape.Rg1LineHCompound(),
        "OutLineHCompound": to_shape.OutLineHCompound(),
    }
    counts = {name: len(_edges(c)) for name, c in compounds.items()}
    visible: list[Prim] = []
    hidden: list[Prim] = []
    for name in VISIBLE_COMPOUNDS:
        visible.extend(prims_of(compounds[name], chord))
    for name in HIDDEN_COMPOUNDS:
        hidden.extend(prims_of(compounds[name], chord))
    wall = (time.perf_counter() - started) * 1000.0
    return Projection(frame, sort_prims(visible), sort_prims(hidden), counts, wall)


# --------------------------------------------------------------------------- sections


def section_body(
    shape: Any, point: Sequence[float], normal: Sequence[float]
) -> tuple[Any, list[Any]]:
    """The body with its `+normal` half removed, and its faces lying ON the plane.

    The half-space is a prism of a plane face sized from the bounding box (its diagonal,
    doubled, plus the plane's distance to the box), so no constant has to be right. A plane
    that removes nothing or everything is refused: an empty section answers a different
    question (Law 11, read for a view).
    """
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
    from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
    from OCP.gp import gp_Dir, gp_Pln, gp_Pnt, gp_Vec

    from partkiln.brep import query, shapes

    n = _unit(normal, "the section plane normal")
    px, py, pz = (float(c) for c in point)
    x0, y0, z0, x1, y1, z1 = shapes.bbox(shape)
    centre = (0.5 * (x0 + x1), 0.5 * (y0 + y1), 0.5 * (z0 + z1))
    reach = 2.0 * math.dist((x0, y0, z0), (x1, y1, z1)) + math.dist((px, py, pz), centre) + 1.0
    face = BRepBuilderAPI_MakeFace(
        gp_Pln(gp_Pnt(px, py, pz), gp_Dir(*n)), -reach, reach, -reach, reach
    ).Face()
    half = BRepPrimAPI_MakePrism(face, gp_Vec(n[0] * reach, n[1] * reach, n[2] * reach)).Shape()
    cut = BRepAlgoAPI_Cut(shape, half)
    box = f"bbox [{x0:.3f}, {y0:.3f}, {z0:.3f}]..[{x1:.3f}, {y1:.3f}, {z1:.3f}]"
    where = f"[{px:.3f}, {py:.3f}, {pz:.3f}] normal [{n[0]:.3f}, {n[1]:.3f}, {n[2]:.3f}]"
    if not cut.IsDone():
        raise CommandError(
            f"the section at {where} failed in the boolean. Fix: check the body is valid "
            "(pk_check valid) and move the plane off a face.",
            code="pk_op_failed",
        )
    body = cut.Shape()
    on_plane = [
        f
        for f in query.faces(body)
        if f.surface_type == "plane"
        and f.normal is not None
        and _dot(f.normal, n) > 1.0 - 1e-6
        and abs(_dot((f.centroid[0] - px, f.centroid[1] - py, f.centroid[2] - pz), n)) < 1e-6
    ]
    if not on_plane:
        raise CommandError(
            f"the section plane at {where} cuts no material ({box}). Fix: put the plane point "
            "inside the bounding box, or flip its side with side: '-'.",
            code="pk_no_effect",
        )
    return body, on_plane


def face_rings(face: Any, frame: ViewFrame, chord: float = CHORD_MM) -> list[list[Pt2]]:
    """The closed rings of a face in view coordinates, outer ring first.

    Edges are walked in wire order with `BRepTools_WireExplorer`, each sampled on its 3D
    curve and reversed when the wire runs it backwards, so the ring is a polygon the hatch
    scanline can cross.
    """
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.BRepTools import BRepTools, BRepTools_WireExplorer
    from OCP.GCPnts import GCPnts_QuasiUniformDeflection
    from OCP.TopAbs import TopAbs_REVERSED, TopAbs_WIRE
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS

    outer = BRepTools.OuterWire_s(face)
    rings: list[list[Pt2]] = []
    ex = TopExp_Explorer(face, TopAbs_WIRE)
    while ex.More():
        wire = TopoDS.Wire_s(ex.Current())
        pts: list[Pt2] = []
        wex = BRepTools_WireExplorer(wire, face)
        while wex.More():
            edge = wex.Current()
            curve = BRepAdaptor_Curve(edge)
            d = GCPnts_QuasiUniformDeflection(
                curve, chord, curve.FirstParameter(), curve.LastParameter()
            )
            sampled = (
                [d.Value(i) for i in range(1, d.NbPoints() + 1)]
                if d.IsDone() and d.NbPoints() >= 2
                else [curve.Value(curve.FirstParameter()), curve.Value(curve.LastParameter())]
            )
            if edge.Orientation() == TopAbs_REVERSED:
                sampled.reverse()
            pts.extend(frame.to_view((p.X(), p.Y(), p.Z())) for p in sampled[:-1])
            wex.Next()
        ring = _simplify(pts)
        if len(ring) >= 3:
            if wire.IsSame(outer):
                rings.insert(0, ring)
            else:
                rings.append(ring)
        ex.Next()
    return rings


def hatch(
    faces: Sequence[Sequence[Sequence[Pt2]]], pitch: float, angle_deg: float = 45.0
) -> list[Segment]:
    """45-degree hatch lines clipped to each face's rings by the even-odd scanline rule.

    Each face is hatched on its own (section faces never overlap). A ring edge counts as a
    crossing when `lo <= t < hi` (half-open), which settles a line through a vertex the
    same way on both edges that meet there; the grid is anchored on absolute multiples of
    the pitch so two runs of the same model hatch identically.
    """
    if pitch <= 0:
        raise CommandError(f"hatch pitch must be > 0 mm, got {pitch}.", code="pk_needs")
    a = math.radians(angle_deg)
    d = (math.cos(a), math.sin(a))
    m = (-math.sin(a), math.cos(a))
    out: list[Segment] = []
    for rings in faces:
        ts = [p[0] * m[0] + p[1] * m[1] for ring in rings for p in ring]
        if not ts:
            continue
        tmin, tmax = min(ts), max(ts)
        k = math.floor(tmin / pitch)
        t = (k + 0.5) * pitch
        while t < tmax:
            crossings: list[float] = []
            for ring in rings:
                for i, pa in enumerate(ring):
                    pb = ring[(i + 1) % len(ring)]
                    ta = pa[0] * m[0] + pa[1] * m[1]
                    tb = pb[0] * m[0] + pb[1] * m[1]
                    if ta == tb:
                        continue
                    lo, hi = (ta, tb) if ta < tb else (tb, ta)
                    if not (lo <= t < hi):
                        continue
                    u = (t - ta) / (tb - ta)
                    px = pa[0] + u * (pb[0] - pa[0])
                    py = pa[1] + u * (pb[1] - pa[1])
                    crossings.append(px * d[0] + py * d[1])
            crossings.sort()
            for j in range(0, len(crossings) - 1, 2):
                s0, s1 = crossings[j], crossings[j + 1]
                if s1 - s0 > 1e-9:
                    out.append(
                        Segment(
                            t * m[0] + s0 * d[0],
                            t * m[1] + s0 * d[1],
                            t * m[0] + s1 * d[0],
                            t * m[1] + s1 * d[1],
                        )
                    )
            t += pitch
    return sort_prims(out)  # type: ignore[return-value]


# --------------------------------------------------------------------------- detail windows


def _clip_segment(seg: Segment, cx: float, cy: float, r: float) -> Segment | None:
    dx, dy = seg.x1 - seg.x0, seg.y1 - seg.y0
    fx, fy = seg.x0 - cx, seg.y0 - cy
    a = dx * dx + dy * dy
    if a < 1e-18:
        return None
    b = 2.0 * (fx * dx + fy * dy)
    c = fx * fx + fy * fy - r * r
    disc = b * b - 4.0 * a * c
    if disc < 0:
        return None
    root = math.sqrt(disc)
    s0 = max(0.0, (-b - root) / (2.0 * a))
    s1 = min(1.0, (-b + root) / (2.0 * a))
    if s1 - s0 <= 1e-9:
        return None
    return Segment(seg.x0 + s0 * dx, seg.y0 + s0 * dy, seg.x0 + s1 * dx, seg.y0 + s1 * dy)


def _clip_arc(arc: Arc, cx: float, cy: float, r: float) -> list[Arc]:
    d = math.hypot(arc.cx - cx, arc.cy - cy)
    if d + arc.r <= r + 1e-9:
        return [arc]
    if d >= r + arc.r - 1e-9 or d + r <= arc.r - 1e-9:
        return []
    phi = math.degrees(math.atan2(cy - arc.cy, cx - arc.cx))
    cos_alpha = (arc.r * arc.r + d * d - r * r) / (2.0 * arc.r * d)
    alpha = math.degrees(math.acos(max(-1.0, min(1.0, cos_alpha))))
    cuts = sorted({(a - arc.a0) % 360.0 for a in (phi - alpha, phi + alpha)} - {0.0})
    bounds = [0.0, *[c for c in cuts if c < arc.sweep - 1e-9], arc.sweep]
    pieces: list[Arc] = []
    for lo, hi in itertools.pairwise(bounds):
        if hi - lo <= 1e-9:
            continue
        piece = Arc(arc.cx, arc.cy, arc.r, arc.a0 + lo, arc.a0 + hi)
        mx, my = piece.point(0.5 * (piece.a0 + piece.a1))
        if math.hypot(mx - cx, my - cy) < r:
            pieces.append(piece)
    return pieces


def clip_to_circle(prims: Iterable[Prim], cx: float, cy: float, r: float) -> list[Prim]:
    """The parts of `prims` inside the circle window (a detail view's geometry)."""
    out: list[Prim] = []
    for prim in prims:
        if isinstance(prim, Segment):
            clipped = _clip_segment(prim, cx, cy, r)
            if clipped is not None:
                out.append(clipped)
        elif isinstance(prim, Arc):
            out.extend(_clip_arc(prim, cx, cy, r))
        else:
            for seg in prim.segments():
                clipped = _clip_segment(seg, cx, cy, r)
                if clipped is not None:
                    out.append(clipped)
    return sort_prims(out)


__all__ = [
    "CHORD_MM",
    "HIDDEN_COMPOUNDS",
    "VISIBLE_COMPOUNDS",
    "Arc",
    "Polyline",
    "Prim",
    "Projection",
    "Segment",
    "ViewFrame",
    "canonical",
    "clip_to_circle",
    "face_rings",
    "hatch",
    "prim_bbox",
    "prim_of_edge",
    "prims_of",
    "project",
    "section_body",
    "sort_prims",
    "view_frame",
]
