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
            capability="read-scene",
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
        # echo-free batch report (hard rule 2): everything applied exactly as
        # requested, so no details ride back - only the id->name addressing
        # map. Drift (a rename, a clamp) would appear under details.
        assert out["names"] == {"e1": "Torus", "e2": "Key"}
        assert "details" not in out
        ent = payload(await client.call_tool("tee_entity_detail", {"entity_id": "e1"}))
        assert ent["entity"]["scale"] == 2
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
        assert len(summary["items"]) == 1
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
        assert hits["items"][0]["name"] == "bl_demo_tool"

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


MINIMAL_ARGS = {
    "tee_status": {},
    "tee_recall": {},
    "tee_remember": {"note": "canary"},
    "tee_scene_summary": {},
    "tee_entity_detail": {"entity_id": "e999"},
    "tee_diff": {"epoch": 0, "revision": 0},
    "tee_batch": {"ops": [{"op": "create", "kind": "mesh", "name": "X"}]},
    "tee_checkpoint": {"label": "canary"},
    "tee_rollback": {"ref": "cp1"},
    "tee_job": {"job_id": "job999"},
    "tee_media": {"source": "nothing-ingested"},
    "tee_script": {"code": "result = 1 + 1"},
    # loopback refuses via the SSRF guard - a deterministic, offline,
    # model-visible answer (the refusal names the allow_local fix)
    "tee_web_lookup": {"url": "http://127.0.0.1/x", "question": "canary"},
    "tee_search_tools": {"query": "demo"},
    "tee_describe_tool": {"name": "bl_demo_tool"},
    "tee_call": {"name": "bl_demo_tool", "args": {"n": 1}},
}


def test_every_tool_answers_with_model_visible_content():
    """Silent-content-drop canary: every tool must return content a model
    can read - either parseable JSON or an image block - never nothing."""
    from mcp.types import ImageContent

    async def scenario(client):
        listed = (await client.list_tools()).tools
        for tool in listed:
            if tool.name in ("tee_capture", "tee_media"):
                pass
            if tool.name == "tee_capture":
                result = await client.call_tool("tee_capture", {"max_kb": 8})
                assert isinstance(result.content[0], (ImageContent, TextContent))
                continue
            args = MINIMAL_ARGS[tool.name]
            result = await client.call_tool(tool.name, args)
            assert result.content, tool.name
            parsed = payload(result)
            assert "ok" in parsed, tool.name

    run_session(scenario)


def test_stdio_subprocess_end_to_end(tmp_path):
    """The real transport: spawn `tee serve` as a subprocess over stdio and
    drive initialize + tools/list + a call through the SDK client."""
    import sys
    from pathlib import Path

    import anyio
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    server_dir = Path(__file__).resolve().parents[1]
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "tee.cli", "serve", "--adapter", "fake", "--project", str(tmp_path)],
        cwd=str(server_dir),
        env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(server_dir / "src")},
    )

    async def main():
        async with (
            stdio_client(params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()
            tools = await session.list_tools()
            assert any(t.name == "tee_status" for t in tools.tools)
            result = await session.call_tool(
                "tee_batch",
                {"ops": [{"op": "create", "kind": "mesh", "name": "Stdio"}]},
            )
            parsed = json.loads(result.content[0].text)
            assert parsed["ok"] is True
            assert parsed["created"] == ["e1"]

    anyio.run(main)


def test_columnar_encoding_on_large_summaries():
    """Phase 8 acceptance (8.2): a 100-entity summary comes back columnar
    and >= 35% smaller than the row-of-objects form; small summaries are
    untouched."""

    async def scenario(client):
        ops = [{"op": "create", "kind": "cube", "name": f"B{i}"} for i in range(100)]
        payload(await client.call_tool("tee_batch", {"ops": ops}))

        out = payload(await client.call_tool("tee_scene_summary", {"limit": 100}))
        assert out["columnar"] == ["items"]
        cols, rows = out["items"]["cols"], out["items"]["rows"]
        assert len(rows) == 100
        decoded = [dict(zip(cols, r[: len(cols)], strict=True)) for r in rows]
        names = {d["name"] for d in decoded}
        assert "B42" in names

        from tee.kernel.budget import estimate_tokens

        row_form = {**out, "entities": decoded}
        row_form.pop("columnar")
        assert estimate_tokens(out) <= estimate_tokens(row_form) * 0.65

        small = payload(await client.call_tool("tee_scene_summary", {"limit": 5}))
        assert "columnar" not in small
        assert isinstance(small["items"], list)

    run_session(scenario)


def test_adapter_omitted_resolves_to_sole_adapter():
    # SI-B6: a single-adapter server (every real deployment) must accept
    # calls that omit adapter= instead of failing on a 'fake' default.
    async def scenario(client):
        out = payload(await client.call_tool("tee_scene_summary", {}))
        assert out["ok"] is True
        cp = payload(await client.call_tool("tee_checkpoint", {"label": "solo"}))
        assert cp["ok"] is True

    run_session(scenario)


def test_adapter_omitted_with_two_adapters_reads_across_and_writes_loud():
    """SI-B6 as A68 keeps it: a WRITE two lanes accept and none was declared
    for fails loud, naming them. A READ with no lane is no longer a
    refusal - it is the lanes at a glance."""
    app = TeeApp({"fake": FakeAdapter(), "fake2": FakeAdapter()}, project_root=".")
    server = build_server(app)

    async def main():
        async with Client(server) as client:
            out = payload(await client.call_tool("tee_scene_summary", {}))
            assert out["ok"] is True and set(out["lanes"]) == {"fake", "fake2"}
            write = payload(
                await client.call_tool("tee_batch", {"ops": [{"op": "create", "name": "x"}]})
            )
            assert write["ok"] is False
            assert write["error"]["code"] == "adapter_required"
            assert "fake, fake2" in write["error"]["message"]
            named = payload(await client.call_tool("tee_scene_summary", {"adapter": "fake2"}))
            assert named["ok"] is True and named["adapter"] == "fake2"

    try:
        anyio.run(main)
    finally:
        app.shutdown()
