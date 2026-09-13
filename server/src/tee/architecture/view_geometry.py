"""Orthographic architectural visibility from closed, millimetre triangle meshes.

Coplanar triangles are united before edges are generated. Hidden edge intervals
are clipped analytically against projected polygons and linear face depths; no
pixel buffer, point sampling, camera distance, or sample-house exclusions exist.
Shapely is an existing optional TEE dependency, imported only for drawing work.
"""

from __future__ import annotations

import itertools
import math
from collections import defaultdict
from typing import Any

from tee.kernel.errors import TeeError

TOL = 1e-6  # model millimetres; strict depth comparison permits coincident edges
CAMERAS = {
    "south": ((1, 0, 0), (0, 0, 1), (0, 1, 0)),
    "north": ((-1, 0, 0), (0, 0, 1), (0, -1, 0)),
    "east": ((0, 1, 0), (0, 0, 1), (-1, 0, 0)),
    "west": ((0, -1, 0), (0, 0, 1), (1, 0, 0)),
    "plan": ((1, 0, 0), (0, 1, 0), (0, 0, -1)),
}


def _libraries() -> tuple:
    try:
        from shapely import STRtree
        from shapely.geometry import LineString, Polygon
        from shapely.ops import polygonize, unary_union
    except ImportError as exc:
        raise TeeError(
            "architecture_drawing_dependency",
            "Coordinated drawings require Shapely from TEE's extract dependencies.",
            fix="Install the configured TEE extract dependencies, then retry.",
        ) from exc
    return STRtree, LineString, Polygon, polygonize, unary_union


def project(point: list[float], camera: str) -> list[float]:
    return [sum(a * b for a, b in zip(point, axis, strict=True)) for axis in CAMERAS[camera]]


def _key(point: list[float]) -> tuple[float, ...]:
    return tuple(round(float(v), 7) for v in point)


def _group(mesh: dict[str, Any]) -> tuple:
    # Wall prism decomposition is an implementation detail. Cabinet panel and
    # assembly material boundaries are design information and retain their IDs.
    part = None if mesh["kind"] == "wall" else mesh.get("part")
    return mesh["id"], mesh["kind"], part, mesh.get("material_role")


def _depth_plane(points: list[list[float]]) -> tuple[float, float, float] | None:
    a, b, c = points[:3]
    dx, dy = b[0] - a[0], b[1] - a[1]
    ex, ey = c[0] - a[0], c[1] - a[1]
    determinant = dx * ey - dy * ex
    if abs(determinant) < TOL * TOL:
        return None  # edge-on faces have no projected area
    dz, ez = b[2] - a[2], c[2] - a[2]
    u, v = (dz * ey - dy * ez) / determinant, (dx * ez - dz * ex) / determinant
    return u, v, a[2] - u * a[0] - v * a[1]


def _clip_depth(points: list[list[float]], cut: float) -> list[list[float]]:
    result = []
    for a, b in zip(points, points[1:] + points[:1], strict=True):
        ia, ib = a[2] >= cut - TOL, b[2] >= cut - TOL
        if ia:
            result.append(a)
        if ia != ib:
            t = (cut - a[2]) / (b[2] - a[2])
            result.append([a[i] + t * (b[i] - a[i]) for i in range(3)])
    return result


def _section_segments(points: list[list[float]], cut: float) -> list[list[float]] | None:
    if all(abs(p[2] - cut) < TOL for p in points):
        return None
    hits = {}
    for a, b in zip(points, points[1:] + points[:1], strict=True):
        da, db = a[2] - cut, b[2] - cut
        if abs(da) < TOL:
            hits[_key(a[:2])] = a[:2]
        if da * db < 0:
            t = da / (da - db)
            p = [a[i] + t * (b[i] - a[i]) for i in range(2)]
            hits[_key(p)] = list(_key(p))
    if len(hits) == 2:
        values = list(hits.values())
        if math.dist(*values) > TOL:
            return values
    return None


def _inside_segments(point: tuple[float, float], segments: list) -> bool:
    x, y = point
    crossings = 0
    for a, b in segments:
        if (a[1] > y) != (b[1] > y):
            at = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            crossings += at > x
    return bool(crossings % 2)


def _polygons(geometry: Any) -> list:
    if geometry.is_empty:
        return []
    if geometry.geom_type == "Polygon":
        return [geometry]
    return [p for child in getattr(geometry, "geoms", []) for p in _polygons(child)]


def surfaces(meshes: list[dict], camera: str, cut_depth: float | None = None) -> list[dict]:
    """Return united projected surfaces with affine depth and optional cut caps."""
    _, LineString, Polygon, polygonize, unary_union = _libraries()
    grouped: dict[tuple, list] = defaultdict(list)
    caps: dict[tuple, list] = defaultdict(list)
    source = {}
    face_count = 0
    for mesh in meshes:
        if mesh["kind"] == "space":
            continue
        group = _group(mesh)
        source[group] = {k: mesh.get(k) for k in ("id", "kind", "material_role")}
        source[group]["part"] = group[2]
        vertices = [project(point, camera) for point in mesh["vertices"]]
        cuts = {}
        for face in mesh["faces"]:
            points = [vertices[index] for index in face]
            face_count += 1
            if face_count > 100000:
                raise TeeError(
                    "architecture_drawing_limit",
                    "View exceeds 100,000 source triangles.",
                    fix="Split the document into smaller drawing scopes.",
                )
            plane = _depth_plane(points)
            if cut_depth is not None:
                segment = _section_segments(points, cut_depth)
                if segment:
                    cuts[tuple(sorted(_key(p) for p in segment))] = segment
                points = _clip_depth(points, cut_depth)
            if plane is None or len(points) < 3:
                continue
            polygon = Polygon([p[:2] for p in points])
            if polygon.area > TOL * TOL:
                plane_key = tuple(round(v, 8) for v in plane)
                grouped[(group, plane_key)].append(polygon)
        if cuts:
            segments = list(cuts.values())
            polygons = list(polygonize(unary_union([LineString(s) for s in segments])))
            # Nested closed loops describe holes. Polygonize also returns each
            # hole interior as a face, so use even/odd material parity to omit it.
            caps[group].extend(
                p
                for p in polygons
                if _inside_segments(p.representative_point().coords[0], segments)
            )
    result = []
    for (group, plane), parts in grouped.items():
        for polygon in _polygons(unary_union(parts)):
            result.append({**source[group], "polygon": polygon, "plane": plane, "role": "context"})
    if cut_depth is not None:
        for group, parts in caps.items():
            for polygon in _polygons(unary_union(parts)):
                result.append(
                    {**source[group], "polygon": polygon, "plane": (0, 0, cut_depth), "role": "cut"}
                )
    return result


def _line_parts(geometry: Any) -> list:
    if geometry.is_empty:
        return []
    if geometry.geom_type == "LineString":
        return [geometry]
    return [line for child in getattr(geometry, "geoms", []) for line in _line_parts(child)]


def _depth(plane: tuple, point: list[float]) -> float:
    return plane[0] * point[0] + plane[1] * point[1] + plane[2]


def _hidden_interval(first: float, last: float, d0: float, d1: float) -> tuple | None:
    """Portion on which blocker depth minus edge depth is strictly negative."""
    a, b = d0 + (d1 - d0) * first, d0 + (d1 - d0) * last
    if a >= -TOL and b >= -TOL:
        return None
    if a < -TOL and b < -TOL:
        return first, last
    crossing = (-TOL - d0) / (d1 - d0)
    return (first, crossing) if a < -TOL else (crossing, last)


def _remaining(intervals: list[tuple]) -> list[tuple]:
    visible, cursor = [], 0.0
    for first, last in sorted(intervals):
        first, last = max(0.0, first), min(1.0, last)
        if first > cursor + 1e-10:
            visible.append((cursor, first))
        cursor = max(cursor, last)
    if cursor < 1 - 1e-10:
        visible.append((cursor, 1.0))
    return visible


def visible_edges(meshes: list[dict], camera: str, cut_depth: float | None = None) -> list[dict]:
    """Exact edge-interval visibility; small strict tolerance in model units."""
    STRtree, LineString, _, _, _ = _libraries()
    faces = surfaces(meshes, camera, cut_depth)
    if not faces:
        return []
    tree = STRtree([f["polygon"] for f in faces])
    output = {}
    for face_index, face in enumerate(faces):
        polygon = face["polygon"]
        for ring in [polygon.exterior, *polygon.interiors]:
            points = list(ring.coords)
            for start, end in itertools.pairwise(points):
                a, b = list(start), list(end)
                delta = [b[i] - a[i] for i in range(2)]
                length2 = sum(v * v for v in delta)
                if length2 <= TOL * TOL:
                    continue
                edge = LineString([a, b])
                hidden = []
                for index in tree.query(edge, predicate="intersects"):
                    if int(index) == face_index:
                        continue
                    other = faces[int(index)]
                    d0 = _depth(other["plane"], a) - _depth(face["plane"], a)
                    d1 = _depth(other["plane"], b) - _depth(face["plane"], b)
                    if min(d0, d1) >= -TOL:
                        continue
                    for part in _line_parts(edge.intersection(other["polygon"])):
                        parameters = [
                            sum((p[i] - a[i]) * delta[i] for i in range(2)) / length2
                            for p in part.coords
                        ]
                        interval = _hidden_interval(min(parameters), max(parameters), d0, d1)
                        if interval:
                            hidden.append(interval)
                for first, last in _remaining(hidden):
                    ends = [[a[i] + t * delta[i] for i in range(2)] for t in (first, last)]
                    if math.dist(*ends) <= TOL:
                        continue
                    key = tuple(sorted(_key(p) for p in ends))
                    row = {k: face[k] for k in ("id", "kind", "part", "material_role", "role")}
                    row["points"] = ends
                    # Coincident cap/context boundaries must use the cut style.
                    if key not in output or row["role"] == "cut":
                        output[key] = row
    return list(output.values())
