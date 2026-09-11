"""Cut dimensions, assembled envelopes and independently checked sheet spacing."""

import copy
import math
import random

import pytest
from tee.architecture.cabinets import nest, panels, schedule
from tee.architecture.model import ArchitectureError, Document


def cabinet(**changes) -> dict:
    return {
        "id": "cab",
        "kind": "cabinet",
        "name": "Cabinet",
        "storey": "ground",
        "origin": [100, 200, 300],
        "width": 800,
        "depth": 600,
        "height": 900,
        "panel_thickness": 18,
        "back_thickness": 6,
        "shelves": 2,
        "doors": 2,
        "plinth_height": 100,
        "grain": "height",
        "edge_band_mm": 1,
        "material": "plywood",
        "properties": {"door_gap_mm": 2},
        **changes,
    }


def test_carcass_cut_dimensions_and_finished_envelopes():
    rows = panels(cabinet())
    assert len(rows) == 10
    by_id = {p["id"]: p for p in rows}
    assert by_id["cab_side_1"]["size"] == [18, 582, 800]
    assert by_id["cab_side_1"]["width"] == 581  # front edge band
    assert by_id["cab_side_2"]["origin"] == [882, 218, 400]
    assert by_id["cab_top_1"]["size"] == [764, 582, 18]
    assert by_id["cab_back_1"]["size"] == [764, 6, 764]
    assert by_id["cab_back_1"]["origin"] == [118, 794, 418]
    assert by_id["cab_shelf_1"]["size"] == [764, 576, 18]
    assert by_id["cab_shelf_1"]["origin"][2] == pytest.approx(300 + 100 + 18 + 728 / 3)
    assert by_id["cab_door_1"]["size"] == [397, 18, 796]
    assert by_id["cab_door_1"]["width"] == 395
    assert by_id["cab_door_1"]["height"] == 794
    assert by_id["cab_door_2"]["origin"] == [501, 200, 402]
    assert by_id["cab_plinth_1"]["size"] == [800, 18, 100]
    # Panel envelopes do not overlap by positive volume, and fit overall cabinet.
    for i, a in enumerate(rows):
        for axis, value in enumerate(a["origin"]):
            assert value >= [100, 200, 300][axis]
            assert value + a["size"][axis] <= [900, 800, 1200][axis] + 1e-8
        for b in rows[i + 1 :]:
            overlap = [
                min(a["origin"][k] + a["size"][k], b["origin"][k] + b["size"][k])
                - max(a["origin"][k], b["origin"][k])
                for k in range(3)
            ]
            assert min(overlap) <= 1e-8
    report = schedule(cabinet())
    assert report["cut_area_m2"] == pytest.approx(sum(p["width"] * p["height"] for p in rows) / 1e6)
    assert report["requirements"]["cnc"] == "not_verified"


def test_open_cabinet_no_plinth_or_gap_and_one_door():
    rows = panels(cabinet(doors=0, shelves=0, plinth_height=0, properties={}, edge_band_mm=0))
    assert len(rows) == 5
    assert rows[0]["size"] == [18, 600, 900]
    door = next(p for p in panels(cabinet(doors=1)) if p["role"] == "door")
    assert door["finished_width"] == 796


@pytest.mark.parametrize(
    "changes",
    [
        {"width": 36},
        {"depth": 24},
        {"height": 136},
        {"plinth_height": -1},
        {"plinth_height": 900},
        {"panel_thickness": 0},
        {"back_thickness": 600},
        {"edge_band_mm": -1},
        {"edge_band_mm": 10},
        {"shelves": 100},
        {"shelves": 1.5},
        {"shelves": True},
        {"doors": 3},
        {"doors": True},
        {"properties": {}},
        {"properties": {"door_gap_mm": 0}},
        {"properties": {"door_gap_mm": 500}},
        {"width": math.inf},
        {"origin": [0, 0, math.nan]},
        {"origin": [0, 0]},
        {"material": ""},
        {"grain": []},
    ],
)
def test_impossible_cabinets_refuse(changes):
    with pytest.raises(ArchitectureError):
        panels(cabinet(**changes))


def test_cabinet_edit_regenerates_cutlist_and_invalid_edit_rolls_back():
    doc = Document.create("Cabinet project")
    doc.apply(
        [
            {
                "op": "create",
                "entity": {
                    "id": "ground",
                    "kind": "storey",
                    "name": "Ground",
                    "height": 3000,
                    "elevation": 0,
                },
            },
            {"op": "create", "entity": cabinet()},
        ]
    )
    old = panels(doc.entities["cab"])
    doc.apply([{"op": "update", "id": "cab", "changes": {"width": 1000}}])
    new = panels(doc.entities["cab"])
    assert [p["id"] for p in old] == [p["id"] for p in new]
    assert next(p for p in new if p["role"] == "back")["width"] == 964
    before = doc.to_dict()
    with pytest.raises(ArchitectureError):
        doc.apply([{"op": "update", "id": "cab", "changes": {"width": 20}}])
    assert doc.to_dict() == before
    doc.undo()
    assert panels(doc.entities["cab"]) == old


def row(pid="p", width=100, height=200, grain="none", material="plywood", thickness=18):
    return {
        "id": pid,
        "width": width,
        "height": height,
        "grain": grain,
        "material": material,
        "thickness": thickness,
    }


def test_nesting_rotation_grain_stock_and_kerf():
    with pytest.raises(ArchitectureError):
        nest([row(width=200, height=100, grain="height")], 100, 200, 3, allow_rotate=True)
    out = nest([row(width=200, height=100)], 100, 200, 3, allow_rotate=True)
    assert out["sheets"][0]["placements"][0]["rotated"]
    out = nest([row("a", 100, 100), row("b", 100, 100)], 203, 100, 3)
    assert out["sheet_count"] == 1
    assert out["sheets"][0]["placements"][1]["x"] == 103
    assert nest([row("a", 100, 100), row("b", 100, 100)], 202, 100, 3)["sheet_count"] == 2
    assert (
        nest([row("a"), row("b", material="oak"), row("c", thickness=6)], 1000, 1000, 3)[
            "sheet_count"
        ]
        == 3
    )


def test_seeded_nesting_independent_bounds_and_rectangle_separation():
    rng = random.Random(24)
    rows = [row(str(i), rng.randint(50, 400), rng.randint(50, 400)) for i in range(90)]
    original = copy.deepcopy(rows)
    result = nest(rows, 1200, 2400, 3, True)
    assert rows == original
    assert result == nest(list(reversed(rows)), 1200, 2400, 3, True)
    seen = set()
    for sheet in result["sheets"]:
        for i, a in enumerate(sheet["placements"]):
            seen.add(a["id"])
            assert 0 <= a["x"] <= 1200 - a["width"]
            assert 0 <= a["y"] <= 2400 - a["height"]
            for b in sheet["placements"][i + 1 :]:
                assert (
                    a["x"] + a["width"] + 3 <= b["x"]
                    or b["x"] + b["width"] + 3 <= a["x"]
                    or a["y"] + a["height"] + 3 <= b["y"]
                    or b["y"] + b["height"] + 3 <= a["y"]
                )
    assert seen == {p["id"] for p in rows}
    assert 0 < result["utilization"] <= 1


@pytest.mark.parametrize(
    "rows,sw,sh,kerf",
    [
        ([], 1000, 1000, 3),
        ([row(), row()], 1000, 1000, 3),
        ([row(width=0)], 1000, 1000, 3),
        ([row()], 0, 1000, 3),
        ([row()], 1000, math.nan, 3),
        ([row()], 1000, 1000, -1),
        ([row(grain=[])], 1000, 1000, 3),
        ([row(width=1001)], 1000, 1000, 3),
    ],
)
def test_nesting_invalid_inputs(rows, sw, sh, kerf):
    with pytest.raises(ArchitectureError):
        nest(rows, sw, sh, kerf)
