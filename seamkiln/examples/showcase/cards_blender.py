"""Title cards, rendered by Blender's own text objects. Runs INSIDE Blender.

blender --background --factory-startup --python cards_blender.py -- WORK W H SAMPLES
"""

import json
import sys
from pathlib import Path

import bpy

ARGS = sys.argv[sys.argv.index("--") + 1 :]
WORK = Path(ARGS[0])
RES = (int(ARGS[1]), int(ARGS[2]))
SAMPLES = int(ARGS[3]) if len(ARGS) > 3 else 32
CARDS = json.loads((WORK / "cards.json").read_text())


def emissive(name, colour, strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*colour, 1.0)
    b.inputs["Emission Color"].default_value = (*colour, 1.0)
    b.inputs["Emission Strength"].default_value = strength
    b.inputs["Roughness"].default_value = 1.0
    return m


def text(body, size, y, material, align="CENTER", x=0.0):
    curve = bpy.data.curves.new("t", type="FONT")
    curve.body = body
    curve.size = size
    curve.align_x = align
    obj = bpy.data.objects.new("t", curve)
    bpy.context.collection.objects.link(obj)
    obj.location = (x, y, 0.01)
    obj.data.materials.append(material)
    return obj


def main():
    for card in CARDS:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x, scene.render.resolution_y = RES
        scene.eevee.taa_render_samples = SAMPLES
        scene.view_settings.view_transform = "Standard"
        world = bpy.data.worlds.new("w")
        scene.world = world
        world.use_nodes = True
        world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.022, 0.026, 1)

        bpy.ops.object.camera_add(location=(0, 0, 10))
        cam = bpy.context.active_object
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = 16.0
        scene.camera = cam
        aspect = RES[1] / RES[0]

        ink = emissive("ink", (0.92, 0.90, 0.86), 1.0)
        dim = emissive("dim", (0.55, 0.56, 0.60), 1.0)
        gold = emissive("gold", (0.95, 0.72, 0.18), 1.0)

        still = card.get("still")
        image_path = WORK / still if still else None
        if image_path is not None and image_path.exists():
            # the still on the right, the words on the left
            img = bpy.data.images.load(str(image_path))
            bpy.ops.mesh.primitive_plane_add(size=1.0, location=(4.1, -0.2, 0.0))
            plane = bpy.context.active_object
            plane.scale = (7.0, 7.0 * (img.size[1] / max(img.size[0], 1)), 1.0)
            m = bpy.data.materials.new("still")
            m.use_nodes = True
            nt = m.node_tree
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = img
            b = nt.nodes["Principled BSDF"]
            nt.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
            b.inputs["Emission Strength"].default_value = 1.0
            b.inputs["Base Color"].default_value = (0, 0, 0, 1)
            plane.data.materials.append(m)
            text(card["title"], 0.62, 2.4, gold, align="LEFT", x=-7.6)
            for k, line in enumerate(card["lines"]):
                text(line, 0.29, 1.3 - k * 0.56, ink if k == 0 else dim, align="LEFT", x=-7.6)
        else:
            text(card["title"], 1.1, 1.6, gold)
            for k, line in enumerate(card["lines"]):
                text(line, 0.42, 0.3 - k * 0.75, ink if k == 0 else dim)
        _ = aspect
        scene.render.filepath = str(WORK / f"card_{card['name']}.png")
        bpy.ops.render.render(write_still=True)
        print("CARD", card["name"], flush=True)


main()
