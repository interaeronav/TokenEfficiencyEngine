"""The sketch model: tagged entities, constraints by tag, driving and driven dims.

The one decision worth stating: every entity is TAGGED at creation and every
constraint refers to tags. FreeCAD's Sketcher indexes constraints by integer
and that is the documented way a model loses track of which line it meant
(A66 script, "Context"). Here `horizontal("r.0")` reads like the drawing and
survives the insertion of a line before it.

Two dimension words. A DRIVING dimension constrains - it is a row in the
solver. A DRIVEN dimension only measures: it is reported after the solve
and never moves anything, which is how a designer reads a derived length
without over-constraining the sketch. Nothing here imports OCP; the solver
(`partkiln.sketch.solver`) is scipy, and turning a solved sketch into wires
is P2's `profile.py`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from partkiln.document import CommandError

PLANES = ("XY", "XZ", "YZ")

CONSTRAINT_KINDS = (
    "coincident",
    "collinear",
    "concentric",
    "fix",
    "parallel",
    "perpendicular",
    "horizontal",
    "vertical",
    "equal",
    "tangent",
    "symmetric",
    "smooth",
)
DIM_KINDS = ("len", "dist", "angle", "dia", "rad")
CURVE_KINDS = ("line", "arc", "circle")


@dataclass(slots=True)
class Point:
    tag: str
    x: float
    y: float
    fixed: bool = False

    kind = "point"


@dataclass(slots=True)
class Line:
    tag: str
    a: str
    b: str
    construction: bool = False

    kind = "line"


@dataclass(slots=True)
class Arc:
    """Centre, start and end are point tags. The radius is |start - centre|;
    the solver keeps |end - centre| equal to it with one internal row, so an
    arc adds five degrees of freedom to a sketch, as it should."""

    tag: str
    center: str
    start: str
    end: str
    ccw: bool = True
    construction: bool = False

    kind = "arc"


@dataclass(slots=True)
class Circle:
    tag: str
    center: str
    r: float
    construction: bool = False

    kind = "circle"


Entity = Point | Line | Arc | Circle


@dataclass(frozen=True, slots=True)
class Constraint:
    kind: str
    refs: tuple[str, ...]
    tag: str

    def describe(self) -> str:
        return f"{self.tag} {self.kind}({', '.join(self.refs)})"


@dataclass(slots=True)
class Dimension:
    kind: str
    refs: tuple[str, ...]
    value: float
    tag: str
    driven: bool = False
    axis: str | None = None
    expr: str | None = None  # the source text when the value came from a parameter expression

    def describe(self) -> str:
        axis = f", axis={self.axis}" if self.axis else ""
        driven = " driven" if self.driven else ""
        return f"{self.tag} {self.kind}({', '.join(self.refs)}{axis})={self.value:g}{driven}"


def _check_plane(plane: str) -> str:
    text = str(plane)
    if text in PLANES or text.startswith("plane:") or text.startswith("on:"):
        return text
    raise CommandError(
        f"plane {plane!r} is not a sketch plane. Use XY, XZ, YZ, plane:<name> or on:<face ref>.",
        code="pk_plane_missing",
    )


@dataclass(slots=True)
class Sketch:
    """A 2D sketch in its own frame. `plane` is stored, not resolved - the
    part kernel (P2) turns it into a coordinate system when it extrudes."""

    name: str
    plane: str = "XY"
    entities: dict[str, Entity] = field(default_factory=dict)
    constraints: list[Constraint] = field(default_factory=list)
    dims: list[Dimension] = field(default_factory=list)
    solution: Any = None  # partkiln.sketch.solver.SolveReport, after solve()
    param_deps: set[str] = field(default_factory=set)
    _next_tag: int = 0

    def __post_init__(self) -> None:
        self.plane = _check_plane(self.plane)

    # -- entities -----------------------------------------------------------

    def add(self, entity: Entity) -> Entity:
        tag = entity.tag
        if not isinstance(tag, str) or not tag:
            raise CommandError("every sketch entity needs a tag (a short string).", code="pk_needs")
        if tag in self.entities:
            raise CommandError(
                f"tag {tag!r} is already used in sketch {self.name}. Tags are unique per sketch.",
                code="pk_ref_ambiguous",
            )
        if isinstance(entity, Line):
            self._need(entity.a, "point", f"line {tag}")
            self._need(entity.b, "point", f"line {tag}")
            if entity.a == entity.b:
                raise CommandError(f"line {tag} needs two different points.", code="pk_needs")
        elif isinstance(entity, Arc):
            for ref in (entity.center, entity.start, entity.end):
                self._need(ref, "point", f"arc {tag}")
            if entity.center in (entity.start, entity.end):
                raise CommandError(f"arc {tag}: the centre cannot be an endpoint.", code="pk_needs")
        elif isinstance(entity, Circle):
            self._need(entity.center, "point", f"circle {tag}")
            if entity.r <= 0:
                raise CommandError(
                    f"circle {tag}: radius must be > 0, got {entity.r:g}.", code="pk_needs"
                )
        elif not isinstance(entity, Point):
            raise CommandError(
                f"{type(entity).__name__} is not a sketch entity (point, line, arc, circle).",
                code="pk_bad_op",
            )
        self.entities[tag] = entity
        self.solution = None
        return entity

    def tags(self) -> set[str]:
        return {*self.entities, *(c.tag for c in self.constraints), *(d.tag for d in self.dims)}

    def entity(self, tag: str) -> Entity:
        entity = self.entities.get(tag)
        if entity is None:
            known = ", ".join(sorted(self.entities)) or "(none)"
            raise CommandError(
                f"no entity {tag!r} in sketch {self.name}. Entities: {known}.",
                code="pk_ref_unknown",
            )
        return entity

    def _need(self, tag: str, kind: str, for_what: str) -> Entity:
        entity = self.entity(tag)
        kinds = kind.split("|")
        if entity.kind not in kinds:
            raise CommandError(
                f"{for_what} needs a {kind.replace('|', ' or ')}; {tag!r} is a {entity.kind}.",
                code="pk_ref_unknown",
            )
        return entity

    def point(self, tag: str) -> Point:
        entity = self._need(tag, "point", "this")
        assert isinstance(entity, Point)
        return entity

    def points(self) -> list[Point]:
        return [e for e in self.entities.values() if isinstance(e, Point)]

    def curves(self) -> list[Line | Arc | Circle]:
        return [e for e in self.entities.values() if not isinstance(e, Point)]

    def xy(self, tag: str) -> tuple[float, float]:
        p = self.point(tag)
        return (p.x, p.y)

    def radius(self, tag: str) -> float:
        entity = self._need(tag, "arc|circle", "radius")
        if isinstance(entity, Circle):
            return entity.r
        assert isinstance(entity, Arc)
        cx, cy = self.xy(entity.center)
        sx, sy = self.xy(entity.start)
        return math.hypot(sx - cx, sy - cy)

    def sweep(self, arc: Arc) -> float:
        """The arc's turned angle in radians, (0, 2*pi]; start == end is a full turn."""
        cx, cy = self.xy(arc.center)
        sx, sy = self.xy(arc.start)
        ex, ey = self.xy(arc.end)
        a0 = math.atan2(sy - cy, sx - cx)
        a1 = math.atan2(ey - cy, ex - cx)
        turned = (a1 - a0) if arc.ccw else (a0 - a1)
        turned %= 2.0 * math.pi
        return turned if turned > 1e-12 else 2.0 * math.pi

    # -- constraints --------------------------------------------------------

    def _tag(self, prefix: str, tag: str | None) -> str:
        if tag is not None:
            if tag in self.tags():
                raise CommandError(
                    f"tag {tag!r} is already used in sketch {self.name}.",
                    code="pk_ref_ambiguous",
                )
            return str(tag)
        while True:
            self._next_tag += 1
            candidate = f"{prefix}{self._next_tag}"
            if candidate not in self.tags():
                return candidate

    def constrain(self, kind: str, *refs: str, tag: str | None = None) -> Constraint:
        """Add a constraint by tag. Validates arity and entity kinds NOW, so
        the refusal names the entity, not a solver row number later."""
        if kind not in CONSTRAINT_KINDS:
            raise CommandError(
                f"no constraint {kind!r}. Constraints: {', '.join(CONSTRAINT_KINDS)}.",
                code="pk_bad_op",
            )
        refs = tuple(str(r) for r in refs)
        self._validate_constraint(kind, refs)
        constraint = Constraint(kind, refs, self._tag("c", tag))
        self.constraints.append(constraint)
        if kind == "fix":
            self.point(refs[0]).fixed = True
        self.solution = None
        return constraint

    def _validate_constraint(self, kind: str, refs: tuple[str, ...]) -> None:
        kinds = [self.entity(r).kind for r in refs]
        what = f"{kind}({', '.join(refs)})"

        def refuse(needs: str) -> CommandError:
            got = ", ".join(f"{r} ({k})" for r, k in zip(refs, kinds, strict=True)) or "nothing"
            return CommandError(f"{what} needs {needs}; got {got}.", code="pk_ref_unknown")

        if kind == "coincident":
            if len(refs) != 2 or kinds[0] != "point" or kinds[1] not in ("point", *CURVE_KINDS):
                raise refuse("a point and a point, line, arc or circle")
        elif kind in ("collinear", "parallel", "perpendicular"):
            if len(refs) != 2 or kinds != ["line", "line"]:
                raise refuse("two lines")
        elif kind == "concentric":
            if len(refs) != 2 or any(k not in ("arc", "circle") for k in kinds):
                raise refuse("two arcs or circles")
        elif kind == "fix":
            if len(refs) != 1 or kinds != ["point"]:
                raise refuse("one point")
        elif kind in ("horizontal", "vertical"):
            if not (kinds == ["line"] or kinds == ["point", "point"]):
                raise refuse("one line, or two points")
        elif kind == "equal":
            if len(refs) != 2 or not (
                kinds == ["line", "line"] or all(k in ("arc", "circle") for k in kinds)
            ):
                raise refuse("two lines, or two arcs/circles")
        elif kind == "tangent":
            if len(refs) != 2 or sorted(kinds) not in (["arc", "line"], ["circle", "line"]):
                raise refuse("a line and an arc or circle")
        elif kind == "symmetric":
            if len(refs) != 3 or kinds != ["point", "point", "line"]:
                raise refuse("two points and the line they mirror about")
        elif kind == "smooth":
            if len(refs) != 2 or kinds != ["arc", "arc"]:
                raise refuse("two arcs")
            if self.shared_point(refs[0], refs[1]) is None:
                raise CommandError(
                    f"{what}: the arcs share no endpoint. Give them the same point tag at the "
                    "join, or make their endpoints coincident first. (G1 only; G2 curvature "
                    "continuity is later.)",
                    code="pk_ref_unknown",
                )
        if len(set(refs)) != len(refs):
            raise CommandError(f"{what} names the same entity twice.", code="pk_ref_unknown")

    def shared_point(self, a: str, b: str) -> tuple[str, str] | None:
        """The endpoint each of two arcs (or a line and an arc) has at their join:
        the same tag, or two tags made coincident. (tag_on_a, tag_on_b) or None."""
        ends_a = self._ends(a)
        ends_b = self._ends(b)
        for pa in ends_a:
            if pa in ends_b:
                return (pa, pa)
        for c in self.constraints:
            if c.kind != "coincident" or len(c.refs) != 2:
                continue
            x, y = c.refs
            if x in ends_a and y in ends_b:
                return (x, y)
            if y in ends_a and x in ends_b:
                return (y, x)
        return None

    def _ends(self, tag: str) -> tuple[str, ...]:
        entity = self.entity(tag)
        if isinstance(entity, Line):
            return (entity.a, entity.b)
        if isinstance(entity, Arc):
            return (entity.start, entity.end)
        return ()

    # -- dimensions ---------------------------------------------------------

    def dimension(
        self,
        kind: str,
        *refs: str,
        value: float,
        driven: bool = False,
        axis: str | None = None,
        tag: str | None = None,
        expr: str | None = None,
    ) -> Dimension:
        if kind not in DIM_KINDS:
            raise CommandError(
                f"no dimension {kind!r}. Dimensions: {', '.join(DIM_KINDS)}.", code="pk_bad_op"
            )
        refs = tuple(str(r) for r in refs)
        kinds = [self.entity(r).kind for r in refs]
        what = f"{kind}({', '.join(refs)})"

        def refuse(needs: str) -> CommandError:
            got = ", ".join(f"{r} ({k})" for r, k in zip(refs, kinds, strict=True)) or "nothing"
            return CommandError(f"{what} needs {needs}; got {got}.", code="pk_ref_unknown")

        if kind == "len" and kinds != ["line"]:
            raise refuse("one line")
        if kind == "dist" and not (
            kinds == ["point", "point"] or sorted(kinds) == ["line", "point"]
        ):
            raise refuse("two points, or a point and a line")
        if kind == "angle" and kinds != ["line", "line"]:
            raise refuse("two lines")
        if kind in ("dia", "rad") and (len(kinds) != 1 or kinds[0] not in ("arc", "circle")):
            raise refuse("one arc or circle")
        if axis is not None:
            axis = str(axis).upper()
            if axis not in ("X", "Y"):
                raise CommandError(f"{what}: axis must be X or Y, not {axis!r}.", code="pk_needs")
            if kinds != ["point", "point"]:
                raise CommandError(
                    f"{what}: an axis applies to a point-to-point distance only.", code="pk_needs"
                )
        value = float(value)
        if kind != "angle" and value < 0:
            raise CommandError(f"{what}: {value:g} is negative; a {kind} is >= 0.", code="pk_needs")
        if kind in ("dia", "rad", "len") and value == 0:
            raise CommandError(f"{what}: a {kind} of 0 collapses the entity.", code="pk_needs")
        dim = Dimension(kind, refs, value, self._tag("d", tag), bool(driven), axis, expr)
        self.dims.append(dim)
        self.solution = None
        return dim

    def dim(self, tag: str) -> Dimension:
        for d in self.dims:
            if d.tag == tag:
                return d
        known = ", ".join(d.tag for d in self.dims) or "(none)"
        raise CommandError(
            f"no dimension {tag!r} in sketch {self.name}. Dimensions: {known}.",
            code="pk_ref_unknown",
        )

    def set_dim(self, tag: str, value: float, *, expr: str | None = None) -> tuple[float, float]:
        """Change a dimension's value. Returns (old, new); the caller re-solves."""
        dim = self.dim(tag)
        old = dim.value
        if dim.kind != "angle" and float(value) <= 0:
            raise CommandError(
                f"{dim.tag}: {float(value):g} is not a {dim.kind} (> 0 needed).", code="pk_needs"
            )
        dim.value = float(value)
        dim.expr = expr
        self.solution = None
        return old, dim.value

    def measure(self, dim: Dimension) -> float:
        """What a dimension reads right now, in mm or degrees."""
        refs = dim.refs
        if dim.kind == "len":
            line = self.entity(refs[0])
            assert isinstance(line, Line)
            (ax, ay), (bx, by) = self.xy(line.a), self.xy(line.b)
            return math.hypot(bx - ax, by - ay)
        if dim.kind == "dist":
            kinds = [self.entity(r).kind for r in refs]
            if kinds == ["point", "point"]:
                (ax, ay), (bx, by) = self.xy(refs[0]), self.xy(refs[1])
                if dim.axis == "X":
                    return abs(bx - ax)
                if dim.axis == "Y":
                    return abs(by - ay)
                return math.hypot(bx - ax, by - ay)
            p, line = (refs[0], refs[1]) if kinds[0] == "point" else (refs[1], refs[0])
            return abs(self._side(line, p))
        if dim.kind == "angle":
            u = self._direction(refs[0])
            v = self._direction(refs[1])
            return math.degrees(math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1]))
        if dim.kind == "dia":
            return 2.0 * self.radius(refs[0])
        return self.radius(refs[0])

    def _direction(self, line_tag: str) -> tuple[float, float]:
        line = self.entity(line_tag)
        assert isinstance(line, Line)
        (ax, ay), (bx, by) = self.xy(line.a), self.xy(line.b)
        return (bx - ax, by - ay)

    def _side(self, line_tag: str, point_tag: str) -> float:
        line = self.entity(line_tag)
        assert isinstance(line, Line)
        (ax, ay), (bx, by) = self.xy(line.a), self.xy(line.b)
        px, py = self.xy(point_tag)
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy) or 1e-12
        return (dx * (py - ay) - dy * (px - ax)) / length

    # -- solving ------------------------------------------------------------

    def solve(self) -> Any:
        from partkiln.sketch.solver import solve

        self.solution = solve(self)
        return self.solution

    def dof(self) -> int:
        if self.solution is None:
            self.solve()
        return int(self.solution.dof)

    # -- topology -----------------------------------------------------------

    def loops(self) -> list[list[tuple[str, bool]]]:
        """Closed loops of non-construction curves, walked by shared endpoints.

        Each loop is [(curve tag, reversed)] in walking order. Endpoints are
        merged through `coincident` point-point constraints, so a profile
        drawn with separate but coincident corners still closes. Dangling
        runs are peeled first; a junction where three curves meet is left
        unwalked (the profile is then not closed, and P2 says so).
        """
        parent: dict[str, str] = {p.tag: p.tag for p in self.points()}

        def find(tag: str) -> str:
            while parent[tag] != tag:
                parent[tag] = parent[parent[tag]]
                tag = parent[tag]
            return tag

        for c in self.constraints:
            if c.kind == "coincident" and len(c.refs) == 2 and c.refs[1] in parent:
                ra, rb = find(c.refs[0]), find(c.refs[1])
                if ra != rb:
                    parent[max(ra, rb)] = min(ra, rb)

        loops: list[list[tuple[str, bool]]] = []
        adjacency: dict[str, list[tuple[str, str]]] = {}
        curves: dict[str, tuple[str, str]] = {}
        for curve in self.curves():
            if curve.construction:
                continue
            if isinstance(curve, Circle):
                loops.append([(curve.tag, False)])
                continue
            if isinstance(curve, Line):
                a, b = find(curve.a), find(curve.b)
            else:
                a, b = find(curve.start), find(curve.end)
            curves[curve.tag] = (a, b)
            adjacency.setdefault(a, []).append((curve.tag, b))
            adjacency.setdefault(b, []).append((curve.tag, a))

        alive = set(curves)
        changed = True
        while changed:  # peel dangling curves until every remaining node has degree >= 2
            changed = False
            for edges in adjacency.values():
                live = [e for e in edges if e[0] in alive]
                if len(live) == 1:
                    alive.discard(live[0][0])
                    changed = True
        visited: set[str] = set()
        for start_tag in sorted(alive):
            if start_tag in visited:
                continue
            a, b = curves[start_tag]
            loop: list[tuple[str, bool]] = [(start_tag, False)]
            visited.add(start_tag)
            node = b
            ok = True
            while node != a:
                nxt = [e for e in adjacency.get(node, []) if e[0] in alive and e[0] not in visited]
                if len(nxt) != 1 or len([e for e in adjacency[node] if e[0] in alive]) != 2:
                    ok = False
                    break
                tag, other = nxt[0]
                ca, _cb = curves[tag]
                loop.append((tag, ca != node))
                visited.add(tag)
                node = other
            if ok and len([e for e in adjacency[a] if e[0] in alive]) == 2:
                loops.append(loop)
        loops.sort(key=lambda lp: lp[0][0])
        return loops

    def loop_area(self, loop: list[tuple[str, bool]]) -> float:
        """Signed area (CCW positive): the shoelace over chord endpoints plus an
        exact circular-segment correction per arc, r^2/2 (theta - sin theta),
        added when the arc bulges outward of the walk and subtracted when it
        bulges inward. A lone circle is pi r^2."""
        if len(loop) == 1 and isinstance(self.entities[loop[0][0]], Circle):
            r = self.entities[loop[0][0]].r  # type: ignore[union-attr]
            return math.pi * r * r
        chords: list[tuple[float, float]] = []
        correction = 0.0
        for tag, reversed_ in loop:
            curve = self.entities[tag]
            if isinstance(curve, Line):
                first = curve.b if reversed_ else curve.a
                chords.append(self.xy(first))
            else:
                assert isinstance(curve, Arc)
                first = curve.end if reversed_ else curve.start
                chords.append(self.xy(first))
                theta = self.sweep(curve)
                r = self.radius(tag)
                segment = 0.5 * r * r * (theta - math.sin(theta))
                sign = 1.0 if curve.ccw else -1.0
                if reversed_:
                    sign = -sign
                correction += sign * segment
        shoelace = 0.0
        n = len(chords)
        for i in range(n):
            x0, y0 = chords[i]
            x1, y1 = chords[(i + 1) % n]
            shoelace += x0 * y1 - x1 * y0
        return 0.5 * shoelace + correction

    def closed(self) -> bool:
        """True when every non-construction curve lies on a closed loop."""
        drawn = {c.tag for c in self.curves() if not c.construction}
        if not drawn:
            return False
        on_loops = {tag for loop in self.loops() for tag, _ in loop}
        return drawn <= on_loops

    def area_mm2(self) -> float:
        """Area of the outer loop - the largest by magnitude. 0.0 when open."""
        areas = [abs(self.loop_area(loop)) for loop in self.loops()]
        return max(areas) if areas else 0.0

    # -- reporting ----------------------------------------------------------

    def report(self) -> dict[str, Any]:
        """The compact sketch report (D7): counts and verdicts, never coordinates."""
        if self.solution is None:
            self.solve()
        sol = self.solution
        driving = [d for d in self.dims if not d.driven]
        driven = [d for d in self.dims if d.driven]
        out: dict[str, Any] = {
            "entities": len(self.entities),
            "curves": len(self.curves()),
            "constraints": len(self.constraints) + len(driving),
            "dims": len(driving),
            "dof": sol.dof,
            "status": sol.status,
            "conflicts": list(sol.conflicts),
            "redundant": list(sol.redundant),
            "closed": self.closed(),
            "loops": len(self.loops()),
            "area_mm2": round(self.area_mm2(), 3),
            "frame": self.plane,
            "residual_max_mm": sol.residual_max_mm,
        }
        if driven:
            out["driven"] = {d.tag: round(self.measure(d), 6) for d in driven}
        return out

    def coordinates(self) -> dict[str, list[float]]:
        """Solved coordinates by tag (points [x, y]; circles [r]) - the
        fingerprint's input, and `tee_entity_detail`'s opt-in payload."""
        out: dict[str, list[float]] = {}
        for tag in sorted(self.entities):
            entity = self.entities[tag]
            if isinstance(entity, Point):
                out[tag] = [round(entity.x, 6) + 0.0, round(entity.y, 6) + 0.0]
            elif isinstance(entity, Circle):
                out[tag] = [round(entity.r, 6) + 0.0]
        return out
