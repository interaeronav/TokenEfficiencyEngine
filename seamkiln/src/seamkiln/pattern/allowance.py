"""Seam allowance and outline offsetting, on shapely.

Two directions, named for what a pattern maker means by them rather than by
the sign of a buffer:

  add_seam_allowance  the outline you drew is the SEW line; grow it outward
                      to the cut line and keep the sew line as an internal
                      line (ASTM layer 14), which is what a cutter needs.
  sew_line            the outline you drew is the CUT line; shrink it inward
                      to find where the stitching goes.

Both refuse loudly rather than returning something plausible: an inward
offset larger than the narrowest part of a panel does not "mostly work", it
silently deletes a point or splits the piece in two, and a pattern that
quietly lost its dart tip is worse than an error message.
"""

from __future__ import annotations

from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry

from seamkiln.pattern.geometry import Polyline, Vertex, VertexKind, retag_by_angle, to_array
from seamkiln.pattern.model import LineKind, Panel


class AllowanceError(ValueError):
    """An offset that cannot be represented as one closed piece."""


def _to_polygon(outline: Polyline) -> Polygon:
    polygon = Polygon(to_array(outline))
    if not polygon.is_valid:
        repaired = polygon.buffer(0)
        if repaired.is_empty or repaired.geom_type != "Polygon":
            raise AllowanceError(
                "the outline self-intersects and could not be repaired; "
                "fix the crossing before offsetting"
            )
        return repaired
    return polygon


def _single_ring(result: BaseGeometry, distance: float, context: str) -> Polyline:
    if result.is_empty:
        raise AllowanceError(
            f"{context}: offsetting by {distance:g} mm consumed the whole panel. "
            "The offset exceeds half the panel's narrowest width."
        )
    if result.geom_type == "MultiPolygon":
        parts = len(result.geoms)
        raise AllowanceError(
            f"{context}: offsetting by {distance:g} mm split the panel into {parts} pieces. "
            "Reduce the allowance, or split the panel deliberately first."
        )
    if result.geom_type != "Polygon":
        raise AllowanceError(f"{context}: offset produced {result.geom_type}, not a polygon")
    if list(result.interiors):
        raise AllowanceError(
            f"{context}: offsetting by {distance:g} mm created a hole; the outline "
            "probably doubles back on itself"
        )
    coords = list(result.exterior.coords)[:-1]  # shapely repeats the first point
    ring = [Vertex(float(x), float(y), VertexKind.CURVE) for x, y in coords]
    # shapely carries no turn/curve tags through a buffer, so rebuild them.
    return retag_by_angle(ring)


def offset_outline(outline: Polyline, distance_mm: float, *, context: str = "offset") -> Polyline:
    """Offset a closed outline. Positive grows it, negative shrinks it.

    Mitred joins, because a pattern corner is a corner: a rounded join would
    silently shave the point off a dart or a collar tip.
    """
    if distance_mm == 0.0:
        return list(outline)
    polygon = _to_polygon(outline)
    result = polygon.buffer(distance_mm, join_style="mitre", mitre_limit=8.0)
    return _single_ring(result, distance_mm, context)


def add_seam_allowance(panel: Panel, allowance_mm: float) -> Panel:
    """Record the allowance. The outline stays the SEW line.

    The first version replaced the outline with the offset cut line, and it
    was wrong in a way that only showed up through the adapter: a mitred
    offset re-tags corners by angle, so the tee front went from 8 edges to 6,
    and every seam referencing edge 6 or 7 pointed past the end of the list.

    Keeping the sew line as the outline is also the more honest model. A seam
    is sewn along the sew line - that is the length `true_up` must match -
    and the cut line is derived from it, not the other way round. `cut_line`
    computes it on demand, and the DXF writer puts the cut line on layer 1
    and the sew line on layer 14, which is what the standard expects.
    """
    if allowance_mm <= 0.0:
        raise AllowanceError(f"seam allowance must be positive, got {allowance_mm:g} mm")
    cut_line(panel, allowance_mm)  # fail now if the offset is impossible, not at export
    return Panel(
        id=panel.id,
        name=panel.name,
        outline=list(panel.outline),
        internals=list(panel.internals),
        marks=list(panel.marks),
        seam_allowance_mm=allowance_mm,
        meta={**panel.meta, "outline_is": "sew_line"},
    )


def cut_line(panel: Panel, allowance_mm: float | None = None) -> Polyline:
    """Where the scissors go: the outline grown by the seam allowance."""
    distance = allowance_mm if allowance_mm is not None else panel.seam_allowance_mm
    if not distance:
        return list(panel.outline)
    return offset_outline(panel.outline, abs(distance), context=f"panel {panel.id} cut line")


def sew_line(panel: Panel, allowance_mm: float | None = None) -> Polyline:
    """The stitch line. It IS the outline unless the outline is a cut line
    (which is what a DXF read gives you: ASTM layer 1 is the piece boundary)."""
    if panel.meta.get("outline_is") != "cut_line":
        return list(panel.outline)
    distance = allowance_mm if allowance_mm is not None else panel.seam_allowance_mm
    if not distance:
        raise AllowanceError(f"panel {panel.id} carries no seam allowance; pass one explicitly")
    for internal in panel.internals:  # if the file kept it, use it
        if internal.kind is LineKind.SEW and internal.closed:
            return list(internal.points)
    return offset_outline(panel.outline, -abs(distance), context=f"panel {panel.id} sew line")


def fabric_consumption(panel: Panel) -> dict[str, float]:
    """Area, bounding area and how much of the bounding box the piece wastes.

    Not a marker maker - that is out of scope - but the honest first number:
    a piece that fills 40% of its bounding box will nest badly and the
    designer should know before the fabric is cut.
    """
    minx, miny, maxx, maxy = panel.bbox
    bounding = max((maxx - minx) * (maxy - miny), 1e-9)
    return {
        "area_mm2": round(panel.area_mm2, 2),
        "bbox_mm2": round(bounding, 2),
        "bbox_w_mm": round(maxx - minx, 2),
        "bbox_h_mm": round(maxy - miny, 2),
        "fill_ratio": round(panel.area_mm2 / bounding, 4),
    }
