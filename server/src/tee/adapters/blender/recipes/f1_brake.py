"""Authored TEE F1 lesson for Blender 5.2; load, then call build/revise/inspect.

All geometry is in metres. No work runs when the program is loaded.
The inspector raises on failed geometry, ownership or dependency checks.
"""

import math

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OWNER = "TEE A79 Blender F1"


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _start():
    _require(
        abs(bpy.context.scene.unit_settings.scale_length - 1) < 1e-12,
        "Lesson requires scene unit scale 1 (coordinates in metres)",
    )
    _require(bpy.context.mode == "OBJECT", "Switch to Object Mode first")
    _require(COLLECTION not in bpy.data.collections, "Lesson already exists; use revise/inspect")
    for items in (bpy.data.objects, bpy.data.meshes, bpy.data.materials):
        _require(not any(x.name.startswith(PREFIX) for x in items), "Lesson name collision")
    c = bpy.data.collections.new(COLLECTION)
    c["tee_owner"] = OWNER
    bpy.context.scene.collection.children.link(c)
    mat = bpy.data.materials.new(PREFIX + "Surface")
    mat["tee_owner"] = OWNER
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.12, 0.18, 0.23, 1)
    bsdf.inputs["Metallic"].default_value = 0.55
    bsdf.inputs["Roughness"].default_value = 0.3
    return c


def _owned(names):
    _require(
        abs(bpy.context.scene.unit_settings.scale_length - 1) < 1e-12,
        "Lesson requires scene unit scale 1 (coordinates in metres)",
    )
    c = bpy.data.collections.get(COLLECTION)
    _require(c is not None and c.get("tee_owner") == OWNER, "Owned lesson collection required")
    objects = {o.name: o for o in c.all_objects}
    _require(set(objects) == {PREFIX + x for x in names}, "Missing or foreign lesson object")
    for o in objects.values():
        _require(
            o.get("tee_owner") == OWNER and list(o.users_collection) == [c],
            "Mixed object ownership",
        )
        if o.data is not None:
            _require(
                o.data.get("tee_owner") == OWNER and o.data.users == 1,
                "Shared or foreign mesh data",
            )
        if o.parent:
            _require(o.parent in objects.values(), "Foreign parent dependency")
        for m in o.modifiers:
            if m.type == "BOOLEAN":
                _require(m.object in objects.values(), "Foreign Boolean dependency")
        if o.animation_data:
            for fc in o.animation_data.drivers:
                for v in fc.driver.variables:
                    _require(
                        all(t.id in objects.values() for t in v.targets),
                        "Foreign driver dependency",
                    )
    return {name: objects[PREFIX + name] for name in names}


def _object(c, name, verts=None, faces=None, hidden=False):
    mesh = None
    if verts is not None:
        mesh = bpy.data.meshes.new(PREFIX + name)
        mesh["tee_owner"] = OWNER
        mesh.from_pydata(verts, [], faces)
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(bpy.data.materials[PREFIX + "Surface"])
    o = bpy.data.objects.new(PREFIX + name, mesh)
    o["tee_owner"] = OWNER
    c.objects.link(o)
    if hidden:
        o.hide_render = True
        o.hide_set(True)
    return o


def _prism(points, height=1.0):
    n = len(points)
    verts = [(x, y, z) for z in (0, height) for x, y in points]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return verts, faces


def _circle(radius, n=128):
    return [
        (radius * math.cos(2 * math.pi * i / n), radius * math.sin(2 * math.pi * i / n))
        for i in range(n)
    ]


def _drive(o, path, axis, control, prop, expression="p"):
    curve = o.driver_add(path, axis)
    d = curve.driver
    v = d.variables.new()
    v.name, v.type = "p", "SINGLE_PROP"
    v.targets[0].id = control
    v.targets[0].data_path = '["' + prop + '"]'
    d.expression = expression


def _driver_check(o, path, axis, control, prop, expression="p"):
    curves = o.animation_data.drivers if o.animation_data else []
    found = [fc for fc in curves if fc.data_path == path and fc.array_index == axis]
    _require(len(found) == 1, "Missing live dimension driver: " + o.name)
    d = found[0].driver
    _require(
        d.is_valid
        and not found[0].mute
        and d.type == "SCRIPTED"
        and d.expression == expression
        and len(d.variables) == 1,
        "Invalid dimension driver: " + o.name,
    )
    v = d.variables[0]
    _require(
        v.name == "p"
        and v.type == "SINGLE_PROP"
        and v.targets[0].id == control
        and v.targets[0].data_path == '["' + prop + '"]',
        "Wrong dimension dependency",
    )


def _boolean(target, cutter, operation="DIFFERENCE"):
    m = target.modifiers.new(cutter.name, "BOOLEAN")
    m.operation, m.solver, m.object = operation, "EXACT", cutter


def _evaluated(o):
    bpy.context.view_layer.update()
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = ev.to_mesh()
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.transform(ev.matrix_world)
        _require(
            bool(bm.faces) and all(e.is_manifold for e in bm.edges),
            "Evaluated mesh is not closed manifold: " + o.name,
        )
        volume = abs(bm.calc_volume(signed=True))
        points = [tuple(v.co) for v in bm.verts]
        tree = BVHTree.FromBMesh(bm)
        seen, components = set(), 0
        for v in bm.verts:
            if v in seen:
                continue
            components += 1
            stack = [v]
            while stack:
                q = stack.pop()
                if q in seen:
                    continue
                seen.add(q)
                stack.extend(e.other_vert(q) for e in q.link_edges)
        _require(components == 1, "Disconnected evaluated solid: " + o.name)
        return volume, points, tree
    finally:
        bm.free()
        ev.to_mesh_clear()


def _bounds(points):
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    return [hi[i] - lo[i] for i in range(3)]


def _near(value, expected, tolerance, label):
    _require(abs(value - expected) <= tolerance, label + " differs from measured expectation")


def _ray(tree, origin, direction, length):
    return tree.ray_cast(Vector(origin), Vector(direction), length)[0]


def _update(control):
    control.update_tag()
    bpy.context.view_layer.update()


COLLECTION = "TEE Lesson — F1 Ventilated Brake"
PREFIX = "TEE_F1B_"
NAMES = (
    "Controls",
    "Disc",
    *tuple("Channel_" + row + f"_{i:02d}" for row in "AB" for i in range(30)),
)


def _annulus():
    n = 720
    verts = [
        (r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), z)
        for z in (0, 0.028)
        for r in (0.09, 0.14)
        for i in range(n)
    ]
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.extend(
            [
                (i, j, j + n, i + n),
                (i + 2 * n, i + 3 * n, j + 3 * n, j + 2 * n),
                (i, i + 2 * n, j + 2 * n, j),
                (i + n, j + n, j + 3 * n, i + 3 * n),
            ]
        )
    return verts, faces


def build():
    """60 real Boolean cooling passages: two rows, 30 each, staggered by six degrees."""
    c = _start()
    control = _object(c, "Controls")
    control["diameter_A_m"], control["diameter_B_m"], control["stage"] = 0.006, 0.006, "initial"
    disc = _object(c, "Disc", *_annulus())
    for row, z, phase in (("A", 0.007, 0), ("B", 0.021, 90)):
        for i in range(30):
            cutter = _object(
                c, "Channel_" + row + f"_{i:02d}", *_prism(_circle(1, 96)), hidden=True
            )
            a = math.radians(phase + 12 * i)
            cutter.rotation_euler = (
                Vector((math.cos(a), math.sin(a), 0)).to_track_quat("Z", "Y").to_euler()
            )
            cutter.location.z, cutter.scale.z = z, 0.16
            for axis in (0, 1):
                _drive(cutter, "scale", axis, control, "diameter_" + row + "_m", "p/2")
            _boolean(disc, cutter)
    _update(control)
    return inspect()


def revise():
    """Drive the rows independently: 6/6 mm passages become 7/8 mm, preserving staggering."""
    control = _owned(NAMES)["Controls"]
    control["diameter_A_m"], control["diameter_B_m"], control["stage"] = 0.007, 0.008, "revised"
    _update(control)
    return inspect()


def inspect():
    """Measure closed evaluated geometry, all 60 open paths and 240 actual passage radii."""
    o = _owned(NAMES)
    control, disc = o["Controls"], o["Disc"]
    _require(control.get("stage") in ("initial", "revised"), "Unknown lesson stage")
    revised = control.get("stage") == "revised"
    diameters = (0.007, 0.008) if revised else (0.006, 0.006)
    expected_volume = (878448.8535736335 if revised else 926762.2571630095) * 1e-9
    _require(len(disc.modifiers) == 60, "Expected sixty editable cooling cuts")
    volume, points, tree = _evaluated(disc)
    _near(volume, expected_volume, expected_volume * 0.0004, "Faceted brake volume")
    for actual, expected in zip(_bounds(points), (0.28, 0.28, 0.028), strict=True):
        _near(actual, expected, 2e-7, "Disc bounds")
    mouth_count, radius_error = 0, 0.0
    for row, z, phase, diameter in zip("AB", (0.007, 0.021), (0, 90), diameters, strict=True):
        _near(control["diameter_" + row + "_m"], diameter, 1e-12, "Row diameter")
        for i in range(30):
            cutter = o["Channel_" + row + f"_{i:02d}"]
            for axis in (0, 1):
                _driver_check(cutter, "scale", axis, control, "diameter_" + row + "_m", "p/2")
            modifier = disc.modifiers.get(cutter.name)
            _require(
                modifier
                and modifier.operation == "DIFFERENCE"
                and modifier.solver == "EXACT"
                and modifier.show_viewport
                and modifier.show_render
                and modifier.object == cutter,
                "Cooling cut was disabled or rewired",
            )
            a = math.radians(phase + 12 * i)
            radial = Vector((math.cos(a), math.sin(a), 0))
            tangent = Vector((-math.sin(a), math.cos(a), 0))
            centre = radial * 0.115 + Vector((0, 0, z))
            # A ray beginning inside the hub hole and ending outside the rim must stay in air.
            origin = radial * 0.089 + Vector((0, 0, z))
            _require(_ray(tree, origin, radial, 0.052) is None, "Blocked radial cooling passage")
            # Two nearby material witnesses prevent an absent disc being mistaken for a passage.
            for sign in (-1, 1):
                witness = origin + tangent * (sign * diameter * 0.7)
                _require(
                    _ray(tree, witness, radial, 0.052) is not None, "Missing passage side wall"
                )
            mouth_count += 2
            for direction in (tangent, -tangent, Vector((0, 0, 1)), Vector((0, 0, -1))):
                hit = _ray(tree, centre, direction, diameter)
                _require(hit is not None, "Passage boundary missing")
                error = abs((hit - centre).length - diameter / 2)
                radius_error = max(radius_error, error)
                _near(error, 0, 0.00002, "Measured passage radius")
    return {
        "passed": True,
        "stage": "revised" if revised else "initial",
        "collection": COLLECTION,
        "primary_objects": [disc.name],
        "volume_m3": volume,
        "ideal_volume_m3": expected_volume,
        "relative_volume_error": volume / expected_volume - 1,
        "mesh_volume_tolerance_relative": 0.0004,
        "bounds_m": _bounds(points),
        "verified_open_mouths": mouth_count,
        "max_radius_error_m": radius_error,
        "checks": {
            "closed_single_solid": True,
            "si_dimensions": True,
            "all_60_through_passages": True,
            "two_independent_diameter_drivers": True,
            "all_240_radius_rays": True,
            "staggered_rows": True,
        },
        "limits": "720 rim and 96 passage facets; educational geometry, no brake performance claim",
    }
