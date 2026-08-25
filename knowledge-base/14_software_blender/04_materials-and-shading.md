---
id: blender.materials
title: Materials, shading and texturing for architecture and joinery
domain: software_blender
tags: [blender, materials, principled-bsdf, pbr, uv, texel-density, wood-grain, glass, metal, polyhaven, ambientcg, asset-browser, colour-management]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Blender 5.2 LTS; Working Space colour management is 5.0+; Thin Wall on Principled BSDF is 5.2+"
unit_system: metric
sources:
  - {title: "Blender Manual — Principled BSDF", url: "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Color Spaces / Working Space", url: "https://docs.blender.org/manual/en/latest/render/color_management/color_spaces.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Normal Map Node", url: "https://docs.blender.org/manual/en/latest/render/shader_nodes/displacement/normal_map.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Smart UV Project", url: "https://docs.blender.org/manual/en/latest/modeling/meshes/editing/uv.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Asset Browser", url: "https://docs.blender.org/manual/en/latest/editors/asset_browser.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Poly Haven — Licence", url: "https://polyhaven.com/license", publisher: "Poly Haven", accessed: 2026-08-25}
  - {title: "ambientCG", url: "https://ambientcg.com/", publisher: "ambientCG (Lennart Demes)", accessed: 2026-08-25}
  - {title: "Blender Manual — Node Wrangler", url: "https://docs.blender.org/manual/en/latest/addons/node/node_wrangler.html", publisher: "Blender Foundation", accessed: 2026-08-25}
related: [blender.lighting_rendering, blender.geometry_nodes, blender.resources]
---

# Materials, shading and texturing for architecture and joinery

**Summary.** Blender materials are node graphs terminating in a Material Output. For architecture and furniture, 90 % of the work is one Principled BSDF node fed by a PBR texture set or by procedural noise, plus correct UVs at a consistent texel density. The remaining 10 % — glass, brushed metal, believable wood grain that runs the right way on every panel — is what separates a render that reads as a building from one that reads as a video game. This file covers the Principled BSDF inputs, procedural wood construction, UV strategy for building-scale objects, the free CC0 texture sources and their licences, and how to keep a project's materials in one asset library.

## Key facts

| Item | Value |
|---|---|
| Standard shader | Principled BSDF (`ShaderNodeBsdfPrincipled`) — layered: base (diffuse/metal/transmission/subsurface) → specular → coat → sheen, with emission below the coat |
| Key inputs | Base Color, Metallic, Roughness, IOR (default **1.5**, good for glass), Alpha, Normal |
| Sub-panels | Diffuse (Cycles-only Roughness → Oren-Nayar), Subsurface, Specular, Transmission, Coat, Sheen, Emission, Thin Film |
| Thin Wall (5.2+) | Renders single-surface glass, leaves and paper correctly without a second surface |
| Colour space of maps | Base Color / diffuse = **sRGB**; Roughness, Metallic, Normal, Displacement, AO, Alpha = **Non-Color** |
| Normal map convention | Blender is **OpenGL** (+Y up) by default; the Normal Map node has a `Convention` setting for DirectX (−Y) sources |
| Working Space (5.0+) | `Render Properties ▸ Color Management ▸ Working Space ▸ File` — Linear Rec.709 (default), Linear Rec.2020, ACEScg. **Choose once at project start.** |
| Colour ramp node | `ShaderNodeValToRGB` |
| Mix node | `ShaderNodeMix` (set `data_type` to `'RGBA'`, `'FLOAT'` or `'VECTOR'`) |
| Node Wrangler PBR setup | Select Principled BSDF, `Shift-Ctrl-T`, pick the texture files — it creates Image Texture nodes, sets colour spaces, and wires them |
| Node Wrangler preview | `Shift-Ctrl-LMB` on a node (Shader editor) |
| Asset libraries | `Preferences ▸ File Paths ▸ Asset Libraries` (`bpy.types.UserAssetLibrary`); browse in the Asset Browser editor |
| Poly Haven licence | **CC0** — any purpose, commercial included, redistributable, no attribution required |
| ambientCG licence | **CC0** — same terms |

## The Principled BSDF, input by input

The Principled BSDF is an "uber shader": a physically-motivated layer stack that covers almost every real material. The manual describes it as base layers with an optional glossy **coat** above and a **sheen** layer on top of everything, with emission below coat and sheen.

**Base Color.** The overall colour used for diffuse, subsurface, metal and transmission. From a texture, this is the `_Color` / `_BaseColor` / `_diff` map, set to **sRGB**. Real-world albedo is narrower than people expect: nothing in nature is darker than about 0.03 or brighter than about 0.9 linear. Painted white plaster is roughly 0.75–0.85; fresh concrete 0.35–0.45; oak 0.15–0.25; charcoal 0.03–0.05. Values outside that band destroy indirect lighting realism because they either eat or amplify every bounce.

**Roughness.** Microfacet roughness. 0.0 is a mirror; 1.0 is fully diffuse. The single most important input for making a render look real, and the one most often left flat. Real surfaces vary: a lacquered door is 0.05–0.15 with roughness *variation* from the polish; matt emulsion is 0.7–0.9; a screeded floor is 0.4–0.6 with wear patterns. Always feed roughness from a map or a procedural texture, never a constant, on anything larger than a light switch.

**Metallic.** A blend between dielectric and metal. It is effectively binary in reality: a surface is metal (1.0) or it is not (0.0). Intermediate values exist only to handle mixed-material texels in a texture map (a painted-and-worn steel gate). Metals take their reflection tint from Base Color and have no diffuse component.

**IOR.** Index of refraction for specular reflection and transmission. Default 1.5 — the manual notes this is a good approximation for glass. Water 1.33, acrylic 1.49, glass 1.45–1.55, diamond 2.42. Non-metals essentially all sit between 1.3 and 1.7.

**Alpha.** Transparency, 1.0 opaque. Usually driven from an image's alpha channel (set to Non-Color if separated). For foliage cut-outs and perforated screens.

**Normal.** Perturbs base-layer normals. Feed from a Normal Map node, not directly from an image.

**Sub-panel highlights.**

- *Subsurface* — for stone, marble, wax, skin, thin timber veneer against light. Set Weight, Radius (per-channel, in metres — this is why unit setup matters) and Scale.
- *Specular* — IOR Level and Tint. Leave IOR Level at 0.5 unless matching a measured material.
- *Transmission* — Weight 1.0 makes glass. Combine with Roughness for frosted glass.
- *Coat* — a clear varnish layer. Weight 1.0, Roughness 0.03–0.1 for a lacquered or polyurethane-finished cabinet door; the coat has its own Normal input so you can have a smooth varnish over a textured grain.
- *Sheen* — retro-reflective fuzz for fabric, dust and felt.
- *Emission* — Color and Strength (in Watts-equivalent radiance). For light fittings, screens, LED strips.
- *Thin Film* — iridescence.
- **Thin Wall (5.2+)** — tick this for single-plane glass, blinds, paper lampshades and leaves. Before 5.2, single-surface glass rendered incorrectly in Cycles and needed a modelled thickness.

## Node-based shading: what to actually build

A production architectural material is rarely more than:

```
[Texture Coordinate] → [Mapping] → [Image Texture ×4] → [Principled BSDF] → [Material Output]
                                    ├ BaseColor (sRGB)       → Base Color
                                    ├ Roughness (Non-Color)  → Roughness
                                    ├ Metallic  (Non-Color)  → Metallic
                                    └ Normal    (Non-Color)  → [Normal Map] → Normal
```

Node Wrangler builds this for you: select the Principled BSDF, press `Shift-Ctrl-T`, and pick the whole texture set at once. The manual states it detects the map type from filenames, loads the images, selects the appropriate colour space and connects everything; the filename tags are editable in the add-on preferences, so if your supplier uses `_rgh` instead of `_roughness` you add the tag once.

Use the **Mapping** node's Scale to set real-world tiling. A brick texture representing a 2 × 2 m patch, on a 6 m wall UV-unwrapped at 1:1, needs Scale = 3. Getting this right is the same problem as texel density, below.

**Procedural vs textured.** Use procedural for anything where tiling would be visible or where you need infinite resolution: plaster, painted walls, concrete, brushed metal, and — importantly — wood grain that must follow the panel. Use scanned PBR sets for anything with complex real-world structure: brick, natural stone, paving, fabric, ceramic tile, roof sheeting. Mix them: a scanned brick base with a procedural grime gradient on the roughness.

## UV unwrapping for architecture

Architecture has thousands of square metres of flat surface and almost no organic form, so the organic-modelling unwrapping advice does not apply.

**Box / Cube Projection** (`UV ▸ Cube Projection` in Edit Mode) projects from six directions with a given cube size. On a box-shaped building, a wall, a slab or a cabinet panel it produces a perfect, undistorted, seam-free-enough unwrap in one keystroke. Set `Cube Size` to a round number in metres and every object shares a coordinate system.

**Smart UV Project** for anything more complex. Its options that matter: *Angle Limit* (higher = fewer, larger islands with more distortion), *Margin Method* set to **Fraction** so Island Margin is a real texel count (1/1024 on a 1024 px texture gives a 1 px gutter), *Rotation Method*, and *Correct Aspect* for non-square textures.

**Object-space coordinates instead of UVs.** For repeating architectural surfaces, skip UVs entirely: Texture Coordinate ▸ **Object** or **Generated** into Mapping into the texture. Object coordinates are in the object's local metres, so a Mapping Scale of `(1,1,1)` means one texture repeat per metre — dimensionally exact, no unwrapping, no seams. This is the right default for plaster, concrete and paint. It fails on curved or deformed geometry and cannot carry baked detail, which is when you unwrap properly.

**Texel density.** The number of texture pixels per real-world metre. Consistency matters more than the absolute number: if the floor is 512 px/m and the wall is 128 px/m, the wall looks blurry next to the floor no matter how good the texture is.

| Use | Texel density | Meaning |
|---|---|---|
| Hero close-up joinery, worktops | 1024 px/m | A 2048 px texture covers 2 m |
| Interior walls, floors, general | 512 px/m | A 2048 px texture covers 4 m |
| Exterior building surfaces | 256 px/m | A 2048 px texture covers 8 m |
| Distant context, terrain | 64–128 px/m | |

To set it, unwrap, then scale the UV island so that a known real dimension maps to the intended fraction of the 0–1 space. A 4 m wall at 512 px/m on a 2048 px map should occupy exactly the full 0–1 range. Blender has no native texel-density readout; the standard practice is to make a **UV grid test material** (`Image ▸ New ▸ Generated Type: UV Grid` or `Color Grid`), apply it to everything, and check by eye that the squares are the same size across every surface and are not stretched. Do this before texturing, not after.

For **UDIMs** — multiple 1001, 1002… tiles — Blender supports them natively via `Image ▸ Source: UDIM Tiles`. Worth it on a large hero interior; overkill for most residential work. Note the USD exporter cannot pack UDIM textures into a USDZ archive.

## Displacement vs bump vs normal

Three ways to fake or create surface relief, in increasing cost:

- **Normal map** — an RGB image encoding a perturbed normal in tangent space. Cheapest, no silhouette change, no self-shadowing. Feed through a Normal Map node with Space = Tangent and the image set to Non-Color. Blender uses the **OpenGL** convention (+Y up, green channel points up); the node's `Convention` setting switches to DirectX for maps authored elsewhere. The UV map named on the Normal Map node must match the one used by the image texture.
- **Bump map** — a greyscale height image converted to a normal perturbation at render time by a Bump node. Slightly more expensive, no extra maps needed, and easy to derive from a procedural. Use for fine grain, brush marks and dust.
- **Displacement** — actually moves geometry. In Cycles, plug into Material Output ▸ Displacement and set the material's Settings ▸ Displacement to `Displacement Only` or `Displacement and Bump`; enable Adaptive Subdivision on the object (standard from Blender 5.0, with an Object Space option). Changes silhouettes and self-shadows correctly. Expensive. Reserve it for hero elements: a rough-cut stone plinth, a heavily raked bagged wall, deep-profile roof sheeting seen at grazing angles.

Rule of thumb: normal map for everything, bump added for micro-detail, displacement only where the silhouette matters.

## Wood grain for joinery

Believable timber has four ingredients: a long-axis stretched noise for the grain, a ring structure, colour variation between boards, and per-board grain direction.

**Procedural construction** (a solid oak / meranti / pine door rail):

1. **Texture Coordinate ▸ Object** → **Mapping**. Set Mapping Scale to something like `(1, 30, 30)` so the pattern is stretched enormously along the board's local X (the grain direction) and tight across it.
2. **Noise Texture** (Scale ~6, Detail ~8, Roughness 0.55) → this is the grain wander.
3. **Wave Texture** (`ShaderNodeTexWave`), Type = **Bands**, Profile = **Sine** or **Saw**, Direction = X, Scale ~2, Distortion 8–20, Detail 3, Detail Scale 2. Feed the Noise output into the Wave's Distortion or add it to the Vector — this is what turns straight bands into cathedral figure.
4. **ColorRamp** (`ShaderNodeValToRGB`) on the Wave output, with 4–6 stops sampled from a photo of the actual species. Constant interpolation on two stops gives crisp early/late wood; B-Spline gives soft blending. Output → Base Color.
5. A second, tighter **Noise** → ColorRamp → **Roughness** (range roughly 0.25–0.45 for an oiled finish, 0.05–0.12 under lacquer). Late wood is slightly rougher than early wood; this is the detail that sells it.
6. The same wave/noise combination → **Bump** node (Strength 0.05–0.15, Distance 0.0005 m) → Normal. Real open-grain oak has 0.1–0.3 mm of texture.
7. Optional **Coat** Weight 1.0, Coat Roughness 0.05 for a lacquered finish.

**Per-board variation.** Two mechanisms:

- *Object coordinates* already give each separate object its own grain origin, so a run of separate slats is automatically varied.
- *Instances or a single mesh*: store a random value per panel with Geometry Nodes' Store Named Attribute, read it in the shader with an **Attribute** node, and use it to offset the Mapping Location and to shift the ColorRamp — one material, forty visibly different boards.

**Grain direction.** This is the thing most renders get wrong. On a real carcass, the grain on a side panel runs vertically, on a top panel it runs front-to-back or left-to-right depending on the cutting list, and on a door it runs vertically on stiles and horizontally on rails. Because the procedural above is driven by **object local coordinates**, grain follows the object's own axes: model every panel with its length along local X and orient the object, and the grain is automatically correct. Store the intended grain direction as a custom property (`obj["grain"] = "length"`) so the cutting-list script (file `06`) can output it for the workshop.

**Textured alternative.** For veneers and melamine, a scanned set from ambientCG or a decor manufacturer's own image is faster and more accurate. Use Cube Projection so the grain runs along the panel, and vary the Mapping Location per panel as above.

## Glass and metal

**Glass.** Two valid approaches:

- *Principled with Transmission* — Transmission Weight 1.0, Roughness 0.0, IOR 1.5, Base Color near white with a faint green-cyan tint for float glass (a 6 mm pane is roughly `(0.87, 0.94, 0.90)`). For a modelled double-glazed unit, model both panes with a real cavity. For a single-surface pane, enable **Thin Wall** (5.2+).
- *Architectural "fake" glass* for interiors seen from outside — a Transparent BSDF mixed with a Glossy BSDF by a Fresnel node, or simply Principled with Transmission and the material's Settings ▸ Ray Visibility ▸ Shadow disabled. Cheaper, no caustics, and stops interiors going black.

In Cycles, tick `Render Properties ▸ Light Paths ▸ Caustics ▸ Reflective/Refractive` off for architectural work unless you specifically want caustics; they are the main source of fireflies in glazed scenes. `Filter Glossy` at 0.5–1.0 also helps.

**Metal.** Metallic 1.0, Roughness driven by a map, Base Color set to the measured F0 reflectance:

| Metal | Approximate linear sRGB base colour |
|---|---|
| Aluminium | 0.91, 0.92, 0.92 |
| Steel / iron | 0.56, 0.57, 0.58 |
| Chrome | 0.55, 0.56, 0.55 |
| Copper | 0.95, 0.64, 0.54 |
| Brass | 0.89, 0.73, 0.40 |
| Gold | 1.00, 0.77, 0.34 |

Brushed metal = an anisotropic roughness: use the Anisotropic and Anisotropic Rotation inputs with a Tangent node, or fake it with a stretched noise into Roughness. Powder-coated aluminium (the common Namibian window frame) is **not** metal: Metallic 0.0, Roughness 0.35–0.5, Base Color the RAL colour, plus a light Coat.

## Free PBR sources and their licences

| Source | URL | Licence | Content |
|---|---|---|---|
| **Poly Haven** | https://polyhaven.com | **CC0** — any purpose including commercial, redistributable, no attribution required | HDRIs, PBR textures, 3D models |
| **ambientCG** | https://ambientcg.com | **CC0** — free for personal and commercial use, redistribution permitted | PBR textures to 8K, photogrammetry materials, HDRIs, Substance source files |
| **Blender Essentials** | Bundled / online (5.2+) | Ships with Blender | Parametric materials, HDR backgrounds, compositing effects, downloaded on demand |
| **Blender Studio** | https://studio.blender.org | Subscription €11.50/month; asset licence not stated on the welcome page — **verify per asset** | Production assets and training |

> CC0 means you may use the textures in client work, embed them in a delivered `.blend`, and resell renders, with no attribution obligation. Note the distinction Poly Haven draws: the **assets** are CC0, but the site's own logos, promotional renders and copy remain copyrighted.

Do not assume every "free" texture site is CC0. Many are CC-BY (attribution required) or "free for personal use" (unusable for a paid Namibian residential project). Record the licence of every downloaded set in the project folder.

The Poly Haven asset browser add-on (file `08`) and the Blender MCP integration both pull Poly Haven assets directly into the Asset Browser, which is the fastest route from "I need a plaster texture" to a shaded wall.

## Material libraries and the Asset Browser

The Asset Browser is Blender's library front-end. Workflow:

1. Build materials in a dedicated `project_materials.blend`.
2. Right-click each material in the Outliner or the Material Properties dropdown ▸ **Mark as Asset**. A preview is generated automatically.
3. Organise with **catalogs** (`Masonry / Plaster`, `Timber / Solid`, `Timber / Veneer`, `Metal / Powdercoat`, `Glass`, `Paving`). Catalogs are stored per library and merge when bundles are copied.
4. Fill in the Asset Details region: description, author, tags, and a custom preview (`Load Custom Preview`, or the screenshot capture operator) where the auto preview is unhelpful.
5. Add the containing folder in `Preferences ▸ File Paths ▸ Asset Libraries` and give it a name.
6. In any project file, open an Asset Browser, pick the library, and drag a material onto an object.

For a shared library across a practice, put the folder on a network share or in version control. **Asset bundles** — self-contained `.blend` files ending in `_bundle.blend` with all textures packed — are the portable distribution format; the Asset Browser's *Copy Bundle to Asset Library* copies one in and merges its catalogs.

Linking vs appending matters: dragging in *links* by default, so a change in the library propagates. If you need to edit locally, `Object ▸ Relations ▸ Make Local ▸ Selected Objects` makes the object local while keeping the mesh and materials linked — the manual's own recommended pattern.

## Colour management for materials

From Blender 5.0 there is a per-file **Working Space** (`Render Properties ▸ Color Management ▸ Working Space ▸ File`): Linear Rec.709 (default), Linear Rec.2020, or ACEScg. It governs all scene-linear colours, and all shader, compositor and geometry-node processing. The manual is emphatic: **choose it at the start of a project and use the same one for every file in that project.** Conversion between working spaces is only approximate and needs manual fix-ups.

For ordinary architectural work delivered as sRGB JPEGs and PDFs, the default Linear Rec.709 is correct. Choose ACEScg only if you are integrating with a film pipeline that demands it.

Per-texture colour space is separate and is set on each Image Texture node. Getting it wrong is the single most common cause of "my render looks wrong and I don't know why": a roughness map left on sRGB is gamma-decoded and every roughness value is wrong.

## Sources

- [Manual — Principled BSDF](https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html) — accessed 2026-08-25 via the version-matched local manual bundle
- [Manual — Color Spaces and Working Space](https://docs.blender.org/manual/en/latest/render/color_management/color_spaces.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Normal Map node](https://docs.blender.org/manual/en/latest/render/shader_nodes/displacement/normal_map.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Environment Texture node (colour space guidance)](https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/environment.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — UV Operators: Smart UV Project](https://docs.blender.org/manual/en/latest/modeling/meshes/editing/uv.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Asset Browser](https://docs.blender.org/manual/en/latest/editors/asset_browser.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Node Wrangler (Add Principled Texture Setup, `Shift-Ctrl-T`)](https://docs.blender.org/manual/en/latest/addons/node/node_wrangler.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Wave Texture node](https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/wave.html) — accessed 2026-08-25 via the local manual bundle
- [Poly Haven licence](https://polyhaven.com/license) — accessed 2026-08-25
- [ambientCG](https://ambientcg.com/) — accessed 2026-08-25
- [Blender Studio](https://studio.blender.org/welcome/) — accessed 2026-08-25

## Open questions

- The metal base-colour table and the albedo ranges are widely used industry reference values, not values taken from Blender documentation — treat as guidance, **needs-verification** against a measured source if colour accuracy is contractual.
- Texel-density figures are conventions from production practice, not documented Blender defaults.
- The licence attached to Blender Studio's downloadable production assets is not stated on the welcome page; check each asset's own page before using one in paid client work.

