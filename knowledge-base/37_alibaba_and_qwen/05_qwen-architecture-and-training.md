---
id: alibaba.qwen_architecture
title: Qwen architecture and training — from GQA transformers to Gated DeltaNet hybrids
domain: 37_alibaba_and_qwen
tags: [qwen, transformer, grouped-query-attention, swiglu, rmsnorm, rope, yarn, dual-chunk-attention, gated-deltanet, linear-attention, mixture-of-experts, tokenizer, sft, rlhf, dpo, grpo, gspo, distillation, quantisation, multi-token-prediction]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Qwen Technical Report (arXiv:2309.16609)", url: "https://arxiv.org/abs/2309.16609", publisher: "Qwen Team, Alibaba Group", accessed: 2026-08-25}
  - {title: "Qwen2 Technical Report (arXiv:2407.10671)", url: "https://arxiv.org/abs/2407.10671", publisher: "Qwen Team", accessed: 2026-08-25}
  - {title: "Qwen2.5 Technical Report (arXiv:2412.15115)", url: "https://arxiv.org/abs/2412.15115", publisher: "Qwen Team", accessed: 2026-08-25}
  - {title: "Qwen2.5-1M Technical Report (arXiv:2501.15383)", url: "https://arxiv.org/abs/2501.15383", publisher: "Qwen Team", accessed: 2026-08-25}
  - {title: "Qwen3 Technical Report (arXiv:2505.09388)", url: "https://arxiv.org/abs/2505.09388", publisher: "Qwen Team", accessed: 2026-08-25}
  - {title: "GSPO: Towards Scalable Reinforcement Learning for Language Models", url: "https://qwenlm.github.io/blog/", publisher: "Qwen Team", accessed: 2026-08-25}
  - {title: "Qwen/Qwen3.8-27B config.json", url: "https://huggingface.co/Qwen/Qwen3.8-27B/raw/main/config.json", publisher: "Qwen / Alibaba Cloud", accessed: 2026-08-25}
  - {title: "Qwen/Qwen3.8-2.4T-A95B config.json", url: "https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/raw/main/config.json", publisher: "Qwen / Alibaba Cloud", accessed: 2026-08-25}
related: [alibaba.qwen_models, alibaba.qwen_local, alibaba.qwen_finetune, alibaba.open_weight_landscape]
---

# Qwen architecture and training — from GQA transformers to Gated DeltaNet hybrids

**Summary.** Qwen 1 through Qwen3 were conventional decoder-only transformers: pre-norm RMSNorm, SwiGLU feed-forward, rotary position embeddings, grouped-query attention, untied embeddings, byte-level BPE with a ~152,000-token vocabulary. The architectural break came with **Qwen3-Next** (September 2025) and became the family standard in **Qwen3.5** (February 2026): three Gated DeltaNet linear-attention layers for every one gated softmax-attention layer, ultra-sparse mixture-of-experts (512 experts, top-10 routed plus one shared), partial rotary embeddings on a head dimension of 256, a 248,320-token vocabulary, and a multi-token-prediction head. The practical consequence is that only one layer in four maintains a KV cache that grows with sequence length — which is why a 27B model can serve a 262,144-token context in roughly 16 GiB of cache instead of roughly 64 GiB.

> ⚠️ **Confidence note.** Everything about Qwen 1 through Qwen3 is sourced to published technical reports (high confidence). Everything about Qwen3.5 / 3.6 / 3.8 is reconstructed from configuration files, model cards and the release README, because **no technical report for those generations exists on arXiv as of 25 August 2026**. Where the mechanism is inferred rather than stated, this file says so.

## Key facts

| Component | Qwen2 / Qwen2.5 / Qwen3 | Qwen3-Next / Qwen3.5 / 3.6 / 3.8 |
|---|---|---|
| Attention | Grouped-query attention, all layers | 3 × Gated DeltaNet + 1 × gated full attention, repeating |
| Head dim | 128 | 256 (attention layers) |
| Rotary coverage | Full head dim | `partial_rotary_factor` 0.25 → 64 of 256 dims |
| RoPE base | 1,000,000 (Qwen2.5/3) | 10,000,000 |
| Positional scheme | RoPE (+ M-RoPE in VL models) | Interleaved M-RoPE, section [11, 11, 10] |
| Normalisation | RMSNorm, pre-norm, eps 1e-6 | RMSNorm, eps 1e-6 |
| FFN | SwiGLU (`hidden_act: silu`) | SwiGLU |
| Vocabulary | 151,936 (Qwen3) / 152,064 (Qwen2.5) | **248,320** (padded) |
| MoE routing | 128 experts, top-8, no shared expert (Qwen3) | **512 experts, top-10 routed + 1 shared** |
| Native context | 32,768–40,960 | **262,144** |
| Extended context | 131,072 (YaRN) / 1,010,000 (Qwen2.5-1M, DCA) | ~1,010,000 |
| Speculative decoding | none built in | **Multi-token prediction head** (`mtp_num_hidden_layers: 1`) |
| Attention output gate | no | `attn_output_gate: true` |

## Part 1 — the classical Qwen transformer (Qwen 1 → Qwen3)

### The base recipe

Every Qwen text model from 2023 to mid-2025 is a decoder-only transformer with:

- **Pre-normalisation with RMSNorm.** Root-mean-square layer normalisation, `rms_norm_eps: 1e-6`, applied before each sub-block rather than after. RMSNorm drops the mean-centring of LayerNorm, keeping only the scale, which is cheaper and empirically no worse for transformers.
- **SwiGLU feed-forward.** `hidden_act: silu` with a gated pair of projections: `FFN(x) = W_down( SiLU(W_gate x) ⊙ W_up x )`. Three matrices instead of two, so the intermediate dimension is set to roughly 8/3 of hidden rather than 4× to keep parameter count comparable. Qwen3-8B: hidden 4,096, intermediate 12,288 (exactly 3×).
- **Rotary position embeddings (RoPE)** applied to queries and keys, with `rope_theta` raised from the original 10,000 to **1,000,000** in Qwen2.5 and Qwen3. A larger base spreads the rotation frequencies out, which extends the range over which positions stay distinguishable — a prerequisite for long-context extension.
- **Untied input and output embeddings** (`tie_word_embeddings: false`) for models above roughly 1B parameters; tied for the smallest ones (Qwen3.5-4B still ties).
- **QK-Norm.** Qwen3 introduced per-head RMSNorm on queries and keys before the attention dot product, replacing the QKV bias used in Qwen2. This is a training-stability measure: it prevents attention logits from drifting to extreme magnitudes in deep models.
- **No attention bias** (`attention_bias: false`), no dropout at inference (`attention_dropout: 0.0`).

### Grouped-query attention

From Qwen2 onward every size uses GQA rather than multi-head attention. Multiple query heads share one key/value head, which shrinks the KV cache by the ratio of query heads to KV heads.

Qwen3-8B (verified from `config.json`): 32 attention heads, **8 key/value heads**, head dim 128, 36 layers. The KV cache per token is therefore

```
2 (K and V) × 36 layers × 8 kv_heads × 128 head_dim × 2 bytes (fp16)
  = 147,456 bytes = 144 KiB per token
```

At 32,768 tokens that is 4.83 GB. With MHA (32 KV heads) it would be 19.3 GB. That 4× saving is the entire reason GQA is universal.

Qwen3-30B-A3B pushes further: 32 query heads to **4** KV heads. Qwen3-235B-A22B: 64 query heads to 4 KV heads.

### The MoE design (Qwen2-57B-A14B, Qwen3-30B-A3B, Qwen3-235B-A22B)

Qwen3's MoE layers, from `config.json`:

- `num_experts: 128`, `num_experts_per_tok: 8` — every token is routed to 8 of 128 experts.
- `decoder_sparse_step: 1`, `mlp_only_layers: []` — **every** layer is an MoE layer, not every other one.
- `moe_intermediate_size: 768` (30B-A3B) or `1536` (235B-A22B) — each expert is a small SwiGLU FFN.
- `norm_topk_prob: true` — the top-k router probabilities are renormalised to sum to 1.
- `router_aux_loss_coef: 0.001` — a load-balancing auxiliary loss with a small coefficient.
- **No shared expert** in Qwen3, unlike DeepSeek's design. This changed in Qwen3-Next.

Qwen3-30B-A3B activates 3B of 30B parameters per token. The consequence for local inference is important and often misunderstood: **you must hold all 30B parameters in memory** (any token may route anywhere), but you only *compute* with 3B of them. So an MoE gives you dense-model quality at sparse-model speed, at dense-model memory cost. On a memory-rich, bandwidth-limited machine like a Mac, that is a favourable trade.

### Long-context extension

Three mechanisms, layered:

**YaRN (Yet another RoPE extensioN).** A frequency-dependent interpolation of RoPE that stretches position encodings beyond the trained window. Applied at inference by setting `rope_scaling` in `config.json`, e.g. `{"rope_type": "yarn", "factor": 4.0, "original_max_position_embeddings": 32768}`. Qwen3's 40,960 native window becomes 131,072 this way. The cost is a small degradation on *short* prompts, which is why Qwen ships YaRN off by default and documents it as opt-in.

**Dual Chunk Attention (DCA).** Introduced for **Qwen2.5-1M** (arXiv:2501.15383). DCA remaps relative positions so that positions within a chunk, across adjacent chunks, and between distant chunks are each handled by a distinct scheme — allowing a model trained on 32K to attend coherently at 1M without further training. Combined with sparse attention kernels for the actual computation, this is what made 1,010,000-token context practical rather than theoretical.

**Progressive length training.** Qwen2 and Qwen2.5 extend the training context in stages (4K → 32K → 128K) rather than training long from the start, which is far cheaper.

### Tokenizer

Byte-level byte-pair encoding, `Qwen2Tokenizer` class, with the GPT-4-style pretokenisation regex (verified in `tokenizer_config.json`):

```
(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?[\p{L}\p{M}]+|\p{N}| ?[^\s\p{L}\p{M}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+
```

Note `\p{N}` alone — **digits are split individually**, which measurably improves arithmetic. Vocabulary sizes: 151,936 (Qwen2, Qwen3), 152,064 (Qwen2.5), and **248,320** from Qwen3.5 onward. The jump of ~96,000 tokens accompanies the expansion from "100+ languages" to "201 languages and dialects" and the addition of multimodal special tokens.

Control tokens are ChatML: `<|im_start|>`, `<|im_end|>`, `<|endoftext|>`, plus `<|object_ref_start|>`, `<|box_start|>`, `<|quad_start|>`, `<|vision_start|>`, `<|image_pad|>`, `<|video_pad|>`, `<|audio_start|>`, `<|audio_pad|>` and their closers — 33 added special tokens in Qwen3.8-27B. In Qwen3.8-27B, `<|endoftext|>` is 248,044, `<|im_start|>` is 248,045, `<|im_end|>` is 248,046, and `eos_token` is `<|im_end|>`.

The tokenizer has been essentially stable across Qwen2 → Qwen3, which is why LoRA adapters and quantisation recipes port easily within that range, and why the Qwen3.5 vocabulary change is a hard break.

### Pretraining data as disclosed

| Generation | Reported pretraining scale |
|---|---|
| Qwen 1 | 2.2–3 trillion tokens |
| Qwen2 | 7 trillion tokens (12T trialled for some sizes) |
| Qwen2.5 | **18 trillion tokens** |
| Qwen3 | **36 trillion tokens across 119 languages and dialects** |
| Qwen3.5 | "trillions of multimodal tokens", early fusion; 201 languages — no total disclosed |

Composition disclosures are thin across the industry and Qwen is no exception: the reports describe web data, code, mathematics, books and synthetic data, with quality filtering by classifier and deduplication, but give no proportions and no source list. Qwen2.5 and Qwen3 both describe using earlier Qwen models to generate and filter synthetic data — Qwen2.5-Math and Qwen2.5-Coder are named as generators for the Qwen3 corpus. This is `needs-verification` beyond what the reports state, and the reports do not permit reproduction.

## Part 2 — the Gated DeltaNet hybrid (Qwen3-Next → Qwen3.8)

This is the architecture that matters for anyone running Qwen locally today.

### The layout

From `Qwen/Qwen3.8-27B/config.json`, `layer_types` is a 64-element list with the pattern:

```
linear_attention, linear_attention, linear_attention, full_attention,  (× 16)
```

`full_attention_interval: 4`. Described in the model card as `16 × (3 × (Gated DeltaNet → FFN) → 1 × (Gated Attention → FFN))`. The MoE flagship uses the same pattern over 92 layers with MoE in place of FFN: `23 × (3 × (Gated DeltaNet → MoE) → 1 × (Gated Attention → MoE))`.

### What Gated DeltaNet is

Gated DeltaNet is a linear-attention / state-space variant. Instead of storing every past key-value pair and computing an O(n²) attention matrix, it maintains a **fixed-size matrix-valued recurrent state** that is updated per token with a *delta rule* — a rank-one corrective write that removes the old association for a key before writing the new one — combined with a learned **gate** that decays the state.

The configuration fields:

```
linear_num_value_heads: 48      (128 in the 2.4T model)
linear_num_key_heads:   16
linear_key_head_dim:    128
linear_value_head_dim:  128
linear_conv_kernel_dim: 4       short causal depthwise convolution before the recurrence
output_gate_type:       swish
mamba_ssm_dtype:        float32 state kept in fp32 for numerical stability
```

State size per layer is on the order of `num_value_heads × value_head_dim × key_head_dim` = 48 × 128 × 128 ≈ 786,432 elements, i.e. about 3.1 MB at fp32. Across 48 linear layers that is roughly **150 MB — constant, regardless of context length**. Compare the KV cache, which grows linearly.

The trade is expressiveness: linear attention cannot perform exact retrieval of an arbitrary earlier token the way softmax attention can. Hence the hybrid — one full-attention layer every four provides the precise recall, and the linear layers carry the bulk of the sequence modelling cheaply.

### The KV-cache arithmetic that makes this matter

Qwen3.8-27B full-attention layers: 16 of 64, with 4 KV heads at head dim 256.

```
per token = 2 × 16 layers × 4 kv_heads × 256 head_dim × 2 bytes
          = 65,536 bytes = 64 KiB per token

at 262,144 tokens = 17.18 GB ≈ 16 GiB
```

Had all 64 layers been full attention, the same context would need **64 GiB**. On a 64 GB Mac that is the difference between "loads a 4-bit 27B with a quarter-million-token context" and "does not load at all."

Qwen3.8-2.4T-A95B: 23 full-attention layers × 4 KV heads × 256 dim → 92 KiB/token → ~23 GiB at 262,144 tokens.

### Gated attention and partial RoPE

The full-attention layers are not vanilla either:

- `attn_output_gate: true` — a learned sigmoid/SiLU gate on the attention output, borrowed from the same family of stability tricks as QK-Norm.
- `head_dim: 256` with `partial_rotary_factor: 0.25` — **only 64 of the 256 dimensions per head carry rotary position information**; the remaining 192 are position-agnostic ("NoPE"). This is a deliberate long-context design: purely positional heads degrade at extrapolation, while position-free dimensions carry content-addressable retrieval that does not care how far away the match is.
- `rope_theta: 10,000,000` — ten times Qwen3's base, consistent with a 262,144 native window.
- **Interleaved M-RoPE** with `mrope_section: [11, 11, 10]` — the 32 rotary frequency pairs are allocated across temporal, height and width axes for multimodal inputs, so a single position scheme covers text, image patches and video frames. M-RoPE originated in Qwen2-VL (arXiv:2409.12191); `mrope_interleaved: true` indicates the axes are interleaved rather than blocked, which improves text-only behaviour when no image is present.

### Ultra-sparse MoE

Qwen3.8-2.4T-A95B: `num_experts: 512`, `num_experts_per_tok: 10`, `shared_expert_intermediate_size: 2048`, `moe_intermediate_size: 2048`. So 10 routed experts plus 1 always-on shared expert out of 512, giving roughly 95B active from 2,446B total — an activation ratio of about **3.9%**.

Two design choices distinguish this from Qwen3's MoE:

1. **The shared expert.** One expert every token always uses, capturing the general-purpose computation, so the routed experts can specialise harder. (DeepSeek pioneered this; Qwen adopted it at Qwen3-Next.)
2. **Far more, far smaller experts.** 512 experts of intermediate size 2,048 rather than 128 of size 1,536. Finer-grained specialisation for the same active budget.

`router_aux_loss_coef: 0.001` and `norm_topk_prob: true` carry over.

### Multi-token prediction

`mtp_num_hidden_layers: 1`, `mtp_use_dedicated_embeddings: false`. A single extra transformer layer is trained to predict token *t+2* given the hidden state that produced token *t+1*. During training this is a denser learning signal. At inference it is a **built-in draft model for speculative decoding** — and the MTP head is distributed as a separate small repository (e.g. `mlx-community/Qwen3.8-27B-MTP-4bit`, 0.27 GB; `unsloth/Qwen3.8-27B-GGUF` ships `MTP/mtp-Qwen3.8-27B-Q4_0.gguf` at 1.37 GB). See `06` for how to use it.

## Part 3 — post-training

### The classical stack (Qwen2 → Qwen3)

**Supervised fine-tuning.** Qwen2.5 reports over 1 million SFT examples; Qwen3 reports a large multi-stage SFT covering instruction following, coding, mathematics, tool use, multilingual tasks and long context, with extensive rejection sampling — generate many candidates from a strong model, keep only those that pass a verifier or reward model.

**Preference optimisation.** Qwen has used the full progression:
- **RLHF with PPO** and a separate reward model in Qwen 1 and Qwen2.
- **DPO (Direct Preference Optimization)** — offline, no reward model, optimises a closed-form objective on preference pairs. Qwen2.5 uses offline DPO followed by online GRPO.
- **GRPO (Group Relative Policy Optimization)** — samples a group of completions per prompt and uses their relative rewards as the advantage, eliminating the value network. Cheap and effective for verifiable domains.
- **GSPO (Group Sequence Policy Optimization)** — Qwen's own contribution, published 27 July 2025. GSPO applies importance ratios and clipping at the **sequence** level rather than the token level, which the team argues is the correct granularity because the reward is assigned to the sequence. The stated motivation is stability when RL-training large MoE models, where token-level ratios are noisy because expert routing changes between the sampling and update policies.

**Reward models.** Qwen ships several openly: Qwen2-Math-RM-72B, Qwen2.5-Math-RM-72B, the Qwen2.5-Math-PRM process reward models (7B and 72B, January 2025) which score individual reasoning steps rather than final answers, and the WorldPM-72B series (May 2025).

### Reasoning-model training

QwQ-32B-Preview (November 2024) and QwQ-32B (March 2025) established the approach that became Qwen3's thinking mode:

1. **Cold-start SFT** on long chain-of-thought traces, filtered so that only traces reaching a verified-correct answer survive.
2. **RL with verifiable rewards** on mathematics and code, where correctness is checkable by execution or symbolic comparison — no reward model needed, so no reward hacking of the usual kind.
3. **General RL** on broader instruction-following and preference data to recover the conversational and safety behaviour that stage 2 erodes.
4. **Thinking-mode fusion** (Qwen3): the thinking and non-thinking behaviours are merged into one checkpoint by training on a mixture where the template signals which mode is expected, then **thinking-budget control** is trained by truncating the reasoning at varying lengths so the model learns to conclude gracefully under a budget.

The Qwen3 report describes a **strong-to-weak distillation** pipeline: the flagship 235B-A22B and 32B models are trained with the full RL pipeline, then the smaller models (0.6B–14B, 30B-A3B) are trained by distilling from them — off-policy distillation on generated traces followed by on-policy distillation matching the teacher's logits. Qwen reports this reaching comparable quality at roughly a tenth of the GPU hours of running full RL on each size, which is why the small Qwen3 models punch above their weight.

### Thinking and non-thinking modes — the actual mechanism

This is template-level, not a separate model. From the verified Qwen3.8-27B chat template:

- With `add_generation_prompt=True` and thinking enabled, the template emits `<|im_start|>assistant\n<think>\n` — the model is *started inside* a thinking block and must close it with `</think>` before answering.
- With `enable_thinking=False`, the template emits `<|im_start|>assistant\n<think>\n\n</think>\n\n` — an empty, already-closed thinking block, so the model proceeds straight to the answer.
- **Qwen3.8 adds `reasoning_effort`**, accepting `xhigh` (default), `medium` or `low`, and an unrecognised value raises a template exception. It is implemented as an injected system instruction, e.g. for `xhigh`: *"Reasoning effort is set to xhigh. Please think carefully through the task, validate key assumptions, consider plausible alternatives, and prioritize correctness, consistency, and clarity in the final answer."* and for `low`: *"Reasoning effort is set to low. Keep your thinking brief and focused, moving directly to the conclusion without unnecessary elaboration."* `medium` injects nothing.
- **`preserve_thinking`** (default true) controls whether `reasoning_content` from earlier assistant turns is replayed into the context. When false, thinking is stripped from all turns before the last user query.

The Qwen3-2507 refresh removed the hybrid entirely, shipping separate `-Instruct` and `-Thinking` checkpoints; Qwen3.5 onward returned to a single checkpoint with effort control. If your code sets `enable_thinking` on a 2507 Instruct model it will be silently ignored — those models never emit `<think>`.

### Multimodal training

The vision path evolved substantially:

- **Qwen-VL (2023):** frozen ViT-bigG encoder, a single-layer cross-attention adapter compressing image features to 256 tokens, and a Qwen-7B language model. Three-stage training.
- **Qwen2-VL (2024):** **Naive Dynamic Resolution** — images are processed at native resolution into a variable number of visual tokens rather than being resized to a fixed grid — plus **M-RoPE** decomposing position into temporal, height and width components so images and video share one scheme with text.
- **Qwen2.5-VL (2025):** window attention in the ViT for linear cost in image size, dynamic FPS sampling for video, absolute-time-aligned M-RoPE, and native document/GUI grounding.
- **Qwen3.5 (2026):** **early fusion** — the model is pretrained on interleaved multimodal tokens from the start rather than adapting a text model afterwards. The README claims this achieves "cross-generational parity with Qwen3 [text-only] and outperforms Qwen3-VL models." The vision tower in Qwen3.8-27B is small relative to the LM: 27 layers, hidden 1,152, `patch_size: 16`, `spatial_merge_size: 2`, `temporal_patch_size: 2`, projecting to the LM's 5,120 hidden. `deepstack_visual_indexes: []` in this checkpoint, meaning the DeepStack multi-level feature injection used in Qwen3-VL is not active here.

The audio path (Qwen-Audio → Qwen2-Audio → Qwen3-ASR/TTS) uses a Whisper-derived encoder; Qwen2.5-Omni and Qwen3-Omni add a **Thinker–Talker** split where a reasoning module produces text and a separate autoregressive module produces streaming speech tokens.

## Part 4 — quantisation-aware considerations

Alibaba publishes first-party quantised checkpoints — FP8, GPTQ-Int4 and AWQ — alongside BF16 for most releases. Three architectural facts affect how well Qwen quantises:

**1. Untied, very large embeddings.** With a 248,320-token vocabulary and hidden 5,120, the input embedding alone is 1.27 billion parameters, and the output head another 1.27 billion. In a 27.8B model that is 9% of parameters in two matrices. Quantisation tools usually keep these at higher precision (mlx-community's Qwen3.8-27B 4-bit repo retains 1.30 billion parameters in BF16), which is why a "4-bit" 27B model occupies 16.08 GB rather than the naive 13.9 GB.

**2. MoE experts quantise unevenly.** Rarely-routed experts see few calibration samples, so activation-aware methods (AWQ, GPTQ) can misestimate their scales. Practically, MoE models tolerate 4-bit less gracefully than dense models of the same active size, and mixed-precision recipes that spend more bits on the router and shared expert do better.

**3. The linear-attention state is precision-sensitive.** `mamba_ssm_dtype: float32` is set explicitly in the config. The recurrent state accumulates over the whole sequence, so error compounds in a way it does not in attention. Quantisation of the DeltaNet state is not something to do casually, and runtimes keep it in fp32 by default.

Practical formats and their trade-offs are covered in `06`.

## Sources

- [Qwen Technical Report, arXiv:2309.16609](https://arxiv.org/abs/2309.16609) — 28 September 2023
- [Qwen2 Technical Report, arXiv:2407.10671](https://arxiv.org/abs/2407.10671) — 15 July 2024 (v4, 10 September 2024)
- [Qwen2.5 Technical Report, arXiv:2412.15115](https://arxiv.org/abs/2412.15115) — 19 December 2024 (v2, 3 January 2025)
- [Qwen2.5-1M Technical Report, arXiv:2501.15383](https://arxiv.org/abs/2501.15383) — 26 January 2025, Dual Chunk Attention
- [Qwen2.5-Coder Technical Report, arXiv:2409.12186](https://arxiv.org/abs/2409.12186); [Qwen2.5-Math, arXiv:2409.12122](https://arxiv.org/abs/2409.12122)
- [Qwen2-VL, arXiv:2409.12191](https://arxiv.org/abs/2409.12191) — Naive Dynamic Resolution, M-RoPE; [Qwen2.5-VL, arXiv:2502.13923](https://arxiv.org/abs/2502.13923)
- [Qwen-VL, arXiv:2308.12966](https://arxiv.org/abs/2308.12966); [Qwen-Audio, arXiv:2311.07919](https://arxiv.org/abs/2311.07919); [Qwen2-Audio, arXiv:2407.10759](https://arxiv.org/abs/2407.10759)
- [Qwen3 Technical Report, arXiv:2505.09388](https://arxiv.org/abs/2505.09388) — 14 May 2025; thinking-mode fusion, thinking budget, strong-to-weak distillation
- [Qwen3-Omni Technical Report, arXiv:2509.17765](https://arxiv.org/abs/2509.17765); [Qwen3-VL Technical Report, arXiv:2511.21631](https://arxiv.org/abs/2511.21631); [Qwen3 Embedding, arXiv:2506.05176](https://arxiv.org/abs/2506.05176); [Qwen3-Coder-Next, arXiv:2603.00729](https://arxiv.org/abs/2603.00729); [Qwen3.5-Omni, arXiv:2604.15804](https://arxiv.org/abs/2604.15804)
- ["GSPO: Towards Scalable Reinforcement Learning for Language Models", Qwen blog, 27 July 2025](https://qwenlm.github.io/blog/)
- Configuration files read directly on 25 August 2026: [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B/raw/main/config.json), [Qwen3.8-2.4T-A95B](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/raw/main/config.json), [Qwen3.5-397B-A17B](https://huggingface.co/Qwen/Qwen3.5-397B-A17B/raw/main/config.json), [Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B/raw/main/config.json), [Qwen3-Next-80B-A3B-Instruct](https://huggingface.co/Qwen/Qwen3-Next-80B-A3B-Instruct/raw/main/config.json), [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B/raw/main/config.json), [Qwen3-30B-A3B](https://huggingface.co/Qwen/Qwen3-30B-A3B/raw/main/config.json), [Qwen3-235B-A22B](https://huggingface.co/Qwen/Qwen3-235B-A22B/raw/main/config.json), [Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/raw/main/config.json)
- [Qwen3.8-27B tokenizer_config.json](https://huggingface.co/Qwen/Qwen3.8-27B/raw/main/tokenizer_config.json) — full chat template, `reasoning_effort` and `preserve_thinking` logic, special tokens, pretokenisation regex

## Open questions

- **No Qwen3.5 / 3.6 / 3.8 technical report exists on arXiv** as of 25 August 2026. The Gated DeltaNet mechanism described here is inferred from configuration fields and the general Gated DeltaNet literature; the *specific* variant Qwen uses is not documented in a citable paper.
- Qwen3-Next has no standalone technical report either; its architecture is documented only in a blog post and configs.
- Pretraining data composition and proportions are undisclosed for every generation. Contamination-control methodology is described only in general terms.
- The training compute (GPU-hours, cluster hardware) for any Qwen model is undisclosed, which matters for the compute-constraint argument in `03` and `08`.
- Whether Qwen3.5+ uses quantisation-aware training for the FP8 checkpoints, or straightforward post-training quantisation, is `needs-verification`.
- The exact Gated DeltaNet state-size accounting above is an order-of-magnitude estimate from the config fields, not a figure Qwen publishes.
