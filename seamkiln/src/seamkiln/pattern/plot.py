"""Pattern sheets: SVG and true 1:1 PDF, tiled for a home printer.

The only requirement that matters here is the boring one: **a 100 mm line
must measure 100 mm when the sheet comes out of the printer.** Everything
else - tiling, registration marks, labels - exists to keep that true across
more than one page. A pattern that prints at 97% is not a pattern, and the
failure is invisible until a garment is cut, so the 1:1 claim is tested by
reading the coordinates back out of the finished PDF rather than trusted.

Pattern space has y increasing upward; PDF and SVG have it increasing
downward. That flip happens once, here, in `_project`.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any

from seamkiln.pattern.geometry import Polyline
from seamkiln.pattern.model import LineKind, MarkKind, Panel, Pattern

PAGES_MM: dict[str, tuple[float, float]] = {
    "A4": (210.0, 297.0),
    "A3": (297.0, 420.0),
    "A0": (841.0, 1189.0),
    "LETTER": (215.9, 279.4),
    "PLOTTER_1370": (1370.0, 20000.0),  # a roll: one very long sheet
}
PT_PER_MM = 72.0 / 25.4


@dataclass
class Layout:
    """Where each panel sits on the shared sheet, in mm."""

    placements: dict[str, tuple[float, float]]
    width_mm: float
    height_mm: float


def lay_out(pattern: Pattern, *, gap_mm: float = 20.0, max_width_mm: float = 1370.0) -> Layout:
    """Left-to-right shelf packing. Deliberately NOT a marker maker.

    Real nesting is an optimisation problem and it is out of scope (see the
    script's "Out of scope"). This packs predictably so a sheet is
    reproducible; it does not claim to save fabric.
    """
    placements: dict[str, tuple[float, float]] = {}
    cursor_x = gap_mm
    cursor_y = gap_mm
    shelf_height = 0.0
    width = gap_mm

    for panel in pattern.panels:
        minx, miny, maxx, maxy = panel.bbox
        w, h = maxx - minx, maxy - miny
        if cursor_x > gap_mm and cursor_x + w + gap_mm > max_width_mm:
            cursor_x = gap_mm
            cursor_y += shelf_height + gap_mm
            shelf_height = 0.0
        placements[panel.id] = (cursor_x - minx, cursor_y - miny)
        cursor_x += w + gap_mm
        shelf_height = max(shelf_height, h)
        width = max(width, cursor_x)

    return Layout(placements, width, cursor_y + shelf_height + gap_mm)


def _project(points: Polyline, offset: tuple[float, float], height_mm: float):
    """Pattern mm (y up) -> sheet mm (y down), once."""
    dx, dy = offset
    return [(v.x + dx, height_mm - (v.y + dy)) for v in points]


def to_svg(pattern: Pattern, path: str | Path, *, gap_mm: float = 20.0) -> dict[str, Any]:
    """One SVG sheet at 1:1. `width`/`height` in mm, viewBox in the same mm."""
    layout = lay_out(pattern, gap_mm=gap_mm)
    # Round ONCE and write the same number to the file and the report: a
    # viewBox that disagrees with the declared width is a silent rescale.
    width = round(layout.width_mm, 2)
    height = round(layout.height_mm, 2)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" '
        f'height="{height}mm" viewBox="0 0 {width} {height}">',
        '<g fill="none" stroke-width="0.3">',
    ]
    for panel in pattern.panels:
        offset = layout.placements[panel.id]
        ring = _project(panel.outline, offset, layout.height_mm)
        d = "M " + " L ".join(f"{x:.3f},{y:.3f}" for x, y in ring) + " Z"
        parts.append(f'<path d="{d}" stroke="#000"/>')
        for internal in panel.internals:
            pts = _project(internal.points, offset, layout.height_mm)
            d = "M " + " L ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
            if internal.closed:
                d += " Z"
            parts.append(f'<path d="{d}" stroke="#888" stroke-dasharray="4 2"/>')
        for mark in panel.marks:
            x, y = mark.x + offset[0], layout.height_mm - (mark.y + offset[1])
            radius = mark.diameter / 2 if mark.kind is MarkKind.DRILL else 1.5
            parts.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{radius:.2f}" stroke="#c00"/>')
        minx, miny, _, _ = panel.bbox
        parts.append(
            f'<text x="{minx + offset[0] + 4:.2f}" '
            f'y="{layout.height_mm - (miny + offset[1]) - 6:.2f}" '
            f'font-size="8" fill="#444" stroke="none">{panel.name}</text>'
        )
    parts.extend(["</g>", "</svg>"])
    destination = Path(path)
    destination.write_text("\n".join(parts), encoding="utf-8")
    return {"path": str(destination), "width_mm": width, "height_mm": height, "scale": "1:1"}


def to_pdf(
    pattern: Pattern,
    path: str | Path,
    *,
    page: str = "A4",
    gap_mm: float = 20.0,
    margin_mm: float = 10.0,
    overlap_mm: float = 10.0,
) -> dict[str, Any]:
    """Tiled 1:1 PDF. Every page carries its grid reference and a 100 mm ruler."""
    try:
        from fpdf import FPDF
    except ImportError as exc:  # the same extra TEE's pdf lane uses
        raise RuntimeError(
            "plotting to PDF needs fpdf2. Install seamkiln's [plot] extra "
            "(uv pip install 'seamkiln[plot]')."
        ) from exc

    key = page.upper()
    if key not in PAGES_MM:
        raise ValueError(f"unknown page {page!r}; known: {', '.join(sorted(PAGES_MM))}")
    page_w, page_h = PAGES_MM[key]
    layout = lay_out(pattern, gap_mm=gap_mm)

    usable_w = page_w - 2 * margin_mm
    usable_h = page_h - 2 * margin_mm
    step_w = max(usable_w - overlap_mm, 1.0)
    step_h = max(usable_h - overlap_mm, 1.0)
    cols = max(1, int(-(-layout.width_mm // step_w)))
    rows = max(1, int(-(-layout.height_mm // step_h)))

    pdf = FPDF(orientation="P", unit="mm", format=(page_w, page_h))
    pdf.set_auto_page_break(False)
    pdf.set_line_width(0.3)

    for row in range(rows):
        for col in range(cols):
            pdf.add_page()
            origin_x = col * step_w
            origin_y = row * step_h
            _draw_tile(pdf, pattern, layout, origin_x, origin_y, margin_mm, usable_w, usable_h)
            _draw_furniture(pdf, page_w, page_h, margin_mm, row, col, rows, cols, pattern.name)

    destination = Path(path)
    pdf.output(str(destination))
    return {
        "path": str(destination),
        "scale": "1:1",
        "page": key,
        "page_mm": [page_w, page_h],
        "pages": rows * cols,
        "tiles": {"rows": rows, "cols": cols, "overlap_mm": overlap_mm},
        "sheet_mm": [round(layout.width_mm, 2), round(layout.height_mm, 2)],
        "ruler_mm": 100.0,
    }


def _draw_tile(
    pdf,
    pattern: Pattern,
    layout: Layout,
    ox: float,
    oy: float,
    margin: float,
    usable_w: float,
    usable_h: float,
) -> None:
    """Draw the sheet region [ox, ox+usable_w) x [oy, oy+usable_h) at 1:1.

    fpdf2 has no clipping primitive in this path, so segments are clipped
    by rejection: a segment with both ends outside the tile is dropped.
    That is exact for the outline and internal lines, which are polylines.
    """

    def emit(points, dashed: bool = False) -> None:
        pdf.set_draw_color(*((120, 120, 120) if dashed else (0, 0, 0)))
        for (x1, y1), (x2, y2) in pairwise(points):
            px1, py1 = x1 - ox + margin, y1 - oy + margin
            px2, py2 = x2 - ox + margin, y2 - oy + margin
            inside = (
                margin - 1 <= px1 <= margin + usable_w + 1
                and margin - 1 <= py1 <= margin + usable_h + 1
            ) or (
                margin - 1 <= px2 <= margin + usable_w + 1
                and margin - 1 <= py2 <= margin + usable_h + 1
            )
            if inside:
                pdf.line(px1, py1, px2, py2)

    for panel in pattern.panels:
        offset = layout.placements[panel.id]
        ring = _project(panel.outline, offset, layout.height_mm)
        emit([*ring, ring[0]])
        for internal in panel.internals:
            pts = _project(internal.points, offset, layout.height_mm)
            emit([*pts, pts[0]] if internal.closed else pts, dashed=True)
        for mark in panel.marks:
            x = mark.x + offset[0] - ox + margin
            y = layout.height_mm - (mark.y + offset[1]) - oy + margin
            if margin <= x <= margin + usable_w and margin <= y <= margin + usable_h:
                pdf.set_draw_color(200, 0, 0)
                radius = mark.diameter / 2 if mark.kind is MarkKind.DRILL else 1.5
                pdf.circle(x=x - radius, y=y - radius, radius=radius)


def _draw_furniture(
    pdf,
    page_w: float,
    page_h: float,
    margin: float,
    row: int,
    col: int,
    rows: int,
    cols: int,
    name: str,
) -> None:
    """Grid reference, trim box, and the 100 mm ruler that proves the scale."""
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.1)
    pdf.rect(margin, margin, page_w - 2 * margin, page_h - 2 * margin)

    pdf.set_font("helvetica", size=7)
    pdf.set_xy(margin, max(margin - 6, 1))
    pdf.cell(0, 5, f"{name}  tile {chr(65 + row)}{col + 1} of {chr(64 + rows)}{cols}  1:1")

    # a 100 mm ruler with 10 mm ticks - the reader's own check on the printer
    base_y = page_h - margin + 5
    if base_y < page_h - 1:
        pdf.set_line_width(0.3)
        pdf.line(margin, base_y, margin + 100.0, base_y)
        for tick in range(0, 101, 10):
            height = 2.5 if tick % 50 else 4.0
            pdf.line(margin + tick, base_y - height, margin + tick, base_y)
        pdf.set_xy(margin + 102, base_y - 4)
        pdf.cell(0, 5, "100 mm - measure me")


def piece_report(panel: Panel) -> dict[str, Any]:
    """The per-piece numbers a tech pack wants, without a vertex in sight."""
    minx, miny, maxx, maxy = panel.bbox
    return {
        "id": panel.id,
        "name": panel.name,
        "area_mm2": round(panel.area_mm2, 1),
        "perimeter_mm": round(panel.perimeter_mm, 1),
        "bbox_mm": [round(maxx - minx, 1), round(maxy - miny, 1)],
        "edges": len(panel.edges()),
        "notches": sum(1 for m in panel.marks if m.kind is not MarkKind.DRILL),
        "drills": sum(1 for m in panel.marks if m.kind is MarkKind.DRILL),
        "grain": any(i.kind is LineKind.GRAIN for i in panel.internals),
        "seam_allowance_mm": panel.seam_allowance_mm,
    }
