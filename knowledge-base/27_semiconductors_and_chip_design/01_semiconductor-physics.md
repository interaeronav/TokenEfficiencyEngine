---
id: semi.physics
title: Semiconductor physics — from band theory to the CFET
domain: 27_semiconductors_and_chip_design
tags: [semiconductor-physics, mosfet, band-theory, doping, pn-junction, subthreshold-slope, leakage, dennard-scaling, moores-law, finfet, gaafet, nanosheet, cfet]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Moore's law", url: "https://en.wikipedia.org/wiki/Moore%27s_law", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Multigate device", url: "https://en.wikipedia.org/wiki/Multigate_device", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "2 nm process", url: "https://en.wikipedia.org/wiki/2_nm_process", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "3 nm process", url: "https://en.wikipedia.org/wiki/3_nm_process", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Intel 18A process technology", url: "https://www.intel.com/content/www/us/en/foundry/process/18a.html", publisher: "Intel Corporation", accessed: 2026-08-25}
related: [semi.overview, semi.fabrication, semi.euv]
---

# Semiconductor physics — from band theory to the CFET

**Summary.** Everything in digital electronics rests on one device — the MOSFET — and on one inconvenient constant: at room temperature a thermally-populated barrier cannot be switched off faster than about 60 mV per decade of current. That number, `(kT/q)·ln(10)` = 59.6 mV/decade at 300 K, is why supply voltages stopped falling around 2005, why Dennard scaling ended, why power rather than area became the binding constraint on chip design, and ultimately why the industry has spent twenty years redesigning the transistor's *geometry* (planar → FinFET → nanosheet → CFET) rather than simply shrinking it. This file builds from band theory to the 2026 device roadmap, and treats Moore's Law as an economic observation with a documented history rather than a law of nature.

## Key facts

| Quantity | Value | Note |
|---|---|---|
| Silicon bandgap `Eg` at 300 K | 1.12 eV | 1.17 eV at 0 K; falls with temperature |
| Silicon intrinsic carrier concentration `ni` at 300 K | ~1.0 × 10¹⁰ cm⁻³ | vs 5 × 10²² atoms/cm³ — semiconductors are *nearly* insulators |
| Thermal voltage `kT/q` at 300 K | 25.85 mV | The origin of every "60 mV" statement |
| Subthreshold swing theoretical floor | 59.6 mV/decade at 300 K | `(kT/q)·ln(10)`; real devices 65–75 mV/dec |
| Electron / hole mobility in bulk Si | ~1400 / ~450 cm²·V⁻¹·s⁻¹ | Why PMOS is wider than NMOS, historically ~2–3× |
| SiO₂ relative permittivity | 3.9 | HfO₂ high-k: ~20–25 |
| Gate oxide thickness at the 90 nm node | ~1.2 nm SiO₂ (≈5 atomic layers) | Direct tunnelling forced the high-k/metal-gate switch at 45 nm (2007) |
| Typical Vdd trajectory | 5 V (0.8 µm) → 1.8 V (180 nm) → 1.0 V (45 nm) → ~0.75 V (5 nm) → ~0.65–0.75 V (2 nm class) | Scaling essentially stalled below ~0.7 V |
| Contacted poly (gate) pitch, 2 nm class | ~45 nm | Same as TSMC N3 — gate pitch has almost stopped scaling |
| Minimum metal pitch | 23 nm (TSMC N3E); ~20 nm (2 nm class) | |
| SRAM bit cell, TSMC N3 / N3E | 0.0199 µm² / 0.021 µm² | SRAM scaling has effectively stalled |

## 1. Band theory, in the amount needed

Isolated atoms have discrete energy levels. Bring 10²³ of them into a crystal and the levels split and smear into **bands**. In silicon the highest fully-occupied band at 0 K is the **valence band**; the next empty one is the **conduction band**; between them is a forbidden **bandgap** of 1.12 eV at 300 K.

- **Metals** have a partly-filled band — carriers are free at any temperature.
- **Insulators** have a large gap (SiO₂: ~9 eV) — thermal excitation is hopeless.
- **Semiconductors** have a gap small enough that thermal energy, light, or (crucially) *deliberate impurities* can put usable carrier densities into the conduction band.

Silicon's gap is **indirect** — the conduction-band minimum sits at a different crystal momentum from the valence-band maximum — which is why silicon is a poor light emitter and why silicon photonics uses germanium or III-V materials for sources. GaAs (1.42 eV) and InP are direct-gap; GaN (3.4 eV) and SiC (3.26 eV for 4H) are wide-gap, hence their dominance in power and RF (`07`, Infineon/ST).

Carriers obey Fermi–Dirac statistics; the **Fermi level** `EF` is the energy at which occupation probability is ½. In an intrinsic semiconductor `EF` sits near mid-gap. Everything that follows is the story of moving `EF` around — by doping, by applied bias, or by a gate.

## 2. Doping and the p-n junction

**Doping** substitutes impurity atoms into the lattice:

- **n-type**: group-V donors (phosphorus, arsenic, antimony) contribute a loosely-bound fifth electron. Typical source/drain doping: 10²⁰–10²¹ cm⁻³. Channel/well doping historically 10¹⁷–10¹⁸ cm⁻³.
- **p-type**: group-III acceptors (boron, and BF₂ for shallow implants) contribute a hole.

Mass action holds in equilibrium: `n·p = ni²`. Doping to 10¹⁸ cm⁻³ raises `n` by eight orders of magnitude over intrinsic — this is the whole trick.

Put n and p material in contact and mobile carriers diffuse across, leaving behind fixed ionised dopants. The resulting **depletion region** carries a built-in field; equilibrium is reached when drift balances diffusion. The built-in potential is

`Vbi = (kT/q)·ln(Na·Nd / ni²)` — typically 0.6–0.9 V in silicon.

The diode equation `I = Is·(exp(qV/nkT) − 1)` follows, with ideality factor `n` ≈ 1–2. Two properties matter downstream:

1. **Rectification** — the basis of every ESD clamp, every substrate isolation scheme, and every solar cell.
2. **Reverse leakage** — the source/drain-to-body junctions of every MOSFET are reverse-biased diodes, and their leakage (including band-to-band tunnelling and gate-induced drain leakage) is a real component of standby power at advanced nodes.

## 3. The MOSFET

A MOSFET is a **capacitor that modulates a resistor**. In an n-channel enhancement device built in a p-type body: source and drain are n⁺ regions; between them the p-type channel is normally non-conducting (two back-to-back diodes). A gate electrode, separated from the silicon by a thin dielectric, is biased positive. Three regimes follow:

- **Accumulation** (Vg < 0): holes pile up at the surface.
- **Depletion** (0 < Vg < Vt): holes are pushed away; a depletion layer forms.
- **Inversion** (Vg > Vt): the surface population *inverts* to electrons, forming a conducting channel. **Strong inversion** is conventionally defined as surface potential = 2φF.

### Threshold voltage

`Vt = VFB + 2φF + (√(2εsi·q·Na·2φF))/Cox`

where `VFB` is the flat-band voltage (set by gate work function and fixed charge), `φF` the bulk Fermi potential, and `Cox = εox/tox` the oxide capacitance per unit area. Practical consequences:

- Vt is set primarily by **gate work function** and **channel doping**. Modern nodes use multiple metal-gate work-function stacks to offer 2–4 Vt flavours (ULVT / LVT / SVT / HVT). Choosing Vt per cell is the single most-used lever in physical design: LVT for timing-critical paths, HVT for everything else, because leakage rises roughly an order of magnitude per ~100 mV of Vt reduction.
- **Random dopant fluctuation (RDF)**: at 22 nm a channel contains only tens of dopant atoms, so Poisson statistics produce σVt of tens of mV. This is the physical origin of much local variation, and one of the reasons FinFET and nanosheet channels are **undoped or lightly doped**, with Vt set by work function instead.

### Current equations

Long-channel, linear region (Vds < Vgs − Vt):
`Id = µn·Cox·(W/L)·[(Vgs − Vt)·Vds − Vds²/2]`

Saturation:
`Id = ½·µn·Cox·(W/L)·(Vgs − Vt)²`

Short-channel devices are **velocity saturated**: carriers cap out near 10⁷ cm/s in silicon, and `Id` becomes roughly *linear* in overdrive rather than quadratic — `Id ≈ W·vsat·Cox·(Vgs − Vt − Vdsat)`. This matters: it means shrinking L stops buying drive current, and drive comes instead from effective width, mobility (strain engineering), and reduced parasitic resistance.

## 4. The 60 mV/decade limit and why it governs everything

Below threshold, the channel is not off — it is a thermally-populated barrier, and current falls **exponentially** with gate voltage:

`Id ∝ exp(q·Vgs / (n·kT))`

The **subthreshold swing** `S = (n·kT/q)·ln(10)` is the gate voltage needed to change current by 10×. The body factor `n = 1 + Cdep/Cox` is ≥ 1, so:

> ⚠️ **`S ≥ 59.6 mV/decade at 300 K`.** This is a thermodynamic floor for any device that switches by modulating a thermal barrier. No amount of process improvement escapes it. Real FinFETs achieve ~65–70 mV/dec; good nanosheet devices ~65 mV/dec.

The consequence chain is the central story of modern chip design:

1. To switch fast you want large overdrive `(Vdd − Vt)`.
2. To keep off-state leakage tolerable you need `Vt` several times `S` above zero — roughly 300–400 mV for `Ioff` in the low nA/µm range.
3. Therefore `Vdd` cannot fall much below ~0.6–0.7 V without either destroying performance or exploding leakage.
4. Dynamic power `P = α·C·V²·f` therefore stops falling.
5. Therefore **power density**, not transistor count, became the constraint — the "dark silicon" and "power wall" era from roughly 2005 onwards.

Steep-slope research devices (tunnel FETs using band-to-band tunnelling, negative-capacitance FETs using ferroelectric gate stacks) aim to beat 60 mV/dec. As of 2026 none is in volume production; TFETs deliver sub-60 mV/dec only at impractically low currents.

## 5. Short-channel effects

As `L` approaches the source/drain depletion widths, the gate loses exclusive control of the channel:

- **Vt roll-off** — short devices have lower Vt because drain and source depletion regions already deplete part of the channel.
- **DIBL (drain-induced barrier lowering)** — drain bias lowers the source-side barrier. Measured in mV/V (Vt shift per volt of Vds); 50–150 mV/V is typical, and lower is better. DIBL is the cleanest single number for "how good is the electrostatics of this device".
- **Punch-through** — source and drain depletion regions merge; current flows below the gate's control entirely.
- **Hot carrier injection and channel-length modulation** — reliability and output-conductance degradation.

The controlling parameter is the **natural length** `λ ≈ √(εsi·tsi·tox/εox)` for a thin-body device. Electrostatic integrity requires roughly `L > 5λ`. This single expression explains the entire device roadmap: to shrink `L`, you must shrink `tsi` (body thickness) and `tox` (electrically, via high-k), or increase the number of gates surrounding the channel.

## 6. Leakage mechanisms — the five that matter

| Mechanism | Where | Mitigation |
|---|---|---|
| Subthreshold conduction | Source→drain, gate off | Higher Vt, better electrostatics (FinFET/GAA), power gating |
| Gate direct tunnelling | Through gate dielectric | High-k/metal gate (Intel 45 nm, 2007): HfO₂ at ~2–3 nm physical gives ~1 nm equivalent oxide thickness with orders of magnitude less tunnelling |
| GIDL (gate-induced drain leakage) | Gate–drain overlap, band-to-band tunnelling | Lighter drain doping, spacer engineering |
| Junction / band-to-band tunnelling | Reverse-biased S/D–body junctions | Doping-profile engineering; worse with high channel doping |
| Punch-through / substrate | Body | Halo implants, SOI, thin-body devices |

At 28 nm and below, static (leakage) power is a first-class design concern, routinely 20–40% of total power in a mobile SoC at high temperature. Every physical-design flow uses multi-Vt swapping, power gating with retention flops, body biasing (on FD-SOI), and clock gating as standard countermeasures (`03`).

## 7. Dennard scaling and its end

Robert Dennard's 1974 paper set out **constant-field scaling**. Shrink every dimension and the voltage by κ (say 0.7 per generation), and increase doping by κ⁻¹:

| Quantity | Scales as |
|---|---|
| Dimensions (L, W, tox) | ×κ |
| Voltage | ×κ |
| Capacitance | ×κ |
| Delay (CV/I) | ×κ |
| Power per device | ×κ² |
| Device density | ×1/κ² |
| **Power density** | **×1 (constant)** |

That last row is the miracle: for two decades you got twice the transistors, ~40% more clock speed, and *no increase in power per unit area*. It is what made 1974–2004 feel effortless.

It ended because voltage stopped scaling, for exactly the reason in §4: threshold voltage cannot scale without leakage exploding, so supply voltage cannot scale without losing overdrive. Dennard scaling broke down around 2005–2007. The visible symptoms:

- **Clock frequency plateaued** at 3–4 GHz in 2004–2005 and has barely moved since. Intel cancelled the 4 GHz Pentium 4 in October 2004.
- **The multicore turn** — parallelism replaced frequency as the way to spend transistors.
- **Dark silicon** — you can integrate more transistors than you can simultaneously power at full speed.
- **Specialisation** — if you cannot run everything fast, run the important things efficiently. This is the physical root of the accelerator era covered in `04`.

## 8. Moore's Law — the actual history

- **1965**: Gordon Moore, in *Electronics*, observes that "the complexity for minimum component costs has increased at a rate of roughly a factor of two per year," projecting a decade forward. Note the wording: it is a statement about the *cost-optimal* component count, i.e. an economic observation.
- **1975**: Moore revises the doubling period to **two years** at IEDM — a 41% compound annual growth rate.
- The "18 months" version is not Moore's; it is generally attributed to Intel's David House, combining density and speed gains.
- Node cadence in practice: 20 µm (1968) → 10 µm (1971) → 6 µm (1974) → 3 µm (1977) → 1 µm (1984) → 350 nm (1993) → 180 nm (1999) → 90 nm (2003) → 22 nm (2012) → 7 nm (2018) → 3 nm (2022) → 2 nm (2025).
- **The slowdown is documented by the participants.** Intel CEO Brian Krzanich, 2015: "Our cadence today is closer to two and a half years than two." NVIDIA CEO Jensen Huang declared Moore's Law dead in September 2022; Intel's Pat Gelsinger publicly disagreed days later.

**What is actually still scaling in 2026:**

- Transistor *count per package* — very much yes, aided by chiplets. NVIDIA's B100-class accelerator carries ~208 billion transistors across two reticle-limit dies; the GB202 consumer die alone exceeds 92 billion.
- Transistor *density per mm²* — yes, but at roughly 1.1–1.3× per node rather than 2×, and unevenly (logic scales, SRAM and analog barely do).
- **Cost per transistor** — this is where the law has genuinely broken. Wafer prices at each new node have risen faster than density since roughly 16/14 nm, so cost-per-transistor improvement has flattened and by some accounts reversed at the leading edge. Since Moore's original statement was explicitly about *minimum cost per component*, this is the strongest case that Moore's Law in its literal form has ended. See `08` for the cost curve.

> ⚠️ Treat any single-number claim about "cost per transistor" with suspicion: foundry wafer pricing is confidential and every published curve is a modelled estimate.

## 9. Power, performance, area — and the fourth axis, cost

Design is a four-way negotiation (PPAC). Useful mental models:

- **Dynamic power** `P = α·C·Vdd²·f`. Quadratic in voltage — hence DVFS (dynamic voltage and frequency scaling) is the highest-leverage runtime knob.
- **Energy per operation** `E = C·Vdd²` — independent of frequency. This is the correct metric for anything battery- or datacentre-power-limited, and why running many cores slowly beats few cores fast for throughput workloads.
- **Delay** `≈ C·Vdd / Id` with `Id` roughly linear in `(Vdd − Vt)` for velocity-saturated devices — so delay degrades sharply as Vdd approaches Vt. Near-threshold operation (~0.4–0.5 V) can give 5–10× energy efficiency at a large frequency cost and severe variability penalties.
- **Area** buys you parallelism, cache and margin — and costs you yield (`08`: defect density × area drives good-die count).

## 10. The device architecture progression

### Planar bulk CMOS → ~28/20 nm

Gate on top of the channel; one gate face. Electrostatics maintained by shrinking oxide thickness and raising channel doping — both of which hit walls (tunnelling; RDF and mobility degradation). Extensions used along the way: strained silicon (Intel 90 nm, 2003), high-k/metal gate (Intel 45 nm, 2007), and FD-SOI (an alternative thin-body planar route still used by STMicroelectronics and GlobalFoundries at 22FDX/18FDX, attractive for RF and ultra-low-power because of back-bias control).

### FinFET, ~22/16 nm → ~5/3 nm

The channel is a vertical fin; the gate wraps three faces. Origin: the DELTA transistor, fabricated at Hitachi Central Research Laboratory in **1989** (Hisamoto, Kaga, Kawamoto, Takeda); the name "FinFET" was coined in December 2000 by a Berkeley group including Chenming Hu and Tsu-Jae King Liu. First volume production: **Intel's 22 nm tri-gate, 2012**, claimed at 37% higher speed or under half the power of the previous planar generation; TSMC announced 16 nm FinFET in 2014.

Why it was needed: three-sided control cuts the natural length, killing DIBL and punch-through at gate lengths where planar had failed. Why it ran out: width is quantised in fins (you get drive current in integer multiples), fin pitch scaling stalled around 22–24 nm, and fin height cannot grow indefinitely without mechanical and capacitance penalties.

### Gate-all-around nanosheet / MBCFET, 3 nm → 2 nm

Horizontal stacked sheets of silicon with the gate wrapped fully around all four sides. A GAA MOSFET was first demonstrated in **1988** by a Toshiba team (Takato, Sunouchi, Masuoka). Production history:

- **Samsung SF3E (3 nm-class MBCFET)** — the first GAA in production, shipping from mid-2022.
- **TSMC N3** stayed with FinFET; TSMC's GAA debut is **N2, in volume production from 4Q 2025** (TSMC's own statement).
- **Intel 18A (RibbonFET + PowerVia)** — in high-volume manufacturing per Intel's process page, claiming up to 18% higher performance at iso-power, 38% lower power at iso-performance and 30% higher density versus Intel 3.1, plus roughly 30% higher CPU frequency at ~0.5 V versus FinFET.

The decisive advantage is **continuous effective-width tuning**: nanosheet width (typically ~8–50 nm) is a design variable, so drive current is no longer quantised in fins. TSMC markets this flexibility as NanoFlex; Intel and Samsung have equivalents. Electrostatics also improve — four-sided control gives the smallest natural length of any planar-substrate device.

### Forksheet and CFET — what comes after

- **Forksheet** (imec concept): NMOS and PMOS nanosheets share a dielectric wall, allowing the n-to-p separation to shrink below what independent gates permit. Primarily an *area* play — it targets cell height reduction (e.g. 5T → 4.3T tracks).
- **CFET (complementary FET)**: stack the PMOS device directly *above* the NMOS device. This halves the footprint of a CMOS pair in principle and is the leading candidate for the 2029–2032 window. Monolithic CFET requires sequential epitaxy or wafer bonding at extreme alignment tolerance; sequential (bonded) CFET is the more likely first production form. imec, TSMC, Intel and Samsung have all shown research devices; none is in production as of August 2026.
- **Backside power delivery** is orthogonal but arrives in the same window and is arguably more important near-term: moving power rails to the wafer backside frees front-side routing tracks for signals and slashes IR drop. Intel PowerVia is in production on 18A; TSMC's Super Power Rail arrives with **A16, production-ready 2H 2026**, claimed at +8–10% speed at the same Vdd or −15–20% power at the same speed versus N2P, with up to 1.10× density.

### Beyond silicon channels

2D materials (MoS₂, WS₂) offer atomically-thin bodies with excellent electrostatics; carbon nanotube FETs offer high mobility. Both remain research-stage for logic in 2026 — the blockers are contact resistance, wafer-scale uniform growth, and doping control, not the intrinsic physics.

## Open questions

- Published DIBL, subthreshold swing and effective drive-current figures for TSMC N2 and Intel 18A production devices are not public in primary sources; the numbers here are generic device-class values.
- CFET timing (2029–2032) is an industry expectation drawn from roadmap presentations, not a committed date from any manufacturer — treat as `needs-verification`.

## Sources

- [Moore's law — Wikipedia](https://en.wikipedia.org/wiki/Moore%27s_law) — accessed 2026-08-25
- [Multigate device — Wikipedia](https://en.wikipedia.org/wiki/Multigate_device) — accessed 2026-08-25
- [2 nm process — Wikipedia](https://en.wikipedia.org/wiki/2_nm_process) — accessed 2026-08-25
- [3 nm process — Wikipedia](https://en.wikipedia.org/wiki/3_nm_process) — accessed 2026-08-25
- [Intel 18A process technology](https://www.intel.com/content/www/us/en/foundry/process/18a.html) — Intel, accessed 2026-08-25
- [TSMC A16 Technology](https://www.tsmc.com/english/dedicatedFoundry/technology/logic/l_A16) — TSMC, accessed 2026-08-25
- [TSMC 2nm Technology](https://www.tsmc.com/english/dedicatedFoundry/technology/logic/l_2nm) — TSMC, accessed 2026-08-25
