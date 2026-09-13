"""Standalone Blender 5.2 lesson: joint.

Run build(), then revise(), then inspect(); distances are SI metres in the scene.
Every mutation is scoped to tagged lesson objects; no file or network access.
Keep the retained cutters/driver parameters when saving an editable blend.
"""

import math

import bmesh
import bpy
from mathutils import Vector

OWNER = "tee.blender.lesson.joint.v1"
COLLECTION = "TEE Lesson — Revolute lever"
PREFIX = "TEE Joint | "
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
    """Build a 40x30x8 mm base and a 60x12x4 mm lever with 2 mm gap."""
    _start()
    control = _object("Parameters")
    control["angle_deg"], control["stage"] = 0.0, "built"
    base = _box("Base")
    base.scale, base.location = (0.04, 0.03, 0.008), (-0.02, -0.015, 0)
    lever = _box("Lever")
    # Centre the mesh at its true hinge, rather than rotating an offset object origin.
    for vertex in lever.data.vertices:
        vertex.co.x = (vertex.co.x - 0.5) * 0.06
        vertex.co.y = (vertex.co.y - 0.5) * 0.012
        vertex.co.z *= 0.004
    lever.location = (0, 0, 0.010)
    _drive(lever, "rotation_euler", 2, "angle_deg", "p*pi/180")
    _material(base)
    _material(lever)
    control.update_tag()
    bpy.context.view_layer.update()
    return inspect()


def revise():
    """Measure every pose of the 0/45/90/0/45 degree sweep, keeping the final 45°."""
    control = _owned("Parameters")
    samples = []
    for angle in (0, 45, 90, 0, 45):
        control["angle_deg"], control["stage"] = float(angle), "revised"
        control.update_tag()
        bpy.context.view_layer.update()
        row = inspect()
        samples.append(
            {
                "angle_deg": angle,
                "passed": row["passed"],
                "lever_bbox_mm": row["measurements"]["lever"]["bbox_mm"],
                "gap_mm": row["measurements"]["gap_mm"],
            }
        )
    result = inspect()
    result["motion_samples"] = samples
    result["checks"]["all_measured_sweep_poses"] = all(row["passed"] for row in samples)
    result["passed"] = all(result["checks"].values())
    return result


def inspect():
    control, base, lever = _owned("Parameters"), _owned("Base"), _owned("Lever")
    base_mesh, lever_mesh = _mesh(base), _mesh(lever)
    base_stats, lever_stats = _stats(base_mesh), _stats(lever_mesh)
    angle = math.radians(float(control["angle_deg"]))
    expected = [
        abs(60 * math.cos(angle)) + abs(12 * math.sin(angle)),
        abs(60 * math.sin(angle)) + abs(12 * math.cos(angle)),
        4,
    ]
    gap = lever_stats["min_mm"][2] - base_stats["max_mm"][2]
    # Compare the identity of the long-edge endpoints after evaluated world transformation.
    target = Vector(
        (
            0.03 * math.cos(angle) + 0.006 * math.sin(angle),
            0.03 * math.sin(angle) - 0.006 * math.cos(angle),
            0.010,
        )
    )
    endpoint_error = min((v.co - target).length for v in lever_mesh.verts) * 1000
    base_mesh.free()
    lever_mesh.free()
    checks = {
        "metre_scene_scale": math.isclose(bpy.context.scene.unit_settings.scale_length, 1.0),
        "two_closed_manifold_bodies": base_stats["nonmanifold_edges"] == 0
        and lever_stats["nonmanifold_edges"] == 0
        and base_stats["connected_components"] == lever_stats["connected_components"] == 1,
        "base_anchored_and_unchanged": all(
            _near(a, b, 0.001)
            for a, b in zip(
                base_stats["bbox_mm"] + base_stats["min_mm"], [40, 30, 8, -20, -15, 0], strict=True
            )
        ),
        "individual_solid_volumes": _near(base_stats["volume_mm3"], 9600, 0.02)
        and _near(lever_stats["volume_mm3"], 2880, 0.02),
        "two_mm_clearance": _near(gap, 2, 0.001),
        "evaluated_world_rotation": endpoint_error < 0.001
        and all(_near(a, b, 0.001) for a, b in zip(lever_stats["bbox_mm"], expected, strict=True)),
        "live_hinge_driver": _dependency(lever, "rotation_euler", 2, "angle_deg", "p*pi/180"),
    }
    return {
        "lesson": "joint",
        "stage": control["stage"],
        "collection": COLLECTION,
        "primary_objects": [base.name, lever.name],
        "passed": all(checks.values()),
        "checks": checks,
        "measurements": {
            "base": base_stats,
            "lever": lever_stats,
            "angle_deg": float(control["angle_deg"]),
            "gap_mm": gap,
            "long_edge_endpoint_error_mm": endpoint_error,
            "mesh_error_bound_mm3": 0.02,
        },
        "limits": "Editable kinematic driver; no bearing, loads or physics constraint claimed.",
    }
