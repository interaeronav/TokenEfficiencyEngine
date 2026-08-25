---
id: envasset.vegetation
title: Vegetation and foliage that reads as real
domain: 25_environmental_asset_creation
tags: [foliage, vegetation, speedtree, sapling-tree-gen, the-grove, geometry-nodes, nanite-foliage, lod, billboard, pivot-painter, wind, subsurface-scattering, mopane, marula, makalani, namibia]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
applies_to: "Unreal Engine 5.8, Blender 5.2 LTS, SpeedTree Modeler (Unity-owned). Botanical data for northern Namibia."
unit_system: SI
sources:
  - {title: "SpeedTree product tiers and pricing", url: "https://unity.com/products/speedtree", publisher: "Unity Technologies", accessed: 2026-08-25}
  - {title: "Nanite Virtualized Geometry in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Pivot Painter Tool in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/pivot-painter-tool-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Creating and Using LODs in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/creating-and-using-lods-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Colophospermum mopane", url: "https://en.wikipedia.org/wiki/Colophospermum", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Sclerocarya birrea", url: "https://en.wikipedia.org/wiki/Sclerocarya_birrea", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Hyphaene petersiana", url: "https://en.wikipedia.org/wiki/Hyphaene_petersiana", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Diospyros mespiliformis", url: "https://en.wikipedia.org/wiki/Diospyros_mespiliformis", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Vachellia erioloba", url: "https://en.wikipedia.org/wiki/Vachellia_erioloba", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Schinziophyton rautanenii", url: "https://en.wikipedia.org/wiki/Schinziophyton", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Terminalia sericea", url: "https://en.wikipedia.org/wiki/Terminalia_sericea", publisher: "Wikipedia", accessed: 2026-08-25}
related: [envasset.principles, envasset.terrain, envasset.rocks_surfaces, envasset.pipeline, namibia.geography, namibia.climate]
---

# Vegetation and foliage that reads as real

**Summary.** Trees are the hardest photoreal asset class, because everyone has looked at thousands of them and nobody has to think to know when one is wrong. In the Okongo sandveld they are also the *dominant* visual element — the terrain is flat, there is no stone, and the image is carried by a small number of specific, correct trees plus eight months of straw-coloured grass. This file starts with the botanical reference step (which species, what shape, what size, what seasonal colour), then covers SpeedTree, Blender tree tools, leaf and bark texturing, the geometry-vs-cards-vs-Nanite decision, LODs and billboards, wind animation in both applications, ground-cover scattering, and subsurface scattering — closing with a list of the tells that make CG trees fake.

## Key facts — the species that actually grow at Okongo

| Species | Oshiwambo / common | Height | Habit and silhouette | Notes |
|---|---|---|---|---|
| **Colophospermum mopane** | *omusati*, mopane, butterfly tree | 10–15 m single-stemmed on sandy alluvium; up to **18 m** ("cathedral mopane"); **stunted 1–3 m multi-stemmed shrub** on clayey or impermeable alkaline soil | Upright, open, sparse; **distinctive bifoliate "butterfly" leaf** — two mirror-image leaflets on a common petiole | The regional keystone. Wood 0.99–1.23 g/cm³ at 12% MC, termite-resistant — hence the palisade poles. Leaves fold vertically in heat |
| **Sclerocarya birrea** subsp. *afra* | *omuongo*, marula | up to **18 m** | **Single-stemmed with a broad, spreading crown**; grey mottled bark | Fruit ripens Feb–Apr. Protected culturally and often deliberately retained in cultivated land |
| **Hyphaene petersiana** | makalani / real fan palm | tall palm, dioecious | Single unbranched (occasionally forked) trunk, fan-shaped fronds in a crown | Habitat: open woodland, floodplains, **fringes of pans and swamps** — i.e. near *iishana*, not on the dry interfluve |
| **Diospyros mespiliformis** | jackalberry, African ebony | average **4–6 m**, occasionally **25 m** | Dense, dark green, elliptical leaves; **dark grey fissured bark** | Grows **on termite mounds** and in riparian forest; mutualistic with termites. The darkest green in the landscape |
| **Vachellia erioloba** | camelthorn, *kameeldoring* | up to **20 m** | Rounded to flat crown; **light-grey thorns that reflect sunlight**; bipinnate leaves that **close when hot**; ear-shaped pods | Deep dry sandy soils. Slow-growing, very drought-hardy |
| **Schinziophyton rautanenii** | mangetti / mongongo / manketti | **15–20 m** | Large, spreading; **distinctive hand-shaped (palmate) leaves**; pale yellow balsa-like wood | **Associated with Kalahari sand soil-types**, wooded hills and dunes — exactly Okongo's substrate. Fruit falls Mar–May |
| **Terminalia sericea** | silver cluster-leaf, *vaalboom* | ~**9 m** in woodland, isolated trees to **23 m** | **Foliage clustered at branch tips**; bluish-green leaves with **silvery hairs on both surfaces**; reddish/greyish-brown bark peeling in strips | The silver sheen is a real, visible, and easily-missed characteristic. Winged nuts turn pink and persist a year |

> ⚠️ The single most valuable line in this file: **the mopane at Okongo is not the tall Zambezi mopane of the stock photos.** On the sandveld it is variable, often multi-stemmed and 4–8 m; on impermeable alkaline ground it is a 1–3 m shrub. Getting this wrong makes the whole environment read as somewhere else in Africa. `needs-verification` on the specific height distribution at Okongo — this needs a site photograph, not a reference book.

## Key facts — tools and technical

| Item | Value | Source |
|---|---|---|
| **SpeedTree Indie** | **US$19/month**, revenue under 100 K | unity.com/products/speedtree, 2026-08-25 |
| **SpeedTree Pro** | **US$899/year**, revenue under 1 M | unity.com/products/speedtree |
| **SpeedTree Library** add-on | **US$999** one-time, year-long subscription, games *or* cinema library | unity.com/products/speedtree |
| **SpeedTree Enterprise** | Custom pricing, revenue over 1 M; adds Runtime SDK, node-locked/floating | unity.com/products/speedtree |
| Nanite + masked materials | **Supported** (Opaque and Masked blend modes) | Epic Nanite docs |
| Nanite Foliage | A dedicated system: "Nanite's virtualized geometry rendering to achieve dense, highly detailed foliage at scale" | Epic Nanite docs |
| Nanite + World Position Offset | Supported with caveats — WPO clusters are culled individually; **you must clamp the displacement** | Epic Nanite docs |
| Nanite unsupported | Morph targets, forward rendering, VR stereo, MSAA; ray tracing uses the fallback mesh | Epic Nanite docs |
| Unreal auto-LOD screen size | Auto Compute divides screen-size percentage equally across LODs (2 LODs → swap at 50%) | Epic LOD docs |
| Pivot Painter | MAXScript that stores pivot and rotation information in the model's vertex data, read by the shader; versions **1.0 and 2.0** | Epic Pivot Painter docs |

---

## 1. The botanical reference step

Before opening any tree tool, answer these, with photographs:

1. **Which species are actually on this plot?** Not "which grow in Namibia". Walk the site, photograph every distinct tree, and identify them. The list above is the candidate set for eastern Ohangwena; the site will have a subset plus fruit trees planted around the homestead.
2. **What is the age structure?** A homestead yard typically has a few large retained shade trees (marula, jackalberry, mopane) and cleared ground beneath — not a uniform woodland.
3. **What season is the render?** This changes everything:

| Season | Months | Grass | Trees | Sky | Ground |
|---|---|---|---|---|---|
| Late dry / pre-rain | Aug–Oct | Straw, grey-gold, much of it broken and lodged | Many deciduous species bare or sparse; mopane leafless late dry season | Cloudless, hazy with dust and smoke | Pale, dusty, bare between tussocks |
| Early wet | Nov–Dec | New green flush at tussock bases, straw still standing | Fresh flush, brightest greens of the year | Building cumulus | Darkening, first crusting |
| Peak wet | Jan–Mar | Full green, tall, dense | Full canopy, densest shade | Frequent cloud, ~80% RH at 08:00 | Damp, locally ponded, oshana filling |
| Early dry | Apr–Jul | Curing — green to gold transition, seed heads | Fruit falling (marula Feb–Apr, mangetti Mar–May), leaves colouring and dropping | Clear, cool | Drying, leaf litter accumulating |

4. **Photograph bark at 300 mm with a scale**, for every species you will model. Bark is where trees are most often wrong.
5. **Photograph the silhouette against sky** at 100–200 mm focal length. Silhouette is the primary read at distance.

---

## 2. Building the trees

### 2.1 SpeedTree

SpeedTree is the industry standard and the fastest route to a correct, well-LODded, well-windable tree. Its Modeler is procedural-with-manual-override: you build a generator hierarchy (Trunk → Branch → Branch → Leaf), tune the growth parameters, then hand-edit individual branches where needed.

**Pricing** (Unity-owned since the acquisition): Indie **US$19/month** (revenue under 100 K), Pro **US$899/year** (revenue under 1 M), Enterprise custom (revenue over 1 M). The **SpeedTree Library** is a separate **US$999** one-time purchase giving a year of access to either the games or the cinema library.

**Why it is worth it for this project.** None of the seven species above exists in any stock library in a correct Namibian form. You will be building them from scratch regardless. SpeedTree's Indie tier at US$19/month for the two or three months of asset production is cheap relative to the time it saves on LODs, billboards and wind setup alone.

**Workflow to Unreal:**
1. Build in SpeedTree Modeler at real scale, metres.
2. Set up LODs inside SpeedTree (it generates them procedurally, reducing branch and leaf counts and finally swapping to a billboard).
3. Export as `.st9`/`.st` for Unreal's native SpeedTree importer, or as FBX + textures.
4. Unreal imports SpeedTree assets with the wind parameters intact and generates the material with SpeedTree's wind nodes wired up.
5. Reassign materials to your own master material instances if you want engine-consistent shading (see `08`).

**The species-specific things SpeedTree makes easy:** mopane's paired butterfly leaflets (a two-leaflet leaf mesh on a common petiole), camelthorn's bipinnate compound leaves and paired thorns, mangetti's palmate leaf, and the makalani's crown of fan fronds (build the frond as a single mesh with a rib, then radiate).

### 2.2 Blender-based tree creation

**Sapling Tree Gen** — the classic bundled add-on (`Add → Curve → Sapling Tree Gen`). Since Blender 4.2 it is distributed through the extensions system rather than as a bundled add-on; enable it from Preferences → Get Extensions. It generates a branch skeleton from a parameter set, with presets and a `Branch Splitting`/`Branch Growth`/`Leaves` panel structure. Its output is curves converted to mesh, with leaves as instanced planes.

*Honest assessment:* Sapling produces convincing *temperate* trees quickly and struggles with the sparse, irregular, wind-shaped forms of savanna trees. Use it for a fast base skeleton, then edit heavily.

**The Grove** (paid add-on) simulates growth over years with light competition and branch shedding, producing genuinely believable structure and — critically — **dead branches and asymmetry** for free. It is the strongest Blender option for a hero tree. `needs-verification` on current price and Blender 5.2 compatibility.

**Modular Tree** (free, open source) is a node-based tree generator. Less polished than either of the above but free and scriptable.

**Geometry Nodes** is the most flexible route and the one that fits an agent-driven workflow. A workable structure:

```
Curve Line / Curve to Points          ← trunk spine
  └ Set Curve Radius (from Spline Parameter, tapered)
  └ Curve to Mesh (profile: Curve Circle, 8-12 verts)

Instance on Points (on trunk points, selection = above height threshold)
  └ Rotate Instances (random pitch 25-70°, random yaw)
  └ Scale Instances (falls off with height)
  └ [recursive: repeat for second-order branches]

Distribute Points on Faces (on branch mesh, density weighted by branch radius)
  └ Instance on Points → leaf card mesh
  └ Align Rotation to Vector (normal) + Random Rotation
  └ Store Named Attribute "leaf_variation" (Random Value 0-1) → shader
```

Blender 5.x additions that help: **Bundles and Closures** (5.0) let you package a branch generator as a reusable closure and recurse cleanly; the node-based **Scatter on Surface** modifier (5.0) removes a lot of manual node work for leaf and ground-cover distribution.

### 2.3 Photogrammetry for trees

Photogrammetry a whole tree only works in still air with a very large capture, and is rarely worth it. What *is* worth it:

- **Bark**: photogrammetry or cross-polarised texture capture of a 400 × 400 mm patch of mopane, marula and jackalberry bark. These are the three most-seen bark surfaces and none of them exists correctly in any library.
- **A fallen branch or a dead stump**: easy, static, high-value set dressing.
- **A single leaf / frond**: flatbed-scan it. Put leaves on a scanner at 1200 dpi with a black backing. This gives a perfect, sharp, evenly-lit albedo with a clean alpha, in five minutes. Scan 20 leaves per species, including damaged, insect-eaten and dead ones.

**The flatbed scanner is the single most underrated foliage tool.** Do this before anything else.

---

## 3. Leaf and bark texture creation

### 3.1 Leaf atlases

Build an **atlas** — one texture containing many leaves and small branch clusters — rather than one texture per leaf.

- Resolution: **2048 × 2048** for a hero tree, 1024² for background species.
- Channels: `BaseColor` (RGB) + `Opacity` (A); `Normal` (RGB); `ORDT` packed as R=AO, G=Roughness, B=Translucency/Thickness, A=(spare).
- **Leave generous margins** and dilate the albedo well beyond the alpha edge (16–32 px), or mip-mapping will pull background colour into the leaf edges and give you the classic dark or white halo.
- Include **variation**: 6–10 leaf variants per species, plus 2–3 dead/yellowed, plus 1–2 insect-damaged. Real canopies contain 5–15% non-green material and CG canopies contain none.
- **Alpha test threshold**: set the material's `Opacity Mask Clip Value` around 0.33 and author the alpha so the edge lands there cleanly. Enable *dithered LOD transition* only if you have TSR/TAA to resolve it.

### 3.2 Bark

- Photograph or scan at **≥ 300 px per 100 mm** for a hero trunk (i.e. ~3 000 px per metre).
- Make it tile vertically only; horizontal tiling on a trunk is hidden by the cylinder wrap.
- Author **displacement/height** as well as normal — bark's deep fissures need parallax at close range (see `05`).
- Bark roughness: 0.75–0.92, with the fissure interiors *rougher and darker* than the ridges. Drive from an inverted height/AO.
- Mopane bark is grey-brown and relatively smooth to shallowly fissured; jackalberry is **dark grey and deeply fissured**; marula is **grey and mottled, flaking in patches**; Terminalia sericea **peels away in strips** revealing lighter wood beneath. These are the distinguishing marks and they are what make a species recognisable.

---

## 4. Atlases and cards vs full geometry vs Nanite foliage

| Approach | Cost | Realism | Use when |
|---|---|---|---|
| **Leaf cards on an atlas** | Lowest triangle count, but heavy **overdraw** and alpha-test cost | Good if cards are small and dense, poor if cards are large slabs | The default for mid and background trees; anything running in real time at scale |
| **Modelled leaf geometry** (each leaf a few triangles, no alpha) | High triangle count, **zero overdraw**, no alpha test | Best silhouette, best shading, best at close range | Hero trees under Nanite; offline renders in Cycles |
| **Nanite foliage** | Triangle count effectively free; masked materials supported | Very good — you can keep modelled leaves at full density | Unreal 5.4+ with Nanite Foliage; the right default for this project's hero trees |
| **Billboards / imposters** | Cheapest possible | Only acceptable at distance | Far LOD, background treeline |

**The overdraw trap.** A tree built from large alpha-tested cards can cost more than the same tree with 10× the triangles in solid geometry, because every pixel is shaded several times over. If a foliage-heavy scene is slow, check `r.Shaders.Optimize` — no; check the **Quad Overdraw** and **Shader Complexity** view modes first. Reducing card *size* (more, smaller cards) usually helps more than reducing card *count*.

**Nanite foliage practicalities:**
- Nanite supports Opaque and Masked blend modes, so alpha-tested leaf cards work — but modelled leaves with no alpha are cheaper still under Nanite because they avoid the masked-material path.
- **World Position Offset** (wind) works, but Nanite splits WPO meshes into clusters culled individually against their own bounds. You must **clamp the displacement** — set `Max World Position Offset Displacement` on the static mesh to the actual maximum your wind can push a vertex (e.g. 60 cm for a large tree), otherwise you get culling artefacts or a large conservative-bounds cost.
- Ray tracing (and Lumen's hardware path) uses the **fallback mesh**. If reflections or ray-traced shadows of foliage matter, lower `Fallback Relative Error` so the fallback keeps more of the source triangles.

---

## 5. LOD strategy and billboard transitions

For non-Nanite foliage, or for the far field:

| LOD | Screen size (approx.) | Content |
|---|---|---|
| LOD0 | 1.0 – 0.35 | Full leaf cards, full branch geometry |
| LOD1 | 0.35 – 0.15 | ~50% leaf cards, merged small branches |
| LOD2 | 0.15 – 0.06 | ~25% cards, trunk only for branch geometry |
| LOD3 | 0.06 – 0.02 | Crossed-plane or few-card cluster |
| LOD4 / Billboard | < 0.02 | Single camera-facing imposter |

Unreal's **Auto Compute LOD Distances** divides screen size equally across LODs — with 2 LODs the swap is at 50%. That is almost never right for foliage. Uncheck it and set **Screen Size** per LOD manually using the numbers above as a start, then walk the camera out and watch for popping.

**Killing the pop:**
1. **Dithered LOD Transition** — tick it in the material. Combined with TSR it dissolves the transition over a few frames.
2. Keep the **silhouette** consistent across LODs. Most popping is silhouette change, not detail change.
3. Keep the **average colour** consistent. If LOD2 is noticeably darker because fewer overlapping cards produce less self-shadowing, brighten LOD2's material or bake a lighter AO.
4. For billboards, generate a **full octahedral imposter** (Unreal's Imposter Baker, available as a plugin/Content Example) rather than a single crossed plane — it holds up from any angle including above.

---

## 6. Wind animation

Wind is the difference between a photograph and a still life. Even a *still* frame benefits, because a windless canopy looks unnaturally rigid — but the main win is in animation.

**[NA]** Note the local wind character from domain `18`: calms below 0.5 m/s occur at Ondangwa **53–68% of the time** depending on month. Northern Namibia is a *calm* place much of the time. Heavy, constant tree motion is wrong here. Author for **gentle, intermittent** movement with occasional gusts.

### 6.1 Unreal — SimpleGrassWind and material-driven wind

For grass and small plants, the standard route is the **`SimpleGrassWind`** material function: plug a `WindIntensity` scalar, `WindWeight` (usually vertex colour red or the green channel used as a stiffness mask), `WindSpeed`, and an `AdditionalWPO` input, and connect its output to **World Position Offset**. Vertex colour is the mask: **black at the base (rigid), white at the tips (free)**. Paint this in Blender before export.

For trees, the correct approach is hierarchical: the trunk sways slowly and slightly, branches sway faster with more amplitude, leaves flutter fastest with least amplitude. Two mechanisms:

**A. SpeedTree wind.** If the tree came from SpeedTree, use it. The importer wires up SpeedTree's wind material nodes and exposes wind strength/direction parameters. It is hierarchical and correct out of the box.

**B. Pivot Painter 2.** Pivot Painter is described by Epic as a MAXScript that stores model pivot and rotation information in the model's vertex data, which the shader then reads to produce interactive effects; there are versions 1.0 and 2.0. In practice: each branch's pivot position and axis are baked into textures, and a material function reads them per-vertex to rotate each branch about its own pivot. This gives per-branch hierarchical motion on a single mesh with one draw call.

> `needs-verification`: Epic's Pivot Painter documentation pages did not return body content on 2026-08-25. Confirm before relying on details: the exact material function names, the required texture import settings (the pivot textures must be imported with sRGB **off**, compression set to a lossless/HDR setting, and filtering set to nearest), and which UV channels carry the index data. Also confirm whether a Blender-side Pivot Painter equivalent is available — the original tool is 3ds Max-only, and community Blender ports exist but need checking.

**C. Vertex-animation textures (VAT).** Bake a simulated animation to a texture and read it in the material. Highest fidelity, highest cost, and overkill for architectural visualisation.

**Practical wind settings** for a calm Ohangwena day: wind speed low, gust frequency low, amplitude at leaf tips **20–60 mm** for a mopane, **100–250 mm** for a marula branch tip, trunk sway **< 20 mm**. Add a *very* low-frequency (0.05–0.1 Hz) global offset so the whole canopy breathes.

### 6.2 Blender

- **Wind force field** (`Add → Force Field → Wind`) + **Cloth** or **Softbody** on the leaf mesh: physically correct, slow, and unnecessary for stills.
- **Simple Deform (Bend)** modifier driven by a noise-textured driver: cheap and adequate for a background tree.
- **Geometry Nodes**: `Set Position` with an offset driven by `Noise Texture` (4D, W = `Scene Time`) multiplied by a stiffness attribute (distance from trunk, normalised). This is the direct analogue of the Unreal approach and lets you author the same stiffness mask once and use it in both applications.
- **Wave modifier** for grass fields: crude but fast.

---

## 7. Grass and ground cover

In this landscape grass is at least as important as trees, and for eight months of the year it is **straw**, not green.

**Building it:**
1. Model a **grass clump** — 8–15 blades of varying height, curvature and colour, on 2–3 cards or as thin modelled strips. Blades 300–900 mm.
2. Make **4–6 clump variants**, including one mostly dead, one lodged/flattened, one with seed heads.
3. Vertex-colour the stiffness mask (black at base, white at tip).
4. Model separate **seed heads** as a distinct scatter layer — they are the finest, brightest element and catch backlight beautifully.

**Scattering in Unreal:**
- **Foliage tool** for hand-painted areas, **Procedural Foliage Volumes** for large-area generation with species competition, **Landscape Grass Type** assets driven from the landscape material for automatic density-by-layer.
- Grass Type settings that matter: `Grass Density` (per 10 m² by default), `Start Cull Distance` / `End Cull Distance`, `Min LOD`, `Random Rotation`, `Align to Surface`, `Scale X/Y/Z` min-max.
- **Cull distances are a realism setting, not just a performance setting.** Grass that disappears at 30 m leaves a visible bald ring. Extend `End Cull Distance` to at least 60–80 m and blend the transition by making the ground material's colour match the grass average beyond that distance.

**Scattering in Blender:**
- **Geometry Nodes** `Distribute Points on Faces` (Poisson disk) → `Instance on Points`, with density weighted by a vertex-colour or texture mask.
- Blender 5.0's node-based **Scatter on Surface** modifier does this without building the graph.
- Use **linked collection instances** and enable *Display As: Bounds* in the viewport to keep the scene navigable.

**Placement realism.**
- Grass is **not uniform**. It grows in clumps with bare sand between, denser in hollows and along the shade line of trees and walls, absent from the swept yard, dense along the outside of a fence where livestock cannot reach.
- The **shade line** is the most convincing single placement rule: vegetation is visibly greener and denser under and just north/south of tree canopies.
- Add **leaf litter** as a separate low scatter under every tree.
- Add **livestock effects**: browse lines at 1.2–1.8 m on trees near a kraal, trampled ground, dung.

---

## 8. Subsurface scattering, translucency and backlighting

Covered in principle in `01 §4.4`. Specifics for foliage:

**Unreal.**
- Shading Model: **Two Sided Foliage** for thin single-sided cards. Its `Subsurface Color` input controls transmitted light.
- Set `Subsurface Color` to a *lighter, warmer, less saturated* version of the leaf base colour. For a green leaf, something around a yellow-green at higher value. Drive it from a `Thickness` map (packed in ORDT.B) so veins and the midrib transmit less than the lamina.
- Enable `Two Sided` on the material.
- The effect is most visible when the sun is **behind** the tree relative to camera. Compose at least one shot that way — it is the single most convincing foliage image available.

**Blender.**
- Principled BSDF: **Subsurface Weight** 0.05–0.2, **Subsurface Radius** roughly (0.004, 0.002, 0.001) m for a typical leaf, Subsurface Color a warm light green.
- Blender 5.2's **Thin Wall** mode on the Principled BSDF is the correct treatment for genuinely single-surface geometry (leaves, blinds, paper, glass panes) and should be preferred over a fake translucency setup.
- Ensure the leaf card's **Backface Culling** is off and the normals are handled — for cards, either use a `Geometry → Backfacing` node to flip the normal, or model leaves double-sided.

**Leaf normals.** The most impactful non-obvious trick: for leaf cards, **override the vertex normals to point outward from the canopy centre** (a spherical normal) rather than perpendicular to the card. This makes the canopy shade as a single soft volume rather than as thousands of flat flickering planes. In Blender: add an empty at the canopy centre, use the `Data Transfer` modifier from a sphere, or use the *Normal Edit* modifier in `Radial` mode targeting the empty. Blend 60–80% toward the spherical normal; keeping 20–40% of the original preserves some leaf-level detail.

---

## 9. The tells that make CG trees look fake

| Tell | Why it happens | Fix |
|---|---|---|
| **Uniform colour** | One albedo texture, no per-instance or per-leaf variation | `PerInstanceRandom` → hue/value shift; leaf-index attribute → colour ramp; include 5–15% dead/yellow leaves in the atlas |
| **No wind variance** | One wind phase for all instances | Offset the wind phase per instance from `PerInstanceRandom` or object position; vary intensity per instance |
| **Perfect symmetry** | Procedural generators default to even distribution | Force asymmetry: prune branches on one side, lean the trunk, thin the crown where it competed with a neighbour |
| **Wrong leaf density** | Artists make canopies solid | Real savanna canopies are **open** — you can see sky through them. Mopane especially is sparse |
| **No dead material** | Nobody models dead branches | Every mature tree has dead twigs, a broken limb, bark scars, a lightning strike or a browse line |
| **Flat, flickering canopy shading** | Card normals perpendicular to cards | Spherical normal override (§8) |
| **Cardboard-cutout backlight** | No translucency | Two Sided Foliage / Thin Wall (§8) |
| **Floating trunk** | No ground blending, no litter, no drift | RVT blend at the base, leaf litter scatter, a sand drift mesh on the lee side |
| **Wrong species for the place** | Library assets | Build the seven species in the table above |
| **Green in September** | Reference from the wet season | Match grass and canopy colour to the render's declared date |
| **Trees all the same age and size** | Single asset instanced | Minimum 3 size classes per species: sapling, mid, mature, plus one dead standing |
| **Regular spacing** | Grid or uniform scatter | Cluster: trees grow where seeds landed and survived. Use Poisson with a clustering bias, and hand-place the hero trees |
| **No browse line** | Livestock not considered | A hard horizontal edge to the canopy at 1.2–1.8 m near any kraal or grazed area |

---

## 10. Foliage checklist

- [ ] Species identified from site photographs, not from a general Namibia list
- [ ] Season declared and grass/canopy colour matched to it
- [ ] Leaves flatbed-scanned, including dead and damaged
- [ ] Bark captured per species at ≥ 3 000 px/m
- [ ] Minimum 3 size classes and 3 mesh variants per species
- [ ] Dead material present on every mature tree
- [ ] Vertex-colour stiffness mask painted (black base → white tip)
- [ ] Spherical normals applied to canopy cards
- [ ] Two Sided Foliage / Thin Wall shading in use
- [ ] Wind phase and intensity randomised per instance; amplitude matched to a calm climate
- [ ] LOD screen sizes set manually, dithered transition on, silhouette consistent
- [ ] Nanite WPO displacement clamped
- [ ] Grass cull distance ≥ 60 m with a matching ground colour beyond
- [ ] Leaf litter and drift at the base of every tree
- [ ] Browse line applied where livestock graze

## Sources

- [SpeedTree — product tiers and pricing](https://unity.com/products/speedtree) — Unity Technologies
- [Nanite Virtualized Geometry in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine) — Epic Games
- [Pivot Painter Tool in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/pivot-painter-tool-in-unreal-engine) — Epic Games
- [Creating and Using LODs in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/creating-and-using-lods-in-unreal-engine) — Epic Games
- [Colophospermum mopane](https://en.wikipedia.org/wiki/Colophospermum) — Wikipedia
- [Sclerocarya birrea (marula)](https://en.wikipedia.org/wiki/Sclerocarya_birrea) — Wikipedia
- [Hyphaene petersiana (makalani / real fan palm)](https://en.wikipedia.org/wiki/Hyphaene_petersiana) — Wikipedia
- [Diospyros mespiliformis (jackalberry)](https://en.wikipedia.org/wiki/Diospyros_mespiliformis) — Wikipedia
- [Vachellia erioloba (camelthorn)](https://en.wikipedia.org/wiki/Vachellia_erioloba) — Wikipedia
- [Schinziophyton rautanenii (mangetti / mongongo)](https://en.wikipedia.org/wiki/Schinziophyton) — Wikipedia
- [Terminalia sericea (silver cluster-leaf)](https://en.wikipedia.org/wiki/Terminalia_sericea) — Wikipedia
- Internal: `18_namibia_context/01_geography-and-regions.md`, `18_namibia_context/02_climate-and-weather.md`, `18_namibia_context/05_namibian-architecture.md`

## Open questions

- **Pivot Painter 2 technical detail** — material function names, texture import settings, UV channel usage. Epic's docs pages returned no body content. `needs-verification`.
- **Blender Pivot Painter equivalent** — the original is 3ds Max MAXScript; community Blender ports need evaluation. `needs-verification`.
- **The Grove** current price and Blender 5.2 compatibility. `needs-verification`.
- **Sapling Tree Gen** distribution status in Blender 5.2 (bundled vs extension). `needs-verification`.
- **Actual height and habit distribution of mopane at Okongo** — the shrub/tree split depends on local soil, and the site is on deep sand rather than the clay that produces mopane scrub. Requires site photographs.
- A verified list of the fruit and shade trees *planted* around Ohangwena homesteads (as opposed to wild species). Domain `18` flags this same gap.

