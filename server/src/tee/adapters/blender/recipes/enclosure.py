"""Standalone Blender 5.2 lesson: enclosure.

Run build(), then revise(), then inspect(); distances are SI metres in the scene.
Every mutation is scoped to tagged lesson objects; no file or network access.
Keep the retained cutters/driver parameters when saving an editable blend.
"""

import math

import bmesh
import bpy

OWNER = "tee.blender.lesson.enclosure.v1"
COLLECTION = "TEE Lesson — Enclosure"
PREFIX = "TEE Enclosure | "
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
    """Build a 120x80x30 mm open enclosure with a 3 mm shell and 15 vents."""
    _start()
    control = _object("Parameters")
    control["width_m"], control["height_m"], control["depth_m"] = 0.12, 0.08, 0.03
    control["stage"] = "built"
    body = _box("Enclosure")
    for axis, parameter in enumerate(("width_m", "height_m", "depth_m")):
        _drive(body, "scale", axis, parameter, "p")
    interior = _box("Interior cutter")
    interior.location = (0.003, 0.003, 0.003)
    for axis, parameter in enumerate(("width_m", "height_m", "depth_m")):
        _drive(interior, "scale", axis, parameter, "p-0.006" if axis < 2 else "p")
    _cut(body, interior)
    for x in range(5):
        for y in range(3):
            vent = _cylinder(f"Vent {x + 1} {y + 1}")
            vent.scale = (0.003, 0.003, 0.004)
            vent.location = (0, 0.02 * (y + 1), 0.0015)
            _drive(vent, "location", 0, "width_m", "p/2+" + repr(-0.04 + 0.02 * x))
            _cut(body, vent)
    _material(body)
    control.update_tag()
    bpy.context.view_layer.update()
    return inspect()


def revise():
    """Resize to 140x80x40 mm; the same drivers move the vent grid +10 mm."""
    control = _owned("Parameters")
    control["width_m"], control["depth_m"], control["stage"] = 0.14, 0.04, "revised"
    control.update_tag()
    bpy.context.view_layer.update()
    return inspect()


def inspect():
    """Measure the evaluated solid, complete vent walls and retained dependencies."""
    control, body = _owned("Parameters"), _owned("Enclosure")
    w, h, d = (float(control[k]) for k in ("width_m", "height_m", "depth_m"))
    bm = _mesh(body)
    stats = _stats(bm)
    removed = 15 * math.pi * 3**2 * 3
    analytic = w * h * d * 1e9 - (w - 0.006) * (h - 0.006) * (d - 0.003) * 1e9 - removed
    factor = math.sin(2 * math.pi / SEGMENTS) / (2 * math.pi / SEGMENTS)
    bound = removed * (1 - factor) + 0.1
    vents = []
    deps = []
    for x in range(5):
        for y in range(3):
            centre = (w / 2 - 0.04 + 0.02 * x, 0.02 * (y + 1), 0)
            vents.append(_bore(bm, centre, 0.003, 2, 0, 0.003))
            deps.append(
                _dependency(
                    _owned(f"Vent {x + 1} {y + 1}"),
                    "location",
                    0,
                    "width_m",
                    "p/2+" + repr(-0.04 + 0.02 * x),
                )
            )
    bm.free()
    interior = _owned("Interior cutter")
    for axis, parameter in enumerate(("width_m", "height_m", "depth_m")):
        deps.append(_dependency(body, "scale", axis, parameter, "p"))
        deps.append(_dependency(interior, "scale", axis, parameter, "p-0.006" if axis < 2 else "p"))
    checks = {
        "metre_scene_scale": math.isclose(bpy.context.scene.unit_settings.scale_length, 1.0),
        "one_closed_manifold_surface": stats["nonmanifold_edges"] == 0
        and stats["connected_components"] == 1,
        "dimensions_and_anchored_origin": all(
            _near(a, b, 0.001)
            for a, b in zip(
                stats["bbox_mm"] + stats["min_mm"],
                [w * 1000, h * 1000, d * 1000, 0, 0, 0],
                strict=True,
            )
        ),
        "volume_with_declared_polygon_bound": _near(stats["volume_mm3"], analytic, bound),
        "all_fifteen_complete_inner_vent_walls": all(vents),
        "live_width_height_depth_dependencies": all(deps),
        "retained_boolean_operations": len(body.modifiers) == 16
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
        "lesson": "enclosure",
        "stage": control["stage"],
        "collection": COLLECTION,
        "primary_objects": [body.name],
        "passed": all(checks.values()),
        "checks": checks,
        "measurements": {
            **stats,
            "analytic_volume_mm3": analytic,
            "mesh_error_bound_mm3": bound,
            "verified_vents": sum(vents),
            "first_vent_centre_mm": [w * 500 - 40, 20, 0],
            "wall_mm": 3,
        },
        "limits": "128-sided mesh bores; editable booleans and drivers, not exact CAD BRep.",
    }
