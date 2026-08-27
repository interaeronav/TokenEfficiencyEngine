---
id: semi.career
title: Getting into chip design — education, skills, free routes and the career ladder
domain: 27_semiconductors_and_chip_design
tags: [career, education, rtl-jobs, verification-jobs, physical-design-jobs, dft, analog-design, nand2tetris, hdlbits, tinytapeout, openlane, fpga, interviews, career-ladder]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Tiny Tapeout", url: "https://tinytapeout.com/", publisher: "Tiny Tapeout", accessed: 2026-08-25}
  - {title: "Tiny Tapeout FAQ", url: "https://tinytapeout.com/faq/", publisher: "Tiny Tapeout", accessed: 2026-08-25}
  - {title: "OpenROAD Project", url: "https://en.wikipedia.org/wiki/OpenROAD_Project", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "SkyWater Technology", url: "https://en.wikipedia.org/wiki/SkyWater_Technology", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "RISC-V", url: "https://en.wikipedia.org/wiki/RISC-V", publisher: "Wikipedia", accessed: 2026-08-25}
related: [semi.rtl, semi.physical_design, semi.resources, semi.economics]
---

# Getting into chip design — education, skills, free routes and the career ladder

**Summary.** Chip design is one of the few remaining engineering fields where the barrier to entry is knowledge rather than capital — since about 2020 an individual can write RTL, run it through a full open-source physical-design flow, submit it to a shared multi-project wafer, and receive working silicon and a development board within a year for the price of a mid-range phone. This file covers the degrees and specialisations that matter, the five hiring tracks and what each actually requires, a complete free learning path, FPGA boards worth buying, the interview process in detail, and the career ladder with honest notes on where the money and the leverage are.

## Key facts

| Item | Value |
|---|---|
| Usual degree | BSc/BEng in electrical engineering, computer engineering or (less commonly) computer science with hardware electives |
| Typical entry point for design/verification roles | MSc is common and often expected at large firms; PhD standard for architecture research and advanced analog |
| Tiny Tapeout tile | ~160 × 100 µm ≈ 1,000 gates; 8 in / 8 out / 8 bidirectional pins; ≥50 MHz guaranteed |
| Tiny Tapeout turnaround | Silicon in 6–9 months; full fulfilment up to ~1 year; participant receives a chip and devkit |
| Tiny Tapeout shuttles open (25 August 2026) | **SKY26c** and **IHP26b** |
| Open PDKs available | SkyWater SKY130, GlobalFoundries GF180MCU, IHP SG13G2 (130 nm SiGe BiCMOS) |
| Open flow | Yosys → OpenLane/OpenROAD → Magic/KLayout → GDSII |
| RISC-V International membership | 4,500+ members (2025) |

## 1. The education

### Undergraduate

**Electrical engineering** or **computer engineering** is the standard route. The courses that matter, in rough order of importance to a hiring manager:

1. **Digital logic design** — Boolean algebra, combinational and sequential design, FSMs, timing.
2. **Computer architecture** — pipelining, caches, memory, ISA. Usually two courses.
3. **Semiconductor devices / solid-state electronics** — you cannot reason about leakage, variation or analog without it.
4. **Analog circuits** — even for a digital engineer: everything about signal integrity, IR drop and IO derives from it.
5. **VLSI design** — CMOS logic families, layout, standard cells, and ideally a course project taken to layout.
6. **Signals and systems, probability** — for anything touching DSP, SerDes or process variation.
7. **Programming** — C, Python and Tcl. Tcl is unglamorous and unavoidable: every EDA tool is scripted in it.

**Computer science alone is a harder route** but not a closed one, particularly into verification (which is software engineering applied to hardware), architecture/performance modelling, and EDA tool development. Fill the gaps with the digital-logic and architecture courses above.

### Graduate specialisations

An MSc is the norm at large employers in most regions, and it is where you choose a track. The specialisations that map onto real job families:

- **Digital VLSI / physical design** — place-and-route, timing closure, low-power design.
- **Verification** — formal methods, constrained-random methodology, coverage.
- **Computer architecture** — the research-heavy track; PhD common. This is where the ISCA/MICRO/HPCA publication route lives.
- **Analog and mixed-signal / RF** — the highest-scarcity, longest-training track. Data converters, PLLs, SerDes, LDOs and bandgaps.
- **Device physics and process integration** — the route into a foundry or an equipment vendor.
- **EDA algorithms** — graph algorithms, SAT/SMT, optimisation. A CS-heavy track that pays well and is genuinely intellectually deep.

### The strong programmes

Not exhaustive, and reputation is a poor proxy for fit — but these have deep, continuous industry pipelines:

- **United States**: UC Berkeley (RISC-V, Chisel, BOOM, ADEPT; the Berkeley Wireless Research Center for analog), MIT, Stanford, University of Michigan, UIUC, Georgia Tech, Carnegie Mellon, UT Austin, UCSD (OpenROAD's home), Purdue (large semiconductor workforce programme), Cornell, Columbia, Arizona State (co-located with TSMC/Intel Arizona).
- **Europe**: ETH Zürich (PULP platform — open RISC-V cores widely used in industry), EPFL, TU Delft, KU Leuven (co-located with imec), TU Munich, RWTH Aachen, Imperial, Cambridge, Politecnico di Torino/Milano.
- **Asia**: NTU/NCTU and NTHU (Taiwan; the TSMC pipeline), KAIST and Seoul National University (Korea), Tokyo, Tsinghua and Peking (China), IIT Madras (home of the Shakti RISC-V programme), IIT Bombay/Delhi/Kharagpur, IISc Bangalore, NUS and NTU Singapore.
- **Elsewhere**: University of Stellenbosch and the University of Cape Town run credible microelectronics groups **[ZA]**; the University of Namibia's engineering faculty does not currently offer a VLSI specialisation, so the practical Namibian route is a South African, European or online-plus-remote-work path **[NA]**.

## 2. The five hiring tracks

| Track | What you actually do | Core skills | Notes |
|---|---|---|---|
| **RTL design** | Write synthesisable SystemVerilog for a block; own its microarchitecture, timing and power | SystemVerilog, microarchitecture, STA literacy, protocols (AXI/AHB), scripting | The most competitive entry track; smallest headcount of the digital roles |
| **Design verification** | Build UVM environments, write constrained-random tests and assertions, close coverage, debug | SystemVerilog/UVM, object-oriented design, SVA, Python, formal | **The largest headcount and the easiest entry.** Software-strong graduates do well. Do not treat it as a lesser role — DV engineers at senior levels are as valued as designers |
| **Physical design / implementation** | Floorplan, place, CTS, route, close timing, signoff | Tcl (heavily), Innovus/Fusion Compiler, PrimeTime, STA, IR/EM, patience | Very hands-on, tool-centric, high demand, often geographically tied to design centres |
| **DFT** | Scan insertion, ATPG, compression, MBIST, JTAG/IJTAG, test-time optimisation | Tessent/TestMAX, fault models, scripting | Chronically short-staffed and therefore a reliable way in |
| **Analog / mixed-signal** | Design amplifiers, converters, PLLs, SerDes, regulators; do your own layout or work closely with a layout engineer | Device physics, Cadence Virtuoso/Spectre, layout, intuition built over years | Highest scarcity, longest apprenticeship, least automatable. If you have the temperament, this is the strongest long-term position in the industry |

Adjacent tracks worth knowing: **architecture/performance modelling** (C++/Python simulators, workload analysis), **CAD/design-methodology engineering** (build and maintain the flow — high leverage, invisible from outside), **process integration and yield** (foundry-side), **applications engineering** (customer-facing at an EDA or IP vendor — an underrated entry route with excellent exposure), and **firmware/embedded** at the hardware/software boundary.

## 3. The free learning route, in order

This is a complete path from nothing to fabricated silicon, using only free or near-free resources.

### Step 1 — Build a computer from a NAND gate: **Nand2Tetris**

Noam Nisan and Shimon Schocken's *The Elements of Computing Systems*. Twelve projects: from NAND to logic gates, to an ALU, to a CPU, to an assembler, VM, compiler and OS. Free on nand2tetris.org, with Coursera courses ("Build a Modern Computer from First Principles", parts I and II). It is not chip design — it uses a toy HDL and a simulator — but it removes the mystery, and completing it is the single best filter for whether you enjoy this work. Two to six weeks.

### Step 2 — Learn real HDL: **HDLBits**

hdlbits.01xz.net — several hundred graded Verilog exercises from a single wire to FSMs and a full CPU datapath, checked by simulation against a reference. Free. This is the fastest way to build actual Verilog fluency, and it is the resource practising engineers most often recommend. Two to eight weeks alongside other work.

### Step 3 — The textbook: **Harris & Harris**

*Digital Design and Computer Architecture* (David Money Harris and Sarah L. Harris) — available in **RISC-V**, ARM and MIPS editions. It takes you from transistors to a working pipelined processor in one coherent narrative, with both Verilog and VHDL throughout. If you buy one book, buy this one. (`10` has the full register.)

### Step 4 — Simulate properly

- **Verilator** — compile Verilog to C++ and run at hundreds of kHz to MHz. The standard for open CPU development.
- **cocotb** — write testbenches in Python. Dramatically lowers the barrier for anyone with software experience.
- **Icarus Verilog** + **GTKWave** or **Surfer** — the simplest event-driven simulate-and-view loop.

Build something with real structure: a UART, an SPI master, a small RISC-V RV32I core (this is the canonical rite of passage — a single-cycle core in a weekend, a pipelined one in a month), a VGA or HDMI generator, an I²S audio path.

### Step 5 — Put it on an FPGA

| Board | Approx. price | Toolchain | Why |
|---|---|---|---|
| **Tang Nano 9K** (Gowin GW1NR-9) | ~US$15–20 | Gowin IDE; open **Apicula** flow | Cheapest serious start; HDMI output |
| **iCEBreaker** / **iCEStick** (Lattice iCE40) | ~US$25–70 | **Fully open**: Yosys + nextpnr + IceStorm | The best board for learning the *open* toolchain end to end |
| **ULX3S** (Lattice ECP5) | ~US$100–160 | Open: Yosys + nextpnr + Project Trellis | Large enough for a Linux-capable RISC-V SoC |
| **Digilent Arty A7** (AMD Artix-7) | ~US$130–250 | Vivado (free WebPACK) | The standard academic board; huge body of tutorials |
| **Digilent Nexys A7** | ~US$270–350 | Vivado | Rich peripherals, common in university labs |
| **Zynq boards** (PYNQ-Z2, Kria KV260) | ~US$150–400 | Vivado/Vitis | ARM cores + FPGA fabric; the hardware/software co-design platform |

> ⚠️ Prices are indicative and move; check current retail. Marked `needs-verification`.

The open Lattice flow (Yosys → nextpnr → bitstream) is worth doing at least once, because it is the same synthesis engine you will use for ASIC work.

### Step 6 — Run the full ASIC flow: **OpenLane + SkyWater**

Install OpenLane 2 (or use the container image), point it at the **SKY130** PDK, and take your Verilog through synthesis, floorplan, placement, CTS, routing, extraction, STA, DRC and LVS to a GDSII. You will meet, in miniature, every problem in `03`: congestion, hold violations, antenna rules, density fill. This is the single highest-value exercise in the whole path, because it makes the abstractions physical.

### Step 7 — Get actual silicon: **Tiny Tapeout**

Tiny Tapeout is the reason this file exists. It buys one die on a multi-project wafer and subdivides it into tiles, so that hundreds of participants share a mask set.

**How it works:**
- You get a **tile of roughly 160 × 100 µm** — about **1,000 digital logic gates** — with a fixed interface of **8 inputs, 8 outputs and 8 bidirectional pins**, plus clock and active-low reset. Larger designs buy multiple tiles.
- Clock speed is **guaranteed to at least 50 MHz**.
- Submission is via a **GitHub template repository**: you push your Verilog and configuration, GitHub Actions runs OpenLane, and the generated GDS is checked automatically. There is a browser-based flow for simple designs and an analog track on some shuttles.
- The default process is the **open-source SkyWater SKY130** PDK; other shuttles have used **IHP** (130 nm SiGe BiCMOS, which supports analog and RF) and **GlobalFoundries** processes.
- **Turnaround: 6–9 months to silicon**, up to about a year including PCB assembly, test and fulfilment.
- Each participant receives **a chip and a devkit** — a demo board plus a breakout board carrying the ASIC — so you can physically run your own silicon.
- As of **25 August 2026** the open shuttles are **SKY26c** and **IHP26b**.

**Cost.** Pricing depends on tile count, shuttle and whether the design is analog or digital, and is quoted through Tiny Tapeout's own calculator; early-bird pricing is available once per person. Historically a single digital tile has been in the low hundreds of US dollars. Treat any specific figure as `needs-verification` and check the calculator at submission time.

**Why it matters for a career.** "I have a chip I designed, here it is, here is the test bench, here is what I got wrong on the first spin" is an interview answer almost no other candidate can give. It also teaches the one lesson simulation cannot: silicon is final. There is no patch.

**The wider open-silicon shuttle context.** The Google/SkyWater open MPW programme, run through **Efabless** with the **Caravel** harness, was the origin of this ecosystem and produced dozens of open tapeouts from 2020 onward; OpenROAD's continuous-integration suite carries **over 80 SkyWater shuttle designs**. Efabless' current operating status could not be verified in this research pass (`needs-verification`) — check before planning around it. Note also that **SkyWater itself agreed on 26 January 2026 to be acquired by IonQ for US$1.8 bn**, which makes the long-term future of the SKY130 shuttle programme worth checking rather than assuming.

Other routes to silicon: university MPW programmes (**Europractice** for European academics, **CMP** in Grenoble, **TSMC CyberShuttle** through a university), and **Muse Semiconductor** for low-cost TSMC shuttle access in the US.

### Step 8 — Contribute to open hardware

The open RISC-V ecosystem is a genuine hiring signal: **CVA6/CV32E40P** (OpenHW Group), **Rocket** and **BOOM** (Berkeley, Chisel), **PULP/Ibex** (ETH Zürich and lowRISC), **VexRiscv** (SpinalHDL), **SERV** (the world's smallest RISC-V core), and the **OpenTitan** root-of-trust project. Contributing verification, documentation or a peripheral to any of these puts your name on work that hiring managers can read.

## 4. The interview

Expect three to six rounds. What is actually asked:

**Digital design / RTL:**
- Design an FSM on a whiteboard (traffic light, sequence detector, arbiter). Draw the state diagram, then the RTL.
- Clock domain crossing: "how do you pass a 16-bit value from a 100 MHz to a 33 MHz domain?" — the expected answer is an async FIFO with Gray-coded pointers, and the interviewer wants to hear *why* Gray coding.
- Setup and hold: derive the inequalities, compute maximum frequency for a given path, explain why hold violations cannot be fixed by slowing the clock.
- Metastability and MTBF; two-flop synchronisers and their limits.
- Blocking versus non-blocking assignment, and what goes wrong when they are mixed.
- Latch inference: show me code that infers a latch, and fix it.
- Small design puzzles: divide-by-3 with 50% duty cycle; a clock-gating cell and why a plain AND gate is wrong; a synchronous FIFO's full/empty logic; a round-robin arbiter.
- Low power: clock gating, power gating, multi-Vt, DVFS — when each applies.

**Verification:**
- All the above, plus: object-oriented design in SystemVerilog; UVM component roles and the phase order; how the factory and config DB work and why they exist; constraint writing and solving order; functional versus code coverage and what closure means; how you would verify a specific block (they will name one and expect a test plan).

**Physical design:**
- The flow end to end, in order, with what each step optimises.
- Congestion: how you detect it and the five things you would try.
- Fixing setup versus hold; useful skew; why hold fixes can create setup violations.
- IR drop and electromigration; what a power grid looks like and how you strengthen it.
- Antenna violations; DRC/LVS debugging.
- Expect Tcl and a lot of "what would you do if the tool reported X".

**Architecture:**
- Cache design: set associativity, replacement policies, write-back versus write-through; compute the AMAT for a given hierarchy.
- Coherence: walk MESI through a two-core scenario.
- Branch prediction; the cost of a misprediction; pipeline hazards and forwarding.
- Amdahl's law and roofline analysis — expect to be asked to reason quantitatively.

**Universally:** projects. You will be asked to walk through something you built, and the depth of follow-up will be considerable. A Tiny Tapeout chip, an FPGA project or an open-source contribution carries far more weight than coursework.

**Also universal:** coding. Python and C are expected, and many companies run a general software screen regardless of track.

## 5. The career ladder

| Level | Typical years | What changes |
|---|---|---|
| Junior / Engineer I–II | 0–3 | Own a block or a testbench component under supervision. Learn the flow and the internal tools |
| Senior Engineer | 3–8 | Own a subsystem end to end; make microarchitectural decisions; mentor |
| Staff / Principal | 8–15 | Own an architecture, a methodology or a chip-level function; make decisions that bind other teams |
| Distinguished / Fellow | 15+ | Set technical direction across products; the top of the individual-contributor track, and at most companies it pays as well as senior management |
| Management track | branches at senior | Team lead → manager → director → VP of engineering |

Notes that matter:

- **The individual-contributor ladder is real in this industry** — Fellow and Distinguished Engineer are genuine destinations, unlike in much of software.
- **Compensation** is highest at fabless AI and CPU companies, then EDA and IP vendors, then IDMs, then foundries and equipment makers; the gap between the top and the median is large and has widened since 2023. Regional variation is enormous.
- **Geography still binds.** Design centres cluster: Silicon Valley and Austin, Hillsboro, Bangalore and Hyderabad, Hsinchu, Seoul, Shanghai and Shenzhen, Cambridge and Bristol, Munich and Dresden, Grenoble, Haifa, Kraków. Remote work exists for verification, architecture and CAD far more than for physical design or analog.
- **The specialisation trap.** Deep tool-specific expertise pays well and travels badly. Keep the fundamentals — timing, physics, architecture — sharp enough that you could change track.
- **The most durable positions** are analog/mixed-signal design, process integration, and anything at the boundary between physics and design. The most automatable are the routine parts of implementation, which is exactly where the AI-assisted flows (`03`) are pointed.

## Open questions

- Tiny Tapeout current pricing and shuttle process nodes are not stated on the pages retrieved; use the site's calculator (`needs-verification`).
- Efabless' operating status is unverified.
- FPGA board prices are indicative and unverified.
- Compensation figures are deliberately omitted rather than guessed; regional survey data (Levels.fyi, Glassdoor, national engineering bodies) should be consulted directly.

## Sources

- [Tiny Tapeout](https://tinytapeout.com/) — accessed 2026-08-25
- [Tiny Tapeout FAQ](https://tinytapeout.com/faq/) — accessed 2026-08-25
- [OpenROAD Project — Wikipedia](https://en.wikipedia.org/wiki/OpenROAD_Project) — accessed 2026-08-25
- [SkyWater Technology — Wikipedia](https://en.wikipedia.org/wiki/SkyWater_Technology) — accessed 2026-08-25
- [RISC-V — Wikipedia](https://en.wikipedia.org/wiki/RISC-V) — accessed 2026-08-25
