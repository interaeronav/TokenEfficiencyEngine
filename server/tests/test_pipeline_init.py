"""A43 P4: the draft authoring route, and the law that makes it safe.

`pipeline_init` reads a project's own scripts and proposes steps. The
proposal is deliberately inert: a scan is a guess about intent, so the
drafted file cannot execute anything even if the owner moves it in
wholesale. These fixtures hold that line, and check the three authoring
routes all arrive at the same place.
"""

from __future__ import annotations

import tomllib

import pytest

from tee.app import TeeApp
from tee.kernel import trustctx
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.pipeline import init, schema
from tee.pipeline.tools import register_adhoc_tools

BUILDER = '''
"""build_basemap.py - assemble the basemap from source tiles."""
import argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aerodromes", type=str, required=True, help="csv of sites")
    ap.add_argument("--out", default="./build")
    ap.add_argument("--execute", action="store_true")
    return 0

if __name__ == "__main__":
    main()
'''

STATS = '''
"""blunder_stats.py - mechanical diagnostics for a set of cells."""
import argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", required=True)
    ap.add_argument("--top", default=10)

if __name__ == "__main__":
    main()
'''

NOT_AN_ENTRY_POINT = "def helper(x):\n    return x + 1\n"


def _project(tmp_path):
    project = tmp_path / "proj"
    (project / "builder").mkdir(parents=True)
    (project / "builder" / "build_basemap.py").write_text(BUILDER)
    (project / "builder" / "blunder_stats.py").write_text(STATS)
    (project / "builder" / "helpers.py").write_text(NOT_AN_ENTRY_POINT)
    (project / ".tee").mkdir()
    (project / ".tee" / "config.toml").write_text("")
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    register_adhoc_tools(app, project)
    trustctx.CALLER.set("live-turn")
    return app, project


def test_the_scan_finds_entry_points_and_ignores_libraries(tmp_path):
    _, project = _project(tmp_path)
    found = {c.name: c for c in init.scan(project)}
    assert set(found) == {"build_basemap", "blunder_stats"}  # helpers.py is not a step
    assert found["build_basemap"].summary == "assemble the basemap from source tiles."
    assert found["build_basemap"].required == ["--aerodromes"]
    assert "--out" in found["build_basemap"].optional  # has a default -> not required
    assert "--execute" in found["build_basemap"].optional  # store_true defaults itself
    assert found["blunder_stats"].kind_guess == "query"  # named like an answer
    assert found["build_basemap"].kind_guess == "produce"


def test_the_draft_declares_zero_steps_even_copied_verbatim(tmp_path):
    """The structural promise: a guess must not become an execution grant
    just because it parsed as TOML."""
    _, project = _project(tmp_path)
    text = init.draft(project)
    assert "build_basemap" in text and "blunder_stats" in text  # it IS useful
    assert tomllib.loads(text) == {}  # ...and it declares nothing at all
    approved = project / ".tee" / "pipeline.toml"
    approved.write_text(text)
    pipeline = schema.load(project)
    assert pipeline.steps == {}


def test_the_draft_marks_what_a_scan_cannot_know(tmp_path):
    _, project = _project(tmp_path)
    text = init.draft(project)
    assert "<FILL>" in text  # the required flag has no value a scan can supply
    assert "inputs = []" in text and "outputs = []" in text  # staleness is the owner's
    assert "GUESS" in text  # kind is inferred from a NAME, and says so


def test_init_refuses_to_clobber_proposals_you_have_not_read(tmp_path):
    app, project = _project(tmp_path)
    app.registry.call("pipeline_init", {})
    proposed = project / ".tee" / "pipeline.proposed.toml"
    proposed.write_text(proposed.read_text() + "\n# my own note\n")
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("pipeline_init", {})
    assert excinfo.value.code == "pipeline_draft_exists"
    assert "my own note" in proposed.read_text()  # untouched
    app.registry.call("pipeline_init", {"replace": True})  # explicit is fine
    assert "my own note" not in proposed.read_text()
    app.shutdown()


def test_init_reports_honestly_that_nothing_it_wrote_can_run(tmp_path):
    app, project = _project(tmp_path)
    result = app.registry.call("pipeline_init", {})
    assert result["runnable"] is False
    assert {c["name"] for c in result["candidates"]} == {"build_basemap", "blunder_stats"}
    assert ".tee/pipeline.toml" in result["next"].replace(str(project), "").lstrip("/")
    app.shutdown()


def test_a_project_with_no_entry_points_says_so_and_points_elsewhere(tmp_path):
    bare = tmp_path / "bare"
    (bare / "docs").mkdir(parents=True)
    (bare / "docs" / "notes.md").write_text("# nothing runnable here")
    text = init.draft(bare)
    assert "Nothing with a command-line interface" in text
    assert "pipeline_adhoc" in text  # the discovery route is the way in
    assert tomllib.loads(text) == {}
