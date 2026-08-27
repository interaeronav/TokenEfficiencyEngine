---
id: blender.lighting_rendering
title: Lighting, rendering and output in Blender
domain: software_blender
tags: [blender, cycles, eevee, sampling, denoising, hdri, sun-position, namibia, okongo, agx, colour-management, render-passes, compositing, output]
jurisdiction: namibia
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Blender 5.2 LTS; EEVEE settings apply from 4.2 LTS (EEVEE Next) onward"
unit_system: metric
sources:
  - {title: "Blender Manual — Cycles Sampling", url: "https://docs.blender.org/manual/en/latest/render/cycles/render_settings/sampling.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — EEVEE Raytracing", url: "https://docs.blender.org/manual/en/latest/render/eevee/render_settings/raytracing.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Light Objects", url: "https://docs.blender.org/manual/en/latest/render/lights/light_object.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Sky Texture Node", url: "https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/sky.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Displays and Views (colour management)", url: "https://docs.blender.org/manual/en/latest/render/color_management/displays_views.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Cameras", url: "https://docs.blender.org/manual/en/latest/render/cameras.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Cryptomatte node", url: "https://docs.blender.org/manual/en/latest/compositing/types/mask/cryptomatte.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Sun Position extension", url: "https://extensions.blender.org/add-ons/sun-position/", publisher: "Blender Foundation / Damien Picard", accessed: 2026-08-25}
  - {title: "NOAA Solar Calculator (algorithm reference cited by the Sun Position add-on)", url: "https://gml.noaa.gov/grad/solcalc/", publisher: "NOAA Global Monitoring Laboratory", accessed: 2026-08-25}
related: [blender.materials, blender.python_api, blender.overview]
---

# Lighting, rendering and output in Blender

**Summary.** Blender ships two production renderers. **Cycles** is an unbiased path tracer: physically correct, noisy until converged, the right choice for final architectural stills. **EEVEE** is a real-time rasteriser with screen-space and ray-traced effects: near-instant, approximate, the right choice for design iteration, client walkthroughs and animation. Both consume the same materials and the same lights, so you can switch. For a Namibian residential project the lighting problem is specific and unusually well-defined: a very high-altitude sun, an extremely bright sky, deep shade, and a design that lives or dies on north-facing overhangs. This file covers both engines, real photometric values, HDRI and sky lighting, exact sun positioning for Okongo (≈17.4° S, 17.6° E), colour management, passes and output.

## Key facts

| Item | Value |
|---|---|
| Engines | Cycles, EEVEE, Workbench. Set via `scene.render.engine`; list them with `blender -E help` |
| Cycles sampling | `Max Samples`, `Noise Threshold` (adaptive sampling; typical 0.1–0.001, 0 = auto), `Min Samples`, `Time Limit` (seconds, 0 = off) |
| Denoisers | **OpenImageDenoise** (usually highest quality; GPU-accelerated on NVIDIA CC ≥ 7.0 and all supported AMD/Intel/Apple GPUs) and **OptiX** (NVIDIA, works on older cards). `Automatic` prefers OIDN. |
| Sun light | `Strength` in **W/m²** when Normalize is on; `Angle` = angular diameter as seen from Earth (real sun ≈ 0.526°) |
| Point/Spot/Area | `Power` in **Watts of radiant flux**, not electrical watts and not "watt-equivalent" bulb ratings |
| Sky Texture types | **Multiple Scattering** (most accurate, default choice), Single Scattering, Preetham (legacy), Hosek/Wilkie (legacy) |
| Sky Texture params | Sun Direction, Turbidity (2 arctic, 3 clear, 6 warm/moist, 10 hazy), Ground Albedo, Sun Disc, Sun Size, Sun Intensity, Sun Elevation, Sun Rotation, Altitude, Air, Aerosols, Ozone |
| View transforms | Standard, ACES 1.3, ACES 2.0, Khronos PBR Neutral, **AgX** (current default photographic transform), Filmic (**deprecated, superseded by AgX**), Filmic Log, False Color, Raw |
| Camera lens | Perspective (Focal Length / FOV), Orthographic (Orthographic Scale), Panoramic (Cycles only), Custom OSL (Cycles only); **Shift X/Y** adjusts vanishing points without skewing verticals |
| Cryptomatte | Enable in `Properties ▸ View Layer ▸ Passes`, use the Cryptomatte node in the compositor |
| Okongo, Ohangwena | ≈ **17.4° S, 17.6° E**; Namibia is **UTC+2 (CAT) year-round**, no daylight saving since 2017 |

## Cycles: how it works and how to configure it

Cycles traces rays from the camera, bounces them around the scene sampling lights and surfaces, and averages many samples per pixel. More samples = less noise, linearly more time. Everything else is an optimisation on that.

**Sampling.** Set `Max Samples` high (1024–4096 for an exterior, 2048–8192 for a daylit interior) and rely on **adaptive sampling** to stop early where the image is already clean. Tick `Noise Threshold` and set it to 0.01 for drafts, 0.005 for client images, 0.002 for print. `Min Samples` prevents adaptive sampling from bailing out too early in dark regions — 64 is a safe floor. `Time Limit` is the useful safety valve for batch renders: set it to, say, 600 s per frame so an overnight batch cannot be consumed by one pathological view. It counts render time only, not pre-processing.

**Denoising.** Leave `Render ▸ Denoise` on with `OpenImageDenoise`, `Prefilter: Accurate`, and `Passes: Albedo + Normal` — the auxiliary passes are what stop the denoiser eating fine detail like grout lines and window mullions. Denoising is not a substitute for samples: denoise a 64-sample interior and you get a waxy, blotchy image. Get the noise threshold low enough that the raw render is nearly clean, then denoise to finish it.

**Light Paths.** For architecture: Max Bounces 12, Diffuse 4, Glossy 4, Transmission 12 (glazing needs them), Volume 2, Transparent 8. Turn **Caustics (Reflective and Refractive) off** unless you specifically want them — they are the main cause of fireflies in glazed scenes — and set `Filter Glossy` to 0.5–1.0. The Light Tree (Sampling ▸ Lights) should stay on in scenes with many small emitters.

**Performance.** `Persistent Data` keeps the scene resident between frames of an animation — a large win when geometry is static. `Fast GI Approximation` (Sampling ▸ Path Guiding area) trades bounce accuracy for speed. Blender 5.2's **Texture Cache** substantially reduces memory and start-up time on texture-heavy scenes, which is the normal archviz condition.

## EEVEE: how it works and when to use it

EEVEE rasterises. It approximates global illumination with light probes, screen-space ray tracing and a "Fast GI" fallback. Since 4.2 (EEVEE Next) it has real ray-traced reflections, ray-traced shadows and volumetrics, and since 4.3 light linking and shadow linking.

The settings that matter for architecture:

- **Raytracing** — enable it. `Threshold` is the maximum BSDF roughness that gets real ray tracing; rougher surfaces fall back to the Fast GI Approximation. Setting it to 1 ray-traces everything and disables Fast GI.
- **Fast GI Method** — `Ambient Occlusion` (fastest) or `Global Illumination` (accounts for bounce light off surroundings). Use Global Illumination for interiors.
- **Fast GI Resolution / Rays / Steps / Precision / Distance / Thickness Near / Far / Bias** — the quality/speed dials. Raise `Steps` before raising `Rays`; more steps means fewer missed occluders, which in turn lets you lower `Thickness` without losing bounce energy.
- **Screen-space limitation** — everything above is a screen-space effect and inherits screen-space limitations: geometry outside the frame does not reflect or occlude. This is why an EEVEE interior looking out of a window can be subtly wrong.
- **Light Probes** — place a Volume probe over each room and Sphere probes near reflective surfaces. Without them, interiors are flat.
- **World ▸ Sun** — EEVEE can extract an intense light source from an HDRI and replace it with a real sun light, with its own `Threshold` and `Angle`. Leave it enabled for outdoor HDRIs; it is what gives crisp shadows instead of a mushy sky.

**Choose EEVEE** for: design iteration, dozens of options a day, client walkthrough animations, quick shadow studies, anything where a 3-second frame beats a 3-minute one. **Choose Cycles** for: final presentation stills, anything with glass or metal that must read correctly, interior daylight where bounce accuracy matters, and anything a client will print.

## Lights and real-world values

The manual is explicit that Blender light power is **radiant flux in Watts**, not the electrical wattage on a bulb box and not the "60 W equivalent" marketing figure of an LED. There is no built-in lumens conversion. Practical approach:

1. Look up the fitting's **luminous flux in lumens** (on the box, or the manufacturer's data sheet).
2. Divide by the luminous efficacy of the source to get radiant watts. For white LED and fluorescent sources, 250–350 lm/W of *radiant* power is a workable approximation for the visible band; for a warm-white LED, dividing lumens by roughly 300 gives a usable radiant-watt figure.
3. Adjust by eye against the exposure, because the view transform and exposure settings dominate perceived brightness anyway.

Working starting values for a residential interior at 1.0 exposure with AgX:

| Fitting | Blender light | Power |
|---|---|---|
| Recessed LED downlight (~800 lm) | Point, Radius 0.03 m | 3–5 W |
| LED strip under a kitchen wall unit | Area (rectangle, actual strip length × 0.01 m) | 5–15 W |
| Pendant with a diffuser | Point or small Sphere area, Radius 0.1 m | 8–20 W |
| Ceiling luminaire (~2000 lm) | Area disc 0.3 m | 10–25 W |
| Exterior bulkhead | Point, Radius 0.05 m | 5–10 W |
| **Sun (clear day)** | Sun, Angle 0.526° | **~1000 W/m²** with Normalize on |

> ⚠️ Set the **Radius** (Point/Spot) or **Size** (Area) to the physical size of the emitting surface. A zero-radius point light gives razor-sharp, unrealistic shadows and is the fastest way to make an interior look fake. A real downlight aperture is 30–90 mm.

Sun `Angle` at 0.526° is the true angular diameter of the sun and gives correct penumbra softness. Widening it to 1–3° softens shadows for a hazy day; the Ohangwena dry season is not hazy, so keep it near 0.5° for anything from May to October.

## HDRI environment lighting

An equirectangular HDRI in the World shader is the fastest way to get correct ambient light and reflections.

```
[Texture Coordinate ▸ Generated] → [Mapping (Rotation Z)] → [Environment Texture (.hdr/.exr)] → [Background (Strength)] → [World Output]
```

The Environment Texture node's Projection is `Equirectangular` (or `Mirror Ball`); leave the Vector unconnected and the image maps with **Z as up**. Add the Mapping node purely so you can rotate the sky to put the sun where the site needs it.

Notes:

- Use a **4K or larger** HDRI if the sky is visible in reflections or in frame; 1K is fine if it is only lighting.
- Poly Haven's HDRIs are CC0 and are the standard free source. Its outdoor sets include the sun in the image, so you often do not need a separate sun light — but a real Sun object gives sharper, controllable shadows, and EEVEE's World ▸ Sun extraction exists precisely to convert one into the other.
- `Film ▸ Transparent` in Render Properties removes the sky from the alpha channel so you can composite a photographic backplate — the normal deliverable for a site-specific Namibian render where the client wants the real horizon.
- For an interior, add **Light Portals** (Area lights with `Portal` enabled, in Cycles) filling each window opening. They tell the sampler where the light comes in and cut interior noise dramatically.

**Sky Texture as an alternative.** The Sky Texture node (`Multiple Scattering` type) generates a physically modelled sky from Sun Elevation, Sun Rotation, Turbidity, Ozone, Air, Aerosols, Ground Albedo and Altitude. It is analytically correct, infinitely sharp, and free of a photograph's baked-in time and place — ideal for a shadow study where the sun must be at a known azimuth. The manual warns that Single and Multiple Scattering skies are **very bright by default (because they are accurate)** and that you should lower `Properties ▸ Render ▸ Color Management ▸ Exposure` to compensate rather than dimming the sky.

For northern Namibia in the dry season, Turbidity 2.5–3 (clear sky), Ozone ~1, Aerosols 0.3–0.7, Ground Albedo 0.3–0.4 (dry sand and Kalahari sandveld are bright), Altitude ~1100 m.

## Sun positioning for Okongo, Ohangwena, Namibia

**Site data.**

| Parameter | Value |
|---|---|
| Latitude | ≈ **−17.4°** (17.4° **South**) |
| Longitude | ≈ **+17.6°** (17.6° **East**) |
| Time zone | **UTC+2** (Central Africa Time), all year — Namibia has had no daylight saving since 2017 |
| Elevation | ≈ 1100 m |

**Two consequences that shape the architecture.** At 17.4° S the sun is directly overhead twice a year (when solar declination equals −17.4°, i.e. around early November and early February). Between those dates the midday sun is slightly **south**; for the remaining ~9 months of the year — including the whole cool season — the midday sun is **north**. So north-facing openings need deep horizontal shading, east and west elevations take the punishing low-angle sun, and a south wall is in shade for most of the year. Any Blender daylight study must therefore cover at least: **21 June** (winter solstice, sun lowest, solar-noon altitude ≈ **49°**, sun to the **north**), **21 December** (summer solstice, solar-noon altitude ≈ **84°**, sun just to the **south**), and an **equinox** (≈ **73°**, sun effectively overhead-north). Note that Namibia's clock is set to the 30° E meridian while Okongo sits at 17.6° E, so **solar noon falls at roughly 12:50 CAT**, not 12:00 — shadow studies run at clock noon are about 50 minutes early.

### Option A — the Sun Position add-on

Sun Position is a bundled/official extension (GPL-3.0-or-later, maintained by Damien Picard, v4.4.0 as of Nov 2025) that computes sun position from geographic coordinates, date and time using the NOAA solar calculator algorithms and Jean Meeus' *Astronomical Algorithms*. It works in two modes: **Sun Object Mode**, which drives a Sun light and/or a Sky Texture from location and time, and **Environment Mode**, which synchronises an environment texture with a sun light so they rotate together.

Enable it in `Edit ▸ Preferences ▸ Add-ons` (search "Sun Position"; install from `Get Extensions` if it is not present). Its panel lives in the **World Properties** editor. Enter Latitude `−17.4`, Longitude `17.6`, UTC zone `+2`, the date and the time, and set North Offset if your model's +Y is not true north (model with **+Y = north** and it is zero).

### Option B — compute it in Python (no add-on, fully deterministic)

This is the preferred route for agent-driven work: it is reproducible, has no add-on dependency, and runs in background mode. It implements the same NOAA general solar position equations the add-on cites.

```python
"""Place a Sun light for a real date/time at a real location.
Model convention: +Y = true north, +X = east, +Z = up, 1 unit = 1 m.
Implements the NOAA general solar position equations.
"""
import bpy, math, datetime
from mathutils import Vector


def solar_altaz(lat_deg, lon_deg, utc_offset_h, year, month, day, hour, minute=0):
    """Return (altitude, azimuth) in radians. Azimuth is clockwise from true north."""
    doy = datetime.date(year, month, day).timetuple().tm_yday
    hour_frac = hour + minute / 60.0

    gamma = 2.0 * math.pi / 365.0 * (doy - 1 + (hour_frac - 12.0) / 24.0)

    eqtime = 229.18 * (0.000075
                       + 0.001868 * math.cos(gamma)
                       - 0.032077 * math.sin(gamma)
                       - 0.014615 * math.cos(2 * gamma)
                       - 0.040849 * math.sin(2 * gamma))          # minutes

    decl = (0.006918
            - 0.399912 * math.cos(gamma)     + 0.070257 * math.sin(gamma)
            - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma)
            - 0.002697 * math.cos(3 * gamma) + 0.001480 * math.sin(3 * gamma))   # radians

    time_offset = eqtime + 4.0 * lon_deg - 60.0 * utc_offset_h     # minutes
    tst         = hour_frac * 60.0 + time_offset                   # true solar time, minutes
    ha          = math.radians(tst / 4.0 - 180.0)                  # hour angle, radians

    lat = math.radians(lat_deg)
    cos_zen = (math.sin(lat) * math.sin(decl)
               + math.cos(lat) * math.cos(decl) * math.cos(ha))
    cos_zen = max(-1.0, min(1.0, cos_zen))
    zen = math.acos(cos_zen)
    alt = math.pi / 2.0 - zen

    denom = math.cos(lat) * math.sin(zen)
    if abs(denom) < 1e-9:
        az = 0.0
    else:
        c = max(-1.0, min(1.0, (math.sin(lat) * cos_zen - math.sin(decl)) / denom))
        az = math.pi - math.acos(c)
        if ha > 0.0:                       # afternoon
            az = 2.0 * math.pi - az
    return alt, az


def place_sun(obj, lat, lon, tz, y, mo, d, h, mi=0):
    alt, az = solar_altaz(lat, lon, tz, y, mo, d, h, mi)
    # unit vector FROM the site TOWARDS the sun, in a +Y=north / +X=east / +Z=up frame
    direction = Vector((math.sin(az) * math.cos(alt),
                        math.cos(az) * math.cos(alt),
                        math.sin(alt)))
    # a Sun lamp emits along its local -Z, so aim its local +Z at the sun
    obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    return math.degrees(alt), math.degrees(az)


# --- Okongo, Ohangwena, Namibia -------------------------------------------
LAT, LON, TZ = -17.4, 17.6, 2

sun_data = bpy.data.lights.new("Sun_Okongo", type='SUN')
sun_data.energy = 1000.0                      # W/m^2, clear-sky order of magnitude
sun_data.angle  = math.radians(0.526)         # true angular diameter of the sun
sun = bpy.data.objects.new("Sun_Okongo", sun_data)
bpy.context.scene.collection.objects.link(sun)

for label, (mo, d) in {"winter solstice": (6, 21),
                       "equinox":         (9, 22),
                       "summer solstice": (12, 21)}.items():
    for h in (9, 12, 15):
        a, z = place_sun(sun, LAT, LON, TZ, 2026, mo, d, h)
        print(f"{label:16s} {h:02d}:00  altitude {a:6.2f} deg  azimuth {z:7.2f} deg from N (CW)")
```

Run it, note the printed altitudes and azimuths, and sanity-check them against the NOAA solar calculator for the same date and coordinates before you trust a shading study to it. Expect winter-solstice solar noon at roughly 49° altitude with the sun to the north (azimuth near 0°), and summer-solstice noon at roughly 84° with the sun just south of the zenith. Running the script above for 2026 gives, for example, winter 12:00 → altitude 47.3° / azimuth 17.3°, equinox 12:00 → 69.2° / 31.1°, summer 12:00 → 77.4° / 120.4° — all consistent with true solar noon arriving near 12:50.

**Model north.** Decide once that **+Y is true north** and never deviate. Then a site plan imported from DXF, an HDRI rotation, the Sky Texture's Sun Rotation and the script above all agree. If you must rotate the model, record the offset in a scene custom property.

## Camera and lens

Architectural camera conventions:

- **Focal length** 18–24 mm for cramped interiors, 24–35 mm for general interiors and exterior three-quarter views, 50–85 mm for detail and joinery shots. Below 18 mm the distortion reads as an estate-agent photograph.
- **Keep the camera level** and use **Shift Y** rather than tilting. The manual's own illustration makes the point: lens shift preserves horizontal and vertical lines, whereas rotating the camera skews them. Vertical convergence is the single clearest tell of an amateur architectural render.
- **Camera height** 1.5–1.6 m for interiors (standing eye level), 1.2 m for a seated view, 1.6–1.8 m for exteriors.
- **Sensor** defaults to 36 mm width; leave it unless matching a real camera.
- **Depth of field** — `Properties ▸ Object Data ▸ Depth of Field`, with a Focus Object rather than a typed distance, and F-Stop 2.8–5.6 for a detail shot, 8–16 or DOF off entirely for a whole-room view. Architecture is normally rendered nearly all-in-focus.
- **Clip Start/End** — 0.01 m and 1000 m (file `01`). The manual notes ray-traced renders tolerate extreme values better than the rasterised viewport does, but there is no reason to be sloppy.
- **Orthographic** cameras with a set Orthographic Scale produce true elevations and plans directly from the model — the fastest route to a scaled elevation drawing without leaving Blender.

## Exposure and colour management

`Properties ▸ Render ▸ Color Management`:

- **View Transform** — use **AgX**. The manual states AgX improves on Filmic, gives more photorealistic results, offers 16.5 stops of dynamic range and desaturates highly exposed colours to mimic film's response; and that **Filmic is deprecated and superseded by AgX**. Do not start new work on Filmic. Use `Standard` only when the image is already graded or when you need exact colour matching. `Khronos PBR Neutral` is aimed at product-photography accuracy and is a reasonable choice for a joinery product shot where the client's melamine decor colour must match a swatch. `False Color` is a diagnostic: it heat-maps luminance so you can see whether the image is properly exposed.
- **Look** — `AgX - Base Contrast` is a sane default; `Medium High Contrast` for a punchier exterior.
- **Exposure** — in stops. Raise it for a dim interior, lower it for a Sky-Texture-lit exterior (the manual explicitly recommends lowering exposure rather than dimming an accurate sky).
- **Working Space** (5.0+) — Linear Rec.709 unless a pipeline demands ACEScg. Set at project start (file `04`).

## Render passes and compositing

Enable passes in `Properties ▸ View Layer ▸ Passes`. The useful set for architecture:

- **Combined** — the beauty pass.
- **Z / Mist** — depth. Mist is the easier one to grade; set its Start/Depth in World Properties.
- **Diffuse / Glossy / Transmission ▸ Direct, Indirect, Color** — lets you rebalance bounce light and reflections after rendering without re-rendering.
- **Ambient Occlusion** — a contact-shadow multiply layer.
- **Normal** and **Position** — for relighting tricks and for driving compositor masks.
- **Cryptomatte Object / Material / Asset** — per-object and per-material mattes with correct anti-aliased and motion-blurred edges. Enable the pass, add a **Cryptomatte** node in the compositor, and pick objects with the eyedropper. This is how you change one wall's colour in post, or isolate the joinery for a separate grade, without a re-render. (Use the current Cryptomatte node, not the legacy one; the current node does not need the CryptoObject passes wired to it.)

Save to **multilayer OpenEXR** to keep every pass in one file. Then composite in Blender's compositor (35 new nodes in 5.2, plus compositing assets), or take the EXR to a dedicated compositor.

A minimal, high-value archviz comp: Render Layers → *Denoise* (if not denoising at render time) → *Color Balance* → *Glare* (Fog Glow, low threshold, for a soft bloom on bright windows) → *Unsharp Mask* (Radius small, Factor low) → Composite. Everything else is taste.

## Output settings

`Properties ▸ Output`:

- **Resolution** — 3840 × 2160 for presentation stills, 1920 × 1080 for animation, `Resolution %` at 25–50 for test renders.
- **Frame Rate** — 25 fps for European/African broadcast conventions, 30 fps for web.
- **File Format** —
  - *Stills for client review*: PNG, RGBA, 16-bit if it will be graded.
  - *Stills for print or grading*: OpenEXR (multilayer if you enabled passes), Float (Half), ZIP or DWAA compression.
  - *Animation*: render an **image sequence** (PNG or EXR), never straight to video. A crashed frame 400 of 500 then costs one frame, not the job. Assemble in the Video Sequencer or ffmpeg afterwards.
  - *Final video*: FFmpeg Video, MPEG-4 container, H.264, Output Quality "High Quality" or "Perceptually Lossless", Encoding Speed "Good", plus AAC audio if any.
- **Colour depth and `Save as Render`** — leave `Save as Render` ticked so the view transform is applied on save.
- **Path templating** — the output path accepts `//` for blend-relative, `#` characters for zero-padded frame numbers (`render_####.png` → `render_0001.png`), and template tokens such as `{blend_name}`.

Command line for a batch:

```bash
blender -b house.blend -S "Presentation" -E CYCLES \
        -o //renders/exterior_#### -F PNG -x 1 \
        -f 1 -- --cycles-device OPTIX
```

`-E help` lists the available engine identifiers on your build; `-f 1,5,9` renders a list of frames and `-f 1..24` a range; `-a` renders the whole frame range; `--cycles-print-stats` logs memory and time.

## Sources

- [Manual — Cycles Sampling (adaptive sampling, noise threshold, time limit, denoiser)](https://docs.blender.org/manual/en/latest/render/cycles/render_settings/sampling.html) — accessed 2026-08-25 via the version-matched local manual bundle
- [Manual — EEVEE Raytracing and Fast GI Approximation](https://docs.blender.org/manual/en/latest/render/eevee/render_settings/raytracing.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — EEVEE World Settings (sun extraction from HDRI)](https://docs.blender.org/manual/en/latest/render/eevee/world_settings.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Light Objects and Power of Lights](https://docs.blender.org/manual/en/latest/render/lights/light_object.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Sky Texture node](https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/sky.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Environment Texture node](https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/environment.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Displays and Views (AgX, Filmic deprecation, False Color)](https://docs.blender.org/manual/en/latest/render/color_management/displays_views.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Cameras (lens, shift, clipping)](https://docs.blender.org/manual/en/latest/render/cameras.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Cryptomatte node](https://docs.blender.org/manual/en/latest/compositing/types/mask/cryptomatte.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Command Line Arguments (render and Cycles options)](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html) — accessed 2026-08-25 via the local manual bundle
- [Sun Position extension listing](https://extensions.blender.org/add-ons/sun-position/) — accessed 2026-08-25
- [NOAA Global Monitoring Laboratory Solar Calculator](https://gml.noaa.gov/grad/solcalc/) — cited by the Sun Position add-on as its algorithm source; accessed 2026-08-25

## Open questions

- **[NA]** Okongo's coordinates are given to one decimal place as supplied in the brief (≈17.4° S, 17.6° E). Take the exact site coordinates from the survey diagram before a shading study is used to justify an overhang depth — a 0.1° error is ~11 km and shifts solar time by ~24 s, which is negligible, but a sign or transposition error is not.
- Namibia's permanent UTC+2 (no DST) is stated from general knowledge of the 2017 change and is **needs-verification** against the current statute if legal precision is required.
- The lumens→radiant-watts conversion factor (~300 lm/W for white LED) is a working approximation, not a Blender-documented figure; Blender provides no lumens input.
- The clear-sky sun value of ~1000 W/m² is the standard solar-constant-at-sea-level figure, not a Blender default; the Blender default Sun strength is much lower.
- Whether `Filmic` remains selectable in 5.2 or has been removed: the manual still documents it and marks it deprecated.
