"""Live plan -> Blender handoff & conformance (7.7 acceptance).

The DXF fixture plan builds a multi-room shell in real headless Blender
through the normal batch machinery (both bridge flavors via the parametrized
`blender_bridge` fixture); the conformance check passes clean, and a
deliberately mis-placed wall yields exactly one conflict fact naming the
delta. Run with: uv run pytest -m dcc
"""

from __future__ import annotations

import time

import pytest
from fixtures_extract import HOUSE_D, HOUSE_W, make_dxf

from tee.adapters.blender.adapter import BlenderAdapter
from tee.adapters.blender.tools import register_blender_tools
from tee.adapters.blender.wire import BlenderWire
from tee.app import TeeApp
from tee.extract.handoff import register_handoff_tools
from tee.extract.tools import register_extract_tools

pytestmark = pytest.mark.dcc


@pytest.fixture()
def app(blender_bridge, tmp_path):
    adapter = BlenderAdapter(BlenderWire(port=blender_bridge), workdir=str(tmp_path))
    application = TeeApp({"blender": adapter}, project_root=tmp_path, allow_code_exec=True)
    register_blender_tools(application, adapter, docs_cache_dir=tmp_path / "docs-cache")
    store, registry = register_extract_tools(application, tmp_path)
    register_handoff_tools(application, store, registry)
    application._store = store
    adapter.execute_python(
        "import bpy\n"
        "for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)\n"
        "result = {'cleared': True}"
    )
    application.cache("blender").resync(adapter)
    yield application
    application.shutdown()


@pytest.fixture()
def plan_source(app, tmp_path):
    """Ingest the fixture DXF and return its source hash prefix."""
    dxf = make_dxf(tmp_path / "plan.dxf")
    out = app.registry.call("ex_ingest", {"path": str(dxf)})
    deadline = time.time() + 120
    while time.time() < deadline:
        status = app.jobs.status(out["job"])
        if status["state"] in ("done", "error"):
            break
        time.sleep(0.2)
    assert status["state"] == "done", status
    source = app._store.resolve("plan.dxf")
    return source["hash"][:8]


def test_build_check_and_deliberate_misbuild(app, plan_source):
    # -- build: 5 walls (4 outer + 1 interior) + 1 slab, one checkpointed batch
    built = app.registry.call("bl_build_from_plan", {"source": plan_source})
    assert built["built_walls"] == 5
    assert built["built_objects"] == 6
    assert built["checkpoint"]

    # the multi-room shell is really in the scene: 6 meshes, and the two
    # long outer walls carry the fixture's 8 m / 6 m dimensions
    cache = app.cache("blender")
    assert cache.summary()["total"] == 6
    lengths = sorted(
        round(e.summary["dimensions"][0], 1)
        for e in cache.entities.values()
        if e.name.startswith("Wall_")
    )
    assert lengths.count(HOUSE_W + 0.0) == 2  # two 8 m walls
    assert lengths.count(HOUSE_D + 0.0) >= 2  # 6 m walls incl. the interior

    # -- conformance on the honest build: clean report, no conflict facts
    report = app.registry.call("bl_check_against_plan", {"source": plan_source})
    assert report["conformant"] is True
    assert report["walls_checked"] == 5
    assert report["conflicts"] == []
    assert app._store.facts(app._store.resolve(plan_source)["hash"], kind="conflict") == []

    # -- deliberately mis-place one wall beyond tolerance (~0.017 m)
    manifest = app._store.facts(app._store.resolve(plan_source)["hash"], kind="build_manifest")[-1]
    wall_id, entity_id = next(iter(manifest["walls"].items()))
    location = list(cache.get(entity_id).summary["location"])
    location[0] += 0.1
    app.run_batch("blender", [{"op": "set", "id": entity_id, "props": {"location": location}}])

    report = app.registry.call("bl_check_against_plan", {"source": plan_source})
    assert report["conformant"] is False
    assert len(report["conflicts"]) == 1
    conflict = report["conflicts"][0]
    assert conflict["fact_a"] == f"plan:{wall_id}:position"
    assert conflict["fact_b"] == f"scene:{entity_id}"
    assert conflict["delta_m"] == pytest.approx(0.1, abs=0.005)
    assert conflict["winner"] == "plan"

    # the conflict IS the report: it landed in the fact store, queryable
    stored = app._store.facts(app._store.resolve(plan_source)["hash"], kind="conflict")
    assert len(stored) == 1
    assert stored[0]["delta_m"] == pytest.approx(0.1, abs=0.005)


def test_ifc_export_from_live_plan(app, plan_source):
    out = app.registry.call("ex_export_ifc", {"source": plan_source})
    assert out["walls"] == 5
    assert out["storeys"] >= 1

    import ifcopenshell

    model = ifcopenshell.open(out["path"])
    assert len(model.by_type("IfcWall")) == 5
