---
id: envasset.principles
title: Principles of photorealistic environments
domain: 25_environmental_asset_creation
tags: [photorealism, reference, scale, light-physics, fresnel, roughness, subsurface-scattering, weathering, tiling, atmospheric-perspective, camera-realism, environment-art]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Unreal Engine 5.8, Blender 5.2 LTS. Physical values are general photometry/optics, not vendor-specific."
unit_system: SI
sources:
  - {title: "Physically Based Materials", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Blender Manual — Principled BSDF", url: "https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Sky Texture Node", url: "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/sky.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Daylight", url: "https://en.wikipedia.org/wiki/Daylight", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Atlas of Namibia, Chapter 3 — Climate", url: "https://atlasofnamibia.online/chapter-3", publisher: "Atlas of Namibia", accessed: 2026-08-25}
related: [envasset.overview, envasset.reference_scanning, envasset.rocks_surfaces, envasset.lookdev, ue.archviz_workflow, blender.materials_shading, namibia.climate]
---

# Principles of photorealistic environments

**Summary.** An environment reads as real when a viewer's unconscious model of the world is not contradicted. That model is built from millions of observed relationships — how bright a shadow is relative to sunlight, how a surface changes at grazing angles, how dust accumulates, how a lens fails. Photorealism is therefore an exercise in *not being caught*: every default value in every DCC application is a small lie, and the work is finding and correcting them. This file lists the corrections in the order they matter, with the specific numbers, node names and settings to act on. Every point ends in something you can do.

## Key facts

| Quantity | Value | Why it matters |
|---|---|---|
| Direct sunlight illuminance, clear sky, high sun | **~100 000–120 000 lux** | The Directional Light value in Unreal; anything much lower reads as an overcast day |
| Clear blue sky (no sun), horizontal | **~10 000–25 000 lux** | Sky is 5–10× dimmer than sun; this ratio *is* the look of a desert |
| Overcast day | **~1 000–20 000 lux** | Two decades of range; "overcast" is not one condition |
| Full moon | **~0.1–0.3 lux** | Roughly 10⁶× dimmer than sun — night scenes need real exposure, not blue tint |
| Dielectric (non-metal) specular reflectance at normal incidence | **~0.02–0.08** (4% typical) | Anything else is wrong; this is why UE's default Specular is 0.5 → 4% |
| Fresnel reflectance at 90° grazing | **→ 1.0 for every material** | Every surface becomes a mirror at glancing angles |
| Fresh snow albedo | ~0.80–0.90 | Upper bound of natural diffuse albedo |
| Pale dry quartz sand albedo | **~0.30–0.45** | Kalahari sand is a *bright* bounce source, not a dark one |
| Dry grass / straw albedo | ~0.15–0.25 | Reads much darker than sand next to it |
| Fresh asphalt albedo | ~0.04–0.09 | The darkest common outdoor material |
| Coal / charcoal albedo | ~0.04 | Practical floor for any albedo texture |
| Human eye height, standing adult | **1 600 mm** | The default camera height for any believability check |
| Sun angular diameter | **0.53°** | Blender Sun lamp Angle default 0.526°; shadow softness follows from this |

> ⚠️ Two numbers do more damage than all others when wrong: **albedo below 0.03 or above 0.90**, and **sky-to-sun ratio**. No real diffuse surface is blacker than ~0.03 or whiter than ~0.90. If a texture has 0,0,0 pixels, the shading breaks — no bounce light, crushed blacks, and a hole in the image the eye reads instantly.

---

## 1. Observed reference, and the discipline of gathering it

**The principle.** You cannot render what you have not looked at. The single strongest predictor of whether an environment reads as real is whether the artist had photographs of the specific thing in front of them while working.

**What "reference" actually means here.** Not "an inspiring image". A reference set for a Namibian residential exterior is:

- **The site itself**, photographed at 08:00, 12:00 and 17:00 on a clear day, from a fixed tripod position, at a known focal length, with a colour chart in one frame of each set.
- **Material close-ups**: sand at 300 mm, sand at 3 m, sand drifted against a wall, sand with tyre tracks, the shadow edge of a wall on sand, calcrete nodules, a mopane trunk from 500 mm, grass in September vs March.
- **Detail-of-detail**: the corner where the wall meets the ground, the rain splash line at 300 mm above ground, the dust film on a window sill, the rust bloom at a gate hinge.
- **Wide shots for value relationships** — how dark is the shadow *really* compared to the sunlit sand? Expose one frame for the highlights so you can measure it.
- **Negative reference**: photographs of the same landscape that look *bad* or *fake*, which tell you what to avoid.

**Actionable.**
1. Build a `_ref/` folder inside the project, mirroring the asset folder structure (see `08`). `_ref/Materials/Sand/`, `_ref/Foliage/Mopane/`.
2. Use PureRef (free for personal use; paid licence available) or a Blender scene with reference image empties. Keep it on a second monitor, always visible.
3. For each hero asset, pin **at least three** reference photos before modelling: silhouette, surface detail, and the asset in context with something of known size.
4. Photograph a **grey card or colour chart** in at least one frame per lighting condition. Without it, every subsequent colour judgement is guesswork. See `02`.
5. Record EXIF: focal length, aperture, shutter, ISO. These become your virtual camera settings in `09`.

**The tell if you skip it.** Invented proportions. Trees that are the "idea" of a tree. Sand that is orange because deserts are orange in films. Shadow colours that are grey rather than sky-blue.

---

## 2. Real-world scale and human reference

**The principle.** Scale is not a number, it is a set of relationships the viewer already knows. Depth of field, atmospheric haze, texture frequency and light falloff all encode scale, and if the geometry lies, they all lie together and the image reads as a miniature.

**Actionable.**
1. **Fix units first.** Blender: Scene Properties → Units → Metric, Unit Scale 1.0, Length Metres. Unreal: 1 uu = 1 cm, non-negotiable. Fusion: internal API units are **centimetres and radians**, though the UI shows mm — see `07`.
2. **Keep a scale figure in every scene.** A 1 750 mm biped mesh, always visible, always at the origin of a check. In Unreal the default `SM_Mannequin` or a simple 1 750 mm capsule.
3. **Memorise the calibration set** and check assets against it: door leaf 900 × 2 100 mm; brick 222 × 106 × 73 mm (SA/NA standard) — confirm against domain `07_materials_and_suppliers`; standard corrugated sheet pitch 76 mm (IBR) or 32 mm corrugate; 1 200 mm balustrade height; 2 400 mm ceiling; car 4 400 × 1 800 × 1 500 mm; wheelbarrow 1 400 mm long.
4. **Vegetation scale is the most commonly wrong.** Mature mopane 4–8 m in this region (it is a shrubby form on poor sand, not the 18 m Zambezi form); marula 9–18 m; makalani palm 10–20 m with a fronded crown 3–5 m across. Grass tussocks 300–900 mm. Getting the grass 2× too tall makes the house look like a model.
5. **Texel density is a scale statement.** A ground texture at 512 px/m and a wall at 1024 px/m puts the wall visually closer. See `08 §Texel density`.
6. **Check at 1 600 mm eye height before checking from a drone.** Most CG environments are composed from an aerial position where scale cues are weakest.

---

## 3. The physics of light

### 3.1 Inverse square

Illuminance from a point source falls as 1/d². Doubling distance quarters the light. In Unreal this requires **Inverse Squared Falloff** enabled on point/spot lights (it is the default with physical units); with it off you get a fake linear falloff that instantly reads as a game.

**Actionable.** Never use Attenuation Radius as a brightness control — it is a hard clamp for culling. Set it generously (2–5× the visible falloff), and control brightness with lumens/candela.

The sun is *not* subject to inverse square in practice: at 150 million km, the falloff across a scene is zero. Directional lights are correct.

### 3.2 Energy conservation

A surface cannot reflect more light than it receives. This is enforced by the Principled BSDF and Unreal's PBR model, but you can defeat it with:

- Emissive values used to "brighten" a diffuse surface.
- Albedo textures with clipped whites.
- Ambient/fill lights added to compensate for exposure error.

**Actionable.** Clamp every albedo texture to the range **0.03–0.90 linear** (sRGB roughly 45–243 in 8-bit terms). In Blender, a `Map Range` node on the base colour during authoring; in Substance Designer, a `Levels` node. Verify with a colour picker on the darkest and lightest pixel.

### 3.3 The colour of bounce light

Light takes the colour of what it bounces off, and multiplies with it on the second bounce. In Ohangwena this is decisive: **pale quartz sand at ~0.35 albedo throws a strong, warm, bright fill light upward**. Under-eave soffits, the undersides of window reveals, and the lower half of every north-facing wall are lit by sand, not by sky. This is the opposite of the temperate default where bounce comes from green grass and is dim.

**Actionable.**
1. Use a GI system that actually solves it — Lumen in Unreal (`Project Settings → Rendering → Global Illumination → Lumen`), Cycles in Blender. EEVEE's screen-space GI is not sufficient for this and will under-light soffits.
2. Set Lumen's **Final Gather Quality** ≥ 2 and **Max Trace Distance** to at least the site diagonal, for still frames.
3. Do not "correct" the warm underside colour. It is right. If it looks wrong, your white balance is wrong (§9).
4. In Blender Cycles, ensure the ground plane extends well beyond frame — bounce from a truncated ground plane is a classic cause of a dark, floating building.

### 3.4 Sky vs sun ratio

The ratio of sun illuminance to sky illuminance defines the *hardness* of a landscape. A clear dry-season Ohangwena day is roughly **100 000 lux sun : 15 000 lux sky ≈ 7:1**. An English overcast day is 0:1 — all sky. A hazy tropical coast might be 3:1.

**Actionable.**
- Unreal: Directional Light 100 000–120 000 lx, Sky Light 3 000–10 000 cd/m², Real Time Capture on. (Values from domain `13`, file `04`.)
- Blender: Sun strength in W/m² — a physical clear-sky value is ~1 000 W/m² normal irradiance, but Blender's Sun `Strength` is irradiance in W/m² and a value of **3–6** with the Nishita/Multiple Scattering sky is the usual practical range when Film Exposure is 0. Prefer to let the **Sky Texture** drive both sun and sky: set Sky Type to *Multiple Scattering*, enable Sun Disc, and the model produces a physically consistent ratio automatically. The manual warns these skies are "very bright by default (hence accurate)" and to lower scene Exposure rather than the sky strength.
- If the shadows look too soft or too filled, the ratio is wrong, not the shadow settings.

### 3.5 The specific character of tropical, high-altitude sun

Okongo is at **17.57°S and ~1 150 m**. The consequences:

- **The sun is very high.** Noon altitude ranges 49.2° (21 June) to 90.0° (around 8 November and 1 February, when it passes directly overhead) to 84.0° (21 December). For most of the year, shadows at midday are *short and directly below objects*. A tutorial-standard 45° key light is a morning or late-afternoon condition here, not a midday one.
- **Between about 8 November and 1 February the noon sun is to the SOUTH.** North-facing shading logic inverts for the hottest quarter.
- **Altitude thins the atmosphere.** Less Rayleigh scattering means a **deeper, more saturated blue zenith** and a harder shadow edge with less scattered fill near the sun.
- **The dry season is exceptionally clear.** May to September is dominated by subsiding anticyclonic air — cloudless, low humidity (relative humidity below 20% at 14:00 east of the escarpment). Atmospheric perspective at 1–2 km is minimal; at 10 km+ it is significant.
- **The wet season is different.** November–April brings cumulus, higher humidity (~80% at 08:00 in northern Namibia in the wettest months), and the *lowest* solar irradiance in the country despite the highest sun. Do not render a February scene with a January-dry-season sky.

**Actionable.** Choose and declare the date and time of every shot. Write it into the level name: `L_House_Ext_1400_Aug`. Then set sun position from real solar geometry (Unreal SunSky plugin with Latitude −17.4, Longitude 17.6, Time Zone +2, DST off; or the Python solar script in domain `14` file `05`). Solar noon at Okongo is about **12:50 local clock time**, not 12:00.

---

## 4. Material response

### 4.1 Fresnel

Every dielectric surface reflects ~4% at normal incidence and ~100% at grazing angles. This is not an artistic effect; it is why a road ahead of you looks wet on a hot day and why a matte wall shows a bright rim when the sun is behind it.

**Actionable.**
- Unreal: leave **Specular at 0.5** for all dielectrics unless you have a measured IOR. Do not use Specular as a shininess control — that is what Roughness is for. Use Specular below 0.5 only to kill reflections on a surface occluded from the environment (e.g. deep inside a crevice), and drive it from an AO/cavity map.
- Blender: Principled BSDF **IOR 1.45–1.5** for most dielectrics; 1.33 water; 1.5 glass; 1.55 quartz sand grains. Metals get Metallic = 1.0 and take their reflectance from Base Color.
- Verify grazing behaviour by orbiting the camera to near-tangent on a flat surface. If nothing brightens, Fresnel is being suppressed somewhere.

### 4.2 Roughness variation is the whole game

Uniform roughness is the most common single reason a material reads as CG. Nothing in the real world has one roughness value across its surface.

**Actionable.**
1. Every material gets a **roughness texture**, never a constant — even if that texture is a mild procedural noise at 0.55–0.72.
2. Break roughness at **three frequencies**: micro (grain of the material), meso (wear patterns, dirt), macro (whole-surface variation over metres). Layer three noises at different scales and different amplitudes.
3. Roughness and albedo should be **correlated but not identical**. Dust makes a surface both lighter and rougher; water makes it darker and smoother. Drive both from the same mask with different remaps.
4. Real roughness values: polished glass 0.0–0.05; painted smooth wall 0.3–0.5; plastered wall 0.55–0.75; weathered timber 0.7–0.9; dry sand **0.85–0.95**; wet sand 0.35–0.55; galvanised steel new 0.25–0.4; galvanised steel weathered 0.5–0.7; rusted steel 0.75–0.9.
5. **Never author a fully 0.0 or 1.0 roughness.** Clamp to 0.03–0.97.

### 4.3 Microsurface and the normal/roughness relationship

Roughness *is* a statistical statement about normals below pixel size. If you mip-map a normal map without also adjusting roughness, distant surfaces lose their microstructure and become mirror-smooth — a well-known "specular aliasing" artefact seen as shimmering on distant roofs and metal.

**Actionable.**
- Unreal: enable **Composite Texture** on the base-colour or roughness texture, set `Composite Texture Mode = CTM_RoughnessFromNormalAlpha` and assign the normal map as the composite texture. This bakes normal variance into the roughness mip chain.
- Alternatively enable `Project Settings → Rendering → Normal maps → Sharpen` off and rely on TSR; but the composite-texture route is the correct fix.
- Blender/Cycles: use a **Bump** node with a small distance rather than pushing normal strength, and let adaptive sampling handle it; or bake a roughness map that already includes the variance.

### 4.4 Subsurface scattering

Light enters, scatters inside, and exits somewhere else. Governs leaves, skin, thin plastic, marble, wax, and — importantly for this project — **thatch, dry grass and thin foliage backlit by a low sun**.

**Actionable.**
- Unreal: use the **Subsurface** or **Two Sided Foliage** shading model for leaves. `Two Sided Foliage` is the correct one for thin single-sided leaf cards — it takes a *Subsurface Color* input and transmits light through the card. Set the Subsurface Color to a *desaturated, slightly warmer and lighter* version of the leaf albedo, not a saturated green.
- Blender: Principled BSDF **Subsurface Weight** 0.05–0.2 for leaves with Radius around (0.004, 0.002, 0.001) m; or in Blender 5.x use **Thin Wall** mode on the Principled BSDF for genuinely thin geometry (leaves, blinds, glass panes), which is the physically correct treatment for single-surface sheets.
- The tell if you skip it: backlit trees look like black cardboard cutouts. Backlit foliage at golden hour is one of the highest-value realism wins available.

---

## 5. Surface history — the storytelling layer

Real surfaces record what has happened to them. Every one of these is a *mask* driving a blend between two material states.

| Phenomenon | Physical driver | Mask to author | Where it appears in Ohangwena |
|---|---|---|---|
| Sun bleaching | UV degradation | World-space up-vector + a north/south bias | Top faces of everything; the north (equator-facing for most of the year) side of painted walls; plastic and paint fade fastest |
| Dust accumulation | Gravity + wind | World normal Z, plus windward-side bias | Horizontal ledges, window sills, tops of walls, the base of everything. This is the dominant weathering effect here |
| Wind-driven sand abrasion | Saltating quartz grains | Windward face mask (prevailing wind), height 0–600 mm | Polished/eroded lower 300–500 mm of walls, posts and gate frames |
| Water staining | Runoff paths | Inverted-Z, curvature, drip-point sources | Below gutter joints, window sills, roof edges. Short but violent in the November–April wet season |
| Splash line | Rain hitting ground and bouncing | Height band 0–350 mm above grade | A distinct dirt band on every wall base; almost universal and almost never modelled |
| Edge wear | Contact abrasion | Curvature/convexity map | Gate latch, door handle heights, step nosings, threshold plates |
| Rust bloom | Fe + O₂ + H₂O | Curvature + downward-flow + scratch mask | Steel gates, burglar bars, roof fixings. Low humidity slows it; near the *iishana* saline conditions accelerate it |
| Biological growth | Shade + moisture | Inverted AO/cavity + downward-Z | Rare here in the open, present in permanently shaded courtyard corners and near tap drips |
| Thermal crazing | Extreme drying | Fine random cellular noise | Concrete slabs and plaster cured in high evapotranspiration — an authentic Namibian detail (see domain `18`) |

**Actionable.**
1. In Unreal, build a **master weathering material function** taking `WorldAlignedNormal.B` (up-facing), a `PixelDepth`-independent world-position noise, and a vertex-colour channel; output a 0–1 dust mask. Reuse it across every exterior material via material instances.
2. In Blender, bake **Pointiness** (Geometry node → Pointiness) into a vertex colour or a texture for curvature-driven edge wear; bake **AO** for cavity dirt.
3. In Substance Painter, the corresponding generators are `Dirt`, `Curvature`, `Mask Editor`, `Water Level` — these are the standard names.
4. **Vertex colour is the cheapest per-instance variation** you have. Paint dust density per placed mesh in Unreal's Mesh Paint mode so two identical gate meshes weather differently.

---

## 6. Imperfection and asymmetry

**The principle.** Nothing built or grown is symmetrical or straight at the scale the eye can see. A CG fence has posts at exactly 2 000 mm centres, exactly vertical, exactly the same height. A real palisade — the defining boundary type of an Owambo homestead (see domain `16` and domain `18` file `05`) — has hundreds of hand-cut poles, none plumb, none the same diameter, none the same height, spaced by eye.

**Actionable.**
1. **Randomise per instance**: rotation ±3° on all axes, uniform scale 0.92–1.08, and a Z-offset of ±15 mm to break the ground plane. In Unreal's Foliage tool these are `Random Pitch Angle`, `Scale X/Y/Z` min/max, and `Z Offset`. In Blender Geometry Nodes: `Random Value` → `Rotate Instances` / `Scale Instances`.
2. **Randomise the mesh, not just the transform.** Three to five variants of a palisade pole beats one pole rotated randomly, because rotation does not change the silhouette of a cylinder.
3. **Vary the colour per instance.** Unreal: `PerInstanceRandom` node into a hue/value shift. Blender: `Object Info → Random` into a Color Ramp. A ±6% value shift and ±4° hue shift is enough.
4. **Add deliberate faults.** One pole leaning, one missing, one repaired with wire. The eye reads intentional imperfection as history.
5. **Never mirror a hero asset.** Mirrored normal maps and mirrored dirt are visible.
6. **Bend straight lines.** A 12 m boundary wall should deviate 20–40 mm from true over its length. Use a subtle lattice or a bend modifier.

---

## 7. Tiling and repetition — the primary CG tell

At exterior scale this is *the* problem. A 2 m sand texture across a 40 m yard repeats 400 times in plan; the eye finds the pattern immediately, and the moment it does, the whole image collapses.

Techniques, roughly in order of cost and effectiveness:

1. **Macro variation.** Multiply the albedo by a very large-scale (30–100 m) low-contrast noise, ±10–15% in value and a few degrees in hue. Cheapest, highest impact, do it always.
2. **Detail normal / detail albedo at a different scale.** Overlay a second tiling at ~1/8 the primary UV scale to break the mid-frequency rhythm. Unreal: `DetailTexturing` material function or a manual `Add` of a second normal via `BlendAngleCorrectedNormals`.
3. **Distance-based tiling break-up.** Blend to a larger UV scale beyond ~15 m so distant ground does not shimmer with high-frequency repeats. Drive with `PixelDepth` → `Divide` → `Saturate` → `Lerp` between two `TexCoord` scales.
4. **Stochastic / hex-grid sampling.** Sample the texture three times at randomly offset UVs on a hexagonal lattice and blend by barycentric weight. Unreal ships `TextureVariation` / the `Texture Bombing` approach in material function form; Blender 5.x has **Texture Coordinate → Object** plus the `White Noise` node, or the built-in `Image Texture` node's *stochastic* interpolation where available. Cost: 3× texture fetches.
5. **Layer blending with height.** Use `Landscape Layer Blend` with `LB Height Blend` so the transition between sand and gravel follows a heightmap rather than a straight alpha — this breaks the *outline* of the repeat as well as its interior.
6. **Break with objects.** Scattered debris, tussocks, tyre tracks, a wheelbarrow, drifted leaf litter. Cheaper than any shader trick and more convincing.
7. **Vertex-painted variation** on the landscape itself.
8. **Runtime Virtual Texture** — bake the composited landscape material into an RVT and sample it from meshes so rocks, plinths and paving blend into terrain colour. This kills both the repeat and the "pasted-on object" tell at once.

**The diagnostic.** Render a top-down orthographic view of the ground at 4K and look at it as a flat image. Any pattern visible there is visible in perspective too.

---

## 8. Colour variation

Real materials are not one colour. Sand contains quartz, feldspar, iron-stained grains and organic fragments; a plastered wall has patch repairs and differential drying; grass is a mixture of green, straw, grey and black seed heads.

**Actionable.**
1. Author base colour with **hue variation of ±5–10°**, not just value variation. Value-only variation looks like a dirty greyscale.
2. Use a **three-colour ramp** driven by noise rather than a single tint: for Kalahari sand, a pale grey-cream (approx. sRGB #D8CDB6), a warmer ochre (#C4A87E) and a darker iron-stained tone (#8E7452), mixed by two noise octaves. Verify against your own site photographs — these are indicative, not measured.
3. Beware **saturated shadows**. Shadow colour comes from sky (blue) plus bounce (warm sand). The net is a *desaturated warm-neutral*, not blue. Over-blue shadows are the classic desert-render mistake.
4. Check colour with a **false-colour or luminance-only view** to confirm the value structure works before judging hue.

---

## 9. Atmospheric perspective and haze

Air scatters. Distant objects lose contrast, shift toward the sky colour, and lose saturation. This is the strongest depth cue available and the one CG most often omits — an environment with perfectly crisp 5 km distance reads as a diorama.

**Actionable.**
- Unreal: **Exponential Height Fog** with Volumetric Fog enabled, plus **Sky Atmosphere**'s *Aerial Perspective View Distance Scale*. In an arid landscape keep `Fog Density` very low — **0.005–0.02** — because the dry-season air genuinely is clear. Push it to 0.03–0.06 for a wet-season or dusty afternoon.
- The Sky Atmosphere component provides physically-derived aerial perspective from its Rayleigh and Mie parameters. Defaults: Rayleigh exponential distribution **8 km**, Mie anisotropy **0.8**, ground radius **6 360 km**, atmosphere height **100 km**, multiscattering **1.0**, ground albedo **0.4**. For a bright sand landscape raise ground albedo toward **0.35–0.45** (it is already close) so the sky picks up ground bounce.
- Blender: use the **Sky Texture** node's *Multiple Scattering* type with `Altitude` set to **1 150 m**, `Air` around 1.0, `Aerosols` low (0.1–0.4 for a clear dry day, 0.8–1.5 for a dusty one), and `Ozone` around 1.0. For explicit distance fog use a **Volume Scatter** in the World with density ~1e-5 to 5e-5 per metre, or the `Mist` pass composited.
- **Dust haze is different from water haze.** Dust is warm and slightly yellow-brown; water vapour is neutral-to-blue. Ohangwena's dry-season haze at the end of the day is dust and biomass smoke — warm. Tint the fog inscattering colour accordingly (a warm grey, ~#B9A88F), not the default blue-grey.

---

## 10. Camera realism

The last 10% of photorealism is *photographic*, not 3D. A physically perfect render that has never passed through a lens looks synthetic.

| Effect | Real cause | Setting | Restraint |
|---|---|---|---|
| **Exposure** | Sensor + aperture + shutter | Unreal: Post Process → Lens → Exposure, **Manual**, EV100 14–15 for Okongo midday. Blender: Film → Exposure, plus camera f-stop/shutter in the physical camera panel | Auto-exposure is the enemy of a matched sequence. Use Manual for stills |
| **Depth of field** | Finite aperture | Real architectural photography uses f/8–f/16 — DoF is *subtle*. Set CineCamera aperture to **f/8** and let the sensor size do the work | The classic CG error is f/1.4 DoF on an exterior. It reads as a miniature |
| **Bloom** | Lens flare and internal scatter | Unreal: Bloom Method **Convolution** with a real lens kernel for stills; Standard for real-time. Intensity 0.3–0.6 | Bloom over ~0.8 destroys the highlight structure |
| **Chromatic aberration** | Dispersion in glass | Unreal: Lens → Chromatic Aberration **0.1–0.35**, Start Offset 0.4 (so it only affects edges). Blender: compositor `Lens Distortion` node, Dispersion 0.002–0.008 | Above ~0.5 it reads as a filter |
| **Vignette** | Lens falloff (cos⁴) | Unreal: Vignette Intensity **0.2–0.4** | Not a mood tool |
| **Grain / noise** | Sensor read noise | Unreal: Film Grain Intensity **0.1–0.3**, Film Grain Texel Size ~1.0. Blender: compositor noise at 0.5–1.5% | Grain is *the* cheapest realism win and the most commonly omitted |
| **Lens distortion** | Optical design | Slight barrel on wide lenses. Blender compositor `Lens Distortion` 0.002–0.01 | Architectural shots are usually corrected — keep near zero |
| **Motion blur** | Shutter open time | Only if something moves. Shutter angle 180° = 1/50 s at 25 fps | Static architectural stills should have none |
| **Sensor and lens choice** | Physical camera | Set **Filmback first** (Full Frame 36 × 24 mm), then focal length. Architectural exteriors 24–35 mm; interiors 18–24 mm; detail 50–85 mm | A 35 mm "focal length" is meaningless without a sensor size |
| **Perspective correction** | Tilt-shift lens | Architectural photography keeps verticals vertical. Keep the camera level and crop, or use a shift | A tilted camera with converging verticals reads as amateur, not artistic |

**Actionable checklist for any hero frame.**
1. Set Filmback, then focal length, then position at a plausible human or tripod height (1 500–1 700 mm).
2. Set aperture to a real architectural value (f/8–f/11) and focus on a real subject.
3. Set Manual exposure to the EV that matches the real illuminance.
4. Add grain, mild vignette, mild CA, restrained bloom.
5. View at 100%, then at thumbnail size. Both must hold up.

---

## 11. The failure catalogue — read this when a frame looks CG

| Symptom | Most likely cause |
|---|---|
| Objects look pasted onto the ground | No contact shadow, no ground blending (use RVT), no dust drift at the base |
| Everything looks like plastic | Uniform roughness; no roughness texture |
| Image looks flat and grey | Wrong exposure; or tonemapper crushing; or fog too strong |
| Shadows look wrong | Sky/sun ratio wrong; or shadow bias/VSM resolution |
| Landscape shimmers in the distance | Specular aliasing — enable roughness-from-normal compositing; no distance tiling break-up |
| Trees look like cardboard | No two-sided foliage / subsurface; no wind; leaf cards too large |
| Repetition visible | See §7, in order |
| Colours feel "video game" | Over-saturated albedo; missing colour management (§ file `09`) |
| Scene reads as a miniature | DoF too shallow; no atmospheric perspective; scale error |
| Sand looks orange | Copying Namib Sand Sea reference instead of Kalahari sandveld reference |
| Perfect, dead-clean surfaces | No surface history layer (§5) |

## Sources

- [Physically Based Materials in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine) — Epic Games
- [Landscape Materials in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-materials-in-unreal-engine) — Epic Games
- [Sky Atmosphere Component in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/sky-atmosphere-component-in-unreal-engine) — Epic Games
- [Exponential Height Fog in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/exponential-height-fog-in-unreal-engine) — Epic Games
- [Blender Manual — Sky Texture Node](https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/sky.html) — Blender Foundation
- [Blender Manual — Ocean Modifier](https://docs.blender.org/manual/en/latest/modeling/modifiers/physics/ocean.html) — Blender Foundation
- [Atlas of Namibia — Climate](https://atlasofnamibia.online/chapter-3) — Namibia Nature Foundation
- Internal cross-references: `13_software_unreal_engine/04_archviz-workflow.md`, `14_software_blender/05_lighting-and-rendering.md`, `18_namibia_context/02_climate-and-weather.md`, `18_namibia_context/03_geology-and-soils.md`

## Open questions

- Measured albedo of Okongo-area Kalahari sand. The 0.30–0.45 range given is from general arid-quartz-sand literature, not a local measurement. `needs-verification` — a grey-card reference photograph on site would settle it.
- Whether the Unreal SunSky `Solar Time` field expects true solar time or local clock time (flagged in domain `13`). Verify empirically once on this project.
- Indicative sand hex values in §8 are eyeballed from reference practice, not colorimetric measurements. Replace with chart-calibrated values after the site visit.
