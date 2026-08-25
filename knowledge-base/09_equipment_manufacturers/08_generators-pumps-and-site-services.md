---
id: equipment.site_services
title: Generators, pumps, compressors and site services
domain: 09_equipment_manufacturers
tags: [generator, genset, load-calculation, water-pump, borehole, solar-pump, grundfos, lorentz, franklin-electric, compressor, atlas-copco, ingersoll-rand, welding, lincoln, esab, miller, site-lighting, off-grid, namibia]
jurisdiction: southern-africa
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Cummins QuickServe Online (service and parts information)", url: "https://quickserve.cummins.com/", publisher: "Cummins Inc.", accessed: 2026-08-25}
  - {title: "Cummins Mart (parts catalogue)", url: "https://mart.cummins.com/", publisher: "Cummins Inc.", accessed: 2026-08-25}
  - {title: "LORENTZ solar water pumps", url: "https://www.lorentz.de/products/", publisher: "Bernt Lorentz GmbH", accessed: 2026-08-25}
  - {title: "LORENTZ partnerNET (technical portal)", url: "https://partnernet.lorentz.de/", publisher: "Bernt Lorentz GmbH", accessed: 2026-08-25}
  - {title: "Franklin Electric", url: "https://www.franklin-electric.com/", publisher: "Franklin Electric Co.", accessed: 2026-08-25}
  - {title: "Atlas Copco South Africa", url: "https://www.atlascopco.com/en-za", publisher: "Atlas Copco", accessed: 2026-08-25}
  - {title: "Atlas Copco construction equipment", url: "https://www.atlascopco.com/en-uk/construction-equipment", publisher: "Atlas Copco", accessed: 2026-08-25}
  - {title: "Smith Power Equipment (SA distributor)", url: "https://www.smithpower.co.za/", publisher: "Smith Power Equipment", accessed: 2026-08-25}
related: [equipment.overview, equipment.manual_library, equipment.maintenance]
unit_system: SI
---

# Generators, pumps, compressors and site services

**Summary.** On a remote or newly opened site, the temporary services are the project: no power means no tools, no water means no concrete, no compressed air means no drilling. This file covers generator selection and load calculation, water supply from boreholes including solar pumping, compressed air, welding plant, site lighting, and how to design an off-grid site power system that is neither dangerously undersized nor ruinously oversized.

## Key facts

| Item | Value | Note |
|---|---|---|
| Generator power notation | **kVA** (apparent) and **kW** (real); kW = kVA × PF | site gensets rated at **PF 0.8**, so 100 kVA = 80 kW |
| Standard supply **[NA] [ZA]** | **230 V single phase / 400 V three phase, 50 Hz** | never assume 60 Hz equipment will run correctly |
| Duty ratings (ISO 8528) | **COP** (continuous), **PRP** (prime, variable load, unlimited hours), **LTP/ESP** (standby, ≤500 h/yr) | a prime-rated set run at standby rating will fail early |
| Healthy loading band | **50–80% of prime rating** | below ~30% for extended periods causes wet stacking |
| Diesel consumption rule of thumb | **≈0.25–0.30 L/kWh** at good loading | a 100 kVA set at 70% load ≈ 15–18 L/h |
| Motor starting inrush (DOL) | **6–8 × full-load current** | the single biggest genset sizing driver |
| Soft starter / VFD inrush | 2–3 × / 1.2–1.5 × FLC | can halve the required genset size |
| Compressor output notation | **l/s** or **cfm** at a stated **bar** | 1 cfm ≈ 0.472 l/s; 7 bar is the standard site pressure |
| Jackhammer air demand | ~25–35 l/s (50–75 cfm) each at 7 bar | plus ~20% for leaks and simultaneity |
| Submersible borehole pump | rated by **flow (m³/h) at head (m)** | duty point must sit near the pump's best efficiency point |
| Solar pump array sizing | roughly **1.3–1.5 × pump kW** in kWp of PV | derated for temperature, dust and non-optimal tilt |
| Welding plant duty cycle | % of a **10-minute** period at rated current | a 250 A @ 35% machine welds 3.5 min then rests 6.5 min |

## Generators

### Manufacturers and what they actually are
A generator set is an **engine** + **alternator** + **controller** + **canopy**, often from four different companies. Know which is which.

| Role | Suppliers |
|---|---|
| **Engines** | **Perkins** (Caterpillar-owned; the most common industrial genset engine worldwide), **Cummins**, **Caterpillar**, **Volvo Penta**, **John Deere**, **Deutz**, **FPT/Iveco**, **Mitsubishi**, **Yanmar**, **Kubota** (small), **Honda** (petrol, small) |
| **Alternators** | **Stamford** (Cummins Generator Technologies), **Leroy-Somer** (Nidec), **Mecc Alte**, **Marathon** |
| **Controllers** | **Deep Sea Electronics (DSE)**, **ComAp**, **Woodward**, **Cummins PowerCommand** |
| **Packagers / brands** | **Caterpillar** (Cat generator sets), **Cummins Power Generation**, **FG Wilson** (Perkins-based, extremely common in Africa), **Aggreko** (rental), **Atlas Copco** (QAS/QES range), **Himoinsa**, **Pramac**, **SDMO/KOHLER**, **Kipor** and **Elemax** (small portable) |
| **Small petrol** | **Honda** (EU/EM series; the inverter EU series is the reference for clean power to sensitive tools), **Yamaha**, **Kipor**, **Ryobi**, **Generac** |

**[ZA] [NA]** In southern Africa, FG Wilson (Perkins), Cummins and Cat dominate the 20–500 kVA site market; Honda and Kipor dominate small portable; Atlas Copco dominates hire-fleet mobile sets. **Smith Power Equipment** is a major South African distributor across several of these lines.

### Load calculation — the method

1. **List every load** with its rated power, whether it is single- or three-phase, its power factor, and its starting method.
2. Convert everything to **kW** and **kVA**: for a motor, input kW = shaft kW ÷ efficiency; kVA = kW ÷ PF.
3. Apply a **diversity factor** — not everything runs at once. A realistic assessment (typically 0.5–0.8 across a mixed site) matters more than any other number in this calculation.
4. Identify the **largest motor** and its starting method. Compute the starting kVA: FLC × starting multiple. If a 15 kW DOL pump is on the set, its ~7× inrush may briefly demand 100+ kVA even though its running demand is 18 kVA.
5. **Size the set** to the *greater* of (running kVA ÷ 0.8 utilisation) and (the transient kVA needed to start the largest motor within the allowable voltage dip — usually 15–20% maximum).
6. Check the **step-load acceptance** of the chosen set (ISO 8528 class G2/G3) and the **voltage and frequency dip** limits of the sensitive loads.
7. Add **future load** honestly, but do not oversize: a chronically under-loaded diesel wet-stacks, glazes bores and needs expensive de-carbonising.

**Worked shape of the calculation.** A site with 3 × 3 kW power-float, a 5.5 kW mixer, an 11 kW submersible pump (DOL), 4 kW of welding and 3 kW of lighting and small tools has a connected load of ~32 kW. With a diversity factor of 0.7, running demand ≈ 22 kW ≈ 28 kVA. But the 11 kW pump starting DOL draws roughly 7 × its 21 A FLC ≈ 147 A ≈ 100 kVA transient. The set must be sized for the transient: a **60–80 kVA prime-rated set**, or the pump gets a soft starter and a **40 kVA** set suffices. The soft starter is the cheaper answer.

### Practical rules
- **Fuel storage and quality.** **[NA]** Bunded tanks, water separation, and a fuel polishing regime. Diesel bug (microbial contamination) is a real and common failure at the water/fuel interface in warm climates; treat with a biocide and drain water weekly.
- **Ventilation and derating.** Gensets derate with **altitude** (roughly 3% per 300 m above 1 000 m) and **ambient temperature** (roughly 2% per 5 °C above 40 °C). **[NA]** Windhoek sits at ~1 700 m — a set rated at sea level loses roughly 6–7% before any temperature derating.
- **Earthing.** A site genset must have a properly installed earth electrode and correct neutral-earth bonding, with earth leakage protection. This is the most commonly botched item on temporary installations and it is a fatality risk.
- **Synchronising and load sharing** for multiple sets; **auto-start/auto-transfer** where a mains supply exists.
- **Hybrid and battery.** Battery-hybrid gensets (Atlas Copco ZenergiZE, Aggreko Y.Cube) let the diesel run only at high load and idle at night on battery. On a site with a low overnight base load, this can cut fuel by 30–50%.

## Water supply, pumps and boreholes

### Surface and dewatering pumps
- **Centrifugal / self-priming trash pumps** — 50–150 mm, 10–150 m³/h; the general site dewatering machine. **Honda WT/WB**, **Wacker Neuson PT**, **Atlas Copco WEDA/PAS**, **Tsurumi**.
- **Submersible dewatering pumps** — **Tsurumi**, **Grindex**, **Atlas Copco WEDA**, **Sulzer/ABS**; electric, robust, for sumps and excavations.
- **Diaphragm pumps** — slow, high solids tolerance, run dry safely; good for silty seepage.
- **Wellpoint dewatering** systems for granular soils with high water table.

### Borehole (submersible) pumps
Manufacturers: **Grundfos** (SP range — the reference product, with the Grundfos Product Center selection tool), **Franklin Electric** (motors and pumps; owns the majority of the submersible motor market), **Lowara/Xylem**, **Pedrollo**, **KSB**, **Caprari**, **Davis & Shirtliff** (East African assembler), **Speck** and **Mono** (progressive cavity, historically important in southern African boreholes).

**Selection method.**
1. Establish the **borehole yield** from the driller's test-pumping data (blow yield is not yield). Never size a pump above the sustainable yield — a pump that dewaters the borehole burns out and can damage the aquifer.
2. Compute the **total dynamic head**: static water level + drawdown at the design rate + vertical rise to the tank + friction losses in the rising main and delivery pipe + residual pressure at discharge.
3. Pick the pump whose curve crosses the **duty point (Q, H)** near its best efficiency point.
4. Check **NPSH**, the motor cooling flow velocity (submersible motors need a minimum flow past them — use a flow sleeve if the borehole is wide), and the **pump setting depth** relative to pump-intake and screen positions.
5. Protect it: dry-run protection, over/under-voltage protection, and a non-return valve.

### Solar pumping
**LORENTZ** (German; PS2 and PSk series helical-rotor and centrifugal solar submersibles) is the reference brand in southern Africa, with **Grundfos SQFlex**, **Franklin Electric SubDrive Solar/ SolarPAK**, **Shakti** and **Dayliff** as alternatives. LORENTZ operates **partnerNET**, a partner technical portal, and publishes the **COMPASS** sizing software.

**Why it dominates rural Namibia and the SADC interior:** no fuel logistics, no theft-prone diesel, minimal moving parts, and demand (irrigation, stock watering, site water) that coincides with solar availability. Design the system around a **storage tank sized for 2–3 days**, not around a battery — storing water is an order of magnitude cheaper than storing electricity.

**Sizing:** determine the daily water requirement (m³/day) and the total dynamic head, then size the pump for the duty and the array for the pump. As a planning figure, allow **1.3–1.5 kWp of PV per kW of pump**, adjusted for insolation (much of Namibia receives 5.5–6.5 kWh/m²/day, among the best in the world), array temperature derating (~10–15%), dust soiling (5–15% if uncleaned) and cable losses.

> ⚠️ **[NA]** Groundwater in parts of Namibia is saline or fluoride-rich. Test the water chemistry before selecting pump materials (stainless 316 vs 304 vs cast iron) and before assuming it is potable. A pump specified for fresh water will not survive a brackish borehole.

## Compressors

**Manufacturers.** **Atlas Copco** (the market leader; XAS/XATS portable diesel, GA rotary screw stationary), **Ingersoll Rand** (Doosan Portable Power now under IR), **Kaeser**, **Sullair**, **CompAir**, **Chicago Pneumatic** (Atlas Copco group), **ELGi**, and small piston compressors from many suppliers.

**Types.**
- **Portable diesel screw** — 2–25 m³/min (70–900 cfm) at 7–14 bar. The site compressor for jackhammers, rock drills, sandblasting and pipeline testing.
- **Stationary rotary screw** — workshop and plant use; oil-injected (standard) or oil-free (where air purity matters).
- **Piston** — small workshop, intermittent duty.

**Sizing.** Add the air demand of every simultaneous tool (a 25 kg jackhammer ≈ 25–35 l/s at 7 bar; a hand-held rock drill 40–60 l/s; a sandblast pot 60–150 l/s depending on nozzle), apply a **simultaneity factor** and add **15–20% for leaks and hose losses**. Pressure drop in a long hose run is significant: 50 m of 19 mm hose at 30 l/s costs roughly 0.5–1 bar. Under-pressure at the tool is the most common complaint and is usually a hose problem, not a compressor problem.

**Air treatment.** After-cooler, water separator, filters and (where needed) a dryer. Wet air destroys pneumatic tools and ruins paint and blasting work.

## Welding plant

**Manufacturers.** **Lincoln Electric**, **ESAB**, **Miller (ITW)**, **Fronius**, **Kemppi**, **EWM**, **Böhler/voestalpine** (consumables), plus **Afrox** (Linde) as the dominant southern African gas and consumables supplier.

**Processes on site.**
- **SMAW / MMA (stick)** — the site standard: tolerant of wind, rust and poor fit-up, portable, no shielding gas. Electrodes E6013 (general), E7018 (low hydrogen, structural).
- **GMAW / MIG-MAG** — fast and clean, but needs shielding gas and wind protection; used in workshops and under cover.
- **FCAW (flux-cored)** — self-shielded wires give MIG productivity with stick-like wind tolerance; increasingly the site structural process.
- **GTAW / TIG** — stainless, aluminium, thin sections, pipework root runs.

**Machine specification.** Look at the **output current range**, the **duty cycle at a stated current** (e.g. 250 A @ 40% at 40 °C), the **input supply** (single- or three-phase, or engine-driven), and the **OCV**. **Engine-driven welder-generators** (Lincoln Ranger, Miller Bobcat, ESAB) are the correct answer for remote structural work: one machine gives welding output and auxiliary power.

**[ZA] [NA]** Structural welding requires a qualified welding procedure (WPS/PQR) and qualified welders to **ISO 9606** or **ASME IX**, with the fabricator's quality system to **ISO 3834** or **EN 1090** — check what the structural specification calls for before the first weld.

> ⚠️ Welding fume from galvanized, painted or stainless material contains hexavalent chromium, zinc and manganese compounds. Local exhaust ventilation or on-torch extraction, plus appropriate RPE, is a legal control, not a courtesy.

## Site lighting

- **Mobile lighting towers** — diesel or hybrid/battery, 4 × 320 W LED (formerly 4 × 1 000 W metal halide), 9 m mast, covering roughly 2 000–4 000 m² at usable levels. **Atlas Copco HiLight**, **Generac/Tower Light**, **Wacker Neuson**, **Aggreko** (hire), **Trime**.
- **Balloon lights** for glare-free area lighting near roads and public interfaces.
- **Task and string lighting** — LED festoon on 110 V CTE (centre-tapped earth) transformers where the standard applies, or 230 V with RCD protection.
- **Solar site lights** for compounds, security and access routes — no cabling, no fuel, and increasingly the default in SADC.

**Illuminance targets (planning):** general site movement 20 lux; general work areas 50–100 lux; detailed tasks (steel erection connections, rebar fixing, formwork setting) 200–500 lux; workshop/fine work 500+ lux. Verify against the project's own specification.

## Off-grid site power design

A method for a remote construction camp and worksite:

1. **Build the load profile by hour**, not just a total. Separate the **daytime construction load** (tools, plant, pumps, batch plant) from the **overnight base load** (camp lighting, refrigeration, security, communications).
2. **Match the technology to the profile.** Daytime load with strong solar resource → PV plus a modest genset for the peaks. Overnight base load → battery, not a diesel idling all night.
3. **Size the genset to the daytime peak**, with the largest motor's starting requirement checked, and add a **soft starter or VFD** to any motor above ~7.5 kW.
4. **Add PV with a hybrid inverter** where the daytime load is substantial and the site will last more than a season. **[NA]** With 5.5–6.5 kWh/m²/day of insolation, PV payback against diesel at N$ 20+/litre is frequently under three years — and the array is recoverable and re-deployable.
5. **Add battery storage** sized for the overnight base load plus the morning start, allowing the genset to shut down entirely at night. This is the biggest single fuel and noise saving.
6. **Design the distribution properly**: a temporary supply is still an electrical installation. Distribution boards with RCDs, correct cable sizing for the run length (volt drop, not just current, governs on long site runs — aim for ≤5% total), IP-rated outlets, and a competent person's certificate of compliance. **[ZA]** A Certificate of Compliance under the Electrical Installation Regulations is required; **[NA]** equivalent under the Namibian electricity regulations.
7. **Plan the fuel logistics** — delivery interval, bunded storage, security and metering — and the **maintenance schedule** (see file 10).

## Sources

- [Cummins QuickServe Online](https://quickserve.cummins.com/) and [Cummins Mart parts catalogue](https://mart.cummins.com/) — Cummins Inc., accessed 2026-08-25
- [Caterpillar](https://www.cat.com/) and [Perkins](https://www.perkins.com/) — accessed 2026-08-25 *(both block automated fetching; reachable in a browser)*
- [MTU Solutions](https://www.mtu-solutions.com/) — Rolls-Royce Power Systems, accessed 2026-08-25
- [Smith Power Equipment](https://www.smithpower.co.za/) — South African distributor, accessed 2026-08-25
- [LORENTZ solar pumps](https://www.lorentz.de/products/) and [partnerNET](https://partnernet.lorentz.de/) — Bernt Lorentz GmbH, accessed 2026-08-25
- [Franklin Electric](https://www.franklin-electric.com/) and [Franklin Water](https://www.franklinwater.com/) — accessed 2026-08-25
- [Pump Solutions South Africa](https://www.pumpsolutions.co.za/) — accessed 2026-08-25
- [Atlas Copco South Africa](https://www.atlascopco.com/en-za), [UK](https://www.atlascopco.com/en-uk), [construction equipment](https://www.atlascopco.com/en-uk/construction-equipment) — accessed 2026-08-25
- [Wacker Neuson products](https://www.wackerneuson.com/us/products) and [Wacker Neuson South Africa](https://www.wackerneuson.co.za/) — accessed 2026-08-25
- [Lincoln Electric](https://www.lincolnelectric.com/), [ESAB](https://esab.com/), [Miller Welds](https://www.millerwelds.com/) — accessed 2026-08-25 *(all three block automated fetching; reachable in a browser)*
- [SA Department of Employment and Labour](https://www.labour.gov.za/) — Electrical Installation Regulations and OHS Act, accessed 2026-08-25

## Open questions

- Grundfos's web properties (grundfos.com and product-selection.grundfos.com) were not reachable from this environment; the Grundfos Product Center is the standard pump selection tool and should be reached directly in a browser. Status `needs-verification` for the exact URL.
- Diesel and electricity prices, and therefore PV payback periods, move constantly — the "under three years" figure is indicative and must be recomputed with current N$ / R prices.
- **[NA]** Confirm current Namibian electrical installation certification requirements and the accepted competent-person qualification before designing a temporary site supply.

