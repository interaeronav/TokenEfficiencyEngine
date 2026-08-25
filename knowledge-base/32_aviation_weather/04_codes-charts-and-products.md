---
id: aviation_weather.products
title: Codes, charts and products — METAR, TAF, SIGMET, SIGWX, satellite, radar, WAFS
domain: 32_aviation_weather
tags: [metar, speci, taf, sigmet, airmet, gamet, atis, pirep, airep, amdar, sigwx, wafs, grib2, satellite, water-vapour, weather-radar, lightning-detection, rvr, trend, iwxxm]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "METAR", url: "https://en.wikipedia.org/wiki/METAR", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Terminal aerodrome forecast", url: "https://en.wikipedia.org/wiki/Terminal_aerodrome_forecast", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "SIGMET", url: "https://en.wikipedia.org/wiki/SIGMET", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Aviation Weather Center — GFA help / product list", url: "https://aviationweather.gov/gfa/help", publisher: "NOAA/NWS Aviation Weather Center", accessed: 2026-08-25}
  - {title: "Weather radar", url: "https://en.wikipedia.org/wiki/Weather_radar", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Volcanic Ash Advisory Center", url: "https://en.wikipedia.org/wiki/Volcanic_Ash_Advisory_Center", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Terminal Doppler Weather Radar", url: "https://en.wikipedia.org/wiki/Terminal_Doppler_Weather_Radar", publisher: "Wikipedia", accessed: 2026-08-25}
related: [aviation_weather.overview, aviation_weather.hazards, aviation_weather.nwp, aviation_weather.operations]
unit_system: mixed
---

# Codes, charts and products — METAR, TAF, SIGMET, SIGWX, satellite, radar, WAFS

**Summary.** The operational products are a closed, standardised set defined by ICAO Annex 3 and WMO No. 306. This file decodes each one to the level where you can read a raw bulletin without a decoder, explains the ICAO/US divergences that catch people out, and covers the interpretation skills — satellite channels, radar tilt management, SIGWX symbology — that the codes alone do not give you.

## Key facts

| Product | Code form | Validity / issue |
|---|---|---|
| METAR | WMO **FM 15** | Routine, normally half-hourly or hourly |
| SPECI | WMO **FM 16** | On significant change between routines |
| TAF | WMO **FM 51** | Short TAF 9 h, long TAF **24 or 30 h**; issued **0000/0600/1200/1800 UTC** four times daily |
| TREND (landing forecast) | appended to METAR | **2 hours** from the observation |
| SIGMET | Annex 3 template | **≤ 4 h**; **6 h** for volcanic ash and tropical cyclone |
| Convective SIGMET (US) | US-specific | **2 h**, issued hourly at **H+55** |
| AIRMET | Annex 3 template / US G-AIRMET | ≤ 4 h |
| VAA | VAAC text + graphic | forecast positions at **+6, +12, +18 h** |
| WAFS | GRIB2 + SIGWX charts | WAFC **London** and **Washington** |
| Cloud amount | oktas: **FEW 1–2, SCT 3–4, BKN 5–7, OVC 8** | ceiling = lowest **BKN or OVC** |
| CAVOK | vis **≥ 10 km**, no cloud below **5000 ft** (or below the highest MSA, whichever is greater) and no CB/TCU, no significant weather | — |

## 1. METAR and SPECI

### 1.1 The group order

```
METAR/SPECI  CCCC  YYGGggZ  [AUTO|COR]  dddffGfmfmKT dndndnVdxdxdx
             VVVV [VVVVNDV] [DvDvDvDvDv]  RDRDR/VRVRVRVRi
             w'w'  NsNsNshshshs [CB/TCU] | VVhshshs | NSC/NCD/SKC
             T'T'/T'dT'd  QPHPHPHPH | APAPAPAP
             [REw'w'] [WS RWYnn | WS ALL RWY] [WTsTs/SS'] [RWY state / SNOWTAM group]
             [TREND: NOSIG | BECMG ... | TEMPO ...]  [RMK ...]
```

### 1.2 Group by group

**Report type.** `METAR` (routine) or `SPECI` (special). `METAR COR` = corrected. `AUTO` = fully automatic observation with no human augmentation — read it with suspicion, because automatic stations under-report thunderstorms, freezing precipitation, and cloud above the ceilometer's range, and they report `//////` where a sensor is absent.

**Station.** Four-letter ICAO location indicator: `OTHH` Hamad, `OTBD` Doha Int'l, `OMDB` Dubai, `EGLL` Heathrow, `KJFK` New York.

**Date/time.** `DDHHMMZ`, always UTC. `041600Z` = 4th at 1600 UTC.

**Wind.** `dddff[Gfmfm]KT` — direction in **degrees true**, rounded to the nearest 10; speed in **KT** (ICAO also permits **MPS** and **KMH**; Russia, China and several other States report **MPS** — read the unit suffix, always).
- `VRB` when direction is variable and the speed is **≤ 6 kt** (or when the variation exceeds 180° at any speed).
- `dndndnVdxdxdx` (e.g. `180V240`) when direction varies by **60° or more** and speed exceeds 3 kt.
- Gust reported when the peak exceeds the mean by **10 kt or more** in the last 10 minutes.
- `00000KT` = calm. `P99KT` = above 99 kt.
- **The METAR wind is a 10-minute mean, true north.** The **ATIS/tower wind is a 2-minute mean, magnetic**. Confusing the two is a routine crosswind-calculation error — and in the Gulf, magnetic variation is small, but in Canada or Scandinavia it is not.

**Visibility.** ICAO: **metres**; `0000` to `9999` where **9999 means 10 km or more**. Prevailing visibility is *the visibility value reached or exceeded within at least half the horizon circle or half the aerodrome surface*. If the minimum visibility in some direction differs significantly and is below 1500 m or below 50 % of the prevailing, both are given with a direction (`2000 1200NE`). `NDV` = no directional variation (automatic station).
US: **statute miles**, e.g. `1/2SM`, `10SM`.

**RVR.** `R[runway]/[value][tendency]` — e.g. `R04/P1500N`. `P` = more than the reported value, `M` = less than. Tendency `U` up, `D` down, `N` no change. Variable RVR is given as `R25L/0600V1000U`. Reported when visibility or RVR is at or below **1500 m** (ICAO) — in the US when visibility ≤ 1 statute mile or RVR ≤ 6000 ft. Up to four runways.

**Present weather.** Built from **intensity/proximity + descriptor + phenomenon**, in that order, up to three groups.

| Intensity/proximity | |
|---|---|
| `-` | light |
| (none) | moderate |
| `+` | heavy (or, with `FC`, "well-developed" = tornado/waterspout) |
| `VC` | in the vicinity (5–10 statute miles / 8–16 km, not at the aerodrome) |

| Descriptor | |
|---|---|
| `MI` shallow | `BC` patches |
| `PR` partial | `DR` low drifting |
| `BL` blowing | `SH` shower(s) |
| `TS` thunderstorm | `FZ` freezing (supercooled) |

| Precipitation | Obscuration | Other |
|---|---|---|
| `DZ` drizzle | `BR` mist | `PO` dust/sand whirls |
| `RA` rain | `FG` fog | `SQ` squall |
| `SN` snow | `FU` smoke | `FC` funnel cloud/tornado |
| `SG` snow grains | `VA` volcanic ash | `SS` sandstorm |
| `IC` ice crystals | `DU` widespread dust | `DS` duststorm |
| `PL` ice pellets | `SA` sand | |
| `GR` hail (≥ 5 mm) | `HZ` haze | |
| `GS` small hail/snow pellets | `PY` spray | |
| `UP` unknown precipitation (automatic) | | |

Combinations read left to right: `+TSRA` heavy thunderstorm with rain; `-FZDZ` light freezing drizzle; `VCTS` thunderstorm in the vicinity; `+DS` heavy duststorm; `SHRAGS` shower of rain and small hail; `MIFG` shallow fog; `BLDU` blowing dust; `FZFG` freezing fog (fog composed of supercooled droplets, **not** "fog when it's below zero" — `FG` at −5 °C with ice crystals is `FG` or `IC`).

**Cloud.** `NsNsNs hshshs` in oktas and hundreds of feet **above aerodrome elevation**:

| Code | Oktas |
|---|---|
| `FEW` | 1–2 |
| `SCT` | 3–4 |
| `BKN` | 5–7 |
| `OVC` | 8 |

`BKN022` = broken at 2200 ft. `CB` or `TCU` is appended when present — these are the **only** cloud types coded, and they are coded regardless of amount. Reporting rule: the lowest layer whatever the amount; the next layer covering more than 2 oktas; the next covering more than 4 oktas; plus any CB/TCU.

Special groups: `VV003` vertical visibility 300 ft (sky obscured, no discernible cloud base); `NSC` no significant cloud; `NCD` no cloud detected (automatic); `SKC` sky clear (in North America, indicates a human observation); `CLR` (US automatic, no cloud below 12 000 ft); `CAVOK` replaces visibility, RVR, weather and cloud groups entirely.

**Temperature/dewpoint.** `T'T'/T'dT'd` in whole degrees Celsius; `M` prefix for negative. `15/10`, `M04/M07`. In the US remarks a tenths-precision group appears (`T01500100`).

**Pressure.** `Q1020` = QNH 1020 hPa (ICAO). `A3006` = altimeter 30.06 inHg (US/Canada). Some States report both.

**Supplementary.**
- `RE` + phenomenon: recent weather since the last report, e.g. `RETS`, `REFZRA`.
- `WS RWY12` or `WS ALL RWY`: wind shear reported on that runway.
- `WT`/sea state groups at coastal/offshore stations.
- **Runway state group** (historically `RDRDR/ERCReReRBRBR` — runway designator, deposit type, extent of contamination, depth, friction coefficient or braking action). This traditional group has been superseded operationally in most States by the **Global Reporting Format SNOWTAM/RCR** (see `06`); treat any legacy runway-state group with care and check the State's implementation. `needs-verification`

**Trend (landing forecast).** Appended to the METAR, valid **2 hours** from the observation time:
- `NOSIG` — no significant change expected.
- `BECMG` — a permanent change expected, optionally with `FM`/`TL`/`AT` time markers, e.g. `BECMG FM1200 TL1300 SCT015`.
- `TEMPO` — temporary fluctuations, each lasting less than an hour and in total less than half the period.
Only elements that change are listed. `TEMPO 3000 SHRA BKN010CB` is a complete trend.

**RMK.** Everything after `RMK` is State-defined. In the US it is extensive and highly informative:
- `AO1` automatic without a precipitation discriminator; `AO2` with one.
- `SLP132` sea-level pressure 1013.2 hPa.
- `PK WND 24035/1815` peak wind.
- `WSHFT 1715` wind shift.
- `RAB05E32` rain began :05, ended :32; `TSB24` thunderstorm began :24.
- `CIG 013V017` variable ceiling.
- `PRESRR`/`PRESFR` pressure rising/falling rapidly.
- `T01500100` temperature 15.0 / dewpoint 10.0.
- `1[s]TTT` 6-hour maximum, `2[s]TTT` 6-hour minimum, `4[s]TTT[s]TTT` 24-hour max/min.
- `5appp` 3-hour pressure tendency; `6RRRR` 3/6-hour precipitation; `7RRRR` 24-hour precipitation.
- `4/012` snow depth 12 inches; `931222` 22.2 in snowfall in 6 h; `933021` 2.1 in water equivalent.
- `98060` 60 minutes of sunshine.
- `TS OHD MOV E`, `CB DSNT NE`, `VIRGA` — plain-language observations that are frequently the most operationally useful part of the whole report.

### 1.3 ICAO vs US conventions — the traps

| Element | ICAO | US |
|---|---|---|
| Visibility | metres, `9999` = ≥10 km | statute miles, `10SM` |
| RVR | metres | feet |
| Pressure | `Q` hPa | `A` inHg |
| Wind speed | KT (also MPS, KMH) | KT |
| Cloud "clear" | `NSC`/`NCD` | `SKC`/`CLR` |
| Trend group | `NOSIG`/`BECMG`/`TEMPO` normally present | Rarely used; US uses TAF instead |
| Remarks | Sparse | Extensive and codified |
| Flight categories | not used | VFR / MVFR / IFR / LIFR (>3 sm & >3000 ft; 1–3 sm or 1000–3000 ft; ½–1 sm or 500–1000 ft; <½ sm or <500 ft) |
| Ceiling | Annex 3 definition, feet AAL | feet AGL, same idea |

### 1.4 Worked example

```
METAR OTHH 020600Z 32014KT 3000 BLDU SCT035 41/12 Q0998 NOSIG
```
Hamad International, 2nd at 0600 UTC, wind 320° at 14 kt, visibility 3000 m in blowing dust, scattered cloud at 3500 ft, temperature 41 °C, dewpoint 12 °C, QNH 998 hPa, no significant change expected in the next two hours. Reading: a shamal day. Pressure altitude ≈ +405 ft, ΔISA ≈ +26 °C, density altitude ≈ 3500 ft, so a performance-limited departure; the dust will get worse before it gets better; the crosswind on 34/16 is modest but 32014 on runway 34 is 14 kt at 20° off, about 5 kt of crosswind and 13 kt of headwind.

```
METAR EGLL 121250Z AUTO 24016G28KT 210V270 2000 R27R/1200D +SHRA BKN008 OVC015CB 09/08 Q0987 RESQ TEMPO 1200 TSRA BKN006
```
Heathrow, automatic, 12th at 1250 UTC, wind 240° 16 gusting 28, varying 210–270, visibility 2000 m, RVR on 27R 1200 m and decreasing, heavy rain shower, broken at 800 ft, overcast at 1500 ft with CB, 9/8, QNH 987 (that is 26 hPa below standard — **FL80 is really about 7220 ft**), recent squall, temporarily 1200 m in thunderstorm with rain and broken 600 ft.

## 2. TAF

### 2.1 Structure

```
TAF [AMD|COR] CCCC YYGGggZ YYG1G1/YYG2G2
    dddffKT VVVV w'w' NsNsNshshshs [TX../TN..]
    [change groups...]
```

- **Issue time** `YYGGggZ`; **validity** `YYG1G1/YYG2G2` — e.g. `0518/0624` = from the 5th 1800 UTC to the 6th 2400 UTC. (Older format used `0518/24`.)
- **Validity length**: 9 h (short TAF, issued 8-hourly or 3-hourly in some States) or **24 or 30 h** (long TAF), **issued four times daily at 0000, 0600, 1200 and 1800 UTC** for major aerodromes.
- **`TAF AMD`** amended; **`TAF COR`** corrected; **`NIL`** not available; **`CNL`** cancelled.
- The forecast covers **wind, visibility, weather and cloud** — and, only where required, temperature (`TX32/1512Z TN22/1602Z`), icing and turbulence groups (mainly military/State-specific).

### 2.2 Change groups

| Group | Meaning | Rules |
|---|---|---|
| `FM YYGGgg` | **From** — a rapid and permanent change, complete within about an hour; everything after it **replaces** the entire preceding forecast | All elements must be restated |
| `BECMG YYGG/YYGG` | **Becoming** — a gradual permanent change during the stated window, normally not exceeding **2 hours** in ICAO practice (the change is expected at an unspecified time within it) | Only the changing elements are stated |
| `TEMPO YYGG/YYGG` | **Temporary** fluctuations, each lasting **less than 1 hour** and **in aggregate less than half** the stated period | Only the changing elements |
| `PROB30 / PROB40 [TEMPO] YYGG/YYGG` | **30 % or 40 % probability** of the stated conditions | `PROB` is used only for 30 % and 40 %; below 30 % the condition is not forecast, at 50 % or more it is forecast outright. **`PROB` is not used with `FM` or `BECMG`** |
| `TEMPO`/`PROB` in the US | US TAFs use `FM`, `TEMPO` and `PROB30` (`PROB40` is used in ICAO practice but the US convention differs) | Check the State |

> ⚠️ **`PROB30 TEMPO`** is not a double-discount: it means a 30 % probability that the *temporary* conditions occur at all. Whether it counts against your planning minima depends on your operator's fuel and alternate policy and on the applicable rule set (EU-OPS/Part-CAT historically required certain `PROB` and `TEMPO` conditions to be taken into account for alternate selection but permitted disregarding others). Read the OM-A rule, not the folklore.

### 2.3 Worked example

```
TAF OTHH 051100Z 0512/0618 32012KT 9999 SCT040
  BECMG 0518/0520 VRB03KT 6000 HZ
  PROB40 TEMPO 0522/0603 3000 BR
  TEMPO 0600/0604 0800 FG BKN002
  BECMG 0605/0607 07008KT 9999 NSC
```
Hamad, issued 5th 1100 UTC, valid 5th 1200 to 6th 1800. Northwesterly 12 kt, 10 km+, scattered 4000 ft. Becoming variable 3 kt and 6000 m in haze between 1800 and 2000 UTC. 40 % probability of temporary 3000 m in mist between 2200 and 0300. Temporary 800 m in fog with broken 200 ft between 0000 and 0400 — **that is below CAT I minima and drives the alternate and fuel decision for any arrival in that window**. Clearing after 0500–0700 with a light easterly.

## 3. SIGMET, AIRMET and area forecasts

### 3.1 SIGMET

Issued by the **Meteorological Watch Office** responsible for the FIR, for phenomena hazardous to **all** aircraft. Three ICAO types:

| Type | Header code | Phenomena |
|---|---|---|
| **WS** | ordinary SIGMET | Thunderstorms (obscured/embedded/frequent/squall line), severe turbulence, severe icing, severe mountain wave, heavy duststorm/sandstorm, radioactive cloud, hail |
| **WV** | volcanic ash SIGMET | Volcanic ash cloud |
| **WC** | tropical cyclone SIGMET | Tropical cyclone with 10-min mean surface wind ≥ 34 kt |

**Validity:** up to **4 hours** for ordinary SIGMET; **6 hours** for volcanic ash and tropical cyclone.

**Structure (three parts):**
1. **Bulletin header** — data type designator (WS/WV/WC), country code, bulletin number, originating station, date/time.
2. **SIGMET line** — FIR ICAO indicator + `SIGMET` + sequence number + `VALID YYGGgg/YYGGgg` + originating MWO indicator + FIR name.
3. **Body** — phenomenon, `OBS`/`FCST` with time, location (lat/long polygon, or relative to named points/FIR boundary), vertical extent (`FL`, `SFC/FL100`, `TOP FL450`), movement (`MOV NE 25KT` or `STNR`), and intensity change (`INTSF` / `WKN` / `NC`).

**Common abbreviations:** `ABV` above, `BLW` below, `BTN` between, `CNL` cancel, `FCST` forecast, `FIR` flight information region, `FL` flight level, `MOV` moving, `NC` no change, `NM` nautical miles, `OBS` observed, `SFC` surface, `STNR` stationary, `TOP` cloud top, `WI` within, `Z` UTC, `INTSF` intensifying, `WKN` weakening.

Example shape:
`OTDF SIGMET 3 VALID 021200/021600 OTBD- OTDF DOHA FIR EMBD TS OBS AT 1150Z WI N2500 E05100 - N2530 E05230 - N2400 E05300 - N2400 E05100 TOP FL450 MOV SE 20KT INTSF`

**US Convective SIGMET** is a separate national product: issued **hourly at H+55**, valid **2 hours**, for embedded thunderstorms, lines of thunderstorms, or areas of thunderstorms with VIP level 4+ covering 40 % of an area, plus severe surface weather and tornadoes. It automatically implies severe turbulence, severe icing and low-level windshear.

### 3.2 AIRMET

For phenomena hazardous to **light aircraft and low-level operations** and not covered by SIGMET: widespread areas of surface visibility below 5000 m, thunderstorms without hail, cloud below 1000 ft, moderate turbulence, moderate icing, moderate mountain wave, surface wind above a stated speed. Valid up to 4 hours. Issued only where the State provides low-level area forecasts. The **US G-AIRMET** is a graphical, 3-hourly, gridded version with Sierra (IFR/mountain obscuration), Tango (turbulence/surface wind/LLWS) and Zulu (icing/freezing level) categories.

### 3.3 GAMET and low-level area forecasts

**GAMET** is the Annex 3 plain-abbreviated-text area forecast for low-level flight, issued in two sections: **Section I** hazards (surface wind, visibility, significant weather, mountain obscuration, cloud, icing, turbulence, mountain wave, sea state) and **Section II** supporting information (pressure centres and fronts, upper winds and temperatures, freezing level, MSLP, volcanic ash and radioactivity). Many States replace it with a chart-form **low-level SIGWX**.

### 3.4 Aerodrome and wind shear warnings

- **Aerodrome warning** — issued by the aerodrome meteorological office for conditions that could damage aircraft/facilities on the ground: gales, gusts, thunderstorms, hail, snow, freezing precipitation, frost, duststorm, tropical cyclone, tsunami, volcanic ash fall, rising water.
- **Wind shear warning** — a concise statement of observed or expected wind shear in the approach/take-off path between runway level and 1600 ft. Issued from PIREPs, LLWAS/TDWR/LIDAR, or forecaster judgement.
- **Wind shear alert** — the automated, real-time version from LLWAS/TDWR, passed by ATC.

### 3.5 Advisories

- **Volcanic Ash Advisory (VAA)** from a VAAC — text plus a graphic (VAG), with observed and **forecast ash positions at +6, +12 and +18 h**. The VAA is *advisory*; the SIGMET is the binding hazard statement, and States/operators act on both.
- **Tropical Cyclone Advisory (TCA)** from a TCAC — position, intensity, movement, forecast positions.
- **Space Weather Advisory (SWX)** from the four global providers — HF COM, GNSS and RADIATION hazards at MOD/SEV levels, with affected areas and forecast times.

## 4. ATIS, VOLMET and datalink

- **ATIS** — continuous broadcast of the current aerodrome information, updated on a new observation or a significant change, identified by a phonetic letter. Contains: aerodrome name, information letter, time, runway(s) in use, approach type, transition level, wind (**2-minute mean, magnetic**), visibility/RVR, present weather, cloud, temperature/dewpoint, QNH, trend, and remarks (windshear, LVP in force, braking action, birds, work in progress).
- **D-ATIS** — the datalink version, textually identical, and the one you should prefer because you can re-read it.
- **VOLMET** — HF/VHF broadcast of METARs and TAFs for a list of aerodromes, on a fixed schedule.
- **Datalink weather** — ACARS/CPDLC-delivered METAR/TAF/SIGMET on request; the routine way a long-haul crew updates the destination picture mid-Atlantic.
- **IWXXM** — the XML/GML digital representation of METAR/TAF/SIGMET and the other Annex 3 products, being phased in alongside (and eventually replacing) the traditional alphanumeric codes for machine-to-machine exchange. Human-readable form persists on the flight deck.

## 5. Aircraft observations

- **AIREP / AIREP SPECIAL** — the pilot's report. AIREP SPECIAL is required for severe turbulence, severe icing, severe mountain wave, thunderstorms (obscured/embedded/heavy squall line), heavy duststorm/sandstorm, volcanic ash or pre-eruption volcanic activity, and other conditions affecting safety. Format: aircraft identification, position, time, flight level, and the phenomenon.
- **PIREP** (US format `UA` routine / `UUA` urgent) — fields: `/OV` location, `/TM` time, `/FL` altitude, `/TP` aircraft type, `/SK` sky condition, `/WX` flight visibility and weather, `/TA` temperature, `/WV` wind, `/TB` turbulence, `/IC` icing, `/RM` remarks. **The single most useful product in the system and the most under-supplied — file them.**
- **AMDAR** — automated meteorological data relay: pressure, temperature, wind and (on some fleets) humidity and **EDR turbulence**, downlinked automatically. Modern AMDAR/TAMDAR fleets provide the largest single source of upper-air observations by volume, and the vertical profiles on climb-out and descent are effectively free radiosondes at every busy airport. Their loss during the 2020 traffic collapse measurably degraded global forecast skill — a useful proof of how much they matter.

## 6. Charts

### 6.1 Significant weather (SIGWX) charts

Issued by the WAFCs (high level) and by national services (medium and low level), as a **fixed-time** forecast (not a period).

| Chart | Layer | Typical content |
|---|---|---|
| **High level SIGWX** | **FL250–FL630** | CB areas, CAT areas, jet streams, tropopause heights, volcanic activity, tropical cyclones, radioactive release |
| **Medium level SIGWX** | **FL100–FL450** (regional) | As above plus icing, freezing level, fronts |
| **Low level SIGWX** | **SFC–FL100** (or FL150) | Fronts, cloud, weather, visibility, icing, turbulence, freezing level, surface wind, mountain obscuration |

**Symbology you must read fluently:**

| Symbol | Meaning |
|---|---|
| Scalloped box | Area of **CB / significant convective cloud**, annotated with `ISOL`, `OCNL`, `FRQ`, `EMBD`, `OBSC`, `SQL` and base/top flight levels |
| Ragged/jagged box with `^` bars | **CAT area**, numbered, with a legend box giving flight levels and intensity |
| Bold arrow with speed flags and an `FL` label, double bars | **Jet stream axis**; double bars mark 20 kt speed changes; drawn only for cores ≥ 80 kt |
| `<80>` in a box | Tropopause height in flight levels; `H`/`L` boxes for tropopause maxima/minima |
| Red erupting-volcano symbol | Volcanic eruption with name and position |
| `☢` | Radioactive material release |
| Tropical cyclone symbol | With name and forecast position |
| Standard front symbols with arrow and speed | Surface fronts with movement |
| Icing and turbulence symbols | Moderate/severe, with base/top |
| Height convention | All heights in **flight levels**, `XXX` = above the chart's ceiling, `SFC` = surface |

Convective cloud coverage terms: `ISOL` isolated (individual, < 50 % area coverage in the sense of ICAO's definition), `OCNL` occasional (well separated, 50–75 %), `FRQ` frequent (little or no separation, > 75 %), `EMBD` embedded in other cloud (the important one — you cannot see them), `OBSC` obscured by haze/dust, `SQL` squall line.

### 6.2 Wind and temperature charts

Upper-level charts at standard levels, each corresponding to an approximate flight level:

| Pressure level | Approximate FL |
|---|---|
| 850 hPa | FL050 |
| 700 hPa | FL100 |
| 500 hPa | FL180 |
| 400 hPa | FL240 |
| 300 hPa | FL300 |
| 250 hPa | FL340 |
| 200 hPa | FL390 |
| 150 hPa | FL450 |

Wind is plotted as barbs (**half barb 5 kt, full barb 10 kt, pennant 50 kt**), temperature as a plain negative number (the minus sign is omitted above the tropopause in some formats — check the legend). These are the charts behind the OFP's forecast wind components, and the difference between the flight-plan wind and the actual is the first thing you check at each waypoint.

### 6.3 Surface analysis and prognostic charts

- **Surface analysis** — isobars (MSLP, using **QFF**), fronts, pressure centres, and often plotted station models. Isobar spacing gives geostrophic wind; the sense of the isobar curvature gives gradient corrections.
- **Prognostic charts (prog charts)** — forecast surface pressure and fronts at T+12/24/36/48 etc., often combined with precipitation type and areas.
- **Station model** — the plotted circle with wind barb, cloud amount (shading of the circle), temperature and dewpoint, pressure and 3-h tendency, present weather symbol, and cloud types. Worth being able to read; it is the densest weather notation ever devised.

## 7. Satellite imagery

Three primary channels, and knowing what each **actually measures** is the difference between using them and being misled.

| Channel | Measures | Strengths | Traps |
|---|---|---|---|
| **Visible (VIS)** | Reflected sunlight (albedo) | Best spatial resolution; distinguishes thick from thin cloud by brightness; shows texture, shadows, overshooting tops, gravity waves, dust plumes | **Useless at night.** Cannot separate low cloud from fog from snow (all bright) |
| **Infrared (IR ~10.8 µm)** | Emitted thermal radiation → **cloud-top temperature**, converted to height | Works 24 h; identifies deep convection by cold tops; enhancement tables colour-code the coldest tops | **Cannot see low cloud/fog when its top temperature is close to the surface temperature** — the classic overnight fog blind spot. Cirrus over a storm masks what is underneath. In a temperature inversion, low cloud can appear *warmer* than the surface |
| **Water vapour (WV ~6.2–7.3 µm)** | Radiation from the **mid/upper-troposphere water vapour layer**, roughly 300–600 hPa | Shows the **flow**, not just the cloud: jet streams, dry intrusions, PV anomalies, tropopause folds, deformation zones. Dark = dry, descending, high-PV stratospheric air. Bright = moist, ascending | Shows nothing below the moist layer. It is a *dynamics* channel, not a cloud channel |

Derived and multi-channel products worth knowing: **fog/low-stratus RGB** (IR 3.9 µm minus IR 10.8 µm — the standard night fog detection trick), **dust RGB** (separates airborne dust from cloud, invaluable in the Gulf), **airmass RGB** (ozone/WV combination that renders PV anomalies vividly), **convective-initiation products**, **cloud-top height/phase retrievals**, and **GOES/Meteosat lightning mappers**.

Geostationary imagers (Meteosat Third Generation over Europe/Africa/Indian Ocean, GOES-R series over the Americas, Himawari over the western Pacific) give **rapid-scan imagery at 10-minute full-disk and 1–2.5 minute mesoscale sectors**, which turns satellite from a snapshot into a movie. Watching the loop is worth more than any single image: motion, growth rate and overshooting tops tell you which cell is intensifying.

## 8. Weather radar

### 8.1 Ground-based principles

- **Reflectivity (Z)** in **dBZ**, logarithmic because return power varies enormously. Typical NEXRAD colour scale: ~20 dBZ green (light), ~35 dBZ yellow (moderate), ~50 dBZ red (heavy), ≥ 65 dBZ magenta (extreme / hail).
- **Z–R relation**: `Z = a·R^b` — the rainfall estimate. Because reflectivity goes as the **sixth power of drop diameter**, a few large drops dominate the return and the same rain rate can give wildly different Z depending on the drop-size distribution. Hail wrecks the relation entirely.
- **Attenuation**: negligible at **10 cm (S-band)**; **significant at 5 cm (C-band) in heavy rain**; severe at **3 cm (X-band)** — which is the band most airborne radars use. This is the single most important limitation of your own radar.
- **Radar shadow**: an intense cell absorbs the beam and creates a false low-reflectivity region behind it. On airborne radar this is the **"blind alley"**: the apparently clear gap beyond a strong cell may contain the worst weather on the route.
- **Doppler**: phase shift between pulses gives radial velocity → wind fields, mesocyclones, gust fronts, microburst divergence signatures.
- **Dual polarisation**: differential reflectivity (Z_DR) for drop shape, correlation coefficient (ρ_HV) for hydrometeor homogeneity (low ρ_HV = mixed types or debris), specific differential phase (K_DP) for rain rate immune to attenuation. Used to identify hail, melting layer, and tornado debris.
- **TDWR** (§3 of `03`) is a dedicated C-band terminal radar for microburst and gust-front detection, complementing longer-range NEXRAD.

### 8.2 Airborne radar and tilt management

The airborne radar is a narrow-beam (typically 3°) X-band radar with a stabilised antenna. It measures **water**, not turbulence, not cloud, not ice. Dry hail, ice crystals and volcanic ash return very little.

**The beam geometry problem.** Beam width in nautical miles ≈ `beamwidth(°) × range(nm) / 60 × 6076 ft`, i.e. a 3° beam is about **1 nm wide at 20 nm and 5 nm wide at 100 nm**, and the vertical spread is the same. So at long range the beam samples a huge vertical slice and averages it; at short range it samples a thin slice and can miss the core entirely.

**Tilt management technique:**

1. **On the ground / low altitude**: tilt up to keep ground clutter off the display while still seeing the weather; a good starting point is enough up-tilt that ground returns sit at the edge of the display.
2. **In the climb**: progressively reduce tilt as you climb so that the beam stays in the *wet* part of the storm — **below the freezing level**, where reflectivity is greatest. A storm scanned above the freezing level shows dry ice crystals and looks harmless.
3. **At cruise**: use **down-tilt** so that the beam intercepts the storm core at or below the freezing level ahead of you. A common technique is to set the tilt so that ground return just appears at the outer range ring, then work upward and downward around that.
4. **Manually sweep the tilt** through the vertical to build a mental 3-D picture: find the top by tilting up until the return disappears, and find the core by tilting down. Do not leave it in one position, and do not trust an auto-tilt function to do this thinking for you.
5. **Gain**: use calibrated/auto gain for assessment (the colour thresholds only mean something at calibrated gain); use manual gain increase to reveal weak returns (ice, dry hail) and manual decrease to find the strongest core inside a saturated red area.
6. **Range**: scan long range for strategy (200–320 nm) and short range for tactics (40–80 nm). Alternate. A 20-nm-wide gap seen at 160 nm may not exist at 40 nm.

**Interpretation cues on airborne radar:**
- **Steep gradient** (colours packed close together) = strong updraft = hazard, even if the peak return is only amber.
- **Scalloped, finger, hook or U-shaped edges** = hail and severe turbulence.
- **Shadow behind a cell** = do not go there.
- **Magenta/turbulence (Doppler) mode** shows only turbulence *in precipitation* — clear-air turbulence adjacent to the cell is invisible.
- Above the freezing level, add **at least 10–15 dBZ mentally** to what you see.
- **Predictive windshear (PWS)** uses the same antenna in a Doppler mode below ~1200–2300 ft AGL, out to about 3 nm, looking for the outflow divergence signature.

### 8.3 Lightning detection networks

Ground-based networks (**WWLLN**, **GLD360**, **ENTLN**, **Blitzortung**, and national networks) locate strokes by **time-of-arrival** or **magnetic direction finding** on VLF/LF sferics, over thousands of kilometres including oceans. **Satellite lightning mappers** (GOES **GLM**, Meteosat Third Generation **LI**) detect optical flashes from orbit with continuous hemispheric coverage.

Operational value: lightning is the only *direct*, continuous, ocean-capable indicator of active deep convection. It fills exactly the gap that ground radar leaves over the ITCZ, the Atlantic, the Indian Ocean and the Sahara — the places where you most need to know which cell is alive. Lightning rate trends also lead updraft intensification (a "lightning jump" often precedes severe weather by minutes).

## 9. The World Area Forecast System

Two **World Area Forecast Centres** — **London (Met Office)** and **Washington (NOAA/NWS)** — produce, from their global models, the standard global gridded forecasts that every flight-planning system in the world uses.

**Products:**
- **GRIB2 gridded forecasts** of upper wind, upper temperature, humidity, geopotential height, **icing potential, clear-air and in-cloud turbulence (EDR), cumulonimbus horizontal extent and base/top**, tropopause height and maximum wind level.
- **SIGWX high-level charts** (FL250–FL630) and medium-level charts for defined regions.
- Both centres produce the full global set so that each is a hot backup for the other.

**Why it matters to you:** the wind and temperature figures on your OFP, and therefore the fuel, come from WAFS GRIB interpolated to your route and levels. The **CB, icing and turbulence GRIB fields** are what drive the graphical hazard overlays in modern EFB flight-planning apps. Understanding that they are *model output on a coarse grid*, with the limitations described in `05`, is the difference between using them well and being surprised.

> ⚠️ The **exact WAFS GRIB2 horizontal resolution, forecast steps and parameter list have changed several times** and could not be verified in this session (the Met Office and AWC WAFS pages were unreachable). Check the current WAFS product specification before quoting resolution or step figures. `needs-verification`

## Sources

- [METAR](https://en.wikipedia.org/wiki/METAR) — Wikipedia (group order, wind/visibility/RVR rules, weather codes, cloud oktas, CAVOK, US remarks, flight categories, SPECI)
- [Terminal aerodrome forecast](https://en.wikipedia.org/wiki/Terminal_aerodrome_forecast) — Wikipedia (validity, issue times, FM/TEMPO/PROB30, AMD/COR)
- [SIGMET](https://en.wikipedia.org/wiki/SIGMET) — Wikipedia (three-part structure, validity, WS/WV/WC, abbreviations, US convective SIGMET)
- [Aviation Weather Center product list](https://aviationweather.gov/gfa/help) — NOAA/NWS (product catalogue, G-AIRMET, CWA, prog charts)
- [Weather radar](https://en.wikipedia.org/wiki/Weather_radar) — Wikipedia (dBZ scale, Z–R, attenuation by band, shadow, Doppler, dual-pol, airborne tilt)
- [Terminal Doppler Weather Radar](https://en.wikipedia.org/wiki/Terminal_Doppler_Weather_Radar) — Wikipedia
- [Volcanic Ash Advisory Center](https://en.wikipedia.org/wiki/Volcanic_Ash_Advisory_Center) — Wikipedia (VAA content and +6/+12/+18 h forecasts)

## Open questions

- **WAFS GRIB2 resolution, forecast steps and current parameter list** — not verified. `needs-verification`
- **The legacy METAR runway state group** vs the Global Reporting Format transition differs by State; verify per AIP. `needs-verification`
- **`PROB40` usage in US TAFs** and the exact US/ICAO divergence in change-group rules — partially verified only.
- **SIGWX `ISOL`/`OCNL`/`FRQ` percentage-coverage definitions** are quoted from working practice; verify against ICAO Annex 3 Appendix 2. `needs-verification`
- **Airborne radar beamwidth (3°) and PWS range/altitude limits** are typical values; they are equipment-specific — check the AFM/FCOM.
- **RVR reporting thresholds (1500 m ICAO)** and step sizes vary; verify per State AIP.
