"""A68 P2: the model is told - by the server, from what it serves.

The MCP instructions used to say TEE "drives Unreal Engine and Blender", on
every server, whatever it served. They are now built from the app: the
lanes and what each is for, that none is the default unless declared, how
an omitted adapter= routes, which lanes never need a DCC, and when to search
the long tail. A deferring host indexes exactly tool names plus this string
and truncates past 2 KB (research 08), so the cap is a law and the
seven-lane worst case is measured against it."""

from __future__ import annotations

import json

import anyio
import pytest
from mcp.client import Client
from test_lane_routing import Lane

from tee import cli
from tee.app import TeeApp
from tee.kernel import lanes
from tee.kernel.adapter import FakeAdapter
from tee.server import ADAPTER_PARAM_DOC, build_server

CAP = lanes.INSTRUCTIONS_CAP_BYTES


def _serve_desktop(tmp_path):
    from importlib import import_module

    from tee.adapters.partkiln import PartkilnAdapter

    fake_kernel = import_module("fixtures_partkiln").FakeKernel
    return cli.build_app(
        [
            cli._blender_lane("127.0.0.1", 1),
            cli.Lane("partkiln", PartkilnAdapter(tmp_path, kernel=fake_kernel())),
            cli._seamkiln_lane(str(tmp_path)),
        ],
        str(tmp_path),
        allow_code_exec=False,
    )


def test_the_desktop_instructions_name_every_lane_and_its_purpose(tmp_path):
    app = _serve_desktop(tmp_path)
    try:
        text = build_server(app).instructions
        assert len(text.encode()) <= CAP
        assert "drives Unreal Engine and Blender" not in text
        assert "none of them the hub" in text and "No lane is the default." in text
        assert "blender (3D scene: model, materials, physics, render (pixels))" in text
        assert "partkiln (mechanical CAD, headless" in text
        assert "seamkiln (garment CAD + drape, headless" in text
        assert "entity id to the lane that holds it" in text
        assert "never need Blender or Unreal" in text
        assert lanes.LEGEND in text
        assert "tee_search_tools" in text and "tee_describe_tool" in text
    finally:
        app.shutdown()


def test_a_declared_default_is_stated(tmp_path):
    app = TeeApp(
        {"fake": FakeAdapter(), "fake2": FakeAdapter()},
        project_root=tmp_path,
        default_adapter="fake2",
    )
    try:
        text = build_server(app).instructions
        assert "Declared default lane: fake2" in text
        assert "No lane is the default." not in text
    finally:
        app.shutdown()


def test_seven_lanes_stay_under_the_cap(tmp_path):
    """The worst case the CLI can build: every adapter it knows, each with
    a purpose. The purposes are what gets trimmed first, never the rule."""
    seven = {
        name: Lane(name)
        for name in ("fake", "blender", "unreal", "freecad", "godot", "seamkiln", "partkiln")
    }
    app = TeeApp(seven, project_root=tmp_path)
    try:
        text = build_server(app).instructions
        assert len(text.encode()) <= CAP
        for name in seven:
            assert name in text
        assert "a batch goes where its content says" in text
    finally:
        app.shutdown()


def test_a_pathological_lane_list_is_still_capped(tmp_path):
    many = {f"lane{i:02d}": Lane(f"lane{i:02d}") for i in range(60)}
    app = TeeApp(many, project_root=tmp_path)
    try:
        text = build_server(app).instructions
        assert len(text.encode()) <= CAP
    finally:
        app.shutdown()


def test_the_wire_carries_the_adapter_line_and_no_default(tmp_path):
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    server = build_server(app)

    async def fetch():
        async with Client(server) as client:
            return (await client.list_tools()).tools

    try:
        tools = anyio.run(fetch)
        with_adapter = [t for t in tools if "adapter" in (t.input_schema.get("properties") or {})]
        assert len(with_adapter) == 8
        for tool in with_adapter:
            prop = tool.input_schema["properties"]["adapter"]
            assert prop["description"] == ADAPTER_PARAM_DOC, tool.name
            assert "default" not in prop, tool.name  # SI-B6 stands
        batch = next(t for t in tools if t.name == "tee_batch")
        assert "the ops pick the lane" in batch.description
        search = next(t for t in tools if t.name == "tee_search_tools")
        assert "drape a garment" in search.description
        assert json.dumps([t.model_dump(mode="json") for t in tools])  # serialises
    finally:
        app.shutdown()


@pytest.mark.parametrize("name", ["tee_batch", "tee_scene_summary", "tee_capture"])
def test_descriptions_stay_under_two_kb(name, tmp_path):
    from tee.server import _DESC

    assert len(_DESC[name].encode()) <= 2_048
