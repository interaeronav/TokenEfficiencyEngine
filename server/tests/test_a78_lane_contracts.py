"""A78: ignored properties, guessed IDs and malformed batches must not look successful."""

from __future__ import annotations

import copy
import json
import sys
from types import SimpleNamespace

import pytest
from fixtures_fusion import FakeFusionWire
from test_blender_bad_op import QuietWire

from tee.adapters.blender import codegen as blender_code
from tee.adapters.blender.adapter import BlenderAdapter
from tee.adapters.fusion.adapter import FusionAdapter
from tee.adapters.fusion.guidance import PLATE
from tee.app import TeeApp
from tee.kernel.errors import TeeError


@pytest.mark.parametrize(
    "op",
    [
        {"op": "set", "id": "b1", "props": {"rotation": [0, 0, 90]}},
        {"op": "create", "kind": "cube", "props": {"location": "1 2 3"}},
        {"op": "create", "kind": "cube", "props": {"dimensions": [1, 2]}},
        {"op": "set", "props": {"location": [1, 2, 3]}},
        {"op": "create", "kind": "cube", "props": {"radius": 4}},
        {"op": "create", "kind": "cube", "props": {"size": float("inf")}},
        {"op": "create", "kind": "camera", "props": {"lens": -1}},
        {"op": "create", "kind": "camera", "props": {"active": "true"}},
        {"op": "create", "kind": "camera", "props": {"location": [1, 2, 3], "target": [1, 2, 3]}},
        {
            "op": "create",
            "kind": "camera",
            "props": {"target": [1, 2, 3], "rotation_euler": [0, 0, 0]},
        },
        {"op": "assign_material", "id": "b1", "props": {"base_color": [2, 0, 0]}},
        {"op": "assign_material", "id": "b1", "props": {"roughness": "polished"}},
    ],
)
def test_blender_bad_properties_refuse_before_any_wire_call(op):
    wire = QuietWire()
    adapter = BlenderAdapter(wire=wire)
    with pytest.raises(TeeError) as error:
        adapter.execute([{"op": "create", "kind": "cube", "name": "must_not_exist"}, op])
    assert "batch[1]" in error.value.message
    assert wire.executed == []


def test_blender_preflight_does_not_checkpoint_or_restore(tmp_path):
    wire = QuietWire()
    app = TeeApp(
        {"blender": BlenderAdapter(wire=wire, workdir=str(tmp_path))}, project_root=tmp_path
    )
    try:
        with pytest.raises(TeeError):
            app.run_batch("blender", [{"op": "set", "id": "b1", "props": {"focal_length": 85}}])
        assert wire.executed == []
        assert not list(tmp_path.glob("*.blend"))
    finally:
        app.shutdown()


def test_typed_camera_lens_and_active_are_applied_and_read_back(monkeypatch):
    """Execute production Blender program functions, faking only the app objects."""
    camera = SimpleNamespace(
        type="CAMERA",
        data=SimpleNamespace(lens=50.0),
        parent=None,
        session_uid=21,
        name="Camera",
        location=[0, 0, 0],
        dimensions=[0, 0, 0],
        rotation_euler=[0, 0, 0],
    )
    scene = SimpleNamespace(camera=None)
    monkeypatch.setitem(sys.modules, "bpy", SimpleNamespace(context=SimpleNamespace(scene=scene)))
    monkeypatch.setitem(sys.modules, "bmesh", SimpleNamespace())
    env = {}
    exec(blender_code.PRELUDE, env)
    env["_apply_props"](camera, {"lens": 71, "active": True})
    row = env["_ent"](camera)
    assert row["lens_mm"] == 71 and row["active"] is True
    assert scene.camera is camera
    env["_apply_props"](camera, {"active": False})
    assert scene.camera is None
    mesh = SimpleNamespace(type="MESH", location=[0, 0, 0])
    with pytest.raises(ValueError, match="only to a camera"):
        env["_apply_props"](mesh, {"lens": 71, "location": [4, 5, 6]})
    assert mesh.location == [0, 0, 0]


@pytest.mark.parametrize("initial_tree", [True, False])
def test_material_nodes_follow_actual_availability_not_version(monkeypatch, initial_tree):
    class Material:
        def __init__(self):
            self._nodes = None
            self.enabled = 0
            if initial_tree:
                self.use_nodes = True
                self.enabled = 0

        @property
        def node_tree(self):
            return self._nodes

        @property
        def use_nodes(self):
            return self._nodes is not None

        @use_nodes.setter
        def use_nodes(self, value):
            self.enabled += 1
            bsdf = SimpleNamespace(
                type="BSDF_PRINCIPLED", inputs={"Roughness": SimpleNamespace(default_value=0)}
            )
            self._nodes = SimpleNamespace(nodes=[bsdf])

    material = Material()
    bpy = SimpleNamespace(
        app=SimpleNamespace(version=(5, 2, 0)),
        data=SimpleNamespace(materials=SimpleNamespace(get=lambda _: material)),
    )
    monkeypatch.setitem(sys.modules, "bpy", bpy)
    monkeypatch.setitem(sys.modules, "bmesh", SimpleNamespace())
    env = {}
    exec(blender_code.PRELUDE, env)
    obj = SimpleNamespace(type="MESH", name="Panel", data=SimpleNamespace(materials=[]))
    env["_assign_material"](obj, {"material": "Carbon", "roughness": 0.2})
    assert material.enabled == (0 if initial_tree else 1)
    assert obj.data.materials == [material]
    assert material.node_tree.nodes[0].inputs["Roughness"].default_value == 0.2


def test_fusion_aliases_bind_the_new_sketch_in_a_nonempty_design():
    adapter = FusionAdapter(FakeFusionWire())
    adapter.execute(
        [{"op": "create", "kind": "sketch", "name": "existing", "props": {"rects": [[0, 0, 2, 3]]}}]
    )
    ops = copy.deepcopy(PLATE)
    ops += [
        {"op": "set", "id": "@plate.feature", "props": {"expression": "12 mm"}},
        {"op": "set", "id": "@plate", "props": {"name": "New plate"}},
    ]
    before = copy.deepcopy(ops)
    result = adapter.execute(ops)
    assert ops == before
    bodies = [e for e in adapter.list_entities() if e.kind == "body"]
    assert len(bodies) == 1
    assert bodies[0].name == "New plate"
    assert bodies[0].summary["bbox_mm"] == [120, 80, 12]
    assert bodies[0].summary["volume_mm3"] == pytest.approx(115200)
    assert "@" not in json.dumps(result.to_payload())
    assert [e.name for e in adapter.list_entities() if e.kind == "sketch"] == [
        "existing",
        "Plate profile",
    ]


@pytest.mark.parametrize(
    "ops",
    [
        [{"op": "create", "kind": "extrude", "props": {"sketch": "@missing", "distance": 10}}],
        [PLATE[0], PLATE[0]],
        [{"op": "create", "kind": "sketch", "as": "@wrong", "props": {"rects": [[0, 0, 2, 3]]}}],
        [{"op": "set", "id": "b1", "as": "wrong", "props": {"name": "x"}}],
        [{"op": "create", "kind": "sketch", "props": {"rects": [[0, 0, 2, 3]], "offset": 5}}],
        [{"op": "create", "kind": "loft", "props": {"sections": ["sk1", "sk2"]}}],
        [{"op": "create", "kind": "extrude", "props": {"sketch": "sk1", "distance": float("nan")}}],
    ],
)
def test_fusion_invalid_aliases_and_ignored_properties_never_reach_wire(ops):
    wire = FakeFusionWire()
    adapter = FusionAdapter(wire)
    before = len(wire.executed)
    with pytest.raises(TeeError):
        adapter.execute(copy.deepcopy(ops))
    assert len(wire.executed) == before
    assert wire.app.activeProduct.rootComponent.bRepBodies.count == 0


def test_aliases_are_request_local_and_subentity_addresses_resolve():
    adapter = FusionAdapter(FakeFusionWire())
    adapter.execute(
        [
            PLATE[0],
            {
                "op": "create",
                "kind": "dimension",
                "as": "width",
                "props": {
                    "of": ["@profile/r0.bl", "@profile/r0.br"],
                    "type": "distance",
                    "expression": "130 mm",
                },
            },
            PLATE[1],
        ]
    )
    body = next(e for e in adapter.list_entities() if e.kind == "body")
    assert body.summary["bbox_mm"] == [130, 80, 10]
    with pytest.raises(TeeError, match="not defined by an earlier create"):
        adapter.execute([{"op": "set", "id": "@plate", "props": {"name": "stale alias"}}])
    assert body.summary["bbox_mm"] == [130, 80, 10]


@pytest.mark.parametrize("adapter", [BlenderAdapter(wire=object()), FusionAdapter(wire=object())])
def test_guides_are_compact_detached_and_offline(adapter):
    index = adapter.guide()
    assert len(json.dumps(index)) < 1200
    for topic in index["topics"]:
        card = adapter.guide(topic)
        # Full lessons are opt-in; the default index and original cards retain
        # their budgets. A complete advanced workflow still has a hard ceiling.
        advanced = topic in (
            "cadagent_enclosure",
            "cadagent_flange",
            "cadagent_joint",
            "cadagent_f1_wing",
            "cadagent_f1_brake",
            "cadagent_f1_wishbone",
        )
        assert len(json.dumps(card)) < (18000 if advanced else 2600)
        if "ops" in card:
            adapter.preflight(card["ops"])
            card["ops"].clear()
            assert adapter.guide(topic)["ops"]
    with pytest.raises(TeeError, match="guide topic"):
        adapter.guide("imaginary")


@pytest.mark.parametrize("topic", ["sketch_extrude", "parameters", "hole_fillet"])
def test_fusion_guide_workflows_execute_on_the_shim(topic):
    adapter = FusionAdapter(FakeFusionWire())
    out = adapter.execute(adapter.guide(topic)["ops"])
    assert any(row.get("kind") == "body" for row in out.details.values())
    body = next(e for e in adapter.list_entities() if e.kind == "body")
    assert body.summary["solid"]
    assert body.summary["volume_mm3"] > 0
    expected = [140, 80, 10] if topic == "parameters" else [120, 80, 10]
    assert body.summary["bbox_mm"] == expected


def test_fusion_feature_alias_drives_thickness_and_survives_parameter_update():
    adapter = FusionAdapter(FakeFusionWire())
    adapter.execute(adapter.guide("parameters")["ops"])
    adapter.execute([{"op": "param_set", "name": "A78_thickness", "expression": "14 mm"}])
    body = next(e for e in adapter.list_entities() if e.kind == "body")
    assert body.summary["bbox_mm"] == [140, 80, 14]
    assert body.summary["volume_mm3"] == pytest.approx(156800)


def test_fusion_alias_delete_reports_actual_id_not_the_alias():
    adapter = FusionAdapter(FakeFusionWire())
    out = adapter.execute(
        [
            {"op": "create", "kind": "component", "name": "temporary", "as": "tmp"},
            {"op": "delete", "id": "@tmp"},
        ]
    )
    assert out.deleted == ["c1"]
    assert not adapter.list_entities()


def test_fusion_named_new_body_does_not_rename_existing_cut_target():
    adapter = FusionAdapter(FakeFusionWire())
    adapter.execute(PLATE)
    adapter.execute(
        [
            {"op": "create", "kind": "sketch", "as": "bore", "props": {"circles": [[60, 40, 3]]}},
            {
                "op": "create",
                "kind": "extrude",
                "name": "Cut feature",
                "props": {"sketch": "@bore", "distance": 10, "operation": "cut"},
            },
        ]
    )
    body = next(e for e in adapter.list_entities() if e.kind == "body")
    assert body.name == "Plate"
    assert body.summary["volume_mm3"] < 96000


def test_fusion_parameter_refusal_names_the_actual_top_level_fields():
    wire = FakeFusionWire()
    adapter = FusionAdapter(wire)
    with pytest.raises(TeeError) as error:
        adapter.preflight([{"op": "param_set", "id": "param:depth", "props": {"value": "12 mm"}}])
    assert "top-level name and expression" in error.value.message
    assert '"name":"width","expression":"120 mm"' in error.value.fix
    assert "component" not in error.value.fix
    assert wire.executed == []


@pytest.mark.parametrize(
    "lane,ops",
    [
        ("blender", [{"op": "create", "kind": "cube", "name": {"not": "a string"}}]),
        ("blender", [{"op": "create", "kind": "cube", "name": ""}]),
        (
            "fusion",
            [{"op": "create", "kind": "extrude", "props": {"sketch": ["sk1"], "distance": 10}}],
        ),
        (
            "fusion",
            [{"op": "create", "kind": "fillet", "props": {"body": {"id": "b1"}, "radius": 1}}],
        ),
        (
            "fusion",
            [{"op": "create", "kind": "extrude", "props": {"sketch": "bad name", "distance": 10}}],
        ),
        (
            "fusion",
            [{"op": "param_set", "name": "thickness", "expression": {"not": "an expression"}}],
        ),
        ("fusion", [{"op": "param_set", "name": ["thickness"], "expression": "12 mm"}]),
        ("fusion", [{"op": "create", "kind": "component", "name": 17}]),
    ],
)
def test_common_model_type_mistakes_are_compact_preflight_errors(lane, ops, tmp_path):
    wire = QuietWire() if lane == "blender" else FakeFusionWire()
    adapter = (
        BlenderAdapter(wire=wire, workdir=str(tmp_path))
        if lane == "blender"
        else FusionAdapter(wire)
    )
    app = TeeApp({lane: adapter}, project_root=tmp_path)
    try:
        with pytest.raises(TeeError) as error:
            app.run_batch(lane, ops)
        assert error.value.code == "bad_op"
        assert "string" in error.value.message
        assert wire.executed == []
    finally:
        app.shutdown()
