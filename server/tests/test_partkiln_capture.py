"""A66 gap 3 — the capture refusal must name a route the caller can walk.

The shipped 0.20.0 refusal ended "A JPEG through Blender is the P6 opt-in."
No such opt-in was ever built. A refusal that names a door that is not there
is worse than a plain no: the reader stops reading and goes looking for it.
So these tests hold the fix to two things at once - that it names the manual
route STEP BY STEP, and that every tool it names is a tool that exists.

Why the route stays manual, checked here so the reason cannot rot:
`capture()` is handed no app to reach the asset lane through, and the
partkiln lane builds no Blender adapter of its own - one is in the process
only when the operator lists `--adapter blender` too (the Desktop manifest
does, since 2026-09-04), and even then it is `as_import`'s batch, not
`capture()`, that reaches it.
"""

from __future__ import annotations

import re

import pytest

from tee.adapters.partkiln.adapter import PartkilnAdapter
from tee.kernel import trust
from tee.kernel.errors import TeeError

# Every `xx_yyy` token in the fix that looks like a TEE tool name.
_TOOL_TOKEN = re.compile(r"\b((?:pk|as|tee)_[a-z_]+)\b")


@pytest.fixture
def refusal(tmp_path) -> TeeError:
    adapter = PartkilnAdapter(tmp_path)
    with pytest.raises(TeeError) as err:
        adapter.capture("viewport", 65536)
    return err.value


def test_capture_refuses_with_its_own_code(refusal) -> None:
    assert refusal.code == "pk_capture_text_first"
    assert "numbers are the evidence" in refusal.message


def test_the_fix_names_no_opt_in_that_does_not_exist(refusal) -> None:
    """The defect itself: an advertised P6 opt-in nobody can take."""
    fix = refusal.fix.lower()
    assert "opt-in" not in fix
    assert "p6" not in fix


def test_the_fix_walks_the_route_that_actually_exists(refusal) -> None:
    """Four steps, in order, each naming the tool that performs it - the
    same route `examples/acceptance/run_tee.py` step 7 walks."""
    fix = refusal.fix
    for step in ("pk_export", "as_ingest", "as_import", "tee_capture"):
        assert step in fix, step
    order = [fix.index(s) for s in ("pk_export", "as_ingest", "as_import", "tee_capture")]
    assert order == sorted(order), "the steps must read in the order they are run"
    assert "format=glb" in fix and "adapter=blender" in fix
    assert "tee serve --adapter blender" in fix, "the route needs a server that HAS Blender"
    assert "stem" in fix.lower(), "as_ingest keys a local asset by file stem - a real trap"


def test_every_tool_the_fix_names_is_a_tool_that_exists(refusal) -> None:
    """The guard that keeps the fix true: `trust.capability_for` refuses a
    name that is not in the trust table, and every registered tool is."""
    named = sorted(set(_TOOL_TOKEN.findall(refusal.fix)))
    assert named, "a fix with no tool in it is not a fix"
    for name in named:
        assert trust.capability_for(name), name


def test_the_text_routes_are_still_offered_first(refusal) -> None:
    """Text before pixels is the lane's whole posture, not a limitation."""
    fix = refusal.fix
    for name in ("pk_drawing", "pk_measure", "tee_entity_detail"):
        assert name in fix, name
    assert fix.index("pk_drawing") < fix.index("pk_export")


def test_the_partkiln_lane_builds_no_blender_adapter_of_its_own() -> None:
    """The reason the route is manual, pinned so a later reader does not
    have to take the docstring's word for it. Until 2026-09-04 a partkiln
    server held exactly one adapter; now `tee serve` holds every adapter
    listed in ONE app, so what stays true is narrower: the partkiln lane
    constructs only `PartkilnAdapter`, and `capture()` takes no app."""
    import inspect

    from tee import cli

    source = inspect.getsource(cli._partkiln_lane)
    assert "PartkilnAdapter(" in source
    assert "blender" not in source.lower()
    assert "app" not in inspect.signature(PartkilnAdapter.capture).parameters
