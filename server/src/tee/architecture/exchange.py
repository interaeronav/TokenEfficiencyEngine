"""A82 semantic IFC4 and bounded derived meshes; authoritative dimensions are mm.

IfcOpenShell 0.8.5 APIs are imported at operation time. Geometry is authored in
explicit project millimetres; no nominal bounding box stands in for a polygon,
wall opening, or cabinet assembly. Supplied opening construction has explicit
closed-position frame/panel solids; absent construction remains unspecified.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import re
import threading
import uuid
import warnings
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

from .spatial import base_elevation, boundary_mesh, space_polygons

_GUID_NAMESPACE = uuid.UUID("85b4977a-f536-4a43-afec-21437d8d1b63")
_SECRET = re.compile(r"password|secret|apikey|token|authorization|credential|privatekey", re.I)
_VALIDATE_LOCK = threading.Lock()


def _document(data: dict[str, Any]) -> dict[str, Any]:
    from .model import Document

    document = Document.from_dict(data)
    document.validate()
    return document.to_dict()


def _ifc() -> Any:
    try:
        import ifcopenshell
        import ifcopenshell.api
    except ImportError as exc:
        raise TeeError(
            "architecture_ifc_unavailable",
            "IfcOpenShell is unavailable.",
            fix="Use the existing IFC-enabled TEE interpreter.",
        ) from exc
    return ifcopenshell


def _guid(identifier: str, document_id: str) -> str:
    namespace = uuid.uuid5(_GUID_NAMESPACE, document_id)
    return _ifc().guid.compress(uuid.uuid5(namespace, identifier).hex)


def _safe_metadata(value: Any, depth: int = 0) -> Any:
    if depth > 4:
        return "[depth limit]"
    if isinstance(value, dict):
        return {
            str(key)[:80]: (
                "[redacted]"
                if _SECRET.search(re.sub(r"[^a-z]", "", str(key).lower()))
                else _safe_metadata(item, depth + 1)
            )
            for key, item in list(value.items())[:32]
        }
    if isinstance(value, list):
        return [_safe_metadata(item, depth + 1) for item in value[:32]]
    if isinstance(value, str):
        return "".join(char for char in value if char >= " " or char == "\n")[:512]
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and math.isfinite(value):
        return value
    return "[unsupported]"


def _area(polygon: list[list[float]]) -> float:
    x, y = polygon[0]
    return (
        sum(
            (a[0] - x) * (b[1] - y) - (b[0] - x) * (a[1] - y)
            for a, b in zip(polygon, polygon[1:] + polygon[:1], strict=False)
        )
        / 2
    )


def _wall_polygon(
    wall: dict[str, Any], start: float = 0, end: float | None = None
) -> list[list[float]]:
    a, b = wall["start"], wall["end"]
    length = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    end = length if end is None else end
    half = wall["thickness"] / 2
    return [
        [a[0] + ux * x - uy * y, a[1] + uy * x + ux * y]
        for x, y in [(start, -half), (end, -half), (end, half), (start, half)]
    ]


def _wall_parts(
    wall: dict[str, Any],
    openings: list[dict[str, Any]],
    elevation: float,
    span: tuple[float, float] | None = None,
) -> list[dict]:
    """Exact rectangular strip decomposition of the wall minus its hosted voids."""
    xs = sorted(
        {
            *(span or (0.0, math.dist(wall["start"], wall["end"]))),
            *(float(o["offset"]) for o in openings),
            *(float(o["offset"] + o["width"]) for o in openings),
        }
    )
    parts = []
    for low, high in itertools.pairwise(xs):
        mid = (low + high) / 2
        blocked = sorted(
            (o["sill"], o["sill"] + o["height"])
            for o in openings
            if o["offset"] < mid < o["offset"] + o["width"]
        )
        current = 0.0
        for bottom, top in [*blocked, (wall["height"], wall["height"])]:
            if bottom > current:
                parts.append(
                    {
                        "polygon": _wall_polygon(wall, low, high),
                        "z": elevation + current,
                        "depth": bottom - current,
                    }
                )
            current = max(current, top)
    return parts


def _intersection_area(subject: list[list[float]], clip: list[list[float]]) -> float:
    """Sutherland-Hodgman clipping of the convex rectangular wall footprints."""
    output = subject
    for start, end in zip(clip, clip[1:] + clip[:1], strict=True):
        prior, output = output, []
        if not prior:
            break

        for a, b in zip(prior, prior[1:] + prior[:1], strict=True):
            da, db = [
                (end[0] - start[0]) * (point[1] - start[1])
                - (end[1] - start[1]) * (point[0] - start[0])
                for point in (a, b)
            ]
            if (da >= 0) != (db >= 0):
                t = da / (da - db)
                output.append([a[i] + t * (b[i] - a[i]) for i in range(2)])
            if db >= 0:
                output.append(b)
    return abs(_area(output)) if len(output) >= 3 else 0


def _junctions(
    document: dict[str, Any], spans: dict[str, tuple[float, float]] | None = None
) -> dict[str, Any]:
    entities = document["entities"]
    walls = []
    for identifier, wall in entities.items():
        if wall["kind"] == "wall":
            openings = [
                row
                for row in entities.values()
                if row["kind"] == "opening" and row["wall"] == identifier
            ]
            walls.append(
                (
                    identifier,
                    _wall_parts(
                        wall,
                        openings,
                        base_elevation(wall, entities),
                        spans.get(identifier) if spans else None,
                    ),
                )
            )
    findings = []
    comparisons = 0
    total = 0
    for index, (first, parts) in enumerate(walls):
        for second, others in walls[index + 1 :]:
            overlap = 0.0
            for part in parts:
                for other in others:
                    comparisons += 1
                    if comparisons > 100000:
                        return {
                            "status": "not_verified",
                            "reason": "100000 part-pair limit",
                            "overlaps": findings[:50],
                            "pairs_found": total,
                        }
                    z = min(part["z"] + part["depth"], other["z"] + other["depth"]) - max(
                        part["z"], other["z"]
                    )
                    if z > 0:
                        overlap += _intersection_area(part["polygon"], other["polygon"]) * z
            if overlap > 1e-3:
                total += 1
                if len(findings) < 50:
                    findings.append(
                        {"walls": [first, second], "overlap_m3": round(overlap / 1e9, 12)}
                    )
    return {
        "status": "overlaps_present" if total else "no_wall_overlap_found",
        "pairs_found": total,
        "overlaps": findings,
        "policy": "Volumes are not additive across classes; this checks wall-wall overlap only.",
        "scope": "Wall-wall material only, after hosted voids; other element clashes not checked.",
    }


def _triangles(polygon: list[list[float]]) -> list[list[int]]:
    """Ear clipping for an already validated simple polygon, including concavity."""
    order = list(range(len(polygon)))
    if _area(polygon) < 0:
        order.reverse()
    triangles = []

    def cross(a: list[float], b: list[float], c: list[float]) -> float:
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    while len(order) > 3:
        found = False
        for index, b in enumerate(order):
            a, c = order[index - 1], order[(index + 1) % len(order)]
            if cross(polygon[a], polygon[b], polygon[c]) <= 1e-9:
                continue
            if any(
                all(
                    v >= -1e-9
                    for v in (
                        cross(polygon[a], polygon[b], polygon[k]),
                        cross(polygon[b], polygon[c], polygon[k]),
                        cross(polygon[c], polygon[a], polygon[k]),
                    )
                )
                for k in order
                if k not in (a, b, c)
            ):
                continue
            triangles.append([a, b, c])
            del order[index]
            found = True
            break
        if not found:
            # Collinear boundary vertices carry no area; remove one explicitly.
            collinear = next(
                (
                    i
                    for i, b in enumerate(order)
                    if abs(
                        cross(
                            polygon[order[i - 1]], polygon[b], polygon[order[(i + 1) % len(order)]]
                        )
                    )
                    <= 1e-9
                ),
                None,
            )
            if collinear is None:
                raise TeeError(
                    "architecture_triangulation",
                    "Polygon could not be triangulated.",
                    fix="Supply a valid simple polygon without near-coincident edges.",
                )
            del order[collinear]
    triangles.append(order)
    return triangles


def _prism_mesh(polygon: list[list[float]], z: float, depth: float) -> dict[str, Any]:
    polygon = [list(map(float, point)) for point in polygon]
    if _area(polygon) < 0:
        polygon.reverse()
    n = len(polygon)
    vertices = [[x, y, float(z)] for x, y in polygon] + [
        [x, y, float(z + depth)] for x, y in polygon
    ]
    faces = []
    for a, b, c in _triangles(polygon):
        faces.extend([[c, b, a], [a + n, b + n, c + n]])
    for a in range(n):
        b = (a + 1) % n
        faces.extend([[a, b, b + n], [a, b + n, a + n]])
    return {"vertices": vertices, "faces": faces}


def _box_part(origin: list[float], size: list[float], **metadata: Any) -> dict:
    x, y, z = origin
    sx, sy, sz = size
    return {
        "polygon": [[x, y], [x + sx, y], [x + sx, y + sy], [x, y + sy]],
        "z": z,
        "depth": sz,
        **metadata,
    }


def _rotate_parts(parts: list[dict], origin: list[float], degrees: float) -> list[dict]:
    angle = math.radians(degrees)
    c, s = math.cos(angle), math.sin(angle)
    for part in parts:
        part["polygon"] = [
            [
                origin[0] + c * (x - origin[0]) - s * (y - origin[1]),
                origin[1] + s * (x - origin[0]) + c * (y - origin[1]),
            ]
            for x, y in part["polygon"]
        ]
    return parts


def _opening_parts(document: dict, entity: dict) -> list[dict]:
    from .bim import opening_components

    wall = document["entities"][entity["wall"]]
    start, end = wall["start"], wall["end"]
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    c, s = math.cos(angle), math.sin(angle)
    z = base_elevation(wall, document["entities"]) + entity["sill"]
    parts = []
    for row in opening_components(entity, wall["thickness"]):
        local = _box_part(
            row["origin"],
            row["size"],
            material_role=row["material_role"],
            component=row["name"],
            material_id=row["material_id"],
        )
        local["polygon"] = [
            [
                start[0] + c * (entity["offset"] + x) - s * y,
                start[1] + s * (entity["offset"] + x) + c * y,
            ]
            for x, y in local["polygon"]
        ]
        local["z"] += z
        parts.append(local)
    return parts


def _furnishing_parts(entity: dict) -> list[dict]:
    """Schematic furniture silhouettes within explicit overall dimensions.

    Proportions only aid spatial review; these are not manufacturer assemblies.
    """
    x, y, z = entity["origin"]
    w, d, h = entity["size"]
    category = entity["category"]
    boxes = []

    def box(name: str, a: tuple, b: tuple) -> None:
        boxes.append(
            _box_part(
                [x + a[0] * w, y + a[1] * d, z + a[2] * h],
                [b[0] * w, b[1] * d, b[2] * h],
                component=name,
                material_role="schematic_furnishing",
            )
        )

    if category == "bed":
        box("base", (0, 0, 0), (1, 0.95, 0.4))
        box("mattress", (0, 0, 0.4), (1, 0.95, 0.3))
        box("headboard", (0, 0.95, 0), (1, 0.05, 1))
        box("pillow-a", (0.05, 0.72, 0.7), (0.4, 0.2, 0.12))
        box("pillow-b", (0.55, 0.72, 0.7), (0.4, 0.2, 0.12))
    elif category == "sofa":
        box("seat", (0.08, 0, 0), (0.84, 0.8, 0.55))
        box("back", (0, 0.8, 0), (1, 0.2, 1))
        box("arm-a", (0, 0, 0), (0.08, 0.8, 0.8))
        box("arm-b", (0.92, 0, 0), (0.08, 0.8, 0.8))
    elif category in {"table", "chair"}:
        top = 0.88 if category == "table" else 0.5
        box("top", (0, 0, top), (1, 1, 0.12))
        for ax in (0.04, 0.88):
            for ay in (0.04, 0.88):
                box(f"leg-{ax}-{ay}", (ax, ay, 0), (0.08, 0.08, top))
        if category == "chair":
            box("back", (0, 0.92, 0.62), (1, 0.08, 0.38))
    elif category == "wc":
        box("pan", (0.15, 0, 0), (0.7, 0.75, 0.52))
        box("seat", (0, 0, 0.52), (1, 0.78, 0.1))
        box("cistern", (0, 0.78, 0), (1, 0.22, 1))
    elif category == "basin":
        box("pedestal", (0.35, 0.25, 0), (0.3, 0.5, 0.8))
        box("rim", (0, 0, 0.8), (1, 1, 0.2))
    elif category == "shower":
        box("tray", (0, 0, 0), (1, 1, 0.04))
        box("screen-a", (0, 0, 0.04), (0.01, 1, 0.96))
        box("screen-b", (0.01, 0.99, 0.04), (0.99, 0.01, 0.96))
    else:
        box(category, (0, 0, 0), (1, 1, 1))
    return _rotate_parts(
        boxes, entity["origin"], entity.get("properties", {}).get("rotation_deg", 0)
    )


def _panel_csg(file: Any, panel: dict, relative_to: list[float]) -> Any:
    """Exact box minus explicit cylindrical drills/rectangular pockets in IFC4.

    Panel FRONT is its low thickness coordinate; BACK is the high coordinate.
    Both share the same positive u/v axes, independent of cabinet rotation.
    """
    origin = [panel["origin"][i] - relative_to[i] for i in range(3)]

    def position(point: list[float], axis: int = 2) -> Any:
        normal = tuple(1.0 if i == axis else 0.0 for i in range(3))
        ref = (0.0, 1.0, 0.0) if axis == 0 else (1.0, 0.0, 0.0)
        return file.create_entity(
            "IfcAxis2Placement3D",
            Location=file.create_entity("IfcCartesianPoint", Coordinates=tuple(map(float, point))),
            Axis=file.create_entity("IfcDirection", DirectionRatios=normal),
            RefDirection=file.create_entity("IfcDirection", DirectionRatios=ref),
        )

    def block(point: list[float], size: list[float]) -> Any:
        # Mixed IfcBlock/boolean representations triangulate with opposite
        # component winding in 0.8.5. Consistent swept solids avoid cancellation.
        points = [
            file.create_entity("IfcCartesianPoint", Coordinates=(float(x), float(y)))
            for x, y in ((0, 0), (size[0], 0), (size[0], size[1]), (0, size[1]))
        ]
        polyline = file.create_entity("IfcPolyline", Points=[*points, points[0]])
        profile = file.create_entity(
            "IfcArbitraryClosedProfileDef", ProfileType="AREA", OuterCurve=polyline
        )
        return file.create_entity(
            "IfcExtrudedAreaSolid",
            SweptArea=profile,
            Position=position(point),
            ExtrudedDirection=file.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)),
            Depth=float(size[2]),
        )

    result = block(origin, panel["size"])
    u_axis, v_axis, t_axis = {"XY": (0, 1, 2), "XZ": (0, 2, 1), "YZ": (1, 2, 0)}[
        panel["orientation"]
    ]
    epsilon = 1.0  # Outside-face overlap only; blind interior depth stays exact.
    for op in panel.get("machining", []):
        point = list(origin)
        point[u_axis] += op["u_mm"]
        point[v_axis] += op["v_mm"]
        thickness, depth = panel["thickness"], op["depth_mm"]
        if op["through"]:
            point[t_axis] -= epsilon
            depth = thickness + 2 * epsilon
        elif op["face"] == "front":
            point[t_axis] -= epsilon
            depth += epsilon
        else:
            point[t_axis] += thickness - depth
            depth += epsilon
        if op["type"] == "drill":
            # IfcOpenShell 0.8.5 silently drops IfcRightCircularCylinder in a
            # difference (measured); a circle extrusion is independently verified.
            profile = file.create_entity(
                "IfcCircleProfileDef", ProfileType="AREA", Radius=float(op["diameter_mm"] / 2)
            )
            cutter = file.create_entity(
                "IfcExtrudedAreaSolid",
                SweptArea=profile,
                Position=position(point, t_axis),
                ExtrudedDirection=file.create_entity(
                    "IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)
                ),
                Depth=float(depth),
            )
        else:
            size = [0.0, 0.0, 0.0]
            size[u_axis], size[v_axis], size[t_axis] = op["width_mm"], op["height_mm"], depth
            cutter = block(point, size)
        result = file.create_entity(
            "IfcBooleanResult", Operator="DIFFERENCE", FirstOperand=result, SecondOperand=cutter
        )
    return (
        file.create_entity("IfcCsgSolid", TreeRootExpression=result)
        if panel.get("machining")
        else result
    )


@lru_cache(maxsize=128)
def _panel_mesh_cached(encoded: str) -> dict:
    """Tessellate the same exact CSG used in IFC, with no mesh-boolean dependency."""
    ifc = _ifc()
    import ifcopenshell.geom
    import ifcopenshell.util.shape

    panel = json.loads(encoded)
    run = ifc.api.run
    file = run("project.create_file", version="IFC4")
    run("root.create_entity", file, ifc_class="IfcProject", name="Owned panel tessellation")
    run(
        "unit.assign_unit",
        file,
        units=[run("unit.add_si_unit", file, unit_type="LENGTHUNIT", prefix="MILLI")],
    )
    context = run("context.add_context", file, context_type="Model")
    item = _panel_csg(file, panel, [0, 0, 0])
    representation = file.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=context,
        RepresentationIdentifier="Body",
        RepresentationType="SolidModel",
        Items=[item],
    )
    product = run("root.create_entity", file, ifc_class="IfcBuildingElementProxy", name="Panel")
    run("geometry.assign_representation", file, product=product, representation=representation)
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    settings.set("mesher-linear-deflection", 0.00001)
    settings.set("mesher-angular-deflection", 0.05)
    shape = ifcopenshell.geom.create_shape(settings, product)
    vertices = ifcopenshell.util.shape.get_vertices(shape.geometry)
    faces = ifcopenshell.util.shape.get_faces(shape.geometry)
    if not len(vertices) or len(vertices) > 50000 or len(faces) > 100000:
        raise TeeError(
            "architecture_panel_mesh_limit",
            "Machined panel exceeds the mesh budget.",
            fix="Use fewer explicit machining operations per panel.",
        )
    # Cabinet validation rejects intersecting operation volumes. This independent
    # analytic control catches a geometry backend silently dropping a subtraction.
    expected_removed = sum(
        (
            math.pi * (op["diameter_mm"] / 2) ** 2
            if op["type"] == "drill"
            else op["width_mm"] * op["height_mm"]
        )
        * op["depth_mm"]
        for op in panel["machining"]
    )
    actual_removed = (
        math.prod(panel["size"]) - abs(ifcopenshell.util.shape.get_volume(shape.geometry)) * 1e9
    )
    if not math.isclose(actual_removed, expected_removed, rel_tol=0.005, abs_tol=0.05):
        raise TeeError(
            "architecture_machining_geometry",
            "Panel cut volume disagrees with the operations.",
            fix="Review the operation dimensions; this geometry is not exportable.",
        )
    return {"vertices": (vertices * 1000).tolist(), "faces": faces.tolist()}


def _machined_panel_mesh(panel: dict, cabinet: dict) -> dict:
    # Keep cached coordinates near zero; large world coordinates belong to placement.
    local = {key: panel[key] for key in ("size", "orientation", "thickness", "machining")}
    local["origin"] = [0, 0, 0]
    result = _panel_mesh_cached(json.dumps(local, sort_keys=True, separators=(",", ":")))
    origin = cabinet["origin"]
    angle = math.radians(cabinet.get("properties", {}).get("rotation_deg", 0))
    c, s = math.cos(angle), math.sin(angle)
    points = []
    for point in result["vertices"]:
        x, y = point[0] + panel["origin"][0] - origin[0], point[1] + panel["origin"][1] - origin[1]
        points.append(
            [origin[0] + c * x - s * y, origin[1] + s * x + c * y, point[2] + panel["origin"][2]]
        )
    return {"vertices": points, "faces": [list(face) for face in result["faces"]]}


def preview(document_dict: dict[str, Any]) -> dict[str, Any]:
    document = _document(document_dict)
    spans, joins = _wall_ranges(document)
    entities = document["entities"]
    meshes: list[dict[str, Any]] = []
    openings: dict[str, list[dict]] = {}
    for entity in entities.values():
        if entity["kind"] == "opening":
            openings.setdefault(entity["wall"], []).append(entity)
    count = 0
    for identifier, entity in entities.items():
        kind = entity["kind"]
        parts: list[dict] = []
        if kind == "wall":
            parts = _wall_parts(
                entity,
                openings.get(identifier, []),
                base_elevation(entity, entities),
                spans[identifier],
            )
        elif kind in {"roof", "stair"}:
            from .systems import roof_meshes, stair_meshes

            system_meshes = (
                roof_meshes(entity, base_elevation(entity, entities))
                if kind == "roof"
                else stair_meshes(entity, entities)
            )
            parts = [{"system_mesh": mesh, "component": mesh["part"]} for mesh in system_meshes]
        elif kind == "slab":
            from .penetrations import slab_mesh

            parts = [{"system_mesh": slab_mesh(entity, entities)}]
        elif kind == "space":
            elevation = base_elevation(entity, entities)
            parts = [
                {"polygon": ring, "z": elevation, "depth": entity["height"]}
                for ring in space_polygons(entity)
            ]
        elif kind == "virtual_boundary":
            parts = [{"system_mesh": boundary_mesh(entity, entities), "nonphysical": True}]
        elif kind == "cabinet":
            from .cabinets import panels

            for panel in panels(entity):
                x, y, z = panel["origin"]
                sx, sy, sz = panel["size"]
                parts.append(
                    {
                        "polygon": [[x, y], [x + sx, y], [x + sx, y + sy], [x, y + sy]],
                        "z": z,
                        "depth": sz,
                        "panel_id": panel["id"],
                        **({"machined_panel": panel} if panel.get("machining") else {}),
                    }
                )
            _rotate_parts(
                parts, entity["origin"], entity.get("properties", {}).get("rotation_deg", 0)
            )
        elif kind == "opening":
            parts = _opening_parts(document, entity)
        elif kind == "furnishing":
            parts = _furnishing_parts(entity)
        elif kind == "member":
            from .members import member_mesh

            parts = [
                {
                    "system_mesh": member_mesh(entity, entities),
                    "component": entity["role"],
                    "material_role": entity["role"],
                    "material_id": entity.get("properties", {}).get("bim", {}).get("material_id"),
                }
            ]
        for index, part in enumerate(parts):
            mesh = (
                _machined_panel_mesh(part["machined_panel"], entity)
                if part.get("machined_panel")
                else part["system_mesh"]
                if "system_mesh" in part
                else _prism_mesh(part["polygon"], part["z"], part["depth"])
            )
            count += len(mesh["vertices"])
            if count > 50000 or len(meshes) >= 4000:
                raise TeeError(
                    "architecture_preview_limit",
                    "Preview exceeds the bounded mesh budget.",
                    fix="Preview a smaller document or fewer cabinet shelves.",
                )
            meshes.append(
                {
                    "id": identifier,
                    "entity_id": identifier,
                    "kind": kind,
                    "part": part.get("panel_id", part.get("component", index)),
                    **{
                        key: part[key]
                        for key in ("material_role", "material_id", "nonphysical")
                        if key in part
                    },
                    **mesh,
                }
            )
    vertices = [point for mesh in meshes for point in mesh["vertices"]]
    bounds = (
        {
            "min": [min(p[axis] for p in vertices) for axis in range(3)],
            "max": [max(p[axis] for p in vertices) for axis in range(3)],
        }
        if vertices
        else None
    )
    return {
        "revision": document["revision"],
        "units": "mm",
        "meshes": meshes,
        "bounds": bounds,
        "wall_junctions": _junctions(document, spans),
        "wall_joins": joins,
        "limitations": [
            "Opening construction is explicit when supplied; other fillings remain semantic-only.",
            "Furnishings are dimensioned schematic silhouettes, not manufacturer assemblies.",
            "Spaces are separate transparent volume candidates, not construction solids.",
            (
                "Virtual boundaries are zero-thickness reference surfaces, "
                "not physical assemblies or traversable portals."
            ),
            "Declared drills/pockets are cut; machine programs and hardware remain unverified.",
            "Inspect wall_joins and wall_junctions; other-element intersections remain unverified.",
            (
                "Roof/stair solids exclude drainage details, railings, slab openings and "
                "engineered connections."
            ),
        ],
    }


def export_ifc(document_dict: dict[str, Any], path: Path) -> dict[str, Any]:
    document = _document(document_dict)
    spans, joins = _wall_ranges(document)
    ifc = _ifc()
    import numpy as np

    run = ifc.api.run
    file = run("project.create_file", version="IFC4")
    project_name = document["project"]["name"]

    def create(identifier: str, kind: str, name: str, predefined: str | None = None) -> Any:
        entity = run(
            "root.create_entity", file, ifc_class=kind, name=name, predefined_type=predefined
        )
        entity.GlobalId = _guid(kind + ":" + identifier, document["document_id"])
        return entity

    project = create("project", "IfcProject", project_name)
    units = [
        run("unit.add_si_unit", file, unit_type="LENGTHUNIT", prefix="MILLI"),
        run("unit.add_si_unit", file, unit_type="AREAUNIT"),
        run("unit.add_si_unit", file, unit_type="VOLUMEUNIT"),
    ]
    run("unit.assign_unit", file, units=units)
    context = run("context.add_context", file, context_type="Model")
    body = run(
        "context.add_context",
        file,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=context,
    )
    site = create("site", "IfcSite", project_name + " site")
    building = create("building", "IfcBuilding", project_name)
    run("aggregate.assign_object", file, relating_object=project, products=[site])
    run("aggregate.assign_object", file, relating_object=site, products=[building])
    entities = document["entities"]
    exported: dict[str, Any] = {}
    semantic_products: dict[str, Any] = {}

    def metadata(product: Any, identifier: str, data: dict[str, Any], **extra: Any) -> None:
        properties = {
            "EntityId": identifier,
            "DocumentRevision": document["revision"],
            "Units": "mm",
            **extra,
        }
        for key in ("properties", "provenance"):
            if data.get(key):
                value = data[key]
                if key == "properties":
                    value = {k: v for k, v in value.items() if k not in {"bim", "assembly"}}
                if not value:
                    continue
                safe = json.dumps(_safe_metadata(value), ensure_ascii=True, separators=(",", ":"))
                properties[key.title()] = (
                    safe if len(safe) <= 8192 else "[metadata exceeds 8192 characters]"
                )
        pset = run("pset.add_pset", file, product=product, name="TEE_Architecture")
        pset.GlobalId = _guid(product.GlobalId + ":metadata", document["document_id"])
        run("pset.edit_pset", file, pset=pset, properties=properties)

    def place(product: Any, x: float = 0, y: float = 0, z: float = 0, angle: float = 0) -> None:
        matrix = np.eye(4)
        matrix[:3, 3] = (x, y, z)
        matrix[0, 0], matrix[0, 1] = math.cos(angle), -math.sin(angle)
        matrix[1, 0], matrix[1, 1] = math.sin(angle), math.cos(angle)
        run("geometry.edit_object_placement", file, product=product, matrix=matrix, is_si=False)

    def solid(polygon: list[list[float]], depth: float, z: float = 0) -> Any:
        points = [
            file.create_entity("IfcCartesianPoint", Coordinates=tuple(map(float, point)))
            for point in polygon
        ]
        curve = file.create_entity("IfcPolyline", Points=[*points, points[0]])
        profile = file.create_entity(
            "IfcArbitraryClosedProfileDef", ProfileType="AREA", OuterCurve=curve
        )
        position = file.create_entity(
            "IfcAxis2Placement3D",
            Location=file.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, float(z))),
        )
        direction = file.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
        return file.create_entity(
            "IfcExtrudedAreaSolid",
            SweptArea=profile,
            Position=position,
            ExtrudedDirection=direction,
            Depth=float(depth),
        )

    def assign(product: Any, solids: list[Any], representation_type: str = "SweptSolid") -> None:
        representation = file.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=body,
            RepresentationIdentifier="Body",
            RepresentationType=representation_type,
            Items=solids,
        )
        run("geometry.assign_representation", file, product=product, representation=representation)

    def brep(mesh: dict, origin: list[float]) -> Any:
        points = [
            file.create_entity(
                "IfcCartesianPoint", Coordinates=tuple(float(p[i] - origin[i]) for i in range(3))
            )
            for p in mesh["vertices"]
        ]
        faces = []
        for triangle in mesh["faces"]:
            loop = file.create_entity("IfcPolyLoop", Polygon=[points[i] for i in triangle])
            bound = file.create_entity("IfcFaceOuterBound", Bound=loop, Orientation=True)
            faces.append(file.create_entity("IfcFace", Bounds=[bound]))
        return file.create_entity(
            "IfcFacetedBrep", Outer=file.create_entity("IfcClosedShell", CfsFaces=faces)
        )

    metadata(
        project,
        "project",
        document["project"],
        DocumentId=document["document_id"],
        WallJoinPolicy=joins["policy"],
    )
    for identifier, data in entities.items():
        if data["kind"] != "storey":
            continue
        storey = create(identifier, "IfcBuildingStorey", data["name"])
        storey.Elevation = float(data["elevation"])
        run("aggregate.assign_object", file, relating_object=building, products=[storey])
        place(storey, z=data["elevation"])
        metadata(storey, identifier, data)
        exported[identifier] = storey
    types = {
        "wall": "IfcWall",
        "virtual_boundary": "IfcVirtualElement",
        "member": "IfcMember",
        "space": "IfcSpace",
        "slab": "IfcSlab",
        "roof": "IfcRoof",
        "stair": "IfcStair",
        "cabinet": "IfcFurnishingElement",
        "furnishing": "IfcFurnishingElement",
    }
    for identifier, data in entities.items():
        kind = data["kind"]
        if kind not in types:
            continue
        from .members import IFC_ROLES

        product_class = IFC_ROLES[data["role"]][0] if kind == "member" else types[kind]
        predefined = {"slab": "FLOOR", "roof": "FLAT_ROOF"}.get(kind)
        if kind == "member":
            predefined = IFC_ROLES[data["role"]][1]
        if kind == "roof":
            predefined = {
                "flat": "FLAT_ROOF",
                "mono": "SHED_ROOF",
                "gable": "GABLE_ROOF",
                "planes": "USERDEFINED",
            }[data["form"]]
        elif kind == "stair":
            predefined = "STRAIGHT_RUN_STAIR"
        if kind == "furnishing" and data["category"] in {"basin", "wc", "shower"}:
            product_class = "IfcSanitaryTerminal"
            predefined = {"basin": "WASHHANDBASIN", "wc": "TOILETPAN", "shower": "SHOWER"}[
                data["category"]
            ]
        product = create(identifier, product_class, data["name"], predefined)
        storey = exported[data["storey"]]
        if kind == "space":
            from .spatial import space_environment

            environment = space_environment(data)
            if environment != "unclassified":
                pset = run("pset.add_pset", file, product=product, name="Pset_SpaceCommon")
                run(
                    "pset.edit_pset",
                    file,
                    pset=pset,
                    properties={"IsExternal": environment == "exterior"},
                )
            run("aggregate.assign_object", file, relating_object=storey, products=[product])
        else:
            run("spatial.assign_container", file, relating_structure=storey, products=[product])
        elevation = base_elevation(data, entities)
        if kind == "wall":
            low, high = spans[identifier]
            half = data["thickness"] / 2
            assign(
                product,
                [solid([[low, -half], [high, -half], [high, half], [low, half]], data["height"])],
            )
            a, b = data["start"], data["end"]
            place(product, *a, elevation, math.atan2(b[1] - a[1], b[0] - a[0]))
        elif kind == "virtual_boundary":
            # IFC4 IfcVirtualElement Body SurfaceModel: an explicitly nonphysical
            # imaginary/reference boundary, not an empty physical wall or void.
            # buildingSMART IFC4 FINAL IfcVirtualElement, Common Use Definitions.
            mesh = boundary_mesh(data, entities)
            origin = [*data["start"], elevation]
            points = [
                file.create_entity(
                    "IfcCartesianPoint",
                    Coordinates=tuple(float(p[i] - origin[i]) for i in range(3)),
                )
                for p in mesh["vertices"]
            ]
            loop = file.create_entity("IfcPolyLoop", Polygon=points)
            bound = file.create_entity("IfcFaceOuterBound", Bound=loop, Orientation=True)
            face = file.create_entity("IfcFace", Bounds=[bound])
            surface = file.create_entity(
                "IfcFaceBasedSurfaceModel",
                FbsmFaces=[file.create_entity("IfcConnectedFaceSet", CfsFaces=[face])],
            )
            assign(product, [surface], "SurfaceModel")
            place(product, *origin)
        elif kind == "roof" and data["form"] == "planes":
            from .systems import roof_meshes

            # IFC4 ADD2_TC1 IfcRoof: aggregate ROOF slabs supply the Body; the
            # parent must not duplicate their geometry. USERDEFINED needs ObjectType.
            # standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/
            # ifcsharedbldgelements/lexical/ifcroof.htm
            product.ObjectType = "Explicit planar roof"
            origin = [*data["polygon"][0], elevation + data["base_height"]]
            place(product, *origin)
            for mesh in roof_meshes(data, elevation):
                child_id = identifier + ":" + mesh["part"]
                child = create(child_id, "IfcSlab", data["name"] + " " + mesh["part"], "ROOF")
                run("aggregate.assign_object", file, relating_object=product, products=[child])
                assign(child, [brep(mesh, origin)], "Brep")
                place(child, *origin)
                metadata(
                    child,
                    child_id,
                    {},
                    ParentEntityId=identifier,
                    ParentRoofId=identifier,
                    RoofPlaneId=mesh["part"][6:],
                    ReferenceSurface="top",
                    NormalThicknessMm=float(data["thickness"]),
                    Geometry=(
                        "nominal geometric envelope; physical gauge/profile and mass not inferred"
                    ),
                )
        elif kind == "roof" and data["form"] != "flat":
            from .systems import roof_meshes

            origin = [*data["polygon"][0], elevation + data["base_height"]]
            assign(product, [brep(mesh, origin) for mesh in roof_meshes(data, elevation)], "Brep")
            place(product, *origin)
        elif kind == "stair":
            from .systems import stair_dimensions, stair_meshes

            dims = stair_dimensions(data, entities)
            origin = [*data["start"], elevation]
            place(product, *origin)
            file.create_entity(
                "IfcRelReferencedInSpatialStructure",
                GlobalId=_guid(identifier + ":upper-reference", document["document_id"]),
                RelatedElements=[product],
                RelatingStructure=exported[data["top_storey"]],
            )
            for mesh in stair_meshes(data, entities):
                part = mesh["part"]
                child = create(
                    identifier + ":" + part,
                    "IfcStairFlight" if part == "flight" else "IfcSlab",
                    data["name"] + " " + part,
                    "STRAIGHT" if part == "flight" else "LANDING",
                )
                run("aggregate.assign_object", file, relating_object=product, products=[child])
                assign(child, [brep(mesh, origin)], "Brep")
                place(child, *origin)
                metadata(child, identifier + ":" + part, {}, ParentEntityId=identifier)
                if part == "flight":
                    child.NumberOfRisers = dims["riser_count"]
                    child.NumberOfTreads = dims["tread_count"]
                    child.RiserHeight = float(dims["riser_height_mm"])
                    child.TreadLength = float(dims["going_mm"])
            metadata(
                product,
                identifier,
                data,
                BottomStoreyId=data["storey"],
                TopStoreyId=data["top_storey"],
                Geometry="monolithic flight and optional landing; last tread flush with top level",
            )
        elif kind in {"space", "slab", "roof"}:
            depth = data["height"] if kind == "space" else data["thickness"]
            rings = space_polygons(data) if kind == "space" else [data["polygon"]]
            assign(product, [solid(ring, depth) for ring in rings])
            z = elevation - depth if kind == "slab" else elevation
            place(product, z=z + (data["base_height"] if kind == "roof" else 0))
        elif kind == "member":
            from .members import member_mesh

            if predefined == "USERDEFINED":
                product.ObjectType = data["role"]
            origin = [*data["origin"][:2], data["origin"][2] + elevation]
            assign(product, [brep(member_mesh(data, entities), origin)], "Brep")
            place(product, *origin)
        elif kind == "furnishing":
            local = {**data, "origin": [0, 0, 0], "properties": {}}
            parts = _furnishing_parts(local)
            assign(product, [solid(part["polygon"], part["depth"], part["z"]) for part in parts])
            place(
                product,
                *data["origin"],
                math.radians(data.get("properties", {}).get("rotation_deg", 0)),
            )
        else:
            from .cabinets import panels

            panel_solids = []
            origin = data["origin"]
            panel_rows = panels(data)
            machined = any(panel.get("machining") for panel in panel_rows)
            for panel in panel_rows:
                if machined:
                    if panel.get("machining"):
                        _machined_panel_mesh(
                            panel, data
                        )  # Verify actual cut volume before publication.
                    panel_solids.append(_panel_csg(file, panel, origin))
                    continue
                x, y, z = [panel["origin"][i] - origin[i] for i in range(3)]
                sx, sy, sz = panel["size"]
                panel_solids.append(
                    solid([[x, y], [x + sx, y], [x + sx, y + sy], [x, y + sy]], sz, z)
                )
            assign(product, panel_solids, "SolidModel" if machined else "SweptSolid")
            place(product, *origin, math.radians(data.get("properties", {}).get("rotation_deg", 0)))
            binding = data.get("properties", {}).get("bim", {})
            if not binding.get("type_id") and not binding.get("material_id"):
                material = run("material.add_material", file, name=data["material"])
                run("material.assign_material", file, products=[product], material=material)
        metadata(
            product,
            identifier,
            data,
            Geometry="panel solids"
            if kind == "cabinet"
            else (
                "schematic furnishing; not manufacturer geometry"
                if kind == "furnishing"
                else "authored roof/stair solid"
                if kind in {"roof", "stair"}
                else "nonphysical reference surface; physical fill and access unverified"
                if kind == "virtual_boundary"
                else "authored extrusion"
            ),
            BaseOffsetMm=float(data.get("base_offset", 0)),
            **(
                {
                    "SpacePartCount": len(space_polygons(data)),
                    "SpaceEnvironment": space_environment(data),
                    "SpaceVolumeBasis": (
                        "reference prism; exterior height does not assert a ceiling"
                    ),
                }
                if kind == "space"
                else {}
            ),
        )
        exported[identifier] = product
        semantic_products[identifier] = product
    for identifier, data in entities.items():
        if data["kind"] != "virtual_boundary":
            continue
        for space_id in data.get("space_ids", []):
            file.create_entity(
                "IfcRelSpaceBoundary",
                GlobalId=_guid(identifier + ":space-boundary:" + space_id, document["document_id"]),
                Name="Explicit authored reference; adjacency not independently verified",
                RelatingSpace=exported[space_id],
                RelatedBuildingElement=exported[identifier],
                PhysicalOrVirtualBoundary="VIRTUAL",
                InternalOrExternalBoundary="INTERNAL"
                if len(data["space_ids"]) == 2
                else "NOTDEFINED",
            )
    filling_count = 0
    for identifier, data in entities.items():
        if data["kind"] == "slab_opening":
            slab = entities[data["slab"]]
            opening = create(identifier, "IfcOpeningElement", data["name"], "OPENING")
            # Cut fully through the host; overcut is outside the two slab faces.
            assign(opening, [solid(data["polygon"], slab["thickness"] + 2)])
            run("feature.add_feature", file, feature=opening, element=exported[data["slab"]])
            place(opening, z=base_elevation(slab, entities) - slab["thickness"] - 1)
            metadata(opening, identifier, data, HostSlabId=data["slab"], OvercutEachSideMm=1.0)
            exported[identifier] = opening
            continue
        if data["kind"] != "opening":
            continue
        wall = entities[data["wall"]]
        host = exported[data["wall"]]
        opening = create(identifier, "IfcOpeningElement", data["name"], "OPENING")
        # One mm overcut on each wall side avoids coincident boolean faces.
        half = wall["thickness"] / 2 + 1
        assign(
            opening,
            [
                solid(
                    [[0, -half], [data["width"], -half], [data["width"], half], [0, half]],
                    data["height"],
                )
            ],
        )
        run("feature.add_feature", file, feature=opening, element=host)
        a, b = wall["start"], wall["end"]
        angle = math.atan2(b[1] - a[1], b[0] - a[0])
        x, y = a[0] + math.cos(angle) * data["offset"], a[1] + math.sin(angle) * data["offset"]
        z = base_elevation(wall, entities) + data["sill"]
        place(opening, x, y, z, angle)
        metadata(
            opening,
            identifier,
            data,
            NominalWidthMm=float(data["width"]),
            NominalHeightMm=float(data["height"]),
            OvercutEachSideMm=1.0,
        )
        exported[identifier] = opening
        if data["fill"] != "void":
            from .bim import opening_components

            filling = create(
                identifier + ":fill",
                "IfcDoor" if data["fill"] == "door" else "IfcWindow",
                data["name"] + " " + data["fill"],
            )
            filling.OverallWidth, filling.OverallHeight = (
                float(data["width"]),
                float(data["height"]),
            )
            run("feature.add_filling", file, opening=opening, element=filling)
            run(
                "spatial.assign_container",
                file,
                relating_structure=exported[wall["storey"]],
                products=[filling],
            )
            place(filling, x, y, z, angle)
            components = opening_components(data, wall["thickness"])
            if components:
                solids = []
                for component in components:
                    cx, cy, cz = component["origin"]
                    sx, sy, sz = component["size"]
                    item = solid(
                        [[cx, cy], [cx + sx, cy], [cx + sx, cy + sy], [cx, cy + sy]], sz, cz
                    )
                    role = component["material_role"]
                    colours = {
                        "frame": (0.25, 0.28, 0.30),
                        "glazing": (0.65, 0.85, 0.92),
                        "leaf": (0.65, 0.48, 0.30),
                    }
                    colour = file.create_entity(
                        "IfcColourRgb",
                        Red=colours[role][0],
                        Green=colours[role][1],
                        Blue=colours[role][2],
                    )
                    shading = file.create_entity(
                        "IfcSurfaceStyleShading",
                        SurfaceColour=colour,
                        Transparency=0.65 if role == "glazing" else 0.0,
                    )
                    style = file.create_entity(
                        "IfcSurfaceStyle", Name=role, Side="BOTH", Styles=[shading]
                    )
                    file.create_entity(
                        "IfcStyledItem", Item=item, Styles=[style], Name=component["name"]
                    )
                    solids.append(item)
                assign(filling, solids)
            metadata(
                filling,
                identifier + ":fill",
                {},
                Geometry="explicit closed-position frame and panel solids"
                if components
                else "semantic-only; construction not supplied",
            )
            semantic_products[identifier] = filling
            filling_count += 1
    from .bim import export_semantics

    semantic_report = export_semantics(file, document, semantic_products)
    from .distribution import export_ifc as export_distribution

    distribution_report = export_distribution(file, document, semantic_products)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    file.write(str(path))
    return {
        "path": str(path),
        "schema": "IFC4",
        "units": "mm",
        "revision": document["revision"],
        "entities": len(exported),
        "fillings": filling_count,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "wall_junctions": _junctions(document, spans),
        "wall_joins": joins,
        "bim": semantic_report,
        "distribution": distribution_report,
        "limitations": [
            "Door/window bodies need assembly dimensions; other fillings remain semantic-only.",
            "Furnishings are schematic, not manufacturer geometry or service design.",
            "Declared drills/pockets are cut into finished panels; separate edge bands omitted.",
            "Schema, geometry, IDS and jurisdiction verification are separate checks.",
            (
                "Virtual boundaries are nonphysical reference surfaces; "
                "physical fill and access remain unverified."
            ),
            "Inspect wall_joins and wall_junctions; other-element intersections remain unverified.",
        ],
    }


def validate_ifc(path: Path) -> dict[str, Any]:
    """Schema/EXPRESS and measured geometry are independent, bounded checks."""
    path = Path(path)
    if path.stat().st_size > 64 * 1024 * 1024:
        raise TeeError(
            "architecture_ifc_limit",
            "IFC exceeds the 64 MiB validation limit.",
            fix="Validate a smaller model or use an external IFC checker.",
        )
    ifc = _ifc()
    import ifcopenshell.geom
    import ifcopenshell.util.element
    import ifcopenshell.util.shape
    import ifcopenshell.util.unit
    import ifcopenshell.validate

    file = ifc.open(str(path))
    if sum(1 for _ in file) > 200000:
        raise TeeError(
            "architecture_ifc_limit",
            "IFC exceeds 200,000 entities.",
            fix="Validate a smaller model.",
        )

    class Logger(ifcopenshell.validate.json_logger):
        def __init__(self) -> None:
            super().__init__()
            self.count = 0

        def log(self, level: str, message: str, *args: Any) -> None:
            self.count += 1
            if len(self.statements) < 20:
                self.statements.append({"level": level, "message": (message % args)[:300]})

    logger = Logger()
    # 0.8.5 rule_executor.py:95 uses open(fn).read() without a context manager.
    # Capture that specific dependency warning and expose it; all other warning
    # policies remain active. The upstream checker temporarily changes a global
    # IFC setting, so serialize this operation within the process as well.
    with _VALIDATE_LOCK, warnings.catch_warnings(record=True) as captured:
        warnings.filterwarnings(
            "always", category=ResourceWarning, module=r"ifcopenshell\.express\.rule_executor"
        )
        prior_inverse_setting = ifc.settings.unpack_non_aggregate_inverses
        try:
            ifcopenshell.validate.validate(file, logger, express_rules=True)
        finally:
            ifc.settings.unpack_non_aggregate_inverses = prior_inverse_setting
    scale = ifcopenshell.util.unit.calculate_unit_scale(file)
    products = file.by_type("IfcProduct")
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    measured = []
    virtual_surfaces = []
    failures = []
    for product in products[:2000]:
        if not product.Representation or product.is_a("IfcOpeningElement"):
            continue
        try:
            shape = ifcopenshell.geom.create_shape(settings, product)
            verts = ifcopenshell.util.shape.get_vertices(shape.geometry)
            psets = ifcopenshell.util.element.get_psets(product).get("TEE_Architecture", {})
            if product.is_a("IfcVirtualElement"):
                area = float(ifcopenshell.util.shape.get_area(shape.geometry))
                if not len(verts) or not math.isfinite(area) or area <= 0:
                    raise ValueError("non-positive or non-finite virtual surface area")
                virtual_surfaces.append(
                    {
                        "guid": product.GlobalId,
                        "id": psets.get("EntityId"),
                        "class": product.is_a(),
                        "area_m2": round(area, 12),
                        "physical_volume": "not_applicable",
                        "bounds_mm": {
                            "min": [round(float(v) * 1000, 6) for v in verts.min(axis=0)],
                            "max": [round(float(v) * 1000, 6) for v in verts.max(axis=0)],
                        },
                        "space_references": len(product.ProvidesBoundaries),
                        "adjacency": "not_verified",
                    }
                )
                continue
            volume = abs(float(ifcopenshell.util.shape.get_volume(shape.geometry)))
            if not len(verts) or not math.isfinite(volume) or volume <= 0:
                raise ValueError("non-positive or non-finite solid volume")
            measured.append(
                {
                    "guid": product.GlobalId,
                    "id": psets.get("EntityId"),
                    "class": product.is_a(),
                    "volume_m3": round(volume, 12),
                    "bounds_mm": {
                        "min": [round(float(v) * 1000, 6) for v in verts.min(axis=0)],
                        "max": [round(float(v) * 1000, 6) for v in verts.max(axis=0)],
                    },
                }
            )
        except Exception as exc:
            failures.append({"guid": product.GlobalId, "reason": type(exc).__name__})
    roof_assemblies = []
    measured_by_guid = {row["guid"]: row for row in measured}
    for roof in file.by_type("IfcRoof"):
        if roof.ObjectType != "Explicit planar roof":
            continue
        pset = ifcopenshell.util.element.get_psets(roof).get("TEE_Architecture", {})
        children = [child for relation in roof.IsDecomposedBy for child in relation.RelatedObjects]
        child_rows = [measured_by_guid.get(child.GlobalId) for child in children]
        valid = (
            not roof.Representation
            and bool(children)
            and len({child.GlobalId for child in children}) == len(children)
            and all(child.is_a("IfcSlab") and child.PredefinedType == "ROOF" for child in children)
            and all(row is not None for row in child_rows)
        )
        if not valid:
            failures.append(
                {
                    "guid": roof.GlobalId,
                    "reason": (
                        "Explicit planar roof needs unique represented ROOF slab children "
                        "and no duplicate parent body"
                    ),
                }
            )
            continue
        roof_assemblies.append(
            {
                "guid": roof.GlobalId,
                "id": pset.get("EntityId"),
                "child_ids": [row["id"] for row in child_rows],
                "plane_count": len(child_rows),
                "volume_m3": sum(row["volume_m3"] for row in child_rows),
                "bounds_mm": {
                    "min": [
                        min(row["bounds_mm"]["min"][i] for row in child_rows) for i in range(3)
                    ],
                    "max": [
                        max(row["bounds_mm"]["max"][i] for row in child_rows) for i in range(3)
                    ],
                },
                "quantity_policy": (
                    "Summary of measured child envelopes; not an additional physical "
                    "product or verified net material volume"
                ),
            }
        )
    return {
        "schema": {
            "status": "pass" if logger.count == 0 else "fail",
            "ifc_schema": file.schema,
            "express_rules": True,
            "findings_count": logger.count,
            "findings": logger.statements,
            "dependency_warnings": [
                {
                    "category": row.category.__name__,
                    "reason": "IfcOpenShell EXPRESS rule source file closed by finalization.",
                }
                for row in captured[:5]
            ],
        },
        "geometry": {
            "status": "fail"
            if failures
            else (
                "not_verified"
                if len(products) > 2000 or not (measured or virtual_surfaces)
                else "pass"
            ),
            "products_measured": len(measured),
            "measurements": measured,
            "roof_assemblies": roof_assemblies,
            "virtual_surfaces": virtual_surfaces,
            "virtual_surfaces_measured": len(virtual_surfaces),
            "failures": failures[:20],
            "scope": (
                "Represented physical products require positive solid volumes; "
                "virtual boundaries require measurable surfaces and carry no material volume. "
                "Schema-only fillings are not construction solids."
            ),
            "quantity_policy": "Per-product volumes; overlaps prevent adding as net material.",
            "junctions": "not_verified; inspect the authoring export's wall_junctions report",
            "unrepresented_fillings": sum(
                1
                for product in products
                if (product.is_a("IfcDoor") or product.is_a("IfcWindow"))
                and not product.Representation
            ),
        },
        "length_unit_metres": scale,
        "classes": dict(Counter(p.is_a() for p in products)),
        "ids": {"status": "not_verified", "reason": "No IDS specification supplied to this check."},
        "regulatory": {
            "status": "not_verified",
            "reason": "IFC validity is not building approval.",
        },
    }


def export_glb(document_dict: dict[str, Any], path: Path) -> dict[str, Any]:
    """Visual interchange in glTF metres; stable semantic node names survive export."""
    derived = preview(document_dict)
    try:
        import numpy as np
        import trimesh
    except ImportError as exc:
        raise TeeError(
            "architecture_mesh_unavailable",
            "Trimesh is unavailable.",
            fix="Use the existing geometry-enabled TEE interpreter.",
        ) from exc
    scene = trimesh.Scene()
    scene.metadata.update({"units": "m", "source_units": "mm", "revision": derived["revision"]})
    colours = {
        "wall": [185, 194, 199, 255],
        "space": [70, 155, 200, 35],
        "slab": [135, 145, 155, 255],
        "roof": [100, 113, 130, 255],
        "stair": [150, 155, 165, 255],
        "cabinet": [181, 141, 90, 255],
        "furnishing": [180, 170, 150, 255],
        "opening": [65, 72, 80, 255],
        "virtual_boundary": [125, 95, 180, 40],
        "member": [155, 158, 164, 255],
    }
    from .spatial import space_environment

    nodes = []
    for item in derived["meshes"]:
        # Float32 glTF vertices stay close to a local origin and, for oriented
        # parts, their authored axes. Placement remains in the node transform.
        entity = document_dict["entities"][item["id"]]
        angle = 0.0
        if entity["kind"] in {"cabinet", "furnishing"}:
            angle = math.radians(entity.get("properties", {}).get("rotation_deg", 0))
        elif entity["kind"] in {"wall", "opening"}:
            wall = entity if entity["kind"] == "wall" else document_dict["entities"][entity["wall"]]
            angle = math.atan2(wall["end"][1] - wall["start"][1], wall["end"][0] - wall["start"][0])
        c, s = math.cos(angle), math.sin(angle)
        rotation = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        aligned = np.asarray(item["vertices"], dtype=float) @ rotation
        centre = (aligned.min(axis=0) + aligned.max(axis=0)) / 2
        transform = np.eye(4)
        transform[:3, :3] = rotation
        transform[:3, 3] = rotation @ centre / 1000
        mesh = trimesh.Trimesh(
            vertices=(aligned - centre) / 1000,
            faces=item["faces"],
            process=False,
        )
        role = item.get("material_role")
        mesh.metadata.update(
            {
                "entity_id": item["id"],
                "kind": item["kind"],
                "material_role": role,
                "nonphysical": bool(item.get("nonphysical")),
                **(
                    {
                        "environment": space_environment(entity),
                        "conditioned": entity.get("conditioned"),
                    }
                    if entity["kind"] == "space"
                    else {}
                ),
            }
        )
        colour = {"glazing": [170, 220, 240, 90], "leaf": [170, 125, 80, 255]}.get(
            role, colours[item["kind"]]
        )
        material = trimesh.visual.material.PBRMaterial(
            name=role or item["kind"],
            baseColorFactor=colour,
            metallicFactor=0,
            roughnessFactor=0.85,
            alphaMode="BLEND"
            if item["kind"] in {"space", "virtual_boundary"} or role == "glazing"
            else "OPAQUE",
            doubleSided=True,
        )
        mesh.visual = trimesh.visual.texture.TextureVisuals(material=material)
        node = item["id"] + ":" + str(item["part"])
        scene.add_geometry(mesh, node_name=node, geom_name=node, transform=transform)
        nodes.append(node)
    if not nodes:
        raise TeeError(
            "architecture_empty_mesh",
            "There is no geometry to export.",
            fix="Author a wall, space, slab, roof or cabinet first.",
        )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(scene.export(file_type="glb"))
    return {
        "path": str(path),
        "units": "m",
        "source_units": "mm",
        "revision": derived["revision"],
        "nodes": len(nodes),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "limitations": derived["limitations"],
    }


def _wall_ranges(document: dict[str, Any]) -> tuple[dict[str, tuple[float, float]], dict]:
    """Opt-in orthogonal L/T butt joints; authored axes and offsets stay fixed."""
    from .model import ArchitectureError

    entities = document["entities"]
    walls = {key: value for key, value in entities.items() if value["kind"] == "wall"}
    spans = {key: (0.0, math.dist(wall["start"], wall["end"])) for key, wall in walls.items()}
    policy = document["project"]["facts"].get("wall_join_policy")
    report: dict[str, Any] = {"policy": policy or "unjoined", "count": 0, "joints": []}
    if policy is None:
        return spans, report
    if policy != "orthogonal_butt_v1":
        raise ArchitectureError(
            "ak_join_policy",
            "Unsupported wall join policy.",
            "Use orthogonal_butt_v1 or remove wall_join_policy.",
        )
    tolerance = 1e-6  # mm; only coincident authored endpoints/axes are joined.
    joints = []

    def reject(reason: str) -> None:
        raise ArchitectureError(
            "ak_join_unsupported",
            reason,
            "Adjust the named junction/opening or remove wall_join_policy.",
        )

    def cross(a: list[float], b: list[float]) -> float:
        return a[0] * b[1] - a[1] * b[0]

    items = sorted(walls.items())
    for index, (first, a) in enumerate(items):
        for second, b in items[index + 1 :]:
            za, zb = [base_elevation(wall, entities) for wall in (a, b)]
            if min(za + a["height"], zb + b["height"]) - max(za, zb) <= tolerance:
                continue
            overlap = _intersection_area(_wall_polygon(a), _wall_polygon(b))
            ra = [a["end"][i] - a["start"][i] for i in range(2)]
            rb = [b["end"][i] - b["start"][i] for i in range(2)]
            lengths = (math.dist(a["start"], a["end"]), math.dist(b["start"], b["end"]))
            denominator = cross(ra, rb)
            if abs(denominator) < 1e-12 * lengths[0] * lengths[1]:
                if overlap > tolerance:
                    reject(f"Parallel overlapping walls {first}/{second} need an explicit design.")
                continue
            delta = [b["start"][i] - a["start"][i] for i in range(2)]
            ta, tb = cross(delta, rb) / denominator, cross(delta, ra) / denominator
            inside = all(
                -tolerance <= t * length <= length + tolerance
                for t, length in zip((ta, tb), lengths, strict=True)
            )
            if not inside:
                if overlap > tolerance:
                    reject(f"Overlapping walls {first}/{second} have no centerline junction.")
                continue
            if abs(sum(x * y for x, y in zip(ra, rb, strict=True))) > 1e-8 * math.prod(lengths):
                reject(f"Walls {first}/{second} are not orthogonal.")
            if abs(za - zb) > tolerance or abs(a["height"] - b["height"]) > tolerance:
                reject(f"Walls {first}/{second} have different base/top elevations.")
            ends = []
            for t, length in zip((ta, tb), lengths, strict=True):
                ends.append(
                    0
                    if abs(t * length) <= tolerance
                    else (1 if abs((1 - t) * length) <= tolerance else None)
                )
            if ends == [None, None]:
                reject(f"X junction {first}/{second} is outside the L/T butt policy.")
            # Sorted IDs pick the through wall at L; the continuous wall wins at T.
            through = 0 if ends[1] is not None else 1
            abutting = 1 - through
            point = [a["start"][i] + ta * ra[i] for i in range(2)] + [za]
            if any(math.dist(prior["point"], point) <= tolerance for prior in joints):
                reject(f"Multiway junction involving {first}/{second} is ambiguous.")
            joints.append(
                {
                    "walls": [first, second],
                    "point": point,
                    "through": (first, second)[through],
                    "type": "L" if all(end is not None for end in ends) else "T",
                }
            )
            names, rows = (first, second), (a, b)
            name = names[abutting]
            low, high = spans[name]
            trim = rows[through]["thickness"] / 2
            spans[name] = (low + trim, high) if ends[abutting] == 0 else (low, high - trim)
            if ends[through] is not None:
                name = names[through]
                low, high = spans[name]
                extend = rows[abutting]["thickness"] / 2
                spans[name] = (low - extend, high) if ends[through] == 0 else (low, high + extend)
    for identifier, (low, high) in spans.items():
        if high - low <= tolerance:
            reject(f"Wall {identifier} is consumed by its butt trims.")
    # Check original junction footprints as well as final footprints: trimming
    # a T endpoint must not conceal that it lands in a door/window opening.
    for opening in entities.values():
        if opening["kind"] != "opening":
            continue
        identifier = opening["wall"]
        wall = walls[identifier]
        low, high = spans[identifier]
        if (
            opening["offset"] < low - tolerance
            or opening["offset"] + opening["width"] > high + tolerance
        ):
            reject(f"Opening {opening['id']} intersects the butt trim of wall {identifier}.")
        void = _wall_polygon(wall, opening["offset"], opening["offset"] + opening["width"])
        bottom = base_elevation(wall, entities) + opening["sill"]
        for other_id, other in walls.items():
            if other_id == identifier:
                continue
            z = base_elevation(other, entities)
            if min(bottom + opening["height"], z + other["height"]) - max(bottom, z) <= tolerance:
                continue
            if (
                max(
                    _intersection_area(void, _wall_polygon(other)),
                    _intersection_area(void, _wall_polygon(other, *spans[other_id])),
                )
                > tolerance
            ):
                reject(f"Opening {opening['id']} intersects wall junction {other_id}.")
    checked = _junctions(document, spans)
    if checked["status"] != "no_wall_overlap_found":
        reject("Derived butt junctions still overlap or exceed the verification budget.")
    report.update(
        {
            "count": len(joints),
            "joints": joints[:128],
            "details_limit": 128,
            "source_centerlines_unchanged": True,
        }
    )
    return spans, report


def validate_geometry_policy(document: dict[str, Any]) -> dict[str, Any]:
    """Validate an already structurally checked document, without mesh libraries.

    No call to Document/from_dict here: core validation invokes this function.
    Unsupported explicit join policies raise before an authoring transaction commits.
    """
    spans, joins = _wall_ranges(document)
    overlaps = _junctions(document, spans)
    return {
        "status": "not_verified",
        "wall_joins": joins,
        "wall_junctions": overlaps,
        "scope": "Selected wall junction policy and bounded wall-wall overlap checks only.",
        "remaining": [
            "room enclosure and other-element intersections",
            "structural, service and construction-system design",
            "regulatory and fabrication approval",
        ],
    }
