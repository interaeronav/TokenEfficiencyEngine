"""Home Builder lane (A37 P5.1), hermetic: codegen correctness (mm->m,
module paths, read-back shapes), refusal shapes, csv file-out, and the
hb_missing mapping. The real HB drive is the live closet run (-m dcc
territory; recorded in PROGRESS)."""

from __future__ import annotations

import pytest

from tee.adapters.blender.homebuilder import HB_MODULE, register_hb_tools
from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError


class CannedWire:
    """Answers queued bridge responses; records every script."""

    def __init__(self, *responses: dict):
        self.queue = list(responses)
        self.executed: list[str] = []

    def execute(self, code: str, *, timeout=None) -> dict:
        self.executed.append(code)
        if "_tee_52_compat" in code:  # the 5.2 shim: always fine, not queued
            return {"status": "ok", "result": {"ok": True}}
        if not self.queue:
            return {"status": "ok", "result": {"ok": True}}
        return self.queue.pop(0)


class HostAdapter:
    def __init__(self, wire: CannedWire):
        self.wire = wire


def app_with(wire: CannedWire, tmp_path):
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    register_hb_tools(app, HostAdapter(wire))
    return app


OK_PROBE = {"status": "ok", "result": {"ok": True}}


def test_room_codegen_converts_mm_and_chains_walls(tmp_path) -> None:
    wire = CannedWire(OK_PROBE, {"status": "ok", "result": {"walls": ["Wall", "Wall.001"]}})
    app = app_with(wire, tmp_path)
    try:
        out = app.registry.call(
            "hb_room",
            {"walls": [{"length_mm": 3000}, {"length_mm": 2000, "angle_deg": -90}]},
        )
        assert out["walls"] == ["Wall", "Wall.001"]
        script = wire.executed[-1]
        assert "'length_m': 3.0" in script and "'length_m': 2.0" in script
        assert "'angle_deg': -90.0" in script
        assert f'"{HB_MODULE}.hb_types"' in script
        assert "connect_to_wall(prev)" in script
    finally:
        app.shutdown()


def test_cabinet_codegen_and_type_validation(tmp_path) -> None:
    wire = CannedWire(OK_PROBE, {"status": "ok", "result": {"cabinet": "W", "parts": 9}})
    app = app_with(wire, tmp_path)
    try:
        out = app.registry.call(
            "hb_cabinet",
            {
                "type": "tall",
                "width_mm": 1200,
                "height_mm": 2200,
                "depth_mm": 600,
                "wall": "Wall",
                "offset_mm": 150,
                "name": "Wardrobe",
            },
        )
        assert out["cabinet"] == "W" and out["parts"] == 9
        script = wire.executed[-1]
        assert "cab.width = 1.2" in script and "cab.height = 2.2" in script
        assert "cab.depth = 0.6" in script and "(0.15, 0.0, 0.0)" in script
        with pytest.raises(TeeError) as excinfo:
            app.registry.call("hb_cabinet", {"type": "corner"})
        assert "tall, base, upper" in excinfo.value.fix
    finally:
        app.shutdown()


def test_cutlist_shapes_rows_and_writes_csv(tmp_path) -> None:
    rows = [
        ["Side", "Wardrobe", 2200.0, 600.0, 19.0, 2],
        ["Top", "Wardrobe", 1162.0, 600.0, 19.0, 1],
    ]
    wire = CannedWire(OK_PROBE, {"status": "ok", "result": {"rows": rows, "parts": 3}})
    app = app_with(wire, tmp_path)
    try:
        out = app.registry.call("hb_cutlist", {"csv": str(tmp_path / "cuts.csv")})
        assert out["cols"][0] == "part" and out["parts"] == 3
        assert "no 32 mm system holes" in out["note"]  # honesty rides the response
        text = (tmp_path / "cuts.csv").read_text()
        assert text.splitlines()[0] == "part,product,length_mm,width_mm,thickness_mm,qty"
        assert "Side,Wardrobe,2200.0,600.0,19.0,2" in text
    finally:
        app.shutdown()


def test_missing_extension_maps_to_install_fix(tmp_path) -> None:
    wire = CannedWire({"status": "ok", "result": {"ok": False, "why": "No module"}})
    app = app_with(wire, tmp_path)
    try:
        with pytest.raises(TeeError) as excinfo:
            app.registry.call("hb_room", {"walls": [{"length_mm": 1000}]})
        assert excinfo.value.code == "hb_missing"
        assert "extensions.blender.org" in excinfo.value.fix
    finally:
        app.shutdown()


def test_bridge_error_maps_rule6_with_last_line(tmp_path) -> None:
    wire = CannedWire(
        OK_PROBE,
        {"status": "error", "message": "Traceback ...\nRuntimeError: no wall 'W9'"},
    )
    app = app_with(wire, tmp_path)
    try:
        with pytest.raises(TeeError) as excinfo:
            app.registry.call("hb_cabinet", {"type": "tall", "wall": "W9"})
        assert excinfo.value.code == "hb_failed"
        assert "no wall 'W9'" in excinfo.value.message
    finally:
        app.shutdown()


def test_layout_validates_views_and_passes_out_dir(tmp_path) -> None:
    wire = CannedWire(
        OK_PROBE,
        {"status": "ok", "result": {"scenes": ["Plan"], "files": [str(tmp_path / "plan.png")]}},
    )
    app = app_with(wire, tmp_path)
    try:
        out = app.registry.call(
            "hb_layout", {"views": ["plan"], "out_dir": str(tmp_path), "resolution": 800}
        )
        assert out["scenes"] == ["Plan"]
        assert "resolution = 800" in wire.executed[-1]
        with pytest.raises(TeeError) as excinfo:
            app.registry.call("hb_layout", {"views": ["sections"]})
        assert "plan, elevations" in excinfo.value.fix
    finally:
        app.shutdown()
