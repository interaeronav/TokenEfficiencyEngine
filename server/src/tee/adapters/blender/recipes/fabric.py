"""Two woven-fabric material studies on authored, metrically checked folds.

The folds are analytic display geometry, not cloth simulation. UVs preserve
metres of the flat pattern on every base triangle. The enlarged weave and
shader values are authored teaching choices, not measured textile properties.
"""

import hashlib
import math

import bmesh
import bpy

COLLECTION = "TEE Lesson — Fabric"
TAG = "tee.lesson.fabric.v1"
ROLES = ("linen", "indigo cotton")
WIDTH = 0.45
HEIGHT = 0.6
NX = 32
NZ = 40
DRIVERS = (
    ("Weave pitch", "Scale", "pitch", "1/pitch"),
    ("Principled BSDF", "Roughness", "roughness", "roughness"),
    ("Principled BSDF", "Sheen Weight", "sheen", "sheen"),
    ("Principled BSDF", "Sheen Roughness", "sheen_roughness", "sheen_roughness"),
)
LINKS = (
    ("Pattern metres", "UV", "Weave pitch", "Vector"),
    ("Weave pitch", "Vector", "Crossing yarns", "Vector"),
    ("Weave pitch", "Vector", "Warp ridges", "Vector"),
    ("Weave pitch", "Vector", "Weft ridges", "Vector"),
    ("Crossing yarns", "Color", "Principled BSDF", "Base Color"),
    ("Crossing yarns", "Factor", "Over under relief", "Factor"),
    ("Warp ridges", "Color", "Over under relief", "Color1"),
    ("Weft ridges", "Color", "Over under relief", "Color2"),
    ("Over under relief", "Color", "Yarn relief", "Height"),
    ("Yarn relief", "Normal", "Principled BSDF", "Normal"),
    ("Principled BSDF", "BSDF", "Material Output", "Surface"),
)


def _require_metres():
    if abs(bpy.context.scene.unit_settings.scale_length - 1) > 1e-9:
        raise ValueError("Fabric lesson requires scene unit scale 1 metre")


def _owned():
    collection = bpy.data.collections.get(COLLECTION)
    if collection is None or collection.get("tee_lesson") != TAG:
        raise ValueError("Build the owned fabric lesson first")
    return collection


def _object(role):
    found = [
        o for o in _owned().objects if o.get("lesson_role") == role and o.get("tee_lesson") == TAG
    ]
    if len(found) != 1:
        raise ValueError("Fabric role must resolve exactly once: " + role)
    return found[0]


def _inventory_errors():
    collection = _owned()
    objects = list(collection.objects)
    expected = set(ROLES) | {"controls"}
    roles = [str(o.get("lesson_role", "")) for o in objects]
    errors = []
    if len(objects) != 3 or set(roles) != expected or collection.children:
        errors.append("Expected exactly two fabric meshes and one controller")
    for obj in objects:
        if obj.get("tee_lesson") != TAG or list(obj.users_collection) != [collection]:
            errors.append("Foreign or shared collection member: " + obj.name)
        if obj.get("lesson_role") == "controls":
            if obj.type != "EMPTY":
                errors.append("Controller must remain an empty")
        elif obj.get("lesson_role") in ROLES:
            if obj.type != "MESH" or obj.data.users != 1:
                errors.append("Foreign or shared fabric mesh: " + obj.name)
            elif (
                len(obj.data.materials) != 1
                or obj.data.materials[0] is None
                or obj.data.materials[0].get("tee_lesson") != TAG
                or obj.data.materials[0].users != 1
            ):
                errors.append("Foreign or shared fabric material: " + obj.name)
    return errors


def _control_errors(controller):
    errors = []
    for parameter in ("pitch", "roughness", "sheen", "sheen_roughness"):
        value = controller.get(parameter)
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            errors.append(parameter + ": expected a finite number")
        elif parameter == "pitch" and not 0 < value <= 0.1:
            errors.append("pitch: expected a positive yarn cell width at most 0.1 m")
        elif parameter != "pitch" and not 0 <= value <= 1:
            errors.append(parameter + ": expected a value between 0 and 1")
    return errors


def _shader_setting_errors(tree, role):
    errors = []
    types = {
        "Pattern metres": "ShaderNodeUVMap",
        "Weave pitch": "ShaderNodeVectorMath",
        "Crossing yarns": "ShaderNodeTexChecker",
        "Warp ridges": "ShaderNodeTexWave",
        "Weft ridges": "ShaderNodeTexWave",
        "Over under relief": "ShaderNodeMixRGB",
        "Yarn relief": "ShaderNodeBump",
        "Principled BSDF": "ShaderNodeBsdfPrincipled",
        "Material Output": "ShaderNodeOutputMaterial",
    }
    for name, node_type in types.items():
        node = tree.nodes.get(name)
        if node is None or node.bl_idname != node_type:
            errors.append(name + ": wrong or missing node type")
    if errors:
        return errors
    expected_properties = (
        ("Pattern metres", "uv_map", "FabricUV"),
        ("Weave pitch", "operation", "SCALE"),
        ("Warp ridges", "wave_type", "BANDS"),
        ("Warp ridges", "bands_direction", "X"),
        ("Weft ridges", "wave_type", "BANDS"),
        ("Weft ridges", "bands_direction", "Y"),
        ("Warp ridges", "wave_profile", "SIN"),
        ("Weft ridges", "wave_profile", "SIN"),
        ("Over under relief", "blend_type", "MIX"),
        ("Yarn relief", "invert", False),
    )
    for node_name, property_name, expected in expected_properties:
        if getattr(tree.nodes[node_name], property_name) != expected:
            errors.append(node_name + ": changed " + property_name)
    expected_inputs = (
        ("Crossing yarns", "Scale", 1),
        ("Warp ridges", "Scale", 1.5),
        ("Weft ridges", "Scale", 1.5),
        ("Warp ridges", "Distortion", 0.15),
        ("Weft ridges", "Distortion", 0.15),
        ("Yarn relief", "Strength", 0.3),
        ("Yarn relief", "Distance", 0.00018),
        ("Principled BSDF", "Metallic", 0),
        ("Principled BSDF", "Alpha", 1),
        ("Principled BSDF", "Transmission Weight", 0),
        ("Principled BSDF", "Coat Weight", 0),
    )
    for node_name, socket_name, expected in expected_inputs:
        socket = tree.nodes[node_name].inputs[socket_name]
        if socket.is_linked or abs(socket.default_value - expected) > max(
            1e-8, abs(expected) * 2e-7
        ):
            errors.append(node_name + ": changed or linked " + socket_name)
    color = (0.60, 0.39, 0.19) if role == "linen" else (0.025, 0.09, 0.22)
    for name, expected in (
        ("Color1", (*color, 1)),
        ("Color2", (*(value * 0.72 for value in color), 1)),
    ):
        socket = tree.nodes["Crossing yarns"].inputs[name]
        if socket.is_linked or any(
            abs(a - b) > 1e-6 for a, b in zip(socket.default_value, expected, strict=True)
        ):
            errors.append("Crossing yarns: changed or linked " + name)
    return errors


def _drive(socket, parameter, expression):
    driver = socket.driver_add("default_value").driver
    driver.type = "SCRIPTED"
    variable = driver.variables.new()
    variable.name = parameter
    variable.type = "SINGLE_PROP"
    variable.targets[0].id = _object("controls")
    variable.targets[0].data_path = '["' + parameter + '"]'
    driver.expression = expression


def _shader(role, color):
    material = bpy.data.materials.new("Fabric — " + role)
    material["tee_lesson"] = TAG
    tree = material.node_tree
    shader = tree.nodes.get("Principled BSDF")
    shader.inputs["Metallic"].default_value = 0
    shader.inputs["Sheen Tint"].default_value = (0.82, 0.84, 0.88, 1)
    for kind, name in (
        ("ShaderNodeUVMap", "Pattern metres"),
        ("ShaderNodeVectorMath", "Weave pitch"),
        ("ShaderNodeTexChecker", "Crossing yarns"),
        ("ShaderNodeTexWave", "Warp ridges"),
        ("ShaderNodeTexWave", "Weft ridges"),
        ("ShaderNodeMixRGB", "Over under relief"),
        ("ShaderNodeBump", "Yarn relief"),
    ):
        node = tree.nodes.new(kind)
        node.name = node.label = name
    tree.nodes["Pattern metres"].uv_map = "FabricUV"
    tree.nodes["Weave pitch"].operation = "SCALE"
    checker = tree.nodes["Crossing yarns"]
    checker.inputs["Scale"].default_value = 1
    checker.inputs["Color1"].default_value = (*color, 1)
    checker.inputs["Color2"].default_value = (*(value * 0.72 for value in color), 1)
    for name, axis in (("Warp ridges", "X"), ("Weft ridges", "Y")):
        wave = tree.nodes[name]
        wave.wave_type = "BANDS"
        wave.bands_direction = axis
        wave.wave_profile = "SIN"
        wave.inputs["Scale"].default_value = 1.5
        wave.inputs["Distortion"].default_value = 0.15
    tree.nodes["Over under relief"].blend_type = "MIX"
    bump = tree.nodes["Yarn relief"]
    bump.inputs["Strength"].default_value = 0.3
    bump.inputs["Distance"].default_value = 0.00018
    for source, output, target, input_name in LINKS:
        tree.links.new(tree.nodes[source].outputs[output], tree.nodes[target].inputs[input_name])
    for node, socket, parameter, expression in DRIVERS:
        _drive(tree.nodes[node].inputs[socket], parameter, expression)
    return material


def _folded_grid(role, x, material):
    # Integrate unit tangents with a fixed arc step: every horizontal segment
    # remains WIDTH/NX metres, so the triangulated display is intrinsically flat.
    curve = [(0.0, 0.0)]
    for i in range(NX):
        angle = 0.65 * math.sin(6 * math.pi * (i + 0.5) / NX)
        px, py = curve[-1]
        curve.append((px + WIDTH / NX * math.cos(angle), py + WIDTH / NX * math.sin(angle)))
    center_x = curve[-1][0] / 2
    center_y = (max(y for _, y in curve) + min(y for _, y in curve)) / 2
    vertices = [
        (px - center_x, py - center_y, HEIGHT * j / NZ) for j in range(NZ + 1) for px, py in curve
    ]
    faces = []
    for j in range(NZ):
        for i in range(NX):
            a = j * (NX + 1) + i
            b, c, d = a + 1, a + NX + 1, a + NX + 2
            faces.extend(((a, b, d), (a, d, c)))
    mesh = bpy.data.meshes.new("Fabric — " + role)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name="FabricUV")
    for loop in mesh.loops:
        index = loop.vertex_index
        uv.data[loop.index].uv = (
            (index % (NX + 1)) * WIDTH / NX,
            (index // (NX + 1)) * HEIGHT / NZ,
        )
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new("Fabric — " + role, mesh)
    _owned().objects.link(obj)
    obj.location = (x, 0, 0.08)
    obj["tee_lesson"] = TAG
    obj["lesson_role"] = role
    obj.data.materials.append(material)
    solidify = obj.modifiers.new("Presentation thickness 1 mm", "SOLIDIFY")
    solidify.thickness = 0.001
    solidify.offset = 0
    solidify.use_rim = True
    return obj


def _geometry_signature():
    values = []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for role in ROLES:
        obj = _object(role).evaluated_get(depsgraph)
        values.extend(round(value, 8) for row in obj.matrix_world for value in row)
        values.extend(round(value, 8) for vertex in obj.data.vertices for value in vertex.co)
        values.extend(loop.vertex_index for loop in obj.data.loops)
    return hashlib.sha256(repr(values).encode()).hexdigest()


def _result(stage):
    return {
        "stage": stage,
        "collection": COLLECTION,
        "units": "m",
        "primary_objects": [_object(role).name for role in ROLES],
        "presentation": {"camera": [0.9, -1.8, 0.9], "target": [0, 0, 0.38]},
        "limitations": [
            "Authored folds, not cloth simulation or calibrated textile mechanics",
            "Enlarged weave and shader values are authored, not measured BRDF data",
            "Solidify gives approximate presentation thickness, not a thickness certification",
            "Native procedural materials require baking or recreation "
            "for neutral appearance export",
        ],
    }


def build():
    _require_metres()
    if bpy.data.collections.get(COLLECTION) is not None:
        raise ValueError("Fabric lesson already exists; revise it instead")
    collection = bpy.data.collections.new(COLLECTION)
    collection["tee_lesson"] = TAG
    bpy.context.scene.collection.children.link(collection)
    controller = bpy.data.objects.new("Fabric — controls", None)
    collection.objects.link(controller)
    controller["tee_lesson"] = TAG
    controller["lesson_role"] = "controls"
    for key, value in {
        "pitch": 0.004,
        "roughness": 0.65,
        "sheen": 0.3,
        "sheen_roughness": 0.7,
    }.items():
        controller[key] = value
    controller["stage"] = "built"
    for role, x, color in (
        ("linen", -0.27, (0.60, 0.39, 0.19)),
        ("indigo cotton", 0.27, (0.025, 0.09, 0.22)),
    ):
        _folded_grid(role, x, _shader(role, color))
    bpy.context.view_layer.update()
    controller["geometry_signature"] = _geometry_signature()
    return inspect()


def revise():
    _require_metres()
    if not inspect()["passed"]:
        raise ValueError("Repair failed fabric checks before changing owned controls")
    controller = _object("controls")
    for key, value in {
        "pitch": 0.006,
        "roughness": 0.45,
        "sheen": 0.6,
        "sheen_roughness": 0.4,
    }.items():
        controller[key] = value
    controller["stage"] = "revised"
    controller.update_tag()
    bpy.context.view_layer.update()
    return inspect()


def inspect():
    bpy.context.view_layer.update()
    errors = _inventory_errors()
    if errors:
        return {
            "stage": "invalid",
            "collection": COLLECTION,
            "primary_objects": [],
            "passed": False,
            "checks": {"exact_owned_inventory": {"passed": False, "measured": {"errors": errors}}},
        }
    controller = _object("controls")
    depsgraph = bpy.context.evaluated_depsgraph_get()
    checks = {}

    def record(name, passed, measured):
        checks[name] = {"passed": bool(passed), "measured": measured}

    record("exact_owned_inventory", True, {"mesh_roles": 2, "controllers": 1})
    control_errors = _control_errors(controller)
    record("finite_physical_controls", not control_errors, {"errors": control_errors})
    if control_errors:
        return {
            **_result(str(controller.get("stage", "invalid"))),
            "passed": False,
            "checks": checks,
        }
    record(
        "metre_scene_scale",
        abs(bpy.context.scene.unit_settings.scale_length - 1) < 1e-9,
        {"scale_length": bpy.context.scene.unit_settings.scale_length},
    )
    identity_error = max(
        abs(controller.matrix_world[i][j] - (1 if i == j else 0))
        for i in range(4)
        for j in range(4)
    )
    record(
        "identity_controller",
        identity_error < 1e-7 and controller.parent is None,
        {"max_error": identity_error},
    )
    signature = _geometry_signature()
    record(
        "geometry_unchanged",
        signature == controller.get("geometry_signature"),
        {"sha256": signature},
    )
    for role in ROLES:
        obj = _object(role)
        mesh = obj.data
        visible = (
            not obj.hide_render
            and not obj.hide_viewport
            and not obj.hide_get()
            and obj.visible_camera
            and not _owned().hide_render
            and not _owned().hide_viewport
        )
        assigned = all(polygon.material_index == 0 for polygon in mesh.polygons)
        record(
            role + "_visible_material_assignment",
            visible and assigned,
            {"visible": visible, "all_faces_use_owned_material": assigned},
        )
        uv = mesh.uv_layers.get("FabricUV")
        uv_errors, metric_errors = [], []
        if uv is not None:
            for loop in mesh.loops:
                index = loop.vertex_index
                expected = ((index % (NX + 1)) * WIDTH / NX, (index // (NX + 1)) * HEIGHT / NZ)
                uv_errors.extend(abs(uv.data[loop.index].uv[i] - expected[i]) for i in range(2))
            for polygon in mesh.polygons:
                for i in range(3):
                    a, b = polygon.loop_indices[i], polygon.loop_indices[(i + 1) % 3]
                    pa = mesh.vertices[mesh.loops[a].vertex_index].co
                    pb = mesh.vertices[mesh.loops[b].vertex_index].co
                    metric_errors.append(
                        abs((pa - pb).length - (uv.data[a].uv - uv.data[b].uv).length)
                    )
        surface_area = sum(p.area for p in mesh.polygons)
        record(
            role + "_metre_uv_metric",
            uv is not None
            and bool(uv_errors)
            and max(uv_errors) < 1e-6
            and max(metric_errors) < 1e-6
            and abs(surface_area - WIDTH * HEIGHT) < 1e-6,
            {
                "max_uv_error_m": max(uv_errors, default=1),
                "max_edge_metric_error_m": max(metric_errors, default=1),
                "surface_area_m2": surface_area,
            },
        )
        bm = bmesh.new()
        bm.from_mesh(mesh)
        boundary_edges = sum(edge.is_boundary for edge in bm.edges)
        base_valid = (
            len(bm.verts) == (NX + 1) * (NZ + 1)
            and len(bm.faces) == 2 * NX * NZ
            and boundary_edges == 2 * (NX + NZ)
            and all(
                edge.is_boundary or (edge.is_manifold and edge.is_contiguous) for edge in bm.edges
            )
            and all(face.calc_area() > 1e-12 for face in bm.faces)
        )
        bm.free()
        evaluated = obj.evaluated_get(depsgraph)
        bm = bmesh.new()
        bm.from_mesh(evaluated.data)
        volume = bm.calc_volume() * evaluated.matrix_world.to_3x3().determinant()
        closed = all(edge.is_manifold and edge.is_contiguous for edge in bm.edges)
        bm.free()
        modifier = obj.modifiers.get("Presentation thickness 1 mm")
        modifier_valid = (
            len(obj.modifiers) == 1
            and modifier is not None
            and modifier.type == "SOLIDIFY"
            and modifier.show_viewport
            and modifier.show_render
            and modifier.use_rim
            and abs(modifier.thickness - 0.001) < 1e-9
            and modifier.offset == 0
        )
        record(
            role + "_fabric_geometry",
            base_valid and closed and volume > 0 and modifier_valid,
            {
                "base_vertices": len(mesh.vertices),
                "base_triangles": len(mesh.polygons),
                "boundary_edges": boundary_edges,
                "closed_evaluated": closed,
                "volume_m3": volume,
            },
        )
        tree = obj.data.materials[0].node_tree
        setting_errors = _shader_setting_errors(tree, role)
        record(
            role + "_authored_shader_settings",
            not setting_errors,
            {
                "errors": setting_errors,
                "yarn_cell_width_m": float(controller["pitch"]),
                "two_colour_repeat_m": 2 * float(controller["pitch"]),
            },
        )
        actual = {
            (link.from_node.name, link.from_socket.name, link.to_node.name, link.to_socket.name)
            for link in tree.links
        }
        missing = [list(link) for link in LINKS if link not in actual]
        required = {name for link in LINKS for name in (link[0], link[2])}
        inactive = [
            name for name in required if tree.nodes.get(name) is None or tree.nodes[name].mute
        ]
        output = tree.nodes.get("Material Output")
        output_active = output is not None and output.is_active_output and output.target == "ALL"
        uv_node = tree.nodes.get("Pattern metres")
        record(
            role + "_shader_links",
            not missing
            and not inactive
            and output_active
            and uv_node is not None
            and uv_node.uv_map == "FabricUV",
            {"missing": missing, "inactive": inactive, "active_surface": output_active},
        )
        driver_errors, expected_paths = [], set()
        curves = list(tree.animation_data.drivers) if tree.animation_data else []
        for node_name, socket_name, parameter, expression in DRIVERS:
            node = tree.nodes.get(node_name)
            socket = node.inputs.get(socket_name) if node else None
            if socket is None:
                driver_errors.append(parameter + ": missing socket")
                continue
            path = socket.path_from_id("default_value")
            expected_paths.add((path, 0))
            matching = [f for f in curves if f.data_path == path and f.array_index == 0]
            if len(matching) != 1:
                driver_errors.append(parameter + ": missing driver")
                continue
            curve = matching[0]
            driver = curve.driver
            variables = list(driver.variables)
            expected_value = (
                1 / controller[parameter] if parameter == "pitch" else controller[parameter]
            )
            valid = (
                not curve.mute
                and driver.is_valid
                and driver.type == "SCRIPTED"
                and driver.expression == expression
                and len(variables) == 1
                and abs(socket.default_value - expected_value)
                < max(1e-6, abs(expected_value) * 2e-7)
            )
            if valid:
                variable = variables[0]
                valid = (
                    variable.name == parameter
                    and variable.type == "SINGLE_PROP"
                    and len(variable.targets) == 1
                    and variable.targets[0].id == controller
                    and variable.targets[0].data_path == '["' + parameter + '"]'
                )
            if not valid:
                driver_errors.append(parameter + ": inactive, foreign or changed driver")
        if len(curves) != 4 or {(f.data_path, f.array_index) for f in curves} != expected_paths:
            driver_errors.append("unexpected driver inventory")
        record(role + "_live_shader_drivers", not driver_errors, {"errors": driver_errors})
    return {
        **_result(str(controller["stage"])),
        "passed": all(c["passed"] for c in checks.values()),
        "checks": checks,
        "authored_controls": {
            name: float(controller[name])
            for name in ("pitch", "roughness", "sheen", "sheen_roughness")
        },
    }
