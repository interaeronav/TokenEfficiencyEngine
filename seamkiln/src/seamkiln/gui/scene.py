"""The 2D pattern view: QGraphicsView, because that is what it is for.

Qt's own docs put "2D design tools" in Graphics View's list of intended uses,
and a pattern piece is exactly that - a few hundred line segments that need
selecting, panning and zooming smoothly. Nothing here holds pattern state:
the scene is rebuilt from the Session's pattern, so what you see cannot drift
from what a script would produce.
"""

from __future__ import annotations

from typing import Any

CUT_COLOUR = (30, 30, 30)
SEW_COLOUR = (120, 120, 120)
GRAIN_COLOUR = (60, 110, 190)
MARK_COLOUR = (200, 40, 40)


def build_scene(session: Any, scene: Any) -> dict[str, int]:
    """Draw the session's pattern into a QGraphicsScene. Returns what it drew."""
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QColor, QPainterPath, QPen

    from seamkiln.pattern.allowance import cut_line
    from seamkiln.pattern.model import LineKind, MarkKind
    from seamkiln.pattern.plot import lay_out

    scene.clear()
    counts = {"panels": 0, "marks": 0, "internals": 0}
    if session.pattern is None:
        return counts

    # Panels are drafted about a shared origin, so drawn raw they sit on top
    # of one another - the first version of this window showed four pieces as
    # one tangle with the labels overlapping. The plot lane already solves
    # this for printing; using the SAME layout means what the window shows and
    # what the printer produces are laid out identically.
    layout = lay_out(session.pattern, gap_mm=30.0)

    def path_of(points, closed: bool, offset=(0.0, 0.0)):
        path = QPainterPath()
        # y is flipped once, here: pattern space has y up, Qt has y down
        dx, dy = offset
        path.moveTo(QPointF(points[0].x + dx, -(points[0].y + dy)))
        for vertex in points[1:]:
            path.lineTo(QPointF(vertex.x + dx, -(vertex.y + dy)))
        if closed:
            path.closeSubpath()
        return path

    for panel in session.pattern.panels:
        offset = layout.placements[panel.id]
        if panel.seam_allowance_mm:
            pen = QPen(QColor(*CUT_COLOUR), 1.2)
            pen.setCosmetic(True)
            scene.addPath(path_of(cut_line(panel), True, offset), pen)
            pen = QPen(QColor(*SEW_COLOUR), 1.0, Qt.PenStyle.DashLine)
            pen.setCosmetic(True)
            scene.addPath(path_of(panel.outline, True, offset), pen)
        else:
            pen = QPen(QColor(*CUT_COLOUR), 1.4)
            pen.setCosmetic(True)
            scene.addPath(path_of(panel.outline, True, offset), pen)
        counts["panels"] += 1

        for internal in panel.internals:
            colour = GRAIN_COLOUR if internal.kind is LineKind.GRAIN else SEW_COLOUR
            pen = QPen(QColor(*colour), 1.0, Qt.PenStyle.DashLine)
            pen.setCosmetic(True)
            scene.addPath(path_of(internal.points, internal.closed, offset), pen)
            counts["internals"] += 1

        for mark in panel.marks:
            radius = mark.diameter / 2 if mark.kind is MarkKind.DRILL else 4.0
            pen = QPen(QColor(*MARK_COLOUR), 1.2)
            pen.setCosmetic(True)
            scene.addEllipse(
                mark.x + offset[0] - radius,
                -(mark.y + offset[1]) - radius,
                radius * 2,
                radius * 2,
                pen,
            )
            counts["marks"] += 1

        label = scene.addText(panel.name)
        label.setDefaultTextColor(QColor(90, 90, 90))
        minx, miny, _, _ = panel.bbox
        label.setPos(minx + offset[0], -(miny + offset[1]))
        label.setScale(2.0)
    return counts
