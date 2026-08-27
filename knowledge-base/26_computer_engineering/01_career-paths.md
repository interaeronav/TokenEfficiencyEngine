---
id: compeng.careers
title: Computer engineering career paths, pay and entry routes
domain: 26_computer_engineering
tags: [careers, embedded, firmware, rtl-design, verification, compilers, distributed-systems, security, salaries, hiring, portfolio]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Occupational Outlook Handbook — Computer Hardware Engineers", url: "https://www.bls.gov/ooh/architecture-and-engineering/computer-hardware-engineers.htm", publisher: "US Bureau of Labor Statistics", accessed: 2026-08-25}
  - {title: "Occupational Outlook Handbook — Software Developers, QA Analysts and Testers", url: "https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm", publisher: "US Bureau of Labor Statistics", accessed: 2026-08-25}
  - {title: "Occupational Outlook Handbook — Information Security Analysts", url: "https://www.bls.gov/ooh/computer-and-information-technology/information-security-analysts.htm", publisher: "US Bureau of Labor Statistics", accessed: 2026-08-25}
  - {title: "Occupational Outlook Handbook — Computer Network Architects", url: "https://www.bls.gov/ooh/computer-and-information-technology/computer-network-architects.htm", publisher: "US Bureau of Labor Statistics", accessed: 2026-08-25}
  - {title: "Occupational Outlook Handbook — Computer and Information Research Scientists", url: "https://www.bls.gov/ooh/computer-and-information-technology/computer-and-information-research-scientists.htm", publisher: "US Bureau of Labor Statistics", accessed: 2026-08-25}
  - {title: "2025 Stack Overflow Developer Survey — Work and salary", url: "https://survey.stackoverflow.co/2025/work", publisher: "Stack Overflow", accessed: 2026-08-25}
related: [compeng.overview, compeng.curriculum, compeng.learning_plan, compeng.manufacturing]
unit_system: SI
---

# Computer engineering career paths, pay and entry routes

**Summary.** Fourteen distinct tracks sit under the label "computer engineer", and they differ more from each other than most outsiders realise: an RTL designer and a backend distributed-systems engineer share almost no daily tools. This file describes what each track's work actually is, the prerequisites that gate it, the typical progression, verified salary anchors, and — track by track — the realistic route in without a traditional degree. All salary figures carry their year and source; where no source could be verified the band is marked as an estimate.

## Key facts — verified salary anchors

| Occupation (US) | Median annual wage | Year | Employment | 2024–34 growth |
|---|---|---|---|---|
| Computer hardware engineers | **US$155,020** | May 2024 | 76,800 | +7% |
| Computer & information research scientists | **US$140,910** | May 2024 | 40,300 | +20% |
| Software developers | **US$133,080** | May 2024 | 1,693,800 | +16% |
| Computer network architects | **US$130,390** | May 2024 | 179,200 | +12% |
| Information security analysts | **US$124,910** | May 2024 | 182,800 | +29% |
| Software QA analysts and testers | **US$102,610** | May 2024 | 201,700 | +10% |

Source: US Bureau of Labor Statistics Occupational Outlook Handbook, May 2024 wage data.

| Role (global median total comp) | Global | US | UK | Germany | India |
|---|---|---|---|---|---|
| Engineering manager | $130,000 | $200,000 | $136,141 | $118,335 | $52,308 |
| Software architect | $102,000 | — | — | $109,054 | $46,496 |
| Cloud infrastructure engineer | $103,112 | — | — | — | — |
| AI/ML engineer | — | $189,500 | $149,756 | — | — |
| Front-end developer | $62,015 | — | — | — | — |
| QA / test developer | $57,442 | — | — | — | — |
| System administrator | $55,148 | — | — | — | — |

Source: 2025 Stack Overflow Developer Survey, n ≈ 49,000 respondents, self-reported, USD-converted.

> ⚠️ Self-reported survey medians and BLS medians are not comparable instruments. BLS measures wage only, from employer records; Stack Overflow measures self-reported total compensation from a self-selected sample skewed toward English-speaking, web-oriented developers. Use BLS for level-setting a market, Stack Overflow for cross-country ratios.

**[NA] [ZA]** No verified Namibian or South African salary series for these occupations was obtainable for this file. As a working heuristic used across the region, senior software salaries in South Africa run roughly 20–30% of US levels in nominal USD, and Namibian public/parastatal IT roles benchmark against the South African public sector. **Treat any regional number in this folder as `needs-verification`.**

## The fourteen tracks

### 1. Embedded and firmware engineering
**The work.** Writing the software that runs on a microcontroller or SoC with no OS or a small RTOS: bring-up of a new board, bootloaders, device drivers, interrupt handlers, power management, communication stacks (SPI, I²C, CAN, UART, BLE), and meeting hard real-time deadlines in tens of kilobytes of RAM. Half the job is reading datasheets and errata; a quarter is on an oscilloscope or logic analyser; a quarter is C.
**Prerequisites.** C (fluent, including volatile, bitfields, linker scripts), digital logic, basic circuits, one MCU family (STM32, ESP32, nRF, RP2040), how to read a schematic, an RTOS (FreeRTOS or Zephyr).
**Progression.** Firmware engineer → senior → firmware lead / systems architect → principal. Domain specialisation (automotive ISO 26262, medical IEC 62304, aerospace DO-178C) commands a premium and locks you into the domain.
**Pay.** Sits within the BLS hardware-engineer and software-developer bands; safety-critical automotive/aero firmware in the US typically clears the software-developer median.
**Entry without a degree.** The most degree-permeable hardware-adjacent track. Buy an STM32 or RP2040 board, write a driver from the datasheet with no HAL, publish it. Contribute to Zephyr, ChibiOS or the Rust embedded HAL crates. A GitHub with three real drivers and one product-quality bootloader is a stronger signal than a transcript. Ham radio, drone and robotics communities are real recruiting pipelines.

### 2. Systems and OS engineering
**The work.** Kernel, hypervisor, container runtime, filesystem, storage stack, and the userspace plumbing beneath applications. Debugging deadlocks in a scheduler, chasing memory corruption across a syscall boundary, making the page-fault path 3% faster.
**Prerequisites.** C (and increasingly Rust), OS theory to OSTEP depth, virtual memory and paging, concurrency and memory models, gdb/ftrace/perf, comfort reading 100k-line codebases.
**Progression.** Systems engineer → kernel/hypervisor specialist → principal. Employers: cloud providers, Red Hat/SUSE/Canonical, chip vendors' software teams, storage vendors, HFT shops.
**Entry without a degree.** Uniquely meritocratic because the review process is public. Fix real bugs in the Linux kernel, submit patches to a subsystem via its mailing list, or work on a smaller kernel (seL4, Redox, xv6-derived teaching kernels). A merged mainline commit is a hiring credential.

### 3. Compilers and toolchains
**The work.** Front ends (lexing, parsing, semantic analysis), middle ends (SSA, optimisation passes, alias analysis, autovectorisation), back ends (instruction selection, register allocation, scheduling). Also linkers, debuggers, sanitizers, JITs, and the ML-compiler stack (MLIR, TVM, XLA, Triton).
**Prerequisites.** Data structures and graph algorithms, formal languages, an ISA in depth, C++ (LLVM and GCC are both C++), and the ability to read a language standard.
**Progression.** Compiler engineer → optimisation or codegen specialist → toolchain architect. Small field, high leverage, unusually stable careers.
**Pay.** Consistently above the software-developer median; ML-compiler specialists in 2025–26 are among the best-paid non-managerial software roles.
**Entry without a degree.** Follow *Crafting Interpreters* (free) end to end, then write a real compiler for a small language targeting LLVM IR or your own bytecode VM. Then contribute an LLVM pass or a Rust/Zig compiler fix. The field hires on demonstrated code almost exclusively.

### 4. Hardware / RTL design
**The work.** Describing digital hardware in SystemVerilog, VHDL or Chisel: datapaths, pipelines, cache controllers, DMA engines, bus fabrics (AXI, TileLink, CHI), clock-domain crossings. Then synthesis, timing closure, area and power optimisation, and hand-off to physical design.
**Prerequisites.** Digital logic and finite state machines, computer architecture, static timing analysis, an HDL, and an FPGA toolchain (Vivado, Quartus, or the open Yosys/nextpnr flow).
**Progression.** RTL design engineer → block owner → subsystem/SoC architect. Employers: Apple, Nvidia, AMD, Intel, Qualcomm, Arm, Broadcom, SiFive, plus defence and aerospace.
**Pay.** The BLS computer-hardware-engineer median of US$155,020 (May 2024) is the anchor; senior silicon designers at leading fabless firms are well above it.
**Entry without a degree.** Hardest of the fourteen. The realistic path is an FPGA portfolio: implement a RISC-V core (RV32I first, then pipelined, then with caches), get it running on a cheap FPGA board (Tang Nano, iCEBreaker, Arty), and publish the RTL plus testbenches and timing reports. The open-source silicon community (OpenROAD, Efabless/Caravel shuttle runs, OpenTitan, Chipyard) has produced people who got hired without degrees, but they are exceptions. Cross-reference `27_semiconductors_and_chip_design`.

### 5. Design verification (DV)
**The work.** Proving the RTL is correct before US$10m+ of mask costs are committed. Constrained-random testbenches in SystemVerilog/UVM, functional coverage closure, assertion-based verification (SVA), formal property verification, and emulation. In most SoC teams DV headcount exceeds design headcount by 2:1 or 3:1.
**Prerequisites.** SystemVerilog (the verification subset is essentially a different language from the synthesis subset), object-oriented design, UVM, constrained-random and coverage methodology, plus scripting (Python, TCL, Perl).
**Progression.** DV engineer → verification lead → verification architect / methodology owner.
**Entry without a degree.** More permeable than RTL design because demand chronically exceeds supply. Build a UVM testbench for an open-source core (a PicoRV32 or CVA6), publish the coverage report. Free simulators (Verilator, Icarus) plus the open cocotb framework (Python-based verification) let you build a portfolio at zero cost.

### 6. Computer architecture
**The work.** Deciding what the hardware should be before anyone writes RTL: workload analysis, performance modelling in C++ simulators (gem5, custom cycle-approximate models), cache hierarchy and prefetcher design, branch predictor design, memory-system sizing, power/performance/area trade-offs.
**Prerequisites.** Hennessy & Patterson to *Computer Architecture: A Quantitative Approach* depth, statistics, strong C++, workload characterisation, and reading ISCA/MICRO/ASPLOS/HPCA papers.
**Progression.** Performance modelling engineer → architect → chief architect. Very often gated by a PhD or a master's; the BLS "computer and information research scientists" line (median US$140,910, May 2024, master's typical entry) is the closest official match.
**Entry without a degree.** The least permeable track. Realistic on-ramp: get in as a performance engineer on the software side, build a track record of workload analysis, then move across internally.

### 7. Networking
**The work.** Splits into three sub-tracks. *Protocol/dataplane engineering*: writing packet-processing code (DPDK, eBPF/XDP, P4, kernel networking), implementing routing protocols, building switch/router software. *Network architecture*: designing datacentre fabrics (Clos topologies, BGP-to-the-host), WAN, and increasingly the AI-cluster interconnect (RoCE, InfiniBand, ultra-Ethernet). *Network security*: overlaps with track 8.
**Prerequisites.** TCP/IP in depth from the wire up, sockets, packet capture (tcpdump/Wireshark), one of C/Rust/Go, and — for architecture — BGP and datacentre topology.
**Pay.** BLS computer network architects median US$130,390 (May 2024), 179,200 employed, +12% to 2034.
**Entry without a degree.** Excellent. CCNA/CCNP still open doors; then Stanford's CS 144 (build a TCP stack) converts a network operator into a network engineer. AI-cluster networking is currently the hottest sub-niche and hires on demonstrated ability.

### 8. Security engineering
**The work.** Offensive (penetration testing, red teaming, exploit development, vulnerability research), defensive (detection engineering, incident response, threat hunting), or product security (secure design review, cryptography engineering, supply-chain security, hardware security and side channels).
**Prerequisites.** Deep systems knowledge — you cannot exploit what you do not understand. Assembly, memory layout, OS internals, networking, cryptography basics, and reverse engineering (Ghidra, IDA, radare2).
**Pay.** BLS information security analysts median US$124,910 (May 2024), 182,800 employed, **+29% to 2034 — the fastest growth of any occupation in this file**. Vulnerability research and exploit development pay well above that median.
**Entry without a degree.** The most degree-indifferent track of all fourteen. Capture-the-flag competitions (picoCTF for beginners, then DEF CON quals, pwnable.kr, Hack The Box), public CVEs, bug bounty payouts, and a technical blog are the currency. OSCP is the certification with the most real credibility; CISSP is a management credential, not an engineering one.

### 9. Distributed systems and backend
**The work.** Building services that stay correct and available across many machines: consensus and replication, sharding, caching, queues, idempotency, backpressure, schema evolution, and the operational discipline of running it. This is the largest employer of the fourteen by headcount.
**Prerequisites.** One backend language (Go, Java, Rust, C#, Python), SQL and data modelling, networking, concurrency, and Kleppmann's *Designing Data-Intensive Applications* internalised. MIT 6.824 (now 6.5840) is the standard course.
**Progression.** Backend engineer → senior → staff → principal, or → engineering manager. Levels above senior are defined by scope of technical judgement, not by output volume.
**Pay.** BLS software developers median US$133,080 (May 2024); Stack Overflow 2025 global medians put cloud infrastructure engineers at $103,112 and software architects at $102,000, with US engineering managers at $200,000.
**Entry without a degree.** Very permeable and always has been. The portfolio that works: a real service with real users, plus one from-scratch systems project (a Raft implementation, a key-value store with a WAL, a toy database). Avoid CRUD-tutorial portfolios — every recruiter has seen ten thousand of them.

### 10. Graphics and games
**The work.** Rendering engineers (rasterisation, ray tracing, shading models, GPU pipeline optimisation), engine engineers (memory, streaming, ECS architecture, tooling), and gameplay/physics. Also the non-game graphics market: CAD, simulation, film VFX, medical visualisation.
**Prerequisites.** Linear algebra to a genuine working level, C++ (still overwhelmingly dominant), one graphics API (Vulkan, DirectX 12, Metal, WebGPU), shader languages (HLSL/GLSL/WGSL), and GPU architecture.
**Pay.** Games pay noticeably below equivalent seniority in backend or systems, with worse hours; graphics work in simulation, automotive HMI, CAD and film pays better than games.
**Entry without a degree.** Extremely portfolio-driven. Write a software rasteriser, then a path tracer (Pete Shirley's free *Ray Tracing in One Weekend*), then a small Vulkan renderer. Shadertoy work, demoscene productions and a published devlog all count. Cross-reference `28_graphic_and_game_design`.

### 11. ML / AI infrastructure
**The work.** Not model research — the machinery underneath. Distributed training (data/tensor/pipeline parallelism), inference serving and batching, GPU kernel authoring (CUDA, Triton, ROCm), compiler stacks (XLA, TorchInductor, MLIR), quantisation, memory and interconnect optimisation, cluster scheduling, and datacentre-scale reliability.
**Prerequisites.** Strong systems fundamentals, CUDA or Triton, PyTorch internals, numerical computing, networking (collectives, NCCL, RDMA), and profiling.
**Pay.** The best-paid non-managerial software niche in 2025–26. Stack Overflow 2025 reports US AI/ML engineers at a $189,500 median and UK at $149,756 — and infrastructure specialists inside frontier labs and cloud providers sit well above those medians.
**Entry without a degree.** Genuinely open, because the field is young enough that nobody has the right credential. Write GPU kernels, publish benchmarks, contribute to vLLM / llama.cpp / PyTorch / TVM. Demonstrated kernel-level performance work is hired on sight.

### 12. Robotics
**The work.** Perception (sensor fusion, SLAM, computer vision), planning and control (motion planning, MPC, state estimation), and the real-time embedded layer underneath. Applied in warehouse automation, agriculture, mining, drones, surgical robotics and autonomous vehicles.
**Prerequisites.** Linear algebra, probability and estimation (Kalman/particle filters), control theory, C++ and Python, ROS 2, and real-time embedded skills from track 1.
**Entry without a degree.** Build something that moves. A ROS 2 robot that maps a room, a drone with custom flight-control code, a line-following robot with a properly tuned PID. Competitions (RoboCup, university-adjacent challenges, DIY Robocars) are recruiting grounds. Cross-reference `21_machine_vision`.

### 13. EDA (electronic design automation) software
**The work.** Writing the tools chip designers use: synthesis, place-and-route, static timing analysis, simulation engines, formal verification, DRC/LVS. Algorithmically among the hardest software in existence — graph algorithms, SAT/SMT solving, numerical methods and combinatorial optimisation at enormous scale.
**Prerequisites.** Very strong C++, algorithms and optimisation, plus enough VLSI knowledge to understand what the tool is for.
**Employers.** Synopsys, Cadence, Siemens EDA, Ansys, plus in-house tool teams at every large chip company and the open-source flow (OpenROAD, Yosys, KLayout, Verilator).
**Entry without a degree.** Contribute to Yosys, OpenROAD or Verilator. These are small enough communities that a competent contributor becomes known quickly, and all three have produced hires.

### 14. Quantitative and HFT engineering
**The work.** Two distinct roles conflated by outsiders. *Quantitative researcher*: statistical modelling of markets — heavily PhD-gated in maths, physics or statistics. *Low-latency engineer*: making the path from market data to order as short as possible — kernel bypass networking, lock-free data structures, cache-line-aware layout, FPGA acceleration, nanosecond-scale measurement. The second is a computer engineering job in the purest sense.
**Prerequisites.** C++ at expert level (or Rust), CPU microarchitecture, cache behaviour, NUMA, kernel bypass (Solarflare/onload, DPDK), FPGA for the fastest paths, and rigorous measurement discipline.
**Pay.** The highest total compensation in this file at senior levels, with the largest variable component. Stack Overflow 2025 puts "financial analyst/engineer" at a $103,757 global median, but that category conflates ordinary fintech with HFT and badly understates the top of the distribution. **Specific HFT compensation figures could not be verified from a primary source and are deliberately omitted.**
**Entry without a degree.** Rare but real, and almost always via demonstrated low-level performance work: published benchmarks, a lock-free queue with a proof of correctness, measurable microarchitectural optimisation. Firms hire on interview performance more than on credentials, and their interviews are genuinely hard.

## Breaking in without a degree — the general method

1. **Pick one track and one adjacent track.** Breadth without depth reads as a hobbyist. Depth in one plus literacy in a neighbour reads as an engineer.
2. **Build the artefact that only a competent person can build.** For each track above, that artefact is named. Three deep projects beat twenty shallow ones.
3. **Make the work public and legible.** Repository with a real README, a design document, tests, and a write-up of what went wrong. The write-up matters as much as the code — it is the only evidence of judgement.
4. **Contribute to something that has a review process.** A merged patch in Linux, LLVM, Zephyr, Yosys or PyTorch is a third-party assessment of your competence. Nothing on a CV substitutes for it.
5. **Get the fundamentals that interviews actually test.** Data structures and algorithms, systems design, and — for hardware tracks — digital logic and timing. `02_the-curriculum.md` sequences this.
6. **Route around HR.** Degree filters are usually applied by recruiting systems, not by engineers. Referrals, open-source maintainers, conference hallways, and small companies bypass them. Start at a smaller employer, get two years of title, then the filter stops mattering.
7. **Know what the credential still buys.** Work visas, defence and aerospace clearance-adjacent roles, most graduate-scheme pipelines, and professional registration (ECSA, PEng, CEng) all effectively require an accredited degree. If any of those are in your plan, the degree is not optional.

## Progression, generally

Most technical ladders in this domain run: junior (0–2 yrs, executes well-defined tasks) → mid (2–5, owns features) → senior (5–8, owns systems and mentors) → staff (owns cross-team technical direction) → principal/distinguished (owns organisation-level technical strategy). The management ladder forks at senior. The two are usually paid comparably up to staff/manager, after which the paths diverge by company.

The two mistakes that cost the most: staying at one employer past the point of learning (compensation and skill both stagnate), and moving so often that no project is ever seen through to production consequences.

## Sources

- [BLS OOH — Computer Hardware Engineers](https://www.bls.gov/ooh/architecture-and-engineering/computer-hardware-engineers.htm)
- [BLS OOH — Software Developers, QA Analysts and Testers](https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm)
- [BLS OOH — Information Security Analysts](https://www.bls.gov/ooh/computer-and-information-technology/information-security-analysts.htm)
- [BLS OOH — Computer Network Architects](https://www.bls.gov/ooh/computer-and-information-technology/computer-network-architects.htm)
- [BLS OOH — Computer and Information Research Scientists](https://www.bls.gov/ooh/computer-and-information-technology/computer-and-information-research-scientists.htm)
- [2025 Stack Overflow Developer Survey — Work](https://survey.stackoverflow.co/2025/work)

## Open questions

- No verified salary series for Namibia or South Africa was obtainable. The regional heuristic given is **`needs-verification`** and should be replaced with data from a local source (e.g. a South African IT remuneration survey) before use.
- HFT and quant compensation bands are widely reported but were not verifiable from a primary source; they are omitted rather than estimated.
- Compensation for RTL design, DV and ML infrastructure above the BLS medians is well attested anecdotally but no primary-source band was fetched; these are described qualitatively rather than numerically.
