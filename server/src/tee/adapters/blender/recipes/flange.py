"""Standalone Blender 5.2 lesson: flange.

Run build(), then revise(), then inspect(); distances are SI metres in the scene.
Every mutation is scoped to tagged lesson objects; no file or network access.
Keep the retained cutters/driver parameters when saving an editable blend.
"""

import math

import bmesh
import bpy

OWNER = "tee.blender.lesson.flange.v1"
COLLECTION = "TEE Lesson — Flanged hub"
PREFIX = "TEE Flange | "
SEGMENTS = 128


def _collection():
    collection = bpy.data.collections.get(COLLECTION)
    if collection is None or collection.get("tee_lesson_owner") != OWNER:
        raise ValueError("Build this lesson first; its owned collection is required.")
    return collection


def _owned(label):
    obj = bpy.data.objects.get(PREFIX + label)
    if obj is None or obj.get("tee_lesson_owner") != OWNER or obj.name not in _collection().objects:
        raise ValueError("Lesson object missing or ownership changed: " + label)
    return obj


def _start():
    if not math.isclose(bpy.context.scene.unit_settings.scale_length, 1.0):
        raise ValueError("Use a scene with unit scale 1.0; this lesson uses metres directly.")
    if bpy.data.collections.get(COLLECTION) is not None:
        raise ValueError("Lesson collection already exists; use revise() or inspect().")
    if any(obj.name.startswith(PREFIX) for obj in bpy.data.objects):
        raise ValueError("Lesson object name collision; preserve the existing data.")
    collection = bpy.data.collections.new(COLLECTION)
    collection["tee_lesson_owner"] = OWNER
    bpy.context.scene.collection.children.link(collection)
    return collection


def _object(label, vertices=None, faces=None):
    mesh = None
    if vertices is not None:
        mesh = bpy.data.meshes.new(PREFIX + label)
        mesh["tee_lesson_owner"] = OWNER
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
    obj = bpy.data.objects.new(PREFIX + label, mesh)
    obj["tee_lesson_owner"] = OWNER
    _collection().objects.link(obj)
    return obj


def _box(label):
    return _object(
        label,
        [(x, y, z) for z in (0, 1) for y in (0, 1) for x in (0, 1)],
        [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)],
    )


def _cylinder(label, axis=2):
    vertices = []
    for length in (-1, 1):
        for i in range(SEGMENTS):
            angle = 2 * math.pi * i / SEGMENTS
            point = [math.cos(angle), math.sin(angle)]
            point.insert(axis, length)
            vertices.append(point)
    faces = [tuple(range(SEGMENTS)), tuple(range(SEGMENTS, 2 * SEGMENTS))]
    faces += [
        (i, (i + 1) % SEGMENTS, (i + 1) % SEGMENTS + SEGMENTS, i + SEGMENTS)
        for i in range(SEGMENTS)
    ]
    return _object(label, vertices, faces)


def _cut(body, cutter):
    cutter.hide_render = True
    cutter.display_type = "WIRE"
    cutter.hide_set(True)
    mod = body.modifiers.new("Editable cut: " + cutter.name, "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter


def _drive(obj, path, index, parameter, expression):
    curve = obj.driver_add(path, index)
    driver = curve.driver
    driver.type = "SCRIPTED"
    variable = driver.variables.new()
    variable.name = "p"
    variable.type = "SINGLE_PROP"
    variable.targets[0].id = _owned("Parameters")
    variable.targets[0].data_path = '["' + parameter + '"]'
    driver.expression = expression


def _dependency(obj, path, index, parameter, expression):
    curves = obj.animation_data.drivers if obj.animation_data else []
    for curve in curves:
        if curve.data_path == path and curve.array_index == index:
            driver = curve.driver
            return (
                driver.is_valid
                and not curve.mute
                and driver.expression == expression
                and len(driver.variables) == 1
                and driver.variables[0].targets[0].id == _owned("Parameters")
                and driver.variables[0].targets[0].data_path == '["' + parameter + '"]'
            )
    return False


def _mesh(obj):
    graph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(graph)
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.transform(evaluated.matrix_world)
    bm.normal_update()
    evaluated.to_mesh_clear()
    return bm


def _stats(bm):
    lo = [min(v.co[i] for v in bm.verts) * 1000 for i in range(3)]
    hi = [max(v.co[i] for v in bm.verts) * 1000 for i in range(3)]
    unseen = set(bm.verts)
    components = 0
    while unseen:
        components += 1
        pending = [unseen.pop()]
        while pending:
            vertex = pending.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in unseen:
                    unseen.remove(other)
                    pending.append(other)
    return {
        "connected_components": components,
        "volume_mm3": abs(bm.calc_volume(signed=True)) * 1e9,
        "bbox_mm": [hi[i] - lo[i] for i in range(3)],
        "min_mm": lo,
        "max_mm": hi,
        "nonmanifold_edges": sum(not e.is_manifold for e in bm.edges),
        "faces": len(bm.faces),
    }


def _bore(bm, centre, radius, axis, low, high):
    # Later booleans can split a facet into several faces. Group by facet normal;
    # require every angular strip, its full area and both rim planes.
    transverse = [i for i in range(3) if i != axis]
    step = 2 * math.pi / SEGMENTS
    groups = {}
    for face in bm.faces:
        if abs(face.normal[axis]) > 1e-4:
            continue
        if not all(
            radius * math.cos(step / 2) - 2e-7
            <= math.hypot(*(v.co[k] - centre[k] for k in transverse))
            <= radius + 2e-7
            for v in face.verts
        ):
            continue
        point = face.calc_center_median()
        if sum(face.normal[k] * (point[k] - centre[k]) for k in transverse) >= 0:
            continue
        angle = math.atan2(-face.normal[transverse[1]], -face.normal[transverse[0]])
        index = round((angle - step / 2) / step) % SEGMENTS
        groups.setdefault(index, []).append(face)
    expected_area = 2 * radius * math.sin(step / 2) * (high - low)
    return len(groups) == SEGMENTS and all(
        abs(sum(f.calc_area() for f in faces) - expected_area) < 2e-10
        and abs(min(v.co[axis] for f in faces for v in f.verts) - low) < 2e-7
        and abs(max(v.co[axis] for f in faces for v in f.verts) - high) < 2e-7
        for faces in groups.values()
    )


def _near(actual, expected, tolerance):
    return abs(actual - expected) <= tolerance


def _material(body):
    mat = bpy.data.materials.new(PREFIX + "Satin metal")
    mat["tee_lesson_owner"] = OWNER
    node = mat.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value = (0.17, 0.24, 0.30, 1)
    node.inputs["Metallic"].default_value = 0.65
    node.inputs["Roughness"].default_value = 0.28
    body.data.materials.append(mat)


def build():
    """Build a stepped x-axis hub, central bore and six holes on 60 mm PCD."""
    _start()
    control = _object("Parameters")
    control["bore_diameter_m"], control["mount_diameter_m"] = 0.012, 0.006
    control["stage"] = "built"
    vertices = [
        (x, r * math.cos(2 * math.pi * i / SEGMENTS), r * math.sin(2 * math.pi * i / SEGMENTS))
        for x, r in ((0, 0.04), (0.008, 0.04), (0.008, 0.02), (0.032, 0.02))
        for i in range(SEGMENTS)
    ]
    faces = [tuple(range(SEGMENTS)), tuple(range(3 * SEGMENTS, 4 * SEGMENTS))]
    for ring in range(3):
        faces += [
            (
                ring * SEGMENTS + i,
                ring * SEGMENTS + (i + 1) % SEGMENTS,
                (ring + 1) * SEGMENTS + (i + 1) % SEGMENTS,
                (ring + 1) * SEGMENTS + i,
            )
            for i in range(SEGMENTS)
        ]
    body = _object("Flanged hub", vertices, faces)
    bore = _cylinder("Central bore cutter", axis=0)
    bore.scale, bore.location = (0.018, 1, 1), (0.016, 0, 0)
    for axis in (1, 2):
        _drive(bore, "scale", axis, "bore_diameter_m", "p/2")
    _cut(body, bore)
    for i in range(6):
        angle = 2 * math.pi * i / 6
        cutter = _cylinder(f"Mount cutter {i + 1}", axis=0)
        cutter.location = (0.004, 0.03 * math.cos(angle), 0.03 * math.sin(angle))
        cutter.scale = (0.006, 1, 1)
        for axis in (1, 2):
            _drive(cutter, "scale", axis, "mount_diameter_m", "p/2")
        _cut(body, cutter)
    _material(body)
    control.update_tag()
    bpy.context.view_layer.update()
    return inspect()


def revise():
    """Grow the central bore 12→16 mm and all six mount bores 6→8 mm."""
    control = _owned("Parameters")
    control["bore_diameter_m"], control["mount_diameter_m"] = 0.016, 0.008
    control["stage"] = "revised"
    control.update_tag()
    bpy.context.view_layer.update()
    return inspect()


def inspect():
    control, body = _owned("Parameters"), _owned("Flanged hub")
    bore, mount = control["bore_diameter_m"] / 2, control["mount_diameter_m"] / 2
    bm = _mesh(body)
    stats = _stats(bm)
    holes = [_bore(bm, (0, 0, 0), bore, 0, 0, 0.032)]
    deps = [
        _dependency(_owned("Central bore cutter"), "scale", i, "bore_diameter_m", "p/2")
        for i in (1, 2)
    ]
    for i in range(6):
        angle = 2 * math.pi * i / 6
        holes.append(
            _bore(bm, (0, 0.03 * math.cos(angle), 0.03 * math.sin(angle)), mount, 0, 0, 0.008)
        )
        deps += [
            _dependency(_owned(f"Mount cutter {i + 1}"), "scale", j, "mount_diameter_m", "p/2")
            for j in (1, 2)
        ]
    bm.free()
    gross = math.pi * (40**2 * 8 + 20**2 * 24)
    removed = math.pi * ((bore * 1000) ** 2 * 32 + 6 * (mount * 1000) ** 2 * 8)
    analytic = gross - removed
    factor = math.sin(2 * math.pi / SEGMENTS) / (2 * math.pi / SEGMENTS)
    bound = (gross + removed) * (1 - factor) + 0.1
    checks = {
        "metre_scene_scale": math.isclose(bpy.context.scene.unit_settings.scale_length, 1.0),
        "closed_manifold": stats["nonmanifold_edges"] == 0 and stats["connected_components"] == 1,
        "bounds_and_x_axis_placement": all(
            _near(a, b, 0.001)
            for a, b in zip(
                stats["bbox_mm"] + stats["min_mm"], [32, 80, 80, 0, -40, -40], strict=True
            )
        ),
        "volume_with_declared_polygon_bound": _near(stats["volume_mm3"], analytic, bound),
        "central_and_six_complete_mount_bores": all(holes),
        "both_diameter_drivers_retained": all(deps),
        "seven_retained_boolean_operations": len(body.modifiers) == 7
        and all(
            m.type == "BOOLEAN"
            and m.operation == "DIFFERENCE"
            and m.show_viewport
            and m.show_render
            and m.object is not None
            and m.object.get("tee_lesson_owner") == OWNER
            for m in body.modifiers
        ),
    }
    return {
        "lesson": "flange",
        "stage": control["stage"],
        "collection": COLLECTION,
        "primary_objects": [body.name],
        "passed": all(checks.values()),
        "checks": checks,
        "measurements": {
            **stats,
            "analytic_volume_mm3": analytic,
            "mesh_error_bound_mm3": bound,
            "verified_bores": sum(holes),
            "bore_diameter_mm": bore * 2000,
            "mount_diameter_mm": mount * 2000,
            "pitch_circle_diameter_mm": 60,
        },
        "limits": "128-sided mesh circles; stepped profile is editable mesh, not a CAD revolve.",
    }
