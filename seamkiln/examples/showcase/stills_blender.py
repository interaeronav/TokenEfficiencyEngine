"""Two stills: the flat pattern, and the jacket arranged on the figure before
the solver has touched it. Runs INSIDE Blender.

    blender --background --factory-startup --python stills_blender.py -- WORK W H SAMPLES
"""

import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1 :]
WORK = Path(ARGS[0])
RES = (int(ARGS[1]), int(ARGS[2]))
SAMPLES = int(ARGS[3]) if len(ARGS) > 3 else 48


def to_blender(p):
    out = np.empty_like(p)
    out[:, 0], out[:, 1], out[:, 2] = p[:, 0], p[:, 2], p[:, 1]
    return out


def emissive(name, colour, strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*colour, 1.0)
    b.inputs["Emission Color"].default_value = (*colour, 1.0)
    b.inputs["Emission Strength"].default_value = strength
    return m


def fresh(world_colour):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = RES
    scene.eevee.taa_render_samples = SAMPLES
    world = bpy.data.worlds.new("w")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (*world_colour, 1)
    return scene


def pattern_still():
    """The panels laid side by side as outlines, orthographic, top down."""
    scene = fresh((0.02, 0.022, 0.026))
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_y = int(RES[0] * 0.42)  # a wide strip: five pieces side by side
    data = json.loads((WORK / "pattern.json").read_text())
    ink = emissive("ink", (0.92, 0.90, 0.86))
    zipc = emissive("zip", (0.95, 0.72, 0.18))
    x_cursor = 0.0
    total_w = 0.0
    boxes = []
    for panel in data["panels"]:
        pts = np.asarray(panel["outline"], dtype=np.float64) / 1000.0
        w = pts[:, 0].max() - pts[:, 0].min()
        boxes.append((panel, pts, w))
        total_w += w + 0.06
    x_cursor = -total_w / 2.0
    for panel, pts, w in boxes:
        shift = np.array([x_cursor - pts[:, 0].min(), -(pts[:, 1].max() + pts[:, 1].min()) / 2.0])
        loop = pts + shift
        curve = bpy.data.curves.new(panel["id"], type="CURVE")
        curve.dimensions = "2D"
        curve.bevel_depth = 0.004
        spline = curve.splines.new("POLY")
        spline.points.add(len(loop) - 1)
        for k, (x, y) in enumerate(loop):
            spline.points[k].co = (x, y, 0.0, 1.0)
        spline.use_cyclic_u = True
        obj = bpy.data.objects.new(panel["id"], curve)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(zipc if panel["id"].startswith("FRONT") else ink)
        label = bpy.data.curves.new("l", type="FONT")
        label.body = panel["id"].replace("_", " ").lower()
        label.size = 0.05
        label.align_x = "CENTER"
        t = bpy.data.objects.new("l", label)
        bpy.context.collection.objects.link(t)
        t.location = (x_cursor + w / 2.0, -(pts[:, 1].max() - pts[:, 1].min()) / 2.0 - 0.09, 0)
        t.data.materials.append(ink)
        x_cursor += w + 0.06
    bpy.ops.object.camera_add(location=(0, 0, 5))
    cam = bpy.context.active_object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max(total_w * 1.08, 1.2)
    scene.camera = cam
    scene.render.filepath = str(WORK / "pattern.png")
    bpy.ops.render.render(write_still=True)
    print("STILL pattern", flush=True)


def arranged_still():
    """The wrapped, undressed jacket on the figure: what the solver starts from."""
    scene = fresh((0.09, 0.10, 0.125))
    scene.view_settings.view_transform = "AgX"
    pts = np.load(WORK / "arranged.npy").astype(np.float64)
    tri = np.load(WORK / "arranged_tri.npy")
    me = bpy.data.meshes.new("jacket")
    me.from_pydata([Vector(v) for v in to_blender(pts)], [], tri.tolist())
    me.update()
    obj = bpy.data.objects.new("jacket", me)
    bpy.context.collection.objects.link(obj)
    cloth = bpy.data.materials.new("cloth")
    cloth.use_nodes = True
    b = cloth.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.55, 0.32, 0.14, 1.0)
    b.inputs["Roughness"].default_value = 0.85
    obj.data.materials.append(cloth)
    wire = obj.modifiers.new("wire", "WIREFRAME")
    wire.thickness = 0.0025
    wire.use_replace = False
    for poly in me.polygons:
        poly.use_smooth = True

    before = set(bpy.data.objects)
    bpy.ops.wm.ply_import(filepath=str(WORK / "body.ply"))
    body = next(iter(set(bpy.data.objects) - before))
    body.rotation_euler = (math.radians(90), 0, 0)
    skin = bpy.data.materials.new("figure")
    skin.use_nodes = True
    sb = skin.node_tree.nodes["Principled BSDF"]
    sb.inputs["Base Color"].default_value = (0.18, 0.19, 0.22, 1.0)
    sb.inputs["Roughness"].default_value = 0.5
    body.data.materials.append(skin)
    for poly in body.data.polygons:
        poly.use_smooth = True
    body.modifiers.new("smooth", "SUBSURF").levels = 1

    # the figure faces +Y; a sun tilted by a NEGATIVE X angle travels toward
    # -Y and so lights the faces that look toward +Y - the front
    bpy.ops.object.light_add(type="SUN")
    key = bpy.context.active_object
    key.data.energy = 3.0
    key.rotation_euler = (math.radians(-55), 0, math.radians(35))
    bpy.ops.object.light_add(type="AREA", location=(2.0, 4.5, 2.6))
    fill = bpy.context.active_object
    fill.data.energy = 400.0
    fill.data.size = 5.0
    fill.rotation_euler = (math.radians(-62), 0, math.radians(20))

    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    cam.data.lens = 55.0
    # the figure faces +Y here (seamkiln +Z), so the camera stands in front
    cam.location = (1.9, 3.4, 1.35)
    look = Vector((0.0, 0.0, 1.05))
    cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.filepath = str(WORK / "arranged.png")
    bpy.ops.render.render(write_still=True)
    print("STILL arranged", flush=True)


pattern_still()
arranged_still()
