"""Threads: cosmetic by default (Law 18), MODELLED only when asked for.

`{on: <cylindrical face>, spec: "M6" | "M6x0.75", length: <len>, from: min |
max, hand: right | left, modelled: false}`; an omitted `length` is the whole
face and says so in `assumed`.

**Cosmetic is the default and stays cosmetic.** A cosmetic thread records the
designation, the ISO 261 pitch and the ISO 68-1 diameters on the feature,
changes NO geometry, and leaves the part's fingerprint bit-identical - Law 18,
and the same contract `hole {thread: "M6"}` has always had. `modelled: true`
is a separate, declared choice that cuts and adds real helical material, and
the diff says which one you got.

## How a modelled thread is built, and why not the obvious way

The obvious way - sweep the V-groove along a helix and cut it out of the
shaft - is BROKEN on this OCCT (OCP 7.9.3, macOS, measured 2026-09-04):
`BRepAlgoAPI_Cut` of a 14-turn helical groove from a d6 x 12 cylinder
answered `IsDone() == True` with 311.02 mm3 where the arithmetic says 275.49;
the same cut on a 5-turn groove returned an EMPTY shape (0 solids, 0 faces)
still reporting `IsDone() == True`; splitting the groove into one tool per
turn took 458 SECONDS and returned volume -0.0. Those are silent wrong
answers, which is the one outcome this lane refuses to ship.

What does work is the sequence a machinist uses, and every step of it is a
boolean between well-separated transversal surfaces:

1. **turn down / bore out** to the thread's own core with a plain cylindrical
   tool (external: cut a tube down to the minor diameter d1; internal: bore
   the hole out to the major diameter D);
2. **sweep the thread's MATERIAL** - the ISO 68-1 basic profile, 3P/4 wide at
   the minor and P/8 at the major for an external thread, the complement for
   an internal one - along the helix, its inner corner buried `eps` below the
   core surface so the two surfaces meet transversally rather than tangentially;
3. **trim** that ridge to the thread's axial span with one cylinder, and
4. **fuse** it onto the core.

Measured for the acceptance case, M6x1 modelled over 12 mm on a d6 shaft:
275.510 mm3 against the arithmetic 275.486 mm3 (relative +8.6e-5, the
partial threads at the two ends), a VALID single solid, minor diameter
4.917 468 mm against ISO 68-1's d1 = d - 1.082 5 P = 4.917 468 mm, 22 unique
faces (a helicoid is ONE face however many turns it makes, so a modelled
thread does not multiply face counts) - and **0.64 s of wall time**, against
the 13-17 ms every other feature in this kernel costs. The cost is the two
booleans and it scales with the turns: on a d6 shaft 6 mm takes 0.48 s,
12 mm 0.64 s and 24 mm 1.23 s (79, 54 and 51 ms per turn). The cosmetic
thread beside it costs 0.5 ms. `MAX_TURNS` refuses beyond 200 turns (about
11 s at 55 ms a turn) and names `job: true` as the fix.

Because the answer is expensive AND was silently wrong by another route,
every modelled thread is verified before it is returned: valid solid, exactly
one solid, and the measured root diameter within `DIA_TOL_MM` of the ISO
value. A build that fails any of those refuses `pk_op_failed` with the
numbers rather than handing back a plausible-looking part.

Roles: `<name>.root[k]` (the minor cylinder an external thread runs in),
`<name>.crest[k]`, `<name>.flank[k]`. OCP is imported inside functions only.
"""

from __future__ import annotations

import math
from typing import Any

from partkiln.document import CommandError
from partkiln.features.base import Outcome, builder, name_from_tool, one, r3
from partkiln.features.coil import helix_wire

Vec3 = tuple[float, float, float]

# ISO 68-1: the fundamental triangle is H = P * sqrt(3)/2; the basic profile
# truncates it H/8 at the external crest and H/4 at the external root, so the
# external minor is d - 2*(5/8)H = d - 1.0825*P.
_H_OVER_P = math.sqrt(3.0) / 2.0
_MINOR_FACTOR = 1.25 * _H_OVER_P  # 1.082 532...; d1 = d - _MINOR_FACTOR * P

# How far the swept ridge is buried below the core surface. It must be small
# enough that consecutive turns stay well apart (the widest external section
# is 3P/4 at the minor, so the turn-to-turn gap is P/4 - 2*eps*tan(30)) and
# large enough that the ridge crosses the core transversally. Measured: 0.02P,
# 0.05P and 0.1P all give the arithmetic to 1e-4 relative.
_EPS_FRAC = 0.05
_FLANK_HALF_ANGLE = math.radians(30.0)

MAX_TURNS = 200.0
DIA_TOL_MM = 1e-3


def _iso(spec: str) -> dict[str, Any]:
    """ISO 261 pitch + ISO 68-1 basic diameters for 'M6' or 'M6x0.75'."""
    from partkiln import standards

    row = standards.pitch(spec)
    pitch = float(row["pitch_mm"])
    nominal = float(row["nominal_mm"])
    return {
        "designation": str(row["designation"]),
        "nominal_mm": nominal,
        "pitch_mm": pitch,
        "major_dia_mm": nominal,
        "minor_dia_mm": nominal - _MINOR_FACTOR * pitch,
        "source": row.get("source", ""),
        "authority": row.get("authority", ""),
        "licence": row.get("licence", ""),
    }


def _cyl_axis(face: Any) -> tuple[Vec3, Vec3, float, float, float]:
    """(axis point, unit direction, radius, v_min, v_max) of a cylindrical face.

    A cylinder's v parameter IS the distance along its own axis from the
    surface's location, so the face's v range is its axial span - no bounding
    box, which would be wrong for a face that is not axis-aligned in world.
    """
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    surface = BRepAdaptor_Surface(face)
    cyl = surface.Cylinder()
    axis = cyl.Axis()
    loc, direction = axis.Location(), axis.Direction()
    return (
        (loc.X(), loc.Y(), loc.Z()),
        (direction.X(), direction.Y(), direction.Z()),
        cyl.Radius(),
        surface.FirstVParameter(),
        surface.LastVParameter(),
    )


def _profile_wire(points: list[tuple[float, float]], origin: Vec3, direction: Vec3, xdir: Vec3):
    """A closed polygon in the AXIAL plane: (radius, axial offset) per point."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon
    from OCP.gp import gp_Pnt

    poly = BRepBuilderAPI_MakePolygon()
    for radius, axial in points:
        poly.Add(gp_Pnt(*[origin[i] + radius * xdir[i] + axial * direction[i] for i in range(3)]))
    poly.Close()
    return poly.Wire()


def _perpendicular(direction: Vec3) -> Vec3:
    other = (1.0, 0.0, 0.0) if abs(direction[0]) < 0.9 else (0.0, 1.0, 0.0)
    cross = (
        direction[1] * other[2] - direction[2] * other[1],
        direction[2] * other[0] - direction[0] * other[2],
        direction[0] * other[1] - direction[1] * other[0],
    )
    norm = math.sqrt(sum(c * c for c in cross))
    return (cross[0] / norm, cross[1] / norm, cross[2] / norm)


def _face_radius(face: Any, point: Vec3, direction: Vec3) -> float:
    """The radius of a POINT on the face, sampled at its parametric middle.

    Not the centroid: a helicoid wraps the axis, so the centroid of the crest
    band - every point of which is at the major radius - sits on the axis and
    would read as radius 0.
    """
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    surface = BRepAdaptor_Surface(face)
    p = surface.Value(
        0.5 * (surface.FirstUParameter() + surface.LastUParameter()),
        0.5 * (surface.FirstVParameter() + surface.LastVParameter()),
    )
    delta = (p.X() - point[0], p.Y() - point[1], p.Z() - point[2])
    axial = sum(delta[i] * direction[i] for i in range(3))
    return math.sqrt(sum((delta[i] - axial * direction[i]) ** 2 for i in range(3)))


def _coaxial_radii(shape: Any, point: Vec3, direction: Vec3, lo: float, hi: float) -> list[float]:
    """Radii of the cylindrical faces coaxial with the thread, inside its span."""
    from partkiln.brep import query

    out: list[float] = []
    for info in query.faces(shape):
        if info.surface_type != "cylinder" or info.radius is None:
            continue
        centre = info.centroid
        delta = tuple(centre[i] - point[i] for i in range(3))
        axial = sum(delta[i] * direction[i] for i in range(3))
        if lo - 1e-6 <= axial <= hi + 1e-6:
            out.append(float(info.radius))
    return sorted(out)


def _boolean(kind: str, base: Any, tools: list[Any], feature: Any, what: str) -> tuple[Any, Any]:
    """One boolean with Law 11 answered, WITHOUT `UnifySameDomain`.

    `features.base.boolean` unifies every result; on a helical body that is a
    real risk (measured: unify on the BROKEN groove-cut result collapsed it to
    4 faces and the volume of the uncut shaft), so the thread does its own
    booleans and unifies nothing. Face counts here are therefore raw.
    """
    from partkiln.brep import history, shapes

    res = shapes.cut(base, tools) if kind == "cut" else shapes.fuse([base, *tools])
    if not res.is_done:
        raise CommandError(
            f"thread {feature.id}: the {what} did not complete in OCCT.",
            code="pk_op_failed",
        )
    if res.empty:
        raise CommandError(f"thread {feature.id}: the {what} left no solid.", code="pk_no_effect")
    if res.no_effect:
        raise CommandError(
            f"thread {feature.id}: the {what} changed nothing - the body still has "
            f"{res.counts_after['faces']} faces and {r3(res.volume_after)} mm3 (Law 11). "
            "Check that the face named by `on` is the one to be threaded.",
            code="pk_no_effect",
        )
    return res.shape, history.from_algo(res.history)


def _ridge_points(
    internal: bool, pitch: float, r_minor: float, r_major: float, eps: float
) -> list[tuple[float, float]]:
    """The ISO 68-1 basic thread MATERIAL as (radius, axial offset) corners.

    External: 3P/4 wide at the minor, P/8 at the major (the groove between two
    crests is the complement: P/4 at the root, 7P/8 at the crest). Internal is
    that complement - P/4 wide at the minor crest, 7P/8 at the major root -
    and grows OUTWARD, so its buried corner is `eps` beyond the major.
    """
    over = eps * math.tan(_FLANK_HALF_ANGLE)
    if internal:
        r_in, w_in = r_major + eps, 7.0 * pitch / 16.0 + over
        r_tip, w_tip = r_minor, pitch / 8.0
    else:
        r_in, w_in = r_minor - eps, 3.0 * pitch / 8.0 + over
        r_tip, w_tip = r_major, pitch / 16.0
    return [(r_in, -w_in), (r_tip, -w_tip), (r_tip, w_tip), (r_in, w_in)]


@builder("thread")
def build_thread(doc: Any, part: Any, feature: Any, assumed: dict[str, Any]) -> Outcome:
    args = feature.args
    if part.shape is None:
        raise CommandError(
            f"thread {feature.id}: part {part.name} has no body to thread.", code="pk_needs"
        )
    if not args.get("spec"):
        raise CommandError(
            f"thread {feature.id} needs spec: 'M6' (the ISO 261 coarse pitch) or 'M6x0.75'.",
            code="pk_needs",
        )
    iso = _iso(str(args["spec"]))
    pitch = iso["pitch_mm"]
    res = one(part, feature, args.get("on"), "face", "on: <cylindrical face ref>")
    face = res.infos[0]
    if face.surface_type != "cylinder":
        raise CommandError(
            f"thread {feature.id}: {args.get('on')} is a {face.surface_type} face; a thread "
            "needs a cylindrical face (a shaft's wall, or a hole's wall).",
            code="pk_plane_mismatch",
        )
    point, direction, r_face, v_lo, v_hi = _cyl_axis(face.shape)
    span = v_hi - v_lo
    from partkiln.brep import shapes

    internal = shapes.is_concave_cylinder(face.shape)
    deps = feature.param_deps

    # Omitted `length` means the whole face - a default, not a keyword: a
    # magic string here would trip the same lint wart `depth: "through"` has.
    if "length" in args:
        length = doc.length(args["length"], assumed, deps)
    else:
        length = span
        assumed["length"] = f"{r3(span)}mm, the face's own length"
    if length <= 0:
        raise CommandError(
            f"thread {feature.id}: length must be > 0, got {r3(length)} mm.",
            code="pk_needs",
        )
    if length > span + 1e-6:
        raise CommandError(
            f"thread {feature.id}: length {r3(length)} mm is longer than the face "
            f"{args.get('on')}, which is {r3(span)} mm long. Shorten it, or thread a longer "
            "face.",
            code="pk_spec_conflict",
        )
    start = str(args.get("from", "min")).lower()
    if start not in ("min", "max"):
        raise CommandError(
            f"thread {feature.id}: from is 'min' or 'max' (which end of the face the thread "
            f"starts at), not {args.get('from')!r}.",
            code="pk_needs",
        )
    if "from" not in args and length < span - 1e-6:
        assumed["from"] = "min"
    v0 = v_lo if start == "min" else v_hi - length
    v1 = v0 + length

    hand = str(args.get("hand", "right")).lower()
    if hand not in ("right", "left"):
        raise CommandError(
            f"thread {feature.id}: hand is 'right' or 'left', not {args.get('hand')!r}.",
            code="pk_needs",
        )
    if "hand" not in args:
        assumed["hand"] = "right"
    modelled = bool(args.get("modelled", False))
    if "modelled" not in args:
        assumed["modelled"] = False

    r_major, r_minor = iso["major_dia_mm"] / 2.0, iso["minor_dia_mm"] / 2.0
    # The face may already be at the thread's major OR at its minor (a shaft
    # left at size, or one already turned down; a hole bored to major, or one
    # drilled at the tap drill). Anything further off than half a pitch is a
    # spec that contradicts the geometry, and Law 19 says ask only then.
    if abs(r_face - r_major) > 0.5 * pitch and abs(r_face - r_minor) > 0.5 * pitch:
        kind = "hole" if internal else "shaft"
        raise CommandError(
            f"thread {feature.id}: {iso['designation']} runs between "
            f"{r3(iso['minor_dia_mm'])} mm and {r3(iso['major_dia_mm'])} mm, but the {kind} "
            f"{args.get('on')} is {r3(2 * r_face)} mm across. Size the {kind} to the major "
            f"({r3(iso['major_dia_mm'])} mm) or the minor ({r3(iso['minor_dia_mm'])} mm) "
            "diameter first, or name the thread that fits it.",
            code="pk_spec_conflict",
        )

    notes: list[str] = []
    extra: dict[str, Any] = {
        "spec": iso["designation"],
        "pitch_mm": r3(pitch),
        "turns": r3(length / pitch),
        "length_mm": r3(length),
        "hand": hand,
        "internal": internal,
        "modelled": modelled,
        "iso_major_dia_mm": r3(iso["major_dia_mm"]),
        "iso_minor_dia_mm": r3(iso["minor_dia_mm"]),
    }
    if iso["authority"]:
        notes.append(
            f"{iso['designation']} pitch {pitch:g} mm per {iso['authority']} "
            f"({iso['licence']}); the profile is ISO 68-1 basic"
        )

    if not modelled:
        notes.append(
            f"thread {iso['designation']} is cosmetic: no geometry changed (Law 18). "
            "Pass modelled: true for real helical geometry."
        )
        return Outcome(
            part.shape,
            None,
            [],
            [],
            [],
            "",
            notes=notes,
            cosmetic={
                "thread": iso["designation"],
                "pitch_mm": r3(pitch),
                "hand": hand,
                "internal": internal,
            },
            extra=extra,
        )

    turns = length / pitch
    if turns > MAX_TURNS:
        raise CommandError(
            f"thread {feature.id}: {r3(turns)} turns of {iso['designation']} would take about "
            f"{r3(turns * 0.055)} s of solid modelling (measured: 51-79 ms per turn on this "
            f"machine). The cap is {MAX_TURNS:g} turns. Shorten `length`, use a coarser "
            "pitch, or run the batch with job: true.",
            code="pk_too_long",
        )
    return _model(
        doc,
        part,
        feature,
        args,
        iso,
        notes,
        extra,
        internal,
        hand,
        point,
        direction,
        r_face,
        v0,
        v1,
        turns,
    )


def _model(
    doc: Any,
    part: Any,
    feature: Any,
    args: dict[str, Any],
    iso: dict[str, Any],
    notes: list[str],
    extra: dict[str, Any],
    internal: bool,
    hand: str,
    point: Vec3,
    direction: Vec3,
    r_face: float,
    v0: float,
    v1: float,
    turns: float,
) -> Outcome:
    """Turn down / bore out, sweep the ridge, trim it, fuse it, then VERIFY."""
    from partkiln.brep import query, shapes

    pitch = iso["pitch_mm"]
    r_major, r_minor = iso["major_dia_mm"] / 2.0, iso["minor_dia_mm"] / 2.0
    eps = _EPS_FRAC * pitch
    length = v1 - v0
    base_at = tuple(point[i] + v0 * direction[i] for i in range(3))
    xdir = _perpendicular(direction)
    core_r = r_major if internal else r_minor

    body = part.shape
    histories: list[Any] = []
    tools: list[Any] = []
    # 1. the core the thread is cut into: a plain cylindrical tool, no helix.
    if abs(r_face - core_r) > 1e-6:
        if internal:
            tool = shapes.cylinder(core_r, length, base_at, direction)
        else:
            outer = shapes.cylinder(r_face + 1.0, length, base_at, direction)
            inner = shapes.cylinder(core_r, length, base_at, direction)
            tool = shapes.cut(outer, [inner]).shape
        tools.append(tool)
        body, hist = _boolean(
            "cut",
            body,
            [tool],
            feature,
            "bore out to the major" if internal else "turn down to the minor",
        )
        histories.append(hist)

    # 2. the thread's own material, swept along the helix and trimmed to the span.
    spine = helix_wire(
        r_major,
        pitch,
        turns + 2.0,
        tuple(base_at[i] - pitch * direction[i] for i in range(3)),
        direction,
        xdir,
        hand,
    )
    from partkiln.features.coil import _pipe  # the shared MakePipeShell wrapper

    profile = _profile_wire(
        _ridge_points(internal, pitch, r_minor, r_major, eps),
        tuple(base_at[i] - pitch * direction[i] for i in range(3)),
        direction,
        xdir,
    )
    ridge = _pipe(spine, profile, False).Shape()
    envelope = shapes.cylinder(max(r_face, r_major) + eps + 0.5, length, base_at, direction)
    trimmed = shapes.common(ridge, envelope)
    if trimmed.empty:
        raise CommandError(
            f"thread {feature.id}: the swept thread does not meet the face {args.get('on')} "
            f"over {r3(length)} mm from its {args.get('from', 'min')} end.",
            code="pk_no_effect",
        )
    ridge = trimmed.shape
    tools.append(ridge)

    # Roles are pre-indexed (`flank[0]`, `flank[1]`, ...): several DISTINCT tool
    # faces share a role here, and `name_from_tool` only disambiguates one tool
    # face that fanned out - without the index every flank would be `<n>.flank`.
    ridge_roles: list[tuple[str, Any]] = []
    seen: dict[str, int] = {}
    tip = r_minor if internal else r_major
    for info in query.faces(ridge):
        if info.surface_type == "plane":
            continue  # the trim's flat ends
        radial = _face_radius(info.shape, point, direction)
        role = "crest" if abs(radial - tip) < 0.05 * pitch else "flank"
        index = seen.get(role, 0)
        seen[role] = index + 1
        ridge_roles.append((f"{role}[{index}]", info.shape))

    # 3. fuse the ridge onto the core.
    shape, hist = _boolean("fuse", body, [ridge], feature, "thread fuse")
    histories.append(hist)
    merged = histories[0]
    for other in histories[1:]:
        merged.merge(other)

    names = name_from_tool(hist, shape, feature.id, ridge_roles)
    root_r = core_r if not internal else r_major
    for k, info in enumerate(
        f
        for f in query.faces(shape)
        if f.surface_type == "cylinder"
        and f.radius is not None
        and abs(f.radius - root_r) < DIA_TOL_MM
    ):
        names.append((f"{feature.id}.root[{k}]", "root", info.shape))

    # 4. verify - an expensive answer that was silently wrong by another route
    #    is checked before it is handed back.
    # Only the faces the thread itself owns: the part may be a nut with a
    # 14 mm outside diameter, and its outer wall is coaxial too.
    radii = [r for r in _coaxial_radii(shape, point, direction, v0, v1) if r <= r_major + 1e-6]
    measured = (max(radii) if internal else min(radii)) if radii else 0.0
    counts = shapes.counts(shape)
    want = r_major if internal else r_minor
    if counts["solids"] != 1 or not shapes.is_valid(shape) or abs(measured - want) > DIA_TOL_MM:
        raise CommandError(
            f"thread {feature.id}: OCCT built a body this kernel will not vouch for - "
            f"{counts['solids']} solid(s), valid={shapes.is_valid(shape)}, "
            f"{'major' if internal else 'minor'} diameter {r3(2 * measured)} mm against "
            f"ISO {r3(2 * want)} mm. The modelled thread is refused rather than returned "
            "wrong; use the cosmetic thread (drop modelled: true) or thread a plain "
            "cylindrical face.",
            code="pk_op_failed",
        )
    extra["measured_minor_dia_mm" if not internal else "measured_major_dia_mm"] = r3(2 * measured)
    extra["faces"] = counts["faces"]
    notes.append(
        f"modelled thread: {r3(turns)} turns swept and fused (Law 18's cosmetic default was "
        "overridden by modelled: true)"
    )
    # `cosmetic` stays EMPTY here on purpose: it is the field that means "an
    # annotation that moved no volume" (checks/spec.py leans on it), and this
    # thread moved 63.8 mm3.
    return Outcome(shape, merged, names, tools, ridge_roles, "fuse", notes=notes, extra=extra)


__all__ = ["DIA_TOL_MM", "MAX_TURNS", "build_thread"]
