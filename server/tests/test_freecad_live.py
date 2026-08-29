"""Live FreeCAD parity (-m dcc): the kit contract and the fabrication
flow against the real bridge (FreeCAD GUI + MCP addon RPC on :9875).
Skips cleanly when no bridge answers - docs/setup-freecad.md starts one."""

from __future__ import annotations

import pytest

from tee.adapters.freecad.adapter import FreeCADAdapter
from tee.adapters.freecad.wire import FreeCADWire
from tee.kernel.contract import AdapterContract

pytestmark = pytest.mark.dcc


def _live_wire() -> FreeCADWire:
    wire = FreeCADWire()
    if not wire.ping():
        pytest.skip("no FreeCAD RPC bridge on :9875 (docs/setup-freecad.md)")
    return wire


@pytest.fixture()
def adapter():
    wire = _live_wire()
    instance = FreeCADAdapter(wire, doc="TeeLiveTest")
    yield instance
    wire.py("import FreeCAD\ntry: FreeCAD.closeDocument('TeeLiveTest')\nexcept Exception: pass")


class TestFreeCADLiveContract(AdapterContract):
    def make_adapter(self):
        wire = _live_wire()
        wire.py("import FreeCAD\ntry: FreeCAD.closeDocument('TeeLiveTest')\nexcept Exception: pass")
        return FreeCADAdapter(wire, doc="TeeLiveTest")


def test_live_pad_volume_and_dimension_readback(adapter) -> None:
    pytest.importorskip("py_slvs")
    from tee.adapters.freecad.tools import register_freecad_tools
    from tee.app import TeeApp

    app = TeeApp({"freecad": adapter}, project_root=adapter._spill())
    try:
        register_freecad_tools(app, adapter)
        app.run_batch(
            "freecad",
            [
                {
                    "op": "create",
                    "kind": "sketch",
                    "name": "sq",
                    "props": {
                        "points": [
                            {"id": "a", "at": [0, 0], "fixed": True},
                            {"id": "b", "at": [45, 3]},
                            {"id": "c", "at": [52, 49]},
                            {"id": "d", "at": [-2, 51]},
                        ],
                        "lines": [
                            {"id": "ab", "from": "a", "to": "b"},
                            {"id": "bc", "from": "b", "to": "c"},
                            {"id": "cd", "from": "c", "to": "d"},
                            {"id": "da", "from": "d", "to": "a"},
                        ],
                        "constraints": [
                            {"kind": "distance", "a": "a", "b": "b", "value": 50},
                            {"kind": "distance", "a": "b", "b": "c", "value": 50},
                            {"kind": "horizontal", "line": "ab"},
                            {"kind": "vertical", "line": "bc"},
                            {"kind": "horizontal", "line": "cd"},
                            {"kind": "vertical", "line": "da"},
                        ],
                    },
                },
                {
                    "op": "create",
                    "kind": "pad",
                    "name": "cube",
                    "props": {"sketch": "sq", "length": 50},
                },
            ],
        )
        row = next(e for e in adapter.list_entities() if e.id == "cube")
        assert abs(row.summary["volume_mm3"] - 125_000) < 1  # 50^3 exactly
        sheet = app.registry.call(
            "fc_drawing",
            {
                "objects": ["cube"],
                "views": ["top"],
                "dimensions": [{"view": 0, "type": "ExtentX"}],
                "formats": ["dxf"],
                "name": "LiveSheet",
            },
        )
        assert sheet["dimensions"][0]["value_mm"] == 50.0  # from the document
    finally:
        app.shutdown()
