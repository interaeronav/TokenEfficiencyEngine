---
id: medical_field.ebm
title: Evidence-based medicine — study design, bias, statistics and appraisal
domain: 34_medical_field
tags: [evidence-based-medicine, rct, cohort, case-control, bias, confounding, randomisation, blinding, intention-to-treat, p-value, confidence-interval, nnt, hazard-ratio, meta-analysis, grade, consort, prisma, strobe, rob2, amstar, reproducibility, p-hacking]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Evidence-based medicine", url: "https://en.wikipedia.org/wiki/Evidence-based_medicine", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Number needed to treat", url: "https://en.wikipedia.org/wiki/Number_needed_to_treat", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "GRADE approach", url: "https://en.wikipedia.org/wiki/GRADE_approach", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Consolidated Standards of Reporting Trials (CONSORT)", url: "https://en.wikipedia.org/wiki/Consolidated_Standards_of_Reporting_Trials", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Replication crisis", url: "https://en.wikipedia.org/wiki/Replication_crisis", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Cochrane (organisation)", url: "https://en.wikipedia.org/wiki/Cochrane_(organisation)", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Semaglutide", url: "https://en.wikipedia.org/wiki/Semaglutide", publisher: "Wikipedia", accessed: 2026-08-25}
related: [medical_field.literature, medical_field.research_practice, medical_field.drug_development]
unit_system: SI
---

# Evidence-based medicine — study design, bias, statistics and appraisal

**Summary.** Evidence-based medicine is the discipline of deciding what to believe about a clinical intervention. It supplies a hierarchy of study designs, a taxonomy of the ways each design goes wrong, a statistical vocabulary for expressing effects and uncertainty, and a set of reporting and appraisal instruments for judging a published paper. This file covers all of it, with worked numerical examples for the effect measures, and closes with an honest account of the reproducibility problem, p-hacking, spin and industry funding — and a practical fifteen-minute reading protocol.

> ⚠️ The worked examples use illustrative numbers to demonstrate arithmetic. They are not clinical recommendations and must not be read as guidance about any treatment.

## Key facts

| Item | Detail |
|---|---|
| Term coined | Gordon Guyatt, 1991 editorial (after teaching it as "Scientific Medicine" from 1990); McMaster University |
| Canonical definition | Sackett et al., 1996: "the conscientious, explicit and judicious use of current best evidence in making decisions about the care of individual patients" |
| GRADE founded | 2000; four certainty levels (High, Moderate, Low, Very Low); adopted by **100+ organisations** including WHO and NICE |
| CONSORT 2010 | 25-item checklist + flow diagram; **600+ journals** endorse |
| CONSORT 2025 | Adds 7 items, modifies 3, removes 1; adds an open-science section |
| Cochrane founded | 1993, under Iain Chalmers; **53 review groups**, **37,000+ contributors**; refuses commercial funding |
| Amgen preclinical replication | **11%** of 53 landmark cancer studies confirmed (2012) |
| Bayer preclinical replication | 20–25% range reported |
| Reproducibility Project: Cancer Biology | 53 papers (2010–2012) targeted; replicated effect sizes averaged **85% smaller** than originals (2021) |
| Ioannidis | "Why Most Published Research Findings Are False", PLoS Medicine, 2005 |

---

## 1. The hierarchy of evidence, and its critiques

The classical pyramid, weakest to strongest:

1. Expert opinion, mechanistic reasoning, bench research
2. Case report → case series
3. Cross-sectional study
4. Case-control study
5. Cohort study
6. Randomised controlled trial
7. Systematic review and meta-analysis of RCTs

The USPSTF formalised a five-level version in 1989 with Level I reserved for properly designed RCTs.

**The critiques are substantial and are now part of standard teaching.**

- **The pyramid ranks designs, not studies.** A small, poorly concealed, badly analysed RCT is worse evidence than a large, well-controlled cohort study. GRADE exists precisely to replace design-ranking with an assessment of the *body* of evidence, which can start high and be downgraded, or start low and be upgraded.
- **Meta-analysis is not automatically the top.** A meta-analysis inherits every flaw of its inputs and adds its own (publication bias, inappropriate pooling of heterogeneous populations, double-counting). "Garbage in, garbage out" is the standard warning.
- **Some questions cannot be randomised.** Harms, rare outcomes, long latency, and anything where randomisation is unethical (parachutes, the famous *BMJ* Christmas satire; smoking; child abuse). Observational designs are not a lesser substitute here — they are the correct design.
- **External validity.** Trials recruit selected populations: younger, less comorbid, more adherent, disproportionately male and white in historical datasets. Applying a trial result to an 85-year-old with five other conditions and eleven medicines is an extrapolation, not a deduction. This is the strongest of the routine critiques of EBM.
- **Multimorbidity and guideline collision.** Single-disease guidelines, each internally evidence-based, interact badly when stacked on one patient.
- **Evidence lags and implementation gaps.** The often-quoted 17-year gap between research and practice is itself poorly evidenced but points at a real problem.
- **EBM as a rhetorical instrument.** Trisha Greenhalgh and colleagues' "evidence based medicine: a movement in crisis?" (*BMJ*, 2014) argued that the brand had been captured — by industry-driven trial agendas, by unmanageable guideline volume, and by rule-following that displaces clinical judgement. This is now taught alongside the pyramid rather than against it.

## 2. Study designs

### Randomised controlled trial (RCT)

Participants are allocated by chance to intervention or comparator. Randomisation's purpose is not fairness but **the elimination of confounding by both measured and unmeasured variables** in expectation — the only design that achieves the latter.

Variants: **parallel group** (the default), **crossover** (each participant receives both, useful for stable chronic conditions, vulnerable to carryover), **cluster-randomised** (randomising practices, wards or villages; requires analysis accounting for intracluster correlation), **factorial** (two interventions tested simultaneously in a 2×2), **stepped wedge** (all clusters eventually receive the intervention, in randomised order), and **pragmatic** versus **explanatory** trials (the PRECIS-2 continuum: does this work in routine practice, or can it work under ideal conditions?).

### Cohort study

A defined group is followed forward in time; exposure is measured before outcome. Prospective cohorts (Framingham, Nurses' Health Study, UK Biobank, the Whitehall studies) give incidence, relative risk, and temporality. Retrospective (historical) cohorts reconstruct the same structure from existing records — faster and cheaper, more exposed to record quality. Weaknesses: confounding, loss to follow-up, expense, and unsuitability for rare outcomes.

### Case-control study

Cases with the outcome and controls without are sampled, and prior exposure is compared. Efficient for **rare outcomes** and long latency (the design that established smoking and lung cancer, and thalidomide and phocomelia). Yields an **odds ratio**, not a risk ratio, because incidence cannot be computed. Highly vulnerable to **selection bias** in control choice and **recall bias** in exposure ascertainment. **Nested case-control** and **case-cohort** designs sample from within an existing cohort and inherit its better exposure data.

### Cross-sectional study

Exposure and outcome measured at the same moment. Gives **prevalence**, not incidence. Cannot establish temporality, which is why cross-sectional associations should never be described causally. The standard design for surveys and for diagnostic-accuracy studies.

### Case report and case series

No comparator. Value is in **signal generation**: the first reports of AIDS (1981), of thalidomide teratogenicity, of vaccine-associated rare events. A case series can never estimate an effect, and treating one as if it can is a recurring error in the surgical and complementary-medicine literature.

### Ecological studies

Units of analysis are populations, not people. Cheap and hypothesis-generating; subject to the **ecological fallacy** (an association at population level need not hold at individual level).

### n-of-1 trial

A single patient is randomised repeatedly between treatment and comparator (or placebo) in blinded, counterbalanced periods, with the outcome measured in each. Formally, this is the highest-validity design *for that individual*, and it is genuinely used for chronic stable conditions where the response is rapid, reversible and measurable. It generalises poorly by construction, though series of n-of-1 trials can be meta-analysed.

### Other designs worth naming

- **Diagnostic accuracy studies** — index test versus reference standard; reported as sensitivity, specificity, predictive values and likelihood ratios; reporting standard **STARD**.
- **Prognostic and prediction-model studies** — development and external validation; reporting standard **TRIPOD** (with **TRIPOD+AI** for machine-learning models).
- **Qualitative research** — interviews, focus groups, ethnography; answers "why" and "how it is experienced" questions that no trial can; reporting standards **COREQ** and **SRQR**.
- **Mendelian randomisation** — uses genetic variants as instrumental variables to approximate randomisation of a lifelong exposure. Powerful, and dependent on assumptions (relevance, independence, exclusion restriction) that are difficult to verify.
- **Target trial emulation** — the modern discipline for observational causal inference: specify the randomised trial you would have run, then emulate its protocol in observational data. This framework has substantially reduced errors like immortal time bias.

## 3. Bias — the taxonomy

**Bias is systematic error.** It does not shrink with sample size. That single sentence is the most important thing in this file: a bigger biased study is a more confidently wrong study.

### Selection bias

The groups compared differ in ways related to both exposure and outcome because of how they were selected or retained.

- **Sampling / referral bias** — hospital-based controls are not the source population.
- **Berkson's bias** — hospitalisation itself induces spurious associations between conditions.
- **Healthy worker effect** — employed cohorts are healthier than the general population.
- **Healthy user / adherer bias** — people who take a preventive drug (or a placebo, faithfully) differ systematically from those who do not. This is the most likely explanation for a large part of the observational hormone-replacement-therapy cardioprotection literature, which the WHI randomised trial then failed to confirm.
- **Attrition bias** — differential loss to follow-up.
- **Volunteer bias**, **collider stratification bias** (conditioning on a common effect of exposure and outcome creates association where none exists).

### Information (measurement) bias

- **Recall bias** — cases remember exposures differently from controls; endemic in case-control studies of birth defects, diet, and trauma.
- **Observer / ascertainment bias** — an unblinded assessor scores outcomes differently by group.
- **Detection bias** — one group is investigated more intensively, so more disease is found (a major issue in screening evaluation).
- **Misclassification** — **non-differential** misclassification of a binary exposure generally biases toward the null; **differential** misclassification can bias in either direction. Non-differential misclassification is not "safe" — it dilutes real effects and can make a true harm look absent.
- **Reporting / outcome-reporting bias** — outcomes measured but not reported because they were unfavourable.

### Confounding

A third variable associated with the exposure and independently a cause of the outcome, and not on the causal pathway. The classic: coffee drinking appears associated with lung cancer because smoking is associated with both. Handled by randomisation (in expectation), restriction, matching, stratification, multivariable regression, propensity scores, or instrumental variables — but **only for measured confounders**, which is the central limitation of all observational adjustment. **Residual confounding** is what remains after imperfect adjustment; **confounding by indication** is the special case where the reason a treatment was given is itself a predictor of outcome, and it is the dominant threat in pharmacoepidemiology.

### Immortal time bias

A period of follow-up during which, by the design's own logic, the outcome could not have occurred, misallocated to the treated group. Example: classifying patients as "treated" if they ever received a drug during follow-up, then counting time from cohort entry — a patient must survive long enough to receive the drug, so the treated group is guaranteed extra event-free time. It was the likely explanation for the notorious finding that Oscar winners live longer, and for a series of apparent survival benefits of statins, inhaled corticosteroids and transplantation that vanished under correct time-varying analysis. Avoided by time-varying exposure classification, landmark analysis, or target trial emulation.

### Lead-time and length-time bias (screening)

**Lead-time bias**: screening moves the diagnosis earlier, so survival *from diagnosis* lengthens even if the date of death is unchanged. **Length-time bias**: screening preferentially detects slow-growing, better-prognosis disease because it spends longer in the detectable preclinical phase. **Overdiagnosis** is the extreme of length-time bias — detection of disease that would never have caused symptoms. Together these mean **survival rates are not a valid endpoint for screening**; only disease-specific and all-cause mortality in a randomised comparison are.

### Publication and dissemination bias

Positive, novel and statistically significant results are more likely to be submitted, accepted, published in English, published faster, and cited more. The consequence is that the visible literature overstates effects. Detected (imperfectly) by funnel plot asymmetry and Egger's test; addressed by prospective trial registration, results-reporting mandates, and journals that accept **Registered Reports** (peer review of the protocol, with in-principle acceptance before results exist).

### Other named biases

Hawthorne effect (being observed changes behaviour), regression to the mean (extreme baseline values drift toward average without any treatment — the reason uncontrolled before-after studies are near-worthless), placebo and nocebo effects, and the **will-Rogers phenomenon** (stage migration improving apparent survival in every stage without helping anyone).

## 4. The machinery of a good trial

- **Sequence generation** — a genuinely random sequence (computer-generated, permuted blocks, stratified by centre or key prognostic factors, or minimisation).
- **Allocation concealment** — those recruiting cannot foresee the next assignment. This is *not* the same as blinding, it applies before randomisation, and it is the item most strongly and consistently associated with exaggerated effect estimates when absent. Achieved by central randomisation, pharmacy-controlled allocation, or sequentially numbered opaque sealed envelopes.
- **Blinding (masking)** — of participants, clinicians, outcome assessors, data analysts. "Double-blind" is ambiguous and CONSORT asks authors to say *who* was blinded. Subjective outcomes are far more sensitive to blinding than hard ones; all-cause mortality is nearly immune.
- **Comparator choice** — placebo, active control, or usual care. A trial against an inadequate dose of a comparator, or against an outdated standard, can be technically valid and clinically meaningless. This is one of the commonest forms of legitimate-looking distortion.
- **Outcome definition** — a single pre-specified primary outcome, with a hierarchy for secondary outcomes and a plan for multiplicity. **Composite outcomes** (e.g. "MACE": cardiovascular death, MI, stroke) increase power but must be interpreted by component: a composite driven entirely by its least serious element (revascularisation, hospitalisation) is weak evidence.
- **Surrogate endpoints** — a biomarker substituting for an outcome that matters (LDL cholesterol for cardiovascular events, HbA1c for diabetic complications, tumour response or progression-free survival for overall survival, CD4 count for AIDS). Valid surrogacy requires that the treatment's effect on the surrogate *predicts* its effect on the outcome, which is often false. CAST (1989) is the canonical disaster: antiarrhythmic drugs suppressed ventricular ectopy, the surrogate, and **increased** mortality. See `07` on accelerated approval.
- **Intention-to-treat (ITT) versus per-protocol** — ITT analyses everyone in the group to which they were randomised regardless of what they received. It preserves the randomisation and therefore the causal claim, and it estimates the effect of *offering* the treatment. Per-protocol restricts to those who complied, which reintroduces confounding (compliers differ) and generally *exaggerates* efficacy. Standard practice: ITT primary for superiority; both ITT and per-protocol for **non-inferiority**, because in a non-inferiority trial sloppiness pushes results toward "no difference" and thus toward the desired conclusion. **Modified ITT** ("mITT") is a warning sign — the modification must be pre-specified and justified, and it is often neither.
- **Sample size and power** — the calculation requires a pre-specified minimum clinically important difference, an expected event rate, α (usually 0.05, two-sided), and power (usually 80% or 90%). Underpowered trials do not merely fail to detect real effects; when they *do* reach significance, the effect estimate is inflated (the "winner's curse", a consequence of low power plus a significance filter).
- **Interim analysis and stopping rules** — pre-specified group-sequential boundaries (O'Brien–Fleming, Pocock) with alpha spending, overseen by an independent Data and Safety Monitoring Board. **Trials stopped early for benefit systematically overestimate the effect**, and the practice is a documented source of exaggeration.
- **Registration and protocol publication** — prospective registration (ClinicalTrials.gov, ISRCTN, the WHO ICTRP, the **[ZA]** South African National Clinical Trial Register) plus a published protocol and statistical analysis plan is now the minimum for credibility; the ICMJE has required prospective registration as a condition of publication since 2005.

## 5. Statistics a reader must be able to use

### p-values — what they are and the seven ways they are misread

A p-value is **the probability of observing data at least as extreme as those obtained, if the null hypothesis and all other model assumptions were true.** The routine misinterpretations, most of them named in the American Statistical Association's 2016 statement on p-values:

1. It is **not** the probability that the null hypothesis is true.
2. It is **not** the probability that the result occurred by chance.
3. p > 0.05 does **not** mean "no effect" — absence of evidence is not evidence of absence.
4. p = 0.049 and p = 0.051 are not different in kind; the 0.05 threshold is a convention Fisher offered casually.
5. A p-value says nothing about **effect size** or clinical importance. With a large enough sample, a trivial difference is "significant".
6. It does not measure the size or the importance of an effect, nor the quality of the study.
7. Multiple comparisons inflate false positives: twenty independent tests at α = 0.05 give roughly a 64% chance of at least one "significant" result under the null (1 − 0.95²⁰).

### Confidence intervals

A 95% confidence interval is the range of parameter values not rejected at α = 0.05; the coverage claim is about the **procedure** — 95% of intervals constructed this way over repeated sampling contain the true value — not about the specific interval in front of you. Practically, a CI is more informative than a p-value because it shows both the estimate and its precision, and lets the reader ask the right question: **"is the whole interval clinically unimportant, or does it include effects I would care about?"** A wide interval crossing the null is an *uninformative* trial, not a *negative* one.

### The other essentials

- **Absolute versus relative** measures (below).
- **Survival analysis** — Kaplan–Meier curves, the log-rank test, the Cox proportional hazards model and its proportional-hazards assumption (check it; if hazards cross, the hazard ratio is close to meaningless).
- **Regression** — linear, logistic, Poisson; the distinction between adjustment for confounding and overfitting; the rule of thumb of ~10 events per variable in logistic models (itself now contested).
- **Missing data** — MCAR, MAR, MNAR; complete-case analysis versus multiple imputation; last-observation-carried-forward is obsolete and biased.
- **Multiplicity control** — Bonferroni, Holm, false discovery rate (Benjamini–Hochberg) for genomics-scale testing.
- **Subgroup analyses** — pre-specified, limited in number, tested by an **interaction test** rather than by significance within subgroups. The ISIS-2 astrological subgroup (aspirin appeared not to work in Gemini and Libra) is the standard teaching example of why.
- **Bayesian methods** — prior, likelihood, posterior; increasingly used in adaptive and platform trials, where they answer the question clinicians actually ask ("what is the probability this treatment is better?").

## 6. Effect measures, with worked calculations

Take a two-arm trial. **Control arm:** 200 patients, 40 events. **Treatment arm:** 200 patients, 20 events.

| Quantity | Formula | Calculation | Result |
|---|---|---|---|
| Control event rate (CER) | events ÷ n | 40/200 | **0.20 (20%)** |
| Experimental event rate (EER) | events ÷ n | 20/200 | **0.10 (10%)** |
| **Relative risk (RR)** | EER ÷ CER | 0.10 / 0.20 | **0.50** |
| **Relative risk reduction (RRR)** | 1 − RR | 1 − 0.50 | **0.50 (50%)** |
| **Absolute risk reduction (ARR)** | CER − EER | 0.20 − 0.10 | **0.10 (10 percentage points)** |
| **Number needed to treat (NNT)** | 1 ÷ ARR | 1 / 0.10 | **10** |
| **Odds (control)** | events ÷ non-events | 40/160 | 0.25 |
| **Odds (treatment)** | events ÷ non-events | 20/180 | 0.111 |
| **Odds ratio (OR)** | odds_t ÷ odds_c | 0.111 / 0.25 | **0.444** |

Read: treating 10 patients with this intervention prevents one event, over the trial's duration.

**Now the same relative effect at a low baseline risk.** Control 1,000 patients, 10 events (CER = 0.01); treatment 1,000 patients, 5 events (EER = 0.005).

- RR = 0.005/0.01 = **0.50** — identical relative effect.
- ARR = 0.01 − 0.005 = **0.005**.
- NNT = 1/0.005 = **200**.

**This is the single most important arithmetic in clinical medicine.** "Halves your risk" is the same sentence for an NNT of 10 and an NNT of 200. Relative measures are portable across baseline risks and are what trials report; absolute measures are what patients experience and are what a decision requires. A press release quoting only a relative reduction is, by default, a misleading press release.

**A verified real example.** In the SELECT trial (semaglutide, 17,604 participants, follow-up around 48 months), major adverse cardiovascular events occurred in **6.5%** on semaglutide versus **8.0%** on placebo.
- ARR = 8.0% − 6.5% = **1.5 percentage points**
- RR = 6.5/8.0 = 0.8125, so **RRR ≈ 18.8%** (as reported)
- NNT = 1/0.015 ≈ **67** over ~4 years

A second verified example, from the NNT literature: in ASCOT-LLA, atorvastatin produced a **36% relative** reduction in cardiovascular events but an **absolute** risk reduction of **1.02%**, giving an **NNT of about 98 over 3.3 years**.

**Odds ratio versus risk ratio.** The OR always lies further from 1 than the RR. When the outcome is rare (say <10%), OR ≈ RR and the approximation is harmless. When the outcome is common, the OR badly exaggerates: with CER 50% and EER 25%, RR = 0.5 but OR = (0.25/0.75)/(0.50/0.50) = 0.33. Case-control studies and logistic regression produce ORs by construction, so this misreading is extremely common in the literature and in the press.

**Harms.** The same arithmetic with harmful outcomes gives **absolute risk increase (ARI)** and **number needed to harm (NNH)**. A responsible summary of any intervention states NNT and NNH together over the same time horizon.

**Hazard ratio (HR).** The ratio of instantaneous event rates over time, from a Cox model. It is not a risk ratio and it is not a ratio of median survivals. It assumes proportional hazards; if the Kaplan–Meier curves cross or separate late (common with immunotherapies and with vaccines), the single HR conceals more than it reveals, and restricted mean survival time (RMST) is the better summary.

**Limits of NNT.** It has no natural confidence interval when the ARR interval crosses zero (the CI becomes two disjoint infinite ranges), it is time-dependent (an NNT without a time horizon is meaningless), it assumes a form of monotonic benefit across individuals, and it can conflict with survival-analysis summaries.

## 7. Non-inferiority and equivalence trials

A non-inferiority trial asks whether a new treatment is *not worse than* an active comparator by more than a pre-specified **margin (Δ)**, usually because the new treatment has some other advantage (oral rather than injected, cheaper, safer, shorter).

Critical points:
- The **margin must be justified** clinically and statistically, ideally as a fraction (commonly 50%) of the comparator's own established effect versus placebo. An over-generous margin can make an inferior drug look acceptable, and margin justification is the item most often absent.
- **Assay sensitivity** must be plausible: the comparator must actually work in this population, or "no difference" is uninformative.
- **Sloppiness biases toward the null and therefore toward the desired conclusion** — non-adherence, crossover and measurement error all help a non-inferiority claim. This inverts the usual incentive structure and is why both ITT and per-protocol analyses are required.
- Interpretation is by **confidence interval versus margin**, not by a p-value: the entire CI must lie on the acceptable side of Δ.
- **CONSORT has a non-inferiority extension.** Use it as the checklist.

## 8. Systematic review and meta-analysis

A systematic review is a study whose unit of analysis is other studies. Its method:

1. **Pre-registered protocol** (PROSPERO for health reviews).
2. **Explicit question** in PICO form (see `08`).
3. **Comprehensive search** — at minimum MEDLINE/PubMed, Embase, CENTRAL, plus trial registries, grey literature, reference lists and forward citation searching, with the full search strategy published.
4. **Duplicate screening and data extraction**, with disagreement resolution.
5. **Risk-of-bias assessment** of every included study.
6. **Synthesis** — quantitative pooling if appropriate, narrative or structured synthesis (SWiM) if not.
7. **Assessment of certainty**, usually GRADE.

**Meta-analysis** pools effect estimates. Fixed-effect models assume one true effect and weight by inverse variance; random-effects models (DerSimonian–Laird, or the better-behaved Hartung–Knapp–Sidik–Jonkman) assume a distribution of true effects and give small studies relatively more weight — which is a liability if small studies are biased. **Network meta-analysis** compares three or more interventions using indirect evidence, and depends on a transitivity assumption that must be argued, not assumed.

**Heterogeneity.** Cochran's Q tests it (underpowered with few studies); **τ²** estimates the between-study variance; **I²** expresses the percentage of total variability attributable to heterogeneity rather than chance. Conventional rough bands: 0–40% may be unimportant, 30–60% moderate, 50–90% substantial, 75–100% considerable. Two warnings that the bands invite people to forget: **I² is not an absolute measure** — it depends on the precision of the included studies, so large precise trials can produce a high I² for a clinically trivial spread — and **a low I² does not license pooling of clinically incomparable studies**. A **prediction interval** is the more honest summary of a random-effects meta-analysis than the confidence interval around the pooled mean.

**Small-study effects** are examined with funnel plots and Egger's regression, both weak with fewer than ~10 studies, and both capable of reflecting genuine heterogeneity rather than publication bias.

## 9. GRADE

**GRADE** (Grading of Recommendations Assessment, Development and Evaluation), established **2000**, separates two judgements that older systems conflated: **certainty of evidence** and **strength of recommendation**.

Certainty is rated per outcome as **High, Moderate, Low or Very Low**. Randomised evidence starts High; observational evidence starts Low.

**Five domains that downgrade:**
1. **Risk of bias** in the included studies.
2. **Inconsistency** — unexplained heterogeneity.
3. **Indirectness** — different population, intervention, comparator or outcome than the question.
4. **Imprecision** — wide confidence intervals, few events, failure to meet optimal information size.
5. **Publication bias** — suspected small-study effects.

**Three domains that upgrade** (observational evidence only):
1. Large magnitude of effect.
2. Dose–response gradient.
3. All plausible residual confounding would work against the observed effect.

Recommendations are **strong** ("we recommend") or **conditional/weak** ("we suggest"), and the strength depends not only on certainty but on the balance of benefits and harms, values and preferences, resource use, equity, acceptability and feasibility — formalised in the **Evidence-to-Decision (EtD)** framework. Crucially, **high certainty does not compel a strong recommendation, and low certainty does not forbid one**: a strong recommendation can rest on low-certainty evidence when the alternative is catastrophic. GRADE has been adopted by more than **100 organisations**, including the WHO and NICE.

## 10. The appraisal toolkit

| Tool | Applies to | What it is |
|---|---|---|
| **CONSORT** | Reporting of RCTs | 25-item checklist plus flow diagram (2010); the **2025 update** adds 7 items, modifies 3, removes 1, and adds an open-science section covering registration, protocol access, data sharing and disclosures. Endorsed by 600+ journals including *The Lancet* and *BMJ*. Extensions exist for cluster, non-inferiority, pragmatic, factorial, harms, abstracts, herbal and non-pharmacological interventions, plus **TIDieR** for describing the intervention well enough to replicate it. |
| **SPIRIT** | Trial **protocols** | The protocol counterpart of CONSORT. |
| **PRISMA** | Reporting of systematic reviews | 2009 statement, substantially revised as **PRISMA 2020**; 27-item checklist plus the flow diagram everyone recognises. Extensions for abstracts, protocols (PRISMA-P), network meta-analysis, scoping reviews, individual participant data, and searching (PRISMA-S). |
| **STROBE** | Reporting of observational studies | 22 items covering cohort, case-control and cross-sectional designs; **STROBE-MR** for Mendelian randomisation; **RECORD** for routinely collected health data. |
| **Cochrane RoB 2** | Risk of bias in **randomised** trials | Five domains — randomisation process; deviations from intended interventions; missing outcome data; measurement of the outcome; selection of the reported result — each rated Low / Some concerns / High, with signalling questions, producing an overall domain-driven judgement. Replaced the older domain-plus-summary tool. |
| **ROBINS-I** | Risk of bias in **non-randomised** studies of interventions | Judges observational studies against a hypothetical target trial; adds pre-intervention confounding and selection domains, with a "Critical" category above High. **ROBINS-E** is the exposure analogue. |
| **AMSTAR 2** | Quality of **systematic reviews** | 16 items, 7 of them "critical" (protocol registered before the review, adequacy of the literature search, justification for excluding studies, risk-of-bias assessment, appropriateness of meta-analytic methods, consideration of risk of bias when interpreting, assessment of publication bias). Produces a confidence rating: High, Moderate, Low or Critically Low. Most published reviews rate Low or Critically Low. |
| **QUADAS-2** | Diagnostic accuracy studies | Patient selection, index test, reference standard, flow and timing. |
| **PROBAST** | Prediction-model studies | Risk of bias and applicability. |
| **GRADE** | Bodies of evidence and recommendations | See above. |
| **EQUATOR Network** | All of the above | equator-network.org indexes every reporting guideline; the correct first stop when writing or appraising anything. |
| **CASP checklists** | Teaching | Critical Appraisal Skills Programme; simple free checklists per design, the usual undergraduate teaching instrument. |

## 11. Reproducibility, p-hacking, spin and money

### The reproducibility problem

- **Preclinical.** Amgen scientists reported being able to confirm only **11% (6 of 53)** of landmark preclinical oncology studies (2012); Bayer reported replication rates in the **20–25%** range. These are the two most-cited numbers in the field, and both come from industry attempts to build on published academic work.
- **The Reproducibility Project: Cancer Biology** (2021) targeted 53 high-impact cancer papers published 2010–2012. Among the experiments with enough information to replicate, **effect sizes averaged 85% smaller** than the originals. A large fraction of the original papers did not contain enough methodological detail to attempt replication at all, and many original authors declined to share protocols or reagents — a finding as damning as the replication rate itself.
- **Ioannidis (2005)**, "Why Most Published Research Findings Are False", gave the formal argument: with low prior probability of the tested hypothesis, small studies, small effects, flexible designs and analytic choices, financial interest and competitive fields, the **positive predictive value of a "significant" finding** can fall below 50%.
- Surveys find roughly half of cancer researchers report having been unable to reproduce a published result.

### Questionable research practices

- **p-hacking** — trying analyses until one crosses 0.05: adding or dropping covariates, excluding outliers post hoc, choosing among multiple outcome scales, optional stopping (peeking at the data and continuing until significance), splitting or merging subgroups.
- **HARKing** — Hypothesising After the Results are Known: presenting a post-hoc finding as if it had been predicted.
- **Outcome switching** — changing the primary outcome between registration and publication. The COMPare project documented this at scale in high-impact journals and found substantial resistance from journals when discrepancies were reported.
- **Selective reporting** of favourable subgroups, timepoints or analyses.
- **Salami slicing** and duplicate publication, which inflate apparent evidence and corrupt meta-analyses.

### Spin

Spin is reporting that distorts interpretation without falsifying data: emphasising a statistically significant secondary outcome when the primary was null; using causal language for observational associations; reporting only relative effects; concluding "well tolerated" from an underpowered safety analysis; a conclusion in the abstract that the results do not support. Studies of abstracts of trials with non-significant primary outcomes find spin in a large majority. **Read the results, not the conclusions** is the direct practical response.

### Industry funding

Cochrane methodology reviews have repeatedly found that **industry-sponsored studies more often reach conclusions favourable to the sponsor** than independently funded studies of the same question, and that this is only partly explained by conventional risk-of-bias items. The mechanisms are structural rather than fraudulent: choice of comparator and dose, choice of population, choice of outcome, publication decisions, ghost- and guest-authorship, and control of the data. Mitigations: mandatory registration and results posting, data-sharing requirements, independent statistical analysis, and full conflict-of-interest disclosure — none of which is fully effective, and all of which are better than nothing.

### Remedies with evidence behind them

Pre-registration; **Registered Reports** (in-principle acceptance based on the protocol, now offered by 140+ journals in psychology and a growing number in medicine); results-blind review; data and code sharing; multi-laboratory replication consortia; reporting guidelines and their enforcement; and larger, simpler, more collaborative trials.

## 12. How to read a paper in fifteen minutes

A working protocol. The order matters — it is designed so that you can stop early.

1. **Minute 1 — the question and the design.** Read only the title and the methods' first sentence. What is the PICO, and what design? If the design cannot answer the question, stop.
2. **Minutes 2–3 — the registration and the protocol.** Is there a registration number? Was it registered *before* recruitment? Does the registered primary outcome match the reported primary outcome? A mismatch here is the highest-yield 90 seconds in the whole exercise.
3. **Minute 4 — the population.** Table 1, plus the inclusion and exclusion criteria. Would your patient have been eligible? Look at age, sex, comorbidity, ethnicity, and country.
4. **Minutes 5–6 — the comparator and the outcome.** Was the control arm a fair test? Is the primary outcome one that matters to a patient, a surrogate, or a composite? If a composite, which component drove it?
5. **Minutes 7–8 — bias.** Randomised: was allocation concealed, who was blinded, how much loss to follow-up, was analysis ITT? Observational: what confounders were adjusted for, and which obvious ones were not? Any immortal time?
6. **Minutes 9–11 — the numbers.** Go to the primary results table, not the abstract. Extract the event rates in both arms and compute ARR and NNT yourself. Look at the confidence interval and ask whether both ends are clinically acceptable. Check whether the reported effect is relative-only.
7. **Minute 12 — harms.** Find the adverse events table. Was harm measured actively or passively? Compute NNH if you can.
8. **Minutes 13–14 — funding, conflicts and role of the sponsor.** Who paid, who wrote it, who held the data, who had the right to publish.
9. **Minute 15 — the conclusion versus the results.** Read the abstract's conclusion last, and ask whether the data you just looked at support it. If it overreaches, that tells you something about everything else in the paper.

If you have thirty seconds rather than fifteen minutes: **read the primary outcome result with its confidence interval, and the funding statement.** Those two items discriminate better than anything else of comparable length.

## Sources

- [Evidence-based medicine](https://en.wikipedia.org/wiki/Evidence-based_medicine) — Wikipedia, accessed 2026-08-25
- [Number needed to treat](https://en.wikipedia.org/wiki/Number_needed_to_treat) — Wikipedia, accessed 2026-08-25
- [GRADE approach](https://en.wikipedia.org/wiki/GRADE_approach) — Wikipedia, accessed 2026-08-25
- [Consolidated Standards of Reporting Trials](https://en.wikipedia.org/wiki/Consolidated_Standards_of_Reporting_Trials) — Wikipedia, accessed 2026-08-25
- [Replication crisis](https://en.wikipedia.org/wiki/Replication_crisis) — Wikipedia, accessed 2026-08-25
- [Cochrane (organisation)](https://en.wikipedia.org/wiki/Cochrane_(organisation)) — Wikipedia, accessed 2026-08-25
- [Semaglutide](https://en.wikipedia.org/wiki/Semaglutide) — Wikipedia, accessed 2026-08-25

## Open questions

- **PRISMA 2020** item count (27) and the description of its extensions are stated from general reference knowledge; the Wikipedia article was unfetchable in this pass. Verify at prisma-statement.org.
- **AMSTAR 2** (16 items, 7 critical), **RoB 2** domain list and **ROBINS-I** were not verified against primary sources here; check the Cochrane Methods and AMSTAR sites.
- The ASA 2016 statement on p-values, Greenhalgh's 2014 *BMJ* "EBM in crisis" paper, the COMPare project and the Cochrane methodology review on industry sponsorship are named from general reference knowledge and were not retrieved in this pass — verify before citing.
- The I² interpretive bands (0–40 / 30–60 / 50–90 / 75–100) come from the Cochrane Handbook; verify the current wording, which is deliberately hedged in the source.
- The ASCOT-LLA and SELECT figures are as reported by the secondary sources cited; check the primary papers (*Lancet* 2003 and *NEJM* 2023 respectively) before quoting.

