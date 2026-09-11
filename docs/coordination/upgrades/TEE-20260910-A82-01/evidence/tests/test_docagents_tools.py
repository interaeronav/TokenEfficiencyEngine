"""Documentation workers preserve host permissions, pins and review boundaries."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from tee.app import TeeApp
from tee.docagents import tools
from tee.kernel import trust, trustctx
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.kernel.jobs import JobManager


@pytest.fixture
def project(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/api.py").write_text("def greet(name):\n    return 'Hello ' + name\n")
    (tmp_path / "README.md").write_text("# Example\n")
    (tmp_path / ".tee").mkdir()
    return tmp_path


def configure(root, grants=(), *, paid=True):
    (root / ".tee/config.toml").write_text(
        "[trust]\ngrants = " + json.dumps(list(grants)) + "\n"
        '[llm.profiles.qmax]\nmodel="declared-model"\nurl="http://127.0.0.1:4000/v1"\n'
        + f"paid={str(paid).lower()}\n"
    )
    (root / ".tee/llm-profile.json").write_text(
        json.dumps({"active": "qmax", "pinned": True, "ready": True})
    )


@pytest.fixture
def make_app(project):
    instances = []
    trustctx.install("live-turn", ())

    def factory(grants=(), paid=True):
        configure(project, grants, paid=paid)
        app = TeeApp({"fake": FakeAdapter()}, project_root=project)
        tools.register_documentation_tools(app, project)
        instances.append(app)
        return app

    yield factory
    for app in instances:
        app.shutdown()
    trustctx.install("content-derived", ())


def prepared(app):
    return app.registry.call(
        "doc_prepare",
        {
            "inputs": ["src/api.py"],
            "outputs": ["README.md"],
            "instruction": "Document greet with an example backed by the source.",
        },
    )["run_id"]


def done(app, job):
    until = time.monotonic() + 5
    while time.monotonic() < until:
        result = app.jobs.status(job)
        if result["state"] not in ("running", "queued"):
            return result
        time.sleep(0.01)
    pytest.fail("documentation fixture job did not finish")


@pytest.fixture
def fake_worker(monkeypatch):
    calls = []
    monkeypatch.setattr(
        tools.backends,
        "discover",
        lambda: {
            "cline": {"available": True},
            "aider": {"available": True},
        },
    )

    def plan(backend, manifest, profile, **kwargs):
        calls.append((backend, profile.copy(), kwargs.copy()))
        return SimpleNamespace(manifest=manifest)

    class Worker:
        def cancel(self):
            pass

        def run(self, plan, run_dir, **kwargs):
            (Path(plan.manifest["work_dir"]) / "README.md").write_text(
                "# Example\n\n`greet(name)` returns `Hello ` followed by the name.\n"
            )
            return {"ok": True, "usage": None, "exit_code": 0}

    monkeypatch.setattr(tools.backends, "build_plan", plan)
    monkeypatch.setattr(tools, "Worker", Worker)
    return calls


@pytest.mark.parametrize("grants", [(), ("call-paid-engine",), ("exec-code",)])
def test_other_grants_do_not_authorize_agent_execution(make_app, fake_worker, grants):
    app = make_app(grants)
    task = prepared(app)
    with pytest.raises(TeeError, match="run-doc-agent"):
        app.registry.call("doc_run", {"run_id": task, "backend": "aider"})
    assert not fake_worker


def test_loopback_paid_route_still_requires_paid_grant(make_app, fake_worker):
    app = make_app(("run-doc-agent",))
    with pytest.raises(TeeError, match="call-paid-engine"):
        app.registry.call("doc_run", {"run_id": prepared(app), "backend": "cline"})
    assert not fake_worker


def test_tainted_worker_call_is_denied_even_with_grants(make_app, fake_worker):
    app = make_app(("run-doc-agent", "call-paid-engine"))
    task = prepared(app)
    trustctx.add_taint("untrusted-web-result")
    with pytest.raises(TeeError, match="untrusted"):
        app.registry.call("doc_run", {"run_id": task, "backend": "aider"})
    assert not fake_worker


def test_worker_preserves_pin_and_requires_separate_review_apply(make_app, fake_worker, project):
    app = make_app(("run-doc-agent", "call-paid-engine"))
    pin = (project / ".tee/llm-profile.json").read_bytes()
    task = prepared(app)
    queued = app.registry.call("doc_run", {"run_id": task, "backend": "aider"})
    assert queued["state"] == "queued" and not queued["applied"]
    result = done(app, queued["job"])
    assert result["state"] == "done" and result["result"]["ok"]
    assert (project / "README.md").read_text() == "# Example\n"
    assert fake_worker[0][1]["profile"] == "qmax"
    assert fake_worker[0][1]["paid"] is True
    assert fake_worker[0][2]["authorized"] is True
    assert (project / ".tee/llm-profile.json").read_bytes() == pin
    review = app.registry.call("doc_diff", {"run_id": task})
    assert review["changes"]
    applied = app.registry.call(
        "doc_apply",
        {
            "run_id": task,
            "review_sha256": review["review_sha256"],
        },
    )
    assert applied["ok"] and "greet" in (project / "README.md").read_text()


def occupy(app):
    app.jobs.shutdown()
    app.jobs = JobManager(workers=1)
    gate = threading.Event()
    app.jobs.submit("occupied", lambda: (gate.wait(5), {"ok": True})[1])
    return gate


def test_grant_revocation_while_queued_prevents_spawn(make_app, fake_worker, project):
    app = make_app(("run-doc-agent", "call-paid-engine"))
    gate = occupy(app)
    task = prepared(app)
    queued = app.registry.call("doc_run", {"run_id": task, "backend": "cline"})
    configure(project, ("call-paid-engine",))
    gate.set()
    result = done(app, queued["job"])
    assert result["state"] == "error" and "run-doc-agent" in result["error"]
    assert not fake_worker


def test_profile_change_while_queued_never_silently_reroutes(make_app, fake_worker, project):
    app = make_app(("run-doc-agent", "call-paid-engine"))
    gate = occupy(app)
    task = prepared(app)
    queued = app.registry.call("doc_run", {"run_id": task, "backend": "cline"})
    state = project / ".tee/llm-profile.json"
    state.write_text(json.dumps({"active": "q14b", "pinned": True, "ready": True}))
    gate.set()
    result = done(app, queued["job"])
    assert result["state"] == "error" and "doc_profile_changed" in result["error"]
    assert not fake_worker
    assert json.loads(state.read_text())["active"] == "q14b"


def test_cancelled_queued_task_can_be_submitted_again(make_app, fake_worker):
    app = make_app(("run-doc-agent", "call-paid-engine"))
    gate = occupy(app)
    task = prepared(app)
    first = app.registry.call("doc_run", {"run_id": task, "backend": "aider"})
    app.jobs.cancel(first["job"])
    second = app.registry.call("doc_run", {"run_id": task, "backend": "aider"})
    gate.set()
    assert done(app, second["job"])["result"]["ok"]
    assert len(fake_worker) == 1


def test_cancel_after_scheduler_start_before_execute_refuses_retry(
    make_app, fake_worker, project, monkeypatch
):
    app = make_app(("run-doc-agent", "call-paid-engine"))
    task = prepared(app)
    entered, release = threading.Event(), threading.Event()
    original_install = trustctx.install

    def pause_before_execute(caller, taint):
        # JobManager marks the job running before installing its carried
        # context; DocumentationLane.execute has not set its started event yet.
        if caller == "job":
            entered.set()
            assert release.wait(3)
        return original_install(caller, taint)

    monkeypatch.setattr(trustctx, "install", pause_before_execute)
    queued = app.registry.call("doc_run", {"run_id": task, "backend": "aider"})
    try:
        assert entered.wait(3)
        assert app.jobs.status(queued["job"])["state"] == "running"
        app.jobs.cancel(queued["job"])
        run_dir = Path(tools.DocWorkspace(project).load(task)["run_dir"])
        assert (run_dir / ".worker-cancelled").exists()
        assert not (run_dir / ".worker-started").exists()
        with pytest.raises(TeeError) as error:
            app.registry.call("doc_run", {"run_id": task, "backend": "cline"})
        assert error.value.code == "doc_run_used"
        assert not fake_worker
    finally:
        release.set()
        deadline = time.monotonic() + 3
        while app.jobs._jobs[queued["job"]].finished_at is None:
            assert time.monotonic() < deadline
            time.sleep(0.01)


def test_new_capability_is_explicit_high_risk_and_not_a_baseline():
    assert "run-doc-agent" in trust.HIGH_RISK
    assert "run-doc-agent" in trust.TAINT_ENFORCED
    assert "run-doc-agent" not in trust.BASELINE
    assert trust.capability_for("doc_run") == "run-doc-agent"
    assert trust.capability_for("doc_diff") in trust.TAINT_SOURCES


def test_apply_requires_a_completed_worker_even_if_staged_diff_is_valid(make_app, project):
    app = make_app()
    task = prepared(app)
    workspace = tools.DocWorkspace(project)
    manifest = workspace.load(task)
    (Path(manifest["work_dir"]) / "README.md").write_text("# Unexecuted candidate\n")
    review = app.registry.call("doc_diff", {"run_id": task})
    with pytest.raises(TeeError, match="completed worker"):
        app.registry.call(
            "doc_apply",
            {
                "run_id": task,
                "review_sha256": review["review_sha256"],
            },
        )
    assert (project / "README.md").read_text() == "# Example\n"


def test_completed_task_refuses_second_execution_before_touching_backend(make_app, fake_worker):
    app = make_app(("run-doc-agent", "call-paid-engine"))
    task = prepared(app)
    queued = app.registry.call("doc_run", {"run_id": task, "backend": "aider"})
    assert done(app, queued["job"])["result"]["ok"]
    with pytest.raises(TeeError, match="already executed"):
        app.registry.call("doc_run", {"run_id": task, "backend": "cline"})
    assert len(fake_worker) == 1


def test_late_cancellation_cannot_apply_valid_partial_documents(
    make_app,
    fake_worker,
    project,
    monkeypatch,
):
    app = make_app(("run-doc-agent", "call-paid-engine"))
    task = prepared(app)
    entered, release = threading.Event(), threading.Event()
    original = tools.DocWorkspace.diff

    def held_diff(self, *args, **kwargs):
        entered.set()
        release.wait(5)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(tools.DocWorkspace, "diff", held_diff)
    queued = app.registry.call("doc_run", {"run_id": task, "backend": "aider"})
    assert entered.wait(3)
    app.jobs.cancel(queued["job"])
    release.set()
    manifest = tools.DocWorkspace(project).load(task)
    marker = Path(manifest["run_dir"]) / ".worker-active"
    deadline = time.monotonic() + 3
    while marker.exists():
        assert time.monotonic() < deadline
        time.sleep(0.01)
    review = app.registry.call("doc_diff", {"run_id": task})
    with pytest.raises(TeeError, match="Cancelled"):
        app.registry.call(
            "doc_apply",
            {
                "run_id": task,
                "review_sha256": review["review_sha256"],
            },
        )
    assert (project / "README.md").read_text() == "# Example\n"


def test_diff_reserves_task_against_other_clients(make_app, project, monkeypatch):
    app = make_app()
    task = prepared(app)
    original = tools.DocWorkspace.diff

    def assert_reserved(self, *args, **kwargs):
        manifest = self.load(task)
        assert (Path(manifest["run_dir"]) / ".worker-active").is_file()
        return original(self, *args, **kwargs)

    monkeypatch.setattr(tools.DocWorkspace, "diff", assert_reserved)
    app.registry.call("doc_diff", {"run_id": task})
    manifest = tools.DocWorkspace(project).load(task)
    assert not (Path(manifest["run_dir"]) / ".worker-active").exists()


def test_explicit_worker_key_is_never_in_status(make_app, monkeypatch):
    app = make_app()
    monkeypatch.setenv("TEE_DOCAGENT_API_KEY", "PRIVATE_TEST_SENTINEL")
    status = app.registry.call("doc_status", {})
    assert "PRIVATE_TEST_SENTINEL" not in json.dumps(status)
    assert status["model"]["profile"] == "qmax"
