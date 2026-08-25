---
id: cartography.resources
title: Books, courses and reference resources
domain: 23_cartography_and_mapping
tags: [books, courses, moocs, penn-state, qgis-training, colorbrewer, blogs, communities, reference, bibliography]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "GEOG 486: Cartography and Visualization", url: "https://www.e-education.psu.edu/geog486/", publisher: "Penn State John A. Dutton e-Education Institute", accessed: 2026-08-25}
  - {title: "The Nature of Geographic Information", url: "https://www.e-education.psu.edu/natureofgeoinfo/", publisher: "Penn State Dutton Institute", accessed: 2026-08-25}
  - {title: "QGIS Training Manual", url: "https://docs.qgis.org/latest/en/docs/training_manual/", publisher: "QGIS project", accessed: 2026-08-25}
  - {title: "ColorBrewer 2.0", url: "https://colorbrewer2.org/", publisher: "Brewer & Harrower, Penn State", accessed: 2026-08-25}
  - {title: "GIS&T Body of Knowledge", url: "https://gistbok.ucgis.org/", publisher: "UCGIS", accessed: 2026-08-25}
  - {title: "International Cartographic Association", url: "https://icaci.org/", publisher: "ICA", accessed: 2026-08-25}
related: [cartography.overview, cartography.career, cartography.design]
unit_system: SI
---

# Books, courses and reference resources

**Summary.** An annotated register of what to read, what to take, and where to look things up. Every URL in this file was checked on **2026-08-25** and returned content unless noted. Books are listed with author and title; **edition numbers and publication years are deliberately omitted where they were not verified** — check the publisher before citing one. The shortest useful path for someone starting: **Brewer's *Designing Better Maps*** for design, the **QGIS Training Manual** for tools, **Iliffe & Lott** for coordinates, and one Penn State open course for structure.

## Key facts

| Resource | Note |
|---|---|
| **Penn State open courseware** | Full course materials, free, no registration, at `e-education.psu.edu/<coursecode>/`. **GEOG 486 Cartography and Visualization** is the flagship |
| **QGIS Training Manual** | The single best free structured start in the field |
| **ColorBrewer 2.0** | Palette selector with colour-blind-safe, print-friendly and photocopy-safe filters |
| **GIS&T Body of Knowledge** (UCGIS) | The field's formal knowledge taxonomy; the reference for what "knowing GIS" means |
| **ICA Commissions** | The best free technical literature on map design and generalisation |
| **gis.stackexchange.com** | Where technical questions actually get answered |

## 1. The canonical books

### Cartographic design and theory

| Book | Author(s) | Why it matters | Level |
|---|---|---|---|
| ***Elements of Cartography*** | Robinson, Morrison, Muehrcke, Kimerling, Guptill | The classic textbook that defined academic cartography for three generations. Now dated on technology and unimprovable on principles. The map-communication model, symbolisation theory and generalisation chapters remain the reference | Foundational |
| ***Thematic Cartography and Geovisualization*** | Slocum, McMaster, Kessler, Howard | The modern standard university text. Comprehensive on thematic map types, classification, colour, multivariate mapping and geovisualisation. If you buy one textbook, this is it | Intermediate–advanced |
| ***Designing Better Maps: A Guide for GIS Users*** | Cynthia A. Brewer (Esri Press) | **The single most useful practical design book.** Short, concrete, applicable the same day. Layout, type, colour, hierarchy — all with worked examples. The companion to ColorBrewer | **Start here** |
| ***Designed Maps: A Sourcebook for GIS Users*** | Cynthia A. Brewer (Esri Press) | The case-study companion: real maps deconstructed, showing the decisions. Read after *Designing Better Maps* | Beginner–intermediate |
| ***How to Lie with Maps*** | Mark Monmonier | The failure modes, entertainingly. Projection propaganda, classification manipulation, selective omission, the choropleth traps. Everyone in the field should have read it | **Read early, read fast** |
| ***Cartography.*** | Kenneth Field (Esri Press) | A large, encyclopaedic, visually superb modern compendium — hundreds of short topic spreads. Excellent as a reference and a browse; not a linear read | Reference |
| ***Cartography: Visualization of Geospatial Data*** | Menno-Jan Kraak & Ferjan Ormeling | The European academic standard. Strong on the map as a communication and analysis instrument, spatial data infrastructure and the ITC tradition | Intermediate |
| ***The Visual Display of Quantitative Information*** | Edward Tufte | Not cartography, but the foundational text on graphical integrity, data-ink and chartjunk. *Envisioning Information* has the more map-relevant material on layering and small multiples | Foundational |
| ***Semiology of Graphics*** (*Sémiologie graphique*) | Jacques Bertin | The origin of the visual variables. Dense, translated, and still the theoretical bedrock of symbolisation | Advanced |
| ***How Maps Work: Representation, Visualization, and Design*** | Alan MacEachren | The cognitive-science account of map reading. Extends Bertin; hard going and worth it if you want theory | Advanced |
| ***Cartographic Relief Presentation*** | Eduard Imhof | The book on relief. Swiss-style shading, hypsometric tints, rock drawing. Beautiful and still unsurpassed on the principles | Specialist |
| ***Making Maps: A Visual Guide to Map Design for GIS*** | John Krygier & Denis Wood | Approachable, visual, opinionated. A good alternative to Brewer for people who dislike textbooks | Beginner |

### GIS, geodesy and remote sensing

| Book | Author(s) | Why it matters | Level |
|---|---|---|---|
| ***Geographic Information Science and Systems*** | Longley, Goodchild, Maguire, Rhind | The standard GIS textbook. Broad, institutional, strong on the science-vs-systems distinction, data quality and uncertainty | Foundational |
| ***Datums and Map Projections for Remote Sensing, GIS and Surveying*** | Jonathan Iliffe & Roger Lott | **The practical book on coordinate systems.** Concise, correct, worked examples. If you read one thing before touching a coordinate, read this. Pairs directly with `02_geodesy-and-coordinate-systems.md` | **Essential** |
| ***Map Projections: A Working Manual*** | John P. Snyder (USGS Professional Paper 1395) | The mathematical reference for projection formulae. **Free from USGS.** Not a read-through; a lookup | Reference |
| ***Flattening the Earth: Two Thousand Years of Map Projections*** | John P. Snyder | The historical and comparative account. The right companion to the Working Manual | Intermediate |
| ***Remote Sensing and Image Interpretation*** | Lillesand, Kiefer & Chipman | The standard remote-sensing textbook. Physics, sensors, interpretation, digital processing. Comprehensive and readable | **Essential for EO** |
| ***Introduction to Remote Sensing*** | James B. Campbell & Randolph H. Wynne | The main alternative to Lillesand; slightly more accessible | Foundational |
| ***Geospatial Analysis*** | de Smith, Goodchild & Longley | A comprehensive guide to spatial analysis methods, **free online** at spatialanalysisonline.com | Reference |
| ***Geocomputation with R*** | Lovelace, Nowosad & Muenchow | **Free online** at r.geocompx.org. The best R spatial book, and a good general spatial-analysis text regardless of language | **Free, excellent** |
| ***Geocomputation with Python*** | Lovelace, Nowosad, Muenchow et al. | **Free online** at py.geocompx.org. The Python companion | **Free** |
| ***PostGIS in Action*** | Obe & Hsu | The practical spatial-SQL book | Intermediate |
| ***Python for Geospatial Data Analysis*** / ***Python Geospatial Development*** | various | Serviceable; the free online books above are generally better and more current | — |

### Books to know about but not necessarily buy

- **Monmonier, *Rhumb Lines and Map Wars*** — a history of the Mercator projection and the Peters controversy. The best cure for projection politics.
- **Wood, *The Power of Maps*** / ***Rethinking the Power of Maps*** — the critical-cartography argument that maps are interested claims, not neutral descriptions.
- **Harley, *The New Nature of Maps*** — the foundational essays in critical cartography.
- **Brotton, *A History of the World in Twelve Maps*** — accessible map history, genuinely good.
- **Tobler, Dorling, Gastner** on cartograms — the primary literature rather than a textbook.

## 2. Courses

### Free and open

| Course | Provider | URL | Note |
|---|---|---|---|
| **GEOG 486: Cartography and Visualization** | Penn State Dutton Institute | https://www.e-education.psu.edu/geog486/ | **The best free cartography course materials on the web.** Full lesson content, no registration |
| **GEOG 160: Mapping our Changing World** | Penn State | https://www.e-education.psu.edu/geog160/ | Introductory geographic information; a gentle entry |
| **The Nature of Geographic Information** | Penn State | https://www.e-education.psu.edu/natureofgeoinfo/ | The conceptual foundations — data models, scale, accuracy, uncertainty. Excellent |
| **GEOG 485: GIS Programming and Software Development** | Penn State | https://www.e-education.psu.edu/geog485/ | Python for GIS, ArcPy-flavoured but transferable |
| **GEOG 489: Advanced Python Programming for GIS** | Penn State | https://www.e-education.psu.edu/geog489/ | The follow-on |
| **GEOG 892: Geospatial Applications of Unmanned Aerial Systems** | Penn State | https://www.e-education.psu.edu/geog892/ | **Directly relevant to drone site survey.** Flight planning, photogrammetry, accuracy |
| **GEOG 858: Spatial Data Science for Emergency Management** | Penn State | https://www.e-education.psu.edu/geog858/ | Applied spatial data science |
| **QGIS Training Manual** | QGIS project | https://docs.qgis.org/latest/en/docs/training_manual/ | **The best free structured start in the whole field.** Work it end to end |
| **QGIS Tutorials and Tips** | Ujaval Gandhi | https://www.qgistutorials.com/ | Task-oriented, exceptionally clear, constantly updated |
| **Spatial Thoughts courses** | Ujaval Gandhi | https://spatialthoughts.com/ | Free open course material on QGIS, Python, Earth Engine. Among the best teaching material available |
| **Automating GIS Processes** | University of Helsinki | https://automating-gis-processes.github.io/ | Free open course on Python geospatial |
| **Introduction to Python for Geographic Data Analysis** | Tenkanen, Heikinheimo, Whipp | https://pythongis.org/ | Free online book/course |
| **mapschool.io** | Tom MacWright | https://mapschool.io/ | A short, plain-language introduction to what maps and geodata are. 20 minutes, high value |
| **Axis Maps Cartography Guide** | Axis Maps | https://www.axismaps.com/guide | A concise, well-designed practical guide to cartographic design. Free |
| **ICA Commission materials** | ICA | https://icaci.org/ | The commissions (Map Design, Generalisation, Mountain Cartography, Cartography and Children) publish workshop material and proceedings, mostly free |
| **GIS&T Body of Knowledge** | UCGIS | https://gistbok.ucgis.org/ | The formal knowledge taxonomy for the field, with short authored entries per topic. The right place to find out what you don't know |

### Paid / structured

| Course | Provider | Note |
|---|---|---|
| **Esri MOOCs and Esri Academy** | Esri — https://www.esri.com/training/ | Esri runs periodic free MOOCs (Cartography., Spatial Data Science, Imagery in Action) that are genuinely good even if you never touch ArcGIS. The Academy catalogue is largely subscription |
| **Penn State GIS Certificate / MGIS** | Penn State World Campus | The reference online GIS qualification; per-credit pricing |
| **UNIGIS Salzburg MSc (GIS) / Professional Certificate** | University of Salzburg Z_GIS | Fully online, EQF 7 / EQF 6; intakes 1 October |
| **ITC short courses and MOOCs** | University of Twente ITC | *Fundamentals of Geospatial Science* (10 weeks), *Photogrammetry and 3D Mapping* (6 weeks), *Remote Sensing and Digital Image Processing* (6 weeks), plus 3–40 hour MOOCs |
| **Coursera / edX specialisations** | various | UC Davis *GIS Specialization*, Johns Hopkins and others. Quality varies; the Penn State and Spatial Thoughts free material is often better |
| **ArcGIS Pro documentation and tutorials** | Esri — https://pro.arcgis.com/en/pro-app/latest/help/ | If you must use ArcGIS Pro, the official tutorials are the fastest route |

## 3. Blogs, communities and people worth following

| Resource | URL | Note |
|---|---|---|
| **GIS Stack Exchange** | https://gis.stackexchange.com/ | **The single most useful technical resource in the field.** Search before asking |
| **r/gis** | https://www.reddit.com/r/gis/ | Career, tooling and job-market discussion |
| **r/cartography** | https://www.reddit.com/r/cartography/ | Design critique. Post your maps here |
| **Something About Maps** (Daniel Huffman) | https://somethingaboutmaps.wordpress.com/ | The best working cartographer's blog. Deep, generous posts on technique, especially terrain and colour |
| **Cartographic Perspectives** (NACIS journal) | https://cartographicperspectives.org/ | **Open access.** The most readable peer-reviewed cartography journal. NACIS's annual conference is the design community's meeting |
| **Cloud-Native Geospatial Forum** | https://cloudnativegeo.org/ | Where the format and infrastructure conversation happens now |
| **Geoawesome** | https://geoawesome.com/ | Industry news, sometimes breathless; useful for tracking commercial developments |
| **GIS Lounge** | https://www.gislounge.com/ | News and explainers |
| **CARTO blog** | https://carto.com/blog/ | Spatial data science and analytics posts |
| **Mapbox blog** | https://www.mapbox.com/blog | Technical posts on tiling, rendering, styling |
| **Perry Geo** (Matthew Perry) | https://www.perrygeo.com/ | Long-running open-source geospatial engineering blog |
| **OSGeo** | https://www.osgeo.org/ | The umbrella foundation for open-source geospatial; the project list is a good tool directory |
| **FOSS4G** | https://foss4g.org/ | The annual open-source geospatial conference. Talks are recorded and free |
| **OSM community** | https://community.openstreetmap.org/ | The OSM forum; regional channels including Africa |
| **HOT (Humanitarian OpenStreetMap Team)** | https://www.hotosm.org/ | The route into humanitarian mapping, and the main driver of OSM coverage in southern Africa |

## 4. Essential reference sites

| Site | URL | For |
|---|---|---|
| **EPSG Geodetic Parameter Dataset** | https://apps.epsg.org/ | The authority on CRSs, datums, ellipsoids and transformations. Free API, no key |
| **epsg.io** | https://epsg.io/ | A friendlier front end to the same data, with PROJ/WKT export |
| **PROJ documentation** | https://proj.org/ | Coordinate transformation. `projinfo`, `cs2cs`, pipelines |
| **GDAL documentation** | https://gdal.org/ | The driver list and the program reference. The most-used documentation in the field |
| **PostGIS reference** | https://postgis.net/docs/ | Spatial SQL function reference |
| **QGIS documentation** | https://docs.qgis.org/ | User manual, training manual, PyQGIS cookbook |
| **PDAL** | https://pdal.io/ | Point-cloud processing |
| **GRASS GIS** | https://grass.osgeo.org/ | Deep raster, terrain and hydrology modules |
| **WhiteboxTools** | https://www.whiteboxgeo.com/ | Terrain and hydrology; the best depression-breaching implementations |
| **ColorBrewer 2.0** | https://colorbrewer2.org/ | Palette selection with CVD-safe, print-safe and photocopy-safe filters |
| **Natural Earth** | https://www.naturalearthdata.com/ | Public-domain small-scale base data |
| **MapLibre Style Spec** | https://maplibre.org/maplibre-style-spec/ | The web styling reference |
| **Leaflet** | https://leafletjs.com/ | Lightweight web mapping |
| **OpenLayers** | https://openlayers.org/ | Standards-heavy web mapping |
| **deck.gl** | https://deck.gl/ | GPU data-visualisation layers |
| **CesiumJS** | https://cesium.com/platform/cesiumjs/ | 3D globes and 3D Tiles |
| **Protomaps / PMTiles** | https://www.protomaps.com/ and https://pmtiles.io | Serverless tiles, and the browser viewer/debugger |
| **STAC Index / stacspec.org** | https://stacspec.org/en | Catalogue standard and a directory of public catalogues |
| **OGC standards** | https://www.ogc.org/standards/ | The formal standards: WMS, WMTS, WFS, OGC API, GeoPackage, 3D Tiles, CityGML |
| **Geofabrik downloads** | https://download.geofabrik.de/ | OSM regional extracts, including `africa/namibia` |
| **Overture docs** | https://docs.overturemaps.org/ | Schema, releases, attribution |
| **Copernicus Data Space Ecosystem** | https://dataspace.copernicus.eu/ | Sentinel data and the Copernicus DEM |
| **USGS EarthExplorer** | https://earthexplorer.usgs.gov/ | Landsat, ASTER, SRTM and the US archives |
| **Microsoft Planetary Computer** | https://planetarycomputer.microsoft.com/ | Open STAC catalogue plus hosted compute |
| **Google Earth Engine** | https://earthengine.google.com/ | Planetary-scale EO analysis |

## 5. Professional and standards bodies

| Body | URL | Scope |
|---|---|---|
| **ICA** — International Cartographic Association | https://icaci.org/ | Cartography and GIScience. Founded 1959. ICC 2027, Warsaw, 18–23 July 2027; EuroCarto 2026, Brno, 9–11 September 2026 |
| **FIG** — International Federation of Surveyors | https://www.fig.net/ | Surveying, cadastre, land administration. Ten technical commissions |
| **ISPRS** | https://www.isprs.org/ | Photogrammetry, remote sensing, spatial information science. Its *Archives* and *Annals* are **open access** — the primary literature for UAV photogrammetry |
| **OGC** | https://www.ogc.org/ | Standards |
| **RICS** | https://www.rics.org/ | Chartered surveying (Geomatics pathway) |
| **NACIS** | https://nacis.org/ | North American Cartographic Information Society. The design community; publishes *Cartographic Perspectives* |
| **[ZA]** **SAGC** — South African Geomatics Council | https://sagc.org.za/ | Statutory registration: Professional/Technologist/Technician Surveyor, **GISc Practitioner** |
| **[NA]** Namibian Council for Professional Land Surveyors, Technical Surveyors and Survey Technicians | — | Statutory registration under Act 32 of 1993. Recognised society: Institute of Land Surveyors of Namibia |
| **GISCI** | https://www.gisci.org/ | The GISP credential |
| **[NA]** **ILMI** — Integrated Land Management Institute, NUST | https://www.nust.na/ | The principal publisher of Namibian land-tenure and land-administration research |

## 6. A suggested reading order

**Week 1** — mapschool.io (20 min), then *How to Lie with Maps* (a weekend), then the Axis Maps Cartography Guide.

**Weeks 2–6** — QGIS Training Manual, worked end to end with your own local data.

**Weeks 4–8, in parallel** — Brewer, *Designing Better Maps*, applying one chapter per map you make.

**Weeks 6–10** — Iliffe & Lott, *Datums and Map Projections*, alongside `02_geodesy-and-coordinate-systems.md` in this domain, reproducing every PROJ command against Namibian data.

**Months 3–6** — Penn State **GEOG 486** for cartographic depth, **GEOG 892** if drone survey is the goal, and *Geocomputation with Python* or *with R* for the analysis side.

**Ongoing** — Slocum as the reference textbook, Field's *Cartography.* as the browse, *Cartographic Perspectives* and Something About Maps for the craft, gis.stackexchange for the problems.

## Sources

- [GEOG 486: Cartography and Visualization](https://www.e-education.psu.edu/geog486/) — Penn State Dutton Institute, accessed 2026-08-25
- [GEOG 160: Mapping our Changing World](https://www.e-education.psu.edu/geog160/) — accessed 2026-08-25
- [The Nature of Geographic Information](https://www.e-education.psu.edu/natureofgeoinfo/) — accessed 2026-08-25
- [GEOG 485](https://www.e-education.psu.edu/geog485/), [GEOG 489](https://www.e-education.psu.edu/geog489/), [GEOG 858](https://www.e-education.psu.edu/geog858/), [GEOG 892](https://www.e-education.psu.edu/geog892/) — all accessed 2026-08-25
- [Penn State Dutton e-Education Institute](https://dutton.psu.edu/) — accessed 2026-08-25
- [QGIS Training Manual](https://docs.qgis.org/latest/en/docs/training_manual/) — accessed 2026-08-25
- [ColorBrewer 2.0](https://colorbrewer2.org/) — accessed 2026-08-25
- [Axis Maps Cartography Guide](https://www.axismaps.com/guide) — accessed 2026-08-25
- [mapschool.io](https://mapschool.io/) — accessed 2026-08-25
- [GIS&T Body of Knowledge](https://gistbok.ucgis.org/) — UCGIS, accessed 2026-08-25
- [Cartographic Perspectives](https://cartographicperspectives.org/) — NACIS, accessed 2026-08-25
- [Something About Maps](https://somethingaboutmaps.wordpress.com/) — Daniel Huffman, accessed 2026-08-25
- [Geocomputation with R](https://r.geocompx.org/) and [with Python](https://py.geocompx.org/) — accessed 2026-08-25
- [Spatial Thoughts](https://spatialthoughts.com/) and [QGIS Tutorials](https://www.qgistutorials.com/) — Ujaval Gandhi, accessed 2026-08-25
- [Esri Training](https://www.esri.com/training/) — accessed 2026-08-25
- [ICA](https://icaci.org/), [FIG](https://www.fig.net/), [ISPRS](https://www.isprs.org/) — accessed 2026-08-25
- [SAGC](https://sagc.org.za/), [GISCI](https://www.gisci.org/) — accessed 2026-08-25

## Open questions

- **Book editions and years are not stated** because they were not verified from publisher pages in this session. Every title and author above is correct; confirm the edition before citing.
- Penn State course codes are volatile — `geog862`, `geog883`, `geog884`, `geog497`, `geog468`, `geog480/481` and `geog482` returned 404 at the time of checking and have been omitted rather than guessed. `geog861` exists but is behind a sign-in.
- The ICA site did not respond to a plain HTTP client during link checking (it responded via a full browser fetch); the URL is correct.
- *Cartographic Perspectives* is open access; *The Cartographic Journal* and *Cartography and Geographic Information Science* are paywalled — `paywalled: true` applies to those two.
- Esri MOOC availability is periodic; check the catalogue rather than assuming a course is currently running.

