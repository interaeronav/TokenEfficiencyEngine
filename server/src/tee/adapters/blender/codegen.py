"""Programs executed inside Blender over the wire (principle P2).

One generic batch interpreter travels with each request; the typed operations
travel as JSON data. N operations therefore cost exactly one round-trip, and
the Blender-side code is static and testable. Entity ids are
``b<session_uid>`` - stable for the life of a Blender session, surviving
renames and undo (docs/research/09).

All construction prefers ``bpy.data`` / ``bmesh`` over ``bpy.ops`` so no
operator context is needed (bpy.ops poll failures are the classic opaque
bridge error); the only operator used is undo_push in GUI sessions.
"""

from __future__ import annotations

import json
from typing import Any

PRELUDE = """
import bpy
import bmesh
import math

def _uid(o):
    return "b%d" % o.session_uid

def _find(eid):
    try:
        want = int(str(eid)[1:])
    except ValueError:
        return None
    for o in bpy.data.objects:
        if o.session_uid == want:
            return o
    return None

def _ent(o):
    d = {"id": _uid(o), "name": o.name, "kind": o.type.lower() if o.type else "empty"}
    if o.parent is not None:
        d["parent"] = _uid(o.parent)
    d["location"] = [round(float(v), 4) for v in o.location]
    d["dimensions"] = [round(float(v), 4) for v in o.dimensions]
    if o.type == "MESH" and o.data is not None:
        d["verts"] = len(o.data.vertices)
        d["polys"] = len(o.data.polygons)
        if o.data.materials:
            d["materials"] = [m.name for m in o.data.materials if m]
    if o.type == "LIGHT" and o.data is not None:
        d["light_type"] = o.data.type.lower()
        d["energy"] = round(float(o.data.energy), 2)
    return d

def _link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj

def _mesh_prim(kind, name, params):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    size = float(params.get("size", 2.0))
    radius = float(params.get("radius", 1.0))
    segments = int(params.get("segments", 32))
    if kind == "cube":
        bmesh.ops.create_cube(bm, size=size)
    elif kind == "plane":
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size / 2.0)
    elif kind == "uv_sphere":
        bmesh.ops.create_uvsphere(
            bm, u_segments=segments, v_segments=max(3, segments // 2), radius=radius)
    elif kind == "ico_sphere":
        bmesh.ops.create_icosphere(
            bm, subdivisions=int(params.get("subdivisions", 2)), radius=radius)
    elif kind == "cylinder":
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=segments, radius1=radius, radius2=radius,
            depth=float(params.get("depth", 2.0)))
    elif kind == "cone":
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=segments, radius1=radius,
            radius2=float(params.get("radius_top", 0.0)),
            depth=float(params.get("depth", 2.0)))
    elif kind == "torus":
        _torus(bm, radius, float(params.get("minor_radius", 0.25)),
               segments, int(params.get("minor_segments", 12)))
    elif kind == "monkey":
        bmesh.ops.create_monkey(bm)
    else:
        bm.free()
        bpy.data.meshes.remove(mesh)
        raise ValueError("unknown mesh kind: %s" % kind)
    bm.to_mesh(mesh)
    bm.free()
    return _link(bpy.data.objects.new(name, mesh))

def _torus(bm, major_r, minor_r, major_seg, minor_seg):
    verts = []
    for i in range(major_seg):
        a = 2.0 * math.pi * i / major_seg
        for j in range(minor_seg):
            b = 2.0 * math.pi * j / minor_seg
            x = (major_r + minor_r * math.cos(b)) * math.cos(a)
            y = (major_r + minor_r * math.cos(b)) * math.sin(a)
            z = minor_r * math.sin(b)
            verts.append(bm.verts.new((x, y, z)))
    for i in range(major_seg):
        for j in range(minor_seg):
            v1 = verts[i * minor_seg + j]
            v2 = verts[i * minor_seg + (j + 1) % minor_seg]
            v3 = verts[((i + 1) % major_seg) * minor_seg + (j + 1) % minor_seg]
            v4 = verts[((i + 1) % major_seg) * minor_seg + j]
            bm.faces.new((v1, v2, v3, v4))

def _create(op):
    kind = op.get("kind", "cube")
    name = op.get("name") or kind.title()
    params = dict(op.get("props") or {})
    if kind in ("cube", "plane", "uv_sphere", "ico_sphere", "cylinder",
                "cone", "torus", "monkey"):
        obj = _mesh_prim(kind, name, params)
    elif kind == "empty":
        obj = _link(bpy.data.objects.new(name, None))
    elif kind == "light":
        light = bpy.data.lights.new(name, str(params.get("light_type", "POINT")).upper())
        if "energy" in params:
            light.energy = float(params["energy"])
        if "color" in params:
            light.color = params["color"]
        obj = _link(bpy.data.objects.new(name, light))
    elif kind == "camera":
        obj = _link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    else:
        raise ValueError("unknown kind: %s" % kind)
    _apply_props(obj, params)
    return obj

def _assign_material(obj, params):
    if obj.type != "MESH":
        raise ValueError("assign_material target %r is not a mesh" % obj.name)
    name = str(params.get("material") or obj.name + "_mat")
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        out = next((n for n in mat.node_tree.nodes if n.type == "OUTPUT_MATERIAL"), None)
        if out is not None:
            mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    # 4.0+ socket names (docs/research/02): Base Color, Metallic, Roughness,
    # Emission Color, Emission Strength
    if "base_color" in params:
        rgb = list(params["base_color"])
        bsdf.inputs["Base Color"].default_value = (rgb + [1.0])[:4]
    for key, sock in (("metallic", "Metallic"), ("roughness", "Roughness"),
                      ("emission_strength", "Emission Strength")):
        if key in params:
            bsdf.inputs[sock].default_value = float(params[key])
    if "emission_color" in params:
        rgb = list(params["emission_color"])
        bsdf.inputs["Emission Color"].default_value = (rgb + [1.0])[:4]
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

_SETTABLE = ("location", "rotation_euler", "scale", "hide_viewport", "hide_render")

def _apply_props(obj, props):
    for key in _SETTABLE:
        if key in props:
            setattr(obj, key, props[key])
    if "name" in props:
        obj.name = str(props["name"])
    if "parent" in props:
        ref = props["parent"]
        obj.parent = _find(ref) if ref else None
    if "dimensions" in props:
        # obj.dimensions writes scale from the bound_box, which is stale for
        # meshes built this same batch - derive scale from real vertex extents
        target = props["dimensions"]
        verts = getattr(obj.data, "vertices", None)
        if verts is not None and len(verts):
            for axis in range(min(3, len(target))):
                lo = min(v.co[axis] for v in verts)
                hi = max(v.co[axis] for v in verts)
                if hi - lo > 1e-9:
                    obj.scale[axis] = float(target[axis]) / (hi - lo)
        else:
            obj.dimensions = target
"""

BATCH_INTERPRETER = """
_created, _modified, _deleted = [], [], []
_touched = {}

for _i, _op in enumerate(_OPS):
    _kind = _op.get("op")
    if _kind == "create":
        _obj = _create(_op)
        _eid = _uid(_obj)
        _created.append(_eid)
        _touched[_eid] = _obj
    elif _kind == "set":
        _obj = _find(_op.get("id"))
        if _obj is None:
            raise ValueError("no entity %r (batch index %d)" % (_op.get("id"), _i))
        _apply_props(_obj, _op.get("props") or {})
        _eid = _uid(_obj)
        if _eid not in _created and _eid not in _modified:
            _modified.append(_eid)
        _touched[_eid] = _obj
    elif _kind == "assign_material":
        _obj = _find(_op.get("id"))
        if _obj is None:
            raise ValueError("no entity %r (batch index %d)" % (_op.get("id"), _i))
        _assign_material(_obj, _op.get("props") or {})
        _eid = _uid(_obj)
        if _eid not in _created and _eid not in _modified:
            _modified.append(_eid)
        _touched[_eid] = _obj
    elif _kind == "delete":
        _obj = _find(_op.get("id"))
        if _obj is None:
            raise ValueError("no entity %r (batch index %d)" % (_op.get("id"), _i))
        _eid = _uid(_obj)
        bpy.data.objects.remove(_obj, do_unlink=True)
        _deleted.append(_eid)
        _touched.pop(_eid, None)
        if _eid in _created:
            _created.remove(_eid)
        if _eid in _modified:
            _modified.remove(_eid)
    else:
        raise ValueError("unknown op %r (batch index %d)" % (_kind, _i))

# details are read AFTER one depsgraph update - dimensions/bounds of objects
# built or scaled this batch are stale until then
bpy.context.view_layer.update()
if not bpy.app.background:
    bpy.ops.ed.undo_push(message=_UNDO_LABEL)

_details = {}
for _eid, _obj in _touched.items():
    _details[_eid] = _ent(_obj)

result = {
    "created": _created,
    "modified": _modified,
    "deleted": _deleted,
    "details": _details,
    "entities": list(_details.values()),
}
"""

LIST_ENTITIES = """
result = {"entities": [_ent(o) for o in bpy.data.objects]}
"""

INFO = """
import bpy
result = {
    "version": list(bpy.app.version),
    "version_string": bpy.app.version_string,
    "background": bpy.app.background,
    "filepath": bpy.data.filepath,
    "objects": len(bpy.data.objects),
}
"""


def program_info() -> str:
    return INFO


def program_list_entities() -> str:
    return PRELUDE + LIST_ENTITIES


def program_batch(ops: list[dict[str, Any]], undo_label: str) -> str:
    # Ops are embedded as a JSON string parsed at runtime: inlining
    # json.dumps output as Python source would turn true/false/null into
    # NameErrors (json and Python literals differ).
    header = (
        "import json as _tee_json\n"
        f"_OPS = _tee_json.loads({json.dumps(ops)!r})\n"
        f"_UNDO_LABEL = {undo_label!r}\n"
    )
    return PRELUDE + header + BATCH_INTERPRETER


def program_snapshot(path: str) -> str:
    return (
        "import bpy\n"
        f"bpy.ops.wm.save_as_mainfile(filepath={json.dumps(path)}, copy=True, compress=True)\n"
        f"result = {{'path': {json.dumps(path)}}}\n"
    )


def program_restore(path: str) -> str:
    return (
        "import bpy\n"
        f"bpy.ops.wm.open_mainfile(filepath={json.dumps(path)})\n"
        "result = {'restored': True, 'objects': len(bpy.data.objects)}\n"
    )


def program_capture(path: str, width: int, height: int, quality: int, samples: int) -> str:
    """Render a small JPEG, leaving the scene EXACTLY as found: render/cycles
    settings, scene.camera, and any temp camera are all restored/removed."""
    return f"""
import bpy
scene = bpy.context.scene
render = scene.render
prev = (render.engine, render.resolution_x, render.resolution_y,
        render.resolution_percentage, render.filepath,
        render.image_settings.file_format, render.image_settings.quality,
        scene.cycles.samples, scene.cycles.use_denoising, scene.camera)
temp_cam = None
try:
    render.engine = 'CYCLES'
    scene.cycles.samples = {samples}
    scene.cycles.use_denoising = False
    render.resolution_x = {width}
    render.resolution_y = {height}
    render.resolution_percentage = 100
    render.filepath = {json.dumps(path)}
    render.image_settings.file_format = 'JPEG'
    render.image_settings.quality = {quality}
    if not any(o.type == 'CAMERA' for o in bpy.data.objects):
        cam_data = bpy.data.cameras.new('TEE_TempCamera')
        temp_cam = bpy.data.objects.new('TEE_TempCamera', cam_data)
        bpy.context.scene.collection.objects.link(temp_cam)
        scene.camera = temp_cam
        temp_cam.location = (8, -8, 6)
        temp_cam.rotation_euler = (1.1, 0.0, 0.785)
    elif scene.camera is None:
        scene.camera = next(o for o in bpy.data.objects if o.type == 'CAMERA')
    bpy.ops.render.render(write_still=True)
finally:
    (render.engine, render.resolution_x, render.resolution_y,
     render.resolution_percentage, render.filepath,
     render.image_settings.file_format, render.image_settings.quality,
     scene.cycles.samples, scene.cycles.use_denoising, prev_camera) = prev
    if temp_cam is not None:
        cam_data = temp_cam.data
        bpy.data.objects.remove(temp_cam, do_unlink=True)
        bpy.data.cameras.remove(cam_data)
        scene.camera = prev_camera
    else:
        scene.camera = prev_camera
result = {{'path': {json.dumps(path)}}}
"""
