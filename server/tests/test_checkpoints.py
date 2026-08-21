import pytest

from tee.kernel.adapter import FakeAdapter
from tee.kernel.checkpoints import CheckpointManager
from tee.kernel.errors import TeeError


def test_create_and_rollback_by_id_and_label():
    fake = FakeAdapter()
    mgr = CheckpointManager()
    fake.execute([{"op": "create", "kind": "mesh", "name": "A"}])
    cp1 = mgr.create(fake, "after-A", revision=1)
    fake.execute([{"op": "create", "kind": "mesh", "name": "B"}])
    mgr.create(fake, "after-B", revision=2)
    fake.execute([{"op": "delete", "id": "e1"}])

    restored = mgr.rollback(fake, "after-A")
    assert restored.id == cp1.id
    assert [e.name for e in fake.list_entities()] == ["A"]
    # later checkpoints were discarded
    labels = [c["label"] for c in mgr.list("fake")]
    assert labels == ["after-A"]


def test_rollback_unknown_ref_lists_recent():
    fake = FakeAdapter()
    mgr = CheckpointManager()
    mgr.create(fake, "known", revision=0)
    with pytest.raises(TeeError) as err:
        mgr.rollback(fake, "nope")
    assert err.value.code == "unknown_checkpoint"
    assert "known" in (err.value.fix or "")


def test_retention_is_bounded():
    fake = FakeAdapter()
    mgr = CheckpointManager(keep=3)
    for i in range(6):
        mgr.create(fake, f"cp-{i}", revision=i)
    labels = [c["label"] for c in mgr.list("fake")]
    assert labels == ["cp-3", "cp-4", "cp-5"]
