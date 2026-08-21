"""Release-gating lint over the MCP tool surface (decision A6).

Client failure modes this protects against are silent (whole-catalog drops,
content drops), so the assertions run against the real tools/list output as
an MCP client sees it.
"""

import json

import anyio
import pytest
from mcp.client import Client

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.budget import estimate_tokens
from tee.server import build_server

MAX_TOOLS = 15
MAX_DESCRIPTION_BYTES = 2_048
MAX_TOTAL_DEFINITION_TOKENS = 8_000


@pytest.fixture(scope="module")
def tools():
    app = TeeApp({"fake": FakeAdapter()}, project_root=".")
    server = build_server(app)

    async def fetch():
        async with Client(server) as client:
            listed = await client.list_tools()
            return listed.tools

    try:
        return anyio.run(fetch)
    finally:
        app.shutdown()


def test_surface_is_small(tools):
    assert 1 <= len(tools) <= MAX_TOOLS


def test_every_input_schema_is_a_plain_object(tools):
    for tool in tools:
        schema = tool.input_schema
        assert isinstance(schema, dict), tool.name
        assert schema.get("type") == "object", tool.name
        for key in ("anyOf", "oneOf", "allOf"):
            assert key not in schema, f"{tool.name}: root-level {key} breaks clients"
        for prop_name, prop in (schema.get("properties") or {}).items():
            assert isinstance(prop, dict), f"{tool.name}.{prop_name}: boolean schemas break clients"


def test_no_output_schema_emitted(tools):
    for tool in tools:
        assert tool.output_schema in (None, {}), (
            f"{tool.name}: outputSchema triggers silent tool drops in Claude "
            "Desktop and historic drop-all in Claude Code (A6)"
        )


def test_descriptions_are_present_and_bounded(tools):
    for tool in tools:
        assert tool.description and tool.description.strip(), tool.name
        assert len(tool.description.encode()) <= MAX_DESCRIPTION_BYTES, tool.name


def test_total_definition_budget(tools):
    total = estimate_tokens(json.dumps([t.model_dump(mode="json") for t in tools], default=str))
    assert total <= MAX_TOTAL_DEFINITION_TOKENS, (
        f"always-loaded tool definitions cost ~{total} tokens; "
        f"budget is {MAX_TOTAL_DEFINITION_TOKENS}"
    )


def test_tool_names_are_prefixed_and_stable(tools):
    for tool in tools:
        assert tool.name.startswith("tee_"), tool.name


EXPECTED_TOOL_COUNT = 14


def test_tool_count_matches_expectation(tools):
    # silent whole-catalog drops are the failure mode this canary catches;
    # update the constant deliberately when adding/removing a tool
    assert len(tools) == EXPECTED_TOOL_COUNT
