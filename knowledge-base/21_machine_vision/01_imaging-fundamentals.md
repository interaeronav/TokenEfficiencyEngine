---
id: vision.imaging
title: Imaging fundamentals — light, illumination, optics and sensors
domain: 21_machine_vision
tags: [illumination, lighting, optics, lens, focal-length, depth-of-field, telecentric, sensor, cmos, ccd, shutter, camera-selection]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Understanding Focal Length and Field of View", url: "https://www.edmundoptics.com/knowledge-center/application-notes/imaging/understanding-focal-length-and-field-of-view/", publisher: "Edmund Optics", accessed: 2026-08-25}
  - {title: "Image sensor format", url: "https://en.wikipedia.org/wiki/Image_sensor_format", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Vision Standards", url: "https://www.automate.org/vision/vision-standards/vision-standards", publisher: "A3", accessed: 2026-08-25}
related: [vision.overview, vision.calibration, vision.deployment]
unit_system: SI
---

# Imaging fundamentals — light, illumination, optics and sensors

**Summary.** Everything a vision system can ever know arrives through three components chosen before any code is written: the light, the lens and the sensor. Get them right and the algorithm is trivial; get them wrong and no amount of deep learning recovers the information that was never captured. This file covers the electromagnetic basis of imaging, the seven canonical illumination geometries and when each is correct, the lens equations that govern field of view, depth of field and distortion, the sensor properties that actually matter (shutter type, pixel size, quantum efficiency, dynamic range), and two fully worked selection calculations — a general inspection station and a joinery panel gauge.

## Key facts

| Quantity | Formula / value | Note |
|---|---|---|
| Magnification | `m = S / FOV` | `S` = sensor dimension, same axis as FOV |
| Focal length (approximation) | `f ≈ S × WD / FOV` | Valid for `m < 0.1`; Edmund Optics Eq. 3 |
| Focal length (exact, thin lens) | `f = WD × m / (1 + m)` | `WD` measured to the lens principal plane |
| Object distance from `f` and `m` | `WD = f × (1 + 1/m)` | |
| Angular field of view | `AFOV = 2·arctan(S / 2f)` | |
| Spatial sampling | `mm/px = FOV_width / pixel_count_width` | |
| Total depth of field (close-up) | `DoF ≈ 2·N·c·(1 + m) / m²` | `N` = f-number, `c` = circle of confusion |
| Airy disk diameter | `d = 2.44 · λ · N · (1 + m)` | λ ≈ 0.55 µm for visible |
| Diffraction-limit threshold | `N > p / (1.22 λ)` starts softening | `p` = pixel pitch |
| Practical detection rule | ≥ 3 px across the smallest feature to **find** | ≥ 10 px to **measure** it |
| Subpixel edge repeatability | 1/4 to 1/10 px on a clean, high-contrast edge | Not accuracy — repeatability |

## Light and the spectrum

Machine vision uses a narrow slice of the electromagnetic spectrum, but which slice is a genuine design variable.

| Band | Wavelength | Typical use |
|---|---|---|
| UV-A | 365–405 nm | Fluorescence (adhesive beads, UV-tracered coatings), fine surface scratch enhancement |
| Blue | 450–470 nm | Highest resolution of visible LEDs (shortest λ → smallest diffraction spot); good contrast on red/orange parts |
| Green | 520–530 nm | Peak human and sensor sensitivity; general purpose |
| Red | 620–660 nm | Cheapest and brightest LED per watt; penetrates some plastics; standard default |
| NIR | 850, 940 nm | Sees through some inks and plastics; silicon still responds; 940 nm is nearly invisible to the eye, useful where flicker annoys operators |
| SWIR | 1000–1700 nm | Requires InGaAs sensors. Moisture content in timber, silicon wafer inspection, seeing through many opaque plastics |
| Thermal LWIR | 8–14 µm | Microbolometer cameras; heat, not reflected light. Building envelope thermography, electrical inspection |

Three practical consequences:

1. **Monochromatic light plus a matched bandpass filter defeats ambient light.** A 625 nm LED with a 625 ± 10 nm filter rejects most of a workshop's fluorescent and daylight contribution. This is the standard fix for uncontrolled environments and should be reached for before software.
2. **Shorter wavelength = finer detail**, because the diffraction limit scales with λ. Blue light on a diffraction-limited system resolves roughly 1.4× finer than red.
3. **SWIR is the honest answer to timber moisture and some sub-surface defect work**, and it is expensive — InGaAs cameras run an order of magnitude above silicon.

## Illumination techniques

The geometry of the light relative to the surface and the camera determines what becomes visible. Learn these seven and you have covered ~95 % of industrial cases.

**Bright field (direct, front).** Light strikes the surface and specularly reflects into the lens. Flat, smooth, reflective surfaces appear bright; defects that scatter appear dark. Cheap, high contrast on flat parts, but it produces glare hot-spots on curved or glossy surfaces.

**Dark field.** Light comes in at a very low angle (typically 10–30° from the surface plane) so specular reflection misses the lens entirely. The background goes black; only features that scatter — scratches, engraved marks, edges, dust, raised print, surface tear-out — light up. **This is the correct choice for surface scratch and engraving inspection**, and it is under-used. On a sanded joinery panel, low-angle dark field is the single best way to reveal sanding scratches, glue squeeze-out and grain tear.

**Backlight (transmitted).** The part sits between the light and the camera; you image its silhouette. Contrast is essentially infinite, edges are crisp, and the resulting binary image is the ideal input to a dimensional gauge. **Anything you must measure to tight tolerance should be backlit if the geometry allows it.** Combine with a telecentric lens for the highest-accuracy gauging.

**Diffuse dome ("cloudy day" illuminator).** A hemispherical diffuser with LEDs firing at its inner wall, camera looking through a hole at the top. Produces near-uniform light from all directions, eliminating specular hotspots. Correct for shiny, curved or crumpled surfaces — foil, chrome, curved metal, glossy lacquered panels. Expensive, bulky, and it kills texture contrast, which is sometimes a problem.

**Coaxial / on-axis (DOAL — diffuse on-axis light).** A beamsplitter puts the light source on the optical axis, so illumination arrives perpendicular to a flat surface and reflects straight back. Flat specular areas go bright white; anything tilted or textured goes dark. Ideal for reading laser-etched codes on polished metal and for flatness/planarity checks.

**Ring light.** LEDs in an annulus around the lens. The default general-purpose light. Cheap and convenient; produces a characteristic ring-shaped glare on specular surfaces and a doughnut of uneven illumination at short working distances. Variants: high-angle (bright-field-ish), low-angle ring (dark-field-ish), segmented/quadrant rings for shape-from-shading.

**Structured light.** A projector casts a known pattern — a single laser line, a stripe sequence, phase-shifted sinusoids, or a pseudorandom dot field — and the deformation of that pattern in the camera image encodes depth. Laser-line triangulation profilers (Keyence LJ-X, Cognex 3D-A1000, LMI Gocator, Photoneo) are the workhorse of 3D industrial inspection and reach micron-level Z resolution over small fields. See `02` for the geometry.

Two second-order but decisive properties: **strobing** (a strobed LED at 10–20× continuous current freezes motion and dominates ambient light, at the cost of driver complexity) and **stability** (LEDs lose output as they age and as junction temperature rises; a system calibrated in a cold shop in July will drift by February unless the light is current-regulated and thermally managed).

## Lenses and optics

### Focal length, field of view and working distance

The three are locked together by the sensor size. Choose any two and the third follows.

```
m   = S / FOV                     (magnification)
f   ≈ S × WD / FOV                (approximation, m < 0.1)
f   = WD × m / (1 + m)            (exact thin lens)
WD  = f × (1 + 1/m)               (exact thin lens)
AFOV= 2 · arctan(S / 2f)
```

Lenses are sold in a standard ladder — 4, 6, 8, 12, 16, 25, 35, 50, 75, 100 mm — so the workflow is: compute the ideal `f`, pick the nearest standard value *below* it (to guarantee you cover the FOV), then recompute the actual working distance from `WD = f(1 + 1/m)`.

**Lens image circle must cover the sensor.** A lens sold as "2/3 inch format" will vignette on a 1.1" sensor. Check the specified format, not the mount.

### Aperture and f-number

`N = f / D` where `D` is the entrance pupil diameter. Opening up (lower `N`) gains light as `1/N²` and loses depth of field roughly linearly. Closing down gains depth of field until diffraction takes over.

**Diffraction.** The Airy disk diameter is `d = 2.44 λ N (1+m)`. At λ = 0.55 µm and f/8 with `m ≈ 0`, `d ≈ 10.7 µm`. On a sensor with 3.45 µm pixels that spot spans about three pixels — the lens, not the sensor, now limits resolution. The threshold to remember: **softening begins around `N ≈ p / (1.22 λ)`**; for 3.45 µm pixels that is roughly f/5. Most industrial systems live between f/4 and f/8, and going to f/16 "for depth of field" quietly throws away half the resolution you paid for.

### Depth of field

```
DoF_total ≈ 2 · N · c · (1 + m) / m²
```

`c`, the circle of confusion, is a decision, not a physical constant: choose 1 pixel for strict work, 2 pixels for tolerant work. DoF grows with f-number and collapses quadratically as magnification rises. At `m = 0.5` you will be fighting for a couple of millimetres.

### Distortion

Real lenses depart from the pinhole model. **Barrel** distortion (magnification falls with radius) is typical of short focal lengths; **pincushion** (magnification rises with radius) of long ones. Machine-vision lenses are specified with a distortion percentage — under 0.1 % for metrology grade, 1–3 % for a cheap wide-angle. Distortion is *correctable by calibration* (`02`), so a well-calibrated 1 % lens can out-measure an uncalibrated 0.1 % lens. What is not correctable is chromatic aberration in a colour system, vignetting beyond a couple of stops, and any loss of contrast (MTF) — so specify MTF at the Nyquist frequency of your pixel pitch, not just the megapixel rating.

### Telecentric lenses

An **object-space telecentric** lens has its entrance pupil at infinity, so the chief rays are parallel to the optical axis. Consequences:

- **Magnification is constant with object distance.** A part 5 mm nearer the camera images at exactly the same size. This eliminates the dominant error source in dimensional gauging of parts with thickness or presentation variation.
- **No perspective error.** You see the top face of a bore, not its side wall — bore diameters measure correctly.
- **Constraint:** the front element must be at least as large as the field of view. A 100 mm telecentric lens is physically large and expensive (four figures in EUR/USD for good ones); above ~200 mm FOV they become impractical.

> ⚠️ If a specification says "measure to ± 0.05 mm" and the part position varies by more than a millimetre in depth, an entocentric lens cannot meet it without depth compensation. Either fixture the part rigidly, use telecentric optics, or measure in 3D.

## Sensors

### CCD vs CMOS

CCD is effectively obsolete in new industrial designs. Sony discontinued CCD production, and modern CMOS — particularly Sony's Pregius global-shutter family (IMX250, IMX264, IMX253, IMX304, IMX530/Pregius S) — matches or beats CCD on noise, dynamic range and quantum efficiency while adding speed, lower power, region-of-interest readout and on-chip functions. CCD survives only in legacy systems and some scientific niches.

### Global vs rolling shutter — the decision that matters most

A **global shutter** exposes every pixel simultaneously. A **rolling shutter** exposes rows sequentially, so a moving object is skewed, a rotating fan blade bends, and a strobed light illuminates only part of the frame. For any application with relative motion, or with strobed/pulsed illumination, or with LED-lit scenes that flicker, **specify global shutter**. Rolling shutter is acceptable for static inspection, stationary tripod photogrammetry and most site-progress photography — but it corrupts drone photogrammetry unless the flight is slow and the software models the rolling-shutter effect (Pix4D, Agisoft Metashape and COLMAP all have some support; see `02`).

### Resolution, pixel size and the sampling rule

`mm per pixel = FOV_width / horizontal_pixels`. Then:

- **To detect** a feature reliably: at least 3 pixels across it (Nyquist says 2; practice says 3–5 for noise tolerance).
- **To measure** a feature: 10+ pixels across it, with subpixel edge fitting adding a factor of 4–10 in repeatability.
- **To classify** with a CNN: the object should occupy at least ~32 × 32 px in the network's input resolution, which after resizing is a much harsher requirement than it sounds.

Bigger pixels collect more photons (better SNR, better dynamic range) but give coarser sampling for a given sensor size. 3.45 µm is the current industrial sweet spot; 2.74 µm and 2.5 µm sensors trade light for resolution.

### Dynamic range, quantum efficiency, bit depth

**Quantum efficiency (QE)** is the fraction of incident photons that produce a counted electron; modern monochrome CMOS peaks around 70 % near 525 nm. A colour sensor of the same die has roughly one-third the effective QE per pixel because each pixel sees only one Bayer channel through a filter.

**Dynamic range** is full-well capacity divided by read noise, expressed in dB (`20·log10(ratio)`). Industrial global-shutter sensors typically deliver 65–72 dB. **HDR** modes (dual-gain, multi-exposure) push this higher at a cost in frame rate or motion artefacts.

**Bit depth** — 8-bit is enough for pass/fail on a well-lit scene; 10- or 12-bit matters when you must recover detail in both a bright specular highlight and a shadow, or when doing subpixel gradient work. Bit depth is only useful if the noise floor is below the least significant bit; a 12-bit camera with 4 counts of noise is a 10-bit camera.

### Colour vs monochrome

Default to **monochrome** unless colour is the discriminating feature. Reasons: a Bayer colour sensor demosaics, so true spatial resolution is roughly 70 % of the monochrome equivalent; colour costs about 3× in light; and a monochrome sensor plus a coloured light plus a filter gives you *selectable* colour contrast with full resolution. Use colour when you must verify colour matching (lacquer, veneer, wire harnesses), when the model is a pretrained RGB network, or when a human must review the images.

## Worked example 1 — a general inspection station

**Requirement.** Inspect a 280 × 200 mm printed component for missing print and a defect down to 0.6 mm. Working distance constrained to roughly 500 mm by the machine guard. Part sits on a conveyor with ± 3 mm height variation, moving at 150 mm/s, indexed and stopped for imaging.

**1. Required sampling.** To *detect* a 0.6 mm defect at 3 px minimum → 0.2 mm/px. To be safe against orientation and contrast, target 0.15 mm/px.

**2. Pixel count.** 280 mm / 0.15 = 1867 px horizontally; 200 / 0.15 = 1333 px vertically. Add ~10 % FOV margin for part placement → FOV 310 × 225 mm, requiring 2067 × 1500 px. The Sony IMX250 (2448 × 2048, 3.45 µm, "2/3 inch" type, sensor 8.45 × 7.07 mm) comfortably covers it and is the commonest 5 MP industrial sensor.

**3. Achieved sampling.** 310 mm / 2448 px = **0.127 mm/px** → a 0.6 mm defect spans 4.7 px. Good.

**4. Focal length.** `m = 8.45 / 310 = 0.02726`. Approximation: `f ≈ 8.45 × 500 / 310 = 13.6 mm`. Nearest standard below: **12 mm**. Recompute the true working distance: `WD = 12 × (1 + 1/0.02726) = 12 × 37.68 = 452 mm` to the principal plane — inside the guard envelope, so acceptable.

**5. Depth of field.** With `c` = 2 px = 6.9 µm and f/8: `DoF ≈ 2 × 8 × 0.0069 × 1.0273 / 0.02726² = 0.1134 / 0.000743 = 152 mm`. Vastly more than the ± 3 mm needed, so we can open up. At f/4: ≈ 76 mm — still ample, and f/4 keeps us clear of the diffraction threshold (`N > 3.45/0.671 ≈ 5.1`). **Choose f/4–f/5.6.**

**6. Exposure and light.** Part is stopped, so blur is not critical, but allow for index jitter: at 150 mm/s residual creep, 1 ms exposure gives 0.15 mm of smear = 1.2 px. Acceptable. Choose a red (625 nm) diffuse bright-field bar-light pair at ± 45° plus a 625 nm bandpass filter to reject shed lighting.

**7. Sanity check on the lens.** A 12 mm lens with 2/3" image circle and < 1 % distortion, MTF specified at 145 lp/mm (Nyquist for 3.45 µm = 1/(2 × 0.00345) = 145 lp/mm). Do not buy a "5 MP lens" without checking that number.

## Worked example 2 — joinery panel dimension gauge

**Requirement.** Measure the length and width of melamine-faced panels up to 1200 × 600 mm to a stated tolerance of ± 0.3 mm, in a workshop.

**1. Reject the single-camera idea immediately.** One camera covering 1200 mm on a 2448 px sensor gives 0.49 mm/px. Even with 1/5-pixel subpixel edge fitting (≈ 0.1 px repeatability) that is 0.05 mm repeatability — *seemingly* fine — but the accuracy is destroyed by perspective error: an entocentric lens at that FOV has several degrees of chief-ray angle at the corners, so any variation in panel thickness (16 mm vs 18 mm board, ± 0.2 mm thickness tolerance) shifts the apparent edge by a large fraction of a millimetre.

**2. Correct architecture: four corner cameras on a rigid frame.** Each camera views one corner over a small FOV (say 60 × 50 mm) through a **telecentric** lens, backlit from below. Panel edges appear as perfect silhouettes.

- FOV 60 mm on 8.45 mm sensor → `m = 0.141`. A 0.14× telecentric lens is a standard catalogue item.
- Sampling: 60 / 2448 = **0.0245 mm/px**. Subpixel edge fitting at 1/5 px → ≈ **0.005 mm** repeatability per edge.
- The measurement is then corner-to-corner across a *calibrated frame*, so the error budget is dominated by the mechanical frame's thermal stability, not by the optics.

**3. Error budget (see `09` for the full version).** Optical edge repeatability 0.01 mm; calibration artefact uncertainty 0.05 mm; frame thermal expansion of a 1.2 m steel beam over 10 °C at 12 µm/m/°C = 0.14 mm; panel bow and support 0.10 mm. Root-sum-square ≈ 0.18 mm — inside ± 0.3 mm with margin, and it tells you immediately that the money goes into a temperature-stable frame, not a better camera.

> ⚠️ This example is the general lesson of the whole file: once the optics are competently chosen, the accuracy limit of an industrial vision gauge is nearly always mechanical and thermal, not optical.

## Sources

- [Edmund Optics — Understanding Focal Length and Field of View](https://www.edmundoptics.com/knowledge-center/application-notes/imaging/understanding-focal-length-and-field-of-view/) — equations for AFOV, `f = H·WD/FOV`, `m = H/FOV`.
- [Wikipedia — Image sensor format](https://en.wikipedia.org/wiki/Image_sensor_format) — origin of the legacy "inch type" nomenclature (video camera tube outside diameter, ~1.5× the actual diagonal).
- [A3 Vision Standards](https://www.automate.org/vision/vision-standards/vision-standards).

## Open questions

- Specific Sony sensor figures quoted here (IMX250: 2448 × 2048 at 3.45 µm; ~70 % peak QE; 65–72 dB dynamic range for the Pregius family) are from general industry familiarity and were **not** re-verified against a Sony datasheet in this pass — treat as indicative and check the camera vendor's EMVA 1288 report before designing to them. Marked `needs-verification` at the numeric level.
- SWIR timber moisture measurement wavelengths (the water absorption bands near 1450 nm and 1940 nm) are stated qualitatively only; no primary source fetched.

