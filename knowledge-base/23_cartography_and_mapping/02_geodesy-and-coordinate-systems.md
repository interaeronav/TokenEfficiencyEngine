---
id: cartography.geodesy
title: Geodesy and coordinate systems
domain: 23_cartography_and_mapping
tags: [geodesy, datum, ellipsoid, geoid, projection, epsg, proj, utm, gauss-conform, schwarzeck, hartebeesthoek94, cape-datum, egm2008, vertical-datum, namibia, south-africa]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "EPSG Geodetic Parameter Dataset (API v1)", url: "https://apps.epsg.org/api/v1/", publisher: "IOGP Geomatics Committee", accessed: 2026-08-25}
  - {title: "PROJ Transverse Mercator projection", url: "https://proj.org/en/stable/operations/projections/tmerc.html", publisher: "PROJ contributors", accessed: 2026-08-25}
  - {title: "Copernicus DEM collection description", url: "https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM", publisher: "Copernicus Data Space Ecosystem", accessed: 2026-08-25}
related: [cartography.overview, cartography.namibia, cartography.terrain]
unit_system: SI
---

# Geodesy and coordinate systems

**Summary.** Every coordinate is a claim about a reference frame, and the frame is usually implicit. This file makes it explicit: the geoid and ellipsoid, datums and the transformations between them, map projections and their distortion trade-offs, the EPSG registry, vertical datums and the orthometric/ellipsoidal height distinction, geoid models, and PROJ pipelines with commands that run. It gives the southern African cases in full because they are unusually treacherous: **Namibia's Schwarzeck datum sits on a Bessel ellipsoid whose semi-major axis is defined in German Legal Metres**, and both Namibia and South Africa use a **south-orientated Gauss-Conform grid with westing/southing axes** that half the world's software mishandles.

## Key facts

| Item | Value | EPSG |
|---|---|---|
| WGS 84 geographic 2D | a = 6 378 137 m, 1/f = 298.257223563 | **4326** |
| WGS 84 / Pseudo-Mercator (web) | Spherical Mercator maths on WGS 84 coordinates | **3857** |
| GRS 80 ellipsoid | a = 6 378 137 m, 1/f = 298.257222101 | 7019 |
| Clarke 1880 (Arc) ellipsoid | a = **6 378 249.145 m**, 1/f = **293.4663077** | 7013 |
| **[NA]** Bessel Namibia (GLM) ellipsoid | a = **6 377 397.155 German Legal Metres** = **6 377 483.865 international m**, 1/f = **299.1528128** | **7046** |
| German Legal Metre | **1 GLM = 1.0000135965 m** | unit 9031 |
| **[NA]** Schwarzeck datum | Fundamental point Schwarzeck, **22°45′35.820″S, 18°40′34.549″E** (Greenwich). Fixed during the German South West Africa–British Bechuanaland boundary survey, **1898–1903** | datum 6293, CRS **4293** |
| **[NA]** Schwarzeck → WGS 84 (1) | Geocentric translation **dX = +616, dY = +97, dZ = −251 m**; stated accuracy **35 m** (derived at 3 stations, ~20 m per axis) | operation **1226** |
| **[NA]** Schwarzeck → WGS 84 (2) | **dX = +615.64, dY = +102.08, dZ = −255.81 m** | operation **1271** |
| **[NA]** Namibian Lo belts | Schwarzeck / Lo22/11, /13, /15, /17, /19, /21, /23, /25 | **29371, 29373, 29375, 29377, 29379, 29381, 29383, 29385** |
| **[NA]** Namibian Lo axes and units | **westing, southing (Y,X)**, unit **German Legal Metre**; latitude of natural origin **−22°**, scale factor **1.0** | CS 6502 |
| **[ZA]** Cape datum | Fundamental point Buffelsfontein, **33°59′32.000″S, 25°30′44.622″E**; Clarke 1880 (Arc) | datum 6222, CRS 4222 |
| **[ZA]** Cape → Hartebeesthoek94 (1) | **dX = −134.73, dY = −110.92, dZ = −292.66 m**; residuals should not exceed **15 m** | operation **1504** |
| **[ZA]** Hartebeesthoek94 | Coincident with **ITRF91 at epoch 1994.0** at Hartebeesthoek observatory; WGS 84 ellipsoid | datum 6148, CRS **4148** / 4941 (3D) / 4940 (geocentric) |
| **[ZA]** SA Lo belts | Hartebeesthoek94 / Lo15…Lo33 | **2046–2055**; legacy Cape / Lo15…Lo33 = 22275–22293 |
| **[ZA]** SA Lo axes and units | **westing, southing (Y,X)**, metres; latitude of natural origin **0°**, scale factor **1.0** | CS 6503 |
| UTM zones over Namibia | zone 32S (west of 12°E, tiny sliver), **33S (12–18°E)**, **34S (18–24°E)**, 35S (east of 24°E) | 32732, **32733**, **32734**, 32735 |
| EGM96 geoid height | Vertical CRS "EGM96 height" | **5773** |
| EGM2008 geoid height | Vertical CRS "EGM2008 height" | **3855** |

> ⚠️ **[NA]** The Namibian Lo grids are in **German Legal Metres, not metres**. A distance of 10 000 grid units is 10 000.136 international metres. Over a 1 km site that is 13.6 mm — usually irrelevant. Over a 100 km traverse it is 1.36 m — never irrelevant. Software that silently treats GLM as metres will introduce a scale error of **13.6 ppm**.

> ⚠️ **[NA]** The Schwarzeck→WGS 84 geocentric translations are only good to **~20–35 m**. They are *not* adequate for cadastral work. For survey-grade transformation you need the official parameters or grid from the Namibian Surveyor-General, not the EPSG global fallback. Never present a datum-shifted cadastral coordinate as authoritative.

## 1. The shape of the Earth: geoid, ellipsoid, terrain

Three surfaces, routinely confused.

- **The terrain** — the physical surface. What you stand on.
- **The ellipsoid** — a smooth mathematical figure of revolution chosen to approximate the Earth. Purely geometric; has no physical meaning. Defined by a semi-major axis `a` and inverse flattening `1/f`.
- **The geoid** — the equipotential surface of the Earth's gravity field that best matches global mean sea level. It is *physical*: water at rest lies along it. It is lumpy at the ±100 m level globally because the Earth's mass distribution is irregular.

The vertical separation between geoid and ellipsoid at a point is the **geoid undulation `N`**. The relationship that governs all height work:

```
h = H + N
```
where `h` = **ellipsoidal height** (what GNSS gives you natively), `H` = **orthometric height** (height above the geoid — what surveyors, engineers and hydrologists mean by "elevation"), `N` = geoid undulation from a geoid model.

Historically ellipsoids were chosen to fit *one region* well — hence Clarke 1880 for Africa, Bessel 1841 for central Europe and (via the Germans) South West Africa, Everest for India. Modern global datums (WGS 84, GRS 80, ITRF) fit the whole Earth and are **geocentric** — the ellipsoid centre coincides with the Earth's centre of mass. Regional datums are *not* geocentric, which is precisely why the shift between Schwarzeck and WGS 84 is ~300–400 m in plan.

### The ellipsoids you will actually meet

| Ellipsoid | a (m) | 1/f | Used by |
|---|---|---|---|
| WGS 84 | 6 378 137 | 298.257223563 | GPS, WGS 84, Hartebeesthoek94 |
| GRS 80 | 6 378 137 | 298.257222101 | NAD83, ETRS89, most modern national datums. Differs from WGS 84 in the last decimal of flattening — sub-millimetre in practice |
| Clarke 1880 (Arc) | 6 378 249.145 | 293.4663077 | **[ZA]** Cape Datum, and Arc 1950/1960 across much of Africa |
| Bessel 1841 | 6 377 397.155 | 299.1528128 | Central Europe, Japan, Indonesia |
| **Bessel Namibia (GLM)** | 6 377 397.155 **GLM** (= 6 377 483.865 m) | 299.1528128 | **[NA]** Schwarzeck |

The Bessel Namibia case is the sharpest trap in African geodesy: the *number* is identical to Bessel 1841, but the *unit* is not, so the ellipsoid is physically **86.7 m larger** in semi-major axis. Any software that assumes "Bessel 1841" for Namibia is wrong by that amount.

## 2. Datums, reference frames and epochs

A **geodetic datum** = an ellipsoid + a definition of how it is positioned and oriented relative to the Earth. A **terrestrial reference frame** (ITRF2014, ITRF2020) is a modern realisation: a set of station coordinates *and velocities*, valid at a stated **epoch**, because tectonic plates move.

Southern Africa is on the slowly-moving African/Nubian plate — of the order of 2–3 cm/yr. Over the 30+ years since **Hartebeesthoek94** was fixed (coincident with ITRF91 at epoch 1994.0), that accumulates to a metre or more of difference from a current ITRF/WGS 84 realisation. For sub-decimetre work you must state the **epoch**, not just the datum.

For construction-site work at the centimetre level this rarely matters *within* a site (all points share the frame). It matters enormously when you combine a 1998 cadastral coordinate with a 2026 RTK observation.

### Datum transformation methods, in increasing rigour

1. **Geocentric translation (3-parameter, Molodensky-Badekas simplified)** — dX, dY, dZ. This is what EPSG publishes for Schwarzeck→WGS 84 and Cape→Hartebeesthoek94. Cheap, national-scale, metre-to-tens-of-metres accurate.
2. **Helmert 7-parameter (Position Vector or Coordinate Frame)** — three translations, three rotations, one scale. Note the **sign convention trap**: "Position Vector" and "Coordinate Frame" rotations differ in sign. Getting this backwards produces an error that is small near the datum origin and grows with distance — very hard to spot.
3. **10-parameter Molodensky-Badekas** — Helmert plus a rotation origin. Avoids correlation between rotations and translations.
4. **Grid-based (NTv2, GTX, or a national geoid/shift grid)** — a gridded correction field. The only method that captures the *distortions* of a classical network. This is what NTv2 does in Canada/Australia/Germany and what modern national transformations use.

> **[ZA]/[NA]** Both countries' national bodies publish or hold official transformation products beyond the EPSG globals. For legally significant work, use theirs. The EPSG entries are explicitly annotated as low accuracy for Namibia (operation 1226 remark: "Derived at 3 stations. Accuracy 20m in each axis").

## 3. Map projections

Projection = a mapping from the curved surface to a plane. **Every projection distorts.** Gauss's *Theorema Egregium* guarantees that a sphere or ellipsoid cannot be flattened without distortion; you choose which property to preserve.

| Property preserved | Class | Preserves | Destroys | Use for |
|---|---|---|---|---|
| Angles/shape locally | **Conformal** | local angles, shape of small features, bearings | area | Navigation, survey, large-scale mapping, anything where you measure angles |
| Area | **Equal-area / equivalent** | area ratios | shape, angles | Thematic maps, density, statistics, land-area calculation |
| Distance from a point/line | **Equidistant** | distance along specific lines only | everything else | Range rings, radial analysis |
| Compromise | none exactly | nothing exactly, everything a bit | — | World reference maps (Robinson, Winkel Tripel, Natural Earth, Equal Earth) |

### The projections that matter in practice

**Mercator** — cylindrical, conformal. Rhumb lines are straight, which is why it won at sea. Area distortion goes as sec(φ)²; Greenland looks like Africa. Legitimate for navigation and for any map where local shape and bearing matter more than area. Illegitimate for any thematic world map.

**Web Mercator, EPSG:3857** — the projection of essentially all slippy maps. It applies *spherical* Mercator formulae to *ellipsoidal* WGS 84 latitudes. This means:
- It is **not strictly conformal** (the sphere/ellipsoid mismatch introduces a small angular distortion, up to ~0.2%).
- It is not a legitimate CRS for measurement. **Never compute area or distance in EPSG:3857** — near the equator the scale error is ~0.7%; at 60° latitude a naive planar distance is 2× too long.
- Latitude is clipped at about **±85.0511°** so the world is square.
- It exists because it makes the tile pyramid trivially simple, not because it is good.

**Transverse Mercator** — the cylinder rotated 90°, tangent (or secant) along a meridian. Conformal, low distortion in a narrow north–south strip, which is why it underpins UTM, Gauss-Krüger, and the southern African Lo systems. Scale error grows roughly as (distance from central meridian)²/(2R²).

**UTM** — 60 zones of 6° longitude, central meridian at zone centre, **scale factor 0.9996** at the central meridian (secant, so scale error is spread ±~0.04% across the zone), false easting 500 000 m, false northing 10 000 000 m in the southern hemisphere. Zones over Namibia: **33S (12–18°E)**, **34S (18–24°E)**, plus slivers of 32S and 35S.

- EPSG:32733 = WGS 84 / UTM zone 33S — covers Windhoek (17.08°E), Walvis Bay, Swakopmund, the whole central corridor.
- EPSG:32734 = WGS 84 / UTM zone 34S — covers eastern Ohangwena beyond 18°E, Rundu, Katima Mulilo and the eastern Kalahari. Note that **Okongo (17.22°E) falls in zone 33S**, not 34S — the zone boundary at 18°E runs east of it.

> UTM is the right *working* CRS for most Namibian analysis: metres, north-orientated, well supported. It is **not** the cadastral CRS.

**Lambert Conformal Conic (LCC)** — conic, conformal, usually with two standard parallels. The standard for mid-latitude countries wider east–west than north–south, and for **aeronautical charts** (ICAO 1:500 000 topographic charts are LCC). Straight lines approximate great circles well over moderate distances — the reason aviation likes it.

**Albers Equal Area Conic** — the equal-area counterpart of LCC. The right choice for a national statistical or land-cover map. EPSG:9221 "Hartebeesthoek94 / ZAF BSU Albers 25E" is South Africa's official national equal-area CRS for biodiversity/statistical use.

### **[NA]/[ZA]** The Gauss-Conform / Lo system — the one that catches everyone

Both countries use a **Transverse Mercator (South Orientated)** projection in **2°-wide belts**, each named by its central meridian. Three peculiarities:

1. **Scale factor is exactly 1.0** at the central meridian — tangent, not secant like UTM. Distortion is therefore zero on the CM and grows to about +180 ppm at the belt edge (1° away). Belts are narrow precisely because there is no secant relief.
2. **The axes are westing and southing.** The coordinate pair is written **(Y, X)** where **Y increases westward** from the central meridian and **X increases southward**. So a point east of the CM has a **negative Y**. Almost all Namibian and South African cadastral coordinates you will see have a negative Y and a large positive X (X ≈ 2 000 000–3 500 000 for **[ZA]**; different for **[NA]** because of the different origin latitude).
3. **The origin latitude differs between the two countries.**
   - **[ZA]** South African Survey Grid: `lat_0 = 0°` (the equator), `lon_0 = odd degree` (15, 17, 19, 21, 23, 25, 27, 29, 31, 33). Hence names Lo15…Lo33. EPSG conversion 17517 = "South African Survey Grid zone 17".
   - **[NA]** South West African Survey Grid: `lat_0 = −22°`, `lon_0 = odd degree` (11, 13, 15, 17, 19, 21, 23, 25). Hence names **Lo22/11 … Lo22/25** — the "22" is the origin latitude, the second number is the central meridian. EPSG conversion 17617 = "South West African Survey Grid zone 17".

That is why Namibian southings are much smaller numbers than South African ones — Namibia's grid origin is at 22°S, not the equator.

**EPSG belt table**

| **[NA]** Belt | Longitude range | EPSG | | **[ZA]** Belt | Longitude range | EPSG (Hart94) | EPSG (Cape) |
|---|---|---|---|---|---|---|---|
| Lo22/11 | west of 12°E | 29371 | | Lo15 | Namibia – Walvis Bay | 2046 | 22275 |
| Lo22/13 | 12–14°E | 29373 | | Lo17 | west of 18°E | 2047 | 22277 |
| Lo22/15 | 14–16°E | 29375 | | Lo19 | 18–20°E | 2048 | 22279 |
| **Lo22/17** | **16–18°E** | **29377** | | Lo21 | 20–22°E | 2049 | 22281 |
| Lo22/19 | 18–20°E | 29379 | | Lo23 | 22–24°E | 2050 | 22283 |
| Lo22/21 | 20–22°E | 29381 | | Lo25 | 24–26°E | 2051 | 22285 |
| Lo22/23 | 22–24°E | 29383 | | Lo27 | 26–28°E | 2052 | 22287 |
| Lo22/25 | east of 24°E | 29385 | | Lo29 | 28–30°E | 2053 | 22289 |
| | | | | Lo31 | 30–32°E | 2054 | 22291 |
| | | | | Lo33 | east of 32°E | 2055 | 22293 |

Note the oddity: **Hartebeesthoek94 / Lo15 (EPSG:2046) and Cape / Lo15 (EPSG:22275) have extent "Namibia – Walvis Bay"** — a legacy of Walvis Bay being administered by South Africa until 1994 and therefore surveyed on the South African grid.

**"Inverted Lo" — EPSG 11296–11306.** Introduced **from 1 January 2019** as an explicit workaround for software that cannot implement south-orientated projection mathematics. These emulate Hartebeesthoek94 / Lo15…Lo33 with conventional **easting, northing** axes. EPSG's own caution is worth quoting in full because it is the correct warning: *"this definition supports emulation of geographical ↔ grid point coordinate conversions, but applications need to be evaluated to verify whether other geometric calculations including but not limited to calculation of bearing, grid convergence, area, etc. are handled correctly. Unexpected calculation results may arise."*

Use Inverted Lo only to get numbers into a stubborn package. Never use it as the CRS of record.

## 4. EPSG codes and how to use the registry properly

The **EPSG Geodetic Parameter Dataset** is maintained by the IOGP Geomatics Committee. It is the authority. Three practices:

1. **Always cite a code, never a name.** "UTM 33S" is ambiguous (which datum?). `EPSG:32733` is not.
2. **Query the registry rather than trusting memory.** The public API is free and needs no key:

```bash
# Find every CRS whose name mentions Schwarzeck
curl -s "https://apps.epsg.org/api/v1/CoordRefSystem/?keywords=Schwarzeck&pageSize=50&format=json" | jq '.Results[] | {Code, Name, Type, Area}'

# Get the definition of one projected CRS
curl -s "https://apps.epsg.org/api/v1/ProjectedCoordRefSystem/29377/" | jq '{Name, CoordSys: .CoordSys.Name, Projection: .Projection.Name}'

# Get the parameters of a datum transformation
curl -s "https://apps.epsg.org/api/v1/Transformation/1226/" | jq '{Name, Accuracy, Params: [.ParameterValues[] | {(.Name): .ParameterValue}]}'
```

3. **Watch axis order.** EPSG:4326's authoritative axis order is **latitude, longitude**. GeoJSON, most web APIs and most casual usage are **longitude, latitude**. GDAL ≥ 3.0 honours the authority order by default; `OAMS_TRADITIONAL_GIS_ORDER` restores lon/lat. This single issue accounts for a large share of "my points are in the Indian Ocean" bugs — though note that for southern Africa a lat/lon swap puts points in Somalia or the Arabian Sea rather than the classic null-island case.

## 5. Vertical datums, orthometric vs ellipsoidal height

**GNSS measures ellipsoidal height `h`.** It has no idea where sea level is. Every builder, hydrologist and drainage engineer wants **orthometric height `H`**.

```
H = h − N
```

`N` comes from a **geoid model**. The globally available ones:

| Model | Year | Resolution | EPSG vertical CRS | Notes |
|---|---|---|---|---|
| **EGM96** | 1996 | 15′ (~28 km) spherical harmonics to degree 360 | **5773** | Legacy. Still the vertical reference of SRTM. Errors of ~0.5–1 m are common. |
| **EGM2008** | 2008 | 1′ (~2 km) grid, harmonics to degree 2159 | **3855** | The current global default. Vertical reference of **Copernicus DEM GLO-30/GLO-90** and most modern global products. |
| National geoid models | varies | varies | national codes | Always better than a global model where they exist. |

For southern Africa, `N` is broadly in the **+10 to +35 m** range and varies across the country, so **using the wrong geoid model, or none at all, produces height errors of tens of metres**. Using EGM96 where EGM2008 is expected typically produces sub-metre to metre errors — enough to ruin a drainage design.

> ⚠️ Two DEMs referenced to different vertical datums (say SRTM on EGM96 and Copernicus on EGM2008) will mosaic into a surface with a **step at every seam**. It renders beautifully and is wrong. Transform to a single vertical datum before merging, always.

**A compound CRS** expresses this properly: horizontal + vertical in one declaration, e.g. `EPSG:32733 + EPSG:3855` (UTM 33S with EGM2008 heights). PROJ writes this as `EPSG:32733+3855`.

## 6. PROJ in practice

PROJ is the engine underneath GDAL, QGIS, PostGIS, pyproj, R's sf, and almost everything else. Learn to drive it directly; it is the fastest way to debug a coordinate problem.

### Inspecting a CRS

```bash
# Human-readable summary + the PROJ string + the WKT
projinfo EPSG:29377
projinfo -o PROJ EPSG:29377
projinfo -o WKT2:2019 EPSG:4293
```

`projinfo EPSG:29377` will show the axis abbreviations **Y (west), X (south)** and the unit **German legal metre** — the two facts that matter most.

### Listing the available transformations between two CRSs

This is the single most useful PROJ command, and almost nobody runs it:

```bash
projinfo -s EPSG:4293 -t EPSG:4326 --spatial-test intersects --summary
```

It lists every candidate pipeline **with its stated accuracy**, ranked. If the best available is 35 m, you now know that before you produce the map, not after the client's surveyor queries it.

### Converting points

```bash
# Schwarzeck geographic -> WGS 84, choosing the transformation explicitly
echo "-22.5 17.1" | cs2cs -f "%.8f" \
  "+proj=longlat +ellps=bess_nam +towgs84=616,97,-251 +no_defs" \
  "+proj=longlat +datum=WGS84 +no_defs"

# The modern, explicit way: build a pipeline and know exactly what it does
echo "17.1 -22.5 1400" | cct -d 4 +proj=pipeline \
  +step +proj=cart +ellps=bess_nam \
  +step +proj=helmert +x=616 +y=97 +z=-251 \
  +step +inv +proj=cart +ellps=WGS84
```

`bess_nam` is PROJ's built-in Bessel Namibia ellipsoid — it already carries the GLM-derived size, so **do not also apply a GLM scale factor**. Verify with:

```bash
proj -le | grep -i bess
# bessel   a=6377397.155  rf=299.1528128  Bessel 1841
# bess_nam a=6377483.865  rf=299.1528128  Bessel 1841 (Namibia)
```

Those two lines are the whole trap, visible in one command.

### **[NA]** Working with the Namibian Lo grid directly

```bash
# WGS 84 lon/lat -> Schwarzeck / Lo22/17 (EPSG:29377), full pipeline
echo "17.1 -22.5" | cs2cs -f "%.4f" EPSG:4326 EPSG:29377

# Explicit PROJ definition, for software that will not take the EPSG code.
# NOTE: +axis=wsu (west, south, up) and +to_meter for German Legal Metres.
+proj=tmerc +lat_0=-22 +lon_0=17 +k=1 +x_0=0 +y_0=0 \
  +axis=wsu +ellps=bess_nam +towgs84=616,97,-251 \
  +units=m +to_meter=1.0000135965 +no_defs
```

The `+axis=wsu` term is what makes it south-orientated. The PROJ `tmerc` documentation itself does not list `+axis` (it is a generic CRS-level parameter, not a projection parameter), which is why so many hand-written definitions omit it and silently produce a north-orientated grid with the right numbers and the wrong signs.

### **[ZA]** South African Lo grid

```bash
echo "28.0 -26.2" | cs2cs -f "%.4f" EPSG:4326 EPSG:2052   # Hartebeesthoek94 / Lo27
# Cape -> Hartebeesthoek94 (the legacy conversion that every old diagram needs)
projinfo -s EPSG:4222 -t EPSG:4148 --summary
```

### Reprojecting data with GDAL/OGR

```bash
# Vector: WGS 84 GeoJSON -> Namibian Lo22/17 GeoPackage
ogr2ogr -f GPKG site_lo2217.gpkg site_wgs84.geojson \
        -s_srs EPSG:4326 -t_srs EPSG:29377 -nln site

# Vector with an explicit datum transformation (do not let it guess)
ogr2ogr -f GPKG out.gpkg in.gpkg \
        -s_srs EPSG:4293 -t_srs EPSG:4326 \
        -ct "+proj=pipeline +step +proj=axisswap +order=2,1 \
             +step +proj=unitconvert +xy_in=deg +xy_out=rad \
             +step +proj=cart +ellps=bess_nam \
             +step +proj=helmert +x=616 +y=97 +z=-251 \
             +step +inv +proj=cart +ellps=WGS84 \
             +step +proj=unitconvert +xy_in=rad +xy_out=deg \
             +step +proj=axisswap +order=2,1"

# Raster: reproject a DEM to UTM 34S at 10 m, bilinear, COG output
gdalwarp -t_srs EPSG:32734 -tr 10 10 -r bilinear \
         -of COG -co COMPRESS=DEFLATE -co PREDICTOR=2 \
         dem_wgs84.tif dem_utm34s.tif
```

### Ellipsoidal → orthometric height with PROJ's geoid grids

PROJ can download geoid grids on demand:

```bash
export PROJ_NETWORK=ON
# WGS 84 ellipsoidal height -> EGM2008 orthometric height
echo "17.1 -22.5 1450.0" | cct -d 3 +proj=pipeline \
  +step +proj=axisswap +order=2,1 \
  +step +proj=unitconvert +xy_in=deg +xy_out=rad \
  +step +proj=vgridshift +grids=us_nga_egm08_25.tif +multiplier=1 \
  +step +proj=unitconvert +xy_in=rad +xy_out=deg \
  +step +proj=axisswap +order=2,1
```

Or, more simply, declare the compound CRS and let GDAL do it:

```bash
gdalwarp -s_srs EPSG:4979 -t_srs "EPSG:32734+3855" ellipsoidal_dem.tif ortho_dem.tif
```

`EPSG:4979` is WGS 84 geographic 3D (ellipsoidal height); `EPSG:32734+3855` is UTM 34S with EGM2008 orthometric height.

### Python (pyproj)

```python
from pyproj import CRS, Transformer, TransformerGroup

lo2217 = CRS.from_epsg(29377)          # Schwarzeck / Lo22/17
print(lo2217.axis_info)                # -> westing (GLM), southing (GLM)
print(lo2217.to_proj4())

# Inspect ALL candidate transformations and their accuracies before choosing
tg = TransformerGroup("EPSG:4293", "EPSG:4326", always_xy=True)
for t in tg.transformers:
    print(f"{t.description}  accuracy={t.accuracy} m")

# Then transform explicitly, lon/lat order
tr = Transformer.from_crs("EPSG:4326", "EPSG:29377", always_xy=True)
y_west, x_south = tr.transform(17.1, -22.5)
print(y_west, x_south)                 # y is NEGATIVE east of the CM
```

`always_xy=True` forces lon,lat input order regardless of authority axis order. Use it consistently or not at all — mixing is where bugs live.

## 7. A decision procedure for choosing a CRS

1. **Is this a legal/cadastral deliverable?** Use the statutory CRS. **[NA]** the relevant Schwarzeck / Lo22/xx belt; **[ZA]** the relevant Hartebeesthoek94 / Loxx belt. No discretion.
2. **Am I measuring distances, areas or doing terrain analysis?** Use a projected CRS with metres and low local distortion. **[NA]** UTM 33S/34S is the pragmatic answer; for the whole country an Albers equal-area with sensible standard parallels for area work.
3. **Am I making a thematic map of area-based quantities?** Equal-area projection, always.
4. **Am I publishing on the web as tiles?** EPSG:3857 for the tiles, but do all computation in a proper CRS first and reproject only for display.
5. **Am I storing data for exchange?** EPSG:4326 (lon/lat) is the lingua franca. Store the CRS in the file (GeoPackage, GeoTIFF, GeoParquet all carry it). Never ship a coordinate list without its CRS.
6. **Am I combining sources?** Reproject everything to one CRS *and one vertical datum* explicitly, logging the transformation used and its accuracy.

## 8. Classic errors, ranked by how often they occur

1. Assuming a coordinate is WGS 84 when it is on a local datum (**[NA]** ~300–400 m error, **[ZA]** ~200–300 m).
2. Computing area or length in EPSG:3857.
3. Latitude/longitude axis order swaps.
4. Treating German Legal Metres as metres (**[NA]**, 13.6 ppm).
5. Ignoring the west/south axis orientation and sign-flipping a whole dataset.
6. Mixing ellipsoidal and orthometric heights in one model.
7. Mosaicking DEMs across different vertical datums.
8. Using a 3-parameter transformation for survey-grade work and quoting its result to millimetres.
9. Ignoring epoch when combining old and new coordinates.
10. Using "Bessel 1841" instead of "Bessel Namibia (GLM)" for Namibia — an 86.7 m ellipsoid error.

## Sources

- [EPSG Geodetic Parameter Dataset API](https://apps.epsg.org/api/v1/) — IOGP Geomatics Committee, accessed 2026-08-25. Specific records used: CRS 4293, 29371–29385, 29333, 4148, 2046–2055, 22275–22293, 11296–11306, 32732–32735, 3857, 3855, 5773; datums 6293, 6222, 6148; ellipsoids 7046, 7013; unit 9031; conversions 17517, 17617; transformations 1226, 1271, 1504.
- [PROJ — Transverse Mercator](https://proj.org/en/stable/operations/projections/tmerc.html) — PROJ contributors, accessed 2026-08-25
- [Copernicus DEM collection description](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM) — accessed 2026-08-25 (vertical datum EGM2008, horizontal WGS84-G1150)

## Open questions

- **[NA]** The official, survey-grade Schwarzeck ↔ ITRF/WGS 84 transformation (7-parameter or grid) held by the Namibian Surveyor-General was not retrieved. The EPSG 3-parameter values above are the public fallback and are explicitly ~20–35 m. `needs-verification` before any cadastral use.
- **[NA]** Whether Namibia has adopted (or is adopting) a modern geocentric national datum in the way South Africa adopted Hartebeesthoek94. Not confirmed.
- **[NA]/[ZA]** The current official national geoid models (as distinct from EGM2008) and their distribution terms.
- Whether the Namibian Lo grid is legally defined in German Legal Metres in the Land Survey Act 33 of 1993 regulations, or only conventionally. EPSG records it as GLM from a Chief Directorate: Surveys and Land Information communication.

