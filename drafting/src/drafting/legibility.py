"""The second tier: check the PLOT, not the specification.

The spec critic can tell you the text is 2,5 mm and the border is 0,70 mm and
be entirely satisfied while a section cut line runs straight through a room
name. Conformance and legibility are different properties, and only one of
them is visible in the data: collisions are a fact about the rendered sheet.

So this tier measures the drawn artists after the figure exists - text boxes
against text boxes, and everything against the frame - and reports overlaps in
millimetres on the plotted sheet. It is a critic, not a solver: a collision is
reported with both offenders named so the layout can be fixed deliberately.
"""

from __future__ import annotations

from dataclasses import dataclass

from drafting import standards as S


@dataclass
class Box:
    label: str
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def area(self) -> float:
        return max(0.0, self.x1 - self.x0) * max(0.0, self.y1 - self.y0)

    def overlap(self, other: Box) -> float:
        w = min(self.x1, other.x1) - max(self.x0, other.x0)
        h = min(self.y1, other.y1) - max(self.y0, other.y0)
        return w * h if w > 0 and h > 0 else 0.0


IGNORE_PREFIX = ("_", "scalebar-tick")


def _text_extent(artist, renderer):
    """The box the GLYPHS occupy, not the annotation's leader as well.

    Annotation.get_window_extent includes the arrow, so a 2 mm label with a
    35 mm leader measured 35 mm tall and collided with everything the leader
    passed near. A false positive in a critic is worse than a missing check:
    it teaches the reader to skim the findings.
    """
    from matplotlib.text import Annotation, Text

    if isinstance(artist, Annotation):
        return Text.get_window_extent(artist, renderer=renderer)
    return artist.get_window_extent(renderer=renderer)


MIN_OVERLAP_MM2 = 1.5  # below this the boxes merely touch
# Text needs clear space, not merely the absence of intersection: a caption
# sitting 0,08 mm off a soffit line reads as sitting ON it. Boxes are inflated
# by this much before being tested against graphics.
CLEARANCE_MM = 0.6
FRAME_MARGIN_MM = 8.0


def _is_masked(artist) -> bool:
    """True when the text carries an opaque backing patch.

    Drafting practice places a dimension figure IN A BREAK in its own
    dimension line, and a section-mark letter inside a bubble. Text with an
    opaque background reproduces exactly that, so a line running under it is
    correct rather than a collision - flagging it would train the eye to
    ignore this whole tier.
    """
    patch = artist.get_bbox_patch()
    if patch is None:
        return False
    face = patch.get_facecolor()
    if isinstance(face, str):
        return face not in ("none", "None")
    return len(face) < 4 or face[3] > 0.5


def text_boxes(canvas, masked: bool | None = None) -> list[Box]:
    """Every text artist on the sheet, in millimetres from the bottom-left.

    `masked=False` returns only text a line may NOT pass under.
    """
    fig = canvas.fig
    fig.canvas.draw()
    dpi = fig.dpi
    boxes = []
    for artist in fig.findobj(match=lambda a: hasattr(a, "get_text")):
        content = (artist.get_text() or "").strip()
        if not content or content.startswith(IGNORE_PREFIX):
            continue
        try:
            bb = _text_extent(artist, fig.canvas.get_renderer())
        except Exception:
            continue
        if bb.width <= 0 or bb.height <= 0:
            continue
        if masked is not None and _is_masked(artist) != masked:
            continue
        k = 25.4 / dpi
        boxes.append(Box(content[:34], bb.x0 * k, bb.y0 * k, bb.x1 * k, bb.y1 * k))
    return boxes


def line_segments(canvas) -> list[tuple[str, list[tuple[float, float]]]]:
    """Drawn polylines in sheet millimetres, so text can be checked against them.

    Text-versus-text was not enough: the defect that actually spoiled the first
    re-issue was a section cut line running straight through two room names,
    and a cut line is a graphic, not a string.
    """
    import numpy as np

    fig = canvas.fig
    fig.canvas.draw()
    k = 25.4 / fig.dpi
    out = []
    for ax in fig.axes:
        for line in ax.get_lines():
            data = line.get_xydata()
            if data is None or len(data) < 2:
                continue
            if line.get_linewidth() < 0.4:  # hairlines are not obstructions
                continue
            pts = ax.transData.transform(np.asarray(data, float))
            out.append((f"line lw={line.get_linewidth():.2f}", [(x * k, y * k) for x, y in pts]))
    return out


def patch_boxes(canvas) -> list[Box]:
    """Filled rectangles - the scale bar is one, and text ran underneath it.

    A Rectangle is neither a Line2D nor a Text, so the first two checks both
    walked straight past a solid black bar sitting on top of a note.
    """
    from matplotlib.patches import Rectangle

    fig = canvas.fig
    fig.canvas.draw()
    k = 25.4 / fig.dpi
    # An Axes paints its own white background rectangle, which "covers" every
    # label inside it. Counting those made the whole plan one giant collision.
    backgrounds = {id(fig.patch)} | {id(ax.patch) for ax in fig.axes}
    out = []
    for artist in fig.findobj(match=Rectangle):
        if id(artist) in backgrounds:
            continue
        face = artist.get_facecolor()
        if artist.get_fill() is False or (len(face) > 3 and face[3] < 0.5):
            continue
        try:
            bb = artist.get_window_extent(renderer=fig.canvas.get_renderer())
        except Exception:
            continue
        if bb.width <= 0 or bb.height <= 0:
            continue
        if bb.width * k > 0.9 * canvas.w:  # the sheet background itself
            continue
        out.append(Box("filled rectangle", bb.x0 * k, bb.y0 * k, bb.x1 * k, bb.y1 * k))
    return out


def _segment_hits_box(p0, p1, box: Box, steps: int = 24) -> bool:
    for i in range(steps + 1):
        t = i / steps
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        if box.x0 <= x <= box.x1 and box.y0 <= y <= box.y1:
            return True
    return False


def inspect(canvas, report: S.Report | None = None) -> S.Report:
    report = report or S.Report()
    number = canvas.spec.number
    boxes = text_boxes(canvas)

    for i, a in enumerate(boxes):
        for b in boxes[i + 1 :]:
            area = a.overlap(b)
            if area >= MIN_OVERLAP_MM2:
                report.add(
                    "LEGIBILITY-OVERLAP",
                    f"{number}/text",
                    f"'{a.label}' collides with '{b.label}' over {area:.1f} mm²",
                    severity="correct",
                    remedy="Move one of them; a reader cannot resolve overlapping text.",
                )
    for label, pts in line_segments(canvas):
        for box in text_boxes(canvas, masked=False):
            if box.area < 2.0:
                continue
            grown = Box(
                box.label,
                box.x0 - CLEARANCE_MM,
                box.y0 - CLEARANCE_MM,
                box.x1 + CLEARANCE_MM,
                box.y1 + CLEARANCE_MM,
            )
            if any(_segment_hits_box(pts[i], pts[i + 1], grown) for i in range(len(pts) - 1)):
                report.add(
                    "LEGIBILITY-OVERLAP",
                    f"{number}/graphic",
                    f"a drawn {label} passes through the text '{box.label}'",
                    severity="correct",
                    remedy="Move the text clear, or break the line around it.",
                )
                break

    for patch in patch_boxes(canvas):
        for box in text_boxes(canvas, masked=False):
            if patch.overlap(box) >= MIN_OVERLAP_MM2:
                report.add(
                    "LEGIBILITY-OVERLAP",
                    f"{number}/graphic",
                    f"a filled rectangle covers the text '{box.label}'",
                    severity="correct",
                    remedy="Move the text or the panel clear.",
                )

    for box in boxes:
        if (
            box.x0 < FRAME_MARGIN_MM - 0.5
            or box.y0 < FRAME_MARGIN_MM - 0.5
            or box.x1 > canvas.w - FRAME_MARGIN_MM + 0.5
            or box.y1 > canvas.h - FRAME_MARGIN_MM + 0.5
        ):
            report.add(
                "LEGIBILITY-FRAME",
                f"{number}/text",
                f"'{box.label}' falls outside the drawing frame",
                severity="reject",
                remedy="Bring it inside the border.",
            )
    return report
