---
id: sedef.ai_landscape
title: AI and the new threat landscape — deepfakes, agents and prompt injection
domain: 33_social_engineering_defence
tags: [generative-ai, deepfake, voice-cloning, prompt-injection, indirect-prompt-injection, ai-agents, owasp-llm, confused-deputy, agentic-browsing, synthetic-identity, defensive-ai, detection]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "LLM01:2025 Prompt Injection", url: "https://genai.owasp.org/llmrisk/llm01-prompt-injection/", publisher: "OWASP GenAI Security Project", accessed: 2026-08-25}
  - {title: "OWASP Top 10 for LLM Applications 2025", url: "https://genai.owasp.org/llm-top-10/", publisher: "OWASP GenAI Security Project", accessed: 2026-08-25}
  - {title: "Adversarial Machine Learning: A Taxonomy and Terminology of Attacks and Mitigations (NIST AI 100-2 E2025)", url: "https://csrc.nist.gov/pubs/ai/100/2/e2025/final", publisher: "NIST", accessed: 2026-08-25}
  - {title: "ENISA Threat Landscape 2024", url: "https://www.enisa.europa.eu/sites/default/files/2024-11/ENISA%20Threat%20Landscape%202024_0.pdf", publisher: "ENISA", accessed: 2026-08-25}
  - {title: "Deepfake", url: "https://en.wikipedia.org/wiki/Deepfake", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Guidelines for secure AI system development / Machine Learning Principles", url: "https://www.ncsc.gov.uk/collection/machine-learning", publisher: "UK NCSC", accessed: 2026-08-25}
  - {title: "Data Breach Investigations Report (2026 landing page)", url: "https://www.verizon.com/business/resources/reports/dbir/", publisher: "Verizon Business", accessed: 2026-08-25}
  - {title: "Pig butchering scam", url: "https://en.wikipedia.org/wiki/Pig_butchering_scam", publisher: "Wikipedia", accessed: 2026-08-25}
related: [sedef.taxonomy, sedef.technical_controls, sedef.cases, sedef.personal]
---

# AI and the new threat landscape — deepfakes, agents and prompt injection

**Summary.** Generative AI changes social engineering in three distinct ways, and it is worth keeping them apart because they demand different responses. First, it **removes the surface tells** that awareness training has relied on for twenty years — bad grammar, wrong idiom, generic salutations — and makes personalised lures cheap at scale. Second, it **breaks the trust hierarchy of channels** by making voice and, as of 2024, live video forgeable. Third, and least discussed, it creates an **entirely new victim class: the AI agent itself**, which can be socially engineered through the content it reads. That third category — indirect prompt injection, tool-use abuse and confused-deputy problems — is a genuine structural change, not hype, and it is covered here at length. The file dates everything and flags where claims outrun evidence.

> ⚠️ This file describes attack categories so that defenders can recognise and mitigate them. It contains no instructions for generating synthetic media of any person, no prompt-injection payloads, and no guidance on defeating any specific model's safeguards.

## Key facts

| Claim | Status | Source and date |
|---|---|---|
| Real-time video deepfake used in a multi-participant fraud call | **Documented** — Arup, ~US$25 m, 2024 | Reported May 2024 |
| Voice deepfake used in CEO fraud | **Documented** — €220,000, UK energy firm | 2019 |
| Automated deepfake detection is reliable | **Not supported.** Deepfake Detection Challenge winner: 65% accuracy on 4,000-video holdout; humans 69–72% on a 50-video sample (MIT) | Wikipedia summary of DFDC and MIT results |
| State actors use LLMs for phishing assistance | **Documented** — Russian, North Korean, Iranian and Chinese state-nexus groups; tools such as FraudGPT for scam emails | ENISA Threat Landscape 2024 |
| GenAI is augmenting attack techniques | 15 attack techniques identified as bolstered by generative AI | Verizon DBIR 2026 landing summary |
| Prompt injection is the top LLM application risk | **LLM01:2025**, first entry in the OWASP Top 10 for LLM Applications 2025 | OWASP GenAI Security Project |
| Formal taxonomy for adversarial ML exists | NIST AI 100-2 E2025, *Adversarial Machine Learning: A Taxonomy and Terminology of Attacks and Mitigations*, 24 March 2025 | NIST |

---

## 1. The collapse of the "bad grammar" tell

For two decades, awareness training taught recipients to look for spelling errors, awkward phrasing, wrong register and generic greetings. Those indicators were never *causally* related to maliciousness — they were artefacts of attackers writing in a second language at volume. Large language models remove them completely and at negligible cost.

**What this means for programmes, concretely:**
- **Remove language-quality indicators from all training material.** They are now a *negative* signal: a fluent, well-formatted, contextually apt message is exactly what a modern lure looks like. Teaching otherwise trains people to trust the dangerous case.
- **Replace them with structural indicators** that AI does not change: an unexpected channel switch, a manufactured deadline, a request that bypasses a documented process, a change to payment details, pressure toward secrecy, a request to authenticate from a link.
- **Update your simulation library**, because simulations built on crude lures now measure nothing useful.

**Personalisation at scale.** The economics that once separated bulk phishing (cheap, generic, low yield) from spear phishing (expensive, tailored, high yield) no longer hold. Public professional profiles, company websites, filings and press releases are readily summarised into per-recipient context. The practical consequence for defenders is that **you should assume every phish is a spear phish**, and stop treating "it knew about my project" as evidence of legitimacy.

**Evidence base, honestly.** ENISA's 2024 Threat Landscape documents LLM use for "phishing assistance" by Russian, North Korean, Iranian and Chinese state-nexus groups, and names purpose-built criminal tools for crafting scam emails. The 2026 DBIR landing summary reports 15 attack techniques bolstered by generative AI. What is *not* yet established by good public data is a clean causal attribution of a specific rise in successful-compromise rates to AI-generated content. Volume and quality have clearly increased; the isolated effect size on outcomes is not well measured. Say so, rather than repeating vendor claims of enormous percentage increases.

---

## 2. Voice cloning and real-time video deepfakes

**Where the capability actually is (as of mid-2026).** Voice cloning from short samples is commoditised and effective over telephone-quality channels, where bandwidth limitations conceal artefacts. Real-time video puppeteering good enough to survive a business video call has moved from research demonstration to documented criminal use: the **Arup fraud of 2024 (~US$25 million)** involved a video conference populated with AI-generated impersonations of senior officials. The earlier **2019 UK energy company case (€220,000)** was voice only.

**Where detection stands — and why you must not rely on it.** The Deepfake Detection Challenge's winning model achieved **65% accuracy** on a holdout set of 4,000 videos; MIT research found ordinary people **69–72% accurate** on a 50-video sample. Detection faces a structural "moving goalpost" problem: generation improves at least as fast as detection, and detectors generalise poorly to generators they were not trained on. Provenance approaches — cryptographic content credentials such as C2PA — are more promising in principle because they assert origin rather than infer forgery, but they only help where the whole capture-to-display chain is instrumented, which video conferencing generally is not.

**The defensive conclusion is blunt and liberating:** stop trying to authenticate media, and authenticate the *transaction* instead.

- **Out-of-band callback** to a number from the corporate directory or the signed contract, never a number from the call.
- **Pre-agreed code words** for verbal high-value authorisation, corporate and family (file `09` §4).
- **Process over identity**: a payment is authorised by dual control in a workflow, not by recognising a face. Once accepted, this makes deepfakes commercially irrelevant to your organisation.
- **Do not train staff to look for artefacts.** Any perceptual checklist you publish will be obsolete within a release cycle and will create false confidence in the interim.

**Family-level implication.** The "grandparent scam" and distress calls are now voice-cloned routinely. The countermeasure is a family safe word agreed offline, plus a rule to hang up and call back. See file `09`.

---

## 3. AI-assisted reconnaissance

The exposure inventory in file `03` §2 was always necessary; AI makes it urgent. Publicly available information about an organisation — staff lists, roles, tenure, suppliers, systems named in job adverts, workflows described in case studies, tone of internal communications inferable from public writing — can now be aggregated and summarised automatically at a fraction of the previous effort.

**Defensive consequences:**
- **Assume complete public-information aggregation.** Any control whose security rests on an attacker not knowing something publishable is already broken.
- **Kill knowledge-based verification everywhere** — helpdesk, bank, insurer, internal process. This is the single largest practical implication.
- **Reduce process disclosure** in job adverts, case studies and conference talks, as the cheapest available mitigation (file `03` §2.3).
- **Brief high-exposure staff before high-exposure moments.**

---

## 4. Prompt injection and the social engineering of AI agents

This is the genuinely new category, and it deserves the space. An LLM-based agent reads text and acts on it. If an attacker controls text the agent reads, the attacker can attempt to control the agent. **This is social engineering with the human replaced by a model** — the same structure of authority claims, urgency and misdirected trust, applied to a system that has no truth-default to defend and no colleague to consult.

OWASP ranks it **LLM01:2025 Prompt Injection**, the first entry in the OWASP Top 10 for LLM Applications 2025. NIST's **AI 100-2 E2025** (24 March 2025) provides the formal taxonomy and terminology for adversarial machine learning within which these attacks sit.

### 4.1 Direct prompt injection
A user supplies input that changes the model's behaviour — intentionally or not. OWASP notes the effect need not be visible to a human: it works as long as the model parses the content. Documented attack shapes include adversarial suffixes, multilingual phrasing, and encoded instructions (e.g. Base64) intended to slip past naive filters.

**Risk to an organisation:** mostly reputational and policy-related where the user is the attacker and attacks their own session. It becomes serious when the model's output is consumed by another system without validation (see **LLM05:2025 Improper Output Handling**).

### 4.2 Indirect prompt injection — the important one
The model processes **external content** — a web page, an email, a PDF, a calendar invite, a code comment, a support ticket, a document in a shared drive — that contains instructions. The model has no reliable way to distinguish "data I was asked to summarise" from "instructions I should follow", because both arrive as text in the same context window.

OWASP's published scenarios include hidden instructions in a web page that cause data exfiltration, malicious content split across sections of a résumé to manipulate an automated evaluation, and a support chatbot induced to disregard its guidelines and reach a private database.

**Why this maps exactly onto social engineering.** The attacker never touches the target system. They place content where a trusted process will read it, and the trusted process acts with its own privileges. It is a **watering hole for machines**.

### 4.3 Tool use and the confused deputy
An agent with tools — send email, browse, execute code, query a database, make a purchase, file a ticket — is a **deputy holding the user's authority**. The classic confused-deputy problem is that the deputy's privileges are used at the direction of someone who does not hold them. In agent terms: the agent has your mailbox access; the injected instruction does not; but the injected instruction can direct the agent's use of it.

**Concrete risk shapes to design against:**
- **Exfiltration through legitimate tools** — the agent is induced to include sensitive context in an outbound request, a URL parameter, an image fetch, or a message to an attacker-controlled destination.
- **Privilege chaining** — the agent uses one tool's output to authorise another action.
- **Persistence** — injected content written into the agent's own memory, notes or a shared document, so the compromise recurs on future runs.
- **Excessive agency** (OWASP **LLM06:2025**) — the agent simply has more capability than the task requires, so a successful injection is worth more.

### 4.4 Agentic browsing and autonomous agents
An agent that browses the live web on a user's behalf, while authenticated as that user, combines the worst properties: untrusted input by definition, real credentials, and real capability. The same applies to agents connected to mailboxes, ticketing systems, code repositories and payment tools.

**Design rules (drawing on OWASP's prevention guidance and standard least-privilege practice):**
1. **Treat all model output as untrusted input** to whatever consumes it. Validate and constrain formats; never pass model output into a shell, a query or a renderer unescaped.
2. **Least privilege for the agent**, scoped per task, with credentials that are not the user's full credentials.
3. **Human approval for consequential, irreversible actions** — payments, external sends, data deletion, permission changes, code merges. This is the same dual-control principle as file `04` §7, applied to a non-human actor.
4. **Segregate and label external content clearly** in the context so the system prompt's authority is structurally distinguishable, and constrain model behaviour with a specific system prompt.
5. **Filter input and output** with semantic checks, not only string matching.
6. **Adversarial testing** as a routine, repeated activity, not a one-off assessment.
7. **Log everything the agent does**, and alert on unusual tool-use sequences and on outbound destinations not previously seen. Agent activity is a detection surface, and most organisations currently have no telemetry for it.
8. **Set spend, rate and scope limits** so a compromised agent's blast radius is bounded.
9. **Isolate browsing** from authenticated sessions where possible — an agent that browses should not hold your session cookies.

**Honest limitation.** There is at present **no complete solution to prompt injection**. OWASP's guidance is framed as mitigation, not elimination, and the reason is structural: instructions and data share a channel. Any vendor claiming to have solved it should be treated the way you would treat a claim to have solved phishing. Plan on the assumption that injection will sometimes succeed, and bound the consequences — the identical posture recommended for human social engineering throughout this domain.

---

## 5. Synthetic identity fraud

Synthetic identity fraud combines real and fabricated attributes into an identity that passes checks but corresponds to no person. Generative AI contributes: plausible document images, consistent photographs across a fabricated history, and — increasingly — the ability to pass some remote video "liveness" checks.

**Where it bites in this domain:**
- **Fraudulent job applicants** obtaining remote employment and internal access (file `02` §10).
- **Fraudulent vendor onboarding** creating a payment relationship with no underlying entity.
- **Account opening** at financial institutions, enabling mule infrastructure that receives BEC proceeds.

**Controls:** document verification with chip/NFC reading rather than photograph inspection; liveness checks with active challenges; cross-checking against authoritative registries rather than supplied documents; equipment shipped only to verified addresses; and — for vendors — independent verification of the legal entity and its banking relationship before the first payment.

---

## 6. Defensive uses of AI

The technology is not one-sided, and the defensive applications are less speculative than the offensive hype suggests.

- **Anomaly detection on communications**: models that learn normal writing style, relationship graphs and payment patterns can flag a request that is out of character for a real sender — which is exactly the BEC and thread-hijacking case that content filters miss.
- **Triage of the report queue.** Clustering user reports into campaigns, deduplicating, and prioritising is a natural fit and directly amplifies the human-sensor capability that Lain et al. showed to be effective.
- **Detection engineering assistance**: drafting and tuning detection logic, summarising alerts, and generating investigation timelines.
- **Exposure inventory**: automating the periodic sweep of your own public footprint (file `03` §2).
- **Personalised, contextual training** delivered at the moment of risk, which the evidence favours over annual modules (file `05` §4).
- **Voice-channel anomaly detection** in contact centres — behavioural and device signals rather than attempts to detect synthesis.

**Where to be sceptical.** Products claiming reliable deepfake detection, claiming to "eliminate" phishing risk, or claiming to solve prompt injection. Ask for the false-positive rate on your own traffic, the generalisation evidence to unseen generators, and an independent evaluation. Treat any vendor statistic without a dated, reproducible methodology as marketing.

---

## 7. What to change now, and what to watch

**Change now:**
1. Strip language-quality indicators from all training and replace with structural indicators.
2. Adopt process-over-identity for all financial authorisation; assume voice and video are forgeable.
3. Establish family and corporate code words for verbal authorisation.
4. Abolish knowledge-based verification everywhere.
5. Inventory every AI agent with tool access, apply least privilege and human-in-the-loop for irreversible actions, and start logging agent activity.
6. Add prompt injection to your threat model and your penetration testing scope; use NIST AI 100-2 E2025 for terminology and OWASP LLM Top 10 2025 for the risk register.

**Watch, without acting prematurely:**
- Maturation of content provenance (C2PA) in conferencing and mobile capture.
- Whether measured compromise rates — not lure volume — shift attributably to AI. The DBIR and IC3 series are the places this will show up first.
- Regulatory treatment of synthetic media in financial authorisation contexts.
- Emerging architectural mitigations for prompt injection that separate instruction and data channels at the model level, rather than filtering.

## Sources

- [LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) — OWASP GenAI Security Project
- [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/) — OWASP GenAI Security Project
- [NIST AI 100-2 E2025: Adversarial Machine Learning](https://csrc.nist.gov/pubs/ai/100/2/e2025/final) — NIST, 24 March 2025
- [ENISA Threat Landscape 2024](https://www.enisa.europa.eu/sites/default/files/2024-11/ENISA%20Threat%20Landscape%202024_0.pdf) — ENISA
- [Deepfake](https://en.wikipedia.org/wiki/Deepfake) — Wikipedia (Arup, 2019 case, DFDC and MIT detection accuracy)
- [Machine Learning Principles](https://www.ncsc.gov.uk/collection/machine-learning) — UK NCSC, 22 May 2024
- [DBIR landing page (2026 edition summary)](https://www.verizon.com/business/resources/reports/dbir/) — Verizon Business
- [Pig butchering scam](https://en.wikipedia.org/wiki/Pig_butchering_scam) — Wikipedia (industrialised relationship fraud context)

## Open questions

- **NIST AI 100-2 E2025 attack-category detail** — only the title, number, date and scope were retrievable from the CSRC landing page; the taxonomy's specific generative-AI categories were not read. Marked `needs-verification` for any specific category claim.
- **NCSC Machine Learning Principles sub-pages** (secure design, development, deployment, operation, end of life) were not read; only the 22 May 2024 overview was retrieved. The NCSC/CISA *Guidelines for Secure AI System Development* should also be consulted directly.
- **C2PA content credentials** are described from general knowledge; the specification was not fetched.
- **Claims of percentage increases in phishing volume attributable to AI** circulate widely from vendor telemetry. None is used here, because none could be verified against a dated, methodologically transparent source.
- The statement that no complete solution to prompt injection exists reflects OWASP's mitigation-framed guidance as of the 2025 list; re-check at each OWASP revision.

