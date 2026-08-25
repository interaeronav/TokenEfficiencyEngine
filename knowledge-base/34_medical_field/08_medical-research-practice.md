---
id: medical_field.research_practice
title: Medical research practice — from question to publication
domain: 34_medical_field
tags: [pico, protocol, irb, rec, research-ethics, declaration-of-helsinki, good-clinical-practice, informed-consent, trial-registration, data-management, statistical-analysis-plan, imrad, icmje, authorship, peer-review, grants, clinician-scientist, md-phd]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Declaration of Helsinki", url: "https://en.wikipedia.org/wiki/Declaration_of_Helsinki", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Defining the Role of Authors and Contributors (ICMJE Recommendations)", url: "https://www.icmje.org/recommendations/browse/roles-and-responsibilities/defining-the-role-of-authors-and-contributors.html", publisher: "ICMJE", accessed: 2026-08-25}
  - {title: "MD–PhD", url: "https://en.wikipedia.org/wiki/MD%E2%80%93PhD", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Replication crisis", url: "https://en.wikipedia.org/wiki/Replication_crisis", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Consolidated Standards of Reporting Trials", url: "https://en.wikipedia.org/wiki/Consolidated_Standards_of_Reporting_Trials", publisher: "Wikipedia", accessed: 2026-08-25}
related: [medical_field.ebm, medical_field.literature, medical_field.drug_development]
unit_system: SI
---

# Medical research practice — from question to publication

**Summary.** This file is the operational counterpart to `05_evidence-based-medicine.md`: not how to read a study but how to do one. It covers question formulation, protocol writing, the ethics approval machinery and its founding documents, informed consent, trial registration, data management, statistical analysis plans, the statistics a clinician-researcher must actually be able to use, writing for publication under ICMJE rules, peer review from both sides, grant funding, and the career structures — MD-PhD and clinician-scientist pathways — that make a research life possible.

> ⚠️ Nothing here is medical advice. This file describes research governance and methods; it is not a substitute for your institution's own SOPs, your REC/IRB's requirements, or national law.

## Key facts

| Item | Detail |
|---|---|
| Declaration of Helsinki adopted | **June 1964**, Helsinki |
| Revisions | 1975 Tokyo · 1983 Venice · 1989 Hong Kong · 1996 Somerset West (South Africa) · 2000 Edinburgh · 2008 Seoul · 2013 Fortaleza · **2024 Helsinki** (most recent) |
| Core principle | "The participant's welfare must always take precedence over the interests of science and society" |
| Independent ethics review | Introduced in the **1975** revision; US IRB regulations took effect **1981** |
| ICMJE authorship criteria | **Four**, all of which must be met |
| AI and authorship | "AI cannot be listed as an author or co-author"; use must be disclosed |
| Trial registration | Required prospectively by ICMJE as a condition of publication (policy from 2005) |
| MD-PhD duration | **8+ years**; NIH MSTP supports ~50 schools; attrition ≈10% (1998–2007 entrants) |
| MD-PhD outcomes | ~67% academic centres, 4% research institutes, 8% industry |

---

## 1. Formulating the question

A research question is not a topic. The discipline of converting an interest into an answerable question is the single highest-leverage step in a project, because everything downstream — design, sample size, analysis, reporting — is determined by it.

### PICO and its relatives

**PICO** — the standard structure for a therapy or prevention question:

- **P**opulation — who, defined by inclusion and exclusion criteria specific enough that another team could assemble the same group.
- **I**ntervention — what, defined precisely enough to replicate (dose, route, duration, who delivers it, in what setting).
- **C**omparator — against what: placebo, active control, usual care, nothing. This choice determines what the answer means.
- **O**utcome — measured how, when, by whom, and with a single pre-specified **primary** outcome.

Extensions: **PICOT** adds **T**ime (follow-up horizon), **PICOS** adds **S**tudy design, **PECO** substitutes **E**xposure for aetiological questions. For diagnostic questions the structure is **PIRD** (Population, Index test, Reference standard, Diagnosis of interest); for prognosis, **PEO**; for qualitative research, **SPIDER** (Sample, Phenomenon of Interest, Design, Evaluation, Research type).

### FINER

Hulley's criteria for whether a question is worth pursuing: **F**easible (adequate subjects, technical expertise, time and money, manageable scope), **I**nteresting to the investigator, **N**ovel (confirms, refutes or extends existing findings), **E**thical, **R**elevant (to knowledge, to practice, to policy, to future research).

Two additions that the FINER acronym does not capture and which are the commonest failures in practice: **has this already been answered?** — a systematic search before designing a study is now an expected step, and funders increasingly require evidence that the proposed trial is not redundant — and **is the question one that patients care about?**, which is what patient and public involvement (PPI) exists to establish. **[UK]** NIHR requires PPI in funding applications; the James Lind Alliance Priority Setting Partnerships exist to identify what patients and clinicians actually want answered, and their answers repeatedly diverge from what researchers choose to study.

## 2. The protocol

The protocol is the contract between the investigator, the participants, the ethics committee, the regulator, the funder and the eventual reader. **SPIRIT 2013** (with its 2025 update) is the reporting guideline for protocols and is the correct template.

Standard contents:

1. **Administrative** — title, registration identifiers, protocol version and date, funders, roles and responsibilities, sponsor, trial committees (steering, DSMB, endpoint adjudication).
2. **Introduction** — background, rationale, justification for the comparator, explicit statement of the objectives and hypotheses.
3. **Methods** — design (with allocation ratio and framework: superiority, non-inferiority, equivalence); setting; eligibility criteria; the interventions with strategies for adherence and permitted concomitant care; **outcomes** with definitions, measurement instruments, timepoints and the specific metric used for analysis; participant timeline; **sample size** with all its assumptions stated; recruitment strategy.
4. **Allocation** — sequence generation, **concealment mechanism**, implementation (who generates, who enrols, who assigns), blinding and the procedure for unblinding.
5. **Data collection, management and analysis** — instruments, retention plans, data management procedures, the statistical methods for primary and secondary outcomes, methods for additional analyses (subgroups, adjusted), handling of non-adherence and **missing data**.
6. **Monitoring** — data monitoring committee composition and independence, interim analyses and stopping guidelines, harms collection and reporting, auditing.
7. **Ethics and dissemination** — approvals, protocol amendments, consent, confidentiality, declaration of interests, **access to data**, ancillary and post-trial care, dissemination policy, **authorship rules agreed in advance**, plans for public data availability.
8. **Appendices** — model consent form, biological specimen handling.

Two practical rules. First, **write the analysis before you collect the data**; if you cannot specify the analysis, the question is not yet defined. Second, **write the tables and figures you intend to publish, empty**, at protocol stage. Shell tables expose ambiguity in outcome definitions faster than any amount of prose.

## 3. Research ethics: the founding documents

**The Nuremberg Code (1947)** emerged from the Doctors' Trial and established voluntary consent as absolutely essential, alongside social value, avoidance of unnecessary suffering, qualified investigators and the right to withdraw.

**The Declaration of Helsinki**, adopted by the World Medical Association in **June 1964**, is the profession's own statement of ethical principles for medical research involving human participants. It has been revised eight times — **1975 (Tokyo), 1983 (Venice), 1989 (Hong Kong), 1996 (Somerset West, South Africa), 2000 (Edinburgh), 2008 (Seoul), 2013 (Fortaleza), and 2024 (Helsinki)**. The 2000 revision was described as the most far-reaching and contentious to that point, principally over placebo controls and post-trial access; the 2024 revision is the most recent.

Core principles as they stand:
- **The welfare of the individual participant takes precedence over the interests of science and society.**
- Respect for autonomy and genuinely informed, freely given consent.
- Independent ethical review before the research begins — the **1975** revision introduced the "independent committee", which became the **IRB** in the US (regulations effective **1981**) and the research ethics committee elsewhere.
- Scientific validity as an ethical requirement: a badly designed study cannot be ethical, because it exposes participants to risk for no possible knowledge gain.
- Favourable risk–benefit balance, with special protections for vulnerable groups.
- Public registration and publication of results, including negative results.
- Post-trial provisions for participants.

The Declaration is **not itself legally binding** but is incorporated by reference into national regulation, into GCP, and into most journals' publication requirements.

**The Belmont Report (1979)**, produced after the exposure of the Tuskegee syphilis study, gave US research ethics its three principles — **respect for persons, beneficence, justice** — mapped onto informed consent, risk–benefit assessment, and fair selection of subjects. **The Common Rule** (45 CFR 46, substantially revised in 2018) is the US federal regulation implementing them.

**CIOMS International Ethical Guidelines** (with WHO, most recently 2016) address the problems Helsinki leaves thin, particularly research in low-resource settings: standard of care in the control arm, community engagement, capacity building, and post-trial access.

**[ZA]** South Africa's framework: the **National Health Act 61 of 2003** (sections 71–73 on research on human subjects), the National Department of Health's *Ethics in Health Research: Principles, Processes and Structures* (2nd edition, 2015), the **National Health Research Ethics Council (NHREC)** which registers and audits RECs, the **Protection of Personal Information Act (POPIA)**, and SAHPRA's requirements for clinical trials. Every South African university has a registered Health Research Ethics Committee. **[NA]** Namibia's research is governed by the Ministry of Health and Social Services research authorisation process and institutional review at UNAM, with regional ethics review through partner institutions for multi-country studies.

### The historical cases every researcher is taught

Nazi medical experiments; the **Tuskegee Study of Untreated Syphilis in the Negro Male** (1932–1972), which withheld effective treatment from Black American men for four decades and is the direct cause of measurable, rational, persistent mistrust of medical research in Black communities; the Willowbrook hepatitis studies; the Jewish Chronic Disease Hospital cancer-cell injections; the Guatemala syphilis experiments (1946–1948); the unconsented harvesting of **Henrietta Lacks's** cells (1951); and, in the modern era, the Havasupai diabetes samples used for unconsented ancestry and schizophrenia research. **[ZA]** Southern African research ethics carries the additional weight of apartheid-era medical complicity and of the 1990s–2000s HIV trials conducted in populations who could not afford the resulting drugs — the origin of the "standard of care in the control arm" debate that reshaped Helsinki in 2000.

## 4. Good Clinical Practice

**ICH E6 Good Clinical Practice** is the international quality standard for designing, conducting, recording and reporting trials involving human participants. **E6(R2)** added risk-based quality management; **E6(R3)**, adopted in 2025, restructured the guideline around proportionality, fitness for purpose and modern data sources including decentralised trials and real-world data.

The thirteen principles, in substance: trials are conducted according to Helsinki, GCP and applicable regulation; anticipated benefits justify risks; participant rights, safety and wellbeing prevail over science and society; adequate non-clinical and clinical information supports the trial; the trial is scientifically sound and described in a clear protocol; conduct follows the protocol as approved by the IRB/IEC; medical care and decisions remain the responsibility of a qualified physician; personnel are qualified; freely given informed consent is obtained from every participant; information is recorded, handled and stored so it can be accurately reported, interpreted and verified; confidentiality is protected; investigational products are manufactured to GMP and used per protocol; and quality systems are implemented.

**In practice this means:** a delegation log, signed and dated; a trial master file; source data that are attributable, legible, contemporaneous, original and accurate (**ALCOA**, extended to ALCOA+ with complete, consistent, enduring and available); an investigator's brochure; monitoring visits and source data verification; a serious adverse event reporting pathway with defined timelines; and inspection readiness.

**Adverse event terminology** every investigator must be able to use correctly: an **adverse event (AE)** is any untoward occurrence, whether or not related; an **adverse reaction (AR)** is one judged causally related; a **serious adverse event (SAE)** meets one of the seriousness criteria (death, life-threatening, hospitalisation or prolongation, persistent or significant disability, congenital anomaly, or other medically important event); and a **SUSAR** is a suspected unexpected serious adverse reaction — serious, related, and not consistent with the reference safety information — which triggers expedited reporting to the regulator and the ethics committee.

## 5. Informed consent

Consent is a **process**, not a form. Its elements:

- **Capacity** to consent, assessed and documented; a pathway for participants who lack capacity (legally authorised representative, and in emergency research, exception-from-consent frameworks with community consultation).
- **Disclosure** — purpose, procedures, duration, risks, benefits (including honest statement of the possibility of none), alternatives, confidentiality, compensation for injury, funding and conflicts, and whom to contact.
- **Understanding** — plain language at an appropriate reading level, in the participant's language, with time to consider and to discuss with others. **Teach-back** is the standard technique for verifying comprehension.
- **Voluntariness** — free of coercion or undue influence. Payment should compensate for time and inconvenience without being so large as to distort risk judgement, a boundary that ethics committees police case by case.
- **Documentation** — signed and dated by participant and by the person taking consent; **witnessed consent** where the participant cannot read.
- **Ongoing consent** — re-consent after protocol amendments, and the right to withdraw at any time without penalty.

Recurring problems: the **therapeutic misconception** (participants believing a trial is treatment individualised for them); consent forms that have grown to 20+ pages of legally driven text nobody reads; consent in emergency and critical care; consent for **secondary use of data and samples** — broad consent, dynamic consent, and the biobanking debate; and consent in settings with a steep power gradient between clinician-investigator and participant. **[ZA]/[NA]** Multilingual consent, low literacy, community and traditional-authority engagement, and the ethics of paying travel costs in low-income settings are live and specific problems, and RECs in the region examine them closely.

## 6. Registration, data management and the analysis plan

### Trial registration

Prospective registration in a WHO ICTRP primary registry — **ClinicalTrials.gov**, **ISRCTN**, the EU **CTIS**, ANZCTR, CTRI (India), the **[ZA] South African National Clinical Trial Register** — is required by the ICMJE as a condition of publication, by the Declaration of Helsinki, and by many funders. Registration must occur **before the first participant is enrolled**, and the registered primary outcome is the one against which the published paper will be judged. **[US]** The FDA Amendments Act of 2007 requires results reporting to ClinicalTrials.gov within 12 months of completion for applicable trials — a requirement with documented, widespread non-compliance, tracked publicly by projects such as the EU Trials Tracker and FDAAA TrialsTracker.

Systematic reviews register in **PROSPERO**; observational studies increasingly register too, and some journals now require it.

### Data management

- **A data management plan** written before collection: what is collected, in what format, where stored, who has access, how long retained, how shared.
- **Electronic data capture** — REDCap (free to non-profit consortium members and near-universal in academic medicine), Medidata Rave, OpenClinica — with audit trails, edit checks and role-based access. Spreadsheets are not a data management system and are the origin of a disproportionate share of retractions.
- **Case report forms** designed against the shell tables; every field must map to an analysis.
- **Identifiability** — direct identifiers separated from research data, a linkage key held separately, and a defined de-identification standard. **[EU]/[UK]** GDPR and the UK Data Protection Act; **[US]** HIPAA and the Common Rule; **[ZA]** POPIA. Anonymised data fall outside most of these regimes; pseudonymised data do not.
- **Reproducibility** — version control (git) for analysis code, a scripted rather than point-and-click analysis, a defined random seed, and a data dictionary. If the analysis cannot be rerun from raw data by a stranger, it is not reproducible and neither is the paper.
- **Sharing** — FAIR principles (Findable, Accessible, Interoperable, Reusable), controlled-access repositories (dbGaP, EGA), and individual participant data sharing platforms (Vivli, YODA, ClinicalStudyDataRequest.com). Sharing plans are now required by the NIH (2023 policy), Wellcome, and increasingly by journals.

### The statistical analysis plan (SAP)

A separate, dated, version-controlled document finalised **before unblinding**, containing:

- The estimand: precisely what quantity is being estimated, in whom, under what handling of intercurrent events (the **ICH E9(R1)** addendum framework, which forced the field to be explicit about what "the treatment effect" means when people stop taking the drug or take something else).
- Analysis populations: ITT, modified ITT with justification, per-protocol, safety population.
- The primary analysis model, exactly specified, including covariates and their form.
- Handling of missing data, with a primary approach and pre-specified sensitivity analyses.
- Multiplicity strategy and the testing hierarchy.
- Subgroup analyses, pre-specified and limited, tested by interaction.
- Interim analyses and stopping boundaries.
- Definitions of derived variables.

The SAP is what separates confirmatory analysis from exploration. Analyses not in the SAP are exploratory and must be labelled as such — a rule broken constantly and detectably.

## 7. The statistics a clinician-researcher must know

Not to be a statistician — to talk to one usefully, and to avoid the errors that destroy a study before a statistician sees it.

**Descriptive and inferential basics.** Distributions and when the normal approximation matters; measures of central tendency and spread and when the median is obligatory; standard deviation versus standard error (a confusion that appears in published figures constantly); the central limit theorem and what it does and does not license.

**Comparisons.** t-tests and their assumptions; ANOVA and post-hoc correction; non-parametric alternatives (Mann–Whitney, Wilcoxon, Kruskal–Wallis) and their real hypothesis, which is not "the medians are equal"; chi-squared and Fisher's exact test; paired versus unpaired designs; and the fact that **the design determines the test**, not the other way round.

**Regression.** Linear regression and its assumptions (linearity, independence, homoscedasticity, normality of residuals); logistic regression for binary outcomes and the interpretation of an odds ratio; Poisson and negative binomial for counts and rates; the difference between prediction and explanation, which drives whether you should be selecting variables at all; interaction and effect modification versus confounding; **collinearity**; and why stepwise variable selection is a discredited procedure that still appears in submitted manuscripts every week.

**Time-to-event.** Kaplan–Meier estimation, censoring and its assumptions, the log-rank test, Cox proportional hazards and how to check the proportional-hazards assumption, competing risks (Fine–Gray), and restricted mean survival time as an alternative when hazards are not proportional.

**Clustered and longitudinal data.** Mixed-effects models and generalised estimating equations; the intracluster correlation coefficient and the design effect, which is why a cluster-randomised trial needs more participants than an individually randomised one; repeated measures handled properly rather than by comparing timepoints separately.

**Design-side statistics.** Sample size and power for the common designs; the **minimum clinically important difference** and the fact that it is a clinical, not statistical, judgement; the consequences of underpowering (missed effects *and* inflated estimates among the significant ones); randomisation methods including stratification and minimisation.

**Measurement.** Reliability (intraclass correlation, Cohen's and Fleiss's kappa), agreement (Bland–Altman, not correlation — plotting two methods against each other and reporting r is one of the most persistent errors in the clinical literature), validity, responsiveness, and floor and ceiling effects.

**Diagnostic and prognostic performance.** Sensitivity, specificity, predictive values and their dependence on prevalence, likelihood ratios, ROC curves and AUC, calibration (which matters more than discrimination for a clinical prediction model and is reported far less often), and the distinction between development and external validation.

**Causal inference from observational data.** Directed acyclic graphs for reasoning about which variables to adjust for — and, critically, which not to (adjusting for a mediator or a collider introduces bias rather than removing it); propensity scores and their four uses; instrumental variables; difference-in-differences and interrupted time series for policy evaluation; and target trial emulation as the organising discipline.

**Software.** **R** (free, the field's lingua franca, with the tidyverse and the survival, lme4, meta and mice packages), **Stata** (dominant in epidemiology and health economics), **SAS** (still dominant in regulated pharmaceutical work), **Python** (growing, strongest where the work is computational), **SPSS** (widespread in teaching, discouraged for research because point-and-click analysis is not reproducible). Choose one and learn it properly; the choice matters far less than whether the analysis is scripted.

## 8. Writing for publication

### IMRaD

**I**ntroduction — what is known, what is not known, what this study does. Three paragraphs is usually enough; the last sentence states the objective.
**M**ethods — enough for replication, in the past tense, following the relevant reporting guideline. Ethics approval and registration go here.
**R**esults — what was found, without interpretation. Numbers with measures of uncertainty; the primary outcome first; no p-value without an effect estimate.
**a**nd
**D**iscussion — a short summary of the principal finding; comparison with existing literature; **limitations, stated honestly and specifically** (not "further research is needed"); implications; conclusion that does not exceed the data.

Plus: title, structured abstract (which is what nearly everyone will read and, in a large fraction of cases, all they will read), keywords, tables and figures, references, contributions, funding, conflicts, data availability.

**Choose the reporting guideline before writing**, from the EQUATOR Network: CONSORT for trials (2010, updated **2025** with seven new items, three modified, one removed and a new open-science section), PRISMA for systematic reviews, STROBE for observational studies, STARD for diagnostic accuracy, TRIPOD for prediction models, CARE for case reports, SQUIRE for quality improvement, COREQ for qualitative work, ARRIVE for animal studies.

### ICMJE authorship

The **International Committee of Medical Journal Editors** recommends that authorship require **all four** of the following:

1. "Substantial contributions to the conception or design of the work; or the acquisition, analysis, or interpretation of data";
2. "Drafting the work or reviewing it critically for important intellectual content";
3. "Final approval of the version to be published";
4. "Agreement to be accountable for all aspects of the work in ensuring that questions related to the accuracy or integrity of any part of the work are appropriately investigated and resolved".

Those who do not meet all four should be **acknowledged**, not listed as authors. Activities that alone do not qualify include acquiring funding, general supervision of a research group, and "writing assistance, technical editing, language editing, and proofreading".

**Named abuses:** *gift* or *honorary* authorship (adding a head of department who did nothing); *ghost* authorship (omitting a professional medical writer paid by a sponsor, historically endemic in industry-sponsored publication); *guest* authorship (adding a prestigious name to ease acceptance); and coercive authorship by supervisors. The **CRediT taxonomy** (14 contributor roles) is the increasingly common remedy: state who did what, explicitly.

**AI-assisted technologies.** ICMJE requires disclosure at submission: describe the use in the cover letter and in the relevant manuscript sections; **AI cannot be listed as an author or co-author**; "authors should carefully review and edit the result because AI can generate authoritative-sounding output that can be incorrect, incomplete, or biased"; and AI-assisted writing should be reported in the acknowledgements. Humans remain fully responsible for the submitted work, including the absence of plagiarism and the correctness of all attribution.

Other ICMJE requirements: prospective trial registration; a conflict-of-interest disclosure from every author; a data-sharing statement for clinical trials; and no duplicate or redundant publication.

### Publication ethics

**COPE** (the Committee on Publication Ethics) publishes the flowcharts editors follow for suspected misconduct. The recognised categories: fabrication, falsification, plagiarism (including self-plagiarism and text recycling), image manipulation (duplication, splicing, inappropriate adjustment — now routinely screened by software and by sleuths on PubPeer), salami publication, duplicate submission, undisclosed conflicts, and authorship disputes. Outcomes range from correction through expression of concern to retraction. The **Retraction Watch Database** is the public record; retractions have risen sharply, driven substantially by **paper mills** selling authorship on fabricated manuscripts at industrial scale.

## 9. Peer review, from both sides

### As an author

Journal selection first: scope fit, audience, indexing, speed, open-access model and cost, and — see `06` — whether it is legitimate. Read the instructions to authors before writing, not after. Write a cover letter that says in three sentences what is new and why this journal's readers need it. Suggest reviewers honestly and declare exclusions with reasons.

Then wait. Desk rejection at high-impact journals runs 50–80% of submissions and typically arrives in days, which is a service. If reviewed, expect one of: accept (rare), minor revision, major revision, reject with an invitation to resubmit, or reject.

**Responding to reviewers.** A point-by-point response letter reproducing each comment; a clear statement of what changed and where (page and line); polite, specific disagreement where you disagree, backed by evidence rather than assertion; and no unaddressed comments. Reviewers are almost always improving the paper even when they are wrong about the reason. If rejected, revise using the reviews before submitting elsewhere — and expect to meet the same reviewer.

**Cascading and transfer** — many publishers offer transfer to a lower-tier journal in the same family with the reviews attached, which saves months.

### As a reviewer

You will be asked once you have published a few papers, and the obligation is real: the system runs on unpaid labour, roughly proportional to what you consume.

- **Decline if you cannot do it properly** — outside your competence, no time, or a conflict of interest (recent collaboration, same institution, competing work, financial interest). Say so quickly; a slow decline is worse than a fast one.
- **Confidentiality is absolute.** The manuscript is not yours to circulate, cite, use, or paste into an AI system that retains inputs. Several journals now explicitly prohibit uploading manuscripts to generative AI tools.
- **Structure a review**: a short summary of what the paper claims (which demonstrates you read it and lets the editor calibrate); major concerns, numbered, each with the specific issue and what would resolve it; minor points; and confidential comments to the editor with your recommendation.
- **Review the work, not the author.** Comment on what is there. Do not demand the study you would have done, or citations to your own work.
- **Check the things that are checkable**: does the reported analysis match the registered protocol; do the numbers in the abstract match the tables; do the tables add up; is the reporting guideline followed; are the figures internally consistent; is there a data-availability statement.
- **Recommend, do not decide.** The editor decides.

**Models.** Single-blind (reviewers anonymous, the default and criticised for enabling bias without accountability); double-blind (both anonymised, imperfectly, and increasingly common); **open review** (signed reviews published with the paper — the *BMJ*'s model, and BMC's); and post-publication review (PubPeer, F1000Research). Known failures of peer review: it is slow, it detects fraud poorly, it is inconsistent between reviewers, it is conservative toward novel claims, and it can be biased by author gender, institution and country. Known value: it substantially improves reporting quality even when it does not change conclusions. The honest position is Rennie's — peer review is a weak filter that is better than no filter, and its main product is a better paper, not a correct one.

## 10. Grant funding

**Major public funders.** **[US]** NIH (the R01 as the standard investigator-initiated project grant; K awards for career development; F awards for fellowships; R21 for exploratory work; U and P mechanisms for cooperative and programme funding), plus AHRQ, PCORI, CDC, and the Department of Veterans Affairs. **[UK]** NIHR (applied and clinical research, with a strong PPI requirement), MRC, Wellcome (charitable and among the world's largest), the British Heart Foundation and Cancer Research UK. **[EU]** Horizon Europe and the European Research Council (ERC Starting, Consolidator, Advanced — funding people and ideas rather than projects). **[ZA]** the **South African Medical Research Council (SAMRC)**, the **National Research Foundation (NRF)** with its rating system, the DSI, and substantial international funding through NIH, Wellcome, Gates and EDCTP/Global Health EDCTP3. **[NA]** the National Commission on Research, Science and Technology (NCRST), with most clinical research funding arriving through regional and international partnerships. Globally: the Gates Foundation, the Global Fund, Unitaid, and Wellcome.

**Anatomy of an application.** Specific aims or summary (the single most important page — it is what reviewers read first and often decides the outcome); background and significance; innovation; approach, with preliminary data, methods, sample size, analysis, timeline, milestones and a frank statement of pitfalls and alternatives; investigator team and environment; budget and justification; data management and sharing plan; PPI plan; and a dissemination plan.

**Realities.** Success rates for major project grants commonly sit in the 10–25% range and are lower for early-career applicants; writing a major application costs weeks of unfunded time; resubmission after rejection is normal and often successful; and the funding system's incentives — novelty, positive results, productivity metrics — feed directly into the questionable research practices described in `05`. **[ZA]/[NA]** For southern African researchers the binding constraints are usually not ideas but protected research time, statistical support, and the fact that the largest funders are foreign, which shapes what gets studied.

## 11. Research careers

### MD-PhD and the physician-scientist

The **MD-PhD** route interleaves the pre-clerkship medical curriculum, a complete PhD, and the clinical years — **eight or more years** in total. **[US]** NIH **Medical Scientist Training Program (MSTP)** grants support roughly 50 schools; some programmes admit as few as two students a year. Matriculants have higher mean MCAT and GPA than MD-only entrants. Attrition averaged about **10%** for 1998–2007 entrants, varying substantially by school. Outcomes are strongly academic: roughly **67%** in academic centres, **4%** in research institutes such as the NIH, **8%** in industry — about 80% in research-adjacent full-time employment. Internal medicine (29%) and surgery (11%) are the commonest residencies.

**[UK]** The equivalents are the **Academic Clinical Fellowship (ACF)** and **Clinical Lectureship (CL)** under the NIHR Integrated Academic Training pathway, with a funded PhD (usually a three-year MRC/Wellcome/charity clinical research training fellowship) between them. **[ZA]** The MMed research component is the entry point, followed by a PhD, with SAMRC clinician-researcher and NRF rating pathways; the structural obstacle is that public-sector clinical service demand leaves little protected time. **[NA]** Namibian clinical research careers are typically built through collaboration with South African or international institutions.

### The problem the pathway faces

The physician-scientist workforce has been described as an endangered species for four decades, and the reasons are structural rather than motivational:

- **Length.** A physician-scientist commonly reaches independence in their late thirties or early forties, a decade behind a PhD-only peer.
- **Debt.** **[US]** MD-only graduates carry median education debt around US$200,000, which makes a salary-sacrificing research career financially irrational without loan repayment programmes.
- **The 80/20 fiction.** Protected research time is the first thing surrendered when clinical service is short-staffed, which it always is.
- **Grant competition.** Competing with full-time scientists for the same grants while carrying clinical duties.
- **No clear off-ramp back.** Leaving research is easy; returning is not.

Countermeasures with some evidence: bridge funding, institutional protected-time guarantees written into contracts, loan repayment programmes (the NIH LRP), team-science models in which the clinician contributes clinical insight and access rather than running a bench, and clinical-trialist and implementation-science careers that do not require a laboratory.

### Other research-adjacent careers

Clinical trialist; epidemiologist and public health researcher; health services and implementation researcher; medical educationalist (a genuine research discipline with its own journals and methods); clinical informatician (see `10`); biostatistician; regulatory scientist; and industry medical affairs and clinical development, which absorbs a substantial and growing share of clinically trained researchers and is frequently a better-resourced environment for actually completing trials.

## Sources

- [Declaration of Helsinki](https://en.wikipedia.org/wiki/Declaration_of_Helsinki) — Wikipedia, accessed 2026-08-25
- [Defining the Role of Authors and Contributors](https://www.icmje.org/recommendations/browse/roles-and-responsibilities/defining-the-role-of-authors-and-contributors.html) — ICMJE, accessed 2026-08-25
- [MD–PhD](https://en.wikipedia.org/wiki/MD%E2%80%93PhD) — Wikipedia, accessed 2026-08-25
- [Replication crisis](https://en.wikipedia.org/wiki/Replication_crisis) — Wikipedia, accessed 2026-08-25
- [Consolidated Standards of Reporting Trials](https://en.wikipedia.org/wiki/Consolidated_Standards_of_Reporting_Trials) — Wikipedia, accessed 2026-08-25
- [Evidence-based medicine](https://en.wikipedia.org/wiki/Evidence-based_medicine) — Wikipedia, accessed 2026-08-25

## Open questions

- **ICH E6(R3)** adoption in 2025 and the ICH E9(R1) estimand addendum are stated from general reference knowledge and were not verified in this pass.
- **SPIRIT 2013 / 2025**, the Belmont Report (1979), the Common Rule 2018 revision, CIOMS 2016, FDAAA 2007 results-reporting requirements, and the NIH 2023 data-sharing policy were not independently verified here.
- **[ZA]** The National Health Act sections (71–73), the NDoH ethics guidelines edition (2nd, 2015) and NHREC's current registration requirements should be confirmed against the Department of Health.
- **[NA]** Namibian research authorisation and ethics review procedures are described generally; verify with the Ministry of Health and Social Services and UNAM.
- CRediT's 14 roles and grant success-rate ranges (10–25%) are stated from general knowledge, not verified.

