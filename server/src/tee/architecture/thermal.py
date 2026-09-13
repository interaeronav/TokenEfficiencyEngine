"""Explicit steady one-dimensional conduction scenarios, not building load sizing.

Series areal resistance: R = Rsi + sum(thickness_m / conductivity) + Rse.
For each explicitly assigned surface: H = area / R; outward heat flow = H * dT.
No default material, film, weather, adjacency or thermal boundary is inferred.
"""

from __future__ import annotations

import math
from typing import Any

from .model import ArchitectureError, number, positive
from .spatial import space_area_mm2, space_environment


def _fail(message: str) -> None:
    raise ArchitectureError("ak_thermal", message, "Correct the named thermal scenario value.")


def _text(value: Any, name: str, limit: int = 500) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        _fail(f"{name} needs nonempty text up to {limit} characters.")


def _rows(spec: dict, name: str, maximum: int, key: str = "id") -> list[dict]:
    rows = spec.get(name, [])
    if not isinstance(rows, list) or len(rows) > maximum:
        _fail(f"thermal.{name} needs a list of at most {maximum} rows.")
    identifiers = set()
    for row in rows:
        if not isinstance(row, dict):
            _fail(f"thermal.{name} rows must be objects.")
        _text(row.get(key), name + "." + key, 80)
        if row[key] in identifiers:
            _fail(f"Repeated thermal.{name} identifier {row[key]}.")
        identifiers.add(row[key])
        _text(row.get("source"), name + ".source")
    return rows


def _optional_number(value: Any, field: str, zero: bool = False) -> None:
    if value is not None:
        if zero:
            if number(value, field) < 0:
                _fail(field + " must be nonnegative or null.")
        else:
            positive(value, field)


def assembly_result(assembly: dict) -> dict:
    missing = []
    resistance = None
    if assembly["method"] == "declared_u":
        value = assembly["u_value_w_m2k"]
        if value is None:
            missing.append("u_value_w_m2k")
        else:
            resistance = 1 / value
    else:
        films = [assembly[k] for k in ("inside_resistance_m2k_w", "outside_resistance_m2k_w")]
        for key in ("inside_resistance_m2k_w", "outside_resistance_m2k_w"):
            if assembly[key] is None:
                missing.append(key)
        layers = []
        for index, layer in enumerate(assembly["layers"]):
            for key in ("thickness_mm", "conductivity_w_mk"):
                if layer[key] is None:
                    missing.append(f"layers[{index}].{key}")
            if layer["thickness_mm"] is not None and layer["conductivity_w_mk"] is not None:
                layers.append(layer["thickness_mm"] / 1000 / layer["conductivity_w_mk"])
        if not missing:
            resistance = sum(films) + sum(layers)
        value = 1 / resistance if resistance and math.isfinite(resistance) else None
    if not missing and (
        resistance is None
        or not math.isfinite(resistance)
        or resistance <= 0
        or value is None
        or not math.isfinite(value)
        or value <= 0
    ):
        _fail(f"Assembly {assembly['id']} resistance/transmittance exceeds numerical range.")
    return {
        "id": assembly["id"],
        "name": assembly["name"],
        "method": assembly["method"],
        "source": assembly["source"],
        "missing": missing,
        "status": "incomplete" if missing else "calculated_from_declared_inputs",
        "resistance_m2k_w": resistance,
        "u_value_w_m2k": value,
        "scope": "declared whole-product value"
        if assembly["method"] == "declared_u"
        else "one-dimensional continuous layers; framing and thermal bridges excluded",
    }


def definitions(state: dict) -> tuple[list[dict], list[dict], list[dict]]:
    if "thermal" not in state["project"]["facts"]:
        return [], [], []
    spec = state["project"]["facts"]["thermal"]
    if not isinstance(spec, dict) or set(spec) - {"assemblies", "zones", "surfaces"}:
        _fail("thermal accepts assemblies, zones and surfaces only.")
    assemblies = _rows(spec, "assemblies", 64)
    zones = _rows(spec, "zones", 64)
    surfaces = _rows(spec, "surfaces", 200, "entity_id")
    for assembly in assemblies:
        _text(assembly.get("name"), "assembly.name", 160)
        base = {"id", "name", "source", "method"}
        if assembly.get("method") == "declared_u":
            if set(assembly) != base | {"u_value_w_m2k"}:
                _fail("declared_u needs a whole-product u_value_w_m2k, or null.")
            _optional_number(assembly["u_value_w_m2k"], "u_value_w_m2k")
        elif assembly.get("method") == "layers":
            if set(assembly) != base | {
                "layers",
                "inside_resistance_m2k_w",
                "outside_resistance_m2k_w",
            }:
                _fail("layers needs explicit layers and inside/outside_resistance_m2k_w.")
            for key in ("inside_resistance_m2k_w", "outside_resistance_m2k_w"):
                _optional_number(assembly[key], key, zero=True)
            layers = assembly["layers"]
            if not isinstance(layers, list) or not 1 <= len(layers) <= 16:
                _fail("Each assembly needs 1-16 explicit continuous layers.")
            for layer in layers:
                if not isinstance(layer, dict) or set(layer) != {
                    "name",
                    "source",
                    "thickness_mm",
                    "conductivity_w_mk",
                }:
                    _fail("Layer needs name, source, thickness_mm and conductivity_w_mk.")
                _text(layer["name"], "layer.name", 160)
                _text(layer["source"], "layer.source")
                for key in ("thickness_mm", "conductivity_w_mk"):
                    _optional_number(layer[key], key)
        else:
            _fail("Thermal assembly method must be layers or declared_u.")
        assembly_result(assembly)
    entities, assigned_spaces = state["entities"], set()
    for zone in zones:
        if set(zone) != {"id", "space_ids", "temperature_c", "source"}:
            _fail("Zone needs id, space_ids, temperature_c and source.")
        temperature = number(zone["temperature_c"], "zone.temperature_c")
        if temperature <= -273.15:
            _fail("Temperature must be above absolute zero.")
        if not isinstance(zone["space_ids"], list) or not 1 <= len(zone["space_ids"]) <= 128:
            _fail("Zone space_ids needs 1-128 distinct interior conditioned spaces.")
        for identifier in zone["space_ids"]:
            if not isinstance(identifier, str) or identifier not in entities:
                _fail("Zone references an unknown space.")
            entity = entities[identifier]
            if (
                entity["kind"] != "space"
                or space_environment(entity) != "interior"
                or entity.get("conditioned") is not True
            ):
                _fail("Thermal zones require explicit interior, conditioned=true spaces.")
            if identifier in assigned_spaces:
                _fail("A space cannot be repeated or assigned to multiple thermal zones.")
            assigned_spaces.add(identifier)
    aids, zids = {a["id"] for a in assemblies}, {z["id"] for z in zones}
    for surface in surfaces:
        if set(surface) != {
            "entity_id",
            "zone_id",
            "assembly_id",
            "boundary_temperature_c",
            "source",
        }:
            _fail("Surface needs entity_id, zone_id, assembly_id, boundary_temperature_c, source.")
        for key, known in (("zone_id", zids), ("assembly_id", aids)):
            if not isinstance(surface[key], str) or surface[key] not in known:
                _fail(f"Surface {key} must reference a declared thermal definition.")
        entity = entities.get(surface["entity_id"])
        if entity is None or entity["kind"] not in {"wall", "opening", "roof", "slab"}:
            _fail("Thermal surfaces support native walls, filled openings, roofs and slabs.")
        if entity["kind"] == "opening" and entity["fill"] not in {"window", "door"}:
            _fail("An unfilled opening is not a conductive product.")
        if (
            entity["kind"] == "opening"
            and next(a["method"] for a in assemblies if a["id"] == surface["assembly_id"])
            != "declared_u"
        ):
            _fail("Filled openings require a declared whole-product U-value, not glazing layers.")
        if number(surface["boundary_temperature_c"], "boundary_temperature_c") <= -273.15:
            _fail("Temperature must be above absolute zero.")
    return assemblies, zones, surfaces


def validate_thermal(state: dict) -> None:
    definitions(state)


def _area(entity: dict, entities: dict) -> tuple[float, str]:
    kind = entity["kind"]
    if kind == "wall":
        holes = sum(
            e["width"] * e["height"]
            for e in entities.values()
            if e["kind"] == "opening" and e["wall"] == entity["id"]
        )
        return (
            (math.dist(entity["start"], entity["end"]) * entity["height"] - holes) / 1e6,
            "net centreline face less all hosted apertures; junction adjustments excluded",
        )
    if kind == "opening":
        return entity["width"] * entity["height"] / 1e6, "full aperture; needs whole-product U"
    if kind == "roof":
        from .systems import roof_quantities

        return (
            roof_quantities(entity, entities[entity["storey"]]["elevation"])["slope_area_m2"],
            "full sloped model surface including authored eaves; thermal boundary not inferred",
        )
    from .penetrations import slab_quantities

    return slab_quantities(entity, entities)["net_area_m2"], "net slab plan less hosted voids"


def report(state: dict) -> dict:
    assemblies, zones, surfaces = definitions(state)
    materials = {a["id"]: assembly_result(a) for a in assemblies}
    climates = {z["id"]: z for z in zones}
    assignments = {s["entity_id"]: s for s in surfaces}
    entities = state["entities"]
    surface_rows = []
    for identifier, entity in sorted(entities.items()):
        if entity["kind"] not in {"wall", "opening", "roof", "slab"}:
            continue
        area, basis = _area(entity, entities)
        assignment = assignments.get(identifier)
        row = {
            "id": identifier,
            "kind": entity["kind"],
            "name": entity["name"],
            "area_m2": area,
            "area_basis": basis,
            "status": "not_assigned",
            "conductance_w_k": None,
            "outward_heat_flow_w": None,
        }
        if assignment:
            assembly = materials[assignment["assembly_id"]]
            delta = (
                climates[assignment["zone_id"]]["temperature_c"]
                - assignment["boundary_temperature_c"]
            )
            u = assembly["u_value_w_m2k"]
            conductance = area * u if u is not None else None
            flow = conductance * delta if conductance is not None else None
            if any(v is not None and not math.isfinite(v) for v in (delta, conductance, flow)):
                _fail(f"Surface {identifier} calculation exceeds numerical range.")
            row.update(
                {
                    **assignment,
                    "temperature_difference_k": delta,
                    "status": "assembly_incomplete" if u is None else "calculated_scenario",
                    "conductance_w_k": conductance,
                    "outward_heat_flow_w": flow,
                }
            )
        surface_rows.append(row)
    space_zones = {i: z["id"] for z in zones for i in z["space_ids"]}
    space_rows = [
        {
            "id": i,
            "environment": space_environment(e),
            "conditioned": e.get("conditioned"),
            "zone_id": space_zones.get(i),
            "reference_area_m2": space_area_mm2(e) / 1e6,
        }
        for i, e in sorted(entities.items())
        if e["kind"] == "space"
    ]
    zone_rows = []
    for zone in zones:
        selected = [r for r in surface_rows if r.get("zone_id") == zone["id"]]
        calculated = [r for r in selected if r["status"] == "calculated_scenario"]
        zone_rows.append(
            {
                **zone,
                "selected_surface_count": len(selected),
                "calculated_surface_count": len(calculated),
                "missing_surface_count": len(selected) - len(calculated),
                "selected_conductance_subtotal_w_k": sum(r["conductance_w_k"] for r in calculated)
                if calculated
                else None,
                "selected_outward_heat_flow_subtotal_w": sum(
                    r["outward_heat_flow_w"] for r in calculated
                )
                if calculated
                else None,
                "conditioned_reference_area_m2": sum(
                    r["reference_area_m2"] for r in space_rows if r["zone_id"] == zone["id"]
                ),
                "whole_building_load_w": None,
            }
        )
    return {
        "document_id": state["document_id"],
        "revision": state["revision"],
        "configured": bool(assemblies or zones or surfaces),
        "assemblies": list(materials.values()),
        "surfaces": surface_rows,
        "zones": zone_rows,
        "spaces": space_rows,
        "units": {"resistance": "m2 K/W", "u_value": "W/(m2 K)", "heat_flow": "W"},
        "scope": (
            "Selected-surface steady 1D scenario, positive heat flow outward. Native surface "
            "inventory is not an established thermal boundary. No infiltration, ventilation, "
            "solar gain, moisture, thermal bridges, ground coupling, dynamic energy or code check."
        ),
    }
