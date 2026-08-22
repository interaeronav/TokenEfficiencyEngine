"""Exact-count assertions on the seeded-defect fixtures (research 48 -
each expected value was verified live before being encoded here)."""

from voxkiln import fixtures, metrics


def test_clean_sphere_is_clean():
    stats = metrics.mesh_stats(fixtures.clean_sphere(), expected_topology="closed")
    assert stats["watertight"] is True
    assert stats["boundary_edges"] == 0
    assert stats["boundary_loops"] == 0
    assert stats["nonmanifold_edges"] == 0
    assert stats["degenerate_faces"] == 0
    assert stats["components"] == 1
    assert stats["euler_per_component"] == [2]
    assert stats["topology_ok"] is True


def test_holed_sphere_counts():
    stats = metrics.mesh_stats(fixtures.holed_sphere(), expected_topology="closed")
    assert stats["watertight"] is False
    assert stats["boundary_edges"] == 3
    assert stats["boundary_loops"] == 1
    assert stats["euler_per_component"] == [1]
    assert stats["topology_ok"] is False


def test_nonmanifold_fin():
    stats = metrics.mesh_stats(fixtures.nonmanifold_fin())
    assert stats["nonmanifold_edges"] == 1


def test_degenerate_slivers():
    stats = metrics.mesh_stats(fixtures.degenerate_slivers())
    assert stats["degenerate_faces"] == 2


def test_watertight_but_interpenetrating_trap():
    # watertightness alone MISSES interpenetration - the reason
    # self-intersection checking stays in the (GPL, dev-only) eval venv.
    mesh = fixtures.interpenetrating_boxes()
    stats = metrics.mesh_stats(mesh)
    assert stats["watertight"] is True
    assert stats["boundary_edges"] == 0
    assert stats["components"] == 2


def test_open_topology_is_not_a_defect():
    stats = metrics.mesh_stats(fixtures.holed_sphere(), expected_topology="open")
    assert stats["topology_ok"] is True
