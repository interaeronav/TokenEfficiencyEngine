"""Extrude: a sketch profile swept along its frame normal, then one boolean.

`{sketch, distance | to:<face> | "through", direction + | - | both, mode new |
join | cut | intersect, taper, height}`. Defaults are declared, not guessed
(Law 19): `+` is the frame normal - except a cut or intersect on an `on:`
face, which goes INTO the body (`-`) because that is the only direction a
cut from a face can mean; `new` when the part is empty, else `join`; taper
0. `through` starts 1 mm behind the sketch plane and runs past the body's
extent along the direction, so the boolean never meets a coplanar face
(the F1 fixture's cylinder starts at z = -1 for the same reason).

Roles (D6): `<name>.start` (the face on the sketch plane), `<name>.end`, and
`<name>.side.<tag>` per sketch entity, read from `MakePrism.Generated(edge)`
- the tag is the sketch's, so `plate.side.r.0` is the side the line `r.0`
swept. A tapered body comes from `LocOpe_DPrism` (its height semantics are
in brep/shapes.py). OCP is imported inside functions only.
"""

from __future__ import annotations

from typing import Any

from partkiln.document import CommandError
from partkiln.features.base import Outcome, boolean, builder, name_from_tool, parse_mode
from partkiln.features.workplane import face_of, frame_for
from partkiln.sketch.profile import Frame, build_profile, split_plane_ref

Vec3 = tuple[float, float, float]


def _scale(v: Vec3, s: float) -> Vec3:
    return (v[0] * s, v[1] * s, v[2] * s)


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def extent_along(shape: Any, origin: Vec3, direction: Vec3) -> tuple[float, float]:
    """(min, max) of the body's bbox corners projected on `direction` from `origin`."""
    from partkiln.brep import shapes

    x0, y0, z0, x1, y1, z1 = shapes.bbox(shape)
    values = [
        _dot((x - origin[0], y - origin[1], z - origin[2]), direction)
        for x in (x0, x1)
        for y in (y0, y1)
        for z in (z0, z1)
    ]
    return min(values), max(values)


def cap_roles(tool: Any, direction: Vec3) -> list[tuple[str, Any]]:
    """`start` = the planar face facing against `direction`, `end` = the one facing along it."""
    from partkiln.brep import query

    roles: list[tuple[str, Any]] = []
    for f in query.faces(tool):
        if f.surface_type != "plane" or f.normal is None:
            continue
        d = _dot(f.normal, direction)
        if d <= -0.999:
            roles.append(("start", f.shape))
        elif d >= 0.999:
            roles.append(("end", f.shape))
    return roles


def side_roles(algo: Any, profile: Any, prefix: str = "side") -> list[tuple[str, Any]]:
    from partkiln.brep import shapes

    roles: list[tuple[str, Any]] = []
    for tag, edge in profile.edges:
        for g in shapes.as_list(algo.Generated(edge)):
            if g.ShapeType().name == "TopAbs_FACE":
                roles.append((f"{prefix}.{tag}", g))
    return roles


@builder("extrude")
def build_extrude(doc: Any, part: Any, feature: Any, assumed: dict[str, Any]) -> Outcome:
    from partkiln.brep import shapes

    args = feature.args
    if not args.get("sketch"):
        raise CommandError(
            f"extrude {feature.id} needs sketch: <name> and distance (or to:<face> / through).",
            code="pk_needs",
        )
    sketch = doc.sketch(args["sketch"])
    feature.depends.add(f"sk:{sketch.name}")
    feature.refs.append(f"sk:{sketch.name}")
    plane_kind, _ref, _at = split_plane_ref(sketch.plane)
    mode = parse_mode(args, part, assumed)
    frame = frame_for(doc, sketch.plane, part, feature)
    deps = feature.param_deps

    raw_dir = args.get("direction")
    if raw_dir is None:
        direction = "-" if (mode in ("cut", "intersect") and plane_kind == "on") else "+"
        assumed["direction"] = direction if direction == "+" else "- (into the body)"
    else:
        direction = str(raw_dir)
        if direction not in ("+", "-", "both"):
            raise CommandError(f"direction {raw_dir!r} is +, - or both.", code="pk_needs")
    sign = -1.0 if direction == "-" else 1.0
    along: Vec3 = _scale(frame.normal, sign)

    taper = doc.angle(args["taper"], assumed, deps) if "taper" in args else 0.0
    if "taper" not in args:
        assumed.setdefault("taper", 0)
    height_mode = str(args.get("height", "vertical"))

    distance_raw = args.get("distance")
    to_ref = args.get("to")
    start_frame: Frame = frame
    if to_ref is not None:
        if part.shape is None:
            raise CommandError(
                f"extrude {feature.id}: to:<face> needs a body to reach.", code="pk_needs"
            )
        target = face_of(doc, part, str(to_ref), feature).infos[0]
        distance = _dot(
            (
                target.centroid[0] - frame.origin[0],
                target.centroid[1] - frame.origin[1],
                target.centroid[2] - frame.origin[2],
            ),
            along,
        )
        if distance <= 1e-6:
            raise CommandError(
                f"extrude {feature.id}: face {to_ref} lies {abs(distance):.3f} mm BEHIND the "
                f"sketch plane along {direction}; flip direction or pick the face ahead.",
                code="pk_needs",
            )
        feature.resolved[f"to {to_ref}"] = round(distance, 3)
    elif distance_raw == "through":
        if mode not in ("cut", "intersect") or part.shape is None:
            raise CommandError(
                f"extrude {feature.id}: 'through' is for a cut or intersect of an existing body; "
                "give a distance for a new body or a join.",
                code="pk_needs",
            )
        lo, hi = extent_along(part.shape, frame.origin, along)
        if direction == "both":
            start_frame = frame.shifted(-(abs(lo) + 1.0))
            distance = abs(lo) + hi + 2.0
        else:
            start_frame = frame.shifted(-1.0 * sign)
            distance = max(hi, 0.0) + 2.0
        assumed["through"] = f"{round(distance, 3)} mm from 1 mm behind the plane"
    elif distance_raw is None:
        raise CommandError(
            f"extrude {feature.id} needs distance (a length), to:<face ref> or "
            "distance: through (cut/intersect).",
            code="pk_needs",
        )
    else:
        distance = doc.length(distance_raw, assumed, deps)
        if distance <= 0:
            raise CommandError(
                f"extrude {feature.id}: distance must be > 0 (got {distance:g} mm); use "
                "direction: - to go the other way.",
                code="pk_needs",
            )
        if direction == "both":
            start_frame = frame.shifted(-distance / 2.0)
            assumed["both"] = "distance is the total, split equally about the plane"
    vec = _scale(along, distance)

    profile = build_profile(sketch, start_frame)
    assumed.update(profile.assumed)
    if taper and len(profile.faces) > 1:
        raise CommandError(
            f"extrude {feature.id}: a taper needs a single-loop profile; sketch {sketch.name} "
            f"has {len(profile.faces)} outer loops.",
            code="pk_needs",
        )
    tools: list[Any] = []
    tool_roles: list[tuple[str, Any]] = []
    multi = len(profile.faces) > 1
    for k, face in enumerate(profile.faces):
        res = shapes.prism(face, vec, taper_deg=taper, height=height_mode)
        if not res.is_done:
            raise CommandError(
                f"extrude {feature.id}: OCCT could not build the prism.", code="pk_op_failed"
            )
        tools.append(res.shape)
        suffix = f".{k}" if multi else ""
        tool_roles.extend((role + suffix, sub) for role, sub in cap_roles(res.shape, along))
        tool_roles.extend((role + suffix, sub) for role, sub in side_roles(res.algo, profile))

    if mode == "new":
        if len(tools) == 1:
            shape, hist = tools[0], None
        else:
            from partkiln.brep import history

            fused = shapes.fuse(tools)
            shape, hist = fused.shape, history.from_algo(fused.history)
    else:
        shape, hist = boolean(part.shape, tools, mode, feature, bool(args.get("allow_no_effect")))
    names = name_from_tool(hist, shape, feature.id, tool_roles)
    cosmetic = {"thread": str(args["thread"])} if args.get("thread") else {}
    extra = {
        "distance_mm": round(distance, 3),
        "direction": direction,
        "area_mm2": profile.area_mm2,
    }
    if taper:
        extra["taper_deg"] = round(taper, 3)
        if abs(taper) > 0 and "height" not in args:
            assumed["height"] = "vertical (|distance| reached; along_wall gives OCCT's raw height)"
    return Outcome(
        shape,
        hist,
        names,
        tools,
        tool_roles,
        mode,
        frame=frame,
        cosmetic=cosmetic,
        extra=extra,
    )


__all__ = ["build_extrude", "cap_roles", "extent_along", "side_roles"]
