---
id: aviation_industry.operations
title: Airline operations — planning, scheduling and running the day
domain: 31_aviation_industry
tags: [network-planning, slots, crew-rostering, pairing, preferential-bidding, disruption-management, mel, cdl, flight-planning, fuel-policy, weight-and-balance, occ, turnaround, maintenance-planning, sms]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Commission Implementing Regulation (EU) 2021/1296", url: "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32021R1296", publisher: "EUR-Lex", accessed: 2026-08-25}
  - {title: "Easy Access Rules for Air Operations (Revision 24, March 2026)", url: "https://www.easa.europa.eu/en/document-library/easy-access-rules/easy-access-rules-air-operations", publisher: "EASA", accessed: 2026-08-25}
  - {title: "Convention on International Civil Aviation", url: "https://en.wikipedia.org/wiki/Convention_on_International_Civil_Aviation", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "IATA, CANSO and ACI Launch Joint Runway Safety Initiative", url: "https://www.iata.org/en/pressroom/2026-releases/07-28-iata-canso-aci-launch-joint-runway-safety-initiative/", publisher: "IATA", accessed: 2026-08-25}
related: [aviation_industry.economics, aviation_industry.safety, aviation_industry.software]
unit_system: SI
---

# Airline operations — planning, scheduling and running the day

**Summary.** An airline operation is a very large constrained-optimisation problem executed in real time by people, with a planning horizon that runs from five years out (fleet) to five minutes out (a gate change). The sequence — network → schedule → fleet assignment → aircraft routing → crew pairing → crew rostering → day-of-operation → recovery — is solved as a chain of sub-problems because the joint problem is computationally intractable, and almost every operational failure traces back to a seam between two of those sub-problems. This file covers each stage, plus the regulatory scaffolding around dispatch, fuel, mass and balance, maintenance planning and safety management.

## Key facts

| Item | Detail |
|---|---|
| EASA fuel/energy rules | Commission Implementing Regulation (EU) 2021/1296, amending (EU) No 965/2012; applicable from **30 October 2022** |
| Slot coordination levels | Level 1 (non-coordinated), Level 2 (schedules facilitated), Level 3 (fully coordinated) |
| Slot use rule (EU Reg 95/93) | 80/20 "use it or lose it" in a scheduling season |
| IATA scheduling seasons | Northern Summer (last Sunday in March → last Saturday in October); Northern Winter (the remainder) |
| Slot conferences | IATA Slot Conference (SC), twice a year, ~six months before each season |
| Typical narrowbody turnaround | 25–40 min LCC, 45–60 min network carrier |
| A-check interval (modern types) | ~600–1,000 FH or a calendar equivalent |
| C-check interval | ~18–30 months / 6,000–7,500 FH depending on type and programme |
| SMS pillars | Safety policy and objectives; safety risk management; safety assurance; safety promotion (ICAO Annex 19 / Doc 9859) |

## 1. Network planning and scheduling

### Network planning

The commercial question: which markets, at what frequency, with what aircraft, at what time of day, at what fare, against which competitors. Inputs:

- **O&D demand data** — MIDT (Marketing Information Data Tapes) from the GDSs, IATA's **DDS/PaxIS** (BSP-derived ticketing data), government survey data (US DB1B/T-100, UK CAA survey), and increasingly booking-data consortia (Cirium, ForwardKeys).
- **QSI / market share models** — Quality of Service Index. Assigns each itinerary in a market a score based on service type (nonstop > 1-stop > 2-stop), elapsed time, departure time, aircraft type and carrier preference; share of market ≈ share of QSI. Combined with an S-curve for frequency share: at low frequency share you get less than proportional traffic share; above about 50% you get more. This asymmetry is why dominant carriers at a hub can defend it.
- **Profitability model** — allocating network revenue to a route requires deciding how to credit connecting revenue. Fully-allocated route profitability is misleading (it charges a route with fixed overhead it did not cause); marginal/incremental profitability is what should drive add/drop decisions but is much harder to compute honestly.
- **Constraints** — slots, bilateral rights, curfews, aircraft range/payload at the actual field elevation and temperature, crew bases, maintenance base access, ETOPS/EDTO approvals, overflight permissions.

**Route decision economics.** A new route is evaluated on ramp-up: typically 12–36 months to mature, with the first season loss-making. Airlines de-risk with incentives from airports and tourism authorities (waived landing fees, marketing support), which is a real and rarely disclosed revenue line for thin routes.

### Schedule construction

1. **Schedule design** — the flight-leg list with times, built to hit bank structures at hubs, aircraft rotations that close, and market-competitive departure times.
2. **Fleet assignment** — assign a fleet type to each leg to maximise contribution (revenue minus type-specific cost), subject to count of aircraft available, and to balance (aircraft in = aircraft out at each station overnight). This is a large multi-commodity network flow problem; the classical formulation is Hane et al. (1995).
3. **Aircraft routing / tail assignment** — string legs into rotations for individual airframes, respecting maintenance opportunities (the aircraft must reach a maintenance station at the right intervals), and — for reliability — building in "slack" where recovery would otherwise be impossible. **Through-flights** (same aircraft, same flight number, no change of gate) are commercially valuable and constrain routing.
4. **Crew pairing** — see below.
5. **Crew rostering** — see below.

The whole chain is usually run 6–12 months before operation, then re-run as the schedule changes.

## 2. Slots

At a **Level 3 coordinated** airport, a movement cannot be scheduled without a slot: a permission to use the full range of airport infrastructure at a specific date and time. Slots are allocated by an independent coordinator (ACL in the UK, Airport Coordination Germany, COHOR in France, and equivalents worldwide) under the **IATA Worldwide Airport Slot Guidelines (WASG)**, jointly maintained by IATA, ACI and the Worldwide Airport Coordinators Group, and in the EU under **Council Regulation (EEC) No 95/93** as amended.

The mechanics:

- **Historic precedence ("grandfather rights")** — a carrier that operated a series of slots for at least 80% of the times allocated in the equivalent previous season is entitled to the same series next season. This is the **80/20 rule**. Failure means the slot returns to the pool.
- **The pool** — returned, newly created and unused slots. **50% of pool slots go to new entrants** in the EU regime.
- **Series of slots** — at least five slots requested for the same time on the same day of the week over consecutive weeks.
- **Slot conferences** — held twice a year, roughly six months before each season, where coordinators and airlines negotiate face-to-face. Initial Submission Deadline (SAL), Initial Coordination, then the conference, then Historic Baseline Date.
- **Secondary trading** — legal and active at UK airports since the *Guernsey Transport Board* case; the EU's position was ambiguous for years and slot swaps for consideration now occur widely. Prices are not published.
- **COVID waivers** — the 80/20 rule was suspended and then progressively restored between 2020 and 2023.

Distinguish **airport slots** from **ATFM slots (CTOTs)**: the latter are tactical calculated take-off times issued by the network manager (EUROCONTROL NM in Europe) to meet en-route or destination capacity constraints on the day, with a −5/+10 minute tolerance window. They have nothing to do with the seasonal allocation.

## 3. Crew planning and rostering

The largest and most politically charged optimisation problem an airline runs.

### Pairing (trip) construction

A **pairing** (US: *trip*; Europe: often *pattern*) is a sequence of duty periods starting and ending at a crew base. Building them is a set-partitioning problem: cover every flight leg exactly once with a legal, minimum-cost set of pairings.

Legality constraints come from:

- **Flight and duty time limitations (FTL)** — EASA **ORO.FTL** (Subpart FTL of Part-ORO) in Europe; **14 CFR Part 117** for US Part 121 passenger operations; national rules elsewhere (Qatar applies QCAR-OPS derived limits). Typical elements: maximum daily Flight Duty Period as a function of report time and number of sectors; cumulative limits (e.g. 100 hours flight time in 28 days, 900 or 1,000 in 12 months); minimum rest, extended rest, and recovery rest; limits on consecutive night duties and on early starts; standby rules; and rules for augmented crew and in-flight rest facility classes.
- **Collective labour agreements**, which are frequently more restrictive than the regulation and are where the real cost sits.
- **Qualifications** — type, licence privileges, route/airport competence (Cat B/C aerodromes), low-visibility qualification, ETOPS, recency (three take-offs and landings in 90 days).

Cost drivers of a pairing: **credit hours** (what the crew is paid) versus **block hours** (what is flown) — the ratio is the *pay-to-block* or *credit-to-block* ratio; hotel and per diem cost; deadheading (positioning as a passenger); and time-away-from-base.

Solution method: column generation over a very large set of candidate pairings, with a constrained shortest-path pricing subproblem on a duty network. Commercial solvers: Jeppesen (Boeing) Crew Pairing, Sabre AirCentre, IBS iFlight, Lufthansa Systems NetLine/Crew, AIMS.

### Rostering

Assigning pairings, training, standby, office duty and leave to individuals for a month. Two philosophies:

- **Bidline** (mostly North America, legacy union structures) — the company builds anonymous *lines of time* from the pairings; crew bid for whole lines in seniority order; the most senior gets the line they want. Simple, transparent, and produces poor overall utilisation.
- **Preferential Bidding System (PBS)** — crew express weighted preferences (specific days off, trip types, layovers, avoid-pairings, partner requests), and an optimiser constructs individual rosters honouring preferences in seniority order subject to full legality and coverage. Used widely in Europe, at many Gulf and Asian carriers, and increasingly in North America. Systems: **AIMS**, **Jeppesen Crew Rostering**, **Sabre CrewPlan/CrewTrac**, **NAVBLUE N-Rostering**, **Hitit**, **PBS by Trip Trade**.
- **Fixed-pattern rostering** — some short-haul operators build repeating patterns (e.g. 5 on / 4 off) which crews find predictable and which simplify the problem enormously.

The optimisation objective is usually a weighted combination of: cover all duties, minimise open time (unassigned trips), minimise premium pay, maximise preference satisfaction, honour seniority ordering, and respect fatigue-mitigation rules. A roster that is legal but fatiguing is the standard failure; **Fatigue Risk Management Systems (FRMS)** exist to catch it (see `09`).

### Day-of-operation crew control

Crew control (crew tracking) handles sickness, delays that break legality, and disruption. Tools: standby crew (airport standby vs home standby), reserve pools, discretion (commander's discretion to extend an FDP within defined limits, which must be reported), and — expensively — deadheading crews or cancelling.

## 4. Disruption management and recovery

When the plan breaks, the airline must re-solve aircraft routing, crew assignment and passenger itineraries simultaneously, under time pressure, with incomplete information. Practically it is decomposed:

1. **Schedule recovery** — decide which flights to delay, cancel, swap aircraft on, or ferry. Objective: minimise total cost = passenger disruption cost + crew cost + EU261/DOT liability + downstream propagation + curfew and slot penalties.
2. **Aircraft recovery** — tail swaps, subject to maintenance due dates, ETOPS status, cabin configuration and range.
3. **Crew recovery** — the binding constraint more often than aircraft, because legality is discrete: a crew is either legal or it is not.
4. **Passenger re-accommodation** — rebooking, prioritised by connection value, status, and onward liability. Systems: Amadeus Altéa Disruption Management, Sabre, 15below and similar for notification.

**Propagation** is the core phenomenon: a delay on the first sector of a rotation cascades through the day. The mitigating levers are **schedule padding** (block time buffers), **slack in rotations**, **spare aircraft** and **crew reserves** — all of which cost money in normal operation and save money in disruption. The right amount of buffer is an economic question that most airlines answer badly, usually by adding block time until on-time performance targets are met, which inflates cost and hides the underlying reliability problem.

**Recovery hierarchy** in practice: protect the long-haul departures (highest revenue, hardest to recover, curfew-constrained), protect the last wave of the day (a cancellation there strands crews and aircraft out of position overnight), and cancel in pairs to preserve rotations rather than singly.

## 5. The Operations Control Centre (OCC)

Typical structure — names vary, functions do not:

| Desk | Responsibility |
|---|---|
| **Duty Operations Manager / OCC Manager** | Single accountable decision-maker on the day; delay/cancel authority |
| **Flight dispatch / flight operations officers** | Flight planning, fuel, NOTAM and weather assessment, operational control of assigned flights, in-flight monitoring |
| **Aircraft / fleet controllers** | Tail assignment, swaps, ferry flights |
| **Crew control** | Crew legality, replacements, hotels |
| **Maintenance control (MCC)** | AOG management, deferrals under MEL, technical decisions in real time |
| **Network / ATFM desk** | Slot management, CTOT negotiation with the network manager |
| **Customer/passenger recovery** | Rebooking, communications, welfare |
| **Cargo control** | Load, priority, offload decisions |
| **Emergency Response Coordinator** | Activates the Emergency Response Plan |

Two legal models of **operational control**:

- **Shared/joint dispatch (FAA Part 121 flag and domestic)** — the licensed **aircraft dispatcher** and the pilot-in-command *jointly* exercise operational control; both must agree to release the flight, and the dispatcher can (and must) initiate diversion or cancellation. The dispatcher holds an FAA certificate and has legal responsibility.
- **Commander-centred with operational control by the operator (EASA)** — the operator exercises operational control; the commander is responsible for the safe conduct of the flight. The flight operations officer/flight dispatcher role is defined but not licensed in the FAA sense, although EASA requires training where the operator uses one (ORO.GEN and the associated AMC).

The practical difference matters when things go wrong: under the FAA model there is a second licensed professional on the ground who must concur.

## 6. Dispatch: MEL and CDL

**Master Minimum Equipment List (MMEL)** — produced by the manufacturer and approved by the State of Design's authority (an FAA Flight Operations Evaluation Board or EASA Operational Suitability Data process). It lists items that may be inoperative and under what conditions.

**Minimum Equipment List (MEL)** — the operator's own document, derived from the MMEL, never less restrictive, approved by the operator's authority. It contains, per item:

- **Rectification interval categories**: **A** (as specified in the remarks — often a number of flights or days), **B** (3 consecutive calendar days), **C** (10 days), **D** (120 days), with day zero being the day of discovery.
- **(O)** operational procedures and **(M)** maintenance procedures that must be carried out to use the relief.
- Number installed / number required for dispatch.

**Configuration Deviation List (CDL)** — a section of the AFM listing *secondary airframe and engine parts* that may be missing (a fairing, a panel, a seal) with the associated performance penalty and any operational limitation. Unlike the MEL, the CDL is part of the AFM.

**Dispatch Deviation Guide (DDG)** — Boeing's combined MMEL/CDL guidance document; Airbus's equivalent is the MEL/CDL within the operator's documentation set plus the Trouble Shooting Manual.

Operationally: an item goes into the **Technical Log** (Tech Log), maintenance control assesses it, either rectifies or raises a deferred defect under the MEL with a rectification interval, applies the (O) and (M) procedures, and the crew is informed via the Tech Log and any performance penalty in the loadsheet. Interval extensions are possible for category B, C and D with authority approval — a common area of regulatory finding.

## 7. Flight planning and fuel policy

### The flight plan

A computerised flight plan (CFP/OFP) is produced by a flight planning system (Lido/Flight from Lufthansa Systems, Jeppesen JetPlan/JetPlanner, NAVBLUE Flight Planning, PACE/Sabre, ARINC/Collins) and contains: the route (with ATS route segments, waypoints, FIR boundaries and overflight charges), the vertical profile with step climbs, forecast winds and temperatures aloft interpolated from GRIB data (usually a global model such as the NOAA GFS or ECMWF), fuel at each waypoint, alternates and their fuel, ETOPS/EDTO entry and exit points and equal-time points, and the mass at each stage.

**Cost Index (CI)** ties speed to economics: CI = (time-related cost per hour) / (fuel cost per unit mass). CI = 0 gives maximum range cruise (minimum fuel); a high CI gives maximum speed. A typical long-haul CI is a small number (single to low double digits on Boeing's scale; Airbus uses kg/min); airlines raise it to recover delay and lower it when fuel is expensive.

Route optimisation is a shortest-path problem over a 4-D wind field with constraints (airspace availability, RVSM, PBN capability, overflight cost, conflict zones). Free Route Airspace in Europe and the flexible tracks over the North Atlantic (OTS) and the Pacific change the shape of that problem.

### Fuel policy — EASA

**Commission Implementing Regulation (EU) 2021/1296**, amending Regulation (EU) No 965/2012, restructured fuel planning and management with effect from **30 October 2022**. It introduced a performance-based framework with three **fuel/energy schemes**:

1. **Basic fuel scheme** — the traditional, conservative scheme available to any operator without special approval.
2. **Basic fuel scheme with variations** — allows defined reductions (e.g. reduced contingency fuel, use of the *Reduced Contingency Fuel* / RCF and *Pre-determined Point* procedures, isolated aerodrome procedure, and dispatch without a destination alternate under specified conditions) subject to the operator meeting additional conditions and, for some variations, a specific approval.
3. **Individual fuel scheme** — a fully performance-based scheme requiring specific approval, in which the operator uses its own validated statistical model and a safety risk assessment to determine fuel, supported by a robust fuel monitoring programme.

The fuel categories themselves:

| Category | Purpose |
|---|---|
| **Taxi fuel** | Ground operation before take-off; based on local conditions and APU use |
| **Trip fuel** | Departure to destination via the planned profile |
| **Contingency fuel** | Unforeseen deviations — typically 5% of trip fuel, or 3% with an en-route alternate, or a statistical value under an approved scheme, with a floor of 5 minutes' holding at 1,500 ft above destination in ISA |
| **Destination alternate fuel** | Missed approach at destination, climb, cruise, descent and approach at the alternate |
| **Final reserve fuel** | 30 minutes' holding at 1,500 ft in ISA at estimated arrival mass (turbine, non-augmented); 45 minutes for piston |
| **Additional fuel** | Where required by the isolated aerodrome procedure or by a critical-scenario analysis (e.g. engine failure or depressurisation at the most critical point) |
| **Discretionary / extra fuel** | At the commander's discretion |

**Statistical contingency fuel (SCF)** is the key modernisation: instead of a flat 5%, the operator computes the contingency for a given city pair and season from the historical distribution of actual trip fuel burn versus planned, and carries the fuel needed to cover, say, the 95th or 99th percentile. It typically reduces carried fuel materially on routes with stable performance, which reduces the fuel burned to carry fuel (roughly 2–4% of the extra mass per hour of flight, type-dependent). It requires a demonstrated data set, a monitoring programme and — for the individual scheme — approval.

**In-flight fuel management** is a separate legal obligation: the commander must continuously monitor, and must declare **MINIMUM FUEL** when committed to a specific aerodrome and any change would result in landing with less than final reserve, and **MAYDAY MAYDAY MAYDAY FUEL** when calculated usable fuel on landing at the nearest suitable aerodrome would be below final reserve. The terminology was harmonised by ICAO in 2012 after a series of fuel-emergency accidents (Avianca 052 being the canonical case).

**FAA equivalent**: 14 CFR 121.639/121.645 (domestic: destination + alternate + 45 min; flag: destination + alternate + 10% of total flight time + 30 min, with variations), a rule set that is structurally different and generally less flexible than the EASA performance-based scheme.

## 8. Mass and balance

Each flight requires a **loadsheet** establishing that the aircraft is within its certified mass and centre-of-gravity envelope for taxi, take-off, en route, landing and zero fuel.

Elements: Dry Operating Mass (DOM, including crew, catering and unusable fluids), traffic load (passengers, baggage, cargo, mail), zero fuel mass (ZFM ≤ MZFM), take-off mass (TOM ≤ the most limiting of MTOM, structural, performance-limited take-off mass and en-route/landing limits), landing mass (LM ≤ MLM), and the CG expressed as **%MAC**.

**Passenger and baggage masses** may be standard (EASA's standard masses by category and flight type, revalidated by periodic weighing surveys) or actual. EASA and the FAA have both revised standard masses upward over the last two decades. Discrepancies here have caused accidents and serious incidents; the loadsheet is a safety document, not an administrative one.

**Last Minute Changes (LMC)** are permitted within limits stated in the Operations Manual; beyond them the loadsheet must be re-issued.

**Trim** matters for performance: a more aft CG reduces trim drag and the required stabiliser setting, improving fuel burn, which is why several airlines actively manage CG towards the aft limit within safe margins.

Systems: departure control systems (Amadeus Altéa DC, SITA DCS, Sabre) generate the loadsheet; EFB applications (Airbus FlySmart, Boeing OPT, NAVBLUE) compute performance.

## 9. Ground handling and the turnaround

The turnaround is a critical-path problem executed in 25–60 minutes:

Chocks on → doors open → disembark → cabin clean → catering → refuel (often concurrent with boarding, requiring specific procedures and a fire crew standby in some States) → baggage offload/onload → cargo → potable water and lavatory service → boarding → doors close → pushback.

Critical path is usually **deplane → clean → board** for LCCs and **baggage/cargo** or **catering** for network carriers. The LCC advantage comes from eliminating steps (no catering uplift, no seat assignment queueing, single-class cabin, no interline bags) rather than from doing them faster.

**A-CDM (Airport Collaborative Decision Making)** shares milestone data (TOBT — Target Off-Block Time; TSAT — Target Start-up Approval Time; TTOT) between airline, handler, airport and ATC to sequence departures and cut taxi queueing. It is standard at most large European airports and is the main mechanism by which the airline's ground process is coupled to ATFM.

Safety and cost: ground damage (jet bridges, belt loaders, catering trucks, pushback events) is one of the industry's largest self-inflicted cost lines, and IATA's **IGOM** (IATA Ground Operations Manual) and **ISAGO** audit programme exist to standardise it.

## 10. Maintenance planning

### Programme structure

The **Maintenance Review Board Report (MRBR)**, developed under **MSG-3** logic by an Industry Steering Committee with the OEM and the authorities, is the baseline. MSG-3 is a task-oriented, top-down analysis: for each significant item, ask what functional failures can occur, what their consequences are (evident/hidden × safety/operational/economic), and select a task (lubrication/servicing, operational check, functional check, inspection, restoration, discard) only if it is applicable and effective.

From the MRBR the operator builds an **Aircraft Maintenance Programme (AMP)** approved by its authority, adding: airworthiness directives, service bulletins it elects to embody, Certification Maintenance Requirements (CMRs), Airworthiness Limitation Items (ALIs, including fatigue-critical and, since the TWA 800 rulemaking, fuel tank system limitations — CDCCL), corrosion prevention and control, structural inspections, and the operator's own reliability-driven tasks.

### Checks

The traditional letter checks:

| Check | Traditional scope | Typical modern interval |
|---|---|---|
| **Transit / daily / pre-flight** | Walkaround, fluids, obvious damage | Every turnaround / 24–48 h |
| **A-check** | Detailed visual, lubrication, filter changes, functional checks | ~600–1,000 FH or 2–3 months (type-dependent) — often done overnight at the line station |
| **B-check** | Largely obsolete; absorbed into A-check packages | — |
| **C-check** | Extensive inspection, zonal and structural, aircraft out of service several days to two weeks | ~18–30 months / 6,000–7,500 FH |
| **D-check / heavy structural check** | Near-teardown; paint strip, structural inspection, systems overhaul, 3–8 weeks | ~6–12 years |

The letter-check model is being replaced. Modern programmes (787, A350, A220, and the later 737/A320 evolutions) use **equalised** or **packaged** maintenance: the MRBR tasks are grouped into small blocks that can be flown into short overnight opportunities, spreading the workload and avoiding long downtime. Instead of "C-check", the operator runs a rolling sequence of task packages against a common interval grid. The commercial effect is high availability and less variance, at the cost of more frequent, shorter ground events and more complex planning.

**Engines and components** are managed separately on their own life-limited part (LLP) cycles, shop visit intervals and on-condition monitoring, usually under a power-by-the-hour or total care agreement with the OEM.

### Reliability programmes

Required by the authority for operators using a controlled maintenance programme. The operator tracks: **technical dispatch reliability** (percentage of departures without a technical delay >15 min or cancellation — network carriers target >99%), **pilot reports (PIREPs) per 1,000 FH**, **component removal rates and MTBUR** (mean time between unscheduled removals), **in-flight shutdown rate** (an ETOPS gate), **delay and cancellation causes by ATA chapter**, and **repeat defects**. Alert levels are set statistically (usually mean + 2σ or 3σ over a rolling window); exceedance triggers an investigation and, potentially, an escalation or de-escalation of a task interval — which is how the AMP evolves.

**Aircraft health monitoring** feeds this in real time: ACARS-downlinked ACMS/DAR data, engine trend monitoring (EGT margin, fuel flow, vibration), Airbus AIRMAN and Boeing AHM, and increasingly OEM predictive services (Skywise, AnalytX). The commercial promise is converting unscheduled removals into scheduled ones.

## 11. Safety Management Systems

Required by **ICAO Annex 19** and implemented in the EU through Part-ORO.GEN.200 and the corresponding organisational requirements, and in the US through 14 CFR Part 5. Guidance is **ICAO Doc 9859, Safety Management Manual**.

The **four components (pillars)** and their twelve elements:

**1. Safety policy and objectives**
- Management commitment and responsibility
- Safety accountabilities (Accountable Manager, safety manager, safety action groups)
- Appointment of key safety personnel
- Coordination of emergency response planning
- SMS documentation

**2. Safety risk management**
- Hazard identification (reactive, proactive and predictive sources)
- Risk assessment and mitigation — the classic 5×5 severity/likelihood matrix, with a tolerability boundary and an ALARP region

**3. Safety assurance**
- Safety performance monitoring and measurement — **SPIs** (safety performance indicators) and **SPTs** (targets), against an agreed **Acceptable Level of Safety Performance (ALoSP)** in the State Safety Programme
- The management of change
- Continuous improvement of the SMS (internal audit)

**4. Safety promotion**
- Training and education
- Safety communication

The State side is the **State Safety Programme (SSP)**, with its own four components, under which the authority sets the ALoSP and oversees operators' SMS.

Data sources feeding hazard identification: mandatory and voluntary occurrence reports (Air Safety Reports), **FDM/FOQA** flight data, **LOSA** line observations, cabin and ground reports, maintenance reports, ATC reports, and audit findings (internal, IOSA, ISAGO, authority). See `09_safety-and-human-factors.md` for how these are analysed.

> ⚠️ An SMS without a functioning just culture produces no reports and therefore no hazards, and will look excellent on paper right up to the accident. Report volume is a leading indicator of SMS health; a falling report rate in a stable operation is a warning sign, not a success.

## Sources

- [EUR-Lex — Commission Implementing Regulation (EU) 2021/1296](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32021R1296)
- [EASA — Easy Access Rules for Air Operations (Revision 24, March 2026)](https://www.easa.europa.eu/en/document-library/easy-access-rules/easy-access-rules-air-operations)
- [IATA — IATA, CANSO and ACI Launch Joint Runway Safety Initiative (28 July 2026)](https://www.iata.org/en/pressroom/2026-releases/07-28-iata-canso-aci-launch-joint-runway-safety-initiative/)
- [Wikipedia — Convention on International Civil Aviation](https://en.wikipedia.org/wiki/Convention_on_International_Civil_Aviation)

## Open questions

- **Maintenance check intervals** in section 10 are typical ranges from general industry knowledge; the actual figures are type- and operator-specific and come from the approved AMP. Do not quote them as authoritative for any given fleet.
- **EASA fuel scheme detail** (the exact list of permitted variations under the "basic scheme with variations") is summarised from the regulation's structure and should be checked against the current Easy Access Rules for Air Operations text.
- **Slot secondary trading prices** and the current legal position on monetary slot transfers in the EU are unverified.
- **Turnaround time figures** are industry norms, not sourced.
- Technical dispatch reliability targets (>99%) are conventional industry practice, unsourced here.
