---
id: psych.assessment_psychometrics
title: Assessment and psychometrics — the technical core
domain: 22_psychology_and_education
tags: [psychometrics, classical-test-theory, reliability, validity, norms, standard-scores, sem, item-response-theory, test-bias, wisc-v, wais-iv, kabc, wj-iv, ssais-r, jsais, conners, basc, sdq, aseba, projective-tests, dynamic-assessment, report-writing, south-africa, namibia]
jurisdiction: southern-africa
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Wechsler Intelligence Scale for Children", url: "https://en.wikipedia.org/wiki/Wechsler_Intelligence_Scale_for_Children", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Item response theory", url: "https://en.wikipedia.org/wiki/Item_response_theory", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Cattell–Horn–Carroll theory", url: "https://en.wikipedia.org/wiki/Cattell%E2%80%93Horn%E2%80%93Carroll_theory", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Rorschach test", url: "https://en.wikipedia.org/wiki/Rorschach_test", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Dynamic assessment", url: "https://en.wikipedia.org/wiki/Dynamic_assessment", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Crossref metadata for South African assessment literature", url: "https://api.crossref.org/works", publisher: "Crossref", accessed: 2026-08-25}
related: [psych.edpsych_core, psych.intervention_practice, psych.ethics_law, psych.research_methods]
---

# Assessment and psychometrics — the technical core

**Summary.** Psychometrics is the part of the discipline that distinguishes a psychologist from a well-read helper. It is also the part most often applied badly. The chain of reasoning that has to hold for a test score to mean anything runs: a construct is defined → items are written and calibrated → the test is standardised on a defined population → reliability and validity evidence is accumulated **for a specified use with a specified population** → a score is placed against appropriate norms → an error band is attached → the score is interpreted alongside history, observation and other data. In southern Africa the weakest links in that chain are norms and validity-for-this-population, and pretending otherwise is the field's most common professional failure.

## Key facts

| Quantity | Definition | Typical scale |
|---|---|---|
| Standard score (IQ-type) | M = 100, SD = 15 | 55–145 covers ±3 SD |
| Scaled score (subtest) | M = 10, SD = 3 | 1–19 |
| *T*-score | M = 50, SD = 10 | Behaviour rating scales |
| *z*-score | M = 0, SD = 1 | Raw statistical form |
| Stanine | M = 5, SD ≈ 2 | 1–9, coarse |
| Percentile rank | % of norm group scoring at or below | 1–99, **not** an equal-interval scale |
| SEM | SD × √(1 − *r*<sub>xx</sub>) | Attach to every reported score |
| 95% confidence interval | score ± 1.96 × SEM | Report as a band, not a point |

> ⚠️ **[ZA]** Psychological tests are controlled instruments. A test classified as a psychological test under the Health Professions Act framework may be used only by practitioners registered in an appropriate category, and interpretation beyond a psychometrist's defined scope belongs to a psychologist. Distributing, photocopying or lending test materials, or allowing an unqualified person to administer them, is both a copyright breach and an ethical offence. *The current classified-tests list could not be retrieved — see Open questions.*

---

## 1. Classical test theory

The founding equation: **X = T + E** — an observed score is a true score plus error. "True score" is defined operationally as the expected value of observed scores over infinite independent administrations; it is not a Platonic ability. Error is assumed random, uncorrelated with true score, and mean-zero.

From this: **reliability** *r*<sub>xx</sub> is the proportion of observed-score variance that is true-score variance. Everything else in CTT follows.

**Limitations that matter in practice.** Item statistics are sample-dependent (a "difficult" item is difficult relative to the sample that took it); the standard error is assumed constant across the score range, which is false — measurement is less precise at the extremes, exactly where educational psychologists work; and scores from different tests of the same construct are not on a common scale. IRT (§6) fixes all three, which is why modern batteries are built with it even when they report CTT-style statistics.

---

## 2. Reliability

| Type | What it estimates | How obtained | Watch out for |
|---|---|---|---|
| Internal consistency | Item homogeneity | Cronbach's α, KR-20, McDonald's ω | α rises with test length and with redundant items; α is **not** a measure of unidimensionality; ω is the better statistic and is increasingly expected |
| Test–retest | Stability over time | Same test, two occasions | Practice effects; interval must be stated; unsuitable for state constructs |
| Alternate/parallel forms | Equivalence of forms | Two forms, one or two occasions | Requires genuinely parallel forms, which are rare |
| Inter-rater | Agreement between scorers | Cohen's κ, ICC, % agreement | Raw % agreement inflates with skewed base rates; use κ or ICC |
| Split-half | Internal consistency | Spearman-Brown corrected | Depends on how the halves are split |

**Interpretive conventions.** For high-stakes individual decisions, reliability ≥ .90 is the usual expectation; ≥ .80 for group-level or lower-stakes use; below .70 is generally unusable for individual decisions. These are conventions, not laws, and the honest question is always "reliable enough for what decision?"

**Standard error of measurement.** SEM = SD√(1 − *r*<sub>xx</sub>). For a test with SD = 15 and *r*<sub>xx</sub> = .95, SEM ≈ 3.4, so a 95% band is roughly ±6.6 points. This is the single most important number to put in a report, because it is what stops a reader treating an IQ of 84 and an IQ of 89 as different. **Standard error of the difference** (for comparing two scores from the same person) and **standard error of estimate** (for predicted scores) are the two related quantities routinely confused with it.

---

## 3. Validity

The modern position (following Messick and the *Standards for Educational and Psychological Testing*) is that validity is **a unitary property of interpretations and uses of scores**, not of tests. "The WISC-V is valid" is a category error; "the WISC-V FSIQ is a valid basis for identifying intellectual disability in an English-first-language South African child schooled continuously in English" is a claim you can evaluate.

The traditional taxonomy remains useful as a checklist of evidence types:

- **Content validity** — do the items sample the domain adequately? Judged, not computed. Central for achievement tests and for curriculum-based measurement.
- **Criterion validity** — concurrent (against a criterion measured now) and predictive (against a future criterion). Constrained by criterion reliability and by range restriction, both of which attenuate observed coefficients.
- **Construct validity** — the whole nomological net: convergent evidence (correlates with what it should), discriminant evidence (does not correlate with what it should not), factorial evidence (the internal structure matches the theory), developmental evidence, and evidence from experimental manipulation. The multitrait–multimethod matrix (Campbell and Fiske) is the classic design.
- **Consequential validity** — what happens as a result of the test being used. Contested as a category but practically indispensable: a test that is technically sound and systematically misplaces second-language learners in special education is not doing acceptable work.
- **Incremental validity** — does this test add predictive power over cheaper information already available? The question that kills most add-on instruments, and the one practitioners most often fail to ask.
- **Face validity** — whether it *looks* right. Not validity. Relevant only to test-taker acceptance.

---

## 4. Standardisation and norms

A **norm-referenced** score says where a person stands relative to a reference group. It is meaningless without knowing the group. The standardisation sample must be defined, stratified (age, sex, region, socio-economic status, language, education level, and **[ZA]/[NA]** quality of schooling), adequately sized per age band, and recent.

**Criterion-referenced** scores, by contrast, say what a person can do against a defined standard, and **ipsative** scores compare a person to themselves. Curriculum-based measurement is criterion-referenced and is often far more useful to a teacher than a norm-referenced score.

**Norm obsolescence.** The **Flynn effect** means norms inflate scores as they age — a test normed 25 years ago will over-estimate current ability. Instruments still in circulation in southern African practice that were normed in the 1980s or early 1990s should be treated with corresponding suspicion.

**Score types and their traps.** Percentile ranks are ordinal and bunch severely in the middle of the distribution — the difference between the 45th and 55th percentile is trivial while the difference between the 1st and 5th is large. **Age-equivalent and grade-equivalent scores should generally not be reported at all**: they are statistically crude, invite over-interpretation ("she reads like a seven-year-old"), and have unequal units.

---

## 5. Test bias and fairness in multilingual, multicultural contexts

This is the defining technical and ethical problem of assessment in South Africa and Namibia and it deserves to be handled properly rather than as a disclaimer paragraph.

**Bias is a technical concept, not a synonym for unfairness.** Its forms:

- **Construct bias** — the construct itself is not equivalent across groups (e.g. what counts as "intelligent behaviour" or as appropriate adult-child interaction).
- **Method bias** — differential familiarity with the testing situation: being timed, being asked questions by a stranger to which the stranger already knows the answer, working with pencil-and-paper formats, manipulating blocks, or the fundamental convention that speed is valued.
- **Item bias / differential item functioning (DIF)** — an item functions differently for equally able members of different groups. Detectable statistically (Mantel-Haenszel, logistic regression, IRT-based DIF) and removable.
- **Predictive bias** — the regression of criterion on test score differs by group (different slopes or intercepts). Note this is a different question from mean-score differences: groups can differ in mean score with no predictive bias, and a test can be predictively unbiased and still be an unfair basis for a decision.

**The southern African specifics:**

1. **Language.** Most learners are assessed in a language that is not their home language. A verbal test administered in the language of instruction measures language proficiency confounded with reasoning. Translating a test does not solve this: translation without re-standardisation produces an instrument with unknown properties. The **ITC Guidelines for Translating and Adapting Tests** (2nd edn, *International Journal of Testing*, 2017) set out the required process — and it is expensive, which is why it is so rarely done properly.
2. **Quality of education as a moderator.** Shuttleworth-Edwards and colleagues' work on WAIS-III performance in South Africa (*Journal of Clinical and Experimental Neuropsychology*, 2004; and in *Psychological Assessment in South Africa*, 2013) demonstrated that **quality and duration of education**, not race as such, is the dominant moderator of test performance, and produced stratified normative indications on that basis. This is the correct framing: the variable to stratify on is educational history, socio-economic circumstance and language exposure.
3. **Test-wiseness.** Learners from well-resourced schools have practised the format. This is a method-bias effect and it is large.
4. **Availability.** Many instruments are simply not available with local norms; some are available only in English and Afrikaans; **[NA]** locally normed instruments are scarcer still.

**Practical responses.** Prefer non-verbal and reduced-language measures where the referral question permits (Raven's Progressive Matrices, the non-verbal indices of a full battery, the UNIT and the Leiter family). Use **multiple sources** and never a single score. Use **dynamic assessment** (§9) where static scores are likely to underestimate. Report the language of assessment, the assessor's language competence, the learner's language history and schooling history **in the report**, and state explicitly the limits this places on interpretation. Where you use norms from another population, say so and say what it means.

> ⚠️ Using a foreign-normed cognitive battery to place a second-language, under-schooled child in a special class, without qualification, is the classic malpractice case in this field. It is also, historically, exactly what apartheid-era assessment did. The profession's institutional memory on this point is a resource, not a rebuke.

---

## 6. Item response theory

IRT models the probability of a given item response as a function of a latent trait θ and item parameters. The common models: **1PL/Rasch** (difficulty only), **2PL** (difficulty and discrimination), **3PL** (adds a guessing/lower-asymptote parameter), and graded-response or partial-credit models for polytomous items.

Why it matters practically:

- **Item and person parameters are on the same scale**, so item difficulty and person ability can be compared directly.
- **Invariance** — item parameters are (in principle) sample-independent and person parameters test-independent, which enables **equating** across forms and versions.
- **Conditional standard errors** — precision varies across the ability range and IRT quantifies it, replacing CTT's single SEM. This matters enormously at the tails.
- **Computerised adaptive testing** — select each next item at the current ability estimate; far more efficient.
- **DIF detection** — the technically strongest way to identify biased items, which is directly relevant to §5.

The information function is the central IRT tool: a test is informative where its items are targeted, and a battery aimed at the middle of the distribution measures gifted and intellectually disabled learners poorly.

---

## 7. The instruments an educational psychologist actually uses

### 7.1 Cognitive batteries

- **WISC-V** (Wechsler Intelligence Scale for Children, Fifth Edition; Wechsler, 2014), ages 6–16. 21 subtests yielding 15 composite scores. Full Scale IQ is derived from 7 of the 10 primary subtests. **Five primary index scores**: Verbal Comprehension (VCI: Similarities, Vocabulary), Visual Spatial (VSI: Block Design, Visual Puzzles), Fluid Reasoning (FRI: Matrix Reasoning, Figure Weights), Working Memory (WMI) and Processing Speed (PSI). Ancillary indices include the General Ability Index (GAI). Administration 45–65 minutes for the core; a full extended battery can run to three hours or more. Each edition is renormed against the Flynn effect.
- **WAIS-IV** — the adult counterpart, 16+, four index structure (VCI, PRI, WMI, PSI). Used for school-leavers, adult learners and disability determinations. *WAIS-5 has been published in some markets — verify local availability and norms.*
- **SB5** (Stanford-Binet, Fifth Edition) — the widest age range (roughly 2 to 85+), strong at the extremes, which makes it the preferred instrument for very young, very low-functioning or very gifted assessment.
- **KABC-II** (Kaufman Assessment Battery for Children) — dual-theoretical, interpretable through either the Luria model (which excludes acquired knowledge) or the CHC model; explicitly designed to reduce cultural loading. The Luria-model option (MPI rather than FCI) is the single most useful feature for second-language assessment.
- **WJ-IV** (Woodcock-Johnson IV) — Tests of Cognitive Abilities, Oral Language and Achievement, built directly on CHC theory and designed for cross-battery use.

### 7.2 South African instruments

- **SSAIS-R** — Senior South African Individual Scale, Revised. The locally developed individual cognitive scale for older children; verbal and non-verbal scales. Studied against reading ability in South African samples (Cockcroft & Blackburn, *South African Journal of Psychology*, 2008).
- **JSAIS** — Junior South African Individual Scales, for younger children; used in school-readiness assessment (Theron, in *Psychological Assessment in South Africa*, 2013).
- **ASB** — Aptitude Test for School Beginners, for school-readiness screening.
- **GSAT / Individual Scale for General Scholastic Aptitude** — group and individual scholastic aptitude measures from the former HSRC stable; comparability across population groups was studied and questioned as far back as Claassen (*SAJP*, 1990).
- **IPT-R** — named in some practitioner lists; **this abbreviation could not be verified from any source reachable here and should not be used until confirmed.**

The general position on the South African instruments: they were developed for a specific historical population and language configuration, their norms are in most cases old, and their continued use is defended on the grounds that locally-normed-but-dated may still beat foreign-normed-and-current. That trade-off should be made explicitly, case by case, and stated in the report.

**[NA]** Namibia has essentially no locally standardised cognitive battery. Practice relies on South African and international instruments with the corresponding caveats.

### 7.3 Achievement and academic measures

Standardised reading, spelling and mathematics tests; curriculum-based measurement (repeated brief probes of oral reading fluency, maths computation, written expression — cheap, sensitive to change, and better suited to progress monitoring than any norm-referenced battery); phonological awareness and rapid automatised naming measures for reading difficulty; and error analysis of the learner's actual books, which is free and frequently the most informative thing in the file.

### 7.4 Behaviour rating scales

- **Conners** (Conners 4 / Conners 3) — ADHD-focused, multi-informant (parent, teacher, self).
- **BASC-3** (Behavior Assessment System for Children) — broad-band, with clinical and adaptive scales, plus a structured developmental history and observation system.
- **SDQ** (Strengths and Difficulties Questionnaire, Goodman) — 25 items, five scales, **free to use**, extensively translated and used internationally including in African research. The best value instrument in the field for screening.
- **ASEBA / CBCL** (Achenbach System of Empirically Based Assessment; Child Behavior Checklist, Teacher's Report Form, Youth Self-Report) — the most extensively cross-culturally validated broad-band system, with multi-society norms.

**Interpretation rule.** Rating scales measure the *rater's perception* in a *specific setting*. Parent–teacher agreement on child behaviour is typically modest (correlations in the .2–.4 range are common). Disagreement is data about setting-specificity, not noise to be averaged away. No rating scale diagnoses anything.

### 7.5 Projective techniques and the controversy

Rorschach inkblots, the Thematic Apperception Test, Children's Apperception Test, sentence completion, Draw-a-Person and Kinetic Family Drawing, the House-Tree-Person.

The evidence position, stated plainly: **the psychometric case against most projective techniques as diagnostic instruments is strong**. Wood, Lilienfeld and colleagues' critiques (e.g. "The Rorschach Inkblot Test: A case of overstatement?", *Assessment*, 1999) documented weak or absent validity for most Rorschach indices, over-pathologising norms, and inter-scorer problems. Human-figure-drawing indices of emotional disturbance have repeatedly failed validation. The Exner Comprehensive System improved standardisation and the newer R-PAS represents a further attempt; a small number of Rorschach variables (notably some thought-disorder indices) have defensible validity, and the general finding is that the instrument is far weaker than its clinical popularity implies.

**Where they retain a defensible place:** as *structured clinical interview aids* and rapport-builders with children who will not talk, generating hypotheses to be tested against other data — never as the evidential basis for a diagnosis, a placement or a custody recommendation. Anyone using them should be able to say which specific scoring system, with what published validity, for what inference.

### 7.6 Adaptive behaviour scales

**Vineland-3** and **ABAS-3** are the standard instruments. They are not optional extras: a diagnosis of intellectual disability requires deficits in adaptive functioning as well as in intellectual functioning, and adaptive behaviour is what actually determines the support a learner needs. They are informant-based (parent/caregiver and teacher forms) and are therefore subject to informant effects and to cultural variation in what independence is expected at what age — a real issue in rural southern African contexts where expected competences differ substantially from the standardisation samples.

---

## 8. Dynamic assessment

Static tests measure what the learner can currently do unaided — Vygotsky's actual developmental level. **Dynamic assessment** measures the **zone of proximal development** by embedding mediation in the assessment: a test–teach–retest or graduated-prompt design in which the assessor deliberately intervenes and records how much and what kind of help produces change.

**Feuerstein's** Learning Propensity Assessment Device (LPAD), built on the theory of structural cognitive modifiability and mediated learning experience, is the best-known system, with Instrumental Enrichment as the associated intervention programme. **Budoff's** learning-potential approach and **Campione and Brown's** graduated-prompting are the other main traditions.

**Why it matters here.** For a learner whose static score is depressed by educational deprivation, poor prior teaching, second-language testing or test-unfamiliarity, dynamic assessment distinguishes *low current performance* from *low modifiability* — which is exactly the distinction a placement decision needs and exactly the one a static IQ cannot make. It is therefore disproportionately valuable in South African and Namibian practice.

**The honest caveats.** Dynamic assessment procedures are time-expensive (hours, not minutes), their own psychometric properties are weaker and less standardised than those of static tests, scoring is less objective, and the evidence that DA-derived indices predict response to intervention better than well-conducted static assessment plus progress monitoring is suggestive rather than settled.

---

## 9. Report writing

The report is the profession's actual product. A defensible educational psychology report:

1. **States the referral question** explicitly, in the referrer's words, and answers *that* question.
2. **Records the assessment conditions** — dates, sessions, language of assessment, interpreter if any, the learner's cooperation, illness, medication, glasses, hearing aids.
3. **Records background** — developmental, medical, educational and family history; language history; schooling history including changes of school and language of instruction; previous assessments.
4. **Reports observations** as behaviour, not inference ("stopped after 40 seconds and said 'I can't'", not "was poorly motivated").
5. **Reports scores with confidence bands**, names the instrument and edition, names the norms used, and states where those norms come from and what the limits are.
6. **Integrates** rather than lists. A report that recites subtest scores in sequence has not done the work. Subtest-level profile analysis, in particular, has poor reliability and should be used to generate hypotheses at most.
7. **Formulates** — a coherent account of how this learner's profile, history and context produce the presenting difficulty (see file `09` on formulation versus diagnosis).
8. **Recommends** in operational terms: who does what, how often, with what resources, reviewed when. "Requires individualised support" is not a recommendation.
9. **Is written to be read by the parent and the teacher**, not only by another psychologist. Two versions are sometimes justified; jargon that the reader cannot act on never is.
10. **Acknowledges limitations** honestly, including everything in §5.

> ⚠️ Reports outlive the case. They are read by schools, by other clinicians, sometimes by courts, and by the child themselves years later. Write nothing you could not defend in a disciplinary hearing or explain to the child as an adult.

## Sources

- [Wechsler Intelligence Scale for Children](https://en.wikipedia.org/wiki/Wechsler_Intelligence_Scale_for_Children) — Wikipedia (WISC-V structure, indices, subtests, administration time, renorming)
- [Item response theory](https://en.wikipedia.org/wiki/Item_response_theory) — Wikipedia
- [Cattell–Horn–Carroll theory](https://en.wikipedia.org/wiki/Cattell%E2%80%93Horn%E2%80%93Carroll_theory) — Wikipedia
- [Rorschach test](https://en.wikipedia.org/wiki/Rorschach_test) — Wikipedia
- [Dynamic assessment](https://en.wikipedia.org/wiki/Dynamic_assessment) — Wikipedia
- Crossref metadata (https://api.crossref.org/works) verifying: Shuttleworth-Edwards, Kemp & Rust, "Cross-cultural effects on IQ test performance", *Journal of Clinical and Experimental Neuropsychology* 26:903–920 (2004), doi:10.1080/13803390490510824; Shuttleworth-Edwards, Gaylard & Radloff, "WAIS-III test performance in the South African context", in *Psychological Assessment in South Africa* pp.17–32 (2013), doi:10.18772/22013015782.7; Cockcroft & Blackburn, SSAIS-R and reading ability, *South African Journal of Psychology* 38:377–389 (2008), doi:10.1177/008124630803800209; Theron, JSAIS and school readiness, *Psychological Assessment in South Africa* pp.60–73 (2013), doi:10.18772/22013015782.10; Claassen, comparability of GSAT scores across population groups, *SAJP* 20:80–92 (1990), doi:10.1177/008124639002000203; ITC Guidelines for Translating and Adapting Tests (2nd edn), *International Journal of Testing* 18:101–134 (2017), doi:10.1080/15305058.2017.1398166; Wood & Lilienfeld, "The Rorschach Inkblot Test: A case of overstatement?", *Assessment* 6:341–351 (1999), doi:10.1177/107319119900600405

## Open questions

- **[ZA]** The current HPCSA list of tests classified as psychological tests, and the precise scope-of-practice boundary between psychometrist and psychologist. HPCSA site unreachable on 2026-08-25 — `needs-verification`.
- **IPT-R** — the instrument named by this abbreviation could not be identified from any reachable source. Do not cite it until the full name and publisher are confirmed.
- Whether WAIS-5 is published and normed for southern African use, and the current edition status of the Conners, BASC and Vineland families.
- Whether the SSAIS-R, JSAIS, ASB and GSAT have been renormed since their original standardisation, and if so when.
- **[NA]** Whether HPCNA operates any equivalent test-classification regime — not verified.
- The current standing of R-PAS validity evidence relative to the Exner Comprehensive System.
