"""A69 P2 - the Fusion adapter on the hermetic shim.

The kit contract, then the behaviours that are easy to get wrong later: the
unit boundary (mm on the wire, cm inside), the retired call never emitted,
the id map, checkpoints that are the timeline plus parameters and say what
they restore, the direct-design refusal, the generic kind, imports, and the
capture budget with Fusion's jpg-or-png fact left open.
"""

from __future__ import annotations

import math

import pytest
from fixtures_fusion import FakeFusionWire

from tee.adapters.fusion import codegen
from tee.adapters.fusion.adapter import FusionAdapter
from tee.kernel.contract import AdapterContract
from tee.kernel.errors import TeeError

RECT = {"op": "create", "kind": "sketch", "name": "base", "props": {"rects": [[0, 0, 120, 80]]}}


def _adapter(**kw) -> FusionAdapter:
    return FusionAdapter(FakeFusionWire(**kw))


def _plate(adapter: FusionAdapter, distance: float = 10):
    diff = adapter.execute(
        [
            RECT,
            {
                "op": "create",
                "kind": "extrude",
                "name": "plate",
                "props": {"sketch": "sk1", "distance": distance},
            },
        ]
    )
    return diff


class TestFusionAdapterContract(AdapterContract):
    def make_adapter(self):
        return _adapter()


# -- units and the retired call ---------------------------------------------------


def test_a_rectangle_extruded_reads_back_in_millimetres(tmp_path):
    adapter = _adapter()
    diff = _plate(adapter, 10)
    assert diff.created == ["sk1", "f1", "b1"]
    body = diff.details["b1"]
    assert body["volume_mm3"] == pytest.approx(96_000.0)
    assert body["bbox_mm"] == pytest.approx([120.0, 80.0, 10.0])
    assert diff.details["f1"]["distance_mm"] == pytest.approx(10.0)
    assert diff.details["sk1"].items() >= {"profiles": 1, "curves": 4, "kind": "sketch"}.items()
    script = adapter.wire.executed[-1]
    assert "createByString('10 mm')" in script, "the unit travels in the string"
    assert "Point3D.create(12.0, 8.0, 0.0)" in script, "sketch points are centimetres"
    assert "setDistanceExtent" not in script, "retired September 2022"
    assert "setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create" in script


def test_a_circle_a_cut_and_a_join_do_the_arithmetic(tmp_path):
    adapter = _adapter()
    _plate(adapter, 10)
    hole = adapter.execute(
        [
            {
                "op": "create",
                "kind": "sketch",
                "name": "hole",
                "props": {"circles": [[60, 40, 5]]},
            },
            {
                "op": "create",
                "kind": "extrude",
                "name": "bore",
                "props": {"sketch": "sk2", "distance": -10, "operation": "cut"},
            },
        ]
    )
    assert hole.created == ["sk2", "f2"] and hole.modified == ["b1"]
    assert hole.details["b1"]["volume_mm3"] == pytest.approx(96_000.0 - math.pi * 25 * 10)
    assert "NegativeExtentDirection" in adapter.wire.executed[-1]
    assert "CutFeatureOperation" in adapter.wire.executed[-1]
    boss = adapter.execute(
        [
            {
                "op": "create",
                "kind": "extrude",
                "props": {"sketch": "sk2", "distance": 5, "operation": "join", "profile": 0},
            }
        ]
    )
    assert boss.modified == ["b1"] and boss.details["b1"]["bbox_mm"][2] == pytest.approx(15.0)


def test_a_fillet_modifies_the_body_and_creates_a_feature():
    adapter = _adapter()
    _plate(adapter)
    diff = adapter.execute(
        [{"op": "create", "kind": "fillet", "name": "round", "props": {"body": "b1", "radius": 2}}]
    )
    assert diff.created == ["f2"] and diff.modified == ["b1"]
    assert diff.details["f2"]["type"] == "FilletFeature" and diff.details["f2"]["bodies"] == 1
    script = adapter.wire.executed[-1]
    assert (
        "addConstantRadiusEdgeSet(_edges, adsk.core.ValueInput.createByString('2 mm'), True)"
        in script
    )


# -- parameters ---------------------------------------------------------------------


def test_parameters_are_created_set_and_drive_the_extrude():
    adapter = _adapter()
    _plate(adapter)
    diff = adapter.execute(
        [{"op": "create", "kind": "param", "name": "thick", "props": {"value": "10 mm"}}]
    )
    assert diff.created == ["param:thick"]
    facts = {"expression": "10 mm", "unit": "mm", "value": 10.0, "name": "thick", "kind": "param"}
    assert diff.details["param:thick"] == facts
    diff = adapter.execute([{"op": "param_set", "name": "thick", "expression": "12 mm"}])
    assert diff.modified == ["param:thick"] and diff.details["param:thick"]["value"] == 12.0
    # an extrude's own distance is a parameter too: set it and the body follows
    diff = adapter.execute([{"op": "set", "id": "f1", "props": {"expression": "20 mm"}}])
    assert diff.modified == ["f1"] and diff.details["f1"]["distance_mm"] == 20.0
    body = next(e for e in adapter.list_entities() if e.id == "b1")
    assert body.summary["volume_mm3"] == pytest.approx(192_000.0)
    with pytest.raises(TeeError) as err:
        adapter.execute([{"op": "param_set", "name": "nope", "expression": "1 mm"}])
    assert err.value.code == "fusion_unknown_entity" and "refresh=true" in err.value.fix


def test_listing_names_every_kind_with_compact_facts_and_stable_ids():
    adapter = _adapter()
    _plate(adapter)
    adapter.execute(
        [
            {"op": "create", "kind": "component", "name": "bracket"},
            {"op": "create", "kind": "param", "name": "w", "props": {"value": 120, "units": "mm"}},
        ]
    )
    first = {e.id: e for e in adapter.list_entities()}
    assert set(first) == {"sk1", "f1", "b1", "c1", "param:w"}
    assert first["c1"].kind == "component" and first["c1"].summary == {"bodies": 0, "sketches": 0}
    assert first["f1"].summary["type"] == "ExtrudeFeature"
    assert {e.concise()["id"] for e in adapter.list_entities()} == set(first)
    assert adapter.wire.namespace["_tee"]["ids"]["b1"].startswith("tok-")
    for row in first.values():
        assert set(row.concise()) <= {"id", "name", "kind", "parent"}


def test_a_generic_kind_lands_as_a_named_component_that_remembers_its_kind():
    adapter = _adapter()
    diff = adapter.execute([{"op": "create", "kind": "jig", "name": "holder"}])
    assert diff.created == ["c1"] and diff.details["c1"]["kind"] == "jig"
    listed = next(e for e in adapter.list_entities() if e.id == "c1")
    assert listed.kind == "jig" and listed.name == "holder"
    adapter.execute([{"op": "set", "id": "c1", "props": {"name": "holder2"}}])
    assert next(e for e in adapter.list_entities() if e.id == "c1").name == "holder2"


def test_delete_removes_and_forgets_the_id():
    adapter = _adapter()
    _plate(adapter)
    diff = adapter.execute([{"op": "delete", "id": "b1"}])
    assert diff.deleted == ["b1"]
    assert "b1" not in {e.id for e in adapter.list_entities()}
    assert "b1" not in adapter.wire.namespace["_tee"]["ids"]
    with pytest.raises(TeeError) as err:
        adapter.execute([{"op": "set", "id": "b1", "props": {"name": "x"}}])
    assert err.value.code == "fusion_unknown_entity"


# -- refusals before the wire, and Fusion's own -------------------------------------------


@pytest.mark.parametrize(
    ("op", "code", "needle"),
    [
        ({"op": "frobnicate"}, "bad_op", "Fusion accepts"),
        ({"op": "create"}, "bad_kind", "Kinds:"),
        (
            {"op": "create", "kind": "sketch", "props": {"plane": "QQ", "rects": [[0, 0, 1, 1]]}},
            "bad_op",
            "XY, XZ or YZ",
        ),
        ({"op": "create", "kind": "sketch"}, "bad_op", "needs geometry"),
        ({"op": "create", "kind": "sketch", "props": {"circles": [[0, 0, -1]]}}, "bad_op", "r > 0"),
        (
            {"op": "create", "kind": "extrude", "props": {"sketch": "sk1"}},
            "bad_op",
            "distance (mm)",
        ),
        (
            {
                "op": "create",
                "kind": "extrude",
                "props": {"sketch": "sk1", "distance": 1, "operation": "melt"},
            },
            "bad_op",
            "Use:",
        ),
        ({"op": "create", "kind": "fillet", "props": {"body": "b1"}}, "bad_op", "radius"),
        ({"op": "create", "kind": "param", "name": "p", "props": {}}, "bad_op", "expression"),
        ({"op": "set", "id": "b1", "props": {"colour": "red"}}, "bad_op", "not settable"),
        ({"op": "delete"}, "bad_op", "needs id"),
        ({"op": "param_set", "name": "w"}, "bad_op", "needs name and expression"),
        ({"op": "import_file", "path": "/tmp/x.obj"}, "bad_op", "does not import '.obj'"),
        (
            {"op": "import_file", "path": "/tmp/x.step", "props": {"scale": [0.1, 0.1, 0.1]}},
            "bad_op",
            "scale is not applied",
        ),
    ],
)
def test_a_malformed_op_is_refused_before_the_wire(op, code, needle):
    adapter = _adapter()
    with pytest.raises(TeeError) as err:
        adapter.execute([op])
    assert err.value.code == code and needle in (err.value.message + err.value.fix)
    assert adapter.wire.executed == [], "no wire trip for a malformed op"


def test_fusions_own_failure_names_the_op_and_rolls_nothing_after_it():
    adapter = _adapter()
    with pytest.raises(TeeError) as err:
        adapter.execute(
            [
                RECT,
                {"op": "create", "kind": "extrude", "props": {"sketch": "sk9", "distance": 1}},
            ]
        )
    assert err.value.code == "fusion_unknown_entity" and "Batch op 1 failed" in err.value.message
    assert "sk9" in err.value.message


def test_no_active_design_is_one_refusal_with_the_fix():
    adapter = _adapter(design=False)
    assert adapter.info().to_payload()["connected"] is True
    with pytest.raises(TeeError) as err:
        adapter.execute([RECT])
    assert err.value.code == "fusion_no_design" and "File > New Design" in err.value.fix
    with pytest.raises(TeeError):
        adapter.list_entities()


def test_a_bridge_that_is_down_is_not_connected():
    class _Down(FakeFusionWire):
        def execute(self, code, **kw):
            raise TeeError("fusion_unreachable", "down", fix="start it")

    adapter = FusionAdapter(_Down())
    info = adapter.info().to_payload()
    assert info["connected"] is False and info["product"] == "Autodesk Fusion"
    assert adapter.probe() is False


# -- checkpoints -----------------------------------------------------------------------


def test_a_checkpoint_is_the_timeline_plus_parameters_and_says_so():
    adapter = _adapter()
    _plate(adapter)
    payload = adapter.snapshot("plate")
    assert payload["marker"] == 2 and payload["count"] == 2
    assert payload["params"] == {"d1": "10 mm"}
    assert "timeline+parameters" in payload["restores"] and "not restored" in payload["restores"]
    # after: a second extrude, a fillet, the first extrude thickened
    adapter.execute(
        [
            {"op": "create", "kind": "sketch", "name": "s2", "props": {"circles": [[0, 0, 10]]}},
            {"op": "create", "kind": "extrude", "props": {"sketch": "sk2", "distance": 3}},
            {"op": "create", "kind": "fillet", "props": {"body": "b1", "radius": 1}},
            {"op": "set", "id": "f1", "props": {"expression": "25 mm"}},
        ]
    )
    assert {e.id for e in adapter.list_entities()} == {"sk1", "f1", "b1", "sk2", "f2", "b2", "f3"}
    adapter.restore(payload)
    listed = {e.id: e for e in adapter.list_entities()}
    assert set(listed) == {"sk1", "f1", "b1"}, "what came after the marker is gone"
    assert listed["b1"].summary["volume_mm3"] == pytest.approx(96_000.0), "the expression is back"
    assert listed["f1"].summary["distance_mm"] == pytest.approx(10.0)


def test_a_direct_modeling_design_refuses_a_checkpoint_honestly():
    adapter = _adapter(parametric=False)
    _plate(adapter)
    with pytest.raises(TeeError) as err:
        adapter.snapshot("x")
    assert err.value.code == "fusion_direct_design" and "Capture Design History" in err.value.fix


# -- imports ---------------------------------------------------------------------------


def test_a_step_file_lands_as_a_body_with_its_own_units(tmp_path):
    adapter = _adapter()
    _plate(adapter)
    path = tmp_path / "plate.step"
    adapter.run(codegen.export_program("step", str(path), None))  # STEP takes a component
    diff = adapter.execute([{"op": "import_file", "path": str(path), "name": "imported"}])
    assert diff.created == ["b2"] and diff.details["b2"]["name"] == "imported"
    assert diff.details["b2"]["bbox_mm"] == pytest.approx([120.0, 80.0, 10.0])
    assert "createSTEPImportOptions" in adapter.wire.executed[-1]
    assert "importToTarget2(_opts, _root)" in adapter.wire.executed[-1]


# -- capture ------------------------------------------------------------------------------


def test_capture_fits_then_saves_a_jpeg_under_budget_with_at_most_two_renders():
    adapter = _adapter()
    _plate(adapter)
    data = adapter.capture("viewport", 64 * 1024)
    assert data.startswith(b"\xff\xd8") and len(data) <= 64 * 1024
    viewport = adapter.wire.app.activeViewport
    assert viewport.fits == 1 and viewport.saved[0][1:] == (1024, 576)
    small = adapter.capture("viewport", 2_000)
    assert len(small) <= 2_000 and viewport.saved[-1][1:] == (320, 180)
    with pytest.raises(TeeError) as err:
        adapter.capture("viewport", 100)
    assert err.value.code == "capture_over_budget"


def test_a_png_only_fusion_is_re_encoded_to_jpeg():
    pytest.importorskip("PIL")
    adapter = _adapter(jpg_supported=False)
    _plate(adapter)
    data = adapter.capture("viewport", 64 * 1024)
    assert data.startswith(b"\xff\xd8")
    assert adapter.wire.app.activeViewport.saved[0][0].endswith(".png")


def test_capture_with_no_document_refuses():
    adapter = _adapter(design=False)
    with pytest.raises(TeeError) as err:
        adapter.capture("viewport", 65536)
    assert err.value.code == "fusion_no_design"


# -- vocabulary ------------------------------------------------------------------------------


def test_the_vocab_is_the_codegens_and_never_touches_the_wire():
    vocab = _adapter().vocab()
    assert vocab.ops == codegen.OPS and vocab.kinds == codegen.KINDS
    assert vocab.imports == codegen.IMPORT_SUFFIXES and vocab.renders and not vocab.kind_optional
    assert vocab.accepts({"op": "create", "kind": "extrude"})
    assert not vocab.accepts({"op": "create", "kind": "cube"})
    assert vocab.accepts({"op": "param_set", "name": "w", "expression": "1 mm"})


# -- A71: the id map is per design ----------------------------------------------------


def test_a_design_switch_empties_the_id_map_and_no_foreign_token_is_ever_resolved(tmp_path):
    """Measured live on Fusion 2704.1.53 (A71, 2026-09-06): the listing's prune
    called findEntityByToken on ids minted in a design that had since been
    closed, and Fusion segfaulted inside DesignImp::findEntityByToken_raw, then
    sat in its crash reporter with the primary thread - and the bridge - held.
    The map is per DOCUMENT, keyed by Document.creationId (row 52) - the root
    component's entityToken is the same 24 characters in every untitled design
    (measured) and the first fix keyed on it crashed Fusion the same way. A
    switch empties the map and renumbers, as a bridge restart does, and a token
    from another document never reaches Fusion."""
    from fixtures_fusion import Design, Document

    wire = FakeFusionWire()
    adapter = FusionAdapter(wire, workdir=str(tmp_path))
    adapter.execute(
        [
            {"op": "create", "kind": "sketch", "props": {"rects": [[0, 0, 120, 80]]}},
            {"op": "create", "kind": "extrude", "props": {"sketch": "sk1", "distance": 10}},
        ]
    )
    first = wire.namespace["_tee"]  # the persistent dict itself; copy what the switch clears
    first_design = str(first["design"])
    assert set(first["ids"]) == {"sk1", "f1", "b1"} and first_design
    foreign_tokens = set(first["ids"].values())

    # a new design becomes active (File > New Design, or the previous one closed)
    old_design = wire.app.activeProduct
    new_design = Design(parametric=True)
    wire.app.activeProduct = new_design
    wire.app.activeDocument = Document("Untitled(1)")
    real_find = new_design.findEntityByToken

    def guarded(token):
        assert token not in foreign_tokens, f"a token from another design reached Fusion: {token}"
        return real_find(token)

    new_design.findEntityByToken = guarded
    assert adapter.list_entities() == []
    state = wire.namespace["_tee"]
    assert state["ids"] == {} and state["design"] != first_design
    adapter.execute(
        [
            {"op": "create", "kind": "sketch", "props": {"rects": [[0, 0, 10, 10]]}},
            {"op": "create", "kind": "extrude", "props": {"sketch": "sk1", "distance": 1}},
        ]
    )
    assert set(wire.namespace["_tee"]["ids"]) == {"sk1", "f1", "b1"}, "renumbered from 1"
    assert adapter.info().extra["ids"] == 3
    # the old design is untouched and still holds its own entities
    assert old_design.findEntityByToken(next(iter(foreign_tokens)))
