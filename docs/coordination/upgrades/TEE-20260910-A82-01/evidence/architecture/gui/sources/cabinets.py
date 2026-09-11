"""Explicit frameless cabinet construction and deterministic sheet layouts.

All quantities are mm. A cabinet's declared depth includes overlay doors. Back
fits between sides, top and bottom; shelves terminate at its inner face. Panel
solids use finished envelopes; cut blanks subtract the declared edge bands.
No joinery method, fixing strength or manufacturer machining is certified.
"""

from __future__ import annotations

import copy
import math
from typing import Any

from tee.architecture.model import ArchitectureError, number, positive


def panels(entity: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(entity, dict) or entity.get("kind") != "cabinet":
        raise ArchitectureError("panels needs a cabinet entity.")
    w, d, h, t, back = (
        positive(entity.get(k), f"cabinet.{k}")
        for k in ("width", "depth", "height", "panel_thickness", "back_thickness")
    )
    p = number(entity.get("plinth_height"), "cabinet.plinth_height", minimum=0)
    band = number(entity.get("edge_band_mm"), "cabinet.edge_band_mm", minimum=0)
    shelves, doors = entity.get("shelves"), entity.get("doors")
    if type(shelves) is not int or not 0 <= shelves <= 100:
        raise ArchitectureError("cabinet.shelves must be an integer from 0 to 100.")
    if type(doors) is not int or doors not in {0, 1, 2}:
        raise ArchitectureError("cabinet.doors must be 0, 1 or 2.")
    grain = entity.get("grain")
    if not isinstance(grain, str) or grain not in {"width", "height", "none"}:
        raise ArchitectureError("cabinet.grain must be width, height or none.")
    material = entity.get("material")
    if not isinstance(material, str) or not material.strip() or len(material) > 256:
        raise ArchitectureError("cabinet.material needs an explicit material name.")
    origin = entity.get("origin")
    if not isinstance(origin, list) or len(origin) != 3:
        raise ArchitectureError("cabinet.origin needs three world coordinates in mm.")
    x, y, z = (number(v, "cabinet.origin") for v in origin)
    props = entity.get("properties", {})
    if not isinstance(props, dict):
        raise ArchitectureError("cabinet.properties must be an object.")
    gap = (
        number(props.get("door_gap_mm"), "cabinet.properties.door_gap_mm", minimum=0)
        if doors
        else 0
    )
    if doors and gap <= 0:
        raise ArchitectureError("Doors require an explicit positive properties.door_gap_mm.")
    front = t if doors else 0.0
    body_depth, body_height, inside_width = d - front, h - p, w - 2 * t
    inside_height = body_height - 2 * t
    shelf_depth = body_depth - back
    if min(inside_width, inside_height, shelf_depth) <= 0 or p >= h:
        raise ArchitectureError("Cabinet thickness/back/plinth leaves no internal space.")
    if shelves * t >= inside_height:
        raise ArchitectureError("Cabinet shelves leave no clear storage height.")
    if band > t / 2:
        raise ArchitectureError("Edge band exceeds half the panel thickness.")
    if p and p <= 2 * band:
        raise ArchitectureError("Plinth height is too small for the declared edge bands.")
    result = []

    def add(
        role: str,
        index: int,
        width: float,
        height: float,
        thickness: float,
        position: list[float],
        orientation: str,
        edged: tuple[str, ...] = (),
    ) -> None:
        edges = {
            edge: band if edge in edged else 0.0 for edge in ("left", "right", "top", "bottom")
        }
        cut_width = width - edges["left"] - edges["right"]
        cut_height = height - edges["top"] - edges["bottom"]
        if min(cut_width, cut_height) <= 0:
            raise ArchitectureError(f"{role} has no usable blank after edge-band allowance.")
        size = {
            "XY": [width, height, thickness],
            "XZ": [width, thickness, height],
            "YZ": [thickness, width, height],
        }[orientation]
        result.append(
            {
                "id": f"{entity.get('id', 'cabinet')}_{role}_{index}",
                "name": f"{entity.get('name', 'Cabinet')} {role} {index}",
                "role": role,
                "width": cut_width,
                "height": cut_height,
                "thickness": thickness,
                "finished_width": width,
                "finished_height": height,
                "origin": position,
                "orientation": orientation,
                "size": size,
                "grain": grain,
                "edges": edges,
                "material": material,
            }
        )

    # Side panels are full-height; top/bottom fit between them. Edge at front is
    # the cut rectangle's left edge for side panels and bottom edge for horizontals.
    for i, px in enumerate((x, x + w - t), 1):
        add("side", i, body_depth, body_height, t, [px, y + front, z + p], "YZ", ("left",))
    for i, pz in enumerate((z + p, z + h - t), 1):
        add(
            "bottom" if i == 1 else "top",
            1,
            inside_width,
            body_depth,
            t,
            [x + t, y + front, pz],
            "XY",
            ("bottom",),
        )
    add("back", 1, inside_width, inside_height, back, [x + t, y + d - back, z + p + t], "XZ")
    clear = (inside_height - shelves * t) / (shelves + 1)
    for i in range(1, shelves + 1):
        add(
            "shelf",
            i,
            inside_width,
            shelf_depth,
            t,
            [x + t, y + front, z + p + t + i * clear + (i - 1) * t],
            "XY",
            ("bottom",),
        )
    if doors:
        door_width = (w - (doors + 1) * gap) / doors
        door_height = body_height - 2 * gap
        if min(door_width, door_height) <= 0:
            raise ArchitectureError("Door clearance consumes the entire door blank.")
        for i in range(doors):
            add(
                "door",
                i + 1,
                door_width,
                door_height,
                t,
                [x + gap + i * (door_width + gap), y, z + p + gap],
                "XZ",
                ("left", "right", "top", "bottom"),
            )
    if p:
        add("plinth", 1, w, p, t, [x, y + front, z], "XZ", ("top",))
    return result


def schedule(entity: dict[str, Any]) -> dict[str, Any]:
    rows = panels(entity)
    edge_length = sum(
        (p["finished_height"] if edge in {"left", "right"} else p["finished_width"])
        for p in rows
        for edge, band in p["edges"].items()
        if band
    )
    return {
        "cabinet": entity.get("id"),
        "units": "mm",
        "panels": rows,
        "panel_count": len(rows),
        "cut_area_m2": sum(p["width"] * p["height"] for p in rows) / 1e6,
        "finished_volume_m3": sum(math.prod(p["size"]) for p in rows) / 1e9,
        "edge_band_length_mm": edge_length,
        "construction": "Frameless; sides full height above plinth; top/bottom between sides; "
        "back between sides/top/bottom at rear; shelves stop at back; overlay doors consume "
        "front thickness within overall depth. Cut blanks subtract edge bands. Solids represent "
        "finished envelopes, not separate core/band materials.",
        "requirements": {
            "hardware": "not_verified",
            "machining": "not_verified",
            "cnc": "not_verified",
            "assembly": "Select joints/fixings, shelf support, door hinges and plinth supports; "
            "verify manufacturer clearances and loads before manufacture.",
        },
    }


def nest(
    panels: list[dict[str, Any]],
    sheet_width: float,
    sheet_height: float,
    kerf: float,
    allow_rotate: bool = False,
) -> dict[str, Any]:
    """Deterministic row packing, separated by material/thickness/grain direction.

    A guillotine-compatible layout, not an optimization claim or CNC toolpath.
    Kerf separates neighbouring rectangles and rows, with no assumed edge trim.
    """
    sw, sh = positive(sheet_width, "sheet_width"), positive(sheet_height, "sheet_height")
    k = number(kerf, "kerf", minimum=0)
    if type(allow_rotate) is not bool:
        raise ArchitectureError("allow_rotate must be boolean.")
    if not isinstance(panels, list) or not 1 <= len(panels) <= 1000:
        raise ArchitectureError("nest needs 1-1000 panel rows.")
    identifiers = set()
    checked = []
    for panel in panels:
        if not isinstance(panel, dict):
            raise ArchitectureError("Each panel must be an object.")
        pid = panel.get("id")
        if not isinstance(pid, str) or not pid or pid in identifiers:
            raise ArchitectureError("Panel ids must be nonempty and unique.")
        identifiers.add(pid)
        w, h, t = (
            positive(panel.get(field), f"{pid}.{field}")
            for field in ("width", "height", "thickness")
        )
        if not isinstance(panel.get("grain"), str) or panel.get("grain") not in {
            "width",
            "height",
            "none",
        }:
            raise ArchitectureError(f"{pid}.grain must be width, height or none.")
        if not isinstance(panel.get("material"), str) or not panel["material"].strip():
            raise ArchitectureError(f"{pid}.material is required.")
        rotate = allow_rotate and panel["grain"] == "none"
        if not (w <= sw and h <= sh) and not (rotate and h <= sw and w <= sh):
            raise ArchitectureError(
                "ak_sheet_fit", f"Panel {pid} does not fit the sheet with permitted grain."
            )
        checked.append((panel, w, h, t, rotate))
    checked.sort(key=lambda row: (-max(row[1:3]), -(row[1] * row[2]), row[0]["id"]))
    sheets: list[dict[str, Any]] = []
    for panel, w, h, t, rotate in checked:
        group = (panel["material"], t, panel["grain"])
        placed = False
        for sheet in [*sheets, None]:
            if sheet is None:
                sheet = {
                    "index": len(sheets) + 1,
                    "material": group[0],
                    "thickness": t,
                    "grain": group[2],
                    "width": sw,
                    "height": sh,
                    "placements": [],
                    "_rows": [],
                }
                sheets.append(sheet)
            if (sheet["material"], sheet["thickness"], sheet["grain"]) != group:
                continue
            options = [(w, h, False)] + ([(h, w, True)] if rotate and w != h else [])
            for rw, rh, rotated in options:
                if rw > sw or rh > sh:
                    continue
                for row in sheet["_rows"] + [None]:
                    if row is None:
                        y = (
                            sheet["_rows"][-1]["y"] + sheet["_rows"][-1]["h"] + k
                            if sheet["_rows"]
                            else 0.0
                        )
                        if y + rh > sh:
                            continue
                        row = {"x": 0.0, "y": y, "h": rh}
                        sheet["_rows"].append(row)
                    if rh <= row["h"] and row["x"] + rw <= sw:
                        sheet["placements"].append(
                            {
                                "id": panel["id"],
                                "x": row["x"],
                                "y": row["y"],
                                "width": rw,
                                "height": rh,
                                "rotated": rotated,
                            }
                        )
                        row["x"] += rw + k
                        placed = True
                        break
                if placed:
                    break
            if placed:
                break
    for sheet in sheets:
        del sheet["_rows"]
    return {
        "ok": True,
        "units": "mm",
        "sheet_count": len(sheets),
        "sheets": copy.deepcopy(sheets),
        "kerf": k,
        "allow_rotate": allow_rotate,
        "utilization": sum(w * h for _, w, h, _, _ in checked) / (len(sheets) * sw * sh),
        "method": "deterministic row packing; no optimality claim",
        "note": "Grained panels keep orientation; separate stock by material/thickness/grain. "
        "No edge trim or machining toolpath is assumed; CNC readiness not_verified.",
    }
