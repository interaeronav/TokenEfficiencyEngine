"""Look at the drape. Renders through Blender, headlessly.

A drape can satisfy every number - seams closed, nothing inside the body -
and still be wrong in a way only an eye catches: a panel inside out, a
sleeve on the wrong arm, a garment hanging beside the body rather than on
it. So this exists from P2 rather than P6, and it is used at every step.

Blender is the renderer because TEE already drives it headlessly and it
boots in about half a second. Nothing here is on the solver's path; if
Blender is absent, it refuses and the numbers still stand.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import trimesh

_RENDER = r"""
import bpy, json, sys, math
from mathutils import Vector

args = json.loads(sys.argv[sys.argv.index("--") + 1])
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
# The engine enum drifts between versions: 4.2 renamed EEVEE to
# BLENDER_EEVEE_NEXT, and 5.x renamed it back. Ask the build what it has
# rather than hardcoding a name that was right for one release.
available = {
    item.identifier
    for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
}
for candidate in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH"):
    if candidate in available:
        scene.render.engine = candidate
        break
scene.render.resolution_x, scene.render.resolution_y = args["width"], args["height"]
scene.render.film_transparent = False
world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[1].default_value = 1.6

def load(path, colour, alpha=1.0):
    before = set(bpy.data.objects)
    if path.endswith(".ply"):
        # PLY, not OBJ, when the mesh carries per-vertex colour: OBJ has no
        # portable vertex-colour channel, so a denim wash exported through it
        # arrives as flat cloth and the finish silently does nothing.
        bpy.ops.wm.ply_import(filepath=path, forward_axis="NEGATIVE_Z", up_axis="Y")
    else:
        bpy.ops.wm.obj_import(filepath=path, forward_axis="NEGATIVE_Z", up_axis="Y")
    objects = [o for o in bpy.data.objects if o not in before]
    material = bpy.data.materials.new("m"); material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
    vertex_colour = next(
        (o for o in objects if o.data.color_attributes), None
    )
    if vertex_colour is not None:
        node = material.node_tree.nodes.new("ShaderNodeVertexColor")
        node.layer_name = vertex_colour.data.color_attributes[0].name
        material.node_tree.links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.75
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        material.blend_method = "BLEND"
    for obj in objects:
        obj.data.materials.append(material)
        for polygon in obj.data.polygons:
            polygon.use_smooth = False
    return objects

everything = []
for spec in args["meshes"]:
    everything += load(spec["path"], spec["colour"], spec.get("alpha", 1.0))

corners = [o.matrix_world @ Vector(c) for o in everything for c in o.bound_box]
lowest = min(c.z for c in corners)
highest = max(c.z for c in corners)
# frame on the WIDEST axis, not just height: three specimens side by side are
# wide and short, and framing on height alone put the camera inside them
wide = max(
    max(c.x for c in corners) - min(c.x for c in corners),
    max(c.y for c in corners) - min(c.y for c in corners),
)
centre = Vector((
    (max(c.x for c in corners) + min(c.x for c in corners)) / 2,
    (max(c.y for c in corners) + min(c.y for c in corners)) / 2,
    (lowest + highest) / 2,
))
span = max(highest - lowest, wide, 0.5)

light_data = bpy.data.lights.new("key", type="AREA"); light_data.energy = 400
light_data.size = 3.0
key = bpy.data.objects.new("key", light_data); scene.collection.objects.link(key)
key.location = (2.5, -3.0, highest + 1.0)
key.rotation_euler = (math.radians(55), 0.0, math.radians(40))

fill_data = bpy.data.lights.new("fill", type="AREA"); fill_data.energy = 120
fill_data.size = 4.0
fill = bpy.data.objects.new("fill", fill_data); scene.collection.objects.link(fill)
fill.location = (-3.0, -2.0, highest * 0.6)
fill.rotation_euler = (math.radians(75), 0.0, math.radians(-55))

camera_data = bpy.data.cameras.new("cam"); camera_data.type = "ORTHO"
camera_data.ortho_scale = span * 1.15
camera = bpy.data.objects.new("cam", camera_data)
scene.collection.objects.link(camera); scene.camera = camera

for name, (angle, elevation) in args["views"].items():
    radians = math.radians(angle)
    distance = span * 2.5
    camera.location = (
        centre.x + distance * math.sin(radians),
        centre.y - distance * math.cos(radians),
        centre.z + distance * math.sin(math.radians(elevation)),
    )
    direction = centre - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = args["out"].replace("VIEW", name)
    bpy.ops.render.render(write_still=True)

print(json.dumps({"ok": True, "objects": len(everything)}))
"""


def available() -> tuple[bool, str]:
    exe = shutil.which("blender")
    if not exe:
        return False, "blender is not on PATH; preview renders need it"
    return True, exe


def render(
    out_prefix: str | Path,
    *,
    garment: trimesh.Trimesh | None = None,
    body: trimesh.Trimesh | None = None,
    views: dict[str, tuple[float, float]] | None = None,
    width: int = 700,
    height: int = 900,
) -> dict[str, object]:
    """Render garment (and body) to `<prefix>_<view>.png`. Refuses honestly."""
    ok, exe = available()
    if not ok:
        raise RuntimeError(exe)
    views = views or {"front": (0.0, 5.0), "side": (90.0, 5.0)}

    with tempfile.TemporaryDirectory() as tmp:
        specs = []
        if body is not None:
            path = Path(tmp) / "body.obj"
            body.export(path)
            specs.append({"path": str(path), "colour": [0.75, 0.72, 0.70]})
        if garment is not None:
            coloured = hasattr(garment.visual, "vertex_colors") and len(
                getattr(garment.visual, "vertex_colors", [])
            ) == len(garment.vertices)
            path = Path(tmp) / ("garment.ply" if coloured else "garment.obj")
            garment.export(path)
            specs.append({"path": str(path), "colour": [0.18, 0.35, 0.62]})
        if not specs:
            raise ValueError("nothing to render: pass a garment, a body, or both")

        script = Path(tmp) / "render.py"
        script.write_text(_RENDER)
        payload = {
            "meshes": specs,
            "out": f"{out_prefix}_VIEW.png",
            "views": {k: list(v) for k, v in views.items()},
            "width": width,
            "height": height,
        }
        proc = subprocess.run(
            [
                exe,
                "--background",
                "--factory-startup",
                "--python",
                str(script),
                "--",
                json.dumps(payload),
            ],
            capture_output=True,
            text=True,
            timeout=900,
        )
    written = [f"{out_prefix}_{name}.png" for name in views]
    missing = [p for p in written if not Path(p).exists()]
    if missing:
        raise RuntimeError(
            f"blender wrote no image for {missing}: {(proc.stderr or proc.stdout)[-500:]}"
        )
    return {"images": written, "views": list(views)}


def garment_mesh(
    points: np.ndarray, triangles: np.ndarray, uv: np.ndarray | None = None
) -> trimesh.Trimesh:
    """Cloth points + triangles as a mesh. Not watertight, and that is correct:
    a garment is a surface with a hem, a neckline and two cuffs.

    `uv` attaches a texture layout. For a garment that is FREE and exact: the
    flat pattern IS the UV map, because a pattern is precisely the surface
    unrolled into the plane. Every other 3D pipeline pays an unwrap step here,
    guesses where the seams go, and lives with the distortion; a garment
    already knows its seams, and its parameterisation is the shape a cutter
    will cut - so a print lands exactly where it was drawn.
    """
    mesh = trimesh.Trimesh(vertices=np.asarray(points), faces=np.asarray(triangles), process=False)
    if uv is not None:
        mesh.visual = trimesh.visual.TextureVisuals(uv=np.asarray(uv, dtype=np.float64))
    return mesh


def pattern_uv(rest_points_mm: np.ndarray) -> np.ndarray:
    """The flat pattern normalised to [0, 1] - the garment's UV map.

    Normalised over the WHOLE pattern rather than per panel, so the pieces
    keep their relative scale and a print that spans a seam still lines up.
    """
    flat = np.asarray(rest_points_mm, dtype=np.float64)
    low = flat.min(axis=0)
    span = np.maximum(flat.max(axis=0) - low, 1e-9)
    return (flat - low) / span.max()
