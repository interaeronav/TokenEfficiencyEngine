---
id: compeng.overview
title: Computer engineering domain map and how it differs from CS, SWE, EE and IT
domain: 26_computer_engineering
tags: [computer-engineering, computer-science, software-engineering, electrical-engineering, information-technology, discipline-map, abstraction-stack]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Open Source Society University — Computer Science curriculum", url: "https://github.com/ossu/computer-science", publisher: "OSSU", accessed: 2026-08-25}
  - {title: "Teach Yourself Computer Science", url: "https://teachyourselfcs.com/", publisher: "Oz Nova & Myles Byrne (Bradfield School of Computer Science)", accessed: 2026-08-25}
  - {title: "From Nand to Tetris", url: "https://www.nand2tetris.org/", publisher: "Noam Nisan & Shimon Schocken", accessed: 2026-08-25}
  - {title: "Occupational Outlook Handbook — Computer Hardware Engineers", url: "https://www.bls.gov/ooh/architecture-and-engineering/computer-hardware-engineers.htm", publisher: "US Bureau of Labor Statistics", accessed: 2026-08-25}
  - {title: "Occupational Outlook Handbook — Software Developers, QA Analysts and Testers", url: "https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm", publisher: "US Bureau of Labor Statistics", accessed: 2026-08-25}
  - {title: "2025 Stack Overflow Developer Survey — Technology", url: "https://survey.stackoverflow.co/2025/technology", publisher: "Stack Overflow", accessed: 2026-08-25}
  - {title: "ACM A. M. Turing Award (list of laureates)", url: "https://en.wikipedia.org/wiki/Turing_Award", publisher: "Wikipedia", accessed: 2026-08-25}
related: [compeng.careers, compeng.curriculum, compeng.machine_level, compeng.languages_survey, semiconductors.overview]
unit_system: SI
---

# Computer engineering domain map and how it differs from CS, SWE, EE and IT

**Summary.** Computer engineering is the discipline that owns the *whole* stack between physics and application: transistors, logic gates, microarchitecture, instruction sets, firmware, operating systems, compilers, networks and the software that runs on top. It is not a subset of computer science and it is not "software engineering with a soldering iron" — its defining habit of mind is that no layer of the abstraction stack is permitted to be magic. This file maps the domain, draws the honest boundaries between computer engineering, computer science, software engineering, electrical engineering and IT, and names the abstraction ladder that every subsequent file in this folder climbs.

## Key facts

| Fact | Value | Source / date |
|---|---|---|
| US median wage, computer hardware engineers | **US$155,020** | BLS OOH, May 2024 |
| US employment, computer hardware engineers | 76,800 | BLS, 2024 |
| Projected growth, hardware engineers 2024–34 | 7% | BLS |
| US median wage, software developers | **US$133,080** | BLS OOH, May 2024 |
| US employment, software developers | 1,693,800 | BLS, 2024 |
| Projected growth, software developers 2024–34 | 16% (267,700 jobs) | BLS |
| Ratio of software to hardware engineering jobs (US) | ≈ **22 : 1** | computed from BLS 2024 |
| Most-used language, professional developers | JavaScript 66%, HTML/CSS 61.9%, SQL 58.6%, Python 57.9% | Stack Overflow Survey 2025 (n≈49,000) |
| Turing Awards given | annually since **1966** (Alan Perlis) | ACM / Wikipedia |
| Canonical "build the whole stack" course | Nand to Tetris, **12 projects**, taught at 400+ institutions | nand2tetris.org |

> ⚠️ The 22:1 software-to-hardware employment ratio is the single most important number for career planning in this domain. Hardware roles pay more per head and are far scarcer; software roles are abundant and increasingly commoditised at the low end. Plan accordingly — see `01_career-paths.md`.

## The abstraction stack

Computer engineering is best understood as a ladder. Each rung is a *contract* that lets you stop thinking about the rung below — until it leaks, at which point you must be able to descend.

```
  application software        (a web app, a game, a trading system)
  ─────────────────────────
  libraries and runtimes      (libc, JVM, CPython, Node, Tokio)
  language + compiler         (C, Rust, LLVM IR, JIT)
  operating system            (processes, VM, scheduling, filesystems, drivers)
  ─────────────────────────
  ABI / calling convention    (System V AMD64, AAPCS64)
  instruction set (ISA)       (x86-64, AArch64, RISC-V)
  ─────────────────────────
  microarchitecture           (pipeline, caches, branch predictor, OoO engine)
  register transfer level     (Verilog/VHDL/Chisel; synthesis)
  logic gates                 (NAND, NOR, flip-flops, standard cells)
  ─────────────────────────
  transistors and process     (FinFET/GAA, EUV lithography, PDK)
  device physics              (band gaps, carrier mobility, leakage)
```

The ISA is the most important boundary in the whole picture. Everything above it is software, everything below is hardware, and the ISA is the only line in the stack that both sides have signed. That is why `03_machine-level-language.md` sits at the centre of this folder.

## The five disciplines, honestly distinguished

### Computer engineering (CE)
**Owns:** the hardware/software boundary. Digital logic, computer architecture, embedded systems, firmware, VLSI, signal processing, real-time systems, hardware-software co-design.
**Accredited as:** an engineering degree (ABET EAC in the US; ECSA in South Africa; ENAEE/EUR-ACE in Europe). Typically requires physics, circuits, electromagnetics and a capstone design project.
**Characteristic artefact:** a working board, an SoC that boots, a driver that meets a latency budget.
**Characteristic failure:** knowing the transistor and the C compiler but never having shipped a product with a user.

### Computer science (CS)
**Owns:** what is computable, at what cost, and how to reason about it. Algorithms, complexity, automata, logic, programming-language theory, cryptography, machine learning theory, databases theory.
**Accredited as:** usually a BSc under a science faculty, not an engineering one. Mathematics-heavy, physics-light.
**Characteristic artefact:** a proof, a new algorithm with a better bound, a paper.
**Characteristic failure:** an elegant asymptotic win that loses to a cache-friendly O(n²) loop on real hardware.

The honest overlap: at good universities, roughly 60% of the CE and CS core is identical (data structures, algorithms, OS, networks, compilers, discrete maths). The divergence is that CE adds circuits, electromagnetics, digital design and signals, while CS adds theory of computation, more discrete maths and more breadth in AI/PL/theory.

### Software engineering (SWE)
**Owns:** building and sustaining large software systems with teams over years. Requirements, architecture, testing, version control, CI/CD, review culture, incident response, maintenance.
**Accredited as:** sometimes a distinct degree, more often a specialisation of CS. In a handful of jurisdictions (Canada, parts of the US) "software engineer" is a protected title requiring licensure; in most of the world it is not.
**Characteristic artefact:** a system that a hundred people can change without breaking.
**Characteristic failure:** process without depth — an engineer who can run a sprint but cannot read a stack trace into the kernel.

SWE is a *practice discipline*, closer to civil engineering's construction management than to physics. It is the least mathematical of the five and the most economically significant by headcount.

### Electrical engineering (EE)
**Owns:** everything electrical, of which digital computing is one branch. Analogue circuits, power systems, RF and microwave, control systems, electromagnetics, photonics, semiconductor devices, communications theory.
**Relationship to CE:** CE was carved out of EE in the 1970s–80s. Many universities still award "Electrical and Computer Engineering" (ECE) as one department — MIT's Course 6, Berkeley's EECS, CMU's ECE.
**Where the boundary really is:** if the problem is dominated by continuous-time physics (noise, impedance, thermal, RF), it is EE. If it is dominated by discrete state and instruction sequencing, it is CE. Signal integrity on a 112 Gb/s SerDes link is EE wearing a CE badge.

### Information technology (IT)
**Owns:** operating and securing computing infrastructure for an organisation. Networks, servers, identity, endpoints, helpdesk, cloud administration, SaaS integration, compliance.
**Distinguishing feature:** IT *consumes* systems that CE and SWE *create*. It is credentialed by vendor certifications (CCNA, RHCE, AWS SA, CISSP) far more than by degrees.
**Where it becomes engineering:** site reliability engineering (SRE), platform engineering and network engineering at scale are genuinely engineering — they involve building software to run software. The boundary is whether you write the tooling or click through it.

### One-line discriminator
> CS asks *can it be done and at what cost*; CE asks *how does the machine actually do it*; SWE asks *how do we keep doing it with a team for ten years*; EE asks *what do the electrons do*; IT asks *how do we keep it running for the business tomorrow*.

## What a modern computer engineer must actually be able to do

This is the competence set that the rest of this folder is designed to build.

1. **Read and write assembly for at least one ISA** and understand what the compiler did to your C. (`03_machine-level-language.md`)
2. **Reason about memory** — stack vs heap, alignment, cache lines, false sharing, virtual memory, TLB pressure.
3. **Write correct concurrent code** — knowing what a memory model is, what a data race is, and why `volatile` is not a synchronisation primitive.
4. **Use C fluently and one memory-safe systems language** (Rust, Go, or modern C++ with discipline). (`05_language-deep-dives.md`)
5. **Debug at every layer** — printf, gdb, perf, strace, a logic analyser, a scope. (`08_modern-practice-and-tooling.md`)
6. **Design digital logic** — write synthesisable Verilog/VHDL, understand timing closure, know what an FPGA is for.
7. **Understand networks from the wire up** — Ethernet framing, IP, TCP state machine, TLS, HTTP.
8. **Understand the OS** — processes, scheduling, syscalls, page tables, interrupts, filesystems.
9. **Understand data at rest and in flight** — relational modelling, indexes, transactions, serialisation formats.
10. **Estimate** — latency numbers, bandwidth budgets, power budgets, cost. Jeff Dean's "latency numbers every programmer should know" is the entry ticket.
11. **Ship** — version control, tests, CI, code review, documentation, on-call.

## The three canonical self-study spines

Three curricula dominate serious self-teaching, and they are complementary rather than competing.

- **Nand to Tetris** (*The Elements of Computing Systems*, Nisan & Schocken, MIT Press) — 12 projects, from a NAND gate to a Tetris implementation running on a computer you built. Part I (projects 1–6) is hardware: Boolean logic, arithmetic, memory, machine language, computer architecture, assembler. Part II (projects 7–12) is software: two VM stages, a high-level language (Jack), a two-stage compiler, and an OS. All materials are free at nand2tetris.org; a paid Coursera track exists. This is the single best cure for "the computer is magic."
- **Teach Yourself CS** (teachyourselfcs.com) — nine subjects, one canonical book and one video course each, 100–200 hours per subject. Its abbreviated path is unusually honest: if you only read two books, read *Computer Systems: A Programmer's Perspective* and *Designing Data-Intensive Applications*.
- **OSSU Computer Science** (github.com/ossu/computer-science) — a full degree-equivalent path from free online courses: Intro CS (14 weeks), then Core Programming (54 weeks), Core Math (45 weeks), CS Tools (2 weeks), Core Systems (30–38 weeks), Core Theory (16 weeks), Core Security (16 weeks), Core Applications (28 weeks), Core Ethics (16 weeks), then Advanced CS and a final project (12–26 weeks). It is broader and slower than Teach Yourself CS and closer to an actual degree.

`02_the-curriculum.md` sequences these into one path; `10_learning-plan.md` turns that into a 24-month calendar.

## Files in this domain

| File | Covers |
|---|---|
| `00_overview.md` | this map; discipline boundaries |
| `01_career-paths.md` | fourteen career tracks, prerequisites, progression, pay, entry without a degree |
| `02_the-curriculum.md` | sequenced subject-by-subject study plan with books, courses, projects, hours |
| `03_machine-level-language.md` | binary through ISAs, ABIs, pipelines, caches, MMU, ELF, linking, real assembly |
| `04_programming-languages-survey.md` | paradigms, type systems, memory models, compilation models; 48-language register |
| `05_language-deep-dives.md` | C, C++, Rust, Python, JS/TS, Go — mental model, traps, tooling, weaknesses |
| `06_great-computer-scientists.md` | the figures, their actual contributions, Turing Award years, what to read |
| `07_essential-books-and-papers.md` | annotated register of books and landmark papers, with free links |
| `08_modern-practice-and-tooling.md` | Git internals, build systems, CI/CD, containers, testing, debugging, AI assistants |
| `09_computer-manufacturing-economics.md` | the value chain from IP to retail, margins, fabs, memory cycle, geopolitics |
| `10_learning-plan.md` | month-by-month 24-month plan and portfolio projects |

Cross-domain: `27_semiconductors_and_chip_design` covers process technology, EDA flows and fab physics in depth; `28_graphic_and_game_design` covers the rendering pipeline; `21_machine_vision` covers applied CV.

## The honest state of the field in 2026

Three structural facts should shape any plan made today.

**One: the low end of software work is under real pressure.** The 2025 Stack Overflow survey found 84% of developers using or planning to use AI tools, up from 76% the year before, and 51% of professionals using them daily. At the same time trust fell — only 3% highly trust AI output, 46% actively distrust it, and 66% cite "AI solutions that are almost right, but not quite" as their top frustration. The work that survives is the work that requires holding a real model of the machine, which is exactly what this domain teaches.

**Two: hardware and systems skills are scarce and getting scarcer.** 76,800 US computer hardware engineers against 1.69 million software developers. The AI datacentre buildout has made anyone who genuinely understands memory bandwidth, interconnect and power a scarce commodity.

**Three: the credential is negotiable but the competence is not.** A degree still opens the first door fastest, particularly for hardware, verification and defence work, and it is often mandatory for visas. But in software, systems and security, a portfolio of built things — a CPU, a compiler, a kernel, a database — beats a transcript at almost every serious employer. `10_learning-plan.md` is written for that route.

## Sources

- [OSSU Computer Science curriculum](https://github.com/ossu/computer-science) — OSSU
- [Teach Yourself Computer Science](https://teachyourselfcs.com/) — Bradfield School of Computer Science
- [From Nand to Tetris](https://www.nand2tetris.org/) and [course project list](https://www.nand2tetris.org/course) — Nisan & Schocken
- [BLS OOH — Computer Hardware Engineers](https://www.bls.gov/ooh/architecture-and-engineering/computer-hardware-engineers.htm)
- [BLS OOH — Software Developers, QA Analysts and Testers](https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm)
- [2025 Stack Overflow Developer Survey — Technology](https://survey.stackoverflow.co/2025/technology)
- [2025 Stack Overflow Developer Survey — AI](https://survey.stackoverflow.co/2025/ai)
- [Turing Award laureates](https://en.wikipedia.org/wiki/Turing_Award) — Wikipedia

## Open questions

- ABET/ECSA/EUR-ACE accreditation criteria for computer engineering were not fetched for this file; the accreditation statements above are general and should be checked against the current criteria documents before being relied on for admissions or registration advice.
- The 2025 Turing Award (announced in 2026) could not be verified — the ACM award pages returned 403 or stale cached content. The verified list in this folder ends at the 2024 award (Barto & Sutton).
