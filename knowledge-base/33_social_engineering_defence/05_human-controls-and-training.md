---
id: sedef.human_controls
title: Human controls and training — doing awareness properly
domain: 33_social_engineering_defence
tags: [security-awareness, phishing-simulation, training-effectiveness, reporting-culture, just-in-time, tabletop-exercise, metrics, nist-800-50, human-risk-management, safe-word]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Phishing in Organizations: Findings from a Large-Scale and Long-Term Study", url: "https://arxiv.org/abs/2112.07498", publisher: "Lain, Kostiainen & Čapkun, IEEE S&P 2022", accessed: 2026-08-25}
  - {title: "Phishing attacks: defending your organisation", url: "https://www.ncsc.gov.uk/guidance/phishing", publisher: "UK NCSC", accessed: 2026-08-25}
  - {title: "Telling users to avoid clicking bad links still isn't working", url: "https://www.ncsc.gov.uk/blog-post/telling-users-to-avoid-clicking-bad-links-still-isnt-working", publisher: "UK NCSC", accessed: 2026-08-25}
  - {title: "NIST SP 800-50 Rev. 1: Building a Cybersecurity and Privacy Learning Program", url: "https://csrc.nist.gov/pubs/sp/800/50/r1/final", publisher: "NIST", accessed: 2026-08-25}
  - {title: "Cyber Security Toolkit for Boards", url: "https://www.ncsc.gov.uk/collection/board-toolkit", publisher: "UK NCSC", accessed: 2026-08-25}
  - {title: "OUCH! Newsletter", url: "https://www.sans.org/newsletters/ouch/", publisher: "SANS Institute", accessed: 2026-08-25}
  - {title: "Truth-default theory", url: "https://en.wikipedia.org/wiki/Truth-default_theory", publisher: "Wikipedia", accessed: 2026-08-25}
related: [sedef.psychology, sedef.technical_controls, sedef.resilience, sedef.personal]
---

# Human controls and training — doing awareness properly

**Summary.** Security awareness is the most-purchased and least-evidenced control in the field. The honest position, supported by the strongest available field studies and by the UK NCSC's published guidance, is that **training does not reliably make people better at detecting phishing**, that **embedded training delivered at the moment of a simulated failure may not help and may make things worse**, and that the one human capability with clear evidence behind it is **reporting**. This file sets out how to design a programme on that basis: what to teach, what to stop teaching, how to run simulations ethically if you run them at all, how to build a reporting culture, how to train the roles that actually carry the risk, and how to measure the programme with something more meaningful than click rate.

> ⚠️ Any programme whose primary metric is click rate, and whose primary consequence for clicking is a punishment, is optimising the wrong variable and actively degrading its own detection capability. That is the central argument of this file.

## Key facts

| Claim | Evidence | Confidence |
|---|---|---|
| Employees can function as a collective phishing-detection sensor at large scale | Lain et al., 15 months, 14,000+ employees, IEEE S&P 2022 — practical, manageable operational burden, engagement sustained | High |
| Embedded training at the moment of simulated failure improves resilience | **Not supported.** Same study found it "does not make employees more resilient to phishing" and may increase susceptibility | High for this study; see limits below |
| Warnings on suspicious emails reduce susceptibility | Supported by the same study, described as confirming prior literature with stronger real-world evidence | High |
| Users can be trained to reliably spot phishing | **Not supported.** NCSC: "spotting all phishing emails is hard, and spear phishing attacks are even harder to detect"; "being able to spot a phish is **not** their job" | High |
| Human deception-detection accuracy | ~50–60%, barely above chance (truth-default literature) | High |
| Punitive simulation programmes suppress reporting | NCSC states stigma "often prevents people from reporting incidents, delaying response times"; simulations can erode trust and discourage reporting | High (guidance-level, not RCT) |
| Standards basis for programme design | NIST SP 800-50 Rev. 1, *Building a Cybersecurity and Privacy Learning Program*, published 12 September 2024, superseding SP 800-50 (2003) and SP 800-16 (1998) | High |

---

## 1. Programme design: the current standards basis

NIST replaced two long-obsolete documents in one step. **SP 800-50 Rev. 1, "Building a Cybersecurity and Privacy Learning Program" (12 September 2024)**, supersedes SP 800-50 (October 2003) and SP 800-16 (April 1998). Three features of the revision matter:

1. It frames the work as a **lifecycle** — assess, design, develop, implement, evaluate, improve — rather than an annual event.
2. It explicitly targets **behavioural change in support of risk management**, not knowledge transfer, and treats organisational security culture as the objective.
3. It requires **metrics and evaluation methods** as part of the programme, not as an afterthought.

Alongside it, ISO/IEC 27001:2022 places awareness in Annex A control **A.6.3, "Information security awareness, education and training"** (people controls), and NIST SP 800-53 Rev. 5 carries the **AT** control family, of which AT-2 (Literacy Training and Awareness) has enhancements covering insider threat, social engineering and social mining, and advanced persistent threat. Use these to justify budget; do not mistake them for evidence that any particular training product works.

**A workable programme structure:**

| Layer | Audience | Frequency | Content |
|---|---|---|---|
| Baseline literacy | Everyone | On joining, then annually, short | What social engineering is, the negative rules, how and when to report, no-blame guarantee |
| Continuous nudges | Everyone | Monthly, ≤5 minutes | One mechanism, one real example, one action. SANS *OUCH!* is a free monthly vehicle |
| Role-specific | Finance, helpdesk, HR, executives, EAs, developers | Quarterly to biannual, deeper | The specific fraud shapes and procedures for that role |
| Just-in-time | Triggered | At the moment of risk | Contextual warnings in the workflow (see §4) |
| Exercises | Leadership, IR, finance, comms | At least annually | Tabletop scenarios (see §6) |

---

## 2. What the evidence actually says

This is where most organisational practice diverges from the literature. Be honest about it internally; the credibility of the whole programme depends on it.

**The strongest field study.** Lain, Kostiainen and Čapkun ran a 15-month experiment with over 14,000 employees of a real organisation receiving simulated phishing emails, measuring clicks, credential submission and reports via a dedicated button (IEEE S&P 2022). Three findings:
- **Embedded training** — the "you clicked, now read this" page — did **not** make employees more resilient, and the authors report it may increase susceptibility.
- **Warnings** on emails were effective at reducing susceptibility, confirming earlier work with much stronger real-world evidence.
- **Crowd-sourced reporting** works: employees collectively provided rapid campaign detection at a manageable operational burden, with engagement sustained over the full period.

**The regulator's position.** The NCSC's phishing guidance says plainly that spotting all phishing emails is hard and spear phishing is harder, and warns that simulations can create unrealistic expectations, carry legal risk "resembling entrapment", erode trust between staff and security teams, and discourage reporting if punitive. Its December 2022 post by Dave Chismon goes further: users "frequently *need* to click on links from unfamiliar domains to do their job, and being able to spot a phish is **not** their job", and organisations should accept that users will click and take responsibility for protecting them with technology.

**What this does not mean.** It does not mean "do no training". It means the *goal* of training must change. Training that reliably works targets **procedures and reporting**, not detection:
- Teaching a finance clerk the callback rule changes behaviour that is entirely within their control.
- Teaching a helpdesk agent the identity-proofing script changes behaviour entirely within their control.
- Teaching everyone the one-click report path changes behaviour entirely within their control.
- Teaching everyone to "spot the phish" asks them to perform a task humans perform at near chance.

**Caveat on generalisation.** These are a small number of studies in specific organisations. Effect sizes vary by population, baseline maturity, and how "training" is operationalised. Present the evidence as *the best we have and unfavourable to the conventional model*, not as settled science. A large 2025 study of phishing training at a US academic healthcare system, reported at IEEE S&P 2025, is frequently cited as reaching similar conclusions with very small measured training effects; **that paper could not be retrieved during the construction of this file and is marked `needs-verification`** — do not quote its figures without reading it.

---

## 3. Simulated phishing: ethics, pitfalls, and how to do it if you must

Many organisations are contractually or regulatorily obliged to run simulations. If you are, run them well.

**Legitimate purposes.** Measuring *reporting rate* and *reporting latency*; testing the technical clawback and triage pipeline; giving leadership a concrete, non-abstract picture; identifying roles and processes that need procedural change.

**Illegitimate purposes.** Ranking individuals; generating a click-rate number for a board slide; justifying disciplinary action; "proving" that staff are the weak link.

**Rules for ethical simulations:**
1. **Announce the programme** (not individual campaigns) in advance, with the purpose, the metrics used, and an explicit statement of what will *not* happen to people who click.
2. **Never use cruel lures.** Bonuses, redundancies, disciplinary notices, bereavement, medical results, immigration status, and anything touching a live organisational anxiety. The NCSC's entrapment concern is at its sharpest here, and a lure that causes genuine distress destroys years of goodwill in an afternoon. Several widely-reported corporate incidents involved fake bonus emails and did lasting reputational damage internally.
3. **No individual consequences.** No naming, no leaderboards, no manager notification of individual clicks, no mandatory remedial training as a punishment.
4. **Get works-council, HR, legal and privacy sign-off**, and be clear about the lawful basis for processing the resulting personal data (GDPR/POPIA both apply to click data tied to an identified employee).
5. **Measure reporting first.** Report rate and median time-to-first-report are the operationally meaningful numbers; click rate is context for them.
6. **Debrief collectively and specifically.** "Here is the campaign, here is why it was convincing, here is the procedural control that would have saved us anyway" — aimed at the group, never at an individual.
7. **Do not use simulations to test people the technology should be protecting.** If a simulated adversary-in-the-middle lure would harvest a working session, the finding is that you have not deployed FIDO2 — that is a control gap, not a people gap.

**The NCSC's alternative,** worth trying at least once: have staff **craft their own phishing emails** in a workshop. It teaches the mechanisms from the inside, produces genuine insight into what makes a request plausible in *your* organisation, and generates no distress or entrapment risk.

---

## 4. Just-in-time interventions

The intervention with the best cost-to-effect ratio is a warning delivered at the moment of risk, in the workflow. Because the evidence supports warnings over training, invest here first.

- **External-sender and first-time-sender banners** in mail, with a distinct treatment for display names resembling internal staff.
- **Interstitial warnings** on links to newly registered or uncategorised domains.
- **In-application prompts at the decision point**: when a user changes a vendor's bank details in the ERP, the screen states the callback rule and requires an attestation that it was followed, with the number called recorded.
- **Payment-platform prompts** on first-time beneficiaries.
- **Authenticator context**: application name and sign-in location shown in the MFA prompt so an unexpected approval request is legible.
- **Browser warnings** for credential entry on non-corporate domains, where the platform supports it.

Design rule: a warning must be **rare, specific and actionable**. Warnings on every external email become invisible within a week.

---

## 5. Reporting culture — the control that matters most

Reporting is the only human behaviour in this domain with strong supporting evidence, and it is the behaviour most easily destroyed by management practice.

**Why punishing victims is self-defeating.** A person who has just entered credentials into a fake page is the most valuable sensor in the organisation for the next fifteen minutes. If they fear consequences, they will delay, hope, or say nothing — and the NCSC notes exactly this dynamic, that stigma prevents reporting and delays response. Every hour of delay in a BEC materially reduces recall odds. The organisation trades a genuine detection capability for the illusion of accountability.

**How to build it:**
- **A one-click report button** in the mail client on every device, including mobile. Friction is fatal.
- **A published no-blame guarantee**, signed by the CEO, stating that no one will face consequences for reporting a security concern or for having been deceived, and that the only reportable failure is *not* reporting.
- **Acknowledge every report**, automatically within seconds and personally for the useful ones.
- **Close the loop.** Tell reporters what happened. "Your report let us pull that message from 400 mailboxes in 12 minutes" converts one reporter into a department of them.
- **Celebrate the catch, publicly and by name where the person consents.** Especially celebrate a senior person reporting their own mistake — nothing else moves culture as fast.
- **Make false positives welcome.** "Thanks — it was legitimate, and you were right to check" must be the standard response. A programme with no false positives has no reporting.
- **Give the helpdesk and finance an explicit licence to refuse and verify**, with a named escalation contact who will back them.

**A hard test of your culture:** what happens to the accounts payable clerk who declines to pay an urgent invoice the CFO personally chased? If the answer is anything other than visible support, your controls are decorative.

---

## 6. Tabletop exercises

Tabletops rehearse the decisions that a real incident makes under pressure, and they surface missing authority more reliably than any audit.

**Cadence and participants.** At least annually, ideally quarterly for the core team. Include: security, IT, finance/treasury, HR, legal, communications, a business owner, and at least one board or executive sponsor.

**Scenarios worth running:**
- A supplier's mailbox is compromised and a bank-detail change was already paid, three weeks ago.
- The service desk reset MFA for an executive after a convincing call; the caller was not the executive.
- A finance manager joined a video call with the CFO and two colleagues and was asked to make an urgent transfer (the Arup shape).
- A staff member reports entering credentials on a fake portal — 40 minutes ago.
- Ransomware follows a successful phish on a Friday evening.
- A payroll diversion is discovered on payday.

**What to test, not just discuss.** Who can freeze a payment at 22:00? Who authorises customer notification? What is the regulator clock (72 hours under GDPR, 24-hour early warning under NIS2, four business days for a material incident under the SEC rules — file `06` §10)? Who talks to the press? Is the out-of-hours contact list current, and is it stored somewhere that survives the incident?

**Output.** A short list of concrete gaps with owners and dates. A tabletop that generates no actions was a presentation.

---

## 7. Role-specific training

**Finance and accounts payable.** The callback rule with the known-good-number principle stated explicitly; the vendor bank-change procedure; dual authorisation; the gift-card ban; the escalation contact; the no-exceptions clause and the guarantee of support for refusing. Use anonymised real cases (file `07`). This group needs procedure drills, not awareness videos.

**IT helpdesk and service desk.** The highest-risk function in most large organisations and the most under-trained. Cover: the identity-proofing procedure and why knowledge-based questions are worthless; the escalation path for any reset on a privileged account; how to say no to an angry caller claiming to be an executive; how to recognise pressure and multi-agent attempts (a second caller "confirming" the first); the requirement to log every verification method used. Rehearse with live role-play, and back the agent every time they refuse.

**Executives and executive assistants.** Hardware keys, no exemptions. The specific point that their public profile is an attack input. A standing commitment, made by the executive personally and communicated to all staff, that they will never request a payment, a credential, or a bypass outside the documented process — and that any such request is by definition fraudulent. EAs need explicit authority to verify anything, including at inconvenient moments.

**HR and payroll.** Bank-detail change procedures for employees; recruitment-fraud indicators in both directions; identity verification at onboarding; the sensitivity of the personnel data they hold.

**Developers and cloud administrators.** Credential hygiene and secrets management (the Uber 2022 escalation came from hardcoded credentials in a script); OAuth consent risks; package and supply-chain lures; the fact that they are specifically targeted.

**New starters.** Front-load the negative rules in week one, before they have learned that "normal" includes irregular requests. Explicitly tell them that being new is not a reason to comply with an unusual request.

---

## 8. Verification habits and callback protocols

The transferable habit, for businesses and families alike, is **out-of-band verification using a channel obtained independently of the request**.

**For businesses:**
- A vendor master file containing verified contact numbers, itself under change control.
- A written rule: never use contact details supplied within the request.
- Pre-agreed **code phrases** for verbal high-value authorisation, rotated periodically, never stored in the system being protected.
- A documented log of verification for each qualifying transaction.

**For families** (expanded in file `09` §4):
- A **family safe word** or shared question, agreed offline, for any distress or emergency-money call. Voice cloning makes "it sounded exactly like her" worthless as evidence.
- A rule that any request for money made by phone or message is verified by calling the person back on their stored number.
- A designated trusted person to consult before any large or unusual financial decision.
- Agreement in advance that no legitimate emergency is ever harmed by a five-minute callback.

Teach these as **habits with no exceptions**, because an exception clause is exactly what an attacker manufactures.

---

## 9. Measuring the programme with meaningful metrics

Click rate is a poor primary metric: it is dominated by campaign difficulty (which you control), it can be gamed by sending easier simulations, it says nothing about consequence, and optimising it encourages punitive practice. Replace it with a portfolio.

**Detection metrics (the important ones)**
- **Report rate** on simulated *and* real phishing, by department.
- **Median time-to-first-report** from delivery — the number most tightly coupled to containment.
- **Reports per real campaign**, and the fraction of real campaigns first detected by a human.
- **Time from first report to clawback complete.**
- **False-positive rate** — a rate near zero indicates a broken culture, not a vigilant one.

**Resilience metrics (do the controls work?)**
- Percentage of accounts on phishing-resistant MFA, split out for privileged accounts.
- Percentage of owned domains at DMARC `p=reject`.
- Percentage of qualifying payments with documented callback verification.
- Percentage of vendor bank changes following the full procedure.
- Number of MFA/password resets performed without full identity proofing (target zero).
- Standing privileged accounts remaining.

**Outcome metrics**
- Number of real incidents by category, and losses avoided (a caught invoice fraud has a countable value — record it; it is the best budget argument you have).
- Actual financial loss to social engineering per period.
- Mean time to contain, by playbook.

**Culture metrics**
- Anonymous survey: "Would you report immediately if you had just clicked something and entered your password?" Track the *yes* percentage over time. This single question is the most informative culture measure available and costs nothing.
- Proportion of staff who can state the callback rule unprompted.

**Reporting to the board.** The NCSC's Cyber Security Toolkit for Boards (v3.0, published 30 March 2023, reviewed 8 April 2025) organises board engagement around five principles — risk management, strategy, people, incident planning and response, and assurance and oversight — and supplies question sets. Use the "people" principle to steer the conversation away from click rate and toward reporting capability, control coverage and rehearsed response.

## Sources

- [Phishing in Organizations: Findings from a Large-Scale and Long-Term Study](https://arxiv.org/abs/2112.07498) — Lain, Kostiainen & Čapkun, IEEE S&P 2022
- [Phishing attacks: defending your organisation](https://www.ncsc.gov.uk/guidance/phishing) — UK NCSC (four-layer model; simulation cautions; "craft your own phishing email")
- [Telling users to "avoid clicking bad links" still isn't working](https://www.ncsc.gov.uk/blog-post/telling-users-to-avoid-clicking-bad-links-still-isnt-working) — UK NCSC, Dave Chismon, 20 December 2022
- [NIST SP 800-50 Rev. 1: Building a Cybersecurity and Privacy Learning Program](https://csrc.nist.gov/pubs/sp/800/50/r1/final) — NIST, 12 September 2024
- [Cyber Security Toolkit for Boards](https://www.ncsc.gov.uk/collection/board-toolkit) — UK NCSC, v3.0
- [OUCH! Newsletter](https://www.sans.org/newsletters/ouch/) — SANS Institute
- [Truth-default theory](https://en.wikipedia.org/wiki/Truth-default_theory) — Wikipedia
- [ISO/IEC 27001](https://www.iso.org/standard/27001) — ISO (2022 edition, published 25 October 2022)

## Open questions

- **The 2025 IEEE S&P study on phishing training efficacy** (widely reported as an eight-month study across a large US academic healthcare system finding very small training effects) **could not be retrieved**; multiple candidate URLs returned 404 and WebSearch was unavailable. Treat as `needs-verification` and read the paper before citing figures.
- **ISO/IEC 27001:2022 Annex A structure** (93 controls in four themes; A.6.3 as the awareness control) is stated from general knowledge — the ISO landing page did not expose Annex A detail. Verify against the standard text.
- **NIST SP 800-53 Rev. 5 AT-family control enhancement numbering** is from general knowledge; the CSRC control browser could not be read directly. Verify identifiers before quoting them in an audit response.
- Reported corporate incidents involving distressing simulated-phishing lures (fake bonus emails and similar) are referenced generically because specific incidents could not be re-verified during construction.

