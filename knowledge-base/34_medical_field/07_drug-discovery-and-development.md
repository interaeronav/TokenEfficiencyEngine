---
id: medical_field.drug_development
title: Drug discovery and development — from target to market
domain: 34_medical_field
tags: [drug-discovery, target-validation, high-throughput-screening, medicinal-chemistry, admet, rule-of-five, preclinical, ind, clinical-trials, fda, ema, accelerated-approval, orphan-drug, cmc, pharmacovigilance, patents, generics, biosimilars, mrna, car-t, crispr, sirna, glp-1, ai-drug-discovery]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Drug development", url: "https://en.wikipedia.org/wiki/Drug_development", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Lipinski's rule of five", url: "https://en.wikipedia.org/wiki/Lipinski%27s_rule_of_five", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Accelerated approval (FDA)", url: "https://en.wikipedia.org/wiki/Accelerated_approval", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Hatch-Waxman Act", url: "https://en.wikipedia.org/wiki/Hatch-Waxman_Act", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Biosimilar", url: "https://en.wikipedia.org/wiki/Biosimilar", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "mRNA vaccine", url: "https://en.wikipedia.org/wiki/MRNA_vaccine", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Chimeric antigen receptor T cell", url: "https://en.wikipedia.org/wiki/Chimeric_antigen_receptor_T_cell", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Exagamglogene autotemcel", url: "https://en.wikipedia.org/wiki/Exagamglogene_autotemcel", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "AlphaFold", url: "https://en.wikipedia.org/wiki/AlphaFold", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Novel Drug Approvals for 2025", url: "https://www.fda.gov/drugs/novel-drug-approvals-fda/novel-drug-approvals-2025", publisher: "US FDA", accessed: 2026-08-25}
related: [medical_field.ebm, medical_field.research_practice, medical_field.health_systems]
unit_system: SI
---

# Drug discovery and development — from target to market

**Summary.** Turning a biological idea into a licensed medicine takes over a decade, costs somewhere between one and three billion US dollars per approved product depending on whose accounting you accept, and fails about nine times out of ten from first human dosing. This file walks the pipeline: target identification and validation, hit discovery, lead optimisation, preclinical work and its translational failure rate, the regulatory gates, the clinical phases with their real sizes and success rates, manufacturing, pharmacovigilance, the economics of cost, patents and pricing — and then the modality landscape from small molecules to CRISPR, with an honest account of where AI has and has not delivered.

> ⚠️ Nothing here is medical advice, and no drug named in this file is recommended for anyone. Drugs are discussed as objects of an industrial and regulatory process.

## Key facts

| Item | Figure | Source |
|---|---|---|
| Overall success, Phase I → approval | **9.6%** (2006–2015); vaccines **16%** | BIO/Wikipedia |
| Historic comparison (1980s–90s) | **21.5%** of drugs entering Phase I approved | Wikipedia |
| Typical time, concept → approval | **>10 years** | Wikipedia |
| Capitalised cost per approval | **US$2.6 bn** (DiMasi 2016); **US$1.1 bn** (Wouters 2020) | Wikipedia |
| Cost by class | Orphan drugs **US$291 m**; cell and gene therapies up to **US$1.8 bn** | Wikipedia |
| Mean phase costs | Phase I **US$25 m**; Phase II **US$59 m**; Phase III **US$255–345 m** | Wikipedia |
| Lipinski's rule of five | MW <500 Da; logP ≤5; H-bond donors ≤5; acceptors ≤10; ≤1 violation | Lipinski, 1997 |
| Compliance in practice | Only ~**50%** of orally administered new chemical entities obey it | Wikipedia |
| FDA accelerated approval established | **1992** | Wikipedia |
| Hatch-Waxman | **1984**; 5-year NCE exclusivity; 180-day first-filer generic exclusivity; 30-month stay | Wikipedia |
| Generic prescription share (US) | 13% (1983) → **84%** (2012) | Wikipedia |
| Biosimilars approved | **60** by FDA (Oct 2024); **>50** EMA authorisations since 2006 | Wikipedia |
| FDA CDER novel approvals 2025 | **46** | FDA |

---

## 1. Target identification and validation

A **target** is a molecular entity — usually a protein — whose modulation is expected to change the course of a disease. Sources of targets:

- **Human genetics.** The strongest single source. Loss-of-function variants that protect against disease are the gold standard: *PCSK9* (protective LOF → evolocumab, alirocumab, inclisiran), *SLC30A8*, *ANGPTL3*, *LPA*. Analyses of pipeline attrition repeatedly find that targets with human genetic support are roughly twice as likely to survive to approval.
- **Disease biology and pathway analysis** — the classical route (HMG-CoA reductase for cholesterol synthesis, ACE for blood pressure).
- **Functional genomics screens** — genome-wide CRISPR knockout, CRISPRi/CRISPRa and RNAi screens for dependencies, especially in oncology (the Cancer Dependency Map).
- **Phenotypic screening**, where the target is identified afterwards (or never).
- **Immunology and the immune synapse** — the checkpoint targets CTLA-4 and PD-1/PD-L1.

**Target validation** asks: does modulating this target change the disease phenotype, in a system that resembles the human disease, and is the effect on-target? Tools: genetic knockout and knockdown, conditional and inducible models, chemical probes with proven selectivity, human tissue and organoid systems, and — the closest thing to a natural experiment — Mendelian randomisation using variants in the target gene as instruments for lifelong modulation.

**The druggable genome.** Hopkins and Groom's 2002 estimate put the small-molecule-druggable fraction of the ~20,000 human protein-coding genes at around 3,000, intersecting with disease-relevant genes to give perhaps 600–1,500 realistic targets. Enzyme classes (kinases, proteases, GPCRs, ion channels, nuclear receptors) dominate. Two developments have since expanded the space:

- **New modalities** reach targets small molecules cannot — antibodies for extracellular targets, oligonucleotides for any transcript, and degraders and molecular glues for proteins with no catalytic pocket.
- **"Undruggable" targets have fallen.** KRAS G12C, considered untouchable for three decades, yielded to covalent inhibitors (sotorasib, adagrasib) exploiting the mutant cysteine.

Roughly **20% of the proteome remains completely uncharacterised** ("the dark proteome"), which is both a failure and an opportunity; the NIH Illuminating the Druggable Genome programme exists for that reason.

## 2. Hit discovery

A **hit** is a compound with measurable, reproducible activity against the target.

- **High-throughput screening (HTS).** Robotic assay of 10⁵–10⁶ compounds from a corporate or academic library in miniaturised (384- or 1536-well) format. Hit rates are typically 0.01–1%. Requires a robust, miniaturisable, cheap assay with a good Z′-factor. The chronic problem is **PAINS** (pan-assay interference compounds) — aggregators, redox cyclers, chelators and fluorescence artefacts that look active against everything.
- **Fragment-based drug discovery (FBDD).** Screens very small molecules (<300 Da, the "rule of three"), which bind weakly (mM–µM) but with high **ligand efficiency**, then grows or links them. Requires sensitive biophysical detection: X-ray crystallography, NMR, surface plasmon resonance, thermal shift, native mass spectrometry. Vemurafenib is the canonical FBDD-derived success.
- **DNA-encoded libraries (DEL).** Each compound is covalently tagged with a DNA barcode recording its synthetic history; libraries of 10⁸–10¹² compounds are screened in a single tube by affinity selection, and the bound population is identified by sequencing. Enormously efficient in chemical space per experiment; the cost is that the DNA tag can influence binding and hits must be resynthesised off-DNA and re-validated.
- **Virtual screening.** Structure-based docking of large virtual libraries against the target's binding site, now at the scale of billions of make-on-demand compounds (Enamine REAL and similar). Combined with active-learning triage, this has produced genuine, experimentally confirmed hits at low cost. Ligand-based approaches (pharmacophore models, similarity searching, QSAR) apply when no structure is available.
- **Phenotypic screening.** Screens for a cellular or organismal phenotype without a defined target. Historically the source of most first-in-class drugs, and enjoying a revival because target-based screening has a poor record of producing genuinely novel mechanisms. The cost is **deconvolution** — identifying what the compound actually hits, via chemoproteomics, resistance-mutation selection or genome-wide screens.
- **Natural products.** Still the origin of a large fraction of antibiotics and anticancer agents; supply, complexity of synthesis and rediscovery of known compounds are the standing barriers.
- **Repurposing.** Screening approved drugs for new indications: fast, cheap, safety already characterised, but with weak intellectual property and therefore weak commercial incentive.

## 3. Lead optimisation and medicinal chemistry

Hits become **leads**, and leads become **candidates**, through iterative design–make–test–analyse cycles.

**Structure–activity relationship (SAR).** Systematic modification of the scaffold, mapping which substitutions increase potency, which are tolerated and which kill activity. **Structure-based design** uses co-crystal structures to reason about the interactions being formed. **Bioisosteric replacement** swaps a group for one with similar properties but better metabolic or physicochemical behaviour.

**The competing objectives.** Optimisation is multi-parameter, and improving one property usually degrades another:

- **Potency and selectivity** against the target and against the off-target panel (kinase panels, the hERG channel, CYP enzymes, the safety pharmacology receptor screen).
- **ADME** — Absorption, Distribution, Metabolism, Excretion. Measured through solubility, permeability (Caco-2, PAMPA), metabolic stability in liver microsomes and hepatocytes, plasma protein binding, transporter interactions (P-glycoprotein, BCRP, OATP), and in-vivo pharmacokinetics giving clearance, volume of distribution, half-life and oral bioavailability.
- **Toxicity (the T in ADMET)** — cytotoxicity, genotoxicity (Ames test, micronucleus), hERG-mediated QT prolongation, hepatotoxicity signals, reactive metabolite formation.
- **Developability** — can it be made at scale, is it crystalline and stable, does it have a workable salt or polymorph, can it be formulated.

**Lipinski's rule of five (1997).** An orally active drug tends to have **no more than one** violation of: ≤5 hydrogen-bond donors; ≤10 hydrogen-bond acceptors; molecular mass <500 Da; logP ≤5. It is a *descriptive generalisation about attrition*, not a law, and it is routinely and correctly broken: only about **50% of orally administered new chemical entities** obey it, and natural products such as macrolides and cyclic peptides violate it while remaining orally active. Its blind spot is that it assumes passive diffusion and ignores transporter-mediated uptake. Companion heuristics: **Veber's rule** (polar surface area ≤140 Å², rotatable bonds ≤10), the **Ghose filter**, and the **rule of three** for fragments (logP ≤3, MW <300 Da, ≤3 donors/acceptors/rotatable bonds). **"Beyond rule of five" (bRo5)** is now a recognised design space for macrocycles, PROTACs and peptides that achieve oral exposure through conformational chameleonicity.

Discovery to candidate typically takes **3–6 years** and consumes thousands of synthesised compounds.

## 4. Preclinical development

**In vitro.** Target engagement, mechanism, selectivity, and the full ADMET package above, plus species comparison of metabolism to choose the toxicology species.

**Animal models and their translational record.** Efficacy models — xenografts and genetically engineered models in oncology, disease models in inflammation, neurology, metabolism — are the weakest link in the chain. The honest summary:

- Concordance between animal efficacy and human efficacy is poor in most therapeutic areas, and worst in neurology, psychiatry, sepsis and stroke. Well over a hundred neuroprotective agents effective in rodent stroke models failed in humans.
- Preclinical studies are frequently underpowered, unblinded, unrandomised and selectively reported. The CAMARADES and related meta-research groups have documented effect inflation of the same kind seen in clinical trials.
- The **ARRIVE guidelines** (and ARRIVE 2.0) exist to fix the reporting; uptake is partial.
- Regulatory acceptance of alternatives has changed: the **FDA Modernization Act 2.0 (2022)** removed the statutory requirement for animal testing specifically, allowing cell-based assays, organ-on-chip and computational models as alternatives — a permission, not a replacement, and its practical effect so far is modest.
- The commonly cited "over 90% of drugs that pass animal testing fail in humans" figure is a restatement of the Phase-I-to-approval attrition rate and should be quoted with that framing rather than as an independent measurement.

**Toxicology.** Conducted under **Good Laboratory Practice (GLP)** — a data-integrity regime covering facilities, personnel, SOPs, study directors, raw-data retention and quality assurance. Core package for a small molecule: single-dose and repeat-dose toxicity in one rodent and one non-rodent species (typically rat and dog, or non-human primate for biologics), of duration matched to intended clinical exposure; safety pharmacology (cardiovascular including hERG and telemetry, respiratory, CNS — ICH S7A/S7B); genotoxicity (ICH S2); reproductive and developmental toxicity; and, for chronic use, carcinogenicity bioassays. The outputs are the **NOAEL** (no-observed-adverse-effect level) and, from it, the **maximum recommended starting dose** for first-in-human, derived by allometric scaling with a safety factor (typically 10×) under FDA guidance; for high-risk biologics the **MABEL** (minimum anticipated biological effect level) approach is used instead — a direct consequence of the 2006 TGN1412 disaster, in which six healthy volunteers suffered life-threatening cytokine release at a dose 500-fold below the primate NOAEL.

**Chemistry, Manufacturing and Controls (CMC)** begins here: route scale-up, impurity profiling and qualification, polymorph screening, stability studies, analytical method validation, and formulation. CMC is the most common cause of *delay* in development even when it is rarely the cause of *failure*.

## 5. The regulatory gate into humans

**[US] IND — Investigational New Drug application.** Submitted to the FDA with three content pillars: animal pharmacology and toxicology; manufacturing information; and clinical protocols with investigator qualifications. A **30-day safety review** runs from submission; if the FDA does not place a **clinical hold**, the trial may begin. IND types: investigator, commercial, emergency use, treatment (expanded access). A **pre-IND meeting** with the agency is standard practice and materially reduces the risk of a hold.

**[EU] CTA — Clinical Trial Application.** Since the **Clinical Trials Regulation (EU) No 536/2014** came into application on **31 January 2022**, applications go through the single **Clinical Trials Information System (CTIS)** portal, assessed jointly by the member states concerned, replacing the old country-by-country Directive 2001/20/EC process. **[UK]** The MHRA operates its own combined review with the Research Ethics Committee.

**[ZA]** Clinical trials are authorised by **SAHPRA** (the South African Health Products Regulatory Authority, which replaced the Medicines Control Council in 2018) with parallel approval from a registered Research Ethics Committee, and must be registered on the **South African National Clinical Trial Register**. **[NA]** The Namibia Medicines Regulatory Council and the Ministry of Health and Social Services research ethics process perform the equivalent function; Namibian trial activity is small and usually part of multi-country studies.

## 6. The clinical phases

| Phase | Population | Typical n | Typical duration | Primary question | Approx. success to next phase |
|---|---|---|---|---|---|
| **Phase 0 / microdose** | Healthy or patients | 10–15 | Weeks | Does it distribute as predicted (subtherapeutic dosing)? | Not a standard step |
| **Phase I** | Healthy volunteers (patients in oncology) | 20–100 | 6–18 months | Safety, tolerability, PK, maximum tolerated dose | ~50–65% |
| **Phase II** | Patients with the disease | 100–500 | 1–3 years | Does it work at all; dose-finding; short-term safety | ~30% (the "valley of death") |
| **Phase III** | Patients, multicentre, often multinational | 300–5,000+ (CV outcome trials 10,000–20,000+) | 2–5 years | Confirmatory efficacy and safety versus control | ~55–65% |
| **Regulatory review** | — | — | 6–12 months (US), 12–15 months (EU) | Benefit–risk | ~85–90% |
| **Phase IV** | Post-approval | Thousands to millions | Ongoing | Rare harms, long-term outcomes, real-world effectiveness | — |

**Phase I detail.** Single ascending dose then multiple ascending dose, with pre-specified stopping rules, sentinel dosing (one or two participants dosed ahead of the cohort), and staggered administration. Food effect, drug–drug interaction and special-population (hepatic, renal impairment) studies sit here. In oncology and for cytotoxic or high-risk agents, Phase I recruits **patients**, not healthy volunteers, because the risk is not justifiable in the healthy — and the traditional 3+3 dose-escalation design is being replaced by model-based designs (CRM, BOIN, mTPI) that are statistically better behaved.

**Phase II detail.** Often split into IIa (proof of concept, sometimes single-arm) and IIb (dose-ranging, randomised, controlled). This is where most compounds die, and the commonest reason is **lack of efficacy** — the target was wrong, or modulating it does not change the disease. The second commonest is unexpected toxicity; the document consulted for this file notes roughly **50% failure of Phase II cardiology trials** attributed to unknown toxic side effects, together with inadequate financing, weak trial design and poor execution.

**Phase III detail.** The pivotal, registrational trials — usually two adequate and well-controlled trials, or one plus confirmatory evidence. Everything in `05_evidence-based-medicine.md` applies: randomisation and concealment, blinding, a pre-specified primary endpoint, ITT analysis, an independent DSMB, and prospective registration. The **choice of comparator** is where commercial interest and scientific interest diverge most sharply.

**Phase IV and post-marketing requirements.** Trials mandated by the regulator as a condition of approval, plus voluntary studies, registries, and the pharmacovigilance system described below.

**Adaptive and platform trials.** Pre-specified rules allow modification during the trial: dropping futile arms, response-adaptive randomisation, sample-size re-estimation, seamless Phase II/III transition, and Bayesian decision rules. **Platform trials** run a shared master protocol and control arm against multiple interventions entering and leaving over time — **RECOVERY** (UK, COVID-19; identified dexamethasone's mortality benefit within months and definitively excluded hydroxychloroquine), **REMAP-CAP**, **I-SPY 2** in breast cancer, **STAMPEDE** in prostate cancer, and the **Adaptive COVID-19 Treatment Trial (ACTT)**. **Basket** trials test one drug across tumours sharing a molecular alteration; **umbrella** trials test multiple drugs within one tumour type stratified by alteration. Adaptive designs need pre-specified operating characteristics, simulation-based type I error control, and firewalled interim analysis, or they become a licensed form of p-hacking.

## 7. Regulatory review and approval pathways

### [US] FDA

- **NDA** (New Drug Application) for small molecules; **BLA** (Biologics License Application) for biologics; **ANDA** for generics; **351(k)** for biosimilars. Review is by CDER (most drugs and therapeutic biologics) or CBER (vaccines, blood products, cell and gene therapies).
- **Standard review**: PDUFA goal of **10 months** from the 60-day filing date. **Priority review**: **6 months**, for products offering significant improvement in safety or effectiveness.
- **Fast Track** — for serious conditions with unmet need; enables rolling review and more frequent meetings.
- **Breakthrough Therapy** (created by FDASIA, 2012) — preliminary clinical evidence of substantial improvement over available therapy on a clinically significant endpoint; brings intensive FDA guidance and organisational commitment.
- **Accelerated Approval** — established **1992**. Permits approval on a **surrogate endpoint** or an intermediate clinical endpoint "reasonably likely to predict clinical benefit", with **confirmatory (Phase 4) trials** required to verify benefit; failure permits withdrawal. Rationale: "it is much faster to measure a reduction in tumour size, for example, than overall patient survival."
- **Regenerative Medicine Advanced Therapy (RMAT)**, **Qualified Infectious Disease Product (QIDP)** and **priority review vouchers** (tropical disease, rare paediatric disease) are additional incentives; vouchers are transferable and have sold for hundreds of millions of dollars.
- **Orphan drug designation** — under the Orphan Drug Act of 1983, for diseases affecting fewer than 200,000 people in the US: **seven years of market exclusivity**, tax credits for clinical research, and fee waivers. Enormously effective at stimulating rare-disease development, and criticised for "salami slicing" — subdividing a common disease into orphan-sized molecular subsets to capture the incentives.

### The accelerated approval controversy

The pathway's defenders point to HIV therapy in the 1990s and to oncology drugs that reached patients years earlier than they otherwise would; a 2023 analysis found it shortened approval timelines with "no impact on the ratio of approval to withdrawal" relative to traditional approval. Its critics point to:

- **Confirmatory trials that are slow, under-enrolled, or never completed**, leaving drugs on the market for years on surrogate evidence.
- **Dangling approvals** — indications whose confirmatory trials failed but which remained marketed while withdrawal was negotiated.
- **Aducanumab (Aduhelm)** — approved in 2021 for Alzheimer's disease on the amyloid-reduction surrogate, priced initially at **US$56,000 a year**, over the unanimous objection of all 11 advisory committee members, with a broad label covering all Alzheimer's patients despite testing only in early disease. A 2022 congressional investigation was highly critical of the FDA's conduct, three advisory committee members resigned, CMS restricted reimbursement to trial participants, and the product was ultimately discontinued.
- **Makena (hydroxyprogesterone caproate)** — accelerated approval in 2011 on a surrogate; the confirmatory PROLONG trial failed; withdrawal took until 2023.
- **Eteplirsen** and the Duchenne muscular dystrophy exon-skipping drugs — approved on dystrophin production of uncertain clinical meaning, over the reviewers' objections.

**Reform.** The Food and Drug Omnibus Reform Act (**FDORA**, part of the December 2022 appropriations package) strengthened the pathway: the FDA may require confirmatory trials to be **underway before** accelerated approval is granted, may specify conditions, must receive progress reports, and gained a **streamlined withdrawal procedure**.

### [EU] EMA

- **MAA** (Marketing Authorisation Application) through the **centralised procedure**, mandatory for biotechnology products, advanced therapies, orphans, and several therapeutic areas including cancer, HIV, diabetes and neurodegenerative disease; optional for others. Scientific assessment is by the **CHMP**, which issues an opinion; the legally binding marketing authorisation is granted by the **European Commission**, valid across the EU/EEA.
- Alternative routes: decentralised, mutual recognition and national procedures for non-centralised products.
- **Accelerated assessment** (150 days instead of 210), **conditional marketing authorisation** (the EU analogue of accelerated approval, renewed annually pending specific obligations), **authorisation under exceptional circumstances**, and **PRIME** (PRIority MEdicines), the EMA's counterpart to Breakthrough designation.
- **Orphan designation** in the EU applies to conditions affecting no more than 5 in 10,000 people, and confers **ten years of market exclusivity** (twelve with a completed paediatric investigation plan).
- The **Paediatric Regulation** requires a Paediatric Investigation Plan for new products, with a six-month SPC extension as the reward.

### Elsewhere

**[UK]** The MHRA operates independently post-Brexit, with the International Recognition Procedure relying on approvals by trusted regulators, and its own Innovative Licensing and Access Pathway. **Japan** PMDA, **China** NMPA (whose reforms since 2015 and accession to ICH in 2017 transformed the timelines), **Canada** Health Canada, **Australia** TGA, **Switzerland** Swissmedic. **[ZA]** SAHPRA has published backlog-clearance programmes and uses reliance pathways on stringent-regulatory-authority decisions. **[NA]** The Namibia Medicines Regulatory Council largely relies on decisions by SAHPRA and other recognised authorities. **WHO Prequalification** is the mechanism by which products become procurable by UN agencies and the Global Fund, and is therefore the effective gate for much of Africa. The **African Medicines Agency (AMA)**, whose treaty entered into force in November 2021, is intended to become a continental regulator.

## 8. Manufacturing and CMC

**Good Manufacturing Practice (GMP)** governs everything from raw materials to release testing: qualified facilities and equipment, validated processes, environmental monitoring, batch records, change control, deviation and CAPA systems, and a Qualified Person (EU) or equivalent releasing each batch.

Small molecules: route selection and optimisation, control of impurities including genotoxic impurities and nitrosamines (the source of the 2018–2021 recalls of valsartan, ranitidine, metformin and others), polymorph control, particle size, and formulation into a stable dosage form.

Biologics are harder in kind, not merely degree: living-cell expression systems (CHO cells, *E. coli*, yeast), bioreactor scale-up, purification trains, and the fact that **the process defines the product** — glycosylation, aggregation and charge variants shift with process changes, which is the entire reason biosimilars are not generics. **Comparability** exercises after any process change are a regulatory discipline in their own right.

Cell and gene therapies add vein-to-vein logistics: apheresis, cryopreservation, a manufacturing slot, and delivery back to a specific patient within a defined window, with viral-vector supply as the standing bottleneck.

**Supply chain.** The concentration of active pharmaceutical ingredient manufacturing in China and India, and the fragility this creates, became a first-order policy issue after 2020, alongside chronic shortages of low-margin generic sterile injectables.

## 9. Pharmacovigilance and post-marketing surveillance

Pre-approval trials, even at 5,000 patients, cannot detect an adverse event occurring at 1 in 10,000 (the "**rule of three**": to be 95% confident of seeing at least one event with incidence 1/n, you need roughly 3n patients). Everything rarer is found after launch, or not at all.

**The system:**
- **Spontaneous reporting** — FDA **FAERS**, the **MedWatch** programme, the UK **Yellow Card Scheme**, **EudraVigilance**, and the WHO's **VigiBase** at the Uppsala Monitoring Centre. Under-reporting is severe (commonly estimated at 90–95% of events), and reports carry no denominator, so these systems generate signals, not rates.
- **Signal detection** — disproportionality analysis (proportional reporting ratio, reporting odds ratio, Bayesian shrinkage methods) across the reporting databases.
- **Active surveillance** — the FDA **Sentinel Initiative** and the EU's Darwin EU query electronic health records and claims data with a denominator, which is a categorical improvement over spontaneous reporting.
- **Risk management** — the EU **Risk Management Plan**, the US **REMS** (Risk Evaluation and Mitigation Strategy) with elements such as restricted distribution, prescriber certification and pregnancy prevention programmes (isotretinoin, thalidomide, clozapine monitoring).
- **Periodic Safety Update Reports (PSUR/PBRER)** and structured benefit–risk reassessment.
- **Regulatory action** — label changes, boxed warnings, Direct Healthcare Professional Communications, restriction, suspension, withdrawal.

**Cases that shaped the system:** thalidomide (1957–1961) created modern drug regulation and the 1962 Kefauver–Harris amendments requiring proof of efficacy; practolol; benoxaprofen; cerivastatin (rhabdomyolysis, withdrawn 2001); **rofecoxib (Vioxx)**, withdrawn 2004 after cardiovascular harm that had been visible in earlier data, which drove trial-registration mandates and the FDA Amendments Act of 2007; troglitazone; and the still-unfolding examination of opioid marketing.

## 10. The economics

### What a drug costs to develop

The competing estimates and why they differ:

| Estimate | Figure | Basis |
|---|---|---|
| **DiMasi et al., 2016** (Tufts CSDD) | **US$2.6 bn** capitalised pre-approval cost | Confidential company data on 106 compounds from 10 firms; includes the cost of failures, and **capitalises** out-of-pocket spend at an 10.5% cost of capital over ~10 years |
| **Wouters, McKee & Luyten, 2020** (*JAMA*) | Median **US$985 m**, mean **US$1.1 bn** | SEC filings for 63 drugs approved 2009–2018; more transparent inputs, narrower sample |
| **Prasad & Mailankody, 2017** (*JAMA Intern Med*) | Median **US$648 m** to develop a cancer drug (US$757 m capitalised) | Ten companies that had brought a single drug to market; excludes broader portfolio failure costs |
| **By class** | Orphan **US$291 m**; cell and gene therapy up to **US$1.8 bn** | Class-specific analyses |
| **By phase (mean)** | Phase I **US$25 m**; Phase II **US$59 m**; Phase III **US$255–345 m** | — |

The dispersion is not fraud on anyone's part; it comes from four choices: (1) whether the cost of **failed** compounds is attributed to the survivors; (2) whether out-of-pocket spend is **capitalised** at a cost of capital (which can nearly double the number over a decade); (3) whether **public and academic** contributions to the underlying science are counted; and (4) sample selection — a portfolio of ten firms is not the industry. Both the high and low figures are used politically, and neither is a lie.

**What is not disputed:** development is expensive, most of the money is spent on things that fail, and R&D cost bears **no mechanical relationship to price**, because prices are set by what payers will bear, not by cost recovery.

### Patents and exclusivity

- A patent runs **20 years from filing**, and filing occurs early — often at the composition-of-matter stage, years before first-in-human. Effective post-approval patent life is commonly **8–12 years**.
- **[US] Patent term restoration** under Hatch-Waxman (**1984**) restores part of the time lost to FDA review, capped. **[EU]** The **Supplementary Protection Certificate** does the same job, up to five years.
- **Regulatory exclusivity is separate from patents.** **[US]** Five years for a **new chemical entity**, three years for a new clinical investigation supporting a change, seven years for **orphan** designation, six months' paediatric extension, twelve years for **biologics** under the BPCIA. **[EU]** The **8+2+1** rule: eight years of data exclusivity, two further years of market protection, plus one more for a significant new indication.
- **Evergreening and thickets.** Secondary patents on polymorphs, salts, formulations, devices, methods of use and manufacturing processes extend the effective monopoly. Insulin and inhaler devices are the standard examples; the patent estate around some biologics runs to well over a hundred patents.
- **Pay-for-delay** (reverse-payment) settlements, in which an originator pays a generic challenger to stay out, have been the subject of sustained antitrust action on both sides of the Atlantic.

### Generics

**[US]** Hatch-Waxman created the **ANDA** pathway: a generic need only demonstrate **bioequivalence** (typically that the 90% confidence interval for the ratio of Cmax and AUC to the reference falls within 80–125%) and adequate manufacturing, not repeat clinical trials. A **Paragraph IV certification** asserts that the listed patents are invalid or not infringed, triggering a 45-day window for suit and, if suit is filed, an automatic **30-month stay** on approval; the first successful filer earns **180 days of generic exclusivity**. The result: generic share of US prescriptions rose from **13% in 1983 to 84% in 2012**, with price falling steeply once several generics enter (commonly 80–90% below brand with four or more competitors). A recent assessment nonetheless characterises the resulting system as "a convoluted and expensive approach to balancing innovation and competition."

### Biosimilars

A biosimilar is "almost an identical copy" of an originator biologic made by a different company — it cannot be identical, because the process defines the product. **[US]** The **BPCIA (2009)** created the **351(k)** pathway, with a separate and higher standard of **interchangeability** permitting pharmacy-level substitution without prescriber involvement; **60 biosimilars** had FDA approval by October 2024. **[EU]** The EMA has authorised **more than 50** since 2006 and treats EU-approved biosimilars as interchangeable with their reference medicines. The WHO issued international guidelines in 2009.

Milestones: **Zarxio** (filgrastim), the first FDA biosimilar approval, **March 2015**, approved as a biosimilar but not as interchangeable; the first EU monoclonal antibody biosimilar (infliximab) in **2013**. Major molecules with biosimilar competition include adalimumab, bevacizumab, etanercept, insulin, rituximab and trastuzumab. Price erosion is smaller than for small-molecule generics — typically 15–50% rather than 80–90% — because development still costs US$100–300 million and takes years.

### The pricing debate

The positions, stated fairly:

- **Industry.** Prices fund the failures and the next generation of medicines; the marginal cost of a pill is irrelevant to the economics of an industry whose costs are almost entirely sunk and probabilistic; value-based pricing (what the health gain is worth) is the correct basis, not cost-plus.
- **Critics.** Prices bear no relation to R&D cost; much foundational science is publicly funded (the NIH's budget is over US$45 bn a year); marketing spend rivals or exceeds R&D at several large firms; buybacks and dividends consume large fractions of cash flow; and monopoly pricing on a life-saving product is coercion, not a market.
- **The extreme cases** force the question: **Casgevy at US$2.2 million**, CAR-T at **US$375,000–475,000**, and gene therapies priced above US$3 million. These are one-time treatments with potentially curative intent, which breaks the annuity model that both pricing and insurance are built on, and has driven experiments in outcomes-based agreements, instalment payment and subscription ("Netflix") models for hepatitis C.
- **Access.** **[ZA]/[NA]** For southern Africa the operative mechanisms are not list prices but **tiered pricing, voluntary licensing** (the Medicines Patent Pool), **compulsory licensing** under TRIPS flexibilities as clarified by the Doha Declaration (2001), local manufacture, and pooled procurement through the Global Fund and PEPFAR. The 1998–2001 South African litigation over the Medicines and Related Substances Control Amendment Act, in which 39 pharmaceutical companies sued the South African government and then withdrew under international pressure, is the defining episode in this history and directly shaped the Doha Declaration.

## 11. The modality landscape

### Small molecules

Still the majority of approvals. Advantages: oral bioavailability, intracellular access, low cost of goods, stability, straightforward manufacture, generic competition at patent expiry. Limitations: difficulty achieving selectivity, restriction to targets with a suitable binding pocket, and metabolism-driven interactions. Live frontiers: **covalent inhibitors** (KRAS G12C), **targeted protein degradation** — PROTACs and molecular glues, which convert a binding event into destruction of the target and therefore work on proteins with no functional pocket — **allosteric modulators**, and **macrocycles**.

### Monoclonal antibodies

Extracellular and cell-surface targets, exquisite selectivity, long half-life (2–3 weeks, enabling monthly dosing), and mature manufacture. Formats have progressed from murine (-omab) through chimeric (-ximab) and humanised (-zumab) to fully human (-umab), with the naming convention revised by the WHO in 2021 (new stems -tug, -bart, -mig, -ment). Fc engineering tunes effector function and half-life. Antibodies are the backbone of modern oncology (trastuzumab, rituximab, pembrolizumab, nivolumab), immunology (adalimumab, ustekinumab, dupilumab) and lipid management (evolocumab, alirocumab).

### Antibody–drug conjugates (ADCs)

An antibody, a linker and a cytotoxic payload. The design problem is the **therapeutic index**: enough payload delivered to tumour, little enough released systemically. Modern ADCs use cleavable linkers, high drug-to-antibody ratios and payloads with **bystander effect** (killing neighbouring antigen-negative cells). Trastuzumab deruxtecan redefined the field by showing activity in **HER2-low** disease, which reclassified a large population of breast cancers. **Datopotamab deruxtecan (Datroway)** was approved on **17 January 2025** for unresectable or metastatic HR-positive, HER2-negative breast cancer. Characteristic toxicities — interstitial lung disease, ocular surface effects, neutropenia — are payload- and linker-specific.

### Bispecifics and multispecifics

Two binding domains in one molecule. The dominant clinical form is the **T-cell engager**, binding CD3 on a T cell and a tumour antigen, forcing an immunological synapse: blinatumomab (CD19), teclistamab and elranatamab (BCMA), tarlatamab (DLL3), mosunetuzumab and glofitamab (CD20). Advantages over CAR-T: off-the-shelf, no manufacturing slot, immediately available. Disadvantages: continuous dosing, and the same cytokine release syndrome risk requiring step-up dosing and monitoring.

### Vaccines, including mRNA

Conventional platforms: live attenuated, inactivated, subunit, conjugate, toxoid, viral vector.

**mRNA vaccines** deliver nucleoside-modified mRNA in **lipid nanoparticles (LNPs)** that protect the RNA and mediate cellular uptake; the cell then produces the antigen, generating both humoral and cellular responses. The milestone chain: first successful mRNA transfection in liposomal nanoparticles (**1989**); naked mRNA injected into mouse muscle (**1990**); first human trial using mRNA-loaded dendritic cells (**2001**); **2005** — Katalin Karikó and Drew Weissman show that modified nucleosides suppress the innate immune response that had made mRNA unusable; BioNTech and Moderna founded **2008–2010**; LNPs first approved as a delivery system in **2018** for an siRNA drug; **December 2020** — UK and FDA authorisation of the Pfizer-BioNTech and Moderna COVID-19 vaccines, with short-term efficacy **over 90%** against the original SARS-CoV-2. Karikó and Weissman received the **2023 Nobel Prize in Physiology or Medicine**. Manufacturing scale-up was solved industrially — Pfizer ran roughly **100 microfluidic mixers in parallel** to make LNPs at volume. Current pipeline: influenza, RSV, malaria, rabies, cytomegalovirus, individualised neoantigen cancer vaccines, and **self-amplifying mRNA** (saRNA) which reduces the required dose.

### Cell therapies (CAR-T)

Autologous T cells are collected, transduced *ex vivo* with a **chimeric antigen receptor** — a construct that "combines antigen-binding and T cell activating functions into a single receptor" — expanded, and reinfused after lymphodepleting chemotherapy. The first two FDA approvals came in **2017**: **tisagenlecleucel (Kymriah)** for B-cell precursor acute lymphoblastic leukaemia and **axicabtagene ciloleucel (Yescarta)** for diffuse large B-cell lymphoma. By 2022 six products were approved, targeting CD19 and BCMA.

**Toxicities.** **Cytokine release syndrome (CRS)** occurs in almost all treated patients, resembling sepsis with fever, fatigue and organ dysfunction, managed with corticosteroids and the anti-IL-6 antibody tocilizumab. **ICANS** (immune effector cell-associated neurotoxicity syndrome) causes delirium, expressive difficulty and seizures, and in severe cases cerebral oedema and death. Both are graded on standard scales and require centres with defined capability.

**Cost and access.** Initial pricing **US$375,000–475,000**, driven by "complex cellular manufacturing in specialized good manufacturing practice (GMP) facilities". **Secondary malignancy** is a live question: insertional mutagenesis is a theoretical risk with integrating vectors, considered lower with modern vectors, and the FDA added a class boxed warning for T-cell malignancies after post-marketing reports.

**Frontiers.** Allogeneic ("off-the-shelf") CAR-T and CAR-NK, *in vivo* CAR generation using targeted LNPs, and the hard problem of solid tumours, where antigen heterogeneity, trafficking and the immunosuppressive microenvironment have so far defeated the approach.

### Gene therapy and gene editing

**Gene addition** delivers a functional copy of a gene, usually with an **AAV** vector (tissue tropism by serotype, non-integrating, limited ~4.7 kb cargo, and pre-existing neutralising antibodies in much of the population) or a **lentivirus** for *ex vivo* haematopoietic work. Approved examples include voretigene neparvovec (RPE65 retinal dystrophy), onasemnogene abeparvovec (spinal muscular atrophy), and haemophilia products.

**Gene editing** changes the genome in place. **Casgevy (exagamglogene autotemcel)** from Vertex and CRISPR Therapeutics is the landmark: the patient's own haematopoietic stem cells are edited *ex vivo* with CRISPR-Cas9 to disrupt the *BCL11A* erythroid enhancer, de-repressing fetal haemoglobin; after myeloablative conditioning the edited cells are reinfused. Approvals: **MHRA November 2023**; Bahrain 2 December 2023; **FDA December 2023** for sickle cell disease with recurrent vaso-occlusive crises; **FDA January 2024** for transfusion-dependent β-thalassaemia; **EMA February 2024**. Generally for patients aged 12 and over. In the pivotal data **93.5%** of evaluable participants were free of severe vaso-occlusive crises for at least 12 consecutive months, with engraftment in all. US list price **US$2.2 million**. **Lyfgenia** (lovotibeglogene autotemcel), a lentiviral gene-addition therapy for sickle cell disease, was approved the same day by the FDA.

Beyond nuclease editing: **base editing** (chemical conversion of one base to another without a double-strand break) and **prime editing** (search-and-replace via a reverse transcriptase fused to a nickase) are in clinical trials, including a widely reported bespoke *in vivo* base-editing treatment for an individual infant with a urea cycle disorder in 2025. *In vivo* CRISPR delivery to the liver by LNP has produced durable knockdown in transthyretin amyloidosis programmes. The unresolved issues across the field are off-target editing, delivery outside liver and haematopoietic tissue, immune responses to Cas proteins, long-term durability, and cost.

### RNA therapeutics

- **Antisense oligonucleotides (ASOs)** — short chemically modified single strands that bind a target transcript to trigger RNase H cleavage, block translation, or modulate splicing. Approved examples: **nusinersen** (spinal muscular atrophy, splice modulation), **inotersen** and **eplontersen** (transthyretin amyloidosis), **eteplirsen** and relatives (Duchenne exon skipping, and the contested accelerated approvals noted above). ASOs are chemistry-intensive and can be delivered intrathecally for CNS targets.
- **siRNA** — double-stranded RNA loaded into RISC for catalytic transcript degradation. **Patisiran** (2018) was the first approved siRNA drug and the first therapeutic use of an LNP. GalNAc conjugation, which targets the asialoglycoprotein receptor on hepatocytes, transformed the field by enabling subcutaneous dosing every three to six months: **givosiran**, **lumasiran**, **vutrisiran**, and **inclisiran** for LDL cholesterol. **Fitusiran (Qfitlia)** was approved on **28 March 2025** for haemophilia A or B — an siRNA that lowers antithrombin to rebalance haemostasis, notable as an RNA drug with a non-hepatic-disease indication achieved through a hepatic target.
- **mRNA therapeutics** beyond vaccines — protein replacement and *in vivo* CAR generation are in early trials.

### Peptides and the GLP-1 story

Peptides sit between small molecules and biologics: potent and selective, historically limited by proteolysis and lack of oral bioavailability, and now engineered around both.

The **incretin** story is the most consequential commercial and clinical development in metabolic medicine in a generation:

- **Semaglutide**, a GLP-1 receptor agonist with a **7-day half-life** enabling once-weekly dosing. It lowers glucose, stimulates beta-cell insulin secretion, inhibits glucagon, slows gastric emptying and reduces appetite. Approvals: **Ozempic** (injectable, type 2 diabetes) **December 2017** US, January 2018 Canada, February 2018 EU, March 2018 Japan; **Rybelsus** (oral, diabetes) **September 2019** US, April 2020 EU, updated as a first-line option January 2023; **Wegovy** (injectable, weight management) **June 2021** US, January 2022 EU, with a **cardiovascular indication in March 2024** and an **oral formulation approved December 2025**; **Kayshild** for metabolic-associated steatohepatitis in the **EU in March 2026**.
- **Key trials.** STEP (2021): mean body-weight change at week 68 of **−14.9%** with semaglutide versus **−2.4%** with placebo, in 1,961 participants across 16 countries. SUSTAIN-6: 3,297 participants with type 2 diabetes at cardiovascular risk over 104 weeks. **SELECT** (2024): 17,604 participants, MACE **6.5% versus 8.0%**, an **18.8% relative** reduction over about 48 months — the trial that established cardiovascular benefit in people **without** diabetes.
- **Tirzepatide**, a dual **GIP and GLP-1** receptor agonist with greater affinity for GIP receptors. **Mounjaro** for type 2 diabetes **May 2022** (designated first-in-class); **Zepbound** for chronic weight management **November 2023**; **obstructive sleep apnoea December 2024**. SURMOUNT-1: mean weight reduction of **−15.0%, −19.5% and −20.9%** at 5, 10 and 15 mg over 72 weeks versus **−3.1%** placebo. A three-year analysis reported in August 2024 found a **94%** reduction in progression to type 2 diabetes.
- **Why it matters beyond obesity.** These agents have produced outcome benefits in cardiovascular disease, heart failure with preserved ejection fraction, chronic kidney disease, sleep apnoea and steatohepatitis, which is forcing a reconsideration of obesity as a treatable upstream cause rather than a behavioural failing. The counterweights are cost, supply, the compounded-copy market, discontinuation and weight regain, loss of lean mass, gastrointestinal tolerability, and the almost complete absence of access in low- and middle-income countries.

> ⚠️ These medicines are prescription drugs with significant adverse effects and contraindications. Nothing in this description is a recommendation, and their use is a matter for a prescribing clinician.

### AI in drug discovery — the honest state

**What has genuinely landed.**

- **AlphaFold.** AlphaFold 1 won CASP13 in **2018** (GDT 68.5 overall, 58.9 on the hardest targets). **AlphaFold 2 (2020)** achieved a median GDT of **92.4** at CASP14, comparable to experimental determination, and was best on 88 of 97 targets. The **AlphaFold Protein Structure Database** launched in July 2021 with ~365,000 predictions and by July 2022 covered **~200 million proteins from 1 million species**. **AlphaFold 3 (May 2024)** extended prediction to complexes with DNA, RNA, ligands and ions, with a reported minimum **50% accuracy improvement** for protein interactions with other molecules. The **2024 Nobel Prize in Chemistry** went half to Hassabis and Jumper, half to David Baker for computational protein design.
- **What AlphaFold actually changed:** the cost and time of getting *a* structure fell to near zero, which is transformative for target triage, construct design, cryo-EM model building and understanding variants. It is a research accelerator of the first order.
- **What it did not change:** structures are not drugs. The documented limitations matter for exactly the cases drug discovery cares about — many regions predict with low confidence, including intrinsically disordered regions; performance "drops markedly on test cases with low similarity to its training data — an area of particular importance for drug discovery"; **50–70%** of human proteome structures lack covalently attached glycans; and the model has "limited capability to represent alternative conformational states, particularly those that coexist or interconvert in biological environments". Ligand-binding-site prediction and induced fit remain hard. Docking into an AlphaFold model performs worse than docking into an experimental structure.
- **Generative chemistry and property prediction.** Generative models, reinforcement learning over synthesisability-constrained chemical space, active-learning-guided ultra-large virtual screening, and ML-based ADMET prediction are now routine industrial tools. **Halicin** and **abaucin**, antibacterials identified by deep-learning screens at MIT (2020 and 2023), are the most-cited academic demonstrations.
- **Protein design.** RFdiffusion and related generative models from the Baker lab have produced *de novo* binders validated experimentally — arguably a larger long-run change than structure prediction.

**What has not landed.**

- **No drug discovered end-to-end by AI has yet been approved.** Several AI-originated molecules have reached Phase II; the field's most-watched example, Insilico Medicine's **rentosertib (ISM001-055)**, a TNIK inhibitor for idiopathic pulmonary fibrosis with both target and molecule AI-derived, has reported positive Phase IIa results — a genuine milestone, and not an approval.
- **The reckoning happened.** **Exscientia** and **Recursion** merged in 2024 after clinical setbacks; **BenevolentAI** restructured drastically after a Phase II failure in atopic dermatitis; several AI-designed candidates failed in Phase I or II. The pattern is that AI has compressed the **discovery** phase — the cheapest, fastest part — while the **clinical** phase, where the money and the failures are, is unchanged because the failures are biological, not chemical.
- **The honest framing:** the binding constraint on drug development is not molecule generation. It is knowing which target matters in human disease, and predicting human efficacy and toxicity. AI helps at the margins of both and solves neither. Where AI *is* likely to matter most is upstream (target identification from multi-omic and human genetic data), in trial design and patient stratification, and in the regulatory and manufacturing paperwork that consumes enormous human effort.
- Regulators are moving: the FDA published draft guidance in January 2025 on AI used to support regulatory decision-making about drugs, and the EMA has a reflection paper on AI in the medicinal product lifecycle.

## Sources

- [Drug development](https://en.wikipedia.org/wiki/Drug_development) — Wikipedia, accessed 2026-08-25
- [Lipinski's rule of five](https://en.wikipedia.org/wiki/Lipinski%27s_rule_of_five) — Wikipedia, accessed 2026-08-25
- [Accelerated approval (FDA)](https://en.wikipedia.org/wiki/Accelerated_approval) — Wikipedia, accessed 2026-08-25
- [Hatch-Waxman Act](https://en.wikipedia.org/wiki/Hatch-Waxman_Act) — Wikipedia, accessed 2026-08-25
- [Biosimilar](https://en.wikipedia.org/wiki/Biosimilar) — Wikipedia, accessed 2026-08-25
- [mRNA vaccine](https://en.wikipedia.org/wiki/MRNA_vaccine) — Wikipedia, accessed 2026-08-25
- [Chimeric antigen receptor T cell](https://en.wikipedia.org/wiki/Chimeric_antigen_receptor_T_cell) — Wikipedia, accessed 2026-08-25
- [Exagamglogene autotemcel](https://en.wikipedia.org/wiki/Exagamglogene_autotemcel) — Wikipedia, accessed 2026-08-25
- [Semaglutide](https://en.wikipedia.org/wiki/Semaglutide) — Wikipedia, accessed 2026-08-25
- [Tirzepatide](https://en.wikipedia.org/wiki/Tirzepatide) — Wikipedia, accessed 2026-08-25
- [AlphaFold](https://en.wikipedia.org/wiki/AlphaFold) — Wikipedia, accessed 2026-08-25
- [Novel Drug Approvals for 2025](https://www.fda.gov/drugs/novel-drug-approvals-fda/novel-drug-approvals-2025) — US FDA, accessed 2026-08-25

## Open questions

- **Phase-transition success rates** in the phases table (50–65%, 30%, 55–65%) are indicative composites from the general literature (BIO/Informa/QLS analyses); only the overall Phase I → approval figure of 9.6% was verified here.
- **Hopkins & Groom's druggable-genome estimate (2002)**, the DiMasi/Wouters/Prasad methodological contrasts beyond the headline figures, the TGN1412 details, the Vioxx timeline, the FDA Modernization Act 2.0 (2022), FDORA (2022), EU CTR 536/2014 application date, and the EU 8+2+1 exclusivity rule are stated from general reference knowledge and were **not** independently verified in this pass.
- **Rentosertib / ISM001-055** Phase IIa results, the Exscientia–Recursion merger, BenevolentAI's restructuring, halicin and abaucin, and the FDA's January 2025 draft AI guidance were not verified — treat as `needs-verification`.
- **Lyfgenia** (lovotibeglogene autotemcel) approval date is stated as concurrent with Casgevy's US sickle-cell approval from general knowledge; verify with FDA.
- Bioequivalence limits (80–125% for the 90% CI) and the "rule of three" in pharmacovigilance are standard but were not verified against a primary source here.
- **[ZA]/[NA]** SAHPRA and Namibia Medicines Regulatory Council process detail is described generally; verify current procedures with each authority.
