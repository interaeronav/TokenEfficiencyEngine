---
id: sedef.resources
title: Resources and further reading — an annotated register
domain: 33_social_engineering_defence
tags: [reading-list, books, standards, nist, iso-27001, mitre-attack, mitre-engage, training, certifications, annual-reports, research-venues, dbir, ic3, apwg, enisa]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "NIST SP 800-50 Rev. 1", url: "https://csrc.nist.gov/pubs/sp/800/50/r1/final", publisher: "NIST", accessed: 2026-08-25}
  - {title: "ISO/IEC 27001", url: "https://www.iso.org/standard/27001", publisher: "ISO", accessed: 2026-08-25}
  - {title: "MITRE ATT&CK T1566 Phishing", url: "https://attack.mitre.org/techniques/T1566/", publisher: "MITRE", accessed: 2026-08-25}
  - {title: "MITRE Engage", url: "https://engage.mitre.org/", publisher: "MITRE", accessed: 2026-08-25}
  - {title: "OUCH! Newsletter", url: "https://www.sans.org/newsletters/ouch/", publisher: "SANS Institute", accessed: 2026-08-25}
  - {title: "Phishing Quiz", url: "https://phishingquiz.withgoogle.com/", publisher: "Jigsaw / Google", accessed: 2026-08-25}
  - {title: "The Art of Deception", url: "https://en.wikipedia.org/wiki/The_Art_of_Deception", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Robert Cialdini", url: "https://en.wikipedia.org/wiki/Robert_Cialdini", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Timothy R. Levine", url: "https://en.wikipedia.org/wiki/Timothy_R._Levine", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "OWASP Top 10 for LLM Applications 2025", url: "https://genai.owasp.org/llm-top-10/", publisher: "OWASP GenAI Security Project", accessed: 2026-08-25}
  - {title: "NIST AI 100-2 E2025", url: "https://csrc.nist.gov/pubs/ai/100/2/e2025/final", publisher: "NIST", accessed: 2026-08-25}
  - {title: "Cyber Security Toolkit for Boards", url: "https://www.ncsc.gov.uk/collection/board-toolkit", publisher: "UK NCSC", accessed: 2026-08-25}
related: [sedef.overview, sedef.psychology, sedef.human_controls]
---

# Resources and further reading — an annotated register

**Summary.** An annotated register of what to read, which standards to work from, which free training to use, which reports to track annually, which certifications signal what, and where the research is published. Annotations say what each item is *good for* and, where relevant, what to be careful about. Two cautions run through the list: several foundational books were written from the attacker's chair and should be read as threat briefings rather than manuals; and several foundational psychology books contain findings that have not replicated well and should be read with file `01` §5 in hand.

## Key facts

| Category | Track these |
|---|---|
| Annual reports | Verizon DBIR, FBI IC3 Internet Crime Report, APWG Phishing Activity Trends (quarterly), ENISA Threat Landscape, Proofpoint State of the Phish |
| Core standards | NIST SP 800-50 Rev. 1 (Sept 2024), NIST SP 800-53 Rev. 5 (AT family), ISO/IEC 27001:2022 A.6.3, NIST SP 800-63 (identity), NIST AI 100-2 E2025 |
| Frameworks | MITRE ATT&CK (T1566 and Initial Access), MITRE Engage, OWASP Top 10 for LLM Applications 2025 |
| Free training | CISA, UK NCSC, SANS *OUCH!*, Jigsaw/Google Phishing Quiz |
| Research venues | IEEE S&P, USENIX Security, ACM CCS, NDSS, SOUPS, APWG eCrime |

---

## 1. Books

### 1.1 On influence and persuasion

**Robert Cialdini, *Influence: The Psychology of Persuasion* (1984; extensively revised editions since).** The foundational text. Six principles — reciprocity, commitment and consistency, social proof, authority, liking, scarcity — drawn from three years of participant observation inside used-car dealerships, fundraising organisations and telemarketing firms, combined with the experimental literature. Over five million copies sold, translated into 41 languages.
*Good for:* a diagnostic vocabulary you will use in every incident review.
*Careful:* it is a synthesis, not a single validated study. Some underlying research is robust, some is from an era of small samples and flexible analysis. Do not present each principle as though a single decisive experiment stands behind it.

**Robert Cialdini, *Pre-Suasion* (2016).** Adds the seventh principle, **unity** — the more we identify with others, the more we are influenced by them — and argues that the moment *before* a message matters as much as the message. Useful for understanding shared-identity pretexts and insider recruitment. The evidential base for unity specifically is thinner than for the original six.

**Daniel Kahneman, *Thinking, Fast and Slow* (2011).** The canonical popular account of dual-process thinking, heuristics and biases, and (with Tversky) prospect theory — which underlies every loss-framed lure in this domain.
*Careful:* the book's chapter on priming rests on literature that has largely failed replication, and Kahneman himself publicly acknowledged this. Read the heuristics-and-biases and prospect-theory material as strong; read the social-priming material as historical.

**Dan Ariely, *Predictably Irrational* (2008).** Accessible treatment of systematic irrationality — anchoring, the zero-price effect, the cost of social versus market norms.
*Careful:* several of Ariely's own headline results, particularly on dishonesty and signing-at-the-top, have been the subject of serious data-integrity controversy and failed replication. Use the book for intuition, not for citations.

### 1.2 On deception and trust

**Timothy R. Levine, *Duped* (University of Alabama Press).** The scholarly source for **truth-default theory** and the **veracity effect**. Levine is Distinguished Professor and Chair of Communication Studies at the University of Oklahoma, with research funded by the NSF, the Department of Defense and the FBI.
*Good for:* the most important argument in the whole field — that people default to belief, that human lie detection is near chance, and therefore that "train people to detect deception" is not a viable control. If you read one book to change how you design an awareness programme, read this one.

**Bruce Schneier, *Liars and Outliers: Enabling the Trust That Society Needs to Thrive* (2012).** Why societies need both trust and defectors, and how security systems are really mechanisms for managing the trade-off. The best available framing for *why* an organisation cannot simply eliminate trust.

**Bruce Schneier, *Secrets and Lies: Digital Security in a Networked World* (2000).** Now historical in its technology but still the clearest statement of security as a process rather than a product, and of the primacy of people over cryptography.

### 1.3 From the attacker's chair — read as threat briefings

> ⚠️ The following are written from the operator's perspective. They are genuinely valuable for defenders because they explain attacker reasoning, and they are widely used in professional training. Read them for **recognition**, not for method, and do not use them as the model for your own written material.

**Kevin Mitnick with William L. Simon, *The Art of Deception* (2002).** Fictional-but-plausible scenarios of social engineering, each followed by an analysis of the vulnerability exploited and practical countermeasures; the closing section sets out a defensive strategy and business plan. The structure is explicitly pedagogical and defensive in intent.
*Historical framing note:* the scenarios reflect the corporate telephony, fax and physical-office world of the late 1990s. The *psychology* has not dated at all; the *setting* has completely.

**Kevin Mitnick with William L. Simon, *The Art of Intrusion* (2005).** Third-party accounts of real intrusions. Same caveats, similar value.

**Christopher Hadnagy, *Social Engineering: The Science of Human Hacking* and related works.** The most systematic modern treatment, widely used in the professional penetration-testing community.
*Defensive-reading caveat:* considerably more operational than Mitnick, and a substantial portion is method rather than analysis. If you are building defensive material, take the taxonomy and the psychology and leave the methodology. Organisations should be deliberate about who has it on the shelf and why.

**David Maurer, *The Big Con* (1940).** The classic ethnography of confidence artistry, source of the ten-stage model of the long con. Historical, beautifully written, and startlingly current — the "convincer" and the manufactured crisis are visible in every modern investment fraud.

### 1.4 Adjacent and worth the time

**Maria Konnikova, *The Confidence Game* (2016).** Journalistic and psychological account of why victims believe, written with unusual sympathy for the victim — which matters, because contempt for victims is the main obstacle to a reporting culture.
**Kevin Poulsen, *Kingpin* (2011)** and **Andy Greenberg, *Sandworm* (2019).** Narrative accounts that make the operational reality concrete for non-specialist audiences; useful for executive briefings.

---

## 2. Standards and frameworks

**NIST SP 800-50 Rev. 1, *Building a Cybersecurity and Privacy Learning Program*** (published 12 September 2024; supersedes SP 800-50 of October 2003 and SP 800-16 of April 1998). The current authority for awareness programme design. Lifecycle approach, explicit focus on behavioural change and security culture rather than knowledge transfer, and a requirement for metrics and evaluation built into the programme. Written for federal agencies but scoped to be usable by organisations of any size. **Start here** if you are designing a programme.

**NIST SP 800-53 Rev. 5 — Awareness and Training (AT) control family.** The control catalogue entries you will be assessed against, including AT-2 Literacy Training and Awareness with enhancements addressing insider threat, social engineering and social mining, and advanced persistent threat. *Verify the exact enhancement numbering against the catalogue before quoting it in an audit response.*

**ISO/IEC 27001:2022** (third edition, published 25 October 2022). Annex A control **A.6.3, "Information security awareness, education and training"**, sits in the people-controls theme of the restructured Annex A. Pair with ISO/IEC 27002:2022 for implementation guidance. *Confirm the Annex A structure against the standard text.*

**NIST SP 800-63 Digital Identity Guidelines.** The authority for identity proofing and authenticator assurance levels — directly relevant to the helpdesk verification problem (file `06` §5) and to choosing phishing-resistant authenticators.

**MITRE ATT&CK.** For this domain, the Initial Access tactic and specifically **T1566 Phishing** with sub-techniques T1566.001 (attachment), .002 (link), .003 (via service) and .004 (voice), plus mitigations M1017 user training, M1021 restrict web-based content, M1031 network intrusion prevention, M1047 audit, M1049 antivirus/antimalware and M1054 software configuration. Use it to map your detections and to speak a common language with your SOC and your vendors.

**MITRE Engage.** A framework for planning and discussing **adversary engagement** — denial, deception and engagement operations — organised as Goals, Approaches and Activities across Prepare, Operate and Understand phases, with a Matrix, Playbook, Process, Community, Standards and Mindset. Its framing is useful even if you never deploy deception: "the defender must be right every time; in an engagement operation the adversary only needs to be wrong once."

**OWASP Top 10 for LLM Applications 2025.** LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure, LLM03 Supply Chain, LLM04 Data and Model Poisoning, LLM05 Improper Output Handling, LLM06 Excessive Agency, LLM07 System Prompt Leakage, LLM08 Vector and Embedding Weaknesses, LLM09 Misinformation, LLM10 Unbounded Consumption. Essential if your organisation deploys AI agents (file `08` §4).

**NIST AI 100-2 E2025, *Adversarial Machine Learning: A Taxonomy and Terminology of Attacks and Mitigations*** (24 March 2025). The formal vocabulary for adversarial ML, covering ML methods, attack lifecycle stages, attacker characteristics and mitigations.

**UK NCSC guidance.** The *Phishing attacks: defending your organisation* collection (four-layer defence model), the *Cyber Security Toolkit for Boards* (v3.0, 30 March 2023, reviewed 8 April 2025), and the *Machine Learning Principles* collection (22 May 2024). NCSC guidance is unusually honest about the limits of user training and is the best free counterweight to vendor messaging.

**CISA guidance.** *Phishing Guidance: Stopping the Attack Cycle at Phase One* (joint with NSA, FBI and MS-ISAC, October 2023), the *Implementing Phishing-Resistant MFA* fact sheet (October 2022), and the *Implementing Number Matching in MFA Applications* fact sheet.

---

## 3. Free training and awareness material

**SANS *OUCH!* newsletter.** A free monthly security-awareness newsletter from SANS Security Awareness, written for a non-technical audience, developed through a review process involving community volunteers, translators and subject-matter experts, and available in multiple languages. The single best free vehicle for a monthly awareness drumbeat, especially for small organisations. *Check the current licence terms with SANS before redistributing internally.*

**Jigsaw / Google Phishing Quiz** (phishingquiz.withgoogle.com, also g.co/phishingquiz). An interactive quiz asking users to classify messages as legitimate or phishing, with explanation after each. Excellent as an *experience* — most people score worse than they expect, which is exactly the point of file `01` §8 — but treat the result as a demonstration of difficulty, not as an assessment of individuals.

**CISA free resources.** Awareness materials, tabletop exercise packages (CISA Tabletop Exercise Packages), and the Secure Our World campaign. Public-sector-oriented but freely reusable.

**UK NCSC free training.** The *Top Tips for Staff* e-learning package, *Cyber Action Plan*, *Exercise in a Box* (free tabletop and technical exercise service including phishing scenarios), and the *Cyber Essentials* scheme material. **Exercise in a Box** is the most under-used free resource in this list for small and medium organisations.

**National CSIRT material.** For Southern African readers, Nam-CSIRT (Namibia) publishes advisories; SABRIC publishes risk alerts and consumer awareness material for South Africa; SAFPS runs the **Yima** scam-prevention toolbox with a public reporting route.

---

## 4. Reports to track annually

**Verizon Data Breach Investigations Report (DBIR).** Annually, usually April–May. The 2025 edition analysed 22,052 incidents and 12,195 confirmed breaches across 139 countries. Track: human element percentage, social engineering share, initial access vector mix, third-party involvement, ransomware prevalence. The 2026 edition covers 1 November 2024 – 31 October 2025.
*Good for:* the only large, consistently-methodologised, multi-source breach dataset. *Careful:* the corpus is contributor-dependent; year-on-year shifts sometimes reflect contributor changes rather than threat changes, which the DBIR itself flags.

**FBI IC3 Internet Crime Report.** Annually, usually March–April. 2024: 859,532 complaints, US$16.6 billion reported losses, BEC US$2.77 billion, investment fraud US$6.57 billion, tech support fraud US$1.46 billion, victims aged 60+ US$4.885 billion. Also publishes a separate **Elder Fraud Report** and per-state reports.
*Careful:* US-centric and complaint-based, so it undercounts substantially; use it for trend and relative magnitude, not for global totals.

**APWG Phishing Activity Trends Report.** Quarterly. Q4 2024: 989,123 observed phishing attacks; sector shares (SaaS/webmail 23.3%, social media 22.5%, financial 11.9%, e-commerce 10.9%); average BEC wire request US$128,980. The best public series for phishing *volume* and BEC cash-out methods.

**ENISA Threat Landscape.** Annually, September/October. The 2024 edition (19 September 2024) identifies seven prime threats and gives good qualitative coverage of BEC growth, quishing, and adversary-in-the-middle MFA bypass. EU-focused, strong on sectoral and geopolitical framing.

**Proofpoint State of the Phish.** Annually. Survey-based, covering user behaviour, reporting rates and organisational practice.
*Careful:* vendor-produced and survey-based; useful for benchmarking practice, weaker as a source of incidence statistics. Read the methodology section before quoting a number.

**Others worth a look:** IBM Cost of a Data Breach Report (annual, for cost modelling — vendor-produced, methodology stated); Chainalysis Crypto Crime Report (for investment-fraud flows); Interpol regional cyberthreat assessments (including for Africa); the UK's Cyber Security Breaches Survey (annual, government statistics); FTC Consumer Sentinel Network data and Data Spotlight series (US consumer fraud).

---

## 5. Certifications, and what they actually signal

**For security awareness and human risk specifically:**
- **SANS SEC/MGT-track security awareness credentials** (e.g. the SANS Security Awareness Professional pathway) — the most directly relevant, focused on programme design and behaviour change.

**For the broader defensive role:**
- **CISSP** (ISC2) — breadth across security management; signals a generalist practitioner with experience. Widely used as an HR filter.
- **CISM** (ISACA) — governance and management orientation; well matched to the file `06` material.
- **CISA** (ISACA, the audit certification — not the US agency) — for assurance over the processes in this domain.
- **GIAC certifications** (SANS) — GSEC, GCIH for incident handling, GCFA for forensics. Practical and expensive.
- **CompTIA Security+** — entry level, adequate as a baseline for a helpdesk or junior analyst.
- **Offensive certifications (OSCP and similar)** — signal technical intrusion skill. Note that they are largely irrelevant to social-engineering *defence*, which is a process and psychology discipline more than a technical one. Hiring for this domain on offensive credentials is a common and expensive mistake.

**For fraud specifically:**
- **CFE (Certified Fraud Examiner, ACFE)** — the right credential for the BEC and payment-fraud side, and the one most often missing from security teams.

**Honest note:** no certification predicts competence at building a reporting culture, which is the hardest and most valuable skill in this domain.

---

## 6. Research venues

Where the peer-reviewed work appears. Most publish open-access preprints.

- **IEEE Symposium on Security and Privacy ("Oakland")** — home of the large-scale phishing field studies, including Lain, Kostiainen and Čapkun's *Phishing in Organizations* (2022).
- **USENIX Security Symposium** — strong on empirical and measurement work.
- **ACM Conference on Computer and Communications Security (CCS)**.
- **Network and Distributed System Security Symposium (NDSS)**.
- **SOUPS (Symposium on Usable Privacy and Security)** — the venue for usable-security and human-factors work; the most relevant single venue for awareness-programme evidence.
- **APWG Symposium on Electronic Crime Research (eCrime)** — phishing and e-crime measurement.
- **Workshop on the Economics of Information Security (WEIS)** — for the cost-and-incentives view.
- **Journal of Cybersecurity** (Oxford), **Computers & Security**, and in psychology **Journal of Personality and Social Psychology**, **Psychological Science** (for influence and deception research — check replication status).

**How to read this literature as a practitioner.** Prefer field studies in real organisations over laboratory studies with student participants; check the sample size and duration; check whether the outcome measured was *click rate* (weak) or *reporting behaviour and time-to-report* (strong); and be sceptical of any single study, including the ones cited approvingly in file `05`.

## Sources

- [NIST SP 800-50 Rev. 1](https://csrc.nist.gov/pubs/sp/800/50/r1/final) — NIST, 12 September 2024
- [ISO/IEC 27001](https://www.iso.org/standard/27001) — ISO, 2022 edition
- [MITRE ATT&CK T1566 Phishing](https://attack.mitre.org/techniques/T1566/) — MITRE
- [MITRE Engage](https://engage.mitre.org/) — MITRE
- [OUCH! Newsletter](https://www.sans.org/newsletters/ouch/) — SANS Institute
- [Phishing Quiz](https://phishingquiz.withgoogle.com/) — Jigsaw / Google
- [The Art of Deception](https://en.wikipedia.org/wiki/The_Art_of_Deception) — Wikipedia (Mitnick & Simon, 2002)
- [Robert Cialdini](https://en.wikipedia.org/wiki/Robert_Cialdini) — Wikipedia (*Influence* 1984, *Pre-Suasion* 2016)
- [Timothy R. Levine](https://en.wikipedia.org/wiki/Timothy_R._Levine) — Wikipedia (*Duped*, University of Alabama Press)
- [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/) — OWASP GenAI Security Project
- [NIST AI 100-2 E2025](https://csrc.nist.gov/pubs/ai/100/2/e2025/final) — NIST, 24 March 2025
- [Cyber Security Toolkit for Boards](https://www.ncsc.gov.uk/collection/board-toolkit) — UK NCSC
- [Phishing attacks: defending your organisation](https://www.ncsc.gov.uk/guidance/phishing) — UK NCSC
- [Implementing Phishing-Resistant MFA](https://www.cisa.gov/sites/default/files/publications/fact-sheet-implementing-phishing-resistant-mfa-508c.pdf) — CISA
- [Phishing in Organizations](https://arxiv.org/abs/2112.07498) — Lain, Kostiainen & Čapkun, IEEE S&P 2022
- [2025 Data Breach Investigations Report](https://www.verizon.com/business/resources/reports/2025-dbir-data-breach-investigations-report.pdf) — Verizon Business
- [2024 Internet Crime Report](https://www.ic3.gov/AnnualReport/Reports/2024_IC3Report.pdf) — FBI IC3
- [APWG Phishing Activity Trends Report Q4 2024](https://docs.apwg.org/reports/apwg_trends_report_q4_2024.pdf) — APWG
- [ENISA Threat Landscape 2024](https://www.enisa.europa.eu/publications/enisa-threat-landscape-2024) — ENISA
- [SAFPS](https://www.safps.org.za/) — Southern African Fraud Prevention Service
- [Nam-CSIRT](https://nam-csirt.na/) — CRAN, Namibia

## Open questions

- **Publication details not verified:** publisher/year for Hadnagy's works; year and subtitle for Levine's *Duped*; publishers for Schneier's *Liars and Outliers* and *Secrets and Lies*; edition history for Cialdini's *Influence*. Verify before producing a formal bibliography.
- **NIST SP 800-53 Rev. 5 AT-family enhancement numbering** was not read from the control catalogue directly. Marked `needs-verification`.
- **ISO/IEC 27001:2022 Annex A structure** (control count and themes) was not confirmed from the standard text; the ISO landing page does not expose it.
- **CISA phishing guidance PDF** returned HTTP 403 during construction; the title, joint authorship and October 2023 date are from the CISA resource page, but the document's detailed recommendations were not read directly.
- **SANS *OUCH!* licence terms** for organisational redistribution were not stated on the fetched page; confirm with SANS.
- **Replication controversies** around Ariely's dishonesty research and Kahneman's priming chapter are described from general knowledge; primary sources not fetched. The characterisations are widely documented but should be cited properly if published.
- **Proofpoint State of the Phish** was not fetched; described from general knowledge of the series.
