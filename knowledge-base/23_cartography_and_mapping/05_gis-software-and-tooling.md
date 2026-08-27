---
id: cartography.software
title: GIS software and the geospatial toolchain
domain: 23_cartography_and_mapping
tags: [qgis, arcgis, grass, saga, gdal, ogr, proj, postgis, geopandas, rasterio, sf, terra, tmap, leaflet, maplibre, deck-gl, cesium, tile-server, blender, inkscape]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "QGIS download", url: "https://qgis.org/download/", publisher: "QGIS project", accessed: 2026-08-25}
  - {title: "GDAL FlatGeobuf driver", url: "https://gdal.org/en/stable/drivers/vector/flatgeobuf.html", publisher: "GDAL contributors", accessed: 2026-08-25}
  - {title: "PROJ — Transverse Mercator", url: "https://proj.org/en/stable/operations/projections/tmerc.html", publisher: "PROJ contributors", accessed: 2026-08-25}
  - {title: "MapLibre Style Spec", url: "https://maplibre.org/maplibre-style-spec/", publisher: "MapLibre", accessed: 2026-08-25}
  - {title: "PMTiles documentation", url: "https://docs.protomaps.com/pmtiles/", publisher: "Protomaps", accessed: 2026-08-25}
related: [cartography.data, cartography.web, cartography.terrain, cartography.remote_sensing]
unit_system: SI
---

# GIS software and the geospatial toolchain

**Summary.** The open-source geospatial stack is now strictly more capable than the proprietary one for most work, and it is free. Underneath almost everything sit two libraries — **GDAL/OGR** (read, write, warp, translate) and **PROJ** (coordinate transformation). Above them: **QGIS** for desktop and layout, **PostGIS** for the database, **Python** (GeoPandas / Rasterio / xarray) or **R** (sf / terra) for analysis, **MapLibre / Leaflet / deck.gl** for the web, and **Blender / Inkscape** for the finishing that GIS packages do badly. This file gives the practical shape of that stack with commands and code that run.

## Key facts

| Tool | Current version / status | Licence |
|---|---|---|
| **QGIS** | Latest release **4.2.1 "Belém do Pará"** (2026-07-31); **LTR 3.44.13 "Solothurn"** | GPL |
| **GDAL/OGR** | The universal translator; 250+ raster and 100+ vector drivers | MIT/X |
| **PROJ** | The coordinate engine under GDAL, QGIS, PostGIS, pyproj, sf | MIT |
| **PostGIS** | Spatial extension for PostgreSQL | GPL |
| **GRASS GIS** | Deep raster/terrain/hydrology analysis; QGIS ships it as a processing provider | GPL |
| **SAGA GIS** | Terrain morphometry and geostatistics; also a QGIS provider | GPL/LGPL |
| **ArcGIS Pro / ArcGIS Online** | Esri's commercial desktop and SaaS | Proprietary, per-seat |
| **MapLibre GL JS** | Open fork of Mapbox GL JS v1; style spec version **8** | BSD |
| **PMTiles** | Spec **version 3**; single-file tile archive read by HTTP range request | BSD |

> Choose the **LTR** QGIS (3.44.x) for production work and the latest release only when you need a specific new feature. Plugins lag major version transitions.

## 1. QGIS — the desktop centre of gravity

QGIS does everything the commercial desktop packages do for the vast majority of jobs: read and write everything GDAL supports, style with full symbology control, run a 1000+ algorithm Processing toolbox (its own, plus GDAL, GRASS and SAGA providers), build print layouts with atlas/series generation, edit topologically, connect to PostGIS, and script in Python.

**The parts worth learning deliberately:**

- **The Processing toolbox and the Graphical Modeler.** Anything you do twice should be a model. Models are portable files and can be run headless via `qgis_process`.
- **Rule-based symbology with scale-dependent rules.** This is where cartographic generalisation actually lives in QGIS — filter expressions plus min/max scale per rule.
- **Print Layout with Atlas.** Generates one sheet per feature in a coverage layer — the correct way to produce a series of site plans, plot sheets or map books.
- **Expressions.** A full function language for labels, symbology, geometry generators and data-driven overrides. `@atlas_feature`, `format_number()`, `geometry_generator` symbol layers.
- **Data-defined overrides.** Any symbol property can be driven by an expression, which is how you build proportional symbols, variable-width lines and rotation-by-attribute.

**Headless QGIS** (for automation and CI):

```bash
# List available algorithms
qgis_process list

# Run one
qgis_process run native:buffer -- \
  INPUT=roads.gpkg DISTANCE=25 OUTPUT=roads_buffer.gpkg

# Render a layout to PDF from a project, no GUI
qgis_process run native:printlayouttopdf -- \
  LAYOUT="Site Plan" \
  PROJECT_PATH=site.qgz \
  OUTPUT=site_plan.pdf
```

**PyQGIS inside the console:**

```python
from qgis.core import (QgsProject, QgsVectorLayer, QgsCoordinateReferenceSystem,
                       QgsVectorFileWriter, QgsCoordinateTransformContext)

layer = QgsVectorLayer("/data/plot.gpkg|layername=boundary", "boundary", "ogr")
QgsProject.instance().addMapLayer(layer)

opts = QgsVectorFileWriter.SaveVectorOptions()
opts.driverName = "GPKG"
opts.ct = QgsProject.instance().transformContext()
QgsVectorFileWriter.writeAsVectorFormatV3(
    layer, "/data/plot_lo2217.gpkg",
    QgsProject.instance().transformContext(), opts)
```

**Plugins worth having:**

| Plugin | Does |
|---|---|
| **QuickMapServices** | Adds XYZ basemaps (OSM, satellite providers) in two clicks |
| **QuickOSM** | Overpass queries from inside QGIS |
| **Profile Tool / Elevation Profile** (native in 3.30+) | Terrain cross-sections |
| **Qgis2threejs** | Exports a 3D terrain + features scene to a WebGL page |
| **DEMto3D** | Exports a DEM as an STL for 3D printing |
| **MMQGIS / Shape Tools** | Geometry and geodesic utilities |
| **Serval** | Direct raster cell editing — invaluable for patching DEM voids |
| **QField / QFieldSync** | Field data collection on Android/iOS from a QGIS project |
| **Processing R Provider** | Runs R scripts as QGIS algorithms |
| **Lat Lon Tools** | Coordinate capture/zoom in arbitrary CRSs and formats |

## 2. ArcGIS Pro and ArcGIS Online

Still dominant in government, utilities and large consultancies, particularly **[ZA]** in provincial and municipal GIS. What it genuinely does better: **geodatabase topology and domains**, **network analyst** (routing with turn restrictions), **cartographic representations**, ArcGIS Online/Enterprise as an integrated publishing and permissions platform, and Esri's curated content (Living Atlas, World Imagery). What it does worse: cost, licence management, headless automation without a licence server, and openness.

`arcpy` is the Python API; `ArcGIS API for Python` is the modern, notebook-friendly one. Data exchange with the open stack is via GeoPackage or (unavoidably) File Geodatabase, which GDAL reads with the OpenFileGDB driver and writes with the FileGDB driver.

For a small Namibian practice, **there is no case for buying ArcGIS** unless a client mandates it. QGIS + PostGIS + Python covers the work.

## 3. GRASS GIS and SAGA

Both are best used *through QGIS Processing* rather than as primary interfaces, unless you need their depth.

**GRASS** is the strongest open-source engine for raster/terrain/hydrology: `r.watershed`, `r.stream.extract`, `r.sun` (solar irradiation), `r.viewshed`, `v.generalize` (a full cartographic generalisation toolbox implementing Douglas-Peucker, Visvalingam, Chaikin, Hermite and displacement). Its topological vector model is stricter than the simple-features model and catches errors others silently accept.

**SAGA** is the strongest for **terrain morphometry**: curvature suites, topographic wetness index, multi-scale roughness, relative slope position, and the *Terrain Analysis – Lighting* module set (including a good sky-view-factor and analytical hillshading).

```bash
# GRASS in a throwaway session, from the shell
grass -c EPSG:32733 /tmp/grassdb/namibia --exec bash -c '
  r.in.gdal input=dem.tif output=dem
  g.region raster=dem
  r.watershed elevation=dem threshold=5000 \
    accumulation=facc drainage=fdir stream=streams
  r.to.vect input=streams output=streams type=line
  v.out.ogr input=streams output=streams.gpkg format=GPKG
'
```

## 4. GDAL/OGR — the command line that does the real work

Learn these seven commands and you can do 80% of geospatial data work without opening a GUI.

```bash
# --- INSPECT ---
gdalinfo -stats dem.tif                 # raster metadata, CRS, stats, overviews
ogrinfo -so -al data.gpkg               # vector layers, fields, extents, feature counts

# --- CONVERT ---
ogr2ogr -f GPKG out.gpkg in.shp                       # format conversion
gdal_translate -of COG -co COMPRESS=DEFLATE in.tif out.tif

# --- REPROJECT ---
ogr2ogr -f GPKG out.gpkg in.gpkg -s_srs EPSG:4326 -t_srs EPSG:32733
gdalwarp -t_srs EPSG:32733 -tr 10 10 -r bilinear in.tif out.tif

# --- CLIP ---
ogr2ogr -f GPKG clip.gpkg in.gpkg -clipsrc aoi.gpkg
gdalwarp -cutline aoi.gpkg -crop_to_cutline -dstnodata -9999 in.tif clip.tif

# --- MOSAIC ---
gdalbuildvrt mosaic.vrt tiles/*.tif          # virtual, instant, no copy
gdal_translate -of COG mosaic.vrt mosaic_cog.tif

# --- QUERY / FILTER with SQL ---
ogr2ogr -f GPKG primary.gpkg roads.gpkg \
  -dialect SQLITE \
  -sql "SELECT fid, name, highway, ST_Length(geom) AS len_m
        FROM roads WHERE highway IN ('trunk','primary')"

# --- RASTER MATHS ---
gdal_calc.py -A ndvi_2020.tif -B ndvi_2026.tif \
  --outfile=ndvi_change.tif --calc="B-A" --NoDataValue=-9999
```

**Virtual file systems** are the underrated superpower. GDAL can read *inside* archives and *over* the network without downloading:

```bash
gdalinfo /vsizip/archive.zip/folder/data.tif
gdalinfo /vsicurl/https://example.com/big_cog.tif      # range requests only
gdalinfo /vsis3/bucket/key.tif                          # with AWS creds
ogrinfo -so /vsigzip/data.geojson.gz
```

**Performance flags worth knowing:**

```bash
export GDAL_CACHEMAX=2048              # MB of block cache
export GDAL_NUM_THREADS=ALL_CPUS
export VSI_CACHE=TRUE
export CPL_VSIL_CURL_ALLOWED_EXTENSIONS=.tif,.TIF,.vrt
gdalwarp -multi -wo NUM_THREADS=ALL_CPUS ...
```

## 5. PROJ

Covered in depth in `02_geodesy-and-coordinate-systems.md`. The commands to remember:

```bash
projinfo EPSG:29377                                   # what is this CRS
projinfo -s EPSG:4293 -t EPSG:4326 --summary          # what transformations exist, and how good
proj -le | grep -i bess                               # what ellipsoids are built in
echo "17.1 -22.5" | cs2cs -f "%.4f" EPSG:4326 EPSG:29377
export PROJ_NETWORK=ON                                # let PROJ fetch geoid/NTv2 grids on demand
projsync --list-files                                 # or pre-fetch them
```

## 6. PostGIS and spatial SQL

PostgreSQL + PostGIS is the correct home for any dataset you query repeatedly, and spatial SQL is the most transferable skill in the field.

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_raster;

-- Load an OSM extract
-- ogr2ogr -f PostgreSQL PG:"dbname=gis" namibia.osm.pbf -nlt PROMOTE_TO_MULTI

-- Always index
CREATE INDEX roads_geom_idx ON roads USING GIST (geom);
ANALYZE roads;

-- Reproject on the fly (note: Lo22/17 for the Okongo belt)
SELECT id, ST_Transform(geom, 29377) AS geom_lo FROM parcels;

-- Area in a metric CRS, never in 4326 or 3857
SELECT name, ST_Area(ST_Transform(geom, 32733)) / 10000.0 AS hectares
FROM parcels ORDER BY hectares DESC;

-- Geodesic length/area without projecting at all
SELECT ST_Length(geom::geography) AS metres FROM roads WHERE id = 1;

-- Nearest neighbour, index-assisted (the <-> KNN operator)
SELECT p.name, ST_Distance(p.geom::geography, s.geom::geography) AS m
FROM places p, (SELECT geom FROM sites WHERE id = 7) s
ORDER BY p.geom <-> s.geom
LIMIT 5;

-- Points within 500 m of a road, using the index properly
SELECT b.*
FROM buildings b
JOIN roads r ON ST_DWithin(b.geom::geography, r.geom::geography, 500);

-- Dissolve / union by attribute
SELECT region, ST_Union(geom) AS geom FROM districts GROUP BY region;

-- Topology-preserving simplification for a whole coverage (PostGIS 3.4+)
SELECT ST_CoverageSimplify(geom, 50) OVER () FROM districts;

-- Serve vector tiles straight from the database
SELECT ST_AsMVT(t, 'parcels', 4096, 'geom')
FROM (
  SELECT id, name,
         ST_AsMVTGeom(ST_Transform(geom, 3857),
                      ST_TileEnvelope(14, 8901, 9420), 4096, 64, true) AS geom
  FROM parcels
  WHERE geom && ST_Transform(ST_TileEnvelope(14, 8901, 9420), 4326)
) AS t;
```

**DuckDB spatial** is the newer, lighter alternative for file-based analytics — no server, reads GeoParquet/GeoJSON/Shapefile/GPKG directly, and queries remote Parquet over HTTP:

```sql
INSTALL spatial; LOAD spatial;
SELECT count(*) FROM ST_Read('namibia.gpkg', layer='roads');
SELECT name, ST_Area(ST_Transform(geom, 'EPSG:4326', 'EPSG:32733')) AS m2
FROM ST_Read('parcels.gpkg');
```

## 7. Python

The standard stack, and what each thing is for:

| Library | For |
|---|---|
| **GeoPandas** | Vector dataframes — pandas plus geometry. The default entry point |
| **Shapely** | Geometry objects and predicates (the GEOS binding) |
| **Fiona** | Low-level vector IO (OGR binding); GeoPandas uses it or pyogrio |
| **pyogrio** | Faster vectorised OGR IO; use `engine="pyogrio"` |
| **Rasterio** | Raster IO and windowed reads (GDAL binding) |
| **pyproj** | CRS objects and transformations (PROJ binding) |
| **xarray + rioxarray** | Labelled N-dimensional arrays; the right tool for time-series raster cubes |
| **rasterstats / exactextract** | Zonal statistics |
| **Folium / Leafmap** | Quick interactive maps in a notebook |
| **PDAL (Python bindings)** | Point clouds |
| **scikit-learn / PyTorch** | Classification and deep learning |

```python
import geopandas as gpd
import rioxarray as rxr
import numpy as np
from rasterstats import zonal_stats

# --- Vector ---
plots = gpd.read_file("plots.gpkg", layer="boundary", engine="pyogrio")
print(plots.crs)                                   # EPSG:4326
plots_m = plots.to_crs(32733)                      # UTM 33S, metres
plots_m["area_ha"] = plots_m.area / 10_000
plots_m["perim_m"] = plots_m.length

# Buffer, dissolve, overlay
setback = plots_m.buffer(3.0)                      # 3 m building line
buildable = gpd.overlay(plots_m,
                        gpd.GeoDataFrame(geometry=setback, crs=plots_m.crs),
                        how="intersection")

# Namibian cadastral CRS — note the axis order
plots_lo = plots.to_crs("EPSG:29377")
print(plots_lo.total_bounds)   # y is westing (negative east of the CM), x is southing

# --- Raster ---
dem = rxr.open_rasterio("dem_utm33s.tif", masked=True).squeeze()
print(dem.rio.crs, dem.rio.resolution())
clipped = dem.rio.clip(plots_m.geometry, plots_m.crs)
print(f"min {float(clipped.min()):.2f} m, max {float(clipped.max()):.2f} m")

# Slope from a metric-CRS DEM
dy, dx = np.gradient(clipped.values, *[abs(r) for r in dem.rio.resolution()])
slope_deg = np.degrees(np.arctan(np.hypot(dx, dy)))

# --- Zonal statistics ---
stats = zonal_stats("plots.gpkg", "dem_utm33s.tif",
                    stats=["min", "max", "mean", "std"], geojson_out=False)

# --- Streaming a remote COG without downloading it ---
import rasterio
from rasterio.windows import from_bounds
url = "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_S18_00_E017_00_DEM/Copernicus_DSM_COG_10_S18_00_E017_00_DEM.tif"
with rasterio.open(url) as src:
    win = from_bounds(17.10, -17.60, 17.30, -17.45, src.transform)
    arr = src.read(1, window=win)
    print(arr.shape, arr.min(), arr.max())
```

## 8. R

R's spatial stack is smaller but excellent, and **tmap** is arguably the best declarative thematic-mapping library in any language.

```r
library(sf); library(terra); library(tmap); library(dplyr)

# Vector
plots <- st_read("plots.gpkg", layer = "boundary")
plots_m <- st_transform(plots, 32733)
plots_m$area_ha <- as.numeric(st_area(plots_m)) / 1e4

# Raster
dem <- rast("dem_utm33s.tif")
slope <- terrain(dem, v = "slope", unit = "degrees")
hs <- shade(terrain(dem, "slope", unit="radians"),
            terrain(dem, "aspect", unit="radians"),
            angle = 45, direction = 315)

# Zonal stats
plots_m$mean_elev <- terra::extract(dem, vect(plots_m), fun = mean, na.rm = TRUE)[,2]

# A publication-quality thematic map, declaratively
tm_shape(hs) + tm_raster(palette = gray(0:100/100), legend.show = FALSE) +
tm_shape(plots_m) +
  tm_polygons("area_ha", palette = "YlOrBr", style = "jenks", n = 5,
              title = "Plot area (ha)", border.col = "grey20", alpha = 0.85) +
tm_scale_bar(position = c("left","bottom")) +
tm_compass(type = "arrow", position = c("right","top")) +
tm_credits("Data: own survey 2026. CRS: EPSG:32733 (WGS 84 / UTM 33S).",
           size = 0.6, position = c("left","bottom")) +
tm_layout(main.title = "Plot areas, Okongo", frame = TRUE)
```

## 9. Web mapping libraries

| Library | Model | Use when |
|---|---|---|
| **Leaflet** | Lightweight, DOM/Canvas, raster-first | Simple raster-tile maps, small vector overlays, maximum compatibility. ~40 kB |
| **MapLibre GL JS** | WebGL, vector tiles, style-spec driven | The default modern choice. Open fork of Mapbox GL JS v1, no token, no per-load billing |
| **Mapbox GL JS** (v2+) | WebGL, proprietary since v2 | Only if you are paying for Mapbox services and want their specific features |
| **OpenLayers** | Comprehensive, standards-heavy | OGC service integration (WMS/WMTS/WFS), non-Web-Mercator projections, complex editing |
| **deck.gl** | GPU data-visualisation layers | Large point/arc/hexbin datasets, millions of features, custom shaders. Composes with MapLibre |
| **CesiumJS** | 3D globe, WGS 84 ellipsoid, 3D Tiles | True 3D globes, terrain, 3D city models, time-dynamic data |

```js
// MapLibre with a PMTiles basemap and a GeoJSON overlay — no tile server
import maplibregl from 'maplibre-gl';
import * as pmtiles from 'pmtiles';

const protocol = new pmtiles.Protocol();
maplibregl.addProtocol('pmtiles', protocol.tile);

const map = new maplibregl.Map({
  container: 'map',
  style: {
    version: 8,
    glyphs: 'https://cdn.example/fonts/{fontstack}/{range}.pbf',
    sources: {
      base:  { type: 'vector', url: 'pmtiles://https://cdn.example/namibia.pmtiles' },
      hills: { type: 'raster-dem', url: 'pmtiles://https://cdn.example/dem.pmtiles',
               tileSize: 512, encoding: 'terrarium' }
    },
    layers: [
      { id: 'bg', type: 'background', paint: { 'background-color': '#f6f1e7' } },
      { id: 'hillshade', type: 'hillshade', source: 'hills',
        paint: { 'hillshade-exaggeration': 0.4,
                 'hillshade-shadow-color': '#5b4a36' } },
      { id: 'roads', type: 'line', source: 'base', 'source-layer': 'transportation',
        paint: { 'line-color': '#8a7a63',
                 'line-width': ['interpolate', ['exponential', 1.5], ['zoom'],
                                6, 0.5, 14, 3, 18, 12] } }
    ]
  },
  center: [17.22, -17.57],   // Okongo
  zoom: 12
});

map.on('load', () => {
  map.addSource('site', { type: 'geojson', data: '/data/site.geojson' });
  map.addLayer({ id: 'site-fill', type: 'fill', source: 'site',
                 paint: { 'fill-color': '#c1440e', 'fill-opacity': 0.25 } });
  map.addLayer({ id: 'site-line', type: 'line', source: 'site',
                 paint: { 'line-color': '#c1440e', 'line-width': 2 } });
});
```

## 10. Tile servers

| Server | Serves | Note |
|---|---|---|
| **TileServer GL** | Raster and vector tiles from MBTiles/PMTiles, plus style-based raster rendering | Node; the general-purpose choice |
| **Martin** | MVT directly from PostGIS tables and functions, plus MBTiles/PMTiles | Rust, very fast, config-light. Best-in-class for live database tiles |
| **pg_tileserv** | MVT from PostGIS | Go, from Crunchy Data; simple and stable |
| **tegola** | MVT from PostGIS/GeoPackage with caching | Go |
| **TiTiler** | Dynamic tiles from COGs, STAC and MosaicJSON | Python/FastAPI; the standard for raster-on-the-fly |
| **pmtiles serve / a plain CDN** | PMTiles | **No server at all** is often the right answer — see `06` |

```bash
# Build vector tiles from GeoJSON and package as PMTiles
tippecanoe -o namibia.mbtiles -Z4 -z14 \
  --drop-densest-as-needed --extend-zooms-if-still-dropping \
  -l roads roads.geojson -l places places.geojson
pmtiles convert namibia.mbtiles namibia.pmtiles

# Serve PostGIS tables as vector tiles with Martin
martin postgresql://user:pass@localhost/gis
# -> http://localhost:3000/parcels/{z}/{x}/{y}
```

## 11. Design-side tools

GIS packages are bad at the last 10% of visual finish. These fill the gap.

**Blender — terrain relief rendering.** The strongest tool available for photorealistic or artistic shaded relief. Workflow: import a DEM as a displaced plane, light it, render with Cycles, and composite the render over the map as a shaded-relief layer. It handles soft shadows, ambient occlusion, atmospheric perspective and multi-light setups that no `gdaldem` hillshade can approach.

```python
# Blender: build a displaced terrain plane from a 16-bit heightmap
import bpy
W, H = 200.0, 200.0            # ground extent in Blender units (metres)
Z_RANGE = 340.0                # (max_elev - min_elev) in metres, from gdalinfo

bpy.ops.mesh.primitive_plane_add(size=1)
plane = bpy.context.object
plane.scale = (W/2, H/2, 1)
bpy.ops.object.transform_apply(scale=True)

sub = plane.modifiers.new("Subdiv", 'SUBSURF')
sub.subdivision_type = 'SIMPLE'
sub.levels = sub.render_levels = 8      # 2^8 = 256 subdivisions

tex = bpy.data.textures.new("heightmap", 'IMAGE')
tex.image = bpy.data.images.load("/data/dem_16bit.png")
tex.extension = 'EXTEND'

disp = plane.modifiers.new("Displace", 'DISPLACE')
disp.texture = tex
disp.texture_coords = 'UV'
disp.mid_level = 0.0
disp.strength = Z_RANGE                 # exact 1:1 vertical scale
```

The `strength = (max_elev − min_elev)` rule with `mid_level = 0` and a **16-bit** heightmap gives true 1:1 vertical scale. An 8-bit PNG gives 256 elevation steps and will terrace visibly — always export 16-bit. See `08_terrain-and-3d.md` for the export commands.

**Adobe Illustrator / Inkscape — finishing.** Export the map from QGIS as SVG or PDF with layers preserved, then adjust label positions, tidy line joins, add annotation and build the final sheet. Illustrator is the industry standard; Inkscape is free and adequate. The MAPublisher and Avenza plugins keep georeferencing alive inside Illustrator (commercial).

**Figma** — for map *interfaces* rather than maps: legends, controls, dashboards, and the layout around an embedded map.

**Aerialod** — a free, fast point-cloud/heightmap renderer producing isometric relief images with a distinctive look. Good for quick striking terrain visuals; not a production cartography tool.

**Qgis2threejs** — exports a QGIS scene (DEM + draped imagery + extruded vectors) to a self-contained WebGL page. The fastest route from a QGIS project to a shareable 3D view.

```bash
# Export a DEM to a 16-bit PNG heightmap for Blender/Unreal
gdal_translate -of PNG -ot UInt16 -scale <min> <max> 0 65535 \
  dem_utm33s.tif heightmap_16bit.png
gdalinfo -stats dem_utm33s.tif | grep -E "STATISTICS_(MINIMUM|MAXIMUM)"
```

## 12. A recommended minimal stack

For a one-person practice doing construction-site and context mapping in Namibia:

| Need | Tool |
|---|---|
| Desktop, layout, print | **QGIS LTR 3.44.x** |
| Data wrangling, format conversion, reprojection | **GDAL/OGR** from the shell |
| Coordinate diagnosis | **PROJ** (`projinfo`, `cs2cs`) |
| Analysis and automation | **Python** (GeoPandas, Rasterio, rioxarray) in a `conda`/`micromamba` environment |
| Repeated queries, multi-user data | **PostGIS** (or DuckDB spatial if single-user) |
| Drone processing | **OpenDroneMap / WebODM** (see `07`) |
| Point clouds | **PDAL**, **CloudCompare** |
| Web publishing | **tippecanoe → PMTiles → MapLibre**, hosted on any static host |
| Relief rendering | **gdaldem** for production, **Blender** for showpieces |
| Final sheet polish | **Inkscape** |

```bash
# One environment that contains all of it (conda-forge; do NOT pip install gdal)
micromamba create -n geo -c conda-forge \
  python=3.12 gdal proj geos qgis \
  geopandas rasterio rioxarray xarray pyproj shapely pyogrio \
  rasterstats pdal python-pdal duckdb \
  jupyterlab matplotlib
micromamba activate geo
export PROJ_NETWORK=ON
```

## Sources

- [QGIS download page](https://qgis.org/download/) — QGIS project, accessed 2026-08-25
- [GDAL documentation](https://gdal.org/en/stable/) — GDAL contributors, accessed 2026-08-25
- [GDAL FlatGeobuf driver](https://gdal.org/en/stable/drivers/vector/flatgeobuf.html) — accessed 2026-08-25
- [PROJ — Transverse Mercator](https://proj.org/en/stable/operations/projections/tmerc.html) — accessed 2026-08-25
- [MapLibre Style Spec](https://maplibre.org/maplibre-style-spec/) — accessed 2026-08-25
- [PMTiles documentation](https://docs.protomaps.com/pmtiles/) — Protomaps, accessed 2026-08-25

## Open questions

- The exact QGIS 4.x plugin compatibility position (which of the plugins listed have been ported) was not verified; the LTR recommendation is partly for this reason.
- Martin, pg_tileserv, tegola and TiTiler version numbers were not checked in this session — the descriptions are of their stable, long-standing behaviour.
- ArcGIS Pro's current version number and licensing tiers were not verified.
