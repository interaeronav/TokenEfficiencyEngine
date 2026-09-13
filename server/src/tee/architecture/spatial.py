"""Spatial identity and placements shared by modeling, schedules and exchange.

A multipart room remains one semantic space. Polygon parts represent disjoint
exterior rings, never material solids, implicit storeys or inferred survey facts.
"""

from __future__ import annotations

from typing import Any


def base_elevation(entity: dict, entities: dict) -> float:
    """World base elevation in mm; optional offset is relative to the real storey."""
    return entities[entity["storey"]]["elevation"] + entity.get("base_offset", 0)


def space_polygons(entity: dict) -> list[list[list[float]]]:
    """All authored exterior rings belonging to one space identity."""
    return [entity["polygon"], *entity.get("additional_polygons", [])]


def space_geometry(entity: dict) -> Any:
    from shapely.geometry import MultiPolygon, Polygon

    parts = [Polygon(ring) for ring in space_polygons(entity)]
    return parts[0] if len(parts) == 1 else MultiPolygon(parts)


def space_area_mm2(entity: dict) -> float:
    from .model import polygon_area

    return sum(abs(polygon_area(ring)) for ring in space_polygons(entity))


def space_environment(entity: dict) -> str:
    """No location is inferred from a name, canopy, height or an absent flag."""
    if "environment" in entity:
        return entity["environment"]
    legacy = entity.get("properties", {}).get("outdoor")
    return "exterior" if legacy is True else "interior" if legacy is False else "unclassified"


def boundary_mesh(entity: dict, entities: dict) -> dict:
    """A zero-thickness reference surface, never a closed physical volume."""
    z = base_elevation(entity, entities)
    a, b = entity["start"], entity["end"]
    return {
        "vertices": [[*a, z], [*b, z], [*b, z + entity["height"]], [*a, z + entity["height"]]],
        "faces": [[0, 1, 2], [0, 2, 3]],
    }
