---
id: envasset.lookdev
title: Lighting and look development — making the render read true
domain: 25_environmental_asset_creation
tags: [lighting, lookdev, photometric-units, lux, ev100, exposure, colour-management, aces, agx, tonemapper, white-balance, chart, reference-matching, grading, checklist]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Unreal Engine 5.8, Blender 5.2 LTS. Site: 17.57°S, ~1 150 m."
unit_system: SI
sources:
  - {title: "Blender Manual — Color Management", url: "https://docs.blender.org/manual/en/latest/render/color_management.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Sky Texture Node", url: "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/sky.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Sky Atmosphere Component in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/sky-atmosphere-component-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Exponential Height Fog in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/exponential-height-fog-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Atlas of Namibia, Chapter 3 — Climate", url: "https://atlasofnamibia.online/chapter-3", publisher: "Atlas of Namibia", accessed: 2026-08-25}
related: [envasset.principles, envasset.water_sky, envasset.reference_scanning, ue.materials_rendering, ue.archviz_workflow, blender.lighting_rendering, namibia.climate]
---

# Lighting and look development — making the render read true

**Summary.** Look development is the discipline of getting the image to match reality, measured rather than judged. The tools are: physically correct light values in real units, a correct exposure derived from those values, a colour-managed pipeline that does not silently distort anything, calibration objects placed in the scene, and a reference photograph to compare against. This file gives the real illuminance figures for a clear dry-season Ohangwena day, the EV maths, the colour-management settings for both applications with their current names, a look-dev sphere and chart setup, a structured reference-matching workflow, grading discipline, the honest difference between real-time and offline expectations, and a failure-mode checklist.

## Key facts

| Quantity | Value |
|---|---|
| Direct sun, clear sky, high sun | **~100 000–120 000 lux** |
| Clear blue sky alone (horizontal) | **~10 000–25 000 lux** |
| Sun : sky ratio, clear desert day | **≈ 7 : 1** |
| Overcast | ~1 000–20 000 lux |
| Deep shade under a tree, sunny day | ~5 000–15 000 lux |
| Interior, next to a window | ~1 000–5 000 lux |
| Interior, artificially lit domestic | ~100–300 lux |
| Full moon | ~0.1–0.3 lux |
| Okongo global horizontal irradiance | **≈ 2 275 kWh/m²/yr (6.23 kWh/m²/day)** (PVGIS SARAH2, domain 18) |
| Okongo max noon solar altitude | **90.0°** (~8 Nov, ~1 Feb); min **49.2°** (21 Jun) |
| Solar noon at Okongo | **≈ 12:50** local clock time |
| Sun angular diameter | **0.53°** (Unreal `Source Angle` 0.5357; Blender Sun `Angle` 0.526°) |
| Unreal exposure unit | **EV100** (ISO 100) |
| Unreal light units | Directional = lux; Sky Light = cd/m²; Point/Spot/Rect = candela, lumen or unitless; emissive = cd/m² |
| Blender view transform to use | **AgX** — the manual states Filmic is deprecated and superseded by AgX; AgX gives 16.5 stops and desaturates highly exposed colours |
| Blender working space (5.0+) | Linear Rec.709 default; ACEScg available |
| Blender ACES views (5.0+) | ACES 1.3 and 2.0 |
| Unreal tonemapper | Filmic, ACES-derived, with Film Slope/Toe/Shoulder/Black clip/White clip and Expand Gamut |

> ⚠️ **Set the light first, the exposure second, and judge third.** The overwhelmingly common workflow error is to set an arbitrary light intensity, then push exposure until the image looks right. That produces an image whose *relative* values — the ratio of sunlit sand to shadowed wall — are wrong, and no grading fixes it.

---

## 1. Physically based lighting units, and matching real illuminance

### 1.1 The unit systems

Cross-reference domain `13` file `04` for the full Unreal unit relationship table (1 cd = 625 unitless; a light at 1000 cd measures 1000 lux at one metre; the point/spot/rect solid-angle conversions). The essentials:

**Unreal.** Set `Project Settings → Rendering → Default Settings → Light Units` once. Directional lights are in **lux** (direct normal illuminance — light on a surface perpendicular to the sun's rays). Sky Light is in **cd/m²**. Point, spot and rect lights offer candela, lumen or unitless; **use lumen for anything with a real product datasheet**, because that is the unit the manufacturer publishes.

**Blender.** Sun lamp `Strength` is **irradiance in W/m²**. Point/spot/area lamp `Power` is in **watts** — but this is *radiometric* watts of emitted light, not electrical watts, and Blender's conversion assumes a particular luminous efficacy. In practice: prefer to light the exterior from the **Sky Texture** (which produces a physically consistent sun and sky together) and use explicit lamps only for interiors, where you tune against a target lux measured on a plane.

### 1.2 The target values for Okongo

| Condition | Directional (lux) | Sky Light (cd/m²) | Manual EV100 | Notes |
|---|---|---|---|---|
| Clear sky, noon (Nov–Feb, sun near zenith) | **110 000–120 000** | 5 000–10 000 | **15** | Shadows almost directly under objects |
| Clear sky, noon (Jun–Jul, sun at 49°) | 95 000–110 000 | 4 000–8 000 | 14–15 | Longer shadows, warmer light |
| Mid-morning / mid-afternoon (09:00 / 15:00) | 60 000–90 000 | 3 000–6 000 | 13–14 | The best general-purpose architectural light |
| Golden hour (07:00 / 17:30 approx.) | 5 000–20 000 | 1 000–3 000 | 10–12 | The money shot for sand and foliage |
| Civil twilight | 100–1 000 | 200–800 | 6–9 | Sky dominates entirely |
| Overcast (wet season) | 1 000–20 000 | 2 000–5 000 | 11–13 | Rare in the dry season |
| Interior, daylit, away from window | — | — | 8–11 | |
| Interior, artificial only | — | — | 5–8 | |

These are working values from photometric practice, not Epic-published figures. What matters is the **ratio between rows**, which encodes the real behaviour of the day.

### 1.3 The EV maths

Exposure value at ISO 100:

```
EV100 = log2( N² / t )                         N = f-number, t = shutter in seconds
EV100 = log2( L × S / K )                      L = luminance cd/m², S = ISO, K ≈ 12.5
EV100 ≈ log2( E × S / C )                      E = illuminance lux,  C ≈ 250
```

For a scene at 110 000 lux incident with a mid-grey (18%) subject:

```
subject luminance L = 110 000 × 0.18 / π  ≈  6 302 cd/m²
EV100 = log2(6302 × 100 / 12.5) = log2(50 419) ≈ 15.6
```

Which is why **EV100 ≈ 15** is right for full sun. The classic photographer's "Sunny 16" rule — f/16 at 1/ISO seconds — gives EV100 = log2(16²/(1/100)) = log2(25 600) ≈ 14.6 for temperate full sun. Ohangwena's higher, clearer sun sits about half a stop to a stop above that, at **EV 15 to 15.5**, which matches the physics.

**Set exposure to Manual.** Auto-exposure drifting between frames of a sequence, or between two stills of the same house, is a defect. In Unreal: Post Process Volume (unbound) → Lens → Exposure → Metering Mode **Manual**, then set Exposure Compensation to the EV100 you want. In Blender: Render → Color Management → Exposure, in stops relative to the render's own scale — set it once for a lighting condition and leave it.

Epic's own troubleshooting notes are worth repeating: if the image goes white after placing a light, raise `Auto Exposure Max EV100` and `Histogram Max EV100`; and `Project Settings → Rendering → Default → Extend default luminance range in Auto Exposure settings` must be on for the SunSky actor to display correctly.

---

## 2. Sun and sky ratios in clear desert conditions

The ratio is the *look*. Get it wrong and no other correction helps.

| Environment | Sun : sky | Visual signature |
|---|---|---|
| Clear high-altitude arid (Ohangwena, dry season) | **≈ 7 : 1** | Very dark, high-contrast shadows; deep blue zenith; sharp shadow edges |
| Temperate clear summer day | ≈ 4–5 : 1 | Softer shadows, paler sky |
| Hazy tropical coast | ≈ 2–3 : 1 | Washed, low contrast |
| Overcast | 0 : 1 | No cast shadows at all |

**Setting it correctly:**
1. Set the Directional Light to the target lux from §1.2.
2. Set Sky Light to **Real Time Capture** and let the Sky Atmosphere produce the sky luminance. Do not override the Sky Light intensity to "fix" the shadows — that breaks the ratio you are trying to reproduce.
3. Set the Sky Atmosphere's **Ground Albedo to 0.35–0.45**. Pale sand genuinely bounces this much and it lifts the shadows in exactly the way the real place does.
4. If the shadows still look too dark, check that **Lumen** is on and its Final Gather Quality is adequate — the fill in a real desert shadow comes from sky *plus* sand bounce, and a scene without GI will always look wrong here.
5. Set the sun's **Source Angle to 0.5357°**. Many defaults are larger and produce shadows that are too soft.

**The diagnostic.** Photograph the site at the target time, exposing for the highlights. Measure the sunlit sand and the shadowed wall in the photograph. In the render, measure the same two surfaces with a colour picker in linear space. The *ratio* should match within about 15%. If it does not, the sun/sky balance is wrong, not the grade.

---

## 3. Colour management

Colour management is where an otherwise-correct render acquires a subtly wrong, "CG" look — usually through over-saturated, clipped highlights.

### 3.1 Blender

`Properties → Render → Color Management`:

| Setting | Value | Reasoning |
|---|---|---|
| **View Transform** | **AgX** | The manual states AgX improves on Filmic, gives more photorealistic results, offers **16.5 stops** of dynamic range and desaturates highly exposed colours to mimic film — and that **Filmic is deprecated and superseded by AgX** |
| **Look** | `AgX - Base Contrast` for neutral; `Medium High Contrast` for a punchier exterior | |
| **Exposure** | Stops. Lower it for a Sky-Texture-lit exterior — the manual explicitly recommends this rather than dimming an accurate sky | |
| **Working Space** (5.0+) | Linear Rec.709 unless a downstream pipeline requires ACEScg | |
| **Sequencer** | sRGB (leave) | |

Use **Standard** only when the image is already graded or when you need exact colour matching; **Khronos PBR Neutral** for product-accurate colour (a joinery swatch match); **False Color** as a *diagnostic* — it heat-maps luminance so you can see immediately whether the image is exposed correctly.

Blender 5.0 added **ACES 1.3 and 2.0 views and an ACEScg working space**. Use ACES only if you are delivering into an ACES pipeline (a film or a client with a colour spec). For a standalone architectural deliverable, AgX with Linear Rec.709 is simpler and looks better out of the box.

### 3.2 Unreal

Unreal's tonemapper is **filmic and ACES-derived**, with `Film` controls (Slope, Toe, Shoulder, Black clip, White clip) and `Expand Gamut`.

| Setting | Where | Recommendation |
|---|---|---|
| Tonemapper Film curve | Post Process Volume → Color Grading → Misc → Film | Leave at defaults for a neutral filmic look; adjust Toe only if blacks are crushing |
| Expand Gamut | Same | Leave |
| **Legacy tonemapper** | `r.TonemapperFilm 0` | **Do not use.** It is the pre-4.15 curve and clips badly |
| **OCIO** | Project Settings, and Movie Render Graph's OCIO node | Configure only if delivering into a managed pipeline |
| Working colour space | `Project Settings → Rendering → Working Color Space` | sRGB/Rec.709 default; change only with a reason |
| Auto Exposure Bias | Project Settings → Rendering → Default Settings | Leave at 0 and control exposure per Post Process Volume |

**Local Exposure** (Post Process → Lens → Local Exposure → Highlight/Shadow Contrast Scale) is genuinely useful for the defining exposure problem of this project: a bright sunlit exterior seen through a window from a dim interior. Values around 0.7–0.85 recover detail without producing the flat HDR-photo look. Below ~0.5 it becomes obvious.

### 3.3 The pipeline rule

**Do the grade once, at the end, in one place.** Not a bit in the material, a bit in the Post Process Volume, and a bit in Photoshop. A grade split across three stages cannot be reproduced or reversed.

---

## 4. White balance

The sun at Okongo is a warm source (roughly 5 000–5 500 K near midday, dropping to 2 000–3 000 K at sunrise/sunset) seen against a very blue sky. A camera set to daylight white balance renders the shadows blue and the sunlit surfaces neutral-warm. That is what a photograph of the place looks like, and it is what your render should look like.

**Actionable:**
1. Decide the white balance **once per shot** and record it. Unreal: Post Process → Color Grading → Temperature (White Balance) + Tint. Blender: leave it at neutral and correct in the compositor, or use a `Color Balance` node.
2. **Do not white-balance the warm sand bounce away.** The warm underside of the eaves is physically correct.
3. For golden-hour shots, resist neutralising the warmth. A golden-hour render corrected to neutral looks like a mistake.
4. If you have a **colour chart photograph** from the site (`02 §1.3`), match to it: place a virtual chart in the scene, render, and compare patch by patch.

---

## 5. Look-dev spheres and charts in scene

The standard VFX practice, and it costs nothing.

Build a `BP_LookDevRig` / a Blender collection containing:

1. **A 100% diffuse white sphere** (albedo 0.9, roughness 1.0) — reads the lighting's *shape and colour*, including bounce.
2. **A grey sphere** (albedo 0.18, roughness 1.0) — the mid-grey reference. If this does not render at mid-grey, the exposure is wrong.
3. **A chrome sphere** (metallic 1.0, roughness 0.0) — shows the environment, the sun position, and whether reflections are being captured.
4. **A rough metal sphere** (metallic 1.0, roughness 0.35) — reads specular response.
5. **A virtual ColorChecker chart** with the 24 patches at their published reflectance values. `needs-verification`: the exact sRGB/linear values of the ColorChecker patches — take them from your own chart photograph rather than from memory.
6. **A 1 750 mm scale figure**.
7. **A 1 m calibration cube** with 100 mm gridlines.

Place the rig at the focal point of the shot, render, then hide it. Compare against a photograph of a real grey ball and chart shot on site in the same light. This is how film VFX matches plates, and it works exactly as well for architecture.

**What each sphere tells you:**
- White sphere too dark on its shadow side → GI is off or too weak.
- White sphere shadow side is *blue* rather than warm-neutral → your ground albedo/bounce is wrong.
- Grey sphere not reading mid-grey → exposure is wrong.
- Chrome sphere shows no sun disc → the Sky Atmosphere or Sky Light capture is misconfigured.
- Chrome sphere reflections are blocky → Sky Light capture resolution or reflection capture placement.

---

## 6. Reference matching workflow

This is the most valuable single process in this whole domain.

1. **Choose one reference photograph** from the site, taken at a known time, with known EXIF and a colour chart in an accompanying frame.
2. **Rebuild its camera** exactly: filmback (36 × 24 mm for full frame), focal length from EXIF, aperture from EXIF, position and height measured or estimated from the photograph's perspective.
3. **Set the sun** to the date and time the photograph was taken, from the solar model — not by eye.
4. **Set the light values** from §1.2 and the exposure from EXIF: `EV100 = log2(N²/t)` at ISO 100, adjusted for the actual ISO by `− log2(ISO/100)`.
5. **Render at the photograph's aspect ratio.**
6. **Compare**, in this order:
   - **Value structure first.** Convert both to greyscale. Do the sunlit and shadowed areas have the same relationship? This is 70% of the match.
   - **Shadow direction and length.** If they differ, the sun position is wrong — fix that before anything else.
   - **Contrast.** Too flat → fog too heavy or sky too bright. Too harsh → GI off or sky too dim.
   - **Colour**, last. Sample specific surfaces in both images and compare in linear space.
7. **Difference blend.** Put the render over the photograph in Difference blend mode in any image editor. Areas that go black match. This is brutal and effective.
8. **Fix the cause, not the symptom.** A too-dark shadow is fixed by GI or ground albedo, not by lifting the shadows in the grade.
9. **Record what you changed** in the project notes, so the next shot starts closer.

---

## 7. Post-process and grading discipline

For architectural work the grade should be nearly invisible. The client is judging the building.

**A defensible post-process stack:**

| Effect | Setting | Rationale |
|---|---|---|
| Exposure | Manual, EV from §1.2 | Consistency across shots |
| Local Exposure | Highlight/Shadow Contrast Scale 0.75–0.9 if there is an interior/exterior range | Recovers detail without the HDR look |
| Bloom | Convolution for hero stills, Intensity 0.3–0.6 | Real lens scatter |
| Vignette | 0.2–0.4 | Real lens falloff |
| Chromatic Aberration | 0.1–0.35, Start Offset 0.4 | Domain `13` advises **off** for architecture; a very small amount at the frame edge is defensible for a photoreal look. Decide once and be consistent |
| Film Grain | Intensity 0.1–0.3 | The cheapest realism win |
| Depth of Field | Driven by the CineCamera aperture, f/8–f/11 | Not a Post Process Volume setting |
| Motion Blur | Off for stills; shutter angle 180° for sequences | |
| Lens Flares | Off | |
| Colour Grading | Very light. Saturation ≤ ±5%, Contrast ≤ ±10% | |
| LUT | Only if the client has a house look | |

**What not to do:** teal-and-orange grades, heavy contrast S-curves, crushed blacks, "cinematic" letterboxing, lens dirt overlays, and anamorphic flares. Every one of these is a signal that the underlying image did not work.

---

## 8. Real-time versus offline expectations

| Aspect | Unreal (real-time, Lumen) | Unreal (Path Tracer) | Blender Cycles |
|---|---|---|---|
| GI accuracy | Approximate; screen-space and software/hardware ray tracing; some light leaking | Ground truth | Ground truth |
| Reflections | Screen-space + Lumen reflections; misses off-screen detail | Correct | Correct |
| Foliage GI | Approximate; translucency handled by the shading model | Correct but slow | Correct but slow |
| Caustics | Not supported | Limited | Supported with the caustics options |
| Frame time | 8–33 ms | Seconds to minutes per frame | Seconds to minutes per frame |
| Iteration speed | Instant | Slow | Slow |
| Best use here | The whole project: layout, lighting, sequences, client review | A hero still, and as ground truth to validate the Lumen setup | Look-dev of individual assets; the ground-truth reference render |

**The workflow that gets both:** build and light in Lumen; validate periodically against the Path Tracer with the same camera and lights (`Show → Lit → Path Tracing` in the viewport, or the Movie Render Graph's path-tracing node). Where they diverge substantially, Lumen is under-sampling something — usually a small bright source, a highly reflective surface, or foliage translucency. Fix it in the Lumen setup rather than accepting the difference.

**Where real-time genuinely cannot match offline**, and you should say so to a client: caustics through water and glass, perfectly clean mirror reflections of off-screen geometry, and very-many-bounce interreflection in a small bright room.

---

## 9. Look-dev checklist and common failure modes

**Checklist**
- [ ] Light units set project-wide; Directional in lux, Sky Light in cd/m²
- [ ] Sun value from §1.2, not eyeballed
- [ ] Sun `Source Angle` = 0.5357°
- [ ] Sky Light on Real Time Capture; not manually overridden to fix shadows
- [ ] Sky Atmosphere Ground Albedo 0.35–0.45
- [ ] Sun position from real solar geometry for the declared date and time
- [ ] Exposure **Manual**, EV recorded in the shot notes
- [ ] AgX (Blender) / default filmic tonemapper (Unreal); Filmic and Legacy not used
- [ ] Look-dev rig rendered and checked, then hidden
- [ ] Grey sphere reads mid-grey
- [ ] Reference photograph difference-blended and the value structure matched
- [ ] Grade is light: saturation ≤ ±5%, contrast ≤ ±10%
- [ ] Grain, vignette and a trace of CA present
- [ ] Path-traced validation frame rendered and compared
- [ ] Shot checked at 100% and at thumbnail size

**Common failure modes**

| Symptom | Cause | Fix |
|---|---|---|
| Image looks flat and grey | Fog too dense, or exposure too high, or contrast lost to Local Exposure | Reduce Fog Density to 0.005–0.02; set exposure from EV maths; Local Exposure ≥ 0.75 |
| Shadows blue and cold | Sky too dominant; ground albedo too low; white balance overcorrected | Raise Sky Atmosphere Ground Albedo; check the sun/sky ratio; stop neutralising the bounce |
| Shadows black and dead | GI off or under-sampled | Enable Lumen; raise Final Gather Quality; check Max Trace Distance covers the scene |
| Highlights clipped and hue-shifted | Legacy tonemapper, or Standard view transform, or over-bright albedo | Use AgX / the filmic tonemapper; clamp albedo ≤ 0.90 |
| Everything looks over-saturated | Standard view transform, or a heavy grade, or albedo textures saturated in authoring | Switch to AgX; desaturate source albedos toward measured values |
| Sunlight looks weak | Directional light far below 100 000 lux, compensated with exposure | Set the real lux value; then set the exposure |
| Interior blows out through the window | No Local Exposure; wrong EV | Local Exposure 0.75–0.85; expose for the interior and accept a bright window, as a photograph would |
| Sequence flickers between shots | Auto exposure | Manual exposure everywhere |
| The render matches nothing you photographed | No reference-matching pass was done | §6 |
| Looks good on your monitor, wrong on the client's | Uncalibrated display | Calibrate with a hardware probe; check on a second device; deliver sRGB |

## Sources

- [Blender Manual — Color Management](https://docs.blender.org/manual/en/latest/render/color_management.html) — Blender Foundation
- [Blender Manual — Sky Texture Node](https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/sky.html) — Blender Foundation
- [Sky Atmosphere Component in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/sky-atmosphere-component-in-unreal-engine) — Epic Games
- [Exponential Height Fog in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/exponential-height-fog-in-unreal-engine) — Epic Games
- [Atlas of Namibia — Climate](https://atlasofnamibia.online/chapter-3) — Atlas of Namibia
- Internal: `13_software_unreal_engine/03_materials-and-rendering.md`, `13_software_unreal_engine/04_archviz-workflow.md`, `14_software_blender/05_lighting-and-rendering.md`, `18_namibia_context/02_climate-and-weather.md`

## Open questions

- **ColorChecker patch reference values** for building a virtual chart. Take these from a measured chart or the manufacturer's published data rather than from memory. `needs-verification`.
- Whether the **Blender colour management manual URL** used here is current — `docs.blender.org/manual/en/latest/render/color_management.html` returned 404 on 2026-08-25, so the page has moved; the settings described are from domain `14`'s verified summary. `needs-verification` on the new URL.
- Whether **Unreal 5.8** has changed the default working colour space or added new view transforms beyond the ACES-derived filmic tonemapper. `needs-verification`.
- The actual colour temperature of direct sun at Okongo through the day. The 5 000–5 500 K midday figure is standard daylight practice, not a local measurement. `needs-verification`.
