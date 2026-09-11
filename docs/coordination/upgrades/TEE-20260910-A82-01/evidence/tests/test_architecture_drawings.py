"""Round-trip drawing units, dimensions, revision binding and physical cuts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from xml.etree import ElementTree

import pytest
from tee.architecture.drawings import _cut, export_drawings
from tee.architecture.exchange import preview
from tee.architecture.model import Document
from test_architecture_exchange import example_document


def test_plan_cut_has_real_door_window_voids() -> None:
    data = example_document()
    wall_parts = [mesh for mesh in preview(data)["meshes"] if mesh["id"] == "wall"]
    segments = [line for mesh in wall_parts for line in _cut(mesh, 2, 4500)]
    assert segments
    # At half-storey height both openings are void. No material cut edge may
    # cross the middle of either opening at either exterior wall face.
    for opening_x in (900, 3000):
        assert not any(
            abs(a[1] - b[1]) < 1e-8
            and abs(abs(a[1]) - 100) < 1e-8
            and min(a[0], b[0]) < opening_x < max(a[0], b[0])
            for a, b in segments
        )
    assert any(min(a[0], b[0]) <= 200 <= max(a[0], b[0]) for a, b in segments)


def test_svg_dxf_pdf_and_cutlist_share_revision_and_real_blank_sizes(tmp_path: Path) -> None:
    ezdxf = pytest.importorskip("ezdxf")
    pypdf = pytest.importorskip("pypdf")
    data = example_document()
    result = export_drawings(data, tmp_path / "drawings")
    manifest = json.loads(Path(result["manifest"]).read_text())
    assert result["pdf"]["status"] == "written", result
    directory = Path(result["directory"])
    assert result["panels"] > 5
    for view in manifest["views"]:
        svg = ElementTree.fromstring((directory / (view["name"] + ".svg")).read_text())
        metadata = json.loads(svg.find("{http://www.w3.org/2000/svg}metadata").text)
        assert metadata["revision"] == data["revision"]
        assert metadata["units"] == "mm"
        dxf = ezdxf.readfile(directory / (view["name"] + ".dxf"))
        assert dxf.units == ezdxf.units.MM
        dimensions = list(dxf.modelspace().query("DIMENSION"))
        assert dimensions
        assert all(
            dim.get_xdata("TEE_ARCHITECTURE")[1].value == data["revision"] for dim in dimensions
        )
    with (directory / "cabinet-cutlist.csv").open() as stream:
        cutlist = list(csv.DictReader(stream))
    door = next(row for row in cutlist if row["role"] == "door")
    assert float(door["blank_width_mm"]) == pytest.approx(295)
    assert float(door["finished_width_mm"]) == pytest.approx(297)
    assert door["material"] == "Fixture plywood"
    assert all(int(row["revision"]) == data["revision"] for row in cutlist)
    assert len(pypdf.PdfReader(directory / "review-set.pdf").pages) == len(manifest["views"])
    assert "no hidden-line removal" in next(
        view["note"] for view in manifest["views"] if view["name"] == "elevation"
    )


def test_dimensions_regenerate_after_edit_and_ifc_polygon_is_not_bbox(tmp_path: Path) -> None:
    document = Document.from_dict(example_document())
    first = export_drawings(document.to_dict(), tmp_path / "first")
    old = json.loads(Path(first["manifest"]).read_text())
    document.apply([{"op": "update", "id": "wall", "changes": {"end": [5000, 0]}}])
    second = export_drawings(document.to_dict(), tmp_path / "second")
    new = json.loads(Path(second["manifest"]).read_text())
    old_width = next(view for view in old["views"] if view["name"] == "plan-level")["dimensions"][
        0
    ]["value_mm"]
    new_width = next(view for view in new["views"] if view["name"] == "plan-level")["dimensions"][
        0
    ]["value_mm"]
    assert new_width - old_width == 1000
    assert new["revision"] == old["revision"] + 1
    with (tmp_path / "second/schedule.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    slab = next(row for row in rows if row["id"] == "slab")
    assert float(slab["area_m2"]) == 12  # bounding rectangle would be 16.


def test_spreadsheet_formula_metadata_is_inert(tmp_path: Path) -> None:
    data = example_document()
    data["entities"]["cabinet"]["material"] = '=HYPERLINK("https://example.invalid")'
    result = export_drawings(data, tmp_path / "safe")
    with (Path(result["directory"]) / "cabinet-cutlist.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert all(row["material"].startswith("'=") for row in rows)


def test_annotations_share_ids_dimensions_area_and_revision_in_all_formats(tmp_path: Path) -> None:
    import ezdxf
    from pypdf import PdfReader

    data = example_document()
    result = export_drawings(data, tmp_path / "annotated")
    directory = Path(result["directory"])
    manifest = json.loads(Path(result["manifest"]).read_text())
    plan = next(view for view in manifest["views"] if view["name"] == "plan-level")
    labels = {label["id"]: label for label in plan["annotations"]}
    assert set(labels) == {"room", "door", "window", "cabinet"}
    assert "12.00 m²" in labels["room"]["lines"]
    assert "Sill 1000 mm" in labels["window"]["lines"]
    assert all(label["revision"] == data["revision"] for label in labels.values())
    assert labels["window"]["leader_mm"]
    svg = ElementTree.fromstring((directory / "plan-level.svg").read_text())
    metadata = json.loads(svg.find("{http://www.w3.org/2000/svg}metadata").text)
    assert metadata["annotations"] == plan["annotations"]
    text = PdfReader(directory / "review-set.pdf").pages[0].extract_text()
    dxf = ezdxf.readfile(directory / "plan-level.dxf")
    dxf_text = {entity.dxf.text for entity in dxf.modelspace().query("TEXT")}
    for label in labels.values():
        for line in label["lines"]:
            assert line in text
            assert line in dxf_text


def test_concave_room_text_box_stays_out_of_the_notch(tmp_path: Path) -> None:
    from tee.architecture.drawings import _paper_inverse

    doc = Document.create("Concave room")
    polygon = [
        [0, 0],
        [6000, 0],
        [6000, 6000],
        [4000, 6000],
        [4000, 2000],
        [2000, 2000],
        [2000, 6000],
        [0, 6000],
    ]
    doc.apply(
        [
            {"op": "create", "entity": entity}
            for entity in [
                {"id": "level", "kind": "storey", "name": "Ground", "elevation": 0, "height": 3000},
                {
                    "id": "room",
                    "kind": "space",
                    "name": "U room",
                    "storey": "level",
                    "height": 3000,
                    "polygon": polygon,
                },
            ]
        ]
    )
    result = export_drawings(doc.to_dict(), tmp_path / "concave")
    view = json.loads(Path(result["manifest"]).read_text())["views"][0]
    label = view["annotations"][0]
    a, b = [_paper_inverse(view, p) for p in (label["box_mm"][:2], label["box_mm"][2:])]
    low, high = [min(a[i], b[i]) for i in range(2)], [max(a[i], b[i]) for i in range(2)]
    assert all(0 <= low[i] < high[i] <= 6000 for i in range(2))
    notch_area = max(0, min(high[0], 4000) - max(low[0], 2000)) * max(
        0, min(high[1], 6000) - max(low[1], 2000)
    )
    assert notch_area == 0  # The ordinary polygon/bounding-box centre lies in the notch.
    assert "28.00 m²" in label["lines"]


def test_overcrowded_labels_refuse_before_any_delivery(tmp_path: Path) -> None:
    from tee.kernel.errors import TeeError

    doc = Document.create("Crowded")
    doc.apply(
        [
            {"op": "create", "entity": entity}
            for entity in [
                {"id": "level", "kind": "storey", "name": "Ground", "elevation": 0, "height": 3000},
                *[
                    {
                        "id": name,
                        "kind": "space",
                        "name": name,
                        "storey": "level",
                        "height": 3000,
                        "polygon": [[0, 0], [6000, 0], [0, 6000]],
                    }
                    for name in ("RoomA", "RoomB")
                ],
            ]
        ]
    )
    with pytest.raises(TeeError, match="without a label/line collision"):
        export_drawings(doc.to_dict(), tmp_path / "crowded")
    assert not (tmp_path / "crowded").exists()
