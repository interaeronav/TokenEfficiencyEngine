---
id: cartography.namibia
title: Practical mapping projects and the Namibian case
domain: 23_cartography_and_mapping
tags: [namibia, okongo, ohangwena, site-plan, construction, gnss, drone-survey, orthomosaic, contours, cut-fill, georeferencing, cuvelai, oshana, communal-land, cadastre, skyfi, building-submission]
jurisdiction: namibia
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "EPSG Geodetic Parameter Dataset (API v1)", url: "https://apps.epsg.org/api/v1/", publisher: "IOGP Geomatics Committee", accessed: 2026-08-25}
  - {title: "Namibian annotated statutes index", url: "https://www.lac.org.na/laws/annoSTAT/", publisher: "Legal Assistance Centre, Namibia", accessed: 2026-08-25}
  - {title: "Professional Land Surveyors', Technical Surveyors' and Survey Technicians' Act 32 of 1993", url: "https://www.lac.org.na/laws/annoSTAT/Professional%20Land%20Surveyors'%20Technical%20Surveyors'%20and%20Survey%20Technicians'%20Act%2032%20of%201993.pdf", publisher: "Legal Assistance Centre", accessed: 2026-08-25}
  - {title: "OpenDroneMap documentation", url: "https://docs.opendronemap.org/", publisher: "OpenDroneMap", accessed: 2026-08-25}
  - {title: "SkyFi", url: "https://skyfi.com/", publisher: "SkyFi", accessed: 2026-08-25}
  - {title: "Copernicus DEM collection description", url: "https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM", publisher: "Copernicus Data Space Ecosystem", accessed: 2026-08-25}
related: [cartography.geodesy, cartography.terrain, cartography.remote_sensing, cartography.data, namibia.overview, namibia.geography, namibia.climate]
unit_system: SI
---

# Practical mapping projects and the Namibian case

**Summary.** This is the applied file: how to map a construction site and its surroundings in Namibia end to end — GNSS control, drone flight, orthomosaic, contours, cut and fill — and how to turn that into a scaled site plan and a printable location map for a building submission. It also covers the Namibian coordinate systems *in practice*, sourcing Namibian base data, the Cuvelai oshana problem that breaks naive hydrological analysis, communal versus freehold land, georeferencing a scanned plan, and working with purchased SkyFi imagery. The worked example is **Okongo, Ohangwena Region (17°34′S, 17°13′E, ~1 150 m)**.

## Key facts

| Item | Value |
|---|---|
| Okongo coordinates | **17.567°S, 17.217°E**, ~**1 151 m** |
| Working analysis CRS at Okongo | **EPSG:32733** — WGS 84 / UTM zone 33S (17.22°E is inside the 12–18°E zone) |
| Cadastral CRS at Okongo | **EPSG:29377** — Schwarzeck / Lo22/17. Axes **westing, southing**; units **German Legal Metres** |
| Vertical reference for deliverables | Orthometric heights on **EGM2008** (EPSG:3855) unless a local benchmark is specified |
| Compound CRS for a levelled deliverable | `EPSG:32733+3855` |
| Free regional DEM | **Copernicus DEM GLO-30** (~31 m, DSM, EGM2008, < 4 m LE90) |
| Site-scale DEM | **Drone photogrammetry** — 30 m is useless on a plot |
| Regulator for cadastral survey | **[NA]** Namibian Council for Professional Land Surveyors, Technical Surveyors and Survey Technicians (Act 32 of 1993); survey practice under the **Land Survey Act 33 of 1993** |
| Regional relief | **Metres over tens of kilometres.** The Cuvelai sandveld is exceptionally flat |

> ⚠️ **[NA]** Nothing in this file makes an unregistered person a land surveyor. A plan produced from a drone survey is a **site plan / topographic survey for design purposes**. A **cadastral diagram** fixing beacons and boundaries, for lodgement with the Surveyor-General and registration in the Deeds Office, must be produced and signed by a **registered professional land surveyor** (Act 32 of 1993, s.14). Establish which one the submission actually requires before starting.

> ⚠️ **The single most likely error on a Namibian site plan** is a datum mismatch. GNSS gives WGS 84 / ITRF; the existing diagram is on **Schwarzeck**. The plan offset is of the order of **300–400 m**. A plan that mixes the two looks correct and is useless. Establish the datum of every input in writing before combining anything.

## 1. The Namibian coordinate systems in practice

### Which CRS for which purpose

| Purpose | CRS | Why |
|---|---|---|
| Field GNSS capture | **EPSG:4326** / 4979 (WGS 84) | What the receiver produces. Record the epoch and the correction service |
| Site analysis, areas, volumes | **EPSG:32733** (UTM 33S) | Metres, north-orientated, universally supported, negligible distortion over a site |
| Cadastral reference, comparison to a Surveyor-General diagram | **EPSG:29377** (Schwarzeck / Lo22/17) | The statutory system for the 16–18°E belt |
| Web display | **EPSG:3857** | Tiles only. Never measure in it |
| National context map | UTM 33S/34S, or an Albers equal-area for area work | — |

### The Lo belt for a site

The belt is chosen by longitude, in 2° bands centred on odd meridians:

| Longitude | Belt | EPSG |
|---|---|---|
| west of 12°E | Lo22/11 | 29371 |
| 12–14°E | Lo22/13 | 29373 |
| 14–16°E | Lo22/15 | 29375 |
| **16–18°E (Okongo, Eenhana, Ondangwa, Windhoek)** | **Lo22/17** | **29377** |
| 18–20°E | Lo22/19 | 29379 |
| 20–22°E | Lo22/21 | 29381 |
| 22–24°E | Lo22/23 | 29383 |
| east of 24°E | Lo22/25 | 29385 |

### Three things that break software

1. **Axes are westing (Y) and southing (X).** East of the central meridian, Y is **negative**. Software that assumes easting/northing will mirror the site.
2. **Units are German Legal Metres** (1 GLM = 1.0000135965 m). A 13.6 ppm scale error — 13.6 mm per kilometre.
3. **Latitude of origin is −22°**, not the equator. Southings are therefore much smaller than South African ones. Do not "sanity check" a Namibian Lo coordinate against South African expectations.

```bash
# Diagnose before you transform. This is always the first command.
projinfo EPSG:29377
projinfo -s EPSG:4326 -t EPSG:29377 --spatial-test intersects --summary

# WGS 84 lon/lat -> Schwarzeck / Lo22/17
echo "17.217 -17.567" | cs2cs -f "%.3f" EPSG:4326 EPSG:29377

# WGS 84 lon/lat -> UTM 33S (the working CRS)
echo "17.217 -17.567" | cs2cs -f "%.3f" EPSG:4326 EPSG:32733
```

> ⚠️ For any coordinate that will be compared to an official diagram, do **not** rely on the EPSG global Schwarzeck→WGS 84 translation (`+616, +97, −251 m`, stated accuracy **35 m**). Obtain the official transformation from the Surveyor-General, or — far better — **have a registered surveyor tie your site into the national control network**. `needs-verification`: whether Namibia publishes a grid-based (NTv2-style) transformation.

## 2. Mapping a construction site end to end

### Step 1 — Establish control

The whole survey's accuracy is decided here.

1. **Decide the deliverable CRS and vertical datum first**, in writing, with the architect/engineer. UTM 33S horizontal + EGM2008 orthometric is a sensible default for design work. If the project ties to an existing benchmark or a Surveyor-General beacon, that governs instead.
2. **Establish 2 site control points** with good sky view, on stable ground, that will survive the works. Mark them properly (a concrete-set steel pin, not a wooden peg in Kalahari sand).
3. **Observe them** with the best method available:
   - **RTK from a local base** on a known point — centimetre, immediate.
   - **PPK / long static occupation** (2–4 h) post-processed against a CORS or a PPP service — centimetre without a base. This is the practical method in northern Namibia, where CORS coverage is sparse.
   - **Galileo HAS / commercial PPP-RTK** — decimetre or better, free (HAS) or subscription, no base.
   - A handheld GNSS is **not** control. It is 3–10 m.
4. **Record both heights** — ellipsoidal and orthometric — and **name the geoid model** used (EGM2008 unless a national model is specified).
5. **Lay out 5+ GCPs** across the site for the drone flight (four near corners, one central; more for elongated sites), plus **2–3 independent check points** that will be excluded from the photogrammetric adjustment. See `07`, §11.

### Step 2 — Fly the site

```
Target: 2 cm GSD for a site plan with 0.25 m contours
Camera: 13.2 mm sensor width, 8.8 mm focal length, 5472 px wide

height = (GSD × focal × image_width) / sensor_width
       = (0.02 × 8.8 × 5472) / 13.2
       = 72.9 m  ->  fly at 73 m AGL
```

- **Overlap 80% front / 70% side.** Increase over uniform sandveld — feature matching struggles on bare Kalahari sand, and an under-lapped block over it will have holes.
- **Cross-hatch (double grid)** for anything with vertical structure; add a **15–20° oblique** pass around buildings.
- Fly **near solar noon**, in low wind, under stable light. Avoid the transitional periods where cloud shadows move across the block.
- Include the GCP targets in multiple images from different angles — each GCP wants **3+ observations, ideally 5+**.
- Extend the flight block **beyond the site boundary** by at least 50 m so the edges are properly reconstructed. Photogrammetric quality degrades at the block edge.

> ⚠️ **[NA]** Confirm the current Namibia Civil Aviation Authority requirements for UAV registration, operator authorisation, altitude limits and insurance before any commercial flight. `needs-verification`.

### Step 3 — Process to orthomosaic, DSM and DTM

```bash
# OpenDroneMap with GCPs (gcp_list.txt in the project root, CRS on line 1)
docker run -ti --rm -v /data/okongo_site:/datasets/code opendronemap/odm \
  --project-path /datasets \
  --dsm --dtm \
  --orthophoto-resolution 2.0 \
  --dem-resolution 5.0 \
  --dem-gapfill-steps 4 \
  --smrf-scalar 1.2 --smrf-slope 0.15 --smrf-threshold 0.4 --smrf-window 16 \
  --pc-quality high --feature-quality high \
  --min-num-features 12000 \
  --cog
```

The `--smrf-*` parameters control ground filtering for the DTM. On flat sandveld with sparse shrubs, a **low slope value (0.1–0.2)** and a **modest window** work well; the defaults are tuned for more varied terrain.

```bash
# Reproject and package the outputs into the delivery CRS
gdalwarp -t_srs EPSG:32733 -r cubic -of COG \
  -co COMPRESS=JPEG -co QUALITY=92 -co BLOCKSIZE=512 \
  odm_orthophoto/odm_orthophoto.tif ortho_2cm_utm33s.tif

# Convert the DTM from ellipsoidal to EGM2008 orthometric height
export PROJ_NETWORK=ON
gdalwarp -s_srs EPSG:4979 -t_srs "EPSG:32733+3855" \
  odm_dem/dtm.tif dtm_ortho_utm33s.tif

# Verify against the independent check points BEFORE using it
gdallocationinfo -valonly -geoloc dtm_ortho_utm33s.tif 664231.12 8055412.34
```

### Step 4 — Contours

On terrain as flat as the Cuvelai sandveld, contour interval choice is the whole game.

| Site relief | Interval | Note |
|---|---|---|
| < 1 m across the site | **0.1 m** | Below the noise floor of most photogrammetry — validate first |
| 1–3 m | **0.25 m** | The normal choice for an Okongo plot |
| 3–10 m | **0.5 m** | |
| > 10 m | 1.0 m with 5 m index | |

```bash
# Smooth the DTM lightly first — raw photogrammetric DTMs contour into spaghetti
gdal_translate -of GTiff dtm_ortho_utm33s.tif dtm_tmp.tif
saga_cmd grid_filter 0 -INPUT dtm_tmp.sgrd -RESULT dtm_smooth.sgrd -MODE 1 -RADIUS 3
# or, with GDAL only:
gdalwarp -r average -tr 0.5 0.5 dtm_ortho_utm33s.tif dtm_0p5m.tif

gdal_contour -a elev -i 0.25 dtm_0p5m.tif contours_025.gpkg -f GPKG -nln contours
gdal_contour -a elev -i 1.00 dtm_0p5m.tif contours_index.gpkg -f GPKG -nln index
```

Then in QGIS: label the index contours only, hide contour labels where they cross buildings, and simplify lightly (Visvalingam) for legibility without changing the values.

### Step 5 — Cut and fill volumes

Volume is the **difference between two surfaces** integrated over an area. Both surfaces must be on the **same vertical datum** and the **same grid**.

```bash
# 1. Build the design surface (from the engineer's levels, or a constant platform level)
#    Example: a flat platform at 1150.40 m over the building footprint
gdal_rasterize -burn 1150.40 -tr 0.25 0.25 \
  -te <xmin> <ymin> <xmax> <ymax> -a_nodata -9999 \
  -ot Float32 platform.gpkg design_surface.tif

# 2. Align the existing DTM to exactly the same grid
gdalwarp -tr 0.25 0.25 -te <xmin> <ymin> <xmax> <ymax> -r bilinear \
  dtm_ortho_utm33s.tif existing_aligned.tif

# 3. Difference: positive = fill required, negative = cut required
gdal_calc.py -A design_surface.tif -B existing_aligned.tif \
  --outfile=cutfill.tif --calc="A-B" --NoDataValue=-9999

# 4. Integrate
python3 - <<'PY'
import rasterio, numpy as np
with rasterio.open("cutfill.tif") as s:
    d = s.read(1, masked=True)
    cell = abs(s.transform.a * s.transform.e)      # m² per cell
fill = float(np.sum(d[d > 0]) * cell)
cut  = float(np.sum(-d[d < 0]) * cell)
print(f"Cell area      : {cell:.4f} m2")
print(f"Fill required  : {fill:10.2f} m3")
print(f"Cut required   : {cut:10.2f} m3")
print(f"Net (fill-cut) : {fill-cut:+10.2f} m3")
PY
```

**Report volumes honestly.** State: the source of the existing surface and its **measured** vertical accuracy, the grid resolution, the design surface's origin, and a resulting uncertainty. A ±0.05 m surface accuracy over a 400 m² platform is **±20 m³** of volume uncertainty before any bulking factor. Add the material bulking/compaction factor separately and label it as an assumption — Kalahari sand behaves very differently from the graded fill an engineer's table assumes.

## 3. Producing a site plan to scale

A site plan is a **drawing**, not a screenshot of a GIS. The requirements:

| Element | Requirement |
|---|---|
| **Scale** | A round scale — 1:100, 1:200, **1:250**, 1:500, 1:1000 — stated numerically **and** as a graphic bar |
| **Sheet** | A standard size (A3, A2, A1) with a defined printable area. Set the layout to the sheet, not the screen |
| **Grid** | The **projected coordinate grid** (UTM 33S or Lo22/17) with labelled ticks. This is what makes the sheet usable in the field |
| **North** | Grid north arrow, with a note of the grid convergence if it is significant, or true north stated explicitly |
| **Levels** | Spot heights at corners, at the building platform, at boundary points and at drainage inverts. State the vertical datum |
| **Boundary** | Plot boundary with bearings and distances, and beacon references if they exist |
| **Setbacks** | Building lines / setbacks dimensioned from the boundary |
| **Existing features** | Buildings, trees over a stated girth, boreholes, septic, power lines, access |
| **Proposed works** | Footprint, hard surfaces, drainage direction, ramps and levels |
| **Title block** | Project, client, plot/erf, locality, scale, sheet size, **CRS and datum**, date, surveyor/producer, revision |
| **Source note** | Every data source with its date, accuracy and licence attribution |

**Scale arithmetic** — the thing to get right:

```
paper_length_mm = ground_length_m × 1000 / scale_denominator

A 40 m plot at 1:250   ->  40 × 1000 / 250   = 160 mm      fits A3 easily
A 40 m plot at 1:100   ->  40 × 1000 / 100   = 400 mm      needs A2/A1
A 250 m site at 1:1000 ->  250 × 1000 / 1000 = 250 mm      fits A3
```

**In QGIS Print Layout:**
1. Set the page to the sheet size and orientation.
2. Add a Map item, then set its **Scale** field to exactly `250` (not "fit to extent"). Lock it.
3. Set the map's CRS explicitly in Layout properties.
4. Add a **Grid** to the map item: interval 10 m (or 25/50 m depending on scale), CRS = the map CRS, frame style "Zebra", and annotation on all sides.
5. Add a graphic **scale bar** in metres with round divisions and a zero.
6. Add the legend, title block (an HTML or fixed table item), and a source/CRS note.
7. Export to **PDF at 300 dpi minimum**, with "Always export as vectors" enabled so text and lines stay crisp and the PDF remains measurable.

```bash
# Or render it headlessly, repeatably
qgis_process run native:printlayouttopdf -- \
  PROJECT_PATH=/data/okongo_site.qgz \
  LAYOUT="Site Plan 1-250" \
  DPI=300 FORCE_VECTOR=true \
  OUTPUT=/out/site_plan_A2_1-250.pdf
```

## 4. Producing a printable location map for a building submission

A submission usually wants **two** maps, and confusing them is a common rejection cause.

**(a) Locality plan** — where the site is, at ~1:5 000 to 1:25 000.
- Base: satellite image or a light topographic base.
- Show: the site outlined and hatched, the settlement, named access roads, a scale bar and north arrow, and a small inset showing the region within Namibia.
- Include: coordinates of the site centroid in **both** WGS 84 lat/lon (for a phone) and the projected CRS.

**(b) Site plan** — the works, at 1:100 to 1:500. As §3.

**A workable production recipe:**

```bash
# 1. Regional context DEM + hillshade for the inset
gdalwarp -te 16.9 -17.75 17.5 -17.35 -t_srs EPSG:32733 -tr 30 30 -r bilinear \
  /vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_S18_00_E017_00_DEM/Copernicus_DSM_COG_10_S18_00_E017_00_DEM.tif \
  okongo_dem.tif
gdaldem hillshade -multidirectional -compute_edges okongo_dem.tif okongo_hs.tif

# 2. Roads and places from OSM
osmium extract -b 16.9,-17.75,17.5,-17.35 namibia-latest.osm.pbf -o okongo.osm.pbf
ogr2ogr -f GPKG okongo.gpkg okongo.osm.pbf lines points multipolygons

# 3. Site boundary from the survey, in the same CRS
ogr2ogr -f GPKG -update -nln site_boundary okongo.gpkg site_boundary.gpkg
```

Then build both sheets as **QGIS Atlas pages** or as two layouts in one project, so a change to the boundary propagates to both.

**Attribution that must appear on the sheet:**
- If OSM is used: **© OpenStreetMap contributors** and a note that the data is under ODbL.
- If Copernicus DEM is used: **© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA**.
- If commercial imagery is used: the operator's required credit line from the EULA.

> **[NA]** Confirm the specific submission requirements with the **Local Authority or Regional Council** and, on communal land, with the **Traditional Authority and the Communal Land Board** before producing the sheets. Required scales, sheet sizes, and whether a registered surveyor's diagram is needed vary. `needs-verification`.

## 5. Georeferencing a scanned plan

A common job: an existing site diagram, layout plan or old survey sheet exists only on paper or as a PDF.

1. **Scan at 300–600 dpi**, flat, without keystone. A phone photo of a plan is a last resort and will need a higher-order transform to compensate for perspective.
2. **Identify control** on the scan: grid intersections (best — they are exact), surveyed beacons, or unambiguous permanent features (building corners, road intersections) whose real coordinates you can obtain.
3. **Choose the transformation by point count**: 2 points → Helmert (translate, rotate, uniform scale); 3+ → **affine / 1st-order polynomial, the default choice**; 6+ → 2nd-order polynomial; 10+ → thin plate spline (rubber-sheets exactly through every point). **Higher order is not better** — a 2nd-order fit with a low RMS is usually overfitting scanner distortion and will bend the plan outside the control area. Prefer affine unless you have a specific reason.
4. **Georeference in QGIS** (Raster → Georeferencer): place points, set the target CRS, choose the transform, resample **cubic** for imagery or **nearest** for line drawings, and check the **residual per point**. A residual much larger than the others means a mis-identified point — fix it rather than accepting the RMS.
5. **Target RMS**: better than half the smallest feature you care about. For a 1:500 plan where 0.5 m matters, aim well under 0.25 m.
6. **Record what you did** — control points, transform, RMS, target CRS — in the output's metadata or a sidecar file. A georeferenced scan with no provenance is not evidence.

```bash
# Command-line equivalent, if you have the control points
gdal_translate -of GTiff \
  -gcp 412 3180  664120.5 8055100.2 \
  -gcp 3980 3175 664520.8 8055102.9 \
  -gcp 3975 620  664519.1 8055455.4 \
  -gcp 418 615   664118.9 8055452.7 \
  scan.tif scan_gcp.tif

gdalwarp -r cubic -order 1 -t_srs EPSG:32733 \
  -co COMPRESS=DEFLATE -co TILED=YES \
  scan_gcp.tif scan_georef.tif
```

`-order 1` is the affine transform; `-tps` switches to thin plate spline.

## 6. Working with purchased SkyFi imagery

SkyFi aggregates 40+ providers (Vantor, Planet, ICEYE US, Umbra, Satellogic and others) with archive from about **$15** and tasking from about **$200**, including 30–50 cm optical and SAR.

**On receipt:**

```bash
# 1. What did you actually get?
gdalinfo -stats -mm image.tif | head -60
#    Check: CRS, pixel size, band count, bit depth, nodata, and whether it is
#    already orthorectified (a "Level 2/ORTHO" product) or not.

# 2. Reproject to the working CRS if needed, preserving radiometry
gdalwarp -t_srs EPSG:32733 -r cubic -of COG \
  -co COMPRESS=DEFLATE -co PREDICTOR=2 image.tif image_utm33s.tif

# 3. Pan-sharpen if you got separate pan + multispectral
gdal_pansharpen.py pan.tif ms.tif pansharp.tif -r cubic -of COG

# 4. Contrast stretch for display ONLY — keep the original for analysis
gdal_translate -ot Byte -scale_1 <min> <max> 0 255 \
               -scale_2 <min> <max> 0 255 \
               -scale_3 <min> <max> 0 255 \
  image_utm33s.tif image_display.tif
```

**Check:** the **acquisition date** (a two-year-old scene will not show recent works); the **off-nadir angle** (high off-nadir means building lean and displaced rooftops, which matters if you measure from the image); whether it is **orthorectified** and against which DEM (orthorectification against a 30 m DEM leaves residual terrain displacement); and whether the stated **cloud cover** applies to your AOI or the whole scene.

**Be careful:** the licence is the **originating operator's**, not SkyFi's — read the EULA attached to the order before publishing or redistributing. **Do not use a satellite image as a survey**: a 30 cm image is not 30 cm accurate in *position*, and horizontal accuracy is typically metres unless the product is explicitly precision-orthorectified against control. Redistribution rights are usually restricted — use in a building submission is normally internal/regulatory, but a public web map may not be permitted.

> `needs-verification`: SkyFi's per-order redistribution terms. They are set per provider and must be read per purchase.

## 7. Sourcing Namibian base data

| Layer | Source | Licence | Note |
|---|---|---|---|
| Roads, tracks, buildings, places | **OpenStreetMap** (Geofabrik `namibia-latest.osm.pbf`) | ODbL | Coverage of Ohangwena is improving; tracks are patchy. HOT mapping has helped |
| Roads, buildings, places (packaged) | **Overture** (2026-08-19.0) | **ODbL** for transportation/buildings; **CDLA-Permissive** for places | Better IDs and conflation; same ODbL constraint on the OSM-derived themes |
| Settlements, admin boundaries, coastline | **Natural Earth** (1:10m) | Public domain | Small scale only |
| Place names | **GeoNames** | CC BY 4.0 | Gazetteer, not survey positions |
| Regional/constituency boundaries | Namibia Statistics Agency; geoBoundaries; Overture divisions | Varies | Verify vintage against the current constituency delimitation |
| Elevation (regional) | **Copernicus DEM GLO-30**, GEDTM30, AW3D30 | Free with attribution | 30 m. **Not** site-scale |
| Land cover | ESA WorldCover 10 m, Dynamic World, ESRI Land Cover | CC BY 4.0 | Good for context and vegetation extent |
| Built-up extent / settlement | **GHSL**, Microsoft/Google building footprints (via Overture) | Copernicus open / ODbL | ML footprints cover rural homesteads surprisingly well |
| Imagery (free) | **Sentinel-2** 10 m, Landsat 30 m | Copernicus open / public domain | 5-day revisit; excellent for seasonal oshana flooding |
| Imagery (commercial) | SkyFi, Planet, Vantor/Maxar, Airbus | Per EULA | 0.3–5 m |
| Topographic map series, orthophotos, geodetic control | **[NA]** **Directorate of Survey and Mapping** | Unknown | `needs-verification` — site unreachable during research |
| Cadastral / deeds | **[NA]** Surveyor-General and Deeds Registry, under the Land Survey Act 33 of 1993 | Unknown, likely fee-based | Approach through a registered surveyor or a conveyancer |
| Communal land rights | **[NA]** Communal Land Boards and Traditional Authorities; NUST's **Integrated Land Management Institute (ILMI)** publishes the research literature | Varies | See §9 |
| Hydrology, oshanas, water points | **[NA]** Atlas of Namibia; Ministry of Agriculture, Water and Land Reform; derived from Sentinel-2/DEM | Varies | See §8 |

## 8. The Cuvelai oshana system — why naive hydrology fails here

**[NA]** The Cuvelai is not a river system in the ordinary sense. It is a broad, extremely flat alluvial fan crossed by **iishana** (singular **oshana**) — shallow, grassy, interlinked channels that fill from Angolan rainfall and local rain, spread laterally, and drain slowly southwards towards the Etosha Pan. Okongo sits on the **deep Kalahari sandveld east of the main oshana network**, where relief across tens of kilometres is measured in **metres**.

This breaks standard DEM hydrology in four specific ways:

1. **Relief is below the DEM's noise floor.** With < 4 m LE90 vertical accuracy and 1–3 m of real relief across kilometres, a 30 m DEM cannot resolve the drainage direction of an oshana. Flow-accumulation output on Copernicus GLO-30 in the Cuvelai is **largely noise**, and it looks completely plausible.
2. **Sink filling destroys the landscape.** Pans and the Etosha basin are **real endorheic depressions**. Filling them turns the defining feature of the hydrology into a plateau. Use **depression breaching** (`BreachDepressionsLeastCost`) with a mask of known real depressions, or do not do DEM hydrology here at all.
3. **Flow is not channelised.** Oshana flooding is **wide, shallow, slow sheet inundation** that can persist for weeks — not a channel with a discharge. D8 single-flow-direction routing is the wrong model; multiple-flow-direction (MFD, D-infinity) is closer but still poorly conditioned on a surface this flat.
4. **The network is seasonal and variable.** Roughly 45% of years see significant oshana flooding. A single-date map of "water" is a map of that date's rainfall, not of the system.

**What to do instead — map the oshanas from imagery, not from the DEM:**

```javascript
// Earth Engine: seasonal water frequency from Sentinel-2 MNDWI, 2019-2026
var aoi = ee.Geometry.Rectangle([15.0, -18.5, 17.6, -17.0]);   // Cuvelai + eastern sandveld

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(aoi).filterDate('2019-01-01', '2026-08-01')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50))
  .map(function(img) {
    var scl = img.select('SCL');
    var clear = scl.eq(4).or(scl.eq(5)).or(scl.eq(6));
    var mndwi = img.normalizedDifference(['B3','B11']).rename('MNDWI');
    return mndwi.updateMask(clear).copyProperties(img, ['system:time_start']);
  });

// Fraction of clear observations classed as water
var water = s2.map(function(i){ return i.gt(0.0).rename('w'); });
var freq  = water.mean().clip(aoi);       // 0 = never wet, 1 = always wet

Map.addLayer(freq, {min:0, max:0.4, palette:['ffffff','cde7f0','4a90c4','1d3557']},
             'Oshana inundation frequency 2019-2026');

Export.image.toDrive({image: freq, description: 'cuvelai_water_frequency',
  region: aoi, scale: 20, crs: 'EPSG:32733', maxPixels: 1e11});
```

An **inundation-frequency** surface is the honest product: it says how often a place is wet, from observation, rather than asserting a flow direction the DEM cannot support. Cross-check it against the **2008/2009 and 2011 flood events**, which are the reference floods in living memory, and against local knowledge. Sentinel-1 SAR is a valuable complement because it sees through the wet-season cloud that blocks Sentinel-2 exactly when flooding occurs.

## 9. Cadastral and communal land in Namibia

**[NA]** Two land regimes, mapped very differently.

**Freehold / registered land** — surveyed cadastre, beacons, diagrams approved by the **Surveyor-General** under the **Land Survey Act 33 of 1993**, and title registered in the Deeds Registry. Coordinates are on **Schwarzeck / Lo22/xx**. Only a **registered professional land surveyor** (Act 32 of 1993) may produce the diagrams. This regime covers towns, commercial farms and proclaimed areas.

**Communal land** — a very large share of Namibia, including most of Ohangwena and the Okongo area. Rights are **customary land rights allocated by Traditional Authorities and ratified by Communal Land Boards**, not freehold title. Boundaries are often described by reference to features and neighbours rather than by surveyed coordinates, and the registration process has produced a growing but incomplete spatial record.

**Practical consequences for mapping:**

- **Do not assume a plot has surveyed boundaries.** Ask, early, whether the boundary is registered, sketched, or agreed verbally with neighbours and the Traditional Authority.
- **Where boundaries are not surveyed**, the correct product is a **boundary as agreed and demarcated on the ground**, GNSS-observed, with the agreement documented and the Traditional Authority involved — not an assertion of a legal boundary.
- **Label the plan accordingly.** "Boundary as demarcated on site, [date], in the presence of [parties]" is honest. "Site boundary" alone implies a legal boundary that may not exist.
- **NUST's Integrated Land Management Institute (ILMI)** is the principal publisher of Namibian land-tenure research and is the right starting point for the current state of communal land registration.

> `needs-verification`: the current status and public availability of the Communal Land Registration spatial dataset, and whether cadastral data for freehold land is obtainable in digital form and on what terms.

## 10. A project checklist

**Before starting**
- [ ] Deliverable CRS, vertical datum and geoid model agreed **in writing**.
- [ ] Established whether a registered surveyor's cadastral diagram is required, or a topographic site plan suffices.
- [ ] Land regime established: freehold with surveyed boundaries, or communal with customary rights.
- [ ] Data licences cleared for every intended use, including the submission.
- [ ] UAV regulatory position confirmed.

**During**
- [ ] Site control observed by a method with known accuracy, marked to survive the works; both ellipsoidal and orthometric heights recorded with the geoid model named.
- [ ] 5+ GCPs plus 2–3 **independent** check points; flight height derived from a target GSD; overlap raised for uniform sandveld.

**After**
- [ ] Accuracy **measured** against the check points — bias, RMSE, LE90 — not the software's internal residual.
- [ ] Vertical datum consistent across every surface before any differencing; contour interval chosen against measured accuracy.
- [ ] Volumes reported with an uncertainty, bulking labelled as an assumption.
- [ ] Sheets exported at a **locked** round scale with a graphic scale bar and a coordinate grid, and carrying CRS, datum, epoch, sources, dates, accuracy and licence attributions.

## Sources

- [EPSG Geodetic Parameter Dataset API](https://apps.epsg.org/api/v1/) — IOGP, accessed 2026-08-25 (CRS 29377, 32733, 3855, 4293)
- [Namibian annotated statutes index](https://www.lac.org.na/laws/annoSTAT/) — Legal Assistance Centre, accessed 2026-08-25 (Land Survey Act 33 of 1993)
- [Professional Land Surveyors', Technical Surveyors' and Survey Technicians' Act 32 of 1993](https://www.lac.org.na/laws/annoSTAT/Professional%20Land%20Surveyors'%20Technical%20Surveyors'%20and%20Survey%20Technicians'%20Act%2032%20of%201993.pdf) — accessed 2026-08-25
- [NUST Programmes](https://www.nust.na/programmes) — accessed 2026-08-25 (Integrated Land Management Institute)
- [OpenDroneMap documentation](https://docs.opendronemap.org/) — accessed 2026-08-25
- [SkyFi](https://skyfi.com/) — accessed 2026-08-25
- [Copernicus DEM collection description](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM) — accessed 2026-08-25
- [OpenStreetMap copyright](https://www.openstreetmap.org/copyright) — accessed 2026-08-25
- Internal: `18_namibia_context/01_geography-and-regions.md`, `02_climate-and-weather.md`, `03_geology-and-soils.md` for the Cuvelai, oshana and Okongo terrain description

## Open questions

- **[NA]** Directorate of Survey and Mapping: product catalogue, scales, digital availability, pricing and licence. Site unreachable. `needs-verification`.
- **[NA]** Whether digital cadastral data is obtainable from the Surveyor-General / Deeds Registry, and on what terms.
- **[NA]** Current status and public availability of the Communal Land Registration spatial dataset.
- **[NA]** Namibia Civil Aviation Authority UAV rules — registration, operator authorisation, altitude ceiling, insurance, BVLOS.
- **[NA]** Whether an official Schwarzeck ↔ ITRF transformation (7-parameter or grid) is published, and whether a national geoid model exists beyond EGM2008.
- **[NA]** Whether a national CORS network with public correction streams covers northern Namibia.
- Local Authority / Regional Council submission requirements for Okongo — required scales, sheet sizes, and whether a surveyor's diagram is mandatory.
- SkyFi per-order redistribution terms (set by each originating operator).

