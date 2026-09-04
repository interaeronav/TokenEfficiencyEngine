"""A solved sketch becomes OCCT faces, placed on its plane: the sketch-to-solid door.

Every closed loop of the sketch becomes a wire (lines as edges between SHARED
vertices, arcs through `GC_MakeArcOfCircle`, circles as one closed edge); the
loop with the largest area is a face, the loops it contains are its holes,
and every other outer loop is a further face - so `{circle: 80}` next to
`{circle: 10}` is a ring, and two disjoint rectangles are two faces. Vertices
are shared on purpose: a loop that closes only because two corner points are
`coincident` is walked through the merged point, so the wire is closed
topologically, not just within tolerance.

Disjoint and nested are not the only two readings. Loops whose boundaries
genuinely CROSS - three overlapping profiles drawn as one dumbbell - are
neither, and asking `_inside(<one sampled point>, other)` about them answers
at random: the A66 defect B was a dumbbell whose two outer bulbs were
classified as a hole and a separate face, cutting exactly one circle out of
the plate and leaving a solid whose interior classified OUT. So a crossing is
now DETECTED before nesting is asked anything (`_Overlap`: two boundaries
that never meet cannot cross, and two that do meet are told apart by the area
they share - none is a touch, all of the smaller is a nesting, part of it is
the crossing), and every crossing cluster is FUSED into one region and
declared in the feature's `assumed` (Law 19: default and declare), because
one region is what a drawing of overlapping closed profiles means. Only a
fuse OCCT cannot do refuses, naming the two profiles (Law 6).

Frames. A sketch is drawn in its own (x, y); the frame says where that is in
the world: `XY` (x -> X, y -> Y, normal +Z), `XZ` (x -> X, y -> Z, normal -Y:
the right-hand rule, X x Z), `YZ` (x -> Y, y -> Z, normal +X), `plane:<name>`
(a datum from features/workplane.py) and `on:<face ref>` - the face's own
plane with its OUTWARD normal, origin at the projection of the world origin
onto that plane (so a hole "at (50, 30)" on the top of a plate at the origin
lands at world (50, 30), the F1/F2/F5 reading) unless the ref carries
`@centroid` or `@x,y,z`, and x along the projected world X (world Y when the
normal is along X). The frame is part of every extrude's diff (`frame`).

An open profile refuses with `pk_sketch_open` naming the gap in mm between
the two nearest dangling ends - "close the loop" is not a fix, "0.500 mm
between r.p3 and r.p0" is. OCP is imported inside the functions only.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from partkiln.document import CommandError
from partkiln.sketch.model import Arc, Circle, Line, Sketch

Vec3 = tuple[float, float, float]


def _sub(a: Sequence[float], b: Sequence[float]) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Sequence[float], b: Sequence[float]) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _unit(v: Sequence[float]) -> Vec3:
    n = math.sqrt(_dot(v, v))
    if n < 1e-12:
        raise CommandError("a frame axis cannot be the zero vector.", code="pk_needs")
    return (v[0] / n, v[1] / n, v[2] / n)


def _round3(v: Sequence[float]) -> list[float]:
    return [round(float(c), 3) + 0.0 for c in v]


@dataclass(frozen=True)
class Frame:
    """A right-handed frame: `origin`, unit `normal` (z) and unit `xdir`; y = n x x."""

    origin: Vec3
    normal: Vec3
    xdir: Vec3

    @property
    def ydir(self) -> Vec3:
        return _cross(self.normal, self.xdir)

    def to_world(self, x: float, y: float, z: float = 0.0) -> Vec3:
        o, n, u, v = self.origin, self.normal, self.xdir, self.ydir
        return (
            o[0] + x * u[0] + y * v[0] + z * n[0],
            o[1] + x * u[1] + y * v[1] + z * n[1],
            o[2] + x * u[2] + y * v[2] + z * n[2],
        )

    def to_local(self, p: Sequence[float]) -> tuple[float, float, float]:
        d = _sub(p, self.origin)
        return (_dot(d, self.xdir), _dot(d, self.ydir), _dot(d, self.normal))

    def shifted(self, along_normal: float) -> Frame:
        n = self.normal
        o = (
            self.origin[0] + along_normal * n[0],
            self.origin[1] + along_normal * n[1],
            self.origin[2] + along_normal * n[2],
        )
        return Frame(o, n, self.xdir)

    def as_dict(self) -> dict[str, Any]:
        return {
            "origin": _round3(self.origin),
            "normal": _round3(self.normal),
            "x": _round3(self.xdir),
        }


def make_frame(
    origin: Sequence[float], normal: Sequence[float], xdir: Sequence[float] | None = None
) -> Frame:
    """A frame from a point and a normal; `xdir` is projected into the plane, or
    chosen as the projected world X (world Y when the normal is along X)."""
    n = _unit(normal)
    if xdir is None:
        xdir = (0.0, 1.0, 0.0) if abs(n[0]) > 0.999 else (1.0, 0.0, 0.0)
    d = _dot(xdir, n)
    projected = (xdir[0] - d * n[0], xdir[1] - d * n[1], xdir[2] - d * n[2])
    return Frame((float(origin[0]), float(origin[1]), float(origin[2])), n, _unit(projected))


NAMED_FRAMES: dict[str, Frame] = {
    "XY": Frame((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
    "XZ": Frame((0.0, 0.0, 0.0), (0.0, -1.0, 0.0), (1.0, 0.0, 0.0)),
    "YZ": Frame((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
}


def split_plane_ref(plane: str) -> tuple[str, str, str | None]:
    """'on:plate.end@centroid' -> ('on', 'plate.end', 'centroid'); 'XY' -> ('named', 'XY', None)."""
    text = str(plane)
    if text in NAMED_FRAMES:
        return "named", text, None
    if text.startswith("plane:"):
        return "datum", text[6:], None
    if text.startswith("on:"):
        ref, _, origin = text[3:].partition("@")
        return "on", ref, origin or None
    raise CommandError(
        f"plane {plane!r} is not a sketch plane. Use XY, XZ, YZ, plane:<name> or on:<face ref>.",
        code="pk_plane_missing",
    )


def face_frame(origin: Vec3, normal: Vec3, centroid: Vec3, at: str | None) -> Frame:
    """The frame of a face: outward normal, origin per `at` (None -> the world
    origin projected onto the plane; 'centroid'; 'x,y,z' projected)."""
    n = _unit(normal)
    if at is None:
        point: Vec3 = (0.0, 0.0, 0.0)
    elif at == "centroid":
        point = centroid
    else:
        parts = at.split(",")
        if len(parts) != 3:
            raise CommandError(
                f"a sketch origin is @centroid or @x,y,z; got @{at}.", code="pk_needs"
            )
        try:
            point = (float(parts[0]), float(parts[1]), float(parts[2]))
        except ValueError as exc:
            raise CommandError(f"@{at} is not three numbers (mm).", code="pk_needs") from exc
    d = _dot(_sub(point, centroid), n)
    projected = (point[0] - d * n[0], point[1] - d * n[1], point[2] - d * n[2])
    return make_frame(projected, n)


# --------------------------------------------------------------------------- loops


@dataclass
class Loop:
    tags: list[tuple[str, bool]]
    area: float  # signed, in the sketch's own orientation (CCW positive)
    is_circle: bool
    points: list[tuple[float, float]]  # chord vertices (or the circle centre)
    radius: float = 0.0


@dataclass
class Profile:
    """The faces (outer loop + holes each) with the sketch tag of every edge,
    and the frame they sit in. `edge_tags` maps `id`-independent OCCT hashes
    to tags; `edges` keeps the (tag, edge) pairs in a stable order."""

    frame: Frame
    faces: list[Any]
    edges: list[tuple[str, Any]] = field(default_factory=list)
    area_mm2: float = 0.0
    loops: int = 0
    assumed: dict[str, Any] = field(default_factory=dict)

    def edge_tag(self, edge: Any) -> str | None:
        for tag, e in self.edges:
            if e.IsSame(edge):
                return tag
        return None


def _dangling_gap(sketch: Sketch) -> str:
    """Name the two nearest dangling ends and their distance, for `pk_sketch_open`."""
    degree: dict[str, list[str]] = {}
    for curve in sketch.curves():
        if curve.construction or isinstance(curve, Circle):
            continue
        ends = (curve.a, curve.b) if isinstance(curve, Line) else (curve.start, curve.end)
        for end in ends:
            degree.setdefault(end, []).append(curve.tag)
    merged: set[str] = set()
    for c in sketch.constraints:
        if c.kind == "coincident" and len(c.refs) == 2 and c.refs[1] in degree:
            merged.update(c.refs)
    loose = [tag for tag, curves in degree.items() if len(curves) == 1 and tag not in merged]
    if len(loose) < 2:
        return "a curve ends at a junction where more than two curves meet"
    best = None
    for i, a in enumerate(loose):
        for b in loose[i + 1 :]:
            d = math.dist(sketch.xy(a), sketch.xy(b))
            if best is None or d < best[0]:
                best = (d, a, b)
    assert best is not None
    return f"{best[0]:.3f} mm gap between {best[1]} and {best[2]}"


def _loops(sketch: Sketch) -> list[Loop]:
    out: list[Loop] = []
    for loop in sketch.loops():
        first = sketch.entities[loop[0][0]]
        if len(loop) == 1 and isinstance(first, Circle):
            out.append(
                Loop(loop, math.pi * first.r * first.r, True, [sketch.xy(first.center)], first.r)
            )
            continue
        pts: list[tuple[float, float]] = []
        for tag, reversed_ in loop:
            curve = sketch.entities[tag]
            if isinstance(curve, Line):
                pts.append(sketch.xy(curve.b if reversed_ else curve.a))
            else:
                assert isinstance(curve, Arc)
                pts.append(sketch.xy(curve.end if reversed_ else curve.start))
        out.append(Loop(loop, sketch.loop_area(loop), False, pts))
    return out


def _representative(loop: Loop) -> tuple[float, float]:
    """A point ON the loop's boundary - a corner, or the circle's +x point.

    On the boundary, not inside it, so that a pair whose boundaries are known
    to stay apart can be classified by "how far is this point from that face":
    zero means inside, anything else means outside, with no third answer.
    """
    if loop.is_circle:
        cx, cy = loop.points[0]
        return (cx + loop.radius, cy)
    return loop.points[0]


# ------------------------------------------------------------------ crossing loops

_TOUCH_TOL = 1e-7  # mm: two boundaries nearer than this are taken to meet


def _loop_bbox(loop: Loop, sketch: Sketch) -> tuple[float, float, float, float]:
    """A CONSERVATIVE (xmin, ymin, xmax, ymax) for `loop`.

    An arc contributes its whole circle rather than its chord: a box that
    missed a bulge would rule out a crossing that is really there, and this
    box exists only to skip pairs that cannot possibly meet.
    """
    if loop.is_circle:
        cx, cy = loop.points[0]
        r = loop.radius
        return (cx - r, cy - r, cx + r, cy + r)
    xs = [x for x, _ in loop.points]
    ys = [y for _, y in loop.points]
    for tag, _reversed in loop.tags:
        curve = sketch.entities[tag]
        if isinstance(curve, Arc):
            cx, cy = sketch.xy(curve.center)
            sx, sy = sketch.xy(curve.start)
            r = math.hypot(sx - cx, sy - cy)
            xs += [cx - r, cx + r]
            ys += [cy - r, cy + r]
    return (min(xs), min(ys), max(xs), max(ys))


def _boxes_apart(a: tuple[float, ...], b: tuple[float, ...]) -> bool:
    return (
        a[2] < b[0] - _TOUCH_TOL
        or b[2] < a[0] - _TOUCH_TOL
        or a[3] < b[1] - _TOUCH_TOL
        or b[3] < a[1] - _TOUCH_TOL
    )


def _nest(
    loops: list[Loop], clusters: list[list[int]], overlap: _Overlap
) -> list[tuple[int, list[int]]]:
    """(outer cluster, [hole clusters]): a region is a hole of the SMALLEST
    region containing it, exactly as before - but containment is the measured
    `overlap.inside`, never a point sampled into a chord polygon.

    One member decides for its whole cluster, which is sound: a loop that
    crosses another cannot also cross their container, or container and
    crossed loop would be one cluster.
    """
    areas = [sum(abs(loops[i].area) for i in c) for c in clusters]
    order = sorted(range(len(clusters)), key=lambda k: -areas[k])

    def held(inner: int, outer: int) -> bool:
        member = clusters[inner][0]
        return any(overlap.inside(member, i) for i in clusters[outer])

    parent: dict[int, int | None] = {}
    for pos, k in enumerate(order):
        parent[k] = None
        for j in reversed(order[:pos]):  # smallest container wins: walk from the smallest up
            if held(k, j):
                parent[k] = j
                break
    depth: dict[int, int] = {}
    for k in range(len(clusters)):
        d, up = 0, parent[k]
        while up is not None:
            d, up = d + 1, parent[up]
        depth[k] = d
    return [
        (k, [h for h in range(len(clusters)) if parent[h] == k]) for k in order if depth[k] % 2 == 0
    ]


# --------------------------------------------------------------------------- OCCT


def _merged_points(sketch: Sketch) -> dict[str, str]:
    parent: dict[str, str] = {p.tag: p.tag for p in sketch.points()}

    def find(tag: str) -> str:
        while parent[tag] != tag:
            parent[tag] = parent[parent[tag]]
            tag = parent[tag]
        return tag

    for c in sketch.constraints:
        if c.kind == "coincident" and len(c.refs) == 2 and c.refs[1] in parent:
            ra, rb = find(c.refs[0]), find(c.refs[1])
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
    return {tag: find(tag) for tag in parent}


class _Builder:
    def __init__(self, sketch: Sketch, frame: Frame) -> None:
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
        from OCP.gp import gp_Pnt

        self.sketch = sketch
        self.frame = frame
        self.merged = _merged_points(sketch)
        self._vertices: dict[str, Any] = {}
        self._mk_vertex = BRepBuilderAPI_MakeVertex
        self._pnt = gp_Pnt
        self.edges: list[tuple[str, Any]] = []

    def pnt(self, tag: str) -> Any:
        x, y = self.sketch.xy(tag)
        return self._pnt(*self.frame.to_world(x, y))

    def vertex(self, tag: str) -> Any:
        root = self.merged[tag]
        v = self._vertices.get(root)
        if v is None:
            v = self._mk_vertex(self.pnt(root)).Vertex()
            self._vertices[root] = v
        return v

    def edge(self, tag: str, reversed_: bool) -> Any:
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
        from OCP.GC import GC_MakeArcOfCircle

        curve = self.sketch.entities[tag]
        if isinstance(curve, Line):
            a, b = (curve.b, curve.a) if reversed_ else (curve.a, curve.b)
            mk = BRepBuilderAPI_MakeEdge(self.vertex(a), self.vertex(b))
        else:
            assert isinstance(curve, Arc)
            cx, cy = self.sketch.xy(curve.center)
            sx, sy = self.sketch.xy(curve.start)
            r = math.hypot(sx - cx, sy - cy)
            a0 = math.atan2(sy - cy, sx - cx)
            half = 0.5 * self.sketch.sweep(curve)
            am = a0 + half if curve.ccw else a0 - half
            mid = self._pnt(*self.frame.to_world(cx + r * math.cos(am), cy + r * math.sin(am)))
            start, end = (curve.end, curve.start) if reversed_ else (curve.start, curve.end)
            geom = GC_MakeArcOfCircle(self.pnt(start), mid, self.pnt(end)).Value()
            mk = BRepBuilderAPI_MakeEdge(geom, self.vertex(start), self.vertex(end))
        if not mk.IsDone():
            raise CommandError(
                f"sketch {self.sketch.name}: entity {tag} cannot become an edge "
                "(zero length or a degenerate arc).",
                code="pk_op_failed",
            )
        e = mk.Edge()
        self.edges.append((tag, e))
        return e

    def circle_edge(self, tag: str) -> Any:
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
        from OCP.gp import gp_Ax2, gp_Circ, gp_Dir

        circle = self.sketch.entities[tag]
        assert isinstance(circle, Circle)
        cx, cy = self.sketch.xy(circle.center)
        centre = self._pnt(*self.frame.to_world(cx, cy))
        n, x = self.frame.normal, self.frame.xdir
        axis = gp_Ax2(centre, gp_Dir(*n), gp_Dir(*x))
        e = BRepBuilderAPI_MakeEdge(gp_Circ(axis, circle.r)).Edge()
        self.edges.append((tag, e))
        return e

    def wire(self, loop: Loop) -> Any:
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeWire

        mw = BRepBuilderAPI_MakeWire()
        if loop.is_circle:
            mw.Add(self.circle_edge(loop.tags[0][0]))
        else:
            # A CCW walk gives a face whose normal is the frame normal (the
            # direction "+" extrudes along); reverse a CW loop so every outer
            # wire is CCW and MakeFace does not flip the face under us.
            walk = loop.tags if loop.area >= 0 else [(t, not r) for t, r in reversed(loop.tags)]
            for tag, reversed_ in walk:
                mw.Add(self.edge(tag, reversed_))
        if not mw.IsDone():
            raise CommandError(
                f"sketch {self.sketch.name}: loop starting at {loop.tags[0][0]} does not chain "
                "into a wire (endpoints do not meet).",
                code="pk_sketch_open",
            )
        return mw.Wire()


_APART, _TOUCH, _CROSS, _I_IN_J, _J_IN_I = range(5)


class _Overlap:
    """How every pair of loops really sits - the question `nest_loops` used to
    answer by sampling one point per loop into a chord polygon.

    Nothing here is sampled. Boxes rule out pairs that cannot meet (an arc
    contributes its whole circle, so a bulge is never missed). For the rest,
    the two boundaries are measured: if they stay more than `_TOUCH_TOL`
    apart they cannot cross, and a point ON one boundary at zero distance
    from the other's face says which holds which. If they DO meet, the area
    they share decides - none is a touch (two circles tangent at a point stay
    two faces), all of the smaller one is a nesting (a hole tangent to its
    outer wire is still a hole), all of BOTH is the same region drawn twice,
    and anything else is the partial overlap that used to be classified at
    random and built a wrong solid in silence.

    Wires and faces are built once and cached; the crossing branch reuses them.
    """

    def __init__(self, sketch: Sketch, frame: Frame, loops: list[Loop]) -> None:
        self.sketch = sketch
        self.frame = frame
        self.loops = loops
        self.builder = _Builder(sketch, frame)
        self.boxes = [_loop_bbox(lp, sketch) for lp in loops]
        self._wires: dict[int, Any] = {}
        self._faces: dict[int, Any] = {}
        self._areas: dict[int, float] = {}
        self._edges: dict[int, list[tuple[str, Any]]] = {}
        self._rel: dict[tuple[int, int], int] = {}

    # -- the shapes, built once ------------------------------------------------

    def wire(self, i: int) -> Any:
        w = self._wires.get(i)
        if w is None:
            mark = len(self.builder.edges)
            w = self.builder.wire(self.loops[i])
            self._edges[i] = list(self.builder.edges[mark:])
            self._wires[i] = w
        return w

    def edges_of(self, i: int) -> list[tuple[str, Any]]:
        self.wire(i)
        return self._edges[i]

    def face(self, i: int) -> Any:
        f = self._faces.get(i)
        if f is None:
            from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace

            mk = BRepBuilderAPI_MakeFace(self.wire(i), True)
            if not mk.IsDone():
                raise CommandError(
                    f"sketch {self.sketch.name}: the loop starting at "
                    f"{self.loops[i].tags[0][0]} is not planar or does not bound a face.",
                    code="pk_op_failed",
                )
            f = mk.Face()
            self._faces[i] = f
        return f

    def area(self, i: int) -> float:
        """The face's OCCT area - exact for arcs, unlike a chord polygon."""
        a = self._areas.get(i)
        if a is None:
            from partkiln.brep import shapes

            a = shapes.area(self.face(i))
            self._areas[i] = a
        return a

    # -- the measurements ------------------------------------------------------

    def _boundary_in_face(self, i: int, j: int) -> bool:
        """Is loop `i`'s boundary point inside face `j`? Only ever asked of a
        pair whose boundaries stay apart, so the distance is 0 or well clear."""
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
        from OCP.BRepExtrema import BRepExtrema_DistShapeShape
        from OCP.gp import gp_Pnt

        x, y = _representative(self.loops[i])
        v = BRepBuilderAPI_MakeVertex(gp_Pnt(*self.frame.to_world(x, y))).Vertex()
        dist = BRepExtrema_DistShapeShape(v, self.face(j))
        dist.Perform()
        return bool(dist.IsDone()) and dist.Value() <= _TOUCH_TOL

    def _measure(self, i: int, j: int) -> int:
        from OCP.BRepExtrema import BRepExtrema_DistShapeShape

        from partkiln.brep import shapes

        if _boxes_apart(self.boxes[i], self.boxes[j]):
            return _APART
        dist = BRepExtrema_DistShapeShape(self.wire(i), self.wire(j))
        dist.Perform()
        if not dist.IsDone() or dist.Value() > _TOUCH_TOL:
            if self._boundary_in_face(i, j):
                return _I_IN_J
            if self._boundary_in_face(j, i):
                return _J_IN_I
            return _APART
        ai, aj = self.area(i), self.area(j)
        tol = 1e-7 * max(min(ai, aj), 1.0)
        shared = shapes.area(shapes.common(self.face(i), self.face(j)).shape)
        if shared <= tol:
            return _TOUCH
        held_i, held_j = shared >= ai - tol, shared >= aj - tol
        if held_i and held_j:
            return _CROSS  # the same region drawn twice: one region is the answer
        if held_i:
            return _I_IN_J
        if held_j:
            return _J_IN_I
        return _CROSS

    def relation(self, i: int, j: int) -> int:
        key = (i, j) if i < j else (j, i)
        rel = self._rel.get(key)
        if rel is None:
            rel = self._measure(*key)
            self._rel[key] = rel
        return rel

    def inside(self, i: int, j: int) -> bool:
        """Is loop `i` inside loop `j`? False for a pair that crosses or only
        touches - neither holds the other."""
        if i == j:
            return False
        rel = self.relation(i, j)
        return rel == (_I_IN_J if i < j else _J_IN_I)

    def self_crossing(self, i: int) -> tuple[str, str, tuple[float, float, float]] | None:
        """The two curve tags of loop `i` that cross each other, and where.

        A loop that crosses ITSELF is closed, so `sketch.closed()` passes and
        every pairwise measurement above is about a *different* loop - yet the
        face OCCT makes of it is invalid and its area is the SIGNED sum of the
        lobes: a symmetric bowtie reads 0 mm2 and an asymmetric one reads the
        difference, not the figure the user drew. Nothing downstream notices
        (an extrude of it answered `status: ok, volume 0.0`), so it is caught
        here. `ShapeAnalysis_Wire.CheckSelfIntersection` is the detector -
        measured False on every legitimate fixture, tangent-arc slots included.
        """
        from OCP.IntRes2d import IntRes2d_SequenceOfIntersectionPoint
        from OCP.ShapeAnalysis import ShapeAnalysis_Wire
        from OCP.TColgp import TColgp_SequenceOfPnt
        from OCP.TColStd import TColStd_SequenceOfReal

        wire = self.wire(i)
        saw = ShapeAnalysis_Wire(wire, self.face(i), _TOUCH_TOL)
        if not saw.CheckSelfIntersection():
            return None
        data = saw.WireData()
        tags = self.edges_of(i)

        def tag_of(num: int) -> str:
            edge = data.Edge(num)
            return next((t for t, e in tags if e.IsSame(edge)), f"edge {num}")

        n = data.NbEdges()
        for a in range(1, n + 1):
            for b in range(a, n + 1):
                pts2d = IntRes2d_SequenceOfIntersectionPoint()
                pts3d = TColgp_SequenceOfPnt()
                errs = TColStd_SequenceOfReal()
                hit = (
                    saw.CheckIntersectingEdges(a, pts2d, pts3d, errs)
                    if a == b
                    else saw.CheckIntersectingEdges(a, b, pts2d, pts3d, errs)
                )
                if hit and pts3d.Length():
                    p = pts3d.Value(1)
                    x, y, _ = self.frame.to_local((p.X(), p.Y(), p.Z()))
                    return (tag_of(a), tag_of(b), (round(x, 3), round(y, 3), 0.0))
        first = self.loops[i].tags[0][0]
        return (first, first, (0.0, 0.0, 0.0))

    def clusters(self) -> list[list[int]]:
        """Loops grouped by "crosses, directly or through another"."""
        n = len(self.loops)
        parent = list(range(n))

        def find(a: int) -> int:
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        for i in range(n):
            for j in range(i + 1, n):
                if self.relation(i, j) == _CROSS:
                    ra, rb = find(i), find(j)
                    if ra != rb:
                        parent[max(ra, rb)] = min(ra, rb)
        groups: dict[int, list[int]] = {}
        for i in range(n):
            groups.setdefault(find(i), []).append(i)
        return [groups[k] for k in sorted(groups)]


def _cannot_union(overlap: _Overlap, cluster: Sequence[int]) -> str:
    tags = [overlap.loops[i].tags[0][0] for i in cluster]
    return (
        f"sketch {overlap.sketch.name}: the overlapping profiles {tags[0]} and {tags[1]} could "
        "not be unioned into one region. Move one so they no longer overlap, or draw the outline "
        "you want as a single closed loop."
    )


def _surviving(tagged: Sequence[tuple[str, Any]], hmap: Any, shape: Any) -> list[tuple[str, Any]]:
    """The tagged edges again, after a boolean: each one followed to its
    successors and kept only if that successor is still in `shape`, so
    `side.<tag>` still names the wall a sketch entity swept."""
    from OCP.TopAbs import TopAbs_EDGE
    from OCP.TopoDS import TopoDS

    from partkiln.brep import history, shapes

    # `unique_subshapes` downcasts; a history successor does not, and an
    # undowncast TopoDS_Shape blows up inside TopExp.FirstVertex_s later, so
    # the surviving edge is taken from the map rather than from the history.
    present = shapes.unique_subshapes(shape, TopAbs_EDGE)
    out: list[tuple[str, Any]] = []
    for tag, edge in tagged:
        for succ in history.follow(edge, [hmap]):
            if succ.ShapeType() != TopAbs_EDGE:
                continue
            here = next((q for q in present if q.IsSame(succ)), None)
            if here is None:
                continue
            if not any(t == tag and e.IsSame(here) for t, e in out):
                out.append((tag, TopoDS.Edge_s(here)))
    return out


def _region(overlap: _Overlap, cluster: Sequence[int]) -> tuple[list[Any], list[tuple[str, Any]]]:
    """One planar region from a cluster: the loop itself when it crosses
    nothing, else the FUSE of the crossing loops - the reading a drawing of
    overlapping closed profiles means."""
    from OCP.TopAbs import TopAbs_FACE

    from partkiln.brep import history, shapes

    faces = [overlap.face(i) for i in cluster]
    tagged = [pair for i in cluster for pair in overlap.edges_of(i)]
    if len(faces) == 1:
        return faces, tagged
    fused = shapes.fuse(faces)
    if not fused.is_done:
        raise CommandError(_cannot_union(overlap, cluster), code="pk_op_failed")
    shape, unified = shapes.unify(fused.shape)
    out = shapes.unique_subshapes(shape, TopAbs_FACE)
    if not out:
        raise CommandError(_cannot_union(overlap, cluster), code="pk_op_failed")
    hmap = history.from_algo(fused.history).merge(unified)
    return out, _surviving(tagged, hmap, shape)


def _compound(faces: Sequence[Any]) -> Any:
    from OCP.BRep import BRep_Builder
    from OCP.TopoDS import TopoDS_Compound

    comp = TopoDS_Compound()
    mk = BRep_Builder()
    mk.MakeCompound(comp)
    for f in faces:
        mk.Add(comp, f)
    return comp


def _region_profile(
    sketch: Sketch, frame: Frame, loops: list[Loop], overlap: _Overlap, clusters: list[list[int]]
) -> Profile:
    """The profile when some loops cross: every cluster fused into one region,
    regions nested as loops were, and the union DECLARED (Law 19)."""
    from OCP.TopAbs import TopAbs_FACE

    from partkiln.brep import history, shapes

    faces: list[Any] = []
    edges: list[tuple[str, Any]] = []
    total = 0.0
    for outer_k, hole_ks in _nest(loops, clusters, overlap):
        outer_faces, tagged = _region(overlap, clusters[outer_k])
        holes: list[Any] = []
        for hk in hole_ks:
            hole_faces, hole_edges = _region(overlap, clusters[hk])
            holes.extend(hole_faces)
            tagged = [*tagged, *hole_edges]
        if holes:
            base = outer_faces[0] if len(outer_faces) == 1 else _compound(outer_faces)
            res = shapes.cut(base, holes)
            if not res.is_done:
                raise CommandError(
                    f"sketch {sketch.name}: the loops inside "
                    f"{loops[clusters[outer_k][0]].tags[0][0]} could not be cut from it as holes. "
                    "Move them clear of its boundary, or draw the outline as a single loop.",
                    code="pk_op_failed",
                )
            shape, unified = shapes.unify(res.shape)
            outer_faces = shapes.unique_subshapes(shape, TopAbs_FACE)
            tagged = _surviving(tagged, history.from_algo(res.history).merge(unified), shape)
        faces.extend(outer_faces)
        edges.extend(tagged)
        total += sum(shapes.area(f) for f in outer_faces)
    merged = [c for c in clusters if len(c) > 1]
    names = ", ".join(loops[i].tags[0][0] for c in merged for i in c)
    count = sum(len(c) for c in merged)
    assumed = {
        "overlap": f"{count} overlapping loops ({names}) unioned into "
        f"{len(merged)} region{'' if len(merged) == 1 else 's'}"
    }
    return Profile(frame, faces, edges, round(total, 3), len(loops), assumed)


def build_profile(sketch: Sketch, frame: Frame) -> Profile:
    """Faces from every closed loop of `sketch`, placed in `frame` (mm).

    Loops that CROSS are detected first and fused into one region each, with
    the union declared in `Profile.assumed` - never classified as nested or
    disjoint by a sampled point, which is how defect B built a wrong solid in
    silence. Refuses `pk_sketch_open` (naming the gap) when any drawn curve is
    off a closed loop, and `pk_needs` when the sketch has no curves at all.
    """
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
    from OCP.ShapeFix import ShapeFix_Face
    from OCP.TopoDS import TopoDS

    if sketch.solution is None:
        sketch.solve()
    if not sketch.curves():
        raise CommandError(
            f"sketch {sketch.name} has no curves to make a profile from.", code="pk_needs"
        )
    if not sketch.closed():
        raise CommandError(
            f"sketch {sketch.name} is not a closed profile: {_dangling_gap(sketch)}. "
            "Make the ends coincident (constraints: [{c: coincident, a: <p>, b: <q>}]) or "
            "close the loop with another line.",
            code="pk_sketch_open",
        )
    loops = _loops(sketch)
    if not loops:
        raise CommandError(f"sketch {sketch.name} has no closed loop.", code="pk_sketch_open")
    overlap = _Overlap(sketch, frame, loops)
    for i, loop in enumerate(loops):
        crossing = overlap.self_crossing(i)
        if crossing is not None:
            a, b, (x, y, _z) = crossing
            where = f"{a} crosses {b}" if a != b else f"{a} crosses itself"
            raise CommandError(
                f"sketch {sketch.name}: the loop starting at {loop.tags[0][0]} crosses itself "
                f"({where} at ({x:g}, {y:g}) mm), so its area is the signed sum of its lobes, "
                "not the figure drawn. Split it into separate closed loops, or move a point so "
                "the boundary no longer crosses.",
                code="pk_sketch_open",
            )
    clusters = overlap.clusters()
    if any(len(c) > 1 for c in clusters):
        return _region_profile(sketch, frame, loops, overlap, clusters)
    builder = _Builder(sketch, frame)
    faces: list[Any] = []
    total = 0.0
    for outer_k, hole_ks in _nest(loops, clusters, overlap):
        outer = loops[clusters[outer_k][0]]
        holes = [loops[clusters[k][0]] for k in hole_ks]
        mk = BRepBuilderAPI_MakeFace(builder.wire(outer), True)
        for hole in holes:
            mk.Add(builder.wire(hole))
        if not mk.IsDone():
            raise CommandError(
                f"sketch {sketch.name}: the loop starting at {outer.tags[0][0]} is not planar "
                "or does not bound a face.",
                code="pk_op_failed",
            )
        face = mk.Face()
        if holes:  # inner wires must run against the outer one; ShapeFix knows how
            fixer = ShapeFix_Face(face)
            fixer.FixOrientation()
            face = TopoDS.Face_s(fixer.Face())
        faces.append(face)
        total += abs(outer.area) - sum(abs(h.area) for h in holes)
    return Profile(frame, faces, list(builder.edges), round(total, 3), len(loops))


def build_path(sketch: Sketch, frame: Frame) -> Any:
    """An OPEN sketch (one chain of lines/arcs) as a wire - a sweep path."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeWire

    if sketch.solution is None:
        sketch.solve()
    curves = [c for c in sketch.curves() if not c.construction]
    if not curves:
        raise CommandError(f"sketch {sketch.name} has no curves for a path.", code="pk_needs")
    if any(isinstance(c, Circle) for c in curves):
        raise CommandError(
            f"sketch {sketch.name}: a sweep path is an open chain of lines and arcs, not a circle.",
            code="pk_needs",
        )
    builder = _Builder(sketch, frame)
    merged = builder.merged
    ends: dict[str, list[str]] = {}
    for c in curves:
        a, b = (c.a, c.b) if isinstance(c, Line) else (c.start, c.end)  # type: ignore[union-attr]
        ends.setdefault(merged[a], []).append(c.tag)
        ends.setdefault(merged[b], []).append(c.tag)
    starts = [p for p, tags in ends.items() if len(tags) == 1]
    if len(starts) != 2:
        raise CommandError(
            f"sketch {sketch.name}: a path has exactly two free ends; found {len(starts)}.",
            code="pk_needs",
        )
    node = min(starts)
    remaining = {c.tag: c for c in curves}
    mw = BRepBuilderAPI_MakeWire()
    while remaining:
        nxt = [t for t in ends.get(node, []) if t in remaining]
        if not nxt:
            raise CommandError(
                f"sketch {sketch.name}: the path breaks at {node}.", code="pk_sketch_open"
            )
        curve = remaining.pop(nxt[0])
        a, b = (curve.a, curve.b) if isinstance(curve, Line) else (curve.start, curve.end)  # type: ignore[union-attr]
        reversed_ = merged[a] != node
        mw.Add(builder.edge(curve.tag, reversed_))
        node = merged[a] if reversed_ else merged[b]
    return mw.Wire()


__all__ = [
    "NAMED_FRAMES",
    "Frame",
    "Loop",
    "Profile",
    "build_path",
    "build_profile",
    "face_frame",
    "make_frame",
    "split_plane_ref",
]
