from tee.kernel.adapter import Diff, Entity, FakeAdapter
from tee.kernel.scene_cache import SceneCache


def ent(eid: str, name: str | None = None, kind: str = "mesh") -> Entity:
    return Entity(id=eid, name=name or eid, kind=kind)


def test_apply_diff_and_diff_since_returns_delta():
    cache = SceneCache()
    stamp = cache.stamp()
    cache.apply_diff(Diff(created=["a"]), [ent("a")])
    cache.apply_diff(Diff(created=["b"]), [ent("b")])
    delta = cache.diff_since(stamp["epoch"], stamp["revision"])
    assert delta.get("resync_required") is None
    assert delta["created"] == ["a", "b"]
    assert delta["revision"] == cache.revision


def test_diff_merging_nets_out_create_delete():
    cache = SceneCache()
    stamp = cache.stamp()
    cache.apply_diff(Diff(created=["a"], details={"a": {"x": 1}}), [ent("a")])
    cache.apply_diff(Diff(modified=["a"], details={"a": {"x": 2}}), [ent("a")])
    cache.apply_diff(Diff(deleted=["a"]), [])
    delta = cache.diff_since(stamp["epoch"], stamp["revision"])
    assert delta.get("created") is None
    assert delta.get("deleted") is None
    assert delta.get("modified") is None


def test_diff_merging_delete_then_recreate_is_modified():
    cache = SceneCache()
    cache.apply_diff(Diff(created=["a"]), [ent("a")])
    stamp = cache.stamp()
    cache.apply_diff(Diff(deleted=["a"]), [])
    cache.apply_diff(Diff(created=["a"], details={"a": {"x": 9}}), [ent("a")])
    delta = cache.diff_since(stamp["epoch"], stamp["revision"])
    assert delta["modified"] == ["a"]
    assert delta.get("created") is None
    assert delta["details"]["a"] == {"x": 9}


def test_user_edits_flagged():
    cache = SceneCache()
    stamp = cache.stamp()
    cache.apply_diff(Diff(modified=["a"]), [ent("a")], source="user")
    delta = cache.diff_since(stamp["epoch"], stamp["revision"])
    assert delta["user_edits"] is True


def test_epoch_mismatch_demands_resync():
    cache = SceneCache()
    stamp = cache.stamp()
    cache.invalidate()
    delta = cache.diff_since(stamp["epoch"], stamp["revision"])
    assert delta["resync_required"] is True


def test_future_revision_demands_resync():
    cache = SceneCache()
    delta = cache.diff_since(cache.epoch, cache.revision + 5)
    assert delta["resync_required"] is True


def test_pruned_history_demands_resync():
    cache = SceneCache()
    stamp = cache.stamp()
    for _ in range(250):  # exceeds the 200-entry log bound
        cache.apply_diff(Diff(modified=["a"]), [ent("a")])
    delta = cache.diff_since(stamp["epoch"], stamp["revision"])
    assert delta["resync_required"] is True


def test_resync_from_adapter_bumps_epoch():
    fake = FakeAdapter()
    fake.execute([{"op": "create", "kind": "mesh", "name": "A"}])
    cache = SceneCache()
    before = cache.stamp()
    cache.resync(fake)
    assert cache.epoch == before["epoch"] + 1
    assert set(cache.entities) == {"e1"}


def test_summary_filters_pages_and_truncates():
    cache = SceneCache()
    for i in range(30):
        kind = "mesh" if i % 2 == 0 else "light"
        cache.apply_diff(Diff(created=[f"e{i}"]), [ent(f"e{i}", f"Obj{i}", kind)])
    s = cache.summary(limit=5, offset=0, kind="mesh")
    assert s["total"] == 15
    assert len(s["entities"]) == 5
    assert "truncated" in s and "offset=5" in s["truncated"]
    assert s["kinds"] == {"mesh": 15, "light": 15}
    s2 = cache.summary(name_contains="obj1", limit=50)
    assert s2["total"] == 11  # Obj1, Obj10..Obj19
