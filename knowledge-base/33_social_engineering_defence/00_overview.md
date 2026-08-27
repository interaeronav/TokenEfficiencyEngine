---
id: sedef.overview
title: Social engineering defence — overview and domain map
domain: 33_social_engineering_defence
tags: [social-engineering, phishing, security-awareness, human-risk, bec, threat-landscape, defensive-security, ciso, breach-statistics]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "2024 Internet Crime Report", url: "https://www.ic3.gov/AnnualReport/Reports/2024_IC3Report.pdf", publisher: "FBI Internet Crime Complaint Center (IC3)", accessed: 2026-08-25}
  - {title: "2025 Data Breach Investigations Report", url: "https://www.verizon.com/business/resources/reports/2025-dbir-data-breach-investigations-report.pdf", publisher: "Verizon Business", accessed: 2026-08-25}
  - {title: "Data Breach Investigations Report (landing page, 2026 edition)", url: "https://www.verizon.com/business/resources/reports/dbir/", publisher: "Verizon Business", accessed: 2026-08-25}
  - {title: "Phishing Activity Trends Report, Q4 2024", url: "https://docs.apwg.org/reports/apwg_trends_report_q4_2024.pdf", publisher: "Anti-Phishing Working Group (APWG)", accessed: 2026-08-25}
  - {title: "ENISA Threat Landscape 2024", url: "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2024", publisher: "ENISA", accessed: 2026-08-25}
  - {title: "Phishing attacks: defending your organisation", url: "https://www.ncsc.gov.uk/guidance/phishing", publisher: "UK National Cyber Security Centre", accessed: 2026-08-25}
  - {title: "Social engineering (security)", url: "https://en.wikipedia.org/wiki/Social_engineering_(security)", publisher: "Wikipedia", accessed: 2026-08-25}
related: [sedef.psychology, sedef.taxonomy, sedef.lifecycle, sedef.technical_controls, sedef.human_controls, sedef.resilience, sedef.cases, sedef.ai_landscape, sedef.personal]
---

# Social engineering defence — overview and domain map

**Summary.** Social engineering is the use of psychological influence — not technical exploitation — to make a person take an action that harms them or their organisation: revealing a credential, approving a payment, plugging in a device, or holding a door. It is the single most reliable route into an organisation, because it targets the one component that cannot be patched. This domain is written for **defenders**: people who must recognise these attacks, train staff against them, design controls that fail safe, and respond when something gets through. It describes attack *patterns, psychology and indicators* at the level of NIST, CISA, ENISA and NCSC guidance and the peer-reviewed literature. It deliberately does **not** contain operational attack material — no ready-to-send lures, no reconnaissance playbooks, no evasion techniques. Where a technique must be named so defenders can recognise it, it is described from the victim's side and paired with detection and control.

> ⚠️ **Defensive framing, stated explicitly.** Everything in this domain exists to help an individual, a family or a business *resist* manipulation. If you are reading a section and it starts to read like an operator's manual rather than a threat briefing, that is a defect in the writing — the correct form of any such passage is "here is what it looks like from the receiving end, here is how you detect it, here is the control that stops it."

## Key facts

| Measure | Figure | Source and period |
|---|---|---|
| Complaints to the FBI's IC3 | 859,532 | IC3 Internet Crime Report, calendar year 2024 |
| Total reported losses, IC3 | **US$16.6 billion** | IC3, 2024 |
| Business email compromise (BEC) | 21,442 complaints, **US$2.77 billion** | IC3, 2024 |
| Phishing / spoofing complaints | 193,407 | IC3, 2024 |
| Investment fraud losses (incl. "pig butchering") | US$6.57 billion | IC3, 2024 |
| Tech support fraud losses | US$1.46 billion | IC3, 2024 |
| Victims aged 60+ | 147,127 complaints, **US$4.885 billion** | IC3, 2024 |
| Breaches involving the **human element** | **60%** (down from 61%) | Verizon DBIR 2025 |
| Breaches involving social engineering | 22% | Verizon DBIR 2025 |
| Initial access via credential abuse | 22% | Verizon DBIR 2025 |
| Breaches involving a third party | 30% (roughly double the prior year) | Verizon DBIR 2025 |
| Ransomware presence in breaches | 44%; median ransom paid US$115,000 | Verizon DBIR 2025 |
| DBIR 2025 dataset | 22,052 incidents, 12,195 confirmed breaches, 139 countries | Verizon DBIR 2025 |
| Phishing attacks observed in one quarter | 989,123 (Q4 2024, up from 932,923 in Q3) | APWG Phishing Activity Trends, Q4 2024 |
| Average wire transfer requested in BEC | US$128,980 (Q4 2024), vs US$67,145 in Q3 2024 | APWG, Q4 2024 |
| Most-phished sectors | SaaS/webmail 23.3%, social media 22.5%, financial 11.9%, e-commerce 10.9% | APWG, Q4 2024 |

## 1. What social engineering actually is

The working definition used across the security literature is short: **social engineering is the use of psychological pressure or deception to induce a person to perform an action or disclose information they would not otherwise disclose.** Two features distinguish it from other attack classes.

First, **the vulnerability is a feature, not a bug.** Trust, deference to authority, helpfulness, reciprocity and the desire to avoid conflict are the properties that make organisations function. An employee who refuses every unusual request, questions every executive, and never helps a stranger is not a secure employee — they are an unemployable one. This is why "just train people to be suspicious" fails as a strategy, and why the whole of file `04` exists: the durable defences are the ones that survive a trusting human.

Second, **the attack is delivered through legitimate channels.** A BEC email carries no malware; a vishing call carries no payload; a person following you through a door triggers no alert. There is frequently nothing for a signature-based control to find. ENISA's 2024 Threat Landscape notes precisely this about BEC — that it is "particularly challenging to detect because [it] seldom involve[s] malware."

Both features push defence toward the same conclusion: you defend against social engineering primarily by **changing what a deceived person is able to do**, and only secondarily by trying to reduce the rate of deception.

## 2. Why it dominates the breach statistics

Three structural reasons, all evidenced:

**(a) It is the cheapest reliable initial access.** Verizon's 2025 DBIR puts the human element in 60% of breaches and credential abuse at 22% of initial access vectors. Exploiting a software vulnerability requires a vulnerability to exist, to be reachable, and to remain unpatched; asking someone for their password requires only an email. Note the 2025 DBIR's counter-trend — vulnerability exploitation rose 34% year on year to 20% of initial access — which is a reminder that the mix shifts and that a defence programme weighted entirely to phishing is unbalanced.

**(b) Credentials are the universal skeleton key in a cloud estate.** When corporate data lives in SaaS platforms reachable from any browser, a valid username, password and one-time code is functionally equivalent to physical presence in the office. APWG's sector data reflects this: SaaS and webmail is the most-phished category at 23.3% of attacks in Q4 2024.

**(c) The payment fraud variants have an extraordinary return on effort.** BEC accounted for US$2.77 billion of reported US losses in 2024 across only 21,442 complaints — an average well over US$100,000 per complaint, consistent with APWG's Q4 2024 observed average wire request of US$128,980. No malware development is required.

Add the third-party dimension — 30% of breaches in the 2025 DBIR involved a third party — and the picture is of an attack class that scales across supply chains as easily as it scales across inboxes.

## 3. The scale of harm, in dated figures

Use dated figures and name the source; do not repeat undated round numbers.

- **United States, 2024 (IC3).** 859,532 complaints, US$16.6 billion reported losses. The largest single category by loss was investment fraud at US$6.57 billion, most of which is relationship-based confidence fraud rather than technical intrusion. Tech support fraud reached US$1.46 billion. Victims aged 60 and over reported US$4.885 billion in losses across 147,127 complaints — roughly 29% of all reported loss from about 17% of complaints, which is the clearest evidence in the public data that the elderly are targeted and lose more per incident.
- **Global breach data, 2025 (Verizon DBIR).** 22,052 incidents and 12,195 confirmed breaches from 139 countries; 60% involved the human element; 22% involved social engineering; ransomware appeared in 44% of breaches with a median paid ransom of US$115,000 and 64% of victim organisations refusing to pay.
- **Phishing volume, Q4 2024 (APWG).** 989,123 distinct phishing attacks observed in the quarter, continuing a rise from 877,536 in Q2 and 932,923 in Q3. Gift-card demands made up 49% of BEC cash-out attempts; payroll diversion 10%; cryptocurrency demands rose to 12% from 2.7% in Q3.
- **Europe, 2024 (ENISA).** ENISA's Threat Landscape 2024 (published 19 September 2024) identifies seven prime threats, with availability threats, ransomware and threats against data at the top, and records a "sharp increase" in BEC, a surge in QR-code phishing ("quishing"), and continuing adversary-in-the-middle attacks that defeat one-time-code MFA.
- **2026 edition, early figures.** The DBIR landing page for the 2026 edition (covering 1 November 2024 – 31 October 2025) headlines 31% of breaches beginning with a software vulnerability, ransomware in 48% of breaches, 15 attack techniques being augmented by generative AI, and mobile devices showing click rates 40% higher than desktop. These are landing-page summary figures; the full-report context should be checked before they are quoted in a board paper.

**Regional caveat.** Comparable authoritative loss figures for Southern Africa are much thinner. Interpol publishes periodic African Cyberthreat Assessment reports, and South Africa's SABRIC publishes annual banking crime statistics; neither was retrievable at the time of writing (see Open questions). Treat any single figure for "cybercrime losses in South Africa" with suspicion unless you can trace it to SABRIC, the South African Reserve Bank, or Interpol directly.

## 4. The defender's mental model

Four propositions organise everything that follows.

**Proposition 1 — Assume deception succeeds.** The NCSC's position, argued directly in its December 2022 post by Dave Chismon, is that users "frequently *need* to click on links from unfamiliar domains to do their job, and being able to spot a phish is **not** their job." The design goal is therefore not zero clicks; it is that a click is survivable.

**Proposition 2 — Defend in layers.** The NCSC's four-layer model is the cleanest public articulation: (1) make it difficult for attackers to reach your users; (2) help users identify and report suspected phishing; (3) protect the organisation from the effects of undetected phishing; (4) respond quickly to incidents. Layers 1, 3 and 4 are technical and procedural; only layer 2 is training. Programmes that consist almost entirely of layer 2 are the common failure mode.

**Proposition 3 — Make the high-consequence actions require more than one deceived person.** Almost every catastrophic social-engineering loss in file `07` traces back to a single person being able to do something irreversible alone: approve a payment, reset an MFA factor, grant an admin role. Segregation of duties, callback verification on a known-good number, and dual authorisation are unglamorous and extremely effective.

**Proposition 4 — Reporting is a detection capability, not a compliance box.** Lain, Kostiainen and Čapkun's 15-month study of over 14,000 employees (IEEE S&P 2022) showed for the first time at scale that employees acting as a collective detection sensor is practical in a large organisation, giving rapid campaign detection at manageable operational cost. That capability is destroyed by punishing people who click. This is the single most consequential cultural point in the domain.

## 5. Domain map

| File | Covers | Use it when |
|---|---|---|
| `00_overview.md` | This file: definitions, scale, framing, map | Orienting; briefing a board on why this matters |
| `01_the-psychology.md` | Influence principles, obedience and conformity research, heuristics, truth-default theory, replication status, why senior people are vulnerable | Designing training content; explaining *why* a smart person fell for it |
| `02_attack-taxonomy.md` | Recognition-oriented catalogue of attack types, victim experience, indicators, typical loss, controls | Building a threat register; writing awareness material; triage |
| `03_the-attack-lifecycle-from-a-defenders-view.md` | Kill-chain view, OSINT exposure inventory, trust/pressure/action/exfiltration phases, enumerated interruption points | Threat modelling; deciding where to spend control budget |
| `04_technical-controls.md` | SPF/DKIM/DMARC, gateways and their limits, phishing-resistant MFA, conditional access, DNS/web filtering, endpoint, payment controls, PAM, zero trust, detection engineering, IR playbooks | Control design and architecture review |
| `05_human-controls-and-training.md` | Programme design, the honest evidence on training and simulations, ethics, just-in-time interventions, reporting culture, metrics beyond click rate | Building or fixing an awareness programme |
| `06_organisational-resilience.md` | Policy, segregation of duties, vendor management, JML hygiene, helpdesk identity proofing, executive protection, brand/domain monitoring, takedowns, insurance, regulatory reporting, BCP | Governance layer; audit preparation |
| `07_notable-cases.md` | Documented incidents with verified facts, the human control that failed, and what changed | Case studies for training; making the risk concrete |
| `08_ai-and-the-new-threat-landscape.md` | GenAI effects on lures and scale, voice/video deepfakes and detection status, AI-assisted OSINT, prompt injection and the social engineering of AI agents, agentic risks, defensive AI | Planning for 2026 and beyond; assessing AI agent deployments |
| `09_personal-protection.md` | Individual and family guide: accounts, phone/SIM, financial controls, family verification, exposure reduction, first hour after a compromise, reporting channels by country | Personal use; briefing family; helping a victim |
| `10_resources-and-further-reading.md` | Annotated register of books, standards, free training, annual reports, certifications, research venues | Building a reading list or a curriculum |

## 6. Scope boundaries of this domain

**In scope:** recognition, psychology, indicators, controls, governance, incident response, training design, case analysis, personal protection.

**Out of scope, deliberately:** phishing email templates or pretext scripts in usable form; target reconnaissance methodology; techniques for evading named security products; instructions for cloning any specific person's voice or face; step-by-step procedures for defrauding a named institution. Where a public case involved such a technique, this domain records *that it happened and what the organisation changed*, not how to repeat it.

**A note on the classic literature.** Much of the best-known writing in this field — Mitnick's *The Art of Deception*, Hadnagy's *Social Engineering* — is written from the operator's chair. It remains genuinely useful for defenders because it explains what the attacker is thinking, and it is included in file `10` with that caveat attached. Read it as a threat briefing, not a manual.

## Sources

- [2024 Internet Crime Report (IC3)](https://www.ic3.gov/AnnualReport/Reports/2024_IC3Report.pdf) — FBI Internet Crime Complaint Center
- [2025 Data Breach Investigations Report](https://www.verizon.com/business/resources/reports/2025-dbir-data-breach-investigations-report.pdf) — Verizon Business
- [DBIR landing page (2026 edition summary figures)](https://www.verizon.com/business/resources/reports/dbir/) — Verizon Business
- [APWG Phishing Activity Trends Report, Q4 2024](https://docs.apwg.org/reports/apwg_trends_report_q4_2024.pdf) — Anti-Phishing Working Group
- [ENISA Threat Landscape 2024](https://www.enisa.europa.eu/publications/enisa-threat-landscape-2024) — ENISA
- [ENISA Threat Landscape 2024 (full report PDF)](https://www.enisa.europa.eu/sites/default/files/2024-11/ENISA%20Threat%20Landscape%202024_0.pdf) — ENISA
- [Phishing attacks: defending your organisation](https://www.ncsc.gov.uk/guidance/phishing) — UK NCSC
- [Telling users to "avoid clicking bad links" still isn't working](https://www.ncsc.gov.uk/blog-post/telling-users-to-avoid-clicking-bad-links-still-isnt-working) — UK NCSC, 20 December 2022
- [Phishing in Organizations: Findings from a Large-Scale and Long-Term Study](https://arxiv.org/abs/2112.07498) — Lain, Kostiainen, Čapkun, IEEE S&P 2022
- [Social engineering (security)](https://en.wikipedia.org/wiki/Social_engineering_(security)) — Wikipedia

## Open questions

- **Interpol African Cyberthreat Assessment figures could not be retrieved** (interpol.int returned HTTP 503 during research). Regional loss figures for Africa in this domain are therefore absent rather than estimated. Verify against the current Interpol report before quoting.
- **SABRIC annual crime statistics** (South Africa) exist and are referenced on sabric.co.za, but the specific figures were not retrievable. Obtain the current SABRIC Annual Crime Statistics Report before citing South African banking fraud numbers.
- **2026 DBIR detailed figures** — only landing-page headline numbers were available. The human-element percentage for the 2026 edition is not yet recorded here.
- **IC3 2025 Internet Crime Report** — if published by the time of reading, all 2024 figures above should be refreshed.
- WebSearch was unavailable during the construction of this domain; all sources were fetched directly by URL. A small number of intended sources (CISA PDF fact sheets behind 403s, some news archives behind robots.txt) could not be read and are noted per-file.
