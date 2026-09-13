"""Atomic authoring, geometry constraints and persistent undo contracts."""

import copy
import json
import math

import pytest
from tee.architecture.model import MAX_HISTORY, ArchitectureError, Document


def storey() -> dict:
    return {"id": "ground", "kind": "storey", "name": "Ground", "elevation": 0, "height": 3000}


def wall() -> dict:
    return {
        "id": "wall",
        "kind": "wall",
        "name": "Wall",
        "storey": "ground",
        "start": [0, 0],
        "end": [4000, 0],
        "height": 2800,
        "thickness": 200,
    }


def opening(**changes) -> dict:
    return {
        "id": "door",
        "kind": "opening",
        "name": "Door",
        "wall": "wall",
        "offset": 500,
        "width": 900,
        "height": 2100,
        "sill": 0,
        "fill": "door",
        **changes,
    }


def house() -> Document:
    doc = Document.create("Test house")
    doc.apply([{"op": "create", "entity": e} for e in (storey(), wall(), opening())])
    return doc


def test_persistent_undo_monotonic_revision_and_copy_isolation():
    doc = house()
    doc.apply([{"op": "update", "id": "wall", "changes": {"end": [5000, 0]}}], 1)
    restored = Document.from_dict(json.loads(json.dumps(doc.to_dict())))
    assert restored.revision == 2
    restored.undo(2)
    assert restored.revision == 3
    assert restored.entities["wall"]["end"] == [4000, 0]
    assert restored.entities["door"]["wall"] == "wall"
    restored.undo(3)
    assert restored.revision == 4 and not restored.entities
    with pytest.raises(ArchitectureError) as exc:
        restored.undo()
    assert exc.value.code == "ak_no_undo"
    detached = doc.to_dict()
    detached["entities"].clear()
    doc.entities["wall"]["end"][0] = 1
    assert doc.entities["wall"]["end"] == [5000, 0]
    assert "history" not in doc.summary()


def test_document_identity_survives_edits_undo_and_distinguishes_same_named_models():
    doc = house()
    identity = doc.to_dict()["document_id"]
    assert identity != house().to_dict()["document_id"]
    doc.apply([{"op": "project", "changes": {"name": "Renamed"}}])
    assert doc.to_dict()["document_id"] == identity
    doc.undo()
    assert Document.from_dict(doc.to_dict()).to_dict()["document_id"] == identity
    for corrupt in (None, "not-a-uuid", identity.upper()):
        data = doc.to_dict()
        data["document_id"] = corrupt
        with pytest.raises(ArchitectureError) as exc:
            Document.from_dict(data)
        assert exc.value.code == "ak_identity"
    data = doc.to_dict()
    del data["document_id"]
    with pytest.raises(ArchitectureError, match="document_id"):
        Document.from_dict(data)
    data = doc.to_dict()
    data["history"][0]["document_id"] = house().to_dict()["document_id"]
    with pytest.raises(ArchitectureError, match="another document"):
        Document.from_dict(data)


def test_atomic_batch_allows_forward_refs_and_cascade_delete_explicit():
    doc = Document.create("Project")
    doc.apply([{"op": "create", "entity": e} for e in (opening(), wall(), storey())])
    before = doc.to_dict()
    with pytest.raises(ArchitectureError):
        doc.apply(
            [
                {"op": "update", "id": "wall", "changes": {"name": "Changed"}},
                {"op": "delete", "id": "ground"},
            ]
        )
    assert doc.to_dict() == before
    doc.apply([{"op": "delete", "id": eid} for eid in ("ground", "wall", "door")])
    assert not doc.entities


@pytest.mark.parametrize(
    "changes",
    [
        {"end": [1200, 0]},
        {"height": 2000},
        {"start": [4000, 0]},
        {"thickness": -1},
        {"height": math.nan},
        {"end": [math.inf, 0]},
        {"height": True},
        {"height": 10**1000},
        {"storey": []},
        {"id": "new"},
        {"kind": "slab"},
        {"unexpected": 42},
    ],
)
def test_invalid_wall_edits_leave_revision_geometry_and_history(changes):
    doc = house()
    before = doc.to_dict()
    with pytest.raises(ArchitectureError):
        doc.apply([{"op": "update", "id": "wall", "changes": changes}])
    assert doc.to_dict() == before


@pytest.mark.parametrize(
    "changes",
    [
        {"offset": -1},
        {"width": 0},
        {"sill": -1},
        {"width": 4000},
        {"height": 3000},
        {"wall": "door"},
        {"wall": []},
        {"fill": []},
    ],
)
def test_opening_bounds_and_wrong_kind_references(changes):
    doc = house()
    with pytest.raises(ArchitectureError):
        doc.apply([{"op": "update", "id": "door", "changes": changes}])


def test_opening_overlap_is_two_dimensional_and_touching_is_allowed():
    doc = house()
    with pytest.raises(ArchitectureError, match="overlap"):
        doc.apply([{"op": "create", "entity": opening(id="other", offset=1000)}])
    doc.apply([{"op": "create", "entity": opening(id="transom", sill=2100, height=400)}])
    doc.apply([{"op": "create", "entity": opening(id="adjacent", offset=1400)}])
    assert doc.validate()["ok"]


@pytest.mark.parametrize(
    "polygon",
    [
        [[0, 0], [10, 10], [0, 10], [10, 0]],
        [[0, 0], [10, 0], [5, 0]],
        [[0, 0], [10, 0], [5, 0], [5, 10]],
        [[0, 0], [10, 0], [10, 10], [0, 0]],
        [[0, 0], [10, 0], [math.nan, 10]],
        [[0, 0], [10, 0]],
    ],
)
def test_invalid_polygons_refuse(polygon):
    doc = house()
    with pytest.raises(ArchitectureError):
        doc.apply(
            [
                {
                    "op": "create",
                    "entity": {
                        "id": "slab",
                        "kind": "slab",
                        "name": "Slab",
                        "storey": "ground",
                        "polygon": polygon,
                        "thickness": 200,
                    },
                }
            ]
        )


def test_concave_translated_polygon_and_explicit_flat_roof():
    doc = house()
    polygon = [
        [x + 1e8, y - 1e8] for x, y in [(0, 0), (1000, 0), (1000, 1000), (500, 500), (0, 1000)]
    ]
    doc.apply(
        [
            {
                "op": "create",
                "entity": {
                    "kind": "roof",
                    "name": "Flat roof",
                    "storey": "ground",
                    "polygon": polygon,
                    "thickness": 200,
                    "base_height": 3000,
                },
            }
        ]
    )
    roof = next(e for e in doc.entities.values() if e["kind"] == "roof")
    assert roof["id"].startswith("ak_") and roof["form"] == "flat"
    with pytest.raises(ArchitectureError, match="flat"):
        doc.apply([{"op": "update", "id": roof["id"], "changes": {"form": "gable"}}])


def test_revision_conflicts_and_project_has_no_implicit_jurisdiction():
    doc = house()
    assert all(v is None for v in doc.to_dict()["project"]["jurisdiction"].values())
    for value in (0, True, "1"):
        with pytest.raises(ArchitectureError) as exc:
            doc.undo(value)
        assert exc.value.code == "ak_conflict"
    doc.apply(
        [
            {
                "op": "project",
                "changes": {"jurisdiction": {"country": "NZ"}, "facts": {"note": "owner supplied"}},
            }
        ]
    )
    assert doc.to_dict()["project"]["jurisdiction"] == {
        "country": "NZ",
        "region": None,
        "municipality": None,
    }
    assert "facts" not in doc.summary()["project"]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(units="m"),
        lambda d: d.update(schema="unknown"),
        lambda d: d.update(revision=-1),
        lambda d: d.update(extra=True),
        lambda d: d["history"][0].update(units="m"),
        lambda d: d["history"][0].update(revision=100),
        lambda d: d["entities"].update(wall=[]),
        lambda d: d["project"].update(facts={"bad": float("nan")}),
    ],
)
def test_malformed_saved_state_and_history_refuse(mutate):
    data = house().to_dict()
    mutate(data)
    with pytest.raises(ArchitectureError):
        Document.from_dict(data)


def test_bounds_duplicate_id_and_json_metadata():
    doc = house()
    before = doc.to_dict()
    invalid = [
        [],
        [{"op": "delete", "id": "missing"}],
        [{"op": "create", "entity": wall()}],
        [{"op": "create", "entity": {**storey(), "id": "../bad"}}],
        [{"op": "update", "id": "wall", "changes": {"properties": {"large": "x" * 17000}}}],
        [{"op": "update", "id": "wall", "changes": {"properties": {"tuple": (1, 2)}}}],
    ]
    for operations in invalid:
        with pytest.raises(ArchitectureError):
            doc.apply(operations)
        assert doc.to_dict() == before
    for i in range(MAX_HISTORY + 3):
        doc.apply([{"op": "project", "changes": {"name": f"Revision {i}"}}])
    assert len(doc.to_dict()["history"]) == MAX_HISTORY
    assert Document.from_dict(copy.deepcopy(doc.to_dict())).validate()["ok"]
