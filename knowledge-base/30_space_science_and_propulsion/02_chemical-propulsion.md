---
id: space.chemical-propulsion
title: Chemical rocket propulsion
domain: 30_space_science_and_propulsion
tags: [propulsion, rocket-engines, nozzles, specific-impulse, staged-combustion, propellants, combustion-instability, turbopumps, solid-motors, hybrid-rockets]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
unit_system: SI
related: [space.overview, space.orbital-mechanics, space.electric-advanced-propulsion, space.launch-industry]
sources:
  - {title: "RS-25", url: "https://en.wikipedia.org/wiki/RS-25", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Merlin (rocket engine family)", url: "https://en.wikipedia.org/wiki/Merlin_(rocket_engine_family)", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "SpaceX Raptor", url: "https://en.wikipedia.org/wiki/SpaceX_Raptor", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "BE-4", url: "https://en.wikipedia.org/wiki/BE-4", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Vulcain (rocket engine)", url: "https://en.wikipedia.org/wiki/Vulcain_(rocket_engine)", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Rutherford (rocket engine)", url: "https://en.wikipedia.org/wiki/Rutherford_(rocket_engine)", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "RD-170", url: "https://en.wikipedia.org/wiki/RD-170", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "LE-9", url: "https://en.wikipedia.org/wiki/LE-9", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "YF-100", url: "https://en.wikipedia.org/wiki/YF-100", publisher: "Wikipedia", accessed: "2026-08-25"}
---

# Chemical rocket propulsion

**Summary.** A chemical rocket converts the enthalpy of a combustion reaction into directed kinetic energy through a converging–diverging nozzle. Its performance separates cleanly into a combustion term (characteristic velocity `c*`) and a nozzle term (thrust coefficient `C_F`), whose product is the effective exhaust velocity. The engineering problem is not making thrust — it is feeding the chamber efficiently, cooling it, keeping the combustion stable, and doing all three at a mass and cost that closes the vehicle. This file covers nozzle thermodynamics with worked numbers, propellant combinations and their real specific impulses, the six engine cycles with flying examples, cooling and instability, turbomachinery, solids and hybrids, and a comparison table of significant engines currently flying.

## Key facts

| Quantity | Value |
|---|---|
| g₀ (Isp definition constant) | 9.80665 m/s² exactly |
| Highest flight-proven vacuum Isp | 452 s — RS-25, LOX/LH2, staged combustion |
| Highest flight-proven chamber pressure | ≈300 bar Raptor 2; Raptor 3 tested to 350 bar |
| Highest-thrust single engine ever flown | RD-170: 7,887 kN vacuum, four chambers, one turbopump |
| Highest-thrust single-chamber engine flown | F-1: 6,770 kN sea level (Saturn V, retired) |
| Merlin 1D thrust-to-weight | ≈180 (highest of any production engine) |
| Typical LOX/RP-1 c* | ≈1,750–1,800 m/s |
| Typical LOX/LH2 c* | ≈2,350–2,400 m/s |
| Universal gas constant | 8,314.46 J/(kmol·K) |

## 1. Nozzle thermodynamics

### The De Laval nozzle

Subsonic flow accelerates in a converging duct; supersonic flow accelerates in a diverging duct. The area–Mach relation for isentropic flow of a calorically perfect gas,

```
dA/A = (M² − 1) dV/V
```

means a nozzle must converge to a **throat** where M = 1 and then diverge. The throat is choked: once the pressure ratio exceeds the critical value `(2/(γ+1))^(γ/(γ−1))` (≈1.83 for γ = 1.2), mass flow is fixed by chamber conditions alone.

**Mass flow through the throat:**

```
ṁ = p_c A* Γ / √(R T_c),    Γ = √γ · (2/(γ+1))^((γ+1)/(2(γ−1)))
```

Γ is the *Vandenkerckhove function*; it varies only from 0.63 to 0.68 across all realistic γ, which is why `c*` is so insensitive to nozzle details.

**Area ratio:**

```
A_e/A* = (1/M_e) · [ (2/(γ+1))(1 + ((γ−1)/2) M_e²) ]^((γ+1)/(2(γ−1)))
```

**Exhaust velocity (ideal, fully expanded):**

```
v_e = √( (2γ/(γ−1)) · R T_c · [1 − (p_e/p_c)^((γ−1)/γ)] )
```

The bracket approaches 1 as p_e → 0, so `v_e,max = √(2γ R T_c/(γ−1))` — the theoretical limit even with an infinite nozzle. Everything else is chasing the last 20%.

**Thrust:**

```
F = ṁ v_e + (p_e − p_a) A_e
```

The pressure term is why a sea-level engine and a vacuum engine differ. An engine is *optimally expanded* when p_e = p_a. Over-expansion (p_e < p_a) risks flow separation and side loads; under-expansion (p_e > p_a) wastes performance. A first-stage engine is deliberately over-expanded at sea level so it performs better as it climbs.

### The clean decomposition

```
c* = p_c A*/ṁ = √(R T_c)/Γ            (combustion quality — chamber only)
C_F = F/(p_c A*)                       (nozzle quality — geometry only)
c = I_sp g₀ = c* · C_F
```

`c*` is measured, not assumed: comparing measured `c*` with the CEA-predicted value gives **c\* efficiency**, typically 0.94–0.99 for a good injector. `C_F` efficiency is 0.95–0.98 depending on divergence and boundary-layer losses.

### Worked example: LOX/RP-1 first-stage engine

Take a realistic chamber: T_c = 3,670 K, mean molar mass M = 23.3 kg/kmol (so R = 356.85 J/(kg·K)), γ = 1.24, p_c = 100 bar.

**Characteristic velocity.**
```
Γ = √1.24 × (2/2.24)^(2.24/0.48) = 0.656186
c* = √(R T_c)/Γ = √(356.84 × 3670)/0.656186 = 1,744.0 m/s
```
Real LOX/RP-1 engines achieve 1,730–1,790 m/s. Good.

**Exit velocity at p_e/p_c = 0.007 (p_e = 0.7 bar, roughly sea-level optimum).**
```
(0.007)^(0.24/1.24) = 0.382777
v_e = √((2γ/(γ−1)) R T_c [1 − 0.007^((γ−1)/γ)]) = 2,890.2 m/s
I_sp (ideal, optimum expansion) = 2890.2/9.80665 = 294.7 s
```
Apply a combined c*·C_F efficiency of ≈0.96 and you get **≈283 s** — which is essentially the Merlin 1D sea-level figure.

**Thrust coefficient, checked for consistency.**
```
C_F,vac ≈ √( (2γ²/(γ−1)) (2/(γ+1))^((γ+1)/(γ−1)) [1 − (p_e/p_c)^((γ−1)/γ)] ) + (p_e/p_c)(A_e/A*)
        = 1.6572 + 0.007 × 17 ≈ 1.657 + 0.119 = 1.776
c = c* C_F(momentum part) = 1744.0 × 1.6572 = 2,890.2 m/s ✓
```

**Vacuum nozzle, p_e/p_c = 0.0006 (area ratio ≈165, Merlin Vacuum).**
```
v_e = √((2γ/(γ−1)) R T_c [1 − 0.0006^((γ−1)/γ)]) = 3,211.4 m/s → 327.5 s momentum term
```
Adding the vacuum pressure thrust `p_e A_e/(ṁ g₀)` brings the total to the observed **348 s** for the Merlin Vacuum. The pressure term is not a rounding error at high area ratio; it is ~6% of the total.

### Definitions of specific impulse — get these right

- **Vacuum Isp** — the number quoted for upper stages. Includes the full pressure-thrust term.
- **Sea-level Isp** — for first stages; always lower for the same engine (RS-25: 366 s SL, 452 s vacuum).
- **Delivered Isp** — measured on the vehicle, includes all losses.
- **Theoretical/shifting-equilibrium Isp** — CEA output assuming the gas re-equilibrates as it expands. **Frozen-flow Isp** assumes composition freezes at the throat. Reality lies between, closer to shifting for large engines.
- **Density impulse** `ρ I_sp` — the figure of merit for volume-limited stages. LOX/LH2 has superb Isp and terrible density impulse; this is why hydrogen upper stages are enormous and why no operational first stage outside the Delta IV and H-II families has used hydrogen alone.

## 2. Propellant combinations

| Combination | Vac Isp (typical, s) | Bulk density (kg/m³) | O/F | Notes |
|---|---|---|---|---|
| LOX / LH2 | 440–465 | ≈360 | 5.5–6.0 | Best Isp; cryogenic, bulky, hydrogen embrittlement, deep-cryo (20 K) handling |
| LOX / RP-1 | 330–350 | ≈1,030 | 2.3–2.8 | Dense, cheap, storable fuel; coking limits reuse and regen cooling |
| LOX / CH4 | 355–380 | ≈830 | 3.2–3.8 | Clean-burning, mildly cryogenic (111 K vs 20 K), ISRU-compatible on Mars |
| N2O4 / MMH | 315–336 | ≈1,190 | 1.6–2.0 | Hypergolic, storable, restartable; toxic and carcinogenic |
| N2O4 / UDMH (or UH-25/Aerozine-50) | 310–333 | ≈1,190 | 1.9–2.4 | Same, Soviet/Chinese heritage; UDMH is more toxic still |
| HTPB / AP / Al (solid) | 265–290 | ≈1,800 | — | High density impulse, no plumbing, no shutdown |
| Hydrazine (monoprop) | 220–235 | 1,004 | — | Catalytic decomposition over Shell 405; the ACS workhorse |
| LMP-103S (green monoprop) | ≈235–255 | ≈1,240 | — | ADN-based; ≈6% higher Isp and ≈30% higher density impulse than hydrazine **[needs-verification for exact figures]** |
| AF-M315E / ASCENT | ≈245–260 | ≈1,470 | — | HAN-based; flown on NASA GPIM (2019) **[needs-verification for exact figures]** |
| H2O2 (85–98%, monoprop) | 150–185 | ≈1,400 | — | Simple, non-toxic; low Isp; used by some smallsat and amateur groups |
| Cold gas (N2, GHe) | 60–75 | — | — | Trivial, reliable, used for fine control and CubeSats |

**On the green monopropellants.** The motivation is not performance but ground operations: hydrazine loading requires SCAPE suits, an exclusion zone and a large fraction of a launch campaign's cost and schedule. LMP-103S (ammonium dinitramide based, developed by ECAPS/Bradford in Sweden) flew on **PRISMA** in 2010 and is now on multiple commercial buses. AF-M315E, redesignated **ASCENT** (hydroxylammonium nitrate based, US Air Force Research Laboratory), flew on NASA's **Green Propellant Infusion Mission (GPIM)** launched June 2019 on Falcon Heavy STP-2. Both have higher density impulse than hydrazine and both require higher catalyst preheat temperatures (350–450 °C versus ~120 °C), which is the main system-level penalty. Exact Isp and density figures vary by source and thruster; treat quoted values as vendor data.

> ⚠️ Hydrazine, MMH and UDMH are acutely toxic and carcinogenic. UDMH and its combustion products are a documented environmental problem around Baikonur drop zones. Any handling requires trained personnel, respiratory protection and regulatory clearance; this is not amateur territory under any circumstances.

## 3. Engine cycles

### Pressure-fed

No turbomachinery. Tank pressure feeds the chamber directly, so tank pressure must exceed chamber pressure plus injector drop — which caps p_c at 10–30 bar and forces heavy tanks. Extremely reliable and restartable.

**Examples:** Apollo Lunar Module Descent and Ascent engines; the Space Shuttle OMS (AJ10-190); Orion's service module main engine (AJ10-190 heritage); most attitude control thrusters; the Draco/SuperDraco thrusters on Dragon (SuperDraco: 71 kN each, pressure-fed NTO/MMH, 3D-printed Inconel chamber).

### Gas generator (open cycle)

A small fraction of propellant (2–5%) burns fuel-rich in a separate gas generator to drive the turbine; the turbine exhaust is dumped overboard, usually into the nozzle skirt or a separate duct. Simple, robust, and loses 1–3% of Isp to the dumped flow.

**Examples:** F-1 (Saturn V), Merlin 1D, Vulcain 2/2.1, RS-68A (Delta IV), Rocketdyne J-2, LE-7A's predecessor lineage. The black smoke in Saturn V and Falcon 9 launch footage is the fuel-rich turbine exhaust.

### Staged combustion (closed cycle)

The preburner exhaust is routed into the main chamber, so no propellant is wasted. It buys 5–10 s of Isp and allows much higher chamber pressure — at the cost of high-pressure, high-temperature turbine machinery and a much harder start transient.

- **Fuel-rich staged combustion (FRSC):** preburner runs fuel-rich, turbine sees hydrogen-rich gas at ~800 K. Practical only with hydrogen. **RS-25** is the canonical example (452 s vacuum, ~207 bar chamber, 69:1 nozzle, 3.5 t, throttle 67–109%).
- **Oxidiser-rich staged combustion (ORSC):** preburner runs oxygen-rich. The turbine handles hot oxygen — historically considered impossible in the West because it eats metal. Soviet metallurgy (ZhS6K nickel alloys, enamel-coated surfaces) solved it in the 1960s. **RD-170/171/180/191, RD-253, NK-33, BE-4, YF-100, Archimedes** all use it. ORSC allows dense hydrocarbon propellants at very high chamber pressure, which is why the RD-180 delivers ~338 s vacuum Isp on kerosene where a gas-generator engine gets ~310.

### Full-flow staged combustion (FFSC)

Two preburners — one fuel-rich, one oxidiser-rich — each driving its own turbopump, with *both* exhausts entering the main chamber. No propellant is dumped, turbine inlet temperatures are lower for a given power, and there is no fuel/oxidiser interpropellant seal (each turbopump sees only its own propellant), which is a major life driver.

Only two engines have ever flown FFSC and one of them is **Raptor**. (The Soviet RD-270 was tested but never flown; the US Integrated Powerhead Demonstrator never became an engine.) Raptor 2: 230 tf sea level, 258 tf vacuum, Isp 347 s, 300 bar chamber, 1,630 kg. Raptor 3: 250 tf nominal (280 tf target), 275 tf vacuum, Isp 350 s, 330–350 bar demonstrated, 1,525 kg, and designed without an external heat shield — the plumbing is integrated into the structure. Raptor Vacuum runs ≈380 s.

### Expander cycle

Regenerative cooling heats the fuel (hydrogen or methane) enough to drive the turbine directly; no combustion in the power loop. Inherently self-limiting and very safe — turbine power scales with chamber surface area (∝ D²) while thrust scales with throat area, so the cycle *caps out* around 300–400 kN. Beautiful, benign, restartable, and small.

- **Closed expander:** RL10 family. RL10C-1-1 on Vulcan Centaur delivers 203.6 kN at 453.8 s; the newer RL10E variant delivers 214.6 kN at 460.9 s.
- **Expander bleed (open):** a fraction of the heated fuel drives the turbine and is dumped, breaking the power cap. **LE-5B** and **LE-9** (H3 first stage, 1,471 kN) use this. LE-9 is the only large first-stage expander-bleed engine ever built, and its development was, in JAXA's own framing, the hardest element of H3 — turbopump turbine blade fatigue and combustion chamber cracks delayed the vehicle from 2020 to a first flight on **7 March 2023** (which failed on second-stage ignition) and a successful second flight on **17 February 2024**.
- **Vinci** (Ariane 6 upper stage): closed expander, 180 kN, up to five restarts, burn times to 900 s.

### Electric pump-fed

Batteries and brushless DC motors drive the pumps. Removes the turbine, the gas generator, the start cartridge and most of the plumbing; adds dead battery mass that grows with burn time. Only viable at small scale and short burn — exactly the Electron's regime.

**Rutherford** is the flight example and the only one at scale: 24.9 kN sea level / 25.8 kN vacuum, Isp 311 s SL / 343 s vacuum, LOX/RP-1, regeneratively cooled, largely 3D-printed by direct metal laser sintering. Two brushless DC motors per engine produce 37 kW at 40,000 rpm; the nine-engine first stage draws over 1 MW of electrical power. Rocket Lab quotes pump drive efficiency of ~95% against ~50% for a gas generator — though the correct comparison includes battery mass, which is why Neutron's Archimedes is ORSC rather than electric-pump.

## 4. Cooling

**Regenerative cooling** routes one propellant (usually fuel) through channels in the chamber and nozzle wall before injection. Heat flux at the throat of a high-pressure engine reaches 80–160 MW/m² — higher than a re-entry stagnation point — and the wall must stay below ~800 K. Copper alloys (NARloy-Z, CuCrZr, GRCop-42/84) are used for their thermal conductivity, with a thin electroformed nickel closeout. Channel design is a coupled conjugate heat-transfer problem: too small and the pressure drop kills the pump, too large and the wall overheats.

RP-1 regen cooling is limited by **coking** — thermal cracking deposits carbon on the channel walls, raising wall temperature run over run. This is one of the reasons methane is preferred for reusable engines: it does not coke.

**Film cooling** injects a fuel-rich curtain along the wall. Cheap, effective, costs 1–3 s of Isp. Almost every engine uses some.

**Ablative cooling** lets a silica-phenolic or carbon-phenolic liner char and erode. Simple, mass-efficient for short burns, single-use. Used on the Kestrel and Merlin 1C upper-stage nozzles and on most solid motor throats and exit cones.

**Radiative cooling** for high-area-ratio nozzle extensions: niobium alloy (C-103) or carbon–carbon skirts glowing at 1,300–1,600 K. The Merlin Vacuum, RL10 and AJ10 extensions all do this.

**Dump cooling** passes propellant through the nozzle wall and dumps it — rare, but used on the RS-68 nozzle (ablative) and some upper stages.

## 5. Combustion instability

The failure mode that destroyed engines for two decades and can still destroy one today. Pressure oscillations couple to the combustion process and grow.

- **Chugging** (low frequency, 10–400 Hz): feed-system coupling. The chamber pressure oscillation modulates injector Δp, which modulates flow, which modulates chamber pressure. Fixed by raising injector pressure drop (typically 15–25% of p_c) or adding a feed-line accumulator/cavitating venturi.
- **Buzzing** (400–1,000 Hz): intermediate, acoustic coupling with the injector manifold.
- **Screeching / high-frequency instability** (>1,000 Hz): transverse acoustic modes of the chamber (first tangential mode is usually the killer) coupling to the combustion zone. Growth is fast — milliseconds — and the enhanced heat transfer burns through a wall before shutdown can act.

The F-1 programme spent from 1959 to 1961 on this, running over 2,000 tests and deliberately detonating small bombs inside running engines to prove the design could damp a perturbation within ~400 ms. The fix was **injector baffles** (radial and hub baffles dividing the injector face) plus injector pattern redesign. Modern practice adds **acoustic cavities** (Helmholtz resonators around the injector periphery tuned to the first tangential mode) and relies heavily on CFD and on the Rayleigh criterion: instability grows when heat release is in phase with pressure oscillation.

Stability rating tests — bomb tests, pulse guns, directed gas flows — remain a required qualification item for any new large engine.

## 6. Turbopumps

The highest power density machinery humans build. The RS-25 high-pressure fuel turbopump produces ≈55 MW from a package the size of a car engine, running at 35,000 rpm, pumping liquid hydrogen at 20 K to over 400 bar. The RD-170's single turbopump develops ≈190 MW.

Design drivers:

- **Cavitation.** Net positive suction head must exceed the vapour pressure margin. Solved with an **inducer** — a low-head axial screw ahead of the main impeller — and with tank pressurisation. Suction specific speed is the governing parameter.
- **Bearings and seals.** Cryogenic propellant is the lubricant. Interpropellant seals (between the LOX and fuel sides on a single-shaft pump) are a chronic failure source — hence the appeal of FFSC's separate shafts.
- **Materials.** Oxygen-rich turbine gas requires nickel superalloys with protective coatings; hydrogen requires resistance to hydrogen environment embrittlement (Inconel 718 is susceptible; Inconel 625 and A-286 less so).
- **Rotordynamics.** Operating above the first critical speed requires careful damping; the RS-25 turbopump whirl problem cost years.

## 7. Throttling and restart

**Throttling** is limited at the low end by injector Δp collapsing (loss of atomisation and stability) and by cooling channel flow. Fixes: pintle injectors (variable annulus — the Apollo LM descent engine throttled 10:1, and Merlin uses a pintle), dual-manifold injectors, or simply accepting a narrow range. Real ranges: RS-25 67–109%; Merlin 1D roughly 40–100% (MVac down to 360 kN of 981 kN, i.e. 39%); BE-4 40–100%; RD-191 down to 30%; RD-180 to 47%.

**Deep throttling matters for landing.** Falcon 9's landing burn uses one engine at minimum throttle and the vehicle is still thrust-to-weight > 1 at touchdown — hence the "hoverslam"/suicide burn: the vehicle cannot hover, so the burn must terminate at zero velocity and zero altitude simultaneously.

**Restart** requires ignition (pyrotechnic, TEA-TEB hypergolic slug as on Merlin, spark torch as on Raptor and RL10, or true hypergolic propellants), propellant settling (ullage motors or RCS), and thermal conditioning of the pumps. Number of restarts is a hard spec item: Vinci is qualified for five, the Centaur RL10 for many more, and Falcon 9's second stage typically performs two to three.

## 8. Solid motors

A solid motor is a case, a grain, an igniter and a nozzle. No plumbing, no pumps, no throttling, and no shutdown.

**Burn rate law:** `r = a p_c^n`. The pressure exponent n must be below 1 for stable operation; typical composite propellants have n = 0.3–0.4 and a burn rate of 5–15 mm/s at 70 bar.

**Grain geometry sets the thrust profile** because thrust ∝ burning surface area:
- **Star/internal-burning star** — near-neutral burn (constant thrust)
- **Cylindrical bore** — progressive (increasing area)
- **End-burner** — long, low, neutral
- **Wagon wheel, dog-bone, finocyl** — tailored profiles
The Shuttle SRB used an 11-point star at the forward end tapering to a circular perforation aft, producing a deliberate thrust dip through max-Q.

**Composition (composite, HTPB class):** 68–70% ammonium perchlorate oxidiser (bimodal particle sizes for packing), 16–20% aluminium fuel, 10–14% hydroxyl-terminated polybutadiene binder plus curative, plus burn-rate modifiers (iron oxide) and plasticisers. Isp 265–290 s vacuum, density ≈1,800 kg/m³ — the density impulse is superb, which is why boosters are solid.

**Case materials:** steel (Shuttle SRB), or filament-wound graphite-epoxy (P120C on Ariane 6 and Vega-C, GEM 63XL on Vulcan and Atlas V, Castor 30/120). Composite cases dominate new designs.

**Nozzle:** carbon–carbon or graphite throat insert (eroding, so the throat area grows during the burn), carbon-phenolic exit cone, and a flexible bearing joint for thrust vector control.

**Structural analysis** of the grain matters: the propellant is a viscoelastic solid bonded to the case, and thermal cycling plus ignition pressurisation can crack it. A crack increases burning surface, which increases pressure, which can burst the case. Grain structural integrity and non-destructive inspection are the discipline's core.

> ⚠️ A solid motor cannot be shut down. Once ignited it runs to propellant exhaustion. This is why the Shuttle had no abort mode during SRB burn and why crewed vehicles with solid first stages are contentious.

## 9. Hybrid rockets

Solid fuel (usually HTPB, paraffin wax, or PMMA) with liquid or gaseous oxidiser (N2O, LOX, or nitrogen tetroxide). Throttleable, shut-downable, safe to handle (fuel and oxidiser cannot react without deliberate injection), and simpler than a bipropellant.

The problem is **regression rate**: combustion is diffusion-limited at the fuel surface, so the fuel burns back slowly (typically 1–3 mm/s) and the O/F ratio shifts through the burn as the port area grows. Multi-port grains improve mass flow but waste volume and leave slivers. **Paraffin-based fuels** regress 3–4× faster because a melt layer entrains droplets into the gas stream — this is the main advance of the last twenty years (Karabeyoglu et al., Stanford).

Flight record: SpaceShipOne (2004, HTPB/N2O, three X-Prize flights) and SpaceShipTwo/VSS Unity (HTPB then a nylon-based grain). Gilmour Space in Australia and hybrid teams across university rocketry keep the field alive. No orbital hybrid launcher has flown.

## 10. Comparison of significant engines flying today

| Engine | Vehicle | Propellants | Cycle | Thrust SL (kN) | Thrust vac (kN) | Isp SL (s) | Isp vac (s) | p_c |
|---|---|---|---|---|---|---|---|---|
| **Merlin 1D** | Falcon 9/Heavy S1 | LOX/RP-1 | Gas generator | 845 (2018) | ≈914 | ≈282 | ≈311 | 9.7 MPa |
| **Merlin 1D Vacuum** | Falcon 9/Heavy S2 | LOX/RP-1 | Gas generator | — | 981 | — | 348 | — |
| **Raptor 2** | Starship / Super Heavy | LOX/CH4 | Full-flow staged | 2,256 (230 tf) | 2,530 (258 tf) | — | 347 | 300 bar |
| **Raptor 3** | Starship / Super Heavy | LOX/CH4 | Full-flow staged | 2,452 (250 tf) | 2,697 (275 tf) | — | 350 | 330–350 bar |
| **Raptor Vacuum** | Starship | LOX/CH4 | Full-flow staged | — | ≈2,400 | — | ≈380 | — |
| **RS-25** | SLS core | LOX/LH2 | Fuel-rich staged | 1,670 | 2,090 | 366 | 452 | ≈207 bar |
| **BE-4** | Vulcan, New Glenn | LOX/CH4 | Ox-rich staged | 2,400 (ULA rating) – 2,800 (full) | — | — | 340 | 14 MPa |
| **BE-3U** | New Glenn S2 | LOX/LH2 | Expander bleed | — | ≈710 each **[needs-verification]** | — | — | — |
| **Vulcain 2.1** | Ariane 6 core | LOX/LH2 | Gas generator | — | 1,324 | — | ≈429 (V2 figure) | 120.8 bar |
| **Vinci** | Ariane 6 upper | LOX/LH2 | Closed expander | — | 180 | — | ≈457 **[needs-verification]** | — |
| **RL10C-1-1** | Vulcan Centaur | LOX/LH2 | Closed expander | — | 203.6 | — | 453.8 | — |
| **RL10E** | Centaur (2025+) | LOX/LH2 | Closed expander | — | 214.6 | — | 460.9 | — |
| **RD-180** | Atlas V (retiring) | LOX/RP-1 | Ox-rich staged, 2 chambers | ≈3,830 | ≈4,150 | ≈311 | ≈338 **[needs-verification]** | ≈257 bar **[needs-verification]** |
| **RD-191** | Angara | LOX/RP-1 | Ox-rich staged, 1 chamber | ≈1,920 | ≈2,090 | ≈311 | ≈337 **[needs-verification]** | — |
| **RD-170 / 171M** | Energia / Zenit (heritage) | LOX/RG-1 | Ox-rich staged, 4 chambers | — | 7,887 | 309 | 338 | — |
| **YF-100** | Long March 5/6/7/8/12 | LOX/kerosene | Ox-rich staged | ≈1,200 (120 tf) | — | — | — | — |
| **LE-9** | H3 core | LOX/LH2 | Expander bleed | — | 1,471 | — | ≈425 **[needs-verification]** | — |
| **Rutherford** | Electron S1 | LOX/RP-1 | Electric pump-fed | 24.9 | 25.8 | 311 | 343 | — |
| **Archimedes** | Neutron | LOX/CH4 | Ox-rich staged | ≈733 (9 give 6,600) | ≈900 (S2) | — | — | — |

Figures without a `[needs-verification]` tag are from the cited sources. Note the two very different design philosophies visible in the table: American hydrocarbon engines historically chose gas-generator simplicity and accepted ~310–350 s, while Soviet/Russian and now Chinese engines chose oxidiser-rich staged combustion and got the same propellants to 337–338 s at much higher chamber pressure. Raptor and BE-4 represent the American convergence on the Russian approach, with methane substituted for kerosene.

## Open questions

- RD-180, RD-191 and YF-100 chamber pressure and Isp are widely cited but I could not retrieve them from a primary or well-sourced page in this pass (Aerojet Rocketdyne's RD-180 datasheet is robots-disallowed). Marked `needs-verification`.
- Vulcain 2.1 vacuum Isp is not stated on the source page; the Vulcain 2 figure of 429 s is given as an approximation.
- LMP-103S and AF-M315E/ASCENT Isp and density figures come from vendor and programme literature that varies by thruster configuration; treat as indicative.

## Sources

- [RS-25](https://en.wikipedia.org/wiki/RS-25) — Wikipedia, accessed 2026-08-25
- [Merlin (rocket engine family)](https://en.wikipedia.org/wiki/Merlin_(rocket_engine_family)) — Wikipedia, accessed 2026-08-25
- [SpaceX Raptor](https://en.wikipedia.org/wiki/SpaceX_Raptor) — Wikipedia, accessed 2026-08-25
- [BE-4](https://en.wikipedia.org/wiki/BE-4) — Wikipedia, accessed 2026-08-25
- [Vulcain (rocket engine)](https://en.wikipedia.org/wiki/Vulcain_(rocket_engine)) — Wikipedia, accessed 2026-08-25
- [Rutherford (rocket engine)](https://en.wikipedia.org/wiki/Rutherford_(rocket_engine)) — Wikipedia, accessed 2026-08-25
- [RD-170](https://en.wikipedia.org/wiki/RD-170) — Wikipedia, accessed 2026-08-25
- [RD-180](https://en.wikipedia.org/wiki/RD-180) — Wikipedia, accessed 2026-08-25
- [LE-9](https://en.wikipedia.org/wiki/LE-9) — Wikipedia, accessed 2026-08-25
- [YF-100](https://en.wikipedia.org/wiki/YF-100) — Wikipedia, accessed 2026-08-25
- [Vulcan Centaur](https://en.wikipedia.org/wiki/Vulcan_Centaur) — Wikipedia, accessed 2026-08-25 (RL10C-1-1 and RL10E figures)
- [Ariane 6](https://en.wikipedia.org/wiki/Ariane_6) — Wikipedia, accessed 2026-08-25 (Vinci, P120C)
- [Rocket Lab Neutron](https://en.wikipedia.org/wiki/Rocket_Lab_Neutron) — Wikipedia, accessed 2026-08-25 (Archimedes)
