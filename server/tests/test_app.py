import pytest

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError


@pytest.fixture()
def app(tmp_path):
    application = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    yield application
    application.shutdown()


def test_run_batch_checkpoints_then_applies(app):
    out = app.run_batch("fake", [{"op": "create", "kind": "mesh", "name": "Cube"}])
    assert out["ok"] is True
    assert out["created"] == ["e1"]
    assert out["checkpoint"] == "cp1"
    assert out["revision"] == app.cache("fake").revision
    # the checkpoint captured the state BEFORE the batch
    rolled = app.rollback("fake", "cp1")
    assert rolled["ok"] is True
    assert app.adapters["fake"].list_entities() == []


def test_rollback_bumps_epoch_and_resyncs(app):
    app.run_batch("fake", [{"op": "create", "kind": "mesh", "name": "A"}])
    stamp_before = app.cache("fake").stamp()
    app.run_batch("fake", [{"op": "create", "kind": "mesh", "name": "B"}])
    app.rollback("fake", "cp2")  # back to before B
    cache = app.cache("fake")
    assert cache.epoch > stamp_before["epoch"]
    assert [e.name for e in cache.entities.values()] == ["A"]
    delta = cache.diff_since(stamp_before["epoch"], stamp_before["revision"])
    assert delta["resync_required"] is True


def test_unknown_adapter_and_disconnected_adapter(app):
    with pytest.raises(TeeError) as err:
        app.adapter("blender")
    assert err.value.code == "unknown_adapter"
    app.adapters["fake"].disconnect()
    with pytest.raises(TeeError) as err:
        app.adapter("fake")
    assert err.value.code == "adapter_unavailable"


def test_status_reports_adapters_and_checkpoints(app):
    app.run_batch("fake", [{"op": "create", "kind": "mesh", "name": "A"}])
    status = app.status()
    assert status["adapters"]["fake"]["connected"] is True
    assert status["adapters"]["fake"]["scene"]["revision"] >= 1
    assert status["checkpoints"][-1]["label"].startswith("auto:batch")
    assert status["active_jobs"] == []


def test_failed_batch_is_atomic_and_cache_stays_truthful(app):
    app.run_batch("fake", [{"op": "create", "kind": "mesh", "name": "A"}])
    stamp = app.cache("fake").stamp()
    with pytest.raises(TeeError) as err:
        app.run_batch(
            "fake",
            [
                {"op": "create", "kind": "mesh", "name": "Orphan"},
                {"op": "set", "id": "no-such-id", "props": {}},
            ],
        )
    assert "rolled back" in (err.value.fix or "")
    # adapter and cache agree: the orphan never happened
    names = [e.name for e in app.adapters["fake"].list_entities()]
    assert names == ["A"]
    assert app.cache("fake").summary()["total"] == 1
    delta = app.cache("fake").diff_since(stamp["epoch"], stamp["revision"])
    assert delta.get("resync_required") is None
    assert delta.get("created") is None


def test_cold_cache_with_prepopulated_adapter_is_warmed(tmp_path):
    fake = FakeAdapter()
    fake.execute(
        [
            {"op": "create", "kind": "mesh", "name": "PreA"},
            {"op": "create", "kind": "mesh", "name": "PreB"},
        ]
    )
    application = TeeApp({"fake": fake}, project_root=tmp_path)
    try:
        stamp = application.status()["adapters"]["fake"]["scene"]
        out = application.run_batch("fake", [{"op": "create", "kind": "mesh", "name": "New"}])
        delta = application.cache("fake").diff_since(stamp["epoch"], stamp["revision"])
        assert delta.get("resync_required") is None
        assert delta["created"] == out["created"]
        assert application.cache("fake").summary()["total"] == 3
    finally:
        application.shutdown()


def test_status_reports_code_exec_flag(app):
    assert app.status()["code_exec_enabled"] is False


def test_trim_batch_echoes_reports_drift_not_echoes():
    from tee.app import _trim_batch_echoes

    ops = [
        {"op": "create", "kind": "cube", "name": "A", "props": {"location": [0, 0, 0]}},
        {"op": "set", "id": "e9", "props": {"scale": 2}},
    ]
    payload = {
        "created": ["e1"],
        "modified": ["e9"],
        "details": {
            "e1": {"id": "e1", "name": "A.001", "kind": "mesh", "location": [0, 0, 1e-7]},
            "e9": {"id": "e9", "name": "B", "scale": 2, "dimensions": [2, 2, 2]},
        },
    }
    prior = {"e9": {"id": "e9", "name": "B", "scale": 1, "dimensions": [1, 1, 1]}}
    _trim_batch_echoes(ops, payload, prior)
    # the adapter renamed A -> A.001: the names map carries the truth; the
    # location echo (within float tolerance) is gone; kind differs from the
    # creation recipe so it stays
    assert payload["names"] == {"e1": "A.001"}
    assert payload["details"]["e1"] == {"kind": "mesh"}
    # set: scale echo and unchanged re-reports dropped; the computed side
    # effect (dimensions doubled) is the news and stays
    assert payload["details"]["e9"] == {"dimensions": [2, 2, 2]}


def test_trim_batch_echoes_skips_request_mapping_when_unaligned():
    from tee.app import _trim_batch_echoes

    ops = [{"op": "create", "kind": "scatter", "name": "S", "props": {"location": [1, 1, 1]}}]
    payload = {
        "created": ["e1", "e2"],
        "details": {
            "e1": {"id": "e1", "name": "S", "location": [1, 1, 1]},
            "e2": {"id": "e2", "name": "S.001", "location": [2, 1, 1]},
        },
    }
    _trim_batch_echoes(ops, payload, {})
    # one op yielded two entities: no positional request mapping, so nothing
    # is guessed - ids/names still compact, locations stay reported
    assert payload["names"] == {"e1": "S", "e2": "S.001"}
    assert payload["details"]["e1"] == {"location": [1, 1, 1]}
    assert payload["details"]["e2"] == {"location": [2, 1, 1]}
