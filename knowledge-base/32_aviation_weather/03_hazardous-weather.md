---
id: aviation_weather.hazards
title: Hazardous weather — convection, shear, turbulence, icing, ash, dust, fog, space weather
domain: 32_aviation_weather
tags: [thunderstorm, microburst, downburst, windshear, llwas, tdwr, pws, turbulence, cat, mountain-wave, wake-turbulence, recat, icing, sld, holdover-time, volcanic-ash, vaac, dust-storm, shamal, haboob, fog, lvp, rvr, space-weather]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Downburst / microburst", url: "https://en.wikipedia.org/wiki/Microburst", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Supercell", url: "https://en.wikipedia.org/wiki/Supercell", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Terminal Doppler Weather Radar", url: "https://en.wikipedia.org/wiki/Terminal_Doppler_Weather_Radar", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Clear-air turbulence", url: "https://en.wikipedia.org/wiki/Clear-air_turbulence", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Lee wave", url: "https://en.wikipedia.org/wiki/Lee_wave", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Wake turbulence", url: "https://en.wikipedia.org/wiki/Wake_turbulence", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Atmospheric icing", url: "https://en.wikipedia.org/wiki/Atmospheric_icing", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Volcanic Ash Advisory Center", url: "https://en.wikipedia.org/wiki/Volcanic_Ash_Advisory_Center", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Volcanic ash", url: "https://en.wikipedia.org/wiki/Volcanic_ash", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Air travel disruption after the 2010 Eyjafjallajökull eruption", url: "https://en.wikipedia.org/wiki/Air_travel_disruption_after_the_2010_Eyjafjallaj%C3%B6kull_eruption", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Haboob", url: "https://en.wikipedia.org/wiki/Haboob", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Fog", url: "https://en.wikipedia.org/wiki/Fog", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "NOAA Space Weather Scales", url: "https://www.swpc.noaa.gov/noaa-scales-explanation", publisher: "NOAA SWPC", accessed: 2026-08-25}
  - {title: "FAA Aircraft Ground Deicing (Holdover Tables)", url: "https://www.faa.gov/other_visit/aviation_industry/airline_operators/airline_safety/deicing", publisher: "FAA", accessed: 2026-08-25}
related: [aviation_weather.atmosphere, aviation_weather.circulation, aviation_weather.products, aviation_weather.operations, aviation_weather.cases]
unit_system: mixed
---

# Hazardous weather — convection, shear, turbulence, icing, ash, dust, fog, space weather

**Summary.** This is the operational core of the domain. Each hazard is treated the same way: the physics, the recognition cues (visual, radar, satellite, forecast product), the numbers that define severity, and the procedure. The order roughly follows likelihood of ruining your day: convection first, then shear, then turbulence, then icing, then the less frequent but high-consequence hazards — ash, dust, low visibility and space weather.

## Key facts

| Hazard | Defining numbers |
|---|---|
| Microburst | outflow **≤ 4 km (2.5 mi)** diameter; macroburst larger. Winds to **240 km/h (150 mph)**; record 240.5 km/h at Andrews Field, 1 Aug 1983. Lifetime a few minutes; downdraft ~25 m/s |
| Thunderstorm avoidance | **20 nm** lateral from a cell with tops above FL350 or with hail/severe echo; **5000 ft** vertically over a cell top and never *through* an anvil |
| Hail | can be thrown **20+ nm downwind of the core in clear air** beneath the anvil |
| CAT | ~**64 %** of non-light turbulence observed within **150 nm** of a jet core; **Ri < 0.25** is the instability criterion |
| CAT climate trend | transatlantic winter CAT projected **+60 % light, +95 % moderate, +150 % severe** at CO₂ doubling |
| Mountain wave | needs wind **> 20 kt at ridge top**, within **30°** of perpendicular, increasing with height, stable layer |
| Icing peak | half of reported icing between **−8 °C and −12 °C**; icing impossible below **−48 °C** (all water frozen) |
| Wake vortices | sink **300–490 ft/min**, level off **150–270 m (500–900 ft)** below the generator; move laterally **2–3 kt** in ground effect |
| Volcanic ash | melts in the combustor to **glass**, resolidifies on turbine nozzles → compressor stall and thrust loss |
| 2010 ash thresholds | UK CAA set **200–2000 µg/m³** on 21 Apr 2010, revised to **4 mg/m³** on 18 May 2010 |
| Haboob | **up to 2000 m deep**, dust wall to **100 km wide**, advancing at up to **70 km/h**, lasting up to **6 h** |
| Fog | visibility **< 1000 m**; forms when T−Td **< 2.5 °C** |
| Space weather | **R1–R5** radio blackout, **S1–S5** solar radiation, **G1–G5** geomagnetic (NOAA scales) |

> ⚠️ Every avoidance figure above is a *minimum*. Company OM-A/OM-B figures, if larger, govern. Nothing here authorises penetrating convection.

## 1. Thunderstorms

### 1.1 Ingredients and the three stages

A thunderstorm needs **moisture, instability and a lift trigger**. Organisation into anything more than a single cell additionally needs **vertical wind shear**.

| Stage | Duration | Vertical motion | Radar / visual | Hazard |
|---|---|---|---|---|
| **Cumulus (developing)** | ~10–15 min | Updraft only, growing to 3000 ft/min | Hard cauliflower edges, no precipitation reaching the ground; first radar echo aloft | Turbulence, updraft; deceptively benign |
| **Mature** | ~15–30 min | Updraft **and** downdraft coexisting; anvil forms at the equilibrium level; overshooting top | Heavy precipitation core, gust front, lightning, hail | **All of them** — severe turbulence, hail, lightning, downburst, icing, heavy rain, tornado |
| **Dissipating** | ~30 min | Downdraft dominant, updraft cut off by its own outflow | Anvil spreads, echo weakens and lowers, precipitation lightens | Still severe turbulence and windshear; a collapsing cell can produce the strongest downburst of its life |

A single-cell (air-mass) storm lives ~30–60 minutes and rarely produces severe weather. **The organised forms are the problem.**

### 1.2 Organisation

- **Multicell cluster** — a sequence of cells at different stages; new cells form on the gust front on the flank where inflow converges. The cluster lives for hours while individual cells do not. Heavy rain, hail, downbursts.
- **Multicell line / squall line** — cells organised along a line, typically along or ahead of a cold front, with a leading gust front and a trailing stratiform region. Can extend hundreds of nautical miles with no usable gap. **A squall line has no safe transit** — the classic error is to aim at a radar gap that closes before you reach it, or that is a "blind alley" of attenuated echo.
- **Supercell** — a single, persistent **rotating updraft (mesocyclone)** in strong deep-layer shear. Lives many hours, deviates right of the mean wind (NH), and produces the extremes: giant hail, damaging winds, and about 30 % produce tornadoes. Sub-types: **LP** (low-precipitation, dry environments, huge hail from an almost clear sky), **classic**, **HP** (high-precipitation, rain wraps the mesocyclone — the most dangerous to fly near because the structure is hidden).
- **MCS / MCC (mesoscale convective system/complex)** — a large, long-lived, often nocturnal cluster with a common anvil, a leading convective line and a trailing stratiform region with a bright band. Sahel, Argentine pampas, US Great Plains, Indian monsoon, ITCZ. **AF447 crossed one.** Tops FL500+, hundreds of nautical miles across, and the convective cores are embedded and invisible.
- **Bow echo / derecho** — a line segment that bows forward under a rear-inflow jet, producing widespread straight-line damaging winds.

### 1.3 Radar signatures worth recognising

| Signature | Meaning |
|---|---|
| **Hook echo** | Mesocyclone; the reflectivity hook between the main updraft and the rear-flank downdraft. Possible tornado; a debris ball inside it means one is on the ground |
| **Bounded weak echo region (BWER) / vault** | Updraft so strong that hydrometeors have not yet formed — the strongest updraft signature there is |
| **Overshooting top** | Updraft has punched through the tropopause into the stratosphere. Severe |
| **V-notch / flying eagle** | Anvil-level flow splitting around a strong updraft |
| **Three-body scatter spike / hail spike** | Radar energy scattered ground–hail–ground. Diagnostic of large hail |
| **Bright band** | Melting layer in stratiform precipitation; a horizontal band of enhanced reflectivity at the 0 °C level. Not a hazard, but it fools you into thinking the stratiform region is convective |
| **Steep reflectivity gradient** | Tight packing of colour contours on airborne radar — the strongest single indicator of a hazardous cell |
| **Scalloped / U-shaped edges** | Turbulence and hail |

### 1.4 Avoidance rules

- **Lateral**: 20 nm from any cell with tops above FL350, from any cell showing a steep gradient or scalloped edge, and from all cells in the tropics where tops are systematically higher than they look. 10 nm is a bare minimum for benign-looking cells at low level; 20 nm is the working number in a widebody.
- **Vertical**: do not overfly a cell by less than 5000 ft above the visible top, and remember that at high cruise altitude you rarely have the performance to do so. Better to go round.
- **Never fly under an anvil** — hail is routinely thrown well downwind in clear air, and the ride is severe.
- **Upwind side, not downwind side.** Deviate into the wind wherever possible; the downwind side has the hail, the anvil and the new cell development on the outflow boundary... except that gust-front new-cell development is on the *inflow* flank, so the honest rule is: deviate to the side with the least reflectivity gradient and the most room, and re-evaluate every 5 minutes.
- **Squall line**: go round the end, or hold, or land somewhere else. Do not thread it.
- If penetration becomes unavoidable: turbulence penetration speed, seat belts, ignition on, engine anti-ice on, autothrottle off, attitude flying, accept altitude excursions, do not chase airspeed, and turn on all lights to reduce lightning-flash startle.

### 1.5 Hail

Grows by accretion in the **−10 °C to −30 °C** layer, cycling through the updraft. Updraft speed sets the maximum size: `w ≈ √(2·CAPE)`, so CAPE 3000 J/kg gives ~77 m/s, enough to support golf-ball-plus hail. Aviation consequences: radome destruction (which blinds the radar, removing the tool you need most), windshield crazing or failure, leading-edge and engine-inlet damage, and pitot/static damage. Hail can be encountered **in clear air up to 20 nm from the core**, most often beneath and downwind of the anvil, and at altitudes where the reflectivity looks weak because dry hail is a poor reflector at C/X-band — a genuine trap on airborne radar.

### 1.6 Lightning

An aircraft in flight is usually a *triggerer* rather than a victim: most strikes to aircraft are initiated by the airframe in a high field region. Statistically each aircraft is struck roughly once a year. Highest risk band is **around the freezing level, −5 °C to +5 °C, in or near cloud, in precipitation, and within 5 nm of convection**. Effects: entry/exit burn marks (usually radome, wingtips, static wicks, tail), transient upsets to avionics, compass error, occasional fuel-system and composite-structure concerns, crew flash-blindness, and rarely damage to the radome that then affects radar performance. St Elmo's fire and increasing precipitation static are the warning that field strength is building.

Certification: aircraft are designed to **SAE ARP5412/5414 lightning environment and zoning standards** and CS-25.581/25.899 bonding requirements — a strike should be a maintenance event, not a safety event.

### 1.7 Downbursts and microbursts

**Definition.** A downburst is a strong downdraft that induces an outward burst of damaging winds at the surface. **Microburst: outflow diameter ≤ 4 km (2.5 mi)**; larger is a **macroburst**. Most downbursts are microbursts.

**Mechanism.** Two contributions: **precipitation loading** (the weight of falling water dragging air down) and **evaporative/melting cooling** (negative buoyancy). Dry microbursts come from high-based convection over a deep dry sub-cloud layer — virga is the visual cue, and there may be no rain at the surface at all. This is a *very* Gulf/desert phenomenon. Wet microbursts come from heavy precipitation cores.

**Numbers.** Vertical velocity ~25 m/s in the core; horizontal outflow to **240 km/h (150 mph)**; the record measured event was **240.5 km/h at Andrews Field, Maryland, 1 August 1983**, minutes after Air Force One landed. Lifetime: a few minutes; the whole hazard can appear and vanish inside one approach sequence.

**The encounter profile on approach.** Flying into the outflow you first meet a **performance-increasing headwind** — airspeed rises, the aircraft balloons above the glidepath, and the instinctive reaction is to reduce thrust and push. Then you pass through the downdraft core — sinking air, high rate of descent. Then you exit into a **performance-decreasing tailwind** — airspeed collapses, lift collapses, and you are low, slow, with the thrust you reduced two hundred feet ago. Delta 191 and Pan Am 759 are the canonical cases (`09`).

> ⚠️ **Windshear escape manoeuvre (generic — fly your type's exact procedure):** simultaneously **maximum available thrust (TOGA / firewall)**, **disconnect autothrottle**, **rotate smoothly toward the pitch attitude in the FCOM (commonly 15° initially)**, **do not change configuration** (gear and flap stay where they are), **follow the flight director if it is a windshear-mode FD**, and **respect the stick shaker — fly to just below shaker, using intermittent shaker as the limit**. Accept altitude loss; the aim is to trade energy for survival, not to hold the glidepath. Announce it. Do not attempt to re-establish the approach.

**Prevention is the real procedure.** A microburst is survivable only marginally; avoidance is not optional. Cues: convective cloud within 3 nm of the approach or departure path, virga, a ring of blowing dust on the surface, a rain shaft with a visible curl, wind shift and temperature drop reported on ATIS, a PIREP of airspeed loss/gain of 15 kt or more, an LLWAS/TDWR microburst alert, or the aircraft's own **predictive windshear (PWS)** alert.

## 2. Windshear

**Definition.** A change of wind vector (speed and/or direction) over a short distance. Vertical shear is expressed in kt per 100 ft or per 1000 ft; horizontal shear in kt per nm.

**Severity classification (ICAO, vertical shear over 30 m/100 ft):** light < 4 kt, moderate 4–8 kt, strong 8–12 kt, severe > 12 kt per 100 ft.

**Sources:**
1. **Convective outflow / microburst** — the lethal case (above).
2. **Frontal shear** — a sharp front with a temperature difference > 5 °C and/or a frontal speed > 30 kt gives significant low-level shear as it passes the airport.
3. **Low-level jet under a nocturnal inversion** — the surface decouples from the flow above; 30–50 kt at 1000 ft AGL over calm surface winds. Common over deserts and plains, and a genuine Gulf night-approach factor.
4. **Terrain and buildings** — mechanical shear/turbulence, funnelling, downslope flow. Aerodromes like Innsbruck, Funchal, Wellington, Kathmandu, Queenstown live with it.
5. **Sea breeze front** and land breeze front — sharp wind shift, often with a shallow convergence line.
6. **Mountain wave** — rotor and downslope windstorm shear.
7. **Wake turbulence** (§4).

**Detection systems:**

| System | What it is | Strength / limitation |
|---|---|---|
| **LLWAS** (Low-Level Wind Shear Alert System) | A network of surface anemometers around the airport, comparing outlying sensors with a centre-field reference; alerts on divergence | Detects the shear at the surface only; LLWAS-NE (network expansion) with more sensors is much better. Cannot see aloft |
| **TDWR** (Terminal Doppler Weather Radar) | Dedicated Doppler radar at ~**5600–5650 MHz (5 cm / C-band)**, 0.5° beam, 250 kW, 150 m range resolution to 135 km, velocity data to ~90 km; **45 operational units in the US and Puerto Rico as of 2011** | Purpose-built to see microburst outflow and gust fronts in the terminal area; complements the longer-range NEXRAD. Not universally deployed outside the US |
| **Integrated TDWR/LLWAS** | Fused product driving the controller's alert display | The best ground-based combination |
| **Aircraft reactive windshear** | Compares inertial and air data to compute the shear the aircraft is *already* in; triggers "WINDSHEAR, WINDSHEAR, WINDSHEAR" | Reliable but only after entry |
| **Aircraft Predictive Windshear (PWS)** | The weather radar looks ahead in Doppler mode for the outflow divergence signature, typically to 3 nm and only below ~1200–2300 ft AGL | Gives 10–40 seconds of warning *before* entry: "MONITOR RADAR DISPLAY" (caution) or "WINDSHEAR AHEAD" (warning). Needs radar reflectors — it is weak on genuinely dry microbursts |
| **Doppler LIDAR** | Aerosol-based Doppler; sees dry shear a radar cannot | Deployed at Hong Kong (with the terrain-induced shear problem), Tokyo and others |

**Reporting.** Aerodrome **wind shear warnings** (Annex 3 Chapter 7) and **wind shear alerts** from automated systems; pilots should file a PIREP with the height band and the airspeed gain/loss.

## 3. Turbulence

### 3.1 Classification by cause

| Type | Mechanism | Where | Cue |
|---|---|---|---|
| **Convective** | Buoyancy-driven updrafts/downdrafts | In and near cumuliform cloud, and in clear air below cumulus | Visible cloud, radar, CAPE |
| **Mechanical** | Friction and obstacles | Boundary layer, especially with strong wind over rough terrain or buildings | Wind strength vs terrain roughness |
| **Thermal (low-level convective)** | Surface heating | Desert and land surfaces on hot afternoons, up to the inversion | Dust devils, superadiabatic layer |
| **Mountain wave and rotor** | Stable flow over a barrier | Downstream of ridges, from the surface to the stratosphere | Lenticulars, rotor cloud, foehn wall, cap cloud |
| **Clear air turbulence (CAT)** | Kelvin–Helmholtz instability in shear layers | Near the jet, tropopause, and in upper troughs | No visual cue; Ri, EDR forecasts, SIGWX |
| **Wake turbulence** | Aircraft-generated vortices | Behind and below other aircraft | Separation standards |
| **Frontal** | Shear and convergence at a front | Along fronts, worst at active cold fronts | Front position |

### 3.2 Intensity — the ICAO/EDR framework

Historically reported subjectively (light/moderate/severe/extreme) with definitions based on aircraft reaction and effect on occupants. The objective replacement is **EDR — eddy dissipation rate**, in m^(2/3)/s^(1/3), which is aircraft-independent and is what AMDAR-equipped fleets now downlink automatically and what WAFS turbulence forecasts are expressed in.

| Subjective | Effect | Approximate EDR |
|---|---|---|
| Light | Slight, erratic changes in attitude/altitude; occupants feel slight strain against belts | ~0.10–0.20 |
| Moderate | Changes in attitude/altitude but aircraft remains in control; occupants feel definite strain; unsecured objects dislodge | ~0.20–0.45 |
| Severe | Large abrupt changes; momentary loss of control; occupants forced violently against belts; food service impossible | ~0.45–0.70 |
| Extreme | Aircraft violently tossed, practically impossible to control; structural damage possible | > ~0.70 |

> ⚠️ The EDR bands above are indicative and are **aircraft-mass dependent in the mapping to the subjective scale**. Verify against ICAO Annex 3 Appendix 3 and your operator's turbulence reporting policy. `needs-verification`

### 3.3 Clear air turbulence in depth

CAT is **Kelvin–Helmholtz instability**: when the gradient Richardson number `Ri = (g/θ)(∂θ/∂z) / (∂u/∂z)²` falls below about **0.25**, a stably stratified sheared layer breaks down into billows and then into turbulence. Since Ri has stability on top and shear-squared underneath, CAT is favoured where **shear is large and stability is not overwhelming**.

Preferred locations:
- **Within 150 nm of the jet core** — one classic study found 64 % of non-light turbulence there.
- **On the cold (poleward) side and just below the core**, where the horizontal and vertical shear are both large.
- **In sharply curved upper troughs** — the sharper the curvature, the greater the CAT probability. Anticyclonic shear side of a jet in a sharp ridge is also productive.
- **At the tropopause**, especially across a **tropopause fold** — visible as a dark stripe on WV imagery.
- **Where two jets merge or a jet streak enters/exits.**
- **Above and downstream of mountain ranges** (mountain-wave CAT, which can reach the lower stratosphere).
- **Above thunderstorms** — CAT above and around the anvil, out to 20 nm.

Management: SIGWX chart CAT areas, WAFS EDR/turbulence GRIB fields, SIGMETs, PIREPs, and above all the ride reports from aircraft ahead of you on the same track. Tactically: **slow to turbulence penetration speed**, seat belts on early, altitude change of 2000–4000 ft (up or down — CAT layers are typically only 1000–3000 ft deep) or a lateral change of 25–50 nm perpendicular to the jet axis, and accept a level that is not optimum. Do not chase altitude in severe turbulence; fly attitude and accept ±. Note the transatlantic CAT climate signal (+60/95/150 % light/moderate/severe by CO₂ doubling) — turbulence encounters, and cabin injuries, are a growing exposure.

### 3.4 Mountain wave and rotor

**Conditions for significant mountain wave:**
1. Wind at ridge top **> 20 kt** (much more for severe wave).
2. Wind direction **within ~30° of perpendicular** to the ridge.
3. Wind speed **increasing with height** with little directional change.
4. A **stable layer near ridge top** with less stable air above and below (a "trapped lee wave" structure).

**Structure.** Upwind: a **cap cloud** on the summit and a **foehn wall** on the lee crest. Downwind: a train of **lenticular clouds (ACSL)** at the wave crests, stationary relative to the ground, stacked where alternating moist layers exist. Beneath the first wave crest: the **rotor** — a horizontal-axis vortex with its axis parallel to the ridge, marked by ragged cumulus, and the most violent turbulence in the system. Wavelength typically 5–25 km; wave amplitude and vertical velocities of 2000–5000 ft/min are routine, and extreme cases exceed that.

**Hazards.**
- **Rotor turbulence** — severe to extreme, at low level, exactly where you are on approach or departure at a mountain aerodrome.
- **Downslope windstorm** — the wave can break and bring stratospheric-strength winds to the surface on the lee slope (Boulder, Colorado windstorms; the Zonda; the Bora; Greenland's piteraq).
- **Altitude excursion at cruise** — sustained updraft or downdraft of 1000–2000 ft/min that the autopilot fights with pitch, driving the aircraft toward either overspeed or low-speed buffet. In thin air at high altitude the margin between the two is small; this is the "coffin corner" problem made real by mountain wave.
- **Wave-induced CAT** propagating into the lower stratosphere, hundreds of miles downstream.
- **Altimetry**: the local pressure field in a wave can shift the indicated altitude.

**Regions**: Rockies (Colorado Front Range, Sierra Nevada), Greenland (both coasts, plus tip jets), Andes (the most reliable in the world), Alps, Scandinavian mountains, Southern Alps of New Zealand, Japan (Mount Fuji — BOAC 911, 1966), Himalaya, the Zagros (relevant to eastbound Gulf departures), and the Hajar of Oman.

**Management**: avoid the lee side below the wave crests; if crossing, cross at 50–100 % of the ridge height above it or higher, at turbulence penetration speed, expecting altitude excursions; consider crossing at 45° to the ridge to shorten exposure and preserve an escape turn; and treat SIGWX mountain-wave symbols as real.

### 3.5 Wake turbulence

**Physics.** Lift implies a bound circulation, which sheds as a pair of counter-rotating **wingtip vortices**. Strength scales with **weight / (air density × airspeed × wingspan)** — so the worst generator is **heavy, slow, clean** (i.e. shortly after takeoff and on approach with flaps up or a low-drag configuration).

**Behaviour.**
- Vortices **sink at 300–490 ft/min** and **level off 500–900 ft (150–270 m) below** the generating aircraft's flight path.
- They **decay** by viscous diffusion and by atmospheric turbulence — so they persist longest in **stable, light-wind conditions** and dissipate fastest in a gusty, convective boundary layer.
- **In ground effect** they stop descending and **move laterally outward at 2–3 kt**. A **crosswind of 3–5 kt can hold the upwind vortex over the runway** while blowing the downwind one onto the parallel — the classic parallel-runway trap.
- The hazard is the **induced roll**: a vortex can impose rolling moments exceeding the roll authority of a lighter aircraft.

**Categorisation.** ICAO's legacy scheme, still the default in most airspace:

| ICAO category | MTOW |
|---|---|
| **Heavy (H)** | 136 000 kg or more |
| **Medium (M)** | more than 7 000 kg, less than 136 000 kg |
| **Light (L)** | 7 000 kg or less |
| **Super (J)** | applied to the A380-800 (and An-225) by special provision |

The FAA additionally treats the **Boeing 757** with heavy-aircraft separation because its wake is disproportionate to its weight.

**RECAT.** The re-categorisation programme replaces the coarse three-band scheme with a finer set based on **both MTOW and wingspan** (wingspan matters because it sets the vortex separation and hence the decay rate). **RECAT-EU** uses six categories, conventionally labelled **CAT-A "Super Heavy" through CAT-F "Light"**, with a pairwise separation matrix rather than a single table. **RECAT-EU-PWS** and the ICAO **wake turbulence re-categorisation in PANS-ATM** extend this further, and some airports operate **time-based separation (TBS)** which shortens spacing in strong headwinds because the wake is blown clear faster.

> ⚠️ The exact **RECAT-EU MTOW/wingspan boundaries and the separation matrix values were not verifiable in this session** (the EUROCONTROL and SKYbrary pages were unreachable). Do not quote numeric RECAT separations from memory — obtain the current EUROCONTROL RECAT-EU document or the relevant State AIP. `needs-verification`

**Avoidance in practice.** Stay at or above the preceding aircraft's flight path; on approach, fly at or above the glidepath and land beyond its touchdown point; on departure behind a heavy, rotate before its rotation point and climb above its path; be alert on **parallel and crossing runways**, on **opposite-direction operations**, and when **descending through the level of a preceding aircraft in cruise** — en-route wake encounters at RVSM separation are a known and growing phenomenon, especially behind an A380 or 777.

## 4. Icing

### 4.1 Physics

Cloud droplets remain liquid well below 0 °C because homogeneous nucleation requires a large enough droplet or an ice nucleus. **Supercooled liquid water (SLW)** exists from 0 °C down to about **−40 °C**, and reliably below **−48 °C water always freezes, so icing is impossible below that**. Roughly **half of all reported icing occurs between −8 °C and −12 °C**.

Ice accretes when supercooled droplets strike the airframe and freeze. What happens next depends on the **liquid water content (LWC)**, the **droplet median volume diameter (MVD)**, the **temperature**, and the **collection efficiency** of the surface (small radius → high efficiency, which is why the sharp edges — probes, antennas, small radius leading edges, propeller blades — ice first and worst).

### 4.2 Ice types

| Type | Conditions | Appearance | Why it matters |
|---|---|---|---|
| **Rime** | Small droplets, low LWC, colder (typically −15 to −40 °C), stratiform cloud | Rough, milky, opaque, brittle; freezes on impact trapping air | Builds forward into the airflow, spoils the leading-edge shape, but sheds relatively well from boots |
| **Clear (glaze)** | Larger droplets, high LWC, warmer (0 to −10 °C), cumuliform cloud and freezing rain | Glossy, transparent, dense, hard | Droplets run back before freezing → forms **beyond the protected area**, creates **ridges aft of the boots**, very heavy, hard to shed, the most dangerous |
| **Mixed** | Intermediate | Rough, opaque with clear inclusions | Common in practice |
| **Hoar frost** | Deposition on a cold airframe descending into moist air, or overnight on the ground | White crystalline | Obscures vision; on the wing it destroys laminar flow out of all proportion to its thickness |

### 4.3 SLD, freezing drizzle and freezing rain

**Supercooled large droplets (SLD)** have MVD greater than the certification envelope's droplets — freezing drizzle (roughly 50–500 µm) and freezing rain (> 500 µm). They matter because:
- They have high inertia, so they **impinge much further aft** than the design envelope assumes, including on **unprotected surfaces**, upper wing surfaces, and behind de-ice boots.
- They form **ridges** that trigger flow separation ahead of the aileron, producing sudden, sometimes uncommanded roll — the mechanism in the **ATR 72 at Roselawn, Indiana (American Eagle 4184, 31 October 1994)**, the accident that drove SLD rulemaking.
- SLD ice accretes **fast** and can exceed the capability of pneumatic or thermal protection.

The classic freezing-rain structure is a **warm nose**: warm air overrunning a shallow cold layer at the surface, so snow melts aloft and refreezes on contact below. Look for it ahead of warm fronts and in warm-air-advection situations, and read the sounding for it.

### 4.4 The certification icing envelopes

- **CS-25 / 14 CFR Part 25 Appendix C** — the historical icing certification envelope, defined as **continuous maximum (stratiform)** and **intermittent maximum (cumuliform)** conditions expressed as combinations of LWC, MVD (roughly 15–50 µm) and temperature, with horizontal/vertical extent factors. Every transport aeroplane's ice protection system is sized to it.
- **CS-25 / 14 CFR Part 25 Appendix O** — the **SLD envelope**, added after Roselawn, covering freezing drizzle and freezing rain conditions outside Appendix C. Appendix O introduced the requirement for aeroplanes to be shown either capable of safe operation in, or capable of safe detection of and exit from, SLD conditions.
- **Appendix D** relates to **ice crystal (mixed-phase/glaciated) conditions** affecting engines — the environment implicated in high-altitude engine power-loss and roll-back events and in ice-crystal icing of probes at cruise.

> ⚠️ The **numeric LWC/MVD/temperature values** in Appendices C, O and D are not reproduced here; they were not retrievable in this session. Consult the current CS-25 (EASA) or 14 CFR Part 25 text. `needs-verification`

### 4.5 Ice-crystal icing

At cruise, in and near deep convection (particularly the ITCZ and tropical MCSs), the aircraft flies through high concentrations of **small ice crystals** in air that is well below freezing and shows **little or no radar reflectivity** (small ice crystals are poor reflectors). Crystals bounce off cold surfaces but **stick inside warm engine components and inside pitot probes**, where partial melting produces a slush that then refreezes.

Consequences: engine **rollback**, surge, flameout or damage; **unreliable airspeed** from blocked pitot heads. This is the meteorological mechanism behind **Air France 447's** initial upset and behind a long list of engine events that drove the Appendix D rulemaking and probe redesigns. Recognition: cruising near or downwind of deep convection with **little radar return**, high total air temperature anomalies, St Elmo's fire, a "heavy rain" sound at altitude. Mitigation: avoid the anvil and the region within 20 nm of and downwind of deep convection; follow the OEM ice-crystal-icing procedures (engine anti-ice, thrust changes, avoiding prolonged idle descent near convection).

### 4.6 Airframe and engine effects

- **Lift loss and drag rise** — a small leading-edge accretion can cost 30 % of maximum lift and add 40 % drag; a very thin, rough layer (frost) is enough.
- **Stall speed rises and the stall becomes abrupt**, often without the usual warning because the AoA vane is itself iced or because the wing stalls at a lower AoA than the vane is set for.
- **Tailplane icing** — the horizontal stabiliser has a smaller leading-edge radius and collects ice faster than the wing; flap extension increases download and negative tail AoA and can cause **tailplane stall**, which produces an uncommanded nose-down pitch that is *worsened* by pulling and by more flap. Recovery differs from wing stall: retract flap, reduce power, pull. Know which one your type is susceptible to.
- **Control surface jamming** and hinge-moment reversal (aileron snatch).
- **Probes and static ports** — the primary reason for pitot heat.
- **Antennas and radome** — radar degradation.
- **Engine**: inlet lip and spinner ice shedding into the core (FOD), inlet distortion, fan blade ice, compressor stall, and the ice-crystal path above.
- **Weight** — usually a minor factor compared with the aerodynamic penalty, but not on a small aeroplane.

### 4.7 Ground de-icing and anti-icing

**The clean aircraft concept**: no frost, ice or snow adhering to critical surfaces at takeoff. This is an absolute requirement, not a judgement call, and includes upper wing surfaces, control surfaces, engine inlets, probes and, for many types, the fuselage.

**Fluids (SAE AMS specifications; ISO equivalents):**

| Type | Character | Colour | Purpose |
|---|---|---|---|
| **Type I** | Low viscosity, unthickened, applied hot | Usually orange/pink | **De-icing** — removes contamination. Short holdover |
| **Type II** | Pseudoplastic (thickened) | Usually straw/white | **Anti-icing** — stays on the wing and shears off at rotation. Longer holdover. Minimum rotation speed applies |
| **Type III** | Thickened but designed to shear off at lower rotation speeds | Usually bright yellow-green | For **slower** aircraft (commuter/turboprop) |
| **Type IV** | Most heavily thickened | **Green** | **Longest holdover** anti-icing; the workhorse for jets |

Thickened fluids are **non-Newtonian**: viscous at rest, thinning under shear so they flow off during the takeoff roll. Hence the minimum rotation speed constraints, the requirement for clean application, and the concern about **dried fluid residue** rehydrating in the flap/slat cavities on later flights.

**Holdover time (HOT)**: the estimated time that the applied fluid will prevent frost/ice forming and snow accumulating. Tables are published annually — the **FAA "2025-26 Holdover Tables"** are the current US set — and are indexed by **fluid type and concentration, outside air temperature band, and precipitation type and intensity** (freezing fog, snow, freezing drizzle, light freezing rain, rain on a cold-soaked wing). They give a **range** (e.g. 25–50 minutes), and the lower end applies in heavier precipitation.

> ⚠️ HOT is a **planning guideline, not a clearance**. The determining factor is always the **pre-takeoff contamination check**. Conditions outside the tables (moderate/heavy freezing rain, hail, ice pellets beyond the specified allowance) are outside the certification of the fluid and generally require re-treatment or a return to stand. **Rain on a cold-soaked wing** is specifically dangerous because the wing skin is below zero from cold fuel while the OAT is above zero.

## 5. Volcanic ash

### 5.1 Why it kills engines

Volcanic ash is pulverised rock and glass with a melting point around **1100 °C**, well below turbine gas temperatures. In an engine it:
1. **Abrades** compressor blades, inlet, windshields and lights.
2. **Melts in the combustor to molten glass**.
3. **Resolidifies on the turbine nozzle guide vanes**, blocking the flow area, driving the engine toward surge and **flameout**.
4. Blocks cooling holes and pitot/static systems; the electrostatically charged cloud produces St Elmo's fire.

**Ash is invisible to weather radar** at aviation wavelengths because it is dry and the particles are small — this is exactly why BA9 flew into it in 1982 (`09`). At night the cues are St Elmo's fire, a sulphurous or "electrical" smell, cabin haze, engine surging, glowing engine inlets, and bright plumes off the leading edges.

**Immediate actions** (generic — fly the type-specific QRH): **autothrottle off, thrust to idle, turn 180°, descend if terrain permits, engine and wing anti-ice on, APU start if available, oxygen masks on, ignition on, expect and attempt restarts** — engines that have flamed out have restarted repeatedly once clear and cooler (BA9 and KLM 867 both did).

### 5.2 The institutional response — IAVW and the VAACs

ICAO's **International Airways Volcano Watch (IAVW)** coordinates volcano observatories, State volcano observatory notices (**VONA**), meteorological watch offices (which issue **volcanic ash SIGMETs**), and **nine Volcanic Ash Advisory Centres (VAACs)**, each responsible for a defined region and each hosted inside a national meteorological service. A **VAA (Volcanic Ash Advisory)** carries: volcano name, position and elevation; the information source (satellite, pilot report, observatory); eruption details with UTC time; the observed ash cloud's vertical extent in flight levels and its horizontal extent; movement; and **forecast position and evolution at +6, +12 and +18 hours**, issued as both text and a **VAG (graphic)**.

> ⚠️ The **names and areas of responsibility of the nine VAACs** were not retrievable in this session (the Wikipedia table did not render). London, Toulouse, Washington, Anchorage, Montreal, Darwin, Wellington, Tokyo and Buenos Aires are the commonly cited set, but **verify against ICAO Doc 9691 / the IAVW Handbook** before relying on the list. `needs-verification`

### 5.3 Eyjafjallajökull 2010 and the concentration thresholds

The eruption began **14 April 2010**. European airspace was largely closed **15–23 April**, with further intermittent closures into mid-May.

- **Over 95 000 flights cancelled** in the six-day ban; later estimates put it at **107 000 over eight days**, about **48 % of global air traffic**, affecting roughly **10 million passengers**.
- **IATA estimated €148 million per day** in airline losses, with total industry losses around **€1.3 billion**; UK airports lost about **£80 million over 6.5 days**.
- The initial regulatory position was **zero tolerance** — any forecast ash meant closure. On **21 April 2010** the UK CAA introduced safety thresholds of **200–2000 µg/m³**, and on **18 May 2010** raised the enhanced-procedures ceiling to **4 mg/m³**.
- **London VAAC** provided the ash forecasts that drove the closures.
- **What changed**: engine manufacturers were required to define **ash ingestion limits** for their products; the zone framework (no-fly / enhanced-procedures / low-contamination, and the **Time Limited Zone** concept) replaced blanket closure; European ATM coordination through the Single European Sky/Network Manager accelerated; and airlines developed volcanic-ash contingency plans and safety risk assessments. Airborne detection research (e.g. infrared ash imaging) followed.

## 6. Sand and dust storms

Directly relevant to a Doha base. Three generating mechanisms, with different forecastability:

1. **Synoptic (shamal) dust** — a strong pressure gradient behind a cold front lifts dust over a wide area for days. Reasonably well forecast by global models because the driving wind field is synoptic scale. Visibility 1000–5000 m in blowing dust (**BLDU**), lower in the core, and dust suspended to 5000–10 000 ft. In the METAR it appears as **DU/BLDU/DS** with a corresponding drop in visibility.
2. **Convective (haboob)** — thunderstorm cold-pool outflow as a density current. **Up to 2000 m (7000 ft) deep, dust wall to 100 km wide, advancing at up to 70 km/h (38 kt), lasting up to 6 hours.** Arrives with almost no warning; visibility can go from 10 km to under 200 m in minutes, with a 30–50 kt wind shift and severe low-level turbulence. **Very poorly forecast** by global models because the parent convection is sub-grid; convection-permitting regional models and nowcasting/radar are the only real tools.
3. **Local/thermal** — dust devils and shallow blowing dust from surface heating; a nuisance rather than a hazard, but a marker of a superadiabatic surface layer.

**Effects on the aircraft.** Erosion of compressor blades, leading edges, windshields, paint and rotor blades; blockage of filters and cooling passages; ingestion of fine silicate at high engine temperature can produce the same glassification mechanism as volcanic ash on a slower timescale; contamination of oil and hydraulic systems; static discharge and communication interference; pitot/static contamination; and reduced visibility with slant-visual-range effects worse than the reported horizontal visibility on approach.

**Operational management.** Watch the TAF trend groups and the SIGMET (dust storms are a listed SIGMET phenomenon — **SS** / **DS**); watch satellite dust RGB products, which separate dust from cloud well; expect visibility to be reported worse than it looks from above because dust is optically thicker along a slant path; expect ILS as the only usable approach; carry extra fuel in shamal season; and treat a convective outflow boundary on radar approaching the field the same way you would a squall line.

## 7. Fog and low visibility

### 7.1 Types

| Type | Mechanism | Season/setting | Dispersal |
|---|---|---|---|
| **Radiation** | Nocturnal longwave cooling of the ground cools the air to its dewpoint. Needs **clear sky, light wind (2–7 kt), moist air, long night** | Autumn/winter, inland, valleys, and Gulf coastal plains in winter | Insolation after sunrise, or wind increase; can persist all day under a strong winter inversion |
| **Advection** | Warm moist air moves over a colder surface | Sea fog (Grand Banks, Namibian coast, California, Arabian Gulf in spring), snow-covered ground; **persists in wind up to ~20 kt** | Change of air mass or trajectory; does **not** clear with heating over the sea |
| **Frontal / precipitation** | Rain from warm air aloft evaporates into cold surface air, raising its dewpoint to saturation | Ahead of warm fronts and along occlusions | Frontal passage |
| **Steam (evaporation/arctic sea smoke)** | Very cold air over much warmer water | High latitudes, lakes in autumn, and over warm Gulf water after a strong cold outbreak | Air mass modification |
| **Upslope** | Air forced up a slope cools adiabatically to saturation | Windward slopes, US High Plains | Wind change |
| **Freezing fog (FZFG)** | Fog droplets supercooled; deposit rime on surfaces | Cold continental interiors under an inversion | — |
| **Ice fog** | Droplets frozen to crystals; needs **≈ −35 °C or below** | Arctic/Antarctic, Siberia, interior Alaska | — |
| **Valley fog** | Radiation fog concentrated by cold-air drainage | Alpine valleys, and any basin | Slow |

**Definitions**: fog is visibility **below 1000 m**; **mist (BR)** is 1000–5000 m with high humidity; **haze (HZ)** is dry-particle obscuration. Fog typically forms once the temperature–dewpoint spread is **below 2.5 °C**.

Forecasting cues: dewpoint trend through the evening, wind forecast (too calm → dew instead of fog; too windy → stratus instead of fog), cloud cover (any mid or high cloud kills radiation fog), soil moisture after rain, and the previous night's behaviour. Fog is the single hardest thing a TAF forecaster does, which is why **PROB30/PROB40 TEMPO 0300/0700 0300 FG** is such a common — and such an expensive — line in a TAF.

### 7.2 RVR and the low-visibility framework

**RVR (runway visual range)** is the range over which a pilot on the runway centreline can see the runway surface markings, the runway edge lights or the centreline lights. It is measured by **transmissometers or forward-scatter meters** at touchdown, midpoint and stop-end, and it is *not* the same as the meteorological visibility — RVR accounts for light intensity and background luminance, so at night with high-intensity lights the RVR can greatly exceed the reported visibility.

- Reported in metres (feet in the US), in steps (typically 25 m below 400 m, 50 m to 800 m, 100 m above).
- Reported in the METAR when visibility or RVR falls below the reporting threshold, with a trend letter **U/D/N** and **P** (above the maximum measurable) or **M** (below the minimum).
- **Touchdown RVR is controlling** for the approach; mid and stop-end become relevant at lower minima.

**LVP (Low Visibility Procedures)** are aerodrome procedures activated when visibility/ceiling falls below a defined threshold, typically **RVR below 550 m or ceiling below 200 ft**. Under LVP: ILS sensitive/critical areas are protected (so that no vehicle or aircraft distorts the localiser or glideslope beam), surface movement is restricted and separation increased, standby power requirements apply to lighting, and the aerodrome capacity drops sharply. LVP status must be established before CAT II/III approaches are flown. Details of minima, aircraft and crew requirements are in `06`.

## 8. Space weather

Since **November 2019**, ICAO has required space weather advisories, provided by four designated global centres: **NOAA (US)**, the **ACFJ consortium (Australia, Canada, France, Japan)**, **PECASUS (pan-European)** and the **China–Russian Federation consortium**.

### 8.1 The three NOAA scales

| Scale | Physical measure | Aviation-relevant effects |
|---|---|---|
| **R1–R5 Radio Blackout** (X-ray flare class M1 → X20) | R1 = M1 (10⁻⁵ W/m²) up to R5 = X20 (2×10⁻³) | R1: low-frequency navigation signals degraded briefly. R2: LF nav degraded for tens of minutes. R3: HF blackout ~1 hour on the sunlit side. R4: 1–2 h HF blackout plus navigation disruption. R5: **complete HF blackout on the entire sunlit side for hours** |
| **S1–S5 Solar Radiation Storm** (>10 MeV proton flux, 10 → 10⁵ pfu) | S1: minor HF impacts in polar regions. S2: possible radiation risk to high-altitude crews at polar latitudes. S3–S5: increasing radiation hazard; **HF blackout through the polar regions**; at S4/S5 unavoidable high radiation exposure |
| **G1–G5 Geomagnetic Storm** (Kp 5 → 9) | G1: aurora at high latitude, minor satellite effects. G2: HF fading at higher latitudes. G3: **HF radio intermittent**. G4: **HF propagation sporadic**. G5: **HF propagation may be impossible in many areas** |

### 8.2 What it does to the aircraft

- **HF communication** — the primary casualty. Ionospheric irregularities scatter rather than reflect HF; polar routes lose HF first and most completely. This matters because HF is the required communication medium on many oceanic and remote routes, and loss of the required communication capability means the route is no longer legal (SATCOM/CPDLC mitigates but does not eliminate the requirement).
- **GNSS** — ionospheric scintillation and large horizontal gradients degrade or deny GPS/GNSS. **SBAS (WAAS/EGNOS) is disabled by every major space weather event**, with outages from minutes to days, so LPV approaches can be unavailable.
- **Radiation dose** — cosmic ray secondaries increase with altitude and latitude. During an S-scale solar radiation storm, dose rates at cruise on polar routes can rise enough that operators descend or reroute equatorward. Crew are classified as occupationally exposed in the EU with dose monitoring obligations.
- **Avionics single-event effects** — neutron-induced upsets in memory and processors; designed against, but the reason for the redundancy.
- **Rerouting cost**: rerouting a polar flight is quoted at roughly **US$100 000**, which is why the advisory service exists.

Products: the ICAO **space weather advisory** (issued in the same style as a volcanic ash advisory, with HF COM, GNSS and RADIATION hazard areas at defined thresholds MOD or SEV), plus NOAA SWPC and the regional providers' own alerts.

### 8.3 GNSS jamming and spoofing — the man-made analogue

Since 2022 there has been a very large increase in deliberate GNSS interference around conflict zones — the eastern Mediterranean, the Black Sea and Baltic regions, the Caucasus, the Persian Gulf and the Middle East corridors, and northern Iraq/Iran. This is not space weather but it presents identically in the flight deck.

- **Jamming** denies the signal: GPS PRIMARY LOST, degraded RNP capability, loss of GNSS-based approaches, and reversion to DME/DME or IRS-only navigation with a growing position error.
- **Spoofing** feeds a false position: this is the dangerous one, because the aircraft accepts a plausible but wrong position, which can corrupt the IRS position, generate false EGPWS terrain alerts and false time, and in reported cases has led to complete loss of navigation capability requiring ATC vectors.
- Mitigations that operators have adopted: crew awareness bulletins for affected FIRs, cross-checking with conventional navaids, not accepting GNSS-derived time, procedures for IRS realignment on the ground, and in some cases avoiding the affected airspace.

> ⚠️ The **GNSS jamming section could not be verified from a fetched source in this session** (the relevant page was unavailable). The regions and effects described are consistent with published EASA Safety Information Bulletins and IATA guidance from 2022 onward, but **verify the current EASA SIB and the affected-FIR list before operational use**. `needs-verification`

## Sources

- [Downburst / microburst](https://en.wikipedia.org/wiki/Microburst) — Wikipedia (size definition, wet/dry, record wind, vertical velocity, encounter profile)
- [Supercell](https://en.wikipedia.org/wiki/Supercell) — Wikipedia (mesocyclone, hook echo, BWER, overshooting top, LP/classic/HP, 30 % tornado figure)
- [Terminal Doppler Weather Radar](https://en.wikipedia.org/wiki/Terminal_Doppler_Weather_Radar) — Wikipedia (frequency, beamwidth, power, resolution, 45 units)
- [Clear-air turbulence](https://en.wikipedia.org/wiki/Clear-air_turbulence) — Wikipedia (150 nm / 64 % figure, climate projection)
- [Lee wave](https://en.wikipedia.org/wiki/Lee_wave) — Wikipedia (formation criteria, rotor, lenticulars, incidents)
- [Wake turbulence](https://en.wikipedia.org/wiki/Wake_turbulence) — Wikipedia (sink rates, lateral drift, ICAO MTOW basis, B757 exception)
- [Atmospheric icing](https://en.wikipedia.org/wiki/Atmospheric_icing) — Wikipedia (rime/clear/mixed, −8 to −12 °C peak, −48 °C limit)
- [Volcanic Ash Advisory Center](https://en.wikipedia.org/wiki/Volcanic_Ash_Advisory_Center) — Wikipedia (nine VAACs, VAA content, IAVW)
- [Volcanic ash](https://en.wikipedia.org/wiki/Volcanic_ash) — Wikipedia (engine damage mechanism)
- [Air travel disruption after the 2010 Eyjafjallajökull eruption](https://en.wikipedia.org/wiki/Air_travel_disruption_after_the_2010_Eyjafjallaj%C3%B6kull_eruption) — Wikipedia (dates, cancellations, cost, thresholds)
- [Haboob](https://en.wikipedia.org/wiki/Haboob) — Wikipedia (dimensions, speed, duration)
- [Fog](https://en.wikipedia.org/wiki/Fog) — Wikipedia (types, 1000 m definition, 2.5 °C spread, ice fog −35 °C)
- [NOAA Space Weather Scales](https://www.swpc.noaa.gov/noaa-scales-explanation) — NOAA SWPC (R/S/G scales and effects)
- [Space weather](https://en.wikipedia.org/wiki/Space_weather) — Wikipedia (HF, GNSS, SBAS, polar reroute cost, ICAO providers)
- [FAA Aircraft Ground Deicing / Holdover Tables](https://www.faa.gov/other_visit/aviation_industry/airline_operators/airline_safety/deicing) — FAA (2025-26 tables)

## Open questions

- **RECAT-EU category boundaries and separation matrix** — not verified; EUROCONTROL and SKYbrary unreachable. `needs-verification`
- **CS-25/FAR-25 Appendix C, O and D numeric envelopes** — not retrieved; consult the regulation text. `needs-verification`
- **EDR ↔ subjective turbulence intensity mapping** — indicative only; verify against ICAO Annex 3 Appendix 3 and operator policy. `needs-verification`
- **The nine VAACs by name and area of responsibility** — the commonly cited list is given but was not confirmed from a fetched table. `needs-verification`
- **GNSS jamming/spoofing regions and mitigations** — not verified from a fetched source this session. `needs-verification`
- **ICAO windshear severity thresholds (kt/100 ft)** are the widely used figures but were not verified from an ICAO document here.
- **Holdover time table values** — only the existence and title of the FAA 2025-26 tables was confirmed; no numeric HOT values are reproduced.
