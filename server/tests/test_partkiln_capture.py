"""A66 gap 3, closed by A68 P3 - the capture refusal names a route that exists.

The shipped 0.20.0 refusal ended "A JPEG through Blender is the P6 opt-in."
No such opt-in was ever built; 0.21.1 replaced it with four manual calls "in
a TEE served on Blender", false the moment one server held several lanes.
A refusal that names a door that is not there is worse than a plain no: the
reader stops reading and goes looking for it. So these tests hold the fix
to two things at once - that it names the two-call route `pk_export into=`
then `tee_capture adapter=` in order, and that every tool it names exists.
"""

from __future__ import annotations

import re

import pytest

from tee.adapters.partkiln.adapter import PartkilnAdapter
from tee.kernel import trust
from tee.kernel.errors import TeeError

# Every `xx_yyy` token in the fix that looks like a TEE tool name.
_TOOL_TOKEN = re.compile(r"\b((?:pk|as|tee|sk|fc)_[a-z_]+)\b")


@pytest.fixture
def refusal(tmp_path) -> TeeError:
    adapter = PartkilnAdapter(tmp_path)
    with pytest.raises(TeeError) as err:
        adapter.capture("viewport", 65536)
    return err.value


def test_capture_refuses_with_its_own_code(refusal) -> None:
    assert refusal.code == "pk_capture_text_first"
    assert "numbers are the evidence" in refusal.message


def test_the_fix_names_no_door_that_is_not_there(refusal) -> None:
    """The defect itself, twice over: an advertised P6 opt-in nobody could
    take, then a manual route in "a TEE served on Blender" that a multi-lane
    server made false."""
    fix = refusal.fix.lower()
    assert "opt-in" not in fix and "p6" not in fix
    assert "nothing in this session" not in fix
    assert "served on partkiln" not in fix and "served on blender" not in fix
    assert "as_ingest" not in fix and "as_import" not in fix, "the four-call route is gone"


def test_the_fix_walks_the_two_call_route_in_order(refusal) -> None:
    """pk_export into= lands the GLB in a served lane that renders, then
    tee_capture adapter= looks at it - the route kernel/handoff_import built."""
    fix = refusal.fix
    for step in ("pk_export", "into=", "tee_capture", "adapter="):
        assert step in fix, step
    order = [fix.index(s) for s in ("pk_export", "into=", "tee_capture", "adapter=")]
    assert order == sorted(order), "the steps must read in the order they are run"
    assert "format=glb" in fix
    assert "into=auto" in fix, "auto is the one served lane that imports GLB"
    assert "tee_status" in fix, "where the lane names come from"
    assert "verify" in fix, "the read-back verdict is part of the route"


def test_the_fix_says_what_to_do_when_no_lane_renders(refusal) -> None:
    fix = refusal.fix
    assert "tee serve --adapter blender --adapter partkiln" in fix
    assert "never renders" in fix


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


def test_the_route_the_fix_names_is_the_one_the_tool_takes() -> None:
    """The fix is not prose about a tool: `pk_export` really takes `into`,
    and `capture()` still takes no app - the route is a call the model
    makes, not a side effect of asking this lane for pixels."""
    import inspect

    from tee.adapters.partkiln import tools

    source = inspect.getsource(tools.register_partkiln_tools)
    assert '"into"' in source and "handoff_import" in source
    assert "app" not in inspect.signature(PartkilnAdapter.capture).parameters
