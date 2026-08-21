"""Live end-to-end tests against real headless Blender through the official
bridge protocol. Run with: uv run pytest -m dcc"""

from __future__ import annotations

import pytest

from tee.adapters.blender.adapter import BlenderAdapter
from tee.adapters.blender.tools import register_blender_tools
from tee.adapters.blender.wire import BlenderWire
from tee.app import TeeApp
from tee.kernel.errors import TeeError

pytestmark = pytest.mark.dcc


@pytest.fixture()
def adapter(blender_bridge, tmp_path):
    return BlenderAdapter(BlenderWire(port=blender_bridge), workdir=str(tmp_path))


@pytest.fixture()
def app(adapter, tmp_path):
    application = TeeApp({"blender": adapter}, project_root=tmp_path)
    register_blender_tools(application, adapter)
    # factory scene contains Cube/Camera/Light; start every test from empty
    adapter.execute_python(
        "import bpy\n"
        "for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)\n"
        "result = {'cleared': True}"
    )
    application.cache("blender").resync(adapter)
    yield application
    application.shutdown()


def test_info_and_probe(adapter):
    info = adapter.info()
    assert info.connected is True
    assert info.version.startswith("5.")
    assert info.extra["background"] is True
    assert adapter.probe() is True


def test_batch_create_set_delete_roundtrip(app):
    out = app.run_batch(
        "blender",
        [
            {"op": "create", "kind": "cube", "name": "Base", "props": {"size": 2}},
            {
                "op": "create",
                "kind": "uv_sphere",
                "name": "Ball",
                "props": {"radius": 0.5, "location": [0, 0, 2]},
            },
            {"op": "create", "kind": "light", "name": "Sun", "props": {"light_type": "SUN"}},
        ],
    )
    assert out["ok"] is True
    assert len(out["created"]) == 3
    ball_id = out["created"][1]
    assert out["details"][ball_id]["location"] == [0, 0, 2]
    assert out["details"][ball_id]["kind"] == "mesh"
    assert all(eid.startswith("b") for eid in out["created"])

    moved = app.run_batch(
        "blender", [{"op": "set", "id": ball_id, "props": {"location": [1, 1, 3]}}]
    )
    assert moved["modified"] == [ball_id]
    assert moved["details"][ball_id]["location"] == [1, 1, 3]

    gone = app.run_batch("blender", [{"op": "delete", "id": ball_id}])
    assert gone["deleted"] == [ball_id]

    summary = app.cache("blender").summary()
    assert summary["total"] == 2
    names = {e["name"] for e in summary["entities"]}
    assert names == {"Base", "Sun"}


def test_diff_tracking_across_batches(app):
    stamp = app.cache("blender").stamp()
    out1 = app.run_batch("blender", [{"op": "create", "kind": "cube", "name": "A"}])
    cube_id = out1["created"][0]
    app.run_batch("blender", [{"op": "set", "id": cube_id, "props": {"scale": [2, 2, 2]}}])
    delta = app.cache("blender").diff_since(stamp["epoch"], stamp["revision"])
    assert delta["created"] == [cube_id]
    assert "modified" not in delta or delta["modified"] == []  # folded into create


def test_snapshot_restore_via_checkpoints(app):
    app.run_batch("blender", [{"op": "create", "kind": "cube", "name": "Keep"}])
    checkpoint = app.checkpoints.create(
        app.adapters["blender"], "before-mess", app.cache("blender").revision
    )
    app.run_batch(
        "blender",
        [
            {"op": "create", "kind": "torus", "name": "Mess1"},
            {"op": "create", "kind": "cone", "name": "Mess2"},
        ],
    )
    assert app.cache("blender").summary()["total"] == 3

    rolled = app.rollback("blender", checkpoint.id)
    assert rolled["ok"] is True
    summary = app.cache("blender").summary()
    assert summary["total"] == 1
    assert summary["entities"][0]["name"] == "Keep"


def test_assign_material_via_virtual_tool(app):
    out = app.run_batch("blender", [{"op": "create", "kind": "monkey", "name": "Suzanne"}])
    suzanne = out["created"][0]
    result = app.registry.call(
        "bl_assign_material",
        {"entity_id": suzanne, "base_color": [0.8, 0.1, 0.1], "roughness": 0.3},
    )
    assert result["ok"] is True
    assert result["details"][suzanne]["materials"] == ["Suzanne_mat"]


def test_execute_python_firewall_blocks_stale_api(app):
    with pytest.raises(TeeError) as err:
        app.registry.call(
            "bl_execute_python",
            {"code": "import bpy\nbpy.data.objects[0].data.use_auto_smooth = True"},
        )
    assert err.value.code == "stale_api"
    assert "Smooth by Angle" in err.value.fix


def test_execute_python_error_is_compact(app):
    with pytest.raises(TeeError) as err:
        app.registry.call("bl_execute_python", {"code": "raise ValueError('kaboom')"})
    assert err.value.code == "blender_exec_error"
    assert "ValueError: kaboom" in err.value.message
    assert "Traceback" not in err.value.message
    assert len(err.value.message) < 450


def test_scene_stats_detects_overlap(app):
    app.run_batch(
        "blender",
        [
            {"op": "create", "kind": "cube", "name": "C1", "props": {"size": 2}},
            {
                "op": "create",
                "kind": "cube",
                "name": "C2",
                "props": {"size": 2, "location": [0.5, 0, 0]},
            },
            {
                "op": "create",
                "kind": "cube",
                "name": "Far",
                "props": {"size": 1, "location": [10, 10, 10]},
            },
        ],
    )
    stats = app.registry.call("bl_scene_stats", {})
    assert stats["meshes"] == 3
    assert stats["total_polys"] == 18  # three cubes
    assert len(stats["overlapping_pairs"]) == 1


def test_capture_respects_byte_budget(app, adapter):
    app.run_batch("blender", [{"op": "create", "kind": "cube", "name": "Subject"}])
    data = adapter.capture("viewport", max_bytes=16 * 1024)
    assert data[:2] == b"\xff\xd8"  # JPEG magic
    assert len(data) <= 16 * 1024


def test_user_edit_outside_batches_detected_on_resync(app):
    # simulate a concurrent human edit: mutate through raw python (no batch)
    adapter = app.adapters["blender"]
    app.run_batch("blender", [{"op": "create", "kind": "cube", "name": "Tracked"}])
    adapter.wire.execute(
        "import bpy\nbpy.data.objects['Tracked'].location.x = 5\nresult={'ok':True}"
    )
    # cache is stale; a refresh resyncs and the new position is visible
    app.cache("blender").resync(adapter)
    ent = next(iter(app.cache("blender").entities.values()))
    assert ent.summary["location"][0] == 5
