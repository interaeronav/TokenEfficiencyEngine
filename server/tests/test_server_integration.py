"""End-to-end MCP session over the SDK's in-memory transport: a scripted
client drives the real server exactly as an MCP client would (initialize,
tools/list, tools/call), against the fake adapter."""

import json

import anyio
from mcp.client import Client
from mcp.types import ImageContent, TextContent

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.registry import VirtualTool
from tee.server import build_server


def payload(result):
    """Decode the JSON payload from a tool call result."""
    block = result.content[0]
    assert isinstance(block, TextContent)
    return json.loads(block.text)


def run_session(scenario, project_root="."):
    """Run `scenario(client)` against a fresh server over in-memory streams."""
    app = TeeApp({"fake": FakeAdapter()}, project_root=project_root)
    app.registry.register(
        VirtualTool(
            name="bl_demo_tool",
            description="Demo virtual tool for integration tests.",
            schema={
                "type": "object",
                "properties": {"n": {"type": "integer"}},
                "required": ["n"],
            },
            handler=lambda args: {"doubled": args["n"] * 2},
            tags=["demo"],
        )
    )
    server = build_server(app)

    async def main():
        async with Client(server) as client:
            await scenario(client)

    try:
        anyio.run(main)
    finally:
        app.shutdown()


def test_full_editing_session():
    async def scenario(client):
        # baseline stamp
        status = payload(await client.call_tool("tee_status", {}))
        stamp = status["adapters"]["fake"]["scene"]

        # one batch, three ops, one round-trip
        out = payload(
            await client.call_tool(
                "tee_batch",
                {
                    "ops": [
                        {"op": "create", "kind": "mesh", "name": "Torus"},
                        {"op": "create", "kind": "light", "name": "Key"},
                        {"op": "set", "id": "e1", "props": {"scale": 2}},
                    ]
                },
            )
        )
        assert out["ok"] is True
        assert out["created"] == ["e1", "e2"]
        assert out["details"]["e1"]["scale"] == 2
        checkpoint = out["checkpoint"]

        # diff since baseline returns the delta, not the scene
        delta = payload(
            await client.call_tool(
                "tee_diff",
                {"epoch": stamp["epoch"], "revision": stamp["revision"]},
            )
        )
        assert delta["created"] == ["e1", "e2"]
        assert "entities" not in delta

        # summary is compact and paged
        summary = payload(await client.call_tool("tee_scene_summary", {"limit": 1}))
        assert summary["total"] == 2
        assert len(summary["entities"]) == 1
        assert "offset=1" in summary["truncated"]

        # rollback, then the old stamp demands resync
        rolled = payload(await client.call_tool("tee_rollback", {"ref": checkpoint}))
        assert rolled["ok"] is True
        stale = payload(
            await client.call_tool(
                "tee_diff", {"epoch": stamp["epoch"], "revision": stamp["revision"]}
            )
        )
        assert stale["resync_required"] is True

    run_session(scenario)


def test_progressive_disclosure_roundtrip():
    async def scenario(client):
        hits = payload(await client.call_tool("tee_search_tools", {"query": "demo"}))
        assert hits["tools"][0]["name"] == "bl_demo_tool"

        desc = payload(await client.call_tool("tee_describe_tool", {"name": "bl_demo_tool"}))
        assert desc["schema"]["required"] == ["n"]

        result = payload(
            await client.call_tool("tee_call", {"name": "bl_demo_tool", "args": {"n": 21}})
        )
        assert result == {"ok": True, "doubled": 42}

        # validation failure is a compact structured error, not an exception
        bad = payload(
            await client.call_tool("tee_call", {"name": "bl_demo_tool", "args": {"n": "x"}})
        )
        assert bad["ok"] is False
        assert bad["error"]["code"] == "bad_argument_type"

    run_session(scenario)


def test_errors_are_compact_payloads():
    async def scenario(client):
        out = payload(await client.call_tool("tee_batch", {"ops": [{"op": "explode"}]}))
        assert out["ok"] is False
        assert out["error"]["code"] == "bad_op"
        assert "fix" in out["error"]
        assert "Traceback" not in json.dumps(out)

        unknown = payload(
            await client.call_tool("tee_diff", {"epoch": 0, "revision": 0, "adapter": "nope"})
        )
        assert unknown["ok"] is False
        assert unknown["error"]["code"] == "unknown_adapter"

    run_session(scenario)


def test_capture_returns_inline_image():
    async def scenario(client):
        result = await client.call_tool("tee_capture", {"max_kb": 8})
        image = result.content[0]
        assert isinstance(image, ImageContent)
        assert image.mime_type in ("image/jpeg", "image/jpg")

    run_session(scenario)


def test_memory_roundtrip(tmp_path):
    async def scenario(client):
        saved = payload(
            await client.call_tool(
                "tee_remember",
                {"key": "engine", "value": "blender 5.2", "note": "phase 1 done"},
            )
        )
        assert saved["ok"] is True
        recalled = payload(await client.call_tool("tee_recall", {}))
        assert recalled["facts"]["engine"] == "blender 5.2"

    run_session(scenario, project_root=tmp_path)


def test_concurrent_tool_calls_are_serialized_and_all_succeed():
    async def scenario(client):
        import anyio as _anyio

        outcomes = []

        async def one_batch(i):
            result = payload(
                await client.call_tool(
                    "tee_batch",
                    {"ops": [{"op": "create", "kind": "mesh", "name": f"Obj{i}"}]},
                )
            )
            outcomes.append(result)

        async with _anyio.create_task_group() as tg:
            for i in range(24):
                tg.start_soon(one_batch, i)

        assert len(outcomes) == 24
        assert all(o["ok"] is True for o in outcomes), [o for o in outcomes if not o.get("ok")]
        summary = payload(await client.call_tool("tee_scene_summary", {"limit": 50}))
        assert summary["total"] == 24

    run_session(scenario)


def test_responses_are_compact_json_not_pretty_printed():
    async def scenario(client):
        result = await client.call_tool("tee_status", {})
        text = result.content[0].text
        assert "\n" not in text  # compact separators, no indent
        json.loads(text)

    run_session(scenario)
