"""Independent IFC reopen/geometry controls for A82, with no DCC dependency."""

from __future__ import annotations

import copy
import math
from pathlib import Path

import pytest
from tee.architecture.exchange import export_ifc, preview, validate_ifc
from tee.architecture.model import Document


def example_document() -> dict:
    document = Document.create("Owned IFC fixture")
    polygon = [[0, 0], [4000, 0], [4000, 2000], [2000, 2000], [2000, 4000], [0, 4000]]
    entities = [
        {"id": "level", "kind": "storey", "name": "Upper", "elevation": 3000, "height": 3000},
        {
            "id": "wall",
            "kind": "wall",
            "name": "Wall",
            "storey": "level",
            "start": [0, 0],
            "end": [4000, 0],
            "thickness": 200,
            "height": 3000,
        },
        {
            "id": "door",
            "kind": "opening",
            "name": "Door",
            "wall": "wall",
            "offset": 500,
            "width": 900,
            "height": 2100,
            "sill": 0,
            "fill": "door",
        },
        {
            "id": "window",
            "kind": "opening",
            "name": "Window",
            "wall": "wall",
            "offset": 2500,
            "width": 1000,
            "height": 1000,
            "sill": 1000,
            "fill": "window",
        },
        {
            "id": "room",
            "kind": "space",
            "name": "L-shaped room",
            "storey": "level",
            "polygon": polygon,
            "height": 3000,
        },
        {
            "id": "slab",
            "kind": "slab",
            "name": "L-shaped slab",
            "storey": "level",
            "polygon": polygon,
            "thickness": 200,
        },
        {
            "id": "roof",
            "kind": "roof",
            "name": "Flat roof",
            "storey": "level",
            "polygon": polygon,
            "thickness": 150,
            "base_height": 3000,
        },
        {
            "id": "cabinet",
            "kind": "cabinet",
            "name": "Fixture cabinet",
            "storey": "level",
            "origin": [200, 200, 3000],
            "width": 600,
            "depth": 600,
            "height": 900,
            "panel_thickness": 18,
            "back_thickness": 6,
            "shelves": 1,
            "doors": 2,
            "plinth_height": 100,
            "grain": "height",
            "edge_band_mm": 1,
            "material": "Fixture plywood",
            "properties": {"door_gap_mm": 2, "api_key": "never-export-this"},
        },
    ]
    document.apply([{"op": "create", "entity": entity} for entity in entities])
    return document.to_dict()


def _mesh_volume(mesh: dict) -> float:
    # Independent signed tetrahedra; preview/IFC writer do not calculate this.
    values = []
    for face in mesh["faces"]:
        a, b, c = [mesh["vertices"][index] for index in face]
        values.append(
            (
                a[0] * (b[1] * c[2] - b[2] * c[1])
                + a[1] * (b[2] * c[0] - b[0] * c[2])
                + a[2] * (b[0] * c[1] - b[1] * c[0])
            )
            / 6
        )
    return abs(math.fsum(values))


def test_real_ifc_semantics_units_and_actual_solids(tmp_path: Path) -> None:
    ifc = pytest.importorskip("ifcopenshell")
    import ifcopenshell.util.element
    import ifcopenshell.util.placement
    import ifcopenshell.util.unit

    path = tmp_path / "fixture.ifc"
    report = export_ifc(example_document(), path)
    model = ifc.open(str(path))
    assert report["entities"] == 8 and report["fillings"] == 2
    assert model.schema == "IFC4"
    assert ifcopenshell.util.unit.calculate_unit_scale(model) == 0.001
    storey = model.by_type("IfcBuildingStorey")[0]
    assert storey.Elevation == 3000
    assert ifcopenshell.util.placement.get_local_placement(storey.ObjectPlacement)[2, 3] == 3000
    wall = model.by_type("IfcWall")[0]
    assert ifcopenshell.util.element.get_container(wall) == storey
    assert len(wall.HasOpenings) == 2
    assert {
        relation.RelatedOpeningElement.HasFillings[0].RelatedBuildingElement.is_a()
        for relation in wall.HasOpenings
    } == {"IfcDoor", "IfcWindow"}
    assert model.by_type("IfcDoor")[0].OverallWidth == 900
    assert model.by_type("IfcDoor")[0].Representation is None
    assert (
        ifcopenshell.util.element.get_material(model.by_type("IfcFurnishingElement")[0]).Name
        == "Fixture plywood"
    )
    assert "never-export-this" not in path.read_text()
    result = validate_ifc(path)
    assert result["schema"]["status"] == "pass", result["schema"]
    assert result["geometry"]["status"] == "pass", result["geometry"]
    measured = {row["id"]: row for row in result["geometry"]["measurements"]}
    # 4*3*.2 gross minus both real host subtractions, not an attribute check.
    assert measured["wall"]["volume_m3"] == pytest.approx(2.4 - 0.9 * 2.1 * 0.2 - 1 * 1 * 0.2)
    assert measured["wall"]["bounds_mm"] == {"min": [0, -100, 3000], "max": [4000, 100, 6000]}
    assert measured["room"]["volume_m3"] == pytest.approx(36)
    assert measured["slab"]["volume_m3"] == pytest.approx(2.4)  # L polygon, not 4x4 box.
    assert measured["slab"]["bounds_mm"]["min"][2] == 2800
    assert measured["roof"]["volume_m3"] == pytest.approx(1.8)
    assert measured["roof"]["bounds_mm"]["min"][2] == 6000
    assert 0 < measured["cabinet"]["volume_m3"] < 0.6 * 0.6 * 0.9 / 2
    # Independent fixture arithmetic: two sides, top/bottom, back, one shelf,
    # two gapped doors and the plinth, all using FINISHED envelopes.
    assert measured["cabinet"]["volume_m3"] == pytest.approx(0.046602288)
    assert result["ids"]["status"] == result["regulatory"]["status"] == "not_verified"


def test_guids_survive_edits_and_door_host_rotation(tmp_path: Path) -> None:
    ifc = pytest.importorskip("ifcopenshell")

    data = example_document()
    first, second = tmp_path / "first.ifc", tmp_path / "second.ifc"
    export_ifc(data, first)
    old = ifc.open(str(first))
    document = Document.from_dict(data)
    document.apply(
        [
            {
                "op": "update",
                "id": "wall",
                "changes": {"start": [10000, 20000], "end": [10000, 24000]},
            }
        ]
    )
    export_ifc(document.to_dict(), second)
    new = ifc.open(str(second))
    assert old.by_type("IfcWall")[0].GlobalId == new.by_type("IfcWall")[0].GlobalId
    assert (
        old.by_type("IfcOpeningElement")[0].GlobalId == new.by_type("IfcOpeningElement")[0].GlobalId
    )
    measured = {row["id"]: row for row in validate_ifc(second)["geometry"]["measurements"]}
    assert measured["wall"]["bounds_mm"] == {
        "min": [9900, 20000, 3000],
        "max": [10100, 24000, 6000],
    }
    assert measured["wall"]["volume_m3"] == pytest.approx(1.822)
    # Negative control: deleting a real void relationship changes measured volume.
    relation = new.by_type("IfcRelVoidsElement")[0]
    new.remove(relation)
    negative = tmp_path / "missing-void.ifc"
    new.write(str(negative))
    bad = {row["id"]: row for row in validate_ifc(negative)["geometry"]["measurements"]}
    assert bad["wall"]["volume_m3"] > measured["wall"]["volume_m3"] + 0.1


def test_preview_true_openings_concavity_and_panel_solids() -> None:
    data = example_document()
    original = copy.deepcopy(data)
    result = preview(data)
    assert data == original
    volumes = {}
    for mesh in result["meshes"]:
        volumes[mesh["id"]] = volumes.get(mesh["id"], 0) + _mesh_volume(mesh)
    assert volumes["wall"] == pytest.approx(1.822e9)
    assert volumes["slab"] == pytest.approx(2.4e9)
    assert volumes["room"] == pytest.approx(36e9)
    assert volumes["cabinet"] < 600 * 600 * 900 / 2
    assert result["revision"] == data["revision"]
    assert result["units"] == "mm"


def test_export_refuses_unvalidated_nonfinite_dimensions(tmp_path: Path) -> None:
    data = example_document()
    data["entities"]["wall"]["height"] = float("nan")
    with pytest.raises(ValueError):
        export_ifc(data, tmp_path / "bad.ifc")
    assert not (tmp_path / "bad.ifc").exists()


def test_old_extract_elevation_attribute_matches_metre_geometry(tmp_path: Path) -> None:
    ifc = pytest.importorskip("ifcopenshell")
    import ifcopenshell.util.placement
    import ifcopenshell.util.unit
    from tee.extract.ifc import export_ifc as old_export

    plan = {
        "levels": [{"index": 1, "name": "Upper", "elevation_z": 3.0}],
        "walls": [{"id": "w", "a": [0, 0], "b": [4, 0], "level": 1, "thickness": 0.2, "height": 3}],
    }
    path = tmp_path / "legacy.ifc"
    old_export(plan, path)
    model = ifc.open(str(path))
    scale = ifcopenshell.util.unit.calculate_unit_scale(model)
    assert model.by_type("IfcBuildingStorey")[0].Elevation * scale == pytest.approx(3.0)
    wall = model.by_type("IfcWall")[0]
    assert ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement)[
        2, 3
    ] * scale == pytest.approx(3.0)


def test_glb_reopens_in_metres_with_stable_semantic_node_names(tmp_path: Path) -> None:
    trimesh = pytest.importorskip("trimesh")
    import json
    import struct

    from tee.architecture.exchange import export_glb

    data = example_document()
    path = tmp_path / "visual.glb"
    result = export_glb(data, path)
    loaded = trimesh.load(str(path), force="scene", process=False)
    bounds = preview(data)["bounds"]
    assert loaded.bounds[0] == pytest.approx([value / 1000 for value in bounds["min"]], abs=1e-6)
    assert loaded.bounds[1] == pytest.approx([value / 1000 for value in bounds["max"]], abs=1e-6)
    assert result["units"] == "m" and result["source_units"] == "mm"
    raw = path.read_bytes()
    size = struct.unpack_from("<I", raw, 12)[0]
    gltf = json.loads(raw[20 : 20 + size])
    names = {node["name"] for node in gltf["nodes"]}
    assert "wall:0" in names and "room:0" in names
    assert any(name.startswith("cabinet:cabinet_side_") for name in names)
    assert gltf["asset"]["version"] == "2.0"


def test_schema_failure_stays_distinct_from_geometric_measurement(tmp_path: Path) -> None:
    ifc = pytest.importorskip("ifcopenshell")
    path = tmp_path / "schema-bad.ifc"
    export_ifc(example_document(), path)
    model = ifc.open(str(path))
    model.by_type("IfcWall")[0].GlobalId = "invalid"
    model.write(str(path))
    result = validate_ifc(path)
    assert result["schema"]["status"] == "fail"
    assert result["geometry"]["products_measured"] > 0
    assert result["regulatory"]["status"] == "not_verified"


def test_unjoined_wall_overlap_is_measured_after_actual_opening_voids() -> None:
    document = Document.from_dict(example_document())
    document.apply(
        [
            {
                "op": "create",
                "entity": {
                    "id": "crossing",
                    "kind": "wall",
                    "name": "Crossing",
                    "storey": "level",
                    "start": [900, -1000],
                    "end": [900, 1000],
                    "thickness": 200,
                    "height": 3000,
                },
            }
        ]
    )
    joints = preview(document.to_dict())["wall_junctions"]
    assert joints["status"] == "overlaps_present"
    assert joints["pairs_found"] == 1
    assert joints["overlaps"][0]["overlap_m3"] == pytest.approx(0.036)
    assert "not additive" in joints["policy"]
    document.apply(
        [
            {
                "op": "update",
                "id": "crossing",
                "changes": {
                    "start": [200, -1000],
                    "end": [200, 1000],
                },
            }
        ]
    )
    assert preview(document.to_dict())["wall_junctions"]["overlaps"][0][
        "overlap_m3"
    ] == pytest.approx(0.12)


def joined_document(*, tee: bool = False, rotation: float = 0) -> dict:
    document = Document.create("Butt fixture")
    angle = math.radians(rotation)

    def rotate(point):
        x, y = point
        return [
            10000 + math.cos(angle) * x - math.sin(angle) * y,
            20000 + math.sin(angle) * x + math.cos(angle) * y,
        ]

    rows = [
        {"id": "level", "kind": "storey", "name": "Ground", "elevation": 0, "height": 3000},
        {
            "id": "z_main" if tee else "alpha",
            "kind": "wall",
            "name": "Main",
            "storey": "level",
            "start": rotate([0, 0]),
            "end": rotate([4000, 0]),
            "thickness": 200,
            "height": 3000,
        },
        {
            "id": "a_branch" if tee else "beta",
            "kind": "wall",
            "name": "Branch",
            "storey": "level",
            "start": rotate([2000 if tee else 0, 0]),
            "end": rotate([2000 if tee else 0, 3000]),
            "thickness": 300,
            "height": 3000,
        },
    ]
    document.apply(
        [{"op": "create", "entity": row} for row in rows]
        + [{"op": "project", "changes": {"facts": {"wall_join_policy": "orthogonal_butt_v1"}}}]
    )
    return document.to_dict()


@pytest.mark.parametrize(
    "tee,rotation,volume", [(False, 0, 5.1), (True, 0, 5.01), (False, 37, 5.1), (True, 37, 5.01)]
)
def test_l_t_butt_solids_have_closed_corners_and_no_overlap(
    tmp_path: Path, tee, rotation, volume
) -> None:
    data = joined_document(tee=tee, rotation=rotation)
    original = copy.deepcopy(data)
    scene = preview(data)
    assert data == original
    assert scene["wall_junctions"]["pairs_found"] == 0
    assert scene["wall_joins"]["count"] == 1
    joint = scene["wall_joins"]["joints"][0]
    assert joint["through"] == ("z_main" if tee else "alpha")
    assert joint["type"] == ("T" if tee else "L")
    assert sum(_mesh_volume(mesh) for mesh in scene["meshes"]) / 1e9 == pytest.approx(volume)
    if not tee and rotation == 0:
        # An outer L corner is filled; simple box-overlap subtraction leaves this missing.
        assert any(
            vertex == [9850.0, 19900.0, 0.0]
            for mesh in scene["meshes"]
            for vertex in mesh["vertices"]
        )
    path = tmp_path / "joined.ifc"
    exported = export_ifc(data, path)
    assert exported["wall_junctions"]["pairs_found"] == 0
    verified = validate_ifc(path)
    assert verified["schema"]["status"] == "pass"
    assert sum(row["volume_m3"] for row in verified["geometry"]["measurements"]) == pytest.approx(
        volume
    )


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"end": [13000, 23000]}, "not orthogonal"),
        ({"start": [12000, 19000], "end": [12000, 21000]}, "X junction"),
        ({"height": 2500}, "different base/top"),
        ({"start": [10000, 20050], "end": [14000, 20050]}, "Parallel overlapping"),
        ({"end": [10000, 20050]}, "consumed"),
    ],
)
def test_join_policy_refuses_unsupported_geometry(changes, reason) -> None:
    document = Document.from_dict(joined_document())
    before = document.to_dict()
    with pytest.raises(ValueError, match=reason):
        document.apply([{"op": "update", "id": "beta", "changes": changes}])
    assert document.to_dict() == before


@pytest.mark.parametrize(
    "tee,host,offset,reason",
    [
        (False, "beta", 50, "butt trim"),
        (True, "z_main", 1800, "intersects wall junction"),
    ],
)
def test_join_refuses_opening_in_trim_or_at_t_throat(tee, host, offset, reason) -> None:
    document = Document.from_dict(joined_document(tee=tee))
    before = document.to_dict()
    with pytest.raises(ValueError, match=reason):
        document.apply(
            [
                {
                    "op": "create",
                    "entity": {
                        "id": "bad",
                        "kind": "opening",
                        "name": "Bad",
                        "wall": host,
                        "offset": offset,
                        "width": 500,
                        "height": 2100,
                        "sill": 0,
                        "fill": "door",
                    },
                }
            ]
        )
    assert document.to_dict() == before


def test_federated_guids_are_document_unique_and_rename_stable(tmp_path: Path) -> None:
    ifc = pytest.importorskip("ifcopenshell")
    a, b = Document.from_dict(joined_document()), Document.from_dict(joined_document())
    assert a.to_dict()["document_id"] != b.to_dict()["document_id"]
    paths = [tmp_path / name for name in ("a.ifc", "b.ifc", "renamed.ifc")]
    export_ifc(a.to_dict(), paths[0])
    export_ifc(b.to_dict(), paths[1])
    a.apply([{"op": "project", "changes": {"name": "Renamed"}}])
    export_ifc(a.to_dict(), paths[2])
    models = [ifc.open(str(path)) for path in paths]
    for kind in ("IfcProject", "IfcSite", "IfcBuilding", "IfcBuildingStorey", "IfcWall"):
        before, other, renamed = [{row.GlobalId for row in model.by_type(kind)} for model in models]
        assert before.isdisjoint(other)
        assert before == renamed
