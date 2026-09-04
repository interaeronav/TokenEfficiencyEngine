"""Coil: a true helical sweep - a profile carried along a helix, then one boolean.

`{profile: <closed sketch>, axis, pitch, turns | height, hand right|left,
taper, section normal|axial, mode}`. The coil radius is NOT a property: it
is where the profile is, measured from the axis to the profile's centroid,
which is how a coil is specified in a parametric CAD sketch (draw the wire
section 10 mm off the axis and it coils at R10).

The helix is OCCT's own: a straight `Geom2d_Line` of slope `pitch / 2*pi`
laid on a `Geom_CylindricalSurface` (or a `Geom_ConicalSurface` when the
coil tapers), turned into an edge by `BRepBuilderAPI_MakeEdge(curve2d,
surface, u1, u2)` and given its 3D curve by `BRepLib.BuildCurves3d_s`, then
swept with `BRepOffsetAPI_MakePipeShell`. Measured on OCP 7.9.3 (this Mac,
2026-09-04) for the acceptance spring - wire d2, mean coil d20, pitch 5, 6
turns:

* helix length 378.182 882 mm against `sqrt((pi*D)^2 + p^2) * turns` =
  378.182 897 mm - a 1.5e-5 mm difference, which is `GCPnts_AbscissaPoint`'s
  integration, not the curve;
* `section: normal` (the profile is the WIRE's own section, carried
  perpendicular to the helix - `Add(wire, contact=False, correction=True)`)
  gives 1 188.096 1 mm3 against the torus approximation `A * L` =
  pi * 1^2 * 378.182 882 = 1 188.096 6 mm3, relative -4.0e-7;
* `section: axial` (the profile stays in the plane it was drawn in -
  `correction=False`, Inventor's coil) gives 1 184.352 0 mm3 against Pappus
  on the HORIZONTAL travel, `A * pi*D * turns` = 1 184.352 5, relative
  -4.0e-7. The two differ by 1/cos(lead angle) = 0.3 % here, so the section
  rule is echoed in `assumed` every time.

Both are exact to seven figures, so the coil is pinned against arithmetic,
not against a golden file. `taper` is the cone half-angle: the radius grows
by `pitch * tan(taper)` per turn, and a taper that would drive the radius to
zero refuses rather than building a degenerate cone.

Roles: `<name>.side.<tag>` per profile segment, `<name>.cap.a` / `.cap.b`.
OCP is imported inside functions only.
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

# A cone whose half-angle reaches this is a point, not a coil; OCCT's own
# `Geom_ConicalSurface` refuses |Ang| >= pi/2 outright.
_MAX_TAPER_DEG = 80.0


def helix_edge(
    radius: float,
    pitch: float,
    turns: float,
    origin: Vec3,
    direction: Vec3,
    xdir: Vec3,
    hand: str = "right",
    taper_deg: float = 0.0,
) -> Any:
    """The helix edge starting at `origin + radius * xdir` and climbing `direction`.

    A left-hand helix is the SAME climb with the winding reversed, so the 2D
    line runs `(-1, slope)` rather than `(1, slope)`: negating the slope
    instead would send the curve down the axis and out of the body (measured:
    that variant lost the whole thread in the boolean).
    """
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
    from OCP.BRepLib import BRepLib
    from OCP.Geom import Geom_ConicalSurface, Geom_CylindricalSurface
    from OCP.Geom2d import Geom2d_Line
    from OCP.gp import gp_Ax3, gp_Dir, gp_Dir2d, gp_Pnt, gp_Pnt2d

    ax3 = gp_Ax3(gp_Pnt(*origin), gp_Dir(*direction), gp_Dir(*xdir))
    if abs(taper_deg) < 1e-12:
        surface: Any = Geom_CylindricalSurface(ax3, radius)
        slope = pitch / (2.0 * math.pi)
    else:
        ang = math.radians(taper_deg)
        surface = Geom_ConicalSurface(ax3, ang, radius)
        # v runs along the SLANT of the cone, so a full turn must advance v by
        # pitch / cos(ang) to climb `pitch` along the axis.
        slope = pitch / (2.0 * math.pi * math.cos(ang))
    u_sign = -1.0 if hand == "left" else 1.0
    line = Geom2d_Line(gp_Pnt2d(0.0, 0.0), gp_Dir2d(u_sign, slope))
    # The 2D line is parametrised by distance in (u, v), and one turn is 2*pi
    # of u, so the edge ends at turns * 2*pi * hypot(1, slope).
    last = turns * 2.0 * math.pi * math.hypot(1.0, slope)
    edge = BRepBuilderAPI_MakeEdge(line, surface, 0.0, last).Edge()
    BRepLib.BuildCurves3d_s(edge)
    return edge


def helix_wire(*args: Any, **kwargs: Any) -> Any:
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeWire

    return BRepBuilderAPI_MakeWire(helix_edge(*args, **kwargs)).Wire()


def curve_length(edge: Any) -> float:
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.GCPnts import GCPnts_AbscissaPoint

    return float(GCPnts_AbscissaPoint.Length_s(BRepAdaptor_Curve(edge)))


def count(doc: Any, value: Any, deps: set[str] | None = None) -> float:
    """A UNITLESS number (turns): a bare value or a parameter expression.

    `doc.length` would happily read `turns: "6mm"`, so turns goes through the
    expression evaluator directly - a count has no unit, and Law 12's "a bare
    number is millimetres" must not leak into one.
    """
    from partkiln import params as _params

    evaluated = doc.params.evaluate(value)
    if evaluated.kind != _params.SCALAR:
        raise CommandError(
            f"turns is a count, not {'a ' + evaluated.kind}: {value!r} carries a unit. "
            "Write turns: 6 (or height: 30mm for the same coil).",
            code="pk_unit_kind",
        )
    if deps is not None:
        deps.update(evaluated.depends_on)
    return float(evaluated.value)


def _centroid(face: Any) -> Vec3:
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps

    props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(face, props)
    c = props.CentreOfMass()
    return (c.X(), c.Y(), c.Z())


def _axis_frame(point: Vec3, direction: Vec3, target: Vec3) -> tuple[float, float, Vec3]:
    """(axial offset, radius, unit radial direction) of `target` about the axis."""
    delta = (target[0] - point[0], target[1] - point[1], target[2] - point[2])
    axial = sum(delta[i] * direction[i] for i in range(3))
    radial = tuple(delta[i] - axial * direction[i] for i in range(3))
    radius = math.sqrt(sum(c * c for c in radial))
    if radius < 1e-9:
        return axial, 0.0, (1.0, 0.0, 0.0)
    return axial, radius, (radial[0] / radius, radial[1] / radius, radial[2] / radius)


def _pipe(spine: Any, wire: Any, correction: bool) -> Any:
    """`MakePipeShell` over a helix, raising the kernel's own error on failure."""
    from OCP.BRepOffsetAPI import BRepOffsetAPI_MakePipeShell

    from partkiln._errors import KernelError

    algo = BRepOffsetAPI_MakePipeShell(spine)
    algo.SetMode(True)  # Frenet: a helix has no inflection, so it never flips
    algo.Add(wire, False, correction)
    algo.Build()
    if not algo.IsDone():
        raise KernelError(
            f"the helical sweep failed (status {algo.GetStatus().name}).",
            fix="reduce the profile size, the taper or the pitch: a section wider than the "
            "pitch overlaps itself turn on turn",
            code="pk_op_failed",
        )
    if not algo.MakeSolid():
        raise KernelError(
            "the helical sweep produced an open shell, not a solid.",
            fix="the profile must be one closed loop",
            code="pk_op_failed",
        )
    return algo


@builder("coil")
def build_coil(doc: Any, part: Any, feature: Any, assumed: dict[str, Any]) -> Outcome:
    args = feature.args
    if not args.get("profile") or args.get("axis") is None:
        raise CommandError(
            f"coil {feature.id} needs profile: <closed sketch> and axis: X | Y | Z | "
            "axis:<datum> | [[px,py,pz],[dx,dy,dz]] | <cylindrical face>.",
            code="pk_needs",
        )
    sketch = doc.sketch(args["profile"])
    feature.depends.add(f"sk:{sketch.name}")
    feature.refs.append(f"sk:{sketch.name}")
    mode = parse_mode(args, part, assumed)
    deps = feature.param_deps
    frame = frame_for(doc, sketch.plane, part, feature)
    point, direction = axis_of(doc, args["axis"], part, feature, frame=frame)

    if args.get("pitch") is None:
        raise CommandError(
            f"coil {feature.id} needs pitch: <len> (the rise per turn).", code="pk_needs"
        )
    pitch = doc.length(args["pitch"], assumed, deps)
    if pitch <= 0:
        raise CommandError(
            f"coil {feature.id}: pitch must be > 0, got {pitch:g} mm.", code="pk_needs"
        )
    has_turns, has_height = args.get("turns") is not None, args.get("height") is not None
    if has_turns and has_height:
        raise CommandError(
            f"coil {feature.id}: give turns OR height, not both (height = turns * pitch).",
            code="pk_spec_conflict",
        )
    if has_turns:
        turns = count(doc, args["turns"], deps)
    elif has_height:
        turns = doc.length(args["height"], assumed, deps) / pitch
        assumed["turns"] = round(turns, 6)
    else:
        raise CommandError(f"coil {feature.id} needs turns: <n> or height: <len>.", code="pk_needs")
    if turns <= 0:
        raise CommandError(f"coil {feature.id}: turns must be > 0, got {turns:g}.", code="pk_needs")

    hand = str(args.get("hand", "right")).lower()
    if hand not in ("right", "left"):
        raise CommandError(
            f"coil {feature.id}: hand is 'right' or 'left', not {args.get('hand')!r}.",
            code="pk_needs",
        )
    if "hand" not in args:
        assumed["hand"] = "right"
    taper = doc.angle(args["taper"], assumed, deps) if args.get("taper") is not None else 0.0
    if "taper" not in args:
        assumed["taper"] = 0
    if abs(taper) >= _MAX_TAPER_DEG:
        raise CommandError(
            f"coil {feature.id}: taper must be within +-{_MAX_TAPER_DEG:g} deg, got {taper:g} deg.",
            code="pk_needs",
        )
    section = str(args.get("section", "normal")).lower()
    if section not in ("normal", "axial"):
        raise CommandError(
            f"coil {feature.id}: section is 'normal' (the profile is the wire's own section, "
            "carried perpendicular to the helix) or 'axial' (it stays in the plane it was "
            f"drawn in), not {args.get('section')!r}.",
            code="pk_needs",
        )
    if "section" not in args:
        assumed["section"] = "normal"

    profile = build_profile(sketch, frame)
    if len(profile.faces) != 1:
        raise CommandError(
            f"coil {feature.id}: the profile must be one closed loop; {sketch.name} has "
            f"{len(profile.faces)}.",
            code="pk_needs",
        )
    axial, radius, xdir = _axis_frame(point, direction, _centroid(profile.faces[0]))
    if radius < 1e-6:
        raise CommandError(
            f"coil {feature.id}: the profile's centroid sits ON the axis, so the coil has no "
            "radius. Move the profile off the axis - its distance from the axis IS the mean "
            "coil radius.",
            code="pk_spec_conflict",
        )
    end_radius = radius + turns * pitch * math.tan(math.radians(taper))
    if end_radius <= 1e-6:
        raise CommandError(
            f"coil {feature.id}: taper {taper:g} deg over {turns:g} turns closes the coil "
            f"radius from {radius:.3f} mm to {end_radius:.3f} mm. Reduce the taper, the turns "
            "or the pitch.",
            code="pk_spec_conflict",
        )

    origin = tuple(point[i] + axial * direction[i] for i in range(3))
    edge = helix_edge(radius, pitch, turns, origin, direction, xdir, hand, taper)
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeWire
    from OCP.BRepTools import BRepTools

    spine = BRepBuilderAPI_MakeWire(edge).Wire()
    algo = _pipe(spine, BRepTools.OuterWire_s(profile.faces[0]), section == "normal")
    tool = algo.Shape()
    tool_roles = list(side_roles(algo, profile))
    tool_roles.append(("cap.a", algo.FirstShape()))
    tool_roles.append(("cap.b", algo.LastShape()))

    if mode == "new":
        shape, hist = tool, None
    else:
        shape, hist = boolean(part.shape, [tool], mode, feature, bool(args.get("allow_no_effect")))
    names = name_from_tool(hist, shape, feature.id, tool_roles)
    helix_mm = curve_length(edge)
    extra = {
        "turns": round(turns, 6),
        "pitch_mm": round(pitch, 3),
        "radius_mm": round(radius, 3),
        "end_radius_mm": round(end_radius, 3),
        "helix_mm": round(helix_mm, 3),
        "height_mm": round(turns * pitch, 3),
        "taper_deg": round(taper, 3),
        "hand": hand,
        "section": section,
        "area_mm2": profile.area_mm2,
    }
    return Outcome(shape, hist, names, [tool], tool_roles, mode, frame=frame, extra=extra)


__all__ = ["build_coil", "count", "curve_length", "helix_edge", "helix_wire"]
