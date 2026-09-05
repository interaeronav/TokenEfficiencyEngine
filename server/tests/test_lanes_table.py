"""A68: the lane table - a scene-writing tool says which scene.

`kernel/lanes.py` is one table, like the trust table: families first, then
explicit rows. Every registered tool resolves a lane (or None, agnostic);
every write-scene / exec-code tool resolves one that is not None, and one
that does not fails at REGISTRATION, so a new scene-writing tool cannot slip
in without saying which scene it writes."""

from __future__ import annotations

import pytest

from tee.app import TeeApp
from tee.kernel import lanes
from tee.kernel.adapter import FakeAdapter
from tee.kernel.registry import ToolRegistry, VirtualTool

SCENE_WRITING = {"write-scene", "exec-code"}
KNOWN = {"blender", "unreal", "freecad", "partkiln", "seamkiln", "godot", "fake", "uefn"}


def _noop(args):
    return {}


def test_families_and_explicit_rows_resolve():
    assert lanes.lane_for("bl_render") == "blender"
    assert lanes.lane_for("hb_cabinet") == "blender"
    assert lanes.lane_for("sim_settle") == "blender"
    assert lanes.lane_for("ue_capture") == "unreal"
    assert lanes.lane_for("pin_set") == "unreal"
    assert lanes.lane_for("fc_drawing") == "freecad"
    assert lanes.lane_for("pk_export") == "partkiln"
    assert lanes.lane_for("sk_fit") == "seamkiln"
    assert lanes.lane_for("wall_with_openings") == "blender"
    assert lanes.lane_for("as_import") == lanes.ADAPTER_ARG
    assert lanes.lane_for("uefn_place_device") == "uefn"
    assert lanes.lane_for("pdf_compose") is None
    assert lanes.lane_for("pc_slice") is None


def test_every_desktop_tool_resolves_a_lane_the_table_knows(tmp_path):
    """The composition the manifest serves, every kernel lane attached:
    each tool's lane is an adapter name, ADAPTER_ARG, a proxy label, or
    None - and every scene-writing tool has one."""
    from tee import cli

    app = cli.build_app(
        [cli.Lane("blender", FakeAdapter()), cli._seamkiln_lane(str(tmp_path))],
        str(tmp_path),
        allow_code_exec=False,
    )
    try:
        store = cli._attach_extract(app, str(tmp_path), with_handoff=True)
        cli._attach_assets(app, str(tmp_path), store)
        cli._attach_capture(app, str(tmp_path), store)
        cli._attach_pointcloud(app, str(tmp_path))
        cli._attach_pipeline(app, str(tmp_path))
        cli._attach_design(app, str(tmp_path))
        cli._attach_senses(app, str(tmp_path))
        cli._attach_pdf(app, str(tmp_path))
        cli._attach_purge(app, str(tmp_path))
        cli._attach_physical(app, str(tmp_path))
        cli._attach_uefn(app, str(tmp_path))
        cli._attach_kb(app, str(tmp_path))
        cli._attach_llm(app, str(tmp_path))
        cli._attach_web(app, str(tmp_path))
        writers = []
        for tool in app.registry._tools.values():
            assert tool.lane is None or tool.lane == lanes.ADAPTER_ARG or tool.lane in KNOWN, (
                tool.name,
                tool.lane,
            )
            if tool.capability in SCENE_WRITING:
                writers.append(tool.name)
                assert tool.lane is not None, f"{tool.name} writes a scene and names none"
        assert writers, "the composition registers scene-writing tools"
        assert "as_sheet" not in writers, "a contact sheet is an artifact, not a scene"
        assert app.registry.describe("pk_export")["lane"] == "partkiln"
        assert "lane" not in app.registry.describe("pdf_compose")
    finally:
        app.shutdown()


def test_a_scene_writing_tool_with_no_lane_fails_at_registration():
    registry = ToolRegistry()
    with pytest.raises(ValueError, match="must name its lane"):
        registry.register(
            VirtualTool(
                name="mystery_write",
                description="writes somewhere",
                schema={"type": "object", "properties": {}},
                handler=_noop,
                capability="write-scene",
            )
        )
    # the same tool, told where it writes, registers
    registry.register(
        VirtualTool(
            name="mystery_write",
            description="writes somewhere",
            schema={"type": "object", "properties": {}},
            handler=_noop,
            capability="write-scene",
            lane=lanes.ADAPTER_ARG,
        )
    )
    assert registry.describe("mystery_write")["lane"] == "adapter="


def test_search_indexes_the_lane_and_prefers_served_lanes(tmp_path):
    app = TeeApp({"partkiln": FakeAdapter()}, project_root=tmp_path)
    try:
        reg = app.registry
        for name, lane in (("bl_cut", "blender"), ("pk_cut", "partkiln"), ("cut_plain", None)):
            reg.register(
                VirtualTool(
                    name=name,
                    description="cut a thing",
                    schema={"type": "object", "properties": {}},
                    handler=_noop,
                    capability="read-scene",
                    lane=lane,
                )
            )
        # the lane name is a haystack: "partkiln cut" reaches pk_cut first
        names = [i["name"] for i in reg.search("partkiln cut", limit=3)["items"]]
        assert names[0] == "pk_cut"
        # at equal score the unserved lane's tool sinks below the served one
        names = [i["name"] for i in reg.search("cut", limit=3)["items"]]
        assert names.index("bl_cut") > names.index("pk_cut")
        assert names.index("bl_cut") > names.index("cut_plain")
    finally:
        app.shutdown()


def test_status_says_what_each_lane_is_for(tmp_path):
    from tee.adapters.partkiln.adapter import PartkilnAdapter
    from tee.adapters.seamkiln import SeamkilnAdapter

    app = TeeApp(
        {"partkiln": PartkilnAdapter(tmp_path), "seamkiln": SeamkilnAdapter(tmp_path)},
        project_root=tmp_path,
    )
    try:
        status = app.status()
        assert "default_adapter" not in status
        lanes_block = status["lanes"]
        assert lanes_block["partkiln"].startswith("mechanical CAD, headless")
        assert "ops create, set, delete, param_set, export, check" in lanes_block["partkiln"]
        assert "kinds angle, axis, ball, chamfer, coil, combine +31" in lanes_block["partkiln"]
        assert "tools pk_" in lanes_block["partkiln"] and "no pixels" in lanes_block["partkiln"]
        assert (
            "garment CAD" in lanes_block["seamkiln"]
            and "kinds block, panel, seam" in (lanes_block["seamkiln"])
        )
        assert all(len(line) < 260 for line in lanes_block.values()), "capped"
    finally:
        app.shutdown()
    solo = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        assert "lanes" not in solo.status(), "one lane needs no map"
    finally:
        solo.shutdown()


def test_a_script_checkpoints_only_the_lane_a_tool_touches(tmp_path):
    """Before A68 every call() saved the default lane's snapshot - a full
    .blend for pdf_compose. Now an agnostic tool snapshots nothing and a
    lane-bound one snapshots its lane."""
    from tee.kernel.script import run_script

    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        app.registry.register(
            VirtualTool(
                name="fake_touch",
                description="touches the fake lane",
                schema={"type": "object", "properties": {}},
                handler=_noop,
                capability="read-scene",
                lane="fake",
            )
        )
        out = run_script(app, "result = call('report_savings', {})", default_adapter=None)
        assert "checkpoints" not in out, "an agnostic call takes no snapshot"
        out = run_script(app, "result = call('fake_touch', {})", default_adapter=None)
        assert list(out["checkpoints"]) == ["fake"], "a lane-bound call snapshots its lane"
    finally:
        app.shutdown()


def test_families_for_and_the_legend():
    assert lanes.families_for("blender")[:3] == ("bl_", "hb_", "sim_")
    assert "wall_with_openings" in lanes.families_for("blender")
    assert lanes.families_for("partkiln") == ("pk_",)
    assert "pk_ partkiln" in lanes.LEGEND and "headless" in lanes.LEGEND
