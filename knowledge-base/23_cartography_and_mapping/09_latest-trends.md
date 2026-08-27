---
id: cartography.trends
title: Latest trends in cartography and geospatial (2025–2026)
domain: 23_cartography_and_mapping
tags: [cloud-native-geospatial, cog, stac, geoparquet, zarr, geozarr, icechunk, pmtiles, overture, foundation-models, prithvi, clay, segment-anything, digital-twin, citygml, 3d-tiles, sar, newspace, ppp-rtk, galileo-has, design-as-code, hype-check]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Cloud-Native Geospatial Forum blog", url: "https://cloudnativegeo.org/blog/", publisher: "Radiant Earth", accessed: 2026-08-25}
  - {title: "Overture Maps release listing", url: "https://overturemaps-us-west-2.s3.us-west-2.amazonaws.com/?list-type=2&delimiter=/&prefix=release/", publisher: "Overture Maps Foundation", accessed: 2026-08-25}
  - {title: "GeoParquet", url: "https://geoparquet.org/", publisher: "OGC / GeoParquet contributors", accessed: 2026-08-25}
  - {title: "IBM-NASA Geospatial models", url: "https://huggingface.co/ibm-nasa-geospatial", publisher: "IBM / NASA", accessed: 2026-08-25}
  - {title: "Clay Foundation Model", url: "https://clay-foundation.github.io/model/", publisher: "Clay Foundation", accessed: 2026-08-25}
  - {title: "OGC 3D Tiles", url: "https://www.ogc.org/standards/3dtiles/", publisher: "OGC", accessed: 2026-08-25}
  - {title: "OGC CityGML", url: "https://www.ogc.org/standards/citygml/", publisher: "OGC", accessed: 2026-08-25}
  - {title: "Galileo High Accuracy Service", url: "https://www.gsc-europa.eu/galileo/services/galileo-high-accuracy-service-has", publisher: "European GNSS Service Centre", accessed: 2026-08-25}
  - {title: "PMTiles documentation", url: "https://docs.protomaps.com/pmtiles/", publisher: "Protomaps", accessed: 2026-08-25}
related: [cartography.data, cartography.web, cartography.remote_sensing, cartography.terrain]
unit_system: SI
---

# Latest trends in cartography and geospatial (2025–2026)

**Summary.** *Dated 2026-08-25.* Five things are genuinely new and genuinely deployed: **cloud-native formats** have become the default rather than the experiment; **serverless maps** via PMTiles have removed the tile server from most architectures; **Overture Maps** is shipping monthly, schema-stable global data under mixed licences; **geospatial foundation models and embeddings** have moved from papers to benchmarked, community-adopted artefacts; and **cartographic design has substantially migrated into code**. Three things are still mostly promise: full digital twins, real-time streaming geospatial at scale, and end-to-end AI map generalisation. This file separates them, with dates, and flags each item **DEPLOYED**, **EMERGING** or **HYPE**.

## Key facts — the dated state of play

| Item | State as of 2026-08-25 |
|---|---|
| **Overture Maps latest release** | **2026-08-19.0**; monthly cadence; six themes (addresses, base, buildings, divisions, places, transportation) |
| **GeoParquet** | **v2.0.0-rc.1**; an **incubating OGC standard**; supported by QGIS, ArcGIS Pro, GeoPandas, DuckDB, Sedona, Databricks, BigQuery, Snowflake, Felt, Kepler GL, gpq |
| **PMTiles** | Spec **version 3**; MapLibre-recommended; Leaflet/OpenLayers/Python/Dart/Kotlin/Rust readers |
| **Icechunk + GeoZarr** | CNG published *"Hybrid Icechunk stores for serverless web mapping"* on **2026-08-10** — virtualised analysis data rendered directly in web maps via GeoZarr multiscales |
| **Geo-embeddings** | **Second** IBM / CNG / Clark University / Planet **Geo-Embeddings Sprint**, announced 2026-07-29, running **27–28 October 2026, Zürich**, focused on *benchmarking and adoption* |
| **Prithvi (IBM/NASA)** | Prithvi-EO-1.0 **100M**; Prithvi-EO-2.0 **300M** and **600M**, trained on NASA HLS; Prithvi-WxC-1.0 **2.3B** on MERRA-2 (technical paper 2024-09-20). Enterprise variants branded Granite |
| **Clay** | Latest **v1.5**; ViT + masked autoencoder SSL; **Apache-2.0** weights and code, CC-BY docs, ODC-BY embeddings; moved from Radiant Earth to Renaissance Philanthropy support |
| **3D Tiles** | **v1.1**, OGC Community Standard **22-025r4** |
| **CityGML** | **3.0**, OGC **20-010**; standardises the *information model* (not only a GML encoding); improved indoor LOD and BIM integration; GML encoding standard **21-006r2** |
| **Galileo HAS** | Free PPP corrections via **E6-B** and internet; **Initial Service declared 24 January 2023**; Service Level 1 with reduced coverage/performance |
| **QGIS** | 4.2.1 "Belém do Pará" (2026-07-31); LTR 3.44.13 |
| **CNG Forum 2026** | 6–9 October 2026, Snowbird, Utah. **CNG Japan** 24 Aug 2026; **STAC Japan** 25–27 Aug 2026, co-located with FOSS4G Hiroshima |

> ⚠️ Everything below is dated to **August 2026**. Foundation-model version numbers and Overture releases change monthly. Re-verify before quoting.

## 1. Cloud-native geospatial — **DEPLOYED**

The idea: store data on object storage in formats designed to be **partially read over HTTP**, and query it in place rather than downloading it. The change from 2020 to 2026 is that this stopped being a technique and became the default.

| Format | Replaces | Status |
|---|---|---|
| **COG** (Cloud-Optimized GeoTIFF) | Plain GeoTIFF + a download step | **Fully deployed.** An OGC standard; the delivery format of Sentinel, Landsat, Copernicus DEM |
| **STAC** | Bespoke catalogue APIs | **Fully deployed.** Item/Catalog/Collection/API; the universal EO discovery layer. Used by AWS Open Data, Planetary Computer, Element 84, ESA |
| **GeoParquet** | Shapefile and GeoPackage for analytics | **Deployed and accelerating.** v2.0.0-rc.1; incubating OGC standard; what Overture ships |
| **Zarr / GeoZarr** | NetCDF/HDF5 for large N-D cubes | **Deployed in science, emerging in mapping.** Chunked arrays on object storage |
| **Icechunk** | Ad-hoc Zarr versioning | **Emerging.** Transactional, versioned storage for Zarr. The August 2026 "hybrid Icechunk store" work renders analysis-ready arrays *directly* into web maps via GeoZarr multiscales — a genuinely new capability |
| **PMTiles** | MBTiles + a tile server | **Fully deployed.** See §2 |
| **COPC** | LAZ + an index service | **Deployed.** Range-requestable point clouds |
| **FlatGeobuf** | Shapefile for streaming vectors | **Deployed.** Hilbert R-tree index, range-requestable |

**Why it matters practically.** A Namibian consultancy can now query the whole Sentinel-2 archive, the Copernicus DEM, and Overture's global data from a laptop on a modest connection, because nothing is downloaded that is not needed. The infrastructure gap between a large institution and a one-person practice has largely closed for *data access*. It has not closed for *compute*, and it never closed for *ground truth*.

**A useful counter-current:** CNG published a *"Beyond Open Data"* white paper on **2026-04-13** arguing that **usefulness**, not openness, is the quality metric that matters. That is a healthy correction — a technically open dataset that nobody can find, join or trust is not a public good.

## 2. PMTiles and serverless maps — **DEPLOYED**

A single archive file on object storage, read by HTTP range request, replaces a tile server. Spec version 3, read-only, supported by MapLibre (recommended), Leaflet, OpenLayers, and Python/Dart/Kotlin/Rust implementations.

**Why it is more than a format.** It removes an entire operational tier — the tile server, its scaling, its monitoring, its bill. For a national basemap the cost falls from "a server plus egress" to "a few hundred MB of object storage". Combined with Protomaps' daily open OSM basemap builds, the practical result is that **self-hosting a country basemap is now a weekend task**, not a project.

**The honest limitation.** Read-only. Any update rewrites the archive. That is fine for data with a scheduled refresh and wrong for live-edited data — which still wants Martin, pg_tileserv or a database-backed tiler.

## 3. Overture Maps Foundation — **DEPLOYED, with a licence caveat**

Monthly releases (latest **2026-08-19.0**), GeoParquet, stable **GERS** identifiers, six themes. Backed by Amazon, Meta, Microsoft, TomTom and others under the Linux Foundation.

**What it genuinely solves:** schema stability, ID stability across releases, and conflation of OSM with proprietary and ML-derived sources (Microsoft/Google building footprints, Meta and Foursquare places, TomTom roads) into one queryable dataset.

**What it does not solve, and must not be glossed over:** the licences differ by theme. **Base, buildings, divisions and transportation are ODbL**, requiring "© OpenStreetMap contributors" and carrying share-alike into any derivative database you distribute. **Places is CDLA-Permissive 2.0.** Addresses varies by country. For a commercial, resellable database, places and divisions are usable and buildings/transportation are not — a distinction that is easy to miss because it all arrives in the same S3 prefix.

## 4. Geospatial foundation models and embeddings — **EMERGING, moving fast**

| Model | Who | Size | Data | Licence |
|---|---|---|---|---|
| **Prithvi-EO-1.0** | IBM + NASA | 100M | NASA HLS (Harmonized Landsat Sentinel-2) | See model card |
| **Prithvi-EO-2.0** | IBM + NASA | **300M** and **600M** | HLS | See model card |
| **Prithvi-WxC-1.0** | IBM + NASA | **2.3B** | MERRA-2 weather/climate | Paper 2024-09-20 |
| **Clay v1.5** | Clay Foundation | ViT/MAE | Multi-sensor EO | **Apache-2.0** code+weights; **ODC-BY** embeddings |
| **SatlasNet / Satlas** | Allen Institute for AI | — | Sentinel-2 + NAIP, large labelled set | Open |

**The mechanism.** Self-supervised pretraining (masked autoencoding) on huge *unlabelled* archives produces a backbone that encodes what imagery generally looks like. Fine-tuning on a small labelled set then reaches accuracy that previously needed orders of magnitude more labels. For a region like Namibia with almost no labelled EO training data, this is the single most consequential development of the period.

**Embeddings as a product** is the 2026 turn. Rather than shipping a model, projects ship **precomputed embedding vectors per location per time**, which anyone can query with a similarity search or feed to a trivial classifier. The **second Geo-Embeddings Sprint** (IBM, CNG, Clark University, Planet — 27–28 October 2026, Zürich) is explicitly about *benchmarking and adoption*, which is the signal that the field has moved past novelty into evaluation.

**Honest assessment:** **EMERGING, not settled.** The models are real, downloadable and produce results. What is not yet settled is (a) whether they beat a well-tuned Random Forest on modest tasks with adequate labels — often they do not; (b) how they generalise to underrepresented regions, which includes most of Africa; and (c) reproducible benchmarking, which is exactly what the sprint exists to fix. Treat a foundation model as a strong prior, not as an answer, and **validate against independent ground truth exactly as you would any classifier** (`07`, §8).

## 5. Segment Anything applied to imagery — **EMERGING**

Meta's **Segment Anything Model** family, adapted for geospatial use (`samgeo`, SAM-based QGIS plugins, and various fine-tuned variants), does promptable instance segmentation: click a field, a building, a water body, and get a polygon.

**What works today:** interactive digitising acceleration — segmenting fields, water bodies, building footprints and vegetation patches with a click or a box prompt. This genuinely saves hours in a digitising task, and it is available now in QGIS and in Python (`leafmap`/`samgeo`).

**What does not:** SAM has no semantic knowledge. It segments *a thing*, not *a building*. Turning masks into an attributed, topologically clean feature class still requires classification, cleaning and human review. And it is imagery-resolution-bound: at 10 m Sentinel-2 it will not find a Namibian homestead.

**Verdict:** a very good **assistive** tool, not an extraction pipeline.

## 6. AI-assisted feature extraction and map generalisation

**Feature extraction — DEPLOYED.** Microsoft Global ML Building Footprints and Google Open Buildings are production datasets covering most of the world including Namibia, both flowing into Overture. Road extraction from imagery is production-quality in well-imaged areas. This is settled technology.

**Map generalisation — HYPE, mostly.** Automated cartographic generalisation with deep learning has produced good research results (building simplification and typification, coastline generalisation, deep-learning displacement) and essentially no production systems that replace a cartographer. National mapping agencies still run rule-based generalisation with human oversight. The ICA Commission on Generalisation and Multiple Representation is the honest place to watch this.

**Why it stays hard:** generalisation is not a perceptual task, it is a *decision* task about what a specific map is for. Models can imitate a training corpus's style; they cannot infer the purpose that justified it.

## 7. Digital twins and 3D city models — **EMERGING, over-claimed**

The standards are real and mature:
- **CityGML 3.0** (OGC **20-010**) — now standardises the underlying **information model**, implementable in technologies other than GML; better indoor LOD and much better BIM integration. CityGML 1.0/2.0 remain active and their datasets are not deprecated. A separate GML Encoding Standard is **21-006r2**.
- **3D Tiles 1.1** (OGC Community Standard **22-025r4**) — the streaming and rendering standard for massive 3D content: photogrammetry, buildings, BIM/CAD, instanced features, point clouds.
- **IFC** for BIM, with the perennial CityGML↔IFC semantic-mismatch problem still unsolved in general.

**What is deployed:** LOD1/LOD2 city models for many European and East Asian cities; 3D Tiles streaming of large photogrammetry meshes; municipal 3D viewers.

**What is hype:** the word "digital twin" applied to a static 3D model. A twin implies a **live, bidirectional link** to sensors and to the operation of the asset. Most "digital twins" in the geospatial press are 3D visualisations with a dashboard. The genuine article exists in industrial plant, some utilities and some ports; it does not exist for most cities.

**Verdict:** use CityGML and 3D Tiles because they are good standards. Do not buy the word.

## 8. Real-time and streaming geospatial — **EMERGING, narrow**

Kafka/Flink pipelines with geospatial operators, H3/S2 discrete global grids for stream partitioning, and live vector-tile updates. Genuinely deployed in fleet telematics, ride-hailing, maritime AIS and aviation ADS-B. Largely absent from mapping, planning and Earth observation, where the natural cadence is days to months.

**H3** (Uber's hexagonal hierarchical index) deserves a specific note: it has quietly become the default aggregation grid for large-scale point analytics, is supported natively in DuckDB, BigQuery, Snowflake and PostGIS extensions, and is genuinely useful outside streaming. Hexagons avoid the orientation bias and diagonal-neighbour ambiguity of square grids — but they do **not** nest exactly between resolutions, which is a real gotcha for hierarchical roll-ups.

## 9. Commercial smallsat constellations and NewSpace SAR — **DEPLOYED**

The optical smallsat business is mature: Planet's daily 3–5 m PlanetScope coverage is a routine input, and sub-metre tasking is a commodity purchase through aggregators like SkyFi (archive from ~$15, tasking from ~$200).

**NewSpace SAR** is the more interesting development. **ICEYE**, **Capella Space** and **Umbra** operate X-band SAR constellations delivering sub-metre imagery, all-weather and at night, with tasking latency measured in hours. What changed is price and access: SAR was a national-agency capability a decade ago and is now a credit-card purchase.

**Practical relevance:** cloud is not a constraint for SAR. For monitoring in a rainy season, or for InSAR deformation over a mine, tailings dam or large structure, SAR is now a realistic option for a mid-sized consultancy. Namibia's arid, sparsely vegetated terrain is close to an ideal InSAR environment — coherence stays high where tropical forest destroys it.

## 10. GNSS modernisation and PPP-RTK — **DEPLOYED**

Four global constellations (GPS, GLONASS, **Galileo**, **BeiDou**) plus regional augmentation, and multi-frequency consumer chipsets, have changed what a cheap receiver can do.

- **Galileo High Accuracy Service (HAS)** — **free** PPP corrections broadcast on the **E6-B** signal and over the internet, enabling real-time Precise Point Positioning without a subscription. **Initial Service declared 24 January 2023**, currently at Service Level 1 with reduced coverage and performance. A free, satellite-broadcast decimetre service is a structural change for regions like Namibia with sparse terrestrial CORS coverage.
- **PPP-RTK / SSR** — the convergence of PPP (global, slow convergence) and RTK (local, instant, needs a nearby base) using State Space Representation corrections. Commercial services (Trimble RTX, Hexagon/NovAtel TerraStar, Swift Skylark, u-blox PointPerfect) deliver centimetre-to-decimetre accuracy with convergence in tens of seconds and no local base station.
- **Multi-band consumer chipsets** (u-blox ZED-F9P class) put centimetre RTK into sub-$500 hardware, which is why RTK drones and cheap RTK rovers are now normal.

> ⚠️ Precise positioning still gives you **ellipsoidal height** in a **global reference frame at the current epoch**. Everything in `02` about Schwarzeck, German Legal Metres and geoid separation still applies, and applies *more* — the better your positioning, the more the datum error dominates.

## 11. Indoor and underground mapping — **EMERGING**

Indoor: **IndoorGML**, CityGML 3.0's improved indoor LOD, SLAM-based backpack and handheld scanners (NavVis, Leica BLK2GO, Matterport), and UWB/BLE positioning. Deployed in large commercial buildings, airports and warehouses; not standardised across vendors.

Underground: ground-penetrating radar, utility locating, and the perennial unsolved problem of **utility record accuracy**. The UK's National Underground Asset Register is the most serious institutional attempt. Nothing comparable exists in southern Africa, which is why every excavation is still a risk.

## 12. The shift of cartographic design to code — **DEPLOYED**

The most quietly consequential trend for practitioners. A map style is now a **JSON document under version control**, not a set of dialog boxes.

- **MapLibre / Mapbox style JSON** (spec version 8) — the dominant declarative styling language, with a full expression language.
- **QGIS QML / SLD** — portable style documents.
- **Python and R plotting** — `matplotlib`/`cartopy`, `plotnine`, `ggplot2`, `tmap` — reproducible thematic cartography from a script.
- **Observable / D3** — bespoke cartography as code, with full control.
- **Vega-Lite / deck.gl** — declarative layer specification.

**What this changes:** styles diff, review, branch and deploy like software. A design decision has an author, a date and a rationale in a commit message. Regression is detectable. A style can be generated programmatically — a hundred sheets with consistent symbology from one template.

**What it does not change:** the design judgements in `03_map-design-and-cartographic-theory.md`. Encoding a bad hierarchy in JSON does not improve it.

## 13. Hype check — summary table

| Claim | Verdict |
|---|---|
| "Cloud-native formats are the default" | **DEPLOYED.** True and settled |
| "You don't need a tile server" | **DEPLOYED.** True for scheduled-refresh data |
| "Overture replaces OSM" | **HYPE.** It *packages* OSM plus other sources. OSM remains the upstream for four of six themes, with ODbL attached |
| "Foundation models have solved EO classification" | **HYPE.** They are a strong prior. Validate like any classifier; they often lose to a tuned Random Forest with adequate labels |
| "Precomputed EO embeddings are usable now" | **EMERGING.** Real artefacts exist; benchmarking is the active work (Zürich sprint, Oct 2026) |
| "SAM automates feature extraction" | **PARTLY.** Excellent assistive digitising; not a pipeline. No semantics |
| "AI does map generalisation" | **HYPE.** Research results, no production replacement for a cartographer |
| "Digital twins are here" | **HYPE** for cities; **DEPLOYED** in industrial plant. The standards (CityGML 3.0, 3D Tiles 1.1) are real |
| "SAR is affordable now" | **DEPLOYED.** Sub-metre X-band SAR on a credit card |
| "Free decimetre GNSS from space" | **DEPLOYED** — Galileo HAS, Initial Service since Jan 2023, Service Level 1 |
| "Real-time geospatial everywhere" | **HYPE** outside telematics/maritime/aviation |
| "Cartographic design is code now" | **DEPLOYED** |
| "GeoParquet replaces Shapefile" | **DEPLOYED for analytics**; GeoPackage still the right general file format |

## 14. What to actually adopt, in order

For a small practice doing construction, terrain and context mapping in Namibia:

1. **Stop using Shapefile.** GeoPackage for files, GeoParquet for analytics. Free, immediate, zero risk.
2. **Adopt COG + STAC** for all imagery and elevation. Stream, do not download.
3. **Adopt PMTiles + MapLibre** for any web deliverable. The cost model is unbeatable.
4. **Use Overture places and divisions**; use OSM/Overture transportation and buildings only where ODbL is acceptable.
5. **Put styles under version control.**
6. **Add SAM-assisted digitising** to the QGIS workflow — immediate time saving, no risk.
7. **Watch, do not yet build on**: foundation models and embeddings, Icechunk/GeoZarr, digital twins.

## Sources

- [Cloud-Native Geospatial Forum blog](https://cloudnativegeo.org/blog/) — Radiant Earth, accessed 2026-08-25 (Icechunk 2026-08-10; Geo-Embeddings Sprint 2026-07-29; STAC Japan 2026-06-23; CNG Forum 2026-04-24; Beyond Open Data 2026-04-13)
- [Cloud-Native Geospatial Forum](https://cloudnativegeo.org/) — accessed 2026-08-25
- [Overture release listing (S3)](https://overturemaps-us-west-2.s3.us-west-2.amazonaws.com/?list-type=2&delimiter=/&prefix=release/) — accessed 2026-08-25 (2026-08-19.0)
- [Overture attribution and licensing](https://docs.overturemaps.org/attribution/) — accessed 2026-08-25
- [GeoParquet](https://geoparquet.org/) — accessed 2026-08-25 (v2.0.0-rc.1, incubating OGC standard)
- [IBM-NASA Geospatial on Hugging Face](https://huggingface.co/ibm-nasa-geospatial) — accessed 2026-08-25
- [Clay Foundation Model](https://clay-foundation.github.io/model/) — accessed 2026-08-25 (v1.5, Apache-2.0)
- [OGC 3D Tiles](https://www.ogc.org/standards/3dtiles/) — accessed 2026-08-25 (1.1, 22-025r4)
- [OGC CityGML](https://www.ogc.org/standards/citygml/) — accessed 2026-08-25 (3.0, 20-010; encoding 21-006r2)
- [Galileo High Accuracy Service](https://www.gsc-europa.eu/galileo/services/galileo-high-accuracy-service-has) — European GNSS Service Centre, accessed 2026-08-25
- [PMTiles documentation](https://docs.protomaps.com/pmtiles/) — Protomaps, accessed 2026-08-25
- [QGIS download](https://qgis.org/download/) — accessed 2026-08-25

## Open questions

- **Prithvi model licences and exact release dates** were not stated on the Hugging Face organisation page; only the WxC technical paper date (2024-09-20) is confirmed. Check individual model cards. `needs-verification`.
- **SatlasNet / Satlas** details (current version, coverage, licence) were **not** verified from a primary source in this session. The description is from general knowledge and should be confirmed.
- Galileo HAS **accuracy and convergence-time figures** are in the Service Definition Document, which was not retrieved. The service page confirms free, E6-B + internet, PPP, Initial Service 2023-01-24, Service Level 1 — but not the numbers.
- Commercial PPP-RTK service accuracy and convergence claims (Trimble RTX, TerraStar, Skylark, PointPerfect) are vendor claims and were not verified.
- Whether GeoParquet 2.0.0 has moved from release candidate to final since the page was fetched.
- 2025 CNG blog post titles were not enumerated (the archive page lists 20 posts without titles in the fetched view).
