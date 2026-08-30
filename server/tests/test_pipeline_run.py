"""A43 P1 acceptance: declared steps run as jobs and answer, never dump.

Produce steps answer with an artifact diff; query steps answer with their
own output in the declared format, budgeted and provenance-stamped; a
failing step returns one honest line plus a bounded tail.
"""

from __future__ import annotations

import sys
import time
from dataclasses import replace

import pytest

from tee.app import TeeApp
from tee.kernel import trustctx
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.pipeline import schema
from tee.pipeline.tools import register_pipeline_tools, register_run_tools

PY_EXE = sys.executable

DECL = f"""
[[step]]
name = "build"
kind = "produce"
argv = ["{PY_EXE}", "make_artifact.py", "{{tile}}"]
params = {{ tile = {{ type = "string", pattern = "^[a-z0-9_]+$" }} }}
inputs = ["make_artifact.py"]
outputs = ["out/tile_{{tile}}.txt"]
cost = {{ wall_s = [1, 5], footprint_gb = 0.5 }}

[[step]]
name = "stats"
kind = "query"
argv = ["{PY_EXE}", "stats.py"]
answer = {{ format = "json", max_tokens = 400 }}

[[step]]
name = "noisy"
kind = "query"
argv = ["{PY_EXE}", "noisy.py"]
answer = {{ format = "text", max_tokens = 50 }}

[[step]]
name = "broken"
kind = "query"
argv = ["{PY_EXE}", "broken.py"]
answer = {{ format = "text", max_tokens = 100 }}
"""


def _project(tmp_path, *, approve: bool = True, grant: bool = True):
    project = tmp_path / "proj"
    (project / ".tee").mkdir(parents=True)
    (project / ".tee" / "pipeline.toml").write_text(DECL)
    (project / "make_artifact.py").write_text(
        "import os, sys\n"
        "os.makedirs('out', exist_ok=True)\n"
        "open('out/tile_%s.txt' % sys.argv[1], 'w').write('built ' + sys.argv[1])\n"
    )
    (project / "stats.py").write_text('print(\'{"blunders": 3, "kept": 41}\')\n')
    (project / "noisy.py").write_text("print('x' * 8000)\n")
    (project / "broken.py").write_text(
        "import sys\nprint('progress', flush=True)\n"
        "sys.stderr.write('boom: the input file was empty\\n')\nsys.exit(2)\n"
    )
    if grant:
        (project / ".tee" / "config.toml").write_text('[trust]\ngrants = ["run-declared-step"]\n')
    if approve:
        schema.pin_path(project).write_text(schema.load(project).digest)
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    register_pipeline_tools(app, project)
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


def test_a_produce_step_answers_with_an_artifact_diff(tmp_path):
    app, _project_root = _project(tmp_path)
    started = app.registry.call("pipeline_run", {"step": "build", "params": {"tile": "north"}})
    assert started["kind"] == "produce"
    result = _finish(app, started)["result"]
    assert "exit" not in result  # success is the absence of a failure line
    created = result["artifacts"]["created"]
    assert created[0]["path"] == "out/tile_north.txt"
    assert created[0]["size"] > 0 and len(created[0]["hash"]) == 16
    # Provenance is the two hashes that let you re-derive the answer plus
    # the wall clock - nothing the payload already says (P6: on a one-line
    # answer the old block cost more than the answer did).
    assert set(result["provenance"]) == {"argv_hash", "inputs_hash", "wall_s"}
    assert result["step"] == "build"
    assert app.machine.active_jobs() == []  # the ledger released

    # P2: a second immediate run does not execute at all - it is fresh
    trustctx.CALLER.set("live-turn")
    again = app.registry.call("pipeline_run", {"step": "build", "params": {"tile": "north"}})
    assert again["ran"] == [] and again["answer"] == "all fresh - nothing to do"
    assert again["skipped"] == [{"step": "build", "reason": "fresh"}]

    # forcing runs anyway, and the diff reports the output as UNCHANGED
    trustctx.CALLER.set("live-turn")
    forced = _finish(
        app,
        app.registry.call(
            "pipeline_run",
            {"step": "build", "params": {"tile": "north"}, "force": True},
        ),
    )["result"]
    assert forced["artifacts"].get("unchanged") == ["out/tile_north.txt"]
    assert "created" not in forced["artifacts"]
    app.shutdown()


def test_a_query_step_answers_in_its_declared_format(tmp_path):
    app, _ = _project(tmp_path)
    started = app.registry.call("pipeline_run", {"step": "stats"})
    result = _finish(app, started)["result"]
    assert result["format"] == "json"
    assert result["answer"] == {"blunders": 3, "kept": 41}
    assert result["provenance"]["argv_hash"]
    app.shutdown()


def test_a_query_answer_is_held_to_its_declared_budget(tmp_path):
    app, _ = _project(tmp_path)
    result = _finish(app, app.registry.call("pipeline_run", {"step": "noisy"}))["result"]
    assert "trimmed to the declared 50-token budget" in result["answer"]
    assert len(result["answer"]) < 1000  # 8k chars of noise did not arrive
    app.shutdown()


def test_a_failing_step_returns_one_line_and_a_tail(tmp_path):
    app, _ = _project(tmp_path)
    result = _finish(app, app.registry.call("pipeline_run", {"step": "broken"}))["result"]
    assert result["exit"] == 2
    assert result["error"].startswith("step 'broken' exited 2")
    assert "boom: the input file was empty" in result["error"]
    assert len(result["tail"]) <= 1200
    app.shutdown()


# -- the refusals that make a declared step a BOUNDED capability -----------


def test_an_unapproved_declaration_will_not_run(tmp_path):
    app, _ = _project(tmp_path, approve=False)
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("pipeline_run", {"step": "stats"})
    assert excinfo.value.code == "pipeline_unapproved"
    assert "attacker-authored by definition" in excinfo.value.fix
    app.shutdown()


def test_a_changed_declaration_stops_running_until_re_approved(tmp_path):
    app, project = _project(tmp_path)
    assert _finish(app, app.registry.call("pipeline_run", {"step": "stats"}))["state"] == "done"
    (project / ".tee" / "pipeline.toml").write_text(
        DECL
        + f'\n[[step]]\nname = "sneaky"\nkind = "query"\nargv = ["{PY_EXE}", "-c", "print(1)"]\n'
    )
    trustctx.CALLER.set("live-turn")
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("pipeline_run", {"step": "stats"})
    assert excinfo.value.code == "pipeline_unapproved"
    assert "changed since it was approved" in excinfo.value.message
    app.shutdown()


def test_the_capability_is_required(tmp_path):
    app, _ = _project(tmp_path, grant=False)
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("pipeline_run", {"step": "stats"})
    assert excinfo.value.code == "trust_denied"
    assert "run-declared-step" in excinfo.value.fix
    app.shutdown()


def test_a_param_that_breaks_its_constraint_never_reaches_argv(tmp_path):
    app, _ = _project(tmp_path)
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("pipeline_run", {"step": "build", "params": {"tile": "north; rm -rf ~"}})
    assert excinfo.value.code == "pipeline_bad_param"
    app.shutdown()


def test_untrusted_content_cannot_trigger_a_declared_step(tmp_path):
    """A declared step is bounded, but it still executes. A LIVE TURN may
    run one after reading the web - the human is present and the argv is
    fixed - but an unattended task carrying that content may not."""
    app, _ = _project(tmp_path)
    app.registry.grants = replace(app.registry.grants, enforce_quality_band=True)

    trustctx.add_taint("fetch-web:docs.example")
    started = app.registry.call("pipeline_run", {"step": "stats"})  # live turn: allowed
    assert _finish(app, started)["state"] == "done"

    trustctx.install("job", ("fetch-web:docs.example",))  # the same content, unattended
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("pipeline_run", {"step": "stats"})
    assert excinfo.value.code == "trust_denied"
    assert "untrusted content" in excinfo.value.fix
    app.shutdown()


def test_a_bad_param_is_refused_even_when_the_step_is_fresh(tmp_path):
    """Found in the P4 acceptance run against a real project: freshness was
    checked before the value was, so garbage got 'all fresh - nothing to
    do' - a success-shaped reply to a request that was never valid."""
    app, _root = _project(tmp_path)
    first = _finish(
        app, app.registry.call("pipeline_run", {"step": "build", "params": {"tile": "north"}})
    )["result"]
    assert "exit" not in first  # a zero exit code is not worth its tokens
    again = app.registry.call("pipeline_run", {"step": "build", "params": {"tile": "north"}})
    assert again["ran"] == []  # genuinely fresh now
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("pipeline_run", {"step": "build", "params": {"tile": "rm -rf /"}})
    assert excinfo.value.code == "pipeline_bad_param"
    app.shutdown()
