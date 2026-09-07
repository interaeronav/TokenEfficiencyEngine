"""A68: reads that name no lane are answered ACROSS lanes, never defaulted.

On a multi-lane server with no declared default: the summary is an overview
of every lane, an entity is found where it lives, a checkpoint covers every
lane that holds state, a rollback finds the lane that owns the ref (ids were
global and lane-stamped all along), a capture goes to the one lane that can
render, and a diff - whose stamps are per lane - asks for the lane by name.
A read never snapshots."""

from __future__ import annotations

import json

import anyio
import pytest
from mcp.client import Client
from mcp.types import TextContent
from test_lane_routing import Lane

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter, LaneVocab
from tee.kernel.checkpoints import CheckpointManager
from tee.kernel.errors import TeeError
from tee.kernel.script import run_script
from tee.server import build_server

PART = [{"op": "create", "kind": "part", "name": "bracket"}]
CUBE = [{"op": "create", "kind": "cube", "name": "box"}]


def _desk(tmp_path) -> TeeApp:
    return TeeApp(
        {
            "blender": Lane("blender", kinds=("cube", "light")),
            "partkiln": Lane("partkiln", kinds=("part", "sketch"), kind_optional=False),
            "seamkiln": Lane("seamkiln", kinds=("panel", "seam"), kind_optional=False),
        },
        project_root=tmp_path,
    )


@pytest.fixture
def desk(tmp_path):
    app = _desk(tmp_path)
    yield app
    app.shutdown()


def _payload(result):
    block = result.content[0]
    assert isinstance(block, TextContent), block
    return json.loads(block.text)


def _call(app, name, args):
    server = build_server(app)

    async def go():
        async with Client(server) as client:
            return await client.call_tool(name, args)

    return anyio.run(go)


# -- overview ----------------------------------------------------------------


def test_a_summary_with_no_lane_is_the_lanes_at_a_glance(desk):
    desk.run_batch("partkiln", PART)
    out = _payload(_call(desk, "tee_scene_summary", {}))
    assert out["ok"] and set(out["lanes"]) == {"blender", "partkiln", "seamkiln"}
    # the first batch on a cold lane warms it (a resync: epoch 1, revision 1)
    # and then applies (revision 2); the overview reports the lane's own stamp
    assert out["lanes"]["partkiln"] == {
        "connected": True,
        "entities": 1,
        "epoch": 1,
        "revision": 2,
        "kinds": {"part": 1},
    }
    assert out["lanes"]["blender"]["entities"] == 0 and "kinds" not in out["lanes"]["blender"]
    assert "items" not in out and "adapter=" in out["note"]


def test_a_summary_that_names_a_lane_says_which(desk):
    desk.run_batch("blender", CUBE)
    out = _payload(_call(desk, "tee_scene_summary", {"adapter": "blender"}))
    assert out["adapter"] == "blender" and out["items"][0]["name"] == "box"


def test_a_single_lane_summary_changes_nothing(tmp_path):
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        out = _payload(_call(app, "tee_scene_summary", {}))
        assert "lanes" not in out and "adapter" not in out and out["total"] == 0
    finally:
        app.shutdown()


# -- locate ------------------------------------------------------------------


def test_an_entity_is_found_where_it_lives(desk):
    desk.run_batch("blender", CUBE)  # blender's e1
    desk.run_batch("partkiln", [{"op": "create", "kind": "sketch", "name": "base"}])
    made = desk.run_batch("partkiln", PART)  # partkiln's e2
    eid = made["created"][0]
    out = _payload(_call(desk, "tee_entity_detail", {"entity_id": eid}))
    assert out["adapter"] == "partkiln" and out["entity"]["name"] == "bracket"


def test_an_unknown_entity_names_the_lanes_searched(desk):
    out = _payload(_call(desk, "tee_entity_detail", {"entity_id": "nope"}))
    assert out["error"]["code"] == "unknown_entity"
    assert "blender, partkiln, seamkiln" in out["error"]["message"]


def test_an_entity_in_two_lanes_is_ambiguous(desk):
    desk.run_batch("blender", CUBE)
    desk.run_batch("partkiln", PART)  # both lanes now hold an e1
    with pytest.raises(TeeError) as err:
        desk.locate("e1")
    assert err.value.code == "entity_ambiguous" and "blender, partkiln" in err.value.message


# -- checkpoints -------------------------------------------------------------


def test_a_rollback_finds_the_lane_that_owns_the_ref(desk):
    made = desk.run_batch("partkiln", PART)  # auto checkpoint cp1 on partkiln
    desk.run_batch("blender", CUBE)  # cp2 on blender
    out = _payload(_call(desk, "tee_rollback", {"ref": made["checkpoint"]}))
    assert out["ok"] and out["adapter"] == "partkiln"
    assert out["restored"]["adapter"] == "partkiln"
    assert not desk.caches["partkiln"].entities and desk.caches["blender"].entities


def test_a_label_in_two_lanes_is_ambiguous_and_an_unknown_ref_lists_recent(desk):
    desk.run_batch("partkiln", PART, label="before")
    desk.run_batch("blender", CUBE, label="before")
    out = _payload(_call(desk, "tee_rollback", {"ref": "before"}))
    assert out["error"]["code"] == "checkpoint_ambiguous"
    assert (
        "partkiln (cp1)" in out["error"]["message"] and "blender (cp2)" in out["error"]["message"]
    )
    out = _payload(_call(desk, "tee_rollback", {"ref": "cp9"}))
    assert out["error"]["code"] == "unknown_checkpoint"
    assert "cp1:before (partkiln)" in out["error"]["fix"]


def test_two_adapters_with_one_id_keep_separate_stacks():
    manager = CheckpointManager()
    a, b = FakeAdapter(), FakeAdapter()  # both report id "fake"
    first = manager.create(a, "x", 0, lane="a")
    manager.create(b, "x", 0, lane="b")
    assert [c["adapter"] for c in manager.list()] == ["a", "b"]
    assert manager.find(first.id) == ("a", first)
    with pytest.raises(TeeError) as err:
        manager.find("x")
    assert err.value.code == "checkpoint_ambiguous"
    # without a lane the old keying stands: one stack per adapter id
    manager.create(a, "y", 0)
    assert manager.list()[-1]["adapter"] == "fake"


def test_a_checkpoint_with_no_lane_covers_every_lane_with_state(desk):
    out = _payload(_call(desk, "tee_checkpoint", {"label": "empty"}))
    assert out["error"]["code"] == "nothing_to_checkpoint"
    desk.run_batch("partkiln", PART)
    out = _payload(_call(desk, "tee_checkpoint", {"label": "after"}))
    assert out["ok"] and list(out["checkpoints"]) == ["partkiln"]
    assert sorted(out["skipped"]) == ["blender", "seamkiln"]
    assert desk.checkpoints.find("after")[0] == "partkiln"


def test_a_diff_with_no_lane_asks_for_one(desk):
    out = _payload(_call(desk, "tee_diff", {"epoch": 0, "revision": 0}))
    assert out["error"]["code"] == "adapter_required"
    assert "per lane" in out["error"]["message"]
    assert "blender, partkiln, seamkiln" in out["error"]["fix"]


# -- capture -----------------------------------------------------------------


class Pixels(FakeAdapter):
    def __init__(self, renders=True, can=None):
        super().__init__()
        self._renders = renders
        self._can = can

    def vocab(self):
        return LaneVocab(renders=self._renders, purpose="pixels")

    def can_render(self):
        return True if self._can is None else self._can


def _lanes(tmp_path, **lanes):
    return TeeApp(lanes, project_root=tmp_path)


def test_a_capture_with_no_lane_goes_to_the_one_lane_that_renders(tmp_path):
    app = _lanes(
        tmp_path,
        text=Pixels(renders=False),
        scene=Pixels(),
        garment=Pixels(can=False),  # renders, but nothing is arranged
    )
    try:
        assert app.renderers() == ["scene"]
        result = _call(app, "tee_capture", {})
        assert result.content[0].type == "image"
    finally:
        app.shutdown()


def test_a_capture_with_no_renderer_or_two_refuses(tmp_path):
    none = _lanes(tmp_path, text=Pixels(renders=False), garment=Pixels(can=False))
    try:
        out = _payload(_call(none, "tee_capture", {}))
        assert out["error"]["code"] == "capture_no_renderer"
        assert "text, garment" in out["error"]["fix"]
    finally:
        none.shutdown()
    two = _lanes(tmp_path, scene=Pixels(), level=Pixels())
    try:
        out = _payload(_call(two, "tee_capture", {}))
        assert out["error"]["code"] == "capture_ambiguous"
        assert "scene, level" in out["error"]["message"]
    finally:
        two.shutdown()


# -- the script lane ---------------------------------------------------------


def test_a_script_on_an_unbound_server_reads_across_lanes_and_snapshots_nothing(desk):
    made = desk.run_batch("partkiln", PART)
    eid = made["created"][0]
    code = (
        "lanes = summary()\n"
        f"row = detail({eid!r})\n"
        "saved = call('report_savings', {})\n"
        "result = {'lanes': sorted(keys(lanes['lanes'])), 'name': row['name']}\n"
    )
    out = run_script(desk, code, default_adapter=None)
    assert out["result"] == {"lanes": ["blender", "partkiln", "seamkiln"], "name": "bracket"}
    assert "checkpoints" not in out, "a read and an agnostic call snapshot nothing"
