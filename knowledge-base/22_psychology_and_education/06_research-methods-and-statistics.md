---
id: psych.research_methods
title: Research methods and statistics — the methods training
domain: 22_psychology_and_education
tags: [research-methods, experimental-design, quasi-experimental, longitudinal, sampling, thematic-analysis, ipa, grounded-theory, discourse-analysis, mixed-methods, anova, regression, factor-analysis, effect-size, power, meta-analysis, replication-crisis, open-science, preregistration, spss, r, jamovi, jasp, nvivo]
jurisdiction: global
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Replication crisis", url: "https://en.wikipedia.org/wiki/Replication_crisis", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Item response theory", url: "https://en.wikipedia.org/wiki/Item_response_theory", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Crossref metadata for methodological sources", url: "https://api.crossref.org/works", publisher: "Crossref", accessed: 2026-08-25}
  - {title: "Open Library search API — bibliographic verification of methods texts", url: "https://openlibrary.org/search.json", publisher: "Internet Archive / Open Library", accessed: 2026-08-25}
related: [psych.undergraduate_curriculum, psych.assessment_psychometrics, psych.how_psychologists_think, psych.reading_list]
---

# Research methods and statistics — the methods training

**Summary.** Psychology's methods training is unusually thorough for a social science, and it is the transferable core of the degree. It is also the part of the discipline that has changed most in the last fifteen years: the replication crisis moved the field from a null-hypothesis-significance-testing culture toward effect sizes, estimation, power, preregistration and open data. A graduate trained before about 2012 and one trained after have measurably different default habits. This file sets out what the training covers now.

## Key facts

| Quantity | Convention | Caution |
|---|---|---|
| α (Type I error) | .05 | Arbitrary; a threshold, not a measure of evidence |
| Power (1 − β) | .80 conventional target | Median power in published psychology has historically been far below this |
| Cohen's *d* | .2 small, .5 medium, .8 large | Cohen himself called these arbitrary and context-free |
| *r* | .1 / .3 / .5 | Same caveat |
| η²ₚ (partial eta squared) | Reported for ANOVA | Inflates relative to η²; not comparable across designs |
| Confidence interval | 95% | Does not mean "95% probability the parameter is in this interval" |
| Reproducibility of psychological findings | ~36% of 100 studies produced statistically significant replications (OSC 2015) | Effect sizes about half the originals |

> ⚠️ A *p*-value is the probability of data at least this extreme *given the null hypothesis is true*. It is not the probability the null is true, not the probability the finding will replicate, and not a measure of effect size or importance. Nearly every misuse of statistics in applied psychology traces back to forgetting this sentence.

---

## 1. Experimental and quasi-experimental design

**True experiment.** Random assignment to conditions plus manipulation of the independent variable plus control of extraneous variables. Random assignment is what buys causal inference; nothing else does it as cheaply.

Designs: between-subjects (independent groups), within-subjects/repeated measures (each participant in every condition — more powerful, fewer participants, but carries order and carryover effects, addressed by counterbalancing or Latin squares), matched-pairs, factorial (2×2, 2×3 and larger — the point of which is the **interaction**, which is usually the interesting result), and mixed designs with both between and within factors.

**Threats to internal validity** (Campbell and Stanley's list, still the working checklist): history, maturation, testing, instrumentation, **statistical regression to the mean**, selection, mortality/attrition, selection–maturation interactions, and diffusion of treatment. Regression to the mean deserves special emphasis for educational psychologists because it is the mechanism that makes almost any intervention selected on the basis of extreme baseline scores appear to work.

**External and ecological validity.** Whether the effect generalises across people, settings, times and operationalisations. The **WEIRD problem** — that the participant base of psychology is overwhelmingly Western, Educated, Industrialised, Rich and Democratic undergraduates — bears directly on southern African practice, since most of what is in the textbooks was established on samples unlike the local population.

**Quasi-experimental designs** are used where random assignment is impossible, which in schools is most of the time:
- Non-equivalent control group with pre- and post-test — the workhorse; vulnerable to selection.
- Interrupted time series — repeated observations before and after an intervention; strong when there are enough pre-intervention points to establish a trend.
- Regression discontinuity — assignment on a cut-off score; strong causal inference near the threshold, and a natural fit for programmes with eligibility cut-offs.
- Difference-in-differences — comparing change in a treated and untreated group.
- **Single-case experimental designs** — ABAB reversal, multiple baseline across participants/settings/behaviours, changing criterion, alternating treatments. These deserve more prominence than they usually get: they are the appropriate methodology for individual intervention evaluation in schools, they generate real causal evidence with n = 1, and they are exactly what an educational psychologist can actually run.

---

## 2. Correlational and longitudinal designs

Correlational designs measure without manipulating. They answer "do these covary?" and never, on their own, "does this cause that?" Third variables and reverse causation must be addressed by design (measured confounders, instrumental variables, longitudinal ordering) or acknowledged.

**Longitudinal designs.** Panel studies, cohort studies, accelerated longitudinal designs. The characteristic problems: attrition that is not random (the highest-risk participants leave first, biasing everything), practice effects on repeated testing, cohort effects confounded with age in cross-sectional comparison, and the sheer expense. Cross-lagged panel models are the standard analysis for reciprocal effects; the classic cross-lagged panel model has been substantially criticised in favour of random-intercept cross-lagged panel models that separate within-person from between-person variance.

---

## 3. Sampling

**Probability sampling** — simple random, systematic, stratified (which reduces sampling error when the strata relate to the outcome), cluster (which is what schools force on you, and which requires accounting for the design effect and intra-class correlation), and multistage.

**Non-probability sampling** — convenience (dominant in practice), purposive, quota, snowball (essential for hidden populations), and theoretical sampling in grounded theory.

**Sample size** is a power question for quantitative work (§7) and a saturation question for qualitative work. "Saturation" is itself contested: it is often asserted rather than demonstrated, and the more defensible current practice is to specify **information power** in advance and to state what was done.

---

## 4. Qualitative methods

Psychology's qualitative training is genuinely methodological, not a soft option, and the distinctions between approaches are substantive rather than stylistic.

**Thematic analysis (Braun and Clarke).** The most widely used, and the most widely misused. Their six phases — familiarisation, generating initial codes, searching for themes, reviewing themes, defining and naming themes, producing the report — are frequently reported as if TA were a single method. It is not: Braun and Clarke distinguish **reflexive TA** (themes are analytic outputs developed by an engaged researcher; no codebook, no inter-rater reliability, and calculating a kappa is a category error within this approach) from **codebook** and **coding-reliability** variants. The researcher must state which, and must state the theoretical position: inductive or deductive, semantic or latent, essentialist/realist or constructionist. Their *Thematic Analysis: A Practical Guide* (2021) is the current reference.

**Interpretative Phenomenological Analysis (IPA).** Jonathan Smith and colleagues. Phenomenological, hermeneutic and idiographic. Small, homogeneous, purposively selected samples (often 3–10); detailed case-by-case analysis before cross-case pattern-finding; the double hermeneutic — the researcher making sense of the participant making sense of their experience. Suited to questions about lived experience of a significant event or condition. Not suited to broad questions or heterogeneous samples.

**Grounded theory.** Glaser and Strauss originally; then the divergence between Glaser's classic version, Strauss and Corbin's more procedural version, and **Charmaz's constructivist grounded theory**, which is the version most used in psychology now. Constant comparison, open/axial/selective (or initial/focused/theoretical) coding, memo-writing, theoretical sampling, theoretical saturation. The output is a theory grounded in the data, not a set of themes — a distinction routinely violated in published work that calls itself grounded theory and is actually thematic analysis.

**Discourse analysis.** Two broad traditions: **discursive psychology** (Potter and Wetherell) analysing how psychological matters are constructed and used in talk to perform social actions, and **Foucauldian discourse analysis** analysing how discourses constitute subjects and objects and how they operate with power. Both treat language as constitutive rather than as a window onto an inner state — which is a genuinely different ontology from thematic analysis and cannot be mixed casually with it.

**Other approaches** in the training: narrative analysis, conversation analysis, ethnography, case study, participatory action research (with a strong tradition in South African community psychology), and photovoice.

**Quality criteria for qualitative work** are not reliability and validity in the psychometric sense. Lincoln and Guba's credibility, transferability, dependability and confirmability; Yardley's sensitivity to context, commitment and rigour, transparency and coherence, and impact and importance; and the practices — reflexivity statements, audit trails, thick description, negative case analysis, and (used carefully, and rejected outright within reflexive TA) member checking and triangulation.

---

## 5. Mixed methods

**Designs** (Creswell's typology is the standard teaching reference): convergent parallel (both strands concurrently, merged at interpretation), explanatory sequential (quantitative first, qualitative to explain it), exploratory sequential (qualitative first, to build an instrument or hypothesis, then quantitative), and embedded designs. **Notation**: QUAN → qual, QUAL + quan, capitalisation indicating priority.

The recurring problem is that most published "mixed methods" work is two studies stapled together with no genuine integration. Integration happens through **connecting** (results of one strand determine sampling for the other), **building** (one strand builds the instrument for the other), **merging** (joint displays comparing strands) or **embedding**. A joint display table is the cheapest way to demonstrate that integration actually occurred. Note also the epistemological problem: mixing a positivist strand with a social-constructionist strand requires a stated pragmatist or critical-realist position, not silence.

---

## 6. Descriptive and inferential statistics

**Descriptives.** Central tendency (mean, median, mode — and when the median is the honest choice), dispersion (range, IQR, variance, SD), shape (skewness, kurtosis), and — most importantly — **plotting the data before testing it**. Anscombe's quartet and the datasaurus dozen exist precisely because summary statistics conceal structure. Boxplots, violin plots, scatterplots with fitted lines, and raincloud plots for group comparisons; bar charts of means with standard errors hide the distribution and should generally be replaced.

**The inferential toolkit taught to psychologists:**

| Test | Use | Key assumptions |
|---|---|---|
| One-sample / independent / paired *t*-test | Compare one or two means | Normality of sampling distribution, homogeneity of variance (Welch's *t* relaxes this and should arguably be the default), independence |
| One-way ANOVA | 3+ group means | As above; follow with planned contrasts (preferred) or post-hoc tests with correction |
| Factorial ANOVA | Multiple factors and their interactions | As above; interpret interactions before main effects |
| Repeated-measures ANOVA | Within-subject factors | Sphericity (Mauchly's test; Greenhouse-Geisser or Huynh-Feldt correction); mixed/multilevel models are usually better |
| ANCOVA | Adjust for a covariate | Homogeneity of regression slopes; does **not** rescue non-random assignment (Lord's paradox) |
| Chi-square | Categorical association | Expected cell counts ≥5; Fisher's exact for small tables |
| Correlation (Pearson, Spearman) | Linear/monotonic association | Linearity, no influential outliers; range restriction attenuates |
| Multiple regression | Predict a continuous outcome from several predictors | Linearity, independence of errors, homoscedasticity, normal residuals, no severe multicollinearity (check VIF) |
| Logistic regression | Binary outcome | Log-odds linearity, adequate events per predictor |
| Multilevel / mixed models | Nested data (learners in classes in schools) | The correct default for school data; ignoring clustering inflates Type I error badly |
| Mediation / moderation | Process and boundary conditions | Bootstrapped indirect effects (PROCESS, lavaan); mediation from cross-sectional data is weak inference and should be stated as such |
| SEM / CFA | Latent variable models | Large N; fit indices (CFI, TLI, RMSEA, SRMR) with the cut-offs treated as guidance, not law |

**Factor analysis** deserves separate treatment because it is the backbone of psychometrics (file `04`). **Exploratory factor analysis** — decide extraction (principal axis factoring or maximum likelihood; note that principal components analysis is a data-reduction technique, not a factor model, and the two are constantly conflated), decide how many factors (parallel analysis is the best-supported method; the Kaiser eigenvalue > 1 rule is known to over-extract and should not be used alone; scree plots are subjective), and decide rotation (oblique — promax, oblimin — is almost always right in psychology because psychological factors correlate; varimax orthogonal rotation is usually an unjustified assumption). **Confirmatory factor analysis** tests a specified structure and is what you use for measurement-invariance testing across language and cultural groups — the technically correct way to ask whether an instrument means the same thing in two populations, and directly relevant to the test-bias material in file `04`.

---

## 7. Effect sizes, power and estimation

**Effect sizes.** Standardised mean differences (Cohen's *d*, Hedges' *g* which corrects small-sample bias, Glass's Δ), correlation family (*r*, *R*², η², partial η², ω² which is less biased), odds ratios and risk ratios, and — for practical educational work — **unstandardised** effects in the units people care about (words per minute, marks, days absent), which are often more useful than any standardised index.

Report an effect size with a **confidence interval** for every primary analysis. Cohen's benchmarks (.2/.5/.8) were offered as a last resort in the absence of context and have hardened into an unjustified convention; the right comparison is to the distribution of effects in the relevant literature, and in education a *d* of .2 delivered cheaply at scale can matter more than a *d* of .8 in a laboratory.

**Power analysis.** Compute the required N **before** collecting data, from the smallest effect size of interest (not from the effect a previous underpowered study happened to report, which is inflated by publication bias). G*Power, the `pwr` package in R, and simulation-based power analysis for complex designs. Post-hoc "observed power" computed from the obtained effect is uninformative and should not be reported.

**Meta-analysis.** Systematic search with a preregistered protocol (PRISMA reporting), coding and effect-size extraction, fixed-effect versus random-effects models (random effects is nearly always the honest choice in psychology), heterogeneity (*Q*, *I*²) and its exploration by moderator analysis and meta-regression, publication-bias assessment (funnel plots, Egger's test, trim-and-fill, *p*-curve, PET-PEESE, selection models — all imperfect, and none of which rescues a biased literature). Multilevel meta-analysis for dependent effect sizes. Meta-analysis inherits the quality of its inputs: a meta-analysis of underpowered, *p*-hacked studies produces a precisely estimated wrong number, which is exactly what happened in several of the literatures discussed in file `03`.

---

## 8. The replication crisis and open science

**What happened.** A convergence of events from around 2011: a high-profile fraud case; the publication of an implausible pre-cognition result using standard methods, which functioned as a reductio of those methods; Simmons, Nelson and Simonsohn's demonstration that researcher degrees of freedom make it trivially easy to obtain *p* < .05 for a false hypothesis; and then the **Open Science Collaboration's "Estimating the reproducibility of psychological science"** (*Science*, 2015, vol. 349, doi:10.1126/science.aac4716), which attempted 100 replications and found roughly a third produced statistically significant results in the same direction, with replication effect sizes averaging about half the originals.

**The mechanisms.**
- **p-hacking** — flexibility in analysis (optional stopping, dropping outliers post hoc, trying covariates, choosing among DVs) exploited until *p* < .05.
- **HARKing** — Hypothesising After the Results are Known, presenting an exploratory finding as confirmatory.
- **Publication bias / the file drawer** — null results go unpublished, so the published literature over-estimates effects.
- **Underpowered studies** — which produce both false negatives and, when significant, inflated effect estimates (the winner's curse).
- **Incentives** — novelty and significance were rewarded; replication was not.

**The reforms.**
- **Preregistration** — timestamp hypotheses, design and analysis plan before data collection (OSF, AsPredicted). **Registered Reports** go further: peer review of the protocol before data collection, with in-principle acceptance regardless of outcome. This is the single most effective structural fix available.
- **Open data, open materials, open code** — with the corresponding badges, and with genuine ethical limits where participants are identifiable, which matters for small-community research in Namibia and rural South Africa.
- **Larger samples, multi-site collaborations** — Many Labs, the Psychological Science Accelerator.
- **Estimation over dichotomous testing** — report effect sizes and intervals; equivalence testing (TOST) to make claims about the absence of a meaningful effect; Bayesian methods, and Bayes factors in particular, to quantify evidence *for* the null.
- **Better reporting standards** — CONSORT for trials, PRISMA for reviews, JARS for APA journals, STROBE for observational work.

**What this means for an applied educational psychologist.** Be sceptical of any single striking study. Prefer meta-analyses, and then check whether the meta-analysis handled publication bias. Prefer large-sample field trials in real schools over laboratory demonstrations. Note whether an intervention's evidence base consists of trials run by the intervention's own developers — the developer-allegiance effect is large and pervasive in intervention research. And be willing to say "this was widely believed and has not held up", which is the professional stance that files `03` and `08` take throughout.

---

## 9. Software

| Tool | What it is for | Notes |
|---|---|---|
| **SPSS** | The default in most southern African and UK psychology departments | Menu-driven, familiar, expensive, poor reproducibility unless syntax is saved. **Always save and archive syntax** — a point-and-click analysis is not reproducible |
| **R** | Statistics and everything else | Free, open, the standard for methodologists. `tidyverse`, `lme4` (multilevel), `lavaan` (SEM), `psych` (psychometrics), `metafor` (meta-analysis), `pwr`, `mirt` (IRT), `ggplot2`. R Markdown/Quarto gives genuinely reproducible reports |
| **jamovi** | Free, SPSS-like GUI built on R | The best teaching bridge; produces APA-formatted output; syntax mode available |
| **JASP** | Free GUI, strong Bayesian support | The easiest route into Bayes factors for a practitioner |
| **Python** | General-purpose; `pandas`, `statsmodels`, `scipy`, `pingouin` | Less common in psychology than R but growing |
| **Mplus** | Latent variable modelling | Powerful, expensive, terse |
| **G*Power** | Power analysis | Free, standard |
| **NVivo** | Qualitative coding and retrieval | Commercial, dominant; expensive site licences |
| **ATLAS.ti** | Qualitative coding | The main NVivo alternative |
| **MAXQDA** | Qualitative and mixed methods | Strong joint-display support |
| **Taguette / QualCoder** | Free qualitative coding | Realistic option where licences are unaffordable |
| **OSF** | Preregistration, data and materials hosting | Free |
| **Zotero / Mendeley** | Reference management | Zotero is free and open |

> ⚠️ Qualitative software codes nothing and analyses nothing. It stores, retrieves and organises. The analysis is done by the researcher, and a project that outsources interpretive judgment to the software has not done qualitative research.

## Sources

- [Replication crisis](https://en.wikipedia.org/wiki/Replication_crisis) — Wikipedia
- [Item response theory](https://en.wikipedia.org/wiki/Item_response_theory) — Wikipedia
- Crossref metadata (https://api.crossref.org/works) verifying: Open Science Collaboration, "Estimating the reproducibility of psychological science", *Science* 349 (2015), doi:10.1126/science.aac4716
- [Open Library search API](https://openlibrary.org/search.json) — Internet Archive, verifying: Field, *Discovering Statistics Using IBM SPSS Statistics*; Howell, *Statistical Methods for Psychology* (1982); Tabachnick & Fidell, *Using Multivariate Statistics* (1983); Cohen, *Statistical Power Analysis for the Behavioral Sciences* (1969); Creswell, *Research Design* (1994); Braun & Clarke, *Thematic Analysis: A Practical Guide* (2021); Smith, *Interpretative Phenomenological Analysis* (2009)

## Open questions

- The Simmons, Nelson & Simonsohn "False-Positive Psychology" paper and the Many Labs / Psychological Science Accelerator outputs are described from general knowledge; locate and cite the primary references before relying on specifics.
- Current editions of all methods texts named — only first-publication years were verified.
- The "developer allegiance" effect size in educational intervention research — asserted here from general knowledge; find and cite the meta-analytic estimate.
- Whether South African and Namibian ethics committees have adopted preregistration and open-data expectations, and what the local guidance says about open data from small or identifiable communities.

