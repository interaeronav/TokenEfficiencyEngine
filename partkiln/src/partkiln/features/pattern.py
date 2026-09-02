"""Pattern (rect / circular / sketch-driven) and mirror: copies of a feature's tools, ONE boolean.

A pattern does not re-run its source feature n times: it takes the tool
bodies the source made BEFORE its boolean (the hole's cylinders, the
extrude's prism), transforms a copy per instance with `brep.shapes.transform`
(instance 0 is the source itself and is never re-cut), and applies ONE
boolean in the source's own mode - the measured fact behind it is F5: 100
holes as one n-ary cut in 0.09 s against 0.46 s sequentially, identical
topology (106 faces, 312 unique edges, 520 481.421 mm3). Glue is never
used: it returned the uncut plate with `IsDone() == True`.

`layout: rect {dx, nx, dy, ny}` steps along the source's frame x / y (the
face a hole was drilled from, the sketch plane of an extrude); `circ {axis,
n, angle}` turns about an axis (`Z` is the world axis through the origin - the
disc fixture: d80 x 5 with 6 x d5 on PCD 60 -> 24 543.693 mm3, 9 faces);
`sketch {points}` offsets in the same frame (`layout` is inferred from
nx/dx, axis/n or points when omitted - `kind` is the wire's word for the
feature itself, so it cannot double as the layout). `suppress: [i]` skips
instances (i >= 1; the source is suppressed on its own feature). Children
are named `<name>.<i>.<role>` from the source's tool roles followed through
the copy's `Modified` and the boolean's history.

`mirror {of, plane}`: `of` a feature mirrors its tools; `of` the PART
mirrors the whole body and joins it (F2 about x=80 -> 89 833.933 mm3, 17
faces after unify). The plane is XY | XZ | YZ | plane:<n> | x=80 | a face.
OCP is imported inside functions only.
"""

from __future__ import annotations

from typing import Any

from partkiln.document import CommandError
from partkiln.features.base import Outcome, boolean, builder, follow, refs_of
from partkiln.features.workplane import axis_of, plane_of
from partkiln.sketch.profile import NAMED_FRAMES, Frame

Vec3 = tuple[float, float, float]

_PATTERNABLE = ("extrude", "revolve", "sweep", "loft", "hole")


def _source(part: Any, feature: Any, of: Any) -> Any:
    if not of:
        raise CommandError(
            f"{feature.kind} {feature.id} needs of: <feature name>.", code="pk_needs"
        )
    src = part.feature(str(of))
    refs_of(feature, str(of))
    feature.depends.add(f"feat:{src.id}")
    if src.kind not in _PATTERNABLE or not src.tools:
        raise CommandError(
            f"{feature.kind} {feature.id}: {src.kind} {src.id} has no tool body to copy; only "
            f"{', '.join(_PATTERNABLE)} features can be patterned or mirrored. Pattern the "
            "feature that made the geometry, then fillet the result.",
            code="pk_needs",
        )
    if not src.active:
        raise CommandError(
            f"{feature.kind} {feature.id}: {src.id} is "
            f"{src.status if src.status != 'ok' else 'suppressed'}.",
            code="pk_needs",
        )
    if src.mode == "intersect":
        raise CommandError(
            f"{feature.kind} {feature.id}: an intersect cannot be patterned.", code="pk_needs"
        )
    return src


def _copy(tool: Any, translation: Vec3 = (0.0, 0.0, 0.0), rotation: Any = None) -> tuple[Any, Any]:
    from partkiln.brep import history, shapes

    res = shapes.transform(tool, translation=translation, rotation=rotation)
    return res.shape, history.record(res.algo, res.inputs)


def _mirror(shape: Any, point: Vec3, normal: Vec3) -> tuple[Any, Any]:
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt, gp_Trsf

    from partkiln.brep import history

    trsf = gp_Trsf()
    trsf.SetMirror(gp_Ax2(gp_Pnt(*point), gp_Dir(*normal)))
    algo = BRepBuilderAPI_Transform(shape, trsf, True)
    return algo.Shape(), history.record(algo, [shape])


def _child_names(
    feature: Any,
    prefix: str,
    roles: list[tuple[str, Any]],
    copy_map: Any,
    copy_shape: Any,
    hist: Any,
    shape: Any,
    present: list[Any] | None = None,
) -> list[tuple[str, str, Any]]:
    from OCP.TopAbs import TopAbs_FACE

    from partkiln.brep import query, shapes

    if present is None:
        present = shapes.unique_subshapes(shape, TopAbs_FACE)
    out: list[tuple[str, str, Any]] = []
    for role, sub in roles:
        moved = copy_map.successors(sub)
        hits: list[Any] = []
        for m in moved:
            for h in follow(hist, shape, m, present):
                if not any(h.IsSame(x) for x in hits):
                    hits.append(h)
        if len(hits) == 1:
            out.append((f"{prefix}.{role}", role, hits[0]))
        elif hits:
            ranked = sorted(
                hits, key=lambda h: tuple(round(c, 3) for c in query.faces(h)[0].centroid)
            )
            for k, h in enumerate(ranked):
                out.append((f"{prefix}.{role}[{k}]", role, h))
    return out


def _frame_of(src: Any) -> Frame:
    return src.frame if src.frame is not None else NAMED_FRAMES["XY"]


@builder("pattern")
def build_pattern(doc: Any, part: Any, feature: Any, assumed: dict[str, Any]) -> Outcome:
    args = feature.args
    src = _source(part, feature, args.get("of"))
    kind = args.get("layout")
    if kind is None:
        if "points" in args:
            kind = "sketch"
        elif "axis" in args or "n" in args:
            kind = "circ"
        elif "nx" in args or "ny" in args or "dx" in args:
            kind = "rect"
        if kind is not None:
            assumed["layout"] = kind
    if kind not in ("rect", "circ", "sketch"):
        raise CommandError(
            f"pattern {feature.id} needs layout: rect {{dx, nx, dy, ny}} | circ {{axis, n, angle}} "
            "| sketch {points}.",
            code="pk_needs",
        )
    deps = feature.param_deps
    frame = _frame_of(src)
    if src.frame is None:
        assumed["frame"] = "world XY (the source has no frame)"
    transforms: list[tuple[Vec3, Any]] = []  # (translation, rotation) per instance i >= 1
    if kind == "rect":
        nx = int(args.get("nx", 1))
        ny = int(args.get("ny", 1))
        if "ny" not in args:
            assumed["ny"] = 1
        if nx < 1 or ny < 1 or (nx == 1 and ny == 1):
            raise CommandError(
                f"pattern {feature.id}: rect needs nx and/or ny > 1.", code="pk_needs"
            )
        if (nx > 1 and args.get("dx") is None) or (ny > 1 and args.get("dy") is None):
            raise CommandError(
                f"pattern {feature.id}: rect needs dx for nx > 1 and dy for ny > 1.",
                code="pk_needs",
            )
        dx = doc.length(args["dx"], assumed, deps) if nx > 1 else 0.0
        dy = doc.length(args["dy"], assumed, deps) if ny > 1 else 0.0
        xd, yd = frame.xdir, frame.ydir
        for ix in range(nx):
            for iy in range(ny):
                if ix == 0 and iy == 0:
                    continue
                t = (
                    dx * ix * xd[0] + dy * iy * yd[0],
                    dx * ix * xd[1] + dy * iy * yd[1],
                    dx * ix * xd[2] + dy * iy * yd[2],
                )
                transforms.append((t, None))
    elif kind == "circ":
        n = int(args.get("n", 0))
        if n < 2 or args.get("axis") is None:
            raise CommandError(
                f"pattern {feature.id}: circ needs axis and n >= 2.", code="pk_needs"
            )
        point, direction = axis_of(doc, args["axis"], part, feature)
        if isinstance(args["axis"], str):
            refs_of(feature, str(args["axis"]))
        angle = doc.angle(args["angle"], assumed, deps) if "angle" in args else 360.0
        if "angle" not in args:
            assumed["angle"] = 360
        step = angle / n if abs(angle - 360.0) < 1e-9 else angle / (n - 1)
        for i in range(1, n):
            transforms.append(((0.0, 0.0, 0.0), (point, direction, i * step)))
    else:
        points = args.get("points")
        if not isinstance(points, list | tuple) or not points:
            raise CommandError(
                f"pattern {feature.id}: sketch needs points: [[x, y], ...].", code="pk_needs"
            )
        for p in points:
            if not isinstance(p, list | tuple) or len(p) != 2:
                raise CommandError(
                    f"pattern {feature.id}: points are [x, y]; got {p!r}.", code="pk_needs"
                )
            x, y = doc.length(p[0], assumed, deps), doc.length(p[1], assumed, deps)
            xd, yd = frame.xdir, frame.ydir
            transforms.append(
                ((x * xd[0] + y * yd[0], x * xd[1] + y * yd[1], x * xd[2] + y * yd[2]), None)
            )
    count = len(transforms) + 1
    suppress = args.get("suppress") or []
    if not isinstance(suppress, list | tuple):
        raise CommandError(
            f"pattern {feature.id}: suppress is a list of instance numbers.", code="pk_needs"
        )
    suppressed: set[int] = set()
    for s in suppress:
        if not isinstance(s, int) or isinstance(s, bool) or not 1 <= s < count:
            raise CommandError(
                f"pattern {feature.id}: suppress {s!r} is not an instance 1..{count - 1} "
                "(0 is the source; suppress it with set feat:<source> suppressed=true).",
                code="pk_needs",
            )
        suppressed.add(s)
    copies: list[tuple[int, Any, Any]] = []
    tools: list[Any] = []
    for i, (translation, rotation) in enumerate(transforms, start=1):
        if i in suppressed:
            continue
        for tool in src.tools:
            moved, cmap = _copy(tool, translation, rotation)
            copies.append((i, moved, cmap))
            tools.append(moved)
    if not tools:
        raise CommandError(
            f"pattern {feature.id}: every instance is suppressed.", code="pk_no_effect"
        )
    mode = "cut" if src.mode == "cut" else "join"
    shape, hist = boolean(part.shape, tools, mode, feature, bool(args.get("allow_no_effect")))
    names: list[tuple[str, str, Any]] = []
    per_tool = len(src.tools)
    present = _present_faces(shape)
    for k, (i, moved, cmap) in enumerate(copies):
        roles = src.tool_roles if per_tool == 1 else _roles_for_tool(src, k % per_tool)
        names.extend(
            _child_names(feature, f"{feature.id}.{i}", roles, cmap, moved, hist, shape, present)
        )
    extra = {"layout": kind, "instances": count, "suppressed": sorted(suppressed), "source": src.id}
    return Outcome(shape, hist, names, tools, [], mode, frame=frame, extra=extra)


def _present_faces(shape: Any) -> list[Any]:
    from OCP.TopAbs import TopAbs_FACE

    from partkiln.brep import shapes

    return shapes.unique_subshapes(shape, TopAbs_FACE)


def _roles_for_tool(src: Any, k: int) -> list[tuple[str, Any]]:
    """Roles that live on the k-th tool of a multi-tool source (hole instances)."""
    from OCP.TopAbs import TopAbs_FACE

    from partkiln.brep import shapes

    present = shapes.unique_subshapes(src.tools[k], TopAbs_FACE)
    return [(role, sub) for role, sub in src.tool_roles if any(sub.IsSame(p) for p in present)]


@builder("mirror")
def build_mirror(doc: Any, part: Any, feature: Any, assumed: dict[str, Any]) -> Outcome:
    args = feature.args
    of = args.get("of")
    if not of or args.get("plane") is None:
        raise CommandError(
            f"mirror {feature.id} needs of: <feature | part> and plane: XY | XZ | YZ | plane:<n> "
            "| x=80 | <face ref>.",
            code="pk_needs",
        )
    point, normal = plane_of(doc, args["plane"], part, feature)
    if isinstance(args["plane"], str):
        refs_of(feature, str(args["plane"]))
    if str(of) in (part.name, f"part:{part.name}"):
        if part.shape is None:
            raise CommandError(
                f"mirror {feature.id}: part {part.name} has no body.", code="pk_needs"
            )
        refs_of(feature, f"part:{part.name}")
        inv = part.inventory()
        roles = [(inv.name_of_face(i), f.shape) for i, f in enumerate(inv.faces)]
        moved, cmap = _mirror(part.shape, point, normal)
        shape, hist = boolean(
            part.shape, [moved], "join", feature, bool(args.get("allow_no_effect"))
        )
        names = _child_names(feature, feature.id, roles, cmap, moved, hist, shape)
        return Outcome(shape, hist, names, [moved], [], "join", extra={"of": part.name})
    src = _source(part, feature, of)
    mode = "cut" if src.mode == "cut" else "join"
    tools: list[Any] = []
    copies: list[tuple[Any, Any]] = []
    for tool in src.tools:
        moved, cmap = _mirror(tool, point, normal)
        tools.append(moved)
        copies.append((moved, cmap))
    shape, hist = boolean(part.shape, tools, mode, feature, bool(args.get("allow_no_effect")))
    names: list[tuple[str, str, Any]] = []
    per_tool = len(src.tools)
    for k, (moved, cmap) in enumerate(copies):
        roles = src.tool_roles if per_tool == 1 else _roles_for_tool(src, k)
        names.extend(_child_names(feature, f"{feature.id}.1", roles, cmap, moved, hist, shape))
    return Outcome(shape, hist, names, tools, [], mode, extra={"of": src.id})


__all__ = ["build_mirror", "build_pattern"]
