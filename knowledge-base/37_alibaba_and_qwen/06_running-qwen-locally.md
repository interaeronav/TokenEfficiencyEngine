---
id: alibaba.qwen_local
title: Running Qwen locally — Apple Silicon, MLX, quantisation and serving
domain: 37_alibaba_and_qwen
tags: [qwen, mlx, mlx-lm, apple-silicon, quantisation, gguf, llama-cpp, ollama, lm-studio, vllm, sglang, kv-cache, speculative-decoding, chat-template, tool-calling, thinking-mode, openai-compatible]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "ml-explore/mlx-lm README", url: "https://raw.githubusercontent.com/ml-explore/mlx-lm/main/README.md", publisher: "Apple / MLX contributors", accessed: 2026-08-25}
  - {title: "mlx-lm convert.py, generate.py, server.py, lora.py, setup.py", url: "https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/convert.py", publisher: "Apple / MLX contributors", accessed: 2026-08-25}
  - {title: "mlx_lm/LORA.md", url: "https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/LORA.md", publisher: "Apple / MLX contributors", accessed: 2026-08-25}
  - {title: "QwenLM/Qwen3.8 README", url: "https://github.com/QwenLM/Qwen3.8", publisher: "Qwen Team, Alibaba Group", accessed: 2026-08-25}
  - {title: "Qwen/Qwen3.8-27B tokenizer_config.json (chat template)", url: "https://huggingface.co/Qwen/Qwen3.8-27B/raw/main/tokenizer_config.json", publisher: "Qwen / Alibaba Cloud", accessed: 2026-08-25}
  - {title: "unsloth/Qwen3.8-27B-GGUF file listing", url: "https://huggingface.co/api/models/unsloth/Qwen3.8-27B-GGUF?blobs=true", publisher: "Unsloth / Hugging Face", accessed: 2026-08-25}
  - {title: "mlx-community Qwen repositories", url: "https://huggingface.co/models?search=mlx-community%20Qwen3.8", publisher: "MLX Community / Hugging Face", accessed: 2026-08-25}
  - {title: "Unsloth Qwen3.8 running guide", url: "https://unsloth.ai/docs/models/qwen3.8", publisher: "Unsloth", accessed: 2026-08-25}
  - {title: "Qwen docs — MLX LM", url: "https://qwen.readthedocs.io/en/latest/run_locally/mlx-lm.html", publisher: "Qwen Team", accessed: 2026-08-25}
related: [alibaba.qwen_models, alibaba.qwen_architecture, alibaba.qwen_finetune, alibaba.qwen_agents]
---

# Running Qwen locally — Apple Silicon, MLX, quantisation and serving

**Summary.** On Apple Silicon, `mlx-lm` is the fastest and lowest-friction way to run Qwen, and Qwen is unusually well served: `mlx-community` publishes 4-, 5-, 6- and 8-bit affine quantisations plus `mxfp4`, `nvfp4` and `mxfp8` for the current Qwen3.8 and Qwen3.5 generations, and separate MTP draft modules for speculative decoding. The two numbers that decide everything are **weight bytes** (parameters × bits ÷ 8, plus about 10–16% overhead) and **KV cache bytes** (a function of full-attention layers, not total layers — which is why the Qwen3.5-generation hybrid architecture is so friendly to a Mac). This file gives the arithmetic, real measured file sizes, working commands, the exact chat template semantics, and concrete recommendations by RAM tier.

> ⚠️ Versions checked on 25 August 2026: `mlx-lm` 0.31.3 (PyPI), `mlx` 0.32.2. `mlx-lm` supports `qwen3_5` and `qwen3_5_moe` architectures (both model files present in the repository), as well as `qwen3_next`, `qwen3_moe`, `qwen3` and `qwen2`. Flag names below are taken from the current argument parsers; check `-h` if a flag is rejected.

## Key facts — measured sizes

Real repository sizes, retrieved from the Hugging Face API on 25 August 2026. These are what actually lands on disk and (approximately) in RAM.

| Model | Format | Size on disk |
|---|---|---|
| Qwen3.8-27B | MLX bf16 | 54.74 GB |
| Qwen3.8-27B | MLX 8-bit | 29.53 GB |
| Qwen3.8-27B | MLX `mxfp8` | ~8 GB reported params; repo listed as 8B class |
| Qwen3.8-27B | MLX 4-bit (affine) | **16.08 GB** |
| Qwen3.8-27B | MLX `mxfp4` | 15.24 GB |
| Qwen3.8-27B-MTP | MLX 4-bit (draft head) | 0.27 GB |
| Qwen3.5-27B | MLX 4 / 5 / 6 / 8-bit | 16.08 / — / 22.80 / 29.53 GB |
| Qwen3.5-9B | MLX 4-bit | 5.98 GB |
| Qwen3.5-4B | MLX 4-bit | 3.06 GB |
| Qwen3.5-2B | MLX 4-bit | 1.75 GB |
| Qwen3.5-0.8B | MLX 4-bit | 0.65 GB |
| Qwen3.5-35B-A3B | MLX 4-bit | 20.42 GB |
| Qwen3.5-122B-A10B | MLX 4-bit | 69.62 GB |
| Qwen3.8-27B | GGUF Q4_K_M (Unsloth UD) | 16.46 GB |
| Qwen3.8-27B | GGUF Q5_K_M | 19.77 GB |
| Qwen3.8-27B | GGUF Q6_K | 21.98 GB |
| Qwen3.8-27B | GGUF Q8_0 | 29.05 GB |
| Qwen3.8-27B | GGUF UD-IQ2_XXS | 7.27 GB |
| Qwen3.5-9B | GGUF Q4_K_M | 5.68 GB |
| Qwen3.5-9B | GGUF Q8_0 | 9.53 GB |
| Qwen3.8-27B / Qwen3.5-9B | GGUF `mmproj` (vision projector) | 0.93 / 0.92 GB — **separate file, add it** |

## The memory arithmetic — do this, don't guess

### Step 1: weights

```
weight_bytes ≈ parameters × (bits / 8) × overhead
```

`overhead` is 1.05–1.20. It comes from three places: quantisation scales and zero-points (one pair per group; group size 64 for MLX affine, 32 for `mxfp4`/`mxfp8`, 16 for `nvfp4`), norms and biases kept at full precision, and — the big one for Qwen — **embeddings and the output head usually left at BF16**.

Worked example, Qwen3.8-27B at MLX 4-bit:

```
27,781,427,952 × 0.5 bytes = 13.89 GB   naive
measured                    = 16.08 GB   ⇒ overhead factor 1.158
```

Where the extra 2.19 GB goes: the mlx-community repo reports 1,303,792,880 parameters retained in BF16. With vocabulary 248,320 and hidden 5,120, the input embedding is 1.271 billion parameters — at BF16 that is 2.54 GB on its own. So the "overhead" is almost entirely the embedding table, which is 4.6% of the model's parameters but 16% of its 4-bit footprint.

Sanity check at 8-bit: 27.78e9 × 1.0 = 27.78 GB naive, 29.53 GB measured ⇒ factor 1.063. The BF16 embedding is a smaller *relative* premium when the rest is already 8-bit. Both check out.

**Effective bits per weight** is the honest way to compare GGUF quants:

```
bpw = file_bytes × 8 / parameters
```

| Qwen3.8-27B GGUF | Size | bpw |
|---|---|---|
| UD-IQ2_XXS | 7.27 GB | 2.09 |
| UD-Q3_K_XL | 13.15 GB | 3.79 |
| UD-IQ4_XS | 14.25 GB | 4.10 |
| Q4_0 | 16.06 GB | 4.63 |
| **UD-Q4_K_M** | 16.46 GB | **4.74** |
| UD-Q5_K_M | 19.77 GB | 5.69 |
| UD-Q6_K | 21.98 GB | 6.33 |
| Q8_0 | 29.05 GB | 8.37 |

### Step 2: KV cache

For a conventional GQA transformer:

```
kv_bytes_per_token = 2 × n_layers × n_kv_heads × head_dim × bytes_per_element
```

For the Qwen3.5-generation hybrid, **substitute the number of full-attention layers**, because linear-attention layers hold a fixed-size state instead:

```
kv_bytes_per_token = 2 × n_full_attention_layers × n_kv_heads × head_dim × bytes_per_element
```

| Model | Layers used | kv_heads | head_dim | fp16 bytes/token | at 32K | at 262,144 |
|---|---|---|---|---|---|---|
| Qwen3-8B (dense GQA) | 36 | 8 | 128 | 147,456 (144 KiB) | 4.83 GB | — |
| Qwen3-30B-A3B | 48 | 4 | 128 | 98,304 (96 KiB) | 3.22 GB | — |
| Qwen3-32B | 64 | 8 | 128 | 262,144 (256 KiB) | 8.59 GB | — |
| **Qwen3.8-27B / Qwen3.5-27B** | **16** of 64 | 4 | 256 | **65,536 (64 KiB)** | 2.15 GB | **17.2 GB (16 GiB)** |
| Qwen3.5-4B | 8 of 32 | 4 | 256 | 32,768 (32 KiB) | 1.07 GB | 8.6 GB |
| Qwen3.8-2.4T-A95B | 23 of 92 | 4 | 256 | 94,208 (92 KiB) | 3.09 GB | 24.7 GB |

A hypothetical all-full-attention Qwen3.8-27B would need 64 layers × the same per-layer cost = **68.7 GB** at full context. The hybrid gets it to 17.2 GB. That is the single most consequential architectural fact for local users.

Add roughly **150 MB** of constant Gated DeltaNet recurrent state (48 linear layers × 48 value heads × 128 × 128 × 4 bytes fp32) — negligible, and it does not grow.

**Quantised KV cache.** `mlx-lm` supports `--kv-bits 8` or `--kv-bits 4` with `--kv-group-size` (default 64) and `--quantized-kv-start` (start quantising only after N tokens, so short prompts stay exact). 8-bit halves the table above; 4-bit quarters it. Quality cost is small at 8-bit, noticeable at 4-bit for retrieval-heavy long-context work.

### Step 3: everything else

- **Activations and prefill workspace:** roughly 1–3 GB depending on `--prefill-step-size` (default 2048; lower it to reduce peak).
- **macOS itself:** budget 6–10 GB. On a 16 GB machine, more.
- **The wired-memory limit.** MLX wires the memory holding the model, and macOS caps that. If you see `[WARNING] Generating with a model that requires ...`, raise it:

```bash
sudo sysctl iogpu.wired_limit_mb=57344   # 56 GB on a 64 GB machine
```

Set N larger than the model in megabytes but smaller than physical RAM. Requires macOS 15.0 or higher. This single setting is the most common cause of "my 4-bit model is inexplicably slow."

### The complete budget, worked

Qwen3.8-27B, MLX 4-bit, 32,768-token working context, on a 32 GB Mac:

```
weights                16.08 GB
KV cache (fp16, 32K)    2.15 GB
DeltaNet state          0.15 GB
activations/workspace   ~1.5 GB
                       --------
total                  ~19.9 GB
macOS + apps            ~8 GB
                       --------
                       ~28 GB of 32 GB   → fits, with little headroom
```

Same model at 131,072 context: KV becomes 8.6 GB, total ~26.4 GB + OS → tight. Add `--kv-bits 8` and it drops to 22.1 GB → comfortable.

## Quantisation formats compared

### MLX affine (the default)

`mlx_lm.convert -q` produces affine (asymmetric integer) quantisation. Defaults by mode, from `mlx_lm/utils.py`:

| `--q-mode` | Default group size | Default bits |
|---|---|---|
| `affine` | 64 | 4 |
| `mxfp4` | 32 | 4 |
| `nvfp4` | 16 | 4 |
| `mxfp8` | 32 | 8 |

- **4-bit affine, group 64** — the default and the right first choice. Quality loss on Qwen is small; on a 27B it is hard to detect in ordinary use.
- **6-bit** — the sweet spot if you have the RAM. Qwen3.5-27B 6-bit is 22.80 GB vs 16.08 GB at 4-bit. Essentially indistinguishable from 8-bit in practice.
- **8-bit** — near-lossless. Use when RAM is not the constraint and you are evaluating quality.
- **`mxfp4` / `nvfp4` / `mxfp8`** — microscaling float formats (OCP MX and Nvidia FP4). On Apple Silicon they are supported for storage and compute in MLX but the hardware advantage is smaller than on Blackwell GPUs. `mxfp4` at 15.24 GB is marginally smaller than affine 4-bit at 16.08 GB with comparable quality; worth benchmarking on your own prompts, not worth agonising over.
- **Mixed-bit recipes** — `--quant-predicate mixed_2_6 | mixed_3_4 | mixed_3_6 | mixed_4_6`. These mimic llama.cpp's `Q4_K_M` strategy: spend high bits on `v_proj`, `down_proj` and `lm_head` in the first eighth and last eighth of layers plus every third layer in between, low bits elsewhere. `mixed_3_6` is a good aggressive option when 4-bit does not fit.
- **AWQ / DWQ / GPTQ in mlx-lm** — `mlx_lm.awq`, `mlx_lm.dwq`, `mlx_lm.gptq`, `mlx_lm.dynamic_quant` are shipped CLI tools. **DWQ (distilled weight quantisation)** is the interesting one: it trains the quantised student to match the full-precision teacher's outputs on a calibration set, recovering much of the 4-bit loss for a few minutes of local compute. The `mlx-community` repos tagged `OptiQ`, `oQ4` and `oQ6` are community optimised quantisations in this family.

### GGUF (llama.cpp / Ollama / LM Studio)

The `Q<n>_K_<S|M|L>` family are k-quants with per-block scales; `IQ<n>` are importance-matrix quants that use a calibration pass to allocate precision. Unsloth's `UD-` prefix denotes their "Dynamic" recipe, which selectively keeps sensitive tensors at higher precision.

Practical ordering for a 27B, from the measured table above:

- **Q4_K_M (16.46 GB)** — the standard recommendation. Good quality/size.
- **Q5_K_M (19.77 GB)** — better, if you have the room.
- **Q6_K (21.98 GB)** — very close to Q8 quality at 75% of the size.
- **Q8_0 (29.05 GB)** — reference quality.
- **IQ3_XXS / IQ2_* (7–11 GB)** — real quality degradation, but they *run*. For a 27B squeezed onto a 16 GB machine this is the trade you make. Instruction-following and formatting degrade before world knowledge does.
- **BF16 (54.7 GB)** — only for conversion or evaluation baselines.

> ⚠️ For a **multimodal** Qwen (Qwen3.5/3.6/3.8 are all vision-capable), the GGUF weights file is not enough. You must also download the **`mmproj`** file (0.92–0.93 GB) and pass it to llama.cpp with `--mmproj`, or images will be silently ignored.

### AWQ, GPTQ, FP8

- **AWQ (Activation-aware Weight Quantization)** — protects the weight channels with the largest activation magnitudes. Excellent for GPU serving via vLLM; on Apple Silicon, MLX-native quants are faster.
- **GPTQ** — layer-wise second-order error compensation. Qwen publishes `-GPTQ-Int4` and `-GPTQ-Int8` checkpoints for many models.
- **FP8** — Qwen publishes `-FP8` checkpoints (E4M3 weights with per-tensor or per-block scales) for essentially every recent release. These need Hopper-class or newer Nvidia hardware to get the speed benefit; on a Mac they are not the right choice.

### Choosing, in one line each

- **On a Mac, running text or vision chat:** MLX 4-bit, or 6-bit if it fits.
- **On a Mac, needing GGUF tooling or Ollama integration:** Q4_K_M, or UD-Q4_K_XL from Unsloth.
- **On an Nvidia server:** FP8 for Hopper+, AWQ-Int4 otherwise, via vLLM or SGLang.
- **Squeezing a too-large model in:** `mixed_3_6` (MLX) or UD-IQ3_XXS (GGUF), and accept the degradation.

## MLX and mlx-lm — the working commands

### Install

```bash
python3 -m venv ~/qwen3.8-venv && source ~/qwen3.8-venv/bin/activate
pip install -U mlx-lm
# for fine-tuning:
pip install -U "mlx-lm[train]"
# vision models:
pip install -U mlx-vlm
```

`conda install -c conda-forge mlx-lm` also works. macOS only, Apple Silicon only.

### Generate

```bash
mlx_lm.generate \
  --model mlx-community/Qwen3.8-27B-4bit \
  --prompt "Explain grouped-query attention in three sentences." \
  --max-tokens 512 \
  --temp 1.0 --top-p 0.95 --top-k 20 --min-p 0.0
```

Read the prompt from stdin with `--prompt -`. Key flags actually present in `mlx_lm/generate.py`:

| Flag | Purpose |
|---|---|
| `--max-kv-size N` | Rotating fixed-size KV cache — bounds memory, loses the oldest tokens |
| `--prefill-step-size N` | Prompt tokens processed per step (default 2048); lower = lower peak memory |
| `--kv-bits {4,8}` | Quantise the KV cache |
| `--kv-group-size N` | Group size for KV quantisation (default 64) |
| `--quantized-kv-start N` | Only quantise after N tokens |
| `--prompt-cache-file F` | Reuse a precomputed prompt cache |
| `--draft-model REPO` | Speculative decoding draft model |
| `--num-draft-tokens N` | Tokens drafted per step (default 3) |
| `--chat-template-args JSON` | **Pass `enable_thinking`, `reasoning_effort`, `preserve_thinking`** |
| `--system-prompt TEXT` | System message |
| `--extra-eos-token TOK` | Additional stop tokens |
| `--ignore-chat-template` | Raw completion mode |
| `--adapter-path DIR` | Load a LoRA adapter |
| `--trust-remote-code` | Needed for original Qwen 1 tokenizers |

Thinking control:

```bash
# fast, minimal reasoning
mlx_lm.generate --model mlx-community/Qwen3.8-27B-4bit \
  --prompt "List three uses for a hash map." \
  --chat-template-args '{"reasoning_effort": "low"}'

# no thinking block at all
mlx_lm.generate --model mlx-community/Qwen3.8-27B-4bit \
  --prompt "Translate to French: the cat sat on the mat." \
  --chat-template-args '{"enable_thinking": false}'
```

### Chat REPL

```bash
mlx_lm.chat --model mlx-community/Qwen3.5-9B-4bit
```

### Convert and quantise

```bash
# straightforward 4-bit
mlx_lm.convert --model Qwen/Qwen3.5-9B --mlx-path ./Qwen3.5-9B-4bit -q

# 6-bit, group size 32
mlx_lm.convert --model Qwen/Qwen3.5-9B --mlx-path ./Qwen3.5-9B-6bit \
  -q --q-bits 6 --q-group-size 32

# microscaling FP4
mlx_lm.convert --model Qwen/Qwen3.5-9B --mlx-path ./Qwen3.5-9B-mxfp4 \
  -q --q-mode mxfp4

# mixed-precision recipe
mlx_lm.convert --model Qwen/Qwen3.5-27B --mlx-path ./Qwen3.5-27B-m36 \
  -q --quant-predicate mixed_3_6 --q-group-size 64

# upload
mlx_lm.convert --model Qwen/Qwen3.5-9B -q --upload-repo yourname/Qwen3.5-9B-4bit-mlx

# reverse a quantisation
mlx_lm.convert --model ./Qwen3.5-9B-4bit --mlx-path ./Qwen3.5-9B-bf16 -d
```

`--mlx-path` must not already exist. Quality-recovering quantisation:

```bash
# AWQ
mlx_lm.awq -m Qwen/Qwen3.5-9B --mlx-path ./Qwen3.5-9B-awq4 \
  --bits 4 --group-size 64 --num-samples 128 --sequence-length 512

# DWQ — distil the quantised student against the bf16 teacher
mlx_lm.dwq --model Qwen/Qwen3.5-9B --quantized-model ./Qwen3.5-9B-4bit \
  --mlx-path ./Qwen3.5-9B-dwq4 --bits 4 --group-size 64 \
  --num-samples 2048 --batch-size 4 --learning-rate 1e-6
```

DWQ defaults to `allenai/tulu-3-sft-mixture` for calibration; use `--data-path` for something domain-relevant. Add `--grad-checkpoint` if you run out of memory.

### Serve an OpenAI-compatible endpoint

```bash
mlx_lm.server \
  --model mlx-community/Qwen3.8-27B-4bit \
  --host 127.0.0.1 --port 8080 \
  --temp 1.0 --top-p 0.95 --top-k 20 \
  --max-tokens 4096 \
  --prefill-step-size 1024 \
  --chat-template-args '{"reasoning_effort":"medium"}'
```

Then:

```bash
curl http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "mlx-community/Qwen3.8-27B-4bit",
    "messages": [{"role":"user","content":"Say hello in Afrikaans."}],
    "temperature": 1.0, "top_p": 0.95, "max_tokens": 256
  }'
```

Server-specific flags worth knowing: `--decode-concurrency` and `--prompt-concurrency` (batched serving), `--prompt-cache-size` / `--prompt-cache-bytes` (cross-request prefix caching — a large win for agent loops that resend a long system prompt), `--draft-model` / `--num-draft-tokens`, `--adapter-path`, `--chat-template` / `--use-default-chat-template`, `--allowed-origins`, `--pipeline` (distributed across machines with `mx.distributed`).

Point any OpenAI-compatible client at `http://127.0.0.1:8080/v1` with a dummy API key.

### Prompt caching for long fixed contexts

```bash
cat contract.txt | mlx_lm.cache_prompt \
  --model mlx-community/Qwen3.8-27B-4bit \
  --prompt - --prompt-cache-file contract.safetensors

mlx_lm.generate --prompt-cache-file contract.safetensors \
  --prompt "\nList every payment obligation with its clause number."
```

The model is read from the cache file, so `--model` is not needed on the second call. For a 100,000-token document this turns a 60-second prefill into an instant one on every subsequent question.

### Speculative decoding with the MTP head

Qwen3.5-generation models ship a multi-token-prediction head as a separate small repo. Use it as a draft model:

```bash
mlx_lm.generate \
  --model mlx-community/Qwen3.8-27B-4bit \
  --draft-model mlx-community/Qwen3.8-27B-MTP-4bit \
  --num-draft-tokens 3 \
  --prompt "Write a Python function to parse ISO 8601 durations."
```

The draft is 0.27 GB, so it is nearly free in memory. Speculative decoding is **output-identical** to greedy decoding from the target model (the target verifies every drafted token), so there is no quality risk — only a throughput change, positive when acceptance rates are high (structured/code output) and slightly negative when they are low.

You can also use a smaller model from the same family as a draft, e.g. `mlx-community/Qwen3.5-0.8B-4bit` drafting for `Qwen3.5-27B-4bit` — but only if the tokenizers match exactly. Qwen3.5+ and Qwen3 have *different* vocabularies (248,320 vs 151,936), so you cannot mix generations.

### Benchmark, evaluate, manage

```bash
mlx_lm.benchmark --model mlx-community/Qwen3.8-27B-4bit
mlx_lm.perplexity --model mlx-community/Qwen3.5-9B-4bit --data ./eval.jsonl
mlx_lm.evaluate --model mlx-community/Qwen3.5-9B-4bit --tasks arc_easy
mlx_lm.manage --scan        # list cached models
mlx_lm.manage --delete ...  # reclaim disk
```

### Python API

```python
from mlx_lm import load, generate, stream_generate

model, tokenizer = load("mlx-community/Qwen3.8-27B-4bit")

messages = [
    {"role": "system", "content": "You are a terse technical assistant."},
    {"role": "user", "content": "What is a KV cache?"},
]
prompt = tokenizer.apply_chat_template(
    messages,
    add_generation_prompt=True,
    enable_thinking=False,          # skip the <think> block
)

for chunk in stream_generate(model, tokenizer, prompt, max_tokens=512):
    print(chunk.text, end="", flush=True)
```

`generate` and `stream_generate` accept `sampler` and `logits_processors`; helpers live in `mlx_lm.sample_utils`.

## Other runtimes

### llama.cpp

```bash
# text
./llama-cli -m Qwen3.8-27B-UD-Q4_K_M.gguf \
  -c 32768 -ngl 99 \
  --temp 1.0 --top-p 0.95 --top-k 20 --min-p 0.0

# vision — you MUST pass the projector
./llama-mtmd-cli -m Qwen3.8-27B-UD-Q4_K_M.gguf \
  --mmproj mmproj-F16.gguf --image photo.jpg -p "Describe this."

# OpenAI-compatible server
./llama-server -m Qwen3.8-27B-UD-Q4_K_M.gguf \
  -c 65536 -ngl 99 --host 127.0.0.1 --port 8080 \
  --jinja --chat-template-kwargs '{"reasoning_effort":"medium"}'
```

`--jinja` is required for Qwen's chat template to be applied correctly; without it llama.cpp falls back to a built-in template and thinking/tool-call handling breaks. `-ngl 99` offloads all layers to Metal.

On Apple Silicon, llama.cpp with Metal is respectable but MLX is generally faster for the same quantisation because MLX is written for the unified-memory model rather than adapted to it. Use llama.cpp when you need GGUF-only tooling, grammar-constrained sampling (`--grammar`), or cross-platform parity.

### Ollama

```bash
ollama pull qwen3.5:9b
ollama run qwen3.5:27b
ollama pull qwen3.5:35b     # the MoE
```

The official `qwen3.5` library entry offers 0.8b, 2b, 4b, 9b, 27b, 35b and 122b across 64 tags. As of 25 August 2026 there was **no `qwen3.8` entry in the Ollama library** — Ollama lags the release cycle by weeks. Older entries: `qwen3` (58 variants, 0.6b–235b).

Ollama is llama.cpp underneath with model management, an OpenAI-compatible API on `http://localhost:11434/v1`, and sane defaults. Its costs are opacity about which quantisation you actually got (`:latest` is Q4_K_M by convention) and default context windows that are often much shorter than the model supports — set `num_ctx` in a Modelfile or per-request or you will silently truncate.

### LM Studio

A GUI over both llama.cpp and MLX. On Apple Silicon it will offer MLX builds of Qwen directly and exposes an OpenAI-compatible server on `http://localhost:1234/v1`. It is the right recommendation for someone who does not want a terminal, and its model browser surfaces the `mlx-community` quants. The command-line tool `lms` can load, unload and serve models for scripting.

### vLLM and SGLang (server deployment, Nvidia)

From the official Qwen3.8 README:

```bash
vllm serve Qwen/Qwen3.8-27B --port 8000 \
  --tensor-parallel-size 4 --max-model-len 262144 \
  --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_coder

sglang serve --model-path Qwen/Qwen3.8-27B --port 8000 \
  --tp-size 4 --context-length 262144 \
  --reasoning-parser qwen3 --tool-call-parser qwen3_coder
```

Note `--tool-call-parser qwen3_coder`, not a JSON parser — Qwen3.8's tool-call format is XML-ish (see below). `--reasoning-parser qwen3` separates `<think>` content into a `reasoning_content` field in the response.

Neither vLLM nor SGLang runs on Apple Silicon in any useful configuration; they are for Linux/CUDA.

### Hugging Face transformers

```bash
transformers serve Qwen/Qwen3.8-27B --port 8000 --continuous-batching
```

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
tok = AutoTokenizer.from_pretrained("Qwen/Qwen3.5-9B")
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3.5-9B", dtype="auto", device_map="auto")
text = tok.apply_chat_template([{"role":"user","content":"Hello"}],
                               tokenize=False, add_generation_prompt=True)
out = model.generate(**tok([text], return_tensors="pt").to(model.device), max_new_tokens=512)
```

`transformers` on MPS works but is slow and memory-hungry compared to MLX. Use it for correctness reference, not production.

## The Qwen chat template, precisely

Verified from `Qwen/Qwen3.8-27B/tokenizer_config.json` on 25 August 2026.

**Base format** is ChatML:

```
<|im_start|>system
{system content}<|im_end|>
<|im_start|>user
{user content}<|im_end|>
<|im_start|>assistant
<think>
{reasoning}
</think>

{answer}<|im_end|>
```

**Generation prompt.** `add_generation_prompt=True` emits `<|im_start|>assistant\n` followed by:
- `<think>\n` when thinking is enabled (the model is started *inside* the block), or
- `<think>\n\n</think>\n\n` when `enable_thinking=False` (an empty closed block, so the model answers directly).

**`reasoning_effort`** accepts `xhigh` (default), `medium`, `low`. Anything else raises a template exception. It works by prepending a sentence to the system message; `medium` prepends nothing.

**`preserve_thinking`** (default true) controls whether `reasoning_content` from previous assistant turns is replayed. Set false and thinking is stripped from all turns before the last user query — useful for keeping long agent loops inside the context window.

**Tool calling — this changed and it will break your parser.** Qwen3.8 does **not** emit JSON in `<tool_call>`. The template instructs:

```
<tool_call>
<function=example_function_name>
<parameter=example_parameter_1>
value_1
</parameter>
<parameter=example_parameter_2>
This is the value for the second parameter
that can span
multiple lines
</parameter>
</function>
</tool_call>
```

with the reminders that the `<function=...>` block must nest inside `<tool_call>`, required parameters must be given, optional natural-language reasoning may appear *before* but not after the call. Non-string argument values are serialised as JSON inside the `<parameter>` block; strings are emitted raw. Tool definitions go inside `<tools>...</tools>` in a system message, one JSON object per line.

**Qwen3 and earlier** used the JSON form:

```
<tool_call>
{"name": <function-name>, "arguments": <args-json-object>}
</tool_call>
```

So a tool-call parser written for Qwen3 silently fails on Qwen3.8. Use `--tool-call-parser qwen3_coder` in vLLM/SGLang, or let the OpenAI-compatible server layer do the parsing.

**Tool results** are wrapped as `<tool_response>...</tool_response>` inside a **user** message (consecutive tool results are merged into a single user turn). Qwen has no `tool` role on the wire.

**System message position** is enforced — it must be first or the template raises. Images and videos cannot appear in a system message.

**Vision tokens:** `<|vision_start|><|image_pad|><|vision_end|>` for images, `<|vision_start|><|video_pad|><|vision_end|>` for video. With `add_vision_id=True` each is prefixed `Picture N: ` or `Video N: `.

## Sampling parameters — use the published ones

Wrong sampling is the most common cause of "this model is bad". Qwen publishes per-mode recommendations:

| Model / mode | temp | top_p | top_k | min_p | presence_penalty |
|---|---|---|---|---|---|
| Qwen3.8-2.4T-A95B (thinking always on) | 1.0 | 0.95 | 20 | 0.0 | 0.0 |
| Qwen3.8-27B, thinking | 1.0 | 0.95 | 20 | 0.0 | 0.0 |
| Qwen3.8-27B, instruct/non-thinking | 0.7 | 0.80 | 20 | 0.0 | 1.5 |
| Qwen3.5-4B, thinking | 1.0 | 0.95 | 20 | 0.0 | 1.5 |
| Qwen3.5-4B, instruct | 0.7 | 0.80 | 20 | 0.0 | 1.5 |

`repetition_penalty` should stay at 1.0 — Qwen models are sensitive to it and it interacts badly with thinking blocks.

Suggested output budgets: 32,768 tokens for typical queries, 81,920 for hard mathematics or programming when thinking is on. Cutting `max_tokens` too low truncates the model mid-`<think>` and you get no answer at all — the single most common "it returned nothing" bug.

## Structured output

Three approaches, in order of reliability:

1. **Grammar-constrained decoding.** llama.cpp `--grammar-file schema.gbnf` or `--json-schema`; vLLM/SGLang guided decoding with `response_format: {"type":"json_schema", ...}`. This makes malformed output impossible. `mlx-lm` does not ship a grammar engine, but `logits_processors` in the Python API can implement one, and the `outlines` library has MLX support.
2. **Prompt + validate + retry.** Ask for JSON, parse, and on failure re-prompt with the parser error. Cheap and works well with Qwen, which is a strong JSON generator.
3. **Tool calling as a schema mechanism.** Define a single function whose parameters are your schema and let the tool-call machinery enforce shape. With Qwen3.8's XML format this is more robust than free-form JSON because the delimiters are unambiguous.

Whichever you use: **turn thinking off or set `reasoning_effort: low` for structured extraction.** A `<think>` block before a JSON object breaks naive parsers and wastes tokens.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `[WARNING] Generating with a model that requires…` and 2 tok/s | Model exceeds the wired-memory limit | `sudo sysctl iogpu.wired_limit_mb=N` |
| Output is empty or ends mid-sentence | Truncated inside `<think>` | Raise `--max-tokens` to ≥16384, or set `reasoning_effort: low` / `enable_thinking: false` |
| `<think>` text appears in your JSON | Thinking on for a structured task | `--chat-template-args '{"enable_thinking": false}'` |
| Tool calls never parse | Qwen3.8 XML format vs JSON parser | Use `qwen3_coder` parser; update your extractor |
| Repetitive loops | `repetition_penalty` ≠ 1.0, or temp too low with thinking | Restore published sampling params |
| Model ignores images | Missing `mmproj` (GGUF) or text-only runtime | Download and pass `--mmproj`; use `mlx-vlm` not `mlx-lm` |
| `Unexpected reasoning effort` exception | Passed `high` instead of `xhigh` | Only `xhigh`, `medium`, `low` are valid |
| OOM on a long prompt | Prefill peak, not steady state | Lower `--prefill-step-size` to 512 or 256 |
| Context silently truncated in Ollama | Default `num_ctx` | Set `num_ctx` in a Modelfile or the request |
| `trust_remote_code` prompt | Original Qwen 1 tokenizer | `--trust-remote-code`, or use a Qwen1.5+ model |
| Draft model rejected | Tokenizer mismatch | Draft must be same generation (Qwen3.5+ vocab 248,320) |
| Machine swaps and freezes | Total exceeds physical RAM | Recompute the budget; drop a quantisation level or shorten context |

## Recommended setups by RAM tier

All figures are weights + KV at the stated context, before macOS overhead.

### 16 GB
- **Primary: `mlx-community/Qwen3.5-4B-MLX-4bit`** — 3.06 GB, vision-capable, 32K context costs 1.07 GB. Total under 5 GB, leaves the machine usable.
- **Stretch: `mlx-community/Qwen3.5-9B-4bit`** — 5.98 GB + 1.9 GB at 64K. Workable if you close everything else.
- Avoid 27B on 16 GB. An IQ2 GGUF will load but the quality is not worth it.

### 24 GB
- **Primary: `mlx-community/Qwen3.5-9B-4bit`** (5.98 GB) or **6-bit** if published — comfortable at 128K context with `--kv-bits 8`.
- **Also: `mlx-community/Qwen3.5-35B-A3B-4bit`** at 20.42 GB — an MoE with only 3B active, so it is *fast*, but it leaves almost no headroom. Use a 32K context.

### 32 GB
- **Primary: `mlx-community/Qwen3.8-27B-4bit`** — 16.08 GB + 2.15 GB at 32K. The best quality that fits comfortably.
- Add `--draft-model mlx-community/Qwen3.8-27B-MTP-4bit` (0.27 GB) for throughput.
- For 128K context add `--kv-bits 8`.
- **Alternative: `Qwen3.5-35B-A3B-4bit`** (20.42 GB) when you want speed over depth.

### 48 GB
- **Primary: `mlx-community/Qwen3.8-27B-4bit`** at full 262,144 context — 16.08 + 17.2 = 33.3 GB. Fits.
- Or **`Qwen3.5-27B-6bit`** (22.80 GB) at 64K for better quality on shorter work.

### 64 GB
- **Primary: `mlx-community/Qwen3.8-27B-8bit`** (29.53 GB) at 64K (4.3 GB KV) — near-lossless 27B.
- **Or `Qwen3.8-27B-4bit` at full 262K context** (33.3 GB) with room for a second model loaded.
- Raise the wired limit: `sudo sysctl iogpu.wired_limit_mb=57344`.

### 128 GB and above
- **`mlx-community/Qwen3.5-122B-A10B-4bit`** — 69.62 GB, only 10B active per token, so it runs at a speed a 122B dense model never could. This is the flagship-quality option for a single Mac.
- **`Qwen3.8-27B-bf16`** (54.74 GB) as a quality reference for evaluating your own quantisations.
- Qwen3.8-2.4T-A95B is **not** feasible: 4-bit would be roughly 1.2 TB. Unsloth's smallest UD-Q1_0 is 397 GB. That model is a datacentre artefact.

### A general rule

> Prefer a **larger model at 4-bit** to a smaller model at 8-bit, until you get to about 4B parameters, below which quantisation damage becomes disproportionate. A 27B at 4-bit beats a 9B at 8-bit on nearly everything, at roughly three times the memory.

## Sources

- [mlx-lm README](https://raw.githubusercontent.com/ml-explore/mlx-lm/main/README.md) — installation, generate/convert/chat/server, long-prompt tooling, wired-memory `sysctl`, `trust_remote_code`
- mlx-lm source, read 25 August 2026: [`convert.py`](https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/convert.py) (quant modes, mixed recipes), [`generate.py`](https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/generate.py) (all CLI flags), [`server.py`](https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/server.py), [`utils.py`](https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/utils.py) (per-mode quant defaults), [`setup.py`](https://raw.githubusercontent.com/ml-explore/mlx-lm/main/setup.py) (entry points), [`quant/awq.py`](https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/quant/awq.py), [`quant/dwq.py`](https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/quant/dwq.py)
- [QwenLM/Qwen3.8 README](https://github.com/QwenLM/Qwen3.8) — vLLM, SGLang, TokenSpeed, transformers serve, llama.cpp and MLX guidance
- [Qwen/Qwen3.8-27B tokenizer_config.json](https://huggingface.co/Qwen/Qwen3.8-27B/raw/main/tokenizer_config.json) — full chat template
- [Qwen/Qwen3.8-27B config.json](https://huggingface.co/Qwen/Qwen3.8-27B/raw/main/config.json) — layer types, KV heads, head dim
- [unsloth/Qwen3.8-27B-GGUF](https://huggingface.co/api/models/unsloth/Qwen3.8-27B-GGUF?blobs=true) and [unsloth/Qwen3.5-9B-GGUF](https://huggingface.co/api/models/unsloth/Qwen3.5-9B-GGUF?blobs=true) — measured GGUF file sizes
- [mlx-community Qwen3.8 repositories](https://huggingface.co/models?search=mlx-community%20Qwen3.8) and [Qwen3.5](https://huggingface.co/models?search=mlx-community%20Qwen3.5); sizes via the HF API `?blobs=true`
- [Unsloth Qwen3.8 guide](https://unsloth.ai/docs/models/qwen3.8) — sampling settings, quant recommendations
- [Qwen docs — MLX LM](https://qwen.readthedocs.io/en/latest/run_locally/mlx-lm.html) and [Ollama qwen3 library](https://ollama.com/library/qwen3), [Ollama qwen3.5 search](https://ollama.com/search?q=qwen3.5)

## Open questions

- Measured tokens-per-second on specific Apple Silicon chips (M3 Max, M4 Pro, M4 Max, M5) for Qwen3.8-27B at 4-bit are `needs-verification` — no benchmark was run and no first-party table was located. Expect roughly 15–35 tok/s decode on an M4 Max at 4-bit for a 27B, memory-bandwidth-bound, but verify locally with `mlx_lm.benchmark`.
- MTP-head acceptance rates, and therefore the real speedup from `--draft-model`, are workload-dependent and unmeasured here.
- Whether `mlx-vlm` fully supports the Qwen3.5/3.8 early-fusion vision path is `needs-verification`; the Qwen README states mlx-vlm supports "the Qwen3.5 open model series (vision + text)".
- The exact MLX `mxfp8` repo size for Qwen3.8-27B was reported ambiguously by the HF listing and is `needs-verification`.
- Ollama's Qwen3.8 availability and its default context settings per tag are `needs-verification` and change frequently.
