"""Shell (hollow a body, opening named faces) and draft (tilt named faces).

`shell {faces, t, direction in | out}`: `MakeThickSolidByJoin` keeps the
outer skin for `in` (a 40x40x20 box opened at the top with t = 2 leaves
32 000 - 36*36*18 = 8 672 mm3, 11 faces - measured) and grows outward for
`out`. Every kept face generates its offset twin (`Generated(face)`,
measured), named `<name>.inner[i]` in the order of the input faces; the
opened faces become rims and keep their names through `Modified`.

`draft {faces, angle, neutral, pull}`: `BRepOffsetAPI_DraftAngle` about
the neutral plane; a face that is not a plane, cylinder or cone is refused
BY TYPE before OCCT is asked ("it is a sphere"), because `Add` on a torus
does nothing and says nothing (brep/shapes.py). `pull` defaults to the
neutral plane's normal and is declared. OCP is imported inside functions
only.
"""

from __future__ import annotations

from typing import Any

from partkiln.document import CommandError
from partkiln.features.base import Outcome, builder, many
from partkiln.features.workplane import direction_of, plane_of


@builder("shell")
def build_shell(doc: Any, part: Any, feature: Any, assumed: dict[str, Any]) -> Outcome:
    from partkiln.brep import history, query, shapes

    args = feature.args
    if part.shape is None:
        raise CommandError(f"shell {feature.id}: part {part.name} has no body.", code="pk_needs")
    if args.get("t") is None:
        raise CommandError(
            f"shell {feature.id} needs t (the wall thickness) and faces (to open).", code="pk_needs"
        )
    res = many(part, feature, args.get("faces"), "face", "faces (the ones to open)")
    t = doc.length(args["t"], assumed, feature.param_deps)
    direction = str(args.get("direction", "in"))
    if "direction" not in args:
        assumed["direction"] = "in"
    result = shapes.shell(part.shape, [f.shape for f in res.infos], t, direction)
    hm = history.record(result.algo, result.inputs)
    names: list[tuple[str, str, Any]] = []
    k = 0
    for f in query.faces(part.shape):
        generated = [g for g in hm.generated(f.shape) if g.ShapeType().name == "TopAbs_FACE"]
        for g in generated:
            names.append((f"{feature.id}.inner[{k}]", f"inner[{k}]", g))
            k += 1
    return Outcome(
        result.shape,
        hm,
        names,
        extra={"t_mm": round(t, 3), "direction": direction, "opened": res.count},
    )


@builder("draft")
def build_draft(doc: Any, part: Any, feature: Any, assumed: dict[str, Any]) -> Outcome:
    from partkiln.brep import history, shapes

    args = feature.args
    if part.shape is None:
        raise CommandError(f"draft {feature.id}: part {part.name} has no body.", code="pk_needs")
    if args.get("angle") is None or args.get("neutral") is None:
        raise CommandError(
            f"draft {feature.id} needs faces, angle and neutral (a plane: XY | plane:<n> | "
            "<face ref> | z=10).",
            code="pk_needs",
        )
    res = many(part, feature, args.get("faces"), "face", "faces")
    for info, name in zip(res.infos, res.names, strict=True):
        if info.surface_type not in ("plane", "cylinder", "cone"):
            raise CommandError(
                f"draft {feature.id} cannot tilt {name}: it is a {info.surface_type}; only plane, "
                "cylinder or cone faces can be drafted. Select the planar side walls instead.",
                code="pk_plane_mismatch",
            )
    angle = doc.angle(args["angle"], assumed, feature.param_deps)
    point, normal = plane_of(doc, args["neutral"], part, feature)
    if isinstance(args["neutral"], str):
        feature.refs.append(str(args["neutral"]))
    if "pull" in args:
        pull = direction_of(doc, args["pull"])
    else:
        pull = normal
        assumed["pull"] = "the neutral plane's normal"
    result = shapes.draft(part.shape, [f.shape for f in res.infos], angle, (point, normal), pull)
    hm = history.record(result.algo, result.inputs)
    return Outcome(
        result.shape,
        hm,
        [],
        extra={"angle_deg": round(angle, 3), "drafted": res.count, "occt_status": result.status},
    )


__all__ = ["build_draft", "build_shell"]
