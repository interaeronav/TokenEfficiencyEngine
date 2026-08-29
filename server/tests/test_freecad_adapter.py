"""FreeCAD adapter (A37 P4): the kit contract on the hermetic shim, the
fabrication ops (solved sketch -> pad -> pocket), checkpoints, and the
one-script-per-batch wire discipline. Live parity runs under -m dcc."""

from __future__ import annotations

import pytest
from fixtures_freecad import FakeFcWire

from tee.adapters.freecad.adapter import FreeCADAdapter
from tee.kernel.contract import AdapterContract
from tee.kernel.errors import TeeError


def make() -> FreeCADAdapter:
    return FreeCADAdapter(FakeFcWire())


class TestFreeCADAdapterContract(AdapterContract):
    def make_adapter(self):
        return make()


def test_batch_compiles_to_one_bridge_round_trip() -> None:
    adapter = make()
    adapter.execute(
        [
            {"op": "create", "kind": "box", "name": "b1", "props": {"Length": 40}},
            {"op": "create", "kind": "box", "name": "b2", "props": {"Length": 20}},
            {"op": "set", "id": "b1", "props": {"Width": 30, "at": [5, 0, 0]}},
        ]
    )
    wire: FakeFcWire = adapter.wire  # type: ignore[assignment]
    batch_scripts = [c for c in wire.executed if "created, modified, deleted" in c]
    assert len(batch_scripts) == 1  # three ops, ONE execute_code
    box = next(e for e in adapter.list_entities() if e.id == "b1")
    assert box.kind == "Part::Box"
    assert box.summary["length"] == 40.0 and box.summary["at"] == [5.0, 0.0, 0.0]


def test_failed_op_reports_rule6_and_stops() -> None:
    adapter = make()
    adapter.execute([{"op": "create", "kind": "box", "name": "keep"}])
    with pytest.raises(TeeError) as excinfo:
        adapter.execute(
            [
                {"op": "set", "id": "keep", "props": {"Length": 9}},
                {"op": "set", "id": "ghost", "props": {"Length": 1}},
                {"op": "create", "kind": "box", "name": "never"},
            ]
        )
    assert excinfo.value.code == "freecad_op_failed"
    assert "1" in excinfo.value.message  # the failing op's index named
    assert all(e.id != "never" for e in adapter.list_entities())  # stopped there


def test_solved_sketch_pad_pocket_flow() -> None:
    pytest.importorskip("py_slvs")
    adapter = make()
    # a 100x60 mm rectangle: distances + axis alignment, solved BEFORE FreeCAD
    sketch_props = {
        "points": [
            {"id": "a", "at": [0, 0], "fixed": True},
            {"id": "b", "at": [90, 4]},
            {"id": "c", "at": [95, 55]},
            {"id": "d", "at": [-3, 61]},
        ],
        "lines": [
            {"id": "ab", "from": "a", "to": "b"},
            {"id": "bc", "from": "b", "to": "c"},
            {"id": "cd", "from": "c", "to": "d"},
            {"id": "da", "from": "d", "to": "a"},
        ],
        "constraints": [
            {"kind": "distance", "a": "a", "b": "b", "value": 100},
            {"kind": "distance", "a": "b", "b": "c", "value": 60},
            {"kind": "horizontal", "line": "ab"},
            {"kind": "vertical", "line": "bc"},
            {"kind": "horizontal", "line": "cd"},
            {"kind": "vertical", "line": "da"},
        ],
    }
    diff = adapter.execute(
        [
            {"op": "create", "kind": "sketch", "name": "profile", "props": sketch_props},
            {
                "op": "create",
                "kind": "pad",
                "name": "slab",
                "props": {"sketch": "profile", "length": 18},
            },
        ]
    )
    assert diff.created == ["profile", "slab"]
    wire: FakeFcWire = adapter.wire  # type: ignore[assignment]
    script = next(c for c in wire.executed if "LineSegment" in c)
    # solved coordinates reached the script: the sloppy guesses (90, 4) are
    # gone, the exact 100 x 60 rectangle is placed
    assert "Vector(100.0, 0.0, 0)" in script
    assert "Vector(100.0, 60.0, 0)" in script
    slab = next(e for e in adapter.list_entities() if e.id == "slab")
    assert slab.kind == "Part::Extrusion" and slab.summary["lengthfwd"] == 18.0

    diff = adapter.execute(
        [
            {"op": "create", "kind": "sketch", "name": "hole", "props": sketch_props},
            {
                "op": "create",
                "kind": "pocket",
                "name": "slot",
                "props": {"sketch": "hole", "target": "slab", "depth": 5},
            },
        ]
    )
    assert "slot" in diff.created
    slot = next(e for e in adapter.list_entities() if e.id == "slot")
    assert slot.kind == "Part::Cut"


def test_snapshot_restore_via_savecopy_roundtrip() -> None:
    adapter = make()
    adapter.execute([{"op": "create", "kind": "box", "name": "kept"}])
    payload = adapter.snapshot("before-extras")
    adapter.execute([{"op": "create", "kind": "box", "name": "extra"}])
    adapter.restore(payload)
    names = sorted(e.name for e in adapter.list_entities())
    assert names == ["kept"]


def test_fc_drawing_reads_dimension_values_back(tmp_path) -> None:
    """Pins the live 1.1.3 lesson: dims cache 0.0 until the read-back
    dispatch touches + recomputes them - the shim answers 0.0 unless
    fc_drawing does exactly that."""
    from tee.adapters.freecad.tools import register_freecad_tools
    from tee.app import TeeApp

    adapter = make()
    app = TeeApp({"freecad": adapter}, project_root=tmp_path)
    try:
        register_freecad_tools(app, adapter)
        app.run_batch(
            "freecad", [{"op": "create", "kind": "box", "name": "b", "props": {"Length": 111}}]
        )
        sheet = app.registry.call(
            "fc_drawing",
            {
                "objects": ["b"],
                "views": ["top"],
                "dimensions": [{"view": 0, "type": "ExtentX"}],
                "formats": ["svg", "pdf", "dxf"],
                "name": "S",
                "out_dir": str(tmp_path),
            },
        )
        assert sheet["dimensions"][0]["value_mm"] == 111.0  # touched + recomputed
        for fmt in ("svg", "pdf", "dxf"):
            assert (tmp_path / f"S.{fmt}").stat().st_size > 500
    finally:
        app.shutdown()


def test_generic_kind_carries_dynamic_props() -> None:
    adapter = make()
    diff = adapter.execute(
        [
            {
                "op": "create",
                "kind": "jig",
                "name": "note1",
                "props": {"grid_mm": 32, "supplier": "Blum"},
            }
        ]
    )
    eid = diff.created[0]
    row = next(e for e in adapter.list_entities() if e.id == eid)
    assert row.kind == "App::FeaturePython"
