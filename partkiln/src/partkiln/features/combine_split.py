"""Combine (boolean between parts) and split (a body by a plane or a face).

`combine {bodies: [<part>, ...], mode join | cut | intersect, keep_tool}`
lands in the first body (or `part`); the other parts are the tools, taken
as they stand NOW, so the feature depends on them (`dependents_of("part:x")`
names it, and an edit to a tool part regenerates it). `keep_tool: false`
(the declared default) marks the tool parts `consumed_by` the target - they
stay in the document as the script that made them, which is what a regen
needs; nothing is deleted behind the model's back. Tool faces keep their
own names under `<name>.<i>.<face name>`.

`split {body, plane | face, keep both | + | -}`: `BRepAlgoAPI_Splitter`
(it has a `History()`), the pieces sorted by which side of the plane's
normal their centroid lies; `keep: both` leaves a two-solid body (`solids:
2` in the diff). The new planar faces are `<name>.cap[k]`. OCP is imported
inside functions only.
"""

from __future__ import annotations

from typing import Any

from partkiln.document import CommandError
from partkiln.features.base import Outcome, boolean, builder, follow, name_from_tool, refs_of
from partkiln.features.workplane import plane_of

_MODES = ("join", "cut", "intersect")


def _part_named(doc: Any, raw: Any) -> Any:
    name = str(raw)[5:] if str(raw).startswith("part:") else str(raw)
    part = doc.parts.get(name)
    if part is None:
        known = ", ".join(f"part:{n}" for n in sorted(doc.parts)) or "(none)"
        raise CommandError(f"no part {raw!r}. Parts: {known}.", code="pk_ref_unknown")
    return part


@builder("combine")
def build_combine(doc: Any, part: Any, feature: Any, assumed: dict[str, Any]) -> Outcome:
    args = feature.args
    bodies = args.get("bodies")
    if not isinstance(bodies, list | tuple) or len(bodies) < 2:
        raise CommandError(
            f"combine {feature.id} needs bodies: [<part>, <part>, ...] (the first is the target "
            "unless part: is given) and mode: join | cut | intersect.",
            code="pk_needs",
        )
    mode = str(args.get("mode", "")).lower()
    if mode not in _MODES:
        raise CommandError(
            f"combine {feature.id}: mode is one of {', '.join(_MODES)}.", code="pk_needs"
        )
    keep_tool = bool(args.get("keep_tool", False))
    if "keep_tool" not in args:
        assumed["keep_tool"] = False
    if part.shape is None:
        raise CommandError(
            f"combine {feature.id}: target part {part.name} has no body.", code="pk_needs"
        )
    tool_parts = [_part_named(doc, b) for b in bodies if _part_named(doc, b) is not part]
    if not tool_parts:
        raise CommandError(
            f"combine {feature.id}: bodies must name at least one OTHER part.", code="pk_needs"
        )
    tools: list[Any] = []
    tool_roles: list[tuple[str, Any]] = []
    for i, tp in enumerate(tool_parts, start=1):
        if tp.shape is None:
            raise CommandError(
                f"combine {feature.id}: part {tp.name} has no body.", code="pk_needs"
            )
        feature.depends.add(f"part:{tp.name}")
        refs_of(feature, f"part:{tp.name}")
        tools.append(tp.shape)
        inv = tp.inventory()
        tool_roles.extend((f"{i}.{inv.name_of_face(k)}", f.shape) for k, f in enumerate(inv.faces))
    shape, hist = boolean(part.shape, tools, mode, feature, bool(args.get("allow_no_effect")))
    names = name_from_tool(hist, shape, feature.id, tool_roles)
    for tp in tool_parts:
        tp.consumed_by = None if keep_tool else part.name
    return Outcome(
        shape,
        hist,
        names,
        tools,
        [],
        mode,
        extra={"bodies": [tp.name for tp in tool_parts], "keep_tool": keep_tool},
    )


@builder("split")
def build_split(doc: Any, part: Any, feature: Any, assumed: dict[str, Any]) -> Outcome:
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
    from OCP.gp import gp_Dir, gp_Pln, gp_Pnt

    from partkiln.brep import history, query, shapes

    args = feature.args
    if part.shape is None:
        raise CommandError(f"split {feature.id}: part {part.name} has no body.", code="pk_needs")
    ref = args.get("plane", args.get("face"))
    if ref is None:
        raise CommandError(
            f"split {feature.id} needs plane: XY | XZ | YZ | plane:<n> | x=80 or face: <face ref>, "
            "and keep: both | + | -.",
            code="pk_needs",
        )
    keep = str(args.get("keep", "both"))
    if "keep" not in args:
        assumed["keep"] = "both"
    if keep not in ("both", "+", "-"):
        raise CommandError(f"split {feature.id}: keep is both, + or -.", code="pk_needs")
    point, normal = plane_of(doc, ref, part, feature)
    if isinstance(ref, str):
        refs_of(feature, ref)
    tool = BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(*point), gp_Dir(*normal))).Face()
    result, raw_history = _split(part.shape, tool)
    hm = history.from_algo(raw_history)
    solids = shapes.unique_subshapes(result, _solid_enum())
    if len(solids) < 2:
        raise CommandError(
            f"split {feature.id}: the plane does not cut part {part.name} (still {len(solids)} "
            "solid). Move the plane through the body (Law 11).",
            code="pk_no_effect",
        )
    if keep != "both":
        wanted = 1.0 if keep == "+" else -1.0
        kept = [
            s
            for s in solids
            if wanted
            * sum(
                (c - p) * n for c, p, n in zip(shapes.centre_of_mass(s), point, normal, strict=True)
            )
            > 0
        ]
        if not kept:
            raise CommandError(
                f"split {feature.id}: no solid lies on the {keep} side.", code="pk_no_effect"
            )
        shape = kept[0] if len(kept) == 1 else _compound(kept)
    else:
        shape = result
    names: list[tuple[str, str, Any]] = []
    # Measured (OCP 7.9.3): the splitter's History lists the section faces as
    # MODIFIED images of the tool face (Generated holds only its edges/vertices).
    caps = [
        g
        for g in [*hm.modified(tool), *hm.generated(tool)]
        if g.ShapeType().name == "TopAbs_FACE" and follow(None, shape, g)
    ]
    caps.sort(key=lambda g: tuple(round(c, 3) for c in query.faces(g)[0].centroid))
    for k, g in enumerate(caps):
        names.append((f"{feature.id}.cap[{k}]", f"cap[{k}]", g))
    return Outcome(shape, hm, names, extra={"keep": keep, "pieces": len(solids)})


def _split(shape: Any, tool: Any) -> tuple[Any, Any]:
    """`BRepAlgoAPI_Splitter` (arguments = the body, tools = the face): (shape, History())."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Splitter
    from OCP.TopTools import TopTools_ListOfShape

    algo = BRepAlgoAPI_Splitter()
    arguments, tools = TopTools_ListOfShape(), TopTools_ListOfShape()
    arguments.Append(shape)
    tools.Append(tool)
    algo.SetArguments(arguments)
    algo.SetTools(tools)
    algo.SetRunParallel(True)
    algo.Build()
    if not algo.IsDone():
        raise CommandError("the split did not complete in OCCT.", code="pk_op_failed")
    return algo.Shape(), algo.History()


def _solid_enum() -> Any:
    from OCP.TopAbs import TopAbs_SOLID

    return TopAbs_SOLID


def _compound(solids: list[Any]) -> Any:
    from OCP.BRep import BRep_Builder
    from OCP.TopoDS import TopoDS_Compound

    builder = BRep_Builder()
    compound = TopoDS_Compound()
    builder.MakeCompound(compound)
    for s in solids:
        builder.Add(compound, s)
    return compound


__all__ = ["build_combine", "build_split"]
