---
id: aerospace.propulsion
title: Propulsion — piston, gas turbine, ramjet and beyond
domain: 29_aerospace_engineering
tags: [propulsion, brayton, turbojet, turbofan, turboprop, turboshaft, ramjet, scramjet, compressor, surge, combustor, turbine-cooling, nozzle, sfc, single-crystal, thermal-barrier-coating, ge-aerospace, rolls-royce, pratt-whitney, cfm, hydrogen, hybrid-electric]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "General Electric GE9X", url: "https://en.wikipedia.org/wiki/General_Electric_GE9X", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "CFM International LEAP", url: "https://en.wikipedia.org/wiki/CFM_International_LEAP", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Pratt & Whitney PW1000G", url: "https://en.wikipedia.org/wiki/Pratt_%26_Whitney_PW1000G", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Rolls-Royce UltraFan", url: "https://en.wikipedia.org/wiki/Rolls-Royce_UltraFan", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "CFM RISE", url: "https://en.wikipedia.org/wiki/CFM_RISE", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Airbus ZEROe", url: "https://en.wikipedia.org/wiki/Airbus_ZEROe", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Airbus A350", url: "https://en.wikipedia.org/wiki/Airbus_A350", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "MIT Course 16 subject listing", url: "http://student.mit.edu/catalog/m16a.html", publisher: "MIT", accessed: 2026-08-25}
related: [aerospace.aerodynamics, aerospace.structures, aerospace.curriculum, aerospace.certification]
unit_system: SI
---

# Propulsion — piston, gas turbine, ramjet and beyond

**Summary.** An aircraft propulsion system's job is to add momentum to a stream of air. Everything else — the cycle, the materials, the blade cooling, the gearbox — exists to do that at acceptable fuel burn, weight, cost and reliability. The dominant trend of the last fifty years is unambiguous: accelerate more air, more gently. That is the entire story of bypass ratio going from 0 (turbojet) to 12–15 (GTF, UltraFan) and to the unducted "open fan" now being tested. The second trend is thermodynamic: raise the cycle temperature and pressure ratio, which is a materials problem, not a fluids problem, and which is why single-crystal nickel superalloys and ceramic matrix composites decide who wins.

## Key facts

| Quantity | Relation / value |
|---|---|
| Thrust (uninstalled) | `F = ṁ_e V_e − ṁ_0 V_0 + (p_e − p_0) A_e` |
| Propulsive efficiency | `η_p = 2/(1 + V_e/V_0)` — approaches 1 as `V_e → V_0` |
| Thermal efficiency | `η_th = (½ṁ_eV_e² − ½ṁ_0V_0²)/(ṁ_f · LHV)` |
| Overall efficiency | `η_o = η_p · η_th = F V_0/(ṁ_f LHV)` |
| TSFC ↔ efficiency | `TSFC = V_0/(η_o · LHV)` |
| Ideal Brayton thermal efficiency | `η_th = 1 − 1/π^{(γ−1)/γ}` with π = OPR |
| Jet A / Jet A-1 LHV | **≈ 43.0–43.2 MJ/kg** |
| Jet A-1 density | ≈ 0.775–0.840 kg/L (nominal 0.80 at 15 °C) |
| Modern turbofan cruise TSFC | **0.50–0.56 lb/(lbf·h)** ≈ **14.2–15.9 g/(kN·s)** |
| 1960s turbojet cruise TSFC | 0.85–0.95 lb/(lbf·h) |
| Modern OPR | LEAP ≈ 40–50; PW1100G ≈ 42; **GE9X = 61:1**; UltraFan target 70:1 |
| Modern BPR | CFM56 ≈ 5.5; LEAP ≈ 9–11; **PW1100G = 12.2:1**; **GE9X = 10:1**; UltraFan target 15:1 |
| Turbine entry temperature (TET/T4) | Take-off **1,700–1,900 K** on current large engines; metal melting ≈ 1,600 K |
| Turbofan thrust lapse with altitude | roughly `F ∝ (ρ/ρ₀)^{0.7–1.0}` at fixed Mach |

> ⚠️ Thrust ratings are certified quantities under 14 CFR Part 33 / CS-E and are defined at a specific reference condition. A "110,000 lbf" GE9X does not produce that at 35,000 ft — it produces roughly a fifth of it, which is exactly why the top-of-climb and one-engine-inoperative cases size the engine, not take-off.

## 1. Piston engines — still the general-aviation baseline

Aircraft piston engines are almost all **horizontally opposed, air-cooled, direct-drive, spark-ignition** four-strokes running on 100LL avgas: Lycoming O-320/O-360/IO-540, Continental O-200/IO-360/IO-550. Typical specific power is poor by automotive standards (≈ 0.4–0.6 kW/kg) because the design is optimised for reliability, TBO (1,800–2,200 h) and simplicity, and because the propeller caps useful RPM at ~2,700.

Key thermodynamics: the **Otto cycle**, `η_th = 1 − r^{-(γ−1)}` with compression ratio `r ≈ 7–8.5` (limited by detonation on avgas, hence the lead). Power falls with density: normally aspirated engines lose roughly 3 % per 1,000 ft; turbocharging restores sea-level manifold pressure to a critical altitude, at the cost of exhaust back-pressure, intercooling and heat.

The current transitions: **Jet-A burning compression-ignition aero-diesels** (Continental CD-155/CD-300, Austro AE300 in the Diamond DA40/DA42/DA62) with FADEC single-lever control and 25–40 % lower fuel burn; and the slow replacement of 100LL by unleaded (GAMI G100UL received an FAA STC in 2022; Swift Fuels UL94/100R progressing) — a genuine 2026 operational issue for training fleets.

Propeller efficiency is the other half: `η_prop = T·V/P_shaft`, peaking at 0.80–0.88 for a well-matched constant-speed unit, collapsing when the tip Mach exceeds ~0.88 (why 2,700 RPM and 76-inch diameters coexist).

## 2. The Brayton cycle with real numbers

Station numbering (SAE ARP755): 0 free stream, 2 fan/compressor face, 13 fan exit, 25 booster exit, 3 HP compressor exit, 4 combustor exit (turbine entry), 45 LPT entry, 5 turbine exit, 9 nozzle exit.

**Ideal cycle**, `η_th = 1 − π^{-(γ−1)/γ}`. At OPR 40 and γ = 1.4 this is 0.647; at OPR 61 (GE9X) it is 0.702. Real engines fall short because of component inefficiency and cooling air.

### Worked example: a modern high-bypass turbofan at cruise

Take a representative large turbofan at **FL350, ISA, M 0.85**. Ambient `T₀ = 218.8 K`, `p₀ = 23.84 kPa`, `a = 296.5 m/s`, `V₀ = 252 m/s`.

1. **Ram**: `T_{t0} = T₀(1 + 0.2M²) = 218.8 × 1.1445 = 250.4 K`; `p_{t0} = p₀(1.1445)^{3.5} = 23.84 × 1.6011 = 38.2 kPa`.
2. **Inlet**: assume `π_d = 0.995`, so `p_{t2} = 38.0 kPa`, `T_{t2} = 250.4 K`.
3. **Fan**, `π_f = 1.55`, polytropic efficiency `e_f = 0.92`:
   `T_{t13} = 250.4 × 1.55^{(0.2857/0.92)} = 250.4 × 1.1441 = 286.5 K`. Fan work `= c_p ΔT = 1005 × 36.1 = 36.3 kJ/kg`.
4. **Core compression** to overall `π_c = 40` (i.e. HPC+booster pressure ratio 40/1.55 = 25.8), `e_c = 0.90`:
   `T_{t3} = 286.5 × 25.8^{0.3175} = 286.5 × 2.848 = 816 K`; `p_{t3} = 38.0 × 40 = 1,520 kPa`.
5. **Combustor**: `T_{t4} = 1,550 K` at cruise (take-off would be ~1,800 K), `π_b = 0.96`, `η_b = 0.995`.
   Fuel–air ratio `f = c_p(T_{t4} − T_{t3})/(η_b·LHV − c_p T_{t4}) ≈ 1148×(1550−816)/(0.995×43.0×10⁶ − 1148×1550) ≈ 842,600/41.0×10⁶ ≈ 0.0205`.
6. **HP turbine** drives the HP compressor: `ΔT_{HPT} = c_{p,c}(T_{t3} − T_{t25})/((1+f) c_{p,h})`. With cooling air bleed of ~20 % of core flow this is where real analysis gets messy; a first-order answer gives `T_{t45} ≈ 1,090 K`.
7. **LP turbine** drives the fan; for BPR = 10 the fan work per unit *core* mass is `(1+BPR) × 36.3 = 399 kJ/kg`, requiring `ΔT_{LPT} ≈ 399/1148 ≈ 348 K`, so `T_{t5} ≈ 742 K`.
8. **Nozzles**: expanding the bypass stream from `p_{t13} = 58.9 kPa` to ambient 23.84 kPa gives a pressure ratio of 2.47 — above the critical 1.89, so the fan nozzle is **choked** at cruise, exit `M = 1`, `V_{13} ≈ 310 m/s`. Core jet velocity comes out around 400 m/s.
9. **Specific thrust and efficiency**: mass-averaged `V_e ≈ (10×310 + 1×400)/11 = 318 m/s`.
   `η_p = 2/(1 + 318/252) = 2/2.262 = 0.884`.
   That 88 % propulsive efficiency is the entire justification for high bypass. A 1960s turbojet with `V_e = 600 m/s` at the same flight speed gets `η_p = 2/(1+2.38) = 0.59`.
10. Overall efficiency `η_o = η_p η_th ≈ 0.884 × 0.45 ≈ 0.40`, giving `TSFC = V₀/(η_o LHV) = 252/(0.40 × 43×10⁶) = 1.465×10⁻⁵ kg/(N·s) = 14.65 g/(kN·s) ≈ 0.517 lb/(lbf·h)`. That is the right neighbourhood for a current-generation engine.

The lesson buried in the arithmetic: **`η_th` is bought with OPR and TET (materials), `η_p` is bought with BPR (fan diameter, nacelle drag, weight, gearbox)**. The two fight each other through the core size, and the optimum has been moving toward bigger fans and smaller cores for fifty years.

## 3. Engine architectures

| Architecture | BPR | Best speed range | Where used |
|---|---|---|---|
| **Turbojet** | 0 | M 0.8–2.2 | Historic transports (Comet, 707-120), supersonic military, Concorde (Olympus 593 with reheat) |
| **Low-bypass turbofan** | 0.3–1.5 | M 0.9–2.0 | Fighters (F110, EJ200, F135), older bizjets |
| **High-bypass turbofan** | 4–9 | M 0.75–0.9 | CFM56, V2500, PW4000, Trent 700/800 |
| **Ultra-high-bypass (UHB)** | 9–15 | M 0.78–0.89 | LEAP, PW1000G GTF, GE9X, Trent XWB/7000, UltraFan |
| **Open rotor / open fan** | 25–40 (effective) | M 0.7–0.8 | CFM **RISE** (single-stage open rotor + stator, variable pitch, tractor, with a recuperator; targeting ~20 % fuel-burn reduction; announced June 2021, first rotating component tests June 2023, flight tests planned 2026 on an Airbus A380 testbed, service entry mid-2030s) |
| **Turboprop** | (propeller) | M 0.35–0.65 | PW127 (ATR), PW100/150 (Dash 8), TPE331, GE Catalyst |
| **Turboshaft** | (rotor) | helicopter | RTM322, T700, Arriel, PW200 |
| **Ramjet** | n/a | M 2–5 | Missiles (Meteor uses a throttleable ducted rocket), SR-71's J58 in ram mode |
| **Scramjet** | n/a | M 5–15 | X-43A (M 9.6, 2004), X-51A (M 5.1, 210 s, 2013); no operational vehicle |

**Turbofan spool arrangements.** Two-spool (GE, CFM, P&W) versus three-spool (Rolls-Royce Trent family: separate IP compressor/turbine shaft) versus **geared** (Pratt's PW1000G: a 3:1 planetary reduction gear lets the fan turn at ~3,250 RPM while the LP turbine spins fast and efficient). Rolls-Royce's **UltraFan** combines a geared architecture with a very large fan — its **power gearbox has been tested to 64 MW (86,000 hp)** as of March 2022 (52 MW in 2017), the demonstrator first ran in **May 2023** and reached at least 85,000 lbf (380 kN) by November 2023, with a target BPR of 15:1 and OPR 70:1, claimed 10 % better fuel efficiency than the Trent XWB and at least 25 % better than the first-generation Trent.

**Turboprop performance**: rate on shaft power, and quote **equivalent shaft horsepower (ESHP)** including residual jet thrust. Thermodynamically it is a turboshaft plus a propeller, so `η_o = η_th × η_gearbox × η_prop`. The propeller gives very high propulsive efficiency at low speed (the reason an ATR 72 burns roughly half what a similarly sized jet does on a 300 nm sector) and collapses above M ≈ 0.65 from tip compressibility.

## 4. Components

### Inlet
Subsonic inlets diffuse from flight Mach to `M ≈ 0.5` at the fan face with pressure recovery `π_d = 0.98–0.995`. The design problem is off-design: at high angle of attack and low speed the lip must not separate internally (hence the thick, drooped lower lip), and at cruise the external cowl must not go supersonic and shock. Distortion (DC60 index) at the fan face causes stall — hence the crosswind testing every new engine undergoes.

Supersonic inlets must decelerate through shocks with minimum total-pressure loss: **pitot** (normal shock, adequate to M 1.6), **external compression** with ramps or a spike (Concorde, F-15), **mixed compression** (SR-71's translating spike; the famous "unstart" is the terminal shock being expelled). Recovery is codified by MIL-E-5008B: `π_d = 1 − 0.075(M−1)^{1.35}` for M > 1.

### Compressor
Axial compressors: 8–15 stages, per-stage pressure ratio 1.15–1.45, polytropic efficiency 0.90–0.92. Governing relation is the **Euler turbomachinery equation** `w = U(c_{θ2} − c_{θ1})`, with the diffusion factor and de Haller criterion (`w₂/w₁ > 0.72`) limiting how much a stage can decelerate the relative flow before separating.

**Stall and surge** are the defining failure mode. Rotating stall is a local cell of separated flow propagating around the annulus at ~40–50 % of rotor speed; **surge** is a full annulus flow breakdown with axial flow reversal — audible as a bang, visible as flame out the intake, and dangerous. The surge line on the compressor map sits above the operating line; the **surge margin** is the distance between them. Margin is consumed by: acceleration (fuel added faster than the compressor can pump), inlet distortion, deterioration, ice or bird ingestion, and hot gas re-ingestion. It is protected by **variable inlet guide vanes and variable stator vanes** (on the front stages), **bleed valves** (dumping air overboard at low speed), **multiple spools** running at their own optimal speeds, and FADEC acceleration schedules.

Centrifugal compressors give a pressure ratio of 4–8 in one stage, are short and robust, and are used in small engines (PT6, TPE331, APUs) and as the last stage of some axi-centrifugal designs.

### Combustor
Requirements: complete combustion over a 40:1 fuel-flow range, total-pressure loss under 5 %, exit temperature traverse quality tight enough not to burn turbine blades, stable relight up to 30,000 ft, and low NOx/CO/UHC/smoke to ICAO Annex 16 Volume II limits.

Architecture: annular, with about 20–35 % of the air through the swirler into the primary zone at near-stoichiometric conditions, the rest entering as intermediate and dilution air through the liner, plus film cooling. Modern low-NOx designs are **lean-burn**: GE's **TAPS** (Twin Annular Premixing Swirler) on the GEnx/LEAP, Rolls-Royce's ALECSys/lean-burn, P&W's TALON X. The trade is that lean-burn reduces NOx but narrows the stability margin and complicates altitude relight. CMC liners (GE9X) let the liner run hotter with less cooling air, and cooling air not spent is thrust.

### Turbine
The HP turbine inlet is the hottest, most highly stressed component in engineering. Take-off TET of 1,700–1,900 K sits several hundred kelvin above the melting point of the nickel superalloy the blade is made from. It survives through three technologies stacked:

1. **Single-crystal casting.** Equiaxed → directionally solidified (DS, columnar grains aligned with the centrifugal load) → **single crystal (SX)**, eliminating grain boundaries entirely and with them the dominant creep and fatigue path. Alloys: CMSX-4, René N5, PWA 1484 (2nd generation, with ~3 % Re); CMSX-10, René N6 (3rd generation, ~6 % Re); Ru-bearing 4th generation. Rhenium content is the currency, and its supply is a genuine strategic constraint.
2. **Internal and film cooling.** Serpentine internal passages with turbulators and pin fins, impingement cooling of the leading edge, and hundreds of shaped film-cooling holes (fan-shaped diffusers) laid down by EDM or laser drilling. Cooling effectiveness `η = (T_g − T_w)/(T_g − T_c)` reaches 0.65–0.75, buying 300–400 K. The cost: 15–25 % of core compressor flow bypasses the combustor, and every kilogram of it is a thermodynamic penalty.
3. **Thermal barrier coatings (TBC).** A MCrAlY or platinum-aluminide bond coat plus a 100–400 µm **yttria-stabilised zirconia** (7YSZ) top coat applied by APS or EB-PVD, giving a further 100–170 K of metal-temperature reduction. Failure is by bond-coat oxidation (TGO growth) and spallation, accelerated by **CMAS** (calcium–magnesium–alumino-silicate) attack from ingested sand and volcanic ash — an operationally relevant issue in the Gulf, where every departure ingests desert dust.

The next step is **ceramic matrix composite (CMC)** — SiC/SiC with a BN interphase and an environmental barrier coating. The **GE9X contains 65 CMC components, more than any commercial engine at the time of its introduction**, in the combustor liner, nozzles and turbine shrouds, running about **500 °F (260 °C) hotter than nickel alloys** while weighing roughly a third as much. **Titanium aluminide (TiAl)** low-pressure turbine airfoils, also on the GE9X and GEnx, are lighter and stronger than the nickel parts they replace, which cascades into a lighter disc and a lighter shaft.

### Nozzle
Convergent for subsonic engines (choked at most operating points, giving pressure thrust); convergent–divergent with variable geometry for supersonic and reheated engines. Thrust reversers are part of the nozzle system: **cascade type** (translating sleeve and blocker doors) on turbofans, **clamshell/target** on some smaller engines, and **propeller reverse pitch** on turboprops. Reverser efficiency is only 30–50 %, which is why reverse thrust is a nice-to-have and not credited in certified landing distance under Part 25 for dry runways.

## 5. Performance parameters that matter operationally

- **Thrust rating structure**: take-off (5 min, or 10 min OEI), maximum continuous, max climb, max cruise. Flat-rating means the engine holds a constant thrust up to a corner-point ambient temperature (typically ISA+15 to ISA+30) by throttling back at lower temperatures — which is where derate and assumed-temperature reductions come from and why they extend on-wing life so dramatically. A 1 % reduction in EGT margin consumption compounds over thousands of cycles.
- **EGT margin**: the difference between actual take-off EGT and the certified redline. It erodes with deterioration (tip clearances opening, seal wear, fouling) and its exhaustion — not a hard failure — is what sends an engine to the shop.
- **Specific fuel consumption** at cruise is the number that determines the aircraft's economics; a 1 % TSFC improvement is worth roughly 0.7 % block fuel.
- **Bleed and power extraction**: every kg/s of customer bleed and every kW of generator load shows as an SFC penalty. The 787's bleedless architecture (electric ECS, electric wing anti-ice) exists precisely to move this trade.

## 6. The manufacturers and their current families

| Manufacturer | Current commercial families | Notes |
|---|---|---|
| **GE Aerospace** | **GE9X** (777X): 110,000 lbf / 490 kN, BPR **10:1**, OPR **61:1**, fan case **134 in / 340 cm**, only **16** composite fan blades, 65 CMC parts, TiAl LPT airfoils; **FAA type certificate 25 September 2020**; designed for 10 % better fuel efficiency than the GE90 and ~5 % lower TSFC than the Trent XWB-97. Also GEnx (787, 747-8), GE90, CF34, Passport, and the GE Catalyst turboprop | Separated from GE in April 2024 as a standalone company |
| **CFM International** (GE + Safran, 50/50) | **LEAP-1A** (A320neo, 106.8 kN / 24,010 lbf take-off), **LEAP-1B** (737 MAX, exclusive), **LEAP-1C** (C919); BPR ≈ 9–11; **RTM (resin transfer moulded) woven carbon-fibre fan blades**, CMC HPT shrouds, 3-D printed fuel nozzles; **~15 % less fuel and 15 % less CO₂ than the CFM56**; LEAP-1A/-1C 180-minute ETOPS approval **19 June 2017**. Plus the legacy CFM56, still the highest-volume jet engine ever built | The LEAP-1B HPT durability issue in hot-and-harsh environments (Middle East, India) drove an HPT blade redesign; on-wing life in Gulf operations remains materially shorter than in temperate operations |
| **Pratt & Whitney (RTX)** | **PW1000G GTF**: PW1100G-JM (A320neo, 27,000–34,000 lbf / 120–151 kN, **BPR 12.2:1**, OPR ≈ 42, **3:1 reduction gear**, fan ≈ 81 in, FAA TC **19 December 2014**); PW1500G (A220, 22,550–24,400 lbf, TCCA TC **20 February 2013**, gear 1:3.0625, fan nominal 3,461 RPM); PW1900G (E-Jet E2). Claimed **16 % lower fuel burn** than the prior generation. Also PW4000, PW800, F135 | The **powder-metal contamination** problem: in **July 2023** P&W ordered inspection of **1,200 of 3,000** PW1100G engines for contaminated powdered metal causing cracked HPT discs and hubs; by **September 2023** it was extended to all 3,000. The resulting AOG wave grounded a large share of the A320neo GTF fleet through 2024–2025 and is the defining supply-chain story of the decade |
| **Rolls-Royce** | Trent XWB (**84,000 lbf / 370 kN** baseline for the A350-900, **97,000 lbf / 430 kN** for the A350-1000; regional variants at 75,000 and 79,000 lbf), Trent 7000 (A330neo), Trent 1000 (787), Trent 700/800/900, BR725, Pearl 10X/15X/700; **UltraFan** demonstrator | The Trent 1000 Package C IPT blade corrosion-fatigue crisis (2016–2021) grounded large parts of the 787 fleet and cost RR well over £2 bn. Three-spool architecture historically; UltraFan is geared |
| **Safran Aircraft Engines** | CFM 50 % share, M88 (Rafale), Ardiden/Arrano/Arriel (helicopters via Safran Helicopter Engines), Silvercrest (cancelled for the Citation Hemisphere) | Also nacelles, landing gear, wiring, electrical |
| **MTU Aero Engines** | Risk-and-revenue partner: HPC and LPT modules on the PW1000G family, LPT on the GEnx and GP7000; large MRO network | Germany's engine centre of gravity |
| **IAE International Aero Engines** | V2500 for the A320ceo family and MD-90 | P&W / MTU / JAEC consortium |
| **Honeywell, Williams, GE (small)** | APUs (131-9, HGT1700), business-jet turbofans (HTF7000, FJ44), TPE331 | |

## 7. Ramjets and scramjets

A **ramjet** replaces the compressor with ram compression: `p_{t}/p = (1 + 0.2M²)^{3.5}` gives a pressure ratio of 7.8 at M 2 and 36 at M 3, so no turbomachinery is needed above roughly M 2 — but it produces zero static thrust and must be boosted. Combustion is subsonic behind a terminal normal shock; above about M 5–6 the post-shock temperature is high enough that dissociation eats the energy release, and total pressure loss becomes crippling.

A **scramjet** keeps the flow supersonic through the combustor, so the static temperature stays lower. The engineering problem is that the fuel must mix and burn in of order a millisecond of residence time, the whole vehicle forebody is the inlet and the aftbody is the nozzle (so aero and propulsion cannot be separated), and the structure must survive stagnation temperatures above 2,000 K. Flight record: **NASA X-43A reached M 9.6 in November 2004** for about 10 seconds; the **Boeing X-51A Waverider** achieved M 5.1 for **210 seconds** in May 2013. Nothing operational exists; hypersonic weapons in service are boost-glide vehicles, not air-breathing.

## 8. Electric, hybrid-electric and hydrogen — an honest maturity assessment

**The energy-density problem, stated plainly:**

| Energy store | Specific energy (MJ/kg) | Usable at pack/system level |
|---|---|---|
| Jet A-1 | **43.0** | ~43 × engine efficiency (0.40) = 17 MJ/kg propulsive |
| Best current Li-ion cell | 0.9–1.1 (250–300 Wh/kg) | Pack level 0.65–0.85; × motor/inverter efficiency (0.90) = ~0.7 MJ/kg |
| Li-S / advanced (lab) | 1.4–1.8 (400–500 Wh/kg) | Not qualified, cycle life poor |
| **Liquid hydrogen** | **120 (LHV)** | But density 71 kg/m³ → 8.5 MJ/L vs Jet A's 34.7 MJ/L; needs cryogenic tanks at 20 K with insulation and boil-off management |

A battery-electric aircraft therefore carries roughly **25 times less usable energy per kilogram** than a kerosene one. That is not an incremental gap; it is a categorical one. The honest conclusions:

- **Battery-electric**: viable for 2–19 seat, sub-250 nm missions and for training. Real certified progress: the **Pipistrel Velis Electro** received an EASA type certificate on **10 June 2020** — the world's first type-certified electric aircraft — with about 50 minutes of endurance. Beyond that: Eviation Alice (first flight September 2022, programme subsequently restructured), Heart Aerospace ES-30 (now hybrid, precisely because pure-electric could not close). No credible path to a battery-electric narrowbody.
- **Hybrid-electric**: two flavours. *Series/parallel hybrid* for regional aircraft (a turbogenerator charging/assisting electric propulsors) — modest fuel benefit, big weight and cooling penalties, thermal management is the unglamorous killer. *Distributed electric propulsion* (NASA X-57 Maxwell, cancelled in June 2023 before crewed flight) promised high-lift blowing benefits that were real but did not offset system mass. **eVTOL** (Joby, Archer, Beta, Vertical, Lilium — the last of which entered insolvency proceedings in late 2024) is the one place electric propulsion is genuinely enabling, because the mission is short and the alternative (a turbine helicopter) is expensive and noisy.
- **Hydrogen combustion**: burning H₂ in a modified gas turbine is thermodynamically straightforward — the combustor and fuel system change, the turbomachinery mostly does not. NOx can be lower with lean premixed combustion, and there is no CO₂ and no soot. The problems are volumetric (a cryogenic tank of 4× the volume of the kerosene it replaces, which cannot be in the wing, which means a fatter fuselage and more drag), the boil-off and safety case, contrail/water-vapour effects at altitude, and the absence of any green-hydrogen airport infrastructure. **Airbus unveiled three ZEROe liquid-hydrogen concepts in September 2020 targeting a 2035 entry into service; at the Airbus Summit in March 2025 the company delivered updates on the programme**, and press reporting since has described a slip in the timeline and a shift of emphasis toward fuel cells — the exact revised entry-into-service date is `needs-verification`.
- **Hydrogen fuel cells**: higher efficiency (50–60 %) than combustion but low specific power at the system level once the stack, humidification, compressor, and — critically — the **heat rejection** are included; a fuel cell rejects its waste heat at ~80 °C, which needs an enormous radiator and its drag. ZeroAvia and others have flown demonstrators in the 6–19 seat class.
- **SAF (sustainable aviation fuel)** is the only near-term lever that scales: drop-in, certified under ASTM D7566 with several approved pathways (HEFA is the only one at meaningful volume), currently approved for blends up to 50 % with 100 % SAF flights demonstrated and certification work in progress. Its constraint is feedstock and price, not technology. For a 2026 airline, SAF plus fleet renewal plus operational efficiency is the whole realistic decarbonisation portfolio to 2040.

**The realistic 2030s propulsion picture**: evolved UHB turbofans (UltraFan-derived, next-generation LEAP), the **CFM RISE open fan** if the noise and installation problems close, SAF blending rising, hydrogen confined to regional demonstrators, and hybrid-electric confined to sub-50-seat and eVTOL. Anyone promising a hydrogen narrowbody in service before 2040 is selling something.

## Sources

- [General Electric GE9X](https://en.wikipedia.org/wiki/General_Electric_GE9X) — Wikipedia
- [CFM International LEAP](https://en.wikipedia.org/wiki/CFM_International_LEAP) — Wikipedia
- [Pratt & Whitney PW1000G](https://en.wikipedia.org/wiki/Pratt_%26_Whitney_PW1000G) — Wikipedia
- [Rolls-Royce UltraFan](https://en.wikipedia.org/wiki/Rolls-Royce_UltraFan) — Wikipedia
- [CFM RISE](https://en.wikipedia.org/wiki/CFM_RISE) — Wikipedia
- [Airbus ZEROe](https://en.wikipedia.org/wiki/Airbus_ZEROe) — Wikipedia
- [Airbus A350 (Trent XWB thrust ratings)](https://en.wikipedia.org/wiki/Airbus_A350) — Wikipedia
- [MIT Course 16 subject listing (16.50, 16.511, 16.512, 16.522, 16.540)](http://student.mit.edu/catalog/m16a.html) — MIT

## Open questions

- The revised Airbus ZEROe entry-into-service date and architecture decision following the March 2025 Airbus Summit — `needs-verification`.
- LEAP-1A/-1B fan diameters, blade counts and exact OPR figures per variant were not confirmed from the manufacturer; values quoted as ranges — `needs-verification`.
- Take-off turbine entry temperatures for specific current engines are not published by manufacturers; the 1,700–1,900 K range is the accepted open-literature figure.
- Cruise TSFC values are representative, not certified figures for any named engine.
- Current status of the PW1100G powder-metal inspection programme (completion, remaining AOG count in 2026) — `needs-verification`.

