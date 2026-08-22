"""Handoff tier 1 (7.7): plan facts -> IFC authored offline via ifcopenshell.

Produces real BIM entities (IfcWall with body representation, storeys with
elevations) that open in Bonsai (Blender 4.0-5.x). API shapes verified
empirically against ifcopenshell 0.8.5.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from tee.extract.plan import wall_angle, wall_length, wall_midpoint
from tee.kernel.errors import TeeError


def export_ifc(
    plan: dict[str, Any], out_path: Path, project_name: str = "TEE Export"
) -> dict[str, Any]:
    try:
        import ifcopenshell
        import ifcopenshell.api
        import numpy as np
    except ImportError as exc:
        raise TeeError(
            "ifc_unavailable",
            f"ifcopenshell is not installed: {exc}",
            fix="Install the extract extra: uv sync --extra extract.",
        ) from exc

    run = ifcopenshell.api.run
    file = run("project.create_file", version="IFC4")
    project = run("root.create_entity", file, ifc_class="IfcProject", name=project_name)
    run("unit.assign_unit", file)
    ctx = run("context.add_context", file, context_type="Model")
    body = run(
        "context.add_context",
        file,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=ctx,
    )
    site = run("root.create_entity", file, ifc_class="IfcSite", name="Site")
    building = run("root.create_entity", file, ifc_class="IfcBuilding", name=project_name)
    run("aggregate.assign_object", file, relating_object=project, products=[site])
    run("aggregate.assign_object", file, relating_object=site, products=[building])

    storeys: dict[int, Any] = {}
    for level in plan.get("levels") or [{"index": 0, "elevation_z": 0.0}]:
        storey = run(
            "root.create_entity",
            file,
            ifc_class="IfcBuildingStorey",
            name=level.get("name") or f"Level {level['index']}",
        )
        storey.Elevation = float(level.get("elevation_z") or 0.0)
        storeys[level["index"]] = storey
    run(
        "aggregate.assign_object",
        file,
        relating_object=building,
        products=list(storeys.values()),
    )

    default_storey = next(iter(storeys.values()))
    count = 0
    for wall in plan.get("walls", []):
        entity = run("root.create_entity", file, ifc_class="IfcWall", name=wall["id"])
        height = float(wall.get("height") or 2.7)
        rep = run(
            "geometry.add_wall_representation",
            file,
            context=body,
            length=wall_length(wall),
            height=height,
            thickness=float(wall["thickness"]),
        )
        run("geometry.assign_representation", file, product=entity, representation=rep)
        angle = wall_angle(wall)
        mid_x, mid_y = wall_midpoint(wall)
        length = wall_length(wall)
        # wall representation extrudes along +X from its origin: place the
        # origin at endpoint a, rotated to aim at b
        matrix = np.eye(4)
        matrix[0][0], matrix[0][1] = math.cos(angle), -math.sin(angle)
        matrix[1][0], matrix[1][1] = math.sin(angle), math.cos(angle)
        matrix[0][3] = mid_x - (length / 2) * math.cos(angle)
        matrix[1][3] = mid_y - (length / 2) * math.sin(angle)
        level = plan.get("levels") or []
        elevation = 0.0
        for lvl in level:
            if lvl["index"] == wall.get("level", 0):
                elevation = float(lvl.get("elevation_z") or 0.0)
        matrix[2][3] = elevation
        run("geometry.edit_object_placement", file, product=entity, matrix=matrix)
        storey = storeys.get(wall.get("level", 0), default_storey)
        run("spatial.assign_container", file, relating_structure=storey, products=[entity])
        count += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    file.write(str(out_path))
    return {"path": str(out_path), "walls": count, "storeys": len(storeys)}
