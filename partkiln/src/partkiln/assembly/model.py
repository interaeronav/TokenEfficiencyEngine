"""The assembly model: poses, frames, components, mates and joints - as DATA.

Nothing here touches OCCT. A component's geometry is a `shape_ref` the
caller hands in (the shape itself or a callable that produces it), and a
mate or joint addresses geometry through a `FrameRef` - an origin, a
direction and a kind (`plane`, `axis`, `point`) that the document layer
reads off a NAMED sub-shape (Law 13: names, never indices) before this
layer sees it. That split is what lets the solver run and be tested with
no kernel installed, exactly as the sketch solver does (D1: `import
partkiln` is OCP-free, enforced by a subprocess test).

Conventions (D4, D3): millimetres and degrees at every boundary; a `Pose`
is a translation plus a UNIT quaternion `(w, x, y, z)` canonicalised to
`w >= 0`, so the same rotation always prints the same numbers and the
document's fingerprint (poses rounded to 1e-6) is reproducible.
`a.compose(b)` applies `b` first and then `a`, the matrix convention
`A @ B`.

A frame's `xdir` is the in-plane (plane) or perpendicular (axis) reference
direction that fixes the twist about `axis` for `rigid` and `slider`
joints and carries the `angle_deg` of a joint. When the caller gives none,
a canonical perpendicular is derived from the axis alone (the world axis
least aligned with it, projected) - deterministic, and documented as such
so a twist target that reads "0" against a derived xdir is never mistaken
for design intent.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from partkiln.document import CommandError

Vec3 = tuple[float, float, float]
Quat = tuple[float, float, float, float]

FRAME_KINDS = ("plane", "axis", "point")
MATE_KINDS = ("mate", "flush", "angle", "tangent", "insert")
JOINT_KINDS = ("rigid", "revolute", "slider", "cylindrical", "planar", "ball")

# Which frame kinds each constraint accepts for (a, b). A point frame has no
# direction of its own, so only the kinds that use the origin alone take it.
_DIRECTED = ("plane", "axis")
FRAME_RULES: dict[str, tuple[tuple[str, ...], tuple[str, ...], str]] = {
    "mate": (("plane",), ("plane",), "use insert for axis-axis"),
    "flush": (("plane",), ("plane",), "use insert for axis-axis"),
    "angle": (_DIRECTED, _DIRECTED, "an angle needs two directions"),
    "tangent": (
        ("axis", "plane"),
        ("axis", "plane"),
        "tangent is cylinder-plane or cylinder-cylinder",
    ),
    "insert": (("axis",), ("axis",), "use mate for plane-plane"),
    "rigid": (FRAME_KINDS, FRAME_KINDS, ""),
    "revolute": (_DIRECTED, _DIRECTED, "a revolute needs an axis on each side"),
    "slider": (_DIRECTED, _DIRECTED, "a slider needs an axis on each side"),
    "cylindrical": (_DIRECTED, _DIRECTED, "a cylindrical joint needs an axis on each side"),
    "planar": (_DIRECTED, _DIRECTED, "a planar joint needs a plane (or axis) on each side"),
    "ball": (FRAME_KINDS, FRAME_KINDS, ""),
}

_EPS = 1e-12


def _v3(v: Sequence[float], what: str) -> Vec3:
    try:
        out = tuple(float(c) for c in v)
    except (TypeError, ValueError) as exc:
        raise CommandError(f"{what} {v!r} is not [x, y, z].", code="pk_needs") from exc
    if len(out) != 3:
        raise CommandError(f"{what} {v!r} needs exactly three numbers.", code="pk_needs")
    return out  # type: ignore[return-value]


def _unit(v: Vec3, what: str) -> Vec3:
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if n < _EPS:
        raise CommandError(
            f"{what} {v!r} has zero length; a direction needs a non-zero vector.",
            code="pk_needs",
        )
    return (v[0] / n, v[1] / n, v[2] / n)


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def canonical_perpendicular(axis: Vec3) -> Vec3:
    """The documented derived xdir: the world axis least aligned with `axis`,
    made perpendicular to it. Same axis in, same vector out."""
    ax = _unit(axis, "axis")
    k = min(range(3), key=lambda i: (abs(ax[i]), i))
    seed = [0.0, 0.0, 0.0]
    seed[k] = 1.0
    d = _dot(tuple(seed), ax)  # type: ignore[arg-type]
    perp = (seed[0] - d * ax[0], seed[1] - d * ax[1], seed[2] - d * ax[2])
    return _unit(perp, "xdir")


# --------------------------------------------------------------------------- quaternions


def _qmul(a: Quat, b: Quat) -> Quat:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    )


def _qcanon(q: Sequence[float]) -> Quat:
    w, x, y, z = (float(c) for c in q)
    n = math.sqrt(w * w + x * x + y * y + z * z)
    if n < _EPS:
        raise CommandError(
            f"rotation {tuple(q)!r} is not a unit quaternion (zero length).",
            code="pk_needs",
        )
    w, x, y, z = w / n, x / n, y / n, z / n
    # Fix the double cover so the same rotation always prints the same way.
    if w < 0 or (w == 0 and (x < 0 or (x == 0 and (y < 0 or (y == 0 and z < 0))))):
        w, x, y, z = -w, -x, -y, -z
    return (w + 0.0, x + 0.0, y + 0.0, z + 0.0)


def quat_from_rotvec(rotvec: Sequence[float]) -> Quat:
    """Rotation vector (radians, axis * angle) -> unit quaternion."""
    rx, ry, rz = (float(c) for c in rotvec)
    a = math.sqrt(rx * rx + ry * ry + rz * rz)
    if a < 1e-12:
        return _qcanon((1.0, 0.5 * rx, 0.5 * ry, 0.5 * rz))
    s = math.sin(0.5 * a) / a
    return _qcanon((math.cos(0.5 * a), rx * s, ry * s, rz * s))


def quat_to_rotvec(q: Quat) -> Vec3:
    w, x, y, z = _qcanon(q)
    n = math.sqrt(x * x + y * y + z * z)
    if n < 1e-12:
        return (2.0 * x, 2.0 * y, 2.0 * z)
    angle = 2.0 * math.atan2(n, w)
    return (x / n * angle, y / n * angle, z / n * angle)


def quat_to_matrix(q: Quat) -> np.ndarray:
    w, x, y, z = q
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=float,
    )


def quat_from_matrix(m: np.ndarray) -> Quat:
    """Shepperd's method: pick the largest diagonal term so no division is small."""
    m = np.asarray(m, dtype=float)
    t = float(np.trace(m))
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        return _qcanon(
            (0.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s)
        )
    if m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        return _qcanon(
            ((m[2, 1] - m[1, 2]) / s, 0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s)
        )
    if m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        return _qcanon(
            ((m[0, 2] - m[2, 0]) / s, (m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s)
        )
    s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
    return _qcanon(
        ((m[1, 0] - m[0, 1]) / s, (m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s)
    )


# --------------------------------------------------------------------------- pose


@dataclass(frozen=True, slots=True)
class Pose:
    """A rigid placement: translation in mm, rotation as a unit quaternion (w, x, y, z)."""

    translation: Vec3 = (0.0, 0.0, 0.0)
    rotation: Quat = (1.0, 0.0, 0.0, 0.0)

    def __post_init__(self) -> None:
        object.__setattr__(self, "translation", _v3(self.translation, "translation"))
        object.__setattr__(self, "rotation", _qcanon(self.rotation))

    @staticmethod
    def identity() -> Pose:
        return Pose()

    @staticmethod
    def from_axis_angle(
        axis: Sequence[float], angle_deg: float, translation: Sequence[float] = (0.0, 0.0, 0.0)
    ) -> Pose:
        ax = _unit(_v3(axis, "axis"), "axis")
        a = math.radians(float(angle_deg))
        return Pose(
            _v3(translation, "translation"), quat_from_rotvec((ax[0] * a, ax[1] * a, ax[2] * a))
        )

    @staticmethod
    def from_rotvec(
        rotvec: Sequence[float], translation: Sequence[float] = (0.0, 0.0, 0.0)
    ) -> Pose:
        return Pose(_v3(translation, "translation"), quat_from_rotvec(rotvec))

    @staticmethod
    def from_matrix(m: Any) -> Pose:
        """From a 4x4 (or 3x4) homogeneous matrix; the 3x3 block must be a rotation."""
        arr = np.asarray(m, dtype=float)
        if arr.shape not in ((4, 4), (3, 4)):
            raise CommandError(f"a pose matrix is 4x4, got shape {arr.shape}.", code="pk_needs")
        r = arr[:3, :3]
        if not np.allclose(r.T @ r, np.eye(3), atol=1e-6) or np.linalg.det(r) < 0:
            raise CommandError(
                "the 3x3 block is not a proper rotation (orthonormal, det +1); "
                "a pose carries no scale or mirror.",
                code="pk_needs",
            )
        return Pose(tuple(arr[:3, 3]), quat_from_matrix(r))  # type: ignore[arg-type]

    def rotvec(self) -> Vec3:
        return quat_to_rotvec(self.rotation)

    def rotation_matrix(self) -> np.ndarray:
        return quat_to_matrix(self.rotation)

    def matrix(self) -> np.ndarray:
        m = np.eye(4)
        m[:3, :3] = self.rotation_matrix()
        m[:3, 3] = self.translation
        return m

    def compose(self, other: Pose) -> Pose:
        """`self` after `other`: (self ∘ other)(p) = self(other(p))."""
        t = self.point(other.translation)
        return Pose(t, _qmul(self.rotation, other.rotation))

    def inverse(self) -> Pose:
        w, x, y, z = self.rotation
        inv: Quat = (w, -x, -y, -z)
        r = quat_to_matrix(inv)
        t = -(r @ np.asarray(self.translation))
        return Pose(tuple(t), inv)  # type: ignore[arg-type]

    def point(self, p: Sequence[float]) -> Vec3:
        r = self.rotation_matrix() @ np.asarray(_v3(p, "point"))
        return (
            float(r[0]) + self.translation[0],
            float(r[1]) + self.translation[1],
            float(r[2]) + self.translation[2],
        )

    def vector(self, v: Sequence[float]) -> Vec3:
        r = self.rotation_matrix() @ np.asarray(_v3(v, "vector"))
        return (float(r[0]), float(r[1]), float(r[2]))

    def is_identity(self, tol: float = 0.0) -> bool:
        return all(abs(c) <= tol for c in self.translation) and all(
            abs(c - d) <= tol for c, d in zip(self.rotation, (1.0, 0.0, 0.0, 0.0), strict=True)
        )

    def rounded(self, ndigits: int = 9) -> Pose:
        return Pose(
            tuple(round(c, ndigits) + 0.0 for c in self.translation),  # type: ignore[arg-type]
            tuple(round(c, ndigits) + 0.0 for c in self.rotation),  # type: ignore[arg-type]
        )

    def as_dict(self, ndigits: int = 9) -> dict[str, list[float]]:
        r = self.rounded(ndigits)
        return {"translation": list(r.translation), "rotation": list(r.rotation)}

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> Pose:
        if not isinstance(raw, dict) or "translation" not in raw:
            raise CommandError(
                f"a pose is {{translation: [x, y, z], rotation: [w, x, y, z]}}, got {raw!r}.",
                code="pk_needs",
            )
        return Pose(
            _v3(raw["translation"], "translation"), _qcanon(raw.get("rotation", (1, 0, 0, 0)))
        )


# --------------------------------------------------------------------------- frames and refs


@dataclass(frozen=True, slots=True)
class FrameRef:
    """The geometry a constraint holds on to, in the COMPONENT's local frame.

    `plane`: `origin` on the plane, `axis` its outward normal. `axis`: a point
    on the line and its direction (`radius` when it is a cylinder's axis, for
    `tangent`). `point`: only `origin` matters (`axis` defaults to +Z).
    """

    kind: str
    origin: Vec3
    axis: Vec3 = (0.0, 0.0, 1.0)
    xdir: Vec3 | None = None
    radius: float | None = None

    def __post_init__(self) -> None:
        if self.kind not in FRAME_KINDS:
            raise CommandError(
                f"frame kind {self.kind!r} is not one of {', '.join(FRAME_KINDS)}.",
                code="pk_bad_op",
            )
        object.__setattr__(self, "origin", _v3(self.origin, "origin"))
        ax = _unit(_v3(self.axis, "axis"), "axis")
        object.__setattr__(self, "axis", ax)
        if self.xdir is None:
            xd = canonical_perpendicular(ax)
        else:
            raw = _v3(self.xdir, "xdir")
            d = _dot(raw, ax)
            xd = _unit((raw[0] - d * ax[0], raw[1] - d * ax[1], raw[2] - d * ax[2]), "xdir")
        object.__setattr__(self, "xdir", xd)
        if self.radius is not None:
            r = float(self.radius)
            if r <= 0:
                raise CommandError(f"radius {self.radius!r} must be positive.", code="pk_needs")
            object.__setattr__(self, "radius", r)

    @property
    def ydir(self) -> Vec3:
        return _cross(self.axis, self.xdir)  # type: ignore[arg-type]

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "kind": self.kind,
            "origin": list(self.origin),
            "axis": list(self.axis),
        }
        if self.xdir is not None:
            out["xdir"] = list(self.xdir)
        if self.radius is not None:
            out["radius"] = self.radius
        return out


@dataclass(frozen=True, slots=True)
class Ref:
    """A frame on a named component; `name` is the sub-shape name it came from
    (for messages only - the geometry is already in `frame`)."""

    component: str
    frame: FrameRef
    name: str = ""

    def label(self) -> str:
        return f"{self.component}.{self.name}" if self.name else self.component


# ------------------------------------------------------------------ components and constraints


@dataclass(slots=True)
class Component:
    """An instance of a part at a pose. `shape_ref` is the B-rep or a callable
    returning it (resolved lazily so a document can hand in a part's cache);
    `virtual` marks a create-object generic entity that has no geometry but
    belongs in the BOM (D5)."""

    name: str
    part_name: str
    shape_ref: Any = None
    pose: Pose = field(default_factory=Pose)
    grounded: bool = False
    virtual: bool = False

    @property
    def shape(self) -> Any:
        if self.shape_ref is None:
            if self.virtual:
                raise CommandError(
                    f"component {self.name!r} is virtual and has no geometry.",
                    code="pk_ref_empty",
                )
            raise CommandError(
                f"component {self.name!r} has no shape; give shape_ref a shape or a callable.",
                code="pk_ref_empty",
            )
        return self.shape_ref() if callable(self.shape_ref) else self.shape_ref


@dataclass(frozen=True, slots=True)
class Mate:
    """`mate`: planes coincident (`offset_mm` apart along a's normal), normals
    opposed unless `flip`. `flush`: coplanar with normals aligned. `angle`:
    `angle_deg` between the two directions. `tangent`: a cylinder axis at its
    radius (+ `offset_mm`) from a plane, or two cylinders touching outside
    (inside when `flip`). `insert`: axes coincident and aligned (opposed when
    `flip`); `offset_mm` None leaves the axial position to a mate - the
    concentric + coincident idiom - and a number fixes the origins that far
    apart along the axis."""

    name: str
    kind: str
    a: Ref
    b: Ref
    offset_mm: float | None = None
    angle_deg: float = 0.0
    flip: bool = False

    def __post_init__(self) -> None:
        _check_constraint(self, MATE_KINDS, "mate")


@dataclass(frozen=True, slots=True)
class Joint:
    """`rigid` (6 removed), `revolute` (5, leaves the turn), `slider` (5,
    leaves the travel), `cylindrical` (4), `planar` (3), `ball` (3).
    `offset_mm` is the axial separation of the origins (rigid, revolute) or
    the plane separation (planar); `angle_deg` the twist between the two
    xdirs (rigid, slider). `limits` are carried and reported, never enforced
    by the solver (a joint at its stop is a check, not a constraint)."""

    name: str
    kind: str
    a: Ref
    b: Ref
    offset_mm: float | None = None
    angle_deg: float = 0.0
    limits: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        _check_constraint(self, JOINT_KINDS, "joint")
        if self.limits is not None:
            lo, hi = (float(c) for c in self.limits)
            if lo > hi:
                raise CommandError(
                    f"joint {self.name!r} limits {self.limits!r} are reversed (low > high).",
                    code="pk_needs",
                )
            object.__setattr__(self, "limits", (lo, hi))


Constraint = Mate | Joint


def _check_constraint(c: Any, kinds: tuple[str, ...], what: str) -> None:
    if c.kind not in kinds:
        raise CommandError(
            f"{what} kind {c.kind!r} is not one of {', '.join(kinds)}.", code="pk_bad_op"
        )
    if not isinstance(c.a, Ref) or not isinstance(c.b, Ref):
        raise CommandError(
            f"{what} {c.name!r} needs a and b as Ref(component, frame).", code="pk_needs"
        )
    if c.a.component == c.b.component:
        raise CommandError(
            f"{what} {c.name!r} joins {c.a.component!r} to itself; a and b must be "
            "two different components.",
            code="pk_spec_conflict",
        )
    ok_a, ok_b, hint = FRAME_RULES[c.kind]
    for side, ref, ok in (("a", c.a, ok_a), ("b", c.b, ok_b)):
        if ref.frame.kind not in ok:
            raise CommandError(
                f"{what} {c.name!r} ({c.kind}) needs {side} to be a {' or '.join(ok)} frame, "
                f"but {ref.label()} is a {ref.frame.kind}. Fix: {hint}.",
                code="pk_spec_conflict",
            )
    if c.kind == "tangent":
        cyl = [r for r in (c.a, c.b) if r.frame.kind == "axis"]
        if not cyl or any(r.frame.radius is None for r in cyl):
            raise CommandError(
                f"tangent {c.name!r} needs a cylinder: an axis frame with its radius "
                "(FrameRef(kind='axis', ..., radius=r)).",
                code="pk_needs",
            )
    if c.kind == "angle":
        a = float(c.angle_deg) % 180.0
        if abs(a) < 1e-9 or abs(a - 180.0) < 1e-9:
            raise CommandError(
                f"angle {c.name!r} of {c.angle_deg} deg has no unique solving direction. "
                "Fix: use flush (0 deg, aligned) or mate (opposed) instead.",
                code="pk_needs",
            )
    if c.offset_mm is not None:
        object.__setattr__(c, "offset_mm", float(c.offset_mm))
    object.__setattr__(c, "angle_deg", float(c.angle_deg))


# --------------------------------------------------------------------------- assembly


class Assembly:
    """Components, mates and joints in insertion order; `grounded` names
    components fixed in world space in addition to their own flag."""

    def __init__(
        self,
        components: Sequence[Component] = (),
        mates: Sequence[Mate] = (),
        joints: Sequence[Joint] = (),
        grounded: Sequence[str] = (),
    ) -> None:
        self.components: dict[str, Component] = {}
        # ONE sequence in insertion order: a conflict is charged to the later
        # constraint whatever its type, so mates and joints must not be kept
        # in two lists and re-ordered on the way to the solver.
        self._constraints: list[Constraint] = []
        for c in components:
            self.add_component(c)
        for name in grounded:
            self.component(name).grounded = True
        for m in mates:
            self.add_mate(m)
        for j in joints:
            self.add_joint(j)

    # -- building --------------------------------------------------------

    def add_component(self, c: Component) -> Component:
        if c.name in self.components:
            raise CommandError(
                f"component {c.name!r} already exists; names are unique.", code="pk_ref_ambiguous"
            )
        self.components[c.name] = c
        return c

    def _add(self, c: Constraint) -> None:
        if any(x.name == c.name for x in self._constraints):
            raise CommandError(
                f"constraint {c.name!r} already exists; mates and joints share one namespace.",
                code="pk_ref_ambiguous",
            )
        for ref in (c.a, c.b):
            self.component(ref.component)
        self._constraints.append(c)

    def add_mate(self, m: Mate) -> Mate:
        if not isinstance(m, Mate):
            raise CommandError(f"add_mate needs a Mate, got {type(m).__name__}.", code="pk_bad_op")
        self._add(m)
        return m

    def add_joint(self, j: Joint) -> Joint:
        if not isinstance(j, Joint):
            raise CommandError(
                f"add_joint needs a Joint, got {type(j).__name__}.", code="pk_bad_op"
            )
        self._add(j)
        return j

    def remove_constraint(self, name: str) -> Constraint:
        for i, c in enumerate(self._constraints):
            if c.name == name:
                return self._constraints.pop(i)
        raise CommandError(
            f"no mate or joint {name!r}. Constraints: {self._known()}.",
            code="pk_ref_unknown",
        )

    # -- lookups ---------------------------------------------------------

    def component(self, name: str) -> Component:
        try:
            return self.components[name]
        except KeyError:
            known = ", ".join(self.components) or "none"
            raise CommandError(
                f"no component {name!r}. Components: {known}.", code="pk_ref_unknown"
            ) from None

    def constraints(self) -> list[Constraint]:
        """Mates and joints in insertion order - the solve order: a conflict is
        charged to the LATER constraint."""
        return list(self._constraints)

    @property
    def mates(self) -> list[Mate]:
        return [c for c in self._constraints if isinstance(c, Mate)]

    @property
    def joints(self) -> list[Joint]:
        return [c for c in self._constraints if isinstance(c, Joint)]

    def constraint(self, name: str) -> Constraint:
        for c in self.constraints():
            if c.name == name:
                return c
        raise CommandError(
            f"no mate or joint {name!r}. Constraints: {self._known()}.",
            code="pk_ref_unknown",
        )

    def constraint_names(self) -> list[str]:
        return [c.name for c in self.constraints()]

    def _known(self) -> str:
        return ", ".join(self.constraint_names()) or "none"

    @property
    def grounded(self) -> list[str]:
        return [c.name for c in self.components.values() if c.grounded]

    def free(self) -> list[Component]:
        return [c for c in self.components.values() if not c.grounded]

    def poses(self) -> dict[str, Pose]:
        return {name: c.pose for name, c in self.components.items()}

    def summary(self) -> dict[str, Any]:
        return {
            "components": len(self.components),
            "grounded": self.grounded,
            "mates": [m.name for m in self.mates],
            "joints": [j.name for j in self.joints],
        }


__all__ = [
    "FRAME_KINDS",
    "FRAME_RULES",
    "JOINT_KINDS",
    "MATE_KINDS",
    "Assembly",
    "Component",
    "Constraint",
    "FrameRef",
    "Joint",
    "Mate",
    "Pose",
    "Quat",
    "Ref",
    "Vec3",
    "canonical_perpendicular",
    "quat_from_matrix",
    "quat_from_rotvec",
    "quat_to_matrix",
    "quat_to_rotvec",
]
