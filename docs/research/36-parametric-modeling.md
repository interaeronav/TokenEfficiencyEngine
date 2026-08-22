# 36 — Parametric/precision modeling surfaces (2026-08-22)

Strongest evidence class of the pass: [LOCAL] items were executed
against this container's Blender 5.2.0 headless (re-runnable scripts in
the session scratchpad).

## The 5.2 API break (shim-table entry) [LOCAL]

`NodesModifier` no longer supports ID-properties — `md["Socket_0"]`
raises TypeError. New API: `md.properties.inputs.<identifier>.value`
(typed access via getattr; subscript falls back to a raw
IDPropertyGroup; `.type = 'ATTRIBUTE'` + `.attribute_name` for
attribute inputs). Address sockets ONLY by identifier (Socket_N),
never by name.

## Geometry nodes as the data-driven API [LOCAL]

node_groups.new → interface.new_socket (4.0+ interface API) → nodes/
links — stable and fully headless; writes take effect immediately.
5.x arc: 5.0 Bundles + Closures; 5.1 bundle paths, node-tool operator
registration; 5.2 Lists as a core type, Geometry Bundles, experimental
XPBD node physics, GN-on-Empties, Mesh Bevel node, `gpu.init()` for
background. Import nodes (OBJ/PLY/CSV/STL/VDB) since 4.5; bake nodes
4.1+ with pack/unpack (checkpoints stay single-file). Quantified
payoff: one parameterized group built once server-side, then 3-scalar
param diffs per wall — strictly cheaper than re-emitting mesh code.

## Booleans & BMesh [LOCAL]

Solvers: FLOAT / EXACT / **MANIFOLD** — legacy 'FAST' identifier is
GONE (codegen guard). MANIFOLD (robust, fast) requires manifold
operands → cutters over-penetrate and are manifold by construction;
EXACT is the fallback for coplanar/self-intersecting. Wall − door −
window verified headless with 0 non-manifold edges. bmesh.ops has NO
boolean; the boolean-free wall pattern —
`mathutils.geometry.tessellate_polygon` (respects holes) → faces →
recalc_normals → `bmesh.ops.solidify` — verified watertight. Avoid
face_split_edgenet in codegen (fragile).

## Precision: solve server-side, not in the DCC [LOCAL]

**py-slvs (SolveSpace wheel) imports clean in a plain venv** — full
constraint vocabulary (distance/angle/parallel/equal…) → constraint-
close dimensioned 2D plans BEFORE extrusion, zero Blender involvement.
CAD Sketcher is GPL-3 and UI-centric (headless unlikely).

## Generators & licenses

**Infinigen BSD-3 = minable and embeddable** (127 door/window/staircase
parameters — the best source for op schemas); Buildify free but
no-redistribution (concepts only); BlenderKit RF forbids extraction
(CC0-filter only); archipack GPL (its wall-segment/opening parameter
model is the concept source).

## Non-destructive policy

Keep modifiers live while iterating (param diffs = cheap checkpoints);
`apply` is a checkpoint boundary; glTF `export_apply` exports applied
WITHOUT mutating the scene.

## UE portability

PCG 5.8: drive parameters from Python (PCGGraphParametersHelpers);
graph AUTHORING is not a Python surface → ship pre-built graphs and
parameterize (mirrors the GN pattern). **Geometry Script is officially
Python-scriptable** (UDynamicMesh: primitives, booleans, extrude) —
the UE compile target for the same typed ops.

## Tier-2 op vocabulary (A21)

wall_with_openings (live: GN group + MANIFOLD cutters; baked:
tessellate+solidify) · slab (holes) · roof (gable/hip/shed/flat;
straight-skeleton lib choice open) · stairs · opening_cut (retrofit) ·
array_along · **param_set (the token-efficiency payoff — same schema
both engines)** · profile_extrude · sketch_solve (server-side py-slvs,
no DCC). Live variants default on; `apply` explicit and checkpointed.
