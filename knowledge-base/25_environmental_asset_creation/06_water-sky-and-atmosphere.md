---
id: envasset.water_sky
title: Water, sky and atmosphere — the environmental systems
domain: 25_environmental_asset_creation
tags: [water, single-layer-water, ocean-modifier, caustics, sky-atmosphere, volumetric-clouds, sky-light, nishita, volumetric-fog, god-rays, heat-shimmer, niagara, dust, time-of-day, oshana]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
applies_to: "Unreal Engine 5.8, Blender 5.2 LTS. Solar geometry for 17.57°S, 1 150 m."
unit_system: SI
sources:
  - {title: "Sky Atmosphere Component in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/sky-atmosphere-component-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Volumetric Cloud Component Properties", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/volumetric-cloud-component-properties-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Exponential Height Fog in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/exponential-height-fog-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Water System in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/water-system-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Blender Manual — Ocean Modifier", url: "https://docs.blender.org/manual/en/latest/modeling/modifiers/physics/ocean.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Sky Texture Node", url: "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/sky.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Atlas of Namibia — The Cuvelai", url: "https://atlasofnamibia.online/chapter-4/the-cuvelai", publisher: "Atlas of Namibia", accessed: 2026-08-25}
related: [envasset.principles, envasset.terrain, envasset.lookdev, namibia.climate, namibia.geography, ue.archviz_workflow, blender.lighting_rendering]
---

# Water, sky and atmosphere — the environmental systems

**Summary.** Sky, atmosphere and water are not "background" — in an exterior they are the *light source*, the *depth cue* and, when an *oshana* is in flood, the strongest compositional element available. This file covers Unreal's Water plugin and Single Layer Water shading model, Blender's Ocean modifier and procedural water, the specific problem of still shallow water in a clay-floored pan, Unreal's Sky Atmosphere and Volumetric Cloud with their real property names, Blender's Sky Texture node in its current form, volumetric fog and dust haze, god rays, heat shimmer, particle systems, and time-of-day rigging — all tuned to a clear, high-sun, dry-season northern Namibian sky.

## Key facts

| Item | Value | Source |
|---|---|---|
| Sky Atmosphere requires | A **Directional Light with "Atmosphere Sun Light" enabled**, plus a Sky Light to capture the atmosphere | Epic |
| Rayleigh Exponential Distribution default | **8 km** (altitude at which the Rayleigh effect reduces to 40%) | Epic |
| Mie Anisotropy default | **0.8** | Epic |
| Ground Radius default | **6 360 km** (Earth) | Epic |
| Atmosphere Height default | **100 km** | Epic |
| Multiscattering default | **1.0** | Epic |
| Ground Albedo default | **0.4** (linear) | Epic |
| Volumetric Cloud units | Layer Bottom, Layer Height, Tracing distances all in **km** | Epic |
| Volumetric Cloud material domain | Must be **Volume** material domain | Epic |
| Volumetric Cloud Multi Scattering Contribution default | **0.5** | Epic |
| Volumetric Fog scattering distribution range | **0** (all directions) to **0.9** (strongly forward) | Epic |
| Unreal Water plugin | **Spline-based** workflow; water bodies interact with Landscape; **Water Waves Asset** drives waves; **Single Layer Water** shading model for physically based water surfaces | Epic |
| Blender Ocean modifier internal grid | Powers of two: Resolution 16 → **256 × 256** simulation grid | Blender Manual |
| Blender Ocean spectra | Turbulent Ocean (Phillips), Established Ocean (Pierson-Moskowitz), Established Ocean Sharp Peaks (JONSWAP+PM), **Shallow Water** (JONSWAP + TMA, for depths under ~10 m) | Blender Manual |
| Blender Sky Texture types | **Single Scattering**, **Multiple Scattering** (most accurate), Preetham (legacy), Hosek/Wilkie (legacy) | Blender Manual |
| Blender Sky Texture parameters | Sun Direction, Turbidity, Ground Albedo, Sun Disc, Sun Size (deg), Sun Intensity, Sun Elevation (deg), Sun Rotation (deg), **Altitude**, **Air**, **Aerosols**, **Ozone** | Blender Manual |
| Blender turbidity guide | 2 = arctic-like, 3 = clear sky, 6 = warm/moist day, 10 = hazy day | Blender Manual |
| Okongo noon solar altitude | **49.2°** (21 Jun) → **90.0°** (~8 Nov and ~1 Feb) → **84.0°** (21 Dec) | domain 13 file 04 |
| Oshana flooding frequency | Roughly **45% of years** | domain 18 |
| Iishana channel widths | **< 10 m to > 1 km**; beds mostly impermeable clay or saline soil | Atlas of Namibia |

> ⚠️ Blender's manual explicitly warns that the Single and Multiple Scattering skies are "very bright by default (hence accurate)" and that the fix is to lower the scene's **Exposure** in Properties → Color Management, not to reduce the sky strength. Reducing the sky's strength to "fix" brightness destroys the physical sun/sky ratio and is the commonest cause of wrong-looking Blender exteriors.

---

## 1. Water

### 1.1 What water exists at this site

Be honest about it, because it changes everything:

- **There is no perennial surface water.** Perennial rivers in Namibia exist only on the borders.
- The *iishana* are **shallow, grassy, interlinked channels**, from under ten metres to over a kilometre wide, that fill seasonally and drain slowly toward the Omadhiya lakes. Beds are **impermeable clay or saline soil**, so water **spreads laterally rather than sinking or incising**.
- Flooding occurs in roughly **45% of years**, and homesteads are traditionally sited on the higher sandy interfluves precisely to avoid it.
- Okongo sits on the **deep sandveld east of the main oshana network** — so an oshana may be a landscape feature in the middle distance rather than on the plot.
- Practical on-plot water: a **borehole**, a **water tank**, a **tap and its splash puddle**, a **livestock trough**, and — for four months — **puddles and sheet water on compacted ground**.

The visualisation implications: you almost certainly do not need an ocean shader. You need **still, shallow, turbid water over a clay bed**, plus puddles.

### 1.2 Unreal's Water plugin

Enable `Water` in Edit → Plugins. It provides a spline-based workflow where rivers, lakes and oceans interact with Landscape terrain, a unified shading and mesh rendering pipeline that supports physics interaction and fluid simulation, and a **Water Waves Asset** that drives wave simulation.

Practical setup for an oshana pan:
1. Place a lake-type water body actor and edit its spline to the pan outline.
2. The water body deforms the Landscape to create its bed — check `Affects Landscape` behaviour, and be careful: on a nearly flat landscape the automatic terrain deformation can carve an unrealistically deep basin. An oshana is **centimetres to a metre or two deep over a very wide area**, not a bowl.
3. Set the Water Waves asset to near-zero amplitude. An oshana is **still**. Wind ripples on the surface, not swell.
4. Set the water material's depth-based colour to a **turbid grey-brown** that becomes opaque within 200–400 mm.

> `needs-verification`: the exact Water Body actor class names and their property lists. Epic's water-bodies documentation page returned no body content on 2026-08-25.

### 1.3 Single Layer Water

`Single Layer Water` is a Material **Shading Model** for physically based water surfaces — a single-pass, single-layer approach that renders water without a separate translucent pass, so it can receive shadows, write depth, and be lit by Lumen.

Material setup for shallow, still, turbid pan water:

| Input | Value | Reasoning |
|---|---|---|
| Base Color | Near black (0.02) | Water's colour comes from absorption and scattering, not from albedo |
| Metallic | 0 | Water is a dielectric |
| Specular | 0.5 | IOR 1.33 → ~2% normal-incidence reflectance; 0.5 is the physical default |
| Roughness | 0.02–0.10 | Still water is very smooth; wind-rippled water 0.06–0.15 |
| Normal | Two scrolling normal maps at different scales and speeds, blended with `BlendAngleCorrectedNormals` | One scrolling normal map has a visible direction |
| Water Absorption | High, warm-biased (absorbs red least in muddy water) | Turbid Cuvelai water is brown, not blue-green |
| Water Scattering | Moderate to high | Suspended clay — this is what makes it opaque quickly |
| Water Phase G | 0.3–0.6 | Forward-scattering suspended particles |
| Opacity | Depth-driven | Should reach opaque by ~300 mm |

**Do not use ocean/tropical water presets.** Blue-green transparent water is the wrong physical model entirely: the Cuvelai's water is turbid with suspended clay and reads as brown-grey with a mirror surface.

### 1.4 Shallow vs deep

The difference is not the shader, it is the **absorption depth**:

- **Deep** (> 2 m): the bed is invisible; colour is entirely absorption + scattering + sky reflection.
- **Shallow** (< 500 mm): the bed dominates. You *must* see the clay bed, the grass stems standing in the water, and the shoreline wet-to-dry gradient. This is what makes shallow water read as shallow.
- Implement with `SceneDepth` minus `PixelDepth` to get water thickness, then use it to drive opacity, absorption tint and the strength of refraction distortion.

### 1.5 Caustics

Light refracting through the water surface and focusing on the bed. In shallow, still, *turbid* water caustics are **weak or absent** — the suspended clay scatters the light before it reaches the bed. In clear water over a pale bed they are strong.

- **Unreal, cheap**: a scrolling caustics texture projected onto the bed, masked by the water body's extent and by depth. Use a `Light Function` on the Directional Light, or a decal, or multiply into the bed material.
- **Unreal, better**: bake a caustics animation from Blender/Cycles and play it as a texture array.
- **Blender/Cycles**: real caustics require `Caustics Caster` / `Caustics Receiver` object settings plus the Manifold Next Event Estimation option; brute-force path-traced caustics through a smooth interface are extremely slow.
- **The realism judgement**: if the water is turbid, leave caustics out. Adding them is a common and visible error.

### 1.6 Refraction

Set the material's `Refraction` to an IOR of **1.33**, and use the *Index of Refraction* refraction mode rather than the pixel-normal-offset mode where physical accuracy matters. Note that screen-space refraction cannot show anything outside the frame — objects at the frame edge will smear. For still water viewed from a shallow angle, reflection dominates anyway (Fresnel), and refraction matters mainly when looking steeply down.

### 1.7 Foam and shoreline blending

- **Shoreline foam**: real only where there is wave action. An oshana has almost none. What it *does* have is a **scum line** of dust, pollen and organic debris at the water's edge, and a band of **wet, darkened, saturated ground** extending 100–500 mm beyond the water.
- Implement the wet band with the wetness formula in `05 §2.7`, masked by proximity to the water plane (`WorldPosition.Z` compared against the water level, smoothstepped).
- **Blend the water edge** by fading opacity to zero over the last 20–50 mm of depth. A hard water/land intersection line is a very visible tell.
- Add **emergent vegetation**: grass and sedge stems standing *through* the surface. The iishana are described as *grassy* channels — vegetated, not open water. This single detail does more for believability than any shader parameter.

### 1.8 Blender water

**Ocean modifier** — a port of the Houdini Ocean Toolkit, intended for deep ocean waves and foam. For this project its relevant mode is the **Shallow Water** spectrum, described as "JONSWAP and TMA methods… for shallow water with depths less than about 10 metres which makes it great for small lakes and ponds without heavy wind." Settings: Geometry `Displace` (deform existing geometry rather than replacing it), Resolution 16–32 (a Resolution of 16 gives a 256 × 256 internal grid), Spatial Size = the real width in metres, Depth low (0.3–1.0 m), Wind Velocity low (1–4 m/s), Choppiness 0–0.3, Scale very low.

**Procedural water nodes** — for still water, the Ocean modifier is overkill. Use a flat plane with:

```
Principled BSDF:
  Base Color   (0.02, 0.02, 0.02)
  Roughness    0.03
  IOR          1.33
  Transmission 1.0            (for a clear-water look)
Volume Absorption + Volume Scatter in the Volume socket for turbidity:
  Absorption Color  warm brown, Density  2.0–8.0 per metre
  Scatter    Color  grey-brown, Density  1.0–4.0, Anisotropy 0.4
Normal: two Noise Textures (4D, W = Scene Time) → Bump, strength 0.02–0.06
```

Blender 5.2's **Thin Wall** mode on the Principled BSDF is for genuinely thin sheets (a puddle film) and should not be used for a body of water with real depth.

---

## 2. Sky and atmosphere

### 2.1 Unreal Sky Atmosphere

The Sky Atmosphere component is a physically-based participating-medium model of the atmosphere. It **requires a Directional Light with "Atmosphere Sun Light" enabled**, and a Sky Light to capture its result and contribute it to scene lighting.

Documented settings and defaults:

| Setting | Default | Meaning | Okongo adjustment |
|---|---|---|---|
| Rayleigh Scattering Scale | Earth-like | Scattering from air molecules | Slightly **lower** — 1 150 m altitude means less air above |
| Rayleigh Exponential Distribution | **8 km** | Altitude at which the Rayleigh effect reduces to 40% | Leave |
| Mie Scattering Scale | Earth-like | Scattering from aerosols | **Lower** in dry season (clear); **raise** for a dusty afternoon or the wet season |
| Mie Anisotropy | **0.8** | Directionality around the sun | Leave; raise slightly for a strong dusty forward-scatter halo |
| Absorption Scale | Earth ozone | Ozone absorption | Leave |
| Ground Radius | **6 360 km** | Planet size | Leave |
| Atmosphere Height | **100 km** | Top of atmosphere | Leave |
| Multiscattering | **1.0** | Multiple-bounce contribution | Leave |
| Ground Albedo | **0.4** linear | Ground reflectivity feeding back into the sky | **Keep at 0.35–0.45** — pale sand genuinely is this bright |
| Aerial Perspective View Distance Scale | — | Thickness of aerial perspective | **Reduce to 0.3–0.6** for a very clear dry-season day |
| Height Fog Contribution | — | Artistic blend with Exponential Height Fog | Leave at 1.0 |

The **Ground Albedo** parameter is unusually important here. It is the mechanism by which the bright sand throws light back into the atmosphere, and it is part of why a Kalahari sky near the horizon is paler and warmer than a temperate one.

### 2.2 Volumetric clouds

The `Volumetric Cloud` component uses a **Volume-domain material** and works in **kilometres**. Documented properties:

| Property | Meaning |
|---|---|
| Layer Bottom Altitude | Cloud layer start (km) |
| Layer Height | Layer thickness (km) |
| Tracing Start Max Distance | Max distance before accepting a trace start (km) |
| Tracing Max Distance Mode | Interpretation of the max distance |
| Tracing Max Distance | Max trace distance within the layer (km) |
| Planet Radius | Used only when no Sky Atmosphere is present |
| Ground Albedo | Ground colour lighting the cloud bases |
| Material | Must be **Volume** material domain |
| Use Per Sample Atmospheric Light Transmittance | Per-sample vs global transmittance |
| Sky Light Cloud Bottom Occlusion | Fast approximation of occlusion under the cloud base |
| View / Reflection / Shadow View / Shadow Reflection Sample Count Scale | Quality scales |
| Shadow Tracing Distance | Shadow trace distance (km) |
| Stop Tracing Transmittance Threshold | Early ray-march termination |
| Multi Scattering Contribution | Default **0.5** |

**Cloud choices by season:**

| Season | Cloud | Layer Bottom | Layer Height |
|---|---|---|---|
| Dry (May–Sep) | Essentially none, or a few thin high cirrus | — | — |
| Pre-rain (Oct–Nov) | Building fair-weather cumulus, flat bases, sharply defined | ~2.0–2.5 km | ~2–4 km |
| Wet (Dec–Mar) | Deep convective cumulus and cumulonimbus, tall, with anvils; heavy shadowing | ~1.2–2.0 km | 6–12 km |
| Post-rain (Apr) | Broken cumulus, clearing | ~2.0 km | ~2 km |

**The cloud base altitude is a real physical quantity** — it is roughly where the rising air reaches saturation, and in a hot dry inland climate it is **high** (2–3 km) rather than the 600–1 000 m of a maritime climate. High flat cloud bases with large gaps are characteristic; low overcast is not.

**Cloud shadows are a compositional tool.** With MegaLights and volumetric cloud shadows enabled, a moving cloud shadow across the landscape gives the strongest sense of scale and space available. In UE 5.8, MegaLights reached Production Ready with cloud shadow support (see domain `13`).

### 2.3 Sky Light and real sun intensity

Cross-reference domain `13` file `04` for the full unit table. In summary:

| Condition | Directional Light (lux) | Sky Light (cd/m²) | Manual EV100 |
|---|---|---|---|
| Clear sky, high sun (Okongo midday) | 100 000 – 120 000 | 3 000 – 10 000 | 14 – 15 |
| Clear sky, mid-morning / mid-afternoon | 60 000 – 90 000 | 3 000 – 6 000 | 13 – 14 |
| Golden hour | 5 000 – 20 000 | 1 000 – 3 000 | 10 – 12 |
| Overcast | 1 000 – 20 000 | 2 000 – 5 000 | 11 – 13 |

Set the Sky Light to **Real Time Capture** so it tracks the Sky Atmosphere as the sun moves. Set the Directional Light's `Source Angle` to **0.5357°** (the sun's real angular diameter) — the default is often larger and produces shadows that are too soft.

### 2.4 Physically based sun angles for 17.57°S

From domain `13`, computed from standard solar-position formulae:

| Date | Declination | Max solar altitude | Noon sun is | Day length |
|---|---|---|---|---|
| 21 June | +23.44° | **49.2°** | due **north** | ≈ 10 h 58 m |
| Equinoxes | 0° | **72.6°** | due **north** | 12 h 00 m |
| ~8 Nov and ~1 Feb | −17.4° | **90.0°** | directly overhead | — |
| 21 December | −23.44° | **84.0°** | due **south** | ≈ 13 h 03 m |

**Solar noon at Okongo is about 12:50 local clock time**, because Okongo (17.6°E) is 12.4° west of the UTC+2 standard meridian (30°E), giving ~49.6 minutes of lag, ±16 minutes for the equation of time.

Configure the Unreal **SunSky** actor: Latitude **−17.4**, Longitude **17.6**, Time Zone **+2**, DST **off**, North Offset per level orientation.

### 2.5 Blender's Sky Texture node

The node has been reworked; the current types are **Single Scattering** (an improved Nishita-1993 model, legacy and may be removed), **Multiple Scattering** (based on Fernando García Liñán's work — "the most accurate model as it accounts for multiple bounces of light in the atmosphere"), plus the legacy Preetham and Hosek/Wilkie models which will be removed.

**Use Multiple Scattering.** Parameters:

| Parameter | Meaning | Okongo value |
|---|---|---|
| Sun Direction | Direction vector | Set from the solar model, or drive Sun Elevation/Rotation |
| Turbidity | Atmospheric turbidity — 2 arctic, **3 clear sky**, 6 warm/moist, 10 hazy | **2.5–3.5** dry season; **5–7** wet season |
| Ground Albedo | Light reflected from the planet surface back into the atmosphere | **0.35–0.45** (pale sand) |
| Sun Disc | Enable/disable sun disc lighting (Cycles only) | **On** |
| Sun Size | Angular diameter in degrees | **0.526** (the real value) |
| Sun Intensity | Multiplier for sun disc lighting | **1.0** — do not use this as an exposure control |
| Sun Elevation | Rotation from the horizon, degrees | From the table in §2.4 |
| Sun Rotation | Rotation around zenith, degrees | Azimuth from the solar model |
| **Altitude** | Distance from sea level to the camera | **1150 m** |
| **Air** | Density of air molecules; 1 ≈ urban city air, 0 = none | **0.8–1.0** |
| **Aerosols** | Density of aerosol particles (water droplets); 1 ≈ urban | **0.1–0.4** dry clear; **0.8–1.5** dusty or humid |
| **Ozone** | Density of ozone; makes the sky bluer | **1.0** |

Remember the manual's warning: these skies are accurate and therefore bright. Fix brightness with **Properties → Color Management → Exposure**, not with strength.

**HDRIs vs procedural sky.** Use a captured HDRI (`02 §4`) when you need the *exact* light of a specific moment, or when the sky is visible and you want real cloud. Use the procedural sky when you need a controllable, animatable, physically consistent sun-sky pair. For a project where a client will ask for "the same shot at 4pm", procedural wins.

---

## 3. Volumetric fog, dust haze and god rays

### 3.1 Exponential Height Fog

Documented properties: `Fog Density` (global density factor, "the fog layer's thickness"), `Fog Height Falloff` ("how the density increases as height decreases; smaller values make the transition larger"), a full secondary fog layer (density, height falloff, height offset), `Fog Inscattering Color` (the fog's primary colour, facing the dominant directional light or upward), `Directional Inscattering Color` (approximates inscattering from a directional light), `Start Distance`, and `Fog Cutoff Distance`.

With **Volumetric Fog** enabled: `Scattering Distribution` (0 = all directions, 0.9 = strongly toward the light direction), `Albedo` (particle reflectiveness), `Extinction Scale`, and `View Distance`.

**Okongo settings:**

| Condition | Fog Density | Height Falloff | Inscattering Color | Scattering Distribution |
|---|---|---|---|---|
| Clear dry-season day | **0.005–0.015** | 0.2 | Warm pale grey (~#B9A88F) | 0.4 |
| Dusty afternoon / smoke haze | **0.02–0.05** | 0.15 | Warmer, more yellow (~#C4AE8C) | **0.7–0.85** (strong forward scatter) |
| Wet-season humid morning | **0.02–0.04** | 0.4 | Neutral to slightly blue grey | 0.5 |
| Early morning ground mist (rare) | 0.03 with a high Height Falloff (1.5) | 1.5 | Cool neutral | 0.6 |

**The colour of the fog is the point.** Temperate defaults are blue-grey; Ohangwena dry-season haze is **dust and biomass smoke**, and is warm. A blue haze in this landscape reads as European immediately.

### 3.2 God rays (crepuscular rays)

Volumetric fog plus a shadow-casting occluder produces light shafts automatically. To get them:
1. Volumetric Fog **on** in the Exponential Height Fog actor.
2. The Directional Light's `Volumetric Scattering Intensity` raised (1.0–4.0).
3. `Scattering Distribution` raised toward 0.7–0.85, so light concentrates around the sun direction.
4. Something to cast the shadow — tree canopy, a pergola, a roof edge, cloud.

In this landscape the natural god-ray moments are: **early morning through the palisade** (hundreds of vertical poles producing a picket of shafts — a genuinely characteristic image), **through a mopane canopy**, and **under a cloud break during the wet season**.

Do not use the screen-space `Light Shafts` post-process for a hero frame; it is cheap and inaccurate. Use volumetric fog.

### 3.3 Heat shimmer

Air near a hot surface has a lower refractive index, and the resulting gradient distorts the image. Over sand at 40 °C this is strongly visible beyond about 50 m, and it is one of the most evocative and least-used effects available for this environment.

Implementation options:
1. **Refraction-based**: a translucent plane or box in front of the hot surface, material with `Refraction` driven by an animated noise (two panning noise textures at different speeds, amplitude ~0.002–0.008 IOR). Cheap and controllable; works well for a distant band above the ground.
2. **Post-process material** with a screen-space UV offset from an animated noise, masked to the lower part of the frame and to distance (`SceneDepth > 5000 uu`). Global and cheap.
3. **Niagara** distortion particles — best control, most cost.

**Restraint**: shimmer should be a subtle vertical wobble of 1–3 pixels at 1080p, increasing with distance, present only in the hot hours (10:00–16:00) and only over sunlit ground. Overdone, it reads as a filter.

### 3.4 Particle systems (Niagara)

| Effect | System design | Notes |
|---|---|---|
| **Wind-blown dust** | GPU sprite emitter, wide box location, low gravity, high drag, velocity from a curl-noise force, lifetime 4–10 s, very low opacity (0.02–0.08), soft/subsurface-lit sprite | Should be nearly invisible individually; the effect is cumulative |
| **Dust devils** | Ribbon or sprite emitter on a vortex velocity field, spawn rate ramping over the hot hours | Common in this landscape; a strong storytelling detail |
| **Vehicle / footfall dust puff** | Burst emitter triggered by an event, radial velocity, fast opacity falloff | |
| **Cooking-fire smoke** | Sprite emitter with buoyancy, curl noise, low opacity; light it with the Sky Light and a local point light for the fire | Very characteristic of a homestead at dawn and dusk |
| **Insects** | Small sprite or mesh emitter, chaotic velocity, tight spatial bounds, spawned near vegetation and water | Almost never done; enormously effective at close range |
| **Blowing grass seed / chaff** | Sprite emitter along the wind vector, lifetime 2–4 s | Post-harvest, dry season |

Use **GPU simulation** for anything above a few thousand particles, and enable **Fixed Bounds** on the emitter so it does not get culled incorrectly.

---

## 4. Time-of-day systems

For a client who will ask to see the house at three different times:

**Unreal.**
1. Use the **SunSky** Blueprint (Sun Position Calculator plugin) with the Okongo coordinates. Its `Solar Time` field drives everything.
2. Expose `Month`, `Day` and `Solar Time` as a level Blueprint variable or an Editor Utility Widget slider.
3. Sky Light on **Real Time Capture** so it follows.
4. Drive the Exponential Height Fog's `Fog Inscattering Color` and `Fog Density` from a curve keyed against solar altitude — haze increases through the day as convection lifts dust.
5. Drive Post Process exposure from a curve too, or accept a fixed EV per shot (better for consistency — see `09`).
6. **Animate in Sequencer** by keying the SunSky's Solar Time, not by rotating the Directional Light by hand. Hand-rotated suns produce impossible azimuth/altitude pairs.

> `needs-verification` (carried from domain `13`): whether SunSky's `Solar Time` expects true solar time or local clock time. Determine empirically once, and write the answer into the project notes.

**Blender.**
- The **Sun Position** add-on (enable in Preferences) takes latitude, longitude, time zone, date and time and places a Sun lamp correctly; it can also drive the Sky Texture.
- Or compute it in Python — domain `14` file `05` contains a deterministic, add-on-free solar position script already parameterised for Okongo. Use that.
- Animate by keying the date/time driver, then bake the sun rotation to F-curves before rendering a sequence.

---

## 5. Atmosphere checklist

- [ ] Directional Light has **Atmosphere Sun Light** enabled
- [ ] Sky Light on Real Time Capture
- [ ] Sun `Source Angle` set to **0.5357°**
- [ ] Sky Atmosphere `Ground Albedo` at 0.35–0.45 to reflect pale sand
- [ ] Aerial Perspective View Distance Scale reduced for a clear dry-season day
- [ ] Fog density in the 0.005–0.02 range, **not** temperate defaults
- [ ] Fog inscattering colour **warm**, not blue
- [ ] Cloud layer bottom at 2–3 km, not 600 m
- [ ] Cloud type matched to the declared season
- [ ] Sun position from real solar geometry, not eyeballed
- [ ] Solar noon understood to be ~12:50 clock time
- [ ] Water (if any) turbid brown-grey, shallow, with emergent grass and a wet-ground band
- [ ] Caustics omitted unless the water is genuinely clear
- [ ] Heat shimmer present in the hot hours only, and subtle
- [ ] At least one shot composed with the sun behind the subject, to exploit god rays and foliage translucency

## Sources

- [Sky Atmosphere Component in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/sky-atmosphere-component-in-unreal-engine) — Epic Games
- [Volumetric Cloud Component Properties in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/volumetric-cloud-component-properties-in-unreal-engine) — Epic Games
- [Exponential Height Fog in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/exponential-height-fog-in-unreal-engine) — Epic Games
- [Water System in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/water-system-in-unreal-engine) — Epic Games
- [Blender Manual — Ocean Modifier](https://docs.blender.org/manual/en/latest/modeling/modifiers/physics/ocean.html) — Blender Foundation
- [Blender Manual — Sky Texture Node](https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/sky.html) — Blender Foundation
- [Atlas of Namibia — The Cuvelai](https://atlasofnamibia.online/chapter-4/the-cuvelai) — Atlas of Namibia
- Internal: `13_software_unreal_engine/04_archviz-workflow.md`, `14_software_blender/05_lighting-and-rendering.md`, `18_namibia_context/02_climate-and-weather.md`

## Open questions

- **Water Body actor class names and properties** in the UE Water plugin. Epic's page returned no body content. `needs-verification`.
- **Single Layer Water** material input list and exact parameter names. `needs-verification`.
- Whether the Water plugin's automatic Landscape deformation can be constrained to a very shallow basin without manual sculpting. `needs-verification`.
- **SunSky `Solar Time`** semantics (true solar vs clock time). `needs-verification`.
- Typical cloud base altitude at Okongo in the wet season — the 1.2–3 km figures given are from general meteorological reasoning for a hot inland climate, not from local observation. `needs-verification`.

