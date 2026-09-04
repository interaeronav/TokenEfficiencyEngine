"""Sheets, views and the layout that tells first angle from third.

The one fact a drawing lane cannot get wrong is which side of the front view
the top view lands on, so it is a table here and a test there (P5a):

    THIRD angle (ANSI): the top view is ABOVE the front, the right view is to
    the RIGHT - each view sits on the side of the front view it is seen from.
    FIRST angle (ISO, DIN): the top view is BELOW the front, the right view to
    the LEFT - each view is pushed through to the far side.

The default follows the standard and is never guessed: ISO -> first, DIN ->
first, ANSI -> third (D5, "angle follows the standard"). An explicit `angle`
wins, and the choice is echoed in `assumed` when it was not asked for.

Geometry arrives from `hlr.project` in MODEL millimetres in the view frame.
This module places it: every view gets an `origin` in sheet millimetres and a
`scale`, and `to_sheet()` maps one to the other. The scale is applied to the
COORDINATES here, not as an SVG group transform, because a group transform
would also shrink the arrowheads, the text and the line weights - a 1:2 sheet
must still carry 3.5 mm characters (ISO 3098). That is the one deliberate
deviation from the D5 sketch, and all three writers are identical because of
it.

A view block that does not fit the sheet is refused, not silently clipped
(`pk_spec_conflict`): the refusal names the smallest sheet that fits and the
scale that would fit the sheet asked for.

Nothing here imports OCP at module level; `hlr` does its OCP imports inside
its functions and `dims` does the same.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from partkiln.document import CommandError
from partkiln.drawing import hlr
from partkiln.drawing.hlr import Arc, Polyline, Prim, Projection, Pt2, Segment, ViewFrame

# --------------------------------------------------------------------------- sheets

# ISO 216 landscape sheets in millimetres, plus the one ANSI size D5 names.
# ANSI B is 11 x 17 in = 279.4 x 431.8 mm, landscape 431.8 x 279.4.
SHEETS: dict[str, tuple[float, float]] = {
    "A4L": (297.0, 210.0),
    "A3L": (420.0, 297.0),
    "A2L": (594.0, 420.0),
    "A1L": (841.0, 594.0),
    "A0L": (1189.0, 841.0),
    "ANSI_B": (431.8, 279.4),
}
SHEET_ORDER = ("A4L", "ANSI_B", "A3L", "A2L", "A1L", "A0L")

STANDARDS = ("ISO", "ANSI", "DIN")
ANGLES = ("first", "third")
ANGLE_FOR_STANDARD = {"ISO": "first", "DIN": "first", "ANSI": "third"}

MARGIN_MM = 10.0
GAP_MM = 18.0
TITLE_W_MM = 90.0
TITLE_H_MM = 32.0
TEXT_MM = 3.5  # ISO 3098 character height
LABEL_MM = 5.0
HATCH_PITCH_MM = 3.0
# Room reserved below and left of the view block for the dimension lines that
# hang there (dims.DIM_GAP_MM plus two stacked steps plus the text).
DIM_APRON_MM = 32.0

# The six orthographic directions as (part -> eye, sheet up). `up` is chosen so
# the sheet's horizontal is world +X wherever that is possible, which is what
# makes the top view sit square under the front view.
DIRECTIONS: dict[str, tuple[tuple[float, float, float], tuple[float, float, float]]] = {
    "front": ((0.0, -1.0, 0.0), (0.0, 0.0, 1.0)),
    "back": ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    "top": ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
    "bottom": ((0.0, 0.0, -1.0), (0.0, -1.0, 0.0)),
    "right": ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    "left": ((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    "iso": ((1.0, -1.0, 1.0), (0.0, 0.0, 1.0)),
}

# The projection-angle table. Columns grow to the right, rows upward.
THIRD_SLOTS: dict[str, tuple[int, int]] = {
    "front": (0, 0),
    "top": (0, 1),
    "bottom": (0, -1),
    "right": (1, 0),
    "left": (-1, 0),
    "back": (2, 0),
    "iso": (1, 1),
}
FIRST_SLOTS: dict[str, tuple[int, int]] = {
    "front": (0, 0),
    "top": (0, -1),
    "bottom": (0, 1),
    "right": (-1, 0),
    "left": (1, 0),
    "back": (-2, 0),
    "iso": (1, 1),
}


@dataclass(frozen=True)
class Sheet:
    """One sheet: size in millimetres and the area the views may use."""

    name: str
    width: float
    height: float
    margin: float = MARGIN_MM

    @property
    def area(self) -> tuple[float, float, float, float]:
        """(x0, y0, x1, y1) of the usable area, y up, the title block reserved."""
        return (
            self.margin,
            self.margin + TITLE_H_MM,
            self.width - self.margin,
            self.height - self.margin,
        )


def sheet_named(name: Any) -> Sheet:
    key = str(name or "A4L").upper().replace("-", "_")
    if key not in SHEETS:
        raise CommandError(
            f"sheet {name!r} is not a size partkiln draws. Sizes: {', '.join(SHEETS)}.",
            code="pk_needs",
        )
    w, h = SHEETS[key]
    return Sheet(key, w, h)


def standard_named(value: Any, fallback: str = "ISO") -> str:
    key = str(value or fallback).upper()
    if key not in STANDARDS:
        raise CommandError(
            f"standard {value!r} is not one of {', '.join(STANDARDS)}.", code="pk_needs"
        )
    return key


def angle_for(standard: str) -> str:
    """ISO and DIN draw first angle, ANSI draws third (D5)."""
    return ANGLE_FOR_STANDARD[standard]


def parse_scale(value: Any) -> float:
    """`2`, `0.5`, `"1:2"`, `"2:1"` -> the multiplier applied to model mm."""
    if value is None:
        return 1.0
    if isinstance(value, int | float) and not isinstance(value, bool):
        scale = float(value)
    else:
        text = str(value).strip()
        if ":" in text:
            a, _, b = text.partition(":")
            try:
                num, den = float(a), float(b)
            except ValueError as exc:
                raise CommandError(
                    f"scale {value!r} is not a ratio. Forms: 2, 0.5, '1:2', '2:1'.",
                    code="pk_needs",
                ) from exc
            if den == 0:
                raise CommandError("scale 'n:0' divides by zero.", code="pk_needs")
            scale = num / den
        else:
            try:
                scale = float(text)
            except ValueError as exc:
                raise CommandError(
                    f"scale {value!r} is not a number or a ratio like '1:2'.", code="pk_needs"
                ) from exc
    if scale <= 0:
        raise CommandError(f"scale must be > 0, got {scale:g}.", code="pk_needs")
    return scale


def scale_text(scale: float) -> str:
    """`1.0 -> '1:1'`, `2.0 -> '2:1'`, `0.5 -> '1:2'` - the ratio a title block prints."""
    if abs(scale - 1.0) < 1e-9:
        return "1:1"
    if scale > 1.0:
        return f"{_ratio(scale)}:1"
    return f"1:{_ratio(1.0 / scale)}"


def _ratio(v: float) -> str:
    return f"{v:g}" if abs(v - round(v)) > 1e-9 else str(round(v))


# --------------------------------------------------------------------------- views


@dataclass
class View:
    """One projection placed on the sheet.

    `origin` is where view-millimetre (0, 0) lands in sheet millimetres and
    `scale` multiplies model millimetres, so `to_sheet` is the only mapping
    the writers need. `dir_token` is the orthographic name ('front', 'top',
    ...) or '' for a section / detail / auxiliary view, which is what the
    angle table keys on.
    """

    name: str
    kind: str  # base | section | detail | aux
    label: str
    dir_token: str
    frame: ViewFrame
    projection: Projection
    scale: float = 1.0
    origin: tuple[float, float] = (0.0, 0.0)
    slot: tuple[int, int] = (0, 0)
    hatch: list[Segment] = field(default_factory=list)
    hatch_area_mm2: float = 0.0
    hatch_faces: int = 0
    window: tuple[float, float, float] | None = None  # cx, cy, r in SOURCE view mm
    source: str = ""
    plane: dict[str, Any] | None = None

    # -- geometry ---------------------------------------------------------

    @property
    def visible(self) -> list[Prim]:
        return self.projection.visible

    @property
    def hidden(self) -> list[Prim]:
        return self.projection.hidden

    @property
    def visible_edges(self) -> int:
        return self.projection.visible_edges

    @property
    def hidden_edges(self) -> int:
        return self.projection.hidden_edges

    def view_bbox(self) -> tuple[float, float, float, float]:
        box = hlr.prim_bbox([*self.visible, *self.hidden, *self.hatch])
        return (0.0, 0.0, 0.0, 0.0) if box is None else box

    def size(self) -> tuple[float, float]:
        x0, y0, x1, y1 = self.view_bbox()
        return ((x1 - x0) * self.scale, (y1 - y0) * self.scale)

    def to_sheet(self, point: Sequence[float]) -> Pt2:
        return (
            self.origin[0] + self.scale * float(point[0]),
            self.origin[1] + self.scale * float(point[1]),
        )

    def sheet_bbox(self) -> tuple[float, float, float, float]:
        x0, y0, x1, y1 = self.view_bbox()
        a = self.to_sheet((x0, y0))
        b = self.to_sheet((x1, y1))
        return (a[0], a[1], b[0], b[1])

    def sheet_prims(self, prims: Sequence[Prim]) -> list[Prim]:
        return [map_prim(p, self.origin, self.scale) for p in prims]

    def summary(self) -> dict[str, Any]:
        """The D7 `vw:` row - scalars only."""
        out: dict[str, Any] = {
            "id": f"vw:{self.name}",
            "kind": "view",
            "dir": self.label,
            "scale": round(self.scale, 6) + 0.0,
            "visible_edges": self.visible_edges,
            "hidden_edges": self.hidden_edges,
        }
        if self.kind != "base":
            out["view"] = self.kind
        if self.hatch_faces:
            out["hatch_area_mm2"] = round(self.hatch_area_mm2, 3) + 0.0
            out["hatch_faces"] = self.hatch_faces
        if self.source:
            out["of"] = self.source
        return out


def map_prim(prim: Prim, origin: Sequence[float], scale: float) -> Prim:
    """One primitive from view millimetres into sheet millimetres.

    The map is a uniform scale plus a translation, so an arc stays an arc
    (radius scales, angles do not) and no curve has to be re-sampled.
    """
    ox, oy = float(origin[0]), float(origin[1])
    if isinstance(prim, Segment):
        return Segment(
            ox + scale * prim.x0,
            oy + scale * prim.y0,
            ox + scale * prim.x1,
            oy + scale * prim.y1,
        )
    if isinstance(prim, Arc):
        return Arc(ox + scale * prim.cx, oy + scale * prim.cy, scale * prim.r, prim.a0, prim.a1)
    return Polyline(tuple((ox + scale * x, oy + scale * y) for x, y in prim.points))


# --------------------------------------------------------------------------- the drawing


@dataclass
class Drawing:
    """A sheet, its views, its dimensions and the files it was written to."""

    name: str
    sheet: Sheet
    standard: str
    angle: str
    scale: float
    part: str = ""
    views: list[View] = field(default_factory=list)
    dims: list[Any] = field(default_factory=list)  # dims.Dimension
    holes: list[dict[str, Any]] = field(default_factory=list)
    holes_shown: int = 0
    parts: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    title: dict[str, Any] = field(default_factory=dict)
    files: dict[str, str] = field(default_factory=dict)
    assumed: dict[str, Any] = field(default_factory=dict)

    def view(self, name: str) -> View:
        for v in self.views:
            if v.name == name:
                return v
        known = ", ".join(v.name for v in self.views) or "(none)"
        raise CommandError(
            f"no view {name!r} on drawing {self.name}. Views: {known}.", code="pk_ref_unknown"
        )

    def summary(self) -> dict[str, Any]:
        """The D7 `dwg:` row - scalars only, never geometry (hard rule 1)."""
        return {
            "id": f"dwg:{self.name}",
            "kind": "drawing",
            "of": self.part,
            "sheet": self.sheet.name,
            "standard": self.standard,
            "angle": self.angle,
            "scale": scale_text(self.scale),
            "views": len(self.views),
            "dims": len(self.dims),
            "holes": len(self.holes),
            "parts": len(self.parts),
            "files": dict(self.files),
        }

    def rows(self) -> list[dict[str, Any]]:
        """`dwg:` then every `vw:` then every `dim:` - what `entities()` lists."""
        out = [self.summary()]
        out.extend(v.summary() for v in self.views)
        out.extend(d.summary() for d in self.dims)
        return out

    # `Document.entities()` asks a container entry for its own D7 rows under
    # this name and owns nothing else about them (document.py `_container_rows`).
    entity_rows = rows

    def detail(self, entity_id: str | None = None) -> dict[str, Any]:
        """The opt-in detail for this sheet, one of its views, or one dimension.

        `Document.detail(id)` walks every container entry offering it the id and
        keeps the first non-empty answer, so an id this drawing does not own
        answers `{}` rather than raising.
        """
        if entity_id not in (None, "dwg", f"dwg:{self.name}"):
            for view in self.views:
                if entity_id == f"vw:{view.name}":
                    row = view.summary()
                    row["drawing"] = f"dwg:{self.name}"
                    row["frame"] = view.frame.as_dict()
                    if view.plane is not None:
                        row["plane"] = dict(view.plane)
                    return row
            for dim in self.dims:
                if entity_id == f"dim:{dim.name}":
                    return {**dim.row(), "drawing": f"dwg:{self.name}"}
            return {}
        out = self.summary()
        out["view_rows"] = [v.summary() for v in self.views]
        out["dimensions"] = [d.row() for d in self.dims]
        if self.holes:
            out["hole_table"] = list(self.holes)
        if self.parts:
            out["parts_list"] = list(self.parts)
        if self.notes:
            out["notes"] = list(self.notes)
        if self.title:
            out["title"] = dict(self.title)
        return out


# --------------------------------------------------------------------------- building


def part_named(doc: Any, ref: Any) -> tuple[Any, str]:
    """The part named by `of`, or the only part when there is exactly one."""
    parts = getattr(doc, "parts", {}) or {}
    bodied = [n for n in sorted(parts) if getattr(parts[n], "shape", None) is not None]
    if ref is None:
        if len(bodied) == 1:
            return parts[bodied[0]], bodied[0]
        raise CommandError(
            f"a drawing needs of: <part>. Parts with a body: {', '.join(bodied) or '(none)'}.",
            code="pk_needs",
        )
    name = str(ref).split(":", 1)[-1]
    part = parts.get(name)
    if part is None or getattr(part, "shape", None) is None:
        raise CommandError(
            f"of {ref!r} is not a part with a body. Parts with a body: "
            f"{', '.join(bodied) or '(none)'}.",
            code="pk_ref_unknown",
        )
    return part, name


def _plane_from_token(part: Any, doc: Any, token: str) -> tuple[tuple[float, float, float], ...]:
    """`x=50` / `y=-3.5` / `z=0` / a datum plane name -> (point, normal)."""
    text = token.strip()
    if "=" in text:
        axis, _, value = text.partition("=")
        axis = axis.strip().lower()
        if axis not in ("x", "y", "z"):
            raise CommandError(
                f"section plane {token!r}: the axis is x, y or z, not {axis!r}.", code="pk_needs"
            )
        try:
            at = float(value)
        except ValueError as exc:
            raise CommandError(
                f"section plane {token!r}: {value!r} is not a number of millimetres.",
                code="pk_needs",
            ) from exc
        index = "xyz".index(axis)
        point = [0.0, 0.0, 0.0]
        point[index] = at
        normal = [0.0, 0.0, 0.0]
        normal[index] = 1.0
        return (tuple(point), tuple(normal))  # type: ignore[return-value]
    datums = getattr(doc, "datums", {}) or {}
    datum = datums.get(text)
    if datum is not None and getattr(datum, "kind", "") == "plane":
        return (tuple(datum.origin), tuple(datum.direction))  # type: ignore[return-value]
    from partkiln import naming

    res = naming.resolve(part, text, "face", "one")
    face = res.infos[0]
    if face.surface_type != "plane" or face.normal is None:
        raise CommandError(
            f"section plane {token!r} is a {face.surface_type} face; a section needs a plane. "
            "Fix: name a planar face, a datum plane, or write x=<mm>.",
            code="pk_plane_mismatch",
        )
    return (tuple(face.centroid), tuple(face.normal))  # type: ignore[return-value]


def _face_direction(part: Any, ref: str) -> tuple[tuple[float, float, float], str]:
    from partkiln import naming

    res = naming.resolve(part, ref, "face", "one")
    face = res.infos[0]
    if face.normal is None:
        raise CommandError(
            f"aux view {ref!r}: that face has no single normal ({face.surface_type}). "
            "Fix: name a planar face.",
            code="pk_plane_mismatch",
        )
    return (tuple(face.normal), res.names[0])  # type: ignore[return-value]


def resolve_centre(part: Any, ref: str) -> tuple[float, float, float]:
    """The 3D centre of one named sub-shape.

    A hole instance is written `h.1` on the wire while the kernel names its wall
    `h.1.wall`, so the bare instance is retried with the role appended before
    anything is refused (the same courtesy `dims._resolve` extends).
    """
    from partkiln import naming

    first: CommandError | None = None
    for candidate in (ref, f"{ref}.wall"):
        for kind in ("face", "edge"):
            try:
                res = naming.resolve(part, candidate, kind, "one")
            except CommandError as exc:
                first = first or exc
                continue
            info = res.infos[0]
            centre = getattr(info, "centroid", None) or info.midpoint
            return (float(centre[0]), float(centre[1]), float(centre[2]))
    raise first if first is not None else CommandError(f"{ref} names nothing.")


def _up_for(direction: Sequence[float]) -> tuple[float, float, float]:
    """World +Z on the sheet, unless the line of sight is along it (then +Y)."""
    if abs(float(direction[2])) > 1.0 - 1e-6:
        return (0.0, 1.0, 0.0) if float(direction[2]) > 0 else (0.0, -1.0, 0.0)
    return (0.0, 0.0, 1.0)


def _build_view(
    doc: Any,
    part: Any,
    spec: dict[str, Any],
    index: int,
    scale: float,
    built: dict[str, View],
    assumed: dict[str, Any],
) -> View:
    name = str(spec.get("name") or f"v{index + 1}")
    raw = spec.get("dir", "front")
    view_scale = parse_scale(spec["scale"]) if spec.get("scale") is not None else scale

    if isinstance(raw, dict):
        keys = [k for k in ("detail", "section", "aux") if k in raw]
        if len(keys) != 1:
            raise CommandError(
                f"view {name}: dir is one of detail / section / aux, got "
                f"{sorted(raw) or 'nothing'}.",
                code="pk_needs",
            )
        kind, payload = keys[0], raw[keys[0]]
    else:
        token = str(raw).strip()
        head, sep, rest = token.partition(":")
        if sep and head in ("section", "aux", "detail"):
            kind, payload = head, rest.strip()
        else:
            kind, payload = "base", token

    if kind == "base":
        token = str(payload).lower()
        if token not in DIRECTIONS:
            raise CommandError(
                f"view {name}: dir {payload!r} is not a direction. Directions: "
                f"{', '.join(sorted(DIRECTIONS))}; or section:<plane>, detail:{{of, r}}, "
                "aux:<face>.",
                code="pk_needs",
            )
        direction, up = DIRECTIONS[token]
        frame = hlr.view_frame(direction, up)
        return View(
            name, "base", token, token, frame, hlr.project(part.shape, direction, up), view_scale
        )

    if kind == "aux":
        ref = payload if isinstance(payload, str) else str((payload or {}).get("of", ""))
        direction, resolved = _face_direction(part, ref)
        up = _up_for(direction)
        frame = hlr.view_frame(direction, up)
        return View(
            name,
            "aux",
            f"AUX {resolved}",
            "",
            frame,
            hlr.project(part.shape, direction, up),
            view_scale,
            source=resolved,
        )

    if kind == "section":
        token = payload if isinstance(payload, str) else str((payload or {}).get("plane", ""))
        look = (payload or {}).get("dir") if isinstance(payload, dict) else None
        point, normal = _plane_from_token(part, doc, token)
        body, faces = hlr.section_body(part.shape, point, normal)
        if look is not None and str(look).lower() in DIRECTIONS:
            direction, up = DIRECTIONS[str(look).lower()]
        else:
            # The section is read looking ALONG the cut plane's normal, from the
            # side that was kept: the removed half is the +normal half, so the
            # eye sits at +normal.
            direction = (normal[0], normal[1], normal[2])
            up = _up_for(direction)
            assumed.setdefault(f"{name}.dir", "along the section normal")
        frame = hlr.view_frame(direction, up)
        projection = hlr.project(body, direction, up)
        rings = [hlr.face_rings(f.shape, frame) for f in faces]
        marks = hlr.hatch(rings, HATCH_PITCH_MM / max(view_scale, 1e-9))
        return View(
            name,
            "section",
            f"SECTION {token}",
            "",
            frame,
            projection,
            view_scale,
            hatch=marks,
            hatch_area_mm2=round(sum(f.area for f in faces), 3) + 0.0,
            hatch_faces=len(faces),
            plane={
                "point": [round(c, 3) + 0.0 for c in point],
                "normal": [round(c, 3) + 0.0 for c in normal],
            },
        )

    # detail
    if not isinstance(payload, dict):
        raise CommandError(
            f"view {name}: detail is {{of: <view>, r: <mm>, scale: <n>, at | on}}.",
            code="pk_needs",
        )
    source_name = str(payload.get("of") or "")
    source = built.get(source_name)
    if source is None:
        known = ", ".join(built) or "(none)"
        raise CommandError(
            f"detail {name}: of {source_name!r} is not a view declared before it. Views so far: "
            f"{known}.",
            code="pk_ref_unknown",
        )
    if payload.get("r") is None:
        raise CommandError(f"detail {name} needs r: <mm>, the window radius.", code="pk_needs")
    radius = float(payload["r"])
    if radius <= 0:
        raise CommandError(f"detail {name}: r must be > 0 mm, got {radius:g}.", code="pk_needs")
    detail_scale = parse_scale(payload.get("scale", 2))
    if payload.get("scale") is None:
        assumed.setdefault(f"{name}.scale", "2:1")
    if payload.get("at") is not None:
        at = payload["at"]
        centre = (float(at[0]), float(at[1]))
    elif payload.get("on") is not None:
        centre = source.frame.to_view(resolve_centre(part, str(payload["on"])))
    else:
        x0, y0, x1, y1 = source.view_bbox()
        centre = (0.5 * (x0 + x1), 0.5 * (y0 + y1))
        assumed.setdefault(f"{name}.at", "the centre of the source view")
    cx, cy = centre
    visible = hlr.clip_to_circle(source.visible, cx, cy, radius)
    hidden = hlr.clip_to_circle(source.hidden, cx, cy, radius)
    projection = Projection(
        source.frame,
        [map_prim(p, (-cx, -cy), 1.0) for p in visible],
        [map_prim(p, (-cx, -cy), 1.0) for p in hidden],
        {**{k: 0 for k in hlr.VISIBLE_COMPOUNDS + hlr.HIDDEN_COMPOUNDS}},
        0.0,
    )
    projection.compounds["VCompound"] = len(visible)
    projection.compounds["HCompound"] = len(hidden)
    source.window = (cx, cy, radius)
    return View(
        name,
        "detail",
        f"DETAIL {name.upper()} ({scale_text(detail_scale)})",
        "",
        source.frame,
        projection,
        detail_scale,
        window=(0.0, 0.0, radius),
        source=source_name,
    )


def layout(views: Sequence[View], angle: str, sheet: Sheet) -> None:
    """Place every view: the angle table first, then a grid, then centred.

    Views the angle table does not name (sections, details, auxiliaries, and
    any duplicate of an orthographic direction) go into fresh columns to the
    right of the block, in declaration order, so the layout is a pure
    function of the view list (rule 7).
    """
    if not views:
        return
    table = THIRD_SLOTS if angle == "third" else FIRST_SLOTS
    slots: dict[str, tuple[int, int]] = {}
    extras: list[View] = []
    for v in views:
        slot = table.get(v.dir_token)
        if slot is None or slot in slots.values():
            extras.append(v)
        else:
            slots[v.name] = slot
    next_col = max((c for c, _ in slots.values()), default=-1) + 1
    for i, v in enumerate(extras):
        slots[v.name] = (next_col + i, 0)
    for v in views:
        v.slot = slots[v.name]

    widths: dict[int, float] = {}
    heights: dict[int, float] = {}
    for v in views:
        w, h = v.size()
        c, r = v.slot
        widths[c] = max(widths.get(c, 0.0), w)
        heights[r] = max(heights.get(r, 0.0), h)
    x_of: dict[int, float] = {}
    cursor = 0.0
    for c in sorted(widths):
        x_of[c] = cursor + 0.5 * widths[c]
        cursor += widths[c] + GAP_MM
    block_w = max(cursor - GAP_MM, 0.0)
    y_of: dict[int, float] = {}
    cursor = 0.0
    for r in sorted(heights):
        y_of[r] = cursor + 0.5 * heights[r]
        cursor += heights[r] + GAP_MM
    block_h = max(cursor - GAP_MM, 0.0)

    ax0, ay0, ax1, ay1 = sheet.area
    area_w, area_h = ax1 - ax0, ay1 - ay0
    # Dimensions hang below and to the left of their view (dims.place), so the
    # block is padded on those two sides and the fit is judged on the padded
    # size - otherwise the first dimension of a snug sheet lands in the margin.
    need_w, need_h = block_w + DIM_APRON_MM, block_h + DIM_APRON_MM
    if need_w > area_w + 1e-6 or need_h > area_h + 1e-6:
        raise CommandError(
            f"the views need {need_w:.1f} x {need_h:.1f} mm (dimension apron included) but sheet "
            f"{sheet.name} offers {area_w:.1f} x {area_h:.1f} mm. Fix: "
            f"sheet: '{_fits(need_w, need_h)}', or "
            f"scale: '{_scale_that_fits(need_w, need_h, area_w, area_h)}'.",
            code="pk_spec_conflict",
        )
    dx = ax0 + DIM_APRON_MM + 0.5 * (area_w - need_w)
    dy = ay0 + DIM_APRON_MM + 0.5 * (area_h - need_h)
    for v in views:
        c, r = v.slot
        bx0, by0, bx1, by1 = v.view_bbox()
        cx = dx + x_of[c]
        cy = dy + y_of[r]
        v.origin = (
            cx - v.scale * 0.5 * (bx0 + bx1),
            cy - v.scale * 0.5 * (by0 + by1),
        )


def _fits(w: float, h: float) -> str:
    for name in SHEET_ORDER:
        sw, sh = SHEETS[name]
        if sw - 2 * MARGIN_MM >= w and sh - 2 * MARGIN_MM - TITLE_H_MM >= h:
            return name
    return "A0L"


def _scale_that_fits(w: float, h: float, area_w: float, area_h: float) -> str:
    factor = min(area_w / w if w > 0 else 1.0, area_h / h if h > 0 else 1.0)
    for den in (1, 2, 2.5, 5, 10, 20, 50, 100):
        if 1.0 / den <= factor:
            return f"1:{_ratio(float(den))}"
    return "1:100"


def build_views(
    doc: Any,
    part: Any,
    specs: Sequence[Any],
    scale: float,
    assumed: dict[str, Any],
) -> list[View]:
    """Every view in declaration order; a detail may only cite a view before it."""
    if not specs:
        specs = [{"name": "front", "dir": "front"}]
        assumed.setdefault("views", "one front view")
    built: dict[str, View] = {}
    out: list[View] = []
    for i, raw in enumerate(specs):
        spec = {"dir": raw} if isinstance(raw, str) else dict(raw or {})
        view = _build_view(doc, part, spec, i, scale, built, assumed)
        if view.name in built:
            raise CommandError(
                f"two views are named {view.name!r}; view names are unique on a sheet.",
                code="pk_spec_conflict",
            )
        built[view.name] = view
        out.append(view)
    return out


# --------------------------------------------------------------------------- sheet furniture


def frame_lines(sheet: Sheet) -> list[Segment]:
    """The border and the title-block box, in sheet millimetres (y up)."""
    m = sheet.margin
    w, h = sheet.width, sheet.height
    x0, y0, x1, y1 = m, m, w - m, h - m
    tx = x1 - TITLE_W_MM
    ty = y0 + TITLE_H_MM
    return [
        Segment(x0, y0, x1, y0),
        Segment(x1, y0, x1, y1),
        Segment(x1, y1, x0, y1),
        Segment(x0, y1, x0, y0),
        Segment(tx, y0, tx, ty),
        Segment(tx, ty, x1, ty),
        Segment(tx, ty - 8.0, x1, ty - 8.0),
        Segment(tx, ty - 16.0, x1, ty - 16.0),
    ]


def title_lines(drawing: Drawing) -> list[tuple[float, float, str, float]]:
    """(x, y, text, mm) for the title block: part, rev, scale, angle, standard."""
    sheet = drawing.sheet
    x = sheet.width - sheet.margin - TITLE_W_MM + 3.0
    y = sheet.margin + TITLE_H_MM
    title = drawing.title or {}
    part = str(title.get("part") or drawing.part or drawing.name).upper()
    rows = [
        (y - 5.5, part, LABEL_MM),
        (y - 12.5, f"REV {title.get('rev', '-')}   SCALE {scale_text(drawing.scale)}", TEXT_MM),
        (
            y - 20.5,
            f"{drawing.standard}   {drawing.angle.upper()} ANGLE   mm",
            TEXT_MM,
        ),
    ]
    extra = [f"{k.upper()} {v}" for k, v in sorted(title.items()) if k not in ("part", "rev")]
    if extra:
        rows.append((y - 27.5, "   ".join(extra)[:44], TEXT_MM))
    return [(x, ry, text, size) for ry, text, size in rows]


def projection_symbol(drawing: Drawing) -> list[Prim]:
    """The truncated-cone symbol, drawn so first and third angle differ on sight.

    Two concentric circles and the cone's outline: in FIRST angle the small
    circle is to the right of the large one, in THIRD angle to the left - the
    ISO 128 symbol, and the cheapest visual check that the sheet says what it
    means.
    """
    sheet = drawing.sheet
    cx = sheet.width - sheet.margin - TITLE_W_MM - 22.0
    cy = sheet.margin + 12.0
    big, small = 6.0, 3.6
    sign = 1.0 if drawing.angle == "first" else -1.0
    lx = cx - sign * 9.0
    sx = cx + sign * 9.0
    out: list[Prim] = [
        Arc(lx, cy, big, 0.0, 360.0),
        Arc(sx, cy, small, 0.0, 360.0),
        Segment(lx, cy + big, sx, cy + small),
        Segment(lx, cy - big, sx, cy - small),
    ]
    return out
