"""Explicit architectural design examples, separate from the authoring kernel.

The dwelling has a room program, connected circulation, typed construction,
framed openings and a coordinated kitchen. These are authored design choices,
not assertions about a site, structural calculations or manufacturer approval.
"""

from __future__ import annotations

from typing import Any


def compact_dwelling() -> list[dict[str, Any]]:
    materials = {
        "render": {"name": "Cementitious render", "category": "finish"},
        "masonry": {
            "name": "Masonry core — engineering specification pending",
            "category": "masonry",
        },
        "insulation": {
            "name": "Rigid insulation — product selection pending",
            "category": "insulation",
        },
        "board": {"name": "Internal lining board", "category": "finish"},
        "partition_core": {
            "name": "Partition core — assembly rating not assigned",
            "category": "core",
        },
        "concrete": {"name": "Concrete — reinforcement/grade not assigned", "category": "concrete"},
        "aluminium": {"name": "Aluminium frame — system not selected", "category": "metal"},
        "glass": {"name": "Glass — safety/thermal specification not assigned", "category": "glass"},
        "door_leaf": {"name": "Timber door leaf — rating not assigned", "category": "timber"},
    }

    def type_row(name, kind, parameters, layers=None):
        row = {
            "name": name,
            "kind": kind,
            "parameters": parameters,
            "property_sets": {"DesignStatus": {"Stage": "Design development", "Approved": False}},
        }
        if layers:
            row["material_layers"] = [
                {"material_id": material, "thickness_mm": thickness, "role": role}
                for material, thickness, role in layers
            ]
        return row

    frame = {
        "operation": "fixed",
        "frame_width_mm": 50,
        "frame_depth_mm": 70,
        "reveal_mm": 60,
        "glazing_thickness_mm": 6,
        "frame_material_id": "aluminium",
        "glazing_material_id": "glass",
    }
    door = {
        "operation": "swing",
        "hinge": "start",
        "swing_side": "left",
        "frame_width_mm": 40,
        "frame_depth_mm": 80,
        "reveal_mm": 20,
        "leaf_thickness_mm": 40,
        "clearance_mm": 3,
        "frame_material_id": "door_leaf",
        "leaf_material_id": "door_leaf",
    }
    types = {
        "EW01": type_row(
            "External wall / 240 mm",
            "wall",
            {"thickness": 240, "height": 3000},
            [
                ("render", 15, "finish"),
                ("masonry", 170, "core"),
                ("insulation", 40, "insulation"),
                ("board", 15, "finish"),
            ],
        ),
        "IW01": type_row(
            "Internal partition / 120 mm",
            "wall",
            {"thickness": 120, "height": 3000},
            [("board", 15, "finish"), ("partition_core", 90, "core"), ("board", 15, "finish")],
        ),
        "FL01": type_row(
            "Ground slab / 150 mm", "slab", {"thickness": 150}, [("concrete", 150, "core")]
        ),
        "RF01": type_row(
            "Flat roof slab / 250 mm",
            "roof",
            {"thickness": 250, "form": "flat"},
            [("concrete", 250, "core")],
        ),
        "D01": type_row(
            "Entrance opening / 1100 x 2300",
            "opening",
            {"fill": "door", "width": 1100, "height": 2300, "assembly": {**door, "reveal_mm": 70}},
        ),
        "D02": type_row(
            "Internal door / 1000 x 2100",
            "opening",
            {"fill": "door", "width": 1000, "height": 2100, "assembly": door},
        ),
        "W01": type_row(
            "Living window / 2400 x 1500",
            "opening",
            {"fill": "window", "width": 2400, "height": 1500, "assembly": frame},
        ),
        "W02": type_row(
            "Bedroom window / 1800 x 1500",
            "opening",
            {"fill": "window", "width": 1800, "height": 1500, "assembly": frame},
        ),
        "W03": type_row(
            "Bathroom window / 900 x 900",
            "opening",
            {"fill": "window", "width": 900, "height": 900, "assembly": frame},
        ),
        "W04": type_row(
            "Kitchen window / 1800 x 1400",
            "opening",
            {"fill": "window", "width": 1800, "height": 1400, "assembly": frame},
        ),
    }
    types["EW01"]["property_sets"]["Pset_WallCommon"] = {"IsExternal": True}
    types["IW01"]["property_sets"]["Pset_WallCommon"] = {"IsExternal": False}
    facts = {
        "wall_join_policy": "orthogonal_butt_v1",
        "bim": {"schema": "tee-bim/1", "materials": materials, "types": types},
        "drawing": {
            "project_number": "AK-A83-001",
            "issue": "DD01",
            "issue_date": "2026-09-11",
            "status": "DESIGN DEVELOPMENT",
            "drawn_by": "TEE / archkiln",
            "checked_by": None,
            "site": "No site assigned",
            "client": "Demonstration project",
            "plan_cut_height_mm": 1200,
            "sections": [
                {"id": "A", "axis": "y", "coordinate_mm": 6500, "direction": "positive"},
                {"id": "B", "axis": "x", "coordinate_mm": 10500, "direction": "positive"},
            ],
            "notes": [
                "All dimensions in mm; levels relative to ground finished floor.",
                "Room furnishings are schematic size/clearance references.",
                (
                    "Construction types are explicit design choices; engineering and product "
                    "review remain required."
                ),
            ],
        },
        "specifications": {
            "purpose": (
                "Two-bedroom compact dwelling with a separate circulation zone and fitted kitchen."
            ),
            "datum": "Ground finished floor = +0.000 m; all object dimensions are mm.",
            "walls": "EW01 240 mm and IW01 120 mm; layer dimensions are in the BIM type library.",
            "openings": (
                "Opening sizes are rough openings; frames, glazing/leaf and sill/head "
                "levels are modeled."
            ),
            "roof": (
                "Flat structural slab only; drainage, falls, insulation, waterproofing "
                "and structural design remain required."
            ),
            "cabinetry": (
                "18 mm core, 6 mm backs, 2 mm front gaps, 100 mm plinth; product/hardware "
                "selection requires review."
            ),
            "unresolved": [
                "Site and jurisdiction",
                "Structural calculations and reinforcement",
                "Roof envelope and drainage",
                "MEP layout and fixtures connections",
                "Fire/thermal/acoustic and safety-glazing performance",
                "Hardware supplier and machine-specific manufacturing settings",
            ],
        },
    }
    entities: list[dict[str, Any]] = [
        {"id": "ground", "kind": "storey", "name": "Ground floor", "elevation": 0, "height": 3000}
    ]

    def bind(entity, type_id):
        entity.setdefault("properties", {})["bim"] = {"type_id": type_id, "overrides": []}
        if entity["kind"] == "wall":
            entity["properties"]["is_external"] = type_id == "EW01"
        entity.update({k: v for k, v in types[type_id]["parameters"].items() if k != "assembly"})
        if "assembly" in types[type_id]["parameters"]:
            entity["properties"]["assembly"] = types[type_id]["parameters"]["assembly"]
        return entity

    for identifier, start, end, type_id in (
        ("south", [0, 0], [12000, 0], "EW01"),
        ("east", [12000, 0], [12000, 9000], "EW01"),
        ("north", [12000, 9000], [0, 9000], "EW01"),
        ("west", [0, 9000], [0, 0], "EW01"),
        ("corridor_south", [0, 4600], [12000, 4600], "IW01"),
        ("corridor_north", [0, 5800], [12000, 5800], "IW01"),
        ("bedroom_divider", [5500, 5800], [5500, 9000], "IW01"),
        ("bathroom_divider", [9500, 5800], [9500, 9000], "IW01"),
    ):
        entities.append(
            bind(
                {
                    "id": identifier,
                    "kind": "wall",
                    "name": identifier.replace("_", " ").title(),
                    "storey": "ground",
                    "start": start,
                    "end": end,
                },
                type_id,
            )
        )
    for identifier, wall, offset, sill, type_id in (
        ("entrance", "south", 600, 0, "D01"),
        ("living_window", "south", 2500, 900, "W01"),
        ("living_west_window", "west", 5600, 900, "W02"),
        ("kitchen_window", "east", 1200, 1000, "W04"),
        ("corridor_access", "corridor_south", 4300, 0, "D02"),
        ("bedroom_1_access", "corridor_north", 1600, 0, "D02"),
        ("bedroom_2_access", "corridor_north", 6500, 0, "D02"),
        ("bathroom_access", "corridor_north", 10200, 0, "D02"),
        ("bedroom_1_window", "north", 7800, 900, "W02"),
        ("bedroom_2_window", "north", 3600, 900, "W02"),
        ("bathroom_window", "north", 800, 1500, "W03"),
    ):
        opening = bind(
            {
                "id": identifier,
                "kind": "opening",
                "name": identifier.replace("_", " ").title(),
                "wall": wall,
                "offset": offset,
                "sill": sill,
            },
            type_id,
        )
        if identifier == "corridor_access":
            opening["properties"]["assembly"] = {
                **opening["properties"]["assembly"],
                "swing_side": "right",
            }
            opening["properties"]["bim"]["overrides"] = ["assembly"]
        entities.append(opening)
    for identifier, name, rectangle in (
        ("living_kitchen", "Living / dining / kitchen", [120, 120, 11880, 4540]),
        ("corridor", "Private circulation", [120, 4660, 11880, 5740]),
        ("bedroom_1", "Bedroom 1", [120, 5860, 5440, 8880]),
        ("bedroom_2", "Bedroom 2", [5560, 5860, 9440, 8880]),
        ("bathroom", "Bathroom", [9560, 5860, 11880, 8880]),
    ):
        x0, y0, x1, y1 = rectangle
        entities.append(
            {
                "id": identifier,
                "kind": "space",
                "name": name,
                "storey": "ground",
                "polygon": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
                "height": 2800,
            }
        )
    entities.append(
        bind(
            {
                "id": "floor",
                "kind": "slab",
                "name": "Ground floor slab",
                "storey": "ground",
                "polygon": [[-120, -120], [12120, -120], [12120, 9120], [-120, 9120]],
            },
            "FL01",
        )
    )
    entities.append(
        bind(
            {
                "id": "roof",
                "kind": "roof",
                "name": "Flat roof slab",
                "storey": "ground",
                "polygon": [[-300, -300], [12300, -300], [12300, 9300], [-300, 9300]],
                "base_height": 3000,
            },
            "RF01",
        )
    )
    for identifier, x, width, name, doors in (
        ("kitchen_drawers", 8100, 600, "K01 drawer base", 0),
        ("kitchen_prep", 8700, 600, "K02 preparation base", 1),
        ("kitchen_storage", 9300, 900, "K03 storage base", 2),
        ("kitchen_sink", 10200, 900, "K04 sink base", 2),
    ):
        construction: dict[str, Any] = {
            "schema": "tee-cabinet-construction/1",
            "family": "base",
            "mode": "frameless",
            "front_mode": "overlay",
            "front_thickness_mm": 18,
            "toe_recess_mm": 60,
            "shelf_side_clearance_mm": 1,
            "shelf_rear_clearance_mm": 5,
        }
        props: dict[str, Any] = {
            "door_gap_mm": 2,
            "construction": construction,
            "specification_status": "Hardware and sink cutout require detailed selection",
        }
        if identifier == "kitchen_drawers":
            construction["fronts"] = [
                {
                    "id": "bottom",
                    "kind": "drawer",
                    "height_mm": 312,
                    "box": {
                        "depth_mm": 500,
                        "height_mm": 230,
                        "side_thickness_mm": 15,
                        "bottom_thickness_mm": 6,
                        "side_clearance_mm": 13,
                        "rear_clearance_mm": 20,
                        "bottom_offset_mm": 30,
                    },
                },
                {
                    "id": "middle",
                    "kind": "drawer",
                    "height_mm": 300,
                    "box": {
                        "depth_mm": 500,
                        "height_mm": 220,
                        "side_thickness_mm": 15,
                        "bottom_thickness_mm": 6,
                        "side_clearance_mm": 13,
                        "rear_clearance_mm": 20,
                        "bottom_offset_mm": 30,
                    },
                },
                {
                    "id": "top",
                    "kind": "drawer",
                    "height_mm": 180,
                    "box": {
                        "depth_mm": 500,
                        "height_mm": 110,
                        "side_thickness_mm": 15,
                        "bottom_thickness_mm": 6,
                        "side_clearance_mm": 13,
                        "rear_clearance_mm": 20,
                        "bottom_offset_mm": 30,
                    },
                },
            ]
        entities.append(
            {
                "id": identifier,
                "kind": "cabinet",
                "name": name,
                "storey": "ground",
                "origin": [x, 3880, 0],
                "width": width,
                "depth": 600,
                "height": 900,
                "panel_thickness": 18,
                "back_thickness": 6,
                "shelves": 0 if doors == 0 or identifier == "kitchen_sink" else 1,
                "doors": doors,
                "plinth_height": 100,
                "grain": "height",
                "edge_band_mm": 1,
                "material": "Melamine-faced board — supplier/grade pending",
                "properties": props,
            }
        )
    for identifier, name, category, origin, size in (
        ("bed_1", "Double bed", "bed", [2900, 6660, 0], [1600, 2000, 600]),
        ("bed_2", "Single bed", "bed", [8100, 6660, 0], [1000, 2000, 600]),
        ("sofa", "Living sofa", "sofa", [2700, 2400, 0], [2400, 900, 850]),
        ("dining", "Dining table", "table", [5800, 1500, 0], [1500, 850, 750]),
        ("dining_chair_1", "Dining chair", "chair", [5900, 950, 0], [450, 450, 850]),
        ("dining_chair_2", "Dining chair", "chair", [6800, 950, 0], [450, 450, 850]),
        ("dining_chair_3", "Dining chair", "chair", [5900, 2450, 0], [450, 450, 850]),
        ("dining_chair_4", "Dining chair", "chair", [6800, 2450, 0], [450, 450, 850]),
        ("shower", "Shower zone", "shower", [10680, 7680, 0], [1100, 1100, 2100]),
        ("wc", "WC clearance reference", "wc", [9750, 7900, 0], [450, 700, 750]),
        ("basin", "Vanity basin", "basin", [9700, 6900, 0], [700, 500, 850]),
        ("fridge", "Refrigerator allowance", "appliance", [11200, 3830, 0], [600, 650, 2100]),
    ):
        entities.append(
            {
                "id": identifier,
                "kind": "furnishing",
                "name": name,
                "storey": "ground",
                "origin": origin,
                "size": size,
                "category": category,
                "properties": {"representation": "schematic", "manufacturer": "Not selected"},
            }
        )
    return [
        {"op": "project", "changes": {"facts": facts}},
        *[{"op": "create", "entity": entity} for entity in entities],
    ]
