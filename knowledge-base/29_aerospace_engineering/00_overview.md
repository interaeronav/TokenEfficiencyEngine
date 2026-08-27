---
id: aerospace.overview
title: Aerospace engineering — domain overview
domain: 29_aerospace_engineering
tags: [aerospace, aeronautical, astronautics, oem, supply-chain, tier-1, mro, certification, industry-structure, overview]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "MIT Course 16 (Aeronautics and Astronautics) subject listing", url: "http://student.mit.edu/catalog/m16a.html", publisher: "MIT", accessed: 2026-08-25}
  - {title: "Airbus Orders and Deliveries", url: "https://www.airbus.com/en/products-services/commercial-aircraft/market/orders-and-deliveries", publisher: "Airbus SE", accessed: 2026-08-25}
  - {title: "14 CFR Part 25 — Airworthiness Standards: Transport Category Airplanes", url: "https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-25", publisher: "US Government Publishing Office / eCFR", accessed: 2026-08-25}
  - {title: "Boeing 787 Dreamliner", url: "https://en.wikipedia.org/wiki/Boeing_787_Dreamliner", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Airbus A350", url: "https://en.wikipedia.org/wiki/Airbus_A350", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "TU Delft Faculty of Aerospace Engineering", url: "https://www.tudelft.nl/en/ae", publisher: "Delft University of Technology", accessed: 2026-08-25}
related: [aerospace.curriculum, aerospace.aerodynamics, aerospace.propulsion, aerospace.structures, aerospace.design_process, aerospace.manufacturing, aerospace.certification, aerospace.avionics, aerospace.books, aerospace.practicals]
unit_system: SI
---

# Aerospace engineering — domain overview

**Summary.** Aerospace engineering is the discipline of designing, analysing, building, certifying and sustaining vehicles that operate in the atmosphere and beyond it. It is not one subject but a forced marriage of six: fluid mechanics, thermodynamics, solid mechanics, dynamics and control, materials, and systems engineering — all under the constraint that the artefact must be light enough to fly, strong enough not to break, cheap enough to sell, and demonstrably safe enough for a regulator to sign. The discipline splits into **aeronautics** (air-breathing, atmospheric, lift-based) and **astronautics** (ballistic, orbital, vacuum, radiation-limited), which share the mathematics and diverge sharply in the physics and the economics. This domain covers the education, the technical core, the design and manufacturing process, the regulatory machinery, and the industry that employs it.

## Key facts

| Fact | Value | Note |
|---|---|---|
| Two halves of the field | **Aeronautics** and **Astronautics** | MIT's department is literally "Aeronautics and Astronautics" (Course 16) |
| Canonical undergraduate degree | 4 years (Europe/SA: 3 + 2 Bologna, or 4-yr BEng) | ABET (US), ECSA (ZA), Washington Accord signatories |
| Governing UN body | **ICAO** (Chicago Convention, 1944) — Annex 8 *Airworthiness of Aircraft* | Standards, not law, until a State adopts them |
| Primary Western certification codes | **FAA 14 CFR Part 25** / **EASA CS-25** (large aeroplanes) | Part 25 subparts A–I; Subpart H = EWIS |
| Catastrophic failure probability target | **< 1×10⁻⁹ per flight hour** ("extremely improbable") | 14 CFR 25.1309(b); a catastrophic condition must also not result from a single failure |
| Large commercial airframe duopoly | **Airbus** and **Boeing** | Airbus cumulative: 26,534 orders / 17,176 deliveries as of end-July 2026 |
| Airbus 2026 YTD deliveries | **418 aircraft to 82 customers** through July 2026 | 67 delivered in July 2026; 204 gross orders in July |
| Commercial engine oligopoly | **GE Aerospace, Rolls-Royce, Pratt & Whitney (RTX), Safran** (+ JVs CFM, IAE, EA) | CFM = GE + Safran 50/50 |
| Composite content, current widebodies | **787: ~50 % composite by weight** (80 % by volume); **A350: 53 % composite** | 787 also 20 % Al, 15 % Ti, 10 % steel; A350 19 % Al/Al-Li, 14 % Ti, 6 % steel |
| Clean-sheet programme cost | **787 ≈ US$32 bn**; **A350 ≈ €11 bn (2013 estimate)** | Both ran ~3 years late |
| Typical airframe design life | 60,000–90,000 flight cycles / 20–30 years, extended by damage-tolerance inspections | Set by fatigue, not static strength |

> ⚠️ Nothing in this domain is optional-reading for someone who flies the product. The reason an A350 wing is allowed to bend 5 m at limit load, and the reason a 737's lap joint tore open over Maui in 1988, are the same body of knowledge.

## The aero/astro split

The two branches share a first two years and then separate on physics:

**Aeronautics** is dominated by the fact that the vehicle is immersed in a working fluid it can push against. Lift is essentially free; the entire game is minimising the drag penalty of producing it, and the propulsion system breathes the atmosphere so it need not carry oxidiser. Consequences:
- Range is governed by the **Bréguet range equation**: `R = (V/c) · (L/D) · ln(W₁/W₂)` for jets, where `c` is thrust-specific fuel consumption. Every design decision is traceable to one of the four terms.
- Structural design is fatigue-driven: a transport aircraft accumulates one full pressurisation cycle per flight, tens of thousands over its life.
- Certification is mature, prescriptive and adversarial. The rulebook (Part 25 / CS-25) is ~500 pages of specific numeric requirements accumulated from 80 years of accidents.

**Astronautics** is dominated by the fact that there is nothing to push against and no free lift. Consequences:
- Everything is governed by the **rocket equation**: `Δv = I_sp · g₀ · ln(m₀/m_f)`. With `I_sp ≈ 300–460 s` for chemical propulsion and LEO requiring `Δv ≈ 9.3–9.5 km/s` including gravity and drag losses, the propellant mass fraction is 85–95 %. There is no design freedom; there is only mass discipline.
- Structural design is **stiffness- and buckling-driven**, and the load case is usually max-q or staging, not fatigue — most launch vehicles fly once.
- Thermal, radiation and vacuum environments replace weather. Attitude dynamics replaces flight mechanics.
- Certification is not certification: it is mission assurance, range safety, and (for crewed vehicles) NASA/ESA human-rating requirements, plus ITU/FCC spectrum and orbital debris rules.

A third branch has become large enough to be treated separately in practice: **unmanned and autonomous systems** (UAS/UAM/eVTOL), which borrow aeronautical aerodynamics, astronautical mass discipline, automotive-style electric propulsion, and a certification basis (SC-VTOL, Part 108/UAS rules) that is still being written.

## The technical map of the discipline

```
                      AEROSPACE ENGINEERING
                              |
   +---------+---------+------+------+---------+----------+
   |         |         |             |         |          |
 FLUIDS   THERMO/    STRUCTURES   DYNAMICS  MATERIALS  SYSTEMS
   |      PROPULSION      |       & CONTROL     |          |
   |         |            |            |        |          |
 potential  Brayton   load paths   flight mech  Al/Ti    avionics
 boundary   turbojet  semi-mono-   stability    steels   hydraulics
   layer    turbofan  coque        control      Ni-super electrics
 transonic  ramjet    fatigue &    orbital mech composite ECS/ice
 supersonic rockets   damage tol.  attitude     adhesives fuel
 hypersonic inlets    aeroelastic. autoflight   coatings  landing gear
   CFD      nozzles   FEM/NASTRAN  Kalman/LQR   AM        MBSE/SysML
```

Every one of these branches maps to a module in the degree (`01_the-degree-and-curriculum.md`) and to a chapter of the technical files that follow.

## Industry structure

### 1. Airframe OEMs (Original Equipment Manufacturers)

The OEM owns the **Type Certificate** (TC), holds design authority, integrates the aircraft, runs final assembly, and carries the continued-airworthiness obligation for the life of the fleet. That last point is why the OEM population is small: the liability tail is 50 years long.

| Segment | Players |
|---|---|
| Large commercial jets (100+ seats) | **Airbus**, **Boeing**, **COMAC** (C919, C929), Irkut/UAC (MC-21) |
| Regional jets / turboprops | **Embraer** (E-Jet E2), **ATR** (Airbus/Leonardo JV), De Havilland Canada (Dash 8), Mitsubishi (SpaceJet cancelled Feb 2023) |
| Business jets | **Gulfstream** (General Dynamics), **Bombardier**, **Dassault Aviation**, **Textron Aviation** (Cessna/Beechcraft), Embraer Executive, Honda Aircraft |
| General aviation | Cirrus, Diamond, Piper, Pilatus, Textron |
| Rotorcraft | **Airbus Helicopters**, **Leonardo Helicopters**, **Bell**, **Sikorsky** (Lockheed Martin), Robinson |
| Military primes | Lockheed Martin, Boeing Defense, Northrop Grumman, RTX, BAE Systems, Dassault, Saab, Airbus Defence & Space, KAI, TAI, HAL, Denel (**[ZA]**, distressed) |
| Space launch | SpaceX, ULA, Rocket Lab, Arianespace/ArianeGroup, Blue Origin, Firefly, Relativity, ISRO/NSIL, CASC |
| Satellite primes | Airbus Defence & Space, Thales Alenia, Lockheed Martin Space, Boeing (Millennium), Northrop (SpaceLogistics), Maxar, OHB, SpaceX (Starlink, vertically integrated) |

### 2. Propulsion OEMs

Engines are a separate certification universe: they hold their own Type Certificate under **Part 33 / CS-E**, and the airframer certifies the *installation*. Practically, the engine maker is a peer of the airframer, not a supplier.

| Maker | Current commercial families |
|---|---|
| **GE Aerospace** | GE90, **GE9X** (777X; 110,000 lbf / 490 kN, BPR 10:1, OPR 61:1, 134 in fan, 16 blades, 65 CMC parts, TiAl LPT airfoils; FAA TC 25 Sep 2020), GEnx (787/747-8), CF34, Passport |
| **CFM International** (GE + Safran 50/50) | CFM56 (legacy), **LEAP-1A/-1B/-1C**; RTM carbon-fibre fan blades, CMC HPT shrouds; ~15 % fuel burn improvement vs CFM56; LEAP-1A 180-min ETOPS 19 Jun 2017 |
| **Rolls-Royce** | Trent 700/800/900/1000/7000/XWB (**XWB-84 = 84,000 lbf / 370 kN; XWB-97 = 97,000 lbf / 430 kN**), BR700, Pearl; **UltraFan** demonstrator (first run May 2023, 64 MW power gearbox, target BPR 15:1, OPR 70:1) |
| **Pratt & Whitney** (RTX) | PW1000G **GTF** family — PW1100G-JM (A320neo, BPR 12.2:1, 3:1 reduction gear, FAA TC 19 Dec 2014), PW1500G (A220, TCCA 20 Feb 2013), PW1900G (E2); PW4000, F135 (F-35) |
| **IAE International Aero Engines** | V2500 (A320ceo, MD-90) — P&W/MTU/JAEC consortium |
| **Safran Aircraft Engines** | CFM share, M88 (Rafale), Silvercrest, helicopter engines via Safran Helicopter Engines |
| **MTU Aero Engines** | Risk-and-revenue partner on GEnx, GP7000, PW1000G (HPC, LPT); MRO |
| **Honeywell / Williams / GE Aerospace (small)** | APUs, business-jet turbofans (HTF7000, FJ44) |

### 3. Tier 1 — major structures and systems integrators

A Tier 1 delivers a complete, tested, often certified sub-assembly with design responsibility delegated by the OEM. This is where the 787 outsourcing experiment lived and partly failed (see `06_aerospace-manufacturing.md`).

- **Aerostructures:** Spirit AeroSystems (737 fuselage, A350 sections — being split between Boeing and Airbus following Boeing's July 2024 acquisition agreement, `needs-verification` on final completion date), Leonardo Aerostructures (787 sections 44/46, Grottaglie), Kawasaki Heavy Industries, Mitsubishi Heavy Industries (787 wing box), Subaru (787 centre wing box), GKN Aerospace, Triumph Group, Aernnova, Sonaca, Aciturri, Korean Air Aerospace Division.
- **Systems:** Collins Aerospace (RTX) — avionics, interiors, actuation, wheels/brakes, ECS; Honeywell Aerospace — APUs, avionics, wheels/brakes; Safran (landing gear, nacelles, wiring, seats, electrical); Thales (avionics, IFE, ATM); Liebherr-Aerospace (ECS, actuation); Parker Aerospace (hydraulics, fuel); Moog (actuation); Meggitt/Parker (braking, sensors); Diehl Aviation (cabin, avionics).
- **Nacelles/thrust reversers:** Safran Nacelles, Collins (Goodrich), Spirit.

### 4. Tier 2 and Tier 3 — the part of the industry nobody sees

- **Tier 2**: build-to-print machined assemblies, sub-systems, harnesses, valve and actuator makers, gearbox houses, avionics box shops. Typically 50–1,000 employees.
- **Tier 3**: single-process shops — machining, sheet metal, heat treat, chemical processing, NDT, plating, painting, composite layup. **These must hold Nadcap accreditation for their special processes**, and their capacity is the real constraint on rate ramps.
- **Raw material and semi-finished**: Constellium, Arconic/Howmet, Kaiser Aluminum (aluminium plate/extrusion); ATI, VSMPO-AVISMA, TIMET (titanium); Aubert & Duval, Otto Fuchs, Howmet (forgings); Precision Castparts (structural and turbine castings); Hexcel, Toray, Solvay, Teijin (carbon fibre and prepreg); Howmet Fastening Systems, LISI Aerospace, Arconic (fasteners).

Titanium, large forgings/castings, and fasteners are the perennial bottlenecks. VSMPO-AVISMA's position as a major titanium supplier made the post-2022 sanctions environment a structural supply-chain problem for both Airbus and Boeing.

### 5. MRO — maintenance, repair and overhaul

MRO is roughly a **US$100–120 bn/yr** industry (`needs-verification` on the exact 2026 figure) split into four segments: **line maintenance**, **base/heavy maintenance (C and D checks)**, **engine overhaul** (by far the largest value pool, ~40 %), and **components**. Engine MRO is dominated by the OEMs themselves through licensed networks — this is the razor-and-blades model that makes engine programmes profitable.

Major independents and airline-affiliated MROs: **Lufthansa Technik**, **AFI KLM E&M**, **ST Engineering Aerospace**, **HAECO**, **AAR Corp**, **SIA Engineering**, **Delta TechOps**, **Turkish Technic**, **Etihad Engineering**, **Qatar Airways Technical** (Doha), **Emirates Engineering**, **Joramco** (Amman), **SAA Technical** and **Denel Aviation** (**[ZA]**).

For a line pilot, the MRO interface is visible daily: the MEL, deferred defects, the AD status of the airframe, and the reason a component was replaced on a life-limit rather than on condition.

### 6. Certification authorities and their hierarchy

| Level | Body | Instrument |
|---|---|---|
| International | **ICAO** | Annexes to the Chicago Convention — Annex 8 (Airworthiness), Annex 6 (Operations), Annex 16 (Environmental Protection: noise Vol I, emissions Vol II, CO₂ Vol III) |
| Regional/State | **EASA** (EU), **FAA** (US), **UK CAA**, **TCCA** (Canada), **ANAC** (Brazil), **CAAC** (China), **DGCA** (India), **GCAA** (UAE), **QCAA** (Qatar), **SACAA** (**[ZA]**), **NCAA** (**[NA]**) | Certification Specifications / Federal Aviation Regulations |
| Design organisation | **DOA** (EASA Part 21 Subpart J) / **ODA** (FAA) | Privilege to approve designs and changes |
| Production organisation | **POA** (EASA Part 21 Subpart G) / **PC** (FAA Production Certificate) | Privilege to build to an approved design |
| Continued airworthiness | **AD**s, service bulletins, Part-M/Part-CAMO | The mechanism by which fleets are fixed after entry into service |

Bilateral Aviation Safety Agreements (BASAs) with Technical Implementation Procedures let EASA and the FAA validate each other's certificates rather than repeat them — that reciprocal trust is exactly what the 737 MAX affair damaged, and why EASA independently mandated the AoA disagree alert and a synthetic airspeed pathway before returning the type to service.

## Where the money and the jobs are

- **Design/stress/aero engineering** at OEMs and Tier 1s: highly cyclical, tied to programme launches. A clean-sheet aircraft programme is roughly a 7–10 year, US$10–35 bn undertaking, so there may be only two or three genuinely new large aircraft per decade worldwide.
- **Certification and airworthiness engineering**: counter-cyclical, chronically short-staffed, and the highest-leverage niche for someone who already understands operations.
- **Manufacturing and industrial engineering**: where the rate problem lives, and where Boeing's and Airbus's current constraints actually are.
- **Space**: the fastest-growing employer since ~2015, driven by launch cost collapse (Falcon 9 reusability) and constellation build-out.
- **Sustainability/propulsion transition**: SAF, hydrogen, hybrid-electric — large research spend, honest maturity still low (see `03_propulsion.md`).

## How this domain is organised

| File | Contents |
|---|---|
| `01_the-degree-and-curriculum.md` | Module-by-module curriculum, prerequisite chains, textbooks, free courses, labs, and the leading + southern African programmes |
| `02_aerodynamics.md` | Potential flow through hypersonics, drag decomposition, airfoil and planform design, CFD and its honest limits |
| `03_propulsion.md` | Piston, Brayton cycle, turbojet/turbofan/turboprop/ramjet, components, performance parameters, materials, manufacturers, electric/hydrogen |
| `04_structures-and-materials.md` | Load paths, semi-monocoque, fatigue and damage tolerance, Comet and Aloha, and the materials with real property tables |
| `05_aircraft-design-process.md` | Requirements → conceptual sizing loop → preliminary → detail; constraint analysis worked; MDO, CAD/PLM, MBSE, programme timelines |
| `06_aerospace-manufacturing.md` | Make/buy, the 787 lesson, machining/forming/composites at rate, FAL and pulse lines, learning curve, AS9100/Nadcap, MRO, space manufacturing |
| `07_certification-and-airworthiness.md` | ICAO/EASA/FAA machinery, CS-25/Part 25, TC process, DOA/POA, DO-178C/DO-254, ARP4754B/4761A, ADs, 737 MAX, novel technology |
| `08_avionics-and-systems.md` | Flight controls and control laws, hydraulics, electrics, fuel, ECS, ice protection, gear, APU, IMA and data buses, flight deck, FMS, TCAS/EGPWS/ADS-B |
| `09_essential-books-and-materials.md` | Annotated catalogue by subject, with level and whether free |
| `10_practicals-and-projects.md` | Lab work, software skills, capability-building projects, competitions, internships |

## Sources

- [MIT Course 16 subject listing (undergraduate)](http://student.mit.edu/catalog/m16a.html) — MIT
- [MIT Course 16 subject listing (graduate)](http://student.mit.edu/catalog/m16b.html) — MIT
- [Airbus Orders and Deliveries](https://www.airbus.com/en/products-services/commercial-aircraft/market/orders-and-deliveries) — Airbus SE
- [14 CFR Part 25](https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-25) and [§25.1309](https://www.ecfr.gov/current/title-14/section-25.1309) — eCFR
- [Boeing 787 Dreamliner](https://en.wikipedia.org/wiki/Boeing_787_Dreamliner) — Wikipedia
- [Airbus A350](https://en.wikipedia.org/wiki/Airbus_A350) — Wikipedia
- [General Electric GE9X](https://en.wikipedia.org/wiki/General_Electric_GE9X) — Wikipedia
- [Rolls-Royce UltraFan](https://en.wikipedia.org/wiki/Rolls-Royce_UltraFan) — Wikipedia
- [Pratt & Whitney PW1000G](https://en.wikipedia.org/wiki/Pratt_%26_Whitney_PW1000G) — Wikipedia
- [TU Delft Faculty of Aerospace Engineering](https://www.tudelft.nl/en/ae) — TU Delft

## Open questions

- Exact completion date and final work-package split of the Boeing/Airbus acquisition of Spirit AeroSystems — `needs-verification`.
- Current global MRO market value for 2026 — figure quoted is an order-of-magnitude estimate, `needs-verification`.
- Boeing 2025 full-year and 2026 year-to-date delivery totals could not be fetched from boeing.com (page is a JS application); see `06_aerospace-manufacturing.md`.
