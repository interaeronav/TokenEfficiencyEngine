---
id: cartography.data
title: Geospatial data sources, formats and licensing
domain: 23_cartography_and_mapping
tags: [openstreetmap, overture, sentinel, landsat, copernicus-dem, srtm, geopackage, geoparquet, cog, pmtiles, stac, licensing, resale, namibia, south-africa]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "OpenStreetMap copyright and licence", url: "https://www.openstreetmap.org/copyright", publisher: "OpenStreetMap Foundation", accessed: 2026-08-25}
  - {title: "Overture Maps attribution and licensing", url: "https://docs.overturemaps.org/attribution/", publisher: "Overture Maps Foundation", accessed: 2026-08-25}
  - {title: "Copernicus DEM collection description", url: "https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM", publisher: "Copernicus Data Space Ecosystem", accessed: 2026-08-25}
  - {title: "Sentinel-2 mission", url: "https://sentiwiki.copernicus.eu/web/s2-mission", publisher: "ESA SentiWiki", accessed: 2026-08-25}
  - {title: "Natural Earth terms of use", url: "https://www.naturalearthdata.com/about/terms-of-use/", publisher: "Natural Earth", accessed: 2026-08-25}
  - {title: "GeoNames about", url: "https://www.geonames.org/about.html", publisher: "GeoNames", accessed: 2026-08-25}
  - {title: "ALOS World 3D-30m", url: "https://www.eorc.jaxa.jp/ALOS/en/dataset/aw3d30/aw3d30_e.htm", publisher: "JAXA EORC", accessed: 2026-08-25}
  - {title: "GeoParquet", url: "https://geoparquet.org/", publisher: "OGC / GeoParquet contributors", accessed: 2026-08-25}
  - {title: "GDAL FlatGeobuf driver", url: "https://gdal.org/en/stable/drivers/vector/flatgeobuf.html", publisher: "GDAL contributors", accessed: 2026-08-25}
  - {title: "STAC specification", url: "https://stacspec.org/en", publisher: "STAC community", accessed: 2026-08-25}
  - {title: "PMTiles documentation", url: "https://docs.protomaps.com/pmtiles/", publisher: "Protomaps", accessed: 2026-08-25}
related: [cartography.geodesy, cartography.software, cartography.web, cartography.remote_sensing, cartography.namibia]
licence: mixed — see per-source table
unit_system: SI
---

# Geospatial data sources, formats and licensing

**Summary.** Two questions decide whether a dataset is usable: *is it accurate enough* and *are you allowed to do what you intend with it*. The second question is the one that ends projects. This file catalogues the major global and southern African sources with their licences and — critically — their **resale and sublicensing** position, then covers the formats, why Shapefile must be retired, and what has replaced it. The single most expensive mistake in commercial geospatial work is building a product on **ODbL** data and discovering at the point of sale that share-alike attaches to the database you are selling.

## Key facts

| Source | Licence | Commercial use | Redistribution | Sublicensable | Share-alike |
|---|---|---|---|---|---|
| **OpenStreetMap** | **ODbL 1.0** (data); CC BY-SA 2.0 (docs) | Yes | Yes | Yes | **YES — poisons derivative databases** |
| **Overture — base, buildings, divisions, transportation** | **ODbL** ("© OpenStreetMap contributors") | Yes | Yes | Yes | **YES** |
| **Overture — places** | **CDLA-Permissive 2.0** (plus Foursquare Apache 2.0, AllThePlaces CC0) | Yes | Yes | Yes | No |
| **Overture — addresses** | Varies by country; permissive open licences (CC BY 4.0, CC0, OGL variants) | Yes | Yes | Varies | Check per country |
| **Natural Earth** | **Public domain** | Yes | Yes | Yes | No |
| **GeoNames** | **CC BY 4.0** | Yes | Yes | Yes | No |
| **Sentinel-1/2/3** (Copernicus) | Free, full and open Copernicus terms | Yes | Yes | Yes | No (attribution required) |
| **Landsat** (USGS) | US Government work — public domain | Yes | Yes | Yes | No |
| **Copernicus DEM GLO-30/GLO-90** | Copernicus WorldDEM licence — free | Yes | Yes | Yes (with flow-down) | No, but **attribution chain is mandatory** |
| **SRTM** (NASA/USGS) | Public domain | Yes | Yes | Yes | No |
| **ASTER GDEM v3** | NASA/METI — free, citation required | Yes | Yes | Yes | No |
| **ALOS AW3D30** (JAXA) | Free of charge, **commercial and non-commercial** permitted under JAXA terms | Yes | Yes | Check terms | No |
| **GEDTM30** | **CC BY 4.0**, plus inherited Copernicus notice | Yes | Yes | Yes | No |
| **FABDEM** | **CC BY-NC-SA 4.0** | **NO** | — | — | Yes |
| **Planet, Maxar/Vantor, Airbus, ICEYE, Umbra** | Commercial EULA, per-scene or per-km² | Per contract | Usually **restricted** | Usually **NO** | — |

> ⚠️ **The ODbL trap.** ODbL's share-alike attaches to a *derivative database*. If you build a product database that incorporates OSM or Overture transportation/buildings, and you distribute that database, you must distribute it under ODbL. Producing a *Produced Work* (a rendered map image, a PDF) from ODbL data does **not** trigger share-alike on the produced work — but it does require attribution and a statement that the underlying data is ODbL. Getting this distinction right is the difference between a sellable product and an unsellable one. This is a lawyer question at the point of sale, not a wiki question.

## 1. Vector base data

### OpenStreetMap

The single most important open geospatial dataset. Global, crowd-sourced, continuously updated, with wildly variable completeness — excellent in European cities, thin in rural Namibia but improving, and the Humanitarian OpenStreetMap Team (HOT) has driven substantial coverage in southern Africa.

**Licence:** **ODbL 1.0** for the data. You may copy, distribute, transmit and adapt it, provided you credit "© OpenStreetMap contributors" and that any *adapted database* you distribute is under the same licence. Tiles from openstreetmap.org are subject to a separate **Tile Usage Policy** and are explicitly not a free API for third parties.

**How to get it:**
```bash
# Regional extracts — the normal route
wget https://download.geofabrik.de/africa/namibia-latest.osm.pbf

# Filter and convert with osmium (fast, correct)
osmium tags-filter namibia-latest.osm.pbf \
       w/highway w/waterway n/place -o namibia-core.osm.pbf
ogr2ogr -f GPKG namibia.gpkg namibia-core.osm.pbf lines points

# Or query small areas live via the Overpass API
curl -G https://overpass-api.de/api/interpreter \
  --data-urlencode 'data=[out:json][timeout:60];
    (way["highway"](-17.7,17.1,-17.4,17.4););
    out geom;' > roads.json
```

Other routes: **Protomaps**' daily OSM basemap builds, **Geofabrik** shapefile/PBF extracts, **BBBike** custom extracts, and **Overture** (which re-packages OSM plus other sources into stable-ID Parquet).

### Overture Maps Foundation

A Linux Foundation joint-development project (Amazon, Meta, Microsoft, TomTom and others) publishing an open, schema-stable, ID-stable global map dataset in **GeoParquet**, on a monthly release cycle.

**Latest release at time of writing: `2026-08-19.0`.** Themes: **addresses, base, buildings, divisions, places, transportation**.

```bash
# List available releases
aws s3 ls --no-sign-request s3://overturemaps-us-west-2/release/

# Download a theme partition
aws s3 cp --no-sign-request --recursive \
  s3://overturemaps-us-west-2/release/2026-08-19.0/theme=places/ ./places/

# Or query directly with DuckDB — no download of the whole planet
duckdb -c "
INSTALL spatial; LOAD spatial;
INSTALL httpfs;  LOAD httpfs;
SET s3_region='us-west-2';
COPY (
  SELECT id, names.primary AS name, categories.primary AS category,
         ST_AsText(ST_GeomFromWKB(geometry)) AS wkt
  FROM read_parquet('s3://overturemaps-us-west-2/release/2026-08-19.0/theme=places/type=place/*',
                    filename=true, hive_partitioning=1)
  WHERE bbox.xmin BETWEEN 11.5 AND 25.5
    AND bbox.ymin BETWEEN -29.0 AND -16.9
) TO 'namibia_places.csv' (HEADER, DELIMITER ',');
"
```

The `bbox` struct is a materialised bounding box column that lets the Parquet reader skip row groups — this is what makes a continent-scale query run on a laptop.

**Licence, theme by theme** (this is the thing to know): base, buildings, divisions and transportation are **ODbL** and require "© OpenStreetMap contributors"; **places is CDLA-Permissive 2.0** (with Foursquare content under Apache 2.0 and AllThePlaces under CC0); addresses varies by country. General citation: "Overture Maps Foundation, overturemaps.org".

For a *commercial, resellable* product, **places and divisions are usable; buildings and transportation are not**, without accepting ODbL on your own database.

### Natural Earth

Public-domain vector and raster at **1:10m, 1:50m and 1:110m**, curated for small-scale mapping. Countries, states, populated places, roads, rivers, lakes, bathymetry, shaded relief, land cover rasters. Explicitly public domain: no permission needed, commercial use and resale permitted, credit optional.

This is the correct base for any world or national overview map, and the only major vector source with **no** licence encumbrance whatsoever.

### GeoNames

Over **25 million geographical names** covering **12 million unique features** (4.8 million populated places, 16 million alternate names), in nine feature classes and 645 subcategories, WGS84. Free daily database dumps and free web services. **CC BY 4.0.**

Use it for gazetteer lookups, place-name reconciliation and multilingual naming. Positional accuracy is variable — GeoNames is a *names* database, not a survey.

### National mapping agencies

| Agency | Country | Products |
|---|---|---|
| **Directorate of Survey and Mapping**, under the ministry responsible for land (**[NA]**) | Namibia | National topographic map series, orthophotos, geodetic control, and (with the Surveyor-General) the cadastral record. The Surveyor-General approves survey diagrams and general plans under the **Land Survey Act 33 of 1993** |
| **Chief Directorate: National Geo-spatial Information (CD:NGI)**, Dept of Agriculture, Land Reform and Rural Development (**[ZA]**) | South Africa | The national mapping agency, formerly Chief Directorate: Surveys and Mapping. Topographic map series, orthophotography, aerial imagery, geodetic control (TrigNet CORS network) |
| Ordnance Survey (UK), IGN (FR), USGS (US), swisstopo (CH) | — | The reference examples of open (USGS, and increasingly IGN) vs commercial (OS) national data policy |

> **[NA]** The Namibian Directorate of Survey and Mapping's current product catalogue, scales, pricing and licensing could **not be retrieved** during this research — the ministry website was unreachable. Treat the description above as structural and verify specifics directly. `needs-verification`.

## 2. Satellite imagery

| Mission | Resolution | Revisit | Bands | Cost | Licence |
|---|---|---|---|---|---|
| **Sentinel-2** (A/B/C) | **10 m** (B2,B3,B4,B8), **20 m** (B5–B7, B8A, B11, B12), **60 m** (B1, B9, B10) | **5 days at the equator** (constellation), 290 km swath, 56°S–82.8°N | 13 MSI bands, 442–2202 nm | Free | Copernicus open — attribution |
| **Landsat 8/9 OLI-TIRS** | 30 m multispectral, 15 m panchromatic, 100 m thermal | 16 days per satellite, 8 days combined | 11 bands | Free | Public domain |
| **Landsat 1–7 archive** | 30–80 m | — | — | Free | Public domain; the 1972-onward archive is the longest continuous record |
| **Planet PlanetScope** | ~3–5 m | ~daily | 4–8 bands | Commercial subscription | Restrictive EULA; limited redistribution |
| **Planet SkySat** | ~0.5–0.8 m | tasked | 4 bands + pan | Commercial | Restrictive |
| **Maxar / Vantor (WorldView, GeoEye)** | **0.3–0.5 m** | tasked | pan + 4/8 bands + SWIR | Commercial, high | Restrictive; per-seat and per-use terms |
| **Airbus Pléiades / Pléiades Neo** | 0.5 m / 0.3 m | tasked | pan + 4/6 bands | Commercial | Restrictive |
| **ICEYE, Umbra, Capella** (SAR) | 0.25–1 m SAR | tasked, all-weather, night | X-band SAR | Commercial | Restrictive |
| **NASA/USGS ASTER, MODIS, VIIRS** | 15–1000 m | daily to 16-day | multi/hyper | Free | Public domain / open |

### SkyFi

**SkyFi** is a self-service Earth-intelligence marketplace aggregating **40+ imagery providers** (including Vantor, Planet, ICEYE US, Umbra, Satellogic), with archive, tasking and built-in analytics, sold without contracts. Published entry pricing: **archive imagery from around $15**, **new tasking from around $200**, with Vantor optical at **30–50 cm**; some open data is free. Access is via web app, mobile app or API.

> ⚠️ **SkyFi does not change the underlying licence.** What you buy is a licence from the *originating operator*, passed through. Whether you may publish the image in a submission document, redistribute it, or sell a derived product depends on that operator's EULA, not on SkyFi's checkout page. For a building submission this usually matters little (internal/regulatory use); for anything you intend to resell or publish widely, **read the specific EULA attached to the order**. SkyFi's public site does not state redistribution terms — `needs-verification` per purchase.

## 3. Elevation data

| Product | Resolution | Surface | Vertical datum | Accuracy | Licence |
|---|---|---|---|---|---|
| **SRTM v3 (SRTM Plus)** | 1″ (~30 m) / 3″ | DSM | **EGM96** | ~16 m LE90 (spec); typically much better | Public domain |
| **ASTER GDEM v3** | 1″ | DSM | EGM96 | Noisier than SRTM; artefacts | Free, citation required |
| **Copernicus DEM GLO-30** | **1″ (~31 m)** | **DSM** (canopy + buildings) | **EGM2008** | **< 4 m vertical LE90**, ~6 m horizontal CE90 | Free; **attribution chain mandatory**; resale and sublicensing permitted with flow-down |
| **Copernicus DEM GLO-90** | 3″ (~93 m) | DSM | EGM2008 | < 4 m LE90 | Same |
| **ALOS AW3D30** | 1″ (~30 m) | DSM | height above sea level | comparable to Copernicus | Free, **commercial use permitted** under JAXA terms; v4.1 global (2025), 23 993 tiles |
| **GEDTM30** | 1″ | **DTM (bare earth)** | EGM2008 | ~3 m (provisional), ships a **per-pixel uncertainty band** | **CC BY 4.0** + inherited Copernicus notice. Coverage 83.7°N to 62.0°S |
| **FABDEM** | 1″ | DTM (forest/building removed) | EGM2008 | better than Copernicus in forest | **CC BY-NC-SA 4.0 — non-commercial AND share-alike. Unusable in a commercial product** |
| **National lidar** (USGS 3DEP, IGN LiDAR HD, UK EA, etc.) | 0.3–1 m | DTM + DSM | national vertical datum | 0.1–0.6 m | Varies: 3DEP public domain, IGN Licence Ouverte 2.0, others bespoke |

**For Namibia**, the practical elevation stack is:
1. **Copernicus DEM GLO-30** as the general-purpose base (best free global DSM, clean licence, EGM2008).
2. **GEDTM30** where bare-earth matters — but note Namibia's sparse canopy means the DSM/DTM difference is small outside riparian woodland and settlements.
3. **Drone photogrammetry or RTK GNSS** for anything at site scale. A 30 m DEM is worthless for cut/fill on a building plot; see `08` and `10`.

> ⚠️ There is **no free national lidar programme for Namibia** known at time of writing. Site-scale terrain must be surveyed. `needs-verification`.

```bash
# Copernicus GLO-30 tiles are individually addressable on S3
TILE=Copernicus_DSM_COG_10_S18_00_E017_00_DEM
curl -O "https://copernicus-dem-30m.s3.amazonaws.com/${TILE}/${TILE}.tif"

# Or pull a mosaic for an AOI straight out of a STAC catalogue
gdalwarp -te 17.0 -17.8 17.5 -17.3 -te_srs EPSG:4326 \
  -t_srs EPSG:32733 -tr 30 30 -r bilinear -of COG \
  /vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/${TILE}/${TILE}.tif \
  okongo_dem_utm33s.tif
```

## 4. Land cover and thematic global products

| Product | Resolution | Epoch | Licence |
|---|---|---|---|
| **ESA WorldCover** | 10 m | 2020, 2021 | CC BY 4.0 |
| **ESRI Land Cover (Sentinel-2, 10 m)** | 10 m | annual | CC BY 4.0 |
| **Copernicus Global Land Cover** | 100 m | annual 2015–2019 | CC BY 4.0 |
| **Dynamic World** (Google/WRI) | 10 m | near-real-time | CC BY 4.0 |
| **Global Forest Change** (Hansen) | 30 m | annual since 2000 | CC BY 4.0 |
| **JRC Global Surface Water** | 30 m | 1984–present | Copernicus open |
| **WorldPop** | 100 m / 1 km | annual | CC BY 4.0 |
| **GHSL** (Global Human Settlement Layer, JRC) | 10 m–1 km | multi-epoch | Copernicus open |

WorldCover, Dynamic World and GHSL are the three most useful for a Namibian context map: land cover, built-up extent and settlement density without needing to digitise anything.

## 5. Formats

### Vector

| Format | Verdict | Why |
|---|---|---|
| **Shapefile (.shp)** | **Stop using it** | See below |
| **GeoPackage (.gpkg)** | **The default for files** | Single SQLite file, multiple layers, rasters too, no name limits, full UTF-8, real spatial index, arbitrary geometry types, 140 TB theoretical limit. An OGC standard |
| **GeoJSON (.geojson)** | Interchange and web | Human-readable, universally supported. **Spec mandates WGS 84 lon/lat (RFC 7946)**. Verbose; no index; do not use for big data |
| **TopoJSON** | Web, topology-preserving | Encodes shared arcs once — 80%+ smaller than GeoJSON for administrative boundaries, and simplification cannot create gaps between neighbours |
| **FlatGeobuf (.fgb)** | Streaming and cloud | Binary FlatBuffers, **Hilbert R-tree spatial index** (`SPATIAL_INDEX=YES`, default), supports HTTP range requests so a client can read a bbox from a remote file. One layer per file. GDAL driver since 3.1 |
| **GeoParquet** | **Analytics at scale** | Columnar, compressed, predicate-pushdown. **Currently v2.0.0-rc.1**, an incubating OGC standard. Read by DuckDB, GeoPandas, Sedona, BigQuery, Snowflake, QGIS, ArcGIS Pro. This is what Overture ships |
| **PostGIS / PostgreSQL** | The database answer | Not a file format; the right home for anything queried repeatedly |
| **DXF / DWG** | Interoperating with CAD | Carries no CRS reliably. Always agree the CRS out-of-band with the engineer or architect |
| **KML / KMZ** | Google Earth, field sharing | WGS 84 only; styling embedded; fine for delivery, poor for analysis |

**Why Shapefile must be retired**, concretely:

1. **Attribute names limited to 10 characters** — `population_density` becomes `populati_1`.
2. **2 GB limit** per component file.
3. **255 attribute columns** maximum.
4. **No native UTF-8 guarantee** — the DBF encoding is declared in an optional `.cpg` file that is routinely missing, so non-ASCII names (Oshiwambo, Khoekhoegowab, Afrikaans diacritics) corrupt silently.
5. **Multi-file** — `.shp .shx .dbf .prj .cpg .sbn .sbx`. Lose the `.prj` and the CRS is gone.
6. **No null values** in numeric fields — 0 and "no data" are indistinguishable.
7. **Dates but no datetimes**; no boolean type.
8. **Mixed geometry types not allowed** in one layer.
9. **No topology, no curves, no measures beyond a limited Z/M model.**

```bash
# The one-line fix
ogr2ogr -f GPKG data.gpkg data.shp

# Bulk-convert a directory
for f in *.shp; do ogr2ogr -f GPKG "${f%.shp}.gpkg" "$f"; done
```

### Raster

| Format | Use |
|---|---|
| **GeoTIFF** | The universal raster. TIFF plus georeferencing tags |
| **Cloud-Optimized GeoTIFF (COG)** | GeoTIFF with internal tiling + overviews arranged so an HTTP range request fetches only the needed bytes. **The default for anything served over a network.** Now a formal OGC standard |
| **NetCDF / HDF5** | Multidimensional scientific arrays — climate, ocean, time series with named dimensions and CF conventions |
| **Zarr / GeoZarr** | Chunked, compressed N-dimensional arrays designed for object storage. The cloud-native successor to NetCDF for large time-series cubes |
| **JPEG2000** | Sentinel-2 native delivery format. Efficient, slow to decode |
| **MBTiles** | SQLite container of raster or vector tiles. Superseded for web use by PMTiles |
| **ERDAS IMG, ENVI .hdr** | Legacy remote-sensing formats; convert on ingest |

```bash
# Make a COG (GDAL >= 3.1 has a dedicated driver)
gdal_translate input.tif output_cog.tif \
  -of COG -co COMPRESS=DEFLATE -co PREDICTOR=2 \
  -co BLOCKSIZE=512 -co OVERVIEW_RESAMPLING=AVERAGE

# Validate it
python -m rio_cogeo validate output_cog.tif      # rio-cogeo
gdalinfo output_cog.tif | grep -i overview
```

### Point clouds

| Format | Use |
|---|---|
| **LAS** | The ASPRS standard point-cloud exchange format. Uncompressed |
| **LAZ** | Losslessly compressed LAS — typically 5–10× smaller. The practical default |
| **COPC (Cloud-Optimized Point Cloud)** | LAZ reorganised into a clustered octree so a client can range-request a spatial subset or a level of detail. The point-cloud equivalent of COG |
| **E57** | Terrestrial laser scanning exchange (includes imagery and scan positions) |
| **PLY / OBJ / glTF** | Mesh formats for the downstream 3D model |

### Tiles

| Format | Use |
|---|---|
| **XYZ / TMS raster tiles** | Directory or URL template of PNG/JPEG/WebP tiles. Simple, huge on disk |
| **MVT (Mapbox Vector Tile)** | Protobuf-encoded, clipped, simplified vector geometry per tile. The vector-tile standard; an OGC standard |
| **PMTiles** | **Single-file archive** of a tile pyramid (raster, vector or images), read by **HTTP range request** — no tile server needed. Spec **version 3**. Read-only: updating means rewriting the archive. Supported by MapLibre GL JS (recommended), Leaflet, OpenLayers, a Python package on PyPI, and community Dart/Kotlin/Rust implementations. Browser viewer/debugger at pmtiles.io |

## 6. Catalogues and services

### STAC (SpatioTemporal Asset Catalog)

A JSON convention for describing geospatial assets so they can be indexed and searched. Four parts:

- **Item** — the atomic unit: a GeoJSON Feature with temporal metadata and links to assets (the actual COGs).
- **Catalog** — a linked JSON tree for browsing.
- **Collection** — a Catalog plus extents, licence, keywords, providers.
- **STAC API** — a RESTful search endpoint specified in OpenAPI, aligned with OGC API - Features.

Extensions add domain metadata (the **EO extension** for bands and cloud cover; also `proj`, `raster`, `view`, `sar`, `ml-model`).

```python
from pystac_client import Client

cat = Client.open("https://earth-search.aws.element84.com/v1")
search = cat.search(
    collections=["sentinel-2-l2a"],
    bbox=[17.0, -17.8, 17.5, -17.3],       # Okongo area
    datetime="2026-04-01/2026-06-30",
    query={"eo:cloud_cover": {"lt": 10}},
)
items = sorted(search.items(), key=lambda i: i.properties["eo:cloud_cover"])
best = items[0]
print(best.id, best.properties["eo:cloud_cover"])
print(best.assets["red"].href)   # a COG URL — stream it, do not download the scene
```

### OGC web services

| Service | Serves | Note |
|---|---|---|
| **WMS** | Rendered map images | Server does the styling. Slow, flexible, ubiquitous |
| **WMTS** | Pre-rendered tiles | Cacheable, fast, fixed styling |
| **WFS** | Vector features | Returns real geometry; `WFS 2.0` is verbose XML |
| **WCS** | Raster coverages | Subsettable raster download |
| **OGC API — Features / Tiles / Coverages / Maps / Records** | The modern JSON+OpenAPI replacements | `OGC API - Features` Part 1 is what STAC API aligns with |

```bash
# Read a WFS layer straight into GeoPackage
ogr2ogr -f GPKG parcels.gpkg \
  "WFS:https://example.gov/geoserver/wfs?version=2.0.0" parcels

# Use a WMTS as a GDAL raster source
gdal_translate "WMTS:https://example.org/wmts?layer=orthophoto" ortho.tif
```

## 7. A licence-clearance checklist

Before a source enters production, answer these six in writing and quote the operative clause. (This is the discipline the terrain-basemap workflow enforces mechanically, and it is right.)

1. Is **commercial use** permitted?
2. Is **redistribution** permitted?
3. Is **sublicensing** permitted — can your customer redistribute?
4. Are there **share-alike / copyleft** obligations?
5. What **attribution** must flow downstream, in exactly what wording?
6. What **liability text** must flow downstream?

Get the licence text itself, not a data-portal summary. **Any "unclear" is a fail** until resolved. And keep the determinations in a machine-readable registry so the build can enforce them, rather than in a document nobody re-reads.

For Copernicus DEM, the required downstream notice is:

> © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.

and, where you have modified it:

> produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.

## Sources

- [OpenStreetMap copyright](https://www.openstreetmap.org/copyright) — OSMF, accessed 2026-08-25
- [Overture attribution and licensing](https://docs.overturemaps.org/attribution/) — Overture Maps Foundation, accessed 2026-08-25
- [Overture release listing (S3)](https://overturemaps-us-west-2.s3.us-west-2.amazonaws.com/?list-type=2&delimiter=/&prefix=release/) — accessed 2026-08-25 (release 2026-08-19.0, six themes)
- [Copernicus DEM collection description](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM) — accessed 2026-08-25
- [Sentinel-2 mission](https://sentiwiki.copernicus.eu/web/s2-mission) — ESA SentiWiki, accessed 2026-08-25
- [Natural Earth terms of use](https://www.naturalearthdata.com/about/terms-of-use/) — accessed 2026-08-25
- [GeoNames](https://www.geonames.org/about.html) — accessed 2026-08-25
- [ALOS World 3D-30m](https://www.eorc.jaxa.jp/ALOS/en/dataset/aw3d30/aw3d30_e.htm) — JAXA EORC, accessed 2026-08-25
- [GeoParquet](https://geoparquet.org/) — accessed 2026-08-25
- [GDAL FlatGeobuf driver](https://gdal.org/en/stable/drivers/vector/flatgeobuf.html) — accessed 2026-08-25
- [STAC](https://stacspec.org/en) — accessed 2026-08-25
- [PMTiles documentation](https://docs.protomaps.com/pmtiles/) — Protomaps, accessed 2026-08-25
- [SkyFi](https://skyfi.com/) — accessed 2026-08-25

## Open questions

- **[NA]** Directorate of Survey and Mapping product catalogue, scales, pricing and data licence — site unreachable. `needs-verification`.
- **[ZA]** CD:NGI's current data policy (open vs cost-recovery) and product list — the Wikipedia entry confirms its identity but not its terms.
- SkyFi's per-order redistribution terms; these are set by the originating operator's EULA and must be read per purchase.
- Whether GEDTM30's current COG endpoint is the OpenLandMap STAC or a Zenodo record — the GitHub repository has moved to Codeberg.
- ASTER GDEM v3's exact citation requirement wording.

