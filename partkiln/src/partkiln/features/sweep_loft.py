"""Sweep (a profile along a path) and loft (through sections), each then one boolean.

`sweep {profile: <closed sketch>, path: <open sketch>, frenet, mode}`: the
path is an open chain of lines/arcs in ITS sketch frame (profile.py's
`build_path`), the profile a closed sketch in its own; OCCT's corrected-
Frenet trihedron (`frenet: false`, the default) does not twist on planar
paths - measured: a r3 circle along 50 mm is 1 413.717 mm3.
`loft {sections: [<sketch>, ...], ruled, mode}`: the outer wire of every
section in its own frame (offset datum planes give the spacing);
`ThruSections` with compatibility checks; measured: 40x40 to 20x20 over 30
mm ruled is 28 000 mm3.

Roles: `<name>.side.<tag>` for the face each profile / first-section segment
generated, `<name>.cap.a` / `.cap.b` for the two ends. OCP is imported
inside functions only.
"""

from __future__ import annotations

from typing import Any

from partkiln.document import CommandError
from partkiln.features.base import Outcome, boolean, builder, name_from_tool, parse_mode
from partkiln.features.extrude import side_roles
from partkiln.features.workplane import frame_for
from partkiln.sketch.profile import build_path, build_profile


def _finish(
    doc: Any,
    part: Any,
    feature: Any,
    args: dict[str, Any],
    mode: str,
    tool: Any,
    tool_roles: list[tuple[str, Any]],
    frame: Any,
    extra: dict[str, Any],
) -> Outcome:
    if mode == "new":
        shape, hist = tool, None
    else:
        shape, hist = boolean(part.shape, [tool], mode, feature, bool(args.get("allow_no_effect")))
    names = name_from_tool(hist, shape, feature.id, tool_roles)
    return Outcome(shape, hist, names, [tool], tool_roles, mode, frame=frame, extra=extra)


@builder("sweep")
def build_sweep(doc: Any, part: Any, feature: Any, assumed: dict[str, Any]) -> Outcome:
    from partkiln.brep import shapes

    args = feature.args
    if not args.get("profile") or not args.get("path"):
        raise CommandError(
            f"sweep {feature.id} needs profile: <closed sketch> and path: <open sketch>.",
            code="pk_needs",
        )
    profile_sk = doc.sketch(args["profile"])
    path_sk = doc.sketch(args["path"])
    feature.depends.update({f"sk:{profile_sk.name}", f"sk:{path_sk.name}"})
    feature.refs.extend([f"sk:{profile_sk.name}", f"sk:{path_sk.name}"])
    mode = parse_mode(args, part, assumed)
    frenet = bool(args.get("frenet", False))
    if "frenet" not in args:
        assumed["frenet"] = False
    frame = frame_for(doc, profile_sk.plane, part, feature)
    profile = build_profile(profile_sk, frame)
    if len(profile.faces) != 1:
        raise CommandError(
            f"sweep {feature.id}: the profile must be one closed loop; {profile_sk.name} has "
            f"{len(profile.faces)}.",
            code="pk_needs",
        )
    path = build_path(path_sk, frame_for(doc, path_sk.plane, part, feature))
    res = shapes.sweep(profile.faces[0], path, frenet=frenet)
    tool_roles = side_roles(res.algo, profile)
    tool_roles.append(("cap.a", res.algo.FirstShape()))
    tool_roles.append(("cap.b", res.algo.LastShape()))
    return _finish(
        doc, part, feature, args, mode, res.shape, tool_roles, frame, {"area_mm2": profile.area_mm2}
    )


@builder("loft")
def build_loft(doc: Any, part: Any, feature: Any, assumed: dict[str, Any]) -> Outcome:
    from OCP.BRepTools import BRepTools

    from partkiln.brep import shapes

    args = feature.args
    sections = args.get("sections")
    if not isinstance(sections, list | tuple) or len(sections) < 2:
        raise CommandError(
            f"loft {feature.id} needs sections: [<sketch>, <sketch>, ...] (at least two).",
            code="pk_needs",
        )
    mode = parse_mode(args, part, assumed)
    ruled = bool(args.get("ruled", False))
    if "ruled" not in args:
        assumed["ruled"] = False
    wires = []
    first_profile = None
    first_frame = None
    for name in sections:
        sk = doc.sketch(name)
        feature.depends.add(f"sk:{sk.name}")
        feature.refs.append(f"sk:{sk.name}")
        frame = frame_for(doc, sk.plane, part, feature)
        profile = build_profile(sk, frame)
        if len(profile.faces) != 1:
            raise CommandError(
                f"loft {feature.id}: section {sk.name} must be one closed loop, it has "
                f"{len(profile.faces)}.",
                code="pk_needs",
            )
        wires.append(BRepTools.OuterWire_s(profile.faces[0]))
        if first_profile is None:
            first_profile, first_frame = profile, frame
    res = shapes.loft(wires, ruled=ruled)
    assert first_profile is not None
    tool_roles: list[tuple[str, Any]] = []
    for tag, edge in first_profile.edges:
        try:
            face = res.algo.GeneratedFace(edge)
        except Exception:
            continue
        if face is not None and not face.IsNull():
            tool_roles.append((f"side.{tag}", face))
    tool_roles.append(("cap.a", res.algo.FirstShape()))
    tool_roles.append(("cap.b", res.algo.LastShape()))
    return _finish(
        doc,
        part,
        feature,
        args,
        mode,
        res.shape,
        tool_roles,
        first_frame,
        {"sections": len(wires), "ruled": ruled},
    )


__all__ = ["build_loft", "build_sweep"]
