---
id: aerospace.design_process
title: How an aircraft is actually designed
domain: 29_aerospace_engineering
tags: [aircraft-design, conceptual-design, sizing, constraint-analysis, wing-loading, thrust-to-weight, mdo, catia, 3dexperience, siemens-nx, teamcenter, plm, digital-mockup, digital-twin, mbse, sysml, programme-timeline]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Boeing 777", url: "https://en.wikipedia.org/wiki/Boeing_777", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Boeing 787 Dreamliner", url: "https://en.wikipedia.org/wiki/Boeing_787_Dreamliner", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Airbus A350", url: "https://en.wikipedia.org/wiki/Airbus_A350", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "MIT Course 16 graduate subject listing (16.888[J] MDO, 16.842, 16.885)", url: "http://student.mit.edu/catalog/m16b.html", publisher: "MIT", accessed: 2026-08-25}
  - {title: "OpenVSP", url: "https://openvsp.org/", publisher: "NASA / OpenVSP community", accessed: 2026-08-25}
related: [aerospace.aerodynamics, aerospace.structures, aerospace.manufacturing, aerospace.certification]
unit_system: SI
---

# How an aircraft is actually designed

**Summary.** Aircraft design is a convergent iteration on a fixed point: the aircraft's weight depends on its size, its size depends on the fuel it must carry, the fuel depends on the weight. The conceptual designer's job is to close that loop with the crudest models that are still honest, arriving at a wing area, a thrust level and a take-off weight in days rather than years. Everything after that — preliminary design, detail design, digital mock-up, tooling, test — is the progressive replacement of estimates with facts at a cost that rises by roughly an order of magnitude at each phase. Which is why the decisions taken in the first three months, on perhaps 0.5 % of the programme budget, lock in about 80 % of the life-cycle cost.

## Key facts

| Item | Value |
|---|---|
| Design phases | Requirements → Conceptual → Preliminary → Detail → Test & Certification → Production |
| Cost committed vs cost spent | ≈ 80 % of life-cycle cost committed by end of conceptual design, when ≈ 1–5 % has been spent |
| Clean-sheet large aircraft programme | 7–10 years, US$10–35 bn |
| Boeing 777 | Launched **October 1990**, rollout April 1994, first flight **June 1994**, EIS **June 1995**; **> US$4 bn Boeing + ~US$2 bn suppliers**; **first commercial aircraft developed entirely by CAD** using Dassault/IBM **CATIA**, with no full physical mock-up |
| Boeing 787 | Launched 2004 for 2008 EIS; first flight **15 December 2009**; first delivery **September 2011** — roughly **3 years late** after **five announced delays**; programme cost reported at **≈ US$32 bn**, accumulated deferred/loss position ≈ US$27 bn by May 2015 |
| Airbus A350 | Authority to offer **10 December 2004**, first flight **14 June 2013**, first delivery **22 December 2014 to Qatar Airways**, EIS **15 January 2015**; development ≈ **€11 bn** (June 2013 estimate) |
| Structural factor of safety | 1.5 (14 CFR 25.303) — fixed by regulation, not by the designer |

> ⚠️ The sizing loop below is the actual method used in industry and in every capstone course. It is deliberately crude. Its value is that it converges in minutes and gives a defensible starting point; its danger is that its historical regressions embed the technology level of the aircraft they were fitted to.

## 1. Requirements and market analysis

Nothing is designed without a mission. The requirement set that starts a commercial programme is written by the market, not by engineering:

- **Payload–range**: e.g. "325 passengers in 3-class at 95 kg each including bags, 8,000 nm still-air range, at M 0.85."
- **Field performance**: take-off field length at MTOW, ISA+15, at a specified airport elevation; landing field length at MLW; second-segment climb gradient with one engine inoperative.
- **Cruise**: Mach number, initial cruise altitude capability, buffet margin (typically 1.3 g).
- **Airport compatibility**: ICAO aerodrome code letter (Code E = 52–65 m wingspan, Code F = 65–80 m), pavement classification, door sill heights, turning radius.
- **Certification basis**: CS-25/Part 25 amendment level, plus special conditions for novel features.
- **Economics**: cash operating cost per seat-mile target, residual value, maintenance cost per flight hour, fuel burn per seat versus the competing aircraft. This is usually the single hardest requirement.
- **Environmental**: ICAO Annex 16 Chapter 14 noise, CAEP/8 NOx, and the Annex 16 Volume III CO₂ metric.

The market analysis behind those numbers is a forecast of traffic growth by route group, fleet replacement demand, and competitor product timing. Airbus's *Global Market Forecast* and Boeing's *Commercial Market Outlook* are the public face of this and are, unavoidably, both analysis and marketing.

## 2. Conceptual design: the sizing loop

### Step 1 — First weight estimate

Take-off gross weight decomposes as:
```
W_0 = W_crew + W_payload + W_fuel + W_empty
```
Divide through by `W_0`:
```
W_0 = (W_crew + W_payload) / (1 − W_f/W_0 − W_e/W_0)
```
`W_e/W_0` (empty weight fraction) comes from a historical regression of the form `W_e/W_0 = A·W_0^C` — Raymer tabulates A and C by aircraft class (for a jet transport, roughly `W_e/W_0 ≈ 1.02 W_0^{-0.06}` in imperial units, giving 0.50–0.56 for a large transport; composite structure earns a multiplier of about 0.95).

`W_f/W_0` is built from a chain of mission-segment fractions:
```
W_f/W_0 = 1.06 · (1 − Π (W_i/W_{i-1}))
```
with the 6 % allowance for reserves and trapped fuel. Typical segment fractions: engine start/warm-up 0.990, taxi 0.995, take-off 0.995, climb 0.980, descent 0.990, landing 0.992. The **cruise** segment comes from the Bréguet range equation rearranged:
```
W_i/W_{i-1} = exp( −R·c / (V · (L/D)) )
```
and the **loiter** segment from `W_i/W_{i-1} = exp(−E·c/(L/D))`.

Worked, for a widebody: `R = 8,000 nm = 14.816×10⁶ m`, `V = 250 m/s`, `L/D = 18`.

> **Unit discipline in `c` is the single most common error in student sizing work.** In this form `c` must be expressed as *fuel weight flow per unit thrust*, i.e. N/(N·s) = s⁻¹ — not as mass flow per unit thrust. A TSFC of `15 g/(kN·s)` is `1.5×10⁻⁵ kg/(N·s)`; multiply by `g = 9.81` to get `1.47×10⁻⁴ s⁻¹`. Using the mass-flow value directly under-predicts fuel burn by a factor of ten.

`Rc/(V·L/D) = (14.816×10⁶ × 1.47×10⁻⁴)/(250 × 18) = 2178/4500 = 0.484`, so `W_i/W_{i-1} = e^{−0.484} = 0.616`. Cruise burns 38 % of the weight at top of climb — the right order for an ultra-long-haul sector.

Multiply the fractions: overall ≈ 0.616 × 0.99 × 0.995 × 0.995 × 0.98 × 0.99 × 0.992 ≈ 0.578, so `W_f/W_0 = 1.06 × (1 − 0.578) = 0.447`. With payload+crew of 32 t and `W_e/W_0 = 0.50`, `W_0 = 32,000/(1 − 0.447 − 0.50)` — which is *negative*, meaning the design does not close. That is the correct and useful outcome: with an `L/D` of 18 and that TSFC, an 8,000 nm mission at 0.50 empty weight fraction is impossible; the designer must buy `L/D`, buy TSFC, or accept a lighter structure fraction. Iterating with a composite-structure empty fraction of 0.47 and `L/D = 20` closes the loop at an MTOW in the 270–290 t region — which is where an A350-1000 or 777-9 actually sits. **The loop failing to close is information, not an error.**

### Step 2 — Constraint analysis (the T/W vs W/S diagram)

This is the heart of conceptual design and every capstone. Plot **thrust-to-weight ratio `T/W` against wing loading `W/S`**; each performance requirement becomes a curve; the feasible region is above/right of all of them; the design point is chosen at the lowest `T/W` and highest `W/S` the constraints allow (lowest thrust = cheapest engine and best SFC; highest wing loading = smallest, lightest wing and the best ride).

The master equation (Mattingly form), for a general flight condition:
```
T/W = (q/(W/S)) · [ K₁ (n W/(qS))² + K₂ (n W/(qS)) + C_D0 ]  +  (1/V)(dh/dt) + (1/g)(dV/dt)
```
with `q = ½ρV²`, `n` the load factor, and `K₁ = 1/(π AR e)`.

The individual constraints, in the form actually plotted:

| Requirement | Constraint |
|---|---|
| **Take-off field length** | `T/W ≥ (W/S) · (1.21) / (g ρ σ C_{L,TO} s_{TO})` for a balanced field length `s_{TO}` — a straight line through the origin on the T/W vs W/S plot |
| **Landing field length** | `W/S ≤ ½ ρ σ V_{stall}² C_{L,max,land}` with `V_{app} = 1.23 V_{S1g}` and landing distance ≈ 1.667 × landing field length under Part 25 — **a vertical line**; usually the binding constraint on wing area for a transport |
| **Second-segment climb (OEI)** | `T/W ≥ (N/(N−1)) · (1/(L/D) + γ_min)`, with `γ_min` = 2.4 % for twins, 2.7 % for trijets, 3.0 % for quads; multiply by a factor for the windmilling-drag and bank-angle allowances |
| **Cruise speed / ceiling** | `T/W ≥ (q C_{D0})/(W/S) + (W/S)·K/q`, evaluated at cruise altitude with thrust lapse `α = T_{alt}/T_{SL}` — a hyperbola with a minimum |
| **Sustained turn / manoeuvre** (military) | `T/W ≥ q[C_{D0}/(W/S) + K (n/q)²(W/S)]` |
| **Ceiling / service ceiling** | Residual rate of climb of 100 ft/min at the ceiling |
| **Buffet-limited cruise `C_L`** | `W/S ≤ 0.7 p M² C_{L,buffet}/1.3` |

Representative design points: a large twin-aisle jet transport sits at `W/S ≈ 6,500–7,500 N/m² (135–155 lb/ft²)` and `T/W ≈ 0.28–0.32`; a narrowbody at `W/S ≈ 5,800–6,700 N/m²` and `T/W ≈ 0.30–0.34`; a light single at `W/S ≈ 800–1,200 N/m²` and `P/W ≈ 0.07–0.09 kW/N`; a fighter at `W/S ≈ 3,000–5,000 N/m²` and `T/W ≈ 0.9–1.2`.

Once `W_0`, `W/S` and `T/W` are chosen, `S = W_0/(W/S)` and `T = (T/W)W_0` follow immediately, and with them the wing geometry (AR, sweep, taper, `t/c`), the engine selection, and the fuselage layout from the cabin cross-section outward.

### Step 3 — Configuration layout and the first drawing

Fuselage from the inside out: seat width and pitch → seats abreast → cabin width → structural depth → external diameter; then length from the seat count, galleys, lavatories, doors (Part 25.807 exit requirements by passenger count) and the tail-strike-limited aft body angle. Wing position from the CG: put the wing MAC quarter-chord such that the loaded CG range falls within roughly 15–35 % MAC. Empennage sized by **tail volume coefficients**:
```
V_H = (l_H S_H)/(c̄ S)    typical 0.9–1.2 for jet transports
V_V = (l_V S_V)/(b S)     typical 0.07–0.09
```
Landing gear from the tip-back angle (≥ 15° aft of the aft CG), the overturn angle (≤ 63°), the nose-gear load fraction (8–15 % static), tail strike clearance, and pavement loading (LCN/ACN, which drives the bogie count — this is why a 777 has six-wheel trucks).

Then the drag polar, the weight breakdown by group (Class I: statistical fractions; Class II: component equations from Roskam, Torenbeek or Raymer that account for geometry and load factor), the CG envelope, and back around the loop. Three to six iterations is normal. Tools: **OpenVSP** for the geometry and VSPAERO for the first aero, spreadsheets or Python for the loop, **AVL** for stability derivatives, **XFOIL** for the sections.

## 3. Preliminary design

Configuration is frozen ("configuration freeze" is a real, dated milestone) and the work becomes deep rather than broad:
- Detailed loads: manoeuvre and gust loads across the flight envelope, ground loads, at hundreds of mass/CG/configuration combinations, producing the loads database that every stress analysis uses.
- Structural layout and sizing to those loads, with FEM (Nastran/Abaqus) at global level and hand analysis at detail level; internal loads extracted from the global FEM and fed into margin-of-safety calculations for every part.
- Aerodynamic development: high-speed wing design in CFD, wind-tunnel campaigns (typically 10,000–25,000 tunnel hours for a large transport across cruise, high-lift, powered nacelle, buffet, stability and control, and icing models).
- Systems architecture: hydraulic, electrical, ECS, fuel; ATA chapter decomposition; preliminary FHA.
- Aeroelastic clearance: flutter analysis, GVT planning.
- Supplier selection and the make/buy decision (see `06_aerospace-manufacturing.md`).
- Certification plan agreed with the authority: the **certification basis**, the list of **means of compliance** for every applicable paragraph, and the certification programme plan.

Milestones are gated reviews: SRR (system requirements), PDR (preliminary design), CDR (critical design). Passing CDR means drawings are released for tooling and long-lead procurement — the point of no return financially.

## 4. Detail design

Every part is defined: geometry, material, temper, finish, tolerances, fastener callouts, and the manufacturing and inspection plan. This is where the headcount is — a large aircraft programme employs several thousand engineers for several years at this stage. Outputs are the **3-D master model** (the drawing is now often derived from, or replaced by, the model under model-based definition, MBD), the parts list, the tooling design, the assembly sequence and the build plan.

Concurrently: test articles are built (static, fatigue, iron bird for systems, avionics integration rig, engine test), the flight-test instrumentation is designed, and the flight-test aircraft are laid down. A large transport certification campaign uses **4–6 flight test aircraft** and **2,000–3,000 flight hours** over 12–18 months.

## 5. The design trade space and MDO

Every conceptual design decision is a trade with quantified partial derivatives. The ones every aerospace engineer should have in their head:

| Trade | Direction |
|---|---|
| ↑ Aspect ratio | ↓ induced drag, ↑ wing weight, ↑ root bending moment, ↑ span (gate limits), ↑ flutter risk |
| ↑ Sweep | ↑ `M_DD`, ↓ `C_Lmax`, ↑ wing weight, ↑ tip-stall tendency, ↑ crossflow transition |
| ↑ `t/c` | ↓ wing weight (more depth), ↑ fuel volume, ↓ `M_DD` |
| ↑ Wing loading | ↓ wing weight and drag, ↑ field length, ↓ ride quality, ↑ approach speed |
| ↑ Bypass ratio | ↓ TSFC, ↑ nacelle drag and weight, ↑ ground clearance problem, ↑ gearbox complexity |
| ↑ Cruise Mach | ↑ productivity, ↑ wave drag, ↑ sweep and hence weight |
| Composite structure | ↓ weight 15–20 %, ↑ recurring cost, ↑ NRE, ↑ repair complexity, ↓ fatigue/corrosion maintenance |

**Multidisciplinary Design Optimisation (MDO)** formalises this. The problem is `min f(x)` subject to `g(x) ≤ 0`, `h(x) = 0`, where the objective couples disciplines whose analyses feed each other (aero loads → structural deflection → changed aero shape → changed loads). Architectures:
- **MDF (multidisciplinary feasible)** — an inner multidisciplinary analysis (MDA) loop converged at every optimiser iteration. Simple, robust, slow.
- **IDF (individual discipline feasible)** — coupling variables become optimiser variables with consistency constraints.
- **Simultaneous analysis and design (SAND)**, **collaborative optimisation**, **ATC**, **BLISS** — decomposition schemes for organisationally separated teams.
- **Gradient-based with adjoints** is what makes high-fidelity MDO tractable: the adjoint method computes the gradient of one objective with respect to thousands of design variables at roughly the cost of one extra flow solve, independent of the number of variables. This is the single most important algorithmic development in aerodynamic design since the panel method, and it is why SU2's discrete-adjoint capability matters.

**Aerostructural optimisation** — simultaneously optimising the outer mould line and the internal structure — routinely finds 3–8 % fuel-burn improvements that sequential aero-then-structures design misses, because it correctly values the wing-weight cost of a high-aspect-ratio wing. The University of Michigan MDO Lab's **OpenMDAO / OpenAeroStruct / MACH** ecosystem (NASA-supported, open source) is the accessible entry point; MIT teaches the subject as **16.888[J] Multidisciplinary Design Optimization** (prerequisite 18.085).

## 6. CAD, PLM and the digital thread

**CATIA** (Dassault Systèmes) is the aerospace CAD standard, and its adoption is a genuine historical inflection. The **Boeing 777**, launched October 1990, was **the first commercial aircraft developed entirely by CAD**, using CATIA sourced from Dassault Systèmes and IBM, with a full **digital mock-up** replacing the physical one: engineers virtually assembled the aircraft to check interference and fit before physical assembly, using a tool called **FlyThru** (later the Integrated Visualization Tool, IVT). Boeing organised the work into **240 design-build teams of up to 40 people**, resolving nearly 1,500 design issues, and the aircraft was completed with sufficient precision that it was **the first Boeing jetliner not to require an expensive physical mock-up**. That programme cost over **US$4 bn** from Boeing plus about **US$2 bn** from suppliers, launched October 1990, rolled out April 1994, first flew June 1994 and entered service with United in June 1995 — a 4-year-8-month cycle that has not been matched since.

The current landscape:

| Tool | Vendor | Role |
|---|---|---|
| **CATIA V5 / 3DEXPERIENCE** | Dassault Systèmes | Aerostructure CAD; V5 remains enormously entrenched (787, A350, A380 were V5-era programmes), with new programmes moving onto the **3DEXPERIENCE** platform. Airbus and Boeing have both announced multi-year strategic partnerships with Dassault to move design, manufacturing and services onto 3DEXPERIENCE (`needs-verification` on the exact announcement dates and scope) |
| **ENOVIA** | Dassault Systèmes | PLM: configuration management, change management, BOM, effectivity |
| **DELMIA** | Dassault Systèmes | Digital manufacturing: assembly simulation, ergonomics, line balancing, robot programming |
| **Siemens NX** | Siemens Digital Industries | CAD used across engine makers, Tier 1s, and defence primes; strong in machining (NX CAM) |
| **Teamcenter** | Siemens | PLM competitor to ENOVIA; very widely used in the supply chain and by engine OEMs |
| **Creo / Windchill** | PTC | Common in Tier 2/3 and in space |
| **CAE** | MSC Nastran, Abaqus, ANSYS, LS-DYNA, HyperWorks | Structural and multiphysics |
| **CFD** | Fluent, Star-CCM+, in-house (elsA/CODA), SU2, OpenFOAM | See `02_aerodynamics.md` |

**Configuration management** is the unglamorous core of PLM and the thing that actually distinguishes aerospace from other industries: every aircraft is built to a specific configuration defined by effectivity (by MSN, by block, by date), every change is a controlled document with an approval chain, and the as-designed / as-planned / as-built / as-maintained BOMs must reconcile for the life of the airframe. When they do not reconcile, you get the 787's traveled work and the Alaska 1282 door plug — both, at root, configuration control failures.

**Digital mock-up (DMU)** is the assembled 3-D model used for interference checking, clearance, maintainability (can a hand and a tool reach that fastener?), and assembly sequencing. **Digital twin** is the further step: a model of a *specific* serial-numbered asset, updated with its as-built deviations and its operational data, used to predict remaining life and to plan maintenance. The honest position in 2026: DMU is mature and universal; digital twin is real and valuable for **engines** (GE, RR and P&W all run per-serial-number engine models fed by flight data, which is how EGT margin and LLP life are managed) and largely aspirational for airframes.

**Model-Based Systems Engineering (MBSE)** replaces the requirements document, the interface control document and the architecture PowerPoint with a single connected model — typically in **SysML** (now SysML v2, a substantial rewrite adopted by OMG) in tools such as Cameo/MagicDraw, IBM Rhapsody or Capella (open source, Thales-originated, with the Arcadia method). The claimed benefits — consistency, traceability from requirement to test case, automated document generation, early detection of interface errors — are real, and the barrier is cultural and tooling cost rather than technical. MIT teaches this as **16.842 Fundamentals of Systems Engineering** and **16.885 Aircraft Systems Engineering**. It matters most where the certification evidence trail is the deliverable (see ARP4754B in `07_certification-and-airworthiness.md`), because MBSE and DAL-driven development assurance are the same discipline seen from two sides.

**Simulation-driven design** is the general trend: move analysis earlier, use it to explore rather than to check, and replace physical tests where the model is validated. It has genuinely displaced some wind tunnel and rig testing. It has not displaced the structural test article, the iron bird, the GVT, or flight test, and — after the 737 MAX — the regulatory appetite for replacing physical evidence with simulation has, correctly, decreased.

## 7. Timeline and cost of real programmes

| Programme | Launch | First flight | EIS | Slip vs plan | Cost | What went wrong |
|---|---|---|---|---|---|---|
| **Boeing 777** | Oct 1990 | Jun 1994 | Jun 1995 (United) | ~on time | >$4 bn + $2 bn suppliers | Nothing much — the benchmark |
| **Boeing 787** | 2004 (for 2008 EIS) | **15 Dec 2009** | Sep 2011 (ANA) | **~3 years, five announced delays** | **≈$32 bn**; ≈$27 bn accumulated losses by May 2015 | Extreme outsourcing with Tier 1 design responsibility; subcontractors could not procure parts or finish subassemblies, leaving "**traveled work**" for Boeing to complete; fastener shortages; a wing-body join that did not meet static test; Alenia's parent booked ~€750 m of losses. Then the **January 2013 lithium-ion battery grounding** of the whole fleet, resolved with a redesigned battery enclosure approved by the FAA in April 2013 |
| **Airbus A380** | Dec 2000 | Apr 2005 | Oct 2007 | ~2 years | ≈€12–15 bn | Wiring harness configuration mismatch between CATIA V4 (Hamburg) and V5 (Toulouse) sites — a *configuration management* failure, not a design failure; production ended 2021 after 251 aircraft |
| **Airbus A350** | ATO **10 Dec 2004**, relaunched as A350 XWB Dec 2006 | **14 Jun 2013** | **15 Jan 2015**; first delivery **22 Dec 2014 to Qatar Airways** | ~2 years from the XWB relaunch | **≈€11 bn** (Jun 2013 estimate) | The original A350 was rejected by customers as a re-winged A330; the XWB redesign cost two years. Execution thereafter was comparatively disciplined — Airbus deliberately kept more design authority in-house after watching the 787 |
| **Airbus A220 (Bombardier CSeries)** | Jul 2008 | Sep 2013 | Jul 2016 (Swiss) | ~2.5 years | ≈US$6 bn+ | PW1500G GTF maturity problems; a flight-test engine failure in May 2014; the cost overrun effectively bankrupted the programme for Bombardier, which sold a majority to Airbus in 2018 for a nominal sum. Technically excellent aircraft, commercially catastrophic for its originator |
| **COMAC C919** | 2008 | May 2017 | **Dec 2022 (first delivery to China Eastern)**, commercial service May 2023 | ~5–6 years | undisclosed | First-time integration of a Western supply chain (LEAP-1C, Collins, Honeywell, Liebherr) into a Chinese airframe; certification by CAAC only — **no EASA or FAA validation as of 2026** (`needs-verification` on current EASA validation status). Production ramp is the current constraint |
| **Boeing 777X** | Nov 2013 | Jan 2020 | not yet in service as of 2026 | **5+ years** | — | GE9X development, a 2019 static test failure of a fuselage section, COVID, and post-MAX regulatory scrutiny. Certification timeline has repeatedly slipped (`needs-verification` on the current target) |

**The pattern.** Every clean-sheet programme since the 777 has run 2–5 years late. The recurring causes are not aerodynamic or structural — they are **supply-chain design authority given away without the capability to oversee it**, **configuration management failures**, **new-technology maturity assumed rather than demonstrated**, and **schedule pressure applied to certification**. That last one is the 737 MAX story and it is dealt with in `07_certification-and-airworthiness.md`.

## Sources

- [Boeing 777](https://en.wikipedia.org/wiki/Boeing_777) — Wikipedia (CATIA, digital mock-up, design-build teams, timeline, cost)
- [Boeing 787 Dreamliner](https://en.wikipedia.org/wiki/Boeing_787_Dreamliner) — Wikipedia (outsourcing, traveled work, delays, cost, battery grounding)
- [Airbus A350](https://en.wikipedia.org/wiki/Airbus_A350) — Wikipedia (timeline, cost, first delivery to Qatar Airways)
- [MIT Course 16 graduate subjects](http://student.mit.edu/catalog/m16b.html) — MIT (16.888[J] MDO, 16.842, 16.885, 16.887[J])
- [OpenVSP](https://openvsp.org/) — NASA / OpenVSP community

## Open questions

- Exact announcement dates and scope of the Airbus–Dassault Systèmes and Boeing–Dassault Systèmes 3DEXPERIENCE partnerships — the press-release pages did not resolve; `needs-verification`.
- A380 development cost (€12–15 bn) and A220/CSeries development cost — widely reported ranges, not verified from company filings in this session; `needs-verification`.
- COMAC C919 EASA validation status as of 2026 and Boeing 777X certification target — `needs-verification`.
- Wind-tunnel hour counts and flight-test aircraft/hour counts for a large transport are industry rules of thumb, not programme-specific figures.

