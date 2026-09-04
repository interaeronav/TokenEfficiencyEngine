"""D7: everything a batch can change is a row, and a row is scalars only.

The A65 lesson, pinned: an entity the scene cache cannot see is an entity the
model cannot edit, so the doc, every parameter, every datum, every sketch,
every part, every feature and whatever the later phases put in their
containers all appear in `Document.entities()`. `detail(id)` adds numbers -
never a coordinate list, never a mesh.
"""

from __future__ import annotations

from typing import Any

import pytest

from partkiln.document import CommandError, Document

PARAMS = {"op": "param_set", "props": {"W": "100mm", "H": "60mm", "T": "10mm"}}
SKETCH = {
    "op": "create",
    "kind": "sketch",
    "name": "base",
    "props": {"plane": "XY", "profile": [{"rect": ["W", "H"], "tag": "r"}]},
}


def _doc(commands: list[dict[str, Any]]) -> Document:
    doc = Document(name="rows")
    for command in commands:
        doc.apply(command)
    return doc


def _rows(doc: Document) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in doc.entities()}


def _no_coordinates(row: dict[str, Any]) -> None:
    """A row carries scalars and short lists of them - never a coordinate dump."""
    for key, value in row.items():
        if isinstance(value, list | tuple):
            assert len(value) <= 8, f"{row['id']}.{key} is a list of {len(value)}"
            assert all(v is None or isinstance(v, str | int | float | bool) for v in value), (
                f"{row['id']}.{key} holds structures, not scalars"
            )
        elif isinstance(value, dict):
            assert len(value) <= 12, f"{row['id']}.{key} is a dict of {len(value)}"


# --------------------------------------------------------------------------- the pure rows


def test_params_and_a_sketch_are_rows_with_the_doc() -> None:
    doc = _doc([PARAMS, SKETCH])
    rows = _rows(doc)
    assert set(rows) == {"doc", "param:W", "param:H", "param:T", "sk:base"}
    assert rows["doc"]["kind"] == "doc"
    assert rows["doc"]["units"] == "mm" and rows["doc"]["standard"] == "ISO"
    assert rows["doc"]["sketches"] == 1 and rows["doc"]["parts"] == 0
    assert rows["doc"]["script_commands"] == 2
    assert rows["doc"]["fingerprint"] == doc.fingerprint()
    assert rows["param:W"] == {
        "id": "param:W",
        "kind": "param",
        "name": "W",
        "value": 100.0,
        "unit": "mm",
        "expr": "100mm",
        "used_by": 1,  # the sketch that dimensions itself with it
    }
    sketch = rows["sk:base"]
    assert sketch["kind"] == "sketch" and sketch["plane"] == "XY"
    assert sketch["dof"] == 0 and sketch["status"] == "ok" and sketch["closed"] is True
    assert sketch["area_mm2"] == 6000.0
    for row in rows.values():
        _no_coordinates(row)


def test_a_datum_is_a_row() -> None:
    doc = _doc(
        [
            PARAMS,
            {
                "op": "create",
                "kind": "plane",
                "name": "top",
                "props": {"offset": {"from": "XY", "distance": "T"}},
            },
        ]
    )
    row = _rows(doc)["plane:top"]
    assert row["kind"] == "datum" and row["type"] == "plane"
    assert row["origin"] == [0.0, 0.0, 10.0] and row["normal"] == [0.0, 0.0, 1.0]


def test_detail_of_a_sketch_is_scalars_never_coordinates() -> None:
    doc = _doc([PARAMS, SKETCH])
    detail = doc.detail("sk:base")
    assert detail["id"] == "sk:base" and detail["dof"] == 0
    assert "coordinates" not in detail
    assert len(detail["dims"]) == 2 and all(isinstance(d, str) for d in detail["dims"])
    assert detail["params"] == ["H", "W"]
    assert doc.detail("param:W")["used_by"] == ["sk:base"]
    assert doc.detail("doc")["params"] == ["H", "T", "W"]


def test_an_unknown_id_names_the_ids_that_exist() -> None:
    doc = _doc([PARAMS, SKETCH])
    # A known prefix refuses with that container's own list...
    with pytest.raises(CommandError) as caught:
        doc.detail("sk:nope")
    assert caught.value.code == "pk_ref_unknown"
    assert "sk:base" in str(caught.value)
    # ...an unknown one with every id there is.
    with pytest.raises(CommandError) as caught:
        doc.detail("widget:1")
    assert caught.value.code == "pk_ref_unknown"
    assert "sk:base" in str(caught.value) and "param:W" in str(caught.value)


# --------------------------------------------------------------------------- parts (F1)


@pytest.mark.brep
def test_f1_rows_carry_the_part_and_every_feature() -> None:
    pytest.importorskip("OCP", reason="partkiln[brep] not installed")
    from test_document_parts import F1, build

    doc = build(F1())
    rows = _rows(doc)
    assert set(rows) == {
        "doc",
        "sk:base",
        "part:plate",
        "feat:plate",
        "feat:hole1",
    }
    part = rows["part:plate"]
    assert part["kind"] == "body"
    assert part["volume_mm3"] == pytest.approx(59214.602, abs=5e-4)
    assert part["area_mm2"] == pytest.approx(15357.080, abs=5e-4)
    assert part["faces"] == 7 and part["edges"] == 15 and part["solids"] == 1
    assert part["bbox_mm"] == [100.0, 60.0, 10.0] and part["com_mm"] == [50.0, 30.0, 5.0]
    assert part["valid"] is True and part["fingerprint"] == doc.parts["plate"].fingerprint()
    assert part["material"] is None and "tree" not in part

    hole = rows["feat:hole1"]
    assert hole["kind"] == "hole" and hole["status"] == "ok"
    assert hole["parent"] == "part:plate"
    assert hole["delta_mm3"] == pytest.approx(-785.398, abs=5e-4)
    assert hole["roles"] == 1
    assert hole["params"]["dia"] == 10 and hole["refs"] == ["plate.end"]
    # a zero count and a false flag are silence, not noise
    assert "downstream" not in hole and "suppressed" not in hole
    assert rows["feat:plate"]["downstream"] == 1  # the hole sits on its end face
    assert "bbox_min" not in part and "names" not in part  # detail() has those
    assert rows["doc"]["features"] == 2 and rows["doc"]["parts"] == 1
    for row in rows.values():
        _no_coordinates(row)


@pytest.mark.brep
def test_detail_of_a_part_and_a_feature_adds_numbers_only() -> None:
    pytest.importorskip("OCP", reason="partkiln[brep] not installed")
    from test_document_parts import F1, build

    doc = build(F1())
    part = doc.detail("part:plate")
    assert [row["id"] for row in part["tree"]] == ["feat:plate", "feat:hole1"]
    assert part["used_by"] == []
    feature = doc.detail("feat:hole1")
    assert feature["kind"] == "hole" and feature["names"] == ["hole1.1.wall"]
    assert feature["args"]["dia"] == 10
    assert feature["downstream"] == []
    assert not any(isinstance(v, list) and len(v) > 8 for v in feature.values())


# --------------------------------------------------------------------------- other containers


class _Container:
    """What a later phase's container looks like from here: a compact report
    whose nested rows carry their own ids (a drawing's views, say)."""

    def summary(self) -> dict[str, Any]:
        return {
            "id": "dwg:sheet1",
            "sheet": "A4L",
            "standard": "ISO",
            "views": [
                {"id": "vw:top", "kind": "view", "dir": "top", "visible_edges": 5},
                {"id": "vw:front", "kind": "view", "dir": "front", "visible_edges": 4},
            ],
        }


def test_a_phase_container_is_read_tolerantly_and_its_children_are_rows() -> None:
    doc = _doc([PARAMS])
    doc.drawings["sheet1"] = _Container()
    rows = _rows(doc)
    assert rows["dwg:sheet1"]["kind"] == "dwg" and rows["dwg:sheet1"]["sheet"] == "A4L"
    assert rows["dwg:sheet1"]["views"] == 2  # the list became a count
    assert rows["vw:top"]["parent"] == "dwg:sheet1" and rows["vw:top"]["visible_edges"] == 5
    assert rows["doc"]["drawings"] == 1
    assert doc.detail("dwg:sheet1")["sheet"] == "A4L"


def test_a_container_with_no_report_at_all_still_gets_one_row() -> None:
    doc = _doc([PARAMS])
    doc.sheets["brk"] = object()
    assert _rows(doc)["sheet:brk"] == {"id": "sheet:brk", "kind": "sheet", "name": "brk"}
