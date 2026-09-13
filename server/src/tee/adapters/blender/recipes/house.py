"""Editable compact modern house. Metres; authored layout, not permit drawings.

Call build(), inspect(), revise(), inspect(). All drivers reference one owned
controller. Walls are explicit solid segments around genuine voids, avoiding a
fragile chain of overlapping booleans. The roof is a separate removable object.
"""

import hashlib
import math

import bmesh
import bpy
from mathutils import Vector

COLLECTION = "TEE Lesson — House"
TAG = "tee.lesson.house.v1"

# Expected authored roles and exact path/index/expression signatures. These remain
# fixed across a supported parameter revision; property values are checked separately.
ROLE_CONTRACT = {
    "floor slab": ("slab", "65f267e27a3bac7d8d1539d8279e40c5f7bf277ad7bbd31bcca4fa632024bd50"),
    "living kitchen floor": (
        "floor",
        "7cf82c224f4a0e90f100f2f2c35997cf4cde89061f1e823d2e4cff11cee7e3c5",
    ),
    "bedroom floor": ("floor", "943f123f30f85b2c83329906692e2aab658fd96353772e6dca88043d3e7673c8"),
    "bathroom floor": ("floor", "68ae42ade68fbef4734095a9f451a77b2000d4e1656bb3f9336b53f996365eb8"),
    "front west": ("wall", "c248977f30cb7954c35a2cf79b774eab4e0daa68977b32187e8d955d16abac59"),
    "front pier": ("wall", "8e44ac834d0d75f307912c8f745c2f51dd3d5fa9b05f84b3fa3300531d781489"),
    "front east": ("wall", "c9449d3fe8cdf98616afa142a62dbabe01f4cc0c55eb86600c628731ce9ca0b6"),
    "entry lintel": ("wall", "83923433309e794733a547eb9b35763c05531269fcde86e1aa4e66d21724ea4a"),
    "living window sill wall": (
        "wall",
        "8535c4e21c4a6bf93546c597daf5df417c14c24d6e29e4c4072e57a3435ec831",
    ),
    "living window lintel": (
        "wall",
        "7c750363acce488495f3d96601c23ad57a42b0f3f17856c4b7faad488a6de2ce",
    ),
    "living window glazing": (
        "glazing",
        "77b95c5b980b44df28f66dadb8d834cd41b1dfaca10bf0147b7409fe4bbc13b9",
    ),
    "back west": ("wall", "cbdd25cf4de5f53213ec5a14e783f98ff3261b10cec91785589d07cbc0869cf5"),
    "back middle": ("wall", "b5646d734bd7721d18613077d8cb8e462e8f527d7fa2e9e3aa39230b3e3a04cd"),
    "back east": ("wall", "e2a5c45ff06cdcae565b878fbec4ac9e92bb5522f9ad4f10d331d062c70fe5b5"),
    "kitchen window sill wall": (
        "wall",
        "482b25a42424d210d267dc05c6249bd214fe1a51e7f4150030936c6d743b687c",
    ),
    "kitchen window lintel": (
        "wall",
        "95bacfc1d5b7a46d18bea7bda23f427c9d6e9ef94b80b8ef345e5350b04116fe",
    ),
    "kitchen window glazing": (
        "glazing",
        "1e77818584f21b216e48f0ac23b8bde43cc3331064c9ab3104c26bf9f2949343",
    ),
    "bathroom window sill wall": (
        "wall",
        "713cf1f1177fd6a56b3be7cc4483fa7bbab8f596eee1a076eff06f3f1815547e",
    ),
    "bathroom window lintel": (
        "wall",
        "749d7c6963a6cd40b12bcfa7b81949a356eb79e022ba703205ab82e31860cacc",
    ),
    "bathroom window glazing": (
        "glazing",
        "d0ad0a71b06135be6d634a1a2423512b8c304ba43afb9630934290ac76e9a89b",
    ),
    "west wall": ("wall", "aa00702e1d264417ff07812ca9a0778f85c0dd101b8cc7d7c4be5655e738cb5f"),
    "east south": ("wall", "078dd4c291b623d9cdccc7c771381acc9c38a345e7d0d9a46642013937618714"),
    "east north": ("wall", "9b9f92be9739d0255fdaba8e768212808d2c579094763f503e10ab4e3dab60ac"),
    "bedroom sill wall": (
        "wall",
        "162ff6836f1d307c4eaf2150633b40924b56c382b8c6d528f942e4c7313a42dc",
    ),
    "bedroom lintel": ("wall", "48dd549b4370eda5a9bf7dba9fd4dd333dcd65a39b91c28b7221c2fa1b7d30f5"),
    "bedroom glazing": (
        "glazing",
        "5c981aa7a309e7a38350176025ac1dce4eaf5c9dd2d7744216e02d4d5c20ae2b",
    ),
    "room partition south": (
        "wall",
        "acf28395d0f8566a3f48ad4109cd9a7b6950314ee9fa3139812e4f304e5aee31",
    ),
    "room partition north": (
        "wall",
        "276c01d1fe106f5b20e40c4fad17ff4b799f685b8682a146575519da56d9114d",
    ),
    "room door lintel": (
        "wall",
        "be620eae7f47a0b18e807df9d537670dfdaf8e3762fed3efdf41f8947872fd32",
    ),
    "bath partition west": (
        "wall",
        "37b6f5a4fa1a3a710a52ac2b9e009489c1b642b666be4f1b4bf133d2cca95345",
    ),
    "bath partition east": (
        "wall",
        "57fdc5e666772ad0c7c716410f90bf38bf22d0d9d2f1c4892e8a714268932267",
    ),
    "bath door lintel": (
        "wall",
        "8a64c29a49c175577ed853fc92bb30c419088448d162edbf1cd34be183d2df14",
    ),
    "roof": ("roof", "4f45c789b1404b9774dbddb0a03a25e749090330950d523c333e5a090b98cc43"),
    "front roof infill": (
        "wall",
        "57cc6567ef95ffe3943bb9b24190429479672a61b6cd4d732f95c9dca84f7ab3",
    ),
    "front roof infill base": (
        "wall",
        "6ef1917fca48660054e7e4ddc43aa6b3801bb5d4881322631b99b6f2c42df878",
    ),
    "back roof infill": (
        "wall",
        "57cc6567ef95ffe3943bb9b24190429479672a61b6cd4d732f95c9dca84f7ab3",
    ),
    "back roof infill base": (
        "wall",
        "1cbd3a3de3dc777fc6cc9ea2321d8d51fe09e222aa309cf58790e0c2154c85db",
    ),
    "west roof infill": (
        "wall",
        "f1d3c6dc54d77f97ecc5fbbc2056848860d9e8e55fa7dd2a5f378c1a24bb0f86",
    ),
    "west roof infill base": (
        "wall",
        "99a5e28074acdba1dcefa1947f6ab1f47864c32ff3e4bcf0d9df0e6a84dac517",
    ),
    "east roof infill": (
        "wall",
        "21b468ea2888d96a360635dbc65bf1152932546616b4c96ba3385d3c62e3da61",
    ),
    "east roof infill base": (
        "wall",
        "00b61afb324c2fa171479974c93c52f65c2bf8d84efdfdea3b4a07eab6831b86",
    ),
    "front window top frame": (
        "frame",
        "d6cc902804a9ef6c7d5c3b0079eb1ba7a16f1ef0d8b957fb0868ca374ce7eed8",
    ),
    "front window lower frame": (
        "frame",
        "15075c00801a3c1a1e4daa63d789b272707c9e0212070905e7fd1424a72c1e88",
    ),
    "front window left frame": (
        "frame",
        "ea81d7d0012373e112b0d4e071458d4a0e7c7da22ef1c763f99c86285f3f7ffe",
    ),
    "front window right frame": (
        "frame",
        "a62d1f0e13ea9bf346a896493bf4681e9d57b7ab8d2ee83fe3e1fb5560e47c43",
    ),
    "kitchen worktop": (
        "furniture",
        "862fec24fd46f8375479a9fc386755da764c779bc6e02834246c9f094a48b0d3",
    ),
    "bed platform": (
        "furniture",
        "d8201ca1053b38cb6769fb32f558662f9c0a2ec7c5cc3c4f3dd0bf75a9de9119",
    ),
    "shower tray": (
        "furniture",
        "556cbd8e5f56ef68d8b1febe93b76d4e88ce0abf898bafddec423f7db81e9540",
    ),
}


def _owned():
    collection = bpy.data.collections.get(COLLECTION)
    if collection is None or collection.get("tee_lesson") != TAG:
        raise ValueError("Build the owned house lesson first")
    return collection


def _object(role):
    matches = [
        o for o in _owned().objects if o.get("lesson_role") == role and o.get("tee_lesson") == TAG
    ]
    if len(matches) != 1:
        raise ValueError("House role must resolve exactly once: " + role)
    return matches[0]


def _require_metres():
    if abs(bpy.context.scene.unit_settings.scale_length - 1.0) > 1e-9:
        raise ValueError("House lesson requires scene unit scale 1 metre before build or revision")


def _inventory_errors():
    collection = _owned()
    expected = set(ROLE_CONTRACT) | {"dimensions"}
    objects = list(collection.objects)
    roles = [str(obj.get("lesson_role", "")) for obj in objects]
    errors = []
    if len(objects) != len(expected) or set(roles) != expected:
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
        if role == "dimensions":
            if obj.type != "EMPTY":
                errors.append({"controller_type": obj.type})
        elif role in ROLE_CONTRACT:
            category = ROLE_CONTRACT[role][0]
            if obj.type != "MESH" or obj.get("category") != category:
                errors.append({"role_type_or_category": role})
            elif obj.data.users != 1:
                errors.append({"shared_mesh": role})
    return errors


def _driver_errors(controller):
    errors = []
    parameters = {"width", "depth", "height", "room_x", "window_w", "overhang"}
    for role, (_, expected_signature) in ROLE_CONTRACT.items():
        obj = _object(role)
        curves = list(obj.animation_data.drivers) if obj.animation_data else []
        signature = "\n".join(
            sorted(
                f"{curve.data_path}|{curve.array_index}|{curve.driver.expression}"
                for curve in curves
            )
        )
        if hashlib.sha256(signature.encode()).hexdigest() != expected_signature:
            errors.append({"role": role, "defect": "missing or changed driver path/expression"})
        for curve in curves:
            driver = curve.driver
            variables = list(driver.variables)
            if (
                curve.mute
                or not driver.is_valid
                or driver.type != "SCRIPTED"
                or len(variables) != len(parameters)
                or {variable.name for variable in variables} != parameters
            ):
                errors.append({"role": role, "defect": "inactive driver or wrong variables"})
                continue
            for variable in variables:
                if (
                    variable.type != "SINGLE_PROP"
                    or len(variable.targets) != 1
                    or variable.targets[0].id != controller
                    or variable.targets[0].data_path != '["' + variable.name + '"]'
                ):
                    errors.append({"role": role, "defect": "foreign or changed controller binding"})
    return errors


def _drive(obj, path, axis, expression, controller):
    curve = obj.driver_add(path, axis)
    driver = curve.driver
    driver.type = "SCRIPTED"
    for name in ("width", "depth", "height", "room_x", "window_w", "overhang"):
        variable = driver.variables.new()
        variable.name = name
        variable.type = "SINGLE_PROP"
        variable.targets[0].id = controller
        variable.targets[0].data_path = '["' + name + '"]'
    driver.expression = str(expression)


def _material(name, color, roughness=0.6, metallic=0.0, transmission=0.0):
    material = bpy.data.materials.new("House — " + name)
    material["tee_lesson"] = TAG
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Transmission Weight"].default_value = transmission
    return material


def _box(role, lower, upper, material, category="wall"):
    collection = _owned()
    controller = _object("dimensions")
    mesh = bpy.data.meshes.new("House — " + role)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("House — " + role, mesh)
    collection.objects.link(obj)
    obj["tee_lesson"] = TAG
    obj["lesson_role"] = role
    obj["category"] = category
    for axis in range(3):
        lo, hi = str(lower[axis]), str(upper[axis])
        _drive(obj, "location", axis, f"(({lo})+({hi}))/2", controller)
        _drive(obj, "scale", axis, f"(({hi})-({lo}))/2", controller)
    obj.data.materials.append(material)
    return obj


def _front_opening(prefix, x0, x1, sill, head, y0, y1, material, glass):
    if sill:
        _box(prefix + " sill wall", [x0, y0, 0], [x1, y1, sill], material)
    _box(prefix + " lintel", [x0, y0, head], [x1, y1, "height"], material)
    if glass is not None:
        _box(
            prefix + " glazing",
            [x0, f"({y0})+0.085", sill],
            [x1, f"({y0})+0.115", head],
            glass,
            "glazing",
        )


def _infill(role, x0, x1, y0, y1, material):
    controller = _object("dimensions")
    mesh = bpy.data.meshes.new("House — " + role)
    vertices = [
        (x, y, z)
        for zlevel in (0, 1)
        for y in (y0, y1)
        for x in (-1, 1)
        for z in (0 if zlevel == 0 else 0.01 + 0.04 * y,)
    ]
    faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("House — " + role, mesh)
    _owned().objects.link(obj)
    obj["tee_lesson"] = TAG
    obj["lesson_role"] = role
    obj["category"] = "wall"
    obj.data.materials.append(material)
    _drive(obj, "location", 0, f"(({x0})+({x1}))/2", controller)
    _drive(obj, "scale", 0, f"(({x1})-({x0}))/2", controller)
    _drive(obj, "location", 2, "height+0.04*overhang-0.01", controller)
    _box(role + " base", [x0, y0, "height"], [x1, y1, "height+0.04*overhang-0.01"], material)


def build():
    _require_metres()
    if bpy.data.collections.get(COLLECTION) is not None:
        raise ValueError("House lesson already exists; revise it or rename/remove it explicitly")
    collection = bpy.data.collections.new(COLLECTION)
    collection["tee_lesson"] = TAG
    bpy.context.scene.collection.children.link(collection)
    controller = bpy.data.objects.new("House — dimensions", None)
    controller["tee_lesson"] = TAG
    controller["lesson_role"] = "dimensions"
    controller.empty_display_type = "PLAIN_AXES"
    collection.objects.link(controller)
    for key, value in {
        "width": 10.0,
        "depth": 8.0,
        "height": 3.0,
        "room_x": 6.0,
        "window_w": 2.0,
        "overhang": 0.4,
    }.items():
        controller[key] = value
    controller["stage"] = "built"
    plaster = _material("warm plaster", (0.78, 0.72, 0.59))
    frame = _material("anodised frame", (0.035, 0.048, 0.056), 0.3, 0.7)
    glass = _material("glazing", (0.70, 0.88, 0.92), 0.08, transmission=1)
    floor = _material("concrete floor", (0.29, 0.34, 0.34), 0.8)
    bedroom = _material("bedroom floor", (0.47, 0.26, 0.11), 0.55)
    bathroom = _material("bathroom floor", (0.23, 0.43, 0.45), 0.4)
    roof_material = _material("standing seam roof", (0.045, 0.08, 0.095), 0.35, 0.7)
    _box("floor slab", [0, 0, -0.15], ["width", "depth", 0], floor, "slab")
    _box("living kitchen floor", [0.2, 0.2, 0], ["room_x", 7.8, 0.012], floor, "floor")
    _box("bedroom floor", ["room_x+0.15", 0.2, 0], ["width-0.2", 5, 0.012], bedroom, "floor")
    _box("bathroom floor", ["room_x+0.15", 5.15, 0], ["width-0.2", 7.8, 0.012], bathroom, "floor")
    # Front: 1 m entrance and a width-driven window with a real 0.9 m sill.
    for role, lo, hi in (
        ("front west", 0, 1.2),
        ("front pier", 2.2, 3),
        ("front east", "3+window_w", "width"),
    ):
        _box(role, [lo, 0, 0], [hi, 0.2, "height"], plaster)
    _front_opening("entry", 1.2, 2.2, 0, 2.2, 0, 0.2, plaster, None)
    _front_opening("living window", 3, "3+window_w", 0.9, 2.2, 0, 0.2, plaster, glass)
    # Back: separate kitchen and raised-sill bathroom windows.
    for role, lo, hi in (
        ("back west", 0, 1.4),
        ("back middle", 3.8, 7.4),
        ("back east", 8.4, "width"),
    ):
        _box(role, [lo, 7.8, 0], [hi, 8, "height"], plaster)
    _front_opening("kitchen window", 1.4, 3.8, 1, 2.2, 7.8, 8, plaster, glass)
    _front_opening("bathroom window", 7.4, 8.4, 1.6, 2.4, 7.8, 8, plaster, glass)
    _box("west wall", [0, 0.2, 0], [0.2, 7.8, "height"], plaster)
    _box("east south", ["width-0.2", 0.2, 0], ["width", 2, "height"], plaster)
    _box("east north", ["width-0.2", 3.8, 0], ["width", 7.8, "height"], plaster)
    _box("bedroom sill wall", ["width-0.2", 2, 0], ["width", 3.8, 0.9], plaster)
    _box("bedroom lintel", ["width-0.2", 2, 2.2], ["width", 3.8, "height"], plaster)
    _box("bedroom glazing", ["width-0.115", 2, 0.9], ["width-0.085", 3.8, 2.2], glass, "glazing")
    # Internal doors remain open, without a decorative leaf masking the void.
    _box("room partition south", ["room_x", 0.2, 0], ["room_x+0.15", 3.4, "height"], plaster)
    _box("room partition north", ["room_x", 4.4, 0], ["room_x+0.15", 7.8, "height"], plaster)
    _box("room door lintel", ["room_x", 3.4, 2.2], ["room_x+0.15", 4.4, "height"], plaster)
    _box("bath partition west", ["room_x+0.15", 5, 0], [7, 5.15, "height"], plaster)
    _box("bath partition east", [7.9, 5, 0], ["width-0.2", 5.15, "height"], plaster)
    _box("bath door lintel", [7, 5, 2.2], [7.9, 5.15, "height"], plaster)
    # Sloping upper wall infill closes the gap beneath the removable shed roof.
    roof = _box(
        "roof",
        ["-overhang", "-overhang", 0],
        ["width+overhang", "depth+overhang", 0.18],
        roof_material,
        "roof",
    )
    # Cube rotation with driver-corrected length yields an exact 4% fall in y.
    slope = 0.04
    roof.rotation_euler.x = math.atan(slope)
    roof.driver_remove("location", 2)
    _drive(
        roof, "location", 2, "height+0.09*1.0007996802557443+0.04*(depth/2+overhang)", controller
    )
    roof.driver_remove("scale", 1)
    _drive(roof, "scale", 1, "(depth+2*overhang)*1.0007996802557443/2", controller)
    for role, x0, x1, y0, y1 in (
        ("front roof infill", 0, "width", 0, 0.2),
        ("back roof infill", 0, "width", 7.8, 8),
        ("west roof infill", 0, 0.2, 0.2, 7.8),
        ("east roof infill", "width-0.2", "width", 0.2, 7.8),
    ):
        _infill(role, x0, x1, y0, y1, plaster)
    # Roof fascia makes the slope readable; no claim of a detailed weather seal.
    _box("front window top frame", [3, -0.025, 2.16], ["3+window_w", 0.225, 2.22], frame, "frame")
    _box("front window lower frame", [3, -0.025, 0.88], ["3+window_w", 0.225, 0.94], frame, "frame")
    _box("front window left frame", [2.98, -0.025, 0.9], [3.04, 0.225, 2.2], frame, "frame")
    _box(
        "front window right frame",
        ["2.96+window_w", -0.025, 0.9],
        ["3.02+window_w", 0.225, 2.2],
        frame,
        "frame",
    )
    # Plain kitchen units / bed / shower define use without external assets.
    _box("kitchen worktop", [0.3, 6.9, 0.85], [3.7, 7.7, 0.94], frame, "furniture")
    _box("bed platform", ["room_x+0.7", 0.8, 0.15], ["room_x+2.1", 2.8, 0.45], bedroom, "furniture")
    _box("shower tray", ["width-1.3", 6.6, 0.015], ["width-0.3", 7.6, 0.1], glass, "furniture")
    bpy.context.view_layer.update()
    return inspect()


def _result(stage):
    return {
        "stage": stage,
        "collection": COLLECTION,
        "primary_objects": [o.name for o in _owned().objects if o.type == "MESH"],
        "presentation": {"target": [5, 4, 1], "camera": [17, -17, 14]},
        "units": "m",
        "roof_note": "4% shed roof; weather seals and drainage sizing are outside this study",
    }


def revise():
    _require_metres()
    if not inspect()["passed"]:
        raise ValueError("Repair the failed house inspection before revising owned dimensions")
    controller = _object("dimensions")
    for key, value in {"width": 11.2, "room_x": 6.5, "window_w": 2.5, "overhang": 0.6}.items():
        controller[key] = value
    controller["stage"] = "revised"
    controller.update_tag()
    bpy.context.view_layer.update()
    return inspect()


def _bounds(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    vertices = [evaluated.matrix_world @ v.co for v in evaluated.data.vertices]
    return (
        [min(v[i] for v in vertices) for i in range(3)],
        [max(v[i] for v in vertices) for i in range(3)],
    )


def _volume(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    bm = bmesh.new()
    bm.from_mesh(evaluated.data)
    value = abs(bm.calc_volume()) * abs(evaluated.matrix_world.to_3x3().determinant())
    bm.free()
    return value


def _wall_hit(origin, direction, distance, depsgraph):
    for obj in _owned().objects:
        if obj.get("category") != "wall":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        inverse = evaluated.matrix_world.inverted()
        local_origin = inverse @ Vector(origin)
        local_end = inverse @ (Vector(origin) + Vector(direction) * distance)
        delta = local_end - local_origin
        if evaluated.ray_cast(local_origin, delta.normalized(), distance=delta.length)[0]:
            return True
    return False


def inspect():
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
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
    controller = _object("dimensions")
    w, rx, ww, oh = (float(controller[k]) for k in ("width", "room_x", "window_w", "overhang"))
    checks = {}

    def record(name, passed, measured):
        checks[name] = {"passed": bool(passed), "measured": measured}

    record("exact_owned_inventory", True, {"mesh_roles": 48, "wall_roles": 32})
    record(
        "metre_scene_scale",
        abs(bpy.context.scene.unit_settings.scale_length - 1) < 1e-9,
        {"scale_length": bpy.context.scene.unit_settings.scale_length},
    )
    driver_errors = _driver_errors(controller)
    record("complete_dimension_driver_contract", not driver_errors, {"errors": driver_errors})
    slab_lo, slab_hi = _bounds(_object("floor slab"), depsgraph)
    slab_volume = _volume(_object("floor slab"), depsgraph)
    record(
        "slab_dimensions_volume",
        abs(slab_hi[0] - w) < 1e-5
        and abs(slab_hi[1] - 8) < 1e-5
        and abs(slab_volume - w * 8 * 0.15) < 1e-4,
        {"bounds_m": [slab_lo, slab_hi], "volume_m3": slab_volume},
    )
    left = _bounds(_object("room partition south"), depsgraph)[0][0]
    floor_lo, floor_hi = _bounds(_object("living kitchen floor"), depsgraph)
    record(
        "room_width_dependency",
        abs(left - rx) < 1e-5 and abs(floor_hi[0] - left) < 1e-5,
        {"partition_x_m": left, "clear_living_width_m": floor_hi[0] - floor_lo[0]},
    )
    window_left = _bounds(_object("front pier"), depsgraph)[1][0]
    window_right = _bounds(_object("front east"), depsgraph)[0][0]
    record(
        "actual_wall_window_width",
        abs(window_right - window_left - ww) < 1e-5,
        {"opening_edges_m": [window_left, window_right]},
    )
    window_lo, window_hi = _bounds(_object("living window glazing"), depsgraph)
    record(
        "window_dimensions",
        abs(window_hi[0] - window_lo[0] - ww) < 1e-5 and abs(window_lo[2] - 0.9) < 1e-5,
        {"width_m": window_hi[0] - window_lo[0], "sill_m": window_lo[2]},
    )
    for name, origin, direction, distance in (
        ("entry_clear", [1.7, -0.5, 1], [0, 1, 0], 1),
        ("window_clear_in_wall", [3 + ww / 2, -0.5, 1.5], [0, 1, 0], 1),
        ("room_door_clear", [rx - 0.5, 3.9, 1], [1, 0, 0], 1),
        ("bath_door_clear", [7.45, 4.6, 1], [0, 1, 0], 1),
    ):
        hit = _wall_hit(origin, direction, distance, depsgraph)
        record(name, not hit, {"wall_hit": hit, "origin_m": origin})
    for name, origin in (
        ("entry_lintel_present", [1.7, -0.5, 2.5]),
        ("window_sill_present", [3 + ww / 2, -0.5, 0.5]),
    ):
        hit = _wall_hit(origin, [0, 1, 0], 1, depsgraph)
        record(name, hit, {"wall_hit": hit})
    door_l = _bounds(_object("front west"), depsgraph)[1][0]
    door_r = _bounds(_object("front pier"), depsgraph)[0][0]
    record("entry_width", abs(door_r - door_l - 1) < 1e-5, {"clear_width_m": door_r - door_l})
    roof = _object("roof").evaluated_get(depsgraph)
    roof_lo, roof_hi = _bounds(_object("roof"), depsgraph)
    normal = roof.matrix_world.to_3x3() @ Vector((0, 0, 1))
    slope = -normal.y / normal.z
    record(
        "roof_slope_overhang",
        abs(slope - 0.04) < 1e-6
        and abs(roof_lo[0] + oh) < 1e-5
        and abs(roof_hi[0] - w - oh) < 1e-5,
        {"slope": slope, "x_bounds_m": [roof_lo[0], roof_hi[0]], "overhang_m": oh},
    )
    roof_vertices = [roof.matrix_world @ v.co for v in roof.data.vertices if v.co.z < 0]
    plane_errors = [abs(v.z - (3 + 0.04 * (v.y + oh))) for v in roof_vertices]
    record(
        "roof_underside_plane", max(plane_errors) < 1e-5, {"max_plane_error_m": max(plane_errors)}
    )
    infill_errors = []
    for obj in _owned().objects:
        if str(obj.get("lesson_role", "")).endswith("roof infill"):
            evaluated = obj.evaluated_get(depsgraph)
            infill_errors.extend(
                abs(
                    (evaluated.matrix_world @ vertex.co).z
                    - (3 + 0.04 * ((evaluated.matrix_world @ vertex.co).y + oh))
                )
                for vertex in evaluated.data.vertices
                if vertex.co.z > 0
            )
    record(
        "closed_roof_wall_infill",
        len(infill_errors) == 16 and max(infill_errors) < 1e-5,
        {"top_vertices": len(infill_errors), "max_plane_error_m": max(infill_errors)},
    )
    invalid = [
        o.name
        for o in _owned().objects
        if o.animation_data and any(not f.driver.is_valid for f in o.animation_data.drivers)
    ]
    record("valid_dimension_drivers", not invalid, {"invalid_objects": invalid})
    topology_errors = []
    for role, (category, _) in ROLE_CONTRACT.items():
        if category != "wall":
            continue
        obj = _object(role).evaluated_get(depsgraph)
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        if (
            not bm.faces
            or not all(edge.is_manifold for edge in bm.edges)
            or not all(vertex.is_manifold for vertex in bm.verts)
            or any(face.calc_area() <= 1e-12 for face in bm.faces)
        ):
            topology_errors.append(role)
        bm.free()
    record(
        "closed_manifold_wall_solids",
        not topology_errors,
        {"wall_roles": 32, "invalid_roles": topology_errors},
    )
    volumes = [_volume(o, depsgraph) for o in _owned().objects if o.get("category") == "wall"]
    record(
        "positive_wall_solids",
        all(v > 0 for v in volumes),
        {"wall_solids": len(volumes), "summed_volume_m3": sum(volumes)},
    )
    return {
        **_result(str(controller["stage"])),
        "passed": all(c["passed"] for c in checks.values()),
        "checks": checks,
        "limitations": [
            "Authored concept; no structural, services, code or weatherproofing verification",
            "Roof can be hidden by its returned owned name to inspect the rooms",
        ],
    }
