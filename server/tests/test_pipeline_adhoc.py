"""A43 P0b acceptance: the ad-hoc door opens for a live human turn only.

Declared steps are the norm and the only thing anything automatic may
run. This file is the proof of that sentence: one refusal fixture per
caller class, plus the invariant that untrusted content can never cause
execution - and then the discovery route working end to end.
"""

from __future__ import annotations

import sys

import pytest

from tee.app import TeeApp
from tee.kernel import trustctx
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.pipeline import schema
from tee.pipeline.tools import register_adhoc_tools, register_pipeline_tools


def _app(tmp_path, *, allow_adhoc: bool = True, grant: bool = True):
    project = tmp_path / "proj"
    (project / ".tee").mkdir(parents=True)
    config = "[pipeline]\nallow_adhoc = true\n" if allow_adhoc else ""
    if grant:
        config += '[trust]\ngrants = ["run-adhoc"]\n'
    (project / ".tee" / "config.toml").write_text(config)
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    register_pipeline_tools(app, project)
    register_adhoc_tools(app, project)
    return app, project


# -- one refusal per caller class (the invariant, exhaustively) -------------


@pytest.mark.parametrize(
    "caller", ["job", "scheduled", "chore", "gateway-fronted", "content-derived"]
)
def test_adhoc_is_refused_for_every_automatic_caller(tmp_path, caller):
    app, _ = _app(tmp_path)
    trustctx.CALLER.set(caller)
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("pipeline_adhoc", {"argv": [sys.executable, "-c", "print(1)"]})
    assert excinfo.value.code in ("pipeline_not_a_live_turn", "trust_denied")
    app.shutdown()


def test_fetched_provenance_refuses_even_in_a_live_turn(tmp_path):
    """The load-bearing sentence: untrusted content can never cause
    execution. A live turn that has read the web is not a clean turn."""
    app, _ = _app(tmp_path)
    trustctx.CALLER.set("live-turn")
    trustctx.add_taint("fetch-web:docs.example/page")
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("pipeline_adhoc", {"argv": [sys.executable, "-c", "print(1)"]})
    # The KERNEL refuses first - run-adhoc is high-risk, so a tainted turn
    # is denied before the lane's own door is even reached.
    assert excinfo.value.code == "trust_denied"
    assert "untrusted content" in excinfo.value.fix

    # ...and the door refuses independently, so the guarantee does not rest
    # on one layer. Grant the capability and the taint guard still holds.
    from dataclasses import replace

    app.registry.grants = replace(
        app.registry.grants, granted=app.registry.grants.granted | {"run-adhoc"}
    )
    trustctx.CALLER.set("live-turn")
    trustctx.add_taint("fetch-web:docs.example/page")
    with pytest.raises(TeeError) as excinfo:
        app.registry._tools["pipeline_adhoc"].handler({"argv": [sys.executable, "-c", "print(1)"]})
    assert excinfo.value.code == "pipeline_tainted_turn"
    assert "never cause execution" in excinfo.value.fix
    app.shutdown()


def test_adhoc_needs_the_project_opt_in_and_the_grant(tmp_path):
    app, _ = _app(tmp_path, allow_adhoc=False)
    trustctx.CALLER.set("live-turn")
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("pipeline_adhoc", {"argv": ["echo", "hi"]})
    assert excinfo.value.code == "pipeline_adhoc_disabled"
    assert "allow_adhoc = true" in excinfo.value.fix
    app.shutdown()

    ungranted, _ = _app(tmp_path / "b", grant=False)
    trustctx.CALLER.set("live-turn")
    with pytest.raises(TeeError) as excinfo:
        ungranted.registry.call("pipeline_adhoc", {"argv": ["echo", "hi"]})
    assert excinfo.value.code == "trust_denied"  # the kernel, before the door
    assert "run-adhoc" in excinfo.value.fix
    ungranted.shutdown()


def test_a_command_string_is_refused(tmp_path):
    app, _ = _app(tmp_path)
    trustctx.CALLER.set("live-turn")
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("pipeline_adhoc", {"argv": "python build.py --all"})
    # The schema refuses it before the handler; the refusal now carries a
    # fix line, which it did not before this phase.
    assert excinfo.value.code == "bad_argument_type"
    assert "must be array" in excinfo.value.message
    assert "never one string" in excinfo.value.fix

    # and the handler refuses independently, so neither layer is load-bearing
    # alone (the runner would too - argv is validated there as well)
    trustctx.CALLER.set("live-turn")
    with pytest.raises(TeeError) as excinfo:
        app.registry._tools["pipeline_adhoc"].handler({"argv": "python build.py --all"})
    assert "never a command string" in excinfo.value.fix
    app.shutdown()


# -- the discovery route, end to end ---------------------------------------


def test_adhoc_then_adopt_then_the_step_is_declared(tmp_path):
    app, project = _app(tmp_path)
    trustctx.CALLER.set("live-turn")

    out = app.registry.call(
        "pipeline_adhoc",
        {"argv": [sys.executable, "-c", "open('artifact.txt','w').write('built')"]},
    )
    assert out["ran"] == "ad-hoc, not declared"  # labelled in the report
    assert out["exit"] == 0 and out["cached"] is False and out["scheduled"] is False
    assert "artifact.txt" in out["touched"]["created"]

    trustctx.CALLER.set("live-turn")
    adopted = app.registry.call("pipeline_adopt", {"name": "build_thing"})
    assert adopted["inferred"]["kind"] == "produce"
    assert "artifact.txt" in adopted["inferred"]["outputs"]
    proposed = project / ".tee" / "pipeline.proposed.toml"
    assert proposed.is_file()
    assert not (project / ".tee" / "pipeline.toml").exists()  # TEE wrote NOTHING

    # the owner moves the proposal in, and it parses as a real declaration
    declaration = proposed.read_text()
    (project / ".tee" / "pipeline.toml").write_text(declaration)
    pipeline = schema.load(project)
    step = pipeline.require("build_thing")
    assert step.kind == "produce" and step.outputs == ["artifact.txt"]
    assert step.argv[0] == sys.executable
    assert pipeline.approved is False  # a new declaration is still unapproved
    app.shutdown()


def test_a_failing_adhoc_returns_one_line_and_a_tail_not_a_flood(tmp_path):
    app, _ = _app(tmp_path)
    trustctx.CALLER.set("live-turn")
    out = app.registry.call(
        "pipeline_adhoc",
        {
            "argv": [
                sys.executable,
                "-c",
                "import sys; [print('noise %d' % i) for i in range(5000)]; sys.exit(3)",
            ]
        },
    )
    assert out["exit"] == 3
    assert out["error"].startswith("step 'ad-hoc' exited 3")
    assert len(out.get("tail", "")) <= 2100  # bounded, not a log dump
    app.shutdown()


def test_the_runner_can_never_reach_a_shell():
    """P0's AST guard, evolved: the runner exists now, so the assertion
    becomes the permanent one - no shell, no os.system, ever."""
    import ast
    import pathlib

    lane = pathlib.Path(__file__).resolve().parents[1] / "src" / "tee" / "pipeline"
    for path in lane.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    assert keyword.arg != "shell", f"{path.name} passes shell="
                target = ast.unparse(node.func)
                assert target not in ("os.system", "os.popen", "eval", "exec"), (
                    f"{path.name} calls {target}"
                )
