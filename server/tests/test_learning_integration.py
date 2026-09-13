"""Learning observes execution without gaining authority or retaining content."""

from __future__ import annotations

import time

import pytest

from tee.app import TeeApp
from tee.config import ProjectConfig
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool
from tee.learning.hooks import tool_version


@pytest.fixture
def app(tmp_path):
    instance = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    yield instance
    instance.shutdown()


def register(app, name="test_observed", handler=None, capability="read-session"):
    tool = VirtualTool(
        name,
        "Execution observation fixture",
        {"type": "object", "properties": {"text": {"type": "string"}}},
        handler or (lambda _: {"ok": True, "result": {"passed": True}}),
        capability=capability,
        lane="fake" if capability == "exec-code" else None,
    )
    app.registry.register(tool)
    return tool


def rows(app):
    return app.learning.recent(20)


def test_payloads_and_errors_never_enter_learning_store(app):
    secret = "USER_PAYLOAD_SENTINEL_NEVER_STORE_386491"
    register(app, handler=lambda _: {"ok": True, "text": secret, "passed": True})
    app.registry.call("test_observed", {"text": secret})

    def fail(_):
        raise TeeError("unexpected_" + secret, secret, fix=secret)

    register(app, "test_failure", fail)
    with pytest.raises(TeeError):
        app.registry.call("test_failure", {"text": secret})
    with pytest.raises(TeeError):
        app.registry.call(secret, {})
    observed = rows(app)
    assert len(observed) == 3
    assert {row["domain"] for row in observed} == {"execution"}
    assert {row["choice"] for row in observed} == {"test_observed", "test_failure", "unknown"}
    for path in (app.project_root / ".tee" / "learning").rglob("*"):
        if path.is_file():
            assert secret.encode() not in path.read_bytes()


def test_observer_failure_leaves_success_and_original_exception_unchanged(app, monkeypatch):
    register(app)

    def broken(**_):
        raise OSError("unwritable storage")

    monkeypatch.setattr(app.learning, "observe", broken)
    assert app.registry.call("test_observed", {})["ok"]

    def fail(_):
        raise TeeError("fixture_error", "original")

    register(app, "test_failure", fail)
    with pytest.raises(TeeError, match="original") as error:
        app.registry.call("test_failure", {})
    assert error.value.code == "fixture_error"


def test_refusals_never_become_verified_failures(app):
    touched = []
    register(app, handler=lambda _: touched.append(True), capability="exec-code")
    with pytest.raises(TeeError):
        app.registry.call("test_observed", {})
    assert not touched
    row = rows(app)[0]
    assert row["success"] is None and row["category"] == "refused"
    assert row["domain"] == "execution"


def test_nested_batch_has_one_observation_but_direct_batch_gets_its_own(app):
    operation = [{"op": "create", "kind": "cube", "name": "fixture"}]
    register(app, handler=lambda _: app.run_batch("fake", operation))
    app.registry.call("test_observed", {})
    assert len(rows(app)) == 1
    assert rows(app)[0]["choice"] == "test_observed"
    app.run_batch("fake", operation)
    assert len(rows(app)) == 2
    assert sum(row["context"] == "batch" for row in rows(app)) == 1


def test_queued_reply_is_unknown_and_completion_is_observed(app):
    register(app, handler=lambda _: {"job": "fixture", "state": "queued"})
    app.registry.call("test_observed", {})
    assert rows(app)[0]["success"] is None
    job = app.jobs.submit("PRIVATE JOB LABEL", lambda: {"passed": True})
    deadline = time.monotonic() + 3
    while not any(row["context"] == "job" for row in rows(app)):
        assert time.monotonic() < deadline
        time.sleep(0.01)
    assert app.jobs.status(job)["state"] == "done"
    completed = next(row for row in rows(app) if row["context"] == "job")
    assert completed["success"] is True and completed["domain"] == "execution"
    assert "PRIVATE JOB LABEL" not in repr(rows(app))


def test_learning_tools_are_not_observations(app):
    for tool, args in [
        ("learn_status", {}),
        ("learn_evaluate", {}),
        ("learn_control", {"action": "pause"}),
    ]:
        app.registry.call(tool, args)
    assert rows(app) == []


def test_cached_version_changes_without_probing(app):
    tool = register(app)
    before = tool_version(app, tool)
    tool.lane = "fake"
    app.adapters["fake"]._version = (5, 2, 0)
    current = tool_version(app, tool)
    app.adapters["fake"]._version = (5, 3, 0)
    assert len({before, current, tool_version(app, tool)}) == 3


def test_routed_tool_fingerprint_covers_served_versions(app):
    from tee.kernel.lanes import ADAPTER_ARG

    tool = register(app)
    tool.lane = ADAPTER_ARG
    app.adapters["fake"]._version = (5, 2, 0)
    before = tool_version(app, tool)
    app.adapters["fake"]._version = (5, 3, 0)
    assert tool_version(app, tool) != before


@pytest.mark.parametrize(
    "code",
    ["refused", "job_refused_admission", "job_backpressure", "trust_denied", "llm_unreachable"],
)
def test_async_refusal_or_network_error_never_becomes_failure_label(app, code):
    def fail():
        raise TeeError(code, "private details")

    job = app.jobs.submit("private label", fail)
    deadline = time.monotonic() + 3
    while not rows(app):
        assert time.monotonic() < deadline
        time.sleep(0.01)
    assert app.jobs.status(job)["state"] == "error"
    assert rows(app)[0]["success"] is None


def test_async_error_reply_and_implementation_identity(app):
    def fail():
        return {"ok": False, "error": "failure details"}

    def succeed():
        return {"ok": True}

    app.jobs.submit("private failure", fail)
    app.jobs.submit("private success", succeed)
    deadline = time.monotonic() + 3
    while len(rows(app)) < 2:
        assert time.monotonic() < deadline
        time.sleep(0.01)
    assert {row["success"] for row in rows(app)} == {True, False}
    assert len({row["version"] for row in rows(app)}) == 2


def test_blender_python_guard_refusal_is_unlabelled(app):
    from tee.adapters.blender.adapter import BlenderAdapter

    adapter = BlenderAdapter(wire=object())
    register(app, handler=lambda _: adapter.validate_python("bpy.ops.wm.read_factory_settings()"))
    with pytest.raises(TeeError):
        app.registry.call("test_observed", {})
    assert rows(app)[0]["success"] is None
    assert rows(app)[0]["category"] == "refused"


def test_explicit_learning_disable_is_loaded_and_writes_nothing(tmp_path):
    folder = tmp_path / ".tee"
    folder.mkdir()
    (folder / "config.toml").write_text("[learning]\nenabled = false\n")
    assert ProjectConfig.load(tmp_path).learning == {"enabled": False}
    instance = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    register(instance)
    instance.registry.call("test_observed", {})
    assert not (folder / "learning").exists()
    instance.shutdown()
