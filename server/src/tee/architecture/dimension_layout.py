"""Paper-space dimension labels with exact model-space witness endpoints."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

from tee.kernel.errors import TeeError


def dimension_graphics(
    rows: list[dict], paper: Callable, geometry: list[dict], reserved: list[list[float]]
) -> list[dict[str, Any]]:
    from shapely.geometry import LineString, box

    graphics, texts, lines = [], [], []
    for row in rows:
        a, b = [list(paper(row[k])) for k in ("a", "b")]
        n = [row["normal"][0], -row["normal"][1]]
        offset = row["offset_paper_mm"]
        x, y = [[p[i] + n[i] * offset for i in range(2)] for p in (a, b)]
        strokes = [[x, y]]
        for p, end in zip((a, b), (x, y), strict=True):
            strokes.append(
                [
                    [p[i] + n[i] * 1 for i in range(2)],
                    [p[i] + n[i] * (offset + 2) for i in range(2)],
                ]
            )
            strokes.append([[end[0] - 0.7, end[1] - 0.7], [end[0] + 0.7, end[1] + 0.7]])
        for points in strokes:
            graphics.append(
                {"type": "line", "points": points, "role": "dimension", "id": row["id"]}
            )
            lines.append(LineString(points))
        texts.append((row, [(x[i] + y[i]) / 2 for i in range(2)], n))
    lines.extend(LineString([paper(p) for p in item["points"]]) for item in geometry)
    occupied = [box(*r) for r in reserved]
    frame = box(14, 48, 403, 261)
    for row, mid, n in texts:
        value = f"{row['value_mm']:.3f}".rstrip("0").rstrip(".")
        size = 2.4
        width = max(3.0, len(value) * 1.55)
        tangent = [-n[1], n[0]]
        candidates = []
        for distance in (4, 8, 13, 19, 27, 38, 52):
            for lateral in (0, 7, -7, 15, -15, 28, -28, 45, -45):
                candidates.append(
                    [mid[i] + n[i] * distance + tangent[i] * lateral for i in range(2)]
                )
        selected = None
        for centre in candidates:
            rectangle = box(
                centre[0] - width / 2 - 0.5,
                centre[1] - size / 2 - 0.5,
                centre[0] + width / 2 + 0.5,
                centre[1] + size / 2 + 0.5,
            )
            if not frame.covers(rectangle) or any(rectangle.intersects(p) for p in occupied):
                continue
            if any(rectangle.intersects(line) for line in lines):
                continue
            leader = LineString([mid, centre])
            if any(leader.intersects(p) for p in occupied):
                continue
            selected = (centre, rectangle)
            break
        if selected is None:
            raise TeeError(
                "architecture_dimension_crowding",
                f"Cannot place dimension {row['id']}.",
                fix="Use a smaller named scope or larger scale; no dimension was omitted.",
            )
        centre, rectangle = selected
        if math.dist(centre, mid) > 4.01:
            boundary = [
                max(rectangle.bounds[i], min(mid[i], rectangle.bounds[i + 2])) for i in range(2)
            ]
            graphics.append(
                {
                    "type": "line",
                    "points": [mid, boundary],
                    "role": "dimension-leader",
                    "id": row["id"],
                }
            )
            lines.append(LineString([mid, boundary]))
        graphics.append(
            {
                "type": "text",
                "at": [centre[0] - width / 2, centre[1] + size / 3],
                "centre_mm": centre,
                "box_mm": list(rectangle.bounds),
                "value": value,
                "size": size,
                "role": "dimension-text",
                "id": row["id"],
                "value_mm": row["value_mm"],
                "dimension_key": row["dimension_key"],
                "basis": row["basis"],
            }
        )
        occupied.append(rectangle)
    return graphics
