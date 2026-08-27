---
id: semi.euv
title: EUV lithography and the 2 nm frontier
domain: 27_semiconductors_and_chip_design
tags: [euv, lithography, asml, high-na, nxe, exe, tin-plasma, multilayer-mirror, pellicle, stochastic-defects, n2, a16, 18a, sf2, rapidus, smic, transistor-density, yield]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Extreme ultraviolet lithography", url: "https://en.wikipedia.org/wiki/Extreme_ultraviolet_lithography", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "EUV lithography systems", url: "https://www.asml.com/en/products/euv-lithography-systems", publisher: "ASML", accessed: 2026-08-25}
  - {title: "ASML Holding", url: "https://en.wikipedia.org/wiki/ASML_Holding", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "TSMC 2nm Technology", url: "https://www.tsmc.com/english/dedicatedFoundry/technology/logic/l_2nm", publisher: "TSMC", accessed: 2026-08-25}
  - {title: "TSMC A16 Technology", url: "https://www.tsmc.com/english/dedicatedFoundry/technology/logic/l_A16", publisher: "TSMC", accessed: 2026-08-25}
  - {title: "Intel 18A process technology", url: "https://www.intel.com/content/www/us/en/foundry/process/18a.html", publisher: "Intel Corporation", accessed: 2026-08-25}
  - {title: "2 nm process", url: "https://en.wikipedia.org/wiki/2_nm_process", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "3 nm process", url: "https://en.wikipedia.org/wiki/3_nm_process", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Rapidus", url: "https://en.wikipedia.org/wiki/Rapidus", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Semiconductor Manufacturing International Corporation", url: "https://en.wikipedia.org/wiki/Semiconductor_Manufacturing_International_Corporation", publisher: "Wikipedia", accessed: 2026-08-25}
related: [semi.fabrication, semi.physics, semi.firms, semi.economics]
---

# EUV lithography and the 2 nm frontier

**Summary.** Extreme ultraviolet lithography at 13.5 nm is the most difficult manufacturing technology ever put into volume production, and one company on earth builds the machines. This file explains why 13.5 nm was necessary, how the tin-plasma light source and all-reflective optics work, what ASML's NXE (0.33 NA) and EXE (0.55 NA High-NA) tools actually do and cost, the unsolved problems (stochastic defects, pellicles, source power), and then the nodes themselves: what "3 nm" and "2 nm" mean physically, and the dated state of TSMC N2/A16, Samsung SF2, Intel 18A, Rapidus and SMIC as of August 2026. Every claim is dated; where a number is a manufacturer's own marketing claim it is labelled as such.

## Key facts

| Item | Value | Date / source |
|---|---|---|
| EUV wavelength | 13.5 nm | Sn ionic states Sn IX–Sn XIV |
| Mo/Si multilayer mirror | 40–50 alternating layers, ~70–75% peak reflectivity, ~2% FWHM bandwidth, Ru capping layer | |
| Optical path | ≥2 condenser mirrors + 6 projection mirrors + reflective mask = 11 reflections → **~2% of source light reaches the wafer** | |
| Wall-plug efficiency | ~0.02%; ~1 MW input for 200 W at intermediate focus (100 wph) vs ~165 kW for an ArF immersion tool | |
| Source power targets | >250 W optical in production; High-NA expected to need ≥500 W; >40 kW electrical input | |
| Collector degradation | ~0.1–0.3% reflectivity loss per billion 50 kHz pulses (~10% in ~2 weeks) | |
| NXE resolution / NA | 13 nm at NA 0.33 (NXE:3400C, 3600D, 3800E) | ASML product page |
| EXE resolution / NA | 8 nm at NA 0.55 (EXE:5000, EXE:5200B) | ASML product page |
| High-NA optics | 4×/8× **anamorphic**; field 26 × 16.5 mm (half of the 26 × 33 mm standard field) | |
| Scanner prices | NXE class up to ~US$200 m; High-NA EXE ~US$370 m | ASML/Wikipedia |
| First High-NA shipments | Intel December 2023; TSMC late 2024 | |
| ASML lithography market share | 83% of worldwide lithography sales (2025); effectively 100% of EUV | |
| Typical EUV resist dose | ~40 mJ/cm² to sustain throughput | |
| Stochastic defect floor | >0.25/cm² missing+bridging contacts at 32 nm pitch (ASML study, 2024) = 177 defects per wafer | 2024 |
| TSMC N2 | Volume production started **4Q 2025** | TSMC |
| TSMC A16 | Production-ready **2H 2026**; +8–10% speed at same Vdd, −15–20% power at same speed, up to 1.10× density vs N2P | TSMC |
| Intel 18A | In high-volume manufacturing in the US; +18% perf iso-power, −38% power iso-perf, +30% density vs Intel 3.1 | Intel, 2026 |
| Samsung SF2 | Mass production from 2025; yields reported in the 50–60% range into early 2026 | |
| Rapidus 2 nm | Pilot line from 1 April 2025; prototype wafer 18 July 2025 at **237.31 MTr/mm²**; mass production target 2H 2027 | |
| SMIC | 7 nm from 21 July 2022; "N+3" scaled evolution as of December 2025; no EUV access | |

## 1. Why 13.5 nm

`CD = k1·λ/NA`. With 193 nm light, `k1` floored at ~0.25–0.28 for a single exposure and NA capped at 1.35 by water's refractive index, the single-exposure half-pitch limit is about **38 nm**. Below that, the industry used multi-patterning (`05`): LELE, LELELE, SADP, SAQP. At 10 nm and 7 nm the cost became brutal — some layers needed four separate exposure/etch cycles, each with its own mask, overlay budget and cycle time, and the design rules that multi-patterning imposes (unidirectional metal, colouring constraints, cut masks) constrained density in their own right.

Cutting `λ` from 193 nm to 13.5 nm is a 14× improvement in the numerator. That single move restores single-exposure patterning at pitches down to about 30 nm (13 nm resolution at NA 0.33 for lines/spaces), collapsing four-mask sequences to one.

The cost of that choice is that **nothing is transparent at 13.5 nm**. Every material absorbs. So:

- No refractive lenses — all-reflective optics only.
- No transmissive masks — the mask is a **mirror**.
- No air — the entire beam path is in vacuum.
- Only a narrow band of angles and wavelengths reflects at all, via Bragg interference in a multilayer stack.

This is why EUV took roughly twenty-five years and tens of billions of dollars of R&D between first serious proposals and volume production (first HVM deployment in 2019, at TSMC N7+ and Samsung 7LPP).

## 2. The light source

The most improbable part of the machine. Per pulse, at 50 kHz:

1. A generator ejects a **molten tin droplet** of ~25–30 µm diameter into the vessel.
2. A **CO₂ laser** pre-pulse strikes the droplet and flattens it into a pancake, maximising the surface presented to the main pulse.
3. The **main CO₂ pulse** (tens of kilowatts of average power, delivered by a multi-stage amplifier chain) vaporises the tin into a plasma at ~40–50 eV.
4. Tin ions in charge states **Sn IX through Sn XIV** emit broadband, with a strong unresolved transition array around **13.5 nm**.
5. A grazing-incidence/normal-incidence **collector mirror** — an ellipsoidal multilayer — gathers the emission and focuses it at the **intermediate focus**, the interface to the scanner.

Numbers that convey the difficulty:

- **Conversion efficiency** from laser energy to in-band EUV is a few per cent at best; **wall-plug efficiency is ~0.02%**. Delivering 200 W at intermediate focus for a 100 wph tool takes roughly **1 MW** of electrical input — an ArF immersion tool needs ~165 kW.
- The droplet must be hit **50,000 times per second**, each time within micrometres, with the laser fired at the right instant. The tracking system is a real-time control problem.
- **Tin debris** coats everything. The vessel runs a hydrogen ambient that reacts with tin to form volatile stannane, continuously cleaning surfaces. Even so, the collector loses ~0.1–0.3% reflectivity per billion pulses — about 10% in two weeks — and must be replaced periodically. Collector life and swap time are a major contributor to tool availability.
- Production tools now target **>250 W** optical at intermediate focus; High-NA is expected to need **≥500 W** because of the smaller field and higher dose demands. ASML has publicly targeted higher source powers with each generation, and source power is the primary determinant of throughput.

## 3. The optics

- **Multilayer mirrors**: 40–50 alternating **molybdenum and silicon** layers, each a few nanometres thick, forming a Bragg reflector for 13.5 nm at near-normal incidence. Peak reflectivity ~70–75%, with a bandwidth of about 2% FWHM. Each mirror therefore absorbs ~30% of what hits it — and that absorbed energy becomes heat that must not distort the mirror.
- **Figure accuracy**: the projection optics (six mirrors, made by Zeiss SMT) are figured to sub-nanometre and roughness in the tens of picometres. The canonical comparison — a mirror the size of Germany would have bumps under a millimetre — is Zeiss's own.
- **Transmission budget**: 11 reflections (two-plus condenser, six projection, plus the reflective mask) at ~0.7 each gives roughly **2% of source light at the wafer**. Everything about EUV economics follows from that number.
- **The mask is reflective**: a Mo/Si multilayer blank (Hoya is effectively the sole qualified supplier) with a patterned tantalum-based absorber. Because the mask is illuminated at a ~6° chief-ray angle, the absorber's thickness causes **mask 3D effects** — shadowing, best-focus shift versus pitch and orientation — which have to be corrected in OPC.

## 4. The tools

| Model | NA | Resolution | Target nodes |
|---|---|---|---|
| NXE:3400B/C | 0.33 | 13 nm | 7 and 5 nm |
| NXE:3600D | 0.33 | 13 nm | 5 and 3 nm |
| NXE:3800E | 0.33 | 13 nm | 2 nm logic and leading-edge DRAM |
| EXE:5000 | 0.55 | 8 nm | High-NA introduction; HVM support 2025–2026 |
| EXE:5200B | 0.55 | 8 nm | sub-2 nm logic and leading-edge DRAM |

**Scale and price.** An NXE-class tool weighs ~180 tonnes, ships in multiple Boeing 747 loads, takes months to install and qualify, and costs up to about **US$200 m**. A High-NA **EXE** system costs roughly **US$370 m**. Intel took the first High-NA shipment in **December 2023**; TSMC took one in **late 2024**.

**Throughput and uptime.** Historical trajectory: ASML's 2006 prototype produced one wafer in 23 hours. The NXE:3400C is specified around **136 wafers per hour**; by 2022 EUV scanners reached **up to ~200 wph**, versus ~296 wph for a DUV immersion tool. In practice tools in production ran on the order of **1,000 wafers per day** as of 2019–2022, with substantial idle time when a fab has many EUV layers to schedule.

> ⚠️ Published throughput figures for the NXE:3800E and EXE:5200B could not be verified from a primary source in this pass. Commonly-reported figures (NXE:3800E around 220 wph; EXE:5200 in the 175–200 wph range) should be treated as `needs-verification`.

**Availability** matters as much as nameplate throughput. At ~US$200 m per tool with EUV layers on the critical path of every wafer in the fab, a percentage point of uptime is worth a great deal. Early NXE tools ran well below 80% availability; mature fleets are reported in the low-to-mid 90s. Source-driven downtime (collector swaps, droplet generator maintenance) dominates.

**High-NA's specific complication: the half field.** Raising NA from 0.33 to 0.55 requires larger, steeper mirrors; keeping the mask illumination angles manageable forced an **anamorphic** design — 4× demagnification in one direction, 8× in the other. The consequence is that the printable field is **26 × 16.5 mm** instead of 26 × 33 mm. Any die larger than the half field must be **stitched** from two exposures, with all the overlay and design-rule pain that implies. For a large GPU die this is a serious constraint, and it is one reason High-NA adoption is being led by Intel (for logic tiles) rather than by the makers of reticle-limit accelerators.

Intel has been the most aggressive High-NA adopter; TSMC has publicly signalled that it will introduce High-NA only when the cost per wafer justifies it, preferring 0.33-NA EUV with multi-patterning for as long as that is cheaper. That disagreement is the most interesting open strategic question in lithography as of 2026.

## 5. Resists, stochastics and pellicles — the unsolved problems

### The photon-count problem

At 13.5 nm each photon carries 92 eV, versus 6.4 eV at 193 nm — 14× more energy per photon. For the same delivered dose in mJ/cm², EUV therefore delivers **14× fewer photons**. Photon arrival is Poisson: fewer photons means larger relative fluctuation. At the doses that keep throughput viable (~40 mJ/cm²), the natural dose variation is "at least several percent, 3σ" across a feature.

This produces **stochastic defects**: individual contact holes that fail to open, individual lines that bridge or break — not a systematic CD error, but a random, low-probability, catastrophic failure. The numbers as reported:

- Stochastic defect densities have exceeded **1/cm² at 36 nm pitch**.
- An ASML exposure study (2024) found a **missing + bridging defect density floor of >0.25/cm² at 32 nm pitch contact holes** — **177 defects per wafer**.
- As of 2025, stochastic defect probabilities were "on the order of ppm, and could also vary over an order of magnitude, leading to erratic yields."

This is the single most important technical fact about the leading edge in 2026: **defectivity at EUV is partly irreducible and statistical**, and the industry's answer is the unpleasant one — raise the dose (costing throughput and therefore money), improve resist chemistry, and design layouts to be more stochastics-tolerant.

The **RLS trade-off** (resolution / line-edge roughness / sensitivity) is the governing constraint: you can have two of the three. Improving any one degrades another, and the coupling is roughly `LWR² · dose · resolution³ ≈ constant`.

### Resists

- **Chemically amplified resists (CAR)** — a photoacid generator releases acid, which catalytically deprotects the polymer during the post-exposure bake. The acid diffusion length smooths high-frequency roughness, which helps, but it also blurs the image and its own statistics (how many PAG molecules were in that volume?) add noise. Higher doses increase LER through PAG decomposition.
- **Metal-oxide resists** (Inpria, acquired by JSR, and others) — tin-oxo clusters. Much higher EUV absorption per unit thickness, so thinner films and better sensitivity, and higher etch resistance. But there is no acid blur, so high-frequency roughness is not smoothed; and they outgas water, oxygen and potentially metals into a vacuum system that must not be contaminated.
- **Dry resist** (Lam Research with ASML and imec) — deposited and developed by vapour processes rather than spin-coating. Claims better uniformity, thinner films and lower defectivity. Under adoption evaluation.
- The ITRS line-width roughness guideline is **8% (3σ) of linewidth** — at 16 nm lines, that is 1.3 nm.

### Pellicles

A pellicle is a thin membrane held above the mask so that particles landing on it are out of the focal plane. On DUV masks this is routine. On EUV it is brutally hard:

- The membrane must transmit EUV **twice** (in and out), so every percent of absorption costs 2% of dose.
- ASML developed a **70 nm-thick polysilicon** membrane transmitting **82%** of EUV — but "less than half of the membranes survived expected EUV power levels." SiNx alternatives "failed at 82 W equivalent EUV source power levels."
- At a 250 W source, the pellicle surface temperature is expected to reach **686 °C** — above the melting point of aluminium — because there is no convection in vacuum, only radiation.
- Hydrogen cleaning plasma damages carbon-based alternatives (CNT membranes are the leading research candidate).
- Reporting indicates periods with **no users of EUV pellicles** because of accelerated damage at higher powers.

Running without a pellicle means every mask must be inspected extremely frequently for particles, and a single particle can print on every die on every wafer until it is caught. This is a live yield risk at the leading edge.

## 6. What "3 nm" and "2 nm" actually mean

Nothing on the chip is 3 nm or 2 nm. The names are marketing successors to a dimensional-scaling convention abandoned around the 22/20 nm generation. The real numbers:

| Metric | TSMC N3 | TSMC N3E | 2 nm class (generic) |
|---|---|---|---|
| Contacted poly pitch (gate pitch) | 45 nm | — | ~45 nm |
| Minimum metal pitch | — | 23 nm | ~20 nm |
| SRAM bit cell | 0.0199 µm² | 0.021 µm² | marginal further scaling |
| Device | FinFET | FinFET | Nanosheet GAA |

Note two things. First, **gate pitch has essentially stopped scaling** between 3 nm and 2 nm — the density gain comes from cell-height reduction (fewer routing tracks), fin/sheet depopulation, and design-technology co-optimisation, not from shrinking the transistor pitch. Second, **N3E's SRAM cell is larger than N3's** — SRAM scaling has effectively stalled, which is why cache dominates die area and why stacked SRAM (AMD's 3D V-Cache) and chiplet partitioning are so attractive (`04`).

**Transistor density in MTr/mm²** is the number most quoted and the least comparable, because it depends entirely on the assumed mix of high-density and high-performance cells. The most useful *verified* recent data point: Rapidus reported **237.31 MTr/mm²** on a 2 nm prototype 300 mm wafer on **18 July 2025**.

## 7. The roadmaps, node by node, dated

### TSMC

| Node | Device | Status / claim | Date |
|---|---|---|---|
| N5 | FinFET, first heavy-EUV node | Volume production 2020 | 2020 |
| N4 / N4P / N4X | FinFET, N5 family | Ramped 2022 onward; NVIDIA Blackwell uses custom 4NP | 2022– |
| N3 | FinFET | Volume production Q4 2022; SRAM 0.0199 µm², CPP 45 nm | Q4 2022 |
| N3E | FinFET | H2 2023; +10–15% performance at iso-power or −30–35% power vs N5; MMP 23 nm | H2 2023 |
| N3P | FinFET | H2 2024; +5% speed or −5–10% power and 1.04× density vs N3E | H2 2024 |
| N3X | FinFET | 2025; +5% speed over N3P, ~3.5× higher leakage, same density — a high-performance-compute variant | 2025 |
| **N2** | **Nanosheet GAA** | **Volume production started 4Q 2025** (TSMC's own statement). Reported +10–15% performance at iso-power or −20–30% power at iso-performance, >20% higher density vs N3E. Adds low-resistance RDL and high-performance MiM capacitors | 4Q 2025 |
| N2P | Nanosheet GAA | Performance-enhanced N2 | 2026 |
| **A16** | Nanosheet GAA + **Super Power Rail** backside power | **Production-ready 2H 2026** (TSMC). +8–10% speed at same Vdd, −15–20% power at same speed, up to 1.10× density vs N2P. TSMC emphasises a "novel backside contact scheme" that preserves gate density and device-width flexibility | 2H 2026 |
| A14 | Next generation | Announced on TSMC's roadmap; targeted around 2028 | — (`needs-verification`) |

TSMC's own N2 marketing avoids publishing head-to-head percentage figures on its public technology page; the +10–15%/−20–30% numbers come from secondary reporting of TSMC statements.

### Samsung Foundry

- **SF3E** — the industry's *first* GAA (MBCFET) node in production, shipping from mid-2022. Claimed +23% performance or −45% power versus its 5 nm reference.
- **SF3** — second generation, up to 35% higher transistor density and up to 50% power reduction targets; trial production January 2024.
- **SF2** — 2 nm-class, mass production from 2025, used for the **Exynos 2600**. **Reported yields in the 50–60% range into early 2026** — respectable for a ramping GAA node but well behind what a high-volume external customer would demand.
- **SF2P** — second-generation 2 nm planned for 2026.

Samsung's persistent problem is not device capability — it was first to GAA — but **yield and customer trust**. Its foundry business has repeatedly lost large external customers to TSMC after yield shortfalls. Its 2025 Tesla AI5/AI6 agreement and Taylor, Texas fab are the attempts to break that pattern.

### Intel

| Node | Status |
|---|---|
| Intel 7 (formerly 10 nm Enhanced SuperFin) | Alder Lake, late 2021 |
| Intel 4 | First Intel EUV node; Meteor Lake compute tile |
| Intel 3 | Foundry-capable; Sierra Forest / Granite Rapids |
| Intel 20A | **Cancelled** as a production node; effort folded into 18A |
| **Intel 18A** | **RibbonFET (GAA) + PowerVia (backside power).** Intel's own process page states it is "in high-volume production in the United States" and "ready for customer projects," claiming vs Intel 3.1: **+18% performance at iso-power, −38% power at iso-performance, +30% chip density**, and ~30% higher CPU frequency at ~0.5 V versus FinFET designs. PowerVia is claimed to cut worst-case dynamic voltage droop by up to **10×**. Variants: 18A-P (mobile-optimised, >9% higher performance at iso-power) and 18A-PT (for 3D integration) |
| Intel 14A | Next node; the first Intel node planned around High-NA EUV. Intel has publicly conditioned its continuation on securing external foundry customers |

Intel is the only manufacturer with **backside power in volume production ahead of TSMC**, and the only one to have taken High-NA tools first. Whether that translates into foundry business is the central question for the company (`07`, `08`). The US government took a **9.9% stake in Intel in August 2025**, converting US$11.1 bn of CHIPS grants into equity — a fact with no precedent in modern US industrial policy.

### Rapidus (Japan)

Founded **10 August 2022** by eight Japanese companies (Denso, Kioxia, MUFG Bank, NEC, NTT, SoftBank, Sony, Toyota) with an initial ¥7.3 bn of private capital and, since then, extraordinary state support: ¥70 bn (August 2022), ¥260 bn (April 2023), up to ¥590 bn (April 2024), and **¥802.5 bn (≈US$5.4 bn) in fiscal 2025**, within a US$65 bn programme announced November 2024 running to 2030.

Technology comes from **IBM** (2 nm nanosheet GAA, partnership announced 13 December 2022) and **imec** (Core Partner Program, April 2023). The IIM-1 fab is at **Chitose, Hokkaido** (ground broken September 2023). The **pilot line started 1 April 2025**; a 2 nm prototype wafer was shown on **18 July 2025** at **237.31 MTr/mm²**. Mass production target: **second half of 2027**.

The honest assessment: Rapidus has credible technology transfer and unprecedented funding, but no volume-manufacturing learning curve, no customer base, and it is attempting to enter at the hardest node in history. Japan's semiconductor equipment and materials strength is real; a Japanese leading-edge *logic foundry* has not existed for two decades.

### SMIC and the Chinese constrained position

SMIC established a **7 nm-class process on 21 July 2022** — using **DUV multi-patterning only**, since EUV export to China has been prohibited since 2019 (Dutch licensing) and comprehensively since the October 2022 US rules. As of December 2025 SMIC was reported at "**N+3**", described as a scaled evolution of its 7 nm-class process. Its products include Huawei's **Kirin 9000s** (7 nm, 2023), **Kirin 9020** (7 nm, Q4 2024) and **Kirin 9030** (reported as SMIC 5 nm-class, Q4 2025), and the **Ascend 910B/910C** AI accelerators.

The constraint is arithmetic, not ingenuity. Without EUV, every additional density step requires more DUV exposures: a 5 nm-class metal layer needs quadruple patterning where EUV would need a single exposure. The consequences are (a) cost per wafer that rises steeply, (b) cycle time that lengthens with each added mask, (c) yield that compounds downward across more steps, and (d) capacity consumed by re-exposing the same wafers. SMIC has demonstrated it can *make* 7 nm and 5 nm-class parts; the open question is at what yield, cost and volume — figures it does not publish. SMIC has been on the US Entity List since **December 2020**, and Taiwan added it to its own export-control list in **June 2025**.

## 8. Yield learning — how a node actually ramps

Yield is modelled as `Y = Y0 · f(D0·A)`, where `D0` is defect density per cm² and `A` is die area. The commonly used Murphy model gives `Y = ((1 − e^(−D0·A))/(D0·A))²`. The practical implications:

- **Large dies are punished quadratically.** At D0 = 0.1/cm², a 100 mm² die yields roughly 90%; an 800 mm² die yields roughly 45%. This single fact drives chiplet adoption (`04`).
- A new node typically starts risk production at defect densities several times the mature target and takes **four to eight quarters** to converge. Each learning cycle is gated by the 3–4 month wafer cycle time (`05`), which is why yield learning cannot be accelerated by simply spending more.
- **Redundancy changes the arithmetic.** Memory repairs itself with spare rows and columns; GPUs and CPUs disable defective SMs, cores or cache slices and sell the part as a lower SKU. The economically relevant metric is therefore not "perfect die yield" but **yield to a saleable bin**.
- Published yield figures are almost always leaks or analyst estimates. The Samsung SF2 "50–60% into early 2026" figure above is of that character. TSMC does not publish node yields at all; treat any specific TSMC yield number you encounter as unverified.

## 9. The honest state of 2 nm as of August 2026

- **TSMC N2 is in volume production** (from 4Q 2025, TSMC's own statement) and is the node the industry's highest-value products are moving to. TSMC's 2Q 2026 gross margin of **67.7%** on **US$40.20 bn** of quarterly revenue indicates a company with pricing power and no yield crisis.
- **Intel 18A is in high-volume manufacturing** by Intel's own account, with backside power in production ahead of everyone. The unresolved question is external customers, not silicon.
- **Samsung SF2 is producing** — its own Exynos 2600 — at yields reported around 50–60% in early 2026.
- **Rapidus is on a pilot line** with a 2027 production target.
- **China has no 2 nm path** without EUV, and there is no credible domestic EUV tool. SMIC's route is DUV multi-patterning at rising cost.
- **High-NA is deployed but not yet load-bearing.** Intel is furthest along; TSMC is deliberately deferring. No 2026 production node depends on High-NA.
- The binding constraints on leading-edge output in 2026 are not lithography resolution. They are **advanced packaging capacity (CoWoS), HBM supply, and power availability at the datacentre** (`08`).

## Open questions

- NXE:3800E and EXE:5200B throughput figures unverified (`needs-verification`).
- TSMC N2 percentage performance claims come from secondary reporting; TSMC's public page does not state them.
- TSMC A14 timing and specifications unverified.
- Actual N2 and 18A yields are not public. Samsung SF2's 50–60% figure is secondary reporting.
- The claim that Kirin 9030 uses an SMIC 5 nm-class process is from a secondary source and is contested; other reporting describes it as an N+3 evolution of 7 nm.

## Sources

- [Extreme ultraviolet lithography — Wikipedia](https://en.wikipedia.org/wiki/Extreme_ultraviolet_lithography) — accessed 2026-08-25
- [EUV lithography systems — ASML](https://www.asml.com/en/products/euv-lithography-systems) — accessed 2026-08-25
- [ASML Holding — Wikipedia](https://en.wikipedia.org/wiki/ASML_Holding) — accessed 2026-08-25
- [TSMC 2nm Technology](https://www.tsmc.com/english/dedicatedFoundry/technology/logic/l_2nm) — accessed 2026-08-25
- [TSMC A16 Technology](https://www.tsmc.com/english/dedicatedFoundry/technology/logic/l_A16) — accessed 2026-08-25
- [Intel 18A process technology](https://www.intel.com/content/www/us/en/foundry/process/18a.html) — accessed 2026-08-25
- [2 nm process — Wikipedia](https://en.wikipedia.org/wiki/2_nm_process) — accessed 2026-08-25
- [3 nm process — Wikipedia](https://en.wikipedia.org/wiki/3_nm_process) — accessed 2026-08-25
- [Rapidus — Wikipedia](https://en.wikipedia.org/wiki/Rapidus) — accessed 2026-08-25
- [SMIC — Wikipedia](https://en.wikipedia.org/wiki/Semiconductor_Manufacturing_International_Corporation) — accessed 2026-08-25
- [TSMC 2Q26 Quarterly Results](https://investor.tsmc.com/english/quarterly-results/2026/q2) — accessed 2026-08-25
- [CHIPS and Science Act — Wikipedia](https://en.wikipedia.org/wiki/CHIPS_and_Science_Act) — accessed 2026-08-25
