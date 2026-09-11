"""The architectural lane uses existing TEE permissions, jobs and compact interfaces."""

import json
import threading
import time

import pytest
from tee.app import TeeApp
from tee.architecture.tools import register_architecture_tools
from tee.kernel import trust, trustctx
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.kernel.jobs import JobManager


@pytest.fixture
def app(tmp_path):
    trustctx.install("live-turn", ())
    instance = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    register_architecture_tools(instance, tmp_path)
    yield instance
    instance.shutdown()
    trustctx.install("content-derived", ())


def wait(app, job):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        result = app.jobs.status(job)
        if result["state"] not in ("queued", "running"):
            return result
        time.sleep(0.01)
    pytest.fail("owned architecture job timed out")


def test_readiness_does_not_create_model_or_launch_gui(app, tmp_path):
    before = list(tmp_path.rglob("architecture"))
    status = app.registry.call("ak_status", {})
    assert status["product"] == "archkiln" and status["models"] == []
    prepared = app.registry.call("ak_open", {})
    assert prepared["prepared"] and not prepared["launched"]
    assert getattr(app, "architecture_gui", None) is None
    assert list(tmp_path.rglob("architecture")) == before


def test_batch_edit_query_undo_and_job_export(app):
    created = app.registry.call(
        "ak_create", {"name": "Integrated fixture", "preset": "compact-house"}
    )
    model_id = created["model_id"]
    initial = app.registry.call("ak_query", {"model_id": model_id})
    assert len(initial["entities"]) == 15 and "history" not in initial
    edited = app.registry.call(
        "ak_edit",
        {
            "model_id": model_id,
            "expected_revision": 1,
            "operations": [{"op": "update", "id": "east_window", "changes": {"width": 1500}}],
        },
    )
    assert edited["revision"] == 2
    with pytest.raises(TeeError, match="revision"):
        app.registry.call(
            "ak_edit",
            {
                "model_id": model_id,
                "expected_revision": 1,
                "operations": [{"op": "update", "id": "east_window", "changes": {"width": 1400}}],
            },
        )
    app.registry.call("ak_undo", {"model_id": model_id, "expected_revision": 2})
    query = app.registry.call("ak_query", {"model_id": model_id, "entity_id": "east_window"})
    assert query["entity"]["width"] == 1800
    job = app.registry.call("ak_export", {"model_id": model_id, "format": "json"})
    completed = wait(app, job["job"])
    assert completed["state"] == "done" and completed["result"]["ok"]
    assert completed["result"]["regulatory_status"] == "not_verified"


def test_all_architecture_tools_are_tabled_individually():
    expected = {
        "ak_status": "read-state",
        "ak_create": "write-artifacts",
        "ak_edit": "write-artifacts",
        "ak_query": "read-state",
        "ak_undo": "write-artifacts",
        "ak_import": "write-artifacts",
        "ak_candidates": "read-extract",
        "ak_promote": "write-artifacts",
        "ak_export": "write-artifacts",
        "ak_check": "read-compute",
        "ak_open": "call-engine",
    }
    for name, capability in expected.items():
        assert trust.capability_for(name) == capability
    with pytest.raises(TeeError, match="no capability"):
        trust.capability_for("ak_untabled_escape")


def test_broken_grants_block_mutation_but_keep_status(app, tmp_path):
    (tmp_path / ".tee").mkdir(exist_ok=True)
    (tmp_path / ".tee/config.toml").write_text('[trust]\ngrants=["unknown-capability"]\n')
    assert app.registry.call("ak_status", {})["ok"]
    with pytest.raises(TeeError, match="trust"):
        app.registry.call("ak_create", {"name": "Should refuse"})


def test_queued_export_rechecks_permission_before_writing(app, tmp_path):
    model_id = app.registry.call("ak_create", {"name": "Queue fixture"})["model_id"]
    app.jobs.shutdown()
    app.jobs = JobManager(workers=1)
    gate = threading.Event()
    app.jobs.submit("occupied", lambda: (gate.wait(3), {"ok": True})[1])
    job = app.registry.call("ak_export", {"model_id": model_id, "format": "json"})
    (tmp_path / ".tee/config.toml").write_text('[trust]\ngrants=["unknown-capability"]\n')
    gate.set()
    result = wait(app, job["job"])
    assert result["state"] == "error"
    assert not (tmp_path / "output/archkiln").exists()


def test_arbitrary_code_and_traversal_are_not_edit_operations(app):
    model_id = app.registry.call("ak_create", {"name": "Refusal fixture"})["model_id"]
    with pytest.raises(TeeError):
        app.registry.call(
            "ak_edit", {"model_id": model_id, "operations": [{"op": "exec", "code": "print(1)"}]}
        )
    with pytest.raises(TeeError):
        app.registry.call("ak_query", {"model_id": "../../other"})
    assert "print(1)" not in json.dumps(app.registry.call("ak_query", {"model_id": model_id}))


def test_cancelled_running_import_does_not_publish_candidates(app, tmp_path, monkeypatch):
    model = app.registry.call("ak_create", {"name": "Cancelled import"})["model_id"]
    (tmp_path / "scan.xyz").write_text("0 0 0\n")
    entered, release, returned = threading.Event(), threading.Event(), threading.Event()

    def proposal(*args, **kwargs):
        entered.set()
        release.wait(3)
        returned.set()
        return {"candidates": []}

    monkeypatch.setattr("tee.architecture.imports.inspect_source", lambda *a, **kw: {})
    monkeypatch.setattr("tee.architecture.imports.propose", proposal)
    job = app.registry.call(
        "ak_import",
        {
            "model_id": model,
            "path": "scan.xyz",
            "units": "mm",
            "tolerance_mm": 1,
        },
    )
    assert entered.wait(3)
    assert app.jobs.cancel(job["job"])["state"] == "cancelled"
    release.set()
    assert returned.wait(3)
    app.jobs.shutdown()
    assert not list((tmp_path / ".tee/architecture" / model).glob("imports/*.json"))


def test_cancelled_export_retains_partial_files_without_success_manifest(app, monkeypatch):
    model = app.architecture.create("Partial export")["model_id"]
    entered, release = threading.Event(), threading.Event()

    def drawing(state, folder):
        (folder / "partial.svg").write_text("<svg/>")
        entered.set()
        release.wait(3)
        return {"ok": True}

    monkeypatch.setattr("tee.architecture.drawings.export_drawings", drawing)
    job = app.registry.call("ak_export", {"model_id": model, "format": "drawings"})
    assert entered.wait(3)
    app.jobs.cancel(job["job"])
    release.set()
    app.jobs.shutdown()
    root = app.architecture.project / "output/archkiln" / model
    assert list(root.glob("*/partial.svg"))
    assert not list(root.glob("*/manifest.json"))
