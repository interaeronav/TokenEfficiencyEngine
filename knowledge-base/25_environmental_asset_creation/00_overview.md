---
id: envasset.overview
title: Environmental asset creation — domain overview
domain: 25_environmental_asset_creation
tags: [environment-art, photorealism, unreal-engine, blender, fusion, pipeline, asset-creation, namibia, overview, domain-map]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Unreal Engine 5.8, Blender 5.2 LTS, Autodesk Fusion (May 2026 release). Verified 2026-08-25."
unit_system: SI
sources:
  - {title: "Unreal Engine 5.8 Documentation", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-documentation", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Nanite Virtualized Geometry", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Landscape Technical Guide", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-technical-guide-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Runtime Virtual Texturing", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/runtime-virtual-texturing-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Blender Manual — Sky Texture Node", url: "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/sky.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Quixel — licensing and Fab transition", url: "https://quixel.com/pricing", publisher: "Quixel / Epic Games", accessed: 2026-08-25}
related: [envasset.principles, envasset.reference_scanning, envasset.terrain, envasset.vegetation, envasset.rocks_surfaces, envasset.water_sky, envasset.hardsurface_fusion, envasset.pipeline, envasset.lookdev, envasset.libraries, envasset.learning, ue.overview, blender.overview, fusion.overview, namibia.overview]
---

# Environmental asset creation — domain overview

**Summary.** This domain covers making environmental assets that read as *real* — terrain, vegetation, rock, ground surfaces, water, sky and the hard-surface objects that sit on them — across Blender, Unreal Engine and Autodesk Fusion. Its organising principle is a single question applied to every decision: **what actually makes this read as real, and what is the tell that makes it read as CG?** The target case throughout is a residential project in the dry sandveld of Ohangwena, northern Namibia — a flat, sandy, sparsely wooded landscape with brutal overhead sun, which is a much harder photoreal target than the mountains and forests that most tutorials assume. The division of labour is: **Blender authors and procedurally generates**, **Unreal assembles, lights and renders in real time**, **Fusion produces anything that will be manufactured**.

## Key facts

| Item | Value |
|---|---|
| Primary authoring app | Blender 5.2 LTS |
| Primary assembly and render app | Unreal Engine 5.8 |
| Fabricable/mechanical CAD | Autodesk Fusion (May 2026 release) |
| Interchange formats used here | FBX (mesh + LOD), glTF 2.0 (interchange/web), USD/USDZ (scene backbone), STEP AP242 (CAD), OpenEXR (HDR), 16-bit PNG / R16 (heightmaps) |
| Unreal landscape heightmap formats | 16-bit greyscale PNG, 16-bit greyscale `.r16`, 8-bit `.r8`, or `.raw` + JSON sidecar |
| Unreal landscape Z-scale constant | `0.001953125` (= 1/512) × desired height in cm |
| Largest recommended Unreal landscape | 8129 × 8129 vertices, 127 quads/section, 2×2 sections/component, 1024 components (32 × 32) |
| Free CC0 texture/HDRI sources | Poly Haven, ambientCG |
| Site latitude driving all sun work | **17.57°S**, ~1 150 m elevation (Okongo, Ohangwena) |
| Site texture family | Kalahari aeolian quartz sand (Arenosol), calcrete, no surface stone |

> ⚠️ Photorealism is not a rendering setting. Every "make it photoreal" checkbox in every engine is downstream of three things you control before you open the software: **observed reference**, **correct real-world scale**, and **physically correct light**. A path tracer will render an unconvincing scene with perfect physical accuracy.

## The realism-first philosophy

Most environment work fails for a small, repeatable set of reasons. This domain is structured around eliminating them, not around teaching menus.

**1. The scene was invented, not observed.** Artists build what they think a Namibian yard looks like. The sand is too orange, the grass is too green, the trees are too round, the shadows are too soft. The fix is not a better shader — it is a reference board assembled *before* modelling, ideally from photographs taken on the actual site. See `01` and `02`.

**2. The scale is wrong.** A 2.2 m door, a 350 mm grass blade, a 90 mm brick — get any of these wrong and every lighting and depth-of-field cue lies. Humans read scale from thousands of learned relationships. See `01 §Scale` and `08 §Units`.

**3. Everything is too clean and too uniform.** Real surfaces carry history: sun bleaching on the north face, dust drifted against the windward side of a wall, water staining under a drip, edge wear on a gate latch, biological growth in shade. CG surfaces are uniform because uniform is the default. See `01 §Surface history` and `05`.

**4. It tiles.** Repetition is the single loudest CG tell in an exterior. A 4 m sand texture on a 40 m yard repeats ten times and the eye finds the pattern in under a second. See `01 §Tiling` and `05 §Breaking repetition`.

**5. The light is not physical.** Wrong sun intensity, wrong sky-to-sun ratio, wrong bounce colour, no atmospheric perspective, a tonemapper doing something arbitrary. See `06` and `09`.

**6. The camera is perfect.** Real photographs have lens falloff, slight chromatic aberration, sensor noise, imperfect focus and a real exposure. Perfectly clean CG frames read as CG. See `01 §Camera realism` and `09`.

Each of the nine content files below is written to attack one or more of these.

## Division of labour between the three applications

### Blender — authoring and procedural generation

Blender is where *individual assets are made and where procedural systems live*. Use it for:

- **Organic modelling and sculpting** — rocks, termite mounds, tree trunks, eroded calcrete edges, dirt berms.
- **Geometry Nodes procedural systems** — scattering, wear generation, plank/paling distribution for a palisade, branch instancing, erosion-driven displacement.
- **Retopology and UV work** — including cleaning up photogrammetry scans and CAD-derived meshes from Fusion.
- **Baking** — high-to-low normal, AO, curvature, position and thickness maps.
- **Procedural material authoring** as the free alternative to Substance Designer (see `05`).
- **Offline reference renders in Cycles** — a physically accurate ground truth to match the Unreal real-time render against (`09`).
- **Batch export automation** via `bpy` (`08`).

Blender's weakness for this domain is scene *assembly at landscape scale*: it has no streaming world partition, its viewport degrades badly past a few million instanced polygons without careful use of the Texture Cache and linked libraries, and its foliage LOD story is manual.

### Unreal Engine — assembly, lighting, real-time render

Unreal is where the *world is built and looked at*. Use it for:

- **Landscape** — the heightmap terrain system, layer-blended materials, spline roads and tracks (`03`).
- **Foliage** — the Foliage tool, Procedural Foliage Volumes, Nanite foliage, wind (`04`).
- **Nanite** — removes the polygon budget conversation for static geometry; supports Opaque and Masked blend modes, and Nanite Foliage exists as a dedicated system.
- **Lumen** — dynamic global illumination and reflections without a bake, which is what makes an unbaked exterior with a moving sun viable.
- **Sky Atmosphere, Volumetric Cloud, Exponential Height Fog** — the atmospheric systems (`06`).
- **Runtime Virtual Texturing** — the standard technique for blending meshes into terrain so rocks and plinths do not read as pasted-on (`03`, `05`).
- **World Partition** — streaming for a site larger than a plot.
- **Movie Render Graph** — final stills and animation output.

Unreal's weakness is *authoring*. Its modelling tools have improved but are not a substitute for Blender, and its material editor, while powerful, is not a procedural texture generator in the Substance Designer sense.

### Autodesk Fusion — hard surface and fabricable objects

Fusion is where *anything that will be manufactured* is designed. Use it for:

- Steel entrance gates, burglar bars, palisade brackets, balustrades, pergola connections, gutter brackets, solar-panel frames, water-tank stands.
- Furniture and joinery that will be cut on a CNC (see domain `15` and domain `06_joinery_and_woodwork`).
- Anything where a **dimension is a contract** — a bolt hole pattern, a hinge centre, a section size that must match stock.

The key insight is that Fusion's output is *the same geometry the fabricator will build from*. A gate modelled in Blender "to look right" and a gate modelled in Fusion "to be built" are different objects; only the second one gives you a visualisation that is honest. See `07`.

Fusion's weakness is that its output is NURBS-derived tessellation, not artist-controlled topology — dense, badly distributed triangles with no useful UVs. `07` is largely about fixing that.

## The pipeline, end to end

```
                 REFERENCE (02)
   site photos · HDRI capture · photogrammetry · satellite/drone · DEM
                        │
        ┌───────────────┼────────────────┬─────────────────┐
        ▼               ▼                ▼                 ▼
   TERRAIN (03)   VEGETATION (04)   SURFACES (05)   HARD SURFACE (07)
   DEM → Gaea/      SpeedTree /     Substance /      Fusion parametric
   World Creator/   Blender trees   Blender procedural   model
   Blender ANT      + atlases       + scans
        │               │                │                 │
        │               └────────┬───────┘                 │
        │                        ▼                         ▼
        │              BLENDER — author, retopo, UV, bake, LOD
        │                        │                         │
        └────────────────────────┼─────────────────────────┘
                                 ▼
                    PIPELINE + STANDARDS (08)
        naming · texel density · LODs · collision · USD/glTF/FBX
                                 ▼
                      UNREAL ENGINE — assemble
        Landscape · Foliage · RVT · Nanite · Lumen · Water (06)
                                 ▼
                     LOOK DEV + LIGHTING (09)
          real lux values · ACES/AgX · exposure · grade
                                 ▼
                  Movie Render Graph → stills / sequence
```

The loop that matters is the one that is not drawn: **compare against reference, at every stage**. `09` describes the reference-matching workflow that closes it.

## The Ohangwena case specifically

This landscape breaks most default assumptions in environment art:

| Generic tutorial assumption | Ohangwena reality | Consequence |
|---|---|---|
| Interesting terrain relief | Regional relief is **metres over tens of kilometres** | Terrain sculpting is nearly irrelevant; ground *material* and *vegetation* carry the whole image |
| Rock outcrops and boulders | **No surface stone at all**; calcrete nodules at most | Rock assets are near-useless; anthropogenic objects supply the hard shapes |
| Rich green vegetation | Broadleaved dry woodland; **8 months of straw-coloured grass** | Green must be reserved and specific; the default foliage palette is wrong |
| Overcast/soft key light | ~2 275 kWh/m²/yr GHI, sun to **84° altitude** in December | Shadows are short, hard and near-vertical for much of the year |
| Moderate sky/sun ratio | Very clear dry-season sky, deep blue, low haze | Sun/sky contrast is extreme; bounce off pale sand is the fill light |
| Soil is brown loam | Kalahari **quartz sand**, pale, with iron staining | Albedo is *high* and *desaturated*, not orange |

The two most load-bearing assets in this project are therefore (a) the **ground material** — a sand that catches raking light correctly, drifts against objects, and does not tile — and (b) the **trees** — a small number of specific, correct, asymmetric species. Everything else is supporting cast. Files `04` and `05` are correspondingly the longest.

## Domain map

| File | Covers | Read it when |
|---|---|---|
| `01_principles-of-photoreal-environments.md` | Why things read as real: reference, scale, light physics, material response, surface history, tiling, atmosphere, camera | Before anything else, and again whenever a shot "looks CG" and you cannot say why |
| `02_reference-and-scanning.md` | Photographic reference discipline, photogrammetry, LiDAR/phone scanning, HDRI capture, satellite/drone source, licensing of scans | Planning a site visit, or converting captured data to assets |
| `03_terrain-and-landscape.md` | DEM → heightmap maths, Gaea/World Creator/Blender terrain, erosion, Unreal Landscape and layer materials, RVT, World Partition | Building the ground plane |
| `04_vegetation-and-foliage.md` | Botanical reference for northern Namibia, SpeedTree, Blender tree tools, atlases vs Nanite foliage, LODs, wind, SSS | Building or placing plants |
| `05_rocks-terrain-materials-and-surfaces.md` | Rock modelling, layered ground materials, sand and dust specifically, Substance, texel density, trim sheets | Authoring the surfaces the light lands on |
| `06_water-sky-and-atmosphere.md` | Water shaders, oshana pans, Sky Atmosphere, volumetric cloud, fog, dust haze, heat shimmer, particles, time of day | Building the environmental systems around the site |
| `07_hard-surface-and-fusion-workflow.md` | What Fusion is for, STEP → polygon pipeline, tessellation control, unit handling, worked gate example | Anything manufactured enters the scene |
| `08_asset-pipeline-and-standards.md` | Naming, folders, versioning, budgets, texel density, UVs, pivots, collision, USD, automation code, validation | Setting the project up, or when it starts to sprawl |
| `09_lighting-and-look-development.md` | Physical light units, sun/sky ratios, EV, ACES/AgX, white balance, look-dev spheres, reference matching, grading | Making the render read true |
| `10_asset-libraries-and-sources.md` | Where assets come from, with licence, cost and format | Sourcing rather than building |
| `11_learning-and-references.md` | Artists, breakdown culture, courses, books, channels, a 12-month progression | Getting better on purpose |

## Cross-domain links

- **Domain 13 (Unreal Engine)** — engine fundamentals, licensing, materials and rendering, archviz workflow with Okongo sun angles, Python automation, performance. This domain assumes 13 and does not repeat it.
- **Domain 14 (Blender)** — interface, modelling, Geometry Nodes, materials, lighting/rendering including the Okongo sun-position script, Python API, import/export.
- **Domain 15 (Fusion)** — licensing, sketching, parametric modelling, assemblies, CAM, interoperability. `07` here is the *visualisation* half of Fusion's story; 15 is the *manufacturing* half.
- **Domain 18 (Namibia context)** — the real geography, climate, geology, soils and architecture. `03`, `04`, `05` and `06` here are the visual translation of 18's facts.
- **Domain 23 (Cartography and mapping)** — DEM sourcing and coordinate systems in more depth.
- **Domain 24 (Arid hydrology)** — oshana behaviour, flood extents, the physical basis for `06`'s water work.

## Open questions

- Whether the user's SkyFi imagery licence permits derived 3D assets to be distributed to a client (see `02 §Licensing`). `needs-verification` against the specific SkyFi order terms.
- Exact current Fab licence tier names and revenue thresholds — Fab's legal pages are behind a bot challenge and could not be fetched. See `10`.
- Whether the site has any calcrete surface exposure; this changes the ground-material layer count materially. Requires a site visit.

## Sources

- [Unreal Engine 5.8 Documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-documentation) — Epic Games
- [Landscape Technical Guide in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-technical-guide-in-unreal-engine) — Epic Games
- [Nanite Virtualized Geometry in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine) — Epic Games
- [Runtime Virtual Texturing in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/runtime-virtual-texturing-in-unreal-engine) — Epic Games
- [Landscape Materials in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-materials-in-unreal-engine) — Epic Games
- [Blender Manual — Sky Texture Node](https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/sky.html) — Blender Foundation
- [Quixel — pricing and Fab transition](https://quixel.com/pricing) — Quixel / Epic Games
- [Poly Haven licence](https://polyhaven.com/license) — Poly Haven
- [ambientCG](https://ambientcg.com/) — ambientCG
