---
id: sedef.personal
title: Personal protection — the individual's and family's guide
domain: 33_social_engineering_defence
tags: [personal-security, passkeys, password-manager, account-recovery, sim-swap, safe-word, voice-clone, elder-fraud, romance-scam, reporting, south-africa, namibia, incident-recovery]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Passkeys", url: "https://fidoalliance.org/passkeys/", publisher: "FIDO Alliance", accessed: 2026-08-25}
  - {title: "Implementing Phishing-Resistant MFA", url: "https://www.cisa.gov/sites/default/files/publications/fact-sheet-implementing-phishing-resistant-mfa-508c.pdf", publisher: "CISA", accessed: 2026-08-25}
  - {title: "SIM swap scam", url: "https://en.wikipedia.org/wiki/SIM_swap_scam", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "2024 Internet Crime Report", url: "https://www.ic3.gov/AnnualReport/Reports/2024_IC3Report.pdf", publisher: "FBI IC3", accessed: 2026-08-25}
  - {title: "Report a scam email", url: "https://www.ncsc.gov.uk/collection/phishing-scams/report-scam-email", publisher: "UK NCSC", accessed: 2026-08-25}
  - {title: "Nam-CSIRT", url: "https://nam-csirt.na/", publisher: "Communications Regulatory Authority of Namibia", accessed: 2026-08-25}
  - {title: "Southern African Fraud Prevention Service", url: "https://www.safps.org.za/", publisher: "SAFPS", accessed: 2026-08-25}
  - {title: "SABRIC", url: "https://www.sabric.co.za/", publisher: "South African Banking Risk Information Centre", accessed: 2026-08-25}
  - {title: "Pig butchering scam", url: "https://en.wikipedia.org/wiki/Pig_butchering_scam", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "FTC Data Spotlight", url: "https://www.ftc.gov/news-events/data-visualizations/data-spotlight", publisher: "US Federal Trade Commission", accessed: 2026-08-25}
related: [sedef.taxonomy, sedef.psychology, sedef.ai_landscape]
---

# Personal protection — the individual's and family's guide

**Summary.** Most personal security advice is a long list of things to remember, which is why it fails. This file is ordered by how much risk each action removes. The top five are: put your email and banking on **passkeys or a hardware key**, use a **password manager**, secure **account recovery** (the weakest link in almost every consumer compromise), **lock your mobile number** against porting, and agree a **family safe word** so a cloned voice cannot extract money from someone who loves you. Everything else is refinement. The file closes with what to do in the first hour after falling for something, and verified reporting channels by country, including South Africa and Namibia.

> ⚠️ If you are reading this because something has just happened, go straight to §8 (first hour) and §9 (reporting). Speed matters more than understanding; recovery odds fall sharply after the first hours.

## Key facts

| Risk | Dated figure | Source |
|---|---|---|
| Total US consumer/business losses reported | US$16.6 billion, 859,532 complaints (2024) | FBI IC3 |
| Losses by victims aged 60+ | US$4.885 billion, 147,127 complaints (2024) | FBI IC3 |
| Investment fraud (incl. pig-butchering) | US$6.57 billion (2024) | FBI IC3 |
| Tech support fraud | US$1.46 billion (2024) | FBI IC3 |
| SIM swap losses | US$68 million in 2021, vs US$12 million total 2018–2020 | FBI, via Wikipedia |
| UK scam URLs removed via public reporting | 454,800 as of July 2026 | UK NCSC Suspicious Email Reporting Service |
| Phishing-resistant authentication | FIDO/WebAuthn and PKI only; SMS, voice, app OTP and plain push are not | CISA, October 2022 |

---

## 1. Secure your accounts, in priority order

**Step 1 — Identify your keystone account.** For nearly everyone this is the **email account used to reset every other password**. Whoever controls it controls your digital life. Protect it as though it were your house keys and your passport combined.

**Step 2 — Turn on passkeys or a hardware security key** for that account first, then banking, then anything financial or professional. A passkey is a FIDO2/WebAuthn credential: the private key never leaves your device, the service never receives a shared secret, and the credential is **cryptographically bound to the site's origin**. If you land on a convincing fake, the browser simply will not release an assertion for the real site. There is nothing to type, so nothing to phish and nothing to relay. This is the single most effective personal security action available, and it is free.

CISA's position is that FIDO/WebAuthn and PKI are the only phishing-resistant forms of MFA, and that SMS and voice codes are vulnerable to phishing, SS7 exploitation and SIM swap, that app-based one-time codes are phishable, and that push notifications without number matching are vulnerable to blind approval.

**Step 3 — Enrol two authenticators**, not one. A phone plus a hardware key, or two hardware keys with one stored somewhere safe. The most common reason people avoid passkeys is fear of lockout; two enrolled authenticators removes it.

**Step 4 — Use a password manager** for everything that still needs a password. Long unique random passwords everywhere, one strong passphrase to open the vault, and MFA on the vault itself. The manager also gives you a quiet anti-phishing benefit: **it will not autofill on the wrong domain.** If your manager does not offer to fill, treat that as a warning, not an inconvenience.

**Step 5 — Fix account recovery. This is where most people are actually compromised.** Attackers rarely defeat your MFA; they go around it.
- Remove SMS as a recovery method wherever the service allows.
- Remove or update stale recovery email addresses and phone numbers — an old address you no longer control is an open door.
- Replace security questions with **long random strings stored in your password manager**. Your mother's maiden name and your first school are public.
- Download and **store recovery/backup codes offline** — printed, in a safe or a sealed envelope. Not in the email account they recover.
- Check your account's list of authorised devices, sessions and connected third-party apps twice a year and revoke what you do not recognise.
- **Turn on login alerts** everywhere they are offered.

**Step 6 — Be deliberate about authenticator cloud sync.** Cloud-synchronised one-time-code apps are convenient and improve recovery, but they place your second factor inside another account. If that account is compromised, both factors fall together. For your highest-value accounts, prefer a passkey or hardware key over a synced OTP app.

---

## 2. Protect your phone number

Your mobile number is a master key at many institutions, and it is held by a company whose call centre can be socially engineered.

- **Set a port-out PIN, account PIN or SIM-lock** with your mobile operator. Ask specifically for a port-out freeze if offered.
- **Remove your phone number as an authentication or recovery factor** on financial and email accounts wherever an app or key is supported.
- **For high-value accounts** (cryptocurrency in particular), use a number that appears nowhere publicly, or no phone factor at all.
- **Know the warning sign:** your phone abruptly losing service with no outage in your area, especially alongside an unexpected "your SIM has been updated" message. Treat that as an emergency — go to §8 immediately.
- Set a SIM PIN on the device and a strong device passcode; disable message previews on the lock screen so codes are not readable without unlocking.

The scale is real: the FBI recorded **US$68 million** in SIM-swap losses in 2021 against US$12 million for 2018–2020 combined.

---

## 3. Financial account controls

- **Turn on transaction alerts** for every card and account, at the lowest threshold your bank permits. Real-time notification is the fastest fraud detection available to you.
- **Use separate accounts**: a day-to-day account with a modest balance, and savings held separately with transfer limits.
- **Set low daily transfer limits** and raise them deliberately when you need to. A limit that requires a 24-hour change is a cooling-off period you have imposed on yourself.
- **Never authorise a payment during an inbound call.** Hang up and use your banking app or the number on your card.
- **Know that no bank ever asks you to move money to a "safe account".** That sentence is definitionally fraud.
- **Beneficiary hygiene:** verify a new beneficiary's details by voice with the recipient on a number you already have, and send a small test payment first for large transfers.
- **Check statements monthly**, and check your credit report at least annually — in South Africa, **[ZA]** you are entitled to a free annual credit report from the registered credit bureaux, and SAFPS specifically recommends an annual credit check as an identity-theft control.

---

## 4. Family verification protocols against voice cloning

Voice cloning from short public samples is now routine, and the Arup case (file `07` §2) showed that live video can be faked in a business setting. "It sounded exactly like her" is no longer evidence of anything.

**Agree these in person, with everyone in the family, and write nothing down online:**

1. **A safe word or shared question.** Any call claiming distress, arrest, hospitalisation, kidnap or an urgent need for money must be answered with the safe word. Choose something unguessable and not present in any social media post — not a pet's name, not a school. A shared private memory works well as a question.
2. **The callback rule.** Any request for money by phone or message is verified by hanging up and calling the person back on the number already stored in your phone. Never a new number given during the call.
3. **A named trusted person.** Every adult in the family names someone they will consult before any unusual or large financial decision. Older relatives especially benefit from this: it introduces the Asch "ally" who breaks the spell (file `01` §3).
4. **The no-secrecy rule.** Any request that includes "don't tell anyone" is fraudulent. Real emergencies do not require secrecy from family.
5. **Explicit permission to be slow.** Agree in advance that nobody will ever be upset by a five-minute verification. Removing the social cost of checking is the entire point.
6. **For businesses run from home** — very common in Namibia and South Africa — the same code-word discipline applies to any verbal payment instruction from a partner, bookkeeper or supplier.

---

## 5. Reduce your social media exposure

You are not trying to be invisible. You are trying to stop your public profile from answering verification questions and supplying pretext material.

- **Audit what is public**: date of birth, home town, employer and role, family members' names, children's schools, pets, car, travel plans, your daily routine.
- **Do not post real-time travel.** "Away until the 14th" is an operational detail for both burglars and impersonators of you.
- **Remove or restrict** anything that matches a security question anywhere.
- **Assume voice and face are public** if you have ever appeared in a video or a voice note. This is not a reason to withdraw; it is a reason to rely on §4 instead of on recognition.
- **Lock down friend and connection lists** where possible — they are the source list for impersonation of you to your contacts.
- **Watch for clones of your own profile**, which are used to approach your friends. Report them promptly.
- **[ZA]/[NA]** Be cautious with community WhatsApp groups. They are an efficient scam-distribution channel and a rich source of personal detail; treat forwarded "warnings" and investment tips as unverified.

---

## 6. Scams targeting older relatives

Older people are targeted deliberately and lose more per incident. IC3 recorded **147,127 complaints and US$4.885 billion in losses** from victims aged 60+ in 2024 — about 29% of all reported loss from roughly 17% of complaints.

**The recurring shapes:**
- **Tech support fraud** — a pop-up or cold call, remote access, then "your account has been hacked, move your money to a safe account." US$1.46 billion reported in 2024.
- **Impersonation of a grandchild or child in trouble**, now routinely voice-cloned.
- **Government, bank or utility impersonation** demanding payment or account "verification".
- **Romance fraud**, often over many months, frequently ending in an investment approach.
- **Payment by unusual instrument** — gift cards, cryptocurrency ATMs, wire to an individual. The FTC has documented Bitcoin ATMs specifically as a scam payment portal (Data Spotlight, 3 September 2024).

**What actually helps:**
- The safe word and callback rule from §4, practised, not just explained.
- A **named trusted person** to call before any money moves, agreed as a normal arrangement rather than as a restriction.
- Bank-side controls: transaction alerts to a second family member where the bank supports it; low transfer limits; a note on file.
- **Never shame them.** Shame is the mechanism by which fraud continues undetected — a person who has been made to feel foolish will hide the next approach and the losses compound. The single most protective thing a family can offer is a standing, believable promise that there will be no judgement.
- A blunt, memorable rule: **"No legitimate organisation will ever ask you to buy gift cards, use a crypto ATM, or move money to keep it safe."**

## 7. Scams targeting young people

- **Job and task scams** — "earn commission by completing tasks", requiring the victim's own deposits. The FTC recorded record losses from gamified job scams (Data Spotlight, 12 December 2024).
- **Money muling.** Being paid to receive and forward money. This is a criminal offence with lasting consequences, often presented as a legitimate part-time job. Say this explicitly to teenagers and students.
- **Sextortion**, including AI-generated imagery. The correct response is: do not pay, do not comply, preserve evidence, block, and report to the platform and police. Paying does not end it. Tell them in advance that they can come to you with this and nothing bad will happen to them.
- **Gaming and crypto scams** — fake giveaways, "free" in-game currency, account trades, phishing for gaming credentials.
- **Marketplace fraud** — overpayment scams, fake couriers, and requests to move off-platform.
- **Investment pressure via social media**, including from apparently successful peers whose accounts have been compromised.

---

## 8. The first hour after falling for something

Work top to bottom. Do not wait until you are certain.

**If you entered credentials on a fake site:**
1. From a **different, trusted device**, change the password on that account. Change it anywhere else you reused it.
2. **Sign out all sessions / revoke all devices** in the account's security settings. A password change alone can leave the attacker's session alive.
3. Re-check MFA settings, recovery email, recovery phone, forwarding rules and connected apps — attackers add persistence immediately.
4. Enable a passkey or security key now.
5. Warn anyone who might receive messages from your account.

**If money has moved:**
1. **Call your bank immediately** and ask for a recall or reversal. Use the number on your card. Minutes matter.
2. Report to the national body (§9). Give the beneficiary account details, amounts and timestamps.
3. Do not send further money. "Recovery fees", "release taxes" and "unlock payments" are always a second fraud.
4. Preserve everything — messages, emails with full headers, screenshots, phone numbers, transaction references.

**If your phone lost service unexpectedly:**
1. Contact your mobile operator from another phone and ask whether a SIM swap or port-out occurred.
2. From a trusted device, secure your email and banking first.
3. Report to the police and your bank.

**If you gave someone remote access:**
1. Disconnect the device from the internet.
2. From a different device, change your email and banking passwords and revoke sessions.
3. Assume anything typed while they were connected is compromised.
4. Have the machine cleaned professionally, or reinstall. Uninstalling the remote-access tool is not sufficient.

**Always:** tell someone. The isolation is part of the attack, and a second person will see what you cannot.

---

## 9. Reporting channels by country

**[ZA] South Africa**
- **Your bank first**, on the fraud line printed on your card, immediately.
- **South African Police Service** — report at any police station; obtain a case (CAS) number, which banks and insurers will require.
- **SAFPS (Southern African Fraud Prevention Service)** — a not-for-profit fraud prevention body operating since 2001. Offers **Protective Registration** to flag your identity against future fraud (onboarding portal at onboarding-safps.kyc.business), and the **Yima** scam toolbox with a scam reporting form at yima.org.za/reportscam. Phone 011 867 2234.
- **SABRIC (South African Banking Risk Information Centre)** — the banking industry's crime-intelligence body; publishes risk alerts and annual crime statistics. Midrand, 011 847 3000.
- **Information Regulator** — for a breach of your personal information by an organisation, under POPIA (Act 4 of 2013). Section 22 obliges the responsible party to notify you and the Regulator.
- Credit bureaux — place a fraud alert and obtain your credit report.

**[NA] Namibia**
- **Your bank first**, on its fraud line.
- **Nam-CSIRT** (Namibia Cyber Security Incident Response Team), operated by the Communications Regulatory Authority of Namibia: online reporting at nam-csirt.na/report-security-incidents/, **info@nam-csirt.na**, **+264 61 222 666**. Office hours Monday–Friday 08:00–17:00 CAT. Located at CRAN, Freedom Plaza, Courtside Building, cnr Fidel Castro & Rev. Michael Scott Street, Windhoek; Private Bag 13309, Windhoek 10005.
- **Namibian Police (NamPol)** — report at a police station for a case number.
- Your mobile operator, for SIM-swap and smishing.

**[UK] United Kingdom**
- **Action Fraud** — online reporting at reportfraud.police.uk, or **0300 123 2040** (England, Wales, Northern Ireland). In Scotland, call **Police Scotland on 101**.
- **NCSC Suspicious Email Reporting Service** — forward suspicious emails to the NCSC's reporting address (published on the NCSC "report a scam email" page). The service had removed **454,800 scam URLs** as of July 2026. Forward anything that feels suspicious even if you are unsure; do not click first.
- Suspicious text messages can be forwarded to the mobile industry short code (**7726**) — confirm the current arrangement on the NCSC page.

**[US] United States**
- **IC3** (ic3.gov) — the FBI's main intake for cyber-enabled fraud and cybercrime. Note that IC3 will not contact you back; reports may be referred to federal, state, local or international agencies. **File within hours for wire fraud**, because rapid reporting is what enables recovery action on transfers.
- **FTC** — reportfraud.ftc.gov for consumer fraud and identity theft; identitytheft.gov for a recovery plan.
- Your bank and card issuer, immediately.

**[EU] European Union** — report to your national police and national CSIRT; where personal data is involved, your national data protection authority. Under NIS2 and GDPR the *organisation* has reporting duties too (file `06` §10).

**Everywhere** — report the phishing message to the impersonated brand (most banks and platforms have a phishing report address), and to the platform on which it arrived.

---

## 10. A one-page checklist

1. Passkey or hardware key on email and banking. Two authenticators enrolled.
2. Password manager for everything else, with MFA on the vault.
3. Recovery hardened: no SMS recovery, no real security-question answers, backup codes stored offline, stale recovery addresses removed.
4. Port-out PIN with your mobile operator; phone number removed as a factor where possible.
5. Transaction alerts on; low transfer limits; separate savings.
6. Family safe word agreed in person; callback rule; named trusted person; no-secrecy rule.
7. Social exposure audited; no real-time travel posts; security-question material removed.
8. Older relatives briefed, with a no-judgement promise and a named person to call.
9. Younger family briefed on job scams, money muling and sextortion, with the same promise.
10. Reporting numbers for your country saved in your phone **before** you need them.

## Sources

- [Passkeys](https://fidoalliance.org/passkeys/) — FIDO Alliance
- [Implementing Phishing-Resistant MFA](https://www.cisa.gov/sites/default/files/publications/fact-sheet-implementing-phishing-resistant-mfa-508c.pdf) — CISA, October 2022
- [SIM swap scam](https://en.wikipedia.org/wiki/SIM_swap_scam) — Wikipedia
- [2024 Internet Crime Report](https://www.ic3.gov/AnnualReport/Reports/2024_IC3Report.pdf) — FBI IC3
- [IC3 complaint intake](https://www.ic3.gov/) — FBI IC3
- [Report a scam email](https://www.ncsc.gov.uk/collection/phishing-scams/report-scam-email) — UK NCSC (454.8k URLs removed as of July 2026; Action Fraud 0300 123 2040; Police Scotland 101)
- [Action Fraud](https://www.actionfraud.police.uk/) — UK
- [Nam-CSIRT](https://nam-csirt.na/) — CRAN, Namibia (contact details and reporting form)
- [Communications Regulatory Authority of Namibia](https://cran.na/) — CRAN
- [SAFPS](https://www.safps.org.za/) — Southern African Fraud Prevention Service (Protective Registration, Yima)
- [SABRIC](https://www.sabric.co.za/) — South African Banking Risk Information Centre
- [FTC Data Spotlight](https://www.ftc.gov/news-events/data-visualizations/data-spotlight) — US FTC (Bitcoin ATM and gamified job scam spotlights)
- [Pig butchering scam](https://en.wikipedia.org/wiki/Pig_butchering_scam) — Wikipedia

## Open questions

- **SAPS online crime reporting** could not be retrieved (TLS/robots failure on saps.gov.za). The station-based reporting and CAS-number procedure is stated from general knowledge; confirm the current SAPS cybercrime reporting route, and whether the Cybercrimes Act 19 of 2020 has introduced a dedicated channel. Marked `needs-verification`.
- **NCSC Suspicious Email Reporting Service address** — the page redacted the email address in the fetched rendering. The service exists and the statistics are verified; obtain the exact address from the NCSC page before publishing it.
- **UK 7726 SMS short code** — widely used and industry-standard, but not confirmed on the fetched NCSC page. Marked `needs-verification`.
- **South African free annual credit report entitlement** is stated from general knowledge of the National Credit Act; verify with the National Credit Regulator.
- **Namibian Police cybercrime reporting** — no dedicated online channel was identified; Nam-CSIRT is the verified technical route.

