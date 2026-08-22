from voxkiln import fixtures, metrics
from voxkiln.repair import fill_boundary_loops, repair


def test_fast_fills_the_hole():
    # one missing icosphere face is far larger than the generator-hole
    # default threshold (3% of bbox diagonal), so raise it explicitly;
    # the threshold behavior itself is covered below
    mesh, log = repair(fixtures.holed_sphere(), level="fast", max_hole_perimeter=1.0)
    assert metrics.boundary_loop_count(mesh) == 0
    assert mesh.is_watertight
    assert any(entry["op"] == "fill_holes" for entry in log)


def test_fill_respects_perimeter_threshold():
    # a hole bigger than the threshold stays open (and honest)
    mesh, filled = fill_boundary_loops(fixtures.holed_sphere(), max_hole_perimeter=1e-6)
    assert filled == 0
    assert metrics.boundary_loop_count(mesh) == 1


def test_fill_winding_matches_surrounding_surface():
    mesh, _ = repair(fixtures.holed_sphere(), level="fast")
    assert mesh.is_winding_consistent


def test_fast_drops_degenerates():
    mesh, log = repair(fixtures.degenerate_slivers(), level="fast")
    assert metrics.degenerate_face_count(mesh) == 0
    assert any(entry["op"] == "drop_degenerate_faces" for entry in log)


def test_fast_culls_debris_component():
    mesh, log = repair(fixtures.small_debris(), level="fast")
    assert metrics.mesh_stats(mesh)["components"] == 1
    assert any(entry["op"] == "drop_small_components" for entry in log)


def test_repair_log_is_diff_not_snapshot():
    # a clean mesh produces an (almost) empty log - diffs over snapshots
    mesh, log = repair(fixtures.clean_sphere(), level="fast")
    assert mesh.is_watertight
    assert [e for e in log if "removed" in e or "loops_filled" in e] == []


def test_manifold_level_reports_status():
    _, log = repair(fixtures.nonmanifold_fin(), level="manifold")
    checks = [e for e in log if e["op"] == "manifold_check"]
    assert len(checks) == 1
    assert checks[0]["status"]


def test_unknown_level_rejected():
    import pytest

    with pytest.raises(ValueError):
        repair(fixtures.clean_sphere(), level="extreme")
