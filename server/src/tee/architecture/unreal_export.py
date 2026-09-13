"""Selected static-mesh Editor export with explicit, checked coordinate frames.

Source-reviewed against Epic's Python 5.6 class references on 2026-09-11:
EditorActorSubsystem, Actor, StaticMeshComponent, InstancedStaticMeshComponent,
SceneComponent, Transform, AssetExportTask, StaticMeshExporterOBJ and Exporter.
Their canonical URLs are recorded in data/README.md. No live Unreal acceptance
is claimed. Importing this module neither imports Unreal nor starts an Editor.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

_UNITS = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4, "ft": 304.8}


def _value(value: Any) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or abs(value) > 1e12
        or not math.isfinite(value)
    ):
        raise ValueError("Frame values must be finite numbers within 1e12.")
    return float(value)


def _det(matrix: list[list[float]]) -> float:
    a, b, c = matrix
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def _matrix(value: Any) -> list[list[float]]:
    if (
        not isinstance(value, list)
        or len(value) != 4
        or any(not isinstance(row, list) or len(row) != 4 for row in value)
    ):
        raise ValueError("Supply both explicit 4x4 coordinate-frame matrices.")
    result = [[_value(v) for v in row] for row in value]
    if result[3] != [0, 0, 0, 1] or abs(_det([row[:3] for row in result[:3]])) < 1e-12:
        raise ValueError("Coordinate frames must be invertible affine matrices.")
    return result


def _multiply(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def _controls(
    matrix: list[list[float]],
    units: str,
    controls: Any,
    tolerance: float,
) -> dict[str, Any]:
    if not isinstance(controls, list) or len(controls) != 4:
        raise ValueError("Supply four measured noncoplanar mesh/unreal_mm control-point pairs.")
    source, target = [], []
    for control in controls:
        if not isinstance(control, dict):
            raise ValueError("Each basis control requires mesh and unreal_mm triples.")
        for key, destination, factor in (("mesh", source, _UNITS[units]), ("unreal_mm", target, 1)):
            vector = control.get(key)
            if not isinstance(vector, list) or len(vector) != 3:
                raise ValueError("Each basis control requires mesh and unreal_mm triples.")
            destination.append([_value(v) * factor for v in vector])
    edges = [[source[index][axis] - source[0][axis] for axis in range(3)] for index in (1, 2, 3)]
    if abs(_det(edges)) < max(tolerance**3, 1e-9):
        raise ValueError("Basis controls are coplanar or too close; measure a 3D control fixture.")
    errors = []
    for point, expected in zip(source, target, strict=True):
        actual = [sum(matrix[i][j] * point[j] for j in range(3)) + matrix[i][3] for i in range(3)]
        errors.append(math.sqrt(sum((a - b) ** 2 for a, b in zip(actual, expected, strict=True))))
    if max(errors) > tolerance:
        raise ValueError(
            "Mesh frame disagrees with measured controls; correct units or axis mapping."
        )
    return {
        "control_points": controls,
        "max_residual_mm": max(errors),
        "tolerance_mm": tolerance,
        "verification": "supplied_control_consistency_only",
    }


def _world_matrix(transform: Any, unreal: Any) -> list[list[float]]:
    # Probe basis positions through the documented Transform API; avoid assuming
    # Unreal's Matrix row/column storage or quaternion component conventions.
    positions = [
        transform.transform_location(unreal.Vector(*point))
        for point in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))
    ]
    xyz = [[_value(getattr(point, axis)) for axis in ("x", "y", "z")] for point in positions]
    result = [[xyz[j + 1][i] - xyz[0][i] for j in range(3)] + [xyz[0][i] * 10] for i in range(3)]
    return _matrix([*result, [0, 0, 0, 1]])


def export_selected(
    output_dir: str | Path,
    *,
    mesh_units: str,
    mesh_to_unreal_mm: list[list[float]],
    unreal_world_to_target_mm: list[list[float]],
    basis_controls: list[dict[str, Any]],
    basis_evidence: str,
    tolerance_mm: float = 0.1,
) -> dict[str, Any]:
    """Run explicitly inside an Editor, exporting only selected static meshes.

    mesh_to_unreal_mm maps exported mesh coordinates after unit conversion to
    Unreal asset-local millimetres. unreal_world_to_target_mm maps Unreal world
    millimetres into the desired right-handed Z-up project frame. Neither has a
    guessed default. Four supplied measured controls check the exporter's basis.
    """
    if mesh_units not in _UNITS:
        raise ValueError("Declare exported mesh units: mm, cm, m, in or ft.")
    mesh_frame, target_frame = _matrix(mesh_to_unreal_mm), _matrix(unreal_world_to_target_mm)
    tolerance = _value(tolerance_mm)
    if not 0 < tolerance <= 100:
        raise ValueError("Control tolerance must be greater than zero and at most 100 mm.")
    if not isinstance(basis_evidence, str) or not 1 <= len(basis_evidence) <= 512:
        raise ValueError("Name the measured export-basis evidence before exporting.")
    control = _controls(mesh_frame, mesh_units, basis_controls, tolerance)
    import unreal

    selected = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_selected_level_actors()
    if not 1 <= len(selected) <= 128:
        raise ValueError("Select 1-128 actors containing supported static mesh components.")
    pending = []
    for actor in selected:
        components = actor.get_components_by_class(unreal.StaticMeshComponent)
        for component in components:
            # A spline mesh is a deformed subclass; exporting its asset would
            # omit that deformation. Support exact types explicitly.
            if type(component).__name__ not in {
                "StaticMeshComponent",
                "InstancedStaticMeshComponent",
                "HierarchicalInstancedStaticMeshComponent",
            }:
                raise ValueError(
                    "Selected component deformation/type is unsupported; "
                    "export reviewed baked geometry."
                )
            mesh = component.get_editor_property("static_mesh")
            if mesh is None:
                raise ValueError("Selected static mesh component has no mesh asset.")
            count = (
                component.get_instance_count()
                if isinstance(component, unreal.InstancedStaticMeshComponent)
                else 1
            )
            if not 1 <= count <= 128 or len(pending) + count > 128:
                raise ValueError("Export supports at most 128 selected mesh instances.")
            for instance in range(count):
                world = (
                    component.get_instance_transform(instance, world_space=True)
                    if isinstance(component, unreal.InstancedStaticMeshComponent)
                    else component.get_world_transform()
                )
                if world is None:
                    raise ValueError("Unreal did not return the selected instance transform.")
                frame = _matrix(
                    _multiply(target_frame, _multiply(_world_matrix(world, unreal), mesh_frame))
                )
                ids = [str(obj.get_path_name()) for obj in (actor, component, mesh)]
                if any(not item or len(item) > 256 for item in ids):
                    raise ValueError("Selected object identifier exceeds the interchange limit.")
                pending.append((mesh, ids, instance, frame))
    if not pending:
        raise ValueError("No supported static mesh components are selected.")
    directory = Path(output_dir).expanduser().absolute()
    if any(parent.is_symlink() for parent in (directory, *directory.parents)):
        raise ValueError("Export directory must not contain symlink components.")
    # A new owned directory prevents replacement of existing exports or designs.
    directory.mkdir(mode=0o700, parents=False, exist_ok=False)
    exported = {}
    instances = []
    for mesh, ids, instance, frame in pending:
        asset_id = ids[2]
        if asset_id not in exported:
            filename = hashlib.sha256(asset_id.encode()).hexdigest()[:24] + ".obj"
            path = directory / filename
            task = unreal.AssetExportTask()
            for key, value in {
                "object": mesh,
                "filename": str(path),
                "exporter": unreal.StaticMeshExporterOBJ(),
                "automated": True,
                "prompt": False,
                "replace_identical": False,
            }.items():
                task.set_editor_property(key, value)
            if (
                not unreal.Exporter.run_asset_export_task(task)
                or not path.is_file()
                or path.stat().st_size == 0
            ):
                raise ValueError(
                    "Unreal mesh export failed; partial files remain for inspection, "
                    "no manifest accepted."
                )
            if path.is_symlink() or path.stat().st_size > 32 * 1024 * 1024:
                raise ValueError(
                    "Unreal mesh export exceeds 32 MiB or is not a regular owned file."
                )
            exported[asset_id] = filename
        instances.append(
            {
                "actor": ids[0],
                "component": ids[1],
                "instance": str(instance),
                "mesh": exported[asset_id],
                "units": mesh_units,
                "transform": frame,
            }
        )
    manifest = {
        "schema": "tee-unreal-geometry/1",
        "frame": "right-handed-z-up",
        "transform_units": "mm",
        "instances": instances,
        "exporter": "archkiln-selected-static-mesh/1",
        "basis_evidence": basis_evidence,
        "basis_control": control,
        "mesh_to_unreal_mm": mesh_frame,
        "unreal_world_to_target_mm": target_frame,
        "live_unreal_acceptance": "pending",
    }
    output = directory / "scene.json"
    with output.open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, allow_nan=False)
    return {
        "manifest_path": str(output),
        "instances": len(instances),
        "mesh_assets": len(exported),
        "live_unreal_acceptance": "pending",
        "basis_control": control,
    }
