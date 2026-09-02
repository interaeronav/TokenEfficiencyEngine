"""Fillet and chamfer: edges by name or selector, a radius or distance by design intent.

`fillet {edges, r | [r1, r2]}` and `chamfer {edges, d | [d1, d2] | {d, angle}}`
REFUSE without `r` / `d` (`pk_needs`): a fillet radius is a design decision
and no default is honest (D5). The edges are resolved by naming.py (seams
excluded by default, `seam_excluded` reported), so `plate:edges(dir=Z)` on
F1 is 4 corners, not the cylinder seam OCCT would silently ignore.

Two failure modes, both surfaced (Law 11): OCCT refuses the whole operation
(fillet r12 on the top-front edge of a 10 mm plate: `NbFaultyContours=1 of
1`, the pinned case) -> the command refuses naming the edge and the count;
or OCCT accepts an edge and generates NOTHING for it (`Generated(edge)`
empty) -> that edge is listed under `failed` while the others land. Every
generated face is named `<name>.face[i]` in the order of the resolved
edges. Measured: r2 on F1's four verticals removes 34.336 mm3 (7 -> 11
faces); d2 on one 100 mm top edge removes 200.000 mm3. OCP is imported
inside functions only.
"""

from __future__ import annotations

import math
from typing import Any

from partkiln._errors import KernelError
from partkiln.document import CommandError
from partkiln.features.base import Outcome, builder, follow, many


def _pair(
    doc: Any, feature: Any, raw: Any, assumed: dict[str, Any], what: str
) -> float | tuple[float, float]:
    deps = feature.param_deps
    if isinstance(raw, list | tuple):
        if len(raw) != 2:
            raise CommandError(
                f"{feature.kind} {feature.id}: {what} as a pair is [a, b].", code="pk_needs"
            )
        a, b = doc.length(raw[0], assumed, deps), doc.length(raw[1], assumed, deps)
        if a <= 0 or b <= 0:
            raise CommandError(f"{feature.kind} {feature.id}: {what} must be > 0.", code="pk_needs")
        return (a, b)
    value = doc.length(raw, assumed, deps)
    if value <= 0:
        raise CommandError(
            f"{feature.kind} {feature.id}: {what} must be > 0, got {value:g} mm.", code="pk_needs"
        )
    return value


def _edge_faces(
    hm: Any, shape: Any, res: Any, feature: Any, ignored: tuple[int, ...]
) -> tuple[list[tuple[str, str, Any]], list[str]]:
    names: list[tuple[str, str, Any]] = []
    failed: list[str] = []
    for i, edge in enumerate(res.infos):
        if i in ignored:
            failed.append(res.names[i])
            continue
        generated = [g for g in hm.generated(edge.shape) if g.ShapeType().name == "TopAbs_FACE"]
        present = [g for g in generated if follow(None, shape, g)]
        if not present:
            failed.append(res.names[i])
            continue
        if len(present) == 1:
            names.append((f"{feature.id}.face[{i}]", f"face[{i}]", present[0]))
        else:
            for k, g in enumerate(present):
                names.append((f"{feature.id}.face[{i}].{k}", f"face[{i}]", g))
    return names, failed


def _smallest_face(part: Any, res: Any) -> str:
    """D8: a fillet refusal names the face height - the smallest extent of the
    faces the edges roll across (r12 on the 10 mm plate reads "10.000 mm")."""
    try:
        faces = part.inventory().faces
    except CommandError:
        return ""
    heights: list[float] = []
    for edge in res.infos:
        for i in getattr(edge, "adjacent_face_indices", ()):
            if 0 <= i < len(faces):
                x0, y0, z0, x1, y1, z1 = faces[i].bbox
                extents = [d for d in (x1 - x0, y1 - y0, z1 - z0) if d > 1e-9]
                if extents:
                    heights.append(min(extents))
    if not heights:
        return ""
    return f" The smallest face it rolls across is {min(heights):.3f} mm high."


@builder("fillet")
def build_fillet(doc: Any, part: Any, feature: Any, assumed: dict[str, Any]) -> Outcome:
    from partkiln.brep import history, shapes

    args = feature.args
    if part.shape is None:
        raise CommandError(f"fillet {feature.id}: part {part.name} has no body.", code="pk_needs")
    if args.get("r") is None:
        raise CommandError(
            f"fillet {feature.id} needs r (a radius, or [r1, r2] for a variable fillet): a fillet "
            "radius is design intent and has no default.",
            code="pk_needs",
        )
    res = many(part, feature, args.get("edges"), "edge", "edges")
    radius = _pair(doc, feature, args["r"], assumed, "r")
    try:
        result = shapes.fillet(part.shape, [e.shape for e in res.infos], radius)
    except KernelError as exc:
        listed = ", ".join(res.names[:6])
        raise CommandError(
            f"fillet {feature.id} r={radius} on {listed}: {exc.message}"
            f"{_smallest_face(part, res)} Fix: {exc.fix}",
            code="pk_op_failed",
        ) from exc
    hm = history.record(result.algo, result.inputs)
    names, failed = _edge_faces(hm, result.shape, res, feature, result.ignored_edges)
    if not names:
        raise CommandError(
            f"fillet {feature.id}: OCCT generated no face for any of {', '.join(res.names[:6])} "
            "(Law 11). Are these seams or tangent edges? Select the sharp edges.",
            code="pk_no_effect",
        )
    extra = {
        "r_mm": radius if isinstance(radius, float) else list(radius),
        "edges_filleted": len(names),
    }
    if result.faulty_contours:
        extra["faulty_contours"] = result.faulty_contours
    return Outcome(result.shape, hm, names, failed_edges=failed, extra=extra)


@builder("chamfer")
def build_chamfer(doc: Any, part: Any, feature: Any, assumed: dict[str, Any]) -> Outcome:
    from partkiln.brep import history, shapes

    args = feature.args
    if part.shape is None:
        raise CommandError(f"chamfer {feature.id}: part {part.name} has no body.", code="pk_needs")
    raw = args.get("d")
    if raw is None:
        raise CommandError(
            f"chamfer {feature.id} needs d (a distance, [d1, d2], or {{d, angle}}): a chamfer size "
            "is design intent and has no default.",
            code="pk_needs",
        )
    res = many(part, feature, args.get("edges"), "edge", "edges")
    if isinstance(raw, dict):
        if "d" not in raw or "angle" not in raw:
            raise CommandError(f"chamfer {feature.id}: {{d, angle}} needs both.", code="pk_needs")
        d1 = doc.length(raw["d"], assumed, feature.param_deps)
        angle = doc.angle(raw["angle"], assumed, feature.param_deps)
        if not 0 < angle < 90 or d1 <= 0:
            raise CommandError(
                f"chamfer {feature.id}: d > 0 and angle in (0, 90).", code="pk_needs"
            )
        distance: float | tuple[float, float] = (d1, d1 * math.tan(math.radians(angle)))
    else:
        distance = _pair(doc, feature, raw, assumed, "d")
    try:
        result = shapes.chamfer(part.shape, [e.shape for e in res.infos], distance)
    except KernelError as exc:
        listed = ", ".join(res.names[:6])
        raise CommandError(
            f"chamfer {feature.id} d={distance} on {listed}: {exc.message} Fix: {exc.fix}",
            code="pk_op_failed",
        ) from exc
    hm = history.record(result.algo, result.inputs)
    names, failed = _edge_faces(hm, result.shape, res, feature, result.ignored_edges)
    if not names:
        raise CommandError(
            f"chamfer {feature.id}: OCCT generated no face for any of {', '.join(res.names[:6])} "
            "(Law 11). Select the sharp edges.",
            code="pk_no_effect",
        )
    extra = {
        "d_mm": distance if isinstance(distance, float) else [round(x, 3) for x in distance],
        "edges_chamfered": len(names),
    }
    return Outcome(result.shape, hm, names, failed_edges=failed, extra=extra)


__all__ = ["build_chamfer", "build_fillet"]
