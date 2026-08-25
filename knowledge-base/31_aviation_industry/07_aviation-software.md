---
id: aviation_industry.software
title: The aviation software estate — onboard, airline, ATM, airport and data standards
domain: 31_aviation_industry
tags: [do-178c, arinc-653, rtos, fms, efb, acars, cpdlc, pss, amadeus, sabre, ndc, aims, jeppesen, lido, amos, trax, eurocontrol, eram, itec, ads-b, aireon, sesar, nextgen, arinc-424, aixm, fixm]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "DO-178C", url: "https://en.wikipedia.org/wiki/DO-178C", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "ARINC 653", url: "https://en.wikipedia.org/wiki/ARINC_653", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "New Distribution Capability (NDC)", url: "https://www.iata.org/en/programs/airline-distribution/retailing/ndc/", publisher: "IATA", accessed: 2026-08-25}
  - {title: "Aireon", url: "https://en.wikipedia.org/wiki/Aireon", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Single European Sky ATM Research", url: "https://en.wikipedia.org/wiki/Single_European_Sky_ATM_Research", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "ARINC 424", url: "https://en.wikipedia.org/wiki/ARINC_424", publisher: "Wikipedia", accessed: 2026-08-25}
related: [aviation_industry.operations, aviation_industry.simulation, aviation_industry.design_trends]
unit_system: SI
---

# The aviation software estate

**Summary.** Aviation software divides into four estates with almost nothing in common except the data that flows between them: safety-critical airborne software developed to DO-178C with objective counts that scale from 71 to 26 depending on design assurance level; airline commercial and operational systems built on 1960s-era reservation architectures that are still being migrated; air traffic management systems with 20–30 year lifecycles being modernised under SESAR and NextGen; and airport systems. Holding them together is a set of data standards — ARINC 424 for navigation databases, AIXM and FIXM for aeronautical and flight information, IATA's messaging and NDC for distribution — several of which are older than the people maintaining them.

## Key facts

| Item | Detail |
|---|---|
| DO-178C levels | A (catastrophic) → E (no effect); objective counts commonly cited as A:71, B:69, C:62, D:26, E:0 **[needs-verification]** |
| DO-178C supplements | DO-330 (tool qualification), DO-331 (model-based), DO-332 (object-oriented), DO-333 (formal methods) |
| Companion standards | DO-254 (airborne electronic hardware), ARP4754A/ED-79A (system development), ARP4761 (safety assessment), DO-326A/ED-202A (airworthiness security) |
| ARINC 653 | Time and space partitioning; APEX API; two-level scheduling with Major Time Frame and partition windows |
| ARINC 424 | 132-byte fixed-length records; first published May 1975; Supplement 22 July 2018; FAA CIFP publishes in ARINC 424-18 |
| AIRAC cycle | 28 days, common effective dates worldwide |
| NDC | IATA Resolution 787, October 2012; XML-based; latest generation **NDC 24.1** |
| Aireon space-based ADS-B | Hosted payloads on Iridium NEXT; first payloads January 2017; constellation complete and operational **January 2019**; 75 payloads (66 operational, 9 spares) |
| SESAR phases | Definition 2004–2008; Development 2008–2013 (€2.1 bn); Deployment 2014–2020; now SESAR 3 Joint Undertaking |

## 1. Onboard software

### DO-178C and design assurance levels

**RTCA DO-178C / EUROCAE ED-12C, *Software Considerations in Airborne Systems and Equipment Certification*** (2011, superseding DO-178B of 1992) is the means of compliance the FAA and EASA accept for airborne software. It is **not a development process**; it is a set of **objectives** with associated activities, evidence and, for higher levels, a requirement for **independence** between the person who did the work and the person who verified it.

The **software level** (Design Assurance Level, DAL) is assigned by the system safety assessment (ARP4761) from the severity of the failure condition the software could contribute to:

| Level | Failure condition | Consequence |
|---|---|---|
| **A** | Catastrophic | Loss of aircraft and/or multiple fatalities |
| **B** | Hazardous / Severe-major | Large reduction in safety margins, serious injury to a small number, higher crew workload such that they cannot be relied on to perform accurately |
| **C** | Major | Significant reduction in safety margins or functional capabilities, significant increase in crew workload, discomfort or minor injuries |
| **D** | Minor | Slight reduction in safety margins, slight increase in workload, inconvenience |
| **E** | No effect | No effect on operational capability or crew workload; **outside DO-178C's scope** |

What changes with level, in practice:

- **Structural coverage.** Level C requires **statement coverage**. Level B adds **decision coverage**. Level A adds **Modified Condition/Decision Coverage (MC/DC)** — for every condition in a decision, a pair of test cases must show that condition independently affecting the decision outcome. MC/DC is the single largest cost driver in Level A software and the reason avionics code is written with simple, shallow decision logic.
- **Data and control coupling analysis**, required at A, B and C.
- **Source-to-object code traceability**, required at Level A where the compiler generates object code not directly traceable to source.
- **Independence** of verification activities: extensive at A, reduced at B, minimal at C, essentially absent at D.
- **Robustness testing** — normal-range and abnormal-range test cases at all levels; the abnormal-range obligations grow with level.

The lifecycle data items: Plan for Software Aspects of Certification (**PSAC**), Software Development Plan, Verification Plan, Configuration Management Plan, Quality Assurance Plan, Requirements Standards, Design Standards, Code Standards, High-Level and Low-Level Requirements, Design Description, Source Code, Executable Object Code, Verification Cases and Procedures, Verification Results, Configuration Index, Accomplishment Summary (**SAS**), and the problem reports. The **Stage of Involvement (SOI) audits** — SOI-1 planning, SOI-2 development, SOI-3 verification, SOI-4 final — are how the authority or its designee checks compliance.

**The four supplements**, all published with DO-178C in 2011:

- **DO-330** — *Software Tool Qualification Considerations*. Split out because tool qualification applies beyond DO-178C (it is referenced by DO-254 and even by ISO 26262 in automotive). Tool Qualification Levels TQL-1 to TQL-5 depend on the tool's criteria (does it eliminate/reduce/automate a process?) and the software level.
- **DO-331** — *Model-Based Development and Verification*. Addresses Simulink/SCADE-style development where the model is the requirement or the design, and simulation is used for verification credit.
- **DO-332** — *Object-Oriented Technology and Related Techniques*. Deals with inheritance, polymorphism, dynamic dispatch, overloading, type conversion, exception management and — the hard one — memory management. The "vulnerabilities" annex is the useful part.
- **DO-333** — *Formal Methods*. Allows formal analysis (model checking, abstract interpretation, theorem proving) to *complement but not replace* testing. Airbus's use of Astrée and Caveat on A380/A350 flight control software is the flagship application.

**Related standards** an engineer will meet: **DO-254/ED-80** for complex airborne electronic hardware (FPGAs, ASICs); **ARP4754A/ED-79A** for development of civil aircraft and systems (the level above software, where DALs are allocated); **ARP4761/ED-135** for safety assessment (FHA, PSSA, SSA, FTA, FMEA, CCA); **DO-297** for Integrated Modular Avionics; **DO-326A/ED-202A, DO-355, DO-356A** for airworthiness security (cyber); and **DO-200B** for aeronautical data processing.

### RTOS and ARINC 653 partitioning

**Integrated Modular Avionics (IMA)** replaced the federated architecture — one box per function — with shared computing cabinets hosting many applications. That only works if applications cannot interfere with each other, which is what **ARINC 653** provides:

- **Space partitioning** — each partition has its own memory space, enforced by the MMU; a partition cannot read or write outside it.
- **Time partitioning** — a **two-level hierarchical scheduler**. The first level is a fixed, cyclic, round-robin schedule of **partition windows** repeating over a **Major Time Frame**; a partition gets its window whether it needs it or not, and cannot exceed it. The second level, within a partition window, is a preemptive priority-based scheduler over the partition's processes.
- **APEX (APplication EXecutive)** — the standardised API that decouples the application from the RTOS, with six service groups: partition management, process management, time management, inter-partition communication (sampling and queuing ports), intra-partition communication (buffers, blackboards, semaphores, events), and error handling. Every call returns a status code (NO_ERROR, INVALID_PARAM, TIMED_OUT, …).
- **Health monitoring** — a hierarchy of error handlers at process, partition and module level. The partition's **error handler process** is a preemptive, highest-priority process created at initialisation that can stop a faulty process or collect the exception information.

Certified ARINC 653 RTOS implementations in production: **Wind River VxWorks 653**, **Green Hills INTEGRITY-178 tuMP**, **SYSGO PikeOS**, **DDC-I Deos**, **Lynx LynxOS-178**, and open/research implementations such as XtratuM and the ESA-funded work. All ship with DO-178C certification evidence packages up to Level A, which is what you are actually buying.

The IMA platforms themselves: Airbus's **IMA** on A380/A350 (with the **AFDX/ARINC 664 Part 7** deterministic switched Ethernet backbone), Boeing's **Common Core System** on the 787 (Collins-supplied), and the equivalents on the 777X and the Embraer E2.

### The Flight Management System

The FMS is the most complex piece of airborne software the crew interacts with. Functionally it comprises:

- **Navigation** — sensor fusion of IRS, GPS/GNSS, DME/DME, VOR/DME and (increasingly) SBAS, into a best-estimate of position with an associated accuracy figure (ANP/EPU) compared against the RNP for the phase of flight.
- **Flight planning** — route construction from the navigation database, SIDs, STARs, approaches, holds, offsets, direct-to, and the "path and terminator" leg construction described below.
- **Performance** — takeoff and landing performance, cruise optimisation (optimum and maximum altitude, step climb points), speed schedule from the **Cost Index**, fuel prediction, ETA prediction, and the descent path computation (the idle path back from the constraint set, which is where FMSs differ most in behaviour).
- **Guidance** — lateral (LNAV) and vertical (VNAV) commands to the autopilot/flight director.
- **Datalink** — CPDLC and AOC message handling on some architectures.

Suppliers: **Honeywell** (Pegasus and the NG FMS on Boeing and business jets), **Collins Aerospace** (FMS-4200/6000, Pro Line), **Thales** (the A350 and A320 FMS), **GE Aerospace/Universal Avionics**. The A320/A330/A350 FMGC is a Thales/Honeywell split; Boeing's 737 and 787 use Honeywell.

Certification: FMS software is typically DAL B or C for the flight planning and performance functions and DAL A for the guidance outputs, depending on the architecture and on what the autopilot does with the data.

### EFB — classification

The **Electronic Flight Bag** was originally a way to get the paper off the flight deck; it is now the primary computing platform for performance calculation, documentation and operational data.

**Hardware classes** (per FAA AC 120-76D and EASA AMC 20-25A):

- **Class 1** — portable, not mounted, stowed for critical phases of flight, no aircraft power or data connection (or only through a certified port).
- **Class 2** — portable, mounted on a certified mount, may connect to aircraft power and to a read-only data source, may be used in all phases of flight. Removable without tools by the crew.
- **Class 3** — **installed equipment**, part of the aircraft type design, certified under DO-178C/DO-254 as part of the aircraft. The FAA has moved away from the class 1/2/3 language toward "portable EFB" and "installed EFB", with the mounting and the data connection certified separately.

**Software types**:

- **Type A** — applications with no safety effect: manuals, regulations, forms, logs. No authority approval required beyond the operator's own process.
- **Type B** — applications whose malfunction or misuse could have a safety effect but below "major": **performance calculations** (takeoff, landing, weight and balance), airport moving map with own-ship position, electronic charts, weather. Require an operational evaluation and, in EASA terms, are covered by the EFB operational approval under **SPA/AMC 20-25A**.
- **Type C** — anything requiring airworthiness approval, i.e. it is not an EFB application but certified avionics.

Typical Type B applications: **Airbus FlySmart+** (running on the pilot's iPad or an installed Class 3 device), **Boeing OPT/OPT+ and Onboard Performance Tool**, **NAVBLUE** (FlySmart, N-Flight Planning, RocketRoute), **Jeppesen FliteDeck Pro** and **Mobile FliteDeck**, **Lido mPilot**, **Ubik/Comply365**, **AvioBook**, **eTechLog** solutions.

The security question is now live: an EFB with a cellular connection is a networked device on the flight deck, and DO-326A/ED-202A airworthiness security applies to any connection into aircraft systems.

### ACARS and datalink

**ACARS** (Aircraft Communications Addressing and Reporting System, 1978) is a character-oriented message system over VHF, HF and satcom, with a media-advisory function that selects the cheapest available link. Two traffic types:

- **AOC (Airline Operational Control)** — the airline's own traffic: OOOI (Out/Off/On/In) times, position reports, fuel, delay codes, weather requests, load sheets, free text to and from dispatch, ACMS/engine data downlinks, and maintenance messages.
- **ATS** — air traffic services traffic: departure clearance (DCL), oceanic clearance (OCL), ATIS (D-ATIS), position reporting (ADS-C), and pre-departure clearance.

Service providers: **SITA** and **Collins Aerospace ARINC** (the two global datalink networks), plus **Inmarsat SwiftBroadband-Safety**, **Iridium Certus**, and regional providers.

**CPDLC** (Controller-Pilot Data Link Communications) is the modern, message-set-based replacement for voice, defined in ICAO Doc 4444 and implemented over two distinct stacks:

- **FANS 1/A(+)** — the oceanic and remote implementation, built on ACARS, used with **ADS-C** contracts for automatic position reporting. Boeing FANS-1 and Airbus FANS-A converged as FANS 1/A.
- **ATN B1 (Link 2000+)** — the European continental implementation over VDL Mode 2 with the ATN protocol stack, mandated in European airspace by the **Data Link Services Implementing Rule (Regulation (EC) 29/2009 as amended)**. **ATN B2**, part of SESAR, adds trajectory-based clearances and 4D data.

Message sets are constrained and formal — uplinks like `CLIMB TO AND MAINTAIN FL350`, downlinks like `REQUEST DIRECT TO [position]`, with WILCO/UNABLE/STANDBY responses — precisely to prevent the ambiguity of free text. Free-text messages exist and are discouraged.

## 2. Airline systems

### The Passenger Service System (PSS)

Three functional blocks, historically three separate systems, now sold as a suite:

1. **Reservation (CRS)** — the PNR: passenger name records, itineraries, contact details, special service requests, fare and ticketing information. The oldest code in the industry — IBM's SABRE (1960) and the TPF/ALCS transaction processing systems still underpin significant parts of it.
2. **Inventory** — the seat availability by flight, date and booking class; the interface to revenue management; the AVS/AVN availability messaging.
3. **Departure Control System (DCS)** — check-in, seat allocation, boarding, baggage acceptance, load control and the loadsheet, and the government reporting (APIS/API, PNRGOV).

Around them: **ticketing** (electronic ticket server, the ET database, interline e-ticketing), **fares and pricing** (ATPCO fare filings, the pricing/shopping engine), **revenue accounting**, **revenue management**, **loyalty**, **crew**, **flight operations**, and **cargo**.

**Vendors:**

- **Amadeus Altéa** — the dominant modern suite (Altéa Reservation, Inventory, Departure Control), used by Lufthansa Group, IAG's carriers, Qatar Airways, Singapore Airlines, Qantas, Etihad and many others. Amadeus also owns Navitaire (the LCC-oriented New Skies platform) and has been migrating customers to **Nevio**, its offer-and-order platform.
- **Sabre** — SabreSonic CSS (reservation, inventory, DCS) plus Sabre's AirVision commercial products and the Sabre GDS. Customers include American, Alaska, JetBlue, Gulf Air.
- **SITA** — Horizon and the widely-used common-use airport products (CUTE/CUPPS, CUSS).
- **TravelSky** — the Chinese national system; carries the Chinese carriers.
- **Radixx**, **Hitit Crane**, **IBS iFly**, **AirlineERP** — the mid-market and LCC end.

**Migration risk** is the defining operational characteristic of the PSS: a cut-over is the highest-risk IT event an airline undertakes, and the failures are legendary (Virgin America to Sabre in 2011; British Airways' 2017 data centre failure was a different failure mode but the same lesson about single points of failure in the passenger-facing stack).

### GDS and the NDC transition

The **Global Distribution Systems** — Amadeus, Sabre and Travelport — connect airline inventory to travel agents using **EDIFACT** messaging over teletype-descended protocols. The airline pays a segment fee for each booking; the GDS pays part of it back to the agent as an incentive. From the airline's point of view this is an expensive channel selling a commoditised product, because EDIFACT can only express a fare and a schedule — not a branded fare, a bundle, a personalised offer or a dynamically priced ancillary.

**NDC (New Distribution Capability)** is IATA's answer, launched under **Resolution 787 in October 2012**. It is an **XML data exchange standard for Offer and Order management** that lets an airline present a rich, personalised offer directly to any distribution channel. The airline becomes the offer engine; the intermediary becomes a pipe. The latest generation is **NDC 24.1** (2024), released by IATA's Shop-Order-Pay Standards Board as a stepping stone to the full **Offers and Orders** end state.

The associated programmes:

- **ONE Order** — replaces the PNR, e-ticket and EMD triad with a single customer **order** record. The e-ticket is a 1990s digitisation of a 1930s paper document with accounting rules attached; ONE Order eliminates it.
- **Offers and Orders** — the destination architecture: an **Offer Management System** and an **Order Management System** replacing reservation/inventory/ticketing, with IATA targeting the retirement of the e-ticket by a stated date that has moved more than once **[needs-verification on the current target]**.
- **Airline Retailing Maturity (ARM) index** — IATA's replacement for the old NDC certification levels, assessing an organisation's technical capability and partnership scalability rather than issuing a badge.

Adoption is real but uneven: British Airways, Lufthansa Group, Iberia, American, Air France-KLM, Emirates, Qatar Airways and Singapore have all pushed content into NDC channels, several with surcharges on GDS-EDIFACT bookings to force migration. Corporate travel — where the TMC's tooling, expense integration and duty-of-care systems all assume EDIFACT — has been the drag.

### Crew management systems

- **AIMS** (AIMS International) — very widely used, particularly in the Middle East and Asia; integrated pairing, rostering, crew tracking, training records, payroll interface and crew portal. Qatar Airways, Emirates and many others run it.
- **Sabre CrewTrac / AirCentre Crew** — pairing, rostering, tracking; strong in North America and with the bidline model.
- **Jeppesen (Boeing) Crew Solutions** — Crew Pairing, Crew Rostering, Crew Tracking, plus Crew Fatigue; the strongest optimisation heritage (the Carmen Systems acquisition).
- **Lufthansa Systems NetLine/Crew**, **IBS iFlight Crew**, **Hitit**, **PDC/Sabre**, **CAE Flight & Crew Operations (the former AD OPT Altitude products)**.

What they must do: hold the legality rule set (FTL, CLA, qualifications, recency, licence and medical expiries), run the optimisation, publish the roster, handle bids and swaps, track actual duty, feed payroll and feed the FRMS and the training system.

### Flight planning systems

- **Lido/Flight** (Lufthansa Systems) — flight planning plus the Lido navigation database and charts.
- **Jeppesen JetPlan / JetPlanner** (Boeing) — the long-standing US-centred system, plus the Jeppesen navigation data and charts that half the world flies on.
- **NAVBLUE Flight Planning / N-Flight Planning** (Airbus) — with **Flysmart+** as the EFB performance side and **Mission+** for the operational flight folder.
- **PACE / TFDi / ForeFlight (Boeing)** — business aviation and the light end.
- **Collins Aerospace ARINCDirect**, **Universal Weather & Aviation**, **RocketRoute**.

Inputs: aircraft performance model, navigation data, NOTAMs, GRIB weather, airspace availability, overflight charges, ETOPS/EDTO adequacy, company routes. Outputs: the OFP, the ATC flight plan (ICAO FPL, now FF-ICE), the loadsheet inputs, and the datalink of the flight plan into the FMS.

### Maintenance systems (M&E / MRO)

- **AMOS** (Swiss AviationSoftware) — the European market leader for airline M&E: engineering, planning, production, materials, and the CAMO functions.
- **TRAX** — cloud-based, strong in the Americas and Asia.
- **Ramco Aviation** — strong in MRO and defence, particularly in India and the Middle East.
- **IFS Maintenix** — heavy on complex fleets and defence.
- **Swiss-AS, Rusada ENVISION, EmpowerMX, Oracle/SAP-based in-house builds**.

Functions: the Aircraft Maintenance Programme and task cards; component and life-limited-part tracking with serialised traceability; the technical log and deferred defect (MEL) management; airworthiness directive and service bulletin management; the reliability programme; materials, stores and purchasing; work order and shop floor control; and the **electronic technical logbook (eTL)** which is finally replacing paper.

Adjacent: **aircraft health monitoring** (Airbus **Skywise**, Boeing **AnalytX/Airplane Health Management**, GE and RR engine services), and **records** — the digitisation of the aircraft's continuous airworthiness record, which is worth millions of dollars at lease redelivery.

## 3. Air traffic management systems

### Europe

- **EUROCONTROL Network Manager (NM)** — the pan-European traffic flow and capacity management system. It runs the **IFPS** (flight plan processing) for all IFR flight plans in the ECAC area, the **ETFMS** (traffic flow management, which issues **CTOTs**), the **CACD** environment database, the **CFMU/NM B2B** services, and the **Airspace Use Plan / Updated Airspace Use Plan** for flexible use of airspace. This is the system that decides whether your flight departs on time.
- **iTEC (interoperability Through European Collaboration)** — the flight data processing system developed by Indra with DFS, ENAIRE, NATS, LVNL and Polish PANSA, replacing the previous generation of national FDPS. It is the European counterpart to ERAM.
- **COOPANS** — the parallel alliance (Ireland, Denmark, Sweden, Austria, Croatia) on a Thales TopSky baseline.
- **Maastricht UAC** — EUROCONTROL's own operational upper area control centre, historically the testbed for new concepts.
- **SESAR** — the technology pillar of the Single European Sky. Definition phase 2004–2008 (delivering the **ATM Master Plan**); Development 2008–2013 under the SESAR Joint Undertaking (established 8 December 2008, programme launched 3 June 2009, budget €2.1 bn, partner commitment €1.9 bn); Deployment 2014–2020 through the SESAR Deployment Manager and the Pilot Common Projects; now **SESAR 3 Joint Undertaking** under Horizon Europe. Key concept threads: **SWIM** (System Wide Information Management), **trajectory-based operations** and 4D trajectories, **free route airspace**, **extended arrival management (XMAN)**, **remote and digital towers**, **virtual centres** and the decoupling of data provision from service provision, **airspace architecture study** proposals, and U-space for drone integration.

The **Single European Sky** legislative packages (SES I in 2004, SES II in 2009, and the long-stalled **SES2+** recast finally agreed in 2024) provide the regulatory frame: functional airspace blocks, the performance and charging schemes, the Network Manager function, and EASA's expanded ATM/ANS competence.

### United States

- **ERAM (En Route Automation Modernization)** — Lockheed Martin's replacement for the HOST computer at the 20 Air Route Traffic Control Centers, fully deployed by 2015 after a long and painful development. Handles flight data processing, surveillance data processing and conflict probe for the en-route domain.
- **STARS (Standard Terminal Automation Replacement System)** — Raytheon/Leidos, the TRACON automation.
- **TFMS / TBFM (Time-Based Flow Management)** and **TFDM (Terminal Flight Data Manager)** — flow and surface management.
- **NextGen** — the FAA's modernisation programme: ADS-B Out mandate (from 1 January 2020 in defined airspace), Data Comm (CPDLC departure clearances and en-route services, delivered ahead of schedule and one of NextGen's genuine successes), Performance-Based Navigation procedures, System Wide Information Management, and NAS Voice System.

### Surveillance

- **Primary and secondary radar** — PSR and SSR, with **Mode S** interrogation providing the aircraft address and downlinked airborne parameters (**Mode S EHS/ELS**).
- **ADS-B** — the aircraft broadcasts its GNSS-derived position, velocity and identity on 1090 MHz Extended Squitter (or 978 MHz UAT in the US at low level). Cheap infrastructure, dependent on the aircraft's own navigation source, and unencrypted and unauthenticated — which is a known and unresolved security weakness.
- **Space-based ADS-B (Aireon)** — ADS-B receivers hosted on the **Iridium NEXT** constellation. First payloads launched **January 2017**; deployment complete over eight launches by **January 2019**, with **75 payloads (66 operational, 9 spares)**. It provides real-time surveillance beyond ground-station range, over oceans and remote areas. Data services agreements with NAV CANADA, NATS, ENAV, the Irish Aviation Authority, Naviair, Isavia, CAAS Singapore, ATNS South Africa and others. Its operational effect: reduction of oceanic separation minima on the North Atlantic from the old 30/30 NM toward much tighter standards, and genuine search-and-rescue and MH370-class tracking capability.
- **Multilateration (MLAT/WAM)** — time-difference-of-arrival positioning from multiple ground receivers; used where radar is uneconomic and as an ADS-B integrity cross-check.
- **GADSS** (Global Aeronautical Distress and Safety System) — the ICAO response to MH370: normal tracking at 15-minute intervals, autonomous distress tracking at 1-minute intervals once a distress condition is detected, and post-flight localisation of an accident site.

## 4. Airport systems

- **AODB (Airport Operational Database)** — the single flight record for the airport, feeding everything else.
- **RMS (Resource Management System)** — stands, gates, check-in desks, baggage carousels, bus and staff allocation.
- **FIDS** — flight information display.
- **BHS/BRS** — baggage handling and reconciliation, with IATA Resolution 753 requiring tracking at four points (acceptance, loading, transfer, delivery).
- **Common use** — **CUTE/CUPPS** (common use passenger processing systems) letting any airline use any desk, **CUSS** self-service kiosks, and now common-use biometric touchpoints under IATA **One ID**.
- **A-CDM** — the collaborative decision making platform sharing TOBT/TSAT/TTOT with the airline, handler and the network manager.
- **Security screening** — checkpoint management, CT scanner networking, and the ECAC/TSA certification regimes for detection equipment.
- **Border systems** — APIS/API and PNR transmission, e-gates, EU Entry/Exit System.

Vendors: **SITA**, **Amadeus Airport IT**, **Collins/ARINC (vMUSE, AirVue)**, **INFORM**, **TAV Technologies**, **Veovo**, **Damarel**, plus large in-house builds at the major hubs.

## 5. Data standards

| Standard | What it is |
|---|---|
| **ARINC 424** | The navigation database interchange standard. Fixed-length **132-byte records**, one per navigation element (airport, runway, waypoint, navaid, airway, SID, STAR, approach, holding, MSA, company route). First published **May 1975**; Supplement 22 in **July 2018**; the FAA publishes its **CIFP** in ARINC 424-18 format. Maintained by the Airlines Electronic Engineering Committee. |
| **Path and terminator (leg types)** | The 23 ARINC 424 leg types that define how the FMS flies between fixes: IF, TF, CF, DF, FA, FC, FD, FM, CA, CD, CI, CR, RF, AF, VA, VD, VI, VM, VR, PI, HA, HF, HM. Understanding these explains almost every "why did the FMS do that?" question — e.g. a **CF** leg has a fixed course to a fix and will produce a turn to intercept, whereas a **DF** leg goes direct from wherever you are. |
| **AIRAC** | Aeronautical Information Regulation and Control: a **28-day cycle** with globally common effective dates, published 56 days in advance, under ICAO Annex 15. Every navigation database, chart set and FMS load is keyed to it. |
| **AIXM** | Aeronautical Information Exchange Model — the XML/GML model for aeronautical information (airspace, routes, procedures, obstacles, airport data), maintained by EUROCONTROL and the FAA. Version 5.1 is the operative one; the basis of the digital AIP and of SWIM aeronautical services. |
| **FIXM** | Flight Information Exchange Model — the XML model for flight data, underpinning **FF-ICE** (Flight and Flow Information for a Collaborative Environment), ICAO's replacement for the 1960s-format ATC flight plan. |
| **WXXM / IWXXM** | Weather information exchange; IWXXM is the ICAO-mandated XML form for METAR, TAF, SIGMET etc., replacing the traditional alphanumeric bulletins in machine-to-machine exchange. |
| **SWIM** | System Wide Information Management — the service-oriented architecture (registries, service descriptions, publish/subscribe) through which AIXM, FIXM and IWXXM data are exchanged in SESAR and NextGen. |
| **IATA/ICAO messaging** | **Type B** teletype messages, still the operational backbone: PNL/ADL (passenger lists), LDM (load message), CPM (container/pallet distribution), MVT (movement), UCM, PTM, and the **AHM/IGOM** message set. **EDIFACT** PAXLST/CUSRES for border data. |
| **IATA settlement standards** | BSP/ARC reporting, SIS (Simplified Invoicing and Settlement) for interline billing, and the Clearing House rules. |
| **ATPCO** | Airline Tariff Publishing Company — the industry's fare filing and distribution utility; Category 1–35 fare rules, Routings, Record 1/3/6, plus the Branded Fares and Optional Services (Cat 25/Cat 5/Cat 31) data that make merchandising work. |
| **ARINC 429 / 664 / 653 / 615A / 610 / 828** | Avionics data bus, deterministic Ethernet, partitioning, data loading, simulator support, and electrical standards respectively. |

## Sources

- [Wikipedia — DO-178C](https://en.wikipedia.org/wiki/DO-178C)
- [Wikipedia — ARINC 653](https://en.wikipedia.org/wiki/ARINC_653)
- [Wikipedia — ARINC 424](https://en.wikipedia.org/wiki/ARINC_424)
- [IATA — New Distribution Capability (NDC)](https://www.iata.org/en/programs/airline-distribution/retailing/ndc/)
- [Wikipedia — Aireon](https://en.wikipedia.org/wiki/Aireon)
- [Wikipedia — Single European Sky ATM Research](https://en.wikipedia.org/wiki/Single_European_Sky_ATM_Research)

## Open questions

- **DO-178C objective counts** (A:71, B:69, C:62, D:26) are the widely-quoted DO-178C figures but were not confirmed from the cited source; verify against DO-178C Annex A tables.
- **IATA's target date for e-ticket retirement / full Offers and Orders** has moved repeatedly and is unverified here.
- **iTEC and COOPANS deployment status** by centre is unverified.
- **SES2+ recast** — agreement reported in 2024; the implementing timeline is unverified.
- The list of **ARINC 424 leg types** is from working knowledge; verify against the specification before using operationally.
- **PSS vendor customer lists** change with every contract renewal; verify before citing any specific airline-vendor pairing.

