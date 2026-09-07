"""A68 P1e: a headless lane never touches a DCC, and no kernel lane assumes
Blender by position or by name.

Nine sites used to default to Blender: `next(iter(app.adapters), "fake")`
(assets, physical, pins, capture), `sorted(adapters)[0]` (senses) and the
literal "blender" (assets/importer, uefn, senses, extract/handoff). Each now
resolves by capability or by content, and refuses by name when the lane it
needs is not served. The first test greps for the old habits so they cannot
come back."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from test_lane_routing import Lane

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter, LaneVocab
from tee.kernel.errors import TeeError

SRC = Path(__file__).resolve().parents[1] / "src" / "tee"


def test_no_kernel_lane_defaults_to_the_first_or_a_named_adapter():
    """The three habits, by pattern, over every module under src/tee."""
    habits = (
        re.compile(r"next\(iter\(app\.adapters"),
        re.compile(r"sorted\(adapters\)\[0\]"),
        re.compile(r"""\.get\("adapter"\)\s+or\s+"blender\""""),
    )
    offenders = []
    for path in SRC.rglob("*.py"):
        text = path.read_text()
        for habit in habits:
            if habit.search(text):
                offenders.append((str(path.relative_to(SRC)), habit.pattern))
    assert offenders == []


MODELING = ("wall_with_openings", "slab", "roof", "stairs")


class Blenderish(FakeAdapter):
    """A fake with Blender's shape: it executes Python, aims a camera, and
    takes the tier-2 modeling ops (as creates, for the test's purposes)."""

    def execute_python(self, code, timeout=None):
        return {"result": {}}

    def capture_look(self, *args, **kwargs):
        return b""

    def execute(self, batch):
        rewritten = [
            {**op, "op": "create", "kind": op["op"]} if op.get("op") in MODELING else op
            for op in batch
        ]
        return super().execute(rewritten)

    def vocab(self):
        return LaneVocab(
            ops=("create", "set", "delete", "import_file", *MODELING),
            kinds=("cube", "light"),
            imports=("glb", "gltf", "obj", "fbx"),
            purpose="a scene",
        )


class Text(FakeAdapter):
    """A headless lane: no pixels, ever."""

    def vocab(self):
        return LaneVocab(ops=("create", "set", "delete"), renders=False, purpose="text")


def _desk(tmp_path, **extra):
    lanes = {
        "scene": Blenderish(),
        "partkiln": Lane("partkiln", kinds=("part",), kind_optional=False),
    }
    lanes.update(extra)
    return TeeApp(lanes, project_root=tmp_path)


def test_blender_lane_is_found_by_capability_never_by_position(tmp_path):
    app = TeeApp(
        {"partkiln": Lane("partkiln", kinds=("part",), kind_optional=False), "scene": Blenderish()},
        project_root=tmp_path,
    )
    try:
        assert app.blender_lane() == "scene", "second in the list, first by capability"
        assert app.blender_lane("scene") == "scene"
        with pytest.raises(TeeError) as err:
            app.blender_lane("partkiln")
        assert err.value.code == "unsupported_adapter" and "scene" in err.value.fix
    finally:
        app.shutdown()


def test_blender_lane_refuses_by_name_when_none_is_served(tmp_path):
    app = TeeApp({"partkiln": Lane("partkiln")}, project_root=tmp_path)
    try:
        with pytest.raises(TeeError) as err:
            app.blender_lane()
        assert err.value.code == "blender_not_served"
        assert "served: partkiln" in err.value.message
        assert "tee serve --adapter blender" in err.value.fix
    finally:
        app.shutdown()


def test_importer_lane_routes_a_file_by_its_suffix(tmp_path):
    app = _desk(tmp_path)
    try:
        assert app.importer_lane("glb") == "scene"
        assert app.importer_lane(".GLB") == "scene"
        with pytest.raises(TeeError) as err:
            app.importer_lane("step")
        assert err.value.code == "handoff_no_importer" and "'.step'" in err.value.message
    finally:
        app.shutdown()
    two = _desk(tmp_path, level=Blenderish())
    try:
        with pytest.raises(TeeError) as err:
            two.importer_lane("glb")
        assert err.value.code == "handoff_importer_ambiguous"
        assert "scene, level" in err.value.message
        assert two.importer_lane("glb", "level") == "level"
    finally:
        two.shutdown()


def test_importer_lane_on_a_single_lane_server_is_that_lane(tmp_path):
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        assert app.importer_lane("step") == "fake", "the sole lane takes it, as before"
    finally:
        app.shutdown()


def test_run_routed_routes_and_declares(tmp_path):
    app = _desk(tmp_path)
    try:
        out = app.run_routed([{"op": "create", "kind": "part", "name": "b"}], None, label="x")
        assert out["adapter"] == "partkiln" and out["routed"] == "by kind; pass adapter= to pin"
        out = app.run_routed([{"op": "create", "kind": "cube"}], "scene", label="x")
        assert out["adapter"] == "scene" and "routed" not in out
    finally:
        app.shutdown()


def test_the_physical_lane_finds_blender_by_capability(tmp_path):
    from tee.physical.tools import register_physical_tools

    app = TeeApp(
        {"partkiln": Lane("partkiln", kinds=("part",), kind_optional=False), "scene": Blenderish()},
        project_root=tmp_path,
    )
    try:
        register_physical_tools(app, tmp_path)
        out = app.registry.call("slab", {"name": "floor", "props": {}})
        assert out["adapter"] == "scene"
        with pytest.raises(TeeError) as err:
            app.registry.call("slab", {"adapter": "partkiln", "props": {}})
        assert err.value.code == "unsupported_adapter"
    finally:
        app.shutdown()


def test_the_extract_ifc_writer_registers_without_blender(tmp_path):
    pytest.importorskip("tee.extract.tools")
    from tee import cli

    app = TeeApp({"partkiln": Lane("partkiln")}, project_root=tmp_path)
    try:
        cli._attach_extract(app, str(tmp_path), with_handoff=False)
        names = app.registry.names()
        assert "ex_export_ifc" in names
        assert "bl_build_from_plan" not in names and "bl_check_against_plan" not in names
    finally:
        app.shutdown()


def test_uefn_export_refuses_by_name_without_a_blender(tmp_path):
    from tee.uefn.tools import register_uefn_tools

    app = TeeApp({"partkiln": Lane("partkiln")}, project_root=tmp_path)
    try:
        register_uefn_tools(app, tmp_path)
        with pytest.raises(TeeError) as err:
            app.registry.call("export_for_uefn", {"ids": ["e1"], "name": "thing"})
        assert err.value.code == "blender_not_served"
    finally:
        app.shutdown()


def test_the_senses_pick_the_one_lane_that_renders_or_ask():
    from tee.senses import _one_viewport

    assert _one_viewport({"partkiln": Text(), "scene": Blenderish()}) == "scene"
    with pytest.raises(TeeError) as err:
        _one_viewport({"scene": Blenderish(), "level": Blenderish()})
    assert err.value.code == "sense_adapter_required" and "scene, level" in err.value.message
