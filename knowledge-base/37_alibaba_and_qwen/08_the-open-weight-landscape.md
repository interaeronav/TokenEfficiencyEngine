---
id: alibaba.open_weight_landscape
title: The open-weight landscape — Qwen in context, August 2026
domain: 37_alibaba_and_qwen
tags: [open-weight, open-source-ai, llama, deepseek, mistral, glm, zhipu, kimi, moonshot, minimax, gpt-oss, gemma, phi, granite, nemotron, licences, benchmarks, contamination, lmarena, china-us-gap]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Hugging Face model API — org listings and licence metadata", url: "https://huggingface.co/api/models?author=deepseek-ai&sort=lastModified", publisher: "Hugging Face", accessed: 2026-08-25}
  - {title: "Hugging Face model search counts", url: "https://huggingface.co/models?search=qwen", publisher: "Hugging Face", accessed: 2026-08-25}
  - {title: "Qwen3.8-Max License", url: "https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/raw/main/LICENSE", publisher: "Qwen / Alibaba Cloud", accessed: 2026-08-25}
  - {title: "Alibaba Group Announces June Quarter 2026 Results", url: "https://data.alibabagroup.com/ecms-files/1532295521/fa5d65fc-9b3e-4e82-a8fc-4ce1c3e2c407/Alibaba%20Group%20Announces%20June%20Quarter%202026%20Results.pdf", publisher: "Alibaba Group", accessed: 2026-08-25}
  - {title: "Alibaba Group Holding Ltd Form 20-F FY2026", url: "https://www.sec.gov/Archives/edgar/data/1577552/000119312526231755/baba-20260331.htm", publisher: "SEC EDGAR", accessed: 2026-08-25}
related: [alibaba.qwen_models, alibaba.qwen_local, alibaba.qwen_agents, alibaba.cloud]
---

# The open-weight landscape — Qwen in context, August 2026

**Summary.** As of 25 August 2026 the largest openly-released models in the world are all Chinese: Kimi K3 (2.78 T parameters), Qwen3.8-2.4T-A95B (2.45 T), DeepSeek V4-Pro (1.65 T), GLM-5.2 (753 B). The largest Western open releases are an order of magnitude smaller — Mistral Large 3 at 675 B, Nvidia Nemotron 3 Ultra at 550B-A55B, OpenAI's gpt-oss-120b at 117 B — and Meta, which started the modern open-weight movement, has published nothing newer than Llama 4 in April 2025. Qwen's distinguishing feature is not that it is the largest but that it is the most *complete*: a full size ladder from 0.8 B to 2.4 T, mostly Apache 2.0, with first-party quantisations, embeddings, rerankers, guards, ASR, TTS and vision in the same family. That completeness is why 290,280 models on Hugging Face match "qwen" against 176,203 for "llama".

> ⚠️ **Confidence note.** Model names, parameter counts, licence tags and dates in the comparison table are read from the Hugging Face API on 25 August 2026 (high confidence). Capability claims and any assertion about relative quality are `needs-verification` — no independent evaluation was run, and this file argues at length that vendor benchmarks should not be used to make such claims.

## Key facts

| Item | Value (25 Aug 2026) |
|---|---|
| HF models matching "qwen" | **290,280** |
| HF models matching "llama" | 176,203 |
| HF models matching "gemma" | 98,755 |
| HF models matching "deepseek" | 17,710 |
| Largest open model | Kimi K3, 2,779,931,837,184 params |
| Largest Apache-2.0 open model | Qwen3.5-397B-A17B (403.4 B) / gpt-oss-120b (116.8 B) among Western |
| Meta's most recent open release | Llama 4 Scout / Maverick, April 2025 |
| Most permissive frontier licence | MIT (DeepSeek V4, GLM-5.2) |

## The comparison set

Parameter counts are exact `safetensors.total` values from the Hugging Face API; licences are the repository's declared licence.

### Chinese labs

| Model | Lab | Params (exact) | Licence | Repo updated |
|---|---|---|---|---|
| **Kimi K3** | Moonshot AI | 2,779,931,837,184 | `kimi-k3` (custom) | 2026-08-20 |
| **Qwen3.8-2.4T-A95B** | Alibaba | 2,446,182,725,504 | `qwen3.8-max` (custom) | 2026-08-12 |
| **DeepSeek-V4-Pro-0813** | DeepSeek | 1,650,497,936,906 | **MIT** | 2026-08-13 |
| DeepSeek-V4-Flash-0731 | DeepSeek | — | MIT | 2026-08-01 |
| **GLM-5.2** | Z.ai (Zhipu) | 753,329,940,480 | **MIT** | 2026-07-02 |
| GLM-5 / GLM-5.1 | Z.ai | — | MIT | 2026-08-11 / 2026-05-13 |
| **MiniMax-M3** | MiniMax | 427,040,140,160 | `minimax-community` | 2026-07-23 |
| MiniMax-H3 | MiniMax | — | `minimax-community` | 2026-08-13 |
| **Qwen3.5-397B-A17B** | Alibaba | 403,397,928,944 | **Apache 2.0** | 2026-02-16 |
| Qwen3.5-122B-A10B | Alibaba | 125,086,497,008 | Apache 2.0 | 2026-02-24 |
| Qwen3.8-27B | Alibaba | 27,781,427,952 | Apache 2.0 | 2026-08-14 |

### Western labs

| Model | Lab | Params (exact) | Licence | Repo updated |
|---|---|---|---|---|
| **Mistral-Large-3-675B-Instruct-2512** | Mistral AI | — (name says 675 B) | **Apache 2.0** | 2026-07-15 |
| Mistral-Small-4-119B-2603 | Mistral AI | — | Apache 2.0 | 2026-07-15 |
| Mistral-Medium-3.5-128B | Mistral AI | — | Apache 2.0 | 2026-07-15 |
| Ministral-3-8B-Instruct-2512 | Mistral AI | — | Apache 2.0 | 2026-07-15 |
| **Nemotron-3-Ultra-550B-A55B** | Nvidia | — | `nvidia-nemotron-open-model-license` | 2026-08-25 |
| Nemotron-3-Super-120B-A12B | Nvidia | 123,611,012,096 | `nvidia-nemotron-open-model-license` | 2026-08-25 |
| Nemotron-3-Nano-30B-A3B | Nvidia | — | `nvidia-nemotron-open-model-license` | 2026-08-25 |
| **gpt-oss-120b** | OpenAI | 116,829,156,672 | **Apache 2.0** | 2025-08-26 |
| gpt-oss-20b | OpenAI | — | Apache 2.0 | 2025-08-26 |
| gpt-oss-safeguard-120b / -20b | OpenAI | — | Apache 2.0 | 2025-10-29 / 2026-01-14 |
| **Llama-4-Scout-17B-16E-Instruct** | Meta | 108,641,793,536 | `llama4` (custom) | 2025-05-22 |
| Llama-4-Maverick-17B-128E-Instruct | Meta | — | `llama4` | 2025-05-22 |
| **gemma-4-12B-it** | Google | 11,959,730,224 | **Apache 2.0** | 2026-07-20 |
| gemma-4-12B-it-assistant (draft) | Google | 422,856,964 | Apache 2.0 | 2026-08-20 |
| **granite-4.2-30b / -8b / -3b** | IBM | 29,276,770,304 (30b) | **Apache 2.0** | 2026-08-25 |
| Fara1.5-27B / -9B / -4B | Microsoft | — | (see repo) | 2026-07-27 |

Three observations from that table.

**1. Meta has stopped.** The most recent Meta open-weight release is Llama 4 (April 2025, refreshed May 2025). Prompt-Guard-86M was touched in November 2025 but is a 2024 safety classifier. Meta's most-downloaded model in the last 30 days is still `Meta-Llama-3-8B-Instruct` from 2024. Whatever Meta's strategy now is, it is not shipping frontier open weights.

**2. Google moved Gemma to Apache 2.0.** Gemma 1–3 shipped under the Gemma Terms of Use with a use-restriction policy. `google/gemma-4-12B-it` is tagged `apache-2.0`. That is a material liberalisation, and it makes Gemma 4 the most permissive Western small-model family.

**3. DeepSeek and Z.ai use MIT.** DeepSeek V4 and GLM-5.2 are MIT-licensed at 1.65 T and 753 B parameters respectively. MIT is *more* permissive than Apache 2.0 (no patent grant, but also no notice-preservation ceremony). Two of the four largest open models in the world carry the most permissive licence in common use.

## What "open weight" does and does not mean

**It means:** you can download the parameters, run them on your own hardware, inspect their outputs, fine-tune them, and — depending on the licence — redistribute and sell.

**It does not mean:**

- **Open source.** The Open Source Initiative's 2024 Open Source AI Definition requires data information, code and parameters. Essentially no frontier model qualifies; none of the models above publish their training data. "Open weight" is the honest term and this domain uses it.
- **Reproducible.** You cannot retrain any of these from the published artefacts. You do not know the data, the mixture, the hyperparameters, the cluster or the total compute.
- **Auditable in any deep sense.** You can probe behaviour. You cannot inspect provenance, verify contamination claims, or trace a capability to its source.
- **Unrestricted.** Even Apache 2.0 models are subject to export control, sanctions law, and the acceptable-use policies of whatever platform you deploy on.

### The licence tiers, ranked

1. **MIT** — DeepSeek V4, GLM-5.2. Do anything; keep the notice.
2. **Apache 2.0** — most Qwen, gpt-oss, Gemma 4, Granite 4.2, Mistral's current line. Same freedom plus an explicit patent grant and a patent-retaliation clause.
3. **Permissive-with-scale-trigger** — the Qwen3.8-Max License (attribution above 100 M MAU or US$20 M monthly revenue; separate licence for MaaS or AI-work-assistant businesses above US$50 M/12 months), the older Qwen License Agreement and Tongyi Qianwen licence (100 M MAU). Irrelevant to almost everyone; decisive for a handful of companies.
4. **Community licences with acceptable-use policies** — Meta's `llama4`, Nvidia's `nvidia-nemotron-open-model-license`, Moonshot's `kimi-k3`, MiniMax's `minimax-community`. These add naming requirements, use restrictions, and in Meta's case a competitor exclusion. They are not Apache 2.0 and a lawyer must read them.
5. **Weights available, non-commercial** — research-only releases. Fine for experimentation, unusable in a product.

**The practical rule:** for anything you intend to sell, restrict yourself to tiers 1 and 2 unless you have had counsel read the specific licence file in the specific repository.

## The benchmark problem

Every capability claim in this domain, and in the industry, rests on benchmarks that are unreliable in four distinct ways.

### 1. Contamination

Benchmark test sets are on the public web. Pretraining corpora are scraped from the public web. Test items therefore appear in training data — sometimes verbatim, more often as paraphrases, discussion, solutions on Stack Overflow, or in synthetic data generated by a model that had seen them.

Every lab claims decontamination. Decontamination is usually n-gram overlap filtering against known benchmark strings, which catches verbatim copies and misses everything else: a Chinese translation of an MMLU question, a Reddit thread discussing a GPQA item, a textbook exercise that is the source of a GSM8K problem. **Nobody can verify anyone's decontamination** because nobody publishes the corpus.

The observable symptom: models that score highly on a public benchmark and noticeably worse on a freshly-written private set of the same difficulty.

### 2. Overfitting to the leaderboard

A benchmark used as a target ceases to measure what it measured. Every lab tracks the same fifteen or so numbers, and every training decision that raises them is kept. The result is real progress on those numbers and much smaller progress on the underlying capability. This is Goodhart's law with a US$100 billion budget behind it.

Specific symptoms to watch for:
- Enormous scores on saturated benchmarks (MMLU above 88 stops discriminating).
- Scores that jump discontinuously between minor versions.
- Strong performance on the benchmark's exact format and weak performance when the question is rephrased.

### 3. Self-reporting

Every score on a model card was produced by the vendor, using the vendor's prompts, sampling settings, harness, answer-extraction logic and number of attempts. All of these move scores by several points. A vendor comparing itself to a competitor is running the competitor's model under settings the vendor chose. **Cross-vendor comparisons from a model card are close to meaningless.**

This is why file `04` labels Qwen's own numbers as self-reported and does not tabulate competitors against them.

### 4. LMArena and the incentives of preference

LMArena (formerly Chatbot Arena) collects blind pairwise human preferences and computes an Elo-style rating. It is the best of the public leaderboards because it uses fresh, real prompts and cannot be trained on directly. It has three known problems:

- **It measures preference, not correctness.** Longer, better-formatted, more confident and more sycophantic answers win. Models can be — and demonstrably have been — tuned for arena appeal.
- **Private variants and selective release.** Labs test unreleased checkpoints under codenames and publish only the ones that score well, which is a selection effect on the leaderboard itself.
- **Prompt distribution.** Arena prompts skew toward what people type into a free chat box, which is not what an agent harness sends.

### What to do instead

**Build a private eval.** 50–200 items drawn from your actual workload, with a scoring function you wrote, that has never been published anywhere. This is the only measurement that will not be gamed, contaminated or misreported. It takes an afternoon and it is worth more than every leaderboard combined.

Then:

- **Version it and freeze it.** Score every candidate model on the identical set.
- **Score behaviour, not text.** Did the JSON parse? Did the tool call have the right arguments? Did the extracted date match? Not "does it look good".
- **Include adversarial and negative cases** — inputs where the correct answer is a refusal or "not present".
- **Measure latency and cost alongside quality.** A model that is 2 points better and 4× slower may be worse for your application.
- **Re-run on every model upgrade.** Vendors regress capabilities silently.

Where public benchmarks are still useful: **within one family, on one harness, run by one party** — e.g. Qwen3.5-4B vs Qwen3.5-9B vs Qwen3.5-27B on the Qwen team's own table. That ordering is informative even if the absolute numbers are not.

## The China–US model gap — the evidence

Stripped of rhetoric, here is what can actually be observed as of August 2026.

### Evidence that Chinese labs lead on open weights

- **Scale.** The four largest open models in the world are Chinese. The largest Western open model (Mistral Large 3, 675 B) is a quarter the size of Kimi K3.
- **Cadence.** In the eight weeks to 25 August 2026, Chinese labs shipped Kimi K3, Qwen3.8 (two models), DeepSeek V4-Pro, MiniMax M3 and H3, and GLM-5.2. In the same window the Western open releases were Nvidia's Nemotron 3 line, IBM Granite 4.2, Gemma 4 variants and Mistral's July batch.
- **Ecosystem gravity.** 290,280 Hugging Face repositories match "qwen" against 176,203 for "llama". The derivative ecosystem — the fine-tunes, merges, quantisations and distillations that the community actually builds on — has migrated to Qwen.
- **Architectural innovation.** Ultra-sparse MoE with sub-4% activation, linear-attention hybrids, multi-token prediction and native FP8 checkpoints all appeared in Chinese open models before or at the same time as Western ones. This is a rational response to compute constraint (`03`), and it produced genuinely better efficiency.

### Evidence that the gap persists at the closed frontier

- **The Max tier exists.** Alibaba maintains an API-only flagship a generation ahead of its open releases; the FY2026 20-F names Qwen3.7-Max as the frontier model while the open series was at 3.5/3.6. Chinese labs do not open-weight their best.
- **Compute.** Export controls since 2022 have restricted advanced accelerators. Alibaba's own filing describes the constraint in detail and its response has been to build domestic silicon of unproven relative performance. Training compute is the input that most reliably predicts frontier capability, and no Chinese lab discloses theirs.
- **Agentic capability.** The hardest current frontier — long-horizon autonomous work — is where the largest gaps between models show up, and it is the capability least well captured by benchmarks. Vendor claims here are the least verifiable of all.

### What cannot be concluded

That either side is "ahead" in general. The honest position:

- **On open weights available today, at a given parameter budget, Chinese models are competitive and often the best available.** This is verifiable by downloading them.
- **On the closed frontier, the ordering is unresolved from public evidence**, and every party claiming otherwise is citing benchmarks they produced.
- **On compute, the US retains a large advantage** that has not yet translated into a proportionate capability advantage, which is itself the interesting fact.

### One structural caveat

Chinese open models are trained and aligned under PRC content rules. On politically sensitive topics they will refuse, deflect or reframe. This is a real functional limitation for some applications, and it is not fixed by fine-tuning at the margins — though "abliterated" community variants exist (e.g. `huihui_ai/qwen3.5-abliterated` on Ollama, 563,000+ pulls) which strip refusal behaviour, generally at some cost to overall quality and safety behaviour. Judge whether it matters for your workload rather than assuming it does or does not.

## Why Qwen specifically became the favoured base

Six reasons, in rough order of importance:

**1. The complete size ladder.** 0.8 B, 2 B, 4 B, 9 B, 27 B dense plus 35B-A3B, 122B-A10B, 397B-A17B, 2.4T-A95B MoE — all in one generation, all with the same tokenizer, template and behaviour. You can prototype on a 4 B locally and deploy a 122 B with identical prompts. No other family offers that.

**2. Apache 2.0 by default.** No acceptable-use policy, no MAU trigger, no naming requirement for the great majority of checkpoints. Anyone building a product can use Qwen without a legal review.

**3. Day-one ecosystem support.** Qwen ships FP8, GPTQ-Int4 and AWQ checkpoints itself; `mlx-community` publishes MLX quants within days; Unsloth publishes GGUF including MTP draft heads; vLLM and SGLang ship named parsers (`--reasoning-parser qwen3`, `--tool-call-parser qwen3_coder`). This is deliberate — Alibaba works with the runtimes before release.

**4. Base checkpoints are published.** `-Base` variants exist for most sizes, which is what you need for continued pretraining and serious SFT. Several competitors publish only instruct-tuned weights.

**5. Multilingual breadth.** 201 languages and dialects claimed for Qwen3.5, against "100+" for most Western families. For non-English work this is often decisive, and it is why Qwen dominates as a base in the Chinese, South-East Asian, Turkish, Arabic and Indic fine-tuning communities.

**6. The specialist lines share the base.** Coder, VL, Omni, ASR, TTS, Embedding, Reranker and Guard are all Qwen-derived and Apache-2.0. You can build an entire stack — retrieval, generation, safety filtering, speech — inside one family with one licence and one tokenizer.

The compounding effect: each of those makes the next fine-tuner more likely to pick Qwen, which produces more community quantisations, adapters, cookbooks and Stack Overflow answers, which makes Qwen the path of least resistance for the next person. DeepSeek's distilled R1 series was itself built on Qwen bases (`DeepSeek-R1-Distill-Qwen-*`), and DeepSeek's 2026 speculative-decoding drafts (`eagle3_qwen3_14b_ttt7`, `dflash_qwen3_8b_block7`) target Qwen models — a competitor treating Qwen as infrastructure.

## Why Alibaba open-weights at all

The strategic logic, drawn from Alibaba's own filings rather than speculation:

**1. Cloud demand generation.** Alibaba's growth engine is AI Cloud and Compute Services: +45% revenue in the June 2026 quarter with AI product revenue at RMB 12,376 million. The FY2026 20-F describes PAI as offering "end-to-end support for the fine-tuning, evaluation, and deployment of major open-source large models". Every developer who standardises on Qwen is a candidate to run Qwen at scale on Alibaba Cloud. Open weights are the top of that funnel.

**2. Standard-setting under constraint.** If you cannot win on compute, win on the layer everyone builds against. A world in which Qwen is the default base model is a world in which Alibaba's tokenizer, chat template, tool-call format and architecture assumptions are the defaults — and in which its cloud is the natural place to scale.

**3. Talent and feedback.** The FY2026 20-F describes a flywheel: "broader AI adoption unlocks new growth opportunities, while feedback from real-world use cases enables us to enhance our models and user experiences." Open release is the cheapest possible source of adversarial testing.

**4. Denying a competitor's moat.** Open weights at a given capability level cap what anyone can charge for API access at that level. This disadvantages closed-model vendors more than it disadvantages Alibaba, whose revenue comes from cloud and commerce.

**5. Domestic and geopolitical positioning.** Chinese national policy favours domestic AI capability and open ecosystems; being the world's most-used open model family is a strong position with regulators at home and with developers in markets where US models are unavailable or distrusted.

**6. The Max tier preserves the monetisation.** The best model stays closed. Qwen3.8-2.4T-A95B — the first Max-class open release — carries a licence specifically restricting rival model-as-a-service and AI-work-assistant businesses. The generosity is real and it is bounded exactly where it would cost revenue.

## Sources

- Hugging Face model API, retrieved 25 August 2026: [deepseek-ai](https://huggingface.co/api/models?author=deepseek-ai&sort=lastModified), [meta-llama](https://huggingface.co/api/models?author=meta-llama&sort=lastModified), [moonshotai](https://huggingface.co/api/models?author=moonshotai&sort=lastModified), [zai-org](https://huggingface.co/api/models?author=zai-org&sort=lastModified), [MiniMaxAI](https://huggingface.co/api/models?author=MiniMaxAI&sort=lastModified), [openai](https://huggingface.co/api/models?author=openai&sort=lastModified), [google](https://huggingface.co/api/models?author=google&sort=lastModified), [mistralai](https://huggingface.co/api/models?author=mistralai&sort=lastModified), [nvidia](https://huggingface.co/api/models?author=nvidia&sort=lastModified), [ibm-granite](https://huggingface.co/api/models?author=ibm-granite&sort=lastModified), [microsoft](https://huggingface.co/api/models?author=microsoft&sort=lastModified) — names, dates, exact parameter counts, licence tags
- Hugging Face model search counts: [qwen](https://huggingface.co/models?search=qwen), [llama](https://huggingface.co/models?search=llama), [gemma](https://huggingface.co/models?search=gemma), [deepseek](https://huggingface.co/models?search=deepseek)
- [Qwen3.8-Max License](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/raw/main/LICENSE) — the MaaS and AI-Work-Assistant conditions
- [Alibaba Group Form 20-F FY2026](https://www.sec.gov/Archives/edgar/data/1577552/000119312526231755/baba-20260331.htm) — PAI open-model support, the AI/e-commerce flywheel, Qwen3.7-Max, export-control risk factors
- [Alibaba June Quarter 2026 Results](https://data.alibabagroup.com/ecms-files/1532295521/fa5d65fc-9b3e-4e82-a8fc-4ce1c3e2c407/Alibaba%20Group%20Announces%20June%20Quarter%202026%20Results.pdf) — cloud growth, AI product revenue, Qwen3.8-Max open-weighting
- [Ollama search for qwen3.5](https://ollama.com/search?q=qwen3.5) — community abliterated variants and pull counts

## Open questions

- All capability comparisons between the models in the table are `needs-verification`. No independent evaluation was run.
- Exact parameter counts are missing for several entries (Mistral Large 3, Nemotron 3 Ultra, GLM-5, MiniMax H3, DeepSeek V4-Flash) because their repositories do not expose a safetensors index via the API.
- Yi / 01.AI and Microsoft Phi do not appear in the current-release table — 01.AI's recent activity was not checked, and Microsoft's recent HF releases are the Fara agent line rather than a Phi 5. Both are `needs-verification`.
- Apple's on-device foundation models are not on Hugging Face and were not assessed; they are distributed through the Foundation Models framework in the OS, not as downloadable weights.
- The claim that Meta has stopped shipping frontier open weights is inferred from the absence of releases after May 2025 in its HF org, not from a Meta statement.
- Training-compute figures for any model in this file are undisclosed, which is the largest single gap in the China–US gap analysis.
- LMArena's current methodology and any 2026 changes to it are `needs-verification`; the criticisms above are structural and long-standing rather than specific to a current version.
