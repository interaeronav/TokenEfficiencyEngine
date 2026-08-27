---
id: space.books
title: Books, standards and open courseware — an annotated catalogue
domain: 30_space_science_and_propulsion
tags: [books, references, textbooks, sutton, curtis, vallado, smad, nasa-sp, ecss, open-courseware]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
related: [space.overview, space.orbital-mechanics, space.chemical-propulsion, space.spacecraft-engineering, space.tools]
sources:
  - {title: "Vallado software and code", url: "https://celestrak.org/software/vallado-sw.php", publisher: "CelesTrak", accessed: "2026-08-25"}
  - {title: "CelesTrak fundamentals-of-astrodynamics repository", url: "https://github.com/CelesTrak/fundamentals-of-astrodynamics", publisher: "CelesTrak / GitHub", accessed: "2026-08-25"}
  - {title: "NASA RP-1311 Part I (CEA analysis)", url: "https://ntrs.nasa.gov/citations/19950013764", publisher: "NASA NTRS", accessed: "2026-08-25"}
  - {title: "NASA Systems Engineering Handbook", url: "https://www.nasa.gov/reference/systems-engineering-handbook/", publisher: "NASA", accessed: "2026-08-25"}
  - {title: "ECSS active standards", url: "https://ecss.nl/standards/active-standards/", publisher: "ECSS", accessed: "2026-08-25"}
---

# Books, standards and open courseware — an annotated catalogue

**Summary.** A short, opinionated list of what to actually read, what each book is good and bad at, and — importantly — which are free. The field has a handful of genuinely canonical texts and a great deal of derivative material; this catalogue covers the canon plus the free primary sources that most people don't know exist. **FREE** marks material available at no cost with a working link.

> ⚠️ Edition numbers and prices change. Verify the current edition before purchase; several entries below carry an edition caveat.

## Key facts

| Reference | Edition / date | Free? |
|---|---|---|
| Sutton & Biblarz, *Rocket Propulsion Elements* | 9th ed., 2016, Wiley **[needs-verification]** | No |
| Curtis, *Orbital Mechanics for Engineering Students* | 4th ed., 2020, Elsevier **[needs-verification]** | No |
| Vallado, *Fundamentals of Astrodynamics and Applications* | 4th ed. (2013, March 2022 printing); a 5th ed. is referenced by CelesTrak **[needs-verification]** | Code **FREE** |
| Bate, Mueller & White, *Fundamentals of Astrodynamics* | Dover, 1971 | Cheap (~US$20) |
| Wertz & Larson, *SMAD* / *The New SMAD* | 3rd ed. 1999 / 2011, Microcosm | No |
| NASA Systems Engineering Handbook | NASA/SP-6105, rev. 27 Mar 2024 | **FREE** |
| NASA RP-1311 Parts I & II (CEA) | Part I: October 1994 | **FREE** on NTRS |
| ECSS standards | Various, see ecss.nl | **FREE** under licence |

## 1. Propulsion

**Sutton & Biblarz, *Rocket Propulsion Elements*** — Wiley, **9th edition (2016)** **[needs-verification: confirm whether a 10th edition has appeared]**. First published 1949 and continuously revised since; George Sutton essentially defined the genre. This is *the* propulsion textbook and if you buy one book on the subject, buy this. Covers nozzle theory, propellant chemistry, liquid and solid systems, hybrids, electric propulsion, combustion instability, testing and safety. Strengths: enormous breadth, real hardware data throughout, excellent tables. Weaknesses: it is a survey, so the depth on any single topic is moderate; the electric propulsion chapters lag the field; and the notation is occasionally dated. Buy a used copy of any edition from the 7th onward — the fundamentals do not change.

**Humble, Henry & Larson (eds.), *Space Propulsion Analysis and Design*** — McGraw-Hill, 1995 (with later reprints). Out of print and expensive second-hand, but it fills the gap Sutton leaves: it is a *design* book, organised around sizing procedures with worked examples and design tables. If you need to actually size a stage, a turbopump or a solid grain rather than understand the theory, this is the one. The chapters on nuclear and advanced propulsion are dated; the liquid and solid design chapters are not.

**Turner, *Rocket and Spacecraft Propulsion: Principles, Practice and New Developments*** — Springer, 3rd edition (2009). Shorter and more accessible than Sutton, with the best treatment of solid motor design in a general text — grain geometries, burn-rate laws, case design, thrust vector control. Good bridge between undergraduate and professional level. Also strong on launch vehicle staging arithmetic.

**Huzel & Huang, *Modern Engineering for Design of Liquid-Propellant Rocket Engines*** — AIAA Progress in Astronautics and Aeronautics vol. 147, 1992. Originally NASA SP-125 (1967), which is **FREE** on NTRS. This is the Rocketdyne engineering manual: injector design, chamber contours, turbopump layout, valve design, with real drawings and real dimensions from F-1 and J-2 era hardware. Nothing else is this concrete. The AIAA edition is the polished version; the free SP-125 is nearly as good.

**Anderson, *Hypersonic and High-Temperature Gas Dynamics*** — AIAA, 2nd edition (2006). Not a propulsion book but the necessary companion for anything involving re-entry, nozzle flow at high temperature, or real-gas effects. Anderson writes better than anyone in the field; the historical asides are worth the price on their own. Covers Newtonian and modified Newtonian methods, viscous interaction, chemically reacting boundary layers, and the physics behind the blunt-body concept.

**Barrere et al., *Rocket Propulsion*** (Elsevier, 1960) and **Hill & Peterson, *Mechanics and Thermodynamics of Propulsion*** (2nd ed., 1991) are the other two classics; Hill & Peterson is the better choice if you want air-breathing and rocket propulsion in one volume with rigorous thermodynamics.

## 2. Astrodynamics

**Curtis, *Orbital Mechanics for Engineering Students*** — Elsevier/Butterworth-Heinemann, **4th edition (2020)** **[needs-verification]**. The best first book on the subject, by a wide margin. Derivations are complete and readable, every method comes with a worked numerical example, and MATLAB code is provided for essentially every algorithm. Covers the two-body problem, orbital elements, Kepler's and Lambert's problems, orbital manoeuvres, relative motion and rendezvous, interplanetary trajectories, rigid-body dynamics and attitude, satellite attitude control, and rocket vehicle dynamics. If you are learning this alone, start here.

**Vallado, *Fundamentals of Astrodynamics and Applications*** — Microcosm/Springer. The **4th edition (2013, with a March 2022 printing)** is the widely-held version; CelesTrak's code repository refers to a **5th edition** **[needs-verification — confirm which is current before buying]**. This is the professional reference: 1,000+ pages, exhaustive on coordinate and time systems (which is where real work goes wrong), perturbation theory, orbit determination, and numerical methods. It is not a teaching book — it is what you consult when you need the right answer including all the corrections. **The accompanying code is FREE**: the CelesTrak GitHub repository (`CelesTrak/fundamentals-of-astrodynamics`) provides implementations in **C#, MATLAB, Python and C++** covering core orbital mechanics routines, coordinate transformations, covariance conversion, orbit determination and manoeuvre calculations, under the **GNU AGPL v3.0**. The maintainers note C# is the most authoritative implementation, followed by MATLAB and Python.

**Bate, Mueller & White, *Fundamentals of Astrodynamics*** — Dover, 1971. Around US$20 new, and one of the great bargains in technical publishing. Written for USAF Academy cadets, it develops the universal variable formulation, the f and g functions, Lambert's problem via the Gauss method, and patched conics with genuine clarity. The orbit determination material is dated and the notation differs from modern practice, but the core is timeless. Buy it regardless of what else you buy.

**Battin, *An Introduction to the Mathematics and Methods of Astrodynamics*** — AIAA, revised edition 1999. The hard one. Battin was the MIT Instrumentation Laboratory's guidance theorist for Apollo and this book is where the deep mathematics lives — variation of parameters, the Battin–Vaughan Lambert algorithm, elegant treatments most texts skip. Not a first book, but the one serious practitioners eventually own.

**Montenbruck & Gill, *Satellite Orbits: Models, Methods and Applications*** — Springer, 2000. The best book on numerical orbit propagation and orbit determination in practice: force models, numerical integrators, least-squares and Kalman estimation, with C++ code. If you are implementing a propagator, this is the reference.

**Schaub & Junkins, *Analytical Mechanics of Space Systems*** — AIAA, 4th edition (2018). The bridge between astrodynamics and attitude dynamics, and the theoretical basis behind the **Basilisk** simulation framework. Excellent on attitude parameterisations (including modified Rodrigues parameters, which Schaub popularised), nonlinear control and relative orbital motion.

## 3. Spacecraft systems

**Wertz & Larson (eds.), *Space Mission Analysis and Design*** — Microcosm, 3rd edition (1999), universally called **SMAD**. For twenty years the single most-used book in the industry. Its virtue is that it is organised as a *process*: define the mission, derive requirements, size each subsystem with first-order equations and lookup tables, iterate. The tables of typical values — mass fractions, power densities, pointing accuracies, cost model coefficients — are what people actually use it for.

**Wertz, Everett & Puschell (eds.), *Space Mission Engineering: The New SMAD*** — Microcosm, 2011. The successor. Substantially rewritten, more content on smallsats and constellations, updated cost models. Both are expensive and both are worth it if you do mission design. If choosing one: New SMAD for current practice, classic SMAD for the tables and the terser style — many practitioners keep both.

**Fortescue, Stark & Swinerd (eds.), *Spacecraft Systems Engineering*** — Wiley, 4th edition (2011). The British counterpart to SMAD, and a better *textbook* — it reads as a coherent course rather than a handbook. Chapter-by-chapter subsystem coverage with derivations rather than lookup tables. Strong on the European approach and on launch vehicle interfaces. If you want to learn spacecraft engineering rather than look things up, prefer this to SMAD.

**Griffin & French, *Space Vehicle Design*** — AIAA, 2nd edition (2004). Mike Griffin later ran NASA. This is the design-oriented middle ground: more depth than SMAD on any given subsystem, more breadth than a specialist text, with real engineering judgement in the prose. Particularly good on propulsion sizing, structures and the launch environment.

**Wertz (ed.), *Spacecraft Attitude Determination and Control*** — Reidel/Kluwer, 1978. Still the standard reference after almost fifty years, and still in print. Exhaustive on attitude parameterisations, sensor and actuator models, deterministic and statistical attitude determination (this is where TRIAD and QUEST are properly documented), and control. The hardware chapters are historical; the mathematics is not.

**Markley & Crassidis, *Fundamentals of Spacecraft Attitude Determination and Control*** — Springer, 2014. The modern replacement for Wertz on the estimation side: rigorous, current, and the best treatment of the multiplicative extended Kalman filter available.

**Gilmore (ed.), *Spacecraft Thermal Control Handbook, Volume I: Fundamental Technologies*** — Aerospace Press/AIAA, 2nd edition (2002). The thermal bible. Volume II covers cryogenics. Everything: environments, surface properties and their degradation, MLI, heat pipes, louvres, radiators, thermal analysis practice, and test. If you do thermal, you own this.

**Larson & Pranke (eds.), *Human Spaceflight: Mission Analysis and Design*** — McGraw-Hill, 1999. The SMAD of crewed missions: life support, EVA, habitat design, crew systems, abort analysis. Dated on programme specifics, sound on fundamentals, and there is no real competitor.

**Pisacane (ed.), *Fundamentals of Space Systems*** — Oxford, 2nd edition (2005). From the Johns Hopkins APL course. Denser and more mathematical than SMAD; excellent chapters on power and on space environment effects.

## 4. Free primary sources

**NASA Systems Engineering Handbook, NASA/SP-6105** — **FREE**, revision of **27 March 2024**. Six sections: introduction, fundamentals of systems engineering, the NASA programme/project life cycle, system design processes, product realisation, and crosscutting technical management. Incorporates model-based systems engineering and current NPR 7123.1. This is how large space projects are actually managed and it is a better systems engineering education than most university courses.

**The NASA SP series** — a treasure and largely forgotten. All **FREE** on NTRS (ntrs.nasa.gov):
- **SP-125**, *Design of Liquid Propellant Rocket Engines* (Huzel & Huang, 1967) — the Rocketdyne manual, as noted above.
- **SP-8000 series, Space Vehicle Design Criteria** — around 100 monographs, each a distilled design guide on one topic (SP-8007 buckling of thin-walled cylinders, SP-8057 structural design criteria for lunar landers, SP-8113 combustion instability, and so on). These are terse, quantitative and still used.
- **SP-33**, *Planetary Flight Handbook*; **SP-35**, *Aerodynamic Design of Axial-Flow Compressors*; **SP-290**, *Turbine Design and Application*.
- **RP-1311 Parts I and II**, *Computer Program for Calculation of Complex Chemical Equilibrium Compositions and Applications* (Gordon & McBride) — Part I (Analysis) is **NASA-RP-1311, 1 October 1994**, freely downloadable from NTRS. This is the CEA theory manual and the reference for anything involving propellant performance calculation. See `09` for running the code.
- **SP-4000 series** — the NASA History Series, including *Stages to Saturn* and *What Made Apollo a Success*, all free and genuinely informative about engineering as well as history.

**ECSS standards** — **FREE** from ecss.nl subject to accepting the licence agreement; a zip of all active standards is available. Branches E (engineering), M (management), Q (product assurance), S (system implementation), U (space sustainability). Start with **ECSS-E-ST-10C Rev.1** (system engineering general requirements, 15 February 2017), then the branch relevant to your work: **ECSS-E-ST-32C Rev.1** (structures), **ECSS-E-ST-35C Rev.1** (propulsion), **ECSS-Q-ST-70C Rev.2** (materials, mechanical parts and processes), **ECSS-U-ST-20C** (planetary protection).

**NASA Technical Standards** (standards.nasa.gov) — **FREE**. **GSFC-STD-7000 (GEVS)** for environmental verification levels, **NASA-STD-5001** for structural factors of safety, the **NASA-STD-8739** workmanship series, **NASA-HDBK-4002** on spacecraft charging.

**NASA Technical Reports Server (ntrs.nasa.gov)** — **FREE**. Millions of documents. The single most underused resource in the field. If you want to know how something was actually done, it is probably here.

**CCSDS Blue Books** (ccsds.org) — **FREE**. The international standards for space data systems: packet telemetry and telecommand, space link extension, the CCSDS File Delivery Protocol, and the coding standards (LDPC, turbo, Reed–Solomon) used across almost all missions.

**The Space Report / Bryce Tech reports** — some free, some paid; the standard source for industry statistics.

**arXiv (astro-ph.IM, physics.space-ph)** — **FREE**. Instrument papers, mission descriptions and analysis techniques.

## 5. Open courseware

**MIT OpenCourseWare** — **FREE**. The strongest set available:
- **16.07 Dynamics** and **16.06/16.30/16.31 Feedback Control Systems and Estimation** — the GNC foundation.
- **16.512 Rocket Propulsion** (Manuel Martinez-Sanchez) — the best free propulsion course anywhere, including the electric propulsion lectures.
- **16.522 Space Propulsion** — electric propulsion in depth from the same author.
- **16.851 Satellite Engineering** and **16.89 Space Systems Engineering** — project-based, with real design documents as materials.
- **12.410 Observational Techniques of Optical Astronomy**.

**edX/Coursera** — TU Delft's *Space Mission Design and Operations* and *Introduction to Aerospace Structures and Materials*; University of Colorado Boulder's **Spacecraft Dynamics and Control** specialisation (Hanspeter Schaub — the same author as the Schaub & Junkins text, and the courses use Basilisk); Caltech's *The Evolving Universe*.

**ESA Learning Zone and ESA Academy** — training materials, and the ESA Education Office's CubeSat and Fly Your Satellite! documentation is a free, complete, real project-management and verification curriculum.

**AIAA and IAF conference proceedings** — mostly paywalled, but many authors post preprints, and IAC papers often surface on ResearchGate and institutional repositories.

**The Orbital Mechanics podcast, and the Everyday Astronaut engine explainers** — not references, but unusually accurate popular material that is genuinely useful for building intuition before tackling the textbooks.

## 6. A suggested reading order

1. **Bate, Mueller & White** (cheap, short) to see whether the subject suits you.
2. **Curtis** properly, working the examples, alongside **MIT 16.07**.
3. **Fortescue** or **SMAD** for the systems view.
4. **Sutton** for propulsion breadth, with **MIT 16.512** for depth.
5. Then specialise: **Vallado** + **Montenbruck & Gill** for flight dynamics; **Markley & Crassidis** + **Schaub & Junkins** for GNC; **Gilmore** for thermal; **Huzel & Huang** + **Humble** for engine design; **Anderson** for entry.
6. Read **NASA/SP-6105** and **ECSS-E-ST-10C** at any point — they cost nothing and change how you think about the rest.

## Open questions

- Sutton & Biblarz edition: 9th (2016) is the last confirmed; a later edition may exist.
- Curtis edition: 4th (2020) is widely cited; verify whether a 5th has appeared.
- Vallado: CelesTrak's page states 4th edition (March 2022 printing) while the CelesTrak code repository refers to the 5th edition. Confirm before purchase.
- Prices are not given because they vary by region and vendor and go stale immediately.

## Sources

- [Vallado software and code](https://celestrak.org/software/vallado-sw.php) — CelesTrak, accessed 2026-08-25
- [CelesTrak fundamentals-of-astrodynamics repository](https://github.com/CelesTrak/fundamentals-of-astrodynamics) — GitHub, accessed 2026-08-25
- [NASA RP-1311 Part I, Gordon & McBride, October 1994](https://ntrs.nasa.gov/citations/19950013764) — NASA NTRS, accessed 2026-08-25
- [NASA Systems Engineering Handbook (NASA/SP-6105)](https://www.nasa.gov/reference/systems-engineering-handbook/) — NASA, accessed 2026-08-25
- [ECSS active standards](https://ecss.nl/standards/active-standards/) — ECSS, accessed 2026-08-25
