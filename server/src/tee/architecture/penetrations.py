"""Hosted through-slab openings and shared net solids; coordinates are millimetres."""

from __future__ import annotations

from typing import Any

from .model import ArchitectureError


def hosted_openings(slab_id: str, entities: dict) -> list[dict]:
    return [
        e
        for _, e in sorted(entities.items())
        if e["kind"] == "slab_opening" and e["slab"] == slab_id
    ]


def validate_openings(entities: dict) -> None:
    openings = [e for e in entities.values() if e["kind"] == "slab_opening"]
    if not openings:
        return
    from shapely.geometry import Polygon

    checked: dict[str, list] = {}
    for opening in openings:
        host = entities[opening["slab"]]
        shape, boundary = Polygon(opening["polygon"]), Polygon(host["polygon"])
        if not boundary.contains(shape) or boundary.boundary.distance(shape) <= 1e-6:
            raise ArchitectureError(
                "ak_host_bounds",
                f"{opening['id']} must lie strictly inside slab {host['id']}; "
                "edge notches are unsupported.",
            )
        for other, other_shape in checked.get(host["id"], []):
            if shape.distance(other_shape) <= 1e-6:
                raise ArchitectureError(
                    "ak_opening_overlap",
                    f"Slab openings {opening['id']} and {other} touch or overlap.",
                )
        checked.setdefault(host["id"], []).append((opening["id"], shape))


def slab_shape(entity: dict, entities: dict) -> Any:
    from shapely.geometry import Polygon

    return Polygon(
        entity["polygon"], [o["polygon"] for o in hosted_openings(entity["id"], entities)]
    )


def slab_quantities(entity: dict, entities: dict) -> dict:
    from .model import polygon_area

    openings = hosted_openings(entity["id"], entities)
    gross = abs(polygon_area(entity["polygon"])) / 1e6
    removed = sum(abs(polygon_area(o["polygon"])) for o in openings) / 1e6
    return {
        "gross_area_m2": gross,
        "opening_area_m2": removed,
        "net_area_m2": gross - removed,
        "thickness_mm": entity["thickness"],
        "net_volume_m3": (gross - removed) * entity["thickness"] / 1000,
        "removed_volume_m3": removed * entity["thickness"] / 1000,
        "opening_count": len(openings),
        "quantity_basis": "Full-thickness hosted polygon openings deducted; junctions excluded.",
    }


def slab_mesh(entity: dict, entities: dict) -> dict:
    from .spatial import base_elevation

    elevation = base_elevation(entity, entities)
    z, depth = elevation - entity["thickness"], entity["thickness"]
    return profile_mesh(
        entity["polygon"], [o["polygon"] for o in hosted_openings(entity["id"], entities)], z, depth
    )


def profile_mesh(polygon: list, holes: list, z: float, depth: float) -> dict:
    """Watertight prism of a validated profile, shared by slabs and members."""
    from shapely.geometry import Polygon

    from .exchange import _prism_mesh

    if not holes:
        return _prism_mesh(polygon, z, depth)
    import shapely
    from shapely import affinity
    from shapely.geometry.polygon import orient

    if not hasattr(shapely, "constrained_delaunay_triangles") or shapely.geos_version < (3, 10, 0):
        raise ArchitectureError(
            "ak_geometry_dependency", "Slab openings require Shapely 2.1+ with GEOS 3.10+."
        )
    # Work near zero; maintain exact ring vertices across top, bottom and sides.
    ox, oy = polygon[0]
    shape = orient(affinity.translate(Polygon(polygon, holes), -ox, -oy), sign=1)
    triangles = list(shapely.constrained_delaunay_triangles(shape).geoms)
    points: list[tuple] = []
    lookup: dict[tuple, int] = {}

    def index(point: tuple) -> int:
        key = tuple(point[:2])
        if key not in lookup:
            lookup[key] = len(points)
            points.append(key)
        return lookup[key]

    cap = [[index(p) for p in orient(t, sign=1).exterior.coords[:-1]] for t in triangles]
    rings = [[index(p) for p in ring.coords[:-1]] for ring in [shape.exterior, *shape.interiors]]
    n = len(points)
    faces = []
    for a, b, c in cap:
        faces.extend([[c, b, a], [a + n, b + n, c + n]])
    for ring in rings:
        for a, b in zip(ring, ring[1:] + ring[:1], strict=True):
            faces.extend([[a, b, b + n], [a, b + n, a + n]])
    vertices = [[x + ox, y + oy, height] for height in (z, z + depth) for x, y in points]
    return {"vertices": vertices, "faces": faces}
