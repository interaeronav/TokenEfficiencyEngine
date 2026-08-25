---
id: alibaba.overview
title: Alibaba and Qwen — domain map and why this matters
domain: 37_alibaba_and_qwen
tags: [alibaba, qwen, open-weight, china-ai, local-llm, apple-silicon, mlx, domain-map, alibaba-cloud]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Alibaba Group Announces June Quarter 2026 Results", url: "https://data.alibabagroup.com/ecms-files/1532295521/fa5d65fc-9b3e-4e82-a8fc-4ce1c3e2c407/Alibaba%20Group%20Announces%20June%20Quarter%202026%20Results.pdf", publisher: "Alibaba Group", accessed: 2026-08-25}
  - {title: "Alibaba Group Holding Ltd Form 20-F, fiscal year ended March 31, 2026", url: "https://www.sec.gov/Archives/edgar/data/1577552/000119312526231755/baba-20260331.htm", publisher: "U.S. Securities and Exchange Commission (EDGAR)", accessed: 2026-08-25}
  - {title: "QwenLM/Qwen3.8 repository README", url: "https://github.com/QwenLM/Qwen3.8", publisher: "Qwen Team, Alibaba Group", accessed: 2026-08-25}
  - {title: "Qwen organisation model index (HF API)", url: "https://huggingface.co/api/models?author=Qwen", publisher: "Hugging Face", accessed: 2026-08-25}
  - {title: "Qwen3.8-Max License", url: "https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/raw/main/LICENSE", publisher: "Qwen / Alibaba Cloud", accessed: 2026-08-25}
related: [alibaba.history, alibaba.structure, alibaba.cloud, alibaba.qwen_models, alibaba.qwen_architecture, alibaba.qwen_local, alibaba.qwen_finetune, alibaba.open_weight_landscape, alibaba.qwen_agents, alibaba.resources]
---

# Alibaba and Qwen — domain map and why this matters

**Summary.** Alibaba Group is a Chinese commerce-and-cloud conglomerate that, since roughly 2023, has become the single most prolific publisher of openly-licensed large language models in the world. Its Qwen family — 462 model repositories on Hugging Face as of 25 August 2026, most of them under Apache 2.0 — is now the default base model for the open fine-tuning ecosystem and the practical answer to "what can I actually run on my own hardware?" This domain covers three interlocking things: the company (files 01–03), the models as a technical register (04–05), and the practical business of running, adapting and building on them locally (06–09), with a tested link register in 10.

## Key facts

| Item | Value (dated) | File |
|---|---|---|
| Alibaba FY2026 revenue (year ended 31 Mar 2026) | RMB 1,023,670 m (US$148,401 m) — first year over RMB 1 trillion | `02` |
| Alibaba FY2026 income from operations | RMB 50,150 m (US$7,270 m), down from RMB 140,905 m in FY2025 | `02` |
| Alibaba FY2026 capital expenditure | RMB 126,063 m (US$18,275 m), vs RMB 85,972 m FY2025 and RMB 32,087 m FY2024 | `02`, `03` |
| Cloud/AI segment revenue growth, quarter ended 30 Jun 2026 | +45% year over year (total and external), RMB 48,437 m | `02`, `03` |
| AI-related product revenue, quarter ended 30 Jun 2026 | RMB 12,376 m — twelfth consecutive quarter of triple-digit YoY growth | `02` |
| Alibaba Cloud share of China AI cloud market | 38.1%, ranked first (Omdia, "AI Cloud Market: China – 2025") | `03` |
| Current open flagship | Qwen3.8-2.4T-A95B — 2,446,182,725,504 params, 95B active, released 12 Aug 2026 | `04` |
| Current open dense/omni model | Qwen3.8-27B — 27,781,427,952 params, vision+text, Apache 2.0, released 14 Aug 2026 | `04` |
| Native context length, Qwen3.5/3.6/3.8 generation | 262,144 tokens; extensible to ~1,010,000 with RoPE scaling | `04`, `05` |
| Models matching "qwen" on Hugging Face | 290,280 (vs 176,203 for "llama", 98,755 for "gemma", 17,710 for "deepseek") | `08` |
| Fiscal year end | 31 March. FY2026 = 1 Apr 2025 → 31 Mar 2026 | `02` |

> ⚠️ Alibaba's fiscal year ends **31 March**. "FY2026" means the twelve months to 31 March 2026, not calendar 2026. Every figure in this domain states which. Quarterly labels follow Alibaba's own convention ("June quarter 2026" = quarter ended 30 June 2026, which is the *first* quarter of fiscal 2027).

## Why this domain exists as one domain

Three arguments would normally be separate: a company history, a model register, and a local-inference cookbook. They belong together because the causal chain runs through all three.

**Alibaba open-weights its frontier models because of where it sits in the market, not out of altruism.** It is the number-one cloud provider in China with 38.1% of the AI cloud market, and its cloud growth (+45% YoY in the June 2026 quarter) is now the group's growth engine while its e-commerce core grows at 4%. Open weights are a demand-generation mechanism for that cloud: every developer who standardises on Qwen locally is a candidate to run Qwen at scale on Alibaba Cloud, and every derivative model on Hugging Face is free distribution. It is also a hedge against export controls — if you cannot buy the best GPUs, the next-best strategic position is to own the software layer everybody else builds on. See `03` and `08`.

**That corporate motive produces an unusually good deal for individual practitioners.** Because the strategy is ecosystem capture rather than API monetisation, most Qwen weights ship under Apache 2.0 — genuinely permissive, no acceptable-use appendix, no monthly-active-user ceiling. The exception is the very top of the range: Qwen3.8-2.4T-A95B ships under a bespoke "Qwen3.8-Max License" with two commercial triggers (see `04` for the exact wording). Knowing which licence applies to which checkpoint is a commercial fact, not a footnote.

**And the models are architected in a way that makes local deployment tractable.** The Qwen3.5-generation architecture — inherited by Qwen3.6 and Qwen3.8 — interleaves three Gated DeltaNet (linear-attention) layers with one gated full-attention layer. Only one layer in four keeps a growing KV cache. On a Qwen3.8-27B running at its full 262,144-token context, that is about 16 GiB of KV cache instead of about 64 GiB for an equivalent all-attention model. That single design decision is the difference between "runs on a 64 GB Mac" and "does not." The arithmetic is worked in `06`.

## The domain map

### 01 — `01_alibaba-group-history.md`
The company from Jack Ma's Hangzhou apartment on 28 June 1999 through the eBay China fight, the Alipay spin-off controversy, the record 2014 NYSE IPO, the November 2020 Ant Group IPO suspension and the regulatory winter that followed, the 2023 "1+6+N" restructuring and its partial reversal, the Zhang → Wu/Tsai leadership handover, and the 2024–2026 AI pivot. Everything dated and sourced.

### 02 — `02_alibaba-business-structure.md`
What the group actually is in August 2026 — including the fact that the familiar six-unit structure no longer exists. In the quarter ended 30 June 2026 Alibaba collapsed its reporting into four segments: Alibaba E-commerce Group, AI Cloud and Compute Services, AI Labs and Applications, and All Others. Segment revenue and adjusted EBITA for each, plus the affiliated Ant Group (33% equity interest) and the group financials with fiscal years attached.

### 03 — `03_alibaba-cloud-and-infrastructure.md`
The technical arm: Apsara, Shenlong, Pangu, Lingjun; the PolarDB / AnalyticDB / Lindorm database stack; the T-Head silicon programme — Hanguang 800 (2019), Yitian 710 (2021), the XuanTie RISC-V line from C910 (2019, open-sourced 2021) to the RVA23-class C930 (2025), and the Zhenwu AI processors now serving 650+ external customers; the capex programme; and how US export controls shaped all of it, including Alibaba's February 2026 addition to and removal from the US Department of Defense's Chinese Military Companies list.

### 04 — `04_qwen-model-family.md` — the key reference file
A complete dated register from Qwen-7B (3 August 2023) to Qwen3.8-27B (14 August 2026): every generation, parameter counts to the exact figure where the Hugging Face safetensors index reports one, context lengths, architecture notes, licence per checkpoint, and reported benchmark positioning with the self-reporting caveat attached. Table first, then per-generation detail.

### 05 — `05_qwen-architecture-and-training.md`
The technical substance behind the register: GQA, SwiGLU, RMSNorm, RoPE and its extensions (YaRN, dual chunk attention), the shift to Gated DeltaNet hybrid attention in Qwen3-Next and Qwen3.5, MoE routing (512 experts, 10 routed + 1 shared), the tokenizer's growth from 151,936 to 248,320 tokens, multi-token prediction, the post-training stack including GSPO, and the thinking/non-thinking modes. Cited to the arXiv technical reports by identifier.

### 06 — `06_running-qwen-locally.md` — the practical file
Memory arithmetic you can check, quantisation formats compared with real measured file sizes, MLX and `mlx_lm` end to end (generate, server, convert, LoRA, AWQ/DWQ/GPTQ, speculative decoding with MTP draft modules), llama.cpp/Ollama/LM Studio, vLLM/SGLang, the exact Qwen chat template, thinking-mode control, tool calling, structured output, troubleshooting, and concrete recommended setups at 16/24/32/48/64/128 GB unified memory.

### 07 — `07_fine-tuning-and-adaptation.md`
When not to fine-tune; dataset formats; full vs LoRA vs QLoRA vs DoRA with the memory maths; the tooling (mlx-lm, Unsloth, Axolotl, LLaMA-Factory, MS-SWIFT, TRL/PEFT); hyperparameters that actually move the needle; evaluating a fine-tune; catastrophic forgetting; adapter merging; continued pretraining; and a worked end-to-end example on Apple Silicon.

### 08 — `08_the-open-weight-landscape.md`
Qwen in context against DeepSeek V4, Kimi K3, GLM-5.x, MiniMax M3, Llama 4, Mistral Large 3, gpt-oss, Gemma 4, Granite 4.2, Nemotron 3 and the rest — with licences and parameter counts as of 25 August 2026. What "open weight" does and does not mean. Why benchmarks are unreliable and what to do instead. The China–US gap debate with evidence rather than assertion.

### 09 — `09_using-qwen-in-agent-systems.md`
Qwen as a coding-agent backend, tool-calling reliability, Qwen-Agent and Qwen Code, MCP integration, prompt engineering specifics, long-document handling, JSON reliability, Qwen3-Embedding and the retrieval stack, agent evaluation, cost/latency versus API models, privacy and data-residency arguments, and an honest account of where a local Qwen is simply not good enough.

### 10 — `10_resources.md`
The link register: official sites, GitHub org, Hugging Face and ModelScope collections, arXiv identifiers, documentation, quantisation providers, leaderboards, and Alibaba's investor relations and SEC filings.

## The three things worth internalising

**1. The generation numbering moved fast and the names are confusing.** Between April 2025 and August 2026 the family went Qwen3 → Qwen3-2507 refresh → Qwen3-Next → Qwen3-VL → Qwen3.5 → Qwen3.6 → Qwen3.8, with parallel Coder, Omni, VL, ASR, TTS, Embedding, Reranker and Guard lines, plus API-only "Max" tiers. There is no Qwen3.7 open release (Qwen3.7-Max was API-only; it is named in the FY2026 20-F). File `04` disentangles this.

**2. "Open weight" is a spectrum and Qwen sits at the permissive end — mostly.** Apache 2.0 covers the overwhelming majority of Qwen checkpoints including everything in the Qwen3.5/3.6/3.8 open series *except* the 2.4T flagship. Historic Qwen 1/1.5/2 used the "Tongyi Qianwen" licence and Qwen2/2.5 large models the "Qwen License Agreement" (release date 19 September 2024), both of which carry a 100-million-monthly-active-user commercial trigger. If you are shipping a product, check the LICENSE file in the specific repository you are pulling — not the family.

**3. Local Qwen is genuinely useful and genuinely limited.** A Qwen3.8-27B at 4-bit on Apple Silicon runs in about 16 GB of weights and answers well on summarisation, extraction, classification, routine code, and tool-driven workflows. It is not a substitute for a frontier hosted model on long-horizon agentic coding, hard multi-step reasoning, or anything where a subtle error is expensive. File `09` is explicit about the boundary rather than optimistic about it.

## Conventions used throughout this domain

- **Dates.** Every model, figure and claim carries a date. Model release dates are taken from the `createdAt` field of the Hugging Face repository (first publication) or from the dated news entries in the official GitHub README, and the file says which.
- **Financials.** Stated in RMB with the US$ conversion as published by Alibaba, with the fiscal year or quarter named. Figures from the 20-F are preferred over press summaries.
- **Benchmarks.** Any score originating from a vendor's own model card or blog is labelled as self-reported. This is not a rhetorical hedge — see `08` on contamination and leaderboard overfitting.
- **Commands.** Every command in `06` and `07` is written against the flags actually present in the current `mlx-lm` argument parsers, the Qwen3.8 README, or the vendor documentation cited. Version drift is the usual failure mode; the file says which version was checked.
- **Unverified items** are marked inline as `needs-verification` and collected under `## Open questions` at the end of each file.


## The China AI position, stated plainly

The debate about Chinese AI capability is usually conducted with adjectives. The observable facts as of August 2026 are narrower and more useful.

**On the open-weight frontier, Chinese labs are ahead by volume and roughly level on capability.** The largest openly-released models in the world are Chinese: Moonshot's Kimi K3 at 2.78 trillion parameters (20 August 2026), Alibaba's Qwen3.8-2.4T-A95B at 2.45 trillion (12 August 2026), DeepSeek V4-Pro at 1.65 trillion (13 August 2026), Z.ai's GLM-5.2 at 753 billion (2 July 2026). The largest Western open releases in the same window are an order of magnitude smaller: Mistral Large 3 at 675 billion, NVIDIA Nemotron 3 Ultra at 550B-A55B, OpenAI's gpt-oss-120b at 117 billion. Meta, which created the modern open-weight movement with LLaMA in 2023, has published nothing newer than Llama 4 (April 2025). See `08` for the full table with licences.

**On the closed frontier, the gap is real but the direction of travel is contested.** Alibaba's own top-tier models — the Max tier — are API-only and are the ones it benchmarks against Western frontier systems. Its open releases are deliberately a step behind that. Anyone claiming a definitive verdict on the gap is over-reading benchmark tables that all parties have an incentive to game.

**On compute, the constraint is hardware, and the response has been architectural and vertical.** US export controls since 2022 have restricted advanced computing chips to China, and Alibaba's FY2026 20-F documents the escalating position, including the January 2026 House passage of the Remote Access Security Act and the September 2025 Chinese instruction to domestic firms to halt certain chip purchases. Alibaba's answer has been to build its own: T-Head's Zhenwu AI processors are now in production at scale and serving more than 650 external customers across 20-plus industries via Alibaba Cloud. Whether that closes the compute gap is unproven; that it changes the shape of the problem is not.

**For a practitioner, none of this is the operative question.** The operative question is: which weights can I download today, under what licence, that will run on the machine in front of me and do the job? On that question, the Qwen family is currently the best-stocked shelf in the shop, and files `04` and `06` are the inventory and the instructions.

## How to use this domain

- **"Which Qwen should I download?"** → `04` for the register, then `06` for the size/RAM table.
- **"Will it fit in my RAM?"** → `06`, section on memory arithmetic. Compute it; do not guess.
- **"Can I ship a product on this?"** → `04`, licence column, then read the LICENSE file in the actual repository.
- **"Why is my tool calling broken?"** → `06` (chat template) and `09` (tool-calling reliability). The Qwen3.8 tool-call format is XML-ish, not JSON — this changed from Qwen3 and breaks naive parsers.
- **"Should I fine-tune?"** → `07`, first section. The answer is usually no.
- **"How does Qwen compare to X?"** → `08`.
- **"How big is Alibaba and can it keep funding this?"** → `02`, then `03` for the capex trajectory.
- **"Where do I get the primary source?"** → `10`.

## Sources

- [Alibaba Group Announces June Quarter 2026 Results (PDF)](https://data.alibabagroup.com/ecms-files/1532295521/fa5d65fc-9b3e-4e82-a8fc-4ce1c3e2c407/Alibaba%20Group%20Announces%20June%20Quarter%202026%20Results.pdf) — Alibaba Group, 20 August 2026
- [Alibaba Group Holding Ltd, Form 20-F for fiscal year ended 31 March 2026](https://www.sec.gov/Archives/edgar/data/1577552/000119312526231755/baba-20260331.htm) — SEC EDGAR, filed 20 May 2026
- [SEC XBRL company concept API, CIK 0001577552](https://data.sec.gov/api/xbrl/companyconcept/CIK0001577552/us-gaap/Revenues.json) — audited annual revenue series
- [QwenLM/Qwen3.8 README](https://github.com/QwenLM/Qwen3.8) — release news, deployment commands
- [Qwen organisation on Hugging Face](https://huggingface.co/Qwen) and the [model index API](https://huggingface.co/api/models?author=Qwen)
- [Qwen3.8-Max License](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/raw/main/LICENSE)
- [Qwen/Qwen3.8-27B config.json](https://huggingface.co/Qwen/Qwen3.8-27B/raw/main/config.json) — architecture parameters
- [Hugging Face model search counts](https://huggingface.co/models?search=qwen) — retrieved 25 August 2026

## Open questions

- Alibaba's group-wide employee headcount as of 31 March 2026 was not extractable from the 20-F text used here; the FY2025 figure (~124,000) circulating on secondary sources is `needs-verification`.
- Alibaba Cloud's current region and availability-zone count could not be confirmed from a first-party page (the global-locations page returned no readable content). Treat any specific figure as `needs-verification` — see `03`.
- The Qwen3.5 and Qwen3.8 technical reports were not on arXiv as of 25 August 2026; architecture detail in `05` for those generations is reconstructed from configuration files and model cards, not from a peer-reviewable paper.
