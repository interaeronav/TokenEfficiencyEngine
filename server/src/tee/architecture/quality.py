"""Model-derived schedules and explicit design review observations.

Room access is a graph of actual authored door portals and space polygons.
Furniture collision review uses conservative door-sweep envelopes, labelled as
potential conflicts rather than a claim of exact motion or legal approval.
"""

from __future__ import annotations

import math
from collections import Counter, deque
from typing import Any

from .model import ArchitectureError, Document, polygon_area
from .spatial import (
    base_elevation,
    space_area_mm2,
    space_environment,
    space_geometry,
    space_polygons,
)


def schedules(state: dict[str, Any]) -> dict[str, Any]:
    document = Document.from_dict(state)
    entities = document.entities
    openings, rooms, walls, cabinets = [], [], [], []
    roofs, stairs, slabs, slab_openings, virtual_boundaries, members = [], [], [], [], [], []
    for identifier, entity in sorted(entities.items()):
        kind = entity["kind"]
        binding = entity.get("properties", {}).get("bim", {})
        common = {"id": identifier, "name": entity["name"], "type_id": binding.get("type_id")}
        if kind == "opening":
            wall = entities[entity["wall"]]
            level = base_elevation(wall, entities)
            local_base = wall.get("base_offset", 0)
            openings.append(
                {
                    **common,
                    "fill": entity["fill"],
                    "host": entity["wall"],
                    "storey": wall["storey"],
                    "width_mm": entity["width"],
                    "height_mm": entity["height"],
                    "sill_above_level_mm": local_base + entity["sill"],
                    "sill_above_host_base_mm": entity["sill"],
                    "head_above_level_mm": local_base + entity["sill"] + entity["height"],
                    "sill_world_mm": level + entity["sill"],
                    "head_world_mm": level + entity["sill"] + entity["height"],
                    "operation": entity.get("properties", {}).get("assembly", {}).get("operation"),
                }
            )
        elif kind == "virtual_boundary":
            z = base_elevation(entity, entities)
            virtual_boundaries.append(
                {
                    **common,
                    "storey": entity["storey"],
                    "width_mm": math.dist(entity["start"], entity["end"]),
                    "height_mm": entity["height"],
                    "base_offset_mm": entity.get("base_offset", 0),
                    "base_world_mm": z,
                    "head_world_mm": z + entity["height"],
                    "space_ids": entity.get("space_ids", []),
                    "semantics": "nonphysical reference boundary",
                    "physical_assembly": "not_represented",
                    "traversability": "not_established",
                }
            )
        elif kind == "space":
            area = space_area_mm2(entity) / 1_000_000
            rooms.append(
                {
                    **common,
                    "storey": entity["storey"],
                    "area_m2": area,
                    "environment": space_environment(entity),
                    "conditioned": entity.get("conditioned"),
                    "volume_basis": "authored reference prism; exterior height is not a ceiling",
                    "enclosed_volume_m3": area * entity["height"] / 1000
                    if space_environment(entity) == "interior"
                    else None,
                    "part_count": len(space_polygons(entity)),
                    "base_offset_mm": entity.get("base_offset", 0),
                    "base_world_mm": base_elevation(entity, entities),
                    "height_mm": entity["height"],
                    "volume_m3": area * entity["height"] / 1000,
                }
            )
        elif kind == "wall":
            length = math.dist(entity["start"], entity["end"])
            holes = [
                o for o in entities.values() if o["kind"] == "opening" and o["wall"] == identifier
            ]
            face = (
                length * entity["height"] - sum(o["width"] * o["height"] for o in holes)
            ) / 1_000_000
            walls.append(
                {
                    **common,
                    "storey": entity["storey"],
                    "base_offset_mm": entity.get("base_offset", 0),
                    "base_world_mm": base_elevation(entity, entities),
                    "centreline_length_mm": length,
                    "thickness_mm": entity["thickness"],
                    "height_mm": entity["height"],
                    "net_centreline_face_m2": face,
                    "quantity_basis": (
                        "Centreline face less opening rectangles; junction adjustments excluded."
                    ),
                }
            )
        elif kind == "member":
            from .members import member_quantities

            members.append({**common, "storey": entity["storey"], **member_quantities(entity)})
        elif kind == "roof":
            from .systems import roof_quantities

            roofs.append(
                {
                    **common,
                    "storey": entity["storey"],
                    **roof_quantities(entity, entities[entity["storey"]]["elevation"]),
                }
            )
        elif kind == "stair":
            from .clearance import stair_clearance
            from .systems import stair_dimensions

            stairs.append(
                {
                    **common,
                    "storey": entity["storey"],
                    "top_storey": entity["top_storey"],
                    **stair_dimensions(entity, entities),
                    "headroom": stair_clearance(entity, entities),
                }
            )
        elif kind == "slab":
            from .penetrations import slab_quantities

            slabs.append(
                {
                    **common,
                    "storey": entity["storey"],
                    "base_offset_mm": entity.get("base_offset", 0),
                    "top_world_mm": base_elevation(entity, entities),
                    "bottom_world_mm": base_elevation(entity, entities) - entity["thickness"],
                    **slab_quantities(entity, entities),
                }
            )
        elif kind == "slab_opening":
            host = entities[entity["slab"]]
            slab_openings.append(
                {
                    **common,
                    "host": entity["slab"],
                    "storey": host["storey"],
                    "area_m2": abs(polygon_area(entity["polygon"])) / 1e6,
                    "through_depth_mm": host["thickness"],
                    "base_offset_mm": host.get("base_offset", 0),
                    "top_world_mm": base_elevation(host, entities),
                    "bottom_world_mm": base_elevation(host, entities) - host["thickness"],
                }
            )
        elif kind == "cabinet":
            from .cabinets import schedule

            cutlist = schedule(entity)
            cabinets.append(
                {
                    **common,
                    "width_mm": entity["width"],
                    "depth_mm": entity["depth"],
                    "height_mm": entity["height"],
                    "panel_count": cutlist["panel_count"],
                    "material": entity["material"],
                    "construction": entity.get("properties", {})
                    .get("construction", {})
                    .get("mode", "legacy frameless"),
                    "manufacturing_release": "not_verified",
                }
            )
    return {
        "revision": document.revision,
        "units": {"length": "mm", "area": "m2", "volume": "m3"},
        "openings": openings,
        "rooms": rooms,
        "walls": walls,
        "cabinets": cabinets,
        "roofs": roofs,
        "stairs": stairs,
        "slabs": slabs,
        "slab_openings": slab_openings,
        "virtual_boundaries": virtual_boundaries,
        "members": members,
        "space_area_m2": sum(room["area_m2"] for room in rooms),
        "room_area_m2": sum(room["area_m2"] for room in rooms if room["environment"] != "exterior"),
        "room_area_basis": "interior plus unclassified footprints; exterior excluded; not GFA",
        "indoor_area_m2": sum(
            room["area_m2"] for room in rooms if room["environment"] == "interior"
        ),
        "outdoor_area_m2": sum(
            room["area_m2"] for room in rooms if room["environment"] == "exterior"
        ),
        "unclassified_area_m2": sum(
            room["area_m2"] for room in rooms if room["environment"] == "unclassified"
        ),
        "conditioned_area_m2": sum(
            room["area_m2"] for room in rooms if room["conditioned"] is True
        ),
    }


def review(state: dict[str, Any], max_issues: int = 100, issue_offset: int = 0) -> dict[str, Any]:
    from shapely import affinity
    from shapely.geometry import LineString, Polygon, box

    if (
        isinstance(max_issues, bool)
        or not isinstance(max_issues, int)
        or not 1 <= max_issues <= 500
    ):
        raise ArchitectureError(
            "architecture_query", "max_issues must be an integer from 1 to 500."
        )
    if type(issue_offset) is not int or issue_offset < 0:
        raise ArchitectureError("architecture_query", "issue_offset must be an integer >= 0.")
    document = Document.from_dict(state)
    entities = document.entities
    spaces = {key: entity for key, entity in entities.items() if entity["kind"] == "space"}
    polygons = {key: space_geometry(entity) for key, entity in spaces.items()}
    graph: dict[str, set[str]] = {key: set() for key in spaces}
    entrances: set[str] = set()
    issues: list[dict] = []
    portals = []

    def issue(code, ids, message, severity="warning"):
        issues.append(
            {"code": code, "entities": sorted(ids), "severity": severity, "message": message}
        )

    for identifier, entity in entities.items():
        if entity["kind"] == "stair":
            from .clearance import stair_clearance

            clearance = stair_clearance(entity, entities)
            if clearance["limiting"] and clearance["limiting"]["solid_intersects_walking_envelope"]:
                issue(
                    "stair_solid_intersection",
                    [identifier, clearance["limiting"]["obstacle_id"]],
                    "An authored slab or roof penetrates the stair walking envelope.",
                    "error",
                )
            if clearance["status"] == "below_target":
                issue(
                    "stair_headroom_below_target",
                    [identifier, clearance["limiting"]["obstacle_id"]],
                    f"Headroom {clearance['minimum_clearance_mm']:.3f} mm is below the explicit "
                    f"design target {clearance['target_mm']:g} mm; inspect the schedule witness.",
                    "error",
                )
            elif clearance["status"] == "target_unset":
                issue(
                    "stair_headroom_target_unset",
                    [identifier],
                    "No design headroom target is set; geometric clearance is reported "
                    "in the stair schedule.",
                )
            issue(
                "stair_design_unverified",
                [identifier],
                (
                    "Slab/roof clearance is measured separately. Railings, other obstacles, "
                    "bearing connections and local stair rules are not verified."
                ),
            )
        elif entity["kind"] == "roof" and entity["form"] != "flat":
            issue(
                "roof_details_unverified",
                [identifier],
                (
                    "Roof geometric envelope only: drainage, weathering, wall junctions, material "
                    "layers, physical profile/gauge and structural design are not verified."
                ),
            )

    for i, first in enumerate(sorted(spaces)):
        for second in sorted(spaces)[i + 1 :]:
            z1, z2 = [base_elevation(spaces[key], entities) for key in (first, second)]
            vertical_overlap = min(
                z1 + spaces[first]["height"], z2 + spaces[second]["height"]
            ) - max(z1, z2)
            if spaces[first]["storey"] == spaces[second]["storey"] and vertical_overlap > 0.01:
                overlap = polygons[first].intersection(polygons[second]).area
                if overlap > 1:
                    issue(
                        "overlapping_spaces",
                        [first, second],
                        f"Room polygons overlap by {overlap / 1e6:.4f} m².",
                        "error",
                    )
    furniture = {}
    for identifier, entity in entities.items():
        if entity["kind"] not in {"cabinet", "furnishing"}:
            continue
        x, y, _ = entity["origin"]
        width, depth = (
            entity["size"][:2]
            if entity["kind"] == "furnishing"
            else (entity["width"], entity["depth"])
        )
        footprint = affinity.rotate(
            box(x, y, x + width, y + depth),
            entity.get("properties", {}).get("rotation_deg", 0),
            origin=(x, y),
        )
        furniture[identifier] = footprint
        containers = [
            key
            for key, room in spaces.items()
            if room["storey"] == entity["storey"] and polygons[key].buffer(0.01).covers(footprint)
        ]
        if spaces and not containers:
            issue(
                "furnishing_outside_space",
                [identifier],
                "The furnishing footprint does not fit wholly within an authored room.",
            )

    for identifier, opening in entities.items():
        if opening["kind"] != "opening" or opening["fill"] != "door":
            continue
        wall = entities[opening["wall"]]
        length = math.dist(wall["start"], wall["end"])
        ux, uy = [(wall["end"][i] - wall["start"][i]) / length for i in (0, 1)]
        nx, ny = -uy, ux
        # Cover the entire opening span on each room side. A midpoint can
        # conceal a room boundary crossing the doorway, so it is insufficient.
        sides, partial = [], []
        for sign in (-1, 1):
            side = LineString(
                [
                    [
                        wall["start"][i]
                        + (ux, uy)[i] * distance
                        + sign * (nx, ny)[i] * (wall["thickness"] / 2 + 1)
                        for i in (0, 1)
                    ]
                    for distance in (opening["offset"], opening["offset"] + opening["width"])
                ]
            )
            full = []
            for key, room in spaces.items():
                if room["storey"] != wall["storey"]:
                    continue
                shape = polygons[key].buffer(0.01)
                if shape.covers(side):
                    full.append(key)
                elif shape.intersection(side).length > 0.01:
                    partial.append(key)
            sides.append(full)
        sill_world = base_elevation(wall, entities) + opening["sill"]
        adjacent_spaces = set(sides[0] + sides[1])
        floor_discontinuity = (
            any(
                abs(base_elevation(spaces[key], entities) - sill_world) > 0.01
                for key in adjacent_spaces
            )
            if adjacent_spaces
            else opening["sill"] > 0.01
        )
        if partial:
            issue(
                "partial_door_space",
                [identifier, *set(partial)],
                "A room covers only part of the doorway width; full-width access is unverified.",
            )
        connected = sorted(set(sides[0] + sides[1]))
        portals.append(
            {
                "door": identifier,
                "spaces": connected,
                "sill_mm": opening["sill"],
                "sill_world_mm": sill_world,
            }
        )
        if floor_discontinuity:
            issue(
                "door_level_discontinuity",
                [identifier],
                (
                    "Door sill and adjacent room floor levels do not coincide; "
                    "a step or threshold detail is "
                    "required before access can be verified."
                ),
            )
        if any(len(side) > 1 for side in sides):
            issue(
                "ambiguous_door_spaces",
                [identifier, *connected],
                "Door sides belong to multiple overlapping spaces.",
                "error",
            )
        elif floor_discontinuity or partial:
            pass
        elif all(sides) and sides[0][0] != sides[1][0]:
            a, b = sides[0][0], sides[1][0]
            graph[a].add(b)
            graph[b].add(a)
        elif len(connected) == 1 and wall.get("properties", {}).get("is_external") is True:
            entrances.add(connected[0])
        elif spaces:
            issue(
                "unresolved_door_access",
                [identifier, *connected],
                "Door lacks two adjacent rooms or an explicitly external wall reference.",
            )
        assembly = opening.get("properties", {}).get("assembly", {})
        if assembly.get("operation") != "swing":
            continue
        sign = 1 if assembly["swing_side"] == "left" else -1
        a = [wall["start"][i] + (ux, uy)[i] * opening["offset"] for i in (0, 1)]
        b = [a[i] + (ux, uy)[i] * opening["width"] for i in (0, 1)]
        # This enclosing quadrilateral deliberately overestimates the actual arc.
        # Intersections are potential clashes for detailed motion review.
        envelope = Polygon(
            [
                a,
                b,
                [b[0] + sign * nx * opening["width"], b[1] + sign * ny * opening["width"]],
                [a[0] + sign * nx * opening["width"], a[1] + sign * ny * opening["width"]],
            ]
        )
        for target, footprint in furniture.items():
            item = entities[target]
            z0 = base_elevation(wall, entities) + opening["sill"]
            item_height = item["size"][2] if item["kind"] == "furnishing" else item["height"]
            vertical_overlap = min(z0 + opening["height"], item["origin"][2] + item_height) - max(
                z0, item["origin"][2]
            )
            if (
                item["storey"] == wall["storey"]
                and vertical_overlap > 0.01
                and envelope.intersection(footprint).area > 1
            ):
                issue(
                    "potential_door_furnishing_conflict",
                    [identifier, target],
                    (
                        "Furnishing intersects the conservative door-sweep envelope; verify "
                        "detailed motion."
                    ),
                )
        clear = opening["width"] - 2 * assembly["frame_width_mm"] - 2 * assembly["clearance_mm"]
        if clear <= 0:
            issue(
                "no_clear_door_width",
                [identifier],
                "Frame and leaf clearances consume the opening width.",
                "error",
            )

    reached, pending = set(entrances), deque(entrances)
    while pending:
        current = pending.popleft()
        for neighbor in graph[current] - reached:
            reached.add(neighbor)
            pending.append(neighbor)
    for identifier in sorted(set(spaces) - reached):
        issue(
            "exterior_route_unverified"
            if space_environment(spaces[identifier]) == "exterior"
            else "room_access_unverified",
            [identifier],
            "Exterior classification does not establish a safe site exit or continuous route."
            if space_environment(spaces[identifier]) == "exterior"
            else "No authored door path reaches an explicitly external entrance.",
        )
    facts = state["project"]["facts"]
    specifications = facts.get("specifications")
    if specifications is not None and not isinstance(specifications, dict):
        issue(
            "specification_information_invalid",
            [],
            "Specifications must be a structured object.",
            "error",
        )
    unresolved = specifications.get("unresolved", []) if isinstance(specifications, dict) else []
    if not isinstance(unresolved, list) or any(not isinstance(value, str) for value in unresolved):
        issue(
            "specification_information_invalid",
            [],
            "Unresolved specifications must be a list of descriptions.",
            "error",
        )
        unresolved = []
    for missing in unresolved:
        issue("specification_unresolved", [], str(missing))
    drawing = facts.get("drawing")
    if not isinstance(drawing, dict):
        drawing = {}
    for field in ("project_number", "issue", "issue_date", "drawn_by", "checked_by"):
        if not drawing.get(field):
            issue("drawing_information_missing", [], f"Drawing field {field} is not set.")
    counts = dict(Counter(row["severity"] for row in issues))
    return {
        "revision": document.revision,
        "issues": issues[issue_offset : issue_offset + max_issues],
        "issue_count": len(issues),
        "truncated": issue_offset + max_issues < len(issues),
        "issue_offset": issue_offset,
        "next_issue_offset": (
            issue_offset + max_issues if issue_offset + max_issues < len(issues) else None
        ),
        "counts": counts,
        "room_access": {
            "reachable": sorted(reached),
            "unverified": sorted(set(spaces) - reached),
            "portals": portals,
        },
        "checks": [
            "room polygon overlap",
            "declared door/room connectivity",
            "furnishing room containment",
            "conservative door-sweep envelope",
            "declared unresolved specifications",
            "drawing metadata",
            "analytic stair headroom against authored slabs and roofs",
        ],
        "scope": (
            "Design observations; detailed motion, full clash detection and "
            "regulatory approval are not established."
        ),
    }
