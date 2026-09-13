"""Explicit casework panels share the normal recipe/stock/machining pipeline.

Useful for a continuous run plinth, fillers and authored shop variants. No
carcass, back, front, gap or fitting is silently added to a panel set.
"""

from __future__ import annotations

from .model import ArchitectureError, _point, number, positive


def explicit_parts(entity: dict, spec: dict) -> tuple[list[dict], dict]:
    from .cabinet_production import (
        _ROLES,
        SCHEMA,
        _enum,
        _identifier,
        _object,
        _rows,
        _text,
    )

    _object(
        spec, "panel_set", {"schema", "family", "mode", "parts", "hardware", "machining", "costing"}
    )
    if (
        spec.get("mode") != "explicit"
        or entity.get("shelves") != 0
        or entity.get("doors") != 0
        or entity.get("plinth_height") != 0
    ):
        raise ArchitectureError(
            "panel_set needs mode=explicit and shelves=doors=plinth_height=0; supply every part."
        )
    overall = [positive(entity.get(k), k) for k in ("width", "depth", "height")]
    _point(entity.get("origin"), "cabinet.origin", 3)
    rows, seen = [], set()
    parts = _rows(spec.get("parts"), "panel_set.parts", 200)
    if not parts:
        raise ArchitectureError("panel_set.parts must contain at least one part.")
    for part in parts:
        _object(
            part,
            "part",
            {
                "id",
                "role",
                "origin_mm",
                "orientation",
                "finished_width_mm",
                "finished_height_mm",
                "thickness_mm",
                "material",
                "grain",
                "edges_mm",
                "source",
            },
        )
        identifier = _identifier(part.get("id"), "part.id")
        if identifier in seen:
            raise ArchitectureError("Duplicate panel_set part id.")
        seen.add(identifier)
        role = _enum(part.get("role"), "part.role", _ROLES)
        orientation = _enum(part.get("orientation"), "part.orientation", {"XY", "XZ", "YZ"})
        w, h, t = [
            positive(part.get(k), k)
            for k in ("finished_width_mm", "finished_height_mm", "thickness_mm")
        ]
        _point(part.get("origin_mm"), "part.origin_mm", 3)
        material = _text(part.get("material"), "part.material")
        grain = _enum(part.get("grain"), "part.grain", {"width", "height", "none"})
        raw_edges = _object(
            part.get("edges_mm"), "part.edges_mm", {"left", "right", "top", "bottom"}
        )
        if set(raw_edges) != {"left", "right", "top", "bottom"}:
            raise ArchitectureError("Declare all four part edges; use zero for an unbanded edge.")
        edges = {k: number(v, f"part.edges_mm.{k}", minimum=0) for k, v in raw_edges.items()}
        if any(v > t / 2 for v in edges.values()):
            raise ArchitectureError("Part edge band exceeds half the panel thickness.")
        cw, ch = w - edges["left"] - edges["right"], h - edges["top"] - edges["bottom"]
        if min(cw, ch) <= 0:
            raise ArchitectureError("Part edges consume the blank.")
        size = {"XY": [w, h, t], "XZ": [w, t, h], "YZ": [t, w, h]}[orientation]
        source = _object(
            part.get("source"), "part.source", {"kind", "title", "revision", "reference"}
        )
        _enum(
            source.get("kind"),
            "part.source.kind",
            {"design_record", "shop_specification", "manufacturer_document"},
        )
        for key in ("title", "revision", "reference"):
            _text(source.get(key), f"part.source.{key}", 1024)
        rows.append(
            {
                "id": entity["id"] + "_" + identifier,
                "name": entity["name"] + " " + identifier,
                "role": role,
                "width": cw,
                "height": ch,
                "thickness": t,
                "finished_width": w,
                "finished_height": h,
                "origin": [entity["origin"][i] + part["origin_mm"][i] for i in range(3)],
                "orientation": orientation,
                "size": size,
                "grain": grain,
                "edges": edges,
                "material": material,
                "source": dict(source),
            }
        )
    return rows, {
        "schema": SCHEMA,
        "family": "panel_set",
        "mode": "explicit",
        "front_mode": "authored parts",
        "overall_mm": overall,
        "clear_internal_mm": None,
        "front_sections": [],
        "panel_count": len(rows),
        "quantity_basis": "declared panels only; joints and supports unverified",
    }
