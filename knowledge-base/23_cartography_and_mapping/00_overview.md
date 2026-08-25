---
id: cartography.overview
title: Cartography and mapping — overview
domain: 23_cartography_and_mapping
tags: [cartography, gis, geodesy, geoinformatics, remote-sensing, mapping, spatial-data, overview]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "International Cartographic Association", url: "https://icaci.org/", publisher: "ICA", accessed: 2026-08-25}
  - {title: "EPSG Geodetic Parameter Dataset API", url: "https://apps.epsg.org/api/v1/CoordRefSystem/?keywords=Schwarzeck", publisher: "IOGP Geomatics Committee", accessed: 2026-08-25}
  - {title: "Programmes", url: "https://www.nust.na/programmes", publisher: "Namibia University of Science and Technology", accessed: 2026-08-25}
  - {title: "Study Finder", url: "https://www.utwente.nl/en/itc/education/study-finder/", publisher: "ITC, University of Twente", accessed: 2026-08-25}
  - {title: "Overture Maps Foundation", url: "https://overturemaps.org/", publisher: "Overture Maps Foundation / Linux Foundation", accessed: 2026-08-25}
  - {title: "Cloud-Native Geospatial Forum", url: "https://cloudnativegeo.org/", publisher: "Radiant Earth", accessed: 2026-08-25}
related: [cartography.career, cartography.geodesy, cartography.design, cartography.data, cartography.software, cartography.web, cartography.remote_sensing, cartography.terrain, cartography.trends, cartography.namibia, cartography.resources]
unit_system: SI
---

# Cartography and mapping — overview

**Summary.** Cartography is no longer a drawing discipline with a surveying appendix; it is a data-engineering discipline with a design conscience. A working practitioner today moves between five overlapping fields — **geodesy** (where things actually are, on a curved, lumpy, moving Earth), **GIS / spatial data science** (how spatial data is stored, queried and analysed), **cartographic design** (how a map communicates without lying), **geoinformatics / geospatial software engineering** (the pipelines, tiles, APIs and services), and **remote sensing / Earth observation** (how the raw observations are made). This domain covers all five, the education and registration route into them, and the applied southern African case — with particular attention to Namibia, where the **Schwarzeck datum on the Bessel Namibia ellipsoid in German Legal Metres** and the **Lo22/xx belts with west/south axes** trap almost everyone the first time.

## Key facts

| Fact | Value | Note |
|---|---|---|
| Governing international body for cartography | **International Cartographic Association (ICA)**, founded **1959** | Runs the biennial International Cartographic Conference; next **ICC 2027, Warsaw, 18–23 July 2027** |
| Governing body for surveying | **FIG** (Fédération Internationale des Géomètres) | Ten technical commissions |
| Governing body for photogrammetry / remote sensing | **ISPRS** | Congress every 4 years |
| Web-map de-facto projection | **EPSG:3857** "WGS 84 / Pseudo-Mercator" | Spherical maths on an ellipsoidal datum; not conformal in the strict sense |
| Global geographic CRS | **EPSG:4326** (WGS 84, lat/lon) | Axis order lat,lon in the authority definition — a perennial bug source |
| **[NA]** Namibian legacy datum | **Schwarzeck**, EPSG:4293, ellipsoid *Bessel Namibia (GLM)* EPSG:7046 | a = 6 377 397.155 **German Legal Metres** = 6 377 483.865 international m |
| **[NA]** Namibian projected grids | **Schwarzeck / Lo22/11 … Lo22/25**, EPSG:**29371, 29373, 29375, 29377, 29379, 29381, 29383, 29385** | Axes **westing, southing**; units **German Legal Metre** |
| **[ZA]** South African modern datum | **Hartebeesthoek94**, EPSG:4148 (2D), 4941 (3D), 4940 (geocentric) | Coincident with ITRF91 at epoch 1994.0 |
| **[ZA]** South African projected grids | **Hartebeesthoek94 / Lo15 … Lo33**, EPSG:2046–2055 | Axes westing, southing; metres |
| Current QGIS | **4.2.1 "Belém do Pará"** (2026-07-31); LTR **3.44.13 "Solothurn"** | qgis.org/download |
| Latest Overture Maps release | **2026-08-19.0** | `s3://overturemaps-us-west-2/release/2026-08-19.0/` |
| Copernicus DEM GLO-30 | 1 arc-second, WGS84-G1150 / **EGM2008**, **< 4 m vertical LE90** | TanDEM-X 2011–2015 |

> ⚠️ Every metre-accurate decision in Namibia depends on knowing whether a coordinate is on **Schwarzeck** or on **WGS 84 / ITRF**. The offset is roughly **300–400 m** in plan. A site plan drawn in the wrong datum will look perfectly plausible and be catastrophically wrong. See `02_geodesy-and-coordinate-systems.md`.

## What cartography is today

The classical definition — "the art, science and technology of making and using maps" — survives, but the practice behind it has been reorganised twice in thirty years.

**The first reorganisation** was the collapse of the map as an artefact into the map as a *view over a database*. Until roughly the mid-1990s, a topographic map sheet was the primary data product: the compilation, the generalisation and the symbolisation were baked into one immutable engraving. Today the primary product is a **spatial database** with an attached **style**, and the printed or screen map is one rendering of it. This is why a modern cartographer spends more time in SQL and style specifications than in a drawing package, and why "cartographic design" has migrated into **code** — MapLibre style JSON, QGIS QML, CartoCSS, deck.gl layer configs (see `09_latest-trends.md`).

**The second reorganisation**, still under way, is the move of the whole stack to **cloud-native, object-store-backed formats** that are queried by HTTP range request rather than downloaded: Cloud-Optimized GeoTIFF, STAC, GeoParquet, Zarr, PMTiles, COPC. The consequence for a small practice — including a one-person operation in Namibia — is that the entry cost to serious geospatial work has collapsed. A laptop, a browser and a free STAC endpoint now do what needed an institution in 2010.

## The five sub-fields and how they divide

### 1. Geodesy — the science of the Earth's shape, gravity field and rotation

Geodesy answers "where is this, to what accuracy, in which reference frame, at what epoch". It supplies the datums, ellipsoids, projections, geoid models and transformation parameters everything else depends on. It is unglamorous, mathematically demanding, and the single largest source of silent error in applied mapping. The practitioner-level subset is: ellipsoid vs geoid, datum vs coordinate reference system, projection distortion, EPSG codes, orthometric vs ellipsoidal height, and how to drive PROJ correctly.

Covered in `02_geodesy-and-coordinate-systems.md`.

### 2. GIS and spatial data science — storage, query, analysis

The relational and array models for spatial data: vector features with topology and attributes, raster grids, point clouds, networks. Spatial indexing (R-tree, quadtree, H3/S2 discrete global grids), spatial SQL (PostGIS, DuckDB spatial), overlay and buffer operations, network routing, geostatistics and interpolation, terrain analysis. This is the analytic engine room.

Covered in `05_gis-software-and-tooling.md` and `08_terrain-and-3d.md`.

### 3. Cartographic design — the communication craft

Visual hierarchy, figure-ground, generalisation, Bertin's visual variables, colour theory, typography and label placement, thematic map types and their failure modes, layout and relief representation. This is the part that cannot be automated away, because it is a set of judgements about what a specific reader needs to understand. It is also the part most often skipped, which is why so much output from otherwise competent GIS work is unreadable.

Covered in `03_map-design-and-cartographic-theory.md`.

### 4. Geoinformatics and geospatial software engineering

Data formats and their trade-offs, tiling schemes, web map clients, tile servers, OGC service standards (WMS/WMTS/WFS/OGC API), catalogues, pipelines and CI. In practice this is where most paid work now sits: building and operating the machinery that turns raw sources into maps and analyses on a schedule.

Covered in `04_data-sources-and-formats.md` and `06_web-and-interactive-mapping.md`.

### 5. Remote sensing and Earth observation

The physics of measuring the Earth from a distance — electromagnetic spectrum, spectral signatures, passive optical vs active radar and lidar, resolution trade-offs — and the practice of turning that into information: atmospheric correction, spectral indices, classification, change detection, InSAR deformation, and photogrammetry from drones. This is where the raw data enters the system.

Covered in `07_remote-sensing-and-earth-observation.md`.

## How the sub-fields interlock — a worked example

A single practical job, "produce a site plan and location map for a building submission in Okongo, Namibia", touches all five:

1. **Geodesy** — the plot corners come off a GNSS receiver in WGS 84 / ITRF. The Deeds Office and the surveyor-general's diagrams are on **Schwarzeck**. You must know which, and transform explicitly rather than letting software guess. Heights from GNSS are **ellipsoidal**; the building levels want **orthometric** heights, which needs a geoid model (EGM2008 or better).
2. **Remote sensing** — a drone flight at a planned ground sample distance gives an orthomosaic and a dense point cloud; or an archive Sentinel-2 / commercial scene gives the surrounding context.
3. **Terrain / 3D** — the point cloud is filtered to bare earth, gridded to a DTM, and contoured; cut and fill volumes come from differencing the existing surface against the design surface.
4. **GIS** — plot boundary, servitudes, setbacks, drainage lines and building footprint are held as vector layers, checked topologically, and analysed (areas, coverage ratio, distances to boundaries).
5. **Cartographic design** — the output is a **scaled** sheet with a correct scale bar, north arrow referenced to the right north (grid, true or magnetic — say which), a legend, a graticule or grid, a location inset, and a title block that names the CRS, the datum, the epoch and the source of every layer.

Skip any one of the five and the sheet is either wrong, unreadable, or rejected.

## Domain map — the files in this folder

| File | Covers | Read it when |
|---|---|---|
| `00_overview.md` | This map of the domain | Orienting |
| `01_becoming-a-cartographer.md` | Degrees, leading programmes, southern African route, professional registration (**[ZA]** SAGC, **[NA]** the Namibian Council), ICA/FIG/ISPRS/RICS, GISP, self-taught curriculum | Planning a career or hiring |
| `02_geodesy-and-coordinate-systems.md` | Geoid, ellipsoids, datums, transformations, projections, EPSG codes, vertical datums, PROJ pipelines. **The Namibian and South African systems in detail** | Before touching any coordinate |
| `03_map-design-and-cartographic-theory.md` | Visual hierarchy, generalisation, Bertin, typography, colour, thematic types, layout, relief, classic errors | Before drawing anything |
| `04_data-sources-and-formats.md` | OSM, national agencies, satellite imagery, DEMs, land cover, Natural Earth, Overture; Shapefile→GeoPackage, GeoJSON, FlatGeobuf, GeoParquet, COG, LAS/LAZ, MVT/PMTiles, STAC, OGC services. **Licensing and resale for each** | Sourcing data |
| `05_gis-software-and-tooling.md` | QGIS, ArcGIS, GRASS, SAGA, GDAL/OGR, PROJ, PostGIS, Python, R, web libraries, tile servers, Blender/Illustrator finishing | Building the toolchain |
| `06_web-and-interactive-mapping.md` | Tile schemes, vector tiles, style JSON, PMTiles, clustering, accessibility, basemap pricing, self-hosting, 3D | Publishing on the web |
| `07_remote-sensing-and-earth-observation.md` | Spectrum, sensors, resolution, correction, indices, SAR/InSAR, classification, GEE and Planetary Computer, UAV photogrammetry | Working from imagery |
| `08_terrain-and-3d.md` | DSM/DTM/DEM, accuracy, void filling, hydrological conditioning, derivatives, lidar and PDAL, heightmaps for Unreal and Blender, accuracy assessment | Working with elevation |
| `09_latest-trends.md` | Cloud-native geospatial, PMTiles, Overture, geospatial foundation models, SAM, digital twins, NewSpace SAR, PPP-RTK, design-as-code — **with hype flags** | Deciding what to adopt |
| `10_practical-projects-and-namibia.md` | Construction-site mapping end to end, site plans to scale, georeferencing scans, SkyFi imagery, Namibian base data, printable submission maps | Doing the actual job |
| `11_books-courses-and-resources.md` | Annotated register of books, courses, blogs, reference sites | Learning further |

## Vocabulary that must not be confused

- **Datum** vs **coordinate reference system (CRS)**: a datum fixes the ellipsoid and its position/orientation relative to the Earth; a CRS is a datum *plus* a coordinate system (geographic, or a projection with axes and units). `Schwarzeck` is a datum; `Schwarzeck / Lo22/17` (EPSG:29377) is a CRS.
- **Projection** vs **transformation**: a *projection* (map projection, a *conversion* in ISO 19111 terms) is exact and lossless in the mathematical sense — it moves between a geographic CRS and a projected CRS on the *same* datum. A *transformation* moves between *different* datums and is always empirical and approximate.
- **Accuracy** vs **precision**: a receiver reporting 8 decimal places is precise; whether it is accurate depends on the reference frame, the correction service and the multipath environment.
- **Resolution** vs **scale**: a 30 m raster has a resolution; a paper map has a scale. A screen map has neither in a stable sense — it has a **zoom level**.
- **DEM / DSM / DTM**: DEM is the umbrella term; DSM includes canopy and buildings; DTM is bare earth. Copernicus GLO-30 is a **DSM**; GEDTM30 is a **DTM**. Confusing them puts trees in your contours.
- **Geoid** vs **ellipsoid**: heights above the ellipsoid (from GNSS) and heights above the geoid (what water levels and builders care about) differ by the geoid undulation N, which in southern Africa is of the order of tens of metres and varies across a country.

## The honest position on where the work is

Paid cartography today is roughly: (a) geospatial data engineering and web map infrastructure, (b) surveying and cadastral work, which in both Namibia and South Africa is statutorily reserved to registered professionals, (c) remote sensing analytics for agriculture, mining, insurance and defence, (d) planning, environmental and infrastructure consultancy, and (e) a thin, prestigious layer of pure cartographic design. Anyone entering the field for the design should expect to earn from (a) or (c) and practise (e). Anyone entering for the surveying should note that **registration is the gate**, not the degree — see `01_becoming-a-cartographer.md`.

## Sources

- [International Cartographic Association](https://icaci.org/) — ICA, accessed 2026-08-25
- [EPSG Geodetic Parameter Dataset — Schwarzeck query](https://apps.epsg.org/api/v1/CoordRefSystem/?keywords=Schwarzeck) — IOGP, accessed 2026-08-25
- [EPSG Geodetic Parameter Dataset — Hartebeesthoek94 query](https://apps.epsg.org/api/v1/CoordRefSystem/?keywords=Hartebeesthoek94) — IOGP, accessed 2026-08-25
- [NUST Programmes](https://www.nust.na/programmes) — Namibia University of Science and Technology, accessed 2026-08-25
- [ITC Study Finder](https://www.utwente.nl/en/itc/education/study-finder/) — University of Twente ITC, accessed 2026-08-25
- [Overture Maps Foundation](https://overturemaps.org/) — accessed 2026-08-25
- [Overture release listing (S3)](https://overturemaps-us-west-2.s3.us-west-2.amazonaws.com/?list-type=2&delimiter=/&prefix=release/) — accessed 2026-08-25
- [QGIS download page](https://qgis.org/download/) — QGIS project, accessed 2026-08-25
- [Copernicus DEM collection description](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM) — Copernicus Data Space Ecosystem, accessed 2026-08-25
- [Cloud-Native Geospatial Forum](https://cloudnativegeo.org/) — Radiant Earth, accessed 2026-08-25

## Open questions

- The exact ICA commission list for the 2027–2031 term will change at the Warsaw General Assembly; the 2023–2027 list is the current one.
- Whether the **[NA]** Directorate of Survey and Mapping publishes an open national topographic dataset (as opposed to selling sheets) could not be confirmed — the ministry site was not reachable during research. Marked in `04` and `10` as needing verification.

