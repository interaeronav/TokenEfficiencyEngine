# A34 build script — web_lookup + the TEE-native code model

**What this builds** (owner directive, 2026-08-28): the two capabilities
researched and measured in `docs/research/49-web-lookup-multimodal.md`
and `docs/research/50-tee-native-small-llm.md` (incl. its code-root
addendum) — a budgeted, cited, multimodal **web_lookup** tool, and the
**TEE-native small LLM**: a dense code-and-debugging expert serving
TEE's chore list on local infrastructure. The research docs ARE the
design; this script is the build order and the acceptance bars. Read
both docs before writing any code, and re-read the relevant section at
the start of each phase.

A one-paste prompt for a fresh session:

> Read CLAUDE.md, then CLAUDE_A34_SCRIPT.md, then research docs 49 and
> 50, then the last dated entries of docs/PROGRESS.md. Call tee_status
> and tee_recall first and use TEE's own tools as co-pilot throughout.
> Work the A34 tracks from where the evidence says they stand —
> fixtures before features, benchmarks before adoption. Stop and
> report if any phase's premise no longer holds.

## Standing rules (inherited, plus two specific gates)

- Everything in CLAUDE.md and the A33 campaign rules applies: branch
  `claude/token-efficiency-engine-5jv1dj`, small evidence-backed
  commits, PROGRESS before ticks, append-only benchmarks,
  revert-on-regression, A30/A31 knowledge boundaries, owner-only
  decisions flagged never made, friction → `docs/SI_BACKLOG.md`.
- **Download gate**: the chosen base model (4-bit, 7–14B ≈ 4–9 GB)
  exceeds the 2 GB rule — state free disk and ask the owner before
  fetching. Everything else in this campaign is under the gate.
- **Machine etiquette**: no LoRA training or model benchmarking
  concurrent with a voxkiln battery or UE editor session (the §2
  lesson); lazy-start and idle-unload are part of every acceptance.

## Track W — web_lookup (design: research 49 + its mitigation section)

### W0. Contracts and hostile fixtures FIRST (weightless, CI)

1. The answer schema (`{quote, source, retrieved_at, truncated}`), the
   tool description's untrusted-content sentence, and the SSRF
   validator spec written as tests before any fetcher exists.
2. Fixture suites: hostile pages (instructions in body / alt-text /
   hidden div / comment / image text → extract passes through inert,
   no server state changes); evil URLs (metadata IP, decimal-encoded,
   userinfo@, redirect-to-localhost, rebinding simulation → all
   refused with rule-6 fixes); robots/rate fixtures on a local test
   server. These fixtures are the definition of done for W1–W2.

### W1. The guarded fetcher

Resolve-then-pin IP validation (loopback/private/link-local/ULA/
multicast refused; per-hop redirect revalidation, max 3), http/https +
80/443 only, size caps (5 MB text; larger media → the cost-confirm
gate), timeouts, TTL'd private cache (URL-hash + ETag revalidation),
`urllib.robotparser` + Crawl-delay, per-host rate limit, honest
versioned UA, 429/503 backoff. Stdlib only. Acceptance: W0's evil-URL
and etiquette fixtures green; refusals carry the exact fix.

### W2. The extractor

Stdlib parser per research 49 (script/style/template/comment/hidden
stripped, zero-width and bidi controls dropped, whitespace normalized,
hard cap) → budgeted, cited extract. Optional cheap `kb_search`
precheck: when the KB already answers, say so in the response (KB-first
routing made visible, not enforced). Acceptance: the three research-49
pages reproduce ≈500-tok extracts; hostile-page fixtures green.

### W3. The tool + the benchmark

`web_lookup {url, question, max_tokens=500, media=auto|off}` joins the
always-loaded surface at SI-1 discipline — measure the surface delta
(~60–120 tok budget) and record it. Then, BEFORE any tuning, the
research-48-style scenario: "answer five documentation questions",
naive (page-in-context) vs TEE — append to benchmarks/RESULTS.md.
Skills (`tee-usage`) and docs (quickstart line, security.md additions
from the mitigation section) updated. Acceptance: benchmark row + docs
+ surface delta all recorded.

### W4. Media arms

Images: only when the question needs them AND a local endpoint answers
(`local_vlm` contract) — top-N captioned server-side, degrade per the
research-49 contract (inline via tee_media, or the structured refusal;
never silent). Audio/video FILES: size-gated through cost-confirm →
extract-lane transcription → facts. Anti-goals enforced by test: no
streaming-platform fetch paths, no paywall bypass. Acceptance: one
live captioned lookup + one live transcribed lookup recorded (start
and stop the local stack the way the launcher does), degradation paths
proven with NOTHING running.

## Track M — the native code model (design: research 50 + addendum)

### M0. Adoption research (deep, open, dated)

Pick the base per the addendum's criteria: **code-specialist, dense
preferred, 7–14B, Apache/MIT through the license lint, MLX 4-bit
available, `mlx_lm.lora`-trainable.** Seed shortlist from the
2026-08-28 open-research pass (verify everything at adoption day):
Qwen coder family 7B/14B (Apache-2.0), Ministral 3 dense 8B/14B
(Apache-2.0), DeepSeek-R1 distill 7B/14B (MIT, debugging-strong).
Append the candidate table, the choice, and the evidence as a dated
section in research 50. Owner gate: the weights download (state free
disk, ask). Acceptance: the dated section + the linted license file.

### M1. The client seam

`kernel/local_llm.py` mirroring `local_vlm.py` exactly (stdlib
OpenAI-style client, `available()` probe, `TEE_LOCAL_LLM_URL/MODEL`
env, thinking disabled, JSON-constrained decoding, structured
"start the local stack" refusal), `[llm]` config section, a fake
endpoint for CI. Acceptance: contract tests green with the fake; live
round-trip recorded once with the real endpoint.

### M2. Rung 0 — the chores as templates

Implement the chore list behind the `refine=auto|local|off` idiom,
each with schema-validated output and a provenance stamp
(`model: tee-<name>@<revision>`):

1. **Traceback triage** (flagship): failure text → one-line diagnosis
   + exact fix. Ships with the API-defer trap fixtures — seeded
   tracebacks whose correct fix needs an API the fixture omits; the
   passing answer defers to docs/research or a live probe, the failing
   answer invents. A trap failure blocks adoption outright.
2. **Script repair draft** on tee_script/batch validation failures.
3. **Lint explanation** (deterministic checkers stay the judges).
4. **web_lookup extraction** upgrade (Track W consumer) — with the
   extractive-by-verification guarantee: every emitted sentence
   string-checked against the source, else fall back to W2's parser.
5. Fact structuring, recap compression, kb rerank (the research-50
   originals).

Acceptance: all chores green on fixtures with the fake; the trap suite
green with the real model.

### M3. The benchmarks decide

- Fix-loop scenario re-run with triage on — append the row (the
  current mark to beat sits in benchmarks/RESULTS.md; any regression
  reverts the chore, not the benchmark).
- Extract-quality graded fixtures for chore 4 (grader = the big local
  model, labeled as such in the row).
- Latency rows per chore (the 105 tok/s / 5.3 GB baseline from
  research 50 is the reference).
Acceptance: rows appended; a one-paragraph adopt/don't-adopt verdict
per chore in PROGRESS, from the numbers.

### M4. Rung 1 — the LoRA gate (only on M3 evidence)

If and only if M3 shows a quality gap worth training: distillation
set (2–5k examples/chore) generated from TEE's own failure universe
(fault-injection tables, PROGRESS tracebacks, seeded fixtures) by the
local teachers; `mlx_lm.lora` overnight on a quiet machine; adapter
versioned, benchmarked against M3's rows, adopted only on improvement.
Skipping is a valid, recorded outcome. Acceptance: either the adapter
+ its winning rows, or the dated "rung 0 suffices" verdict.

### M5. Close-out

Docs (bring-your-own-model + reference setup + memory-pressure rules),
suites green, and the campaign ledger in PROGRESS: surface delta, new
benchmark rows, chore adoption verdicts, live-proof pointers —
wrong-way numbers in the same table with their why. `tee_remember` the
close-out. Owner decides the version bump.

## Order and interleaving

W0 + M0 first (fixtures and adoption research share no code). Then
W1→W2→W3 (the web text MVP goes live and benchmarked before media),
then M1→M2 with W4 interleaved (both consume the local-endpoint
lifecycle), then M3 → M4 gate → M5. Premises to re-check at each
session start: the local endpoints are OPTIONAL (every degrade path
must pass with nothing running); the installed co-pilot's project_root
is this repo; parallel sessions may hold this branch — pull first.
