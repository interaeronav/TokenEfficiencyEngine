"""Authored TEE F1 lesson for Blender 5.2; load, then call build/revise/inspect.

All geometry is in metres. No work runs when the program is loaded.
The inspector raises on failed geometry, ownership or dependency checks.
"""

import math

import bmesh
import bpy
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


def _update(control):
    control.update_tag()
    bpy.context.view_layer.update()


COLLECTION = "TEE Lesson — F1 Active Wing"
PREFIX = "TEE_F1W_"
NAMES = ("Controls", "Hinge", "Mainplane", "Flap")


def _profile(chord, leading, offset):
    # NASA TM 4741 four-digit thickness; round to the Fusion wire's 1e-5 mm grid.
    upper = []
    for i in range(25):
        u = (1 - math.cos(math.pi * i / 24)) / 2
        y = (
            0.6
            * chord
            * (0.2969 * math.sqrt(u) - 0.126 * u - 0.3516 * u * u + 0.2843 * u**3 - 0.1015 * u**4)
        )
        upper.append((round(leading + chord * u, 8), round(offset + y, 8)))
    lower = [(x, round(2 * offset - y, 8)) for x, y in reversed(upper[1:])]
    return upper + lower


def _area(p):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(p, p[1:] + p[:1], strict=True))) / 2


def _rotate(p, angle):
    a = math.radians(angle)
    return [(x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)) for x, y in p]


def _distance(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _gap(a, b):
    def cross(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    def inside(p, poly):
        odd = False
        for u, v in zip(poly, poly[1:] + poly[:1], strict=True):
            if (u[1] > p[1]) != (v[1] > p[1]) and p[0] < (v[0] - u[0]) * (p[1] - u[1]) / (
                v[1] - u[1]
            ) + u[0]:
                odd = not odd
        return odd

    if inside(a[0], b) or inside(b[0], a):
        return 0.0
    result = float("inf")
    for p, q in zip(a, a[1:] + a[:1], strict=True):
        for r, s in zip(b, b[1:] + b[:1], strict=True):
            if cross(p, q, r) * cross(p, q, s) < 0 and cross(r, s, p) * cross(r, s, q) < 0:
                return 0.0
            result = min(
                result,
                _distance(p, r, s),
                _distance(q, r, s),
                _distance(r, p, q),
                _distance(s, p, q),
            )
    return result


def build():
    """Create two closed 49-edge sections and a driven quarter-chord hinge, in metres."""
    c = _start()
    control = _object(c, "Controls")
    control["span_m"], control["flap_angle_deg"], control["stage"] = 1.0, 0.0, "initial"
    hinge = _object(c, "Hinge")
    hinge.empty_display_type, hinge.empty_display_size = "ARROWS", 0.025
    _drive(hinge, "rotation_euler", 2, control, "flap_angle_deg", "-p*0.017453292519943295")
    for name, profile in (
        ("Mainplane", _profile(0.36, -0.42, 0.015)),
        ("Flap", _profile(0.16, -0.04, 0)),
    ):
        o = _object(c, name, *_prism(profile))
        _drive(o, "scale", 2, control, "span_m")
        if name == "Flap":
            o.parent = hinge
    _update(control)
    return inspect()


def revise():
    """One span drives both parts; positive 25-degree command rotates the flap clockwise."""
    objects = _owned(NAMES)
    control = objects["Controls"]
    control["span_m"], control["flap_angle_deg"], control["stage"] = 1.2, 25.0, "revised"
    _update(control)
    return inspect()


def inspect():
    """Compare evaluated vertices, volume, driver targets and a continuous sweep bound."""
    o = _owned(NAMES)
    control = o["Controls"]
    _require(control.get("stage") in ("initial", "revised"), "Unknown lesson stage")
    revised = control.get("stage") == "revised"
    span, angle = (1.2, 25.0) if revised else (1.0, 0.0)
    _near(control["span_m"], span, 1e-12, "span control")
    _near(control["flap_angle_deg"], angle, 1e-12, "angle control")
    _driver_check(
        o["Hinge"], "rotation_euler", 2, control, "flap_angle_deg", "-p*0.017453292519943295"
    )
    _require(o["Flap"].parent == o["Hinge"], "Flap lost its actual hinge parent")
    _near(o["Hinge"].location.length, 0, 1e-12, "quarter-chord pivot")
    profiles = {"Mainplane": _profile(0.36, -0.42, 0.015), "Flap": _profile(0.16, -0.04, 0)}
    readings = {}
    vertex_tolerance = 2e-7
    for name, section in profiles.items():
        _driver_check(o[name], "scale", 2, control, "span_m")
        volume, points, _ = _evaluated(o[name])
        expected_section = _rotate(section, -angle) if name == "Flap" else section
        expected = [(x, y, z) for z in (0, span) for x, y in expected_section]
        _require(len(points) == len(expected), "Section vertex count changed")
        unmatched = list(points)
        for p in expected:
            index = min(range(len(unmatched)), key=lambda i: math.dist(p, unmatched[i]))
            _near(math.dist(p, unmatched.pop(index)), 0, vertex_tolerance, name + " actual vertex")
        expected_volume = _area(section) * span
        _near(volume, expected_volume, expected_volume * 2e-6, name + " mesh volume")
        readings[name] = {"volume_m3": volume, "bounds_m": _bounds(points)}
    # Every point moves by at most 2*r*sin(half the nearest-sample angular distance).
    gaps = [
        _gap(profiles["Mainplane"], _rotate(profiles["Flap"], -a)) for a in (0, 5, 10, 15, 20, 25)
    ]
    radius = max(math.hypot(x, y) for x, y in profiles["Flap"])
    lower = min(gaps) - 2 * radius * math.sin(math.radians(5) / 4) - 2 * vertex_tolerance
    _require(lower > 0.010, "Continuous 0..25 degree sweep loses 10 mm clearance")
    return {
        "passed": True,
        "stage": "revised" if revised else "initial",
        "collection": COLLECTION,
        "primary_objects": [o[x].name for x in ("Mainplane", "Flap")],
        "measured": readings,
        "continuous_clearance_lower_bound_m": lower,
        "checks": {
            "closed_single_solids": True,
            "evaluated_vertices": True,
            "quarter_chord_parent_hinge": True,
            "shared_span_drivers": True,
            "continuous_sweep_clearance": True,
        },
        "limits": "49-edge faceted educational sections; no aerodynamic certification",
    }
