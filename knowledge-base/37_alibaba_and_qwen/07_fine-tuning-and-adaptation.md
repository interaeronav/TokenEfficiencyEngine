---
id: alibaba.qwen_finetune
title: Fine-tuning and adapting Qwen — LoRA, QLoRA, DoRA and the memory maths
domain: 37_alibaba_and_qwen
tags: [qwen, fine-tuning, lora, qlora, dora, mlx-lm, unsloth, axolotl, llama-factory, ms-swift, trl, peft, dataset-format, catastrophic-forgetting, continued-pretraining, evaluation]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "mlx_lm/LORA.md", url: "https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/LORA.md", publisher: "Apple / MLX contributors", accessed: 2026-08-25}
  - {title: "mlx_lm/lora.py CONFIG_DEFAULTS and parser", url: "https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/lora.py", publisher: "Apple / MLX contributors", accessed: 2026-08-25}
  - {title: "mlx_lm/examples/lora_config.yaml", url: "https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/examples/lora_config.yaml", publisher: "Apple / MLX contributors", accessed: 2026-08-25}
  - {title: "QwenLM/Qwen3.8 README — Finetuning section", url: "https://github.com/QwenLM/Qwen3.8", publisher: "Qwen Team, Alibaba Group", accessed: 2026-08-25}
  - {title: "Qwen documentation — Training frameworks", url: "https://qwen.readthedocs.io/en/latest/", publisher: "Qwen Team", accessed: 2026-08-25}
  - {title: "Qwen/Qwen3-8B config.json", url: "https://huggingface.co/Qwen/Qwen3-8B/raw/main/config.json", publisher: "Qwen / Alibaba Cloud", accessed: 2026-08-25}
related: [alibaba.qwen_local, alibaba.qwen_architecture, alibaba.qwen_agents, alibaba.qwen_models]
---

# Fine-tuning and adapting Qwen — LoRA, QLoRA, DoRA and the memory maths

**Summary.** Fine-tuning is the third thing to try, not the first. Prompting and retrieval solve most problems that people bring to fine-tuning, faster and reversibly. When fine-tuning *is* right — teaching a fixed output format, a house style, a narrow domain vocabulary, or a tool-calling protocol — LoRA on a quantised base is almost always the correct method, and on Apple Silicon `mlx_lm.lora` does it in one command. The defaults that ship with mlx-lm (rank 8, 16 layers, `q_proj` and `v_proj` only, lr 1e-5, 1000 iterations) train roughly 1.7 million parameters on an 8B model — 0.02% of the weights — which is enough for format and style and not enough for new knowledge.

> ⚠️ Versions checked 25 August 2026: `mlx-lm` 0.31.3. `mlx_lm/LORA.md` lists supported families as Mistral, Llama, Phi2, Mixtral, Qwen2, Gemma, OLMo, MiniCPM, InternLM2 — but that list is stale relative to the model files actually present in the package, which include `qwen3`, `qwen3_moe`, `qwen3_next`, `qwen3_5` and `qwen3_5_moe`. Verify with a short run before committing to a long one.

## Key facts

| Item | Value |
|---|---|
| mlx-lm LoRA defaults | rank 8, scale 20.0, dropout 0.0, `num_layers` 16, targets `self_attn.q_proj` + `self_attn.v_proj` |
| Other defaults | `batch_size` 4, `iters` 1000, `learning_rate` 1e-5, `max_seq_length` 2048, optimizer adam, `save_every` 100 |
| Fine-tune types | `lora` (default), `dora`, `full` |
| Optimizers available | adam, adamw, muon, sgd, adafactor |
| Data formats | `chat`, `tools`, `completions`, `text` (JSONL) |
| Trainable params, Qwen3-8B at defaults | ~1,703,936 (0.021% of 8B) |
| Full fine-tune memory rule of thumb | ~16 bytes per parameter with Adam in mixed precision |
| QLoRA memory rule of thumb | base at 4-bit + adapters + activations |

## When fine-tuning is and is not the right answer

### Try these first

**Prompting.** A well-constructed system prompt with three to five worked examples solves format, tone, and most classification tasks. It costs nothing, is versioned in git, and can be changed in seconds. If you have not written a 500-word system prompt with examples and measured it, you are not ready to fine-tune.

**Retrieval (RAG).** If the problem is "the model does not know our facts", the answer is retrieval, not fine-tuning. Fine-tuning is a spectacularly inefficient way to install facts: you need many paraphrases of each fact to make it stick, the model will still hallucinate around the edges, you cannot update a fact without retraining, and you cannot cite a source. Retrieval fixes all four. See `09` for the Qwen3-Embedding stack.

**A bigger model.** Before fine-tuning a 4B, check whether a 27B at 4-bit — the same memory footprint as an 8B at bf16 — simply does the job. This is very often the cheapest answer.

**Constrained decoding.** If the problem is "the output is not valid JSON", use a grammar (`06`). Do not fine-tune to teach syntax a decoder can enforce.

### Fine-tune when

- **Output format must be exact and repeated** — a specific XML dialect, a fixed CSV schema, a domain-specific DSL. Few-shot gets you 95%; fine-tuning gets you 99.5% and lets you drop the examples from every prompt, which pays for itself in latency.
- **Style and register matter** — legal drafting conventions, a particular clinical note format, an organisation's voice.
- **A narrow domain vocabulary or reasoning pattern is underrepresented** — a specialised sublanguage where the base model's priors are actively wrong.
- **You want to shrink the prompt.** A 2,000-token system prompt sent on every request costs real money and latency at scale. Fine-tuning can internalise it.
- **You are distilling a larger model's behaviour** into a small one you can run locally — generate a few thousand examples with a frontier model, train a Qwen3.5-4B on them, and get 80% of the behaviour at 3 GB.
- **Tool-calling reliability on your specific tools** needs to go from 85% to 97%.

### Do not fine-tune when

- The requirement changes weekly.
- You have fewer than ~500 good examples and no way to make more.
- You cannot articulate a metric that would tell you it worked.
- The base model already scores 90%+ on your eval and the remaining failures are diverse.

## Dataset construction

### Format

mlx-lm reads JSONL from a directory containing `train.jsonl`, optionally `valid.jsonl`, and `test.jsonl` for `--test`. Four formats are supported.

**`chat`** — the one to use for Qwen. Multi-turn, and the tokenizer's own chat template is applied, so thinking blocks, system messages and roles are handled correctly:

```json
{"messages": [{"role": "system", "content": "You extract structured data from survey reports."}, {"role": "user", "content": "Borehole BH-14, drilled 12 March 2024, static water level 38.4 m, yield 1.2 L/s."}, {"role": "assistant", "content": "{\"id\":\"BH-14\",\"drilled\":\"2024-03-12\",\"swl_m\":38.4,\"yield_lps\":1.2}"}]}
```

**`tools`** — for training tool-calling. Includes a `tools` array with the function schemas alongside `messages`, so the template renders the `<tools>` block exactly as it will appear at inference.

**`completions`** — prompt/completion pairs:

```json
{"prompt": "Convert to ISO 8601: 3rd of March 2024", "completion": "2024-03-03"}
```

**`text`** — raw continuation, for continued pretraining:

```json
{"text": "SANS 10400-K:2011 requires that ..."}
```

Hugging Face datasets can be used directly with an `hf_dataset` block in the YAML config specifying `path`, `train_split`, `valid_split`, `prompt_feature` and `completion_feature`.

### Quality over quantity — the actual numbers

| Examples | What it buys |
|---|---|
| < 200 | Nothing reliable. Use few-shot prompting instead. |
| 500–1,000 | Format and style adherence. This is the sweet spot for most format-fixing tasks. |
| 2,000–10,000 | Domain behaviour, tool-calling reliability, a genuine capability shift within a narrow scope. |
| 50,000+ | You are doing instruction tuning, not adaptation. Consider whether you should instead be continuing pretraining. |

Rules that matter more than the count:

- **Deduplicate.** Near-duplicates are the fastest route to memorisation and a useless model.
- **Hold out a real test set before you start**, from a different source or time period than the training data. A random split of a homogeneous corpus tells you nothing.
- **Include negatives and refusals.** If the model should say "not present in the document", show it doing so. Otherwise you train a confident fabricator.
- **Match inference exactly.** If production sends a system prompt, put that system prompt in every training example. If production runs with thinking off, train with thinking off.
- **Decide about thinking traces explicitly.** For a Qwen3.5+ target, either (a) train on non-thinking outputs and run with `enable_thinking: false`, or (b) include real `reasoning_content` in your examples. Mixing them produces a model that opens `<think>` and never closes it.
- **Mask the prompt.** Pass `--mask-prompt` so the loss is computed only on the completion (for `chat` datasets, the final message). Training on the prompt teaches the model to generate your inputs, which is not what you want.

## Full fine-tuning versus LoRA — the memory maths

### Full fine-tuning

Per parameter, in mixed-precision training with Adam:

| Item | Bytes/param |
|---|---|
| Weights (bf16) | 2 |
| Gradients (bf16) | 2 |
| Adam first moment `m` (fp32) | 4 |
| Adam second moment `v` (fp32) | 4 |
| fp32 master weights | 4 |
| **Total** | **16** |

Plus activations, which scale with batch size × sequence length × hidden × layers.

| Model | Params | Optimiser state at 16 B/param |
|---|---|---|
| Qwen3.5-0.8B | 0.873 B | 14.0 GB |
| Qwen3.5-2B | 2.274 B | 36.4 GB |
| Qwen3.5-4B | 4.660 B | 74.6 GB |
| Qwen3.5-9B | 9.653 B | 154.4 GB |
| Qwen3.8-27B | 27.781 B | **444.5 GB** |

So on a 64 GB Mac, full fine-tuning is feasible up to roughly 2B parameters and no further, and even that needs `--grad-checkpoint`, `batch_size 1` and a short `max_seq_length`. Using SGD or Adafactor instead of Adam cuts the optimiser state substantially (`--optimizer sgd` removes 8 bytes/param; `adafactor` uses factored second moments) and moves the ceiling up, at some cost in convergence quality.

### LoRA

LoRA freezes the base weights and learns a low-rank update `ΔW = B·A` where `A ∈ ℝ^(r×d_in)` and `B ∈ ℝ^(d_out×r)`. Trainable parameters per targeted linear layer:

```
r × (d_in + d_out)
```

Worked example — **Qwen3-8B** at mlx-lm defaults (`rank: 8`, `keys: ["self_attn.q_proj", "self_attn.v_proj"]`, `num_layers: 16`). From `config.json`: hidden 4,096, 32 attention heads × head_dim 128 = 4,096 for `q_proj` output; 8 KV heads × 128 = 1,024 for `v_proj` output.

```
q_proj:  8 × (4096 + 4096) =  65,536
v_proj:  8 × (4096 + 1024) =  40,960
per layer                  = 106,496
× 16 layers                = 1,703,936 trainable parameters
```

That is **0.021%** of the model. At bf16 the adapters are 3.4 MB; Adam states add 13.6 MB. Total optimiser overhead: about **17 MB**. Compare 128 GB for a full fine-tune of the same model.

The memory that actually matters in LoRA is therefore **the frozen base plus activations**, not the optimiser:

```
LoRA peak ≈ base_weights + activations + (tiny adapter state)
```

- Qwen3.5-9B at bf16 base: ~19 GB + activations → needs 32 GB+
- Qwen3.5-9B at 4-bit base (QLoRA): ~6 GB + activations → runs on 16 GB
- Qwen3.8-27B at 4-bit base (QLoRA): ~16 GB + activations → runs on 32 GB

### QLoRA

QLoRA = LoRA where the frozen base is quantised. In mlx-lm this is automatic: *"If `--model` points to a quantized model, then the training will use QLoRA, otherwise it will use regular LoRA."* Point it at `mlx-community/Qwen3.5-9B-4bit` and you are doing QLoRA.

The trade-off: quantisation noise in the frozen base slightly limits how much the adapter can compensate. For format and style tasks the difference is not measurable. For pushing a model into genuinely new behaviour, a bf16 base is better if you can afford it.

### DoRA

`--fine-tune-type dora` — weight-decomposed low-rank adaptation, which separates magnitude and direction and learns them independently. It typically closes some of the gap between LoRA and full fine-tuning at the same rank, at maybe 10–20% more compute. Worth trying if LoRA underfits and you have already raised the rank.

## Hyperparameters that actually matter

Ranked by how much they move the result:

**1. Which modules you target (`lora_parameters.keys`).** The mlx-lm default of `q_proj` and `v_proj` only is conservative. Adding the MLP projections is the single biggest quality lever:

```yaml
lora_parameters:
  keys: ["self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj", "self_attn.o_proj",
         "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj"]
  rank: 16
  scale: 32.0
  dropout: 0.05
```

This roughly quintuples trainable parameters and usually improves everything. For Qwen3.5-generation hybrids, the linear-attention layers expose different module names — inspect with `model.named_modules()` before assuming.

**2. `num_layers`.** Default 16 means only the last 16 layers get adapters. `-1` applies to all. More layers = more capacity; start at 16, go to `-1` if you underfit.

**3. Rank.** 8 for format and style; 16–32 for domain behaviour; 64+ rarely helps and starts to overfit. `scale` (LoRA alpha) conventionally tracks rank — the default 20.0 with rank 8 is an effective alpha/r of 2.5, which is on the aggressive side; `scale = 2 × rank` is a common convention.

**4. Learning rate.** mlx-lm defaults to 1e-5, which is low for LoRA. For LoRA specifically, 1e-4 to 2e-4 is the usual range; 1e-5 is a full-fine-tune learning rate. If your loss barely moves in 200 iterations, this is why. Use a schedule:

```yaml
lr_schedule:
  name: cosine_decay
  warmup: 100
  warmup_init: 1e-7
  arguments: [2e-4, 1000, 1e-6]
```

**5. Iterations and effective batch size.** `iters × batch_size` should give you 2–4 passes over the dataset. More than that and you memorise. Use `--grad-accumulation-steps` to raise the effective batch without raising memory.

**6. `max_seq_length`.** Default 2048. Set it to just above your longest example — memory scales with it, and padding waste is real.

**7. `--mask-prompt`.** Not a number but a flag that changes what you are optimising. Almost always on.

**8. Dropout.** 0.0 by default. Set 0.05 if you see the validation loss diverge from training loss.

## The tooling

| Tool | Platform | Best for |
|---|---|---|
| **mlx-lm** | Apple Silicon only | LoRA/DoRA/full on a Mac. Simplest path. Officially supported quantised training. |
| **Unsloth** | CUDA (Linux/WSL); desktop app | 2× faster LoRA/QLoRA with custom Triton kernels and much lower memory. Explicit Qwen3.8 support. Alibaba names it as a recommended framework. |
| **LLaMA-Factory** | CUDA | Broadest coverage: SFT, DPO, KTO, ORPO, PPO, pretraining, with a web UI. Named by Alibaba. |
| **MS-SWIFT** | CUDA | ModelScope's framework — Alibaba's own, so Qwen support lands first. Named by Alibaba. |
| **Axolotl** | CUDA | YAML-driven, reproducible, good multi-GPU and DeepSpeed/FSDP integration. Named in Qwen docs. |
| **TRL + PEFT** | CUDA / CPU | The Hugging Face primitives. Use when you need a custom training loop or a non-standard objective. |
| **verl** | CUDA | RL at scale (PPO/GRPO). Named in Qwen docs. |

The Qwen3.8 README's own recommendation: *"We advise you to use training frameworks, including Unsloth, Swift, Llama-Factory, to finetune your models with SFT, DPO, GRPO, etc."*

## Worked example — end to end on Apple Silicon

Task: teach Qwen3.5-4B to extract borehole survey data into a fixed JSON schema, reliably, without a long prompt.

### 1. Prepare data

```bash
mkdir -p ~/qwen-ft/data && cd ~/qwen-ft
```

`data/train.jsonl` (900 lines), `data/valid.jsonl` (100), `data/test.jsonl` (200), each line:

```json
{"messages":[{"role":"system","content":"Extract borehole data as JSON. Fields: id, drilled (ISO 8601), swl_m, yield_lps, aquifer. Use null for missing values. Output JSON only."},{"role":"user","content":"BH-207 was completed on 4 April 2023 in the Kalahari sequence; SWL measured at 51.7 metres, blow yield 0.8 litres per second."},{"role":"assistant","content":"{\"id\":\"BH-207\",\"drilled\":\"2023-04-04\",\"swl_m\":51.7,\"yield_lps\":0.8,\"aquifer\":\"Kalahari\"}"}]}
```

Include roughly 10% examples with missing fields, and roughly 5% where the text contains no borehole data and the correct answer is `{"id":null,...}` or an explicit refusal — otherwise the model invents boreholes.

### 2. Baseline before training

```bash
mlx_lm.generate --model mlx-community/Qwen3.5-4B-MLX-4bit \
  --prompt "$(cat data/one_test_prompt.txt)" \
  --chat-template-args '{"enable_thinking": false}' --max-tokens 256
```

Score your test set. Write the score down. Without it you cannot tell whether the fine-tune helped.

### 3. Config

`lora_config.yaml`:

```yaml
model: "mlx-community/Qwen3.5-4B-MLX-4bit"   # 4-bit base ⇒ QLoRA
train: true
fine_tune_type: lora
optimizer: adamw
data: "./data"
seed: 0
num_layers: -1
batch_size: 4
iters: 900
val_batches: 25
learning_rate: 2e-4
steps_per_report: 10
steps_per_eval: 100
save_every: 100
adapter_path: "./adapters/borehole-v1"
max_seq_length: 1024
grad_checkpoint: true
grad_accumulation_steps: 2
mask_prompt: true
test: true
test_batches: -1

lora_parameters:
  keys: ["self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj", "self_attn.o_proj",
         "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj"]
  rank: 16
  scale: 32.0
  dropout: 0.05

lr_schedule:
  name: cosine_decay
  warmup: 90
  warmup_init: 1e-7
  arguments: [2e-4, 900, 1e-6]
```

### 4. Train

```bash
source ~/qwen3.8-venv/bin/activate
mlx_lm.lora --config lora_config.yaml
```

Watch the reported train and validation loss. Validation should fall and then flatten. If it rises while train loss falls, you are overfitting — reduce `iters` or `rank`, or add data. On an M-series Mac a 4B QLoRA at these settings is a matter of tens of minutes, not hours.

Resume with `--resume-adapter-file ./adapters/borehole-v1/adapters.safetensors`. Log to Weights & Biases with `--report-to wandb --project-name borehole-extract`.

### 5. Evaluate

```bash
# test-set perplexity via the same command
mlx_lm.lora --model mlx-community/Qwen3.5-4B-MLX-4bit \
  --adapter-path ./adapters/borehole-v1 --data ./data --test

# behavioural check
mlx_lm.generate --model mlx-community/Qwen3.5-4B-MLX-4bit \
  --adapter-path ./adapters/borehole-v1 \
  --prompt "$(cat data/one_test_prompt.txt)" \
  --chat-template-args '{"enable_thinking": false}' --max-tokens 256
```

Perplexity is a sanity check, not the metric. The metric is **exact-match JSON validity and per-field accuracy on the held-out test set**, scored by a script. Run it before and after. If the improvement is under 5 points, the fine-tune was not worth it.

Also run a **regression check**: ask the adapted model a handful of general questions unrelated to boreholes. If it now answers "What is the capital of Namibia?" with a JSON object, you have over-fitted the format and need more diverse training data or fewer iterations.

### 6. Fuse and deploy

```bash
mlx_lm.fuse --model mlx-community/Qwen3.5-4B-MLX-4bit \
  --adapter-path ./adapters/borehole-v1 \
  --save-path ./Qwen3.5-4B-borehole

mlx_lm.server --model ./Qwen3.5-4B-borehole --port 8080
```

`mlx_lm.fuse` also supports `--upload-repo` with `--hf-path` for attribution, and `--export-gguf` (limited to Mistral/Mixtral/Llama-style models in fp16, so **not** applicable to Qwen3.5-generation hybrids).

Keeping the adapter unfused is often better: `mlx_lm.generate --adapter-path` and `mlx_lm.server --adapter-path` both load adapters at runtime, so one base model in memory can serve several specialisations by swapping a few megabytes.

## Catastrophic forgetting

Fine-tuning on a narrow distribution degrades everything else. It is not subtle and it is not avoidable, only manageable.

**Detect it.** Keep a fixed "general capability" probe set — 50 questions spanning general knowledge, reasoning, multilingual output, code, and instruction following — and run it before and after every fine-tune. Score it the same way each time.

**Mitigate it:**

- **LoRA over full fine-tuning.** A rank-16 adapter on 0.1% of parameters simply cannot destroy as much as a full update.
- **Fewer epochs.** 2–3 passes, not 10.
- **Lower learning rate.** Halving the LR often preserves general ability at little cost to the target task.
- **Mix in general data.** 10–20% of your training set drawn from a general instruction dataset (e.g. a sample of tulu-3-sft-mixture) is the standard rehearsal technique and works.
- **Fewer target modules.** Attention-only adapters forget less than attention+MLP.
- **Keep the adapter separate.** An unfused adapter can be turned off. A fused model cannot.

## Merging adapters

`mlx_lm.fuse` merges `ΔW = scale/rank × B·A` into the base weights. Points to watch:

- **Fusing into a quantised base** re-quantises, adding a second round of error. For quality, fuse into the bf16 base and then quantise the result — not the other way round.
- **Merging multiple adapters** is not supported directly by mlx-lm. Options: train one adapter on the union of tasks; serve adapters separately and route; or, in PEFT-land, use weighted merging (`add_weighted_adapter` with `linear`, `ties`, or `dare_ties` methods). Naive linear averaging of adapters trained on different tasks usually degrades both.
- **Adapter portability** is limited to the exact base checkpoint and its quantisations. An adapter trained on Qwen3.5-9B will not load on Qwen3.6-9B or on Qwen3-8B.

## Continued pretraining for domain adaptation

When the domain has its own sublanguage — regulatory codes, clinical notes, a proprietary programming language — continued pretraining on raw text can help where instruction tuning cannot.

```bash
# data/train.jsonl: {"text": "..."} per line, from a -Base checkpoint
mlx_lm.lora --model Qwen/Qwen3.5-4B-Base \
  --train --data ./domain_corpus --fine-tune-type lora \
  --num-layers -1 --iters 5000 --learning-rate 5e-5 \
  --max-seq-length 4096 --batch-size 2 --grad-checkpoint
```

Rules:

- **Start from a `-Base` checkpoint**, not an instruct one — you will destroy the instruction tuning otherwise.
- **You need scale.** Under ~100 million tokens, continued pretraining is unlikely to beat retrieval. This is the one adaptation technique where quantity genuinely dominates.
- **Then re-instruction-tune.** Continued pretraining produces a completion model. You must follow with SFT on chat-format data to restore conversational behaviour.
- **Mix in general text** at 10–30% to limit forgetting.
- For a genuinely new vocabulary, tokenizer extension is possible but requires resizing and retraining embeddings — a substantially harder project, and rarely worth it given Qwen's 248,320-token multilingual vocabulary.

## A checklist

1. Can prompting do it? Try a proper system prompt with examples first.
2. Is it a knowledge problem? Use retrieval.
3. Would a bigger model do it? Check.
4. Do you have ≥500 clean, deduplicated examples and a held-out test set from a different source?
5. Have you measured the base model on that test set and written the number down?
6. Start with QLoRA on a 4-bit base, rank 16, all attention + MLP modules, lr 2e-4, cosine schedule, `--mask-prompt`, 2–3 epochs.
7. Measure. Compare against step 5. Run the general-capability probe.
8. If it underfits: raise rank, raise `num_layers` to -1, try DoRA, add data.
9. If it overfits: fewer iterations, lower rank, more diverse data, add dropout.
10. Keep the adapter unfused for as long as possible.

## Sources

- [mlx_lm/LORA.md](https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/LORA.md) — commands, QLoRA behaviour, `--mask-prompt`, data formats, fuse and GGUF export limits, logging
- [mlx_lm/lora.py](https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/lora.py) — `CONFIG_DEFAULTS` (rank 8, scale 20.0, num_layers 16, lr 1e-5, iters 1000, max_seq_length 2048), optimiser choices including muon and adafactor, all CLI flags
- [mlx_lm/examples/lora_config.yaml](https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/examples/lora_config.yaml) — default target keys, `lr_schedule` and `hf_dataset` block syntax
- [mlx-lm README](https://raw.githubusercontent.com/ml-explore/mlx-lm/main/README.md) — installation, `mlx-lm[train]`
- [QwenLM/Qwen3.8 README](https://github.com/QwenLM/Qwen3.8) — recommended fine-tuning frameworks
- [Qwen documentation index](https://qwen.readthedocs.io/en/latest/) — training section listing Axolotl, LLaMA-Factory, MS-SWIFT, Unsloth, verl
- [Qwen/Qwen3-8B config.json](https://huggingface.co/Qwen/Qwen3-8B/raw/main/config.json) — dimensions used in the LoRA parameter-count arithmetic
- Parameter counts for Qwen3.5 sizes from the [Hugging Face model API](https://huggingface.co/api/models?author=Qwen)

## Open questions

- The exact LoRA-targetable module names for Qwen3.5-generation Gated DeltaNet layers were not enumerated; the `keys` list above is the standard transformer set and is `needs-verification` for the linear-attention blocks.
- Whether `mlx_lm.lora` supports the `qwen3_5_moe` architecture for expert-layer adaptation is `needs-verification` — MoE LoRA has framework-specific caveats about whether router weights are trainable.
- The claim that mlx-lm's stale supported-families list is functionally out of date is inferred from the presence of `qwen3_5.py` in `mlx_lm/models/`, not from a successful training run.
- Unsloth's claimed 2× speed and 70% memory reduction for Qwen fine-tuning is a vendor figure and is `needs-verification`.
- Wall-clock training times on specific Apple Silicon chips are `needs-verification` — none were measured.
