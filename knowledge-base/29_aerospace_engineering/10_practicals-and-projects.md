---
id: aerospace.practicals
title: Practicals, software skills, projects and competitions
domain: 29_aerospace_engineering
tags: [wind-tunnel, instrumentation, structures-testing, propulsion-test-cell, flight-test, matlab, python, xfoil, xflr5, openvsp, su2, openfoam, ansys-fluent, abaqus, nastran, catia, projects, uav, cfd-validation, competitions, dbf, cansat, spaceport-america-cup, urc, internships]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "AIAA Design/Build/Fly", url: "https://www.aiaa.org/dbf", publisher: "AIAA", accessed: 2026-08-25}
  - {title: "University Rover Challenge", url: "https://urc.marssociety.org/", publisher: "The Mars Society", accessed: 2026-08-25}
  - {title: "Formula Student Germany — Concept", url: "https://www.formulastudent.de/about/concept/", publisher: "Formula Student Germany", accessed: 2026-08-25}
  - {title: "XFOIL", url: "https://web.mit.edu/drela/Public/web/xfoil/", publisher: "M. Drela, MIT", accessed: 2026-08-25}
  - {title: "SU2", url: "https://su2code.github.io/", publisher: "SU2 Foundation", accessed: 2026-08-25}
  - {title: "OpenVSP", url: "https://openvsp.org/", publisher: "NASA / OpenVSP community", accessed: 2026-08-25}
  - {title: "Cranfield Aerospace Dynamics MSc", url: "https://www.cranfield.ac.uk/courses/taught/aerospace-dynamics", publisher: "Cranfield University", accessed: 2026-08-25}
  - {title: "MIT Course 16 subject listing", url: "http://student.mit.edu/catalog/m16a.html", publisher: "MIT", accessed: 2026-08-25}
related: [aerospace.curriculum, aerospace.books, aerospace.aerodynamics]
unit_system: SI
---

# Practicals, software skills, projects and competitions

**Summary.** Aerospace competence is demonstrated, not claimed. The gap between someone who has read Anderson and someone employable is a set of specific practical abilities: instrumenting a measurement and knowing its uncertainty, running a CFD case and being able to defend the mesh, sizing an aircraft and defending the assumptions, and building something that flies. This file catalogues the laboratory work a degree contains, the software an employer expects, the projects that actually build capability, the competitions that compress a whole programme into nine months, and the routes into industry.

## Key facts

| Item | Value |
|---|---|
| **AIAA Design/Build/Fly 2025–26** | Proposals 15–31 Oct 2025; team notification 21 Nov 2025; final report 1–20 Feb 2026; **fly-off 16–19 April 2026** at the Textron Aviation Employees' Flying Club, **Wichita, Kansas**. 30th year of the competition. **2026 mission: a Banner Towing Bush Plane.** All members must hold AIAA Student Membership |
| **University Rover Challenge 2026** | Organised by **The Mars Society**; finals **27–30 May 2026** at the **Mars Desert Research Station, Hanksville, Utah**; **38 teams** in the finals; gated by a Preliminary Design Review, System Acceptance Review, Science Plan and a Delivery Mission Course; partnered with the **INCOSE Foundation** for systems-engineering recognition |
| **Formula Student** | Students "build a single seated formula style car"; judged on **static events** (construction, cost planning, sales presentation, assessed by motorsport and automotive industry experts) and **dynamic events** on track — not on speed alone |
| **XFOIL** | Free, GPL, **v6.99 (23 Dec 2013)**, Drela & Youngren, MIT |
| **SU2** | Free, **LGPL 2.1**, governed by the **SU2 Foundation**; discrete adjoints, shape optimisation, NICFD, incompressible flow with heat transfer, HPC |
| **OpenVSP** | Free, NASA-originated, **v3.51.3 (17 August 2026)** |
| **Cranfield flight test** | The MSc Aerospace Dynamics includes a **group flight test project** (two compulsory modules) flown on the **National Flying Laboratory Centre** aircraft |
| **MIT hands-on composites subject** | **16.202 Manufacturing with Advanced Composite Materials**, 1-3-2 units — fabrication and testing of composite specimens |

---

## 1. The laboratory work

### Wind tunnel testing and its instrumentation

A typical undergraduate low-speed tunnel is an open-return (Eiffel) or closed-return (Göttingen) design with a 0.3–1.0 m² working section running at 10–50 m/s, giving chord Reynolds numbers of 10⁵–5×10⁵ — an important limitation, because that is an order of magnitude below flight and the boundary layer behaves differently.

**What gets measured, and with what:**

| Quantity | Instrument | Practical notes |
|---|---|---|
| Freestream velocity | Pitot-static probe + micromanometer or pressure transducer | `V = √(2(p_t − p_s)/ρ)`; needs air density from measured `p` and `T`. Check the probe is aligned within a few degrees |
| Surface pressure | Pressure taps + multi-channel scanner (Scanivalve, or an electronic pressure scanner) | Integrate `C_p` around the section to get `c_l` and `c_m`; the tap in the separated region is where your integration goes wrong |
| Forces and moments | External or internal **strain-gauge balance** (3- or 6-component) | Calibration matrix with interaction terms; **model support (sting/strut) tare and interference correction** is essential and is the single largest error source in a student experiment |
| Profile drag | **Wake rake** (a comb of total-pressure tubes) + momentum-deficit integration | Far more accurate than a balance for 2-D drag; `c_d = 2∫(u/U)(1−u/U)dy/c` |
| Boundary layer profile | Flattened Pitot traversed on a micrometer stage, or **hot-wire anemometry** (CTA) | Hot wire gives turbulence intensity and spectra; fragile and needs careful calibration |
| Velocity field | **PIV** (particle image velocimetry) — seeded flow, laser sheet, double-pulse camera, cross-correlation | The modern standard; expensive but increasingly common in undergraduate labs |
| Flow visualisation | Smoke/tufts/oil film/china clay/IR thermography | Cheap, and the fastest route to understanding what is actually happening |
| Model attitude | Angle-of-attack drive with encoder | Backlash matters |

**Corrections you must apply and be able to justify:** solid blockage, wake blockage, streamline curvature and downwash corrections for a closed test section (Maskell/Glauert), buoyancy from the streamwise static pressure gradient, and Reynolds-number scaling. A student report that quotes `c_l` to four significant figures without a corrections section and an uncertainty budget is worthless, and every good lab course says so.

**Higher-speed facilities:** transonic and supersonic blowdown tunnels (with **schlieren** or shadowgraph for shock visualisation), shock tubes, Ludwieg tubes, hypersonic guns and arc-heated facilities, water tunnels for flow visualisation at low Reynolds number, and — increasingly — anechoic tunnels for aeroacoustics.

### Structures testing

- **Tensile, compressive and shear coupon tests** to ASTM standards on a universal testing machine, with an extensometer and/or strain gauges; determine E, `σ_y`, `σ_UTS`, elongation and reduction of area.
- **Strain gauging**: quarter/half/full Wheatstone bridge, temperature compensation, gauge factor, rosettes to extract principal strains and their direction. This is a genuinely useful and transferable skill.
- **Buckling of columns and stiffened panels** — measure `P_cr` and compare with Euler and with the effective-width prediction; the discrepancy is the lesson.
- **Shear centre determination** on an open channel section.
- **Torsion of a thin-walled box** and comparison with Bredt–Batho.
- **Modal / vibration testing**: impulse hammer or shaker excitation, accelerometers, FRF measurement, mode shape extraction; a GVT in miniature.
- **Fatigue**: rotating-bending or servo-hydraulic axial fatigue to build an S–N curve, then fractography of the failure surface — beach marks, the initiation site, the final overload zone.
- **Composite fabrication and test** — MIT's **16.202 Manufacturing with Advanced Composite Materials** (1-3-2) is a hands-on layup and test subject; the general pattern is hand layup, vacuum bag, oven or autoclave cure, then tensile/ILSS/CAI testing and a void-content check by acid digestion or micrograph.
- **NDT familiarisation**: dye penetrant, eddy current, ultrasonic A-scan/C-scan, and how a defect actually presents.

### Propulsion test cells

- **Small gas turbine rig** — an SR-30 or a JetCat-class turbojet instrumented at each station for total and static pressure and temperature; students compute component efficiencies, plot the compressor and turbine map points, and derive thrust and TSFC. The gap between the measured and ideal cycle is the lesson.
- **Cascade rig** — a linear cascade of compressor or turbine blades in a wind tunnel; measure blade loading and loss coefficient vs incidence, and find the stall incidence.
- **Piston engine dynamometer** — brake power, BSFC, volumetric efficiency, and a full heat balance.
- **Rocket static fire** — solid motor or a small liquid/hybrid, with a load cell for thrust, a chamber pressure transducer, and thermocouples. `c* = p_c A_t/ṁ` and `C_F = F/(p_c A_t)` separate combustion efficiency from nozzle efficiency, which is the single most useful thing a rocket test teaches.
- **Electric propulsion** — thrust stand measurement of a Hall or ion thruster in a vacuum chamber (MIT's **16.522 Space Propulsion** is 3-3-6 with a laboratory project).

### Flight test

The most valuable and least common lab. Where a programme has an aircraft — **Cranfield's National Flying Laboratory Centre**, TU Delft, Embry-Riddle, the USAF/USN test pilot schools, or a partnered flying club — the standard exercises are:
- **Sawtooth climbs** at a series of speeds → rate of climb vs speed → excess power → drag polar.
- **Level-flight performance**: power/thrust required vs speed at constant weight and altitude, corrected to standard conditions.
- **Stall speed determination** at several configurations and weights, corrected to 1 g.
- **Static longitudinal stability**: elevator angle and stick force vs speed at several CGs → neutral point by extrapolation.
- **Dynamic modes**: excite the **phugoid** (pulse and release), **short period** (doublet), **Dutch roll** (rudder doublet), **spiral** (bank and release) and identify frequency and damping from the time histories.
- **Takeoff and landing distance** measurement and correction.
- **Data reduction and uncertainty** — the point of the whole exercise.

Even without an aircraft, a well-instrumented model, a simulator with data output, or a Pixhawk-equipped UAV reproduces most of these exercises honestly.

---

## 2. Software skills employers actually expect

| Tool | Why | How to acquire it |
|---|---|---|
| **MATLAB / Simulink** | Still the lingua franca for control design, flight dynamics, signal processing and rapid analysis. Simulink is the de-facto standard for control law development and autocode (with Embedded Coder feeding DO-178C workflows via DO-331) | University licence; MathWorks Onramp courses are free and good |
| **Python** | Rapidly displacing MATLAB for analysis and automation. NumPy/SciPy/pandas/Matplotlib, plus `scipy.optimize`, `control`, `pyvista`, `CoolProp`, `poliastro`/`astropy` for orbital work, and `pymoo` for optimisation | Free; the highest-return investment on this list |
| **XFOIL / XFLR5** | 2-D airfoil analysis and design in seconds, with viscous effects and `e^N` transition; XFLR5 adds LLT/VLM/3-D panel for whole aircraft | Free; XFOIL v6.99 GPL |
| **AVL** | Vortex lattice with trim and full stability-derivative output — the fastest route from geometry to `C_{mα}`, `C_{nβ}` and the dynamic modes | Free (Drela, MIT) |
| **OpenVSP + VSPAERO** | Parametric aircraft geometry, mass properties, parasite drag build-up and VLM/panel aero; the bridge from sketch to analysis. v3.51.3 (Aug 2026) | Free; the OpenVSP Ground School is the tutorial set |
| **SU2** | Open-source compressible/incompressible RANS with **discrete adjoints and shape optimisation** under LGPL 2.1 | Free; excellent tutorials |
| **OpenFOAM** | Open-source finite-volume CFD; steeper learning curve, enormous flexibility | Free |
| **ANSYS Fluent / CFX / Star-CCM+** | The commercial CFD you will meet in industry; know the meshing workflow (`y⁺` targets, prism layers, refinement regions), the turbulence model choice, and the convergence/grid-independence discipline | University licence; ANSYS Student is free with cell-count limits |
| **Abaqus / MSC Nastran / Patran / Femap** | Structural FEM. Nastran is the aerospace standard for linear statics, normal modes, buckling and aeroelasticity (SOL 144/145/146); Abaqus for nonlinear, contact, composites and damage | University licence |
| **CATIA V5 / 3DEXPERIENCE, Siemens NX, SolidWorks, Fusion** | CAD. CATIA is the airframe standard and NX is common at engine makers and Tier 1s; SolidWorks/Fusion/Onshape are fine for learning parametric modelling and are what a student project will actually use | Student licences widely available |
| **Ansys/Siemens systems tools, Cameo/MagicDraw, Capella** | MBSE in SysML; Capella is free and open source | Free (Capella) |
| **Git, Linux, shell, HPC batch schedulers (SLURM)** | Non-negotiable for anything computational. A CFD engineer who cannot submit a job to a cluster is not a CFD engineer | Free |
| **LaTeX** | Reports, theses and papers | Free |

A realistic minimum for employability in a technical aerospace role: **Python + MATLAB/Simulink + one CFD code + one FEM code + one CAD package + Git**, with the ability to explain the assumptions inside each.

---

## 3. Projects that build real capability

Ranked by what they demonstrate to an employer.

### 3.1 Design, build and fly a UAV end to end
The single highest-value project, because it forces every discipline to meet reality.
- **Requirements**: pick a mission (a 3 kg payload, 45 minutes endurance, hand launch, 1 km range) and write it down.
- **Sizing**: run the weight loop with an electric-specific range/endurance model (`E = (1/g)(η_total/ (P_req/W)) · (E_batt/W)` — battery specific energy replaces the Bréguet fuel fraction).
- **Aero**: choose an airfoil at the right Reynolds number in XFOIL (expect `Re_c` of 100,000–400,000 and therefore separation bubbles); size the wing and tail; check `C_{mα}` and the static margin in AVL.
- **Structure**: spar sizing to a limit load factor you choose and justify, with a real safety factor; build in foam/balsa/CFRP; **load-test the wing to limit load with sandbags before you fly it**.
- **Propulsion**: match motor, ESC, propeller and battery using measured static thrust and a propeller database (APC data, or UIUC's propeller database).
- **Avionics**: Pixhawk/ArduPilot or PX4, tune the loops, set up failsafes, log everything.
- **Flight test**: measure what you predicted — stall speed, climb rate, endurance, and the drag polar from glide tests. **The comparison of prediction to measurement is the deliverable.**

### 3.2 A CFD study with genuine validation
Not "I ran Fluent and it looked pretty." Pick a case with published experimental data — the **NASA 2-D NACA 0012 validation case**, the **ONERA M6 wing**, the **NASA Common Research Model**, or a backward-facing step — and:
1. Build three systematically refined grids and demonstrate grid convergence with Richardson extrapolation and a grid-convergence index.
2. Run at least two turbulence models (SA and k-ω SST) and quantify the difference.
3. Compare to the experiment *including* the places where it does not match, and explain why.
4. State the uncertainty of your answer.
This one project separates people who can use CFD from people who can operate CFD software.

### 3.3 A full aircraft sizing exercise on a known aircraft
Take an aircraft you know intimately — for a line pilot, the one on your licence — and size it from its published requirements using Raymer's method. Predict MTOW, wing area, thrust, empty weight and fuel burn; then compare to the real numbers. You will be wrong by 10–20 % somewhere, and finding out where is the education. Then do the same for an aircraft that does not exist yet.

### 3.4 Build a model rocket to a target altitude
- Design in **OpenRocket** (free) with a chosen motor; predict apogee, max velocity, max acceleration and stability margin (calibre).
- Verify the CP/CG margin physically (swing test) as well as analytically.
- Build, fly with an altimeter, and compare measured apogee to prediction. The discrepancy will be drag coefficient and it will teach you more than any textbook chapter on drag.
- Progress to dual-deploy recovery, then to a student-researched-and-developed (SRAD) motor if a competent supervising body exists. **Amateur solid propellant work is genuinely dangerous and is regulated** — do it inside an organised body, never alone.

### 3.5 Contribute to an open-source aerospace project
The most under-used credential available. Live, welcoming projects: **SU2**, **OpenFOAM**, **OpenVSP**, **OpenMDAO / OpenAeroStruct** (Michigan MDO Lab), **ArduPilot / PX4**, **OpenRocket**, **poliastro/astropy**, **Basilisk** (spacecraft simulation), **RocketPy**. Start with documentation and validation cases, move to bug fixes, then to features. A merged pull request in SU2 is more persuasive than a grade.

### 3.6 A CubeSat or high-altitude balloon payload
Balloons are the cheap version: a payload to 30 km with a GPS tracker, a camera, and a real thermal and pressure environment, launched under the applicable national aviation permission (**[ZA]** SACAA; **[NA]** NCAA — permission is required, and this is not optional). CubeSats are the expensive version, usually via a university programme (CPUT's **F'SATI** built **ZACube-1** and **ZACube-2** — the southern African precedent).

---

## 4. Student competitions

| Competition | Organiser | What it demands |
|---|---|---|
| **AIAA Design/Build/Fly (DBF)** | AIAA | Design, fabricate and demonstrate an unmanned, electric, radio-controlled aircraft against an annually changing mission. **2025–26 cycle: proposals 15–31 Oct 2025, notifications 21 Nov 2025, final report 1–20 Feb 2026, fly-off 16–19 April 2026 at the Textron Aviation Employees' Flying Club, Wichita, Kansas.** The **2026 mission is a Banner Towing Bush Plane**; 2026 is the competition's **30th year**. Scoring combines a written report, flight mission scores and rated aircraft cost, so a beautiful aeroplane that misses the report deadline scores zero. All members need AIAA Student Membership |
| **SAE Aero Design** | SAE International | Payload-lifting competition in Regular, Advanced and Micro classes, with a design report and presentation alongside the flight rounds (class definitions and current dates `needs-verification` — the SAE page did not render) |
| **Formula Student / Formula SAE** | SAE / IMechE / FSG and national bodies | Students "build a single seated formula style car"; judged on **static events** — construction, cost planning and sales presentation assessed by motorsport and automotive industry experts — and **dynamic events** on track. Not an aerospace competition, but the best available training in project management, manufacturing, and defending an engineering decision to a hostile expert. Its aerodynamics subteam is a legitimate aero apprenticeship, and its driverless class is a serious autonomy exercise |
| **CanSat** (ESA, NASA/AAS, and national programmes) | ESA Education and others | Build a satellite-like payload in a 330 ml drinks-can volume, launched by rocket or balloon to ~1 km, with a primary mission (telemetry of temperature and pressure during descent) and a self-chosen secondary mission. The best low-cost introduction to the full systems-engineering cycle (ESA page returned HTTP 403; current dates `needs-verification`) |
| **Spaceport America Cup** | Experimental Sounding Rocket Association (ESRA), New Mexico | The world's largest intercollegiate rocket engineering competition, with categories at **10,000 ft and 30,000 ft apogee**, each split into **COTS**, **SRAD solid/liquid/hybrid** motor classes, and a payload requirement. Teams number in the low hundreds from dozens of countries (site blocked automated access; current dates and category details `needs-verification`) |
| **University Rover Challenge (URC)** | **The Mars Society** | Build a Mars-analogue rover. **2026 finals 27–30 May 2026 at the Mars Desert Research Station, Hanksville, Utah**, with **38 finalist teams**. Gated by a **Preliminary Design Review, System Acceptance Review, Science Plan** and a **Delivery Mission Course**; partnered with the **INCOSE Foundation** to recognise systems-engineering work. Sponsors in 2026 included MDA Space, Nissan Advanced Technology Center, Astrolab, Honeybee Robotics and ProtoSpace Manufacturing |
| **European Rover Challenge (ERC)** | Poland | The European analogue of URC |
| **AIAA Student Design Competitions** | AIAA | Paper design competitions in aircraft, engine, spacecraft, missile and undergraduate/graduate team categories — the closest thing to a real RFP response, and excellent CV material |
| **DARPA / NASA challenges, Hyperloop, IMechE UAS Challenge, REXUS/BEXUS (ESA/DLR/SNSA)** | Various | REXUS/BEXUS in particular flies student experiments on sounding rockets and stratospheric balloons and is an outstanding, genuinely spaceflight-adjacent programme |
| **[ZA] SA competitions** | | The SA CanSat/Space Challenge activity, university UAV competitions, and Formula Student South Africa exist but with less continuity than the international events; check current status each year |

**How to get value out of a competition team**: take a subsystem you can own end-to-end, keep an engineering notebook with dated decisions and their justification, do the analysis *and* the test, and write the report. Interviewers ask "what did *you* do, what went wrong, and what did you change?" — a team that won means nothing if you cannot answer that.

---

## 5. Internships, graduate schemes and the route in

**Europe/UK**
- **Airbus** — 6–12 month industrial placements and a graduate programme in the UK (Filton, Broughton), France, Germany and Spain; the placement route is the single most reliable entry.
- **Rolls-Royce** — a long-established and well-regarded graduate scheme and summer internships; strong in Derby (civil aerospace).
- **BAE Systems, Leonardo, MBDA, Safran, Thales, GKN, Collins** — structured schemes, most requiring nationality/security clearance for defence work.
- **ESA** — the **Young Graduate Trainee (YGT)** programme (one year, ESA establishments) and the **NPI** PhD scheme; highly competitive, ESA member/associate state nationality required.
- **DLR, ONERA, NLR, VKI** — the **von Karman Institute** Research Master and Short Training Programme in Belgium are outstanding and open internationally.

**United States**
- **NASA** — the **Pathways** internship programme and **NASA Internships (OSSI)**; almost all require US citizenship.
- **SpaceX, Blue Origin, Rocket Lab, Anduril, Joby, Boeing, Lockheed Martin, Northrop, GE Aerospace, Pratt & Whitney** — internships are the primary hiring pipeline; ITAR restricts most roles to US persons.

**Middle East / Asia**
- **Qatar Airways, Emirates, Etihad engineering divisions**; **Mubadala/Strata** (composite manufacturing, Al Ain); **Turkish Aerospace (TAI)**; **HAL, ISRO, DRDO** (India, national restrictions); **COMAC/AVIC** (China).
- Qatar's **Qatar Foundation / HBKU** and the QCAA offer some engineering-adjacent routes; the region's growth area is MRO engineering and airline engineering rather than OEM design.

**[ZA]/[NA] Southern Africa**
- **Denel Aeronautics / Denel Dynamics** (technically significant, financially distressed), **Aerosud**, **Paramount Group**, **Milkor**, **CSIR** (aeronautic systems), **SANSA**, **SAA Technical**, **FlySafair engineering**, and the UAV survey sector.
- The realistic pattern: a South African aerospace degree (Wits BSc(Eng) Aeronautical, or a mechanical degree from UP/Stellenbosch/UCT) → an ECSA candidacy → either the local defence/UAV sector or emigration to a European or Gulf employer. **[NA]** For Namibians there is no domestic aerospace employer; the route is a South African or overseas degree followed by overseas employment, or the aircraft-maintenance-engineering path through an approved Part-147 organisation.

**What actually gets people hired**, in rough order of weight: a relevant internship or placement; a competition team role you can describe technically; a strong final-year or master's project with a real result; demonstrable software skill (a public repository); and — for anyone already in aviation — **operational domain knowledge**, which is rarer among graduate engineers than they realise and is disproportionately valuable in certification, flight operations engineering, human factors, flight test and airline engineering roles.

## Sources

- [AIAA Design/Build/Fly](https://www.aiaa.org/dbf) — AIAA (2025–26 timeline, 2026 mission, fly-off venue)
- [University Rover Challenge](https://urc.marssociety.org/) — The Mars Society (2026 finals dates, location, team count, review gates)
- [Formula Student Germany — Concept](https://www.formulastudent.de/about/concept/) — Formula Student Germany
- [XFOIL](https://web.mit.edu/drela/Public/web/xfoil/) — Mark Drela, MIT
- [SU2](https://su2code.github.io/) — SU2 Foundation
- [OpenVSP](https://openvsp.org/) — NASA / OpenVSP community
- [Cranfield Aerospace Dynamics MSc](https://www.cranfield.ac.uk/courses/taught/aerospace-dynamics) — Cranfield University (group flight test project, National Flying Laboratory Centre)
- [MIT Course 16 subject listing](http://student.mit.edu/catalog/m16a.html) — MIT (16.202, 16.522)

## Open questions

- **SAE Aero Design** current class definitions and event dates — sae.org did not render; `needs-verification`.
- **Spaceport America Cup** current categories, team counts and 2026 dates — site disallowed automated access; `needs-verification`.
- **ESA CanSat** current competition structure and dates — esa.int returned HTTP 403; `needs-verification`.
- Formula Student class structure (combustion / electric / driverless) and the points allocation — not present on the fetched page; `needs-verification`.
- Current status and continuity of South African student aerospace competitions — `needs-verification`.
- Nationality and clearance requirements for the named graduate schemes change frequently; check each employer's current terms.
