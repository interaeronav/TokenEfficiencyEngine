---
id: sedef.resilience
title: Organisational resilience — governance, process and the helpdesk problem
domain: 33_social_engineering_defence
tags: [governance, policy, segregation-of-duties, vendor-management, joiner-mover-leaver, helpdesk-verification, identity-proofing, executive-protection, brand-monitoring, takedown, cyber-insurance, breach-notification, gdpr, popia, nis2, sec-disclosure, business-continuity]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Scattered Spider", url: "https://en.wikipedia.org/wiki/Scattered_Spider", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Caesars Entertainment", url: "https://en.wikipedia.org/wiki/Caesars_Entertainment", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "MGM Resorts International", url: "https://en.wikipedia.org/wiki/MGM_Resorts_International", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Twitter investigation report", url: "https://www.dfs.ny.gov/Twitter_Report", publisher: "NY State Department of Financial Services", accessed: 2026-08-25}
  - {title: "SEC Adopts Rules on Cybersecurity Risk Management, Strategy, Governance, and Incident Disclosure", url: "https://www.sec.gov/newsroom/press-releases/2023-139", publisher: "US Securities and Exchange Commission", accessed: 2026-08-25}
  - {title: "Directive (EU) 2022/2555 (NIS2)", url: "https://eur-lex.europa.eu/eli/dir/2022/2555/oj/eng", publisher: "EUR-Lex", accessed: 2026-08-25}
  - {title: "NIS2 Directive policy page", url: "https://digital-strategy.ec.europa.eu/en/policies/nis2-directive", publisher: "European Commission", accessed: 2026-08-25}
  - {title: "POPIA Section 22 — Notification of security compromises", url: "https://popia.co.za/section-22-notification-of-security-compromises/", publisher: "popia.co.za", accessed: 2026-08-25}
  - {title: "Information Regulator (South Africa)", url: "https://inforegulator.org.za/", publisher: "Information Regulator", accessed: 2026-08-25}
  - {title: "Cyber Security Toolkit for Boards", url: "https://www.ncsc.gov.uk/collection/board-toolkit", publisher: "UK NCSC", accessed: 2026-08-25}
related: [sedef.technical_controls, sedef.human_controls, sedef.cases]
---

# Organisational resilience — governance, process and the helpdesk problem

**Summary.** Technical controls fail when governance is absent: an exemption granted to an executive, a vendor added without checks, a leaver whose access persists, or a service desk that will reset an MFA factor for anyone who sounds convincing. This file covers the governance layer — the policies that matter, segregation of duties, vendor management, joiner-mover-leaver hygiene, **helpdesk identity verification** (the weakest point in most large organisations, and the mechanism behind the MGM and Caesars compromises of September 2023), executive impersonation monitoring, brand and domain monitoring with takedown, cyber insurance, statutory breach-reporting duties across four regimes, and continuity planning for the attack that succeeds.

> ⚠️ Regulatory deadlines below are stated with their source. They differ by regime and by whether the incident involves personal data, an essential service, or a listed company. Get local legal advice; do not run a breach off a knowledge-base table.

## Key facts

| Obligation | Trigger | Deadline | Source |
|---|---|---|---|
| **GDPR** Art. 33 notification to supervisory authority | Personal data breach likely to result in a risk | **72 hours** from awareness | Regulation (EU) 2016/679 |
| **GDPR** Art. 34 communication to data subjects | High risk to rights and freedoms | Without undue delay | Regulation (EU) 2016/679 |
| **NIS2** early warning | Significant incident, essential/important entity | **24 hours** from awareness | Directive (EU) 2022/2555, Art. 23 |
| **NIS2** incident notification | Same | **72 hours** from awareness | Directive (EU) 2022/2555, Art. 23 |
| **NIS2** final report | Same | **1 month** after notification (progress report if ongoing) | Directive (EU) 2022/2555, Art. 23 |
| **NIS2** transposition | — | Member states by **17 October 2024** | European Commission |
| **POPIA** s.22 **[ZA]** | Security compromise of personal information | "As soon as reasonably possible after discovery" (delay permitted for law enforcement or to determine scope) | POPIA, Act 4 of 2013 |
| **SEC** Form 8-K Item 1.05 **[US]** | Material cybersecurity incident | **4 business days** from materiality determination | SEC rules adopted July 2023 |
| **SEC** Reg S-K Item 106 **[US]** | Annual | Form 10-K, FY ending on/after 15 Dec 2023 | SEC, July 2023 |

---

## 1. The policies that actually matter

Most policy sets are too long to be read and too vague to be applied. For social engineering, six documents carry nearly all the weight. Each should be one to three pages, written as rules a person can apply under pressure.

1. **Payment authorisation policy.** Thresholds, dual authorisation, the callback rule with the known-good-number principle, cooling-off periods, the gift-card prohibition, and the **no-exceptions clause** signed by the CEO.
2. **Vendor bank-detail change procedure.** Separate from the above because it is the single highest-loss process in the organisation.
3. **Identity verification standard for the service desk.** What proofs are acceptable, what is prohibited (knowledge-based questions), escalation for privileged accounts, and the requirement to log the method used.
4. **Access management policy.** Least privilege, just-in-time elevation, four-eyes on privilege grants, joiner-mover-leaver timelines, and the rule that no account is exempt from MFA.
5. **Incident reporting policy.** How to report, the no-blame guarantee, and the statement that failing to report is the only reportable failure.
6. **Acceptable channels policy.** Which systems constitute official communication; a statement that business instructions are never issued through consumer messaging apps, so an approach on WhatsApp is itself an anomaly.

Everything else — asset management, cryptography, physical security — matters for other reasons. These six are the social-engineering set.

---

## 2. Segregation of duties

Segregation of duties is the structural implementation of the Asch ally effect (file `01` §3): it guarantees a second person in the loop, so no one deceived individual can complete an irreversible act.

**Minimum separations:**
- Initiate payment ≠ approve payment.
- Maintain vendor master data ≠ approve payments to vendors.
- Create/modify user accounts ≠ approve privilege grants.
- Perform an action ≠ review the log of that action.
- Request an access change ≠ implement it.

**Common failure modes:** emergency-override procedures that bypass the split; small teams where one person holds all roles; system administrators who can grant themselves any role; and *nominal* separation where the second approver rubber-stamps. Test the last one during audit by asking approvers what they actually check.

**Where headcount makes true separation impossible**, use compensating controls: bank-side dual authorisation with an external party (the accountant, a director), payee whitelisting requiring a delay, mandatory callback logged and reviewed monthly, and daily transaction review by a person other than the initiator.

---

## 3. Vendor and third-party management

Third parties appeared in **30% of breaches** in the 2025 DBIR, roughly double the previous year. Caesars was reportedly breached through an outside IT vendor in September 2023. Treat suppliers as part of your attack surface.

**Onboarding:** verify the legal entity independently of the documents supplied; verify banking details by callback to a number obtained from an independent source before the first payment; record named, verified contacts in the vendor master file; set security requirements proportionate to the access granted.

**Ongoing:**
- **Vendor master data is a security asset.** Changes require change control, callback verification, notification to the previous known contact, a hold period and a second approver.
- **Contractual obligations**: prompt notification of any compromise affecting your data or your communications with them; MFA on any access to your systems; named security contact.
- **Access control**: no standing supplier access; just-in-time with expiry; separate identities; the same MFA standard as employees. Outsourced support staff must be treated as privileged users, not as an exception — the Coinbase May 2025 insider bribery case (file `02` §13) turned on outsourced support access.
- **Monitoring**: watch for lookalike domains of your key suppliers as well as your own; a supplier-mailbox compromise usually shows up first as an odd invoice.
- **Offboarding**: a documented, time-bounded access revocation with evidence.

---

## 4. Joiner-mover-leaver hygiene

Access accretion is how a modest compromise becomes a serious one.

- **Joiner:** access provisioned from a role template, not by copying an existing user's permissions — "copy Jane's access" is the primary mechanism of privilege sprawl. MFA enrolled on day one, in person or with verified identity, before any remote access is granted.
- **Mover:** the hardest and most-skipped. On a role change, access must be **rebuilt from the new role template**, not added to. Require the losing manager to confirm removal.
- **Leaver:** revocation within a defined SLA (same day for standard leavers, immediately and pre-emptively for high-risk departures), covering identity provider, email, SaaS applications outside SSO, VPN, physical badge, mobile device, and — importantly — **session and refresh token revocation**, plus removal from the vendor and payment platforms.
- **Periodic recertification:** managers attest to their team's access at least annually, more often for privileged roles. Make the default action *removal* if no attestation is received.
- **Orphan and service accounts:** inventory them, assign owners, and eliminate shared credentials.

---

## 5. Helpdesk identity verification — the major weak point

This deserves its own treatment because it is where the largest recent enterprise compromises began.

**What happened.** In September 2023 the group tracked as Scattered Spider compromised MGM Resorts by calling the service desk impersonating an employee identified from LinkedIn; the initial breach occurred on 11 September 2023 and was disclosed on 12–13 September. Systems affected included food and beverage credits, ATMs, remote room keys and parking. MGM stated losses of about **US$100 million**, expected to be covered by cyber insurance, and settled consolidated class actions for **US$45 million** on 18 June 2025. Caesars Entertainment was breached in the same period — reportedly through an outside IT vendor — exposed loyalty-programme data for roughly 65 million members including driver's licence numbers and possibly social security numbers, and paid **US$15 million** of a US$30 million ransom demand. The group's broader toolkit included MFA fatigue, SIM swapping, and SMS and Telegram phishing.

**Why the service desk is structurally vulnerable.** It is measured on speed and satisfaction; it exists to help people who are locked out and frustrated; it is frequently outsourced and offshored with high turnover; and it authenticates callers using information that is now public (employee number, date of birth, manager's name, last four digits of anything). Add an angry caller claiming to be an executive and the agent's incentives point exactly the wrong way.

**A verification standard that works:**

1. **Abolish knowledge-based verification.** Nothing an attacker can research, buy in a breach corpus, or read on a public profile counts as proof.
2. **Use an authenticated channel.** Approve the request via a push to an already-enrolled device, or a challenge in the corporate identity app, or a code delivered to a verified corporate channel the caller must already control.
3. **Where no enrolled factor exists** (the genuine lockout case), require **manager attestation through the ticketing system** — the manager, verified separately, approves in writing — or an in-person check, or a **verified video call against the HR-held photograph with a documented liveness step**. Record which method was used.
4. **Tier by target privilege.** Any reset affecting a privileged or executive account escalates to a named security contact; never handled by first-line.
5. **Enforce a callback to the number in the HR record**, never a number supplied by the caller.
6. **Instrument it.** Alert on reset volume per agent, resets outside hours, resets on privileged targets, multiple resets for one identity, and a second caller "confirming" the first — a documented multi-agent pattern.
7. **Train agents to refuse pressure, and back them publicly every single time.** An agent who is overruled once will not refuse again. This is a leadership control, not a training control.
8. **Consider a cooling-off period** for MFA re-enrolment on privileged accounts, during which the legitimate user is notified through every channel on file.

> ⚠️ If your helpdesk can reset an MFA factor on the strength of a phone call, your investment in phishing-resistant MFA is contingent on a stranger's charm. Fix the registration and reset flows before, or at least alongside, the authentication flow.

---

## 6. Executive protection and impersonation monitoring

- **No exemptions.** Executives get hardware keys and the strictest conditional access, not a waiver. Exemptions granted for convenience are the attack surface.
- **A personal, publicised commitment** from each executive that they will never request a payment, credential, approval bypass or gift card outside the documented process, and that any such request is fraudulent by definition. Repeat it annually and at every all-hands.
- **Named delegates with defined authority**, so the EA knows exactly what they may and may not act on.
- **Reduce the personal footprint** of executives and their families — home address, travel patterns, children's schools — as a request, supported by help, not as a mandate.
- **Impersonation monitoring**: watch for fake executive profiles on professional and social networks, lookalike personal-style email addresses, and fraudulent WhatsApp accounts using their photograph. Have a standing reporting relationship with the major platforms.
- **A briefing before high-exposure moments** — results announcements, M&A activity, conference keynotes — because these are exactly when a confidential-urgent pretext is most plausible.

---

## 7. Brand and domain monitoring

- Monitor **certificate transparency logs** and domain registration feeds for lookalikes of your primary domains, your key brands and your top suppliers.
- Monitor app stores for cloned mobile applications, and social platforms for impersonating pages and support accounts.
- **Defensively register** the highest-risk permutations, but recognise this cannot be exhaustive — it buys you the obvious cases.
- Publish a single, prominent page stating your legitimate domains, the channels you use, and what you will never ask for. Point customers and suppliers to it in every dispute.
- Feed confirmed lookalikes into your own DNS blocklists and gateway rules immediately — **blocking is faster than takedown and is entirely within your control.**

## 8. Takedown processes

Have this ready before you need it:
- A named owner and an out-of-hours contact.
- A pre-drafted abuse notice template and the abuse contacts for common registrars, hosting providers, CDNs and the major platforms.
- Relationships with your registrar, your brand-protection provider (if any), and the national CSIRT — the NCSC's takedown service in the UK, CISA in the US, Nam-CSIRT in Namibia (see file `09` §7).
- Evidence preservation *before* takedown: full-page captures, headers, hashes, WHOIS and hosting records, timestamps. A removed site is also removed evidence.
- Realistic expectations: hours to days for hosted phishing pages, considerably longer for registered domains, and often unsuccessful in uncooperative jurisdictions. **Blocking and customer warning are the controls you own; takedown is a request.**

## 9. Cyber insurance

- **Check the coverage triggers.** Many policies distinguish *cyber* loss (systems compromise) from *crime* or *social engineering fraud* cover (a deceived employee makes an authorised-looking transfer). BEC losses often fall under the latter and may be a low-limit endorsement or absent entirely. This is the single most common coverage surprise.
- **Read the conditions precedent.** Insurers increasingly require MFA, dual authorisation and callback verification as conditions; failing to operate a control you attested to can void a claim.
- **Know the notification clock** in the policy, which is frequently shorter than the regulatory clock, and the requirement to use panel counsel and panel forensics.
- **Understand what it buys beyond indemnity**: incident response retainer, forensics, legal, notification costs, PR. For smaller organisations that capability is often worth more than the payout.
- **Scale is real.** MGM stated approximately US$100 million in losses from the September 2023 incident and expected cyber insurance to cover it — a useful data point for a board discussion about limits.

## 10. Regulatory reporting duties

**[EU] GDPR** — Regulation (EU) 2016/679. Article 33 requires notification of a personal data breach to the supervisory authority without undue delay and, where feasible, **within 72 hours** of becoming aware, unless the breach is unlikely to result in a risk to individuals; processors must notify controllers without undue delay. Article 34 requires communication to affected data subjects without undue delay where there is a **high risk** to their rights and freedoms. A social-engineering incident that exposes personal data engages this even if no money was lost.

**[EU] NIS2** — Directive (EU) 2022/2555, in force January 2023, transposition deadline **17 October 2024**. Applies to medium and large entities in listed critical sectors — energy, transport, health, finance, water, digital infrastructure, electronic communications, digital services, waste, critical manufacturing, postal and courier, public administration, space. Article 23 imposes a staged duty: **early warning within 24 hours**, **incident notification within 72 hours** with an initial severity assessment and indicators of compromise, and a **final report within one month** (or a progress report if the incident is ongoing, with the final report one month after handling completes). The directive explicitly states the reporting duty must not divert resources from incident handling.

**[ZA] POPIA** — Protection of Personal Information Act 4 of 2013; commenced 1 July 2020 with full compliance from 1 July 2021; enforced by the **Information Regulator**, established under section 39. **Section 22** requires the responsible party to notify both the Regulator and the affected data subject (unless the data subject cannot be identified) **as soon as reasonably possible after discovery**, with delay permitted only for law-enforcement needs or to determine the scope and restore system integrity. The notification must describe the possible consequences, the measures taken or intended, recommendations for the individual's own mitigation, and the identity of the unauthorised person if known. It may be delivered by post, email, a prominent website notice, news media, or any means the Regulator directs. Penalties under POPIA reach R10 million and/or imprisonment; the Regulator fined the Department of Justice and Constitutional Development R5 million in July 2023.

**[US] SEC** — Rules adopted July 2023. **Form 8-K Item 1.05** requires disclosure of a material cybersecurity incident within **four business days of determining materiality**, describing the material aspects of the incident's nature, scope and timing and its material impact; the Attorney General may authorise delay on national-security or public-safety grounds. **Regulation S-K Item 106** requires annual Form 10-K disclosure of processes for assessing and managing material cyber risk, the effects of prior incidents, board oversight and management's role. Compliance began with fiscal years ending on or after 15 December 2023 for annual disclosures and 18 December 2023 (or 90 days after Federal Register publication) for 8-K, with a further 180 days for smaller reporting companies. Foreign private issuers report on Forms 6-K and 20-F.

**[NA] Namibia** — Namibia has no comprehensive data protection statute in force at the time of writing; a Data Protection Bill and cybercrime legislation have been in development. **Nam-CSIRT**, operated under the Communications Regulatory Authority of Namibia (CRAN, established under the Communications Act 8 of 2009), is the national incident response point. Confirm current legislative status before relying on this. Marked `needs-verification`.

**Practical governance point.** These clocks run concurrently and from different trigger events — "awareness" of a breach, "determination" of materiality, "discovery" of a compromise. Build a single incident timeline with a documented awareness timestamp, and have counsel identify which clocks started when. Rehearse this in a tabletop (file `05` §6); organisations routinely discover mid-incident that nobody knows who may authorise a regulatory filing.

## 11. Business continuity for a successful attack

Assume the attack works. Plan for four scenarios:

**(a) Funds are gone.** A rehearsed recall procedure with named bank contacts and out-of-hours numbers; immediate reporting to law enforcement; a cash-flow plan for the loss; an insurance notification path; and a decision-maker empowered to freeze all outbound payments.

**(b) The identity provider is compromised.** Break-glass accounts with hardware keys held in physical custody, tested quarterly; documented procedure to revoke all sessions and force re-enrolment; out-of-band communications (a pre-agreed alternative messaging channel and a printed contact list) because your email may be untrustworthy or unavailable.

**(c) Operations are down.** MGM's operations were disrupted for several days across guest-facing systems. Manual fallback procedures for revenue-critical operations, printed and rehearsed, are not an anachronism.

**(d) The story is public.** Pre-drafted holding statements; a named spokesperson; a customer notification process that can run at volume; and a plan for the secondary wave of scams that impersonates your own incident response — after Equifax's 2017 breach, 194 malicious domains were created mimicking the legitimate help site. **Publish your real support URL early and repeat it.**

**Board oversight.** The NCSC's Cyber Security Toolkit for Boards (v3.0, 30 March 2023, reviewed 8 April 2025) structures this around five principles: risk management, strategy, people, incident planning and response, and assurance and oversight. Its people and incident-response principles are the right frame for social engineering at board level.

## Sources

- [Scattered Spider](https://en.wikipedia.org/wiki/Scattered_Spider) — Wikipedia (MGM and Caesars 2023, tactics, arrests)
- [Caesars Entertainment](https://en.wikipedia.org/wiki/Caesars_Entertainment) — Wikipedia (outside IT vendor vector, US$15 m ransom, 65 million members)
- [MGM Resorts International](https://en.wikipedia.org/wiki/MGM_Resorts_International) — Wikipedia (US$100 m loss, US$45 m settlement 18 June 2025)
- [Twitter investigation report](https://www.dfs.ny.gov/Twitter_Report) — NY State DFS (privilege sprawl, absent CISO)
- [SEC press release 2023-139](https://www.sec.gov/newsroom/press-releases/2023-139) — US SEC (Item 1.05, Item 106, timelines)
- [Directive (EU) 2022/2555 (NIS2)](https://eur-lex.europa.eu/eli/dir/2022/2555/oj/eng) — EUR-Lex (Article 23 staged reporting)
- [NIS2 Directive](https://digital-strategy.ec.europa.eu/en/policies/nis2-directive) — European Commission (scope, transposition deadline)
- [POPIA Section 22](https://popia.co.za/section-22-notification-of-security-compromises/) — popia.co.za
- [Protection of Personal Information Act, 2013](https://en.wikipedia.org/wiki/Protection_of_Personal_Information_Act,_2013) — Wikipedia (dates, penalties, DoJ fine)
- [Information Regulator (South Africa)](https://inforegulator.org.za/) — Information Regulator
- [Communications Regulatory Authority of Namibia](https://cran.na/) — CRAN (Nam-CSIRT)
- [Cyber Security Toolkit for Boards](https://www.ncsc.gov.uk/collection/board-toolkit) — UK NCSC
- [Social engineering (security)](https://en.wikipedia.org/wiki/Social_engineering_(security)) — Wikipedia (Equifax lookalike domains)

## Open questions

- **GDPR Articles 33 and 34 text was not directly retrieved** (gdpr-info.eu blocked by robots.txt; EUR-Lex returned metadata only). The 72-hour and high-risk thresholds stated here are canonical but should be checked against the regulation text before use in a compliance document. Marked `needs-verification`.
- **Namibian data protection and cybercrime legislation status** — a Data Protection Bill and cybercrime provisions have been in development; the current status was not confirmed. Verify with CRAN, Nam-CSIRT and the Ministry of Information and Communication Technology.
- **Caesars' SEC 8-K disclosure** of the 2023 incident was not retrieved; the reporting position is therefore not stated here.
- **MGM's US$100 million figure** is reported as the company's stated loss expected to be covered by insurance; the underlying 8-K/10-Q language was not read directly.
- Cyber insurance market practice (social engineering fraud endorsements, conditions precedent) is described from general industry knowledge; no policy wordings were consulted.
