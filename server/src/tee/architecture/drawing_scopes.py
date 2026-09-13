"""Named enlarged plan extents, exact clipping and annotation coverage.

Scopes are views of the same model. They never trim entities or create storeys.
The unannotated coordination plan retains the complete geometry/dimension set;
all requested annotations must occur on at least one enlarged view.
"""

from __future__ import annotations

import math
import re
from typing import Any

from tee.kernel.errors import TeeError


def _invalid(message: str) -> TeeError:
    return TeeError(
        "architecture_drawing_scope",
        message,
        fix="Use drawing.plan_scope_mode='rooms', or named plan_scopes with storey "
        "and bounds_mm=[xmin,ymin,xmax,ymax]. Every plan annotation must be covered.",
    )


def contains(bounds: list[float], point: list[float]) -> bool:
    return all(bounds[i] - 1e-7 <= point[i] <= bounds[i + 2] + 1e-7 for i in range(2))


def clip_segment(points: list[list[float]], bounds: list[float]) -> list[list[float]] | None:
    """Liang-Barsky clip preserves authored coordinates and oblique intersections."""
    a, b = points
    enter, leave = 0.0, 1.0
    for axis in range(2):
        delta = b[axis] - a[axis]
        if abs(delta) < 1e-12:
            if not bounds[axis] <= a[axis] <= bounds[axis + 2]:
                return None
            continue
        first, last = sorted(
            ((bounds[axis] - a[axis]) / delta, (bounds[axis + 2] - a[axis]) / delta)
        )
        enter, leave = max(enter, first), min(leave, last)
        if enter >= leave - 1e-12:
            return None
    return [[a[i] + t * (b[i] - a[i]) for i in range(2)] for t in (enter, leave)]


def clipped_segments(segments: list[dict], bounds: list[float]) -> list[dict]:
    return [
        {**segment, "points": points}
        for segment in segments
        if (points := clip_segment(segment["points"], bounds)) is not None
    ]


def _request_points(request: dict[str, Any]) -> list[list[float]]:
    if request["kind"] != "space":
        return [request["anchor"]]
    from shapely.geometry import Point, Polygon

    polygons = [Polygon(part) for part in request["polygons"]]
    return [
        point
        for point in request["centres"]
        if any(polygon.contains(Point(point)) for polygon in polygons)
    ]


def plan_scopes(settings: dict[str, Any], storey: str, requests: list[dict]) -> list[dict]:
    """Produce explicit per-view annotation membership, refusing coverage holes."""
    mode, explicit = settings.get("plan_scope_mode"), settings.get("plan_scopes")
    if mode is None and explicit is None:
        return []
    if (mode is not None and mode != "rooms") or (mode is not None and explicit is not None):
        raise _invalid("Select room scopes or explicit scopes, not both.")
    scopes = []
    if mode == "rooms":
        padding = settings.get("plan_scope_padding_mm", 1500)
        if (
            isinstance(padding, bool)
            or not isinstance(padding, (int, float))
            or not math.isfinite(padding)
            or not 250 <= padding <= 10000
        ):
            raise _invalid("Scope padding must be finite and between 250 and 10000 mm.")
        for request in requests:
            if request["kind"] != "space":
                continue
            points = [p for polygon in request["polygons"] for p in polygon]
            bounds = [min(p[i] for p in points) - padding for i in range(2)] + [
                max(p[i] for p in points) + padding for i in range(2)
            ]
            scopes.append(
                {
                    "id": f"R{len(scopes) + 1:02d}",
                    "storey": storey,
                    "bounds_mm": bounds,
                    "annotation_ids": [request["id"]],
                    "subject_id": request["id"],
                    "title": request["lines"][0],
                }
            )
        for request in requests:
            if request["kind"] == "space":
                continue
            anchor = request["anchor"]
            candidates = [scope for scope in scopes if contains(scope["bounds_mm"], anchor)]
            if candidates:
                chosen = min(
                    candidates,
                    key=lambda scope: math.dist(
                        anchor,
                        [(scope["bounds_mm"][i] + scope["bounds_mm"][i + 2]) / 2 for i in range(2)],
                    ),
                )
                chosen["annotation_ids"].append(request["id"])
            else:
                scopes.append(
                    {
                        "id": f"R{len(scopes) + 1:02d}",
                        "storey": storey,
                        "bounds_mm": [
                            anchor[0] - padding,
                            anchor[1] - padding,
                            anchor[0] + padding,
                            anchor[1] + padding,
                        ],
                        "annotation_ids": [request["id"]],
                        "subject_id": request["id"],
                        "title": request["lines"][0],
                    }
                )
    else:
        if not isinstance(explicit, list) or not explicit or len(explicit) > 128:
            raise _invalid("plan_scopes must be a nonempty list of at most 128 scopes.")
        seen = set()
        for value in explicit:
            if not isinstance(value, dict):
                raise _invalid("Each plan scope must be an object.")
            sid, target, bounds = value.get("id"), value.get("storey"), value.get("bounds_mm")
            if (
                not isinstance(sid, str)
                or re.fullmatch(r"[A-Za-z0-9_-]{1,40}", sid) is None
                or not isinstance(target, str)
                or (target, sid) in seen
                or not isinstance(bounds, list)
                or len(bounds) != 4
                or any(
                    isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                    for v in bounds
                )
                or bounds[0] >= bounds[2]
                or bounds[1] >= bounds[3]
            ):
                raise _invalid("Invalid or duplicate named plan scope.")
            seen.add((target, sid))
            if target != storey:
                continue
            ids = [
                request["id"]
                for request in requests
                if any(contains(bounds, point) for point in _request_points(request))
            ]
            scopes.append(
                {
                    "id": sid,
                    "storey": storey,
                    "bounds_mm": list(bounds),
                    "annotation_ids": ids,
                    "title": sid,
                }
            )
    if len(scopes) > 128:
        raise _invalid("A storey exceeds 128 enlarged plans.")
    required = {request["id"] for request in requests}
    covered = {identifier for scope in scopes for identifier in scope["annotation_ids"]}
    if required - covered:
        missing = ", ".join(sorted(required - covered)[:8])
        raise _invalid(f"Plan scopes omit annotations: {missing}.")
    return scopes
