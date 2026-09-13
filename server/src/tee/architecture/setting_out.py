"""Measured room boundary and aperture references, independent of paper layout.

Authored space polygons are the datum. No finish allowance, survey control,
manufactured frame or usable opening is inferred from that geometry.
"""

from __future__ import annotations

import math
from typing import Any

from .spatial import base_elevation, space_geometry


def room_boundary(entity: dict[str, Any], entities: dict[str, Any]) -> dict[str, Any]:
    from shapely.geometry.polygon import orient

    shape = space_geometry(entity)
    parts = list(shape.geoms) if shape.geom_type == "MultiPolygon" else [shape]
    vertices, dimensions = [], []
    for part_number, part in enumerate(sorted(parts, key=lambda p: p.bounds), 1):
        part = orient(part, sign=1)
        for ring_number, ring in enumerate([part.exterior, *part.interiors]):
            points = [list(p) for p in ring.coords[:-1]]
            # Stable starting corner; retain all authored boundary breaks.
            start = min(range(len(points)), key=lambda i: tuple(points[i]))
            points = points[start:] + points[:start]
            first = len(vertices) + 1
            for index, point in enumerate(points):
                mark = f"P{len(vertices) + 1:02d}"
                vertices.append(
                    {"mark": mark, "xy_mm": point, "part": part_number, "ring": ring_number}
                )
                other = points[(index + 1) % len(points)]
                length = math.dist(point, other)
                target = f"P{first + (index + 1) % len(points):02d}"
                dimensions.append(
                    {
                        "id": f"{entity['id']}:boundary:{mark}-{target}",
                        "entity_id": entity["id"],
                        "from": mark,
                        "to": target,
                        "a": point,
                        "b": other,
                        "value_mm": length,
                        "normal": [(other[1] - point[1]) / length, -(other[0] - point[0]) / length],
                        "offset_paper_mm": 7.0,
                        "basis": "authored room boundary; finish/survey status separate",
                    }
                )
    return {
        "id": entity["id"],
        "storey": entity["storey"],
        "base_world_mm": base_elevation(entity, entities),
        "vertices": vertices,
        "dimensions": dimensions,
        "boundary_length_mm": sum(d["value_mm"] for d in dimensions),
        "basis": "Authored room boundary coordinates and lengths in model mm; not crop extents.",
        "finished_clear_dimensions": "not_established_without_finish_and_assembly_specification",
        "survey_control": "not_verified",
    }


def aperture_references(entities: dict[str, Any], storey: str) -> list[dict[str, Any]]:
    rows = []
    for opening in entities.values():
        if opening["kind"] != "opening":
            continue
        host = entities[opening["wall"]]
        if host["storey"] != storey:
            continue
        length = math.dist(host["start"], host["end"])
        u = [(host["end"][i] - host["start"][i]) / length for i in range(2)]
        a, b = [
            [host["start"][i] + u[i] * distance for i in range(2)]
            for distance in (opening["offset"], opening["offset"] + opening["width"])
        ]
        properties = opening.get("properties", {})
        assembly = properties.get("assembly", {})
        rows.append(
            {
                "id": opening["id"],
                "host": host["id"],
                "a": a,
                "b": b,
                "authored_aperture_width_mm": math.dist(a, b),
                "authored_aperture_height_mm": opening["height"],
                "host_offset_mm": opening["offset"],
                "sill_world_mm": base_elevation(host, entities) + opening["sill"],
                "head_world_mm": base_elevation(host, entities)
                + opening["sill"]
                + opening["height"],
                "nominal_source_width_mm": properties.get("source_nominal_width_mm"),
                "operation": assembly.get("operation"),
                "source_operation": properties.get("source_operation"),
                "clear_opening_width_mm": None,
                "clear_opening_basis": "Requires actual frame, leaf and operation evidence.",
            }
        )
    return rows
