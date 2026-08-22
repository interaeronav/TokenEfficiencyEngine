"""Editor-side programs for the pin lane (Unreal, unsandboxed Python).

Epic's sandboxed script lane cannot import `unreal`, and its registered
toolsets expose no way to read or write an actor's Tags array, so pins run
through TEE's content plugin. Every program is ONE dispatch and returns a
compact dict; nothing here dumps the scene.
"""

from __future__ import annotations

import json
from typing import Any

#: The marker mesh: engine primitive, 100 uu cube-bounded, pivot at centre.
MARKER_MESH = "/Engine/BasicShapes/Cone.Cone"
MARKER_MATERIAL = "/Game/TeeAssets/Pins/MI_TeePin"
MARKER_PARENT_MATERIAL = "/Engine/BasicShapes/BasicShapeMaterial"
MARKER_DIR = "/Game/TeeAssets/Pins"
MARKER_HEIGHT_CM = 50.0
MARKER_RADIUS_CM = 9.0
PIN_FOLDER = "TEE/Pins"


def _args(payload: dict[str, Any]) -> str:
    """Embed arguments as JSON text parsed in-script: JSON null/true/false are
    not Python literals, and a bare None in generated source is a NameError."""
    return f"import json\n_A = json.loads({json.dumps(json.dumps(payload))})\n"


_HELPERS = '''
import json
import unreal

_AES = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def _tags(actor):
    return [str(t) for t in actor.tags]


def _pins(namespace):
    """Every pin actor in the level, cheapest-first: one in-process pass."""
    out = []
    for actor in _AES.get_all_level_actors():
        tags = _tags(actor)
        if namespace in tags:
            out.append((actor, tags))
    return out


def _find(namespace, pin_id):
    wanted = (namespace + "_id:" + pin_id).lower()
    for actor, tags in _pins(namespace):
        if any(t.lower() == wanted for t in tags):
            return actor
    return None


def _by_label(label):
    # EVERY match: a label is not unique in Unreal, and a fill that was
    # interrupted can leave two actors stacked on the same spot.
    return [a for a in _AES.get_all_level_actors() if a.get_actor_label() == label]


def _report(actor, namespace):
    loc = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    return {
        "actor": actor.get_path_name(),
        "label": actor.get_actor_label(),
        "tags": _tags(actor),
        "location_m": [round(loc.x / 100.0, 4), round(loc.y / 100.0, 4),
                       round(loc.z / 100.0, 4)],
        "yaw": round(rot.yaw, 2),
    }
'''


READ = (
    _HELPERS
    + """
def _run():
    rows = []
    for actor, tags in _pins(_A["namespace"]):
        rows.append(_report(actor, _A["namespace"]))
    # A pin's marker sits with its BASE on the spot; the reported position is
    # the spot itself, not the marker's centre.
    for row in rows:
        row["location_m"][2] = round(row["location_m"][2] - _A["half_height_m"], 4)
    return {"pins": rows}


result = _run()
"""
)


UPSERT = (
    _HELPERS
    + """
def _ensure_material():
    # A bright instance of the engine's own basic-shape material. An authored
    # emissive Material would read better, but on 5.8.1
    # MaterialEditingLibrary.connect_material_property returns True while the
    # compiled shader keeps the default graph (95 pixel instructions, renders
    # black) - a silent no-op. Parametrising a shipped material is verifiable:
    # the colour reads back.
    path = _A["material"]
    mel = unreal.MaterialEditingLibrary
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        folder, _, name = path.rpartition("/")
        tools.create_asset(name, folder, unreal.MaterialInstanceConstant,
                           unreal.MaterialInstanceConstantFactoryNew())
    inst = unreal.EditorAssetLibrary.load_asset(path)
    if inst.get_editor_property("parent") is None:
        mel.set_material_instance_parent(
            inst, unreal.EditorAssetLibrary.load_asset(_A["parent_material"]))
    colour = unreal.LinearColor(1.0, 0.25, 0.02, 1.0)
    # The setter returns False even when it applies, so verify by reading back
    # rather than trusting it.
    mel.set_material_instance_vector_parameter_value(inst, "Color", colour)
    mel.set_material_instance_scalar_parameter_value(inst, "Roughness", 0.9)
    mel.update_material_instance(inst)
    got = mel.get_material_instance_vector_parameter_value(inst, "Color")
    if abs(got.r - colour.r) > 0.01 or abs(got.g - colour.g) > 0.01:
        raise RuntimeError("pin marker colour did not stick: " + str(got))
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    return inst


def _spawn(loc_cm):
    mesh = unreal.EditorAssetLibrary.load_asset(_A["mesh"])
    actor = _AES.spawn_actor_from_object(
        mesh, unreal.Vector(loc_cm[0], loc_cm[1], loc_cm[2] + _A["half_height_cm"]))
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    # Collision is set AT SPAWN: a marker must never block the player, and a
    # component whose collision is changed later can miss the physics rebuild.
    comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    comp.set_material(0, _ensure_material())
    actor.set_actor_scale3d(unreal.Vector(
        _A["radius_cm"] / 50.0, _A["radius_cm"] / 50.0, _A["height_cm"] / 100.0))
    # Editor-only: the marker is an authoring aid and is stripped from any
    # cooked build rather than shipping inside the walkable twin.
    actor.set_editor_property("is_editor_only_actor", True)
    actor.set_folder_path(_A["folder"])
    return actor


def _run():
    actor = _find(_A["namespace"], _A["id"])
    created = actor is None
    if created:
        if _A["location_cm"] is None:
            return {"error": "no_location"}
        actor = _spawn(_A["location_cm"])
    elif _A["location_cm"] is not None:
        loc = _A["location_cm"]
        actor.set_actor_location(
            unreal.Vector(loc[0], loc[1], loc[2] + _A["half_height_cm"]), False, True)
    if _A["yaw"] is not None:
        rot = unreal.Rotator()
        rot.pitch = 0.0
        rot.roll = 0.0
        rot.yaw = float(_A["yaw"])
        actor.set_actor_rotation(rot, False)
    actor.set_actor_label(_A["label"])
    actor.tags = [unreal.Name(t) for t in _A["tags"]]
    out = _report(actor, _A["namespace"])
    out["created"] = created
    out["location_m"][2] = round(out["location_m"][2] - _A["half_height_m"], 4)
    origin, extent = actor.get_actor_bounds(False)
    out["marker_base_z_m"] = round((origin.z - extent.z) / 100.0, 4)
    out["marker_size_m"] = [round(extent.x * 2 / 100.0, 3), round(extent.y * 2 / 100.0, 3),
                            round(extent.z * 2 / 100.0, 3)]
    return out


result = _run()
"""
)


REMOVE = (
    _HELPERS
    + """
def _run():
    actor = _find(_A["namespace"], _A["id"])
    if actor is None:
        return {"removed": False}
    filled = 0
    if _A["label_of_fill"] and _A["remove_fill"]:
        for fill in _by_label(_A["label_of_fill"]):
            _AES.destroy_actor(fill)
            filled += 1
    label = actor.get_actor_label()
    _AES.destroy_actor(actor)
    return {"removed": True, "label": label, "removed_fill": filled or None}


result = _run()
"""
)


CLEAR_FILL = (
    _HELPERS
    + """
def _run():
    # Delete whatever currently stands at this pin, by its actor label.
    found = _by_label(_A["label_of_fill"])
    for fill in found:
        _AES.destroy_actor(fill)
    return {"removed": len(found)}


result = _run()
"""
)


def read_program(namespace: str) -> str:
    return _args({"namespace": namespace, "half_height_m": MARKER_HEIGHT_CM / 200.0}) + READ


def upsert_program(
    namespace: str,
    pin_id: str,
    label: str,
    tags: list[str],
    location_cm: list[float] | None,
    yaw: float | None,
) -> str:
    payload = {
        "namespace": namespace,
        "id": pin_id,
        "label": label,
        "tags": tags,
        "location_cm": location_cm,
        "yaw": yaw,
        "mesh": MARKER_MESH,
        "material": MARKER_MATERIAL,
        "parent_material": MARKER_PARENT_MATERIAL,
        "folder": PIN_FOLDER,
        "height_cm": MARKER_HEIGHT_CM,
        "radius_cm": MARKER_RADIUS_CM,
        "half_height_cm": MARKER_HEIGHT_CM / 2.0,
        "half_height_m": MARKER_HEIGHT_CM / 200.0,
    }
    return _args(payload) + UPSERT


def remove_program(
    namespace: str, pin_id: str, label_of_fill: str | None, remove_fill: bool
) -> str:
    return (
        _args(
            {
                "namespace": namespace,
                "id": pin_id,
                "label_of_fill": label_of_fill,
                "remove_fill": remove_fill,
            }
        )
        + REMOVE
    )


def clear_fill_program(label_of_fill: str) -> str:
    return _args({"label_of_fill": label_of_fill}) + CLEAR_FILL
