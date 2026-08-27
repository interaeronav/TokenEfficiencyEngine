---
id: cartography.web
title: Web and interactive mapping
domain: 23_cartography_and_mapping
tags: [web-mapping, tiles, vector-tiles, maplibre, style-spec, pmtiles, clustering, accessibility, basemap-pricing, self-hosting, 3d-terrain, cesium]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "MapLibre Style Spec", url: "https://maplibre.org/maplibre-style-spec/", publisher: "MapLibre", accessed: 2026-08-25}
  - {title: "PMTiles documentation", url: "https://docs.protomaps.com/pmtiles/", publisher: "Protomaps", accessed: 2026-08-25}
  - {title: "OpenStreetMap copyright and licence", url: "https://www.openstreetmap.org/copyright", publisher: "OpenStreetMap Foundation", accessed: 2026-08-25}
  - {title: "OGC 3D Tiles", url: "https://www.ogc.org/standards/3dtiles/", publisher: "Open Geospatial Consortium", accessed: 2026-08-25}
related: [cartography.design, cartography.software, cartography.data, cartography.trends]
unit_system: SI
---

# Web and interactive mapping

**Summary.** Modern web cartography is a tile pyramid, a style document and a WebGL renderer. Understanding the tile scheme — how zoom levels map to scale and resolution — explains almost every performance and design decision that follows. The most consequential recent change is that **you no longer need a tile server**: a single **PMTiles** archive on object storage, read by HTTP range request, serves a whole country's basemap from a static host. This file covers the tile scheme, raster vs vector tiles, the MapLibre style specification with a worked example, PMTiles and serverless hosting, performance at scale, interaction, accessibility, basemap provider economics, self-hosting, and 3D.

## Key facts

| Item | Value |
|---|---|
| Standard tile scheme | **Web Mercator (EPSG:3857)**, XYZ, origin top-left, `z/x/y` |
| Tiles at zoom z | `4^z` (2^z × 2^z) |
| Tile size | **256 px** classic, **512 px** common for vector tiles (a 512 px tile at z is equivalent to 256 px at z+1) |
| Ground resolution at the equator (256 px tiles) | `156543.034 / 2^z` metres per pixel |
| Latitude clip | ±**85.0511287798°** |
| Approx scale at z (equator, 96 dpi) | z0 ≈ 1:559 000 000, halving each level: **z10 ≈ 1:546 000**, **z14 ≈ 1:34 000**, **z16 ≈ 1:8 500**, z18 ≈ 1:2 100 |
| MapLibre style spec version | **8** |
| PMTiles spec version | **3** (read-only; updating = rewriting the archive) |
| MVT tile extent (default) | **4096** integer units per tile side |
| 3D Tiles | version **1.1**, OGC Community Standard **22-025r4** (1.0 = 18-053r2) |

**Ground resolution, the number that governs everything:**

```
resolution(z, lat) = 156543.03392804097 * cos(lat_radians) / 2^z     [m/px, 256 px tiles]
```

At Okongo (−17.57°), `cos(lat) = 0.9533`:

| z | m/px | Approx scale | Useful for |
|---|---|---|---|
| 6 | 2 331 | 1:8.4 M | Country in view |
| 10 | 145.7 | 1:520 000 | Region |
| 12 | 36.4 | 1:130 000 | District |
| 14 | 9.11 | 1:33 000 | Settlement |
| 16 | 2.28 | 1:8 200 | Streets |
| 18 | 0.57 | 1:2 000 | **Building footprints, site plan scale** |
| 20 | 0.14 | 1:510 | Drone orthomosaic detail |

> A 5 cm/px drone orthomosaic contains real detail down to about **z22**. Building tiles beyond z20 is usually wasteful; instead serve the orthomosaic as a **COG** with a dynamic tiler, which reads only the pixels needed.

## 1. Raster vs vector tiles

| | Raster tiles | Vector tiles |
|---|---|---|
| Content | Pre-rendered PNG/JPEG/WebP images | Protobuf-encoded geometry + attributes (MVT) |
| Styling | Baked in at generation time | **Applied in the client at runtime** |
| Restyle cost | Regenerate the whole pyramid | Edit a JSON file, reload |
| Size | Large; a country to z14 is many GB | Much smaller; a country to z14 is often < 1 GB |
| Rotation / pitch / 3D | Fixed north-up, flat | Free rotation, tilt, extrusion |
| Label placement | Fixed | Collision-detected at runtime, rotates with the map |
| Client cost | Trivial (image display) | GPU; needs WebGL |
| Best for | Imagery, hillshade, scanned maps, anything genuinely pixel-based | Basemaps, thematic overlays, anything vector |

**The correct combination for most projects:** vector tiles for the basemap and thematic vectors, raster tiles (or a dynamic COG tiler) for imagery and hillshade. MapLibre handles both in the same style.

**Terrain-RGB / Terrarium** deserves a mention: elevation encoded into RGB channels of a raster tile, decoded on the GPU. Two encodings exist and they are **not interchangeable**:

```
Mapbox Terrain-RGB:  height = -10000 + ((R * 256*256 + G * 256 + B) * 0.1)
Terrarium (Mapzen):  height = (R * 256 + G + B / 256) - 32768
```

Declare which with `"encoding": "mapbox"` or `"encoding": "terrarium"` on a `raster-dem` source. Getting it wrong produces terrain that is wildly, obviously wrong — which is at least a merciful failure mode.

## 2. The MapLibre style specification

A style is a single JSON document. Root properties:

| Property | Purpose |
|---|---|
| `version` | Always **8** |
| `name`, `metadata` | Descriptive; no rendering effect |
| `sources` | Named data sources: `vector`, `raster`, `raster-dem`, `geojson`, `image`, `video` |
| `layers` | Ordered list of draw operations. **Order is paint order** — first drawn is bottom |
| `sprite` | URL prefix for the icon spritesheet (`.json` + `.png`) |
| `glyphs` | URL template for font PBFs: `{fontstack}/{range}.pbf` |
| `light`, `sky`, `terrain`, `projection` | Global rendering settings |
| `center`, `zoom`, `pitch`, `bearing` | Default camera |
| `transition` | Default animation timing |

**Layer types:** `background`, `fill`, `line`, `symbol`, `circle`, `fill-extrusion`, `raster`, `hillshade`, `heatmap`, plus `custom`.

**Expressions** are the heart of the specification. Every paint and layout property can be a data-driven or zoom-driven expression:

```json
["interpolate", ["exponential", 1.5], ["zoom"], 8, 0.5, 14, 3, 18, 14]
["step", ["get", "population"], 4, 10000, 7, 100000, 11]
["match", ["get", "surface"], ["paved","asphalt"], "#8a7a63", "#b9a887"]
["case", ["has", "name"], ["get", "name"], ""]
["coalesce", ["get", "name:ng"], ["get", "name"]]
```

`interpolate` produces a continuous ramp between stops; `step` produces discrete classes; `match` and `case` are categorical switches. `["exponential", base]` with base > 1 makes changes accelerate at higher zooms, which is what you want for line widths.

### A worked style — a Namibian site-context basemap

```json
{
  "version": 8,
  "name": "Okongo site context",
  "glyphs": "https://cdn.example/fonts/{fontstack}/{range}.pbf",
  "sprite": "https://cdn.example/sprites/basic",
  "sources": {
    "base": {
      "type": "vector",
      "url": "pmtiles://https://cdn.example/namibia.pmtiles",
      "attribution": "© OpenStreetMap contributors (ODbL)"
    },
    "terrain": {
      "type": "raster-dem",
      "tiles": ["https://cdn.example/dem/{z}/{x}/{y}.png"],
      "tileSize": 512,
      "encoding": "terrarium",
      "maxzoom": 12,
      "attribution": "© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA"
    },
    "site": { "type": "geojson", "data": "/data/site.geojson" }
  },
  "layers": [
    { "id": "bg", "type": "background",
      "paint": { "background-color": "#f4efe4" } },

    { "id": "hillshade", "type": "hillshade", "source": "terrain",
      "paint": {
        "hillshade-exaggeration": 0.35,
        "hillshade-shadow-color": "#6b5b45",
        "hillshade-highlight-color": "#fffaf0",
        "hillshade-accent-color": "#a8967a"
      } },

    { "id": "landuse", "type": "fill", "source": "base",
      "source-layer": "landuse",
      "paint": {
        "fill-color": ["match", ["get", "class"],
          "wood", "#d8dfc6", "grass", "#e2e5cf", "residential", "#eee7da",
          "#f4efe4"],
        "fill-opacity": 0.7
      } },

    { "id": "water", "type": "fill", "source": "base", "source-layer": "water",
      "paint": { "fill-color": "#b6cdd8" } },

    { "id": "road-casing", "type": "line", "source": "base",
      "source-layer": "transportation",
      "filter": ["in", ["get", "class"], ["literal", ["trunk","primary","secondary","tertiary"]]],
      "layout": { "line-cap": "round", "line-join": "round" },
      "paint": {
        "line-color": "#8f8069",
        "line-width": ["interpolate", ["exponential", 1.5], ["zoom"],
                        8, 1.2, 14, 6, 18, 22]
      } },

    { "id": "road-fill", "type": "line", "source": "base",
      "source-layer": "transportation",
      "filter": ["in", ["get", "class"], ["literal", ["trunk","primary","secondary","tertiary","unclassified","track"]]],
      "layout": { "line-cap": "round", "line-join": "round" },
      "paint": {
        "line-color": ["match", ["get", "class"],
          "trunk", "#f7c873", "primary", "#fbe3a6", "#ffffff"],
        "line-width": ["interpolate", ["exponential", 1.5], ["zoom"],
                        8, 0.6, 14, 4, 18, 16],
        "line-dasharray": ["case", ["==", ["get","class"], "track"],
                            ["literal", [2, 2]], ["literal", [1]]]
      } },

    { "id": "buildings", "type": "fill", "source": "base",
      "source-layer": "building", "minzoom": 14,
      "paint": { "fill-color": "#ddd2c0", "fill-outline-color": "#bfb29c" } },

    { "id": "site-fill", "type": "fill", "source": "site",
      "paint": { "fill-color": "#c1440e", "fill-opacity": 0.2 } },
    { "id": "site-line", "type": "line", "source": "site",
      "paint": { "line-color": "#c1440e", "line-width": 2.5 } },

    { "id": "place-labels", "type": "symbol", "source": "base",
      "source-layer": "place",
      "layout": {
        "text-field": ["coalesce", ["get", "name:en"], ["get", "name"]],
        "text-font": ["Noto Sans Medium"],
        "text-size": ["interpolate", ["linear"], ["zoom"], 6, 10, 14, 16],
        "text-max-width": 8,
        "text-padding": 6,
        "symbol-sort-key": ["-", 0, ["coalesce", ["get","population"], 0]]
      },
      "paint": {
        "text-color": "#2b2b2b",
        "text-halo-color": "rgba(244,239,228,0.9)",
        "text-halo-width": 1.3,
        "text-halo-blur": 0.4
      } }
  ]
}
```

> Two things this style does that most do not: it uses `symbol-sort-key` so that when labels collide, the **larger settlement wins** rather than whichever tile arrived first; and its halo colour matches the background rather than being white. Both are cheap and both visibly improve the result.

**Validation:**
```bash
npx @maplibre/maplibre-gl-style-spec validate style.json
```

## 3. PMTiles and serverless hosting

PMTiles is a **single-file archive format for pyramids of tiled data** — vector tiles, raster tiles, or JPEG imagery — indexed by z/x/y. Clients use **HTTP Range Requests** to fetch only the tile or metadata they need, so the archive can sit on plain object storage (S3, R2, Backblaze, GitHub Pages, any HTTP server that honours `Range`) with **no tile server, no database, and no per-request compute**.

Properties to know:
- **Spec version 3.**
- **Read-only.** Updating means rewriting the whole archive — the same model as a CSV or a Parquet file.
- Supported by **MapLibre GL JS** (the recommended client), **Leaflet**, **OpenLayers**, a Python package on PyPI, and community implementations in Dart, Kotlin/JVM and Rust.
- Debug and inspect at **pmtiles.io** in the browser.
- Any HTTP server supporting range requests will serve it; the docs suggest the npm `http-server` package for local work.

```bash
# 1. Build vector tiles
tippecanoe -o namibia.mbtiles -Z4 -z14 \
  --drop-densest-as-needed --extend-zooms-if-still-dropping \
  --force \
  -L roads:roads.geojson -L places:places.geojson -L buildings:buildings.geojson

# 2. Convert to PMTiles
pmtiles convert namibia.mbtiles namibia.pmtiles

# 3. Inspect
pmtiles show namibia.pmtiles

# 4. Serve locally for development
npx http-server -p 8080 --cors

# 5. Upload to object storage. CORS and Range must both be enabled.
aws s3 cp namibia.pmtiles s3://my-bucket/ --acl public-read
```

**Required bucket configuration** — this is where most PMTiles deployments fail:

```json
[{
  "AllowedOrigins": ["https://yoursite.example"],
  "AllowedMethods": ["GET", "HEAD"],
  "AllowedHeaders": ["range", "if-match"],
  "ExposeHeaders": ["ETag", "Content-Range", "Content-Length", "Accept-Ranges"],
  "MaxAgeSeconds": 86400
}]
```

If `Content-Range` and `Accept-Ranges` are not exposed to the browser, the client silently falls back to fetching the whole archive — the map works, and your bandwidth bill does not.

**Cost comparison, order of magnitude.** A Namibia-wide vector basemap to z14 is on the order of a few hundred MB. On R2 or B2 (zero or near-zero egress) it costs cents per month to host and serves an unlimited number of map loads. The equivalent on a metered commercial basemap API is a per-1000-loads charge forever.

## 4. Performance at scale

**Vector tile budgets.** Keep individual tiles under ~**500 kB** and preferably under 200 kB. Tools:
- `--drop-densest-as-needed` and `--extend-zooms-if-still-dropping` in tippecanoe.
- Attribute pruning: `-y name -y class` keeps only the attributes the style actually reads. Attributes you never style are pure weight.
- Simplify per zoom (tippecanoe does this by default; `--simplification=N` tunes it).
- Split rarely-used layers into a separate source so they load on demand.

**Point clustering.** For more than a few thousand points, cluster server-side or in the source:

```js
map.addSource('boreholes', {
  type: 'geojson',
  data: '/data/boreholes.geojson',
  cluster: true,
  clusterMaxZoom: 14,
  clusterRadius: 50,
  clusterProperties: { depth_sum: ['+', ['get', 'depth_m']] }
});

map.addLayer({
  id: 'clusters', type: 'circle', source: 'boreholes',
  filter: ['has', 'point_count'],
  paint: {
    'circle-color': ['step', ['get','point_count'], '#a8dadc', 20, '#457b9d', 100, '#1d3557'],
    'circle-radius': ['step', ['get','point_count'], 14, 20, 20, 100, 28],
    'circle-stroke-width': 1.5, 'circle-stroke-color': '#fff'
  }
});
map.addLayer({
  id: 'cluster-count', type: 'symbol', source: 'boreholes',
  filter: ['has', 'point_count'],
  layout: { 'text-field': ['get','point_count_abbreviated'],
            'text-font': ['Noto Sans Bold'], 'text-size': 12 },
  paint: { 'text-color': '#fff' }
});
```

**Beyond ~100 000 features**, move to **deck.gl** layers (`ScatterplotLayer`, `HexagonLayer`, `ArcLayer`, `MVTLayer`) composed over MapLibre, or aggregate server-side into hexbins (H3) or a heatmap.

**Other levers:**
- Serve `.pbf` tiles **gzipped** with `Content-Encoding: gzip`.
- Set long `Cache-Control` on immutable tile archives; version the filename instead of busting the cache.
- Use `maxzoom` on the source and let MapLibre **overzoom** — do not build tiles you do not need.
- Prefer **WebP** over PNG for raster tiles (typically 25–35% smaller).
- Lazy-load the map library itself; MapLibre is not small.

## 5. Interaction and popups

```js
// Cursor affordance + click popup, bound to a specific layer
map.on('mouseenter', 'site-fill', () => map.getCanvas().style.cursor = 'pointer');
map.on('mouseleave', 'site-fill', () => map.getCanvas().style.cursor = '');

map.on('click', 'site-fill', (e) => {
  const f = e.features[0];
  new maplibregl.Popup({ closeButton: true, maxWidth: '320px' })
    .setLngLat(e.lngLat)
    .setHTML(`<h3>${f.properties.name ?? 'Site'}</h3>
              <dl><dt>Area</dt><dd>${(+f.properties.area_m2/10000).toFixed(2)} ha</dd>
                  <dt>Erf</dt><dd>${f.properties.erf ?? '—'}</dd></dl>`)
    .addTo(map);
});

// Hover highlight using feature state (much cheaper than restyling)
let hovered = null;
map.on('mousemove', 'parcels', (e) => {
  if (hovered !== null) map.setFeatureState({source:'base', sourceLayer:'parcels', id:hovered}, {hover:false});
  hovered = e.features[0].id;
  map.setFeatureState({source:'base', sourceLayer:'parcels', id:hovered}, {hover:true});
});
```

**Interaction design rules:**
- Popups are for detail on demand; **tooltips** (hover) for identification. Do not put essential information only in a popup — mobile and keyboard users may never open it.
- Always give a **visible affordance** that a feature is clickable (cursor, hover highlight).
- Preserve state in the **URL hash** (`#zoom/lat/lon/bearing/pitch`) so a view is shareable. MapLibre does this with `hash: true`.
- Constrain the camera with `maxBounds` and `minZoom`/`maxZoom` when the data only covers one area — an unbounded map of a single site invites the user to get lost.
- Provide a **scale control** (`maplibregl.ScaleControl`) and an **attribution control** — the latter is a licence obligation for OSM-derived data, not a nicety.

## 6. Accessibility

Web maps are among the least accessible common web components. The minimum honest effort:

1. **Never make the map the only route to the information.** Provide a data table, list or text summary of the same content. This is the single highest-value action and it also helps search engines and low-bandwidth users.
2. **Keyboard navigation.** MapLibre supports arrow-key pan and `+`/`−` zoom when the canvas has focus. Ensure the canvas is focusable and that focus is visible. Every control (layer toggles, search) must be reachable by keyboard.
3. **ARIA.** Give the map container `role="region"` and an `aria-label` describing it. Announce dynamic changes through an `aria-live` region rather than relying on the visual update.
4. **Colour contrast.** Text over the map needs a real contrast ratio — WCAG 2.2 AA requires **4.5:1** for normal text, **3:1** for large text and for non-text UI components. Halos help but are not a substitute for adequate contrast between text colour and halo colour.
5. **Do not encode meaning by colour alone.** Add pattern, shape, or a label. Roughly 8% of male users have a colour-vision deficiency.
6. **Respect `prefers-reduced-motion`** — disable `flyTo` animation and easing for those users.
7. **Touch targets** of at least 44 × 44 CSS px for controls and clickable symbols.
8. **Text zoom.** Do not disable page zoom; test at 200%.

```html
<div id="map" role="region" aria-label="Map of the site and surrounding area in Okongo, Namibia" tabindex="0"></div>
<div id="map-status" aria-live="polite" class="visually-hidden"></div>
<noscript><img src="/static/site-map-fallback.png" alt="Static map of the site"></noscript>
```

## 7. Basemap providers and their pricing models

| Provider | Model | Notes |
|---|---|---|
| **OpenStreetMap tile servers (tile.openstreetmap.org)** | Free, community-funded | Governed by the **Tile Usage Policy**. OSM states plainly that it **cannot provide a free map API or tiles for third parties**. Do not build a product on it |
| **Mapbox** | Per map load / per tile request, generous free tier then metered | Excellent tooling; GL JS v2+ is proprietary and requires a token |
| **MapTiler** | Per map load, tiered subscriptions; also sells self-hostable tilesets | Good middle path — you can buy the data and host it yourself |
| **Stadia Maps** | Per map load, free non-commercial tier | Hosts Stamen styles |
| **Protomaps** | **Sells nothing per-load**; open-source tooling plus downloadable daily OSM basemap builds you host yourself | The zero-marginal-cost option |
| **Esri ArcGIS Location Platform** | Per transaction/credits | Integrated with the Esri ecosystem |
| **Google Maps Platform** | Per request, expensive at scale; restrictive terms | Cannot be used as a basemap under another vector data layer in most configurations; read the terms |
| **Carto, HERE, TomTom** | Enterprise contracts | — |

**The economics that matter.** Metered basemaps are cheap at prototype scale and expensive at product scale, and the cost is unbounded and proportional to success. A self-hosted PMTiles basemap has a fixed, near-zero cost and unbounded scale. For most non-consumer applications — a municipal viewer, a site-context map, an internal dashboard — **self-hosting is both cheaper and more robust**. The trade-offs are that you own the update cycle and the geocoding/routing services are not included.

## 8. Self-hosting a basemap stack

Two viable architectures.

**A — fully static (recommended for most cases)**

```
OSM extract (.osm.pbf)
   ↓ planetiler / tilemaker
MBTiles (vector tiles, OpenMapTiles or Shortbread schema)
   ↓ pmtiles convert
namibia.pmtiles  →  object storage + CDN
   ↓ pmtiles:// protocol
MapLibre GL JS in the browser
```

Plus: fonts (glyph PBFs) and a sprite sheet, both static files.

```bash
# Build a whole-country vector tileset from an OSM extract (Java, one command)
java -Xmx8g -jar planetiler.jar \
  --area=namibia --download \
  --output=namibia.mbtiles

pmtiles convert namibia.mbtiles namibia.pmtiles

# Generate glyph PBFs from a TTF once
npx fontnik-cli build --font NotoSans-Regular.ttf --out fonts/Noto\ Sans\ Regular/
```

**B — dynamic, database-backed**

```
PostGIS  →  Martin (or pg_tileserv)  →  MVT
COGs     →  TiTiler                  →  dynamic raster tiles
                    ↓
             MapLibre GL JS
```

Choose B when the data changes constantly (live editing, frequently updated parcels) or when the tileset is too large to rebuild. Choose A when the data changes on a schedule — which is almost always.

**Hillshade for a self-hosted stack:**

```bash
# Copernicus DEM -> terrarium-encoded raster tiles
gdaldem hillshade -multidirectional -compute_edges dem.tif hs.tif
rio rgbify -b -10000 -i 0.1 dem.tif dem_terrainrgb.tif   # Mapbox encoding
gdal2tiles.py --xyz -z 4-12 --processes=8 dem_terrainrgb.tif tiles/
```

## 9. 3D terrain and globes

**MapLibre 3D terrain** — the cheapest route to a 3D map. Add a `raster-dem` source and enable terrain:

```js
map.on('load', () => {
  map.addSource('dem', {
    type: 'raster-dem',
    tiles: ['https://cdn.example/dem/{z}/{x}/{y}.png'],
    tileSize: 512, encoding: 'terrarium', maxzoom: 12
  });
  map.setTerrain({ source: 'dem', exaggeration: 1.6 });
  map.setSky({ 'sky-color': '#a7c6e8', 'horizon-color': '#e8d8bd',
               'fog-color': '#e8e0d0', 'fog-ground-blend': 0.6 });
  map.addControl(new maplibregl.TerrainControl({ source: 'dem', exaggeration: 1.6 }));
});
```

Vertical exaggeration of 1.5–2 is usually right for Namibian relief, which is subtle over most of the country. Above ~3 it stops reading as terrain and starts reading as a graph.

**3D buildings** via `fill-extrusion`:

```json
{ "id": "buildings-3d", "type": "fill-extrusion", "source": "base",
  "source-layer": "building", "minzoom": 15,
  "paint": {
    "fill-extrusion-color": "#ddd2c0",
    "fill-extrusion-height": ["coalesce", ["get","height"], ["*", ["get","levels"], 3.0], 4.0],
    "fill-extrusion-base": ["coalesce", ["get","min_height"], 0],
    "fill-extrusion-opacity": 0.9
  } }
```

**CesiumJS** for true globes and heavy 3D. Uses the **3D Tiles** standard (version **1.1**, OGC Community Standard **22-025r4**) — a hierarchical spatial data structure with tile formats for photogrammetry meshes, buildings, BIM/CAD, instanced features and point clouds. Use Cesium when you need: a genuine ellipsoidal globe, global terrain with correct curvature, time-dynamic data, or to stream a large photogrammetry mesh. Its cost is complexity and weight — it is a much larger commitment than MapLibre.

**deck.gl** sits between the two: GPU-accelerated data layers (including `Tile3DLayer` for 3D Tiles and `TerrainLayer`) that compose over MapLibre, with a React-friendly API. The right choice for large-data visualisation with a 3D component.

## 10. A checklist before shipping a web map

- [ ] Attribution is present, visible, and contains the exact strings the licences require (**© OpenStreetMap contributors** for ODbL; the full Copernicus notice for Copernicus DEM).
- [ ] The CRS and datum of any surveyed overlay is stated somewhere the user can find.
- [ ] The map has a scale control, and no distances are computed in EPSG:3857.
- [ ] Tiles are gzipped and cached; CORS exposes `Content-Range` and `Accept-Ranges`.
- [ ] Camera is bounded to the data extent; `hash: true` for shareable views.
- [ ] Keyboard reachable; `aria-label` on the container; a non-map fallback exists.
- [ ] Text contrast ≥ 4.5:1 over its halo; no meaning conveyed by colour alone.
- [ ] `prefers-reduced-motion` respected.
- [ ] Tested on a slow connection and a mid-range Android device, not just on the development machine.
- [ ] The style validates against the spec.

## Sources

- [MapLibre Style Specification](https://maplibre.org/maplibre-style-spec/) — MapLibre, accessed 2026-08-25
- [PMTiles documentation](https://docs.protomaps.com/pmtiles/) — Protomaps, accessed 2026-08-25
- [OpenStreetMap copyright and Tile Usage Policy reference](https://www.openstreetmap.org/copyright) — OSMF, accessed 2026-08-25
- [OGC 3D Tiles](https://www.ogc.org/standards/3dtiles/) — Open Geospatial Consortium, accessed 2026-08-25
- [Overture attribution](https://docs.overturemaps.org/attribution/) — Overture Maps Foundation, accessed 2026-08-25

## Open questions

- Current per-load prices for Mapbox, MapTiler, Stadia, Esri and Google were **not** retrieved and change frequently. The *models* above are accurate; the numbers must be read from the providers' pricing pages.
- The precise current MapLibre GL JS major version and its terrain API stability were not verified in this session.
- Whether Google Maps Platform's current terms permit use as a basemap under third-party vector data — historically restricted; must be read in the current terms.
