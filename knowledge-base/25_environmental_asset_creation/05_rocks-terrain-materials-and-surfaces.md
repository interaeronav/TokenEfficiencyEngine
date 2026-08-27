---
id: envasset.rocks_surfaces
title: Rocks, ground materials and surfaces — the geology the light lands on
domain: 25_environmental_asset_creation
tags: [rocks, sculpting, remesh, ground-material, layered-materials, height-blend, macro-variation, detail-normal, parallax-occlusion, tessellation, sand, dust, substance-designer, substance-painter, texel-density, trim-sheets, calcrete]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
applies_to: "Unreal Engine 5.8, Blender 5.2 LTS, Adobe Substance 3D Collection (2026)."
unit_system: SI
sources:
  - {title: "Adobe Substance 3D Collection", url: "https://www.adobe.com/products/substance3d.html", publisher: "Adobe", accessed: 2026-08-25}
  - {title: "Landscape Materials in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-materials-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Runtime Virtual Texturing in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/runtime-virtual-texturing-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Nanite Virtualized Geometry in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "ambientCG", url: "https://ambientcg.com/", publisher: "ambientCG", accessed: 2026-08-25}
  - {title: "Atlas of Namibia — Soil types", url: "https://atlasofnamibia.online/chapter-5/soil-types", publisher: "Atlas of Namibia", accessed: 2026-08-25}
related: [envasset.principles, envasset.terrain, envasset.vegetation, envasset.pipeline, namibia.geology_soils, blender.materials_shading, ue.materials_rendering]
---

# Rocks, ground materials and surfaces — the geology the light lands on

**Summary.** In most environment work, rocks carry the scene. In the eastern Ohangwena sandveld there are **no rocks** — the Atlas of Namibia and the geology record show deep aeolian Kalahari quartz sand (Arenosols) with calcrete horizons at depth and saline/sodic soils in the *iishana*, and no natural aggregate on site at all. So this file inverts the usual emphasis: rock technique is covered because you will still need termite mounds, calcrete nodules, borrow-pit faces and imported aggregate, but the bulk of it is about **sand** — how it is coloured, how it catches raking light, how it ripples, how it drifts against objects, and how to build a layered ground material that never tiles. It also covers Substance and Blender procedural authoring, texel density discipline, and trim sheets.

## Key facts

| Item | Value | Source |
|---|---|---|
| Adobe **Substance 3D Collection**, individual | **US$59.99/month** | adobe.com, 2026-08-25 |
| Substance 3D Collection, teams | **US$119.99/month per licence** (annual, billed monthly) | adobe.com |
| Substance 3D student/teacher | **Free** — Painter, Designer, Sampler, Stager; personal non-commercial only | adobe.com |
| Collection contents | Painter, Sampler, Stager, Designer, Modeler + 20 000+ asset library | adobe.com |
| ambientCG materials | **CC0**, up to 8K and sometimes larger; also ships SBSAR files | ambientcg.com |
| Landscape height-blend node | `Landscape Layer Blend` with **LB Height Blend** — adds transition detail from a heightmap | Epic |
| RVT nodes | `Runtime Virtual Texture Output`, `Runtime Virtual Texture Sample`, `…Sample Parameter` | Epic |
| Nanite blend modes | Opaque and Masked only | Epic |
| Kalahari surface material | **Aeolian quartz sand (Arenosols)**; calcrete at depth; **no surface stone or gravel** | Atlas of Namibia / domain 18 |
| Sandy-soil cation exchange capacity | **< 4 cmol/kg** — extremely low | Atlas of Namibia ch.5 |
| Bulk density threshold for good air/water movement | **< 1.5 t/m³** | Atlas of Namibia ch.5 |

> ⚠️ The commonest single mistake in visualising this landscape is importing "desert sand" assets built from Namib Sand Sea or Sahara reference. Those are **orange-red iron-coated dune sands**. Kalahari sandveld at Okongo is a **pale, greyish-cream to light-ochre quartz sand** with local iron staining, carrying leaf litter and grass. It is much lighter and much less saturated than the stock library expects.

---

## 1. Rock modelling — when you actually need it

### 1.1 What rock-like objects exist at Okongo

- **Termite mounds.** Ubiquitous, hard, sculptural, and completely absent from asset libraries. The highest-value "rock-technique" asset for this site.
- **Calcrete nodules and hardpan fragments.** Calcisols cement into calcrete at depth; where a track, a borehole or a foundation trench has cut through, angular pale-cream fragments appear at the surface. Calcrete is also the local road base-course material, so it appears wherever anything has been built.
- **Imported aggregate.** Concrete stone and crusher sand hauled 300–500 km from the Damara belt / Otavi carbonates. Visible as a stockpile, in exposed concrete, and in the aggregate exposed in a weathered slab edge.
- **Anthropic hard shapes.** Blocks, off-cuts, broken slab, discarded metal. In a landscape with no stone, these fill the visual role stone would otherwise play.

### 1.2 Sculpting in Blender

For a termite mound or a calcrete boulder:

1. Start from a `UV Sphere` or a rough box; add a **Remesh** modifier in **Voxel** mode, voxel size 0.05 m, to get an even quad-ish base at real scale.
2. Enter Sculpt Mode with **Dyntopo off** and use Voxel Remesh (`Ctrl+R`) as you go, stepping the resolution down from 0.05 → 0.02 → 0.008 m.
3. Brushes, in order: `Grab` for the primary form, `Clay Strips` for mass, `Scrape/Flatten` for planar facets, `Draw Sharp` for cracks, `Crease` for edges, `Smooth` at low strength between passes.
4. **Primary → secondary → tertiary.** Establish the whole silhouette first, then the facets, then the surface. Skipping to detail is the commonest sculpting mistake and produces a lumpy, scale-less object.
5. For a termite mound specifically: broad conical base, vertical fluting from rain runoff, rounded weathered top, small repair patches of fresher darker material, and — critically — a **skirt of eroded material** at the base merging into the ground.

### 1.3 Boolean and remesh workflows

For angular material (calcrete fragments, broken concrete):

1. Create a rough mass.
2. Cut it with several randomly rotated planes or cubes using the **Boolean** modifier in `Difference` mode (Exact solver).
3. Apply, then **Remesh (Voxel)** at a fine setting to weld everything and remove degenerate faces.
4. `Shade Smooth` + **Weighted Normal** modifier, or add a Bevel modifier (Angle mode, 0.5–2 mm, 2 segments) — **every real edge has a radius**, and a perfectly sharp edge is one of the clearest CG tells at close range.

### 1.4 Procedural rock generation

- **Blender Geometry Nodes**: subdivide an icosphere, displace with layered `Noise Texture` and `Voronoi Texture` (Distance to Edge gives the faceting), then `Set Shade Smooth` false on high-curvature faces. Wrap it as a node group with seed, angularity and elongation inputs, and generate 20 variants in a loop.
- **Rock Generator add-ons** exist (several free and paid); they save time but produce a recognisable "look" — vary the output heavily.
- **Displacement from a scanned height map** onto a low-poly base is the most convincing procedural route: take a CC0 rock height map from ambientCG or Poly Haven, apply it as a Displace on a rough sculpt, and the surface inherits real geology.

### 1.5 Photogrammetry rocks

Covered in `02`. For this project the targets are the termite mound, a calcrete outcrop at a cut, and a concrete block — all easy static subjects with good texture. Capture in overcast or open shade.

### 1.6 Rock LODs and Nanite

- **With Nanite**: keep the decimated scan at 1–5 M triangles, enable Nanite, done. Set `Position Precision` to Auto unless the asset is very large. Remember Nanite supports only Opaque and Masked blend modes, and that ray tracing uses the **fallback mesh** — lower `Fallback Relative Error` if the rock appears in reflections.
- **Without Nanite**: 3–8 k triangles for a hero rock, 4 LODs at screen sizes 1.0 / 0.4 / 0.15 / 0.05, plus a baked normal from the high-poly.
- **Collision**: simple convex hull, generated from a heavily decimated copy (`Convex Decomposition` in Unreal's Static Mesh editor, Hull Count 4–8). Never per-triangle collision on a scanned rock.

---

## 2. Ground material creation

This is the single most important asset in the project. Build it as one **master material** with a layer stack, then instance.

### 2.1 The layer stack for an Okongo yard

| # | Layer | Description | Height-blend? |
|---|---|---|---|
| 1 | `Sand_Base` | Mid-tone Kalahari sand, medium grain, wind-rippled | Base weight layer |
| 2 | `Sand_Fine` | Palest, softest, drifted fine sand — hollows, lee of objects | Yes |
| 3 | `Sand_Compacted` | The swept homestead yard: darker, denser, near-flat, with broom marks and footprints | Yes |
| 4 | `LagGravel` | Deflated surface — coarse grains and calcrete chips left where fines blew away | Yes |
| 5 | `Clay_Pan` | Oshana bed — grey-brown, smooth, desiccation-cracked in the dry season | Yes |
| 6 | `Litter` | Leaf litter and twigs under trees | Alpha blend on top |
| 7 | `Track` | Vehicle ruts and footpaths | Alpha blend on top |

Seven layers is a lot for a real-time material. Wrap layers 4–7 in **`Landscape Layer Switch`** so they compile out where their weight is zero.

### 2.2 Height blending — the technique that makes layers look real

A straight alpha blend between sand and gravel produces a soft airbrushed transition that no natural boundary has. **Height blending** uses each layer's height map to decide which wins at each pixel, so the gravel's stones poke through the sand exactly where they are proud of it.

In Unreal use `Landscape Layer Blend` with **LB Height Blend** and feed each layer's height into the node's Height input. Epic describes it as "the same as LB Weight Blend, but also adds detail to the transition between layers based on a height map."

The manual version (for mesh materials, where the landscape node is unavailable):

```
// heightLerp(a, b, ha, hb, t, contrast)
d      = 0.1                                   // transition contrast; smaller = sharper
ma     = ha + (1 - t)
mb     = hb + t
maxv   = max(ma, mb)
wa     = max(ma - (maxv - d), 0)
wb     = max(mb - (maxv - d), 0)
result = (a * wa + b * wb) / (wa + wb)
```

Build this once as a **Material Function** (`MF_HeightLerp`) with inputs A, B, HeightA, HeightB, Alpha, Contrast and reuse it everywhere.

### 2.3 Macro variation

Multiply the composited base colour by a very-large-scale noise. This is the highest-value anti-tiling technique and costs one texture fetch.

```
LandscapeLayerCoords (MappingScale = 4)
      │
      ├─ Multiply × 0.01  →  TextureSample(T_MacroNoise, sRGB off)   // ~100 m period
      │        └─ Lerp(0.86, 1.14, noise)  →  MacroA
      └─ Multiply × 0.05  →  TextureSample(T_MacroNoise)             // ~20 m period
               └─ Lerp(0.93, 1.07, noise)  →  MacroB

BaseColor × MacroA × MacroB
```

Two octaves at different scales beat one at double the amplitude, because a single octave has a visible period of its own.

**Better still: use the satellite image.** Project a real overhead image of the site (see `02 §6`) as the macro-variation texture, normalised to a 0.85–1.15 multiplier. The ground then reproduces the actual pattern of bare sand, grass and shrub cover, which no procedural noise can invent.

### 2.4 Detail normal

Beyond about 3 m the base normal map's mip chain has lost all micro-structure and the ground goes flat. Overlay a second, much smaller-scale normal:

```
DetailUV     = LandscapeLayerCoords × 32
DetailNormal = TextureSample(T_SandDetail_N, DetailUV)
FinalNormal  = BlendAngleCorrectedNormals(BaseNormal, DetailNormal)
              // fade DetailNormal to flat beyond ~4 m using PixelDepth
```

`BlendAngleCorrectedNormals` is the correct node — a plain `Add` of two normal maps produces wrong results at steep angles.

### 2.5 Distance-based tiling break-up

```
Depth        = PixelDepth
FarBlend     = saturate((Depth - 1500) / 6000)     // 15 m → 75 m, in uu
UV_Near      = LandscapeLayerCoords(MappingScale = 4)
UV_Far       = LandscapeLayerCoords(MappingScale = 24)
UV           = Lerp(UV_Near, UV_Far, FarBlend)
```

Sampling the same texture at a 6× larger scale in the distance removes the high-frequency repeat that causes both the visible pattern *and* the specular shimmer.

For a stronger break, use **stochastic (hex-grid) sampling**: sample three times at randomly offset UVs on a hex lattice and blend by barycentric weight. Cost: 3× fetches per texture. Worth it on the single most-visible ground layer only.

### 2.6 Parallax occlusion mapping and tessellation

| Technique | Cost | When |
|---|---|---|
| **Bump / normal only** | Free | Anything under ~2 mm of relief, or seen only at distance |
| **Bump Offset** (simple parallax) | Very cheap | Shallow relief seen at moderate angles — brick joints, shallow ripples |
| **Parallax Occlusion Mapping** (`ParallaxOcclusionMapping` material function) | Moderate — a loop of texture fetches | Deep relief seen at grazing angles: gravel, cobbles, deep bark, calcrete. Set MinSteps 8, MaxSteps 32, HeightRatio 0.03–0.08 |
| **Nanite Displaced Meshes / Tessellation** | Expensive but real geometry, correct silhouette and shadows | Hero foreground ground, where the silhouette against a wall base matters |
| **Modelled geometry** | Free at render, costs authoring | Anything the camera gets within 500 mm of |

**For sand specifically, POM is usually wrong** — sand's relief is shallow and its shading is dominated by grain-scale scattering, not by self-occlusion. Use a good normal map plus grazing-angle roughness variation. Save POM for gravel, calcrete and paving.

### 2.7 Puddles and wetness

Relevant for four months of the year, and for the oshana margin.

```
WetMask  = saturate( PuddleHeightMap - WaterLevel ) × LayerWeight(Clay_Pan)
BaseColor_wet  = BaseColor × Lerp(1.0, 0.55, WetMask)   // wet darkens
Roughness_wet  = Lerp(Roughness, 0.08, WetMask)          // wet smooths
Normal_wet     = Lerp(Normal, float3(0,0,1), WetMask)    // water surface is flat
Specular_wet   = Lerp(Specular, 0.5, WetMask)
```

The physics: water fills the microstructure, so the surface becomes **darker** (light enters and scatters before exiting), **smoother** and **flatter**. All four changes must happen together; changing only roughness gives the classic "shiny dry sand" error.

Add a **flow/height mask** so water collects in the low points rather than uniformly — drive from the same height map used for height blending, or from Gaea's `Flow` output.

---

## 3. Sand and dust, specifically

This is the material the whole project rests on. Get it right and the rest follows.

### 3.1 Grain scale

Kalahari aeolian sand is well-sorted fine-to-medium quartz sand — individual grains roughly **0.1–0.5 mm**. At a viewing distance of 1.5 m a grain subtends far less than a pixel, so **do not model or texture individual grains** at normal viewing distance. What you *do* see:

- **Ripples**: wavelength typically 50–150 mm, amplitude 3–10 mm, asymmetric with the steep face downwind.
- **Micro-relief**: footprints, tyre tracks, insect trails, raindrop pits, animal spoor.
- **Texture at 300 mm and closer**: individual grain sparkle and shadowing. Only author this on a foreground hero material.

Texel density guidance: **1024 px/m** for the primary sand layer gives ~1 mm per texel, enough for ripple detail and grain-level normal noise. See §6.

### 3.2 Wind ripple patterns

Ripples are the signature of a sand surface and are almost always missing or wrong in CG.

- They align **perpendicular to the prevailing wind**.
- They are **asymmetric**: gentle windward slope, steeper lee slope. A symmetric sine wave is wrong.
- They **fork and merge**; they are not parallel lines.
- They are **erased by traffic** — footprints, tyres, livestock — and re-form over hours to days. In a homestead yard the ripples exist only where nobody walks.
- On coarse-grained or moist sand they are absent or very subdued.

Author them in Substance Designer or as a Blender procedural: a directional gradient noise, sharpened asymmetrically with a `Curve`/`Levels` operation, warped with a low-frequency noise so the lines fork.

**[NA]** Prevailing wind direction at Ondangwa is documented in the Atlas of Namibia's wind chapter; calms below 0.5 m/s occur **53–68%** of the time depending on month, so ripples here are subdued and often relict rather than fresh. `needs-verification` on the specific prevailing direction to use for ripple orientation at Okongo.

### 3.3 Colour

Do not guess. Photograph the site with a colour chart (`02 §1.3`). As a starting point until you do:

- Dry pale Kalahari quartz sand: high value, low saturation — a greyish cream to light ochre. Albedo roughly **0.30–0.45**.
- Iron-stained fractions: warmer and darker, appearing as patches and as the fill of hollows.
- Damp sand: about **half the albedo** of dry sand of the same material, and slightly more saturated.
- Compacted swept yard: darker and slightly greyer than loose sand, because it is denser and carries fine dust and organic matter.
- The **contrast with dry grass** matters as much as the absolute colour: grass albedo ~0.15–0.25, so grass reads clearly *darker* than the sand around it. If your grass reads lighter than your sand, one of them is wrong.

### 3.4 How sand catches low light

At sunrise and sunset, sand does three things that no default material reproduces:

1. **The ripples cast long shadows**, turning a flat surface into a strongly textured one. This is why 07:00 and 17:30 are the money shots and midday is the hardest. Ensure the ripple *normal* (and ideally displacement) is strong enough to shadow itself — this is the one case where POM or tessellation on sand earns its cost.
2. **Forward scattering.** Looking toward the low sun, sand grains scatter light forward and the surface becomes noticeably brighter and warmer than when looking away from the sun. Model this by adding a small **forward-scattering lobe**: in Unreal, a `Fresnel`-driven addition to base colour weighted by `dot(LightVector, ViewVector)` — or more simply, use the `Subsurface` shading model with a very small subsurface contribution.
3. **Specular sheen at grazing angles.** Quartz grains have IOR ~1.55; at grazing incidence the whole surface picks up a sheen. This comes free from correct Fresnel if you have not suppressed Specular. Do **not** set Specular below 0.5 on sand.

### 3.5 Drift accumulation

Sand piles up where the wind slows: on the lee side of every obstruction. Concretely:

- A **wedge** against the lee face of a wall, deepest at the wall and tapering out over roughly 3–8× the obstruction height for a low object.
- A **scour hollow** on the windward side and at the ends, where accelerated flow removes material.
- Accumulation in **corners** and at the base of every post.
- Sand **on top of** horizontal surfaces — sills, ledges, steps, the tops of walls — held by the smallest roughness. This is the single most convincing weathering detail in this environment.

Implement in three ways, in order of cost:
1. **Material only** — a world-up-facing mask (`WorldAlignedNormal.B` raised to a power) that lerps to the sand material. Free, applies everywhere, gets the ledges.
2. **RVT blend at the base** — the bottom 100–200 mm of every mesh takes the landscape's sampled colour and normal (`03 §5.3`). Removes the pasted-on look.
3. **Modelled drift meshes** — an actual sculpted wedge against hero walls and posts. Necessary only where the camera gets close and the silhouette matters.

### 3.6 Airborne dust

See `06` for the atmospheric side. At material level, dust means: everything horizontal is slightly lighter, rougher and less saturated than it "should" be; and the difference between a swept and an unswept surface is large and visible.

---

## 4. Authoring tools

### 4.1 Substance 3D Designer

Node-based procedural material authoring. The industry standard, and the only tool where you can build a sand material that is fully parametric (grain size, ripple wavelength, ripple direction, moisture, iron staining, litter density) and re-derive it at any resolution.

**Cost: US$59.99/month for the full Substance 3D Collection** (Painter, Sampler, Stager, Designer, Modeler plus a 20 000+ asset library); US$119.99/month per licence for teams. Students and teachers get Painter, Designer, Sampler and Stager free for personal non-commercial use.

A sand-material graph in Designer, in outline:

```
Tile Generator (Cells) → Blur HQ → Warp        ← grain-scale base
Directional Noise / Anisotropic Noise          ← ripple direction
   └ Directional Warp (by low-freq Perlin)     ← fork and merge the ripples
   └ Curve (asymmetric)                        ← steep lee face
Blend (Add) → Height
Height → Normal (Normal node, intensity ~1.5)
Height → Ambient Occlusion (HBAO)
Height → Curvature Smooth → drives roughness and colour variation
Gradient Map (from a photographed sand palette) → Base Color
Base Color × Macro Perlin (0.9–1.1) → Base Color out
Roughness: 0.86 base, −0.06 in hollows, +0.04 on ridges
```

Export as SBSAR so the parameters remain live in Unreal (Substance plugin) or bake to textures.

### 4.2 Substance 3D Painter

For **hero assets** — the gate, a door, a piece of joinery, a water tank. Painter's value is the **generators**: `Curvature`, `Dirt`, `Mask Editor`, `Water Level`, `Position` — which turn the surface-history list in `01 §5` into a few minutes of work rather than a day of hand painting.

Workflow: bake mesh maps (Normal, World Space Normal, ID, AO, Curvature, Position, Thickness) → build a layer stack base → add smart masks driven by generators → export with an Unreal or glTF preset.

### 4.3 Substance 3D Sampler

Photo → material. The fastest route from a phone photo of the actual site sand to a usable PBR set. Its multi-angle-to-material filter (several photos with different flash directions) produces genuinely good normals. Covered in `02 §5`.

### 4.4 Blender's procedural nodes — the free alternative

Everything Designer does can be done in Blender's shader nodes, with two caveats: it is slower to author, and the result lives in Blender rather than as a portable SBSAR. For an agent-driven workflow, the second point cuts the other way — a Blender node tree is Python-scriptable and version-controllable as text-ish data.

A sand shader in Blender nodes:

```
Texture Coordinate (Object)  →  Mapping (scale 40)
   ├─ Noise Texture (4D, Scale 400, Detail 6, Roughness 0.55)   → grain
   ├─ Wave Texture (Bands, Direction X, Scale 12, Distortion 3, Detail 4)  → ripples
   │     └─ Map Range (clamp, curve to asymmetric)  ┐
   ├─ Noise Texture (Scale 1.2)  → warp the ripples ┘  (via Vector Math Add)
   └─ Noise Texture (Scale 0.06) → macro variation

Combine:  Math(Add) grain*0.15 + ripples*0.85  →  Height
Height → Bump (Strength 0.6, Distance 0.004)  →  Principled Normal
Height → ColorRamp → Mix Color between three sampled sand colours → Base Color
Base Color × macro (0.88–1.12)
Roughness: Map Range(Height, 0,1, 0.90, 0.83)
IOR 1.55, Specular default, Metallic 0
```

For real relief, drive **Displacement** with the same Height and use `Displacement Method: Displacement and Bump` with Adaptive Subdivision (Cycles).

**Baking out.** Whatever you author in Blender, bake it to textures for Unreal: `Render Properties → Bake`, with a UV-unwrapped plane, baking `Base Color` (with Direct/Indirect contributions off), `Normal`, `Roughness` and a custom `Emission`-trick pass for height. Script it (`08`).

---

## 5. Trim sheets and material atlases

A **trim sheet** is one texture containing horizontal strips of related detail — a skirting profile, a coping, a plaster band, a corrugated profile, a bolt row — which many meshes UV onto. For a building's exterior it collapses a dozen textures into one and removes a dozen material draw calls.

**When to use one here:** the boundary wall coping and plinth, the roof-sheet profile and its ridge/barge/eave trims, the palisade pole ends and lashings, gate and burglar-bar sections, window and door reveals.

**Rules:**
1. Lay strips out at a **consistent texel density** with the rest of the project (§6).
2. Keep strips aligned to whole pixel rows so mip-mapping does not bleed between them.
3. Leave **8–16 px** of gutter between strips at the highest resolution.
4. UV meshes so the strip runs along the length; scale only along the strip axis.
5. Pack a **height** channel and use `Bump Offset` for the profile depth — a trim sheet with parallax reads as modelled.

A **material atlas** is the same idea for whole surfaces: several unrelated materials packed into one 4K texture, used by many small props. Effective for set dressing (buckets, tools, crates) where each object gets a small patch.

---

## 6. Texel density discipline

Texel density = texture pixels per real-world metre. Inconsistent density is a *visible* error: two adjacent surfaces at different densities read as being at different distances.

**Set a project standard and enforce it.** A workable standard for architectural exterior visualisation:

| Class | Texel density | Example |
|---|---|---|
| Hero close-up (camera within 500 mm) | **2048 px/m** | Door handle, gate latch, tap |
| Primary architecture (walls, floors, joinery) | **1024 px/m** | Plaster, block, timber, paving |
| Ground / landscape layers | **1024 px/m** at the near tiling scale | Sand, gravel, clay |
| Secondary props | **512 px/m** | Water tank, wheelbarrow, furniture |
| Background / distant | **256 px/m** or lower | Distant treeline, far buildings |

Worked example: a 4 m × 2.6 m wall panel at 1024 px/m needs 4096 × 2662 texels. Round up to a 4096 × 4096 texture and accept some waste, or split it.

**Checking it.**
- Blender: the **UV Checker** texture (Add → Image → Generated → UV Grid) at a known size; or the `TexTools` add-on which reports px/m directly.
- Unreal: viewport **Optimization Viewmodes → Texture Density** (formerly "Shader Complexity → Texture Density"); or place a checker material and compare square sizes across surfaces.
- Make your own checker with a **100 mm square grid** and one red square per metre. Then a correct surface shows exactly ten squares per metre and you can read errors at a glance.

**Landscape texel density** is set by the `Landscape Layer Coords` Mapping Scale, not by the texture resolution alone. Mapping Scale 4 with 1 m quads means one texture tile per 4 m; a 4096² texture then gives 1024 px/m.

---

## 7. Surface checklist

- [ ] Sand colour taken from a colour-chart-calibrated site photograph, not from a library
- [ ] Grass reads darker than sand
- [ ] Ripples present, asymmetric, forking, and absent where traffic has erased them
- [ ] Drift wedges and scour hollows at every obstruction
- [ ] Sand on every horizontal ledge, sill and wall top
- [ ] Macro variation applied (satellite image preferred)
- [ ] Detail normal at ~32× the base scale, faded with distance
- [ ] Distance-based UV scale blend in place
- [ ] Height blending (`LB Height Blend`) on every layer transition, not alpha blending
- [ ] Roughness textured everywhere, clamped 0.03–0.97
- [ ] Albedo clamped 0.03–0.90
- [ ] Specular left at 0.5 on all dielectrics
- [ ] RVT blend on every mesh base
- [ ] Texel density consistent and checked with a grid material
- [ ] Every edge bevelled — no perfectly sharp geometry
- [ ] Wet-state variant authored for the four wet-season months

## Sources

- [Adobe Substance 3D Collection](https://www.adobe.com/products/substance3d.html) — Adobe
- [Landscape Materials in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-materials-in-unreal-engine) — Epic Games
- [Runtime Virtual Texturing in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/runtime-virtual-texturing-in-unreal-engine) — Epic Games
- [Nanite Virtualized Geometry in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine) — Epic Games
- [ambientCG](https://ambientcg.com/) — ambientCG (CC0 materials, SBSAR files)
- [Poly Haven licence](https://polyhaven.com/license) — Poly Haven (CC0)
- [Atlas of Namibia — Soil types](https://atlasofnamibia.online/chapter-5/soil-types) — Atlas of Namibia
- Internal: `18_namibia_context/03_geology-and-soils.md`, `01_principles-of-photoreal-environments.md`, `03_terrain-and-landscape.md`

## Open questions

- **Measured albedo and colour of Okongo sand.** All colour guidance here is indicative until a chart-calibrated site photograph exists. `needs-verification`.
- **Prevailing wind direction at Okongo** for ripple and drift orientation. The Atlas of Namibia's wind chapter has regional data; the local direction needs confirming. `needs-verification`.
- Whether **Nanite Displaced Meshes / tessellation** is production-ready in UE 5.8 and its cost on a landscape-scale ground material. `needs-verification`.
- Whether calcrete is exposed anywhere on or near the site. Site visit.
