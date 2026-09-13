"""Geometric usable-space scenarios with explicit design targets and witnesses.

No jurisdiction thresholds, environmental simulation or safe-egress decisions
are inferred. Route candidates use polygon geometry; acceptance remeasures the
whole resulting path against original boundaries and obstacle footprints.
"""

from __future__ import annotations

import heapq
import math
from collections import defaultdict

from .model import ArchitectureError, Document, _point, _polygon, number, positive
from .spatial import base_elevation, space_environment, space_geometry


def _polygons(shape):
    if shape.is_empty:
        return []
    if shape.geom_type == "Polygon":
        return [shape]
    return [p for g in getattr(shape, "geoms", []) for p in _polygons(g)]


def _project(mesh):
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    vertices = mesh["vertices"]
    pieces = [Polygon([vertices[i][:2] for i in face]) for face in mesh["faces"]]
    return unary_union([p for p in pieces if p.area > 1e-7])


def _route(region, obstacles, start, end, width):
    from shapely.geometry import LineString, Point

    radius = width / 2
    free = region.buffer(-radius, join_style="mitre").difference(
        obstacles.buffer(radius, join_style="mitre")
    )
    component = next(
        (p for p in _polygons(free) if p.covers(Point(start)) and p.covers(Point(end))), None
    )
    if component is None:
        return {"status": "no_route_in_conservative_region", "path_mm": [], "length_mm": None}
    corners = [
        list(p) for ring in [component.exterior, *component.interiors] for p in ring.coords[:-1]
    ]
    points = [start, end, *corners]
    if len(points) > 256:
        return {"status": "geometry_budget_exceeded", "path_mm": [], "length_mm": None}
    graph = defaultdict(list)
    for i, a in enumerate(points):
        for j in range(i + 1, len(points)):
            line = LineString([a, points[j]])
            if component.covers(line):
                length = line.length
                graph[i].append((j, length))
                graph[j].append((i, length))
    distance = {0: 0.0}
    previous = {}
    queue = [(0.0, 0)]
    while queue:
        cost, node = heapq.heappop(queue)
        if cost != distance[node]:
            continue
        if node == 1:
            break
        for target, length in graph[node]:
            value = cost + length
            if value < distance.get(target, math.inf):
                distance[target] = value
                previous[target] = node
                heapq.heappush(queue, (value, target))
    if 1 not in distance:
        return {"status": "candidate_path_not_found", "path_mm": [], "length_mm": None}
    ids = [1]
    while ids[-1] != 0:
        ids.append(previous[ids[-1]])
    path = [points[i] for i in reversed(ids)]
    line = LineString(path)
    clearance = min(
        line.distance(region.boundary),
        line.distance(obstacles) if not obstacles.is_empty else math.inf,
    )
    valid = region.covers(line) and clearance + 1e-7 >= radius
    return {
        "status": "meets_geometric_target" if valid else "candidate_clearance_failed",
        "path_mm": path,
        "length_mm": line.length,
        "minimum_plan_clearance_mm": clearance,
        "basis": "entire path distance to original geometry; not sampled grid or legal egress",
    }


def evaluate(state: dict) -> dict:
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    from .exchange import preview

    document = Document.from_dict(state)
    entities = document.entities
    spec = state["project"]["facts"].get("performance", {})
    if not isinstance(spec, dict) or set(spec) - {
        "clearance_width_mm",
        "clearance_height_mm",
        "routes",
        "basis",
        "reference_obstacles",
    }:
        raise ArchitectureError("performance needs explicit clearance targets, routes and a basis.")
    width, height = spec.get("clearance_width_mm"), spec.get("clearance_height_mm")
    if (width is None) != (height is None):
        raise ArchitectureError(
            "Set clearance_width_mm and clearance_height_mm together, or omit both."
        )
    if width is not None:
        width = positive(width, "performance.clearance_width_mm")
        height = positive(height, "performance.clearance_height_mm")
    routes = spec.get("routes", [])
    if not isinstance(routes, list) or len(routes) > 64:
        raise ArchitectureError("performance.routes supports at most 64 explicit routes.")
    meshes = preview(state)["meshes"]
    projected = []
    references = spec.get("reference_obstacles", [])
    if not isinstance(references, list) or len(references) > 200:
        raise ArchitectureError("performance.reference_obstacles supports at most 200 prisms.")
    reference_ids = set()
    for reference in references:
        if not isinstance(reference, dict) or set(reference) != {
            "id",
            "polygon",
            "base_world_mm",
            "height_mm",
            "source",
            "basis",
        }:
            raise ArchitectureError(
                "Reference obstacle needs id, polygon, base_world_mm, height_mm, source and basis."
            )
        identifier = reference["id"]
        if (
            not isinstance(identifier, str)
            or not identifier
            or len(identifier) > 80
            or identifier in reference_ids
            or identifier in entities
        ):
            raise ArchitectureError(
                "Reference obstacle id must be unique and distinct from model entities."
            )
        reference_ids.add(identifier)
        for field in ("source", "basis"):
            if not isinstance(reference[field], str) or not reference[field].strip():
                raise ArchitectureError(
                    "Reference obstacle source and basis must be nonempty text."
                )
        _polygon(reference["polygon"], "reference_obstacle.polygon")
        base = number(reference["base_world_mm"], "reference_obstacle.base_world_mm")
        height_value = positive(reference["height_mm"], "reference_obstacle.height_mm")
        projected.append((identifier, base, base + height_value, Polygon(reference["polygon"])))
    roof_shapes = []
    for mesh in meshes:
        if mesh["kind"] == "space" or mesh.get("nonphysical"):
            continue
        footprint = _project(mesh)
        if footprint.is_empty:
            continue
        zs = [p[2] for p in mesh["vertices"]]
        projected.append((mesh["id"], min(zs), max(zs), footprint))
        if mesh["kind"] == "roof":
            roof_shapes.append((min(zs), footprint))
    space_rows = []
    regions = {}
    obstacles = {}
    bases = {}
    for identifier, space in sorted(entities.items()):
        if space["kind"] != "space":
            continue
        region = space_geometry(space)
        base = base_elevation(space, entities)
        overlapping = [
            (eid, shape)
            for eid, z0, z1, shape in projected
            if z1 > base + 1e-7
            and z0 < base + (height if height is not None else 1) - 1e-7
            and shape.intersects(region)
        ]
        solid = unary_union([shape for _, shape in overlapping]) if overlapping else Polygon()
        blocked = region.intersection(solid)
        free = region.difference(solid)
        cover = unary_union([shape for z0, shape in roof_shapes if z0 > base])
        uncovered = region.difference(cover).area
        environment = space_environment(space)
        centre = (
            region.buffer(-width / 2, join_style="mitre").difference(
                solid.buffer(width / 2, join_style="mitre")
            )
            if width
            else None
        )
        space_rows.append(
            {
                "id": identifier,
                "environment": environment,
                "gross_footprint_m2": region.area / 1e6,
                "obstacle_projection_m2": blocked.area / 1e6,
                "remaining_projection_m2": free.area / 1e6,
                "obstacle_ids": sorted({eid for eid, _ in overlapping}),
                "centre_region_m2": centre.area / 1e6 if centre is not None else None,
                "centre_components": len(_polygons(centre)) if centre is not None else None,
                "uncovered_by_model_roofs_m2": uncovered / 1e6,
                "roof_requirement": "not_inferred_for_exterior"
                if environment == "exterior"
                else "enclosure_verification_required",
                "scope": "conservative solid projections in the declared height band"
                if height
                else "floor contact projection only; circulation targets unset",
            }
        )
        regions[identifier] = region
        obstacles[identifier] = solid
        bases[identifier] = base
    route_rows = []
    seen = set()
    for route in routes:
        if not isinstance(route, dict) or set(route) != {"id", "space_id", "start_mm", "end_mm"}:
            raise ArchitectureError(
                "Each route needs id, space_id, start_mm and end_mm (XY model mm)."
            )
        identifier = route["id"]
        space = route["space_id"]
        if (
            not isinstance(identifier, str)
            or not identifier
            or len(identifier) > 80
            or identifier in seen
        ):
            raise ArchitectureError("Route id must be unique nonempty text up to 80 characters.")
        seen.add(identifier)
        if not isinstance(space, str) or space not in regions:
            raise ArchitectureError("Route space_id must name an authored space.")
        for key in ["start_mm", "end_mm"]:
            _point(route[key], "route." + key)
        result = (
            {"status": "targets_unset", "path_mm": [], "length_mm": None}
            if width is None
            else _route(regions[space], obstacles[space], route["start_mm"], route["end_mm"], width)
        )
        route_rows.append(
            {"id": identifier, "space_id": space, "floor_world_mm": bases[space], **result}
        )
    return {
        "revision": document.revision,
        "spaces": space_rows,
        "routes": route_rows,
        "targets": {
            "width_mm": width,
            "height_mm": height,
            "basis": spec.get("basis", "not supplied"),
            "jurisdiction_approval": False,
            "reference_obstacle_count": len(references),
        },
        "unevaluated": [
            "thermal and moisture performance",
            "daylight and glare",
            "natural/mechanical ventilation",
            "acoustics",
            "structural capacity",
            "fire and site egress",
            "occupancy and local code",
        ],
        "scope": (
            "Authored geometry and sourced reference prisms; "
            "conservative height-band projections. "
            "Sloped solids may be over-restricted; absent objects do not prove clearance."
        ),
    }
