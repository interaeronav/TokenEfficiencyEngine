"""A77 P1: the benchmark measures the server that ships.

`run_benchmarks.py` hand-rolled its own registration list and fell seven lanes
behind `cmd_serve`, so the headline saving was computed over 141 virtual tools
where a real server serves 197. Nothing failed, because nothing compared them.

These are the comparison. `cli.attach_all` is the one list; a lane that reaches
one caller and not the other fails here rather than silently skewing a number
nobody re-runs.
"""

from __future__ import annotations

import ast
import re
import tempfile
from pathlib import Path

import pytest

from tee import cli
from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter

SERVER = Path(__file__).resolve().parents[1]
CLI_SRC = (SERVER / "src" / "tee" / "cli.py").read_text()
BENCH = SERVER.parent / "benchmarks" / "run_benchmarks.py"

#: Attached before the loop because they need the extract store threaded
#: through them; they are part of `attach_all`, not exceptions to it.
STORE_LANES = ("extract", "assets", "capture")


def _attach_functions() -> set[str]:
    """Every `_attach_<lane>` cli.py defines."""
    return {
        m.name.removeprefix("_attach_")
        for m in ast.parse(CLI_SRC).body
        if isinstance(m, ast.FunctionDef) and m.name.startswith("_attach_")
    }


def test_every_attach_function_is_in_the_one_list():
    """The canary. Adding a lane to cli.py without adding it here fails, which
    is what did not happen for windtunnel, flightdyn and engines."""
    defined = _attach_functions()
    listed = set(cli.LANE_ATTACHMENTS) | set(STORE_LANES)
    missing = sorted(defined - listed)
    assert not missing, (
        f"cli.py defines _attach_{{{', '.join(missing)}}} but attach_all never calls "
        f"them - a lane the server has and the benchmark cannot see"
    )
    stale = sorted(listed - defined - set(STORE_LANES))
    assert not stale, f"attach_all names lanes cli.py no longer defines: {stale}"


def test_cmd_serve_attaches_nothing_on_its_own():
    """If cmd_serve grows a bare _attach_ call, the list stops being the list."""
    body = CLI_SRC[CLI_SRC.index("def cmd_serve") :]
    body = body[: body.index("\ndef ", 1)] if "\ndef " in body[1:] else body
    stray = re.findall(r"_attach_([a-z]+)\(app", body)
    assert not stray, f"cmd_serve attaches {stray} directly instead of through attach_all"


def test_the_benchmark_harness_does_not_hand_roll_its_own_server():
    """The drift's actual mechanism: register_*_tools called straight from the
    harness, so a new lane never reached it."""
    if not BENCH.exists():  # pragma: no cover - benchmarks are optional on a checkout
        pytest.skip("benchmarks/run_benchmarks.py absent")
    src = BENCH.read_text()
    surface = src[src.index("def run_surface_scenario") :]
    surface = surface[: surface.index("\ndef ", 1)]
    hand_rolled = re.findall(r"\bregister_([a-z_]+)_tools\(", surface)
    assert not hand_rolled, (
        f"run_surface_scenario registers {sorted(set(hand_rolled))} by hand; it must "
        f"build the server through cli.attach_all so it cannot fall behind"
    )
    assert "attach_all" in surface, "the surface scenario must go through the one seam"


def test_attach_all_builds_the_whole_long_tail():
    """A floor, not an exact count: the number grows every campaign, and a test
    that pinned it exactly would be edited to pass rather than read."""
    root = tempfile.mkdtemp()
    app = TeeApp({"fake": FakeAdapter()}, project_root=root)
    cli.attach_all(app, root)
    names = app.registry.names()
    assert len(names) > 150, f"attach_all built only {len(names)} virtual tools"
    for prefix in ("wt_", "fd_", "eng_", "pc_", "pdf_", "sense_", "kb_"):
        assert any(n.startswith(prefix) for n in names), (
            f"no {prefix}* tool: attach_all missed that lane"
        )


def test_attach_all_returns_the_extract_store_the_capture_lane_needs():
    root = tempfile.mkdtemp()
    app = TeeApp({"fake": FakeAdapter()}, project_root=root)
    store = cli.attach_all(app, root)
    assert store is not None, "capture and assets are threaded off this store"


def test_the_canary_actually_fires(monkeypatch):
    """A gate that cannot fail is decoration. This is the exact shape of what
    went wrong: a lane defined in cli.py and absent from the list."""
    import sys

    module = sys.modules[__name__]
    monkeypatch.setattr(
        module, "CLI_SRC", CLI_SRC + "\n\ndef _attach_newlane(app, project):\n    pass\n"
    )
    with pytest.raises(AssertionError) as e:
        test_every_attach_function_is_in_the_one_list()
    assert "newlane" in str(e.value)
    assert "the benchmark cannot see" in str(e.value)
