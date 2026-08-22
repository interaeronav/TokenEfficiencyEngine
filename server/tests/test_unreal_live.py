"""Live tests against a running UE 5.8 editor with Epic's MCP server started.

Skipped cleanly when no editor is listening. Bring one up with:

    UnrealEditor <project>.uproject -ModelContextProtocolStartServer

Run with: uv run pytest -m dcc
"""

from __future__ import annotations

import json

import pytest

from tee.adapters.unreal.catalog import ToolsetCatalog
from tee.adapters.unreal.summarize import _REF_DESC
from tee.adapters.unreal.wire import UnrealWire
from tee.kernel.budget import estimate_tokens

pytestmark = pytest.mark.dcc

# Acceptance bounds (script Phase 3, as amended by DECISIONS A25).
MAX_SUMMARY_TOKENS = 2_500
MAX_SUMMARY_RATIO = 0.20


@pytest.fixture(scope="session")
def unreal_wire():
    wire = UnrealWire()
    if not wire.probe():
        pytest.skip(f"no Unreal MCP server at {wire.url}")
    return wire


@pytest.fixture()
def catalog(unreal_wire):
    return ToolsetCatalog(unreal_wire)


def test_handshake_and_meta_tools(unreal_wire):
    info = unreal_wire.connect()
    assert info["protocolVersion"] == "2025-06-18"
    assert unreal_wire.session_id
    names = {t["name"] for t in unreal_wire.list_tools()}
    # Tool-search mode: the 830-tool catalog is dispatched server-side.
    assert names == {"list_toolsets", "describe_toolset", "call_tool"}


def test_server_is_not_identified_by_name(unreal_wire):
    """5.8.1 returns an EMPTY serverInfo.name, though research 07 says it is
    always 'unreal-mcp'. Nothing may key off it."""
    info = unreal_wire.connect()
    assert "serverInfo" in info
    assert not info["serverInfo"].get("name")


def test_toolsets_resolve_by_suffix_on_the_real_catalog(catalog):
    qualified = catalog.resolve("BlueprintTools")
    assert qualified.endswith(".BlueprintTools")
    assert qualified != "BlueprintTools"  # a real module path was found


def test_describe_toolset_is_never_forwarded_raw(catalog):
    """Phase 3 acceptance (A25): raw payload never reaches the model, the
    largest toolset summarizes under 2,500 tokens, every summary under 20%."""
    worst_ratio = 0.0
    report = {}
    for name in ("BlueprintTools", "ActorTools", "SceneTools", "AssetTools"):
        raw = json.dumps(catalog.parsed(name), separators=(",", ":"))
        summary = catalog.summary(name)
        text = json.dumps(summary, separators=(",", ":"))

        # nothing from the raw schema dump survives into the model's view
        assert _REF_DESC not in text
        assert "refPath" not in text
        assert "inputSchema" not in text

        tokens = estimate_tokens(text)
        ratio = len(text) / len(raw)
        worst_ratio = max(worst_ratio, ratio)
        report[name] = (estimate_tokens(raw), tokens, ratio)
        assert tokens < MAX_SUMMARY_TOKENS, f"{name}: {tokens} tokens\n{report}"
        assert summary["total"] == len(catalog.parsed(name)["tools"])
    assert worst_ratio < MAX_SUMMARY_RATIO, report


def test_full_schema_expansion_is_one_tool_not_the_toolset(catalog):
    one = catalog.describe_tool("ActorTools", "get_actor_bounds")
    assert one["tool"] == "get_actor_bounds"
    assert "input_schema" in one
    whole = json.dumps(catalog.parsed("ActorTools"))
    assert len(json.dumps(one)) < len(whole) / 5


def test_toolset_summary_is_cached_across_calls(catalog):
    catalog.summary("ActorTools")
    catalog.summary("ActorTools")
    catalog.describe_tool("ActorTools", "get_actor_bounds")
    assert catalog.fetches == 1
