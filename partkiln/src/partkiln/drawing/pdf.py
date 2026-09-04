"""The PDF writer: fpdf2, and only inside `partkiln[pdf]`.

fpdf2 is LGPL-3.0-only. It lives in the optional `[pdf]` extra, exactly as
TEE's own PDF lane does, and the core never imports it - so the import is
inside this function and its absence is a refusal that names the extra
(`pk_not_served`), never an ImportError.

Page size comes from the sheet, in millimetres, so an A3 landscape sheet
(420 x 297 mm) is a 1190.55 x 841.89 pt MediaBox - the number a PDF reader
reports, and the P5a acceptance.

Two facts measured against fpdf2 2.8.8 on 2026-09-02, from the emitted content
stream, not from the docs:

  * `FPDF.circle(x, y, r)` takes the CENTRE (a 10 mm circle at (50, 50) on a
    100 mm page emits Béziers spanning 40..60 mm), so full circles are native.
  * `FPDF.arc(x, y, a, start, end)` does NOT anchor on the centre in this
    release, so partial arcs are emitted as chord-tolerance polylines. Same
    geometry, no version guessing.

Text is real text (`FPDF.text`), not outlines, so the title block, the hole
notes and every dimension are extractable by pypdf - which is how the
acceptance reads them back. The core Helvetica font is Latin-1, which covers
both characters a mechanical drawing needs: U+00D8 and U+00D7 (diameter, times).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import UTC
from pathlib import Path
from typing import Any

from partkiln.document import CommandError
from partkiln.drawing.dims import arrow_polygon, place
from partkiln.drawing.hlr import Arc, Polyline, Prim, Segment
from partkiln.drawing.views import (
    LABEL_MM,
    TEXT_MM,
    Drawing,
    View,
    frame_lines,
    projection_symbol,
    title_lines,
)

INSTALL_LINE = "uv pip install 'partkiln[pdf]'  (fpdf2, LGPL-3.0-only)"
ARC_CHORD_MM = 0.05
# 3.5 mm characters (ISO 3098) as a point size: fpdf sizes fonts in points even
# when the page is in millimetres.
PT_PER_MM = 72.0 / 25.4


def _require_fpdf() -> Any:
    try:
        from fpdf import FPDF
    except ImportError as exc:
        raise CommandError(
            "partkiln[pdf] is not installed in this interpreter, so the sheet cannot be written "
            f"as PDF. Fix: {INSTALL_LINE} - or ask for formats: ['svg', 'dxf'], which need no "
            "extra.",
            code="pk_not_served",
        ) from exc
    return FPDF


def _flip(y: float, height: float) -> float:
    """Sheet millimetres (y up) into fpdf page millimetres (y down)."""
    return height - y


def _arc_points(arc: Arc) -> list[tuple[float, float]]:
    steps = max(8, math.ceil(abs(arc.sweep) / 360.0 * 2.0 * math.pi * arc.r / ARC_CHORD_MM))
    steps = min(steps, 720)
    return [arc.point(arc.a0 + arc.sweep * i / steps) for i in range(steps + 1)]


def _draw(pdf: Any, prim: Prim, height: float) -> None:
    if isinstance(prim, Segment):
        pdf.line(prim.x0, _flip(prim.y0, height), prim.x1, _flip(prim.y1, height))
    elif isinstance(prim, Arc):
        if prim.full:
            pdf.circle(prim.cx, _flip(prim.cy, height), prim.r)
        else:
            pdf.polyline([(x, _flip(y, height)) for x, y in _arc_points(prim)])
    elif isinstance(prim, Polyline):
        pdf.polyline([(x, _flip(y, height)) for x, y in prim.points])


def _text(pdf: Any, x: float, y: float, text: str, size_mm: float, height: float) -> None:
    pdf.set_font_size(max(size_mm * PT_PER_MM, 1.0))
    pdf.text(x, _flip(y, height), _latin(text))


def _latin(text: str) -> str:
    """Everything the core Helvetica can print; anything else named, not dropped."""
    try:
        text.encode("latin-1")
    except UnicodeEncodeError:
        return text.encode("latin-1", "replace").decode("latin-1")
    return text


def _table(
    pdf: Any,
    x: float,
    y: float,
    heading: str,
    columns: Sequence[str],
    rows: Sequence[Sequence[Any]],
    widths: Sequence[float],
    height: float,
    row_mm: float = 5.0,
) -> float:
    _text(pdf, x, y, heading, TEXT_MM, height)
    cursor = y - row_mm
    at = x
    for column, width in zip(columns, widths, strict=True):
        _text(pdf, at, cursor, column, TEXT_MM * 0.85, height)
        at += width
    cursor -= row_mm
    for row in rows:
        at = x
        for cell, width in zip(row, widths, strict=True):
            _text(pdf, at, cursor, str(cell), TEXT_MM * 0.85, height)
            at += width
        cursor -= row_mm
    return cursor - row_mm


def _view_geometry(pdf: Any, view: View, height: float) -> None:
    pdf.set_line_width(0.5)
    pdf.set_dash_pattern()
    for prim in view.sheet_prims(view.visible):
        _draw(pdf, prim, height)
    pdf.set_line_width(0.25)
    pdf.set_dash_pattern(dash=2.0, gap=1.0)
    for prim in view.sheet_prims(view.hidden):
        _draw(pdf, prim, height)
    pdf.set_dash_pattern()
    pdf.set_line_width(0.18)
    for prim in view.sheet_prims(view.hatch):
        _draw(pdf, prim, height)


def render(drawing: Drawing, path: str | Path) -> Path:
    """Write the sheet as a one-page PDF the size of the sheet."""
    FPDF = _require_fpdf()
    sheet = drawing.sheet
    height = sheet.height
    pdf = FPDF(orientation="P", unit="mm", format=(sheet.width, sheet.height))
    # Rule 7 again: without a fixed date two identical sheets differ.
    from datetime import datetime

    pdf.set_creation_date(datetime(2026, 9, 2, tzinfo=UTC))
    pdf.set_title(drawing.name)
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.set_font("Helvetica", size=TEXT_MM * PT_PER_MM)
    pdf.set_draw_color(16, 16, 16)
    pdf.set_text_color(16, 16, 16)

    pdf.set_line_width(0.7)
    for line in frame_lines(sheet):
        _draw(pdf, line, height)
    for prim in projection_symbol(drawing):
        _draw(pdf, prim, height)

    for view in drawing.views:
        _view_geometry(pdf, view, height)
        if view.window is not None and view.kind != "detail":
            cx, cy, r = view.window
            p = view.to_sheet((cx, cy))
            pdf.set_line_width(0.35)
            pdf.circle(p[0], _flip(p[1], height), r * view.scale)
        x0, y0, x1, _y1 = view.sheet_bbox()
        pdf.set_font_size(LABEL_MM * PT_PER_MM)
        label = _latin(view.label.upper())
        pdf.text(
            0.5 * (x0 + x1) - 0.5 * pdf.get_string_width(label),
            _flip(y0 - 6.0 - LABEL_MM, height),
            label,
        )

    pdf.set_line_width(0.25)
    pdf.set_draw_color(13, 71, 161)
    pdf.set_text_color(13, 71, 161)
    for dim in drawing.dims:
        geo = place(drawing.view(dim.view), dim)
        for line in geo.lines:
            _draw(pdf, line, height)
        for tip, angle in geo.arrows:
            pdf.polygon(
                [(x, _flip(y, height)) for x, y in arrow_polygon(tip, angle)],
                style="F",
            )
        for x, y, text, size, _rotation in geo.texts:
            _text(pdf, x, y, text, size, height)

    pdf.set_draw_color(16, 16, 16)
    pdf.set_text_color(16, 16, 16)
    tx = sheet.margin + 2.0
    ty = sheet.height - sheet.margin - 6.0
    if drawing.holes:
        shown = drawing.holes[: drawing.holes_shown or len(drawing.holes)]
        rows: list[Sequence[Any]] = [
            (r["name"], r["x"], r["y"], r["dia_mm"], r["depth"]) for r in shown
        ]
        if len(shown) < len(drawing.holes):
            rows.append((f"+{len(drawing.holes) - len(shown)} more", "", "", "", ""))
        ty = _table(
            pdf,
            tx,
            ty,
            f"HOLE TABLE ({len(drawing.holes)})",
            ("TAG", "X", "Y", "DIA", "DEPTH"),
            rows,
            (26.0, 16.0, 16.0, 14.0, 16.0),
            height,
        )
    if drawing.parts:
        ty = _table(
            pdf,
            tx,
            ty,
            f"PARTS LIST ({len(drawing.parts)})",
            ("ITEM", "PART", "QTY", "MATERIAL", "MASS g"),
            [
                (r["item"], r["part"], r["qty"], r["material"], r.get("total_g", 0.0))
                for r in drawing.parts
            ],
            (14.0, 34.0, 12.0, 30.0, 20.0),
            height,
        )
    for i, note in enumerate(drawing.notes):
        _text(pdf, tx, ty - i * 5.0, note, TEXT_MM, height)

    for x, y, text, size in title_lines(drawing):
        _text(pdf, x, y, text, size, height)

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(destination))
    return destination


def write(drawing: Drawing, path: str | Path) -> Path:
    return render(drawing, path)


def available() -> bool:
    """True when `partkiln[pdf]` is installed here (checked without importing)."""
    from importlib.util import find_spec

    return find_spec("fpdf") is not None


__all__ = ["INSTALL_LINE", "available", "render", "write"]
