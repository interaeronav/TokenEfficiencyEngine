---
id: space.overview
title: Space science and propulsion — domain map
domain: 30_space_science_and_propulsion
tags: [space, astrodynamics, propulsion, launch-vehicles, spacecraft, mission-design, newspace]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
unit_system: SI
related: [space.orbital-mechanics, space.chemical-propulsion, space.electric-advanced-propulsion, space.launch-industry, space.spacecraft-engineering, space.missions, space.careers, space.books, space.tools]
sources:
  - {title: "2025 in spaceflight", url: "https://en.wikipedia.org/wiki/2025_in_spaceflight", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Falcon 9", url: "https://en.wikipedia.org/wiki/Falcon_9", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Starlink", url: "https://en.wikipedia.org/wiki/Starlink", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Artemis program", url: "https://en.wikipedia.org/wiki/Artemis_program", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "NASA Systems Engineering Handbook (SP-6105)", url: "https://www.nasa.gov/reference/systems-engineering-handbook/", publisher: "NASA", accessed: "2026-08-25"}
---

# Space science and propulsion — domain map

**Summary.** This domain covers the physics, engineering and industry of operating machines beyond the atmosphere: the astrodynamics that decides where a spacecraft can go and how much it costs in delta-v; the propulsion that supplies that delta-v, chemical and electric; the launch vehicles and the market that has reshaped access to orbit since 2015; the engineering of the spacecraft bus itself; and the science payloads that justify the whole enterprise. The organising quantity throughout is **delta-v** — the velocity budget — and the organising equation is Tsiolkovsky's. Everything else is a consequence: staging exists because the rocket equation is exponential, electric propulsion exists because exhaust velocity beats propellant mass, and reusability exists because the hardware is the dominant cost once propellant is only ~0.3% of the price of a flight.

## Key facts

| Quantity | Value | Note |
|---|---|---|
| Delta-v, surface to 200 km LEO | ≈ 9.3–9.6 km/s | 7.8 km/s orbital + 1.5–1.8 km/s gravity, drag and steering losses |
| Delta-v, 28.5° LEO → GEO | ≈ 4.22 km/s | Hohmann with combined plane change at apogee (worked in `01`) |
| Delta-v, LEO → trans-Mars injection | ≈ 3.6 km/s | v∞ ≈ 2.94 km/s, C3 ≈ 8.7 km²/s² |
| Best flight-proven chemical Isp | 452 s vac (RS-25, LOX/LH2) | Staged combustion, 69:1 nozzle |
| Best flight-proven electric Isp | 4,170 s (NASA NEXT at 6.9 kW) | 237 mN thrust — 17,600× less than one RS-25 |
| Orbital launch attempts, 2025 | 330 attempts, 317 successes, 13 failures | Global total |
| Falcon 9 flights / landings | 587 flights, 584 successes; 542 landings of 553 attempts (12 Jan 2026) | 99.5% mission success |
| Falcon 9 list price | US$69.85 M (2025) | ≥17,400 kg to LEO reusable |
| Starlink satellites in orbit | ≈10,413, 10,397 operational (June 2026) | ~75% of active manoeuvrable satellites |
| Solar radiation pressure at 1 AU | 9.08 μPa (perfect reflector) | The entire budget of a solar sail |

## The six territories

### 1. Astrodynamics (`01_orbital-mechanics.md`)

The two-body problem is integrable and its solution — the conic section — is the backbone. From it come the vis-viva equation `v² = μ(2/r − 1/a)`, the six classical orbital elements, Kepler's equation for time of flight, and the closed-form manoeuvre theory (Hohmann, bi-elliptic, plane change) that lets you cost a mission before you design a bolt. Beyond two bodies you get perturbations — Earth's J2 oblateness (which makes sun-synchronous and Molniya orbits possible), atmospheric drag, lunisolar third-body terms, solar radiation pressure — and the patched-conic method that turns interplanetary trajectory design into a sequence of two-body problems glued at spheres of influence. Gravity assists and low-thrust spiral trajectories are the two escapes from the tyranny of the rocket equation.

### 2. Launch (`04_launch-vehicles-and-the-industry.md`)

Getting to orbit is a ~9.4 km/s problem attacked by staging. The market since 2015 has been transformed by one company: Falcon 9's booster reuse changed the cost structure of medium-lift, and Starlink converted SpaceX from a launch provider into its own dominant customer. The rest of the industry — ULA's Vulcan, Arianespace's Ariane 6, JAXA's H3, Blue Origin's New Glenn, the Chinese state and commercial vehicles, Rocket Lab's Electron and Neutron — is responding. The small-launch sector that bloomed after 2015 has consolidated hard; most of the ~150 announced small launchers never flew.

### 3. Propulsion, chemical (`02_chemical-propulsion.md`)

A rocket engine is a chemical heat source feeding a converging-diverging nozzle. Performance decomposes cleanly: characteristic velocity `c*` measures the combustion, thrust coefficient `C_F` measures the nozzle, and effective exhaust velocity is their product, `c = c* · C_F`. The engineering is in feeding the chamber (pressure-fed, gas generator, staged combustion, full-flow staged combustion, expander, electric pump-fed), keeping it from melting (regenerative cooling, film cooling, ablatives), and keeping it from resonating itself apart (combustion instability). Propellant choice is a trade among Isp, density, storability, toxicity and cost: LOX/LH2 wins on Isp, LOX/RP-1 on density and cost, LOX/CH4 on the combination plus reusability, hypergolics on storability, solids on simplicity and thrust density.

### 4. Propulsion, electric and advanced (`03_electric-and-advanced-propulsion.md`)

Decouple the energy source from the propellant and Isp rises by an order of magnitude — but thrust falls by three or four. Electric propulsion is now routine: gridded ion engines (NSTAR on Deep Space 1 and Dawn, NEXT on DART, T6 on BepiColombo), Hall-effect thrusters (SPT-100 and its descendants, now flying by the thousand on Starlink), and electrospray/FEEP at the small end. The governing trade is the **jet power** relation `P_jet = ½ F c`: every newton of thrust at 30 km/s exhaust costs at least 15 kW of jet power, so the power system, not the thruster, sets the mission. Beyond electric lie nuclear thermal (real, tested, repeatedly cancelled), solar sails (flown, tiny, real), and a long tail of concepts ranging from plausible to pseudoscience — the EmDrive being the field's standing cautionary tale.

### 5. Spacecraft engineering (`05_spacecraft-engineering.md`)

The bus is a set of interacting subsystems — structure, thermal, power, attitude determination and control, propulsion, command and data handling, communications — sized against mass, power and link budgets, and hardened against a hostile environment: hard vacuum, ±150 K thermal cycles, trapped-particle radiation, single-event effects, atomic oxygen in LEO, and an increasingly crowded debris population. The CubeSat standard (1U = 10 cm cube, ~1.33 kg) collapsed the cost of entry and created an ecosystem of COTS parts, rideshare launch and university programmes.

### 6. Space science and missions (`06_space-science-and-missions.md`)

Why any of it happens. Space astronomy (Hubble, Chandra, Spitzer, Kepler/TESS, Gaia, JWST, Euclid, Roman), planetary exploration (Voyager, Galileo, Cassini–Huygens, New Horizons, Juno, the Mars programme, the small-body sample returns), heliophysics (Parker Solar Probe, Solar Orbiter), Earth observation, and human spaceflight (ISS, Artemis, Tiangong, commercial LEO destinations).

## The three equations that govern everything

**Tsiolkovsky's rocket equation.**

```
Δv = v_e · ln(m₀/m_f) = I_sp · g₀ · ln(m₀/m_f)
```

Exponential in the mass ratio. A stage with structural coefficient ε = 0.08 and Isp = 350 s cannot exceed `3.432 km/s × ln(1/0.08) = 8.67 km/s` even with zero payload — which is why single-stage-to-orbit remains a paper exercise for chemical rockets and why every orbital launcher stages.

**The vis-viva equation.**

```
v² = μ (2/r − 1/a)
```

The energy integral of the two-body problem. It reduces most manoeuvre problems to arithmetic: pick the two orbits, evaluate v at the common radius, difference them.

**The jet power relation.**

```
P_jet = ½ · F · c = ½ · ṁ · c²
```

Thrust and Isp trade against available power. A 5 kW Hall thruster at Isp 1,600 s (c = 15.7 km/s) with 50% total efficiency produces roughly `2 × 0.5 × 5000 / 15700 ≈ 0.32 N`. This single relation explains why electric propulsion is used for station-keeping and slow orbit-raising and never for launch.

## How the pieces constrain each other

A mission design loop runs roughly like this, and the NASA Systems Engineering Handbook (NASA/SP-6105, latest revision 27 March 2024) formalises it:

1. **Science or service requirement** → orbit. (A radar mapper wants a dawn–dusk sun-synchronous orbit; a comms satellite wants GEO; a gravity-wave observatory wants a heliocentric drift-away.)
2. **Orbit** → delta-v budget, including insertion, station-keeping over life, momentum dumping, and disposal.
3. **Delta-v + propulsion choice** → propellant mass fraction via the rocket equation.
4. **Payload + propellant** → dry mass budget → launch vehicle class → launch cost.
5. **Orbit + mission duration** → radiation dose → parts selection → mass and cost again.
6. **Data rate + orbit** → link budget → antenna size and transmit power → power budget → solar array area and battery capacity → mass again.

Every arrow is a loop back. The classic outcome is *mass growth*: SMAD-style practice carries 20–30% mass margin at preliminary design review precisely because it always grows.

## The delta-v map

Every mission is a path through this table. Figures are impulsive, ideal, and exclude losses unless stated; they are computed in `01_orbital-mechanics.md` from μ_Earth = 398,600.4418 km³/s² and R_Earth = 6,378.137 km.

| From → To | Δv (km/s) | Notes |
|---|---|---|
| Earth surface → 200 km LEO | 9.3–9.6 | 7.784 km/s ideal + 1.5–1.8 km/s losses |
| 400 km LEO circular velocity | 7.669 | Period 92.6 min |
| LEO (400 km) → GTO | 2.40 | Perigee burn of a Hohmann to GEO radius |
| GTO → GEO, coplanar | 1.46 | Apogee circularisation |
| GTO (28.5° inclined) → GEO | 1.82 | Combined circularisation + 28.5° plane change |
| LEO 28.5° → GEO, total | 4.22 | Two burns, plane change folded into the second |
| LEO → Earth escape (C3 = 0) | 3.22 | From 200 km: 11.008 − 7.784 |
| LEO → trans-lunar injection | ≈3.15 | v∞ small; TLI is barely more than escape |
| LEO → trans-Mars injection | ≈3.61 | v∞ = 2.94 km/s, C3 = 8.67 km²/s² |
| Mars arrival → 250 km Mars orbit | ≈2.1 propulsive, ≈0 aerocapture | Which is why every Mars orbiter since 2001 aerobrakes |
| GEO station-keeping, N–S | 45–55 m/s per year | Lunisolar; dominates the budget |
| GEO station-keeping, E–W | 2–6 m/s per year | Triaxiality of the geopotential |
| LEO drag make-up, 400 km | 20–100 m/s per year | Strongly solar-cycle dependent |
| Graveyard disposal from GEO | ≈11 m/s | Raise ≈300 km above GEO |
| De-orbit from 400 km LEO | ≈120 m/s | Lower perigee to ≈50 km |

Two observations follow. First, GEO comms satellites spend more delta-v on 15 years of station-keeping (≈750 m/s) than on the last stage of getting there. Second, the Earth surface → LEO leg costs more than LEO → anywhere in the inner solar system — which is the entire argument for orbital propellant depots and for making Starship's economics work.

## Orbit taxonomy at a glance

| Regime | Altitude / semi-major axis | Period | Typical use |
|---|---|---|---|
| VLEO | 200–450 km | 88–94 min | Imaging, Starlink lower shell, ISS (≈400 km, 51.6°) |
| LEO | 450–2,000 km | 94–127 min | Constellations, remote sensing, science |
| SSO | 600–800 km, i ≈ 97.8–98.6° | ≈97–101 min | Consistent local solar time; J2-driven |
| MEO | 2,000–35,786 km | 2–12 h | GNSS (GPS a = 26,560 km, 12 h; Galileo 23,222 km, 14 h) |
| Molniya | a = 26,554 km, e = 0.74, i = 63.4° | ≈11.97 h | Long dwell over high latitudes |
| GEO | a = 42,164 km, e ≈ 0, i ≈ 0 | 23 h 56 m 4 s | Comms, meteorology (GOES, Meteosat) |
| GTO | 185 × 35,786 km typical | ≈10.5 h | Transfer only |
| HEO / Tundra | a = 42,164 km, e ≈ 0.27, i = 63.4° | 24 h | Sirius XM, regional coverage |
| Sun–Earth L1 | 1.5 × 10⁶ km sunward | Halo, ≈6 months | SOHO, DSCOVR, ACE — uninterrupted Sun view |
| Sun–Earth L2 | 1.5 × 10⁶ km anti-sunward | Halo, ≈6 months | JWST, Gaia, Euclid, Planck — cold, stable thermal |
| Heliocentric drift-away | ≈1 AU, slowly receding | 1 yr | Kepler, Spitzer, Roman-adjacent concepts |

## A compressed history, and why the dates matter

- **1903** Tsiolkovsky publishes the rocket equation. **1926** Goddard flies the first liquid rocket. **1942** the A-4/V-2 becomes the first object in space.
- **1957** Sputnik 1. **1961** Gagarin. **1969** Apollo 11 — the Saturn V's 3,000+ t liftoff mass for 48.6 t to trans-lunar injection remains the benchmark.
- **1981–2011** the Space Shuttle: partially reusable, 135 flights, two losses, and a cost per kg that never approached the promise. Its RS-25 engines are the highest-Isp production chemical engines ever flown and are now being expended on SLS.
- **1998–2011** ISS assembly; continuous human occupation since 2 November 2000.
- **2008** Falcon 1 reaches orbit. **2015** Falcon 9 first booster landing. **2019** first Starlink launch. **2024** first booster catch by the launch tower (Starship IFT-5, 13 October 2024).
- **2021–2022** JWST launched 25 December 2021 on Ariane 5, first images 12 July 2022.
- **2025** 330 orbital launch attempts globally, 317 successful — an all-time record, roughly triple the 2015 rate.
- **2026** Artemis II flew 1–11 April 2026, the first crewed flight beyond LEO since Apollo 17; the Lunar Gateway was cancelled the same year in favour of a lunar surface base.

## Vocabulary

- **Isp (specific impulse)** — impulse per unit weight of propellant, in seconds. `I_sp = F/(ṁ g₀)`. Multiply by g₀ = 9.80665 m/s² to get effective exhaust velocity in m/s. Always state whether sea-level or vacuum.
- **C3** — characteristic energy, `C3 = v∞²`, in km²/s². The standard currency for launch-vehicle escape performance.
- **Mass ratio** — `m₀/m_f`. **Structural coefficient** ε = m_structure/(m_structure + m_propellant). **Payload fraction** π = m_payload/m₀.
- **Throughput** — for electric thrusters, total propellant a unit can process before wear-out; the practical life limit.
- **Total ionising dose (TID)** — cumulative radiation damage, in krad(Si). **SEE** — single-event effects: upsets, latch-ups, burnout.
- **Bus vs payload** — the bus is everything that keeps the payload alive and pointed.
- **TRL** — technology readiness level, 1 (basic principles) to 9 (flight proven). NASA and ESA definitions differ in detail.

## Cross-references

- `29_aerospace_engineering/` — atmospheric flight, aerodynamics, structures and materials, propulsion for air-breathing vehicles. Re-entry aerothermodynamics sits at the boundary and is treated here in `01`.
- `26_computer_engineering/` and `27_semiconductors_and_chip_design/` — radiation-hardened processors, FPGA design and the COTS-versus-rad-hard trade are elaborated in `05` here but the device physics belongs there.
- `31_aviation_industry/` — range safety, airspace integration and the regulatory overlap with launch licensing.
- `23_cartography_and_mapping/` — Earth observation products, geodetic reference frames (WGS 84, ITRF) and the coordinate systems that orbital mechanics feeds.

## Reading order

`01` (orbital mechanics) is the prerequisite for everything else — read it first even if propulsion is the interest, because delta-v is the currency propulsion is paid in. `02` and `03` are parallel and can be read in either order. `05` depends on `01` lightly and on nothing else. `04` and `06` are largely narrative and can be sampled. `07`–`09` are practical: how to enter the field, what to read, what to run.

## Open questions

- Reusable-launch cost data is the weakest evidence base in the domain. Internal cost per flight is not published by any operator; all "cost per kg" figures in `04` are either list prices (public, verifiable) or third-party estimates (marked as such).
- Chinese vehicle performance figures are drawn from state media and secondary compilations; treat payload numbers as nominal rather than demonstrated.

## Sources

- [2025 in spaceflight](https://en.wikipedia.org/wiki/2025_in_spaceflight) — Wikipedia, accessed 2026-08-25
- [Falcon 9](https://en.wikipedia.org/wiki/Falcon_9) — Wikipedia, accessed 2026-08-25
- [Starlink](https://en.wikipedia.org/wiki/Starlink) — Wikipedia, accessed 2026-08-25
- [Artemis program](https://en.wikipedia.org/wiki/Artemis_program) — Wikipedia, accessed 2026-08-25
- [NASA Systems Engineering Handbook (NASA/SP-6105)](https://www.nasa.gov/reference/systems-engineering-handbook/) — NASA, accessed 2026-08-25
- [NEXT (ion thruster)](https://en.wikipedia.org/wiki/NEXT_(ion_thruster)) — Wikipedia, accessed 2026-08-25
- [RS-25](https://en.wikipedia.org/wiki/RS-25) — Wikipedia, accessed 2026-08-25
- [Solar sail](https://en.wikipedia.org/wiki/Solar_sail) — Wikipedia, accessed 2026-08-25
