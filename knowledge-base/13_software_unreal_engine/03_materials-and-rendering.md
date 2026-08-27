---
id: ue.materials_rendering
title: Unreal Engine materials and rendering
domain: software_unreal_engine
tags: [material-editor, pbr, material-instance, nanite, lumen, virtual-shadow-maps, path-tracer, ray-tracing, tsr, lightmass, lightmap, post-process, exposure, color-grading, profiling, console-variables]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Unreal Engine 5.8. Console variables verified against 5.8 documentation; Lumen/Nanite behaviour is broadly the same from 5.4."
sources:
  - {title: "Nanite Virtualized Geometry", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Lumen Global Illumination and Reflections", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Virtual Shadow Maps", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/virtual-shadow-maps-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Temporal Super Resolution", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/temporal-super-resolution-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Stat Commands", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/stat-commands-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Unreal Insights", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-insights-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
related: [ue.archviz_workflow, ue.performance, ue.overview]
---

# Unreal Engine materials and rendering

**Summary.** Unreal's renderer is physically based: materials describe surface response in metallic/roughness terms, lights are entered in real photometric units, and the camera applies a filmic tonemap. UE5 replaced three of the four legacy pillars — Nanite replaced the LOD budget, Lumen replaced the lightmap bake, Virtual Shadow Maps replaced cascaded shadow maps — and Temporal Super Resolution replaced TAA upscaling. This file covers the material graph, the four rendering systems and their real constraints, when the old baked-lightmap workflow is still the correct answer, post-processing and exposure, and the profiling tools you use to find out why a frame is slow.

## Key facts

| System | Purpose | Hard requirement | Main archviz caveat |
|---|---|---|---|
| Nanite | Virtualised geometry | DX12 SM6.6 atomics or Vulkan `VK_KHR_shader_atomic_int64`; SM6 enabled | Opaque and Masked blend modes only; no Nanite for glass |
| Lumen | Dynamic GI and reflections | SM6; DX12; RTX-2000 / RX-6000 / Arc A-series or newer | Disables all baked lightmaps when enabled |
| Virtual Shadow Maps | High-resolution shadows | SM6 | Cost scales with light count and page invalidation |
| MegaLights | Many-light rendering (Production Ready in 5.8) | Same as Lumen | New; validate before committing |
| TSR | Temporal upscaling and AA | SM5 minimum; 16-bit types on D3D12 SM6 | Ghosting on fast-moving thin geometry |
| Path Tracer | Reference offline renderer inside UE | Hardware ray tracing | Not real-time; use via Movie Render Graph |
| Lightmass | Precomputed static GI | None | Incompatible with Lumen; requires UV1 lightmap UVs |
| Max Nanite instances | Hard limit | — | 16 million instances streamed in, across the whole scene |
| Light unit relationships | — | — | 1 cd = 625 unitless; 1 cd = 1 lm/sr |

> ⚠️ Enabling Lumen hides every lightmap in the project. You cannot mix a Lumen exterior with a Lightmass-baked interior in the same world. Choose the lighting strategy before you build materials, because the material authoring differs (bounce-friendly diffuse values matter far more under Lumen).

## The material editor

A Material is a shader authored as a node graph. Its output node has the PBR inputs:

| Input | Range | Archviz notes |
|---|---|---|
| Base Color | linear RGB | Real-world albedo. Nothing is darker than ~0.02 or brighter than ~0.9. Fresh snow ≈ 0.81, white paint ≈ 0.85, asphalt ≈ 0.05–0.10, dry sand ≈ 0.30–0.40 |
| Metallic | 0 or 1 | Binary in practice. Painted steel is 0 with a metal *underneath* only if worn |
| Specular | 0–1, default 0.5 | Leave at 0.5. It maps to IOR ≈ 1.5, correct for almost all dielectrics |
| Roughness | 0–1 | The single most important channel for realism. Polished concrete ≈ 0.25, matt plaster ≈ 0.85, brushed aluminium ≈ 0.35 |
| Normal | tangent-space | |
| Emissive Color | cd/m² when used for lighting | Emissive surfaces are expressed in candela per square metre |
| Opacity / Opacity Mask | 0–1 | Blend mode dependent |
| Ambient Occlusion | 0–1 | Micro-occlusion only; Lumen handles the rest |
| World Position Offset | vector, cm | Foliage wind, deformation. Limited under Nanite |
| Displacement | scalar | Nanite tessellation |

**Blend Modes:** Opaque, Masked, Translucent, Additive, Modulate. **Shading Models:** Default Lit, Unlit, Subsurface, Preintegrated Skin, Clear Coat, Subsurface Profile, Two Sided Foliage, Hair, Cloth, Eye, Single Layer Water, Thin Translucent.

**Substrate** is the newer, layered material system replacing the fixed shading-model list with composable BSDF slabs. UE 5.8 adds X-Rite AxF measured-material import into Substrate, which is the accurate route for scanned finishes, and an experimental Substrate Toon BSDF for non-photorealistic output. Substrate is a project-wide switch; do not flip it mid-project.

### Master materials and instances — the only sane workflow

Author a small number of **master materials** with parameters exposed (`ScalarParameter`, `VectorParameter`, `TextureSampleParameter2D`, `StaticSwitchParameter`), then create **Material Instances** from them. Reasons:

- A material instance is a set of parameter values, not a shader. Changing it does **not** trigger a shader recompile. Changing the master does — for every instance.
- `MaterialInstanceConstant` (`MI_`) is the asset. `MaterialInstanceDynamic` (MID) is the runtime object you create in Blueprint with `Create Dynamic Material Instance` to animate a parameter — the mechanism behind a runtime finishes configurator.
- Instances can be nested: `M_Master_Architectural` → `MI_Brick_Base` → `MI_Brick_Facebrick_Grey`.
- Python and Blueprint can create and populate instances in bulk. See file `06`.

A serviceable archviz master material set is four or five graphs: an architectural opaque (tiling texture set + tint + roughness scale + UV scale), a glass, a foliage/two-sided, a decal, and an emissive. Everything else is an instance.

**Static switches** compile out branches, so one master can serve many cases without runtime cost — but each unique combination of static switch values is a separate shader permutation, and permutation count is the main cause of hour-long cooks.

## Nanite

Nanite meshes are Static Meshes with a flag set. On import the mesh is analysed and broken into hierarchical clusters of triangle groups; at render time clusters are swapped at varying LOD based on the camera view, connecting without cracks, streamed on demand, in a rendering pass that **completely bypasses traditional draw calls**.

Enable it: on import (check **Build Nanite**), per-mesh in the Static Mesh Editor (*Nanite Settings > Enable Nanite Support*), or in batch — select meshes in the Content Browser, right-click, **Nanite > Enable**.

Epic's guidance is to **enable Nanite wherever possible**: a Nanite mesh typically renders faster and takes less memory and disk than a non-Nanite one. A mesh is an especially good candidate if it has many triangles, has triangles that will be small on screen, has many instances, occludes other Nanite geometry, or casts Virtual Shadow Map shadows. The classic exception is a sky sphere — large on screen, occludes nothing, one instance.

**When importing for Nanite, disable *Generate Lightmap UVs*** unless you are also baking with Lightmass. Building Nanite on highly detailed geometry already adds significant import time, and the extra UV channel is a lot of data on a dense mesh.

### Nanite constraints that matter in archviz

- **Materials:** Opaque and Masked blend modes only. An unsupported material causes a default material assignment plus an Output Log warning. **Glass is therefore not Nanite.** Keep windows, glazed balustrades and water as non-Nanite translucent meshes.
- No **Mesh Decals** (they need translucent blend). Ordinary projected decals *do* work on Nanite surfaces.
- Wireframe checkbox unsupported.
- `Vertex Interpolator` and Custom UVs work but evaluate three times per pixel; Custom UV0 and UV1 are hardware-interpolated in hardware rasterisation.
- **Custom expression nodes** (and functions built on them, e.g. `ParallaxOcclusionMapping`) may produce artifacts — Nanite has no analytic derivative support yet.
- **Per-vertex tangents are not stored**; tangent space is derived in the pixel shader. Can cause discontinuities at edges, rarely significant.
- **Morph targets are not supported.** World Position Offset *is* supported but limited: WPO-displaced Nanite meshes are split into smaller clusters that are culled individually on the GPU, so you must clamp displacement amount.
- **Not supported:** view-specific filtering by Minimum Screen Radius or distance culling, Forward Rendering, **stereo rendering for VR**, MSAA, Lighting Channels, and ray tracing against Nanite meshes (a Fallback Mesh is used instead; lower *Fallback Relative Error* to use more source triangles; experimental native ray tracing via `r.RayTracing.Nanite.Mode 1`).
- **Hard limit: 16 million instances** streamed in at once, counting all instances, not only Nanite ones.

The VR exclusion is the one that catches archviz teams: if the deliverable includes a VR walkthrough, plan for a non-Nanite (or dual) mesh path.

Component types that support Nanite meshes: static mesh, skeletal mesh, instanced static mesh, spline mesh, hierarchical instanced static mesh, geometry collection, foliage painter, landscape grass. Nanite also supports landscapes, splines, offline static displacement mapping, and runtime tessellation.

## Lumen

Enable in `Project Settings > Engine > Rendering`: *Dynamic Global Illumination Method* = **Lumen**, *Reflection Method* = **Lumen**. This auto-enables *Generate Mesh Distance Fields* (needed for software ray tracing) and requires a restart. Lumen GI replaces Distance Field Ambient Occlusion; Lumen Reflections replace Screen Space Reflections.

What it gives you:

- **Infinite diffuse bounces** — critical in white-painted interiors, which is most residential archviz.
- Sky lighting solved as part of the final gather, **including sky shadowing**, so interiors are naturally much darker than the exterior without faking it.
- Emissive materials propagate light through the final gather at no extra cost — but small, bright emissive areas cause noise.
- Reflections across the full roughness range, on clear coat, on translucency (glossy; mirror on the front layer with *High Quality Translucency Reflections*), and on Single Layer Water (forced mirror).
- All light types supported: Directional, Sky, Point, Spot, Rect, with Light Functions. **Lights with Mobility = Static are not supported** — static lights live entirely in lightmaps, whose contribution Lumen disables.

**Software vs Hardware ray tracing.** Software traces against mesh distance fields (*Detail Tracing*, highest quality) or the coarser Global Distance Field (*Global Tracing*, fastest). Hardware ray tracing is higher quality but Epic warns of *significant scene update costs for scenes with more than 100 000 instances*. *Ray Lighting Mode* defaults to Surface Cache for performance; *Hit Lighting for Reflections* is higher quality.

**Post Process Volume controls** (the artist-facing knobs, under Global Illumination and Reflections):

| Setting | Effect |
|---|---|
| Lumen Scene Lighting Quality | Higher fidelity Lumen Scene, visible in reflections, higher GPU cost |
| Lumen Scene Detail | Size of instances representable in Lumen Scene; higher = small objects included |
| Lumen Scene View Distance | Range of sky shadowing and GI; higher = more GPU |
| Final Gather Quality | Less noise, more GPU |
| Screen Traces | Screen-space traces bypass Lumen Scene and sample scene depth/colour |
| Max Trace Distance | Too small leaks light into enclosed spaces such as basements |
| Diffuse Color Boost | `pow(DiffuseColor, 1/Boost)`. Not physically correct; keep below 2. A legitimate art-direction knob for gloomy interiors |
| Skylight Leaking | Fraction of sky light allowed to leak into unlit interiors |

Useful console variables for tuning (verified in the Lumen Performance Guide): `r.Lumen.ScreenProbeGather.DownsampleFactor`, `r.Lumen.ScreenProbeGather.TracingOctahedronResolution`, `r.Lumen.Reflections.DownsampleFactor`, `r.Lumen.Reflections.MaxRoughnessToTraceClamp`, `r.Lumen.HardwareRayTracing.MaxIterations`, `r.LumenScene.DirectLighting.UpdateFactor`, `r.LumenScene.Radiosity.UpdateFactor`, `r.Lumen.AsyncCompute`, `r.RayTracing.Culling.Radius`.

**Lumen Lite** (Beta in 5.8) is a medium-quality irradiance-field GI path with probe occlusion, roughly twice as fast as high-quality Lumen while preserving art direction. Worth testing for a walkthrough that must run on a client's laptop.

## Virtual Shadow Maps

VSMs give consistent, high-resolution shadows across an entire scene by paging a very large virtual shadow map and only rendering the pages that are actually sampled. They pair with Nanite: Nanite geometry rendering into VSM pages is cheap; non-Nanite geometry is not.

Key console variables (all verified on the VSM page): `r.Shadow.Virtual.Enable`, `r.Shadow.Virtual.Cache`, `r.Shadow.Virtual.MaxPhysicalPages`, `r.Shadow.Virtual.ResolutionLodBiasDirectional`, `r.Shadow.Virtual.ResolutionLodBiasLocal`, `r.Shadow.Virtual.ResolutionLodBiasDirectionalMoving`, `r.Shadow.Virtual.SMRT.RayCountDirectional`, `r.Shadow.Virtual.SMRT.SamplesPerRayDirectional`, `r.Shadow.Virtual.NormalBias`, `r.Shadow.Virtual.Clipmap.FirstLevel` / `.LastLevel`, `r.Shadow.Virtual.OnePassProjection`-adjacent settings, plus the diagnostics `r.Shadow.Virtual.ShowStats`, `r.Shadow.Virtual.Stats`, `r.Shadow.Virtual.Visualize`, `r.Shadow.Virtual.Visualize.LightName`, `r.Shadow.Virtual.Visualize.NextLight`.

Archviz-specific advice: **cache invalidation is the cost.** A moving directional light (an animated sun study) invalidates directional pages every frame. If a sun-study sequence is slow, that is why — raise `r.Shadow.Virtual.ResolutionLodBiasDirectionalMoving` or accept the cost in offline rendering where it does not matter. Interior spot and rect lights that never move are nearly free once cached; adding many *moving* local lights is not.

## Path tracing, ray tracing and TSR

**Path Tracer** is a physically correct, progressively refining renderer built into the same viewport, using the same materials, lights and geometry. Enable *Support Hardware Ray Tracing* and *Path Tracing* in Project Settings, then switch the viewport view mode to Path Tracing. It is the reference for "what should this look like" and, driven through Movie Render Graph, a legitimate final-output path for hero stills. It does not support every material feature, and Nanite meshes are traced via their Fallback Mesh unless `r.RayTracing.Nanite.Mode 1` is set.

**Hardware ray tracing** also powers optional ray-traced shadows, ambient occlusion and reflections independent of Lumen. In offline Movie Render Queue renders Epic's own high-quality guide sets `r.RayTracing.GlobalIllumination 1` (brute force, multiple bounces), `r.RayTracing.GlobalIllumination.MaxBounces 2`, `r.RayTracing.Reflections.MaxRoughness 1`, `r.RayTracing.Reflections.MaxBounces 2`, `r.RayTracing.Reflections.Shadows 2`.

**Temporal Super Resolution (TSR)** renders at a lower internal resolution and reconstructs to output resolution using temporal history. It is UE5's default anti-aliasing and upscaler. Controls: `r.AntiAliasingMethod`, `r.ScreenPercentage`, `r.TSR.History.ScreenPercentage`, `r.TSR.History.UpdateQuality`, `r.TSR.ShadingRejection.Flickering`, `r.TSR.RejectionAntiAliasingQuality`, `r.TSR.Resurrection`, `r.TSR.Visualize`. For a real-time walkthrough on modest hardware, `r.ScreenPercentage 66` with TSR usually looks better than native resolution with a cheaper AA method. For offline output, TSR is turned **off** in favour of Movie Render Queue's spatial and temporal sample accumulation.

## The baked lightmap workflow — and when it is still right

**Lightmass** precomputes static global illumination into lightmap textures. It requires:

- Lights with Mobility = **Static** (fully baked) or **Stationary** (baked indirect, dynamic direct, limited to 4 overlapping)
- Meshes with a clean, non-overlapping **UV channel 1** with adequate padding
- A **Lightmass Importance Volume** around the region of interest
- A build: `Build > Build Lighting Only`

It is incompatible with Lumen. Use it when:

- **The target hardware cannot run Lumen.** A packaged walkthrough for a client's four-year-old laptop, an integrated-GPU machine, or a mobile/standalone VR headset.
- **VR.** Baked lighting plus a forward renderer with MSAA remains the reliable path to a stable 90 fps stereo image. Lumen in stereo is expensive and Nanite does not support stereo rendering.
- **Absolute frame-time determinism** matters — an exhibition kiosk that must never drop frames.
- The scene is genuinely static and the sun does not move.

If none of those apply, use Lumen. Baking a residential interior costs hours per iteration and destroys the ability to move the sun, which is the single most persuasive thing you can show a client on a Namibian site.

The ArchViz template ships both: an Exterior level demonstrating a dynamic SunSky time-of-day sequence, and an Interior level demonstrating precomputed static lighting with Lightmass.

## Post-process, exposure and colour grading

Place a **Post Process Volume** in every level and tick *Infinite Extent (Unbound)*. Epic explicitly recommends this: default post-process settings apply even with no volume present, and they may affect camera settings in unexpected ways.

**Exposure.** UE expresses auto-exposure in **EV100 (ISO 100)**. The relevant settings live under *Lens > Exposure*:

- *Metering Mode*: Auto Exposure Histogram, Auto Exposure Basic, or **Manual**. For archviz stills and controlled sequences, **Manual** is correct — auto-exposure drifting between shots is a defect, not a feature.
- *Exposure Compensation*, *Min EV100*, *Max EV100*, *Histogram Min/Max EV100*, *Speed Up*, *Speed Down*.
- Epic's own troubleshooting: if the image goes white after placing a light, the auto-exposure range is too limited — raise *Auto Exposure Max EV100* and *Histogram Max EV100*. If reflective surfaces show black patches, the SceneColor buffer may be overflowing — enable *Apply Pre-Exposure before writing to scene color* in Project Settings or reduce light brightness. Histogram instability can be reduced by narrowing the Min/Max range around actual scene usage; use the **Visualize HDR** show flag to see that usage.
- `Project Settings > Rendering > Default > Extend default luminance range in Auto Exposure settings` must be on for the SunSky Actor to display correctly out of the box.

**Colour grading** is organised as Global / Shadows / Midtones / Highlights, each with Saturation, Contrast, Gamma, Gain, Offset, plus Temperature (White Balance) and Tint, and a *Color Grading LUT* slot. The tonemapper is filmic (ACES-derived) with *Film* controls (Slope, Toe, Shoulder, Black clip, White clip) and *Expand Gamut*. For archviz, grade lightly: the client is judging the building, not your look.

Other volume settings that matter: *Bloom* (keep low; Convolution bloom for hero stills), *Lens Flares* (usually off), *Image Effects > Vignette Intensity* (low), *Depth of Field* (Cinematic; driven from the Cine Camera's aperture, not here), *Motion Blur*, *Chromatic Aberration* (off — it reads as a defect in architecture), *Film Grain*, and *Local Exposure* (Highlight/Shadow Contrast Scale — genuinely useful for retaining detail in a bright window seen from a dark room, which is the defining exposure problem of interior archviz).

`Project Settings > Rendering > Default Settings > Auto Exposure Bias` and the OCIO configuration matter if you are delivering into a colour-managed pipeline.

## Profiling

**Viewport show and view modes** (`Lit` dropdown) — the fastest diagnosis:

- **Shader Complexity** — green good, red bad. Overlapping translucency turns interiors red.
- **Quad Overdraw**, **Light Complexity**, **Lightmap Density** (colour-coded, aim for even blue/green), **Stationary Light Overlap**
- **Nanite Visualization** → Triangles, Clusters, Overdraw, Material Complexity, Mask
- **Lumen** → Lumen Scene, Surface Cache, Geometry Normals, Reflection View
- **Virtual Shadow Map** → `r.Shadow.Virtual.Visualize`
- **Visualize HDR**, **Visualize Local Exposure**

**Stat commands** (type `stat <name>` in the console; also on the viewport Stat dropdown). The ones that earn their keep:

| Command | Tells you |
|---|---|
| `stat fps`, `stat unit` | Frame, Game, Draw, GPU and RHIT times. **Always start here** — it tells you whether you are CPU- or GPU-bound |
| `stat unitgraph` | The same over time |
| `stat SceneRendering` | General rendering breakdown; good first stop for slow rendering |
| `stat InitViews` | Visibility culling cost and effectiveness. *Visible Static Mesh Elements* is the single most important number for render-thread cost |
| `stat GPU` | GPU statistics for the frame |
| `stat RHI` | RHI memory and performance |
| `stat LightRendering` | Lighting and shadow render cost |
| `stat ShadowRendering` | Shadow calculation cost, separate from shadow render time |
| `stat Memory`, `stat MemoryStaticMesh`, `stat LLM` | Memory by subsystem |
| `stat Streaming`, `stat Levels` | Texture and level streaming |
| `stat Engine` | Frame time plus triangle counts |
| `stat Hitches` / `stat DumpHitches` | Uses `t.HitchFrameTimeThreshold`; writes hitches to the log |
| `stat Help` | Lists all stat commands |

Log the output by launching with `LOG=`, e.g. `UnrealEditor.exe -silent LOG=MyLog.txt`.

**GPU Visualiser** — `ProfileGPU` in the console captures one frame and opens a hierarchical breakdown of GPU passes with timings. This is where you discover that Virtual Shadow Maps or Lumen Reflections are eating half your frame.

**Unreal Insights** — the telemetry capture and analysis suite. Trace events are recorded by the **Unreal Trace Server** (`UnrealTraceServer.exe` in `Engine/Binaries/Win64`; the Trace Recorder listens on **port 1981**) into `.utrace` files with companion `.ucache` files. Launch from the editor's Trace/Insights status-bar widget in the bottom toolbar, or run the prebuilt `Engine\Binaries\[Platform]\UnrealInsights.exe`. Build from source with `Engine/Build/BatchFiles/RunUBT.bat UnrealInsights Win64 Development`. Trace sessions are self-describing and compatible across engine versions.

**Console Variables Editor** — a UI for setting and saving cvar presets, far better than typing into the console repeatedly.

## Open questions

- `r.Shadow.Virtual.OnePassProjection` was inferred rather than read from the VSM cvar list — **needs verification**.
- Albedo reference values quoted above are standard photometric figures, not from Epic documentation.
- Substrate's default-on/default-off status in 5.8 was not confirmed on the pages fetched — **needs verification** before starting a Substrate project.

## Sources

- [Nanite Virtualized Geometry](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Lumen Global Illumination and Reflections](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Lumen Performance Guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-performance-guide-for-unreal-engine) — Epic Games, accessed 2026-08-25
- [Lumen Technical Details](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-technical-details-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Virtual Shadow Maps](https://dev.epicgames.com/documentation/en-us/unreal-engine/virtual-shadow-maps-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Temporal Super Resolution](https://dev.epicgames.com/documentation/en-us/unreal-engine/temporal-super-resolution-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Path Tracer](https://dev.epicgames.com/documentation/en-us/unreal-engine/path-tracer-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Physical Lighting Units](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-physical-lighting-units-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Post Process Effects](https://dev.epicgames.com/documentation/en-us/unreal-engine/post-process-effects-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Auto Exposure](https://dev.epicgames.com/documentation/en-us/unreal-engine/auto-exposure-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Color Grading and the Filmic Tonemapper](https://dev.epicgames.com/documentation/en-us/unreal-engine/color-grading-and-the-filmic-tonemapper-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Lightmass Basics](https://dev.epicgames.com/documentation/en-us/unreal-engine/lightmass-basics-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Stat Commands](https://dev.epicgames.com/documentation/en-us/unreal-engine/stat-commands-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Unreal Insights](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-insights-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Rendering High Quality Frames with Movie Render Queue](https://dev.epicgames.com/documentation/en-us/unreal-engine/rendering-high-quality-frames-with-movie-render-queue-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Unreal Engine 5.8 Release Notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes) — Epic Games, accessed 2026-08-25
