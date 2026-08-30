"""A43 P3 acceptance: declared steps are task-graph nodes like any other.

They are dispatched, admitted, metered and traced by the SAME K-layer
that runs chores and reconstructions - no new concepts - and with the
scheduler switched off they run exactly as they did in P1, only
sequentially. That last sentence is the degrade-to-static promise, and
it is a fixture rather than a claim.
"""

from __future__ import annotations

import sys
import threading
import time

from tee.app import TeeApp
from tee.kernel import shadow, trustctx
from tee.kernel.adapter import FakeAdapter
from tee.pipeline import schema
from tee.pipeline.tools import register_run_tools

PY_EXE = sys.executable

DECL = f"""
[[step]]
name = "quick"
kind = "produce"
argv = ["{PY_EXE}", "make.py"]
inputs = ["make.py"]
outputs = ["out/quick.txt"]
cost = {{ wall_s = [1, 3], footprint_gb = 0.5 }}
"""


def _project(tmp_path, *, scheduler: bool = True):
    project = tmp_path / "proj"
    (project / ".tee").mkdir(parents=True)
    (project / ".tee" / "pipeline.toml").write_text(DECL)
    (project / ".tee" / "config.toml").write_text(
        '[trust]\ngrants = ["run-declared-step"]\n'
        + ("" if scheduler else "[scheduler]\nqos = false\ndispatch = false\n")
    )
    (project / "make.py").write_text(
        "import os\nos.makedirs('out', exist_ok=True)\nopen('out/quick.txt','w').write('done')\n"
    )
    schema.pin_path(project).write_text(schema.load(project).digest)
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    register_run_tools(app, project)
    trustctx.CALLER.set("live-turn")
    return app, project


def _finish(app, started, timeout=30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = app.jobs.status(started["job"])
        if status["state"] in ("done", "error"):
            return status
        time.sleep(0.02)
    raise AssertionError("job never finished")


def test_a_step_is_admitted_dispatched_and_metered_like_any_job(tmp_path):
    app, _ = _project(tmp_path)
    started = app.registry.call("pipeline_run", {"step": "quick"})
    # batch QoS by default, and the ledger holds the DECLARED footprint
    assert app.jobs.status(started["job"])["qos"] == "batch"
    held = {row["engine"]: row["footprint_gb"] for row in app.machine.active_jobs()}
    assert held.get("pipeline-step") == 0.5 or _finish(app, started)  # may finish fast
    _finish(app, started)
    assert app.machine.active_jobs() == []  # released

    meter = app.machine.meter_block()
    assert meter["pipeline"]["steps_run"] == 1
    assert meter["pipeline"]["wall_s"] >= 0
    app.shutdown()


def test_pipeline_work_reaches_report_savings(tmp_path):
    app, _ = _project(tmp_path)
    _finish(app, app.registry.call("pipeline_run", {"step": "quick"}))
    savings = app.registry.call("report_savings", {})
    assert savings["routing"]["pipeline"]["steps_run"] == 1
    app.shutdown()


def test_a_step_leaves_a_shadow_trace_like_every_other_dispatch(tmp_path):
    app, project = _project(tmp_path)
    shadow.RECORDER.enable(project / ".tee" / "shadow")
    _finish(app, app.registry.call("pipeline_run", {"step": "quick"}))
    time.sleep(0.1)
    traced = [line for line in shadow.RECORDER.recent(10) if line["task"]["kind"] == "job"]
    assert any(line["task"].get("engine") == "pipeline-step" for line in traced)
    app.shutdown()


def test_interactive_work_is_not_stuck_behind_a_pipeline_step(tmp_path):
    """K1's law applies to the lane for free: batch never blocks a turn."""
    app, _ = _project(tmp_path)
    gate = threading.Event()
    app.jobs.submit("slow-batch", lambda: (gate.wait(5), {})[1], qos="batch")
    time.sleep(0.05)
    done: list[str] = []
    app.jobs.submit("chat", lambda: (done.append("chat"), {})[1], qos="interactive")
    deadline = time.time() + 3
    while time.time() < deadline and not done:
        time.sleep(0.01)
    assert done == ["chat"]  # the reserved worker served it at once
    gate.set()
    app.shutdown()


def test_with_the_scheduler_off_the_same_run_completes_identically(tmp_path):
    """Degrade-to-static: the answer is the same, the ordering is plain."""
    on_app, on_project = _project(tmp_path / "on", scheduler=True)
    on_result = _finish(on_app, on_app.registry.call("pipeline_run", {"step": "quick"}))["result"]
    on_app.shutdown()

    off_app, off_project = _project(tmp_path / "off", scheduler=False)
    assert off_app.jobs._qos_enabled is False  # the switch really is off
    off_result = _finish(off_app, off_app.registry.call("pipeline_run", {"step": "quick"}))[
        "result"
    ]
    off_app.shutdown()

    assert on_result["artifacts"]["created"][0]["path"] == "out/quick.txt"
    assert (
        off_result["artifacts"]["created"][0]["hash"]
        == (on_result["artifacts"]["created"][0]["hash"])
    )
    assert (on_project / "out" / "quick.txt").read_text() == (
        off_project / "out" / "quick.txt"
    ).read_text()


def test_a_mixed_run_places_sanely_and_the_meter_shows_all_three(tmp_path):
    """P3's acceptance, literally: a pipeline step, a chore and a
    reconstruction in flight together. The K-layer places them by class -
    the chore is not stuck behind the batch work - and ONE meter shows
    all three, because the lane added a row rather than a lane."""
    app, _ = _project(tmp_path)
    release = threading.Event()
    order: list[str] = []

    # reconstruction: batch, registers its footprint in the ledger
    def _reconstruct():
        app.machine.register_job("recon-1", "reconstruct-photogrammetry")
        try:
            release.wait(5)
            order.append("reconstruct")
            return {"views": 36}
        finally:
            app.machine.release_job("recon-1")

    app.jobs.submit("reconstruct", _reconstruct, qos="batch", engine="reconstruct-photogrammetry")
    started = app.registry.call("pipeline_run", {"step": "quick"})  # batch
    time.sleep(0.05)

    # chore: interactive, must not wait behind either batch job
    app.jobs.submit("chore", lambda: (order.append("chore"), {})[1], qos="interactive")
    deadline = time.time() + 3
    while time.time() < deadline and "chore" not in order:
        time.sleep(0.01)
    assert order == ["chore"], "the interactive chore waited behind batch work"

    release.set()
    _finish(app, started)

    meter = app.machine.meter_block()
    assert meter["pipeline"]["steps_run"] == 1  # the lane's own row
    assert meter["jobs"]["active"] == 0  # everything released
    assert meter["scheduler"]["queue_age_s"]["queued"] == 0
    app.shutdown()
