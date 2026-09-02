"""Revolve: a sketch profile turned about an axis, then one boolean.

`{sketch, axis X | Y | Z | axis:<datum> | [[p], [d]] | <cylindrical face>,
angle (360), mode}`. A letter axis is read in the SKETCH frame through the
frame origin (a profile drawn in XY revolved about `X` turns about the
sketch's x axis, which is what a shaft drawing means); a datum, a literal
or a face is world geometry. F3's stepped shaft (d20 x 50 / d30 x 30 / d20 x
40) is pi * 15 750 = 49 480.084 mm3 with 7 faces.

Roles: every face generated from a profile segment is `<name>.<tag>` (the
sketch tag, so `shaft.p.1` is the face the line `p.1` swept - a stepped
shaft needs a name per step, which is why D6's `outer/inner` pair is not
enough and is not materialised); `cap.a` / `cap.b` are the two end faces of
a partial revolve. Measured (OCP 7.9.3): for a FULL 360 deg revolve
`MakeRevol.Generated(edge)` answers only for the edges that sweep curved
faces; a radial edge's planar annulus/disk comes back empty (at 180 deg it
does not). Those faces are matched geometrically instead: same axial
position as the edge's midpoint and the area pi * |r2^2 - r1^2| the edge's
end radii predict. OCP is imported inside functions only.
"""

from __future__ import annotations

import math
from typing import Any

from partkiln.document import CommandError
from partkiln.features.base import Outcome, boolean, builder, name_from_tool, parse_mode
from partkiln.features.extrude import side_roles
from partkiln.features.workplane import axis_of, frame_for
from partkiln.sketch.profile import build_profile

Vec3 = tuple[float, float, float]


def _axial_radial(p: Vec3, point: Vec3, direction: Vec3) -> tuple[float, float]:
    d = (p[0] - point[0], p[1] - point[1], p[2] - point[2])
    axial = d[0] * direction[0] + d[1] * direction[1] + d[2] * direction[2]
    rad = (d[0] - axial * direction[0], d[1] - axial * direction[1], d[2] - axial * direction[2])
    return axial, math.sqrt(rad[0] ** 2 + rad[1] ** 2 + rad[2] ** 2)


def planar_roles(
    shape: Any, profile: Any, named: set[str], point: Vec3, direction: Vec3
) -> list[tuple[str, Any]]:
    """The planar faces a full revolve makes from radial edges, by geometry."""
    from OCP.BRep import BRep_Tool
    from OCP.TopExp import TopExp

    from partkiln.brep import query

    faces = [f for f in query.faces(shape) if f.surface_type == "plane"]
    roles: list[tuple[str, Any]] = []
    for tag, edge in profile.edges:
        if tag in named:
            continue
        a = BRep_Tool.Pnt_s(TopExp.FirstVertex_s(edge))
        b = BRep_Tool.Pnt_s(TopExp.LastVertex_s(edge))
        xa, ra = _axial_radial((a.X(), a.Y(), a.Z()), point, direction)
        xb, rb = _axial_radial((b.X(), b.Y(), b.Z()), point, direction)
        if abs(xa - xb) > 1e-6 or abs(ra - rb) < 1e-9:
            continue  # not a radial edge (axial, or on the axis)
        area = math.pi * abs(rb * rb - ra * ra)
        for f in faces:
            xf, _ = _axial_radial(f.centroid, point, direction)
            if abs(xf - xa) <= 1e-6 and abs(f.area - area) <= max(1e-6, 1e-9 * area):
                roles.append((tag, f.shape))
                break
    return roles


@builder("revolve")
def build_revolve(doc: Any, part: Any, feature: Any, assumed: dict[str, Any]) -> Outcome:
    from partkiln.brep import shapes

    args = feature.args
    if not args.get("sketch") or args.get("axis") is None:
        raise CommandError(
            f"revolve {feature.id} needs sketch: <name> and axis: X | Y | Z | axis:<datum> | "
            "[[px,py,pz],[dx,dy,dz]] | <cylindrical face>.",
            code="pk_needs",
        )
    sketch = doc.sketch(args["sketch"])
    feature.depends.add(f"sk:{sketch.name}")
    feature.refs.append(f"sk:{sketch.name}")
    mode = parse_mode(args, part, assumed)
    frame = frame_for(doc, sketch.plane, part, feature)
    deps = feature.param_deps
    point, direction = axis_of(doc, args["axis"], part, feature, frame=frame)
    if "angle" in args:
        angle = doc.angle(args["angle"], assumed, deps)
    else:
        angle = 360.0
        assumed["angle"] = 360
    if not 0 < angle <= 360:
        raise CommandError(
            f"revolve {feature.id}: angle must be in (0, 360], got {angle:g}.", code="pk_needs"
        )
    profile = build_profile(sketch, frame)
    tools: list[Any] = []
    tool_roles: list[tuple[str, Any]] = []
    multi = len(profile.faces) > 1
    for k, face in enumerate(profile.faces):
        res = shapes.revolve(face, point, direction, angle)
        if not res.is_done:
            raise CommandError(
                f"revolve {feature.id}: OCCT could not revolve the profile (does it cross the "
                "axis?).",
                code="pk_op_failed",
            )
        suffix = f".{k}" if multi else ""
        tools.append(res.shape)
        swept = [(role[len("side.") :], sub) for role, sub in side_roles(res.algo, profile)]
        if angle >= 360:
            swept.extend(planar_roles(res.shape, profile, {r for r, _ in swept}, point, direction))
        tool_roles.extend((role + suffix, sub) for role, sub in swept)
        if angle < 360:
            tool_roles.append(("cap.a" + suffix, res.algo.FirstShape()))
            tool_roles.append(("cap.b" + suffix, res.algo.LastShape()))
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
    if cosmetic:
        feature.notes.append(
            f"thread {cosmetic['thread']} is cosmetic: no geometry changed (Law 18)"
        )
    return Outcome(
        shape,
        hist,
        names,
        tools,
        tool_roles,
        mode,
        frame=frame,
        cosmetic=cosmetic,
        extra={"angle_deg": round(angle, 3), "area_mm2": profile.area_mm2},
    )


__all__ = ["build_revolve"]
