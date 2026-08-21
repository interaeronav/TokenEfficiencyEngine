"""Blender virtual tools (bl_*) registered into the progressive-disclosure
registry when the Blender adapter is active. Discoverable via
tee_search_tools; invoked via tee_call."""

from __future__ import annotations

import time
from typing import Any

from tee.adapters.blender import codegen
from tee.adapters.blender.adapter import BlenderAdapter
from tee.app import TeeApp
from tee.kernel.registry import VirtualTool

_STATS_PROGRAM = (
    codegen.PRELUDE
    + """
_meshes = [o for o in bpy.data.objects if o.type == 'MESH']
_total_verts = sum(len(o.data.vertices) for o in _meshes)
_total_polys = sum(len(o.data.polygons) for o in _meshes)

def _world_aabb(o):
    from mathutils import Vector
    corners = [o.matrix_world @ Vector(c) for c in o.bound_box]
    xs = [c.x for c in corners]; ys = [c.y for c in corners]; zs = [c.z for c in corners]
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))

_boxes = {_uid(o): _world_aabb(o) for o in _meshes}
_overlaps = []
_names = list(_boxes)
for _a in range(len(_names)):
    for _b in range(_a + 1, len(_names)):
        A, B = _boxes[_names[_a]], _boxes[_names[_b]]
        if A[0] < B[3] and B[0] < A[3] and A[1] < B[4] and B[1] < A[4] \\
                and A[2] < B[5] and B[2] < A[5]:
            _overlaps.append([_names[_a], _names[_b]])
            if len(_overlaps) >= 20:
                break
    if len(_overlaps) >= 20:
        break
_below = [_uid(o) for o in _meshes if _world_aabb(o)[2] < -0.001][:20]
result = {
    "meshes": len(_meshes),
    "total_verts": _total_verts,
    "total_polys": _total_polys,
    "overlapping_pairs": _overlaps,
    "below_ground": _below,
}
"""
)


def register_blender_tools(app: TeeApp, adapter: BlenderAdapter) -> None:
    reg = app.registry

    def execute_python(args: dict[str, Any]) -> dict[str, Any]:
        cache = app.cache("blender")
        cp = app.checkpoints.create(adapter, f"auto:exec-r{cache.revision + 1}", cache.revision)
        out = adapter.execute_python(args["code"], timeout=args.get("timeout") or 60.0)
        cache.resync(adapter)  # arbitrary code may have changed anything
        return {"checkpoint": cp.id, **out, **cache.stamp()}

    reg.register(
        VirtualTool(
            name="bl_execute_python",
            description=(
                "Run arbitrary Python inside Blender (escape hatch). "
                "Auto-checkpoints first; validates against known stale-API "
                "idioms for the connected version; assign a dict to `result` "
                "to return data. Prefer typed tee_batch ops when they cover "
                "the task - they are cheaper and diff-tracked."
            ),
            schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "timeout": {"type": "number"},
                },
                "required": ["code"],
            },
            handler=execute_python,
            tags=["blender", "python", "escape-hatch", "script"],
            examples=[{"code": "import bpy\nresult = {'objects': len(bpy.data.objects)}"}],
        )
    )

    def scene_stats(args: dict[str, Any]) -> dict[str, Any]:
        return adapter._call(_STATS_PROGRAM, timeout=30.0)

    reg.register(
        VirtualTool(
            name="bl_scene_stats",
            description=(
                "Cheap geometric checks in text (principle: text before "
                "pixels): mesh/vert/poly counts, world-AABB overlapping "
                "pairs, objects below ground plane. Use this to verify a "
                "scene before ever requesting a screenshot."
            ),
            schema={"type": "object", "properties": {}},
            handler=scene_stats,
            tags=["blender", "verify", "geometry", "stats", "overlap"],
        )
    )

    def assign_material(args: dict[str, Any]) -> dict[str, Any]:
        props = {k: v for k, v in args.items() if k != "entity_id"}
        return app.run_batch(
            "blender",
            [{"op": "assign_material", "id": args["entity_id"], "props": props}],
        )

    reg.register(
        VirtualTool(
            name="bl_assign_material",
            description=(
                "Create/reuse a Principled BSDF material and assign it to a "
                "mesh entity. Uses version-correct socket names (Base Color, "
                "Metallic, Roughness, Emission Color/Strength). Checkpointed "
                "and diff-tracked like any batch."
            ),
            schema={
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string"},
                    "material": {"type": "string"},
                    "base_color": {"type": "array"},
                    "metallic": {"type": "number"},
                    "roughness": {"type": "number"},
                    "emission_color": {"type": "array"},
                    "emission_strength": {"type": "number"},
                },
                "required": ["entity_id"],
            },
            handler=assign_material,
            tags=["blender", "material", "shader", "pbr"],
            examples=[{"entity_id": "b42", "base_color": [0.8, 0.1, 0.1], "roughness": 0.4}],
        )
    )

    def render(args: dict[str, Any]) -> dict[str, Any]:
        width = int(args.get("width") or 960)
        height = int(args.get("height") or 540)
        samples = int(args.get("samples") or 32)
        path = args.get("path") or f"{adapter.workdir}/render-{int(time.time())}.jpg"

        def job() -> dict[str, Any]:
            start = time.time()
            adapter._call(
                codegen.program_capture(path, width, height, 90, samples),
                timeout=1800.0,
            )
            return {"path": path, "seconds": round(time.time() - start, 1)}

        job_id = app.jobs.submit(f"render {width}x{height}", job)
        return {
            "job": job_id,
            "note": (
                "Rendering in the background; poll tee_job. The bridge "
                "serves one request at a time, so other Blender calls wait "
                "until it finishes."
            ),
        }

    reg.register(
        VirtualTool(
            name="bl_render",
            description=(
                "Full-quality render to a file on disk as an async job "
                "(poll tee_job). Returns a file path, never inline pixels. "
                "For a quick look use tee_capture (small inline JPEG) "
                "or bl_scene_stats (text) instead."
            ),
            schema={
                "type": "object",
                "properties": {
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                    "samples": {"type": "integer"},
                    "path": {"type": "string"},
                },
            },
            handler=render,
            tags=["blender", "render", "image", "job"],
        )
    )
