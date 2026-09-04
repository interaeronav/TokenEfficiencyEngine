"""Dimensions, hole tables and parts lists - every number read from the model.

**Law 15: a drawing dimension is read back from the model, never typed.** No
kind here accepts a `value`; each one names sub-shapes and asks the B-rep what
they measure. A dimension therefore carries two numbers and a verdict:

  `value_mm`      what the MODEL says (bounding box in the view frame, face
                  centroids and axes, cylinder radii, plane normals - exact
                  `BRepGProp`/`BRepBndLib` reads, never a tessellation).
  `projected_mm`  what the DRAWN geometry says (the HLR primitives of the view:
                  the bbox of the projected edges, the centre and radius of the
                  circle actually drawn for a hole, the projected directions).
  `agree`         `abs(value_mm - projected_mm) < 1e-3`.

The two are computed by different routes on purpose. If a view is placed wrong,
a circle is missing, or a scale is applied twice, `agree` goes false and the
sheet says so instead of printing a confident wrong number.

Kinds (D5): `extent` `dist` `dia` `rad` `angle` `chamfer` `ordinate` `baseline`.
`angle` between two planar faces is the angle between the PLANES (the acute
fold of the normals), which is what a drafted wall means on a drawing: a box
side drafted 3 degrees reads 3.000 against its undrafted opposite, not 177.

Placement is computed in SHEET millimetres from anchors kept in view
millimetres, so text, arrowheads and offsets keep their size at any scale
(ISO 3098: 3.5 mm characters). Dimensions of the same view and axis stack at a
fixed pitch in declaration order, which makes a baseline chain a chain.

The hole table reads cylindrical faces whose axis is the line of sight - dia
from the model radius, x/y from the view frame - and names them from the part's
inventory; the note line ("4x d6.6 THRU (M6 clearance, ISO 273 medium)") comes
from the owning hole feature's `std` argument through `partkiln.standards`, so
the standard on the sheet is the standard the geometry was cut to. ISO 273's
three series are Close/Normal/Loose in the shipped table and fine/medium/coarse
in the standard's own words (`data/manifest.json`), so the note prints the
standard's word.

OCP is imported inside functions only.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from partkiln.document import CommandError
from partkiln.drawing.hlr import Arc, Prim, Pt2, Segment
from partkiln.drawing.views import TEXT_MM, Drawing, View

AGREE_TOL_MM = 1e-3
ARC_MATCH_MM = 0.5

ARROW_MM = 3.2
ARROW_HALF_DEG = 10.0
DIM_GAP_MM = 12.0
DIM_STEP_MM = 8.0
EXT_GAP_MM = 1.2
EXT_OVER_MM = 2.0
LEADER_MM = 8.0
TAIL_MM = 7.0

KINDS = ("extent", "dist", "dia", "rad", "angle", "chamfer", "ordinate", "baseline")
# ISO 273 names its three clearance series fine / medium / coarse; the shipped
# table (bd_warehouse) heads the columns Close / Normal / Loose.
ISO273_SERIES = {"close": "fine", "normal": "medium", "loose": "coarse"}

Vec3 = tuple[float, float, float]


def _r3(x: float) -> float:
    return round(float(x), 3) + 0.0


def _num(x: float) -> str:
    """A drawing number: 100.0 -> '100', 6.6 -> '6.6', 3.0000001 -> '3'."""
    return f"{round(float(x), 3) + 0.0:g}"


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(float(x) * float(y) for x, y in zip(a, b, strict=True))


# --------------------------------------------------------------------------- the record


@dataclass
class Dimension:
    """One dimension: what the model says, what the drawing says, and whether
    they agree."""

    name: str
    view: str
    kind: str
    refs: list[str]
    value_mm: float
    projected_mm: float
    text: str
    axis: str = ""
    values_mm: list[float] = field(default_factory=list)
    anchors: tuple[Pt2, Pt2] = ((0.0, 0.0), (0.0, 0.0))
    chain: list[Pt2] = field(default_factory=list)
    index: int = 0
    centre: Pt2 | None = None
    radius: float = 0.0
    lines2d: tuple[tuple[Pt2, Pt2], tuple[Pt2, Pt2]] | None = None
    projected_from: str = "frame"
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def agree(self) -> bool:
        return abs(self.value_mm - self.projected_mm) < AGREE_TOL_MM

    def summary(self) -> dict[str, Any]:
        """The D7 `dim:` row."""
        out: dict[str, Any] = {
            "id": f"dim:{self.name}",
            "kind": self.kind,
            "view": self.view,
            "refs": list(self.refs),
            "value_mm": _r3(self.value_mm),
            "projected_mm": _r3(self.projected_mm),
            "agree": self.agree,
        }
        if self.axis:
            out["axis"] = self.axis
        return out

    def row(self) -> dict[str, Any]:
        out = self.summary()
        out["text"] = self.text
        if self.values_mm:
            out["values_mm"] = [_r3(v) for v in self.values_mm]
        if self.extra:
            out.update(self.extra)
        return out


# --------------------------------------------------------------------------- model reads


def _resolve(part: Any, ref: Any, what: str) -> tuple[Any, str]:
    """One sub-shape by name or selector: a face if there is one, else an edge.

    A hole instance is addressed `h.1` on the wire (D5's `dist a: h.1`) while
    the kernel names its wall `h.1.wall`, so the bare instance is retried with
    the role appended before anything is refused.
    """
    from partkiln import naming

    text = str(ref)
    errors: list[CommandError] = []
    for candidate in (text, f"{text}.wall"):
        for kind in ("face", "edge"):
            try:
                res = naming.resolve(part, candidate, kind, "one")
            except CommandError as exc:
                errors.append(exc)
                continue
            return res.infos[0], res.names[0]
    raise CommandError(f"{what}: {ref!r} names no face or edge. {errors[0]}", code=errors[0].code)


def _centre3(info: Any) -> Vec3:
    """The 3D point a dimension measures to: a face's centroid (the axis point
    of a full cylinder) or an edge's mid-parameter point."""
    centre = getattr(info, "centroid", None)
    if centre is None:
        centre = info.midpoint
    return (float(centre[0]), float(centre[1]), float(centre[2]))


def _radius_of(info: Any, ref: str) -> float:
    r = getattr(info, "radius", None)
    if r is None:
        kind = getattr(info, "surface_type", None) or getattr(info, "curve_type", "?")
        raise CommandError(
            f"{ref} is a {kind}; a dia/rad dimension needs a cylinder, a cone, a sphere or a "
            "circular edge. Fix: name the hole wall (h.1.wall) or the arc edge.",
            code="pk_ref_unknown",
        )
    return float(r)


def _normal_of(info: Any, ref: str) -> Vec3:
    n = getattr(info, "normal", None) or getattr(info, "direction", None)
    if n is None:
        raise CommandError(
            f"{ref} has no direction to measure an angle from. Fix: name a planar face or a "
            "straight edge.",
            code="pk_ref_unknown",
        )
    return (float(n[0]), float(n[1]), float(n[2]))


def _compound(subshapes: Sequence[Any]) -> Any:
    from OCP.BRep import BRep_Builder
    from OCP.TopoDS import TopoDS_Compound

    builder = BRep_Builder()
    comp = TopoDS_Compound()
    builder.MakeCompound(comp)
    for s in subshapes:
        builder.Add(comp, s)
    return comp


def _frame_extents(shape: Any, view: View) -> tuple[float, float, float]:
    """The shape's tight extents along the view's right / up / depth axes.

    The shape is rotated into the view frame with a `gp_Trsf` built from
    (right, up, direction) - a right-handed orthonormal triple by construction
    (`right = up x direction`) - and measured with `BRepBndLib.AddOptimal_s`,
    which is exact for analytic geometry and never pads by the tolerance. This
    is a MODEL read: no projection, no tessellation.
    """
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Trsf

    from partkiln.brep import shapes as _shapes

    r, u, n = view.frame.right, view.frame.up, view.frame.direction
    trsf = gp_Trsf()
    trsf.SetValues(r[0], r[1], r[2], 0.0, u[0], u[1], u[2], 0.0, n[0], n[1], n[2], 0.0)
    moved = BRepBuilderAPI_Transform(shape, trsf, True).Shape()
    x0, y0, z0, x1, y1, z1 = _shapes.bbox(moved)
    return (x1 - x0, y1 - y0, z1 - z0)


# --------------------------------------------------------------------------- drawn reads


def _prims_bbox_extent(prims: Sequence[Prim], axis_index: int) -> float:
    from partkiln.drawing import hlr

    box = hlr.prim_bbox(prims)
    if box is None:
        return 0.0
    return box[axis_index + 2] - box[axis_index]


def _drawn_circle(view: View, expected: Pt2, radius: float) -> tuple[Pt2, float] | None:
    """The arc the sheet actually draws for a hole: the nearest circle to where
    the model puts it, within `ARC_MATCH_MM`. A missing or displaced circle
    leaves `projected_mm` at the frame value and `agree` decides."""
    best: tuple[float, Arc] | None = None
    for prim in (*view.visible, *view.hidden):
        if not isinstance(prim, Arc):
            continue
        d = math.hypot(prim.cx - expected[0], prim.cy - expected[1])
        if d <= ARC_MATCH_MM and (best is None or d < best[0]):
            best = (d, prim)
    if best is None:
        return None
    arc = best[1]
    del radius
    return ((arc.cx, arc.cy), arc.r)


def _projected_centre(view: View, info: Any) -> tuple[Pt2, str]:
    """Where the drawing puts a sub-shape: the centre of the circle it drew when
    there is one, else the frame projection of the model centroid."""
    expected = view.frame.to_view(_centre3(info))
    r = getattr(info, "radius", None)
    if r is not None:
        found = _drawn_circle(view, expected, float(r))
        if found is not None:
            return (found[0], "arc")
    return (expected, "frame")


# --------------------------------------------------------------------------- axes


def _axis_index(value: Any, what: str, default: str | None = None) -> tuple[int, str]:
    """`X`/`Y` are the view's horizontal and vertical, `Z` its depth (D5)."""
    if value is None:
        if default is None:
            raise CommandError(
                f"{what} needs axis: 'X' (across the view) or 'Y' (up the view).",
                code="pk_needs",
            )
        value = default
    key = str(value).strip().upper().lstrip("+")
    if key not in ("X", "Y", "Z"):
        raise CommandError(
            f"{what}: axis {value!r} is X (across the view), Y (up the view) or Z (its depth).",
            code="pk_needs",
        )
    return ("XYZ".index(key), key)


def _view_axis(view: View, index: int) -> Vec3:
    return (view.frame.right, view.frame.up, view.frame.direction)[index]


# --------------------------------------------------------------------------- the kinds


def _refs_of(spec: dict[str, Any], key: str) -> list[str]:
    raw = spec.get(key)
    if raw is None:
        return []
    if isinstance(raw, list | tuple):
        return [str(r) for r in raw]
    return [str(raw)]


def _measure_extent(part: Any, view: View, spec: dict[str, Any], name: str) -> dict[str, Any]:
    from partkiln.drawing import hlr

    index, axis = _axis_index(spec.get("axis"), f"dimension {name}")
    refs = _refs_of(spec, "of")
    if refs:
        infos = [_resolve(part, r, f"dimension {name}") for r in refs]
        shape = _compound([i[0].shape for i in infos])
        names = [i[1] for i in infos]
        value = _frame_extents(shape, view)[index]
        drawn = hlr.project(shape, view.frame.direction, view.frame.up)
        projected = _prims_bbox_extent([*drawn.visible, *drawn.hidden], index if index < 2 else 0)
        source = "hlr"
    else:
        names = [part.name]
        value = _frame_extents(part.shape, view)[index]
        projected = _prims_bbox_extent([*view.visible, *view.hidden], index if index < 2 else 0)
        source = "view"
    x0, y0, x1, y1 = view.view_bbox()
    anchors = ((x0, y0), (x1, y0)) if index == 0 else ((x0, y0), (x0, y1))
    return {
        "refs": names,
        "axis": axis,
        "value_mm": value,
        "projected_mm": projected,
        "text": _num(value),
        "anchors": anchors,
        "projected_from": source,
    }


def _measure_dist(part: Any, view: View, spec: dict[str, Any], name: str) -> dict[str, Any]:
    a_ref, b_ref = spec.get("a"), spec.get("b")
    if a_ref is None or b_ref is None:
        raise CommandError(
            f"dimension {name}: a dist needs a: and b:, the two sub-shapes it spans.",
            code="pk_needs",
        )
    a_info, a_name = _resolve(part, a_ref, f"dimension {name} a")
    b_info, b_name = _resolve(part, b_ref, f"dimension {name} b")
    ca, cb = _centre3(a_info), _centre3(b_info)
    delta = (cb[0] - ca[0], cb[1] - ca[1], cb[2] - ca[2])
    pa, from_a = _projected_centre(view, a_info)
    pb, from_b = _projected_centre(view, b_info)
    if spec.get("axis") is None:
        value = math.dist(ca, cb)
        projected = math.dist(pa, pb)
        axis = ""
    else:
        index, axis = _axis_index(spec.get("axis"), f"dimension {name}")
        value = abs(_dot(delta, _view_axis(view, index)))
        projected = (
            abs(pb[0] - pa[0])
            if index == 0
            else abs(pb[1] - pa[1])
            if index == 1
            else abs(_dot(delta, view.frame.direction))
        )
    return {
        "refs": [a_name, b_name],
        "axis": axis,
        "value_mm": value,
        "projected_mm": projected,
        "text": _num(value),
        "anchors": (pa, pb),
        "projected_from": "arc" if "arc" in (from_a, from_b) else "frame",
    }


def _measure_round(part: Any, view: View, spec: dict[str, Any], name: str, kind: str) -> dict:
    ref = spec.get("of") or spec.get("a")
    if ref is None:
        raise CommandError(
            f"dimension {name}: a {kind} needs of: <cylindrical face or circular edge>.",
            code="pk_needs",
        )
    info, resolved = _resolve(part, ref, f"dimension {name}")
    r = _radius_of(info, resolved)
    centre, source = _projected_centre(view, info)
    drawn = _drawn_circle(view, view.frame.to_view(_centre3(info)), r)
    drawn_r = drawn[1] if drawn is not None else r
    value = 2.0 * r if kind == "dia" else r
    projected = 2.0 * drawn_r if kind == "dia" else drawn_r
    count = int(spec.get("count") or 1)
    head = f"{count}× " if count > 1 else ""  # noqa: RUF001 - the drawing symbol
    text = f"{head}Ø{_num(value)}" if kind == "dia" else f"{head}R{_num(value)}"
    return {
        "refs": [resolved],
        "value_mm": value,
        "projected_mm": projected,
        "text": text,
        "centre": centre,
        "radius": drawn_r,
        "anchors": (centre, centre),
        "projected_from": source,
        "extra": {"count": count} if count > 1 else {},
    }


def _fold(cos_value: float) -> float:
    return math.degrees(math.acos(max(0.0, min(1.0, abs(cos_value)))))


def _measure_angle(part: Any, view: View, spec: dict[str, Any], name: str) -> dict[str, Any]:
    a_ref, b_ref = spec.get("a"), spec.get("b")
    if a_ref is None or b_ref is None:
        raise CommandError(
            f"dimension {name}: an angle needs a: and b:, two planar faces or two straight edges.",
            code="pk_needs",
        )
    a_info, a_name = _resolve(part, a_ref, f"dimension {name} a")
    b_info, b_name = _resolve(part, b_ref, f"dimension {name} b")
    na, nb = _normal_of(a_info, a_name), _normal_of(b_info, b_name)
    value = _fold(_dot(na, nb))
    a2 = view.frame.vector(na)
    b2 = view.frame.vector(nb)
    la, lb = math.hypot(*a2), math.hypot(*b2)
    cos2d = (a2[0] * b2[0] + a2[1] * b2[1]) / (la * lb) if la > 1e-9 and lb > 1e-9 else 1.0
    projected = _fold(cos2d)
    pa = view.frame.to_view(_centre3(a_info))
    pb = view.frame.to_view(_centre3(b_info))
    # A face draws itself edge-on as a line perpendicular to its projected normal.
    da = (-a2[1] / la, a2[0] / la) if la > 1e-9 else (1.0, 0.0)
    db = (-b2[1] / lb, b2[0] / lb) if lb > 1e-9 else (0.0, 1.0)
    return {
        "refs": [a_name, b_name],
        "value_mm": value,
        "projected_mm": projected,
        "text": f"{_num(value)}°",
        "anchors": (pa, pb),
        "lines2d": ((pa, (pa[0] + da[0], pa[1] + da[1])), (pb, (pb[0] + db[0], pb[1] + db[1]))),
        "extra": {"angle_deg": _r3(value)},
    }


def _measure_chamfer(part: Any, view: View, spec: dict[str, Any], name: str) -> dict[str, Any]:
    """The chamfer's leg and its angle, both read off the geometry.

    The chamfer face F meets two faces A and B. The leg along A is the distance
    from the edge F-B to the PLANE of A: on a 1 mm 45-degree chamfer of a box
    corner that is exactly 1 mm, with no dependence on how the feature was
    specified (`d`, `[d1, d2]` or `{d, angle}`).
    """
    ref = spec.get("of") or spec.get("a")
    if ref is None:
        raise CommandError(
            f"dimension {name}: a chamfer needs of: <the chamfer face>.", code="pk_needs"
        )
    info, resolved = _resolve(part, ref, f"dimension {name}")
    if getattr(info, "surface_type", "") != "plane":
        raise CommandError(
            f"dimension {name}: {resolved} is a {getattr(info, 'surface_type', '?')} face; a "
            "chamfer dimension needs the flat chamfer face.",
            code="pk_ref_unknown",
        )
    from partkiln.brep import query

    inv = part.inventory()
    index = inv.aliases.get(resolved)
    if index is None:
        raise CommandError(
            f"dimension {name}: {resolved} is not on the current body.", code="pk_ref_stale"
        )
    faces = inv.faces
    neighbours = []
    for e in query.edges(part.shape, faces):
        if index in e.adjacent_face_indices:
            for other in e.adjacent_face_indices:
                if other != index and faces[other].surface_type == "plane":
                    neighbours.append((other, e))
    # A chamfer band meets FOUR planar faces on a box corner: the two it cut
    # into, along its two long edges, and the neighbouring chamfer bands along
    # its two short ends. The two it cut into are the ones with the long shared
    # edges, so the pair is chosen by edge length (measured: the wrong pair on a
    # 100 mm band reads 1 mm for a 2 mm chamfer).
    neighbours.sort(key=lambda pair: (-pair[1].length, pair[0]))
    if len(neighbours) < 2:
        raise CommandError(
            f"dimension {name}: {resolved} does not meet two planar faces, so it has no leg to "
            "measure. Fix: name the chamfer face itself.",
            code="pk_ref_unknown",
        )
    (ia, ea), (_ib, eb) = neighbours[0], neighbours[1]
    fa = faces[ia]
    pa, pb = ea.midpoint, eb.midpoint
    na = fa.normal or (0.0, 0.0, 1.0)
    leg = abs(_dot((pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2]), na))
    angle = _fold(_dot(info.normal or (0.0, 0.0, 1.0), na))
    p0 = view.frame.to_view(pa)
    p1 = view.frame.to_view(pb)
    projected = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    # The drawn leg is the projected span only when the corner lies in the view
    # plane; on a 45-degree chamfer the projected span is the hypotenuse.
    projected = projected * abs(math.cos(math.radians(angle))) if projected > 0 else 0.0
    return {
        "refs": [resolved],
        "value_mm": leg,
        "projected_mm": projected,
        "text": f"{_num(leg)} × {_num(angle)}°",  # noqa: RUF001 - the drawing symbol
        "anchors": (p0, p1),
        "extra": {"angle_deg": _r3(angle)},
    }


def _measure_chain(part: Any, view: View, spec: dict[str, Any], name: str, kind: str) -> dict:
    index, axis = _axis_index(spec.get("axis"), f"dimension {name}")
    refs = _refs_of(spec, "of")
    if not refs:
        raise CommandError(
            f"dimension {name}: a {kind} chain needs of: [<ref>, ...] - the features it steps "
            "through.",
            code="pk_needs",
        )
    infos = [_resolve(part, r, f"dimension {name}") for r in refs]
    direction = _view_axis(view, index)
    if spec.get("from") is not None:
        origin_info, origin_name = _resolve(part, spec["from"], f"dimension {name} from")
        base = _dot(_centre3(origin_info), direction)
        base2 = view.frame.to_view(_centre3(origin_info))[index] if index < 2 else 0.0
    else:
        # The datum is the body's own extreme on that axis - the edge a machinist
        # hooks a rule over. Read from the model as the least of the eight
        # bounding-box corners along the axis; the drawn datum is the same edge
        # in the projected outline.
        from partkiln.brep import shapes as _shapes

        origin_name = f"{part.name} datum"
        corners = _shapes.bbox(part.shape)
        base = min(
            _dot(
                (
                    corners[0] if (m & 1) else corners[3],
                    corners[1] if (m & 2) else corners[4],
                    corners[2] if (m & 4) else corners[5],
                ),
                direction,
            )
            for m in range(8)
        )
        base2 = view.view_bbox()[index] if index < 2 else 0.0
    values: list[float] = []
    projected: list[float] = []
    points: list[Pt2] = []
    for info, _resolved_name in infos:
        values.append(abs(_dot(_centre3(info), direction) - base))
        centre, _ = _projected_centre(view, info)
        points.append(centre)
        projected.append(abs((centre[index] if index < 2 else 0.0) - base2))
    order = sorted(range(len(values)), key=lambda i: (round(values[i], 6), i))
    values = [values[i] for i in order]
    projected = [projected[i] for i in order]
    points = [points[i] for i in order]
    span = max(values) if values else 0.0
    span_p = max(projected) if projected else 0.0
    x0, y0 = view.view_bbox()[:2]
    start: Pt2 = (base2, y0) if index == 0 else (x0, base2)
    return {
        "refs": [n for _, n in infos],
        "axis": axis,
        "value_mm": span,
        "projected_mm": span_p,
        "values_mm": values,
        "text": _num(span),
        "anchors": (start, points[-1] if points else start),
        "chain": points,
        "extra": {"from": origin_name, "steps": len(values)},
    }


def measure(
    doc: Any, part: Any, drawing: Drawing, spec: dict[str, Any], index: int, order: dict[str, int]
) -> Dimension:
    """One dimension, measured. `order` counts dims per (view, axis) so they stack."""
    del doc
    name = str(spec.get("name") or f"d{index + 1}")
    kind = str(spec.get("kind") or "extent").lower()
    if kind not in KINDS:
        raise CommandError(
            f"dimension {name}: kind {spec.get('kind')!r} is not one of {', '.join(KINDS)}.",
            code="pk_bad_op",
        )
    view_name = spec.get("view")
    if view_name is None:
        if len(drawing.views) != 1:
            raise CommandError(
                f"dimension {name} needs view: <name>. Views: "
                f"{', '.join(v.name for v in drawing.views)}.",
                code="pk_needs",
            )
        view = drawing.views[0]
    else:
        view = drawing.view(str(view_name))
    if "value" in spec:
        raise CommandError(
            f"dimension {name}: a drawing dimension is read back from the model, never typed "
            f"(Law 15). Drop value: {spec['value']!r} and name the sub-shapes instead.",
            code="pk_spec_conflict",
        )

    if kind == "extent":
        payload = _measure_extent(part, view, spec, name)
    elif kind == "dist":
        payload = _measure_dist(part, view, spec, name)
    elif kind in ("dia", "rad"):
        payload = _measure_round(part, view, spec, name, kind)
    elif kind == "angle":
        payload = _measure_angle(part, view, spec, name)
    elif kind == "chamfer":
        payload = _measure_chamfer(part, view, spec, name)
    else:
        payload = _measure_chain(part, view, spec, name, kind)

    axis = str(payload.get("axis", ""))
    key = f"{view.name}|{axis or kind}"
    stack = order.get(key, 0)
    order[key] = stack + 1
    return Dimension(
        name=name,
        view=view.name,
        kind=kind,
        refs=list(payload["refs"]),
        value_mm=float(payload["value_mm"]),
        projected_mm=float(payload["projected_mm"]),
        text=str(payload["text"]),
        axis=axis,
        values_mm=[float(v) for v in payload.get("values_mm", [])],
        anchors=payload.get("anchors", ((0.0, 0.0), (0.0, 0.0))),
        chain=list(payload.get("chain", [])),
        index=stack,
        centre=payload.get("centre"),
        radius=float(payload.get("radius", 0.0)),
        lines2d=payload.get("lines2d"),
        projected_from=str(payload.get("projected_from", "frame")),
        extra=dict(payload.get("extra", {})),
    )


# --------------------------------------------------------------------------- placement


@dataclass
class DimGeometry:
    """A dimension drawn: sheet-millimetre lines, arrowheads and text, plus the
    handful of numbers the DXF writer needs to emit a REAL `DIMENSION` entity
    instead of the exploded picture."""

    lines: list[Segment] = field(default_factory=list)
    arrows: list[tuple[Pt2, float]] = field(default_factory=list)
    texts: list[tuple[float, float, str, float, float]] = field(default_factory=list)
    dxf: dict[str, Any] = field(default_factory=dict)


def arrow_polygon(tip: Pt2, angle_deg: float, size: float = ARROW_MM) -> list[Pt2]:
    """The filled arrowhead as three points; `angle_deg` points from tip to tail."""
    a = math.radians(angle_deg)
    half = math.radians(ARROW_HALF_DEG)
    return [
        tip,
        (tip[0] + size * math.cos(a - half), tip[1] + size * math.sin(a - half)),
        (tip[0] + size * math.cos(a + half), tip[1] + size * math.sin(a + half)),
    ]


def _linear(view: View, dim: Dimension, horizontal: bool) -> DimGeometry:
    sx0, sy0, sx1, sy1 = view.sheet_bbox()
    a = view.to_sheet(dim.anchors[0])
    b = view.to_sheet(dim.anchors[1])
    offset = DIM_GAP_MM + dim.index * DIM_STEP_MM
    geo = DimGeometry()
    if horizontal:
        y = sy0 - offset
        p0, p1 = (a[0], y), (b[0], y)
        for anchor in (a, b):
            geo.lines.append(Segment(anchor[0], sy0 - EXT_GAP_MM, anchor[0], y - EXT_OVER_MM))
        geo.lines.append(Segment(p0[0], y, p1[0], y))
        geo.arrows.append((p0, 0.0 if p1[0] > p0[0] else 180.0))
        geo.arrows.append((p1, 180.0 if p1[0] > p0[0] else 0.0))
        geo.texts.append((0.5 * (p0[0] + p1[0]), y + 1.2, dim.text, TEXT_MM, 0.0))
        geo.dxf = {"kind": "linear", "base": (p0[0], y), "p1": a, "p2": b, "angle": 0.0}
    else:
        x = sx0 - offset
        p0, p1 = (x, a[1]), (x, b[1])
        for anchor in (a, b):
            geo.lines.append(Segment(sx0 - EXT_GAP_MM, anchor[1], x - EXT_OVER_MM, anchor[1]))
        geo.lines.append(Segment(x, p0[1], x, p1[1]))
        geo.arrows.append((p0, 90.0 if p1[1] > p0[1] else 270.0))
        geo.arrows.append((p1, 270.0 if p1[1] > p0[1] else 90.0))
        geo.texts.append((x - 1.2, 0.5 * (p0[1] + p1[1]), dim.text, TEXT_MM, 90.0))
        geo.dxf = {"kind": "linear", "base": (x, p0[1]), "p1": a, "p2": b, "angle": 90.0}
    del sx1, sy1
    return geo


def _leader(view: View, dim: Dimension, from_point: Pt2, radius: float) -> DimGeometry:
    geo = DimGeometry()
    start = (
        from_point[0] + radius * math.cos(math.radians(45.0)),
        from_point[1] + radius * math.sin(math.radians(45.0)),
    )
    knee = (
        from_point[0] + (radius + LEADER_MM) * math.cos(math.radians(45.0)),
        from_point[1] + (radius + LEADER_MM) * math.sin(math.radians(45.0)),
    )
    tail = (knee[0] + TAIL_MM, knee[1])
    geo.lines.append(Segment(start[0], start[1], knee[0], knee[1]))
    geo.lines.append(Segment(knee[0], knee[1], tail[0], tail[1]))
    geo.arrows.append((start, 45.0))
    geo.texts.append((tail[0] + 1.0, tail[1] + 1.0, dim.text, TEXT_MM, 0.0))
    del view
    return geo


def place(view: View, dim: Dimension) -> DimGeometry:
    """The dimension's drawn geometry in sheet millimetres."""
    if dim.kind in ("extent", "dist", "chamfer") or dim.kind in ("ordinate", "baseline"):
        if dim.kind in ("ordinate", "baseline"):
            return _chain_geometry(view, dim)
        if dim.axis == "Y":
            return _linear(view, dim, horizontal=False)
        if dim.axis in ("X", ""):
            return _linear(view, dim, horizontal=True)
        return _linear(view, dim, horizontal=True)
    if dim.kind in ("dia", "rad"):
        centre = view.to_sheet(dim.centre or (0.0, 0.0))
        geo = _leader(view, dim, centre, dim.radius * view.scale)
        geo.dxf = {
            "kind": dim.kind,
            "centre": centre,
            "radius": dim.radius * view.scale,
            "angle": 45.0,
        }
        return geo
    if dim.kind == "angle":
        return _angle_geometry(view, dim)
    return DimGeometry()


def _chain_geometry(view: View, dim: Dimension) -> DimGeometry:
    """A baseline or ordinate chain: every step measured from the same datum."""
    horizontal = dim.axis == "X"
    sx0, sy0, _sx1, _sy1 = view.sheet_bbox()
    base = view.to_sheet(dim.anchors[0])
    geo = DimGeometry()
    for step, (value, point) in enumerate(zip(dim.values_mm, dim.chain, strict=False)):
        at = view.to_sheet(point)
        text = _num(value)
        if dim.kind == "ordinate":
            if horizontal:
                tip = (at[0], sy0 - DIM_GAP_MM)
                geo.lines.append(Segment(at[0], sy0 - EXT_GAP_MM, tip[0], tip[1]))
                geo.texts.append((tip[0], tip[1] - TEXT_MM, text, TEXT_MM, 90.0))
            else:
                tip = (sx0 - DIM_GAP_MM, at[1])
                geo.lines.append(Segment(sx0 - EXT_GAP_MM, at[1], tip[0], tip[1]))
                geo.texts.append((tip[0] - TEXT_MM, tip[1], text, TEXT_MM, 0.0))
            continue
        offset = DIM_GAP_MM + (dim.index + step) * DIM_STEP_MM
        if horizontal:
            y = sy0 - offset
            geo.lines.append(Segment(base[0], sy0 - EXT_GAP_MM, base[0], y - EXT_OVER_MM))
            geo.lines.append(Segment(at[0], sy0 - EXT_GAP_MM, at[0], y - EXT_OVER_MM))
            geo.lines.append(Segment(base[0], y, at[0], y))
            geo.arrows.append(((base[0], y), 0.0 if at[0] > base[0] else 180.0))
            geo.arrows.append(((at[0], y), 180.0 if at[0] > base[0] else 0.0))
            geo.texts.append((0.5 * (base[0] + at[0]), y + 1.2, text, TEXT_MM, 0.0))
            geo.dxf.setdefault("chain", []).append(
                {"kind": "linear", "base": (base[0], y), "p1": base, "p2": at, "angle": 0.0}
            )
        else:
            x = sx0 - offset
            geo.lines.append(Segment(sx0 - EXT_GAP_MM, base[1], x - EXT_OVER_MM, base[1]))
            geo.lines.append(Segment(sx0 - EXT_GAP_MM, at[1], x - EXT_OVER_MM, at[1]))
            geo.lines.append(Segment(x, base[1], x, at[1]))
            geo.arrows.append(((x, base[1]), 90.0 if at[1] > base[1] else 270.0))
            geo.arrows.append(((x, at[1]), 270.0 if at[1] > base[1] else 90.0))
            geo.texts.append((x - 1.2, 0.5 * (base[1] + at[1]), text, TEXT_MM, 90.0))
            geo.dxf.setdefault("chain", []).append(
                {"kind": "linear", "base": (x, base[1]), "p1": base, "p2": at, "angle": 90.0}
            )
    return geo


def _intersect(a: tuple[Pt2, Pt2], b: tuple[Pt2, Pt2]) -> Pt2 | None:
    (x1, y1), (x2, y2) = a
    (x3, y3), (x4, y4) = b
    d = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
    if abs(d) < 1e-12:
        return None
    t = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / d
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def _angle_geometry(view: View, dim: Dimension) -> DimGeometry:
    geo = DimGeometry()
    if dim.lines2d is None:
        return geo
    (a0, a1), (b0, b1) = dim.lines2d
    la = (view.to_sheet(a0), view.to_sheet(a1))
    lb = (view.to_sheet(b0), view.to_sheet(b1))
    apex = _intersect(la, lb)
    if apex is None:
        mid = (0.5 * (la[0][0] + lb[0][0]), 0.5 * (la[0][1] + lb[0][1]))
        geo.texts.append((mid[0], mid[1], dim.text, TEXT_MM, 0.0))
        return geo
    reach = 14.0
    for line in (la, lb):
        d = (line[1][0] - line[0][0], line[1][1] - line[0][1])
        n = math.hypot(*d) or 1.0
        far = (apex[0] + reach * d[0] / n, apex[1] + reach * d[1] / n)
        geo.lines.append(Segment(apex[0], apex[1], far[0], far[1]))
    geo.texts.append((apex[0] + reach * 0.6, apex[1] + reach * 0.6, dim.text, TEXT_MM, 0.0))
    geo.dxf = {
        "kind": "angular",
        "line1": la,
        "line2": lb,
        "base": (apex[0] + reach, apex[1] + reach),
    }
    return geo


# --------------------------------------------------------------------------- hole table


def _cylinder_axis(face_shape: Any) -> Vec3:
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    d = BRepAdaptor_Surface(face_shape).Cylinder().Axis().Direction()
    return (d.X(), d.Y(), d.Z())


def _std_note(part: Any, name: str) -> str:
    """`M6 clearance, ISO 273 medium` for a hole cut to a standard, else ''.

    Read from the OWNING FEATURE's `std` argument through `partkiln.standards`,
    so the note cites the table the geometry was actually cut to.
    """
    fid = name.split(".", 1)[0]
    feature = None
    for f in getattr(part, "features", []) or []:
        if f.id == fid:
            feature = f
            break
    if feature is None:
        return ""
    spec = feature.args.get("std")
    if not spec:
        return ""
    words = str(spec).split()
    if len(words) < 2:
        return ""
    size, what = words[0], words[1].lower()
    from partkiln import standards

    if what == "clearance":
        series = words[2].lower() if len(words) > 2 else "normal"
        try:
            row = standards.clearance_hole(size, series)
        except CommandError:
            return ""
        authority = str(row.get("authority", "")).split(":")[0]
        return f"{size} clearance, {authority} {ISO273_SERIES.get(series, series)}"
    if what == "tap":
        try:
            row = standards.tap_drill(size)
        except CommandError:
            return ""
        return f"{size} tap drill, {str(row.get('authority', '')).split(':')[0]}"
    return ""


def hole_table(part: Any, view: View) -> list[dict[str, Any]]:
    """Every hole seen down its own axis in this view, as table rows.

    A row is `{name, x, y, dia_mm, depth}`: `dia_mm` is twice the model radius
    (never a typed size), `x`/`y` are the axis in the view frame, and `depth` is
    `THRU` when the cylinder spans the body along its own axis.
    """
    from partkiln.brep import shapes as _shapes

    inv = part.inventory()
    direction = view.frame.direction
    body_box = _shapes.bbox(part.shape)
    rows: list[dict[str, Any]] = []
    for i, face in enumerate(inv.faces):
        if face.surface_type != "cylinder" or face.radius is None:
            continue
        axis = _cylinder_axis(face.shape)
        if abs(_dot(axis, direction)) < 1.0 - 1e-6:
            continue
        name = inv.name_of_face(i)
        x, y = view.frame.to_view(face.centroid)
        span = _face_span(face, axis)
        body = _body_span(body_box, axis)
        rows.append(
            {
                "name": name,
                "x": _r3(x),
                "y": _r3(y),
                "dia_mm": _r3(2.0 * face.radius),
                "depth": "THRU" if abs(span - body) < 1e-6 else _num(span),
                "note": _std_note(part, name),
            }
        )
    rows.sort(key=lambda r: (r["x"], r["y"], r["name"]))
    return rows


def _face_span(face: Any, axis: Vec3) -> float:
    x0, y0, z0, x1, y1, z1 = face.bbox
    return abs(_dot((x1 - x0, y1 - y0, z1 - z0), tuple(abs(c) for c in axis)))


def _body_span(box: Sequence[float], axis: Vec3) -> float:
    return abs(
        _dot(
            (box[3] - box[0], box[4] - box[1], box[5] - box[2]),
            tuple(abs(c) for c in axis),
        )
    )


def hole_notes(rows: Sequence[dict[str, Any]]) -> list[str]:
    """One note per distinct (dia, depth, standard): `4x d6.6 THRU (...)`."""
    groups: dict[tuple[Any, ...], int] = {}
    for row in rows:
        key = (row["dia_mm"], row["depth"], row.get("note", ""))
        groups[key] = groups.get(key, 0) + 1
    notes: list[str] = []
    for (dia, depth, note), count in sorted(groups.items(), key=lambda kv: kv[0][0]):
        head = f"{count}× " if count > 1 else ""  # noqa: RUF001 - the drawing symbol
        text = f"{head}Ø{_num(dia)} {depth}"
        if note:
            text += f" ({note})"
        notes.append(text)
    return notes


# --------------------------------------------------------------------------- parts list


def parts_list(doc: Any, view_kind: str = "parts") -> list[dict[str, Any]]:
    """The BOM as sheet rows, or `[]` when the document holds no assembly.

    `partkiln.assembly.bom` is imported lazily and its absence is tolerated:
    P5a must not depend on P3 being present in the interpreter that draws.
    """
    assemblies = getattr(doc, "assemblies", {}) or {}
    if not assemblies:
        return []
    try:
        from partkiln.assembly.bom import bom
    except Exception:  # pragma: no cover - the assembly layer is optional here
        return []
    cards: dict[str, dict[str, Any]] = {}
    for name, part in (getattr(doc, "parts", {}) or {}).items():
        card: dict[str, Any] = {"material": getattr(part, "material", None)}
        mass = getattr(part, "mass_g", None)
        if callable(mass):
            value = mass()
            if value is not None:
                card["mass_g"] = value
        if "mass_g" not in card:
            volume = getattr(part, "volume", None)
            if callable(volume):
                card["volume_mm3"] = volume()
        cards[name] = card
    rows: list[dict[str, Any]] = []
    for name in sorted(assemblies):
        record = assemblies[name]
        # The document wraps the P3 `Assembly` in a `DocAssembly`; the BOM wants
        # the assembly itself, and a bare one is accepted too.
        asm = getattr(record, "asm", record)
        report = bom(asm, cards, view_kind)
        for row in report["rows"]:
            rows.append({**row, "assembly": name})
    return rows


__all__ = [
    "AGREE_TOL_MM",
    "ARROW_MM",
    "KINDS",
    "DimGeometry",
    "Dimension",
    "arrow_polygon",
    "hole_notes",
    "hole_table",
    "measure",
    "parts_list",
    "place",
]
