"""Is this a valid, closed solid? `BRepCheck_Analyzer` plus a closedness test.

`BRepCheck_Analyzer.IsValid()` answers "is every sub-shape well-formed", and
NOTHING about being a solid: measured here (2026-09-02), an OPEN shell of
five box faces is `IsValid() == True`, and `BRepClass3d_SolidClassifier`'s
infinite-point test says `OUT` for it exactly as it does for a solid - so
"closed" cannot come from either. It comes from the ancestor map instead
(`TopExp.MapShapesAndAncestors_s(EDGE -> FACE)`): a closed skin has every
edge shared by two faces (a cylinder seam lists its one face twice, so seams
are not free edges), an open one has free edges with a single ancestor. F1's
15 edges all have two ancestors; the open shell has 4 free edges.

`fix()` is `ShapeFix_Shape` - the repair for imported geometry, never for
our own (a feature that needs fixing is a bug in the feature).
"""

from __future__ import annotations

from typing import Any

_PROBLEM_CAP = 8


def validate(shape: Any) -> dict[str, Any]:
    """{valid, problems, solids, faces, edges, closed, free_edges}.

    `problems` names the first invalid sub-shapes as `"<kind> <k>: <status>"`
    in the deterministic map order (Law 20: unique sub-shapes), capped at 8.
    `closed` is True only for a shape with at least one solid and no free
    edge - the "is it watertight" the spec rule reads.
    """
    from OCP.BRepCheck import BRepCheck_Analyzer
    from OCP.TopAbs import (
        TopAbs_EDGE,
        TopAbs_FACE,
        TopAbs_SHELL,
        TopAbs_SOLID,
        TopAbs_VERTEX,
        TopAbs_WIRE,
    )

    from partkiln.brep import shapes

    analyzer = BRepCheck_Analyzer(shape, True)
    valid = bool(analyzer.IsValid())
    problems: list[str] = []
    if not valid:
        hidden = 0
        for kind, label in (
            (TopAbs_SOLID, "solid"),
            (TopAbs_SHELL, "shell"),
            (TopAbs_FACE, "face"),
            (TopAbs_WIRE, "wire"),
            (TopAbs_EDGE, "edge"),
            (TopAbs_VERTEX, "vertex"),
        ):
            for k, sub in enumerate(shapes.unique_subshapes(shape, kind)):
                result = analyzer.Result(sub)
                if result is None:
                    continue
                bad = sorted(
                    {s.name.removeprefix("BRepCheck_") for s in result.Status()} - {"NoError"}
                )
                if not bad:
                    continue
                if len(problems) < _PROBLEM_CAP:
                    problems.append(f"{label} {k}: {', '.join(bad)}")
                else:
                    hidden += 1
        if hidden:
            problems.append(f"+{hidden} more")
    counts = shapes.counts(shape)
    free = free_edges(shape)
    closed = counts["solids"] >= 1 and free == 0
    if not closed and valid and counts["faces"]:
        problems.append(
            f"not a closed solid: {counts['solids']} solids, {free} free edges"
            if free
            else f"not a closed solid: {counts['solids']} solids"
        )
    return {
        "valid": valid,
        "problems": problems,
        "solids": counts["solids"],
        "faces": counts["faces"],
        "edges": counts["edges"],
        "closed": closed,
        "free_edges": free,
    }


def free_edges(shape: Any) -> int:
    """Edges with a single ancestor face - the boundary of an open skin."""
    from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
    from OCP.TopExp import TopExp
    from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape

    ancestors = TopTools_IndexedDataMapOfShapeListOfShape()
    TopExp.MapShapesAndAncestors_s(shape, TopAbs_EDGE, TopAbs_FACE, ancestors)
    return sum(1 for i in range(1, ancestors.Extent() + 1) if ancestors.FindFromIndex(i).Size() < 2)


def fix(shape: Any) -> tuple[Any, dict[str, Any]]:
    """`ShapeFix_Shape` pass -> (fixed shape, {changed, before, after}).

    `changed` is True when validity, closedness or a unique count moved;
    `before`/`after` are the two `validate` reports so the caller can say
    exactly what the repair did (an edit reports its blast radius, Law 14).
    """
    from OCP.ShapeFix import ShapeFix_Shape

    before = validate(shape)
    fixer = ShapeFix_Shape(shape)
    fixer.Perform()
    fixed = fixer.Shape()
    after = validate(fixed)
    keys = ("valid", "closed", "solids", "faces", "edges", "free_edges")
    changed = any(before[k] != after[k] for k in keys)
    return fixed, {"changed": changed, "before": before, "after": after}


__all__ = ["fix", "free_edges", "validate"]
