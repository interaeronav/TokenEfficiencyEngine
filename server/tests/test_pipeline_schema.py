"""A43 P0 acceptance: the declaration surface is provably safe BEFORE any
runner exists.

Every fixture here is a refusal or an inertness proof. The lane's whole
security argument is that a declared step is a BOUNDED capability, so
these tests are the bound.
"""

from __future__ import annotations

import pytest

from tee.kernel.errors import TeeError
from tee.pipeline import schema

GOOD = """
[[step]]
name = "basemap"
kind = "produce"
argv = ["python", "builder/build_basemap.py", "--tile", "{tile}"]
params = { tile = { type = "string", pattern = "^[a-z0-9_]{1,32}$" } }
inputs = ["builder/build_basemap.py"]
outputs = ["out/basemap_{tile}.tif"]
cost = { wall_s = [120, 900], footprint_gb = 4 }

[[step]]
name = "blunder_stats"
kind = "query"
argv = ["python", "builder/blunder_stats.py", "--json"]
answer = { format = "json", max_tokens = 400 }
"""


def _write(tmp_path, text: str):
    (tmp_path / ".tee").mkdir(exist_ok=True)
    (tmp_path / ".tee" / "pipeline.toml").write_text(text)
    return tmp_path


def _approve(tmp_path) -> None:
    """What the OWNER does after reading the file - never TEE."""
    pipeline = schema.load(tmp_path)
    schema.pin_path(tmp_path).write_text(pipeline.digest)


# -- the shapes that must be refused ---------------------------------------


def test_a_shell_string_is_refused_by_name(tmp_path):
    """The one mistake that turns a bounded capability into a shell."""
    _write(tmp_path, '[[step]]\nname = "x"\nkind = "query"\nargv = "python build.py --all"\n')
    with pytest.raises(TeeError) as excinfo:
        schema.load(tmp_path)
    assert excinfo.value.code == "pipeline_shell_string"
    assert "never a shell string" in excinfo.value.fix
    assert "TEE never runs a shell" in excinfo.value.fix


def test_an_unconstrained_param_is_refused_as_a_laundered_allowlist(tmp_path):
    """`make {target}` with a free string is arbitrary execution wearing a
    declaration's clothes - the bound is the point, not the ceremony."""
    _write(
        tmp_path,
        '[[step]]\nname = "build"\nkind = "query"\n'
        'argv = ["make", "{target}"]\n'
        'params = { target = { type = "string" } }\n',
    )
    with pytest.raises(TeeError) as excinfo:
        schema.load(tmp_path)
    assert excinfo.value.code == "pipeline_unbounded_param"
    assert "arbitrary-execution grant" in excinfo.value.message
    assert "enum" in excinfo.value.fix and "pattern" in excinfo.value.fix


def test_malformed_declarations_name_the_exact_fix(tmp_path):
    cases = [
        ('[[step]]\nname = "X bad"\nkind = "query"\nargv = ["ls"]\n', "lower-case identifiers"),
        ('[[step]]\nname = "s"\nkind = "magic"\nargv = ["ls"]\n', 'kind = "produce"'),
        ('[[step]]\nname = "s"\nkind = "produce"\nargv = ["ls"]\n', "outputs ="),
        (
            '[[step]]\nname = "s"\nkind = "query"\nargv = ["ls", "{missing}"]\n',
            "Declare it",
        ),
    ]
    for text, expected_fix in cases:
        _write(tmp_path, text)
        with pytest.raises(TeeError) as excinfo:
            schema.load(tmp_path)
        assert expected_fix in excinfo.value.fix, text


def test_duplicate_step_names_refuse(tmp_path):
    _write(
        tmp_path,
        '[[step]]\nname = "s"\nkind = "query"\nargv = ["ls"]\n'
        '[[step]]\nname = "s"\nkind = "query"\nargv = ["pwd"]\n',
    )
    with pytest.raises(TeeError) as excinfo:
        schema.load(tmp_path)
    assert "declared twice" in excinfo.value.message


def test_unknown_step_lists_the_declared_ones(tmp_path):
    pipeline = schema.load(_write(tmp_path, GOOD))
    with pytest.raises(TeeError) as excinfo:
        pipeline.require("nope")
    assert excinfo.value.code == "pipeline_unknown_step"
    assert "basemap" in excinfo.value.fix and "blunder_stats" in excinfo.value.fix


# -- inertness: a permitted nasty value is DATA, not syntax -----------------


def test_a_hostile_value_lands_as_exactly_one_inert_argv_element(tmp_path):
    """The declaration deliberately permits spaces and quotes here. Even so,
    the value can only ever be ONE argument - there is no shell to reach."""
    _write(
        tmp_path,
        '[[step]]\nname = "label"\nkind = "query"\n'
        'argv = ["python", "label.py", "--title", "{title}"]\n'
        'params = { title = { type = "string", pattern = "^[\\\\w \\"\';|&$()~/-]+$" } }\n',
    )
    step = schema.load(tmp_path).steps["label"]
    hostile = "a b\"c'; rm -rf ~ | cat & $(whoami)"
    argv = schema.substitute(step, {"title": hostile})
    assert argv == ["python", "label.py", "--title", hostile]
    assert len(argv) == 4  # the metacharacters did not become arguments
    assert hostile in argv  # verbatim, unsplit, unquoted, uninterpreted


def test_traversal_and_null_bytes_are_refused_whatever_the_pattern_says(tmp_path):
    """Belt over braces: a permissive pattern cannot re-enable path escape."""
    _write(
        tmp_path,
        '[[step]]\nname = "label"\nkind = "query"\n'
        'argv = ["python", "label.py", "{title}"]\n'
        'params = { title = { type = "string", pattern = "^.+$" } }\n',
    )
    step = schema.load(tmp_path).steps["label"]
    for hostile in ("../../etc/passwd", "ok\x00hidden"):
        with pytest.raises(TeeError) as excinfo:
            schema.substitute(step, {"title": hostile})
        assert excinfo.value.code == "pipeline_bad_param"


def test_declared_values_are_validated_against_their_constraint(tmp_path):
    step = schema.load(_write(tmp_path, GOOD)).steps["basemap"]
    assert schema.substitute(step, {"tile": "atl08_north"})[-1] == "atl08_north"
    with pytest.raises(TeeError) as excinfo:
        schema.substitute(step, {"tile": "ATL08 North!"})
    assert excinfo.value.code == "pipeline_bad_param"
    with pytest.raises(TeeError) as excinfo:
        schema.substitute(step, {})
    assert excinfo.value.code == "pipeline_missing_param"


# -- trust on first use ----------------------------------------------------


def test_an_unapproved_declaration_is_not_trusted(tmp_path):
    """A cloned repo ships a pipeline.toml too - it is attacker-authored by
    definition until this machine's owner has seen it."""
    pipeline = schema.load(_write(tmp_path, GOOD))
    assert pipeline.approved is False
    assert "never approved" in pipeline.change


def test_a_changed_declaration_loses_approval_and_names_the_change(tmp_path):
    _write(tmp_path, GOOD)
    _approve(tmp_path)
    assert schema.load(tmp_path).approved is True

    _write(tmp_path, GOOD + '\n[[step]]\nname = "sneaky"\nkind = "query"\nargv = ["curl", "x"]\n')
    reloaded = schema.load(tmp_path)
    assert reloaded.approved is False
    assert "changed since it was approved" in reloaded.change


def test_tee_never_writes_the_projects_declaration(tmp_path):
    """The adopt flow emits a .proposed file; the real path stays the
    owner's. This test is the guard on that promise."""
    import pathlib

    import tee.pipeline.schema as schema_module

    source = pathlib.Path(schema_module.__file__).read_text()
    for writer in ("write_text(", "open(", "write_bytes("):
        for line in source.splitlines():
            if writer in line and "pipeline.toml" in line:
                pytest.fail(f"schema.py writes the project's declaration: {line.strip()}")


# -- the lane through the registry (the kernel's first tenant) -------------


def test_pipeline_list_reports_absence_with_the_fix(tmp_path):
    from tee.app import TeeApp
    from tee.kernel.adapter import FakeAdapter
    from tee.pipeline.tools import register_pipeline_tools

    project = tmp_path / "proj"
    project.mkdir()
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    register_pipeline_tools(app, project)
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("pipeline_list", {})
    assert excinfo.value.code == "pipeline_absent"
    assert "pipeline_init" in excinfo.value.fix
    app.shutdown()


def test_pipeline_list_shows_steps_and_approval_state(tmp_path):
    from tee.app import TeeApp
    from tee.kernel.adapter import FakeAdapter
    from tee.pipeline.tools import register_pipeline_tools

    project = tmp_path / "proj"
    project.mkdir()
    _write(project, GOOD)
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    register_pipeline_tools(app, project)
    listing = app.registry.call("pipeline_list", {})
    assert [s["name"] for s in listing["steps"]] == ["basemap", "blunder_stats"]
    assert listing["approved"] is False
    assert "to_approve" in listing and "never approves its own inputs" in listing["to_approve"]
    kinds = {s["name"]: s["kind"] for s in listing["steps"]}
    assert kinds == {"basemap": "produce", "blunder_stats": "query"}
    app.shutdown()


def test_no_runner_exists_yet():
    """P0's acceptance is literally that nothing can execute yet.

    Checked against the AST, not the text: the module docstrings discuss
    `shell=True` precisely because they forbid it, and a prose match would
    make this test lie in both directions."""
    import ast
    import pathlib

    lane = pathlib.Path(__file__).resolve().parents[1] / "src" / "tee" / "pipeline"
    for path in lane.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in getattr(node, "names", [])]
                names.append(getattr(node, "module", "") or "")
                assert not any(
                    n.split(".")[0] in {"subprocess", "os", "pty", "shutil"} for n in names
                ), f"{path.name} imports an execution module: {names}"
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    assert keyword.arg != "shell", f"{path.name} passes shell="
