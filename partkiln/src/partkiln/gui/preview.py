"""The 2D preview: partkiln's OWN SVG writer, pointed at a sketch.

There is no 3D viewport here and there will not be one from this package. The
kernel ships no renderer, `partkiln.exchange` hands a body to Blender, and a
second-rate GL widget inside Qt would be a worse picture and a whole new
surface to maintain - the same decision seamkiln's shell took, for the same
reason, and the same honest cost: you cannot orbit it.

What partkiln DOES have is a deterministic SVG writer (`drawing.svg`), so the
drawing pane shows the file the kernel wrote, byte for byte, and the sketch
pane goes through that writer's own element emitters and stylesheet rather than
a second renderer with its own rounding. `_element`/`_group`/`_n` are private
to the package, not to this module; reaching for them is the whole point.

Sheet convention, inherited unchanged: 1 user unit = 1 millimetre, the page is
emitted inside one `translate(0, H) scale(1, -1)` group so y is up, and every
number goes through `_n` (3 dp, -0 folded). Construction geometry is drawn in
the `hidden` class, which the stylesheet dashes.
"""

from __future__ import annotations

import math
from typing import Any

from partkiln.drawing import svg as svg_writer
from partkiln.drawing.hlr import Arc, Prim, Segment, prim_bbox

MARGIN_MM = 8.0


def sketch_prims(sketch: Any) -> tuple[list[Prim], list[Prim]]:
    """A solved sketch as (real, construction) primitives in sketch millimetres.

    Points are not drawn: a rectangle's four corners add eight marks and no
    information, and the tags that name them are in the entity rows already.
    """
    real: list[Prim] = []
    construction: list[Prim] = []
    for tag in sorted(sketch.entities):
        entity = sketch.entities[tag]
        prim = _prim(sketch, entity)
        if prim is None:
            continue
        (construction if getattr(entity, "construction", False) else real).append(prim)
    return real, construction


def _prim(sketch: Any, entity: Any) -> Prim | None:
    kind = getattr(entity, "kind", "")
    if kind == "line":
        x0, y0 = sketch.xy(entity.a)
        x1, y1 = sketch.xy(entity.b)
        return Segment(x0, y0, x1, y1)
    if kind == "circle":
        cx, cy = sketch.xy(entity.center)
        return Arc(cx, cy, sketch.radius(entity.tag), 0.0, 360.0)
    if kind == "arc":
        cx, cy = sketch.xy(entity.center)
        radius = sketch.radius(entity.tag)
        a0 = _angle(sketch, entity.center, entity.start)
        a1 = _angle(sketch, entity.center, entity.end)
        # `Arc` is counter-clockwise from a0 to a1; a clockwise sketch arc is
        # the same curve traversed the other way, so swap the ends rather than
        # emit a negative sweep the writer would have to guess about.
        if not getattr(entity, "ccw", True):
            a0, a1 = a1, a0
        if a1 <= a0:
            a1 += 360.0
        return Arc(cx, cy, radius, a0, a1)
    return None


def _angle(sketch: Any, centre_tag: str, point_tag: str) -> float:
    cx, cy = sketch.xy(centre_tag)
    px, py = sketch.xy(point_tag)
    return math.degrees(math.atan2(py - cy, px - cx)) % 360.0


def sketch_svg(sketch: Any) -> str:
    """One sketch as a standalone SVG string, sized to its own extents.

    Deterministic for a given solve, exactly as the sheet writer is: the same
    sketch in another process produces the same bytes.
    """
    real, construction = sketch_prims(sketch)
    box = prim_bbox([*real, *construction])
    if box is None:
        box = (0.0, 0.0, 1.0, 1.0)
    x0, y0, x1, y1 = box
    width = max(x1 - x0, 1.0) + 2 * MARGIN_MM
    height = max(y1 - y0, 1.0) + 2 * MARGIN_MM
    shift_x = MARGIN_MM - x0
    shift_y = MARGIN_MM - y0
    body: list[str] = []
    body.extend(svg_writer._group("visible", [_shift(p, shift_x, shift_y) for p in real]))
    body.extend(svg_writer._group("hidden", [_shift(p, shift_x, shift_y) for p in construction]))
    n = svg_writer._n
    head = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
        f'width="{n(width)}mm" height="{n(height)}mm" '
        f'viewBox="0 0 {n(width)} {n(height)}">\n'
        f"<title>{svg_writer._escape(sketch.name)}</title>\n"
        f"<style>{svg_writer.STYLE}</style>\n"
        f'<g transform="translate(0,{n(height)}) scale(1,-1)">'
    )
    return head + "\n" + "\n".join(body) + "\n</g>\n</svg>\n"


def _shift(prim: Prim, dx: float, dy: float) -> Prim:
    """Move a primitive into the page's margin. Frozen dataclasses, so a new
    one - which also keeps `sketch_prims` usable for measurement."""
    if isinstance(prim, Segment):
        return Segment(prim.x0 + dx, prim.y0 + dy, prim.x1 + dx, prim.y1 + dy)
    if isinstance(prim, Arc):
        return Arc(prim.cx + dx, prim.cy + dy, prim.r, prim.a0, prim.a1)
    return type(prim)(tuple((x + dx, y + dy) for x, y in prim.points))


__all__ = ["MARGIN_MM", "sketch_prims", "sketch_svg"]
