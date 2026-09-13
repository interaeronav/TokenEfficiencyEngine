"""A79: CADAgent-derived modelling through the existing Fusion batch protocol.

The generated scripts execute against FakeFusionWire. These extra collections
record the native inputs and mimic timeline ownership only; they make no claim
about shell volume or pattern placement. Real geometry is the live smoke's job.
"""

from __future__ import annotations

from types import SimpleNamespace

import fixtures_fusion as shim
import pytest

from tee.adapters.fusion.adapter import FusionAdapter
from tee.kernel.errors import TeeError


def _create(kind, props, **fields):
    return {"op": "create", "kind": kind, "props": props, **fields}


SEED = [
    _create("sketch", {"rects": [[0, 0, 40, 30]]}, **{"as": "profile"}),
    _create("extrude", {"sketch": "@profile", "distance": 20}, **{"as": "seed"}),
]
SHELL = {"body": "b1", "inside": 2}
RECTANGULAR = {"features": ["f1"], "axis": "x", "count": 3, "spacing": 15}
CIRCULAR = {"features": ["f1"], "axis": "z", "count": 4}


class _CadFeature(shim._Feature):
    def __init__(self, component, kind, inp):
        super().__init__(component._design, component, kind)
        self.objectType = f"adsk::fusion::{kind}Feature"
        self.assemblyContext = None
        self.input = inp
        if kind == "Shell":
            self._bodies = list(dict.fromkeys(getattr(e, "body", e) for e in inp.entities))
        else:
            # Multiple bodies intentionally expose any alias that silently
            # chooses a first body. No physical operation is modelled here.
            source = inp.entities.item(0).bodies.item(0)
            self._bodies = [source]
            clone = shim.BRepBody(
                component._design, component, "pattern-copy", list(source.dims), source.shape
            )
            component._bodies.append(clone)
            self._bodies.append(clone)
            self._created.append(clone)


class _CadCollection:
    def __init__(self, component, kind):
        self.component, self.kind = component, kind
        self.inputs = []
        self.refuse = False
        self.refuse_input = False
        self.refuse_second_direction = False

    def createInput(self, *args):
        if self.refuse_input:
            return None
        if self.kind == "Shell":
            entities, tangent = args
            inp = SimpleNamespace(entities=entities, tangent=tangent)
        elif self.kind == "RectangularPattern":
            entities, axis, quantity, distance, distance_type = args
            inp = SimpleNamespace(
                entities=entities,
                directionOneEntity=axis,
                quantityOne=quantity,
                distanceOne=distance,
                patternDistanceType=distance_type,
                # Native Fusion retained quantityTwo=3 in the live smoke:
                # omitted second-direction settings produced nine instances.
                # Positive spacing and symmetry also model sticky GUI state.
                quantityTwo=shim.ValueInput.createByString("3"),
                distanceTwo=shim.ValueInput.createByString("10 mm"),
                isSymmetricInDirectionOne=True,
                isSymmetricInDirectionTwo=True,
            )

            def second_direction(axis, quantity, distance):
                inp.directionTwoEntity = axis
                inp.quantityTwo = quantity
                inp.distanceTwo = distance
                return not self.refuse_second_direction

            inp.setDirectionTwo = second_direction
        else:
            entities, axis = args
            inp = SimpleNamespace(entities=entities, axis=axis)
        self.inputs.append(inp)
        return inp

    def add(self, inp):
        if self.refuse:
            return None
        feature = _CadFeature(self.component, self.kind, inp)
        self.component._features.append(feature)
        return feature


@pytest.fixture
def adapter(monkeypatch):
    """Extend only this test's shim; preserve all existing Fusion fixtures."""
    original_features = shim.Component.features.fget
    original_modules = shim._modules

    def features(component):
        result = original_features(component)
        if not hasattr(component, "cad_collections"):
            component.cad_collections = {
                "shellFeatures": _CadCollection(component, "Shell"),
                "rectangularPatternFeatures": _CadCollection(component, "RectangularPattern"),
                "circularPatternFeatures": _CadCollection(component, "CircularPattern"),
            }
        for name, collection in component.cad_collections.items():
            setattr(result, name, collection)
        return result

    def modules(app):
        result = original_modules(app)
        fusion = result["adsk.fusion"]
        fusion.ShellTypes = SimpleNamespace(SharpOffsetShellType=0, RoundedOffsetShellType=1)
        fusion.PatternDistanceType = SimpleNamespace(SpacingPatternDistanceType=1)
        fusion.PatternComputeOptions = SimpleNamespace(IdenticalPatternCompute=0)
        return result

    monkeypatch.setattr(shim.Component, "features", property(features))
    monkeypatch.setattr(shim, "_modules", modules)
    return FusionAdapter(shim.FakeFusionWire())


@pytest.mark.parametrize(
    ("kind", "props"),
    [
        ("shell", {"inside": 1}),
        ("shell", {**SHELL, "inside": 0}),
        ("shell", {**SHELL, "inside": -1}),
        ("shell", {**SHELL, "inside": True}),
        ("shell", {**SHELL, "inside": "2 mm"}),
        ("shell", {**SHELL, "inside": float("nan")}),
        ("shell", {**SHELL, "outside": float("inf")}),
        ("shell", {**SHELL, "outside": -1}),
        ("shell", {**SHELL, "tangent": "false"}),
        ("shell", {**SHELL, "shell_type": "smooth"}),
        ("shell", {**SHELL, "remove_faces": "+z"}),
        ("shell", {**SHELL, "remove_faces": ["top"]}),
        ("shell", {**SHELL, "remove_faces": ["+z", "+z"]}),
        ("shell", {**SHELL, "anchor": [0, 0, 0]}),
        ("rectangular_pattern", {**RECTANGULAR, "features": []}),
        ("rectangular_pattern", {**RECTANGULAR, "features": "f1"}),
        ("rectangular_pattern", {**RECTANGULAR, "features": [None]}),
        ("rectangular_pattern", {**RECTANGULAR, "features": ["f1", "f1"]}),
        ("rectangular_pattern", {**RECTANGULAR, "features": [f"f{i}" for i in range(33)]}),
        ("rectangular_pattern", {**RECTANGULAR, "axis": "XY"}),
        ("rectangular_pattern", {**RECTANGULAR, "count": 1}),
        ("rectangular_pattern", {**RECTANGULAR, "count": 1001}),
        ("rectangular_pattern", {**RECTANGULAR, "count": 2.5}),
        ("rectangular_pattern", {**RECTANGULAR, "count": True}),
        ("rectangular_pattern", {**RECTANGULAR, "count": "3"}),
        ("rectangular_pattern", {**RECTANGULAR, "spacing": 0}),
        ("rectangular_pattern", {**RECTANGULAR, "spacing": float("inf")}),
        ("rectangular_pattern", {**RECTANGULAR, "spacing": "15 mm"}),
        ("rectangular_pattern", {**RECTANGULAR, "axis2": "y"}),
        ("rectangular_pattern", {**RECTANGULAR, "count2": 2, "spacing2": 10}),
        (
            "rectangular_pattern",
            {**RECTANGULAR, "axis2": "x", "count2": 2, "spacing2": 10},
        ),
        (
            "rectangular_pattern",
            {**RECTANGULAR, "axis2": "y", "count2": 1, "spacing2": 10},
        ),
        (
            "rectangular_pattern",
            {**RECTANGULAR, "axis2": "y", "count2": 2, "spacing2": 0},
        ),
        (
            "rectangular_pattern",
            {**RECTANGULAR, "count": 50, "axis2": "y", "count2": 21, "spacing2": 10},
        ),
        ("circular_pattern", {**CIRCULAR, "angle": 0}),
        ("circular_pattern", {**CIRCULAR, "angle": -90}),
        ("circular_pattern", {**CIRCULAR, "angle": 361}),
        ("circular_pattern", {**CIRCULAR, "angle": float("nan")}),
        ("circular_pattern", {**CIRCULAR, "angle": True}),
        ("circular_pattern", {**CIRCULAR, "anchor": [10, 0, 0]}),
        ("circular_pattern", {**CIRCULAR, "spacing": 10}),
    ],
)
def test_malformed_modelling_refuses_the_whole_batch_before_wire(adapter, kind, props):
    with pytest.raises(TeeError) as error:
        adapter.execute([*SEED, _create(kind, props)])
    assert error.value.code == "bad_op"
    assert adapter.wire.executed == [], "even earlier valid operations must not reach Fusion"


@pytest.mark.parametrize(
    "kind,props", [("rectangular_pattern", RECTANGULAR), ("circular_pattern", CIRCULAR)]
)
@pytest.mark.parametrize("reference", ["@missing.feature", "@later.feature"])
def test_pattern_feature_references_cannot_escape_alias_preflight(adapter, kind, props, reference):
    with pytest.raises(TeeError) as error:
        adapter.execute(
            [
                *SEED,
                _create(kind, {**props, "features": [reference]}),
                _create("shell", SHELL, **{"as": "later"}),
            ]
        )
    assert error.value.code == "bad_op" and "alias" in error.value.message.lower()
    assert adapter.wire.executed == []


@pytest.mark.parametrize("remove_faces", [[], ["+z"], ["+z", "-z"]])
def test_shell_selects_body_or_named_faces_and_sends_explicit_mm(adapter, remove_faces):
    adapter.execute(SEED)
    diff = adapter.execute(
        [
            _create(
                "shell",
                {
                    **SHELL,
                    "outside": 0.5,
                    "remove_faces": remove_faces,
                    "tangent": False,
                    "shell_type": "rounded",
                },
                name="thin housing",
            )
        ]
    )
    root = adapter.wire.design.rootComponent
    inp = root.cad_collections["shellFeatures"].inputs[-1]
    assert inp.tangent is False
    assert inp.insideThickness.expression == "2.0 mm" and inp.insideThickness.value == 0.2
    assert inp.outsideThickness.expression == "0.5 mm" and inp.outsideThickness.value == 0.05
    assert inp.shellType == 1
    selected = list(inp.entities)
    body = root.bRepBodies.item(0)
    if remove_faces:
        assert all(face.body is body for face in selected)
        assert [face.geometry.normal.z for face in selected] == [
            1 if face == "+z" else -1 for face in remove_faces
        ]
    else:
        assert selected == [body], "an empty removal list means a closed shell"
    assert diff.created == ["f2"] and diff.modified == ["b1"]
    assert diff.details["f2"]["name"] == "thin housing"
    assert diff.details["f2"]["type"] == "ShellFeature"


def test_shell_defaults_and_feature_aliases_preserve_body_identity(adapter):
    diff = adapter.execute(
        [
            *SEED,
            _create("shell", {"body": "@seed", "outside": 1}, **{"as": "thin"}),
            {"op": "set", "id": "@thin", "props": {"name": "housing"}},
            {"op": "set", "id": "@thin.feature", "props": {"name": "wall"}},
        ]
    )
    inp = adapter.wire.design.rootComponent.cad_collections["shellFeatures"].inputs[0]
    assert inp.tangent is True and inp.shellType == 0
    assert diff.details["b1"]["name"] == "housing" and diff.details["f2"]["name"] == "wall"


def test_rectangular_pattern_preserves_signed_spacing_and_second_direction(adapter):
    adapter.execute(SEED)
    diff = adapter.execute(
        [
            _create(
                "rectangular_pattern",
                {**RECTANGULAR, "spacing": -15, "axis2": "y", "count2": 2, "spacing2": 25},
            )
        ]
    )
    root = adapter.wire.design.rootComponent
    inp = root.cad_collections["rectangularPatternFeatures"].inputs[0]
    assert inp.entities.item(0) is root._features[0]
    assert inp.directionOneEntity is root.xConstructionAxis
    assert inp.quantityOne.value == 3 and inp.quantityOne.unit == ""
    assert inp.distanceOne.expression == "-15.0 mm" and inp.distanceOne.value == -1.5
    assert inp.directionTwoEntity is root.yConstructionAxis
    assert inp.quantityTwo.value == 2 and inp.quantityTwo.unit == ""
    assert inp.distanceTwo.expression == "25.0 mm" and inp.distanceTwo.value == 2.5
    assert inp.patternDistanceType == 1
    assert inp.isSymmetricInDirectionOne is False
    assert inp.isSymmetricInDirectionTwo is False
    assert diff.details["f2"]["type"] == "RectangularPatternFeature"


@pytest.mark.parametrize("axis", ["x", "y", "z"])
def test_one_direction_pattern_explicitly_disables_native_second_direction_defaults(adapter, axis):
    adapter.execute(SEED)
    adapter.execute([_create("rectangular_pattern", {**RECTANGULAR, "axis": axis})])
    root = adapter.wire.design.rootComponent
    inp = root.cad_collections["rectangularPatternFeatures"].inputs[0]
    assert inp.quantityOne.value == 3
    assert inp.quantityTwo.expression == "1" and inp.quantityTwo.value == 1
    assert inp.distanceTwo.expression == "0.0 mm" and inp.distanceTwo.value == 0
    perpendicular = root.yConstructionAxis if axis == "x" else root.xConstructionAxis
    assert inp.directionTwoEntity is perpendicular
    assert inp.isSymmetricInDirectionOne is False
    assert inp.isSymmetricInDirectionTwo is False


@pytest.mark.parametrize("angle", [None, 135])
def test_circular_pattern_uses_origin_axis_degrees_and_unitless_count(adapter, angle):
    adapter.execute(SEED)
    props = CIRCULAR if angle is None else {**CIRCULAR, "angle": angle}
    adapter.execute([_create("circular_pattern", props)])
    root = adapter.wire.design.rootComponent
    inp = root.cad_collections["circularPatternFeatures"].inputs[0]
    assert inp.axis is root.zConstructionAxis
    assert inp.quantity.value == 4 and inp.quantity.unit == ""
    assert inp.isSymmetric is False
    assert inp.totalAngle.expression == f"{float(angle if angle is not None else 360)} deg"
    assert inp.totalAngle.value == pytest.approx((angle or 360) * 3.141592653589793 / 180)


def test_nearly_full_circle_preserves_partial_pattern_angle_in_native_input(adapter):
    """Rounding 359.9999 to 360 changes Fusion's full-circle spacing semantics."""
    adapter.execute(SEED)
    angle = 359.9999
    adapter.execute([_create("circular_pattern", {**CIRCULAR, "angle": angle})])
    inp = adapter.wire.design.rootComponent.cad_collections["circularPatternFeatures"].inputs[0]
    assert inp.totalAngle.expression == "359.9999 deg"
    assert inp.totalAngle.value < 2 * 3.141592653589793
    assert inp.totalAngle.value == pytest.approx(angle * 3.141592653589793 / 180, rel=0, abs=1e-14)


def test_thickness_and_signed_pattern_spacings_retain_requested_precision(adapter):
    adapter.execute(SEED)
    inside, outside = 0.123456789012345, 0.234567890123456
    spacing, spacing2 = -12.3456789012345, 23.4567890123456
    adapter.execute(
        [
            _create("shell", {**SHELL, "inside": inside, "outside": outside}),
            _create(
                "rectangular_pattern",
                {
                    **RECTANGULAR,
                    "spacing": spacing,
                    "axis2": "y",
                    "count2": 2,
                    "spacing2": spacing2,
                },
            ),
        ]
    )
    collections = adapter.wire.design.rootComponent.cad_collections
    shell = collections["shellFeatures"].inputs[0]
    pattern = collections["rectangularPatternFeatures"].inputs[0]
    for native, requested in (
        (shell.insideThickness, inside),
        (shell.outsideThickness, outside),
        (pattern.distanceOne, spacing),
        (pattern.distanceTwo, spacing2),
    ):
        numeric, unit = native.expression.split()
        assert unit == "mm" and float(numeric) == requested
        assert native.value == pytest.approx(requested * 0.1, rel=0, abs=1e-15)


@pytest.mark.parametrize(
    "kind,props", [("rectangular_pattern", RECTANGULAR), ("circular_pattern", CIRCULAR)]
)
def test_both_pattern_alias_forms_address_the_feature_even_with_multiple_bodies(
    adapter, kind, props
):
    diff = adapter.execute(
        [
            *SEED,
            _create(kind, {**props, "features": ["@seed.feature"]}, **{"as": "repeat"}),
            {"op": "set", "id": "@repeat", "props": {"name": "array"}},
            {"op": "set", "id": "@repeat.feature", "props": {"suppressed": True}},
        ]
    )
    assert diff.details["f2"]["name"] == "array"
    assert diff.details["f2"]["suppressed"] is True
    assert diff.details["b1"]["name"] != "array"
    assert diff.details["b2"]["name"] != "array"
    assert adapter.wire.design.rootComponent._features[-1].bodies.count == 2
    before = len(adapter.wire.executed)
    with pytest.raises(TeeError, match=r"[Aa]lias"):
        adapter.execute([_create(kind, {**props, "features": ["@repeat"]})])
    assert len(adapter.wire.executed) == before, "aliases expire at the end of the batch"


@pytest.mark.parametrize(
    "kind,props",
    [
        ("shell", {**SHELL, "body": "sk1"}),
        ("rectangular_pattern", {**RECTANGULAR, "features": ["b1"]}),
        ("circular_pattern", {**CIRCULAR, "features": ["sk1"]}),
    ],
)
def test_wrong_entity_types_never_reach_native_feature_add(adapter, kind, props):
    adapter.execute(SEED)
    with pytest.raises(TeeError) as error:
        adapter.execute([_create(kind, props)])
    assert error.value.code in {"bad_op", "fusion_op_failed"}
    assert adapter.wire.design.timeline.count == 2
    assert all(
        not coll.inputs for coll in adapter.wire.design.rootComponent.cad_collections.values()
    )


@pytest.mark.parametrize("context", ["other_component", "assemblyContext", "nativeObject"])
@pytest.mark.parametrize(
    "kind,props,target",
    [
        ("shell", SHELL, "b1"),
        ("rectangular_pattern", RECTANGULAR, "f1"),
        ("circular_pattern", CIRCULAR, "f1"),
    ],
)
def test_other_component_and_assembly_proxy_targets_are_refused(
    adapter, context, kind, props, target
):
    adapter.execute(SEED)
    design = adapter.wire.design
    entity = design.findEntityByToken(adapter.wire.namespace["_tee"]["ids"][target])[0]
    if context == "other_component":
        entity.parentComponent = shim.Component(design, "Other")
    else:
        setattr(entity, context, object())
    with pytest.raises(TeeError) as error:
        adapter.execute([_create(kind, props)])
    assert error.value.code == "fusion_op_failed"
    assert design.timeline.count == 2
    assert all(not coll.inputs for coll in design.rootComponent.cad_collections.values())


@pytest.mark.parametrize(
    "kind,props,collection",
    [
        ("shell", SHELL, "shellFeatures"),
        ("rectangular_pattern", RECTANGULAR, "rectangularPatternFeatures"),
        ("circular_pattern", CIRCULAR, "circularPatternFeatures"),
    ],
)
def test_failed_native_add_stops_batch_and_checkpoint_restores_prior_adds(
    adapter, kind, props, collection
):
    adapter.execute(SEED)
    before = {entity.id for entity in adapter.list_entities()}
    snapshot = adapter.snapshot("before-cadagent")
    root = adapter.wire.design.rootComponent
    root.cad_collections[collection].refuse = True
    with pytest.raises(TeeError) as error:
        adapter.execute(
            [
                _create("extrude", {"sketch": "sk1", "distance": 5}),
                _create(kind, props),
                _create("component", {}, name="must-not-run"),
            ]
        )
    assert error.value.code == "fusion_op_failed" and "Batch op 1 failed" in error.value.message
    assert root.occurrences.count == 0
    assert adapter.wire.design.timeline.count == snapshot["count"] + 1
    adapter.restore(snapshot)
    assert adapter.wire.design.timeline.count == snapshot["count"]
    assert {entity.id for entity in adapter.list_entities()} == before


def test_new_document_does_not_resolve_old_pattern_feature_tokens(adapter):
    adapter.execute(SEED)
    adapter.execute([_create("rectangular_pattern", RECTANGULAR)])
    foreign = set(adapter.wire.namespace["_tee"]["ids"].values())
    design = shim.Design()
    original_find = design.findEntityByToken

    def guarded_find(token):
        assert token not in foreign, "Fusion must never see a token from another document"
        return original_find(token)

    design.findEntityByToken = guarded_find
    adapter.wire.app.activeProduct = design
    adapter.wire.app.activeDocument = shim.Document("New design")
    with pytest.raises(TeeError) as error:
        adapter.execute([_create("circular_pattern", {**CIRCULAR, "features": ["f2"]})])
    assert error.value.code == "fusion_unknown_entity"
    assert adapter.wire.namespace["_tee"]["ids"] == {}
    assert design.timeline.count == 0


@pytest.mark.parametrize(
    "kind,props,collection",
    [
        ("shell", SHELL, "shellFeatures"),
        ("rectangular_pattern", RECTANGULAR, "rectangularPatternFeatures"),
        ("circular_pattern", CIRCULAR, "circularPatternFeatures"),
    ],
)
def test_null_native_input_is_a_short_failure_before_timeline_change(
    adapter, kind, props, collection
):
    adapter.execute(SEED)
    adapter.wire.design.rootComponent.cad_collections[collection].refuse_input = True
    with pytest.raises(TeeError) as error:
        adapter.execute([_create(kind, props)])
    assert error.value.code == "fusion_op_failed" and "input failed" in error.value.message
    assert adapter.wire.design.timeline.count == 2


def test_refused_second_direction_never_creates_partial_one_direction_pattern(adapter):
    adapter.execute(SEED)
    root = adapter.wire.design.rootComponent
    root.cad_collections["rectangularPatternFeatures"].refuse_second_direction = True
    with pytest.raises(TeeError) as error:
        adapter.execute(
            [
                _create(
                    "rectangular_pattern",
                    {**RECTANGULAR, "axis2": "y", "count2": 2, "spacing2": 10},
                )
            ]
        )
    assert error.value.code == "fusion_op_failed"
    assert "second pattern direction" in error.value.message
    assert adapter.wire.design.timeline.count == 2


def test_shell_cannot_remove_every_face_or_hollow_a_surface_body(adapter):
    adapter.execute(SEED)
    with pytest.raises(TeeError, match="leave at least one face"):
        adapter.execute(
            [_create("shell", {**SHELL, "remove_faces": ["+x", "-x", "+y", "-y", "+z", "-z"]})]
        )
    adapter.wire.design.rootComponent.bRepBodies.item(0).isSolid = False
    with pytest.raises(TeeError, match="solid body"):
        adapter.execute([_create("shell", SHELL)])
    assert adapter.wire.design.timeline.count == 2


def test_checkpoint_cannot_delete_timeline_entries_in_another_document(adapter):
    checkpoint = adapter.snapshot("empty-original")
    assert checkpoint["document_id"] == adapter.wire.app.activeDocument.creationId
    adapter.wire.app.activeProduct = shim.Design()
    adapter.wire.app.activeDocument = shim.Document("Different design")
    adapter.execute(SEED)
    before = {entity.id for entity in adapter.list_entities()}
    with pytest.raises(TeeError) as error:
        adapter.restore(checkpoint)
    assert error.value.code == "fusion_checkpoint_document"
    assert adapter.wire.design.timeline.count == 2
    assert {entity.id for entity in adapter.list_entities()} == before


def test_legacy_checkpoint_without_document_id_still_restores_current_document(adapter):
    adapter.execute(SEED)
    checkpoint = adapter.snapshot("seed")
    checkpoint.pop("document_id")
    adapter.execute([_create("rectangular_pattern", RECTANGULAR)])
    assert adapter.wire.design.timeline.count == 3
    adapter.restore(checkpoint)
    assert adapter.wire.design.timeline.count == 2
    assert {entity.id for entity in adapter.list_entities()} == {"sk1", "f1", "b1"}
