---
id: cartography.design
title: Map design and cartographic theory
domain: 23_cartography_and_mapping
tags: [cartographic-design, generalisation, bertin, visual-variables, typography, colour, colorbrewer, thematic-mapping, choropleth, hillshade, relief, layout, map-errors]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "International Cartographic Association — Commissions", url: "https://icaci.org/", publisher: "ICA", accessed: 2026-08-25}
  - {title: "ColorBrewer 2.0", url: "https://colorbrewer2.org/", publisher: "Cynthia Brewer, Mark Harrower, Penn State", accessed: 2026-08-25}
  - {title: "MapLibre Style Spec", url: "https://maplibre.org/maplibre-style-spec/", publisher: "MapLibre", accessed: 2026-08-25}
related: [cartography.overview, cartography.web, cartography.resources]
unit_system: SI
---

# Map design and cartographic theory

**Summary.** A map is an argument made in graphics. Cartographic design is the discipline of making that argument legible, honest and appropriate to its reader. The core apparatus is small and stable: **visual hierarchy** and **figure-ground** organise attention; **generalisation** decides what survives at a given scale; **Bertin's visual variables** determine what a symbol can and cannot encode; **typography** carries the names; **colour** carries the quantities; and a handful of **thematic map types** each have a characteristic way of lying if used carelessly. This file is the craft layer — the part that no amount of GIS competence substitutes for.

## Key facts

| Rule | Value |
|---|---|
| Minimum legible text on print | ~**6 pt** for incidental labels, **7–8 pt** working minimum; below 6 pt is decoration, not information |
| Minimum legible line width (offset print) | ~**0.1 mm** (0.3 pt); on screen, 1 device pixel |
| Minimum distinguishable area symbol | ~**0.5 mm** side / ~**0.4 mm** diameter |
| Maximum sensible classes in a choropleth | **5–7**; beyond that readers cannot match swatch to map |
| Maximum sensible hues in a qualitative palette | **~8–12** before confusion; ColorBrewer qualitative sets cap at 12 |
| Colour-vision deficiency prevalence | ~**8% of men, ~0.5% of women** of northern European descent (deuteranomaly dominant) |
| Standard hillshade illumination | azimuth **315°** (NW), altitude **45°** — a convention, not physics |
| Scale bar rule | Always show a **graphic** scale bar; a representative fraction alone is invalid once the map is resized |
| Zoom level ↔ scale (Web Mercator, 256 px tiles) | z0 ≈ 1:559 million at the equator; each level halves the denominator; **z14 ≈ 1:34 000**, z16 ≈ 1:8 500 |

> ⚠️ The single most common quantitative error in thematic cartography is **mapping counts as a choropleth**. Choropleth areas must show **rates, ratios or densities** — normalised quantities — because the eye reads the *area* of the polygon as part of the magnitude. A choropleth of "number of households" is a map of polygon size.

## 1. Visual hierarchy

A map has a subject. Visual hierarchy is the machinery that tells the eye what the subject is, what supports it, and what is context.

Three or four levels is usually right:

1. **Figure / subject** — the thematic content or the primary features. Strongest contrast, most saturated colour, largest and boldest type.
2. **Supporting structure** — the features that let the reader locate the subject: major roads, coastline, settlements.
3. **Context / base** — terrain, minor hydrology, administrative fill. Low contrast, desaturated, small type.
4. **Marginalia** — title, legend, scale, credits. Present, clearly organised, never competing with the map body.

The tools for creating hierarchy, roughly in order of power: **value (lightness) contrast** > **size** > **saturation** > **hue** > **texture/pattern** > **position**.

The commonest failure is a *flat* map: everything at equal weight, so the eye has nowhere to start. The second commonest is an *inverted* hierarchy: a bright saturated basemap under muted thematic data.

## 2. Figure-ground

Figure-ground is the Gestalt perception that some regions of the graphic are objects and others are background. On maps it is what makes a country read as a shape rather than a hole.

Devices that produce figure-ground separation:

- **Differentiation** — the figure is more detailed, more textured, more saturated than the ground.
- **Closed form** — a complete outline reads as figure.
- **Contrast in value** — light figure on dark ground, or the reverse.
- **Drop shadow / vignette** — a soft dark edge outside the figure's border. Overused, but effective for an island or a study area.
- **Feathering / desaturating the surround** — the standard treatment for a study-area map: full colour inside the area of interest, greyed and lightened outside.
- **Interposition** — overlapping symbols imply depth ordering.

For a construction-site plan, the figure is the site boundary and the works; the ground is everything beyond the boundary. Making that separation explicit is the difference between a plan a planning officer can read in five seconds and one they have to hunt through.

## 3. Generalisation

Generalisation is the controlled loss of detail as scale decreases. It is not "simplification" alone — it is six distinct operations, and confusing them produces bad results.

| Operation | What it does | Example |
|---|---|---|
| **Selection (elimination)** | Decide which features survive at all | Drop tracks and footpaths below 1:100 000; keep tarred roads |
| **Simplification** | Reduce vertex count while keeping shape | Douglas-Peucker / Visvalingam-Whyatt on a coastline |
| **Smoothing** | Remove high-frequency wobble without reducing vertices | Chaikin or spline smoothing of contours derived from a noisy DEM |
| **Aggregation (amalgamation)** | Merge nearby like features into one | A cluster of homestead buildings becomes a single built-up polygon |
| **Displacement** | Move features apart so both remain visible | A road and a railway in a pass, pushed apart so neither is occluded |
| **Exaggeration** | Enlarge a feature beyond true scale because it matters | A road drawn 40 m wide at 1:50 000 because a true-scale 7 m road would be invisible |
| *(also)* **Collapse** | Reduce dimension | A town polygon becomes a point; a river polygon becomes a line |
| *(also)* **Typification** | Replace a pattern with a representative sample | Nine scattered buildings drawn as five in the same pattern |
| *(also)* **Classification** | Group attribute values | 137 land-cover classes reduced to 8 |

**Algorithm notes.** Douglas-Peucker preserves extreme points and is fast, but produces spiky, ugly results at aggressive tolerances and can create self-intersections. **Visvalingam-Whyatt** (effective-area) produces far more natural-looking results and is what `mapshaper` uses by default — prefer it for cartographic simplification. For topology-preserving simplification of shared boundaries (which you almost always want for administrative areas), use `mapshaper -simplify` or PostGIS `ST_SimplifyPreserveTopology` / `ST_CoverageSimplify`, never a per-feature `ST_Simplify`.

```bash
# Topology-safe cartographic simplification with mapshaper
mapshaper regions.gpkg \
  -simplify visvalingam 8% keep-shapes \
  -o format=geojson regions_gen.geojson

# Scale-dependent selection in ogr2ogr (SQL-driven)
ogr2ogr -f GPKG roads_250k.gpkg roads.gpkg \
  -sql "SELECT * FROM roads WHERE class IN ('trunk','primary','secondary')"
```

**Scale-dependent rules of thumb.** The *Radical Law* (Töpfer) gives a first estimate of how many features should survive:

```
n_derived = n_source × sqrt(S_source / S_derived)
```

where S is the scale denominator. Going from 1:50 000 with 1 000 settlements to 1:250 000: `1000 × sqrt(50000/250000) ≈ 447`. Treat this as a sanity check, not a rule.

A practical selection ladder for a Namibian base map:

| Scale | Roads | Settlements | Hydrology | Contours |
|---|---|---|---|---|
| 1:1 000 | all, true width | all buildings | all | 0.25–0.5 m |
| 1:5 000 | all, true width | all buildings | all channels | 0.5–1 m |
| 1:50 000 | tarred + gravel + main tracks | all named places | main oshanas and pans | 5–10 m |
| 1:250 000 | tarred + main gravel | towns + settlements | major oshana systems only | 20–50 m |
| 1:1 000 000 | national routes only | towns only | major rivers only | 100 m or hypsometric tint only |

## 4. Symbolisation and Bertin's visual variables

Jacques Bertin's *Sémiologie graphique* (1967) identified the graphic dimensions available to encode data. The set, with what each can honestly express:

| Variable | Nominal (categories) | Ordinal (rank) | Quantitative (magnitude) | Notes |
|---|---|---|---|---|
| **Position** | ✔ | ✔ | ✔ | On a map, position is already spent — it encodes location |
| **Size** | ✘ | ✔ | ✔ | The strongest quantitative variable available on a map |
| **Value (lightness)** | ✘ | ✔ | ~ | The workhorse for choropleths; ordered, roughly quantitative |
| **Texture / grain** | ~ | ✔ | ~ | Coarse-to-fine reads as ordered |
| **Colour hue** | ✔ | ✘ | ✘ | Categorical only. Hue has **no natural order** — using a rainbow for quantity is a design error |
| **Orientation** | ✔ | ✘ | ✘ | Limited; works for a few classes of point/line symbol |
| **Shape** | ✔ | ✘ | ✘ | Purely nominal; ~5–7 distinguishable shapes |
| *(later additions)* **Saturation** | ~ | ✔ | ~ | Ordered; weaker than value |
| *(later additions)* **Arrangement, crispness, transparency, resolution** | varies | varies | varies | MacEachren's extensions |

Two rules follow directly:

- **Never encode magnitude with hue alone.** The rainbow/jet colour ramp is the canonical violation: it is not perceptually uniform, it creates false boundaries at the yellow and cyan bands, and it is unreadable to colour-blind users.
- **Match the variable to the measurement level.** Nominal data gets hue or shape. Ordinal gets value or saturation. Quantitative gets size, or value on a properly-constructed sequential ramp.

## 5. Typography on maps

Type is the only part of a map that is unambiguously language, and it is where amateur maps most obviously give themselves away.

**The classical rules (Imhof's label placement principles, still the standard):**

1. Labels must be **readable and unambiguously associated** with one feature.
2. Labels must not obscure other important content.
3. Preferred point-label positions, in priority order: **upper right**, upper left, lower right, lower left, then directly right/left/above/below. Offset by roughly the cap height.
4. **Line features** (rivers, roads) take labels that follow the line, curved along it, with the baseline on the line or just above; repeat at intervals rather than stretching one label.
5. **Area features** take labels centred, horizontal or gently curved along the area's long axis, letter-spaced to span the area.
6. **Hydrography is conventionally italic**, often blue. This is a genuine convention worth keeping — it lets a reader classify a name before reading it.
7. Type should **not be rotated** more than gently; never upside down.

**Type hierarchy.** Build a small explicit scale and stick to it. For an A3 topographic-style sheet:

| Role | Size | Weight/style | Colour |
|---|---|---|---|
| Map title | 18–24 pt | Bold | Near-black |
| Subtitle / scale statement | 10–12 pt | Regular | Dark grey |
| Major settlement | 10–11 pt | Bold, letter-spaced | Black |
| Minor settlement | 7–8 pt | Regular | Black |
| Road numbers | 6–7 pt | Regular, in a shield | Route colour |
| Hydrography | 7–8 pt | Italic | Blue, darker than the water fill |
| Contour values | 5–6 pt | Regular | Contour colour, darker |
| Credits / source note | 6–7 pt | Regular | Mid grey |

**Halos.** A halo (text buffer, casing) makes type readable over busy backgrounds. Do it properly:
- Halo colour = the *background* colour, not white by default. Over a green landcover, a pale-green halo is invisible as a halo and perfect as separation. White halos on a dark basemap look like stickers.
- Halo width **0.75–1.5 px** on screen, ~0.15–0.25 mm in print. Wider halos eat the letterforms.
- Prefer a **soft/blurred** halo where the renderer supports it (`text-halo-blur` in MapLibre).

```json
{
  "id": "place-labels",
  "type": "symbol",
  "source": "base", "source-layer": "place",
  "layout": {
    "text-field": ["get", "name"],
    "text-font": ["Noto Sans Medium"],
    "text-size": ["interpolate", ["linear"], ["zoom"], 6, 10, 12, 15],
    "text-max-width": 8,
    "text-padding": 4,
    "symbol-sort-key": ["-", 0, ["get", "population"]]
  },
  "paint": {
    "text-color": "#1b1b1b",
    "text-halo-color": "rgba(255,255,255,0.85)",
    "text-halo-width": 1.2,
    "text-halo-blur": 0.5
  }
}
```

**Font choice.** Humanist sans-serifs read well at small sizes and in curved placement (Frutiger, Myriad, Source Sans, Noto Sans, Inter). Serifs are traditional for hydrography and for historical styling. Avoid condensed faces below 7 pt, and avoid any face without a proper italic if you intend to use the hydrography convention.

## 6. Colour in cartography

**The three palette families**, and the rule that governs them:

| Family | Structure | For | Example |
|---|---|---|---|
| **Sequential** | Single or two-hue ramp, monotonic in lightness, light→dark | Ordered data with one direction (population density, rainfall, elevation) | `Blues`, `YlOrRd`, `viridis` |
| **Diverging** | Two sequential ramps meeting at a light neutral midpoint | Data with a meaningful centre (anomaly from mean, change, +/− values) | `RdBu`, `BrBG`, `PuOr` |
| **Qualitative** | Distinct hues, similar lightness | Nominal categories | `Set2`, `Dark2`, `Paired` |

**ColorBrewer** (Cynthia Brewer, colorbrewer2.org) is still the reference. It gives, for each palette and class count, flags for **colour-blind safe**, **print friendly** and **photocopy safe**. Use those filters — they are free correctness.

**Diverging palettes have one hard rule**: the midpoint must correspond to a *meaningful* value (zero, the mean, the baseline). A diverging ramp applied to non-diverging data invents a break that does not exist.

**Colour-vision deficiency.** Roughly 8% of men have some form. The practical consequences:
- **Red–green pairs are the primary failure.** Avoid red/green as the *only* difference between classes.
- Prefer **blue–orange**, **blue–brown**, or **purple–green** oppositions for diverging schemes.
- **viridis / cividis / magma** are perceptually uniform and CVD-safe by construction; `cividis` is specifically optimised for deuteranopia.
- Always test: simulate with a tool, or convert to greyscale — if the classes are indistinguishable in greyscale, they are relying on hue alone and will fail.

**Terrain hypsometric tints.** The classical scheme runs green (lowland) → yellow → tan → brown → grey/white (high). It is conventional, widely understood, and **carries a false implication** that green means vegetated and brown means barren — a real problem in Namibia, where large low-lying areas are sand and gravel, not grassland. Options:
- Use a **desert-adapted hypsometric ramp** (pale straw → tan → orange-brown → grey) that does not imply vegetation.
- Or drop hypsometric tints entirely and carry elevation with **hillshade + contours**, letting land cover carry the colour.
- Or use a **low-saturation** hypsometric scheme under a strong hillshade, so the tint reads as elevation zoning rather than land cover.

Practical composition for a terrain basemap: a **desaturated hypsometric tint** at 40–60% opacity, multiplied over a **hillshade**, with a slight **slope-darkening** layer, then vector content on top. Keep the terrain's total value range narrow (say 55–90% lightness) so overlaid data has room.

## 7. Thematic mapping types and their traps

| Type | Encodes | Correct use | The trap |
|---|---|---|---|
| **Choropleth** | Value per enumeration unit, by area fill | **Normalised** data: rates, densities, percentages, per-capita | Mapping raw counts; and the **MAUP** — results change with the unit boundaries. Also: large sparse units dominate visually |
| **Proportional / graduated symbol** | Magnitude by symbol size at a point | Raw counts and totals; works with unequal-area units | Human size perception underestimates area; use **perceptual scaling** (Flannery) or scale by area not radius, and always show a nested-circle legend |
| **Dot density** | Count by number of dots | Distribution and density of discrete phenomena | Dot placement within units is *arbitrary* and readers treat it as real. State the dot value and never imply precise location |
| **Isoline / isarithm** | Continuous surface by lines of equal value | Genuinely continuous fields: elevation, rainfall, temperature, water table | Applying it to data that is not continuous (e.g. interpolating between administrative centroids) |
| **Cartogram** | Magnitude by distorted area | Making population-weighted comparisons vivid | Unrecognisable geography; needs a reference inset. Contiguous (Gastner-Newman), non-contiguous, and Dorling variants trade shape for accuracy differently |
| **Flow map** | Movement between origins and destinations | Migration, trade, traffic | Rapid clutter; needs aggressive aggregation, edge bundling, or an origin-focused design |
| **Heat map (KDE)** | Density of point events, smoothed | Exploratory density of incidents | The **bandwidth is a free parameter that determines the answer**. Different bandwidths produce different "hotspots" from identical data. Always state it |
| **Bivariate choropleth** | Two variables in a 3×3 or 4×4 colour matrix | Showing correlation spatially | Legibility collapses beyond 3×3; needs a matrix legend |
| **Value-by-alpha** | Choropleth modulated by a second variable's opacity | Damping unreliable/low-population areas | Background colour becomes load-bearing |

**Classification methods** for choropleths, and what each says:

- **Equal interval** — equal value ranges. Honest about the data's range; can put everything in one class if skewed.
- **Quantile** — equal counts per class. Guarantees a full-looking map; can put nearly identical values in different classes.
- **Natural breaks (Jenks)** — minimises within-class variance. Fits the data's own structure; makes comparison between maps impossible because the breaks move.
- **Standard deviation** — classes as multiples of σ from the mean. Only meaningful for roughly normal data; inherently diverging.
- **Manual / meaningful breaks** — thresholds that mean something externally (a regulatory limit, a poverty line). Usually the best choice when they exist.

> If you produce a series of maps to be compared with each other, **the class breaks must be identical across the series.** Re-classifying each map independently makes the series meaningless.

## 8. Layout elements

| Element | Rule |
|---|---|
| **Title** | States subject, place and time. "Rainfall" is not a title. "Mean annual rainfall, Ohangwena Region, 1991–2020" is |
| **Scale bar** | Graphic bar, in metres or kilometres, with a zero and round divisions. Mandatory if any distance may be measured. Omit on small-scale world maps where scale varies too much to be meaningful |
| **Representative fraction** | State it (1:2 000) *in addition to* the bar, and only if the sheet will be printed at a known size |
| **North arrow** | Simple, small, and **specify which north** — grid, true or magnetic. On a Lo-grid sheet, grid north ≠ true north away from the central meridian (grid convergence). Omit entirely on a north-up map with a graticule |
| **Legend** | Every symbol the reader needs, in a sensible order (usually the map's own hierarchy). Omit obvious ones (blue = water). Choropleth legends run **high value at top** for vertical, low at left for horizontal |
| **Graticule / grid** | Graticule = lat/lon. Grid = projected coordinates. On a survey or site plan, show the **projected grid** with coordinate labels — it is what makes the sheet usable in the field |
| **Inset** | Locator inset (where is this?) or detail inset (zoom into a dense area). Show the main map's extent as a rectangle on the locator |
| **Credits / metadata** | Data sources with dates, **CRS and datum**, producer, production date, and licence/attribution text required by the sources. This is not optional if you used ODbL or CC BY data |
| **Neatline / margin** | A frame contains the map. Generous, consistent margins; do not let content touch the trim edge |

**Layout composition.** Give the map body the dominant area (typically 70–85% of the sheet). Group the marginalia rather than scattering it. Align everything to an implicit grid. Use the map's own visual weight to balance the sheet — a dense area of content on the left wants marginalia on the right.

## 9. Relief representation

| Technique | How | Strengths | Weaknesses |
|---|---|---|---|
| **Contours** | Isolines of elevation | Quantitative, measurable, the engineering standard | Hard to read as form; clutters at fine intervals |
| **Analytical hillshade** | Lambertian shading from a light source, conventionally **azimuth 315°, altitude 45°** | Instant, quantitative, universally understood | Flat and mechanical; artefacts along DEM edges; loses form in flat terrain |
| **Multidirectional / soft hillshade** | Combine several azimuths (GDAL `-multidirectional`, or Swiss-style weighted blends) | Far more natural; reveals form in all orientations | Slower; can look muddy |
| **Slope shading** | Darken by slope angle regardless of aspect | Emphasises escarpments and scarps; good in near-flat terrain | No sense of illumination direction |
| **Swiss-style manual shading (Imhof)** | Aerial perspective: high ground lightened and warmed, valleys darkened and cooled; light generalised, not literal | The most beautiful and legible relief ever produced | Labour-intensive; the digital approximations are only approximations |
| **Tanaka contours (illuminated contours)** | Contour lines varied in width and lightness by their aspect relative to the light | Reads as form *and* stays quantitative | Busy; needs a clean DEM |
| **Texture shading** (Leland Brown) | Fractional-Laplacian filtering of the DEM emphasising drainage texture | Reveals drainage networks and geological grain superbly; scale-independent | Not a substitute for hillshade; best blended with one |
| **Hypsometric tints** | Colour by elevation band | Quick elevation reading at small scale | Implies land cover (see §6) |

```bash
# Standard hillshade
gdaldem hillshade dem.tif hillshade.tif -az 315 -alt 45 -z 1.0 -compute_edges

# Multidirectional — noticeably better for general basemaps
gdaldem hillshade dem.tif hillshade_multi.tif -multidirectional -compute_edges

# Slope, for a slope-darkening layer
gdaldem slope dem.tif slope.tif -compute_edges
gdaldem color-relief slope.tif slope_ramp.txt slope_shade.tif

# Contours at 5 m with an indexed attribute
gdal_contour -a elev -i 5.0 dem.tif contours.gpkg -f GPKG
```

**Vertical exaggeration (`-z`).** In flat terrain a `-z` of 2–5 makes form visible; in mountains `-z 1` is already dramatic. Always state the exaggeration in the credits if it is not 1.

> A hillshade computed from a DEM in **degrees** (EPSG:4326) with `-z 1` is wrong, because horizontal units are degrees and vertical units are metres. Either reproject to a metric CRS first (preferred) or pass `-s 111120` to scale.

## 10. The classic errors

1. **Un-normalised choropleth** — counts instead of rates. §7.
2. **Rainbow ramp for quantity** — hue has no order. §4.
3. **Red–green as the sole distinction** — fails for 8% of male readers. §6.
4. **No scale bar, or a scale bar that survives resizing incorrectly** — a representative fraction on a screen map is meaningless.
5. **Missing or wrong CRS/datum statement** — especially fatal in Namibia. See `02`.
6. **Area or distance computed in EPSG:3857.**
7. **Flat visual hierarchy** — everything the same weight.
8. **Basemap louder than the data** — inverted hierarchy.
9. **Illegible type** — below 6 pt, or over a busy background with no halo.
10. **Too many classes** — 9-class choropleths that nobody can decode.
11. **Class breaks changed between maps in a series** — makes comparison impossible.
12. **Unstated KDE bandwidth or unstated interpolation method** — the parameter *is* the result.
13. **No data provenance or attribution** — a licence violation for OSM/ODbL and CC BY sources, and an honesty failure regardless.
14. **North arrow on a north-up map with a graticule** — clutter.
15. **Decorative compass roses, drop shadows on everything, and 3D pie charts** — noise pretending to be design.
16. **Mixing "no data" with "zero"** — give them visually distinct treatments (hatch or grey vs the lightest class).

## Sources

- [ColorBrewer 2.0](https://colorbrewer2.org/) — Brewer & Harrower, Penn State, accessed 2026-08-25
- [MapLibre Style Specification](https://maplibre.org/maplibre-style-spec/) — MapLibre, accessed 2026-08-25 (symbol layer properties used in the label example)
- [International Cartographic Association — Commissions](https://icaci.org/) — ICA, accessed 2026-08-25 (Map Design and Generalisation commissions are the standing technical reference for §3 and §6)
- [GDAL gdaldem](https://gdal.org/en/stable/programs/gdaldem.html) — GDAL contributors, accessed 2026-08-25

## Open questions

- Bertin's original variable set and MacEachren's extensions are cited from the standard literature (`Sémiologie graphique`, 1967; *How Maps Work*, 1995) rather than from a fetched source — the classification above is uncontroversial but the specific wording is not quoted from a primary URL.
- Imhof's label-placement priority ordering is the widely reproduced version; the original is *Positioning Names on Maps* (1975).
- The Töpfer Radical Law formulation is standard but was not verified against a primary source in this session.

