"""Blender handoff & conformance (7.7).

Tier 2 (no add-ons): plan walls become typed batch ops through the EXISTING
kernel machinery - checkpointed, diff-tracked, atomic like any batch. A wall
is a cube rotated about Z with dimensions [length, thickness, height]; the
Blender world is the site ENU frame (datum at origin, meters, Z-up).

Conformance: compare built geometry against plan facts in the common frame;
effective tolerance is the RSS of both tiers' tolerances plus every
transform accuracy on the chain; over-tolerance cases become first-class
conflict facts - the conflict facts ARE the conformance report.
"""

from __future__ import annotations

import math
from typing import Any

from tee.extract.frames import FrameRegistry, rss
from tee.extract.plan import validate_plan, wall_angle, wall_length, wall_midpoint
from tee.extract.store import TIER_TOLERANCE_M, ExtractStore
from tee.kernel.errors import TeeError

BUILD_EXTRACTOR = ("build", "1")
_BATCH_CHUNK = 50


def plan_to_ops(plan: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Typed batch ops for the plan's walls + one floor slab per level.
    Returns (ops, wall ids in op order) - created entity ids come back in
    the same order, which is what the build manifest records."""
    validate_plan(plan)
    levels = {lvl["index"]: lvl for lvl in plan.get("levels") or []}
    ops: list[dict[str, Any]] = []
    wall_order: list[str] = []
    for wall in plan["walls"]:
        level = levels.get(wall.get("level", 0), {"elevation_z": 0.0})
        elevation = float(level.get("elevation_z") or 0.0)
        height = float(wall.get("height") or level.get("ceiling_height") or 2.7)
        mid_x, mid_y = wall_midpoint(wall)
        ops.append(
            {
                "op": "create",
                "kind": "cube",
                "name": f"Wall_{wall['id']}",
                "props": {
                    "size": 1,
                    "location": [
                        round(mid_x, 4),
                        round(mid_y, 4),
                        round(elevation + height / 2, 4),
                    ],
                    "rotation_euler": [0.0, 0.0, round(wall_angle(wall), 6)],
                    "dimensions": [
                        round(wall_length(wall), 4),
                        round(float(wall["thickness"]), 4),
                        round(height, 4),
                    ],
                },
            }
        )
        wall_order.append(wall["id"])

    if plan["walls"]:
        xs = [p for w in plan["walls"] for p in (w["a"][0], w["b"][0])]
        ys = [p for w in plan["walls"] for p in (w["a"][1], w["b"][1])]
        for index, level in (levels or {0: {"elevation_z": 0.0}}).items():
            elevation = float(level.get("elevation_z") or 0.0)
            ops.append(
                {
                    "op": "create",
                    "kind": "cube",
                    "name": f"Slab_L{index}",
                    "props": {
                        "size": 1,
                        "location": [
                            round((min(xs) + max(xs)) / 2, 4),
                            round((min(ys) + max(ys)) / 2, 4),
                            round(elevation - 0.05, 4),
                        ],
                        "dimensions": [
                            round(max(xs) - min(xs) + 0.4, 4),
                            round(max(ys) - min(ys) + 0.4, 4),
                            0.1,
                        ],
                    },
                }
            )
    return ops, wall_order


def register_handoff_tools(
    app, store: ExtractStore, registry: FrameRegistry, *, blender: bool = True
) -> None:
    """The extract-to-scene bridge. `bl_build_from_plan` and
    `bl_check_against_plan` need a served Blender lane and register only
    when `blender` is true; `ex_export_ifc` is an offline IFC writer that
    touches no scene and registers always (A68 - it had been gated on a
    Blender it never used)."""
    from tee.kernel.registry import VirtualTool

    def _plan_fact(source_ref: str) -> tuple[dict[str, Any], dict[str, Any]]:
        source = store.resolve(source_ref)
        plans = store.facts(source["hash"], kind="plan")
        if not plans:
            raise TeeError(
                "no_plan",
                f"Source {source['hash'][:8]} has no plan fact.",
                fix="Extract one first (ex_ingest for DXF/vector PDF, or an "
                "in-band VLM pass via ex_prepare + ex_store_facts).",
            )
        return source, plans[-1]["plan"]

    def build_from_plan(args: dict[str, Any]) -> dict[str, Any]:
        source, plan = _plan_fact(args["source"])
        ops, wall_order = plan_to_ops(plan)
        created: list[str] = []
        result: dict[str, Any] = {}
        lane = app.blender_lane()  # A68: the served Blender, by what it can do
        for start in range(0, len(ops), _BATCH_CHUNK):
            result = app.run_batch(lane, ops[start : start + _BATCH_CHUNK])
            created.extend(result.get("created", []))
        manifest = {
            "kind": "build_manifest",
            "frame": plan["frame"],
            "tier": "built_geometry",
            "walls": dict(zip(wall_order, created, strict=False)),
            "plan_frame": plan["frame"],
        }
        store.store_facts(source["hash"], *BUILD_EXTRACTOR, [manifest])
        return {
            "built_walls": len(wall_order),
            "built_objects": len(created),
            "checkpoint": result.get("checkpoint"),
            **{k: result[k] for k in ("epoch", "revision") if k in result},
        }

    def _register_if_blender(tool: Any) -> None:
        if blender:
            app.registry.register(tool)

    _register_if_blender(
        VirtualTool(
            name="bl_build_from_plan",
            description=(
                "Build the extracted floor plan in Blender through the "
                "normal batch machinery (checkpointed, diff-tracked): one "
                "rotated box per wall plus floor slabs, in the site frame. "
                "Records a build manifest for bl_check_against_plan."
            ),
            schema={
                "type": "object",
                "properties": {"source": {"type": "string"}},
                "required": ["source"],
            },
            handler=build_from_plan,
            tags=["blender", "plan", "build", "walls", "extract"],
            examples=[{"source": "a1b2c3d4"}],
        )
    )

    def check_against_plan(args: dict[str, Any]) -> dict[str, Any]:
        source, plan = _plan_fact(args["source"])
        manifests = store.facts(source["hash"], kind="build_manifest")
        if not manifests:
            raise TeeError(
                "no_build",
                "Nothing built yet for this source.",
                fix="Run bl_build_from_plan first.",
            )
        wall_map = manifests[-1]["walls"]
        lane = app.blender_lane()
        cache = app.cache(lane)
        app.warm(lane)

        # chain accuracy widens the tolerance honestly; an unregistered plan
        # frame means the plan was built directly in the site frame (identity)
        try:
            _, chain_accuracy, _ = registry.to_site(plan["frame"], [(0.0, 0.0)])
        except TeeError:
            chain_accuracy = 0.0

        tolerance = rss(
            TIER_TOLERANCE_M["drawing_geometry"],
            TIER_TOLERANCE_M["built_geometry"],
            chain_accuracy,
        )
        conflicts: list[dict[str, Any]] = []
        checked = 0
        for wall in plan["walls"]:
            entity_id = wall_map.get(wall["id"])
            entity = cache.get(entity_id) if entity_id else None
            if entity is None:
                conflicts.append(
                    {
                        "kind": "conflict",
                        "fact_a": f"plan:{wall['id']}",
                        "fact_b": None,
                        "delta_m": None,
                        "tolerance_m": tolerance,
                        "winner": "plan",
                        "disposition": "wall missing from the scene",
                    }
                )
                continue
            checked += 1
            dims = entity.summary.get("dimensions") or [0, 0, 0]
            loc = entity.summary.get("location") or [0, 0, 0]
            expect_len = wall_length(wall)
            mid_x, mid_y = wall_midpoint(wall)
            deltas = {
                "length": abs(dims[0] - expect_len),
                "thickness": abs(dims[1] - float(wall["thickness"])),
                "position": math.hypot(loc[0] - mid_x, loc[1] - mid_y),
            }
            for aspect, delta in deltas.items():
                if delta > tolerance:
                    conflicts.append(
                        {
                            "kind": "conflict",
                            "fact_a": f"plan:{wall['id']}:{aspect}",
                            "fact_b": f"scene:{entity_id}",
                            "delta_m": round(delta, 4),
                            "tolerance_m": round(tolerance, 4),
                            "winner": "plan",
                            "disposition": "written dimensions govern - fix the scene",
                        }
                    )
        if conflicts:
            store.store_facts(source["hash"], "conformance", "1", conflicts)
        return {
            "walls_checked": checked,
            "tolerance_m": round(tolerance, 4),
            "chain_accuracy_m": round(chain_accuracy, 4),
            "conflicts": conflicts,
            "conformant": not conflicts,
        }

    _register_if_blender(
        VirtualTool(
            name="bl_check_against_plan",
            description=(
                "Dimensional conformance: compare the built scene against "
                "the plan facts in the common frame. Tolerance is the RSS "
                "of both evidence tiers plus transform-chain accuracy; "
                "written dimensions govern. Over-tolerance deltas come back "
                "as conflict facts - this IS the conformance report."
            ),
            schema={
                "type": "object",
                "properties": {"source": {"type": "string"}},
                "required": ["source"],
            },
            handler=check_against_plan,
            tags=["blender", "plan", "conformance", "verify", "extract"],
        )
    )

    def export_plan_ifc(args: dict[str, Any]) -> dict[str, Any]:
        from tee.extract.ifc import export_ifc

        source, plan = _plan_fact(args["source"])
        out = store.derived_dir(source["hash"], "ifc") / "plan.ifc"
        return export_ifc(plan, out, project_name=source["name"])

    app.registry.register(
        VirtualTool(
            name="ex_export_ifc",
            description=(
                "Author an IFC4 file from the extracted plan (real IfcWall "
                "entities with storey elevations) for import via Bonsai/"
                "BlenderBIM or any BIM tool. Zero tokens - runs offline."
            ),
            schema={
                "type": "object",
                "properties": {"source": {"type": "string"}},
                "required": ["source"],
            },
            handler=export_plan_ifc,
            tags=["ifc", "bim", "export", "plan", "extract"],
        )
    )
