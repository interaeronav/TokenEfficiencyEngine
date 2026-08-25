---
id: semi.economics
title: Industry economics and geopolitics — capital, yield, subsidies and control
domain: 27_semiconductors_and_chip_design
tags: [fab-economics, capex, depreciation, utilisation, wafer-pricing, yield, design-cost, memory-cycle, hbm, cowos, export-controls, entity-list, chips-act, eu-chips-act, taiwan-risk, talent]
jurisdiction: global
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "CHIPS and Science Act", url: "https://en.wikipedia.org/wiki/CHIPS_and_Science_Act", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "European Chips Act", url: "https://en.wikipedia.org/wiki/European_Chips_Act", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Semiconductor fabrication plant", url: "https://en.wikipedia.org/wiki/Semiconductor_fabrication_plant", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "TSMC 2Q26 Quarterly Results", url: "https://investor.tsmc.com/english/quarterly-results/2026/q2", publisher: "TSMC Investor Relations", accessed: 2026-08-25}
  - {title: "High Bandwidth Memory", url: "https://en.wikipedia.org/wiki/High_Bandwidth_Memory", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Rapidus", url: "https://en.wikipedia.org/wiki/Rapidus", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Semiconductor industry", url: "https://en.wikipedia.org/wiki/Semiconductor_industry", publisher: "Wikipedia", accessed: 2026-08-25}
related: [semi.firms, semi.euv, semi.overview]
---

# Industry economics and geopolitics — capital, yield, subsidies and control

**Summary.** Semiconductor manufacturing is the most capital-intensive competitive industry on earth: a leading-edge fab costs tens of billions of dollars, depreciates over five years, and must run at very high utilisation to be viable at all. That single fact — plus learning curves that reward whoever is furthest ahead — produced the extreme concentration the industry now has, and that concentration is what made semiconductors an instrument of statecraft after 2018. This file covers fab capital costs, depreciation and utilisation, foundry pricing, yield economics, the design cost curve, ASPs and the memory cycle, the AI accelerator supply constraints (HBM and CoWoS), export controls and entity lists, the CHIPS Act and its international equivalents with committed amounts, Taiwan concentration risk, talent, and an honest outlook.

> ⚠️ **Wafer prices, mask costs and design NRE by node are confidential.** Every public figure is a modelled estimate, most of them tracing to International Business Strategies (IBS). Where such figures appear below they are labelled as estimates and the section carries a `needs-verification` marker. Do not quote them as fact.

## Key facts

| Item | Value | Date / source |
|---|---|---|
| Leading-edge fab cost | "Over one billion USD… tens of billions not uncommon"; TSMC "over US$45 bn" for a 2 nm fab | 2025 |
| EUV scanner price | ~US$200 m (NXE); ~US$370 m (High-NA EXE) | 2024–2026 |
| Single equipment items | Several million USD upward; a fab holds several hundred | |
| TSMC gross / operating margin | 67.7% / 60.3% | 2Q 2026 |
| TSMC quarterly revenue | US$40.20 bn | 2Q 2026 |
| Global semiconductor sales | US$555.9 bn, +26.2%, on 1.15 trillion units | 2021 (SIA) |
| CHIPS and Science Act | US$280 bn authorised; **US$52.7 bn appropriated**; US$39 bn manufacturing incentives, US$11 bn R&D, 25% investment tax credit (~US$24 bn) | Aug 2022 |
| CHIPS investment tax credit increase | +10 percentage points added under the Trump administration | 2025 |
| US equity stake in Intel | **9.9%**, from US$11.1 bn of grants | Aug 2025 |
| EU Chips Act | **€43 bn**; target to raise EU share from <10% to **20% by 2030**; Regulation 2023/1781 published 18 September 2023 | 2023 |
| Japan / Rapidus | ¥802.5 bn (US$5.4 bn) in FY2025; US$65 bn programme announced November 2024 running to 2030 | 2024–2025 |
| SIA-reported US investment | US$630+ bn across 140 projects since 2020; ~500,000 jobs across 28 states; projected US advanced-logic share 28% by 2033 (vs 8% baseline) | 2025 |
| DRAM price inflation | Some categories up **more than 200%** between early 2025 and early 2026 | 2026 |

## 1. Fab capital costs

A modern 300 mm leading-edge logic fab is a US$20–45 bn project. The breakdown, in round proportions:

- **Equipment: 70–80% of total cost.** Several hundred tools. Lithography alone can be 20–25% of equipment spend — a fab with a dozen EUV scanners at US$200 m each has US$2.4 bn in one tool category before High-NA. Etch, deposition and metrology together are comparable.
- **Building and cleanroom: 15–25%.** The shell is not ordinary construction: vibration-isolated slabs, massive HVAC and filtration, ultrapure water plants, gas and chemical distribution, abatement, and redundant power.
- **Land, utilities and start-up: the remainder.**

Two consequences follow immediately. First, **the marginal cost of a wafer is small relative to the fixed cost** — the economics are those of an airline or a hotel, not of a machine shop. Second, **the fab must be full**. A fab at 60% utilisation is usually losing money even with a healthy gross margin per wafer sold.

**Depreciation.** Foundries typically depreciate fab equipment over **five years** (TSMC's convention), which front-loads cost onto a node's early years. This has two effects: (a) gross margin on a node improves markedly in years 4–6 as equipment comes off the books, which is why mature nodes are so profitable; and (b) a node that fails to fill its capacity in years 1–3 is a financial catastrophe.

**Utilisation and the cycle.** Because capacity is added in large indivisible lumps with a 3–4 year lead time, and demand moves faster than that, the industry over- and under-builds in a cycle. The classic pattern: shortage → price rises → everyone announces capacity → capacity arrives 3 years later into a demand trough → prices collapse → capex is cut → shortage. The 2021–2023 automotive shortage and the 2023–2024 memory glut, followed by the 2025–2026 memory shortage, are the most recent full turn.

## 2. Foundry pricing

Foundries price per wafer, not per die — the customer bears yield risk (with some negotiated exceptions such as yield-shared or good-die pricing on new nodes).

> ⚠️ Section status: `needs-verification`. The figures below are the widely-circulated industry estimates and should be treated as order-of-magnitude only.

| Node | Estimated price per 300 mm wafer (US$) |
|---|---|
| 28 nm | ~3,000 |
| 16/12 nm | ~4,000 |
| 7 nm | ~9,000–10,000 |
| 5 nm | ~16,000–17,000 |
| 3 nm | ~18,000–20,000 |
| 2 nm | reported at ~US$30,000 |

What makes the number: EUV exposures per wafer (each EUV layer consumes expensive tool-hours), total mask layer count, cycle time, yield, tool depreciation, and — decisively — whether an alternative supplier exists. At 2 nm there is effectively one supplier with a 67.7% gross margin, so price is set by what the customer's product can bear, not by cost.

**Cost per good die** is what actually matters:

`cost per good die = wafer price / (gross dies per wafer × yield)`

A 300 mm wafer has 70,686 mm² of area, giving roughly 82 gross dies at the 858 mm² reticle limit and about 700 at 100 mm². Apply Murphy's yield model `Y = ((1 − e^(−D0·A))/(D0·A))²`:

| Die area | Gross dies | Yield at D0 = 0.10/cm² | Good dies | Cost/die at US$20,000/wafer |
|---|---|---|---|---|
| 50 mm² | ~1,300 | ~95% | ~1,235 | ~US$16 |
| 100 mm² | ~680 | ~90% | ~612 | ~US$33 |
| 300 mm² | ~215 | ~74% | ~159 | ~US$126 |
| 600 mm² | ~101 | ~55% | ~56 | ~US$357 |
| 858 mm² | ~68 | ~44% | ~30 | ~US$667 |

(Gross die counts are approximate — they depend on die aspect ratio and edge exclusion.)

The quadratic punishment of large dies is the whole economic argument for chiplets (`04`): four 200 mm² dies yield far more good silicon than one 800 mm² die, even after paying for packaging. It is also the argument for **binning** — a die with one defective core sold as a lower SKU converts a scrap into revenue, which is why every CPU and GPU family has a product ladder that mirrors its defect distribution.

## 3. The design cost curve

> ⚠️ `needs-verification` — these are IBS-lineage estimates repeated across the trade press.

| Node | Estimated total design cost for a complex SoC |
|---|---|
| 28 nm | ~US$40–50 m |
| 16 nm | ~US$80–100 m |
| 7 nm | ~US$200–300 m |
| 5 nm | ~US$400–550 m |
| 3 nm | ~US$500 m–1 bn |
| 2 nm | reported at ~US$0.7–1.5 bn |

Composition: verification and validation (the largest single line), physical design and signoff, software and firmware, IP licences, EDA licences and compute, mask sets, and prototype/bring-up. Note that **software is often the largest component** for a platform SoC — the chip is useless without drivers, compilers and a stack.

The strategic consequence: the number of companies that can afford a leading-edge tapeout is small and shrinking, so leading-edge design consolidates onto a handful of very-high-volume or very-high-ASP products (phone SoCs, AI accelerators, hyperscaler ASICs, and CPUs). Everything else stays at 28/22/16 nm, where the economics still work — which is why those nodes are not "legacy" but the industry's profitable middle.

## 4. ASP trends and the memory cycle

**Logic ASPs have risen sharply.** A flagship phone SoC, a datacentre CPU and above all an AI accelerator now carry ASPs multiples of their equivalents ten years ago. This is the industry's escape valve from the cost-per-transistor stall: if transistors stop getting cheaper, sell fewer of them at much higher prices into applications where they are worth it.

**Memory is different.** DRAM and NAND are close to commodities with high fixed costs, so the cycle is violent:

- Supply is added in lumps; demand is elastic; prices are set at the margin.
- In a downturn, prices can fall below cash cost, and makers run negative gross margins rather than idle depreciating fabs.
- In an upturn, incremental revenue is nearly all margin. SK Hynix's 2024 operating income of ₩23.47 tn on ₩66.19 tn of revenue (35.5% operating margin), and its reported ~US$25 bn of operating profit in Q1 2026, are what the top of a cycle looks like.

**The 2025–2026 memory shock.** HBM production consumes far more wafer area per bit than conventional DRAM (a 12- or 16-high stack plus a logic base die, at lower yields), so every HBM bit displaces multiple commodity DRAM bits. With AI demand absorbing HBM capacity, commodity DRAM went short: **some categories rose by more than 200% between early 2025 and early 2026**. Micron reached a **US$1 trillion market capitalisation on 26 May 2026** on the back of it. This is the clearest recent example of an AI-driven distortion propagating into an unrelated market.

## 5. The AI accelerator boom and its real constraints

Since 2023 the binding constraints on accelerator supply have moved *downstream* of the wafer fab:

1. **CoWoS / advanced packaging capacity.** Every HBM-equipped accelerator needs a 2.5D package. TSMC's CoWoS capacity has been the industry's tightest bottleneck, repeatedly doubled and repeatedly sold out. Because the interposer is itself a silicon product made in a fab, capacity cannot be added faster than fab capacity.
2. **HBM supply.** Three suppliers (SK Hynix, Samsung, Micron), long qualification cycles per customer, and yields that fall with stack height. HBM4's move to a 2048-bit interface and a logic-process base die (fabricated by TSMC for some suppliers) adds a further dependency.
3. **Power and datacentre shell.** By 2025–2026 the practical limit on deployment in several regions was grid interconnection and transformer supply, not silicon.
4. **Optics and networking.** 800G/1.6T optical modules and switch silicon have had their own allocation queues.

The strategic effect is that **whoever controls packaging and memory allocation controls accelerator shipments**, which is a large part of why TSMC's and SK Hynix's bargaining positions strengthened so much.

## 6. Export controls and entity lists

The timeline that matters:

- **2018–2019** — Huawei added to the US Entity List (May 2019); the Netherlands ceases issuing EUV export licences for China.
- **May 2020** — the Foreign Direct Product Rule extended to Huawei: any chip made anywhere using US technology requires a licence. HiSilicon stopped producing Kirin chips from **15 September 2020**.
- **September / December 2020** — SMIC designated a military end-user, then **added to the Entity List in December 2020**.
- **7 October 2022** — the pivotal rules: performance thresholds banning advanced AI chips to China, restrictions on advanced logic (≤16/14 nm FinFET), DRAM (≤18 nm half-pitch) and NAND (≥128 layers) equipment, and — novel and consequential — restrictions on **US persons** supporting Chinese advanced fabs.
- **December 2022** — **YMTC added to the Entity List**.
- **October 2023 and successive updates** — thresholds tightened; NVIDIA's China-specific parts repeatedly redesigned and repeatedly restricted.
- **May 2025** — EDA vendors **Cadence, Synopsys and Siemens** restricted from supplying China. This targets the thinnest, highest-leverage layer of the stack.
- **June 2025** — Taiwan adds SMIC and Huawei to its own export-control list.
- **June 2026** — CXMT added to the US Department of Defense's list of Chinese military-linked companies.

**Assessment.** The controls have unambiguously slowed China's access to leading-edge logic: without EUV there is no economically viable path below roughly 5 nm-class density (`06`). They have equally unambiguously accelerated Chinese domestic substitution at mature nodes, in equipment (Naura, AMEC), in EDA (Empyrean, Primarius) and in RISC-V adoption. The honest summary is that export controls buy time at the leading edge and lose ground at the trailing edge, and that the trailing edge is where most of the world's chips by unit volume are made.

## 7. Industrial policy, with committed amounts

| Programme | Amount | Dates and notes |
|---|---|---|
| **US CHIPS and Science Act** | **US$280 bn authorised; US$52.7 bn appropriated** — US$39 bn manufacturing incentives, US$11 bn advanced R&D, US$2 bn defence microelectronics, US$1.5 bn Open RAN, US$500 m State Department; plus a **25% investment tax credit** worth ~US$24 bn | Signed August 2022. Major awards: **Intel US$8.5 bn (March 2024, later reduced to US$7.86 bn)**, **TSMC US$6.6 bn (April 2024)**, **Samsung US$6.4 bn (April 2024)**, **Micron US$6.1 bn (April 2024)**, **GlobalFoundries US$1.5 bn (February 2024)**, Microchip US$162 m, BAE US$35 m. By May 2024, US$32.8 bn of the US$39 bn was allocated. In **August 2025 the US took a 9.9% stake in Intel** using US$11.1 bn of grants. The Trump administration preserved the Act, **added 10 percentage points to the manufacturing tax credit**, closed the Natcast research entity and denied US$7.4 bn of its funding |
| **EU Chips Act** | **€43 bn**; target to raise the EU's share of global production from **<10% to 20% by 2030** | Announced February 2022; Regulation 2023/1781 published **18 September 2023**. Notable approvals: **€5 bn of German state aid for TSMC's Dresden fab (August 2024)**; Infineon's two Dresden plants (€5 bn investment, ~€1 bn subsidy requested, March 2023); **€293 m** for STMicroelectronics' Catania SiC substrate plant |
| **Japan** | **¥802.5 bn (US$5.4 bn) to Rapidus in FY2025** alone, on top of ¥70 bn (2022), ¥260 bn (2023) and up to ¥590 bn (2024); a **US$65 bn programme to 2030 announced November 2024**. Separately, large subsidies to TSMC's Kumamoto JASM fab and to Kioxia | Japan's strategy is to rebuild leading-edge logic (Rapidus) while defending its dominant positions in equipment and materials |
| **South Korea** | A national semiconductor cluster programme centred on Yongin, with a support package announced in 2024 (figures `needs-verification`); tax credits under the "K-Chips Act" | |
| **China** | The National IC Industry Investment Fund ("Big Fund") — Phase I (2014, ~¥138.7 bn), Phase II (2019, ~¥204 bn), **Phase III (May 2024, ~¥344 bn / ~US$47.5 bn)** — plus provincial funds and procurement preference | Amounts widely reported; treat as `needs-verification` |
| **India** | The India Semiconductor Mission, with a US$10 bn incentive programme approved in December 2021 and subsequently expanded; the flagship approvals are a Tata–PSMC fab in Dholera, Gujarat and several ATMP/OSAT plants | Figures `needs-verification` |

**The honest verdict on subsidies.** They can buy capacity; they cannot buy a learning curve. A fab built with a grant still needs a yield ramp, a trained workforce, a customer base and a supply chain within reach. TSMC's Arizona delays and cost overruns, and Intel's Ohio schedule slips, are the evidence. The 28% US advanced-logic share by 2033 projected by the SIA (against an 8% baseline) is a target that depends on demand as much as on construction.

## 8. Taiwan concentration risk

Roughly 70% of foundry revenue and the overwhelming majority of leading-edge logic is manufactured on one island, within a few hundred kilometres of a contested strait. The exposure is not only military:

- **Physical**: earthquakes (Taiwan sits on an active margin; the April 2024 Hualien earthquake caused measurable wafer losses), typhoons, and drought — TSMC's fabs are enormous water consumers and Taiwan has had serious droughts.
- **Grid**: Taiwan's electricity margin is thin and its nuclear policy contested; a leading-edge fab draws hundreds of megawatts.
- **Geopolitical**: a blockade would not need to damage a single fab to halt output, because the inputs (Japanese chemicals, Dutch tools, Korean substrates) and the outputs both move by air and sea.

Mitigation is under way and is slow and expensive: TSMC Arizona, Kumamoto and Dresden; Samsung Taylor; Intel Arizona/Ohio; Rapidus Hokkaido. None of it changes the picture before the 2030s, and the most advanced node will remain in Taiwan by design — TSMC has been explicit that N−1 goes overseas while the leading edge stays home.

**The "silicon shield" argument** — that Taiwan's centrality deters conflict — is real but double-edged: it also makes Taiwan more valuable to control and creates an incentive for every other party to reduce dependence, which erodes the shield over time.

## 9. Talent

The binding constraint on every expansion plan announced since 2022 has been people, not money.

- The SIA projects a shortfall of tens of thousands of US semiconductor workers by 2030; TSMC has publicly attributed Arizona delays partly to the shortage of workers with fab construction and equipment-installation experience.
- The pipeline problem is structural: the number of students choosing semiconductor-adjacent specialisations fell for two decades while software absorbed the talent, and process engineering in particular has very few training paths outside the companies themselves.
- Specific scarcities: analog and mixed-signal designers (a discipline that takes 5–10 years to develop and cannot be automated), DFT engineers, physical-design engineers with advanced-node experience, process integration engineers, and equipment technicians.
- Wage inflation is real, and the geographic mismatch is severe — the expertise sits in Hsinchu, Seoul, Hillsboro, Dresden and Kumamoto, not where new fabs are being sited.

`09` covers the entry paths.

## 10. Honest outlook

**Structurally secure through the late 2020s:**
- ASML's EUV monopoly. There is no second source and no credible programme to build one; the physics, optics and supply chain are a 20-year moat.
- TSMC's leading-edge position, unless Intel Foundry secures major external customers or Samsung solves its yield problem.
- The three-vendor EDA structure.
- Memory's oligopoly, subject to CXMT's slow encroachment at mature densities.

**Genuinely uncertain:**
- **Whether AI capex holds.** A very large share of 2024–2026 industry growth is one demand vector. If accelerator demand normalises, the industry has built capacity against it, and the correction would be severe. This is the single largest risk to every forecast in this file.
- **Intel Foundry's viability.** 18A is real silicon; 14A is conditioned on external customers. The US government's 9.9% stake makes failure politically expensive but not impossible.
- **High-NA's economics.** Intel is committed; TSMC is deferring. Whoever is right saves or wastes billions.
- **CFET and the post-2030 device roadmap.** No production commitment exists from anyone.
- **China's trailing-edge capacity build.** Very large mature-node capacity additions could depress prices across analog, power and MCU markets — a slower but more certain competitive threat to Infineon, ST, NXP and TI than anything at 2 nm.

**What will not change:** the physics (`01`), the capital intensity, and the fact that any new entrant must buy the same tools from the same handful of suppliers and then spend years climbing a yield curve that the incumbent climbed a decade ago.

## Open questions

- Wafer prices, mask costs and design NRE by node are estimates (`needs-verification`) — no primary source exists.
- Global semiconductor sales for 2024 and 2025 could not be verified in this pass; the last verified SIA figure is 2021 (US$555.9 bn).
- South Korean, Indian and Chinese "Big Fund" Phase III amounts are widely reported but unverified here.
- The SIA talent-shortfall figure is cited from memory of SIA/Oxford Economics work and was not verified in this pass.

## Sources

- [CHIPS and Science Act — Wikipedia](https://en.wikipedia.org/wiki/CHIPS_and_Science_Act) — accessed 2026-08-25
- [European Chips Act — Wikipedia](https://en.wikipedia.org/wiki/European_Chips_Act) — accessed 2026-08-25
- [Semiconductor fabrication plant — Wikipedia](https://en.wikipedia.org/wiki/Semiconductor_fabrication_plant) — accessed 2026-08-25
- [Semiconductor industry — Wikipedia](https://en.wikipedia.org/wiki/Semiconductor_industry) — accessed 2026-08-25
- [TSMC 2Q26 Quarterly Results](https://investor.tsmc.com/english/quarterly-results/2026/q2) — accessed 2026-08-25
- [High Bandwidth Memory — Wikipedia](https://en.wikipedia.org/wiki/High_Bandwidth_Memory) — accessed 2026-08-25
- [Rapidus — Wikipedia](https://en.wikipedia.org/wiki/Rapidus) — accessed 2026-08-25
- [SMIC — Wikipedia](https://en.wikipedia.org/wiki/Semiconductor_Manufacturing_International_Corporation) — accessed 2026-08-25
- [Micron Technology — Wikipedia](https://en.wikipedia.org/wiki/Micron_Technology) — accessed 2026-08-25
- [SK Hynix — Wikipedia](https://en.wikipedia.org/wiki/SK_Hynix) — accessed 2026-08-25
- [ChangXin Memory Technologies — Wikipedia](https://en.wikipedia.org/wiki/ChangXin_Memory_Technologies) — accessed 2026-08-25

