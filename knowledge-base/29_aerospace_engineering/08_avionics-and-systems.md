---
id: aerospace.avionics
title: Avionics and aircraft systems
domain: 29_aerospace_engineering
tags: [avionics, fly-by-wire, normal-law, alternate-law, direct-law, hydraulics, electrical, more-electric-aircraft, fuel-system, ecs, pressurisation, ice-protection, landing-gear, apu, ima, arinc-429, arinc-664, afdx, mil-std-1553, flight-deck, fms, autoflight, tcas, egpws, ads-b, cpdlc]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Avionics Full-Duplex Switched Ethernet (ARINC 664 Part 7 / AFDX)", url: "https://en.wikipedia.org/wiki/Avionics_Full-Duplex_Switched_Ethernet", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Fly-by-wire", url: "https://en.wikipedia.org/wiki/Fly-by-wire", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "14 CFR §25.1309", url: "https://www.ecfr.gov/current/title-14/section-25.1309", publisher: "eCFR", accessed: 2026-08-25}
  - {title: "Boeing 787 Dreamliner", url: "https://en.wikipedia.org/wiki/Boeing_787_Dreamliner", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "DO-178C", url: "https://en.wikipedia.org/wiki/DO-178C", publisher: "Wikipedia", accessed: 2026-08-25}
related: [aerospace.certification, aerospace.design_process, aerospace.overview]
unit_system: SI
---

# Avionics and aircraft systems

**Summary.** A modern airliner is a distributed real-time computer network that happens to have wings. The systems half of aerospace engineering is about power (hydraulic, electrical, pneumatic), environment (pressurisation, temperature, ice), and information (sensing, computing, displaying, communicating) — all architected so that no single failure and no plausible combination of failures produces a catastrophic outcome. The two design philosophies that dominate the field, Airbus's protected envelope and Boeing's overridable augmentation, are not arbitrary: each is a coherent answer to the question of where final authority sits, and each has a certification argument behind it.

## Key facts

| Item | Value |
|---|---|
| First production fly-by-wire aircraft | **Concorde** (analogue) |
| First airliner with full digital FBW | **Airbus A320**, in service **1988** |
| Boeing's first FBW airliner | **777**, **1994** |
| Hydraulic system pressure, conventional | **3,000 psi (207 bar)** |
| Hydraulic system pressure, A380/A350/787 (partial) | **5,000 psi (345 bar)** |
| Hydraulic fluid | Phosphate ester, **Skydrol / HyJet** (fire-resistant, aggressive to paint and skin) |
| Conventional electrical | **115 V AC 400 Hz, 3-phase** + 28 V DC |
| Boeing 787 electrical | **±270 V DC, 235 V AC variable frequency**, ~1.45 MW total generation |
| Cabin altitude, conventional | ≤ 8,000 ft at max operating altitude (25.841) |
| Cabin altitude, 787/A350 | ≈ 6,000 ft, at ~8.6–9.4 psi differential, permitted by composite fuselage |
| ARINC 429 | **100 kbit/s** high speed, **12.5 kbit/s** low speed; unidirectional, one transmitter to ≤ 20 receivers (1977) |
| ARINC 629 | 2 Mbit/s bidirectional bus, Boeing 777 |
| MIL-STD-1553B | 1 Mbit/s, command/response, bus controller + remote terminals |
| **ARINC 664 Part 7 / AFDX** | **100 Mbit/s**, switched Ethernet, **virtual links** with a **Bandwidth Allocation Gap (BAG)**, **dual redundant networks**; ~**1,000× faster than ARINC 429** |
| AFDX aircraft | **A380, A350, A400M, A220, Boeing 787**, SSJ100, ATR 42/72, MC-21, Global Express, COMAC types |

> ⚠️ Everything in this file is described at engineering level. Operationally, the authoritative documents are the aircraft's FCOM, QRH, MEL and the AFM. Where this file and the FCOM disagree, the FCOM is right.

## 1. Flight controls

### The three generations

**Mechanical**: cables, pushrods, bellcranks and pulleys directly connecting the control column to the surface. Aerodynamic hinge moments are felt directly, so balance tabs, servo tabs, horn balances and mass balances are used to make forces manageable and flutter-free. Limits at large aircraft size and speed: hinge moments become unmanageable and cable stretch/friction unacceptable.

**Hydro-mechanical (powered controls with artificial feel)**: cables signal a hydraulic servo actuator that moves the surface. Because the pilot no longer feels the surface load, an **artificial feel unit** (usually q-feel, sensing dynamic pressure) generates a force gradient, and a **trim** system re-zeros it. This is the 707/727/737/747 architecture and is still in the 737 today. It requires **manual reversion** provisions: on the 737, loss of both hydraulic systems leaves cable-driven ailerons and elevator with very heavy forces and manual stabiliser trim.

**Fly-by-wire (FBW)**: the pilot's inceptor is a transducer, the computers compute a **command**, and the actuators execute it. The pilot commands a *response variable*, not a surface position:

| Aircraft | Pitch command in normal operation | Roll command |
|---|---|---|
| Airbus A320/A330/A350 | **Load factor demand (C*)** — stick free = 1 g flight path hold, auto-trim | **Roll rate demand** with bank angle hold to 33° |
| Boeing 777/787 | **C*U** — load factor blended with speed stability, so speed change produces a force cue | Roll rate demand |

The certification consequence is huge: the aircraft's handling qualities are now *software*, and that software is DAL A. The DO-178C Level A objective count (**71 objectives, 67 with independence**) is precisely the price of putting handling qualities in code.

### Airbus control laws

**Normal law** — full protections, available with the expected set of computers and sensors healthy:
- **Load factor limit**: +2.5 g / −1.0 g clean; +2.0 g / 0 g with flaps.
- **Pitch attitude protection**: nominally 30° nose-up (reducing to 25° at low speed), 15° nose-down.
- **Bank angle protection**: to 67°, with spiral stability returning the aircraft to 33° if the stick is released.
- **High angle-of-attack protection**: α-prot, α-floor (autothrust TOGA), α-max — the aircraft cannot be stalled with the sidestick full aft; it flies at α-max.
- **High-speed protection**: nose-up demand as V_MO/M_MO is exceeded.

Under normal law "the flight-envelope control system always retain[s] ultimate flight control" and prevents pilots from violating performance limits — the pilot must degrade the law to exceed them.

**Alternate law** — triggered by multiple failures (e.g. loss of two air data references, certain computer or hydraulic combinations). Load factor demand in pitch is retained; **protections are lost or reduced** (typically retaining load factor protection, losing high-α and bank angle protection, with low- and high-speed *stability* replacing the hard protections). Stall warning becomes relevant again, which is exactly the state AF447 was in.

**Direct law** — stick-to-surface proportional, no auto-trim, manual pitch trim required; entered with gear down in certain failure states, or on further degradation.

**Mechanical/backup** — the A320 retains mechanical pitch trim and rudder as ultimate backup. Later designs replaced this: the **A380 has a three-axis Backup Control Module (BCM) using purely electrical power, eliminating hydraulic dependency**, and the A350 similarly has electrical backup. The **787 incorporates electrically powered backup controls that function even during total hydraulic loss** — a capability shared with the A350.

### Boeing's philosophy

Boeing's FBW is deliberately **overridable**: on the **777 and 787 the pilot can completely override the computerised flight control system and operate outside the normal flight envelope**. The protections exist and provide strong tactile and aural cues — bank angle, overspeed, stall (with stick shaker), and a rising force gradient — but they are *soft*: sufficient force defeats them. Boeing also retains a **connected control column and wheel with force feedback and coupled inceptors**, so each pilot sees what the other is doing; Airbus's sidesticks are not mechanically coupled and their inputs are algebraically summed, with a takeover priority button.

Neither philosophy is demonstrably safer. The accident record contains cases attributable to each: hard protections have been implicated where the aircraft's model of the world was wrong (blocked pitot tubes, erroneous AoA), and soft protections have been implicated where the crew did not act on a cue. What matters engineering-wise is that both are coherent and that the crew's mental model matches the design.

### The MCAS counter-example
MCAS was neither: it was an *augmentation* function with hard authority, on a non-FBW aeroplane, without redundant sensing and without disclosure. Its failure is treated fully in `07_certification-and-airworthiness.md`.

## 2. Hydraulics

Function: high force density actuation for flight controls, landing gear, brakes, steering, thrust reversers, and cargo doors.

- **Pressure**: 3,000 psi conventionally; **5,000 psi** on the A380, A350 and parts of the 787 — higher pressure means smaller actuators and smaller lines, hence weight saving, at the cost of tighter sealing and fatigue design.
- **Fluid**: phosphate-ester (Skydrol/HyJet), chosen for fire resistance; it attacks polyurethane paint, many elastomers and human skin.
- **Redundancy**: three independent systems on a large transport (Airbus Green/Blue/Yellow; Boeing Left/Centre/Right), each with different power sources — engine-driven pumps, electric motor pumps, air-driven pumps (**PTU** — power transfer unit, transferring power hydraulically without transferring fluid), and the **Ram Air Turbine (RAT)** for the total-loss case.
- **Separation**: routing is physically separated so that a rotor burst, tyre burst or fire cannot take out more than one system — this is the **Zonal Safety Analysis** and **Particular Risks Analysis** of ARP4761A made concrete. United 232 (Sioux City, 1989) is the case that proves the rule, where all three systems ran close together through the tail.
- **The trend** is away from hydraulics: **EHA (electro-hydrostatic actuator)** — a self-contained actuator with its own electric motor and pump — and **EBHA (electrical backup hydraulic actuator)** appear on the A380, A350 and 787, reducing hydraulic system count and providing dissimilar backup.

## 3. Electrical systems and the more-electric aircraft

Conventional architecture: **115 V AC 400 Hz three-phase** from an **IDG (integrated drive generator)** — a constant-speed drive plus generator — on each engine, plus APU and external power, with TRUs producing 28 V DC and batteries for essential loads and for the emergency case.

**Variable-frequency generation** (A380, A350, 787) removes the constant-speed drive — the heaviest, least reliable part — and lets frequency vary with engine speed (roughly 360–800 Hz), with power electronics conditioning whatever needs fixed frequency.

**The Boeing 787's bleedless architecture** is the most radical step taken to date. It removes engine bleed air entirely (except for engine cowl anti-ice) and replaces it with electrical power:
- **Cabin pressurisation** by electric compressors rather than engine bleed.
- **Wing ice protection** by electrothermal mats rather than hot bleed air.
- **Engine start** by the starter/generators running as motors.
- **Hydraulic pumps** electrically driven.
- Total generation of roughly **1.45 MW** at **235 V AC variable frequency** with **±270 V DC** distribution.

The claimed benefit is a more efficient use of engine power (bleed extraction is thermodynamically wasteful, especially at low power) plus better ECS control. The costs are the weight of the power electronics, a large thermal-management problem (power electronics reject heat), and arc-fault risk at 270 V DC — which is why the 787 uses solid-state power distribution with sophisticated protection, and why its P100/P200 panel fire in 2012 was taken so seriously.

The **A350's** approach is deliberately intermediate: variable-frequency generation and electrical backup actuation, but retaining bleed air for ECS and wing anti-ice. That is a reasonable summary of Airbus's general posture — adopt the technology, not the ideology.

## 4. Fuel systems

Functions: store, feed, transfer, vent, measure, and manage CG. Structure:
- Tanks are integral to the wing box (wet wing) plus a centre tank, and on some types a trim tank in the horizontal stabiliser (A330/A340/A350/A380, and Concorde where it was the primary transonic trim device).
- **Feed** by boost pumps with suction-feed capability as backup.
- **Transfer and CG management**: aft CG within limits reduces trim drag; the A340/A350 trim tank actively manages this in cruise and returns fuel forward for approach.
- **Fuel measurement**: capacitance probes plus densitometers, with a **fuel quantity indication system (FQIS)** that must be intrinsically safe — the TWA 800 centre-tank explosion (1996) traced to FQIS wiring energy in a flammable ullage led to **25.981 tank flammability** rules and to **nitrogen-generating inerting systems (NGS/FTIS)** on modern aircraft, which flood the ullage with < 12 % oxygen air from a hollow-fibre air separation module.
- **Fuel temperature**: Jet A-1 freeze point −47 °C; long ultra-high-latitude cruise can approach it, which is why fuel temperature is a monitored parameter.
- **Water and microbial contamination**: sumping, biocide treatment; ice formation from entrained water was the mechanism in the BA038 777 accident at Heathrow (2008), leading to a redesigned fuel–oil heat exchanger.

## 5. Environmental control and pressurisation

**Pressurisation**. Cabin altitude is controlled by modulating outflow valves against a supply of conditioned air. 25.841 limits cabin altitude to 8,000 ft at maximum operating altitude in normal operation, and 25.841(a) sets the requirement following any reasonably probable failure. Composite fuselages tolerate a higher differential for the same fatigue life, which is why the **787 and A350 hold roughly a 6,000 ft cabin** and higher humidity (about 15–20 % instead of 5–10 %) — a genuine physiological improvement on ultra-long-haul that a Qatar Airways A350 crew sees directly in fatigue outcomes.

**Air conditioning**. The classical **air cycle machine (ACM, "pack")** is a reverse Brayton refrigerator: bleed air is pre-cooled, compressed, cooled again in a heat exchanger against ram air, then expanded through a turbine (extracting work to drive the compressor) which drops its temperature dramatically. A **water separator** and, in modern high-pressure water separation packs, a condenser prevent icing. Mix manifold blending with recirculated cabin air (through HEPA filters, typically 50 % recirculated) gives the delivered temperature per zone.

**Ozone and contamination**: catalytic ozone converters above about FL270; the "**bleed air/fume event**" question — engine oil (containing tricresyl phosphate) leaking past bearing seals into the bleed supply — is a live occupational health controversy and is one of the arguments made for the 787's bleedless architecture.

## 6. Ice protection

| Method | Where |
|---|---|
| **Hot bleed air (thermal anti-ice)** | Wing leading edge slats, engine cowl inlet lips — evaporative or running-wet |
| **Electrothermal mats** | **787 wing** (bleedless), propeller blades, windshields, probes |
| **Pneumatic de-ice boots** | Turboprops and GA — inflate to crack accreted ice; require the crew to allow a build-up |
| **Electro-mechanical expulsion (EMEDS)** | Emerging; low power |
| **Fluid (TKS)** | Glycol weeping through porous panels; GA and some bizjets |

Certification is via **25.1419 and Appendix C** (the classical continuous maximum and intermittent maximum icing envelopes) and, since 2014, **Appendix O** for **supercooled large droplets (SLD)** — freezing drizzle and freezing rain — added after the ATR-72 Roselawn accident (1994) demonstrated that ridge ice aft of the protected area could produce aileron hinge-moment reversal. Appendix D covers ice-crystal/mixed-phase conditions relevant to engine core icing at high altitude near convection, the mechanism behind a series of high-altitude engine rollbacks and probe blockages.

## 7. Landing gear

Function: absorb landing energy, support the aircraft, steer, brake, and retract into minimum volume. The **oleo-pneumatic shock strut** absorbs energy with an efficiency of about 0.8 — a compressed nitrogen spring plus an orifice-metered oil damper — versus about 0.5 for a simple steel spring, which is why nothing else is used on transports.

Design drivers: sink rate (10 ft/s at MLW, 6 ft/s at MTOW, per 25.473), tip-back and overturn angles, pavement loading (which drives wheel and bogie count — see the 777's six-wheel trucks and the A380's 20-wheel, 22-including-nose arrangement), rotation clearance, and stowage volume. Materials: **300M** or Aermet steel forgings, or **Ti-10-2-3** for large components; carbon–carbon brakes with a heat sink sized by the **rejected take-off (RTO) energy** case — a certification test in which a fully loaded aircraft aborts at V1 with worn brakes and no reverse, and must then sit for five minutes without a fire.

Brake control is now **brake-by-wire** with electronic antiskid; the **787 uses electric brake actuation**, removing hydraulics from the gear entirely.

## 8. APU

A small gas turbine (Honeywell 131-9A/B, HGT1700; P&W APS5000 on the 787) providing electrical power and, on bleed aircraft, pneumatic air for engine start and ground air conditioning. Certification under **CS-APU**; ETOPS aircraft require an APU that can be started and will run reliably at cruise altitude, which is a demanding requirement (relight envelope, oil system at altitude). On the 787 the APU is electric-only, producing 2 × 225 kVA.

## 9. Avionics architecture: federated vs IMA

**Federated**: one function, one box, one supplier, own processor and I/O; boxes exchange data over ARINC 429. Simple to certify in isolation, strong fault containment, but heavy, expensive, and duplicative (dozens of LRUs each with its own power supply, chassis and processor).

**Integrated Modular Avionics (IMA)**: a shared computing platform of standard modules hosting many applications, with **robust partitioning** in space (memory protection) and time (fixed cyclic scheduling) so that a fault in one application cannot affect another. The partitioning operating system conforms to **ARINC 653**, and the platform certification approach is **DO-297**. Benefits: large weight and volume savings, easier upgrade, common spares. Costs: the integrator carries far more responsibility, partitioning must be proven, and change impact analysis becomes a system-wide activity. Implementations: A380/A350 **IMA (CPIOM modules)**, Boeing 787 **Common Core System (CCS)** with GPMs and remote data concentrators.

### Data buses

| Bus | Rate | Topology | Use |
|---|---|---|---|
| **ARINC 429** (1977) | **100 kbit/s** high, **12.5 kbit/s** low | Unidirectional, one transmitter → up to 20 receivers, twisted shielded pair, 32-bit words with label/SDI/data/SSM/parity | The workhorse of federated avionics; still ubiquitous |
| **ARINC 629** | 2 Mbit/s | Bidirectional multi-transmitter, CSMA/CA with a distributed protocol | Boeing 777 |
| **MIL-STD-1553B** | 1 Mbit/s | Command/response, bus controller + up to 31 remote terminals, dual redundant | Military aircraft and spacecraft; extremely mature |
| **ARINC 664 Part 7 (AFDX)** | **100 Mbit/s** | Switched full-duplex Ethernet with **virtual links** — unidirectional logical paths from one source end-system to all destinations — each policed by a **Bandwidth Allocation Gap (BAG)** guaranteeing maximum rate; **dual redundant networks** with frame-level redundancy management; determinism from a frozen VL configuration with bounded latency and jitter | **A380, A350, A400M, A220, Boeing 787**, SSJ100, ATR 42/72, MC-21, Global Express, COMAC aircraft. Roughly **1,000× the ARINC 429 rate**, with a large wiring-weight saving |
| **CAN / ARINC 825** | 1 Mbit/s | Multi-master | Sub-system level, actuators, sensors |
| **AFDX successors / TTEthernet, ARINC 664 at 1 Gbit/s** | 1 Gbit/s | | Newer programmes and space (TTEthernet on Orion) |

## 10. Displays and the flight deck

The progression: electromechanical instruments → **EFIS** (CRT, from the 757/767 and A310) → LCD glass (six large displays typical) → large-format touchscreen (777X, G500/G600, some bizjets). The core set is **PFD**, **ND**, **EICAS** (Boeing) or **ECAM** (Airbus), and **MFD/systems synoptics**.

Design principles that matter:
- **Dark cockpit philosophy** (Airbus): a lit annunciator means something is not in its normal configuration. Nothing lit = nothing to do.
- **Alerting hierarchy**: Warning (red, aural, immediate action), Caution (amber, aural, awareness and eventual action), Advisory. Governed by 25.1322 and by ARP4102/ARP5289 practice.
- **HUD and combined vision**: HUD with a flight path vector for low-visibility operations and unusual-attitude recovery; **EVS/EFVS** (IR sensor) and **SVS** (terrain database) fused into **CVS**. EFVS to 100 ft and, in some approvals, to touchdown is now operationally credited.
- **Electronic checklists and flight folder**: normal and non-normal checklists linked to the alerting system.

## 11. FMS, navigation and autoflight

**The FMS** integrates a navigation database (ARINC 424 format, 28-day AIRAC cycle), a performance database, and a flight-plan engine. Its core functions:
- **Navigation**: a multi-sensor Kalman-filtered position from **IRS** (ring-laser or fibre-optic gyros with accelerometers, drifting typically < 2 nm/hr), **GNSS** (GPS, plus GLONASS/Galileo/BeiDou on newer units), **DME/DME** and **VOR/DME** radio updating. **RNP** operations specify a containment value (RNP 0.3, RNP 1, RNP 2, RNP 4, RNP 10/RNAV 10) with an on-board performance monitoring and alerting requirement — the defining difference between RNAV and RNP.
- **Approach**: LNAV/VNAV, LPV (with SBAS — WAAS, EGNOS), RNP AR APCH with radius-to-fix legs, and GLS (GBAS landing system).
- **Performance**: optimum altitude, ECON speed from the **cost index** `CI = (time cost)/(fuel cost)`, step climbs, and the predicted fuel and time at each waypoint.
- **Autoflight**: the **AFDS/FMGC** closes outer loops (heading, track, altitude, vertical speed, FPA, speed via autothrust/autothrottle) around the inner FBW or autopilot servo loops. Fail-passive vs **fail-operational** distinguishes CAT IIIa from CAT IIIb/IIIc capability — a fail-operational system continues to land after a single failure, which requires triplex or dual-dual channels.

## 12. The safety net systems

| System | Function | Notes |
|---|---|---|
| **TCAS II / ACAS II** | Independent, transponder-based collision avoidance issuing **TA** and coordinated vertical **RA** | ICAO mandates ACAS II (TCAS II v7.1) above 5,700 kg or 19 seats. **v7.1** added the "LEVEL OFF, LEVEL OFF" reversal logic after the Überlingen (2002) and Japan Airlines near-miss events showed a defect in v7.0's reversal handling. **ACAS X (ACAS Xa/Xo/Xu)** — a dynamic-programming-optimised successor designed to reduce nuisance alerts and to work with UAS — is the coming replacement |
| **EGPWS / TAWS** | Terrain database + GPS position + predictive alerting envelopes; Modes 1–7 plus terrain display | Reduced CFIT accidents by roughly an order of magnitude after mandate. Its weakness is database currency and, historically, position-source quality |
| **Windshear / predictive windshear** | Reactive (inertial/air-data comparison) and predictive (weather radar Doppler) | Post-Delta 191 (1985) |
| **ADS-B Out / In** | Broadcast of GNSS-derived position, velocity and identity at 1090 MHz Extended Squitter (or 978 UAT in the US below FL180) | Mandated in the US (2020), Europe and elsewhere; enabled space-based ADS-B (Aireon on the Iridium NEXT constellation) giving oceanic and polar surveillance and, consequently, reduced separation minima |
| **CPDLC / datalink** | Controller–pilot data link over ACARS (VHF/HF/SATCOM) or ATN/VDL Mode 2; **FANS-1/A** for oceanic with ADS-C position contracts; **ATN B1** in European domestic airspace | Reduces voice congestion and readback error; the current transition is toward **Baseline 2 (ATN B2)** with trajectory-based operations |
| **Weather radar** | X-band, now with automatic multi-scan, predictive windshear, turbulence detection and hail/lightning prediction | |
| **FDR/CVR** | 25 h flight data (ED-112A), 25 h cockpit voice on new installations (EASA/ICAO extension from 2 h) | Plus emerging requirements for tamper-resistant recorders and deployable recorders on new large aeroplanes |

## 13. The sensor suite

| Sensor | Measures | Failure signature |
|---|---|---|
| **Pitot probes** (3+) | Total pressure | Blockage → erroneous/frozen airspeed. AF447 (2009) — Thales AA probes icing at altitude |
| **Static ports** (paired, both sides) | Static pressure | Blockage → altitude and airspeed errors; blocked/taped ports caused Aeroperú 603 (1996) |
| **AoA vanes / probes** (2–3) | Angle of attack | Damage or icing → false stall/protection inputs. Lion Air 610 and Ethiopian 302 |
| **TAT probes** | Total air temperature | Wet/icing errors |
| **ADIRU / ADIRS** | Air data + inertial reference, typically 3 units | Qantas 72 (2008): an ADIRU data-spike fault produced uncommanded pitch-downs; the fix was in the FCPC's data-validation logic |
| **Radio altimeter** | Height AGL to ~2,500 ft | 4.2–4.4 GHz; the 5G C-band interference issue (2021–2023) drove retrofit filtering and altimeter tolerance standards |
| **GNSS receivers** | Position, velocity, time | **Spoofing and jamming** is now the dominant operational threat, particularly in the Middle East and around conflict zones — with documented cases of IRS contamination requiring an on-ground realignment. Directly relevant to Gulf-based operations |
| **Magnetometers, ILS/GLS receivers, DME/VOR/ADF, transponders, SATCOM** | | |

**Sensor redundancy and voting** is where the safety argument lives: three sources allow mid-value select and fault isolation; two sources allow only disagreement detection, not identification of which is wrong. That distinction — three good sources versus two — is the whole engineering content of the MCAS lesson.

## Sources

- [Avionics Full-Duplex Switched Ethernet (ARINC 664 Part 7 / AFDX)](https://en.wikipedia.org/wiki/Avionics_Full-Duplex_Switched_Ethernet) — Wikipedia (data rate, virtual links, BAG, redundancy, aircraft list, ARINC 429 comparison)
- [Fly-by-wire](https://en.wikipedia.org/wiki/Fly-by-wire) — Wikipedia (Airbus normal/alternate law philosophy, A380 BCM, Boeing 777/787 override philosophy, 787/A350 electrical backup, first FBW airliners)
- [14 CFR §25.1309](https://www.ecfr.gov/current/title-14/section-25.1309) — eCFR
- [Boeing 787 Dreamliner](https://en.wikipedia.org/wiki/Boeing_787_Dreamliner) — Wikipedia (bleedless architecture context)
- [DO-178C](https://en.wikipedia.org/wiki/DO-178C) — Wikipedia (Level A objective counts)

## Open questions

- Boeing 787 total electrical generation (≈1.45 MW), 235 V AC / ±270 V DC distribution, and APU generator rating — widely published but not re-verified in this session; `needs-verification`.
- Exact Airbus protection limit values (pitch 30°/25° nose-up, bank 67°, load factor limits) vary by type and by law state; the FCOM for the specific type is authoritative — treat the values here as typical A320/A330-family figures, `needs-verification` for A350.
- Hydraulic system pressures per type (5,000 psi applicability on the 787) — `needs-verification`.
- CVR duration requirements (25 h) and their applicability dates by authority — `needs-verification`.
- ACAS X deployment timeline and mandate status — `needs-verification`.
- 787 cabin altitude and humidity figures are manufacturer claims — `needs-verification`.

