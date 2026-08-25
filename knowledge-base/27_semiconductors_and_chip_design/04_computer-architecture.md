---
id: semi.architecture
title: Computer architecture as practised — ISAs, cores, memory, chiplets and accelerators
domain: 27_semiconductors_and_chip_design
tags: [computer-architecture, isa, risc-v, out-of-order, branch-prediction, cache-coherence, ddr5, lpddr, gddr, hbm, noc, chiplets, cowos, foveros, ucie, gpu, simt, tensor-core, npu, tpu, trainium, cerebras, groq]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "RISC-V", url: "https://en.wikipedia.org/wiki/RISC-V", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "High Bandwidth Memory", url: "https://en.wikipedia.org/wiki/High_Bandwidth_Memory", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "DDR5 SDRAM", url: "https://en.wikipedia.org/wiki/DDR5_SDRAM", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Blackwell (microarchitecture)", url: "https://en.wikipedia.org/wiki/Blackwell_(microarchitecture)", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Tensor Processing Unit", url: "https://en.wikipedia.org/wiki/Tensor_Processing_Unit", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Cerebras", url: "https://en.wikipedia.org/wiki/Cerebras", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Groq", url: "https://en.wikipedia.org/wiki/Groq", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Chiplet", url: "https://en.wikipedia.org/wiki/Chiplet", publisher: "Wikipedia", accessed: 2026-08-25}
related: [semi.rtl, semi.physics, semi.firms]
---

# Computer architecture as practised — ISAs, cores, memory, chiplets and accelerators

**Summary.** Architecture is the discipline of spending transistors. Since Dennard scaling ended (`01`), the spending rules changed: frequency is fixed, power is the budget, and the returns come from parallelism, specialisation, memory bandwidth and packaging rather than from clock speed. This file covers ISA design and the RISC-V opening, the standard high-performance core (pipelining, superscalar issue, out-of-order execution, branch prediction, caches and coherence), the memory hierarchy with real bandwidth figures (DDR5, LPDDR5X, GDDR7, HBM3E/HBM4), on-chip interconnect, the chiplet and advanced-packaging turn (CoWoS, EMIB, Foveros, hybrid bonding, UCIe), and the accelerator landscape (GPUs and SIMT, tensor units, NPUs, TPU, Trainium, Groq, Cerebras) with dated specifications.

## Key facts

| Item | Value (dated) | |
|---|---|---|
| NVIDIA GB100 die | 104 bn transistors, TSMC custom 4NP; B100/B200 = 2 dies = 208 bn, NV-HBI link 10 TB/s | 2024–2025 |
| NVIDIA GB200 FP4 compute | ~20 PFLOPS (dense, excluding sparsity) | 2024 |
| NVIDIA GB202 (consumer Blackwell die) | >92.2 bn transistors, 750 mm², 24,576 CUDA cores | 2025 |
| HBM3E per stack | up to 1.2 TB/s, 9.8 GT/s, 1024-bit, 16-Hi, up to 48 GB | from May 2023 |
| HBM4 per stack | ~2.048 TB/s, 8 GT/s, **2048-bit**, 4–16 Hi, 16–64 GB; JESD270-4, April 2025 | 2025 |
| DDR5 | 4,000–6,400 MT/s baseline (up to 8.8 GT/s in spec), 32.0–70.4 GB/s per module, 1.1 V, two independent 32-bit subchannels, burst length 16; JEDEC 14 July 2020 | |
| Google TPU v7 "Ironwood" | 4,614 TFLOPS FP8, 192 GB HBM, 7.37 TB/s, pods of 256–9,216 chips | 2025 |
| Cerebras WSE-3 | 4 trillion transistors, 900,000 cores, TSMC 5 nm, full-wafer die | March 2024 |
| Groq LPU v1 (TSP) | 14 nm, 25 × 29 mm, >1 TeraOp/s per mm², 900 MHz; v2 on Samsung 4 nm | 2020 / 2023 |
| Reticle limit | 26 × 33 mm = 858 mm² (0.33-NA); High-NA halves the field to 26 × 16.5 mm | |

## 1. Instruction set architecture

An ISA is a contract: the set of instructions, registers, addressing modes, memory-consistency model, exception behaviour and privilege structure that software may rely on. The implementation beneath it is free to be anything.

**The three that matter commercially:**

- **x86-64** — Intel and AMD. Variable-length CISC encoding (1–15 bytes), decoded into internal micro-ops. The decode complexity is a real power and width cost (wide x86 decoders are expensive because instruction boundaries are not known in parallel), offset by four decades of binary compatibility and an unmatched software base.
- **Arm (AArch64)** — fixed 32-bit encoding, clean load/store design, weak memory model (which permits more reordering, hence more performance, but demands explicit barriers). Dominant in mobile, ascendant in servers (AWS Graviton, Ampere, NVIDIA Grace) and in Apple's Macs. Licensed under architecture licences (design your own core, e.g. Apple, Qualcomm Oryon) or core licences (use Arm's Cortex/Neoverse designs).
- **RISC-V** — an open standard, not a company's product.

### The RISC-V opportunity, stated precisely

RISC-V's structure: a small base integer ISA (**RV32I**, **RV64I**, plus embedded **RV32E** with 16 registers) plus modular standard extensions — **M** (multiply/divide), **A** (atomics), **F**/**D** (single/double float), **C** (16-bit compressed encodings), **V** (vector, ratified at v1.0 in **September 2021**), **B** (bit manipulation, Zba/Zbb/Zbc/Zbs ratified November 2021), and hundreds of Z-extensions. The unprivileged ISA was ratified as version 20191213 (December 2019); privileged ISA 1.12 in December 2021. Governance sits with **RISC-V International**, a Swiss non-profit since March 2020, with more than 4,500 members as of 2025. Profiles (RVA22, RVA23) bundle mandatory extension sets so software can target a known baseline.

Why it matters:
- **No licence fee and no per-unit royalty** for the ISA itself. For a hyperscaler shipping tens of millions of control cores, this is real money; for a startup, it removes a negotiation.
- **Freedom to extend.** Custom instructions are legal and encoding space is reserved for them. This is the single biggest technical draw for accelerator companies, which need a control core with domain-specific instructions.
- **Geopolitical neutrality.** China's strategic pivot toward RISC-V from 2023 onward is explicitly about supply-chain independence; Alibaba's DAMO Academy shipped the XuanTie C910 (2019), open-sourced it in 2021, and released the C930 (March 2025) and C950 (5 nm, up to 3.2 GHz, March 2026).

Honest limits as of 2026: the *ecosystem* — validated IP, verification collateral, performance libraries, and above all a track record of high-performance out-of-order implementations — lags Arm by years. RISC-V is unambiguously winning in embedded control cores (billions shipped, mostly invisible inside SSD controllers, radios, GPUs and NPUs) and is credible in specialised compute; the general-purpose server and phone application-processor markets remain contested.

## 2. The high-performance core

### Pipelining

Split instruction execution into stages so one instruction can be in each. Classic five-stage RISC: fetch, decode, execute, memory, writeback. Modern cores use 10–20 stages. Hazards:

- **Structural** — two instructions want the same unit.
- **Data (RAW/WAR/WAW)** — solved by forwarding/bypass networks and, for true dependences, by stalling.
- **Control** — branches. Solved by prediction (below).

Deeper pipelines allow higher clocks but raise the branch-misprediction penalty (the number of cycles of work thrown away, typically 12–20 in a modern core).

### Superscalar issue and out-of-order execution

Fetch and decode several instructions per cycle (4–10 wide in current high-end cores), rename their architectural registers onto a much larger physical register file to eliminate false dependences (WAR/WAW), dispatch them into **reservation stations** / issue queues, execute them **as soon as their operands are ready** (not in program order), and retire them **in order** from a **reorder buffer (ROB)**.

The ROB is the mechanism that reconciles out-of-order execution with the precise-exception guarantee software depends on: results are held speculatively and only committed to architectural state at retirement, in program order. If an exception or misprediction is detected, everything after the offending entry is squashed. Modern high-end cores have ROBs of several hundred entries (Apple's M-series and Intel's recent P-cores are in the 500–700 range), with load and store queues, physical register files and issue queues scaled to match — this whole set of structures is what "core width" really means, and each grows superlinearly in power.

**Memory disambiguation** (may this load bypass that store?) is speculative too, with predictors deciding when to gamble.

### Branch prediction

The single highest-leverage structure in a modern core. State of the art is **TAGE** (TAgged GEometric history length) — multiple tables indexed by hashes of the program counter with geometrically increasing history lengths, with a tag-match arbitration — often combined with a perceptron-based predictor for linearly-separable correlations. Accuracy on real code is 97–99.5%; at 2% misprediction and a 15-cycle penalty a 5-wide core loses a large fraction of its potential IPC, which is why the last percent matters enormously.

Also present: **branch target buffers** (BTB, often multi-level and thousands of entries), **indirect branch predictors** (ITTAGE) for virtual calls and jump tables, **return address stacks**, and **loop predictors**.

> ⚠️ Speculation is a security surface. Spectre (2018) and its successors exploit the fact that squashed speculative execution still leaves microarchitectural traces (cache state, port contention). Mitigations — speculation barriers, cache partitioning, restricting cross-domain branch-predictor training — cost real performance, and this class of vulnerability is now a standing architectural design constraint.

### Caches and coherence

Typical modern hierarchy:

| Level | Size | Latency | Notes |
|---|---|---|---|
| L1I / L1D | 32–192 KB each per core | 3–5 cycles | Virtually indexed, physically tagged; latency-critical |
| L2 | 512 KB–4 MB per core | 12–20 cycles | Often the coherence point for the core cluster |
| L3 / LLC | 8–128 MB+ shared | 30–60 cycles | Sliced, distributed on a ring or mesh |
| Extra | e.g. AMD 3D V-Cache stacked SRAM | | Hybrid-bonded SRAM die on top of the CCD |

**Coherence protocols**: MESI (Modified/Exclusive/Shared/Invalid) and its extensions MOESI (adds Owned — a dirty line that may be shared, avoiding a writeback) and MESIF (adds Forward — designates one sharer to respond). Implementation styles: **snooping** (broadcast, fine for small counts, bandwidth-hostile beyond ~16 agents) versus **directory-based** (a directory tracks sharers; scales to hundreds of cores at the cost of an indirection). Every many-core server chip is directory-based. Arm's CHI and AMBA ACE, and the CCIX/CXL family, standardise coherent interconnect between chips.

**CXL** (Compute Express Link, on the PCIe physical layer) extends coherence off-package: CXL.io (PCIe-equivalent), CXL.cache (device caching host memory), CXL.mem (host accessing device-attached memory). Its main practical use in 2026 is memory expansion and pooling in servers.

### The memory wall

Core speed has outrun DRAM latency for thirty years: a last-level-cache miss to DRAM is 60–100 ns, i.e. 200–400 core cycles. Architecture's answer is not lower latency (DRAM latency has barely improved since the 1990s) but **latency tolerance**: deep out-of-order windows, aggressive prefetching (stride, stream, and increasingly ML-guided), simultaneous multithreading, and — in throughput machines — thousands of resident threads (GPUs).

## 3. Memory technologies with real numbers

| Standard | Data rate | Bus | Bandwidth | Use |
|---|---|---|---|---|
| DDR5 | 4,000–6,400 MT/s base; spec to 8.8 GT/s | 2 × 32-bit subchannels per DIMM | 32.0–70.4 GB/s per module | Servers, desktops. JEDEC 14 July 2020, 1.1 V, burst length 16 |
| LPDDR5 / LPDDR5X | LPDDR5 released February 2019; LPDDR5X extends to ~8,533 MT/s and beyond | 16-bit channels, many in parallel | e.g. Apple M5: 153.6 GB/s | Phones, laptops, and increasingly AI edge |
| GDDR6 / GDDR6X / GDDR7 | GDDR7 uses PAM3 signalling at ~32 Gbps/pin | 32-bit per device | ~1.8 TB/s on a 384-bit GDDR7 card | Consumer GPUs |
| HBM3E | 9.8 GT/s, 16-Hi, up to 48 GB/stack | 1024-bit | up to ~1.2 TB/s per stack | AI accelerators, from May 2023 |
| HBM4 | 8 GT/s | **2048-bit** (doubled) | ~2.05 TB/s per stack, 16–64 GB | JESD270-4, April 2025 |

HBM is DRAM stacked 8–16 dies high with through-silicon vias over a base logic die, placed millimetres from the compute die on an interposer. Its whole reason for existing is that you cannot get terabytes per second through a package's edge pins at tolerable power; a very wide, very short, comparatively slow bus wins on energy per bit. Suppliers: SK Hynix (which shipped the first 12-layer HBM3E in September 2024), Samsung and Micron. HBM4's move to a 2048-bit interface also moves the base die toward a *logic* process — TSMC fabricates base dies for HBM makers — which blurs the line between memory and logic vendors.

**Market note (dated):** HBM demand crowded out commodity DRAM capacity through 2025–2026; some DRAM categories rose more than 200% in price between early 2025 and early 2026. Micron reached a US$1 trillion market capitalisation on 26 May 2026 on the back of it.

## 4. Interconnect and NoC

Beyond about eight agents, buses and crossbars stop scaling and a **network-on-chip** is used. Topologies: ring (Intel's LLC ring, simple and low-latency at modest scale), 2D mesh (Intel's server mesh, Arm CMN, and most many-core designs), crossbar (small clusters), and torus/dragonfly at the rack scale.

NoC design parameters: flit width, virtual channels (needed to avoid protocol deadlock when multiple message classes share links), routing algorithm (dimension-order XY routing is deadlock-free and cheap; adaptive routing needs escape channels), buffering and flow control (credit-based), and quality-of-service classes. Arteris and Arm sell NoC IP; large SoC teams frequently build their own, and NoC topology is one of the first floorplan-coupled decisions (`03`).

## 5. Chiplets and advanced packaging

The reticle limit (26 × 33 mm ≈ 858 mm² for standard fields; halved to 26 × 16.5 mm for High-NA EUV, `06`) is a hard ceiling on monolithic die size. Yield gives a softer one: defect density × area means a 800 mm² die at a given D0 yields far worse than four 200 mm² dies. Chiplets attack both.

**The economics.** Split an SoC into chiplets and you (a) raise yield per die, (b) can build each function on its optimal node — logic on N3, IO and analog on N6 where they scale poorly anyway, (c) can reuse a chiplet across a product family, amortising its NRE, and (d) can exceed reticle area. You pay in interconnect energy, latency, packaging cost, test complexity (known-good-die testing becomes essential) and thermal density.

**AMD is the proof case**: from Zen 2 (2019) onward, CPU core dies (CCDs) on the leading node pair with an IO die (IOD) on a mature node. NVIDIA's B100/B200 uses two reticle-limit GB100 dies joined by the 10 TB/s NV-HBI link with full cache coherence, presenting as one logical GPU. Intel's Meteor Lake and successors use Foveros to stack compute, graphics, SoC and IO tiles.

### The packaging technologies

| Technology | Owner | What it is |
|---|---|---|
| **CoWoS-S** | TSMC | Chip-on-Wafer-on-Substrate with a **silicon interposer**; the workhorse for GPU+HBM. Interposer area now exceeds 3× reticle in the largest variants |
| **CoWoS-R** | TSMC | Organic RDL interposer — cheaper, lower density |
| **CoWoS-L** | TSMC | Local silicon interconnect bridges embedded in an RDL layer — combines silicon-grade density where needed with organic economics elsewhere; the direction of travel for the largest packages |
| **InFO** | TSMC | Integrated Fan-Out, wafer-level RDL without an interposer; used in Apple's A-series packages |
| **SoIC** | TSMC | Front-end 3D stacking with **hybrid bonding** (no microbumps) — used for AMD 3D V-Cache |
| **EMIB** | Intel | Embedded Multi-die Interconnect Bridge — a small silicon bridge embedded in the organic substrate; avoids a full interposer |
| **Foveros / Foveros Direct** | Intel | 3D die stacking on an active or passive base die; Foveros Direct moves to hybrid bonding |
| **Hybrid bonding** | Industry-wide (also from Xperi/Adeia IP) | Direct copper-to-copper and oxide-to-oxide bonding with no solder. Pitch scales from ~9 µm today toward sub-1 µm, versus 40–55 µm for microbumps. This is the enabling technology for genuine 3D logic and for HBM beyond 16-Hi |

**CoWoS capacity has been the binding constraint on AI accelerator supply since 2023** — more so than wafer capacity. TSMC has repeatedly announced capacity doublings; see `08`.

### UCIe

The **Universal Chiplet Interconnect Express** consortium (Intel, AMD, Arm, TSMC, Samsung, ASE, Google, Meta, Microsoft, Qualcomm and others, formed March 2022) standardises the die-to-die interface: a physical layer, a die-to-die adapter, and a protocol layer that carries PCIe, CXL or a raw streaming protocol. Two package classes are defined: **standard package** (organic substrate, coarse bump pitch, longer reach, lower bandwidth density) and **advanced package** (silicon bridge or interposer, fine pitch, very high bandwidth density at low energy per bit).

> ⚠️ Specific UCIe figures (lane rates, bump-pitch ranges, GB/s per mm, pJ/bit, latency) could not be verified from a primary source in this pass — the consortium page did not resolve. Treat any such numbers as `needs-verification`. What can be stated with confidence: UCIe's purpose is an *open* die-to-die standard so that chiplets from different vendors can be composed, and as of 2026 the open multi-vendor chiplet marketplace it envisages has not materialised — nearly all shipping chiplet systems are single-vendor.

## 6. GPUs and the SIMT model

A GPU is a throughput machine: many simple cores, enormous register files, no large caches relative to compute, and latency hidden by thread oversubscription rather than by speculation.

**SIMT (single instruction, multiple threads)** is NVIDIA's term for the execution model: threads are grouped into **warps** of 32 (AMD: **wavefronts** of 32 or 64) that share an instruction stream. Divergence — different threads in a warp taking different branch paths — is handled by masking and serialising the paths, so branchy code wastes lanes. This is the single most important thing to know when writing GPU code.

Structure of a modern NVIDIA GPU: Streaming Multiprocessors (SMs), each with FP32/INT32 lanes, tensor cores, a large register file (256 KB per SM class), shared memory/L1 (128–256 KB), warp schedulers, and a load/store unit. Above the SMs: L2 cache (tens of MB), memory controllers to HBM, NVLink for scale-out, and (from Hopper onward) a thread-block cluster level in the programming model.

**Tensor cores / matrix units.** Dedicated hardware for small matrix multiply-accumulate — for example a 16×8×16 MMA in one instruction — with mixed precision (FP16/BF16 inputs, FP32 accumulate; then FP8, and in Blackwell FP4 with microscaling formats). The efficiency argument is simple: a matrix unit amortises one instruction fetch, decode and register access over hundreds of MACs, so energy per MAC falls by an order of magnitude versus scalar SIMD. AMD's equivalent is the Matrix Core; Apple, Arm (SME) and Intel (AMX) all have variants.

**The CUDA moat** (see `07`) is not the hardware; it is fifteen years of libraries (cuBLAS, cuDNN, CUTLASS, NCCL, TensorRT), a compiler toolchain, and every framework's default path. AMD's ROCm and the Triton/OpenAI compiler route are the credible challenges.

## 7. NPUs and domain-specific accelerators

**NPU** in a phone or laptop SoC means a low-precision (INT8/INT4, increasingly FP8) matrix engine with a large local SRAM scratchpad and a DMA engine, tuned for energy per inference rather than peak throughput. Apple's Neural Engine, Qualcomm's Hexagon, Arm Ethos, Intel's NPU in Meteor Lake onward. Marketing figures are quoted in TOPS at a stated precision — a number that is close to meaningless without the precision, the sparsity assumption and the achievable utilisation.

**Google TPU** — the longest-running and most successful custom accelerator programme, built with Broadcom:

| Gen | Peak | Memory | Bandwidth | Process | Pod | Year |
|---|---|---|---|---|---|---|
| v1 | 23 TFLOPS | 8 GB DDR3 | 34 GB/s | 28 nm | single chip | 2015 |
| v2 | 45 TFLOPS | 16 GB HBM | 600 GB/s | 16 nm | 256 chips | 2017 |
| v3 | 123 TFLOPS | 32 GB HBM | 900 GB/s | 16 nm | 1,024 chips | 2018 |
| v4 | 275 TFLOPS | 32 GB HBM | 1,200 GB/s | 7 nm | 4,096 chips | 2021 |
| v5e | 393 TOPS (int8) | 16 GB HBM | 819 GB/s | — | — | 2023 |
| v5p | 918 TOPS (int8) | 95 GB HBM | 2,765 GB/s | — | — | 2023 |
| v6e "Trillium" | 1,836 TOPS (int8) | 32 GB | 1,640 GB/s | — | 256 chips | 2024 |
| v7 "Ironwood" | 4,614 TFLOPS (fp8) | 192 GB HBM | 7.37 TB/s | — | 256–9,216 chips | 2025 |

The TPU's architectural core is a large **systolic array** — a 2D grid of MAC cells through which weights and activations are pumped, so each operand is fetched from memory once and reused across the array. Chips are connected in a 2D/3D torus with optical circuit switches at pod scale.

**AWS Trainium / Inferentia** — Annapurna Labs designs; Trainium2 systems shipped from late 2024 and Trainium3 was announced at re:Invent in December 2024. Exact per-chip specifications were not verified in this pass (`needs-verification`). Strategic point: Amazon's motivation is the same as Google's — reduce dependence on NVIDIA pricing and secure supply.

**Groq LPU** — a "functionally sliced" deterministic architecture: memory units interleaved with vector and matrix units, no caches, no branch predictors, with the compiler scheduling every cycle statically. First generation on 14 nm, 25 × 29 mm, >1 TeraOp/s per mm² at 900 MHz nominal; the v2 LPU moved to Samsung 4 nm (selected August 2023). All weights live in on-chip SRAM, which is why Groq's token-generation latency is exceptional and its per-model capital cost is high. Funding: US$640 m Series D (August 2024) at a US$2.8 bn valuation; a US$1.5 bn Saudi commitment (February 2025); a further US$650 m round (May 2026); and in December 2025 a reported ~US$20 bn NVIDIA licensing agreement for Groq's inference technology.

**Cerebras** — wafer-scale integration: one die the size of a wafer, avoiding off-chip communication entirely. WSE-1 (August 2019): 1.2 trillion transistors, 400,000 cores, 18 GB SRAM. WSE-2 (April 2021): 2.6 trillion transistors, 850,000 cores, 40 GB SRAM, 20 PB/s memory bandwidth, 220 Pb/s fabric bandwidth, TSMC 7 nm. WSE-3 (March 2024): 4 trillion transistors, 900,000 cores, 5 nm. Funding over US$1.8 bn including a US$1.1 bn Series G in September 2025 at an US$8.1 bn valuation; IPO filed September 2024 and withdrawn October 2025; a >US$10 bn OpenAI compute agreement announced January 2026.

**The general lesson.** Every one of these accelerators makes the same three trades: reduce precision, replace general control with static scheduling or fixed dataflow, and move memory closer to compute. They win 10–100× in energy per operation on the workload they were built for, and are useless outside it. That is the post-Dennard bargain.

## Open questions

- UCIe quantitative specifications unverified (`needs-verification`).
- AWS Trainium2/3 and Microsoft Maia per-chip specifications unverified.
- Specific L1/L2/ROB sizes for current Apple, Intel and AMD cores are from architectural disclosures and third-party analysis rather than datasheets; ranges given rather than point values.
- NVIDIA Rubin (announced March 2026) specifications not verified in this pass.

## Sources

- [RISC-V — Wikipedia](https://en.wikipedia.org/wiki/RISC-V) — accessed 2026-08-25
- [High Bandwidth Memory — Wikipedia](https://en.wikipedia.org/wiki/High_Bandwidth_Memory) — accessed 2026-08-25
- [DDR5 SDRAM — Wikipedia](https://en.wikipedia.org/wiki/DDR5_SDRAM) — accessed 2026-08-25
- [Blackwell (microarchitecture) — Wikipedia](https://en.wikipedia.org/wiki/Blackwell_(microarchitecture)) — accessed 2026-08-25
- [Tensor Processing Unit — Wikipedia](https://en.wikipedia.org/wiki/Tensor_Processing_Unit) — accessed 2026-08-25
- [Cerebras — Wikipedia](https://en.wikipedia.org/wiki/Cerebras) — accessed 2026-08-25
- [Groq — Wikipedia](https://en.wikipedia.org/wiki/Groq) — accessed 2026-08-25
- [Chiplet — Wikipedia](https://en.wikipedia.org/wiki/Chiplet) — accessed 2026-08-25
- [Chip Scale Package — Wikipedia](https://en.wikipedia.org/wiki/Chip_Scale_Package) — accessed 2026-08-25

