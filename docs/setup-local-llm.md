# Local model setup — the TEE-native code model (A34)

TEE's chore layer (traceback triage, script repair drafts, lint
explanation, web-extract refinement, fact structuring, recap
compression, kb rerank) runs against **any OpenAI-compatible local
endpoint**. TEE does not ship or manage model servers; it speaks to
yours. With nothing running, every chore degrades to its deterministic
path and every refusal names this page's fix — a TEE install with no
model is complete, just less assisted.

## Bring your own model (the whole contract)

```toml
# .tee/config.toml
[llm]
url = "http://127.0.0.1:8080/v1"   # any OpenAI-compatible endpoint
model = "your-served-model-name"
refine = "auto"                     # auto | local | off (chore default)
```

Environment variables `TEE_LOCAL_LLM_URL` / `TEE_LOCAL_LLM_MODEL`
override the defaults; `[llm]` config wins where both exist. The client
(`kernel/local_llm.py`) is stdlib-only: chat/completions, temperature 0,
thinking disabled (and any leaked `<think>` block stripped), JSON mode
with one corrective retry. The vision arm (`web_lookup` image captions)
uses the sibling contract in `kernel/local_vlm.py`
(`TEE_LOCAL_VLM_URL/MODEL`).

## Reference setup (what TEE is benchmarked against)

The adoption research (research 50 §M0, 2026-08-28) chose
**Qwen2.5-Coder-14B-Instruct** — Apache-2.0, dense, code-specialist,
non-thinking — served as the mlx-community 4-bit quant on Apple Silicon:

```bash
hf download mlx-community/Qwen2.5-Coder-14B-Instruct-4bit   # ~8.3 GB
mlx_lm.server --model mlx-community/Qwen2.5-Coder-14B-Instruct-4bit --port 8080
```

```toml
[llm]
url = "http://127.0.0.1:8080/v1"
model = "mlx-community/Qwen2.5-Coder-14B-Instruct-4bit"
```

The 7B sibling (~4.3 GB) is the recorded fallback when the latency
ladder matters more than answer strength; it swaps in behind the same
seam with no code change. Any llama.cpp / vLLM / LM Studio endpoint
works identically — the benchmarks in `benchmarks/RESULTS.md` name the
exact model they were measured against, and a different model means
your numbers differ.

## Memory-pressure rules (the §2 lesson, now policy)

- **Lazy-start, idle-unload.** Nothing loads until the first chore asks;
  stop the server when a session ends. TEE probes availability with a
  30 s cache and degrades silently in `refine=auto` — an absent model is
  never an error, only a missing upgrade.
- **Never resident during a generation battery or UE editor session.**
  Model serving, LoRA training, and model benchmarking share this
  machine with DCCs and voxkiln; two memory-hungry workloads at once is
  how profile runs die. Check `ps` for UnrealEditor/voxkiln before
  starting a server; the benchmark harness refuses to be blamed for
  numbers taken on a contended machine.
- Budgets: the 14B-4bit is ~8.3 GB resident; the 9B general reference
  measured 105 tok/s / 5.3 GB (research 50); chore prompts are small,
  so first-token latency dominates — a warm server answers chore-sized
  work in about a second.

## What the chores may and may not do (the A30 boundary)

The model reasons over evidence in-context: tracebacks, source lines,
diffs, schemas, page text. **API facts from weights are banned** — a
fix that depends on an API name or signature not present in the
evidence must answer `confidence: "needs_verification"` and name what
to check. The trap suite (`server/tests/test_llm_traps.py`, `llm`
marker) enforces this against the real model: seeded tracebacks whose
correct fix requires an omitted API must defer; grounded controls must
not. A trap failure blocks adoption outright. Deterministic checkers
(lint, plaus_check, validators) stay the judges everywhere — the model
translates findings, never overrules them.

Every chore answer is schema-validated fail-closed and carries a
provenance stamp (`model: tee-coder@<revision>`, the template revision
in `tee/llm/chores.py`).
