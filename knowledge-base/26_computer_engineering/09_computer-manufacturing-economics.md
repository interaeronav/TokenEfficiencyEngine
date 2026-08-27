---
id: compeng.manufacturing
title: How computers get made and who makes the money
domain: 26_computer_engineering
tags: [semiconductors, value-chain, foundry, fabless, osat, odm, ems, foxconn, tsmc, arm, memory-cycle, chips-act, supply-chain, ai-datacentre, margins]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "TSMC 2Q26 quarterly results", url: "https://investor.tsmc.com/english/quarterly-results/2026/q2", publisher: "TSMC Investor Relations", accessed: 2026-08-25}
  - {title: "TSMC 2Q25 quarterly results", url: "https://investor.tsmc.com/english/quarterly-results/2025/q2", publisher: "TSMC Investor Relations", accessed: 2026-08-25}
  - {title: "Apple reports third quarter results (FY2026)", url: "https://www.apple.com/newsroom/2026/07/apple-reports-third-quarter-results/", publisher: "Apple Inc.", accessed: 2026-08-25}
  - {title: "NVIDIA announces financial results for Q2 fiscal 2026", url: "https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-second-quarter-fiscal-2026", publisher: "NVIDIA", accessed: 2026-08-25}
  - {title: "Arm Holdings", url: "https://en.wikipedia.org/wiki/Arm_Holdings", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Foxconn", url: "https://en.wikipedia.org/wiki/Foxconn", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Foundry model", url: "https://en.wikipedia.org/wiki/Foundry_model", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Semiconductor fabrication plant", url: "https://en.wikipedia.org/wiki/Semiconductor_fabrication_plant", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Dynamic random-access memory", url: "https://en.wikipedia.org/wiki/Dynamic_random-access_memory", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "CHIPS and Science Act", url: "https://en.wikipedia.org/wiki/CHIPS_and_Science_Act", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "European Chips Act", url: "https://en.wikipedia.org/wiki/European_Chips_Act", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "IDC Worldwide Quarterly Personal Computing Device Tracker (promo page)", url: "https://www.idc.com/promo/pcdforecast", publisher: "IDC", accessed: 2026-08-25}
related: [compeng.overview, compeng.careers, semiconductors.overview]
unit_system: SI
---

# How computers get made and who makes the money

**Summary.** A computer is assembled from IP that someone licensed, silicon that someone else fabricated, packages that a third party assembled and tested, boards that a contract manufacturer built, and a brand that captured most of the margin. Value is distributed along that chain very unevenly, and the distribution has shifted sharply toward the top since 2023. This file traces the chain, gives verified margin figures at each step, covers fab economics, the memory cycle, the AI datacentre buildout, geographic concentration and the reshoring programmes. Cross-reference `27_semiconductors_and_chip_design` for process technology and design flows.

## Key facts — verified

| Company | Metric | Value | Period | Source |
|---|---|---|---|---|
| **TSMC** | Net revenue | **US$40.20bn** | 2Q 2026 | TSMC IR |
| TSMC | Gross margin | **67.7%** | 2Q 2026 | TSMC IR |
| TSMC | Operating margin | **60.3%** | 2Q 2026 | TSMC IR |
| TSMC | Guidance | US$44.6–45.8bn rev, 65.0–67.0% GM | 3Q 2026 | TSMC IR |
| TSMC | Net revenue / GM / OM | US$30.07bn / 58.6% / 49.6% | 2Q 2025 | TSMC IR |
| **NVIDIA** | Revenue | **US$46.7bn** (+56% YoY) | Q2 FY2026 (ended 27 Jul 2025) | NVIDIA |
| NVIDIA | Data centre revenue | **US$41.1bn** (88% of total) | Q2 FY2026 | NVIDIA |
| NVIDIA | GAAP gross margin | **72.4%** | Q2 FY2026 | NVIDIA |
| NVIDIA | GAAP net income | US$26.42bn | Q2 FY2026 | NVIDIA |
| **Apple** | Revenue | **US$109.4bn** (+16% YoY) | Q3 FY2026 (June quarter) | Apple |
| Apple | Gross margin | **50.1%** (incl. ~2pp from tariff refunds) | Q3 FY2026 | Apple |
| **Arm** | Revenue / net income | **US$4.01bn / US$792m** | FY2025 | Wikipedia |
| Arm | SoftBank ownership | 87.1% after Sept 2023 IPO (raised $4.87bn at $54.5bn valuation) | 2023– | Wikipedia |
| **Foxconn (Hon Hai)** | Revenue | **NT$6.16tn ≈ US$198.5bn** | FY2023 | Wikipedia |
| Foxconn | Workforce | **>1,000,000** | — | Wikipedia |
| Foundry market | Total annual revenue | US$111.54bn | 2023 | Wikipedia |
| PC market | Shipments | **65.6m units, +3% YoY** | Q1 2026 | IDC |

> ⚠️ **The single most important comparison in this file.** TSMC's 2Q26 gross margin was **67.7%** and NVIDIA's **72.4%**; Foxconn, which physically builds a very large share of the world's electronics, had FY2023 revenue of roughly US$198.5bn — comparable in scale to TSMC's annual revenue — on operating margins that are conventionally reported at low single digits (**not verified for this file**). Value in electronics accrues to whoever controls a scarce, defensible design or process step, and almost never to whoever does the assembly.

## 1. The value chain, step by step

```
 IP / EDA          Fabless design      Foundry          OSAT           ODM / EMS        Brand        Retail
 ────────          ──────────────      ───────          ────           ──────────       ─────        ──────
 Arm               Apple silicon       TSMC             ASE            Foxconn          Apple        Amazon
 Synopsys          Nvidia              Samsung Foundry  Amkor          Quanta           Dell         Best Buy
 Cadence           AMD                 Intel Foundry    JCET           Compal           HP           carriers
 Siemens EDA       Qualcomm            GlobalFoundries  SPIL           Wistron          Lenovo       channel
 Imagination       Broadcom            UMC              PTI            Pegatron         Samsung
 SiFive            MediaTek            SMIC             Tongfu         Flex, Jabil      Nvidia (DGX)
 RISC-V Intl.      Marvell             Rapidus          ChipMOS        Celestica
```

**IP and EDA — tiny revenue, enormous leverage.** Arm's entire FY2025 revenue was **US$4.01bn** on **US$792m** net income, from a company whose architecture is in the overwhelming majority of the world's mobile devices. Arm licenses designs and instruction-set architectures; it manufactures nothing. Its model is an up-front licence fee plus a per-chip royalty, and in March 2023 it announced a shift toward royalties based on **device** value rather than chip value — a direct attempt to capture more of the value it enables. SoftBank retains 87.1% after the September 2023 Nasdaq IPO, which raised $4.87bn at a $54.5bn valuation. The EDA duopoly-plus-one — Synopsys, Cadence, Siemens EDA — occupies the same structural position: without their tools no advanced chip can be designed, which makes them a chokepoint and, consequently, an export-control instrument.

**Fabless design — where the margin is.** NVIDIA at 72.4% GAAP gross margin owns no fab. Apple's silicon team designs the M- and A-series and buys manufacturing. Qualcomm, AMD, Broadcom, MediaTek and Marvell operate the same way. The fabless model separates the two hardest problems in the industry — architecture and manufacturing — and lets each be capitalised independently. It is why the modern industry exists in the shape it does.

**Foundry — capital-intensive, and increasingly a natural monopoly at the leading edge.** TSMC in 2Q26 posted **US$40.20bn revenue, 67.7% gross margin, 60.3% operating margin**, up from US$30.07bn / 58.6% / 49.6% a year earlier. A foundry business earning 60% operating margins is not behaving like a commodity manufacturer; it is behaving like the sole supplier of something nobody else can make. The total foundry market was US$111.54bn in 2023, and TSMC held 55.9% as far back as 2017 — its share at the leading edge is far higher than its share overall.

**OSAT — outsourced assembly and test.** After wafers leave the fab they must be diced, packaged, interconnected and tested. Historically the lowest-margin step and treated as a commodity — until advanced packaging (2.5D interposers, CoWoS, chiplets, HBM stacking) became the actual bottleneck for AI accelerators. Packaging capacity, not wafer capacity, has repeatedly been the binding constraint on AI GPU supply. The leading OSATs are ASE (Taiwan), Amkor (US/Korea), JCET (China), SPIL and Powertech; TSMC also does its own advanced packaging, which is part of why it captures so much of the value.

**ODM and EMS — enormous revenue, thin margins.** An **ODM** (original design manufacturer) designs *and* builds a product a brand puts its name on; an **EMS** (electronics manufacturing services) provider builds to the customer's design. Foxconn/Hon Hai is the largest, at roughly **US$198.5bn revenue in FY2023** and **over a million employees**, and has been named the world's largest EMS company for fourteen consecutive years. As of 2012 it was reported to manufacture around 40% of worldwide consumer electronics. Quanta, Compal and Wistron between them build the majority of the world's notebooks; Pegatron, Flex, Jabil and Celestica fill out the tier. These companies operate on volume, working-capital efficiency and labour arbitrage. Their bargaining position against a single dominant customer is weak, and that is the whole story of their margins.

**Brand — the second-largest capture point.** Apple at **50.1% gross margin on US$109.4bn of quarterly revenue** is the extreme case, and it is not an accident: Apple designs its own silicon (capturing fabless margin), owns the OS and the ecosystem, and outsources only the low-margin steps. Dell, HP and Lenovo, which own neither silicon nor OS, run gross margins a fraction of that.

**Retail and channel** — a few percent, and shrinking as direct-to-consumer grows.

## 2. Bill of materials — the shape, and what is verifiable

The BOM is what the brand pays for components. Everything between BOM and retail price covers assembly, logistics, warranty, R&D amortisation, marketing, channel margin and profit.

The rough component structure of a modern laptop, by descending cost share:

1. **SoC / CPU (+ discrete GPU if present)** — the largest single line, and the one whose price the brand least controls.
2. **Display panel** — assembly including backlight, touch layer and glass. Usually second, and higher on high-refresh or OLED units.
3. **Memory and storage** — DRAM plus NVMe SSD. **This line is violently cyclical** (see §4) and in 2025–26 has moved from a modest share to a major one.
4. **Battery, chassis and thermals** — mechanical content; higher for premium aluminium unibody designs.
5. **Board, power delivery, connectivity** — PCB, VRMs, Wi-Fi/BT module, USB-C/Thunderbolt controllers.
6. **Camera, audio, keyboard, trackpad, sensors.**
7. **Assembly and test labour** — small, single-digit percent of BOM for a laptop.

For a flagship smartphone the ordering is similar, with the display and the camera subsystem taking a larger share and the SoC still the largest single item; the modem is a substantial separate line where it is not integrated.

> ⚠️ **No verified per-component BOM figures are given here.** Counterpoint Research's teardown pages returned no data content, and no primary teardown source with per-line dollar figures could be fetched. Widely circulated teardown numbers (typically placing a flagship phone BOM at roughly 30–45% of its unpaid retail price) are **`needs-verification`** and are deliberately omitted rather than repeated. The *structure* above is safe; the numbers are not.

What is verifiable is the destination: Apple's **50.1%** gross margin in the June 2026 quarter is a company-level figure that bounds how much of a device's retail price is not component cost.

## 3. Fab economics and capital intensity

Semiconductor fabrication is among the most capital-intensive activities in the world economy.

| Item | Figure | Source |
|---|---|---|
| Cost of a new fab | "over one billion U.S. dollars", with "tens of billions not being uncommon" | Wikipedia |
| TSMC 2nm fab investment | **over US$45bn** | Wikipedia (referenced 2025) |
| Typical 300mm process tool | upwards of **US$4m each** | Wikipedia |
| EUV scanner | up to **US$340m** | Wikipedia |
| Tools per fab | several hundred | Wikipedia |
| Upgrading an existing fab to a newer node | often exceeds the cost of a new one | Wikipedia |

The economics that follow from those numbers:

- **Utilisation is everything.** Depreciation dominates the cost structure, so a fab running at 95% and a fab running at 60% have wildly different unit costs. This is why foundries chase long-term customer commitments and why downturns hit margins so hard.
- **Yield is the second lever.** A defect density improvement that raises yield from 60% to 80% cuts effective cost per good die by a quarter with no change in capital.
- **Only a handful of firms can play at the leading edge.** TSMC, Samsung Foundry and Intel Foundry are the credible list for the most advanced nodes. The barrier is not knowledge; it is the willingness and ability to commit tens of billions per node against uncertain demand.
- **ASML is the single narrowest point in the entire global economy's supply chain.** It is the only supplier of EUV lithography systems. No EUV, no leading-edge logic — which is precisely why EUV is the primary instrument of semiconductor export control.
- **Trailing-edge fabs are a different business** — depreciated equipment, mature processes, automotive and industrial customers, and much lower margins but much lower risk. Much of China's capacity expansion has been here.

## 4. The memory cycle

Memory is the commodity end of semiconductors and the most violently cyclical major market in technology. DRAM is supplied by essentially three firms — **Samsung Electronics, SK Hynix and Micron Technology** — and NAND by a similarly short list.

The dynamic: memory is fungible, so producers compete on price; capacity is added in large, lumpy, multi-year increments; demand is volatile. The result is a repeating boom–bust in which prices can move by factors, not percentages.

Verified data points:
- **2017:** DRAM price per bit rose **47%**, "the largest jump in 30 years since the 45% jump in 1988".
- **1985:** during the US–Japan trade dispute, 64K DRAM prices "plummeted to as low as 35 cents apiece from $3.50 within 18 months" — a 90% collapse. Intel exited DRAM entirely by early 1985.
- **Early 2026:** DRAM prices have seen "compounded increases, some exceeding **200%**, since early 2025", driven by AI demand, with **HBM production crowding out standard DRAM capacity at a 3-to-1 conversion ratio**.

That last figure is the most important single line in this file for anyone building or buying computers in 2026. High-bandwidth memory for AI accelerators consumes roughly three units of wafer capacity for every one unit of conventional DRAM it displaces, so the AI buildout is directly and mechanically inflating the price of memory in laptops, phones, servers and consoles. It is the clearest example of the AI capital cycle spilling into consumer prices.

## 5. Market structure — PCs, servers, AI

**PCs.** IDC reported **65.6m units shipped in Q1 2026, up 3% year on year**. The market is consolidated among Lenovo, HP, Dell, Apple, Asus and Acer, all of whom outsource manufacturing to the same handful of Taiwanese ODMs — so brand competition sits on top of a shared, and highly concentrated, manufacturing base. **Vendor-level share figures could not be verified for this file.**

**Servers and datacentre.** The structural shift of the decade: hyperscalers (AWS, Microsoft, Google, Meta, and in China Alibaba, Tencent, ByteDance) buy directly from ODMs, bypassing the traditional server brands entirely, and increasingly design their own silicon — AWS Graviton and Trainium, Google TPU, Microsoft Cobalt and Maia, Meta MTIA. Every one of those is an Arm-based or custom accelerator design manufactured at TSMC. The traditional server OEMs have been squeezed into enterprise and edge.

**AI accelerators.** NVIDIA's Q2 FY2026 (quarter ended 27 July 2025) data centre revenue of **US$41.1bn** was **88% of its US$46.7bn total**, up 56% year on year, at a **72.4% GAAP gross margin**. That is not a hardware business's margin structure; it is a platform business's, and CUDA is the reason. The competitive question for the rest of the decade is whether AMD's ROCm, the hyperscalers' in-house silicon, or an open compiler stack can erode that software moat, because the hardware gap is narrower than the ecosystem gap.

**The AI datacentre buildout economics.** The chain runs: hyperscaler capex → accelerator purchases → TSMC leading-edge and CoWoS packaging capacity → HBM from SK Hynix/Samsung/Micron → power. Two constraints bind hardest. **Advanced packaging** capacity has repeatedly been the limiting factor on GPU supply. And **electrical power** has become the binding constraint on siting: a large AI training campus draws power at a scale that competes with a small city, and grid interconnection queues, not construction, now set the schedule in many regions. The open financial question is depreciation — whether accelerators bought in 2025–26 have a useful economic life closer to three years or six materially changes the return on the entire buildout, and reasonable analysts disagree.

## 6. Geography and concentration risk

- **Leading-edge logic manufacturing is concentrated in Taiwan**, principally at TSMC. This is the single largest concentration risk in the world economy, and the reason "silicon shield" is a term of art in geopolitics.
- **Memory** is concentrated in South Korea (Samsung, SK Hynix) with Micron in the US, Japan, Singapore and Taiwan.
- **EUV lithography** is a single-vendor monopoly at ASML in the Netherlands, dependent in turn on Zeiss optics in Germany and a long tail of specialised suppliers.
- **Assembly and packaging** is concentrated in Taiwan, China, South Korea, Malaysia, the Philippines and Vietnam.
- **Final assembly** is concentrated in China, with substantial and growing shifts to Vietnam and India.
- **Chemicals, gases, photoresists and substrates** are heavily concentrated in Japan — a dependency demonstrated in the 2019 Japan–Korea export dispute.
- **Raw materials** — gallium, germanium, rare earths, and high-purity quartz from a very small number of sources.

Every one of these is a single point of failure for the global economy, and several of them are within a few hundred kilometres of each other.

**Export controls.** Since October 2022 the United States has progressively restricted the export of advanced semiconductors, semiconductor manufacturing equipment and EDA software to China, with allied controls from the Netherlands and Japan covering lithography and other tools. Effects: a rapid Chinese push toward domestic tooling and toward RISC-V (which carries no licensor able to be compelled to cut off supply); a hard ceiling on the compute available to Chinese AI labs through legitimate channels; and a substantial grey market. The controls have been tightened repeatedly; **the current state of the rules is fast-moving and is `needs-verification` against the US Bureau of Industry and Security's published rules.**

## 7. Reshoring — CHIPS Act and EU Chips Act

**United States — CHIPS and Science Act (2022).**

| Line | Amount |
|---|---|
| Total authorised | ~US$280bn |
| Appropriated | **US$52.7bn** |
| Manufacturing incentives (subsidies, loans, guarantees, grants) | US$39bn |
| Semiconductor R&D and workforce training | US$13bn |
| **Advanced manufacturing investment tax credit** | **25% of equipment cost**, scored at ~US$24bn |
| Advanced semiconductor R&D | US$11bn |
| DoD microelectronics R&D and workforce | US$2bn |
| Broader public science and technology R&D authorised | ~US$174bn (incl. US$81bn NSF) |

Major awards: **Intel US$8.5bn** (March 2024, later reduced to US$7.86bn in November 2024); **TSMC US$6.6bn** (April 2024, third Arizona fab); **Samsung US$6.4bn** (April 2024, Texas); **Micron US$6.1bn** (April 2024, New York and Idaho); **GlobalFoundries US$1.5bn** (February 2024, New York and Vermont). Pre-Act private announcements included TSMC's US$12bn Arizona commitment (May 2020), Samsung's US$17bn Texas facility (November 2021) and Intel's US$20bn Ohio project (January 2022).

The 25% investment tax credit is arguably more consequential than the grants, because it is automatic, uncapped in the same way, and applies to every qualifying dollar of equipment.

**European Union — European Chips Act.** **€43bn** mobilised, with the stated goal of raising Europe's share of global semiconductor production from **less than 10% (2022) to 20% by 2030**, over an investment horizon running "at least until 2030". Three pillars: (1) research, development and innovation; (2) a new state-aid exemption covering semiconductor manufacturing; (3) supply-chain monitoring and crisis intervention powers.

**The honest assessment.** The 20% target requires Europe's capacity to grow considerably faster than a global market that is itself growing rapidly — a demanding arithmetic. On the US side, subsidies have unquestionably brought leading-edge capacity onshore, but they do not by themselves reproduce the ecosystem — the equipment vendors, materials suppliers, packaging capacity and, most stubbornly, the trained workforce — that makes a Taiwanese or Korean fab cluster productive. Cost differentials, construction timelines and skilled-labour shortages have all been reported as binding. Reshoring is achievable; **cost-competitive** reshoring is the harder claim and remains unproven.

## 8. Where the money goes — the summary

For every US$100 of a finished computing device sold at retail, the approximate structural allocation, in descending defensibility:

1. **The brand that owns the platform** captures the largest share, and captures more of it the more of the stack it controls. Apple's 50.1% gross margin is the demonstration.
2. **The fabless designer of the scarce silicon** captures the next largest — NVIDIA at 72.4% gross margin on the component that nobody can substitute.
3. **The foundry that can actually make it** captures a large share at the leading edge — TSMC at 67.7% gross margin, 60.3% operating.
4. **The IP and EDA vendors** capture a small absolute amount from enormous leverage — Arm's entire company earned US$792m in FY2025.
5. **Memory suppliers** capture wildly variable amounts depending on where the cycle is — near-zero at the trough, extraordinary at the peak, and 2026 is a peak.
6. **OSAT and advanced packaging** capture more than they used to, because they became the bottleneck.
7. **ODM/EMS assemblers** capture very little per unit — Foxconn's ~US$198.5bn of FY2023 revenue and million-plus employees translate into thin margins.
8. **Retail and distribution** capture a few percent.

The general law: **margin accrues to whoever controls a step that cannot be substituted.** Assembly can always be moved; a 2nm process and a mature software ecosystem cannot.

## Sources

- [TSMC 2Q26 results](https://investor.tsmc.com/english/quarterly-results/2026/q2) and [2Q25 results](https://investor.tsmc.com/english/quarterly-results/2025/q2) — TSMC Investor Relations
- [Apple reports third quarter results, FY2026](https://www.apple.com/newsroom/2026/07/apple-reports-third-quarter-results/) — Apple
- [NVIDIA Q2 FY2026 financial results](https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-second-quarter-fiscal-2026) — NVIDIA
- [Arm Holdings](https://en.wikipedia.org/wiki/Arm_Holdings) — Wikipedia
- [Foxconn](https://en.wikipedia.org/wiki/Foxconn) — Wikipedia
- [Foundry model](https://en.wikipedia.org/wiki/Foundry_model) — Wikipedia
- [Semiconductor fabrication plant](https://en.wikipedia.org/wiki/Semiconductor_fabrication_plant) — Wikipedia
- [Dynamic random-access memory](https://en.wikipedia.org/wiki/Dynamic_random-access_memory) — Wikipedia
- [CHIPS and Science Act](https://en.wikipedia.org/wiki/CHIPS_and_Science_Act) — Wikipedia
- [European Chips Act](https://en.wikipedia.org/wiki/European_Chips_Act) — Wikipedia
- [IDC Worldwide Quarterly Personal Computing Device Tracker](https://www.idc.com/promo/pcdforecast) — IDC

## Open questions

- **No per-component BOM figures could be verified.** Counterpoint Research's teardown insight pages returned navigation content only. Any laptop or phone BOM number should be sourced from a primary teardown (TechInsights, Fomalhaut, Counterpoint) before use.
- **Foxconn's net income and operating margin were not obtainable** from the source fetched; the "thin margin" characterisation is qualitative and `needs-verification`.
- **Current foundry market shares** could not be verified. The figures given (TSMC 55.9% in 2017; US$111.54bn total market in 2023) are dated. A current TrendForce or Counterpoint quarterly foundry ranking should replace them.
- **PC vendor market shares** (Lenovo/HP/Dell/Apple/Asus/Acer) were not obtainable from the IDC promo page — only the Q1 2026 total of 65.6m units.
- **Export control specifics** are fast-moving; verify against the US Bureau of Industry and Security's current rules rather than this summary.
- NVIDIA's most recent quarter could not be fetched; the figures given are **Q2 FY2026, ended 27 July 2025** — roughly a year stale as of this file's date.
- The claimed "~40% of worldwide consumer electronics" for Foxconn is a **2012** figure and should not be treated as current.
