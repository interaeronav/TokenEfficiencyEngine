---
id: psych.how_psychologists_think
title: How psychologists think — the transferable cognitive toolkit
domain: 22_psychology_and_education
tags: [operationalisation, construct-validity, base-rates, regression-to-the-mean, confounding, correlation-causation, effect-size, individual-differences, ecological-fallacy, cognitive-bias, formulation, hypothesis-testing, falsification, reasoning]
jurisdiction: global
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Replication crisis", url: "https://en.wikipedia.org/wiki/Replication_crisis", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Crossref metadata for cited papers", url: "https://api.crossref.org/works", publisher: "Crossref", accessed: 2026-08-25}
  - {title: "Learning styles", url: "https://en.wikipedia.org/wiki/Learning_styles", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Open Library search API", url: "https://openlibrary.org/search.json", publisher: "Internet Archive / Open Library", accessed: 2026-08-25}
related: [psych.research_methods, psych.assessment_psychometrics, psych.edpsych_core, psych.reading_list]
---

# How psychologists think — the transferable cognitive toolkit

**Summary.** What survives a psychology training after the content fades is a set of reasoning habits. They are not unique to psychology — epidemiologists, econometricians and good engineers hold most of them — but psychology teaches them unusually explicitly because its subject matter is so easy to be wrong about. This file sets them out as a working toolkit for anyone reasoning about human behaviour, whether the domain is a classroom, a construction site, a hiring decision or a building's occupants.

## Key facts

| Habit | The question it forces | The error it prevents |
|---|---|---|
| Operationalisation | How would you measure it? | Arguing about words |
| Construct vs measure | Is this the thing, or an indicator of the thing? | Reifying the score |
| Base rates | How common is this anyway? | Over-reading a positive test |
| Regression to the mean | Was the starting point extreme? | Believing a spurious improvement |
| Confounding | What else differs between these groups? | False causal attribution |
| Effect size | How big, in units that matter? | Treating significant as important |
| Individual differences | For whom, and how much variation? | Applying a group mean to a person |
| Ecological fallacy | At what level was this measured? | Inferring individuals from aggregates |
| Formulation | What produces and maintains this? | Mistaking a label for an explanation |
| Falsification | What would show me I'm wrong? | Confirmation-seeking |

---

## 1. Operationalisation

Before you can study something you must say what would count as an instance of it. "Motivation", "engagement", "resilience", "site culture", "team cohesion" and "quality" all mean nothing until specified as something observable and countable: minutes on task; number of voluntary contributions; latency to resume after failure; unplanned absence rate; near-miss reports per 1,000 hours.

The discipline has two parts. **First**, force the definition: *what would I see more of, or less of, if this were true?* **Second**, notice what the definition excludes. Every operationalisation is a narrowing, and the gap between the concept and the measure is where most bad inference lives.

**The generalisable move.** When a meeting stalls on whether morale is bad, the psychologist's question is not "is it?" but "what would we count?" Most unresolvable arguments are unresolvable because nobody has operationalised the disagreement.

---

## 2. The construct/measure distinction

A **construct** is a theoretical entity — intelligence, anxiety, competence, safety climate. A **measure** is an operationalisation of it — a score, a rating, an incident count. The two are never identical, and the entire discipline of psychometrics (file `04`) exists to characterise the gap.

Three consequences follow, and they generalise well beyond psychology:

1. **Never say "the test measures X"; say "scores on this test correlate with X to this degree, for this population, in this context."** The former is a claim about the world; the latter is a claim you can defend.
2. **Reification is the standard failure.** IQ becomes a thing rather than a score. A KPI becomes the objective rather than an indicator of it. Goodhart's Law — when a measure becomes a target it ceases to be a good measure — is the construct/measure distinction restated for management.
3. **Multiple imperfect indicators beat one good one.** Triangulate. If three unrelated measures point the same way, the inference is much stronger than any of them alone; if they diverge, that divergence is information, not noise.

---

## 3. Base rates and prior probability

The single most consistently under-used piece of statistical reasoning. Given a screening test with 90% sensitivity and 90% specificity for a condition with a 1% base rate, a positive result yields a posterior probability of about 8% — most positives are false. People, including clinicians, routinely estimate this at around 80%.

**Why it matters in practice.** School-wide screening for a rare condition generates far more false positives than true cases, and the consequences of those false positives (labelling, placement, parental anxiety) are real. The same arithmetic governs pre-employment drug screening, structural defect detection, medical testing and fraud detection. **Never interpret a test result without asking how common the thing is in the population being tested.**

**The generalisable move.** Ask "out of a hundred, how many?" — natural-frequency framing eliminates most base-rate errors that probability framing produces.

---

## 4. Regression to the mean

Extreme scores are extreme partly because of measurement error and transient factors. On re-measurement they move toward the mean, without anything having been done.

This produces an entire class of illusions:

- The worst-performing school improves after intervention. So does the worst-performing school that received nothing.
- A child assessed during a crisis scores poorly and appears to improve after therapy.
- Punishing poor performance appears to work, and praising good performance appears to backfire — the classic Kahneman and Tversky flight-instructor example. Both are regression.
- A site with an unusually bad safety month has a better month after the safety talk.

**The generalisable move.** Whenever a group was selected *because* it was extreme, expect improvement without treatment, and insist on a comparison group selected the same way. This is the reason the pre-post design without a control is nearly worthless in applied settings, and the reason regression-discontinuity and interrupted-time-series designs exist.

---

## 5. Confounding and third variables

Two things covary. Before concluding that one causes the other, enumerate: does B cause A? Does C cause both? Is the association an artefact of selection into the sample? Is it an artefact of how the variables were measured?

**Selection effects** deserve special mention because they are the most common and the least noticed. Anything that determines who is in your sample can create associations that do not exist in the population — Berkson's paradox, survivorship bias, differential attrition, and the "restaurants with good food have bad service" pattern that arises purely because both are required for the restaurant to survive.

**Colliders.** Conditioning on a common effect of two variables induces a spurious association between them. This is the subtle one, and it means that "controlling for" more variables is not automatically better — statistical control can create bias as well as remove it.

**The generalisable move.** Draw the causal diagram before you run the analysis. If you cannot draw it, you do not know what you are controlling for.

---

## 6. Correlation and causation, disciplined

The slogan is universally known and almost never applied. The disciplined version is a checklist of what would license a causal claim:

- **Temporal precedence** — the cause preceded the effect, established by design not assumption.
- **Covariation** — they actually co-vary, with an effect size worth caring about.
- **Non-spuriousness** — plausible alternatives are excluded by randomisation, by design, or by measured adjustment with a defensible causal model.
- **Mechanism** — there is an account of how, which is testable.
- **Dose-response** — more of the cause produces more of the effect.
- **Consistency across contexts and methods.**

Randomisation is the cheapest way to get non-spuriousness and is usually available in some form. Where it is not: instrumental variables, regression discontinuity, difference-in-differences, interrupted time series, natural experiments, and — for individual cases — single-case experimental designs (file `06`).

> ⚠️ The most consequential everyday failure is not "correlation is not causation" but **assuming the direction**. Reading achievement correlates with parental reading at home; the causal traffic runs both ways and is confounded by a dozen third variables. Behaviour problems correlate with poor teacher relationships; each causes the other. In practice, reciprocal causation is the default in human systems and unidirectional models are the special case.

---

## 7. Effect size over statistical significance

*p* < .05 tells you an effect is probably not exactly zero. It tells you nothing about magnitude, importance, or whether it will hold up. With a large enough sample, trivial effects are significant; with a small enough sample, large effects are not.

The operational habits:

- **Report and demand magnitudes in units people care about.** "Three weeks of additional reading progress at a cost of R400 per learner" is decision-relevant. "*p* = .03" is not.
- **Report intervals.** A point estimate without an interval is a claim to precision you do not have.
- **Ask about practical significance separately** from statistical significance, and be explicit about the cost side. A small effect delivered cheaply at scale often beats a large one that cannot be delivered.
- **Distrust surprisingly large effects from small samples.** They are usually the winner's curse: an underpowered study can only reach significance if it happens to over-estimate.

---

## 8. Individual differences over group means

The mean is a property of the group, not of any member of it. Psychological training makes this reflexive, and it is the habit that most distinguishes psychologists from disciplines that reason about representative agents.

- **Report variability with every mean.** Two groups with the same mean and different variances behave completely differently.
- **Ask about the distribution of response**, not just its average. An intervention with a mean effect of zero may be helping half the participants and harming the other half — and that is a completely different fact from "it does not work". Most trial reporting hides this.
- **Ask who is in the tails**, because in applied work the tails are the referrals.
- **Beware the average that describes nobody** — the classic case being the US Air Force cockpit sized to the average pilot, which fitted no pilot at all. This is a direct design lesson for domains `01` and `19`.

---

## 9. The ecological fallacy and its inverse

**Ecological fallacy** — inferring individual-level relationships from group-level data. Countries with higher chocolate consumption have more Nobel laureates; nothing follows about eating chocolate. Schools with higher mean SES have higher mean results; nothing directly follows about any individual learner.

**Atomistic fallacy** — the inverse: inferring group-level relationships from individual data, ignoring context and clustering effects.

**Simpson's paradox** is the extreme case: an association can reverse direction when data are aggregated or disaggregated. This is not a curiosity; it appears in admissions data, in mortality statistics and in productivity comparisons routinely.

**The generalisable move.** Always ask **at what level a relationship was observed and at what level you intend to apply it**. Where data are nested (learners in classes in schools; workers in crews on sites), multilevel models exist precisely to keep the levels separate.

---

## 10. Cognitive biases in one's own reasoning

Psychologists are not immune — the "bias blind spot" is itself a documented finding, and it is that people see biases in others more readily than in themselves. The professionally relevant ones:

- **Confirmation bias** — seeking and weighting evidence for the hypothesis you already hold. In assessment this produces the case where the referral question determines the finding.
- **Anchoring** — first information dominates. A referral letter saying "probable ADHD" anchors an entire assessment. The countermeasure is to read the file *after* the first contact where practicable, or to generate competing hypotheses before reading.
- **Availability** — vivid and recent cases feel common. The last dramatic case distorts the base rate.
- **Fundamental attribution error** — over-attributing behaviour to disposition and under-attributing to situation, in others while doing the reverse for oneself. This is the professional deformation of the whole field: a psychologist is trained to look inside the person, and the most common resulting error is missing that the child is hungry, the classroom is chaotic, or the site supervisor is abusive.
- **Hindsight bias** — after an outcome, its causes look obvious. This corrupts every incident review and every retrospective case discussion.
- **Overconfidence and the illusion of clinical judgment.** Meehl's 1954 work and the subsequent literature found that simple actuarial rules typically match or beat expert clinical prediction. Clinicians reliably over-estimate their own accuracy, largely because they receive no clean feedback.

**The countermeasures that actually work.** Consider the opposite explicitly. Write down predictions in advance and check them. Use structured procedures — structured interviews, checklists and decision rules outperform unaided judgment in almost every domain studied. Seek disconfirming evidence deliberately. Get supervision and expose your reasoning to someone whose job is to disagree. And keep a record, because memory reconstructs to fit the outcome.

---

## 11. Formulation rather than diagnosis

This is the most valuable single transferable idea in the file.

A **diagnosis** is a category: this presentation belongs to that class. It is useful for communication, for administrative access to resources, and sometimes for treatment selection. It is not an explanation. "He can't concentrate because he has ADHD" is circular — ADHD is the name for not concentrating.

A **formulation** is a causal account of *this* person's difficulty: predisposing factors, precipitating factors, perpetuating factors and protective factors, arranged into a story of how the problem arose and — crucially — **what is maintaining it now**. It is explicitly a hypothesis, held provisionally, revised as evidence comes in, and shared with the client rather than pronounced over them.

The practical superiority of formulation is that it generates intervention targets. A diagnosis of specific learning disorder tells you nothing about what to do on Monday. A formulation that says *this child decodes slowly, therefore comprehension collapses on longer text, therefore he avoids reading, therefore he practises less, therefore decoding stays slow, and the teacher has read his avoidance as laziness so the relationship has deteriorated* names five points of intervention and identifies the maintaining loop.

**The generalisable move.** Whenever you are handed a label — "difficult client", "bad site", "toxic team", "legacy system" — ask for the formulation. What predisposed this? What precipitated it? **What is maintaining it right now?** What is protecting against it getting worse? The maintaining-factor question is where the leverage is, and labels systematically hide it.

---

## 12. Hypothesis-driven assessment

The alternative to hypothesis-driven assessment is the shotgun: administer everything, report everything, hope the pattern speaks. It produces long reports, low signal, and — because of the multiple-comparisons problem — a guaranteed crop of spurious "significant" discrepancies.

The disciplined sequence:

1. **Clarify the referral question.** What decision does the referrer need to make?
2. **Generate competing hypotheses.** Not one. If the only hypothesis is the referrer's, the assessment is a confirmation exercise.
3. **For each hypothesis, ask what evidence would support it and — more importantly — what would rule it out.**
4. **Choose instruments and procedures on the basis of that discriminating power**, not on habit or on what is in the cupboard.
5. **Collect, then revise.** Assessment is sequential; each result changes what to do next.
6. **Report the reasoning, not just the results.** A reader should be able to see how you moved from data to conclusion, and where you could be wrong.

This is Bayesian in spirit: start with priors (base rates), gather evidence with known likelihood ratios (which is what sensitivity and specificity are), update. Most applied investigation in any field — debugging, defect diagnosis, medical workup, forensic accounting — has exactly this structure.

---

## 13. "What would falsify this?"

The closing habit, and the one that keeps the rest honest.

Popper's demarcation criterion is philosophically contested and Kuhn and Lakatos both complicated it substantially, but as a **working discipline** it is unmatched: an explanation that accommodates every possible observation explains nothing. Psychoanalysis's classic problem was that resistance and its absence both confirmed the theory. The same structure appears in organisational consulting, in market forecasting, and in every managerial theory that explains success and failure equally well after the fact.

Applied to yourself, the question is: **what observation would make me abandon this belief?** If the answer is "none", you are not holding a hypothesis; you are holding a commitment. That may be fine — some commitments are values, not claims — but you should know which one you have.

Applied to others' claims: **ask what result the proponent would accept as disconfirming.** If a training programme's advocates explain a null trial by saying implementation was poor, and would explain a positive trial as evidence the programme works, the claim is unfalsifiable as stated. This test disposes of a great deal of educational and management fashion very quickly.

**A corollary worth holding.** The willingness to say "I was wrong, that finding did not hold up" is the profession's actual mark of competence. Files `03` and `08` in this folder say it about growth mindset, grit, learning styles, multiple intelligences, priming, ego depletion and the 10,000-hour rule — findings that were taught with confidence and have not survived. Anyone who has never had to revise a belief in their field has not been paying attention to their field.

## Sources

- [Replication crisis](https://en.wikipedia.org/wiki/Replication_crisis) — Wikipedia
- [Learning styles](https://en.wikipedia.org/wiki/Learning_styles) — Wikipedia
- [Crossref](https://api.crossref.org/works) — verified: Open Science Collaboration, "Estimating the reproducibility of psychological science", *Science* 349 (2015), doi:10.1126/science.aac4716; Kluger & DeNisi 1996 doi:10.1037/0033-2909.119.2.254
- [Open Library search API](https://openlibrary.org/search.json) — Internet Archive; Kahneman, *Thinking, Fast and Slow* (2011); Nisbett, *Mindware* (2015)

## Open questions

- Meehl's *Clinical versus Statistical Prediction* (1954) and the subsequent Grove et al. meta-analyses are described from general knowledge; verify the specific effect estimates before citing.
- The bias blind spot literature (Pronin and colleagues) is referenced from general knowledge; verify.
- The US Air Force cockpit example (Gilbert Daniels, 1950s) is widely repeated and is described here from general knowledge; verify the primary source before using it in a formal document.
- Berkson's paradox and collider bias are stated correctly in general terms; a worked epidemiological reference would strengthen this file.
