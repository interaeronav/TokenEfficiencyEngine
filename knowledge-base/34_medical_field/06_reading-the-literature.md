---
id: medical_field.literature
title: Reading the literature — journals, databases, guidelines and a monitoring workflow
domain: 34_medical_field
tags: [journals, nejm, lancet, jama, bmj, pubmed, mesh, cochrane, preprints, medrxiv, guidelines, nice, who, uspstf, predatory-journals, impact-factor, altmetrics, open-access, literature-monitoring]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "The New England Journal of Medicine", url: "https://en.wikipedia.org/wiki/The_New_England_Journal_of_Medicine", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Medical Subject Headings", url: "https://en.wikipedia.org/wiki/Medical_Subject_Headings", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "medRxiv", url: "https://en.wikipedia.org/wiki/MedRxiv", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Predatory publishing", url: "https://en.wikipedia.org/wiki/Predatory_publishing", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Cochrane (organisation)", url: "https://en.wikipedia.org/wiki/Cochrane_(organisation)", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "National Institute for Health and Care Excellence", url: "https://en.wikipedia.org/wiki/National_Institute_for_Health_and_Care_Excellence", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "United States Preventive Services Task Force", url: "https://en.wikipedia.org/wiki/United_States_Preventive_Services_Task_Force", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Novel Drug Approvals for 2025", url: "https://www.fda.gov/drugs/novel-drug-approvals-fda/novel-drug-approvals-2025", publisher: "US FDA", accessed: 2026-08-25}
related: [medical_field.ebm, medical_field.research_practice, medical_field.drug_development]
unit_system: SI
---

# Reading the literature — journals, databases, guidelines and a monitoring workflow

**Summary.** Roughly 1.5 million biomedical records are added to PubMed each year, and no clinician reads more than a rounding error of them. This file maps the landscape: which journals matter and why, how preprints should be treated, how to search PubMed properly with MeSH, what Cochrane does, how guidelines are actually made and where they legitimately conflict, how to recognise a predatory journal, what impact factor and altmetrics do and do not measure, the open-access models, and a personal monitoring workflow that is realistically sustainable. It closes with a set of verified recent developments and their dates.

> ⚠️ Nothing in this file is medical advice. Journals and guidelines are described as objects of study, not as sources to act on without a clinician.

## Key facts

| Item | Detail |
|---|---|
| NEJM founded | **1812**; published by the Massachusetts Medical Society; 2024 impact factor **78.5**, 2nd of 168 in Medicine, General & Internal |
| Ingelfinger rule | NEJM policy that submitted work must not have been published or released elsewhere |
| MeSH size | ≈ **30,000 descriptors** (2025) plus ≈ 318,000 supplementary concept records; **83 qualifiers**; ~10–15 headings indexed per article |
| Cochrane | Founded **1993** (Iain Chalmers); **53 review groups**; **37,000+ contributors**; refuses corporate funding |
| medRxiv | Founded **2019** (CSHL + BMJ + Yale); **>61,000 papers** by December 2024; moved with bioRxiv to the nonprofit **openRxiv** on **11 March 2025** |
| NICE cost-effectiveness threshold | £20,000/QALY, rising scrutiny above **£30,000/QALY**; a 2015 University of York analysis argued for ~£13,000 |
| USPSTF grades | A, B, C, D, I; **Grade A and B services must be covered without cost sharing** by US insurers under the ACA |
| Predatory publishing scale | ~53,000 articles (2010) → ~420,000 (2014); **56%** of predatory-journal articles uncited within 5 years vs 9% for reputable journals |
| FDA CDER novel approvals | **46** in 2025 |

---

## 1. The journals and their standing

### The general medical "big five"

| Journal | Founded | Publisher | Character |
|---|---|---|---|
| ***New England Journal of Medicine*** | 1812 | Massachusetts Medical Society | The most selective venue for practice-changing trials, particularly in cardiology, oncology and infectious disease. 2024 impact factor **78.5**. Enforces the **Ingelfinger rule**. Editorially conservative; its accompanying editorials are influential in their own right. |
| ***The Lancet*** | 1823 | Elsevier | Global in outlook, strong in global health, public health and policy; more willing to publish politically consequential work and more willing to be wrong in public (the 1998 Wakefield MMR paper, retracted 2010; the 2020 "Surgisphere" hydroxychloroquine paper, retracted within weeks). The Lancet family (*Lancet Oncology*, *Infectious Diseases*, *Respiratory Medicine*, *Global Health*, *Psychiatry*, *Digital Health*…) is a major specialty tier. |
| ***JAMA*** | 1883 | American Medical Association | Strong methodology, US health-policy focus, excellent statistical editing, and the *JAMA Network* specialty family (*JAMA Internal Medicine*, *Cardiology*, *Oncology*, *Pediatrics*, *Psychiatry*, *Network Open*). |
| ***The BMJ*** | 1840 | BMJ Group | The most explicitly reformist: open data campaigning, "Too Much Medicine", investigative journalism inside the journal, and open peer review with signed reviews published alongside papers. The best place to read about how medicine goes wrong. |
| ***Annals of Internal Medicine*** | 1927 | American College of Physicians | Rigorous, general-internist audience, home of many guideline and clinical-appraisal series. |

### The scientific tier

*Nature*, *Science* and *Cell* publish the underlying biology. ***Nature Medicine*** is the leading translational venue and the most likely place to see a first-in-human result in a new modality. ***Nature Reviews*** titles (Drug Discovery, Cancer, Immunology, Nephrology…) are the best single-article introductions to a field for someone who needs to become competent quickly. *Science Translational Medicine*, *Cell Metabolism*, *Immunity*, *eLife* and *PLOS Medicine* fill out the tier.

### Specialty leaders (indicative, not exhaustive)

Cardiology: *Circulation*, *European Heart Journal*, *Journal of the American College of Cardiology*. Oncology: *Journal of Clinical Oncology*, *Annals of Oncology*, *Lancet Oncology*, *Cancer Discovery*. Neurology: *Brain*, *Neurology*, *Lancet Neurology*, *Annals of Neurology*. Infectious disease: *Clinical Infectious Diseases*, *Lancet Infectious Diseases*, *Journal of Infectious Diseases*. Psychiatry: *American Journal of Psychiatry*, *JAMA Psychiatry*, *World Psychiatry*, *British Journal of Psychiatry*. Surgery: *Annals of Surgery*, *British Journal of Surgery*, *JAMA Surgery*. Paediatrics: *Pediatrics*, *Archives of Disease in Childhood*, *JAMA Pediatrics*. Obstetrics: *Obstetrics & Gynecology* ("the Green Journal"), *BJOG*, *American Journal of Obstetrics and Gynecology*. Anaesthesia and critical care: *Anesthesiology*, *British Journal of Anaesthesia*, *Intensive Care Medicine*, *Critical Care Medicine*. Radiology: *Radiology*, *European Radiology*. Emergency: *Annals of Emergency Medicine*. Endocrinology: *Diabetes Care*, *Journal of Clinical Endocrinology and Metabolism*, *Lancet Diabetes & Endocrinology*.

### Regional and southern African journals

**[ZA]** The ***South African Medical Journal (SAMJ)*** is the country's general medical journal and the correct first stop for South African epidemiology, health-service research and policy commentary; the ***SA Journal of HIV Medicine***, ***South African Family Practice*** and ***African Journal of Primary Health Care & Family Medicine*** cover their fields. Regionally, the ***African Journal of Emergency Medicine***, ***African Health Sciences*** and the ***Pan African Medical Journal*** are the significant venues. **[NA]** Namibia has no large indigenous medical journal; Namibian clinical research typically appears in South African, regional or international journals, or in the WHO AFRO grey literature.

> A structural point worth stating plainly: work from low- and middle-income countries is systematically under-represented in the high-impact journals, editorial boards are dominated by high-income-country authors, and article processing charges price out exactly the researchers whose populations carry most of the global disease burden. Any reading of "the literature" that stops at the big five is a reading of a rich-country literature.

## 2. Preprints

**medRxiv** was founded in **2019** by John Inglis and Richard Sever (Cold Spring Harbor Laboratory), Theodora Bloom and Claire Rawlinson (BMJ), and Joseph Ross and Harlan Krumholz (Yale). Its sister server **bioRxiv** (2013) covers basic biology. Volume grew from about 10,000 papers by January 2022 to **more than 61,000 by December 2024**. On **11 March 2025** both servers moved from Cold Spring Harbor Laboratory to a new nonprofit, **openRxiv**.

**How to treat a preprint.** A preprint has been screened — for plagiarism, obvious ethical problems, patient identifiability, and whether it is research at all — but **not peer reviewed**. medRxiv screens more conservatively than bioRxiv because clinical claims can cause immediate harm, and it declines to post some categories (for example, work reporting results that could drive self-medication).

Practical rules:
- Read a preprint the way you would read a conference abstract: as a signal that something may exist, not as a finding.
- Check whether it was subsequently published, and **compare the versions** — the numbers frequently change.
- Never change practice on a preprint, and never report one to a patient or the public as established.
- Preprints are genuinely valuable for speed (COVID-19 made this undeniable), for null results that journals reject, and for methods.
- The COVID period also demonstrated the failure mode: preprints amplified by media and social platforms as if peer reviewed, some of which were later withdrawn.

**Related infrastructure.** SSRN's *Preprints with The Lancet*, Research Square, and journal-integrated preprint deposition. **Peer Community In** and **Review Commons** offer independent peer review of preprints, decoupling review from journal acceptance.

## 3. Searching PubMed properly

**PubMed** indexes MEDLINE plus PubMed Central plus some additional records — over 37 million citations. It is free, and it is the default. **Embase** (Elsevier, subscription) has better European and pharmacology coverage and its own thesaurus (Emtree); a proper systematic review searches both, plus **CENTRAL** (Cochrane's trial register), plus registries.

### MeSH

**Medical Subject Headings** is the NLM's controlled vocabulary: approximately **30,000 descriptors** (2025) plus about **318,000 supplementary concept records** for chemicals and drugs, and **83 qualifiers** (subheadings). Terms are arranged both alphabetically and in a **hierarchical tree**, and a descriptor can sit at several tree positions. Human indexers assign roughly **10–15 headings per article**, marking the most important with an asterisk (**Major Topic**).

Mechanics that matter:
- **Automatic term mapping** — a free-text query is silently translated to MeSH plus text words. This is convenient and it is why two people running "the same" search get different results.
- **Explosion** — searching a MeSH term automatically includes everything below it in the tree. `"Neoplasms"[Mesh]` returns every cancer type. To prevent this, use `[Mesh:NoExp]`.
- **Subheadings** — `"Measles/epidemiology"[Mesh]` restricts to the epidemiological aspect.
- **Major topic** — `[Majr]` restricts to articles where the term is a principal subject.
- **Publication types** — `"Randomized Controlled Trial"[Publication Type]`, `"Systematic Review"[Publication Type]`, `"Meta-Analysis"[pt]`, `"Practice Guideline"[pt]`.
- **Indexing lag** — the newest citations are not yet MeSH-indexed. A MeSH-only search misses the last few months, so **every real search combines MeSH terms with free-text `[tiab]` terms**.

### Field tags and operators

`[tiab]` title/abstract · `[ti]` title · `[au]` author · `[ta]` journal · `[dp]` date of publication · `[la]` language · `[pt]` publication type · `[Mesh]`, `[Majr]`, `[Mesh:NoExp]`. Boolean `AND`, `OR`, `NOT` must be uppercase. Truncation with `*` (e.g. `randomi*`) — note that truncation **disables** automatic term mapping. Phrases in double quotes. Parentheses for grouping. The **Clinical Queries** and **Systematic Reviews** filters apply validated search hedges.

### A worked search strategy

**Question (PICO):** In adults with type 2 diabetes and established cardiovascular disease (P), do GLP-1 receptor agonists (I) compared with placebo or standard care (C) reduce major adverse cardiovascular events (O)?

```
#1  "Diabetes Mellitus, Type 2"[Mesh]
#2  (type 2 diabet*[tiab] OR T2DM[tiab] OR "non-insulin-dependent diabet*"[tiab])
#3  #1 OR #2

#4  "Glucagon-Like Peptide-1 Receptor Agonists"[Mesh]
#5  (GLP-1[tiab] OR "glucagon-like peptide 1"[tiab] OR liraglutide[tiab]
     OR semaglutide[tiab] OR dulaglutide[tiab] OR exenatide[tiab]
     OR lixisenatide[tiab] OR albiglutide[tiab] OR tirzepatide[tiab])
#6  #4 OR #5

#7  "Cardiovascular Diseases"[Mesh]
#8  (cardiovascular[tiab] OR MACE[tiab] OR "myocardial infarction"[tiab]
     OR stroke[tiab] OR "cardiovascular death"[tiab])
#9  #7 OR #8

#10 "Randomized Controlled Trial"[Publication Type]
#11 (randomi*[tiab] OR placebo[tiab] OR "double blind"[tiab] OR trial[ti])
#12 #10 OR #11

#13 #3 AND #6 AND #9 AND #12
```

Then: apply no language filter (language restriction is itself a bias); export to a reference manager; **screen titles and abstracts in duplicate**; run the same concept structure against Embase using Emtree terms and against CENTRAL; search ClinicalTrials.gov and the WHO ICTRP for unpublished and ongoing trials; hand-search the reference lists of included studies and any existing systematic reviews; and run a forward citation search in Scopus, Web of Science or Google Scholar on the key included papers. Record every step, every database, every date and every hit count, because **PRISMA requires the full strategy to be reproducible** (see `05`).

**Note the deliberate structure:** each concept block combines a controlled-vocabulary term (`OR`) with free-text synonyms, blocks are combined with `AND`, and the design filter is applied last. That pattern is the whole craft.

### Other tools

- **PubMed's "Similar articles"** and the **"Cited by"** links.
- **Connected Papers**, **ResearchRabbit**, **Litmaps**, **Inciteful** — citation-graph exploration; excellent for finding the shape of a field quickly.
- **Scite** — classifies citations as supporting, mentioning or contrasting; useful for spotting a paper that is widely cited *as refuted*.
- **Retraction Watch Database** (now integrated into Crossref) — check whether anything you are about to rely on has been retracted. This takes seconds and is skipped almost universally.
- **Europe PMC** — PubMed's European counterpart, with preprint indexing and better full-text search.
- **Google Scholar** — best recall, worst precision, no reproducibility; fine for finding a known item, unacceptable as the sole search for a review.

## 4. Cochrane

**Cochrane** was founded in **1993** under Iain Chalmers as a British-registered international charity, named for Archie Cochrane, whose 1972 *Effectiveness and Efficiency* argued that medicine should organise a critical summary of all relevant randomised trials. It comprises **53 review groups** hosted at research institutions and over **37,000 contributors** worldwide. Its output is published in the **Cochrane Library**, whose central component is the *Cochrane Database of Systematic Reviews*, alongside CENTRAL.

Distinctives: mandatory published protocols; standardised methods (the *Cochrane Handbook*, RoB 2, GRADE, Summary of Findings tables); plain-language summaries; and a policy of **not accepting commercial funding**. Funders include the UK NIHR, the Danish Health Authority, the German Federal Ministry of Health, the NIH, and several universities.

Honest limitations: reviews are slow and frequently out of date; the emphasis on randomised evidence produces many "insufficient evidence to draw conclusions" verdicts that are correct but unhelpful at the bedside; and the organisation has had significant governance turbulence, most publicly the 2018 expulsion of Peter Gøtzsche from the board after his criticism of a Cochrane HPV vaccine review, followed by four board resignations and structural reform.

Many countries hold **national licences** giving free public access to the Cochrane Library; access in low- and middle-income countries also runs through **HINARI/Research4Life**.

## 5. Guidelines: how they are made and where they conflict

### The bodies

- **NICE** (England, with influence in Wales and Northern Ireland) — a non-departmental public body under the Department of Health and Social Care. It issues technology appraisals, clinical guidelines, public health and social care guidance. Its **technology appraisal** process runs: topic selection → referral by the Secretary of State → scope development → evidence assessment by an independent academic centre → independent Appraisal Committee → **appraisal consultation document** → stakeholder consultation → **final appraisal determination**. Cost-effectiveness is expressed in **cost per QALY**, with a conventional acceptability threshold around **£20,000** and increasingly strong justification required above **£30,000**; a higher threshold has been permitted for end-of-life treatments since 2008. A 2015 University of York analysis argued the threshold should be roughly halved to **£13,000** on the grounds that spending above the true opportunity cost denies more health elsewhere in the NHS than it buys. NICE guidance is the clearest example anywhere of explicit, published rationing.
- **WHO** — global normative guidance, GRADE-based, produced by guideline development groups under the Guidelines Review Committee. WHO guidance carries an explicit equity and feasibility orientation and is often written to be implementable in low-resource settings, which sometimes puts it at odds with high-income-country guidance built on the same evidence.
- **USPSTF** — an independent volunteer panel of primary care and prevention experts, supported by AHRQ, that grades preventive services **A, B, C, D or I**. Under the Affordable Care Act, **Grade A and B recommendations must be covered by US insurers without cost sharing**, "regardless of how much it costs or how small the benefit is" — a statutory link that makes an ostensibly scientific body a de facto coverage authority and has drawn litigation and political pressure. Its April 2024 lowering of the breast-cancer screening starting age from 50 to 40 is a recent illustration of how consequential a grade change is.
- **Specialty societies** — ACC/AHA, ESC, IDSA, ADA, ASCO, NCCN, GOLD, KDIGO, ERS/ATS, RCOG, and dozens more. These are usually faster and more clinically detailed than the national bodies, and more exposed to conflict of interest because the expert authors are frequently trial investigators funded by the manufacturers whose products they are evaluating.
- **[ZA]** South Africa's **Essential Medicines List and Standard Treatment Guidelines**, produced by the National Essential Medicines List Committee, are the operative guidance in the public sector and are explicitly resource-constrained. **[NA]** Namibia maintains its own Essential Medicines List and standard treatment guidelines under the Ministry of Health and Social Services, and additionally follows WHO AFRO guidance.

### Why guidelines conflict

Two competent panels reading the same evidence can and do reach different recommendations, for reasons that are mostly legitimate:

1. **Different questions.** "Should this be offered to everyone?" is not "does it work?"
2. **Different thresholds for action.** GRADE separates certainty from strength precisely because the same certainty supports different recommendations under different values.
3. **Different value judgements** about how to weigh a small mortality benefit against a large burden of testing, cost or harm.
4. **Different cost contexts.** NICE's £/QALY threshold, the WHO's implementability constraint and a US society's cost-blind stance produce different answers by design.
5. **Different evidence cut-off dates.** A guideline is a snapshot, and a major trial published two months after the search date will not be in it.
6. **Composition and conflicts of interest.** Panels heavy with proceduralists recommend procedures.

The commonly cited examples of real divergence — screening ages for breast, prostate and colorectal cancer; blood-pressure treatment thresholds after the 2017 ACC/AHA redefinition versus the ESC and NICE positions; PSA screening; hormone therapy — are all reducible to one or more of the six causes above rather than to one side being unscientific.

**Practical reading rule:** when guidelines conflict, do not average them. Find the recommendation's underlying evidence, check the certainty rating, and look at whose values and which cost context were applied. **AGREE II** is the instrument for appraising a guideline's development quality, and **GIN** (the Guidelines International Network) hosts a registry.

## 6. Predatory journals

**Definition:** journals that charge article processing fees while providing little or no genuine editorial or peer-review service, and misrepresent their practices.

**Warning signs:** aggressive and flattering solicitation email; promises of publication within days; hidden or post-acceptance-disclosed fees; an editorial board of unverifiable people, or real people listed without consent; a fabricated or non-standard "impact factor" (look for invented metrics with names resembling the real Journal Impact Factor); a scope so broad it is meaningless; poor website quality and grammatical errors; a postal address that does not exist; articles obviously outside the stated scope; and no listed policy on retraction, archiving or plagiarism.

**History and scale.** Librarian Jeffrey Beall coined the term around 2012 and maintained an influential blacklist until closing it in 2017 under employer pressure; the list was criticised for sweeping in legitimate open-access journals from developing countries, and unofficial updated versions persist. Volume estimates: about **53,000 articles in 2010** rising to roughly **420,000 in 2014**. About **56%** of predatory-journal articles are uncited within five years, versus **9%** for reputable journals. John Bohannon's 2013 *Science* sting ("Who's Afraid of Peer Review?") saw a deliberately flawed paper accepted by around 60% of the outlets it was sent to.

**How to check a journal before submitting or citing:**
1. Is it indexed in **MEDLINE/PubMed**, **Scopus**, or **Web of Science**? (Note: presence in PubMed Central alone is *not* the same as MEDLINE indexing.)
2. Is it in the **DOAJ** (Directory of Open Access Journals), which now applies substantive criteria?
3. Is the publisher a member of **COPE**, **OASPA** or **STM**?
4. Does **Think. Check. Submit.** (thinkchecksubmit.org) clear it?
5. Do you recognise anyone on the editorial board, and does their institutional page mention the role?

COPE's own position is that institutions should educate rather than rely on blacklists, because binary lists produce both false positives (harming legitimate journals in low-income countries) and false negatives.

**Adjacent problems:** hijacked journals (a clone site impersonating a real journal), paper mills selling authorship on fabricated manuscripts, citation cartels, and predatory conferences.

## 7. Impact factor, altmetrics and what they measure

**Journal Impact Factor (JIF)** — Clarivate's metric: citations in year Y to items published in Y−1 and Y−2, divided by the number of "citable items" in those two years. What it actually is: a *journal-level* average of a wildly skewed distribution, in which a small number of papers supply most citations. What it is routinely misused for: judging individual papers, individual researchers, hiring and promotion. Known distortions: the numerator counts citations to everything (editorials, letters) while the denominator counts only "citable items", giving editors leverage; review journals score higher than research journals; field norms differ by an order of magnitude; and journals can and do negotiate their denominators. The **San Francisco Declaration on Research Assessment (DORA, 2012)** and the **Leiden Manifesto (2015)** are the formal repudiations, signed by thousands of institutions that in many cases still use JIF anyway.

**Alternatives at journal level:** Scopus **CiteScore**, **SJR** (SCImago Journal Rank, prestige-weighted), **SNIP** (field-normalised), and the **Eigenfactor**. At author level, the **h-index** (and its many variants), which rewards sustained mid-level output and penalises early-career and interdisciplinary researchers.

**Altmetrics** — attention counts from news, blogs, policy documents, Wikipedia, patents, social platforms and reference managers, aggregated by **Altmetric.com** (the coloured donut) and **PlumX**. What they measure is **attention**, which correlates weakly with quality and strongly with novelty, controversy and press-release energy. Their genuine uses: detecting policy uptake and news distortion early, and finding the post-publication critique that never enters the citation record. Their misuse: treating attention as impact.

**Post-publication review** — **PubPeer** is the significant venue and has been the origin of a large share of recent image-manipulation and data-integrity investigations, including several that ended senior careers. Checking PubPeer alongside Retraction Watch is a two-minute due-diligence step before building on any paper.

## 8. Open access models

| Model | Who pays | Notes |
|---|---|---|
| **Gold** | Author or funder, via an **article processing charge (APC)** | Immediate free access on the publisher's site. APCs at high-prestige journals commonly run US$3,000–12,000, which excludes unfunded authors and most LMIC researchers. Waiver schemes exist and are inconsistently applied. |
| **Green** | Nobody directly | Author self-archives the accepted manuscript in a repository (PubMed Central, an institutional repository, Europe PMC), often after an embargo of 6–12 months. |
| **Diamond / Platinum** | An institution, society or consortium | Free to read and free to publish. The fastest-growing and least-discussed model; most journals in Latin America (SciELO, Redalyc) and many in Africa operate this way. |
| **Hybrid** | Author optionally, on top of subscription | A subscription journal with a paid-OA option. Widely criticised as "double dipping". |
| **Bronze** | Publisher, discretionarily | Free to read but with no licence granting reuse, and revocable. |
| **Transformative agreements** ("read and publish") | Institutional consortium | National deals (Germany's DEAL, Jisc in the UK) converting subscription spend into publishing rights. |

**Mandates.** Plan S (cOAlition S) required immediate OA under a CC BY licence for funded research; the US **OSTP "Nelson memo" (August 2022)** directed federal agencies to require immediate public access to federally funded publications and their data, with implementation by the end of 2025; the NIH and Wellcome have their own policies. **[ZA]** The NRF has an open-access mandate, and SciELO South Africa hosts a substantial diamond-OA corpus.

**Sci-Hub** exists, is illegal in most jurisdictions, and is used heavily including by researchers at well-resourced institutions — a fact that is itself the most-cited evidence about how badly subscription access serves working clinicians.

## 9. A personal literature-monitoring workflow

The realistic goal is not to read the literature but to **not miss the things that would change what you do**. A sustainable system:

**Layer 1 — Push, weekly, ~20 minutes.**
- **NEJM Journal Watch**, **BMJ Evidence-Based Medicine**, the **ACP Journal Club** section of *Annals*, or **McMaster PLUS / Evidence Alerts** — all are pre-appraised: a small number of clinicians read broadly, apply explicit criteria and summarise what survived. This is the highest-yield hour in the whole enterprise.
- Specialty society email alerts and your national body's guidance updates.
- One or two well-run newsletters or podcasts in your field.

**Layer 2 — Saved searches, weekly, automated.**
- **PubMed My NCBI** saved searches with email alerts, using the concept-block structure above, restricted with a publication-type or Clinical Queries filter.
- **Journal tables of contents** by RSS for 3–6 journals maximum, read by title only.
- **Google Scholar alerts** on your own key papers and on two or three critical citations (forward-citation monitoring catches refutations).
- **Retraction Watch** feed.

**Layer 3 — Pull, on demand.**
- The point-of-care resources in `04` for clinical questions.
- PubMed/Cochrane for the deeper question.
- Citation-graph tools when entering a new area.

**Layer 4 — Capture.**
- A reference manager (**Zotero** free and open source, **Mendeley**, **EndNote**, **Paperpile**) with a browser connector, PDF storage and a citation plugin. Tag by question, not by journal.
- A notes system holding *your* summary of each paper — the effect size, the ARR you computed, the flaw you noticed — because in two years you will remember that you read something and nothing else about it.

**Discipline rules that make it survivable:** cap total time; read title-only for 90% of items; go straight to the results table for the 10% you open; never read an abstract's conclusion first; and delete alerts that have not produced a useful hit in three months.

## 10. Recent developments, verified with dates

Each item below was verified against the source listed in `## Sources`.

- **FDA novel approvals, 2025.** CDER approved **46 novel drugs** in 2025. Named examples with their approval dates: **Datroway** (datopotamab deruxtecan-dlnk), 17 January 2025, for unresectable or metastatic HR-positive/HER2-negative breast cancer; **Journavx** (suzetrigine), 30 January 2025, a **non-opioid** treatment for moderate-to-severe acute pain and the first in a new mechanistic class for pain in decades; **Qfitlia** (fitusiran), 28 March 2025, an siRNA therapy for haemophilia A or B; **Lynkuet** (elinzanetant), 24 October 2025, for menopausal vasomotor symptoms; **Nereus** (tradipitant), 30 December 2025.
- **CRISPR therapeutics reached the clinic.** **Casgevy** (exagamglogene autotemcel), the first approved CRISPR-Cas9 gene-editing therapy, from Vertex and CRISPR Therapeutics: **MHRA November 2023**, Bahrain 2 December 2023, **FDA December 2023** (sickle cell disease with recurrent vaso-occlusive crises), **FDA January 2024** (transfusion-dependent β-thalassaemia), **EMA February 2024**. In trials **93.5%** of evaluable participants were free of severe vaso-occlusive crises for at least 12 consecutive months. US list price **US$2.2 million**.
- **GLP-1 expansion continued.** **Tirzepatide** was approved for type 2 diabetes (Mounjaro, May 2022), chronic weight management (Zepbound, November 2023) and **moderate-to-severe obstructive sleep apnoea (December 2024)**. SURMOUNT-1 reported mean weight reduction of **−15.0%, −19.5% and −20.9%** at 5, 10 and 15 mg over 72 weeks versus **−3.1%** for placebo. A three-year study reported in August 2024 found a **94%** reduction in progression to type 2 diabetes in adults with obesity or overweight.
- **Semaglutide's cardiovascular and hepatic indications.** The **SELECT** trial (17,604 participants, ~48 months) reported MACE in **6.5%** versus **8.0%** on placebo (RRR ≈ 18.8%; ARR 1.5 points; NNT ≈ 67). Wegovy gained a cardiovascular indication in **March 2024**; an **oral formulation was approved in December 2025**; and **Kayshild** was approved in the **EU in March 2026** for metabolic-associated steatohepatitis.
- **AI in structural biology matured and was recognised.** **AlphaFold 3** was released in **May 2024**, extending prediction to complexes of proteins with DNA, RNA, ligands and ions with a reported minimum 50% accuracy improvement for protein–other-molecule interactions. The **2024 Nobel Prize in Chemistry** went half to Demis Hassabis and John Jumper for protein structure prediction and half to David Baker for computational protein design. The AlphaFold Protein Structure Database covers **~200 million proteins from 1 million species** (since July 2022).
- **Reporting standards updated.** **CONSORT 2025** revised the 2010 statement: seven new items, three modified, one removed, and a new **open-science section** covering trial registration, protocol access, data sharing and disclosures.
- **Preprint infrastructure changed hands.** **bioRxiv and medRxiv moved to the new nonprofit openRxiv on 11 March 2025.**
- **WHO published a new AMR action plan.** The updated **Global Action Plan on Antimicrobial Resistance (2026–2036)** targets a **10% reduction in AMR-associated deaths by 2030**, on a base of an estimated **4.7 million deaths associated with bacterial AMR in 2021** and roughly **one in six** laboratory-confirmed bacterial infections showing resistance in 2023.
- **Global HIV and TB figures.** End-2025: **41.0 million** people living with HIV, **64%** in the WHO African Region; **1.2 million** new infections and **570,000** deaths in 2025; the 95-95-95 cascade stood at **88% diagnosed, 89% of those on ART, 95% of those virally suppressed**. TB in 2024: **10.7 million** people ill and **1.23 million** deaths, still the leading cause of death from a single infectious agent; only about **two in five** people with drug-resistant TB accessed treatment, though **~34,000** started shorter 6-month MDR/RR-TB regimens.

## Sources

- [The New England Journal of Medicine](https://en.wikipedia.org/wiki/The_New_England_Journal_of_Medicine) — Wikipedia, accessed 2026-08-25
- [Medical Subject Headings](https://en.wikipedia.org/wiki/Medical_Subject_Headings) — Wikipedia, accessed 2026-08-25
- [medRxiv](https://en.wikipedia.org/wiki/MedRxiv) — Wikipedia, accessed 2026-08-25
- [Predatory publishing](https://en.wikipedia.org/wiki/Predatory_publishing) — Wikipedia, accessed 2026-08-25
- [Cochrane (organisation)](https://en.wikipedia.org/wiki/Cochrane_(organisation)) — Wikipedia, accessed 2026-08-25
- [National Institute for Health and Care Excellence](https://en.wikipedia.org/wiki/National_Institute_for_Health_and_Care_Excellence) — Wikipedia, accessed 2026-08-25
- [United States Preventive Services Task Force](https://en.wikipedia.org/wiki/United_States_Preventive_Services_Task_Force) — Wikipedia, accessed 2026-08-25
- [Consolidated Standards of Reporting Trials](https://en.wikipedia.org/wiki/Consolidated_Standards_of_Reporting_Trials) — Wikipedia, accessed 2026-08-25
- [Novel Drug Approvals for 2025](https://www.fda.gov/drugs/novel-drug-approvals-fda/novel-drug-approvals-2025) — US FDA, accessed 2026-08-25
- [Exagamglogene autotemcel (Casgevy)](https://en.wikipedia.org/wiki/Exagamglogene_autotemcel) — Wikipedia, accessed 2026-08-25
- [Tirzepatide](https://en.wikipedia.org/wiki/Tirzepatide) — Wikipedia, accessed 2026-08-25
- [Semaglutide](https://en.wikipedia.org/wiki/Semaglutide) — Wikipedia, accessed 2026-08-25
- [AlphaFold](https://en.wikipedia.org/wiki/AlphaFold) — Wikipedia, accessed 2026-08-25
- [Antimicrobial resistance fact sheet](https://www.who.int/news-room/fact-sheets/detail/antimicrobial-resistance) — WHO, accessed 2026-08-25
- [HIV and AIDS fact sheet](https://www.who.int/news-room/fact-sheets/detail/hiv-aids) — WHO, accessed 2026-08-25
- [Tuberculosis fact sheet](https://www.who.int/news-room/fact-sheets/detail/tuberculosis) — WHO, accessed 2026-08-25

## Open questions

- Founding years for *The Lancet* (1823), *JAMA* (1883), *The BMJ* (1840) and *Annals of Internal Medicine* (1927), and impact factors for journals other than NEJM, are stated from general reference knowledge and were **not** verified in this pass.
- The PubMed record-count figure (>37 million) and the annual accession rate (~1.5 million) were not verified against NLM in this pass.
- DORA (2012), the Leiden Manifesto (2015), Plan S and the OSTP Nelson memo (August 2022) are named from general reference knowledge — verify dates before citing.
- **[ZA]/[NA]** Current editions of the South African Standard Treatment Guidelines / EML and the Namibian equivalents were not retrieved; check the respective health departments.
- The description of medRxiv's screening policy is a characterisation, not a quotation from its published policy — check medrxiv.org/about.
