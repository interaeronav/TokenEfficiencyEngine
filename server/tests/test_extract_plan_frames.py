import math

import pytest

from tee.extract.frames import FrameRegistry, fit_similarity, rss, scale_conflict
from tee.extract.plan import SCHEMA_ID, empty_plan, validate_plan, wall_length
from tee.kernel.errors import TeeError


def small_plan():
    plan = empty_plan("dwg:test:model")
    plan["levels"] = [{"index": 0, "name": "L0", "elevation_z": 0.0}]
    plan["walls"] = [
        {"id": "w1", "level": 0, "a": [0, 0], "b": [4, 0], "thickness": 0.2, "height": 2.7}
    ]
    plan["openings"] = [
        {"id": "o1", "wall": "w1", "t": 0.5, "width": 0.9, "kind": "door", "sill": 0, "head": 2.1}
    ]
    plan["rooms"] = [{"id": "r1", "level": 0, "name": "A", "polygon": [[0, 0], [4, 0], [4, 3]]}]
    return plan


def test_valid_plan_passes():
    plan = validate_plan(small_plan())
    assert plan["schema"] == SCHEMA_ID
    assert wall_length(plan["walls"][0]) == 4


def test_plan_rejections():
    for mutate, code in [
        (lambda p: p.pop("frame"), "bad_plan"),
        (lambda p: p["walls"][0].update(a=[0]), "bad_plan"),
        (lambda p: p["openings"][0].update(wall="nope"), "bad_plan"),
        (lambda p: p["openings"][0].update(t=1.4), "bad_plan"),
        (lambda p: p.update(roof={"type": "onion-dome"}), "bad_plan"),
        (lambda p: p["walls"][0].update(b=[0.001, 0]), "bad_plan"),
    ]:
        plan = small_plan()
        mutate(plan)
        with pytest.raises(TeeError) as err:
            validate_plan(plan)
        assert err.value.code == code


def test_frame_registry_chain_and_accuracy(tmp_path):
    registry = FrameRegistry(tmp_path)
    registry.add_frame("dwg:x:model", "drawing_model")
    registry.add_frame("geo:local", "intermediate")
    # dwg -> geo: translate +10 east; geo -> site: rotate 90 degrees
    registry.add_transform(
        "dwg:x:model",
        "geo:local",
        [1, 0, 10, 0, 1, 0],
        method="manual",
        accuracy_m=0.5,
        tier="satellite",
    )
    registry.add_transform(
        "geo:local",
        "site:enu",
        [0, -1, 0, 1, 0, 0],
        method="manual",
        accuracy_m=1.0,
        tier="satellite",
    )
    points, accuracy, used = registry.to_site("dwg:x:model", [(1.0, 2.0)])
    x, y = points[0]
    assert (round(x, 6), round(y, 6)) == (-2.0, 11.0)  # translate then rotate
    assert accuracy == pytest.approx(rss(0.5, 1.0))
    assert len(used) == 2


def test_unregistered_frame_fails_loud(tmp_path):
    registry = FrameRegistry(tmp_path)
    registry.add_frame("dwg:y:model", "drawing_model")
    with pytest.raises(TeeError) as err:
        registry.to_site("dwg:y:model", [(0, 0)])
    assert err.value.code == "unregistered_frame"


def test_datum_and_enu(tmp_path):
    registry = FrameRegistry(tmp_path)
    registry.set_site_datum(-22.57, 17.083)
    east, north, _up = registry.enu_of(-22.57, 17.0835)
    assert east == pytest.approx(51.3, abs=1.0)  # ~51 m per 0.0005 deg lon here
    assert abs(north) < 1.0


def test_fit_similarity_recovers_transform():
    src = [(0, 0), (4, 0), (4, 3), (0, 3)]
    angle = math.radians(30)
    dst = [
        (
            2 * (x * math.cos(angle) - y * math.sin(angle)) + 100,
            2 * (x * math.sin(angle) + y * math.cos(angle)) + 50,
        )
        for x, y in src
    ]
    fit = fit_similarity(src, dst)
    assert fit["free_scale"] == pytest.approx(2.0, rel=1e-6)
    assert fit["rotation_deg"] == pytest.approx(30.0, abs=1e-6)
    assert fit["rmse_m"] < 1e-9


def test_pinned_scale_reports_free_scale_conflict():
    src = [(0, 0), (10, 0), (10, 5)]
    dst = [(0, 0), (11, 0), (11, 5.5)]  # actually scaled 1.1
    fit = fit_similarity(src, dst, fix_scale=1.0)
    assert fit["scale"] == 1.0
    assert fit["free_scale"] == pytest.approx(1.1, rel=0.01)
    assert scale_conflict(fit["free_scale"], 1.0) is True
    assert scale_conflict(1.005, 1.0) is False
