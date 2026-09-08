# CLAUDE_A76_SCRIPT.md — the engine lane: `eng_*`, truth about local models

**Owner directive (2026-09-07):** *"research a lane for an open source model"*,
**both** lanes, *doc + campaign script*, **flight first**. A75 is the flight
lane; this is the second half — a lane for the open-weights models TEE routes
work to.

Campaign **A76**; research doc **77** the design of record, building on **50**,
**55**, **66** and **49** by citation; server **0.27.0 → 0.28.0** (A75 takes
0.26.0); pytest marker **`engines`**. Confirm both series are free before the
first commit. Phases are independently shippable.

## Read this before P0 — the campaign may not be worth running

`eng_reconcile` shipped alone **is a config fix in a lane costume.** Dropping the
`dsflash` row, adding `q35b`/`dsflash` to `BUILTIN_PROFILES` (or removing them
from the phrases `llm/tools.py` advertises), fixing `[llm] model`, and adding a
`doctor` line is **half a day** and fixes today's outage completely.

The lane earns its place only through **P2 and P3** — the measurement that cannot
be read out of any file, landing where the router consults it. **If no session on
a machine with a live model stack will spend an hour auditioning, stop here, do
the config fix, and record that decision in `DECISIONS.md`.** Doc 76 §9 question
1 is that decision, and it is the owner's.

## Orientation for a cold session

- Repo `/Users/john/TokenEfficiencyEngine`. Read `docs/PROGRESS.md` first; paste
  real output per phase; **stage only this campaign's own paths** — another
  session edits this repo in parallel.
- Suites: `cd server && uv run --no-sync pytest -q` · `-m engines` (the live
  tier) · `make lint`. **Never `uv sync` in `server/`.**
- **Surface invariant: 17 always-loaded tools.** A76 adds **ZERO**; every
  `eng_*` is a `VirtualTool`. `server.py` and `kernel/lanes.py` stay untouched.
- The lane lives at `server/src/tee/engines/` and is **stdlib-only** — no extra,
  no `extras.WITNESS` row. That is the point, and the gate enforces it.

## Measured facts (2026-09-07, the owner's Mac — build ON them)

1. **The shim serves eight routes and none is `deepseek`** —
   `claude-qwen-27b, qwen-27b, claude-qwen-35b, qwen-35b, claude-qwen-small,
   claude-qwen-vl, mlx-community/*, claude-qwen-max`; `grep -ci deepseek
   ~/.claude/qwen-local/litellm.yaml` → **0**. `ENGINES` still carries `dsflash`
   as the **cheapest declared rung**, so `_ladder()` tries it first.
2. **The inverse also holds:** `q35b` *is* served and TEE cannot reach it —
   `BUILTIN_PROFILES` holds only `q14b` and `q27b`, so `router.py:120` skips it
   with *"profile not declared here"*.
3. **The default engine is dead by name.** `.tee/config.toml` (Aug 30 14:17) has
   `[llm] url = ":8080/v1"`, `model = "tee-coder"`. `:8080` is `mlx_lm.server`,
   which enumerates HF-cache ids; `tee-coder` is not one, and `available()`
   tests `row["id"] == model` — so `q14b` probes false even with the stack up.
   The only profile the file *adds* is `[llm.profiles.qmax]`, `paid = true`.
4. **Nothing is answering.** `:4000`, `:8080`, `:8081`, `:8082` all fail to
   connect. Every chore currently degrades to its deterministic path.
5. **Declared and measured differ in the same line:**
   `"footprint_gb": 9.0,  # 8.0 measured R0 2026-08-29` and
   `"footprint_gb": 55.0,  # 43.7 measured R0 2026-08-29`. `may_swap()` does its
   RAM arithmetic on the declared column.
6. **The router defect**, verbatim at `llm/router.py:130-135`: `except TeeError`
   → `ledger.record_route(engine, verified=False)`. `llm_unreachable` and a real
   verifier kill increment the same counter; the `skipped` arm above it does
   not. A46 fixed the undeclared-profile case, not the dead-endpoint case. Doc 55
   designates `escalation_rate` the quality alarm — today it measures the
   network.
7. **No engine software but MLX is named anywhere in `server/src/`.** Ollama,
   llama.cpp, vLLM, LM Studio: zero hits. `setup-local-llm.md` claims any
   OpenAI-compatible endpoint "works identically" and nothing has ever tested it.

## Prior art in this repo (copy these, do not reinvent)

- **`senses.py::_vision_facts()`** — already the config-overrides-`ENGINES` merge
  `table.py` needs, and its payload is the provenance shape to copy.
- **`windtunnel/engines.py`** — `probe()`, `probed_at`, the cached probe, the
  INSTALL table: the discovery pattern.
- **`kernel/spend.py`** — the measured-vs-estimated discipline, and the reason
  TEE ships no price table.
- **`benchmarks/run_m3_llm.py` / `run_r0_routing.py`** — the audition's fixtures,
  verifier grading and client-brief column, already written. **Import them.**
- **`pointcloud/tools.py`** — a many-tool, zero-always-loaded lane.
- **`tests/test_windtunnel_licences.py`** — the gate.

## Phases

- **P0** — the measurements above reproduced with their commands; the naive-read
  cost measured with `estimate_tokens` over the exact file set; the four-way
  drift table; the oMLX content-addressed limit written down; the ruling in
  `DECISIONS.md` (including doc 77 §9 question 1 — *lane or config fix*); doc 77
  and this script. **The router defect reproduced as a hermetic test that fails.**
  *Acceptance:* every fact carries its command; the failing test exists **before**
  any fix; doc 77 cites 50/55/66/49 rather than re-deriving them.

- **P1** — the deterministic half, hermetic. `discover.py`, `weights.py`,
  `table.py`; `eng_scan`, `eng_senses`, `eng_reconcile`; three trust rows with
  the no-family-row comment; the licence gate; fake endpoints in five server
  shapes (LiteLLM, mlx_lm.server, Ollama, llama.cpp, vLLM) and one test per
  verdict class.
  *Acceptance:* `eng_reconcile` reproduces P0's drift table **from fixtures
  alone**; the digest measures **under 80 tokens per row** (250 total was the opening guess; five rows measured 295, and the excess is the fix lines, which are the value); surface still 17; an
  untabled `eng_*` is a **startup** error; the lane imports stdlib-only and a
  test asserts it opens no listening socket.

- **P2** — the live tier (`-m engines`). `eng_check`, `eng_audition`, the
  `engine-audition` `ENGINES` row, the cold/warm split, the token-floor sweep,
  the conformance block. Run against **two server softwares** — that is the only
  thing that makes fact 7's claim true or false.
  *Acceptance:* a measured row for every engine this machine serves, in
  `.tee/engines.json` and quoted in PROGRESS with wall times; **the sweep
  re-derives `q35b`'s 1024 floor independently** rather than reading the source
  comment — if it lands elsewhere, the comment was the claim and the sweep is the
  evidence; the non-MLX run names a conformance divergence or proves there is
  none, and `setup-local-llm.md` is amended to whatever was measured.

- **P3** — the router reads it, and the meter stops lying. `eng_adopt`;
  `_ladder()` ordered from the measured file with the source literals as
  fallback (note `LADDER` is a module-level constant consumed inside `route()` —
  it becomes a per-call lookup); `min_chore_tokens` from the measured row; the
  unreachable/unverified split plus an `unreachable` column in `meter_block()`;
  `doctor.check_llm` calling `discover.scan()`; `tee_status`'s `llm_profile`
  line carrying liveness and age **from cache**.
  *Acceptance:* P0's failing test passes; a chore against a dead endpoint leaves
  `escalation_rate` attributable; changing a measured row changes the ladder
  order, proven by a test; `eng_adopt` refuses a `paid = true` profile by name;
  **nothing writes `.tee/config.toml`.**

- **P4** — the close. `docs/engines-lane.md`; `setup-local-llm.md` amended with
  the measured conformance table; doc 66's open question 1 answered or restated;
  the `CLAUDE.md` bullet, CHANGELOG 0.27.0, PROGRESS with numbered gaps and the
  `**Suites at close:**` line; the **search-budget re-measure** (six tools join
  the registry — re-measured, not reasoned about); version ×3; the bundle.
  *Acceptance:* a cold session finds the lane by searching *"which local model is
  actually running"*.

## Laws

1. **TEE serves no model** — client and witness only.
2. **The lane measures; the owner declares.** Never writes `.tee/config.toml`;
   it prints the line to paste.
3. **Never start or stop anything**, and never touch
   `PROTECTED_PORTS = (8080, 8090, 4000)`.
4. **Never call a paid engine** — refused by name, not gated behind consent.
5. **Never download weights.**
6. **Senses come from the weights' own `config.json`, never from behaviour**;
   a content-addressed store yields `unverified`, stated not guessed.
7. **A latency number without a warm/cold label is a lie**; the row names its
   endpoint and server software, because a number behind a proxy is partly about
   the proxy.
8. **The digest never probes**, and **it reports without scolding** — a stopped
   server is a fact, not a fault.
9. **A measured row goes stale too**: `measured_at` on every row; a changed
   served model is `wrong`, not `stale`.
10. Zero always-loaded tools; every `eng_*` tabled individually; no family row.

## Non-goals

Serving a model in any form · a process manager · writing the owner's config ·
downloading weights · quant selection · eviction management · streaming,
batching, concurrency · embeddings and tokenizers · routing by confidence ·
redirecting the client's conversation.

## Amendments learned while building

*(Append here as the build teaches.)*
