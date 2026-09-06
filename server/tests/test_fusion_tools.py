"""A69 P3 - the fu_* tools on the shim, the tables, and the CLI lane."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest
from fixtures_fusion import FakeFusionWire
from test_handoff_import import Scene

from tee.adapters.fusion.adapter import FusionAdapter
from tee.adapters.fusion.tools import register_fusion_tools
from tee.app import TeeApp
from tee.kernel import lanes, trust
from tee.kernel.errors import TeeError

PLATE = [
    {"op": "create", "kind": "sketch", "name": "base", "props": {"rects": [[0, 0, 120, 80]]}},
    {
        "op": "create",
        "kind": "extrude",
        "name": "plate",
        "props": {"sketch": "sk1", "distance": 10},
    },
]


@pytest.fixture
def served(tmp_path):
    wire = FakeFusionWire()
    adapter = FusionAdapter(wire, workdir=str(tmp_path / "work"))
    app = TeeApp({"fusion": adapter, "scene": Scene()}, project_root=tmp_path)
    register_fusion_tools(app, adapter)
    try:
        yield app, adapter
    finally:
        app.shutdown()


def test_every_tool_is_tabled_individually_and_lands_in_the_fusion_lane(served):
    app, _ = served
    for name in ("fu_probe", "fu_export", "fu_measure", "fu_params", "fu_timeline"):
        assert trust.capability_for(name), name
        assert lanes.lane_for(name) == "fusion"
        assert app.registry.describe(name)["lane"] == "fusion"
    assert "fu_execute_python" not in app.registry.names(), "off unless code exec is allowed"
    assert trust.capability_for("fu_execute_python") == "exec-code"
    assert trust.capability_for("fu_export") == "write-artifacts"


def test_probe_reports_fusion_and_the_design_without_starting_anything(served):
    app, _ = served
    out = app.registry.call("fu_probe", {})
    assert out["connected"] is True and out["lane"] == "fusion"
    assert out["design"] == "parametric" and out["document"] == "Untitled"
    assert out["bodies"] == 0 and "mm on the wire" in out["units"]
    app.run_batch("fusion", PLATE)
    out = app.registry.call("fu_probe", {})
    assert out["bodies"] == 1 and out["timeline"] == 2 and out["ids"] == 3


def test_probe_without_a_design_is_an_answer_not_a_refusal(tmp_path):
    adapter = FusionAdapter(FakeFusionWire(design=False))
    app = TeeApp({"fusion": adapter}, project_root=tmp_path)
    register_fusion_tools(app, adapter)
    try:
        out = app.registry.call("fu_probe", {})
        assert out["connected"] is True and out["design"] is None
        assert "New Design" in out["note"]
    finally:
        app.shutdown()


def test_probe_names_the_install_when_the_bridge_is_down(tmp_path):
    class _Down(FakeFusionWire):
        def execute(self, code, **kw):
            raise TeeError("fusion_unreachable", "down", fix="x")

    adapter = FusionAdapter(_Down())
    app = TeeApp({"fusion": adapter}, project_root=tmp_path)
    register_fusion_tools(app, adapter)
    try:
        with pytest.raises(TeeError) as err:
            app.registry.call("fu_probe", {})
        assert err.value.code == "fusion_unreachable" and "Scripts and Add-Ins" in err.value.fix
    finally:
        app.shutdown()


def test_measure_reads_mm_back_from_fusions_cm(served):
    app, _ = served
    app.run_batch("fusion", PLATE)
    out = app.registry.call("fu_measure", {"of": "b1"})
    assert out["volume_mm3"] == pytest.approx(96_000.0)
    assert out["bbox_mm"] == pytest.approx([120.0, 80.0, 10.0])
    assert out["mass_kg"] == pytest.approx(96.0 * 0.00785, rel=1e-6)
    assert out["centre_of_mass_mm"] == pytest.approx([60.0, 40.0, 5.0])
    whole = app.registry.call("fu_measure", {})
    assert whole["of"] == "root" and whole["volume_mm3"] == pytest.approx(96_000.0)


def test_params_and_timeline_are_compact_tables(served):
    app, _ = served
    app.run_batch("fusion", PLATE)
    app.run_batch(
        "fusion", [{"op": "create", "kind": "param", "name": "w", "props": {"value": "120 mm"}}]
    )
    rows = app.registry.call("fu_params", {})["rows"]
    assert {r["name"]: r["user"] for r in rows} == {"w": True, "d1": False}
    assert next(r for r in rows if r["name"] == "d1")["value"] == 10.0
    history = app.registry.call("fu_timeline", {})
    assert [r["type"] for r in history["rows"]] == ["Sketch", "ExtrudeFeature"]
    assert history["marker"] == 2 and history["count"] == 2


def test_export_writes_the_format_declares_units_and_can_land(served, tmp_path):
    app, adapter = served
    app.run_batch("fusion", PLATE)
    out = app.registry.call("fu_export", {"format": "step", "out": str(tmp_path / "plate")})
    assert out["path"].endswith("plate.step") and out["bytes"] > 0
    assert out["units"] == "mm" and out["declares_units"] is True
    assert "createSTEPExportOptions('" in adapter.wire.executed[-1]
    obj = app.registry.call(
        "fu_export",
        {"format": "obj", "out": str(tmp_path / "plate.obj"), "of": "b1", "into": "scene"},
    )
    assert obj["units"] == "cm" and "centimetres" in obj["note"]
    assert obj["landed"]["lane"] == "scene" and obj["landed"]["scale"] == 0.01
    assert "createOBJExportOptions(_geom" in adapter.wire.executed[-1]
    with pytest.raises(TeeError) as err:
        app.registry.call("fu_export", {"format": "iges", "out": "x"})
    assert err.value.code == "bad_op" and "doc 71" in err.value.fix
    stl = app.registry.call("fu_export", {"format": "stl", "out": str(tmp_path / "plate.stl")})
    assert stl["units"] is None and "default units" in stl["note"]
    with pytest.raises(TeeError) as err:
        app.registry.call(
            "fu_export", {"format": "stl", "out": str(tmp_path / "p2.stl"), "into": "scene"}
        )
    assert err.value.code in ("handoff_import_unsupported", "handoff_units_unknown")


def test_the_escape_hatch_registers_only_with_code_exec_and_the_kernel_decides(tmp_path):
    wire = FakeFusionWire()
    adapter = FusionAdapter(wire)
    app = TeeApp({"fusion": adapter}, project_root=tmp_path, allow_code_exec=True)
    register_fusion_tools(app, adapter)
    try:
        assert "fu_execute_python" in app.registry.names()
        with pytest.raises(TeeError) as err:
            app.registry.call("fu_execute_python", {"code": "result = {'n': 1}"})
        assert err.value.code == "trust_denied", "exec-code is high-risk: denied unless granted"
        app.registry.grants = dataclasses.replace(
            app.registry.grants, granted=frozenset({"exec-code"})
        )
        out = app.registry.call("fu_execute_python", {"code": "result = {'n': 1 + 1}"})
        assert out == {"ok": True, "result": {"n": 2}}
    finally:
        app.shutdown()


def test_the_cli_serves_fusion_as_a_lane(tmp_path, monkeypatch):
    from tee import cli

    assert "fusion" in cli.ADAPTER_NAMES
    lane = cli._fusion_lane(9899)
    assert lane.name == "fusion" and lane.adapter.wire.port == 9899
    app = cli.build_app([lane], str(tmp_path), allow_code_exec=False)
    try:
        assert "fu_export" in app.registry.names()
        assert app.vocab("fusion").purpose.startswith("Autodesk Fusion")
    finally:
        app.shutdown()
    # the config's [fusion] port is honoured the way [blender] port is
    (tmp_path / ".tee").mkdir(exist_ok=True)
    (tmp_path / ".tee" / "config.toml").write_text("[fusion]\nport = 9900\n")
    from tee.config import ProjectConfig

    assert ProjectConfig.load(tmp_path).fusion_port == 9900
    (tmp_path / ".tee" / "config.toml").write_text("[fusion]\nport = 70000\n")
    config = ProjectConfig.load(tmp_path)
    assert config.fusion_port is None and "[fusion].port" in (config.warning or "")


def test_the_add_in_ships_beside_its_manifest():
    root = Path(__file__).resolve().parents[2] / "adapters" / "fusion" / "tee_bridge" / "TEE"
    assert (root / "TEE.py").is_file() and (root / "TEE.manifest").is_file()
    import json

    manifest = json.loads((root / "TEE.manifest").read_text())
    assert manifest["autodeskProduct"] == "Fusion" and manifest["type"] == "addin"
    assert manifest["supportedOS"] == "windows|mac"
