---
id: sedef.technical_controls
title: Technical controls that actually reduce social-engineering risk
domain: 33_social_engineering_defence
tags: [spf, dkim, dmarc, email-security, fido2, webauthn, passkeys, mfa, conditional-access, number-matching, dns-filtering, edr, payment-controls, pam, zero-trust, detection-engineering, incident-response]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "DMARC Overview", url: "https://dmarc.org/overview/", publisher: "DMARC.org", accessed: 2026-08-25}
  - {title: "Implementing Phishing-Resistant MFA", url: "https://www.cisa.gov/sites/default/files/publications/fact-sheet-implementing-phishing-resistant-mfa-508c.pdf", publisher: "CISA", accessed: 2026-08-25}
  - {title: "Passkeys", url: "https://fidoalliance.org/passkeys/", publisher: "FIDO Alliance", accessed: 2026-08-25}
  - {title: "How number matching works in MFA push notifications", url: "https://learn.microsoft.com/en-us/entra/identity/authentication/how-to-mfa-number-match", publisher: "Microsoft", accessed: 2026-08-25}
  - {title: "Phishing attacks: defending your organisation", url: "https://www.ncsc.gov.uk/guidance/phishing", publisher: "UK NCSC", accessed: 2026-08-25}
  - {title: "Telling users to avoid clicking bad links still isn't working", url: "https://www.ncsc.gov.uk/blog-post/telling-users-to-avoid-clicking-bad-links-still-isnt-working", publisher: "UK NCSC", accessed: 2026-08-25}
  - {title: "Phishing, Technique T1566", url: "https://attack.mitre.org/techniques/T1566/", publisher: "MITRE ATT&CK", accessed: 2026-08-25}
  - {title: "Twitter investigation report", url: "https://www.dfs.ny.gov/Twitter_Report", publisher: "NY State Department of Financial Services", accessed: 2026-08-25}
related: [sedef.lifecycle, sedef.human_controls, sedef.resilience]
---

# Technical controls that actually reduce social-engineering risk

**Summary.** The controls in this file are ordered by how much risk they remove per unit of effort, not by how they appear in a compliance framework. The two that dominate everything else are **phishing-resistant MFA** and **payment process controls** — the first because it makes stolen credentials useless, the second because it makes a deceived employee unable to complete a fraudulent transfer alone. Email authentication, gateways, filtering and endpoint controls are necessary supporting layers with real and specific limits, which are stated here rather than glossed over. The file closes with detection engineering and incident-response playbooks, because the assumption throughout is that some attacks succeed.

> ⚠️ This file describes defensive configuration. It names attack categories only to the extent needed to explain why a control is or is not effective, and gives no product-evasion detail.

## Key facts

| Control | What it stops | What it does not stop |
|---|---|---|
| SPF + DKIM + DMARC `p=reject` | Exact-domain spoofing of your domain | Lookalike domains, display-name spoofing, compromised real accounts |
| Secure email gateway | Known-bad, bulk campaigns, malicious attachments | Zero-hour targeted lures, QR codes, thread hijacking from a real mailbox, non-email channels |
| **FIDO2/WebAuthn (passkeys, security keys)** | Credential phishing, adversary-in-the-middle relay, replay | Malware on an authenticated endpoint, insider misuse, session theft post-auth |
| PKI/smart card MFA | Same as above where infrastructure is mature | Same |
| Number matching on push | Blind approval / push bombing | Real-time relay if the user is actively deceived into typing the number |
| SMS or app OTP | Password-only compromise | Phishing, AitM relay, SIM swap, SS7 |
| Conditional access + device compliance | Use of stolen credentials from unmanaged devices | Attacks from a compromised managed device |
| Dual authorisation + callback on payments | Almost all BEC losses | Collusion; compromise of the callback directory |
| PAM with session recording | Standing privilege abuse | Non-privileged fraud paths |

---

## 1. Email authentication: SPF, DKIM, DMARC

**What they are.** SPF publishes which hosts may send mail for your domain. DKIM cryptographically signs messages so a receiver can verify the signing domain. **DMARC** ties both to the domain the *user actually sees* (the `From:` header) through **alignment**, tells receivers what to do with non-aligned mail, and provides reporting back to the domain owner.

**Alignment is the point.** SPF and DKIM alone validate envelope and signing domains that a recipient never sees. DMARC's `adkim` and `aspf` tags govern how strictly those must match the visible `From:` domain. Without alignment, authentication is decorative.

**A real policy progression.** DMARC.org's recommended staged deployment, expressed as a practical programme:

| Stage | Record | Duration | What you do |
|---|---|---|---|
| 0 | Inventory | 2–4 weeks | Enumerate every system that sends as your domain: marketing platforms, ticketing, ERP, payroll, monitoring, third-party mailers, and *every parked and legacy domain* |
| 1 | `p=none; rua=...` | 4–8 weeks | Collect aggregate reports. Do not skip this; you are looking for legitimate senders you forgot |
| 2 | Fix SPF and DKIM | 4–12 weeks | Bring every legitimate sender into alignment. SPF has a 10-DNS-lookup limit — flattening or consolidating senders is usually needed |
| 3 | `p=quarantine; pct=` | 4–8 weeks | Ramp the percentage upward, monitoring reports and helpdesk tickets |
| 4 | `p=reject` | Permanent | Enforce. Apply to *all* owned domains including non-sending ones (`v=DMARC1; p=reject;` plus a null SPF and DKIM policy) |

**Reporting.** `rua` aggregate reports are the operational feed; `ruf` forensic reports are sparsely supported and carry privacy considerations under GDPR/POPIA. Note that the DMARC specification has continued to evolve within the IETF; check the current RFC status rather than assuming the 2015-era document is definitive.

**Honest limits.** DMARC at `p=reject` prevents someone spoofing `yourcompany.com`. It does nothing about `yourcompany-invoices.com`, `yourcornpany.com`, a Gmail address with your CEO's display name, or a genuine email from your supplier's genuinely compromised mailbox — which is the most common BEC pattern. **DMARC is table stakes, not a solution.** Pair it with lookalike-domain monitoring and display-name-similarity detection at the gateway.

**BIMI** requires DMARC enforcement and displays a verified logo; treat it as a brand and deliverability benefit rather than a security control, since users cannot be relied upon to notice its absence.

---

## 2. Secure email gateways and their limits

Gateways contribute reputation filtering, attachment sandboxing (detonation), URL rewriting with click-time reputation checks, impersonation detection based on display-name and domain similarity, and post-delivery clawback of messages later found malicious. All are worth having. Configure at minimum:

- External-sender banners, plus a distinct warning for **first-time senders** and for **display names similar to internal staff**.
- Attachment policy: block executables and script types outright; sandbox Office and PDF; treat password-protected archives with suspicion since they defeat scanning.
- URL rewriting **with click-time re-evaluation**, because a link benign at delivery is frequently weaponised afterwards.
- Automatic clawback wired to your threat intelligence and to your own report-button triage.

**The limits, stated plainly.** A targeted lure sent from a newly registered domain to five people carries no reputation signal. A QR code is an image. A reply inside an existing thread from a compromised supplier passes every authentication check because it is authentic. A vishing call never touches the gateway. ENISA's 2024 report notes attackers routinely staging links through legitimate cloud services precisely to inherit their reputation. Plan for a meaningful residual rate and design the next layer accordingly.

---

## 3. Phishing-resistant MFA — the single highest-value control

**Why FIDO2/WebAuthn is different.** A passkey is a public-key credential where the private key never leaves the authenticator and the server never receives a shared secret. Critically, the credential is **bound to the relying-party origin**. When a user lands on a lookalike domain, the browser will not release an assertion for the real domain, because the origin does not match. There is nothing for the user to type and nothing for a proxy to relay. This is why FIDO2 defeats both classic credential phishing and adversary-in-the-middle relay — the two attacks that OTP-based MFA does not stop.

**CISA's position** (fact sheet, October 2022): FIDO/WebAuthn and PKI-based MFA are the only phishing-resistant implementations. FIDO/WebAuthn is described as "the only widely available phishing-resistant authentication". SMS and voice codes are vulnerable to phishing, SS7 exploitation and SIM swap; app-based OTP is phishable; push without number matching is vulnerable to push bombing and user error.

**Practical deployment order** (adapting CISA's phased advice):
1. Administrators and privileged accounts first — including break-glass accounts, which should use hardware keys held in physical custody.
2. Identity provider, email, VPN/remote access, and the finance and payroll systems.
3. Executives, executive assistants, finance, HR and helpdesk staff.
4. General workforce.
5. Then, and only then, disable weaker factors — leaving OTP enabled as a fallback preserves the phishable path and negates most of the benefit. **The fallback is the attack surface.**

**Registration is the new weak point.** If a helpdesk can enrol a new factor on the strength of a phone call, the cryptography is irrelevant. Enrolment and reset must themselves be strongly verified (file `06` §5). Attackers now target the *registration* flow rather than the authentication flow.

**Adoption context.** A 2024 FIDO Alliance-commissioned survey reported 53% of respondents had enabled passkeys on at least one account and 22% on every account they could. Treat consumer-survey figures as directional only.

**Where FIDO2 is not yet possible**, use number matching. Microsoft made number matching mandatory for all Authenticator push notifications with no user opt-out: the user must enter a number shown on the sign-in screen, so blind approval is impossible. Enable additional context (application name and sign-in location) in the prompt.

---

## 4. Conditional access and device trust

Authentication answers "who"; conditional access answers "under what circumstances". A useful baseline:

- **Require a compliant, managed device** for access to email, finance systems and administrative consoles. This is what turns a stolen session into a dead end.
- **Block legacy authentication protocols** entirely — they bypass MFA by design.
- **Risk-based policies**: step up or block on impossible travel, anonymising infrastructure, unfamiliar sign-in properties.
- **Short session lifetimes and continuous evaluation** for high-value applications, so a revoked account loses access in minutes rather than at token expiry.
- **Restrict by role and location** for the highest-risk functions — for example, payment approval only from managed devices on corporate networks.
- **Token protection / binding** where the platform supports it, to reduce the value of a stolen refresh token.

---

## 5. DNS and web filtering

Protective DNS blocks resolution of known-malicious and newly registered domains and gives a cheap, high-coverage layer that applies to links clicked from any application, not just email. Configure:

- Block newly registered domains (commonly < 30 days) for general users, with an exception process.
- Block known phishing and malware categories, plus anonymisers and consumer remote-access services.
- Log and alert on blocked resolutions attributable to a user — a blocked click is a **detection event**, and should feed the same triage queue as report-button submissions.
- Extend coverage to roaming devices via the endpoint agent, not just the office network.
- Consider **browser isolation** for high-risk roles or for links from untrusted senders.

---

## 6. Endpoint controls

The purpose here is to make "the user ran the thing" survivable.

- **Application allowlisting** where the environment permits it. This is the highest-value endpoint control and the least deployed.
- **Block Office macros from the internet** by policy; block or restrict scripting hosts and LOLBins where feasible.
- **EDR** with behavioural detection and the ability to isolate a host in one action.
- **Least-privilege endpoints**: no local administrator rights for ordinary users; separate administrative accounts that cannot read email or browse.
- **Removable media policy** — block or read-only USB mass storage; the baiting evidence (98% of dropped drives picked up, 45% opened, University of Illinois 2016) says this is not theoretical.
- **Patching**, since watering-hole and drive-by paths depend on it, and the DBIR 2026 landing summary reports 31% of breaches now beginning with a software vulnerability.

---

## 7. Payment process controls — the controls that stop BEC

BEC is a **process** vulnerability, and the money is recovered by process controls, not by security tooling. IC3 recorded US$2.77 billion in BEC losses in 2024; the controls below are what prevent that number appearing on your P&L.

**The mandatory five:**

1. **Callback verification on a known-good number.** For every change to bank details and every payment above a defined threshold, call the counterparty on a number obtained from the signed contract or the vendor master file — **never** a number contained in, or supplied in response to, the request. Log the call, the number used, and the person spoken to.
2. **Dual authorisation.** No single individual may initiate and approve a payment. Enforce it in the banking platform, not in policy alone.
3. **Vendor bank-detail change procedure.** Changes require: a request through the documented channel, callback verification, a notification to the *previous* known contact at the vendor, a mandatory hold period (typically 24–72 hours), and a second approver. Never accept a change on the strength of an email or a letterhead PDF.
4. **Cooling-off on high-value payments.** A defined window during which the payment cannot execute. This is the direct technical counter to manufactured urgency.
5. **A published no-exceptions clause**, sponsored by the CEO, stating that no executive may request bypass and that staff refusing such a request will be supported.

**Supporting controls:** payee whitelisting; confirmation-of-payee where the jurisdiction supports it; anomaly detection on new beneficiaries and unusual amounts; a hard ban on gift cards as a business instrument; and a documented, rehearsed **recall procedure** — recovery success falls sharply after the first hours.

---

## 8. Privileged access management

- **Eliminate standing privilege.** Just-in-time elevation with an approval step and automatic expiry.
- **Vault credentials**; no shared admin passwords in scripts or documents. The Uber 2022 breach escalated because a PowerShell script on a network share contained hardcoded privileged credentials.
- **Session recording and monitoring** on privileged sessions.
- **Separate administrative identities** with no mail or browsing, on privileged access workstations for the highest tiers.
- **Four-eyes on privilege grants** — adding a role, adding an MFA factor to a privileged account, or granting an application consent should require a second person.
- **Constrain the helpdesk.** The NY DFS report on the 2020 Twitter compromise found more than 1,000 employees with access to sensitive internal account-management tooling. Scope helpdesk tooling to the minimum necessary, tier it by target account sensitivity, and alert on privileged-target resets.

---

## 9. Zero trust principles applied to social engineering

The relevant zero-trust ideas are narrow and practical:

- **Never trust a network location.** Being "inside" grants nothing.
- **Verify explicitly, per request**, using identity, device posture and context.
- **Least privilege with just-in-time and just-enough access.**
- **Assume breach** — segment so a compromised identity reaches a bounded blast radius, and instrument so lateral movement is visible.
- **Continuous evaluation** rather than authentication as a one-time gate.

The connection to this domain is direct: social engineering produces *an authenticated attacker*. Every zero-trust control that constrains what an authenticated identity can do is a social-engineering control.

---

## 10. Detection engineering for these patterns

Build and tune these specifically; most SIEM deployments lack several.

**Identity and email**
- Mailbox rule creation or modification, especially rules that delete, mark-read or forward messages matching payment keywords — a near-definitive indicator of mailbox compromise.
- External auto-forwarding enabled on any mailbox (and block it by policy).
- OAuth application consent grants by end users; illicit consent is a common MFA bypass.
- MFA method registration, modification or removal — high fidelity when the target is privileged.
- Sign-in from anonymising infrastructure or residential proxies; impossible travel weighted by role.
- Repeated MFA denials followed by an approval — the push-bombing signature.
- Mass password-spray patterns against your tenant.

**Helpdesk and privilege**
- Password/MFA reset volume by agent, by target privilege tier, and out of hours.
- Privilege grants outside change windows.
- New device enrolment immediately followed by privileged access.

**Data and payment**
- Bulk downloads or exports from SaaS platforms, particularly by support or outsourced accounts.
- Creation of new payees; changes to vendor master bank data (this should be an alert, not just a log).
- Access to finance systems from unusual devices or locations.

**Human sensors**
- The report-button queue is a detection source. Correlate submissions to identify campaigns, auto-clawback matching messages from all mailboxes, and feed indicators to DNS and gateway blocklists. Lain et al. demonstrated over 15 months and 14,000+ employees that this is operationally practical at manageable cost.

---

## 11. Incident response playbooks

Write these as one-page, decision-oriented documents. Rehearse them (file `05` §6).

**Playbook A — Credential phishing (user reports after entering credentials).**
1. Reset password **and revoke all sessions and refresh tokens**; a password reset alone leaves the stolen session alive.
2. Re-register MFA factors from a verified device.
3. Check for new mailbox rules, forwarding, OAuth grants, new device enrolments, and recent MFA method changes.
4. Clawback the message from all mailboxes; block the sender, domain and URL.
5. Review the user's sent items for messages sent by the attacker to colleagues and counterparties.
6. Thank the reporter, in writing. This is a control, not a courtesy.

**Playbook B — Suspected BEC / fraudulent payment.**
1. Contact the bank immediately and request recall; the first hours dominate recovery odds.
2. Report to the national body (IC3 in the US; Action Fraud in the UK; the bank plus SAPS in South Africa; see file `09` §7).
3. Determine which mailbox was compromised — yours or the counterparty's — and contain it.
4. Notify the counterparty through a verified channel.
5. Preserve headers and logs before anything is deleted.
6. Assess regulatory notification duties (file `06` §10).
7. Review every other pending payment to that vendor.

**Playbook C — Helpdesk compromise / suspicious reset.**
1. Suspend the affected account and any accounts reset by the same agent in the window.
2. Revoke sessions; re-verify the legitimate user in person or by verified video.
3. Audit all resets by that agent for the period; check for privilege grants.
4. Consider a temporary elevation of identity-proofing requirements across the desk.

**Playbook D — Deepfake or voice-clone authorisation attempt.**
1. Do not complete the transaction; there is no perceptual test that settles it.
2. Terminate the call and reach the claimed party through the directory.
3. Preserve the meeting invite, platform logs and any recording.
4. Report as a security incident even if no money moved — attempted incidents are the early warning.

**Cross-cutting:** every playbook must name who can be woken at 02:00, who can authorise a payment freeze, and who speaks to regulators and customers.

## Sources

- [DMARC Overview](https://dmarc.org/overview/) — DMARC.org (alignment, policy progression, reporting)
- [Implementing Phishing-Resistant MFA](https://www.cisa.gov/sites/default/files/publications/fact-sheet-implementing-phishing-resistant-mfa-508c.pdf) — CISA, October 2022
- [Passkeys](https://fidoalliance.org/passkeys/) — FIDO Alliance (origin binding, adoption survey)
- [How number matching works in MFA push notifications](https://learn.microsoft.com/en-us/entra/identity/authentication/how-to-mfa-number-match) — Microsoft
- [Phishing attacks: defending your organisation](https://www.ncsc.gov.uk/guidance/phishing) — UK NCSC
- [Telling users to "avoid clicking bad links" still isn't working](https://www.ncsc.gov.uk/blog-post/telling-users-to-avoid-clicking-bad-links-still-isnt-working) — UK NCSC
- [MITRE ATT&CK T1566 Phishing](https://attack.mitre.org/techniques/T1566/) — MITRE
- [Twitter investigation report](https://www.dfs.ny.gov/Twitter_Report) — NY State DFS
- [ENISA Threat Landscape 2024](https://www.enisa.europa.eu/sites/default/files/2024-11/ENISA%20Threat%20Landscape%202024_0.pdf) — ENISA
- [2024 Internet Crime Report](https://www.ic3.gov/AnnualReport/Reports/2024_IC3Report.pdf) — FBI IC3

## Open questions

- **Current DMARC RFC status.** DMARC.org indicates the specification has continued to evolve in the IETF, with an updated specification noted as published in 2026. Confirm the operative RFC number before citing it. Marked `needs-verification`.
- **The Uber hardcoded-PowerShell-credential detail** is widely reported but the primary confirmation was not fetched here; see file `07`, where it is marked.
- **SPF's 10-lookup limit** and the specific mechanics of "SPF flattening" are from general operational knowledge; verify against RFC 7208 before publishing as guidance.
- **Token binding / token protection** support varies substantially by identity platform and licence tier; verify availability in your own tenant.
