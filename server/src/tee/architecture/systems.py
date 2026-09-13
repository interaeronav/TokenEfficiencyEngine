"""Parametric roof solids and straight stairs, in explicit project millimetres.

Legacy roofs use edge 0->1 as pitch direction and locate the underside at base.
Explicit patches instead locate their TOP vertices above base and extend down.
Roof thickness is NORMAL to each plane, with vertical shared-edge cuts. Stairs
have one tread per riser: the last tread is flush with the destination level.
An optional landing extends beyond that tread. Neither system engineers itself.
"""

from __future__ import annotations

import math
import re
from typing import Any

from .model import ArchitectureError, _polygon, number, polygon_area, positive


def roof_frame(entity: dict[str, Any]) -> tuple:
    polygon = entity["polygon"]
    if len(polygon) != 4:
        raise ArchitectureError(
            "ak_roof", "Pitched roofs require a rectangular footprint; flat roofs accept polygons."
        )
    a, b, c, d = polygon
    length, width = math.dist(a, b), math.dist(a, d)
    if min(length, width) <= 1e-6:
        raise ArchitectureError("ak_roof", "Roof footprint edges must have positive length.")
    u = [(b[i] - a[i]) / length for i in range(2)]
    v = [(d[i] - a[i]) / width for i in range(2)]
    if (
        abs(sum(u[i] * v[i] for i in range(2))) > 1e-9
        or math.dist(c, [b[i] + d[i] - a[i] for i in range(2)]) > 1e-6
    ):
        raise ArchitectureError(
            "ak_roof", "Pitched roof footprint must be a rectangle in boundary order."
        )
    return a, u, v, length, width


def validate_roof(entity: dict[str, Any]) -> None:
    form = entity.get("form")
    if not isinstance(form, str) or form not in {"flat", "mono", "gable", "planes"}:
        raise ArchitectureError("ak_roof", "Roof form must be flat, mono, gable or planes.")
    if form == "planes":
        if number(entity.get("pitch_deg", 0), "roof.pitch_deg") != 0:
            raise ArchitectureError(
                "ak_roof", "Explicit roof planes derive pitch from elevations; omit pitch_deg."
            )
        _validate_roof_planes(entity)
        return
    if entity.get("planes") is not None:
        raise ArchitectureError("ak_roof", "Only form=planes can carry explicit roof planes.")
    if form == "flat":
        if number(entity.get("pitch_deg", 0), "roof.pitch_deg") != 0:
            raise ArchitectureError("ak_roof", "Flat roof pitch must be zero or omitted.")
        return
    roof_frame(entity)
    pitch = positive(entity.get("pitch_deg"), "roof.pitch_deg")
    if pitch >= 80:
        raise ArchitectureError(
            "ak_roof", "Pitched roof pitch_deg must be greater than 0 and below 80."
        )


def roof_planes(entity: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve planar TOP elevations above roof base; no symmetric-roof inference.

    Coordinates are translated before solving to retain accuracy far from the
    origin. The widest available basis avoids a near-collinear leading triple.
    Validation calls this helper after structural field checks.
    """
    result = []
    for patch in entity["planes"]:
        polygon, heights = patch["polygon"], patch["elevations"]
        a = polygon[0]
        bi = max(range(1, len(polygon)), key=lambda i: math.dist(a, polygon[i]))
        bx, by = [polygon[bi][i] - a[i] for i in range(2)]
        ci = max(
            range(1, len(polygon)),
            key=lambda i: abs(bx * (polygon[i][1] - a[1]) - by * (polygon[i][0] - a[0])),
        )
        cx, cy = [polygon[ci][i] - a[i] for i in range(2)]
        determinant = bx * cy - by * cx
        if abs(determinant) <= 1e-12:
            raise ArchitectureError("ak_roof_planes", "Roof patch has no stable planar basis.")
        bz, cz = heights[bi] - heights[0], heights[ci] - heights[0]
        gradient = [(bz * cy - by * cz) / determinant, (bx * cz - bz * cx) / determinant]
        factor = math.sqrt(1 + sum(value * value for value in gradient))
        result.append(
            {
                "id": patch["id"],
                "polygon": polygon,
                "elevations": heights,
                "anchor": [*a, heights[0]],
                "gradient": gradient,
                "normal_factor": factor,
                "pitch_deg": math.degrees(math.atan(math.hypot(*gradient))),
            }
        )
    return result


def roof_plane_height(plane: dict[str, Any], point: list[float] | tuple[float, ...]) -> float:
    return plane["anchor"][2] + sum(
        plane["gradient"][i] * (point[i] - plane["anchor"][i]) for i in range(2)
    )


def _validate_roof_planes(entity: dict[str, Any]) -> None:
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    patches = entity.get("planes")
    if not isinstance(patches, list) or not 1 <= len(patches) <= 32:
        raise ArchitectureError("ak_roof_planes", "Roof planes needs 1-32 named planar patches.")
    seen = set()
    polygons = []
    for patch in patches:
        if not isinstance(patch, dict) or set(patch) != {"id", "polygon", "elevations"}:
            raise ArchitectureError(
                "ak_roof_planes", "Each roof plane needs id, polygon and top elevations."
            )
        identifier = patch["id"]
        if (
            not isinstance(identifier, str)
            or re.fullmatch(r"[A-Za-z0-9_-]{1,80}", identifier) is None
            or identifier in seen
        ):
            raise ArchitectureError(
                "ak_roof_planes", "Roof plane IDs must be distinct safe strings."
            )
        seen.add(identifier)
        _polygon(patch["polygon"], f"roof.planes.{identifier}.polygon")
        heights = patch["elevations"]
        if not isinstance(heights, list) or len(heights) != len(patch["polygon"]):
            raise ArchitectureError(
                "ak_roof_planes", "Every patch vertex needs one top elevation in mm."
            )
        for height in heights:
            number(height, f"roof.planes.{identifier}.elevations")
        polygons.append(Polygon(patch["polygon"]))
    resolved = roof_planes(entity)
    for patch in resolved:
        if patch["pitch_deg"] >= 80:
            raise ArchitectureError(
                "ak_roof_planes", "Explicit roof plane pitch must be below 80 degrees."
            )
        if any(
            abs(roof_plane_height(patch, xy) - z) > 1e-6
            for xy, z in zip(patch["polygon"], patch["elevations"], strict=True)
        ):
            raise ArchitectureError(
                "ak_roof_planes", f"Roof patch {patch['id']} top vertices are not coplanar."
            )
    parent = Polygon(entity["polygon"])
    union = unary_union(polygons)
    tolerance = max(1e-6, parent.area * 1e-12)
    if union.symmetric_difference(parent).area > tolerance:
        raise ArchitectureError(
            "ak_roof_planes",
            "Roof patch union must exactly cover the parent footprint; no holes or outside pieces.",
        )
    for i, first in enumerate(polygons):
        for j in range(i + 1, len(polygons)):
            other = polygons[j]
            if first.intersection(other).area > tolerance:
                raise ArchitectureError(
                    "ak_roof_planes",
                    "Roof patches overlap in plan; divide them at the shared boundary.",
                )
            contact = first.boundary.intersection(other.boundary)
            members = [contact]
            while members:
                member = members.pop()
                if hasattr(member, "geoms"):
                    members.extend(member.geoms)
                    continue
                for point in member.coords:
                    if (
                        abs(
                            roof_plane_height(resolved[i], point)
                            - roof_plane_height(resolved[j], point)
                        )
                        > 1e-6
                    ):
                        raise ArchitectureError(
                            "ak_roof_planes",
                            "Roof patch TOP elevations disagree at a shared boundary.",
                        )


def stair_dimensions(entity: dict[str, Any], entities: dict[str, Any]) -> dict[str, Any]:
    """Resolve both references before arithmetic, regardless of entity map order."""
    levels = []
    for field in ("storey", "top_storey"):
        reference = entity[field]
        level = entities.get(reference) if isinstance(reference, str) else None
        if not isinstance(level, dict) or level.get("kind") != "storey":
            raise ArchitectureError(
                "ak_reference", f"Stair {entity['id']}.{field} must reference a storey."
            )
        levels.append(number(level.get("elevation"), f"{reference}.elevation"))
    rise = positive(levels[1] - levels[0], "stair.total_rise")
    count = entity["riser_count"]
    if type(count) is not int or not 2 <= count <= 64:
        raise ArchitectureError("ak_stair", "Stair riser_count must be an integer from 2 to 64.")
    for field in ("width", "going", "waist_thickness"):
        positive(entity[field], f"stair.{field}")
    number(entity["landing_depth"], "stair.landing_depth", minimum=0)
    number(entity["direction_deg"], "stair.direction_deg")
    riser = rise / count
    angle = math.atan2(riser, entity["going"])
    waist_vertical = entity["waist_thickness"] / math.cos(angle)
    run = count * entity["going"]
    return {
        "bottom_world_mm": levels[0],
        "top_world_mm": levels[1],
        "total_rise_mm": rise,
        "riser_count": count,
        "tread_count": count,
        "riser_height_mm": riser,
        "going_mm": entity["going"],
        "flight_run_mm": run,
        "width_mm": entity["width"],
        "landing_depth_mm": entity["landing_depth"],
        "waist_normal_mm": entity["waist_thickness"],
        "waist_vertical_mm": waist_vertical,
        "pitch_deg": math.degrees(angle),
        "volume_m3": entity["width"]
        * (run * (waist_vertical + riser / 2) + entity["landing_depth"] * entity["waist_thickness"])
        / 1e9,
        "tread_area_m2": entity["width"] * run / 1e6,
        "landing_area_m2": entity["width"] * entity["landing_depth"] / 1e6,
        "quantity_basis": (
            "One tread per riser; last tread flush with top level. Landing separate. Monolithic"
            " solids; connections excluded."
        ),
    }


def roof_quantities(entity: dict[str, Any], elevation: float) -> dict[str, Any]:
    if entity["form"] == "planes":
        base = elevation + entity["base_height"]
        planes = []
        for patch in roof_planes(entity):
            area = abs(polygon_area(patch["polygon"])) / 1e6
            depth = entity["thickness"] * patch["normal_factor"]
            planes.append(
                {
                    "id": patch["id"],
                    "pitch_deg": patch["pitch_deg"],
                    "plan_area_m2": area,
                    "slope_area_m2": area * patch["normal_factor"],
                    "volume_m3": area * depth / 1000,
                    "top_min_world_mm": base + min(patch["elevations"]),
                    "top_max_world_mm": base + max(patch["elevations"]),
                    "underside_min_world_mm": base + min(patch["elevations"]) - depth,
                    "underside_max_world_mm": base + max(patch["elevations"]) - depth,
                    "normal_thickness_mm": entity["thickness"],
                    "vertical_depth_mm": depth,
                }
            )
        return {
            "form": "planes",
            "pitch_deg": None,
            "plane_count": len(planes),
            "reference_surface": "top",
            "planes": planes,
            "plan_area_m2": sum(p["plan_area_m2"] for p in planes),
            "slope_area_m2": sum(p["slope_area_m2"] for p in planes),
            "normal_thickness_mm": entity["thickness"],
            "volume_m3": sum(p["volume_m3"] for p in planes),
            "eave_underside_world_mm": None,
            "lowest_underside_world_mm": min(p["underside_min_world_mm"] for p in planes),
            "highest_top_world_mm": max(p["top_max_world_mm"] for p in planes),
            "quantity_basis": (
                "Explicit top planes; normal thickness extrudes downward with vertical "
                "shared-edge cuts. Nominal geometric envelope only; physical profile, steel "
                "gauge, mass, openings and engineered junctions are not inferred."
            ),
        }
    pitch = entity.get("pitch_deg", 0)
    area = abs(polygon_area(entity["polygon"])) / 1e6
    cosine = math.cos(math.radians(pitch))
    rise = 0.0
    if entity["form"] != "flat":
        length = roof_frame(entity)[3]
        rise = length * math.tan(math.radians(pitch)) / (2 if entity["form"] == "gable" else 1)
    return {
        "form": entity["form"],
        "pitch_deg": pitch,
        "plan_area_m2": area,
        "slope_area_m2": area / cosine,
        "normal_thickness_mm": entity["thickness"],
        "volume_m3": area / cosine * entity["thickness"] / 1000,
        "eave_underside_world_mm": elevation + entity["base_height"],
        "highest_top_world_mm": elevation
        + entity["base_height"]
        + rise
        + entity["thickness"] / cosine,
        "quantity_basis": (
            "Footprint includes eaves; normal thickness with vertical edge/ridge cuts; no "
            "openings or junction deductions."
        ),
    }


def roof_meshes(entity: dict[str, Any], elevation: float) -> list[dict[str, Any]]:
    from .exchange import _prism_mesh

    if entity["form"] == "planes":
        meshes = []
        base = elevation + entity["base_height"]
        for plane in roof_planes(entity):
            depth = entity["thickness"] * plane["normal_factor"]
            mesh = _prism_mesh(plane["polygon"], -depth, depth)
            mesh["vertices"] = [
                [x, y, base + roof_plane_height(plane, [x, y]) + z] for x, y, z in mesh["vertices"]
            ]
            meshes.append({"part": "plane-" + plane["id"], **mesh})
        return meshes
    if entity["form"] == "flat":
        return [
            {
                "part": 0,
                **_prism_mesh(
                    entity["polygon"], elevation + entity["base_height"], entity["thickness"]
                ),
            }
        ]
    a, u, v, length, width = roof_frame(entity)
    slope = math.tan(math.radians(entity["pitch_deg"]))
    thickness_z = entity["thickness"] / math.cos(math.radians(entity["pitch_deg"]))
    runs = [(0, length)] if entity["form"] == "mono" else [(0, length / 2), (length / 2, length)]
    meshes = []
    for index, (start, end) in enumerate(runs):
        mesh = _prism_mesh([[start, 0], [end, 0], [end, width], [start, width]], 0, thickness_z)
        points = []
        for x, y, z in mesh["vertices"]:
            rise = (x if index == 0 else length - x) * slope
            points.append(
                [
                    a[0] + u[0] * x + v[0] * y,
                    a[1] + u[1] * x + v[1] * y,
                    elevation + entity["base_height"] + rise + z,
                ]
            )
        # Clockwise footprints reflect the local basis: preserve outward winding.
        if u[0] * v[1] - u[1] * v[0] < 0:
            mesh["faces"] = [list(reversed(face)) for face in mesh["faces"]]
        meshes.append({"part": f"slope-{index + 1}", "vertices": points, "faces": mesh["faces"]})
    return meshes


def stair_meshes(entity: dict[str, Any], entities: dict[str, Any]) -> list[dict[str, Any]]:
    from .exchange import _prism_mesh

    dims = stair_dimensions(entity, entities)
    count, riser = dims["riser_count"], dims["riser_height_mm"]
    going, width, run = entity["going"], entity["width"], dims["flight_run_mm"]
    profile = [[0, -dims["waist_vertical_mm"]], [0, riser]]
    for i in range(1, count + 1):
        profile.append([i * going, i * riser])
        if i != count:
            profile.append([i * going, (i + 1) * riser])
    profile.append([run, dims["total_rise_mm"] - dims["waist_vertical_mm"]])
    flight = _prism_mesh(profile, 0, width)
    # Rotate the extrusion axis into width without reflecting the closed solid.
    flight["vertices"] = [[x, width - across, z] for x, z, across in flight["vertices"]]
    meshes = [{"part": "flight", **flight}]
    landing = entity["landing_depth"]
    if landing:
        meshes.append(
            {
                "part": "landing",
                **_prism_mesh(
                    [[run, 0], [run + landing, 0], [run + landing, width], [run, width]],
                    dims["total_rise_mm"] - entity["waist_thickness"],
                    entity["waist_thickness"],
                ),
            }
        )
    angle = math.radians(entity["direction_deg"])
    c, s = math.cos(angle), math.sin(angle)
    for mesh in meshes:
        mesh["vertices"] = [
            [
                entity["start"][0] + c * x - s * y,
                entity["start"][1] + s * x + c * y,
                dims["bottom_world_mm"] + z,
            ]
            for x, y, z in mesh["vertices"]
        ]
    return meshes
