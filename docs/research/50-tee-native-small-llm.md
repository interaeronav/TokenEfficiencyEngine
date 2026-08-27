# 50 — A TEE-native small LLM: custom, optimized, zippy, motivated, lite (2026-08-28)

Verification basis: live measurements run this session on the M5 Max
(generation-speed row below executed 2026-08-28); tool/model inventory
by direct filesystem read; source reads of `kernel/local_vlm.py` and
the owner's `claude-qwen` launcher. Naming note to prevent confusion:
**LiteLLM** in this repo's infra is routing software (the :4000 shim);
the subject of this doc is a lightweight *language model* — a different
thing that would sit behind that shim.

## The question (owner ask, 2026-08-28)

How can TEE build and integrate its own custom, optimized, zippy,
motivated and lite LLM?

## The honesty ladder — what "build our own" can mean

1. **Pretraining from scratch: rejected.** Training even a small
   competitive base model is a cluster-scale undertaking (GPU-years,
   millions of dollars, months) and reproduces what Apache-licensed
   bases already give away. Not the mission; judged by
   tokens-per-completed-task it is all cost, no saving.
2. **Take an open base + make it TEE's own: the real path.** "Custom"
   is earned in two layers — a behavior layer (system prompts, task
   templates, output contracts: days of work), then optionally a
   **LoRA fine-tune** performed on this machine (small adapter file
   trained on TEE-task examples distilled from the big local models).
   The adapter — tens of MB — becomes TEE's IP; the base stays
   upstream and Apache-2.0.
3. Hosted fine-tunes / API models: rejected for this purpose — the
   whole point is zero marginal cost and local sovereignty (A32's
   custom-infrastructure story, research 49).

## Measured and inventoried (this session)

- **Speed (live)**: `mlx_lm.generate` on `Qwen3.5-9B-MLX-4bit`:
  **105.4 tok/s generation, 351.3 tok/s prompt processing, 5.3 GB peak
  memory**. A 500-token budgeted answer costs ~5 s; a recap line ~1 s.
  Caveat noted live: this is a thinking-mode model — chore jobs must
  run with thinking disabled or latency balloons.
- **Trainer present**: `mlx_lm.lora` is installed (uv tool `mlx-lm`)
  — LoRA/QLoRA fine-tuning runs natively on Apple Silicon; a 9B-4bit
  base with a few thousand short examples is an overnight job on this
  128 GB machine, not a cluster job.
- **Teacher models present**: DeepSeek V4 Flash (oMLX) and
  Qwen3.8-27B-bf16 in the local cache — distillation traces can be
  generated entirely on-device.
- **Serving + integration seam present**: mlx_lm.server (:8080),
  the small-sidecar pattern (:8082 — the launcher already runs this
  exact 9B for background calls), the LiteLLM shim (:4000), and TEE's
  proven client idiom (`kernel/local_vlm.py`: stdlib OpenAI-style
  client, `available()` probe, env-configured endpoint, structured
  degrade). A `local_llm.py` sibling is a small, boring file.

## "Motivated" made concrete — the chore list

Motivation is a job description, not a vibe. The TEE-native model
serves ONLY server-side chores where quality-per-token is measurable,
and never sits in the client's token path:

1. **web_lookup extraction** (research 49): (page text, question) →
   question-focused extract. Guarantee that kills hallucination for
   this job: **extractive-by-verification** — every emitted sentence
   must appear (near-)verbatim in the source or the extract is rebuilt
   from the dumb-parser path; a string check, cheap, absolute.
2. **Requirement-fact structuring**: transcripts/briefs → typed facts
   JSON (the extract lane's in-band pass, upgraded).
3. **Recap & label compression**: tee_status recaps, checkpoint
   labels, diff summaries — the news-not-echoes discipline applied by
   a model that read the whole thing.
4. **kb_search expansion/rerank**: query → synonyms/domain terms;
   rerank hits. Tiny prompts, tiny gains, measurable.
5. **Never**: `bpy`/`unreal` API facts (the A30 discipline extends to
   the in-house model — a small LLM is a hallucination risk exactly
   where research grounding is mandatory), and never verdicts that
   TEE's deterministic checkers already compute.

Output contract: every chore answers in TEE's report shapes (typed
JSON, budgeted, provenance-stamped `model: tee-<name>@<revision>`), so
"motivated" is enforced by schema, not hoped for.

## The build ladder, with effort honestly sized

- **Rung 0 — behavior layer (days).** `kernel/local_llm.py` + `[llm]`
  config + per-chore prompt templates with few-shot examples from TEE
  fixtures + thinking-off + JSON-constrained decoding. Integrate
  behind the existing degradation idiom (`refine=auto|local|off`, the
  `as_photo_material` pattern): no endpoint → the current dumb paths,
  loudly labeled. Benchmark before/after on fixtures (extract-quality
  graded against held-out questions; grading by the big local model,
  labeled as such).
- **Rung 1 — the LoRA "motivation pack" (a week, on this Mac).**
  Generate 2–5k distillation examples per chore with the local
  teachers over TEE fixtures; `mlx_lm.lora --train` on the 9B-4bit (or
  a 4B-class base for zippier still); ship the adapter alongside TEE
  with the base fetched from upstream (adapter ~tens of MB, under
  every download gate). Adopt ONLY if Rung 0's measured quality gap
  justifies it — the benchmark decides, not enthusiasm.
- **Rung 2 — pretraining: stays rejected** (above).

## The adjectives, answered with numbers

- **Optimized**: 4-bit MLX weights, prompt-cache reuse (the mlx server
  already runs a 10-slot KV cache), thinking disabled for chores,
  JSON-schema-constrained outputs, per-chore max_tokens.
- **Zippy**: 105 tok/s measured; sub-second first token on short
  chore prompts; lazy-start (the VL server's proven pattern) so it
  costs nothing until first use.
- **Motivated**: the chore list + schemas + (optionally) LoRA weights
  trained on nothing but TEE's own tasks.
- **Lite**: 5.3 GB resident (9B-4bit) or ~2.5 GB on a 4B base;
  adapter-only distribution; zero client tokens ever.

## Licensing and packaging

Base model must be Apache-2.0/MIT-class (Qwen3.5 family qualifies;
verify per exact repo at adoption through the existing license lint —
same discipline as every runtime dep). The trained adapter is TEE's
own artifact. Packaging stance inherited from research 49: TEE talks
to ANY OpenAI-compatible endpoint; it does not ship or manage model
servers in the MVP — bring-your-own-model docs plus this doc's
reference setup. Working name: owner's call (Voxkiln precedent).

## Risks and their gates

- **Hallucination**: extractive-verification for quotes; schema
  validation for facts; the A30-style API ban; graded fixtures in CI
  (weightless: fixtures + a fake endpoint; live grading marked).
- **Silent quality drift**: adapter revisions are versioned and
  benchmarked before adoption; provenance stamps name the revision.
- **Memory pressure**: the 9B shares a 128 GB machine with DCCs and
  voxkiln — lazy-start + idle-unload; never resident during a
  generation battery (the §2 lesson).
- **Scope creep**: the chore list is the whitelist; new chores enter
  through a benchmark row, not a prompt edit.

## Verdict

**Viable and cheap.** Every ingredient is already on this machine —
base models, trainer, teachers, server, and TEE's integration idiom —
and the speed measurement says the experience will feel instant for
chore-sized work. The right build order is Rung 0 first (days,
reversible, measurable), Rung 1 only on benchmark evidence. Building
it would be an owner decision (next free number at time of writing:
A34), scoped to the chore list above.
