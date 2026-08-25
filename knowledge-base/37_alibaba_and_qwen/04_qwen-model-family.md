---
id: alibaba.qwen_models
title: The Qwen model family — a dated release register
domain: 37_alibaba_and_qwen
tags: [qwen, qwen3, qwen3.5, qwen3.8, qwen2.5, qwq, qwen-vl, qwen-omni, qwen-coder, qwen-embedding, moe, licence, apache-2.0, model-register, context-length]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Qwen organisation model index (HF API, author=Qwen)", url: "https://huggingface.co/api/models?author=Qwen&sort=createdAt", publisher: "Hugging Face", accessed: 2026-08-25}
  - {title: "QwenLM/Qwen3.8 README (news and model list)", url: "https://github.com/QwenLM/Qwen3.8", publisher: "Qwen Team, Alibaba Group", accessed: 2026-08-25}
  - {title: "QwenLM/Qwen3 README (news)", url: "https://github.com/QwenLM/Qwen3", publisher: "Qwen Team, Alibaba Group", accessed: 2026-08-25}
  - {title: "Qwen/Qwen3.8-2.4T-A95B model card and config", url: "https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B", publisher: "Qwen / Alibaba Cloud", accessed: 2026-08-25}
  - {title: "Qwen3.8-Max License", url: "https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/raw/main/LICENSE", publisher: "Qwen / Alibaba Cloud", accessed: 2026-08-25}
  - {title: "Qwen LICENSE AGREEMENT (release date 19 September 2024)", url: "https://huggingface.co/Qwen/Qwen2.5-72B-Instruct/raw/main/LICENSE", publisher: "Alibaba Cloud", accessed: 2026-08-25}
  - {title: "Qwen/Qwen3.8-27B config.json", url: "https://huggingface.co/Qwen/Qwen3.8-27B/raw/main/config.json", publisher: "Qwen / Alibaba Cloud", accessed: 2026-08-25}
  - {title: "Alibaba Group Holding Ltd Form 20-F FY2026", url: "https://www.sec.gov/Archives/edgar/data/1577552/000119312526231755/baba-20260331.htm", publisher: "SEC EDGAR", accessed: 2026-08-25}
related: [alibaba.overview, alibaba.qwen_architecture, alibaba.qwen_local, alibaba.open_weight_landscape, alibaba.resources]
---

# The Qwen model family — a dated release register

**Summary.** Qwen (通义千问, Tongyi Qianwen) is Alibaba Cloud's foundation model family. The first weights — Qwen-7B and Qwen-7B-Chat — appeared on Hugging Face on **3 August 2023**. As of **25 August 2026** the Qwen organisation hosts **462 model repositories**, and the current open flagship is **Qwen3.8-2.4T-A95B** (2,446,182,725,504 parameters, 95B active, released 12 August 2026) alongside the dense multimodal **Qwen3.8-27B** (27,781,427,952 parameters, Apache 2.0, released 14 August 2026). The generation sequence runs Qwen → Qwen1.5 → Qwen2 → Qwen2.5 → Qwen3 → Qwen3-Next → Qwen3.5 → Qwen3.6 → Qwen3.8, with parallel Coder, VL, Audio, Omni, ASR, TTS, Embedding, Reranker and Guard lines and an API-only "Max" tier that is a generation ahead of the open releases.

> ⚠️ **Every benchmark number in this file is self-reported** by the Qwen team on its own model cards or blog posts unless explicitly attributed elsewhere. Vendor-reported scores are systematically optimistic: they use the vendor's own prompts, sampling settings, harness and extraction logic, and there is no contamination audit. Use them for ordering within a family, never as an absolute capability claim, and never to compare across vendors. See `08` for why.

## Key facts

| Item | Value |
|---|---|
| First public weights | Qwen-7B / Qwen-7B-Chat, 3 August 2023 |
| Repositories in the Qwen HF organisation | 462 (25 August 2026) |
| Current open flagship | Qwen3.8-2.4T-A95B, 12 August 2026, "Qwen3.8-Max License" |
| Current open dense/multimodal | Qwen3.8-27B, 14 August 2026, Apache 2.0 |
| Native context, Qwen3.5/3.6/3.8 | 262,144 tokens; extensible to ~1,010,000 with RoPE scaling |
| Vocabulary, Qwen3.5 generation onward | 248,320 tokens (padded); previously 151,936 (Qwen2/2.5/3) |
| Languages claimed, Qwen3.5 onward | 201 languages and dialects (Qwen3: "100+") |
| Dominant licence | Apache 2.0 |
| Exceptions | Qwen3.8-2.4T-A95B (Qwen3.8-Max License); Qwen 1 / 1.5 / 2 (Tongyi Qianwen); Qwen2.5 72B/Math/VL and QVQ (Qwen License Agreement) |

## Master register

Release dates are the Hugging Face repository creation date (first publication) unless the official README dates a formal announcement differently — where both exist, the README announcement date is given in brackets. Parameter counts are the exact `safetensors.total` figure from the Hugging Face API where available.

### Generation 1 — Qwen (2023)

| Model | First published | Sizes | Context | Licence | Notes |
|---|---|---|---|---|---|
| Qwen-7B / Qwen-7B-Chat | 2023-08-03 | 7B | 8K (32K with NTK) | Tongyi Qianwen | First release. Custom `modeling_qwen.py`, needs `trust_remote_code` |
| Qwen-VL / Qwen-VL-Chat | 2023-08-18 / 08-20 | ~9.6B | 8K | Tongyi Qianwen | ViT-bigG encoder + Qwen-7B; grounding and OCR. arXiv:2308.12966 |
| Qwen-14B / -Chat | 2023-09-24 | 14B | 8K | Tongyi Qianwen | |
| Qwen-72B / -Chat | 2023-11-26 / 11-29 | 72,287,920,128 | 32K | Tongyi Qianwen | |
| Qwen-1_8B | 2023-11-30 | 1.8B | 8K | Tongyi Qianwen | |
| Qwen-Audio / -Chat | 2023-11-30 | ~8.4B | — | Tongyi Qianwen | Whisper-large-v2 encoder + Qwen-7B. arXiv:2311.07919 |

Technical report: **arXiv:2309.16609**, "Qwen Technical Report", 28 September 2023.

### Generation 1.5 — Qwen1.5 (2024)

| Model | First published | Sizes | Context | Licence | Notes |
|---|---|---|---|---|---|
| Qwen1.5 base/chat | 2024-01-22 (announced 2024-02-05) | 0.5B, 1.8B, 4B, 7B, 14B | 32K | Tongyi Qianwen | Merged into `transformers` as `Qwen2ForCausalLM` — no `trust_remote_code` |
| Qwen1.5-72B-Chat | 2024-01-30 | 72,287,920,128 | 32K | Tongyi Qianwen | |
| Qwen1.5-32B-Chat | 2024-04-03 | 32B | 32K | Tongyi Qianwen | |
| CodeQwen1.5-7B / -Chat | 2024-04-15 | 7B | 64K | Tongyi Qianwen | First code specialist |
| Qwen1.5-110B / -Chat | 2024-04-25 | 110B | 32K | Tongyi Qianwen | |
| Qwen1.5-MoE-A2.7B | 2024-03 (announced 2024-03-28) | 14.3B total / 2.7B active | 32K | Tongyi Qianwen | **First Qwen MoE** |

Qwen1.5 has no separate technical report; it is a transitional release whose main contribution was mainline `transformers` integration and the standardised ChatML template that survives to this day.

### Generation 2 — Qwen2 (2024)

| Model | First published | Sizes | Context | Licence | Notes |
|---|---|---|---|---|---|
| Qwen2 base | 2024-05-22 / 05-31 | 0.5B, 1.5B, 7B, 57B-A14B, 72B | 32K–128K | Apache 2.0 (0.5B/1.5B/7B/57B); Tongyi Qianwen (72B) | GQA across all sizes |
| Qwen2-72B-Instruct | 2024-05-28 | 72,706,203,648 | 128K (YaRN) | Tongyi Qianwen | |
| Qwen2-57B-A14B-Instruct | 2024-06-04 | 57B / 14B active | 64K | Apache 2.0 | MoE |
| Qwen2-Audio-7B / -Instruct | 2024-07-16 / 07-31 | 8,397,094,912 | — | Apache 2.0 | Voice chat + audio analysis. arXiv:2407.10759 |
| Qwen2-Math | 2024-08-08 | 1.5B, 7B, 72B | 4K | Tongyi Qianwen (72B) | |
| Qwen2-VL | 2024-08-28 | 2B, 7B, 72B | 32K | Apache 2.0 (2B/7B); Tongyi Qianwen (72B) | **Naive Dynamic Resolution** + **M-RoPE**. arXiv:2409.12191 |

Technical report: **arXiv:2407.10671**, "Qwen2 Technical Report", 15 July 2024.

### Generation 2.5 — Qwen2.5 (2024–2025)

The generation that made Qwen the default open base model. Announced 19 September 2024.

| Model | First published | Sizes | Context | Licence | Notes |
|---|---|---|---|---|---|
| Qwen2.5 base/instruct | 2024-09-17 | 0.5B, 1.5B, 3B, 7B, 14B, 32B, 72B | 128K in, 8K out | Apache 2.0 except 3B and 72B (Qwen License) | 18T-token pretrain corpus reported |
| Qwen2.5-Coder | 2024-09-17 → 2024-11-08 | 0.5B, 1.5B, 3B, 7B, 14B, 32B | 128K | Apache 2.0 except 3B | 5.5T additional code tokens. arXiv:2409.12186 |
| Qwen2.5-Math | 2024-09-16/19 | 1.5B, 7B, 72B | 4K | Qwen License (72B) | CoT + TIR + RM. arXiv:2409.12122 |
| Qwen2.5-Math-PRM | 2025-01-13 | 7B, 72B | — | Qwen License | Process reward models |
| Qwen2.5-1M | 2025-01-23 | 7B, 14B | **1,010,000 tokens** | Apache 2.0 | Dual Chunk Attention + sparse attention. arXiv:2501.15383 |
| Qwen2.5-VL | 2025-01-26/27 | 3B, 7B, 32B, 72B | 128K | Apache 2.0 (7B/32B); Qwen License (3B, 72B) | Document parsing, video grounding, agentic GUI. arXiv:2502.13923 |
| Qwen2.5-Omni | 2025-03-22 (3B: 2025-04-30) | 3B, 7B | — | Apache 2.0 | Thinker–Talker; text/audio/image/video in, text+speech out |
| Qwen2.5-Max | Jan 2025 | undisclosed (API only) | — | proprietary | MoE flagship, not open-weighted |

Technical report: **arXiv:2412.15115**, "Qwen2.5 Technical Report", 19 December 2024.

### Reasoning line — QwQ and QVQ (2024–2025)

| Model | First published | Size | Context | Licence | Notes |
|---|---|---|---|---|---|
| QwQ-32B-Preview | 2024-11-27 | 32B | 32K | Apache 2.0 | First open Qwen reasoning model |
| QVQ-72B-Preview | 2024-12-24 | 73,405,560,320 | 32K | Qwen License | Visual reasoning |
| **QwQ-32B** | 2025-03-05 | 32,763,876,352 | 131K | **Apache 2.0** | RL-trained reasoner. 2,963 likes — one of the most-liked Qwen repos |

QwQ-32B is historically important: it was the first widely-credible demonstration that a 32B open model could be RL-trained into competitive long-chain reasoning, and it is the direct ancestor of the thinking mode built into Qwen3.

### Generation 3 — Qwen3 (2025)

Announced **29 April 2025**; weights first published 27 April 2025. The first generation with unified hybrid thinking/non-thinking modes in a single checkpoint.

| Model | First published | Params (exact where known) | Active | Context | Licence |
|---|---|---|---|---|---|
| Qwen3-0.6B / -Base | 2025-04-27/28 | 0.6B | dense | 32,768 | Apache 2.0 |
| Qwen3-1.7B | 2025-04-27 | 1.7B | dense | 32,768 | Apache 2.0 |
| Qwen3-4B | 2025-04-27 | 4B | dense | 32,768 | Apache 2.0 |
| Qwen3-8B | 2025-04-27 | 8B | dense | 40,960 native / 131,072 YaRN | Apache 2.0 |
| Qwen3-14B | 2025-04-27 | 14B | dense | 40,960 / 131,072 | Apache 2.0 |
| Qwen3-32B | 2025-04-27 | 32B | dense | 40,960 / 131,072 | Apache 2.0 |
| **Qwen3-30B-A3B** | 2025-04-27 | 30,532,122,624 | 3B (128 experts, top-8) | 40,960 / 131,072 | Apache 2.0 |
| **Qwen3-235B-A22B** | 2025-04-27 | 235,093,634,560 | 22B (128 experts, top-8) | 40,960 / 131,072 | Apache 2.0 |

Technical report: **arXiv:2505.09388**, "Qwen3 Technical Report", 14 May 2025. Pretraining reported at 36 trillion tokens across 119 languages and dialects.

**The 2507 refresh** — Qwen abandoned the single hybrid checkpoint and split thinking from non-thinking:

| Model | First published | Note |
|---|---|---|
| Qwen3-235B-A22B-Instruct-2507 | 2025-07-21 | Non-thinking; 256K context |
| Qwen3-235B-A22B-Thinking-2507 | 2025-07-25 | Thinking-only |
| Qwen3-30B-A3B-Instruct-2507 | 2025-07-28 | |
| Qwen3-30B-A3B-Thinking-2507 | 2025-07-29 | |
| Qwen3-4B-Instruct-2507 / -Thinking-2507 | 2025-08-05 | Final 2507 releases |
| 1M-token support added to 2507 models | 2025-08-08 | Per Qwen3 README |

> The 2507 Instruct models **do not emit `<think>` blocks at all**, and `enable_thinking=False` is no longer needed for them. This is a common source of confusion when migrating template code between Qwen3 and Qwen3-2507.

**Specialist lines on the Qwen3 base:**

| Model | First published | Params | Context | Licence |
|---|---|---|---|---|
| Qwen3-Reranker 0.6B / 4B / 8B | 2025-05-29 / 06-03 | 8,188,548,096 (8B) | 32K | Apache 2.0 |
| Qwen3-Embedding 0.6B / 4B / 8B | 2025-06-03 | 7,567,295,488 (8B) | 32K | Apache 2.0 |
| Qwen3-Coder-480B-A35B-Instruct | 2025-07-22 | 480,154,875,392 | 256K → 1M | Apache 2.0 |
| Qwen3-Coder-30B-A3B-Instruct | 2025-07-31 | 30,532,122,624 | 256K | Apache 2.0 |
| **Qwen3-Next-80B-A3B** Instruct/Thinking | 2025-09-09 (announced 09-11) | 81,324,862,720 | 262,144 | Apache 2.0 |
| Qwen3-Omni-30B-A3B Instruct/Thinking/Captioner | 2025-09-15/20 | 35,259,818,545 | — | Apache 2.0 |
| Qwen3Guard-Gen / -Stream 0.6B/4B/8B | 2025-09-23 | | | Apache 2.0 |
| Qwen3-VL-235B-A22B Instruct/Thinking | 2025-09-22 | 235,670,022,896 | 256K → 1M | Apache 2.0 |
| Qwen3-VL 30B-A3B / 8B / 4B / 32B / 2B | 2025-09-30 → 2025-10-20 | | 256K | Apache 2.0 |
| Qwen3-VL-Embedding / -Reranker 2B, 8B | 2026-01-07 | | | Apache 2.0 |
| Qwen3-TTS 0.6B / 1.7B (Base, CustomVoice, VoiceDesign) | 2026-01-21 | | | Apache 2.0 |
| Qwen3-ASR 0.6B / 1.7B; Qwen3-ForcedAligner-0.6B | 2026-01-28 | | | Apache 2.0 |
| Qwen3-Coder-Next | 2026-01-30 | | | Apache 2.0 |

**Qwen3-Next-80B-A3B is the architectural pivot point.** Released 9 September 2025, it introduced the hybrid Gated DeltaNet / gated-attention layout, 512 experts with top-10 routing plus a shared expert, 262,144-token native context, and partial RoPE — the design that became Qwen3.5. Only 3B of 80B parameters are active per token. Technical reports: **arXiv:2511.21631** (Qwen3-VL), **arXiv:2509.17765** (Qwen3-Omni), **arXiv:2506.05176** (Qwen3 Embedding), **arXiv:2603.00729** (Qwen3-Coder-Next).

### Generation 3.5 — Qwen3.5 (2026)

Released **16 February 2026** with the 397B-A17B flagship; smaller sizes followed. All Apache 2.0. All are natively multimodal (image-text-to-text pipeline tag) — the vision encoder is not a bolt-on but part of an early-fusion pretrain.

| Model | Released | Params (exact) | Active | Layers | Context | Licence |
|---|---|---|---|---|---|---|
| **Qwen3.5-397B-A17B** | 2026-02-16 | 403,397,928,944 | ~17B | 60 | 262,144 → 1,010,000 | Apache 2.0 |
| Qwen3.5-122B-A10B | 2026-02-24 | 125,086,497,008 | ~10B | | 262,144 | Apache 2.0 |
| Qwen3.5-35B-A3B | 2026-02-24 | 35,951,822,704 | ~3B | | 262,144 | Apache 2.0 |
| **Qwen3.5-27B** (dense) | 2026-02-24 | 27,781,427,952 | dense | 64 | 262,144 → 1,010,000 | Apache 2.0 |
| Qwen3.5-9B | 2026-03-02 | 9,653,104,368 | dense | | 262,144 | Apache 2.0 |
| Qwen3.5-4B | 2026-03-02 | 4,659,865,088 | dense | 32 | 262,144 | Apache 2.0 |
| Qwen3.5-2B | 2026-03-02 | 2,274,069,824 | dense | | 262,144 | Apache 2.0 |
| Qwen3.5-0.8B | 2026-03-02 | 873,438,784 | dense | | 262,144 | Apache 2.0 |

Base variants (`-Base`) and FP8 and GPTQ-Int4 checkpoints were published alongside. Qwen3.5-Omni has a technical report at **arXiv:2604.15804** (17 April 2026).

Claimed characteristics, per the official README (self-reported):
- **Unified vision-language foundation** — "early fusion training on trillions of multimodal tokens achieves cross-generational parity with Qwen3 and outperforms Qwen3-VL models."
- **Efficient hybrid architecture** — "Gated Delta Networks combined with sparse Mixture-of-Experts."
- **Scalable RL generalization** — "reinforcement learning scaled across million-agent environments."
- **201 languages and dialects.**
- **Near-100% multimodal training efficiency** relative to text-only training.

Self-reported benchmarks for Qwen3.5-27B: MMLU-Pro 86.1, IFEval 95.0, SWE-bench Verified 72.4, MMMU-Pro 75.0, MathVision 86.0. For Qwen3.5-4B: MMLU-Pro 79.1, C-Eval 85.1, IFEval 89.8, MMMU-Pro 66.3, MathVista (mini) 85.1, VideoMME (with subtitles) 83.5.

### Generation 3.6 — Qwen3.6 (April 2026)

A stability-and-coding refresh on the same architecture; parameter counts are identical to the Qwen3.5 equivalents, so these are retrained/re-post-trained checkpoints rather than new architectures.

| Model | Released | Params | Licence | Focus |
|---|---|---|---|---|
| Qwen3.6-35B-A3B | 2026-04-15/16 | 35,951,822,704 | Apache 2.0 | "Agentic Coding Power, Now Open to All" |
| Qwen3.6-27B | 2026-04-21/22 | 27,781,427,952 | Apache 2.0 | "Flagship-Level Coding in a 27B Dense Model" |

Both introduced **thinking preservation** — retaining reasoning context across conversation history, exposed as the `preserve_thinking` chat-template flag.

### Generation 3.7 — API only

The FY2026 20-F (filed 20 May 2026) names **Qwen3.7-Max** as "our latest generation large language model... specifically engineered for agents." No Qwen3.7 open weights were published. If you see "Qwen3.7" referenced, it is the hosted Max tier.

### Generation 3.8 — Qwen3.8 (August 2026), current

| Model | Released | Params (exact) | Active | Layers | Context | Licence |
|---|---|---|---|---|---|---|
| **Qwen3.8-2.4T-A95B** (Qwen3.8-Max) | 2026-08-12 (repo 08-08) | 2,446,182,725,504 | 95B | 92 | 262,144 → 1,010,000 | **Qwen3.8-Max License** |
| Qwen3.8-2.4T-A95B-FP8 | 2026-08-12 | — | | | | Qwen3.8-Max License |
| **Qwen3.8-27B** | 2026-08-14 (repo 08-05) | 27,781,427,952 | dense | 64 | 262,144 → ~1,000,000 | **Apache 2.0** |
| Qwen3.8-27B-FP8 | 2026-08-13 | — | | | | Apache 2.0 |

Per the June 2026 quarterly results: "In August, we launched our flagship foundation model Qwen3.8-Max within three months of its prior version, and we opened its model weights with 2.4 trillion parameters." This is the first time Alibaba has open-weighted a Max-tier model.

Stated enhancements over Qwen3.5/3.6 (self-reported): comprehensive gains in coding, professional work, research and long-horizon agentic tasks; stronger autonomous planning and handling of environment feedback; broader harness compatibility; and **flexible thinking control via `reasoning_effort`** with **`preserve_thinking`** for reasoning context across turns.

Self-reported benchmarks for Qwen3.8-27B: SWE-bench Pro 61.7, Terminal Bench 73.0, DeepSWE 42.2, OSWorld 84.3%, WebArena 64.8%, Android 81.9%, GPQA Diamond 89.2, LiveCodeBench 90.3.

Architecture (from `config.json`, verified 25 August 2026):

**Qwen3.8-27B** — `Qwen3_5ForConditionalGeneration`, `model_type: qwen3_5`. Hidden 5,120; 64 layers as 16 × (3 × linear-attention → 1 × full-attention); Gated DeltaNet with 48 value heads / 16 key heads at 128 dim, conv kernel 4; gated attention 24 Q heads / 4 KV heads at head_dim 256 with `partial_rotary_factor` 0.25 (i.e. 64 rotary dims); FFN intermediate 17,408; `full_attention_interval` 4; vocab 248,320; `rope_theta` 10,000,000 with interleaved M-RoPE section [11, 11, 10]; MTP head with `mtp_num_hidden_layers: 1`; vision tower 27 layers, hidden 1,152, patch 16, spatial merge 2, temporal patch 2.

**Qwen3.8-2.4T-A95B** — `Qwen3_5MoeForCausalLM`. Hidden 8,192; 92 layers as 23 × (3 × (Gated DeltaNet → MoE) → 1 × (Gated Attention → MoE)); Gated DeltaNet 128 value heads / 16 key heads at 128 dim; gated attention 64 Q / 4 KV heads at head_dim 256, 64 rotary dims; **512 experts, 10 routed + 1 shared active**, expert intermediate 2,048; vocab 248,320; MTP.

### The Max tier — what is not open

Alibaba maintains an API-only flagship line that runs ahead of the open releases: Qwen-Max (2024), Qwen2.5-Max (January 2025), Qwen3-Max (2025), Qwen3.7-Max (2026), Qwen3.8-Max — the last of which was then open-weighted as Qwen3.8-2.4T-A95B. Access is through **QwenCloud** / Model Studio (DashScope), which is OpenAI- and Anthropic-API-compatible. Parameter counts for the closed versions are not disclosed.

Other non-weight products: **Qwen Studio** (chat.qwen.ai), **Qoder** (agentic coding), **QwenWork** (enterprise agent platform), **Qwen Code** (open-source terminal coding agent, 27,000+ GitHub stars, Apache 2.0), **Wan** (video generation, now Wan3.0), **Qwen-Image** / **Qwen-Image-Edit**, and specialist research models (Qwen-AgentWorld, Qwen-RobotNav, Qwen-RobotManip, Qwen-Music, HappyShrimp music, HappyOyster world model, HappyHorse multimodal).

## Licensing — read this before shipping

Four distinct licences appear across the family. The difference is commercially material.

**1. Apache 2.0** — the majority, including all Qwen3, Qwen3.5, Qwen3.6 and Qwen3.8-27B open weights, Qwen3-Coder, Qwen3-VL, Qwen3-Omni, Qwen3-Embedding and Qwen3-Reranker. Standard, permissive, patent grant included, no field-of-use restriction, no user-count trigger, no acceptable-use policy appended. You can fine-tune, redistribute, sell, and keep your derivatives closed.

**2. The Qwen3.8-Max License** (Qwen3.8-2.4T-A95B only, © 2026 Qwen). An MIT-style permission grant — "use, copy, modify, merge, publish, distribute, sublicense, sell, deploy, host, fine-tune, and create derivative works" — subject to two conditions:

> **Condition 1 (attribution at scale).** If used in a commercial product or service with **more than 100,000,000 monthly active users or US$20,000,000 monthly revenue**, "respective model name must be prominently displayed on the user interface of such product or service."
>
> **Condition 2 (the MaaS / AI Work Assistant carve-out).** If the licensee or its affiliates run a **Model as a Service or AI Work Assistant business** and aggregate revenue exceeds **US$50,000,000 over any consecutive twelve months**, a separate licence from Qwen must be obtained before any commercial use. This does **not** apply to purely internal use that does not expose the model, its outputs or its capabilities to third parties.
>
> "Model as a Service" is defined as giving a third party access to inference or fine-tuning (API or hosted endpoint) in a way that lets them meaningfully control inputs, parameters or training data — explicitly excluding mere relaying of requests to models hosted by others. "AI Work Assistant" means an independent AI product primarily for AI-assisted coding or office productivity (Qoder and QwenWork are the named examples); it excludes single-purpose tools, assistants for other domains, and AI features inside a product whose primary purpose is not coding or office productivity.

The practical read: this is aimed squarely at rival inference clouds and rival coding assistants. An individual, a startup under US$50 m, or an enterprise using it internally is unconstrained. A company reselling Qwen3.8-Max inference at scale, or building a competitor to Qoder on top of it, needs to talk to Alibaba. Contact given in the licence: `model-business@notice.qwencloud.com`.

**3. The Qwen License Agreement** (release date **19 September 2024**) — applies to Qwen2.5-72B, Qwen2.5-3B, Qwen2.5-Math-72B, Qwen2.5-VL-3B and -72B, QVQ-72B-Preview. Grants a non-exclusive, worldwide, non-transferable, royalty-free licence to use, reproduce, distribute and modify. Redistribution conditions: pass on the agreement, mark modified files, and retain the notice "Qwen is licensed under the Qwen LICENSE AGREEMENT, Copyright (c) Alibaba Cloud. All Rights Reserved." It carries a **100 million monthly active user** threshold above which a separate licence must be requested from Alibaba Cloud.

**4. Tongyi Qianwen licence** — Qwen 1, Qwen1.5, Qwen2-72B, Qwen2-Math-72B, Qwen2-VL-72B. Similar structure to (3) with a 100 million MAU trigger.

> ⚠️ **Check the LICENSE file in the specific repository you download.** The licence varies by *size within a generation*, not just by generation. Qwen2.5-7B is Apache 2.0; Qwen2.5-3B is not. Qwen3.8-27B is Apache 2.0; Qwen3.8-2.4T-A95B is not.

## Reading the naming convention

- `Qwen3.5-397B-A17B` — 397B total parameters, **A**ctive 17B per token (MoE). The reported total (403.4B by exact count) does not always match the name; the name is rounded.
- `-Instruct` / `-Thinking` — post-2507, separate checkpoints for non-reasoning and reasoning behaviour. Qwen3.5/3.6/3.8 returned to a single checkpoint with `reasoning_effort` control.
- `-Base` — pretrained only, no instruction tuning. This is what you want for continued pretraining or when you intend to do your own full SFT.
- `-FP8` — 8-bit floating-point weights for server inference (vLLM/SGLang on Hopper+ hardware). Not the same as an INT8 quantisation.
- `-GPTQ-Int4`, `-AWQ` — 4-bit post-training quantisations published by Qwen itself.
- `-MLX`, `-GGUF` — format conversions; Qwen published first-party MLX repos for Qwen3 (May–June 2025) but the community `mlx-community` org is the more complete source for later generations.
- `-MTP` — the multi-token-prediction head, distributed as a separate small repo for use as a speculative-decoding draft model.
- `-2507`, `-2512`, `-0813` — date stamps (YYMM or MMDD) for refresh checkpoints.
- `-A95B`, `-A3B`, `-A22B` — active parameter count.
- `Qwen3.8-Max` (marketing) = `Qwen3.8-2.4T-A95B` (repository).

## What actually changed, generation to generation

| Generation | The one thing that changed |
|---|---|
| Qwen → Qwen1.5 | Mainline `transformers` support; no more `trust_remote_code` |
| Qwen1.5 → Qwen2 | GQA everywhere; first serious MoE; 128K context via YaRN |
| Qwen2 → Qwen2.5 | Scale of pretraining data (18T tokens) and the breadth of the size ladder; the generation that became the community default base |
| Qwen2.5 → Qwen3 | Unified thinking/non-thinking in one checkpoint; 36T-token multilingual pretrain; strong small MoE (30B-A3B) |
| Qwen3 → Qwen3-2507 | Thinking and non-thinking split back into separate checkpoints; 256K–1M context |
| Qwen3-2507 → Qwen3-Next | **Hybrid Gated DeltaNet + full attention**; ultra-sparse MoE (512 experts, top-10 + shared); 262K native context |
| Qwen3-Next → Qwen3.5 | Native early-fusion multimodality across the whole size ladder; 201 languages; MTP; vocab to 248,320; RL at "million-agent" scale |
| Qwen3.5 → Qwen3.6 | Post-training refresh for agentic coding; `preserve_thinking` |
| Qwen3.6 → Qwen3.8 | `reasoning_effort` control; Max-class model open-weighted at 2.4T |

## Sources

- [Qwen organisation model index, Hugging Face API](https://huggingface.co/api/models?author=Qwen&sort=createdAt) — creation dates, exact `safetensors.total` parameter counts, licence tags, download and like counts for all 462 repositories, retrieved 25 August 2026
- [QwenLM/Qwen3.8 README](https://github.com/QwenLM/Qwen3.8) — dated news entries for Qwen3.5, 3.6 and 3.8, citation block, deployment commands
- [QwenLM/Qwen3 README](https://github.com/QwenLM/Qwen3) — dated news entries back to Qwen1.5 (2024-02-05)
- [Qwen/Qwen3.8-2.4T-A95B model card](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B) and [config.json](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/raw/main/config.json)
- [Qwen3.8-Max License](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/raw/main/LICENSE) — full text of both commercial conditions
- [Qwen LICENSE AGREEMENT, 19 September 2024](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct/raw/main/LICENSE)
- [Qwen/Qwen3.8-27B config.json](https://huggingface.co/Qwen/Qwen3.8-27B/raw/main/config.json), [Qwen3.5-397B-A17B config.json](https://huggingface.co/Qwen/Qwen3.5-397B-A17B/raw/main/config.json), [Qwen3.5-4B config.json](https://huggingface.co/Qwen/Qwen3.5-4B/raw/main/config.json), [Qwen3-Next-80B-A3B-Instruct config.json](https://huggingface.co/Qwen/Qwen3-Next-80B-A3B-Instruct/raw/main/config.json), [Qwen3-8B config.json](https://huggingface.co/Qwen/Qwen3-8B/raw/main/config.json)
- [Alibaba Group Form 20-F FY2026](https://www.sec.gov/Archives/edgar/data/1577552/000119312526231755/baba-20260331.htm) — Qwen3.7-Max naming, Qwen app launch date
- [Alibaba June Quarter 2026 Results](https://data.alibabagroup.com/ecms-files/1532295521/fa5d65fc-9b3e-4e82-a8fc-4ce1c3e2c407/Alibaba%20Group%20Announces%20June%20Quarter%202026%20Results.pdf) — Qwen3.8-Max open-weighting statement
- arXiv abstracts verified via the arXiv API: 2309.16609, 2308.12966, 2311.07919, 2407.10671, 2407.10759, 2409.12191, 2409.12122, 2409.12186, 2412.15115, 2501.15383, 2502.13923, 2505.09388, 2506.05176, 2509.17765, 2511.21631, 2603.00729, 2604.15804

## Open questions

- **No Qwen3.5 or Qwen3.8 technical report exists on arXiv** as of 25 August 2026. Architecture in this file for those generations is reconstructed from configuration files and model cards.
- Context lengths for the earliest models (Qwen 1, Qwen1.5) are from convention and are `needs-verification` against the original model cards.
- Qwen3.5-122B-A10B and -35B-A3B layer counts, expert counts and per-model context extension limits were not individually verified; only 397B-A17B, 27B and 4B configs were read.
- Active parameter counts marked "~" are derived from the model name, not measured.
- Qwen1.5-MoE-A2.7B's exact publication date was not in the API extract used; the 2024-03-28 announcement date is from the Qwen3 README.
- Qwen3.8-2.4T-A95B benchmark figures were not extracted from its model card in this pass; the 27B figures above are from its card. Both are self-reported.
