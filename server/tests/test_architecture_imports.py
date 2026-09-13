"""Owned geometry fixtures: units, ambiguity, immutable sources and promotion."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from tee.architecture.imports import inspect_source, promotion, propose, verify_candidate_source
from tee.architecture.model import ArchitectureError, Document


def wall_scan(path: Path, *, unit_scale: float = 1.0, origin: float = 0.0) -> Path:
    points = (
        np.array(
            [
                [x + origin, 50, z]
                for x in np.linspace(0, 4000, 31)
                for z in np.linspace(0, 2800, 29)
            ]
        )
        / unit_scale
    )
    np.savetxt(path, points)
    return path


def candidate(path: Path) -> dict:
    source = inspect_source(wall_scan(path), units="mm")
    return propose(source, tolerance_mm=1)["candidates"][0]


def test_unit_frame_origin_shift_and_bounded_json(tmp_path):
    path = wall_scan(tmp_path / "scan.xyz", unit_scale=1000, origin=600_000_000)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    transform = [[0, -1, 0, 120], [1, 0, 0, -300], [0, 0, 1, 2000], [0, 0, 0, 1]]
    source = inspect_source(path, units="m", transform=transform, max_points=200)
    assert source["sample_count"] == 200
    assert source["bounds_mm"][0][0] == pytest.approx(70)
    assert source["bounds_mm"][0][1] == pytest.approx(600_000_000 - 300)
    assert source["local_bounds_mm"][1][1] < 4000
    assert source["source_units"] == "m" and source["units"] == "mm"
    assert len(json.dumps(source, allow_nan=False)) < 3000
    assert source["sha256"] == before == hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("units", [None, "cm3", ""])
def test_units_are_never_guessed(tmp_path, units):
    with pytest.raises(ArchitectureError, match="units"):
        inspect_source(wall_scan(tmp_path / "scan.xyz"), units=units)


@pytest.mark.parametrize(
    "transform",
    [
        np.zeros((4, 4)).tolist(),
        [[1]],
        [[1, 0, 0, float("nan")], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
        [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 1, 1]],
    ],
)
def test_transform_must_be_finite_affine_invertible(tmp_path, transform):
    with pytest.raises(ArchitectureError, match="transform"):
        inspect_source(wall_scan(tmp_path / "scan.xyz"), units="mm", transform=transform)


def test_measured_wall_requires_reviewed_dimensions_and_can_enter_model(tmp_path):
    proposed = candidate(tmp_path / "wall.xyz")
    assert proposed["kind"] == "wall"
    assert proposed["measurement"]["rms_mm"] < 1e-8
    assert proposed["dimensions"]["observed_length_mm"] == pytest.approx(4000)
    assert "concealed_thickness_unknown" in proposed["uncertainty"]
    with pytest.raises(ArchitectureError, match="height"):
        promotion(proposed, "ground", {})
    with pytest.raises(ArchitectureError, match="centreline_offset"):
        promotion(proposed, "ground", {"height": 2800, "thickness": 200})
    op = promotion(
        proposed,
        "ground",
        {"height": 2800, "thickness": 200, "centreline_offset_mm": -100, "id": "wall"},
    )
    assert op["entity"]["start"][1] == pytest.approx(-50)
    assert "fire_rating" not in op["entity"]
    model = Document.create("Scan fixture")
    model.apply(
        [
            {
                "op": "create",
                "entity": {
                    "id": "ground",
                    "kind": "storey",
                    "name": "Ground",
                    "elevation": 0,
                    "height": 3000,
                },
            },
            op,
        ]
    )
    assert model.to_dict()["entities"]["wall"]["provenance"]["status"] == "explicitly_promoted"
    retained = model.to_dict()["entities"]["wall"]["provenance"]
    assert retained["reviewed_measurement"] == proposed["measurement"]
    assert retained["observed_bounds_mm"] == proposed["bounds_mm"]
    assert retained["uncertainty"] == proposed["uncertainty"]
    assert retained["source_precision"]["source_quantization"] == "unknown"
    assert len(json.dumps(retained)) < 4000


def test_noisy_two_planes_report_residuals_and_unclassified_points(tmp_path):
    rng = np.random.default_rng(82)
    a = np.array([[x, 0, z] for x in np.linspace(0, 4000, 20) for z in np.linspace(0, 2800, 20)])
    b = np.array([[0, y, z] for y in np.linspace(0, 3000, 20) for z in np.linspace(0, 2800, 20)])
    points = np.vstack(
        [
            a + rng.normal(0, 0.1, a.shape),
            b + rng.normal(0, 0.1, b.shape),
            rng.uniform(100, 2500, (20, 3)),
        ]
    )
    path = tmp_path / "walls.xyz"
    np.savetxt(path, points)
    result = propose(inspect_source(path, units="mm"), tolerance_mm=1)
    walls = [c for c in result["candidates"] if c["kind"] == "wall"]
    assert len(walls) == 2
    assert all(0 < c["measurement"]["p95_mm"] <= 1 for c in walls)
    assert 0 < result["unclassified_fraction"] < 0.1


def test_line_and_tiny_cloud_cannot_become_walls(tmp_path):
    for count in (3, 100):
        path = tmp_path / f"line-{count}.xyz"
        np.savetxt(path, [[i, 0, 0] for i in range(count)])
        result = propose(inspect_source(path, units="mm"), tolerance_mm=0.1)
        assert result["status"] == "not_verified"
        assert result["candidates"] == []


def test_slanted_surface_is_not_silently_straightened_into_a_wall(tmp_path):
    path = tmp_path / "slanted.xyz"
    np.savetxt(
        path, [[x, z * 0.01, z] for x in np.linspace(0, 4000, 20) for z in np.linspace(0, 2800, 20)]
    )
    result = propose(inspect_source(path, units="mm"), tolerance_mm=1)
    assert result["candidates"][0]["kind"] == "plane"


def test_changed_source_refuses_proposal_and_promotion(tmp_path):
    path = wall_scan(tmp_path / "wall.xyz")
    source = inspect_source(path, units="mm")
    selected = propose(source, tolerance_mm=1)["candidates"][0]
    path.write_text(path.read_text() + "4000 50 3000\n")
    with pytest.raises(ArchitectureError, match="identity changed"):
        propose(source, tolerance_mm=1)
    with pytest.raises(ArchitectureError, match="source changed"):
        promotion(selected, "ground", {"height": 2800, "thickness": 200, "centreline_offset_mm": 0})


@pytest.mark.parametrize("extension", ["obj", "stl", "glb"])
def test_real_mesh_reader_fits_surfaces_of_sparse_vertex_box(tmp_path, extension):
    import trimesh

    path = tmp_path / f"box.{extension}"
    trimesh.creation.box(extents=(4, 0.2, 2.8)).export(path)
    result = propose(inspect_source(path, units="m", max_points=4000), tolerance_mm=1)
    assert any(c["kind"] == "wall" for c in result["candidates"])
    assert all(c["measurement"]["max_mm"] <= 1 for c in result["candidates"])


@pytest.mark.parametrize("extension", ["las", "laz"])
def test_chunked_las_round_trip_preserves_large_origin_and_precision(tmp_path, extension):
    import laspy

    path = tmp_path / f"scan.{extension}"
    header = laspy.LasHeader(point_format=3, version="1.2")
    header.scales = [0.0001] * 3
    header.offsets = [600000, 3000000, 0]
    cloud = laspy.LasData(header)
    cloud.x = 600000 + np.linspace(0, 4, 100)
    cloud.y = np.full(100, 3000000.05)
    cloud.z = np.linspace(0, 2.8, 100)
    cloud.write(path)
    source = inspect_source(path, units="m", max_points=30)
    assert source["sample_count"] == 30
    assert source["bounds_mm"][0][0] == pytest.approx(600_000_000)
    assert source["precision"]["quantization_bound_mm"] == pytest.approx([0.05] * 3)


def unreal_manifest(tmp_path):
    import trimesh

    mesh = tmp_path / "wall.obj"
    trimesh.creation.box(extents=(4, 0.2, 2.8)).export(mesh)
    manifest = {
        "schema": "tee-unreal-geometry/1",
        "frame": "right-handed-z-up",
        "transform_units": "mm",
        "instances": [
            {
                "actor": "Room",
                "component": "Wall",
                "instance": "0",
                "mesh": mesh.name,
                "units": "m",
                "transform": [[1, 0, 0, 4000], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            }
        ],
    }
    path = tmp_path / "scene.json"
    path.write_text(json.dumps(manifest))
    return path, mesh, manifest


def test_unreal_manifest_applies_instance_frame_and_preserves_dependency_hash(tmp_path):
    path, mesh, _ = unreal_manifest(tmp_path)
    source = inspect_source(path, units="mm", max_points=2000)
    assert source["bounds_mm"][0][0] == pytest.approx(2000, abs=1)
    assert source["live_unreal_verified"] is False
    selected = next(c for c in propose(source, tolerance_mm=1)["candidates"] if c["kind"] == "wall")
    verify_candidate_source(selected)
    mesh.write_text(mesh.read_text() + "\n# changed\n")
    with pytest.raises(ArchitectureError, match="mesh source changed"):
        verify_candidate_source(selected)
    with pytest.raises(ArchitectureError, match="identity changed"):
        propose(source, tolerance_mm=1)


def test_unreal_manifest_refuses_traversal_and_missing_frame(tmp_path):
    path, _, manifest = unreal_manifest(tmp_path)
    bad = copy.deepcopy(manifest)
    bad["instances"][0]["mesh"] = "../outside.obj"
    (tmp_path.parent / "outside.obj").write_text("v 0 0 0\n")
    path.write_text(json.dumps(bad))
    with pytest.raises(ArchitectureError, match="inside"):
        inspect_source(path, units="mm")
    del manifest["frame"]
    path.write_text(json.dumps(manifest))
    with pytest.raises(ArchitectureError, match="right-handed"):
        inspect_source(path, units="mm")


def test_malformed_and_oversized_sources_fail_cheaply(tmp_path, monkeypatch):
    path = tmp_path / "bad.xyz"
    path.write_text("0 0 0\n1 nan 1\n2 2 2\n")
    with pytest.raises(ArchitectureError, match="non-finite"):
        inspect_source(path, units="mm")
    path.write_text("0 " * 5000)
    with pytest.raises(ArchitectureError, match="8192"):
        inspect_source(path, units="mm")
    with pytest.raises(ArchitectureError, match="max_points"):
        inspect_source(path, units="mm", max_points=200001)


def test_malformed_manifest_and_huge_finite_coordinates_refuse_before_arithmetic(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("[]")
    with pytest.raises(ArchitectureError, match="JSON object"):
        inspect_source(path, units="mm")
    path = tmp_path / "large.xyz"
    path.write_text("1e308 0 0\n1e308 1 0\n1e308 0 1\n")
    with pytest.raises(ArchitectureError, match="origin-shift"):
        inspect_source(path, units="m")
    wall_scan(path)
    transform = np.eye(4).tolist()
    transform[0][0] = 1e308
    with pytest.raises(ArchitectureError, match="transform"):
        inspect_source(path, units="mm", transform=transform)


def test_manifest_cannot_bypass_primary_link_policy(tmp_path):
    import os

    path, mesh, manifest = unreal_manifest(tmp_path)
    linked = tmp_path / "linked.obj"
    os.link(mesh, linked)
    manifest["instances"][0]["mesh"] = linked.name
    path.write_text(json.dumps(manifest))
    with pytest.raises(ArchitectureError, match="regular file"):
        inspect_source(path, units="mm")
    linked.unlink()
    linked.symlink_to(mesh)
    with pytest.raises(ArchitectureError, match="symbolic links"):
        inspect_source(path, units="mm")


def test_trimesh_cannot_create_an_ambient_filesystem_resolver(tmp_path, monkeypatch):
    import trimesh

    path = tmp_path / "box.glb"
    trimesh.creation.box().export(path)

    def forbidden(*args, **kwargs):
        raise AssertionError("Reader attempted ambient material or buffer access")

    monkeypatch.setattr(trimesh.resolvers, "FilePathResolver", forbidden)
    assert inspect_source(path, units="m")["sample_count"] > 0


def test_unreal_helper_requires_controlled_basis_before_importing_unreal(tmp_path):
    from tee.architecture.unreal_export import export_selected

    identity = np.eye(4).tolist()
    with pytest.raises(ValueError, match="four measured"):
        export_selected(
            tmp_path / "export",
            mesh_units="cm",
            mesh_to_unreal_mm=identity,
            unreal_world_to_target_mm=identity,
            basis_controls=[],
            basis_evidence="owned-fixture",
        )
    controls = [
        {"mesh": p, "unreal_mm": [10 * x for x in p]}
        for p in ([0, 0, 0], [100, 0, 0], [0, 100, 0], [0, 0, 100])
    ]
    controls[-1]["unreal_mm"] = [0, 0, 900]
    with pytest.raises(ValueError, match="disagrees"):
        export_selected(
            tmp_path / "export",
            mesh_units="cm",
            mesh_to_unreal_mm=identity,
            unreal_world_to_target_mm=identity,
            basis_controls=controls,
            basis_evidence="owned-fixture",
        )
    assert not (tmp_path / "export").exists()


def test_unreal_helper_stub_contract_preserves_instance_positions_without_live_claim(
    tmp_path, monkeypatch
):
    import sys
    from types import SimpleNamespace

    import trimesh
    from tee.architecture.unreal_export import export_selected

    class Vector:
        def __init__(self, x, y, z):
            self.x, self.y, self.z = x, y, z

    class Transform:
        def __init__(self, offset):
            self.offset = offset

        def transform_location(self, point):
            # Real affine transform fixture: rotate 90 degrees, scale X by two.
            return Vector(-point.y + self.offset, 2 * point.x + 20, point.z + 30)

    class Mesh:
        def get_path_name(self):
            return "/Game/FixtureCube"

    class InstancedStaticMeshComponent:
        def get_editor_property(self, key):
            assert key == "static_mesh"
            return Mesh()

        def get_path_name(self):
            return "/Game/FixtureActor.Instances"

        def get_instance_count(self):
            return 2

        def get_instance_transform(self, index, world_space=False):
            assert world_space is True
            return Transform(100 + 500 * index)

    class Actor:
        def get_path_name(self):
            return "/Game/FixtureActor"

        def get_components_by_class(self, cls):
            return [InstancedStaticMeshComponent()]

    class Task:
        def set_editor_property(self, key, value):
            setattr(self, key, value)

    def export(task):
        assert task.automated and not task.prompt and not task.replace_identical
        trimesh.creation.box(extents=(100, 100, 100)).export(task.filename)
        return True

    api = SimpleNamespace(
        Vector=Vector,
        InstancedStaticMeshComponent=InstancedStaticMeshComponent,
        StaticMeshComponent=object,
        EditorActorSubsystem=object,
        get_editor_subsystem=lambda _: SimpleNamespace(get_selected_level_actors=lambda: [Actor()]),
        AssetExportTask=Task,
        StaticMeshExporterOBJ=object,
        Exporter=SimpleNamespace(run_asset_export_task=export),
    )
    monkeypatch.setitem(sys.modules, "unreal", api)
    identity = np.eye(4).tolist()
    target = np.diag([1, -1, 1, 1]).tolist()
    controls = [
        {"mesh": p, "unreal_mm": [10 * x for x in p]}
        for p in ([0, 0, 0], [100, 0, 0], [0, 100, 0], [0, 0, 100])
    ]
    result = export_selected(
        tmp_path / "export",
        mesh_units="cm",
        mesh_to_unreal_mm=identity,
        unreal_world_to_target_mm=target,
        basis_controls=controls,
        basis_evidence="owned stub fixture; no live Unreal",
    )
    assert result["instances"] == 2 and result["mesh_assets"] == 1
    assert result["live_unreal_acceptance"] == "pending"
    source = inspect_source(result["manifest_path"], units="mm", max_points=4000)
    assert source["bounds_mm"][0] == pytest.approx([500, -1200, -200], abs=2)
    assert source["bounds_mm"][1] == pytest.approx([6500, 800, 800], abs=2)
    with pytest.raises(FileExistsError):
        export_selected(
            tmp_path / "export",
            mesh_units="cm",
            mesh_to_unreal_mm=identity,
            unreal_world_to_target_mm=target,
            basis_controls=controls,
            basis_evidence="owned stub fixture; no live Unreal",
        )
