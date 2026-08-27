---
id: aerospace.curriculum
title: The aerospace engineering degree and curriculum
domain: 29_aerospace_engineering
tags: [curriculum, degree, mit-ocw, nptel, textbooks, prerequisites, universities, abet, ecsa, capstone]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "MIT Course 16 undergraduate subject listing", url: "http://student.mit.edu/catalog/m16a.html", publisher: "MIT", accessed: 2026-08-25}
  - {title: "MIT Course 16 graduate subject listing", url: "http://student.mit.edu/catalog/m16b.html", publisher: "MIT", accessed: 2026-08-25}
  - {title: "16.100 Aerodynamics, Fall 2005", url: "https://ocw.mit.edu/courses/16-100-aerodynamics-fall-2005/", publisher: "MIT OpenCourseWare", accessed: 2026-08-25}
  - {title: "NPTEL course archive", url: "https://archive.nptel.ac.in/course.html", publisher: "NPTEL / IITs & IISc", accessed: 2026-08-25}
  - {title: "Wits School of Mechanical, Industrial and Aeronautical Engineering — undergraduate", url: "https://www.wits.ac.za/mia/undergraduate-studies/", publisher: "University of the Witwatersrand", accessed: 2026-08-25}
  - {title: "UP Department of Mechanical and Aeronautical Engineering", url: "https://www.up.ac.za/mechanical-and-aeronautical-engineering", publisher: "University of Pretoria", accessed: 2026-08-25}
  - {title: "Stellenbosch Department of Mechanical and Mechatronic Engineering", url: "https://www.su.ac.za/en/faculties/engineering/departments/mechanical-mechatronic-engineering", publisher: "Stellenbosch University", accessed: 2026-08-25}
  - {title: "Aerospace Dynamics MSc", url: "https://www.cranfield.ac.uk/courses/taught/aerospace-dynamics", publisher: "Cranfield University", accessed: 2026-08-25}
  - {title: "TU Delft Faculty of Aerospace Engineering", url: "https://www.tudelft.nl/en/ae", publisher: "TU Delft", accessed: 2026-08-25}
related: [aerospace.overview, aerospace.books, aerospace.practicals]
unit_system: SI
---

# The aerospace engineering degree and curriculum

**Summary.** An aerospace degree is a four-year (or 3+2) forced march through applied mathematics, then through six technical pillars, ending in a capstone design project that pretends to be an industrial programme. The prerequisite chain is unusually rigid: you cannot do aerodynamics without fluid mechanics, cannot do fluid mechanics without vector calculus and ODEs, cannot do aeroelasticity without both structures and aerodynamics, cannot do control without Laplace transforms and linear algebra. This file gives the module map with prerequisites, the standard textbook for each, the free course that actually covers it, and the lab work that goes with it — then the leading programmes and the southern African options.

## Key facts

| Fact | Value |
|---|---|
| Typical structure | Year 1–2 = maths + engineering science; Year 3 = discipline core; Year 4 = electives + capstone |
| US accreditation | **ABET** Engineering Accreditation Commission |
| **[ZA]** accreditation | **ECSA** (Engineering Council of South Africa) — Washington Accord signatory |
| MIT's integrated first-year core | **16.001–16.004 "Unified Engineering"** — Materials & Structures / Signals & Systems / Fluid Dynamics / Thermodynamics & Propulsion, each 5-1-6 units |
| MIT aerodynamics gateway | **16.100 Aerodynamics**, prereq 16.003 + 16.004, 3-1-8 units |
| MIT propulsion gateway | **16.50 Aerospace Propulsion**, prereq 16.003 and (2.005 or 16.004) |
| MIT structures gateway | **16.20 Structural Mechanics**, prereq 16.001, 5-0-7 units |
| MIT control chain | 16.06 Principles of Automatic Control → 16.30/16.31 Feedback Control Systems → 16.32 Optimal Control and Estimation |
| MIT MDO subject | **16.888[J] Multidisciplinary Design Optimization**, prereq 18.085 |
| Free courseware | MIT OCW (ocw.mit.edu), NPTEL (nptel.ac.in), edX, TU Delft OCW |
| Wits **[ZA]** | BSc(Eng) **Aeronautical Engineering**, 4 years full-time; plus an 18-month MSc Aeronautical Engineering with Embry-Riddle |
| UP **[ZA]** | Department of **Mechanical and Aeronautical Engineering**; has an Aeronautical Group, wind tunnels and engine test facilities |

## The prerequisite graph

```
 Calculus I/II  →  Multivariable calculus (vector calc: div, grad, curl, Gauss, Stokes)
        ↓                     ↓
   Linear algebra  →  ODEs  →  PDEs / Numerical methods  →  CFD, FEM
        ↓                ↓             ↓
   Statics  →  Dynamics  →  Vibrations  →  Structural dynamics  →  Aeroelasticity
        ↓                                      ↑                        ↑
   Mechanics of materials → Structures (16.20) ┘                        |
                                                                        |
   Thermodynamics → Fluid mechanics → Aerodynamics (incompressible) ─────┤
                          ↓                 ↓                           |
                    Gas dynamics  →  Compressible aerodynamics  → Transonic/supersonic
                          ↓                 ↓
                    Propulsion         Viscous flow / turbulence → CFD
                                            ↓
   Signals & systems → Control theory → Flight dynamics → Stability & control → Autoflight
                                            ↓
                                    Orbital mechanics → Spacecraft systems
```

Nothing in the right-hand columns can be attempted honestly without the left. The single most common failure mode in self-study is attacking aerodynamics before the vector calculus is fluent.

---

## Year 1–2: the mathematics and mechanics foundation

### M1. Calculus and multivariable/vector calculus
**Covers:** limits, differentiation, integration, sequences and series, Taylor expansion; then partial derivatives, multiple integrals, line and surface integrals, gradient/divergence/curl, the divergence and Stokes theorems. Vector calculus *is* the language of fluid mechanics — the continuity equation is `∂ρ/∂t + ∇·(ρV) = 0` and nothing else.
**Prereq:** school calculus.
**Textbook:** Stewart *Calculus: Early Transcendentals* (9th ed.); Kreyszig *Advanced Engineering Mathematics* (10th ed.) as the working reference for the whole degree.
**Free:** MIT OCW **18.01 / 18.02**; MIT OCW 18.02SC has full video. NPTEL has multiple "Engineering Mathematics" series.
**Practical:** none, but do the problem sets by hand — this is where computational fluency is built.

### M2. Linear algebra
**Covers:** vector spaces, rank, LU/QR, eigenvalues and eigenvectors, SVD, quadratic forms, conditioning. Eigenanalysis underpins vibration modes, flutter, aircraft dynamic modes (phugoid, Dutch roll), and modal reduction in FEM.
**Prereq:** calculus.
**Textbook:** Strang *Introduction to Linear Algebra* (6th ed.).
**Free:** MIT OCW **18.06** (Strang's lectures — the canonical free course in the world).
**Practical:** implement Gram–Schmidt and power iteration in Python/MATLAB.

### M3. ODEs, PDEs and complex variables
**Covers:** first/second-order ODEs, systems, Laplace transforms, Fourier series; then classification of second-order PDEs (elliptic/parabolic/hyperbolic), separation of variables, characteristics. Complex analysis gives conformal mapping — Joukowski transform, the classical route to airfoil theory.
**Prereq:** M1, M2. MIT: **18.03** is a co-requisite of Unified Engineering.
**Textbook:** Boyce & DiPrima; Kreyszig chapters 11–12 for PDEs.
**Free:** MIT OCW 18.03; MIT OCW **16.920[J] Numerical Methods for Partial Differential Equations** (prereq 18.03 or 18.06).
**Practical:** solve the 1-D heat and wave equations numerically; verify against analytic solutions.

### M4. Numerical methods and programming
**Covers:** floating point and error, root finding, interpolation, quadrature, ODE integrators (RK4, stiff solvers), linear system solvers (direct vs iterative: GMRES, multigrid), finite difference/volume/element discretisation, stability (CFL condition), convergence order and grid refinement.
**Prereq:** M2, M3, some programming.
**Textbook:** Chapra & Canale *Numerical Methods for Engineers*; Ferziger & Perić *Computational Methods for Fluid Dynamics* later.
**Free:** MIT OCW **16.90 / 16.910[J] Introduction to Modeling and Simulation**; NPTEL "Computational Science in Engineering" (IIT Kanpur, Prof. Ashoke De).
**Practical:** write your own explicit and implicit 1-D solvers before touching a commercial code. This is what makes you able to judge a Fluent result later.

### M5. Statics and mechanics of materials
**Covers:** equilibrium, free-body diagrams, trusses, frames, centroids and second moments of area, stress and strain tensors, Mohr's circle, axial/torsion/bending, shear flow in thin-walled sections, beam deflection, column buckling (Euler `P_cr = π²EI/(KL)²`), combined loading, failure criteria (von Mises, Tresca).
**Prereq:** M1, physics.
**Textbook:** Hibbeler *Statics* and *Mechanics of Materials*; Gere & Goodno.
**Free:** MIT OCW 1.050 / 2.001; NPTEL "Strength of Materials".
**Practical:** tensile test to failure, strain-gauged cantilever beam, buckling of slender struts.

### M6. Dynamics and vibrations
**Covers:** particle and rigid-body kinematics in rotating frames (Coriolis!), Newton–Euler, work–energy, impulse–momentum, Lagrangian mechanics, gyroscopic motion, moments of inertia tensor. Then SDOF free/forced/damped vibration, resonance, MDOF eigenvalue problem, modal analysis, continuous systems (beam and string modes).
**Prereq:** M5, M3. MIT: **16.07 Dynamics**, prereq (16.001 or 16.002) and (16.003 or 16.004).
**Textbook:** Hibbeler *Dynamics*; Rao *Mechanical Vibrations*; Meirovitch *Fundamentals of Vibrations*.
**Free:** MIT OCW 2.003 / 16.07 materials; MIT OCW **16.221[J] Structural Dynamics** (prereq 18.03).
**Practical:** shaker table modal test, accelerometer instrumentation, FFT of a ping test.

### M7. Thermodynamics
**Covers:** First and Second Laws, property relations, ideal and real gases, control-volume analysis, entropy and isentropic processes, exergy, power and refrigeration cycles (Otto, Diesel, Brayton, Rankine), gas mixtures, combustion stoichiometry and adiabatic flame temperature, chemical equilibrium.
**Prereq:** M1, chemistry. MIT: covered in **16.004 Unified Engineering: Thermodynamics and Propulsion**.
**Textbook:** Çengel & Boles *Thermodynamics: An Engineering Approach* (9th ed.); Moran & Shapiro.
**Free:** MIT OCW 2.005/16.004 notes ("Thermodynamics and Propulsion" web notes by Waitz/Greitzer are outstanding and free); NPTEL Thermodynamics.
**Practical:** calibration of a thermocouple, small engine dynamometer, Rankine cycle bench.

### M8. Fluid mechanics
**Covers:** hydrostatics, control-volume conservation laws, Bernoulli and its actual assumptions, dimensional analysis and Π-theorem (Re, M, Fr, St), Navier–Stokes derivation, viscous laminar solutions (Couette, Poiseuille), pipe flow and Moody chart, boundary-layer introduction, turbomachinery Euler equation.
**Prereq:** M1, M3, M6. MIT: **16.003 Unified Engineering: Fluid Dynamics**.
**Textbook:** White *Fluid Mechanics* (8th ed.); Kundu, Cohen & Dowling *Fluid Mechanics* for depth.
**Free:** MIT OCW 2.25 Advanced Fluid Mechanics (graduate, hard, excellent); NPTEL "Fundamentals of Theoretical and Experimental Aerodynamics" (IIT Kharagpur, Prof. Arnab Roy).
**Practical:** pipe friction rig, venturi/orifice calibration, flow visualisation (smoke, dye, tufts).

---

## Year 3: the aerospace core

### A1. Aerodynamics I — incompressible and inviscid
**Covers:** the velocity potential and stream function, Laplace's equation and superposition (source, sink, doublet, vortex), Kutta–Joukowski `L' = ρ V Γ`, the Kutta condition, **thin airfoil theory** (`c_l = 2π(α − α_{L=0})`, `dc_l/dα = 2π /rad`, `c_{m,c/4}` independent of α for symmetric sections), **Prandtl lifting-line theory** (`C_Di = C_L²/(π AR e)`, elliptical loading optimum), downwash and induced angle of attack, finite-wing corrections, source/vortex panel methods.
**Prereq:** M8, M3 (complex variables help). MIT: **16.100 Aerodynamics**, prereq 16.003 + 16.004.
**Textbook:** **Anderson, *Fundamentals of Aerodynamics*** (7th ed.) — the default worldwide. Katz & Plotkin *Low-Speed Aerodynamics* for panel methods.
**Free:** **MIT OCW 16.100 (Fall 2005, Prof. David Darmofal)** — covers subsonic potential flow with source/vortex panel methods, viscous flow, thin airfoil and lifting line, and supersonic/hypersonic airfoil theory; includes lecture notes, problem sets, exams and projects.
**Practical:** low-speed wind tunnel — pressure-tapped airfoil, `C_p` distribution integration to get `c_l`, wake rake for profile drag; XFOIL comparison.

### A2. Gas dynamics / compressible flow
**Covers:** speed of sound, Mach number, isentropic relations (`T₀/T = 1 + (γ−1)M²/2`, `p₀/p = (1+(γ−1)M²/2)^{γ/(γ−1)}`), normal shocks (Rankine–Hugoniot), oblique shocks and the θ–β–M relation, Prandtl–Meyer expansion, Fanno and Rayleigh flow, converging–diverging nozzles and the choked condition, shock–boundary-layer interaction.
**Prereq:** M7, M8, A1.
**Textbook:** Anderson *Modern Compressible Flow: With Historical Perspective* (4th ed.); Shapiro's two-volume classic for depth.
**Free:** NPTEL **"Gasdynamics: Fundamentals and Applications"** (IISc Bangalore, Prof. Srisha Rao M V); MIT OCW **16.120 Compressible Internal Flow**.
**Practical:** supersonic blowdown tunnel, schlieren of a wedge/cone, shock tube.

### A3. Aerodynamics II — viscous flow, transition, turbulence
**Covers:** boundary-layer equations and Blasius solution (`δ/x = 5.0/√Re_x`, `c_f = 0.664/√Re_x`), momentum-integral (von Kármán) method, Falkner–Skan pressure-gradient family, separation, transition mechanisms (T-S waves, crossflow, bypass) and the **e^N method**, turbulent boundary layers, law of the wall, skin-friction correlations, turbulence modelling hierarchy (algebraic → k-ε → k-ω SST → Spalart–Allmaras → RSM → LES → DNS).
**Prereq:** A1, M8. MIT: **16.13 Aerodynamics of Viscous Fluids**, prereq 16.100/16.110.
**Textbook:** Schlichting & Gersten *Boundary-Layer Theory* (9th ed.); Drela *Flight Vehicle Aerodynamics* (MIT Press, 2014) — the compressed modern treatment.
**Free:** MIT OCW **16.110 Flight Vehicle Aerodynamics** (Drela); MIT OCW **16.18 Fundamentals of Turbulence**.
**Practical:** boundary-layer traverse with a flattened Pitot, hot-wire anemometry, transition detection with china clay or IR thermography.

### A4. Propulsion
**Covers:** the ideal and real Brayton cycle, station numbering, component efficiencies, thrust equation `F = ṁ(V_e − V_∞) + (p_e − p_∞)A_e`, propulsive/thermal/overall efficiency, TSFC; turbojet, turbofan (separate and mixed exhaust), turboprop and turboshaft; inlets (subsonic, supersonic external/mixed compression), axial and centrifugal compressors, stage loading and reaction, stall and surge, combustors, turbines and cooling, nozzles; ramjet and scramjet; rocket fundamentals.
**Prereq:** M7, M8, A2. MIT: **16.50 Aerospace Propulsion**.
**Textbook:** Hill & Peterson *Mechanics and Thermodynamics of Propulsion* (2nd ed.); Mattingly *Elements of Propulsion: Gas Turbines and Rockets* (2nd ed.); Farokhi *Aircraft Propulsion*; Cumpsty *Jet Propulsion* for the readable version and *Compressor Aerodynamics* for the deep one.
**Free:** MIT OCW 16.50; the MIT "Thermodynamics and Propulsion" web notes; NPTEL "Aerodynamic Design of Axial Flow Compressors & Fans" (IIT Kharagpur); NPTEL "Introduction to Rocket Propulsion" (IIT Kanpur, Dr D.P. Mishra) and "Rocket Propulsion" (IIT Madras).
**Practical:** small turbojet test cell (JetCat/SR-30 class), cascade rig, rocket motor static fire with load cell and pressure transducers.

### A5. Aircraft structures
**Covers:** idealisation of thin-walled structures into booms and shear panels, shear flow in open/closed sections, shear centre, torsion of multi-cell boxes, bending of unsymmetrical sections, stiffened-panel buckling and effective width, crippling, fittings and joints, bolted and riveted joint analysis (bearing/shear/net-section), composite laminate theory (CLT, ABD matrix), sandwich panels, introduction to FEM.
**Prereq:** M5, M6. MIT: **16.20 Structural Mechanics**, prereq 16.001.
**Textbook:** **Megson *Aircraft Structures for Engineering Students*** (7th ed.) — the teaching standard. **Niu *Airframe Structural Design*** and **Bruhn *Analysis and Design of Flight Vehicle Structures*** for the industry handbook layer.
**Free:** MIT OCW 16.20; NPTEL "Aircraft Structures".
**Practical:** shear-centre demonstration on a channel section, stringer-stiffened panel compression test to buckling, strain gauging a wing box.

### A6. Flight mechanics and aircraft performance
**Covers:** the standard atmosphere (ISA: 288.15 K, 101,325 Pa, lapse 6.5 K/km to 11 km, then isothermal 216.65 K), airspeed definitions (IAS/CAS/EAS/TAS/Mach), drag polar `C_D = C_{D0} + k C_L²`, thrust and power required/available, minimum drag and minimum power speeds, climb and ceiling, range and endurance (Bréguet, both jet and prop forms), turning flight and the V-n diagram, take-off and landing field length, energy-height and specific excess power `P_s = V(T−D)/W`, payload–range.
**Prereq:** A1, A4.
**Textbook:** Anderson *Introduction to Flight* (9th ed.) for the entry level; Anderson *Aircraft Performance and Design*; Ruijgrok *Elements of Airplane Performance*; Vinh *Flight Mechanics of High-Performance Aircraft*.
**Free:** MIT OCW 16.885 Aircraft Systems Engineering; NPTEL "Introduction to Aerospace Engineering" (IIT Bombay, Prof. Rajkumar Pant).
**Practical:** flight test in a light aircraft or the university's flying laboratory (Cranfield runs its National Flying Laboratory Centre for exactly this); sawtooth climbs, stall speed determination, level-flight drag polar extraction.

### A7. Stability and control (flight dynamics)
**Covers:** body/stability/wind axes, the six nonlinear equations of motion, small-perturbation linearisation, stability derivatives (`C_{mα}`, `C_{mq}`, `C_{nβ}`, `C_{lβ}`, `C_{Yβ}`…), static longitudinal stability, neutral point and static margin, stick-fixed/stick-free, trim and control power; dynamic modes — **short period**, **phugoid**, **roll subsidence**, **spiral**, **Dutch roll** — with their approximate eigenvalue expressions; handling qualities (Cooper–Harper, MIL-F-8785C levels); control-surface hinge moments and aerodynamic balance.
**Prereq:** M6, A1, control theory.
**Textbook:** **Etkin & Reid *Dynamics of Flight: Stability and Control*** (3rd ed.); **Nelson *Flight Stability and Automatic Control*** (2nd ed.); Stengel *Flight Dynamics* (2nd ed., 2022) for the modern control-theoretic treatment.
**Free:** MIT OCW 16.333 Aircraft Stability and Control materials; Princeton's Stengel course notes are publicly posted.
**Practical:** flight simulator identification of the phugoid; wind-tunnel measurement of `C_{mα}` on a complete model; free-flight model tests.

### A8. Control theory
**Covers:** Laplace transforms, transfer functions, block diagrams, time response, root locus, Bode/Nyquist, gain and phase margin, PID design, lead–lag compensation; then state space, controllability/observability, pole placement, LQR, Kalman filtering, LQG, robustness.
**Prereq:** M2, M3. MIT: **16.06 Principles of Automatic Control** (prereq 16.002) → **16.30/16.31 Feedback Control Systems** → **16.32 Principles of Optimal Control and Estimation** (prereq 16.31).
**Textbook:** Franklin, Powell & Emami-Naeini *Feedback Control of Dynamic Systems* (8th ed.); Ogata *Modern Control Engineering*; Stengel *Optimal Control and Estimation* (Dover, cheap).
**Free:** MIT OCW 16.06, 16.30/16.31, 16.32; edX "Control of Mobile Robots" (Georgia Tech).
**Practical:** invert a pendulum on a cart; implement a PID attitude loop on a quadrotor; Simulink autopilot with actuator saturation and sensor noise.

---

## Year 4: specialisation

### B1. Computational fluid dynamics
**Covers:** governing equations in conservative form, finite-volume discretisation, flux schemes (central + artificial dissipation, Roe, AUSM, HLLC), limiters and TVD, time integration (explicit, implicit, dual time-stepping), turbulence closure choice, boundary conditions, mesh generation (structured, unstructured, hybrid, `y⁺` requirements: `y⁺ ≈ 1` for wall-resolved, 30–300 for wall functions), convergence and grid-convergence index, verification vs validation.
**Prereq:** A3, M4. MIT: **16.920[J]**, then **16.930 Advanced Topics in Numerical Methods**.
**Textbook:** Ferziger, Perić & Street; Blazek *Computational Fluid Dynamics: Principles and Applications*; Anderson *Computational Fluid Dynamics: The Basics with Applications*.
**Free:** SU2 tutorials (su2code.github.io, LGPL 2.1, governed by the SU2 Foundation — discrete adjoints, shape optimisation, NICFD); OpenFOAM user guide; NASA Turbulence Modeling Resource (turbmodels.larc.nasa.gov) with verification cases.
**Practical:** reproduce the NASA 2-D NACA 0012 or the ONERA M6 wing case and compare to the published experimental data — including the parts that do not match.

### B2. Structural dynamics and aeroelasticity
**Covers:** modal analysis of continuous structures, forced response, damping models; then the aeroelastic triangle (aerodynamic/elastic/inertial), **divergence** (`q_D = K_θ/(∂L/∂α · e)`), **control reversal**, **flutter** (binary bending–torsion, the V-g and p-k methods, unsteady aerodynamics via Theodorsen's function and doublet-lattice), gust response and continuous turbulence (von Kármán/Dryden PSD), buffet, limit-cycle oscillation, and the certification requirement for a flutter margin of at least **1.15 V_D** (CS-25.629 / 25.629).
**Prereq:** A5, A1, M6.
**Textbook:** Hodges & Pierce *Introduction to Structural Dynamics and Aeroelasticity* (2nd ed.); Bisplinghoff, Ashley & Halfman *Aeroelasticity* (Dover); Wright & Cooper *Introduction to Aircraft Aeroelasticity and Loads*.
**Free:** MIT OCW **16.221[J] Structural Dynamics**; NASA technical reports on flutter flight testing.
**Practical:** flutter of a flexible wing model in a low-speed tunnel (safely — this is the one lab that reliably destroys equipment); ground vibration test (GVT) of a model.

### B3. Aerospace materials
**Covers:** structure–property relationships, alloy designation systems, heat treatment and temper designations, fracture mechanics (`K_I = Yσ√(πa)`, `K_IC`, Paris law `da/dN = C(ΔK)^m`), fatigue (S–N, Miner's rule, Goodman diagram), creep and Larson–Miller, corrosion mechanisms (galvanic, pitting, exfoliation, SCC), composites (fibre and matrix types, laminate design, failure criteria: max stress, Tsai–Wu), and processing (see `04_structures-and-materials.md`).
**Prereq:** M5, chemistry. MIT: **16.223[J] Mechanics of Heterogeneous Materials**; **16.235 Design with High Temperature Materials**; **16.202 Manufacturing with Advanced Composite Materials** (1-3-2, hands-on).
**Textbook:** Ashby *Materials Selection in Mechanical Design*; Campbell *Manufacturing Technology for Aerospace Structural Materials*; Jones *Mechanics of Composite Materials*.
**Free:** MIT OCW 3.032; NASA/CMH-17 (Composite Materials Handbook) summaries.
**Practical:** hand layup and vacuum-bag cure of a CFRP coupon; tensile/ILSS testing; fractography of a fatigue surface.

### B4. Avionics, systems and aircraft systems engineering
**Covers:** requirements engineering, functional decomposition, interface control, systems architecture (federated vs integrated modular avionics), data buses (ARINC 429, 629, 664/AFDX, MIL-STD-1553), redundancy and dissimilarity, safety assessment (FHA/PSSA/SSA, FTA, FMEA, CCA), reliability (MTBF, exponential model), the aircraft's power and utility systems.
**Prereq:** A8, some digital electronics. MIT: **16.842 Fundamentals of Systems Engineering**; **16.885 Aircraft Systems Engineering**; **16.35 Real-Time Systems and Software**; **16.36 Communication Systems and Networks**.
**Textbook:** Moir & Seabridge *Aircraft Systems* (3rd ed.) and *Design and Development of Aircraft Systems*; Collinson *Introduction to Avionics Systems* (3rd ed.); Spitzer *Digital Avionics Handbook*.
**Free:** MIT OCW 16.885 (built around the Space Shuttle as a case study), 16.842.
**Practical:** build a working ARINC-429 sniffer; instrument a model aircraft with a Pixhawk and analyse the logs.

### B5. Orbital mechanics and astrodynamics
**Covers:** the two-body problem and its integrals, conic sections, orbital elements, Kepler's equation and time-of-flight, orbit determination (Gibbs, Lambert), coordinate/time systems (ECI, ECEF, J2000, UTC/TAI/GPS), orbital manoeuvres (Hohmann `Δv`, bi-elliptic, plane change `Δv = 2V sin(Δi/2)`), perturbations (J2 nodal regression `Ω̇ = −(3/2) J₂ (R_E/p)² n cos i`, drag, third-body, SRP), sun-synchronous and Molniya orbits, relative motion (Clohessy–Wiltshire) and rendezvous, interplanetary transfer and patched conics, gravity assist.
**Prereq:** M6, M3. MIT: **16.346 Astrodynamics** (prereq 18.03).
**Textbook:** **Curtis *Orbital Mechanics for Engineering Students*** (4th ed.) — the teaching standard with MATLAB code; **Vallado *Fundamentals of Astrodynamics and Applications*** (5th ed.) — the professional reference; Bate, Mueller & White (Dover, cheap, still excellent).
**Free:** MIT OCW 16.346; NPTEL "Introduction to Launch Vehicle Analysis and Design" (IIT Bombay, Prof. Ashok Joshi).
**Practical:** propagate a TLE with SGP4 and compare to observation; write a Lambert solver; plan a Mars transfer with a porkchop plot.

### B6. Spacecraft systems and space propulsion
**Covers:** mission analysis, spacecraft bus subsystems (structure, thermal, power, ADCS, TT&C, C&DH, propulsion), link budgets, thermal balance `Q_in = Q_out` with radiators and MLI, solar array and battery sizing with eclipse fraction, attitude determination and control (reaction wheels, magnetorquers, CMGs, star trackers), launch environment and vibration qualification, space environment (radiation dose, single-event effects, atomic oxygen, debris).
**Prereq:** B5, A4. MIT: **16.851 Introduction to Satellite Engineering**, **16.89[J] Space Systems Engineering**, **16.522 Space Propulsion** (3-3-6, laboratory project), **16.512 Rocket Propulsion**.
**Textbook:** **Wertz & Larson *Space Mission Analysis and Design* (SMAD)**; **Fortescue, Stark & Swinerd *Spacecraft Systems Engineering*** (4th ed.); **Sutton & Biblarz *Rocket Propulsion Elements*** (9th ed.).
**Free:** MIT OCW 16.851/16.89; ESA and NASA state-of-the-art small spacecraft technology reports (free PDFs, updated roughly annually).
**Practical:** CubeSat subsystem build; thermal vacuum test; electric-propulsion thruster characterisation.

### B7. Aircraft design (the capstone)
**Covers:** the whole sizing loop from a requirements set, executed as a team over one or two semesters, ending in a design review defended in front of industry engineers. See `05_aircraft-design-process.md` for the method in detail.
**Prereq:** essentially everything above.
**Textbook:** **Raymer *Aircraft Design: A Conceptual Approach*** (7th ed., AIAA Education Series) — the standard capstone book; Roskam's eight-part series for the numbers; Torenbeek *Synthesis of Subsonic Airplane Design* and *Advanced Aircraft Design*; Gudmundsson *General Aviation Aircraft Design* for the light-aircraft numbers with worked spreadsheets; Nicolai & Carichner *Fundamentals of Aircraft and Airship Design*.
**Free:** MIT OCW 16.885; NPTEL **"Introduction to Aircraft Design"** (IIT Bombay, Prof. Rajkumar Pant); OpenVSP Ground School (openvsp.org).
**Practical:** the design itself, plus a wind-tunnel or flight validation of at least one prediction.

---

## The leading programmes

| University | Structure and character |
|---|---|
| **MIT** (Course 16, Aeronautics and Astronautics) | 16.001–16.004 Unified Engineering is the defining first-year experience: four coupled 5-1-6 subjects taught as one integrated whole. Deep OCW coverage. Strong in aerodynamics (Drela, Darmofal), propulsion (Gas Turbine Lab), systems engineering, autonomy, and space systems. Graduate offerings include 16.888[J] MDO, 16.920[J] numerical PDEs, 16.89[J] space systems engineering. |
| **Caltech** (GALCIT) | Small, theory-heavy, elite. Historically the home of von Kármán; the Graduate Aerospace Laboratories run the Ludwieg tube, shock tubes and hypersonic facilities. Very strong fluid mechanics and solid mechanics; small cohorts. |
| **Stanford** (Aeronautics & Astronautics) | Computational and design-optimisation heavy; the birthplace of SU2 and the Aerospace Design Lab under Alonso. Strong in adjoint methods, autonomy, and space rendezvous (SLAB). |
| **University of Michigan** (Aerospace Engineering) | The MDO powerhouse (MDO Lab, Joaquim Martins — OpenMDAO/OpenAeroStruct ecosystem), plus strong aeroelasticity and hypersonics. |
| **Georgia Tech** (Daniel Guggenheim School) | The largest AE school in the US; systems design and analysis (ASDL) is world-leading in design methodology, technology forecasting and probabilistic design. |
| **Purdue** (School of Aeronautics and Astronautics) | "Cradle of Astronauts"; exceptional propulsion facilities (Zucrow Labs — the largest academic propulsion lab in the US), strong hypersonics (Boeing/AFOSR Mach-6 Quiet Tunnel). |
| **TU Delft** (Faculty of Aerospace Engineering) | The largest aerospace faculty in Europe. BSc Aerospace Engineering (English-taught) and MSc Aerospace Engineering with tracks; famous for the **Design Synthesis Exercise** group capstone. Research in sustainable/hydrogen aviation, aeroacoustics, composites, wind energy, autonomous systems. |
| **ISAE-SUPAERO** (Toulouse) | The French *grande école* model: entry via *Concours* after two years of *classes préparatoires*, three-year *diplôme d'ingénieur*, deeply integrated with Airbus, ONERA and CNES. Also runs English-taught MSc and Advanced Masters. |
| **Cranfield University** (UK) | Postgraduate-only. MSc **Aerospace Dynamics** (1 yr FT / up to 3 yr PT; 50 % taught, 50 % individual project; compulsory Flight Experimental Methods and Introduction to Aircraft Aerodynamics, then eight electives, plus a **group flight test project** flown on the National Flying Laboratory Centre aircraft). Also **Aircraft Engineering MSc** and **Astronautics and Space Engineering MSc**. Entry: UK 2:1 or equivalent, IELTS 6.5. The closest thing to an industrial finishing school. |
| **Imperial College London** | MEng Aeronautics (4 yr) with a strong fluid mechanics and structures core and a substantial group design project; heavy mathematics. |
| **TUM** (Technical University of Munich) | BSc/MSc Aerospace at the Department of Aerospace and Geodesy in Ottobrunn/Taufkirchen; German-language BSc, English MSc; close to Airbus Defence & Space, MTU and the Munich space cluster. |
| **KTH Royal Institute of Technology** (Stockholm) | MSc Aerospace Engineering with tracks in aeronautics, space, and lightweight structures; strong in turbulence (Linné FLOW Centre) and systems. |

Others worth naming: Politecnico di Milano and Torino, ETH Zürich (mechanical with aerospace focus), ISAE-ENSMA, Universidad Politécnica de Madrid, University of Bristol and Southampton (UK), Beihang and NUAA (China), IIT Bombay/Madras/Kanpur (India), UNSW and RMIT (Australia).

## Southern African options

> ⚠️ Aerospace is a small field in southern Africa. There is one accredited undergraduate aeronautical degree in South Africa (Wits), and the rest of the pathway runs through mechanical/mechatronic engineering plus aerospace-flavoured postgraduate work or research groups.

**[ZA] University of the Witwatersrand (Wits)** — School of Mechanical, Industrial and Aeronautical Engineering. Offers **BSc(Eng) Aeronautical Engineering**, four years full-time, described as "the design, development and modification of the components and systems of all types of flight vehicles, including fixed wing aircraft, helicopters, sailplanes, missiles and non-flying aerodynamic devices." Also offers an **18-month MSc in Aeronautical Engineering delivered in partnership with Embry-Riddle Aeronautical University**, described by the school as Africa's only accredited MSc of that kind. This is the default route for a South African who wants an aeronautical title on the certificate.

**[ZA] University of Pretoria (UP)** — the department is named **Mechanical and Aeronautical Engineering** and hosts an explicit **Aeronautical Group** among its research centres (alongside the Centre for Asset Integrity Management, Vehicle Dynamics Group, Clean Energy Research Group, RAMMS, the Ultrasonics Research Laboratory and STEPS). Facilities listed include **wind tunnels, engine test facilities, a structural mechanics laboratory, a vibration and controls laboratory and a heat transfer laboratory**. Postgraduate MEng/PhD in aeronautical topics is well supported.

**[ZA] Stellenbosch University (SU)** — the Department of Mechanical and Mechatronic Engineering offers **BEng Mechanical** and **BEng Mechatronic**, with research grouped into Biomedical, Computational Engineering, Energy & Environment, Mechatronics/Automation/Design, and Solid Mechanics. There is no dedicated aeronautical undergraduate degree. Stellenbosch's substantial UAV and flight-control work sits mainly in the **Electronic Systems Laboratory** in the Electrical & Electronic Engineering department (`needs-verification` on the current ESL programme list). Mechatronic + ESL postgraduate is the strongest southern African route into autonomy and flight control.

**[ZA] University of Cape Town (UCT)** — BSc(Eng) Mechanical Engineering with aeronautical-relevant electives and postgraduate research; the historical strength is in mechanics, materials and vehicle dynamics rather than a named aero degree (`needs-verification` on current aeronautical electives).

**[ZA] Cape Peninsula University of Technology (CPUT)** — the university of technology route: Diploma / Advanced Diploma / BEngTech in mechanical engineering with aeronautical streams, plus a long-standing association with aviation maintenance training and the CPUT satellite programme (**F'SATI**, which built ZACube-1 and ZACube-2). CPUT's site blocked automated access, so specific qualification names and durations are `needs-verification`.

**[NA] Namibia** — there is no aerospace engineering degree in Namibia. The realistic paths are (a) NUST/UNAM mechanical or electrical engineering followed by a South African or overseas aerospace master's, (b) a licensed aircraft maintenance engineering route through an approved Part-147 organisation, or (c) an overseas undergraduate degree. Namibia's SANSA-adjacent and Earth-observation work is the nearest domestic space-sector employment.

**Regional industry to target:** Denel Aeronautics and Denel Dynamics (distressed but technically significant), Aerosud, Paramount Group, Milkor (UAVs), Cybicom Atlas Defence, SAA Technical, Safair/FlySafair engineering, the SANSA space operations facility at Hartebeesthoek, and the growing UAV survey sector.

## The realistic self-study sequence

For a working professional (e.g. a line pilot) building this knowledge without enrolling:

1. **Strang 18.06** (linear algebra) + refresh vector calculus — 3 months.
2. **Anderson *Introduction to Flight*** cover to cover — gives the map, 1 month.
3. **White *Fluid Mechanics*** ch. 1–7 — 3 months, with the dimensional-analysis chapter done properly.
4. **Anderson *Fundamentals of Aerodynamics*** parts I–II, alongside **MIT OCW 16.100** — 4 months. Do the panel-method project.
5. **Anderson *Modern Compressible Flow*** ch. 1–9 — 3 months. This is where a pilot's Mach intuition becomes quantitative.
6. **Hill & Peterson** or **Cumpsty *Jet Propulsion*** — 3 months. Cumpsty is the one to read first if the goal is understanding the engine on the wing.
7. **Etkin & Reid** or **Nelson** — 3 months, in parallel with a simulator or flight-test data.
8. **Megson** ch. 1–12 — 3 months for structures literacy.
9. **Raymer** — do a full sizing exercise on an aircraft you know well; compare your answer with the real one.

That is roughly two years part-time and produces genuine, defensible competence rather than vocabulary.

## Sources

- [MIT Course 16 undergraduate subject listing](http://student.mit.edu/catalog/m16a.html) — MIT
- [MIT Course 16 graduate subject listing](http://student.mit.edu/catalog/m16b.html) — MIT
- [MIT OCW 16.100 Aerodynamics (Fall 2005)](https://ocw.mit.edu/courses/16-100-aerodynamics-fall-2005/) — MIT OpenCourseWare
- [NPTEL course archive](https://archive.nptel.ac.in/course.html) — NPTEL
- [Wits School of Mechanical, Industrial and Aeronautical Engineering — undergraduate studies](https://www.wits.ac.za/mia/undergraduate-studies/) and [school home](https://www.wits.ac.za/mia/) — University of the Witwatersrand
- [UP Department of Mechanical and Aeronautical Engineering](https://www.up.ac.za/mechanical-and-aeronautical-engineering) — University of Pretoria
- [SU Department of Mechanical and Mechatronic Engineering](https://www.su.ac.za/en/faculties/engineering/departments/mechanical-mechatronic-engineering) — Stellenbosch University
- [Cranfield Aerospace Dynamics MSc](https://www.cranfield.ac.uk/courses/taught/aerospace-dynamics) — Cranfield University
- [TU Delft Faculty of Aerospace Engineering](https://www.tudelft.nl/en/ae) — TU Delft
- [SU2 open-source CFD](https://su2code.github.io/) — SU2 Foundation
- [OpenVSP](https://openvsp.org/) — NASA/OpenVSP community

## Open questions

- CPUT's exact aeronautical qualification names, NQF levels and durations — site blocked automated retrieval; `needs-verification`.
- UCT's current aeronautical elective set within BSc(Eng) Mechanical — `needs-verification`.
- Stellenbosch Electronic Systems Laboratory current UAV/flight-control postgraduate offerings — `needs-verification`.
- MIT's current undergraduate capstone subject numbers (historically 16.82 Flight Vehicle Engineering / 16.83 Space Systems Engineering, later restructured) did not appear in the fetched catalogue page — `needs-verification`.
- TU Delft BSc year-by-year module list and ECTS weights could not be fetched (404 on the study-programme page); the Design Synthesis Exercise capstone is well attested but the module list is `needs-verification`.
