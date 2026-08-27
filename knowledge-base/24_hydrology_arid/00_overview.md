---
id: hydrology.overview
title: Hydrology overview and why arid zones differ
domain: 24_hydrology_arid
tags: [hydrology, hydrogeology, water-balance, arid, semi-arid, sub-disciplines, cuvelai]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Hydrology (overview article)", url: "https://en.wikipedia.org/wiki/Hydrology", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "FAO Irrigation and Drainage Paper 56 — Crop evapotranspiration", url: "https://www.fao.org/4/x0490e/x0490e00.htm", publisher: "FAO", accessed: 2026-08-25}
  - {title: "Deep, semi-fossil aquifers in southern Africa: a synthesis of hydrogeological investigations in northern Namibia", url: "https://www.biodiversity-plants.de/biodivers_ecol/article_meta.php?DOI=10.7809/b-e.00306", publisher: "Biodiversity & Ecology 6 (Klaus Hess Publishers)", accessed: 2026-08-25}
  - {title: "The long road to sustainability: integrated water quality and quantity assessments in the Cuvelai-Etosha Basin, Namibia", url: "https://www.biodiversity-plants.de/biodivers_ecol/article_meta.php?DOI=10.7809/b-e.00307", publisher: "Biodiversity & Ecology 6", accessed: 2026-08-25}
  - {title: "NASA POWER climatology API (point 17.566°S, 17.216°E)", url: "https://power.larc.nasa.gov/api/temporal/climatology/point", publisher: "NASA Langley Research Center", accessed: 2026-08-25}
related: [hydrology.arid_zone, hydrology.namibia_cuvelai, hydrology.coursework]
unit_system: SI
---

# Hydrology overview and why arid zones differ

**Summary.** Hydrology is the science of water on and below the land surface — its occurrence, circulation, distribution, chemistry and its relationship to living things. The discipline splits into surface-water hydrology, groundwater hydrology (hydrogeology), hydrometeorology, ecohydrology and water-resources engineering, all bound together by the water-balance equation. Almost every textbook, method and rule of thumb in hydrology was calibrated in humid temperate catchments where rainfall is frequent, evaporation is a minority term and rivers flow all year. In drylands — including Okongo and the Cuvelai basin of northern Namibia — the opposite holds: potential evaporation exceeds rainfall roughly fourfold, rainfall arrives as a handful of intense convective storms, rivers flow for days, and recharge is a small residual of two large, poorly-measured numbers. That inversion is the reason arid-zone hydrology is a distinct craft and not a footnote.

## Key facts

| Quantity | Humid temperate (typical) | Okongo / Ohangwena | Source |
|---|---|---|---|
| Mean annual precipitation (P) | 700–1200 mm | ~550 mm (MERRA-2 reanalysis 1991–2024) | NASA POWER |
| Interannual CV of P | 0.15–0.25 | **0.40** | NASA POWER, computed |
| Driest / wettest modelled year in record | ±30% of mean | 212 mm (2019) / 1330 mm (2007) | NASA POWER, computed |
| Reference evapotranspiration ET₀ | 500–800 mm/yr | **~2400 mm/yr** (FAO-56 PM, computed) | FAO-56 method + POWER |
| Aridity index P/ET₀ | 1.0–2.0 | **0.24** (semi-arid: 0.20–0.50) | computed |
| Runoff coefficient (annual) | 0.25–0.50 | typically <0.05, often ~0 | Wanke et al. 2018 |
| Recharge as % of P | 10–30% | **1–5%** near-surface; **<1%** to the deep KOH-2 aquifer | Wanke et al. 2018; Himmelsbach et al. 2018 |
| Days with measurable rain | 150–200 | ~40–60, concentrated Dec–Mar | POWER monthly pattern |

> ⚠️ The POWER figures above are **satellite/reanalysis** estimates, not gauge records. They are internally consistent and good enough for scoping, but a design that matters (tank sizing, culvert sizing, borehole yield) should be re-run against Namibia Meteorological Service or SASSCAL station data. Flagged `needs-verification` for design use.

## What hydrology covers

The organising identity is the **water balance** over a control volume and a time step:

```
P + Q_in  =  ET + Q_out + R + ΔS
```

where `P` is precipitation, `Q_in`/`Q_out` are surface and subsurface inflow/outflow, `ET` is evapotranspiration, `R` is deep recharge (if not counted in Q_out) and `ΔS` is change in storage (soil water, groundwater, surface water, snow). Every sub-discipline is a specialisation in measuring, predicting or manipulating one or more of these terms.

### Surface-water hydrology
Rainfall–runoff processes, hydrographs, flood frequency, open-channel hydraulics, reservoir operation, sediment transport. Its core outputs are design floods (Q₁₀, Q₅₀, Q₁₀₀), flow-duration curves and routing of water through channels. In drylands its hardest problem is that the flow record is mostly zeros, so standard statistics misbehave.

### Groundwater hydrology / hydrogeology
Darcy's law, aquifer characterisation, well hydraulics, recharge estimation, contaminant transport, groundwater modelling. In arid regions this is usually the *primary* discipline rather than a secondary one, because surface water is unreliable and storage below ground is the only buffer that survives a multi-year drought. The Ohangwena aquifer system beneath Okongo is a textbook case: three stacked aquifer "storeys" of very different depth, salinity and renewability.

### Hydrometeorology
The atmospheric end of the cycle: precipitation measurement and its errors, storm structure, evaporation physics, radar and satellite rainfall estimation, weather-driven flood forecasting. In drylands, convective storm cells of 5–20 km diameter mean that a rain gauge 10 km away tells you almost nothing about what fell on your plot.

### Hydrogeology's applied cousins
- **Ecohydrology** — the two-way coupling between vegetation and water. In drylands, deep-rooted trees, groundwater-dependent ecosystems and vegetation patterning (banded bush, termite-mound catenas) are first-order controls on infiltration and recharge, not decoration.
- **Soil physics / vadose zone hydrology** — Richards equation, retention curves, unsaturated conductivity. In deep sand profiles the unsaturated zone can be tens of metres thick and a wetting front may take years to decades to reach the water table, which is why "recharge this year" and "rain this year" can be almost unrelated.
- **Water-resources engineering** — dams, canals, boreholes, pumps, distribution networks, treatment, allocation, economics and law. This is where hydrology meets budgets.
- **Water quality and geochemistry** — major ions, salinity, fluoride, nitrate, isotopes, contaminant transport. Evaporative concentration makes chemistry a *dominant* concern in drylands, not a compliance afterthought.

## Why the temperate textbook fails in drylands

1. **Evaporation dominates the budget.** At Okongo, ET₀ ≈ 2400 mm/yr against P ≈ 550 mm/yr. Every water balance is therefore a small difference between two large, uncertain numbers — a 10% error in ET is a 40%+ error in the residual (runoff plus recharge). Temperate models tolerate sloppy ET; dryland models do not.

2. **Rainfall is intermittent, intense and spatially tiny.** Convective cells deliver a season's rain in a handful of events. Areal reduction factors derived from frontal rainfall in Europe are wrong. Point rain gauges systematically fail to capture storm cores.

3. **Runoff generation is infiltration-excess (Hortonian), not saturation-excess.** Temperate catchments generate storm flow because the soil is already wet near streams; dryland catchments generate it because rain falls faster than a crusted or sandy soil can absorb it. The controlling parameter is rainfall *intensity* against infiltration capacity, not antecedent wetness — so a curve-number or TOPMODEL approach imported unchanged is conceptually wrong.

4. **Channels lose water instead of gaining it.** Ephemeral rivers running over sand have **transmission losses**: flow decreases downstream, often to zero. Discharge is not conserved along the reach. Nearly all routing formulations assume the opposite.

5. **Recharge is focused, not diffuse.** In the Cuvelai the SASSCAL field programme measured direct recharge on vegetated deep sheet sands at ~9–20 mm/yr, but recharge under depressions and iishana channels reaching 12.5–67 mm in a single season — the water arrives where it ponds, not where it falls. Uniform "percentage of rainfall" recharge is the single most common dryland modelling error.

6. **Storage is old.** Deep aquifers may be palaeowater recharged under wetter Pleistocene climates, or "semi-fossil" — receiving recharge, but at rates so low that abstraction is effectively mining. The Ohangwena II (KOH-2) aquifer at 220–300 m depth is estimated to receive **less than 1% of mean annual precipitation** as recharge, amounting to only a few million cubic metres a year across the whole basin — that number, not the storage volume, is the sustainable yield.

7. **Salinity is a live process, not a boundary condition.** Where the water table is shallow and evaporation strong, capillary rise concentrates salts. Shallow groundwater in Ohangwena runs 50–1200 µS/cm; 100 km west in Omusati the same shallow aquifers run 140–11,450 µS/cm and roughly 70% of hand-dug wells are unfit for drinking on sulphate alone.

8. **The data are sparse and the events are rare.** Gauged records are short, gappy and biased against extremes. Flood-frequency fitting to 15 years of intermittent record in a basin whose floods are driven by decadal wet phases is a statement of faith, not a calculation.

## How to use this domain

- `01` education and registration routes into the profession.
- `02` the standard coursework and the equations you will actually use.
- `03` **the key file** — arid-zone process hydrology.
- `04` Namibia, the Cuvelai and the Ohangwena aquifer system in detail.
- `05`–`06` practical supply, harvesting, stormwater and drainage engineering for a site.
- `07`–`08` measurement, instruments and a procurement register.
- `09` modelling and software.
- `10` what is genuinely new in 2025–2026.
- `11` books, courses and data portals, with free items flagged.

## Sources

- [Hydrology — overview](https://en.wikipedia.org/wiki/Hydrology), Wikipedia (background framing only).
- [FAO Irrigation and Drainage Paper 56, *Crop evapotranspiration*](https://www.fao.org/4/x0490e/x0490e00.htm) — the reference for ET₀.
- Himmelsbach, T., Beyer, M., Wallner, M., Grünberg, I. & Houben, G. (2018) [*Deep, semi-fossil aquifers in southern Africa*](https://www.biodiversity-plants.de/biodivers_ecol/article_meta.php?DOI=10.7809/b-e.00306), Biodiversity & Ecology 6: 66–74. doi:10.7809/b-e.00306 (open access).
- Wanke, H. et al. (2018) [*The long road to sustainability: integrated water quality and quantity assessments in the Cuvelai-Etosha Basin*](https://www.biodiversity-plants.de/biodivers_ecol/article_meta.php?DOI=10.7809/b-e.00307), Biodiversity & Ecology 6: 75–83. doi:10.7809/b-e.00307 (open access).
- [NASA POWER climatology and monthly APIs](https://power.larc.nasa.gov/), point 17.566°S 17.216°E (Okongo), retrieved 2026-08-25; ET₀ computed by the FAO-56 Penman-Monteith and Hargreaves-Samani methods from those data.

## Open questions

- Gauge-based long-term rainfall statistics for Okongo/Eenhana specifically (Namibia Meteorological Service or SASSCAL station data) have not been obtained; all rainfall statistics here are reanalysis-derived.
- No verified A-pan evaporation map value for Ohangwena has been located; the ET₀ figures are computed rather than measured.
