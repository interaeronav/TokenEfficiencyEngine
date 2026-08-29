"""Blender physics lane (A19): settle/drop, cloth drape, bake-all.

Programs run inside Blender via the adapter's python channel (typed
tools, not the model-facing code-exec escape hatch). All stepping is
STRICTLY sequential frame_set with fixed substeps - deterministic on
this machine and build; never across builds (the contract every tool
description repeats). Quiescence is BlenderProc-shaped: windows of
~2 s must move less than 1 cm / 0.1 rad, minimum 4 s, cap ~40 s.

Reports are compact facts (settled flag, moved deltas, max displacement,
wall time) - never per-frame data. Bake-before-checkpoint: memory
caches persist inside .blend snapshots, so `sim_bake_all` is the
checkpoint-prep step.
"""

from __future__ import annotations

import json
import time
from typing import Any

from tee.kernel.errors import TeeError

SETTLE_DEFAULTS = {
    "fps": 24,
    "substeps": 10,
    "iterations": 10,
    "min_s": 4.0,
    "max_s": 40.0,
    "window_s": 2.0,
    "loc_eps_m": 0.01,
    "rot_eps_rad": 0.1,
}

# cloth presets: Blender's bundled parameter sets (5.2 values)
CLOTH_PRESETS = {
    "cotton": {
        "mass": 0.3,
        "tension_stiffness": 15,
        "compression_stiffness": 15,
        "shear_stiffness": 15,
        "bending_stiffness": 0.5,
    },
    "denim": {
        "mass": 1.0,
        "tension_stiffness": 40,
        "compression_stiffness": 40,
        "shear_stiffness": 40,
        "bending_stiffness": 10,
    },
    "leather": {
        "mass": 0.4,
        "tension_stiffness": 80,
        "compression_stiffness": 80,
        "shear_stiffness": 80,
        "bending_stiffness": 150,
    },
    "silk": {
        "mass": 0.15,
        "tension_stiffness": 5,
        "compression_stiffness": 5,
        "shear_stiffness": 5,
        "bending_stiffness": 0.05,
    },
    "rubber": {
        "mass": 3.0,
        "tension_stiffness": 15,
        "compression_stiffness": 15,
        "shear_stiffness": 15,
        "bending_stiffness": 25,
    },
}

DETERMINISM_NOTE = (
    "same machine+build only (pinned stepping); assert above the variance floor (benchmarks/)"
)


def settle_program(
    active_ids: list[str] | None,
    passive_ids: list[str] | None,
    *,
    adopt: bool = False,
    params: dict[str, Any] | None = None,
) -> str:
    cfg = {**SETTLE_DEFAULTS, **(params or {})}
    return f"""
import bpy, math, time
_t0 = time.time()
_cfg = {json.dumps(cfg)}
_active_ids = {json.dumps(active_ids)}
_passive_ids = {json.dumps(passive_ids)}
_adopt = {adopt!r}

def _uid(o):
    return "b%d" % o.session_uid

def _by_ids(ids):
    if ids is None:
        return None
    want = set(int(str(i)[1:]) for i in ids)
    return [o for o in bpy.data.objects if o.session_uid in want]

scene = bpy.context.scene
if scene.rigidbody_world is None:
    bpy.ops.rigidbody.world_add()
world = scene.rigidbody_world
world.substeps_per_frame = int(_cfg["substeps"])
world.solver_iterations = int(_cfg["iterations"])
if world.collection is None:
    world.collection = bpy.data.collections.new("RigidBodyWorld")

_meshes = [o for o in bpy.data.objects if o.type == "MESH"]
_actives = _by_ids(_active_ids)
if _actives is None:
    _actives = [o for o in _meshes if o.rigid_body is not None
                and o.rigid_body.type == "ACTIVE"] or _meshes
_passives = _by_ids(_passive_ids) or [o for o in _meshes if o not in _actives]

for o in _actives:
    if o.rigid_body is None:
        with bpy.context.temp_override(object=o, active_object=o):
            bpy.ops.rigidbody.object_add(type="ACTIVE")
    o.rigid_body.type = "ACTIVE"
    if "tee_density" in o:
        vol = 1.0
        if o.dimensions[0] * o.dimensions[1] * o.dimensions[2] > 0:
            vol = o.dimensions[0] * o.dimensions[1] * o.dimensions[2]
        o.rigid_body.mass = max(0.01, vol * float(o["tee_density"]))
for o in _passives:
    if o.rigid_body is None:
        with bpy.context.temp_override(object=o, active_object=o):
            bpy.ops.rigidbody.object_add(type="PASSIVE")
    o.rigid_body.type = "PASSIVE"

fps = int(_cfg["fps"])
scene.frame_start = 1
scene.frame_end = int(_cfg["max_s"] * fps) + 1
world.point_cache.frame_start = scene.frame_start
world.point_cache.frame_end = scene.frame_end
scene.frame_set(1)
_start = {{}}
_deps = bpy.context.evaluated_depsgraph_get()
for o in _actives:
    m = o.evaluated_get(_deps).matrix_world
    _start[_uid(o)] = (list(m.translation), list(m.to_euler()))

_window = max(1, int(_cfg["window_s"] * fps))
_prev = dict(_start)
_settled = False
_frame = 1
_max_frame = scene.frame_end
while _frame < _max_frame:
    _frame += 1
    scene.frame_set(_frame)
    if _frame % _window == 0 and _frame >= int(_cfg["min_s"] * fps):
        _deps = bpy.context.evaluated_depsgraph_get()
        _quiet = True
        _cur = {{}}
        for o in _actives:
            m = o.evaluated_get(_deps).matrix_world
            loc, rot = list(m.translation), list(m.to_euler())
            _cur[_uid(o)] = (loc, rot)
            p_loc, p_rot = _prev[_uid(o)]
            d_loc = max(abs(a - b) for a, b in zip(loc, p_loc))
            d_rot = max(abs(a - b) for a, b in zip(rot, p_rot))
            if d_loc > _cfg["loc_eps_m"] or d_rot > _cfg["rot_eps_rad"]:
                _quiet = False
        _prev = _cur
        if _quiet:
            _settled = True
            break

_deps = bpy.context.evaluated_depsgraph_get()
_moved = []
_max_disp = 0.0
_final = {{}}
for o in _actives:
    m = o.evaluated_get(_deps).matrix_world
    loc, rot = list(m.translation), list(m.to_euler())
    _final[_uid(o)] = (loc, rot)
    s_loc, s_rot = _start[_uid(o)]
    d_loc = sum((a - b) ** 2 for a, b in zip(loc, s_loc)) ** 0.5
    d_rot = max(abs(a - b) for a, b in zip(rot, s_rot))
    _max_disp = max(_max_disp, d_loc)
    if d_loc > 0.005 or d_rot > 0.02:
        _moved.append({{"id": _uid(o), "dloc_m": round(d_loc, 4),
                       "drot_rad": round(d_rot, 4)}})

if _adopt:
    for o in _actives:
        loc, rot = _final[_uid(o)]
        o.location = loc
        o.rotation_euler = rot
        with bpy.context.temp_override(object=o, active_object=o):
            bpy.ops.rigidbody.object_remove()
    scene.frame_set(1)

result = {{
    "settled": _settled,
    "frames": _frame,
    "seconds": round(_frame / fps, 2),
    "moved": _moved,
    "max_displacement_m": round(_max_disp, 4),
    "final": {{k: [round(v, 4) for v in loc] for k, (loc, rot) in _final.items()}},
    "final_by_name": {{o.name: [round(v, 4) for v in _final[_uid(o)][0]]
                      for o in _actives}},
    "adopted": bool(_adopt),
    "wall_s": round(time.time() - _t0, 2),
}}
"""


def cloth_program(
    cloth_id: str,
    collision_ids: list[str] | None,
    *,
    preset: str = "cotton",
    seconds: float = 3.0,
    apply_result: bool = False,
) -> str:
    if preset not in CLOTH_PRESETS:
        raise TeeError(
            "unknown_preset",
            f"No cloth preset '{preset}'.",
            fix=f"Presets: {', '.join(sorted(CLOTH_PRESETS))}.",
        )
    cfg = CLOTH_PRESETS[preset]
    return f"""
import bpy, time
_t0 = time.time()

def _find(eid):
    want = int(str(eid)[1:])
    for o in bpy.data.objects:
        if o.session_uid == want:
            return o
    return None

_cloth = _find({cloth_id!r})
if _cloth is None:
    raise ValueError("no entity {cloth_id} for cloth drape")
_collides = []
for _cid in {json.dumps(collision_ids or [])}:
    _o = _find(_cid)
    if _o is not None:
        _collides.append(_o)
for _o in _collides:
    if not any(m.type == "COLLISION" for m in _o.modifiers):
        _o.modifiers.new(name="tee_collide", type="COLLISION")
_mod = _cloth.modifiers.new(name="tee_cloth", type="CLOTH")
_s = _mod.settings
_s.mass = {cfg["mass"]}
_s.tension_stiffness = {cfg["tension_stiffness"]}
_s.compression_stiffness = {cfg["compression_stiffness"]}
_s.shear_stiffness = {cfg["shear_stiffness"]}
_s.bending_stiffness = {cfg["bending_stiffness"]}
_scene = bpy.context.scene
_fps = 24
_frames = int({seconds} * _fps)
_scene.frame_start = 1
_scene.frame_end = _frames + 1
for _f in range(1, _frames + 1):
    _scene.frame_set(_f)
_applied = False
if {apply_result!r}:
    with bpy.context.temp_override(object=_cloth, active_object=_cloth,
                                   selected_objects=[_cloth]):
        bpy.ops.object.modifier_apply(modifier=_mod.name)
    _applied = True
    _scene.frame_set(1)
result = {{
    "preset": {preset!r},
    "frames": _frames,
    "applied": _applied,
    "verts": len(_cloth.data.vertices),
    "wall_s": round(time.time() - _t0, 2),
    "note": "drape is a visual aid - no pass/fail metric (A19)",
}}
"""


def fluid_program(
    domain_size: list[float],
    inflow_location: list[float],
    *,
    resolution: int = 64,
    frames: int = 48,
    cache_dir: str = "",
    fluid_type: str = "liquid",
) -> str:
    """Mantaflow setup + synchronous bake. Cost-gated at the tool layer:
    resolution capped at 64, ALL cache mode, ABSOLUTE cache directory
    (relative paths are a classic silent-failure tracker landmine)."""
    resolution = max(16, min(int(resolution), 64))
    return f"""
import bpy, time
_t0 = time.time()
bpy.ops.mesh.primitive_cube_add(size=1.0)
_domain = bpy.context.active_object
_domain.name = "tee_fluid_domain"
_domain.scale = {json.dumps([v / 2 for v in domain_size])}
_dmod = _domain.modifiers.new(name="tee_fluid", type="FLUID")
_dmod.fluid_type = "DOMAIN"
_ds = _dmod.domain_settings
_ds.domain_type = {json.dumps(fluid_type.upper())}
_ds.resolution_max = {resolution}
_ds.cache_type = "ALL"
_ds.cache_directory = {json.dumps(cache_dir)}
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1,
                                     location={json.dumps(inflow_location)})
_flow = bpy.context.active_object
_flow.name = "tee_fluid_inflow"
_fmod = _flow.modifiers.new(name="tee_flow", type="FLUID")
_fmod.fluid_type = "FLOW"
_fmod.flow_settings.flow_type = {json.dumps(fluid_type.upper() if fluid_type != "gas" else "SMOKE")}
_fmod.flow_settings.flow_behavior = "INFLOW"
_scene = bpy.context.scene
_scene.frame_start = 1
_scene.frame_end = {int(frames)}
with bpy.context.temp_override(object=_domain, active_object=_domain):
    bpy.ops.fluid.bake_all()
result = {{
    "baked_frames": {int(frames)},
    "resolution": {resolution},
    "cache_dir": {json.dumps(cache_dir)},
    "wall_s": round(time.time() - _t0, 2),
    "note": "fluids are approximate - never deterministic cross-run (A19)",
}}
"""


BAKE_ALL_PROGRAM = """
import bpy, time
_t0 = time.time()
_scene = bpy.context.scene
with bpy.context.temp_override(scene=_scene, point_cache=(
        _scene.rigidbody_world.point_cache if _scene.rigidbody_world else None)):
    bpy.ops.ptcache.bake_all(bake=True)
result = {
    "baked": True,
    "wall_s": round(time.time() - _t0, 2),
    "note": "memory caches persist inside .blend snapshots - checkpoint now",
}
"""


def run_program(app, adapter_name: str, code: str, *, timeout: float = 300.0) -> dict[str, Any]:
    adapter = app.adapter(adapter_name)
    runner = getattr(adapter, "execute_python", None)
    if runner is None:
        raise TeeError(
            "unsupported_adapter",
            f"The physics lane needs the Blender adapter (got '{adapter_name}').",
            fix="Run against blender; UE settle arrives with the physical machine.",
        )
    started = time.monotonic()
    out = runner(code, timeout=timeout)
    payload = out.get("result", out) if isinstance(out, dict) else out
    if isinstance(payload, dict):
        payload.setdefault("wall_s", round(time.monotonic() - started, 2))
        payload["determinism"] = DETERMINISM_NOTE
    return payload
