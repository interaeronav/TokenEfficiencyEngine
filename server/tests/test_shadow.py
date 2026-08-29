"""K0 shadow layer (A42 acceptance): descriptors and greedy choice, the
recorder's zero-behavior guarantees (off = silent no-op, failures
swallowed, config off-switch honored), traces flowing from the jobs and
router seams, and the recording overhead measured negligible."""

from __future__ import annotations

import json
import time

import pytest
from fixtures_llm import fake_llm_server
from test_llm_router import _by_model, _route

from tee.kernel import shadow
from tee.kernel.shadow import TaskDescriptor, greedy_choice


@pytest.fixture(autouse=True)
def _isolated_recorder():
    shadow.RECORDER.disable()
    yield
    shadow.RECORDER.disable()


def test_disabled_recorder_is_a_silent_noop(tmp_path):
    shadow.record(TaskDescriptor(id="x", kind="chore"), {"outcome": "verified"})
    assert list(tmp_path.iterdir()) == []
    assert shadow.RECORDER.recent() == []


def test_record_line_shape_and_delta(tmp_path):
    shadow.RECORDER.enable(tmp_path)
    shadow.record(
        TaskDescriptor(
            id="chore:triage",
            kind="chore",
            qos="interactive",
            engine="q14b+a2",
            verifier="deterministic",
            inputs=["fixture:none_guard"],
        ),
        {"outcome": "verified", "wall_s": 1.3, "_resident": "q14b+a2"},
    )
    (line,) = shadow.RECORDER.recent()
    assert line["task"]["id"] == "chore:triage"
    assert line["task"]["in"] == ["fixture:none_guard"]
    assert "_resident" not in line["actual"]  # context, not payload
    assert line["shadow"]["engine"] == "q14b+a2"
    assert line["delta"]["agrees"] is True
    assert line["delta"]["est_minus_actual_s"] == pytest.approx(-0.06, abs=0.01)


def test_greedy_choice_math():
    # resident 14B: 1.24 beats 90 + 6.38
    assert greedy_choice("chore", resident="q14b+a2")["engine"] == "q14b+a2"
    # resident 27B: staying (6.38) beats swapping to the 14B (30 + 1.24)
    assert greedy_choice("chore", resident="q27b-bare")["engine"] == "q27b-bare"
    job = greedy_choice("job", engine="reconstruct-odm")
    assert job["estimate_s"] == 260.0  # median of the measured [210, 310]
    assert greedy_choice("gateway", engine="fs")["estimate_s"] is None


def test_record_failure_is_swallowed(tmp_path):
    shadow.RECORDER.enable(tmp_path)
    tmp_path.chmod(0o000)
    try:
        shadow.record(TaskDescriptor(id="x", kind="chore"), {"outcome": "verified"})
    finally:
        tmp_path.chmod(0o755)
    assert shadow.RECORDER.recent() == []  # nothing written, nothing raised


def test_config_off_switch_and_default_on(tmp_path):
    from tee.app import TeeApp
    from tee.kernel.adapter import FakeAdapter

    off_project = tmp_path / "off"
    (off_project / ".tee").mkdir(parents=True)
    (off_project / ".tee" / "config.toml").write_text("[scheduler]\nshadow = false\n")
    app = TeeApp({"fake": FakeAdapter()}, project_root=off_project)
    assert shadow.RECORDER.enabled is False
    app.shutdown()

    on_project = tmp_path / "on"
    on_project.mkdir()
    app = TeeApp({"fake": FakeAdapter()}, project_root=on_project)
    assert shadow.RECORDER.enabled is True
    assert (on_project / ".tee" / "shadow").is_dir()
    app.shutdown()


def test_jobs_seam_emits_a_trace(tmp_path):
    from tee.app import TeeApp
    from tee.kernel.adapter import FakeAdapter

    project = tmp_path / "proj"
    project.mkdir()
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    job_id = app.jobs.submit(
        "probe", lambda: {"ok": True}, qos="batch", engine="reconstruct-photogrammetry"
    )
    deadline = time.time() + 10
    while time.time() < deadline and app.jobs.status(job_id)["state"] != "done":
        time.sleep(0.02)
    deadline = time.time() + 2
    while time.time() < deadline and not shadow.RECORDER.recent():
        time.sleep(0.02)  # the trace lands in the worker's finally
    (line,) = shadow.RECORDER.recent(1)
    assert line["task"]["kind"] == "job"
    assert line["task"]["engine"] == "reconstruct-photogrammetry"
    assert line["actual"]["outcome"] == "done"
    assert line["delta"]["est_minus_actual_s"] == pytest.approx(12.0, abs=1.0)
    app.shutdown()


def test_router_seam_emits_a_trace(tmp_path):
    shadow.RECORDER.enable(tmp_path / "sh")
    with fake_llm_server(_by_model({"fake-14b"})) as (url, _calls):
        routed = _route(url, tmp_path)
    assert routed["ok"]
    (line,) = shadow.RECORDER.recent(1)
    assert line["task"] == {
        "id": "chore:triage",
        "kind": "chore",
        "qos": "interactive",
        "engine": "q14b+a2",
        "verifier": "deterministic",
        "in": ["job7/traceback"],
    }
    assert line["actual"]["outcome"] == "verified" and line["actual"]["hops"] == 1
    assert line["delta"]["agrees"] is True


def test_overhead_is_negligible(tmp_path):
    shadow.RECORDER.enable(tmp_path)
    task = TaskDescriptor(id="chore:x", kind="chore", engine="q14b+a2")
    started = time.perf_counter()
    for _ in range(500):
        shadow.record(task, {"outcome": "verified", "wall_s": 1.0, "_resident": "q14b+a2"})
    per_record_us = (time.perf_counter() - started) / 500 * 1e6
    assert per_record_us < 5000, f"{per_record_us:.0f} us/record"
    print(f"\nshadow record overhead: {per_record_us:.0f} us/record median-ish")
    day_files = list(tmp_path.glob("traces-*.jsonl"))
    assert len(day_files) == 1
    assert len(day_files[0].read_text().splitlines()) == 500
    line = json.loads(day_files[0].read_text().splitlines()[0])
    assert len(json.dumps(line)) < 400  # compact lines, budget discipline
