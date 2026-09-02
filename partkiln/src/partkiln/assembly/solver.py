"""The assembly solver: scipy least squares over rigid-body poses.

Written on scipy (BSD-3) because the obvious dependency, casadi, is
LGPL-3.0+ and the lane ships MIT (pyproject's BANNED block, enforced by
tests/test_licences.py). The problem is small: six unknowns per free
component - a translation delta and a rotation vector applied on the LEFT
of the current rotation - and a handful of residual rows per mate or joint,
all in MILLIMETRES, driven by `least_squares(method="dogbox")` (why that
method: `_System.run`). Direction rows (a unit vector that must match, oppose
or cross another) are scaled by `DEG * MM_PER_DEG` so that one degree of
misalignment reads as one millimetre, the sketch solver's convention
(`MM_PER_DEG = 1.0`); angle and twist rows are in degrees times the same
factor. A residual of 1e-6 therefore means the same thing in every row.

Every row carries an analytic gradient, chained through the SO(3) left
Jacobian (`R(theta + d) ~ exp((J_l(theta) d)^) R(theta)`, so
`d(R v)/d theta = -[R v]_x J_l(theta)`), which is what keeps a three-
component solve well under the 200 ms budget and, more importantly, makes
the degrees-of-freedom count honest: DOF = 6 * n_free - rank(J) at the
solution, raw, no heuristic. Rank is a first-order fact: two constraints
that fix the same direction twice read as `redundant` even when they agree.

Verdicts, as the sketch solver's: `ok` (converged, dof 0), `under`
(converged, dof > 0, named per component from the null space), `over`
(converged, a constraint named whose rows add no rank), `conflict` (the
full set does not converge). A conflict is charged to the LATER constraint:
the constraints are re-added in order and the first one whose addition
breaks convergence is named, with its residual measured at the solution of
everything before it (a 5 mm contradictory offset reports 5.000, not the
2.5 mm least-squares split). The returned poses then satisfy the consistent
subset, and `residual_mm` is the largest violation among ALL rows at those
poses - so a `conflict` report says exactly how far the offender is.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from partkiln.assembly.model import (
    Assembly,
    Constraint,
    FrameRef,
    Joint,
    Pose,
    _qmul,
    canonical_perpendicular,
    quat_from_rotvec,
    quat_to_matrix,
)
from partkiln.document import CommandError

MM_PER_DEG = 1.0
DEG = 180.0 / math.pi
# A unit-vector residual is radians of misalignment at first order; this
# turns it into millimetres at one millimetre per degree.
DIR_SCALE = DEG * MM_PER_DEG
CONVERGED_MM = 1e-6
RANK_RTOL = 1e-7
# The retry start for a stalled solve: a small rotation about no axis of any
# axis-aligned frame, so it moves every antipodal direction row off its
# stationary point (see `_System.run`).
NUDGE_RAD = np.array([0.011, 0.023, 0.037])
_EPS = 1e-12

_I3 = np.eye(3)


def _skew(v: np.ndarray) -> np.ndarray:
    return np.array([[0.0, -v[2], v[1]], [v[2], 0.0, -v[0]], [-v[1], v[0], 0.0]])


def _left_jacobian(theta: np.ndarray) -> np.ndarray:
    """J_l of SO(3): exp((theta + d)^) = exp((J_l(theta) d)^) exp(theta^) to first order."""
    a = float(np.linalg.norm(theta))
    K = _skew(theta)
    if a < 1e-8:
        return _I3 + 0.5 * K
    return _I3 + (1.0 - math.cos(a)) / (a * a) * K + (a - math.sin(a)) / (a * a * a) * (K @ K)


# --------------------------------------------------------------------------- rows
#
# A row kind maps two world frames A = (P, N, X) and B = (P, N, X) - each a
# 9-vector - to k residuals and their 9-column partials on each side.

RowEval = tuple[np.ndarray, np.ndarray, np.ndarray]  # values (k,), dA (k, 9), dB (k, 9)


def _blocks(k: int) -> tuple[np.ndarray, np.ndarray]:
    return np.zeros((k, 9)), np.zeros((k, 9))


def _coincident(A: np.ndarray, B: np.ndarray, off: float) -> RowEval:
    Pa, Na, Pb = A[0:3], A[3:6], B[0:3]
    r = Pb - Pa - off * Na
    dA, dB = _blocks(3)
    dA[:, 0:3] = -_I3
    dA[:, 3:6] = -off * _I3
    dB[:, 0:3] = _I3
    return r, dA, dB


def _plane_dist(A: np.ndarray, B: np.ndarray, off: float) -> RowEval:
    Pa, Na, Pb = A[0:3], A[3:6], B[0:3]
    d = Pb - Pa
    r = np.array([float(d @ Na) - off])
    dA, dB = _blocks(1)
    dA[0, 0:3] = -Na
    dA[0, 3:6] = d
    dB[0, 0:3] = Na
    return r, dA, dB


def _dir_diff(A: np.ndarray, B: np.ndarray, sign: float) -> RowEval:
    """S * (Nb - s Na): zero when aligned (s = +1) or opposed (s = -1); rank 2."""
    Na, Nb = A[3:6], B[3:6]
    r = DIR_SCALE * (Nb - sign * Na)
    dA, dB = _blocks(3)
    dA[:, 3:6] = -sign * DIR_SCALE * _I3
    dB[:, 3:6] = DIR_SCALE * _I3
    return r, dA, dB


def _dir_cross(A: np.ndarray, B: np.ndarray) -> RowEval:
    """S * (Na x Nb): zero when parallel either way; rank 2."""
    Na, Nb = A[3:6], B[3:6]
    r = DIR_SCALE * np.cross(Na, Nb)
    dA, dB = _blocks(3)
    dA[:, 3:6] = -DIR_SCALE * _skew(Nb)
    dB[:, 3:6] = DIR_SCALE * _skew(Na)
    return r, dA, dB


def _point_on_line(A: np.ndarray, B: np.ndarray) -> RowEval:
    """The perpendicular from A's line to B's origin; rank 2."""
    Pa, Na, Pb = A[0:3], A[3:6], B[0:3]
    d = Pb - Pa
    dn = float(d @ Na)
    r = d - dn * Na
    proj = _I3 - np.outer(Na, Na)
    dA, dB = _blocks(3)
    dA[:, 0:3] = -proj
    dA[:, 3:6] = -dn * _I3 - np.outer(Na, d)
    dB[:, 0:3] = proj
    return r, dA, dB


def _xdiff(A: np.ndarray, B: np.ndarray) -> RowEval:
    """S * (Xb - Xa): the frames' reference directions coincide; rank 1 once
    the axes agree (2 before). Together with a direction row this is Wahba's
    two-vector alignment, whose cost has ONE minimum and only saddles
    elsewhere - which is why a rigid joint is written this way and not as a
    wrapped twist angle (that had a discontinuity at 180 deg and a local
    minimum a nudged solve fell into; measured on the pin-on-block case)."""
    Xa, Xb = A[6:9], B[6:9]
    r = DIR_SCALE * (Xb - Xa)
    dA, dB = _blocks(3)
    dA[:, 6:9] = -DIR_SCALE * _I3
    dB[:, 6:9] = DIR_SCALE * _I3
    return r, dA, dB


def _angle(A: np.ndarray, B: np.ndarray, target_deg: float) -> RowEval:
    """The unsigned angle between Na and Nb minus the target, in degrees; rank 1."""
    Na, Nb = A[3:6], B[3:6]
    c = np.cross(Na, Nb)
    L = float(np.linalg.norm(c))
    d = float(Na @ Nb)
    phi = math.atan2(L, d)
    r = np.array([(phi * DEG - target_deg) * MM_PER_DEG])
    # A parallel start has no gradient direction; pick one so the solver can
    # leave the singular point instead of stalling on it.
    u = c / L if L >= 1e-12 else np.asarray(canonical_perpendicular(tuple(Na)))  # type: ignore[arg-type]
    den = max(L * L + d * d, _EPS)
    k = DEG * MM_PER_DEG / den
    dA, dB = _blocks(1)
    dA[0, 3:6] = k * (d * (u @ (-_skew(Nb))) - L * Nb)
    dB[0, 3:6] = k * (d * (u @ _skew(Na)) - L * Na)
    return r, dA, dB


def _tangent_axes(A: np.ndarray, B: np.ndarray, target: float) -> RowEval:
    """Distance from B's origin to A's line minus the target; rank 1 (parallel axes)."""
    Pa, Na, Pb = A[0:3], A[3:6], B[0:3]
    d = Pb - Pa
    dn = float(d @ Na)
    e = d - dn * Na
    L = float(np.linalg.norm(e))
    r = np.array([L - target])
    u = e / L if L > 1e-12 else np.asarray(canonical_perpendicular(tuple(Na)))  # type: ignore[arg-type]
    proj = _I3 - np.outer(Na, Na)
    dA, dB = _blocks(1)
    dA[0, 0:3] = -(u @ proj)
    dA[0, 3:6] = u @ (-dn * _I3 - np.outer(Na, d))
    dB[0, 0:3] = u @ proj
    return r, dA, dB


def _rows_of(c: Constraint) -> list[tuple[str, Any, bool]]:
    """(kind, evaluator(A, B), swap) per row group. `swap` evaluates with the
    frames exchanged (tangent with the cylinder on side a)."""
    off = 0.0 if c.offset_mm is None else float(c.offset_mm)
    ang = float(c.angle_deg)
    flip = bool(getattr(c, "flip", False))
    k = c.kind
    if k == "mate":
        return [("plane", lambda A, B: _plane_dist(A, B, off), False),
                ("dir", lambda A, B: _dir_diff(A, B, 1.0 if flip else -1.0), False)]  # fmt: skip
    if k == "flush":
        return [("plane", lambda A, B: _plane_dist(A, B, off), False),
                ("dir", lambda A, B: _dir_diff(A, B, -1.0 if flip else 1.0), False)]  # fmt: skip
    if k == "angle":
        return [("angle", lambda A, B: _angle(A, B, ang), False)]
    if k == "tangent":
        return _tangent_rows(c, off, flip)
    if k == "insert":
        rows = [("dir", lambda A, B: _dir_diff(A, B, -1.0 if flip else 1.0), False),
                ("line", _point_on_line, False)]  # fmt: skip
        if c.offset_mm is not None:
            rows.append(("plane", lambda A, B: _plane_dist(A, B, off), False))
        return rows
    if k == "rigid":
        return [("point", lambda A, B: _coincident(A, B, off), False),
                ("dir", lambda A, B: _dir_diff(A, B, 1.0), False),
                ("xdir", _xdiff, False)]  # fmt: skip
    if k == "revolute":
        return [("dir", _dir_cross, False), ("line", _point_on_line, False),
                ("plane", lambda A, B: _plane_dist(A, B, off), False)]  # fmt: skip
    if k == "slider":
        return [
            ("dir", _dir_cross, False),
            ("line", _point_on_line, False),
            ("xdir", _xdiff, False),
        ]
    if k == "cylindrical":
        return [("dir", _dir_cross, False), ("line", _point_on_line, False)]
    if k == "planar":
        return [("plane", lambda A, B: _plane_dist(A, B, off), False), ("dir", _dir_cross, False)]
    if k == "ball":
        return [("point", lambda A, B: _coincident(A, B, 0.0), False)]
    raise CommandError(f"no rows for constraint kind {k!r}.", code="pk_bad_op")


def _tangent_rows(c: Constraint, off: float, flip: bool) -> list[tuple[str, Any, bool]]:
    fa, fb = c.a.frame, c.b.frame
    if fa.kind == "axis" and fb.kind == "axis":
        ra, rb = float(fa.radius or 0.0), float(fb.radius or 0.0)
        target = (abs(ra - rb) if flip else ra + rb) + off
        return [("tangent", lambda A, B: _tangent_axes(A, B, target), False)]
    # plane + cylinder: the cylinder sits on the plane's normal side unless flipped
    if fa.kind == "plane":
        r = float(fb.radius or 0.0)
        s = -1.0 if flip else 1.0
        return [("tangent", lambda A, B: _plane_dist(A, B, s * (r + off)), False)]
    r = float(fa.radius or 0.0)
    s = -1.0 if flip else 1.0
    return [("tangent", lambda A, B: _plane_dist(A, B, s * (r + off)), True)]


def _effective_frame(frame: FrameRef, angle_deg: float) -> FrameRef:
    """`frame` with its xdir turned by `angle_deg` about its axis (Rodrigues in
    the component's own coordinates), so a joint's twist offset is data on
    the frame and the row it feeds stays the plain `Xb - Xa`."""
    if angle_deg == 0.0:
        return frame
    n, x = np.asarray(frame.axis), np.asarray(frame.xdir)
    a = math.radians(angle_deg)
    x2 = math.cos(a) * x + math.sin(a) * np.cross(n, x)
    return FrameRef(frame.kind, frame.origin, frame.axis, tuple(x2), frame.radius)


# --------------------------------------------------------------------------- the system


class _System:
    """Unknowns, rows and their evaluation for one solve of `constraints`."""

    def __init__(self, asm: Assembly, constraints: list[Constraint]) -> None:
        self.asm = asm
        self.constraints = constraints
        self.free = [c.name for c in asm.free()]
        self.col = {name: 6 * i for i, name in enumerate(self.free)}
        self.base = {
            name: (np.asarray(c.pose.translation, dtype=float), c.pose.rotation)
            for name, c in asm.components.items()
        }
        self.n = 6 * len(self.free)
        self.groups = [
            (
                c,
                _effective_frame(c.a.frame, c.angle_deg)
                if c.kind in ("rigid", "slider")
                else c.a.frame,
                _rows_of(c),
            )
            for c in constraints
        ]
        self.m = 0
        self.owners: list[str] = []
        self.owner_rows: dict[str, list[int]] = {}
        self._cache_x: np.ndarray | None = None
        self._cache: tuple[np.ndarray, np.ndarray] | None = None
        # Row counts are fixed per kind; take them from one evaluation at x0.
        f, _J = self.evaluate(self.x0())
        self.m = int(f.size)

    def x0(self) -> np.ndarray:
        return np.zeros(self.n)

    # -- poses and frames ------------------------------------------------

    def pose(self, x: np.ndarray, name: str) -> Pose:
        t0, q0 = self.base[name]
        if name not in self.col:
            return Pose(tuple(t0), q0)  # type: ignore[arg-type]
        i = self.col[name]
        dt, th = x[i : i + 3], x[i + 3 : i + 6]
        return Pose(tuple(t0 + dt), _qmul(quat_from_rotvec(th), q0))  # type: ignore[arg-type]

    def poses(self, x: np.ndarray) -> dict[str, Pose]:
        return {name: self.pose(x, name) for name in self.asm.components}

    def _world(
        self, x: np.ndarray, name: str, frame: FrameRef
    ) -> tuple[np.ndarray, np.ndarray | None]:
        """World (P, N, X) 9-vector and its (9, 6) partial on the component's
        unknowns (None when grounded)."""
        pose = self.pose(x, name)
        R = quat_to_matrix(pose.rotation)
        t = np.asarray(pose.translation)
        P = R @ np.asarray(frame.origin) + t
        N = R @ np.asarray(frame.axis)
        X = R @ np.asarray(frame.xdir)
        W = np.concatenate([P, N, X])
        if name not in self.col:
            return W, None
        i = self.col[name]
        Jl = _left_jacobian(x[i + 3 : i + 6])
        D = np.zeros((9, 6))
        D[0:3, 0:3] = _I3
        D[0:3, 3:6] = -_skew(P - t) @ Jl
        D[3:6, 3:6] = -_skew(N) @ Jl
        D[6:9, 3:6] = -_skew(X) @ Jl
        return W, D

    # -- evaluation -------------------------------------------------------

    def evaluate(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if (
            self._cache is not None
            and self._cache_x is not None
            and np.array_equal(x, self._cache_x)
        ):
            return self._cache
        values: list[np.ndarray] = []
        jac_rows: list[np.ndarray] = []
        owners: list[str] = []
        owner_rows: dict[str, list[int]] = {}
        row_i = 0
        world_cache: dict[tuple[str, int], tuple[np.ndarray, np.ndarray | None]] = {}

        def world(name: str, frame: FrameRef) -> tuple[np.ndarray, np.ndarray | None]:
            key = (name, id(frame))
            if key not in world_cache:
                world_cache[key] = self._world(x, name, frame)
            return world_cache[key]

        for c, frame_a, groups in self.groups:
            Wa, Da = world(c.a.component, frame_a)
            Wb, Db = world(c.b.component, c.b.frame)
            for _kind, fn, swap in groups:
                if swap:
                    r, dB, dA = fn(Wb, Wa)
                else:
                    r, dA, dB = fn(Wa, Wb)
                k = r.size
                J = np.zeros((k, self.n))
                if Da is not None:
                    i = self.col[c.a.component]
                    J[:, i : i + 6] += dA @ Da
                if Db is not None:
                    i = self.col[c.b.component]
                    J[:, i : i + 6] += dB @ Db
                values.append(r)
                jac_rows.append(J)
                owners.extend([c.name] * k)
                owner_rows.setdefault(c.name, []).extend(range(row_i, row_i + k))
                row_i += k
        f = np.concatenate(values) if values else np.zeros(0)
        J = np.vstack(jac_rows) if jac_rows else np.zeros((0, self.n))
        self.owners, self.owner_rows = owners, owner_rows
        self._cache_x, self._cache = x.copy(), (f, J)
        return f, J

    def fun(self, x: np.ndarray) -> np.ndarray:
        return self.evaluate(x)[0]

    def jac(self, x: np.ndarray) -> np.ndarray:
        return self.evaluate(x)[1]

    def run(self, tol: float = CONVERGED_MM) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
        """Solve from the components' current poses. (x, residual, J, evaluations).

        `scipy.optimize.least_squares(method="dogbox")`, chosen by measurement
        over the three alternatives on the same sixteen scenarios (this Mac,
        scipy 1.17.1): MINPACK `lm` on a zero-padded system drifts along a
        free rotation's null space - the F6 insert + mate converged at
        theta_z = -2 pi, and five pins plus one conflicting mate ended in a
        NaN rotation; `trf` (the sketch solver's under-determined route)
        stalls on a rank-deficient J with `ftol` "satisfied" (a -13 mm plane
        row ended at +2 mm) and with `tr_solver="lsmr"` is 2-5x slower.
        Dogbox's exact Gauss-Newton step is `lstsq` - the minimum-norm step -
        so a component's free motion never moves from where it started: no
        drift by construction, ~1 ms per two-body scenario, 14 ms for 11 pins.

        A start that does not converge is retried ONCE from a fixed
        rotational nudge (`NUDGE_RAD`): the exact antipode of a direction row
        (a pin standing on a block, whose face normals oppose while a rigid
        joint wants them aligned) is a stationary point of every rotation
        parametrisation, and the nudge is what turns "stalls there" into
        "flips" - deterministically. Rotation vectors are wrapped to
        |theta| <= pi after every pass because the left Jacobian is singular
        at 2 pi and the rank (so the DOF) would read wrong there.
        """
        x = self.x0()
        if self.n == 0 or self.m == 0:
            f, J = self.evaluate(x)
            return x, f, J, 0
        from scipy.optimize import least_squares

        nfev = 0
        best = x
        converged = False
        for start in (x, self.nudged(x)):
            for _attempt in range(3):
                result = least_squares(
                    self.fun,
                    start,
                    jac=self.jac,
                    method="dogbox",
                    xtol=1e-14,
                    ftol=1e-14,
                    gtol=1e-14,
                    max_nfev=200 * (self.n + 1),
                )
                nfev += int(result.nfev)
                best = self.wrapped(result.x)
                f, J = self.evaluate(best)
                converged = not f.size or float(np.max(np.abs(f))) < tol
                if converged or np.array_equal(best, result.x):
                    break
                start = best
            if converged:
                break
        return best, f, J, nfev

    def wrapped(self, x: np.ndarray) -> np.ndarray:
        """`x` with every rotation vector brought into |theta| <= pi (same rotation)."""
        out = x.copy()
        for name in self.free:
            i = self.col[name]
            th = out[i + 3 : i + 6]
            a = float(np.linalg.norm(th))
            if a > math.pi:
                turns = round(a / (2.0 * math.pi))
                out[i + 3 : i + 6] = th * (1.0 - 2.0 * math.pi * turns / a)
        return out

    def nudged(self, x: np.ndarray) -> np.ndarray:
        """`x` with every free component's rotation nudged by `NUDGE_RAD`."""
        out = x.copy()
        for name in self.free:
            i = self.col[name]
            out[i + 3 : i + 6] += NUDGE_RAD
        return out


def _rank(J: np.ndarray) -> int:
    if J.size == 0:
        return 0
    smax = float(np.linalg.norm(J, 2))
    if smax == 0.0:
        return 0
    return int(np.linalg.matrix_rank(J, tol=RANK_RTOL * smax))


def _null_space(J: np.ndarray, n: int) -> np.ndarray:
    if J.size == 0:
        return np.eye(n)
    _u, s, vt = np.linalg.svd(J)
    smax = float(s[0]) if s.size else 0.0
    rank = int(np.sum(s > RANK_RTOL * smax)) if smax > 0 else 0
    return vt[rank:].T


# --------------------------------------------------------------------------- report


@dataclass(slots=True)
class SolveReport:
    dof: int
    dof_by_component: dict[str, int]
    status: str
    residual_mm: float
    conflicts: list[dict[str, Any]]
    redundant: list[str]
    poses: dict[str, Pose]
    unknowns: int = 0
    rows: int = 0
    rank: int = 0
    iterations: int = 0
    joint_values: dict[str, dict[str, float]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    ms: float = 0.0  # wall time; never goes on the wire (D7)

    @property
    def over_constrained(self) -> list[str]:
        return [c["constraint"] for c in self.conflicts]

    @property
    def converged(self) -> bool:
        return self.status != "conflict"

    def as_dict(self, ndigits: int = 9) -> dict[str, Any]:
        return {
            "dof": self.dof,
            "dof_by_component": dict(self.dof_by_component),
            "status": self.status,
            "residual_mm": self.residual_mm,
            "conflicts": [dict(c) for c in self.conflicts],
            "over_constrained": self.over_constrained,
            "redundant": list(self.redundant),
            "poses": {k: p.as_dict(ndigits) for k, p in self.poses.items()},
            "joint_values": {k: dict(v) for k, v in self.joint_values.items()},
            "warnings": list(self.warnings),
        }


def _joint_values(
    asm: Assembly, active: list[Constraint], poses: dict[str, Pose]
) -> tuple[dict, list]:
    values: dict[str, dict[str, float]] = {}
    warnings: list[str] = []
    for c in active:
        if not isinstance(c, Joint) or c.kind not in ("revolute", "slider", "cylindrical"):
            continue
        pa, pb = poses[c.a.component], poses[c.b.component]
        Pa, Na, Xa = (
            np.asarray(v)
            for v in (
                pa.point(c.a.frame.origin),
                pa.vector(c.a.frame.axis),
                pa.vector(c.a.frame.xdir),
            )
        )  # type: ignore[arg-type]
        Pb, Xb = np.asarray(pb.point(c.b.frame.origin)), np.asarray(pb.vector(c.b.frame.xdir))  # type: ignore[arg-type]
        out: dict[str, float] = {}
        if c.kind in ("revolute", "cylindrical"):
            out["angle_deg"] = (
                round(math.atan2(float(np.cross(Xa, Xb) @ Na), float(Xa @ Xb)) * DEG, 6) + 0.0
            )
        if c.kind in ("slider", "cylindrical"):
            out["travel_mm"] = round(float((Pb - Pa) @ Na), 6) + 0.0
        values[c.name] = out
        if c.limits is not None:
            lo, hi = c.limits
            v = out.get("angle_deg" if c.kind == "revolute" else "travel_mm", 0.0)
            if v < lo - 1e-9 or v > hi + 1e-9:
                warnings.append(f"{c.name}: {v:g} is outside limits [{lo:g}, {hi:g}]")
    return values, warnings


def solve(asm: Assembly, *, tol: float = CONVERGED_MM) -> SolveReport:
    """Solve every mate and joint from the components' current poses.

    The assembly is NOT mutated: `report.poses` carries the solved poses
    (grounded components unchanged) for the caller to commit or discard,
    which is how Law 16 holds - a failed batch never advances state.
    """
    t_start = time.perf_counter()
    cons = asm.constraints()
    n_free = len(asm.free())
    system = _System(asm, cons)
    x, f, J, nfev = system.run()
    residual = float(np.max(np.abs(f))) if f.size else 0.0
    conflicts: list[dict[str, Any]] = []
    active = cons

    if residual >= tol:
        active = []
        good: tuple[_System, np.ndarray] = (_System(asm, []), np.zeros(system.n))
        for c in cons:
            trial = _System(asm, [*active, c])
            tx, tf, _tJ, _n = trial.run()
            if not tf.size or float(np.max(np.abs(tf))) < tol:
                active.append(c)
                good = (trial, tx)
            else:
                probe = _System(asm, [*active, c])
                pf = probe.fun(good[1] if probe.n == good[1].size else np.zeros(probe.n))
                rows = probe.owner_rows.get(c.name, [])
                worst = max((abs(float(pf[i])) for i in rows), default=0.0)
                conflicts.append({"constraint": c.name, "residual_mm": round(worst, 3) + 0.0})
        system, x = good
        f, J = system.evaluate(x)
        full = _System(asm, cons)
        f_all = full.fun(x)
        residual = float(np.max(np.abs(f_all))) if f_all.size else 0.0

    rank = _rank(J)
    dof = system.n - rank
    redundant: list[str] = []
    if f.size and rank < J.shape[0]:
        for c in active:
            rows = system.owner_rows.get(c.name, [])
            keep = [i for i in range(J.shape[0]) if i not in set(rows)]
            if rows and _rank(J[keep]) == rank:
                redundant.append(c.name)

    N = _null_space(J, system.n)
    dof_by_component: dict[str, int] = {}
    for name in system.free:
        i = system.col[name]
        block = N[i : i + 6, :]
        dof_by_component[name] = _rank(block) if block.size else 0

    if conflicts:
        status = "conflict"
    elif redundant:
        status = "over"
    elif dof > 0:
        status = "under"
    else:
        status = "ok"

    poses = system.poses(x)
    joint_values, warnings = _joint_values(asm, active, poses)
    if n_free == 0 and cons:
        warnings.append("every component is grounded; the constraints were checked, not solved")
    return SolveReport(
        dof=int(dof),
        dof_by_component=dof_by_component,
        status=status,
        residual_mm=float(round(residual, 12)),
        conflicts=conflicts,
        redundant=redundant,
        poses=poses,
        unknowns=system.n,
        rows=int(f.size),
        rank=rank,
        iterations=nfev,
        joint_values=joint_values,
        warnings=warnings,
        ms=(time.perf_counter() - t_start) * 1000.0,
    )


def jacobian(asm: Assembly) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """(residual, analytic J, row owners) at the current poses - for checking
    the gradients against finite differences."""
    system = _System(asm, asm.constraints())
    f, J = system.evaluate(system.x0())
    return f.copy(), J.copy(), list(system.owners)


def numeric_jacobian(asm: Assembly, h: float = 1e-6) -> np.ndarray:
    system = _System(asm, asm.constraints())
    x = system.x0()
    J = np.zeros((system.m, system.n))
    for col in range(system.n):
        xp, xm = x.copy(), x.copy()
        xp[col] += h
        xm[col] -= h
        J[:, col] = (system.fun(xp) - system.fun(xm)) / (2 * h)
    return J


def apply_poses(asm: Assembly, poses: dict[str, Pose]) -> None:
    """Commit solved poses onto the assembly's components (the caller's choice)."""
    for name, pose in poses.items():
        asm.component(name).pose = pose


__all__ = [
    "CONVERGED_MM",
    "DIR_SCALE",
    "MM_PER_DEG",
    "RANK_RTOL",
    "SolveReport",
    "apply_poses",
    "jacobian",
    "numeric_jacobian",
    "solve",
]
