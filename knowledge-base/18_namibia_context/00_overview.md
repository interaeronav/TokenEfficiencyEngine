---
id: namibia.overview
title: Namibian context for building — overview
domain: 18_namibia_context
tags: [namibia, ohangwena, okongo, context, climate, geology, history, architecture, culture, economy, infrastructure]
jurisdiction: namibia
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Okongo", url: "https://en.wikipedia.org/wiki/Okongo", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Ohangwena Region", url: "https://en.wikipedia.org/wiki/Ohangwena_Region", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Regions of Namibia (2023 census table)", url: "https://en.wikipedia.org/wiki/Regions_of_Namibia", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Atlas of Namibia, Chapter 3 — Climate", url: "https://atlasofnamibia.online/chapter-3", publisher: "Namibia Nature Foundation / Atlas of Namibia Team", accessed: 2026-08-25}
  - {title: "Atlas of Namibia, Chapter 4 — Water", url: "https://atlasofnamibia.online/chapter-4/groundwater-a-vital-hidden-resource", publisher: "Atlas of Namibia", accessed: 2026-08-25}
  - {title: "Vast aquifer found in Namibia could last for centuries", url: "https://www.bbc.com/news/science-environment-18875385", publisher: "BBC News", accessed: 2026-08-25}
  - {title: "PVGIS v5.2 monthly irradiation and TMY, 17.567°S 17.217°E", url: "https://re.jrc.ec.europa.eu/api/v5_2/MRcalc?lat=-17.567&lon=17.217&horirrad=1&startyear=2016&endyear=2020&outputformat=json", publisher: "European Commission Joint Research Centre", accessed: 2026-08-25}
related: [namibia.geography, namibia.climate, namibia.geology_soils, namibia.history, namibia.architecture, namibia.building_culture, namibia.economy, namibia.infrastructure, namibia.climate_responsive_design, logistics.overview]
unit_system: SI
---

# Namibian context for building — overview

**Summary.** This domain is the background knowledge a designer or agent needs before making a single decision about a building in Namibia — and specifically in **Okongo, Ohangwena Region** (17°34′S, 17°13′E, about 1 150 m above sea level). It covers physical geography, climate, geology and soils, history, architecture, building culture, the economy and construction market, infrastructure, and a synthesis of climate-responsive design rules. The governing facts are simple to state and hard to design around: a **hot semi-arid (Köppen BSh)** climate with roughly **590 mm of rain a year at Eenhana**, almost all of it between November and April; **potential evapotranspiration an order of magnitude greater than rainfall**; **about 2 275 kWh/m²/yr of global horizontal irradiance**; deep, structureless **Kalahari aeolian sand** underfoot; a landscape with essentially **no stone, no gravel and no surface water**; and a settlement pattern of dispersed family homesteads on **communal land allocated by Traditional Authorities**, not freehold plots.

## Key facts

| Parameter | Value | Source / note |
|---|---|---|
| Okongo coordinates | **17°34′S, 17°13′E** | Wikipedia infobox |
| Okongo elevation | **≈1 151 m** | PVGIS DEM at those coordinates |
| Okongo population (2023 census) | **3 564** | 2 236 in 2011 |
| Ohangwena Region population (2023) | **337 729** | 31.5 persons/km²; **85.5 % rural** |
| Ohangwena Region area | **10 706 km²** | Smallest-but-one region by area, third by population |
| Namibia population (2023 census) | **3 022 401** | Namibia Statistics Agency |
| Namibia area | **824 292 km²** | 34th largest country; 2nd least densely populated |
| Regional capital | **Eenhana** (16 588 people, 2023) | ~120 km west of Okongo, tarred |
| Annual rainfall, Eenhana | **590 mm** (DWD Klimatafel monthly sum) | Nearest long-record station to Okongo |
| Annual rainfall, Ondangwa | **448 mm** | 1 080 m elevation, BSh |
| Mean annual temperature, Eenhana | **22.7 °C** | Warmest month Nov 26.1 °C; coolest Jul 16.8 °C |
| Global horizontal irradiance at Okongo | **≈2 275 kWh/m²/yr (6.2 kWh/m²/day)** | PVGIS SARAH2, 2016–2020 mean |
| Aridity index (northern margin) | **0.20 or more → semi-arid** | Atlas of Namibia fig. 3.22 |
| Ohangwena II aquifer | **~70 × 40 km on the Namibian side, ~300 m deep, artesian, water up to 10 000 years old** | BGR / BBC 2012 |
| Currency | **Namibian dollar (N$), pegged 1:1 to the South African rand** | Rand is also legal tender |
| Latitude for solar design | **17.57°S** — noon sun 49° (21 Jun) to 84° (21 Dec) | Sun passes *south* of the zenith ~12 Nov – 31 Jan |

> ⚠️ Nothing in this domain is a substitute for a site visit, a trial pit and a local Traditional Authority conversation. The Kalahari sand profile, the depth to the water table, and the specific land rights attaching to a plot all vary over hundreds of metres.

## Why this context governs building decisions

### 1. The climate sets the form before the brief does

Northern Namibia is not simply "hot". It is **hot, dry, intensely sunny, and strongly seasonal**, with a short violent wet season and a long dry one. That combination has four consequences that override almost every stylistic preference:

- **Solar control beats insulation.** At 2 275 kWh/m²/yr, the horizontal roof is the dominant heat gain path. A poorly shaded, uninsulated metal roof will drive indoor temperatures well above the outdoor maximum. Roof design is the single highest-leverage decision.
- **The diurnal swing is the free cooling resource.** The Atlas of Namibia records daily temperature ranges of **18–20 °C at Ondangwa in the dry winter months**, dropping to about **12 °C during peak rain months**. That swing is what makes thermal mass work — but only in the dry season. In February, when the swing collapses and humidity is high, mass stops helping and ventilation has to do the work.
- **Water arrives in a few months and then does not.** Roofs must shed and, ideally, harvest; the ground must drain; and the construction programme has to respect a wet season that turns unsealed access to mud.
- **Evaporation is extreme.** Potential evapotranspiration is *an order of magnitude* higher than rainfall. Concrete and mortar dry far faster than in temperate practice — curing is not a formality here, it is the difference between a slab that works and one that crazes and dusts.

See `02_climate-and-weather.md` for the numbers and `09_climate-responsive-design-for-namibia.md` for the design response.

### 2. The ground is sand, and sand behaves differently

Ohangwena sits on the **Owambo (Etosha) Basin**, blanketed by the Cenozoic **Kalahari Group**: tens to hundreds of metres of aeolian quartz sand (Arenosols), with **calcrete** horizons at depth and **saline/sodic soils (Solonchaks, Solonetz)** in and around the *iishana* channels. What this means practically:

- Cohesionless sand gives **no vertical trench face** — excavations batter back, and deep strip footings become wide, expensive and unsafe without support.
- Bearing capacity is modest but usually adequate for one and two storeys **if compaction is controlled**; loose aeolian sand at low relative density settles under load.
- There is **no natural aggregate on site**. Concrete stone and crusher sand are imported from far away; **calcrete** is the one locally-won material, and it is the backbone of Namibian road and base-course practice.
- Groundwater is a real hazard *and* a real resource: the deep **Ohangwena II** aquifer is fresh and artesian, while the shallower aquifer above it is **saline**. Boreholes drilled carelessly can cross-contaminate the two.

See `03_geology-and-soils.md`.

### 3. Land and labour are social before they are legal or commercial

In Ohangwena, **85.5 % of people live rurally** on **communal land**, which vests in the State and is administered through Traditional Authorities and Communal Land Boards, not through title deeds. A house is not built by a contractor for a client on a serviced erf; it is built incrementally, by an extended family, often over years, funded largely by **remittances from wage earners elsewhere**, on a homestead allocation whose boundaries are social facts before they are surveyed ones.

This changes: how you phase a design; what "finished" means; who has to agree; what skills are actually available on site; and why an incrementally extensible plan is worth more than an efficient one-shot plan. See `06_building-culture-and-society.md`.

### 4. History explains the building stock you see

Namibia's built environment is legible as a sequence: precolonial timber-and-earth homestead traditions; German colonial masonry (1884–1915) with its Wilhelminian and Jugendstil set-pieces at Windhoek, Swakopmund and Lüderitz; a South African administrative period (1915–1990) of pragmatic modernism, mission stations and — in the north — a militarised landscape of bases, airstrips and tarred strategic roads; and a post-independence period of state monuments, institutional campuses and a housing crisis. Okongo's own tarred road and airstrip are partly artefacts of that military period. See `04_history-of-namibia.md` and `05_namibian-architecture.md`.

### 5. The market is small, imported and rand-priced

Namibia's economy is around **US$14.7 bn nominal (2025 IMF forecast)**, with mining ~14 % of GDP, a tertiary sector of ~55 %, and manufacturing ~10 % that is explicitly constrained by "a small domestic market, dependence on imported goods... and subsidised competition from South Africa". Almost every manufactured building product is either South African or landed through Walvis Bay. The N$ is pegged 1:1 to the rand, so **South African input inflation is Namibian input inflation**, with no exchange-rate buffer. See `07_economy-and-construction-market.md`.

### 6. Services are thin and getting thinner with distance

Ohangwena had only **20.7 % of households using electricity for lighting** at the last detailed count, the northern distributor is **NORED**, bulk water is **NamWater** with rural supply run by the Ministry's rural water directorate, and mobile coverage (MTC, Telecom Namibia) is good in the villages and patchy between them. Off-grid solar in this irradiance regime is not a fallback — it is often the rational primary supply. See `08_infrastructure-and-services.md`.

## How to read this domain

| File | What it answers |
|---|---|
| `01_geography-and-regions.md` | Where is this place, what is around it, what is the landform and the settlement pattern |
| `02_climate-and-weather.md` | **The key file.** Every climate variable, with an explicit building implication for each |
| `03_geology-and-soils.md` | What is under the building, what can be dug, where water comes from |
| `04_history-of-namibia.md` | Why the country and the region are as they are |
| `05_namibian-architecture.md` | What has been built here and what each tradition knows about this climate |
| `06_building-culture-and-society.md` | Who builds, on what land, with whose money and labour |
| `07_economy-and-construction-market.md` | What things cost and why, and what the market can supply |
| `08_infrastructure-and-services.md` | Power, water, telecoms, roads, fuel, waste |
| `09_climate-responsive-design-for-namibia.md` | The synthesis: quantified design rules for 17.6°S |

## Confidence and gaps

Data quality declines sharply as you move from the national scale to Okongo. National climate, geology and economic figures are well sourced. Regional figures for Ohangwena are reasonable. **Okongo-specific meteorological data does not exist in any public station record**; where this domain gives Okongo climate numbers they are either (a) from the nearest station with a published record — **Eenhana** (≈120 km west, Deutscher Wetterdienst) or **Ondangwa** (≈180 km west-southwest) — or (b) derived from **reanalysis** (PVGIS/ERA5/SARAH2) at Okongo's coordinates, which is stated explicitly each time. Reanalysis is good for radiation and seasonal shape, and poor for extremes, calms and rainfall intensity.

## Sources

- [Okongo — Wikipedia](https://en.wikipedia.org/wiki/Okongo)
- [Ohangwena Region — Wikipedia](https://en.wikipedia.org/wiki/Ohangwena_Region)
- [Regions of Namibia (2023 census statistics) — Wikipedia](https://en.wikipedia.org/wiki/Regions_of_Namibia)
- [Eenhana — Wikipedia (Deutscher Wetterdienst Klimatafel weather box)](https://en.wikipedia.org/wiki/Eenhana)
- [Ondangwa — Wikipedia](https://en.wikipedia.org/wiki/Ondangwa)
- [Atlas of Namibia, Chapter 3 — Climate](https://atlasofnamibia.online/chapter-3)
- [Atlas of Namibia — Evaporation and aridity](https://atlasofnamibia.online/chapter-3/evaporation-and-aridity)
- [Atlas of Namibia — Groundwater, a vital hidden resource](https://atlasofnamibia.online/chapter-4/groundwater-a-vital-hidden-resource)
- [BBC News — Vast aquifer found in Namibia could last for centuries (2012)](https://www.bbc.com/news/science-environment-18875385)
- [Economy of Namibia — Wikipedia](https://en.wikipedia.org/wiki/Economy_of_Namibia)
- [Water supply and sanitation in Namibia — Wikipedia](https://en.wikipedia.org/wiki/Water_supply_and_sanitation_in_Namibia)
- [PVGIS v5.2 API (JRC) — monthly irradiation and TMY at 17.567°S, 17.217°E](https://re.jrc.ec.europa.eu/api/v5_2/MRcalc?lat=-17.567&lon=17.217&horirrad=1&startyear=2016&endyear=2020&outputformat=json)

## Open questions

- Okongo has no published meteorological station record; all site-specific climate figures here are interpolated or reanalysis-derived.
- The share of Ohangwena households now connected to grid electricity post-2023 census has not been verified; the 20.7 % figure is from earlier census reporting.
- Current NORED and NamWater tariff schedules and connection fees were not retrievable and are marked `needs-verification` in `08_infrastructure-and-services.md`.
- Depth to the shallow (saline) water table specifically at Okongo is unverified.

