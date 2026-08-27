---
id: compeng.learning_plan
title: A 24-month plan from beginner to employable
domain: 26_computer_engineering
tags: [learning-plan, roadmap, portfolio, projects, self-assessment, nand2tetris, csapp, xv6, raft, compiler, kernel, database, milestones]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Open Source Society University — Computer Science curriculum", url: "https://github.com/ossu/computer-science", publisher: "OSSU", accessed: 2026-08-25}
  - {title: "Teach Yourself Computer Science", url: "https://teachyourselfcs.com/", publisher: "Bradfield School of Computer Science", accessed: 2026-08-25}
  - {title: "From Nand to Tetris — course and projects", url: "https://www.nand2tetris.org/course", publisher: "Nisan & Schocken", accessed: 2026-08-25}
  - {title: "Operating Systems: Three Easy Pieces (free)", url: "https://pages.cs.wisc.edu/~remzi/OSTEP/", publisher: "Arpaci-Dusseau Books", accessed: 2026-08-25}
  - {title: "Crafting Interpreters (free)", url: "https://craftinginterpreters.com/", publisher: "Robert Nystrom", accessed: 2026-08-25}
  - {title: "2025 Stack Overflow Developer Survey — Work", url: "https://survey.stackoverflow.co/2025/work", publisher: "Stack Overflow", accessed: 2026-08-25}
related: [compeng.curriculum, compeng.careers, compeng.books_papers, compeng.tooling]
unit_system: SI
---

# A 24-month plan from beginner to employable

**Summary.** Twenty-four months, at **15–20 hours per week** — roughly 1,600–2,000 hours, which is consistent with Teach Yourself CS's 100–200 hours per subject across nine subjects and considerably faster than OSSU's full Core path. Each month has a milestone, a named resource and a deliverable. Six portfolio projects run through it: **a CPU, a compiler, an OS kernel, a database, a network stack, and one real shipped application.** The plan ends with an honest self-assessment rubric, because the most common failure in self-study is not laziness — it is not knowing when you have arrived.

## Key facts

| Parameter | Value |
|---|---|
| Total commitment | 24 months at **15–20 h/week** ≈ 1,600–2,000 hours |
| Reference benchmark | Teach Yourself CS: **100–200 h per subject × 9 subjects** |
| Reference benchmark | Nand to Tetris: Part I 6 weeks @ 7–13 h/wk; Part II 6 weeks @ 12–18 h/wk |
| Portfolio projects | 6 flagship + ~10 supporting |
| Minimum viable path if time is halved | Months 1–4, 7–10, 13–16, 21–24 (see §"If you only have twelve months") |

> ⚠️ **The plan is a sequence, not a schedule.** If a month takes six weeks, it takes six weeks. The order is load-bearing; the calendar is not. What matters is that at every milestone there is a *thing that works* — an artefact you can show and defend.

## Phase 1 — Foundations (months 1–6)

### Month 1 — Programming, from zero
**Resource:** Python for the tooling (`uv`, `ruff`, `pytest`) plus MIT's *Missing Semester of Your CS Education* — OSSU's "CS Tools", 2 weeks at 12 h/week. Learn the shell, Git, the editor, and how to read documentation.
**Deliverable:** a command-line tool you use yourself, in Git, with tests and a README.
**Checkpoint:** you can navigate a filesystem, write a shell pipeline, and recover from a bad commit with `git reflog`.

### Month 2 — Nand to Tetris Part I, projects 1–3
**Resource:** nand2tetris.org, free. Projects 1 (Boolean logic), 2 (Boolean arithmetic), 3 (memory).
**Deliverable:** an ALU and a RAM hierarchy built from NAND gates in the HDL simulator, passing all supplied tests.
**Checkpoint:** you can explain how an adder works from gates, and why a flip-flop needs a clock.

### Month 3 — Nand to Tetris Part I, projects 4–6 → **Portfolio project 1: a CPU**
**Resource:** nand2tetris.org projects 4 (machine language), 5 (computer architecture), 6 (assembler).
**Deliverable:** the Hack CPU, working, running a program you wrote in Hack assembly, plus your own assembler.
**Checkpoint:** the sentence "the computer is magic" is now permanently unavailable to you.

### Month 4 — Discrete mathematics
**Resource:** *Mathematics for Computer Science* (Lehman, Leighton & Meyer, free) with MIT 6.042J video. OSSU allocates 13 weeks at 5 h/week; compress it by doing problems rather than watching everything.
**Deliverable:** written proofs — induction, pigeonhole, a counting argument — plus a DPLL SAT solver in Python.
**Checkpoint:** you can write a correct induction proof without looking up the template.

### Month 5 — C, part one
**Resource:** K&R *The C Programming Language*, chapters 1–5, every exercise. Then CS:APP chapters 1–3 (data representation, machine-level code).
**Deliverable:** a `wc` clone, a `cat` clone, a dynamic array and a linked list, all with tests and all built with `-Wall -Wextra -Werror -fsanitize=address,undefined`.
**Checkpoint:** pointers, arrays and pointer arithmetic are no longer confusing. You can explain what `int *p[10]` versus `int (*p)[10]` means without hesitating.

### Month 6 — C, part two, and the toolchain
**Resource:** K&R chapters 6–8; CS:APP chapters 6–7 (memory hierarchy, linking). Compiler Explorer, daily.
**Deliverable:** **your own `malloc`** — free lists, splitting, coalescing, alignment — passing the CS:APP Malloc Lab traces. Plus a written comparison of the x86-64, AArch64 and RISC-V assembly for one C function (the method is in `03_machine-level-language.md`).
**Checkpoint:** you can read `objdump -d` output and explain what the compiler did.

**Phase 1 review.** You have built a CPU and an allocator. You can read assembly. You have four public repositories. Roughly 350–450 hours in.

## Phase 2 — Core systems (months 7–14)

### Month 7 — Data structures and algorithms, part one
**Resource:** Skiena, *The Algorithm Design Manual*, chapters 1–8; Roughgarden's Stanford *Algorithms* Part 1 (OSSU: 8 weeks @ 4–8 h/wk).
**Deliverable:** implemented from scratch **in C**, with tests and measured complexity: dynamic array, hash map (open addressing *and* chaining, benchmarked against each other), binary heap, BST, and a red-black or AVL tree.
**Checkpoint:** you can derive the amortised cost of dynamic-array growth on a whiteboard.

### Month 8 — Data structures and algorithms, part two
**Resource:** Skiena chapters 9–16; Roughgarden Part 2.
**Deliverable:** graph algorithms (BFS, DFS, topological sort, Dijkstra with a real priority queue, union-find with path compression), dynamic programming (edit distance, knapsack, LIS), and a B-tree — which you will reuse in month 19.
**Checkpoint:** given an unfamiliar problem, you can name the two or three algorithmic families that might apply and say why.

### Month 9 — Computer architecture
**Resource:** Patterson & Hennessy, *Computer Organization and Design* (RISC-V edition); Berkeley CS 61C labs; CS:APP chapters 4–5.
**Deliverable:** a **single-cycle RV32I core in Verilog**, simulated in Verilator, running a compiled C program. Plus the CS:APP Cache Lab, and a blocked matrix multiply benchmarked against the naive version with `perf stat` showing the cache-miss difference.
**Checkpoint:** you can draw the five-stage pipeline and explain every hazard and its mitigation.

### Month 10 — Operating systems, part one
**Resource:** OSTEP (free), the virtualisation part — processes, the process API, limited direct execution, scheduling, virtual memory, paging, TLBs, swapping.
**Deliverable:** **a shell** with pipes, redirection, background jobs, signal handling and job control. Then the first half of the MIT 6.1810 xv6 labs.
**Checkpoint:** you can explain what happens, step by step, from a process calling `fork()` to two processes running.

### Month 11 — Operating systems, part two
**Resource:** OSTEP concurrency and persistence parts; the remaining xv6 labs.
**Deliverable:** a thread pool with condition variables; a lock-free single-producer/single-consumer queue; the xv6 copy-on-write fork and page-table labs; a simple user-space filesystem over a file image.
**Checkpoint:** you can explain why `volatile` is not a mutex, and what a memory barrier does.

### Month 12 — **Portfolio project 2: an OS kernel**
**Resource:** the OSDev wiki; your xv6 experience; a QEMU target (x86-64 or RISC-V).
**Deliverable:** a kernel that boots in QEMU and provides: bootloader hand-off, interrupt handling, a timer, a round-robin scheduler with at least two processes, virtual memory with page tables, a handful of syscalls, and a shell over a serial console. It does not need to be good. It needs to boot.
**Checkpoint:** the most important month in the plan. Almost nobody who has written a kernel is unemployable in systems work.

### Month 13 — Networks, part one
**Resource:** Kurose & Ross, *Computer Networking: A Top-Down Approach*, chapters 1–3; Wireshark, daily.
**Deliverable:** an HTTP/1.1 server from raw sockets with keep-alive and chunked encoding; a DNS resolver over UDP written from the RFC; a full hand-decode of a TLS 1.3 handshake from a capture.
**Checkpoint:** you can draw the TCP state machine and explain what a `TIME_WAIT` is for.

### Month 14 — **Portfolio project 3: a network stack**
**Resource:** Stanford CS 144 labs.
**Deliverable:** a working TCP implementation — byte stream reassembler, receiver, sender, connection state machine — that interoperates with real internet hosts.
**Checkpoint:** you have implemented the protocol that runs the internet. Very few candidates for any job have.

**Phase 2 review.** Three flagship projects done (CPU, kernel, network stack). Roughly 1,000–1,200 hours in. You are already employable for junior systems work.

## Phase 3 — Higher layers (months 15–20)

### Month 15 — Compilers, part one
**Resource:** Nystrom, *Crafting Interpreters* (free) — the whole Java tree-walking interpreter.
**Deliverable:** a working interpreter for the book's language, extended with at least one feature of your own (a new control structure, a standard-library module, better error messages with source spans).
**Checkpoint:** you understand lexing, parsing (recursive descent and Pratt), scope resolution and dynamic dispatch.

### Month 16 — Compilers, part two → **Portfolio project 4: a compiler**
**Resource:** *Crafting Interpreters*, the C bytecode VM half; then Cooper & Torczon on optimisation.
**Deliverable:** a compiler for a small statically-typed language of your own design with a type checker, an SSA-based IR, at least two optimisation passes, and real code generation — either LLVM IR or direct RISC-V/x86-64 assembly. It must compile a non-trivial program that runs.
**Checkpoint:** you can explain what a compiler does to your C, which makes you better at every other language.

### Month 17 — Databases, part one
**Resource:** CMU 15-445 lectures (Andy Pavlo, free); a database textbook for relational algebra and normalisation; PostgreSQL, with `EXPLAIN ANALYZE` on everything.
**Deliverable:** a real schema for a non-trivial domain, correctly normalised, with indexes chosen from measured query plans and a written explanation of each choice.
**Checkpoint:** you can read a query plan and predict which index the planner will choose.

### Month 18 — Databases, part two
**Resource:** CMU 15-445 BusTub assignments; Kleppmann, *Designing Data-Intensive Applications*, Part I.
**Deliverable:** a page-based storage manager, an LRU buffer pool, and a B+ tree index (reusing month 8's B-tree work).
**Checkpoint:** you know why B-trees and LSM-trees have different write amplification, and when each wins.

### Month 19 — **Portfolio project 5: a database**
**Resource:** your own storage engine; the ARIES recovery paper for write-ahead logging.
**Deliverable:** a small relational database: SQL parser for a useful subset, a volcano-model executor, the B+ tree index, transactions with at least two isolation levels, write-ahead logging and crash recovery demonstrated by killing the process mid-write and recovering.
**Checkpoint:** durability is no longer a word you use loosely.

### Month 20 — Distributed systems
**Resource:** MIT 6.824/6.5840 lectures and labs; DDIA Part II; the Raft paper; Lamport's "Time, Clocks".
**Deliverable:** a **working Raft implementation** (leader election, log replication, persistence, snapshots) passing the 6.824 test suite, plus a fault-tolerant sharded key-value store on top. Run it under a partition-injecting harness.
**Checkpoint:** you can explain, precisely, why two-phase commit blocks and Raft does not.

**Phase 3 review.** Five flagship projects. Roughly 1,400–1,700 hours in.

## Phase 4 — Depth, polish and the job (months 21–24)

### Month 21 — Security
**Resource:** pwn.college or picoCTF; Anderson's *Security Engineering* (free chapters); `03_machine-level-language.md` for the memory layout.
**Deliverable:** a stack overflow exploited with ASLR and NX enabled (a ROP chain), a heap exploit, a broken-crypto challenge solved. Then flip sides: audit a real open-source C project with sanitizers and a fuzzer, and file at least one genuine bug report.
**Checkpoint:** you can no longer write C without thinking about the attacker.

### Month 22 — Specialise
Pick **one** track from `01_career-paths.md` and go deep. Suggested month-long deep dives:
- *Embedded* — an STM32 or RP2040 driver written from the datasheet with no HAL, plus your own bootloader.
- *ML infrastructure* — implement a transformer from scratch, then write a CUDA or Triton kernel and benchmark it against the framework's.
- *Graphics* — a software rasteriser, then a path tracer (Shirley's free *Ray Tracing in One Weekend* series).
- *Hardware* — pipeline your month-9 RISC-V core, add caches, get it onto a real FPGA board with timing closure.
- *Distributed/backend* — take your Raft implementation and build something real on it.

### Month 23 — **Portfolio project 6: ship something real**
**Deliverable:** an application with **actual users**, deployed, monitored, with CI, tests, error handling, a runbook and a post-mortem of at least one incident. It does not need to be large. It needs to be *live*, and you need to have been woken up by it once.
**Why this matters more than it looks:** every one of the previous five projects proves you understand computers. This one proves you can be trusted with production. Employers weight the second more heavily than self-taught engineers expect.

### Month 24 — Convert
- **Write.** Five technical posts on the hardest bugs you hit and what you learned. This is the artefact that demonstrates judgement, which nothing else in the portfolio does.
- **Contribute.** At least one merged patch to a real project — Linux, LLVM, Zephyr, Yosys, PyTorch, Verilator, or the largest project you actually use. A merged commit is third-party verification of your competence.
- **Prepare.** Interview fundamentals: ~150 algorithm problems for recall speed, system design practice, and — critically — the ability to *narrate* your six projects. For each: what problem, what design, what you rejected and why, what broke, what you would do differently.
- **Apply.** Referrals first, small companies second, job boards last. Target the track you specialised in.

## The six portfolio projects, and why these six

| # | Project | What it proves | Month |
|---|---|---|---|
| 1 | **A CPU** | You understand the machine from gates up. Nothing else demonstrates this. | 3 (+9, +22 for the RISC-V version) |
| 2 | **An OS kernel** | You can work in an environment with no safety net, no debugger you did not build, and hardware that lies. | 12 |
| 3 | **A network stack** | You understand the protocol the whole industry depends on, at the level of state machines and edge cases. | 14 |
| 4 | **A compiler** | You understand the layer between the language you write and the machine that runs it. | 16 |
| 5 | **A database** | You understand durability, concurrency and query planning — the three things every backend engineer handwaves. | 19 |
| 6 | **A shipped application** | You can be trusted with production. | 23 |

Plus the supporting cast that accumulates naturally: a shell, a `malloc`, a Raft implementation, a container runtime (a weekend project, and a spectacular one for interviews), a regex engine, a ray tracer, a text editor, a `git` clone.

**What does *not* work as a portfolio:** tutorial to-do apps, a repository of cloned coursework, "100 days of code" streaks, a certificate collection, or a personal site whose only content is the personal site.

## How to evaluate your own level honestly

Self-taught engineers routinely misjudge their level in both directions. Use behavioural tests, not feelings.

**You are a beginner if:** you can follow a tutorial but not diverge from it; error messages are frightening rather than informative; you copy code you do not understand; you have never used a debugger.

**You are an advanced beginner if:** you can build something small from a blank file; you use a debugger sometimes; you can read a stack trace; you still avoid whole categories of problem (concurrency, memory management, build systems).

**You are competent if:** you can build a complete small system alone; you reach for a profiler before optimising; you write tests without being told; you can read an unfamiliar codebase and find the relevant part in under an hour; you can explain trade-offs, not just choices. **This is the employable line, and it is where month 24 should land you.**

**You are proficient if:** you debug at every layer including the kernel and the wire; you predict where the bottleneck will be and are usually right; you design systems that survive contact with production; you know when *not* to build something; you can mentor.

**You are an expert if:** people bring you the problems nobody else can solve; you have deep, unusual knowledge of at least one area; you shape what your organisation builds, not just how.

### Concrete tests you can run on yourself
1. **The blank-file test.** Sit down with no internet and write a working HTTP server, a hash map and a binary search that handles the empty case. If you cannot, your fundamentals are thinner than you think.
2. **The explanation test.** Explain virtual memory to a smart non-programmer in five minutes. Explain TCP's three-way handshake and why it exists. If you cannot explain it simply, you do not understand it.
3. **The debugging test.** Take a bug in an unfamiliar open-source project, reproduce it, find the root cause and write a patch. Time yourself. Under a day means competent.
4. **The estimation test.** How long does an L1 hit take? A DRAM access? A datacentre round trip? A disk seek? An engineer who cannot estimate these cannot reason about performance.
5. **The review test.** Read a pull request in a language you use and write three substantive comments that are about correctness or design, not style. If you can only find style issues, you are not reading deeply enough.
6. **The market test.** Apply for jobs a level above where you think you are and see what the interviews reveal. Rejection is expensive information but it is *information*, and it is more reliable than introspection.

### Warning signs to act on
- **You have not finished anything in three months.** Finish something small immediately, even badly. Completion is a skill and it atrophies.
- **You are collecting courses rather than shipping projects.** Course completion certificates convince nobody. Cap yourself at one course at a time and require an artefact from each.
- **You avoid a whole area** (concurrency, maths, front-end, hardware). That avoidance is where your next big gain is.
- **You cannot explain your own code from three months ago.** Write more documentation and simpler code.
- **You are optimising your CV instead of your ability.** The market corrects this quickly and unpleasantly.

## If you only have twelve months

Halve it by taking the highest-density subset and accepting that breadth suffers:

- Months 1–4 → **Months 1–3 of this plan compressed**: Missing Semester, all of Nand to Tetris Part I, C to K&R chapter 8, and `malloc`.
- Months 5–6 → **DS&A** (Skiena, Roughgarden Part 1) with everything implemented in C.
- Months 7–8 → **OSTEP + xv6 labs + a shell**. Skip the from-scratch kernel; the xv6 labs carry most of the signal.
- Months 9–10 → **CS 144's TCP** and *Crafting Interpreters* (tree-walker only).
- Months 11–12 → **Ship one real application** and write about all of it.

You will be employable for backend and general software work. You will not be employable for hardware, compilers or architecture, which need the full path.

## What this plan deliberately omits

Front-end frameworks, mobile development, cloud certifications and DevOps tooling. Not because they are unimportant — a large share of paid work is exactly there — but because they are **fast to learn once the foundations exist and slow to learn without them**. An engineer who has written a kernel picks up React in a fortnight. The reverse is not true. Add them in month 22 as your specialisation, or after employment, where you will be paid to learn them.

## Sources

- [OSSU Computer Science curriculum](https://github.com/ossu/computer-science) — for the week/effort benchmarks used to calibrate this plan
- [Teach Yourself Computer Science](https://teachyourselfcs.com/) — the 100–200 h per subject benchmark
- [Nand to Tetris — course and 12 projects](https://www.nand2tetris.org/course)
- [Operating Systems: Three Easy Pieces (free)](https://pages.cs.wisc.edu/~remzi/OSTEP/)
- [Crafting Interpreters (free)](https://craftinginterpreters.com/)
- [2025 Stack Overflow Developer Survey — Work](https://survey.stackoverflow.co/2025/work)

## Open questions

- Course identifiers (MIT 6.1810, MIT 6.5840, Stanford CS 144, CMU 15-445, Berkeley CS 61C) are stated from general knowledge; **individual course pages were not fetched** and numbering changes over time. Verify against the current university catalogue.
- The 15–20 h/week and 1,600–2,000 h totals are this file's synthesis, calibrated against the OSSU and Teach Yourself CS figures, not an independently sourced estimate.
- The self-assessment rubric is a practitioner's framework, not a validated instrument.
- Hiring-market claims ("almost nobody who has written a kernel is unemployable in systems work") are experience-based judgements, **not** survey-backed — treat as opinion.
