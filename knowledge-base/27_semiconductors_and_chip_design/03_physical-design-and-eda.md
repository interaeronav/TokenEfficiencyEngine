---
id: semi.physical_design
title: Physical design and EDA — netlist to GDSII, and the tools that get you there
domain: 27_semiconductors_and_chip_design
tags: [physical-design, floorplanning, placement, clock-tree-synthesis, routing, parasitic-extraction, signoff, drc, lvs, pdk, standard-cells, ir-drop, electromigration, eda, tapeout, mask]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Synopsys", url: "https://en.wikipedia.org/wiki/Synopsys", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Cadence Design Systems", url: "https://en.wikipedia.org/wiki/Cadence_Design_Systems", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "3 nm process", url: "https://en.wikipedia.org/wiki/3_nm_process", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "2 nm process", url: "https://en.wikipedia.org/wiki/2_nm_process", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Photolithography", url: "https://en.wikipedia.org/wiki/Photolithography", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "OpenROAD Project", url: "https://en.wikipedia.org/wiki/OpenROAD_Project", publisher: "Wikipedia", accessed: 2026-08-25}
related: [semi.rtl, semi.fabrication, semi.euv, semi.economics]
---

# Physical design and EDA — netlist to GDSII, and the tools that get you there

**Summary.** Physical design turns a gate-level netlist into a set of polygons a mask shop can write. Every step — floorplan, power grid, placement, clock tree, route, extraction, signoff — is a constrained optimisation whose objective function is timing, power, area, routability, manufacturability and reliability simultaneously, and whose search space is astronomically large. Three vendors (Synopsys 31%, Cadence 30%, Siemens EDA 13% of the 2024 EDA market) supply nearly all of the tooling, and one artefact — the foundry's PDK — makes the whole flow possible. This file also gives the honest picture of what a tapeout costs, with the caveat that all leading-edge mask and wafer pricing is confidential and every public number is a modelled estimate.

## Key facts

| Item | Value | Note |
|---|---|---|
| EDA market share, 2024 | Synopsys 31%, Cadence 30%, Siemens EDA 13% | ~75% combined |
| Synopsys–Ansys acquisition | US$35 bn, announced 16 January 2024, closed 17 July 2025 | Brings multiphysics/thermal signoff in-house |
| Metal layers, leading-edge logic | 15–20 (including MIM cap and redistribution layers) | Rising with backside power delivery |
| Minimum metal pitch | 23 nm (TSMC N3E); ~20 nm (2 nm class) | |
| Contacted poly pitch, 2 nm class | ~45 nm | |
| SRAM bit cell | 0.0199 µm² (TSMC N3), 0.021 µm² (N3E) | Density signoff reference |
| Standard-cell height | Expressed in metal tracks — 7.5T/6T at 7–5 nm, ~5T at 2 nm class | Lower = denser, weaker drive |
| Reticle field (DUV and 0.33-NA EUV) | 26 × 33 mm | High-NA EUV: 26 × 16.5 mm |
| Lithography k1 in production | ~0.4 (Rayleigh theoretical limit 0.61) | `CD = k1·λ/NA` |
| ArF immersion NA | up to ~1.35 (water limits NA to ~1.4) | |

## 1. The PDK — the thing that makes everything else possible

A **process design kit** is the foundry's complete, legally-controlled description of what can be built. Contents:

- **Design rules (DRM/DRC deck)** — thousands of geometric constraints: minimum width, spacing, enclosure, density (both minimum and maximum, for CMP uniformity), antenna ratios, colouring rules for multi-patterned layers, and at advanced nodes a large body of *pattern-based* rules that forbid specific 2D configurations because OPC cannot resolve them.
- **SPICE models** — BSIM-CMG for FinFET/GAA devices, with statistical (Monte Carlo, and corner) parameter sets.
- **Technology file / LEF** — layer stack, via definitions, routing pitches and directions.
- **Standard-cell libraries** — physical (LEF/GDS) plus characterised timing and power (Liberty `.lib`, with CCS or ECSM current-source models at advanced nodes).
- **Memory and IO compilers** — parameterised SRAM/register-file generators, IO pad libraries, ESD cells.
- **Extraction technology files** (for StarRC/Quantus) and **signoff decks** (Calibre/PVS/IC Validator rule decks, plus DFM and litho-check decks).
- **IP** — PLLs, SerDes, DDR PHYs, eFuse, temperature sensors, either foundry-owned or from an approved partner list.

PDKs are under NDA; access typically requires a foundry agreement. This is precisely why SKY130 and GF180MCU being *open* was such a change (`02`, `09`).

### Standard cells

A standard cell is a fixed-height, variable-width layout of a logic function (INV, NAND2, AOI21, DFF, and hundreds more), with power/ground rails at the top and bottom so cells abut into rows. Key parameters:

- **Height in tracks** — the number of minimum-pitch metal routing tracks the cell spans. A 6-track cell is denser than a 7.5-track cell but has fewer fins/nanosheets and so less drive.
- **Drive strength** — X1, X2, X4… variants of the same function.
- **Vt flavour** — ULVT/LVT/SVT/HVT, chosen per instance to trade leakage against speed (`01`).
- **Multi-bit flops** — 2-, 4- or 8-bit flops sharing clock inverters; a standard 5–15% clock-power saving.

## 2. Floorplanning

The first irreversible decision. Determines die size, aspect ratio, IO placement, macro (SRAM, PLL, IP) placement, power-domain boundaries, and the hierarchical partitioning of the design into physical blocks.

Practical constraints:
- **Utilisation target** — 60–75% standard-cell utilisation at the start of placement for a routable, timing-closable design; higher for regular datapath, lower for congested control logic.
- **Macro placement** — SRAMs pushed to block edges with channels for routing and power; pin sides facing the cell area; keep-out halos to prevent placement crowding.
- **Blockages and channels** — routing over macros is possible on upper layers only if the macro's own routing permits.
- **Power domains** — placed contiguously; level shifters and isolation cells at boundaries; always-on regions carefully carved out.

Floorplan errors are the single most expensive class of physical-design mistake because they are discovered at routing and fixed by starting over.

## 3. Power planning

Build the power delivery network (PDN) before placing anything.

- **Rings and straps** on upper (thick, low-resistance) metals, stitched down to the follow-pin M1 rails that feed cell rows.
- **Decoupling capacitors** filling gaps to supply instantaneous switching current.
- **Power switches** (header/footer cells) for power-gated domains, with enable daisy chains sized so the inrush current on wake-up does not brown out the neighbours.
- **Backside power delivery** (Intel PowerVia on 18A; TSMC Super Power Rail on A16) fundamentally changes this step: power comes from the wafer's back face through nano-TSVs, freeing front-side tracks for signal routing. Intel claims up to a 10× reduction in worst-case dynamic voltage droop.

**IR drop** analysis (static and dynamic, tools: Ansys RedHawk-SC — now Synopsys — and Cadence Voltus) checks that no cell sees less than its characterised voltage. A typical budget is 3–5% of Vdd static plus a dynamic allowance; at 0.7 V, 5% is 35 mV, and 35 mV of Vt-equivalent droop is a large timing effect.

**Electromigration** — metal atoms are displaced by momentum transfer from electrons at high current density. Black's equation gives MTTF ∝ `J⁻ⁿ·exp(Ea/kT)`, with n ≈ 2 for copper. Signoff enforces per-layer current-density limits (average, RMS and peak) at the maximum operating temperature over a specified lifetime (typically 10 years at some duty cycle). Copper's electromigration resistance versus aluminium was one of the two reasons for the damascene transition (`05`); at 2 nm-class dimensions, EM and via resistance are among the hardest signoff items, driving interest in ruthenium and molybdenum liners/fills.

## 4. Placement

Global placement solves an analytic problem (OpenROAD's RePlAce uses an electrostatics analogy — cells as charges, density as potential) minimising a smoothed wirelength subject to density constraints; legalisation snaps cells to rows and sites; detailed placement does local reordering and swaps.

Modern placement is **timing-driven** and **congestion-aware** simultaneously, with in-loop optimisation: gate sizing, buffer insertion, Vt swapping, logic restructuring, and useful-skew scheduling. Physical synthesis has effectively merged synthesis and placement (Synopsys Fusion Compiler, Cadence Innovus with iSpatial).

## 5. Clock tree synthesis

The clock is the largest single net, the largest single power consumer (often 30–40% of dynamic power), and the network on which every timing check depends.

Objectives: minimum **skew** (arrival-time difference between endpoints), minimum **insertion delay** (source-to-endpoint latency — long trees amplify OCV derating), controlled duty cycle, and manageable power.

Structures:
- **H-tree / balanced buffer tree** — classic, good for regular blocks.
- **Clock mesh / grid** — very low skew, very high power; used in high-performance CPUs.
- **Multi-source CTS / clock spine** — the modern compromise on large SoCs.
- **Useful skew** — deliberately delaying a capture clock to borrow time from an adjacent path. Now routinely automated (concurrent clock and data optimisation, CCOpt).

Clock nets get special treatment: wider, shielded, on preferred layers, with non-default routing rules and double vias.

## 6. Routing

- **Global routing** partitions the die into gcells and assigns nets to coarse paths, producing a congestion map. If global routing shows overflow, the fix is upstream (floorplan/placement), not in the router.
- **Track assignment** commits nets to specific tracks on each layer.
- **Detailed routing** creates actual wires and vias, DRC-correct, honouring hundreds of rules including multi-patterning colour constraints, minimum-area rules, end-of-line spacing, via-pillar requirements and cut-metal rules.

Advanced-node complications:
- **Multi-patterning colouring**: on LELE/SADP layers, nets must be assigned to masks such that same-colour features respect a relaxed spacing. An uncolourable ("odd-cycle") configuration is a hard DRC error that the router must avoid *while* routing.
- **Unidirectional metal**: from roughly 20 nm, each layer routes in one direction only, with jogs made through vias.
- **Antenna effects**: during plasma etch, a long floating metal segment collects charge and can rupture a gate oxide. Fixes: diode insertion or metal jumping to a higher layer.
- **Via resistance**: at 2 nm-class pitches, a single via can contribute more resistance than a substantial length of wire, so via pillars and via ladders are inserted on critical nets.

## 7. Parasitic extraction and signoff

**RC extraction** (Synopsys StarRC, Cadence Quantus) converts the layout to a netlist annotated with resistance and capacitance, output as **SPEF**. Field-solver-accurate extraction is used for critical nets; pattern-matched rule-based extraction for the bulk. Multiple extraction corners (Cmin, Cmax, RCmin, RCmax, typical) are generated because interconnect variation is independent of device variation.

**Timing signoff**: PrimeTime (or Tempus) across the full MMMC scenario set with POCV derating, signal-integrity analysis (crosstalk-induced delay and noise — an aggressor switching alongside a victim can add or subtract delay and can glitch a static node), and clock-network variation. Signoff also covers **max transition**, **max capacitance**, and **max fanout** design-rule checks.

**Power signoff**: vector-based (from emulation-captured activity, e.g. FSDB/SAIF of a real workload) and vectorless estimation; dynamic and static IR drop; thermal analysis, increasingly mandatory in 3D-stacked designs where a hot logic die sits under memory.

**Physical verification**:
- **DRC** — geometric rule checking against the foundry deck. Siemens **Calibre** is the de facto signoff standard (most foundries qualify Calibre decks first); Cadence Pegasus and Synopsys IC Validator compete.
- **LVS** — layout-versus-schematic: extract devices and connectivity from the layout and compare to the netlist. Catches shorts, opens, wrong device sizes.
- **ERC / antenna / density** checks.
- **DFM** — lithography-friendly-design checks, critical-area analysis, via redundancy, recommended-rule compliance. At advanced nodes a **litho simulation check** (process-window verification) is run over the full chip.

## 8. Mask data preparation and tapeout

"Tapeout" is the moment the final GDSII/OASIS database is released to the mask shop (the name is a fossil of magnetic tape).

What happens next:
1. **Fracturing** — convert polygons to the writer's primitive shapes.
2. **RET (resolution enhancement)** — **OPC** (optical proximity correction: pre-distort features so the printed image is right), **sub-resolution assist features** (SRAFs: printed-invisible scattering bars that improve process window), **phase-shift masks**, **source-mask optimisation** (co-optimise the illumination pupil and the mask), and **inverse lithography technology** for the hardest layers. OPC on a leading-edge layer is a large-compute job — thousands of CPU-hours per layer is routine.
3. **Multi-patterning decomposition** — split one design layer into two or more mask layers (LELE, LELELE, SADP, SAQP; see `05`).
4. **Mask writing** — multi-beam electron-beam writers (NuFlare, IMS Nanofabrication) on quartz blanks; EUV masks are reflective Mo/Si multilayer blanks with a tantalum-based absorber, and Hoya is essentially the sole qualified supplier of EUV blanks.
5. **Mask inspection and repair**, then **pellicle mounting** (DUV masks routinely; EUV pellicles are difficult — see `06`).

### What a tapeout costs

> ⚠️ All leading-edge mask-set and NRE prices are confidential. The figures below are widely-cited industry *estimates* (largely originating from International Business Strategies, IBS, and repeated in trade press). Treat them as order-of-magnitude, not quotations. Status of this subsection: `needs-verification`.

| Node | Typical full mask set (est.) | Typical total design NRE (est.) |
|---|---|---|
| 130 nm | ~US$0.2–0.4 m | ~US$3–10 m |
| 65 nm | ~US$1–2 m | ~US$20–30 m |
| 28 nm | ~US$2–3 m | ~US$40–50 m |
| 16/14 nm FinFET | ~US$5–8 m | ~US$80–100 m |
| 7 nm | ~US$10–15 m | ~US$200–300 m |
| 5 nm | ~US$15–20 m | ~US$400–550 m |
| 3 nm | ~US$20–30 m | ~US$500–1,000 m |
| 2 nm | reported to exceed US$30 m | reported around US$0.7–1.5 bn for a large SoC |

Design NRE is dominated by *people*, not masks: verification headcount, IP licences, EDA licences, emulation capacity, and multiple respin allowances. The practical consequence is that only products with very large volumes or very high ASPs can justify a leading-edge tapeout — which is why 28 nm and 22FDX remain enormous, profitable nodes, and why chiplets (`04`) are attractive: reuse a proven expensive die across many products.

**Shuttle / MPW services** cut the entry cost by sharing a mask set across many customers: Europractice, MOSIS (historically), CMP (Grenoble), TSMC's CyberShuttle, Muse Semiconductor. A small block on a mature-node shuttle can be a few tens of thousands of dollars; Tiny Tapeout (`09`) reduces this to the low hundreds by sharing a single die.

## 9. The EDA vendors

| Vendor | Position | Flagship tools |
|---|---|---|
| **Synopsys** | ~31% share (2024); ~US$6.1 bn revenue, ~28,000 employees; acquired Ansys for US$35 bn (closed 17 July 2025) | Design Compiler, Fusion Compiler, IC Compiler II, PrimeTime (STA signoff reference), VCS (simulation), Verdi (debug), VC Formal, TestMAX, StarRC, IC Validator, ZeBu (emulation), HAPS (prototyping), plus a very large IP portfolio |
| **Cadence** | ~30% share (2024) | Genus (synthesis), Innovus (place & route), Tempus (STA), Voltus (power), Quantus (extraction), Pegasus (DRC), Xcelium (simulation), JasperGold (formal), Palladium (emulation), Protium (prototyping), Virtuoso (the analog/custom standard), Spectre (SPICE), Allegro (PCB) |
| **Siemens EDA** (formerly Mentor Graphics) | ~13% share (2024) | **Calibre** (the DRC/LVS signoff standard), Questa (simulation/formal/CDC), Tessent (DFT), Catapult (HLS), Veloce (emulation), Solido (variation-aware), Xpedition (PCB) |
| **Ansys** (now Synopsys) | Multiphysics | RedHawk-SC (power integrity), Totem, HFSS (electromagnetics), Icepak (thermal) |
| **Keysight**, **Silvaco**, **Empyrean**, **Primarius** | Niche/regional | RF/system design; Empyrean and Primarius are the leading Chinese EDA vendors, strategically important since the May 2025 US restrictions on EDA supply to China |
| **Open source** | Education, research, small nodes | Yosys, OpenROAD, OpenLane, OpenSTA, Magic, KLayout, netgen, ngspice, Verilator, cocotb |

Two structural facts about this industry: revenue is overwhelmingly recurring (time-based licences plus IP royalties), and the tools are co-developed with foundries — a PDK is only usable if the tools are certified against it, which is why a new EDA entrant cannot simply appear at 3 nm.

## 10. AI in the flow

Since about 2020 the vendors have shipped reinforcement-learning and Bayesian-optimisation layers over the existing engines: Synopsys **DSO.ai**, Cadence **Cerebrus**, Siemens **Solido**. They search the tool's own parameter space (placement effort levels, utilisation, buffer strategies, Vt mixes) across many parallel runs, and are credibly reported to find 5–15% power or area improvements over expert-tuned flows while cutting the tuning time from weeks to days. OpenROAD's **AutoTuner** is the open equivalent. What they do not do is replace the physical-design engineer: they replace the sweep-and-compare labour that engineer used to perform.

## Open questions

- Mask-set and design-NRE figures in §8 are secondary-source estimates and could not be confirmed against a primary source in this pass — marked `needs-verification`.
- Cadence's latest fiscal-year revenue could not be verified (Wikipedia carries a stale 2021 figure of US$3 bn / 9,300 employees); see `07`.
- Exact metal-layer counts and cell-track heights for TSMC N2 and Intel 18A are not publicly disclosed.

## Sources

- [Synopsys — Wikipedia](https://en.wikipedia.org/wiki/Synopsys) — accessed 2026-08-25
- [Cadence Design Systems — Wikipedia](https://en.wikipedia.org/wiki/Cadence_Design_Systems) — accessed 2026-08-25
- [3 nm process — Wikipedia](https://en.wikipedia.org/wiki/3_nm_process) — accessed 2026-08-25
- [2 nm process — Wikipedia](https://en.wikipedia.org/wiki/2_nm_process) — accessed 2026-08-25
- [Photolithography — Wikipedia](https://en.wikipedia.org/wiki/Photolithography) — accessed 2026-08-25
- [OpenROAD Project — Wikipedia](https://en.wikipedia.org/wiki/OpenROAD_Project) — accessed 2026-08-25
- [Intel 18A process technology](https://www.intel.com/content/www/us/en/foundry/process/18a.html) — Intel, accessed 2026-08-25
