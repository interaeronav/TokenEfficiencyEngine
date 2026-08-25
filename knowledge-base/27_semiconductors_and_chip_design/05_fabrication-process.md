---
id: semi.fabrication
title: How a chip is made — crystal growth to final test, step by step
domain: 27_semiconductors_and_chip_design
tags: [fabrication, czochralski, wafer, cleanroom, oxidation, cvd, ald, pvd, epitaxy, photolithography, multi-patterning, etching, rie, ale, ion-implantation, annealing, cmp, damascene, low-k, feol, beol, wafer-test, dicing, packaging]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Wafer (electronics)", url: "https://en.wikipedia.org/wiki/Wafer_(electronics)", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Photolithography", url: "https://en.wikipedia.org/wiki/Photolithography", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Semiconductor fabrication plant", url: "https://en.wikipedia.org/wiki/Semiconductor_fabrication_plant", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Extreme ultraviolet lithography", url: "https://en.wikipedia.org/wiki/Extreme_ultraviolet_lithography", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Applied Materials", url: "https://en.wikipedia.org/wiki/Applied_Materials", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Chip Scale Package", url: "https://en.wikipedia.org/wiki/Chip_Scale_Package", publisher: "Wikipedia", accessed: 2026-08-25}
related: [semi.euv, semi.physics, semi.economics]
---

# How a chip is made — crystal growth to final test, step by step

**Summary.** A leading-edge logic wafer passes through on the order of a thousand or more individual process steps over roughly three to four months, in an environment cleaner than an operating theatre by three orders of magnitude, and emerges carrying tens of billions of features whose critical dimensions are controlled to a small fraction of a nanometre. This file walks the whole sequence — crystal growth, wafer prep, cleanroom discipline, the unit processes (oxidation, deposition, lithography, etch, implant, anneal, CMP), the front-end and back-end-of-line flows, and then test, dicing, packaging and final test — with the numbers that make each step real. `06` takes lithography further into EUV and the leading edge.

## Key facts

| Item | Value | Note |
|---|---|---|
| Leading-edge wafer diameter | 300 mm (thickness ~775 µm) | 450 mm abandoned; Global 450mm Consortium disbanded 2017 |
| Why not 450 mm | Wafers ~4× the cost of 300 mm; equipment cost +20–50%; only 10–20% cost-per-die benefit | Micron's CEO, 2014: "450 mm may never happen" |
| 300 mm wafer area | 70,686 mm² | ~82 gross dies at 858 mm²; ~700 at 100 mm² |
| Cleanroom class at critical steps | ISO Class 1–3 (≈ FED-STD-209E Class 1–10) | ISO 1 = ≤10 particles ≥0.1 µm per m³ |
| Total mask layers, leading-edge logic | ~80–100 | Of which EUV layers: ~13–15 at 5 nm; more at 3/2 nm |
| Total process steps, leading-edge logic | ~1,000–1,500+ | Each mask layer implies 10–15 unit steps |
| Cycle time, leading-edge logic | ~3–4 months wafer start to wafer out | Memory is faster; mature analog faster still |
| Equipment cost per tool | Several million USD upward; EUV scanners up to ~US$340 m | Several hundred tools per fab |
| Fab construction cost | "Over one billion USD… tens of billions not uncommon"; TSMC "over US$45 bn" for a 2 nm fab (2025) | |
| Copper interconnect | Introduced by IBM, 1997, at 220 nm | Replaced aluminium; damascene process |

## 1. Silicon: from sand to wafer

1. **Metallurgical-grade silicon** — quartzite reduced with carbon in an arc furnace, ~98–99% pure.
2. **Siemens process** — converted to trichlorosilane, distilled, and redeposited as **polysilicon** at 9N–11N purity (electronic-grade: under one part per billion of most contaminants).
3. **Czochralski growth** — polysilicon is melted at ~1,414 °C in a quartz crucible; a seed crystal of known orientation (almost always ⟨100⟩ for CMOS, because the Si/SiO₂ interface trap density is lowest on the (100) face) is dipped and slowly withdrawn while rotating. The melt is doped to give the target substrate resistivity. Modern boules are 300 mm in diameter, up to 2 m long, and weigh several hundred kilograms. **Float-zone** growth gives higher purity and is used for power devices, not for CMOS logic.
4. **Wafering** — the boule is ground to exact diameter, notched for orientation, sliced with a diamond wire saw, then lapped, etched, and polished to a mirror finish. Final specification: 300 mm ± 0.2 mm diameter, ~775 µm thick, total thickness variation of a few micrometres, site flatness measured in tens of nanometres, and surface particle counts of a handful above 0.05 µm across the entire wafer.
5. **Epitaxial layer** (optional but usual for advanced logic) — a defect-free single-crystal layer of controlled doping grown on the polished surface by CVD, giving a purer, better-controlled device region than the bulk.

Suppliers: Shin-Etsu, SUMCO, GlobalWafers, Siltronic, SK Siltron — five companies for a genuinely global input.

## 2. The cleanroom

A single 20 nm particle landing on a critical layer kills a die. Fabs therefore run:

- **ISO Class 1–3 air** at critical tools (ISO 1 permits ≤10 particles ≥0.1 µm per cubic metre; ambient outdoor air has tens of millions).
- **Laminar downflow** through ceiling-mounted ULPA filters at ~0.45 m/s, with raised perforated floors.
- **Temperature control to ±0.1 °C** and humidity to ±1% RH — because lithography overlay is sensitive to thermal expansion at the nanometre scale.
- **Vibration isolation** — scanners sit on massive isolated slabs; fabs are not built near railway lines.
- **Yellow light** in the lithography bays — filtered to exclude wavelengths that expose photoresist.
- **AMC control** — airborne molecular contamination (ammonia, amines, acids) is filtered chemically, since parts-per-billion of amine will poison a chemically-amplified resist.
- **Ultrapure water** — 18.2 MΩ·cm resistivity, degassed, with total organic carbon in the low parts per billion. A large fab consumes millions of litres per day; TSMC's water recycling programmes exist because of this.
- **Automation** — wafers travel in sealed 25-wafer **FOUPs** on an overhead hoist transport system. Humans do not carry wafers, and in the most advanced fabs humans are rarely in the cleanroom at all.

Fabs run 24/7/365 because tools are the capital and idle tools are pure loss (`08`).

## 3. The unit processes

### Oxidation

Thermal growth of SiO₂ by exposing silicon to O₂ (dry, slow, high quality) or H₂O vapour (wet, faster, less dense) at 800–1,200 °C. Governed by the Deal–Grove model. Silicon is consumed: growing `t` of oxide consumes ~0.44·`t` of silicon. Used today for gate oxides in mature nodes, sacrificial/screen oxides, pad oxides for STI, and field isolation. At advanced nodes the gate dielectric is not thermal SiO₂ but an ALD-deposited high-k stack over a thin interfacial oxide.

### Deposition

| Method | Mechanism | Typical films | Notes |
|---|---|---|---|
| **LPCVD** | Thermal CVD at low pressure, 600–900 °C | Polysilicon, Si₃N₄, TEOS oxide | Excellent conformality; too hot for back-end |
| **PECVD** | Plasma supplies the energy, 250–400 °C | SiO₂, SiN, SiCN, low-k | The BEOL workhorse — low enough temperature not to damage metal |
| **ALD** | Self-limiting alternating precursor pulses, one monolayer per cycle | HfO₂ and other high-k, TiN/TaN barriers, Al₂O₃, spacers for SADP | Atomic thickness control and near-perfect conformality; indispensable for GAA nanosheets, where the gate stack must wrap a fully-enclosed channel |
| **PVD (sputtering)** | Ions knock atoms from a target | Cu seed, Al, Ti, Ta, TaN, W | Line-of-sight; poor in high-aspect features, hence ALD liners |
| **Epitaxy** | Single-crystal CVD growth | SiGe source/drain (compressive strain for PMOS), Si:P/Si:C (tensile for NMOS), raised S/D, nanosheet channel/sacrificial stacks | Strain engineering has been a primary performance lever since Intel's 90 nm (2003) |
| **Electroplating (ECD)** | Electrochemical fill | Copper interconnect, TSVs, solder bumps | The damascene fill step |
| **Spin-on** | Liquid dispensed on a rotating wafer | Photoresist, some dielectrics, hardmasks | 1,000–5,000 rpm; thickness from viscosity and speed |

### Photolithography

The pattern-defining step, and the one that sets the node. Sequence per layer: dehydration bake and HMDS prime → spin resist (with BARC underneath to suppress reflections) → soft bake → expose → post-exposure bake → develop → hard bake → inspect. Coat and develop happen on a **track** (Tokyo Electron dominates) mechanically docked to the scanner.

**Resolution** obeys the Rayleigh criterion:

`CD = k1 · λ / NA`  and  `DOF = k2 · λ / NA²`

- `k1` is theoretically 0.61 for a two-point resolution criterion; production processes run near **0.4**, and 0.25 is the hard single-exposure limit.
- Wavelength history: g-line 436 nm → i-line 365 nm → KrF 248 nm → **ArF 193 nm** → ArF immersion 193i → **EUV 13.5 nm**.
- **Immersion** replaces the air gap with ultrapure water (n = 1.44), raising achievable NA past 1.0; production tools run **NA = 1.35** (water limits NA to about 1.4). 193i single exposure gives roughly 38 nm half-pitch.
- Depth of focus falls as NA², which is why advanced lithography needs wafer flatness and focus control in the tens of nanometres.

**The scanner.** A step-and-scan system: the wafer stage and reticle stage move in opposite directions at a 4:1 velocity ratio (matching the 4× reduction optics) while a slit of light scans the field. Field size 26 × 33 mm. Overlay (layer-to-layer alignment) is specified in the low single nanometres on advanced tools. Throughput on a DUV immersion scanner is ~200–300 wafers per hour; EUV is much lower (`06`).

**Multi-patterning** — how sub-38 nm pitches were reached before EUV, and how they are still reached below EUV's single-exposure limit:

- **LELE (litho-etch-litho-etch)** — decompose one design layer into two masks, print and etch each in turn. Doubles cost and adds an overlay error between the two colours directly into the CD budget. LELELE triples it.
- **SADP (self-aligned double patterning)** — print a sacrificial mandrel at relaxed pitch, deposit a conformal spacer by ALD, etch back to leave spacers on the mandrel sidewalls, remove the mandrel. The spacers are the pattern, at **half** the mandrel pitch, and their width is set by ALD thickness — so pitch is self-aligned and CD uniformity is excellent. Requires separate **cut masks** to break the resulting continuous lines, and produces only lines/spaces, not arbitrary 2D shapes.
- **SAQP** — repeat SADP; quarter pitch. Used at 10/7 nm fins and metal layers.
- Consequence: unidirectional metal layers with cut masks, and design rules that forbid arbitrary 2D geometry (`03`).

### Etching

Removal, ideally anisotropic (vertical) and selective (attacks the target, not the mask or the underlayer).

- **Wet etch** — chemical baths (HF for oxide, hot phosphoric acid for nitride, TMAH or KOH for crystallographic silicon etching). Isotropic; used for cleans, sacrificial-layer removal and MEMS. Crucially, wet etch is now used *inside* the GAA flow: the SiGe sacrificial layers between silicon nanosheets are removed by a highly selective etch through the source/drain openings, releasing the channels so the gate can be deposited all the way around.
- **RIE / plasma etch** — the workhorse. A capacitively- or inductively-coupled plasma generates reactive species; a DC bias accelerates ions vertically into the wafer, giving directionality by combining chemical reaction with physical bombardment. Fluorine chemistries (CF₄, C₄F₈, SF₆) for oxides and silicon; chlorine/bromine (Cl₂, HBr) for silicon and metals. **Sidewall passivation** — polymer deposited from the plasma on vertical surfaces — is what makes the profile vertical. Aspect ratios above 60:1 are routine in 3D NAND channel holes.
- **ALE (atomic layer etch)** — the etch counterpart of ALD: a self-limiting surface modification (e.g. chlorine adsorption) followed by a low-energy removal step, giving per-cycle removal of a fraction of a monolayer. Essential where a few angstroms of over-etch would destroy a nanosheet or a fin.
- **Etch is now as critical as lithography.** Lam Research, Tokyo Electron and Applied Materials contest this market, and its importance has grown as multi-patterning shifted pattern fidelity from the exposure to the etch.

### Ion implantation and annealing

Dopants are accelerated to 0.2 keV–3 MeV and fired into the wafer through a mask of patterned resist. The tool is a small particle accelerator with a mass-analysing magnet to select the desired ion. Dose (ions/cm²) and energy (which sets projected range) are the control variables; **channelling** along crystal axes is avoided by tilting the wafer ~7°.

Implantation damages the lattice and leaves dopants on interstitial sites, so an **anneal** must repair the crystal and move dopants onto substitutional sites — while diffusing them as little as possible. The thermal-budget squeeze has driven a progression: furnace anneal (minutes) → RTA (seconds) → **spike anneal** (sub-second) → **flash and laser anneal** (milliseconds to microseconds, surface-only). At advanced nodes, junction abruptness of a few nanometres per decade of concentration is required.

At GAA nodes, much doping is done by **in-situ doped epitaxy** rather than implant, because you cannot implant into a fully-wrapped channel stack.

### CMP (chemical-mechanical planarisation)

Invented at IBM in the 1980s and arguably the enabling process for multilevel interconnect. The wafer is pressed face-down against a rotating polyurethane pad while a slurry (abrasive silica or ceria particles plus chemistry that softens the surface) is fed in. Removes topography so that the next lithography step has a flat, in-focus surface — indispensable given the shallow depth of focus above.

Used for: STI oxide planarisation, poly/gate planarisation, tungsten contact plugs, and every copper damascene layer. Its characteristic failure modes are **dishing** (over-polish of wide soft features) and **erosion** (over-polish of dense arrays), which is why layout **density rules** and dummy-fill insertion exist (`03`).

## 4. FEOL — front end of line

Building the transistors. A modern GAA flow, in outline:

1. **STI (shallow trench isolation)** — pattern and etch trenches between device regions, line with oxide, fill (HDP or flowable CVD), CMP back.
2. **Well formation** — n-well and p-well implants, plus deep n-well for isolation; anneal.
3. **Superlattice epitaxy** (GAA-specific) — alternating Si/SiGe layers grown epitaxially; the SiGe will later be sacrificed to release the silicon nanosheets. FinFET flows instead pattern fins directly from the substrate using SADP/SAQP plus a fin-reveal etch.
4. **Fin/nanosheet patterning** — mandrel, spacer, etch; then fin cut/depopulation masks.
5. **Dummy gate** — deposit and pattern a sacrificial polysilicon gate over the channel (the "gate-last" or replacement-metal-gate flow, universal since 45 nm).
6. **Spacers** — ALD nitride/low-k spacers on the dummy gate sidewalls; these define the source/drain offset and, at GAA, the inner spacers that isolate the gate from the source/drain.
7. **Source/drain** — recess etch, then **epitaxial regrowth** of in-situ doped SiGe:B (PMOS, compressive strain) or Si:P (NMOS, tensile strain). The epi shape (diamond, bar) is itself an engineered parameter.
8. **ILD0 deposition and CMP**, exposing the dummy gate.
9. **Channel release** (GAA) — remove the dummy gate, then selectively etch the SiGe from between the silicon sheets, leaving suspended nanosheets.
10. **High-k / metal gate** — ALD interfacial oxide, ALD HfO₂-based high-k, then a stack of work-function metals (TiN, TiAlC, TaN) chosen per Vt flavour, then a low-resistance fill (W or Co). Wrapping this stack around suspended sheets with sub-nanometre control is the hardest step in the flow.
11. **Contacts** — self-aligned contact etch, silicide formation (NiSi, TiSi₂) to cut contact resistance, barrier/liner, and metal fill (W, Co, and increasingly Ru or Mo as dimensions shrink and liner volume becomes intolerable).

**Middle of line (MOL)** covers the contact and local-interconnect levels between FEOL and BEOL, and is now a major contributor to both resistance and yield loss.

## 5. BEOL — back end of line

Wiring. Ten to twenty metal levels, pitch increasing from ~20–23 nm at M1 to micrometres at the top redistribution layers.

**Copper dual damascene** — copper cannot be plasma-etched cleanly (its halides are not volatile at usable temperatures), so the process is inverted:

1. Deposit the interlayer dielectric (low-k).
2. Etch the **trench** (the wire) and the **via** (the connection down) — hence "dual".
3. Deposit a **barrier** (TaN/Ta, or increasingly a thinner ALD stack) to stop copper diffusing into the dielectric, where it is a lifetime killer, plus a copper **seed** by PVD.
4. **Electroplate** copper to overfill, with additives (accelerator, suppressor, leveller) tuned for bottom-up superfill so no void forms.
5. **CMP** the excess copper and barrier back to the dielectric.
6. Cap with a dielectric barrier (SiN, SiCN) or a selective metal cap (CoWP) to suppress surface electromigration.

**Low-k dielectrics** cut RC delay and crosstalk: SiO₂ (k = 3.9) → fluorinated silicate glass (3.5) → carbon-doped oxide/SiCOH (2.7–3.0) → porous SiCOH (2.2–2.5) → **air gaps** selectively introduced between critical lines. The trade is mechanical: low-k films are weak and porous, and they crack and delaminate during CMP, packaging and thermal cycling. This is the central materials tension in BEOL.

**The resistivity problem.** Below ~20 nm wire width, copper resistivity rises sharply because electron mean free path (~39 nm in bulk Cu) exceeds the wire dimension, so grain-boundary and surface scattering dominate; and the barrier/liner occupies a growing fraction of the cross-section. The industry response is to move the lowest, thinnest levels to **cobalt, ruthenium or molybdenum**, which need thinner or no barriers and have shorter mean free paths, and to introduce **backside power delivery** (`01`, `06`) so that the power network is no longer competing for scarce front-side tracks.

Final BEOL steps: aluminium or copper top-metal pads, passivation (SiN/polyimide), and pad openings.

## 6. Metrology, inspection and process control

Between process steps, wafers are measured: **scatterometry/OCD** for CD and profile, **CD-SEM** for direct critical-dimension measurement, **overlay metrology** for layer alignment, **ellipsometry** for film thickness, **four-point probe** for sheet resistance, and **brightfield/darkfield inspection** plus **e-beam inspection** for defects. KLA dominates this segment (US$12.2 bn revenue, FY2025).

Statistical process control feeds back through **APC/R2R (run-to-run) control**, adjusting the next lot's recipe from the last lot's measurements. A leading-edge fab measures a substantial fraction of wafers at dozens of points in the flow; the metrology tool count is a large fraction of total tool count and the data volume is a genuine big-data problem.

## 7. Wafer test (sort), dicing, packaging, final test

1. **Wafer electrical test / wafer sort** — a **prober** steps a card of fine needles (or, at advanced nodes, vertical probe cards) across the wafer; ATE (Advantest, Teradyne) applies scan and functional patterns. Bad dies are recorded in a wafer map (and historically inked). Memory dies are repaired here by blowing fuses to swap in redundant rows/columns — redundancy is why DRAM and NAND yields are high despite huge arrays. **Known-good-die** testing is now essential for chiplets, where one bad die can scrap an expensive package.
2. **Backgrinding** — the wafer is thinned from 775 µm to 50–300 µm (thinner still for stacking), after which it is fragile and handled on tape.
3. **Dicing** — diamond blade sawing, or **laser stealth dicing** and plasma dicing for thin/brittle wafers and low-k stacks that chip.
4. **Die attach** and **interconnect**:
   - **Wire bonding** — gold or copper wire, thermosonic; still the majority of packages by unit volume, and cheap.
   - **Flip-chip** — solder bumps or copper pillars on the die face, reflowed onto a substrate; then underfill to manage thermal-expansion mismatch. Necessary for high pin counts and power delivery.
   - **Hybrid bonding** — direct Cu–Cu and oxide–oxide bonding with no solder, at pitches an order of magnitude finer than microbumps; the basis of AMD's 3D V-Cache, TSMC SoIC and the newest HBM stacks.
5. **Packaging** — from simple QFN/BGA to **wafer-level CSP** (package area ≤1.2× the die area, per the IPC definition), **fan-out** (InFO), **2.5D interposer** (CoWoS), **embedded bridge** (EMIB), and **3D stacking** (Foveros). Substrates use ABF (Ajinomoto build-up film) — a single-supplier material that has been a periodic bottleneck. Molding, ball attach, marking and singulation follow.
6. **Burn-in** (where reliability requires it) — elevated voltage and temperature to precipitate infant-mortality failures.
7. **Final test** — full functional, at-speed, and parametric test over the specified temperature range, including the memory interfaces and analog blocks that cannot be tested at wafer sort. **Binning** sorts parts into speed/power grades; this is where a partially-defective die becomes a lower-SKU product, an economically enormous practice (a GPU with disabled SMs, a CPU with disabled cores or cache).
8. **Tape and reel, mark, ship.**

## 8. Step counts, cycle time and what they mean

- A leading-edge logic process runs roughly **80–100 mask layers**, and each mask layer implies about 10–15 unit operations (clean, coat, expose, develop, etch, strip, measure…), giving **~1,000–1,500+ total steps**.
- **Cycle time is 3–4 months** at the leading edge. The rule of thumb is one to two days of cycle time per mask layer, and the ratio of cycle time to pure processing time (the "X-factor") is typically 2–3× because of queueing at bottleneck tools.
- Consequence for yield learning: a process change takes a full cycle to evaluate. This is why yield ramps take quarters, not weeks, and why short-loop test structures and inline metrology are so heavily used (`06`, `08`).
- **Memory** is simpler in step count per bit but runs enormous volumes; **3D NAND** substitutes vertical stacking (200+ layers) for lithography scaling, trading extreme-aspect-ratio etch and deposition challenges for relaxed lithography.

## Open questions

- Exact step counts and cycle times per node are confidential; the ranges here are industry-consensus figures, not manufacturer disclosures (`needs-verification`).
- Fab-level water, power and gas consumption figures were not verified in this pass.

## Sources

- [Wafer (electronics) — Wikipedia](https://en.wikipedia.org/wiki/Wafer_(electronics)) — accessed 2026-08-25
- [Photolithography — Wikipedia](https://en.wikipedia.org/wiki/Photolithography) — accessed 2026-08-25
- [Semiconductor fabrication plant — Wikipedia](https://en.wikipedia.org/wiki/Semiconductor_fabrication_plant) — accessed 2026-08-25
- [Extreme ultraviolet lithography — Wikipedia](https://en.wikipedia.org/wiki/Extreme_ultraviolet_lithography) — accessed 2026-08-25
- [Applied Materials — Wikipedia](https://en.wikipedia.org/wiki/Applied_Materials) — accessed 2026-08-25
- [Chip Scale Package — Wikipedia](https://en.wikipedia.org/wiki/Chip_Scale_Package) — accessed 2026-08-25

