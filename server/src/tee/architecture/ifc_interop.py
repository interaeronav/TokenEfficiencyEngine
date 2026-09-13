"""Immutable IFC references, explicit federation frames and real IDS assessment.

IFC source bytes remain the authority for unsupported/native-unmapped semantics.
Inspection is paged; an inspection page is never a complete federation inventory.
No referenced URL, external document, texture or model is followed or executed.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REFERENCE_SCHEMA = "tee-ifc-reference/1"
MAX_IFC_BYTES = 64 * 1024 * 1024
MAX_IFC_ENTITIES = 200_000
MAX_PRODUCTS = 10_000
MAX_IDS_BYTES = 1024 * 1024


def _error(message: str) -> None:
    from .model import ArchitectureError

    raise ArchitectureError("ak_ifc_invalid", message, "Correct the named IFC/IDS source or frame.")


def _read(path: Path, maximum: int, suffix: str | tuple[str, ...]) -> tuple[Path, bytes, str]:
    from .imports import _file

    try:
        path = _file(Path(path), maximum)
        allowed = (suffix,) if isinstance(suffix, str) else suffix
        if path.suffix.lower() not in allowed:
            _error(f"Expected an uncompressed {' or '.join(allowed)} file.")
        data = path.read_bytes()
    except OSError as exc:
        _error(f"Source cannot be read ({type(exc).__name__}).")
    if len(data) > maximum:
        _error("Source changed or exceeded its size limit while reading.")
    return path, data, hashlib.sha256(data).hexdigest()


def _open(path: Path) -> tuple[Any, dict, list]:
    import ifcopenshell
    import ifcopenshell.util.unit

    path, raw, digest = _read(path, MAX_IFC_BYTES, ".ifc")
    try:
        model = ifcopenshell.open(str(path))
    except Exception as exc:
        _error(f"IFC could not be parsed ({type(exc).__name__}).")
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        _error("IFC changed during inspection; retry with an immutable source.")
    if model.schema not in {"IFC2X3", "IFC4", "IFC4X3"}:
        _error(f"Unsupported IFC schema {model.schema}.")
    if sum(1 for _ in model) > MAX_IFC_ENTITIES:
        _error(f"IFC exceeds {MAX_IFC_ENTITIES} STEP entities.")
    products = sorted(
        model.by_type("IfcProduct"), key=lambda product: (product.GlobalId or "", product.id())
    )
    if len(products) > MAX_PRODUCTS:
        _error(f"IFC exceeds {MAX_PRODUCTS} products; split the reference by discipline or zone.")
    guids = [product.GlobalId for product in model.by_type("IfcRoot")]
    if any(not isinstance(guid, str) or len(guid) != 22 for guid in guids):
        _error("Every IFC root must have a valid 22-character IFC GUID.")
    try:
        if any(
            ifcopenshell.guid.compress(ifcopenshell.guid.expand(guid)) != guid for guid in guids
        ):
            _error("IFC contains a noncanonical GUID.")
    except (ValueError, KeyError, IndexError):
        _error("IFC contains an invalid GUID.")
    if len(guids) != len(set(guids)):
        _error("IFC contains duplicate root GUIDs; source identity is ambiguous.")
    if not model.by_type("IfcProject") or len(model.by_type("IfcProject")) != 1:
        _error("IFC must contain one project with explicit length units.")
    project = model.by_type("IfcProject")[0]
    units = project.UnitsInContext.Units if project.UnitsInContext else ()
    length_units = [unit for unit in units if getattr(unit, "UnitType", None) == "LENGTHUNIT"]
    if len(length_units) != 1:
        _error("IFC project must have exactly one explicit length unit.")
    try:
        scale = ifcopenshell.util.unit.calculate_unit_scale(model)
    except Exception as exc:
        _error(f"IFC length conversion is unsupported ({type(exc).__name__}).")
    if not math.isfinite(scale) or not 1e-9 <= scale <= 1e6:
        _error("IFC length conversion is unsupported.")
    source = {
        "path": str(path),
        "sha256": digest,
        "bytes": len(raw),
        "schema": model.schema_identifier,
        "project_guid": project.GlobalId,
        "length_unit_metres": scale,
        "product_count": len(products),
        "classes": dict(sorted(Counter(product.is_a() for product in products).items())),
        "validation": "syntax_parsed; full_IFC_schema_rules_not_assessed",
    }
    return model, source, products


def _plain(value: Any, depth: int = 0) -> Any:
    """Bounded inspection values; reference pointers retain original IFC identity."""
    if depth > 4:
        return {"omitted": "depth limit; exact value retained in IFC"}
    if value is None or isinstance(value, (bool, int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            return {"invalid": "non-finite value"}
        return value
    if isinstance(value, str):
        return value if len(value) <= 1024 else {"text": value[:1024], "truncated": True}
    if isinstance(value, (tuple, list)):
        return {
            "items": [_plain(item, depth + 1) for item in value[:64]],
            "total": len(value),
            "complete": len(value) <= 64,
        }
    if isinstance(value, dict):
        return {str(key): _plain(item, depth + 1) for key, item in list(value.items())[:64]}
    if hasattr(value, "is_a"):
        if hasattr(value, "wrappedValue"):
            return {"type": value.is_a(), "value": _plain(value.wrappedValue, depth + 1)}
        return {
            "step_id": value.id(),
            "class": value.is_a(),
            "guid": getattr(value, "GlobalId", None),
            "name": _plain(getattr(value, "Name", None), depth + 1),
        }
    return {"omitted": "unsupported inspection value; retained in IFC"}


def _record(entity: Any, depth: int = 0) -> dict:
    result = {"step_id": entity.id(), "class": entity.is_a()}
    for name, value in entity.get_info().items():
        if name not in {"id", "type"}:
            result[name] = _plain(value, depth)
    return result


def _placement(product: Any, scale: float) -> list | None:
    import ifcopenshell.util.placement
    import numpy as np

    placement = product.ObjectPlacement
    if placement is None:
        return None
    seen = set()
    current = placement
    while current is not None:
        if not current.is_a("IfcLocalPlacement") or current.id() in seen or len(seen) > 128:
            return None
        seen.add(current.id())
        current = current.PlacementRelTo
    try:
        matrix = ifcopenshell.util.placement.get_local_placement(placement)
        matrix[:3, 3] *= scale * 1000
        if not np.isfinite(matrix).all():
            return None
        return matrix.tolist()
    except Exception:
        return None


def _psets(product: Any) -> dict:
    import ifcopenshell.util.element

    mappings = ifcopenshell.util.element.get_psets(product, should_inherit=False, verbose=True)
    result = {}
    for name, properties in list(mappings.items())[:32]:
        values = {}
        property_items = [(key, value) for key, value in properties.items() if key != "id"]
        for key, metadata in property_items[:64]:
            if isinstance(metadata, dict) and metadata.get("id"):
                values[key] = _record(product.file.by_id(metadata["id"]))
            else:
                values[key] = _plain(metadata)
        result[name] = {
            "properties": values,
            "total": len(property_items),
            "complete": len(property_items) <= 64,
        }
    return {"sets": result, "total": len(mappings), "complete": len(mappings) <= 32}


def _materials(product: Any) -> dict | None:
    import ifcopenshell.util.element

    material = ifcopenshell.util.element.get_material(product)
    if material is None:
        return None
    seen = set()

    def visit(row: Any, depth: int = 0) -> dict:
        if row.id() in seen or depth > 3:
            return _plain(row)
        seen.add(row.id())
        values = _record(row)
        for field in (
            "ForLayerSet",
            "MaterialLayers",
            "MaterialConstituents",
            "Material",
            "Materials",
        ):
            child = getattr(row, field, None)
            if child is not None:
                values[field] = (
                    [visit(item, depth + 1) for item in child[:32]]
                    if isinstance(child, tuple)
                    else visit(child, depth + 1)
                )
        return values

    return visit(material)


def _classifications(product: Any) -> list[dict]:
    result = []
    for relation in getattr(product, "HasAssociations", ()):
        if relation.is_a("IfcRelAssociatesClassification"):
            reference = relation.RelatingClassification
            row = _record(reference)
            if getattr(reference, "ReferencedSource", None):
                row["system"] = _record(reference.ReferencedSource)
            result.append(row)
    return result[:32]


def georeference(model: Any) -> dict:
    import ifcopenshell.util.element
    import ifcopenshell.util.geolocation
    import ifcopenshell.util.placement
    import ifcopenshell.util.unit
    import numpy as np

    geo = ifcopenshell.util.geolocation
    if model.schema == "IFC2X3":
        conversion = (
            ifcopenshell.util.element.get_pset(
                model.by_type("IfcProject")[0], "ePSet_MapConversion"
            )
            or {}
        )
    else:
        conversions = model.by_type("IfcCoordinateOperation")
        if len(conversions) > 1:
            return {
                "status": "not_verified",
                "reason": "Multiple coordinate operations need explicit selection.",
            }
        conversion = conversions[0].get_info() if conversions else {}
    for field in ("Scale", "FactorX", "FactorY", "FactorZ"):
        value = conversion.get(field)
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0
        ):
            return {"status": "not_verified", "reason": f"Invalid explicit {field}."}
    if conversion.get("XAxisAbscissa") == 0 and conversion.get("XAxisOrdinate") == 0:
        return {"status": "not_verified", "reason": "Explicit map X axis has zero length."}
    if conversion:
        contexts = model.by_type("IfcGeometricRepresentationContext", include_subtypes=False)
        try:
            frames = [
                ifcopenshell.util.placement.get_axis2placement(context.WorldCoordinateSystem)
                for context in contexts
            ]
            if not frames or any(
                not np.allclose(frame, frames[0], rtol=0, atol=1e-9) for frame in frames[1:]
            ):
                return {
                    "status": "not_verified",
                    "reason": "Conflicting context frames need explicit selection.",
                }
            if model.schema != "IFC2X3" and not conversions[0].SourceCRS.is_a(
                "IfcGeometricRepresentationContext"
            ):
                return {
                    "status": "not_verified",
                    "reason": "Map source CRS is not the IFC project context.",
                }
        except Exception as exc:
            return {
                "status": "not_verified",
                "reason": f"Invalid context frame: {type(exc).__name__}",
            }
    try:
        parameters = geo.get_helmert_transformation_parameters(model)
    except Exception as exc:
        return {
            "status": "not_verified",
            "reason": f"Unsupported coordinate operation: {type(exc).__name__}",
        }
    if parameters is None:
        return {
            "status": "not_verified",
            "reason": "No explicit map conversion; local coordinates are not an assumed CRS.",
        }
    if model.schema == "IFC2X3":
        crs = (
            ifcopenshell.util.element.get_pset(model.by_type("IfcProject")[0], "ePSet_ProjectedCRS")
            or {}
        )
    else:
        target_crs = model.by_type("IfcCoordinateOperation")[0].TargetCRS
        crs = _record(target_crs)
        if getattr(target_crs, "MapUnit", None):
            crs["MapUnit"] = _record(target_crs.MapUnit)
    controls = []
    scale_mm = ifcopenshell.util.unit.calculate_unit_scale(model) * 1000
    for point in ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)):
        try:
            mapped = geo.auto_xyz2enh(model, *point)
            back = geo.auto_enh2xyz(model, *mapped)
            if not all(math.isfinite(value) for value in (*mapped, *back)) or any(
                abs(a - b) * scale_mm > 0.01 for a, b in zip(point, back, strict=True)
            ):
                raise ValueError("Coordinate readback disagrees by more than 0.01 mm.")
        except Exception as exc:
            return {
                "status": "not_verified",
                "reason": f"Invalid map conversion: {type(exc).__name__}",
            }
        controls.append(
            {
                "source_project_units": list(point),
                "map_units": list(mapped),
                "readback_project_units": list(back),
            }
        )
    return {
        "status": "declared_transform_readback",
        "crs": crs,
        "parameters": dict(parameters._asdict()),
        "controls": controls,
        "source_frame": "IFC project world coordinates in project length units",
        "target_frame": "declared projected CRS in its map units; vertical datum as supplied",
        "survey_control_verification": "not_verified",
        "crs_authority_verification": "not_verified",
    }


def inspect_ifc(
    path: Path,
    *,
    offset: int = 0,
    limit: int = 50,
    include_details: bool = False,
    geometry_guids: list[str] | None = None,
) -> dict:
    import ifcopenshell.util.element

    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 100:
        _error("IFC page needs nonnegative offset and limit from 1 to 100.")
    if type(include_details) is not bool:
        _error("include_details must be boolean.")
    selected = geometry_guids or []
    if (
        not isinstance(selected, list)
        or len(selected) > 16
        or any(not isinstance(guid, str) for guid in selected)
    ):
        _error("geometry_guids must name at most 16 GUIDs.")
    model, source, products = _open(path)
    by_guid = {product.GlobalId: product for product in products}
    if set(selected) - set(by_guid):
        _error("Geometry selection names an unknown product GUID.")
    rows = []
    for product in products[offset : offset + limit]:
        element_type = ifcopenshell.util.element.get_type(product)
        container = ifcopenshell.util.element.get_container(product)
        row = {
            "guid": product.GlobalId,
            "class": product.is_a(),
            "name": _plain(product.Name),
            "step_id": product.id(),
            "type_guid": element_type.GlobalId if element_type else None,
            "container_guid": container.GlobalId if container else None,
            "has_representation": bool(product.Representation),
            "editing": "reference_retained",
        }
        if include_details:
            row.update(
                {
                    "placement_world_mm": _placement(product, source["length_unit_metres"]),
                    "property_sets": _psets(product),
                    "materials": _materials(product),
                    "classifications": _classifications(product),
                    "type": {
                        "guid": element_type.GlobalId,
                        "class": element_type.is_a(),
                        "name": element_type.Name,
                        "property_sets": _psets(element_type),
                        "classifications": _classifications(element_type),
                    }
                    if element_type
                    else None,
                }
            )
        rows.append(row)
    geometries = {}
    if selected:
        import ifcopenshell.geom
        import ifcopenshell.util.shape

        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)
        for guid in selected:
            try:
                shape = ifcopenshell.geom.create_shape(settings, by_guid[guid])
                vertices = ifcopenshell.util.shape.get_vertices(shape.geometry)
                geometries[guid] = {
                    "status": "measured",
                    "bounds_world_mm": {
                        "min": (vertices.min(axis=0) * 1000).tolist(),
                        "max": (vertices.max(axis=0) * 1000).tolist(),
                    },
                    "volume_m3": ifcopenshell.util.shape.get_volume(shape.geometry),
                }
            except Exception as exc:
                geometries[guid] = {"status": "not_verified", "reason": type(exc).__name__}
    return {
        "source": source,
        "products": rows,
        "page": {
            "offset": offset,
            "limit": limit,
            "total": len(products),
            "next_offset": offset + limit if offset + limit < len(products) else None,
            "complete": offset == 0 and len(rows) == len(products),
        },
        "georeference": georeference(model),
        "geometry": geometries,
        "preservation": (
            "Exact IFC retains attributes and relationships; inspection details are bounded."
        ),
        "regulatory": "not_verified",
    }


def prepare_ifc_reference(path: Path, output_dir: Path, expected_sha256: str | None = None) -> dict:
    _, source, _ = _open(path)
    if expected_sha256 is not None and expected_sha256 != source["sha256"]:
        _error("IFC source checksum differs from the reviewed source.")
    target = Path(output_dir).absolute()
    if any(part.is_symlink() for part in (target, *target.parents)):
        _error("IFC reference output cannot traverse symbolic links.")
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    raw = Path(source["path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != source["sha256"]:
        _error("IFC changed before the reference could be retained.")
    copy_path = target / "source.ifc"
    manifest_path = target / "reference.json"
    if copy_path.exists() or manifest_path.exists():
        _error("Reference destination already exists; choose a fresh revision directory.")
    with copy_path.open("xb") as handle:
        handle.write(raw)
    os.chmod(copy_path, 0o600)
    manifest = {
        "schema": REFERENCE_SCHEMA,
        "reference_id": "ifc_" + source["sha256"][:16],
        "source": {**source, "path": str(copy_path)},
        "source_bytes_preserved": True,
        "editing": "reference_retained; native promotion requires reviewed supported candidates",
    }
    with manifest_path.open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.chmod(manifest_path, 0o600)
    return {**manifest, "manifest_path": str(manifest_path)}


def federation_manifest(references: list[dict], *, transforms_mm: dict[str, list]) -> dict:
    import numpy as np

    if not isinstance(references, list) or not 1 <= len(references) <= 16:
        _error("Federation requires 1 to 16 immutable IFC references.")
    if not isinstance(transforms_mm, dict):
        _error(
            "Every federation member needs an explicit project-world-mm to authoring-mm transform."
        )
    members, identifiers = [], set()
    for reference in references:
        if not isinstance(reference, dict) or reference.get("schema") != REFERENCE_SCHEMA:
            _error("Federation input must be an immutable reference, not a paged inspection.")
        identifier = reference.get("reference_id")
        source_reference = reference.get("source")
        if (
            not isinstance(identifier, str)
            or not isinstance(source_reference, dict)
            or not isinstance(source_reference.get("path"), str)
            or not isinstance(source_reference.get("sha256"), str)
            or identifier != "ifc_" + source_reference["sha256"][:16]
        ):
            _error("Federation member needs its complete prepared source identity.")
        if identifier in identifiers:
            _error("Federation reference IDs must be unique.")
        identifiers.add(identifier)
        if identifier not in transforms_mm:
            _error(f"No explicit federation transform for {identifier}.")
        _, source, _ = _open(Path(reference["source"]["path"]))
        if source["sha256"] != reference["source"]["sha256"]:
            _error(f"Federation reference {identifier} changed.")
        try:
            matrix = np.asarray(transforms_mm[identifier], dtype=float)
        except (TypeError, ValueError):
            _error("Federation transform must be a finite affine 4x4 matrix.")
        if (
            matrix.shape != (4, 4)
            or not np.isfinite(matrix).all()
            or abs(matrix).max() > 1e12
            or not np.allclose(matrix[3], [0, 0, 0, 1], rtol=0, atol=1e-12)
            or not np.allclose(matrix[:3, :3].T @ matrix[:3, :3], np.eye(3), rtol=0, atol=1e-8)
            or not math.isclose(float(np.linalg.det(matrix[:3, :3])), 1.0, abs_tol=1e-8)
        ):
            _error("Federation needs rigid right-handed transforms after source-unit conversion.")
        members.append(
            {
                "reference_id": identifier,
                "source": source,
                "transform_world_mm_to_authoring_mm": matrix.tolist(),
                "entity_identity": "reference_id:source_IFC_GUID",
                "all_products_retained": True,
            }
        )
    if set(transforms_mm) != identifiers:
        _error("Federation transforms must match member IDs exactly.")
    return {
        "schema": "tee-ifc-federation/1",
        "members": members,
        "total_products": sum(member["source"]["product_count"] for member in members),
        "geometry_merge": False,
        "coordinate_alignment": "explicit_caller_transform; surveyed_alignment_not_verified",
    }


def _wall_candidate(product: Any, scale: float) -> tuple[dict | None, str | None]:
    """Recognise an exact editable wall prism; never fit a wall to a bounding box."""
    import ifcopenshell.geom
    import ifcopenshell.util.element
    import ifcopenshell.util.placement
    import ifcopenshell.util.shape
    import numpy as np

    if not product.is_a("IfcWall"):
        return None, "Only straight rectangular wall geometry has native promotion support."
    if product.HasOpenings:
        return (
            None,
            "Hosted openings remain references until complete host/fill promotion is supported.",
        )
    storey = ifcopenshell.util.element.get_container(product, ifc_class="IfcBuildingStorey")
    if storey is None:
        return None, "Native wall needs explicit building-storey containment."
    matrix = _placement(product, scale)
    storey_matrix = _placement(storey, scale)
    if matrix is None or storey_matrix is None:
        return None, "Unsupported or absent local placement; retained as a reference."
    representation = product.Representation
    bodies = (
        [row for row in representation.Representations if row.RepresentationIdentifier == "Body"]
        if representation
        else []
    )
    if (
        len(bodies) != 1
        or len(bodies[0].Items) != 1
        or bodies[0].Items[0].is_a() != "IfcExtrudedAreaSolid"
    ):
        return (
            None,
            "Body needs one extrusion; mapped items and complex solids remain references.",
        )
    solid = bodies[0].Items[0]
    profile = solid.SweptArea
    unit_mm = scale * 1000
    if profile.is_a() == "IfcRectangleProfileDef":
        x, y = float(profile.XDim), float(profile.YDim)
        points = np.array(
            [
                [-x / 2, -y / 2, 0, 1],
                [x / 2, -y / 2, 0, 1],
                [x / 2, y / 2, 0, 1],
                [-x / 2, y / 2, 0, 1],
            ],
            dtype=float,
        )
        if profile.Position:
            points = (ifcopenshell.util.placement.get_axis2placement(profile.Position) @ points.T).T
    elif profile.is_a() == "IfcArbitraryClosedProfileDef" and profile.OuterCurve.is_a(
        "IfcPolyline"
    ):
        coordinates = [tuple(point.Coordinates) for point in profile.OuterCurve.Points]
        if (
            len(coordinates) != 5
            or coordinates[0] != coordinates[-1]
            or any(len(point) != 2 for point in coordinates)
        ):
            return None, "Polyline profile is not an explicit closed four-corner rectangle."
        points = np.array([[*point, 0, 1] for point in coordinates[:-1]], dtype=float)
    else:
        return None, "Profile is not a supported explicit rectangle."
    local = (
        ifcopenshell.util.placement.get_axis2placement(solid.Position)
        if solid.Position
        else np.eye(4)
    )
    local[:3, 3] *= unit_mm
    points[:, :3] *= unit_mm
    world = np.asarray(matrix) @ local
    points = (world @ points.T).T[:, :3]
    extrusion = world[:3, :3] @ np.asarray(solid.ExtrudedDirection.DirectionRatios, dtype=float)
    norm = np.linalg.norm(extrusion)
    if not norm or not np.allclose(extrusion / norm, [0, 0, 1], rtol=0, atol=1e-8):
        return (
            None,
            "Only vertical positive-Z extrusion is editable; tilted walls remain references.",
        )
    if not np.isfinite(points).all() or not np.allclose(
        points[:, 2], storey_matrix[2][3], rtol=0, atol=0.01
    ):
        return (
            None,
            "Wall base must coincide with its storey world elevation; offsets remain references.",
        )
    edges = np.roll(points, -1, axis=0) - points
    lengths = np.linalg.norm(edges, axis=1)
    if (
        not np.isfinite(lengths).all()
        or min(lengths) <= 0
        or not np.allclose(edges[:2], -edges[2:], rtol=1e-8, atol=1e-6)
        or not math.isclose(
            float(np.dot(edges[0], edges[1])), 0, abs_tol=float(lengths[0] * lengths[1]) * 1e-8
        )
    ):
        return None, "Profile is not a measured rectangle."
    axis = int(lengths[1] > lengths[0])
    length, thickness = float(lengths[axis]), float(lengths[1 - axis])
    if length < 3 * thickness:
        return None, "Wall axis is ambiguous for this short/wide rectangle."
    direction = edges[axis] / length
    center = points.mean(axis=0)
    height = float(solid.Depth) * unit_mm
    if not math.isfinite(height) or height <= 0:
        return None, "Extrusion depth must be positive and finite."
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    try:
        shape = ifcopenshell.geom.create_shape(settings, product)
        actual_volume = ifcopenshell.util.shape.get_volume(shape.geometry)
        vertices_mm = ifcopenshell.util.shape.get_vertices(shape.geometry) * 1000
    except Exception:
        return None, "Independent source geometry readback failed."
    expected_volume = length * thickness * height / 1e9
    if not math.isclose(actual_volume, expected_volume, rel_tol=1e-7, abs_tol=1e-9):
        return None, "Source geometry volume disagrees with the proposed wall prism."
    candidate_vertices = np.vstack([points, np.add(points, [0, 0, height])])
    measured_bounds = [vertices_mm.min(axis=0), vertices_mm.max(axis=0)]
    expected_bounds = [candidate_vertices.min(axis=0), candidate_vertices.max(axis=0)]
    if not np.allclose(measured_bounds, expected_bounds, rtol=0, atol=0.01):
        return None, "Source geometry placement disagrees with the proposed wall prism."
    return {
        "kind": "wall",
        "name": _plain(product.Name),
        "storey_guid": storey.GlobalId,
        "storey_elevation_world_mm": float(storey_matrix[2][3]),
        "start": (center - direction * length / 2)[:2].tolist(),
        "end": (center + direction * length / 2)[:2].tolist(),
        "thickness": thickness,
        "height": height,
        "geometry_frame": "IFC project world in millimetres; federation transform not applied",
        "geometry_check": {
            "status": "measured",
            "source_volume_m3": actual_volume,
            "candidate_volume_m3": expected_volume,
            "bounds_world_mm": [bound.tolist() for bound in measured_bounds],
        },
        "required_before_promotion": [
            "explicit native storey height",
            "review source material/type/property mapping",
        ],
        "semantics": (
            "Types, GUIDs and relationships remain in the immutable reference; "
            "no native conversion has occurred."
        ),
    }, None


def native_candidates(path: Path, *, guids: list[str]) -> dict:
    if (
        not isinstance(guids, list)
        or not 1 <= len(guids) <= 32
        or any(not isinstance(guid, str) for guid in guids)
    ):
        _error("Native candidates require 1 to 32 explicitly selected IFC product GUIDs.")
    _model, source, products = _open(path)
    by_guid = {product.GlobalId: product for product in products}
    if len(set(guids)) != len(guids) or set(guids) - set(by_guid):
        _error("Candidate selection has duplicate or unknown product GUIDs.")
    rows = []
    for guid in guids:
        product = by_guid[guid]
        try:
            candidate, reason = _wall_candidate(product, source["length_unit_metres"])
        except Exception as exc:
            candidate, reason = (
                None,
                f"Unsupported source geometry ({type(exc).__name__}); retained as reference.",
            )
        rows.append(
            {
                "guid": guid,
                "class": product.is_a(),
                "identity": "ifc_" + source["sha256"][:16] + ":" + guid,
                "status": "supported_geometry_candidate" if candidate else "reference_retained",
                "candidate": candidate,
                "reason": reason,
            }
        )
    return {
        "source": source,
        "products": rows,
        "native_objects_created": 0,
        "unsupported_objects": "retained in exact IFC source",
        "regulatory": "not_verified",
    }


def _assess_ids(ifc_path: Path, ids_path: Path) -> dict:
    """Worker entry: schema-validated IDS, no remote schema or document loading."""
    from importlib.metadata import version

    from defusedxml import ElementTree
    from ifctester import ids
    from xmlschema import XMLSchema

    model, source, _ = _open(ifc_path)
    _, data, digest = _read(ids_path, MAX_IDS_BYTES, (".ids", ".xml"))
    try:
        tree = ElementTree.fromstring(
            data, forbid_dtd=True, forbid_entities=True, forbid_external=True
        )
        # The installed IDS 1.0 schema imports only local/bundled XSD resources.
        # Never select a schema from a user-supplied xsi:schemaLocation.
        schema_path = Path(ids.cwd) / "ids.xsd"
        schema = XMLSchema(str(schema_path), allow="local")
        decoded = schema.decode(
            tree,
            strip_namespaces=True,
            namespaces={"": "http://standards.buildingsmart.org/IDS"},
            use_location_hints=False,
        )
        specification = ids.Ids().parse(decoded)
    except Exception as exc:
        _error(f"IDS is not valid against the installed IDS 1.0 schema ({type(exc).__name__}).")
    if not 1 <= len(specification.specifications) <= 64:
        _error("IDS must contain 1 to 64 specifications; an empty assessment cannot pass.")
    if any(
        len(row.applicability) + len(row.requirements) > 32 for row in specification.specifications
    ):
        _error("IDS specifications are limited to 32 applicability/requirement facets.")
    try:
        specification.validate(model, should_filter_version=True, filepath=str(ifc_path))
    except Exception as exc:
        _error(f"IDS evaluator could not complete ({type(exc).__name__}); no verification issued.")
    rows = []
    for index, spec in enumerate(specification.specifications):
        applicable = len(spec.applicable_entities)
        failures = []
        for facet_index, facet in enumerate(spec.requirements):
            for failure in facet.failures:
                if len(failures) < 32:
                    failures.append(
                        {
                            "facet_index": facet_index,
                            "facet": type(facet).__name__,
                            "guid": getattr(failure["element"], "GlobalId", None),
                            "reason": str(failure["reason"])[:1024],
                        }
                    )
        count = sum(len(facet.failures) for facet in spec.requirements)
        if not spec.is_ifc_version:
            status, reason = (
                "not_applicable_schema",
                "Specification does not target this IFC schema.",
            )
        elif not spec.status:
            status, reason = (
                "fail",
                "Required applicability is empty."
                if not applicable and spec.minOccurs != 0
                else "Prohibited applicability is present."
                if applicable and spec.maxOccurs == 0
                else "One or more information requirements failed.",
            )
        elif not applicable:
            status, reason = (
                "pass_no_applicable_entities",
                "Optional/prohibited applicability is empty; no element information was assessed.",
            )
        else:
            status, reason = "pass", None
        rows.append(
            {
                "index": index,
                "name": str(spec.name)[:256],
                "status": status,
                "reason": reason,
                "target_schemas": spec.ifcVersion,
                "applicable_entities": applicable,
                "failed_entities": len(spec.failed_entities),
                "failure_count": count,
                "failures": failures,
                "failures_complete": count <= 32,
                "cardinality": {"minOccurs": spec.minOccurs, "maxOccurs": spec.maxOccurs},
            }
        )
    if any(row["status"] == "fail" for row in rows):
        status = "fail"
    elif all(row["status"] == "not_applicable_schema" for row in rows):
        status = "not_applicable_schema"
    elif not any(row["applicable_entities"] for row in rows):
        status = "no_applicable_entities"
    else:
        status = "pass"
    return {
        "status": status,
        "source": source,
        "ids": {
            "path": str(ids_path),
            "sha256": digest,
            "bytes": len(data),
            "schema": "IDS 1.0",
            "xml_validation": "pass",
            "schema_sha256": hashlib.sha256(schema_path.read_bytes()).hexdigest(),
        },
        "evaluator": {
            "name": "IfcTester",
            "version": version("ifctester"),
            "ifcopenshell": version("ifcopenshell"),
            "xmlschema": version("xmlschema"),
        },
        "specifications": rows,
        "assessment": (
            "Information requirements evaluated by installed IfcTester; no sampled products."
        ),
        "geometry": "not_assessed_by_ids",
        "regulatory": "not_verified",
    }


def assess_ids(ifc_path: Path, ids_path: Path, *, timeout_seconds: float = 60) -> dict:
    """Run parsing/regex evaluation in a bounded independent process."""
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(timeout_seconds)
        or not 1 <= timeout_seconds <= 120
    ):
        _error("IDS timeout must be 1 to 120 seconds.")
    ifc_path, _, ifc_hash = _read(ifc_path, MAX_IFC_BYTES, ".ifc")
    ids_path, _, ids_hash = _read(ids_path, MAX_IDS_BYTES, (".ids", ".xml"))
    request = json.dumps(
        {"ifc": str(ifc_path), "ids": str(ids_path), "ifc_hash": ifc_hash, "ids_hash": ids_hash}
    )
    # Desktop launchers may add the payload to sys.path without setting PYTHONPATH.
    # The worker must load this same payload, not a different editable installation.
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[2]) + (
        os.pathsep + environment["PYTHONPATH"] if environment.get("PYTHONPATH") else ""
    )
    try:
        process = subprocess.run(
            [sys.executable, "-m", "tee.architecture.ifc_interop", "--ids-worker"],
            input=request,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            env=environment,
        )
    except subprocess.TimeoutExpired:
        _error("IDS timed out; no pass issued. Split the specifications or source.")
    if process.returncode != 0 or len(process.stdout) > 4 * 1024 * 1024:
        _error("IDS assessment process failed; no pass result was issued.")
    try:
        result = json.loads(process.stdout)
    except (TypeError, ValueError):
        _error("IDS assessment returned an invalid report; no pass result was issued.")
    if not isinstance(result, dict):
        _error("IDS assessment returned an invalid report; no pass result was issued.")
    if result.get("error"):
        _error(result["error"])
    if not isinstance(result.get("source"), dict) or not isinstance(result.get("ids"), dict):
        _error("IDS assessment returned an invalid report; no pass result was issued.")
    if (
        result.get("source", {}).get("sha256") != ifc_hash
        or result.get("ids", {}).get("sha256") != ids_hash
    ):
        _error("IFC or IDS changed while assessing; no pass result was issued.")
    return result


if __name__ == "__main__":
    if sys.argv[1:] != ["--ids-worker"]:
        raise SystemExit(2)
    try:
        request = json.loads(sys.stdin.read(8192))
        result = _assess_ids(Path(request["ifc"]), Path(request["ids"]))
        if (
            result["source"]["sha256"] != request["ifc_hash"]
            or result["ids"]["sha256"] != request["ids_hash"]
        ):
            result = {"error": "IFC or IDS changed before assessment."}
    except Exception as exc:
        result = {"error": str(exc)[:1024]}
    print(json.dumps(result, allow_nan=False))
