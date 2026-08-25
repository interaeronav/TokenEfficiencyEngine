---
id: space.electric-advanced-propulsion
title: Electric and advanced propulsion
domain: 30_space_science_and_propulsion
tags: [electric-propulsion, ion-thruster, hall-thruster, vasimr, nuclear-thermal, solar-sail, tethers, emdrive, propulsion]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
unit_system: SI
related: [space.overview, space.orbital-mechanics, space.chemical-propulsion, space.spacecraft-engineering]
sources:
  - {title: "NEXT (ion thruster)", url: "https://en.wikipedia.org/wiki/NEXT_(ion_thruster)", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Ion thruster", url: "https://en.wikipedia.org/wiki/Ion_thruster", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Hall-effect thruster", url: "https://en.wikipedia.org/wiki/Hall-effect_thruster", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Nuclear thermal rocket", url: "https://en.wikipedia.org/wiki/Nuclear_thermal_rocket", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Solar sail", url: "https://en.wikipedia.org/wiki/Solar_sail", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "VASIMR", url: "https://en.wikipedia.org/wiki/Variable_Specific_Impulse_Magnetoplasma_Rocket", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "RF resonant cavity thruster", url: "https://en.wikipedia.org/wiki/RF_resonant_cavity_thruster", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Breakthrough Starshot", url: "https://en.wikipedia.org/wiki/Breakthrough_Starshot", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Deep Space 1", url: "https://en.wikipedia.org/wiki/Deep_Space_1", publisher: "Wikipedia", accessed: "2026-08-25"}
---

# Electric and advanced propulsion

**Summary.** Chemical propulsion couples the energy source to the propellant: exhaust velocity is capped by the enthalpy of combustion at around 4.5 km/s. Electric propulsion breaks that coupling — an external power source accelerates the propellant, so exhaust velocity is limited by available power and by thruster life, not by chemistry. The result is Isp of 1,000–5,000 s at thrusts of milli-newtons. The entire discipline is governed by one relation, `P_jet = ½ F c`, which says thrust and Isp trade against power; the power system, not the thruster, is almost always the real constraint. This file covers the electric thruster families with real numbers, nuclear thermal and nuclear electric, solar sails and tethers, and an honest assessment of the speculative end — including the EmDrive, which is the field's most useful lesson in how not to do experimental physics.

## Key facts

| Quantity | Value |
|---|---|
| Governing relation | `P_jet = ½ F c = ½ ṁ c²`; `F = 2 η P / (I_sp g₀)` |
| Typical gridded ion | 1–7 kW, 25–250 mN, Isp 2,000–5,000 s, 65–80% efficiency |
| NASA NEXT | 237 mN at 6.9 kW, Isp 4,170 s; 48,000 h test, 17 MN·s total impulse, ≈870 kg xenon |
| NSTAR | 92 mN at 2.3 kW, Isp 1,000–3,000 s (throttled) |
| Dawn total Δv from ion propulsion | 11.5 km/s from 425 kg xenon |
| SPT-100 Hall thruster | 83 mN, ≈1.35 kW class |
| PPS-1350 (SMART-1) | 30–70 mN, Isp 1,100–1,600 s, 0.46–1.19 kW |
| X3 nested-channel Hall (research) | 5.4 N at ≈100 kW, 80 cm diameter, 230 kg |
| QinetiQ T6 (BepiColombo) | 145 mN each, Isp 4,300 s, 4 units, 4,628 W total |
| Solid-core NTR Isp | 850–1,000 s (hydrogen) |
| Solar radiation pressure at 1 AU | 9.08 μPa (perfect reflector), 4.54 μPa (perfect absorber) |
| Hall thrusters in orbit | Thousands — Starlink alone, krypton then argon |

## 1. The power–thrust trade, stated properly

For a thruster of total efficiency η (electrical power in to jet power out):

```
P_jet = ½ F c        →        F = 2 η P_in / c = 2 η P_in / (I_sp g₀)
```

**Worked.** A 5 kW Hall thruster at Isp 1,600 s (c = 15,690 m/s) and η = 0.50:

```
F = 2 × 0.50 × 5000 / 15690 = 0.319 N
```

Doubling Isp to 3,200 s at the same power and efficiency **halves** thrust to 0.16 N. There is no free lunch: for a fixed power supply, thrust ∝ 1/Isp.

**The optimal Isp is finite.** For a mission of duration t with a power system of specific mass α (kg per kW), the propellant mass falls with Isp but the power-plant mass rises. Minimising total mass gives the *characteristic velocity* `v_ch = √(2 η t / α)` and an optimal exhaust velocity of roughly `c_opt ≈ 0.5–0.8 v_ch` depending on the formulation. With solar arrays at α ≈ 10–20 kg/kW and a one-year thrust arc, c_opt lands around 20–35 km/s (Isp 2,000–3,500 s) — which is exactly where flight hardware sits. This is not coincidence; it is the trade being solved.

**The consequence for mission design.** Electric propulsion cannot launch, cannot land, and cannot do a time-critical orbit insertion. What it can do is:
- station-keeping (where the total impulse is large but spread over 15 years),
- GEO orbit raising (see the worked spiral in `01`: 4.594 km/s but only ~10% of launch mass as propellant),
- deep-space cruise with continuous low thrust,
- constellation orbit maintenance and end-of-life disposal.

## 2. Electrothermal thrusters

The simplest class: heat the propellant electrically, expand it through a conventional nozzle. Isp is limited by material temperature, so gains over chemical are modest.

**Resistojet.** A heated element raises propellant enthalpy. Hydrazine resistojets (electrothermal hydrazine thrusters, EHT) raise Isp from ~230 s to ~300 s and flew on hundreds of Intelsat- and Iridium-class satellites. Water resistojets are now used on some CubeSats (Isp ≈150 s but completely benign propellant). Typical: 0.3–1 kW, 100–500 mN, Isp 150–350 s.

**Arcjet.** An electric arc heats the propellant well past wall temperature limits. Hydrazine arcjets reach Isp 500–600 s at 1–2 kW with 100–250 mN thrust, and flew on Lockheed A2100 and Astrium buses for GEO north–south station-keeping through the 1990s and 2000s. Largely displaced by Hall thrusters.

## 3. Gridded ion engines (electrostatic)

Ionise the propellant in a discharge chamber (DC electron bombardment, or RF), then extract and accelerate the ions through a two- or three-grid electrostatic optics system at 1,000–2,000 V. A **neutraliser cathode** injects electrons downstream to keep the spacecraft from charging.

Characteristic performance: highest Isp of any flight-proven EP, best efficiency, lowest thrust density (limited by the Child–Langmuir space-charge law, which caps extractable current density for a given grid gap and voltage).

| Thruster | Heritage | Power | Thrust | Isp | Note |
|---|---|---|---|---|---|
| **NSTAR** | Deep Space 1 (1998), Dawn (2007) | 0.5–2.3 kW | up to 92 mN | 1,000–3,000 s throttled | 82 kg Xe on DS1; Dawn achieved **11.5 km/s Δv from 425 kg Xe** |
| **NEXT / NEXT-C** | DART (Nov 2021) | 0.5–6.9 kW | up to 237 mN | 1,320 s (min) – 4,170 s (max) | 48,000 h ground test, 17 MN·s total impulse, ≈870 kg Xe |
| **RIT-10 / RIT-22** | Artemis (ESA), AlphaBus | 0.5–5 kW class | 15–150 mN class | 3,000–4,500 s | RF ionisation (no discharge cathode) — Ariane Group |
| **T5** | GOCE (2009–2013) | ≈0.6 kW | 1–20 mN | ≈3,200 s | Drag-free flight at 255 km, throttled continuously |
| **T6** | BepiColombo (2018) | 4,628 W total | 145 mN each, 290 mN max combined | 4,300 s | Four units, 1,400 kg xenon on the Mercury Transfer Module |
| **μ10** | Hayabusa (2003), Hayabusa2 (2014) | ≈350 W each | ≈8 mN each | ≈3,000 s | Microwave discharge, no cathodes — exceptional longevity |

**Life limiters** are grid erosion by charge-exchange ions (the accelerator grid slowly sputters, eventually producing "pits and grooves" and structural failure) and cathode wear. NEXT's 48,000-hour demonstration is the benchmark; μ10's microwave discharge eliminates hollow cathodes entirely and let Hayabusa2 run for tens of thousands of hours across a nine-year mission.

**Propellant.** Xenon has dominated: high atomic mass (131.3 u, so high thrust per ion), easily ionised, inert, storable as a supercritical fluid at ~100 bar. It is also scarce and expensive (roughly US$1,000–3,000/kg, price highly volatile and driven by semiconductor demand). Krypton is cheaper and lighter (lower thrust, higher Isp for the same voltage, somewhat lower efficiency); **argon** is cheaper still and is what Starlink V2 mini uses. Iodine has been flown (ThrustMe NPT30-I2 on a Chinese CubeSat, 2020) and is storable as a solid but is corrosive.

## 4. Hall-effect thrusters

The workhorse. A radial magnetic field traps electrons in an azimuthal E×B drift inside an annular channel; the trapped electron cloud ionises incoming propellant, and the axial electric field accelerates the ions out. Because the plasma is quasi-neutral, there is no space-charge limit — thrust density is roughly an order of magnitude higher than a gridded ion engine, at somewhat lower Isp (1,000–2,500 s typical) and 45–60% efficiency.

Two sub-families: **SPT** (stationary plasma thruster, dielectric BN-SiO₂ channel walls, Soviet/Russian lineage from Fakel) and **TAL** (thruster with anode layer, metallic walls, shorter channel).

| Thruster | Origin | Power | Thrust | Isp | Flight use |
|---|---|---|---|---|---|
| **SPT-100** | Fakel (RU) | ≈1.35 kW | 83 mN | ≈1,600 s | The most-flown EP device in history; GEO NSSK on many Western and Russian buses |
| **PPS-1350** | Safran (FR) | 0.46–1.19 kW | 30–70 mN | 1,100–1,600 s | **SMART-1** — reached lunar orbit on 82 kg of xenon (launched 27 Sept 2003) |
| **PPS-5000** | Safran (FR) | ≈5 kW | ≈300 mN class **[needs-verification]** | ≈1,800 s **[needs-verification]** | All-electric GEO buses (Eurostar Neo, Spacebus Neo) |
| **BPT-4000 / XR-5** | Aerojet (US) | 4.5 kW | ≈270 mN **[needs-verification]** | ≈2,000 s **[needs-verification]** | AEHF (Aug 2010) — noted as the highest-power Hall thruster flown at the time |
| **BHT-600 / BHT-8000** | Busek (US) | 0.6 / 8 kW | — **[needs-verification]** | — | Smallsat and higher-power US programmes |
| **X3** | U. Michigan / AFRL / NASA (research) | ≈100 kW | **5.4 N demonstrated** | — | Three nested channels, 80 cm diameter, 230 kg — the high-power record holder |
| **Starlink thruster** | SpaceX (in-house) | — | — | — | Krypton on v1.x, **argon** on V2 mini; produced by the thousand, the largest EP production run ever |

**AEHF-1 is the field's most dramatic demonstration.** In 2010 its bipropellant apogee engine failed after launch. Over 14 months the spacecraft raised itself from a stranded transfer orbit to GEO using its BPT-4000 Hall thrusters plus small reaction control thrusters, saving a US$1.7 billion satellite. Low thrust is not the same as no capability.

## 5. Electrospray, FEEP and colloid thrusters

At the very small end, extract charged droplets or ions directly from a liquid surface by field emission — no discharge chamber, no neutraliser plasma, and thrust resolution down to sub-micronewton.

- **FEEP (field-emission electric propulsion):** liquid metal (indium or caesium) wetted emitter, ions extracted at 5–10 kV. Isp 4,000–8,000 s, thrust 1 μN–1 mN.
- **Colloid / electrospray:** ionic liquids (EMI-BF4, EMI-Im) extracted from arrays of microfabricated emitter tips. Isp 500–3,000 s.

**LISA Pathfinder** (launched 3 December 2015) flew both — Busek colloid thrusters and ESA's cold-gas micropropulsion — and demonstrated drag-free control at the 10⁻¹⁵ m/s²/√Hz level, the enabling technology for LISA. Accion Systems (TILE) and Enpulsion (IFM Nano, indium FEEP) sell electrospray units for CubeSats today.

## 6. Magnetoplasmadynamic and VASIMR

**MPD thrusters** pass a high current (kA) through a plasma; the self-induced magnetic field produces a j×B Lorentz body force. Thrust density is very high and Isp reaches 2,000–7,000 s — but efficient operation needs hundreds of kilowatts to megawatts, which no spacecraft has. Japan's Space Flyer Unit flew a pulsed MPD experiment in 1995; nothing operational has followed. The technology is waiting for a power source.

**VASIMR** (Variable Specific Impulse Magnetoplasma Rocket, Ad Astra Rocket Company, Franklin Chang Díaz) uses a helicon RF source to ionise argon and an ion cyclotron resonance heating stage to add energy, with a magnetic nozzle. Its selling point is variable Isp at constant power — high thrust/low Isp when you want to move quickly, the reverse when you want efficiency.

**The honest numbers.** VX-200 required **200 kW electrical to produce 5 N** — i.e. 40 kW/N — against NASA's NEXT at **24 kW/N**. VASIMR is *less* power-efficient per newton than a gridded ion engine. Reported thruster efficiency relative to RF power input exceeded 70% by 2013 after more than 10,000 firings on argon, but overall system efficiency (including RF generation and, critically, the superconducting magnet's cryocooler) lags. Optimal efficiency was measured at 50 km/s exhaust velocity (Isp ≈5,000 s). Long-duration runs of 28 hours and 88 hours were achieved in July 2021; the planned 100 kW, 100-hour demonstration under the NASA NextSTEP award (US$10 M, March 2015) has repeatedly slipped.

Robert Zubrin's critique is the standard one and it is not really about the thruster: a VASIMR-powered fast Mars transit needs megawatts, and rejecting the waste heat from a megawatt-class power plant in space requires radiators of implausible area and mass. The thruster is not the hard part; the power and thermal system is. That critique applies to every high-power EP concept, not just VASIMR.

## 7. Nuclear thermal propulsion

Heat hydrogen in a fission reactor and expand it through a nozzle. Because the working fluid is pure hydrogen (molar mass 2 rather than 13–23 for combustion products) and the temperature is set by materials rather than chemistry, Isp roughly doubles chemical performance at comparable thrust.

**Solid-core Isp: 850–1,000 s.** Liquid-core concepts project 1,300–1,500 s; gas-core (a fissioning plasma contained by vortex flow or a quartz bulb) projects 3,000–5,000 s and has never been built.

**The Rover/NERVA programme (1955–1973)** is the entire flight-adjacent database:

| Engine | Date | Reactor power | Thrust | Note |
|---|---|---|---|---|
| Phoebus 1A | June 1965 | 1,090 MW | — | 2,370 K exhaust |
| NRX/XE | March 1968 | 1,100 MW | 334 kN | 28 firings; several tests ended only when the stand ran out of hydrogen |
| Phoebus 2A | June 1968 | 4,000 MW | — | The most powerful nuclear reactor built at the time |
| Pewee | 1968–69 | 500 MW | — | Tested zirconium carbide coatings; the basis for current NASA designs |

The programme was cancelled in 1973 having never flown. Its hardware demonstrated restart, throttling and hours of accumulated run time — the physics is settled; the obstacles are fuel-element erosion (hot hydrogen attacks graphite matrices), ground testing without releasing fission products, highly-enriched-uranium versus high-assay low-enriched-uranium (HALEU) fuel policy, and cost.

**DRACO** (Demonstration Rocket for Agile Cislunar Operations), DARPA with NASA: US$499 M contract awarded July 2023, Lockheed Martin for the spacecraft with Blue Origin, BWX Technologies for the reactor and General Atomics on engine design, targeting an in-space demonstration. It was **cancelled in 2025**, the stated reasoning being falling launch costs eroding the case, plus budget pressure. The US Senate subsequently directed at least US$110 M toward nuclear propulsion research, so the field persists at study level. This is the fourth or fifth time nuclear thermal propulsion has been funded and cancelled since 1973; the pattern is the strongest single fact about it.

**Nuclear electric propulsion (NEP)** is the other branch: a reactor drives a generator that drives electric thrusters. It decouples thrust from reactor thermal limits and gives Isp of 3,000–10,000 s, but needs the same enormous radiators as any megawatt-class EP system. The Soviet **BES-5/Buk** and **TOPAZ** reactors flew on RORSAT ocean surveillance satellites (some 30+ units, 1970–1988) at a few kilowatts electrical; the US flew SNAP-10A once in 1965. NASA's Kilopower/KRUSTY project demonstrated a 1 kWe fission surface power unit in ground testing (2018) and is aimed at surface power rather than propulsion. Nothing at the 100 kWe–1 MWe scale relevant to fast interplanetary transfer exists.

**Radioisotope power** is not propulsion but belongs here for contrast: an MMRTG produces ≈110 W electrical at beginning of life from ≈4.8 kg of plutonium-238 dioxide, declining ~1.6%/year. That powers Curiosity, Perseverance and (with 70 W desired) Dragonfly. Pu-238 supply is the binding constraint on outer-planet exploration.

## 8. Solar sails

No propellant at all. Solar radiation pressure at 1 AU is **9.08 μN/m² (9.08 μPa) for a perfect reflector normal to the Sun**, or 4.54 μN/m² for a perfect absorber; with realistic optical properties, ≈8.17 μN/m². Pressure falls as 1/r².

The figure of merit is **characteristic acceleration** — acceleration at 1 AU with the sail normal to the Sun. A useful sail needs ≈0.1–1 mm/s²; that requires an areal density (sail plus spacecraft, kg per m² of sail) of roughly 10 g/m² or better, which is why sails are made of 2–7.5 μm aluminised polyimide (Kapton, CP1) or Mylar with no supporting structure beyond deployable booms.

**Flight record:**

| Mission | Launch | Sail | Result |
|---|---|---|---|
| **IKAROS** (JAXA) | 21 May 2010 | 14 × 14 m square, 196 m², 7.5 μm aluminised polyimide, ≈10 g/m² | First demonstration of solar sail propulsion; **≈100 m/s velocity change over six months**. Attitude controlled by eight embedded LCD panels that switch reflectivity — no moving parts |
| **NanoSail-D2** (NASA) | Nov 2010 | 10 m² | Deployment and de-orbit demonstration |
| **LightSail 2** (The Planetary Society) | 25 June 2019 | 32 m², 3U CubeSat, deployed 23 July 2019 | Demonstrated measurable orbit raising by sail thrust; re-entered **17 November 2022** |
| **NEA Scout** (NASA) | Nov 2022 (Artemis I) | 83 m² aluminised polyimide | **Lost** — no communications established after deployment from SLS |
| **ACS3** (NASA) | April 2024 | 80 m², composite booms | Boom deployment technology demonstration |

Solar sails are real, flown, and tiny. Their genuine niches are drag-free station-keeping at sub-L1 "statite" positions (a sail can hold a non-Keplerian equilibrium sunward of L1, proposed for solar storm early warning), slow but propellant-free orbit changes for smallsats, and de-orbit devices. They are not a fast route anywhere in the inner solar system unless you get very close to the Sun first, where the 1/r² gain is large.

**Laser sails** substitute a directed beam for sunlight and are the only concept in this file with a plausible path to relativistic velocity — see §10.

## 9. Tethers

**Electrodynamic tethers** run a conducting cable through the geomagnetic field. Motion induces an EMF; driving current against it produces a `IL × B` force. With current flowing one way the tether de-orbits (drag); reversed and powered, it boosts. No propellant, but it works only where there is both a magnetic field and enough plasma to close the circuit — LEO and Jupiter, essentially.

Flight history is mixed: **TSS-1R** (Shuttle, 1996) generated 3,500 V and 480 mA before the tether burned through at 19.7 km deployed; **PMG** (1993) demonstrated bidirectional current; **YES2** (2007) deployed 31.7 km. De-orbit tethers (Tethers Unlimited Terminator Tape) are commercially available and have flown on smallsats.

**Momentum-exchange tethers** (rotating "bolo" architectures, HASTOL-type concepts) transfer angular momentum from a spinning tether to a payload. Analytically attractive, operationally daunting: the rendezvous with a rotating tether tip has a timing tolerance of milliseconds, and the tether itself must survive the debris environment while being long and thin — the worst possible geometry for collision probability. No orbital momentum-exchange tether has flown.

## 10. The speculative end, honestly assessed

**Fusion propulsion.** If you can build a net-energy fusion reactor, direct fusion drive concepts (Princeton's PFRD, magnetic-nozzle designs) project Isp of 10,000–100,000 s at usable thrust. The blocker is not the nozzle; it is that terrestrial fusion has not yet delivered engineering break-even in a device you could put on a spacecraft. Treat all Isp numbers as conditional on a technology that does not exist.

**Antimatter.** Energy density 9 × 10¹⁶ J/kg — nine orders of magnitude above chemical. Current global production is on the order of nanograms per year at a cost that works out to roughly US$10¹²–10¹⁵ per gram, and storage requires Penning traps. Antimatter-catalysed microfission (using a few micrograms to trigger a larger fission/fusion pulse) is the only variant with a non-absurd mass budget, and it is a paper study. Not a near-term technology in any meaningful sense.

**Breakthrough Starshot.** Announced 12 April 2016 by Yuri Milner, Stephen Hawking and Mark Zuckerberg with US$100 M in initial funding. Concept: gram-scale "StarChip" probes on 4 × 4 m graphene-composite sails, accelerated by a ground-based phased array of 10 kW lasers combining to **up to 100 GW** through ≈3 km of coherent optics, reaching **0.15–0.20 c** and crossing to Alpha Centauri in 20–30 years plus ~4 years of light time for the return signal. Estimated final cost US$5–10 billion; projected launch ~2036. Actual spend to September 2025: **≈US$4.5 million**, and the project was **on hold indefinitely** as of that date. The physics is sound — laser sails obey momentum conservation and the acceleration numbers work — but the engineering requires "at least a dozen off-the-shelf technologies to improve by orders of magnitude," and the sail must survive ~10,000 g acceleration, interstellar dust impacts at 0.2 c, and atmospheric turbulence in the beam. It is a legitimate research programme with an implausible schedule, not a scam.

**The EmDrive — a case study in bad science.** Proposed by Roger Shawyer in 2001: microwaves in an asymmetric resonant cavity allegedly produce thrust with no propellant. This is a claimed **reactionless drive**, which violates conservation of momentum — a symmetry-derived conservation law that has survived every test in the history of physics and that follows from the translational invariance of space (Noether's theorem). A working EmDrive would not be a new engine; it would be a new physics.

The sequence is instructive:

1. Small positive results reported by several groups, always at the edge of measurement noise.
2. NASA's Eagleworks laboratory published in 2016 a claimed thrust-to-power of **1.2 ± 0.1 mN/kW** at 40–80 W in vacuum, with the authors themselves listing many potential error sources and a small dataset.
3. Enormous press coverage, essentially none of it noting the size of the claimed effect relative to the apparatus's known systematic errors.
4. Martin Tajmar's group at TU Dresden built a far more careful apparatus and in 2021 **reproduced the apparent thrust and then made it disappear** by properly accounting for thermal expansion warping the torsion balance and for magnetic interaction between the power cables and the Earth's field. Their conclusion: *"Our measurements refute all EmDrive claims by at least 3 orders of magnitude."*

The lessons transfer to any extraordinary propulsion claim: (a) if your signal is the same order as your known systematics, you have not measured anything; (b) thermal drift on a torsion balance in vacuum is the single most common false positive in micro-thrust metrology; (c) a claim that violates a conservation law needs evidence proportional to the century of evidence supporting that law; (d) the correct response to an anomaly is a better experiment, not a press release. The field's current scientific status: pseudoscience.

## Open questions

- PPS-5000, BHT-600 and BHT-8000 thrust and Isp figures are vendor-published but were not retrievable from the sources fetched; marked `needs-verification`.
- BPT-4000/XR-5 thrust and Isp likewise.
- Post-2025 status of Ad Astra's NASA NextSTEP milestones was not verified in this pass.
- Whether any successor to DRACO has been funded beyond study level as of mid-2026 is unverified.

## Sources

- [NEXT (ion thruster)](https://en.wikipedia.org/wiki/NEXT_(ion_thruster)) — Wikipedia, accessed 2026-08-25
- [Ion thruster](https://en.wikipedia.org/wiki/Ion_thruster) — Wikipedia, accessed 2026-08-25
- [Hall-effect thruster](https://en.wikipedia.org/wiki/Hall-effect_thruster) — Wikipedia, accessed 2026-08-25
- [Nuclear thermal rocket](https://en.wikipedia.org/wiki/Nuclear_thermal_rocket) — Wikipedia, accessed 2026-08-25
- [Solar sail](https://en.wikipedia.org/wiki/Solar_sail) — Wikipedia, accessed 2026-08-25
- [Variable Specific Impulse Magnetoplasma Rocket](https://en.wikipedia.org/wiki/Variable_Specific_Impulse_Magnetoplasma_Rocket) — Wikipedia, accessed 2026-08-25
- [RF resonant cavity thruster](https://en.wikipedia.org/wiki/RF_resonant_cavity_thruster) — Wikipedia, accessed 2026-08-25
- [Breakthrough Starshot](https://en.wikipedia.org/wiki/Breakthrough_Starshot) — Wikipedia, accessed 2026-08-25
- [Deep Space 1](https://en.wikipedia.org/wiki/Deep_Space_1) — Wikipedia, accessed 2026-08-25
- [BepiColombo](https://en.wikipedia.org/wiki/BepiColombo) — Wikipedia, accessed 2026-08-25 (T6 figures)

