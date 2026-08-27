---
id: envasset.hardsurface_fusion
title: Hard surface and the Fusion → Blender → Unreal workflow
domain: 25_environmental_asset_creation
tags: [fusion, cad, step, nurbs, tessellation, retopology, uv-unwrapping, hard-surface, units, gate, steel, worked-example, usd, obj]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
applies_to: "Autodesk Fusion (May 2026 release), Blender 5.2 LTS, Unreal Engine 5.8."
unit_system: SI
sources:
  - {title: "Autodesk Fusion overview", url: "https://www.autodesk.com/products/fusion-360/overview", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "FusionAPIReference", url: "https://github.com/AutodeskFusion360/FusionAPIReference", publisher: "Autodesk (GitHub)", accessed: 2026-08-25}
  - {title: "Nanite Virtualized Geometry in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Blender Manual", url: "https://docs.blender.org/manual/en/latest/", publisher: "Blender Foundation", accessed: 2026-08-25}
related: [envasset.overview, envasset.pipeline, fusion.interoperability, fusion.api, fusion.modelling_parameters, blender.import_export, ue.project_setup]
---

# Hard surface and the Fusion → Blender → Unreal workflow

**Summary.** Fusion's role in this pipeline is narrow and important: it produces the geometry of things that will actually be **manufactured** — a steel entrance gate, burglar bars, a water-tank stand, a pergola bracket, a balustrade — at dimensions a fabricator can build from. That same geometry then has to survive the trip into a renderer, and CAD geometry is hostile to rendering: it arrives as dense, badly distributed triangles derived from NURBS, with no useful UVs, no vertex normal control, and a tiny-fillet problem that wrecks both tessellation and normal baking. This file covers what Fusion is genuinely better at, the STEP-to-polygon pipeline with real settings, unit handling across all three applications, and a worked example that carries a steel gate from Fusion through Blender into an Unreal scene.

## Key facts

| Item | Value | Source |
|---|---|---|
| Fusion internal API units | **centimetres** for length, **radians** for angle | domain 15 |
| Fusion default UI unit for a metric design | millimetres | domain 15 |
| Blender unit | **1 Blender unit = 1 metre** with Metric, Unit Scale 1.0 | domain 14 |
| Unreal unit | **1 uu = 1 cm** | domain 13 |
| Fusion export formats out | `.f3d`/`.f3z`, **STEP**, IGES, SAT, SMT, DWG, DXF, STL, 3MF, OBJ, **USD** | domain 15 |
| Fusion does **not** export | FBX, glTF, native Inventor/SolidWorks | domain 15 |
| Best Fusion → Blender routes | **OBJ** (geometry + material assignment) or **USD** (adds hierarchy and transforms) | domain 15 |
| STEP into Blender | Needs an add-on (STEPper) or a FreeCAD conversion — lets you re-tessellate at your chosen quality | domain 15 |
| Nanite blend modes | Opaque and Masked only — Nanite is ideal for dense CAD-derived meshes | Epic |

> ⚠️ **The Fusion model is the dimensional master. Nothing downstream edits geometry.** If a gate rail changes from 40 × 40 × 2 mm to 50 × 50 × 2 mm, it changes in Fusion and re-exports. Any geometry edit made in Blender is lost on the next export, and worse, silently desynchronises the render from the fabrication drawing.

---

## 1. What Fusion is genuinely better at

| Task | Fusion | Blender |
|---|---|---|
| A gate that must fit a 3 200 mm opening with 15 mm clearance each side | **Yes** — parametric, dimensioned, drawing-able | Possible but undisciplined |
| A bracket with a bolt pattern matching a purchased fitting | **Yes** | No |
| Sheet-metal parts with correct bend allowances and a flat pattern | **Yes** — Sheet Metal workspace, DXF flat pattern | No |
| A CNC-cut joinery panel | **Yes** — Manufacture workspace, nested DXF, G-code | No |
| Anything that needs a shop drawing with dimensions and a parts list | **Yes** — Drawing workspace | No |
| A stress check on a cantilevered pergola beam | **Yes** — Simulation workspace, static stress | No |
| An organic rock, a tree, a weathered wall | No | **Yes** |
| Retopology, UVs, baking, LODs | No | **Yes** |
| Anything needing artistic proportion iteration | Painful | **Yes** |

**The rule of thumb:** if the object will be cut, welded, bolted, bent or machined, model it in Fusion. If it will only be looked at, model it in Blender. If it is both — a gate that must be built *and* rendered — Fusion first, always.

**Objects on this project that belong in Fusion:** entrance gate and its frame, pedestrian gate, burglar bars, security-gate lattice, gate hardware brackets, palisade fixing brackets, balustrade and handrail, pergola/shade-structure connection plates, water-tank stand, gutter brackets and downpipe shoes, solar-panel mounting frame, borehole headworks cover, braai/grill ironwork, and any fitted joinery going to a CNC.

---

## 2. The parametric-to-polygon pipeline

### 2.1 Choosing the export route

| Route | Fidelity | Effort | Use when |
|---|---|---|---|
| **Fusion → OBJ → Blender** | Fixed tessellation baked at export | Lowest | Simple parts, prototyping, background props |
| **Fusion → USD → Blender / Unreal** | Fixed tessellation, but carries hierarchy, transforms and material assignments | Low | Assemblies where component structure matters |
| **Fusion → STEP → Blender (STEPper add-on)** | Exact B-rep re-tessellated at *your* chosen quality in Blender | Medium | **Hero assets.** The gate. Anything the camera gets close to |
| **Fusion → STEP → FreeCAD → mesh → Blender** | Same, free, more steps | Medium | If you will not buy a STEP importer |
| **Fusion → STL** | Triangles only, no UVs, no groups | Lowest | Never, for rendering. STL is for printing |

**Recommendation for this project:** STEP for hero assets, USD for assemblies, OBJ for everything else.

### 2.2 Mesh export settings — refinement and tessellation control

Fusion's mesh export (STL/OBJ/3MF dialog) offers a Refinement preset (Low / Medium / High) and a Custom mode exposing:

- **Surface Deviation** — the maximum distance between the mesh and the true surface. This is the parameter that matters most.
- **Normal Deviation** — the maximum angle between adjacent facet normals.
- **Maximum Edge Length**
- **Aspect Ratio**

**Setting Surface Deviation properly.** It should be smaller than the smallest feature you want to see, and comfortably below one screen pixel at the closest camera distance. A practical rule:

```
surface_deviation ≈ (closest_view_distance_mm × 0.0005)

Camera 1 000 mm from a gate  →  0.5 mm       (Low is far too coarse)
Camera   300 mm from a latch →  0.15 mm
Camera 5 000 mm (background) →  2.5 mm
```

Normal Deviation of **10°** gives smooth-looking cylinders (36 sides on a full circle); **5°** gives 72 sides and is what a hero asset wants.

**The consequence to accept:** a fine tessellation of a modest gate can produce 500 k – 3 M triangles. Under Nanite that is fine. Without Nanite it is not, and you retopologise (§2.4).

### 2.3 Dealing with triangulated NURBS output

CAD tessellation has three characteristic pathologies:

1. **Long thin triangles** radiating from surface parameter poles, especially on fillets and revolved features. They shade badly and bake badly.
2. **Non-uniform density** — a flat 2 m panel becomes two triangles, a 3 mm fillet becomes two thousand.
3. **Split vertices at surface boundaries** — every B-rep face becomes a separate mesh island with duplicated vertices along the shared edge, producing visible shading seams.

Fixes in Blender, in order:

```
1. Import.
2. Select All → Mesh → Merge → By Distance, threshold 0.0001 m (0.1 mm)
      → welds the split vertices at face boundaries. Do this FIRST.
3. Mesh → Normals → Recalculate Outside (Shift+N).
4. Add a Weighted Normal modifier (Keep Sharp on) after marking sharp edges.
      → fixes the shading on the long thin fillet triangles without changing geometry.
5. Shade Auto Smooth (Blender 4.1+ this is an operator adding a
      "Smooth by Angle" modifier) with an angle of 30-40 degrees.
6. Optional: Mesh → Clean Up → Decimate (Planar mode, angle 1-5 degrees)
      → collapses the over-tessellated flats without touching curved regions.
      Planar decimation is the right tool for CAD; Collapse is not.
```

**Step 2 is the one people skip and it is the one that matters.** Un-merged boundary vertices produce black seams along every edge of a smooth-shaded CAD part, and no amount of normal editing fixes it.

### 2.4 Retopology — when it is needed

With Nanite, usually never. Retopologise when:
- The asset will be **animated or deformed** (a swinging gate leaf is rigid — it does not need this; a chain does).
- The asset needs **clean UVs for a hand-painted or Substance-generated material**.
- The target is not Unreal (a glTF web deliverable, a mobile viewer).
- The mesh will receive a **baked normal map** from a high-poly — you need a low-poly cage.

For hard surface, retopology is manual or semi-manual: `Poly Build` tool, `Snap → Face Project` with `Project Individual Elements`, and the `Shrinkwrap` modifier. QuadriFlow and Voxel Remesh destroy hard edges and are the wrong tool.

**Realistic targets for a steel gate:**

| Version | Triangles | Purpose |
|---|---|---|
| Fusion export at 0.15 mm deviation | 1.5–3 M | Nanite source; normal-bake source |
| Manual low-poly | 8 000 – 25 000 | Non-Nanite LOD0, glTF deliverable |
| LOD1 / LOD2 | 4 000 / 1 500 | Distance |

### 2.5 UV unwrapping CAD-derived meshes

CAD meshes have no UVs. Options:

1. **Smart UV Project** (Angle Limit 66°, Island Margin 0.02, `Correct Aspect` on). Fast, produces many islands, fine for a metal object with a uniform material and no readable texture direction. **This is the right answer for most steelwork.**
2. **Manual seams + Unwrap (Angle Based)** for anything with a directional material (brushed metal, a wood infill panel) or with decals/labels.
3. **UVPackmaster or Blender's own Pack Islands (`Average Islands Scale` first)** to get consistent texel density.
4. **Trim sheets** (`05 §5`) — for a gate made of standard sections, UV every rail and stile onto the same strip of a trim texture. This is by far the most efficient approach and the one a games artist would use.
5. **Triplanar / world-aligned projection** in the material — no UVs at all. Excellent for uniform painted or galvanised steel, and it means a geometry change does not invalidate the UVs. In Unreal use `WorldAlignedTexture`; in Blender, a `Texture Coordinate → Object` into a `Box` projection on the Image Texture node with Blend ~0.3.

**Recommendation for the gate: triplanar for the base metal, plus a second UV channel with Smart UV Project for the baked AO/curvature masks that drive weathering.**

**Lightmap UVs**: only needed if you bake lighting. Under Lumen you do not. If you do, generate a second UV channel with `Smart UV Project`, margin ≥ 0.05, and let Unreal's `Generate Lightmap UVs` handle it with a min lightmap resolution of 64 for a gate.

### 2.6 Shading, hard and soft edges

CAD parts are made of planar and cylindrical faces meeting at real edges. The shading rules:

- Mark **every B-rep edge that is a real physical edge** as sharp. After the merge-by-distance step, use `Edge → Edge Split`-free approach: `Select → Select Sharp Edges` at 30°, then `Edge → Mark Sharp`.
- Apply **Weighted Normal** (Keep Sharp) so large faces dominate the vertex normal — this is what stops fillets from shading darker than the flats.
- **Never** rely on flat shading everywhere. It doubles the vertex count on export and looks faceted on cylinders.
- On export to FBX/glTF, ensure **Tangent Space** is exported and that smoothing is set to **Face** or **Edge** (FBX) so Unreal reconstructs the same normals.

### 2.7 The tiny-fillet problem

Fusion parts are full of 0.5–2 mm fillets and chamfers, because real fabricated steel has them and because the CAD model needs them for manufacture. In rendering they cause:

- **Explosive tessellation** — a 1 mm fillet at 0.15 mm surface deviation gets many segments; multiply by every edge.
- **Baking failure** — the low-poly cage cannot follow a 1 mm fillet without self-intersecting, so the normal bake produces artefacts along every edge.
- **Aliasing** — a 1 mm feature at 20 m is far below a pixel and produces specular sparkle.

**The strategies:**

1. **Keep them and use Nanite.** The simplest answer and usually the right one for a hero asset. Nanite's cluster LOD handles the density; specular aliasing is handled by roughness-from-normal compositing (`01 §4.3`).
2. **Make a render variant in Fusion.** Fusion is parametric: suppress the small fillet features in a separate configuration/version, export that for rendering, and keep the filleted version for fabrication. This is clean, reversible and keeps both models correct.
3. **Bevel in Blender instead.** Delete the CAD fillets (hard) or export unfilleted and add a **Bevel modifier** (Angle mode, 0.8 mm, 2 segments, Harden Normals on). You get a controllable, evenly distributed bevel with far fewer triangles.
4. **Bevel-in-shader.** Blender's `Bevel` shader node perturbs the normal as if a bevel existed, with zero geometry. Cycles only, and it does not affect the silhouette — but for a 1 mm fillet on a gate seen from 2 m, the silhouette contribution is nil and the shading contribution is everything.
5. **Bake a normal map with a beveled high-poly and a sharp low-poly.** The classic games approach. Highest quality, most work.

> The single most valuable habit: **model the small fillets as a suppressible feature group in Fusion from the start.** A `Fillets_Small` folder in the timeline that can be suppressed turns a two-hour cleanup into a two-click export.

---

## 3. Scale and unit handling across all three applications

This is where the most time is silently lost.

| Application | Native unit | Notes |
|---|---|---|
| **Fusion** | UI: mm (metric design). **API: centimetres, radians** | `Design.modifyParameters` and all API geometry are in cm. A script that assumes mm will be 10× wrong |
| **Blender** | 1 BU = 1 m (Metric, Unit Scale 1.0) | Scene Properties → Units. Set Length to Metres and *leave Unit Scale at 1.0* |
| **Unreal** | 1 uu = 1 cm | Non-negotiable |

**The conversion chain that works:**

```
Fusion  (mm in UI)
   │  export STEP / OBJ / USD  — set export units EXPLICITLY to millimetres
   ▼
Blender (import with Scale 0.001 so 1 mm → 0.001 m)
   │  verify: a 3 200 mm gate should measure 3.2 m with the ruler (Shift+Space, M)
   │  Apply scale (Ctrl+A → Scale) before export
   ▼
FBX export: Scale 1.0, Apply Scalings = "FBX All", Apply Unit = ON, Forward -Z, Up +Y
   │
   ▼
Unreal  (import FBX with Import Uniform Scale 100.0  →  1 m becomes 100 uu)
   │  verify: gate bounds should read 320 uu wide
```

**Alternative, fewer failure modes:** use **USD** end to end. USD carries `metersPerUnit` metadata, and Blender's and Unreal's USD importers honour it. Fusion exports USD (`USDExportOptions`). This is the modern route and worth adopting — see `08 §USD`.

**Verification is mandatory, every time.** Put a **1 000 mm calibration cube** in the Fusion design, export it with everything, and check it reads 1 m in Blender and 100 uu in Unreal. It costs nothing and catches every scale error immediately.

---

## 4. Worked example — a steel entrance gate

The brief: a 3 200 mm clear-opening double-leaf swing gate for a homestead boundary, galvanised steel frame with vertical infill bars, to be fabricated locally in Ohangwena.

### 4.1 Fusion — design it to be built

```
User parameters (Modify → Change Parameters):
  OpeningWidth   = 3200 mm
  LeafGap        = 15 mm      // clearance between leaves
  HingeGap       = 12 mm      // clearance at each pillar
  LeafWidth      = (OpeningWidth - LeafGap - 2*HingeGap) / 2   = 1580.5 mm
  GateHeight     = 1800 mm
  FrameSection   = 50 mm      // 50 x 50 x 2 SHS
  FrameWall      = 2 mm
  BarSection     = 16 mm      // 16 mm solid square bar
  BarSpacing     = 110 mm     // < 100 mm if child safety governs - check codes domain
  BarCount       = floor((LeafWidth - 2*FrameSection) / BarSpacing)
```

1. **Sketch** the leaf outline on the XY plane, fully constrained, driven by the parameters.
2. **Create the frame** with the *Pipe* or *Sweep* tool along the outline using a 50 × 50 SHS profile, or model one member and use a rectangular pattern — but the parametric route is a sketch + `Tube`/`Sweep`.
3. **Pattern the infill bars** with `Create → Pattern → Rectangular Pattern`, quantity driven by `BarCount`, spacing by `BarSpacing`.
4. **Add the real hardware**: hinge lugs (welded plate + pin), a drop bolt socket, a latch plate. Model these with actual bolt hole sizes.
5. **Fillet weld representation**: a 4 mm fillet on the internal corners of every joint. Group these as `Fillets_Weld` in the timeline so they can be suppressed.
6. **Small edge breaks**: 1 mm chamfer on all exposed edges, grouped as `Fillets_Small` — suppressible.
7. **Assemble** the two leaves and the pillars as components with revolute **joints** at the hinges, so you can swing them and check clearances.
8. **Drawing**: produce a dimensioned shop drawing and a parts list. This is the deliverable the fabricator works from.
9. **Archive**: `.f3z`, STEP AP214, PDF drawing, CSV parts list (see domain `15` file `10`).

### 4.2 Export

For a hero gate seen from ~1.5 m in the render:

```
Suppress "Fillets_Small"        (keep the weld fillets - they are visible)
File → Export → STEP (.step)    for the archive and for re-tessellation
File → Export → Mesh (OBJ)      Refinement: Custom
                                Surface Deviation  0.20 mm
                                Normal Deviation   6°
                                Max Edge Length    50 mm
                                Aspect Ratio       10
                                Unit: millimetre
```

Expect roughly 300 k – 1 M triangles. That is fine.

### 4.3 Blender — clean up and material

```python
# Blender 5.2 - CAD cleanup pass. Run with the imported gate selected.
import bpy, bmesh, math

obj = bpy.context.active_object
bpy.ops.object.mode_set(mode='OBJECT')

# 1. Scale from mm to m if the importer did not, then apply.
#    (skip if your importer already applied 0.001)
# obj.scale = (0.001, 0.001, 0.001)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# 2. Weld the split vertices left by B-rep face boundaries.
me = obj.data
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)   # 0.1 mm
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()

# 3. Mark sharp edges above 30 degrees.
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.mesh.edges_select_sharp(sharpness=math.radians(30.0))
bpy.ops.mesh.mark_sharp()
bpy.ops.object.mode_set(mode='OBJECT')

# 4. Smooth by angle + weighted normals.
bpy.ops.object.shade_auto_smooth(angle=math.radians(35.0))
wn = obj.modifiers.new("WeightedNormal", 'WEIGHTED_NORMAL')
wn.keep_sharp = True
wn.mode = 'FACE_AREA'

# 5. Second UV channel for baked masks.
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
if len(me.uv_layers) == 0:
    me.uv_layers.new(name="UVMap")
bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')

# 6. Set origin to the hinge line so the gate can swing correctly in Unreal.
#    Move the 3D cursor to the hinge axis first, then:
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

obj.name = "SM_Gate_Entrance_Leaf_L"
print(f"{obj.name}: {len(me.polygons)} faces, {len(me.uv_layers)} UV layers")
```

**Material for galvanised steel, painted or bare:**

- Base Color: bare hot-dip galvanising is a **light, slightly blue-grey metal**, and it *changes with age* — bright spangled when new, dull matte grey after a year, developing white zinc-oxide bloom in wet conditions. Painted black or dark green over a primer is at least as common on Namibian gates.
- Metallic 1.0 for bare galvanising, 0.0 for paint.
- Roughness: new galvanising 0.25–0.4; weathered 0.5–0.7; enamel paint 0.25–0.4 fading to 0.5–0.65 with UV chalking.
- **Weathering, driven by baked masks** (`01 §5`): curvature-driven paint chipping on edges; downward-flow rust streaks below any horizontal member and below the hinges; dust film on all up-facing surfaces; sand abrasion polishing the bottom 300 mm; a wear patch at the latch and at hand height on the leading stile.
- **Bake in Blender or Substance Painter**: AO, Curvature, Position (for the height-band masks), Thickness.

### 4.4 Unreal — place it

1. Export FBX from Blender with Scale 1.0, Apply Unit on, Forward `-Z`, Up `+Y`, Apply Scalings `FBX All`, and tangents/binormals exported.
2. Import with `Import Uniform Scale = 100.0`; verify bounds read 158 uu × 180 uu for one leaf.
3. Enable **Nanite** on the mesh (blend mode is Opaque — Nanite-compatible). Set `Max World Position Offset Displacement` to 0 (a gate does not use WPO).
4. Add **collision**: `Collision → Add Box Simplified Collision` for the leaf, or a convex decomposition with 4–6 hulls if the infill matters.
5. Set the **pivot at the hinge axis** (done in Blender) so a Blueprint or Sequencer can rotate the leaf about it.
6. Assign a **Material Instance** of the project's master metal material.
7. **Blend the base into the ground**: add a `Runtime Virtual Texture Sample` to the material and lerp the bottom 60–100 mm toward the sampled landscape values, plus a small modelled sand drift against the lee side of each pillar (`05 §3.5`).
8. Add a **contact shadow** (Directional Light → `Contact Shadow Length` 0.02–0.05) so the thin bars read against the bright sand.
9. Check it at **1 600 mm eye height** and from a vehicle-approach position.

### 4.5 Keeping fabrication and render in sync

- The Fusion `.f3z` and the STEP archive are the record.
- Name the export with the Fusion version: `Gate_Entrance_v007.step` → `SM_Gate_Entrance_Leaf_L_v007.fbx`.
- Script the cleanup (§4.3) so a re-export is a two-minute operation, not a re-do.
- When the fabricator changes something on site — and they will — update Fusion, re-export, re-render. Never patch the render.

---

## 5. Hard-surface checklist

- [ ] Object confirmed as "will be manufactured" before it goes in Fusion
- [ ] All driving dimensions as user parameters, not hard numbers
- [ ] Small fillets grouped as a suppressible timeline feature
- [ ] A 1 000 mm calibration cube exported with every batch
- [ ] Export units set explicitly (mm), not left at default
- [ ] Surface Deviation set from the closest camera distance, not from a preset
- [ ] Merge-by-distance run at 0.1 mm on import
- [ ] Normals recalculated; sharp edges marked; Weighted Normal applied
- [ ] UVs generated (triplanar for base metal + a second channel for masks)
- [ ] Origin at the functional pivot (hinge axis), not at the mesh centre
- [ ] Nanite enabled; collision simplified, not per-triangle
- [ ] Weathering masks baked and applied — no clean new steel in a Namibian yard
- [ ] Base blended into terrain with RVT + a drift mesh
- [ ] STEP + PDF drawing + parts list archived outside Autodesk
- [ ] Render version and Fusion version numbers match

## Sources

- [Autodesk Fusion overview](https://www.autodesk.com/products/fusion-360/overview) — Autodesk
- [FusionAPIReference](https://github.com/AutodeskFusion360/FusionAPIReference) — Autodesk (GitHub)
- [Nanite Virtualized Geometry in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine) — Epic Games
- [Blender Manual](https://docs.blender.org/manual/en/latest/) — Blender Foundation
- Internal: `15_software_autodesk_fusion/10_interoperability-and-alternatives.md`, `15_software_autodesk_fusion/09_api-and-automation.md`, `14_software_blender/07_import-export-and-interoperability.md`, `13_software_unreal_engine/02_project-setup-and-pipeline.md`

## Open questions

- The exact parameter names and value ranges in Fusion's **mesh export Refinement Custom** dialog (Surface Deviation, Normal Deviation, Maximum Edge Length, Aspect Ratio) as of the May 2026 release. The names are as documented historically; `needs-verification` against the current UI.
- Whether Blender 5.2's **`bpy.ops.object.shade_auto_smooth()`** operator signature matches the code above (the operator changed in 4.1 when Auto Smooth became a modifier). `needs-verification` — run it once and check.
- Whether **Fusion's USD export** carries `metersPerUnit` correctly and whether Unreal's USD importer honours it without a manual scale. `needs-verification`.
- Child-safety spacing requirements for gate infill bars under the applicable Namibian/South African standard — see domain `03_codes_standards`. `needs-verification`.
- Availability and current price of a Blender **STEP importer** add-on (STEPper or equivalent) compatible with Blender 5.2. `needs-verification`.
