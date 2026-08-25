---
id: namibia.climate
title: Namibian climate and weather, with the Ohangwena/Okongo profile
domain: 18_namibia_context
tags: [namibia, climate, weather, ohangwena, okongo, eenhana, ondangwa, rainfall, temperature, humidity, wind, solar, evaporation, enso, drought, building-implications]
jurisdiction: namibia
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Atlas of Namibia — Rainfall patterns", url: "https://atlasofnamibia.online/chapter-3/rainfall-patterns", publisher: "Atlas of Namibia", accessed: 2026-08-25}
  - {title: "Atlas of Namibia — Temperature", url: "https://atlasofnamibia.online/chapter-3/temperature", publisher: "Atlas of Namibia", accessed: 2026-08-25}
  - {title: "Atlas of Namibia — Evaporation and aridity", url: "https://atlasofnamibia.online/chapter-3/evaporation-and-aridity", publisher: "Atlas of Namibia", accessed: 2026-08-25}
  - {title: "Atlas of Namibia — Humidity", url: "https://atlasofnamibia.online/chapter-3/humidity", publisher: "Atlas of Namibia", accessed: 2026-08-25}
  - {title: "Atlas of Namibia — Wind", url: "https://atlasofnamibia.online/chapter-3/wind", publisher: "Atlas of Namibia", accessed: 2026-08-25}
  - {title: "Atlas of Namibia — Sunshine hours and radiation", url: "https://atlasofnamibia.online/chapter-3/sunshine-hours-and-radiation", publisher: "Atlas of Namibia", accessed: 2026-08-25}
  - {title: "Atlas of Namibia — Climate change", url: "https://atlasofnamibia.online/chapter-3/climate-change", publisher: "Atlas of Namibia", accessed: 2026-08-25}
  - {title: "Klimatafel von Eenhana / Namibia", url: "https://en.wikipedia.org/wiki/Eenhana", publisher: "Deutscher Wetterdienst, via Wikipedia weather box", accessed: 2026-08-25}
  - {title: "Ondangwa climate chart", url: "https://en.wikipedia.org/wiki/Ondangwa", publisher: "World Climate Guide, via Wikipedia", accessed: 2026-08-25}
  - {title: "PVGIS v5.2 TMY and monthly irradiation at 17.567°S 17.217°E", url: "https://re.jrc.ec.europa.eu/api/v5_2/tmy?lat=-17.567&lon=17.217&outputformat=json", publisher: "European Commission Joint Research Centre", accessed: 2026-08-25}
related: [namibia.overview, namibia.geography, namibia.climate_responsive_design, namibia.geology_soils]
unit_system: SI
applies_to: [ohangwena, okongo, northern-namibia]
---

# Namibian climate and weather, with the Ohangwena/Okongo profile

**Summary.** Namibia is the driest country in sub-Saharan Africa, second in aridity within Africa only to the Sahara. Rainfall rises from **under 20 mm/yr within 40 km of the coast to over 650 mm/yr in the north-east**, and the country average is about **350 mm**. Rain is convective, summer-only, concentrated in a few intense months, and highly variable from year to year. **Potential evapotranspiration exceeds rainfall by an order of magnitude everywhere.** Northern Ohangwena sits at the wet end of this gradient — **Eenhana records 590 mm/yr and a mean annual temperature of 22.7 °C** — with the highest humidity, the highest annual mean temperatures, and the *lowest* solar irradiance in the country, because the summer cloud that brings the rain also cuts the sun. Every one of these facts translates into a building decision, and this file makes each translation explicit.

## Key facts

| Parameter | Value | Source |
|---|---|---|
| National average rainfall | **~350 mm/yr** | Wikipedia / Atlas |
| Rainfall within 40 km of coast | **<20 mm/yr** | Atlas 3.07 |
| North-east rainfall | **>650 mm/yr** | Atlas 3.07 |
| Half the country receives | **<350 mm/yr** | Atlas ch.3 |
| Eenhana annual rainfall | **590.0 mm** (sum of DWD monthly means) | Deutscher Wetterdienst |
| Ondangwa annual rainfall | **448 mm** | Wikipedia/World Climate Guide |
| Rain days (≥1 mm), coastal towns | **<7 per season** | Atlas 3.09 |
| Rain days (≥1 mm), Katima Mulilo | **~64 per season** | Atlas 3.09 |
| Namibia's official temperature record | **45.5 °C, Gobabeb, March 2013** | Atlas 3.16 |
| Ondangwa record maximum | **43.2 °C, 28 October 2020** | Wikipedia |
| Daily temperature range, Ondangwa | **18–20 °C** dry season, **~12 °C** peak rain months | Atlas 3.17 |
| Relative humidity, driest months, east of escarpment | **<20 %** (measured 14h00) | Atlas 3.19 |
| Relative humidity, wettest months, northern Namibia | **~80 %** (measured 08h00) | Atlas 3.19 |
| Sunshine hours, inland | **8–10 h/day** (Windhoek); fewer in northern rainy months | Atlas 3.13 |
| Aridity index, far north/north-east | **≥0.20 → semi-arid** | Atlas 3.22 |
| Frequency of calms at Ondangwa (<0.5 m/s) | **Jan 55 %, Apr 68 %, Jul 63 %, Oct 53 %** | Atlas 3.04 |
| Okongo global horizontal irradiance | **≈2 275 kWh/m²/yr; 6.23 kWh/m²/day** | PVGIS SARAH2 2016–2020 |
| Projected rainfall change by 2040–2060 (RCP 8.5) | **−9 %** annual; **−8 %** wet season; **−20 %** dry season | Atlas 3.23 |

> ⚠️ There is **no published meteorological station record for Okongo**. Everything below labelled "Okongo" is either the nearest station (Eenhana, ~120 km west, or Ondangwa, ~180 km WSW) or **reanalysis** (PVGIS TMY built on ERA5 and SARAH2) evaluated at Okongo's coordinates. Reanalysis reproduces seasonal shape and radiation well and **underestimates extremes and calms**. Do not use it for design wind loading or for rainfall intensity.

---

## 1. Climate zones and why Namibia is dry

Namibia lies under the descending limb of the **South Atlantic Anticyclone** to the west and the **Botswana Anticyclone** to the east. Air subsiding in these cells warms and dries as it spreads across southern Africa, producing the cloudless skies that dominate **May to September**. In summer the **Intertropical Convergence Zone (ITCZ)** shifts south, pushing the anticyclones aside and admitting moist tropical air from Angola and the Congo — which is the source of essentially all Namibian rain. The **cold Benguela Current** reinforces the western high and suppresses coastal convection, giving fog instead of rain.

Köppen zones run west to east: **BWh/BWk** (hot/cold desert) along the coast and Namib, **BSh** (hot semi-arid) across the plateau and the north, grading to **BSh/Aw** in the far north-east. **Ondangwa and Eenhana are both classified BSh**, and Okongo is in the same zone.

Aridity index (rainfall ÷ potential evapotranspiration): the coastal belt is **hyper-arid**; the bulk of the country is **arid (0.02–0.20)**; only the far northern and north-eastern margins and the Tsumeb area reach **≥0.20, i.e. semi-arid**. Ohangwena is at that wettest margin.

**Building implication.** Design for a **hot dry** climate for eight months and a **warm humid** climate for four. A single strategy will fail one of the two seasons. Specifically: thermal mass and night flushing work superbly from May to October and stop working in February.

---

## 2. Rainfall

### National pattern
- Average annual rainfall is computed on a **rainfall year of 1 July to 30 June**, not a calendar year. Contract programmes and rainfall data should use the same convention.
- The gradient is steep: **<20 mm** within 40 km of the coast; **>650 mm** in the north-east.
- Rain is overwhelmingly **convective** — heat drives moist air up into dense cumulus, which discharges quickly and locally. There is a little **orographic** enhancement around Otavi, Tsumeb and Grootfontein and a little **frontal** winter rain in the far south-west.
- From **October to February** rain spreads across the country from the east and north, then **retreats in March and April**. In the north-east rains start earlier and peak **December to February**; in the south and west they start later and peak from January, with **February and March** the wettest months over the southern and western thirds.
- Rain-day frequency rises sharply eastwards: fewer than **7 rain days/season** on the coast, about **33** at Opuwo (with 285 mm), about **64** at Katima Mulilo.

### The two-season description
Namibia is often described as having a **small rainy season September–November** and a **main rainy season February–April**. This is a real and useful pattern for the country as a whole and for the central plateau. **In the far north it is less pronounced**: the Eenhana and Ondangwa records show a single broad wet season running November through April with the peak in **January–February**, and only a trace of early-season rain in September–October.

### Variability
Rainfall is described by the Atlas as "low, variable and unpredictable" for most of the country. West of the escarpment, "years may go by without a drop of rain" and average figures are described as "not terribly meaningful". Even in the north, an individual season can deliver half or double the mean.

> **Building implications of rainfall.**
> - **Roofs:** design for **short-duration, high-intensity convective downpours**, not for total volume. Gutters, downpipes and overflow paths must handle a burst, not an average. Minimum practical pitch for profiled sheet is not the issue — **fixings, laps and flashings under wind-driven rain** are.
> - **Ground:** almost all rain falls in four months onto sand that cannot shed it laterally. Provide a **wide, falling apron/hardstanding around the building**, and get roof water **away from the foundation zone**, not just off the roof.
> - **Construction season:** the weather-tight envelope should be complete before **late November**. Earthworks, foundations and slabs are best done **May–September**.
> - **Rainwater harvesting is worth doing** here in a way it is not further south: 590 mm on 100 m² of roof is ~59 m³/yr gross, ~47 m³ after a conservative 0.8 runoff coefficient and first-flush losses. See §12.
> - Use the **1 July–30 June rainfall year** in any programme or water-balance calculation.

---

## 3. The oshana flooding phenomenon

Distinct from local rainfall. The **Cuvelai** *iishana* fill from rain falling in the Angolan highlands as well as locally, and drain slowly south toward the Omadhiya lakes and Etosha. Because channel beds are impermeable clay or saline soil, **infiltration is limited and water spreads laterally rather than sinking**.

Over 1941–2021, medium or major flows (*omafundja*) occurred in **45 % of years** — "almost every second year" — and major floods at an average interval of about **six years**.

> **Building implications of oshana flooding.**
> - The hazard is **broad, shallow, slow, long-duration inundation**, not fast river flow. Depths are typically low but persistence is weeks.
> - **Site on the interfluve, not the channel.** This is what the traditional homestead pattern already does. If a site is anywhere near an *oshana*, obtain local knowledge of the 2008/2009 and 2011 flood extents — those are the reference events in living memory.
> - **Raise the floor level.** A minimum **300–450 mm** finished floor above surrounding ground is a cheap insurance in the Cuvelai; more if local flood history warrants it.
> - Expect a **seasonally raised water table** and design foundations, septic systems and soakaways accordingly. A soakaway that works in September may be submerged in March.
> - Flooding also cuts access. The freight programme must not depend on February–April deliveries.

---

## 4. Drought cycles and ENSO

Drought is not an anomaly in Namibia; it is part of the distribution. The country has recurring drought emergencies (2013, 2015/16 and 2019 are recent declared examples), and the water sector plans around them.

**ENSO signal:** *El Niño* events "tend to increase the probability that the country will experience drier conditions"; *La Niña* "increases the likelihood of wetter conditions in Namibia". This is a probability shift, not a forecast, but it is strong enough to be worth watching when planning a construction season or a water supply.

**Climate change (RCP 8.5, 2040–2060 vs 1960–1990):** total annual rainfall across Namibia is projected to **decrease by nearly 9 %**; **all months drier**; wet season (Oct–Apr) **−8 %**, dry season (May–Sep) **−20 %**. Temperature increases and the trend is described as certain.

> **Building implications.**
> - Size **rainwater storage against a bad year**, not the mean. A tank sized on 590 mm is a tank that runs dry in a 300 mm year.
> - Assume the **cooling load will grow** over the life of the building. Passive headroom designed in now is cheaper than retrofit.
> - Assume **groundwater will be drawn on harder** during droughts — see the Ohangwena aquifer discussion in `03_geology-and-soils.md`.

---

## 5. Temperature

### National
- Average maximum temperatures in the hottest months are **above 30 °C everywhere east of the escarpment**; the hottest parts (far south and south-east) exceed **36 °C** average maximum.
- **July is the coolest month** over most of the country. Average minima in the coldest months are **below 10 °C in most areas**, below **2 °C** along the southern escarpment, and generally **above 6 °C inland and over much of northern Namibia**.
- Frost is common in the south in winter; **extremes below −10 °C** occur under winter frontal incursions, and snow occasionally falls (e.g. Aus). **Frost is not a normal design consideration in Ohangwena.**
- Annual temperature range (hottest month max minus coldest month min) is **22 °C or less** on the coast and **above 32 °C** in the south-east.
- **The highest annual average temperatures in Namibia are in the central-northern and north-eastern areas** along the northern escarpment — i.e. the Ohangwena/Kavango belt. Humid air and cloud retain heat day and night.

### Diurnal range
- Coastal towns: **<10 °C**, consistent year-round.
- Windhoek: **~15 °C**, little seasonal variation.
- **Ondangwa and Rundu: 18–20 °C in the dry winter months, dropping to ~12 °C in peak rain months.**

> **Building implications of temperature.**
> - The **18–20 °C dry-season swing** is the resource that makes **thermal mass + night ventilation** the correct strategy from about April to October.
> - The **~12 °C wet-season swing plus high humidity** is why the same mass becomes a liability in January–March. The building must be able to **switch modes**: openable, cross-ventilated, shaded, with air movement over occupants.
> - **No frost design is required at Okongo**, but winter nights below 10 °C are normal and a lightweight uninsulated building will be genuinely cold at 06h00 in July. Comfort in this climate is a two-tailed problem.
> - Peak design temperature for Ohangwena should be taken from **October**, not January — the hottest month here is at the end of the dry season, before the rains break.

---

## 6. Humidity

- East of the escarpment, average relative humidity in the **least humid months is under 20 %** (measured at 14h00).
- In the **most humid months**, values reach **around 80 % in northern Namibia** (measured at 08h00) and 50–60 % in the south.
- The lowest humidity months inland are **August, September and October** — warming air with no moisture yet.
- Rundu (a good analogue for Okongo) ranges **50–70 % at 08h00** and **20–40 % at 14h00**.

> **Building implications of humidity.**
> - **Evaporative cooling is highly effective from August to November** (RH <20 % at midday) and largely ineffective in February (RH high, air near saturation in the morning).
> - **Timber moves.** Going from 15 % RH in September to 80 % RH in February is a severe cycle. Specify joinery with movement gaps, avoid wide unrestrained solid panels, seal all six faces of doors, and acclimatise material on site.
> - **Condensation risk** exists in the wet season under uninsulated metal roofs during clear nights — night-sky radiation cools the sheet below dew point and it drips. A **ventilated roof space with a sarking/anti-condensation membrane** solves this cheaply.
> - Low winter humidity plus high radiation means **drying is fast**: paints, screeds and renders skin over before they cure. Plan for shading and misting of new work.

---

## 7. Wind

- Offshore and coastal winds are strong and consistent: south-easterly, southerly and south-westerly, driven by the South Atlantic Anticyclone and the Coriolis deflection. The **Lüderitz–Orange River stretch is the windiest area in southern Africa**.
- **Over the land, wind speeds are generally lower, directions more variable, and the proportion of calms much higher.**
- **In winter the Botswana Anticyclone drives easterly airflow** across much of the country. These "**East Winds**" (Berg winds) descend the escarpment, heat by compression, and blow hot and dusty toward the coast.
- Inland easterly winds have shaped the northern Namibian landscape over millennia — blowing alluvial sand out of dry drainage courses into the parallel vegetated dunes of the north, and scouring silts from Cuvelai channels to deposit them just west of the channels.

**Frequency of calms (<0.5 m/s), station data (Atlas fig. 3.04):**

| Station | Jan | Apr | Jul | Oct |
|---|---|---|---|---|
| **Ondangwa** | **55 %** | **68 %** | **63 %** | **53 %** |
| Rundu | 56 % | 59 % | 62 % | 49 % |
| Windhoek | 42 % | 37 % | 28 % | 34 % |
| Gobabis | 36 % | 51 % | 49 % | 36 % |
| Walvis Bay | 17 % | 17 % | 18 % | 13 % |
| Lüderitz | 9 % | 14 % | 14 % | 8 % |

**Direction at Okongo (PVGIS TMY, reanalysis):** predominantly **easterly** — E 22.9 %, ENE 18.6 %, ESE 8.9 %, NE 8.8 %; i.e. **~59 % of hours from the NE–ESE quadrant**. Mean 10 m wind speed **2.1–3.5 m/s** by month, highest in July.

> ⚠️ **The single most important wind fact for building at Okongo: the wind is often not there.** More than half of all observations at Ondangwa are calm. **Do not design a building that depends on cross-ventilation from a prevailing breeze.** It must also work by **stack effect** — high-level outlets, roof ventilators, tall spaces, courtyards — which works when the wind does not.

> **Other building implications of wind.**
> - Orient openable façades to catch the **easterly** flow when it exists. An east-facing opening for air and a west-facing opening for exhaust is the natural pairing — but east and west are also the worst solar façades, so this must be resolved with deep verandas and vertical shading rather than by moving the openings.
> - **Wind loading:** Namibia is not a high-wind country inland, but light sheet roofs on long spans in a thunderstorm downdraught are the classic local failure. Design for **uplift**, not just for downward load; use through-fixings with proper washers, close fixing centres at eaves, verges and ridge, and hold the roof down to the walls with continuous straps to the foundation. Thunderstorm gust fronts and occasional dust-devil/microburst events are the real hazard, and they are not represented in reanalysis mean wind speeds.
> - Prevailing easterlies plus fine sand means **wind-driven dust from the east**: put stores, intake vents and clean-work areas on the western/leeward side.

---

## 8. Solar radiation

Namibia receives some of the highest solar irradiance on earth, and the Atlas notes the general **inverse relationship between irradiance and rainfall** — the arid south and west get the most, and near the coast irradiance drops sharply where fog and low cloud shield the surface. **Northern Namibia is therefore at the lower end of the Namibian range and still very high by world standards.**

Sunshine duration: **8–10 h/day at Windhoek**; only **5–7 h/day** in the foggy central coastal areas; and in the north and north-east, sunshine hours **decrease measurably during the rainy months October–April** because of cloud.

**Okongo global horizontal irradiance (PVGIS, SARAH2 satellite record, 2016–2020 mean):**

| Month | kWh/m²/month | kWh/m²/day |
|---|---|---|
| Jan | 208.0 | 6.71 |
| Feb | 182.3 | 6.51 |
| Mar | 181.0 | 5.84 |
| Apr | 175.9 | 5.86 |
| May | 171.5 | 5.53 |
| Jun | 157.0 | 5.23 |
| Jul | 170.2 | 5.49 |
| Aug | 190.2 | 6.14 |
| Sep | 206.6 | 6.89 |
| Oct | 214.1 | 6.91 |
| Nov | 207.7 | 6.92 |
| Dec | 210.3 | 6.79 |
| **Year** | **≈2 275** | **6.23 average** |

Note the shape: the **peak is September–November**, not midsummer, because December–March cloud offsets the higher sun. The **minimum is June (5.23 kWh/m²/day)** — and even that minimum is higher than the *annual average* of most of Europe.

**Sun geometry at 17.57°S** (computed):

| Date | Solar declination | Noon altitude | Noon sun is | Sunrise azimuth from N | Day length |
|---|---|---|---|---|---|
| 21 Jun | +23.4° | **49.0°** | North | 65.3° (ENE) | 10.95 h |
| 21 Sep | +0.7° | 71.7° | North | 89.2° (E) | 11.97 h |
| 15 Oct | −8.5° | 80.9° | North | 98.9° (E by S) | 12.36 h |
| **12 Nov** | −17.6° | **90.0°** | **Overhead** | — | ~12.8 h |
| 21 Dec | −23.4° | **84.1°** | **South** | 114.7° (ESE) | 13.05 h |
| **31 Jan** | −17.6° | **90.0°** | **Overhead** | — | ~12.9 h |
| 21 Mar | +0.2° | 72.2° | North | 89.8° (E) | 11.99 h |

Two consequences that catch designers from higher latitudes:
1. **The sun passes overhead twice a year (≈12 November and ≈31 January) and is *south* of the zenith at noon for the ~80 days between.** South-facing walls therefore receive direct midday sun in high summer.
2. **Day length varies by only about two hours** across the year — matching the Atlas's statement that Ondangwa's June–December day-length difference is approximately two hours.

> **Building implications of solar radiation.**
> - The **roof is the dominant heat gain surface** — it receives close to the full 6.2 kWh/m²/day. Roof strategy outranks wall strategy, glazing strategy and everything else.
> - Use **high-albedo roof finishes** and a **ventilated roof cavity**. A light-coloured, ventilated, insulated roof is the highest-value intervention available in this climate.
> - **North façades are easy to shade** (winter noon 49°, equinox 72°) with a modest horizontal overhang. **East and west façades are hard** — low sun, high intensity, long duration in summer. Minimise east/west glazing; shade it with deep verandas and vertical/eggcrate devices, or with trees.
> - **Do not assume the south façade is safe.** Between mid-November and end-January the noon sun is south of vertical, and south walls take direct sun in the early morning and late afternoon from October to February (sunrise azimuth reaches 114.7° — i.e. 24.7° south of due east). South glazing still needs an overhang, just a shallower one.
> - The **September–November irradiance peak coincides with the pre-rain temperature peak**. That is the design-critical period for overheating: hot, cloudless, low humidity, sun near vertical, ground bare and reflective.
> - **Off-grid PV is exceptionally viable.** 2 275 kWh/m²/yr with a seasonal minimum only 24 % below the annual mean means small seasonal over-sizing. See `08_infrastructure-and-services.md`.
> - **UV degradation is severe.** Specify UV-stable plastics, exterior-grade sealants, and expect exposed timber, PVC rainwater goods, geotextiles and unshaded paint finishes to fail early. This is a real maintenance and specification issue, not a footnote.

---

## 9. Dust, sand, hail and lightning

- **Dust and sand:** the ground is fine aeolian quartz sand with almost no cohesion when dry, mobilised at low wind speeds and by every vehicle. It penetrates sliding door tracks, hinges, bearings, filters, switchgear and any horizontal detail. The Atlas notes heat "accentuated by sharp reflection off sparsely vegetated pale soils and dry, dusty air".
- **Hail:** occurs with severe convective storms in the summer season. Frequency in northern Namibia is low but non-zero. `needs-verification` — no station hail-day frequency for Ohangwena was located.
- **Lightning:** convective summer storms over the northern regions produce frequent lightning. Namibia's north-east has among the country's highest flash densities. `needs-verification` — no flash-density figure for Ohangwena was located.
- **Tropical cyclones:** Namibia is on the Atlantic side of the continent and is **not exposed to tropical cyclones**. South-east African cyclones (Mozambique Channel) do not reach here, and the South Atlantic effectively does not generate them. **Extreme wind risk is from convective downdraughts, not cyclones.**

> **Building implications.**
> - **Dust:** prefer **hinged over sliding**; use brush seals and drained/ventilated frames; keep external sills sloped and free-draining; specify IP-rated enclosures for electrical gear; put air intakes high and on the leeward (west) side; use washable finishes and avoid deep horizontal ledges.
> - **Reflected glare and radiation from bare pale sand** is a real load on the underside of verandas and on low-level glazing. **Ground-cover planting, gravel or shaded paving around the building reduces it** measurably.
> - **Lightning:** an isolated tall metal-roofed building on a flat sand plain is an obvious strike target, and **dry sand is a poor earth**. Provide a proper lightning protection system with an adequate earth electrode arrangement (multiple rods / a ring conductor, since a single rod in dry sand will not achieve a low resistance). Protect incoming power and telecoms with surge arrestors — the cost of losing an inverter and a pump in one strike far exceeds the protection cost.
> - **Hail:** use profiled steel of adequate gauge rather than thin sheet; consider hail resistance for any solar collectors.

---

## 10. The Ohangwena / Okongo climate profile

### 10a. Station data — Eenhana (17°27′57″S, 16°20′13″E; ~120 km west of Okongo; Deutscher Wetterdienst Klimatafel)

| Month | Mean temp (°C) | Rainfall (mm) |
|---|---|---|
| Jan | 25.2 | 125.1 |
| Feb | 24.7 | 133.3 |
| Mar | 24.2 | 113.5 |
| Apr | 23.7 | 48.7 |
| May | 20.5 | 9.1 |
| Jun | 16.9 | 0.2 |
| Jul | **16.8** | 0.0 |
| Aug | 19.3 | 0.0 |
| Sep | 23.5 | 1.0 |
| Oct | 25.8 | 14.2 |
| Nov | **26.1** | 58.1 |
| Dec | 25.4 | 86.8 |
| **Year** | **22.7** | **590.0** |

**Read this table carefully.** 372 mm — **63 % of the annual rain** — falls in January, February and March. From **May to October inclusive, total rainfall is 24.5 mm**, i.e. effectively nothing for six months.

### 10b. Station data — Ondangwa (17°54′49″S, 15°58′42″E; 1 080 m; Köppen BSh; ~180 km WSW)

| Month | Mean max (°C) | Mean min (°C) | Diurnal range | Rainfall (mm) |
|---|---|---|---|---|
| Jan | 32 | 19 | 13 | 106 |
| Feb | 31 | 19 | 12 | 109 |
| Mar | 28 | 19 | 9 | 92 |
| Apr | 30 | 16 | 14 | 27 |
| May | 29 | 12 | 17 | 3 |
| Jun | 26 | 8 | 18 | 0 |
| Jul | 27 | 8 | 19 | 0 |
| Aug | 30 | 10 | 20 | 0 |
| Sep | 33 | 13 | 20 | 1 |
| Oct | **34** | 17 | 17 | 11 |
| Nov | 33 | 19 | 14 | 45 |
| Dec | 33 | 19 | 14 | 53 |
| **Year** | — | — | — | **≈448** |

Record maximum **43.2 °C on 28 October 2020**. Note that the **hottest month is October**, and the largest diurnal swings (**19–20 °C**) are in **July–September**.

### 10c. Reanalysis at Okongo's coordinates (PVGIS TMY, ERA5/SARAH2, 17.567°S 17.217°E, 1 151 m)

| Month | Mean daily max (°C) | Mean daily min (°C) | Mean (°C) | Mean RH (%) | Mean wind 10 m (m/s) |
|---|---|---|---|---|---|
| Jan | 31.5 | 19.4 | 25.3 | 58.6 | 2.1 |
| Feb | 28.8 | 18.7 | 23.7 | 61.0 | 2.6 |
| Mar | 25.8 | 17.4 | 21.2 | 79.0 | 2.4 |
| Apr | 28.1 | 16.1 | 22.1 | 50.9 | 2.8 |
| May | 27.6 | 14.3 | 21.1 | 50.0 | 2.8 |
| Jun | 25.6 | 9.3 | 17.4 | 34.8 | 2.9 |
| Jul | 24.0 | 9.6 | 16.7 | 37.3 | **3.5** |
| Aug | 29.9 | 13.7 | 21.9 | 25.4 | 2.9 |
| Sep | 34.2 | 17.8 | 26.6 | **17.6** | 3.1 |
| Oct | **36.9** | 20.3 | **29.3** | **17.5** | 3.1 |
| Nov | 34.2 | 20.5 | 27.3 | 45.2 | 2.5 |
| Dec | 35.1 | 21.6 | 28.5 | 38.1 | 2.7 |
| **Year** | — | — | **23.4** | — | — |

TMY absolute maximum **40.2 °C**, absolute minimum **4.2 °C**. Wind direction predominantly **E/ENE**.

**Cross-check:** the reanalysis annual mean (23.4 °C) is 0.7 K above Eenhana's station value (22.7 °C), and the reanalysis October maximum (36.9 °C) is above Ondangwa's station October mean max (34 °C). Treat reanalysis as **warm-biased by roughly 1–3 K on maxima**; use it for shape and relative comparison, and prefer station values for absolute design temperatures.

### 10d. Consolidated design climate for Okongo

| Design quantity | Recommended value | Basis |
|---|---|---|
| Annual rainfall (design mean) | **550–600 mm** | Eenhana station; assume 300 mm in a bad year |
| Wettest month | **February (~130 mm)** | Eenhana |
| Effective dry period | **May–October (<25 mm total)** | Eenhana |
| Hottest month | **October** | Ondangwa and reanalysis agree |
| Design summer maximum | **36–38 °C**, record ~43 °C | Ondangwa station + record |
| Design winter minimum | **6–8 °C**; frost not expected | Ondangwa station |
| Mean annual temperature | **22.7 °C** | Eenhana |
| Dry-season diurnal swing | **18–20 K** | Atlas / Ondangwa |
| Wet-season diurnal swing | **~12 K** | Atlas / Ondangwa |
| RH range | **~15–20 % (Sep/Oct midday)** to **~80 % (Feb morning)** | Atlas + reanalysis |
| Annual GHI | **≈2 275 kWh/m²** | PVGIS |
| Prevailing wind | **Easterly (E/ENE)**, light; **>50 % calms** | Atlas + PVGIS |
| Design latitude | **17.57°S** | Coordinates |

---

## 11. Every climate variable, translated to a building decision

| Climate fact | Building implication |
|---|---|
| 590 mm/yr, 63 % in Jan–Mar, intense convective bursts | Generous roof overhangs and gutter capacity sized for burst intensity; hardstanding apron; roof water piped clear of the foundation zone |
| Six essentially rainless months (May–Oct) | **Build in the dry season.** Weather-tight by late November. Earthworks and concrete May–September |
| Potential evapotranspiration an order of magnitude above rainfall | **Curing is critical.** Cover, wet-cure or membrane-cure all concrete and screeds for a minimum of 7 days; shade fresh work; work early morning; do not place concrete in the October afternoon |
| Hot, cloudless, low-humidity Sep–Nov | Peak overheating season. Design shading for this, not for December |
| Sun overhead 12 Nov – 31 Jan; noon sun *south* of zenith in that window | Shade the **south** façade too; north overhangs alone are not sufficient |
| Winter noon altitude 49°N | North-facing openings admit welcome winter sun; a **0.3–0.45 × head height** overhang balances winter admission against summer exclusion |
| Sunrise azimuth 65°–115° | East and west façades take low, intense sun. Minimise glazing there; use deep verandas, vertical fins, or trees |
| GHI 2 275 kWh/m²/yr onto a horizontal roof | Ventilated, insulated, high-albedo roof is the single highest-return decision |
| Diurnal swing 18–20 K in the dry season | Thermal mass + night-purge ventilation works from April to October |
| Diurnal swing ~12 K plus 80 % RH in Feb | Mass stops helping; switch to **air movement over occupants** — large openings, ceiling fans, veranda living |
| >50 % of hours calm at Ondangwa | **Never rely on cross-ventilation alone.** Provide stack ventilation: high-level outlets, roof ventilators, courtyards |
| Prevailing easterly wind | Air intake east, exhaust west — but resolve against the east/west solar problem with shading, not by relocating openings |
| RH <20 % Aug–Nov | **Evaporative cooling is very effective in the hot pre-rain months.** Shaded water, planting, wetted courtyards all pay |
| RH swing 15 % → 80 % annually | Timber joinery must be detailed for movement; seal all faces; acclimatise on site |
| Clear night skies, high radiant loss | Night-sky cooling is a free resource; also the cause of under-roof condensation — ventilate the roof space and use an anti-condensation membrane |
| Fine mobile sand, easterly dust | Hinged rather than sliding openings; brush seals; IP-rated electrics; intakes high and leeward; no deep horizontal ledges |
| Extreme UV | UV-stable plastics and sealants; shade PVC rainwater goods; expect early failure of exposed finishes |
| Convective downdraughts, no cyclones | Design roofs for **uplift**; continuous hold-down to foundations; close fixing centres at edges |
| Lightning on a flat plain, dry sand earth | Proper LPS with an extended earth electrode arrangement; surge protection on power and comms |
| Oshana flooding in ~45 % of years | Site on interfluves; raise floor ≥300–450 mm; design for a seasonally high water table |
| Projected −9 % rainfall, −20 % dry-season rainfall by 2040–2060 | Oversize water storage; design passive cooling headroom for a hotter future |
| ENSO: El Niño → drier, La Niña → wetter | Watch the ENSO state when planning a construction season or sizing temporary water supply |

---

## Sources

- [Atlas of Namibia — Rainfall patterns](https://atlasofnamibia.online/chapter-3/rainfall-patterns)
- [Atlas of Namibia — Temperature](https://atlasofnamibia.online/chapter-3/temperature)
- [Atlas of Namibia — Humidity](https://atlasofnamibia.online/chapter-3/humidity)
- [Atlas of Namibia — Wind](https://atlasofnamibia.online/chapter-3/wind)
- [Atlas of Namibia — Sunshine hours and radiation](https://atlasofnamibia.online/chapter-3/sunshine-hours-and-radiation)
- [Atlas of Namibia — Evaporation and aridity](https://atlasofnamibia.online/chapter-3/evaporation-and-aridity)
- [Atlas of Namibia — Climate change](https://atlasofnamibia.online/chapter-3/climate-change)
- [Atlas of Namibia — The Cuvelai (flood frequency 1941–2021)](https://atlasofnamibia.online/chapter-4/the-cuvelai)
- [Eenhana — Wikipedia, weather box sourced to Deutscher Wetterdienst "Klimatafel von Eenhana / Namibia"](https://en.wikipedia.org/wiki/Eenhana)
- [Ondangwa — Wikipedia, climate chart and 43.2 °C record](https://en.wikipedia.org/wiki/Ondangwa)
- [Climate of Namibia — Wikipedia](https://en.wikipedia.org/wiki/Climate_of_Namibia)
- [PVGIS v5.2 TMY at 17.567°S, 17.217°E (JRC)](https://re.jrc.ec.europa.eu/api/v5_2/tmy?lat=-17.567&lon=17.217&outputformat=json)
- [PVGIS v5.2 monthly horizontal irradiation, 2016–2020, at 17.567°S, 17.217°E (JRC)](https://re.jrc.ec.europa.eu/api/v5_2/MRcalc?lat=-17.567&lon=17.217&horirrad=1&startyear=2016&endyear=2020&outputformat=json)

## Open questions

- `needs-verification`: **No numeric potential evapotranspiration figure in mm/yr for Ohangwena was obtained.** The Atlas map exists but its values were not readable from text; the qualitative statement "an order of magnitude higher than rainfall" is quoted. A typical Namibian A-pan figure of 2 500–3 800 mm/yr is widely cited but **was not verified here and must not be used as sourced**.
- `needs-verification`: hail-day frequency and lightning flash density for Ohangwena.
- `needs-verification`: design wind speed / basic wind velocity for northern Namibia (would normally come from SANS 10160-3 or a Namibian equivalent — see domain 03).
- `needs-verification`: rainfall intensity–duration–frequency data for northern Namibia, needed to size gutters and downpipes properly.
- `needs-verification`: the number of rain days per season specifically at Eenhana or Okongo.
- Okongo has no station record; all site figures are nearest-station or reanalysis, as labelled.

