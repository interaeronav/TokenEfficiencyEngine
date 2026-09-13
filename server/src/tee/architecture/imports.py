"""Bounded reference geometry, measured candidates, and explicit wall promotion.

No source is modified. Inspection returns JSON metadata, never point arrays;
proposal reopens the recorded source and verifies its identity. Meshes and scans
remain references until a person supplies the missing construction dimensions.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

UNITS = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4, "ft": 304.8}
MAX_POINTS = 200_000
MAX_SOURCE_BYTES = 512 * 1024 * 1024
MAX_MESH_BYTES = 32 * 1024 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_INSTANCES = 128
SCHEMA = "tee-architecture-reference/1"
UNREAL_SCHEMA = "tee-unreal-geometry/1"


def _error(message: str) -> Exception:
    from .model import ArchitectureError

    return ArchitectureError(message)


def _number(value: Any, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _error(f"{label} must be a finite number.")
    if abs(value) > 1e15:
        raise _error(f"{label} must be within 1e15.")
    value = float(value)
    if not math.isfinite(value) or (positive and value <= 0):
        raise _error(f"{label} must be finite{' and positive' if positive else ''}.")
    return value


def _matrix(value: Any = None) -> Any:
    import numpy as np

    if value is None:
        return np.eye(4, dtype=np.float64)
    try:
        matrix = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError):
        raise _error("transform must be a finite affine 4x4 matrix.") from None
    if (
        matrix.shape != (4, 4)
        or not np.isfinite(matrix).all()
        or abs(matrix).max() > 1e12
        or not np.allclose(matrix[3], [0, 0, 0, 1], rtol=0, atol=1e-12)
        or abs(float(np.linalg.det(matrix[:3, :3]))) < 1e-12
    ):
        raise _error("transform must be an invertible finite affine 4x4 matrix within 1e12.")
    return matrix


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dependency_hash(instances: list[dict[str, Any]]) -> str:
    identities = [
        {"mesh": instance["mesh"], "sha256": instance["sha256"]} for instance in instances
    ]
    return hashlib.sha256(
        json.dumps(identities, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _file(path: Path, limit: int = MAX_SOURCE_BYTES) -> Path:
    path = path.expanduser().absolute()
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise _error("Reference paths must not contain symbolic links.")
    path = path.expanduser().resolve(strict=True)
    if not path.is_file() or path.stat().st_size > limit or path.stat().st_nlink != 1:
        raise _error(f"Source must be a regular file no larger than {limit} bytes.")
    return path


def _limit(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 3 <= value <= MAX_POINTS:
        raise _error(f"max_points must be an integer from 3 to {MAX_POINTS}.")
    return value


def _select(points: Any, limit: int) -> Any:
    import numpy as np

    if len(points) <= limit:
        return points
    return points[np.linspace(0, len(points) - 1, limit, dtype=np.int64)]


def _text_points(path: Path, limit: int) -> tuple[Any, dict[str, Any]]:
    """Two streaming passes: evenly select valid rows without a growing buffer."""
    import numpy as np

    def rows() -> Any:
        with path.open("r", encoding="utf-8") as handle:
            while True:
                line = handle.readline(8193)
                if not line:
                    return
                if len(line) > 8192:
                    raise _error("XYZ row exceeds 8192 characters; export plain XYZ triples.")
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                fields = line.split()
                if len(fields) < 3:
                    raise _error("XYZ requires three finite coordinates per data row.")
                try:
                    point = [float(x) for x in fields[:3]]
                except ValueError:
                    raise _error("XYZ requires three finite coordinates per data row.") from None
                if not all(math.isfinite(x) for x in point):
                    raise _error(
                        "Source contains non-finite coordinates; repair the source export."
                    )
                yield point

    count = sum(1 for _ in rows())
    if count < 3:
        raise _error("Source needs at least three finite points.")
    indices = iter(np.linspace(0, count - 1, min(count, limit), dtype=np.int64))
    wanted = next(indices, None)
    selected = []
    for index, point in enumerate(rows()):
        if index == wanted:
            selected.append(point)
            wanted = next(indices, None)
    return np.asarray(selected, dtype=np.float64), {
        "point_count": count,
        "precision": {"encoding": "text", "source_quantization": "unknown"},
    }


def _las_points(path: Path, limit: int) -> tuple[Any, dict[str, Any]]:
    import laspy
    import numpy as np

    with laspy.open(path, read_evlrs=False) as reader:
        scales = np.asarray(reader.header.scales)
        offsets = np.asarray(reader.header.offsets)
        if (
            not np.isfinite(scales).all()
            or not np.isfinite(offsets).all()
            or (scales <= 0).any()
            or (scales > 1e15).any()
            or (abs(offsets) > 1e15).any()
        ):
            raise _error(
                "LAS/LAZ scales and offsets must be finite within source coordinate bounds."
            )
        count = int(reader.header.point_count)
        if count < 3 or count > 100_000_000:
            raise _error("LAS/LAZ needs 3-100000000 points; split larger scans first.")
        indices = np.linspace(0, count - 1, min(count, limit), dtype=np.int64)
        points = np.empty((len(indices), 3), dtype=np.float64)
        cursor = offset = 0
        for chunk in reader.chunk_iterator(50_000):
            end = int(np.searchsorted(indices, offset + len(chunk), side="left"))
            local = indices[cursor:end] - offset
            if len(local):
                points[cursor:end, 0] = np.asarray(chunk.x)[local]
                points[cursor:end, 1] = np.asarray(chunk.y)[local]
                points[cursor:end, 2] = np.asarray(chunk.z)[local]
            cursor = end
            offset += len(chunk)
        if offset != count or cursor != len(indices):
            raise _error("LAS/LAZ point count disagrees with its header; repair the export.")
        precision = {
            "encoding": "scaled_integer",
            "source_quantization": [float(v) for v in reader.header.scales],
            "source_offsets": [float(v) for v in reader.header.offsets],
        }
    return points, {"point_count": count, "precision": precision}


def _mesh_points(path: Path, limit: int) -> tuple[Any, dict[str, Any]]:
    import numpy as np
    import trimesh

    _file(path, MAX_MESH_BYTES)
    # An explicit empty resolver prevents external material/buffer reads.
    # resolver=None is unsafe here: trimesh derives FilePathResolver from .name.
    with path.open("rb") as handle:
        mesh = trimesh.load(
            handle,
            file_type=path.suffix[1:].lower(),
            process=False,
            force="scene",
            skip_materials=True,
            resolver={},
        )
    if len(mesh.graph.nodes_geometry) > MAX_INSTANCES:
        raise _error(f"Mesh has more than {MAX_INSTANCES} instances; split the export.")
    parts = []
    total = 0
    nodes = sorted(mesh.graph.nodes_geometry)
    per_node = max(3, limit // max(1, len(nodes)))
    for node in nodes:
        transform, name = mesh.graph[node]
        vertices = np.asarray(mesh.geometry[name].vertices, dtype=np.float64)
        if vertices.ndim != 2 or vertices.shape[1] != 3:
            raise _error("Mesh contains no usable XYZ vertices.")
        if not np.isfinite(vertices).all() or abs(vertices).max(initial=0) > 1e15:
            raise _error("Mesh coordinates must be finite and within 1e15 source units.")
        total += len(vertices)
        if total > 4_000_000:
            raise _error("Mesh exceeds 4000000 instanced vertices; split the export.")
        geometry = mesh.geometry[name]
        if hasattr(geometry, "faces") and len(geometry.faces):
            # A box has only eight vertices, but its faces provide real planar
            # support. Sampling is deterministic and area weighted in local space.
            vertices, _ = trimesh.sample.sample_surface(geometry, min(per_node, 20_000), seed=82)
        else:
            vertices = _select(vertices, per_node)
        matrix = _matrix(transform)
        parts.append(vertices @ matrix[:3, :3].T + matrix[:3, 3])
    if not parts or total < 3:
        raise _error("Mesh needs at least three vertices.")
    return _select(np.vstack(parts), limit), {
        "point_count": total,
        "precision": {"encoding": "mesh_vertices", "source_quantization": "unknown"},
        "mesh_sampling": "deterministic_local_area_surface_sample_else_vertices",
    }


def _manifest_points(path: Path, limit: int) -> tuple[Any, dict[str, Any]]:
    import numpy as np

    _file(path, MAX_MANIFEST_BYTES)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise _error("Unreal manifest must be a JSON object with schema and instances.")
    instances = manifest.get("instances")
    if manifest.get("schema") != UNREAL_SCHEMA or not isinstance(instances, list):
        raise _error(f"Unreal manifest needs schema {UNREAL_SCHEMA} and instances.")
    if not 1 <= len(instances) <= MAX_INSTANCES:
        raise _error(f"Unreal manifest needs 1-{MAX_INSTANCES} instances.")
    if manifest.get("frame") != "right-handed-z-up" or manifest.get("transform_units") != "mm":
        raise _error("Unreal manifest must declare right-handed-z-up and transform_units mm.")
    parts, identities = [], []
    total = 0
    per_instance = max(3, limit // len(instances))
    for instance in instances:
        if not isinstance(instance, dict):
            raise _error("Each Unreal instance must be an object.")
        relative = instance.get("mesh")
        if not isinstance(relative, str) or Path(relative).is_absolute():
            raise _error("Unreal mesh paths must be relative to the manifest directory.")
        child = _file(path.parent / relative, MAX_MESH_BYTES)
        if not child.is_relative_to(path.parent):
            raise _error("Unreal mesh paths must remain inside the manifest directory.")
        if child.suffix.lower() not in {".obj", ".stl", ".glb"}:
            raise _error("Unreal instances require OBJ, STL or GLB mesh exports.")
        unit = instance.get("units")
        if unit not in UNITS or "transform" not in instance:
            raise _error("Each Unreal instance needs explicit units and a 4x4 transform.")
        for name in ("actor", "component", "instance"):
            if not isinstance(instance.get(name), str) or not 1 <= len(instance[name]) <= 256:
                raise _error(f"Each Unreal instance needs a bounded {name} identifier.")
        identity = _hash(child)
        points, metadata = _mesh_points(child, per_instance)
        if _hash(child) != identity:
            raise _error("A referenced mesh changed during inspection; retry a stable export.")
        matrix = _matrix(instance["transform"])
        points = points * UNITS[unit]
        parts.append(points @ matrix[:3, :3].T + matrix[:3, 3])
        total += metadata["point_count"]
        identities.append(
            {
                "mesh": relative,
                "sha256": identity,
                "units": unit,
                "transform": matrix.tolist(),
                **{name: instance[name] for name in ("actor", "component", "instance")},
            }
        )
    return _select(np.vstack(parts), limit), {
        "point_count": total,
        "instances": identities,
        "precision": {"encoding": "instanced_mesh", "source_quantization": "unknown"},
        "mesh_sampling": "deterministic_local_area_surface_sample_per_instance",
        "live_unreal_verified": False,
    }


def _read(path: Path, limit: int) -> tuple[Any, dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix in {".xyz", ".asc", ".txt"}:
        return _text_points(path, limit)
    if suffix in {".las", ".laz"}:
        return _las_points(path, limit)
    if suffix in {".obj", ".stl", ".glb"}:
        return _mesh_points(path, limit)
    if suffix == ".json":
        return _manifest_points(path, limit)
    raise _error("Use XYZ, LAS/LAZ, OBJ, STL, GLB or a tee-unreal-geometry/1 JSON manifest.")


def _load(path: Path, units: str, transform: Any, limit: int) -> tuple[Any, dict[str, Any]]:
    import numpy as np

    if units not in UNITS:
        raise _error("Declare units explicitly: mm, cm, m, in or ft.")
    matrix = _matrix(transform)
    identity = _hash(path)
    points, metadata = _read(path, limit)
    if path.suffix.lower() == ".json" and units != "mm":
        raise _error("Unreal manifest units must be mm; each instance declares its source units.")
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise _error("Source contains non-finite coordinates; repair the source export.")
    if abs(points).max(initial=0) > 1e15:
        raise _error("Source coordinates exceed 1e15; origin-shift the export before inspection.")
    points = points * UNITS[units]
    points = points @ matrix[:3, :3].T + matrix[:3, 3]
    if not np.isfinite(points).all() or abs(points).max() > 1e15:
        raise _error("Transformed coordinates are non-finite or exceed 1e15 mm.")
    if _hash(path) != identity:
        raise _error("Source changed during inspection; retry a stable export.")
    metadata.update({"sha256": identity, "transform": matrix.tolist()})
    return points, metadata


def inspect_source(
    path: str | Path,
    *,
    units: str,
    transform: Any = None,
    max_points: int = MAX_POINTS,
) -> dict[str, Any]:
    """Inspect source without mutating it. Transform translation is always mm."""
    import numpy as np

    limit = _limit(max_points)
    try:
        source = _file(Path(path))
        points, metadata = _load(source, units, transform, limit)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        # ArchitectureError is a ValueError in the shared model; preserve it.
        from .model import ArchitectureError

        if isinstance(exc, ArchitectureError):
            raise
        raise _error(
            f"Cannot read reference: {type(exc).__name__}; check the file format."
        ) from None
    origin = points.mean(axis=0)
    shifted = points - origin
    precision = metadata["precision"]
    quantization = precision.get("source_quantization")
    if isinstance(quantization, list):
        transform3 = np.asarray(metadata["transform"])[:3, :3]
        precision["quantization_bound_mm"] = (
            abs(transform3) @ (np.asarray(quantization) * UNITS[units] / 2)
        ).tolist()
    return {
        "schema": SCHEMA,
        "source_path": str(source),
        "format": source.suffix[1:].lower(),
        "source_units": units,
        "units": "mm",
        "frame": "right-handed-z-up",
        "max_points": limit,
        "sample_count": len(points),
        "sampling": metadata.get("mesh_sampling", "deterministic_even_row_sample"),
        "bounds_mm": [points.min(axis=0).tolist(), points.max(axis=0).tolist()],
        "bounds_scope": "sampled_points",
        "origin_shift_mm": origin.tolist(),
        "local_bounds_mm": [shifted.min(axis=0).tolist(), shifted.max(axis=0).tolist()],
        "numeric_resolution_mm": float(abs(np.spacing(points)).max()),
        "classification": "reference_only",
        **metadata,
    }


def propose(
    source: dict[str, Any],
    *,
    tolerance_mm: float,
    wall_height: float | None = None,
    thickness: float | None = None,
) -> dict[str, Any]:
    """Measure planar support; do not infer hidden construction attributes."""
    import numpy as np

    tolerance = _number(tolerance_mm, "tolerance_mm", positive=True)
    if wall_height is not None:
        wall_height = _number(wall_height, "wall_height", positive=True)
    if thickness is not None:
        thickness = _number(thickness, "thickness", positive=True)
    if not isinstance(source, dict) or source.get("schema") != SCHEMA:
        raise _error("Pass the reference returned by inspect_source.")
    path = _file(Path(source["source_path"]))
    points, metadata = _load(
        path, source["source_units"], source["transform"], _limit(source["max_points"])
    )
    if metadata["sha256"] != source.get("sha256") or metadata.get("instances") != source.get(
        "instances"
    ):
        raise _error("Reference identity changed; inspect the source again before proposing.")
    origin = points.mean(axis=0)
    local = points - origin
    # RANSAC cost is capped independently of a caller's sample budget.
    fit_points = _select(local, 20_000)
    remaining = np.arange(len(fit_points))
    rng = np.random.default_rng(82)
    candidates = []
    min_support = max(8, math.ceil(len(fit_points) * 0.03))
    if len(fit_points) < 8:
        return {
            "source_sha256": metadata["sha256"],
            "candidates": [],
            "status": "not_verified",
            "reason": "insufficient_surface_support",
            "unclassified_fraction": 1.0,
        }
    for _ in range(12):
        if len(remaining) < min_support:
            break
        active = fit_points[remaining]
        best = None
        best_count = 0
        for _ in range(96):
            trio = active[rng.choice(len(active), 3, replace=False)]
            normal = np.cross(trio[1] - trio[0], trio[2] - trio[0])
            length = float(np.linalg.norm(normal))
            if length < tolerance * tolerance:
                continue
            normal /= length
            mask = abs((active - trio[0]) @ normal) <= tolerance
            support = int(mask.sum())
            if support > best_count:
                best, best_count = mask, support
        if best is None or best_count < min_support:
            break
        inliers = active[best]
        center = inliers.mean(axis=0)
        _, singular, vectors = np.linalg.svd(inliers - center, full_matrices=False)
        # A line can fit infinitely many planes and must never become a wall.
        if len(singular) < 3 or singular[1] < tolerance * math.sqrt(len(inliers)):
            remaining = remaining[~best]
            continue
        normal = vectors[2]
        largest = int(np.argmax(abs(normal)))
        if normal[largest] < 0:
            normal = -normal
        distances = abs((active - center) @ normal)
        best = distances <= tolerance
        inliers = active[best]
        residuals = distances[best]
        world = inliers + origin
        lower, upper = world.min(axis=0), world.max(axis=0)
        observed_height = float(upper[2] - lower[2])
        vertical = abs(float(normal[2])) <= 0.02 and (
            abs(float(normal[2])) * observed_height <= tolerance
        )
        horizontal = abs(float(normal[2])) >= 0.9998
        cid = (
            "candidate_"
            + hashlib.sha256(
                (
                    metadata["sha256"] + json.dumps([normal.tolist(), (center + origin).tolist()])
                ).encode()
            ).hexdigest()[:16]
        )
        candidate: dict[str, Any] = {
            "id": cid,
            "kind": "wall" if vertical else "plane",
            "units": "mm",
            "classification": "vertical_surface"
            if vertical
            else "horizontal_surface"
            if horizontal
            else "inclined_surface",
            "plane": {"normal": normal.tolist(), "point_mm": (center + origin).tolist()},
            "bounds_mm": [lower.tolist(), upper.tolist()],
            "dimensions": {"observed_height_mm": observed_height},
            "measurement": {
                "support_points": len(inliers),
                "sample_points": len(fit_points),
                "support_fraction": len(inliers) / len(fit_points),
                "rms_mm": float(np.sqrt(np.mean(residuals**2))),
                "p95_mm": float(np.quantile(residuals, 0.95)),
                "max_mm": float(residuals.max()),
                "tolerance_mm": tolerance,
            },
            "uncertainty": [
                "sampled_surface_only",
                "concealed_thickness_unknown",
                "construction_role_unknown",
                "observed_extent_may_be_occluded",
                "centreline_offset_requires_review",
            ],
            "provenance": {
                "source_sha256": metadata["sha256"],
                "source_path": str(path),
                "source_units": source["source_units"],
                "transform": source["transform"],
                "method": "deterministic-ransac-svd/1",
                "origin_shift_mm": origin.tolist(),
                "source_precision": copy.deepcopy(source.get("precision", {})),
                "source_sampling": source.get("sampling"),
                "source_sample_budget": source["max_points"],
                "candidate_id": cid,
                "status": "proposed_not_authored",
                "dependency_sha256": _dependency_hash(metadata.get("instances", [])),
            },
        }
        if vertical:
            tangent = np.array([-normal[1], normal[0], 0.0])
            tangent /= np.linalg.norm(tangent)
            along = (inliers - center) @ tangent
            start = center + origin + float(along.min()) * tangent
            end = center + origin + float(along.max()) * tangent
            candidate["surface_line_mm"] = [start[:2].tolist(), end[:2].tolist()]
            candidate["dimensions"]["observed_length_mm"] = float(along.max() - along.min())
            candidate["required_for_promotion"] = [
                "storey",
                "height",
                "thickness",
                "centreline_offset_mm",
            ]
            candidate["declared_dimensions"] = {
                key: value
                for key, value in (("height", wall_height), ("thickness", thickness))
                if value is not None
            }
        candidates.append(candidate)
        remaining = remaining[~best]
    return {
        "source_sha256": metadata["sha256"],
        "candidates": candidates,
        "status": "review_required" if candidates else "not_verified",
        "reason": "surface_candidates_require_explicit_promotion"
        if candidates
        else "no_supported_plane",
        "unclassified_fraction": len(remaining) / len(fit_points),
        "coverage_scope": "sample_support_fraction_not_building_completeness",
    }


def verify_candidate_source(candidate: dict[str, Any]) -> None:
    """Recheck all immutable source identities before accepting a stored proposal."""
    provenance = candidate.get("provenance", {})
    try:
        path = _file(Path(provenance["source_path"]))
        if _hash(path) != provenance["source_sha256"]:
            raise _error("Candidate source changed; inspect and propose again.")
        instances = []
        if path.suffix.lower() == ".json":
            _file(path, MAX_MANIFEST_BYTES)
            instances = json.loads(path.read_text(encoding="utf-8"))["instances"]
        if not isinstance(instances, list) or len(instances) > MAX_INSTANCES:
            raise _error("Candidate source identities are invalid; propose again.")
        identities = []
        for instance in instances:
            relative = Path(instance["mesh"])
            if relative.is_absolute():
                raise _error("Candidate mesh paths must be relative; propose again.")
            child = _file(path.parent / relative, MAX_MESH_BYTES)
            if not child.is_relative_to(path.parent):
                raise _error("Candidate mesh paths must remain inside the manifest directory.")
            identities.append({"mesh": instance["mesh"], "sha256": _hash(child)})
        if _dependency_hash(identities) != provenance.get("dependency_sha256"):
            raise _error("Candidate mesh source changed; inspect and propose again.")
    except (OSError, KeyError, TypeError):
        raise _error("Candidate source is unavailable; inspect and propose again.") from None


def promotion(candidate: dict[str, Any], storey: str, overrides: dict[str, Any]) -> dict[str, Any]:
    """Create one reviewed wall operation; the model validates host and geometry."""
    if not isinstance(candidate, dict) or candidate.get("kind") != "wall":
        raise _error("Only reviewed vertical wall candidates can be promoted.")
    verify_candidate_source(candidate)
    if not isinstance(storey, str) or not storey:
        raise _error("Choose a destination storey before promotion.")
    if not isinstance(overrides, dict):
        raise _error(
            "Promotion overrides must supply explicit height, thickness and centreline_offset_mm."
        )
    declared = dict(candidate.get("declared_dimensions", {}))
    declared.update(overrides)
    height = _number(declared.get("height"), "height", positive=True)
    thickness = _number(declared.get("thickness"), "thickness", positive=True)
    offset = _number(declared.get("centreline_offset_mm"), "centreline_offset_mm")
    from .model import number

    # The observed surface may be occluded or begin above its actual wall base.
    # Preserve an authored storey-relative offset; never infer it from scan bounds.
    # get(..., 0) defaults only an absent field: an explicit null/bool/NaN refuses.
    base_offset = number(declared.get("base_offset", 0), "base_offset")
    base_offset_basis = (
        "authored_override"
        if "base_offset" in overrides
        else "declared_dimensions"
        if "base_offset" in candidate.get("declared_dimensions", {})
        else "storey_default_not_inferred"
    )
    normal = candidate["plane"]["normal"]
    xy_norm = math.hypot(normal[0], normal[1])
    if xy_norm < 0.99 or abs(normal[2]) > 0.02:
        raise _error("Candidate must be a vertical surface before wall promotion.")
    line = [
        [_number(point[i], "surface coordinate") + offset * normal[i] / xy_norm for i in range(2)]
        for point in candidate["surface_line_mm"]
    ]
    provenance = copy.deepcopy(candidate["provenance"])
    provenance.update(
        {
            "status": "explicitly_promoted",
            "centreline_offset_mm": offset,
            "declared_height_mm": height,
            "declared_thickness_mm": thickness,
            "base_offset_mm": base_offset,
            "base_offset_basis": base_offset_basis,
            "reviewed_measurement": copy.deepcopy(candidate.get("measurement", {})),
            "observed_bounds_mm": copy.deepcopy(candidate.get("bounds_mm")),
            "observed_plane": copy.deepcopy(candidate.get("plane")),
            "uncertainty": copy.deepcopy(candidate.get("uncertainty", [])),
        }
    )
    entity = {
        "kind": "wall",
        "name": str(overrides.get("name", f"Imported {candidate['id']}")),
        "storey": storey,
        "base_offset": base_offset,
        "start": line[0],
        "end": line[1],
        "height": height,
        "thickness": thickness,
        "provenance": provenance,
    }
    if "id" in overrides:
        entity["id"] = overrides["id"]
    return {"op": "create", "entity": entity}
