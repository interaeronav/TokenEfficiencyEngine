"""TEE Physical virtual tools: tier-2 modeling ops, material facts,
the physics lane, tier-0 checks, and structural plausibility."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool
from tee.physical import materials as materials_mod
from tee.physical import physics as physics_mod
from tee.physical import plaus as plaus_mod
from tee.physical import verify as verify_mod
from tee.physical.sketch import solve_sketch

_TIER2_OPS = (
    "wall_with_openings",
    "slab",
    "roof",
    "stairs",
    "opening_cut",
    "array_along",
    "profile_extrude",
    "param_set",
)

_DETERMINISM = physics_mod.DETERMINISM_NOTE


def register_physical_tools(app, project_root: Path | str) -> None:
    reg = app.registry
    default_adapter = next(iter(app.adapters), "fake")

    def _adapter(args: dict[str, Any]) -> str:
        return str(args.get("adapter") or default_adapter)

    def _blender_only(args: dict[str, Any]) -> str:
        name = _adapter(args)
        adapter = app.adapters.get(name)
        if adapter is None or not hasattr(adapter, "execute_python"):
            raise TeeError(
                "unsupported_adapter",
                f"This op compiles to Blender-side patterns; adapter '{name}' cannot run it.",
                fix="Use the blender adapter (UE Geometry Script targets "
                "arrive with the physical machine).",
            )
        return name

    # -- tier-2 modeling ---------------------------------------------------

    def _tier2(op_name: str):
        def handler(args: dict[str, Any]) -> dict[str, Any]:
            adapter = _blender_only(args)
            op: dict[str, Any] = {"op": op_name}
            for key in ("id", "name"):
                if args.get(key):
                    op[key] = args[key]
            op["props"] = args.get("props") or {}
            return app.run_batch(adapter, [op], label=op_name)

        return handler

    def sketch_tool(args):
        out = solve_sketch(args["sketch"])
        order = args.get("polygon")
        if order:
            from tee.physical.sketch import polygon_from

            out["polygon"] = polygon_from(out["points"], [str(p) for p in order])
        return out

    # -- materials ---------------------------------------------------------

    def mat_assign(args):
        adapter = _adapter(args)
        entity_id = str(args["id"])
        volume = None
        app.warm(adapter)
        cache = app.caches.get(adapter)
        entity = cache.get(entity_id) if cache else None
        if entity is not None:
            dims = entity.summary.get("dimensions") or entity.summary.get("dims_m")
            if dims and all(d > 0 for d in dims[:3]):
                volume = dims[0] * dims[1] * dims[2]
        ops, fact = materials_mod.assign_ops(entity_id, str(args["query"]), volume_m3=volume)
        batch = app.run_batch(adapter, ops, label=f"mat:{fact['material']}")
        out = {
            "fact": fact,
            **{k: batch[k] for k in ("checkpoint", "modified", "epoch", "revision") if k in batch},
        }
        if volume is not None:
            out["mass_note"] = "mass = AABB volume x density (box approximation)"
        return out

    def mat_facts(args):
        return materials_mod.facts(str(args["query"]))

    # -- physics lane ------------------------------------------------------

    def _run_sim(args, program: str, label: str) -> dict[str, Any]:
        adapter_name = _blender_only(args)
        adapter = app.adapter(adapter_name)
        cache = app.cache(adapter_name)
        checkpoint = app.checkpoints.create(adapter, f"auto:{label}", cache.revision)
        out = physics_mod.run_program(app, adapter_name, program)
        cache.resync(adapter)  # sim moved things outside the batch machinery
        return {"checkpoint": checkpoint.id, **out, **cache.stamp()}

    def sim_settle(args):
        program = physics_mod.settle_program(
            args.get("ids"),
            args.get("passive_ids"),
            adopt=bool(args.get("adopt")),
            params=args.get("params"),
        )
        return _run_sim(args, program, "settle")

    def sim_cloth(args):
        program = physics_mod.cloth_program(
            str(args["id"]),
            args.get("collide_ids"),
            preset=str(args.get("preset", "cotton")),
            seconds=float(args.get("seconds", 3.0)),
            apply_result=bool(args.get("apply")),
        )
        return _run_sim(args, program, "cloth")

    def sim_bake_all(args):
        return _run_sim(args, physics_mod.BAKE_ALL_PROGRAM, "bake")

    def sim_fluid(args):
        if not args.get("confirm_cost"):
            raise TeeError(
                "cost_confirmation_required",
                "Fluid bakes are minutes-to-hours of compute and gigabytes "
                "of cache (res<=64 capped here).",
                fix="Re-call with confirm_cost=true; the bake runs as an "
                "async job - poll with tee_job.",
            )
        adapter_name = _blender_only(args)
        cache_dir = str(
            Path(project_root).resolve() / ".tee" / "fluid_cache"
        )  # ABSOLUTE path: relative cache dirs fail silently (tracker landmine)
        program = physics_mod.fluid_program(
            [float(v) for v in args.get("domain_size", [2, 2, 2])],
            [float(v) for v in args.get("inflow", [0, 0, 1.5])],
            resolution=int(args.get("resolution", 48)),
            frames=int(args.get("frames", 48)),
            cache_dir=cache_dir,
            fluid_type=str(args.get("fluid_type", "liquid")),
        )
        job = app.jobs.submit(
            "sim_fluid",
            lambda: physics_mod.run_program(app, adapter_name, program, timeout=3600),
        )
        return {
            "job": job,
            "note": "poll with tee_job; bake is synchronous "
            "in Blender - the bridge is busy until it finishes",
        }

    def sim_proxy(args):
        from tee.physical.proxy import coacd_proxy

        return coacd_proxy(
            str(args["path"]),
            Path(project_root) / ".tee" / "proxies",
            threshold=float(args.get("threshold", 0.05)),
            max_hulls=int(args.get("max_hulls", 32)),
            seed=int(args.get("seed", 0)),
        )

    def plaus_ids(args):
        try:
            import ifcopenshell
            from ifctester import ids as ids_mod
            from ifctester.reporter import Json as JsonReporter
        except ImportError as exc:
            raise TeeError(
                "physical_extra_missing",
                "The IDS data-completeness tier needs ifctester + ifcopenshell.",
                fix="uv sync --extra extract --extra physical",
            ) from exc
        ifc_path = Path(str(args["ifc"]))
        ids_path = Path(str(args["ids"]))
        if not ifc_path.exists() or not ids_path.exists():
            raise TeeError(
                "no_such_file",
                f"Missing {'IFC' if not ifc_path.exists() else 'IDS'} file.",
                fix="Export IFC via the Phase 7 handoff (bl_export_ifc); the "
                "IDS spec is a buildingSMART IDS 1.0 XML.",
            )
        spec = ids_mod.open(str(ids_path))
        model = ifcopenshell.open(str(ifc_path))
        spec.validate(model)
        report = JsonReporter(spec)
        report.report()
        results = report.to_string()
        import json as json_mod

        parsed = json_mod.loads(results)
        specs = parsed.get("specifications", [])
        failed = [
            {
                "specification": s.get("name"),
                "failed": s.get("total_failed", 0),
                "of": s.get("total", 0),
            }
            for s in specs
            if s.get("total_failed")
        ]
        return {
            "specifications": len(specs),
            "conflicts": failed,
            "summary": (
                f"{len(failed)} specification(s) with failures"
                if failed
                else f"no data-completeness conflicts ({len(specs)} specifications evaluated)"
            ),
        }

    # -- verification ladder ----------------------------------------------

    def phys_tier0(args):
        return verify_mod.tier0(app, _adapter(args))

    def sim_ready(args):
        adapter = _adapter(args)
        app.warm(adapter)
        cache = app.caches.get(adapter)
        entity = cache.get(str(args["id"])) if cache else None
        if entity is None:
            raise TeeError(
                "unknown_entity",
                f"No entity '{args['id']}' in the {adapter} cache.",
                fix="List ids with tee_scene_summary.",
            )
        return verify_mod.sim_readiness(entity.summary)

    # -- plausibility ------------------------------------------------------

    def plaus_check(args):
        return plaus_mod.check({"elements": args["elements"], "region": args.get("region", "US")})

    tier2_descs = {
        "wall_with_openings": (
            "Build a wall with door/window openings as ONE watertight mesh "
            "(tessellate+solidify - 0 non-manifold edges by construction). "
            "props: start [x,y], end [x,y], height, thickness, level_z, "
            "openings [{offset, width, sill, head}]."
        ),
        "slab": (
            "Watertight floor/ceiling slab from a polygon with optional "
            "holes. props: polygon [[x,y]…], holes, thickness, top_z."
        ),
        "roof": (
            "Closed roof massing: kind gable|shed|flat (hip pending a "
            "straight-skeleton choice), footprint [x0,y0,x1,y1], pitch_deg, "
            "base_z, ridge_axis."
        ),
        "stairs": (
            "Straight solid stair run sized from rise_total (riser <= "
            "riser_max, default 196 mm IRC); records riser/tread for "
            "plaus_check. props: rise_total, tread, width, location."
        ),
        "opening_cut": (
            "Retrofit an opening into an existing wall via a live boolean "
            "(MANIFOLD solver default, EXACT fallback, 'FAST' guarded; "
            "over-penetrating manifold cutter). apply=true makes it "
            "destructive (checkpointed). props: center, size, solver, apply."
        ),
        "array_along": (
            "N linked duplicates of an entity stepped along a vector. "
            "props: count, step [dx,dy,dz]."
        ),
        "profile_extrude": (
            "Extrude a closed 2D profile into a watertight solid. props: "
            "profile [[x,y]…], depth, location, rotation_euler."
        ),
        "param_set": (
            "Set geometry-node inputs by SOCKET IDENTIFIER through the "
            "single version-shimmed chokepoint (5.2 RNA API; pre-5.2 "
            "fallback). The token-efficiency payoff: one group, "
            "three-scalar diffs. props: modifier?, values {Socket_N: v}."
        ),
    }

    tools = [
        VirtualTool(
            "sketch_solve",
            "Server-side 2D constraint solving (py-slvs/SolveSpace) - close "
            "a dimensioned plan BEFORE extrusion, no DCC involved. Over-"
            "constrained names the exact conflicting constraints; "
            "polygon=[point ids] returns the ordered outline for wall/slab "
            "ops.",
            {
                "type": "object",
                "properties": {"sketch": {"type": "object"}, "polygon": {"type": "array"}},
                "required": ["sketch"],
            },
            sketch_tool,
            tags=["physical", "sketch", "constraints", "cad", "solve"],
        ),
        VirtualTool(
            "mat_assign",
            "Assign a material across ALL tiers at once: render nodes "
            "(measured CC0 values), rigid-body params (Bullet gets sqrt of "
            "the pair friction - it multiplies), and the engineering fact "
            "for plaus_check; echoes mass = volume x density. Every value "
            "carries source + honesty label.",
            {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "query": {"type": "string"},
                    "adapter": {"type": "string"},
                },
                "required": ["id", "query"],
            },
            mat_assign,
            tags=["physical", "material", "assign", "density", "engineering"],
        ),
        VirtualTool(
            "mat_facts",
            "Three-tier material facts (render/physics/engineering) for one "
            "material, honesty-labeled per value with sources.",
            {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            mat_facts,
            tags=["physical", "material", "facts", "properties"],
        ),
        VirtualTool(
            "sim_settle",
            "Rigid-body settle: sequential frame stepping, quiescence "
            "early-out (1 cm / 0.1 rad windows), compact report (settled, "
            "moved deltas, max displacement); adopt=true keeps the settled "
            f"poses. Auto-checkpointed. Determinism: {_DETERMINISM}.",
            {
                "type": "object",
                "properties": {
                    "ids": {"type": "array"},
                    "passive_ids": {"type": "array"},
                    "adopt": {"type": "boolean"},
                    "params": {"type": "object"},
                    "adapter": {"type": "string"},
                },
            },
            sim_settle,
            tags=["physical", "physics", "settle", "drop", "rigid-body"],
        ),
        VirtualTool(
            "sim_cloth_drape",
            "Cloth drape (visual aid - no pass/fail metric): preset "
            "cotton|denim|leather|silk|rubber, collision targets, apply=true "
            "bakes the drape into the mesh. Auto-checkpointed.",
            {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "collide_ids": {"type": "array"},
                    "preset": {"type": "string"},
                    "seconds": {"type": "number"},
                    "apply": {"type": "boolean"},
                    "adapter": {"type": "string"},
                },
                "required": ["id"],
            },
            sim_cloth,
            tags=["physical", "physics", "cloth", "drape"],
        ),
        VirtualTool(
            "sim_bake_all",
            "Bake every point cache (checkpoint prep: memory caches persist "
            "inside .blend snapshots - bake, then checkpoint).",
            {"type": "object", "properties": {"adapter": {"type": "string"}}},
            sim_bake_all,
            tags=["physical", "physics", "bake", "cache", "checkpoint"],
        ),
        VirtualTool(
            "sim_fluid",
            "Mantaflow fluid bake - COST-GATED (confirm_cost=true required): "
            "res capped at 64, ALL cache mode, absolute cache directory; "
            "runs as an async job (poll tee_job). Fluids are approximate - "
            "never cross-run deterministic.",
            {
                "type": "object",
                "properties": {
                    "confirm_cost": {"type": "boolean"},
                    "domain_size": {"type": "array"},
                    "inflow": {"type": "array"},
                    "resolution": {"type": "integer"},
                    "frames": {"type": "integer"},
                    "fluid_type": {"type": "string"},
                    "adapter": {"type": "string"},
                },
            },
            sim_fluid,
            tags=["physical", "physics", "fluid", "mantaflow", "bake"],
        ),
        VirtualTool(
            "sim_proxy",
            "CoACD convex-decomposition collision proxies for a concave "
            "mesh, cached per source-file hash under .tee/proxies/. Returns "
            "hull count, triangle budget and the proxy GLB path; cache_hit "
            "says whether it computed. Seeded - same file + params, same "
            "hulls on this build.",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "threshold": {"type": "number"},
                    "max_hulls": {"type": "integer"},
                    "seed": {"type": "integer"},
                },
                "required": ["path"],
            },
            sim_proxy,
            tags=["physical", "physics", "collision", "proxy", "coacd", "settle"],
        ),
        VirtualTool(
            "plaus_ids",
            "Data-completeness tier: run a buildingSMART IDS 1.0 spec "
            "against an exported IFC via ifctester; conflicts in the same "
            "findings shape as plaus_check.",
            {
                "type": "object",
                "properties": {"ifc": {"type": "string"}, "ids": {"type": "string"}},
                "required": ["ifc", "ids"],
            },
            plaus_ids,
            tags=["physical", "ids", "ifc", "completeness", "buildingsmart"],
        ),
        VirtualTool(
            "phys_tier0",
            "Tier-0 static physics facts (ms, no sim): floating, "
            "penetrating, unsupported_com - CoM projection inside the "
            "support polygon with margin, cumulative for stacks (the "
            "analytic ShapeStacks criterion). Honest wording: rest-state "
            "facts, never 'structurally sound'.",
            {"type": "object", "properties": {"adapter": {"type": "string"}}},
            phys_tier0,
            tags=["physical", "verify", "stability", "support", "tier0"],
        ),
        VirtualTool(
            "sim_ready",
            "SimReady-style static readiness gate for one entity: extents, "
            "sane scale, physical material, collision proxy - findings with "
            "callable fixes (sims are gated statically, never by running).",
            {
                "type": "object",
                "properties": {"id": {"type": "string"}, "adapter": {"type": "string"}},
                "required": ["id"],
            },
            sim_ready,
            tags=["physical", "verify", "sim", "readiness"],
        ),
        VirtualTool(
            "plaus_check",
            "Structural plausibility findings against cited prescriptive "
            "tables (CODE/STD/HEUR/CONV severity; CODE never relaxable): "
            "spans, headers, masonry, footings, roof pitch per covering, "
            "stairs, ceilings, fall protection, the IRC R301.1 load-path "
            "graph. Findings only - never member sizing, never a 'passes' "
            "state. NOT an engineering review; conditions outside the "
            "prescriptive envelope require a licensed engineer.\n"
            "region selects the legal regime AND how much force a finding "
            "may claim: US (IRC, default) | ZA (SANS 10400 under the NBR "
            "Act, CODE force) | NA-local-authority | NA-settlement | "
            "NA-communal (Namibia: SANS is not law, so CODE is capped to "
            "STD) | NA-unresolved. Namibia's three regimes differ "
            "completely, so bare 'NA' resolves to NA-unresolved and caps "
            "findings until you establish which applies.",
            {
                "type": "object",
                "properties": {
                    "elements": {"type": "array"},
                    "region": {
                        "type": "string",
                        "description": "US (default) | ZA | NA-local-authority "
                        "| NA-settlement | NA-communal | NA-unresolved",
                    },
                },
                "required": ["elements"],
            },
            plaus_check,
            tags=["physical", "plausibility", "structure", "code", "span"],
        ),
    ]
    for name in _TIER2_OPS:
        tools.append(
            VirtualTool(
                name,
                tier2_descs[name],
                {
                    "type": "object",
                    "properties": {
                        "props": {"type": "object"},
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "adapter": {"type": "string"},
                    },
                },
                _tier2(name),
                tags=["physical", "modeling", "tier2", name.replace("_", " ")],
            )
        )
    for tool in tools:
        reg.register(tool)
