"""The sketch solver: scipy least squares over tagged residual rows.

Written in-house because the obvious dependency, py-slvs (SolveSpace), is
GPL-3.0 with no linking exception and the lane ships MIT (A66 decision 1,
enforced by tests/test_licences.py). What it has to do is small: the
unknowns are the free point coordinates and the circle radii (fixed points
are constants, an arc's radius is |start - centre|), every constraint and
driving dimension is one or two residual rows in MILLIMETRES, and
`scipy.optimize.least_squares` drives them to zero from the model's current
coordinates - `lm` when the system is square or over-determined, `trf` when
it is under-determined.

Angular rows (parallel, perpendicular, angle, smooth) are in DEGREES and
counted as one millimetre per degree (`MM_PER_DEG`), so a residual of 1e-6
means the same thing in every row.

Every row carries an analytic gradient. That is what keeps a 40-entity /
60-row sketch under the 50 ms budget - a finite-difference Jacobian costs
n+1 residual evaluations per iteration - and it is what makes the
degrees-of-freedom count honest: DOF = unknowns - rank(J) at the solution,
raw, with no heuristic. The rank is a first-order fact: a constraint that
only bites at second order (equal lengths forcing two already-parallel
sides to line up) reports as redundant, exactly as SolveSpace reports it.

Verdicts: `ok` (converged, dof 0), `under` (converged, dof > 0), `over`
(converged, a constraint named whose rows add no rank), `conflict` (did not
converge; the conflicting set is found by leave-one-out re-solves, capped).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from partkiln.document import CommandError
from partkiln.sketch.model import Arc, Circle, Constraint, Dimension, Line, Point, Sketch

MM_PER_DEG = 1.0
DEG = 180.0 / math.pi
CONVERGED_MM = 1e-6
RANK_RTOL = 1e-7
# Leave-one-out re-solves are the price of naming a conflict; the rows with
# the largest residual go first and the search stops at this many, which
# keeps a 60-row sketch's conflict report under 200 ms.
CONFLICT_SEARCH_CAP = 16
_EPS = 1e-12

# A slot is (0, point index, axis) or (1, circle index).
Slot = tuple[int, int, int]


# -- terms: value and partials, in a fixed slot order ---------------------


class _Coord:
    __slots__ = ("a", "i", "slots")

    def __init__(self, i: int, a: int) -> None:
        self.i, self.a = i, a
        self.slots: tuple[Slot, ...] = ((0, i, a),)

    def __call__(self, P: list[list[float]], R: list[float]) -> tuple[float, tuple[float, ...]]:
        return P[self.i][self.a], (1.0,)


class _Radius:
    __slots__ = ("c", "slots")

    def __init__(self, c: int) -> None:
        self.c = c
        self.slots: tuple[Slot, ...] = ((1, c, 0),)

    def __call__(self, P: list[list[float]], R: list[float]) -> tuple[float, tuple[float, ...]]:
        return R[self.c], (1.0,)


class _Len:
    """|Pi - Pj|."""

    __slots__ = ("i", "j", "slots")

    def __init__(self, i: int, j: int) -> None:
        self.i, self.j = i, j
        self.slots: tuple[Slot, ...] = ((0, i, 0), (0, i, 1), (0, j, 0), (0, j, 1))

    def __call__(self, P: list[list[float]], R: list[float]) -> tuple[float, tuple[float, ...]]:
        pi, pj = P[self.i], P[self.j]
        dx, dy = pi[0] - pj[0], pi[1] - pj[1]
        L = math.sqrt(dx * dx + dy * dy)
        if L < _EPS:
            return 0.0, (0.0, 0.0, 0.0, 0.0)
        ux, uy = dx / L, dy / L
        return L, (ux, uy, -ux, -uy)


class _AxisDist:
    """|Pi[a] - Pj[a]|."""

    __slots__ = ("a", "i", "j", "slots")

    def __init__(self, i: int, j: int, a: int) -> None:
        self.i, self.j, self.a = i, j, a
        self.slots: tuple[Slot, ...] = ((0, i, a), (0, j, a))

    def __call__(self, P: list[list[float]], R: list[float]) -> tuple[float, tuple[float, ...]]:
        v = P[self.i][self.a] - P[self.j][self.a]
        s = 1.0 if v >= 0 else -1.0
        return abs(v), (s, -s)


def _dirs(P: list[list[float]], i: int, j: int, k: int, q: int) -> tuple[float, ...]:
    d1x, d1y = P[j][0] - P[i][0], P[j][1] - P[i][1]
    d2x, d2y = P[q][0] - P[k][0], P[q][1] - P[k][1]
    L1 = math.sqrt(d1x * d1x + d1y * d1y) or _EPS
    L2 = math.sqrt(d2x * d2x + d2y * d2y) or _EPS
    return d1x, d1y, d2x, d2y, L1, L2


class _Cross:
    """sin of the angle between directions i->j and k->l, in degrees (0 when parallel)."""

    __slots__ = ("i", "j", "k", "q", "slots")

    def __init__(self, i: int, j: int, k: int, q: int) -> None:
        self.i, self.j, self.k, self.q = i, j, k, q
        self.slots = (
            (0, i, 0), (0, i, 1), (0, j, 0), (0, j, 1),
            (0, k, 0), (0, k, 1), (0, q, 0), (0, q, 1),
        )  # fmt: skip

    def __call__(self, P: list[list[float]], R: list[float]) -> tuple[float, tuple[float, ...]]:
        d1x, d1y, d2x, d2y, L1, L2 = _dirs(P, self.i, self.j, self.k, self.q)
        N = L1 * L2
        r = (d1x * d2y - d1y * d2x) / N
        g1x = (d2y / N - r * d1x / (L1 * L1)) * DEG
        g1y = (-d2x / N - r * d1y / (L1 * L1)) * DEG
        g2x = (-d1y / N - r * d2x / (L2 * L2)) * DEG
        g2y = (d1x / N - r * d2y / (L2 * L2)) * DEG
        return r * DEG, (-g1x, -g1y, g1x, g1y, -g2x, -g2y, g2x, g2y)


class _Dot:
    """cos of the angle between directions i->j and k->l, in degrees (0 when perpendicular)."""

    __slots__ = ("i", "j", "k", "q", "slots")

    def __init__(self, i: int, j: int, k: int, q: int) -> None:
        self.i, self.j, self.k, self.q = i, j, k, q
        self.slots = (
            (0, i, 0), (0, i, 1), (0, j, 0), (0, j, 1),
            (0, k, 0), (0, k, 1), (0, q, 0), (0, q, 1),
        )  # fmt: skip

    def __call__(self, P: list[list[float]], R: list[float]) -> tuple[float, tuple[float, ...]]:
        d1x, d1y, d2x, d2y, L1, L2 = _dirs(P, self.i, self.j, self.k, self.q)
        N = L1 * L2
        r = (d1x * d2x + d1y * d2y) / N
        g1x = (d2x / N - r * d1x / (L1 * L1)) * DEG
        g1y = (d2y / N - r * d1y / (L1 * L1)) * DEG
        g2x = (d1x / N - r * d2x / (L2 * L2)) * DEG
        g2y = (d1y / N - r * d2y / (L2 * L2)) * DEG
        return r * DEG, (-g1x, -g1y, g1x, g1y, -g2x, -g2y, g2x, g2y)


class _Angle:
    """Signed angle from direction i->j to direction k->l, degrees, (-180, 180]."""

    __slots__ = ("i", "j", "k", "q", "slots")

    def __init__(self, i: int, j: int, k: int, q: int) -> None:
        self.i, self.j, self.k, self.q = i, j, k, q
        self.slots = (
            (0, i, 0), (0, i, 1), (0, j, 0), (0, j, 1),
            (0, k, 0), (0, k, 1), (0, q, 0), (0, q, 1),
        )  # fmt: skip

    def __call__(self, P: list[list[float]], R: list[float]) -> tuple[float, tuple[float, ...]]:
        d1x, d1y, d2x, d2y, L1, L2 = _dirs(P, self.i, self.j, self.k, self.q)
        C = d1x * d2y - d1y * d2x
        D = d1x * d2x + d1y * d2y
        Q = (L1 * L1) * (L2 * L2)
        theta = math.degrees(math.atan2(C, D))
        g1x = (D * d2y - C * d2x) / Q * DEG
        g1y = (-D * d2x - C * d2y) / Q * DEG
        g2x = (-D * d1y - C * d1x) / Q * DEG
        g2y = (D * d1x - C * d1y) / Q * DEG
        return theta, (-g1x, -g1y, g1x, g1y, -g2x, -g2y, g2x, g2y)


class _Side:
    """Signed distance of a point from line i->j (left positive). The point
    is Pk, or the midpoint of Pk and Pl when `l` is given; `absolute` takes
    the magnitude, for tangency at a distance."""

    __slots__ = ("absolute", "i", "j", "k", "q", "slots")

    def __init__(self, i: int, j: int, k: int, q: int | None = None, absolute: bool = False):
        self.i, self.j, self.k, self.q, self.absolute = i, j, k, q, absolute
        slots: list[Slot] = [(0, i, 0), (0, i, 1), (0, j, 0), (0, j, 1), (0, k, 0), (0, k, 1)]
        if q is not None:
            slots += [(0, q, 0), (0, q, 1)]
        self.slots = tuple(slots)

    def __call__(self, P: list[list[float]], R: list[float]) -> tuple[float, tuple[float, ...]]:
        pi, pj = P[self.i], P[self.j]
        if self.q is None:
            wx, wy = P[self.k][0] - pi[0], P[self.k][1] - pi[1]
        else:
            wx = 0.5 * (P[self.k][0] + P[self.q][0]) - pi[0]
            wy = 0.5 * (P[self.k][1] + P[self.q][1]) - pi[1]
        dx, dy = pj[0] - pi[0], pj[1] - pi[1]
        L = math.sqrt(dx * dx + dy * dy) or _EPS
        s = (dx * wy - dy * wx) / L
        gjx = wy / L - s * dx / (L * L)
        gjy = -wx / L - s * dy / (L * L)
        gcx, gcy = -dy / L, dx / L
        gix, giy = -(gjx + gcx), -(gjy + gcy)
        sign = 1.0
        if self.absolute and s < 0:
            sign, s = -1.0, -s
        if self.q is None:
            grads = (gix, giy, gjx, gjy, gcx, gcy)
        else:
            grads = (gix, giy, gjx, gjy, 0.5 * gcx, 0.5 * gcy, 0.5 * gcx, 0.5 * gcy)
        return s, tuple(sign * g for g in grads)


class _DotDir:
    """(Pl - Pk) projected on the unit direction of i->j, in mm."""

    __slots__ = ("i", "j", "k", "q", "slots")

    def __init__(self, i: int, j: int, k: int, q: int) -> None:
        self.i, self.j, self.k, self.q = i, j, k, q
        self.slots = (
            (0, i, 0), (0, i, 1), (0, j, 0), (0, j, 1),
            (0, k, 0), (0, k, 1), (0, q, 0), (0, q, 1),
        )  # fmt: skip

    def __call__(self, P: list[list[float]], R: list[float]) -> tuple[float, tuple[float, ...]]:
        pi, pj = P[self.i], P[self.j]
        dx, dy = pj[0] - pi[0], pj[1] - pi[1]
        wx, wy = P[self.q][0] - P[self.k][0], P[self.q][1] - P[self.k][1]
        L = math.sqrt(dx * dx + dy * dy) or _EPS
        v = (dx * wx + dy * wy) / L
        gdx = wx / L - v * dx / (L * L)
        gdy = wy / L - v * dy / (L * L)
        ux, uy = dx / L, dy / L
        return v, (-gdx, -gdy, gdx, gdy, -ux, -uy, ux, uy)


@dataclass(slots=True)
class _Row:
    owner: str  # constraint / dimension tag, or "<arc tag>:radius" for an internal row
    parts: list[tuple[float, Any, tuple[int, ...]]]  # (coefficient, term, columns per slot)
    target: float = 0.0
    wrap: bool = False  # angle rows: wrap the residual into (-180, 180]


@dataclass(slots=True)
class SolveReport:
    dof: int
    status: str
    conflicts: list[str]
    redundant: list[str]
    residual_max_mm: float
    iterations: int
    solved: dict[str, list[float]]
    radii: dict[str, float] = field(default_factory=dict)
    unknowns: int = 0
    rows: int = 0
    rank: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "dof": self.dof,
            "status": self.status,
            "conflicts": list(self.conflicts),
            "redundant": list(self.redundant),
            "residual_max_mm": self.residual_max_mm,
            "iterations": self.iterations,
            "solved": {k: [round(v, 6) + 0.0 for v in xy] for k, xy in self.solved.items()},
            "radii": {k: round(v, 6) + 0.0 for k, v in self.radii.items()},
        }


class _System:
    """The unknown vector, the rows, and their evaluation for one solve."""

    def __init__(self, sketch: Sketch, exclude: frozenset[str]) -> None:
        self.sketch = sketch
        self.exclude = exclude
        self.point_index: dict[str, int] = {}
        self.circle_index: dict[str, int] = {}
        self.P: list[list[float]] = []
        self.R: list[float] = []
        for entity in sketch.entities.values():
            if isinstance(entity, Point):
                self.point_index[entity.tag] = len(self.P)
                self.P.append([entity.x, entity.y])
            elif isinstance(entity, Circle):
                self.circle_index[entity.tag] = len(self.R)
                self.R.append(entity.r)
        # A `fix` constraint makes its point a constant; excluding the
        # constraint (leave-one-out) frees the point again.
        fixed = {e.tag for e in sketch.entities.values() if isinstance(e, Point) and e.fixed}
        for c in sketch.constraints:
            if c.kind == "fix" and c.tag not in exclude:
                fixed.add(c.refs[0])
        for c in sketch.constraints:
            if c.kind == "fix" and c.tag in exclude:
                fixed.discard(c.refs[0])
        self.columns: dict[Slot, int] = {}
        self.free: list[Slot] = []
        for tag, i in self.point_index.items():
            if tag in fixed:
                continue
            for a in (0, 1):
                self.columns[(0, i, a)] = len(self.free)
                self.free.append((0, i, a))
        for c in self.circle_index.values():
            self.columns[(1, c, 0)] = len(self.free)
            self.free.append((1, c, 0))
        self.rows: list[_Row] = []
        self._build_rows()
        self.n = len(self.free)
        self.m = len(self.rows)
        self._cache_x: np.ndarray | None = None
        self._cache: tuple[np.ndarray, np.ndarray] | None = None

    # -- rows ---------------------------------------------------------------

    def _p(self, tag: str) -> int:
        return self.point_index[tag]

    def _row(self, owner: str, parts: list[tuple[float, Any]], target: float = 0.0, wrap=False):
        assembled = []
        for coef, term in parts:
            assembled.append((coef, term, tuple(self.columns.get(s, -1) for s in term.slots)))
        self.rows.append(_Row(owner, assembled, target, wrap))

    def _radius_term(self, tag: str) -> Any:
        entity = self.sketch.entities[tag]
        if isinstance(entity, Circle):
            return _Radius(self.circle_index[tag])
        assert isinstance(entity, Arc)
        return _Len(self._p(entity.start), self._p(entity.center))

    def _center(self, tag: str) -> int:
        entity = self.sketch.entities[tag]
        assert isinstance(entity, Arc | Circle)
        return self._p(entity.center)

    def _line(self, tag: str) -> tuple[int, int]:
        line = self.sketch.entities[tag]
        assert isinstance(line, Line)
        return self._p(line.a), self._p(line.b)

    def _build_rows(self) -> None:
        sk = self.sketch
        for entity in sk.entities.values():
            if isinstance(entity, Arc):
                c, s, e = self._p(entity.center), self._p(entity.start), self._p(entity.end)
                self._row(f"{entity.tag}:radius", [(1.0, _Len(e, c)), (-1.0, _Len(s, c))])
        for constraint in sk.constraints:
            if constraint.tag not in self.exclude:
                self._constraint_rows(constraint)
        for dim in sk.dims:
            if not dim.driven and dim.tag not in self.exclude:
                self._dim_rows(dim)

    def _constraint_rows(self, c: Constraint) -> None:
        sk, kind, refs, tag = self.sketch, c.kind, c.refs, c.tag
        kinds = [sk.entities[r].kind for r in refs]
        if kind == "fix":
            return  # a constant, not a row
        if kind == "coincident":
            p = self._p(refs[0])
            other = sk.entities[refs[1]]
            if isinstance(other, Point):
                q = self._p(refs[1])
                self._row(tag, [(1.0, _Coord(p, 0)), (-1.0, _Coord(q, 0))])
                self._row(tag, [(1.0, _Coord(p, 1)), (-1.0, _Coord(q, 1))])
            elif isinstance(other, Line):
                a, b = self._line(refs[1])
                self._row(tag, [(1.0, _Side(a, b, p))])
            else:  # on an arc or circle: at its radius from the centre
                self._row(
                    tag, [(1.0, _Len(p, self._center(refs[1]))), (-1.0, self._radius_term(refs[1]))]
                )
        elif kind == "concentric":
            p, q = self._center(refs[0]), self._center(refs[1])
            self._row(tag, [(1.0, _Coord(p, 0)), (-1.0, _Coord(q, 0))])
            self._row(tag, [(1.0, _Coord(p, 1)), (-1.0, _Coord(q, 1))])
        elif kind in ("horizontal", "vertical"):
            axis = 1 if kind == "horizontal" else 0
            p, q = (
                self._line(refs[0]) if kinds == ["line"] else (self._p(refs[0]), self._p(refs[1]))
            )
            self._row(tag, [(1.0, _Coord(p, axis)), (-1.0, _Coord(q, axis))])
        elif kind == "collinear":
            a, b = self._line(refs[0])
            c2, d2 = self._line(refs[1])
            self._row(tag, [(1.0, _Side(a, b, c2))])
            self._row(tag, [(1.0, _Side(a, b, d2))])
        elif kind in ("parallel", "perpendicular"):
            a, b = self._line(refs[0])
            c2, d2 = self._line(refs[1])
            term = _Cross(a, b, c2, d2) if kind == "parallel" else _Dot(a, b, c2, d2)
            self._row(tag, [(MM_PER_DEG, term)])
        elif kind == "equal":
            if kinds == ["line", "line"]:
                a, b = self._line(refs[0])
                c2, d2 = self._line(refs[1])
                self._row(tag, [(1.0, _Len(a, b)), (-1.0, _Len(c2, d2))])
            else:
                self._row(
                    tag, [(1.0, self._radius_term(refs[0])), (-1.0, self._radius_term(refs[1]))]
                )
        elif kind == "tangent":
            line_tag, curve_tag = (refs[0], refs[1]) if kinds[0] == "line" else (refs[1], refs[0])
            a, b = self._line(line_tag)
            centre = self._center(curve_tag)
            shared = sk.shared_point(line_tag, curve_tag)
            if shared is not None and isinstance(sk.entities[curve_tag], Arc):
                # Tangent AT the shared endpoint: the line is perpendicular to
                # the radius there. The distance form is second-order at that
                # point (the endpoint can slide along the line to first order)
                # and would report a phantom degree of freedom.
                self._row(tag, [(1.0, _DotDir(a, b, centre, self._p(shared[0])))])
            else:
                self._row(
                    tag,
                    [
                        (1.0, _Side(a, b, centre, absolute=True)),
                        (-1.0, self._radius_term(curve_tag)),
                    ],
                )
        elif kind == "symmetric":
            p, q = self._p(refs[0]), self._p(refs[1])
            a, b = self._line(refs[2])
            self._row(tag, [(1.0, _Side(a, b, p, q))])  # midpoint on the axis
            self._row(tag, [(1.0, _DotDir(a, b, p, q))])  # p->q perpendicular to the axis
        elif kind == "smooth":
            shared = sk.shared_point(refs[0], refs[1])
            assert shared is not None  # validated at constrain()
            p1, p2 = self._p(shared[0]), self._p(shared[1])
            c1, c2 = self._center(refs[0]), self._center(refs[1])
            self._row(tag, [(MM_PER_DEG, _Cross(p1, c1, p2, c2))])
        else:  # pragma: no cover - constrain() validated the kind
            raise CommandError(f"no solver rows for {kind}.", code="pk_bad_op")

    def _dim_rows(self, d: Dimension) -> None:
        sk, refs, tag = self.sketch, d.refs, d.tag
        kinds = [sk.entities[r].kind for r in refs]
        if d.kind == "len":
            a, b = self._line(refs[0])
            self._row(tag, [(1.0, _Len(a, b))], d.value)
        elif d.kind == "dist":
            if kinds == ["point", "point"]:
                p, q = self._p(refs[0]), self._p(refs[1])
                if d.axis == "X":
                    self._row(tag, [(1.0, _AxisDist(p, q, 0))], d.value)
                elif d.axis == "Y":
                    self._row(tag, [(1.0, _AxisDist(p, q, 1))], d.value)
                else:
                    self._row(tag, [(1.0, _Len(p, q))], d.value)
            else:
                p_tag, l_tag = (refs[0], refs[1]) if kinds[0] == "point" else (refs[1], refs[0])
                a, b = self._line(l_tag)
                self._row(tag, [(1.0, _Side(a, b, self._p(p_tag), absolute=True))], d.value)
        elif d.kind == "angle":
            a, b = self._line(refs[0])
            c2, d2 = self._line(refs[1])
            self._row(tag, [(MM_PER_DEG, _Angle(a, b, c2, d2))], d.value * MM_PER_DEG, wrap=True)
        elif d.kind == "dia":
            self._row(tag, [(2.0, self._radius_term(refs[0]))], d.value)
        elif d.kind == "rad":
            self._row(tag, [(1.0, self._radius_term(refs[0]))], d.value)

    # -- evaluation ---------------------------------------------------------

    def x0(self) -> np.ndarray:
        return np.array(
            [self.P[i][a] if kind == 0 else self.R[i] for kind, i, a in self.free], dtype=float
        )

    def _apply(self, x: np.ndarray) -> None:
        P, R = self.P, self.R
        for col, (kind, i, a) in enumerate(self.free):
            if kind == 0:
                P[i][a] = float(x[col])
            else:
                R[i] = float(x[col])

    def evaluate(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if (
            self._cache is not None
            and self._cache_x is not None
            and np.array_equal(x, self._cache_x)
        ):
            return self._cache
        self._apply(x)
        P, R = self.P, self.R
        f = np.empty(self.m)
        J = np.zeros((self.m, self.n))
        for ri, row in enumerate(self.rows):
            value = -row.target
            Jr = J[ri]
            for coef, term, cols in row.parts:
                tv, partials = term(P, R)
                value += coef * tv
                for col, g in zip(cols, partials, strict=True):
                    if col >= 0 and g != 0.0:
                        Jr[col] += coef * g
            if row.wrap:
                value = (value + 180.0 * MM_PER_DEG) % (360.0 * MM_PER_DEG) - 180.0 * MM_PER_DEG
            f[ri] = value
        self._cache_x = x.copy()
        self._cache = (f, J)
        return f, J

    def fun(self, x: np.ndarray) -> np.ndarray:
        return self.evaluate(x)[0]

    def jac(self, x: np.ndarray) -> np.ndarray:
        return self.evaluate(x)[1]

    def run(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
        """Solve from the model's coordinates. (x, residual, J, evaluations)."""
        x = self.x0()
        if self.n == 0 or self.m == 0:
            f, J = self.evaluate(x)
            return x, f, J, 0
        from scipy.optimize import least_squares

        method = "lm" if self.m >= self.n else "trf"
        result = least_squares(
            self.fun,
            x,
            jac=self.jac,
            method=method,
            xtol=1e-14,
            ftol=1e-14,
            gtol=1e-14,
            max_nfev=200 * (self.n + 1),
        )
        f, J = self.evaluate(result.x)
        return result.x, f, J, int(result.nfev)

    def owners(self) -> list[str]:
        return [row.owner for row in self.rows]


def _rank(J: np.ndarray) -> int:
    if J.size == 0:
        return 0
    smax = float(np.linalg.norm(J, 2))
    if smax == 0.0:
        return 0
    return int(np.linalg.matrix_rank(J, tol=RANK_RTOL * smax))


def _describe(sketch: Sketch, tag: str) -> str:
    for c in sketch.constraints:
        if c.tag == tag:
            return c.describe()
    for d in sketch.dims:
        if d.tag == tag:
            return d.describe()
    return tag


def solve(sketch: Sketch, *, exclude: frozenset[str] = frozenset()) -> SolveReport:
    """Solve a sketch in place and report. Same sketch in, same report out."""
    for c in sketch.constraints:
        if c.kind == "fix":
            sketch.point(c.refs[0]).fixed = True
    system = _System(sketch, exclude)
    _x, f, J, nfev = system.run()
    residual_max = float(np.max(np.abs(f))) if f.size else 0.0
    rank = _rank(J)
    dof = system.n - rank
    converged = residual_max < CONVERGED_MM

    redundant: list[str] = []
    conflicts: list[str] = []
    owners = system.owners()
    user_tags = [c.tag for c in sketch.constraints if c.kind != "fix"] + [
        d.tag for d in sketch.dims if not d.driven
    ]
    user_tags = [t for t in user_tags if t not in exclude]
    if converged and rank < system.m:
        for tag in user_tags:
            keep = [i for i, o in enumerate(owners) if o != tag]
            if len(keep) < len(owners) and _rank(J[keep]) == rank:
                redundant.append(_describe(sketch, tag))
    if not converged:
        by_residual = sorted(
            user_tags,
            key=lambda t: (
                -max((abs(float(f[i])) for i, o in enumerate(owners) if o == t), default=0.0),
                t,
            ),
        )
        for tag in by_residual[:CONFLICT_SEARCH_CAP]:
            trial = _System(sketch, exclude | {tag})
            _tx, tf, _tJ, _n = trial.run()
            if not tf.size or float(np.max(np.abs(tf))) < CONVERGED_MM:
                conflicts.append(_describe(sketch, tag))

    if not converged:
        status = "conflict"
    elif redundant:
        status = "over"
    elif dof > 0:
        status = "under"
    else:
        status = "ok"

    # write back (a conflict still writes the least-squares compromise, so the
    # caller sees where it ended up; the document restores on refusal)
    for tag, i in system.point_index.items():
        point = sketch.entities[tag]
        assert isinstance(point, Point)
        point.x, point.y = system.P[i]
    for tag, ci in system.circle_index.items():
        circle = sketch.entities[tag]
        assert isinstance(circle, Circle)
        circle.r = system.R[ci]
    solved = {tag: [sketch.entities[tag].x, sketch.entities[tag].y] for tag in system.point_index}  # type: ignore[union-attr]
    radii = {tag: sketch.entities[tag].r for tag in system.circle_index}  # type: ignore[union-attr]
    report = SolveReport(
        dof=int(dof),
        status=status,
        conflicts=conflicts,
        redundant=redundant,
        residual_max_mm=float(round(residual_max, 12)),
        iterations=nfev,
        solved=solved,
        radii=radii,
        unknowns=system.n,
        rows=system.m,
        rank=rank,
    )
    return report


def jacobian(sketch: Sketch) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """(residual, analytic J, row owners) at the sketch's current coordinates.
    Exposed so a test can check the analytic gradients against differences."""
    system = _System(sketch, frozenset())
    f, J = system.evaluate(system.x0())
    return f.copy(), J.copy(), system.owners()


def numeric_jacobian(sketch: Sketch, h: float = 1e-6) -> np.ndarray:
    system = _System(sketch, frozenset())
    x = system.x0()
    J = np.zeros((system.m, system.n))
    for col in range(system.n):
        xp, xm = x.copy(), x.copy()
        xp[col] += h
        xm[col] -= h
        J[:, col] = (system.fun(xp) - system.fun(xm)) / (2 * h)
    system.fun(x)
    return J
