"""A69 P3 - the fu_* tools on the shim, the tables, and the CLI lane."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest
from fixtures_fusion import FakeFusionWire
from test_handoff_import import Scene

from tee.adapters.fusion import codegen
from tee.adapters.fusion.adapter import FusionAdapter
from tee.adapters.fusion.tools import register_fusion_tools
from tee.app import TeeApp
from tee.kernel import lanes, trust, trustctx
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
    for name in ("fu_probe", "fu_export", "fu_drawing", "fu_measure", "fu_params", "fu_timeline"):
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
        app.registry.call("fu_export", {"format": "dwg", "out": str(tmp_path / "x")})
    assert err.value.code == "bad_op" and "Formats:" in err.value.fix
    stl = app.registry.call("fu_export", {"format": "stl", "out": str(tmp_path / "plate.stl")})
    # A71: STL carries no unit; `units` is the design's default length unit read
    # from the design at export time (row 53), a measurement rather than a guess
    assert stl["units"] == "mm" and stl["declares_units"] is False
    assert "design's default length unit" in stl["note"]
    lane = app.adapters["scene"]
    imports = tuple(lane.vocab().imports) if hasattr(lane, "vocab") else ()
    if "stl" in imports:
        landed = app.registry.call(
            "fu_export", {"format": "stl", "out": str(tmp_path / "p2.stl"), "into": "scene"}
        )
        assert landed["landed"]["scale"] == 0.001, "millimetres land at 0.001"
    else:
        with pytest.raises(TeeError) as err:
            app.registry.call(
                "fu_export", {"format": "stl", "out": str(tmp_path / "p2.stl"), "into": "scene"}
            )
        assert err.value.code == "handoff_import_unsupported"
    # A71 (rows 17, 48): STEP and the archive take a component or the whole design,
    # never a body - refused before the wire with Fusion's own words
    for fmt in ("step", "f3d"):
        with pytest.raises(TeeError) as err:
            app.registry.call(
                "fu_export", {"format": fmt, "out": str(tmp_path / f"body.{fmt}"), "of": "b1"}
            )
        assert err.value.code == "bad_op" and "invlid argument geometry" in err.value.message
        assert not (tmp_path / f"body.{fmt}").exists(), "refused before the wire"


def test_the_four_more_exports_use_their_verified_constructors(served, tmp_path):
    """A70 P4 (doc 71 row 48): iges/sat/usd filename-first and component-only,
    3mf geometry-first. A71 read what Fusion 2704.1.53 writes: IGES declares MM,
    SAT one millimetre per unit, 3MF unit="millimeter" - so those three declare
    mm now; USD is a USDZ package (Fusion appends .usdz) whose binary usdc
    carries metersPerUnit, a value the lane cannot read, so it stays null."""
    app, adapter = served
    app.run_batch("fusion", PLATE)
    for fmt, header, units in (
        ("iges", "S      1", "mm"),
        ("sat", "700 0 1 0", "mm"),
        ("usd", "#usda 1.0", None),
    ):
        out = app.registry.call("fu_export", {"format": fmt, "out": str(tmp_path / f"p.{fmt}")})
        assert out["units"] == units and out["declares_units"] is True
        assert "measured" in out["note"] or "USDZ" in out["note"]
        assert header in Path(out["path"]).read_text()
        script = adapter.wire.executed[-1]
        assert f"{codegen.EXPORT_FORMATS[fmt][0]}('" in script, "filename first"
    assert out["path"].endswith("p.usd.usdz"), "the file Fusion actually writes"
    three = app.registry.call(
        "fu_export", {"format": "3mf", "out": str(tmp_path / "p.3mf"), "of": "b1"}
    )
    assert three["declares_units"] is True and three["units"] == "mm"
    assert "createC3MFExportOptions(_geom" in adapter.wire.executed[-1], "geometry first"
    with pytest.raises(TeeError) as err:
        app.registry.call("fu_export", {"format": "iges", "out": str(tmp_path / "x"), "of": "b1"})
    assert err.value.code == "bad_op" and "never a body" in err.value.message
    assert not (tmp_path / "x.iges").exists(), "refused before the wire"
    with pytest.raises(TeeError) as err:
        app.registry.call(
            "fu_export", {"format": "usd", "out": str(tmp_path / "p2.usd"), "into": "scene"}
        )
    assert err.value.code == "handoff_import_unsupported"


def test_fu_drawing_is_the_partkiln_route_and_refuses_without_partkiln(tmp_path):
    """A70 P4 (doc 71 section 10.7): the Fusion API cannot create a drawing,
    so the sheet is partkiln's - STEP out, pk_import, pk_drawing - and the
    import is decided as the scene write it is."""
    from fixtures_partkiln import FakeKernel

    from tee.adapters.partkiln.adapter import PartkilnAdapter

    adapter = FusionAdapter(FakeFusionWire(), workdir=str(tmp_path / "work"))
    kernel = FakeKernel()
    kiln = PartkilnAdapter(tmp_path / "pk", kernel=kernel)
    app = TeeApp({"fusion": adapter, "partkiln": kiln}, project_root=tmp_path)
    register_fusion_tools(app, adapter)
    try:
        assert trust.capability_for("fu_drawing") == "write-artifacts"
        assert lanes.lane_for("fu_drawing") == "fusion"
        app.run_batch("fusion", PLATE)
        out = app.registry.call(
            "fu_drawing",
            {
                "out": str(tmp_path / "sheets"),
                "name": "plate",
                "views": [{"name": "top", "dir": "top"}],
            },
        )
        assert out["step"].endswith("plate.step") and Path(out["step"]).is_file()
        assert out["part"] == "part:plate" and out["drawing"]["id"] == "dwg:plate"
        assert out["drawing"]["views"] == ["top"] and out["drawing"]["files"]
        assert "cannot create a drawing" in out["note"]
        seen = {c[0]: c[1] for c in kernel.calls if c[0] in ("import", "drawing")}
        assert seen["import"]["path"] == out["step"] and seen["import"]["name"] == "plate"
        assert seen["drawing"]["of"] == "part:plate" and seen["drawing"]["views"] == [
            {"name": "top", "dir": "top"}
        ]
        # a task carrying untrusted content may not write partkiln's document
        # through a write-artifacts tool: refused before the STEP is written
        before = trustctx.snapshot()
        try:
            app.registry.grants = dataclasses.replace(
                app.registry.grants, enforce_quality_band=True
            )
            trustctx.install("job", ("fetch-web:evil.example/page",))
            with pytest.raises(TeeError) as err:
                app.registry.call("fu_drawing", {"out": str(tmp_path / "sheets2"), "name": "p2"})
            assert err.value.code == "trust_denied" and "fu_drawing" in err.value.message
            assert not (tmp_path / "work" / "drawings" / "p2.step").exists()
        finally:
            trustctx.install(*before)
            trustctx.clear_for_tests()
    finally:
        app.shutdown()
    alone = FusionAdapter(FakeFusionWire())
    app = TeeApp({"fusion": alone}, project_root=tmp_path / "alone")
    register_fusion_tools(app, alone)
    try:
        with pytest.raises(TeeError) as err:
            app.registry.call("fu_drawing", {"out": "sheets"})
        assert err.value.code == "partkiln_not_served" and "--adapter partkiln" in err.value.fix
    finally:
        app.shutdown()


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
