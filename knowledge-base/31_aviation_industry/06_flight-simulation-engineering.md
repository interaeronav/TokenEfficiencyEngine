---
id: aviation_industry.simulation
title: Flight simulation engineering — how full flight simulators are built and qualified
domain: 31_aviation_industry
tags: [ffs, fstd, cs-fstd, part-60, icao-9625, motion-cueing, washout-filter, hexapod, image-generator, collimated-display, control-loading, arinc-610, rehosting, qtg, jsbsim, x-plane, msfs, cae, l3harris, thales, flightsafety]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "14 CFR Part 60 — Flight Simulation Training Device Initial and Continuing Qualification and Use", url: "https://www.ecfr.gov/current/title-14/chapter-I/subchapter-D/part-60", publisher: "US Government (eCFR)", accessed: 2026-08-25}
  - {title: "CS-FSTD(A) Issue 2 — Update of flight simulation training device requirements (UPRT)", url: "https://www.easa.europa.eu/en/document-library/certification-specifications/cs-fstda-issue-2", publisher: "EASA", accessed: 2026-08-25}
  - {title: "Flight simulator", url: "https://en.wikipedia.org/wiki/Flight_simulator", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Stewart platform", url: "https://en.wikipedia.org/wiki/Stewart_platform", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "JSBSim", url: "https://en.wikipedia.org/wiki/JSBSim", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "X-Plane (simulator)", url: "https://en.wikipedia.org/wiki/X-Plane_(simulator)", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Microsoft Flight Simulator 2024", url: "https://en.wikipedia.org/wiki/Microsoft_Flight_Simulator_2024", publisher: "Wikipedia", accessed: 2026-08-25}
related: [aviation_industry.training, aviation_industry.software]
unit_system: SI
---

# Flight simulation engineering — how full flight simulators are built and qualified

**Summary.** A Level D full flight simulator is a real-time, hard-deadline distributed computing system that must reproduce an aircraft's measured behaviour to within published numerical tolerances, drive a six-degree-of-freedom motion platform whose travel is a metre or two while representing accelerations that in reality would displace the pilot hundreds of metres, present a collimated visual scene of at least 200° × 40° at low latency, and load the flight controls with forces derived from a physical model of the aircraft's control system — all while an instructor injects failures from a station behind the pilots. Its qualification is not a matter of subjective realism but of a **Qualification Test Guide** containing several hundred objective tests, each comparing the simulator's response to flight-test data within a stated tolerance. This file covers the regulatory framework, every major subsystem, the data packages behind them, the manufacturers, the desktop end of the market, and how one would actually go about building a simulator.

## Key facts

| Item | Detail |
|---|---|
| FAA regulation | 14 CFR **Part 60** — initial and continuing qualification of FSTDs |
| Part 60 appendices | A: aeroplane FFS; B: aeroplane FTD; C: helicopter FFS; D: helicopter FTD; E: quality management system; F: definitions and abbreviations |
| FAA FFS levels | A, B, C, D |
| FAA FTD levels | 4, 5, 6, 7 |
| EASA specification | **CS-FSTD(A)** for aeroplanes, **CS-FSTD(H)** for helicopters; devices FFS A–D, FTD 1–2, FNPT I–II(MCC), BITD |
| ICAO document | **Doc 9625, Manual of Criteria for the Qualification of Flight Simulation Training Devices** — Vol I aeroplanes (Ed. 4), Vol II helicopters |
| Doc 9625 Ed.3/4 approach | Seven fidelity **Types** (I–VII) defined by training task rather than by a single letter grade |
| Level C/D motion | Six degrees of freedom required |
| Level C FoV | ≥ 75° horizontal per pilot (continuous, cross-cockpit) |
| Level D FoV | ≥ 150° horizontal (in practice 180°–220° × 40° collimated) |
| Continuing qualification | Annual objective testing; recurrent evaluation typically every 12 months, extendable toward 36 months under an approved QMS |
| Market share | CAE ~70%, L3 CTS ~20% (as cited by Wikipedia's flight simulator article — treat as indicative and dated) |

## 1. The qualification framework

### What a simulator is *for*, legally

An FSTD earns credit against a training or checking requirement. The higher its qualification level, the more of the licensing requirement it can replace. A Level D FFS can be used for **Zero Flight Time Training** — an entire type rating including the first landings — which is the commercial reason Level D exists. A Level A device cannot. Nothing else about the qualification hierarchy matters as much as this: the level determines the training credit, and the training credit determines whether the capital cost is recoverable.

### FAA 14 CFR Part 60

Part 60 governs initial and continuing qualification of FSTDs used to meet training, evaluation or flight experience requirements for flight crew certification. Its structure:

| Appendix | Content |
|---|---|
| **A** | Qualification Performance Standards for **aeroplane full flight simulators** |
| **B** | QPS for **aeroplane flight training devices** |
| **C** | QPS for **helicopter FFS** |
| **D** | QPS for **helicopter FTD** |
| **E** | **Quality Management System** requirements the sponsor must establish and maintain |
| **F** | Definitions and abbreviations |

Each QPS appendix has the same internal structure: **Attachment 1** the objective test table (the tolerances), **Attachment 2** the general simulator requirements table (what hardware and function must exist at each level), **Attachment 3** the functions and subjective test table (what the evaluator will fly), and **Attachment 4** sample documents.

**Sponsor** is the FAA's term for the certificate holder responsible for the device — usually an airline or a training centre, not the manufacturer. The sponsor holds the qualification.

### EASA CS-FSTD(A)

The European equivalent, issued as a Certification Specification under the Basic Regulation, with the FSTD operator holding an **FSTD Qualification Certificate** under **Part-ORA Subpart FSTD**. **CS-FSTD(A) Issue 2** was published specifically to update requirements for **Upset Prevention and Recovery Training** — extending the required validity of the aerodynamic model beyond the normal envelope, requiring instructor feedback when the device is flown outside its validated envelope, and adding stall model and buffet requirements.

Device classes under CS-FSTD(A):

- **FFS Level A / B / C / D** — full flight simulators, motion required.
- **FTD Level 1 / 2** — flight training devices; a replica flight deck, no motion (or limited), systems modelled.
- **FNPT I / II / II MCC / III** — Flight and Navigation Procedures Trainers; generic rather than type-specific, used for instrument and MCC training.
- **BITD** — Basic Instrument Training Device, the lowest tier, for PPL/IR procedural work.

EASA and FAA levels are broadly aligned (the criteria descend from the same JAR-STD/AC 120-40 lineage) but are not identical, and a device qualified by one authority requires evaluation, not automatic acceptance, by the other. The **FSTD Operational Suitability Data (OSD)** and the OEM's **Data Package** underpin both.

### ICAO Doc 9625

The classical A/B/C/D ladder has an inherent flaw: it bundles fidelity attributes together, so an operator wanting high-fidelity engine failure training but no visual system has no way to buy it, and an operator wanting a very high fidelity visual for a specific approach must buy a full Level D. **ICAO Doc 9625 Edition 3 (2009) and Edition 4** replaced the letter grades with **seven fidelity Types (I–VII)**, each defined by the set of training tasks it supports, and each specifying the required fidelity of each of a set of **features**:

- Flight deck layout and structure
- Flight model (including ground handling)
- Ground handling
- Aerodynamic and engine modelling
- Control loading (flight controls and forces)
- Sound cues
- Visual cues
- Motion cues
- Environment (weather, ATC, navigation)
- Instructor operating station

Type VII is the equivalent of Level D; Type I is roughly a basic procedural trainer. The intent is that a regulator can define what an operator needs for a given training task and the operator buys exactly that. Adoption has been partial: EASA's proposed FSTD rule restructuring drew on 9625, and several national authorities reference it, but Part 60 and CS-FSTD retain the letter grades as the operative standard.

### The FFS levels, and what each actually demands

**Level A** — the entry point. Motion system with **at least three degrees of freedom**. Aeroplanes only. Aerodynamic programming sufficient for the objective tests at the level. Visual system required (day, at minimum, with a defined field of view). In practice almost nobody builds Level A any more.

**Level B** — three-axis motion, higher-fidelity aerodynamic model including ground handling and ground effect, and the entry level for helicopter FFS. Night visual capability.

**Level C** — **six degrees of freedom motion**. Visual field of view of **at least 75° horizontal and 40° vertical per pilot**, continuous and cross-cockpit. Night and dusk visual scenes. Transport delay (latency) of the total system limited (traditionally 150 ms from control input to the corresponding motion/visual/instrument response). Daylight not required. Sound of precipitation and significant aeroplane noises, and realistic engine and airframe sounds.

**Level D** — the highest. Six degrees of freedom. **At least 150° horizontal field of view** (delivered in practice as 180°–220°) and 40° vertical, **collimated** so the image appears at optical infinity. **Daylight, dusk and night** scenes with a specified minimum number of light points and specified contrast and highlight brightness. Full sound simulation including the sounds of a crash. Motion cueing including specific effects: runway rumble, oleo deflection, buffet due to gear/flap/speedbrake extension, Mach buffet, stall buffet, thrust effects with brakes set, engine malfunction and airframe vibration, and touchdown cues. Control loading dynamic response matched to the aeroplane. Transport delay limited to 100 ms or better in most current interpretations. And, critically, the aerodynamic model must be validated by flight test data across the tested envelope.

Only Level D (and Level C with experience-based credit) supports zero flight time training.

### The Qualification Test Guide

The **QTG** is the document that makes the whole thing objective. It contains, for every required test:

- the test condition (configuration, weight, CG, altitude, speed, thrust setting),
- the **flight test data** (or other approved validation data) plotted or tabulated,
- the **simulator result** under identical conditions,
- the **tolerance** from the QPS/CS table,
- a statement of compliance.

Once the authority has evaluated the device and approved the QTG, it becomes the **Master QTG (MQTG)** — the permanent qualification baseline. Every subsequent recurrent evaluation compares the device against the MQTG, not against the aircraft.

**Objective testing** categories and representative tolerances (Part 60 Appendix A Attachment 1 / CS-FSTD(A) equivalent):

| Test group | Examples | Representative tolerance |
|---|---|---|
| **Performance — taxi** | Minimum radius turn, rate of turn vs. nosewheel steering angle | ±10% or ±0.6 m on radius |
| **Performance — take-off** | Ground acceleration time and distance, minimum control speed (Vmcg/Vmca), rotation rate, one-engine-inoperative climb | ±5% time, ±5% or 61 m distance, ±10% or ±10 kt on speeds |
| **Performance — climb** | Normal and OEI climb rate | ±3% or ±100 fpm |
| **Performance — cruise** | Acceleration/deceleration times, level-flight power | ±5% time, ±5% thrust |
| **Performance — descent/approach/landing** | Descent rate, approach speed, landing distance, flare | ±3% or ±100 fpm; ±5% or 61 m |
| **Handling qualities — static** | Control force vs. displacement (all axes), trim, brake pedal force | ±2 lb (0.9 kg) breakout, ±10% force |
| **Handling qualities — dynamic** | Short period, phugoid, Dutch roll, spiral stability, roll response, control free response | ±10% period, ±10% of time to ½ or 2× amplitude, ±0.02 damping ratio |
| **Motion system** | Frequency response, leg balance, turn-around check, motion cueing performance signature (MCPS) | per manufacturer's design and the QPS |
| **Visual system** | Field of view, system response time, surface contrast ratio, highlight brightness, light point size and contrast | e.g. contrast ratio ≥ 5:1; light point size ≤ 5 arcmin |
| **Sound system** | Frequency response at defined conditions, background noise | ±5 dB over defined bands |
| **Latency / transport delay** | Control input to instrument/motion/visual response | ≤ 150 ms (C), ≤ 100 ms typical (D), and the three channels must be coherent |

Typical volume: **several hundred objective tests** in a large-aeroplane Level D QTG, plus a subjective functions-and-checks list of comparable length.

**Subjective testing** is done by an authority evaluator, usually a pilot type-rated on the aeroplane, flying the device against Attachment 3's task list: preflight, engine start, taxi, take-off (normal, crosswind, engine failure at V1, rejected), climb, cruise, all approach types, missed approach, landing, malfunctions, and specific handling assessments.

**Continuing qualification**: the sponsor runs the **entire MQTG objective test set over a 12-month period** (typically a quarter of the tests each quarter), performs functional and subjective checks, keeps a discrepancy log, and holds a **Quality Management System** under Appendix E. The authority conducts recurrent evaluations, nominally every 12 months, with the interval extendable toward 36 months where the QMS is mature.

## 2. The flight model

### The aerodynamic data package

The starting point is the OEM's **flight test data package** — the single most valuable and most restricted artefact in the simulator business. Its contents:

- **Aerodynamic model** — usually as a coefficient build-up: dimensionless force and moment coefficients (C_L, C_D, C_Y, C_l, C_m, C_n) as functions of angle of attack α, sideslip β, Mach number, control surface deflections, flap and slat configuration, landing gear position, speedbrake and spoiler deflection, dynamic derivatives (C_lp, C_mq, C_nr, etc.), and ground effect as a function of height above ground. Delivered as multi-dimensional lookup tables with defined interpolation, plus the equations that combine them.
- **Mass properties** — inertia tensor as a function of loading, CG range, fuel state.
- **Engine model** — see below.
- **Flight control system** — the full architecture: gearings, gains, schedules, control law logic for fly-by-wire types, actuator dynamics, and failure behaviour.
- **Landing gear model** — oleo strut force-stroke curves, damping, tyre spring rate, tyre friction as a function of slip ratio and surface condition, steering geometry, brake torque vs. pressure vs. speed and temperature, anti-skid logic.
- **Systems data** — schematics, logic, timing, failure modes.
- **Validation flight test data** — the actual recorded time histories for each QTG test condition, from the certification flight test programme, with sufficient instrumentation and a documented data-reduction method.

**Coefficient build-up vs. CFD-derived.** The certified simulator model is fundamentally an **empirical, table-driven** model, built by regressing wind-tunnel and flight-test measurements into a functional form. CFD contributes to the design and to filling gaps in the wind-tunnel matrix, but a purely CFD-derived aerodynamic model has never been the basis of a Level D qualification, because the tolerance tables demand agreement with *measured aircraft behaviour*, not with a prediction. Where CFD does earn its place is in the extended envelope: the post-stall and high-α regions required for UPRT, where flight test data is limited for obvious reasons, are typically built from a combination of wind-tunnel rotary-balance and forced-oscillation data, CFD, and engineering judgement, with the model explicitly flagged as outside the validated envelope so the IOS can warn the instructor.

The alternative modelling philosophy — **component/blade-element** — is used by X-Plane and by some engineering simulators: rather than a whole-aircraft coefficient table, the surfaces are divided into elements, each element's local angle of attack and velocity are computed, a 2-D aerofoil polar is applied, and the forces are summed. It gives plausible behaviour for an arbitrary geometry with no flight-test data, which is exactly why it is valuable for design and useless for certification: plausible is not the same as within ±10%.

### Engine model

Two approaches:

1. **Thermodynamic/component-level model** — compressor and turbine maps, combustor, bleed and power extraction, shaft dynamics. Accurate transients, computationally heavier, requires proprietary maps.
2. **Table-driven performance deck** — net thrust, fuel flow, N1/N2/EGT as functions of Mach, altitude, ambient temperature and throttle/thrust lever position, with first- and second-order lags representing spool-up dynamics.

Most FFS engine models are the second, tuned so that acceleration and deceleration times, thrust asymmetry after failure, relight envelope and windmilling drag all meet tolerance. Engine failure modelling must include the yawing moment build-up rate accurately — the Vmcg test is unforgiving.

The **FADEC** is usually **rehosted** (see §7) rather than simulated, because reimplementing its logic is both expensive and a source of divergence.

### Ground handling model

Frequently the weakest part of a simulator and the source of most pilot complaints. It must reproduce:

- **Oleo dynamics** — nonlinear gas spring plus orifice damping, with the correct static compression at each weight so the aircraft "sits" right and the correct dynamic response on touchdown.
- **Tyre model** — vertical stiffness, cornering stiffness, μ-slip curve for dry, wet, contaminated (standing water, slush, snow, ice) surfaces, and hydroplaning.
- **Steering and rudder blending**, nosewheel scrub, differential braking.
- **Brake model** — torque vs. pressure vs. speed, fade with temperature, anti-skid cycling that the pilot can feel through the pedals.
- **Runway surface** — crown, slope, roughness spectrum for the rumble cue, centreline and joint spacing.
- **Crosswind** on the ground, including the weathervaning moment.

QTG tests here include minimum radius turn, rate of turn vs. steering angle, brake effectiveness, and the crosswind landing and take-off subjective checks.

## 3. The motion platform

### The hexapod

Virtually every FFS uses a **Stewart platform** (also called a hexapod or Gough-Stewart platform): six prismatic actuators attached in pairs to three points on a base and crossing over to three points on the moving platform, giving **six degrees of freedom** — surge (x), sway (y), heave (z), roll (φ), pitch (θ), yaw (ψ). The payload is the cockpit shell plus the visual system, typically 12–18 tonnes.

**Kinematics.** The *inverse* kinematics — given a desired platform pose, find the six actuator lengths — has a simple closed-form solution: for each leg, the required length is the norm of the vector from the base attachment point to the transformed platform attachment point. That is why the architecture is used: the control problem is trivially solvable in real time at 1 kHz or better. The *forward* kinematics — given six lengths, find the pose — has no general closed form and must be solved iteratively (Newton-Raphson from the previous solution), which is fine because it is only needed for monitoring and for the safety envelope check.

**Actuation.**

- **Hydraulic** — the historical standard. A central pump station at 200 bar or so, servo valves, hydraulic cylinders. Very high force density, excellent stiffness and bandwidth, but a large plant room, high energy consumption even at idle, oil leaks, temperature-dependent behaviour, and noise.
- **Electric** — now dominant for new build. Ball-screw or roller-screw actuators driven by permanent-magnet servo motors. Lower standing power (an order of magnitude reduction in energy use is commonly claimed), no hydraulic infrastructure, quieter, simpler maintenance. The engineering challenges are backdriveability, screw life, and the failure mode (a screw jam is more dangerous than a hydraulic failure, so electric platforms need mechanical brakes and a controlled-descent capability).

**Envelope.** A typical FFS hexapod offers roughly ±0.9–1.3 m of heave, sway and surge; ±25–35° of roll and pitch; ±35–45° of yaw; with accelerations up to about 0.6–1 g and rotational rates of 30–50°/s. Against this, a real aircraft's take-off produces a sustained ~0.3 g longitudinal acceleration for 30–40 seconds — which would require several hundred metres of travel.

### Motion cueing and washout

The **motion cueing algorithm (MCA)** is the bridge between an unbounded aircraft and a bounded platform. The classical (Schmidt-Conrad) washout filter has three channels:

1. **High-pass (translational) channel.** Specific force from the flight model is high-pass filtered so that only the *onset* transient is reproduced as platform translation. The steady component is removed, and the platform is *washed out* back toward neutral at a rate below the vestibular detection threshold.
2. **Tilt coordination (low-pass) channel.** The sustained specific force is reproduced by slowly tilting the platform so that a component of gravity acts along the required body axis. The pilot, unable to distinguish gravity from sustained linear acceleration (Einstein's equivalence principle, and the otoliths cannot either), perceives sustained acceleration. The tilt rate must stay below the semicircular canals' detection threshold — commonly taken as **~3°/s in pitch and roll** — or the pilot perceives a rotation instead and the illusion breaks.
3. **Rotational channel.** Angular rates are high-pass filtered and reproduced directly, then washed out.

A **coordinated adaptive** or **optimal (LQR-based)** MCA improves on the classical filter by varying the filter parameters with the manoeuvre or by optimising against a model of the vestibular system, but the classical washout remains the production standard because it is predictable and tunable by hand.

**Tuning** is craft, not science. A simulator is tuned by an experienced pilot and a motion engineer flying representative manoeuvres and adjusting gains and break frequencies until the cues feel right and do not fight the visual. The regulatory hook is the **Motion Cueing Performance Signature (MCPS)** test introduced to give an objective record of the tuning so that recurrent evaluation can detect drift.

### The vestibular system and the illusions exploited

- **Otolith organs** (utricle and saccule) sense specific force — the sum of linear acceleration and gravity. They cannot distinguish the two. This is the entire basis of tilt coordination, and also the basis of the **somatogravic illusion** (a real accident cause: acceleration on go-around perceived as pitch-up, leading to a push-over into the sea — the Flash Airlines 604 and Gulf Air 072 pattern).
- **Semicircular canals** sense angular acceleration, and behave as heavily damped angular accelerometers with a time constant of order 5–10 s. Sustained rotation is not perceived; hence the **somatogyral illusion** and the **graveyard spiral**. The canals have a detection threshold below which rotation is imperceptible — the washout filter lives in that gap.
- **Coriolis / cross-coupled illusion** — head movement during a sustained turn stimulates a canal that was not previously stimulated, producing a violent tumbling sensation. Simulators can produce this if the yaw channel is badly tuned.
- **Proprioception and the seat** — pressure distribution through the seat pan and back is a strong cue, which is why **dynamic seats** and **G-seats** (variable seat-pan pressure and lap-belt tension) can substitute for some platform motion.
- **Visual-vestibular conflict** is the mechanism of **simulator sickness**: when the visual scene says one thing and the vestibular system another, a subset of subjects become nauseated. Latency and mismatched gains are the main causes; this is a hard engineering constraint, not a comfort issue.

There is a live and genuinely unsettled research question about whether platform motion improves *training transfer* at all for large transport aircraft. Several controlled studies have found little or no transfer benefit for Level D motion versus a well-instrumented fixed-base device with vibration and a dynamic seat, for the specific tasks airline pilots train. The regulatory requirement for motion at Level C/D is therefore partly historical. The counter-argument, which is not trivial, is that motion prevents pilots from learning to fly *the simulator* rather than the aircraft, and that its absence changes control strategy in ways that would transfer negatively.

## 4. The visual system

### Image generation

The **Image Generator (IG)** renders the out-the-window scene. Historically these were bespoke machines (Evans & Sutherland's ESIG and Harmony, CAE's Maxvue, Rockwell Collins EP-8000); today they are clusters of commodity GPUs running specialised software — **CAE Medallion/Prodigy** (the latter built on the Unreal Engine), **Rockwell Collins/Collins Aerospace EP-8100**, **Evans & Sutherland**, **Presagis Vega Prime**, **VT MÄK**, **Diamond Visionics GenesisRTX**.

Requirements that distinguish a training IG from a game engine:

- **Deterministic frame rate** at 60 Hz with no dropped frames — a stutter is a qualification failure, not a nuisance.
- **Correlation** with the flight model and the navigation database: the runway the IG draws must be at the same coordinates the ILS model and the terrain database use, to sub-metre accuracy. Loss of correlation is the classic integration bug.
- **Calibrated photometry** — specified surface contrast ratio (≥5:1 typically), highlight brightness, light point size (≤5 arcmin) and light point contrast, all measurable at the eyepoint.
- **Fixed, low latency** through the whole chain.

### Displays

Two families:

- **Collimated cross-cockpit display.** A curved back-projection screen images onto a large **spherical mirror** (a mylar membrane mirror held by vacuum, or a rigid glass mirror), which collimates the light so that the image appears at **optical infinity**. This is the only way to give both pilots a geometrically correct scene from their own eyepoints without parallax error, and the only way the visual scene's apparent distance matches the real world for depth judgement in the flare. Typical field of view **200°–220° horizontal × 40° vertical**, sometimes with a chin window extension. This is what Level D means in practice.
- **Direct-projection dome or wraparound** — used for military and for lower-level devices; cheaper, but the image is at the screen distance, so cross-cockpit geometry is wrong and depth cues are compromised.

Projection technology has moved from CRT to DLP to **laser-phosphor DLP** and now increasingly to **direct-view LED** and **LCoS**, driven by brightness (needed for daylight scenes through a collimating mirror, which throws away a lot of light), contrast, and lamp life. Blending and geometry correction across three to six projector channels is done in the IG or in a dedicated warp-and-blend processor, and must be re-calibrated periodically — a recurrent qualification item.

### Database generation

The visual database is built from:

- **Terrain elevation** — SRTM, Copernicus DEM, or licensed higher-resolution data; converted to a multi-resolution terrain mesh with level-of-detail transitions that do not "pop".
- **Imagery** — satellite or aerial orthophotos, resampled and colour-balanced, with **procedural texture** substituted at high zoom because the source resolution runs out. The transition between photo-texture and procedural detail is a large part of perceived quality.
- **Airport models** — built to the AIP and to survey data: runway and taxiway geometry, markings, signage, lighting (individual light points with correct photometry, beam patterns and colour), buildings, jet bridges, and the approach lighting system. For a Level D airport model, the lighting must be individually modelled light points with the correct intensity distribution, because that is what the pilot uses in low visibility.
- **Culture and features** — roads, rivers, coastlines, vegetation, from OpenStreetMap-class or licensed vector data.
- **Moving models** — other aircraft, ground vehicles, marshallers, birds.

Toolchains: **Presagis Terra Vista** and **Creator**, **TrianGraphics Trian3DBuilder**, **Diamond Visionics**, plus in-house pipelines at CAE and L3Harris. Formats: **OpenFlight (.flt)** is the long-standing interchange format; **CDB (Common Database)**, an OGC standard, is the modern one for a correlated, runtime-ready synthetic environment shared between IG, radar, sensor and CGF systems.

Airports for a training simulator are usually built to **Level D standard for the operator's own network** (perhaps 20–100 airports in full fidelity) with generic representation elsewhere.

### Weather, night and time of day

- **Visibility and RVR** must be settable and must produce a scene that the pilot can use to make a Cat I/II/III decision — which means the **fog model** must be physically calibrated (Koschmieder's law) rather than an artistic haze, and the approach lighting must appear and disappear at the correct slant range.
- **Cloud** — layered decks with settable bases and tops, plus volumetric cloud for realism; entering cloud must produce the correct loss of visual reference immediately.
- **Precipitation** — rain on the windshield (with wiper interaction), snow, and its effect on visibility and on the runway surface (which must be correlated with the ground handling model's friction).
- **Night** — the light point model dominates. The number of simultaneously displayable light points was for decades the headline IG specification; on modern hardware it is not a constraint, but the photometry still is.
- **Special effects** — lightning, St Elmo's fire, sun glare and its position from the ephemeris, moon phase, runway contamination, windshear visualisation, wake vortex, volcanic ash.

## 5. Control loading

The pilot's hands and feet are on a **force-feedback servo system**, not on a spring. The control loading system (CLS) must reproduce:

- **Breakout force** and friction.
- **Force gradient** vs. displacement, which for a conventional aircraft varies with airspeed, configuration and trim, and for a fly-by-wire aircraft is usually a fixed artificial feel.
- **Dynamic response** — the inertia and damping of the control circuit, so that a rapid input feels right and the control column's free response after release matches the aeroplane.
- **Trim** — the movement of the neutral point, and (on a Boeing) the stabiliser trim wheel spinning with the correct noise and torque.
- **Non-linearities** — cable stretch, bobweights, downsprings, the feel unit's q-feel schedule, aileron/spoiler blending.
- **Failures** — jammed controls, hydraulic system loss and the resulting force increase, manual reversion, runaway trim.
- **Tactile cues** — stick shaker (the real hardware is usually fitted), stick pusher, autopilot disconnect, and on Airbus the sidestick's fixed spring feel and the priority takeover.

Architecture: each axis has a servo (historically hydraulic, now almost universally electric brushless), a position sensor, a force sensor, and a high-rate control loop (**1–2 kHz**) closing on a **force-displacement model** of the aircraft's control system. The model itself is provided in the OEM data package as a block diagram with gains, gearings and nonlinearities.

QTG tests: static force-vs-displacement curves for each axis in each configuration (tolerance typically ±2 lb breakout and ±10% gradient), and dynamic control free-response tests (the column released from a displacement, comparing the damped oscillation against the aeroplane).

## 6. Sound

Underrated and a genuine cue. Requirements at Level D include engine sounds at all power settings, airframe and slipstream noise as a function of airspeed, gear and flap operation and the associated aerodynamic noise change, rain and hail, tyre rumble on the runway with the correct correlation to surface and speed, touchdown, thrust reverser, APU, packs and bleed, cabin address, warning and caution tones, stall buffet, and the sound of a crash.

Implementation: recorded samples from the aircraft (an OEM data package usually includes calibrated sound recordings at defined conditions), pitch- and amplitude-modulated in real time, mixed and reproduced through a multi-channel system positioned to give the correct directionality. QTG tests measure sound pressure level across octave bands at defined conditions against the aircraft recordings, typically to ±5 dB, plus a background-noise test.

## 7. Aircraft systems simulation: rehosting versus simulation, and ARINC 610

The flight deck contains dozens of computers — FMS, FCC, FMGC, EEC/FADEC, air data and inertial reference, warning computers, ECAM/EICAS, TCAS, EGPWS/TAWS, weather radar, CMC. Three ways to represent each:

1. **Software simulation (re-engineering)** — write a model that behaves like the box. Cheap for simple systems, hopeless for an FMS: the behaviour is too complex, the OEM will not give you the requirements, and every software update diverges.
2. **Rehosting** — take the **actual target software** from the aircraft LRU and run it on the simulator's host, either recompiled for the host processor or, more commonly, executed on an **instruction-set emulator** of the original processor (PowerPC, 68k, i960, AMD 29k depending on vintage). The box's I/O is redirected to the simulation's data bus. This gives bit-exact behaviour and updates with the aircraft's software load. It is the standard approach for FMS, flight control computers and warning systems.
3. **Stimulation** — put the **real hardware LRU** in the simulator and drive its inputs with simulated signals (ARINC 429 words, discretes, analogue signals) so that it believes it is flying. This is what is done for boxes whose software cannot be rehosted or whose hardware behaviour matters (some displays, radios, TCAS).

The **simulation/stimulation distinction** is the core of **ARINC 610** (*Guidance for Design of Aircraft Equipment and Software for Use in Training Devices*), which asks avionics manufacturers to build in the hooks that make their equipment usable in a simulator:

- a **simulation mode** the box can be commanded into,
- the ability to accept simulated air data, inertial data and radio inputs rather than real sensors,
- **freeze, reposition, snapshot and reset** support — a simulator must be able to jump the aircraft to a new position and state instantly, which a real FMS is not designed to do,
- suppression of built-in test failures caused by absent real hardware,
- and defined data structures for the training device to read internal state.

ARINC 610 compliance is a procurement requirement in modern airliner programmes precisely because retrofitting it is prohibitively expensive. Its absence is why some older types are painful to simulate.

**Data buses.** The simulator reproduces ARINC 429 (the workhorse), ARINC 629 (777), AFDX/ARINC 664 (A380, A350, 787, and the 777X), CAN, MIL-STD-1553 in military applications, and discrete and analogue I/O. Either real bus hardware is used (for stimulated LRUs) or the bus traffic is simulated in shared memory.

## 8. The Instructor Operating Station

The IOS is the simulator's user interface for the person who is not being trained. Functions:

- **Scenario setup** — aircraft position, altitude, speed, configuration, weight and CG, fuel, time of day, date.
- **Environment** — wind (including gradient, shear and turbulence models — Dryden or von Kármán spectra), temperature, QNH, cloud layers, visibility/RVR, precipitation, runway surface condition and braking action, icing.
- **Malfunction insertion** — a catalogue of several hundred to a couple of thousand failures, insertable immediately, on a condition (at a given altitude or speed), or on a timer, with severity where applicable.
- **Freeze / reposition / repeat** — position freeze, total freeze, flight freeze, reposition to a stored point, and "fly again" from a snapshot.
- **Monitoring** — map display with aircraft symbol and approach profile, repeater instruments, engine parameters, a plot of the approach against the ILS, and a **debriefing** capability: recorded flight path, control inputs, parameter traces, and increasingly video from head-mounted or cockpit cameras.
- **Grading** — for EBT/CBTA the IOS must support competency grading against the eight or nine competencies, with observable behaviours, and export to the operator's training records system.
- **Automated exercise scripting** — for standardised recurrent sessions.

Modern IOS design has moved to touchscreen panels behind the pilots, plus a wireless tablet so the instructor can grade from the observer's seat, and — for EBT — deliberately fewer, simpler controls, because the doctrine is that the instructor should be facilitating rather than driving.

## 9. Real-time computing and determinism

The simulator is a **hard real-time system**: the aerodynamic model, control loading and motion must be updated at a fixed rate with bounded jitter, because the pilot's control loop closes through them.

Typical rates:

| Subsystem | Rate |
|---|---|
| Control loading servo loop | 1–2 kHz |
| Motion platform actuator control | 500 Hz – 1 kHz |
| Flight dynamics / equations of motion | 60–120 Hz (JSBSim defaults to 120 Hz; many FFS run 60 Hz with sub-stepping) |
| Systems models | 30–60 Hz |
| Image generation | 60 Hz |
| Sound | audio rate, event-driven |
| IOS | 5–20 Hz |

Architecture: a **host computer** running the flight model, systems and coordination, distributed over a deterministic network (reflective memory such as GE/Abaco VMIC or Dolphin, or a real-time Ethernet with time-triggered scheduling) to the IG cluster, the motion controller, the control loading controller, the sound system and the IOS. Historically these ran on real-time UNIX or VxWorks; now commonly **Linux with PREEMPT_RT** or a real-time hypervisor, with the hard loops on dedicated isolated cores.

Determinism engineering practices: fixed-step integration (usually a second- or fourth-order Runge-Kutta, or Adams-Bashforth for the equations of motion, chosen for stability at the step size rather than for accuracy alone); no dynamic memory allocation in the real-time path; no unbounded loops; pre-allocated message buffers; a watchdog on every node; and a measured, budgeted **transport delay** from control input through the model to instrument, motion and visual response, with the three channels deliberately aligned so they do not conflict.

**Transport delay measurement** is itself a QTG test: a step input is applied at the control, and the time to the corresponding response at the instrument, at the motion platform accelerometer, and at the visual scene is recorded. Level D requires this to be within about 100 ms and, importantly, requires the three channels to be **coherent** — a visual that leads the motion by 60 ms is worse than both being late together.

## 10. The manufacturers

| Company | Position |
|---|---|
| **CAE** (Montreal) | The dominant FFS manufacturer, cited at roughly **70% market share** and ~US$2.8 bn revenue in the source used here (indicative and dated). Builds simulators, operates a very large global training network, and sells the 7000XR series with the Prodigy (Unreal-based) image generator. Its business model is increasingly training services rather than device sales. |
| **L3Harris Commercial Training Solutions** (formerly L-3 Link, incorporating Thales Training & Simulation's civil business acquired in 2021 and CTC/Airline Academy) | The number two, cited at ~20% share. RealitySeven platform, plus a large ab-initio academy business. |
| **TRU Simulation + Training** (Textron) | Built as the Boeing-preferred supplier for the **737 MAX** and **777X** simulators; also Cessna/Beechcraft devices. |
| **Thales** | Retains defence and some civil simulation after divesting the civil FFS business; strong in avionics-adjacent simulation and in helicopter (Reality H). |
| **FlightSafety International** (Berkshire Hathaway) | Dominant in business aviation and regional; builds its own simulators (FS1000) and VITAL visual systems, and operates the largest business-aviation training network. |
| **Indra** (Spain) | Simulators and ATC systems; strong in Spain, Latin America and defence. |
| **Havelsan** (Turkey) | Growing civil and military simulator business; builds FFS for Turkish operators and exports. |
| **Frasca International** (US) | Long-established builder of FTDs, FNPTs and lower-level FFS, particularly for training academies and helicopters; now part of TruSim/Textron **[needs-verification]**. |
| **Redbird Flight Simulations** (US) | AATD/BATD-class devices with motion at a fraction of FFS cost, aimed at flight schools; changed the economics of the light end. |
| **Others** | Multi Pilot Simulations (MPS, Netherlands) — fixed-base 737/A320 FTDs that punch far above their price; Simcom, Alsim, Entrol, Axis Flight Training Systems (Austria), Precision Flight Controls, VRM Switzerland (VR-based helicopter FSTD, the first VR device to achieve EASA qualification). |

Economics: a new Level D FFS for a large transport aircraft is commonly quoted at **US$10–18 million** for the device, plus a purpose-built building with a pit or a raised floor and about 8–10 m of ceiling height, plus the OEM data package licence — which is itself a substantial and recurring cost. Operating economics are driven by **utilisation**: a simulator must be sold in slots close to 20 hours a day to earn its capital back, which is why the training centres cluster them and sell dry-lease hours to third parties. Typical wet hourly rates for a Level D airliner FFS are in the **US$500–1,200/hour** range depending on type, location and whether instruction is included `[indicative]`.

## 11. The desktop and light end, honestly

### X-Plane

Uses **blade-element theory**: the airframe is decomposed into elements, each element's local flow conditions are computed each frame, a 2-D aerofoil section coefficient is looked up, and forces are integrated. The consequence is that X-Plane produces credible behaviour for an arbitrary geometry drawn in **Plane Maker** with no flight-test data — including at high angles of attack, in ground effect, and for unconventional configurations. It has been used for genuine engineering work and NASA has used it for concept evaluation.

Its limits, stated plainly: blade-element theory with 2-D section data does not capture 3-D effects (spanwise flow, tip vortices, wing-body interference, transonic effects) except through fudge factors; the accuracy of a given aircraft model depends overwhelmingly on how carefully the third-party author built and tuned it; and the result is *plausible*, not *validated*. **X-Plane 12.4.1 was released 26 March 2026**, and a professional version of X-Plane 12 is FAA-approved as the basis of certain training devices. Laminar Research sells **X-Plane Professional** with a certification path for FAA AATD/BATD and, through partners, for higher-level FNPT and FTD devices.

### Microsoft Flight Simulator 2024

Released **19 November 2024** for Windows and Xbox Series X/S, with PlayStation 5 on 8 December 2025 and PSVR2 support planned for April 2026. Architecturally its distinguishing feature is **streaming**: the world is not installed but assembled at runtime from cloud services — Bing Maps imagery, photogrammetry meshes for a growing list of cities, elevation data, and AI-generated or procedurally-enhanced scenery — combined with live weather from a meteorological provider and live air and marine traffic. MSFS 2024 extended this from scenery to aircraft and mission content, which is why its offline capability is limited and its launch was disrupted by server capacity.

The 2024 release added an improved physics engine giving third-party developers more control over flight dynamics, better electrical, pneumatic, fuel and hydraulic system simulation, an in-sim EFB, and multithreading. It remains a **table-lookup plus corrections** flight model at its core rather than a blade-element one, though the fidelity of the best third-party add-ons (PMDG, Fenix, iniBuilds) for systems and FMS behaviour is genuinely close to a fixed-base FTD for procedural purposes.

**Prepar3D** (Lockheed Martin) is the professional continuation of the FSX codebase, licensed for training and simulation use (its EULA specifically permits professional use, which the consumer Microsoft products historically did not), and is the basis of a large number of low-cost procedural trainers. **DCS World** (Eagle Dynamics) is the high-fidelity military end of the consumer market: professional-grade systems modelling of specific combat types, with a professional variant sold for actual military training.

### The FAA's light categories

- **BATD — Basic Aviation Training Device.** Approved under a Letter of Authorization issued to the manufacturer. Credit: up to **10 hours** toward the instrument rating; instrument currency tasks with an instructor present.
- **AATD — Advanced Aviation Training Device.** More capable, with a control layout and instrument set closer to the aircraft. Credit: up to **20 hours** toward the instrument rating, **50 hours** toward the commercial certificate, and instrument experience.
- The current authority is **AC 61-136B** and the associated deviation memos; the credits have been adjusted several times, most recently in connection with the FAA's 2024–2025 rulemaking on simulator credit **[needs-verification]**.

Redbird's motion AATDs, Frasca's devices, Precision Flight Controls, and a number of X-Plane-based systems occupy this space. The honest position: a well-built AATD is transformative for instrument procedure training and worthless for handling training, because the control feel is a spring and the visual is a monitor.

**EASA equivalents**: **BITD** (Basic Instrument Training Device) and **FNPT I/II**, which occupy roughly the same niche but with a formal qualification rather than an LoA.

## 12. How you would actually build one

### Software architecture

A workable architecture for a serious simulator, whether a research rig or a commercial FTD:

```
┌───────────────────────────────────────────────────────────┐
│  Instructor Operating Station (soft real-time, 10–20 Hz)  │
└──────────────────────────┬────────────────────────────────┘
                           │  command/state (TCP or DDS)
┌──────────────────────────▼────────────────────────────────┐
│  HOST  (hard real-time, fixed 60–120 Hz frame)            │
│                                                            │
│   Scheduler  ──►  Atmosphere ──► Aerodynamics ──►          │
│                   Propulsion ──► Gear/Ground  ──►          │
│                   Mass properties ──► EOM integrator ──►   │
│                   Systems models ──► Failure manager       │
│                                                            │
│   Shared-memory blackboard: one struct, double-buffered    │
└───┬──────────────┬───────────────┬─────────────┬──────────┘
    │ reflective   │ 1–2 kHz       │ 500 Hz–1kHz │ 60 Hz
┌───▼────────┐ ┌───▼──────────┐ ┌──▼─────────┐ ┌─▼─────────┐
│ Avionics   │ │ Control      │ │ Motion     │ │ Image     │
│ rehost /   │ │ loading      │ │ cueing +   │ │ Generator │
│ stimulation│ │ servo loop   │ │ hexapod    │ │ cluster   │
└────────────┘ └──────────────┘ └────────────┘ └───────────┘
                                       │
                                 ┌─────▼──────┐
                                 │  Sound     │
                                 └────────────┘
```

Principles:
1. **One authoritative state**, published once per frame, consumed by everyone. Never let two subsystems integrate their own copy of position.
2. **Fixed-step integration** with the step chosen for numerical stability of the stiffest mode (usually the control loading or the gear).
3. **Rate groups** — not everything needs 120 Hz. Systems at 30 Hz, IOS at 10 Hz.
4. **Deterministic messaging** — reflective memory or a time-triggered network; no TCP in the hard loop.
5. **Everything data-driven** — the aircraft is a set of configuration files, not compiled code, so a new type is data work rather than a rewrite. This is JSBSim's central design decision and it is the right one.
6. **Record everything** for debrief and for QTG comparison; a test harness that can replay a recorded flight-test input into the model and plot the delta against the reference data is the single most valuable tool you will build.

### Open-source components

| Project | What it gives you | Licence |
|---|---|---|
| **JSBSim** | A mature, data-driven flight dynamics model in C++ with an XML aircraft definition covering mass balance, ground reactions, propulsion, aerodynamics, buoyancy, external and atmospheric forces. Runs at 120 Hz by default, decoupled from rendering. FlightGear's default FDM since 1999; NASA used it in 2015 as one of seven reference codes for 6-DoF verification benchmarks in atmospheric and orbital flight; used for non-terrestrial atmospheres including Mars. Embeddable as a library, scriptable, and interfaceable with MATLAB/Simulink. | LGPL |
| **FlightGear** | A complete open simulator: scenery, multiplayer, ATC, instruments, and a choice of FDMs. Useful as an integration testbed and as a visual system for a low-cost rig. | GPL |
| **YASim** | FlightGear's alternative FDM: a geometry-and-blade-element approach in the X-Plane spirit, where you describe the aircraft's shape and it derives the aerodynamics. Easier to author than JSBSim from scratch; less controllable. | GPL |
| **OpenEaagles / Mixed Reality Simulation Platform (MIXR)** | A C++ simulation framework from the US military simulation community for building distributed simulations — entities, networks (DIS/HLA), sensors, and a component architecture. Heavier and more military-oriented than JSBSim. | Open |
| **OpenSceneGraph / osgEarth** | Scene graph and geospatial terrain rendering; the historical basis of many low-cost IGs. | LGPL-style |
| **Godot / Unreal Engine / Unity** | Modern rendering. Unreal is used in CAE's Prodigy IG. Determinism must be enforced by you; game engines are not real-time systems by default. | Various |
| **OpenGeoFiction / OSM / Copernicus DEM / Natural Earth** | Free source data for terrain and culture. | Open data |
| **X-Plane SDK / MSFS SimConnect / Prepar3D SDK** | If you are building a trainer on a commercial simulator, these are the integration points for external hardware, and are how most low-cost FTDs are built. | Proprietary |

### Hardware

For a serious fixed-base FTD or an FNPT-class device:

- **Cockpit shell** — either a fibreglass/aluminium replica or a repurposed real airframe section. Panel accuracy matters for qualification: switch position, shape, force and travel are all checked.
- **Instruments and displays** — for a glass-cockpit type, LCD panels behind a bezel with the correct dimensions and with the real display software rehosted; for a steam-gauge type, either real instruments driven by servos or high-DPI displays behind glass.
- **Control loading** — for a light device, spring-and-damper with a proper feel unit is acceptable; for anything above FNPT II, electric servo loading is required. Commercial units: Wittenstein, Brunner (the CLS-E series is the standard for low-cost professional loading), Moog, and the OEM-integrated systems in FFS.
- **Motion** — for a light device, a 2- or 3-DoF platform (Motion Systems, D-BOX, Brunner) gives useful onset cueing at a fraction of hexapod cost. For a hexapod: E2M Technologies, Bosch Rexroth, Moog, or an FFS manufacturer's platform. Budget six figures minimum, and remember the building.
- **Visual** — three to five projectors on a curved screen, warped and blended (Immersive Display, Scalable Display Technologies, or the IG's own tools); or a direct-view LED wall; or, at the low end, a VR headset — VRM Switzerland demonstrated that a VR-based device can achieve formal EASA qualification for helicopters, which is a real precedent.
- **Compute** — a Linux host with PREEMPT_RT on isolated cores for the model, one GPU node per projector channel, a microcontroller or industrial PC per I/O concentrator.
- **I/O** — the unglamorous majority of the work. Hundreds of switches, annunciators, encoders and analogue inputs, aggregated over CAN or Ethernet to the host. Commercial concentrators exist (Phidgets, OpenCockpits, Arduino/Teensy-based, or industrial PLC I/O); wiring, labelling and testing them is where the schedule goes.

### The order of work

1. Get the **equations of motion and the integrator** right and validate them against a known reference (JSBSim's own regression suite, or an analytical case).
2. Build the **aerodynamic model** from whatever data you have, and build the **comparison harness** at the same time.
3. Add **propulsion**, then **gear and ground handling** — expect the ground model to take as long as everything before it.
4. Add **systems** in order of training value: electrics, hydraulics, fuel, pneumatics, flight controls, then the avionics.
5. Add the **visual**, then **sound**, then **motion**. Motion last, always, because you cannot tune motion against a flight model you do not trust.
6. Build the **IOS** early enough that you can actually set up test conditions, but expect to rewrite it.
7. **Latency budget** from day one. Measure it, do not estimate it.

## Sources

- [eCFR — 14 CFR Part 60, Flight Simulation Training Device Initial and Continuing Qualification and Use](https://www.ecfr.gov/current/title-14/chapter-I/subchapter-D/part-60)
- [EASA — CS-FSTD(A) Issue 2](https://www.easa.europa.eu/en/document-library/certification-specifications/cs-fstda-issue-2)
- [Wikipedia — Flight simulator](https://en.wikipedia.org/wiki/Flight_simulator)
- [Wikipedia — Stewart platform](https://en.wikipedia.org/wiki/Stewart_platform)
- [Wikipedia — JSBSim](https://en.wikipedia.org/wiki/JSBSim)
- [Wikipedia — X-Plane (simulator)](https://en.wikipedia.org/wiki/X-Plane_(simulator))
- [Wikipedia — Microsoft Flight Simulator 2024](https://en.wikipedia.org/wiki/Microsoft_Flight_Simulator_2024)

## Open questions

- **Exact QTG tolerance values** in the table are representative figures from working knowledge of the Part 60 Appendix A Attachment 1 structure; the authoritative numbers must be read from the current Part 60 appendix or CS-FSTD(A) table before use in any real qualification work.
- **CAE 70% / L3 20% market shares** are as reported by the cited Wikipedia article and carry no date; treat as indicative only.
- **FFS capital and hourly costs** are marked `[indicative]` and are from general industry knowledge, not a source.
- **ICAO Doc 9625 Edition 4 feature list** is summarised from working knowledge of the Type I–VII framework; the document itself is paywalled and was not fetched.
- **Frasca's current ownership** and **the current FAA AATD/BATD credit limits** need verification against AC 61-136 and the FAA's current policy.
- **Motion transfer-of-training research** — the claim that Level D motion shows limited transfer benefit reflects a body of published work (Bürki-Cohen and colleagues at the Volpe Center in particular) that is not cited here and should be read directly.
- **ARINC 610** revision level and its exact list of required simulation-support features were not verified against the current specification.
