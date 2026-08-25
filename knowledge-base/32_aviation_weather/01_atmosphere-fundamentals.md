---
id: aviation_weather.atmosphere
title: The atmosphere, the ISA, altimetry and stability
domain: 32_aviation_weather
tags: [isa, standard-atmosphere, altimetry, qnh, qfe, qne, transition-altitude, cold-temperature-correction, density-altitude, lapse-rate, dalr, salr, elr, stability, tephigram, skew-t, dewpoint, humidity]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "International Standard Atmosphere", url: "https://en.wikipedia.org/wiki/International_Standard_Atmosphere", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Altimeter setting", url: "https://en.wikipedia.org/wiki/Altimeter_setting", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Density altitude", url: "https://en.wikipedia.org/wiki/Density_altitude", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Skew-T log-P diagram", url: "https://en.wikipedia.org/wiki/Skew-T_log-P_diagram", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Fog", url: "https://en.wikipedia.org/wiki/Fog", publisher: "Wikipedia", accessed: 2026-08-25}
related: [aviation_weather.overview, aviation_weather.circulation, aviation_weather.hazards, aviation_weather.operations]
unit_system: mixed
---

# The atmosphere, the ISA, altimetry and stability

**Summary.** Everything operational in aviation meteorology rests on four relationships: the gas law linking pressure, density and temperature; the hydrostatic equation linking pressure to height; the adiabatic lapse rates that govern whether a displaced parcel returns or runs away; and the Clausius–Clapeyron relation that governs how much water vapour the air can hold. The International Standard Atmosphere is the fiction that turns a pressure measurement into an altitude, and every altimetry error a pilot deals with is the difference between that fiction and the real atmosphere. This file gives the full ISA table, works altimetry to operational depth including cold-temperature correction, and closes with parcel stability and how to read a tephigram or skew-T.

## Key facts

| Quantity | ISA value |
|---|---|
| Sea-level pressure | **1013.25 hPa** = 29.9213 inHg = 101 325 Pa |
| Sea-level temperature | **15.0 °C** = 288.15 K |
| Sea-level density | **1.2250 kg/m³** |
| Sea-level speed of sound | **340.294 m/s = 661.5 kt** |
| Standard gravity | **9.80665 m/s²** |
| Gas constant for dry air | **287.05287 J kg⁻¹ K⁻¹** |
| Tropospheric lapse rate | **6.5 °C/km = 1.98 °C/1000 ft** (call it 2 °C/1000 ft) |
| Tropopause (ISA) | **11 km = 36 089 ft**, −56.5 °C, 226.32 hPa, ρ = 0.3639 kg/m³ |
| Pressure lapse near sea level | **≈ 1 hPa per 27 ft** (30 ft is the common working figure) |
| Pressure lapse near FL180 | ≈ 1 hPa per 50 ft |
| Pressure lapse near FL350 | ≈ 1 hPa per 100 ft |
| Dry adiabatic lapse rate (DALR) | **9.8 °C/km ≈ 3 °C/1000 ft** |
| Saturated adiabatic lapse rate (SALR) | **~4 °C/km in warm moist air to ~9 °C/km in very cold air**; 1.5–1.8 °C/1000 ft is the low-level working figure |
| Cold-temperature correction rule of thumb | **≈ 4 % of height per 10 °C below ISA** |
| Fog/mist boundary | fog: visibility **< 1000 m**; mist (BR): 1000 m to 5000 m with RH generally ≥ 95 % |

> ⚠️ The 4 %/10 °C rule and the tables below correct **height above the altimeter setting source**, not indicated altitude. Apply them to the *height* portion, then add the aerodrome elevation back.

## 1. Composition and vertical structure

### 1.1 Composition

Dry air by volume: nitrogen 78.08 %, oxygen 20.95 %, argon 0.93 %, carbon dioxide ~0.042 % and rising, then trace gases. This mixture is essentially constant up to about 80–100 km (the **homosphere**) because turbulent mixing dominates molecular diffusion. Above the turbopause lies the **heterosphere**, where gases stratify by molecular weight.

The variable constituents are what matter:

- **Water vapour** — 0 to about 4 % by volume, almost all of it below 500 hPa, concentrated in the lowest 2 km. It carries the latent heat that drives convection and it is the reason the saturated lapse rate differs from the dry one.
- **Ozone** — peaks around 20–25 km. It absorbs UV and is the reason the stratosphere warms with height. Cabin ozone is an operational issue on high-latitude cruise in spring; aircraft certified for high altitude carry ozone converters.
- **Aerosol** — sea salt, mineral dust (very relevant in the Gulf), sulphate, soot, volcanic ash. Cloud condensation nuclei and ice nuclei come from here, and so does most visibility reduction that is not water.

### 1.2 Layers

| Layer | Top | Temperature behaviour | Aviation relevance |
|---|---|---|---|
| **Troposphere** | 8–9 km polar, 11 km mid-latitude ISA, 16–18 km equatorial | Decreases with height | All weather; the flight envelope of most of the fleet |
| **Tropopause** | — | Inversion / isothermal boundary | Jet cores, CAT, cirrus, aircraft optimum cruise, CB tops |
| **Stratosphere** | ~50 km | Isothermal then increasing (ozone heating) | Very stable, no convection; Concorde and business jets clip the bottom; volcanic aerosol resides here for years |
| **Stratopause** | ~50 km, ~0 °C | Maximum | — |
| **Mesosphere** | ~85 km | Decreasing to ~−90 °C, coldest place in the atmosphere | Noctilucent clouds |
| **Thermosphere** | ~500–1000 km | Increasing steeply with solar activity | Aurora, LEO drag |

The **tropopause height varies with latitude and season** and is discontinuous at the jet streams — the polar and subtropical jets sit in tropopause "breaks" where the boundary folds. Practical consequences: at the equator you may not reach the tropopause at all in a widebody, and CB tops in the ITCZ routinely reach FL500+; over Siberia in winter the tropopause can be below FL300 and the tropopause temperature can be warmer than the air below it, which is why you can get cruise-level temperature *rising* as you climb.

## 2. The International Standard Atmosphere

Defined identically in **ICAO Doc 7488** and **ISO 2533**, built on constant *geopotential* altitude layers with linear temperature lapse in each.

### 2.1 The defining layer table

| Layer | Base geopotential alt (km) | Base alt (ft) | Base temperature (K / °C) | Base pressure (hPa) | Lapse rate (K/km) |
|---|---|---|---|---|---|
| Troposphere | 0 | 0 | 288.15 / +15.0 | 1013.25 | **−6.5** |
| Tropopause / lower stratosphere | 11 | 36 089 | 216.65 / −56.5 | 226.32 | **0.0** |
| Stratosphere | 20 | 65 617 | 216.65 / −56.5 | 54.749 | **+1.0** |
| Stratosphere | 32 | 104 987 | 228.65 / −44.5 | 8.6802 | **+2.8** |
| Stratopause | 47 | 154 199 | 270.65 / −2.5 | 1.1091 | **0.0** |
| Mesosphere | 51 | 167 323 | 270.65 / −2.5 | 0.66939 | **−2.8** |
| Mesosphere | 71 | 232 940 | 214.65 / −58.5 | 0.039564 | **−2.0** |
| Top of ISA | 84.852 | 278 386 | 186.95 / −86.2 | — | — |

### 2.2 The working table a pilot needs

Computed from the ISA definition above (geopotential feet):

| Pressure altitude | ISA temperature | Pressure | Density | Speed of sound |
|---|---|---|---|---|
| 0 ft | +15.0 °C | 1013.25 hPa | 1.2250 kg/m³ | 661.5 kt |
| 1 000 ft | +13.0 °C | 977.17 hPa | 1.1896 | 659.2 kt |
| 2 000 ft | +11.0 °C | 942.13 hPa | 1.1549 | 656.9 kt |
| 5 000 ft | +5.1 °C | 843.07 hPa | 1.0555 | 650.0 kt |
| 8 000 ft | −0.9 °C | 752.62 hPa | 0.9629 | 643.0 kt |
| 10 000 ft | −4.8 °C | 696.82 hPa | 0.9046 | 638.3 kt |
| 14 000 ft | −12.7 °C | 595.24 hPa | 0.7963 | 628.8 kt |
| 18 000 ft | −20.7 °C | 506.00 hPa | 0.6981 | 619.2 kt |
| 20 000 ft | −24.6 °C | 465.63 hPa | 0.6527 | 614.3 kt |
| 25 000 ft | −34.5 °C | 376.01 hPa | 0.5489 | 601.9 kt |
| 30 000 ft | −44.4 °C | 300.90 hPa | 0.4583 | 589.3 kt |
| 34 000 ft | −52.4 °C | 249.99 hPa | 0.3944 | 579.0 kt |
| **36 089 ft** | **−56.5 °C** | **226.32 hPa** | 0.3639 | 573.6 kt |
| 38 000 ft | −56.5 °C | 206.46 hPa | 0.3320 | 573.6 kt |
| 40 000 ft | −56.5 °C | 187.54 hPa | 0.3016 | 573.6 kt |
| 45 000 ft | −56.5 °C | 147.48 hPa | 0.2371 | 573.6 kt |
| 50 000 ft | −56.5 °C | 115.97 hPa | 0.1865 | 573.6 kt |

Two useful memory anchors: **FL180 is almost exactly half sea-level pressure (506 hPa)**, and **FL340 is almost exactly a quarter (250 hPa)**. The 250 hPa and 300 hPa charts are therefore the ones you look at for cruise winds in a widebody, and 200 hPa (≈ FL390) for the very top.

ISA deviation, written ISA+15 or ISA−10, is `OAT − (15 − 1.98 × PA/1000)` for PA below the tropopause and `OAT − (−56.5)` above it. Above the tropopause, ISA+20 means −36.5 °C, not "warm".

### 2.3 The gas law and the hydrostatic equation

- **Ideal gas**: `p = ρ R T`. Density falls if pressure falls *or* temperature rises. This is the whole of density altitude.
- **Hydrostatic**: `dp/dz = −ρ g`. Because ρ falls with height, the pressure interval per unit height stretches with altitude — hence 27 ft/hPa near the surface, ~100 ft/hPa near FL350.
- **Moist air is less dense than dry air at the same p and T**, because the molar mass of water (18) is less than that of dry air (28.96). The humidity effect on density altitude is real but small compared with temperature — of order a few hundred feet at high temperature and high humidity, which is why Gulf operations are dominated by temperature rather than humidity even though summer dewpoints at OTHH can exceed 25 °C.

## 3. Altimetry

### 3.1 The instrument

A pressure altimeter is an aneroid capsule measuring static pressure, with a scale calibrated **to the ISA**. It converts pressure to altitude using the ISA relationship *only*. The subscale (Kollsman window) shifts the datum. It has no knowledge of actual temperature.

### 3.2 The Q-codes

| Setting | Definition | Altimeter reads |
|---|---|---|
| **QNH** | Pressure reduced to mean sea level using the ISA relationship from the station | **Altitude AMSL**; reads aerodrome elevation on the ground |
| **QFE** | Actual pressure at the aerodrome reference datum (or threshold) | **Height above that datum**; reads zero on the ground |
| **QNE** | The *indication* obtained with 1013.25 hPa set — i.e. pressure altitude | **Flight level** |
| **QFF** | Pressure reduced to MSL using the *actual* observed temperature profile | Used on synoptic charts, **not** on altimeters |

QNH is what you fly on below transition; QFE survives in some military use, in parts of the former Soviet sphere (though metric QFE has largely gone), and in some Chinese operations historically. **QFF vs QNH matters when reading an analysis chart**: the isobars on a synoptic chart are QFF, so a station's plotted MSLP need not equal its reported QNH, and in a very cold high-elevation environment the difference can be several hectopascals.

### 3.3 Transition altitude, level and layer

- **Transition altitude (TA)** — the altitude at or below which vertical position is expressed as altitude on QNH. State- or aerodrome-specific. Europe is moving toward a harmonised **TA of 5000 ft** in many FIRs; the UK adopted a common 18 000 ft TA in some airspace as part of that programme; the US and Canada use **18 000 ft**; much of the Gulf uses **13 000 ft** (verify the current AIP value for OTHH/OMDB before relying on it).
- **Transition level (TL)** — the lowest flight level available above the TA. Determined by ATC from the QNH so that the transition layer gives at least a minimum vertical buffer (commonly 1000 ft).
- **Transition layer** — the airspace between TA and TL. You do not cruise in it.

Climbing: set 1013 passing TA. Descending: set QNH passing TL. Two altimeters, cross-check within tolerance (commonly ±75 ft of field elevation on the ground; check the AFM/MEL).

### 3.4 Pressure error — "high to low, look out below"

An altimeter set to a QNH that is higher than the QNH where you actually are will **over-read** — it thinks you are higher than you are. Flying from a high-pressure region into a low-pressure region without resetting, the altimeter over-reads and **the aircraft is lower than indicated**. Hence the mnemonic, which applies to pressure *and*, in its second half, to temperature.

**Quantification: 1 hPa ≈ 27 ft near sea level; use 30 ft.** A 20 hPa fall in QNH (very ordinary crossing a deep Atlantic low) is **600 ft of error** — more than a terrain clearance margin. This is why oceanic and remote-area operations that use pressure altitude for level allocation are safe (everybody shares the same fiction) while approach on a stale QNH is not.

The same arithmetic runs the other way for **QNH below 1013 and flight levels**: with QNH 980, FL80 is only about 8000 − (33 × 30) ≈ 7010 ft AMSL. Minimum usable flight levels in the AIP are published against QNH bands for exactly this reason.

### 3.5 Temperature error and cold-temperature correction

The altimeter assumes an ISA column between the setting source and the aircraft. If the real column is **colder than ISA it is denser, pressure falls off faster with height, and a given pressure occurs at a lower true height** — the altimeter over-reads and **the aircraft is lower than indicated**. Warmer than ISA: the aircraft is higher than indicated (safe for terrain, but relevant for level-bust and for wake separation).

**Rule of thumb: 4 % of the height above the setting source per 10 °C of ISA deviation.**

Indicative correction table (feet to **add** to the published height above the altimeter setting source, computed from the standard temperature-correction formula; ICAO publishes a rounded version of this in PANS-OPS Doc 8168, Volume I):

| Height above source (ft) | 0 °C | −10 °C | −20 °C | −30 °C | −40 °C | −50 °C |
|---|---|---|---|---|---|---|
| 200 | 11 | 19 | 28 | 37 | 47 | 58 |
| 300 | 17 | 29 | 42 | 56 | 71 | 88 |
| 400 | 22 | 38 | 55 | 74 | 95 | 117 |
| 500 | 28 | 48 | 69 | 93 | 118 | 146 |
| 600 | 33 | 57 | 83 | 111 | 142 | 175 |
| 800 | 44 | 76 | 111 | 149 | 189 | 234 |
| 1 000 | 55 | 95 | 139 | 186 | 237 | 293 |
| 1 500 | 83 | 143 | 209 | 279 | 356 | 440 |
| 2 000 | 111 | 192 | 279 | 373 | 476 | 588 |
| 3 000 | 167 | 288 | 420 | 562 | 717 | 886 |
| 4 000 | 223 | 386 | 562 | 753 | 961 | 1187 |
| 5 000 | 280 | 484 | 706 | 945 | 1206 | 1491 |

Read the column at the **aerodrome temperature** (not the temperature at your level). The correction is applied to **all published minimum altitudes on the procedure** — MSA, sector altitudes, initial and intermediate approach altitudes, the FAF crossing altitude, step-downs, DA/MDA, and the missed-approach altitudes — and to the **minimum en-route altitudes** in mountainous terrain. It is *not* applied to the FL assignment above transition, because everybody shares the error.

Operationally: many States publish a **cold-temperature-restricted-airports list** with a temperature below which correction is mandatory (the FAA does this explicitly); many modern FMS/aircraft have an automatic temperature-compensation function for the vertical path. **Baro-VNAV approaches have a published minimum temperature** precisely because the vertical path is a pressure path; below that temperature the approach is not authorised. LPV/SBAS approaches use a geometric path and are not subject to the error, but the published minimum altitudes on the missed approach still are.

> ⚠️ Warm-temperature error is the reverse and is *not* corrected on approach — but it is a factor in level busts and in ADS-B/Mode C reporting versus true height in very hot conditions. It also means that on a 48 °C Doha day your true height above the ground is greater than indicated, which flatters obstacle clearance but does not flatter your climb performance.

### 3.6 Other altimeter errors

- **Position/static source error** — the static port does not sample true free-stream pressure; corrected by the ADC calibration, residual error shows in the AFM as an altimetry system error (ASE). Contamination or blockage of the static ports removes all validity (see Aeroperú 603 in `09`).
- **Instrument error** — mechanical hysteresis and friction in a conventional altimeter; negligible in an air data computer.
- **Lag** — the capsule takes finite time to equalise; significant in rapid descents on old instruments.
- **RVSM** requires demonstrated altimetry system error performance, two independent altimetry systems, an automatic altitude-hold, and an altitude alerter; 1000 ft vertical separation above FL290 depends on it.

## 4. Density altitude and its performance consequences

**Density altitude = the pressure altitude at which ISA density equals the actual density.** It is not a navigational altitude; it is a performance index.

Approximation: **DA ≈ PA + 120 × (OAT − ISA temperature at that PA)** in feet, °C. A useful cross-check: DA ≈ PA + 118.8 × ΔISA.

**Worked example — Doha, a summer afternoon.** OTHH elevation is low (a few metres AMSL). Take QNH 1000 hPa and OAT 48 °C:
- Pressure altitude ≈ elevation + (1013 − 1000) × 27 ≈ 0 + 351 ≈ **350 ft**
- ISA temperature at 350 ft ≈ 15 − 0.7 = 14.3 °C
- ΔISA = 48 − 14.3 = **+33.7 °C**
- DA ≈ 350 + 120 × 33.7 ≈ **4 400 ft**

A sea-level runway performing like a 4 400 ft airfield. Consequences, all simultaneous:

1. **Thrust falls.** Turbofan thrust is roughly proportional to inlet air density above the flat-rate break temperature. Every engine is *flat-rated* to a corner temperature (typically ISA+15) and above it available thrust drops steeply with OAT. Doha in July is far above every flat-rating corner.
2. **TAS for a given IAS rises.** `TAS ≈ IAS × √(ρ₀/ρ)`. At DA 4400 ft the ratio is about 1.07, so V1/VR/V2 as *ground speeds* are ~7 % higher, and takeoff distance scales roughly with the square of that — around 14 % more distance for the same IAS schedule, before the thrust loss.
3. **Climb gradient falls.** Both because of reduced thrust and because gradient = (thrust − drag)/weight and TAS is higher, so the same gradient needs more rate of climb.
4. **Net effect on payload.** On a long sector out of Doha in July the limiting case is usually **the second-segment climb or the obstacle-limited weight, not the field length**, and the answer is either an earlier departure slot, a lower assumed-temperature-derate that is not available, a packs-off takeoff, or offload.
5. **Engine-out drift-down and terrain** in the same conditions is worse for identical reasons — see `06`.

Humidity's contribution: at 48 °C and a dewpoint of 25 °C the vapour pressure is about 32 hPa out of ~1000, and the density reduction is roughly 1 %, worth perhaps another 250–300 ft of density altitude. Real, second-order, and generally already inside the performance data's conservatism — but it is why "hot and humid" is worse than "hot and dry" at the same temperature.

## 5. Humidity, dewpoint and saturation

- **Vapour pressure (e)** — the partial pressure of water vapour. **Saturation vapour pressure (eₛ)** depends on temperature alone, and roughly **doubles for every 10 °C** (Clausius–Clapeyron). This exponential is why tropical air holds so much more moisture than polar air and why deep convection is a tropical speciality.
- **Relative humidity** = e/eₛ × 100 %. A poor conserved variable — it changes when the air merely warms or cools.
- **Dewpoint (Td)** — the temperature to which air must be cooled at constant pressure and mixing ratio to reach saturation. **Conserved under simple heating/cooling**, therefore the variable a forecaster actually uses.
- **Mixing ratio (w)** — grams of vapour per kilogram of dry air. Conserved under vertical motion too, until condensation. This is the line you follow on a tephigram.
- **Wet-bulb temperature (Tw)** — reached by evaporating water into the parcel at constant pressure. Always between T and Td. The **wet-bulb zero height** is a useful hail and downburst predictor.
- **Wet-bulb potential temperature (θw)** — conserved under both dry and saturated adiabatic processes. It is the *air mass label*: it barely changes as air rises, sinks, condenses or evaporates, so a discontinuity in θw is a front.

**Operational shortcuts:**
- **Temperature/dewpoint spread ≤ 3 °C with light wind and clear skies at night → expect radiation fog** (see `03`). Fog by definition is visibility below 1000 m.
- **Cloud base (ft AGL) ≈ 400 × (T − Td) in °C** at the surface — the convective condensation level for a surface-based parcel, using DALR 3 °C/1000 ft against a dewpoint lapse of ~0.5 °C/1000 ft, giving a spread closure of 2.5 °C/1000 ft, hence ~400 ft per °C. Good for cumulus bases, useless for stratus or frontal cloud.
- **Carburettor and airframe icing** care about liquid water content, not RH.

## 6. Lapse rates and stability

### 6.1 The three rates

| Rate | Symbol | Value | What it is |
|---|---|---|---|
| **Dry adiabatic** | DALR / Γd | **9.8 °C/km ≈ 3.0 °C/1000 ft** | The rate an unsaturated parcel cools when lifted, from expansion alone. A physical constant, g/cp. |
| **Saturated adiabatic** | SALR / Γs | **~4 °C/km (warm, moist) to ~9 °C/km (cold, dry)**; 1.5–1.8 °C/1000 ft is the low-level working figure | A saturated parcel cools more slowly because condensation releases latent heat. **Not a constant** — it depends on temperature and pressure. |
| **Environmental** | ELR | **Whatever the sounding says**; ISA's 6.5 °C/km is only an average | The actual temperature profile of the air the parcel moves through. Measured, not derived. |

### 6.2 Stability classification

Compare ELR against the two adiabats:

| Condition | Criterion | Behaviour |
|---|---|---|
| **Absolutely stable** | ELR < SALR | A displaced parcel, saturated or not, returns. Layer cloud, poor dispersion, smooth flight, fog and low stratus, trapped pollution. |
| **Saturated neutral** | ELR = SALR | — |
| **Conditionally unstable** | SALR < ELR < DALR | Stable if dry, unstable if saturated. **This is the normal state of the atmosphere** and the reason a trigger matters: heating, orographic lift, frontal lift or convergence. |
| **Dry neutral** | ELR = DALR | Well-mixed boundary layer, typical afternoon over a desert. |
| **Absolutely unstable** | ELR > DALR | Cannot persist except in a shallow superadiabatic surface layer over strongly heated ground — exactly what a Gulf runway surface produces mid-afternoon, and the source of low-level thermal turbulence and dust devils. |
| **Inversion** | ELR negative | The most stable case. Radiation inversion at night, subsidence inversion under an anticyclone, frontal inversion, and the trade-wind inversion. Caps convection, traps haze/dust, and creates low-level wind shear at its top. |
| **Potential (convective) instability** | θw *decreases* with height | A stable layer that becomes unstable when the whole layer is lifted, because the moist bottom saturates first. The mechanism behind pre-frontal squall lines and much monsoon convection. |

### 6.3 Why it matters in the flight deck

- Stable air → stratiform cloud, drizzle, freezing rain risk from warm-over-cold, continuous icing at a defined level, poor visibility, smooth ride, persistent fog, strong low-level shear at inversion tops, and *good* radio propagation ducting.
- Unstable air → cumuliform cloud, showers, hail, gusty surface winds, good visibility between showers, severe turbulence, downbursts and windshear on approach.
- The transition from one to the other along a route is what a SIGWX chart is trying to draw.

## 7. Reading a tephigram / skew-T

Both are thermodynamic diagrams designed so that **area on the diagram is proportional to energy**. The tephigram plots temperature against entropy (log θ) with the whole plot rotated ~45° so that pressure lines run roughly horizontally; the **skew-T log-P** plots log pressure on the vertical and temperature skewed at 45°. The Americas use skew-T; the UK and much of the Commonwealth tradition uses the tephigram. The lines mean the same things.

### 7.1 The five families of lines

1. **Isotherms** — constant temperature, straight, running lower-left to upper-right at 45°.
2. **Isobars** — constant pressure, roughly horizontal, log-spaced.
3. **Dry adiabats** (constant potential temperature θ) — curving from lower-right to upper-left, steeper than the isotherms. A parcel lifted unsaturated follows one.
4. **Saturated adiabats** (constant θw or θe) — curved, sloping left, asymptotic to the dry adiabats at very cold temperatures (because there is no vapour left to release latent heat). A saturated parcel follows one.
5. **Saturation mixing ratio lines** — nearly straight, slightly sloping, labelled in g/kg. A parcel's dewpoint follows one when lifted unsaturated.

### 7.2 The two traces

The sounding plots **temperature** (right-hand curve) and **dewpoint** (left-hand curve). The horizontal gap between them is the dewpoint depression: where they touch, the air is saturated — a cloud layer. Wind barbs are plotted alongside at their pressure levels.

### 7.3 The construction a forecaster does

1. **Lifting Condensation Level (LCL)** — from the surface temperature follow a **dry adiabat** up; from the surface dewpoint follow a **mixing-ratio line** up; where they intersect is the LCL. That is the cumulus base for a surface parcel. (Compare with the 400 ft/°C rule.)
2. **Convective Condensation Level (CCL)** and **convective temperature** — from the surface dewpoint follow the mixing-ratio line up until it cuts the environmental temperature curve: that height is the CCL. Come back down a dry adiabat to the surface: that temperature is the **convective temperature**, the surface temperature needed for spontaneous convection. This is the classic "what time will the thunderstorms fire" calculation.
3. **Level of Free Convection (LFC)** — above the LCL, follow a **saturated adiabat**; where the parcel first becomes warmer than the environment is the LFC.
4. **Equilibrium Level (EL)** — continue the saturated adiabat up until the parcel is again colder than the environment. That is the anvil level / storm top (real tops overshoot it by momentum).
5. **CAPE** — the area between the parcel's saturated adiabat and the environment curve, from LFC to EL, in J/kg. Rough scale: <1000 marginal, 1000–2500 moderate, 2500–4000 strong, >4000 extreme. Maximum theoretical updraft `w ≈ √(2·CAPE)`: CAPE 2500 J/kg → 70 m/s, about 14 000 ft/min, before entrainment and water loading. This is the number behind hail size and overshooting tops.
6. **CIN** — the negative area below the LFC, the "cap". A strong cap suppresses convection all afternoon and then breaks explosively.
7. **Freezing level and the −20 °C level** — read directly off the temperature trace. Airframe icing risk lives between roughly 0 °C and −20 °C in liquid cloud; the layer between 0 °C and −20 °C in a CB is the hail growth zone; the **wet-bulb freezing level** determines whether hail survives to the surface.
8. **Inversion identification** — any layer where temperature increases with height, plus the moisture structure across it, tells you about trapped haze, low-level jet, and shear.
9. **Icing type** — a saturated layer between 0 °C and −15 °C with a *small* dewpoint depression and a steep lapse (cumuliform) suggests clear ice; a shallow saturated stable layer suggests rime. A warm nose above 0 °C over a sub-freezing surface layer is the freezing-rain signature.

### 7.4 Instability indices you will see quoted

| Index | Meaning | Rough thresholds |
|---|---|---|
| **Lifted Index (LI)** | Environment T minus parcel T at 500 hPa | 0 to −3 marginal; −4 to −6 unstable; < −6 very unstable |
| **K Index** | Combines mid-level moisture and lapse rate | > 30 thunderstorms likely; > 40 heavy convection |
| **Total Totals** | (T850 + Td850) − 2·T500 | > 50 thunderstorms; > 55 severe |
| **Showalter** | LI from 850 hPa | < −3 severe possible |
| **Bulk Richardson Number** | CAPE / shear | 10–45 favours supercells |
| **Gradient Richardson Number (Ri)** | static stability / squared shear | **Ri < 0.25 → turbulence likely** — the CAT criterion |

Ri is worth internalising: `Ri = (g/θ)(∂θ/∂z) / (∂u/∂z)²`. Big stability over small shear = laminar. Increase the shear or reduce the stability and the flow goes turbulent through Kelvin–Helmholtz instability. That is why CAT lives on the *edges* of the jet where shear is large and just below the tropopause where stability changes abruptly, and it is why the billow clouds you occasionally see at the tropopause are the visible form of the thing shaking the aeroplane.

## Sources

- [International Standard Atmosphere](https://en.wikipedia.org/wiki/International_Standard_Atmosphere) — Wikipedia (sea-level constants; 11/20/32 km nodes cross-checked against computed values)
- [Altimeter setting](https://en.wikipedia.org/wiki/Altimeter_setting) — Wikipedia (QNH/QFE/QNE, transition altitude/level/layer)
- [Density altitude](https://en.wikipedia.org/wiki/Density_altitude) — Wikipedia (definition, the 120 ft per °C approximation, performance effects)
- [Skew-T log-P diagram](https://en.wikipedia.org/wiki/Skew-T_log-P_diagram) — Wikipedia (axes, relation to the tephigram)
- [Fog](https://en.wikipedia.org/wiki/Fog) — Wikipedia (fog/mist visibility definition, 2.5 °C spread)

ISA layer table, pressure/density/speed-of-sound table, and the cold-temperature correction table were **computed** from the ISA definition and the standard temperature-correction formula and cross-checked against the published nodes above.

## Open questions

- The cold-temperature correction table here is **computed**, not transcribed from **ICAO Doc 8168 (PANS-OPS) Volume I, Table III-1-4-1**. Values agree with the published table to within a few feet at the nodes checked, but transcribe the official table before publishing operational cards. `needs-verification`
- **Transition altitudes** quoted (Europe 5000 ft harmonisation, Gulf 13 000 ft) must be checked against the current AIP for each aerodrome — they change. `needs-verification`
- The **±75 ft** altimeter pre-flight check tolerance is a common figure but is aircraft- and operator-specific; check the AFM/MEL.
- Exact **baro-VNAV minimum temperature** values are procedure-specific and published on the chart.
