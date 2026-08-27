---
id: aerospace.books
title: Essential aerospace books and study materials
domain: 29_aerospace_engineering
tags: [textbooks, reading-list, anderson, raymer, torenbeek, roskam, megson, niu, bruhn, etkin, nelson, curtis, vallado, sutton, smad, aiaa, nasa-ntrs, esdu, free-resources]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Fundamentals of Aerodynamics, 7th Edition", url: "https://www.mheducation.com/highered/product/fundamentals-aerodynamics-anderson-cadou/M9781264151929.html", publisher: "McGraw Hill", accessed: 2026-08-25}
  - {title: "Orbital Mechanics for Engineering Students, 4th Edition", url: "https://shop.elsevier.com/books/orbital-mechanics-for-engineering-students/curtis/978-0-08-102133-0", publisher: "Elsevier", accessed: 2026-08-25}
  - {title: "Orbital Mechanics for Engineering Students, 5th Edition", url: "https://shop.elsevier.com/books/orbital-mechanics-for-engineering-students/curtis/978-0-443-29015-2", publisher: "Elsevier", accessed: 2026-08-25}
  - {title: "AIAA Books", url: "https://www.aiaa.org/publications/books", publisher: "AIAA", accessed: 2026-08-25}
  - {title: "NASA Technical Reports Server", url: "https://ntrs.nasa.gov/", publisher: "NASA STI Program", accessed: 2026-08-25}
  - {title: "XFOIL", url: "https://web.mit.edu/drela/Public/web/xfoil/", publisher: "M. Drela, MIT", accessed: 2026-08-25}
  - {title: "MIT OCW 16.100 Aerodynamics", url: "https://ocw.mit.edu/courses/16-100-aerodynamics-fall-2005/", publisher: "MIT OpenCourseWare", accessed: 2026-08-25}
  - {title: "NPTEL course archive", url: "https://archive.nptel.ac.in/course.html", publisher: "NPTEL", accessed: 2026-08-25}
related: [aerospace.curriculum, aerospace.practicals]
unit_system: SI
---

# Essential aerospace books and study materials

**Summary.** Aerospace engineering has an unusually stable canon: the books that taught the engineers who designed the 747 are, in later editions, still teaching the engineers designing the 777X. This is an annotated catalogue organised by subject, giving for each entry what it is for, what level it sits at, and whether it is free. Where an edition could not be verified against a publisher page in this session it is flagged — the instruction not to invent an edition is taken literally.

> ⚠️ **Edition discipline.** Only the editions marked ✅ below were verified against a publisher or authoritative page during compilation. Everything else is marked `needs-verification` and should be checked before purchase or citation.

## Key facts

| Item | Status |
|---|---|
| **Anderson, *Fundamentals of Aerodynamics*** | ✅ **7th edition, 2024**, McGraw Hill, Anderson & Cadou, ISBN 9781264151929 |
| **Curtis, *Orbital Mechanics for Engineering Students*** | ✅ **4th edition, 10 July 2019**, Elsevier, ISBN 9780081021330; **5th edition announced for 19 October 2026**, ISBN 9780443290152 |
| **AIAA publishing** | ✅ "the leading publisher in the aerospace industry", **300+ titles** across the **Education Series**, **Progress in Astronautics and Aeronautics**, **Library of Flight**, and **The Aerospace Press** |
| **NASA NTRS** | ✅ Free; NASA metadata records, full-text documents, images and video — conference papers, journal articles, patents, research reports |
| **XFOIL** | ✅ Free, **GPL**, version **6.99 (23 December 2013)**, Mark Drela / Harold Youngren, MIT |
| **MIT OCW 16.100 Aerodynamics** | ✅ Free (Fall 2005, Prof. David Darmofal) — lecture notes, problem sets, exams, projects |
| **NPTEL aerospace** | ✅ Free video courses from the IITs and IISc |

---

## 1. Introduction and general

**Anderson, *Introduction to Flight*** — McGraw Hill. The single best first book in the field: history, standard atmosphere, basic aerodynamics, performance, stability, propulsion, structures, space flight, all at first-year level with genuine physical insight and Anderson's characteristic historical asides. If you read one book before anything else, this is it. *Level:* first year / motivated non-specialist. *Free:* no. *Edition:* `needs-verification`.

**Anderson, *The Airplane: A History of Its Technology*** and ***A History of Aerodynamics*** — AIAA/Cambridge. Not textbooks; the intellectual history of why the field's methods look the way they do. Worth reading for anyone who wants to understand why Prandtl's boundary layer mattered more than any wind tunnel. *Free:* no.

**Kermode, *Mechanics of Flight*** — Pearson. The classic British qualitative treatment, still the best explanation-without-calculus available and a staple of pilot ground school. *Level:* pre-degree. *Free:* no.

---

## 2. Aerodynamics

**Anderson, *Fundamentals of Aerodynamics*** ✅ **7th ed., 2024** (with Cadou), McGraw Hill. The world's default aerodynamics text. Part I fundamentals and governing equations; Part II inviscid incompressible (potential flow, thin airfoil, lifting line, panel methods); Part III inviscid compressible (shocks, expansions, linearised theory, transonic, hypersonic); Part IV viscous. Verbose by design — the verbosity is the teaching. *Level:* years 2–3.

**Anderson, *Modern Compressible Flow: With Historical Perspective*** — McGraw Hill. The companion for gas dynamics: quasi-1-D flow, normal and oblique shocks, expansions, unsteady wave motion, method of characteristics, numerical techniques. *Level:* year 3. *Edition:* `needs-verification`.

**Anderson, *Hypersonic and High-Temperature Gas Dynamics*** — AIAA Education Series. The standard hypersonics text: Newtonian theory, viscous interaction, real-gas effects, aerodynamic heating. *Level:* graduate.

**Bertin & Cummings, *Aerodynamics for Engineers*** — Cambridge/Pearson. Tighter and more application-focused than Anderson, with excellent chapters on wing–body aerodynamics, high-lift, and design data. Many programmes use it instead of, or alongside, Anderson. *Level:* years 2–3. *Edition:* `needs-verification`.

**Katz & Plotkin, *Low-Speed Aerodynamics*** — Cambridge. The definitive treatment of **panel methods and vortex-lattice methods**, with the theory developed rigorously and code structures given explicitly. If you intend to write a panel code, this is the book. *Level:* advanced undergraduate / graduate. *Edition:* 2nd, `needs-verification`.

**Drela, *Flight Vehicle Aerodynamics*** — MIT Press, 2014. Dense, modern, and unified: it covers potential flow, boundary layers, compressible flow, unsteady aerodynamics and aerodynamic performance in one coherent formalism, and it is the theoretical basis behind XFOIL, AVL and ASWING. Not a first book; an excellent second one. *Level:* graduate.

**Schlichting & Gersten, *Boundary-Layer Theory*** — Springer, 9th ed. The reference work on viscous flow. Encyclopaedic rather than pedagogical. *Level:* graduate/reference.

**Abbott & von Doenhoff, *Theory of Wing Sections*** — Dover. Cheap, permanently in print, and containing the **NACA airfoil coordinates and measured section data** that are still used daily. Every aerodynamicist owns a copy. *Level:* all. *Free:* no, but a few dollars.

**Hoerner, *Fluid-Dynamic Drag*** and ***Fluid-Dynamic Lift*** — self-published, still available. Two volumes of empirical drag and lift data on absolutely everything — struts, wheels, antennas, junctions, rough surfaces. When a CFD run is not worth the trouble, Hoerner has a curve. *Level:* practitioner reference.

**Küchemann, *The Aerodynamic Design of Aircraft*** — AIAA Library of Flight reissue. The intellectual case for the slender wing and for treating the aircraft as a single aerodynamic entity; the book behind Concorde's thinking.

---

## 3. Aircraft design

**Raymer, *Aircraft Design: A Conceptual Approach*** — AIAA Education Series. **The** capstone book: the sizing loop, constraint analysis, configuration layout, component weights, aerodynamic build-up, propulsion integration, cost, and the trade studies, all with worked methods and tables. Paired with his **RDS** software. *Level:* year 3–4 / practitioner. *Edition:* 7th, `needs-verification`. *Free:* no.

**Gudmundsson, *General Aviation Aircraft Design: Applied Methods and Procedures*** — Butterworth-Heinemann. The most *usable* design book in print: every method is given as an explicit procedure with worked numbers and downloadable spreadsheets, aimed at the light-aircraft and UAV size class. If Raymer is the syllabus, Gudmundsson is the manual. *Level:* year 3–4 / practitioner. *Edition:* 2nd, `needs-verification`.

**Torenbeek, *Synthesis of Subsonic Airplane Design*** (Delft University Press/Springer) and ***Advanced Aircraft Design*** (Wiley, 2013). Torenbeek's weight-estimation and drag methods are more physically grounded than the pure regressions elsewhere, and the *Advanced* volume is the best available treatment of the conceptual design of large transports including the multidisciplinary trades. *Level:* advanced.

**Roskam, *Airplane Design*** Parts I–VIII (DARcorporation). Eight volumes covering preliminary sizing, configuration, layout, systems, component weights, aerodynamics and performance, cost, and structural layout. It is a data and procedure repository more than a book to read, and it is the reference many capstone teams actually run their numbers from. Also Roskam's *Airplane Flight Dynamics and Automatic Flight Controls* Parts I–II. *Level:* practitioner. *Free:* no, and expensive.

**Nicolai & Carichner, *Fundamentals of Aircraft and Airship Design*** Vols I–II — AIAA Education Series. Volume I is aircraft design with a strong military/high-performance emphasis and the best available treatment of the design of unconventional configurations; Volume II is airship and lighter-than-air. *Level:* year 4 / practitioner.

**Jenkinson, Simpkin & Rhodes, *Civil Jet Aircraft Design*** — AIAA/Elsevier, with a well-known free companion data set of airliner parameters. Excellent for a transport-focused capstone. *Free:* the data appendices have historically been freely available online; `needs-verification`.

**Howe, *Aircraft Conceptual Design Synthesis*** — Wiley. Compact, formula-dense, UK-school approach.

**Kundu, *Aircraft Design*** — Cambridge. A more modern textbook treatment with attention to cost and manufacturing.

---

## 4. Propulsion

**Hill & Peterson, *Mechanics and Thermodynamics of Propulsion*** — Pearson, 2nd ed. The classical text: thermodynamics, cycle analysis, turbomachinery, combustion, rockets, and electric propulsion, all derived properly. Dry but complete. *Level:* year 3.

**Mattingly, *Elements of Propulsion: Gas Turbines and Rockets*** — AIAA Education Series. Heavier on cycle analysis and engine design methodology than Hill & Peterson, with the parametric and performance analysis procedures used in industry, and companion software (AEDsys/ONX/OFFX). Also Mattingly, Heiser & Pratt, ***Aircraft Engine Design*** — AIAA — which is the propulsion analogue of Raymer. *Level:* year 3–4.

**Farokhi, *Aircraft Propulsion*** — Wiley. The most readable modern treatment; strong on component aerodynamics and on the environmental/future-propulsion chapters. *Level:* year 3.

**Cumpsty, *Jet Propulsion*** — Cambridge. Deliberately simple, physical and short: it explains *why* engines look the way they do without hiding behind cycle algebra. The best single book to read first. Cumpsty & Heyes' later editions add material on the environment. *Level:* accessible to all.

**Cumpsty, *Compressor Aerodynamics*** — Krieger/Longman. The reference on axial compressors: stage design, cascade data, stall and surge, matching. *Level:* graduate/practitioner.

**Sutton & Biblarz, *Rocket Propulsion Elements*** — Wiley. The rocket propulsion standard for seventy years: nozzle theory, liquid and solid engines, propellants, combustion instability, electric propulsion, testing. *Level:* year 3 through practitioner. *Edition:* 9th, `needs-verification`.

**Huzel & Huang, *Modern Engineering for Design of Liquid-Propellant Rocket Engines*** — AIAA Progress series. The Rocketdyne design handbook; still the best practical engine-design reference. *Level:* practitioner.

**Kerrebrock, *Aircraft Engines and Gas Turbines*** — MIT Press. Compact and analytically elegant; the text behind MIT's 16.511. *Level:* graduate.

---

## 5. Structures

**Megson, *Aircraft Structures for Engineering Students*** — Butterworth-Heinemann. The teaching standard: elasticity, thin-walled beam theory, shear flow, torsion of multi-cell boxes, buckling, composite laminates, structural idealisation, airworthiness and loads. Includes worked examples of the exact kind found in exams and in early-career work. *Level:* years 2–3. *Edition:* 7th, `needs-verification`.

**Niu, *Airframe Structural Design*** and ***Airframe Stress Analysis and Sizing*** — Conmilit Press. Not textbooks — **industry handbooks**. Every joint type, fitting, cut-out, splice, lug and panel, drawn as it is actually built, with the sizing method beside it. These two books are what a junior stress engineer at an OEM is quietly handed. *Level:* practitioner. *Free:* no, and expensive/hard to find.

**Bruhn, *Analysis and Design of Flight Vehicle Structures*** — Jacobs Publishing. The 1970s bible: 1,000-plus pages of methods, charts and worked examples for buckling, crippling, joints, fittings, and shell analysis. Superseded in presentation, not in content; still cited in stress reports. *Level:* practitioner.

**Peery, *Aircraft Structures*** — Dover. A cheap, clear, classical treatment of loads, shear flow, and structural analysis — the best-value structures book in print. *Level:* years 2–3. *Free:* no, but a Dover price.

**Flabel, *Practical Stress Analysis for Design Engineers*** — Lake City. The pragmatic bridge between textbook mechanics and the margin-of-safety calculations in an actual stress report.

**Sun, *Mechanics of Aircraft Structures*** — Wiley. Modern, concise, with good composite coverage.

**Hodges & Pierce, *Introduction to Structural Dynamics and Aeroelasticity*** — Cambridge. The standard aeroelasticity course text: structural dynamics, static aeroelasticity (divergence, control reversal), and flutter. *Level:* year 4/graduate. **Bisplinghoff, Ashley & Halfman, *Aeroelasticity*** — Dover — remains the deep reference. **Wright & Cooper, *Introduction to Aircraft Aeroelasticity and Loads*** — Wiley — is the most industrially oriented of the three.

**Jones, *Mechanics of Composite Materials*** — Taylor & Francis; **Daniel & Ishai, *Engineering Mechanics of Composite Materials*** — OUP; **Niu, *Composite Airframe Structures*** — Conmilit. In that order for theory → application → practice.

---

## 6. Flight mechanics, stability and control

**Etkin & Reid, *Dynamics of Flight: Stability and Control*** — Wiley, 3rd ed. The rigorous treatment: full nonlinear equations of motion, linearisation, stability derivatives, the dynamic modes, and closed-loop response. *Level:* year 3–4.

**Nelson, *Flight Stability and Automatic Control*** — McGraw Hill, 2nd ed. Gentler and more example-driven than Etkin; the more common undergraduate choice. *Level:* year 3.

**Stengel, *Flight Dynamics*** — Princeton University Press, 2nd ed. 2022. The modern control-theoretic treatment, with extensive MATLAB support and a genuinely current bibliography. Stengel's ***Optimal Control and Estimation*** (Dover) is the cheapest good book on LQR/Kalman filtering in print. *Level:* graduate.

**Cook, *Flight Dynamics Principles*** — Butterworth-Heinemann. The standard UK text, notation-consistent with the European convention and much used at Cranfield. *Level:* year 3.

**Stevens, Lewis & Johnson, *Aircraft Control and Simulation*** — Wiley. The book for anyone building a 6-DOF simulation or designing a real autopilot; includes full aircraft models and control design case studies. *Level:* graduate/practitioner.

**Phillips, *Mechanics of Flight*** — Wiley. Enormous and thorough; combines performance, stability and control in one volume.

**Ruijgrok, *Elements of Airplane Performance*** — Delft Academic Press. The clearest performance text, and the one whose treatment of the drag polar and of range/endurance a pilot will find most immediately usable.

---

## 7. Astronautics and space systems

**Curtis, *Orbital Mechanics for Engineering Students*** ✅ **4th ed., 2019**, Elsevier (5th ed. announced for **19 October 2026**). The teaching standard, with MATLAB code for everything from Kepler's equation to Lambert's problem to perturbations. *Level:* year 3–4.

**Vallado, *Fundamentals of Astrodynamics and Applications*** — Microcosm/Springer. The professional reference: time systems, coordinate frames, perturbation models, orbit determination, SGP4, and the numerical detail that Curtis omits. If you are writing operational software, this is the book. *Level:* practitioner. *Edition:* 5th, `needs-verification`.

**Bate, Mueller & White, *Fundamentals of Astrodynamics*** — Dover. The 1971 USAF Academy text; cheap, clear, still excellent for the two-body problem and Lambert. *Level:* year 2–3.

**Wertz & Larson (eds), *Space Mission Analysis and Design* (SMAD)** — Microcosm/Springer. The systems-level bible: mission design, requirements flow-down, subsystem sizing rules of thumb, budgets, cost models. The successor volume, *Space Mission Engineering: The New SMAD*, updates it. Also **Wertz, *Spacecraft Attitude Determination and Control***, the reference on ADCS. *Level:* practitioner.

**Fortescue, Stark & Swinerd, *Spacecraft Systems Engineering*** — Wiley, 4th ed. The European counterpart to SMAD: more textbook, less handbook, and better as a taught course. *Level:* year 4/graduate.

**Wiesel, *Spaceflight Dynamics*** — a compact alternative to Curtis. **Battin, *An Introduction to the Mathematics and Methods of Astrodynamics*** — AIAA — is the deep mathematical treatment for those who want it.

**Larson & Pranke, *Human Spaceflight: Mission Analysis and Design*** — for crewed systems and life support.

---

## 8. Avionics, systems and safety

**Moir & Seabridge, *Aircraft Systems: Mechanical, Electrical and Avionics Subsystems Integration*** — Wiley, 3rd ed., and their ***Design and Development of Aircraft Systems*** and ***Civil Avionics Systems***. The three together are the best single-source coverage of the systems in `08_avionics-and-systems.md`. *Level:* year 3 through practitioner.

**Collinson, *Introduction to Avionics Systems*** — Springer, 3rd ed. Strong on the mathematics of inertial navigation, air data, displays and flight control. *Level:* year 3–4.

**Spitzer (ed.), *Digital Avionics Handbook*** — CRC. The reference work on architectures, buses, IMA and certification.

**Kayton & Fried, *Avionics Navigation Systems*** — Wiley. The classic navigation reference; still the best on inertial and radio navigation fundamentals.

**Rierson, *Developing Safety-Critical Software: A Practical Guide for Aviation Software and DO-178C Compliance*** — CRC. The most useful practical book on DO-178C. *Level:* practitioner.

**Leveson, *Engineering a Safer World* (STAMP/STPA)** — MIT Press, and it is **free to download from MIT Press**. The most important recent rethinking of system safety, arguing that accidents in complex socio-technical systems are control problems rather than component-failure problems. Directly relevant to understanding the MCAS failure. *Free:* ✅ (open access).

**Kritzinger, *Aircraft System Safety*** — Woodhead; **Lloyd & Tye, *Systematic Safety*** — CAA, the historical origin of the 10⁻⁹ argument.

---

## 9. CFD, numerical methods and optimisation

**Ferziger, Perić & Street, *Computational Methods for Fluid Dynamics*** — Springer. The standard graduate CFD text; finite volume, pressure–velocity coupling, turbulence modelling, and practical advice.

**Blazek, *Computational Fluid Dynamics: Principles and Applications*** — Elsevier. The most implementation-oriented: structured and unstructured schemes, flux formulations, boundary conditions, acceleration, with enough detail to write a solver.

**Anderson, *Computational Fluid Dynamics: The Basics with Applications*** — McGraw Hill. The gentle introduction, in Anderson's usual style.

**Wilcox, *Turbulence Modeling for CFD*** — DCW Industries. The reference on RANS closures, by the author of k-ω.

**Pope, *Turbulent Flows*** — Cambridge. The physics of turbulence, properly.

**Martins & Ning, *Engineering Design Optimization*** — Cambridge University Press, 2021, and it is **freely downloadable as a PDF from the authors** (mdolab). The best modern text on gradient-based optimisation, adjoints and MDO architectures, from the Michigan MDO Lab. *Free:* ✅ (author-hosted PDF; `needs-verification` that the free PDF is still posted).

**Bathe, *Finite Element Procedures*** — free PDF from the author's MIT page; **Cook, Malkus, Plesha & Witt, *Concepts and Applications of Finite Element Analysis*** — Wiley — for the applied route.

---

## 10. Free primary sources — the ones that actually matter

| Resource | What it is | Free? |
|---|---|---|
| **NASA Technical Reports Server (ntrs.nasa.gov)** | ✅ NASA metadata records, full-text documents, images and video: conference papers, journal articles, patents and research reports. Includes the entire **NACA Technical Report / Technical Note / Technical Memorandum** series — the foundational literature of the field, including Jacobs' airfoil reports, Whitcomb's area-rule and supercritical papers, and thousands of wind-tunnel data reports still cited today | ✅ Yes |
| **MIT OpenCourseWare, Course 16** | ✅ 16.100 Aerodynamics (Fall 2005, Darmofal) with lecture notes, problem sets, exams and projects; plus 16.885 Aircraft Systems Engineering, 16.50 propulsion, 16.20 structures, 16.30/16.31 control, 16.346 astrodynamics, 16.920 numerical PDEs, 16.89 space systems | ✅ Yes |
| **NPTEL (archive.nptel.ac.in)** | ✅ Full video courses from the IITs and IISc, including Aerodynamic Design of Axial Flow Compressors & Fans (IIT KGP), Fundamentals of Theoretical and Experimental Aerodynamics (IIT KGP), Introduction to Launch Vehicle Analysis and Design (IIT Bombay), Lighter than Air Systems (IIT Bombay), Gasdynamics: Fundamentals and Applications (IISc), Introduction to Aerospace Engineering and Introduction to Aircraft Design (IIT Bombay), Introduction to Rocket Propulsion (IIT Kanpur), Rocket Propulsion (IIT Madras), Computational Science in Engineering (IIT Kanpur) | ✅ Yes |
| **NASA Turbulence Modeling Resource (turbmodels.larc.nasa.gov)** | Canonical turbulence model formulations and verification/validation cases | ✅ Yes |
| **AIAA Drag Prediction and High-Lift Prediction Workshop archives** | The field's own honest audit of CFD accuracy, with geometries, grids and results | ✅ Yes |
| **NASA SP series** and the **NASA Systems Engineering Handbook (SP-2016-6105 Rev 2)** | Free PDFs; the systems engineering handbook is genuinely excellent and is used well outside NASA | ✅ Yes |
| **ESA/NASA State of the Art of Small Spacecraft Technology** report | Annual free survey of CubeSat and smallsat subsystems with vendor data | ✅ Yes |
| **eCFR (ecfr.gov)** and **EASA document library** | The actual regulations: 14 CFR Parts 21/23/25/33, CS-25, CS-23, AMC/GM | ✅ Yes |
| **NTSB and AAIB/BEA/ATSB accident reports** | The most instructive engineering documents in aviation. Read the Comet inquiry, Aloha 243, AF447, QF32, UA232, and the 737 MAX reports in full | ✅ Yes |
| **XFOIL / AVL / ASWING (Drela, MIT)** | ✅ XFOIL 6.99 (23 Dec 2013), GPL | ✅ Yes |
| **OpenVSP, SU2, OpenFOAM, OpenMDAO/OpenAeroStruct** | Open-source geometry, CFD, and MDO | ✅ Yes |

### ESDU
**ESDU (Engineering Sciences Data Unit)**, now published by IHS Markit/S&P Global, is a set of several thousand validated **Data Items** — methods, correlations and design charts covering aerodynamics, structures, fatigue, dynamics, mechanisms, heat transfer, noise and performance, each with a stated validation basis and worked example. It occupies a unique position: it is the closest thing the industry has to a *certified* handbook method, and ESDU methods are routinely accepted as a means of compliance in certification. Structure is by series (Aerodynamics, Aircraft Noise, Composites, Dynamics, Fatigue-Endurance Data, Performance, Stress and Strength, Structures, Transonic Aerodynamics, Vibration and Acoustic Fatigue). **It is a paid subscription, and an expensive one** — typically institutional. There is no free tier. Most university aerospace departments hold a subscription; use it while you have access. (The ESDU site returned HTTP 403 to automated access, so the current series list and pricing are `needs-verification`.)

### AIAA publications
✅ AIAA is "the leading publisher in the aerospace industry" with **more than 300 titles**:
- **AIAA Education Series** — textbooks "adopted by top engineering programs worldwide", presenting material tutorially: Raymer, Nicolai & Carichner, Mattingly, Anderson's hypersonics, Brandt et al. *Introduction to Aeronautics*, Zipfel *Modeling and Simulation of Aerospace Vehicle Dynamics*.
- **Progress in Astronautics and Aeronautics** — specialised edited volumes on particular topics, often the state of the art in a niche.
- **Library of Flight** — history, economics and management of aerospace, including case studies.
- **The Aerospace Press** — monographs from The Aerospace Corporation, distributed by AIAA.
AIAA journals (*AIAA Journal*, *Journal of Aircraft*, *Journal of Propulsion and Power*, *Journal of Spacecraft and Rockets*, *Journal of Guidance, Control, and Dynamics*) are the field's primary literature and are paywalled; **AIAA student membership** gives substantially discounted book and journal access and is the single best-value purchase a student can make.

---

## 11. A prioritised buying order

For someone building a shelf from nothing, in this order:

1. **Anderson, *Introduction to Flight*** — the map.
2. **Anderson, *Fundamentals of Aerodynamics* (7th ed., 2024)** — the core.
3. **Cumpsty, *Jet Propulsion*** — cheap, short, transformative for anyone who flies behind turbofans.
4. **Abbott & von Doenhoff, *Theory of Wing Sections*** (Dover) — the data.
5. **Nelson** or **Etkin & Reid** — stability and control.
6. **Megson** — structures.
7. **Raymer** — design, once the above are in place.
8. **Gudmundsson** — if you intend to actually design something.
9. **Curtis** — if the interest runs to space.
10. **Moir & Seabridge, *Aircraft Systems*** — if the interest runs to systems.

Everything else on this list is a reference to be consulted, not a book to be read.

## Sources

- [Fundamentals of Aerodynamics, 7th Edition (2024)](https://www.mheducation.com/highered/product/fundamentals-aerodynamics-anderson-cadou/M9781264151929.html) — McGraw Hill
- [Orbital Mechanics for Engineering Students, 4th Edition (2019)](https://shop.elsevier.com/books/orbital-mechanics-for-engineering-students/curtis/978-0-08-102133-0) and [5th Edition (announced 19 Oct 2026)](https://shop.elsevier.com/books/orbital-mechanics-for-engineering-students/curtis/978-0-443-29015-2) — Elsevier
- [AIAA Books](https://www.aiaa.org/publications/books) — AIAA
- [NASA Technical Reports Server](https://ntrs.nasa.gov/) — NASA STI Program
- [XFOIL](https://web.mit.edu/drela/Public/web/xfoil/) — Mark Drela, MIT
- [MIT OCW 16.100 Aerodynamics](https://ocw.mit.edu/courses/16-100-aerodynamics-fall-2005/) — MIT OpenCourseWare
- [NPTEL course archive](https://archive.nptel.ac.in/course.html) — NPTEL

## Open questions

- **Editions**: only Anderson *Fundamentals of Aerodynamics* (7th, 2024) and Curtis (4th 2019 / 5th announced Oct 2026) were verified against publisher pages. All other edition numbers in this file are marked `needs-verification` and were deliberately either omitted or flagged rather than asserted.
- ESDU's current series list, publisher status and pricing — esdu.com returned HTTP 403; `needs-verification`.
- Whether the free author-hosted PDFs of Martins & Ning *Engineering Design Optimization* and Leveson *Engineering a Safer World* are still posted — `needs-verification`.
- Whether the Jenkinson *Civil Jet Aircraft Design* data appendices remain freely available — `needs-verification`.
