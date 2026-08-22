"""Generate ONE `execute_tool_script` program per batch (principle P3).

Epic's `ProgrammaticToolset.execute_tool_script` runs a sandboxed Python
script inside the editor that may call any registered tool through
`execute_tool(tool_name, json_input)`. N actor operations therefore cost one
HTTP round-trip instead of N, which matters more here than on the Blender
side because every UE tool call is serialized onto the game thread.

Environment contract, read live from `get_execution_environment` on 5.8.1:

- the script MUST define `run()` returning a dict;
- `execute_tool` takes the FULLY QUALIFIED tool name and a JSON string, and
  raises RuntimeError on failure (no error checking needed in-script);
- importable modules are exactly {json, math, datetime, copy, re, time}.

The interpreter below mirrors the Blender batch interpreter's op vocabulary
so the same batch shapes work against either DCC.
"""

from __future__ import annotations

import json
from typing import Any

# Fully-qualified names are resolved by the catalog at call time and injected
# here, never hardcoded: Epic's module paths drift between point builds.
SCENE = "editor_toolset.toolsets.scene.SceneTools"
ACTOR = "editor_toolset.toolsets.actor.ActorTools"

_PRELUDE = """
import json

def _call(tool, payload):
    return execute_tool(tool, json.dumps(payload))

def _spawn_asset(asset_path, name, xform, snap):
    return _call("{scene}.add_to_scene_from_asset", {{
        "asset_path": asset_path, "name": name,
        "xform": xform, "snap_to_ground": snap}})["returnValue"]

def _spawn_class(actor_type, name, xform, snap):
    return _call("{scene}.add_to_scene_from_class", {{
        "actor_type": {{"refPath": actor_type}}, "name": name,
        "xform": xform, "snap_to_ground": snap}})["returnValue"]

def _set_xform(actor, xform):
    return _call("{actor}.set_actor_transform", {{
        "actor": actor, "xform": xform, "worldspace": True}})["returnValue"]

def _get_xform(actor):
    return _call("{actor}.get_actor_transform", {{"actor": actor}})["returnValue"]

def _label(actor):
    return _call("{actor}.get_label", {{"actor": actor}})["returnValue"]

def _remove(actor):
    return _call("{scene}.remove_from_scene", {{"actor": actor}})["returnValue"]

def _entity(ref):
    # Values returned by execute_tool are _StrictDict: .get(key, default) is
    # rejected by the sandbox, only direct [] access works (verified live,
    # 5.8.1 - it is not in get_execution_environment's instructions).
    loc = _get_xform(ref)["location"]
    return {{
        "ref": ref["refPath"],
        "label": _label(ref),
        "location": [loc["x"], loc["y"], loc["z"]],
    }}
"""


def _xform(props: dict[str, Any]) -> dict[str, Any]:
    """Epic's transform converter: every field optional, omitted = unchanged,
    rotation in DEGREES."""
    out: dict[str, Any] = {}
    if "location" in props:
        x, y, z = props["location"]
        out["location"] = {"x": float(x), "y": float(y), "z": float(z)}
    if "rotation" in props:
        pitch, yaw, roll = props["rotation"]
        out["rotation"] = {"pitch": float(pitch), "yaw": float(yaw), "roll": float(roll)}
    if "scale" in props:
        x, y, z = props["scale"]
        out["scale"] = {"x": float(x), "y": float(y), "z": float(z)}
    return out


def normalize_batch(ops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Translate TEE batch ops into the script's own compact instruction form,
    so all validation happens server-side before anything touches the editor."""
    out: list[dict[str, Any]] = []
    for index, op in enumerate(ops):
        kind = op.get("op")
        props = dict(op.get("props") or {})
        if kind == "create":
            asset = props.get("asset_path") or op.get("asset_path")
            actor_type = props.get("actor_type") or op.get("actor_type")
            if not asset and not actor_type:
                raise ValueError(
                    f"batch index {index}: 'create' needs asset_path or actor_type "
                    "(e.g. asset_path='/Engine/BasicShapes/Cube')"
                )
            out.append(
                {
                    "op": "create",
                    "asset_path": asset,
                    "actor_type": actor_type,
                    "name": op.get("name") or f"Actor{index}",
                    "xform": _xform(props),
                    "snap": bool(props.get("snap_to_ground")),
                }
            )
        elif kind in ("set", "delete"):
            if not op.get("id"):
                raise ValueError(f"batch index {index}: '{kind}' needs an entity id")
            entry: dict[str, Any] = {"op": kind, "id": op["id"]}
            if kind == "set":
                entry["xform"] = _xform(props)
            out.append(entry)
        else:
            raise ValueError(
                f"batch index {index}: unknown op {kind!r} (supported: create, set, delete)"
            )
    return out


def program_batch(ops: list[dict[str, Any]], refs: dict[str, str]) -> str:
    """`refs` maps TEE entity ids to the actor refPaths the editor knows."""
    prelude = _PRELUDE.format(scene=SCENE, actor=ACTOR)
    return (
        prelude
        # Embedded as JSON text parsed in-script, never as Python source:
        # JSON null/true/false are not Python literals and NameError inside
        # the sandbox the moment an optional field is absent.
        + f"\n_OPS = json.loads({json.dumps(json.dumps(normalize_batch(ops)))})\n"
        + f"_REFS = json.loads({json.dumps(json.dumps(refs))})\n"
        + _INTERPRETER
    )


_INTERPRETER = """
def run():
    created, modified, deleted, details = [], [], [], {}
    for i, op in enumerate(_OPS):
        kind = op["op"]
        if kind == "create":
            if op.get("asset_path"):
                ref = _spawn_asset(op["asset_path"], op["name"], op["xform"], op["snap"])
            else:
                ref = _spawn_class(op["actor_type"], op["name"], op["xform"], op["snap"])
            key = ref["refPath"]
            created.append(key)
            details[key] = _entity(ref)
        elif kind == "set":
            ref = {"refPath": _REFS[op["id"]]}
            if op.get("xform"):
                _set_xform(ref, op["xform"])
            key = ref["refPath"]
            if key not in created and key not in modified:
                modified.append(key)
            details[key] = _entity(ref)
        elif kind == "delete":
            ref = {"refPath": _REFS[op["id"]]}
            _remove(ref)
            key = ref["refPath"]
            deleted.append(key)
            details.pop(key, None)
    return {"created": created, "modified": modified,
            "deleted": deleted, "details": details}
"""

LIST_ACTORS = f'''
import json

def run():
    # ONE tool dispatch. Every execute_tool call costs ~0.37s serialized on
    # the game thread (measured, 5.8.1), so a listing must not be O(actors):
    # labels and transforms are detail, fetched only for entities the model
    # actually asks about (P1/P5).
    actors = execute_tool("{SCENE}.find_actors", json.dumps(
        {{"name": "", "tag": "", "collision_channels": []}}))["returnValue"]
    return {{"actors": [{{"ref": a["refPath"]}} for a in actors]}}
'''


def details_program(refs: list[str]) -> str:
    """Label + transform for a BOUNDED set of actors (2 dispatches each)."""
    prelude = _PRELUDE.format(scene=SCENE, actor=ACTOR)
    return prelude + f"\n_REFS = json.loads({json.dumps(json.dumps(refs))})\n" + _DETAILS


_DETAILS = """
def run():
    out = []
    for ref in _REFS:
        out.append(_entity({"refPath": ref}))
    return {"actors": out}
"""


def restore_program(actors: list[dict[str, Any]]) -> str:
    """Delete actors that are not in the snapshot, and move the rest back."""
    prelude = _PRELUDE.format(scene=SCENE, actor=ACTOR)
    payload = json.dumps({a["ref"]: a for a in actors})
    return prelude + f"\n_WANTED = json.loads({json.dumps(payload)})\n" + _RESTORE


_RESTORE = """
def run():
    found = execute_tool("{scene}.find_actors", json.dumps(
        {"name": "", "tag": "", "collision_channels": []}))["returnValue"]
    removed, moved = [], []
    for a in found:
        ref = a["refPath"]
        if ref not in _WANTED:
            _remove(a)
            removed.append(ref)
    # Transforms are re-applied only for actors TEE itself moved this
    # session. Reading every actor's transform to diff it would cost ~0.37s
    # per actor; and a TEE checkpoint's job is to unwind TEE's own batches,
    # not to fight the user's manual edits.
    for ref, want in _WANTED.items():
        loc = want["location"]
        if loc is None:
            continue
        _set_xform({"refPath": ref},
                   {"location": {"x": loc[0], "y": loc[1], "z": loc[2]}})
        moved.append(ref)
    return {"removed": removed, "moved": moved}
""".replace("{scene}", SCENE)


BLUEPRINT = "editor_toolset.toolsets.blueprint.BlueprintTools"


def blueprint_function_program(
    folder: str,
    asset_name: str,
    function_name: str,
    dsl: str,
    params: list[dict[str, Any]],
    parent_class: str,
    warnings_as_errors: bool,
) -> str:
    """Create-or-reuse a Blueprint, add a typed function graph, write the DSL,
    read it back, and compile - all in ONE round-trip."""
    payload = {
        "folder": folder,
        "asset_name": asset_name,
        "function_name": function_name,
        "dsl": dsl,
        "params": params,
        "parent_class": parent_class,
        "warnings_as_errors": warnings_as_errors,
    }
    return (
        "import json\n\n"
        f"_ARGS = json.loads({json.dumps(json.dumps(payload))})\n"
        f'_BP = "{BLUEPRINT}"\n' + _BLUEPRINT_BODY
    )


_BLUEPRINT_BODY = """
def _bp(tool, payload):
    return execute_tool(_BP + "." + tool, json.dumps(payload))["returnValue"]

def run():
    blueprint = _bp("create", {
        "folder_path": _ARGS["folder"],
        "asset_name": _ARGS["asset_name"],
        "asset_type": {"refPath": _ARGS["parent_class"]}})
    graph = _bp("add_function_graph", {
        "blueprint": blueprint, "graph_name": _ARGS["function_name"]})
    for p in _ARGS["params"]:
        _bp("add_function_param", {
            "graph": graph, "param_name": p["name"],
            "param_type": p["type"], "input_param": p["input"]})
    _bp("write_graph_dsl", {"graph": graph, "code": _ARGS["dsl"]})
    readback = _bp("read_graph_dsl", {"graph": graph})
    out = {"blueprint": blueprint["refPath"], "graph": graph["refPath"],
           "readback": readback}
    try:
        _bp("compile_blueprint", {"blueprint": blueprint,
                                  "warnings_as_errors": _ARGS["warnings_as_errors"]})
        out["compile"] = "clean"
    except RuntimeError as exc:
        out["compile"] = "failed"
        out["compile_error"] = str(exc)[:800]
    return out
"""
