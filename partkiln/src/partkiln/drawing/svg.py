"""The SVG writer: ours, not a library's.

`svgwrite` is one more dependency for string concatenation the kernel can do
itself, and a hand-written writer is the only way to guarantee rule 7: the same
model writes byte-identical SVG on every run, in every process. Every number
goes through `_n()` (3 decimals, `-0` folded to `0`), every element is emitted
in the order `hlr.sort_prims` fixed, and nothing carries a timestamp or a
generated id.

Units: **1 user unit = 1 millimetre of sheet**, declared by
`width="420mm" height="297mm" viewBox="0 0 420 297"`, so a 100 mm edge drawn at
1:1 is 100 user units and a ruler on the printed page agrees with the model. The
drawing scale is already inside the coordinates (see `views.map_prim`), NOT an
SVG group transform, so text and arrowheads keep their 3.5 mm at 1:2.

The sheet frame is y-up (drawing convention); SVG is y-down, so the whole page
is emitted inside one `translate(0, H) scale(1, -1)` group and text is flipped
back locally. Hidden edges carry `class="hidden"` and the stylesheet dashes
them, so a reader can count them with a substring search.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from partkiln.drawing.dims import DimGeometry, arrow_polygon, place
from partkiln.drawing.hlr import Arc, Prim, Segment
from partkiln.drawing.views import (
    LABEL_MM,
    TEXT_MM,
    Drawing,
    View,
    frame_lines,
    projection_symbol,
    title_lines,
)

STYLE = """
.visible { fill: none; stroke: #101010; stroke-width: 0.5; stroke-linecap: round; }
.hidden { fill: none; stroke: #303030; stroke-width: 0.25; stroke-dasharray: 2 1; }
.hatch { fill: none; stroke: #404040; stroke-width: 0.18; }
.frame { fill: none; stroke: #101010; stroke-width: 0.7; }
.dim { fill: none; stroke: #0d47a1; stroke-width: 0.25; }
.arrow { fill: #0d47a1; stroke: none; }
.window { fill: none; stroke: #0d47a1; stroke-width: 0.35; stroke-dasharray: 4 1.5 1 1.5; }
text { fill: #0d47a1; font-family: Helvetica, Arial, sans-serif; }
text.label, text.title { fill: #101010; }
"""


def _n(v: float) -> str:
    """3 decimals, trailing zeros dropped, negative zero folded (rule 7)."""
    x = round(float(v), 3) + 0.0
    if x == 0:
        x = 0.0
    return f"{x:g}"


def _escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _path_arc(arc: Arc) -> str:
    """A full circle as `<circle>`, an arc as a `path` with a real `A` command."""
    if arc.full:
        return f'<circle cx="{_n(arc.cx)}" cy="{_n(arc.cy)}" r="{_n(arc.r)}"/>'
    x0, y0 = arc.start
    x1, y1 = arc.end
    large = 1 if arc.sweep > 180.0 else 0
    # The sheet group flips y, so a counter-clockwise arc in sheet coordinates is
    # emitted with sweep-flag 1 and the flip makes it read correctly on screen.
    return (
        f'<path d="M {_n(x0)} {_n(y0)} A {_n(arc.r)} {_n(arc.r)} 0 {large} 1 {_n(x1)} {_n(y1)}"/>'
    )


def _element(prim: Prim) -> str:
    if isinstance(prim, Segment):
        return (
            f'<line x1="{_n(prim.x0)}" y1="{_n(prim.y0)}" x2="{_n(prim.x1)}" y2="{_n(prim.y1)}"/>'
        )
    if isinstance(prim, Arc):
        return _path_arc(prim)
    points = " ".join(f"{_n(x)},{_n(y)}" for x, y in prim.points)
    return f'<polyline points="{points}"/>'


def _group(cls: str, prims: Sequence[Prim]) -> list[str]:
    if not prims:
        return []
    return [f'<g class="{cls}">', *[_element(p) for p in prims], "</g>"]


def _text(x: float, y: float, text: str, size: float, rotation: float, cls: str) -> str:
    # The page group flips y; flip it back here so the glyphs are the right way up.
    anchor = "middle" if cls == "dim" else "start"
    transform = f"translate({_n(x)},{_n(y)}) scale(1,-1)"
    if rotation:
        transform += f" rotate({_n(-rotation)})"
    return (
        f'<text class="{cls}" transform="{transform}" font-size="{_n(size)}" '
        f'text-anchor="{anchor}">{_escape(text)}</text>'
    )


def _dim_elements(geo: DimGeometry) -> list[str]:
    out: list[str] = []
    out.extend(_group("dim", geo.lines))
    for tip, angle in geo.arrows:
        pts = " ".join(f"{_n(x)},{_n(y)}" for x, y in arrow_polygon(tip, angle))
        out.append(f'<polygon class="arrow" points="{pts}"/>')
    for x, y, text, size, rotation in geo.texts:
        out.append(_text(x, y, text, size, rotation, "dim"))
    return out


def _table(
    x: float,
    y: float,
    heading: str,
    columns: Sequence[str],
    rows: Sequence[Sequence[Any]],
    widths: Sequence[float],
    row_mm: float = 5.0,
) -> list[str]:
    out = [_text(x, y, heading, TEXT_MM, 0.0, "label")]
    cursor = y - row_mm
    at = x
    for column, width in zip(columns, widths, strict=True):
        out.append(_text(at, cursor, column, TEXT_MM * 0.85, 0.0, "label"))
        at += width
    cursor -= row_mm
    for row in rows:
        at = x
        for cell, width in zip(row, widths, strict=True):
            out.append(_text(at, cursor, str(cell), TEXT_MM * 0.85, 0.0, "title"))
            at += width
        cursor -= row_mm
    return out


def _window(view: View) -> list[str]:
    """The detail window drawn on the SOURCE view."""
    if view.window is None or view.kind == "detail":
        return []
    cx, cy, r = view.window
    p = view.to_sheet((cx, cy))
    return [f'<circle class="window" cx="{_n(p[0])}" cy="{_n(p[1])}" r="{_n(r * view.scale)}"/>']


def render(drawing: Drawing) -> str:
    """The whole sheet as one SVG string. Deterministic for a given drawing."""
    sheet = drawing.sheet
    body: list[str] = []
    body.extend(_group("frame", frame_lines(sheet)))
    body.extend(_group("frame", projection_symbol(drawing)))

    for view in drawing.views:
        body.append(f'<g id="view-{_escape(view.name)}">')
        body.extend(_group("visible", view.sheet_prims(view.visible)))
        body.extend(_group("hidden", view.sheet_prims(view.hidden)))
        body.extend(_group("hatch", view.sheet_prims(view.hatch)))
        body.extend(_window(view))
        x0, y0, x1, _y1 = view.sheet_bbox()
        body.append(
            _text(
                0.5 * (x0 + x1),
                y0 - 6.0 - LABEL_MM,
                view.label.upper(),
                LABEL_MM,
                0.0,
                "label",
            )
        )
        body.append("</g>")

    for dim in drawing.dims:
        body.extend(_dim_elements(place(drawing.view(dim.view), dim)))

    tx = sheet.margin + 2.0
    ty = sheet.height - sheet.margin - 6.0
    if drawing.holes:
        shown = drawing.holes[: drawing.holes_shown or len(drawing.holes)]
        rows = [(r["name"], _n(r["x"]), _n(r["y"]), _n(r["dia_mm"]), r["depth"]) for r in shown]
        if len(shown) < len(drawing.holes):
            rows.append((f"+{len(drawing.holes) - len(shown)} more", "", "", "", ""))
        body.extend(
            _table(
                tx,
                ty,
                f"HOLE TABLE ({len(drawing.holes)})",
                ("TAG", "X", "Y", "Ø", "DEPTH"),
                rows,
                (26.0, 16.0, 16.0, 14.0, 16.0),
            )
        )
        ty -= 5.0 * (len(rows) + 3)
    if drawing.parts:
        rows = [
            (r["item"], r["part"], r["qty"], r["material"], _n(float(r.get("total_g") or 0.0)))
            for r in drawing.parts
        ]
        body.extend(
            _table(
                tx,
                ty,
                f"PARTS LIST ({len(drawing.parts)})",
                ("ITEM", "PART", "QTY", "MATERIAL", "MASS g"),
                rows,
                (14.0, 34.0, 12.0, 30.0, 20.0),
            )
        )
        ty -= 5.0 * (len(rows) + 3)
    for i, note in enumerate(drawing.notes):
        body.append(_text(tx, ty - i * 5.0, note, TEXT_MM, 0.0, "label"))

    for x, y, text, size in title_lines(drawing):
        body.append(_text(x, y, text, size, 0.0, "title"))

    head = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
        f'width="{_n(sheet.width)}mm" height="{_n(sheet.height)}mm" '
        f'viewBox="0 0 {_n(sheet.width)} {_n(sheet.height)}">\n'
        f"<title>{_escape(drawing.name)}</title>\n"
        f"<style>{STYLE}</style>\n"
        f'<g transform="translate(0,{_n(sheet.height)}) scale(1,-1)">'
    )
    return head + "\n" + "\n".join(body) + "\n</g>\n</svg>\n"


def write(drawing: Drawing, path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render(drawing), encoding="utf-8")
    return destination


__all__ = ["STYLE", "render", "write"]
