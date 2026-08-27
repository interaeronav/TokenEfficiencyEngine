---
id: sedef.lifecycle
title: The attack lifecycle from a defender's view — where to interrupt it
domain: 33_social_engineering_defence
tags: [kill-chain, threat-modelling, osint-exposure, attack-surface, detection, interruption-points, mitre-attack, incident-response, digital-footprint]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Phishing, Technique T1566", url: "https://attack.mitre.org/techniques/T1566/", publisher: "MITRE ATT&CK", accessed: 2026-08-25}
  - {title: "Phishing attacks: defending your organisation", url: "https://www.ncsc.gov.uk/guidance/phishing", publisher: "UK NCSC", accessed: 2026-08-25}
  - {title: "2025 Data Breach Investigations Report", url: "https://www.verizon.com/business/resources/reports/2025-dbir-data-breach-investigations-report.pdf", publisher: "Verizon Business", accessed: 2026-08-25}
  - {title: "ENISA Threat Landscape 2024", url: "https://www.enisa.europa.eu/sites/default/files/2024-11/ENISA%20Threat%20Landscape%202024_0.pdf", publisher: "ENISA", accessed: 2026-08-25}
  - {title: "Twitter investigation report", url: "https://www.dfs.ny.gov/Twitter_Report", publisher: "NY State Department of Financial Services", accessed: 2026-08-25}
  - {title: "2024 Internet Crime Report", url: "https://www.ic3.gov/AnnualReport/Reports/2024_IC3Report.pdf", publisher: "FBI IC3", accessed: 2026-08-25}
related: [sedef.taxonomy, sedef.technical_controls, sedef.resilience]
---

# The attack lifecycle from a defender's view — where to interrupt it

**Summary.** Social-engineering campaigns have a repeatable shape: the attacker learns about the target, establishes a channel and a reason to be trusted, applies pressure, obtains an action, and converts that action into money or access. Modelling it this way is only useful if it produces **interruption points** — specific, ownable places where a control can break the chain. This file walks the lifecycle and enumerates those points, with the honest observation that the cheapest and most reliable interruptions are almost never at the "spot the phish" stage. It also covers the exposure inventory: what an organisation leaks about itself without noticing, how to enumerate that, and how to reduce it without pretending that obscurity is a control.

> ⚠️ This file is written for defenders performing threat modelling of their own organisation. It describes *categories* of exposure so they can be inventoried and reduced. It does not provide reconnaissance methodology, tooling, or guidance on researching a target you do not own.

## Key facts

| Phase | Defender's question | Strongest interruption |
|---|---|---|
| 0. Exposure | What do we publish that makes us targetable? | Reduce process disclosure; suppress finance-role identification; publish nothing that answers a helpdesk verification question |
| 1. Selection | Who in our organisation is worth attacking? | Apply role-based hardening to finance, HR, IT helpdesk, executive assistants |
| 2. Channel establishment | Can a stranger reach our people? | DMARC/SPF/DKIM, gateway, external banners, blocked lookalike domains |
| 3. Trust establishment | What signals do our people accept as proof of identity? | Replace identity signals with process; ban knowledge-based verification |
| 4. Pressure | Can an urgent request bypass process? | Mandatory cooling-off; no-exception policy; documented escalation |
| 5. Action | What can one deceived person do alone? | Phishing-resistant MFA; dual authorisation; least privilege |
| 6. Conversion | Can value leave without a second check? | Payment holds, callback, egress controls, DLP, recall procedures |
| 7. Persistence/expansion | Would we notice? | Detection engineering, inbox-rule alerts, impossible travel, PAM session logs |

## 1. Why a kill-chain view, and its limits

Lockheed Martin's Cyber Kill Chain and MITRE ATT&CK both give a phase model. ATT&CK is the more useful for this domain because it maps phishing explicitly into Initial Access as **T1566** with sub-techniques for attachment (`.001`), link (`.002`), delivery via service (`.003`) and voice (`.004`), and lists concrete mitigations: M1049 antivirus/antimalware, M1047 audit, M1031 network intrusion prevention, M1021 restrict web-based content, M1054 software configuration (SPF/DKIM/DMARC) and M1017 user training.

The limit of any kill chain here is that **pure fraud campaigns never enter your network at all**. A BEC that ends in a wire transfer has no malware, no lateral movement, no exfiltration in the technical sense. IC3's 2024 figures — US$2.77 billion of BEC loss — are almost entirely outside the reach of an EDR console. So this file uses a lifecycle that covers both the intrusion path and the pure-fraud path, and marks which interruption points apply to each.

## 2. Phase 0 — Exposure: what you leak without realising

Every organisation publishes, involuntarily, an operating manual for social engineering itself. The purpose of an exposure inventory is not secrecy — most of this information has legitimate reasons to be public — but *awareness of which controls it invalidates*.

### 2.1 The categories to inventory

**People and roles.** Names, titles, reporting lines and start dates from professional networks, conference programmes, press releases, award submissions and company registry filings. New starters are a recognised target because they do not yet know what is normal. Finance staff, executive assistants and IT helpdesk staff are the highest-value identifications.

**Process disclosure.** This is the most underrated category. Job adverts describe your systems ("experience with [named ERP] and [named payment platform]"). Case studies describe your approval workflows. Conference talks by your own security team describe your controls. Supplier press releases confirm who you buy from. Procurement portals list your vendors. Court filings and tenders publish contract values and payment terms.

**Email and identity format.** Address format is trivially derivable from any one published address. This is not fixable and should not be treated as a control.

**Technical footprint.** DNS records, certificate transparency logs, public cloud storage, exposed developer artefacts, and the mail infrastructure your SPF record enumerates.

**Physical and temporal.** Site photographs showing badge design and reception layout; office move announcements; holiday closures; financial reporting calendars; conference attendance that tells an attacker who is out of the office and unreachable.

**Personal exposure of key staff.** Personal social accounts revealing family names, pets, schools, travel and — critically — the answers to knowledge-based verification questions used by helpdesks and banks.

**Breach and credential exposure.** Corporate addresses appearing in third-party breach corpora, and reused passwords associated with them.

### 2.2 How to run the inventory

Treat it as a scheduled, documented exercise owned by security with communications and HR at the table. A practical cadence is annual, plus after any major announcement.

1. **Scope and authorise it in writing.** You are inventorying *your own* footprint. Keep it to sources anyone can see without authentication and without interacting with staff.
2. **Enumerate by category** using the list above; record each item, where it appears, who owns it, and whether it can be reduced.
3. **Score by what it unlocks**, not by how sensitive it feels. The question is: *does this item let an attacker answer a verification question, impersonate a role convincingly, or identify a process to bypass?*
4. **Produce two outputs**: a reduction plan for items that can be removed or generalised, and — more importantly — a **control-invalidation list** stating which of your verification procedures are now worthless because their inputs are public.
5. **Feed it into training.** Showing a finance team the publicly available description of their own approval process is the single most effective awareness intervention available, far more so than a generic module.

### 2.3 Reduction that is worth doing

- Remove direct dial numbers and individual email addresses for finance and payables from public pages; publish a shared, monitored channel instead.
- Generalise job adverts: describe skills, not your named systems and versions.
- Review case studies and conference talks for workflow disclosure before publication.
- Ask staff — do not require — to limit public identification of security-sensitive roles.
- **Abolish knowledge-based verification** rather than trying to protect the knowledge. Mother's maiden name, first school, employee number and date of birth are all effectively public. See file `06` §5.
- Monitor for lookalike domain registrations against your brand and your top suppliers, with a standing takedown process (file `06` §8).

> ⚠️ Do not confuse reduction with defence. The correct mental model is: **assume the attacker knows everything you have ever published, plus your org chart, plus your suppliers.** Design the controls to survive that.

## 3. Phase 1 — Selection

Attackers choose targets by *what the target can do*, not by seniority alone. The recurring high-value roles are:

- **Accounts payable and treasury** — can move money.
- **IT helpdesk / service desk** — can reset credentials and MFA factors. This is now the single most attacked function in large enterprises; the MGM and Caesars incidents of September 2023 turned on it.
- **Executive assistants** — hold delegated authority and calendar context.
- **HR and payroll** — can change bank details and hold identity documents.
- **Developers and cloud administrators** — hold keys.
- **New starters** — do not know what normal looks like.
- **Outsourced support** — often has broad read access with weaker controls; the Coinbase May 2025 insider bribery case is the clearest example.

**Interruption point 1.** Maintain an explicit register of these roles and apply *differential hardening*: hardware security keys mandatory, no MFA self-service reset, stricter conditional access, role-specific training, and named escalation contacts. This is cheap and it is where the marginal control spend performs best.

## 4. Phase 2 — Channel establishment

The attacker needs a way to reach the person: email, SMS, phone, a messaging app, a professional network, a QR code, a compromised website, or physical presence.

**Interruption point 2 — deny the easy channels.**
- DMARC at `p=reject` on all owned domains, including parked and legacy ones, stops exact-domain spoofing of you.
- Secure email gateway with attachment detonation and URL rewriting, understanding its limits (file `04` §2).
- External-sender banners, and a distinct banner for first-time senders and for lookalike display names matching internal staff.
- Register and defensively hold obvious lookalike domains; monitor certificate transparency for new ones.
- Block or quarantine inbound mail from newly registered domains.
- Policy that business is not conducted over consumer messaging apps, so a WhatsApp approach from "the CEO" is itself an anomaly.

**What this cannot stop:** a message from a genuinely compromised supplier mailbox, a phone call, a QR code on a poster, or an approach on a personal device. Channel denial is necessary and insufficient.

## 5. Phase 3 — Trust establishment

This is the phase defenders most often mis-model. The attacker's task is to supply signals your people accept as proof. Those signals are, in ascending order of persuasiveness: a familiar display name, a correct logo and signature block, correct internal jargon, knowledge of a real project, a reply inside a real thread, a phone call, a video call with a recognisable face.

**Interruption point 3 — decouple authorisation from identity signals.** Every one of the signals above can now be forged, up to and including a live video call (Arup, 2024, ~US$25 m). The only durable response is structural:

- **Nominate the verification channel in advance.** "Payment instructions are verified by calling the number recorded in the vendor master file" — a rule that does not care how convincing the requester was.
- **Never verify using contact details supplied in the request.** This is the single most important sentence in the domain.
- **Pre-agreed code words** for verbal high-value authorisation, rotated, never stored in the systems being protected.
- **Kill knowledge-based verification** at the helpdesk; replace with an authenticated workflow — a push to an enrolled device, a manager attestation through a ticketing system, or an in-person/verified-video check with a documented process.
- **Publish negative rules** widely: IT will never ask for your password or an MFA code; the CEO will never request a payment by email or WhatsApp; procurement will never accept bank details by email. Negative rules are easier to apply under pressure than positive judgement.

## 6. Phase 4 — Pressure

The manufactured deadline is the attacker's only perishable asset. Every documented case in file `07` contains one: a deal that must close today, a fine that accrues, an account that will lock, a VPN that must be fixed before a meeting, an executive who is boarding a flight.

**Interruption point 4 — make urgency inert.**
- **Mandatory cooling-off** on irreversible actions: high-value payments cannot execute for a defined window, during which the callback happens.
- **A no-exceptions clause with executive sponsorship**, stating in writing that no one, including the CEO, may request bypass of payment or access controls, and that staff who refuse such a request will be supported. Publish it; refer to it in training; have the CEO say it personally at least annually.
- **Remove the social cost of delay.** Attacks work partly because saying "I need to verify this" feels like an accusation. A pre-existing, universal policy converts it from an accusation into a procedure.
- **Alert on urgency language** at the gateway as a low-confidence signal combined with higher-confidence ones (new domain, external, finance recipient).

## 7. Phase 5 — The requested action

Actions cluster into four kinds, and the control differs by kind.

**(a) Authenticate.** The victim enters credentials, or approves an MFA prompt, or reads out a code.
*Interruption point 5a:* **phishing-resistant MFA** (FIDO2/WebAuthn or PKI). CISA identifies these as the only phishing-resistant forms and names SMS, voice, app OTP and plain push as vulnerable to phishing, SS7 exploitation, SIM swap and push bombing. Where FIDO2 is not yet everywhere, number matching removes the blind-approval failure. Conditional access with device compliance blocks a stolen session on an unmanaged device.

**(b) Execute or install.** Open an attachment, enable a macro, install a tool, plug in a device.
*Interruption point 5b:* application allowlisting, macro blocking from the internet, EDR, removable-media policy, and least-privilege endpoints so no ordinary user can install software.

**(c) Pay or change payment data.** Wire funds, change a bank account, buy gift cards.
*Interruption point 5c:* dual authorisation, callback on a known-good number, vendor-master change control with a hold period, out-of-band confirmation to the *previous* known contact, and a hard rule that gift cards are never a legitimate business instrument.

**(d) Disclose or grant.** Send a data extract, reset someone's MFA, add a role, grant portal access.
*Interruption point 5d:* helpdesk identity proofing, four-eyes on privilege grants, just-in-time access with expiry, and DLP on bulk exports.

## 8. Phase 6 — Conversion

For fraud, conversion is the transfer itself and its rapid onward movement through mule accounts. For intrusion, it is exfiltration, ransomware deployment, or persistent access sale.

**Interruption point 6 — the last controllable moment.**
- **Payment-side:** bank-level anomaly detection on new beneficiaries and unusual amounts; confirmation-of-payee schemes where available; a documented internal procedure for immediate recall. Speed matters enormously — the FBI's recovery mechanisms work in hours, not days. Report to the bank and to the national reporting body immediately (file `09` §7).
- **Data-side:** egress monitoring, DLP, alerting on large downloads from SaaS platforms, and blocking unsanctioned file-sharing destinations.
- **Session-side:** ability to revoke all sessions and refresh tokens for an identity in one action, and to force reauthentication. Many organisations reset the password and leave the stolen session alive.

## 9. Phase 7 — Persistence and expansion, and whether you would notice

If the attacker keeps access, the tells are well known and detectable. The NY DFS report on the July 2020 Twitter compromise is instructive on the failure mode: 130 accounts compromised and roughly US$118,000 in bitcoin stolen, in an environment where over 1,000 employees had access to sensitive internal account-management tooling, app-based MFA could be socially engineered, and the CISO role had been vacant since December 2019. The interruption points were all organisational.

**Detection signals worth engineering** (expanded in file `04` §10):
- New or modified mailbox forwarding and inbox rules, especially rules that delete or file messages containing "invoice", "payment", "bank".
- OAuth application consent grants by users.
- Impossible travel and new-country sign-ins, weighted by role.
- MFA method registration and reset events — a new factor added to a privileged account is a high-fidelity signal.
- Helpdesk password/MFA reset volume by agent and by target account privilege.
- First-time access to a sensitive repository or bulk read by a support account.
- Sign-ins from anonymising infrastructure, and from residential proxy ranges.

## 10. The interruption points, consolidated

A one-page version for a threat-modelling workshop. Each line should have a named owner and a stated current state.

1. **Exposure reduction and control-invalidation list** — communications/HR/security, annual.
2. **Role register and differential hardening** for finance, helpdesk, EAs, HR, developers, outsourced support.
3. **Channel denial**: DMARC `p=reject`, gateway, external banners, lookalike monitoring, no-business-on-consumer-apps policy.
4. **Verification decoupled from identity signals**: known-good-number callback, code words, no knowledge-based verification.
5. **Urgency made inert**: cooling-off periods, published no-exceptions clause, no social cost for delay.
6. **Action controls by kind**: phishing-resistant MFA; allowlisting and macro blocking; dual authorisation on payments; four-eyes on privilege grants.
7. **Conversion controls**: payment anomaly detection, immediate-recall procedure, egress/DLP, one-action session revocation.
8. **Detection engineering** for the persistence signals above, with alerts routed to a team that can act at 02:00.
9. **Reporting capability**: a one-click report button, a no-blame culture, and a triage function that can correlate reports into a campaign — the mechanism Lain et al. showed is practical at scale.
10. **Rehearsed response**: a playbook per scenario (credential phish, BEC, helpdesk compromise, deepfake authorisation attempt), exercised at least annually with finance and communications in the room.

The pattern across all ten: **only one of them (number 9) depends on a person recognising an attack.** That is the correct proportion.

## Sources

- [MITRE ATT&CK T1566 Phishing](https://attack.mitre.org/techniques/T1566/) — MITRE (sub-techniques and mitigations)
- [Phishing attacks: defending your organisation](https://www.ncsc.gov.uk/guidance/phishing) — UK NCSC (four-layer model)
- [2025 Data Breach Investigations Report](https://www.verizon.com/business/resources/reports/2025-dbir-data-breach-investigations-report.pdf) — Verizon Business
- [ENISA Threat Landscape 2024](https://www.enisa.europa.eu/sites/default/files/2024-11/ENISA%20Threat%20Landscape%202024_0.pdf) — ENISA
- [Twitter investigation report](https://www.dfs.ny.gov/Twitter_Report) — NY State Department of Financial Services
- [2024 Internet Crime Report](https://www.ic3.gov/AnnualReport/Reports/2024_IC3Report.pdf) — FBI IC3
- [Implementing Phishing-Resistant MFA](https://www.cisa.gov/sites/default/files/publications/fact-sheet-implementing-phishing-resistant-mfa-508c.pdf) — CISA

## Open questions

- The **Lockheed Martin Cyber Kill Chain** is referenced from general knowledge; the original white paper was not fetched.
- **Confirmation of Payee** schemes vary by jurisdiction (UK, EU under the Instant Payments Regulation, South Africa's evolving arrangements). Verify local availability before recommending it as a control.
- The claim that the **service desk is now the most attacked enterprise function** is well supported by the 2023 casino incidents and vendor reporting but is not backed here by a quantified public dataset. Marked `needs-verification` as a quantitative claim.
