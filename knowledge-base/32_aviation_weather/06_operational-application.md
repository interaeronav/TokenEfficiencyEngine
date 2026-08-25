---
id: aviation_weather.operations
title: Operational application — briefing, fuel, performance, LVO, contaminated runways, diversion
domain: 32_aviation_weather
tags: [flight-planning, alternate, planning-minima, fuel-policy, contingency-fuel, density-altitude, doha, takeoff-performance, weather-deviation, sloppy, lvo, cat-ii, cat-iii, rcam, rwycc, grf, crosswind, contaminated-runway, diversion]
jurisdiction: global
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Instrument landing system", url: "https://en.wikipedia.org/wiki/Instrument_landing_system", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Southwest Airlines Flight 1248", url: "https://en.wikipedia.org/wiki/Southwest_Airlines_Flight_1248", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Emirates Flight 521", url: "https://en.wikipedia.org/wiki/Emirates_Flight_521", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Doha — climate", url: "https://en.wikipedia.org/wiki/Doha", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Hamad International Airport", url: "https://en.wikipedia.org/wiki/Hamad_International_Airport", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Density altitude", url: "https://en.wikipedia.org/wiki/Density_altitude", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "North Atlantic Tracks", url: "https://en.wikipedia.org/wiki/North_Atlantic_Tracks", publisher: "Wikipedia", accessed: 2026-08-25}
related: [aviation_weather.hazards, aviation_weather.products, aviation_weather.climatology, aviation_industry.operations]
unit_system: mixed
---

# Operational application — briefing, fuel, performance, LVO, contaminated runways, diversion

**Summary.** Weather becomes operational the moment it changes a number: a fuel figure, a takeoff weight, an alternate, a runway, a decision altitude, a go/no-go. This file walks the decision chain in the order a crew meets it, from the briefing package to the diversion, with the Doha summer takeoff worked through in full and the Global Reporting Format explained properly.

> ⚠️ Every regulatory figure in this file is indicative. **Your operator's OM-A/OM-B, the State AIP, and the applicable regulation (EU 965/2012 Part-CAT, 14 CFR 121, QCAR-OPS or equivalent) govern.** Where this file and a company procedure conflict, the company procedure wins. Several thresholds below are flagged `needs-verification`.

## Key facts

| Item | Typical value |
|---|---|
| ILS **CAT I** | DH **200 ft**, RVR 550 m (or 800 m without certain lighting) |
| ILS **CAT II** | DH **100 ft**, RVR **300–350 m** |
| ILS **CAT IIIA** | DH **< 100 ft** (typically 50 ft), RVR **175–200 m** |
| ILS **CAT IIIB** | DH **< 50 ft or no DH**, RVR **75–175 m** |
| ILS **CAT IIIC** | **no DH, no RVR limitation** — not operationally authorised anywhere without full surface-guidance provision |
| LVP activation | typically RVR **< 550 m** or ceiling **< 200 ft** |
| Contingency fuel (standard) | **5 % of trip fuel** (reducible to 3 % with an en-route alternate, or to a statistical figure under an approved scheme) |
| Final reserve | **30 minutes** holding at 1500 ft above the alternate at estimated landing mass (jet) |
| Alternate fuel | to the most distant required alternate, including missed approach, climb, cruise, descent and approach |
| RWYCC scale | **6 (dry) down to 0 (worse than poor)** |
| Strategic lateral offset | **0, 1 or 2 nm right of centreline** |
| Weather deviation offset (oceanic) | Turn away, offset, and if the deviation is ≥ **10 nm**, climb or descend **300 ft** (direction depending on track and turn) |
| Doha July mean maximum | **42.4 °C**; record **50.4 °C** |
| OTHH runways | **4850 m × 60 m** and **4250 m × 60 m** |

## 1. The pre-flight weather package

A long-haul OFP arrives with a standard set. Read it in this order, because it builds a picture rather than a list:

1. **Significant weather chart(s)** for the cruise levels — where is the convection, where is the CAT, where are the jets, where is the tropopause. This is the strategic picture: it tells you whether the flight plan route is the sensible one.
2. **Wind/temperature charts or the computed wind on the OFP** — check the flight plan's assumed winds against the chart. If the OFP wind looks optimistic against the chart, ask why.
3. **Route METAR/TAF set** — destination, alternates, en-route alternates, ETOPS alternates, departure alternate. Read the TAFs against your ETA window with the *validity period* checked; a TAF that expires before your ETA is not a forecast for your arrival.
4. **SIGMETs and AIRMETs** along the route, and the **volcanic ash advisories** if any volcano on or near the route is active.
5. **Tropical cyclone advisories** if the season and basin apply.
6. **Space weather advisory** for polar or high-latitude routes.
7. **NOTAMs interacting with weather**: navaid outages that remove your low-visibility capability, runway closures, unserviceable approach lighting (which raises your minima), de-icing facility status, and **GNSS interference NOTAMs**.
8. **The aerodrome charts' minima pages** for every planned and alternate aerodrome, checked against the forecast.

**The one question to answer**: *for each of departure, destination and each alternate, what is the worst credible weather in my window, and what does it cost me?*

## 2. Alternate selection and planning minima

### 2.1 Which alternates are required

- **Take-off alternate** — required when the weather at the departure aerodrome is below the applicable landing minima, or when it is impossible to return for other reasons. Distance limit typically **1 hour single-engine cruise** (two-engine aeroplanes) or **2 hours** (three/four-engine) in still air, and the take-off alternate weather must be **at or above the applicable landing minima at the estimated time of use**.
- **Destination alternate(s)** — normally one; **two** are required when the destination forecast is marginal (visibility/ceiling below defined values in the validity window) or when no forecast is available. **No alternate** may be planned in narrowly defined circumstances (flight time below a limit, two separate usable runways, and a forecast comfortably above minima for a window either side of ETA) — this is the "island holding" / isolated-aerodrome rule and it varies by regulator.
- **En-route alternates** and **ETOPS alternates** — required within the ETOPS threshold/rule time, each with its own weather criteria applied at the **earliest and latest possible time of use** (which for a long ETOPS segment can be a wide window).
- **Fuel ERA (en-route alternate)** — used to justify reduced contingency fuel under some fuel schemes.

### 2.2 Planning minima (the classic tables)

The principle: **an alternate must be forecast to be usable when you get there, with a margin, because you will arrive with only final reserve to spare.** Hence the alternate planning minima are *higher* than the actual approach minima. The traditional EU-OPS/Part-CAT structure:

| Approach facility available at the alternate | Planning ceiling | Planning RVR/visibility |
|---|---|---|
| **CAT II/III capability** | CAT I DH | CAT I RVR |
| **CAT I ILS/precision approach** | **Non-precision DH/MDH + 200 ft** | **Non-precision RVR + 1000 m** |
| **Non-precision approach** | **MDH + 200 ft** | **RVR + 1000 m** (minimum 1500 m) |
| **Circling** | Circling MDH | Circling visibility |

> ⚠️ These are the **historical EU-OPS 1.297 / Part-CAT.OP.MPA.185-style** values. Part-CAT and the EASA "performance-based" approach classification have been revised; check the current regulation and, more to the point, your OM-A table. `needs-verification`

Additional principles that matter more than the table:
- **`TEMPO` and `PROB` groups.** Whether a `TEMPO` deterioration must be applied to the alternate assessment, and whether `PROB30/40` may be disregarded, is set by the regulator and the operator. Historically, `PROB30` could be disregarded for planning and `TEMPO` had to be considered with certain relaxations. Know your rule.
- **Do not pick an alternate that shares the destination's weather.** A destination and an alternate 40 nm apart in the same fog basin, or on the same side of the same front, are one aerodrome for planning purposes. In the Gulf in winter fog season, OTHH/OTBD/OMDB/OMAA/OBBI can all go below minima on the same night — a genuine and recurring problem. A weather-independent alternate may mean a much longer diversion (Muscat, Kuwait, Riyadh, Bahrain, Salalah) and therefore materially more fuel.
- **Check the alternate's actual capability**: LVP availability, CAT II/III status, runway length for your weight, fire category, curfew, customs, handling, and whether it will be open at 0300 local.

## 3. Fuel policy and how weather drives it

The standard components, in the order they are added:

| Component | Purpose | Weather sensitivity |
|---|---|---|
| **Taxi fuel** | APU + taxi | De-icing queues, LVP taxi routing, long taxi in congestion |
| **Trip fuel** | Departure to destination via the planned route/levels | Winds, temperature deviation, cost of a weather-avoidance routing, non-optimum levels because of turbulence or convection |
| **Contingency fuel** | Unforeseen: winds worse than forecast, ATC routings, levels | **The core weather buffer.** Standard **5 % of trip fuel**; reducible to **3 %** with a fuel ERA; statistical contingency (e.g. 99th-percentile of historical burn on that city pair) under an approved scheme |
| **Alternate fuel** | Missed approach at destination, climb, cruise, descent, approach and landing at the alternate | Distance to a *weather-independent* alternate, not the nearest one |
| **Final reserve** | **30 min holding at 1500 ft** above the alternate at estimated landing mass (turbine) | Not weather-driven, but it is the floor you must not touch |
| **Additional fuel** | To satisfy a specific requirement (e.g. ETOPS critical fuel scenario, isolated aerodrome holding requirement) | Icing on the critical fuel scenario, depressurised drift-down |
| **Extra fuel** | **Commander's discretion** | This is where your weather judgement is expressed in kilograms |

**How to reason about extra fuel from the weather package:**
- **Convection at destination** → holding is likely, and holding at low level burns much more than at cruise. Add holding fuel for the expected delay, not a nominal round number.
- **A `TEMPO` or `PROB40` below minima in the arrival window** → either an approach attempt plus a diversion, or holding for the condition to lift. Decide which you intend and fuel for it.
- **Fog forecast at destination and both alternates in the same air mass** → fuel to a genuinely different air mass.
- **Strong forecast headwind with a large ensemble spread** → the deterministic wind may be optimistic; contingency at 5 % of a long trip fuel is a lot, but on a 14-hour sector a 20 kt wind error is far more.
- **Convective deviations en route** → deviations cost track miles *and* non-optimum levels. A 200 nm deviation across the ITCZ is common on Africa/South America routes.
- **A destination requiring a long taxi in LVP** → taxi fuel.
- **Runway contamination at destination** → possible landing on a shorter runway, or a different runway with a tailwind, or a diversion.

**Do not over-fuel reflexively.** Carrying fuel costs fuel (typically 3–4 % of the extra mass per hour on a widebody), reduces payload if you are weight-limited, and raises landing weight. The professional standard is *justified* extra fuel with a stated reason.

**In-flight fuel monitoring** is a continuous re-decision. The two thresholds:
- **MINIMUM DIVERSION FUEL** — the fuel needed to divert now, plus final reserve. Below this, you have chosen the destination.
- **"MINIMUM FUEL"** (a declaration to ATC) — you are committed to a specific aerodrome and can accept no undue delay.
- **"MAYDAY MAYDAY MAYDAY FUEL"** — the calculated usable fuel on landing at the nearest suitable aerodrome will be **less than final reserve**. This is an emergency and must be declared. Do not soften it.

## 4. Take-off performance in heat and high density altitude — a Doha case

### 4.1 The environment

OTHH is essentially at sea level with two runways, **4850 m × 60 m** and **4250 m × 60 m** — so runway length is rarely the binding constraint. The binding constraints in July are **thrust, climb gradient and tyre/brake limits**.

Doha's climate normals (1992–2021): **July mean daily maximum 42.4 °C, record 50.4 °C; June 42.2 °C / 49.1 °C; August 41.4 °C / 48.6 °C.** With the Gulf's sea surface above 33 °C in late summer, coastal dewpoints of 25–30 °C accompany them.

### 4.2 Working the numbers

Take **OAT 47 °C, QNH 1002 hPa, field elevation ~15 ft** (a routine mid-afternoon July departure):

- **Pressure altitude** = 15 + (1013 − 1002) × 27 ≈ 15 + 297 ≈ **310 ft**
- **ISA temperature at 310 ft** = 15 − 0.6 ≈ **14.4 °C**
- **ISA deviation** = 47 − 14.4 = **+32.6 °C → ISA+33**
- **Density altitude** ≈ 310 + 120 × 32.6 ≈ **4 200 ft**
- Density ratio σ ≈ 0.878; **TAS/IAS ratio** ≈ 1/√σ ≈ **1.067**

### 4.3 What each of those does

**1. Thrust.** A modern high-bypass turbofan is flat-rated to a corner temperature (commonly around ISA+15). Above it, thrust falls roughly with the density and with the temperature ratio, so at ISA+33 you may be **8–15 % down on the flat-rated take-off thrust**, depending on the engine's rating structure. Reduced/assumed-temperature (flex) thrust is often **unavailable at all** on a hot day at high weight, because the assumed temperature would have to exceed the maximum flex temperature — so you go at full rated thrust with no engine-life saving, which is itself a cost.

**2. Ground speeds.** V1, VR and V2 are indicated speeds. At 6.7 % higher TAS for the same IAS, the ground speeds at rotation and at V1 are 6.7 % higher, and:
- **Take-off distance** scales roughly with the square of the true speed: ~**14 % more distance** for the same speed schedule, before adding the thrust loss.
- **Accelerate-stop distance** grows for the same reason, and the **energy the brakes must absorb scales with the square of the ground speed** — so brake energy limits and the **maximum tyre speed** (typically 195–225 kt ground speed) become live constraints. On a very hot, high-weight departure it is entirely possible to be **tyre-speed limited**.

**3. Climb gradient.** Available thrust is down and required thrust (drag) is unchanged, so the net second-segment gradient shrinks. The **required net gradients** (2.4 % for a twin, 2.7 % three-engine, 3.0 % four-engine in the second segment, with the corresponding net-flight-path obstacle clearance requirement) frequently become the limiting weight at OTHH in summer, not the field length. And the same environment reduces your **engine-out drift-down ceiling** — relevant for departures toward the Zagros/Elburz or the Hajar.

**4. Bleed configuration.** Packs-off take-off (with the associated procedures and cabin considerations) recovers meaningful thrust and is a common hot-day technique. Engine anti-ice is irrelevant here; APU bleed for pack supply is the usual arrangement.

**5. Wind.** The July flow at OTHH is a northwesterly shamal, so runway selection is usually favourable, but a light and variable afternoon wind with a sea-breeze component can put a tailwind on the preferred runway. **A tailwind component is heavily penalised**: performance data uses **150 % of the reported tailwind and 50 % of the reported headwind** as a safety factor. A 5 kt tailwind at high weight in 47 °C can cost several tonnes.

**6. Turbulence and thermals.** The superadiabatic surface layer over a desert in the afternoon gives low-level thermal turbulence and localised windshear on the initial climb. It is uncomfortable, not usually hazardous, but it is a reason to expect airspeed excursions and to be disciplined about not chasing them.

### 4.4 The decisions that follow

- **Schedule** — the reason so many Gulf long-haul departures leave before dawn or late at night is exactly this arithmetic.
- **Payload** — if the performance-limited weight is below the commercial weight, you offload cargo, then bags, then passengers. Knowing the limiting weight two hours before departure is worth more than knowing it at the gate.
- **Runway** — the longer runway, into wind, with the least penalising obstacle set.
- **Derate strategy** — a fixed derate (a lower rating) plus assumed temperature is often not available; full thrust with no flex is the hot-day norm.
- **The reverse case** — arriving at OTHH at 47 °C, landing distance is also affected (higher ground speed for the same IAS, ~14 % more distance, more brake energy, longer turnaround for brake cooling). **Emirates 521 (3 August 2016, Dubai, OAT 48 °C, windshear reported)** is the case study for what happens when a hot-day long landing turns into an attempted go-around (`09`).

## 5. En-route decision-making and weather deviation

### 5.1 The tools in cruise

Datalink METAR/TAF/SIGMET, EFB weather with satellite/radar/lightning overlay where connectivity allows, the aircraft radar, ride reports from ATC and from other aircraft on frequency, and your eyes. In the tropics at night, **the radar plus lightning is the whole picture**, and the radar must be worked (see the tilt technique in `04`).

### 5.2 Convective deviation technique

1. **Start early.** A 20 nm deviation decided 150 nm out costs almost nothing. The same deviation decided at 30 nm costs a hard turn, a possible altitude change, and passenger injuries.
2. **Ask for the deviation with a distance and a side**: "request 30 right of track for weather, expect 60 miles."
3. **Deviate upwind of the cell** where possible (away from the anvil and the hail); if the storm is moving, deviate behind it, not in front of it.
4. **Do not descend to go under.** The area under a cell contains the downburst, the hail and the heaviest turbulence, and it removes your terrain and performance margins.
5. **Do not climb to go over** unless you can genuinely clear the top by 5000 ft, which in the tropics you usually cannot.
6. **Reassess every few minutes.** Cells grow. A gap that exists now may not exist when you get there.
7. **Manage the cabin**: seat belt sign early, crew seated, service secured. Most convective injuries are to unrestrained cabin crew.

### 5.3 Oceanic and remote-area weather deviation

In procedural (non-radar) oceanic airspace — the NAT OTS, PACOTS, the Bay of Bengal, the Indian Ocean, the South Atlantic — the deviation procedure is standardised because ATC cannot see you:

- **Request the deviation from ATC** and, if a clearance cannot be obtained in time, **advise ATC and deviate**, using the **weather deviation procedure**: broadcast intentions on **121.5** and the air-to-air frequency **123.45**, turn away from track, and **if the deviation is 10 nm or more from centreline, establish a vertical offset of 300 ft** (the direction depends on whether the track is easterly or westerly and on which way you turn — read the current ICAO Doc 4444 / regional supplementary procedures wording; the intent is to place you between the RVSM levels used by aircraft on track).
- Return to track and level as soon as practicable and advise ATC.
- **SLOP (Strategic Lateral Offset Procedure)** is separate and routine: fly **0, 1 or 2 nm right of centreline** to mitigate the risk of a collision from an altitude error or a coincident navigation error. Many operators default to 1 or 2 nm right. It also gives a small wake-turbulence benefit behind a preceding aircraft on the same track.
- **Position reporting, HF/SATCOM/CPDLC discipline**, and the **contingency procedures** for a drift-down or a turn-back all interact with weather because the alternate you can reach depends on the wind.
- Space-based **ADS-B** (activated over the North Atlantic at the end of March 2019) has reduced NAT separations substantially (longitudinal from 40 to 14–17 nm, lateral to 15 nm by November 2020) and has made tactical deviation clearances easier to obtain than they were.

### 5.4 CAT management

Ride reports first, then the SIGWX/EDR forecast. In turbulence: **turbulence penetration speed**, autothrottle considerations per type, autopilot normally **left in** (it flies more smoothly than a startled human), seat belts, and a level or track change. CAT layers are usually 1000–3000 ft deep, so **2000–4000 ft of altitude change is more effective than 50 nm of lateral change** — but on the NAT you cannot simply change level, so request it early and be prepared to fly a level you did not plan.

## 6. Arrival planning and holding

- **Get the destination picture early** — one hour out is too late on a convective day. Two to three hours out, pull the METAR/TAF/ATIS by datalink and start the arithmetic.
- **Decide the commit point.** Establish, before descent, the fuel state at which you will divert, and the aerodrome you will divert to. Write it down. The single most common failure mode in weather diversions is deciding late, having already burned the diversion fuel in the hold.
- **Holding burns**: at low level a widebody burns far more than at cruise. If a delay is expected, hold **high** and hold **early** — the hold at cruise level costs much less than the same delay at 8000 ft.
- **Expect the approach to change**: a convective cell over the field will move the runway in use and can invalidate the approach you briefed.
- **Slant visual range**: in dust, haze, fog and heavy rain the visibility *along the approach path* is far worse than the reported horizontal visibility, particularly on a shallow slant into low sun. Reported 1500 m in dust can mean you see nothing until well below the normal acquisition point.
- **Wet runway on arrival after a hot dry spell** — the first rain on a rubber-contaminated runway is the most slippery condition of all.

## 7. Low visibility operations

### 7.1 The minima ladder

| Category | Decision height | RVR (typical) |
|---|---|---|
| **CAT I** | **200 ft** (61 m) | **550 m**, or 800 m without the full approach light system |
| **CAT II** | **100 ft** (30 m) | **300–350 m** |
| **CAT IIIA** | **below 100 ft**, typically 50 ft | **≥ 175–200 m** |
| **CAT IIIB** | **below 50 ft, or no DH** | **75 m to 175 m** |
| **CAT IIIC** | **no DH** | **no RVR limitation** — not operationally authorised |

> ⚠️ The exact RVR values are set by the State, the aerodrome's certification, and the operator's approval; the FAA and EASA numbers differ, and the values above are indicative of common practice. Some Wikipedia-sourced figures (CAT IIIA 600 ft RVR = ~180 m, CAT IIIB 600 ft) reflect **US** practice. `needs-verification`

### 7.2 What has to be true simultaneously

**Aerodrome:** certified for the category; ILS of the required performance level with protected sensitive and critical areas; **LVP in force**; approach, runway and taxiway lighting of the required standard with **secondary power** and the specified changeover time; RVR measurement at the required points (touchdown, mid, stop-end); surface movement guidance and control; and reduced movement rates.

**Aircraft:** certified and maintained for the category — autoland (fail-passive for CAT IIIA, **fail-operational** for CAT IIIB), or a certified **HUD/EVS** in some approvals; radio altimeter; autothrottle; the appropriate autopilot redundancy; and the MEL items intact (a single item can downgrade you from CAT III to CAT I on the day).

**Crew:** trained and qualified for the category, with recency; the pilot flying/pilot monitoring task split for a low-visibility approach; and, for CAT II/III, restrictions on the combination of a low-experience captain with certain minima.

**Procedure:** the approach ban (you may not continue below a defined point — commonly **1000 ft above aerodrome elevation** or the outer marker — if the reported RVR is below minima), the **controlling RVR** rules (touchdown always controlling; mid and stop-end become controlling at lower minima), and the missed approach and rollout requirements.

### 7.3 Practical points

- **RVR is measured, visibility is estimated.** They are not the same number and RVR is usually the larger one at night.
- **A CAT III approval is not a licence to plan to CAT III.** Alternate planning minima are based on CAT I even at a CAT III aerodrome, precisely because the CAT III capability may not be there when you arrive.
- **LVP in force means everything slows down**, so factor the taxi and approach delays into fuel.
- **After landing in CAT III**, taxiing in 75 m RVR is genuinely difficult; follow-me vehicles, surface movement radar, and the SMGCS chart matter.

## 8. Contaminated runways, RCAM and the Global Reporting Format

### 8.1 Why the framework exists

Historic runway condition reporting was inconsistent, and friction measurements from different devices were not comparable and did not correlate reliably with aeroplane braking performance on wet or contaminated surfaces. **Southwest 1248 (Chicago Midway, 8 December 2005)** — snow, RVR 4500 ft, an 8 kt tailwind against a 5 kt limit, delayed reverse thrust, a 4500 ft remaining runway against a 5300 ft requirement, one fatality on the ground — was a principal driver of the FAA's **TALPA ARC**, which produced the **Runway Condition Assessment Matrix (RCAM)** and the **runway condition code**, implemented in the US in **2016**. ICAO adopted the concept globally as the **Global Reporting Format (GRF)**.

### 8.2 The RCAM

The aerodrome operator assesses each **third of the runway** and assigns a **Runway Condition Code (RWYCC) from 6 to 0**, based on the **contaminant type, depth and temperature** — not on a friction measurement. The code is then reported through the **SNOWTAM / Runway Condition Report (RCR)** and via ATIS.

| RWYCC | Surface description (summary) | Braking action term | Deceleration / control |
|---|---|---|---|
| **6** | **Dry** | (not reported) | — |
| **5** | Frost; **wet** (damp, or ≤ 3 mm water); **dry snow or wet snow ≤ 3 mm** | **GOOD** | Braking deceleration normal, directional control normal |
| **4** | **Compacted snow at −15 °C outside air temperature and colder** | **GOOD TO MEDIUM** | — |
| **3** | **"Slippery wet"**; dry or wet snow **over compacted snow**; **dry snow > 3 mm**; **wet snow > 3 mm**; compacted snow **warmer than −15 °C** | **MEDIUM** | Noticeably reduced braking; directional control noticeably reduced |
| **2** | **Standing water > 3 mm**; **slush > 3 mm** | **MEDIUM TO POOR** | Risk of hydroplaning |
| **1** | **Ice** | **POOR** | Braking significantly reduced; directional control significantly reduced |
| **0** | **Wet ice**; **water over compacted snow**; **dry or wet snow over ice** | **LESS THAN POOR** | Minimal braking; minimal directional control |

**Downgrade and upgrade.** The aerodrome may **downgrade** a code on the basis of pilot reports of braking action, friction measurements, observation, or other evidence; upgrades require more evidence and a stricter process. **A pilot report of braking action worse than reported is a formal input into the system — file it.**

> ⚠️ The RCAM detail above is given from the widely published matrix. **Verify against ICAO Annex 14 Volume I, PANS-Aerodromes (Doc 9981) and Doc 10064 (Aeroplane Performance Manual) or the FAA's TALPA material before operational use**, and note that the ICAO GRF applicability date (commonly cited as **4 November 2021**, deferred from 2020) was not verified in this session. `needs-verification`

### 8.3 Using it

- **Manufacturer landing performance data** is published against RWYCC, so the code goes directly into the landing distance calculation on the EFB.
- **In-flight landing distance assessment** at the time of arrival, using the actual conditions, is mandatory practice under most modern rule sets, with a safety factor applied to the actual landing distance.
- **Hydroplaning**: dynamic hydroplaning speed ≈ **9 × √(tyre pressure in psi)** in knots for a rotating tyre (≈ 7.7 × √p for a non-rotating one). At 200 psi that is about **127 kt** — well within the landing speed range of a widebody, which is why standing water above 3 mm is a genuine hazard rather than a nuisance. Reverted-rubber and viscous hydroplaning occur at lower speeds.
- **Crosswind limits reduce with the runway condition code.** Most operators publish a crosswind limit table by RWYCC; the demonstrated crosswind on a dry runway is not the limit on RWYCC 2.
- **Braking action reports** should use the standardised terms (GOOD / GOOD TO MEDIUM / MEDIUM / MEDIUM TO POOR / POOR) — not "not bad" or "it was fine".

## 9. Crosswind, tailwind and gust handling

- **Crosswind limits** are usually a **demonstrated** value (a certification demonstration, not a structural limit) on a dry runway, plus operator limits for wet and contaminated surfaces and for autoland.
- **Compute the component properly**: crosswind = wind speed × sin(angle between wind and runway); headwind = × cos. Quick mental table: 30° → half the wind is crosswind; 45° → 0.7; 60° → 0.87; 90° → all of it.
- **Use the right wind.** The **tower/ATIS wind is a 2-minute mean referenced to magnetic north**; the **METAR wind is a 10-minute mean referenced to true north**. Use the tower wind for the approach, and remember the METAR is not the same number.
- **Gust factor.** The common technique is to add **half the gust increment** to the approach speed, capped (typically at 15–20 kt over VREF), with the reminder that **the additive must be bled off before touchdown or the landing distance grows**. Types differ: some FCOMs use a fixed additive, some use half the headwind plus the full gust increment. **Fly the type's procedure.**
- **Tailwind.** Certified tailwind limits are typically **10 kt**, with some types approved to 15 kt. Performance data penalises tailwind at **150 %** of the reported value. A tailwind landing on a contaminated runway is the combination in the Southwest 1248 accident.
- **Wind shear on final** — a decreasing headwind is an energy loss; if the airspeed decays and the thrust required rises, go around early. **The go-around is free; the overrun is not.**

## 10. Diversion decision-making

The decision is rarely difficult; it is usually **late**. Structure it:

1. **Set the decision in advance.** Before top of descent, state aloud: "If we do not have the field visual by X, or if the fuel reaches Y, we go to Z." Brief the diversion approach at the same time as the destination approach.
2. **Distinguish the triggers**: weather below minima; a `TEMPO` that has arrived; fuel reaching minimum diversion; runway closed or contaminated beyond your capability; unacceptable holding delay; an aircraft or medical issue that interacts with the weather.
3. **Prefer the early diversion.** Diverting with a comfortable fuel state to a good aerodrome in daylight with a full set of options is a normal operation. Diverting after two approaches with final reserve in sight is an emergency.
4. **Two approaches is usually the limit** in deteriorating conditions unless something has materially changed (a different runway, a reported improvement, a wind shift). Repeating an identical approach into an unchanged condition is not a plan.
5. **Consider the whole operation** at the diversion field: fire category, runway length for your landing weight, handling, fuel availability, customs and immigration, crew duty limits, passenger welfare, and — in the Gulf and much of Africa and Asia — whether the field is actually open at that hour.
6. **Declare early.** `MINIMUM FUEL` gets you priority; `MAYDAY FUEL` gets you everything. Neither is a reflection on you; delaying either is.
7. **The commander's authority** is absolute here. A dispatcher's flight plan, a company preference and a slot are inputs, not instructions.

## Sources

- [Instrument landing system](https://en.wikipedia.org/wiki/Instrument_landing_system) — Wikipedia (CAT I/II/IIIA/IIIB/IIIC decision heights and RVR, ground and airborne requirements)
- [Southwest Airlines Flight 1248](https://en.wikipedia.org/wiki/Southwest_Airlines_Flight_1248) — Wikipedia (contaminated runway, tailwind, TALPA ARC, 2016 runway condition code implementation)
- [Emirates Flight 521](https://en.wikipedia.org/wiki/Emirates_Flight_521) — Wikipedia (48 °C, windshear, long landing, go-around)
- [Doha](https://en.wikipedia.org/wiki/Doha) — Wikipedia (1992–2021 temperature normals)
- [Hamad International Airport](https://en.wikipedia.org/wiki/Hamad_International_Airport) — Wikipedia (runway dimensions)
- [Density altitude](https://en.wikipedia.org/wiki/Density_altitude) — Wikipedia (DA approximation and performance consequences)
- [North Atlantic Tracks](https://en.wikipedia.org/wiki/North_Atlantic_Tracks) — Wikipedia (SLOP, space-based ADS-B separation reductions)

## Open questions

- **Alternate planning minima table** — the EU-OPS-style values are historical; the current Part-CAT/EASA structure has been revised. `needs-verification`
- **CAT II/III RVR values** — State-, aerodrome- and approval-specific; the figures given mix EASA and FAA practice. `needs-verification`
- **RCAM contaminant/temperature boundaries and the ICAO GRF applicability date (4 November 2021)** — not verified from an ICAO/FAA source in this session. `needs-verification`
- **Oceanic weather-deviation 300 ft offset direction convention** — verify against the current ICAO Doc 4444 and the regional supplementary procedures for the airspace concerned. `needs-verification`
- **Contingency fuel schemes (3 %/5 %/statistical)** and the `TEMPO`/`PROB` treatment for alternates are operator-approval specific.
- **Hydroplaning speed formula constants (9 and 7.7)** are the classic NASA (Horne) values; not fetched this session.
- **Tyre speed limits and the 150 %/50 % wind factoring** are standard certification practice; verify in the AFM.
