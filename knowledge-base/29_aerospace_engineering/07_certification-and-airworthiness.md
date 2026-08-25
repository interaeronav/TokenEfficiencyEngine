---
id: aerospace.certification
title: Certification and airworthiness
domain: 29_aerospace_engineering
tags: [certification, airworthiness, icao, easa, faa, cs-25, part-25, cs-23, type-certificate, doa, poa, means-of-compliance, do-178c, do-254, arp4754b, arp4761a, failure-conditions, airworthiness-directives, 737-max, evtol, sc-vtol, hydrogen, autonomy]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "14 CFR Part 25 — Airworthiness Standards: Transport Category Airplanes", url: "https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-25", publisher: "eCFR", accessed: 2026-08-25}
  - {title: "14 CFR 25.1309 — Equipment, systems, and installations", url: "https://www.ecfr.gov/current/title-14/section-25.1309", publisher: "eCFR", accessed: 2026-08-25}
  - {title: "DO-178C", url: "https://en.wikipedia.org/wiki/DO-178C", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "DO-254", url: "https://en.wikipedia.org/wiki/DO-254", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "ARP4754", url: "https://en.wikipedia.org/wiki/ARP4754", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Boeing 737 MAX groundings", url: "https://en.wikipedia.org/wiki/Boeing_737_MAX_groundings", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "CS-25 Amendment 28", url: "https://www.easa.europa.eu/en/document-library/certification-specifications/cs-25-amendment-28", publisher: "EASA", accessed: 2026-08-25}
  - {title: "Special Condition for VTOL and proposed Means of Compliance", url: "https://www.easa.europa.eu/en/document-library/product-certification-consultations/special-condition-vtol", publisher: "EASA", accessed: 2026-08-25}
related: [aerospace.avionics, aerospace.structures, aerospace.design_process, aerospace.manufacturing]
unit_system: SI
---

# Certification and airworthiness

**Summary.** Certification is the mechanism by which a State satisfies itself that a design, and each article built to it, is safe enough to carry the public. It is a legal process built on an engineering one: the applicant proposes a **certification basis** (which rules apply), proposes a **means of compliance** for each rule, generates evidence, and the authority — or the applicant's delegated engineers — finds compliance. The whole edifice rests on one quantitative idea: catastrophic failure conditions must be **extremely improbable**, meaning a probability below **1×10⁻⁹ per flight hour**, and must not result from a single failure. Everything else — DO-178C, ARP4754B, damage tolerance, redundancy architecture — is machinery for demonstrating that number.

## Key facts

| Item | Value |
|---|---|
| Treaty basis | **Chicago Convention 1944**; **ICAO Annex 8** *Airworthiness of Aircraft*; Annex 6 Operations, Annex 16 Environmental Protection |
| US large aeroplane code | **14 CFR Part 25**; subparts **A** General, **B** Flight, **C** Structure, **D** Design and Construction, **E** Powerplant, **F** Equipment, **G** Operating Limitations and Information, **H** Electrical Wiring Interconnection Systems (EWIS), **I** Special Federal Aviation Regulations |
| EU equivalent | **CS-25** (Certification Specifications for Large Aeroplanes) — **Amendment 28** is a published amendment level (current level `needs-verification`) |
| Normal-category code | **14 CFR Part 23** (restructured to performance-based rules by Amendment 23-64, effective 2017) / **CS-23** |
| Rotorcraft | Part 27 / CS-27 (small), Part 29 / CS-29 (large) |
| Engines / propellers / APU | Part 33 / CS-E; Part 35 / CS-P; CS-APU |
| Safety objective rule | **14 CFR 25.1309(b)** — catastrophic failure conditions **extremely improbable and not resulting from a single failure**; hazardous **extremely remote**; major **remote**; significant latent failures eliminated or minimised |
| Structural factor of safety | **1.5** (25.303); limit vs ultimate (25.305); damage tolerance (25.571); pressurised compartment loads (25.365) |
| Software standard | **DO-178C / ED-12C**, approved by RTCA December 2011, available from **5 January 2012** |
| DO-178C objectives | **Level A: 71 objectives (67 with independence); B: 68 (51); C: 63 (18); D: 26 (0); E: not covered** |
| Hardware standard | **DO-254 / ED-80**, released **2000**; FAA recognised it as an acceptable means of compliance via **AC 20-152, 30 June 2005**; levels A–E |
| Systems development | **ARP4754** *Guidelines for Development of Civil Aircraft and Systems* — original **Nov 1996**; **Rev A December 2010** (FAA AC 20-174, Nov 2011; EUROCAE ED-79); **Rev B December 2023** aligned with ARP4761A |
| Safety assessment | **ARP4761** (Rev A, Dec 2023) — FHA, PSSA, SSA, FTA, FMEA/FMES, CCA (ZSA, PRA, CMA) |
| 737 MAX ungrounding | FAA cleared return to service **18 November 2020** after a **20-month** grounding, the longest ever of a US airliner |

> ⚠️ Certification is a *legal* status attached to a *specific configuration*. An aircraft that has been modified outside its approved configuration is not certified, no matter how well the modification was engineered. This is the entire reason for STCs, minor/major change classification, and the paperwork culture that pilots experience as MEL/CDL discipline.

## 1. ICAO and the hierarchy

The Chicago Convention makes airworthiness a **State of Registry** responsibility. **Annex 8** sets broad Standards; States implement them in national law (14 CFR in the US, EU Regulation 748/2012 and the Basic Regulation 2018/1139 in Europe). ICAO does not certify anything.

The practical hierarchy:
```
ICAO Annex 8 (Standards and Recommended Practices)
   ↓ implemented by
State airworthiness authority (FAA / EASA / UK CAA / TCCA / CAAC / ANAC / SACAA / QCAA ...)
   ↓ issues
Type Certificate (design) → Production Approval (build) → Certificate of Airworthiness (each aircraft)
   ↓ maintained by
Continuing airworthiness: ADs, service bulletins, maintenance programme, CAMO
```

**Bilateral Aviation Safety Agreements (BASAs)** with **Technical Implementation Procedures (TIPs)** let one authority validate another's certificate with reduced duplication. The FAA–EASA relationship rests on mutual acceptance of most findings — which is what made the 737 MAX affair a diplomatic as well as a safety crisis, since EASA and other authorities declined to simply accept the FAA's return-to-service and imposed their own conditions.

## 2. The type certificate process

1. **Application.** The applicant applies with a description of the product. The date of application usually fixes the **certification basis** — the amendment level of the applicable code — subject to a 5-year (Part 25) currency rule after which the basis must be updated.
2. **Certification basis establishment.** The authority determines the applicable paragraphs, plus:
   - **Special Conditions** where the rules do not cover a novel feature (composite fuselage, lithium batteries, fly-by-wire, eVTOL).
   - **Exemptions / deviations** where compliance is impracticable and an equivalent level of safety exists (**ELOS** findings).
   - **Equivalent Safety Findings**.
3. **Certification Programme / Certification Plan.** Agreed with the authority: the schedule, the **Level of Involvement** (which findings the authority will make itself and which it delegates), and the list of compliance documents.
4. **Means of Compliance (MoC).** For each requirement, the applicant proposes how compliance will be shown. EASA codes them:
   - **MC0** compliance statement; **MC1** design review; **MC2** calculation/analysis; **MC3** safety assessment; **MC4** laboratory test; **MC5** ground test on the aircraft; **MC6** flight test; **MC7** design inspection; **MC8** simulation; **MC9** equipment qualification.
5. **Compliance demonstration.** Analysis reports, test plans and reports, flight test programme, structural test articles, systems rigs, and the safety assessment package.
6. **Findings of compliance.** By the authority's engineers, or by the applicant's **Design Organisation Approval (DOA)** holders / FAA **ODA** unit members acting under delegation.
7. **Type Certificate issue**, with a **Type Certificate Data Sheet (TCDS)** stating the approved models, limitations, engines, weights and required equipment. Then the **Aircraft Flight Manual**, **Instructions for Continued Airworthiness (ICA)**, MMEL, and the maintenance review board report.

Timescales: 3–5 years for a derivative, 5–8 years for a clean sheet, and the flight test programme alone consumes 2,000–3,000 hours across 4–6 aircraft for a large transport.

**Changes** after TC: classified as **minor** (no appreciable effect on weight, balance, structural strength, reliability, operational characteristics or other airworthiness characteristics) or **major**. Major changes need approval; a major change by someone other than the TC holder is a **Supplemental Type Certificate (STC)**. This is how cabin reconfigurations, winglet retrofits, avionics upgrades and freighter conversions are approved.

## 3. Organisation approvals

**Design Organisation Approval (DOA)** — EASA **Part 21 Subpart J**. Requires a design assurance system, an independent monitoring function, a handbook, and nominated postholders. Privileges: classify changes as minor/major, approve minor changes and minor repairs, and — with the appropriate scope — make findings of compliance for major changes and repairs without direct EASA involvement. The FAA equivalent is the **ODA (Organization Designation Authorization)**, whose scope and oversight became the central issue of the MAX inquiry.

**Production Organisation Approval (POA)** — EASA **Part 21 Subpart G** (FAA: Production Certificate). Requires a quality system demonstrating that each article conforms to the approved design. This is what authorises the organisation to issue **EASA Form 1 / FAA Form 8130-3** release certificates, and it is the legal underpinning of the parts traceability system.

**Maintenance organisation approval** — **Part 145** (FAA Part 145 repair station), with **AS9110** as the associated quality standard, and **Part-CAMO** for continuing airworthiness management.

## 4. CS-25 / Part 25 — what the rules actually require

Part 25 subparts, verified from the eCFR:

| Subpart | Scope | Representative rules |
|---|---|---|
| **A** General | Applicability | 25.1 |
| **B** Flight | Performance, controllability, trim, stability, stalls, ground and water handling, misc. flight requirements | 25.107 take-off speeds; 25.111 take-off path; 25.119/121 climb gradients; 25.143 controllability; 25.173–177 static stability; 25.201–207 stalls and stall warning; 25.251 vibration and buffeting |
| **C** Structure | Loads, flight loads, control surface and system loads, ground loads, emergency landing, fatigue | **25.301** loads; **25.303** factor of safety **1.5**; **25.305** strength and deformation; 25.331–341 manoeuvre and gust; **25.365** pressurised compartment loads; 25.561/562 emergency landing and seat dynamics (16 g); **25.571** damage tolerance and fatigue; 25.629 aeroelastic stability |
| **D** Design and Construction | Materials, fabrication, fasteners, protection, control systems, landing gear, doors, fire protection, lightning | 25.603 materials; 25.605 fabrication methods; 25.613 material strength properties and design values (A- and B-basis); 25.671/672 control systems; 25.783 doors; 25.795 security; 25.807 emergency exits |
| **E** Powerplant | Installation, fuel, oil, cooling, induction, exhaust, controls, fire protection | 25.901 installation; 25.903 engines (incl. rotor burst, 25.903(d)); 25.933 reverser systems; 25.951–981 fuel system incl. tank flammability |
| **F** Equipment | Instruments, electrical, lights, safety equipment, ice protection, miscellaneous | **25.1309** equipment, systems and installations; 25.1316/1317 lightning and HIRF; 25.1419 ice protection; 25.1435 hydraulics |
| **G** Operating Limitations and Information | AFM content, markings, placards | 25.1501–1587 |
| **H** EWIS | Electrical Wiring Interconnection Systems | 25.1701–1733 — added post-TWA 800 and Swissair 111 |
| **I** SFARs | Special Federal Aviation Regulations | |

### The 25.1309 safety architecture

The quantitative core. **25.1309(b)** requires that systems be designed so that "each catastrophic failure condition must be extremely improbable" and does not result from a single failure; hazardous conditions must be extremely remote; major conditions remote; and significant latent failures eliminated or minimised where practical. **25.1309(c)** requires the aeroplane and systems to give the flight crew information about unsafe operating conditions in time for corrective action, and to minimise crew errors that could create additional hazards.

The AC 25.1309-1 / AMC 25.1309 classification, which is the table every systems engineer works from:

| Failure condition | Effect | Qualitative probability | Quantitative target (per flight hour) | DAL |
|---|---|---|---|---|
| **No safety effect** | No effect on safety, workload or comfort | No probability requirement | — | **E** |
| **Minor** | Slight reduction in safety margins; slight workload increase; some inconvenience | Probable | > 1×10⁻⁵ | **D** |
| **Major** | Significant reduction in margins; significant workload increase; possible injuries | Remote | < 1×10⁻⁵ | **C** |
| **Hazardous** | Large reduction in margins; excessive workload; serious or fatal injury to a small number | Extremely remote | < 1×10⁻⁷ | **B** |
| **Catastrophic** | Multiple fatalities, usually with loss of the aeroplane | Extremely improbable | **< 1×10⁻⁹** | **A** |

The **1×10⁻⁹** figure has a derivation, not a mystique: historical accident rates gave roughly one catastrophic accident per 10⁷ flight hours, of which perhaps 10 % were attributable to systems failures, and about 100 potentially catastrophic failure conditions were assumed per aircraft — giving 10⁻⁶ × 10⁻¹ ÷ 10² ≈ 10⁻⁹ per condition per hour.

This is why a transport aircraft has three hydraulic systems, dual or triple redundant flight control computers of dissimilar design, and why single-point failures in flight-critical functions are unacceptable *regardless of how reliable the single item is*.

## 5. The standards stack

```
ARP4754B — aircraft/systems development process, FDAL/IDAL assignment
   ├── ARP4761A — safety assessment methods (FHA → PSSA → SSA; FTA, FMEA, CCA)
   ├── DO-178C  — software (DAL A–E, 71/68/63/26 objectives)
   │      ├── DO-330 tool qualification
   │      ├── DO-331 model-based development and verification
   │      ├── DO-332 object-oriented technology
   │      └── DO-333 formal methods
   ├── DO-254   — airborne electronic hardware (complex: FPGA/ASIC/PLD)
   ├── DO-160G  — environmental conditions and test procedures for equipment
   └── DO-297   — Integrated Modular Avionics development and certification
```

**ARP4754B** (*Guidelines for Development of Civil Aircraft and Systems*, December 2023) is the umbrella: it defines the development process from aircraft-level functions down to items, and assigns **FDAL** (Functional Development Assurance Level, aircraft/system level) and **IDAL** (Item Development Assurance Level, for software and complex hardware). Development assurance is the answer to a specific problem: **you cannot test a probability of 10⁻⁹ into existence for a design error.** Random hardware failures can be predicted probabilistically; systematic errors (a mistaken requirement, a coding fault) cannot. Development assurance substitutes process rigour, independence and traceability for a probability calculation.

**ARP4761A** provides the methods: **FHA** (Functional Hazard Assessment) at aircraft and system level to identify and classify failure conditions; **PSSA** (Preliminary System Safety Assessment) to allocate requirements and derive DALs, using fault tree analysis; **SSA** (System Safety Assessment) to verify the implementation meets them; plus **FMEA/FMES**, and **Common Cause Analysis** in three parts — **Zonal Safety Analysis** (what is physically near what), **Particular Risks Analysis** (rotor burst, tyre burst, bird strike, fire, lightning, HIRF), and **Common Mode Analysis** (shared design, manufacture, maintenance, environment).

**DO-178C** governs software. Its 71 objectives at Level A (67 with independence) span planning, development, verification, configuration management, quality assurance and certification liaison. Two things are worth understanding about it: (a) it is a **process** standard, not a product standard — it does not tell you the code is correct, it tells you the process that produced the code was disciplined; and (b) its structural coverage requirement at Level A, **MC/DC** (Modified Condition/Decision Coverage), is what makes Level A software roughly 3–10× the cost per line of Level C.

**DO-254** does the same for **complex electronic hardware** — FPGAs, ASICs, PLDs, and the LRUs and circuit-card assemblies containing them — where "tests and analyses alone" cannot assure performance. It was released in **2000** and recognised by the FAA through **AC 20-152 on 30 June 2005**, with the same A–E level structure.

## 6. Continued airworthiness

Once a type is in service, the TC holder retains an obligation to monitor it and to develop corrective action. The authority's instrument is the **Airworthiness Directive (AD)** — a legally binding order to inspect, modify or restrict operation, issued when an unsafe condition exists in a product and is likely to exist in others of the same type. ADs may mandate a service bulletin, impose a repetitive inspection, reduce a life limit, or ground the fleet.

Supporting machinery:
- **Instructions for Continued Airworthiness (ICA)** per 25.1529 / Appendix H — the AMM, SRM, CMM, IPC and the **Airworthiness Limitations Section**, which contains the mandatory life limits and inspections that no operator may vary.
- **MSG-3 analysis** by the Maintenance Review Board → the **Maintenance Planning Document**, which is the logical basis of every A/C check interval an operator flies to.
- **Certification Maintenance Requirements (CMRs)** — inspections credited in the safety assessment to detect latent failures; these are certification items, not maintenance-optimisation items, and cannot be extended by the operator.
- **Ageing aircraft**: SSIDs, Corrosion Prevention and Control Programmes, the **Limit of Validity (LOV)** for widespread fatigue damage, and repair assessment programmes.
- **Continued Operational Safety (COS)** processes and service difficulty reporting.

## 7. The 737 MAX certification failure

The 737 MAX is the most consequential certification failure of the modern era and should be understood mechanically, not morally.

**The engineering chain.** The MAX's larger-diameter LEAP-1B engines had to be mounted further forward and higher, changing the nacelle's contribution to pitching moment at high angle of attack and producing a nose-up tendency. Boeing added **MCAS (Manoeuvring Characteristics Augmentation System)** to trim the stabiliser nose-down in that regime, so that the column force gradient met the 25.173/25.203 requirements and so that the type could retain a common type rating with the NG.

**The failures, per the public record:**
1. **Single-sensor architecture.** "The original MCAS design relied on input from a single AoA sensor." A single failure of that sensor commanded repeated nose-down stabiliser trim — a textbook violation of the 25.1309(b) principle that a catastrophic condition must not result from a single failure.
2. **Mis-classified hazard.** Boeing "convinced the FAA it could not fail hazardously or catastrophically." The classification drove everything downstream: the redundancy architecture, the DAL, the crew-alerting design, and the training analysis. Get the FHA wrong and every subsequent process is rigorously applied to the wrong problem.
3. **Scope creep after the hazard assessment.** MCAS's authority was increased late in development (larger stabiliser movement, repeated activation) without the safety assessment being redone against the new authority.
4. **Training and disclosure.** MCAS was not described in the flight crew manuals; the assumption that simulator training was unnecessary "diminished safety, minimized the value of pilot training," per the September 2020 House report. Commonality with the NG was a commercial requirement that acted as an engineering constraint.
5. **Delegation without oversight.** In **November 2019 the FAA revoked Boeing's ODA authority to issue airworthiness certificates for individual MAX aircraft**, and fined Boeing for exerting **"undue pressure" on designated inspectors** — evidence that the delegation mechanism's independence safeguards had failed.
6. **Known risk not acted on.** After the **Lion Air crash of October 2018**, the FAA's own internal analysis in **December 2018** predicted that the MCAS design flaw "could result in as many as 15 future fatal crashes over the life of the fleet" — and the fleet was not grounded until after Ethiopian Airlines Flight 302 in March 2019.
7. **Cultural findings.** The House report concluded Boeing "dismissed employee concerns with MCAS, prioritized deadline and budget constraints over safety."

**The fix and the consequences.** The redesign required **dual-sensor confirmation before MCAS activation**, limited its authority to a single activation per AoA event, ensured the crew could always override with column and trim, added an **AoA Disagree** alert, and imposed revised training including simulator sessions. The FAA cleared the type to return to service on **18 November 2020**, ending a **20-month grounding — the longest ever of a US airliner**.

Institutionally: the **Aircraft Certification, Safety, and Accountability Act (2020)** reformed ODA oversight, required safety-critical information disclosure, protected ODA engineers from undue pressure and mandated human-factors consideration of flight-crew response assumptions; the **Joint Authorities Technical Review (JATR)** made findings on the adequacy of the certification process for incremental changes to legacy designs; EASA and other authorities conducted independent reviews and imposed additional conditions rather than accepting the FAA validation unmodified. The deepest structural lesson concerns **derivative certification**: the MAX inherited a certification basis substantially rooted in the 1960s 737, and the incremental-change model allowed a fundamentally new automatic flight-control function to be certified against a legacy framework. That model is now under permanent scrutiny.

## 8. Certifying novel technology

The regulatory system is designed to codify accumulated experience. New technology has, by definition, none — so the machinery available is **Special Conditions**, **Special Classes**, and purpose-written specifications.

**eVTOL / advanced air mobility.** EASA created **SC-VTOL** as a bespoke certification specification for VTOL-capable aircraft, with two categories — **Basic** and **Enhanced** — where Enhanced (commercial passenger operations over congested areas) carries a **continued safe flight and landing** requirement and a catastrophic failure probability target aligned with large aeroplanes. Means of compliance are being published progressively; **MOC-5 to SC-VTOL Issue 1 was published for consultation on 18 July 2025**. The FAA took a different route, certifying eVTOLs as **powered-lift** under 21.17(b) special class with rules drawn from Parts 23, 27, 29 and 33, and published a powered-lift operations SFAR in 2024. The consequences are practical: divergent certification bases mean a European and a US eVTOL are not automatically mutually validatable, and the pilot certification and operational rules were, until recently, a larger obstacle than the airworthiness rules.

**Hydrogen.** No certification basis exists for a large hydrogen aircraft. The gaps are substantial: cryogenic tank structural and thermal requirements, boil-off and venting, fire and explosion protection (hydrogen's wide flammability range and low ignition energy), fuel system leak detection, crashworthiness of a cryogenic tank under 25.561/562 emergency landing loads, refuelling procedures and airport infrastructure standards, and the ICAO Annex 16 environmental framework which currently has no metric for non-CO₂ effects. EASA and the FAA have both begun rulemaking scoping and research programmes; nothing is close to a published certification specification.

**Autonomy and AI.** EASA published an **AI Roadmap** and the first **AI trustworthiness guidance** for Level 1 (assistance to human) and Level 2 (human–machine collaboration) applications, with Level 3 (advanced automation) deliberately deferred. The unresolved problem is fundamental: **DO-178C assumes requirements can be written and traced to code**, and a learned model has no such traceability. The proposed answers — a learning assurance W-shaped process, data quality requirements, runtime monitoring, and operational design domain restriction — are plausible but unproven, and no safety-critical machine-learning function has yet been certified at DAL A or B. Single-pilot operations (eMCO/SiPO) face the same wall from a human-factors direction. Anyone forecasting certified single-pilot commercial operations this decade is ahead of the regulatory evidence.

**Other current special-condition areas**: lithium battery installations, composite structure (crashworthiness, lightning, repair), more-electric architectures, HIRF from ubiquitous portable electronics, cybersecurity of aircraft systems (now addressed by DO-326A/ED-202A airworthiness security process and DO-356A/ED-203A security methods, mandated in Part 21 via the EASA Part-IS rules).

## Sources

- [14 CFR Part 25](https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-25) — eCFR (subpart structure verified)
- [14 CFR §25.1309](https://www.ecfr.gov/current/title-14/section-25.1309) — eCFR (paragraphs (a), (b), (c))
- [DO-178C](https://en.wikipedia.org/wiki/DO-178C) — Wikipedia (publication dates, objective counts by level, supplements)
- [DO-254](https://en.wikipedia.org/wiki/DO-254) — Wikipedia (release 2000, AC 20-152 of 30 June 2005, scope, levels)
- [ARP4754](https://en.wikipedia.org/wiki/ARP4754) — Wikipedia (revision history, FDAL/IDAL, relation to ARP4761 and DO-178C/DO-254)
- [Boeing 737 MAX groundings](https://en.wikipedia.org/wiki/Boeing_737_MAX_groundings) — Wikipedia (MCAS, single AoA sensor, ODA revocation, House report, 18 November 2020 return to service)
- [EASA CS-25 Amendment 28](https://www.easa.europa.eu/en/document-library/certification-specifications/cs-25-amendment-28) — EASA
- [EASA Special Condition for VTOL and proposed Means of Compliance](https://www.easa.europa.eu/en/document-library/product-certification-consultations/special-condition-vtol) — EASA (MOC-5 published 18 July 2025)

## Open questions

- **Current CS-25 amendment level** — Amendment 28 exists as a published document; whether a later amendment is current in 2026 is `needs-verification` (the EASA document library index would not render).
- **SC-VTOL Issue 1 original issue date** (commonly cited as 2 July 2019) and the exact Basic/Enhanced quantitative safety objectives — the EASA page returned only the MOC-5 consultation notice; `needs-verification`.
- The derivation of the 1×10⁻⁹ target given here is the standard one from AC 25.1309-1A/AMC 25.1309, reproduced from memory rather than re-fetched — `needs-verification`.
- Exact scope and current status of the FAA Aircraft Certification, Safety, and Accountability Act 2020 implementation, and the JATR recommendation set — `needs-verification`.
- Part 23 Amendment 23-64 effective date (given as 2017) — `needs-verification`.
- DO-326A/ED-202A and EASA Part-IS applicability dates — `needs-verification`.

