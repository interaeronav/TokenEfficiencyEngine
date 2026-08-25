---
id: compeng.great_figures
title: The significant figures of computing and what they actually contributed
domain: 26_computer_engineering
tags: [turing-award, history-of-computing, turing, von-neumann, shannon, dijkstra, knuth, lamport, liskov, hopper, ritchie, thompson, hinton, biographies]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "ACM A. M. Turing Award — list of laureates by year with citations", url: "https://en.wikipedia.org/wiki/Turing_Award", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "ACM A. M. Turing Award (award site)", url: "https://awards.acm.org/turing", publisher: "Association for Computing Machinery", accessed: 2026-08-25}
related: [compeng.books_papers, compeng.overview, compeng.machine_level]
unit_system: SI
---

# The significant figures of computing and what they actually contributed

**Summary.** Organised by contribution area rather than alphabetically, because the point is the *shape* of the field, not a roll call. Every ACM A. M. Turing Award year given here is verified against the ACM laureate list; where a figure has no Turing Award that is stated explicitly rather than glossed over. For each person, one or two works actually worth reading are named — not the complete bibliography, the thing you should put in front of your eyes.

## Key facts

- The **ACM A. M. Turing Award** has been given annually since **1966** (first laureate: Alan Perlis, "for influence in advanced computer programming techniques"). It is the field's highest honour, sometimes called the Nobel Prize of computing.
- **Alan Turing himself never received it** — he died in 1954, twelve years before the award was created in his name.
- The most recent laureate verified for this file is the **2024 award to Andrew Barto and Richard S. Sutton**, "for developing the conceptual and algorithmic foundations of reinforcement learning."
- Several of the most consequential figures in this file — **Shannon, von Neumann, Hopper, Stroustrup, Torvalds, Hamilton, Perlman, Katherine Johnson, Jean Bartik, Schmidhuber, Fei-Fei Li** — have **no Turing Award**. The award is a strong signal, not a complete map.

## Foundations of computation

**Alan Turing (1912–1954)** — *no Turing Award; the award is named for him.* Defined computation itself. "On Computable Numbers, with an Application to the Entscheidungsproblem" (1936) introduced the abstract machine that bears his name, the universal machine (the idea that one machine can simulate any other — the stored-program concept in mathematical form), and the undecidability of the halting problem. His Bletchley Park cryptanalysis shortened the Second World War. "Computing Machinery and Intelligence" (1950) posed the imitation game and effectively founded AI as a discipline.
**Read:** the 1936 paper (hard but foundational) and the 1950 paper (readable in an evening, and still the best entry to the philosophy of AI).

**John von Neumann (1903–1957)** — *no Turing Award (died 1957).* The "First Draft of a Report on the EDVAC" (1945) described the stored-program architecture — a single memory holding both instructions and data, a control unit, an ALU, and I/O — that every general-purpose computer since has followed. He also founded game theory (with Morgenstern), contributed to quantum mechanics, cellular automata and the Monte Carlo method. The First Draft's circulation under his name alone, over the objections of Eckert and Mauchly, remains a live controversy in the history of computing.
**Read:** the First Draft of a Report on the EDVAC (1945).

**Claude Shannon (1916–2001)** — *no Turing Award.* Two of the most important papers ever written. His MIT master's thesis, "A Symbolic Analysis of Relay and Switching Circuits" (1937), showed that Boolean algebra describes switching circuits — the mathematical basis of all digital design. "A Mathematical Theory of Communication" (1948) created information theory: entropy as a measure of information, the channel-capacity theorem, and the separation of source and channel coding. Every codec, modem, error-correcting code and compression algorithm descends from it.
**Read:** the 1948 paper. It is astonishingly clear.

**Stephen Cook** (Turing Award **1982**) — "The Complexity of Theorem-Proving Procedures" (1971) proved that satisfiability is NP-complete, creating the theory of NP-completeness and, with it, the P versus NP question.
**Read:** the 1971 paper, then Garey & Johnson's *Computers and Intractability*.

**Richard Karp** (Turing Award **1985**) — "Reducibility Among Combinatorial Problems" (1972) showed twenty-one natural problems are NP-complete, which turned Cook's theorem from a curiosity into the organising principle of algorithm design. Also the Rabin–Karp string search and the Hopcroft–Karp matching algorithm.
**Read:** the 1972 paper — it is short and it is why we say "that's NP-complete" instead of "that seems hard".

**Leslie Valiant** (Turing Award **2010**) — "A Theory of the Learnable" (1984) introduced the PAC (probably approximately correct) framework, giving machine learning a rigorous foundation. Also work on complexity of counting (#P) and parallel computation (the BSP model).
**Read:** "A Theory of the Learnable" (1984).

## Programming languages and their design

**John Backus** (Turing Award **1977**) — led the team that built **Fortran** (1957), the first widely used high-level language, and proved that a compiler could generate code competitive with hand-written assembly. Co-created Backus–Naur Form, the notation used to specify programming-language grammars ever since. His 1977 Turing lecture, "Can Programming Be Liberated from the von Neumann Style?", attacked the assignment statement and argued for functional programming decades before it was fashionable.
**Read:** the 1977 Turing lecture.

**John McCarthy** (Turing Award **1971**) — invented **Lisp** (1958), coined the term "artificial intelligence" (1955), invented garbage collection, and proposed time-sharing. "Recursive Functions of Symbolic Expressions and Their Computation by Machine, Part I" (1960) is the paper in which Lisp appears — including the eval function that is a metacircular interpreter, and the discovery that a language can be written in itself in a page.
**Read:** the 1960 paper.

**Niklaus Wirth** (Turing Award **1984**, "for developing innovative computer languages including EULER, ALGOL-W and Modula") — designed **Pascal**, Modula-2 and Oberon, and wrote *Algorithms + Data Structures = Programs* (1976), whose title is itself a contribution. Wirth's law — software slows down faster than hardware speeds up — has aged well. He was the great advocate of simplicity in language design, and of compilers small enough for one person to understand.
**Read:** *Algorithms + Data Structures = Programs*; then *Project Oberon* if you want to see one person build an entire OS, compiler and hardware design.

**C. A. R. (Tony) Hoare** (Turing Award **1980**) — invented **Quicksort** (1961); created **Hoare logic** (1969, "An Axiomatic Basis for Computer Programming"), the foundation of program verification; created **CSP** (Communicating Sequential Processes, 1978), which is the direct ancestor of Go's channels and occam; and introduced monitors for concurrency. In 2009 he called the null reference his "billion-dollar mistake".
**Read:** "An Axiomatic Basis for Computer Programming" (1969) and *Communicating Sequential Processes* (1985, free online).

**Bjarne Stroustrup** — *no Turing Award.* Created **C++** (from 1979, "C with Classes"; released 1985) with the explicit goal of zero-overhead abstraction, and shepherded it through four decades and six ISO standards. Whether one loves or resents C++, it runs a very large share of the world's performance-critical software.
**Read:** *The Design and Evolution of C++* (1994) — the best book ever written about *why* a language is the way it is. *A Tour of C++* for the language itself.

**Kenneth Iverson** (Turing Award **1979**) — created **APL**, the array language, and with it the idea that notation is a tool of thought. His Turing lecture, "Notation as a Tool of Thought" (1979), is the argument.
**Read:** "Notation as a Tool of Thought".

**Alan Kay** (Turing Award **2003**) — Smalltalk, the Dynabook concept, and the coining of "object-oriented programming" — by which he meant message passing and late binding, not classes and inheritance. Central to the Xerox PARC work that produced the modern GUI.
**Read:** "The Early History of Smalltalk" (1993).

**Frances Allen** (Turing Award **2006**, "for pioneering contributions to the theory and practice of optimizing compiler techniques") — the **first woman to win the Turing Award**. Her work on control-flow analysis, data-flow analysis and program optimisation is the theoretical basis of every optimising compiler in use.
**Read:** "Control Flow Analysis" (1970) and "A Program Data Flow Analysis Procedure" (with Cocke, 1976).

**Alfred Aho and Jeffrey Ullman** (Turing Award **2020**) — with Lam and Sethi, wrote *Compilers: Principles, Techniques and Tools* (the Dragon Book), the standard compiler text for four decades. Aho also co-created AWK and the algorithms behind `grep` and `egrep`.
**Read:** the Dragon Book, chapters 1–6.

## Programming discipline and methodology

**Edsger W. Dijkstra** (Turing Award **1972**) — shortest-path algorithm (1959); semaphores and the dining-philosophers problem; the THE multiprogramming system; structured programming; guarded commands; self-stabilisation in distributed systems. "Go To Statement Considered Harmful" (1968, CACM) is the most famous one-page letter in computing — and the title was the editor's, not his. His EWD manuscripts, hand-written and circulated for decades, are a body of prose unlike anything else in the field.
**Read:** "Go To Statement Considered Harmful" (1968); "The Humble Programmer" (1972 Turing lecture); a handful of EWDs.

**Donald Knuth** (Turing Award **1974**) — *The Art of Computer Programming*, begun in 1962 and still in progress, is the field's closest thing to a definitive reference. Created **TeX** and Metafont because he was dissatisfied with the typesetting of his own books, and in doing so fixed mathematical publishing permanently. Introduced literate programming, formalised asymptotic analysis for algorithms, co-created the Knuth–Morris–Pratt string search and LR parsing theory. "Premature optimization is the root of all evil" is his, and is almost always quoted without its qualifying sentence.
**Read:** TAOCP Volume 1 (at least chapter 1); "Computer Programming as an Art" (1974 Turing lecture); *Literate Programming*.

**Fred Brooks** (Turing Award **1999**) — managed IBM's System/360 and OS/360, and wrote *The Mythical Man-Month* (1975) about what went wrong. Brooks's law — adding people to a late software project makes it later — plus conceptual integrity, the second-system effect and the surgical team. "No Silver Bullet" (1986) distinguished essential from accidental complexity and argued that no single technique would give an order-of-magnitude productivity gain. Forty years later it holds up uncomfortably well.
**Read:** *The Mythical Man-Month* (20th anniversary edition, which includes "No Silver Bullet").

**Barbara Liskov** (Turing Award **2008**) — designed CLU, which introduced abstract data types, iterators, exception handling and parametric polymorphism — features now in every mainstream language. The **Liskov Substitution Principle** (from "A Behavioral Notion of Subtyping", Liskov & Wing, 1994) is the L in SOLID and the precise statement of what inheritance must preserve. Also foundational work on Byzantine fault tolerance (with Castro, "Practical Byzantine Fault Tolerance", 1999).
**Read:** "Programming with Abstract Data Types" (1974) and the 1994 subtyping paper.

## Operating systems and Unix

**Dennis Ritchie and Ken Thompson** (Turing Award **1983**, jointly) — created **Unix** at Bell Labs (1969 onwards); Ritchie created **C** (1972) to write it in, making the first portable operating system. Thompson also created the B language, the original `grep`, regular-expression search based on Thompson's construction, and later co-created Go and UTF-8 (with Rob Pike). His 1984 Turing lecture, "Reflections on Trusting Trust", describes a compiler backdoor that survives recompilation from clean source — still the most unsettling four pages in security.
**Read:** "The UNIX Time-Sharing System" (Ritchie & Thompson, 1974); "Reflections on Trusting Trust" (Thompson, 1984); *The C Programming Language* (Kernighan & Ritchie, 1978/1988).

**Brian Kernighan** — *no Turing Award.* Not a creator of C, but its greatest explainer, and the co-author of the books that taught the field to write: *The C Programming Language* (with Ritchie), *The Elements of Programming Style* (with Plauger), *The Practice of Programming* (with Pike), *The Unix Programming Environment* (with Pike). Co-created AWK (the K) and contributed to troff.
**Read:** K&R, then *The Practice of Programming* — the best short book on writing good code.

**Linus Torvalds** — *no Turing Award.* Created the **Linux kernel** (1991) and **Git** (2005). Linux runs essentially all of the world's servers, all Android devices and all of the top 500 supercomputers; Git is the version-control system of record for the entire industry. His contribution is as much about sustaining a distributed development process at unprecedented scale as about code.
**Read:** *Just for Fun* (2001) for the history; then the Linux kernel `Documentation/process/` directory, which is a genuine education in engineering culture.

**Fernando Corbató** (Turing Award **1990**) — CTSS and Multics; the origin of time-sharing, of the password, and of many ideas Unix inherited by reaction.

## Databases

**Edgar F. Codd** (Turing Award **1981**) — "A Relational Model of Data for Large Shared Data Banks" (CACM, 1970) proposed that data be stored in relations and queried by a declarative language grounded in relational algebra and calculus, independent of physical storage. Every relational database, and SQL itself, descends from this one paper. He also formulated normal forms and, later, the twelve rules by which he judged commercial systems (mostly harshly).
**Read:** the 1970 paper. Eleven pages that created a US$100bn+ industry.

**Jim Gray** (Turing Award **1998**) — transactions. ACID, two-phase locking, isolation levels, write-ahead logging, and recovery. *Transaction Processing: Concepts and Techniques* (with Reuter, 1992) is the reference.
**Read:** "The Transaction Concept: Virtues and Limitations" (1981).

**Michael Stonebraker** (Turing Award **2014**) — Ingres, Postgres (which became PostgreSQL), Vertica, VoltDB, C-Store. The most prolific *builder* in databases, and the loudest advocate of the argument that one size does not fit all.
**Read:** "The End of an Architectural Era" (2007) and *Readings in Database Systems* (the Red Book), which he co-edits.

**Charles Bachman** (Turing Award **1973**) — the Integrated Data Store and the network data model, the pre-relational paradigm Codd displaced. Worth knowing because the debate between navigational and declarative access recurs endlessly (see: NoSQL, then the return of SQL).

## Networks and the internet

**Vint Cerf and Robert Kahn** (Turing Award **2004**, jointly) — "A Protocol for Packet Network Intercommunication" (1974) introduced TCP, and the subsequent split into TCP and IP created the internet's layering. Their design choices — end-to-end principle, best-effort delivery, no per-connection state in the network — are why the internet scaled from four nodes to billions.
**Read:** the 1974 paper; Saltzer, Reed & Clark's "End-to-End Arguments in System Design" (1984); David Clark's "The Design Philosophy of the DARPA Internet Protocols" (1988).

**Tim Berners-Lee** (Turing Award **2016**) — invented the **World Wide Web** at CERN: URIs, HTTP and HTML, plus the first browser and server, and — decisively — the decision to release it royalty-free.
**Read:** "Information Management: A Proposal" (1989), the original memo; then *Weaving the Web* (1999).

**Robert Metcalfe** (Turing Award **2022**) — invented **Ethernet** at Xerox PARC (with David Boggs) and drove its standardisation and commercialisation. Ethernet won over every technically fancier LAN because it was cheap, simple and standardised.
**Read:** "Ethernet: Distributed Packet Switching for Local Computer Networks" (Metcalfe & Boggs, 1976).

**Radia Perlman** — *no Turing Award.* Invented the **Spanning Tree Protocol** (1985), which made bridged Ethernet networks possible at scale, and later TRILL. She has objected, publicly and often, to the "Mother of the Internet" label, on the grounds that no one person is. Her textbook *Interconnections* is the best book on bridging and routing ever written.
**Read:** *Interconnections: Bridges, Routers, Switches and Internetworking Protocols* (2nd ed.); and her algorhyme, the poem in which she stated the spanning-tree algorithm.

## Distributed systems

**Leslie Lamport** (Turing Award **2013**) — the most cited distributed-systems researcher alive. "Time, Clocks, and the Ordering of Events in a Distributed System" (1978) introduced the happens-before relation and logical clocks, and is the most-cited paper in the field. "The Byzantine Generals Problem" (1982) framed fault tolerance under arbitrary failure. "The Part-Time Parliament" (1998) introduced **Paxos**, in a form so obscure he later wrote "Paxos Made Simple" (2001) as an apology. He also created **LaTeX** and **TLA+**, the specification language now used at AWS, Microsoft and elsewhere to model-check real distributed protocols before implementing them.
**Read:** "Time, Clocks, and the Ordering of Events" (1978) — read it twice — then "Paxos Made Simple".

**Butler Lampson** (Turing Award **1992**) — the Alto personal computer, WYSIWYG editing, laser printing, Ethernet (with Metcalfe and Thacker), two-phase commit, and "Hints for Computer System Design" (1983), which is the best short piece of engineering advice in the literature.
**Read:** "Hints for Computer System Design".

## Computer architecture

**John Hennessy and David Patterson** (Turing Award **2017**, jointly, "for pioneering a systematic, quantitative approach to the design and evaluation of computer architectures") — Patterson led Berkeley RISC (and coined "RISC"), Hennessy led Stanford MIPS. Together they wrote the two textbooks that taught the field: *Computer Architecture: A Quantitative Approach* and *Computer Organization and Design*. Patterson also co-invented RAID and later championed RISC-V. Their 2018 Turing lecture, "A New Golden Age for Computer Architecture", argued that the end of Dennard scaling makes domain-specific architectures the future — a prediction the AI accelerator boom has confirmed.
**Read:** *Computer Organization and Design* first, then *Computer Architecture: A Quantitative Approach*; then the 2018 Turing lecture.

**Maurice Wilkes** (Turing Award **1967**) — built **EDSAC** (1949), one of the first stored-program computers, and invented **microprogramming**, the technique that lets a complex ISA be implemented over simple hardware — the reason CISC was ever practical.

**John Cocke** (Turing Award **1987**) — the IBM 801 project, the origin of RISC; and much of the foundational work on compiler optimisation with Frances Allen.

**William Kahan** (Turing Award **1989**) — the principal architect of **IEEE 754**, the floating-point standard that made numerical computing reproducible across machines. Every `double` you have ever used is his design.
**Read:** "How Java's Floating-Point Hurts Everyone Everywhere" (1998) — polemical, and instructive.

## Graphics

**Ivan Sutherland** (Turing Award **1988**) — **Sketchpad** (1963), his MIT PhD thesis, was the first interactive graphical interface: constraint-based drawing, object hierarchies, a light pen, zooming. Effectively the first CAD system, the first GUI, and the first object-oriented graphics system. Later built the first head-mounted display and co-founded Evans & Sutherland.
**Read:** the Sketchpad thesis, or watch the 1963 demonstration film.

**Edwin Catmull and Pat Hanrahan** (Turing Award **2019**, jointly) — Catmull invented texture mapping, the **Z-buffer**, and Catmull–Clark subdivision surfaces, then co-founded **Pixar** and led it and Disney Animation. Hanrahan was a founding Pixar employee, architected **RenderMan**, and later created the shading-language tradition that leads to modern GPU shaders.
**Read:** Catmull's *Creativity, Inc.* (2014) for the management story; the RenderMan shading-language paper (Hanrahan & Lawson, 1990) for the technical one.

## Cryptography and security

**Whitfield Diffie and Martin Hellman** (Turing Award **2015**, jointly) — "New Directions in Cryptography" (1976) invented **public-key cryptography**, digital signatures and the Diffie–Hellman key exchange, solving the key-distribution problem that had constrained cryptography for millennia. (Ralph Merkle's contribution is widely acknowledged; he shares no Turing Award.)
**Read:** "New Directions in Cryptography" (1976). It reads like a manifesto because it is one.

**Ron Rivest, Adi Shamir and Leonard Adleman** (Turing Award **2002**, jointly) — "A Method for Obtaining Digital Signatures and Public-Key Cryptosystems" (1978) turned Diffie–Hellman's idea into the first practical public-key cryptosystem, **RSA**. Rivest also created MD5, RC4 and RC5 and co-authored CLRS; Shamir created secret sharing and differential cryptanalysis.
**Read:** the 1978 RSA paper.

**Shafi Goldwasser and Silvio Micali** (Turing Award **2012**, jointly) — made cryptography a rigorous science. "Probabilistic Encryption" (1984) defined semantic security and showed that deterministic encryption cannot be secure. With Rackoff they introduced **zero-knowledge proofs** (1985) — a way to prove you know something without revealing it — which is now the basis of an entire industry in verifiable computation and privacy-preserving systems.
**Read:** "The Knowledge Complexity of Interactive Proof Systems" (1985).

## Artificial intelligence and machine learning

**Geoffrey Hinton, Yann LeCun and Yoshua Bengio** (Turing Award **2018**, jointly, "for conceptual and engineering breakthroughs that have made deep neural networks a critical component of computing") — Hinton co-authored the backpropagation paper (Rumelhart, Hinton & Williams, 1986), invented Boltzmann machines and dropout, and co-authored AlexNet (2012), the result that started the deep-learning era. LeCun created **convolutional neural networks** and LeNet, and demonstrated them on real cheque-reading systems in the 1990s. Bengio's work on neural language models (2003), attention (2014) and generative models supplied much of the theory. Hinton shared the 2024 **Nobel Prize in Physics** with John Hopfield.
**Read:** "Learning representations by back-propagating errors" (1986); "Gradient-Based Learning Applied to Document Recognition" (LeCun et al., 1998); "ImageNet Classification with Deep Convolutional Neural Networks" (Krizhevsky, Sutskever & Hinton, 2012).

**Jürgen Schmidhuber** — *no Turing Award.* With Sepp Hochreiter, created **LSTM** (1997), the recurrent architecture that made sequence learning work and dominated NLP and speech for two decades. He has argued at length and in public that his group's earlier work anticipates much of what the 2018 laureates were credited with; the dispute is genuine, unresolved, and worth knowing about as a case study in how credit is assigned in science.
**Read:** "Long Short-Term Memory" (Hochreiter & Schmidhuber, 1997).

**Fei-Fei Li** — *no Turing Award.* Created **ImageNet** (2009) and the ILSVRC competition. The insight was that the bottleneck in computer vision was data, not algorithms — and building a 14-million-image labelled dataset is what made the 2012 deep-learning result possible. Founded Stanford's Human-Centered AI Institute.
**Read:** "ImageNet: A Large-Scale Hierarchical Image Database" (2009); *The Worlds I See* (2023).

**Richard Sutton and Andrew Barto** (Turing Award **2024**, "for developing the conceptual and algorithmic foundations of reinforcement learning") — temporal-difference learning, actor–critic methods, and the textbook that defined the field. Sutton's essay "The Bitter Lesson" (2019) — that general methods leveraging computation eventually beat methods that encode human knowledge — has arguably shaped more of the last decade's AI research agenda than any paper.
**Read:** Sutton & Barto, *Reinforcement Learning: An Introduction* (2nd ed., free online); "The Bitter Lesson".

**Judea Pearl** (Turing Award **2011**) — Bayesian networks and the causal calculus (do-calculus). The argument that statistics alone cannot answer causal questions.
**Read:** *The Book of Why* (2018) for the accessible version; *Causality* (2009) for the real one.

**Marvin Minsky** (Turing Award **1969**), **John McCarthy** (**1971**), **Allen Newell and Herbert Simon** (**1975**), **Edward Feigenbaum and Raj Reddy** (**1994**) — the symbolic-AI generation. Minsky and Papert's *Perceptrons* (1969) is often blamed for the first AI winter; Newell and Simon built the Logic Theorist and General Problem Solver and formulated the physical symbol system hypothesis; Simon also won the 1978 Nobel Prize in Economics.

## The women whose contributions were systematically under-credited

**Grace Hopper (1906–1992)** — *no Turing Award.* US Navy Rear Admiral. Programmed the Harvard Mark I; wrote the **first compiler**, the A-0 system (1952), against contemporaries who told her computers could only do arithmetic; created FLOW-MATIC, the English-like language that became the direct basis of **COBOL**. Popularised "debugging" after a moth was found in a Mark II relay. The ACM Grace Murray Hopper Award is named for her.
**Read:** "The Education of a Computer" (1952); Kurt Beyer's biography *Grace Hopper and the Invention of the Information Age*.

**Margaret Hamilton (b. 1936)** — *no Turing Award.* Led the software engineering division at MIT's Instrumentation Laboratory that wrote the **Apollo Guidance Computer** flight software. She coined the term "**software engineering**" — deliberately, to claim legitimacy for the discipline. Her priority-scheduling design is why Apollo 11 landed: minutes before touchdown the AGC threw 1201/1202 alarms from an overloaded rendezvous radar, and the software shed low-priority tasks and kept the landing computation running instead of crashing. Awarded the Presidential Medal of Freedom in 2016.
**Read:** the AGC source code, published on GitHub; Hamilton's own papers on the "Universal Systems Language".

**Katherine Johnson (1918–2020)** — *no Turing Award.* NASA mathematician who computed trajectories for Alan Shepard's Freedom 7 and for John Glenn's Friendship 7 orbital flight — Glenn reportedly refused to fly until she had personally verified the electronic computer's numbers. Co-authored NASA's first technical report by a woman in her division (1960). Presidential Medal of Freedom, 2015.
**Read:** *Hidden Figures* (Margot Lee Shetterly, 2016) for the history of the whole group.

**Jean Bartik (1924–2011)** — *no Turing Award.* One of the six original **ENIAC programmers** (with Betty Holberton, Kathleen Antonelli, Marlyn Meltzer, Frances Spence and Ruth Teitelbaum), who worked out how to program the machine from wiring diagrams with no manual, no language and no precedent. They were not invited to the 1946 press unveiling and were long described as "models". Bartik later led the team that converted ENIAC to a stored-program machine.
**Read:** her memoir *Pioneer Programmer* (2013).

**Frances Allen** (Turing Award **2006**), **Barbara Liskov** (**2008**), **Shafi Goldwasser** (**2012**) — covered above. Three women have won the Turing Award in its history.

**Ada Lovelace (1815–1852)** — her 1843 notes on Menabrea's paper about Babbage's Analytical Engine include what is generally regarded as the first published algorithm intended for a machine, and — more importantly — the observation that such a machine could operate on symbols representing anything, not only numbers. That is the conceptual leap from calculator to computer.
**Read:** Note G of her translation of Menabrea's "Sketch of the Analytical Engine" (1843).

## Sources

- [ACM A. M. Turing Award laureates, by year with citations](https://en.wikipedia.org/wiki/Turing_Award) — Wikipedia (all award years in this file verified against this list)
- [ACM A. M. Turing Award](https://awards.acm.org/turing) — ACM

## Open questions

- The **2025** Turing Award (announced in 2026) could not be verified — the ACM award pages returned 403 or a stale cached snapshot ending at 2023, and the Wikipedia list fetched ends at 2024. The most recent award stated here is therefore **2024 (Barto & Sutton)**; a 2025 laureate should be added once verifiable.
- Publication years for individual papers and books are from general knowledge, not from per-paper fetches. High-confidence dates (Turing 1936, Shannon 1948, Codd 1970, Lamport 1978, Diffie–Hellman 1976, RSA 1978) are safe; less-cited ones should be checked against the original venue before citation.
- Hinton's 2024 Nobel Prize in Physics is stated from general knowledge and was not fetched — `needs-verification`.
- Attribution disputes noted here (the EDVAC First Draft; Schmidhuber's priority claims; Merkle's role in public-key cryptography) are genuine live controversies, summarised rather than adjudicated.

