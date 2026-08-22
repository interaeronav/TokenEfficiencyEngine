"""Phase 12 live: the Blender-side export lane (dcc-marked)."""

from __future__ import annotations

import pytest

from tee.adapters.blender.adapter import BlenderAdapter
from tee.adapters.blender.wire import BlenderWire
from tee.app import TeeApp
from tee.uefn.adapter import FakeUefn
from tee.uefn.tools import register_uefn_tools

pytestmark = pytest.mark.dcc


@pytest.fixture()
def app(blender_bridge, tmp_path):
    adapter = BlenderAdapter(BlenderWire(port=blender_bridge), workdir=str(tmp_path))
    application = TeeApp({"blender": adapter}, project_root=tmp_path,
                         allow_code_exec=True)
    register_uefn_tools(application, tmp_path, uefn=FakeUefn())
    adapter.execute_python(
        "import bpy\n"
        "for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)\n"
        "result = {'cleared': True}"
    )
    application.cache("blender").resync(adapter)
    yield application
    application.shutdown()


def test_export_for_uefn_generates_lods_and_fbx(app, tmp_path):
    created = app.run_batch(
        "blender",
        [{"op": "create", "kind": "uv_sphere", "name": "Prop",
          "props": {"radius": 0.4, "segments": 24}}],
    )
    eid = created["created"][0]
    out = app.registry.call(
        "export_for_uefn",
        {"ids": [eid], "name": "prop", "adapter": "blender"},
    )
    assert out["objects"] == 1
    assert out["lods_generated"] == 2  # LOD1 + LOD2 at -50% steps
    from pathlib import Path

    fbx = Path(out["exported"])
    assert fbx.exists() and fbx.stat().st_size > 1000
    # scene is left clean: LOD duplicates removed after export
    app.cache("blender").resync(app.adapters["blender"])
    names = [e.name for e in app.cache("blender").entities.values()]
    assert not any("_LOD" in n for n in names)
