"""A43 P2 acceptance: staleness and the DAG.

Touch one input and exactly the dependent steps re-run; nothing else
moves; a second run is a compact no-op that says WHY it did nothing.
"""

from __future__ import annotations

import sys
import time

import pytest

from tee.app import TeeApp
from tee.kernel import trustctx
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.pipeline import schema
from tee.pipeline.tools import register_run_tools

PY_EXE = sys.executable

# a -> b -> c : each step reads what the previous one wrote
CHAIN = f"""
[[step]]
name = "stage_a"
kind = "produce"
argv = ["{PY_EXE}", "step.py", "a", "seed.txt", "out/a.txt"]
inputs = ["seed.txt"]
outputs = ["out/a.txt"]

[[step]]
name = "stage_b"
kind = "produce"
argv = ["{PY_EXE}", "step.py", "b", "out/a.txt", "out/b.txt"]
inputs = ["out/a.txt"]
outputs = ["out/b.txt"]

[[step]]
name = "stage_c"
kind = "produce"
argv = ["{PY_EXE}", "step.py", "c", "out/b.txt", "out/c.txt"]
inputs = ["out/b.txt"]
outputs = ["out/c.txt"]
"""


def _project(tmp_path, declaration: str = CHAIN):
    project = tmp_path / "proj"
    (project / ".tee").mkdir(parents=True)
    (project / ".tee" / "pipeline.toml").write_text(declaration)
    (project / ".tee" / "config.toml").write_text('[trust]\ngrants = ["run-declared-step"]\n')
    (project / "step.py").write_text(
        "import os, sys\n"
        "tag, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]\n"
        "os.makedirs(os.path.dirname(dst), exist_ok=True)\n"
        "open(dst, 'w').write(tag + ':' + open(src).read())\n"
        "open('runs.log', 'a').write(tag + '\\n')\n"
    )
    (project / "seed.txt").write_text("seed-1")
    schema.pin_path(project).write_text(schema.load(project).digest)
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    register_run_tools(app, project)
    trustctx.CALLER.set("live-turn")
    return app, project


def _run(app, target, **kwargs):
    trustctx.CALLER.set("live-turn")
    started = app.registry.call("pipeline_run", {"step": target, **kwargs})
    if "job" not in started:
        return started  # nothing was stale
    deadline = time.time() + 30
    while time.time() < deadline:
        status = app.jobs.status(started["job"])
        if status["state"] in ("done", "error"):
            return status["result"]
        time.sleep(0.02)
    raise AssertionError("job never finished")


def _ran(project) -> list[str]:
    log = project / "runs.log"
    return log.read_text().split() if log.is_file() else []


def test_the_graph_is_derived_from_the_declarations(tmp_path):
    app, project = _project(tmp_path)
    result = _run(app, "stage_c")
    assert [r["step"] for r in result["ran"]] == ["stage_a", "stage_b", "stage_c"]
    assert _ran(project) == ["a", "b", "c"]  # dependency order, nobody wrote an edge
    assert (project / "out" / "c.txt").read_text() == "c:b:a:seed-1"
    app.shutdown()


def test_touching_one_input_re_runs_exactly_the_dependents(tmp_path):
    app, project = _project(tmp_path)
    _run(app, "stage_c")
    (project / "runs.log").unlink()

    # nothing changed: the whole chain is fresh, and says so
    fresh = _run(app, "stage_c")
    assert fresh["ran"] == [] and fresh["answer"] == "all fresh - nothing to do"
    assert {s["step"] for s in fresh["skipped"]} == {"stage_a", "stage_b", "stage_c"}
    assert _ran(project) == []  # nothing executed at all

    # touch the seed: a re-runs, and b and c follow because their inputs changed
    (project / "seed.txt").write_text("seed-2")
    result = _run(app, "stage_c")
    assert [r["step"] for r in result["ran"]] == ["stage_a", "stage_b", "stage_c"]
    assert (project / "out" / "c.txt").read_text() == "c:b:a:seed-2"
    app.shutdown()


def test_a_mid_graph_change_leaves_upstream_alone(tmp_path):
    app, project = _project(tmp_path)
    _run(app, "stage_c")
    (project / "runs.log").unlink()

    # b's own output is deleted: b must rebuild, c follows, a stays fresh
    (project / "out" / "b.txt").unlink()
    result = _run(app, "stage_c")
    assert [r["step"] for r in result["ran"]] == ["stage_b", "stage_c"]
    assert result["skipped"] == [{"step": "stage_a", "reason": "fresh"}]
    assert _ran(project) == ["b", "c"]  # a did not move
    app.shutdown()


def test_force_runs_anyway_and_says_so(tmp_path):
    app, project = _project(tmp_path)
    _run(app, "stage_c")
    (project / "runs.log").unlink()
    result = _run(app, "stage_c", force=True)
    assert [r["step"] for r in result["ran"]] == ["stage_a", "stage_b", "stage_c"]
    assert "force = true" in result["forced"]
    assert _ran(project) == ["a", "b", "c"]
    app.shutdown()


def test_a_failure_stops_the_chain_and_stays_stale(tmp_path):
    app, project = _project(tmp_path)
    (project / "step.py").write_text(
        "import sys\n"
        "if sys.argv[1] == 'b':\n"
        "    sys.stderr.write('b is broken\\n'); sys.exit(4)\n"
        "import os\n"
        "os.makedirs(os.path.dirname(sys.argv[3]), exist_ok=True)\n"
        "open(sys.argv[3], 'w').write(sys.argv[1])\n"
        "open('runs.log', 'a').write(sys.argv[1] + '\\n')\n"
    )
    schema.pin_path(project).write_text(schema.load(project).digest)
    result = _run(app, "stage_c")
    steps = [r["step"] for r in result["ran"]]
    assert steps == ["stage_a", "stage_b"]  # c was never attempted
    assert result["ran"][-1]["error"].startswith("step 'stage_b' exited 4")

    # the failed step is still stale, so a retry actually retries
    (project / "runs.log").unlink()
    again = _run(app, "stage_c")
    assert [r["step"] for r in again["ran"]] == ["stage_b"]  # a stayed fresh
    app.shutdown()


def test_a_declared_cycle_is_refused_by_name(tmp_path):
    cycle = f"""
[[step]]
name = "one"
kind = "produce"
argv = ["{PY_EXE}", "-c", "print(1)"]
inputs = ["out/two.txt"]
outputs = ["out/one.txt"]

[[step]]
name = "two"
kind = "produce"
argv = ["{PY_EXE}", "-c", "print(2)"]
inputs = ["out/one.txt"]
outputs = ["out/two.txt"]
"""
    app, _ = _project(tmp_path, cycle)
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("pipeline_run", {"step": "one"})
    assert excinfo.value.code == "pipeline_cycle"
    assert "one" in excinfo.value.message and "two" in excinfo.value.message
    app.shutdown()
