"""Phase 2 acceptance scenario, run against live Blender on the physical
machine. These cover the acceptance bullets that the per-feature live tests
do not: the 100-object summary budget through the real MCP surface, recovery
from Blender *exiting* mid-session (not just a stale cache), and a real bake
driven through the async job lane."""

from __future__ import annotations

import json
import subprocess
import time

import anyio
import pytest
from conftest import _tee_boot, find_blender, free_port
from mcp.client import Client
from mcp.types import TextContent

from tee.adapters.blender.adapter import BlenderAdapter
from tee.adapters.blender.tools import register_blender_tools
from tee.adapters.blender.wire import BlenderWire
from tee.app import TeeApp
from tee.kernel.budget import estimate_tokens
from tee.server import build_server

pytestmark = pytest.mark.dcc


@pytest.fixture()
def adapter(blender_bridge, tmp_path):
    return BlenderAdapter(BlenderWire(port=blender_bridge), workdir=str(tmp_path))


@pytest.fixture()
def app(adapter, tmp_path):
    application = TeeApp({"blender": adapter}, project_root=tmp_path, allow_code_exec=True)
    register_blender_tools(application, adapter, docs_cache_dir=tmp_path / "docs-cache")
    adapter.execute_python(
        "import bpy\n"
        "for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)\n"
        "result = {'cleared': True}"
    )
    application.cache("blender").resync(adapter)
    yield application
    application.shutdown()


def test_scene_summary_under_500_tokens_on_100_objects(app, adapter):
    """Acceptance: 'scene summary < 500 tokens on a 100-object scene', measured
    on the bytes an MCP client actually receives, not on an internal dict."""
    app.run_batch(
        "blender",
        [
            {
                "op": "create",
                "kind": "cube",
                "name": f"Obj{i:03d}",
                "props": {"location": [i % 10, i // 10, 0]},
            }
            for i in range(100)
        ],
    )
    server = build_server(app)
    seen = {}

    async def main():
        async with Client(server) as client:
            result = await client.call_tool("tee_scene_summary", {"adapter": "blender"})
            block = result.content[0]
            assert isinstance(block, TextContent)
            seen["text"] = block.text

    anyio.run(main)

    payload = json.loads(seen["text"])
    assert payload["ok"] is True
    assert payload["total"] == 100, payload
    tokens = estimate_tokens(seen["text"])
    assert tokens < 500, f"summary was {tokens} tokens:\n{seen['text'][:400]}"

    # and the response was size-logged (acceptance: 'all response sizes logged')
    report = app.response_log.report()
    assert "tee_scene_summary" in report
    assert report["tee_scene_summary"]["calls"] >= 1
    assert report["tee_scene_summary"]["median_tokens"] < 500


def test_reconnect_and_resync_after_blender_exits(tmp_path):
    """Acceptance: 'kill and restart Blender mid-session -> reconnect and
    resync'. Uses a private Blender process so killing it cannot disturb the
    session-scoped bridge the rest of the suite shares."""
    blender = find_blender()
    if blender is None:
        pytest.skip("no Blender binary (set TEE_BLENDER)")
    port = free_port()
    boot = tmp_path / "boot.py"
    boot.write_text(_tee_boot(port))

    def launch():
        proc = subprocess.Popen(
            [blender, "--background", "--factory-startup", "--python", str(boot)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        probe = BlenderWire(port=port)
        deadline = time.time() + 60
        while time.time() < deadline:
            if probe.probe():
                return proc
            if proc.poll() is not None:
                pytest.fail(f"Blender exited early rc={proc.returncode}")
            time.sleep(0.25)
        proc.kill()
        pytest.fail("Blender never came up")

    proc = launch()
    adapter = BlenderAdapter(BlenderWire(port=port), workdir=str(tmp_path))
    app = TeeApp({"blender": adapter}, project_root=tmp_path, allow_code_exec=True)
    try:
        app.run_batch("blender", [{"op": "create", "kind": "cube", "name": "Survivor"}])
        assert any(e.name == "Survivor" for e in app.cache("blender").entities.values())

        # Blender goes away mid-session.
        proc.kill()
        proc.wait(timeout=15)
        deadline = time.time() + 10
        while adapter.probe() and time.time() < deadline:
            time.sleep(0.2)
        assert adapter.probe() is False, "adapter still reports a live bridge"

        # A call against the dead bridge fails loud and cheap, never hangs.
        started = time.time()
        with pytest.raises(Exception) as err:
            app.run_batch("blender", [{"op": "create", "kind": "cube", "name": "Doomed"}])
        assert time.time() - started < 30
        assert getattr(err.value, "code", "") in {
            "adapter_unavailable",
            "bridge_unreachable",
            "bridge_closed",
        }, err.value

        # Restart on the same port: the adapter reconnects with no new object,
        # and a resync rebuilds the cache from the *fresh* scene.
        proc = launch()
        assert adapter.probe() is True
        app.cache("blender").resync(adapter)
        names = {e.name for e in app.cache("blender").entities.values()}
        assert "Survivor" not in names, "stale pre-restart entity survived the resync"
        assert "Doomed" not in names
        app.run_batch("blender", [{"op": "create", "kind": "cube", "name": "AfterRestart"}])
        names = {e.name for e in app.cache("blender").entities.values()}
        assert "AfterRestart" in names
    finally:
        app.shutdown()
        proc.kill()
        proc.wait(timeout=15)


def test_bake_runs_as_an_async_job(app):
    """Acceptance: 'bake runs as an async job'. A real rigid-body bake is
    submitted to the job lane; the caller gets a job id back immediately and
    polls it to completion instead of blocking on the bridge."""
    from tee.physical import physics as physics_mod

    app.run_batch(
        "blender",
        [
            {"op": "create", "kind": "cube", "name": "Faller", "props": {"location": [0, 0, 4]}},
            {"op": "create", "kind": "plane", "name": "Ground", "props": {"location": [0, 0, 0]}},
        ],
    )
    # Give the bake something real to chew on: without a rigid-body world,
    # ptcache.bake_all returns instantly and the test proves nothing.
    adapter = app.adapters["blender"]
    adapter.execute_python(
        "import bpy\n"
        "scene = bpy.context.scene\n"
        "scene.frame_end = 40\n"
        "if scene.rigidbody_world is None:\n"
        "    bpy.ops.rigidbody.world_add()\n"
        "coll = bpy.data.collections.new('RB')\n"
        "scene.rigidbody_world.collection = coll\n"
        "for name, kind in (('Faller', 'ACTIVE'), ('Ground', 'PASSIVE')):\n"
        "    obj = bpy.data.objects[name]\n"
        "    coll.objects.link(obj)\n"
        "    with bpy.context.temp_override(object=obj):\n"
        "        bpy.ops.rigidbody.object_add(type=kind)\n"
        "result = {'z0': bpy.data.objects['Faller'].location.z}\n"
    )

    job_id = app.jobs.submit(
        "bake_all",
        lambda: physics_mod.run_program(app, "blender", physics_mod.BAKE_ALL_PROGRAM, timeout=300),
    )
    assert isinstance(job_id, str) and job_id

    deadline = time.time() + 300
    status = app.jobs.status(job_id)
    while status["state"] in {"queued", "running"} and time.time() < deadline:
        time.sleep(0.25)
        status = app.jobs.status(job_id)
    assert status["state"] == "done", status
    assert status["result"]["baked"] is True, status

    # the bake really simulated: stepping to the last frame shows the cube fell
    landed = adapter.execute_python(
        "import bpy\n"
        "bpy.context.scene.frame_set(bpy.context.scene.frame_end)\n"
        "result = {'z': bpy.data.objects['Faller'].matrix_world.translation.z}\n"
    )["result"]
    assert landed["z"] < 3.0, f"cube never fell - bake was a no-op: {landed}"
