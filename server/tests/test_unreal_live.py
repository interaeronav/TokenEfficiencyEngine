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


# -- adapter (mutating; each test restores what it changed) ------------------


@pytest.fixture()
def adapter(unreal_wire):
    from tee.adapters.unreal.adapter import UnrealAdapter

    ad = UnrealAdapter(wire=unreal_wire)
    snapshot = ad.snapshot("test-guard")
    yield ad
    ad.restore(snapshot)


def test_batch_spawns_and_configures_in_one_round_trip(adapter):
    """Phase 3 acceptance: 'spawn + configure actors via one macro call'."""
    diff = adapter.execute(
        [
            {
                "op": "create",
                "name": "TeeA",
                "props": {"asset_path": "/Engine/BasicShapes/Cube", "location": [0, 500, 100]},
            },
            {
                "op": "create",
                "name": "TeeB",
                "props": {
                    "asset_path": "/Engine/BasicShapes/Sphere",
                    "location": [300, 500, 100],
                    "scale": [2, 2, 2],
                },
            },
        ]
    )
    assert len(diff.created) == 2
    assert diff.deleted == []
    # the response is a diff, not a scene dump (P2)
    payload = json.dumps({"created": diff.created, "details": diff.details})
    assert estimate_tokens(payload) < 250, payload

    # refPaths stay server-side; the model addresses actors by short id
    assert all(eid.startswith("u") for eid in diff.created)


def test_set_by_short_id_never_needs_a_refpath(adapter):
    diff = adapter.execute(
        [
            {
                "op": "create",
                "name": "TeeMove",
                "props": {"asset_path": "/Engine/BasicShapes/Cube", "location": [0, 700, 100]},
            }
        ]
    )
    eid = diff.created[0]
    moved = adapter.execute([{"op": "set", "id": eid, "props": {"location": [0, 900, 250]}}])
    assert moved.modified == [eid]
    assert moved.details[eid]["location"] == [0, 900, 250]


def test_snapshot_restore_removes_actors_added_since(adapter):
    before = len(adapter.list_entities())
    snap = adapter.snapshot("rollback")
    adapter.execute(
        [
            {
                "op": "create",
                "name": "TeeDoomed",
                "props": {"asset_path": "/Engine/BasicShapes/Cone", "location": [900, 500, 100]},
            }
        ]
    )
    assert len(adapter.list_entities()) == before + 1
    adapter.restore(snap)
    assert len(adapter.list_entities()) == before


def test_unknown_entity_id_fails_with_a_fix(adapter):
    from tee.kernel.errors import TeeError

    with pytest.raises(TeeError) as err:
        adapter.execute([{"op": "set", "id": "u9999", "props": {"location": [0, 0, 0]}}])
    assert err.value.code == "unknown_entity"
    assert "tee_scene_summary" in (err.value.fix or "")


# -- blueprint authoring -----------------------------------------------------


def test_blueprint_function_authored_and_compiled_via_dsl(adapter):
    """Phase 3 acceptance: 'Blueprint function authored and compiled with
    diagnostics via graph DSL'."""
    out = adapter.blueprint_function(
        folder="/Game/TeeProbe",
        asset_name="BP_TeeLiveGood",
        function_name="AddTwo",
        dsl="(fn AddTwo (A B)\n  (return (Utilities|Operators|Add :A A :B B)))",
        params=[
            {"name": "A", "type": "int", "input": True},
            {"name": "B", "type": "int", "input": True},
            {"name": "Sum", "type": "int", "input": False},
        ],
    )
    assert out["compile"] == "clean"
    assert out["verified"] is True
    assert out["forms_written"] == out["forms_requested"]


def test_hallucinated_node_type_is_caught_not_reported_as_success(adapter):
    """Epic's own signals all say success here: write_graph_dsl returns fine
    and compile_blueprint(warnings_as_errors=True) reports the Blueprint
    clean, while the function body is silently empty."""
    from tee.kernel.errors import TeeError

    with pytest.raises(TeeError) as err:
        adapter.blueprint_function(
            folder="/Game/TeeProbe",
            asset_name="BP_TeeLiveBad",
            function_name="Broken",
            dsl="(fn Broken ()\n  (return (NoSuch|Node|Here :A 1)))",
        )
    assert err.value.code == "ue_graph_incomplete"
    assert "NoSuch|Node|Here" in err.value.message
    assert "find_node_types" in (err.value.fix or "")


def test_bad_dsl_syntax_fails_before_reaching_the_editor(adapter):
    from tee.kernel.errors import TeeError

    with pytest.raises(TeeError) as err:
        adapter.blueprint_function(
            folder="/Game/TeeProbe",
            asset_name="BP_TeeNeverMade",
            function_name="Nope",
            dsl="(fn Nope (",
        )
    assert err.value.code == "ue_dsl_syntax"


def test_toolset_listing_has_no_phantom_entries(catalog):
    names = catalog.load_toolsets()
    assert all(" " not in n for n in names), [n for n in names if " " in n]
    # every advertised name must actually resolve and describe
    assert catalog.resolve(sorted(names)[0])


# -- editor state, text-first checks, budgeted vision ------------------------


def test_editor_state_probe(unreal_wire):
    from tee.adapters.unreal.adapter import UnrealAdapter

    state = UnrealAdapter(wire=unreal_wire).busy_state()
    assert state["reachable"] is True
    assert state["pie_running"] in (True, False)


def test_scene_checks_are_text_and_bounded(adapter):
    checks = adapter.scene_checks()
    assert checks["actors_total"] >= checks["actors_in_view"]
    assert len(checks["offscreen"]) <= 25
    assert estimate_tokens(json.dumps(checks)) < 600


def test_capture_is_budgeted_and_uses_the_real_camera(adapter):
    """captureTransform is documented optional but required in practice, and a
    zero-filled default silently photographs the world origin."""
    camera = json.loads(
        adapter.catalog.call("EditorAppToolset", "GetCameraTransform", {}, timeout=60)
    )["returnValue"]["location"]
    data, meta = adapter.capture_with_metadata(16 * 1024)
    assert len(data) <= 16 * 1024
    assert data[:2] == b"\xff\xd8"
    assert meta["cameraLocation"]["x"] == pytest.approx(camera["x"], abs=1.0)


def test_optional_object_params_are_defaulted_from_their_schema(adapter):
    adapter.capture_with_metadata(16 * 1024)
    defaulted = adapter.catalog.defaulted_params.get("EditorAppToolset.CaptureViewport")
    assert defaulted == ["annotations"], defaulted
