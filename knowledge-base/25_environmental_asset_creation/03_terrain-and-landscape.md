---
id: envasset.terrain
title: Terrain and landscape — from DEM to a believable ground plane
domain: 25_environmental_asset_creation
tags: [terrain, landscape, heightmap, dem, srtm, copernicus, gaea, world-creator, erosion, unreal-landscape, layer-blend, runtime-virtual-texture, world-partition, cuvelai, geometry-nodes]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Unreal Engine 5.8, Blender 5.2 LTS, Gaea 2.2, QGIS/GDAL 3.x."
unit_system: SI
sources:
  - {title: "Landscape Technical Guide in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-technical-guide-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Landscape Materials in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-materials-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Runtime Virtual Texturing in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/runtime-virtual-texturing-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Copernicus DEM collection description", url: "https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM", publisher: "European Space Agency / Copernicus Data Space Ecosystem", accessed: 2026-08-25}
  - {title: "Shuttle Radar Topography Mission", url: "https://en.wikipedia.org/wiki/Shuttle_Radar_Topography_Mission", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Gaea editions and pricing", url: "https://quadspinner.com/order", publisher: "QuadSpinner", accessed: 2026-08-25}
  - {title: "Atlas of Namibia — The Cuvelai", url: "https://atlasofnamibia.online/chapter-4/the-cuvelai", publisher: "Atlas of Namibia", accessed: 2026-08-25}
related: [envasset.overview, envasset.rocks_surfaces, envasset.vegetation, envasset.water_sky, namibia.geography, namibia.geology_soils, ue.core_concepts]
---

# Terrain and landscape — from DEM to a believable ground plane

**Summary.** Terrain is where a scene's scale and geology are established, and in a landscape as flat as the eastern Ohangwena sandveld it is also where most CG environment technique becomes irrelevant. There are no mountains to erode and no cliffs to sculpt; regional relief is **metres over tens of kilometres**. What matters instead is: getting the real elevation data in at the right vertical precision, generating *subtle* dune-ridge and interdune structure that is genuinely there, and building a landscape material whose layer blending and macro variation carry the image. This file covers real-world DEM sourcing and the exact heightmap maths for Unreal and Blender, procedural terrain in Gaea and Blender, erosion simulation and why it matters, the Unreal Landscape system and a real layer-blend graph, Runtime Virtual Texturing, World Partition, and the specific character of a Cuvelai-margin landscape.

## Key facts

| Item | Value | Source |
|---|---|---|
| Unreal heightmap formats | 16-bit greyscale **PNG**, 16-bit **`.r16`**, 8-bit **`.r8`**, or `.raw` + JSON sidecar | Epic Landscape Technical Guide |
| Unreal internal height range | **−256 to 255.992** at 16-bit precision | Epic |
| Unreal Z-scale formula | `Z Scale = desired_total_height_cm × 0.001953125` (= /512) | Epic |
| Worked Epic example | Mauna Kea 4 207 m → 420 700 cm × 0.001953125 = **821.68** | Epic |
| Default Landscape scale | 100, 100, 100 → 1 m per quad, ±256 m vertical range | derived from the above |
| Sections per Component | **1 or 4 (2×2)** only | Epic |
| Quads per Section | Powers of two minus one, max 255×255 region (typically **63** or **127**) | Epic |
| Largest recommended landscape | **8129 × 8129 verts**, 127 quads/section, 2×2 sections, 254×254 components, 1024 components (32×32) | Epic |
| SRTM 1-arcsec | ~30 m GSD; tiles 3 601 × 3 601, 16-bit big-endian; coverage 56°S–60°N | Wikipedia |
| Copernicus **GLO-30** | 1.0 arcsec (~30 m), global (~149 M km²), **DSM not DTM** | Copernicus Data Space |
| Copernicus vertical accuracy | **< 4 m absolute (90% LE)**; < 2 m relative on slopes ≤ 20% | Copernicus Data Space |
| Copernicus horizontal accuracy | **< 6 m absolute (90% CE)** | Copernicus Data Space |
| Copernicus source | TanDEM-X acquisitions 2011–2015, gap-filled from ASTER/SRTM/ALOS etc. | Copernicus Data Space |
| Copernicus GLO-30/90 licence | Free for all registered users; **attribution notice required** (see §1.4) | Copernicus Data Space |
| Gaea Community | **Free forever**, build resolution limited to **1024 × 1024** | quadspinner.com/order |
| Gaea Indie / Professional / Enterprise | **US$99 / US$199 / US$299**, perpetual, tiered by revenue (<100 K / <1 M / >1 M) | quadspinner.com/order |

> ⚠️ Copernicus DEM is a **Digital Surface Model** — it includes tree canopy and buildings. In wooded sandveld this systematically raises the "ground" by the canopy height. For a site model, either use it only for regional context, or subtract a canopy estimate, or get a real survey.

---

## 1. Real-world elevation data as the base

### 1.1 Which dataset

| Dataset | GSD | Type | Licence | Use here |
|---|---|---|---|---|
| **Copernicus DEM GLO-30** | 30 m | DSM | Free, attribution required | **First choice** for regional context |
| **Copernicus DEM GLO-90** | 90 m | DSM | Free, attribution required | Very wide context only |
| **SRTM 1-arcsec (SRTM-GL1, v3)** | 30 m | DSM-ish | Public domain | Fallback; older, noisier |
| **ALOS World 3D-30m (AW3D30)** | 30 m | DSM | Free with registration | Cross-check |
| **Drone photogrammetry** | 1–5 cm | DSM → DTM | Yours | **The only useful source at plot scale** |
| **SkyFi DSM analytics** | Varies | DSM | Commercial licence | Site-scale if no drone |
| **Land survey** | mm–cm | DTM | Yours/commissioned | The truth for the building platform |

**For Okongo the honest position is:** a 30 m DEM over a landscape with 10 m of relief across 10 km gives you roughly three usable elevation steps. It will tell you where the interfluve is and where the *oshana* drainage lies — which matters enormously for siting (see domain `18` file `01`) — and it will tell you nothing at all about the ground within 200 m of the house. Use the DEM for context and terrain beyond the plot; use drone photogrammetry or a survey for the plot; use procedural detail to bridge them.

### 1.2 Getting the data and preparing it (GDAL / QGIS)

```bash
# 1. Fetch a Copernicus GLO-30 tile (register on the Copernicus Data Space first).
#    Naming is by 1° geocell; Okongo (17.567 S, 17.217 E) is in S18/E017.

# 2. Reproject to a metric CRS. Namibia: UTM zone 33S = EPSG:32733.
gdalwarp -t_srs EPSG:32733 -r bilinear -tr 30 30 \
         Copernicus_DSM_COG_10_S18_00_E017_00_DEM.tif okongo_utm.tif

# 3. Crop to the area of interest (xmin ymin xmax ymax in EPSG:32733 metres).
gdal_translate -projwin 630000 8060000 638192 8051808 okongo_utm.tif aoi.tif

# 4. Inspect the real elevation range - you need these numbers for the Z scale.
gdalinfo -stats aoi.tif | grep -E "Minimum|Maximum"
#   e.g. Minimum=1142.310, Maximum=1163.870   -> 21.56 m of relief

# 5. Resample to a power-of-two-plus-one grid that Unreal likes.
#    For an 8 km x 8 km area at 1 m per quad you want 8129 x 8129 samples.
gdalwarp -r cubicspline -ts 8129 8129 aoi.tif aoi_8129.tif

# 6. Stretch the real elevation range across the FULL 16-bit range and write PNG.
#    -scale <src_min> <src_max> <dst_min> <dst_max>
gdal_translate -ot UInt16 -of PNG \
               -scale 1142.31 1163.87 0 65535 \
               aoi_8129.tif okongo_heightmap.png
```

**Why stretch to the full range.** A 21.56 m relief stored in the top 0.03% of a 16-bit range would quantise to a handful of levels and produce visible terracing. Stretching to 0–65535 gives 21.56 m / 65 536 = **0.33 mm per level** — far finer than needed, and terracing becomes impossible.

### 1.3 The Unreal import maths, worked

Unreal maps the full 16-bit range onto `−256 → +255.992` *Unreal-internal height units*, then multiplies by the Landscape's Z scale.

```
Z Scale = desired_total_height_in_cm × 0.001953125          (0.001953125 = 1/512)
```

For the Okongo example with 21.56 m of relief stretched to full range:

```
desired_total_height = 21.56 m = 2156 cm
Z Scale = 2156 × 0.001953125 = 4.2109375
```

Enter **4.211** in the Landscape's Scale Z on import. The imported terrain will then have exactly 21.56 m between its lowest and highest point, and the mid-grey value 32768 sits at the landscape actor's Z position.

For XY: at 8129 vertices covering 8 000 m you want **1 m per quad**, which is `Scale X = Scale Y = 100`. If instead you covered 8 000 m with a 4033-vertex landscape you would need `Scale X/Y = 198.4` — but non-round XY scales make placement arithmetic painful, so prefer to resample the DEM to give you a round number.

**Sanity check after import.** Place a 100 × 100 × 100 uu cube on the landscape. Measure a known distance in the viewport against the DEM's real distance. Check the elevation readout at two points against `gdalinfo`.

### 1.4 Attribution

Copernicus GLO-30 imposes a specific notice. Where the data have been adapted or modified — which they always are, once they are a heightmap — the required text is:

> produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved

Put it in the project's `CREDITS.md` and in any published deliverable.

### 1.5 The same data in Blender

```python
# Blender 5.2: import a 16-bit heightmap as a displaced grid.
# Run in the Scripting workspace. Uses the same PNG produced above.
import bpy

W_M   = 8000.0      # real width  in metres
H_M   = 8000.0      # real depth  in metres
RELIEF_M = 21.56    # real elevation range in metres
SUBDIV = 1024       # grid subdivisions per side (keep viewport sane)

bpy.ops.mesh.primitive_grid_add(x_subdivisions=SUBDIV, y_subdivisions=SUBDIV,
                                size=1.0, location=(0, 0, 0))
grid = bpy.context.object
grid.name = "TERRAIN_Okongo"
grid.scale = (W_M / 2.0, H_M / 2.0, 1.0)
bpy.ops.object.transform_apply(scale=True)

img = bpy.data.images.load("//okongo_heightmap.png")
img.colorspace_settings.name = 'Non-Color'      # CRITICAL - never sRGB for height

tex = bpy.data.textures.new("HeightTex", type='IMAGE')
tex.image = img
tex.extension = 'EXTEND'

mod = grid.modifiers.new("Displace", 'DISPLACE')
mod.texture = tex
mod.texture_coords = 'UV'
mod.mid_level = 0.0          # 0 = use full 0..1 range upward
mod.strength = RELIEF_M      # metres, because 1 BU = 1 m
```

Two things that break this and are worth stating: the image **must** be Non-Color (an sRGB transfer curve applied to a heightmap produces a smooth but wrong terrain), and Blender's Displace modifier reads 16-bit PNG correctly only if the image is loaded as 16-bit — check `img.depth` returns 16 or 48.

---

## 2. Procedural terrain

### 2.1 Gaea (QuadSpinner)

Gaea is a node-based, non-destructive terrain generator. **Gaea Community is free forever with a 1024 × 1024 build resolution cap**; Indie is US$99, Professional US$199, Enterprise US$299, all perpetual, tiered by the buyer's revenue (<100 K / <1 M / >1 M). Current released version is 2.2, with 3.0 in development.

The 1024 cap matters: a 1024 heightmap over an 8 km site is 7.8 m per pixel, too coarse for anything but a base layer. For this project the Indie licence at US$99 is the obvious purchase if Gaea is used at all.

**A Gaea graph for a Kalahari sandveld interfluve** (node names as they appear in Gaea's library):

```
Mountain / Perlin (very low Scale, high Octaves)   ← base undulation, amplitude ~8 m
        │
    Warp (small)                                   ← breaks the noise's regularity
        │
    Dunes  (Direction = NW–SE, low height)         ← relict linear dune ridges
        │
    Combine (Blend, ~15%)  ←── Perlin (fine)       ← interdune sand texture
        │
    Erosion2   (Duration low, Rock Softness high)  ← subtle, this is not a mountain
        │
    Thermal / Sediment                             ← fills hollows with fine material
        │
    ├── Export → Height  (Raw16 / PNG16)
    ├── Flow      → Export as FlowMap
    ├── Wear      → Export as ErosionMask
    └── Deposits  → Export as SedimentMask
```

The critical discipline for this landscape is **restraint**. Every Gaea preset is built for mountains. Amplitudes here are 2–10 m, not 2 000 m. Set the terrain's real-world extent in Gaea's Build settings and keep checking the vertical exaggeration.

**The masks are the point.** Gaea's `Flow`, `Wear`, `Deposits` and `Slope`/`Curvature` outputs export as greyscale maps that you import into Unreal as **Landscape layer weight maps** — so the sand deposits where the simulation says sediment settled, and the coarse lag gravel appears where the simulation says fines were removed. That is what makes procedural terrain read as geology rather than as noise.

### 2.2 World Creator

World Creator (BiteTheBytes) is the real-time GPU competitor to Gaea, with a live-sculpting workflow and its own erosion and filter stack. It exports heightmaps, splat/weight maps and meshes, and has direct Unreal integration. `needs-verification`: current version and pricing — world-creator.com's pricing and buy pages returned 404 on 2026-08-25.

### 2.3 Blender

**A.N.T. Landscape** is the classic procedural landscape add-on. Since Blender 4.2's extensions migration it is distributed as an extension (`extensions.blender.org/add-ons/antlandscape/`) rather than a bundled add-on; enable it from Preferences → Get Extensions. It generates a mesh from a choice of noise bases with hydraulic-looking distortion, plus falloff and terracing controls. It is fast and adequate for a base layer; it has no true erosion.

**Geometry Nodes erosion** is achievable but is a real project. The honest summary: Blender's Geometry Nodes can express a grid-based hydraulic erosion loop using the **Repeat Zone** (4.x+) with `Sample Index`/`Sample Nearest` for neighbour lookups, but it is slow and awkward compared with a purpose-built simulator. Blender 5.2's node-based physics with an XPBD solver does not change this. **Recommendation: do erosion in Gaea, do everything else in Blender.**

**Displacement in Blender**, in preference order:
1. **Displace modifier** with a texture (shown in §1.5) — predictable, real geometry, works everywhere.
2. **Adaptive Subdivision** (Cycles, `Subdivision Surface` modifier with *Adaptive Subdivision* on and Dicing Rate ~1.0 px) with a **Displacement** output in the material and `Displacement Method = Displacement Only`. Very high detail with no memory cost until render. Out of experimental as of Blender 5.0.
3. **Bump only** — for anything below ~2 mm of relief.

---

## 3. Erosion, and why it matters even here

Hydraulic erosion (water moving material downslope) and thermal erosion (material sliding when the slope exceeds the angle of repose) are what make natural terrain *look* natural. The reason is that they create **correlated structure**: valleys connect, ridges are sharp where erosion cut them and rounded where deposition filled them, and material is graded — coarse on the steep parts, fine in the hollows. Pure noise has none of this, and the eye reads pure noise as fabric.

**In the Cuvelai the erosion story is unusual and worth getting right.** From domain `18`:

- There are **no rivers in the conventional sense** — only the *iishana* (singular *oshana*), a network of about 100 shallow, grassy, interlinked channels ranging from under ten metres to over a kilometre wide, converging downstream into the Omadhiya lakes.
- Most channel beds are **impermeable clay or saline soil**, so water spreads laterally rather than incising. Channels are **wide and shallow**, not V-shaped.
- Okongo sits on the **deep sandveld east of the main oshana network**, on subdued vegetated dune ridges with interdune flats inherited from earlier arid phases. Aeolian, not fluvial, structure dominates.
- The dominant "erosion" visible at plot scale is therefore **wind**: sand ripples, drift accumulation on the lee of obstacles, and deflation hollows where vegetation is absent.

**Practical translation.**
- Run *light* hydraulic erosion for the broad interfluve/oshana pattern where the site borders a drainage.
- Use **directional (aeolian) structure** for the sandveld: linear ridges aligned NW–SE (the regional Kalahari dune orientation, formed ~28 000 and ~17 000 years ago), heavily smoothed and vegetated.
- Do **not** carve steep gullies or rocky ridges. There is no rock.
- Export the flow/wetness mask anyway — it drives where the grass is greener and where the clay-floored pans are.

---

## 4. Flow maps and erosion masks driving material layers

The output of terrain generation is not one heightmap; it is a heightmap plus a stack of masks. Wire them in as landscape layers:

| Gaea output | Unreal Landscape layer | What it should paint |
|---|---|---|
| `Height` | — (the heightmap itself) | — |
| `Flow` | `Layer_Wet` / `Layer_Clay` | Oshana bed: darker, smoother, cracked clay in the dry season |
| `Deposits` / `Sediment` | `Layer_FineSand` | Interdune flats, hollows — the palest, softest sand |
| `Wear` | `Layer_LagGravel` | Deflated surfaces where fines have blown away, exposing coarse grains and calcrete nodules |
| `Slope` | `Layer_Bare` | Any steeper face (rare here — dune flanks, borrow pits, track cuttings) |
| `Curvature` (concave) | `Layer_Litter` | Where leaf litter and organic material collects |
| Manual paint | `Layer_Yard` | The compacted, swept, vegetation-free ground of a homestead yard — a very characteristic surface |

Import them with `Landscape Mode → Manage → Import`, assigning each greyscale PNG to a named layer. The layer names must match the `Layer Name` fields in the material's `Landscape Layer Blend` node exactly.

---

## 5. Unreal's Landscape system

### 5.1 Components, sections and resolution

A Landscape is a grid of **Components**. Each Component contains 1 or 4 (2×2) **Sections**; each Section is a square of **Quads**. The component is the unit of culling, LOD and rendering — so component count drives draw calls, and section count drives LOD granularity.

Epic's recommended sizes:

| Overall size (vertices) | Quads/Section | Sections/Component | Component size | Total components |
|---|---|---|---|---|
| 8129 × 8129 | 127 | 4 (2×2) | 254 × 254 | 1024 (32 × 32) |
| 4033 × 4033 | 63 | 4 (2×2) | 126 × 126 | 1024 (32 × 32) |
| 2017 × 2017 | 63 | 4 (2×2) | 126 × 126 | 256 (16 × 16) |
| 1009 × 1009 | 63 | 4 (2×2) | 126 × 126 | 64 (8 × 8) |
| 1009 × 1009 | 63 | 1 | 63 × 63 | 256 (16 × 16) |
| 505 × 505 | 63 | 4 (2×2) | 126 × 126 | 16 (4 × 4) |
| 505 × 505 | 63 | 1 | 63 × 63 | 64 (8 × 8) |
| 253 × 253 | 63 | 4 (2×2) | 126 × 126 | 4 (2 × 2) |
| 253 × 253 | 63 | 1 | 63 × 63 | 16 (4 × 4) |
| 127 × 127 | 63 | 4 (2×2) | 126 × 126 | 1 |
| 127 × 127 | 63 | 1 | 63 × 63 | 4 (2 × 2) |

Sections per Component may only be **1 or 4 (2×2)**. Quads per Section are powers of two (63, 127, …) up to a 255 × 255 region.

**Choosing for this project.** A residential plot with 200–400 m of visible surroundings does not need 8129². Use:

- **1009 × 1009 with 63 quads, 2×2 sections (64 components)** at `Scale XY = 50` → 1 008 × 50 cm = **504 m square at 0.5 m per quad**. This gives fine enough vertex density that the ground reads as smooth at eye level while keeping component count trivial.
- Add a second, larger, coarse Landscape for the far distance, or use a static mesh backdrop built from the DEM.

**A flat landscape is cheap.** All the standard "reduce landscape cost" advice is about relief-driven LOD popping, which does not apply. Spend the budget on the material instead.

### 5.2 Layer blending — a real material graph

The core node is **Landscape Layer Blend** (`LandscapeLayerBlend`). Its per-layer properties are `Layer Name`, `Preview Weight`, `Blend Type`, plus `Const Layer Input` and `Const Height Input` for debugging. Blend types:

- **LB Weight Blend** — weighted blend across all weight-blend layers; **not order dependent**. The default and the right choice for most layers.
- **LB Alpha Blend** — an alpha-blended overlay *on top of* the weight- and height-blend layers. Use for a decal-like layer such as a track or a swept yard.
- **LB Height Blend** — as weight blend, but adds detail to the transition using a heightmap. **This is the one that makes layer transitions look real** rather than airbrushed.

A working master material for the Okongo ground:

```
── Landscape Layer Coords (MappingScale = 4.0)  ─────────┐
                                                          │  (UVs in landscape space,
                                                          │   4 = one texture per 4 quads)
   For each of Sand / FineSand / LagGravel / Clay / Yard:
      TexCoord(from LandscapeLayerCoords)
         ├─ Multiply × MacroScale(0.01) ─→ Texture Sample (T_MacroNoise)  → macro variation
         ├─ Texture Sample (T_<layer>_BC)      → Base Color input
         ├─ Texture Sample (T_<layer>_N)       → Normal input
         └─ Texture Sample (T_<layer>_ORDp)    → R:AO  G:Rough  B:Displacement/Height

   Landscape Layer Blend  (Base Color)   ── layers ──┐
       Sand        : LB Weight Blend                  │
       FineSand    : LB Height Blend  (Height = ORDp.B)
       LagGravel   : LB Height Blend  (Height = ORDp.B)
       Clay        : LB Height Blend  (Height = ORDp.B)
       Yard        : LB Alpha  Blend                  │
                                                      ▼
                        Multiply ×  MacroVariation (0.85 – 1.15)
                                                      ▼
                                              [Base Color]

   Landscape Layer Blend  (Normal)     → BlendAngleCorrectedNormals with Detail Normal
                                                      ▼
                                              [Normal]

   Landscape Layer Blend  (Roughness)  → clamp 0.05 – 0.97 → [Roughness]

   Runtime Virtual Texture Output  ←  BaseColor / Normal / Roughness / SpecularMask
```

Notes that matter:

- **`Landscape Layer Coords`** (node name `LandscapeLayerCoords`) generates UVs in landscape space with a `Mapping Scale` in quads. Use it rather than `TexCoord`, because it survives landscape resizing.
- **`Landscape Layer Weight`** returns a single layer's weight as a scalar — use it to drive things other than colour (e.g. grass density, footstep sound, a wetness multiplier).
- **`Landscape Layer Switch`** compiles out an entire branch where a layer's weight is zero. On a five-layer material this is a large performance win; wrap expensive layers in it.
- **`Landscape Visibility Mask`** drives holes in the landscape — use for a borehole, a pit, or where the building's basement cuts through.
- **`Landscape Grass Output`** is the node that spawns grass meshes from layer weights. It is a *material output expression*, not in the node list Epic's landscape-materials page enumerates, so verify its exact availability in 5.8 — see Open questions.
- **Always convert the master material to a Material Instance** for actual use, and expose the tiling scales, macro-variation contrast and per-layer colour tints as parameters. See domain `13` file `03`.

### 5.3 Runtime Virtual Textures — blending meshes into terrain

RVT is the answer to the "objects look pasted on" tell. It is a texture whose texels are generated on demand by the GPU at runtime, functioning as a **shading cache** for the landscape.

The three pieces:
1. **Runtime Virtual Texture asset** — the configuration: size, tile size, and which material attributes it stores (Base Color, Normal, Roughness, Specular, World Height).
2. **Runtime Virtual Texture Volume** — an actor bounding the area that renders into the RVT, using orthographic projection.
3. **Material nodes** — `Runtime Virtual Texture Output` (in the landscape material, to *write*), `Runtime Virtual Texture Sample` (in a mesh material, to *read*), and `Runtime Virtual Texture Sample Parameter` (to let instances override which RVT they sample).

**Setup, concretely:**
1. Create two RVT assets: `RVT_Landscape_BaseColor_Normal_Roughness` (material type: Base Color, Normal, Roughness, Specular) and optionally `RVT_Landscape_Height` (World Height).
2. Add a `Runtime Virtual Texture Volume`, set `Bounds Align Actor` to the Landscape, click **Set Bounds**.
3. On the Landscape actor, under *Virtual Texture → Draw in Virtual Textures*, add both RVT assets.
4. In the landscape material add a `Runtime Virtual Texture Output` node and feed it Base Color, Normal, Roughness, Specular.
5. In a mesh material (a rock, a plinth, a paving slab, a wall base), add a `Runtime Virtual Texture Sample`, assign the RVT, and `Lerp` between the mesh's own material and the sampled landscape values using a mask driven by height above the mesh's base (a vertex-colour gradient or `WorldPosition.Z` remapped over the bottom 100–200 mm).
6. Control layer ordering with **Translucency Sort Priority** where compositing matters.

The result: the bottom 150 mm of every wall, plinth and rock takes on the exact colour and normal of the sand it sits in, and the boundary disappears. In a sand landscape where drift genuinely does bury the base of everything, this is not a cheat — it is the correct physical result.

**Cost.** RVT costs memory and a GPU update pass. Keep the RVT size at 4 K–8 K for a plot-scale site; only go higher if you can see the pixelation.

### 5.4 World Partition and large worlds

World Partition replaces the old level-streaming workflow: the world is divided into a grid of cells, and actors stream in and out based on distance from the streaming source.

- Enable at level creation (`Empty Open World` template) or convert with the World Partition Convert Commandlet.
- Grid cell size default 128 m; loading range default 256 m. For a residential plot these are far larger than needed — the whole site fits in one cell. **World Partition is only worth enabling here if the deliverable includes a drive-in approach across kilometres of landscape.**
- **Data Layers** are the useful part regardless of scale: put dry-season and wet-season vegetation on separate Data Layers and toggle between them, or separate "as-built" from "proposed".
- **World Partition Landscape** splits a large Landscape into streamable proxies automatically.
- **Level Instances** are the right tool for repeated homestead structures — build one kraal, place several.

---

## 6. The specific character of a flat, sandy, sparsely vegetated Cuvelai landscape

Every technique above has to serve this. A summary of what the landscape actually is, from domain `18`:

- **Elevation** ~1 150 m; regional relief across tens of kilometres is **metres, not tens of metres**.
- **Structure**: subdued vegetated dune ridges and interdune flats, relict from earlier arid phases, with the regional Kalahari dune orientation NW–SE.
- **Surface**: deep aeolian quartz sand (Arenosols), structureless, cohesionless, with calcrete horizons at depth and saline/sodic soils (Solonchaks, Solonetz) in and around the *iishana*.
- **No stone, no gravel, no surface water.** This is the single most important visual fact.
- **Vegetation**: broadleaved tree-and-shrub savanna / dry woodland, denser and taller than the western Cuvelai — Okongo means *a place or forest for hunting*.
- **Drainage**: iishana are shallow, grassy, interlinked channels, 10 m to >1 km wide, with impermeable clay or saline beds; they spread rather than incise, and flood in roughly 45% of years.
- **Settlement**: dispersed family homesteads on the slightly higher sandy interfluves, with palisade boundaries and swept, compacted, vegetation-free yards.

**What to build, in order of visual return:**
1. A **flat-to-gently-undulating landscape** with 2–6 m of amplitude over 500 m, no sharp features.
2. A **swept-yard layer** — compacted, pale, near-vegetation-free, with a hard edge at the palisade. This surface is highly characteristic and almost never seen in stock environments.
3. **Track and footpath layers** — the ruts and paths between homesteads, painted as an `LB Alpha Blend` layer with tyre-tread and footprint normals.
4. **Drift accumulation** at every vertical obstruction — palisade bases, wall bases, tree trunks. Modelled as geometry where it matters, as an RVT-blended material effect elsewhere.
5. **An oshana or pan** only if the site actually has one. If it does, it is the strongest compositional element available (see `06`).
6. **Termite mounds.** Ubiquitous in this landscape, structurally interesting, and completely absent from generic asset libraries. Sculpt three variants in Blender.

**What NOT to build:** rock outcrops, boulders, cliff faces, deep gullies, dense green grass lawn, coniferous anything, and orange dune sand borrowed from Namib Sand Sea reference.

---

## 7. Terrain checklist

- [ ] DEM sourced, CRS recorded, attribution notice filed
- [ ] Real elevation range measured (`gdalinfo -stats`) and written into the project notes
- [ ] Heightmap stretched to the full 16-bit range before export
- [ ] Z Scale computed as `height_cm × 0.001953125` and verified in-engine against two known points
- [ ] XY scale a round number
- [ ] Landscape size chosen from Epic's recommended table
- [ ] All layer weight maps imported with names matching the material's Layer Blend entries exactly
- [ ] `Landscape Layer Switch` wrapped around every expensive layer
- [ ] RVT asset + volume set up; mesh bases blend into terrain
- [ ] Macro variation applied (satellite image or large-scale noise)
- [ ] Distance-based tiling break-up present
- [ ] Checked from 1 600 mm eye height, not just from above

## Sources

- [Landscape Technical Guide in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-technical-guide-in-unreal-engine) — Epic Games
- [Landscape Materials in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-materials-in-unreal-engine) — Epic Games
- [Runtime Virtual Texturing in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/runtime-virtual-texturing-in-unreal-engine) — Epic Games
- [Copernicus DEM — collection description](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM) — ESA / Copernicus Data Space Ecosystem
- [Shuttle Radar Topography Mission](https://en.wikipedia.org/wiki/Shuttle_Radar_Topography_Mission) — Wikipedia
- [Gaea editions and pricing](https://quadspinner.com/order) — QuadSpinner
- [QuadSpinner Gaea](https://quadspinner.com/) — QuadSpinner
- [A.N.T. Landscape extension](https://extensions.blender.org/add-ons/antlandscape/) — Blender Foundation
- [Atlas of Namibia — The Cuvelai](https://atlasofnamibia.online/chapter-4/the-cuvelai) — Atlas of Namibia
- Internal: `18_namibia_context/01_geography-and-regions.md`, `18_namibia_context/03_geology-and-soils.md`

## Open questions

- **World Creator** current version, feature set and pricing. Its pricing and buy pages 404'd on 2026-08-25. `needs-verification`.
- **`Landscape Grass Output`** — this material output expression is not listed on Epic's Landscape Materials node page; confirm its exact name and availability in UE 5.8 before relying on it. `needs-verification`.
- Whether **Nanite Landscape** (Landscape with Nanite enabled) is production-ready in 5.8 and whether it changes the component-size advice. `needs-verification`.
- Actual site relief and the presence/absence of a nearby *oshana*. Requires the drone survey or a site visit.
