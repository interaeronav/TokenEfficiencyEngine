---
id: envasset.reference_scanning
title: Reference, photogrammetry, scanning and HDRI capture
domain: 25_environmental_asset_creation
tags: [reference, photogrammetry, realityscan, realitycapture, metashape, meshroom, polycam, lidar, hdri, cross-polarisation, delighting, skyfi, satellite, drone, licensing]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
applies_to: "RealityScan 2.0 (formerly RealityCapture), Agisoft Metashape 2.x, Blender 5.2 LTS, Unreal Engine 5.8."
unit_system: SI
sources:
  - {title: "RealityScan 2.0 release announcement", url: "https://www.realityscan.com/news/realityscan-20-new-release-brings-powerful-new-features-to-a-rebranded-realitycapture", publisher: "Epic Games / Capturing Reality", accessed: 2026-08-25}
  - {title: "Agisoft online store", url: "https://www.agisoft.com/buy/online-store/", publisher: "Agisoft LLC", accessed: 2026-08-25}
  - {title: "Polycam pricing", url: "https://poly.cam/pricing", publisher: "Polycam", accessed: 2026-08-25}
  - {title: "SkyFi pricing", url: "https://skyfi.com/pricing", publisher: "SkyFi", accessed: 2026-08-25}
  - {title: "PTGui", url: "https://ptgui.com/", publisher: "New House Internet Services BV", accessed: 2026-08-25}
  - {title: "Shuttle Radar Topography Mission", url: "https://en.wikipedia.org/wiki/Shuttle_Radar_Topography_Mission", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Poly Haven licence", url: "https://polyhaven.com/license", publisher: "Poly Haven", accessed: 2026-08-25}
related: [envasset.principles, envasset.terrain, envasset.rocks_surfaces, envasset.libraries, namibia.geology_soils]
---

# Reference, photogrammetry, scanning and HDRI capture

**Summary.** Getting real-world data into the pipeline is the highest-leverage thing you can do for realism, and for a site in Ohangwena it is also the only way to get materials nobody sells: local Kalahari sand, calcrete, mopane bark, a specific palisade pole, the actual light of the actual day. This file covers photographic reference discipline, cross-polarised albedo capture, photogrammetry end to end in RealityScan and Metashape, phone and LiDAR scanning, HDRI capture and luminance calibration, satellite and drone imagery as source data (including SkyFi), and the licensing traps that attach to scanned and library assets.

## Key facts

| Item | Value | Verified |
|---|---|---|
| RealityCapture → renamed **RealityScan 2.0** | Released **17 June 2025**; desktop app rebranded, mobile app is *RealityScan Mobile* | realityscan.com news, 2026-08-25 |
| RealityScan 2.0 licensing | Subscription **required only for individuals/businesses above US$1 million gross annual revenue** | realityscan.com news, 2026-08-25 |
| Legacy RealityCapture Enterprise (bought before 23 Apr 2024) | May continue using v1.4/1.5 at no extra cost | realityscan.com news, 2026-08-25 |
| Agisoft Metashape **Standard**, node-locked | **US$179** | agisoft.com store, 2026-08-25 |
| Agisoft Metashape **Professional**, node-locked | **US$3 499** | agisoft.com store, 2026-08-25 |
| Meshroom (AliceVision) | Free, MPL2 / open source | see Sources |
| Polycam Free / Basic / Business / Enterprise | **$0 / $150 per yr / $300 per yr per user / $1 200 per yr per seat (3 min.)** | poly.cam/pricing, 2026-08-25 |
| Polycam free-tier export | glTF only; Basic adds OBJ, FBX, DAE, STL, USDZ | poly.cam/pricing |
| SkyFi optical archive imagery | **from US$15** per image | skyfi.com/pricing, 2026-08-25 |
| SkyFi new tasking (optical) | **from US$200** | skyfi.com/pricing |
| SkyFi aerial imagery | **from US$35** | skyfi.com/pricing |
| SkyFi SAR | **from US$450** | skyfi.com/pricing |
| SkyFi multispectral / open data | **Free** | skyfi.com/pricing |
| SkyFi DSM (digital surface model) | Available as an analytics product | skyfi.com/pricing |
| PTGui current version | **13.9**; trial fully functional but watermarked; Standard and Pro editions (Pro adds HDR/EXR) | ptgui.com, 2026-08-25 |
| SRTM 1-arcsecond resolution | **~30 m at the equator**; tiles 3 601 × 3 601 16-bit big-endian cells | Wikipedia, 2026-08-25 |
| SRTM coverage | **56°S to 60°N** — includes all of Namibia | Wikipedia |

> ⚠️ **Every scan you make on someone's land, and every image you buy, comes with terms.** A photogrammetry scan of a neighbour's kraal is your copyright in the model but may still raise privacy and customary-land issues; SkyFi imagery is licensed, not sold; and a "free" library asset may forbid redistribution inside a client deliverable. §7 of this file is not optional reading.

---

## 1. Photographic reference discipline

### 1.1 What to shoot

Structure the site visit as a shot list, not as browsing. For a residential project in Okongo:

**A. Lighting conditions (tripod, fixed position, same framing)**
- 07:00, 09:00, 12:00, 15:00, 17:30, and 15 minutes after sunset, all on one clear day.
- The same set on a cloudy day if the visit spans one.
- Each set includes one frame with a **grey card / colour chart** held in the scene plane, and one frame **exposed for the highlights** (−2 to −3 EV) so you can measure shadow-to-sun ratio afterwards.

**B. Materials (perpendicular to surface, even light, no shadow of the photographer)**
- Sand: dry surface at 300 mm; dry surface at 3 m; damp sand; drifted sand against a wall; sand with footprints and tyre tracks; the sun-raking texture of ripples at 07:00 and 17:00.
- Ground cover: dry grass tussock, fallen leaf litter, bare compacted yard, calcrete gravel if present.
- Built: block wall unpainted and painted, plaster, corrugated roof sheet new and weathered, concrete slab edge, palisade pole butt and mid-span.
- Bark: mopane, marula, makalani trunk, at 300 mm with a scale ruler in frame.

**C. Context and scale**
- Every wide shot should contain a person or a known object.
- Shoot the *junctions*: wall-to-ground, roof-to-wall, post-in-sand, gate-to-pillar. Junctions are where CG fails.

**D. Sky**
- A 360° HDRI at each of your key times (§4).
- Separate long-lens shots of cloud structure for texture reference.

### 1.2 Camera settings for reference

| Purpose | Settings |
|---|---|
| Texture capture | Aperture **f/8–f/11**, ISO base (100), tripod, 2 s timer, RAW, manual white balance from grey card, focal length 50–85 mm (avoid wide-angle distortion) |
| Material albedo (cross-polarised) | Same, plus polarising filter on lens and polarising film on flash — see §1.4 |
| HDRI | Manual everything, bracket ≥ 7 frames at 2 EV steps, f/8, ISO 100, fisheye or 24 mm on a panoramic head |
| Photogrammetry | Aperture **f/8–f/11** (depth of field vs diffraction), fixed focus, fixed focal length, ISO as low as light allows, RAW, ~70–80% overlap |
| Context | Anything; but record EXIF |

**Lighting condition to prefer for texture capture:** **bright overcast**, or **open shade on a clear day**. Direct sun bakes shadows into the albedo and they are extremely hard to remove. If the trip only offers clear sun (likely in Ohangwena's dry season), shoot textures either shortly after sunrise/before sunset with a diffuser, or in the shadow of a vehicle or building.

### 1.3 Colour charts

Use an X-Rite/Calibrite ColorChecker Classic or Passport. Workflow:

1. Shoot one RAW frame with the chart filling ~20% of the frame, in the same light as the subject.
2. In Lightroom/RawTherapee/darktable, set white balance from the chart's neutral patch.
3. Generate a camera profile (Calibrite's own software, or `ArgyllCMS`) and apply it to the whole shoot.
4. Keep the chart image with the asset in `_ref/`. It is the evidence for any later colour argument.

Without a chart, your "sand colour" is your camera's guess about the colour of the light, which under a deep blue Namibian sky is badly biased.

### 1.4 Cross-polarisation for albedo capture

Specular reflection is polarised; diffuse reflection is not. Cross-polarising eliminates specular and gives you a near-pure albedo.

**Rig.** A linear polarising film taped over a flash or LED panel, and a circular (or linear) polariser on the lens. Rotate the lens polariser until the specular highlights vanish — typically 90° from the light's polarisation.

**Procedure.**
1. Shoot **parallel-polarised** (highlights visible) and **cross-polarised** (highlights gone) frames of the same subject from a tripod.
2. `Cross-polarised` = base colour / albedo.
3. `Parallel − Cross` (in linear space) ≈ the specular/roughness information.
4. Exposure will drop ~2 EV when cross-polarised; compensate with shutter, not ISO.

This is how commercial scan libraries produce clean albedo, and it is entirely achievable with a speedlight, two sheets of polarising film (a few tens of US dollars) and patience.

---

## 2. Photogrammetry end to end

### 2.1 Capture

**Overlap.** Aim for **70–80% overlap between adjacent frames**, with every surface point visible in **at least three, preferably five or more** images. Sparse coverage produces holes; excessive coverage costs alignment time only.

**Turntable (small objects — a calcrete nodule, a bone, a fence-post butt).**
- Object on a turntable with a **non-repeating, matte, mid-grey backdrop** — never a plain seamless white and never a repeating pattern.
- Camera fixed on a tripod; rotate the object in ~10–15° steps (24–36 frames per ring), at 3 rings (low, level, high).
- **Mask the background** — this is essential for turntable capture, because otherwise the software tries to align the *static* background against the *rotating* object and fails. RealityScan 2.0 added AI-assisted masking; Metashape has `Tools → Masks → Import Masks`.
- Include a **scale bar** or two markers a known distance apart.

**Field capture (a tree, a wall, a section of ground, a termite mound).**
- Walk concentric circles at 2–3 heights, camera pointed inward at ~30° down for the high ring, level for the middle, ~20° up for the low ring.
- For ground/material capture, shoot a grid: nadir (straight down) frames at ~1.5–2 m height, 70% overlap in both directions, plus oblique frames at the edges.
- **Diffuse light only.** Hard shadows are baked in and photogrammetry cannot remove them.
- Avoid wind for vegetation — a moving leaf fails alignment. Capture trunks and bark, not whole trees, in wind.
- Include **ground control**: two survey pegs a measured distance apart, or a printed scale bar. Without it your model has no real scale.

**Settings recap.** Manual exposure, fixed focus (tape the focus ring), fixed focal length (no zoom mid-capture), lowest usable ISO, f/8–f/11, RAW. Shoot at a shutter speed that freezes your own body sway: 1/(2 × focal length) or faster handheld.

### 2.2 Processing — RealityScan 2.0

RealityScan (formerly RealityCapture) is the fastest of the three and is free below the US$1 M revenue threshold, which makes it the default choice here.

Workflow:
1. **Add Imagery** → drag the folder in.
2. **Alignment → Align Images.** Check the component count in the 1Ds/2Ds panel — one component is the goal. Multiple components mean insufficient overlap; add connecting photos or place manual control points.
3. **Set scale/ground control**: `Alignment → Define Distance` between two control points, enter the measured distance in metres.
4. **Reconstruction → Normal Detail** (or High Detail for hero assets). Preview Detail for a fast check.
5. **Set Reconstruction Region** to crop to just the subject before meshing — this saves large amounts of time.
6. **Tools → Simplify** to a workable count (2–5 M triangles for a hero rock; more for a scanned tree trunk).
7. **Texture → Unwrap** then **Texture**. Set texture resolution per texel density target (§`08`).
8. Export: **OBJ or FBX** plus textures; or Alembic for large data.

RealityScan 2.0 additions relevant here: AI-assisted masking, alignment improvements, visual quality inspection, and **support for airborne laser scans** (i.e. you can fuse LiDAR with photogrammetry).

### 2.3 Processing — Agisoft Metashape

Metashape Standard (**US$179**) is enough for asset capture; Professional (**US$3 499**) adds georeferencing, multispectral, dense-cloud classification and Python scripting at a level relevant to survey work rather than art.

Workflow: `Add Photos → Align Photos (Accuracy: High, Generic + Reference preselection) → Build Point Cloud (Quality: High, Depth filtering: Mild for organics, Aggressive for hard surfaces) → Build Mesh (Source: Depth maps, Face count: High) → Build Texture (Mapping: Generic, Blending: Mosaic)`.

Metashape's advantages over RealityScan: better handling of poorly-lit or low-texture subjects, a mature Python API for batch processing, and a cheap perpetual entry price. Its disadvantage is speed — it is several times slower on the same dataset.

### 2.4 Processing — Meshroom

Free and open source (AliceVision). Node-graph based, CUDA-dependent for the dense reconstruction step. Good for learning and for occasional use; slower and less robust than either commercial option on difficult data. Use it if you need a zero-cost path or if you want to script the photogrammetry pipeline in a reproducible way.

### 2.5 Cleanup, retopology and de-lighting

A raw scan is not an asset. The steps, in order:

1. **Trim and hole-fill.** In Blender: delete loose geometry (`Select → Select All by Trait → Loose Geometry`), then fill holes with `Mesh → Clean Up → Fill Holes` or manually. For big holes, sculpt them closed.
2. **Decimate or retopologise.**
   - *Nanite target:* you may keep 1–5 M triangles and let Nanite handle it. Still decimate to remove noise.
   - *Non-Nanite target:* retopologise. Blender's `Remesh` modifier in **Voxel** mode with an adaptive size, then `Shrinkwrap` back onto the scan; or **QuadriFlow** (`Object → Quad Remesh`) for a clean quad cage. For rocks specifically, a decimated triangle mesh at 3–8 k triangles plus a baked normal is standard.
3. **UV unwrap** the low-poly. `Smart UV Project` with island margin 0.02 is acceptable for rocks; do it properly for anything with a readable silhouette.
4. **Bake** normal, AO, and (from the scan's vertex colours or texture) base colour: Blender `Render Properties → Bake`, `Bake Type: Normal`, `Selected to Active`, Extrusion 0.02 m, Max Ray Distance 0.05 m.
5. **De-light.** The scan's albedo contains baked ambient occlusion and directional shading. Remove it:
   - Divide the scan albedo by a rendered AO pass (in Blender's compositor or in Photoshop/Krita in linear space).
   - Or use Unreal's **De-Lighting Tool** plugin, which uses a baked AO/normal to estimate and remove lighting. `needs-verification` on whether the standalone Unreal De-Lighting Tool is still shipped in 5.8 — it was historically distributed via the Epic Launcher.
   - Or capture cross-polarised in the first place (§1.4) and avoid the problem.
6. **Flatten and neutralise ground scans.** For a tileable ground material, project the scan to a plane, remove low-frequency height (high-pass the displacement), and make it tile (§`05`).

---

## 3. LiDAR and phone-based scanning

**iPhone / iPad Pro LiDAR.** The sensor is a low-resolution time-of-flight scanner: useful for *scale-accurate rough geometry* (a room, a wall, a vehicle) and useless for surface detail. Range roughly 5 m. Its real value here is producing a **dimensionally trustworthy proxy** of an existing building or site feature that you then rebuild properly.

**Polycam** (poly.cam) is the practical front end. Free tier: limited captures, glTF export only, public sharing only. **Basic at US$150/year** unlocks unlimited photogrammetry and space captures, 300 images per capture, private sharing, and mesh export to OBJ/FBX/DAE/STL/USDZ plus point clouds (PLY, LAS, PTS, XYZ, DXF). **Business US$300/year per user** adds floor plans and measurement tools — relevant if you want an as-built of an existing structure.

**RealityScan Mobile** (the rebranded RealityCapture mobile app) is free and uploads to Epic's cloud for processing; output can be brought into Unreal.

**Gaussian splats.** Polycam supports splat capture at Basic tier and above. Splats are excellent for *presentation of a captured place* and currently poor as a source for an editable asset — treat them as reference, not as geometry, unless you convert to mesh.

**Terrestrial laser scanners** (Leica BLK360, Faro Focus) give survey-grade point clouds. Out of budget for most residential work, but if the project already has a survey, ask for the `.e57` — Unreal imports point clouds via the **LiDAR Point Cloud** plugin, and CloudCompare (free) will convert and decimate.

---

## 4. HDRI capture

An HDRI captured on site at the actual time of day is the single most convincing lighting source you can have, and it also gives you a ground truth for §`09`'s reference matching.

### 4.1 Rig

- **Camera**: any interchangeable-lens camera with manual exposure and auto-bracketing.
- **Lens**: a fisheye (8 mm on APS-C, 15 mm on full frame) needs only 3–6 shots per ring; a 24 mm rectilinear needs ~12–18 plus zenith and nadir.
- **Panoramic head**: essential. It rotates the camera about the **entrance pupil (no-parallax point)** of the lens, not the tripod screw. Nodal Ninja and Manfrotto 303 are common; a printed/3D-printed head works if calibrated. Without one, near-field objects ghost at the stitch seams.
- **Tripod**, spirit level, remote release.

### 4.2 Shooting

1. Manual mode. Fixed aperture **f/8**, fixed ISO **100**, fixed white balance (daylight/5500 K), fixed focus at hyperfocal.
2. Auto-bracket **at least 7 frames at 2 EV steps** — for a scene containing the sun you need far more range than that; **9–11 frames spanning ~20 EV** is realistic. The sun is roughly 10⁵ times brighter than the sky.
3. Even at 1/8000 s, f/22, ISO 100 many cameras cannot capture the solar disc unclipped. Two accepted solutions:
   - Shoot an additional set through a **strong ND filter** (ND1000 / 10-stop) for the sun bracket only, and merge with a known offset.
   - Accept the clipped sun and **reconstruct it analytically**: measure the sky luminance, then replace the clipped disc with a synthetic disc of the correct total flux (sun angular diameter **0.53°**). This is standard practice.
4. Shoot each ring, then zenith, then nadir (with the tripod moved for the nadir shot).
5. Record the **date, time, GPS position and camera height**. Without them the HDRI cannot be aligned to a solar model.

### 4.3 Stitching and calibration

- **PTGui** (current version **13.9**; Standard and Pro; Pro adds HDR merging and OpenEXR output; the trial is fully functional but watermarks output). Load the brackets, let it detect, set the projection to **Equirectangular**, output **32-bit OpenEXR**.
- Output resolution: 8 192 × 4 096 minimum for lighting; 16 384 × 8 192 if the HDRI will appear as a visible background.
- **Calibrate to real luminance.** The stitch gives you relative values. To make them absolute:
  1. Measure a known surface's luminance on site with a spot meter, or measure horizontal illuminance with a lux meter.
  2. Compute the HDRI's implied horizontal illuminance by integrating the upper hemisphere (a small Python/OpenImageIO script, or Blender: light a white lambertian plane with the HDRI and read the result).
  3. Multiply the EXR by the ratio. Now `1.0` in the file means a known cd/m².
- Store the multiplier in the filename: `HDRI_Okongo_1200_2026-08-14_x1.34.exr`.

### 4.4 Using it

- **Blender**: World → Environment Texture, set `Strength` to 1.0 if calibrated. Set the mapping rotation so the sun matches your solar model.
- **Unreal**: import as HDR, create a `Cubemap`, assign to a **Sky Light** with Source Type `SLS Specified Cubemap`. For a physically-lit scene, prefer **Sky Atmosphere + Directional Light** for the sun and use the captured HDRI as a *look reference* and for reflections; a captured HDRI's sun is usually too low-resolution to cast a crisp shadow.
- **Never use an HDRI's sun for shadows in an exterior.** Use a real Directional Light aligned to the HDRI's sun position, and mask the sun out of the HDRI (or accept double-counting and reduce the sky intensity).

---

## 5. Texture scanning

For tileable ground and wall materials without full photogrammetry:

1. **Flat-field capture**: nadir shots at 1.5–2 m, overcast light, 70% overlap, 3 × 3 grid minimum.
2. Photogrammetry the grid → export a **height map** and an **albedo** from the mesh, projected orthographically.
3. Or use **Adobe Substance 3D Sampler** (formerly Alchemist), which converts a single photo or a small set into a full PBR set using its "Image to Material" filters. It is the fastest route from a phone photo to a usable material, and its **multi-angle-to-material** filter (using several photos with different flash directions) gives genuinely good normals.
4. Or use **Materialize** (free, Bounding Box Software) — a simple, capable height/normal/AO/metallic generator from a single diffuse image.
5. Make it tile: offset by half (Blender's `Image Editor` has no offset; use GIMP/Krita `Offset` at 50%/50%), heal the seams, and verify by tiling 4 × 4 and looking for structure (§`01 §7`).

---

## 6. Satellite and drone imagery as source

### 6.1 What each is good for

| Source | Ground sample distance | Good for | Not good for |
|---|---|---|---|
| **SRTM 1-arcsec** | ~30 m | Regional terrain shape, free, global | Anything at plot scale |
| **Copernicus DEM GLO-30** | ~30 m | Better-quality global DEM than SRTM; a *surface* model (includes canopy/buildings) | Bare-earth precision |
| **SkyFi optical archive** | 30–50 cm at the high end | Site context, vegetation pattern, tracks and buildings, texture for a far-field terrain material | Elevation |
| **SkyFi tasking** | 30–50 cm | A current image of the site on a chosen date | Anything urgent/cheap |
| **SkyFi aerial** | Sub-30 cm | Highest-detail overhead texture | Availability outside covered areas |
| **SkyFi DSM analytics** | Varies | A surface model of the site derived from stereo imagery | Sub-metre building detail |
| **Consumer drone (DJI Mini/Air class)** | 1–3 cm at 40 m AGL | Full site photogrammetry: terrain, vegetation positions, existing buildings | Under-canopy, and it needs permission |
| **Google/Bing aerial** | Varies | Free orientation and rough massing | Any deliverable — the licences forbid it |

### 6.2 Practical use for this project

1. **Buy one SkyFi archive optical image** of the site (from US$15) for the plot and its surroundings. Use it to: place existing trees correctly; derive the pattern of tracks, clearings and homestead layout; and supply a far-field colour reference for the landscape material beyond the modelled area.
2. **Use it as an Unreal Landscape "macro variation" texture.** Project the satellite image onto the landscape material as a very-large-scale colour multiply (0.85–1.15 range) so that from a distance the ground reproduces the real pattern of bare sand, grass and shrub. This is one of the strongest realism techniques available for a flat landscape and costs almost nothing.
3. **Fly a drone grid** for the plot itself if permitted: double-grid at 45° camera pitch, 75% front and side overlap, 40–60 m AGL. Process in RealityScan. This produces both a centimetre DEM and a photo-textured mesh that you can use directly as a background and as ground truth for the modelled version.
4. **[NA]** Drone operation in Namibia is regulated by the Namibia Civil Aviation Authority; commercial operation requires authorisation. `needs-verification` on the current NCAA RPAS requirements before flying — check domain `11_logistics_remote_areas` and the NCAA directly.

### 6.3 DEM to terrain

Covered in detail in `03`. In short: download the tile, reproject and crop in QGIS or GDAL, export a 16-bit greyscale PNG or `.r16`, and import to Unreal Landscape with the Z-scale maths in `03 §2`.

---

## 7. Licensing — scans, libraries and imagery

This is where projects get into trouble quietly.

### 7.1 Your own scans

- A photograph you take is your copyright. A 3D model derived from your photographs is your copyright.
- **But**: photographing private property, and especially people's homes on communal land, is a social and legal matter as well as a technical one. **[NA]** In Ohangwena, homesteads sit on land allocated by Traditional Authorities; ask permission from the household, not only from an official. This is both correct practice and the difference between a productive site visit and a hostile one.
- Do not scan a neighbour's building and put it in a client render without consent.
- Trademark and design rights can attach to distinctive manufactured objects (a specific vehicle, a branded water tank). Renders for a private client are low risk; marketing material is not.

### 7.2 Library assets

| Source | Licence | Redistribution inside a deliverable |
|---|---|---|
| **Poly Haven** | **CC0** — public domain, commercial use, redistribution, no attribution required (appreciated) | Yes, unconditionally |
| **ambientCG** | **CC0** | Yes, unconditionally |
| **Quixel Megascans on Fab** | **Fab Standard License** (paid per asset since the Fab transition; a rotating free selection exists) | Rendered images: yes. Redistributing the asset files themselves: normally **no** |
| **Fab marketplace generally** | Per-listing; Standard vs Personal licence tiers | Read each listing |
| **Sketchfab** | Per-model; CC-BY, CC0, or "Sketchfab Standard" | CC-BY requires attribution *in the deliverable* |
| **BlenderKit / Blendkit** | Per-asset, mostly royalty-free commercial | Check per asset |
| **Textures.com** | Proprietary; credit-based; explicit limits on redistribution and on resale of derived textures | Restrictive — read before use |

**The rule that catches people:** almost every licence permits you to *render* the asset and sell the render, and almost none permits you to *hand the asset file to your client*. If the client wants the Unreal project delivered, you are redistributing every asset in it. Plan for that: either use CC0 sources for anything that ships, or buy the licence tier that permits it, or strip and substitute before handover.

### 7.3 Satellite imagery

SkyFi imagery is **licensed**, not sold. Typical commercial satellite imagery licences permit internal use and derived products but restrict redistribution of the imagery itself and may restrict the number of users. A *derived* product — a terrain material that no longer contains recognisable imagery — is usually fine; a render with the satellite photo visible as a ground plane may not be. `needs-verification` against the specific SkyFi order terms for the imagery this project buys. SkyFi's **open data** offering is free and has looser terms; check which programme a given dataset came from.

### 7.4 Government and scientific datasets

- **SRTM** (NASA/USGS): public domain, no restrictions.
- **Copernicus DEM**: free and open under the Copernicus licence, attribution required.
- **Landsat / Sentinel**: free and open, attribution required.
- These are the safest sources for anything that ships.

---

## 8. A reference-and-capture checklist

- [ ] `_ref/` folder created, mirroring asset structure
- [ ] Colour chart shot in every lighting condition
- [ ] Time-series set from a fixed tripod position
- [ ] One highlight-exposed frame per condition for value measurement
- [ ] Material close-ups at two distances, with a scale ruler
- [ ] All junctions photographed
- [ ] HDRI captured at each key time, with GPS, time and camera height recorded
- [ ] HDRI calibrated to a measured lux value and the multiplier in the filename
- [ ] Photogrammetry sets have ≥ 70% overlap and a measured scale bar
- [ ] Scans de-lighted (cross-polarised at capture, or AO-divided afterwards)
- [ ] Satellite/aerial image acquired and its licence terms filed with it
- [ ] Every downloaded asset has its licence recorded in the project's asset register (`08`)
- [ ] Permission obtained and recorded for anything scanned on other people's land

## Sources

- [RealityScan 2.0 release announcement](https://www.realityscan.com/news/realityscan-20-new-release-brings-powerful-new-features-to-a-rebranded-realitycapture) — Epic Games / Capturing Reality
- [Agisoft online store](https://www.agisoft.com/buy/online-store/) — Agisoft LLC
- [Polycam pricing](https://poly.cam/pricing) — Polycam
- [SkyFi pricing](https://skyfi.com/pricing) — SkyFi
- [PTGui](https://ptgui.com/) — New House Internet Services BV
- [Shuttle Radar Topography Mission](https://en.wikipedia.org/wiki/Shuttle_Radar_Topography_Mission) — Wikipedia
- [Poly Haven licence](https://polyhaven.com/license) — Poly Haven
- [ambientCG](https://ambientcg.com/) — ambientCG
- [Quixel pricing / Fab transition](https://quixel.com/pricing) — Quixel

## Open questions

- **PTGui pricing** — the order page could not be fetched (JavaScript-only). `needs-verification`.
- **Unreal De-Lighting Tool** availability in UE 5.8. `needs-verification`.
- **SkyFi licence terms** for derived 3D products and for redistribution to a client. `needs-verification` against the actual order terms.
- **NCAA drone regulations** for commercial RPAS operation in Namibia. `needs-verification`.
- Whether Metashape Standard's feature set is sufficient for scale-bar-based georeferencing, or whether Professional is required for that specifically. `needs-verification`.
