"""The MCP surface stays at exactly 4 tools (decision A28), verified the
way a client sees it, and the tools answer with compact JSON."""

import json

import anyio
import numpy as np
import pytest
from PIL import Image

pytest.importorskip("mcp")
from mcp.client import Client

from voxkiln.engine import FakeEngine
from voxkiln.jobs import JobStore
from voxkiln.mcp_server import build_server

EXPECTED_TOOLS = {"gen3d_generate", "gen3d_wait", "gen3d_query", "gen3d_status"}


@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("VOXKILN_CACHE", str(tmp_path / "cache"))
    return JobStore(engine=FakeEngine(), out_dir=tmp_path / "out")


def _call(server, tool, args):
    async def run():
        async with Client(server) as client:
            result = await client.call_tool(tool, args)
            return result.content[0].text

    return anyio.run(run)


def test_surface_is_exactly_four_tools(store):
    server = build_server(store)

    async def fetch():
        async with Client(server) as client:
            listed = await client.list_tools()
            return {t.name for t in listed.tools}

    assert anyio.run(fetch) == EXPECTED_TOOLS


def test_generate_tool_returns_report(store, tmp_path):
    img = tmp_path / "in.png"
    Image.fromarray(np.zeros((16, 16, 3), dtype=np.uint8)).save(img)
    server = build_server(store)
    text = _call(
        server,
        "gen3d_generate",
        {
            "image_path": str(img),
            "params": {"texture_size": 64, "target_faces": 2000},
            "seed": 1,
        },
    )
    payload = json.loads(text)
    assert payload["state"] == "done"
    assert payload["provenance"]["ai_generated"] is True


def test_status_tool_reports_backend(store):
    server = build_server(store)
    payload = json.loads(_call(server, "gen3d_status", {}))
    assert "probe" in payload and "deps" in payload


def test_bad_image_is_a_compact_error(store):
    server = build_server(store)
    payload = json.loads(_call(server, "gen3d_generate", {"image_path": "missing.png"}))
    assert payload["error"] == "bad_request"
