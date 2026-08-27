---
id: ue.archviz_workflow
title: Architectural visualisation workflow in Unreal Engine
domain: software_unreal_engine
tags: [archviz, sun-position, sunsky, okongo, namibia, lux, lumens, ev100, interior-lighting, glass, foliage, landscape, cine-camera, sequencer, movie-render-queue, movie-render-graph, vr, configurator]
jurisdiction: namibia
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Unreal Engine 5.8. Movie Render Graph is Production Ready from 5.8; Movie Render Queue preset workflow still supported."
unit_system: metric
sources:
  - {title: "Sun and Sky Actor", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/sun-and-sky-actor-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Physical Lighting Units", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/using-physical-lighting-units-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Rendering High Quality Frames with Movie Render Queue", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/rendering-high-quality-frames-with-movie-render-queue-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Movie Render Pipeline", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/movie-render-pipeline-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
related: [ue.materials_rendering, ue.python_automation, ue.performance, ue.project_setup]
---

# Architectural visualisation workflow in Unreal Engine

**Summary.** This is the operational file: the end-to-end route from a building model to delivered stills, walkthroughs, VR and configurators, biased to a Namibian residential project at **Okongo, Ohangwena Region (≈ 17.4° S, 17.6° E)**. It covers real-world scale, the SunSky Actor configured for that latitude and longitude with the solar geometry that follows from it, physically based light values in lux and lumens, interior lighting, glass, arid-environment landscape and foliage, cinematic cameras, Sequencer and Movie Render Graph output settings.

## Key facts — Okongo sun setup

| SunSky property | Value for Okongo | Note |
|---|---|---|
| Latitude | **-17.4** | South of the equator is negative |
| Longitude | **17.6** | East of Greenwich is positive |
| Time Zone | **+2** | Namibia observes UTC+2 (CAT) year-round |
| Use Daylight Saving Time | **off** | Namibia does not observe DST |
| North Offset | 0 unless the level's +X is not true north | Set it once, at the start |
| Solar Time | float, military time (12.5 = 12:30) | See the note on solar vs clock time below |

Solar geometry that follows from 17.4° S (computed from standard solar-position formulae, not from Epic documentation):

| Date | Solar declination | Max solar altitude | Sun at noon is | Day length | Sunrise / sunset azimuth |
|---|---|---|---|---|---|
| 21 June (winter solstice) | +23.44° | **49.2°** | due **north** | ≈ 10 h 58 m | ≈ 65° / 295° (ENE / WNW) |
| ~21 March, ~23 September (equinox) | 0° | **72.6°** | due **north** | 12 h 00 m | 90° / 270° (due E / W) |
| ~8 November and ~1 February | -17.4° | **90.0°** | directly overhead | — | — |
| 21 December (summer solstice) | -23.44° | **84.0°** | due **south** | ≈ 13 h 03 m | ≈ 115° / 245° (ESE / WSW) |

- **Solar noon at Okongo occurs at about 12:50 local clock time**, not 12:00. The standard meridian for UTC+2 is 30° E; Okongo at 17.6° E is 12.4° west of it, which is 49.6 minutes of solar lag, plus or minus the equation of time (roughly ±16 minutes over the year).
- **Between about 8 November and 1 February the noon sun is to the SOUTH.** For the rest of the year it is to the north. Any shading design or shadow study that assumes "shade the north face" is wrong for a quarter of the year — including the hottest quarter.
- The sun is very high for most of the year. Horizontal overhangs work; vertical fins matter mainly for the low early-morning and late-afternoon east and west sun, which is where the real overheating load is.

> ⚠️ Verify the latitude, longitude, time zone and DST setting against the project's actual site coordinates before producing any shadow study a client will rely on. The values above are for the town of Okongo at the coordinates given in the brief; a specific erf may differ enough to matter for a tight site. Solar-geometry numbers here are computed, not measured.

## Key facts — physical lighting units

| Light type | Unit | Notes |
|---|---|---|
| Directional Light (sun) | **Lux (lx)** — Direct Normal Illuminance | Light on a surface perpendicular to the sun's rays |
| Sky Light | **cd/m²** (luminance) | Pixel intensity × light intensity |
| Emissive materials | **cd/m²** | Pixel luminance before lighting is added |
| Point / Spot / Rect Light | **Candela (cd)**, **Lumen (lm)** or Unitless | Selectable per light; requires Inverse Squared Falloff |
| Exposure | **EV100 (ISO 100)** | Post Process Volume > Lens > Exposure |

Unit relationships, exactly as Epic states them:

- 1 cd = 625 unitless
- 1 cd = 1 lm/sr
- A light set to **1000 cd measures 1000 lux at one metre**
- **Point light** (solid angle 4π sr): Illuminance(1 lm) ≈ 49.7 × Illuminance(1 unitless); Illuminance(1 cd) ≈ 12.6 × Illuminance(1 lm)
- **Spot light** (solid angle 2π(1 − cos θ), θ = cone half-angle): Illuminance(1 lm) ≈ 99.5 / (1 − cos θ) × Illuminance(1 unitless). For the default θ = 44° (solid angle ≈ 1.76 sr): Illuminance(1 lm) ≈ 354 × unitless, and Illuminance(1 cd) ≈ 1.76 × Illuminance(1 lm)
- **Rect light** (solid angle 2π sr): Illuminance(1 lm) ≈ 199 × unitless; Illuminance(1 cd) ≈ 3.14 × Illuminance(1 lm)
- Candela intensity is **unaffected by cone angle**; lumen intensity applies only to the solid angle the light covers, so narrowing a spot's cone makes a lumen-defined light brighter on the surface.

Set the project default in `Project Settings > Rendering > Default Settings > Light Units`. Keep a light's unit consistent with the light it was instanced from — changing units on an already-instanced light breaks default-value propagation.

## Step 1 — Units and real-world scale

Unreal's world unit is **1 uu = 1 cm**. Confirm on arrival, not later:

- Place a `SM_Cube` (default 100 uu) next to a door opening. A 900 × 2 100 mm door should read 90 × 210 uu.
- Set the viewport grid snap to 10 uu (100 mm) for placement, 1 uu for fine work.
- In `Editor Preferences > Appearance > Units`, set the display unit for distance to **Centimeters** or **Meters** so the details panel is legible to an architect.
- Set the CineCamera's **Filmback** before judging any framing — a 35 mm lens means nothing until the sensor size is fixed.
- Human eye height: place a `PlayerStart` or a camera at **Z = 160** (1 600 mm) for a standing adult, **Z = 120** for seated. Every interior composition should be checked at 1 600 mm before it is checked from a drone position.

## Step 2 — Import the building

Follow file `02`. In summary: Datasmith from Revit / Archicad / Rhino / SketchUp / 3ds Max, or IFC/STEP through the CAD importer. Then, in order:

1. Batch-enable Nanite on architectural meshes. **Exclude glass and any translucent element** — Nanite supports Opaque and Masked only.
2. Delete imported cameras and lights you will not use. Datasmith brings in the source application's lights, which are almost never correct.
3. Fix pivots on anything you intend to instance or animate.
4. Replace imported materials with your own instances, driven by Datasmith metadata or name pattern (file `06`).
5. Add collision to anything the visitor can walk into — simple box or convex collision, not per-triangle.

## Step 3 — Sun and sky

Enable **Sun Position Calculator** (`Edit > Plugins`, Misc category), restart, then drag **Sun and Sky** from the *Place Actors* panel, Lights tab, into the level. Remove any existing Directional Light, Sky Light or SkyAtmosphere first — or start from a Blank level.

The SunSky Actor is a Blueprint bundling a movable Directional Light, Sky Light and SkyAtmosphere, driven by geographically accurate sun-position equations. Its exposed properties are Latitude, Longitude, Time Zone, North Offset, Month, Day, DST settings, and Solar Time.

If the SunSky appears blinding white on placement, either enable `Project Settings > Rendering > Default > Extend default luminance range in Auto Exposure settings` (the documented fix, and the right one) or lower the Directional Light's Lux intensity.

**A caution about the Solar Time field.** The property is labelled *Solar Time* and takes a float in military time. Whether the plugin interprets it as true solar time or as local clock time (applying the Time Zone and longitude correction internally) determines whether you type 12.5 or 12.83 for "half past twelve on the clock". Verify empirically once, on your project, by setting a known date and comparing the sun azimuth against an independent solar calculator — then write the answer into the project's own notes. This is flagged as **needs verification**.

Add to the sun rig:

- **Exponential Height Fog** with *Volumetric Fog* on. In an arid landscape keep Fog Density very low (0.005–0.02) — the Ohangwena atmosphere is clear, and heavy fog reads as European.
- **Volumetric Clouds** if the sky is in shot. Sparse cumulus for the wet season (roughly November to April), near-cloudless for the dry season.
- **Sky Light** set to *Real Time Capture* so it follows the SkyAtmosphere as the sun moves.
- A **Post Process Volume**, unbound, with **Manual** exposure.

### Reference sun and sky values

| Condition | Directional Light (lux) | Sky Light (cd/m²) | Manual exposure EV100 |
|---|---|---|---|
| Clear sky, high sun (Okongo midday) | 100 000 – 120 000 | 3 000 – 10 000 | 14 – 15 |
| Clear sky, mid-morning / mid-afternoon | 60 000 – 90 000 | 3 000 – 6 000 | 13 – 14 |
| Golden hour | 5 000 – 20 000 | 1 000 – 3 000 | 10 – 12 |
| Overcast | 1 000 – 20 000 | 2 000 – 5 000 | 11 – 13 |
| Interior, daylit, away from window | — | — | 8 – 11 |
| Interior, artificial light only | — | — | 5 – 8 |

These are working starting points from photometric practice, not Epic-published figures. Set the light first, then the exposure, then judge.

## Step 4 — Interior lighting

Under Lumen you light an interior the way an electrical engineer specifies it, not the way a game artist fakes it.

- **Downlights:** Spot Light, Intensity Units = **Lumen**, 600–1 200 lm each for a domestic LED downlight, outer cone 30–45°, inner cone about two-thirds of outer. IES profile assigned in the light's *Light Profiles > IES Texture* slot. Attenuation radius generous — it is a clamp, not a falloff.
- **Pendants / table lamps:** Point Light, 400–800 lm, with the visible bulb geometry given an **emissive material in cd/m²** so it reads as a source in reflections.
- **Cove / LED strip:** Rect Light, Lumen units, with Source Width/Height matching the real fitting, or an emissive strip mesh (cheaper, softer, no shadow control).
- **Window "fill" lights are wrong under Lumen.** Lumen solves sky lighting with sky shadowing; adding a fake rect light in the window aperture double-counts and flattens the result. If the interior is too dark, raise *Diffuse Color Boost* (keep below 2) or *Skylight Leaking*, or fix the exposure.
- **Target illuminance** (from lighting practice, cross-check against the codes domain): domestic living 100–300 lx, kitchen worktop 300–500 lx, study/desk 300–500 lx, circulation 100 lx, bathroom 150–300 lx.
- Set Mobility to **Movable** for all lights under Lumen. Static mobility is not supported by Lumen.
- Watch VSM cost: many *moving* local lights invalidate shadow pages. Static-in-space movable lights cache well.

## Step 5 — Glass and material realism

Glass is where amateur archviz is exposed.

- Blend Mode **Translucent**, Lighting Mode **Surface Translucency Volume** or **Surface ForwardShading** for refraction and proper specular.
- **Never Nanite.**
- Base Colour near white, Metallic 0, Specular 0.5, Roughness 0.0–0.05, Opacity ~0.05–0.12 for clear glazing, IOR 1.52 in the Refraction input.
- Give glazing **real thickness** — two surfaces, 6 mm apart for single glazing, or model the actual IGU. Single-plane glass never looks right in reflections.
- Add a subtle roughness/normal variation map. Perfectly flat glass reads as CG; real float glass has slight roll-wave distortion.
- Enable *High Quality Translucency Reflections* in the Post Process Volume for mirror reflections on the front layer.
- For a Namibian project, consider the **specification reality**: solar-control coated glass has a visible tint and a distinctly higher external reflectance. If the spec calls for it, model it — a grey or blue-green tint at 0.6–0.7 visible transmittance and a raised specular.

Other realism levers, in order of return on effort:

1. **Roughness variation.** Nothing in a real building has uniform roughness. Break it with a subtle grunge map at low contrast.
2. **Edge wear and dirt** in the correct places — wall bases, door handles, sills, the underside of overhangs where dust collects. In a dusty inland site this is not optional.
3. **Correct tiling scale.** A brick texture must produce bricks of the right size. Measure it.
4. **Bevelled edges.** Sharp 90° corners catch no highlight. Chamfer or use a bevel normal.
5. **Decals** for staining, tyre marks, splashes — cheap and enormously effective. Ordinary projected decals work on Nanite.

## Step 6 — Landscape and foliage for an arid Namibian site

**Landscape.** Use the Landscape tool with a real terrain source where possible: a DEM from an SRTM/Copernicus tile, or survey contours, imported as a 16-bit heightmap (`Landscape > Manage > Import from File`). Ohangwena is very flat — a few metres of relief over a kilometre — so exaggerating terrain is a lie the client will notice on site.

A landscape material for this region wants layers for: red-brown Kalahari sand, compacted earth/track, sparse dry grass, and a wet-season green variant. Use **Runtime Virtual Textures (RVT)** to blend the landscape material into the ground plane under buildings, paths and foliage — it removes the seam that otherwise gives away every archviz exterior.

**Foliage.** The realistic vegetation palette for Ohangwena, which reads as *this place* rather than generic savanna:

- **Makalani palm** (*Hyphaene petersiana*) — the signature tree of the Cuvelai/Ohangwena floodplain
- **Marula** (*Sclerocarya birrea*) — large, spreading, culturally significant
- **Mopane** (*Colophospermum mopane*) — dominant woodland species
- **Camel thorn / acacia** species — fine bipinnate foliage, hard to fake
- Sparse tufted grass, mostly straw-coloured outside the November–April rains
- **Omahangu** (pearl millet) plots if the site sits within cultivated land

Practical notes: Fab/Megascans has good generic savanna and desert scatter but few Namibian species; expect to modify. Two-Sided Foliage shading model with Subsurface Color set to a warm green gives the correct backlit leaf. Use the **Foliage** editor mode for scatter (it produces HISM components automatically) or PCG for rule-based distribution. Keep foliage **out of Nanite's WPO trap** — clamp wind displacement, or accept the cluster-culling cost.

Bias the whole palette dry. The instinct to green a scene is strong and wrong here: the ground is red-brown, grass is straw, trees are sparse and open-canopied, shadows are hard, and the light is very bright and slightly warm.

## Step 7 — Cameras

Use **Cine Camera Actor**, never the basic Camera Actor. Its properties are the ones an architectural photographer thinks in:

- **Filmback:** 16:9 Digital Film, or a custom sensor. Set this first.
- **Focal length:** 24 mm for interiors (28 mm if the room allows), 35–50 mm for exterior three-quarter views, 85 mm+ for detail shots. Avoid anything below 20 mm — the distortion is what makes a render look like an estate-agent photo.
- **Aperture (f-stop):** f/8–f/11 for architecture. Shallow depth of field on a building reads as a mistake; save it for interior detail stills.
- **Focus:** Manual, with *Draw Debug Focus Plane* on while setting it. Tracking focus for moving shots.
- **Keep the camera level.** Two-point perspective — verticals vertical — is the architectural convention. Zero the camera's pitch and use a shift instead: raise or lower the camera, or apply an off-centre projection. A pitched camera converging verticals is instantly recognisable as amateur.

Camera rig actors: **Camera Rig Rail** for tracked moves along a spline, **Camera Rig Crane** for boom moves.

## Step 8 — Sequencer

`Cinematics > Add Level Sequence`, or `Window > Cinematics`. Structure a project as a **master sequence** containing **shot** subsequences, each with its own camera — the pattern the ArchViz template's `archviz_cine_MASTER` demonstrates. Access an existing master from the Level Editor's **Cinematics** dropdown.

Tracks you will actually use:

- **Camera Cuts** track — which camera is live when
- **Transform** track on the camera or rig rail
- **Cine Camera Component** track for focal length, aperture, focus distance
- **SunSky** track — keyframe *Solar Time* for a time-of-day study; keyframe *Month*/*Day* for a seasonal study
- **Light** tracks for intensity and colour
- **Material parameter collection** tracks for finish changes
- **Visibility** tracks for construction sequencing — this is how you show a build phased over time
- **Fade** track

Set the sequence frame rate at creation (24 fps for a cinematic feel, 25 fps for PAL-region broadcast, 30 fps for web). Changing it later resamples keys.

`Perspective > Cinematic Viewport` in the Level Editor gives playback controls and shot information in the viewport.

**Construction simulation** is a Sequencer problem, not a special feature: put each construction stage's geometry in a Data Layer or a Level Instance, and keyframe visibility on a timeline against the programme dates. Add a burn-in showing the date.

## Step 9 — Movie Render Graph / Movie Render Queue output

Enable the **Movie Render Pipeline** plugin (`Edit > Plugins`, Built-In, search "movie"). Open `Window > Cinematics > Movie Render Queue`. Click **+ Render** and pick the Level Sequence.

**In UE 5.8, Movie Render Graph is Production Ready and is where new features are going.** Preset-based configurations still work. Author new pipelines on the graph; keep legacy presets for existing projects.

### Settings that produce a final-quality frame

Epic's own high-quality guide, on the ArchViz Interior sample, uses:

**Anti-aliasing**
- Spatial Sample Count: **1**
- Temporal Sample Count: **64**
- Override Anti Aliasing Mode: **Enabled**
- Anti Aliasing Method: **None**
- Render Warm Up Count: **120**
- Engine Warm Up Count: **120**

Spatial samples render the same instant from slightly offset camera positions; temporal samples slice the shutter-open time into sub-frames and interpolate with engine motion blur. Use temporal samples for motion blur quality on moving shots; spatial samples for still frames where nothing moves. The warm-up counts give auto-exposure, Lumen's temporal accumulation and TSR history time to settle before the first frame is captured — **without them your first frames will be visibly noisier and differently exposed**.

**Console Variables** (the same guide's list — these apply only to the queued render and do not change the level):

```
r.MotionBlurQuality                        4
r.MotionBlurSeparable                      1
r.DepthOfFieldQuality                      4
r.BloomQuality                             5
r.Tonemapper.Quality                       5
r.RayTracing.GlobalIllumination            1
r.RayTracing.GlobalIllumination.MaxBounces 2
r.RayTracing.Reflections.MaxRoughness      1
r.RayTracing.Reflections.MaxBounces        2
r.RayTracing.Reflections.Shadows           2
```

`r.RayTracing.GlobalIllumination 1` is brute force — accurate, multiple bounces, expensive. Value `2` is a temporal-history / final-gather method: much faster, single bounce, some ghosting. Query any variable's help with `r.RayTracing.GlobalIllumination ?` in the console; the result prints to the Output Log (`Window > Developer Tools > Output Log`).

**Output formats**

| Format | Alpha | Compression | Use |
|---|---|---|---|
| `.exr` 16-bit | Yes | Lossless | **Default for archviz stills and comps.** HDR, gradeable |
| `.png` 8-bit | Yes | Lossless | Good quality, no HDR headroom |
| `.jpg` 8-bit | No | Lossy | Previews only |
| `.bmp` 8-bit | No | Lossless | Fast to write, huge |
| `.wav` | — | — | Audio |

For alpha output you must first enable `Edit > Project Settings > Engine > Rendering > Postprocessing > Enable alpha channel support in post processing (experimental) > Linear color space only`, restart, and hide opaque background elements (Sky, atmospheric fog).

**Other settings blocks:** Burn In (scene/shot/date/frame overlay — useful for client review copies, remove for final), Camera (shutter settings governing motion blur and exposure), Game Overrides (Game Mode, Cinematic quality — suppresses UI and loading screens), **High Resolution** (tiled rendering to exceed GPU texture-size and memory limits — this is how you output a 12 000 px print image), Deferred Rendering (the actual frame render), UI Renderer (non-composited UMG to a separate file).

**Windows TDR.** Long GPU commands cause Windows to reset the driver and close the engine. Epic's documented fix is to raise `TdrDelay` at `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\GraphicsDrivers` to decimal **60** seconds. Do this before attempting a heavy render. Requires admin rights.

### Command-line rendering

Three modes are supported. Single sequence plus a config preset:

```
UnrealEditor-Cmd.exe "D:\Okongo\Okongo.uproject" L_Main -game ^
  -LevelSequence="/Game/Cinematics/LS_Okongo_Master.LS_Okongo_Master" ^
  -MoviePipelineConfig="/Game/Cinematics/Presets/Final_EXR.Final_EXR" ^
  -windowed -resx=1920 -resy=1080 -log -notexturestreaming
```

A whole saved queue asset:

```
UnrealEditor-Cmd.exe "D:\Okongo\Okongo.uproject" L_Main -game ^
  -MoviePipelineConfig="/Game/Cinematics/Presets/Q_AllShots.Q_AllShots" ^
  -windowed -resx=1920 -resy=1080 -log -notexturestreaming
```

Or a custom Python executor for full control:

```
-MoviePipelineLocalExecutorClass=/Script/MovieRenderPipelineCore.MoviePipelinePythonHostExecutor
-ExecutorPythonClass=/Engine/PythonTypes.MyCustomExecutor
```

Note Epic's architectural point: **the smallest distributable unit of render work in Unreal is one camera cut (one shot), not one frame**, because real-time features depend on the previous frame's state. Split a render farm by shot.

## Deliverables

**Stills.** Set up a dedicated `LS_Stills` sequence with one frame per camera, or use the *Render Multiple Camera Angle Stills* workflow. Output 16-bit EXR at 2× the delivery resolution, grade in Photoshop/Affinity/DaVinci, deliver as sRGB JPEG or TIFF.

**Walkthrough video.** 24 or 25 fps, 1920 × 1080 or 3840 × 2160, EXR sequence → colour grade → H.264/H.265. Keep camera moves slow and level; architecture reads badly at speed.

**Real-time walkthrough (packaged).** Character or DefaultPawn, collision on everything, a simple UI with a level/room selector, exposure locked to Manual per zone via multiple Post Process Volumes. Ship as a Shipping build. See file `08` for the performance budget.

**VR.** OpenXR plugin, VR template pawn, teleport locomotion (continuous locomotion causes nausea and clients will not tell you). **Nanite does not support stereo rendering**, and Lumen in stereo is expensive — for VR, plan on non-Nanite meshes, baked Lightmass lighting, forward rendering with MSAA, and a 90 fps budget. This is a genuinely different build of the same project, not a checkbox.

**Interactive configurator.** Use the **Product Configurator** template or the **Variant Manager**. The pattern: a Data Table of options → a UMG panel → a Blueprint that swaps Material Instances (or `SetMaterial` on named slots) and toggles Actor visibility. See file `05`. Delivered as a packaged desktop application, or via **Pixel Streaming** if the client must open it in a browser.

**Collaborative review.** The **Collab Viewer** template plus **Datasmith Direct Link** lets the architect change the Revit model and push it live into a session the client is standing in.

## Open questions

- Whether SunSky's *Solar Time* field expects true solar time or local clock time — **needs verification** by empirical test on the project.
- Namibia's abolition of daylight saving time (and therefore permanent UTC+2) should be cross-checked against domain `18_namibia_context` — **needs verification** here.
- Rainfall seasonality for Ohangwena (November–April) is stated from general climate knowledge; cross-check against domain `18`.
- Plant species list is from regional botany, not from a verified source in this session — cross-check against domain `18`.
- Reference lux/EV tables are photometric practice, not Epic-published values.

## Sources

- [Sun and Sky Actor](https://dev.epicgames.com/documentation/en-us/unreal-engine/sun-and-sky-actor-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Physical Lighting Units](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-physical-lighting-units-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Rendering High Quality Frames with Movie Render Queue](https://dev.epicgames.com/documentation/en-us/unreal-engine/rendering-high-quality-frames-with-movie-render-queue-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Movie Render Pipeline](https://dev.epicgames.com/documentation/en-us/unreal-engine/movie-render-pipeline-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Using Command Line Rendering with Movie Render Queue](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-command-line-rendering-with-move-render-queue-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Cinematics and Movie Making](https://dev.epicgames.com/documentation/en-us/unreal-engine/cinematics-and-movie-making-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Cinematic Cameras](https://dev.epicgames.com/documentation/en-us/unreal-engine/cinematic-cameras-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Lumen Global Illumination and Reflections](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Nanite Virtualized Geometry](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Foliage Mode](https://dev.epicgames.com/documentation/en-us/unreal-engine/foliage-mode-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Landscape Outdoor Terrain](https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-outdoor-terrain-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Product Configurator Template](https://dev.epicgames.com/documentation/en-us/unreal-engine/product-configurator-template-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Collab Viewer Templates](https://dev.epicgames.com/documentation/en-us/unreal-engine/collab-viewer-templates-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Unreal Engine 5.8 Release Notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes) — Epic Games, accessed 2026-08-25
