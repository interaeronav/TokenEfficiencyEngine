import pytest

from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError


def test_create_set_delete_roundtrip():
    fake = FakeAdapter()
    diff = fake.execute(
        [
            {"op": "create", "kind": "mesh", "name": "Cube", "props": {"verts": 8}},
            {"op": "create", "kind": "light", "name": "Sun"},
        ]
    )
    assert diff.created == ["e1", "e2"]
    assert diff.details["e1"]["verts"] == 8
    assert [e.id for e in diff.upserts] == ["e1", "e2"]

    diff = fake.execute([{"op": "set", "id": "e1", "props": {"verts": 26, "name": "Donut"}}])
    assert diff.modified == ["e1"]
    assert diff.details["e1"]["name"] == "Donut"

    diff = fake.execute([{"op": "delete", "id": "e2"}])
    assert diff.deleted == ["e2"]
    assert len(fake.list_entities()) == 1


def test_create_then_set_in_one_batch_reports_created_only():
    fake = FakeAdapter()
    diff = fake.execute(
        [
            {"op": "create", "kind": "mesh", "name": "Cube"},
            {"op": "set", "id": "e1", "props": {"x": 1}},
        ]
    )
    assert diff.created == ["e1"]
    assert diff.modified == []
    assert diff.details["e1"]["x"] == 1
    assert len(diff.upserts) == 1


def test_unknown_op_and_unknown_entity_raise_short_errors():
    fake = FakeAdapter()
    with pytest.raises(TeeError) as err:
        fake.execute([{"op": "explode"}])
    assert err.value.code == "bad_op"
    with pytest.raises(TeeError) as err:
        fake.execute([{"op": "set", "id": "nope", "props": {}}])
    assert err.value.code == "unknown_entity"


def test_snapshot_restore_restores_store_and_id_counter():
    fake = FakeAdapter()
    fake.execute([{"op": "create", "kind": "mesh", "name": "A"}])
    snap = fake.snapshot("before")
    fake.execute([{"op": "create", "kind": "mesh", "name": "B"}])
    fake.execute([{"op": "delete", "id": "e1"}])
    fake.restore(snap)
    ents = fake.list_entities()
    assert [e.name for e in ents] == ["A"]
    diff = fake.execute([{"op": "create", "kind": "mesh", "name": "C"}])
    assert diff.created == ["e2"]  # counter restored, no id reuse


def test_set_does_not_mutate_caller_op():
    fake = FakeAdapter()
    fake.execute([{"op": "create", "kind": "mesh", "name": "A"}])
    op = {"op": "set", "id": "e1", "props": {"name": "B", "x": 1}}
    fake.execute([op])
    assert op["props"] == {"name": "B", "x": 1}  # caller's dict untouched


def test_create_then_delete_in_one_batch_nets_to_nothing():
    fake = FakeAdapter()
    diff = fake.execute(
        [
            {"op": "create", "kind": "mesh", "name": "Temp"},
            {"op": "delete", "id": "e1"},
        ]
    )
    assert diff.created == []
    assert diff.deleted == []
    assert diff.modified == []
    assert fake.list_entities() == []
