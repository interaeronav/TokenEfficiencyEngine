"""A portable texture workshop: metre-based brick, carbon weave, UV/data maps.

Authored render studies, not measured BRDFs or a laminate specification. Call
build(), inspect(), revise(), inspect(). Generated pixels are packed in the
blend; no image files, downloads, remote APIs or material libraries are used.
"""

import math

import bmesh
import bpy

COLLECTION = "TEE Lesson — Textures"
TAG = "tee.lesson.textures.v1"
IMAGE_SIZE = 128


def _owned():
    collection = bpy.data.collections.get(COLLECTION)
    if collection is None or collection.get("tee_lesson") != TAG:
        raise ValueError("Build the owned texture workshop first")
    return collection


def _object(role):
    matches = [
        o for o in _owned().objects if o.get("lesson_role") == role and o.get("tee_lesson") == TAG
    ]
    if len(matches) != 1:
        raise ValueError("Texture role must resolve exactly once: " + role)
    return matches[0]


def _require_metres():
    if abs(bpy.context.scene.unit_settings.scale_length - 1.0) > 1e-9:
        raise ValueError(
            "Texture lesson requires scene unit scale 1 metre before build or revision"
        )


def _inventory_errors():
    collection = _owned()
    objects = list(collection.objects)
    expected = {"controls", "brick", "carbon", "uv_normal"}
    roles = [str(obj.get("lesson_role", "")) for obj in objects]
    errors = []
    if len(objects) != 4 or set(roles) != expected:
        errors.append(
            {
                "missing": sorted(expected - set(roles)),
                "extra": sorted(set(roles) - expected),
                "object_count": len(objects),
            }
        )
    if len(collection.children):
        errors.append({"unexpected_child_collections": len(collection.children)})
    for obj in objects:
        role = str(obj.get("lesson_role", ""))
        if obj.get("tee_lesson") != TAG or list(obj.users_collection) != [collection]:
            errors.append({"ownership": obj.name})
        if role == "controls":
            if obj.type != "EMPTY":
                errors.append({"controller_type": obj.type})
        elif role in expected:
            if obj.type != "MESH" or obj.data.users != 1:
                errors.append({"mesh_type_or_sharing": role})
            elif (
                len(obj.data.materials) != 1
                or obj.data.materials[0] is None
                or obj.data.materials[0].get("tee_lesson") != TAG
                or obj.data.materials[0].users != 1
            ):
                errors.append({"foreign_or_shared_material": role})
    return errors


def _driver_contract(controller):
    contracts = (
        ("brick", "Physical scale", "Scale", "brick_scale", "brick_scale"),
        ("brick", "Principled BSDF", "Roughness", "brick_roughness", "brick_roughness"),
        ("carbon", "Tow pitch in metres", "Scale", "carbon_pitch", "1/carbon_pitch"),
        ("carbon", "Principled BSDF", "Roughness", "carbon_roughness", "carbon_roughness"),
        ("uv_normal", "Image tile size in metres", "Scale", "image_tile", "1/image_tile"),
    )
    expected_paths = {role: set() for role in ("brick", "carbon", "uv_normal")}
    errors = []
    for role, node_name, socket_name, parameter, expression in contracts:
        tree = _material(role).node_tree
        node = tree.nodes.get(node_name)
        socket = node.inputs.get(socket_name) if node is not None else None
        if socket is None:
            errors.append({"parameter": parameter, "defect": "missing driven socket"})
            continue
        path = socket.path_from_id("default_value")
        expected_paths[role].add((path, 0))
        curves = list(tree.animation_data.drivers) if tree.animation_data else []
        matching = [curve for curve in curves if curve.data_path == path and curve.array_index == 0]
        if len(matching) != 1:
            errors.append({"parameter": parameter, "defect": "missing or duplicate driver"})
            continue
        curve = matching[0]
        driver = curve.driver
        variables = list(driver.variables)
        if (
            curve.mute
            or not driver.is_valid
            or driver.type != "SCRIPTED"
            or driver.expression != expression
            or len(variables) != 1
        ):
            errors.append({"parameter": parameter, "defect": "inactive or changed driver"})
            continue
        variable = variables[0]
        if (
            variable.name != parameter
            or variable.type != "SINGLE_PROP"
            or len(variable.targets) != 1
            or variable.targets[0].id != controller
            or variable.targets[0].data_path != '["' + parameter + '"]'
        ):
            errors.append(
                {"parameter": parameter, "defect": "foreign or changed controller binding"}
            )
    for role, paths in expected_paths.items():
        tree = _material(role).node_tree
        curves = list(tree.animation_data.drivers) if tree.animation_data else []
        if len(curves) != len(paths) or {(c.data_path, c.array_index) for c in curves} != paths:
            errors.append({"role": role, "defect": "unexpected shader driver inventory"})
    return errors


def _material(role):
    return _object(role).data.materials[0]


def _node(material, kind, name):
    node = material.node_tree.nodes.new(kind)
    node.name = name
    node.label = name
    return node


def _link(material, source, output, target, input_name):
    material.node_tree.links.new(source.outputs[output], target.inputs[input_name])


def _driver(socket, expression, *parameters):
    curve = socket.driver_add("default_value")
    driver = curve.driver
    driver.type = "SCRIPTED"
    for parameter in parameters:
        variable = driver.variables.new()
        variable.name = parameter
        variable.type = "SINGLE_PROP"
        variable.targets[0].id = _object("controls")
        variable.targets[0].data_path = '["' + parameter + '"]'
    driver.expression = expression


def _new_material(role):
    material = bpy.data.materials.new("Textures — " + role)
    material["tee_lesson"] = TAG
    return material


def _coordinates(material):
    coord = _node(material, "ShaderNodeTexCoord", "Metre coordinates")
    coord.object = _object("controls")
    separate = _node(material, "ShaderNodeSeparateXYZ", "World axes")
    combine = _node(material, "ShaderNodeCombineXYZ", "Facade XZ in metres")
    _link(material, coord, "Object", separate, "Vector")
    _link(material, separate, "X", combine, "X")
    _link(material, separate, "Z", combine, "Y")
    return combine


def _brick():
    material = _new_material("physical brick")
    shader = material.node_tree.nodes.get("Principled BSDF")
    coords = _coordinates(material)
    scale = _node(material, "ShaderNodeVectorMath", "Physical scale")
    scale.operation = "SCALE"
    _driver(scale.inputs["Scale"], "brick_scale", "brick_scale")
    _link(material, coords, "Vector", scale, 0)
    brick = _node(material, "ShaderNodeTexBrick", "240 x 75 mm brick")
    brick.inputs["Scale"].default_value = 1
    brick.inputs["Brick Width"].default_value = 0.24
    brick.inputs["Row Height"].default_value = 0.075
    brick.inputs["Mortar Size"].default_value = 0.004
    brick.inputs["Mortar Smooth"].default_value = 0.002
    brick.inputs["Color1"].default_value = (0.31, 0.075, 0.025, 1)
    brick.inputs["Color2"].default_value = (0.56, 0.22, 0.08, 1)
    brick.inputs["Mortar"].default_value = (0.36, 0.34, 0.30, 1)
    _link(material, scale, "Vector", brick, "Vector")
    _link(material, brick, "Color", shader, "Base Color")
    bump = _node(material, "ShaderNodeBump", "Recessed mortar")
    bump.invert = True
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.002
    _link(material, brick, "Factor", bump, "Height")
    _link(material, bump, "Normal", shader, "Normal")
    _driver(shader.inputs["Roughness"], "brick_roughness", "brick_roughness")
    return material


def _carbon():
    material = _new_material("carbon weave study")
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Metallic"].default_value = 0
    shader.inputs["Anisotropic"].default_value = 0.8
    shader.inputs["Coat Weight"].default_value = 0.35
    shader.inputs["Coat Roughness"].default_value = 0.18
    coords = _coordinates(material)
    scale = _node(material, "ShaderNodeVectorMath", "Tow pitch in metres")
    scale.operation = "SCALE"
    _driver(scale.inputs["Scale"], "1/carbon_pitch", "carbon_pitch")
    _link(material, coords, "Vector", scale, 0)
    checker = _node(material, "ShaderNodeTexChecker", "Alternating over under")
    checker.inputs["Scale"].default_value = 1
    checker.inputs["Color1"].default_value = (0.009, 0.012, 0.018, 1)
    checker.inputs["Color2"].default_value = (0.05, 0.06, 0.075, 1)
    _link(material, scale, "Vector", checker, "Vector")
    _link(material, checker, "Color", shader, "Base Color")
    tangent = _node(material, "ShaderNodeTangent", "Explicit UV tangent")
    tangent.direction_type = "UV_MAP"
    tangent.uv_map = "LessonUV"
    _link(material, tangent, "Tangent", shader, "Tangent")
    rotation = _node(material, "ShaderNodeMath", "Alternate fibre direction 90 degrees")
    rotation.operation = "MULTIPLY"
    rotation.inputs[1].default_value = 0.25
    _link(material, checker, "Factor", rotation, 0)
    _link(material, rotation, 0, shader, "Anisotropic Rotation")
    waves = []
    for axis in ("X", "Y"):
        wave = _node(material, "ShaderNodeTexWave", "Fibre ridges " + axis)
        wave.wave_type = "BANDS"
        wave.bands_direction = axis
        wave.wave_profile = "SIN"
        wave.inputs["Scale"].default_value = 2
        wave.inputs["Distortion"].default_value = 0.12
        _link(material, scale, "Vector", wave, "Vector")
        waves.append(wave)
    mix = _node(material, "ShaderNodeMixRGB", "Select crossing tow relief")
    mix.blend_type = "MIX"
    _link(material, checker, "Factor", mix, 0)
    _link(material, waves[0], "Color", mix, 1)
    _link(material, waves[1], "Color", mix, 2)
    bump = _node(material, "ShaderNodeBump", "Shallow fibre relief")
    bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.00035
    _link(material, mix, "Color", bump, "Height")
    _link(material, bump, "Normal", shader, "Normal")
    _driver(shader.inputs["Roughness"], "carbon_roughness", "carbon_roughness")
    return material


def _normal_pixel(x, y):
    u, v = (x + 0.5) / IMAGE_SIZE, (y + 0.5) / IMAGE_SIZE
    gradient = 2 * math.pi * 0.004 / 0.25
    dx = gradient * math.cos(2 * math.pi * u) * math.cos(2 * math.pi * v)
    dy = -gradient * math.sin(2 * math.pi * u) * math.sin(2 * math.pi * v)
    length = math.sqrt(dx * dx + dy * dy + 1)
    return ((1 - dx / length) / 2, (1 - dy / length) / 2, (1 + 1 / length) / 2, 1)


def _images():
    images = []
    for role, space in (("orientation colour", "sRGB"), ("periodic tangent normal", "Non-Color")):
        image = bpy.data.images.new(
            "Textures — " + role,
            width=IMAGE_SIZE,
            height=IMAGE_SIZE,
            alpha=True,
            float_buffer=False,
        )
        image["tee_lesson"] = TAG
        image.colorspace_settings.name = space
        pixels = []
        for y in range(IMAGE_SIZE):
            for x in range(IMAGE_SIZE):
                if space == "Non-Color":
                    pixel = _normal_pixel(x, y)
                else:
                    # Red marks +U, green +V: a rotation/mirror cannot hide in a symmetric checker.
                    checker = 0.18 if ((x // 16 + y // 16) % 2) else 0.78
                    pixel = (
                        (0.92, 0.07, 0.035, 1)
                        if x > 111
                        else ((0.03, 0.8, 0.12, 1) if y > 111 else (checker, checker, checker, 1))
                    )
                pixels.extend(pixel)
        image.pixels[:] = pixels
        image.update()
        image.pack()
        images.append(image)
    return images


def _uv_material():
    material = _new_material("UV colour and tangent normal")
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = 0.38
    uv = _node(material, "ShaderNodeUVMap", "Explicit LessonUV")
    uv.uv_map = "LessonUV"
    scale = _node(material, "ShaderNodeVectorMath", "Image tile size in metres")
    scale.operation = "SCALE"
    _driver(scale.inputs["Scale"], "1/image_tile", "image_tile")
    _link(material, uv, "UV", scale, 0)
    nodes = []
    for image, name in zip(
        _images(), ("sRGB orientation image", "Non-Color tangent data"), strict=True
    ):
        node = _node(material, "ShaderNodeTexImage", name)
        node.image = image
        node.extension = "REPEAT"
        node.interpolation = "Linear"
        _link(material, scale, "Vector", node, "Vector")
        nodes.append(node)
    _link(material, nodes[0], "Color", shader, "Base Color")
    normal = _node(material, "ShaderNodeNormalMap", "Tangent normal conversion")
    normal.space = "TANGENT"
    normal.uv_map = "LessonUV"
    normal.inputs["Strength"].default_value = 1
    _link(material, nodes[1], "Color", normal, "Color")
    _link(material, normal, "Normal", shader, "Normal")
    return material


def _board(role, x, material):
    mesh = bpy.data.meshes.new("Textures — " + role)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2)
    for vertex in bm.verts:
        vertex.co.x *= 0.9
        vertex.co.y *= 0.07
        vertex.co.z *= 0.9
    bm.to_mesh(mesh)
    bm.free()
    uv = mesh.uv_layers.new(name="LessonUV")
    for polygon in mesh.polygons:
        axis = max(range(3), key=lambda i: abs(polygon.normal[i]))
        for loop_index in polygon.loop_indices:
            co = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv = (
                (co.y, co.z) if axis == 0 else ((co.x, co.z) if axis == 1 else (co.x, co.y))
            )
    obj = bpy.data.objects.new("Textures — " + role, mesh)
    _owned().objects.link(obj)
    obj.location = (x, 0, 1.3)
    obj["tee_lesson"] = TAG
    obj["lesson_role"] = role
    mesh.materials.append(material)
    return obj


def build():
    _require_metres()
    if bpy.data.collections.get(COLLECTION) is not None:
        raise ValueError("Texture lesson already exists; revise it or rename/remove it explicitly")
    collection = bpy.data.collections.new(COLLECTION)
    collection["tee_lesson"] = TAG
    bpy.context.scene.collection.children.link(collection)
    controller = bpy.data.objects.new("Textures — controls", None)
    collection.objects.link(controller)
    controller["tee_lesson"] = TAG
    controller["lesson_role"] = "controls"
    for key, value in {
        "brick_scale": 1.0,
        "brick_roughness": 0.62,
        "carbon_pitch": 0.024,
        "carbon_roughness": 0.3,
        "image_tile": 0.25,
    }.items():
        controller[key] = value
    controller["stage"] = "built"
    for role, x, material in (
        ("brick", -2.2, _brick()),
        ("carbon", 0, _carbon()),
        ("uv_normal", 2.2, _uv_material()),
    ):
        _board(role, x, material)
    bpy.context.view_layer.update()
    controller["geometry_signature"] = _geometry_signature()
    return inspect()


def _geometry_signature():
    values = []
    for role in ("brick", "carbon", "uv_normal"):
        obj = _object(role)
        values.extend(round(v, 7) for row in obj.matrix_world for v in row)
        values.extend(round(v, 7) for vertex in obj.data.vertices for v in vertex.co)
        values.extend(int(loop.vertex_index) for loop in obj.data.loops)
    return values


def _result(stage):
    return {
        "stage": stage,
        "collection": COLLECTION,
        "primary_objects": [_object(r).name for r in ("brick", "carbon", "uv_normal")],
        "presentation": {"target": [0, 0, 1.2], "camera": [0, -10, 2.8]},
        "units": "m",
        "colour_note": "Authored linear shader colours; colour image sRGB, tangent data Non-Color",
    }


def revise():
    _require_metres()
    if not inspect()["passed"]:
        raise ValueError("Repair the failed texture inspection before revising owned controls")
    controller = _object("controls")
    for key, value in {
        "brick_scale": 1.25,
        "brick_roughness": 0.48,
        "carbon_pitch": 0.032,
        "carbon_roughness": 0.22,
        "image_tile": 0.4,
    }.items():
        controller[key] = value
    controller["stage"] = "revised"
    controller.update_tag()
    bpy.context.view_layer.update()
    return inspect()


def inspect():
    bpy.context.view_layer.update()
    inventory_errors = _inventory_errors()
    if inventory_errors:
        return {
            "stage": "invalid",
            "collection": COLLECTION,
            "primary_objects": [o.name for o in _owned().objects if o.type == "MESH"],
            "passed": False,
            "checks": {
                "exact_owned_inventory": {"passed": False, "measured": {"errors": inventory_errors}}
            },
        }
    controller = _object("controls")
    checks = {}

    def record(name, passed, measured):
        checks[name] = {"passed": bool(passed), "measured": measured}

    record("exact_owned_inventory", True, {"mesh_roles": 3, "controller_roles": 1})
    record(
        "metre_scene_scale",
        abs(bpy.context.scene.unit_settings.scale_length - 1) < 1e-9,
        {"scale_length": bpy.context.scene.unit_settings.scale_length},
    )
    coordinate_error = max(
        abs(controller.matrix_world[row][column] - (1 if row == column else 0))
        for row in range(4)
        for column in range(4)
    )
    record(
        "identity_coordinate_controller",
        coordinate_error < 1e-7 and controller.parent is None,
        {"max_identity_error": coordinate_error, "parented": controller.parent is not None},
    )
    driver_errors = _driver_contract(controller)
    record("complete_live_shader_drivers", not driver_errors, {"errors": driver_errors})
    signature = _geometry_signature()
    record(
        "geometry_unchanged",
        signature == list(controller["geometry_signature"]),
        {"signature_values": len(signature)},
    )
    expected_links = {
        "brick": [
            ("240 x 75 mm brick", "Color", "Principled BSDF", "Base Color"),
            ("Recessed mortar", "Normal", "Principled BSDF", "Normal"),
        ],
        "carbon": [
            ("Explicit UV tangent", "Tangent", "Principled BSDF", "Tangent"),
            (
                "Alternate fibre direction 90 degrees",
                "Value",
                "Principled BSDF",
                "Anisotropic Rotation",
            ),
            ("Shallow fibre relief", "Normal", "Principled BSDF", "Normal"),
        ],
        "uv_normal": [
            ("sRGB orientation image", "Color", "Principled BSDF", "Base Color"),
            ("Non-Color tangent data", "Color", "Tangent normal conversion", "Color"),
            ("Tangent normal conversion", "Normal", "Principled BSDF", "Normal"),
        ],
    }
    expected_links["brick"].extend(
        [
            ("Metre coordinates", "Object", "World axes", "Vector"),
            ("World axes", "X", "Facade XZ in metres", "X"),
            ("World axes", "Z", "Facade XZ in metres", "Y"),
            ("Facade XZ in metres", "Vector", "Physical scale", "Vector"),
            ("Physical scale", "Vector", "240 x 75 mm brick", "Vector"),
            ("240 x 75 mm brick", "Factor", "Recessed mortar", "Height"),
        ]
    )
    expected_links["carbon"].extend(
        [
            ("Facade XZ in metres", "Vector", "Tow pitch in metres", "Vector"),
            ("Tow pitch in metres", "Vector", "Alternating over under", "Vector"),
            ("Alternating over under", "Factor", "Alternate fibre direction 90 degrees", "Value"),
            ("Select crossing tow relief", "Color", "Shallow fibre relief", "Height"),
        ]
    )
    expected_links["uv_normal"].extend(
        [
            ("Explicit LessonUV", "UV", "Image tile size in metres", "Vector"),
            ("Image tile size in metres", "Vector", "sRGB orientation image", "Vector"),
            ("Image tile size in metres", "Vector", "Non-Color tangent data", "Vector"),
        ]
    )
    expected_links["carbon"].extend(
        [
            ("Metre coordinates", "Object", "World axes", "Vector"),
            ("World axes", "X", "Facade XZ in metres", "X"),
            ("World axes", "Z", "Facade XZ in metres", "Y"),
            ("Alternating over under", "Color", "Principled BSDF", "Base Color"),
            ("Tow pitch in metres", "Vector", "Fibre ridges X", "Vector"),
            ("Tow pitch in metres", "Vector", "Fibre ridges Y", "Vector"),
            ("Alternating over under", "Factor", "Select crossing tow relief", "Factor"),
            ("Fibre ridges X", "Color", "Select crossing tow relief", "Color1"),
            ("Fibre ridges Y", "Color", "Select crossing tow relief", "Color2"),
        ]
    )
    for role, links in expected_links.items():
        links.append(("Principled BSDF", "BSDF", "Material Output", "Surface"))
        material = _material(role)
        actual = {
            (link.from_node.name, link.from_socket.name, link.to_node.name, link.to_socket.name)
            for link in material.node_tree.links
        }
        missing = [link for link in links if link not in actual]
        required_nodes = {node for link in links for node in (link[0], link[2])}
        inactive_nodes = [
            name
            for name in required_nodes
            if material.node_tree.nodes.get(name) is None or material.node_tree.nodes[name].mute
        ]
        output = material.node_tree.nodes.get("Material Output")
        output_active = output is not None and output.is_active_output and output.target == "ALL"
        record(
            role + "_shader_links",
            not missing and not inactive_nodes and output_active,
            {
                "missing": missing,
                "inactive_nodes": inactive_nodes,
                "output_active": output_active,
                "links": len(actual),
            },
        )
    missing_nodes = [
        name
        for role, links in expected_links.items()
        for name in {node for link in links for node in (link[0], link[2])}
        if _material(role).node_tree.nodes.get(name) is None
    ]
    if missing_nodes:
        return {**_result(str(controller["stage"])), "passed": False, "checks": checks}
    coordinate_bindings = {
        role: _material(role).node_tree.nodes["Metre coordinates"].object == controller
        for role in ("brick", "carbon")
    }
    record("owned_coordinate_bindings", all(coordinate_bindings.values()), coordinate_bindings)
    brick = _material("brick").node_tree.nodes
    carbon = _material("carbon").node_tree.nodes
    image_nodes = _material("uv_normal").node_tree.nodes
    settings = (
        ("brick_scale", brick["Physical scale"].inputs["Scale"], float(controller["brick_scale"])),
        (
            "brick_roughness",
            brick["Principled BSDF"].inputs["Roughness"],
            float(controller["brick_roughness"]),
        ),
        (
            "carbon_pitch",
            carbon["Tow pitch in metres"].inputs["Scale"],
            1 / float(controller["carbon_pitch"]),
        ),
        (
            "carbon_roughness",
            carbon["Principled BSDF"].inputs["Roughness"],
            float(controller["carbon_roughness"]),
        ),
        (
            "image_tile",
            image_nodes["Image tile size in metres"].inputs["Scale"],
            1 / float(controller["image_tile"]),
        ),
    )
    for name, socket, expected in settings:
        value = float(socket.default_value)
        record(
            name + "_driver", abs(value - expected) < 1e-5, {"value": value, "expected": expected}
        )
    uv_errors = []
    for role in ("brick", "carbon", "uv_normal"):
        mesh = _object(role).data
        uv = mesh.uv_layers.get("LessonUV")
        if uv is None:
            uv_errors.append(role + " missing UV")
            continue
        for poly in mesh.polygons:
            if abs(poly.normal.y) > 0.9:
                for i in poly.loop_indices:
                    vertex = mesh.vertices[mesh.loops[i].vertex_index].co
                    if (
                        abs(uv.data[i].uv.x - vertex.x) > 1e-6
                        or abs(uv.data[i].uv.y - vertex.z) > 1e-6
                    ):
                        uv_errors.append(role + " rotated or rescaled UV")
    record("uv_orientation_and_metre_scale", not uv_errors, {"errors": uv_errors})
    images = [
        image_nodes[name].image for name in ("sRGB orientation image", "Non-Color tangent data")
    ]
    spaces = [image.colorspace_settings.name for image in images]
    packed = [image.packed_file is not None and len(image.packed_files) == 1 for image in images]
    record(
        "portable_colour_and_data_images",
        spaces == ["sRGB", "Non-Color"] and all(packed),
        {"spaces": spaces, "packed": packed, "sizes": [list(image.size) for image in images]},
    )
    colours = []
    for x, y in ((120, 32), (32, 120)):
        offset = (y * IMAGE_SIZE + x) * 4
        colours.append(list(images[0].pixels[offset : offset + 3]))
    record(
        "asymmetric_uv_colour_markers",
        colours[0][0] > 0.8 and colours[0][1] < 0.1 and colours[1][1] > 0.7 and colours[1][0] < 0.1,
        {"u_red_v_green": colours},
    )
    normal_image = images[1]
    deviations = []
    for x, y in ((0, 0), (31, 17), (64, 64), (111, 83), (127, 127)):
        offset = (y * IMAGE_SIZE + x) * 4
        actual = normal_image.pixels[offset : offset + 4]
        expected = _normal_pixel(x, y)
        deviations.extend(abs(a - e) for a, e in zip(actual, expected, strict=True))
    # Packed 8-bit pixels quantise; 1/255 is the honest data bound.
    record(
        "normal_pixel_samples",
        max(deviations) <= 1 / 255 + 1e-5,
        {"max_channel_error": max(deviations), "sample_count": 5},
    )
    normal = image_nodes["Tangent normal conversion"]
    record(
        "normal_map_space",
        normal.space == "TANGENT" and normal.uv_map == "LessonUV",
        {"space": normal.space, "uv_map": normal.uv_map},
    )
    return {
        **_result(str(controller["stage"])),
        "passed": all(c["passed"] for c in checks.values()),
        "checks": checks,
        "physical_scale": {
            "brick_width_m": 0.24 / controller["brick_scale"],
            "brick_course_m": 0.075 / controller["brick_scale"],
            "carbon_tow_m": controller["carbon_pitch"],
            "image_tile_m": controller["image_tile"],
        },
        "limitations": [
            "Carbon weave pitch is deliberately enlarged for teaching; "
            "no measured BRDF or laminate claim",
            "Bump and normal shading change light response, not mesh silhouette",
            "Rescaling the normal-map tile changes apparent feature size; "
            "normal amplitude remains authored",
        ],
    }
