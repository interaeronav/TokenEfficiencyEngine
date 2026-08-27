---
id: sedef.cases
title: Notable cases — what happened, which control failed, what changed
domain: 33_social_engineering_defence
tags: [case-studies, twitter-2020, arup-deepfake, mgm, caesars, ubiquiti, facc, rsa-securid, dnc-2016, uber-2022, experian-south-africa, lessons-learned, incident-analysis]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "2020 Twitter account hijacking", url: "https://en.wikipedia.org/wiki/2020_Twitter_account_hijacking", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Twitter investigation report", url: "https://www.dfs.ny.gov/Twitter_Report", publisher: "NY State Department of Financial Services", accessed: 2026-08-25}
  - {title: "Deepfake", url: "https://en.wikipedia.org/wiki/Deepfake", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Arup Group", url: "https://en.wikipedia.org/wiki/Arup_Group", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Scattered Spider", url: "https://en.wikipedia.org/wiki/Scattered_Spider", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Caesars Entertainment", url: "https://en.wikipedia.org/wiki/Caesars_Entertainment", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "MGM Resorts International", url: "https://en.wikipedia.org/wiki/MGM_Resorts_International", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Business email compromise", url: "https://en.wikipedia.org/wiki/Business_email_compromise", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Ubiquiti", url: "https://en.wikipedia.org/wiki/Ubiquiti", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "RSA SecurID", url: "https://en.wikipedia.org/wiki/RSA_SecurID", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Podesta emails", url: "https://en.wikipedia.org/wiki/Podesta_emails", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "2016 Democratic National Committee email leak", url: "https://en.wikipedia.org/wiki/2016_Democratic_National_Committee_email_leak", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Lapsus$", url: "https://en.wikipedia.org/wiki/Lapsus$", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Uber", url: "https://en.wikipedia.org/wiki/Uber", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Experian", url: "https://en.wikipedia.org/wiki/Experian", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Coinbase", url: "https://en.wikipedia.org/wiki/Coinbase", publisher: "Wikipedia", accessed: 2026-08-25}
related: [sedef.taxonomy, sedef.technical_controls, sedef.resilience]
---

# Notable cases — what happened, which control failed, what changed

**Summary.** Each case below is presented in the same shape: verified facts, the human or process control that failed, and what the organisation changed. The purpose is diagnostic, not voyeuristic. Read across the set and a pattern emerges with uncomfortable clarity: **almost none of these were failures of user vigilance, and almost all were failures of process design** — one person able to act alone, a helpdesk that would reset anything, an MFA factor that could be phished, a payment that needed no callback, a privilege that had no expiry.

> ⚠️ Details are given at the level found in public reporting and regulatory documents. No case description here contains technique detail sufficient to reproduce the attack.

## Key facts

| Case | Date | Loss / impact | Failed control |
|---|---|---|---|
| Twitter account hijacking | 15 July 2020 | 130 accounts; ~US$118,000 in bitcoin | Phishable MFA; privilege sprawl (1,000+ staff with admin tooling); no CISO |
| Arup deepfake video-call fraud | 2024 (reported May) | ~US$25 million | Payment authorisation by apparent identity rather than process |
| MGM Resorts | 11 Sept 2023 | ~US$100 m stated loss; US$45 m settlement (18 June 2025) | Service desk identity verification |
| Caesars Entertainment | Sept 2023 | US$15 m ransom paid; ~65 m loyalty members' data | Outsourced IT vendor access |
| Ubiquiti | 2015 | US$46.7 million | No callback verification; single-person payment authority |
| FACC AG | February 2016 | €42 m (~US$47 m) | CEO-fraud pretext; no dual authorisation |
| RSA Security | March 2011 | US$66.3 m cost to EMC; 30,000+ customers offered token replacement | Spear-phishing attachment; no attachment isolation |
| DNC / Podesta | March–May 2016 | 19,252 DNC emails; 20,000+ pages of Podesta email | Credential phishing; a one-word typo in the IT response |
| Uber | 15 September 2022 | VPN and intranet access | MFA fatigue; standing credentials in a script |
| Experian South Africa **[ZA]** | 2020 | Data of 24 m individuals and ~800,000 businesses | Client identity verification at onboarding |
| Coinbase | May 2025 | Up to US$400 m estimated remediation | Outsourced support privilege; insider bribery |

---

## 1. Twitter, 15 July 2020 — vishing against the helpdesk model

**What happened.** Between 20:00 and 22:00 UTC on 15 July 2020, attackers compromised **130 Twitter accounts**, using **45** to post a cryptocurrency scam. According to the New York Department of Financial Services investigation, the attackers phoned Twitter employees posing as the internal IT helpdesk, offering to fix VPN problems — a highly plausible pretext after the company's March 2020 shift to remote work. Employees were directed to a phishing site that mirrored Twitter's real VPN login page; as credentials were entered, the attackers used them live against the real system, and when the MFA prompt appeared, employees approved it. Attackers had earlier identified likely administrator-privileged staff from public professional profiles.

One bitcoin wallet received over 320 deposits totalling roughly **US$110,000–118,000**; Coinbase blocked over 1,000 transactions worth more than US$280,000, and DFS reported exchanges collectively blocked over US$1.5 million.

**Outcomes.** Graham Ivan Clark, 17, was charged as an adult on 30 felony counts and sentenced in March 2021 to three years' prison plus three years' probation. Joseph James O'Connor was extradited in April 2023 and sentenced on 23 June 2023 to five years' federal prison with US$794,000 forfeiture.

**Which control failed.** Three, in combination:
- **Phishable MFA.** App-based approval could be relayed in real time.
- **Privilege sprawl.** DFS found **over 1,000 employees** had access to sensitive internal account-management tooling.
- **Governance.** The CISO position had been vacant since December 2019, and no compensating controls were introduced when the company went remote.

**What changed.** Twitter introduced heightened employee background checks, deployed **phishing-resistant security keys**, required social-engineering awareness training for customer support staff, and appointed a CISO in September 2020. DFS recommended hardware-based MFA, tighter access controls, enhanced monitoring, and — at policy level — a framework treating large social platforms as "systemically important" with a dedicated regulator.

**Lesson.** The pretext was ordinary and the technology unremarkable. What made it catastrophic was that a thousand people could reach the crown jewels with a phishable factor.

---

## 2. Arup, 2024 — the deepfake video call

**What happened.** The engineering firm Arup lost approximately **US$25 million** in a 2024 fraud in Hong Kong, reported publicly in May 2024. Fraudsters used AI-generated video and audio to impersonate senior company officials, deceiving an employee into making transfers across multiple transactions. The employee reportedly joined what appeared to be a routine video conference populated by recognisable colleagues.

**Which control failed.** Not detection — there was nothing to detect perceptually. The failure was **authorising a payment on the strength of apparent identity** rather than a workflow. Every downstream control that would have caught it (callback on a known-good number, dual authorisation, cooling-off) was either absent or bypassed by the seniority of the apparent requester.

**What changed / what it means for everyone else.** This case ended the era in which "get them on video" was a valid verification step. The generalisable conclusion is stated in file `04` §7 and file `02` §11: **identity is not authorisation.** A payment must be authorised by a process with independent verification, and the process must not have a fast path for senior people.

**Related precedent.** In 2019, the CEO of a UK-based energy firm transferred **€220,000** to a Hungarian account after a caller reported to have used audio deepfake technology impersonated the parent company's chief executive. The 2019 case was voice only; the 2024 case was full video with multiple participants. The trajectory is clear.

---

## 3. MGM Resorts and Caesars Entertainment, September 2023 — the service desk

**What happened.** The group tracked as Scattered Spider (UNC3944) compromised both operators within weeks. For MGM, attackers **called the service desk impersonating an employee identified from LinkedIn**. The initial breach occurred on 11 September 2023 and was disclosed 12–13 September. Guest-facing systems were disrupted for several days — food and beverage credits, ATMs, remote room keys, parking charges. MGM stated losses of about **US$100 million**, expected to be covered by cyber insurance, and settled consolidated class actions for **US$45 million** on 18 June 2025.

Caesars was breached, per public reporting, **through an outside IT vendor**. Data for approximately **65 million** loyalty-programme members was exposed, including driver's licence numbers and possibly social security numbers. Caesars paid **US$15 million** against a US$30 million demand.

The group's broader toolkit included MFA fatigue, SIM swapping of privileged staff, and phishing by SMS and Telegram. Arrests followed: Noah Michael Urban (January 2024), Tyler Buchanan in Spain (June 2024), a 17-year-old in Walsall, UK (July 2024), Remington Ogletree (November 2024), and Peter Stokes at Helsinki Airport (April 2026).

**Which control failed.** **Service desk identity verification** at MGM; **third-party access management** at Caesars. Both are governance failures, not user failures.

**What changed.** Across the sector, service desk identity proofing was rebuilt: manager attestation, verified video with liveness against HR-held photographs, callbacks to HR-recorded numbers, and escalation tiers for privileged targets. See file `06` §5 for the standard.

**Lesson.** Two contrasting choices — MGM refused to pay and absorbed roughly US$100 million in operational loss; Caesars paid US$15 million and kept operating. Neither is a recommendation. The observation for a board is that **the decision point arrives after the control has already failed**, and the cheap intervention was upstream, in the reset procedure.

---

## 4. Ubiquiti, 2015 — BEC at scale

**What happened.** Ubiquiti lost **US$46.7 million** when its finance department was deceived into sending funds to someone impersonating an employee. It remains one of the largest publicly disclosed single-company BEC losses.

**Which control failed.** No independent verification of payment instructions; payment authority concentrated enough that the deception of a small number of people was sufficient.

**What changed.** The case became the standard reference in finance-function training and drove wide adoption of callback verification and dual authorisation for international transfers. It is the case to show a CFO who thinks BEC is a small-company problem.

---

## 5. FACC AG, February 2016 — CEO fraud and executive accountability

**What happened.** The Austrian aerospace supplier FACC was defrauded of **€42 million (about US$47 million)** in February 2016 through a CEO-fraud pretext. Both the **CFO and the CEO were subsequently terminated**.

**Which control failed.** Authority impersonation combined with the absence of an independent verification step for large outbound transfers — precisely the gap that a callback rule and dual authorisation close.

**What changed.** FACC's dismissal of both executives, and the subsequent civil action, made this the reference case for **board-level accountability** for social-engineering losses. It reframed BEC from an operational nuisance to a governance failure with personal consequences, which is the framing that gets payment controls funded.

**Lesson for training.** The lure targeted the *finance process*, not a naive individual. The organisation had no structural reason to stop it.

---

## 6. RSA Security, March 2011 — spear phishing a security company

**What happened.** On 17 March 2011 RSA announced it had suffered an attack. It began with spear-phishing emails to **two small groups of employees**, carrying a Microsoft Excel file with embedded malware exploiting an Adobe Flash vulnerability, which installed the Poison Ivy remote access trojan. Evidence strongly suggests attackers obtained data mapping SecurID token serial numbers to their seed values — RSA advised customers to protect their token serial numbers, which supports that reading.

In May 2011 the stolen material was used in an attack on **Lockheed Martin**, which reported that aggressive action by its security team prevented compromise of customer, programme or employee data. The breach cost EMC **US$66.3 million** in second-quarter earnings for investigation, hardening and customer transaction monitoring. On 6 June 2011 RSA offered token replacement or free security monitoring to **over 30,000 customers**.

**Which control failed.** An employee at a security company opened a document. That is not a training failure; it is an architecture failure. The specific gaps were attachment isolation, exploit mitigation, and — most importantly — the storage of a **single centralised secret whose compromise undermined every customer**.

**What changed.** The industry-wide consequence was a rethink of shared-secret authentication and a push toward architectures where a vendor compromise does not compromise every customer — the intellectual lineage that leads to FIDO2, where no shared secret exists to steal. This is the deepest structural lesson in the file.

---

## 7. DNC and Podesta, 2016 — credential phishing and a one-word typo

**What happened.** On **19 March 2016** John Podesta received a spear-phishing email disguised as a Google security alert containing a Bitly-shortened link to a fake login page, where his Gmail credentials were captured. When IT staff reviewed the flagged message, an employee wrote that the message was **"legitimate"** when they meant "illegitimate" — and the attack proceeded. WikiLeaks published over **20,000 pages** of Podesta emails from October–November 2016. Separately, **19,252 DNC emails and 8,034 attachments** covering January 2015 to May 2016 were published on 22 July 2016. On 13 July 2018 Special Counsel Robert Mueller indicted **12 Russian military intelligence officers** associated with the group known as Fancy Bear.

**Which control failed.** Credential-only authentication on a high-value account; and a verification process that depended on free-text human communication under time pressure, with no structured mechanism to catch a typo with historic consequences.

**What changed.** Political organisations and campaigns across democracies moved to **hardware security keys** and mandatory MFA. It also drove the creation of dedicated protective programmes for high-risk civil-society users.

**Lesson.** The most consequential single character in the history of information security was an absent "il-". Verification processes must be **structured** (a status field, a decision code, a two-person confirmation), not prose.

---

## 8. Uber, 15 September 2022 — MFA fatigue

**What happened.** Uber discovered a breach of its internal network on **15 September 2022**. Uber's own characterisation is that an attacker used **social engineering to obtain an employee's credentials** and gained access to the company's **VPN and intranet**; the company stated no sensitive data was compromised. The incident is attributed to the Lapsus$ ecosystem, whose documented tradecraft includes **MFA fatigue attacks** — overwhelming a target with repeated authentication prompts until one is approved — alongside SIM swapping of privileged employees and **recruitment of insiders** with direct network access. The US Cyber Safety Review Board examined Lapsus$ methods in mid-2023.

**Which control failed.** Push-based MFA without number matching, so an exhausted or misled user could approve an attacker's session; and, per widely-circulated reporting, standing privileged credentials discoverable inside the environment after initial access.

**What changed.** Industry-wide, this incident is the reason **number matching became mandatory** in major authenticator products — Microsoft now enables it for all Authenticator push notifications with no user opt-out. Organisations also accelerated removal of hardcoded credentials from scripts and shares, and moved to just-in-time privilege.

**Note on detail.** The frequently repeated specifics — a contractor whose credentials were purchased, a WhatsApp message impersonating IT, and a PowerShell script on a network share containing hardcoded privileged access management credentials — are consistent with Uber's public statement and with Lapsus$ tradecraft, but **could not be verified from a primary source during construction of this file** and are marked `needs-verification`.

---

## 9. Experian South Africa, 2020 — verification failure at onboarding **[ZA]**

**What happened.** In 2020 Experian's South African operation was **deceived into handing over data by someone posing as a legitimate client**. Personal data of approximately **24 million South Africans** and nearly **800,000 businesses** was exposed, with financial details of 24,838 businesses among them. Experian initially stated the incident had been contained; that assertion did not hold, and data subsequently appeared online. The company's handling drew significant criticism.

**Which control failed.** **Customer identity verification at onboarding.** No system was breached. A pretext was accepted, credentials for a data service were issued, and bulk data was legitimately delivered to a fraudulent party.

**Why this case matters for this knowledge base.** It is the clearest documented southern African example of pure social engineering producing a mass data compromise, and it predates POPIA's full enforcement date of 1 July 2021 — which is exactly why the section 22 notification duties and the Information Regulator's powers described in file `06` §10 now matter so much locally.

**Lesson.** Any business that supplies data or services in bulk to "clients" must treat **client onboarding as a security control**, with independent verification of the legal entity, the individuals authorised to act, and the purpose — and with volume limits and anomaly detection on delivery.

---

## 10. Coinbase, May 2025 — bribed insiders at an outsourced support function

**What happened.** In May 2025 Coinbase disclosed that criminals had **bribed overseas customer-support agents** to steal customer data for use in subsequent social-engineering attacks against those customers. Personal and account details were taken; no passwords, private keys or funds were compromised, and the company said less than 1% of its data was affected. Attackers demanded **US$20 million**; Coinbase refused, offered a US$20 million reward for information leading to conviction, and on 15 May 2025 stated it expected costs of up to **US$400 million**, including customer reimbursement.

**Which control failed.** Outsourced support with broad read access to customer records, insufficient behavioural monitoring of bulk access, and no dual control on data retrieval at volume.

**What changed / what to take from it.** The stolen data was not the end state — it was **input to the next round of social engineering** against customers, who would receive calls from people who knew their real balances and transaction history. The defensive implications: outsourced support must be governed as privileged access (file `06` §3); customers must be told plainly what the company will never ask; and refusing to pay while funding attribution is a legitimate, publicly defensible strategy.

---

## 11. Incidents widely cited but not verified here

Two frequently cited cases could not be verified from retrievable primary or encyclopaedic sources during construction, and are recorded with that caveat rather than omitted:

- **Toyota Boshoku Corporation, 2019** — a European subsidiary is widely reported to have lost approximately ¥4 billion (roughly US$37 million) to a BEC-style payment fraud. **`needs-verification`** — no source confirming the amount or date could be retrieved. Do not cite the figure without checking the company's own disclosure.
- **Retool, August–September 2023** — widely reported as an SMS phishing message followed by a vishing call in which an attacker impersonating IT obtained an MFA code, with the impact amplified because Google Authenticator's then-new cloud sync feature propagated OTP seeds to a compromised Google account, affecting a small number of cryptocurrency-sector customers. **`needs-verification`** — Retool's own blog post could not be retrieved. The *architectural* lesson, if the reporting is accurate, is durable and worth stating regardless: **a convenience feature that synchronises authentication secrets to a cloud account collapses two independent factors into one**, and organisations should evaluate authenticator cloud-sync settings against that risk.
- **Reddit, February 2023** — reported as a phishing campaign against employees using a site imitating the internal intranet gateway, with the attacker obtaining credentials and a second factor. **`needs-verification`** — not confirmed from a retrievable source here.

---

## 12. The pattern across all cases

1. **Single-person authority is the common denominator.** Ubiquiti, FACC and Arup all required exactly one deceived person.
2. **The helpdesk is a privilege-granting function.** Twitter, MGM. Treat it as such.
3. **Phishable second factors are not second factors** against a live relay. Twitter, Uber, and every AitM campaign since.
4. **Third parties and outsourced functions carry your risk.** Caesars, Coinbase.
5. **Onboarding is a security control.** Experian South Africa.
6. **Centralised secrets are systemic risk.** RSA.
7. **The remediable failure is almost never "the user was careless."** In every case above, the fix that would have worked was procedural or architectural.

## Sources

- [2020 Twitter account hijacking](https://en.wikipedia.org/wiki/2020_Twitter_account_hijacking) — Wikipedia
- [Twitter investigation report](https://www.dfs.ny.gov/Twitter_Report) — NY State DFS
- [Deepfake](https://en.wikipedia.org/wiki/Deepfake) — Wikipedia (Arup, 2019 UK energy firm, detection accuracy)
- [Arup Group](https://en.wikipedia.org/wiki/Arup_Group) — Wikipedia
- [Scattered Spider](https://en.wikipedia.org/wiki/Scattered_Spider) — Wikipedia
- [MGM Resorts International](https://en.wikipedia.org/wiki/MGM_Resorts_International) — Wikipedia
- [Caesars Entertainment](https://en.wikipedia.org/wiki/Caesars_Entertainment) — Wikipedia
- [Business email compromise](https://en.wikipedia.org/wiki/Business_email_compromise) — Wikipedia (Ubiquiti, FACC, Rimasauskas)
- [Ubiquiti](https://en.wikipedia.org/wiki/Ubiquiti) — Wikipedia
- [RSA SecurID](https://en.wikipedia.org/wiki/RSA_SecurID) — Wikipedia
- [Podesta emails](https://en.wikipedia.org/wiki/Podesta_emails) — Wikipedia
- [2016 Democratic National Committee email leak](https://en.wikipedia.org/wiki/2016_Democratic_National_Committee_email_leak) — Wikipedia
- [Lapsus$](https://en.wikipedia.org/wiki/Lapsus$) — Wikipedia
- [Uber](https://en.wikipedia.org/wiki/Uber) — Wikipedia (September 2022 incident; 2016 breach and Sullivan prosecution)
- [Experian](https://en.wikipedia.org/wiki/Experian) — Wikipedia (2020 South African incident)
- [Coinbase](https://en.wikipedia.org/wiki/Coinbase) — Wikipedia (May 2025 insider bribery)

## Open questions

- **Toyota Boshoku 2019** loss amount and date — unverified; see §11.
- **Retool 2023** and **Reddit 2023** incident details — unverified; see §11. The Retool blog post URL returned 404 and Reddit's own announcement was blocked.
- **Uber 2022** specifics (contractor credential purchase, WhatsApp impersonation, hardcoded PAM credentials in a PowerShell script) — unverified from primary sources; see §8.
- **Caesars' regulatory filings** for the 2023 incident were not retrieved.
- **Arup** has made limited public statements; the US$25 million figure derives from CNN Business reporting dated 17 May 2024 as summarised on Wikipedia. The CNN article itself was not directly retrievable (robots.txt).
- A **Namibian** documented social-engineering case could not be identified from retrievable sources. Nam-CSIRT and Bank of Namibia publications may contain suitable material.
