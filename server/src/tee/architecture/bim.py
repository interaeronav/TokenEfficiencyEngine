"""Bounded, versioned BIM types and explicit opening construction for A83.

Pure validation/resolution has no geometry or IFC dependency. A type is a real
library definition; occurrence overrides are named, and never include placement.
"""

from __future__ import annotations

import copy
import math
import re
from typing import Any

SCHEMA = "tee-bim/1"
PARAMETERS = {
    "wall": {"thickness", "height"},
    "opening": {"width", "height", "fill", "assembly"},
    "space": {"height"},
    "member": {"profile", "holes", "role", "length"},
    "slab": {"thickness"},
    "roof": {"thickness", "form", "pitch_deg"},
    "stair": {"width", "riser_count", "going", "waist_thickness", "landing_depth"},
    "furnishing": {"size", "category"},
    "cabinet": {
        "width",
        "depth",
        "height",
        "panel_thickness",
        "back_thickness",
        "shelves",
        "doors",
        "plinth_height",
        "grain",
        "edge_band_mm",
        "material",
    },
}
_ID = re.compile(r"[A-Za-z0-9_-]{1,80}\Z")
_VALUE_TYPES = {
    "label": "IfcLabel",
    "text": "IfcText",
    "identifier": "IfcIdentifier",
    "boolean": "IfcBoolean",
    "integer": "IfcInteger",
    "real": "IfcReal",
    "length": "IfcLengthMeasure",
    "area": "IfcAreaMeasure",
    "volume": "IfcVolumeMeasure",
    "ratio": "IfcRatioMeasure",
    "thermal_transmittance": "IfcThermalTransmittanceMeasure",
}
_UNITS = {"length": {"mm", "m"}, "area": {"m2"}, "volume": {"m3"}}
_CATEGORIES = {"bed", "sofa", "table", "chair", "basin", "wc", "shower", "appliance", "storage"}


def _error(message: str) -> None:
    from .model import ArchitectureError

    raise ArchitectureError(
        "ak_bim_invalid", message, "Correct the named BIM definition or override."
    )


def _map(value: Any, name: str, limit: int = 128) -> dict:
    if not isinstance(value, dict) or len(value) > limit:
        _error(f"{name} must be a mapping of at most {limit} entries.")
    return value


def _text(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 512:
        _error(f"{name} must be nonempty text of at most 512 characters.")


def _number(value: Any, name: str, *, positive: bool = True) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        _error(f"{name} must be a finite number.")
    if abs(value) > 1e9 or (value <= 0 if positive else value < 0):
        _error(f"{name} is outside its supported positive/nonnegative range.")
    return float(value)


def _reference(value: Any, table: dict, name: str, *, optional: bool = True) -> None:
    if value is None and optional:
        return
    if not isinstance(value, str) or value not in table:
        _error(f"{name} references an unknown definition.")


def _choice(value: Any, choices: set[str], name: str) -> None:
    if not isinstance(value, str) or value not in choices:
        _error(f"{name} must be one of {', '.join(sorted(choices))}.")


def library(state: dict) -> dict:
    return state.get("project", {}).get("facts", {}).get("bim", {})


def value_spec(value: Any) -> tuple[str, Any, str | None]:
    """Return IFC simple type/value/explicit unit; validate without importing IFC."""
    unit = None
    if isinstance(value, dict):
        if set(value) - {"value", "type", "unit"} or "value" not in value or "type" not in value:
            _error("Typed BIM property needs value, type and optional unit only.")
        kind = value["type"]
        if not isinstance(kind, str):
            _error("BIM property type must be text.")
        reverse = {v: k for k, v in _VALUE_TYPES.items()}
        kind = reverse.get(kind, kind)
        if kind not in _VALUE_TYPES:
            _error(f"Unsupported BIM property type {kind}.")
        unit, value = value.get("unit"), value["value"]
        if unit is not None and (not isinstance(unit, str) or unit not in _UNITS.get(kind, set())):
            _error(f"Unit {unit} is not supported for {kind}.")
        if kind in _UNITS and unit is None:
            _error(f"BIM {kind} property needs an explicit unit.")
    else:
        kind = (
            "boolean"
            if isinstance(value, bool)
            else "integer"
            if isinstance(value, int)
            else ("real" if isinstance(value, float) else "label")
        )
    if kind in {"label", "text", "identifier"}:
        _text(value, "BIM text property")
    elif kind == "boolean":
        if type(value) is not bool:
            _error("BIM boolean property must be true or false.")
    elif kind == "integer":
        if type(value) is not int or abs(value) > 2**53:
            _error("BIM integer property must be an exact bounded integer.")
    elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        _error("BIM numeric property must be finite.")
    elif abs(value) > 1e12:
        _error("BIM numeric property exceeds the supported magnitude.")
    return _VALUE_TYPES[kind], value, unit


def _properties(mapping: Any) -> None:
    for name, properties in _map(mapping, "property_sets", 32).items():
        _text(name, "Property set name")
        if name in {"TEE_Architecture", "TEE_OpeningAssembly"}:
            _error(f"{name} is reserved for authored export identity/construction.")
        if not properties:
            _error(f"Property set {name} must contain at least one property.")
        for property_name, value in _map(properties, f"Property set {name}", 64).items():
            _text(property_name, "Property name")
            value_spec(value)


def _classifications(rows: Any) -> None:
    if not isinstance(rows, list) or len(rows) > 16:
        _error("classifications must be a list of at most 16 references.")
    seen = set()
    for row in rows:
        row = _map(row, "classification", 5)
        if set(row) - {"system", "code", "name", "edition", "location"}:
            _error("Classification has unsupported fields.")
        for field in {"system", "code"} | set(row):
            _text(row.get(field), f"Classification {field}")
        identity = (row["system"], row.get("edition"), row["code"])
        if identity in seen:
            _error("Duplicate classification reference.")
        seen.add(identity)


def _definitions(state: dict) -> dict:
    data = _map(library(state), "project.facts.bim", 3)
    if not data:
        return {"materials": {}, "types": {}}
    if data.get("schema") != SCHEMA or set(data) - {"schema", "materials", "types"}:
        _error(f"project.facts.bim requires schema {SCHEMA}, materials and types.")
    materials = _map(data.get("materials", {}), "BIM materials", 128)
    types = _map(data.get("types", {}), "BIM types", 128)
    for identifier, material in materials.items():
        if not isinstance(identifier, str) or not _ID.fullmatch(identifier):
            _error("Invalid BIM material identifier.")
        material = _map(material, "material", 6)
        if set(material) - {"name", "description", "category", "property_sets"}:
            _error(f"Material {identifier} has unsupported fields.")
        _text(material.get("name"), "Material name")
        for field in {"description", "category"} & set(material):
            _text(material[field], f"Material {field}")
        _properties(material.get("property_sets", {}))
    for identifier, definition in types.items():
        if not isinstance(identifier, str) or not _ID.fullmatch(identifier):
            _error("Invalid BIM type identifier.")
        definition = _map(definition, "type", 8)
        if set(definition) - {
            "name",
            "kind",
            "parameters",
            "material_layers",
            "material_id",
            "classifications",
            "property_sets",
            "description",
        }:
            _error(f"Type {identifier} has unsupported fields.")
        _text(definition.get("name"), "Type name")
        kind = definition.get("kind")
        if not isinstance(kind, str) or kind not in PARAMETERS:
            _error(f"Unsupported BIM type kind {kind}.")
        parameters = _map(definition.get("parameters", {}), "type parameters", 32)
        if set(parameters) - PARAMETERS[kind]:
            _error(f"Type {identifier} contains unsupported or placement parameters.")
        _validate_parameters(kind, parameters)
        _reference(definition.get("material_id"), materials, f"Type {identifier} material")
        layers = definition.get("material_layers", [])
        if not isinstance(layers, list) or len(layers) > 32:
            _error("material_layers must be a list of at most 32 layers.")
        if layers and (kind not in {"wall", "slab", "roof"} or definition.get("material_id")):
            _error("Material layers require wall/slab/roof and cannot coexist with material_id.")
        if layers and kind == "roof" and parameters.get("form", "flat") != "flat":
            _error(
                "Pitched roof material layers require per-plane usage, which is not yet supported."
            )
        for layer in layers:
            layer = _map(layer, "material layer", 3)
            if set(layer) - {"material_id", "thickness_mm", "role"}:
                _error(f"Type {identifier} has an invalid material layer.")
            _reference(layer.get("material_id"), materials, "Layer material", optional=False)
            _number(layer.get("thickness_mm"), "Layer thickness_mm")
            _text(layer.get("role"), "Layer role")
        if (
            layers
            and "thickness" in parameters
            and not math.isclose(
                sum(layer["thickness_mm"] for layer in layers),
                parameters["thickness"],
                abs_tol=1e-6,
                rel_tol=0,
            )
        ):
            _error(f"Type {identifier} layer sum differs from thickness.")
        _properties(definition.get("property_sets", {}))
        _classifications(definition.get("classifications", []))
    return {"materials": materials, "types": types}


def _validate_parameters(kind: str, parameters: dict) -> None:
    for name, value in parameters.items():
        if name in {"fill", "assembly", "form", "category", "profile", "holes", "role"}:
            continue
        if name == "size":
            if not isinstance(value, list) or len(value) != 3:
                _error("Furnishing type size requires three positive dimensions.")
            for coordinate in value:
                _number(coordinate, "Type size")
        elif name in {"grain", "material"}:
            _text(value, f"Type {name}")
            if name == "grain":
                _choice(value, {"width", "height", "none"}, "Type grain")
        elif name == "riser_count":
            if type(value) is not int or not 2 <= value <= 64:
                _error("Type riser_count requires an integer from 2 to 64.")
        elif name in {"shelves", "doors"}:
            limit = 2 if name == "doors" else 100
            if type(value) is not int or not 0 <= value <= limit:
                _error(f"Type {name} requires a nonnegative integer at most {limit}.")
        else:
            _number(
                value,
                f"Type {name}",
                positive=name
                not in {"plinth_height", "edge_band_mm", "landing_depth", "pitch_deg"},
            )
    if kind == "member":
        from .members import IFC_ROLES, validate_member

        _choice(parameters.get("role"), set(IFC_ROLES), "Member type role")
        if "profile" not in parameters:
            _error("Member type requires a profile; placement is supplied by each occurrence.")
        validate_member(
            {
                "origin": [0, 0, 0],
                "axis": [0, 0, 1],
                "x_direction": [1, 0, 0],
                "length": 1,
                **parameters,
            }
        )
    if kind == "opening":
        _choice(parameters.get("fill"), {"window", "door"}, "Opening type fill")
        if "assembly" in parameters:
            entity = {
                "fill": parameters["fill"],
                "width": parameters.get("width", 1e9),
                "height": parameters.get("height", 1e9),
                "properties": {"assembly": parameters["assembly"]},
            }
            opening_assembly(entity)
    if kind == "furnishing":
        _choice(parameters.get("category"), _CATEGORIES, "Furnishing type category")
    if "form" in parameters:
        _choice(parameters["form"], {"flat", "mono", "gable", "planes"}, "Roof type form")
    if kind == "roof" and "pitch_deg" in parameters:
        pitch = parameters["pitch_deg"]
        if (
            pitch >= 80
            or (parameters.get("form") == "flat" and pitch != 0)
            or (parameters.get("form") == "planes" and pitch != 0)
            or (parameters.get("form") in {"mono", "gable"} and pitch == 0)
        ):
            _error(
                "Roof type pitch must be zero/omitted for flat or explicit planes, and greater "
                "than 0, below 80 for mono/gable; plane pitches derive from their top vertices."
            )


def opening_assembly(entity: dict, wall_thickness: float | None = None) -> dict | None:
    """Explicit closed-position, single-panel construction; no hardware inference."""
    assembly = entity.get("properties", {}).get("assembly")
    if assembly is None:
        return None
    assembly = _map(assembly, "opening assembly", 16)
    allowed = {
        "operation",
        "hinge",
        "swing_side",
        "frame_width_mm",
        "frame_depth_mm",
        "reveal_mm",
        "glazing_thickness_mm",
        "leaf_thickness_mm",
        "clearance_mm",
        "frame_material_id",
        "glazing_material_id",
        "leaf_material_id",
    }
    if set(assembly) - allowed:
        _error("Opening assembly has unsupported fields.")
    _choice(entity.get("fill"), {"window", "door"}, "Constructed opening fill")
    _choice(assembly.get("operation"), {"fixed", "swing", "sliding"}, "Opening operation")
    if assembly["operation"] == "swing":
        _choice(assembly.get("hinge"), {"start", "end"}, "Swing hinge")
        _choice(assembly.get("swing_side"), {"left", "right"}, "Swing side")
    elif "hinge" in assembly or "swing_side" in assembly:
        _error("Hinge/swing_side only apply to a swing assembly.")
    width = _number(assembly.get("frame_width_mm"), "frame_width_mm")
    depth = _number(assembly.get("frame_depth_mm"), "frame_depth_mm")
    reveal = _number(assembly.get("reveal_mm"), "reveal_mm", positive=False)
    if width * 2 >= entity["width"] or width * 2 >= entity["height"]:
        _error("Opening frame consumes the clear opening.")
    if wall_thickness is not None and reveal + depth > wall_thickness + 1e-6:
        _error("Opening frame/reveal extends beyond the supported wall thickness.")
    if entity["fill"] == "window":
        pane = _number(assembly.get("glazing_thickness_mm"), "glazing_thickness_mm")
        if pane > depth or "leaf_thickness_mm" in assembly or "clearance_mm" in assembly:
            _error("Window glazing must fit frame depth; leaf_thickness_mm is door-only.")
    else:
        leaf = _number(assembly.get("leaf_thickness_mm"), "leaf_thickness_mm")
        gap = _number(assembly.get("clearance_mm"), "clearance_mm", positive=False)
        if (
            leaf > depth
            or 2 * (width + gap) >= entity["width"]
            or width + 2 * gap >= entity["height"]
        ):
            _error("Door leaf or clearance does not fit the frame.")
        if "glazing_thickness_mm" in assembly:
            _error("glazing_thickness_mm is window-only in this assembly contract.")
    return assembly


def resolve_types(state: dict, explicit_updates: dict[str, set[str]] | None = None) -> dict:
    """Resolve library parameters once after a candidate batch; placement is untouched."""
    definitions = _definitions(state)
    for identifier, entity in state["entities"].items():
        binding = entity.get("properties", {}).get("bim", {})
        if not isinstance(binding, dict):
            _error(f"Entity {identifier} BIM binding must be a mapping.")
        _reference(binding.get("type_id"), definitions["types"], f"Entity {identifier} type")
        if not binding.get("type_id"):
            continue
        definition = definitions["types"].get(binding["type_id"])
        if definition is None or definition["kind"] != entity["kind"]:
            _error(f"Entity {identifier} has unknown or incompatible type.")
        parameters = definition.get("parameters", {})
        overrides = binding.get("overrides", [])
        if not isinstance(overrides, list) or any(not isinstance(k, str) for k in overrides):
            _error(f"Entity {identifier} override names must be a list.")
        changed = (explicit_updates or {}).get(identifier, set()) & set(parameters)
        binding["overrides"] = sorted(set(overrides) | changed)
        for name, value in parameters.items():
            if name not in binding["overrides"]:
                if name == "assembly":
                    entity["properties"]["assembly"] = copy.deepcopy(value)
                else:
                    entity[name] = copy.deepcopy(value)
    return state


def validate_bim(state: dict) -> None:
    """Validate already resolved state without mutation, including saved-state integrity."""
    definitions = _definitions(state)
    for identifier, entity in state.get("entities", {}).items():
        props = entity.get("properties", {})
        binding = _map(props.get("bim", {}), f"Entity {identifier} BIM binding", 5)
        if set(binding) - {
            "type_id",
            "overrides",
            "property_sets",
            "classifications",
            "material_id",
        }:
            _error(f"Entity {identifier} has unsupported BIM binding fields.")
        _properties(binding.get("property_sets", {}))
        if entity["kind"] == "space":
            from .spatial import space_environment

            environment = space_environment(entity)
            definition = definitions["types"].get(binding.get("type_id"), {})
            for properties in (
                binding.get("property_sets", {}),
                definition.get("property_sets", {}),
            ):
                external = properties.get("Pset_SpaceCommon", {}).get("IsExternal")
                if external is not None:
                    _, external, _ = value_spec(external)
                    if (
                        type(external) is not bool
                        or environment == "unclassified"
                        or external != (environment == "exterior")
                    ):
                        _error(
                            f"Entity {identifier} IsExternal must agree with "
                            "its explicit space environment."
                        )
        _classifications(binding.get("classifications", []))
        _reference(
            binding.get("material_id"), definitions["materials"], f"Entity {identifier} material"
        )
        _reference(binding.get("type_id"), definitions["types"], f"Entity {identifier} type")
        overrides = binding.get("overrides", [])
        if (
            not isinstance(overrides, list)
            or any(not isinstance(k, str) for k in overrides)
            or len(set(overrides)) != len(overrides)
        ):
            _error(f"Entity {identifier} override names must be unique strings.")
        if binding.get("type_id"):
            definition = definitions["types"].get(binding["type_id"])
            if definition is None or definition["kind"] != entity["kind"]:
                _error(f"Entity {identifier} has unknown or incompatible type.")
            parameters = definition.get("parameters", {})
            if set(overrides) - set(parameters):
                _error(f"Entity {identifier} overrides a parameter its type does not define.")
            for name, value in parameters.items():
                actual = props.get("assembly") if name == "assembly" else entity.get(name)
                if name not in overrides and actual != value:
                    _error(f"Entity {identifier} parameter {name} disagrees with its type.")
            if entity["kind"] == "opening" and entity["fill"] != parameters["fill"]:
                _error("An opening fill category cannot override its IFC type category.")
            if entity["kind"] == "furnishing" and entity["category"] != parameters["category"]:
                _error("A furnishing category cannot override its IFC type category.")
            layers = definition.get("material_layers", [])
            if layers and entity["kind"] == "roof" and entity["form"] != "flat":
                _error(
                    "Pitched roof material layers require per-plane usage, which is not yet"
                    " supported."
                )
            if layers and not math.isclose(
                sum(x["thickness_mm"] for x in layers), entity["thickness"], abs_tol=1e-6, rel_tol=0
            ):
                _error(f"Entity {identifier} material layer sum differs from geometry thickness.")
            if layers and binding.get("material_id"):
                _error("A layered type cannot be replaced by a single occurrence material.")
        elif overrides:
            _error(f"Entity {identifier} has overrides without a type.")
        if entity["kind"] == "opening":
            wall = state["entities"].get(entity["wall"])
            assembly = opening_assembly(entity, wall.get("thickness") if wall else None)
            if assembly:
                for field in ("frame_material_id", "glazing_material_id", "leaf_material_id"):
                    if field in assembly:
                        _reference(
                            assembly[field],
                            definitions["materials"],
                            f"Opening {identifier} {field}",
                            optional=False,
                        )


def opening_components(entity: dict, wall_thickness: float) -> list[dict]:
    """Boxes in opening-local x/z; y is wall-local (-face + reveal), all mm."""
    assembly = opening_assembly(entity, wall_thickness)
    if assembly is None:
        return []
    width, height = entity["width"], entity["height"]
    fw, depth = assembly["frame_width_mm"], assembly["frame_depth_mm"]
    y = -wall_thickness / 2 + assembly["reveal_mm"]
    parts = []

    def add(name: str, role: str, origin: list[float], size: list[float]) -> None:
        parts.append(
            {
                "name": name,
                "material_role": role,
                "origin": origin,
                "size": size,
                "material_id": assembly.get(role + "_material_id"),
            }
        )

    add("jamb-start", "frame", [0, y, 0], [fw, depth, height])
    add("jamb-end", "frame", [width - fw, y, 0], [fw, depth, height])
    add("head", "frame", [fw, y, height - fw], [width - 2 * fw, depth, fw])
    if entity["fill"] == "window":
        add("sill", "frame", [fw, y, 0], [width - 2 * fw, depth, fw])
        pane = assembly["glazing_thickness_mm"]
        add(
            "pane",
            "glazing",
            [fw, y + (depth - pane) / 2, fw],
            [width - 2 * fw, pane, height - 2 * fw],
        )
    else:
        leaf, gap = assembly["leaf_thickness_mm"], assembly["clearance_mm"]
        add(
            "leaf",
            "leaf",
            [fw + gap, y + (depth - leaf) / 2, gap],
            [width - 2 * fw - 2 * gap, leaf, height - fw - 2 * gap],
        )
    return parts


def bim_report(state: dict) -> dict:
    """Compact semantic coverage; never declares professional/IDS/code completeness."""
    definitions = _definitions(state)
    instances = []
    unspecified = []
    information = []
    for identifier, entity in state["entities"].items():
        binding = entity.get("properties", {}).get("bim", {})
        definition = definitions["types"].get(binding.get("type_id"), {})
        missing = []
        if entity["kind"] not in {"storey", "virtual_boundary", "slab_opening"}:
            if not binding.get("type_id"):
                missing.append("type_assignment")
            if entity["kind"] != "space" and not (
                binding.get("material_id")
                or definition.get("material_layers")
                or definition.get("material_id")
            ):
                missing.append("IFC_material_assignment")
            if not entity.get("provenance"):
                missing.append("source_provenance")
        if entity["kind"] == "space":
            from .spatial import space_environment

            if space_environment(entity) == "unclassified":
                missing.append("space_environment")
        if entity["kind"] == "member":
            missing.append("connection_and_capacity_verification")
            if entity["role"] in {"pipe", "duct"}:
                missing.append("system_connectivity_and_performance")
        if missing:
            information.append({"id": identifier, "kind": entity["kind"], "review": missing})
        if binding.get("type_id"):
            instances.append(
                {
                    "id": identifier,
                    "type_id": binding["type_id"],
                    "overrides": binding.get("overrides", []),
                }
            )
        if (
            entity["kind"] == "opening"
            and entity["fill"] != "void"
            and not opening_assembly(entity)
        ):
            unspecified.append(identifier)
    return {
        "schema": SCHEMA,
        "types": len(definitions["types"]),
        "materials": len(definitions["materials"]),
        "typed_instances": len(instances),
        "instances": instances,
        "unconstructed_fillings": unspecified,
        "information_gaps": sorted(information, key=lambda row: row["id"]),
        "information_basis": (
            "Review prompts, not IFC invalidity or project-specific IDS requirements."
        ),
        "ids": "not_verified",
        "regulatory": "not_verified",
        "full_bim_parity": "not_verified",
    }


def export_semantics(file: Any, state: dict, products: dict[str, Any]) -> dict:
    """Write IFC4 native type/material/property/classification relationships.

    ``products`` maps opening IDs to their filling, not the host's void. Pure
    validation has already run; IFC APIs are imported only for this operation.
    """
    import ifcopenshell.api

    from .exchange import _guid

    run = ifcopenshell.api.run
    data = _definitions(state)
    materials = {}
    for identifier, definition in data["materials"].items():
        materials[identifier] = run(
            "material.add_material",
            file,
            name=definition["name"],
            description=definition.get("description"),
            category=definition.get("category"),
        )
    units = {}

    def unit(name: str | None) -> Any:
        if name is None:
            return None
        if name not in units:
            kind = {"mm": "LENGTHUNIT", "m": "LENGTHUNIT", "m2": "AREAUNIT", "m3": "VOLUMEUNIT"}[
                name
            ]
            units[name] = run(
                "unit.add_si_unit", file, unit_type=kind, prefix="MILLI" if name == "mm" else None
            )
        return units[name]

    def properties(product: Any, mappings: dict) -> None:
        for name, values in mappings.items():
            pset = run("pset.add_pset", file, product=product, name=name)
            if pset.is_a("IfcRoot"):
                pset.GlobalId = _guid(product.GlobalId + ":pset:" + name, state["document_id"])
            entries = []
            for key, value in values.items():
                kind, nominal, explicit_unit = value_spec(value)
                entries.append(
                    file.create_entity(
                        "IfcPropertySingleValue",
                        Name=key,
                        NominalValue=file.create_entity(kind, nominal),
                        Unit=unit(explicit_unit),
                    )
                )
            if pset.is_a("IfcMaterialProperties"):
                pset.Properties = entries
            else:
                pset.HasProperties = entries

    classifications = {}

    def classify(product: Any, references: list[dict]) -> None:
        for row in references:
            system_key = (row["system"], row.get("edition"))
            if system_key not in classifications:
                system = file.create_entity(
                    "IfcClassification", Name=row["system"], Edition=row.get("edition")
                )
                classifications[system_key] = system
            reference = run(
                "classification.add_reference",
                file,
                products=[product],
                identification=row["code"],
                name=row.get("name"),
                classification=classifications[system_key],
            )
            if row.get("location"):
                reference.Location = row["location"]

    for identifier, material in materials.items():
        properties(material, data["materials"][identifier].get("property_sets", {}))

    type_classes = {
        "wall": "IfcWallType",
        "space": "IfcSpaceType",
        "slab": "IfcSlabType",
        "roof": "IfcRoofType",
        "stair": "IfcStairType",
        "cabinet": "IfcFurnishingElementType",
        "furnishing": "IfcFurnishingElementType",
    }
    types, layer_sets = {}, {}
    for identifier, definition in data["types"].items():
        kind = definition["kind"]
        type_class = type_classes.get(kind)
        if kind == "member":
            from .members import IFC_ROLES

            type_class = IFC_ROLES[definition["parameters"]["role"]][0] + "Type"
        if kind == "opening":
            type_class = (
                "IfcWindowType" if definition["parameters"]["fill"] == "window" else "IfcDoorType"
            )
        elif kind == "furnishing" and definition["parameters"].get("category") in {
            "basin",
            "wc",
            "shower",
        }:
            type_class = "IfcSanitaryTerminalType"
        product = run("root.create_entity", file, ifc_class=type_class, name=definition["name"])
        product.GlobalId = _guid("bim-type:" + identifier, state["document_id"])
        product.Description = definition.get("description")
        types[identifier] = product
        properties(product, definition.get("property_sets", {}))
        classify(product, definition.get("classifications", []))
        layers = definition.get("material_layers", [])
        if layers:
            layer_set = run(
                "material.add_material_set",
                file,
                name=definition["name"],
                set_type="IfcMaterialLayerSet",
            )
            for row in layers:
                layer = run(
                    "material.add_layer",
                    file,
                    layer_set=layer_set,
                    material=materials[row["material_id"]],
                    name=row["role"],
                )
                layer.LayerThickness = float(row["thickness_mm"])
            run(
                "material.assign_material",
                file,
                products=[product],
                type="IfcMaterialLayerSet",
                material=layer_set,
            )
            layer_sets[identifier] = layer_set
        elif definition.get("material_id"):
            run(
                "material.assign_material",
                file,
                products=[product],
                material=materials[definition["material_id"]],
            )

    assigned = 0
    for identifier, product in products.items():
        entity = state["entities"][identifier]
        binding = entity.get("properties", {}).get("bim", {})
        type_id = binding.get("type_id")
        if type_id:
            run(
                "type.assign_type",
                file,
                related_objects=[product],
                relating_type=types[type_id],
                should_map_representations=False,
            )
            assigned += 1
            if type_id in layer_sets:
                relation = run(
                    "material.assign_material",
                    file,
                    products=[product],
                    type="IfcMaterialLayerSetUsage",
                    material=layer_sets[type_id],
                )
                usage = relation.RelatingMaterial
                usage.LayerSetDirection = "AXIS2" if entity["kind"] == "wall" else "AXIS3"
                usage.DirectionSense = "POSITIVE"
                usage.OffsetFromReferenceLine = (
                    -entity["thickness"] / 2 if entity["kind"] == "wall" else 0.0
                )
        if binding.get("material_id"):
            run(
                "material.assign_material",
                file,
                products=[product],
                material=materials[binding["material_id"]],
            )
        properties(product, binding.get("property_sets", {}))
        classify(product, binding.get("classifications", []))
        if entity["kind"] == "opening":
            assembly = opening_assembly(entity)
            if assembly:
                construction = {
                    name: (
                        {"value": value, "type": "length", "unit": "mm"}
                        if name.endswith("_mm")
                        else value
                    )
                    for name, value in assembly.items()
                }
                properties(product, {"TEE_OpeningAssembly": construction})
                selected = {
                    role: assembly.get(role + "_material_id")
                    for role in ("frame", "glazing", "leaf")
                }
                selected = {role: identifier for role, identifier in selected.items() if identifier}
                if selected:
                    constituent_set = run(
                        "material.add_material_set",
                        file,
                        name=entity["name"],
                        set_type="IfcMaterialConstituentSet",
                    )
                    for role, material_id in selected.items():
                        run(
                            "material.add_constituent",
                            file,
                            constituent_set=constituent_set,
                            material=materials[material_id],
                            name=role,
                        )
                    run(
                        "material.assign_material",
                        file,
                        products=[product],
                        type="IfcMaterialConstituentSet",
                        material=constituent_set,
                    )
    return {
        "type_definitions": len(types),
        "typed_occurrences": assigned,
        "materials": len(materials),
        "material_layer_sets": len(layer_sets),
        "classification_systems": len(classifications),
        "property_encoding": "native IFC typed properties; explicit dimension units",
        "ids": "not_verified",
    }
