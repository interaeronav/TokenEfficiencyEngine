---
id: space.tools
title: Tools and simulation software for space engineering
domain: 30_space_science_and_propulsion
tags: [gmat, stk, orekit, poliastro, hapsira, basilisk, spice, cea, rpa, openrocket, ksp, simulation, software]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
unit_system: SI
related: [space.overview, space.orbital-mechanics, space.chemical-propulsion, space.spacecraft-engineering, space.books]
sources:
  - {title: "GMAT release history", url: "https://sourceforge.net/projects/gmat/files/GMAT/", publisher: "NASA / SourceForge", accessed: "2026-08-25"}
  - {title: "GMAT (NASA software catalog)", url: "https://software.nasa.gov/software/GSC-17177-1", publisher: "NASA", accessed: "2026-08-25"}
  - {title: "Orekit", url: "https://github.com/CS-SI/Orekit", publisher: "CS GROUP / GitHub", accessed: "2026-08-25"}
  - {title: "Basilisk", url: "https://github.com/AVSLab/basilisk", publisher: "AVS Lab, University of Colorado / GitHub", accessed: "2026-08-25"}
  - {title: "hapsira", url: "https://github.com/pleiszenburg/hapsira", publisher: "pleiszenburg / GitHub", accessed: "2026-08-25"}
  - {title: "poliastro (archived)", url: "https://github.com/poliastro/poliastro", publisher: "GitHub", accessed: "2026-08-25"}
  - {title: "SPICE Toolkit", url: "https://naif.jpl.nasa.gov/naif/toolkit.html", publisher: "NASA NAIF / JPL", accessed: "2026-08-25"}
  - {title: "NASA RP-1311 Part I (CEA)", url: "https://ntrs.nasa.gov/citations/19950013764", publisher: "NASA NTRS", accessed: "2026-08-25"}
  - {title: "OpenRocket", url: "https://openrocket.info/", publisher: "OpenRocket", accessed: "2026-08-25"}
---

# Tools and simulation software for space engineering

**Summary.** The software stack for space engineering divides into mission analysis (GMAT, STK, Orekit, hapsira), spacecraft dynamics simulation (Basilisk, Trick, Simulink), ephemerides and geometry (SPICE), propellant performance (CEA, RPA), structures and thermal (Nastran/Abaqus, Thermal Desktop/ESATAN), and hobby-scale rocketry (OpenRocket, RASAero). Most of the mission analysis tier is free and open source; the structures and thermal tier is not. This file says what each tool is for, its licence and current version, and works three real examples end to end: a Hohmann transfer computed in Python, a CEA propellant performance case, and a link budget sized from first principles.

## Key facts

| Tool | Licence | Current version | Domain |
|---|---|---|---|
| **GMAT** | Apache 2.0, NASA open source | **R2026a, 3 April 2026** | Mission design, optimisation, navigation |
| **STK (Ansys)** | Commercial (free tier available) | Rolling | Mission analysis, visualisation, RF |
| **Orekit** | Apache 2.0 | **13.1.6, 3 June 2026** | Java flight-dynamics library |
| **hapsira** (poliastro fork) | MIT | Active; poliastro archived 14 Oct 2023 | Python astrodynamics |
| **Basilisk** | ISC | **2.10.2, 8 May 2026** | Spacecraft dynamics + FSW simulation |
| **SPICE Toolkit** | NASA/JPL, free | **N0067, 3 January 2022** | Ephemerides, geometry, time |
| **NASA Trick** | NASA open source | Active | Real-time simulation framework |
| **CEA** | US Government, free | Gordon & McBride; theory in NASA RP-1311 (Oct 1994) | Chemical equilibrium, rocket performance |
| **RPA** | Commercial (Lite free) | Rolling | Rocket engine analysis and design |
| **OpenRocket** | CC BY-SA 4.0 | **24.12** | Model and high-power rocketry |

## 1. Mission analysis and astrodynamics

### GMAT — the free professional tool

**General Mission Analysis Tool**, NASA Goddard, developed with industry and public contributors. Described by NASA as "the world's only enterprise, multi-mission, open source software system for space mission design, optimization, and navigation." **Current release R2026a (3 April 2026)**; previous releases R2025a (1 May 2025) and R2022a. Runs on Windows, Linux and macOS with both a GUI and a scripting interface, plus a MATLAB interface and a Python API.

What it does: high-fidelity numerical propagation with full force models (spherical harmonic gravity to arbitrary degree and order, atmospheric drag with several density models, third bodies from SPICE/DE ephemerides, SRP with shadow modelling), impulsive and finite manoeuvres, targeting and optimisation (differential correction, and the VF13ad and SNOPT optimisers), orbit determination with batch least squares, and interplanetary trajectory design including Lambert targeting and B-plane targeting.

GMAT is the right answer for anyone who needs real mission analysis without an STK licence. It is used operationally — NASA has flown missions on GMAT-derived manoeuvre plans, and its orbit determination reached operational certification.

**A GMAT script for a LEO-to-GEO Hohmann transfer** (structure, not a literal runnable file — the real syntax needs the resource definitions above it):

```
Create Spacecraft sat;
sat.SMA = 6778.137;  sat.ECC = 0.0;  sat.INC = 28.5;
sat.RAAN = 0;  sat.AOP = 0;  sat.TA = 0;

Create ImpulsiveBurn TOI;   TOI.Element1 = 2.3975;   % km/s, perigee burn
Create ImpulsiveBurn GOI;   GOI.Element1 = 1.8242;   % combined circularise + plane change

Create Propagator prop;     % default force model

BeginMissionSequence;
Maneuver TOI(sat);
Propagate prop(sat) {sat.Apoapsis};
Maneuver GOI(sat);
Propagate prop(sat) {sat.ElapsedDays = 1};
```

In practice you would wrap the burn magnitudes in a `Target` block with a `Vary`/`Achieve` pair so GMAT solves for them against the desired final SMA, ECC and INC rather than hard-coding the analytic values.

### STK — the industry standard

Ansys **Systems Tool Kit**. Commercial, dominant in industry and defence, with a genuinely useful free tier that covers basic orbit propagation, access/visibility analysis and 3D visualisation. Paid modules add astrogator (manoeuvre planning and targeting, the direct GMAT competitor), coverage, communications and radar, and the Analysis Workbench. Its strengths are the visualisation, the breadth of sensor and RF modelling, and the fact that everyone else uses it — interoperability matters. Its weakness is cost and the difficulty of version-controlling or reviewing an analysis built by clicking.

### Orekit — the library to build on

**Java, Apache License 2.0, maintained by CS GROUP**, current release **13.1.6 (3 June 2026)**. Described as "a low level space dynamics library." Capabilities: analytical, semi-analytical, numerical and TLE-based propagators; flexible orbit and attitude representations with customisable attitude laws; event detection (eclipse entry/exit, station visibility, apsides, node crossings); impulsive and continuous manoeuvres; rigorous time scales (TAI, UTC, UT1, TT, GPS, with leap seconds handled correctly); orbit determination with parameter estimation; Earth models and environment data; and readers for the standard space data formats (CCSDS OEM/OPM/OMM, SP3, RINEX, TLE).

Two official Python wrappers exist: a **JCC-based** wrapper and a **JPype-based** wrapper (`orekit_jpype`), both on GitLab. Orekit is what you use when you are building a flight dynamics system rather than doing a one-off study — it is production-grade, well-tested, and its permissive licence makes it usable commercially.

### Python: astropy, hapsira, poliastro, pykep

**astropy** is the foundation: units and quantities, time scales, coordinate frames (ICRS, GCRS, ITRS, and the transformations between them), and constants. Anything numeric in astronomy or astrodynamics in Python should sit on astropy units, because unit errors are the most common class of bug in this domain.

**poliastro is archived.** The repository was archived by its owner on **14 October 2023** with the note: *"poliastro is archived and will not be developed any further... Forks welcome."* Last release 0.17.0. **Use `hapsira` instead** — an MIT-licensed fork of poliastro's main branch as of 14 October 2023, maintained by pleiszenburg, supporting Python 3.8–3.11 (with 3.12 pending a numba release). Same API, actively maintained.

**pykep** (ESA Advanced Concepts Team) is the low-thrust and trajectory-optimisation library, paired with **pygmo** for the global optimisation. This is what you use for porkchop plots, multi-gravity-assist sequences and low-thrust transcription.

**spiceypy** wraps CSPICE for Python and is the standard way to use SPICE from Python.

### SPICE — ephemerides and geometry

NASA's **Navigation and Ancillary Information Facility** toolkit, from JPL. Free. **Current version N0067, released 3 January 2022**, with earlier versions N0058–N0066 still available. Language bindings: **SPICELIB (Fortran), CSPICE (C), Icy (IDL), Mice (MATLAB)**, a JNI binding at alpha status, and third-party wrappers for Python (spiceypy), Ruby and others.

SPICE answers geometry questions correctly: where was Cassini relative to Enceladus at this instant, in this frame; was the Sun occulted; what was the phase angle; what was the sub-spacecraft point. The data are in **kernels**, each type carrying one thing — **SPK** (ephemerides of bodies and spacecraft), **PCK** (planetary constants and orientation), **CK** (spacecraft and instrument pointing), **IK** (instrument geometry), **FK** (reference frame definitions), **LSK** (leap seconds), **SCLK** (spacecraft clock correlation), **EK** (events), **DSK** (digital shape models). Every NASA planetary mission publishes its kernels; using them is how you reproduce a mission's geometry exactly.

## 2. Spacecraft dynamics and flight software simulation

**Basilisk** — **ISC licence**, maintained by the **AVS Lab at the University of Colorado Boulder**, current release **2.10.2 (8 May 2026)**. Written in C and C++ with a Python interface via SWIG (roughly 41% C, 17% Python, 13% C++). It couples a high-fidelity spacecraft dynamics engine (multi-body, flexible modes, fuel slosh, reaction wheels, CMGs, thrusters) with flight-software algorithm modules, so you can simulate the actual GNC algorithms in the loop at faster than real time. Optional modules cover optical navigation and MuJoCo integration. Installable from PyPI as prebuilt wheels. It is the practical companion to Schaub & Junkins's *Analytical Mechanics of Space Systems*, and the CU Boulder Coursera specialisation uses it.

**NASA Trick** — an open-source simulation development environment from Johnson Space Center, used for real-time and human-in-the-loop simulation (Orion, Gateway, ISS training simulators). It generates the simulation executive, data recording, checkpointing and variable-server infrastructure around your C/C++ models. Pair it with **NASA cFS (core Flight System)**, the flight software framework used on dozens of missions, if you want an end-to-end flight-software-in-the-loop environment.

**MATLAB/Simulink** with the Aerospace Blockset remains the industry default for control law design and autocoding, and most flight GNC still originates there.

**42** (NASA Goddard, open source) is a lighter-weight attitude and orbit dynamics simulator with good visualisation, useful for quick ADCS studies.

## 3. Propellant performance: CEA and RPA

**CEA** — *Chemical Equilibrium with Applications*, Gordon and McBride at NASA Lewis (now Glenn). The theory is documented in **NASA RP-1311 Part I (Analysis), published 1 October 1994**, freely downloadable from NTRS, with Part II covering the program manual. Free to US and, in practice, general use. CEA computes chemical equilibrium compositions and thermodynamic properties for a mixture, and derives rocket performance from them. Problem types include `rocket` (equilibrium or frozen), `tp` (fixed temperature and pressure), `hp` (fixed enthalpy and pressure — adiabatic flame temperature), `sp` (fixed entropy and pressure), `uv`, `detonation`, and `shock`.

Wrappers make it usable from modern code: **rocketcea** (Python), **CEA2py**, and **pycea**. RPA (below) reimplements the same thermochemistry with a better interface.

### Worked CEA case: LOX/RP-1 at 100 bar

A minimal CEA input deck for a sea-level-optimised booster engine:

```
problem  o/f=2.56,
    rocket  equilibrium
    p,bar=100,
    pi/p=100,          ! chamber-to-exit pressure ratio (p_e = 1 bar)
    sup-ae/at=16        ! or specify supersonic area ratio directly
reactants
    fuel=RP-1  wt%=100.  t,k=298.15
    oxid=O2(L) wt%=100.  t,k=90.17
output  siunits  transport
end
```

Typical output for this case (values consistent with the hand calculation in `02_chemical-propulsion.md`, which used T_c = 3,670 K, M = 23.3 kg/kmol, γ = 1.24):

| Quantity | Chamber | Throat | Exit |
|---|---|---|---|
| p (bar) | 100 | ≈57 | 1.0 |
| T (K) | ≈3,670 | ≈3,440 | ≈1,750 |
| M (kg/kmol) | ≈23.3 | ≈23.3 | ≈23.6 |
| γ | ≈1.14 (equilibrium) / 1.24 (frozen, effective) | | |
| c* | ≈1,790 m/s | | |
| C_F (SL, optimum) | | | ≈1.60 |
| **Isp (sea level, optimum expansion)** | | | **≈292 s** |

Apply a c*·C_F efficiency of 0.96 and you land at ≈280 s — the observed Merlin 1D sea-level figure. **This is the workflow**: CEA gives the theoretical ceiling, the efficiency factors are empirical, and the difference between them is where engine design lives.

Things to get right when running CEA: use the **equilibrium** option for large engines and **frozen** as a pessimistic bound; sweep O/F to find the peak (which for LOX/RP-1 sits near 2.6–2.8 for Isp but is often run fuel-rich around 2.3–2.4 for cooler walls and better cooling); and remember that CEA's exit conditions assume one-dimensional isentropic flow with no boundary layer, no divergence loss and no film cooling.

**RPA — Rocket Propulsion Analysis** (Alexander Ponomarenko). Commercial with a free **Lite** version. It does the CEA thermochemistry with a modern GUI, then goes further: nozzle contour generation (conical, Rao/thrust-optimised parabolic, and truncated ideal contours), regenerative cooling channel analysis with wall temperature prediction, injector sizing, engine mass estimation, and cycle analysis for gas generator, staged combustion and expander cycles. For anyone actually designing an engine rather than just evaluating a propellant, RPA saves weeks.

## 4. A worked Hohmann transfer in Python

Using `hapsira` (the maintained poliastro fork) with astropy units:

```python
from astropy import units as u
from hapsira.bodies import Earth
from hapsira.twobody import Orbit
from hapsira.maneuver import Maneuver

# 400 km circular LEO
leo = Orbit.circular(Earth, alt=400 * u.km)

# Hohmann to GEO radius (42164.14 km from Earth centre)
hoh = Maneuver.hohmann(leo, 42164.14 * u.km)

print(hoh.get_total_cost().to(u.km / u.s))   # -> ~3.854 km / s
print(hoh.get_total_time().to(u.h))          # -> ~5.29 h

transfer, geo = leo.apply_maneuver(hoh, intermediate=True)
print(geo.a.to(u.km), geo.ecc, geo.period.to(u.h))
```

Expected output, matching the hand calculation in `01_orbital-mechanics.md`:

```
3.85403... km / s
5.29113... h
42164.14 km   ~0.0   23.934 h
```

Doing the same thing with raw numbers and no library, which is worth doing once to prove you understand it:

```python
import numpy as np
mu = 398600.4418          # km^3/s^2
r1, r2 = 6778.137, 42164.14
at = 0.5 * (r1 + r2)

v1  = np.sqrt(mu / r1)
vp  = np.sqrt(mu * (2/r1 - 1/at))
va  = np.sqrt(mu * (2/r2 - 1/at))
v2  = np.sqrt(mu / r2)

dv1, dv2 = vp - v1, v2 - va
tof = np.pi * np.sqrt(at**3 / mu)

print(f"dv1={dv1:.4f}  dv2={dv2:.4f}  total={dv1+dv2:.4f} km/s  tof={tof/3600:.3f} h")
# dv1=2.3975  dv2=1.4565  total=3.8540 km/s  tof=5.291 h
```

And with the 28.5° plane change folded into the second burn (the real GTO case):

```python
di = np.radians(28.5)
dv2_combined = np.sqrt(va**2 + v2**2 - 2*va*v2*np.cos(di))
print(f"combined dv2 = {dv2_combined:.4f} km/s, total = {dv1+dv2_combined:.4f} km/s")
# combined dv2 = 1.8241 km/s, total = 4.2216 km/s
```

## 5. A worked link budget in code

The same S-band CubeSat downlink developed in `05_spacecraft-engineering.md`, as a script you can vary:

```python
import numpy as np

c    = 2.99792458e8
k_dB = -228.6            # 10*log10(Boltzmann), dBW/K/Hz

def slant_range_km(h_km, elev_deg, Re=6378.137):
    e = np.radians(elev_deg)
    return np.sqrt((Re*np.sin(e))**2 + 2*Re*h_km + h_km**2) - Re*np.sin(e)

def dish_gain_dBi(D_m, f_Hz, eff=0.6):
    lam = c / f_Hz
    return 10*np.log10(eff * (np.pi*D_m/lam)**2)

f      = 2.25e9
d_km   = slant_range_km(500, 10)                       # 1695.1 km
lam    = c / f
fspl   = 20*np.log10(4*np.pi*d_km*1e3/lam)             # 164.08 dB

eirp   = 10*np.log10(2.0) + 6.0 - 1.0                  # 2 W, 6 dBi patch, 1 dB loss
g_rx   = dish_gain_dBi(3.0, f)                         # 34.77 dBi
g_over_t = g_rx - 10*np.log10(150.0)                   # Ts = 150 K -> 13.01 dB/K

cn0    = eirp - fspl - 2.0 + g_over_t - k_dB           # 83.55 dB-Hz

for rate, req in [(1e6, 9.6), (10e6, 9.6), (10e6, 4.5)]:
    ebn0 = cn0 - 10*np.log10(rate)
    print(f"{rate/1e6:5.1f} Mbps  Eb/N0={ebn0:6.2f} dB  required={req:4.1f}  margin={ebn0-req:6.2f} dB")
```

Output:

```
  1.0 Mbps  Eb/N0= 23.55 dB  required= 9.6  margin= 13.95 dB
 10.0 Mbps  Eb/N0= 13.55 dB  required= 9.6  margin=  3.95 dB
 10.0 Mbps  Eb/N0= 13.55 dB  required= 4.5  margin=  9.05 dB
```

The third line is the same link with rate-1/2 convolutional coding — a good illustration of why nobody flies uncoded links.

## 6. Structures and thermal

**FEA:** MSC **Nastran** is the aerospace default for structural analysis, particularly for the normal modes, random vibration and shock response spectrum analyses that launch qualification requires. **Abaqus** (Dassault) is preferred for nonlinear and contact problems; **Ansys Mechanical** covers both and is common in newer companies. **FEMAP** and **Patran** are the usual pre/post-processors. Free options — **CalculiX** and **Code_Aster** — are genuinely capable for linear statics and modal analysis and are used in smallsat work.

**Thermal:** **Thermal Desktop** (C&R Technologies) built on AutoCAD, with **SINDA/FLUINT** as the solver, is the North American standard — it does the radiation exchange factor calculation (RadCAD), orbital heating (Orbital Heating module) and the lumped-parameter thermal network in one environment. **ESATAN-TMS** (ITP Aero) is the European equivalent and the one ECSS-driven projects generally use. Both are expensive. **OpenFOAM** handles CFD but is not a spacecraft thermal tool; for early sizing, a hand-built lumped-node model in Python with the radiation balance from `05` is often enough and always more transparent.

**Radiation environment:** **SPENVIS** (ESA, free web tool) runs AE9/AP9 or AE8/AP8 trapped-particle models, SHIELDOSE-2 dose-depth calculations, SEE rate estimates and atomic-oxygen fluence for a specified orbit and shielding. It is the standard first-pass tool and it is free — every mission should run it early.

## 7. Rocketry and hobby tools

**OpenRocket** — free, **CC BY-SA 4.0**, current version **24.12**, available for Windows, macOS, Linux and as a platform-independent JAR. Six-degrees-of-freedom flight simulation tracking over 50 variables, multi-stage and dual-deployment support with event triggers, a motor database sourced from **ThrustCurve**, a large catalogue of commercial components and materials with custom part creation, real-time stability feedback (centre of pressure versus centre of gravity as you edit), 2D and 3D views, design optimisation and export. It is the standard tool for model and high-power rocketry and is accurate enough that competition teams use it for altitude prediction.

**RASAero II** — free, Windows-only, with better supersonic aerodynamics than OpenRocket (it uses a full aerodynamic prediction method rather than Barrowman-derived extensions) and is preferred for high-Mach flights and for anything targeting 30,000 ft or higher. Many Spaceport America Cup teams run both and compare.

**RockSim** — commercial, similar scope to OpenRocket, less used now that OpenRocket is mature.

**ThrustCurve.org** — free motor database, the source of the certified motor data both tools consume.

**Kerbal Space Program with Realism Overhaul** — worth taking seriously as a learning tool. Base KSP teaches orbital intuition — that you speed up to go higher and thereby fall behind, that plane changes are expensive, that rendezvous is counter-intuitive — faster and more durably than any textbook, because you have to actually do it. With the **Realism Overhaul** / **Realistic Progression** mod stack it uses real Earth dimensions, real engine performance including ullage and ignition limits, real propellant boil-off, life support, and principia-based n-body gravity if you add the **Principia** mod. At that point it is a genuine, if unforgiving, mission-design sandbox. It is not a substitute for GMAT — it will not give you a manoeuvre plan you can trust to three decimal places — but as an intuition builder it is unmatched, and a surprising number of working engineers cite it as their entry point.

## 8. CubeSat-specific tools

**NASA's State of the Art of Small Spacecraft Technology** report (free, updated periodically) is the component catalogue — every subsystem with vendors, mass, power and TRL. **SPENVIS** for the environment. **GMAT** or **Orekit** for the orbit and lifetime. **STK's free tier** or **Orekit's event detection** for ground station access windows. **GNU Radio** with an RTL-SDR for the ground segment, and **SatNOGS** — an open network of volunteer ground stations that will track and record your satellite for free, which is the single most useful thing a student CubeSat team can know about. **Systems Tool Kit**, **42** or **Basilisk** for ADCS simulation. **KiCad** and **FreeCAD** for hardware if budget is the constraint.

## Open questions

- STK version numbering is rolling and tied to the Ansys release cycle; no version is quoted.
- RPA's current version and pricing were not verified in this pass.
- Thermal Desktop and ESATAN-TMS versions and licensing terms were not verified.
- The CEA output table in §3 is a representative case consistent with the hand calculation in `02`, not a captured run; run CEA yourself for design work.

## Sources

- [GMAT release history](https://sourceforge.net/projects/gmat/files/GMAT/) — NASA/SourceForge, accessed 2026-08-25
- [GMAT (NASA software catalog)](https://software.nasa.gov/software/GSC-17177-1) — NASA, accessed 2026-08-25
- [Orekit](https://github.com/CS-SI/Orekit) — CS GROUP / GitHub, accessed 2026-08-25
- [Basilisk](https://github.com/AVSLab/basilisk) — AVS Lab, University of Colorado / GitHub, accessed 2026-08-25
- [hapsira](https://github.com/pleiszenburg/hapsira) — GitHub, accessed 2026-08-25
- [poliastro (archived)](https://github.com/poliastro/poliastro) — GitHub, accessed 2026-08-25
- [SPICE Toolkit](https://naif.jpl.nasa.gov/naif/toolkit.html) — NASA NAIF / JPL, accessed 2026-08-25
- [NASA RP-1311 Part I (CEA)](https://ntrs.nasa.gov/citations/19950013764) — NASA NTRS, accessed 2026-08-25
- [OpenRocket](https://openrocket.info/) — OpenRocket, accessed 2026-08-25
- [CelesTrak fundamentals-of-astrodynamics](https://github.com/CelesTrak/fundamentals-of-astrodynamics) — GitHub, accessed 2026-08-25
