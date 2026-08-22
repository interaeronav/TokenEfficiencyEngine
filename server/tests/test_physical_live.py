"""Phase 11 live acceptance against real headless Blender: watertight
tier-2 ops, boolean opening cuts, geometry-node param_set, and the
rigid-body settle lane with determinism. Run with: uv run pytest -m dcc"""

from __future__ import annotations

import pytest

from tee.adapters.blender.adapter import BlenderAdapter
from tee.adapters.blender.wire import BlenderWire
from tee.app import TeeApp
from tee.physical.tools import register_physical_tools

pytestmark = pytest.mark.dcc

NON_MANIFOLD_PROBE = """
import bpy, bmesh
_o = None
for o in bpy.data.objects:
    if o.session_uid == int({eid!r}[1:]):
        _o = o
bm = bmesh.new()
bm.from_mesh(_o.data)
bm.edges.ensure_lookup_table()
result = {{
    "non_manifold": sum(1 for e in bm.edges if not e.is_manifold),
    "verts": len(bm.verts),
    "faces": len(bm.faces),
}}
bm.free()
"""


@pytest.fixture()
def app(blender_bridge, tmp_path):
    adapter = BlenderAdapter(BlenderWire(port=blender_bridge), workdir=str(tmp_path))
    application = TeeApp({"blender": adapter}, project_root=tmp_path, allow_code_exec=True)
    register_physical_tools(application, tmp_path)
    adapter.execute_python(
        "import bpy\n"
        "for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)\n"
        "for c in list(bpy.data.collections): bpy.data.collections.remove(c)\n"
        "if bpy.context.scene.rigidbody_world:\n"
        "    bpy.ops.rigidbody.world_remove()\n"
        "result = {'cleared': True}"
    )
    application.cache("blender").resync(adapter)
    yield application
    application.shutdown()


def _adapter(app):
    return app.adapters["blender"]


def test_wall_with_openings_watertight(app):
    """Acceptance: the fixture wall builds watertight (0 non-manifold)."""
    out = app.registry.call(
        "wall_with_openings",
        {
            "name": "WallA",
            "props": {
                "start": [0, 0], "end": [5, 0], "height": 2.7, "thickness": 0.22,
                "openings": [
                    {"offset": 1.0, "width": 0.9, "sill": 0.0, "head": 2.03},
                    {"offset": 3.0, "width": 1.2, "sill": 0.9, "head": 2.1},
                ],
            },
        },
    )
    eid = out["created"][0]
    probe = _adapter(app).execute_python(NON_MANIFOLD_PROBE.format(eid=eid))["result"]
    assert probe["non_manifold"] == 0, probe
    assert probe["faces"] > 10
    detail = out["details"][eid]
    assert detail["dimensions"][0] == pytest.approx(5.0, abs=0.01)
    assert detail["dimensions"][2] == pytest.approx(2.7, abs=0.01)


def test_slab_and_profile_extrude_watertight(app):
    slab = app.registry.call(
        "slab",
        {"name": "Slab", "props": {
            "polygon": [[0, 0], [5, 0], [5, 4], [0, 4]],
            "holes": [[[2, 1.5], [3, 1.5], [3, 2.5], [2, 2.5]]],
            "thickness": 0.25,
        }},
    )
    probe = _adapter(app).execute_python(
        NON_MANIFOLD_PROBE.format(eid=slab["created"][0])
    )["result"]
    assert probe["non_manifold"] == 0, probe

    prof = app.registry.call(
        "profile_extrude",
        {"name": "Beam", "props": {
            "profile": [[0, 0], [0.3, 0], [0.3, 0.5], [0, 0.5]], "depth": 4.0,
        }},
    )
    probe = _adapter(app).execute_python(
        NON_MANIFOLD_PROBE.format(eid=prof["created"][0])
    )["result"]
    assert probe["non_manifold"] == 0, probe


def test_roof_kinds_and_stairs(app):
    for kind in ("gable", "shed", "flat"):
        out = app.registry.call(
            "roof",
            {"name": f"Roof_{kind}", "props": {
                "kind": kind, "footprint": [0, 0, 6, 4], "pitch_deg": 35,
                "base_z": 2.7,
            }},
        )
        probe = _adapter(app).execute_python(
            NON_MANIFOLD_PROBE.format(eid=out["created"][0])
        )["result"]
        assert probe["non_manifold"] == 0, (kind, probe)
    stairs = app.registry.call(
        "stairs", {"name": "Stairs", "props": {"rise_total": 2.7, "width": 0.95}}
    )
    detail = stairs["details"][stairs["created"][0]]
    assert detail["dimensions"][2] == pytest.approx(2.7, abs=0.01)


def test_hip_roof_names_the_gap(app):
    from tee.kernel.errors import TeeError

    with pytest.raises(TeeError) as err:
        app.registry.call("roof", {"props": {"kind": "hip"}})
    assert "straight-skeleton" in err.value.message


def test_opening_cut_boolean_manifold(app):
    wall = app.registry.call(
        "wall_with_openings",
        {"name": "WallB", "props": {"start": [0, 0], "end": [4, 0],
                                    "height": 2.7, "thickness": 0.2}},
    )
    eid = wall["created"][0]
    cut = app.registry.call(
        "opening_cut",
        {"id": eid, "props": {"center": [2.0, 0.0, 1.0], "size": [0.9, 1.0, 2.0],
                              "apply": True}},
    )
    assert eid in cut["modified"]
    probe = _adapter(app).execute_python(NON_MANIFOLD_PROBE.format(eid=eid))["result"]
    assert probe["non_manifold"] == 0, probe


def test_opening_cut_guards_fast_solver(app):
    from tee.kernel.errors import TeeError

    wall = app.registry.call(
        "wall_with_openings",
        {"name": "WallC", "props": {"start": [0, 0], "end": [2, 0],
                                    "height": 2.0, "thickness": 0.2}},
    )
    with pytest.raises(TeeError) as err:
        app.registry.call(
            "opening_cut",
            {"id": wall["created"][0], "props": {"solver": "FAST"}},
        )
    assert "removed in Blender 5.x" in err.value.message


def test_param_set_via_socket_identifier(app):
    """The 5.2 NodesModifier RNA chokepoint, against a real GN group."""
    adapter = _adapter(app)
    setup_out = adapter.execute_python(
        """
import bpy
mesh = bpy.data.meshes.new("gnhost")
obj = bpy.data.objects.new("GNHost", mesh)
bpy.context.scene.collection.objects.link(obj)
tree = bpy.data.node_groups.new("tee_test_group", "GeometryNodeTree")
iface_in = tree.interface.new_socket("Geometry", in_out="INPUT",
                                     socket_type="NodeSocketGeometry")
iface_size = tree.interface.new_socket("Size", in_out="INPUT",
                                       socket_type="NodeSocketFloat")
iface_out = tree.interface.new_socket("Geometry", in_out="OUTPUT",
                                      socket_type="NodeSocketGeometry")
n_in = tree.nodes.new("NodeGroupInput")
n_out = tree.nodes.new("NodeGroupOutput")
cube = tree.nodes.new("GeometryNodeMeshCube")
tree.links.new(cube.inputs["Size"], n_in.outputs["Size"])
tree.links.new(n_out.inputs["Geometry"], cube.outputs["Mesh"])
md = obj.modifiers.new(name="tee_gn", type="NODES")
md.node_group = tree
result = {"id": "b%d" % obj.session_uid, "socket": iface_size.identifier}
"""
    )
    setup = setup_out["result"]
    app.cache("blender").resync(adapter)
    out = app.registry.call(
        "param_set",
        {"id": setup["id"], "props": {"modifier": "tee_gn",
                                      "values": {setup["socket"]: 2.5}}},
    )
    assert setup["id"] in out["modified"]
    check_out = adapter.execute_python(
        f"""
import bpy
for o in bpy.data.objects:
    if o.session_uid == int({setup["id"]!r}[1:]):
        md = o.modifiers["tee_gn"]
        try:
            v = getattr(md.properties.inputs, {setup["socket"]!r}).value
        except AttributeError:
            v = md[{setup["socket"]!r}]
        result = {{"value": float(v)}}
"""
    )
    assert check_out["result"]["value"] == pytest.approx(2.5)


def test_settle_deterministic_and_adopts(app):
    """Acceptance: settle returns a compact report; two runs agree within
    the measured variance floor; adopt keeps poses."""
    ops = [
        {"op": "create", "kind": "cube", "name": "Ground",
         "props": {"size": 1.0, "scale": [10, 10, 0.1], "location": [0, 0, -0.05]}},
        {"op": "create", "kind": "cube", "name": "BoxA",
         "props": {"size": 0.4, "location": [0, 0, 1.2],
                   "rotation_euler": [0.3, 0.2, 0.1]}},
        {"op": "create", "kind": "cube", "name": "BoxB",
         "props": {"size": 0.4, "location": [0.1, 0.05, 2.0]}},
    ]
    app.run_batch("blender", ops)

    def ids_by_name():
        cache = app.cache("blender")
        return {e.name: e.id for e in cache.entities.values()}

    runs = []
    for _attempt in range(2):
        current = ids_by_name()  # rollback re-creates objects with new uids
        out = app.registry.call(
            "sim_settle",
            {"ids": [current["BoxA"], current["BoxB"]],
             "passive_ids": [current["Ground"]], "adapter": "blender"},
        )
        assert out["settled"] is True, out
        assert "final" in out and "checkpoint" in out
        assert out["seconds"] <= 41
        runs.append(out["final_by_name"])
        # roll back so the second run starts identically (restored objects
        # get new session_uids, so determinism compares by NAME)
        app.rollback("blender", out["checkpoint"])

    floor = 0.0
    for name in ("BoxA", "BoxB"):
        for a, b in zip(runs[0][name], runs[1][name], strict=True):
            floor = max(floor, abs(a - b))
    assert floor < 0.005, f"variance floor {floor} m exceeds 5 mm"

    # ids changed after rollback: rebuild the mapping by name
    by_name = ids_by_name()
    adopted = app.registry.call(
        "sim_settle",
        {"ids": [by_name["BoxA"], by_name["BoxB"]],
         "passive_ids": [by_name["Ground"]], "adopt": True,
         "adapter": "blender"},
    )
    assert adopted["adopted"] is True
    detail = app.cache("blender").get(by_name["BoxA"])
    assert detail.summary["location"][2] < 1.0  # fell from 1.2 onto the ground


def test_cloth_drape_report(app):
    ops = [
        {"op": "create", "kind": "cube", "name": "Table",
         "props": {"size": 1.0, "location": [0, 0, 0.5]}},
        {"op": "create", "kind": "plane", "name": "Cloth",
         "props": {"size": 2.0, "location": [0, 0, 1.3]}},
    ]
    created = app.run_batch("blender", ops)
    table, cloth = created["created"]
    # subdivide so the cloth can drape
    _adapter(app).execute_python(
        f"""
import bpy, bmesh
for o in bpy.data.objects:
    if o.session_uid == int({cloth!r}[1:]):
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=8, use_grid_fill=True)
        bm.to_mesh(o.data)
        bm.free()
result = {{"ok": True}}
"""
    )
    out = app.registry.call(
        "sim_cloth_drape",
        {"id": cloth, "collide_ids": [table], "preset": "cotton",
         "seconds": 1.5, "adapter": "blender"},
    )
    assert out["preset"] == "cotton"
    assert out["frames"] >= 24
    assert "no pass/fail metric" in out["note"]
