---
id: semi.resources
title: Books, courses, media, conferences and standards — an annotated register
domain: 27_semiconductors_and_chip_design
tags: [books, textbooks, courses, mooc, semianalysis, semiwiki, wikichip, techinsights, isscc, iedm, dac, hot-chips, irds, standards, jedec, ieee]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "IEEE International Roadmap for Devices and Systems", url: "https://irds.ieee.org/", publisher: "IEEE", accessed: 2026-08-25}
  - {title: "Tiny Tapeout", url: "https://tinytapeout.com/", publisher: "Tiny Tapeout", accessed: 2026-08-25}
  - {title: "OpenROAD Project", url: "https://en.wikipedia.org/wiki/OpenROAD_Project", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Universal Verification Methodology", url: "https://en.wikipedia.org/wiki/Universal_Verification_Methodology", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "RISC-V", url: "https://en.wikipedia.org/wiki/RISC-V", publisher: "Wikipedia", accessed: 2026-08-25}
related: [semi.career, semi.rtl, semi.physics]
---

# Books, courses, media, conferences and standards — an annotated register

**Summary.** A curated, annotated register of what to read, watch, attend and cite. Every entry carries a URL where one exists and a **free / paid** flag. Editions and publication years are given where confident; a few are marked `needs-verification` because edition numbers change and could not be confirmed in this research pass.

> ⚠️ Edition numbers and publication years below are from general knowledge, not verified against publisher catalogues in this pass. Verify the current edition before purchase or citation.

## 1. Textbooks — the core register

### Device physics and materials

| Book | Author(s) | Notes | Free/Paid |
|---|---|---|---|
| **Physics of Semiconductor Devices** | S. M. Sze, Yiming Li, Kwok K. Ng (Wiley; 3rd ed. 2006, 4th ed. 2021) | *The* reference. Encyclopaedic, dense, not a first book. You consult it; you do not read it cover to cover. Every device you will meet is in here with its physics derived | Paid |
| **Solid State Electronic Devices** | Ben G. Streetman, Sanjay Banerjee (Pearson; 7th ed. 2014) | The standard undergraduate text and the right *first* device book. Clear on band diagrams, junctions and MOS operation | Paid |
| **Semiconductor Physics and Devices** | Donald A. Neamen (McGraw-Hill) | The main alternative to Streetman; some find its worked examples clearer | Paid |
| **Fundamentals of Modern VLSI Devices** | Yuan Taur, Tak H. Ning (Cambridge; 3rd ed. 2021) | The bridge between device physics and what a process actually delivers. Excellent on scaling theory and short-channel effects — the best single treatment of why the roadmap looks the way it does | Paid |

### Digital design and VLSI

| Book | Author(s) | Notes | Free/Paid |
|---|---|---|---|
| **Digital Design and Computer Architecture** | David Money Harris, Sarah L. Harris (Morgan Kaufmann; **RISC-V edition** 2021, ARM edition 2015, MIPS 2nd ed. 2012) | The best single book for a beginner. Transistors → gates → RTL → a pipelined processor, in one continuous argument, with Verilog and VHDL side by side throughout. If you buy one book, this is it | Paid |
| **CMOS VLSI Design: A Circuits and Systems Perspective** | Neil Weste, David Harris (Pearson; 4th ed. 2010) | The standard VLSI course text. Strong on logical effort, circuit families, and the physical side of digital design. `needs-verification` on any later edition | Paid |
| **Digital Integrated Circuits: A Design Perspective** | Jan M. Rabaey, Anantha Chandrakasan, Borivoje Nikolić (Prentice Hall; 2nd ed. 2003) | Old and still unmatched on the *why*: delay models, power, interconnect, memory design. The definitive treatment of energy-delay trade-offs | Paid |
| **Digital Integrated Circuit Design: From VLSI Architectures to CMOS Fabrication** | Hubert Kaeslin (Cambridge, 2008); also **Top-Down Digital VLSI Design** (2014) | The most complete account of the *engineering process* of building a digital IC — architecture, methodology, verification, and the economics. Underread and excellent | Paid |
| **Logical Effort: Designing Fast CMOS Circuits** | Ivan Sutherland, Bob Sproull, David Harris (Morgan Kaufmann, 1999) | Short and transformative. A closed-form method for sizing gate chains that changes how you think about delay | Paid |
| **CMOS: Circuit Design, Layout, and Simulation** | R. Jacob Baker (Wiley/IEEE Press) | The most hands-on; heavy on SPICE and layout. Good for anyone doing analog-adjacent digital | Paid |

### Verification, timing and test

| Book | Author(s) | Notes | Free/Paid |
|---|---|---|---|
| **SystemVerilog for Verification** | Chris Spear, Greg Tumbush (Springer; 3rd ed. 2012) | The standard practical introduction to SystemVerilog's verification subset | Paid |
| **The UVM Primer** / **UVM Cookbook** | Ray Salemi / Siemens EDA | The Primer is a gentle book; the Verification Academy **UVM Cookbook** is the working reference and is **free** with registration | Mixed |
| **Static Timing Analysis for Nanometer Designs** | J. Bhasker, Rakesh Chadha (Springer, 2009) | The clearest book-length treatment of STA, SDC and signoff | Paid |
| **Constraining Designs for Synthesis and Timing Analysis** | Sanjay Churiwala, Sapan Garg (Springer) | Practical SDC. Fills the gap every new physical-design engineer falls into | Paid |
| **VLSI Test Principles and Architectures** | Laung-Terng Wang, Cheng-Wen Wu, Xiaoqing Wen (Morgan Kaufmann, 2006) | The DFT reference: scan, ATPG, BIST, compression | Paid |

### Computer architecture

| Book | Author(s) | Notes | Free/Paid |
|---|---|---|---|
| **Computer Architecture: A Quantitative Approach** | John L. Hennessy, David A. Patterson (Morgan Kaufmann; 6th ed. 2017, later editions exist — `needs-verification`) | The graduate standard, and the book that made architecture a quantitative discipline. The appendices alone are worth the price | Paid |
| **Computer Organization and Design: RISC-V Edition** | Patterson & Hennessy (Morgan Kaufmann; 2nd ed. 2020) | The undergraduate companion. Also available in ARM and MIPS editions | Paid |
| **The RISC-V Reader: An Open Architecture Atlas** | David Patterson, Andrew Waterman (2017) | Short, opinionated, and the fastest way to understand the ISA's design rationale | Paid |
| **RISC-V specifications** | RISC-V International | The unprivileged and privileged ISA manuals, plus profiles and extensions | **Free** — riscv.org/technical/specifications/ |
| **A Primer on Memory Consistency and Cache Coherence** | Nagarajan, Sorin, Hill, Wood (Morgan & Claypool, 2nd ed. 2020) | The clearest treatment of the hardest topic in multiprocessor architecture | Paid (often free via institutional access) |

### Analog and mixed-signal

| Book | Author(s) | Notes | Free/Paid |
|---|---|---|---|
| **Design of Analog CMOS Integrated Circuits** | Behzad Razavi (McGraw-Hill; 2nd ed. 2016) | The canonical analog text. Start here, and expect to work every problem | Paid |
| **Fundamentals of Microelectronics** | Behzad Razavi (Wiley) | Razavi's undergraduate entry point | Paid |
| **RF Microelectronics** | Behzad Razavi (Prentice Hall; 2nd ed. 2011) | The RF standard | Paid |
| **Analysis and Design of Analog Integrated Circuits** | Gray, Hurst, Lewis, Meyer (Wiley; 5th ed. 2009) | The other canonical text; more classical, deeper on bipolar | Paid |
| **The Art of Electronics** | Horowitz & Hill (Cambridge; 3rd ed. 2015) | Not IC design, but the best practical electronics book ever written and the right foundation for intuition | Paid |

### Process, fabrication and lithography

| Book | Author(s) | Notes | Free/Paid |
|---|---|---|---|
| **Silicon Processing for the VLSI Era** (5 volumes) | Stanley Wolf, Richard Tauber | The exhaustive process reference. Dated in places, unmatched in coverage | Paid |
| **Fundamentals of Semiconductor Manufacturing and Process Control** | Gary S. May, Costas J. Spanos (Wiley, 2006) | The best book on the *statistics and control* of manufacturing — SPC, DOE, yield modelling. The right book if you want to understand yield learning | Paid |
| **Fundamental Principles of Optical Lithography** | Chris A. Mack (Wiley, 2007) | The lithography reference. Mack's site (lithoguru.com) also carries free tutorial material | Paid (site free) |
| **Introduction to Microelectronic Fabrication** | Richard C. Jaeger (Prentice Hall) | A concise undergraduate alternative | Paid |
| **IEEE IRDS — International Roadmap for Devices and Systems** | IEEE | The successor to the ITRS. Annual chapters on lithography, more-Moore, beyond-CMOS, packaging, systems. **The single best free source for forward-looking technical parameters.** Download the current edition's chapter PDFs | **Free** — https://irds.ieee.org/ |

### Industry and context

| Book | Author | Notes | Free/Paid |
|---|---|---|---|
| **Chip War: The Fight for the World's Most Critical Technology** | Chris Miller (Scribner, 2022) | The standard modern history of the industry's geopolitics. Accurate, readable, and the best single primer on why `08` exists | Paid |
| **The Intel Trinity** | Michael S. Malone (2014) | Noyce, Moore and Grove; the founding-era history | Paid |
| **Only the Paranoid Survive** | Andrew S. Grove (1996) | Grove on strategic inflection points, by the person who ran Intel through several | Paid |
| **Crystal Fire** | Michael Riordan, Lillian Hoddeson (1997) | The invention of the transistor | Paid |

## 2. Courses

| Course | Institution | Notes | Free/Paid |
|---|---|---|---|
| **Nand2Tetris — Build a Modern Computer from First Principles** | Nisan & Schocken | Twelve projects from NAND gate to an operating system. The best possible starting point. Site is free; Coursera parts I & II are free to audit | **Free** — https://www.nand2tetris.org/ |
| **HDLBits** | Community (Henry Wong) | Several hundred graded Verilog exercises with automatic checking. The fastest route to HDL fluency | **Free** — https://hdlbits.01xz.net/ |
| **MIT 6.191 (formerly 6.004) Computation Structures** | MIT | Digital design through to a RISC-V processor. Materials on MIT OpenCourseWare | **Free** — https://ocw.mit.edu/ |
| **MIT 6.375 Complex Digital Systems** | MIT | Bluespec-based advanced digital design | **Free** (materials) |
| **Berkeley CS152 / CS252 Computer Architecture** | UC Berkeley | The architecture sequence, with lecture videos and materials frequently posted publicly | **Free** (materials) |
| **Berkeley EECS151/251A** | UC Berkeley | Digital design and integrated circuits, with an ASIC lab flow | **Free** (materials) |
| **VLSI CAD Part I: Logic / Part II: Layout** | Rob A. Rutenbar, UIUC, on Coursera | The best available introduction to how EDA tools work internally | **Free to audit** — coursera.org |
| **NPTEL VLSI courses** | IITs (India) | A very large free catalogue: *VLSI Design*, *Digital VLSI Testing*, *Analog IC Design*, *Microelectronics*. Uneven production, excellent content, and complete lecture series | **Free** — https://nptel.ac.in/ |
| **Zero to ASIC Course** | Matt Venn | The paid companion to Tiny Tapeout: a structured course taking you from Verilog to a submitted, fabricated design using OpenLane and SKY130 | Paid — https://www.zerotoasiccourse.com/ |
| **Verification Academy** | Siemens EDA | Extensive free UVM, formal, CDC and coverage courses; registration required | **Free** — https://verificationacademy.com/ |
| **ChipDev / VLSI interview practice sites** | Various | Interview-question drilling for RTL and DV | Mixed |
| **Coursera / edX device physics** | Purdue (nanoHUB-U), others | Mark Lundstrom's nanoHUB-U courses on nanoscale transistors are outstanding and free | **Free** — https://nanohub.org/ |

## 3. News, analysis and reference

| Source | What it is | Notes | Free/Paid |
|---|---|---|---|
| **SemiAnalysis** | Dylan Patel's research firm | The best-informed public analysis of AI hardware, foundry economics, packaging and supply chains. Free posts plus a substantial paid tier. Occasionally wrong, always worth reading | Mixed — https://semianalysis.com/ |
| **SemiWiki** | Industry blog network | Practitioner-written; especially good on EDA, IP and foundry. Daniel Nenni's foundry commentary is a long-running reference | **Free** — https://semiwiki.com/ |
| **WikiChip** | Reference wiki | Die shots, microarchitecture details, node parameters, transistor densities. The best free structured reference for microarchitecture facts | **Free** — https://en.wikichip.org/ |
| **Chips and Cheese** | Independent microarchitecture analysis | Deep, benchmark-driven analysis of CPU and GPU microarchitecture, with original measurement rather than vendor slides | **Free** — https://chipsandcheese.com/ |
| **TechInsights** | Reverse-engineering and teardown firm | The authority on what is actually inside a shipping chip — die photographs, cross-sections, node identification. Their public blog posts have repeatedly been the first confirmation of, e.g., SMIC's 7 nm. Reports are expensive | Mixed — https://www.techinsights.com/ |
| **Semiconductor Engineering** | Trade publication | Excellent technical depth on process, packaging, verification and DFT; a genuinely useful daily read | **Free** — https://semiengineering.com/ |
| **AnandTech (archives)** | Former review and analysis site | Ceased publishing in 2024; the archive remains one of the best repositories of architecture deep-dives from 1997–2024. `needs-verification` on the exact closure date | **Free** — https://www.anandtech.com/ |
| **IEEE Spectrum** | IEEE magazine | Accessible semiconductor coverage with technical credibility | **Free** — https://spectrum.ieee.org/ |
| **Asianometry** | YouTube channel (Jon Y) | The best free video explainers on semiconductor history, industry structure and technology | **Free** — youtube.com/@Asianometry |
| **Ben Eater** | YouTube channel | Builds an 8-bit computer on breadboards. The best intuition-building resource for digital logic that exists | **Free** — https://eater.net/ |
| **The Chip Letter** | Babbage's newsletter | Semiconductor history and industry essays | **Free/paid** — thechipletter.substack.com |
| **EE Times**, **Digitimes**, **TrendForce** | Trade press and market research | Digitimes and TrendForce are the usual origin of foundry capacity and market-share numbers that circulate elsewhere; both are substantially paywalled and both should be treated as reported-not-verified | Paid |

## 4. Conferences

| Conference | When / where | What it is | Access |
|---|---|---|---|
| **ISSCC** (International Solid-State Circuits Conference) | February, San Francisco | "The Chip Olympics." Where the year's headline circuits are first disclosed — CPUs, SerDes, converters, AI accelerators. The single most important circuits conference | Paid; proceedings via IEEE Xplore |
| **IEDM** (International Electron Devices Meeting) | December, San Francisco | Where new *devices* and *processes* are disclosed. TSMC, Intel, Samsung and imec present node details here — this is the primary source for gate pitch, density and device data | Paid; IEEE Xplore |
| **VLSI Symposium** (Technology & Circuits) | June, Kyoto / Honolulu (alternating) | The technology-and-circuits pair, and the other main venue for node disclosures | Paid |
| **DAC** (Design Automation Conference) | June/July, US | The EDA industry's main event: research papers plus a large commercial exhibition | Paid; some content free |
| **Hot Chips** | August, Stanford (and online) | Companies present their newest chips at architecture level. **The most accessible high-value conference** — presentations are often made public afterwards | Paid, moderate; slides frequently public |
| **DATE** (Design, Automation and Test in Europe) | March/April, Europe | The European DAC equivalent | Paid |
| **ICCAD** | October/November | The EDA algorithms research venue | Paid |
| **ISCA / MICRO / HPCA / ASPLOS** | Various | The four top computer-architecture research conferences. Many papers are freely available from authors' pages | Paid; papers often free |
| **SPIE Advanced Lithography + Patterning** | February, San Jose | Where ASML, imec, Zeiss and the resist makers disclose EUV progress, stochastics data and High-NA results. The primary source for everything in `06` | Paid; some papers open |
| **ITC** (International Test Conference) | Autumn | The DFT and test community's venue | Paid |
| **SEMICON West / Europa / Japan / Taiwan / China** | Various | Equipment and materials industry trade shows, plus market-forecast keynotes | Paid |
| **imec Technology Forum (ITF)** | Various | imec's public roadmap disclosures — forksheet, CFET, backside power | Mixed |
| **RISC-V Summit** | Various | The RISC-V ecosystem's main event | Paid |
| **Chipathon / ORConf / FOSSi Dial-Up** | Various / online | The open-source silicon community's events. FOSSi Foundation's *Dial-Up* talks are free and online | **Free** |

## 5. Datasheets, standards and specifications

| Standard | Body | Number / notes | Access |
|---|---|---|---|
| SystemVerilog | IEEE | **IEEE 1800** (current revision 1800-2023) | Paid; free via IEEE GET programme for some standards |
| VHDL | IEEE | **IEEE 1076** (1076-2019) | Paid |
| Verilog | IEEE | **IEEE 1364** (last standalone 1364-2005; now within 1800) | Paid |
| UVM | IEEE / Accellera | **IEEE 1800.2-2020**, approved 14 September 2020. The Accellera UVM class library reference implementation is free | Standard paid; **library free** — accellera.org |
| Unified Power Format (low-power intent) | IEEE | **IEEE 1801** (UPF) | Paid |
| IP metadata | IEEE | **IEEE 1685** (IP-XACT) | Paid |
| Boundary scan | IEEE | **IEEE 1149.1** (JTAG); **IEEE 1687** (IJTAG) | Paid |
| DDR5 | JEDEC | **JESD79-5**; DDR5 released 14 July 2020 | **Free with JEDEC registration** — jedec.org |
| LPDDR5 | JEDEC | **JESD209-5**; released February 2019 | Free with registration |
| HBM | JEDEC | JESD235 (HBM1, Oct 2013), JESD235a (HBM2, Jan 2016), JESD235d (HBM3, Jan 2022), **JESD270-4 (HBM4, April 2025)** | Free with registration |
| PCI Express | PCI-SIG | Membership required for specifications | Paid |
| CXL | CXL Consortium | Compute Express Link specifications | Free download after registration — computeexpresslink.org |
| UCIe | UCIe Consortium | Die-to-die interconnect | Registration — uciexpress.org |
| RISC-V ISA | RISC-V International | Unprivileged and privileged ISA manuals, profiles (RVA22/RVA23), extension specifications | **Free** — riscv.org |
| AMBA (AXI, AHB, APB, CHI, ACE) | Arm | The de facto SoC interconnect standards | **Free download** — developer.arm.com |
| Wishbone | OpenCores / FOSSi | The open-source SoC bus | **Free** |
| SKY130 PDK | SkyWater / Google | Open 130 nm PDK: design rules, cell libraries, SPICE models | **Free** — skywater-pdk.readthedocs.io |
| GF180MCU PDK | GlobalFoundries / Google | Open 180 nm PDK | **Free** |
| IHP Open PDK (SG13G2) | IHP | Open 130 nm SiGe BiCMOS, with analog/RF devices | **Free** — github.com/IHP-GmbH/IHP-Open-PDK |
| IRDS | IEEE | The forward roadmap; free chapter PDFs | **Free** — irds.ieee.org |

## 6. Open-source tools — where to get them

| Tool | Purpose | URL |
|---|---|---|
| Yosys | Synthesis | https://github.com/YosysHQ/yosys |
| OpenROAD / OpenROAD-flow-scripts | RTL-to-GDSII | https://theopenroadproject.org/ |
| OpenLane 2 | Packaged ASIC flow | https://github.com/efabless/openlane2 |
| OpenSTA | Static timing analysis | https://github.com/parallaxsw/OpenSTA |
| Magic / KLayout | Layout editing, DRC, GDS viewing | http://opencircuitdesign.com/magic/ · https://www.klayout.de/ |
| netgen | LVS | http://opencircuitdesign.com/netgen/ |
| ngspice / Xyce | SPICE simulation | https://ngspice.sourceforge.io/ |
| Verilator | Fast Verilog simulation | https://www.veripool.org/verilator/ |
| Icarus Verilog | Event-driven simulation | https://steveicarus.github.io/iverilog/ |
| cocotb | Python testbenches | https://www.cocotb.org/ |
| GTKWave / Surfer | Waveform viewing | https://gtkwave.sourceforge.net/ · https://surfer-project.org/ |
| SymbiYosys | Formal property checking | https://github.com/YosysHQ/sby |
| nextpnr + Project IceStorm / Trellis | Open FPGA place-and-route | https://github.com/YosysHQ/nextpnr |
| Chisel / SpinalHDL / Amaranth | Hardware construction languages | https://www.chisel-lang.org/ · https://spinalhdl.github.io/ · https://amaranth-lang.org/ |
| OpenTitan, CVA6, Ibex, Rocket, BOOM, VexRiscv, SERV | Open cores and SoCs | https://opentitan.org/ · https://github.com/openhwgroup · https://github.com/chipsalliance |

## Open questions

- Edition numbers and years for several textbooks are from general knowledge and should be checked against publisher listings before citation (`needs-verification`).
- AnandTech's exact closure date is unverified.
- Conference dates and locations rotate annually — check each society's site for the current year.

## Sources

- [IEEE International Roadmap for Devices and Systems](https://irds.ieee.org/) — accessed 2026-08-25
- [Tiny Tapeout](https://tinytapeout.com/) — accessed 2026-08-25
- [Tiny Tapeout FAQ](https://tinytapeout.com/faq/) — accessed 2026-08-25
- [OpenROAD Project — Wikipedia](https://en.wikipedia.org/wiki/OpenROAD_Project) — accessed 2026-08-25
- [Universal Verification Methodology — Wikipedia](https://en.wikipedia.org/wiki/Universal_Verification_Methodology) — accessed 2026-08-25
- [RISC-V — Wikipedia](https://en.wikipedia.org/wiki/RISC-V) — accessed 2026-08-25
- [High Bandwidth Memory — Wikipedia](https://en.wikipedia.org/wiki/High_Bandwidth_Memory) — accessed 2026-08-25
- [DDR5 SDRAM — Wikipedia](https://en.wikipedia.org/wiki/DDR5_SDRAM) — accessed 2026-08-25
- [SkyWater Technology — Wikipedia](https://en.wikipedia.org/wiki/SkyWater_Technology) — accessed 2026-08-25
