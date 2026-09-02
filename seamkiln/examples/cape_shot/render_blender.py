"""Build the set, dress the hero, render the shot. Runs INSIDE headless Blender.

    blender --background --factory-startup --python render_blender.py -- \
        SIM_DIR OUT_DIR FLAG.png FIRST LAST WIDTH HEIGHT SAMPLES

`--factory-startup` on purpose: this never touches whatever the owner has
open. Everything in the scene is built here; the only imports are the meshes
the cloth solver produced.
"""

import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1 :]
SHOT, OUT, FLAG = Path(ARGS[0]), Path(ARGS[1]), ARGS[2]
FIRST = int(ARGS[3]) if len(ARGS) > 3 else 0
LAST = int(ARGS[4]) if len(ARGS) > 4 else -1
RES = (int(ARGS[5]), int(ARGS[6])) if len(ARGS) > 6 else (1920, 1080)
SAMPLES = int(ARGS[7]) if len(ARGS) > 7 else 64

M = json.loads((SHOT / "manifest.json").read_text())
SET = M["set"]
TRI = np.load(SHOT / "cape_topology.npy")
UV2 = np.load(SHOT / "cape_uv.npy")
STATE = {}


def to_blender(p):
    """seamkiln is Y-up; Blender is Z-up. The swap lives in exactly one place."""
    out = np.empty_like(p)
    out[:, 0], out[:, 1], out[:, 2] = p[:, 0], p[:, 2], p[:, 1]
    return out


def mat(name, base, rough=0.5, metallic=0.0, spec=0.5, transmission=0.0, ior=1.45, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = spec
    if "Coat Weight" in b.inputs and coat:
        b.inputs["Coat Weight"].default_value = coat
    if transmission and "Transmission Weight" in b.inputs:
        b.inputs["Transmission Weight"].default_value = transmission
        b.inputs["IOR"].default_value = ior
    return m


def flag_material(name):
    """The cape: the flag, and the water in it, PER VERTEX in the colour
    attribute's alpha - so the hem that went into the pool is dark and heavy
    while the shoulders are still dry."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(FLAG)
    tex.interpolation = "Cubic"
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "wet"
    soaked = nt.nodes.new("ShaderNodeMixRGB")
    soaked.blend_type = "MULTIPLY"
    soaked.inputs["Color2"].default_value = (0.40, 0.43, 0.50, 1.0)
    nt.links.new(attr.outputs["Alpha"], soaked.inputs["Fac"])
    nt.links.new(tex.outputs["Color"], soaked.inputs["Color1"])
    nt.links.new(soaked.outputs["Color"], bsdf.inputs["Base Color"])
    rough = nt.nodes.new("ShaderNodeMix")
    rough.data_type = "FLOAT"
    rough.inputs[2].default_value = 0.72
    rough.inputs[3].default_value = 0.15
    nt.links.new(attr.outputs["Alpha"], rough.inputs["Factor"])
    nt.links.new(rough.outputs[0], bsdf.inputs["Roughness"])
    if "Coat Weight" in bsdf.inputs:
        coat = nt.nodes.new("ShaderNodeMix")
        coat.data_type = "FLOAT"
        coat.inputs[2].default_value = 0.0
        coat.inputs[3].default_value = 0.8
        nt.links.new(attr.outputs["Alpha"], coat.inputs["Factor"])
        nt.links.new(coat.outputs[0], bsdf.inputs["Coat Weight"])
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = 0.35
    m.use_backface_culling = False
    return m


# Base colour per PART, dry; wet is the same colour multiplied down and made
# glossier, because that is what water does to a surface.
PART_COLOURS = [
    (0.030, 0.048, 0.200),  # SUIT   - deep blue
    (0.240, 0.115, 0.062),  # SKIN
    (0.230, 0.016, 0.026),  # BOOT   - red
    (0.230, 0.016, 0.026),  # GLOVE  - red
    (0.420, 0.250, 0.030),  # BELT   - gold
    (0.720, 0.470, 0.040),  # EMBLEM - the flag's gold
]


def part_material(index):
    dry = PART_COLOURS[index]
    m = bpy.data.materials.new(f"part{index}")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "Col"
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (*dry, 1.0)
    mix.inputs[7].default_value = (*[v * 0.40 for v in dry], 1.0)
    nt.links.new(attr.outputs["Alpha"], mix.inputs["Factor"])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    rough = nt.nodes.new("ShaderNodeMix")
    rough.data_type = "FLOAT"
    rough.inputs[2].default_value = 0.16 if index == 5 else 0.40
    rough.inputs[3].default_value = 0.07
    nt.links.new(attr.outputs["Alpha"], rough.inputs["Factor"])
    nt.links.new(rough.outputs[0], bsdf.inputs["Roughness"])
    if "Coat Weight" in bsdf.inputs:
        coat = nt.nodes.new("ShaderNodeMix")
        coat.data_type = "FLOAT"
        coat.inputs[2].default_value = 0.20
        coat.inputs[3].default_value = 0.95
        nt.links.new(attr.outputs["Alpha"], coat.inputs["Factor"])
        nt.links.new(coat.outputs[0], bsdf.inputs["Coat Weight"])
    if index in (4, 5):
        bsdf.inputs["Metallic"].default_value = 0.85
    return m


def box(name, centre, size, material, bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    o = bpy.context.active_object
    o.name = name
    cx, cy, cz = centre
    sx, sy, sz = size
    o.scale = (sx, sz, sy)  # seamkiln (x, up, z) -> blender (x, y, up)
    o.location = (cx, cz, cy + sy / 2.0)
    b = o.modifiers.new("bevel", "BEVEL")
    b.width, b.segments = bevel, 3
    o.data.materials.append(material)
    return o


def build_set():
    ground = mat("ground", (0.42, 0.33, 0.23), rough=0.94)
    nt = ground.node_tree
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 5.5
    noise.inputs["Detail"].default_value = 8.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.16, 0.115, 0.072, 1.0)
    ramp.color_ramp.elements[1].color = (0.34, 0.265, 0.175, 1.0)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    crate = mat("crate", (0.42, 0.30, 0.18), rough=0.75)
    crate2 = mat("crate2", (0.38, 0.26, 0.15), rough=0.78)
    matting = mat("mat", (0.05, 0.35, 0.62), rough=0.55, spec=0.7)
    tiles = mat("tiles", (0.80, 0.83, 0.86), rough=0.35)

    box("BoxA", SET["box_a"]["centre"], SET["box_a"]["size"], crate)
    box("BoxB", SET["box_b"]["centre"], SET["box_b"]["size"], crate2)
    m = box("Mat", SET["mat"]["centre"], SET["mat"]["size"], matting, bevel=0.06)
    m.modifiers.new("smooth", "SUBSURF").levels = 1
    STATE["mat"] = m
    STATE["mat_rest"] = (tuple(m.scale), tuple(m.location))

    # The pool is a hole in the ground, so the GROUND has a hole in it: four
    # quads tiled round the footprint. Cheaper than a boolean and exact.
    p = SET["pool"]
    px, _, pz = p["centre"]
    sx, depth, sz = p["size"]
    hx, hz = sx / 2.0, sz / 2.0
    far = 60.0
    for name, cx, cy, ex, ey in (
        ("GroundN", px, pz + hz + far / 2, far, far),
        ("GroundS", px, pz - hz - far / 2, far, far),
        ("GroundE", px + hx + far / 2, pz, far, sz),
        ("GroundW", px - hx - far / 2, pz, far, sz),
    ):
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(cx, cy, 0.0))
        g = bpy.context.active_object
        g.name = name
        g.scale = (ex, ey, 1.0)
        g.data.materials.append(ground)
    wall = 0.16
    for name, cx, cy, ex, ey in (
        ("PoolN", px, pz + hz, sx + 2 * wall, wall),
        ("PoolS", px, pz - hz, sx + 2 * wall, wall),
        ("PoolE", px + hx, pz, wall, sz),
        ("PoolW", px - hx, pz, wall, sz),
    ):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, cy, (0.10 - depth) / 2))
        o = bpy.context.active_object
        o.name = name
        o.scale = (ex, ey, depth + 0.10)
        o.data.materials.append(tiles)
        o.modifiers.new("bevel", "BEVEL").width = 0.02
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(px, pz, -depth))
    floor = bpy.context.active_object
    floor.name = "PoolFloor"
    floor.scale = (sx, sz, 1.0)
    floor.data.materials.append(mat("pool_floor", (0.06, 0.30, 0.36), rough=0.30))

    water = mat("water", (0.006, 0.105, 0.155), rough=0.012, transmission=0.97, ior=1.333)
    water.use_raytrace_refraction = True
    water.use_screen_refraction = True
    bpy.ops.mesh.primitive_plane_add(size=1.0)
    w = bpy.context.active_object
    w.name = "Water"
    w.scale = (sx * 0.99, sz * 0.99, 1.0)
    w.location = (px, pz, SET["water_y"])
    for _ in range(5):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.subdivide()
        bpy.ops.object.mode_set(mode="OBJECT")
    w.data.materials.append(water)
    disp = w.modifiers.new("ripple", "DISPLACE")
    tex = bpy.data.textures.new("ripple", "CLOUDS")
    tex.noise_scale = 0.55
    disp.texture = tex
    disp.strength = 0.022
    w.modifiers.new("smoothw", "SUBSURF").levels = 1


def build_sky():
    world = bpy.data.worlds.new("sky")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    # Blender 5.2: NISHITA became MULTIPLE_SCATTERING, dust_density became
    # aerosol_density. Both are in TEE's version firewall.
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_elevation = math.radians(26.0)
    sky.sun_rotation = math.radians(215.0)
    sky.altitude = 400.0
    sky.air_density = 1.1
    sky.aerosol_density = 2.6
    sky.ozone_density = 1.4
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.28  # ambient; the sun is the key

    bpy.ops.object.light_add(type="SUN")
    sun = bpy.context.active_object
    sun.name = "Key"
    sun.data.energy = 4.2
    sun.data.angle = math.radians(1.2)
    sun.data.color = (1.0, 0.93, 0.82)
    sun.rotation_euler = (math.radians(56), 0.0, math.radians(42))
    bpy.ops.object.light_add(type="SUN")
    rim = bpy.context.active_object
    rim.name = "Rim"
    rim.data.energy = 1.8
    rim.data.color = (0.72, 0.84, 1.0)
    rim.rotation_euler = (math.radians(68), 0, math.radians(-155))
    bpy.ops.object.light_add(type="AREA", location=(-7, -9, 4.5))
    fill = bpy.context.active_object
    fill.name = "Fill"
    fill.data.energy = 420.0
    fill.data.size = 10.0
    fill.data.color = (0.85, 0.90, 1.0)
    fill.rotation_euler = (math.radians(64), 0, math.radians(-40))


def cape_object(points, wetness, material):
    me = bpy.data.meshes.new("CapeMesh")
    me.from_pydata([Vector(v) for v in to_blender(points)], [], TRI.tolist())
    me.update()
    uv = me.uv_layers.new(name="UVMap")
    lo, hi = UV2.min(axis=0), UV2.max(axis=0)
    norm = (UV2 - lo) / np.maximum(hi - lo, 1e-9)
    for loop in me.loops:
        uv.data[loop.index].uv = tuple(norm[loop.vertex_index])
    wet = me.color_attributes.new(name="wet", type="FLOAT_COLOR", domain="POINT")
    data = np.zeros((len(me.vertices), 4), dtype=np.float32)
    data[:, 3] = wetness  # alpha: the one channel Blender does not colour-manage
    wet.data.foreach_set("color", data.ravel())
    o = bpy.data.objects.new("Cape", me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(material)
    o.modifiers.new("thickness", "SOLIDIFY").thickness = 0.004
    o.modifiers.new("smooth", "SUBSURF").levels = 1
    for poly in me.polygons:
        poly.use_smooth = True
    return o


def load_body(path, materials, offset):
    before = set(bpy.data.objects)
    bpy.ops.wm.ply_import(filepath=str(path))
    o = next(iter(set(bpy.data.objects) - before))
    o.name = "Hero"
    o.rotation_euler = (math.radians(90), 0, 0)  # Y-up -> Z-up
    o.location = (offset[0], offset[2], offset[1])
    o.data.materials.clear()
    for m in materials:
        o.data.materials.append(m)
    # The part tag rides in the colour attribute's RED, which Blender
    # sRGB-decodes on import - stretched but still in ORDER, so faces are
    # matched to slots by RANK (np.searchsorted), never by float equality.
    me = o.data
    attr = me.color_attributes[0]
    raw = np.zeros((len(attr.data), 4), dtype=np.float32)
    attr.data.foreach_get("color", raw.ravel())
    reds = raw[:, 0].astype(np.float64)
    order = np.asarray(sorted(set(reds.tolist())))
    edges = (order[:-1] + order[1:]) / 2.0
    per_vertex = np.searchsorted(edges, reds)
    first = np.asarray([p.vertices[0] for p in me.polygons], dtype=np.int64)
    me.polygons.foreach_set("material_index", per_vertex[first].astype(np.int32))
    me.update()
    for poly in me.polygons:
        poly.use_smooth = True
    o.modifiers.new("smooth", "SUBSURF").levels = 1
    return o


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = RES
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = -0.15
    looks = {i.identifier for i in scene.view_settings.bl_rna.properties["look"].enum_items}
    for wanted in ("AgX - Punchy", "Punchy", "AgX - Medium High Contrast"):
        if wanted in looks:
            scene.view_settings.look = wanted
            break
    scene.eevee.taa_render_samples = SAMPLES
    # Without raytracing the water renders as ICE: transmission in EEVEE
    # needs screen-space rays, and with them off the surface just reflects.
    scene.eevee.use_raytracing = True
    scene.eevee.ray_tracing_method = "SCREEN"
    scene.eevee.ray_tracing_options.resolution_scale = "1"
    scene.eevee.ray_tracing_options.use_denoise = True
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.42

    build_sky()
    build_set()
    parts = [part_material(k) for k in range(len(PART_COLOURS))]
    cape_mat = flag_material("cape")

    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    cam.data.lens = 36.0
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 4.0
    scene.camera = cam

    OUT.mkdir(parents=True, exist_ok=True)
    shots = M["shots"]
    last = LAST if LAST >= 0 else len(shots) - 1
    for shot in shots[FIRST : last + 1]:
        i = shot["frame"]
        pts = np.load(SHOT / "cape" / f"{i:04d}.npy").astype(np.float64)
        wetfile = SHOT / "cape" / f"wet_{i:04d}.npy"
        wetness = np.load(wetfile) if wetfile.exists() else np.zeros(len(pts), dtype=np.float32)
        cape = cape_object(pts, wetness, cape_mat)
        hero = load_body(SHOT / "body" / f"{i:04d}.ply", parts, shot["offset"])

        # The camera trails the hero; its vertical tracking is DAMPED so the
        # set stays in frame - which is the only thing that makes it a jump.
        hx, hy, _ = shot["offset"]
        t = shot["t"]
        rise = 0.55 * max(hy, 0.0)
        cam.location = (
            hx - 3.0 + 0.40 * math.sin(t * 0.6),
            -6.9 - 0.45 * math.cos(t * 0.4),
            rise + 1.85 + 0.22 * math.sin(t * 0.9),
        )
        look = Vector((hx + 0.35, 0.0, rise + 0.72))
        direction = look - cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        cam.data.dof.focus_distance = max(direction.length, 0.5)

        # The mat GIVES: squashed in Z and bulged in X/Y. 0.62 is not a taste
        # value - the mat is 0.42 m thick and gives 0.26, so its top has to
        # arrive at 0.16 m to meet the feet: 1 - 0.16/0.42.
        squash = float(shot.get("mat_squash", 0.0))
        (sx0, sy0, sz0), (lx, ly, lz) = STATE["mat_rest"]
        give = 0.62 * squash
        STATE["mat"].scale = (
            sx0 * (1 + 0.10 * squash),
            sy0 * (1 + 0.10 * squash),
            sz0 * (1 - give),
        )
        STATE["mat"].location = (lx, ly, lz - sz0 * give / 2.0)

        scene.render.filepath = str(OUT / f"{i:04d}.png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cape, do_unlink=True)
        bpy.data.objects.remove(hero, do_unlink=True)
        print(f"RENDERED {i}", flush=True)


main()
