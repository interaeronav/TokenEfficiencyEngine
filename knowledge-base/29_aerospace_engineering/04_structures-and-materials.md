---
id: aerospace.structures
title: Aerospace structures and materials
domain: 29_aerospace_engineering
tags: [structures, semi-monocoque, wing-box, fatigue, damage-tolerance, fail-safe, comet, aloha-243, aluminium, 2024, 7075, al-li, titanium, ti-6al-4v, superalloy, composites, cfrp, prepreg, autoclave, rtm, afp, honeycomb, adhesives, corrosion, additive-manufacturing]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "7075 aluminium alloy", url: "https://en.wikipedia.org/wiki/7075_aluminium_alloy", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Ti-6Al-4V", url: "https://en.wikipedia.org/wiki/Ti-6Al-4V", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "De Havilland Comet", url: "https://en.wikipedia.org/wiki/De_Havilland_Comet", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Aloha Airlines Flight 243", url: "https://en.wikipedia.org/wiki/Aloha_Airlines_Flight_243", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Boeing 787 Dreamliner", url: "https://en.wikipedia.org/wiki/Boeing_787_Dreamliner", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Airbus A350", url: "https://en.wikipedia.org/wiki/Airbus_A350", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "14 CFR Part 25 Subpart C — Structure", url: "https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-25", publisher: "eCFR", accessed: 2026-08-25}
related: [aerospace.aerodynamics, aerospace.manufacturing, aerospace.certification, aerospace.curriculum]
unit_system: SI
---

# Aerospace structures and materials

**Summary.** An airframe is a lightweight pressure vessel with wings attached, required to survive 90,000 pressurisation cycles, gusts, hard landings, bird strikes, corrosion and mechanics with drills, while weighing as little as physically possible. The intellectual core is not static strength — that has been solvable since the 1930s — but **fatigue and damage tolerance**: the acceptance that cracks exist, will grow, and must be detected before they become critical. Two accidents wrote that philosophy into law: the Comet in 1954 and Aloha 243 in 1988. The materials half of the subject is the search for specific stiffness and specific strength at acceptable cost, corrosion resistance and manufacturability — a search that has moved the industry from aluminium to a 50 % composite airframe in one generation.

## Key facts

| Item | Value |
|---|---|
| Limit load | The maximum load expected in service; structure must not permanently deform (**14 CFR 25.305**) |
| Ultimate load | **1.5 × limit** (14 CFR **25.303** factor of safety); structure must not fail for 3 seconds |
| Transport category manoeuvre envelope | `n` = +2.5 to −1.0 (may reduce to +2.1 + 24,000/(W+10,000) for heavy aircraft) |
| Cabin differential, typical widebody | 8.6–9.4 psi (59–65 kPa); 787/A350 ≈ 8.6–9.4 psi permitting a 6,000 ft cabin |
| Pressurised compartment loads rule | **14 CFR 25.365** |
| Damage tolerance and fatigue rule | **14 CFR 25.571** |
| 787 material split by weight | **50 % composite, 20 % aluminium, 15 % titanium, 10 % steel, 5 % other**; ~80 % composite by volume; ≈ 77,000 lb (35 t) of CFRP per aircraft |
| A350 material split by weight | **53 % composites, 19 % aluminium and Al-Li, 14 % titanium, 6 % steel, 8 % misc.** |
| Comet water-tank failure | G-ALYU burst after **3,057 cycles** (1,221 real + 1,836 simulated) on **24 June 1954**, from a **bolt hole forward of the forward left escape hatch** |
| Aloha 243 | **28 April 1988**, Boeing 737-297 N73711, **19 years old, 35,496 flight hours, 89,680 cycles**; ~18 ft of upper fuselage departed; origin **multiple-site fatigue cracking at rivet holes in the S-10L lap joint** |

> ⚠️ Limit and ultimate load are certification terms with exact legal meanings. "The wing is designed to 1.5 g" is meaningless; the wing is designed to a limit load factor with a 1.5 factor of safety on top, and the structural test article is broken to prove it.

## 1. Load paths and the semi-monocoque airframe

The airframe's job is to carry four families of load into a single structural network:

1. **Aerodynamic loads** — wing lift and its spanwise distribution, tail balancing loads, control surface hinge moments, gust loads.
2. **Inertial loads** — mass × acceleration for the structure itself, fuel, payload, engines.
3. **Pressurisation** — hoop stress `σ_h = pr/t` and longitudinal `σ_l = pr/2t` in the fuselage shell, cycling once per flight.
4. **Ground loads** — landing gear reactions, braking, towing, jacking.

**Monocoque** carries all load in the skin; it works only for small, lightly loaded shells because a thin skin buckles at trivial compressive stress. **Semi-monocoque** — the universal solution since the 1930s — divides the work:

| Member | Direction | Carries |
|---|---|---|
| **Skin** | surface | Shear (from torsion and vertical shear), and pressure hoop tension |
| **Stringers / longerons** | spanwise/longitudinal | Axial load from bending; stabilise the skin against buckling |
| **Frames** (fuselage) / **ribs** (wing) | transverse | Maintain the cross-section shape, redistribute shear, introduce concentrated loads, and set the stringer/skin panel buckling length |
| **Spars** (wing) | spanwise | The bulk of the bending moment via the caps, and the vertical shear via the webs |
| **Bulkheads** | transverse, closed | Pressure boundary (the aft pressure bulkhead) and major load introduction (wing/fuselage joint) |

The analytical treatment is **thin-walled beam theory with boom idealisation**: lump the axial-load-carrying area into "booms" at stringer locations, treat the skin as carrying only shear flow `q = τt`, and solve. Shear flow in a closed single cell is `q = q_b + q_{s,0}` with `q_{s,0}` found from moment equilibrium about a convenient point; the **shear centre** is where a transverse load produces no twist. This is Megson chapters 16–23 and it is what a stress engineer actually does before running the FEM.

### The wing box

The structural wing is not the aerofoil; it is the **torsion box** between the front spar (typically 12–20 % chord) and the rear spar (55–70 % chord). Everything forward is the leading edge (slats, anti-ice ducting, sometimes a D-nose torsion box), everything aft is the trailing edge (flaps, ailerons, spoilers). The box carries:
- **Bending**: upper cover in compression, lower cover in tension. This asymmetry drives the material choice — the upper cover is a **compression/stability** problem (buckling, crippling) and historically used **7xxx** alloys for high compressive yield; the lower cover is a **tension/fatigue/damage-tolerance** problem and used **2xxx** alloys for better fracture toughness and crack growth.
- **Torsion**: closed-cell shear flow `q = T/2A_m` (Bredt–Batho), which is why any cut-out (access panels, gear bay) requires a heavy reinforcing frame.
- **Fuel**: the box is a wet tank, so every fastener is a sealing problem and every rib is a baffle.

Root bending moment is the design driver and scales roughly as `M_root ∝ L·b/4`; this is why span is structurally expensive and why the industry buys span with folding tips (777X) rather than paying for it in gate compatibility.

### The fuselage

A pressurised cylinder with the largest possible cut-outs in it (doors, windows, wheel well, wing carry-through). Hoop stress at 9 psi and 3 m radius on 1.6 mm skin: `σ = pr/t = 62,000 × 3.0/0.0016 ≈ 116 MPa` — modest statically, lethal in fatigue over 90,000 cycles. Structural detail therefore dominates: doublers around cut-outs, tear straps (circumferential bonded or integral straps at frame pitch, designed so that a longitudinal crack turns and flaps rather than unzipping the fuselage), and crack-arrest features.

## 2. Joints and fasteners

Joints are where structures fail. Analysis covers three failure modes for every mechanically fastened joint — **fastener shear**, **bearing** on the hole, and **net-section tension** through the fastener row — with a bypass/bearing interaction for fatigue.

| Fastener | Use |
|---|---|
| **Solid rivets** (2117-T4 "AD", 2024-T31 "DD" ice box) | Classic aluminium skin/stringer joining; driven, cheap, light |
| **Blind rivets / Cherrymax** | One-side access |
| **Hi-Lok / Hi-Lite** | Threaded pin + collar with a shear-off drive; the transport-aircraft workhorse for primary structure |
| **Lockbolt / Huck** | Swaged collar, very consistent preload, used in automated systems |
| **Interference-fit / cold-worked holes** | Split-sleeve cold expansion (Fatigue Technology Inc process) introduces compressive residual hoop stress at the hole, typically improving fatigue life 3–10× |
| **Titanium fasteners in CFRP** | Mandatory — steel and aluminium fasteners suffer galvanic corrosion against carbon fibre; Ti-6Al-4V or A286 with sealant and often a lightning-strike design (EME) requirement for cap sealing in fuel tanks |

**Bonded joints** distribute load more evenly (no stress concentration at holes) but are inspectable only by NDT, sensitive to surface preparation, and vulnerable to disbond and environmental degradation. The industry's compromise: bonded joints in secondary structure and in composite substructure; **bonded plus bolted** in primary structure where a certification credit for the bond cannot be obtained. The Aloha accident is precisely the story of a cold-bonded lap joint whose adhesive failed, throwing all load onto the rivets.

**Composite joint design** adds its own rules: no through-thickness strength, so peel must be designed out; bolt-bearing strength is lower than metal so joints get thicker and wider; ply drop-offs are stress raisers; and hole drilling must not delaminate the exit ply (hence back-up plates, dagger drills and orbital drilling).

## 3. Fatigue and damage tolerance philosophy

The regulatory history reads as three successive philosophies, each adopted after the previous one killed people.

### Safe life
Determine, by test, a life at which the probability of a fatigue crack is acceptably small; divide by a scatter factor (typically 3–5 on life); retire the part at that life regardless of condition. Still used where inspection is impossible or a crack is immediately catastrophic: **landing gear**, **engine discs and shafts** (life-limited parts, LLPs, tracked by cycle count on every engine), helicopter rotor components, some fittings. The weakness: it depends entirely on the test article representing the fleet, and it gives no protection against manufacturing defects or accidental damage.

### Fail safe
Design so that after the complete failure of any single principal structural element, the remaining structure carries a specified proportion of limit load until the damage is found. Achieved with multiple load paths, crack stoppers, and redundancy. This was the state of the art from the late 1950s. Its weakness — exposed by Aloha — is **multiple-site damage (MSD)**: many small cracks at adjacent rivet holes that link up simultaneously, so no single "failed element" ever exists and the fail-safe assumption is void.

### Damage tolerance (current)
Codified in **14 CFR 25.571** (and CS-25.571), *Damage-tolerance and fatigue evaluation of structure*. The assumption is that **the structure contains flaws from the day it is built**. The analysis:
1. Assume an initial flaw of a size just below reliable detection (typically a 1.27 mm / 0.05 in corner crack at a fastener hole).
2. Compute crack growth under the actual load spectrum using **linear elastic fracture mechanics**: `K = Yσ√(πa)`, growth per cycle by the **Paris law** `da/dN = C(ΔK)^m` (with `m ≈ 3–4` for aluminium alloys), including retardation from overloads if justified.
3. Determine the critical crack length `a_c` at which `K = K_IC` (or net-section yielding governs) under limit load.
4. Set the inspection interval to **half** (or less) the number of cycles from detectable to critical, so the crack is seen at least twice before it becomes dangerous.
5. Choose an inspection method whose **probability of detection** supports the assumed detectable size — visual, eddy current, ultrasonic, radiographic, thermography.

Bolted onto this since the 1990s are the **Widespread Fatigue Damage (WFD)** rules: an operator may not fly an aeroplane beyond its **Limit of Validity (LOV)** unless WFD has been evaluated and shown not to occur. In the US this came through the FAA's Aging Airplane Safety Rule and the **Widespread Fatigue Damage final rule (2010)**, which required TC holders to establish an LOV for each model — the direct regulatory descendant of Aloha.

**Practical numbers**: paris-law growth in 2024-T3 with `ΔK` around 10 MPa√m gives `da/dN` on the order of 10⁻⁸ m/cycle; the last 20 % of the life consumes 80 % of the crack length, which is why inspection intervals are set in the slow-growth region and why a crack found "just under the limit" is a much worse finding than it sounds.

## 4. The two accidents that wrote the rules

### de Havilland Comet, 1954
The world's first jet airliner suffered three catastrophic losses: **BOAC Flight 783 near Calcutta on 2 May 1953** (43 dead, initially attributed to structural failure in a severe thunderstorm), **BOAC Flight 781 off Elba on 10 January 1954** (35 dead), and **South African Airways Flight 201 near Naples on 8 April 1954** (21 dead).

The **RAE Farnborough water-tank test** — immersing a complete airframe (G-ALYU) in a tank and cycling the cabin pressure hydraulically, so a rupture would not explosively destroy the evidence — produced failure on **24 June 1954 after 3,057 cycles** (1,221 actual flights plus 1,836 simulated), roughly three times G-ALYP's life at the time of its loss. The rupture started **at a bolt hole forward of the forward left escape hatch**, propagated along a stringer at the widest point of the fuselage and then through the hatch cut-out. The Cohen Inquiry found the skin gauge insufficient to distribute load, overloading the frames adjacent to the cut-outs.

The design changes: **thicker skin, reinforced framing, rounded windows and access panels, strengthened cut-out areas**. The deeper legacy is the entire discipline of full-scale fatigue testing and the recognition that **stress concentration at a cut-out corner, plus repeated pressurisation, is the governing case for a pressurised fuselage.** Every airliner since has had a full-scale fatigue test article cycled to at least two (usually three) design service goals ahead of the fleet leader.

### Aloha Airlines Flight 243, 28 April 1988
A Boeing **737-297, N73711, 19 years old, with 35,496 flight hours and 89,680 cycles** — a cycle count far higher than the hours suggest, because of Hawaiian inter-island operations averaging well under 30 minutes. In the cruise at FL240 an approximately **18-foot section of the upper fuselage** separated, from just behind the cockpit to the fore-wing area. One flight attendant was swept out and killed; the crew landed at Kahului.

The failure initiated in the **lap joint along stringer S-10L** by **multiple-site fatigue cracking adjacent to rivet holes**. The NTSB probable cause: *"the failure of the Aloha Airlines maintenance program to detect the presence of significant disbonding and fatigue damage which ultimately led to failure of the lap joint,"* with contributing factors of inadequate FAA oversight and Boeing's failure to act comprehensively on the earlier discovery of **cold-bond lap joint durability problems**.

The mechanism is a cascade: the epoxy cold bond in the lap joint degraded and disbonded → the full hoop load transferred to the three rivet rows → the countersunk knife-edge at the upper rivet row concentrated stress → cracks initiated at many holes at once → MSD link-up defeated the fail-safe tear straps.

The consequences: the **Aging Aircraft programme**, the National Aging Aircraft Research Program, mandatory **Supplemental Structural Inspection Documents (SSIDs)** and Corrosion Prevention and Control Programmes for older aircraft, dozens of airworthiness directives on lap joints across the Boeing fleet, and ultimately the WFD/LOV rulemaking. It also killed cold bonding of primary lap joints outright.

## 5. Structural testing

| Test | Purpose |
|---|---|
| **Coupon and element tests** | Generate allowables (A-basis: 99 % of population at 95 % confidence; B-basis: 90 %/95 %). Thousands of specimens per new material system — the "building block" pyramid |
| **Sub-component tests** | Panels, joints, fittings — validate the analysis method before it is trusted on the full article |
| **Static test article** | Loaded to limit (no permanent deformation) then to **ultimate (150 % limit)** and usually to failure. The A350-900 static wing test and the 787's famous wing-up-bend test to 150 % (achieved in March 2010 at about 25 ft of tip deflection) are the public face of this |
| **Full-scale fatigue test article** | Cycled to 2–3 design service goals ahead of the fleet leader, with teardown inspection afterwards. Establishes inspection thresholds and intervals, and the LOV |
| **Ground vibration test (GVT)** | Establishes modes and frequencies for flutter clearance before first flight |
| **Bird strike, hail, tyre burst, engine burst, HIRF/lightning** | Discrete threat tests per 25.571(e), 25.631, 25.905, 25.903(d) |

## 6. Materials — with real property tables

### Aluminium alloys

Designation: 4 digits + temper. **2xxx** = Al-Cu (strong, tough, fatigue-resistant, poor corrosion, needs cladding). **7xxx** = Al-Zn-Mg-Cu (highest strength, notch- and SCC-sensitive). **6xxx** = Al-Mg-Si (extrusions, moderate). Tempers: **T3** solution treated + cold worked + naturally aged; **T4** solution treated + naturally aged; **T6** solution treated + artificially aged (peak strength); **T73/T7x** overaged (lower strength, far better SCC resistance); **T351** stress-relieved by stretching.

| Alloy / temper | Density (g/cm³) | E (GPa) | σ_y (MPa) | σ_UTS (MPa) | Elong. (%) | K_IC (MPa√m) | Typical use |
|---|---|---|---|---|---|---|---|
| **2024-T3** (sheet) | 2.78 | 73 | ≈ 345 | ≈ 483 | 18 | 30–37 (L-T) | Fuselage skin, lower wing skin — chosen for **fracture toughness and slow crack growth** |
| **2024-T351** (plate) | 2.78 | 73 | ≈ 325 | ≈ 470 | 19 | 32–37 | Machined structure, ribs, frames |
| **7075-T6** | **2.81** | ≈ 71.7 | **430–480** | **510–540** | **5–11** | 23–29 | Upper wing skin, stringers, fittings — highest strength, but **SCC-susceptible in the short-transverse direction** |
| **7075-T73** | 2.81 | ≈ 71.7 | **435** | **505** | **13** | 28–33 | Same applications where SCC resistance matters: the overaged temper grows larger precipitates preferentially at grain boundaries, mitigating SCC at a small strength cost |
| **7050-T7451** (thick plate) | 2.83 | 71 | ≈ 455 | ≈ 510 | 11 | 30–35 | Thick machined structure — better through-thickness properties and quench sensitivity than 7075 |
| **7150/7055-T77** | 2.85 | 71 | 570–615 | 600–655 | 8–11 | 22–27 | 777 upper wing skin — very high strength with acceptable toughness |
| **Al-Li 2195** | 2.71 | 76 | ≈ 545 | ≈ 580 | 8–10 | — | Space Shuttle Super Lightweight External Tank; SLS core stage |
| **Al-Li 2050 / 2196 / 2099** (3rd gen) | 2.70–2.72 | 76–78 | 440–520 | 490–560 | 7–12 | 30–38 | A350 and A380 structure, C-Series/A220 — roughly **3–5 % lower density and 5–8 % higher stiffness** than conventional 2xxx/7xxx, with far better anisotropy than the 1980s 2090/8090 generation |

Al-Li's economics: the alloy costs 2–3× conventional aluminium and machines away 90 % of the billet, but a 4 % density reduction with a 7 % modulus increase gives a compounding weight saving. Its resurgence (A220 fuselage skins, A350 frames, Falcon 9's tanks in 2195) was the aluminium industry's answer to CFRP.

**Cladding**: 2024 and 7075 sheet is commonly supplied "Alclad" — a thin layer of pure aluminium roll-bonded to each face, giving galvanic (sacrificial) protection. It costs a few percent of strength and is removed by any structural repair, which is why repairs need chemical conversion coating and primer.

### Titanium

| Alloy | Density (g/cm³) | E (GPa) | σ_y (MPa) | σ_UTS (MPa) | Elong. (%) | Notes |
|---|---|---|---|---|---|---|
| **Ti-6Al-4V (Grade 5)** | **4.43–4.51** | **104–113** | **880–920** | **900–950** | 5–18 | The workhorse: ~50 % of all titanium used. α-β alloy, heat-treatable, weldable, good to ≈ 400 °C |
| Ti-6Al-4V ELI (Grade 23) | 4.43 | 110 | 795–870 | 860–930 | 10–15 | Lower interstitials → higher fracture toughness and cryogenic capability |
| Ti-10V-2Fe-3Al | 4.65 | 110 | 1,100–1,200 | 1,200–1,300 | 6–10 | Forged landing gear (777, 787 main gear beams) |
| Ti-5553 | 4.65 | 110 | 1,100–1,200 | 1,200–1,300 | 6–10 | High-strength forgings |
| CP Ti (Grade 2) | 4.51 | 105 | 275 | 345 | 20 | Ducting, firewalls, exhaust shrouds |

Titanium is used where (a) temperature exceeds aluminium's 130–150 °C limit (engine pylons, APU compartments, bleed ducting, exhaust washed structure), (b) galvanic compatibility with CFRP is required (all fasteners and fittings mating to composite), or (c) strength-to-weight in a compact volume beats steel (landing gear). It is expensive because the Kroll process is energy-intensive and because the **buy-to-fly ratio** for machined titanium parts is often 10:1 or worse — which is precisely why additive manufacturing found its first business case here.

**Boeing 787 is 15 % titanium by weight; the A350 is 14 %** — up from ~6 % on the 777, entirely because of composite compatibility.

### Steels

| Steel | σ_UTS (MPa) | Use |
|---|---|---|
| **300M** (4340M) | 1,900–2,000 | Landing gear forgings; extremely notch-sensitive, requires shot peening and meticulous cadmium/IVD-aluminium plating (hydrogen embrittlement risk) |
| **4340** | 1,300–1,800 | Fittings, shafts |
| **15-5 PH / 17-4 PH** | 1,000–1,300 | Precipitation-hardening stainless fittings, actuator components |
| **A286** | 900–1,000 | High-temperature fasteners |
| **Aermet 100** | 1,930–2,000 | High-toughness landing gear alternative |
| **AISI 321/347, Inconel 625** | — | Ducting, firewalls, exhaust |

### Nickel superalloys (hot section)

| Alloy | Form | Max use temp | Notes |
|---|---|---|---|
| **Inconel 718** | Wrought/cast/AM | ≈ 650 °C | The most-used superalloy; discs, casings, fasteners; excellent weldability, prints well |
| **Waspaloy** | Wrought | ≈ 700 °C | Discs |
| **René 88DT, RR1000, ME3/LSHR** | Powder-metallurgy discs | 700–760 °C | Modern HPT discs; **this is the powder-metallurgy route in which contamination caused the PW1100G recall** |
| **CMSX-4, René N5, PWA 1484** | Single crystal, 2nd gen (~3 % Re) | ≈ 1,050 °C metal | HPT blades |
| **CMSX-10, René N6** | Single crystal, 3rd gen (~6 % Re) | ≈ 1,100 °C metal | Highest-temperature blades |
| **MAR-M 247, IN738** | Equiaxed / DS | 900–950 °C | Vanes, older blades |

With film cooling (effectiveness 0.65–0.75) plus a 7YSZ **thermal barrier coating** (100–400 µm, EB-PVD columnar for blades, APS for combustor liners), a 1,050 °C-capable alloy survives a 1,700–1,900 K gas stream.

### Composites

**Fibres:**

| Fibre | Tensile modulus (GPa) | Tensile strength (GPa) | Density (g/cm³) | Typical use |
|---|---|---|---|---|
| Standard modulus carbon (T300, AS4) | 230–240 | 3.5–4.4 | 1.76–1.79 | General structure |
| Intermediate modulus (IM7, T800) | 276–294 | 5.5–5.9 | 1.78–1.80 | Primary aerostructure — the 787/A350 workhorse |
| High modulus (M55J) | 540 | 4.0 | 1.91 | Space structures, satellite benches |
| E-glass | 72 | 3.4 | 2.55 | Radomes, fairings, secondary |
| Aramid (Kevlar 49) | 112 | 3.6 | 1.44 | Impact/ballistic, honeycomb core |

**Matrices:** thermoset epoxies (cure 120 °C or 180 °C; the 180 °C systems such as Hexcel 8552 and Cytec 977-3 are the primary-structure standard; toughened with thermoplastic particles in the interlayer to raise compression-after-impact), BMI (to 230 °C, engine nacelle regions), cyanate ester (space, low outgassing), and **thermoplastics** — PEEK, PEKK, and low-melt PAEK — which offer unlimited shelf life, no autoclave, weldability (induction, resistance, ultrasonic), and recyclability, and which are the current frontier for narrowbody structure (Airbus's Wing of Tomorrow and the Clean Aviation programmes are heavily thermoplastic).

**Laminate mechanics:** classical lamination theory gives the **ABD matrix** relating force and moment resultants to mid-plane strains and curvatures. Practical design rules that survive from that theory: use a **balanced and symmetric** stack to avoid extension–shear and extension–bending coupling; include at least 10 % of plies in each of the 0/±45/90 directions; keep ply-drop taper shallower than 1:20; never put a single ply direction at the surface for impact.

**Processing routes:**

| Route | Description | Where used |
|---|---|---|
| **Prepreg + autoclave** | Pre-impregnated tape/fabric laid up, vacuum-bagged, cured at 180 °C and 6–7 bar. Void content < 1 %, `V_f` ≈ 57–60 % | All current primary aerostructure; the 787 and A350 |
| **Automated tape laying (ATL)** | 75–300 mm tape laid on large flat/mildly contoured tools | Wing skins |
| **Automated fibre placement (AFP)** | 3.2–12.7 mm individual tows steered independently over complex 3-D surfaces; 16–32 tows per head | **787 one-piece fuselage barrels**, A350 fuselage panels, wing skins |
| **Out-of-autoclave (OOA/VBO)** | Vacuum-bag-only prepregs cured in an oven at 1 bar | Secondary structure, spacecraft, large single-piece parts where an autoclave does not exist |
| **RTM / RFI / VARTM** | Dry preform in a closed tool, resin injected | **CFM LEAP fan blades** are RTM; wing ribs, spars, brackets |
| **Filament winding** | Continuous fibre wound onto a mandrel | Pressure vessels, COPVs, rocket motor cases |
| **Press-formed / stamped thermoplastic** | Melt and stamp in minutes rather than cure in hours | Clips, brackets, ribs; the rate-enabling technology for future narrowbodies |

**The 787 and A350 fuselage decision** is the industry's most consequential composite trade. Boeing built the **787 fuselage as one-piece composite barrel sections** — the first production airliner to do so — eliminating the longitudinal splices and tens of thousands of fasteners; approximately 77,000 lb of CFRP per aircraft. Airbus built the **A350 fuselage from large CFRP panels bolted to composite frames** on an aluminium-free but panelised architecture — accepting the splices in exchange for easier repair, easier damage isolation, and lower tooling risk. Both are 50–53 % composite by weight. Neither approach has proved decisively better; the 787's barrel has better fastener count and the A350's panels have better repairability, and both fleets are performing.

**Damage and inspection**: the governing composite threat is **barely visible impact damage (BVID)** — a dropped tool or hail impact that leaves an almost invisible surface dent but a large internal delamination, cutting compressive strength by 40–60 %. Design allowables for compression are therefore set by **compression after impact (CAI)** on an impacted coupon, not by the pristine material. Inspection is ultrasonic (pulse-echo, phased array), thermography, or shearography — never visual alone for primary structure.

### Sandwich structures and honeycomb

A sandwich panel is the structural equivalent of an I-beam in two dimensions: thin, stiff facesheets carrying bending in-plane, separated by a light core carrying shear. Bending stiffness scales with the **square** of the core thickness for negligible weight, giving extraordinary specific stiffness.

| Core | Density (kg/m³) | Notes |
|---|---|---|
| **Nomex (aramid paper) honeycomb** | 29–144 | The aerospace standard: flight-control surfaces, floor panels, radomes, nacelle acoustic liners |
| **Aluminium honeycomb (5052/5056)** | 16–190 | Higher strength/stiffness, but corrodes if water enters and is not repairable in the field |
| **PMI foam (Rohacell)** | 31–200 | Isotropic, closed cell, easy to machine; good where honeycomb node bonds would be a concern |
| **Balsa** | 100–250 | Marine and wind, rare in aerospace |

Failure modes to design against: facesheet yielding, facesheet **wrinkling** and **dimpling** (intracell buckling), core shear, and core crushing at load introduction points (hence potted inserts). The chronic in-service problem is **water ingress** through damaged skins and the freeze–thaw disbond that follows — a common finding on flight-control surfaces and one reason full-depth composite is displacing honeycomb in new designs.

### Adhesives, coatings and corrosion protection

**Adhesives**: film adhesives (epoxy on a carrier, e.g. AF163-2, FM73) cured in the autoclave for structural bonds; two-part paste epoxies for repairs; polysulphide and polythioether sealants (PR-1440 class) for fuel tanks and faying surfaces. Surface preparation determines bond durability far more than adhesive choice — phosphoric acid anodising (PAA) for aluminium, peel-ply plus abrasion or plasma for composite.

**Corrosion**: aluminium airframes are protected by a layered system — Alclad or chemical conversion coating (formerly hexavalent chromate, now trivalent chromium under REACH pressure), a **chromate-free epoxy primer**, and a polyurethane topcoat, plus **corrosion-inhibiting compounds (CIC)** sprayed into faying surfaces and lap joints. Mechanisms to know: **galvanic** (CFRP is strongly cathodic to aluminium — the single most important compatibility rule in modern airframes), **pitting** (chloride, coastal and lavatory/galley areas), **crevice**, **exfoliation** (layered attack in wrought 7xxx along grain flow), **filiform** (under paint), **intergranular**, and **stress corrosion cracking** (7xxx in the short-transverse direction under sustained tension). **[NA]/[ZA]** Coastal southern African operation, with salt-laden air at Walvis Bay, Cape Town and Durban, materially accelerates all of these; CPCP intervals should assume a severe environment.

### Additive manufacturing in aerospace

| Process | Materials | Aerospace status |
|---|---|---|
| **Laser powder bed fusion (L-PBF/DMLS)** | Ti-6Al-4V, IN718, AlSi10Mg, Scalmalloy | The dominant metal AM route. **GE's LEAP fuel nozzle tip** consolidated 20 parts into 1, cut weight ~25 % and improved durability 5× — with well over 100,000 produced. Airbus, Boeing and the engine OEMs have thousands of qualified part numbers, almost all non-critical or secondary |
| **Electron beam melting (EBM)** | Ti-6Al-4V, TiAl | Better residual stress, rougher surface; used for TiAl LPT blades |
| **Directed energy deposition (DED/WAAM)** | Ti, steel, Inconel | Near-net-shape large parts and repair; buy-to-fly improvement is the business case |
| **Polymer (FDM/SLS) in ULTEM 9085, PEKK** | Flammability-compliant | Cabin brackets, ducting, tooling |
| **Binder jetting** | Steels, Inconel | Emerging; sintering shrinkage control is the barrier |

**The real qualification problem.** AM is not a material; it is a *process that creates the material as it creates the part*, which breaks the entire certification model. The specific obstacles:
1. **Anisotropy and build-orientation dependence** — properties differ between XY and Z by 5–20 %, so allowables must be generated per orientation.
2. **Porosity and lack-of-fusion defects** — statistically distributed, often sub-surface, and fatigue-critical. As-built fatigue strength can be **half** the wrought value; HIP (hot isostatic pressing) recovers much of it but not all.
3. **Surface roughness** — as-built Ra of 10–20 µm acts as a distributed notch; internal channels cannot be machined.
4. **Residual stress and distortion** — requires stress-relief cycles and careful support strategy.
5. **Powder provenance and reuse** — oxygen pick-up in recycled titanium powder changes properties; lot traceability rules are onerous.
6. **Machine-to-machine and even laser-to-laser variability** — the same file on two "identical" machines does not produce identical material, so qualification is per machine, per parameter set, per powder lot.
7. **NDT** — internal lattice and channel geometries cannot be inspected by conventional UT/RT; CT scanning is the only real option, and it is slow and size-limited.

The consequence: after fifteen years, AM in flight-critical primary structure and rotating hot-section parts remains rare. Where it has won decisively is **complex static hot-section hardware** (fuel nozzles, heat exchangers, brackets, ducting), **rocket engines** (SpaceX SuperDraco, Relativity's approach, Rocket Lab's Rutherford chamber), and **spares and obsolescence** — where the alternative is no part at all. The FAA and EASA have both issued AM guidance and are progressing rulemaking, but the underlying difficulty is real and will not be regulated away.

## Sources

- [7075 aluminium alloy](https://en.wikipedia.org/wiki/7075_aluminium_alloy) — Wikipedia
- [Ti-6Al-4V](https://en.wikipedia.org/wiki/Ti-6Al-4V) — Wikipedia
- [de Havilland Comet](https://en.wikipedia.org/wiki/De_Havilland_Comet) — Wikipedia
- [Aloha Airlines Flight 243](https://en.wikipedia.org/wiki/Aloha_Airlines_Flight_243) — Wikipedia
- [Boeing 787 Dreamliner](https://en.wikipedia.org/wiki/Boeing_787_Dreamliner) — Wikipedia
- [Airbus A350](https://en.wikipedia.org/wiki/Airbus_A350) — Wikipedia
- [14 CFR Part 25](https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-25) — eCFR (Subpart C Structure; §§25.303, 25.305, 25.365, 25.571)

## Open questions

- Property values marked with ranges (2024-T3 `K_IC`, 7050, 7150/7055, Al-Li 2050/2196, the steels and superalloys) are typical handbook values, **not design allowables**. Real design uses **MMPDS** (formerly MIL-HDBK-5) A- or B-basis allowables at the specific product form, thickness and grain direction. Treat every number here as indicative — `needs-verification` against MMPDS for any engineering use.
- 2024-T3 and 7050-T7451 values were not fetched from a primary source in this session — `needs-verification`.
- The FAA Widespread Fatigue Damage final rule date (given as 2010) was not re-verified in this session — `needs-verification`.
- The GE LEAP fuel nozzle production count is a manufacturer claim repeated widely; exact current figure `needs-verification`.

