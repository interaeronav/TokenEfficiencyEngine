"""A70 - the Fusion lane v2 on the shim.

P1: sketch geometry has addresses, constraints and dimensions are ops, a
dimension is an entity whose expression binds a user parameter - and the
shim solves rectangles and circles only, saying so (doc 71 section 10.1,
Laws 8 and 10). P2: faces by outward normal, holes that subtract what they
bore, chamfers on named edges, revolves by Pappus (sections 10.2-10.4).
"""

from __future__ import annotations

import math

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
    grown = {"constraint", "dimension", "hole", "chamfer", "revolve"}
    assert grown <= set(codegen.KINDS) and vocab.kinds == codegen.KINDS
    assert vocab.accepts({"op": "create", "kind": "dimension"})
    assert vocab.accepts({"op": "create", "kind": "hole"})


# -- P2: faces by direction, holes, chamfers, revolves ------------------------------------

PLATE = [
    {"op": "create", "kind": "sketch", "name": "base", "props": {"rects": [[0, 0, 120, 80]]}},
    EXTRUDE,
]


def _hole(**props):
    return {"op": "create", "kind": "hole", "props": props}


def test_two_through_holes_on_the_top_face_subtract_their_cylinders():
    adapter = _adapter()
    adapter.execute(PLATE)
    diff = adapter.execute(
        [
            _hole(body="b1", face="+z", at=[20, 20], diameter=6.6, through=True),
            _hole(body="b1", face="+z", at=[100, 60, 10], diameter=6.6, through=True),
        ]
    )
    assert diff.created == ["f2", "f3"] and diff.modified == ["b1"]
    r = 3.3
    assert diff.details["b1"]["volume_mm3"] == pytest.approx(96_000.0 - 2 * math.pi * r * r * 10)
    hole = diff.details["f2"]
    assert hole["type"] == "HoleFeature" and hole["diameter_mm"] == pytest.approx(6.6)
    assert hole["position_mm"] == pytest.approx([20.0, 20.0, 10.0]), "a 2-vector lands on the face"
    assert diff.details["f3"]["position_mm"] == pytest.approx([100.0, 60.0, 10.0])
    script = adapter.wire.executed[-1]
    assert "createSimpleInput(adsk.core.ValueInput.createByString('6.6 mm'))" in script
    assert "_inp.setPositionByPoint(_fc, _at_point(_fc, '+z', [2.0, 2.0]))" in script
    assert "setAllExtent(adsk.fusion.ExtentDirections.PositiveExtentDirection)" in script
    assert "isDefaultDirection" not in script


def test_a_counterbore_and_a_countersink_subtract_their_extra():
    adapter = _adapter()
    adapter.execute(PLATE)
    diff = adapter.execute(
        [
            _hole(
                body="b1",
                face="+z",
                at=[30, 40],
                diameter=6.6,
                depth=10,
                type="counterbore",
                cbore_diameter=11,
                cbore_depth=6,
            )
        ]
    )
    r, cb_r = 3.3, 5.5
    bore = math.pi * r * r * 10 + math.pi * (cb_r * cb_r - r * r) * 6
    assert diff.details["b1"]["volume_mm3"] == pytest.approx(96_000.0 - bore)
    script = adapter.wire.executed[-1]
    assert (
        "createCounterboreInput(adsk.core.ValueInput.createByString('6.6 mm'), "
        "adsk.core.ValueInput.createByString('11 mm'), adsk.core.ValueInput.createByString('6 mm'))"
        in script
    )
    assert "setDistanceExtent(adsk.core.ValueInput.createByString('10 mm'))" in script
    diff = adapter.execute(
        [
            _hole(
                body="b1",
                face="+z",
                at=[90, 40],
                diameter=6.6,
                depth=10,
                type="countersink",
                csink_diameter=12,
                csink_angle=90,
            )
        ]
    )
    cs_r = 6.0
    h = (cs_r - r) / math.tan(math.pi / 4)
    frustum = math.pi * h / 3 * (cs_r * cs_r + cs_r * r + r * r) - math.pi * r * r * h
    sink = math.pi * r * r * 10 + frustum
    assert diff.details["b1"]["volume_mm3"] == pytest.approx(96_000.0 - bore - sink)
    assert "adsk.core.ValueInput.createByString('90 deg')" in adapter.wire.executed[-1]


def test_a_hole_by_sketch_point_and_a_flipped_direction():
    adapter = _adapter()
    adapter.execute(PLATE)
    diff = adapter.execute(
        [
            {"op": "create", "kind": "sketch", "name": "pts", "props": {"points": [[30, 30]]}},
            _hole(point="sk2/p0", diameter=5, depth=10, flip=True),
        ]
    )
    assert diff.created == ["sk2", "f2"] and diff.modified == ["b1"]
    assert diff.details["b1"]["volume_mm3"] == pytest.approx(96_000.0 - math.pi * 6.25 * 10)
    script = adapter.wire.executed[-1]
    assert "_spt = _sub('sk2', 'p0', 1)" in script and "setPositionBySketchPoint(_spt)" in script
    assert "_inp.isDefaultDirection = False" in script
    # the diameter is a parameter: set it and the body follows (row 34)
    diff = adapter.execute([{"op": "set", "id": "f2", "props": {"expression": "8 mm"}}])
    assert diff.details["f2"]["diameter_mm"] == pytest.approx(8.0)
    body = next(e for e in adapter.list_entities() if e.id == "b1")
    assert body.summary["volume_mm3"] == pytest.approx(96_000.0 - math.pi * 16 * 10)


def test_a_face_the_body_lacks_refuses_naming_the_ones_it_has():
    adapter = _adapter()
    adapter.execute(
        [
            {"op": "create", "kind": "sketch", "props": {"circles": [[0, 0, 20]]}},
            {"op": "create", "kind": "extrude", "props": {"sketch": "sk1", "distance": 30}},
        ]
    )
    with pytest.raises(TeeError) as err:
        adapter.execute([_hole(body="b1", face="+x", at=[5, 5], diameter=4, depth=5)])
    assert err.value.code == "fusion_no_face"
    assert "facing +x" in err.value.message and "+z, -z" in err.value.message
    assert "+x, -x, +y, -y, +z, -z" in err.value.fix


def test_a_chamfer_on_the_top_faces_edges_takes_four_edges_and_never_the_retired_call():
    adapter = _adapter()
    adapter.execute(PLATE)
    diff = adapter.execute(
        [
            {
                "op": "create",
                "kind": "chamfer",
                "name": "break",
                "props": {"body": "b1", "distance": 1, "edges": {"face": "+z"}},
            },
            {
                "op": "create",
                "kind": "fillet",
                "props": {"body": "b1", "radius": 2, "edges": {"face": "-z"}},
            },
            {"op": "create", "kind": "fillet", "props": {"body": "b1", "radius": 1}},
        ]
    )
    assert diff.created == ["f2", "f3", "f4"] and diff.modified == ["b1"]
    assert diff.details["f2"]["type"] == "ChamferFeature" and diff.details["f2"]["edges"] == 4
    assert diff.details["f3"]["edges"] == 4 and diff.details["f4"]["edges"] == 12
    assert diff.details["b1"]["volume_mm3"] == pytest.approx(96_000.0), "the timeline only"
    script = adapter.wire.executed[-1]
    assert "chamferFeatures.createInput2()" in script
    assert "chamferFeatures.createInput()" not in script, "retired December 2020 (row 35)"
    assert (
        "addEqualDistanceChamferEdgeSet(_edges, adsk.core.ValueInput.createByString('1 mm'), True)"
        in script
    )
    assert "_edges_of(_b, {'face': '+z'}, 0)" in script and "_edges_of(_b, 'all', 2)" in script


def test_a_revolve_reads_back_pappus_about_an_axis_or_a_sketch_line():
    adapter = _adapter()
    # a 10 x 20 mm rectangle whose centroid sits 30 mm above the x axis
    diff = adapter.execute(
        [
            {
                "op": "create",
                "kind": "sketch",
                "name": "profile",
                "props": {"rects": [[0, 20, 10, 40]]},
            },
            {
                "op": "create",
                "kind": "revolve",
                "name": "ring",
                "props": {"sketch": "sk1", "axis": "x"},
            },
        ]
    )
    assert diff.created == ["sk1", "f1", "b1"]
    assert diff.details["b1"]["volume_mm3"] == pytest.approx(2 * math.pi * 200 * 30)
    assert diff.details["b1"]["bbox_mm"] == pytest.approx([10.0, 80.0, 80.0])
    assert diff.details["f1"]["type"] == "RevolveFeature"
    script = adapter.wire.executed[-1]
    assert "_ax = _root.xConstructionAxis" in script
    assert (
        "revolveFeatures.createInput(_prof, _ax, "
        "adsk.fusion.FeatureOperations.NewBodyFeatureOperation)" in script
    )
    assert "setAngleExtent(False, adsk.core.ValueInput.createByString('360 deg'))" in script
    # a quarter turn each side about the rectangle's own bottom line (30 -> 10 mm)
    diff = adapter.execute(
        [
            {
                "op": "create",
                "kind": "revolve",
                "props": {"sketch": "sk1", "axis": "sk1/r0.bottom", "angle": 90, "symmetric": True},
            }
        ]
    )
    assert diff.details["b2"]["volume_mm3"] == pytest.approx(math.pi * 200 * 10)
    script = adapter.wire.executed[-1]
    assert "_ax = _sub('sk1', 'r0.bottom', 0)" in script
    assert "setAngleExtent(True, adsk.core.ValueInput.createByString('90 deg'))" in script


def test_a_profile_crossing_its_axis_is_fusions_own_failure():
    adapter = _adapter()
    with pytest.raises(TeeError) as err:
        adapter.execute(
            [
                {"op": "create", "kind": "sketch", "props": {"rects": [[0, -10, 10, 10]]}},
                {"op": "create", "kind": "revolve", "props": {"sketch": "sk1", "axis": "x"}},
            ]
        )
    assert err.value.code == "fusion_op_failed" and "revolve failed" in err.value.message
    with pytest.raises(TeeError) as err:
        adapter.execute(
            [
                {"op": "create", "kind": "sketch", "props": {"rects": [[0, 20, 10, 40]]}},
                {"op": "create", "kind": "revolve", "props": {"sketch": "sk2", "axis": "z"}},
            ]
        )
    assert "leave the sketch plane" in err.value.message


@pytest.mark.parametrize(
    ("props", "needle"),
    [
        ({"body": "b1", "face": "+z", "at": [1, 1]}, "needs diameter"),
        ({"body": "b1", "face": "+z", "at": [1, 1], "diameter": 5, "type": "square"}, "Types:"),
        ({"body": "b1", "face": "+w", "at": [1, 1], "diameter": 5, "depth": 1}, "one of +x"),
        ({"body": "b1", "face": "+z", "diameter": 5, "depth": 1}, "needs at"),
        ({"body": "b1", "face": "+z", "at": [1, 1], "diameter": 5}, "through: true OR depth"),
        (
            {"body": "b1", "face": "+z", "at": [1, 1], "diameter": 5, "depth": 1, "through": True},
            "not both",
        ),
        ({"point": "p0", "diameter": 5, "depth": 1}, "with its sketch"),
        ({"point": "sk1/r0.top", "diameter": 5, "depth": 1}, "not a point address"),
        (
            {
                "body": "b1",
                "face": "+z",
                "at": [1, 1],
                "diameter": 5,
                "depth": 1,
                "type": "counterbore",
            },
            "cbore_diameter",
        ),
        (
            {
                "body": "b1",
                "face": "+z",
                "at": [1, 1],
                "diameter": 5,
                "depth": 1,
                "type": "countersink",
                "csink_diameter": 4,
            },
            "csink_diameter",
        ),
    ],
)
def test_a_malformed_hole_is_refused_before_the_wire(props, needle):
    adapter = _adapter()
    with pytest.raises(TeeError) as err:
        adapter.execute([_hole(**props)])
    assert err.value.code == "bad_op" and needle in (err.value.message + err.value.fix)
    assert adapter.wire.executed == []


@pytest.mark.parametrize(
    ("op", "needle"),
    [
        ({"op": "create", "kind": "chamfer", "props": {"body": "b1"}}, "distance (mm > 0)"),
        (
            {
                "op": "create",
                "kind": "chamfer",
                "props": {"body": "b1", "distance": 1, "edges": "top"},
            },
            "edges is 'all' or",
        ),
        (
            {
                "op": "create",
                "kind": "fillet",
                "props": {"body": "b1", "radius": 1, "edges": {"face": "up"}},
            },
            "directions:",
        ),
        ({"op": "create", "kind": "revolve", "props": {"axis": "x"}}, "needs sketch"),
        (
            {"op": "create", "kind": "revolve", "props": {"sketch": "sk1", "axis": "w"}},
            "with its sketch",
        ),
        (
            {"op": "create", "kind": "revolve", "props": {"sketch": "sk1", "axis": "sk2/l0"}},
            "another sketch",
        ),
        (
            {
                "op": "create",
                "kind": "revolve",
                "props": {"sketch": "sk1", "axis": "x", "angle": 0},
            },
            "degrees in (0, 360]",
        ),
        (
            {
                "op": "create",
                "kind": "revolve",
                "props": {"sketch": "sk1", "axis": "x", "operation": "melt"},
            },
            "Use:",
        ),
    ],
)
def test_a_malformed_chamfer_fillet_or_revolve_is_refused_before_the_wire(op, needle):
    adapter = _adapter()
    with pytest.raises(TeeError) as err:
        adapter.execute([op])
    assert err.value.code == "bad_op" and needle in (err.value.message + err.value.fix)
    assert adapter.wire.executed == []
