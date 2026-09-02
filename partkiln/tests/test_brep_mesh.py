"""P2a acceptance for partkiln.brep.mesh: absolute deflection, pinned hash."""

from __future__ import annotations

import time

import pytest

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

from partkiln._errors import KernelError
from partkiln.brep import fixtures, mesh, shapes

pytestmark = pytest.mark.brep


def test_f5_mesh_hash_identical_serial_and_parallel() -> None:
    t = time.perf_counter()
    serial = mesh.mesh_hash(fixtures.build_F5(), 0.05, parallel=False)
    parallel = mesh.mesh_hash(fixtures.build_F5(), 0.05, parallel=True)
    dt = time.perf_counter() - t
    assert len(serial) == 16 and serial == parallel  # undocumented in OCCT; pinned here
    assert dt < 5.0, f"two F5 meshes at 0.05 mm took {dt:.2f} s"


def test_hash_is_deterministic_and_deflection_sensitive() -> None:
    f1 = fixtures.build_F1()
    fine = mesh.mesh_hash(f1, 0.05)
    assert mesh.mesh_hash(fixtures.build_F1(), 0.05) == fine
    coarse = mesh.mesh_hash(f1, 0.3)
    assert coarse != fine  # clean=True: the coarser request is honoured, not the cached finer mesh
    coarse_count = mesh.triangle_count(f1)
    mesh.tessellate(f1, 0.05)
    assert mesh.triangle_count(f1) > coarse_count


def test_tessellate_refuses_bad_parameters() -> None:
    f1 = fixtures.build_F1()
    with pytest.raises(KernelError, match="deflection"):
        mesh.tessellate(f1, 0.0)
    with pytest.raises(KernelError, match="angular"):
        mesh.tessellate(f1, 0.1, angular=0)
    assert mesh.triangle_count(shapes.box(1, 1, 1)) == 0  # nothing before tessellate


def test_to_trimesh_is_watertight_with_outward_normals() -> None:
    f1 = fixtures.build_F1()
    tm, report = mesh.to_trimesh(f1, 0.1)
    assert report["watertight"] is True and report["faces_without_mesh"] == 0
    assert report["triangles"] == len(tm.faces) and tm.is_winding_consistent
    assert tm.volume == pytest.approx(shapes.volume(f1), rel=2e-3)  # +volume => outward winding
    assert tm.bounds.ravel().tolist() == pytest.approx([0, 0, 0, 100, 60, 10], abs=1e-6)
    block, _ = fixtures.build_F6()
    _, rep2 = mesh.to_trimesh(block, 0.05)
    assert rep2["watertight"] is True


def test_collect_applies_face_locations() -> None:
    moved = shapes.transform(fixtures.build_F1(), translation=(0, 0, 100)).shape
    mesh.tessellate(moved, 0.1)
    t = mesh.collect(moved)
    assert min(n[2] for n in t.nodes) == pytest.approx(100.0) and max(
        n[2] for n in t.nodes
    ) == pytest.approx(110.0)
    assert len(t.triangles) == mesh.triangle_count(moved)
