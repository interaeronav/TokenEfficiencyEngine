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


COLLECTION = "TEE Lesson — F1 Suspension Wishbone"
PREFIX = "TEE_F1S_"
NAMES = (
    "Controls",
    "Web",
    "Aperture",
    *tuple(kind + str(i) for kind in ("Boss", "Bore", "Seat") for i in range(3)),
)
CENTRES = ((0.03, -0.07), (0.03, 0.07), (0.25, 0))


def build():
    """Editable web, integral bosses and underside counterbores; all lengths are metres."""
    c = _start()
    control = _object(c, "Controls")
    for prop, value in (
        ("plate_m", 0.006),
        ("boss_height_m", 0.020),
        ("inboard_bore_m", 0.012),
        ("outboard_bore_m", 0.016),
    ):
        control[prop] = value
    control["stage"] = "initial"
    web = _object(c, "Web", *_prism(((0, -0.1), (0.3, 0), (0, 0.1))))
    _drive(web, "scale", 2, control, "plate_m")
    for i, (x, y) in enumerate(CENTRES):
        boss = _object(c, "Boss" + str(i), *_prism(_circle(0.016 if i < 2 else 0.014)), hidden=True)
        boss.location = (x, y, 0)
        _drive(boss, "scale", 2, control, "boss_height_m")
        _boolean(web, boss, "UNION")
    aperture = _object(
        c, "Aperture", *_prism(((0.06, -0.05), (0.21, 0), (0.06, 0.05))), hidden=True
    )
    aperture.location.z = -0.001
    _drive(aperture, "scale", 2, control, "plate_m", "p+0.002")
    _boolean(web, aperture)
    for i, (x, y) in enumerate(CENTRES):
        bore = _object(c, "Bore" + str(i), *_prism(_circle(1)), hidden=True)
        bore.location = (x, y, -0.001)
        _drive(bore, "scale", 2, control, "boss_height_m", "p+0.002")
        for axis in (0, 1):
            _drive(
                bore,
                "scale",
                axis,
                control,
                "inboard_bore_m" if i < 2 else "outboard_bore_m",
                "p/2",
            )
        _boolean(web, bore)
        seat = _object(
            c,
            "Seat" + str(i),
            *_prism(_circle(0.01 if i < 2 else 0.012), 0.005 if i < 2 else 0.007),
            hidden=True,
        )
        seat.location = (x, y, -0.001)
        _boolean(web, seat)
    # Exact Booleans can leave nanometre duplicate seams after coplanar cuts.
    weld = web.modifiers.new("Merge Boolean seams", "WELD")
    weld.merge_threshold = 1e-8
    _update(control)
    return inspect()


def revise():
    """Revise web, total boss height and both bore families without leaving an aperture membrane."""
    control = _owned(NAMES)["Controls"]
    for prop, value in (
        ("plate_m", 0.008),
        ("boss_height_m", 0.024),
        ("inboard_bore_m", 0.014),
        ("outboard_bore_m", 0.018),
    ):
        control[prop] = value
    control["stage"] = "revised"
    _update(control)
    return inspect()


def inspect():
    """Volume plus actual through-aperture, bearing radii, seat depths and driver checks."""
    o = _owned(NAMES)
    control, web = o["Controls"], o["Web"]
    _require(control.get("stage") in ("initial", "revised"), "Unknown lesson stage")
    revised = control.get("stage") == "revised"
    t, height, di, do = (0.008, 0.024, 0.014, 0.018) if revised else (0.006, 0.020, 0.012, 0.016)
    for prop, expected in (
        ("plate_m", t),
        ("boss_height_m", height),
        ("inboard_bore_m", di),
        ("outboard_bore_m", do),
    ):
        _near(control[prop], expected, 1e-12, prop)
    _driver_check(web, "scale", 2, control, "plate_m")
    _driver_check(o["Aperture"], "scale", 2, control, "plate_m", "p+0.002")
    _require(len(web.modifiers) == 11, "Expected three boss unions, seven cuts and a seam weld")
    weld = web.modifiers[-1]
    _require(
        weld.type == "WELD"
        and weld.show_viewport
        and weld.show_render
        and abs(weld.merge_threshold - 1e-8) < 1e-14,
        "Expected 10 nm Boolean seam weld",
    )
    for m in list(web.modifiers)[:-1]:
        _require(
            m.show_viewport
            and m.show_render
            and m.solver == "EXACT"
            and m.operation
            == ("UNION" if m.object.name.startswith(PREFIX + "Boss") else "DIFFERENCE"),
            "Required Boolean disabled or changed",
        )
    volume, points, tree = _evaluated(web)
    expected = (199622.38771432187 if revised else 154477.8744522567) * 1e-9
    _near(volume, expected, expected * 0.0005, "Faceted wishbone volume")
    for value, dimension in zip(_bounds(points), (0.3, 0.2, height), strict=True):
        _near(value, dimension, 2e-7, "Wishbone bounds")
    # Triangulated aperture interior and nearby material witnesses, checked on the actual solid.
    for x, y in ((0.07, 0), (0.12, 0), (0.18, 0), (0.08, 0.03), (0.08, -0.03)):
        _require(
            _ray(tree, (x, y, -0.002), (0, 0, 1), height + 0.004) is None,
            "Aperture has a surviving membrane",
        )
    for x, y in ((0.02, 0), (0.15, 0.04), (0.15, -0.04)):
        hit = _ray(tree, (x, y, height + 0.002), (0, 0, -1), height + 0.004)
        _require(hit is not None, "Missing web material")
        _near(hit.z, t, 2e-7, "Actual plate thickness")
    radius_error = 0
    for i, (x, y) in enumerate(CENTRES):
        boss, bore = o["Boss" + str(i)], o["Bore" + str(i)]
        _driver_check(boss, "scale", 2, control, "boss_height_m")
        _driver_check(bore, "scale", 2, control, "boss_height_m", "p+0.002")
        for axis in (0, 1):
            _driver_check(
                bore,
                "scale",
                axis,
                control,
                "inboard_bore_m" if i < 2 else "outboard_bore_m",
                "p/2",
            )
        radius, seat_radius, depth = (di / 2, 0.01, 0.004) if i < 2 else (do / 2, 0.012, 0.006)
        _require(
            _ray(tree, (x, y, -0.002), (0, 0, 1), height + 0.004) is None, "Blocked bearing bore"
        )
        for z, expected_radius in ((depth / 2, seat_radius), ((depth + height) / 2, radius)):
            for direction in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)):
                origin = Vector((x, y, z))
                hit = _ray(tree, origin, direction, 0.02)
                _require(hit is not None, "Missing bearing wall")
                error = abs((hit - origin).length - expected_radius)
                radius_error = max(radius_error, error)
                _near(error, 0, 0.00001, "Actual bearing radius")
        hit = _ray(tree, (x + (radius + seat_radius) / 2, y, -0.001), (0, 0, 1), height + 0.002)
        _require(hit is not None, "Missing counterbore shoulder")
        _near(hit.z, depth, 2e-7, "Counterbore depth from underside")
    return {
        "passed": True,
        "stage": "revised" if revised else "initial",
        "collection": COLLECTION,
        "primary_objects": [web.name],
        "volume_m3": volume,
        "ideal_volume_m3": expected,
        "relative_volume_error": volume / expected - 1,
        "mesh_volume_tolerance_relative": 0.0005,
        "bounds_m": _bounds(points),
        "max_radius_error_m": radius_error,
        "checks": {
            "closed_single_solid": True,
            "through_aperture": True,
            "three_stepped_bearing_seats": True,
            "measured_plate_thickness": True,
            "four_dimension_dependencies": True,
        },
        "limits": (
            "128 cylindrical facets; original planar teaching geometry; no structural validation"
        ),
    }
