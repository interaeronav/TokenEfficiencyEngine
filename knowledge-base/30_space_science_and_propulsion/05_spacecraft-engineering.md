---
id: space.spacecraft-engineering
title: Spacecraft engineering — subsystems, budgets and environment
domain: 30_space_science_and_propulsion
tags: [spacecraft, systems-engineering, adcs, thermal-control, power-systems, radiation, link-budget, cubesat, mass-budget]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
unit_system: SI
related: [space.overview, space.orbital-mechanics, space.electric-advanced-propulsion, space.books]
sources:
  - {title: "NASA Systems Engineering Handbook (SP-6105)", url: "https://www.nasa.gov/reference/systems-engineering-handbook/", publisher: "NASA", accessed: "2026-08-25"}
  - {title: "Van Allen radiation belt", url: "https://en.wikipedia.org/wiki/Van_Allen_radiation_belt", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "CubeSat information", url: "https://www.cubesat.org/cubesatinfo", publisher: "Cal Poly CubeSat Program", accessed: "2026-08-25"}
  - {title: "International Space Station", url: "https://en.wikipedia.org/wiki/International_Space_Station", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "James Webb Space Telescope", url: "https://en.wikipedia.org/wiki/James_Webb_Space_Telescope", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "ECSS active standards", url: "https://ecss.nl/standards/active-standards/", publisher: "ECSS", accessed: "2026-08-25"}
---

# Spacecraft engineering — subsystems, budgets and environment

**Summary.** A spacecraft is a set of tightly coupled subsystems flying in an environment that is hostile in half a dozen independent ways at once. Design proceeds by budgets — mass, power, link, pointing, delta-v, data — each of which is allocated top-down, tracked with margin, and reconciled iteratively as the design converges. This file covers the subsystem breakdown with real allocation percentages, the space environment and its effects, thermal control, power systems, attitude determination and control, a fully worked telecommunications link budget, and the CubeSat standard.

## Key facts

| Quantity | Typical value |
|---|---|
| Dry mass allocation, bus vs payload | Payload 15–35% of dry mass for science; 40–50% for comsats |
| Recommended mass margin at PDR | 20–30% (NASA/AIAA practice) |
| Solar constant at 1 AU | 1,361 W/m² (varies ±3.4% with Earth's orbital eccentricity) |
| Triple-junction GaAs cell efficiency | 28–32% BOL; ≈30% is the current production figure |
| Li-ion depth of discharge, LEO | 15–25% (≈5,500 cycles/year at 90 min orbits) |
| Li-ion depth of discharge, GEO | 60–80% (≈90 eclipses/year) |
| MMRTG electrical output | ≈110 W BOL, ≈1.6%/year decline, ≈4.8 kg PuO₂ |
| Inner Van Allen belt | 1,000–12,000 km; protons >100 MeV |
| Outer Van Allen belt | 13,000–60,000 km; electrons 0.1–10 MeV |
| Slot region | 2–4 Earth radii — relatively benign, used by MEO |
| Boltzmann constant in link budgets | 10 log₁₀(k) = −228.6 dBW/K/Hz |
| CubeSat 1U | 100 × 100 × 113.5 mm; CDS Rev 14.1 (Feb 2022) covers 1U–12U |

## 1. The subsystem breakdown

| Subsystem | Function | Typical % of dry mass | Typical % of orbit-average power |
|---|---|---|---|
| **Structure & mechanisms** | Load paths, launch loads, deployables, separation | 20–28% | ≈0 (heaters aside) |
| **Thermal control** | Keep everything in its temperature band | 2–6% | 5–15% (heaters) |
| **Power (EPS)** | Generate, store, regulate, distribute | 20–30% | 5–10% (own losses) |
| **ADCS / GNC** | Determine and control attitude, sometimes orbit | 5–12% | 10–25% |
| **Propulsion** | Δv and momentum management (dry mass only) | 3–10% | 5–20% (EP: dominant) |
| **C&DH / OBC** | Command, telemetry, data storage, timing | 2–6% | 5–15% |
| **Communications (TT&C + payload downlink)** | Uplink, downlink, ranging | 3–8% | 15–35% (transmit) |
| **Harness** | Cabling — always underestimated | 4–8% | — |
| **Payload** | The reason for the mission | 15–35% (science), 40–50% (comsat) | 20–50% |

These are ranges from standard practice (SMAD-style allocations), not laws. Two observations: harness is routinely 5% of dry mass and is routinely forgotten at concept stage; and the power subsystem's mass is dominated by batteries in LEO and by arrays in deep space.

### Budgets and margins

**Mass budget.** Tracked as *current best estimate* (CBE) plus *contingency* per item, based on maturity: 5% for flight-proven hardware, 10% for modified, 20–30% for new designs. System-level margin sits on top. NASA and ESA practice carries **20–30% total margin at preliminary design review**, falling to 5% or less at flight. Mass growth from concept to launch of 20–40% is historically normal, which is why the margin exists.

**Power budget.** Built per operational mode (safe, nominal, payload-on, eclipse, downlink), for both beginning-of-life and end-of-life array performance and worst-case sun angle. The binding case is usually end-of-life, maximum eclipse, payload-on.

**Delta-v budget.** Insertion errors, orbit acquisition, station-keeping over design life, momentum dumping (if using thrusters), collision-avoidance manoeuvres, and end-of-life disposal — plus 5–10% margin.

**Pointing budget.** Decomposed into knowledge error (sensors), control error (actuators and control law), and stability/jitter (structural modes, reaction wheel imbalance, cryocooler vibration).

**Data budget.** Payload generation rate × duty cycle versus downlink capacity × contact time, with onboard storage sized for the worst outage.

The NASA Systems Engineering Handbook (**NASA/SP-6105**, revision of **27 March 2024**) is the reference for how these are managed through the project life cycle, and the ECSS **E** (engineering), **M** (project management), **Q** (product assurance), **S** (system implementation) and **U** (space sustainability) branches are the European equivalent — see `08` for how to obtain both.

## 2. The space environment

### Vacuum

Below ~10⁻⁶ Pa, materials **outgas**. Volatiles migrate and condense on the coldest surfaces — which are the optics and the radiators, exactly where you least want them. Mitigations: material screening to **ASTM E595** (total mass loss ≤1.0%, collected volatile condensable material ≤0.1%), vacuum bakeout before delivery, and vent path design so trapped gas escapes without popping a structure during ascent depressurisation (typically 5–10 kPa/s).

Vacuum also removes convection entirely — all heat transfer is conduction and radiation — and enables **cold welding**: clean metal surfaces in contact without an oxide layer diffusion-bond. Galled bearings and stuck deployment mechanisms are a real failure mode; the fix is dissimilar materials, dry-film lubricants (MoS₂, sputtered), or space-rated greases (Braycote).

### Thermal cycling

A LEO spacecraft crosses the terminator roughly every 45 minutes — about **5,500 cycles per year**. Surface temperature excursions of ±100 °C on external elements are routine. This is a fatigue driver for solar array hinges, coatings, adhesives, and especially for anything with a coefficient-of-thermal-expansion mismatch (electronics solder joints, bonded optics). Qualification is by thermal-vacuum cycling to at least the predicted number of cycles times a factor, with margin on the extremes (typically qualification limits ±10 °C beyond acceptance).

### Radiation

Three distinct threats with three distinct mitigations.

**Trapped particles (Van Allen belts).** The **inner belt** spans roughly 1,000–12,000 km (L = 1.2–3) and is dominated by protons exceeding 100 MeV plus electrons of hundreds of keV. The **outer belt** runs from about 13,000 to 60,000 km (3–10 Earth radii, most intense at 4–5 R_E) and is dominated by 0.1–10 MeV electrons. Between them, the **slot region** at 2–4 R_E is comparatively benign and is where MEO constellations sit. The **South Atlantic Anomaly** is the region where the offset, tilted geomagnetic dipole brings the inner belt down to roughly 200 km altitude — LEO spacecraft take most of their trapped-particle dose there, and instruments are commonly switched off during passes.

**Solar particle events.** Sporadic, unpredictable, dominated by protons of 10–100 MeV, and the main hazard to crew beyond the magnetosphere. A large event can deliver more dose in hours than a year of background.

**Galactic cosmic rays.** Low flux, extremely high energy (GeV/nucleon), including heavy ions. Effectively unshieldable — a few g/cm² of aluminium produces *secondary* showers that can make things worse. GCR is the dominant single-event-effect driver in deep space and the limiting factor for long-duration human Mars missions.

**Effects.**
- **Total ionising dose (TID)**, in krad(Si): cumulative charge trapping in oxides shifts CMOS threshold voltages and raises leakage until the part fails. Typical mission requirements: 5–20 krad for a LEO smallsat behind normal structure, 30–100 krad for GEO over 15 years, and 100 krad to >1 Mrad for Jupiter missions. Juno carried a 1 cm-thick titanium **vault** (≈200 kg) around its electronics for exactly this reason; Europa Clipper carries a similar vault.
- **Displacement damage dose**: lattice damage from non-ionising energy loss; degrades solar cells, CCDs/CMOS imagers and optocouplers.
- **Single-event effects (SEE)**: a single ion deposits enough charge to flip a bit (**SEU**), latch a parasitic thyristor and draw destructive current (**SEL**), or destroy a power MOSFET (**SEB/SEGR**). SEU is handled by EDAC (Hamming or Reed–Solomon), memory scrubbing and triple modular redundancy; SEL by current-limiting and latch-up protection circuits; SEB by derating.

**Rad-hard versus COTS.** Radiation-hardened parts (RHBD — rad-hard by design; RHBP — by process) cost 100–1,000× their commercial equivalents, run several process generations behind, and have long lead times. A rad-hard processor such as the RAD750 delivers on the order of 200 MIPS at 133 MHz; a commercial ARM part delivers orders of magnitude more per watt. The modern smallsat approach is **COTS with architectural mitigation**: cheap commercial parts, watchdog timers, current-limited power switching, EDAC on all memory, frequent scrubbing, redundant voting across multiple commercial processors, and acceptance of a finite failure rate. This works well in LEO for short missions and progressively less well as dose and mission length rise. Class-A flagship missions still fly rad-hard.

### Atomic oxygen

In LEO between roughly 200 and 700 km, atomic oxygen is the dominant neutral species. At 7.8 km/s the impact energy is ~5 eV, enough to erode polymers, silver and osmium. Kapton erodes at roughly 3 × 10⁻²⁴ cm³/atom. Mitigation: silica or SiO₂ coatings, aluminised outer layers on MLI, and choosing materials (Teflon FEP degrades but slowly; polyimide needs protection).

### Micrometeoroids and orbital debris (MMOD)

Natural micrometeoroids arrive at 10–70 km/s; orbital debris at up to 15 km/s relative. Protection is by **Whipple shield** — a thin sacrificial bumper spaced ahead of the pressure wall, which shocks the impactor into a spray of vapour and fragments that the rear wall can absorb. The ISS uses stuffed Whipple shields with Nextel and Kevlar layers.

The debris population is the field's slow-motion crisis. The **Kessler syndrome** — collisional cascading — is not hypothetical: the 2007 Fengyun-1C ASAT test created over 3,000 catalogued fragments, and the 2009 Iridium 33 / Kosmos 2251 collision created around 2,000 more. Current mitigation practice (IADC guidelines, adopted into national licensing) requires disposal within 25 years of end of mission, tightened by the US FCC to **5 years for LEO** from 2024. Compliance is imperfect. Conjunction assessment and collision-avoidance manoeuvres are now routine operational work.

## 3. Thermal control

The problem: reject payload and electronics waste heat while keeping every component inside its qualification band, across eclipse/sunlight transitions, beginning-of-life to end-of-life optical degradation, and all attitudes.

**The governing balance** at steady state:

```
α_s A_solar q_solar + α_s A_albedo q_albedo + ε A_IR q_earth + Q_internal = ε σ A_rad (T⁴ − T_sink⁴)
```

Everything hinges on the ratio **α/ε** — solar absorptivity over infrared emissivity — of external surfaces. Second-surface silvered Teflon has α ≈ 0.09 and ε ≈ 0.8 (α/ε ≈ 0.11) and is the classic radiator finish. White paint (Z93, AZ-93) is similar at BOL but degrades under UV and charged particles; **beginning-of-life versus end-of-life α is one of the standard thermal design traps** — a radiator sized on BOL properties will run hot after five years.

**Passive techniques (always preferred — no power, no failure modes):**
- **Multi-layer insulation (MLI)**: 10–30 layers of aluminised Mylar or Kapton separated by Dacron netting, with an effective emissivity of 0.01–0.03. JWST's sunshield is the extreme case: five layers of aluminium-coated Kapton E, ~0.1 mm each, holding the cold side **below 50 K (−223 °C)** with MIRI required to stay under 6 K.
- **Surface finishes and coatings**, optical solar reflectors (quartz mirror tiles) on GEO radiators.
- **Conductive isolation**: titanium or composite standoffs, thermal washers.

**Semi-active and active:**
- **Radiators** — sized on `Q = ε σ A (T_rad⁴ − T_sink⁴)`. For a radiator at 300 K with ε = 0.8 to deep space: `q = 0.8 × 5.67e−8 × 300⁴ = 367 W/m²`. That is the number to remember: **≈370 W per square metre at room temperature**, less whatever solar and albedo load the radiator sees.
- **Heat pipes** — constant-conductance (ammonia in aluminium grooved extrusion) to spread heat isothermally; **variable-conductance heat pipes** with a non-condensable gas reservoir to regulate; **loop heat pipes** for long transport and for pumping against gravity in ground test.
- **Louvres** — bimetallic-actuated vane assemblies that vary effective emissivity by roughly 5:1. Passive, self-regulating, mechanically risky, and still used (Juno, several Mars landers).
- **Heaters** — resistive patches on mechanical or software thermostats. Simple, reliable, and the largest single housekeeping power line item on many spacecraft.
- **Cryocoolers** — Stirling or pulse-tube for infrared detectors. JWST's MIRI needs a dedicated 6 K cryocooler; its vibration is a jitter source that has to be budgeted against the pointing requirement.

## 4. Power systems

**Solar array sizing.** Work backwards from the orbit-average load.

```
P_array_required = [ P_daylight·T_day/η_day + P_eclipse·T_eclipse/η_eclipse ] / T_day
```

where η_day ≈ 0.85 and η_eclipse ≈ 0.6 account for distribution and charge/discharge losses.

**Worked.** A 400 km LEO satellite with a 150 W orbit-average load, orbit period 92.6 min, eclipse 35 min, daylight 57.6 min:

```
P_array = [150 × 57.6/0.85 + 150 × 35/0.6] / 57.6 = [10,165 + 8,750]/57.6 = 328.4 W (EOL, at normal incidence)
```

Then account for cell efficiency, packing factor, degradation and incidence angle:

```
A = P_array / (q_solar · η_cell · F_packing · F_degradation · cos θ)
  = 328.4 / (1361 × 0.30 × 0.90 × 0.85 × 0.90) = 1.168 m²
```

That is the honest answer: a 150 W LEO spacecraft needs roughly **1.17 m² of triple-junction array**, not the 0.37 m² a naive `150/(1361×0.3)` calculation gives. Each factor matters.

**Cells.** Triple-junction GaInP/GaAs/Ge at 28–32% BOL is the standard; silicon (14–18%) survives in cost-driven CubeSats. Degradation is 1.5–3% per year in LEO, faster if the orbit crosses the belts, and can be dramatic during an electric-propulsion spiral through the inner belt.

**Batteries.** Li-ion has displaced NiH₂ and NiCd almost entirely (specific energy 130–250 Wh/kg versus 50–60 for NiH₂). Depth of discharge is the life driver:

| Orbit | Cycles per year | Typical DoD |
|---|---|---|
| LEO | ≈5,500 | 15–25% |
| GEO | ≈90 (two 45-day eclipse seasons) | 60–80% |
| Interplanetary | Very few | Up to 80% |

**Worked.** A LEO satellite needing 150 W through a 35-minute eclipse at 20% DoD, with 90% discharge efficiency:

```
E_required = 150 × (35/60) = 87.5 Wh
C_battery = 87.5 / (0.20 × 0.90) = 486.1 Wh  →  ≈3.2 kg at 150 Wh/kg
```

**RTGs.** Where sunlight is too weak or the duty cycle too long. An **MMRTG** produces ≈110 W electrical at beginning of life from ≈4.8 kg of ²³⁸PuO₂ (≈2,000 W thermal), declining ≈1.6% per year, at ≈45 kg total mass — a specific power of ~2.4 W/kg, which is terrible, and an operating life measured in decades, which is why it is used. Voyager's RTGs produced 470 W at launch in 1977 and still return engineering data. Beyond about 4–5 AU, solar is impractical for most missions; Juno at 5.2 AU proved otherwise with 60 m² of array producing ~500 W at Jupiter, and Europa Clipper carries a 30.5 m span array (two wings, ~18 m² each) producing ~600 W in the Jovian system.

**Distribution.** Unregulated, sun-regulated or fully regulated buses at 28 V (heritage), 50 V, or 100 V for high-power platforms (higher voltage cuts harness mass, but above ~100 V in LEO plasma you must manage arcing). Peak power tracking versus direct energy transfer is the standard architecture trade.

## 5. Attitude determination and control

### Sensors

| Sensor | Accuracy | Notes |
|---|---|---|
| Sun sensor (coarse) | 1–5° | Cheap, needs sun |
| Sun sensor (fine, digital) | 0.01–0.1° | |
| Magnetometer | 0.5–3° | Only useful in LEO; field model error dominates |
| Earth/horizon sensor | 0.05–0.5° | IR limb sensing |
| **Star tracker** | 1–10 arcsec (cross-boresight) | The precision instrument; needs a dark, unoccluded field |
| Gyroscope (FOG, HRG, MEMS) | Drift 0.001–10 °/h | Provides rate between star tracker updates; drifts, must be bounded |
| GNSS receiver | Position 1–10 m; attitude with multiple antennas | LEO only |

Determination is almost always a **Kalman filter** — typically a multiplicative extended Kalman filter (MEKF) on a quaternion state with gyro bias — fusing star tracker attitude with gyro rate. Static determination from two vector observations uses **TRIAD**; least-squares over many observations uses **QUEST** or Davenport's q-method (Wahba's problem).

### Actuators

- **Reaction wheels.** Momentum storage 0.01–100 N·m·s, torque 0.005–1 N·m. Three for control, four in a pyramid or tetrahedron for single-fault tolerance. Failure modes: bearing wear, and **zero-crossing** friction nonlinearity that creates pointing jitter — commonly avoided by biasing the wheel speed away from zero.
- **Control moment gyros (CMGs).** A constant-speed wheel gimballed to steer its momentum vector. Torque amplification is large — the ISS's four double-gimbal CMGs each store 4,760 N·m·s — making them the choice for large or agile vehicles. Their problem is **singularities**: gimbal configurations where the array cannot produce torque in some direction. Steering laws (singularity-robust pseudo-inverse, null-motion) manage this and are the hard part of any CMG design.
- **Magnetorquers.** Coils or torque rods producing `τ = m × B`. Milli-newton-metre class, LEO only, no consumables, and the standard way to **desaturate reaction wheels** without spending propellant. Nearly universal on CubeSats.
- **Thrusters.** Highest torque, needed for large slews and for momentum dumping outside the magnetosphere. Consumes propellant, so life-limited.
- **Passive.** Gravity-gradient booms (stabilise two axes, ±5° at best), permanent magnets plus hysteresis rods (the classic passive CubeSat combination), and yo-yo despin.

### Control laws

**B-dot detumbling** is the first thing a satellite does after separation, using only a magnetometer and magnetorquers:

```
m = −k (dB/dt)
```

It dissipates rotational energy monotonically and needs no attitude knowledge at all. Robust, cheap, and used on essentially every LEO smallsat.

**Quaternion feedback** for three-axis pointing:

```
τ = −k_p q_e,vec − k_d ω_e
```

with `q_e` the error quaternion. This is globally stabilising (with an unwinding caveat handled by sign selection on `q_e,scalar`) and forms the core of most implementations, wrapped in gain scheduling and actuator allocation.

**Gravity-gradient torque** is a persistent LEO disturbance:

```
τ_gg = (3μ/r³) (r̂ × I r̂)
```

with **aerodynamic torque** (offset between centre of pressure and centre of mass), **solar radiation pressure torque** (dominant at GEO) and **residual magnetic dipole torque** completing the disturbance environment. Sizing wheels means integrating the secular component of these over an orbit and providing storage plus a desaturation path.

## 6. A worked link budget

**Scenario.** S-band downlink from a 3U CubeSat at 500 km to a 3 m ground station, worst-case 10° elevation.

**Slant range.**
```
d = √(R² sin²ε + 2Rh + h²) − R sin ε
  = √(6378² × 0.17365² + 2 × 6378 × 500 + 500²) − 6378 × 0.17365
  = 2802.6 − 1107.5 = 1,695 km
```

**Transmit side.**
| Item | Value |
|---|---|
| Transmit power, 2 W | +3.01 dBW |
| Antenna gain (patch) | +6.0 dBi |
| Line and mismatch loss | −1.0 dB |
| **EIRP** | **+8.01 dBW** |

**Path.**
```
λ = c/f = 3×10⁸ / 2.25×10⁹ = 0.1333 m
FSPL = 20 log₁₀(4πd/λ) = 20 log₁₀(4π × 1.6951×10⁶ / 0.1333) = 164.08 dB
```
| Item | Value |
|---|---|
| Free-space path loss | −164.08 dB |
| Atmospheric + polarisation + pointing | −2.0 dB |

**Receive side.**
```
G_rx = 10 log₁₀(η (πD/λ)²) = 10 log₁₀(0.6 × (π×3/0.1333)²) = 10 log₁₀(2998) = 34.77 dBi
System noise temperature T_s = 150 K  →  21.76 dBK
G/T = 34.77 − 21.76 = 13.01 dB/K
```

**Carrier-to-noise-density.**
```
C/N₀ = EIRP − FSPL − L_other + G/T − 10 log₁₀(k)
     = 8.01 − 164.08 − 2.00 + 13.01 + 228.60
     = 83.55 dB-Hz
```

**Convert to link margin at two data rates.**

| Rate | 10 log₁₀(R) | Eb/N₀ available | Required Eb/N₀ | **Margin** |
|---|---|---|---|---|
| 1 Mbps | 60.0 dB | 23.55 dB | 9.6 dB (uncoded QPSK, BER 10⁻⁵) | **13.95 dB** |
| 10 Mbps | 70.0 dB | 13.55 dB | 9.6 dB (uncoded QPSK) | **3.95 dB** |
| 10 Mbps | 70.0 dB | 13.55 dB | ≈4.5 dB (rate-1/2 convolutional + Viterbi) | **9.05 dB** |

**Reading it.** 1 Mbps is trivially achievable. 10 Mbps uncoded leaves under 4 dB, which is thin — standard practice requires at least 3 dB and preferably 6 dB of margin at the worst-case geometry. Adding rate-1/2 convolutional coding buys back roughly 5 dB of coding gain at the cost of halving the information rate for a given symbol rate, and restores comfortable margin. Modern systems use LDPC or turbo codes and get within 1–2 dB of the Shannon limit. This trade — raise power, raise antenna gain, lower rate, or add coding — is the whole of link design.

## 7. The CubeSat standard

Defined by Cal Poly San Luis Obispo and Stanford in 1999. **1U = 100 × 100 × 113.5 mm**, historically capped at 1.33 kg per U (later revisions permit more; the **CubeSat Design Specification Revision 14.1, February 2022** covers **1U through 12U**). Standard sizes: 1U, 1.5U, 2U, 3U, 6U, 12U, with 16U and larger in some deployer standards. Deployment is from a standardised dispenser — the original **P-POD** and its many commercial descendants (ISIPOD, NanoRacks, Exolaunch EXOpod) — which isolates the launch vehicle from the payload and is what made rideshare practical.

**Why it worked.** The standard did not specify a satellite; it specified an *interface*. That let a supplier ecosystem form: structures, EPS boards, on-board computers, radios, ADCS units, deployable arrays, propulsion modules and ground station networks are all available off the shelf, in interoperable form factors (PC/104 and its successors). A functioning 3U can be assembled from catalogue parts by a small team in a year. The result: over 2,000 CubeSats launched, university programmes worldwide, entire commercial constellations (Planet's Doves are 3U; Spire's Lemurs are 3U), and interplanetary missions — **MarCO-A and MarCO-B**, two 6U CubeSats, relayed InSight's Mars entry telemetry in November 2018, and **CAPSTONE** (12U) flew to a lunar near-rectilinear halo orbit in 2022.

**The limitations are real.** Power is the binding constraint (a 3U with body-mounted cells gets ~5–10 W orbit-average; deployables get to 20–40 W), which caps transmit power and therefore data rate. Pointing to arcsecond level is possible but expensive relative to the platform. Propulsion is available but small. And the reliability statistics are much worse than traditional spacecraft — early-mission failure rates for university CubeSats have historically run around 30–40%, mostly from communications and power faults rather than exotic causes.

## Open questions

- Total ionising dose figures by orbit regime are given as engineering rules of thumb, not from a fetched source; the actual value for any mission comes from a SPENVIS/AE9-AP9 run with the specific shielding geometry.
- CubeSat Design Specification detailed dimensional tolerances were not retrieved from the specification document itself; only the revision number and date (Rev 14.1, February 2022) were confirmed from the Cal Poly page.
- Subsystem mass and power allocation percentages are standard textbook ranges (SMAD lineage), not source-fetched figures.

## Sources

- [NASA Systems Engineering Handbook (NASA/SP-6105)](https://www.nasa.gov/reference/systems-engineering-handbook/) — NASA, accessed 2026-08-25
- [Van Allen radiation belt](https://en.wikipedia.org/wiki/Van_Allen_radiation_belt) — Wikipedia, accessed 2026-08-25
- [CubeSat information](https://www.cubesat.org/cubesatinfo) — Cal Poly CubeSat Program, accessed 2026-08-25
- [International Space Station](https://en.wikipedia.org/wiki/International_Space_Station) — Wikipedia, accessed 2026-08-25
- [James Webb Space Telescope](https://en.wikipedia.org/wiki/James_Webb_Space_Telescope) — Wikipedia, accessed 2026-08-25 (sunshield layers and temperatures)
- [Europa Clipper](https://en.wikipedia.org/wiki/Europa_Clipper) — Wikipedia, accessed 2026-08-25 (solar array area and power at Jupiter)
- [ECSS active standards](https://ecss.nl/standards/active-standards/) — ECSS, accessed 2026-08-25

