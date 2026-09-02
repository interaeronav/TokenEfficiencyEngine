"""A solved sketch becomes OCCT faces, placed on its plane: the sketch-to-solid door.

Every closed loop of the sketch becomes a wire (lines as edges between SHARED
vertices, arcs through `GC_MakeArcOfCircle`, circles as one closed edge); the
loop with the largest area is a face, the loops it contains are its holes,
and every other outer loop is a further face - so `{circle: 80}` next to
`{circle: 10}` is a ring, and two disjoint rectangles are two faces. Vertices
are shared on purpose: a loop that closes only because two corner points are
`coincident` is walked through the merged point, so the wire is closed
topologically, not just within tolerance.

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


def _inside(point: tuple[float, float], loop: Loop) -> bool:
    if loop.is_circle:
        return math.dist(point, loop.points[0]) < loop.radius
    x, y = point
    inside = False
    pts = loop.points
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        if (y0 > y) != (y1 > y):
            xi = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < xi:
                inside = not inside
    return inside


def _representative(loop: Loop) -> tuple[float, float]:
    if loop.is_circle:
        cx, cy = loop.points[0]
        return (cx + loop.radius, cy)
    return loop.points[0]


def nest_loops(loops: list[Loop]) -> list[tuple[Loop, list[Loop]]]:
    """(outer, [holes]) groups: a loop is a hole of the smallest loop containing it."""
    ordered = sorted(loops, key=lambda lp: -abs(lp.area))
    parent: dict[int, int | None] = {}
    for i, lp in enumerate(ordered):
        parent[i] = None
        for j in range(i - 1, -1, -1):  # smallest container wins: walk from the smallest up
            if _inside(_representative(lp), ordered[j]):
                parent[i] = j
                break
    depth: dict[int, int] = {}
    for i in range(len(ordered)):
        d, p = 0, parent[i]
        while p is not None:
            d, p = d + 1, parent[p]
        depth[i] = d
    groups: list[tuple[Loop, list[Loop]]] = []
    for i, lp in enumerate(ordered):
        if depth[i] % 2 == 0:
            holes = [ordered[k] for k in range(len(ordered)) if parent[k] == i]
            groups.append((lp, holes))
    return groups


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


def build_profile(sketch: Sketch, frame: Frame) -> Profile:
    """Faces from every closed loop of `sketch`, placed in `frame` (mm).

    Refuses `pk_sketch_open` (naming the gap) when any drawn curve is off a
    closed loop, and `pk_needs` when the sketch has no curves at all.
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
    builder = _Builder(sketch, frame)
    faces: list[Any] = []
    total = 0.0
    for outer, holes in nest_loops(loops):
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
    "nest_loops",
    "split_plane_ref",
]
