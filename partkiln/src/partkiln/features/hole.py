"""Holes: drilled from a face, one n-ary cut, sized from a diameter or a standard.

`{on: <face ref>, at: [[x, y], ...] in the face frame, dia | std: "M6
clearance normal|close|loose" | "M6 tap", depth through | <len>, seat:
{kind: counterbore | countersink | spotface, dia, depth | angle}, thread:
"M6"}`. The face frame is the one profile.py gives an `on:` sketch (outward
normal, origin = the world origin projected onto the face, x along world
X), so "at (50, 30) on plate.end" of a plate at the origin is the F1 hole.

Every tool starts 1 mm above the face and, for `through`, runs 1 mm past
the body's extent along the drill direction (the F1 fixture's z = -1..11);
all instances are ONE `BRepAlgoAPI_Cut` (measured: 100 holes 0.09 s n-ary
against 0.46 s sequentially). A standard size carries its source into
`assumed` and a note (ISO 273 clearance via bd_warehouse, Apache-2.0; tap
drills likewise). A thread is COSMETIC (Law 18): it is stored on the
feature, echoed in the diff, and changes no geometry - the fingerprint is
bit-identical with or without it. `fit: "H7"` is cosmetic for the same
reason: the bore is cut at its BASIC size and the ISO 286 class only records
the two limits it must be inspected to, so the diff carries `fit_min_mm` /
`fit_max_mm` and the solid does not move. A fit partkiln cannot derive
(`H7` at 8 mm, `P7` anywhere) refuses `pk_not_served` from `standards`
rather than inventing limits - see `standards.fit`. Measured seats on F1: counterbore d11 x 6
removes 98.96 mm3, countersink 90 deg d12 on d10 removes 16.755 more.

`count` is the number of holes that MATERIALISED, never `len(at)`: a tool
whose point lies off the face cuts nothing, and a feature that reports what
it was asked for instead of what it did is Law 11's silent failure one level
up. A hole counts when its `.wall` role survives the boolean (that is the
drilled cylinder, and `name_from_tool` already followed each tool through
the history to find it). The points that cut nothing are named in a note;
if NONE cut, the feature refuses `pk_no_effect` unless `allow_no_effect` is
set - the same contract `boolean()` applies to the body as a whole.

Roles: `<name>.<i>.wall` (the drilled cylinder, i from 1), `.bottom` (a
blind hole's flat floor), `.seat` (the counterbore floor / the countersink
cone) and `.seat.wall` (the counterbore cylinder). OCP is imported inside
functions only.
"""

from __future__ import annotations

import math
from typing import Any

from partkiln.document import CommandError
from partkiln.features.base import Outcome, boolean, builder, name_from_tool, one
from partkiln.features.extrude import extent_along
from partkiln.sketch.profile import Frame, face_frame

_SEATS = ("counterbore", "countersink", "spotface")


def _std(spec: str, assumed: dict[str, Any], notes: list[str]) -> tuple[float, dict[str, Any]]:
    """'M6 clearance normal' | 'M6 clearance' | 'M6 tap' -> (dia_mm, cosmetic)."""
    from partkiln import standards

    words = str(spec).split()
    if len(words) < 2:
        raise CommandError(
            f"std {spec!r} is not a hole standard. Forms: 'M6 clearance normal|close|loose' "
            "(ISO 273) or 'M6 tap' (the tap drill).",
            code="pk_needs",
        )
    size, what = words[0], words[1].lower()
    if what == "clearance":
        series = words[2].lower() if len(words) > 2 else "normal"
        if len(words) <= 2:
            assumed["series"] = "normal"
        row = standards.clearance_hole(size, series)
        dia = row["dia_mm"]
        assumed["dia"] = (
            f"{dia:g}mm from {row['authority']} {series} "
            f"({row['source'].split('/')[2]}, {row['licence']})"
        )
        notes.append(
            f"{row['size']} clearance {series}: {dia:g} mm per {row['authority']} "
            f"({row['licence']})"
        )
        return dia, {}
    if what == "tap":
        row = standards.tap_drill(size)
        dia = row["drill_mm"]
        assumed["dia"] = f"{dia:g}mm tap drill for {row['size']} ({row['licence']})"
        notes.append(
            f"{row['size']} tap drill {dia:g} mm (soft material) - thread {row['size']} cosmetic"
        )
        return dia, {"thread": row["size"]}
    raise CommandError(
        f"std {spec!r}: the second word is 'clearance' or 'tap', not {words[1]!r}.",
        code="pk_needs",
    )


@builder("hole")
def build_hole(doc: Any, part: Any, feature: Any, assumed: dict[str, Any]) -> Outcome:
    from partkiln.brep import shapes

    args = feature.args
    if part.shape is None:
        raise CommandError(
            f"hole {feature.id}: part {part.name} has no body to drill.", code="pk_needs"
        )
    res = one(part, feature, args.get("on"), "face", "on: <face ref>")
    face = res.infos[0]
    if face.surface_type != "plane" or face.normal is None:
        raise CommandError(
            f"hole {feature.id}: {args.get('on')} is a {face.surface_type} face; drill from a "
            "plane.",
            code="pk_plane_mismatch",
        )
    at_mode = str(args.get("frame", "origin"))
    if at_mode not in ("origin", "centroid"):
        raise CommandError(
            "frame is 'origin' (the world origin projected) or 'centroid'.", code="pk_needs"
        )
    if "frame" not in args:
        assumed["frame"] = "origin projected onto the face, x along world X"
    frame: Frame = face_frame(
        face.centroid, face.normal, face.centroid, "centroid" if at_mode == "centroid" else None
    )
    deps = feature.param_deps

    raw_at = args.get("at")
    if raw_at is None:
        raise CommandError(
            f"hole {feature.id} needs at: [[x, y], ...] in the face frame.", code="pk_needs"
        )
    if (
        isinstance(raw_at, list | tuple)
        and len(raw_at) == 2
        and not isinstance(raw_at[0], list | tuple)
    ):
        raw_at = [raw_at]
    points: list[tuple[float, float]] = []
    for p in raw_at:
        if not isinstance(p, list | tuple) or len(p) != 2:
            raise CommandError(
                f"hole {feature.id}: at entries are [x, y]; got {p!r}.", code="pk_needs"
            )
        points.append((doc.length(p[0], assumed, deps), doc.length(p[1], assumed, deps)))

    notes: list[str] = []
    cosmetic: dict[str, Any] = {}
    if args.get("std") is not None:
        if args.get("dia") is not None:
            raise CommandError(
                f"hole {feature.id}: give dia OR std, not both.", code="pk_spec_conflict"
            )
        dia, cosmetic = _std(str(args["std"]), assumed, notes)
    elif args.get("dia") is not None:
        dia = doc.length(args["dia"], assumed, deps)
    else:
        raise CommandError(
            f"hole {feature.id} needs dia: <len> or std: 'M6 clearance normal' | 'M6 tap'.",
            code="pk_needs",
        )
    if dia <= 0:
        raise CommandError(f"hole {feature.id}: dia must be > 0, got {dia:g} mm.", code="pk_needs")
    fit_extra: dict[str, Any] = {}
    if args.get("fit") is not None:
        if args.get("std") is not None:
            raise CommandError(
                f"hole {feature.id}: give fit OR std, not both - a clearance or tap-drill hole "
                "is sized by its own standard, not to an ISO 286 class.",
                code="pk_spec_conflict",
            )
        fit_extra = _fit(str(args["fit"]), dia, feature.id, notes, cosmetic)
    if args.get("thread"):
        cosmetic["thread"] = str(args["thread"])
    if cosmetic.get("thread"):
        notes.append(f"thread {cosmetic['thread']} is cosmetic: no geometry changed (Law 18)")

    n = face.normal
    drill = (-n[0], -n[1], -n[2])
    depth_raw = args.get("depth", "through")
    if "depth" not in args:
        assumed["depth"] = "through"
    if depth_raw == "through":
        _lo, hi = extent_along(part.shape, frame.origin, drill)
        length = max(hi, 0.0) + 2.0
        through = True
    else:
        depth = doc.length(depth_raw, assumed, deps)
        if depth <= 0:
            raise CommandError(
                f"hole {feature.id}: depth must be > 0 or 'through'.", code="pk_needs"
            )
        length = depth + 1.0
        through = False
        if "bottom" not in args:
            assumed["bottom"] = "flat"

    seat = args.get("seat")
    seat_kind = ""
    seat_dia = seat_depth = seat_angle = 0.0
    if seat is not None:
        if not isinstance(seat, dict) or seat.get("kind") not in _SEATS:
            raise CommandError(
                f"hole {feature.id}: seat is {{kind: counterbore | countersink | spotface, dia, "
                "depth | angle}}.",
                code="pk_needs",
            )
        seat_kind = str(seat["kind"])
        if "dia" not in seat:
            raise CommandError(f"hole {feature.id}: seat needs dia.", code="pk_needs")
        seat_dia = doc.length(seat["dia"], assumed, deps)
        if seat_dia <= dia:
            raise CommandError(
                f"hole {feature.id}: seat dia {seat_dia:g} mm must exceed the hole dia {dia:g} mm.",
                code="pk_needs",
            )
        if seat_kind == "countersink":
            seat_angle = doc.angle(seat["angle"], assumed, deps) if "angle" in seat else 90.0
            if "angle" not in seat:
                assumed["seat_angle"] = 90
            if not 0 < seat_angle < 180:
                raise CommandError(
                    f"hole {feature.id}: countersink angle in (0, 180).", code="pk_needs"
                )
        else:
            if "depth" not in seat:
                raise CommandError(f"hole {feature.id}: {seat_kind} needs depth.", code="pk_needs")
            seat_depth = doc.length(seat["depth"], assumed, deps)
            if seat_depth <= 0:
                raise CommandError(f"hole {feature.id}: seat depth must be > 0.", code="pk_needs")

    tools: list[Any] = []
    tool_roles: list[tuple[str, Any]] = []
    for i, (x, y) in enumerate(points, start=1):
        top = frame.to_world(x, y, 1.0)  # 1 mm above the face
        cyl = shapes.cylinder(dia / 2.0, length, top, drill)
        tools.append(cyl)
        for f in _faces(cyl):
            if f.surface_type == "cylinder":
                tool_roles.append((f"{i}.wall", f.shape))
            elif not through and f.normal is not None and _dot(f.normal, drill) > 0.999:
                tool_roles.append((f"{i}.bottom", f.shape))
        if seat_kind in ("counterbore", "spotface"):
            cb = shapes.cylinder(seat_dia / 2.0, seat_depth + 1.0, top, drill)
            tools.append(cb)
            for f in _faces(cb):
                if f.surface_type == "cylinder":
                    tool_roles.append((f"{i}.seat.wall", f.shape))
                elif f.normal is not None and _dot(f.normal, drill) > 0.999:
                    tool_roles.append((f"{i}.seat", f.shape))
        elif seat_kind == "countersink":
            half = math.radians(seat_angle / 2.0)
            r_top = seat_dia / 2.0 + math.tan(half) * 1.0
            h = (seat_dia / 2.0 - dia / 2.0) / math.tan(half)
            cone = shapes.cone(r_top, dia / 2.0, h + 1.0, top, drill)
            tools.append(cone)
            for f in _faces(cone):
                if f.surface_type == "cone":
                    tool_roles.append((f"{i}.seat", f.shape))
    allow_no_effect = bool(args.get("allow_no_effect"))
    shape, hist = boolean(part.shape, tools, "cut", feature, allow_no_effect)
    names = name_from_tool(hist, shape, feature.id, tool_roles)
    drilled = {
        int(role.split(".")[0]) for _n, role, _s in names if role.split(".")[1:2] == ["wall"]
    }
    missed = [i for i in range(1, len(points) + 1) if i not in drilled]
    if missed:
        listed = ", ".join(f"({points[i - 1][0]:g}, {points[i - 1][1]:g})" for i in missed)
        where = f"{listed} in the frame of {args.get('on')}"
        if not drilled and not allow_no_effect:
            raise CommandError(
                f"hole {feature.id}: none of the {len(points)} holes materialised - no drilled "
                f"wall survives the cut. {where} lie off the face. Check `at` against the face "
                "frame (x along world X from the projected origin), or pass allow_no_effect: "
                "true to keep the feature.",
                code="pk_no_effect",
            )
        notes.append(
            f"{len(missed)} of {len(points)} points cut nothing and made no hole: {where}."
        )
    extra: dict[str, Any] = {
        "dia_mm": round(dia, 3),
        "count": len(drilled),
        "requested": len(points),
        "through": through,
    }
    if missed:
        extra["missed"] = len(missed)
    extra.update(fit_extra)
    if seat_kind:
        extra["seat"] = seat_kind
    return Outcome(
        shape,
        hist,
        names,
        tools,
        tool_roles,
        "cut",
        frame=frame,
        notes=notes,
        cosmetic=cosmetic,
        extra=extra,
    )


def _fit(
    spec: str, dia: float, feature_id: str, notes: list[str], cosmetic: dict[str, Any]
) -> dict[str, Any]:
    """An ISO 286 hole class on the drilled diameter: limits recorded, geometry untouched."""
    from partkiln import standards

    row = standards.limits(dia, spec)
    if row["applies"] != "hole":
        raise CommandError(
            f"hole {feature_id}: fit {spec!r} is a SHAFT class; a bore takes the capital "
            f"letter, e.g. {spec.upper()}.",
            code="pk_needs",
        )
    cosmetic["fit"] = row["class"]
    notes.append(
        f"fit {row['class']} on {dia:g} mm: {row['min_mm']:.4g}/{row['max_mm']:.4g} mm "
        f"(IT {row['it_um']:g} um, {row['basis']} from {row['authority'].split(',')[0]}) - "
        "the bore is cut at its basic size, the class changes no geometry (Law 18)"
    )
    return {
        "fit": row["class"],
        "fit_min_mm": row["min_mm"],
        "fit_max_mm": row["max_mm"],
        "fit_it_um": row["it_um"],
        "fit_basis": row["basis"],
    }


def _faces(shape: Any) -> list[Any]:
    from partkiln.brep import query

    return query.faces(shape)


def _dot(a: Any, b: Any) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


__all__ = ["build_hole"]
