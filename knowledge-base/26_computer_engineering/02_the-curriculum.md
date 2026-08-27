---
id: compeng.curriculum
title: The complete sequenced computer engineering curriculum
domain: 26_computer_engineering
tags: [curriculum, self-study, ossu, teach-yourself-cs, nand2tetris, algorithms, operating-systems, compilers, networks, databases, prerequisites]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Open Source Society University — Computer Science curriculum", url: "https://github.com/ossu/computer-science", publisher: "OSSU", accessed: 2026-08-25}
  - {title: "Teach Yourself Computer Science", url: "https://teachyourselfcs.com/", publisher: "Bradfield School of Computer Science", accessed: 2026-08-25}
  - {title: "From Nand to Tetris — course", url: "https://www.nand2tetris.org/course", publisher: "Nisan & Schocken", accessed: 2026-08-25}
  - {title: "Operating Systems: Three Easy Pieces", url: "https://pages.cs.wisc.edu/~remzi/OSTEP/", publisher: "Arpaci-Dusseau Books / University of Wisconsin–Madison", accessed: 2026-08-25}
related: [compeng.overview, compeng.learning_plan, compeng.books_papers, compeng.machine_level]
unit_system: SI
---

# The complete sequenced computer engineering curriculum

**Summary.** This is a single sequenced path from zero to employable competence, mapped to real books, real free courses and a proof-of-competence project per subject. It draws on three published curricula — Nand to Tetris, Teach Yourself CS and OSSU — and reconciles them into one order. The honest total is roughly **1,600–2,400 hours** of focused work, or 18–30 months at 15–20 hours a week. Anyone promising less is selling something.

## Key facts

| Curriculum | Structure | Stated effort | Free? |
|---|---|---|---|
| **Nand to Tetris** | 12 projects, 2 parts | Part I 6 weeks @ 7–13 h/wk; Part II 6 weeks @ 12–18 h/wk (Coursera) | Yes, all materials at nand2tetris.org |
| **Teach Yourself CS** | 9 subjects, 1 book + 1 course each | **100–200 hours per subject** (900–1,800 h total) | Books mostly paid; courses free |
| **OSSU CS** | Intro → Core (8 areas) → Advanced → Final project | Intro 14 wks @ 6–10 h/wk; Core Programming 54 wks; Core Math 45 wks; Core Systems 30–38 wks; Core Theory 16 wks; Core Security 16 wks; Core Applications 28 wks; Core Ethics 16 wks; Final project 12–26 wks | Yes |

**Teach Yourself CS's nine subjects and canonical pairings** (each 100–200 h):

| Subject | Book | Course |
|---|---|---|
| Programming | *Structure and Interpretation of Computer Programs* | Brian Harvey's Berkeley CS 61A |
| Computer architecture | *Computer Systems: A Programmer's Perspective* | Berkeley CS 61C |
| Algorithms & data structures | *The Algorithm Design Manual* (Skiena) | Skiena's lectures |
| Mathematics for CS | *Mathematics for Computer Science* (Lehman, Leighton, Meyer) | MIT 6.042J (Leighton) |
| Operating systems | *Operating Systems: Three Easy Pieces* | Berkeley CS 162 |
| Computer networking | *Computer Networking: A Top-Down Approach* | Stanford CS 144 |
| Databases | *Readings in Database Systems* ("the Red Book") | Berkeley CS 186 (Hellerstein) |
| Languages & compilers | *Crafting Interpreters* (Nystrom) | Alex Aiken's compilers course |
| Distributed systems | *Designing Data-Intensive Applications* (Kleppmann) | MIT 6.824 |

> ⚠️ Teach Yourself CS's own abbreviated advice, if nine subjects is too many: read **two** books — *Computer Systems: A Programmer's Perspective* and *Designing Data-Intensive Applications*. It calls this "incredibly high return on time invested" for self-taught and bootcamp engineers. That advice is correct and should be the fallback if the full path stalls.

## The dependency graph

```
                    ┌──────────────────┐
                    │  Programming     │  ← start here, always
                    │  (a language +   │
                    │   problem solving│
                    └────────┬─────────┘
                             │
        ┌────────────────────┼─────────────────────┐
        ▼                    ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌────────────────┐
│ Discrete math │   │ Digital logic   │   │ Data structures│
│ + proofs      │   │ (Nand2Tetris I) │   │ & algorithms   │
└───┬───────┬───┘   └────────┬────────┘   └────────┬───────┘
    │       │                │                     │
    ▼       ▼                ▼                     │
┌────────┐ ┌───────────┐  ┌──────────────────┐    │
│ Linear │ │Probability│  │ Computer org &   │    │
│ algebra│ │& stats    │  │ architecture     │    │
└───┬────┘ └─────┬─────┘  └────────┬─────────┘    │
    │            │                 │              │
    │            │        ┌────────▼──────────┐   │
    │            │        │ Assembly / machine│   │
    │            │        │ language          │   │
    │            │        └────────┬──────────┘   │
    │            │                 │              │
    │            │        ┌────────▼──────────┐   │
    │            │        │ C & systems       │◄──┘
    │            │        │ programming       │
    │            │        └───┬──────────┬────┘
    │            │            │          │
    │            │      ┌─────▼────┐ ┌───▼──────┐
    │            │      │Operating │ │ Networks │
    │            │      │systems   │ └───┬──────┘
    │            │      └──┬────┬──┘     │
    │            │         │    │        │
    │            │  ┌──────▼─┐ ┌▼────────▼──────┐ ┌───────────┐
    │            │  │Databases│ │ Distributed   │ │ Compilers │
    │            │  └─────────┘ │ systems       │ └───────────┘
    │            │              └───────────────┘
    │            │
    │            └──────────────┐    ┌──────────────┐
    └──────────────────────────►│ ML │◄──┤ Graphics   │
                                └────┘   └────────────┘
                        (+ Security: cuts across everything)
```

Teach Yourself CS states the same prerequisites more tersely: study **computer architecture before operating systems or databases**, and master **networking and operating systems before distributed systems**.

## Subject by subject

### 1. Discrete mathematics and proof
**Prerequisites.** School algebra. Nothing else.
**Canonical book.** *Mathematics for Computer Science* — Lehman, Leighton & Meyer (MIT, free PDF). Covers proofs, induction, number theory, graph theory, counting, probability. This is the OSSU Core Math anchor (13 weeks, 5 h/wk) and the Teach Yourself CS pick.
**Best free course.** MIT 6.042J with Tom Leighton (OCW, full video).
**Alternative.** Rosen's *Discrete Mathematics and Its Applications* if you want more drilled exercises.
**Project that proves competence.** Write, in LaTeX or Markdown, correct proofs for: correctness of Euclid's algorithm by strong induction, the pigeonhole principle applied to hash collisions, and the counting argument for why not every file can be compressed. Then implement a small SAT solver (DPLL) — it forces logic to become mechanical.
**Time.** 100–150 h.

### 2. Linear algebra
**Prerequisites.** Discrete maths helps but is not required.
**Canonical book.** Gilbert Strang, *Introduction to Linear Algebra*. For a CS-flavoured treatment, the linear algebra chapters of Goodfellow/Bengio/Courville's *Deep Learning* (free online) are a good compressed reference.
**Best free course.** MIT 18.06 (Strang) on OCW. Watch 3Blue1Brown's *Essence of Linear Algebra* first — OSSU lists it in Advanced Math for exactly this reason. It builds geometric intuition in about four hours.
**Project.** Implement, from scratch and without a library: matrix multiply (then tile it and measure the cache effect), Gaussian elimination with partial pivoting, QR by Gram–Schmidt, and PCA on a real dataset. If you plan on graphics, add a 4×4 transform stack and a perspective projection.
**Time.** 80–120 h.

### 3. Probability and statistics
**Prerequisites.** Discrete maths (counting), some calculus for continuous distributions.
**Canonical book.** Blitzstein & Hwang, *Introduction to Probability* (free PDF). OSSU lists Harvard's Probability course in Advanced Math.
**Best free course.** Harvard Stat 110 (Blitzstein) — full video on YouTube, with a free problem-set bank.
**Project.** Build a Bloom filter and *derive* its false-positive rate, then verify empirically. Implement HyperLogLog and show the error bound holds. Write a Monte Carlo simulation of a queueing system (M/M/1) and compare against the analytic result — this is the bridge to performance engineering.
**Time.** 80–120 h.

### 4. Digital logic
**Prerequisites.** None. Start here in parallel with programming.
**Canonical book.** Harris & Harris, *Digital Design and Computer Architecture* (RISC-V edition) — the best single bridge from gates to a working processor.
**Best free course.** **Nand to Tetris Part I** — projects 1–6: Boolean logic, Boolean arithmetic, memory, machine language, computer architecture, assembler. Free at nand2tetris.org, taught at 400+ institutions.
**Project.** Complete Nand2Tetris projects 1–5: build an ALU, a RAM hierarchy and a working CPU out of NAND gates in the HDL simulator. Then repeat one block in real Verilog and simulate it in Verilator.
**Time.** 60–100 h for Nand2Tetris Part I; add 40 h for the Verilog repeat.

### 5. Computer organisation and architecture
**Prerequisites.** Digital logic, some C.
**Canonical books.** Two, and you need both eventually: Patterson & Hennessy, *Computer Organization and Design* (RISC-V edition) for the undergraduate treatment, and Hennessy & Patterson, *Computer Architecture: A Quantitative Approach* for the graduate one. Bryant & O'Hallaron's *Computer Systems: A Programmer's Perspective* (CS:APP) is the programmer-facing complement and is the Teach Yourself CS pick.
**Best free course.** Berkeley CS 61C ("Great Ideas in Computer Architecture") — lectures and labs public. OSSU routes through MIT's Computation Structures 1–3 in Advanced Systems.
**Project.** The CS:APP labs, all of them — Data Lab, Bomb Lab, Attack Lab, Cache Lab, Shell Lab, Malloc Lab, Proxy Lab. Malloc Lab alone (write a memory allocator) is worth a month. Then: build a 5-stage pipelined RISC-V RV32I core in Verilog and run a compiled C program on it.
**Time.** 150–250 h.

### 6. Assembly and machine language
**Prerequisites.** Computer organisation.
**Canonical book.** No single canon. CS:APP chapter 3 is the best treatment of x86-64 for programmers. For AArch64, Arm's *Architecture Reference Manual* plus Pyeatt & Ughetta's *ARM 64-bit Assembly Language*. For RISC-V, the free *RISC-V Reader* (Patterson & Waterman) and the official ratified specifications at riscv.org.
**Best free course.** Nand2Tetris project 4 (Hack machine language) for the concept; then CS 61C for real x86/RISC-V.
**Project.** Take a 20-line C function; compile it for x86-64, AArch64 and RISC-V; annotate all three listings line by line; explain every difference. Then hand-write a program in each that does something non-trivial (string reverse, a bubble sort, a recursive factorial) and verify it against the C version. Full worked example in `03_machine-level-language.md`.
**Time.** 60–100 h.

### 7. C and systems programming
**Prerequisites.** Any prior programming, plus computer organisation.
**Canonical book.** Kernighan & Ritchie, *The C Programming Language*, 2nd ed. — still the best 270 pages in the field, though it predates C99 and everything after. Pair it with Klemens' *21st Century C* for the modern toolchain and with the C23 standard's changes (`03` and `05` files cover these). For systems calls: Stevens & Rago, *Advanced Programming in the UNIX Environment*.
**Best free course.** CS:APP labs again; Berkeley CS 61C; MIT's *Missing Semester* (OSSU's CS Tools, 2 weeks @ 12 h/wk) for the surrounding toolchain.
**Project.** In order: (a) a `malloc` implementation; (b) a shell with pipes, redirection and job control; (c) a `grep` clone with a real regex engine you wrote; (d) a memory-mapped file-based key-value store. Every one of these appears in real interviews.
**Time.** 150–200 h.

### 8. Data structures and algorithms
**Prerequisites.** Programming, discrete maths.
**Canonical books.** Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms* (CLRS) is the reference — comprehensive, not a first read. Skiena's *The Algorithm Design Manual* is the better first book and is the Teach Yourself CS choice, because its "war stories" teach problem recognition. Sedgewick & Wayne's *Algorithms* (with the free Coursera course) is the gentlest.
**Best free course.** Tim Roughgarden's Stanford *Algorithms: Design and Analysis* Parts 1 and 2 — OSSU's Core Theory, 8 weeks each at 4–8 h/wk. Skiena's own lectures are freely posted.
**Project.** Implement from scratch, with tests and complexity analysis: a dynamic array, a hash map with open addressing *and* one with chaining (benchmark both), a red-black or AVL tree, a B-tree, a binary heap, Dijkstra with a Fibonacci heap, union-find with path compression, and a suffix array. Then solve ~150 problems across the standard interview corpus — not for its own sake, but because it makes recall automatic.
**Time.** 200–300 h. This is the single largest line item and the one most directly tested in hiring.

### 9. Operating systems
**Prerequisites.** C, computer architecture.
**Canonical book.** **Arpaci-Dusseau & Arpaci-Dusseau, *Operating Systems: Three Easy Pieces* (OSTEP)** — free forever in PDF, version 1.10 (November 2023), 57 chapters, security chapters by Peter Reiher. Organised as virtualisation (processes, scheduling, virtual memory), concurrency (threads, locks, condition variables, semaphores), and persistence (I/O, disks, RAID, filesystems, journaling, LFS, SSDs). OSSU allocates it 10–12 weeks at 6–10 h/wk. Silberschatz's *Operating System Concepts* ("the dinosaur book") and Tanenbaum's *Modern Operating Systems* are the alternative canons; Tanenbaum is more opinionated and more readable, Silberschatz more exhaustive.
**Best free course.** Berkeley CS 162 (Teach Yourself CS's pick) or MIT 6.1810 (formerly 6.828), whose xv6 labs are the best OS labs in existence.
**Project.** MIT 6.1810's xv6 labs end to end — you will implement system calls, page tables, a copy-on-write fork, threads, a lock-free allocator, and a filesystem. Then write your own kernel that boots on real hardware or QEMU: bootloader, protected/long mode, interrupt handling, a scheduler, virtual memory, a simple filesystem. This is the flagship portfolio project.
**Time.** 200–300 h including the kernel.

### 10. Computer networks
**Prerequisites.** C, OS basics.
**Canonical book.** Kurose & Ross, *Computer Networking: A Top-Down Approach* — the Teach Yourself CS and OSSU pick (OSSU: 8 weeks @ 4–12 h/wk via the UMass course). Tanenbaum's *Computer Networks* is the bottom-up alternative. For implementation depth, Stevens' *TCP/IP Illustrated Vol. 1*.
**Best free course.** **Stanford CS 144**, whose labs have you build a working TCP implementation in C++ that interoperates with the real internet. This is the best networking course available anywhere, free.
**Project.** CS 144's TCP stack. Then: write a DNS resolver from scratch over UDP; write an HTTP/1.1 server with keep-alive and chunked encoding; capture and hand-decode an entire TLS 1.3 handshake in Wireshark.
**Time.** 120–180 h.

### 11. Databases
**Prerequisites.** Data structures, OS (for storage and concurrency), discrete maths (for relational algebra).
**Canonical books.** Hellerstein & Stonebraker's *Readings in Database Systems* (the Red Book, 5th ed., free online) is Teach Yourself CS's pick but is a paper collection, not a textbook — pair it with Ramakrishnan & Gehrke's *Database Management Systems* or Silberschatz/Korth/Sudarshan's *Database System Concepts*. Kleppmann's *Designing Data-Intensive Applications* is the modern bridge to distributed storage.
**Best free course.** **CMU 15-445/645 Intro to Database Systems** (Andy Pavlo) — all lectures and assignments public, and the assignments have you build components of a real DBMS. CMU 15-721 (Advanced) follows. OSSU uses Stanford's three short database courses (2 weeks each @ 10 h/wk: modelling and theory, relational databases and SQL, semistructured data).
**Project.** Build a database. Minimum viable: a page-based storage manager, a buffer pool with LRU, a B+ tree index, a heap file, a SQL parser for a subset, a volcano-model executor, write-ahead logging and crash recovery. CMU 15-445's BusTub assignments give you the scaffold. Also: learn to read `EXPLAIN ANALYZE` output in PostgreSQL until query plans are legible.
**Time.** 150–250 h.

### 12. Compilers and languages
**Prerequisites.** Data structures, assembly, formal languages from discrete maths.
**Canonical books.** Aho, Lam, Sethi & Ullman, *Compilers: Principles, Techniques and Tools* (the Dragon Book) is the reference and is heavy on parsing theory relative to modern practice. **Nystrom's *Crafting Interpreters* (free online) is the better first book** and is Teach Yourself CS's pick — it builds two complete interpreters, a tree-walker in Java and a bytecode VM in C. Appel's *Modern Compiler Implementation in ML/C/Java* is the middle ground; Cooper & Torczon's *Engineering a Compiler* is the best on optimisation.
**Best free course.** Alex Aiken's Stanford compilers course (edX/Coursera, in OSSU's Advanced Programming). Nand2Tetris Part II (projects 7–12) builds a VM, a compiler and an OS for the Jack language.
**Project.** Finish *Crafting Interpreters* both halves. Then write a compiler for a small statically-typed language that emits real machine code — either via LLVM IR or direct x86-64/RISC-V codegen — with a type checker, SSA-based optimisation passes and register allocation.
**Time.** 150–250 h.

### 13. Distributed systems
**Prerequisites.** Networks and operating systems — non-negotiable, per Teach Yourself CS.
**Canonical book.** **Kleppmann, *Designing Data-Intensive Applications*** — the most important practitioner book of the last decade. Supplement with the original papers (see `07_essential-books-and-papers.md`): Lamport's *Time, Clocks*, Paxos, Raft, MapReduce, GFS, Bigtable, Dynamo.
**Best free course.** **MIT 6.824 / 6.5840** — lectures on YouTube, labs public. The labs are in Go and build a working Raft implementation and a fault-tolerant sharded key-value store.
**Project.** MIT 6.824 labs 1–4. Then run your Raft implementation under a fault injector and show it survives partitions; better still, model it in TLA+ and check the safety property.
**Time.** 150–250 h.

### 14. Computer security
**Prerequisites.** C, assembly, OS, networks. Security is a *capstone*, not an entry point.
**Canonical books.** Anderson's *Security Engineering* (3rd ed., free chapters online) for the systems view; *The Art of Software Security Assessment* for code auditing; *Hacking: The Art of Exploitation* for the hands-on introduction; Ferguson/Schneier/Kohno's *Cryptography Engineering* for applied crypto.
**Best free course.** OSSU's Core Security is 16 weeks combining RIT's *Cybersecurity Fundamentals* (8 wks @ 10–12 h/wk), *Principles of Secure Coding*, *Identifying Security Vulnerabilities*, and one language-specific vulnerability course. For offensive depth, pwn.college (Arizona State, free) and picoCTF are better.
**Project.** Solve a full CTF category — exploit a stack overflow with ASLR and NX enabled (ROP), write a heap exploit, break a deliberately weakened crypto implementation. Then flip sides: audit a real open-source C project and file a genuine bug.
**Time.** 120–200 h.

### 15. Computer graphics
**Prerequisites.** Linear algebra (real fluency), C++ or Rust.
**Canonical books.** Marschner & Shirley, *Fundamentals of Computer Graphics* for the survey; Pharr, Jakob & Humphreys, *Physically Based Rendering* (free online, 4th ed.) for rendering; *Real-Time Rendering* for the game/engine view.
**Best free course.** OSSU uses UC San Diego's *Computer Graphics* (6 wks @ 12 h/wk). Better: Shirley's free *Ray Tracing in One Weekend* series, then TU Wien's *Rendering* lectures, then the Vulkan tutorial.
**Project.** A software rasteriser (no GPU) that draws a textured, z-buffered, perspective-correct mesh. Then a path tracer with importance sampling. Then a Vulkan or WebGPU renderer with a deferred pipeline.
**Time.** 120–200 h.

### 16. Machine learning
**Prerequisites.** Linear algebra, probability, calculus, Python.
**Canonical books.** Bishop's *Pattern Recognition and Machine Learning* or Hastie/Tibshirani/Friedman's *Elements of Statistical Learning* (free PDF) for classical ML; Goodfellow/Bengio/Courville's *Deep Learning* (free online) for the foundations; Prince's *Understanding Deep Learning* (free) for the modern treatment.
**Best free course.** OSSU uses the DeepLearning.AI *Machine Learning Specialization* (11 wks @ 9 h/wk). For engineers, Karpathy's *Neural Networks: Zero to Hero* — build backpropagation and then a GPT from scratch — is more valuable per hour than any survey course.
**Project.** Implement autodiff and a small neural net library from scratch in NumPy, train it on MNIST. Then implement a transformer from scratch and train a character-level language model. Then optimise the inference loop and measure it.
**Time.** 150–250 h.

## Reconciling the three curricula

- **Do Nand to Tetris first, always.** Six to twelve weeks, and it permanently removes the "computers are magic" reflex. Part I before computer organisation; Part II can run alongside compilers.
- **Use Teach Yourself CS as the spine** if you already program. Nine subjects, 100–200 h each, canonical book plus course — it is the highest signal-to-noise plan published.
- **Use OSSU if you need external structure and a full degree equivalent**, or if you want the maths, ethics and breadth a degree provides. It is slower (its Core alone runs well past two years at a part-time pace) but nothing is missing.
- **Skip nothing in the systems column.** Architecture → assembly → C → OS → networks → distributed systems is the load-bearing wall of this entire domain. Theory can be deferred; systems cannot.

## Sources

- [OSSU Computer Science curriculum](https://github.com/ossu/computer-science)
- [Teach Yourself Computer Science](https://teachyourselfcs.com/)
- [Nand to Tetris — course and 12 projects](https://www.nand2tetris.org/course)
- [Operating Systems: Three Easy Pieces (free)](https://pages.cs.wisc.edu/~remzi/OSTEP/)

## Open questions

- Course numbering for Berkeley CS 61A/61B/61C/162/186, Stanford CS 144, CMU 15-445 and MIT 6.1810/6.5840 is stated from the curricula above and from general knowledge; the individual course pages were **not** fetched for this file. Numbers change (MIT 6.828 → 6.1810, 6.824 → 6.5840). Verify against the current university catalogue before enrolling.
- Book editions are given where the curricula name them. Where an edition is not stated it was not verified.
- Time estimates outside the OSSU and Teach Yourself CS figures are the author's synthesis, not sourced.
