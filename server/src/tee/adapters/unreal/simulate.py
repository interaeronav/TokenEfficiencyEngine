"""Simulate-In-Editor settle for Unreal - the flagship gap Epic leaves open.

Epic's official MCP ships **no simulation toolset**: PhysicsAssetToolset
authors ragdolls and DataflowAgentToolset builds asset graphs, but nothing
runs a sim or reads the result. "Keep Simulation Changes" has no API either.
TEE's macro replaces it: start SIE, poll the play world across many SHORT
calls, stop, and write the settled poses onto the editor actors.

Two engine constraints shape the whole design:

1. **The editor does not tick while a Python call executes.** A blocking
   wait loop inside one call freezes the sim forever. The sanctioned pattern
   is many short calls with the sim advancing between them - which is exactly
   TEE's request/response cadence, so the polling loop lives on the TEE side.

2. **A backgrounded editor does not tick at all.** Verified on 5.8.1: with
   `bThrottleCPUWhenNotForeground` at its default True and the editor window
   behind another app, the play world reports `is_in_play_in_editor() == True`
   and the body reports `is_simulating_physics() == True`, while
   `get_time_seconds()` stays pinned at 0.0 and nothing moves. An agent
   polling that would conclude the scene settled instantly. `settle` therefore
   asserts that sim time actually advances and fails with the exact fix rather
   than returning a confident wrong answer.
"""

from __future__ import annotations

from typing import Any

SETTLE_DEFAULTS: dict[str, Any] = {
    "min_s": 1.0,  # sim seconds before quiescence may be declared
    "max_s": 30.0,  # give up after this much SIM time
    "window_s": 0.8,  # quiet for this long (sim seconds) = settled
    "loc_eps_cm": 1.0,  # UE works in centimetres
    "poll_pause_s": 0.25,  # wall-clock gap that lets the editor tick
    "max_polls": 240,
}

START = """
import unreal
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_play_simulate()
result = {"requested": True}
"""

STOP = """
import unreal
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
result = {"requested": True}
"""


def poll_program(labels: list[str]) -> str:
    """One cheap read of the play world. Deliberately does no waiting: the
    editor cannot tick while this runs."""
    import json as _json

    return f"""
import unreal
_WANT = set({_json.dumps(labels)})
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
out = {{"in_pie": les.is_in_play_in_editor(), "poses": {{}}}}
if gw is not None:
    out["t"] = unreal.GameplayStatics.get_time_seconds(gw)
    for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
        label = a.get_actor_label()
        if label in _WANT:
            loc = a.get_actor_location()
            rot = a.get_actor_rotation()
            out["poses"][label] = [loc.x, loc.y, loc.z, rot.pitch, rot.yaw, rot.roll]
result = out
"""


def read_editor_poses_program(labels: list[str]) -> str:
    import json as _json

    return f"""
import unreal
_WANT = set({_json.dumps(labels)})
aes = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
poses = {{}}
for a in aes.get_all_level_actors():
    label = a.get_actor_label()
    if label in _WANT:
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        poses[label] = [loc.x, loc.y, loc.z, rot.pitch, rot.yaw, rot.roll]
result = {{"poses": poses}}
"""


def adopt_program(poses: dict[str, list[float]]) -> str:
    """Write settled play-world poses onto the editor actors.

    This is what "Keep Simulation Changes" does in the UI, which has no
    scripting API at all - the reason this macro exists.
    """
    import json as _json

    return f"""
import json
import unreal
_POSES = json.loads({_json.dumps(_json.dumps(poses))})
aes = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
applied = []
for a in aes.get_all_level_actors():
    label = a.get_actor_label()
    if label in _POSES:
        x, y, z, pitch, yaw, roll = _POSES[label]
        a.set_actor_location_and_rotation(
            unreal.Vector(x, y, z), unreal.Rotator(pitch, yaw, roll),
            sweep=False, teleport=True)
        applied.append(label)
result = {{"applied": applied}}
"""


def max_delta(a: dict[str, list[float]], b: dict[str, list[float]]) -> float:
    """Largest positional movement (cm) between two pose snapshots.

    Returns infinity when a snapshot is missing an actor rather than 0.0: an
    empty or partial reading means "we do not know", and treating unknown as
    "nothing moved" would declare a scene settled the instant the play world
    had not finished spawning.
    """
    if not a or not b or set(a) != set(b):
        return float("inf")
    worst = 0.0
    for label, pose in a.items():
        other = b[label]
        worst = max(worst, max(abs(pose[i] - other[i]) for i in range(3)))
    return worst


def import_program(
    path: str,
    destination: str,
    label: str,
    location: list[float],
    scale: float,
) -> str:
    """Import a mesh file and spawn it, returning measured world bounds.

    Epic's `AssetTools` toolset has no import call at all (it can find, load,
    save and delete assets, but not bring one in), so this needs the
    unsandboxed lane and TEE's content plugin.
    """
    import json as _json

    args = {
        "path": path,
        "destination": destination,
        "label": label,
        "location": location,
        "scale": scale,
    }
    return f"""
import json
import unreal
_A = json.loads({_json.dumps(_json.dumps(args))})

task = unreal.AssetImportTask()
task.filename = _A["path"]
task.destination_path = _A["destination"]
task.automated = True
task.replace_existing = True
task.save = False
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
paths = [str(p) for p in task.get_editor_property("imported_object_paths")]

meshes = []
for p in paths:
    obj = unreal.EditorAssetLibrary.load_asset(p)
    if isinstance(obj, unreal.StaticMesh):
        meshes.append((p, obj))

out = {{"imported": paths, "meshes": [p for p, _ in meshes]}}
if meshes:
    aes = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    loc = _A["location"]
    actor = aes.spawn_actor_from_object(
        meshes[0][1], unreal.Vector(loc[0], loc[1], loc[2]))
    actor.set_actor_label(_A["label"])
    s = _A["scale"]
    if s != 1.0:
        actor.set_actor_scale3d(unreal.Vector(s, s, s))
    origin, extent = actor.get_actor_bounds(False)
    out["actor"] = actor.get_path_name()
    out["label"] = actor.get_actor_label()
    # UE is centimetres; TEE speaks metres everywhere else.
    out["dims_m"] = [round(extent.x * 2 / 100.0, 4),
                     round(extent.y * 2 / 100.0, 4),
                     round(extent.z * 2 / 100.0, 4)]
result = out
"""
