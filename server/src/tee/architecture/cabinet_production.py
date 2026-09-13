"""Original cabinet recipes, explicit manufacturing intent and stock placement.

Millimetres throughout. Recipe geometry is not a fastener approval, load rating
or machine program. No manufacturer dimensions are silently supplied here.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from tee.architecture.model import ArchitectureError, number, positive

SCHEMA = "tee-cabinet-construction/1"
_ID = re.compile(r"[A-Za-z0-9_-]{1,60}\Z")
_ROLES = {
    "side",
    "top",
    "bottom",
    "back",
    "shelf",
    "door",
    "plinth",
    "frame_stile",
    "frame_rail",
    "drawer_face",
    "drawer_side",
    "drawer_front",
    "drawer_back",
    "drawer_bottom",
    "pullout_face",
    "pullout_side",
    "pullout_bottom",
}


def _object(value: Any, name: str, allowed: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) - allowed:
        raise ArchitectureError(
            f"{name} needs an object with supported fields: {', '.join(sorted(allowed))}."
        )
    return value


def _text(value: Any, name: str, limit: int = 256) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ArchitectureError(f"{name} needs nonempty text up to {limit} characters.")
    return value


def _enum(value: Any, name: str, choices: set[str]) -> str:
    if not isinstance(value, str) or value not in choices:
        raise ArchitectureError(f"{name} must be {' or '.join(sorted(choices))}.")
    return value


def _rows(value: Any, name: str, maximum: int) -> list[Any]:
    if not isinstance(value, list) or len(value) > maximum:
        raise ArchitectureError(f"{name} needs a list of at most {maximum} entries.")
    return value


def _identifier(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ArchitectureError(f"{name} needs 1-60 letters, digits, underscores or hyphens.")
    return value


def _source(value: Any, name: str) -> dict[str, str]:
    source = _object(value, name, {"kind", "title", "revision", "reference"})
    _enum(source.get("kind"), f"{name}.kind", {"shop_specification", "manufacturer_document"})
    for key in ("title", "revision", "reference"):
        _text(source.get(key), f"{name}.{key}", 1024)
    return copy.deepcopy(source)


def build(entity: dict[str, Any]) -> dict[str, Any]:
    """Derive panels and fabrication reports, rejecting contradictory recipes."""
    if entity.get("kind") != "cabinet":
        raise ArchitectureError("Cabinet construction requires kind=cabinet.")
    spec = _object(
        entity["properties"]["construction"],
        "construction",
        {
            "schema",
            "family",
            "mode",
            "front_mode",
            "front_thickness_mm",
            "frame",
            "toe_recess_mm",
            "shelf_positions_mm",
            "shelf_side_clearance_mm",
            "shelf_rear_clearance_mm",
            "fronts",
            "materials",
            "hardware",
            "machining",
            "costing",
            "back_mode",
            "plinth_mode",
            "shelf_front_clearance_mm",
            "appliance_void_height_mm",
            "front_gaps_mm",
            "parts",
        },
    )
    if spec.get("schema") != SCHEMA:
        raise ArchitectureError(f"construction.schema must be {SCHEMA}.")
    family = _enum(
        spec.get("family"),
        "construction.family",
        {"base", "wall", "tall", "topbox", "pullout", "panel_set"},
    )
    if family == "panel_set":
        from .cabinet_parts import explicit_parts

        rows, summary = explicit_parts(entity, spec)
        return _finish(entity, spec, rows, summary)
    if "parts" in spec:
        raise ArchitectureError("parts applies only to family=panel_set.")
    mode = _enum(spec.get("mode"), "construction.mode", {"frameless", "face_frame"})
    front_mode = _enum(spec.get("front_mode", "overlay"), "front_mode", {"overlay", "inset"})
    w, d, h, t, back = (
        positive(entity.get(key), f"cabinet.{key}")
        for key in ("width", "depth", "height", "panel_thickness", "back_thickness")
    )
    p = number(entity.get("plinth_height"), "plinth_height", minimum=0)
    band = number(entity.get("edge_band_mm"), "edge_band_mm", minimum=0)
    grain = _enum(entity.get("grain"), "grain", {"width", "height", "none"})
    material = _text(entity.get("material"), "material")
    shelves, doors = entity.get("shelves"), entity.get("doors")
    if type(shelves) is not int or not 0 <= shelves <= 100:
        raise ArchitectureError("cabinet.shelves must be an integer from 0 to 100.")
    if type(doors) is not int or doors not in {0, 1, 2}:
        raise ArchitectureError("cabinet.doors must be 0, 1 or 2.")
    if family in {"wall", "topbox"} and p:
        raise ArchitectureError(
            "Wall cabinets require plinth_height=0; mounting remains explicitly unverified."
        )
    origin = entity.get("origin")
    if not isinstance(origin, list) or len(origin) != 3:
        raise ArchitectureError("cabinet.origin needs three world coordinates in mm.")
    origin = [number(v, "cabinet.origin") for v in origin]
    fronts = _rows(spec.get("fronts", []), "construction.fronts", 24)
    if fronts and doors:
        raise ArchitectureError(
            "Use doors=0 with construction.fronts; front panels come from the named sections."
        )
    gap = (
        positive(entity["properties"].get("door_gap_mm"), "properties.door_gap_mm")
        if fronts or doors
        else 0
    )
    front_t = positive(spec.get("front_thickness_mm", t), "front_thickness_mm")
    active_front = doors or any(
        isinstance(row, dict) and row.get("kind") != "open" for row in fronts
    )
    front_take = front_t if active_front and front_mode == "overlay" else 0
    frame_t = stile = rail = 0.0
    if mode == "face_frame":
        frame = _object(
            spec.get("frame"),
            "construction.frame",
            {"stile_width_mm", "rail_width_mm", "thickness_mm"},
        )
        stile, rail, frame_t = (
            positive(frame.get(key), f"frame.{key}")
            for key in ("stile_width_mm", "rail_width_mm", "thickness_mm")
        )
    elif "frame" in spec:
        raise ArchitectureError("construction.frame requires mode=face_frame.")
    back_mode = _enum(spec.get("back_mode", "between"), "back_mode", {"between", "applied", "none"})
    plinth_mode = _enum(spec.get("plinth_mode", "front"), "plinth_mode", {"front", "none"})
    back_take = back if back_mode != "none" else 0
    rear_face = d - back_take
    body_front = front_take + frame_t
    body_depth = d - body_front - (back_take if back_mode == "applied" else 0)
    body_height = h - p
    void_height = 0.0
    if family == "topbox":
        void_height = positive(spec.get("appliance_void_height_mm"), "appliance_void_height_mm")
        if void_height + 2 * t >= h or fronts or not doors or shelves or mode != "frameless":
            raise ArchitectureError(
                "Topbox needs frameless cheeks, doors, no extra shelves/fronts "
                "and a void below the top compartment."
            )
    elif "appliance_void_height_mm" in spec:
        raise ArchitectureError("appliance_void_height_mm applies to family=topbox.")
    if family == "pullout" and (doors or len(fronts) != 1 or fronts[0].get("kind") != "pullout"):
        raise ArchitectureError("Pullout family needs one named pullout front and doors=0.")
    inside_w, inside_h = w - 2 * t, h - (void_height if family == "topbox" else p) - 2 * t
    inside_depth = rear_face - body_front
    if min(inside_w, inside_h, inside_depth, body_height) <= 0 or p >= h:
        raise ArchitectureError("Construction thicknesses/plinth leave no internal cabinet volume.")
    if mode == "face_frame" and min(w - 2 * stile, body_height - 2 * rail) <= 0:
        raise ArchitectureError("Face frame leaves no clear opening.")
    toe = number(spec.get("toe_recess_mm", 0), "toe_recess_mm", minimum=0)
    if toe and not p:
        raise ArchitectureError("toe_recess_mm requires a positive plinth_height.")
    if toe + t > body_depth:
        raise ArchitectureError("Toe recess places the plinth beyond the cabinet rear.")
    side_clear = number(
        spec.get("shelf_side_clearance_mm", 0), "shelf_side_clearance_mm", minimum=0
    )
    rear_clear = number(
        spec.get("shelf_rear_clearance_mm", 0), "shelf_rear_clearance_mm", minimum=0
    )
    shelf_front_clear = number(
        spec.get("shelf_front_clearance_mm", 0), "shelf_front_clearance_mm", minimum=0
    )
    materials = _object(spec.get("materials", {}), "construction.materials", _ROLES)
    for role, selection in materials.items():
        _object(selection, f"materials.{role}", {"name", "grain", "edge_band_mm"})
        if "name" in selection:
            _text(selection["name"], f"materials.{role}.name")
        if "grain" in selection:
            _enum(selection["grain"], f"materials.{role}.grain", {"width", "height", "none"})
        if "edge_band_mm" in selection:
            number(selection["edge_band_mm"], f"materials.{role}.edge_band_mm", minimum=0)
    panel_rows: list[dict[str, Any]] = []

    def add(
        role: str,
        suffix: str,
        width: float,
        height: float,
        thickness: float,
        pos: list[float],
        orientation: str,
        edged: tuple[str, ...] = (),
    ) -> None:
        if min(width, height, thickness) <= 0:
            raise ArchitectureError(f"{role} has no usable dimensions.")
        selection = _object(
            materials.get(role, {}), f"materials.{role}", {"name", "grain", "edge_band_mm"}
        )
        mat = _text(selection.get("name", material), f"materials.{role}.name")
        gr = _enum(
            selection.get("grain", grain), f"materials.{role}.grain", {"width", "height", "none"}
        )
        eb = number(
            selection.get("edge_band_mm", band), f"materials.{role}.edge_band_mm", minimum=0
        )
        if edged and eb > thickness / 2:
            raise ArchitectureError(f"{role} edge band exceeds half its core thickness.")
        edges = {edge: eb if edge in edged else 0 for edge in ("left", "right", "top", "bottom")}
        cw, ch = width - edges["left"] - edges["right"], height - edges["top"] - edges["bottom"]
        if min(cw, ch) <= 0:
            raise ArchitectureError(f"{role} edge bands consume its cut blank.")
        size = {
            "XY": [width, height, thickness],
            "XZ": [width, thickness, height],
            "YZ": [thickness, width, height],
        }[orientation]
        panel_rows.append(
            {
                "id": f"{entity['id']}_{suffix}",
                "name": f"{entity.get('name', 'Cabinet')} {suffix}",
                "role": role,
                "width": cw,
                "height": ch,
                "thickness": thickness,
                "finished_width": width,
                "finished_height": height,
                "origin": [origin[i] + pos[i] for i in range(3)],
                "orientation": orientation,
                "size": size,
                "grain": gr,
                "edges": edges,
                "material": mat,
            }
        )

    for i, x in enumerate((0, w - t), 1):
        add("side", f"side_{i}", body_depth, body_height, t, [x, body_front, p], "YZ", ("left",))
    base_z = void_height if family == "topbox" else p
    base_role = "shelf" if family == "topbox" else "bottom"
    for role, z in ((base_role, base_z), ("top", h - t)):
        add(role, f"{role}_1", inside_w, body_depth, t, [t, body_front, z], "XY", ("bottom",))
    if back_mode == "applied":
        add("back", "back_1", w, h - base_z, back, [0, rear_face, base_z], "XZ")
    elif back_mode == "between":
        add("back", "back_1", inside_w, h - base_z - 2 * t, back, [t, rear_face, base_z + t], "XZ")
    if frame_t:
        for i, x in enumerate((0, w - stile), 1):
            add(
                "frame_stile",
                f"frame_stile_{i}",
                stile,
                body_height,
                frame_t,
                [x, front_take, p],
                "XZ",
            )
        for i, z in enumerate((p, h - rail), 1):
            add(
                "frame_rail",
                f"frame_rail_{i}",
                w - 2 * stile,
                rail,
                frame_t,
                [stile, front_take, z],
                "XZ",
            )
    if p and plinth_mode == "front":
        add("plinth", "plinth_1", w, p, t, [0, body_front + toe, 0], "XZ", ("top",))
    positions = spec.get("shelf_positions_mm")
    if positions is None:
        clear = (inside_h - shelves * t) / (shelves + 1)
        if clear <= 0:
            raise ArchitectureError("Shelves leave no clear storage height.")
        positions = [t + i * clear + (i - 1) * t for i in range(1, shelves + 1)]
    positions = _rows(positions, "shelf_positions_mm", 100)
    if len(positions) != shelves:
        raise ArchitectureError("shelf_positions_mm count must equal cabinet.shelves.")
    for i, level in enumerate(positions, 1):
        z = p + number(level, "shelf_positions_mm")
        if z < p + t or z + t > h - t:
            raise ArchitectureError(f"Shelf {i} lies outside the carcass clear height.")
        shelf_front = (max(body_front, front_t) if active_front else body_front) + shelf_front_clear
        add(
            "shelf",
            f"shelf_{i}",
            inside_w - 2 * side_clear,
            rear_face - shelf_front - rear_clear,
            t,
            [t + side_clear, shelf_front, z],
            "XY",
            ("bottom",),
        )
    fx, fz, fw, fh = 0.0, p, w, body_height
    if front_mode == "inset":
        xb, zb = (stile, rail) if frame_t else (t, t)
        fx, fz, fw, fh = xb, p + zb, w - 2 * xb, body_height - 2 * zb
    if family == "topbox":
        fz, fh = void_height + t, h - void_height - t
    gaps = dict.fromkeys(("left", "right", "top", "bottom", "between"), gap)
    if "front_gaps_mm" in spec:
        if not doors or fronts:
            raise ArchitectureError(
                "front_gaps_mm applies to doors; fronts retain their explicit section gaps."
            )
        raw_gaps = _object(spec["front_gaps_mm"], "front_gaps_mm", set(gaps))
        if set(raw_gaps) != set(gaps):
            raise ArchitectureError("front_gaps_mm needs left, right, top, bottom and between.")
        gaps = {k: positive(v, f"front_gaps_mm.{k}") for k, v in raw_gaps.items()}
    face_edges = ("left", "right", "top", "bottom")
    if doors:
        dw = (fw - gaps["left"] - gaps["right"] - (doors - 1) * gaps["between"]) / doors
        dh = fh - gaps["top"] - gaps["bottom"]
        for i in range(doors):
            add(
                "door",
                f"door_{i + 1}",
                dw,
                dh,
                front_t,
                [fx + gaps["left"] + i * (dw + gaps["between"]), 0, fz + gaps["bottom"]],
                "XZ",
                face_edges,
            )
    section_rows = []
    section_ids: set[str] = set()
    section_heights = []
    for row in fronts:
        _object(row, "front", {"id", "kind", "height_mm", "box"})
        sid = _identifier(row.get("id"), "front.id")
        if sid in section_ids:
            raise ArchitectureError("front.id must be unique within the cabinet.")
        section_ids.add(sid)
        _enum(row.get("kind"), "front.kind", {"door", "drawer", "pullout", "open"})
        section_heights.append(positive(row.get("height_mm"), "front.height_mm"))
    if fronts and not math.isclose(
        sum(section_heights) + (len(fronts) + 1) * gap, fh, rel_tol=0, abs_tol=1e-6
    ):
        raise ArchitectureError(
            f"Front heights plus {len(fronts) + 1} gaps must equal "
            f"available front height {fh:g} mm."
        )
    z = fz + gap
    for row, face_h in zip(fronts, section_heights, strict=True):
        sid, kind = row["id"], row["kind"]
        face_w = fw - 2 * gap
        section_rows.append(
            {"id": sid, "kind": kind, "bottom_mm": z, "height_mm": face_h, "width_mm": face_w}
        )
        if kind != "open":
            add(
                "drawer_face"
                if kind == "drawer"
                else "pullout_face"
                if kind == "pullout"
                else "door",
                f"{sid}_face",
                face_w,
                face_h,
                front_t,
                [fx + gap, 0, z],
                "XZ",
                face_edges,
            )
        if kind in {"drawer", "pullout"}:
            box = _object(
                row.get("box"),
                f"front.{sid}.box",
                {
                    "depth_mm",
                    "height_mm",
                    "side_thickness_mm",
                    "bottom_thickness_mm",
                    "side_clearance_mm",
                    "rear_clearance_mm",
                    "bottom_offset_mm",
                    "bottom_mode",
                    "travel_mm",
                },
            )
            depth, height, bt, base_t = (
                positive(box.get(k), f"{sid}.box.{k}")
                for k in ("depth_mm", "height_mm", "side_thickness_mm", "bottom_thickness_mm")
            )
            sc, rc, offset = (
                number(box.get(k), f"{sid}.box.{k}", minimum=0)
                for k in ("side_clearance_mm", "rear_clearance_mm", "bottom_offset_mm")
            )
            passage_w = min(inside_w, w - 2 * stile) if frame_t else inside_w
            bw = passage_w - 2 * sc
            bx, by, bz = (w - bw) / 2, max(body_front, front_t), z + offset
            if min(bw - 2 * bt, depth - 2 * bt, height - base_t) <= 0:
                raise ArchitectureError(f"Drawer {sid} leaves no clear box volume.")
            if by + depth + rc > rear_face + 1e-7:
                raise ArchitectureError(
                    f"Drawer {sid} depth and rear_clearance_mm exceed clear cabinet depth."
                )
            if bz < p + t - 1e-7 or bz + height > h - t + 1e-7:
                raise ArchitectureError(
                    f"Drawer {sid} bottom_offset_mm/height_mm exceed carcass clear height."
                )
            if frame_t and (bz < p + rail - 1e-7 or bz + height > h - rail + 1e-7):
                raise ArchitectureError(
                    f"Drawer {sid} cannot pass the face-frame opening; "
                    "change bottom_offset_mm/height_mm or frame rails."
                )
            if offset + height > face_h + 1e-7:
                raise ArchitectureError(f"Drawer {sid} box exceeds its front section height.")
            bottom_mode = _enum(
                box.get("bottom_mode", "applied"), "box.bottom_mode", {"applied", "between"}
            )
            travel = box.get("travel_mm")
            if travel is not None:
                travel = positive(travel, "box.travel_mm")
                if travel > depth:
                    raise ArchitectureError(
                        "box.travel_mm exceeds box depth; extended runners need their own geometry."
                    )
            if kind == "pullout" and bottom_mode != "between":
                raise ArchitectureError(
                    "Pullout cradle requires bottom_mode=between and explicit open ends."
                )
            section_rows[-1].update(
                {
                    "bottom_mode": bottom_mode,
                    "travel_mm": travel,
                    "runner_verification": "not_established",
                }
            )
            prefix = "pullout" if kind == "pullout" else "drawer"
            applied = bottom_mode == "applied"
            ends = kind == "drawer"
            bottom_w = bw if applied else bw - 2 * bt
            bottom_d = depth if applied or not ends else depth - 2 * bt
            bottom_x = bx if applied else bx + bt
            bottom_y = by if applied or not ends else by + bt
            add(
                prefix + "_bottom",
                f"{sid}_{prefix}_bottom_1",
                bottom_w,
                bottom_d,
                base_t,
                [bottom_x, bottom_y, bz],
                "XY",
            )
            wall_z, wall_h = (bz + base_t, height - base_t) if applied else (bz, height)
            for i, xx in enumerate((bx, bx + bw - bt), 1):
                add(
                    prefix + "_side",
                    f"{sid}_{prefix}_side_{i}",
                    depth,
                    wall_h,
                    bt,
                    [xx, by, wall_z],
                    "YZ",
                )
            if ends:
                for role, yy in (("drawer_front", by), ("drawer_back", by + depth - bt)):
                    add(
                        role,
                        f"{sid}_{role}_1",
                        bw - 2 * bt,
                        wall_h,
                        bt,
                        [bx + bt, yy, wall_z],
                        "XZ",
                    )
        elif "box" in row:
            raise ArchitectureError(f"Front {sid}.box requires kind=drawer or pullout.")
        z += face_h + gap
    summary = {
        "schema": SCHEMA,
        "family": family,
        "mode": mode,
        "front_mode": front_mode,
        "overall_mm": [w, d, h],
        "carcass_depth_mm": body_depth,
        "clear_internal_mm": [inside_w, inside_depth, inside_h],
        "front_sections": section_rows,
        "panel_count": len(panel_rows),
        "toe_recess_mm": toe,
        "back_mode": back_mode,
        "plinth_mode": plinth_mode,
        "front_gaps_mm": gaps,
        "appliance_void_height_mm": void_height if family == "topbox" else None,
        "appliance_void_clear_width_mm": inside_w if family == "topbox" else None,
        "appliance_fit": "not_verified" if family == "topbox" else "not_applicable",
    }
    return _finish(entity, spec, panel_rows, summary)


def _finish(entity: dict, spec: dict, panel_rows: list[dict], summary: dict) -> dict:
    """One manufacturing identity and validation path for recipes and explicit parts."""
    _validate_panels(
        panel_rows, entity["origin"], [entity[k] for k in ("width", "depth", "height")]
    )
    hardware = _hardware(spec.get("hardware", []))
    machining = _machining(spec.get("machining", []), panel_rows)
    for panel in panel_rows:
        operations = [op for op in machining if op["part_id"] == panel["id"]]
        if operations:
            panel["machining"] = copy.deepcopy(operations)
            panel["removed_volume_mm3"] = sum(
                (
                    math.pi * (op["diameter_mm"] / 2) ** 2
                    if op["type"] == "drill"
                    else op["width_mm"] * op["height_mm"]
                )
                * op["depth_mm"]
                for op in operations
            )
            panel["net_volume_mm3"] = math.prod(panel["size"]) - panel["removed_volume_mm3"]
    recipe_id = hashlib.sha256(
        json.dumps(entity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    labels = [
        {
            "part_id": row["id"],
            "cabinet_id": entity["id"],
            "role": row["role"],
            "recipe_sha256": recipe_id,
            "cut_mm": [row["width"], row["height"], row["thickness"]],
            "finished_mm": [row["finished_width"], row["finished_height"], row["thickness"]],
            "grain": row["grain"],
            "material": row["material"],
            "edges_mm": row["edges"],
        }
        for row in panel_rows
    ]
    return {
        "panels": panel_rows,
        "construction": f"{summary['family']}; {summary['mode']}; explicit panel assembly. "
        "Declared back, front and box-bottom construction; no inferred fastener pattern.",
        "assembly": {**summary, "recipe_sha256": recipe_id},
        "bom": [
            {
                "part_id": row["id"],
                "role": row["role"],
                "quantity": 1,
                "material": row["material"],
                "cut_mm": [row["width"], row["height"], row["thickness"]],
            }
            for row in panel_rows
        ],
        "hardware": hardware,
        "machining": machining,
        "labels": labels,
        "costing": _costs(spec.get("costing"), panel_rows, hardware),
        "finished_envelope_volume_m3": sum(math.prod(row["size"]) for row in panel_rows) / 1e9,
        "finished_volume_m3": sum(
            row.get("net_volume_mm3", math.prod(row["size"])) for row in panel_rows
        )
        / 1e9,
        "requirements": {
            "geometry": "checked_panel_bounds_and_interference",
            "hardware": "specification_required" if not hardware else "listed_source_not_verified",
            "machining": "geometry_checked_source_not_verified" if machining else "not_verified",
            "cnc": "not_verified",
            "machining_representation": "explicit_drill_pocket_solids; IFC/GLB use validated cuts",
            "assembly": "Verify fixings, supports, hardware fit/load, edge finishing "
            "and shop construction before manufacture.",
            "drawer_passage": "checked"
            if any(row["kind"] in {"drawer", "pullout"} for row in summary["front_sections"])
            else "not_verified"
            if summary["family"] == "panel_set"
            else "not_applicable",
            "open_clearances": "external room and handles not_verified",
            "structural_loads": "not_verified",
        },
    }


def _validate_panels(rows: list[dict[str, Any]], origin: list[float], overall: list[float]) -> None:
    for i, panel in enumerate(rows):
        for axis in range(3):
            lo, hi = panel["origin"][axis], panel["origin"][axis] + panel["size"][axis]
            if lo < origin[axis] - 1e-7 or hi > origin[axis] + overall[axis] + 1e-7:
                raise ArchitectureError(f"Part {panel['id']} exceeds the cabinet envelope.")
        for other in rows[i + 1 :]:
            overlap = [
                min(panel["origin"][k] + panel["size"][k], other["origin"][k] + other["size"][k])
                - max(panel["origin"][k], other["origin"][k])
                for k in range(3)
            ]
            if min(overlap) > 1e-7:
                raise ArchitectureError(
                    f"Parts {panel['id']} and {other['id']} interfere; "
                    "change shelves/fronts/clearances.",
                )


def _hardware(value: Any) -> list[dict[str, Any]]:
    result = []
    seen = set()
    for row in _rows(value, "hardware", 200):
        _object(
            row,
            "hardware entry",
            {"id", "name", "quantity", "manufacturer", "sku", "revision", "source"},
        )
        hid = _identifier(row.get("id"), "hardware.id")
        if hid in seen:
            raise ArchitectureError("hardware.id must be unique.")
        seen.add(hid)
        _text(row.get("name"), "hardware.name")
        if type(row.get("quantity")) is not int or not 1 <= row["quantity"] <= 10000:
            raise ArchitectureError("hardware.quantity must be an integer from 1 to 10000.")
        for key in ("manufacturer", "sku", "revision"):
            if key in row:
                _text(row[key], f"hardware.{key}")
        source = _source(row.get("source"), "hardware.source")
        result.append(
            {**copy.deepcopy(row), "source": source, "verification": "source_not_verified"}
        )
    return result


def _machining(value: Any, panels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {p["id"]: p for p in panels}
    result = []
    seen = set()
    for op in _rows(value, "machining", 1000):
        _object(
            op,
            "machining operation",
            {
                "id",
                "type",
                "part_id",
                "face",
                "u_mm",
                "v_mm",
                "depth_mm",
                "diameter_mm",
                "width_mm",
                "height_mm",
                "through",
                "source",
            },
        )
        oid = _identifier(op.get("id"), "machining.id")
        if oid in seen:
            raise ArchitectureError("machining.id must be unique.")
        seen.add(oid)
        part_id = _text(op.get("part_id"), "machining.part_id")
        if part_id not in by_id:
            raise ArchitectureError(f"Machining {oid} names unknown part {part_id}.")
        part = by_id[part_id]
        kind = _enum(op.get("type"), "machining.type", {"drill", "pocket"})
        _enum(op.get("face"), "machining.face", {"front", "back"})
        u, v = (number(op.get(k), f"machining.{k}", minimum=0) for k in ("u_mm", "v_mm"))
        depth = positive(op.get("depth_mm"), "machining.depth_mm")
        through = op.get("through")
        if type(through) is not bool:
            raise ArchitectureError("machining.through must be an explicit boolean.")
        if through and not math.isclose(depth, part["thickness"], rel_tol=0, abs_tol=1e-7):
            raise ArchitectureError(
                f"Through operation {oid} depth must equal panel thickness; "
                "machine overtravel belongs to a reviewed post setup."
            )
        if not through and depth >= part["thickness"]:
            raise ArchitectureError(f"Blind operation {oid} breaks through the panel.")
        if kind == "drill":
            if "width_mm" in op or "height_mm" in op:
                raise ArchitectureError("drill accepts diameter_mm, not pocket dimensions.")
            radius = positive(op.get("diameter_mm"), "machining.diameter_mm") / 2
            bounds = [u - radius, v - radius, u + radius, v + radius]
        else:
            if "diameter_mm" in op:
                raise ArchitectureError("pocket accepts width_mm/height_mm, not diameter_mm.")
            ow, oh = (positive(op.get(k), f"machining.{k}") for k in ("width_mm", "height_mm"))
            bounds = [u, v, u + ow, v + oh]
        # The coordinates are fixed to the finished front-view rectangle on BOTH
        # faces; the back changes entry direction, never silently mirrors u/v.
        if (
            bounds[0] < part["edges"]["left"]
            or bounds[1] < part["edges"]["bottom"]
            or bounds[2] > part["finished_width"] - part["edges"]["right"]
            or bounds[3] > part["finished_height"] - part["edges"]["top"]
        ):
            raise ArchitectureError(
                f"Machining {oid} extends outside the core blank or into an edge band."
            )
        source = _source(op.get("source"), "machining.source")
        for prior in result:
            if prior["part_id"] != part_id:
                continue
            pb = prior["bounds_uv_mm"]
            if (
                min(bounds[2], pb[2]) > max(bounds[0], pb[0])
                and min(bounds[3], pb[3]) > max(bounds[1], pb[1])
                and (prior["face"] == op["face"] or prior["depth_mm"] + depth >= part["thickness"])
            ):
                raise ArchitectureError(
                    f"Machining {oid} overlaps {prior['id']}; combined or intersecting "
                    "operations require an explicit supported recipe."
                )
        result.append(
            {
                **copy.deepcopy(op),
                "source": source,
                "bounds_uv_mm": bounds,
                "reference": "finished panel front-view u/v; "
                "back entry reverses thickness direction only",
                "interference_check": "conservative operation bounds",
                "geometry_status": "checked_core_bounds_and_depth",
                "source_status": "not_verified",
                "cnc_status": "not_verified",
            }
        )
    return result


def _costs(
    value: Any, panels: list[dict[str, Any]], hardware: list[dict[str, Any]]
) -> dict[str, Any]:
    if value is None:
        return {"status": "not_priced", "total": None, "missing": ["costing specification"]}
    spec = _object(
        value,
        "costing",
        {
            "currency",
            "material_rates",
            "hardware_rates",
            "labor_hours",
            "labor_rate",
            "markup_percent",
            "source",
        },
    )
    currency = _text(spec.get("currency"), "costing.currency", 3)
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise ArchitectureError("costing.currency needs an explicit three-letter currency code.")
    source = _source(spec.get("source"), "costing.source")
    materials = spec.get("material_rates", {})
    hardware_rates = spec.get("hardware_rates", {})
    if (
        not isinstance(materials, dict)
        or len(materials) > 100
        or not isinstance(hardware_rates, dict)
        or len(hardware_rates) > 200
    ):
        raise ArchitectureError(
            "costing rates must be bounded objects keyed by material name/hardware id."
        )
    for name, rates in materials.items():
        _text(name, "costing material name")
        _object(rates, "material rate", {"per_m2", "edge_per_m"})
        for key, rate in rates.items():
            number(rate, f"material rate.{key}", minimum=0)
    for hid, rate in hardware_rates.items():
        _identifier(hid, "hardware rate id")
        number(rate, "hardware rate", minimum=0)
    missing = []
    amounts: dict[str, Decimal] = {
        key: Decimal(0) for key in ("panels", "edges", "hardware", "labor")
    }
    for panel in panels:
        rates = materials.get(panel["material"], {})
        if "per_m2" not in rates:
            missing.append(f"material {panel['material']} per_m2")
        else:
            amounts["panels"] += (
                Decimal(str(panel["width"]))
                * Decimal(str(panel["height"]))
                / Decimal(1000000)
                * Decimal(str(rates["per_m2"]))
            )
        length = sum(
            panel["finished_height"] if edge in {"left", "right"} else panel["finished_width"]
            for edge, band in panel["edges"].items()
            if band
        )
        if length and "edge_per_m" not in rates:
            missing.append(f"material {panel['material']} edge_per_m")
        elif length:
            amounts["edges"] += (
                Decimal(str(length)) / Decimal(1000) * Decimal(str(rates["edge_per_m"]))
            )
    for item in hardware:
        if item["id"] not in hardware_rates:
            missing.append(f"hardware {item['id']} unit price")
        else:
            amounts["hardware"] += Decimal(item["quantity"]) * Decimal(
                str(hardware_rates[item["id"]])
            )
    for key in ("labor_hours", "labor_rate", "markup_percent"):
        if key not in spec:
            missing.append(key)
        else:
            number(spec[key], f"costing.{key}", minimum=0)
    if "labor_hours" in spec and "labor_rate" in spec:
        amounts["labor"] = Decimal(str(spec["labor_hours"])) * Decimal(str(spec["labor_rate"]))
    subtotal = sum(amounts.values())
    total = (
        subtotal * (1 + Decimal(str(spec.get("markup_percent", 0))) / 100) if not missing else None
    )

    def rounded(amount: Decimal) -> str:
        return str(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    return {
        "status": "estimate" if not missing else "incomplete",
        "currency": currency,
        "source": source,
        "known_components": {key: rounded(amount) for key, amount in amounts.items()},
        "known_subtotal": rounded(subtotal),
        "total": rounded(total) if total is not None else None,
        "missing": sorted(set(missing)),
        "basis": "net cut panel area and finished edge length; "
        "excludes stock waste, tax, delivery and unlisted hardware",
    }


def nest_best_fit(
    panels: list[dict[str, Any]], sw: float, sh: float, kerf: float, rotate: bool, trim: float
) -> dict[str, Any]:
    """Try two best-fit orders and the row baseline; retain the least stock."""
    usable_w, usable_h = sw - 2 * trim, sh - 2 * trim
    if min(usable_w, usable_h) <= 0:
        raise ArchitectureError("Sheet trim leaves no usable stock.")
    for p in panels:
        w, h = p["width"], p["height"]
        if not (w <= usable_w and h <= usable_h) and not (
            rotate and p["grain"] == "none" and h <= usable_w and w <= usable_h
        ):
            raise ArchitectureError(
                "ak_sheet_fit",
                f"Panel {p['id']} does not fit the usable sheet after trim and permitted grain.",
            )

    def pack(area_first: bool) -> list[dict[str, Any]]:
        sheets: list[dict[str, Any]] = []
        ordered = sorted(
            panels,
            key=lambda p: (
                (
                    (-p["width"] * p["height"], -max(p["width"], p["height"]))
                    if area_first
                    else (-max(p["width"], p["height"]), -p["width"] * p["height"])
                )
                + (p["id"],)
            ),
        )
        for panel in ordered:
            group = (panel["material"], panel["thickness"], panel["grain"])
            options = [(panel["width"], panel["height"], False)]
            if rotate and panel["grain"] == "none" and panel["width"] != panel["height"]:
                options.append((panel["height"], panel["width"], True))
            choices = []
            for si, sheet in enumerate(sheets):
                if sheet["_group"] != group:
                    continue
                for ri, rect in enumerate(sheet["_free"]):
                    for w, h, turned in options:
                        if w <= rect[2] and h <= rect[3]:
                            choices.append(
                                (
                                    (
                                        rect[2] * rect[3] - w * h,
                                        min(rect[2] - w, rect[3] - h),
                                        si,
                                        ri,
                                        turned,
                                    ),
                                    si,
                                    ri,
                                    w,
                                    h,
                                    turned,
                                )
                            )
            if not choices:
                sheets.append(
                    {
                        "index": len(sheets) + 1,
                        "material": group[0],
                        "thickness": group[1],
                        "grain": group[2],
                        "width": sw,
                        "height": sh,
                        "placements": [],
                        "_group": group,
                        "_free": [[trim, trim, usable_w, usable_h]],
                    }
                )
                si, ri = len(sheets) - 1, 0
                w, h, turned = next(
                    option for option in options if option[0] <= usable_w and option[1] <= usable_h
                )
            else:
                _, si, ri, w, h, turned = min(choices)
            sheet = sheets[si]
            x, y, fw, fh = sheet["_free"].pop(ri)
            sheet["placements"].append(
                {"id": panel["id"], "x": x, "y": y, "width": w, "height": h, "rotated": turned}
            )
            rw, rh = fw - w - kerf, fh - h - kerf
            splits = [
                [[x + w + kerf, y, rw, fh], [x, y + h + kerf, w, rh]],
                [[x + w + kerf, y, rw, h], [x, y + h + kerf, fw, rh]],
            ]
            splits = [[r for r in split if r[2] > 0 and r[3] > 0] for split in splits]
            best = max(
                splits,
                key=lambda split: (
                    sum(r[2] * r[3] for r in split),
                    max((r[2] * r[3] for r in split), default=0),
                ),
            )
            sheet["_free"].extend(best)
        return sheets

    # Row packing can beat either heuristic on a particular room. Preserve it
    # as a measured candidate; changing the default must not increase stock.
    from tee.architecture.cabinets import _nest_rows

    row_candidate = _nest_rows(panels, usable_w, usable_h, kerf, rotate)["sheets"]
    for sheet in row_candidate:
        free = []
        bands: dict[float, list[dict[str, Any]]] = {}
        for placement in sheet["placements"]:
            bands.setdefault(placement["y"], []).append(placement)
        upper = 0.0
        for y, band_rows in sorted(bands.items()):
            band_height = max(row["height"] for row in band_rows)
            right = max(row["x"] + row["width"] for row in band_rows) + kerf
            if right < usable_w:
                free.append([right + trim, y + trim, usable_w - right, band_height])
            for row in band_rows:
                offcut_height = band_height - row["height"] - kerf
                if offcut_height > 0:
                    free.append(
                        [
                            row["x"] + trim,
                            y + row["height"] + kerf + trim,
                            row["width"],
                            offcut_height,
                        ]
                    )
            upper = y + band_height + kerf
        if upper < usable_h:
            free.append([trim, upper + trim, usable_w, usable_h - upper])
        for row in sheet["placements"]:
            row["x"] += trim
            row["y"] += trim
        sheet.update(width=sw, height=sh, _free=free, _group=None)
    candidates = [pack(False), pack(True), row_candidate]
    sheets = min(
        candidates,
        key=lambda rows: (
            len(rows),
            -sum(max((r[2] * r[3] for r in row["_free"]), default=0) for row in rows),
        ),
    )
    for sheet in sheets:
        sheet["remnants"] = [
            {
                "id": f"sheet_{sheet['index']}_offcut_{i + 1}",
                "x": r[0],
                "y": r[1],
                "width": r[2],
                "height": r[3],
            }
            for i, r in enumerate(sorted(sheet.pop("_free")))
        ]
        del sheet["_group"]
    return {
        "ok": True,
        "units": "mm",
        "sheet_count": len(sheets),
        "sheets": copy.deepcopy(sheets),
        "kerf": kerf,
        "allow_rotate": rotate,
        "trim_mm": trim,
        "utilization": sum(p["width"] * p["height"] for p in panels) / (len(sheets) * sw * sh),
        "method": "deterministic guillotine portfolio: two best-fit orders and row baseline; "
        "no optimality claim",
        "note": "Remnants are disjoint recoverable rectangles after modeled kerf and edge trim. "
        "Grain orientation is retained. No toolpath or machine readiness is implied.",
    }
