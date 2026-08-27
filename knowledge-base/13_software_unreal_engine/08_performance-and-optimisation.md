---
id: ue.performance
title: Performance and optimisation for real-time archviz
domain: software_unreal_engine
tags: [performance, budgets, lod, nanite, instancing, hism, draw-calls, texture-streaming, virtual-textures, shader-complexity, culling, level-streaming, profiling, optimisation]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Unreal Engine 5.8. Budget figures are practitioner guidance, not Epic-published values, and are labelled as such."
sources:
  - {title: "Visibility and Occlusion Culling", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/visibility-and-occlusion-culling-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Stat Commands", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/stat-commands-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Nanite Virtualized Geometry", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Lumen Performance Guide", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-performance-guide-for-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Unreal Insights", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-insights-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
related: [ue.materials_rendering, ue.archviz_workflow, ue.core_concepts]
---

# Performance and optimisation for real-time archviz

**Summary.** Archviz performance work differs from game optimisation in one important way: the content is not yours to simplify. A Revit model arrives with the geometry it arrives with, and the client wants it to look like the render. The levers that matter are therefore instancing, culling, streaming, shader cost and lighting cost — not polygon reduction, which Nanite has largely removed as a concern. This file gives frame-time budgets, the specific systems that reduce cost, and a diagnostic order of operations for making a walkthrough run on a client's laptop.

## Key facts

| Target | Frame budget | Notes |
|---|---|---|
| 30 fps | 33.3 ms | Acceptable for a mouse-driven desktop walkthrough |
| 60 fps | 16.7 ms | The right target for a delivered interactive walkthrough |
| 90 fps | 11.1 ms | **Mandatory** for VR. Per eye |
| 120 fps | 8.3 ms | High-refresh VR |

| Diagnostic | Command | What it means |
|---|---|---|
| Where the time goes | `stat unit` | Frame / Game / Draw / GPU / RHIT |
| CPU-bound (render thread) | `Draw` ≈ `Frame` | Too many draw calls, too many visible primitives |
| CPU-bound (game thread) | `Game` ≈ `Frame` | Too much Tick / Blueprint |
| GPU-bound | `GPU` ≈ `Frame` | Shading, lighting, shadows, overdraw |
| Visible primitive count | `stat InitViews` | *Visible Static Mesh Elements* is the key number |
| GPU pass breakdown | `ProfileGPU` | Opens the GPU Visualiser for one captured frame |

> ⚠️ Optimise in this order: **measure → identify the bound → fix the largest single cost → measure again.** Every hour spent reducing triangle counts on a GPU-bound scene whose cost is Lumen reflections is an hour wasted. `stat unit` first, always.

## Budgets

These are practitioner figures for archviz, not Epic-published numbers. Treat them as sanity checks, not rules.

| Metric | Desktop 60 fps target | VR 90 fps target |
|---|---|---|
| Draw calls per frame | < 3 000 | < 1 000 |
| Visible static mesh elements (`stat InitViews`) | < 5 000 | < 2 000 |
| Unique materials in view | < 200 | < 100 |
| Texture streaming pool | fits VRAM with headroom | as small as possible |
| Dynamic shadow-casting lights in view | < 8 movable | < 2, prefer baked |
| Nanite triangles | effectively unbounded | **Nanite unsupported in stereo** |
| Nanite instances (hard engine limit) | 16 million | 16 million |

Note the VR column. Nanite does not support stereo rendering, and Lumen in stereo is expensive. **A VR deliverable is a different build**: non-Nanite meshes with LODs, baked Lightmass lighting, forward rendering with MSAA, and aggressive culling.

## Geometry: LODs and Nanite

**Nanite is the default answer.** Epic's own guidance is to enable it wherever supported: a Nanite mesh typically renders faster and uses less memory and disk than the same mesh without it, and it bypasses traditional draw calls entirely. For a Datasmith-imported building, batch-enabling Nanite (Content Browser multi-select → right-click → *Nanite > Enable*) is usually the single largest performance win available, and it takes a minute.

Where Nanite does not apply, traditional **LODs** still matter:

- Translucent geometry — glass, water, glazed balustrades
- VR builds
- Anything with morph targets
- Foliage using heavy World Position Offset (Nanite splits WPO meshes into individually culled clusters; unclamped displacement multiplies that cost)

Generate LODs in the Static Mesh Editor (*LOD Settings > Number of LOD Levels*, or *LOD Group*) or in bulk from Python via `StaticMeshEditorSubsystem.set_lods(static_mesh, reduction_options)`. A reasonable archviz chain is LOD0 100%, LOD1 50%, LOD2 25%, LOD3 12%, with screen sizes tuned so the switch is invisible. `LOD Group` presets (`LargeProp`, `SmallProp`, `Foliage`) do this adequately without per-mesh work.

**Fallback meshes** matter under Nanite: ray tracing and some other passes trace against a Nanite mesh's Fallback Mesh, not its full detail. Lower *Fallback Relative Error* in the Static Mesh Editor to make the fallback closer to the source when ray-traced reflections look wrong.

## Instancing

A draw call per object is the cost model for non-Nanite geometry. Instancing collapses many copies of one mesh into one call.

| Component | When |
|---|---|
| `UInstancedStaticMeshComponent` (ISM) | Many instances, all at similar distance, no per-instance culling needed |
| `UHierarchicalInstancedStaticMeshComponent` (HISM) | Many instances over distance — supports per-instance culling and LOD |
| Foliage editor mode | Painting vegetation; produces HISM automatically |
| Level Instance | A whole repeated sub-level (an apartment unit, a house type) |
| `Merge Actors` (`Tools > Merge Actors`) | Combining distinct static meshes into one; also builds HLOD proxies |

For a residential estate — boundary walls, paving units, roof sheeting, plant stock, street furniture — HISM is the correct structure. Build it from Python rather than by hand:

```python
import unreal

def scatter_hism(mesh_path, transforms, label="HISM_BoundaryWall"):
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)

    actor = actors.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0))
    actor.set_actor_label(label)
    comp = actor.add_component_by_class(
        unreal.HierarchicalInstancedStaticMeshComponent, False,
        unreal.Transform(), False)
    comp.set_static_mesh(mesh)
    for t in transforms:
        comp.add_instance(t)
    return actor
```

(`add_component_by_class` signature varies by engine version — **verify against your build** before relying on it in a pipeline.)

**Instances share one material.** If each fence panel must be a different colour, instancing is off the table unless you drive the variation through per-instance custom data floats read in the material.

## Draw calls

For non-Nanite geometry, one draw call per mesh section per visible object. Reduce them by:

1. **Nanite** — bypasses the draw-call path entirely.
2. **Instancing** — many objects, one call.
3. **Merging** — `Tools > Merge Actors` on static clusters that always appear together.
4. **Fewer material slots per mesh.** A Datasmith-imported wall with fourteen material slots costs fourteen draw calls. Consolidate materials before consolidating geometry.
5. **Atlasing textures** so several meshes can share one material instance.
6. **Culling** — see below.

Measure with `stat RHI` (draw call count) and `stat InitViews` (visible elements). If `Draw` time in `stat unit` dominates, this section is your problem.

## Culling

Epic documents four methods, applied in ascending order of cost: **Distance → View Frustum → Precomputed Visibility → Dynamic Occlusion.** Unreal uses View Frustum culling and Hardware Occlusion Queries by default; with many Actors, the occlusion queries themselves cost GPU time.

Culling tests use an Actor's **bounds** — a bounding sphere (fast distance test, usually larger than the object) and a bounding box (closer fit, more accurate). Visualise with `Show > Advanced > Bounds` in the viewport, `Bounds` in the Static Mesh Editor toolbar, or `Character > Bounds` in the Skeletal Mesh Editor. Bounds scale automatically to imported geometry and to scaling or rotation in the viewport.

You can adjust bounds via *Bounds Scale* in the Details panel (a uniform multiplier) or via *Positive/Negative Bounds Extension* in the mesh editors (non-uniform). **Enlarging bounds hurts performance and shadow quality** by preventing an Actor from being culled as early as it otherwise would.

Practical archviz culling:

- **Cull Distance Volumes** — a per-volume table mapping object size to a cull distance. The right tool for a site with many small props.
- Per-Actor **Desired Max Draw Distance** on a primitive component.
- **Precomputed Visibility Volumes** — baked visibility, valuable in a heavily occluded interior on weak hardware, but requires a build and only helps where the camera is constrained.
- `r.AllowOcclusionQueries`, `r.HZBOcclusion`, and the diagnostic `r.VisualizeOccludedPrimitives`.
- **Round Robin Occlusion** exists specifically for VR — alternate eyes per frame for occlusion queries.

The most effective culling in a building is architectural: **occluders**. A solid wall occludes everything behind it, but only if the engine can tell. Ensure walls are single closed meshes rather than thin surfaces with gaps, and that Nanite is enabled on them (Epic lists "acts as a major occluder of other Nanite geometry" as a reason to enable Nanite).

## Textures and streaming

Texture memory is usually the first thing to break on a modest GPU. A Datasmith import from an unmanaged model routinely arrives with dozens of 4096 × 4096 textures for surfaces that occupy 200 pixels on screen.

- **Right-size every texture.** `Maximum Texture Size` in the Texture asset, or a bulk pass from Python. 2048 for a hero surface, 1024 for most architectural finishes, 512 for small props.
- **Compression settings** matter: `Default (DXT1/5)` for colour, `Normalmap (BC5)` for normals, `Masks (no sRGB)` for packed ORM. Getting sRGB wrong on a mask map is the most common archviz texture bug.
- **Texture Streaming Pool.** The Output Log warning "Texture streaming pool over budget" means exactly what it says. Raise it with `r.Streaming.PoolSize <MB>` if you have the VRAM; otherwise reduce texture sizes. Diagnose with `stat Streaming` and the `Texture Streaming Accuracy` viewport view modes.
- **Virtual Textures (VT)** page in only the texels actually visible, decoupling texture memory from texture resolution. Enable per texture (*Virtual Texture Streaming*) and project-wide in `Project Settings > Rendering > Virtual Textures`. Epic notes virtual textures are *not required* for Nanite but are *highly recommended* — they solve for texture data what Nanite solves for mesh data.
- **Runtime Virtual Textures (RVT)** bake landscape material output into a texture the terrain and anything reading it can sample cheaply. In archviz they are the standard way to blend paths, ground decals and building bases into the landscape without a visible seam.

## Shader complexity

Use the **Shader Complexity** viewport view mode. Green is cheap, red is expensive, white is catastrophic. In archviz the two reliable causes of red are:

1. **Overlapping translucency.** Glass behind glass behind a curtain behind a window. Each layer costs a full-screen-area shading pass where it covers pixels. Reduce layers, or use *Masked* where the effect allows.
2. **Over-complex master materials.** A master material with forty texture samples and a dozen dynamic branches costs that on every pixel it covers, whether the instance uses them or not. Use **static switches** (compiled out) rather than runtime `if`/`Lerp` for features an instance either has or does not.

Watch **shader permutation count** too: every unique combination of static switches is a separate compiled shader, and permutation explosion is the usual reason a cook takes six hours. `stat ShaderCompiling` and the shader compiler progress bar tell you when this has got out of hand.

`r.Shaders.Optimize`, `Quad Overdraw` view mode and the Material Editor's instruction-count readout (top of the preview panel) are the other tools.

## Lighting cost

Under Lumen, lighting is frequently the dominant GPU cost in an interior. Tuning order:

1. **`Final Gather Quality`** in the Post Process Volume — the highest-leverage single value.
2. **`Lumen Scene Detail`** and **`Lumen Scene View Distance`** — reducing these removes small objects and distance from the Lumen scene.
3. **`r.Lumen.ScreenProbeGather.DownsampleFactor`** and **`r.Lumen.ScreenProbeGather.TracingOctahedronResolution`** — raise the downsample factor to trade quality for speed.
4. **`r.Lumen.Reflections.DownsampleFactor`** and **`r.Lumen.Reflections.MaxRoughnessToTraceClamp`** — reflections are often half the Lumen cost; clamping max roughness stops Lumen tracing reflections on surfaces where nobody will see them.
5. **`r.LumenScene.DirectLighting.UpdateFactor`** and **`r.LumenScene.Radiosity.UpdateFactor`** — allow more caching, propagate changes more slowly.
6. **`r.Lumen.AsyncCompute`**, `r.Lumen.DiffuseIndirect.AsyncCompute`, `r.Lumen.Reflections.AsyncCompute` — overlap Lumen with other GPU work.
7. **Software vs Hardware ray tracing.** Hardware is higher quality but Epic warns of *significant scene update costs above 100 000 instances*. For a dense archviz scene, test both.
8. **`r.RayTracing.Culling.Radius`** and `r.RayTracing.Culling.Angle` when using hardware ray tracing.
9. **Lumen Lite** (Beta in 5.8) — roughly twice as fast as high-quality Lumen with art direction preserved. Test it for the laptop build.

For **Virtual Shadow Maps**: the cost is page invalidation, not resolution. A stationary sun with static geometry caches almost completely. A moving sun invalidates directional pages every frame — raise `r.Shadow.Virtual.ResolutionLodBiasDirectionalMoving`. Many *moving* local lights are expensive; many *static-in-space movable* local lights are not. Diagnose with `r.Shadow.Virtual.ShowStats` and `r.Shadow.Virtual.Visualize`.

## Level streaming

For a single house, load everything. For a site, an estate or a masterplan:

- **World Partition** with `Enable Streaming` on in World Settings streams grid cells by distance from the streaming source, automatically.
- **World Partition HLOD** generates proxies for distant cells so the horizon is not empty.
- **Data Layers** let you toggle whole logical sets — construction phases, design options, furniture, services — at runtime and in the editor.
- **Legacy sublevels** remain valid and are often simpler: split by storey, or by shell / interior / furniture / landscape, and stream by volume or from Blueprint.
- **Level Instances** for repeated units, so one apartment layout exists once as an asset.

Diagnose with `stat Levels` and `stat Streaming`.

## Game-thread cost

Usually a non-issue in archviz, but when `Game` dominates `stat unit`:

- **Turn off Tick.** `PrimaryActorTick.bCanEverTick = false` in C++, or uncheck *Start with Tick Enabled* in a Blueprint's Class Defaults. Most archviz Actors never need to tick.
- **Replace Tick with Timers.** An interaction trace at 10 Hz is indistinguishable from one at 120 Hz and costs a twelfth as much.
- **Avoid `Get All Actors of Class` on Tick.** It iterates every Actor in the world. Cache the result once.
- **Avoid UMG property bindings.** Each is a function evaluated every frame. Push values on change via an Event Dispatcher instead.
- **Heavy Construction Scripts** slow the editor and every level load, not the runtime — but they slow *you*, which is worse.
- `stat Game`, `stat Dumpticks` and `stat Component` locate the offender.

## Archviz-specific optimisation for modest hardware

A realistic sequence for making a walkthrough run on a client's four-year-old laptop:

1. **Set the target and measure.** `stat unit` at the worst viewpoint in the building — usually standing in a doorway with the whole plan and the exterior visible.
2. **`r.ScreenPercentage 66` with TSR.** Renders at two-thirds resolution and reconstructs. Frequently a 40–50% GPU saving for a barely perceptible quality loss. This is the cheapest big win and should be tried first.
3. **Nanite on everything opaque.** Free draw-call reduction.
4. **Right-size textures.** Bulk pass to 1024 with 2048 for hero surfaces.
5. **Lumen quality down.** Final Gather Quality, Lumen Scene Detail, reflection downsample factor. Or Lumen Lite.
6. **Cull Distance Volumes** for props and landscape scatter.
7. **Cut movable shadow-casting lights.** Turn off *Cast Shadows* on fill lights that contribute no visible shadow — most interior fill lights.
8. **Reduce translucent layering.** The single biggest archviz shader-complexity fix.
9. **Scalability settings.** `Settings > Engine Scalability Settings` in the editor; ship the packaged build with a settings menu driving `r.` scalability groups so the client can choose. Test at **Medium**, not Epic.
10. **If it still will not hold 60 fps**, change strategy: bake with Lightmass, drop Lumen and Nanite, and ship a forward-rendered build. That is a different project, so decide early.

## Profiling toolset summary

| Tool | Use |
|---|---|
| `stat unit` / `stat unitgraph` | First stop. Identifies the bound |
| `stat fps`, `stat Engine` | Frame rate and triangle counts |
| `stat SceneRendering` | Rendering breakdown |
| `stat InitViews` | Culling effectiveness; visible element counts |
| `stat RHI` | Draw calls, RHI memory |
| `stat LightRendering`, `stat ShadowRendering` | Lighting and shadow cost |
| `stat Memory`, `stat LLM`, `stat MemoryStaticMesh` | Memory attribution |
| `stat Streaming`, `stat Levels` | Texture and level streaming |
| `stat Hitches`, `t.HitchFrameTimeThreshold` | Frame spikes |
| `ProfileGPU` | GPU Visualiser, per-pass timings for one frame |
| Viewport view modes | Shader Complexity, Quad Overdraw, Light Complexity, Lightmap Density, Nanite and Lumen visualisations |
| Unreal Insights | Full timeline trace; Trace Recorder listens on port **1981**, traces saved as `.utrace` |
| Console Variables Editor | Save and apply cvar presets |
| `stat Help` | Lists every stat command |

Launch with `-LOG=MyLog.txt` to capture stat dumps to file for later comparison, and record a baseline capture before you start optimising so you can prove the improvement.

## Open questions

- Budget figures in the Key facts and Budgets tables are practitioner guidance, not Epic-published values.
- `r.Streaming.PoolSize` was not verified on the texture streaming page fetched — **needs verification**.
- `add_component_by_class` Python signature varies between engine versions — **needs verification** against the local build.
- Round Robin Occlusion is named in Epic's culling documentation as VR-oriented, but its exact console variable was not captured.

## Sources

- [Visibility and Occlusion Culling](https://dev.epicgames.com/documentation/en-us/unreal-engine/visibility-and-occlusion-culling-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Cull Distance Volumes](https://dev.epicgames.com/documentation/en-us/unreal-engine/cull-distance-volumes-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Nanite Virtualized Geometry](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Lumen Performance Guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-performance-guide-for-unreal-engine) — Epic Games, accessed 2026-08-25
- [Virtual Shadow Maps](https://dev.epicgames.com/documentation/en-us/unreal-engine/virtual-shadow-maps-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Temporal Super Resolution](https://dev.epicgames.com/documentation/en-us/unreal-engine/temporal-super-resolution-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Virtual Texturing](https://dev.epicgames.com/documentation/en-us/unreal-engine/virtual-texturing-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Texture Streaming](https://dev.epicgames.com/documentation/en-us/unreal-engine/texture-streaming-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Creating and Using LODs](https://dev.epicgames.com/documentation/en-us/unreal-engine/creating-and-using-lods-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Instanced Static Mesh Component](https://dev.epicgames.com/documentation/en-us/unreal-engine/instanced-static-mesh-component-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Level Streaming](https://dev.epicgames.com/documentation/en-us/unreal-engine/level-streaming-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [World Partition](https://dev.epicgames.com/documentation/en-us/unreal-engine/world-partition-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Stat Commands](https://dev.epicgames.com/documentation/en-us/unreal-engine/stat-commands-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Unreal Insights](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-insights-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Testing and Optimizing Your Content](https://dev.epicgames.com/documentation/en-us/unreal-engine/testing-and-optimizing-your-content) — Epic Games, accessed 2026-08-25
