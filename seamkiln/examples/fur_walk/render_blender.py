"""Render the fur-jacket walk. Runs INSIDE headless Blender, factory startup.

    blender --background --factory-startup --python render_blender.py -- \
        SIM_DIR OUT_DIR FIRST LAST WIDTH HEIGHT SAMPLES

The fur arrives as three-point strands and becomes camera-facing ribbon MESH.
Blender curves rendered but ignored the material (pure red produced pale
cream), and the Principled Hair BSDF is Cycles-only; with real geometry the
material is an ordinary mesh material that certainly works, and a vertex
colour carries root-to-tip shading because there is no Hair Info to ask.
"""

import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _blender_body import load_figure

ARGS = sys.argv[sys.argv.index("--") + 1 :]
WALK, OUT = Path(ARGS[0]), Path(ARGS[1])
FIRST = int(ARGS[2]) if len(ARGS) > 2 else 0
LAST = int(ARGS[3]) if len(ARGS) > 3 else -1
RES = (int(ARGS[4]), int(ARGS[5])) if len(ARGS) > 5 else (1920, 1080)
SAMPLES = int(ARGS[6]) if len(ARGS) > 6 else 48

M = json.loads((WALK / "manifest.json").read_text())
TRI = np.load(WALK / "cloth_topology.npy")

# The figure is a MANNEQUIN, and it is rendered as one: warm wood, matte, the
# head the same as the body. Rendered as a black suit with a skin neck it read
# as a shop dummy with its head painted out, which is worse than a figure
# that is honestly a figure.
WOOD = (0.33, 0.215, 0.115)
PART_COLOURS = [
    WOOD,  # SUIT
    (0.38, 0.26, 0.15),  # SKIN - a shade lighter, so the neck and hands read
    (0.20, 0.125, 0.07),  # BOOT - darker feet
    (0.29, 0.19, 0.105),  # GLOVE
    WOOD,  # BELT
    WOOD,  # EMBLEM
]
# The pelt: a dense dark undercoat and sparse guard hairs with pale tips,
# each strand tinted a little differently - uniform fuzz reads as felt.
UNDER_ROOT, UNDER_TIP = (0.018, 0.011, 0.007), (0.16, 0.095, 0.048)
GUARD_ROOT, GUARD_TIP = (0.05, 0.03, 0.016), (0.50, 0.37, 0.22)


def to_blender(p):
    out = np.empty_like(p)
    out[..., 0], out[..., 1], out[..., 2] = p[..., 0], p[..., 2], p[..., 1]
    return out


def mat(name, base, rough=0.5, spec=0.5, coat=0.0, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = spec
    if coat and "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = coat
    return m


def fur_material():
    m = bpy.data.materials.new("fur")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "along"
    nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.58
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.28
    for key, value in (
        ("Transmission Weight", 0.18),
        ("Sheen Weight", 0.6),
        ("Sheen Roughness", 0.32),
    ):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = value
    m.use_backface_culling = False
    return m


def build_fur(
    strands,
    material,
    camera,
    root_mm=1.3,
    tip_mm=0.35,
    root=UNDER_ROOT,
    tip=UNDER_TIP,
    name="Fur",
    variation=0.28,
):
    a, m, b = strands[:, 0], strands[:, 1], strands[:, 2]
    pts = to_blender(np.stack([a, m, b], axis=1))  # [n, 3, 3]
    eye = np.asarray(camera, dtype=np.float64)
    tangent = np.diff(np.concatenate([pts, pts[:, 2:3]], axis=1), axis=1)
    to_eye = eye[None, None, :] - pts
    side = np.cross(tangent, to_eye)
    side /= np.maximum(np.linalg.norm(side, axis=2, keepdims=True), 1e-12)
    width = (
        np.stack(
            [
                np.full(len(pts), root_mm),
                np.full(len(pts), (root_mm + tip_mm) / 2),
                np.full(len(pts), tip_mm),
            ],
            axis=1,
        )[:, :, None]
        / 2000.0
    )
    left, right = pts - side * width, pts + side * width
    verts = np.concatenate([left, right], axis=1).reshape(-1, 3)
    n = len(pts)
    base = np.arange(n) * 6
    quads = np.concatenate(
        [
            np.stack([base + 0, base + 3, base + 4, base + 1], axis=1),
            np.stack([base + 1, base + 4, base + 5, base + 2], axis=1),
        ],
        axis=0,
    )
    me = bpy.data.meshes.new(f"{name}Mesh")
    me.from_pydata(verts.tolist(), [], quads.tolist())
    me.update()
    shade = me.color_attributes.new(name="along", type="FLOAT_COLOR", domain="POINT")
    along = np.tile(np.asarray([0.0, 0.5, 1.0]), (n, 2)).reshape(-1)
    # per-strand tint from the strand's index: the strands are regrown from
    # one seed every frame, so index k is the same root every frame and its
    # tint does not flicker
    rng = np.random.default_rng(11)
    tint = 1.0 + variation * (rng.random(n) * 2.0 - 1.0)
    per_vertex = np.repeat(tint, 6)
    colour = np.zeros((len(verts), 4), dtype=np.float32)
    for k in range(3):
        colour[:, k] = (root[k] + (tip[k] - root[k]) * along) * per_vertex
    colour[:, 3] = 1.0
    shade.data.foreach_set("color", colour.ravel())

    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    for poly in me.polygons:
        poly.use_smooth = True
    return obj


def cloth_object(points, material):
    me = bpy.data.meshes.new("Cloth")
    me.from_pydata([Vector(v) for v in to_blender(points)], [], TRI.tolist())
    me.update()
    obj = bpy.data.objects.new("Cloth", me)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    obj.modifiers.new("thickness", "SOLIDIFY").thickness = 0.006
    for poly in me.polygons:
        poly.use_smooth = True
    return obj


def load_body(path, materials_, offset):
    return load_figure(path, materials_, offset, name="Figure")


def build_world():
    world = bpy.data.worlds.new("sky")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_elevation = math.radians(7.0)  # low winter sun, behind
    sky.sun_rotation = math.radians(20.0)
    sky.altitude = 900.0
    sky.air_density = 1.0
    sky.aerosol_density = 0.9
    nt.links.new(sky.outputs["Color"], nt.nodes["Background"].inputs["Color"])
    nt.nodes["Background"].inputs["Strength"].default_value = 0.22

    # The low sun behind is the RIM: fur is read through light passing
    # through it. But a subject lit only from behind is a silhouette, and the
    # first pass was - grey figure, cream pelt. The key is a warm sun from
    # the front-left, and a soft cool fill from the right keeps the shadow
    # side from going to black.
    bpy.ops.object.light_add(type="SUN")
    rim = bpy.context.active_object
    rim.name = "Rim"
    rim.data.energy = 3.4
    rim.data.angle = math.radians(2.5)
    rim.data.color = (1.0, 0.86, 0.68)
    rim.rotation_euler = (math.radians(76), 0, math.radians(188))

    bpy.ops.object.light_add(type="SUN")
    key = bpy.context.active_object
    key.name = "Key"
    key.data.energy = 2.6
    key.data.angle = math.radians(4.0)
    key.data.color = (1.0, 0.93, 0.84)
    # the figure walks toward +Y (seamkiln +Z); a sun tilted by a NEGATIVE X
    # angle travels toward -Y and so lights the faces that look toward +Y
    key.rotation_euler = (math.radians(-52), 0, math.radians(-38))

    bpy.ops.object.light_add(type="AREA", location=(-2.4, 4.6, 2.4))
    fill = bpy.context.active_object
    fill.name = "Fill"
    fill.data.energy = 220.0
    fill.data.size = 6.0
    fill.data.color = (0.78, 0.86, 1.0)
    fill.rotation_euler = (math.radians(-62), 0, math.radians(-30))

    # packed earth, not a grey plane: a coarse and a fine noise, warm, with
    # enough contrast that the figure's shadow lands on something
    ground = mat("ground", (0.115, 0.098, 0.080), rough=0.95)
    nt2 = ground.node_tree
    noise = nt2.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2.2
    noise.inputs["Detail"].default_value = 12.0
    noise.inputs["Roughness"].default_value = 0.72
    ramp = nt2.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[0].color = (0.035, 0.027, 0.019, 1.0)
    ramp.color_ramp.elements[1].position = 0.58
    ramp.color_ramp.elements[1].color = (0.24, 0.185, 0.13, 1.0)
    nt2.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt2.links.new(ramp.outputs["Color"], nt2.nodes["Principled BSDF"].inputs["Base Color"])
    bpy.ops.mesh.primitive_plane_add(size=200.0)
    bpy.context.active_object.data.materials.append(ground)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = RES
    scene.eevee.taa_render_samples = SAMPLES
    scene.eevee.use_raytracing = True
    scene.eevee.ray_tracing_method = "SCREEN"
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.40
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0.05

    build_world()
    # matte: with a coat and a low roughness the figure rendered as porcelain
    parts = [mat(f"p{i}", c, rough=0.78, spec=0.28) for i, c in enumerate(PART_COLOURS)]
    shell = mat("shell", (0.028, 0.018, 0.011), rough=0.9, spec=0.2)
    pelt = fur_material()

    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    cam.data.lens = 50.0
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 2.4
    scene.camera = cam

    OUT.mkdir(parents=True, exist_ok=True)
    shots = M["shots"]
    last = LAST if LAST >= 0 else len(shots) - 1
    for shot in shots[FIRST : last + 1]:
        i = shot["frame"]
        # camera FIRST: every fur ribbon is turned to face it
        hz = shot["offset"][2]
        cam.location = (0.42, 3.15, 1.30)
        look = Vector((0.0, hz + 0.10, 1.08))
        direction = look - cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        cam.data.dof.focus_distance = max(direction.length, 0.6)

        cloth = cloth_object(np.load(WALK / "cloth" / f"{i:04d}.npy").astype(np.float64), shell)
        strands = np.load(WALK / "fur" / f"{i:04d}.npy").astype(np.float64)
        made = [cloth, build_fur(strands, pelt, cam.location, root_mm=0.9, tip_mm=0.25)]
        guard_file = WALK / "guard" / f"{i:04d}.npy"
        if guard_file.exists():
            guard = np.load(guard_file).astype(np.float64)
            made.append(
                build_fur(
                    guard,
                    pelt,
                    cam.location,
                    root_mm=1.0,
                    tip_mm=0.18,
                    root=GUARD_ROOT,
                    tip=GUARD_TIP,
                    name="Guard",
                    variation=0.35,
                )
            )
        made.append(load_body(WALK / "body" / f"{i:04d}.ply", parts, shot["offset"]))

        scene.render.filepath = str(OUT / f"{i:04d}.png")
        bpy.ops.render.render(write_still=True)
        for obj in made:
            bpy.data.objects.remove(obj, do_unlink=True)
        print(f"RENDERED {i} ({strands.shape[0]} strands)", flush=True)


main()
