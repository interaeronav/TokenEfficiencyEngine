"""The cloud workspace: lineage, attribute carry-through, and the caps.

Every geometry-changing op mints a new cloud and records its parent, so any
step is reversible and the chain is auditable without re-reading a point.
"""

from __future__ import annotations

import numpy as np
import pytest

from tee.kernel.errors import TeeError
from tee.pointcloud.store import CloudStore, digest, spacing


@pytest.fixture
def store(tmp_path):
    return CloudStore(tmp_path)


@pytest.fixture
def points():
    rng = np.random.default_rng(3)
    return rng.uniform(0, 4, (5_000, 3))


def test_store_lives_under_the_project_state_dir(tmp_path):
    assert CloudStore(tmp_path).root == tmp_path / ".tee" / "pointcloud"


def test_mint_round_trips_the_points_exactly(store, points):
    cloud_id = store.mint(points)
    assert np.array_equal(store.points(cloud_id), points)
    assert store.meta(cloud_id)["count"] == 5_000


def test_lineage_records_the_parent_and_accumulates_the_chain(store, points):
    first = store.mint(points, op="open")
    second = store.mint(points * 2, parent=first, op="scale", extra={"factor": 2.0})
    third = store.mint(points * 2, parent=second, op="level")

    meta = store.meta(third)
    assert meta["parent"] == second
    assert [step["op"] for step in meta["chain"]] == ["open", "scale", "level"]
    assert meta["chain"][1]["factor"] == 2.0
    # the ancestors are still readable - nothing is destroyed in place
    assert len(store.points(first)) == 5_000


def test_controls_ride_the_lineage_forward(store, points):
    first = store.mint(points)
    store.update_meta(first, controls=[{"name": "wall", "measured_mm": 10.0, "true_mm": 10.0}])
    second = store.mint(points, parent=first, op="level")
    assert store.meta(second)["controls"][0]["name"] == "wall"


def test_colour_survives_a_geometry_only_transform_without_being_copied(store, points):
    colors = np.full((5_000, 3), 128, dtype=np.uint8)
    first = store.mint(points, colors=colors)
    second = store.mint(points * 1.01, parent=first, op="scale")
    assert store.meta(second)["has_colour"] is True
    assert np.array_equal(store.attr(second, "rgb"), colors)
    assert not (store.root / f"{second}.rgb.npy").exists(), "referenced, not duplicated"


def test_unknown_cloud_refuses_with_an_actionable_fix(store):
    with pytest.raises(TeeError) as exc:
        store.points("pc_nope")
    assert exc.value.code == "pc_unknown_cloud"
    assert "pc_open" in (exc.value.fix or "")


def test_an_empty_result_refuses_rather_than_minting_nothing(store):
    with pytest.raises(TeeError) as exc:
        store.mint(np.zeros((0, 3)))
    assert exc.value.code == "pc_empty_cloud"


def test_bad_shape_refuses(store):
    with pytest.raises(TeeError) as exc:
        store.mint(np.zeros((10, 2)))
    assert exc.value.code == "pc_bad_points"


def test_points_are_stored_as_float64_whatever_arrives(store):
    cloud_id = store.mint(np.ones((10, 3), dtype=np.float32))
    assert store.points(cloud_id).dtype == np.float64


def test_digest_is_numbers_only_and_bounded(points):
    out = digest(points)
    assert set(out) == {"count", "bbox_m", "size_m", "centroid_m"}
    assert len(out["bbox_m"]) == 6
    assert all(isinstance(v, (int, float)) for v in out["bbox_m"])


def test_spacing_is_positive_and_scales_with_the_cloud():
    rng = np.random.default_rng(0)
    tight = rng.uniform(0, 1, (4_000, 3))
    loose = tight * 10
    assert spacing(loose) > spacing(tight) > 0
