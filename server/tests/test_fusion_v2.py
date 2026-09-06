"""A70 - the Fusion lane v2 on the shim.

P1: sketch geometry has addresses, constraints and dimensions are ops, a
dimension is an entity whose expression binds a user parameter - and the
shim solves rectangles and circles only, saying so (doc 71 section 10.1,
Laws 8 and 10).
"""

from __future__ import annotations

import pytest
from fixtures_fusion import FakeFusionWire

from tee.adapters.fusion import codegen
from tee.adapters.fusion.adapter import FusionAdapter
from tee.kernel.errors import TeeError


def _adapter(**kw) -> FusionAdapter:
    return FusionAdapter(FakeFusionWire(**kw))


PARAMS = [
    {"op": "create", "kind": "param", "name": "width", "props": {"value": "120 mm"}},
    {"op": "create", "kind": "param", "name": "height", "props": {"value": "80 mm"}},
]
# a 100x50 rectangle anchored at the origin, fully constrained, dimensioned
# to the two user parameters - so it ends up 120x80
RECT = {
    "op": "create",
    "kind": "sketch",
    "name": "base",
    "props": {
        "rects": [[0, 0, 100, 50]],
        "constraints": [
            {"type": "coincident", "of": ["r0.bl", "origin"]},
            {"type": "horizontal", "of": ["r0.bottom"]},
            {"type": "horizontal", "of": ["r0.top"]},
            {"type": "vertical", "of": ["r0.left"]},
            {"type": "vertical", "of": ["r0.right"]},
        ],
        "dims": [
            {
                "name": "w",
                "type": "distance",
                "of": ["r0.bl", "r0.br"],
                "orientation": "horizontal",
                "expression": "width",
            },
            {
                "name": "h",
                "type": "distance",
                "of": ["r0.bl", "r0.tl"],
                "orientation": "vertical",
                "expression": "height",
            },
        ],
    },
}
EXTRUDE = {
    "op": "create",
    "kind": "extrude",
    "name": "plate",
    "props": {"sketch": "sk1", "distance": 10},
}


# -- P1: addresses, constraints, dimensions -------------------------------------------


def test_a_rectangle_dimensioned_to_user_parameters_follows_them():
    adapter = _adapter()
    diff = adapter.execute([*PARAMS, RECT, EXTRUDE])
    assert diff.created == ["param:width", "param:height", "sk1", "dim1", "dim2", "f1", "b1"]
    sketch = diff.details["sk1"]
    assert sketch["constraints"] == 5 and sketch["dims"] == 2 and sketch["constrained"] is True
    assert diff.details["dim1"] == {
        "name": "w",
        "kind": "dimension",
        "parent": "sk1",
        "type": "SketchLinearDimension",
        "expression": "width",
        "value": 120.0,
        "driving": True,
    }
    assert diff.details["b1"]["bbox_mm"] == pytest.approx([120.0, 80.0, 10.0]), (
        "the dimensions drove the 100x50 rectangle to 120x80 before the extrude"
    )
    script = adapter.wire.executed[-1]
    assert (
        "addDistanceDimension(_ents[0], _ents[1], "
        "adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, _tp, True)" in script
    )
    assert "_d.parameter.expression = 'width'" in script
    assert "addCoincident(_sub(_sid, 'r0.bl', 2), _sub(_sid, 'origin', 2))" in script
    assert "addHorizontal(_sub(_sid, 'r0.bottom', 2))" in script
    # the parametric truth: a param_set re-sizes the body through the dimension
    adapter.execute([{"op": "param_set", "name": "width", "expression": "150 mm"}])
    body = next(e for e in adapter.list_entities() if e.id == "b1")
    assert body.summary["bbox_mm"] == pytest.approx([150.0, 80.0, 10.0])
    assert body.summary["volume_mm3"] == pytest.approx(120_000.0)
    dim = next(e for e in adapter.list_entities() if e.id == "dim1")
    assert dim.summary["value"] == 150.0 and dim.name == "w" and dim.parent == "sk1"


def test_a_rectangles_sides_are_named_by_position_not_by_the_order_returned():
    adapter = _adapter()
    adapter.execute(
        [
            {
                "op": "create",
                "kind": "sketch",
                "name": "s",
                "props": {
                    "rects": [[0, 0, 40, 20]],
                    "circles": [[20, 10, 5]],
                    "lines": [[0, 30, 40, 30]],
                    "points": [[5, 5]],
                },
            }
        ]
    )
    subs = adapter.wire.namespace["_tee"]["subs"]["sk1"]
    assert set(subs) == {
        "origin",
        "r0.bottom",
        "r0.top",
        "r0.left",
        "r0.right",
        "r0.bl",
        "r0.br",
        "r0.tl",
        "r0.tr",
        "l0",
        "l0.start",
        "l0.end",
        "c0",
        "c0.center",
        "p0",
    }
    design = adapter.wire.design

    def ent(ref):
        return design.findEntityByToken(subs[ref])[0]

    # the shim returns the four lines scrambled (Law 8): classification wins
    bottom, right, top, left = ent("r0.bottom"), ent("r0.right"), ent("r0.top"), ent("r0.left")
    assert {bottom.startSketchPoint.geometry.y, bottom.endSketchPoint.geometry.y} == {0.0}
    assert {top.startSketchPoint.geometry.y, top.endSketchPoint.geometry.y} == {2.0}
    assert {left.startSketchPoint.geometry.x, left.endSketchPoint.geometry.x} == {0.0}
    assert {right.startSketchPoint.geometry.x, right.endSketchPoint.geometry.x} == {4.0}
    tl, br = ent("r0.tl").geometry, ent("r0.br").geometry
    assert (tl.x, tl.y) == (0.0, 2.0) and (br.x, br.y) == (4.0, 0.0)
    assert ent("c0.center").geometry.x == 2.0 and ent("p0").geometry.y == 0.5
    assert ent("origin").geometry.x == 0.0


def test_addresses_resolve_across_batches_and_a_miss_names_what_exists():
    adapter = _adapter()
    adapter.execute(
        [
            {
                "op": "create",
                "kind": "sketch",
                "props": {
                    "rects": [[0, 0, 40, 20]],
                    "circles": [[20, 10, 5]],
                    "lines": [[0, 30, 40, 30]],
                },
            }
        ]
    )
    diff = adapter.execute(
        [
            {
                "op": "create",
                "kind": "constraint",
                "props": {"sketch": "sk1", "type": "horizontal", "of": ["l0"]},
            },
            {
                "op": "create",
                "kind": "dimension",
                "name": "bore",
                "props": {"type": "diameter", "of": ["sk1/c0"], "expression": "12 mm"},
            },
        ]
    )
    assert diff.modified == ["sk1"] and diff.created == ["dim1"]
    assert diff.details["sk1"]["constraints"] == 1 and diff.details["sk1"]["dims"] == 1
    assert diff.details["dim1"]["value"] == 12.0 and diff.details["dim1"]["name"] == "bore"
    assert "addDiameterDimension(_ents[0], _tp, True)" in adapter.wire.executed[-1]
    with pytest.raises(TeeError) as err:
        adapter.execute(
            [
                {
                    "op": "create",
                    "kind": "constraint",
                    "props": {"sketch": "sk1", "type": "vertical", "of": ["r7.left"]},
                }
            ]
        )
    assert err.value.code == "fusion_unknown_entity"
    assert "r7.left" in err.value.message and "r0.left" in err.value.message
    with pytest.raises(TeeError) as err:
        adapter.execute(
            [
                {
                    "op": "create",
                    "kind": "constraint",
                    "props": {"sketch": "b9", "type": "horizontal", "of": ["l0"]},
                }
            ]
        )
    assert err.value.code == "fusion_unknown_entity"


def test_dimensions_are_entities_that_list_set_and_delete():
    adapter = _adapter()
    adapter.execute(
        [
            {
                "op": "create",
                "kind": "sketch",
                "props": {"circles": [[0, 0, 10]], "dims": [{"type": "radius", "of": ["c0"]}]},
            }
        ]
    )
    listed = {e.id: e for e in adapter.list_entities()}
    assert set(listed) == {"sk1", "dim1"}
    dim = listed["dim1"]
    assert dim.kind == "dimension" and dim.parent == "sk1" and dim.name == "d1"
    assert dim.summary == {
        "type": "SketchRadialDimension",
        "expression": "10 mm",
        "value": 10.0,
        "driving": True,
    }
    diff = adapter.execute([{"op": "set", "id": "dim1", "props": {"expression": "15 mm"}}])
    assert diff.modified == ["dim1"] and diff.details["dim1"]["value"] == 15.0
    assert (
        adapter.wire.design.rootComponent.sketches.item(0).sketchCurves.sketchCircles.item(0).radius
        == 1.5
    )
    diff = adapter.execute([{"op": "delete", "id": "dim1"}])
    assert diff.deleted == ["dim1"]
    assert {e.id for e in adapter.list_entities()} == {"sk1"}
    assert next(e for e in adapter.list_entities() if e.id == "sk1").summary["dims"] == 0


def test_a_driven_dimension_has_no_parameter_and_says_so():
    adapter = _adapter()
    diff = adapter.execute(
        [
            {
                "op": "create",
                "kind": "sketch",
                "props": {
                    "circles": [[0, 0, 10]],
                    "dims": [{"type": "radius", "of": ["c0"], "driving": False}],
                },
            }
        ]
    )
    assert diff.details["dim1"]["driving"] is False and diff.details["dim1"]["expression"] is None
    with pytest.raises(TeeError) as err:
        adapter.execute([{"op": "set", "id": "dim1", "props": {"expression": "5 mm"}}])
    assert err.value.code == "fusion_op_failed" and "driven dimension" in err.value.message


def test_the_shim_refuses_a_constraint_the_geometry_contradicts():
    """Law 10: the shim does not solve, so a coincident on a corner that is
    not at the origin comes back as Fusion's own creation failure - one
    refusal naming the op, nothing after it run."""
    adapter = _adapter()
    with pytest.raises(TeeError) as err:
        adapter.execute(
            [
                {
                    "op": "create",
                    "kind": "sketch",
                    "props": {
                        "rects": [[10, 10, 50, 30]],
                        "constraints": [{"type": "coincident", "of": ["r0.bl", "origin"]}],
                    },
                },
                EXTRUDE,
            ]
        )
    assert err.value.code == "fusion_op_failed" and "Batch op 0 failed" in err.value.message
    assert "coincident constraint on r0.bl + origin" in err.value.message
    # the sketch itself was made before its constraint failed (the kernel's
    # checkpoint restores that); the extrude after it never ran
    assert [e.kind for e in adapter.list_entities()] == ["sketch"]


def test_an_unconstrained_rectangle_reports_so_and_rollback_takes_dims_with_it():
    adapter = _adapter()
    adapter.execute([{"op": "create", "kind": "sketch", "props": {"rects": [[0, 0, 40, 20]]}}])
    sketch = next(e for e in adapter.list_entities() if e.id == "sk1")
    assert sketch.summary["constrained"] is False and sketch.summary["constraints"] == 0
    payload = adapter.snapshot("bare")
    adapter.execute(
        [
            {
                "op": "create",
                "kind": "dimension",
                "props": {
                    "type": "distance",
                    "of": ["sk1/r0.bl", "sk1/r0.br"],
                    "orientation": "horizontal",
                },
            },
            {
                "op": "create",
                "kind": "sketch",
                "props": {"circles": [[0, 0, 3]], "dims": [{"type": "diameter", "of": ["c0"]}]},
            },
        ]
    )
    assert {e.id for e in adapter.list_entities()} == {"sk1", "dim1", "sk2", "dim2"}
    adapter.restore(payload)
    assert {e.id for e in adapter.list_entities()} == {"sk1", "dim1"}, (
        "the dimension on the surviving sketch stays; the later sketch and its dimension go"
    )


@pytest.mark.parametrize(
    ("props", "needle"),
    [
        ({"type": "welded", "of": ["l0"]}, "Types:"),
        ({"type": "horizontal", "of": ["l0", "l1"]}, "takes 1 address in"),
        ({"type": "symmetry", "of": ["l0", "l1"]}, "takes 3 addresses"),
        ({"type": "horizontal", "of": ["bottom"]}, "Bad sketch address"),
        (
            {"type": "horizontal", "of": ["sk1/r0.bl", "sk2/origin"], "sketch": None},
            "another sketch",
        ),
        ({"type": "horizontal", "of": ["l0"]}, "needs sketch"),
    ],
)
def test_a_malformed_constraint_is_refused_before_the_wire(props, needle):
    adapter = _adapter()
    if props.get("type") == "horizontal" and props["of"] == ["sk1/r0.bl", "sk2/origin"]:
        props = {"type": "coincident", "of": ["sk1/r0.bl", "sk2/origin"]}
    with pytest.raises(TeeError) as err:
        adapter.execute([{"op": "create", "kind": "constraint", "props": props}])
    assert err.value.code == "bad_op" and needle in (err.value.message + err.value.fix)
    assert adapter.wire.executed == []


@pytest.mark.parametrize(
    ("op", "needle"),
    [
        (
            {
                "op": "create",
                "kind": "dimension",
                "props": {"sketch": "sk1", "type": "gap", "of": ["l0"]},
            },
            "Types:",
        ),
        (
            {
                "op": "create",
                "kind": "dimension",
                "props": {
                    "sketch": "sk1",
                    "type": "distance",
                    "of": ["l0.start", "l0.end"],
                    "orientation": "slanted",
                },
            },
            "aligned, horizontal or vertical",
        ),
        (
            {
                "op": "create",
                "kind": "dimension",
                "props": {
                    "sketch": "sk1",
                    "type": "diameter",
                    "of": ["c0"],
                    "orientation": "horizontal",
                },
            },
            "not one a diameter dimension takes",
        ),
        (
            {
                "op": "create",
                "kind": "dimension",
                "props": {"sketch": "sk1", "type": "radius", "of": ["c0"], "text": [1]},
            },
            "text is [x, y]",
        ),
        (
            {"op": "create", "kind": "sketch", "props": {"rects": [[0, 0, 0, 5]]}},
            "nonzero width and height",
        ),
        (
            {"op": "create", "kind": "sketch", "props": {"lines": [[1, 1, 1, 1]]}},
            "two distinct points",
        ),
        ({"op": "create", "kind": "sketch", "props": {"points": [[1, 2, 3]]}}, "A point is [x, y]"),
        (
            {
                "op": "create",
                "kind": "sketch",
                "props": {
                    "rects": [[0, 0, 1, 1]],
                    "constraints": [{"type": "horizontal", "of": ["sk1/r0.top"]}],
                },
            },
            "bare",
        ),
    ],
)
def test_a_malformed_dimension_or_sketch_is_refused_before_the_wire(op, needle):
    adapter = _adapter()
    with pytest.raises(TeeError) as err:
        adapter.execute([op])
    assert err.value.code == "bad_op" and needle in (err.value.message + err.value.fix)
    assert adapter.wire.executed == []


def test_the_vocabulary_grew_with_the_kinds():
    vocab = _adapter().vocab()
    assert {"constraint", "dimension"} <= set(codegen.KINDS) and vocab.kinds == codegen.KINDS
    assert vocab.accepts({"op": "create", "kind": "dimension"})
