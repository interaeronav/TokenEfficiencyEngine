# 32 — Blender 5.2 physics surfaces headless (2026-08-22)

Verified against 5.2 docs, the release-branch C sources, and the tracker.
5.2 ships TWO stacks: legacy (Bullet rigid body, cloth/softbody + point
cache, Mantaflow) — the stable surface — and experimental Geometry-Nodes
physics (XPBD solver, Cloth/Hair Dynamics assets; Jolt investigated for
rigid bodies). Legacy = TEE's primary ops; GN = watch-lane.

## Rigid body (best story)

Sim advances ONLY on sequential `frame_set()` (ctime == last+1, from
rigidbody.cc); fixed substeps (substeps_per_frame × solver_iterations),
zero wall-clock dependence; cache range clamps stepping (extend
frame_end before long settles). Blender's own bake_to_keyframes is just
a frame_set loop reading `matrix_world` — the sanctioned readback. NO
velocities in RNA → settle = transform deltas between frames. No seed
anywhere: determinism = fixed stepping order, same machine + build;
manual recommends baking for exactness. Knobs to pin: substeps,
iterations, time_scale, fps, cache range, gravity.

## Cloth

`modifiers.new('CLOTH')`; `solver_result` (status + avg/max error/
iterations) = free compact health report. Exact 5.2 preset values
extracted from presets/cloth/*.py (cotton/denim/leather/rubber/silk —
embeddable as TEE enums, no Blender needed). Headless baking VERIFIED
at source: `ptcache.bake(bake=True)` exec path is synchronous;
`ptcache.bake_all` polls on scene only (cheapest route); per-cache bake
needs `temp_override(point_cache=...)`. Readback via evaluated_get →
reduce to AABB/max-sag/solver_result, never vertices.

## Point caches & checkpoints

5.0 removed LZO/LZMA → ZSTD always (old caches rebake). Baked MEMORY
caches persist inside the .blend → survive TEE snapshots; disk caches
live in `blendcache_<name>/` — renaming a snapshot ORPHANS them. GN
bakes default PACKED (in-.blend, checkpoint-free); disk bakes
enumerable via 5.2's `file_path_foreach(EXPAND_CACHES)`. Rule: bake
before checkpoint.

## Fluid (Mantaflow — unreplaced in 5.2)

`fluid.bake_all` exec is synchronous; needs the domain as ACTIVE object;
`cache_type` defaults 'REPLAY' — must set 'ALL'/'MODULAR' for scripted
bakes; always set absolute `cache_directory` (auto-reset warning
otherwise); fluids do NOT use the point-cache system. TBB-threaded →
bit-exact rebakes UNVERIFIED/doubtful; checkpoint the cache dir, never
re-derive. Cost: default res 32 = seconds-minutes; res 200 ≈ 2 h
(anecdotal) → gate behind cost warning, default res ≤ 64.

## GN simulation zones / XPBD (5.2 experimental)

Sim zones: pair_with_output API, same sequential frame discipline;
`simulation_nodes_cache_bake` exec synchronous (needs
use_simulation_cache); `..._calculate_to_frame` is INVOKE-ONLY (WM job)
— never use headless. XPBD solver outputs a residual-error bundle = a
natural compact health metric. Experimental: design may change; scale/
space issues live on devtalk. 5.2 NodesModifier input API break applies
(digest 36).

## Tracker landmines (headless)

#154889 GN sims not evaluated before saved frame in background renders
("bake, there is no way around it"); #139089 fluid bake crashes under
pip-bpy (drive full `blender --background`, never the bpy module);
#143960 multi-hair ptcache bake crash; #140049 GN disk bakes not
unloading (RAM growth); #158634 stale bake flags after reload (trust
NodesModifierBake data, not UI flags).

## Typed ops → sim_drop, sim_settle (early-out on delta convergence,
optional freeze), sim_cloth_drape (preset enum), sim_cloth_gn (gated),
sim_fluid (cost-warned), sim_bake_all (checkpoint prep). Reports:
resting poses, settled flag, AABB/max-displacement, solver_result/XPBD
residual, PointCache.info, wall-time. Never: per-frame data, vertices,
velocities/contact counts (not in RNA — don't promise).
