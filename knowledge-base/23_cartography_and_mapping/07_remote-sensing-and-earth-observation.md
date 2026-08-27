---
id: cartography.remote_sensing
title: Remote sensing and Earth observation
domain: 23_cartography_and_mapping
tags: [remote-sensing, earth-observation, sentinel-2, landsat, ndvi, ndwi, nbr, savi, sar, insar, classification, google-earth-engine, planetary-computer, photogrammetry, drone, uav, gsd, gcp, opendronemap]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Sentinel-2 mission", url: "https://sentiwiki.copernicus.eu/web/s2-mission", publisher: "ESA SentiWiki", accessed: 2026-08-25}
  - {title: "STAC specification", url: "https://stacspec.org/en", publisher: "STAC community", accessed: 2026-08-25}
  - {title: "OpenDroneMap documentation", url: "https://docs.opendronemap.org/", publisher: "OpenDroneMap", accessed: 2026-08-25}
  - {title: "Copernicus DEM collection description", url: "https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM", publisher: "Copernicus Data Space Ecosystem", accessed: 2026-08-25}
related: [cartography.data, cartography.terrain, cartography.namibia, cartography.trends]
unit_system: SI
---

# Remote sensing and Earth observation

**Summary.** Remote sensing is the measurement of electromagnetic radiation reflected or emitted by the Earth's surface, and the inference of surface properties from it. The whole discipline reduces to a chain: a sensor measures radiance in defined wavebands; atmospheric correction converts that to surface reflectance; band arithmetic or a classifier converts reflectance to information; and validation says how much of that information is real. This file covers the physics, the missions and their bands, correction, the standard indices with formulas, SAR and InSAR, classification including deep learning, the two big cloud platforms with runnable code, and drone photogrammetry from flight planning through to a georeferenced orthomosaic.

## Key facts

| Item | Value |
|---|---|
| **Sentinel-2** constellation | 2A (2015), 2B (2017), **2C (2024)**; nominal pair operating, 2A in extension campaign as of March 2025 |
| Sentinel-2 revisit | **5 days at the equator** (constellation); **290 km** swath; 56°S–82.8°N |
| Sentinel-2 10 m bands | **B2 blue 492.7 nm, B3 green 559.9 nm, B4 red 664.6 nm, B8 NIR 832.8 nm** |
| Sentinel-2 20 m bands | B5–B7 red-edge (704–783 nm), B8A narrow NIR 865 nm, **B11 SWIR 1614 nm, B12 SWIR 2202 nm** |
| Sentinel-2 60 m bands | B1 aerosol 442.7 nm, B9 water vapour 945.1 nm, B10 cirrus 1373.5 nm |
| Sentinel-2 product levels | **L1C** = top-of-atmosphere reflectance, orthorectified; **L2A** = bottom-of-atmosphere surface reflectance (systematic since December 2018) |
| Landsat 8/9 | 30 m multispectral, 15 m pan, 100 m thermal; 16-day per satellite, **8-day combined** |
| Landsat archive | Continuous since **1972** — the longest civilian Earth record |
| GSD formula (nadir) | **GSD = (sensor pixel pitch × flight height) / focal length** |
| Typical survey-grade drone accuracy | **1–3 × GSD** horizontally with good GCPs; **2–5 × GSD** vertically |
| Minimum GCPs for a small site | **5** (four corners + one centre); more for larger or elongated sites |
| Typical photogrammetric overlap | **75–80% front**, **65–75% side**; higher over uniform terrain |

> ⚠️ An orthomosaic produced without ground control is georeferenced only as well as the drone's onboard GNSS — typically **metres** horizontally and **several metres to tens of metres** vertically, and the vertical is on the *ellipsoid*, not the geoid. It will look perfect. Do not use it for levels, setting-out or volumes without control. See §9.

## 1. The physics

**The electromagnetic spectrum, as used in EO:**

| Region | Wavelength | Measures |
|---|---|---|
| Visible (VIS) | 0.4–0.7 µm | Colour; chlorophyll absorption in blue and red |
| Near infrared (NIR) | 0.7–1.3 µm | **Vegetation structure** — healthy leaves reflect NIR strongly |
| Shortwave infrared (SWIR) | 1.3–3.0 µm | **Moisture content**, minerals, burn severity, soil |
| Thermal infrared (TIR) | 3–14 µm | **Emitted** radiation — surface temperature |
| Microwave | 1 mm–1 m | Active radar (SAR); penetrates cloud, works at night; sensitive to roughness, moisture, structure |

**Spectral signatures** — the reflectance-versus-wavelength curve of a surface. The three you must be able to recognise:

- **Healthy vegetation**: low blue, small green peak (~0.55 µm), strong red absorption (chlorophyll), then a **red edge** — a near-vertical rise between ~0.68 and ~0.75 µm — into a high NIR plateau, then SWIR dips at water-absorption features (~1.45, ~1.95 µm).
- **Water**: moderate in blue, declining through green and red, and **near-zero in NIR and SWIR**. This makes water trivially separable with any NIR band.
- **Bare soil / sand**: a gently rising curve from blue to SWIR with no red edge. Namibian Kalahari sand is bright across VIS–SWIR, which matters: it can saturate and it makes vegetation indices noisy at low cover.

**Passive vs active:**
- **Passive** sensors measure reflected sunlight or emitted thermal radiation. Cheap, well understood, **blocked by cloud, useless at night** for reflective bands.
- **Active** sensors emit their own energy and measure the return: **SAR** (radar), **lidar**, altimeters. All-weather, day/night, but geometrically and radiometrically harder to interpret.

## 2. The four resolutions

| Resolution | Definition | Trade-off |
|---|---|---|
| **Spatial** | Ground sample distance per pixel | Finer spatial → narrower swath → longer revisit and more data |
| **Spectral** | Number and width of bands | More/narrower bands → less energy per band → lower SNR or coarser spatial |
| **Temporal** | Revisit interval | Constellation size vs cost |
| **Radiometric** | Bits per pixel (8, 12, 16-bit) | Dynamic range; matters for dark water and bright sand in one scene |

You cannot maximise all four. Sentinel-2 chooses medium spatial (10 m), good spectral (13 bands), good temporal (5 days), free. Maxar/Vantor chooses very fine spatial (0.3 m), modest spectral, tasked temporal, expensive.

## 3. The major missions

| Mission | Spatial | Bands | Revisit | Access |
|---|---|---|---|---|
| **Sentinel-2 A/B/C** | 10/20/60 m | 13 (442–2202 nm) | 5 d | Free — Copernicus Data Space, AWS, GEE, PC |
| **Sentinel-1 A/C** | 5×20 m (IW) | C-band SAR, VV+VH | 6–12 d | Free |
| **Sentinel-3 OLCI/SLSTR** | 300 m / 500–1000 m | 21 / 9 | ~1–2 d | Free — ocean, land, LST |
| **Landsat 8/9 OLI-TIRS** | 30 m, 15 m pan, 100 m TIR | 11 | 8 d combined | Free — USGS EarthExplorer, AWS, GEE |
| **MODIS (Terra/Aqua)** | 250–1000 m | 36 | daily | Free — the long climate record |
| **VIIRS (Suomi-NPP, NOAA-20/21)** | 375–750 m | 22 | daily | Free — includes night lights |
| **PlanetScope** | 3–5 m | 4–8 | ~daily | Commercial |
| **Pléiades / Pléiades Neo** | 0.5 / 0.3 m | pan + 4/6 | tasked | Commercial |
| **WorldView (Vantor/Maxar)** | 0.3 m | pan + 8 + SWIR | tasked | Commercial |
| **ICEYE / Capella / Umbra** | 0.25–1 m SAR | X-band | tasked | Commercial |

## 4. Atmospheric correction

Between the surface and the sensor lie scattering (Rayleigh from molecules, Mie from aerosols) and absorption (water vapour, ozone, CO₂). Uncorrected, these:
- add a wavelength-dependent **path radiance** (worst in blue), and
- **attenuate** the surface signal.

The correction chain:

```
DN  →  TOA radiance  →  TOA reflectance  →  BOA (surface) reflectance
```

| Method | How | Use |
|---|---|---|
| **Dark object subtraction (DOS)** | Assume the darkest pixel should be ~0; subtract its value per band | Quick, crude, single-scene relative work |
| **Radiative transfer models** — 6S, MODTRAN, LaSRC, **Sen2Cor** (Sentinel-2's operational processor), LEDAPS | Physically model the atmosphere from ancillary data | The correct approach; what L2A products already contain |
| **Empirical line calibration** | Regress image DN against field spectrometer measurements of bright and dark targets | Highest accuracy; needs field work |

**Practical rule:** use **L2A / Level-2 surface reflectance products** wherever they exist (Sentinel-2 L2A, Landsat Collection 2 Level-2, HLS). Only correct yourself if you must, and never compare an L1C index value to an L2A one.

**Cloud masking** is part of correction in practice. Sentinel-2 L2A ships an `SCL` scene classification band; use classes 4 (vegetation), 5 (bare soil), 6 (water), 7 (unclassified) and exclude 3 (cloud shadow), 8/9 (cloud medium/high probability), 10 (thin cirrus), 11 (snow). Better still, use **s2cloudless** or **Cloud Score+** which are substantially more accurate than the SCL band.

## 5. Spectral indices

All are normalised ratios, which cancels first-order illumination and gain differences. Values in the formulas are **surface reflectance**, not DN.

| Index | Formula | Sentinel-2 bands | Range | Reads |
|---|---|---|---|---|
| **NDVI** — Normalised Difference Vegetation Index | `(NIR − Red) / (NIR + Red)` | `(B8 − B4)/(B8 + B4)` | −1 to 1 | Green vegetation. Water < 0; bare soil 0.05–0.2; sparse veg 0.2–0.4; dense veg 0.6–0.9 |
| **NDWI** (McFeeters) — water | `(Green − NIR) / (Green + NIR)` | `(B3 − B8)/(B3 + B8)` | −1 to 1 | Open water > 0 |
| **MNDWI** (Xu) — modified water | `(Green − SWIR) / (Green + SWIR)` | `(B3 − B11)/(B3 + B11)` | −1 to 1 | Better than NDWI in built-up areas |
| **NDMI / NDWI (Gao)** — vegetation moisture | `(NIR − SWIR1) / (NIR + SWIR1)` | `(B8 − B11)/(B8 + B11)` | −1 to 1 | Canopy water content, drought stress |
| **NDBI** — built-up | `(SWIR1 − NIR) / (SWIR1 + NIR)` | `(B11 − B8)/(B11 + B8)` | −1 to 1 | Built-up > 0, but **confuses with bare soil** — a serious problem in arid Namibia |
| **NBR** — burn ratio | `(NIR − SWIR2) / (NIR + SWIR2)` | `(B8 − B12)/(B8 + B12)` | −1 to 1 | Burn severity via **dNBR = NBR_pre − NBR_post** |
| **SAVI** — soil-adjusted vegetation | `((NIR − Red) / (NIR + Red + L)) × (1 + L)` with **L = 0.5** | `((B8−B4)/(B8+B4+0.5))×1.5` | −1 to 1.5 | NDVI corrected for soil background — **the right index for sparse arid vegetation** |
| **EVI** — enhanced vegetation | `2.5 × (NIR − Red) / (NIR + 6·Red − 7.5·Blue + 1)` | B8, B4, B2 | — | Less saturating than NDVI in dense canopy; needs blue, so more atmosphere-sensitive |
| **NDRE** — red edge | `(NIR − RedEdge) / (NIR + RedEdge)` | `(B8 − B5)/(B8 + B5)` | −1 to 1 | Chlorophyll in dense canopy where NDVI saturates |
| **BSI** — bare soil | `((SWIR1+Red) − (NIR+Blue)) / ((SWIR1+Red) + (NIR+Blue))` | B11, B4, B8, B2 | −1 to 1 | Bare ground mapping |

> **For Namibia, prefer SAVI over NDVI.** With vegetation cover often below 30% and a very bright sandy background, the soil signal dominates NDVI and compresses its useful range. SAVI with L = 0.5 (or a locally tuned L) recovers discrimination. Similarly, treat **NDBI** with suspicion — bare Kalahari sand and a built-up settlement can produce indistinguishable NDBI.

## 6. SAR fundamentals and InSAR

**Synthetic Aperture Radar** transmits microwave pulses and measures amplitude and **phase** of the return. A long synthetic antenna is created by combining returns as the platform moves, giving fine along-track resolution from a small physical antenna.

Key concepts:

- **Bands:** X (~3 cm, fine detail, poor penetration), **C (~5.6 cm — Sentinel-1)**, L (~24 cm, penetrates canopy, good for soil/biomass), P (~70 cm, biomass).
- **Polarisation:** VV, VH, HH, HV. The **VV/VH ratio** is informative for vegetation structure; HH is better for flooding under vegetation.
- **Backscatter** depends on surface **roughness** relative to wavelength, **dielectric constant** (i.e. **moisture**), and **geometry**. Smooth water is a specular reflector → very dark. Urban corner reflectors → very bright.
- **Geometric distortions:** foreshortening, layover and radar shadow in terrain. Terrain correction (RTC) is mandatory before analysis.
- **Speckle** — coherent-imaging interference noise. Reduce with multilooking or a Lee/Refined Lee filter, accepting resolution loss.

**InSAR (Interferometric SAR)** compares the *phase* of two acquisitions over the same area. Phase difference maps to line-of-sight range change at a fraction of the wavelength — **millimetre to centimetre precision**.

- **DInSAR** (differential): two acquisitions, one deformation map. Used for earthquakes, volcanoes, mining subsidence, dam and building movement.
- **PSInSAR / SBAS** (time series): stacks of tens to hundreds of acquisitions, tracking persistent scatterers over years. **Millimetres per year** of velocity.
- **Coherence** is the reliability measure. It decorrelates with vegetation, water, snow and long time baselines. Namibia's sparse arid terrain has **excellent coherence** — it is close to an ideal InSAR environment, in contrast to tropical forest where C-band InSAR barely works.
- One measurement is **line-of-sight only**. Decomposing into vertical and horizontal requires ascending and descending passes.

Practical relevance for construction: InSAR is the cheapest way to detect ground movement affecting a large structure, tailings dam or open pit over time, using free Sentinel-1 data. Tools: **ESA SNAP**, **ISCE2**, **MintPy**, **LiCSBAS**, and the commercial services.

## 7. Change detection

| Method | How | Good for |
|---|---|---|
| **Image differencing / ratioing** | Subtract or divide co-registered, corrected images | Simple, interpretable; needs a threshold decision |
| **Index differencing** | dNDVI, **dNBR**, dNDWI | Standard for fire severity, vegetation loss, water extent change |
| **Post-classification comparison** | Classify each date, then cross-tabulate | Produces a from-to change matrix; **errors multiply** — 85% × 85% ≈ 72% |
| **Change vector analysis** | Magnitude and direction of change in n-band space | Detects change without pre-defining what changed |
| **Time-series breakpoint** — BFAST, LandTrendr, CCDC | Fit a temporal model and detect structural breaks | Robust to seasonality and phenology; the right approach for multi-year monitoring |
| **Deep learning (Siamese networks)** | Two-branch CNN trained on change pairs | State of the art where labelled change data exists |

**Prerequisites that are routinely skipped:** co-registration to sub-pixel accuracy, identical atmospheric correction level, **phenologically matched dates** (comparing March to September in Namibia detects the season, not change), and consistent cloud/shadow masking.

## 8. Classification

**Unsupervised** — k-means, ISODATA. Clusters spectral space without training data; the analyst then labels clusters. Cheap, fast, useful for reconnaissance. Cluster ≠ class.

**Supervised** — the analyst provides labelled training samples.

| Classifier | Note |
|---|---|
| Maximum Likelihood | Classical, parametric, assumes normality per class |
| **Random Forest** | The reliable workhorse. Handles many correlated bands, gives variable importance, resists overfitting, needs little tuning |
| Gradient boosting (XGBoost, LightGBM) | Often marginally better than RF, more tuning |
| SVM | Strong with limited training data and high dimensionality |
| **CNN / U-Net semantic segmentation** | Uses spatial context, not just spectra. State of the art for building/road/field extraction where labels exist |
| **Vision transformers / geospatial foundation models** | Prithvi, Clay, SatlasNet — pretrained on huge unlabelled EO archives, fine-tuned on small labelled sets. See `09_latest-trends.md` |

**Accuracy assessment is not optional.** Report a **confusion matrix** with:
- **Overall accuracy** — correct / total,
- **Producer's accuracy** (recall) per class — of the real class, how much was found,
- **User's accuracy** (precision) per class — of what was mapped, how much is right,
- **F1** per class, and
- ideally an **area-adjusted** estimate with confidence intervals (Olofsson et al. good practice), because a simple pixel-count area from a classified map is biased.

> Validation samples must be **independent** of training samples and drawn by a probability design. Splitting a hand-drawn training polygon into "train" and "test" halves does not produce an independent test set — the pixels are spatially autocorrelated and the accuracy will be flattering and wrong.

## 9. Google Earth Engine

Server-side planetary-scale raster analysis, free for research and non-commercial use (commercial use requires a paid Google Cloud plan).

```javascript
// Earth Engine (JavaScript Code Editor) — SAVI time series over Okongo, Namibia
var aoi = ee.Geometry.Rectangle([17.10, -17.65, 17.35, -17.45]);

function maskS2(img) {
  var scl = img.select('SCL');
  var good = scl.eq(4).or(scl.eq(5)).or(scl.eq(6)).or(scl.eq(7));
  return img.updateMask(good).divide(10000)
            .copyProperties(img, ['system:time_start']);
}

function addSAVI(img) {
  var L = 0.5;
  var savi = img.expression(
    '((NIR - RED) / (NIR + RED + L)) * (1 + L)',
    {NIR: img.select('B8'), RED: img.select('B4'), L: L}
  ).rename('SAVI');
  return img.addBands(savi);
}

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(aoi)
  .filterDate('2019-01-01', '2026-08-01')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40))
  .map(maskS2).map(addSAVI);

print(ui.Chart.image.series(s2.select('SAVI'), aoi, ee.Reducer.mean(), 20)
        .setOptions({title: 'Mean SAVI, Okongo AOI', vAxis: {title: 'SAVI'}}));

// Dry-season composite, exported in UTM 33S
var dry = s2.filter(ee.Filter.calendarRange(6, 9, 'month')).median().clip(aoi);
Map.centerObject(aoi, 12);
Map.addLayer(dry, {bands: ['B4','B3','B2'], min: 0.02, max: 0.30}, 'Dry season RGB');

Export.image.toDrive({
  image: dry.select(['B4','B3','B2','B8','B11','B12']),
  description: 'okongo_dry_2026',
  region: aoi, scale: 10, crs: 'EPSG:32733', maxPixels: 1e10
});
```

## 10. Microsoft Planetary Computer

An open STAC catalogue plus hosted compute. The advantage over GEE is that it is **standard, portable Python** — the same code runs against any STAC API.

```python
import pystac_client, planetary_computer, odc.stac
import numpy as np

catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)

items = list(catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=[17.10, -17.65, 17.35, -17.45],
    datetime="2026-06-01/2026-08-01",
    query={"eo:cloud_cover": {"lt": 20}},
).items())
print(f"{len(items)} scenes")

ds = odc.stac.load(
    items,
    bands=["B02", "B03", "B04", "B08", "B11", "SCL"],
    resolution=10,
    crs="EPSG:32733",
    bbox=[17.10, -17.65, 17.35, -17.45],
    chunks={},                       # dask-backed, lazy
)

# Cloud/shadow mask from the scene classification layer
good = ds.SCL.isin([4, 5, 6, 7])
ds = ds.where(good)

nir, red = ds.B08 / 10000.0, ds.B04 / 10000.0
L = 0.5
savi = ((nir - red) / (nir + red + L)) * (1 + L)
savi_median = savi.median(dim="time").compute()

savi_median.rio.write_crs("EPSG:32733", inplace=True)
savi_median.rio.to_raster("okongo_savi_median.tif", driver="COG",
                          compress="DEFLATE", predictor=2)
```

## 11. Drone / UAV photogrammetry

The single most useful EO technique at construction-site scale, because it produces **centimetre** data on demand.

### Flight planning and GSD

```
GSD = (sensor_pixel_pitch_mm × flight_height_m × 1000) / focal_length_mm      [mm/px]

or equivalently

GSD = (sensor_width_mm × height_m) / (focal_length_mm × image_width_px)       [m/px]
```

**Worked example — DJI Mavic 3E / Phantom 4 RTK class camera** (1″ or 4/3 sensor, 20 MP, 5472 px wide, sensor width ≈ 13.2 mm, focal length ≈ 8.8 mm):

```
h = 60 m:  GSD = (13.2 × 60) / (8.8 × 5472) = 0.0164 m = 1.64 cm/px
h = 100 m: GSD = (13.2 × 100) / (8.8 × 5472) = 0.0274 m = 2.74 cm/px
h = 120 m: GSD = 3.29 cm/px
```

**Choose the height from the required GSD**, not the other way round:

| Deliverable | Target GSD | Height (13.2 mm / 8.8 mm / 5472 px) |
|---|---|---|
| Volume/stockpile survey | 2–3 cm | 75–110 m |
| Site plan, contours at 0.25 m | 1.5–2.5 cm | 55–90 m |
| Crack/defect inspection | 0.3–0.5 cm | 11–18 m |
| Large-area context orthomosaic | 5–8 cm | 180–290 m (check the legal ceiling) |

**Overlap.** 75–80% forward, 65–75% side is the working standard. Increase both over uniform surfaces (bare sand, water, uniform crops) where feature matching struggles — Namibian sandveld is exactly such a surface, and under-lapped flights over it produce holes. Consider a **cross-hatch** (double grid) flight and **oblique** camera angles (~15–20° off nadir) for anything with vertical structure.

**Flight practicalities:**
- Fly near solar noon to minimise shadow length, but avoid direct hotspot glare on water.
- Avoid strong wind (affects overlap consistency) and rapidly changing cloud (radiometric inconsistency across the mosaic).
- Terrain-follow if relief exceeds ~10% of flight height, or GSD varies across the block.
- Log the camera calibration; do not mix cameras in one block.
- Check local aviation regulation before flying. **[NA]** UAV operation in Namibia is regulated by the Namibia Civil Aviation Authority — registration and operating requirements apply. `needs-verification` for current rules.

### Ground control points

GCPs are what convert a self-consistent 3D model into a *georeferenced, accurate* one.

- **Minimum 5** for a small square site: four near the corners, one in the centre. Add more for elongated sites, and one every ~100–150 m along the perimeter for larger blocks.
- Place them **on the ground, flat, visible from every direction**, with a high-contrast pattern and a well-defined centre. A 60 × 60 cm chequered target is legible at 3 cm GSD.
- Survey them with **RTK/PPK GNSS** or total station, in the CRS you intend to deliver in, and record **both** ellipsoidal and orthometric height with the geoid model used.
- Hold **2–3 as independent check points** — never used in the adjustment — so you can *measure* the accuracy rather than quote the software's internal residuals. Internal RMSE on GCPs used in the bundle adjustment is not an accuracy estimate.
- **RTK/PPK drones** (Phantom 4 RTK, Mavic 3 Enterprise RTK, WingtraOne) reduce GCP requirements dramatically but do **not** eliminate the need for check points, and they still deliver **ellipsoidal** heights unless the base is set up on a known orthometric mark.

### Software

| Tool | Note |
|---|---|
| **Agisoft Metashape** | Commercial, node-locked or floating; excellent quality, scriptable in Python. The pragmatic professional default |
| **Pix4Dmapper / PIX4Dmatic** | Commercial subscription; strong survey workflow, good reporting |
| **RealityCapture** | Very fast; strong for mixed aerial + terrestrial |
| **OpenDroneMap / WebODM** | **Open source.** Produces orthophoto, point cloud, textured 3D model, and **DSM/DTM**. WebODM adds a browser UI, project management and a tiled viewer. Docs cover GCP file format, recommended GCP practice and hardware requirements — RAM is the binding constraint |
| **ODM in the cloud** | WebODM Lightning, or run the Docker image on a rented GPU/large-RAM instance |

**OpenDroneMap GCP file** (`gcp_list.txt`) — the first line is the CRS as a PROJ string or EPSG, then one line per image observation:

```
EPSG:32733
664231.120 8055412.340 1148.221 2451 1832 DJI_0142.JPG gcp1
664231.120 8055412.340 1148.221 2103 1544 DJI_0143.JPG gcp1
664480.905 8055390.117 1147.884 1120 2210 DJI_0187.JPG gcp2
...
```

Columns: `easting northing elevation pixel_x pixel_y image_name [gcp_label]`. Each GCP wants **at least 3 image observations**, ideally 5+ from different angles.

```bash
# Run ODM in Docker on a project directory containing images/ and gcp_list.txt
docker run -ti --rm -v /data/site:/datasets/code opendronemap/odm \
  --project-path /datasets \
  --dsm --dtm \
  --orthophoto-resolution 2.0 \
  --dem-resolution 5.0 \
  --dem-gapfill-steps 4 \
  --pc-quality high \
  --feature-quality high \
  --min-num-features 12000 \
  --use-3dmesh \
  --cog

# Outputs land in /data/site/odm_orthophoto/, odm_dem/, odm_georeferencing/
```

Memory is the practical limit — budget roughly **1 GB of RAM per 15–25 images** at high quality for 20 MP imagery, and use `--split`/`--split-overlap` for large blocks.

### Post-processing chain

```bash
# 1. Reproject the orthomosaic into the delivery CRS and make it a COG
gdalwarp -t_srs EPSG:32733 -r cubic -of COG \
  -co COMPRESS=JPEG -co QUALITY=90 -co BLOCKSIZE=512 \
  odm_orthophoto.tif ortho_utm33s_cog.tif

# 2. Convert the DSM from ellipsoidal to orthometric height (EGM2008)
export PROJ_NETWORK=ON
gdalwarp -s_srs EPSG:4979 -t_srs "EPSG:32733+3855" dsm_ellipsoidal.tif dsm_ortho.tif

# 3. Contours at 0.25 m for a site plan
gdal_contour -a elev -i 0.25 dtm_ortho.tif contours_025.gpkg -f GPKG

# 4. Measure accuracy against the independent check points
#    (compare surveyed CP heights to raster values; report RMSE and 95th percentile)
gdallocationinfo -valonly -geoloc dtm_ortho.tif 664231.12 8055412.34
```

## Sources

- [Sentinel-2 mission](https://sentiwiki.copernicus.eu/web/s2-mission) — ESA SentiWiki, accessed 2026-08-25
- [STAC specification](https://stacspec.org/en) — STAC community, accessed 2026-08-25
- [OpenDroneMap documentation](https://docs.opendronemap.org/) — accessed 2026-08-25
- [Copernicus DEM collection description](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM) — accessed 2026-08-25

## Open questions

- Sentinel-2 constellation status changes: 2A was in an extension campaign as of March 2025 per SentiWiki. Verify which satellites are nominal before quoting revisit.
- **[NA]** Current Namibia Civil Aviation Authority UAV registration and operating rules (altitude ceiling, BVLOS, permits, insurance) were not retrieved. `needs-verification` before flying commercially.
- Sensor dimensions used in the GSD worked example are representative of the DJI 1″/20 MP class; confirm the exact sensor width, focal length and image width from the specific aircraft's specification sheet before planning a survey.
- ODM RAM guidance is an operational rule of thumb, not a figure quoted from the documentation.
- Google Earth Engine's current commercial licensing thresholds were not verified.
