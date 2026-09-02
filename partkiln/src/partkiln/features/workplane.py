"""Datums (planes, axes, points) and the one place a plane/axis/point reference is read.

A datum is pure geometry - three tuples - so the document can hold it with
no OCCT: `plane` {offset: {from, distance}} | {through: [p, q, r]} |
{angle: {about, deg, from}} | {normal_at: {face, at}} | {midplane: [a, b]};
`axis` {through: [p, q]} | {along: X|Y|Z, at} | {of: <cylindrical face>};
`point` {at: [x, y, z]} | {on: <face>, at: [u, v]}. Every reader here
(`frame_for`, `plane_of`, `axis_of`, `point_of`) is what the features call,
so "what does `plane:top` / `on:plate.end` / `x=80` / `Z` mean" is answered
in exactly one module and refused with the accepted forms.

Frames: `XY` (normal +Z), `XZ` (normal -Y, x -> X, y -> Z), `YZ` (normal +X,
x -> Y, y -> Z), `plane:<name>` (the datum's own frame) and `on:<face ref>`
(the face's outward normal; origin = the world origin projected onto the
face plane unless `@centroid` / `@x,y,z` - see sketch/profile.py). OCP is
imported inside functions only, and only for face references.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from partkiln.document import CommandError, register_kind
from partkiln.features.base import get_part, one, refs_of
from partkiln.naming import Resolved
from partkiln.sketch.profile import (
    NAMED_FRAMES,
    Frame,
    face_frame,
    make_frame,
    split_plane_ref,
)

Vec3 = tuple[float, float, float]

_WORLD_AXES: dict[str, Vec3] = {"X": (1.0, 0.0, 0.0), "Y": (0.0, 1.0, 0.0), "Z": (0.0, 0.0, 1.0)}


@dataclass(frozen=True)
class Datum:
    name: str
    kind: str  # plane | axis | point
    origin: Vec3
    direction: Vec3  # the plane normal, the axis direction, (0, 0, 0) for a point
    xdir: Vec3 | None = None

    def frame(self) -> Frame:
        if self.kind != "plane":
            raise CommandError(
                f"{self.kind} {self.name} is not a plane; a sketch needs plane:<plane datum>.",
                code="pk_plane_mismatch",
            )
        return make_frame(self.origin, self.direction, self.xdir)

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": f"{self.kind}:{self.name}",
            "kind": "datum",
            "type": self.kind,
            "origin": [round(c, 3) + 0.0 for c in self.origin],
        }
        if self.kind == "plane":
            out["normal"] = [round(c, 3) + 0.0 for c in self.direction]
        elif self.kind == "axis":
            out["direction"] = [round(c, 3) + 0.0 for c in self.direction]
        return out


# --------------------------------------------------------------------------- vector helpers


def _v(p: Sequence[float]) -> Vec3:
    return (float(p[0]), float(p[1]), float(p[2]))


def _sub(a: Sequence[float], b: Sequence[float]) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a: Sequence[float], b: Sequence[float], s: float = 1.0) -> Vec3:
    return (a[0] + s * b[0], a[1] + s * b[1], a[2] + s * b[2])


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Sequence[float], b: Sequence[float]) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(v: Sequence[float], what: str) -> Vec3:
    n = math.sqrt(_dot(v, v))
    if n < 1e-9:
        raise CommandError(f"{what} is degenerate (zero length).", code="pk_needs")
    return (v[0] / n, v[1] / n, v[2] / n)


def _xyz(doc: Any, raw: Any, assumed: dict[str, Any], deps: set[str], what: str) -> Vec3:
    if not isinstance(raw, list | tuple) or len(raw) != 3:
        raise CommandError(f"{what} needs [x, y, z] in mm, got {raw!r}.", code="pk_needs")
    return (
        doc.length(raw[0], assumed, deps),
        doc.length(raw[1], assumed, deps),
        doc.length(raw[2], assumed, deps),
    )


def _axis_letter(text: str) -> Vec3 | None:
    sign = -1.0 if text.startswith("-") else 1.0
    letter = text.lstrip("+-").upper()
    if letter in _WORLD_AXES and len(text.lstrip("+-")) == 1:
        d = _WORLD_AXES[letter]
        return (sign * d[0], sign * d[1], sign * d[2])
    return None


# --------------------------------------------------------------------------- readers


def datum(doc: Any, ref: str, kind: str) -> Datum:
    name = str(ref).split(":", 1)[1] if ":" in str(ref) else str(ref)
    d = doc.datums.get(name)
    if d is None or d.kind != kind:
        known = ", ".join(f"{x.kind}:{x.name}" for x in doc.datums.values()) or "(none)"
        raise CommandError(f"no {kind} datum {ref!r}. Datums: {known}.", code="pk_ref_unknown")
    return d


def face_of(doc: Any, part: Any, ref: str, feature: Any = None) -> Resolved:
    """One face by name or selector, in `part`."""
    from partkiln.features.base import Feature

    probe = feature if feature is not None else Feature("_ref", "ref", {})
    return one(part, probe, ref, "face", "a face")


def frame_for(doc: Any, plane: str, part: Any = None, feature: Any = None) -> Frame:
    """The frame of a sketch plane string (see the module doc)."""
    kind, ref, at = split_plane_ref(plane)
    if kind == "named":
        return NAMED_FRAMES[ref]
    if kind == "datum":
        return datum(doc, ref, "plane").frame()
    if part is None:
        part = get_part(doc, {}, {})
    res = face_of(doc, part, ref, feature)
    info = res.infos[0]
    if info.surface_type != "plane" or info.normal is None:
        raise CommandError(
            f"on:{ref} is a {info.surface_type} face; a sketch needs a planar face.",
            code="pk_plane_mismatch",
        )
    if feature is not None:
        refs_of(feature, ref)
    return face_frame(info.centroid, info.normal, info.centroid, at)


def plane_of(doc: Any, ref: Any, part: Any = None, feature: Any = None) -> tuple[Vec3, Vec3]:
    """(point, unit normal) for XY/XZ/YZ, plane:<n>, x=80 | y=.. | z=.., on:<face> or a face ref."""
    if isinstance(ref, list | tuple) and len(ref) == 2:
        return _v(ref[0]), _unit(ref[1], "the plane normal")
    text = str(ref).strip()
    if text in NAMED_FRAMES:
        f = NAMED_FRAMES[text]
        return f.origin, f.normal
    if text.startswith("plane:"):
        d = datum(doc, text, "plane")
        return d.origin, d.direction
    m = text.replace(" ", "")
    if len(m) > 2 and m[0] in "xyzXYZ" and m[1] == "=":
        try:
            value = float(m[2:])
        except ValueError as exc:
            raise CommandError(
                f"{ref!r}: {m[2:]!r} is not a number (mm).", code="pk_needs"
            ) from exc
        axis = _WORLD_AXES[m[0].upper()]
        return (axis[0] * value, axis[1] * value, axis[2] * value), axis
    face_ref = text[3:] if text.startswith("on:") else text
    if part is None:
        part = get_part(doc, {}, {})
    res = face_of(doc, part, face_ref, feature)
    info = res.infos[0]
    if info.surface_type != "plane" or info.normal is None:
        raise CommandError(
            f"{face_ref} is a {info.surface_type} face, not a plane.", code="pk_plane_mismatch"
        )
    return info.centroid, info.normal


def axis_of(
    doc: Any, ref: Any, part: Any = None, feature: Any = None, frame: Frame | None = None
) -> tuple[Vec3, Vec3]:
    """(point, unit direction) for X|Y|Z (through the frame origin when a frame
    is given, else the world origin), axis:<n>, [[p], [d]] or a cylindrical face."""
    if isinstance(ref, list | tuple):
        if len(ref) != 2 or not all(isinstance(x, list | tuple) and len(x) == 3 for x in ref):
            raise CommandError("an axis literal is [[px, py, pz], [dx, dy, dz]].", code="pk_needs")
        return _v(ref[0]), _unit(ref[1], "the axis direction")
    text = str(ref).strip()
    letter = _axis_letter(text)
    if letter is not None:
        if frame is not None:
            local = {"X": frame.xdir, "Y": frame.ydir, "Z": frame.normal}[text.lstrip("+-").upper()]
            sign = -1.0 if text.startswith("-") else 1.0
            return frame.origin, (sign * local[0], sign * local[1], sign * local[2])
        return (0.0, 0.0, 0.0), letter
    if text.startswith("axis:"):
        d = datum(doc, text, "axis")
        return d.origin, d.direction
    if part is None:
        part = get_part(doc, {}, {})
    res = face_of(doc, part, text, feature)
    info = res.infos[0]
    if info.surface_type not in ("cylinder", "cone"):
        raise CommandError(
            f"{text} is a {info.surface_type} face; an axis needs a cylinder or cone face, "
            "X|Y|Z, axis:<name> or [[p], [d]].",
            code="pk_ref_unknown",
        )
    return _cyl_axis(info.shape)


def _cyl_axis(face: Any) -> tuple[Vec3, Vec3]:
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    surf = BRepAdaptor_Surface(face)
    ax = surf.Cylinder().Axis() if surf.GetType().name == "GeomAbs_Cylinder" else surf.Cone().Axis()
    p, d = ax.Location(), ax.Direction()
    return (p.X(), p.Y(), p.Z()), (d.X(), d.Y(), d.Z())


def point_of(doc: Any, ref: Any, part: Any = None, assumed: dict[str, Any] | None = None) -> Vec3:
    """A point: [x, y, z], point:<name>, or a face ref (its centroid)."""
    if isinstance(ref, list | tuple):
        return _xyz(doc, ref, assumed if assumed is not None else {}, set(), "a point")
    text = str(ref).strip()
    if text.startswith("point:"):
        return datum(doc, text, "point").origin
    if part is None:
        part = get_part(doc, {}, {})
    return face_of(doc, part, text).infos[0].centroid


def direction_of(doc: Any, ref: Any, frame: Frame | None = None) -> Vec3:
    """A direction: +Z | -X | [dx, dy, dz]; letters in the frame when given."""
    if isinstance(ref, list | tuple):
        return _unit(_v(ref), "the direction")
    _p, d = axis_of(doc, ref, frame=frame)
    return d


# --------------------------------------------------------------------------- the verbs


def _store(doc: Any, args: dict[str, Any], d: Datum) -> dict[str, Any]:
    doc.datums[d.name] = d
    return d.as_dict()


@register_kind("plane")
def _k_plane(doc: Any, args: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
    name = doc.new_name(args, "plane", doc.datums)
    deps: set[str] = set()
    part = doc.parts.get(str(args.get("part"))) if args.get("part") else None
    if "offset" in args:
        spec = args["offset"]
        if not isinstance(spec, dict) or "from" not in spec or "distance" not in spec:
            raise CommandError("plane offset needs {from: <plane>, distance}.", code="pk_needs")
        point, normal = plane_of(doc, spec["from"], part)
        base_frame = make_frame(point, normal)
        d = doc.length(spec["distance"], assumed, deps)
        origin = _add(point, normal, d)
        return _store(doc, args, Datum(name, "plane", origin, normal, base_frame.xdir))
    if "through" in args:
        pts = args["through"]
        if not isinstance(pts, list | tuple) or len(pts) != 3:
            raise CommandError("plane through needs three points [[x,y,z], ...].", code="pk_needs")
        p, q, r = (point_of(doc, x, part, assumed) for x in pts)
        normal = _unit(_cross(_sub(q, p), _sub(r, p)), "the plane through three collinear points")
        return _store(doc, args, Datum(name, "plane", p, normal, _unit(_sub(q, p), "x")))
    if "angle" in args:
        spec = args["angle"]
        if not isinstance(spec, dict) or "about" not in spec or "deg" not in spec:
            raise CommandError(
                "plane angle needs {about: <axis>, deg, from: <plane>}.", code="pk_needs"
            )
        point, normal = plane_of(doc, spec.get("from", "XY"), part)
        if "from" not in spec:
            assumed["from"] = "XY"
        apt, adir = axis_of(doc, spec["about"], part)
        theta = math.radians(doc.angle(spec["deg"], assumed, deps))
        # Rodrigues: rotate the normal about the axis direction.
        c, s = math.cos(theta), math.sin(theta)
        k = adir
        n = normal
        rotated = (
            n[0] * c + (k[1] * n[2] - k[2] * n[1]) * s + k[0] * _dot(k, n) * (1 - c),
            n[1] * c + (k[2] * n[0] - k[0] * n[2]) * s + k[1] * _dot(k, n) * (1 - c),
            n[2] * c + (k[0] * n[1] - k[1] * n[0]) * s + k[2] * _dot(k, n) * (1 - c),
        )
        return _store(doc, args, Datum(name, "plane", apt, _unit(rotated, "normal"), adir))
    if "normal_at" in args:
        spec = args["normal_at"]
        if not isinstance(spec, dict) or "face" not in spec:
            raise CommandError("plane normal_at needs {face: <ref>, at: [u, v]}.", code="pk_needs")
        part = part or get_part(doc, args, assumed)
        info = face_of(doc, part, str(spec["face"])).infos[0]
        if info.normal is None:
            raise CommandError(f"{spec['face']} has no defined normal.", code="pk_plane_mismatch")
        fr = face_frame(info.centroid, info.normal, info.centroid, None)
        at = spec.get("at", [0, 0])
        if not isinstance(at, list | tuple) or len(at) != 2:
            raise CommandError("normal_at.at is [u, v] in the face frame.", code="pk_needs")
        origin = fr.to_world(doc.length(at[0], assumed, deps), doc.length(at[1], assumed, deps))
        return _store(doc, args, Datum(name, "plane", origin, info.normal, fr.xdir))
    if "midplane" in args:
        pair = args["midplane"]
        if not isinstance(pair, list | tuple) or len(pair) != 2:
            raise CommandError("midplane needs [plane a, plane b].", code="pk_needs")
        (pa, na), (pb, nb) = plane_of(doc, pair[0], part), plane_of(doc, pair[1], part)
        if abs(abs(_dot(na, nb)) - 1.0) > 1e-6:
            raise CommandError(
                "midplane needs two parallel planes; these are not parallel.", code="pk_needs"
            )
        mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2, (pa[2] + pb[2]) / 2)
        return _store(doc, args, Datum(name, "plane", mid, na, make_frame(pa, na).xdir))
    raise CommandError(
        "create plane needs one of offset:{from, distance}, through:[p, q, r], "
        "angle:{about, deg, from}, normal_at:{face, at}, midplane:[a, b].",
        code="pk_needs",
    )


@register_kind("axis")
def _k_axis(doc: Any, args: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
    name = doc.new_name(args, "axis", doc.datums)
    deps: set[str] = set()
    part = doc.parts.get(str(args.get("part"))) if args.get("part") else None
    if "through" in args:
        pts = args["through"]
        if not isinstance(pts, list | tuple) or len(pts) != 2:
            raise CommandError("axis through needs two points.", code="pk_needs")
        p, q = point_of(doc, pts[0], part, assumed), point_of(doc, pts[1], part, assumed)
        return _store(doc, args, Datum(name, "axis", p, _unit(_sub(q, p), "the axis")))
    if "along" in args:
        d = direction_of(doc, args["along"])
        at = _xyz(doc, args["at"], assumed, deps, "at") if "at" in args else (0.0, 0.0, 0.0)
        if "at" not in args:
            assumed["at"] = [0, 0, 0]
        return _store(doc, args, Datum(name, "axis", at, d))
    if "of" in args:
        part = part or get_part(doc, args, assumed)
        p, d = axis_of(doc, str(args["of"]), part)
        return _store(doc, args, Datum(name, "axis", p, d))
    raise CommandError(
        "create axis needs one of through:[p, q], along:X|Y|Z (+ at), of:<cylindrical face>.",
        code="pk_needs",
    )


@register_kind("point")
def _k_point(doc: Any, args: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
    name = doc.new_name(args, "point", doc.datums)
    deps: set[str] = set()
    part = doc.parts.get(str(args.get("part"))) if args.get("part") else None
    if "at" in args and "on" not in args:
        return _store(
            doc,
            args,
            Datum(name, "point", _xyz(doc, args["at"], assumed, deps, "at"), (0.0, 0.0, 0.0)),
        )
    if "on" in args:
        part = part or get_part(doc, args, assumed)
        info = face_of(doc, part, str(args["on"])).infos[0]
        if info.normal is None:
            raise CommandError(f"{args['on']} has no defined normal.", code="pk_plane_mismatch")
        fr = face_frame(info.centroid, info.normal, info.centroid, None)
        at = args.get("at", [0, 0])
        if not isinstance(at, list | tuple) or len(at) != 2:
            raise CommandError(
                "point on <face> takes at: [u, v] in the face frame.", code="pk_needs"
            )
        origin = fr.to_world(doc.length(at[0], assumed, deps), doc.length(at[1], assumed, deps))
        return _store(doc, args, Datum(name, "point", origin, (0.0, 0.0, 0.0)))
    raise CommandError(
        "create point needs at:[x, y, z] or on:<face> with at:[u, v].", code="pk_needs"
    )


__all__ = [
    "Datum",
    "axis_of",
    "datum",
    "direction_of",
    "face_of",
    "frame_for",
    "plane_of",
    "point_of",
]
