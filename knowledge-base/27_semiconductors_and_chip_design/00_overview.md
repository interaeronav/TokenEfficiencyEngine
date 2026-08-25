---
id: semi.overview
title: Semiconductors and chip design — domain map and industry structure
domain: 27_semiconductors_and_chip_design
tags: [semiconductors, chip-design, foundry, fabless, idm, eda, osat, industry-structure, domain-map]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "TSMC 2Q26 Quarterly Results", url: "https://investor.tsmc.com/english/quarterly-results/2026/q2", publisher: "TSMC Investor Relations", accessed: 2026-08-25}
  - {title: "TSMC", url: "https://en.wikipedia.org/wiki/TSMC", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Foundry model", url: "https://en.wikipedia.org/wiki/Foundry_model", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Synopsys", url: "https://en.wikipedia.org/wiki/Synopsys", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "ASML Holding", url: "https://en.wikipedia.org/wiki/ASML_Holding", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Intel 18A process", url: "https://www.intel.com/content/www/us/en/foundry/process/18a.html", publisher: "Intel Corporation", accessed: 2026-08-25}
  - {title: "TSMC 2nm Technology", url: "https://www.tsmc.com/english/dedicatedFoundry/technology/logic/l_2nm", publisher: "TSMC", accessed: 2026-08-25}
related: [semi.physics, semi.rtl, semi.physical_design, semi.architecture, semi.fabrication, semi.euv, semi.firms, semi.economics, semi.career, semi.resources]
---

# Semiconductors and chip design — domain map and industry structure

**Summary.** The semiconductor industry is not one industry but a stack of eight interlocking ones, each with a different business model, a different margin structure and, in several layers, a single dominant supplier. Design intent flows down the stack — IP → EDA → design house → foundry → OSAT → product — while physical capability flows up from materials and equipment. The economically decisive fact is that at the leading edge each layer has collapsed to between one and three viable suppliers: one lithography vendor (ASML) for EUV, three EDA vendors, effectively one foundry (TSMC) at 2 nm volume, three DRAM makers. This file maps the domain, defines the business models, and indexes files 01–10.

## Key facts

| Item | Value (dated) | File |
|---|---|---|
| TSMC quarterly revenue, 2Q 2026 | US$40.20 bn; gross margin 67.7%, operating margin 60.3% | `07` |
| TSMC share of global foundry market | ~70% (Wikipedia summary, 2025) | `07`, `08` |
| ASML share of lithography equipment sales | 83% (2025); ~100% of EUV | `06`, `07` |
| EDA market shares, 2024 | Synopsys 31%, Cadence 30%, Siemens EDA 13% (~75% combined) | `03`, `07` |
| TSMC N2 (2 nm, nanosheet GAA) | Volume production started 4Q 2025 | `06` |
| Intel 18A (RibbonFET + PowerVia) | In high-volume manufacturing in the US (Intel, 2026) | `06` |
| TSMC A16 (backside power) | Production-ready 2H 2026; +8–10% speed vs N2P | `06` |
| Cost of a leading-edge fab | TSMC "over US$45 bn" for a 2 nm fab (2025) | `08` |
| Price of an EUV scanner | ~US$200 m (NXE class); ~US$370 m (High-NA EXE) | `06`, `08` |
| Wafer diameter at the leading edge | 300 mm; 450 mm abandoned (consortium disbanded 2017) | `05` |

## The eight layers of the stack

### 1. Semiconductor IP (silicon IP, "SIP")

Companies that sell *designs*, not chips. Arm licenses CPU architectures and cores; Synopsys, Cadence, Rambus, Alphawave and Imagination license interface controllers and PHYs (DDR, PCIe, USB, SerDes, HBM), embedded memories and analog macros. Revenue model: an up-front licence fee plus a per-unit royalty (Arm's FY2025 revenue was US$4.01 bn on 8,330 employees). RISC-V is the structural threat to this layer: the ISA itself is free, so value migrates to implementations and verification.

**Why it exists.** Nobody designs a PCIe 6.0 PHY from scratch for a single chip; the NRE would exceed the product's lifetime margin. IP reuse is what makes a 100-billion-transistor SoC tractable for a team of a few hundred engineers.

### 2. EDA (electronic design automation)

The software that turns human design intent into manufacturable geometry. Three vendors hold about 75% of the market (2024): Synopsys (31%), Cadence (30%), Siemens EDA, formerly Mentor Graphics (13%). Ansys — acquired by Synopsys for US$35 bn, closed 17 July 2025 — supplies multiphysics, thermal and power-integrity signoff. See `03`.

EDA is a small industry (single-digit billions per vendor) that gates a multi-hundred-billion-dollar one. It is also a chokepoint of geopolitics: in May 2025 the US restricted Cadence, Synopsys and Siemens from supplying China.

### 3. Fabless design houses

Design and sell chips; own no fabs. NVIDIA, Qualcomm, Broadcom, AMD, MediaTek, Apple (for its own use), Marvell, and the hyperscaler silicon teams (Google, Amazon, Microsoft, Meta). Gross margins run 45–75%; the capital burden is R&D and mask sets, not buildings. NVIDIA is the extreme case — fiscal 2025 revenue US$130.5 bn and net income US$72.9 bn with no wafer fab of its own.

### 4. IDMs (integrated device manufacturers)

Design *and* fabricate. Intel, Samsung (which is simultaneously an IDM and a foundry), Micron, SK Hynix, Texas Instruments, Infineon, STMicroelectronics, NXP, Analog Devices. The IDM model survives best where the process *is* the product — memory (DRAM/NAND), power devices (SiC, IGBT), precision analog — and where process and circuit must be co-optimised. It has largely failed at leading-edge logic: Intel is the only Western IDM still attempting 2 nm-class logic, and it lost US$0.3 bn on US$52.9 bn revenue in 2025.

### 5. Pure-play foundries

Manufacture to other companies' designs and (formally) never compete with the customer. TSMC (founded 1987, the model's inventor), Samsung Foundry, GlobalFoundries (exited the leading edge in 2018 at 14 nm), UMC, SMIC, Tower, VIS, Rapidus (pre-production). TSMC's ~70% share of foundry revenue and near-total share of leading-edge logic is the single most important structural fact in the industry.

The foundry's product is not a chip, it is a **PDK** — the process design kit, comprising design rules, SPICE models, standard-cell libraries, IO and memory compilers, and the sign-off decks that let a customer's EDA tools target the process. See `03`.

### 6. OSAT (outsourced semiconductor assembly and test)

Packaging, assembly and final test. ASE Technology (the largest), Amkor, JCET, Powertech, TongFu. Historically the commodity end of the chain; advanced packaging has made it strategic. Crucially, the most advanced 2.5D/3D packaging — TSMC's CoWoS and SoIC, Intel's EMIB and Foveros — is done *by the foundry*, not the OSAT, because it requires wafer-level processing. CoWoS capacity, not wafer capacity, has been the binding constraint on AI accelerator supply since 2023.

### 7. Equipment (WFE — wafer fab equipment)

ASML (lithography; €28.26 bn revenue 2024, 43,395 employees), Applied Materials (deposition, etch, implant, CMP; US$27.176 bn FY2024), Lam Research (etch and deposition), Tokyo Electron (coat/develop track, etch, clean), KLA (process control and inspection; US$12.2 bn FY2025). Each is a near-monopolist or duopolist in its niche. A single EUV scanner costs ~US$200 m; a High-NA EXE system ~US$370 m.

### 8. Materials and substrates

Silicon wafers (Shin-Etsu, SUMCO, Siltronic, GlobalWafers), photoresist (JSR, Tokyo Ohka, Shin-Etsu, Fujifilm), specialty gases (Linde, Air Liquide), CMP slurries and pads (Cabot, DuPont), photomask blanks (Hoya, AGC — Hoya is essentially the sole supplier of EUV mask blanks), and ABF substrate (Ajinomoto build-up film, a single Japanese chemical company's product that gates every high-end package).

## How a chip actually gets made — the end-to-end path

1. **Specification and architecture** (`04`) — 6–18 months. Performance targets, power envelope, ISA choice, memory hierarchy, die/chiplet partitioning.
2. **RTL design and verification** (`02`) — the largest headcount. Verification is typically 60–70% of engineering effort on a complex SoC.
3. **Synthesis, physical design, signoff** (`03`) — netlist → placement → clock tree → route → parasitic extraction → timing/power/IR/EM signoff → DRC/LVS clean GDSII.
4. **Mask making and tapeout** (`03`, `05`) — GDSII → OPC/RET → mask writing. A leading-edge mask set is the single largest NRE item.
5. **Wafer fabrication** (`05`, `06`) — 1,000–1,500+ process steps and 3–4 months cycle time at the leading edge.
6. **Wafer test (sort), dicing, packaging, final test** (`05`) — increasingly the differentiating step (`04` on chiplets).
7. **Qualification and ramp** — reliability (HTOL, ESD, latch-up), yield learning, volume ramp.

## The three scaling levers, in the order the industry now pulls them

Classic dimensional scaling has slowed (`01`). The industry now compounds three separate levers:

- **Device architecture** — planar → FinFET (2011–2012) → nanosheet gate-all-around (2022 Samsung, 2025 TSMC/Intel) → forksheet/CFET (research). Each transition buys electrostatic control, not raw area (`01`).
- **Design-technology co-optimisation (DTCO)** — cell architecture (fin depopulation, NanoFlex-style mixed cell heights), buried power rails, backside power delivery (Intel PowerVia, TSMC Super Power Rail). Intel claims PowerVia cuts worst-case dynamic voltage droop by up to 10×; TSMC claims A16 gives +8–10% speed or −15–20% power versus N2P.
- **System technology co-optimisation (STCO)** — chiplets and advanced packaging. Splitting a reticle-limited die into chiplets on an interposer is now a first-order performance and yield lever, not a packaging afterthought (`04`).

## The geography, in one paragraph

Leading-edge logic: Taiwan (TSMC), South Korea (Samsung), and — for the first time in a decade — the United States (Intel 18A, TSMC Arizona). DRAM: South Korea (Samsung, SK Hynix), United States (Micron), China (CXMT, ~4% share Q2 2025). NAND: South Korea, Japan (Kioxia), United States, China (YMTC). Lithography: the Netherlands, exclusively. Photoresist and mask blanks: Japan, overwhelmingly. Assembly and test: Taiwan, China, Malaysia, the Philippines. Legacy analog and power: Europe, the US, Japan, and increasingly China. The concentration is not an accident of policy; it is the endpoint of fifty years of scale economics meeting learning curves (`08`).

## What "nm" means now — read this before believing any node number

Since roughly the 22/20 nm generation, node names have been marketing labels, not physical measurements. Nothing on a "3 nm" chip is 3 nm. The physically meaningful numbers are:

- **CPP / contacted poly pitch (gate pitch)** — ~45 nm at both TSMC N3 and the 2 nm-class generation.
- **MMP / minimum metal pitch** — 23 nm at TSMC N3E; ~20 nm at 2 nm-class nodes.
- **Cell height** in metal tracks (e.g. 6T, 5T) and fin/nanosheet count.
- **SRAM bit-cell area** — 0.0199 µm² for TSMC N3, 0.021 µm² for N3E. SRAM has scaled far worse than logic since 5 nm, which is why cache now dominates die area and drives chiplet partitioning.
- **Transistor density in MTr/mm²** — only comparable when the same mix of high-density and high-performance cells is quoted. Rapidus reported 237.31 MTr/mm² for a 2 nm prototype wafer (18 July 2025).

`06` treats this in full.

## Reading order

| File | Covers |
|---|---|
| `01_semiconductor-physics.md` | Bands, doping, junctions, MOSFET operation, 60 mV/dec, leakage, Dennard, Moore, device roadmap |
| `02_digital-design-and-rtl.md` | HDLs, RTL practice, CDC, synthesis, STA, DFT, formal, UVM, FPGA, open-source flow |
| `03_physical-design-and-eda.md` | Netlist→GDSII, PDK, standard cells, IR/EM, EDA vendors, tapeout cost |
| `04_computer-architecture.md` | ISAs, pipelines, OoO, caches, memory, NoC, chiplets, GPUs, NPUs, accelerators |
| `05_fabrication-process.md` | Crystal growth to final test, every unit process, step counts, cycle time |
| `06_euv-and-leading-edge.md` | EUV physics and tools, node-by-node roadmaps, 2 nm status as of 2026 |
| `07_the-major-firms.md` | ~24 company profiles with dated financials |
| `08_industry-economics-and-geopolitics.md` | Fab economics, wafer pricing, export controls, subsidies, risk |
| `09_getting-into-chip-design.md` | Education, skills, free routes, TinyTapeout, interviews, career ladder |
| `10_books-and-resources.md` | Annotated register of books, courses, media, conferences, standards |

## Where the money sits in the stack

Value is not distributed evenly along the chain, and the distribution has moved sharply since 2020. A rough picture of gross-margin bands, all figures dated to the latest verified fiscal period in `07`:

| Layer | Representative gross margin | Capital intensity | Supplier count at leading edge |
|---|---|---|---|
| Silicon IP | 90%+ (Arm) | Very low | 1 dominant (Arm) + RISC-V commons |
| EDA | 80%+ | Very low | 3 |
| Fabless logic | 45–75% (NVIDIA far above) | Low–medium | Many, but few at 3 nm and below |
| Leading-edge foundry | 67.7% (TSMC 2Q 2026) | Extreme | Effectively 1 at 2 nm volume |
| Memory (cyclical) | −20% to +60% across a cycle | Extreme | 3 DRAM, 5–6 NAND |
| Equipment | 45–60% | Medium | 1–3 per process step |
| OSAT | 15–25% | Medium–high | Many |
| Materials | 25–45% | Medium | 1–4 per material |

Two consequences follow. First, the *thin* layers — IP and EDA, together well under US$30 bn of annual revenue — exert leverage wildly out of proportion to their size, which is exactly why they are the first instruments reached for in export-control policy (`08`). Second, the extreme-capital layers (foundry, memory, equipment) cannot respond quickly to demand shocks: a greenfield leading-edge fab takes roughly three to four years from ground-breaking to qualified volume output, and an EUV scanner has a multi-quarter lead time. The 2023–2026 AI build-out therefore expressed itself first as price inflation and allocation queues — in HBM, in CoWoS slots, and from late 2025 in commodity DRAM, where some categories rose by more than 200% between early 2025 and early 2026 as HBM crowded out conventional DRAM capacity.

Third-order effect, worth stating plainly: because packaging capacity and memory now gate accelerator shipments as tightly as wafer capacity does, "how many chips can be built" is no longer answerable from front-end capacity alone. `08` develops this.

## Open questions

- Precise current foundry market-share percentages by quarter (TrendForce data is paywalled); the ~70% figure is a secondary-source summary.
- Broadcom, Lam Research, Cadence and Tokyo Electron latest-fiscal-year revenue could not be verified from primary sources in this pass — see `07` for flags.

## Sources

- [TSMC 2Q26 Quarterly Results](https://investor.tsmc.com/english/quarterly-results/2026/q2) — TSMC Investor Relations, accessed 2026-08-25
- [TSMC — Wikipedia](https://en.wikipedia.org/wiki/TSMC) — accessed 2026-08-25
- [Foundry model — Wikipedia](https://en.wikipedia.org/wiki/Foundry_model) — accessed 2026-08-25
- [Synopsys — Wikipedia](https://en.wikipedia.org/wiki/Synopsys) — accessed 2026-08-25
- [ASML Holding — Wikipedia](https://en.wikipedia.org/wiki/ASML_Holding) — accessed 2026-08-25
- [Intel 18A process technology](https://www.intel.com/content/www/us/en/foundry/process/18a.html) — Intel, accessed 2026-08-25
- [TSMC 2nm Technology](https://www.tsmc.com/english/dedicatedFoundry/technology/logic/l_2nm) — TSMC, accessed 2026-08-25
- [TSMC A16 Technology](https://www.tsmc.com/english/dedicatedFoundry/technology/logic/l_A16) — TSMC, accessed 2026-08-25
- [3 nm process — Wikipedia](https://en.wikipedia.org/wiki/3_nm_process) — accessed 2026-08-25
- [Rapidus — Wikipedia](https://en.wikipedia.org/wiki/Rapidus) — accessed 2026-08-25

