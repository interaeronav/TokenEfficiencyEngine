---
id: semi.rtl
title: Digital design and RTL — from abstraction stack to signoff-ready netlist
domain: 27_semiconductors_and_chip_design
tags: [rtl, verilog, systemverilog, vhdl, chisel, synthesis, static-timing-analysis, cdc, dft, scan, atpg, formal-verification, uvm, fpga, yosys, openlane, skywater]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Universal Verification Methodology", url: "https://en.wikipedia.org/wiki/Universal_Verification_Methodology", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "OpenROAD Project", url: "https://en.wikipedia.org/wiki/OpenROAD_Project", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Tiny Tapeout FAQ", url: "https://tinytapeout.com/faq/", publisher: "Tiny Tapeout", accessed: 2026-08-25}
  - {title: "SkyWater Technology", url: "https://en.wikipedia.org/wiki/SkyWater_Technology", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "RISC-V", url: "https://en.wikipedia.org/wiki/RISC-V", publisher: "Wikipedia", accessed: 2026-08-25}
related: [semi.physical_design, semi.architecture, semi.career, semi.resources]
---

# Digital design and RTL — from abstraction stack to signoff-ready netlist

**Summary.** A modern SoC is described in a few million lines of register-transfer-level code, verified with an effort roughly twice that of writing it, and mechanically transformed into gates by a synthesis tool. This file covers the abstraction stack, the hardware description languages and their honest trade-offs, the practices that actually keep large RTL projects alive (clock-domain crossing discipline, timing closure feedback, design-for-test built in from the start), the verification methods (constrained-random UVM, formal property checking, emulation), and the open-source flow — Yosys, OpenROAD, OpenLane, the SkyWater 130 nm PDK and Tiny Tapeout — which since 2020 has made real, physically-fabricated silicon accessible to an individual for a few hundred dollars.

## Key facts

| Item | Value | Note |
|---|---|---|
| Verification share of SoC engineering effort | Typically 60–70% | Industry rule of thumb; ratio of verification to design engineers commonly 2:1 to 3:1 |
| UVM standard | IEEE 1800.2-2020, approved 14 September 2020 | UVM 1.0 approved by Accellera 21 February 2011, derived from OVM 2.1.1 |
| SystemVerilog standard | IEEE 1800 (current revision 1800-2023) | Merged design + assertion + verification language |
| VHDL standard | IEEE 1076 (current revision 1076-2019) | |
| Verilog | IEEE 1364, last standalone revision 1364-2005 | Now folded into IEEE 1800 |
| Tiny Tapeout tile | ~160 × 100 µm ≈ 1,000 digital gates | 8 inputs, 8 outputs, 8 bidirectional pins; ≥50 MHz guaranteed |
| Tiny Tapeout default PDK | Open-source SkyWater SKY130 (also IHP and GlobalFoundries shuttles) | Silicon back in 6–9 months; full fulfilment up to ~1 year |
| OpenROAD | Launched 2018 under DARPA IDEA; BSD-licensed; led by UC San Diego | RTL-to-GDSII, no-human-in-loop target of 24 h |
| OpenROAD supported PDKs | SkyWater 130 nm, GF 12LP, GF 65 nm, Intel 22 nm FinFET, ASAP7 predictive | Over 80 SkyWater shuttle tape-outs in CI |
| RISC-V governance | RISC-V International, Swiss non-profit since March 2020; 4,500+ members (2025) | Unprivileged ISA ratified 20191213; privileged 1.12 (Dec 2021); Vector 1.0 (Sep 2021) |

## 1. The abstraction stack

| Level | Description | Typical artefact |
|---|---|---|
| Architecture | ISA, pipeline depth, cache hierarchy, bandwidth budgets | Spec docs, C/C++ or Python performance model, cycle-approximate SystemC |
| Micro-architecture | Block diagrams, state machines, pipeline stages, interfaces | Micro-architecture specification |
| RTL | Cycle-accurate synthesisable description | SystemVerilog / VHDL / Chisel |
| Gate level | Netlist of standard cells | Verilog netlist + SDF timing |
| Transistor level | SPICE, custom analog and memory | SPICE netlist |
| Physical | Placed, routed polygons | DEF, GDSII/OASIS |

The discipline to hold onto: **each level must be equivalent to the one above**, and the industry proves it with formal equivalence checking (RTL↔netlist, netlist↔post-ECO netlist) rather than simulation. Simulation checks *behaviour*; equivalence checking checks *identity*.

## 2. Hardware description languages

### Verilog and SystemVerilog

Verilog (1984, Gateway Design Automation; IEEE 1364 from 1995) is the industry default. **SystemVerilog** (IEEE 1800) subsumes it and adds three separable things:

1. **Design constructs** — `logic` (replacing the reg/wire confusion), packed/unpacked arrays, `always_ff` / `always_comb` / `always_latch` (which make synthesis intent explicit and let tools error on mismatch), interfaces and modports, packages, enums, structs.
2. **Assertions (SVA)** — temporal properties (`assert property (@(posedge clk) req |-> ##[1:3] ack);`) usable both in simulation and by formal tools.
3. **Verification constructs** — classes, randomisation with constraints, coverage groups, mailboxes/semaphores. These are *not* synthesisable and exist to build testbenches.

Practical RTL rules that survive every code review:
- One `always_ff` block per register group, non-blocking assignments (`<=`) only; blocking (`=`) only inside `always_comb`.
- No latches. Fully specify combinational assignments or use `always_comb` with a default.
- Register all module outputs at block boundaries where feasible; it makes timing budgets composable.
- No `#delay` in synthesisable code.
- Reset strategy declared once, project-wide: asynchronous-assert/synchronous-deassert is the common compromise; pure synchronous reset saves area on flops that support it.

### VHDL

IEEE 1076, strongly typed, verbose, Ada-derived. Still dominant in European aerospace and defence, in much FPGA work, and anywhere the strong typing is valued as a defect filter. `std_logic` with its nine-valued logic captures drive strength and unknowns explicitly. A team is productive in either; mixed-language flows are routine and every major simulator supports both.

### Chisel, SpinalHDL, Amaranth — hardware construction languages

Chisel (Berkeley, embedded in Scala) and SpinalHDL (also Scala) and Amaranth (Python) are **generators**: you write a program that *elaborates* to a circuit, emitting Verilog. The win is parameterisation and type-safe composition — Berkeley's Rocket and BOOM RISC-V cores, and SiFive's product line, are Chisel. The cost is a second toolchain, an emitted-Verilog debug indirection, and a much smaller hiring pool. Verdict for a learner: worth knowing that it exists and why; not the first thing to learn.

### High-level synthesis (HLS) — the honest answer

HLS (Siemens Catapult, AMD/Xilinx Vitis HLS, Cadence Stratus, Intel HLS) compiles C/C++/SystemC to RTL, with pragmas controlling pipelining, unrolling and array partitioning. Where it genuinely works: dataflow-heavy, arithmetic-dense, control-light blocks — video codecs, image pipelines, DSP, some ML kernels — especially on FPGAs where the area penalty is affordable. Where it does not: control-dominated logic, anything with tight cycle-level interface contracts, anything where the last 15% of area or frequency matters. HLS does not remove the need to think in hardware; it removes the need to *type* in hardware, and it moves the hard part to constraining and verifying the generated microarchitecture. It has been "about to replace RTL" since roughly 2005 and has not.

## 3. RTL design practice

**Partitioning.** Blocks are drawn along clock-domain, power-domain and physical-hierarchy lines simultaneously, because a partition that is clean in one and messy in another will be re-drawn during physical design at great cost. Aim for blocks in the 100k–1M gate range for physical implementation.

**Interfaces.** Standardise on AMBA (AXI4 / AXI4-Lite / AXI-Stream / AHB / APB) or equivalent (TileLink in the RISC-V world, Wishbone in the open-source world, and Wishbone or a simple 8-bit bus in student projects). Ready/valid handshaking with no combinational path from `ready` to `valid` in the same direction is the single most common source of both deadlock bugs and timing failures.

**Parameterisation.** Widths, depths and feature-enables as parameters, with `generate` blocks. Assertions on parameter legality.

**Coding for timing.** Retiming and pipelining decisions belong in RTL, not in synthesis. If a path needs three cycles, write three cycles.

**Coding for power.** Explicit clock enables (which the tool converts to clock gating), operand isolation on wide datapaths, and memory-enable discipline. Automatic clock gating typically recovers 20–40% of dynamic power on a control-heavy design; sloppy RTL that toggles a 512-bit bus every cycle cannot be rescued downstream.

## 4. Clocks, resets and CDC

Every asynchronous clock-domain crossing is a metastability hazard. Metastability is not eliminable, only made improbable: the figure of merit is **MTBF**, which rises exponentially with the settling time allowed.

Standard structures:
- **Two-flop (or three-flop) synchroniser** — for single-bit level signals only.
- **Pulse synchroniser / toggle synchroniser** — for events.
- **Async FIFO with Gray-coded pointers** — for multi-bit data. Gray coding guarantees single-bit change per increment, so a partially-captured pointer is always either the old or the new value.
- **MCP (multi-cycle path) with handshake** — data held stable while a synchronised request/acknowledge crosses.

> ⚠️ Never pass a multi-bit bus through parallel two-flop synchronisers. Different bits will resolve on different cycles and produce values that never existed.

**CDC verification is a separate tool class** (Synopsys SpyGlass CDC / VC SpyGlass, Cadence Conformal CDC, Siemens Questa CDC). It performs structural analysis (does every crossing have a recognised synchroniser?) plus functional checks (are the source signals stable long enough?). CDC bugs are the classic silicon-respin cause because they are timing-dependent, temperature-dependent and effectively invisible in RTL simulation, where everything is deterministic. Reset-domain crossing (RDC) analysis is the newer companion discipline.

## 5. Synthesis

Logic synthesis maps RTL to a technology library subject to constraints. Tools: Synopsys Design Compiler and Fusion Compiler, Cadence Genus, Siemens Oasys; Yosys in open source.

Inputs: RTL, the standard-cell `.lib` (Liberty) timing/power characterisation, and an **SDC** (Synopsys Design Constraints) file. The SDC is where a design lives or dies:

```
create_clock -name clk -period 1.25 [get_ports clk]      # 800 MHz
set_input_delay  -clock clk 0.35 [all_inputs]
set_output_delay -clock clk 0.30 [all_outputs]
set_clock_uncertainty 0.06 [get_clocks clk]
set_false_path -from [get_clocks clkA] -to [get_clocks clkB]
set_multicycle_path 2 -setup -from [get_pins ...]
```

Phases: elaboration → generic (technology-independent) optimisation → technology mapping → incremental optimisation (gate sizing, buffering, restructuring, Vt swapping). Modern flows are **physically aware**: synthesis places cells coarsely so wire-load estimates reflect reality, because at 7 nm and below interconnect delay dominates and a purely wire-load-model synthesis is worthless.

Outputs: a gate-level netlist, an estimated timing report, and area/power estimates that a physical-design team will treat as optimistic by 10–20%.

## 6. Static timing analysis

STA checks every path exhaustively without vectors. Two fundamental checks:

- **Setup**: data must arrive before the capture edge minus setup time.
  `T_launch + T_cq + T_logic + T_wire ≤ T_period + T_skew − T_setup − T_uncertainty`
- **Hold**: data must not arrive *too early* and corrupt the current capture.
  `T_cq + T_logic_min + T_wire_min ≥ T_skew + T_hold`

**Slack** = required arrival − actual arrival. Negative slack is a violation. Two crucial asymmetries: setup violations can be fixed by slowing the clock; **hold violations cannot** — they are frequency-independent and must be fixed with buffer insertion, so a hold violation discovered after tapeout is fatal.

**Corners and modes.** Timing is signed off across **PVT corners** — process (slow/typical/fast, and increasingly separate SS/FF for N and P), voltage (nominal ±10%, plus low-Vdd DVFS points), temperature (e.g. −40 °C, 25 °C, 125 °C) — crossed with RC extraction corners (Cmin/Cmax/RCmin/RCmax/typ) and functional modes (mission, scan-shift, scan-capture, low-power). At advanced nodes this yields dozens to low hundreds of scenarios, run in **MMMC** (multi-mode multi-corner) analysis. Note **temperature inversion**: below roughly 0.8 V, cold silicon can be *slower* than hot, so the worst corner is not always the hot one.

**OCV/AOCV/POCV.** On-chip variation derating evolved from a flat percentage, to distance- and depth-dependent (AOCV), to statistical parametric (POCV/SOCV) using sigma-based cell delay distributions — the only tractable approach below 16 nm.

Tools: Synopsys PrimeTime (the signoff reference), Cadence Tempus, Siemens; OpenSTA in open source.

## 7. Design for test

Silicon is not tested by running software; it is tested by controlling and observing every flip-flop.

- **Scan chains.** Every flop is replaced by a scan flop with a test multiplexer, and the flops are stitched into shift registers. In test mode you shift in a state, pulse the functional clock once (capture), and shift out the result. Cost: ~5–8% area and a small timing penalty; benefit: near-total controllability.
- **ATPG (automatic test pattern generation).** Tools (Synopsys TestMAX/TetraMAX, Siemens Tessent, Cadence Modus) generate patterns for fault models: **stuck-at** (>99% coverage expected), **transition/at-speed delay** (85–95%), **path delay**, **bridging** and **cell-aware** faults. Cell-aware ATPG, which models defects *inside* standard cells from their layout, has become standard at advanced nodes.
- **Compression.** Raw scan data volume is unaffordable; on-chip decompressors/compactors (EDT, DFTMAX) give 50–200× compression, trading a little coverage for tester time and memory.
- **BIST.** **MBIST** for embedded memories (march algorithms, with built-in repair via redundant rows/columns and fuse programming) is universal — memories occupy the majority of die area and have their own defect modes. **LBIST** (logic BIST with pseudorandom patterns and a MISR signature) is used where in-field self-test is required, notably ISO 26262 automotive designs.
- **Boundary scan** — IEEE 1149.1 (JTAG) for board-level interconnect test, and IEEE 1687 (IJTAG) for accessing embedded instruments.
- **DFT is not a back-end afterthought.** Test-mode clocking, scan-enable timing, and chain balancing must be planned at RTL and floorplan time.

## 8. Formal verification

Two distinct activities share the name:

- **Equivalence checking (LEC/FEV)** — proves two netlists implement the same function. Mandatory at every transformation: RTL→synthesis, pre→post scan insertion, pre→post ECO. Tools: Synopsys Formality, Cadence Conformal.
- **Model checking / property checking** — proves that SVA assertions hold for *all* reachable states, or produces a counterexample trace. Tools: Cadence JasperGold, Synopsys VC Formal, Siemens Questa PropCheck; SymbiYosys/Yosys-SMTBMC in open source.

Where formal wins decisively: arbiters and round-robin fairness, FIFO and memory controllers, cache coherence protocols, register-file/CSR maps (auto-generated proofs from the register spec), FSM deadlock and unreachable-state checks, arithmetic datapath equivalence, security properties (this key register is never readable from this bus master), and connectivity checks on a top-level with thousands of ports. Where it fails: anything with deep sequential state and wide datapaths — state explosion is real, and "inconclusive after 12 hours" is a common outcome. Practically, formal replaces simulation for control logic and *complements* it everywhere else.

## 9. Simulation-based verification and UVM

**UVM** is a SystemVerilog class library, standardised as **IEEE 1800.2-2020** (approved 14 September 2020), derived from OVM 2.1.1 (Cadence + Mentor, 2007), which descended from Verisity's eRM (2001). Accellera approved UVM 1.0 on 21 February 2011.

The structure, top to bottom:

- **Test** — selects the configuration and the sequences to run.
- **Environment** — instantiates agents, scoreboards, coverage collectors.
- **Agent** — per-interface bundle; *active* agents drive, *passive* agents only observe.
  - **Sequencer** — arbitrates sequence items.
  - **Driver** — converts abstract transactions into pin wiggles.
  - **Monitor** — reconstructs transactions from pin activity and publishes them on an analysis port.
- **Scoreboard** — compares observed output transactions against a reference model's prediction.
- **Coverage collector** — functional coverage groups.
- Supporting infrastructure: the factory (type/instance overrides), the configuration database (`uvm_config_db`), phases (build/connect/run/report), objections, and the reporting system.

**Constrained-random verification** is the method: generate legal-but-unexpected stimulus under constraints, check with a reference model, and measure progress with **functional coverage** (did we hit the interesting scenarios?) and **code coverage** (line, branch, toggle, FSM, condition). Signoff is a coverage closure argument, not a test-count argument. A large SoC's regression is millions of simulation-hours across a compute farm.

**Portable Stimulus (Accellera PSS)** targets the reuse of test intent from block simulation up to emulation and post-silicon.

## 10. FPGA prototyping and emulation

Simulation runs a big SoC at roughly 1–100 Hz of virtual clock. Booting an OS is therefore impossible in simulation. Three faster options:

| Method | Speed | Compile time | Debug visibility | Cost |
|---|---|---|---|---|
| RTL simulation | 1–100 Hz | Minutes | Total | Licence only |
| Hardware emulation (Cadence Palladium, Siemens Veloce, Synopsys ZeBu) | 0.5–5 MHz | Hours | Very high (full-visibility waveform capture) | Millions of USD |
| FPGA prototyping (Synopsys HAPS, S2C, custom boards) | 10–100 MHz | Many hours–days | Limited | Hundreds of thousands |

Emulation is where firmware, drivers and OS bring-up happen months before tapeout; it is also where power estimation on real workloads is done. FPGA prototyping is where software teams get a fast-enough platform to develop against. Both require the design to be partitioned across multiple devices and the memories and clock trees to be remapped — non-trivial engineering in itself.

## 11. The open-source flow — genuinely usable

This is the most consequential change in accessibility since the 1990s.

- **Yosys** — open synthesis framework (Claire Wolf/YosysHQ), with ABC for technology mapping. Handles a large subset of SystemVerilog synthesisable constructs; the commercial **Yosys/Tabby CAD** adds fuller SystemVerilog and formal.
- **OpenROAD** — RTL-to-GDSII, launched **2018** under DARPA's IDEA programme (initiated by Andreas Olofsson to attack the design-cost crisis), led by UC San Diego, BSD-licensed. The stated goal is a 24-hour, no-human-in-the-loop flow. Components: RePlAce (global placement), TritonMacroPlace and RTL-MP (macro placement/floorplanning), TritonCTS 2.0 (clock tree), FastRoute (global route), TritonRoute (detailed route with DRC), OpenSTA (timing), OpenRCX (extraction), AutoTuner (ML hyperparameter search), all over the shared **OpenDB** database built on LEF/DEF.
- **OpenLane / OpenLane 2** — the packaged ASIC flow on top of OpenROAD used for the Google/SkyWater and Efabless shuttles.
- **SkyWater SKY130** — the first genuinely open PDK for a real commercial process (SkyWater Technology, Bloomington, Minnesota; a 130 nm process on 200 mm wafers). Open design rules, open standard-cell libraries, open SPICE models. GlobalFoundries opened GF180MCU (180 nm) in 2022, and IHP (Germany) released an open 130 nm SiGe BiCMOS PDK.
- **Verilator** — a cycle-accurate Verilog-to-C++ compiler; the fastest open simulator by a wide margin and the practical choice for RISC-V core development. **Icarus Verilog** for event-driven simulation, **cocotb** for Python testbenches, **GTKWave**/**Surfer** for waveforms.
- **Tiny Tapeout** — see `09`. A shared tile on a multi-project wafer, ~160 × 100 µm (≈1,000 gates) with 8 in / 8 out / 8 bidirectional pins and ≥50 MHz guaranteed, submitted through a GitHub Actions flow that runs OpenLane. Silicon returns in 6–9 months, full fulfilment within about a year, and the participant receives a chip plus a development board.

What the open flow cannot do (state this honestly): it has no signoff-quality parasitic extraction or STA for advanced nodes, no commercial-grade DRC/LVS sign-off decks, no ATPG, no advanced-node PDKs, and no support contract. It is superb for learning, research, small mixed-signal and educational tapeouts, and it is not a substitute for a Synopsys or Cadence flow on a product at 5 nm.

## Open questions

- Efabless' operating status after 2025 could not be verified in this pass (its Wikipedia page was not retrievable); Tiny Tapeout's own FAQ was also unreachable directly and its figures here come from a cached retrieval. Treat the Efabless-specific claims in `09` as `needs-verification`.
- The 60–70% verification-effort figure is a widely repeated industry rule of thumb (Wilson Research/Siemens functional verification study), not verified against a primary source in this pass.

## Sources

- [Universal Verification Methodology — Wikipedia](https://en.wikipedia.org/wiki/Universal_Verification_Methodology) — accessed 2026-08-25
- [OpenROAD Project — Wikipedia](https://en.wikipedia.org/wiki/OpenROAD_Project) — accessed 2026-08-25
- [Tiny Tapeout FAQ](https://tinytapeout.com/faq/) — accessed 2026-08-25
- [SkyWater Technology — Wikipedia](https://en.wikipedia.org/wiki/SkyWater_Technology) — accessed 2026-08-25
- [RISC-V — Wikipedia](https://en.wikipedia.org/wiki/RISC-V) — accessed 2026-08-25
