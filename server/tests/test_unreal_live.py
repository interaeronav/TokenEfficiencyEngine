"""Live tests against a running UE 5.8 editor with Epic's MCP server started.

Skipped cleanly when no editor is listening. Bring one up with:

    UnrealEditor <project>.uproject -ModelContextProtocolStartServer

Run with: uv run pytest -m dcc
"""

from __future__ import annotations

import json

import pytest
from conftest import find_blender

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


# -- TEE content plugin (skipped when it is not installed) -------------------


@pytest.fixture()
def tee_plugin(adapter):
    if not adapter.has_tee_toolset():
        pytest.skip(
            "TEE's Unreal content plugin is not enabled in this project "
            "(copy adapters/unreal/TeeToolset into <project>/Plugins/)"
        )
    return adapter


def test_unsandboxed_editor_python_reaches_the_unreal_module(tee_plugin):
    """Epic's script lane cannot import `unreal` at all - it is sandboxed to
    tool orchestration plus {json, math, datetime, copy, re, time}. This is
    the gap TEE's content plugin fills."""
    out = tee_plugin.editor_python(
        "import unreal\n"
        "sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)\n"
        "result = {'engine': unreal.SystemLibrary.get_engine_version(),\n"
        "          'actors': len(sub.get_all_level_actors())}",
        "TEE: test probe",
    )
    assert out["engine"].startswith("5.")
    assert isinstance(out["actors"], int)


def test_editor_python_failure_returns_the_traceback_not_a_dead_script(tee_plugin):
    from tee.kernel.errors import TeeError

    with pytest.raises(TeeError) as err:
        tee_plugin.editor_python("raise RuntimeError('boom')", "TEE: failing")
    assert err.value.code == "ue_editor_python_failed"
    assert "RuntimeError: boom" in err.value.message


def test_non_dict_result_is_rejected(tee_plugin):
    from tee.kernel.errors import TeeError

    with pytest.raises(TeeError) as err:
        tee_plugin.editor_python("result = 42", "TEE: bad result")
    assert "must be a dict" in err.value.message


def test_settle_drops_actors_and_adopts_the_result(tee_plugin):
    """Epic ships no simulation toolset and 'Keep Simulation Changes' has no
    API; this macro replaces both."""
    setup = """
import unreal
aes = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in aes.get_all_level_actors():
    if a.get_actor_label().startswith("PytestBox"):
        aes.destroy_actor(a)
mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
made = []
for i in range(2):
    # 200 cm apart: a cube is 100 cm, so they cannot interpenetrate
    actor = aes.spawn_actor_from_object(mesh, unreal.Vector(-600, 1400 + i * 200, 300))
    actor.set_actor_label("PytestBox%d" % i)
    c = actor.static_mesh_component
    c.set_mobility(unreal.ComponentMobility.MOVABLE)
    c.set_simulate_physics(True)
    c.set_collision_profile_name("PhysicsActor")
    made.append(actor.get_actor_label())
# The ground under the drop is whatever this project has there - an empty
# level's floor sits at 0, a landscape does not. Measure it instead of
# assuming (OkongoSim's terrain here is ~16 cm below zero).
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
hit = unreal.SystemLibrary.line_trace_single(
    world, unreal.Vector(-600, 1500, 1000), unreal.Vector(-600, 1500, -1000),
    unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
# HitResult exposes nothing as attributes on 5.8.1 - to_dict() or bust.
result = {"made": made, "ground_z": hit.to_dict()["location"].z if hit else 0.0}
"""
    ready = tee_plugin.editor_python(setup, "TEE: test settle setup")
    labels = ready["made"]
    ground = ready["ground_z"]
    report = tee_plugin.settle(labels, adopt=True)
    assert report["settled"] is True
    assert report["actors"] == 2
    assert sorted(report["adopted"]) == sorted(labels)
    # dropped from 300 cm onto a floor; a 100 cm cube rests near 50 cm
    assert all(v > 200 for v in report["moved_cm"].values()), report

    final = tee_plugin.editor_python(
        "import unreal\n"
        "aes = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)\n"
        "result = {a.get_actor_label(): a.get_actor_location().z\n"
        "          for a in aes.get_all_level_actors()\n"
        "          if a.get_actor_label().startswith('PytestBox')}",
        "TEE: verify settle",
    )
    # a 100 cm cube rests with its centre ~50 cm above whatever it landed on
    for z in final.values():
        assert ground + 40 < z < ground + 60, (final, ground)

    # already at rest: returns at the minimum, not the cap
    again = tee_plugin.settle(labels)
    assert again["settled"] is True
    assert again["sim_seconds"] < 3.0, again


def test_settle_rejects_an_unknown_actor_label(tee_plugin):
    from tee.kernel.errors import TeeError

    with pytest.raises(TeeError) as err:
        tee_plugin.settle(["NoSuchActorAnywhere"])
    assert err.value.code == "unknown_actor"


def test_asset_file_imports_and_measures_in_metres(tee_plugin, tmp_path):
    """Epic's AssetTools can find/load/save/delete assets but cannot IMPORT
    one, so this runs through TEE's content plugin. UE is centimetres; every
    TEE surface is metres, so the readback must come back converted."""
    import subprocess

    blender = find_blender()
    if blender is None:
        pytest.skip("no Blender binary to author a source mesh")
    glb = tmp_path / "unit_cube.glb"
    script = tmp_path / "export.py"
    script.write_text(
        "import bpy, sys\n"
        "for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)\n"
        "bpy.ops.mesh.primitive_cube_add(size=2.0)\n"
        "bpy.ops.export_scene.gltf(filepath=sys.argv[-1], export_format='GLB')\n"
    )
    subprocess.run(
        [blender, "--background", "--factory-startup", "--python", str(script), "--", str(glb)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    assert glb.exists()

    out = tee_plugin.import_asset_file(
        str(glb),
        destination="/Game/TeeTestImport",
        label="PytestImported",
        location=[-1200, 1400, 200],
    )
    assert out["meshes"], out
    assert out["entity_id"].startswith("u")
    # the Blender cube is 2 m; UE reports centimetres and TEE converts
    assert out["dims_m"] == pytest.approx([2.0, 2.0, 2.0], abs=0.01), out


def test_import_of_a_missing_file_fails_before_the_editor(tee_plugin):
    from tee.kernel.errors import TeeError

    with pytest.raises(TeeError) as err:
        tee_plugin.import_asset_file("/nope/not/here.glb")
    assert err.value.code == "asset_file_missing"


def test_pins_round_trip_through_the_real_editor(tee_plugin, tmp_path):
    """The whole pin lane against a live level: tags written, tags read back,
    snapshotted to a file, destroyed, and restored from that file. Uses its
    own namespace so it cannot collide with a project's real pins, and no
    asset lane (that needs the network)."""
    from tee.app import TeeApp
    from tee.pins.tools import register_pin_tools

    app = TeeApp({"unreal": tee_plugin}, project_root=tmp_path)
    app.config.pins = {"namespace": "tee_pin_livetest"}
    register_pin_tools(app, tmp_path)

    def call(_tool, **kwargs):
        return app.registry.call(_tool, {"adapter": "unreal", **kwargs})

    made = call(
        "pin_set",
        id="live-1",
        name="Live test pin",
        category="chair",
        notes="written by pytest",
        wishlist=["stool", "bench"],
        location=[-6.0, 22.0, 1.5],
        yaw=45,
    )
    assert made["created"] is True
    # pin_set verifies the marker's BASE landed on the spot and fails if not
    assert made["position_m"] == [-6.0, 22.0, 1.5]

    shown = call("pin_show", id="live-1")["pin"]
    assert shown["name"] == "Live test pin"
    assert shown["wishlist"] == ["stool", "bench"]
    assert shown["notes"] == "written by pytest"
    assert shown["yaw"] == 45.0
    assert shown["fill_present"] is False

    exported = call("pin_export")
    assert exported["pins"] == 1
    document = json.loads((tmp_path / "pins.json").read_text())
    assert document["namespace"] == "tee_pin_livetest"

    assert call("pin_remove", id="live-1")["removed"] is True
    assert call("pin_list")["count"] == 0

    restored = call("pin_import")
    assert restored["restored"] == ["live-1"]
    again = call("pin_show", id="live-1")["pin"]
    assert again["position_m"] == [-6.0, 22.0, 1.5]
    assert again["notes"] == "written by pytest"

    call("pin_remove", id="live-1")


def test_a_pin_marker_never_ships_and_never_blocks_the_player(tee_plugin, tmp_path):
    """A marker is an authoring aid: editor-only, and no collision - set at
    spawn, because a component whose collision changes later can miss the
    physics rebuild."""
    from tee.app import TeeApp
    from tee.pins.tools import register_pin_tools

    app = TeeApp({"unreal": tee_plugin}, project_root=tmp_path)
    app.config.pins = {"namespace": "tee_pin_livetest"}
    register_pin_tools(app, tmp_path)
    app.registry.call(
        "pin_set", {"adapter": "unreal", "id": "live-2", "location": [-9.0, 22.0, 0.0]}
    )
    probe = tee_plugin.editor_python(
        "import unreal\n"
        "aes = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)\n"
        "out = {}\n"
        "for a in aes.get_all_level_actors():\n"
        "    if a.get_actor_label() == 'Pin_live-2':\n"
        "        c = a.get_component_by_class(unreal.StaticMeshComponent)\n"
        "        out = {'editor_only': bool(a.get_editor_property('is_editor_only_actor')),\n"
        "               'collision': str(c.get_collision_enabled()),\n"
        "               'folder': str(a.get_folder_path())}\n"
        "result = out",
        "TEE: pin marker probe",
    )
    assert probe["editor_only"] is True
    assert "NO_COLLISION" in probe["collision"]
    assert probe["folder"] == "TEE/Pins"
    app.registry.call("pin_remove", {"adapter": "unreal", "id": "live-2"})
