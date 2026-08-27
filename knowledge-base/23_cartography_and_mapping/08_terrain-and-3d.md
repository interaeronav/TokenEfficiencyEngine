---
id: cartography.terrain
title: Terrain, elevation models and 3D
domain: 23_cartography_and_mapping
tags: [dem, dsm, dtm, lidar, pdal, void-filling, hydrological-conditioning, slope, aspect, viewshed, watershed, point-cloud, heightmap, unreal-engine, blender, accuracy-assessment]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Copernicus DEM collection description", url: "https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM", publisher: "Copernicus Data Space Ecosystem", accessed: 2026-08-25}
  - {title: "ALOS World 3D-30m", url: "https://www.eorc.jaxa.jp/ALOS/en/dataset/aw3d30/aw3d30_e.htm", publisher: "JAXA EORC", accessed: 2026-08-25}
  - {title: "GEDTM30 repository", url: "https://github.com/openlandmap/GEDTM30", publisher: "OpenGeoHub Foundation", accessed: 2026-08-25}
  - {title: "GDAL gdaldem", url: "https://gdal.org/en/stable/programs/gdaldem.html", publisher: "GDAL contributors", accessed: 2026-08-25}
related: [cartography.data, cartography.remote_sensing, cartography.software, cartography.namibia]
unit_system: SI
---

# Terrain, elevation models and 3D

**Summary.** Elevation is the layer most often used carelessly. Three things must be established before any terrain product is trustworthy: **which surface** it represents (bare earth or first-return), **which vertical datum** its heights are on, and **what its measured accuracy is** — not the accuracy printed on the source datasheet. This file covers the DSM/DTM/DEM distinction, resolution and vertical accuracy, void filling and hydrological conditioning, the standard derivatives with commands, lidar processing and PDAL, point clouds and meshes, the practical heightmap-export workflow to Unreal Engine and Blender with the scaling maths, and how to measure terrain accuracy against control points.

## Key facts

| Item | Value |
|---|---|
| **DEM** | Umbrella term: any gridded elevation model |
| **DSM** | **Digital Surface Model** — first reflective surface: canopy, buildings, powerlines |
| **DTM** | **Digital Terrain Model** — bare earth, vegetation and structures removed |
| Copernicus DEM GLO-30 | 1″ (~31 m), **DSM**, EGM2008, **< 4 m vertical LE90**, ~6 m horizontal CE90, TanDEM-X 2011–2015 |
| GEDTM30 | 1″, **DTM**, EGM2008, ~3 m (provisional), **ships a per-pixel uncertainty band**, coverage 83.7°N–62.0°S, **CC BY 4.0** |
| ALOS AW3D30 | 1″ (~30 m), DSM, PRISM optical stereo; v4.1 global (Mar 2025), 23 993 tiles; free for **commercial and non-commercial** use |
| SRTM v3 | 1″/3″, DSM, **EGM96**, ~16 m LE90 spec |
| Typical airborne lidar | 0.3–1 m grid, DTM+DSM, **0.1–0.6 m** vertical |
| Drone photogrammetry | 1–5 cm GSD, DSM (DTM after ground filtering), **2–5 × GSD** vertical with good control |
| LE90 | Linear Error at 90% confidence — 90% of errors fall within ±LE90 |
| RMSE→LE90 (normal errors) | LE90 ≈ **1.6449 × RMSE**; LE95 ≈ 1.96 × RMSE |

> ⚠️ **The vertical datum is the silent killer.** SRTM is on **EGM96**; Copernicus and GEDTM30 are on **EGM2008**; a raw GNSS-derived drone DSM is on the **ellipsoid**. Mosaicking any two of these without transformation produces a metre-scale step at every seam that renders beautifully and is completely wrong. Transform first, then verify at boundaries with sample transects.

## 1. DSM vs DTM vs DEM

| | DSM | DTM |
|---|---|---|
| Includes | Canopy, buildings, bridges, powerlines | Bare ground only |
| Produced by | Radar/optical stereo first return; photogrammetric dense matching; lidar first return | Lidar ground classification; ground filtering; ML inference |
| Use for | Line of sight, solar shading, viewsheds involving obstruction, building heights, flight obstacle clearance | Hydrology, drainage, cut/fill, contours, geomorphology, slope stability |
| Example | Copernicus GLO-30, AW3D30, SRTM, a raw ODM DSM | GEDTM30, national lidar DTMs, an ODM DTM after ground filtering |

**nDSM (normalised DSM) = DSM − DTM** gives object height above ground — canopy height, building height. This is how you extract building heights from a drone survey without measuring anything.

**In Namibia the DSM/DTM difference is small over most terrain** — sparse mopane, thornveld and open sandveld means the canopy offset is often under a metre. It becomes significant in riparian woodland along the Okavango and Kunene, in dense mopane, and in any settlement where the DSM includes rooftops. Do not assume the difference away for a site plan: a Copernicus GLO-30 pixel over a homestead includes the roof.

## 2. Resolution and vertical accuracy

Two independent properties, routinely conflated:

- **Grid resolution (post spacing)** — how far apart the samples are. A 1 m grid interpolated from 30 m data is *resampled*, not *higher resolution*. It has 1 m pixels and 30 m information.
- **Vertical accuracy** — how close a height is to truth, expressed as RMSE, LE90 or LE95, and always against **independent control**.

**Accuracy is not uniform.** It varies systematically with slope, land cover and the source's own acquisition geometry. A single aggregate figure that hides a forested-terrain or steep-slope failure is not an honest claim. Report the **worst stratum**, not the mean.

Practical resolution guidance:

| Task | Minimum sensible resolution |
|---|---|
| Continental context, hypsometric tint | 90 m (GLO-90) |
| Regional hydrology, catchment delineation | 30 m (GLO-30, GEDTM30) |
| Local drainage, flood routing | 5–10 m |
| Site earthworks, cut/fill, contours at 0.25 m | **0.1–0.5 m** — only lidar or photogrammetry reaches this |
| Building setting-out levels | Survey points, not a raster |

> A 30 m DEM cannot support cut/fill volumes on a building plot. One pixel is roughly the whole footprint. This is not a resolution that can be "interpolated up".

## 3. Void filling

Voids occur where the sensor could not measure: radar shadow and layover in steep terrain (SRTM, TanDEM-X), cloud and water in optical stereo, and specular water surfaces.

| Method | When |
|---|---|
| **Fill from another DEM** (delta surface fill) | The best method where a second source exists. Compute the offset surface between the two around the void edge, apply it to the filler, and blend |
| **Interpolation** — IDW, spline, `gdal_fillnodata` | Small voids in gentle terrain |
| **Hydrological conditioning fill** | Only if the void is in a flat area and the surface is for flow routing |
| **Leave as nodata** | Often correct. A void filled by interpolation looks like data and is not |

> ⚠️ **A void-filled pixel must not inherit the parent tile's accuracy claim.** Copernicus DEM ships a **fill mask** identifying pixels infilled from ASTER, SRTM and other sources. Carry that mask through your processing and degrade the accuracy attribute for those pixels. If you cannot carry it, say so.

```bash
# Interpolate small voids, limited search distance, then smooth the seams
gdal_fillnodata.py -md 20 -si 2 -of GTiff dem_voids.tif dem_filled.tif

# Delta surface fill from a second DEM (conceptually)
gdal_calc.py -A dem_primary.tif -B dem_filler.tif -C void_mask.tif \
  --outfile=dem_merged.tif \
  --calc="where(C==1, B + delta, A)" --NoDataValue=-9999
```

## 4. Hydrological conditioning

A raw DEM contains **sinks** (pits) — cells with no lower neighbour — from noise, resolution and real closed depressions. Flow routing algorithms terminate at sinks, fragmenting the drainage network.

| Operation | Effect | Risk |
|---|---|---|
| **Fill sinks** (Wang & Liu, Planchon-Darboux) | Raises pits to their pour point | **Destroys real closed depressions** — a fatal error in Namibia, where pans and the Etosha basin *are* real endorheic depressions |
| **Breach depressions** (Lindsay) | Cuts a channel through the barrier instead of raising the pit | Preserves more of the original surface; the better default |
| **Stream burning** | Lowers cells along known stream lines | Forces agreement with a vector network; can create artificial channels |
| **Hybrid breach-then-fill** | Breach what is cheap to breach, fill the rest | The pragmatic standard (WhiteboxTools `BreachDepressionsLeastCost`) |

> ⚠️ **[NA]** Namibia is dominated by **endorheic and ephemeral** drainage: the Cuvelai **oshana** system in the north, pans across the Kalahari, and ephemeral westward-flowing rivers that rarely reach the sea. Blind sink-filling turns the Etosha Pan into a plateau and erases the oshanas. Use depression **breaching**, keep a mask of known real depressions, and validate the derived network against imagery before believing it. See `10_practical-projects-and-namibia.md`.

```bash
# GRASS r.watershed handles depressions without a separate fill step
grass -c EPSG:32733 /tmp/grass/nam --exec bash -c '
  r.in.gdal input=dem.tif output=dem
  g.region raster=dem
  r.watershed -s elevation=dem threshold=2000 \
    accumulation=facc drainage=fdir stream=streams basin=basins
  r.stream.order stream_rast=streams direction=fdir strahler=strahler
  r.to.vect input=streams output=streams_v type=line
  v.out.ogr input=streams_v output=streams.gpkg format=GPKG
  r.out.gdal input=basins output=basins.tif
'

# WhiteboxTools: breach rather than fill
whitebox_tools -r=BreachDepressionsLeastCost --dem=dem.tif --output=dem_bd.tif --dist=100
whitebox_tools -r=D8Pointer   --dem=dem_bd.tif --output=d8.tif
whitebox_tools -r=D8FlowAccumulation --i=d8.tif --output=facc.tif --pntr
whitebox_tools -r=ExtractStreams --flow_accum=facc.tif --output=streams.tif --threshold=2000
```

## 5. Terrain derivatives

| Derivative | Definition | Use |
|---|---|---|
| **Slope** | Magnitude of the elevation gradient; degrees or percent | Buildability, erosion risk, access, drainage |
| **Aspect** | Direction of steepest descent, 0–360° | Solar exposure, wind exposure, ecology |
| **Curvature** | Second derivative. **Profile** (down-slope) drives acceleration; **plan** (across-slope) drives convergence; **total/mean** for general morphometry | Landform classification, deposition/erosion zones |
| **Hillshade** | Simulated illumination; conventionally az 315°, alt 45° | Visualisation only — never analysis |
| **TRI / roughness / TPI** | Local variability and relative position | Habitat, trafficability, landform classes |
| **Viewshed** | Cells visible from an observer | Visual impact assessment, mast/antenna siting, security |
| **Flow accumulation** | Upslope contributing cells | Channel network, stream ordering |
| **Watershed / basin** | Catchment upstream of a pour point | Hydrology, runoff estimation |
| **TWI** | `ln(a / tan β)` — specific catchment area over slope | Wetness, soil moisture potential, waterlogging risk |
| **Solar irradiation** (`r.sun`) | Modelled direct + diffuse over a period | PV siting, shading studies |

```bash
# All the standard gdaldem derivatives. NOTE: the DEM must be in a metric CRS.
gdaldem slope     dem_utm33s.tif slope_deg.tif  -compute_edges
gdaldem slope     dem_utm33s.tif slope_pct.tif  -p -compute_edges
gdaldem aspect    dem_utm33s.tif aspect.tif     -compute_edges -zero_for_flat
gdaldem hillshade dem_utm33s.tif hs.tif         -multidirectional -compute_edges
gdaldem TRI       dem_utm33s.tif tri.tif        -compute_edges
gdaldem roughness dem_utm33s.tif rough.tif      -compute_edges
gdaldem color-relief dem_utm33s.tif hypso.txt hypso.tif -alpha

# Viewshed from an observer 10 m above ground, 15 km radius
gdal_viewshed -md 15000 -ox 664231 -oy 8055412 -oz 10 -tz 1.75 \
  dem_utm33s.tif viewshed.tif

# Contours: 5 m index + 1 m intermediate
gdal_contour -a elev -i 1.0  dem_utm33s.tif contours_1m.gpkg  -f GPKG
gdal_contour -a elev -i 5.0  dem_utm33s.tif contours_5m.gpkg  -f GPKG
```

> If the DEM is in EPSG:4326 (degrees), `gdaldem slope` with default settings is wrong — horizontal units are degrees, vertical are metres. **Reproject to a metric CRS first** (correct), or pass `-s 111120` (approximate, and wrong away from the equator by cos(latitude)).

## 6. Lidar processing

Airborne lidar delivers a classified point cloud. The ASPRS standard classification codes:

| Code | Class |
|---|---|
| 0/1 | Never classified / Unclassified |
| **2** | **Ground** |
| 3, 4, 5 | Low, medium, high vegetation |
| **6** | **Building** |
| 7 | Low point (noise) |
| 9 | Water |
| 10 | Rail |
| 11 | Road surface |
| 13–18 | Wire guard, wire conductor, transmission tower, bridge deck, high noise |

**Ground filtering** — separating class 2 from everything else — is the critical step and determines DTM quality:

- **Progressive Morphological Filter (PMF)** — opening with an increasing window; simple, tends to shave hilltops.
- **Simple Morphological Filter (SMRF)** — an improved PMF; PDAL's `filters.smrf` and a good default.
- **Cloth Simulation Filter (CSF)** — inverts the cloud and drapes a virtual cloth; intuitive parameters (rigidness, cloth resolution), excellent on moderate terrain.
- **TIN densification (Axelsson)** — the classical method behind commercial packages (TerraScan, LAStools `lasground`).

**PDAL** is the GDAL of point clouds — a pipeline-driven processing library.

```json
{
  "pipeline": [
    { "type": "readers.las", "filename": "site.laz" },

    { "type": "filters.reprojection",
      "in_srs": "EPSG:4326", "out_srs": "EPSG:32733" },

    { "type": "filters.outlier",
      "method": "statistical", "mean_k": 12, "multiplier": 2.5 },

    { "type": "filters.smrf",
      "ignore": "Classification[7:7]",
      "slope": 0.2, "window": 18, "threshold": 0.45, "scalar": 1.2 },

    { "type": "filters.range", "limits": "Classification[2:2]" },

    { "type": "writers.gdal",
      "filename": "dtm_0p5m.tif",
      "resolution": 0.5,
      "output_type": "idw",
      "window_size": 6,
      "gdaldriver": "GTiff",
      "gdalopts": "COMPRESS=DEFLATE,PREDICTOR=2,TILED=YES" }
  ]
}
```

```bash
pdal pipeline dtm.json
pdal info site.laz --summary                 # extent, count, classes, SRS
pdal info site.laz --stats                   # per-dimension statistics
pdal translate site.laz site_copc.laz --writers.copc.filename=site.copc.laz

# Build a DSM instead: keep first returns, use max
pdal translate site.laz dsm.tif \
  --writers.gdal.resolution=0.5 --writers.gdal.output_type=max
```

**CloudCompare** is the essential interactive companion — registration, cloud-to-cloud and cloud-to-mesh distance, manual classification, cross-sections, and volume computation.

## 7. Point clouds and meshes

| Stage | Format | Tool |
|---|---|---|
| Raw / classified cloud | **LAS / LAZ** | PDAL, LAStools, CloudCompare |
| Cloud-optimised cloud | **COPC** (clustered octree LAZ, range-requestable) | PDAL, Entwine |
| Tiled cloud for the web | **Entwine Point Tile (EPT)**, **3D Tiles pnts** | Entwine, Potree, CesiumJS |
| Mesh | PLY, OBJ, **glTF/GLB** | MeshLab, Blender, CloudCompare |
| Web streaming mesh | **3D Tiles** (v1.1, OGC 22-025r4) | Cesium, deck.gl |

**Cloud → mesh** in practice: clean and downsample, estimate normals, then Poisson surface reconstruction (smooth, watertight, invents geometry in gaps) or Delaunay/ball-pivoting (faithful, leaves holes). For terrain specifically, a **2.5D TIN** from the ground class is usually more useful and far lighter than a full 3D mesh.

**Potree** publishes a point cloud to a browser with no plugin; **Entwine** builds the tiled index it reads.

## 8. Terrain for game engines and visualisation

### The scaling maths, stated once

A heightmap is an image whose pixel values encode elevation. The three numbers you must get right:

1. **Horizontal extent** — `pixels × ground_resolution_m`. A 4096 × 4096 grid at 5 m/px covers 20 480 m.
2. **Vertical range** — `max_elev − min_elev` in metres, read from `gdalinfo -stats`.
3. **Bit depth** — **16-bit is mandatory**. 8-bit gives 256 levels; over a 340 m range that is 1.33 m per step and visible terracing. 16-bit gives 65 536 levels — 5 mm per step over the same range.

```bash
# Get the range
gdalinfo -stats dem_utm33s.tif | grep -E "STATISTICS_(MINIMUM|MAXIMUM)"
# STATISTICS_MINIMUM=1108.42
# STATISTICS_MAXIMUM=1189.77   ->  range = 81.35 m

# Export a 16-bit PNG heightmap scaled across the full range
gdal_translate -of PNG -ot UInt16 -scale 1108.42 1189.77 0 65535 \
  dem_utm33s.tif heightmap_16.png

# Or a 16-bit raw for engines that want it
gdal_translate -of ENVI -ot UInt16 -scale 1108.42 1189.77 0 65535 \
  dem_utm33s.tif heightmap.raw
```

### Unreal Engine

Unreal's Landscape wants a **16-bit greyscale PNG or RAW**, and prefers specific dimensions. The recommended sizes follow `(components × quads_per_component) + 1`:

| Resolution | Components | Note |
|---|---|---|
| 505 × 505 | 8×8 of 63 | Small |
| 1009 × 1009 | 16×16 of 63 | Common |
| **2017 × 2017** | 32×32 of 63 | Large, practical |
| 4033 × 4033 | 64×64 of 63 | Very large |
| 8129 × 8129 | 128×128 of 63 | World Partition territory |

```bash
# Resample to an Unreal-friendly size
gdalwarp -ts 2017 2017 -r cubicspline dem_utm33s.tif dem_2017.tif
gdal_translate -of PNG -ot UInt16 -scale 1108.42 1189.77 0 65535 \
  dem_2017.tif ue_heightmap.png
```

**Unreal scale settings.** Unreal units are **centimetres**. The Landscape import dialog takes Scale X/Y/Z as percentages where **100 = 1 uu per heightmap sample** for X/Y, and Z is scaled such that **100 corresponds to a 512 m total height range** (the engine's default `-256 m … +256 m` for the full 16-bit range).

```
Scale X = Scale Y = (ground_resolution_m × 100 cm/m)                 [as a percentage]
Scale Z = (vertical_range_m / 512) × 100                             [as a percentage]
```

Worked example — 2017 × 2017 samples at 10.16 m/px (20 480 m / 2016 intervals ≈ 10.16 m), vertical range 81.35 m:

```
Scale X = Scale Y = 10.16 × 100 = 1016
Scale Z = (81.35 / 512) × 100 = 15.89
```

Sanity check: `2016 intervals × 10.16 m × 100 cm/m = 2 048 256 uu = 20 482.56 m` — matches the source extent. **Always do this check.** If the terrain in-engine is not the size of the real place, one of the three numbers is wrong.

> A 20 km × 20 km landscape at 10 m sample spacing is far coarser than a playable surface needs. For a construction-site visualisation, export the **site** at 0.25–1 m from the drone DTM (say 2017 × 2017 at 0.5 m = ~1 km square) and use the 30 m regional DEM only as distant backdrop.

### Blender

Blender units default to **metres**, which makes the maths trivial. The displacement approach (see also `05_gis-software-and-tooling.md`):

```python
import bpy

# --- Parameters from gdalinfo ---
GROUND_W_M  = 20480.0     # ground extent, metres
GROUND_H_M  = 20480.0
Z_RANGE_M   = 81.35       # max - min elevation
SUBDIV      = 10          # 2^10 = 1024 divisions; raise for more detail

bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0))
plane = bpy.context.object
plane.name = "Terrain"
plane.scale = (GROUND_W_M / 2.0, GROUND_H_M / 2.0, 1.0)
bpy.ops.object.transform_apply(scale=True)

sub = plane.modifiers.new("Subdiv", 'SUBSURF')
sub.subdivision_type = 'SIMPLE'
sub.levels = 4                    # viewport
sub.render_levels = SUBDIV        # render

tex = bpy.data.textures.new("heightmap", 'IMAGE')
img = bpy.data.images.load("/data/heightmap_16.png")
img.colorspace_settings.name = 'Non-Color'   # CRITICAL: no sRGB transform
tex.image = img
tex.extension = 'EXTEND'

disp = plane.modifiers.new("Displace", 'DISPLACE')
disp.texture = tex
disp.texture_coords = 'UV'
disp.mid_level = 0.0              # 0 maps image black to z=0
disp.strength = Z_RANGE_M         # image white maps to z = Z_RANGE_M
```

Three things that must be right:
1. **`colorspace_settings.name = 'Non-Color'`** — otherwise Blender applies an sRGB curve to the heightmap and the terrain is subtly, systematically distorted.
2. **`mid_level = 0.0` with `strength = Z_RANGE_M`** gives exact 1:1 vertical scale. (`mid_level = 0.5` centres the displacement instead and halves the effective range.)
3. **16-bit image.** An 8-bit PNG terraces.

For rendering, drape the orthomosaic as the base colour (UV-mapped identically to the heightmap), light with a Sun at the sun position for the date and time (Blender's Sun Position add-on takes latitude, longitude, date and time directly — use −17.57, 17.22 for Okongo), and render with Cycles for real shadows and ambient occlusion.

**Add-ons worth knowing:** **BlenderGIS** (imports basemaps, DEMs and Shapefiles with georeferencing), **Sun Position** (bundled).

### Other export targets

- **Unity** — Terrain component imports 16-bit RAW; heightmap resolution must be `2^n + 1` (513, 1025, 2049, 4097). Unity units are metres.
- **Three.js / deck.gl** — displacement in a vertex shader from a Terrain-RGB or Terrarium texture; see `06`.
- **3D printing** — QGIS's **DEMto3D** plugin exports STL directly with a chosen scale and base thickness.

## 9. Terrain accuracy assessment

The phase that is routinely skipped and the one that makes a terrain product defensible.

**Principles:**
1. Measure against **independent control**, never against another DEM and never against a competitor product.
2. Control sources: **own RTK GNSS observations** (best for a site), levelled benchmarks, **ICESat-2 ATL08** and **GEDI L2A** (free, global, laser altimetry), NGS-style datasheets, published AIP aerodrome elevations.
3. **Stratify** by land cover and slope and report the **worst stratum**. An aggregate figure that hides a vegetated-terrain failure is not an honest claim.
4. Errors in steep terrain are often **not normal**. When the distribution fails a normality test, fall back from LE90 to the **90th percentile of absolute error** and say so.
5. Check for a **systematic bias** first. A constant offset usually means a vertical datum mismatch, not random error — fix the cause rather than reporting the symptom.

**The statistics:**

```
error_i   = z_DEM(x_i, y_i) − z_control_i
bias      = mean(error)
RMSE      = sqrt( mean(error²) )
σ         = std(error)
LE90      = 1.6449 × RMSE          [only if errors are ~normal and bias ≈ 0]
LE90_np   = 90th percentile of |error|   [distribution-free fallback]
```

```python
import numpy as np, pandas as pd, rasterio
from scipy import stats

cp = pd.read_csv("check_points.csv")           # x, y, z_orthometric, cover, slope_class
with rasterio.open("dtm_ortho.tif") as src:
    cp["z_dem"] = [v[0] for v in src.sample(zip(cp.x, cp.y))]

cp["err"] = cp.z_dem - cp.z_orthometric
cp = cp[np.isfinite(cp.err)]

def report(g, label):
    e = g.err.values
    rmse = np.sqrt(np.mean(e**2))
    normal = stats.shapiro(e).pvalue > 0.05 if 3 <= len(e) <= 5000 else False
    le90 = 1.6449 * rmse if normal and abs(e.mean()) < 0.1 * rmse else np.percentile(np.abs(e), 90)
    print(f"{label:22s} n={len(e):4d}  bias={e.mean():+7.3f}  "
          f"RMSE={rmse:6.3f}  LE90={le90:6.3f}  "
          f"{'(normal)' if normal else '(non-parametric)'}")

report(cp, "ALL")
for cover, g in cp.groupby("cover"):
    report(g, f"cover={cover}")
for sl, g in cp.groupby("slope_class"):
    report(g, f"slope={sl}")
```

**What to declare.** State the measured figure, the confidence level, the number and source of control points, the stratification, and whether the estimate is parametric or not. If validation has not run for a region, say the accuracy is **provisional and based on the source datasheet** — do not present a datasheet figure as a product claim.

**A worked interpretation:** a drone DTM at 2 cm GSD, checked against 6 RTK points held out of the bundle adjustment, showing `bias = +0.031 m, RMSE = 0.048 m, LE90 = 0.079 m` is a genuinely survey-grade product for earthworks. The same job reporting only the software's internal GCP residual of 0.012 m has measured nothing.

## Sources

- [Copernicus DEM collection description](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM) — accessed 2026-08-25
- [ALOS World 3D-30m](https://www.eorc.jaxa.jp/ALOS/en/dataset/aw3d30/aw3d30_e.htm) — JAXA EORC, accessed 2026-08-25
- [GEDTM30](https://github.com/openlandmap/GEDTM30) — OpenGeoHub Foundation, accessed 2026-08-25. Publication: Ho, Y.-F., Grohmann, C.H., Lindsay, J., Reuter, H.I., Parente, L., Witjes, M. & Hengl, T. (2025), *PeerJ* 13:e19673, CC BY 4.0
- [GDAL gdaldem](https://gdal.org/en/stable/programs/gdaldem.html) — GDAL contributors, accessed 2026-08-25
- [PDAL documentation](https://pdal.io/) — PDAL contributors, accessed 2026-08-25
- [OGC 3D Tiles](https://www.ogc.org/standards/3dtiles/) — OGC, accessed 2026-08-25

## Open questions

- Unreal Engine's Scale Z convention (100 = 512 m range) is the long-standing Landscape behaviour; confirm against the current engine version's Landscape documentation before relying on it for a precise model. `needs-verification`.
- Unity's terrain heightmap resolution constraint (`2^n + 1`) is stable but the current importer's handling of 16-bit RAW endianness was not verified.
- GEDTM30's current COG endpoint — the GitHub repository has moved to Codeberg and the OpenLandMap STAC entry should be checked before a production run.
- **[NA]** Whether any national or regional lidar coverage exists for Namibia. None found. `needs-verification`.
