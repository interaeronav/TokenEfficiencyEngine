---
id: sedef.taxonomy
title: Attack taxonomy — recognising social engineering by what the victim experiences
domain: 33_social_engineering_defence
tags: [phishing, spear-phishing, whaling, smishing, vishing, quishing, bec, pretexting, baiting, tailgating, watering-hole, mfa-fatigue, sim-swap, tech-support-scam, romance-scam, pig-butchering, deepfake, insider-threat, indicators]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "2024 Internet Crime Report", url: "https://www.ic3.gov/AnnualReport/Reports/2024_IC3Report.pdf", publisher: "FBI IC3", accessed: 2026-08-25}
  - {title: "APWG Phishing Activity Trends Report, Q4 2024", url: "https://docs.apwg.org/reports/apwg_trends_report_q4_2024.pdf", publisher: "APWG", accessed: 2026-08-25}
  - {title: "ENISA Threat Landscape 2024", url: "https://www.enisa.europa.eu/sites/default/files/2024-11/ENISA%20Threat%20Landscape%202024_0.pdf", publisher: "ENISA", accessed: 2026-08-25}
  - {title: "Phishing, Technique T1566", url: "https://attack.mitre.org/techniques/T1566/", publisher: "MITRE ATT&CK", accessed: 2026-08-25}
  - {title: "Social engineering (security)", url: "https://en.wikipedia.org/wiki/Social_engineering_(security)", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Business email compromise", url: "https://en.wikipedia.org/wiki/Business_email_compromise", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "SIM swap scam", url: "https://en.wikipedia.org/wiki/SIM_swap_scam", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Pig butchering scam", url: "https://en.wikipedia.org/wiki/Pig_butchering_scam", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Implementing Phishing-Resistant MFA", url: "https://www.cisa.gov/sites/default/files/publications/fact-sheet-implementing-phishing-resistant-mfa-508c.pdf", publisher: "CISA", accessed: 2026-08-25}
related: [sedef.overview, sedef.lifecycle, sedef.technical_controls, sedef.cases, sedef.personal]
---

# Attack taxonomy — recognising social engineering by what the victim experiences

**Summary.** This is a recognition catalogue, not an attack catalogue. Each entry describes what the targeted person actually sees and feels, the structural indicators that survive changes in wording and branding, the typical loss where a dated figure exists, and the controls that stop or contain it. The organising insight is that **content-based indicators decay quickly** — bad grammar, obvious spoofs, crude logos — while **structural indicators are durable**: an unexpected channel switch, a manufactured deadline, a request that bypasses a documented process, a change to payment details, or pressure to keep something confidential. Train on the structure.

> ⚠️ Nothing in this file provides usable lure content, pretext scripts, target-selection methodology or product-evasion technique. Where a mechanism must be named for defenders to recognise it, only the victim-side view and the control are given.

## Key facts

| Attack type | Typical dated loss / prevalence | Primary control that works |
|---|---|---|
| Bulk phishing | 193,407 IC3 complaints (2024); 989,123 attacks observed in Q4 2024 (APWG) | Phishing-resistant MFA; DMARC enforcement; reporting button |
| Spear phishing / whaling | Present in most targeted intrusions; MITRE T1566.001/.002 | Hardware security keys; attachment and macro controls |
| BEC / invoice fraud | 21,442 complaints, **US$2.77 bn** (IC3 2024); average wire request US$128,980 (APWG Q4 2024) | Callback verification on a known-good number; dual authorisation; vendor bank-change procedure |
| Smishing | Dominant mobile vector; toll-road SMS floods noted in APWG Q4 2024 | Number blocking, carrier reporting, never-follow-links rule for SMS |
| Vishing | MITRE T1566.004 Spearphishing Voice | Helpdesk identity proofing; callback culture |
| Quishing (QR) | "Significant surge" (ENISA 2024) | Mobile device management; URL preview; treat QR as an untrusted link |
| MFA fatigue / push bombing | Named by CISA as a distinct threat class | Number matching; better, FIDO2 |
| SIM swap | FBI: **US$68 m** lost in 2021, vs US$12 m total 2018–2020; 2,026 complaints peak in 2022 | Carrier port-out PIN/lock; remove SMS as a recovery factor |
| Tech support fraud | **US$1.46 bn** (IC3 2024) | Never-inbound-support rule; no remote-access to cold callers |
| Investment / pig-butchering fraud | **US$6.57 bn** investment fraud (IC3 2024); ~US$12.4 bn crypto fraud in 2024 (Chainalysis) | Cooling-off; independent advice; platform verification |
| Deepfake video/voice fraud | Arup, 2024: **~US$25 m**; UK energy firm, 2019: €220,000 | Out-of-band callback; pre-agreed code words; process not identity |
| Insider recruitment | Coinbase, May 2025: bribed overseas support agents; remediation estimated up to **US$400 m** | Least privilege; access analytics; dual control on data export |

---

## 1. Phishing and its variants

### 1.1 Bulk phishing
**What the victim experiences.** An email appearing to come from a service they use — mailbox provider, bank, courier, payroll — saying something needs attention now. Clicking leads to a login page that looks correct, which may then "fail" and redirect to the real service so the victim never notices.

**Durable indicators.** Authentication requested from a link rather than a bookmark or app; a lookalike domain, an unrelated host's subdomain, or a generic cloud-hosting domain; loss-framed action with a deadline; a request outside any process the recipient initiated.

**Typical loss.** Individually small, in aggregate enormous. Its real cost is as *initial access* — the credential is the product.

**Controls.** Phishing-resistant MFA (FIDO2/WebAuthn) is decisive: the credential is bound to the origin, so a victim who types everything into a fake site still cannot authenticate the attacker. DMARC at `p=reject` stops direct spoofing of your domain. A one-click report button converts users into sensors.

### 1.2 Spear phishing
**What the victim experiences.** A message that is *correct about them*: their project, their manager's name, a real supplier, a real meeting. Nothing feels wrong.

**Durable indicators.** Correctness is not evidence of legitimacy. The structural tells remain: an unexpected attachment type, a request to enable content or macros, a reply-to address that differs from the display address, a first-time-sender warning on a familiar name.

**Controls.** Hardware keys; block or sandbox risky attachment types; disable Office macros from the internet by default; external-sender banners; attachment detonation. MITRE ATT&CK lists T1566.001 (attachment), T1566.002 (link), T1566.003 (via service) and T1566.004 (voice), with mitigations M1049 antivirus, M1031 network intrusion prevention, M1021 restrict web-based content, M1054 software configuration (SPF/DKIM/DMARC) and M1017 user training.

### 1.3 Whaling
Spear phishing aimed at executives, or impersonating them; the *authority of the impersonated party* is the payload. See file `01` §8 for why seniority increases exposure.

### 1.4 Clone phishing and thread hijacking
**What the victim experiences.** A message they have genuinely seen before, resent with an altered link or attachment — or, worse, a reply inside a real, ongoing thread, quoting real prior content. This usually follows a compromise of one participant's mailbox, sometimes at a supplier.

**Durable indicators.** A resent message with an unexplained "updated version"; a reply that arrives from a slightly different address than the rest of the thread; a change in the requested action mid-thread, especially concerning payment.

**Controls.** This variant is close to undetectable by content. It is defeated by process: **any change to payment details is verified by callback regardless of how the request arrived**. Also by mailbox-compromise detection at the supplier end (impossible-travel alerts, new inbox rules, mass-forward rules).

---

## 2. Channel variants

### 2.1 Smishing (SMS)
**What the victim experiences.** A short text: a failed delivery, an unpaid toll, a bank alert, a "hi mum/dad, this is my new number." Mobile context is the attacker's advantage — small screen, truncated URL, one-handed, in transit. The DBIR 2026 landing summary notes mobile click rates roughly 40% higher than desktop.

**Durable indicators.** Any SMS containing a link and a deadline; a shortened or unfamiliar domain; a "new number" claim from a family member; a request to move to WhatsApp.

**Notable pattern.** APWG's Q4 2024 report records Chinese phishing groups using new kits and `.TOP` domains to flood US residents with toll-road impersonation SMS — an example of an industrialised smishing campaign.

**Controls.** A household and workplace rule that **no SMS link is ever followed** — navigate to the service independently. Report to the national spam short code. For businesses, register your sender IDs where the jurisdiction supports it and publish that you never send links by SMS.

### 2.2 Vishing (voice)
**What the victim experiences.** A phone call from someone who knows things about them — an IT helpdesk troubleshooting VPN problems, a bank fraud team, a courier, a government office. Caller ID shows a plausible number. The caller is calm, competent and helpful, and the request is framed as *protecting* the victim.

**Durable indicators.** An inbound call asking the recipient to authenticate, install anything, read out a code, or move money "to a safe account." Any call that discourages hanging up and calling back.

**Controls.** The single rule that defeats nearly all of it: **end the call and dial back on a number you obtained independently.** For organisations: helpdesk identity-proofing procedures that do not rely on knowledge-based questions (see file `06` §5), and an absolute rule that IT will never ask for a code.

### 2.3 Quishing (QR codes)
**What the victim experiences.** A QR code in an email, a PDF, a poster, a parking meter or a restaurant table, which resolves to a credential-harvesting page. Because the code is an image, it often passes text-based mail filters, and because it is scanned with a personal phone, it leaves the corporate security stack entirely.

**Durable indicators.** A QR code delivered by email at all — legitimate business email rarely needs one; a sticker over a printed code in a public place; a code that leads to a login page.

**Prevalence.** ENISA's 2024 Threat Landscape records a "significant surge" in QR-code phishing.

**Controls.** Configure phones to preview the URL before opening; enrol mobile devices so corporate browsing is filtered; policy that corporate authentication is never initiated from a scanned code; physical inspection of public codes for overlays.

---

## 3. Business email compromise and invoice fraud

**What the victim experiences.** Four recurring shapes:
- **CEO fraud.** A senior person emails asking for an urgent, confidential transfer, often relating to an acquisition, and asks the recipient not to discuss it (the FACC case, file `07`).
- **Supplier invoice fraud.** A known supplier writes that their banking details have changed. The invoice, project and amount are all real; only the account number is wrong.
- **Payroll diversion.** An "employee" asks HR to change their salary deposit account — 10% of BEC cash-out methods in Q4 2024 (APWG).
- **Gift card fraud.** A manager urgently needs gift cards bought and the codes photographed. Crude, but 49% of BEC scam attempts in Q4 2024 — it persists because it works on new staff.

**Durable indicators.** Any change to banking details, ever. Urgency combined with confidentiality. A request routed around normal process ("don't go through procurement on this one"). A reply-to differing from the sender. A domain differing by one character, or a free-mail address claiming to be a known person's personal account.

**Typical loss.** IC3 recorded 21,442 BEC complaints and **US$2.77 billion** in 2024; APWG's observed average requested wire in Q4 2024 was US$128,980, nearly double Q3's US$67,145. Historic single-incident losses include Ubiquiti (US$46.7 m, 2015), FACC (€42 m, February 2016) and the Rimasauskas frauds against Google (~US$23 m) and Facebook (~US$98 m), 2013–2015.

**Controls that actually work.** (1) **Callback verification on a known-good number** for every bank-detail change and every payment over a threshold — the number from the signed contract or vendor master file, never one in the email. (2) **Dual authorisation**, so no single deceived person can complete a payment. (3) **A vendor bank-detail change procedure** with a mandatory hold period and a second channel (file `06` §3). (4) **DMARC at enforcement** plus lookalike-domain monitoring. (5) **A cooling-off delay** on high-value payments — urgency is perishable, and delay destroys it.

---

## 4. Pretexting, baiting and physical intrusion

### 4.1 Pretexting
A fabricated scenario providing a reason to ask. The victim experiences a plausible role — auditor, regulator, new supplier contact, IT support, insurance assessor — attached to a request that is individually reasonable. Pretexting is the connective tissue of most other categories.

**Controls.** Identity verification that does not depend on the claimant's own assertions; published rules about what particular parties will *never* ask for; escalation paths that cost the employee nothing to use.

### 4.2 Baiting
Malicious removable media left where a curious person will find it, or an enticing download. The University of Illinois USB-drop study (2016) remains the reference point: of 297 drives dropped on campus, 290 (98%) were picked up and 135 (45%) resulted in the researchers' tracking page being opened.

**Controls.** Disable autorun; block or restrict USB mass storage via endpoint policy; provide a no-blame place to hand in found devices; application allowlisting.

### 4.3 Tailgating and physical intrusion
**What the victim experiences.** Someone with full hands, a delivery, a high-vis vest, a lanyard, or a plausible story asks — often without asking — to be let through a controlled door. Refusing feels rude and confrontational.

**Durable indicators.** Any person entering behind you without badging; contractors without an expected work order; someone in a restricted area who cannot name their host.

**Controls.** Anti-tailgating physical design (turnstiles, mantraps) so politeness is not the control; a challenge culture that is explicitly authorised and never punished; visitor escorting; reception verification of all contractor visits against a booking. **The key insight is the same as everywhere in this domain: do not ask a polite human to be the lock.**

---

## 5. Watering hole attacks

**What the victim experiences.** Nothing. They visit a site they use and trust — an industry association, a supplier portal, a regional news site — which has been compromised to serve malicious content to a target population. The 2013 compromise of a US Department of Labor server is a documented example.

**Durable indicators.** From the user's side, effectively none — a reminder that user vigilance has hard limits.

**Controls.** Browser and OS patching; protective DNS; EDR; application allowlisting; browser isolation for high-risk roles; egress monitoring.

---

## 6. MFA fatigue, push bombing and adversary-in-the-middle

### 6.1 Push bombing / MFA fatigue
**What the victim experiences.** A stream of authentication approval prompts on their phone, often late at night, sometimes accompanied by a message or call from "IT" saying the prompts are a known glitch and asking them to approve one to stop them. The victim approves out of exhaustion or helpfulness. This is what happened at Uber in September 2022 (file `07`).

**Durable indicators.** Any unrequested approval prompt at all. More than one in a row. Any contact urging you to approve.

**Controls.** **Number matching** — the user must type a number shown on the sign-in screen into the authenticator app, so a random approval is impossible. Microsoft made number matching mandatory for all Authenticator push notifications with no user opt-out. Additional context (application name and sign-in location) in the prompt helps. CISA published a dedicated fact sheet on implementing number matching, and treats push bombing as a named threat. Better still: move to FIDO2, where there is no prompt to approve.

### 6.2 Adversary-in-the-middle credential relay
**What the victim experiences.** A login page that behaves *perfectly* — because it is proxying the real service. They enter password and one-time code, are logged in successfully, and notice nothing. The attacker captures the session.

**Durable indicators.** None reliably visible to the user. ENISA's 2024 report records continued escalation of AitM attacks despite MFA adoption.

**Controls.** This is the decisive argument for phishing-resistant MFA. CISA's fact sheet identifies FIDO/WebAuthn and PKI-based MFA as the only phishing-resistant forms, and describes SMS, voice, app-based OTP and plain push as vulnerable to phishing, SS7 exploitation, SIM swap and push bombing. Because a FIDO2 credential is cryptographically bound to the relying-party origin, a proxy on a different domain cannot obtain a usable assertion. Add conditional access with device compliance, token-binding, and short session lifetimes for sensitive apps.

---

## 7. SIM swap

**What the victim experiences.** Their phone abruptly loses network service, sometimes with a message about a SIM change. Within minutes, password resets and one-time codes flow to someone else's device, and bank and cryptocurrency accounts are emptied.

**Durable indicators.** Sudden loss of mobile service with no outage; an unexpected "your SIM has been updated" notice; account-change emails you did not initiate.

**Documented scale.** The FBI reported **US$68 million** in SIM-swap losses in 2021 against US$12 million total for 2018–2020; US complaints rose from about 400 in 2018 to a peak of 2,026 in 2022. Individual cases include Michael Terpin's US$23.8 million loss. UK reports rose sharply from 2023 to 2024, and Kenya's Safaricom reported a large increase into 2025.

**Controls.** Set a port-out PIN or account lock with the carrier; remove SMS as an account-recovery factor; use an authenticator app or hardware key instead; for high-value accounts use a number published nowhere, or no phone factor at all. Organisations should not use SMS OTP for privileged access.

---

## 8. Tech support scams

**What the victim experiences.** A full-screen browser warning with an alarm sound and a number to call, or a cold call claiming to be a well-known software vendor or ISP. The "technician" asks to install remote-access software, presents ordinary system logs as evidence of infection, then sells a fake service, moves money "to protect it", or keeps persistent access. Payout is increasingly via cryptocurrency ATM or gift card.

**Durable indicators.** *Any* inbound contact offering technical help; any request to install remote-access software; any instruction to move money to a "safe account", buy gift cards or use a crypto ATM; pressure not to tell your bank why you are withdrawing.

**Typical loss.** **US$1.46 billion** reported to IC3 in 2024. Victims aged 60+ filed 147,127 complaints with US$4.885 billion in losses across all crime types.

**Controls.** A blunt household rule: legitimate technology companies never call you, and you never install remote-access software for an inbound caller. Bank-side "safe account" scam detection and branch intervention. For organisations: block consumer remote-access tools and alert on installation.

---

## 9. Romance fraud and pig-butchering investment fraud

**What the victim experiences.** Contact via a dating app, a social platform, or an apparently misdirected message. A relationship develops over weeks or months — attentive, consistent, emotionally significant. The other party avoids video, has reasons for delay, and gradually isolates the victim from friends and family. Eventually an investment opportunity appears, usually cryptocurrency on a platform that looks professional. Small withdrawals succeed (the "convincer"). Larger deposits follow. Withdrawal then requires "tax" or "fees". Nothing comes back.

**Origins and structure.** The Chinese term 杀猪盘 (*shā zhū pán*, "killing pig plate") describes fattening the victim before slaughter; the pattern emerged around 2016. Much of the labour is performed by trafficking victims held in compounds in Cambodia, Myanmar, Laos, the Philippines and Thailand — the UN Human Rights Office has stated hundreds of thousands of people have been trafficked into these operations. **This matters for tone: the person on the other end is frequently a victim too, and awareness material that mocks either party is both wrong and ineffective.**

**Documented scale.** IC3 recorded **US$6.57 billion** in investment fraud losses in 2024. Chainalysis put total cryptocurrency fraud at roughly **US$12.4 billion in 2024**, with pig-butchering growing nearly 40% year on year. Individual losses commonly reach six figures, and the IRS has documented losses up to US$2 million. In an extreme case the CEO of Heartland Tri-State Bank embezzled US$47 million into such a scheme and was sentenced to 24 years in August 2024 — this is not only a consumer risk.

**Durable indicators.** A new online contact who introduces investing; any platform recommended by someone met online; guaranteed returns; pressure to increase deposits; fees demanded before withdrawal; reluctance to appear on video (an indicator now weakened by deepfakes — see file `08`).

**Controls.** A personal rule never to take investment direction from anyone met online; independent verification of any platform with the national financial regulator; a trusted-person check before any large transfer. For banks: transaction-pattern detection and mandatory intervention scripts. For families: a named person consulted before any large financial move (file `09`).

---

## 10. Recruitment and job-offer scams

**What the victim experiences.** An unsolicited but flattering approach about a role, often via a messaging app or a professional network. The process is fast and entirely remote. At some point the candidate is asked to pay for equipment or training, to complete "tasks" that require depositing their own money for commission (gamified task scams), to provide identity documents and banking details for "onboarding", or to install a "assessment tool" that is malware. A variant targets employers rather than candidates: fraudulent applicants using stolen or synthetic identities to obtain remote employment and, from there, internal access.

**Durable indicators.** Recruitment conducted entirely through a consumer messaging app; an offer without a real interview; any request for money from a candidate; identity documents demanded before a formal offer; an interview requiring software installation.

**Scale.** The FTC recorded job scam losses rising more than threefold from 2020, with gamified task scams driving record losses (Data Spotlight, 12 December 2024).

**Controls.** Individuals: verify the recruiter via the employer's published careers page and switchboard; never pay to be employed. Employers: identity verification at onboarding with a live video check against documents, equipment shipped only to verified addresses, and monitoring for impossible travel and remote-access tools among new starters.

---

## 11. Deepfake audio and video fraud

**What the victim experiences.** A voice on the phone that is unmistakably their manager, CFO or child — or, in the most consequential documented case, an entire video conference in which multiple apparently-real colleagues discuss a confidential transaction.

**The Arup case.** In 2024 the engineering firm Arup lost approximately **US$25 million** in Hong Kong after fraudsters used AI-generated video and audio to impersonate senior officials, deceiving an employee into making multiple transfers; reported May 2024, and the reference incident for real-time video deepfake fraud. Earlier, in 2019, a UK energy firm's CEO transferred **€220,000** to a Hungarian account after a caller reportedly used audio deepfake technology to impersonate the parent company's chief executive.

**Durable indicators.** **There is no reliable perceptual indicator.** Do not teach staff to look for blinking artefacts or audio glitches; they will be wrong within a release cycle. The durable indicators are procedural — a transaction outside the documented process, secrecy, urgency, a request to skip approval, an unusual meeting platform, refusal to complete the request through the normal system.

**Controls.** Out-of-band callback on a directory number, not one from the meeting. Pre-agreed code words for high-value verbal authorisation, corporate and family (file `09` §4). **Process over identity** — a payment is authorised by a dual-control workflow, not by recognising a face. Detection technology should not be relied on: the Deepfake Detection Challenge's winning model reached 65% accuracy on a 4,000-video holdout, and MIT research found humans 69–72% accurate on a sample.

---

## 12. Supply chain and vendor impersonation

**What the victim experiences.** Contact from a real supplier — sometimes from the supplier's genuinely compromised mailbox, sometimes from a lookalike domain. Because the relationship is real, scepticism is low. A supplier's own compromise also becomes the customer's incident: third parties were involved in **30% of breaches** in the 2025 DBIR, roughly double the previous year.

**Durable indicators.** Bank detail changes; new contacts at a known supplier who cannot be verified through the existing account manager; invoices arriving through an unusual channel; sudden requests for shared-portal credentials.

**Controls.** Vendor master data change control with callback; contractual security and notification obligations; lookalike-domain monitoring for key suppliers as well as your own; just-in-time supplier access (file `06` §3).

---

## 13. Insider recruitment and bribery

**What the victim experiences (from the organisation's side).** No perimeter event at all. Someone with legitimate access uses it illegitimately, either because they were recruited, bribed, coerced, or because they were themselves deceived into believing the request was authorised.

**Documented cases.** Lapsus$ obtained credentials in part through recruitment of accomplices with direct network access, alongside SIM swapping of privileged employees — behaviour examined by the US Cyber Safety Review Board in 2023. In May 2025, Coinbase disclosed that criminals had **bribed overseas customer-support agents** to steal customer data for use in subsequent social-engineering attacks; the company refused a US$20 million ransom, offered a US$20 million reward instead, and estimated remediation costs of up to **US$400 million**.

**Durable indicators.** Unusual bulk data access by support or operations staff; access outside normal hours or locations; export and screenshot functions used at volume; privilege far exceeding job requirement.

**Controls.** Least privilege and just-in-time access; behaviour analytics tuned for bulk-read patterns; dual control on data export; separation between those who may view and those who may extract; joiner-mover-leaver hygiene (file `06` §4); confidential reporting routes; and treating outsourced support with the same access controls as employees.

## Sources

- [2024 Internet Crime Report](https://www.ic3.gov/AnnualReport/Reports/2024_IC3Report.pdf) — FBI IC3
- [APWG Phishing Activity Trends Report, Q4 2024](https://docs.apwg.org/reports/apwg_trends_report_q4_2024.pdf) — APWG
- [ENISA Threat Landscape 2024](https://www.enisa.europa.eu/sites/default/files/2024-11/ENISA%20Threat%20Landscape%202024_0.pdf) — ENISA
- [MITRE ATT&CK T1566 Phishing](https://attack.mitre.org/techniques/T1566/) — MITRE
- [Social engineering (security)](https://en.wikipedia.org/wiki/Social_engineering_(security)) — Wikipedia (USB drop study, historical incidents)
- [Business email compromise](https://en.wikipedia.org/wiki/Business_email_compromise) — Wikipedia (Ubiquiti, FACC, Rimasauskas figures)
- [SIM swap scam](https://en.wikipedia.org/wiki/SIM_swap_scam) — Wikipedia (FBI loss figures, Terpin case)
- [Pig butchering scam](https://en.wikipedia.org/wiki/Pig_butchering_scam) — Wikipedia (origin, trafficking, Chainalysis figures)
- [Deepfake](https://en.wikipedia.org/wiki/Deepfake) — Wikipedia (Arup, 2019 UK energy firm, detection accuracy)
- [Implementing Phishing-Resistant MFA](https://www.cisa.gov/sites/default/files/publications/fact-sheet-implementing-phishing-resistant-mfa-508c.pdf) — CISA, October 2022
- [How to use number matching in MFA](https://learn.microsoft.com/en-us/entra/identity/authentication/how-to-mfa-number-match) — Microsoft
- [Coinbase](https://en.wikipedia.org/wiki/Coinbase) — Wikipedia (May 2025 insider bribery incident)
- [FTC Data Spotlight index](https://www.ftc.gov/news-events/data-visualizations/data-spotlight) — US Federal Trade Commission

## Open questions

- The **University of Illinois USB study (2016)** figures (297 dropped, 290 picked up, 135 opened) are cited via Wikipedia's summary; the primary paper (Tischer et al., "Users Really Do Plug in USB Drives They Find") should be cited directly.
- **Chainalysis 2024 crypto fraud figure (US$12.4 bn)** is cited via Wikipedia; verify against the Chainalysis Crypto Crime Report directly before quoting in a formal document.
- **CISA number-matching fact sheet** could not be fetched (HTTP 403); its existence and subject are confirmed via the phishing-resistant MFA fact sheet and Microsoft documentation, but the specific recommendations are summarised from the related CISA MFA guidance rather than read directly. Marked `needs-verification`.
- The **US$75 bn aggregate pig-butchering figure** reported in some coverage is a single academic estimate with wide uncertainty and is deliberately not used as a headline here.
