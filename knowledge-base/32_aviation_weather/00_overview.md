---
id: aviation_weather.overview
title: Aviation weather — domain map and syllabus structure
domain: 32_aviation_weather
tags: [aviation-weather, meteorology, icao-annex-3, wmo, easa-atpl-050, faa, syllabus, met-service, domain-map]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Meteorology (ICAO Air Navigation Bureau)", url: "https://www.icao.int/safety/meteorology/Pages/default.aspx", publisher: "ICAO", accessed: 2026-08-25}
  - {title: "METAR", url: "https://en.wikipedia.org/wiki/METAR", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Terminal aerodrome forecast", url: "https://en.wikipedia.org/wiki/Terminal_aerodrome_forecast", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "SIGMET", url: "https://en.wikipedia.org/wiki/SIGMET", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Aviation Weather Center — GFA help / product list", url: "https://aviationweather.gov/gfa/help", publisher: "NOAA/NWS Aviation Weather Center", accessed: 2026-08-25}
  - {title: "Aircraft Ground Deicing (Holdover Tables)", url: "https://www.faa.gov/other_visit/aviation_industry/airline_operators/airline_safety/deicing", publisher: "FAA", accessed: 2026-08-25}
related: [aviation_weather.atmosphere, aviation_weather.circulation, aviation_weather.hazards, aviation_weather.products, aviation_weather.nwp, aviation_weather.operations, aviation_weather.climatology, aviation_weather.study, aviation_weather.cases, aviation_industry.operations]
unit_system: mixed
---

# Aviation weather — domain map and syllabus structure

**Summary.** Aviation meteorology is not general meteorology with aeroplanes bolted on. It is a legally-defined service, specified in ICAO Annex 3 / WMO Technical Regulation C.3.1, delivered by designated meteorological authorities in a fixed catalogue of products, consumed under an operator's approved procedures, and examined against a syllabus (EASA ATPL 050 in Europe, the FAA's Aviation Weather Handbook and airman certification standards in the US). This domain covers the physics, the codes, the forecasting chain, and — most importantly for a line pilot — the decision rules that convert a forecast into fuel, an alternate, a runway and a diversion. It is written for someone flying widebody long-haul out of Doha, so the Arabian Gulf, the ITCZ, the monsoon, the North Atlantic and the Asia-Pacific get disproportionate weight.

## Key facts

| Item | Value |
|---|---|
| Governing ICAO instrument | **Annex 3 — Meteorological Service for International Air Navigation** (dual-numbered as WMO Technical Regulations [C.3.1]) |
| Supporting ICAO manual | **Doc 8896 — Manual of Aeronautical Meteorological Practice** |
| WMO code manual | **WMO No. 306 — Manual on Codes** (FM 15 METAR, FM 16 SPECI, FM 51 TAF, FM 53 ARFOR etc.) |
| WMO observing manual | **WMO No. 8 — Guide to Instruments and Methods of Observation (CIMO Guide)** |
| WMO No. 49 | **Technical Regulations**; Volume II is the aeronautical volume, identical in substance to Annex 3 |
| WAFS providers | **WAFC London (Met Office)** and **WAFC Washington (NOAA/NWS)** |
| VAACs | **Nine** worldwide, under the ICAO International Airways Volcano Watch (IAVW) |
| Space weather advisory providers | **NOAA (US), ACFJ consortium, PECASUS, China–Russian Federation consortium** — ICAO service began late 2019 |
| Standard SIGMET validity | up to **4 h**; **6 h** for volcanic ash and tropical cyclone |
| TAF issue times (long TAF) | **0000, 0600, 1200, 1800 UTC**, four times daily for major aerodromes |
| European ATPL met subject | **050 Meteorology** within the 13/14-subject ATPL(A) theoretical knowledge set |
| Principal FAA text | **Aviation Weather Handbook, FAA-H-8083-28** (consolidating AC 00-6 and AC 00-45 material) |

> ⚠️ Nothing in this domain replaces your operator's Operations Manual Part A/B, the State AIP, or the specific NOTAM and MET package for the flight. Where this file and a company procedure differ, the company procedure governs.

## 1. What the domain contains

| File | Covers |
|---|---|
| `01_atmosphere-fundamentals.md` | Composition, vertical structure, ISA table, altimetry (QNH/QFE/QNE, temperature and pressure error, cold-temperature correction), density altitude, humidity, lapse rates, stability, tephigram/skew-T |
| `02_global-circulation-and-air-masses.md` | Hadley/Ferrel/Polar cells, jets, ITCZ, air masses, fronts and their cross-sections, Norwegian and conveyor-belt models, cyclogenesis, anticyclones, regional seasonal regimes |
| `03_hazardous-weather.md` | Thunderstorms, hail, lightning, downbursts, windshear, all turbulence forms, icing, volcanic ash, dust and sand, fog and low visibility, space weather |
| `04_codes-charts-and-products.md` | METAR/SPECI, TAF, SIGMET/AIRMET/GAMET, warnings, ATIS, PIREP/AIREP/AMDAR, SIGWX and wind/temperature charts, satellite, radar, lightning networks, WAFS GRIB |
| `05_forecasting-and-nwp.md` | Observation networks, data assimilation, the global and regional models, ensembles, skill and predictability, nowcasting, machine-learning models, TAF construction |
| `06_operational-application.md` | Briefing package, alternates and planning minima, fuel policy, hot/high performance (Doha worked case), en-route deviation, LVO, contaminated runway and RCAM, diversion |
| `07_climatology-for-route-planning.md` | Seasonal climatology by region and route, tropical cyclone basins, mountain wave regions, volcanic regions |
| `08_study-material-and-training.md` | Books, free official material, MetEd/COMET, online tools, a structured self-study plan |
| `09_case-studies.md` | The accidents and incidents that wrote the rules |

## 2. The legal and institutional framework

### 2.1 Chicago Convention → Annex 3

Article 28 of the Chicago Convention obliges each contracting State to provide meteorological services for international air navigation. The technical specification of that obligation is **Annex 3, Meteorological Service for International Air Navigation**, which is uniquely published as a *joint* ICAO/WMO instrument — its content is mirrored in **WMO No. 49 Technical Regulations, Volume II [C.3.1]**. This is why a METAR looks identical in Doha, Denpasar and Dakar: the same words are simultaneously an ICAO Standard and a WMO Technical Regulation.

Annex 3 is structured as Chapters plus a large set of Appendices that carry the actual product templates. The chapter subjects, in the order a pilot meets them, are:

1. **Definitions** — the exact meanings of *aerodrome forecast*, *ceiling*, *prevailing visibility*, *runway visual range*, *SIGMET information*, *meteorological authority*, etc. These definitions have legal force; "ceiling" in particular is defined and is not simply "the lowest cloud".
2. **World area forecast system and meteorological offices** — the two WAFCs, the meteorological watch offices (MWOs), aerodrome meteorological offices, and volcanic ash / tropical cyclone advisory centres.
3. **Meteorological observations and reports** — routine (METAR) and special (SPECI) observations, the observing programme, automatic stations.
4. **Aircraft observations and reports** — AIREP, AIREP SPECIAL, and automated (AMDAR/ADS-C derived) reporting.
5. **Forecasts** — TAF, landing forecasts (TREND), forecasts for take-off, area forecasts for low-level flight (GAMET/area forecast in chart form).
6. **SIGMET and AIRMET information, aerodrome warnings and wind shear warnings and alerts**.
7. **Aeronautical climatological information** — climatological tables and summaries used for aerodrome planning.
8. **Service for operators and flight crew members** — briefing, consultation, display, flight documentation.
9. **Information for air traffic services, search and rescue and aeronautical information services**.
10. **Requirements for and use of communications**.

The Appendices carry the templates: the METAR/SPECI template, the TAF template, the SIGMET/AIRMET template, the volcanic ash advisory template, the tropical cyclone advisory template, the space weather advisory template, the WAFS specification, and the technical specifications for observing (including the RVR and prevailing-visibility rules).

**Amendment context.** Annex 3 has been amended repeatedly to add: space weather advisories (applicable November 2019), the IWXXM (ICAO Meteorological Information Exchange Model) XML/GML digital exchange format alongside traditional alphanumeric codes, and the Global Reporting Format alignment for runway condition reporting. Treat any specific amendment number you have not personally checked as `needs-verification`.

### 2.2 The WMO layer

WMO supplies the observing and coding backbone that Annex 3 sits on:

- **WMO No. 306, Manual on Codes** — the actual code definitions. METAR is code form **FM 15**, SPECI **FM 16**, TAF **FM 51**. Volume I.1 holds the traditional alphanumeric codes; Volume I.2 holds BUFR/CREX; Volume I.3 the table-driven representations.
- **WMO No. 8, Guide to Instruments and Methods of Observation (CIMO Guide)** — how a transmissometer, ceilometer, anemometer and barometer must behave, the averaging periods (e.g. 2-minute wind for aviation vs 10-minute for synoptic), and siting rules.
- **WMO No. 49, Technical Regulations** — the umbrella; Volume II is aeronautical.
- **WMO Integrated Global Observing System (WIGOS)** and **WMO Information System (WIS/WIS 2.0)** — the observation and data-exchange plumbing.

### 2.3 The regional/State layer

- **EASA**: Part-MET is not a standalone EU regulation in the way Part-FCL is; meteorological service provision in Europe is regulated through **Commission Implementing Regulation (EU) 2017/373**, which sets common requirements for service providers including MET (Annex V, "Part-MET"). Operator use of met information sits in **Part-ORO/Part-CAT of Regulation (EU) 965/2012** (Air Operations) — planning minima, alternate selection, LVO approvals.
- **FAA**: 14 CFR Part 121 subparts T and U, and 14 CFR 91.103 (preflight action). Products are described in **AC 00-45 Aviation Weather Services**, and the physics in **AC 00-6 Aviation Weather**; both have been consolidated into the **Aviation Weather Handbook FAA-H-8083-28**.
- **Qatar**: the Qatar Civil Aviation Authority Meteorological Department is the designated meteorological authority; OTHH/OTBD observations and TAFs come from it. Qatar's Civil Aviation Regulations (QCAR) mirror ICAO Annexes.

## 3. The EASA ATPL 050 Meteorology syllabus

The European ATPL(A) theoretical knowledge examination set is organised into subjects numbered 010–092. Meteorology is **subject 050**. The top-level subject list is:

| Code | Subject |
|---|---|
| 010 | Air law and ATC procedures |
| 021 | Airframe, systems, electrics, power plant, emergency equipment |
| 022 | Instrumentation |
| 031 | Mass and balance |
| 032 | Performance (aeroplanes) |
| 033 | Flight planning and monitoring |
| 034 | Performance (helicopters) — helicopter stream only |
| 040 | Human performance and limitations |
| **050** | **Meteorology** |
| 061 | General navigation |
| 062 | Radio navigation |
| 070 | Operational procedures |
| 081 | Principles of flight (aeroplanes) |
| 090 | Communications (VFR/IFR) |

Within 050, the classic JAR-FCL/EASA sub-chapter structure — retained through the 2020 Learning Objective revision — is:

| Sub-code | Topic | What it actually contains |
|---|---|---|
| 050 01 | **The atmosphere** | Composition, vertical structure, ISA, air density, altimetry (QNH/QFE/QNE, transition altitude/level, temperature and pressure errors, cold-temperature effects, density altitude) |
| 050 02 | **Wind** | Definition and measurement, primary cause (PGF, Coriolis, friction), geostrophic and gradient wind, general global circulation, local winds (sea/land breeze, anabatic/katabatic, föhn, mountain-wave winds), turbulence and gusts, jet streams, standing waves |
| 050 03 | **Thermodynamics** | Humidity, dewpoint, change of state, adiabatic processes, DALR/SALR/ELR, stability and instability, temperature inversions, thermodynamic diagrams |
| 050 04 | **Clouds and fog** | Cloud formation and classification (the ten genera), fog/mist/haze formation and dispersal by type |
| 050 05 | **Precipitation** | Development of precipitation, types, and their association with cloud types |
| 050 06 | **Air masses and fronts** | Air mass source regions and classification, warm/cold/occluded/stationary fronts, frontal weather sequences, frontal depressions and their life cycle |
| 050 07 | **Pressure systems** | Anticyclones, ridges, cols, troughs, non-frontal depressions (thermal, orographic, polar, secondary), tropical revolving storms |
| 050 08 | **Climatology** | Climatic zones, tropical and mid-latitude seasonal weather, monsoon, local seasonal winds and weather, typical synoptic situations |
| 050 09 | **Flight hazards** | Icing, turbulence, windshear, thunderstorms, tornadoes, inversions, mountain waves, visibility reduction, hazards in mountainous areas, stratospheric conditions, sand/dust storms, volcanic ash |
| 050 10 | **Meteorological information** | Observation, weather charts, information for flight planning, meteorological broadcasts (VOLMET, ATIS, D-ATIS), briefing, the full product catalogue |

> ⚠️ The sub-chapter numbering above reflects the long-standing JAR/EASA 050 structure and is stated from working knowledge, not from a document fetched in this session. Verify against the current **AMC1 FCL.310; FCL.515(b); FCL.615(b) Learning Objectives** before using it for exam preparation or course design. Marked in `## Open questions`.

The typical 050 examination is around 84 multiple-choice questions in 2 hours under the EASA Central Question Bank, but question counts and durations are set by the ECQB version in force — verify with your ATO.

## 4. The FAA equivalent

The US does not use a numbered subject syllabus in the EASA style. The knowledge requirements sit in:

- **14 CFR 61.155** (ATP aeronautical knowledge areas) — includes "meteorology, including knowledge of and effects of fronts, frontal characteristics, cloud formations, icing, and upper-air data"; "weather reports, forecasts, charts, and weather-hazard warnings"; "windshear and microburst awareness, escape, and prevention manoeuvres".
- The **Airline Transport Pilot and Type Rating Airman Certification Standards (FAA-S-ACS-11)** — the task-level standard the examiner works from.
- **FAA-H-8083-28, Aviation Weather Handbook** — the consolidated reference, which absorbed the content of **AC 00-6B Aviation Weather** and **AC 00-45H Aviation Weather Services**. Its structure follows: the earth's atmosphere; heat and temperature; water vapour; earth–atmosphere heat imbalance; atmospheric pressure and altimetry; atmospheric circulation; air masses and fronts; stability; clouds; turbulence; icing; thunderstorms; mountain weather; tropical weather; arctic and high-latitude weather; space weather; then the whole products half (observations, analysis, forecasts, charts, dissemination).

The two systems teach the same physics; the difference is that EASA examines the physics much more formally and the FAA examines product interpretation and hazard avoidance more operationally. A pilot working out of Doha under a QCAA licence built on the EASA-style syllabus should read the FAA handbook anyway, because it is free, current, and much better on radar and satellite interpretation.

## 5. The service chain, end to end

Understanding where a number in your flight plan came from is the single most useful piece of meteorological literacy. The chain:

1. **Observation.** Surface stations (manual and AWOS/ASOS), radiosondes (~800 stations globally, mostly 00Z and 12Z), aircraft (AMDAR/ADS-C — the largest single source of upper-air data by volume), ships and buoys, wind profilers, weather radar, ground-based GNSS water vapour, and satellites (geostationary imagers, polar-orbiting sounders, radio occultation, scatterometers).
2. **Assimilation.** 4D-Var or hybrid ensemble-variational assimilation blends observations with a short-range forecast background to produce an analysis on the model grid.
3. **Model integration.** Global models (ECMWF IFS, NOAA GFS, DWD ICON, Met Office UM, Météo-France ARPEGE, JMA GSM) and nested regional/convection-permitting models.
4. **Ensemble.** Perturbed initial conditions and stochastic physics produce a probability distribution, not a single answer.
5. **WAFS.** The two WAFCs (London and Washington) take model output and issue the global forecasts of upper wind, temperature, humidity, cumulonimbus, icing, turbulence and tropopause in **GRIB2**, plus the SIGWX charts.
6. **Human forecaster.** Aerodrome forecasters build the TAF, MWOs issue SIGMET, VAACs issue volcanic ash advisories, TCACs issue tropical cyclone advisories.
7. **Flight planning system.** The airline's system ingests WAFS GRIB, computes the optimum route and levels, builds the fuel figure, and prints the OFP with the weather package attached.
8. **Crew.** You read the package, form a mental model, decide the fuel and the alternates, and then re-decide continuously in flight against ACARS/datalink updates, ATIS, radar, and what you can see.

Every one of those steps is a place where the information can be wrong, stale, or misinterpreted. Files `05` and `06` deal with the failure modes of the last four steps specifically.

## 6. How to use this domain

- If you want the **physics**, read `01` then `02` then `03` in order.
- If you want to **decode a product in front of you**, go straight to `04`.
- If you want to know **how much to trust a forecast**, read `05`.
- If you are **planning or flying a specific sector**, read `06` and `07`.
- If you are **studying for an exam or a recurrent**, read `08` and work `09`.

Units in this domain are deliberately mixed, because operational aviation is: altitude and cloud base in feet, visibility in metres (or statute miles in the US), RVR in metres (feet in the US), wind in knots (m/s in some States including much of the former Soviet sphere and China's domestic reporting), pressure in hPa (inHg in the US and Canada), temperature in degrees Celsius, and precipitation in millimetres. Where a conversion matters operationally it is given inline.

## Sources

- [Meteorology — ICAO Air Navigation Bureau](https://www.icao.int/safety/meteorology/Pages/default.aspx) — ICAO
- [METAR](https://en.wikipedia.org/wiki/METAR) — Wikipedia
- [Terminal aerodrome forecast](https://en.wikipedia.org/wiki/Terminal_aerodrome_forecast) — Wikipedia
- [SIGMET](https://en.wikipedia.org/wiki/SIGMET) — Wikipedia
- [Aviation Weather Center product list (GFA help)](https://aviationweather.gov/gfa/help) — NOAA/NWS
- [FAA Aircraft Ground Deicing / Holdover Tables](https://www.faa.gov/other_visit/aviation_industry/airline_operators/airline_safety/deicing) — FAA
- [Space weather](https://en.wikipedia.org/wiki/Space_weather) — Wikipedia (ICAO space weather advisory providers)

## Open questions

- The **050 sub-chapter numbering and titles** above are recalled from the long-standing JAR/EASA structure, not fetched this session. Verify against the current EASA Learning Objectives (AMC1 FCL.310 etc.) and the ECQB version in force. `needs-verification`
- The **Annex 3 chapter list** is given from working knowledge of the Annex structure; the official ICAO Annex 3 PDF returned HTTP 403 in this session. Verify chapter numbering and current amendment number directly. `needs-verification`
- **Exam question count and duration for 050** varies with ECQB version and national implementation — not verified.
- Whether **FAA-H-8083-28** has superseded AC 00-6B and AC 00-45H formally (cancellation of the ACs) was not confirmed from an FAA page in this session; the FAA handbooks index returned 404 on the URL tried.
- The precise current **Annex 3 amendment** governing IWXXM mandatory exchange dates.
