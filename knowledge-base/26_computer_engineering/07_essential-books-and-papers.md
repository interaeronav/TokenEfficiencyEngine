---
id: compeng.books_papers
title: Essential books and landmark papers, annotated
domain: 26_computer_engineering
tags: [books, papers, sicp, clrs, knuth, tanenbaum, ostep, dragon-book, csapp, ddia, mapreduce, raft, paxos, transformer, reading-list]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Structure and Interpretation of Computer Programs, 2nd ed. (open access, CC BY-SA)", url: "https://mitpress.mit.edu/9780262510875/structure-and-interpretation-of-computer-programs/", publisher: "MIT Press", accessed: 2026-08-25}
  - {title: "Operating Systems: Three Easy Pieces (free, v1.10, Nov 2023)", url: "https://pages.cs.wisc.edu/~remzi/OSTEP/", publisher: "Arpaci-Dusseau Books", accessed: 2026-08-25}
  - {title: "Crafting Interpreters (free full text)", url: "https://craftinginterpreters.com/", publisher: "Robert Nystrom", accessed: 2026-08-25}
  - {title: "Teach Yourself Computer Science — canonical books", url: "https://teachyourselfcs.com/", publisher: "Bradfield School of Computer Science", accessed: 2026-08-25}
  - {title: "From Nand to Tetris", url: "https://www.nand2tetris.org/", publisher: "Nisan & Schocken / MIT Press", accessed: 2026-08-25}
  - {title: "ACM A. M. Turing Award laureates", url: "https://en.wikipedia.org/wiki/Turing_Award", publisher: "Wikipedia", accessed: 2026-08-25}
related: [compeng.curriculum, compeng.great_figures, compeng.learning_plan]
unit_system: SI
---

# Essential books and landmark papers, annotated

**Summary.** An annotated register of the books worth owning and the papers worth reading in the original, with an honest note on each about who it is for and whether you will actually finish it. Free and open-access items are marked **FREE** and linked. Nothing here is included for prestige — several famous books are marked as references you should consult rather than read.

## Key facts — the free canon

| Work | Status | Where |
|---|---|---|
| *Structure and Interpretation of Computer Programs*, 2nd ed. (1996) | **Open access, CC BY-SA** per MIT Press | mitpress.mit.edu / author-hosted edition |
| *Operating Systems: Three Easy Pieces*, v1.10 (Nov 2023) | **Free PDF, "is and will always be free"** | pages.cs.wisc.edu/~remzi/OSTEP/ |
| *Crafting Interpreters* | **Free full text** — "Read the whole book for free. Really." | craftinginterpreters.com |
| *The Elements of Computing Systems* (Nand2Tetris) | Book is paid (MIT Press); **all course materials free** | nand2tetris.org |
| *Mathematics for Computer Science* (Lehman, Leighton, Meyer) | Free PDF, MIT OCW | ocw.mit.edu |
| *Physically Based Rendering*, 4th ed. | Free online | pbr-book.org |
| *The Elements of Statistical Learning* | Free PDF | Stanford |
| *Deep Learning* (Goodfellow, Bengio, Courville) | Free HTML | deeplearningbook.org |
| *Reinforcement Learning: An Introduction*, 2nd ed. | Free PDF | Sutton's page |
| *Security Engineering*, 3rd ed. (Anderson) | Chapters free | Cambridge / author's page |
| *Communicating Sequential Processes* (Hoare) | Free PDF | usingcsp.com |

## Part 1 — The books

### The two-book shortcut
Teach Yourself CS's own advice, and it is correct: if you read only two, read **Bryant & O'Hallaron, *Computer Systems: A Programmer's Perspective*** and **Kleppmann, *Designing Data-Intensive Applications***. Between them they cover the machine beneath your code and the systems above it, and both are written to be finished.

### Foundations and programming

**Abelson & Sussman, *Structure and Interpretation of Computer Programs* (SICP), 2nd ed., MIT Press 1996 — FREE, CC BY-SA.** The most intellectually serious introductory book in computing. It is not about Scheme; it is about abstraction — procedural abstraction, data abstraction, state and time, metalinguistic abstraction (you build interpreters for the language you are writing in), and register machines. It is genuinely hard and many people bounce off it. The exercises are the book; skipping them wastes it. **Read if** you want to think differently about programs. **Skip if** you need to be employable in six months.

**Nisan & Schocken, *The Elements of Computing Systems* (Nand2Tetris), MIT Press.** Twelve projects from a NAND gate to a working computer running Tetris: Boolean logic, arithmetic, memory, machine language, computer architecture, assembler (Part I); then VM, high-level language, two-stage compiler, OS (Part II). Course materials are free. **The single best cure for treating computers as magic.** Do this first.

**Petzold, *Code: The Hidden Language of Computer Hardware and Software*, 2nd ed. (2022).** Builds from Morse code and Braille through relays, logic gates, adders and memory to a working computer, with no prerequisites at all. The gentlest possible route to the same insight Nand2Tetris delivers with labour. Give it to anyone who asks how computers work.

**Kernighan & Ritchie, *The C Programming Language*, 2nd ed. (1988).** 270 pages, no filler, written by the people who made the thing. It predates C99 and everything after, so pair it with a modern reference — but as a model of technical writing it has never been surpassed. The exercises are excellent.

**Bryant & O'Hallaron, *Computer Systems: A Programmer's Perspective* (CS:APP).** The book that connects your source code to the machine: data representation, machine-level code, processor architecture, optimisation, the memory hierarchy, linking, exceptional control flow, virtual memory, I/O, networking and concurrency. Its lab assignments (Data, Bomb, Attack, Cache, Shell, Malloc, Proxy) are the best set of programming exercises in the field. **If you do one thing from this file, do the CS:APP labs.**

### Algorithms

**Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms* (CLRS), 4th ed. (2022).** The reference. Comprehensive, rigorous, pseudocode-based, ~1,300 pages. It is a book to consult, not to read cover to cover, and treating it as the latter is why most copies stop at chapter 6.

**Skiena, *The Algorithm Design Manual*, 3rd ed. (2020).** Teach Yourself CS's choice, and the better *first* book. Part I teaches design; Part II is a catalogue of problems with advice on which algorithm applies. The "war stories" — real consulting problems and how they were solved — teach the skill CLRS does not: recognising which problem you actually have.

**Sedgewick & Wayne, *Algorithms*, 4th ed.** The gentlest of the three, in Java, with an excellent free Coursera course and outstanding visualisations. Best if CLRS feels like a wall.

**Knuth, *The Art of Computer Programming*, Vols 1–4B.** Begun 1962, still unfinished; Knuth won the 1974 Turing Award largely for it. Exhaustive, mathematically deep, and written in the MIX/MMIX assembly language of a hypothetical machine. **Almost nobody reads it end to end and you probably should not try.** Own Volume 1, read chapter 1, and consult the rest when you need the definitive treatment of something. Bill Gates's remark that anyone who reads it all should send him a résumé is quoted constantly and acted on approximately never.

### Systems

**Arpaci-Dusseau & Arpaci-Dusseau, *Operating Systems: Three Easy Pieces* (OSTEP) — FREE.** Version 1.10, November 2023, 57 chapters, security chapters by Peter Reiher. Three parts: virtualisation (processes, scheduling, virtual memory), concurrency (threads, locks, condition variables, semaphores, bugs), persistence (I/O, disks, RAID, filesystems, journaling, LFS, SSDs, integrity). Short chapters, conversational, with homework simulators. **The best OS book, and free.**

**Tanenbaum & Bos, *Modern Operating Systems*, 4th ed.** More opinionated and more readable than Silberschatz, with real case studies (Linux, Windows, Android). Tanenbaum also wrote MINIX, which is what Linus Torvalds was using when he started Linux — and the Tanenbaum–Torvalds debate on microkernels versus monolithic kernels is worth reading as a historical document.

**Silberschatz, Galvin & Gagne, *Operating System Concepts* ("the dinosaur book"), 10th ed.** The exhaustive university standard. Use as a reference rather than a read-through.

**Kurose & Ross, *Computer Networking: A Top-Down Approach*, 8th ed.** Starts at HTTP and works down to the physical layer, which is pedagogically the right order for software people. Teach Yourself CS's and OSSU's choice.

**Tanenbaum & Wetherall, *Computer Networks*, 6th ed.** The bottom-up alternative, stronger on the link and physical layers.

**Stevens, *TCP/IP Illustrated, Vol. 1*, 2nd ed. (Fall & Stevens).** Packet traces on every page. This is the book that makes TCP concrete rather than described. Volume 2 walks the BSD implementation source; Volume 3 covers T/TCP and HTTP.

**Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*, 6th ed.** The graduate architecture text, from the joint 2017 Turing laureates. Pipelining, ILP, memory hierarchy, thread-level parallelism, data-level parallelism, warehouse-scale computing, and — in recent editions — domain-specific accelerators.

**Patterson & Hennessy, *Computer Organization and Design*, RISC-V edition.** The undergraduate companion. Read this one first. Its rewrite around RISC-V is why a student in 2026 learns architecture in RISC-V rather than MIPS.

**Harris & Harris, *Digital Design and Computer Architecture*, RISC-V edition.** The best bridge from transistors and gates through SystemVerilog/VHDL to a working single-cycle and pipelined processor.

### Databases and data

**Kleppmann, *Designing Data-Intensive Applications*, O'Reilly (2017; 2nd edition in progress).** The most useful practitioner book of the last decade. Part I: data models, storage engines (B-trees vs LSM-trees), encoding. Part II: replication, partitioning, transactions and isolation levels, the trouble with distributed systems, consistency and consensus. Part III: batch and stream processing. Its distinguishing virtue is that every claim is footnoted to the primary paper — it is simultaneously a book and a reading list. **Read it twice.**

**Hellerstein & Stonebraker (eds.), *Readings in Database Systems* ("the Red Book"), 5th ed. — FREE.** A curated paper collection with opinionated editorial commentary. Not a textbook; read it after you have a textbook's grounding.

**Ramakrishnan & Gehrke, *Database Management Systems*, 3rd ed.** or **Silberschatz, Korth & Sudarshan, *Database System Concepts*, 7th ed.** — either serves as the textbook the Red Book presumes.

### Languages and compilers

**Nystrom, *Crafting Interpreters* — FREE, full text online.** Builds a complete language twice: first a tree-walking interpreter, then a bytecode virtual machine with its own garbage collector. Every line of code is in the book and explained. It is the rare technical book that is genuinely enjoyable, and it is the reason a great many people who thought compilers were beyond them have now written one.

**Aho, Lam, Sethi & Ullman, *Compilers: Principles, Techniques and Tools* (the Dragon Book), 2nd ed.** The reference, from two 2020 Turing laureates. Extremely strong on lexing and parsing theory, weaker on the optimisation and code generation that dominate modern compiler work. Read chapters 1–6 and then move to something else.

**Cooper & Torczon, *Engineering a Compiler*, 3rd ed.** Better than the Dragon Book on optimisation, SSA and register allocation, and more representative of what compiler engineers actually do.

**Appel, *Modern Compiler Implementation in ML / C / Java*.** A complete compiler in one book, with a real project structure.

**Pierce, *Types and Programming Languages* (TAPL).** The standard text on type theory: lambda calculus, subtyping, polymorphism, recursive types. Difficult, and the foundation of everything interesting happening in language design.

### Practice and craft

**Brooks, *The Mythical Man-Month*, 20th anniversary ed. (1995).** Brooks's law, conceptual integrity, the second-system effect, the surgical team, and "No Silver Bullet" (included in this edition). Written about a 1960s mainframe project; every observation still applies. Turing Award 1999.

**Hunt & Thomas, *The Pragmatic Programmer*, 20th anniversary ed. (2019).** Short, practical, aphoristic: DRY, orthogonality, tracer bullets, rubber-duck debugging, "don't live with broken windows". The 20th-anniversary edition is a substantial rewrite, not a reprint. Best read early in a career.

**McConnell, *Code Complete*, 2nd ed. (2004).** 900 pages on construction: variables, routines, defensive programming, refactoring, and — unusually — actual empirical data on what practices reduce defect rates. Dated in its examples, sound in its substance. A reference, not a novel.

**Martin, *Clean Architecture* (2017) and *Clean Code* (2008).** Widely read, widely prescribed, and genuinely contested — there is a substantial body of criticism arguing that *Clean Code*'s advice on function decomposition produces worse code in practice. **Read them, then read the criticism.** The dependency-inversion and boundary arguments in *Clean Architecture* are the more durable part.

**Kernighan & Pike, *The Practice of Programming* (1999).** 250 pages on style, algorithms, design, debugging, testing, portability and notation. The most useful-per-page book on this list.

**Fowler, *Refactoring*, 2nd ed. (2018).** The catalogue of behaviour-preserving transformations, and the argument that refactoring is a disciplined technique rather than a euphemism for rewriting.

**Beck, *Test-Driven Development: By Example* (2002).** The primary source. Read it before joining the argument about TDD.

### Security, graphics, ML

- **Anderson, *Security Engineering*, 3rd ed. — chapters FREE.** The definitive systems-security book: not just cryptography but banking, access control, physical security, economics of security and how real attacks work.
- **Ferguson, Schneier & Kohno, *Cryptography Engineering*.** How to use cryptography without inventing your own disaster.
- **Marschner & Shirley, *Fundamentals of Computer Graphics*, 5th ed.** The survey.
- **Pharr, Jakob & Humphreys, *Physically Based Rendering*, 4th ed. — FREE online.** Literate programming: the book *is* the renderer. Won a Scientific and Technical Academy Award.
- **Akenine-Möller et al., *Real-Time Rendering*, 4th ed.** The GPU/game-engine counterpart.
- **Goodfellow, Bengio & Courville, *Deep Learning* — FREE.** The foundations text, from two 2018 Turing laureates.
- **Prince, *Understanding Deep Learning* (2023) — FREE.** The best modern replacement, covering transformers and diffusion models.
- **Sutton & Barto, *Reinforcement Learning: An Introduction*, 2nd ed. — FREE.** From the 2024 Turing laureates.
- **Hastie, Tibshirani & Friedman, *The Elements of Statistical Learning* — FREE.** Classical statistical ML, rigorously.

## Part 2 — The landmark papers

Reading primary sources is a habit worth building. Most of these are shorter and clearer than the textbooks that summarise them.

### Theory
- **Turing, "On Computable Numbers, with an Application to the Entscheidungsproblem" (1936).** Turing machines, the universal machine, undecidability. **FREE** — public domain, widely mirrored.
- **Shannon, "A Mathematical Theory of Communication" (Bell System Technical Journal, 1948).** Information theory in one paper. **FREE** from Bell Labs' archives. Read it; it is remarkably approachable.
- **Cook, "The Complexity of Theorem-Proving Procedures" (1971)** and **Karp, "Reducibility Among Combinatorial Problems" (1972).** NP-completeness.
- **Valiant, "A Theory of the Learnable" (1984).** PAC learning.

### Languages and programming discipline
- **McCarthy, "Recursive Functions of Symbolic Expressions and Their Computation by Machine, Part I" (1960).** Lisp, and `eval` written in itself.
- **Dijkstra, "Go To Statement Considered Harmful" (CACM, 1968).** One page. The title was the editor's. **FREE.**
- **Hoare, "An Axiomatic Basis for Computer Programming" (1969).** Hoare logic; the beginning of program verification.
- **Backus, "Can Programming Be Liberated from the von Neumann Style?" (1977 Turing lecture).**
- **Liskov & Wing, "A Behavioral Notion of Subtyping" (1994).** The substitution principle, stated precisely.
- **Thompson, "Reflections on Trusting Trust" (1984 Turing lecture).** Four pages. **FREE.** The most quietly alarming thing in this file.

### Systems
- **Ritchie & Thompson, "The UNIX Time-Sharing System" (CACM, 1974).** **FREE.** Still the best short statement of the Unix design philosophy.
- **Saltzer, Reed & Clark, "End-to-End Arguments in System Design" (1984).** **FREE.** Why the internet is built the way it is. Arguably the single most important systems-design paper ever written.
- **Lampson, "Hints for Computer System Design" (1983).** **FREE.** Practical wisdom, densely packed.
- **Clark, "The Design Philosophy of the DARPA Internet Protocols" (1988).** **FREE.**
- **Cerf & Kahn, "A Protocol for Packet Network Intercommunication" (1974).** TCP.
- **Metcalfe & Boggs, "Ethernet: Distributed Packet Switching for Local Computer Networks" (1976).**

### Databases and distributed systems
- **Codd, "A Relational Model of Data for Large Shared Data Banks" (CACM, 1970).** **FREE.** Eleven pages; created the relational database industry. Turing Award 1981.
- **Gray, "The Transaction Concept: Virtues and Limitations" (1981).** ACID before the acronym.
- **Lamport, "Time, Clocks, and the Ordering of Events in a Distributed System" (CACM, 1978).** **FREE.** Happens-before, logical clocks. The most-cited paper in distributed systems. Turing Award 2013.
- **Lamport, "The Byzantine Generals Problem" (1982)** and **"The Part-Time Parliament" (1998)** / **"Paxos Made Simple" (2001).** Read *Paxos Made Simple* first; the 1998 paper's allegorical framing is famously impenetrable.
- **Ongaro & Ousterhout, "In Search of an Understandable Consensus Algorithm" (Raft, USENIX ATC 2014).** **FREE at raft.github.io.** Written explicitly because Paxos was too hard to teach or implement correctly — and it worked; almost every consensus implementation shipped since is Raft.
- **Dean & Ghemawat, "MapReduce: Simplified Data Processing on Large Clusters" (OSDI 2004)**; **Ghemawat, Gobioff & Leung, "The Google File System" (SOSP 2003)**; **Chang et al., "Bigtable: A Distributed Storage System for Structured Data" (OSDI 2006).** **All FREE from research.google.** The trio that created the big-data era — Hadoop and HDFS are direct reimplementations.
- **DeCandia et al., "Dynamo: Amazon's Highly Available Key-value Store" (SOSP 2007).** **FREE.** Consistent hashing, vector clocks, eventual consistency, quorum reads and writes. The source of Cassandra, Riak and DynamoDB.
- **Corbett et al., "Spanner: Google's Globally-Distributed Database" (OSDI 2012).** **FREE.** TrueTime, and externally consistent distributed transactions.
- **Brewer's CAP conjecture (2000)** and **Gilbert & Lynch's proof (2002)**; then **Brewer, "CAP Twelve Years Later" (2012)**, which corrects the popular misreading.

### Machine learning
- **Rumelhart, Hinton & Williams, "Learning representations by back-propagating errors" (Nature, 1986).**
- **LeCun et al., "Gradient-Based Learning Applied to Document Recognition" (1998).** CNNs, working, on real cheques.
- **Hochreiter & Schmidhuber, "Long Short-Term Memory" (1997).**
- **Krizhevsky, Sutskever & Hinton, "ImageNet Classification with Deep Convolutional Neural Networks" (NeurIPS 2012).** AlexNet — the result that started the deep-learning era.
- **Vaswani et al., "Attention Is All You Need" (NeurIPS 2017).** **FREE on arXiv (1706.03762).** The Transformer: self-attention, multi-head attention, positional encoding, no recurrence. Every large language model in existence descends from this eight-page paper. If you read one ML paper, read this one.
- **Sutton, "The Bitter Lesson" (2019).** **FREE.** An essay, not a paper, and arguably more influential than most papers.

### Cryptography and elsewhere
- **Diffie & Hellman, "New Directions in Cryptography" (1976).** **FREE.** Public-key cryptography. Turing Award 2015.
- **Rivest, Shamir & Adleman, "A Method for Obtaining Digital Signatures and Public-Key Cryptosystems" (1978).** RSA. Turing Award 2002.
- **Goldwasser, Micali & Rackoff, "The Knowledge Complexity of Interactive Proof Systems" (1985).** Zero-knowledge proofs. Turing Award 2012.
- **Nakamoto, "Bitcoin: A Peer-to-Peer Electronic Cash System" (2008).** **FREE at bitcoin.org.** Nine pages. Regardless of what one thinks of cryptocurrency, it is a genuinely novel combination of proof-of-work, a hash-linked chain and economic incentives to solve Byzantine agreement without a permissioned membership list — a problem the distributed-systems literature had treated as requiring known participants.

## How to actually read this list

1. **Nand2Tetris first.** Do the projects; do not read about them.
2. **CS:APP with the labs.** This is the spine.
3. **OSTEP, free, alongside the xv6 labs.**
4. **Skiena, then CLRS as a reference.**
5. **Kurose & Ross with Stanford CS 144's labs.**
6. **Crafting Interpreters, free, both halves.**
7. **Kleppmann, then the papers he footnotes.** This is the highest-leverage move on the whole list: DDIA is a curated reading list wearing a book's clothes.
8. **One paper a week, forever.** Twenty minutes, a printout, a pen. The compounding is enormous.

## Sources

- [SICP, 2nd ed. — MIT Press open access, CC BY-SA](https://mitpress.mit.edu/9780262510875/structure-and-interpretation-of-computer-programs/)
- [Operating Systems: Three Easy Pieces — free, v1.10 (Nov 2023)](https://pages.cs.wisc.edu/~remzi/OSTEP/)
- [Crafting Interpreters — free full text](https://craftinginterpreters.com/)
- [Teach Yourself Computer Science — canonical book choices](https://teachyourselfcs.com/)
- [From Nand to Tetris](https://www.nand2tetris.org/)
- [ACM Turing Award laureates](https://en.wikipedia.org/wiki/Turing_Award)

## Open questions

- **Editions and publication years** for most books here are from general knowledge; only SICP (2nd ed., 1996, MIT Press, CC BY-SA), OSTEP (v1.10, Nov 2023) and *Crafting Interpreters* were verified by fetch. Check the current edition before buying — CLRS 4th (2022), Skiena 3rd (2020) and *Real-Time Rendering* 4th are the most likely to have moved.
- **Free/paid status** was verified only for SICP, OSTEP and *Crafting Interpreters*. The other **FREE** marks are from general knowledge and are `needs-verification`; publisher terms change.
- Paper venues and years are stated from general knowledge. The high-confidence ones (Turing 1936, Shannon 1948, Codd CACM 1970, Lamport CACM 1978, Raft USENIX ATC 2014, Transformer NeurIPS 2017 / arXiv 1706.03762) are safe; verify the rest against the ACM Digital Library or the venue proceedings before citing.
- The *Crafting Interpreters* page confirmed free access but did not confirm the two-interpreter structure (Java tree-walker, C bytecode VM); that detail is from general knowledge.

