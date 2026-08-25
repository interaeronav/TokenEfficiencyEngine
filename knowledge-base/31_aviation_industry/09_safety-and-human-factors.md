---
id: aviation_industry.safety
title: Safety and human factors — the discipline behind the record
domain: 31_aviation_industry
tags: [accident-rate, swiss-cheese, hfacs, tem, crm, automation, mode-confusion, af447, asiana-214, 737-max, startle, fatigue, ftl, frms, fdm, foqa, losa, adrep, just-culture, safety-ii, resilience, loc-i, cfit, runway-excursion, gnss-spoofing]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Safety Report shows continued improvement (2024 data)", url: "https://www.iata.org/en/pressroom/2025-releases/2025-02-26-01/", publisher: "IATA", accessed: 2026-08-25}
  - {title: "IATA Annual Safety Report (62nd edition)", url: "https://www.iata.org/en/publications/safety-report/", publisher: "IATA", accessed: 2026-08-25}
  - {title: "IATA, CANSO and ACI Launch Joint Runway Safety Initiative", url: "https://www.iata.org/en/pressroom/2026-releases/07-28-iata-canso-aci-launch-joint-runway-safety-initiative/", publisher: "IATA", accessed: 2026-08-25}
  - {title: "Threat and error management", url: "https://en.wikipedia.org/wiki/Threat_and_error_management", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Convention on International Civil Aviation (Annex 13, Annex 19)", url: "https://en.wikipedia.org/wiki/Convention_on_International_Civil_Aviation", publisher: "Wikipedia", accessed: 2026-08-25}
related: [aviation_industry.operations, aviation_industry.training, aviation_industry.legal]
unit_system: SI
---

# Safety and human factors

**Summary.** Commercial aviation's safety record is the outcome of a deliberate, century-long engineering and organisational programme, not of luck or of individual heroism. IATA's data for 2024 shows an all-accident rate of 1.13 per million flights — one accident per 880,000 flights, against a five-year average of 1.25 and one per 456,000 flights a decade earlier — with seven fatal accidents and 244 on-board fatalities across 40.6 million flights. That improvement came from a specific sequence of ideas: engineering out single-point failures, then Crew Resource Management, then systematic data collection, then systemic accident models, then safety management systems, and now competency-based training and resilience engineering. This file covers those ideas, the accidents that produced them, and the risks that remain open — including GNSS interference and conflict-zone overflight, both of which are live in 2026.

## Key facts

| Metric | Figure | Year |
|---|---|---|
| All-accident rate | **1.13 per million flights** (1 per 880,000) | 2024 |
| Five-year average accident rate | 1.25 per million flights | 2020–2024 |
| Accident rate a decade earlier | 1 per 456,000 flights | ~2015 |
| Fatal accidents | 7 (vs 1 in 2023; five-year average 5) | 2024 |
| On-board fatalities | 244 (vs 72 in 2023; five-year average 144) | 2024 |
| Fatality risk | 0.06 (five-year average 0.10; 2023 was 0.03) | 2024 |
| Total flights | 40.6 million | 2024 |
| Leading accident categories | Tail strikes and runway excursions; **zero CFIT** | 2024 |
| Latest safety report | IATA Annual Safety Report, **62nd edition** (covering 2025) — figures not retrieved | 2026 |

> ⚠️ The 2024 numbers are the most recent verified in this pass. The 62nd edition of the IATA Annual Safety Report, covering 2025, exists but its headline figures were not retrieved and are marked as needing verification.

## 1. Accident models

### The linear chain and its limits

The earliest model was the **domino theory** (Heinrich, 1931): a sequence of events, remove one and the accident does not happen. It produced a generation of accident reports whose "probable cause" was a single human error, and a generation of remedies that consisted of telling people to be more careful. It is wrong, but it is intuitive, and it survives in litigation and in journalism.

### Reason's Swiss cheese model

James Reason's **organisational accident** model (*Human Error*, 1990; *Managing the Risks of Organizational Accidents*, 1997) is the field's central metaphor. Defences against hazards are represented as a series of slices with holes; an accident occurs when the holes momentarily align to give a trajectory from hazard to loss.

The important content, which the popular version usually omits:

- **Active failures** — errors and violations committed by people in direct contact with the system. They have immediate, usually short-lived, effect.
- **Latent conditions** — decisions made by designers, managers, regulators and procedure writers that lie dormant in the system, sometimes for years. Reason's phrase is "resident pathogens". Understaffing, a poorly designed checklist, an ambiguous procedure, a maintenance programme with an inadequate interval, a commercially-driven schedule.
- **Error-producing conditions** — the local factors that make active failure likely: time pressure, fatigue, poor human-machine interface, inadequate training, distraction, high workload, poor lighting.
- The key claim: **latent conditions are the more tractable target**, because they can be found before the accident, whereas active failures can only be found afterwards.

Reason's error taxonomy, from Rasmussen's skill/rule/knowledge framework:

| Type | Description | Example |
|---|---|---|
| **Slip** | Correct intention, execution failure at the skill-based level | Selecting the wrong switch on a familiar panel |
| **Lapse** | Memory failure | Forgetting an item because of an interruption |
| **Rule-based mistake** | Applying a good rule in the wrong situation, or applying a bad rule | Using the wrong performance table |
| **Knowledge-based mistake** | Reasoning failure in a novel situation | Misdiagnosing an unfamiliar failure |
| **Violation** | Deliberate deviation from a procedure — routine, situational, optimising, or exceptional | Continuing an unstable approach because everyone does |

Violations require a different remedy from errors: errors respond to design, training and workload management; violations respond to procedure quality, supervision, culture and the perceived cost of compliance. Conflating them is the single most common failure in accident analysis.

### HFACS

The **Human Factors Analysis and Classification System** (Wiegmann and Shappell, 2000, developed for US naval aviation) operationalises Reason into a four-level taxonomy that an investigator can actually code:

1. **Unsafe acts of operators** — errors (skill-based, decision, perceptual) and violations (routine, exceptional).
2. **Preconditions for unsafe acts** — environmental factors (physical and technological), condition of operators (adverse mental states, adverse physiological states, physical/mental limitations), and personnel factors (crew resource management, personal readiness).
3. **Unsafe supervision** — inadequate supervision, planned inappropriate operations, failure to correct a known problem, supervisory violations.
4. **Organisational influences** — resource management, organisational climate, organisational process.

Its value is comparability: coding a large set of accidents in HFACS makes it possible to say which category is over-represented and therefore where intervention pays. Its limitation is that it is still a taxonomy of failure, and therefore blind to how the system usually succeeds.

### Threat and Error Management

**TEM** was developed at the **University of Texas** from 1994, out of the analysis of high-capacity public transport accidents. Its premise is that pilots *will* make errors and *will* encounter risk, so the training target is management rather than elimination.

Three constructs:

- **Threats** — events or conditions outside the crew's influence that increase operational complexity and must be managed: weather, terrain, ATC, aircraft malfunction, cabin events, ground events, operational pressure, fatigue, unfamiliar airports. Split into **environmental** and **organisational** threats, and into **expected** (a known thunderstorm) and **unexpected** (a bird strike).
- **Errors** — crew actions or inactions that deviate from intentions or expectations: aircraft handling errors, procedural errors, communication errors.
- **Undesired Aircraft States (UAS)** — a position, speed, attitude or configuration that clearly reduces safety margins: an unstable approach, a lateral deviation, a wrong configuration, an incorrect altitude. This is the model's most useful contribution, because it names an observable, measurable intermediate state between error and accident, and it defines the crew's job at that point as **recovery**, not diagnosis.

The management sequence: **avoid the threat → trap the error → mitigate the UAS**. Each has its own countermeasures, and the countermeasures are the observable behaviours that LOSA measures and that CBTA assesses.

TEM is now embedded in ICAO PANS-TRG, in EASA's CRM requirements, and in the competency framework described in `05`.

## 2. CRM and its generations

**Crew Resource Management** began after **United 173** (Portland, 1978 — a DC-8 crew fixated on a landing gear indication and ran out of fuel with three functioning engines) and the NASA workshop that followed in 1979. Helmreich's taxonomy of generations:

| Generation | Period | Content | Problem it had |
|---|---|---|---|
| **1st** | ~1981– | "Cockpit Resource Management": management-style seminars, psychological testing, assertiveness training, general management theory | Perceived as "charm school"; resented; no clear link to flight operations |
| **2nd** | mid-1980s | Aviation-specific concepts: situational awareness, stress management, decision strategies, team building; introduction of **LOFT** | Still largely a classroom activity, separate from technical training |
| **3rd** | early 1990s | Integration into the flight deck: procedures and checklists redesigned to support CRM; extension to cabin crew, dispatchers and maintenance; joint training | Became prescriptive; some operators reduced it to a compliance course |
| **4th** | mid-1990s | Integration into **AQP** and into training and checking; competencies made assessable | Assessment of "attitude" is problematic |
| **5th** | late 1990s | **Error management** as the explicit organising principle: error is normal and inevitable, the target is trapping and mitigation. Just culture as a precondition | — |
| **6th** | 2000s | **Threat and error management** — extending beyond the crew's own errors to the threats they face | — |
| **7th (arguably)** | 2010s– | **CBTA/EBT** — CRM dissolved into the competency framework rather than taught as a separate subject; **resilience** and **surprise management** added | Instructor standardisation |

The current EASA structure requires initial, operator conversion, annual recurrent and command CRM training, delivered by a qualified CRM instructor, with defined elements including human error and reliability, error chain, prevention and detection; company safety culture, SOPs, organisational factors; stress and stress management, fatigue and vigilance; information acquisition and processing, situation awareness, workload management; decision making; communication and coordination inside and outside the flight deck; leadership and team behaviour, synergy; automation and philosophy of the use of automation; specific type-related differences; case studies; **resilience development**; **surprise and startle effect**; and **cultural differences**.

## 3. Automation, mode confusion, and the two philosophies

### The problem

Wiener's coinage — **"clumsy automation"** — captures it: automation reduces workload when workload is already low and increases it when workload is already high. Bainbridge's **"ironies of automation"** (1983) states the deeper problem: the more reliable the automation, the less practised the operator, and the more the operator is required to take over precisely in the circumstances the automation could not handle.

The specific failure modes:

- **Mode confusion / mode awareness** — the pilot believes the system is in one mode when it is in another. Vertical modes are the classic case: on an Airbus, the distinction between **OPEN DESCENT / OP DES** (which manages speed with pitch and sets thrust to idle) and **V/S** or **DES** is a live trap, as is the **FLCH trap** on a Boeing.
- **Automation surprise** — the aircraft does something the crew did not expect and cannot immediately explain, at which point they stop flying and start investigating.
- **Loss of mode awareness through protection reversion** — the flight control laws degrade (Normal → Alternate → Direct on an Airbus) and the protections the crew has relied on are no longer there, at the moment they are most needed.
- **Skill decay in manual flight** — automation dependency, exacerbated by operator policies that discouraged hand-flying. The FAA's SAFO 13002 (2013) and subsequent EASA guidance explicitly encourage manual flying practice.

### Airbus and Boeing philosophies

This is often caricatured. The substantive difference:

| | **Airbus (fly-by-wire, from A320)** | **Boeing (from 777, and the 787)** |
|---|---|---|
| Control inceptor | Sidestick, **not** mechanically back-driven, no force feedback between pilots | Yoke, back-driven, both pilots see and feel the other's input and the autopilot's |
| Control law | The pilot commands a **flight path parameter** (load factor in pitch, roll rate in roll); the system holds it | The pilot commands a control surface deflection with **artificial feel**; the aircraft behaves conventionally |
| Envelope limits | **Hard protections** in Normal Law: alpha protection, high speed protection, pitch and bank limits. The pilot cannot exceed them | **Soft protections**: increasing force feedback and aural warnings; the pilot can override with sufficient force |
| Autothrottle/autothrust | Thrust levers **do not move** in autothrust; position indicates the mode detent | Thrust levers **move** with autothrottle commands |
| Design intent | The system should prevent the crew from exceeding the envelope, because the accident record shows crews do | The pilot must retain ultimate authority, because the record shows systems fail in unanticipated ways |

Both philosophies have been vindicated and indicted by accidents. Neither is "safer"; each fails differently, and a pilot moving between them must learn the different failure modes, not just the different switches.

### The accidents that shaped the debate

- **Air France 447** (1 June 2009, A330, Atlantic, 228 fatalities). Pitot icing caused loss of airspeed data; the autopilot and autothrust disconnected and the flight controls reverted to Alternate Law, removing the stall protection. The pilot flying made a sustained nose-up input; the aircraft stalled at cruise altitude and descended for three and a half minutes to the ocean. The BEA report's findings ran through: the ergonomics of the stall warning (which stopped when the angle of attack became so extreme the data was rejected as invalid, and restarted when the nose was lowered — inverting the cue); the non-coupled sidesticks, which meant neither the other pilot nor the returning captain could see what the pilot flying was doing; the absence of high-altitude stall training; and the startle effect. **The remedies**: mandatory high-altitude upset and stall recovery training at the *full stall* rather than at the first indication; changes to unreliable airspeed procedures; angle-of-attack awareness; the whole UPRT rulemaking.
- **Asiana 214** (6 July 2013, 777, San Francisco, 3 fatalities). A visual approach with the ILS glideslope out of service. The crew selected FLCH SPD to correct a high energy state, which commanded a climb, so the pilot flying disconnected the autopilot and retarded the thrust levers — placing the autothrottle in **HOLD**, where it would not wake up. The aircraft decayed below the approach speed and struck the seawall. The NTSB found the complexity of the 777 autoflight system, the crew's over-reliance on automation, and inadequate monitoring. The cultural-authority-gradient reading of this accident is widely repeated and was *not* the NTSB's principal finding.
- **Boeing 737 MAX — Lion Air 610 (29 October 2018, 189 fatalities) and Ethiopian 302 (10 March 2019, 157 fatalities)**. **MCAS** (Manoeuvring Characteristics Augmentation System) was added to give the MAX handling characteristics similar to the NG at high angle of attack, a consequence of the larger, further-forward engine nacelles. As certified it took input from a **single** angle of attack sensor, could command repeated, cumulative nose-down stabiliser trim with no limit on repetition, had authority far beyond what was described in the certification submission, and was not described in the flight crew manuals or differences training — deliberately, because the commercial case for the MAX rested on avoiding simulator differences training. A failed AoA vane therefore produced repeated uncommanded nose-down trim that the crews were expected to diagnose as a runaway stabiliser within seconds while managing stick shaker, unreliable airspeed and multiple warnings.

  The failures were systemic and not primarily flight-deck failures: a hazard classification that assumed crew response within four seconds; a change in MCAS authority late in development that was not re-assessed; **ODA** (Organization Designation Authorization) delegation that put Boeing employees in the certification loop with insufficient independence; and a training philosophy driven by a commercial commitment. The consequences: a 20-month worldwide grounding; the Joint Authorities Technical Review and the US Congressional investigation; the **Aircraft Certification, Safety, and Accountability Act (2020)**; a permanent change in the FAA-EASA validation relationship (EASA conducted its own review rather than accepting FAA findings); the loss of the 737 MAX 7/10 crew-alerting exemption; and, indirectly, the 2024 door plug event that reopened the whole question of Boeing's production quality system.

## 4. Startle and surprise

Distinguished carefully in the literature:

- **Startle** is a reflex — an involuntary physiological response to a sudden, intense stimulus, peaking within about 100–300 ms, with measurable effects on motor control, and a recovery of cognitive function over the following seconds.
- **Surprise** is cognitive — the mismatch between what is expected and what is perceived, which requires the person to update their mental model. Recovery from surprise takes far longer than recovery from startle, and can take tens of seconds or minutes if the event contradicts a strongly-held frame.

The operational consequence, and the reason it appears in CRM syllabi since about 2015: for a period after a surprising event, a crew's diagnostic reasoning is unreliable and their tendency is to act rather than to analyse. Training responses: deliberately unexpected scenarios in the simulator (rather than the traditional briefed "we will now do an engine failure at V1"); explicit "startle recovery" procedures that begin with stabilising the flight path and *pausing* before diagnosis; and teaching the recognition of one's own surprised state. The evidence base is thinner than the enthusiasm, and there is a genuine tension between training surprise and the requirement to brief simulator sessions.

## 5. Fatigue and flight time limitations

### The science

Fatigue is governed by three interacting factors: **time since awake** (homeostatic pressure), **circadian phase** (the two-process model's circadian component, with a **window of circadian low** roughly 0200–0600 in the acclimatised body clock), and **sleep debt** (cumulative). A fourth factor, **workload**, modulates the effect.

Empirically, 17 hours awake produces performance decrement comparable to a blood alcohol concentration of 0.05%, and 24 hours awake to about 0.10% — a comparison that comes from Dawson and Reid's 1997 *Nature* work and is heavily cited because it is comprehensible to legislators.

### Prescriptive limits

**EASA ORO.FTL Subpart FTL** (introduced 2014, applicable to commercial air transport by aeroplane from February 2016):

- Maximum basic **Flight Duty Period** from 13 hours, reduced for late report times and for the number of sectors, down to about 9 hours for a very unfavourable combination.
- **Extensions** of up to one hour (twice in seven days) and **commander's discretion** beyond that, reportable.
- **Cumulative limits**: 60 hours duty in 7 consecutive days, 110 in 14, 190 in 28; flight time 100 hours in 28 days, 900 in a calendar year, 1,000 in 12 consecutive months.
- **Minimum rest**: at least as long as the preceding duty, or 12 hours at home base, whichever is greater; 10 hours away from base with 8 hours sleep opportunity.
- **Recurrent extended recovery rest**: two local nights, extended to 36 hours including two local nights every so often.
- **Disruptive schedules**, **night duty**, **standby** and **split duty** all have their own rules.
- **Augmented crew** rules with rest facility classes 1, 2 and 3.

**FAA 14 CFR Part 117** (2014, post-Colgan 3407): flight duty period limits tabulated by report time and number of segments (from 9 to 14 hours), flight time limits of 8 or 9 hours, minimum 10 hours rest with an 8-hour sleep opportunity, and 30 consecutive hours free of duty in 168 hours. Part 117 famously **does not apply to Part 121 cargo operations** — an exclusion that has never been justified on safety grounds and that the pilot unions continue to fight.

### FRMS

A **Fatigue Risk Management System** is the performance-based alternative to prescriptive limits, permitted by ICAO Annex 6 and by both EASA and FAA rules. It requires:

- A **fatigue risk management policy** and documentation.
- **Fatigue risk management processes**: hazard identification (via fatigue reports, roster analysis, actigraphy and sleep diaries, and bio-mathematical models such as SAFE, FAID, SAFTE-FAST, or the Boeing Alertness Model), risk assessment, and mitigation.
- **Safety assurance** — measuring whether the mitigations work.
- **Promotion** — training for crews, rosterers and managers.

Bio-mathematical models are useful for comparing roster options and dangerous when treated as a compliance tool: they predict group average alertness, not an individual's fitness, and none of them models the actual sleep obtained.

The practical fatigue problems in a modern airline: **early starts** (the most-reported single factor in short-haul), **consecutive night duties**, **eastbound long-haul with short layovers**, **standby followed by a long duty**, **the window of circadian low landing**, and **commuting** — which is outside the regulator's reach and inside the fatigue risk.

## 6. The safety data ecosystem

| Source | What it is | Strength / limitation |
|---|---|---|
| **FDM / FOQA** | Flight Data Monitoring (EASA) / Flight Operational Quality Assurance (FAA). Routine, automated analysis of recorded flight data against defined event thresholds — exceedances of speed, attitude, rate of descent, approach stability, hard landings, GPWS activations, unstable approach criteria. Mandatory in EASA for aeroplanes over 27,000 kg. | Objective, continuous, complete coverage. Says *what* happened, never *why*. Must be de-identified and protected by agreement with the crew body or it will be resisted and, in some jurisdictions, unlawful. |
| **ASR / MOR** | Air Safety Reports (voluntary and mandatory occurrence reports). In the EU, **Regulation (EU) 376/2014** makes reporting mandatory for defined occurrences, requires just culture protection, and requires reporting into the European Central Repository. | Gives the *why*. Volume depends entirely on trust; a falling report rate is a warning, not a success. |
| **LOSA** | Line Operations Safety Audit. Trained observers ride the jump seat on normal flights under a peer-to-peer, de-identified, no-jeopardy agreement, coding threats, errors, undesired aircraft states and countermeasures using the TEM framework. | The only source that shows how the system works *when nothing goes wrong*. Expensive, episodic, and requires a mature culture. |
| **ADREP / ECCAIRS** | ICAO's Accident/Incident Data Reporting system and the European taxonomy and software implementing it. | Enables cross-State analysis; quality depends on States filing. |
| **ASIAS** (US) | Aviation Safety Information Analysis and Sharing — pooled, de-identified FOQA and ASAP data across US carriers plus ATC data. | The best example anywhere of industry-wide data pooling; identifies precursors no single airline could see. |
| **Data4Safety (D4S)** | The EASA equivalent programme, pooling flight data, occurrence reports, surveillance and weather data across European operators. | Newer, still building. |
| **ASAP** (US) | Aviation Safety Action Program — voluntary reporting with a formal Event Review Committee (airline, union, FAA) and enforcement protection. | The institutional embodiment of just culture in the US system. |
| **Manufacturer and OEM data** | In-service event reporting, engine health monitoring, fleet-wide trend data. | Sees across operators; commercially sensitive. |
| **IOSA / ISAGO / audits** | IATA's operational safety audit (a membership condition) and its ground operations equivalent. | Standardised, but an audit measures documented compliance, not behaviour. |
| **ASN, NTSB, AAIB, BEA databases** | Public accident and investigation records. | Free, authoritative for what they cover; only capture the visible tail of the distribution. |

## 7. Just culture

The operating definition (Reason, and codified in **Regulation (EU) 376/2014**): a culture in which front-line operators and others are **not punished for actions, omissions or decisions taken by them that are commensurate with their experience and training**, but in which **gross negligence, wilful violations and destructive acts are not tolerated**.

It is not a "no-blame" culture — no-blame is neither just nor sustainable, because it removes accountability from people who genuinely behave recklessly, and staff know it.

The practical machinery:

- A **published policy**, agreed with staff representatives, describing what will and will not attract disciplinary action.
- A **substitution test** — would another competent person, with the same training, in the same situation, with the same information, plausibly have done the same? If yes, the problem is systemic.
- A **decision algorithm** — the widely-used version asks in sequence: were the actions as intended? Under the influence of a substance? Knowing violation of a procedure that was available, workable, intelligible and correct? Would another person have behaved the same way? Is there a history?
- **Separation of the safety investigation from the disciplinary process**, with the safety investigation's material inadmissible in the latter.
- **Protection of the data** — de-identified FDM, protected ASR, and Annex 13's Chapter 5.12 protection of CVR and investigation records.

The unresolved tension is with the criminal law. Prosecutions of pilots, controllers and engineers after accidents have occurred in Italy, France, Greece, Spain, Brazil, Indonesia and elsewhere. **Regulation (EU) 376/2014** requires member states to refrain from proceedings in respect of unpremeditated or inadvertent infringements coming to their attention only through reporting, but it cannot bind a prosecutor investigating an accident. For an individual, the protection that attaches to a statement depends on whether it was made to a company safety investigator, in a mandatory occurrence report, or to a State investigator, and on the jurisdiction. **This is worth knowing before an event, not after one.**

## 8. Resilience engineering and Safety-II

The critique that produced this school: safety management as practised counts and analyses **failures**, which are rare, and infers from them how the system works. But the system produces successful outcomes millions of times a day through the same processes — adjustment, improvisation, trade-offs, and the constant reconciliation of "work as imagined" with "work as done". Studying only failures is studying a biased sample.

- **Safety-I** — safety defined as the absence of accidents; the goal is to eliminate error and variability.
- **Safety-II** (Hollnagel) — safety defined as the ability to succeed under varying conditions; the goal is to understand and support the performance variability that normally produces success, because the same variability occasionally produces failure. You cannot remove it without removing the adaptability the system depends on.

Related concepts:

- **ETTO — the Efficiency-Thoroughness Trade-Off** (Hollnagel). People and organisations continuously trade thoroughness for efficiency, and must, because resources are finite. Accidents look like ETTO failures in hindsight; so do all the successes.
- **Drift into failure** (Dekker) — systems migrate toward the boundary of safe operation under competitive and resource pressure, in small, locally rational steps, none of which is a violation. Rasmussen's dynamic safety model with its three pressures (workload, economic, and the safety boundary) is the formal version.
- **The four cornerstones of resilience** (Hollnagel): the ability to **respond** to what happens, to **monitor** what is critical, to **anticipate** developments and threats, and to **learn** from experience.
- **The new view of human error** (Dekker, *The Field Guide to Understanding Human Error*) — "human error" is not a cause but a symptom of trouble deeper in the system; it is an attribution made in hindsight, and the investigator's job is to reconstruct why the person's actions made sense to them at the time. **Hindsight bias** and **counterfactual reasoning** ("they should have…") are the enemies of learning.
- **FRAM** (Functional Resonance Analysis Method) — Hollnagel's modelling technique for describing how normal variability in coupled functions can resonate into an unwanted outcome. Intellectually attractive, operationally difficult.

The honest position: Safety-II has been more influential in the literature than in operations, partly because regulators require Safety-I artefacts (risk matrices, indicators, audits) and partly because "study your successes" is harder to operationalise than "investigate your failures". The productive synthesis in practice is EBT/CBTA — which grades competencies displayed in normal operation rather than counting failures — and LOSA, which is a Safety-II data source that predates the label.

## 9. The current top risks

### Runway excursions

The most frequent accident category in 2024, alongside tail strikes. Contributors: unstable approaches continued to landing, long/floated landings, contaminated runways and inaccurate runway condition reporting (the **Global Reporting Format**, applicable from November 2021, replaced the old and demonstrably unreliable braking action reports with a standardised **Runway Condition Code** matrix), tailwind, deep landings, late go-around decisions, and hydroplaning. Mitigations: stable approach criteria with mandatory go-around gates, FDM monitoring of approach and landing parameters, Runway Overrun Awareness and Alerting Systems (Airbus ROPS, Honeywell SmartLanding/SmartRunway), and the GRF.

**IATA, CANSO and ACI launched a joint runway safety initiative on 28 July 2026** targeting **runway incursions** specifically, with three workstreams: improving safety reporting and data collection from incidents, near misses and frontline observations; strengthening local runway safety teams; and sharing effective practices across similar operating environments. It builds on ICAO's **GAPPRI** (Global Action Plan for the Prevention of Runway Incursions). IATA's Nick Careen noted that "several recent incursions have been fatal" — a reference to the 2024 Haneda collision and the 2023–2025 series of serious US incursions.

### Loss of control in flight (LOC-I)

Historically the largest killer by fatalities. Causes: aerodynamic stall (particularly at high altitude), spatial disorientation, icing, mishandled system failures, control system malfunctions, and somatogravic illusion in the go-around. Mitigations: the UPRT rulemaking, angle-of-attack awareness, the simulator model extensions in **CS-FSTD(A) Issue 2**, and the EBT emphasis on manual flight path management as a graded competency.

### CFIT

**Zero CFIT accidents in 2024** — the clearest single success story in aviation safety, attributable almost entirely to **EGPWS/TAWS** (Bateman's terrain database and forward-looking terrain avoidance, mandated from the late 1990s) and to the elimination of non-precision approaches in favour of stabilised constant-descent-angle procedures. The residual risk is at aerodromes without approach procedures, in non-precision approaches flown with obsolete techniques, and in cases where the terrain database or the position source is wrong — which links directly to the next item.

### GNSS jamming and spoofing

This is the live problem of 2024–2026 and there is no complete mitigation.

- **Jamming** denies the GNSS signal. **Spoofing** transmits a false but plausible signal, causing the receiver to compute a wrong position or time.
- Affected regions reported by operators and by EASA since 2022–2023: the **eastern Mediterranean and Middle East** (particularly around Cyprus, Israel, Lebanon, Iraq and Iran), the **Black Sea and Caucasus**, the **Baltic** (Kaliningrad and the Gulf of Finland), and areas around **Ukraine** and **Russia**.
- Operational effects reported: loss of RNP/RNAV capability and reversion to conventional navigation; **inertial reference system contamination**, where a spoofed position is accepted by the IRS/GPIRS hybrid and the position error persists after the aircraft leaves the affected area, in some cases requiring an IRS realignment on the ground; **spurious EGPWS "PULL UP" warnings** caused by a false position over terrain; **spurious TCAS and windshear alerts**; **loss of ADS-B integrity**; and **clock/time errors** that have in reported cases invalidated the ADS-B position and, in a widely-reported incident, corrupted the aircraft's time reference badly enough to affect systems that depend on it.
- Regulatory response: **EASA Safety Information Bulletin 2022-02** and its revisions, EASA/IATA workshops and a joint call to action, ICAO Assembly and Council attention, and operator-level mitigations: awareness briefings, procedures for recognising and responding to spoofing, retention of conventional navigation capability (VOR/DME/ILS raw data monitoring and cross-checking), careful management of IRS alignment, and reporting. **[needs-verification on the exact SIB numbers, revision dates and the workshop dates — the EASA pages returned 404 to automated retrieval in this pass.]**

> ⚠️ The structural problem is that civil GNSS signals are unauthenticated by design. Galileo's **OSNMA** (Open Service Navigation Message Authentication) is the first operational authentication service and addresses spoofing but not jamming, and requires receiver upgrades that will take a decade to propagate through the fleet.

### Conflict zone overflight

MH17 (17 July 2014) demonstrated that the Chicago Convention has no mechanism to close airspace over the objection of the State that controls it. Since 2022 the closures and risk areas have multiplied: Ukrainian and Russian airspace, Belarus, Afghanistan, Iran and Iraq at various times, Israel and Lebanon, Yemen and the Red Sea approaches, Libya, Sudan, Mali and the Sahel. The mechanisms available:

- **State-issued NOTAMs and prohibitions** (FAA SFARs and NOTAMs, UK DfT and CAA restrictions, EASA **Conflict Zone Information Bulletins**, the French DGAC and German LBA equivalents).
- **Operator risk assessment**, required by EASA under ORO.GEN and the associated AMC on operations in airspace with security risk. The operator must do its own assessment and cannot simply rely on the absence of a NOTAM.
- **Insurance** — the war-risk market prices what regulators do not prohibit, and an insurer's exclusion is often the binding constraint in practice.

The commercial consequence is substantial: the closure of Russian airspace to European, US and several Asian carriers since 2022 added hours and fuel to Europe–Northeast Asia routes and gave Chinese carriers a structural cost advantage on those routes. Middle East routings around closed airspace have similar effects, and the June 2026 Middle East traffic collapse shows how quickly the exposure becomes financial.

### Other live areas

- **Lithium batteries** — in cargo and in the cabin. Thermal runaway is not extinguishable by the halon systems in a cargo hold; the ICAO Technical Instructions and the IATA DGR restrict shipment of lithium cells, and undeclared shipments are a known and unquantified risk.
- **Cabin safety and unruly passengers** — rising incident rates, with the Tokyo Convention's Montreal Protocol 2014 as the legal response.
- **Contaminated air / fume events** — contested, with a substantial pilot-body concern and an inconclusive regulatory evidence base.
- **Drones and UAS integration** — near-miss reporting is high and the collision consequence for a transport aircraft is poorly characterised.
- **Cybersecurity** — the airworthiness security standards (DO-326A/ED-202A) now apply to type design; the operational side (EASA Part-IS, applicable from 2025–2026) requires an information security management system in aviation organisations.
- **Mental health** — Germanwings 9525 (2015) produced the two-person cockpit rule (subsequently relaxed in many operators), mandatory psychological assessment of flight crew before line flying (**Regulation (EU) 2018/1042**, the same instrument that introduced support programmes and psychoactive substance testing), and **peer support programmes**, which are now the more evidence-based intervention.

## Sources

- [IATA — Safety Report shows continued improvement (2024 data, 26 February 2025)](https://www.iata.org/en/pressroom/2025-releases/2025-02-26-01/)
- [IATA — Annual Safety Report (62nd edition)](https://www.iata.org/en/publications/safety-report/)
- [IATA — IATA, CANSO and ACI Launch Joint Runway Safety Initiative (28 July 2026)](https://www.iata.org/en/pressroom/2026-releases/07-28-iata-canso-aci-launch-joint-runway-safety-initiative/)
- [Wikipedia — Threat and error management](https://en.wikipedia.org/wiki/Threat_and_error_management)
- [Wikipedia — Convention on International Civil Aviation](https://en.wikipedia.org/wiki/Convention_on_International_Civil_Aviation)

## Open questions

- **2025 safety statistics** (IATA Annual Safety Report 62nd edition) were not retrieved; only the 2024 figures are verified.
- **GNSS interference**: the EASA Safety Information Bulletin number (SIB 2022-02 and revisions), the dates of the EASA/IATA workshops, and any quantified incident counts are unverified — EASA's relevant pages returned 404 to automated retrieval on 2026-08-25.
- **The Dawson and Reid alcohol-equivalence figures** are quoted from the widely-cited 1997 *Nature* paper but not verified in this pass.
- **EASA ORO.FTL numerical limits** are quoted from working knowledge and should be checked against the current Easy Access Rules for Flight Time Limitations.
- **CRM generation taxonomy** is Helmreich, Merritt and Wilhelm's; the sixth and seventh generations are the author's extension of their framework, not their published terminology.
- Accident narratives are summarised from the official reports (BEA for AF447, NTSB for Asiana 214, KNKT and EAIB plus the JATR and US Congressional reports for the MAX) but the reports themselves were not fetched in this pass.
