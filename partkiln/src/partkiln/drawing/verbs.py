"""`create drawing` on the wire, and `pk_drawing` on the kernel.

Importing this module registers both, the way P2's features and P3's assemblies
register themselves (`document.register_verb` / `register_kind`,
`client.register_method`): nothing in `document.py` knows this package exists,
and `import partkiln` still costs no OCP.

The split between the two doors is deliberate:

  `create drawing` is a COMMAND. It computes views and dimensions, stores the
  `Drawing` in `doc.drawings[name]` so `entities()` can list `dwg:` / `vw:` /
  `dim:` rows, and lands in the script - a replay rebuilds the same sheet.
  It writes NO files: a command that touches the disk cannot be replayed
  safely.

  `pk_drawing` (the `drawing` kernel method) WRITES the files. It renders a
  stored drawing, or builds one on the spot from `of` / `views` / `dims` for a
  caller that only wants the sheet. The ad-hoc one is deliberately NOT stored:
  a drawing that never entered the history would vanish at the next `regen()`
  and the fingerprint would be a lie (Law 16 - the checkpoint is the script).

D5's shape, in full: `of`, `sheet A4L..A0L|ANSI_B`, `standard ISO|ANSI|DIN`,
`angle first|third` (default follows the standard), `scale`, `views`, `dims`,
`hole_table`, `parts_list`, `title`.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from partkiln.client import LocalKernel, register_method
from partkiln.document import CommandError, Document, register_kind
from partkiln.drawing import dims as _dims
from partkiln.drawing import views as _views
from partkiln.drawing.views import Drawing

FORMATS = ("svg", "dxf", "pdf")
# How many hole-table rows fit beside the views before the sheet becomes a
# spreadsheet. The FULL table always reaches the caller; only the picture is cut.
MAX_TABLE_ROWS = 26


def build_drawing(doc: Any, name: str, props: dict[str, Any]) -> Drawing:
    """Compose one sheet: views projected, dimensions measured, tables read."""
    assumed: dict[str, Any] = {}
    part, part_name = _views.part_named(doc, props.get("of"))
    sheet = _views.sheet_named(props.get("sheet"))
    if props.get("sheet") is None:
        assumed["sheet"] = sheet.name
    standard = _views.standard_named(props.get("standard"), getattr(doc, "standard", "ISO"))
    if props.get("standard") is None:
        assumed["standard"] = standard
    if props.get("angle") is None:
        angle = _views.angle_for(standard)
        assumed["angle"] = f"{angle} ({standard})"
    else:
        angle = str(props["angle"]).lower()
        if angle not in _views.ANGLES:
            raise CommandError(f"angle {props['angle']!r} is 'first' or 'third'.", code="pk_needs")
    scale = _views.parse_scale(props.get("scale"))
    if props.get("scale") is None:
        assumed["scale"] = "1:1"

    view_specs = props.get("views") or []
    if not isinstance(view_specs, list | tuple):
        raise CommandError("views is a list of {name, dir} objects.", code="pk_needs")
    built = _views.build_views(doc, part, view_specs, scale, assumed)
    _views.layout(built, angle, sheet)

    drawing = Drawing(
        name=name,
        sheet=sheet,
        standard=standard,
        angle=angle,
        scale=scale,
        part=part_name,
        views=built,
        title=dict(props.get("title") or {}),
        assumed=assumed,
    )

    dim_specs = props.get("dims") or []
    if not isinstance(dim_specs, list | tuple):
        raise CommandError("dims is a list of {name, view, kind, ...} objects.", code="pk_needs")
    order: dict[str, int] = {}
    seen: set[str] = set()
    for i, raw in enumerate(dim_specs):
        if not isinstance(raw, dict):
            raise CommandError(
                f"dims[{i}] is {raw!r}; a dimension is an object {{name, view, kind, ...}}.",
                code="pk_needs",
            )
        dim = _dims.measure(doc, part, drawing, dict(raw), i, order)
        if dim.name in seen:
            raise CommandError(
                f"two dimensions are named {dim.name!r}; names are unique on a sheet.",
                code="pk_spec_conflict",
            )
        seen.add(dim.name)
        drawing.dims.append(dim)

    if props.get("hole_table"):
        source = props.get("hole_table")
        # A hole only tables in the view that looks down its axis, so a bare
        # `hole_table: true` takes the first view that yields rows (declaration
        # order, so it is a function of the spec) and says which one it used.
        candidates = [drawing.view(str(source))] if isinstance(source, str) else list(drawing.views)
        used = candidates[0]
        for candidate in candidates:
            rows = _dims.hole_table(part, candidate)
            if rows:
                used, drawing.holes = candidate, rows
                break
        if not isinstance(source, str):
            assumed["hole_table"] = f"read from view {used.name}"
        drawing.holes_shown = min(len(drawing.holes), MAX_TABLE_ROWS)
        if drawing.holes:
            drawing.notes.extend(_dims.hole_notes(drawing.holes))
        else:
            # Two silences reach here and this note cannot tell them apart:
            # a hole exists but no view looks down its axis, OR nothing in the
            # part is a hole. Until 2026-09-04 it asserted the first, so a
            # filleted pocket - viewed down its corner axes already - was told
            # to add a view that would never find anything. It says both.
            drawing.notes.append(
                "hole table: nothing tabled as a hole - either no view looks down a hole "
                "axis, or this part's cylinders are fillets and corner radii, not holes"
            )
    if props.get("parts_list"):
        drawing.parts = _dims.parts_list(doc)
        if not drawing.parts:
            drawing.notes.append("parts list: this document holds no assembly")
    disagree = [d.name for d in drawing.dims if not d.agree]
    if disagree:
        drawing.notes.append(
            "dimensions whose drawn geometry disagrees with the model: " + ", ".join(disagree)
        )
    return drawing


@register_kind("drawing")
def _k_drawing(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
    name = doc.new_name(args, "drawing", doc.drawings)
    props = {k: v for k, v in args.items() if k not in ("kind", "name", "id")}
    drawing = build_drawing(doc, name, props)
    doc.drawings[name] = drawing
    assumed.update(drawing.assumed)
    out = drawing.summary()
    out["view_rows"] = [v.summary() for v in drawing.views]
    out["dimensions"] = [
        {
            "name": d.name,
            "value_mm": round(d.value_mm, 3) + 0.0,
            "projected_mm": round(d.projected_mm, 3) + 0.0,
            "agree": d.agree,
        }
        for d in drawing.dims
    ]
    if drawing.notes:
        out["notes"] = list(drawing.notes)
    out.pop("files", None)
    return out


# --------------------------------------------------------------------------- pk_drawing


def _formats(raw: Any) -> list[str]:
    if raw is None:
        return ["svg"]
    values = [raw] if isinstance(raw, str) else list(raw)
    out: list[str] = []
    for value in values:
        key = str(value).lower().lstrip(".")
        if key not in FORMATS:
            raise CommandError(
                f"format {value!r} is not one partkiln draws. Formats: {', '.join(FORMATS)}.",
                code="pk_needs",
            )
        if key not in out:
            out.append(key)
    return out


def write_files(
    drawing: Drawing, formats: Sequence[str], out_dir: str | Path, stem: str = ""
) -> dict[str, str]:
    """Write the sheet in each format; the paths land on `drawing.files`.

    The format list is validated HERE as well as on the wire, so a caller that
    reaches this function directly gets the same refusal naming the three
    formats rather than a file with a misleading extension.
    """
    folder = Path(out_dir)
    folder.mkdir(parents=True, exist_ok=True)
    base = stem or drawing.name
    written: dict[str, str] = {}
    for fmt in _formats(list(formats)):
        target = folder / f"{base}.{fmt}"
        if fmt == "svg":
            from partkiln.drawing import svg

            svg.write(drawing, target)
        elif fmt == "dxf":
            from partkiln.drawing import dxf

            dxf.write(drawing, target)
        else:
            from partkiln.drawing import pdf

            pdf.write(drawing, target)
        written[fmt] = str(target)
    drawing.files.update(written)
    return written


@register_method("drawing")
def _m_drawing(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    """`pk_drawing`: render a sheet to SVG / DXF / PDF and answer with numbers.

    `{of, views, dims, formats, out_dir, name}` in; `{files, dimensions, views}`
    out, plus the sheet's scalars, the hole table and the parts list when they
    were asked for. Files are written only when `out_dir` is given - a caller
    that only wants the read-back numbers pays for no disk.
    """
    doc = kernel.document
    name = str(params.get("name") or "sheet1")
    stored = (getattr(doc, "drawings", {}) or {}).get(name)
    if stored is not None and not params.get("views"):
        drawing = stored
    else:
        props = {
            k: v for k, v in params.items() if k not in ("name", "formats", "out_dir", "out", "job")
        }
        drawing = build_drawing(doc, name, props)

    formats = _formats(params.get("formats"))
    out_dir = params.get("out_dir") or params.get("out")
    files = write_files(drawing, formats, out_dir, name) if out_dir else {}

    out: dict[str, Any] = drawing.summary()
    out["files"] = files
    out["views"] = [
        {
            "name": v.name,
            "dir": v.label,
            "scale": round(v.scale, 6) + 0.0,
            "visible_edges": v.visible_edges,
            "hidden_edges": v.hidden_edges,
        }
        for v in drawing.views
    ]
    out["dimensions"] = [
        {
            "name": d.name,
            "kind": d.kind,
            "value_mm": round(d.value_mm, 3) + 0.0,
            "projected_mm": round(d.projected_mm, 3) + 0.0,
            "agree": d.agree,
            "text": d.text,
        }
        for d in drawing.dims
    ]
    if drawing.holes:
        out["hole_table"] = list(drawing.holes)
    if drawing.parts:
        out["parts_list"] = list(drawing.parts)
    if drawing.notes:
        out["notes"] = list(drawing.notes)
    return out


__all__ = ["FORMATS", "build_drawing", "write_files"]
