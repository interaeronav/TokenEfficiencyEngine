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
