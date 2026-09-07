# 77 — the engine lane: `eng_*`, truth about local models

Design of record for **A76** (`CLAUDE_A76_SCRIPT.md` is the plan). Written
2026-09-07. It **builds on** docs **50** (a TEE-native small LLM), **55**
(cloud-local routing), **66** (senses for blind hosts) and **49** (`tee_web_lookup`
on local infrastructure) and re-derives none of them: the honesty ladder, the
cascade design and the borrowed-eye pattern are settled there and cited here.
Every number below was measured on the owner's Mac on 2026-09-07 by direct read
or probe; nothing is remembered.

## 1. The observation

TEE is a thorough **client** of local models and never a **server** of them —
that part is by design and stays. What is not by design is that **it holds no
truth about them.**

`kernel/machine.py::ENGINES` is the registry the cascade runs on. It declares
capability, senses, footprint, QoS, per-engine token floors and measured
latency. `llm/router.py::_ladder()` orders the rungs by
`float(ENGINES[e]["cost"]["latency_s"][1])` — cheapest first, read out of a
Python source file. Those numbers are **hand-copied literals stamped with the
date of the session that produced them**:

```python
"footprint_gb": 9.0,   # 8.0 measured R0 2026-08-29
"footprint_gb": 55.0,  # 43.7 measured R0 2026-08-29
"cost": {"latency_s": [4.41, 4.41], "measured": "A46 P3a 2026-08-31"},
```

Note the first two lines: the declared number and the measured number **are
different numbers, in the same line**, and `MachineLedger.may_swap()` does its
RAM arithmetic on the declared one. A65 gave this repo the law — *a declaration
is a claim and a measurement is evidence* — and `ENGINES` is a table of claims
wearing the word `measured` in a string field.

Nothing reconciles it. `available()` in both drivers is a single `GET /models`.

## 2. The drift, measured today

| what | measured |
|---|---|
| the shim's routes | `claude-qwen-27b`, `qwen-27b`, `claude-qwen-35b`, `qwen-35b`, `claude-qwen-small`, `claude-qwen-vl`, `mlx-community/*`, `claude-qwen-max` — **eight, and no `deepseek`** (`grep -ci deepseek` → 0) |
| `dsflash` | still a live `ENGINES` rung with the **cheapest declared latency**, so `_ladder()` tries it first. It has no shim route |
| `q35b` | **is** served (`claude-qwen-35b`), and TEE cannot reach it: `BUILTIN_PROFILES` holds only `q14b` and `q27b`, so `router.py:120` skips it |
| `.tee/config.toml` | dated **Aug 30 14:17**, declares `[llm.profiles.qmax]` with `paid = true` — the **paid** engine is the only profile it adds |
| the default engine | `[llm] url = ":8080/v1"`, `model = "tee-coder"`. `:8080` is `mlx_lm.server`, which enumerates HF-cache ids; `tee-coder` is not one. `available()` compares `row["id"] == model`, so **`q14b` — THE default — probes false even with the whole stack up** |
| right now | `:4000`, `:8080`, `:8081`, `:8082` all fail to connect |

So TEE declares what the machine does not serve, cannot reach what it does, and
its default profile is dead by name. Every chore currently degrades to its
deterministic path — designed behaviour, but the measured routing story in
PROGRESS is not reproducible from this state.

**None of this is the owner's fault and the digest must not imply it is.** Three
of the five facts are things changed outside the repo: a shim route removed, a
server stopped, a model deleted. A lane that reconciles against a live machine
will often report *your machine changed* — that is exactly what the router needs
to know, and the tone is a design constraint (§6).

## 3. A defect this surfaced

`llm/router.py:130-135`:

```python
try:
    result = call(_hop_cfg(cfg, engine))
except TeeError as exc:
    hops.append({"engine": engine, "verdict": exc.code})
    ledger.record_route(engine, verified=False)
    continue
```

**Any** `TeeError` records a verification failure — `llm_unreachable` (nothing
listening) exactly as much as a genuine verifier kill. The arm above it, for a
profile not declared on this machine, correctly records `skipped` and no
failure: A46 fixed the *undeclared profile* case and not the *dead endpoint*
case.

Doc 55 designates `escalation_rate` as the quality alarm — *"a rising rate is a
visible alarm, not a hidden cost"*. On this machine today it is measuring
whether a port is open. The fix is one `elif` and one meter column, and it is
worth more than most of this lane.

## 4. The thesis

Reconciliation **alone** is a config fix in a lane costume, and §7 says so
plainly. What earns a lane is one level down: the numbers the router sorts on
are unmeasurable by reading, and nothing in TEE has ever produced them
automatically.

So the lane's product is **a measured engine row**:

```
discover what this machine serves  ->  read what the weights say about themselves
  ->  audition the model on TEE's own chore fixtures, graded by the chores' own
      deterministic verifiers  ->  emit a row: warm and cold latency, the token
      floor found by sweeping rather than assumed, senses, footprint, and an
      OpenAI-conformance profile  ->  persist it machine-locally  ->  the router
      orders on the file, not the literal.
```

Reconciliation then falls out as a *consequence*: once measurement exists,
"declared but never measured" and "measured but no longer served" become
computable states rather than an afternoon of detective work.

Two alternatives, absorbed rather than rejected:

- **Engine adapters for Ollama / llama.cpp / vLLM.** There is no adapter-shaped
  gap — `local_llm.complete()` already posts plain OpenAI `chat/completions`,
  which all of them speak, and none is named anywhere in `server/src/`. There is
  an **evidence** gap: `docs/setup-local-llm.md` asserts any such endpoint
  "works identically" and nothing has ever tested it, while divergences in that
  class are known to exist (an OpenAI shim that ignores `chat_template_kwargs`
  silently drops `enable_thinking: False`; one that ignores the `adapters`
  extension drops the LoRA; one that lists tags rather than HF ids fails
  `available()`'s id equality). Those are conformance *measurements*, and they
  belong in the audition.
- **A managed lifecycle.** Rejected. `profiles.py` already has one, opt-in and
  verified, and `PROTECTED_PORTS` puts the owner's stack out of bounds. A second
  start/stop path is one step from a model manager and two from a server.

## 5. The tool surface

Prefix **`eng_`**, package `server/src/tee/engines/`. **Zero always-loaded
tools**; each tabled individually in `kernel/trust.py::_EXPLICIT` with
**deliberately no `eng_` family row** — three of the six read and three drive
engines or write state, so a prefix default would hand the writers the open tier.

| tool | what it does | trust row | job |
|---|---|---|---|
| `eng_scan` | every endpoint TEE knows (`[llm] url`, each profile's, `[senses] vision_url`, `local_vlm.DEFAULT_URL`, `[engines] endpoints`) → `GET /v1/models`; who answered, which ids, round-trip, and a **server-software fingerprint** from response shape and headers. No generation | `read-compute` | no |
| `eng_senses` | resolve a model id to weights by stdlib path arithmetic over the HF cache (honouring `HF_HOME`/`HF_HUB_CACHE`), read `config.json` for `architectures` / `vision_config`, sum `*.safetensors` for footprint | `read-extract` | no |
| `eng_check` | one ~10-token completion: liveness, first-token and total wall, and the conformance block — `<think>` leakage, `json_object` honoured, `chat_template_kwargs` honoured, `adapters` accepted or 400, `usage` present | `call-engine` | no |
| `eng_audition` | **the measurement.** TEE's own chore fixtures graded by their own deterministic verifiers, sweeping `max_tokens` to *find* the floor rather than assume it. Emits a candidate row | `call-engine` | **yes** |
| `eng_reconcile` | **the digest.** Joins four tables that have never been joined — `ENGINES` × `profiles(cfg)` × the cached scan × the measured file — one verdict and one-line fix per row. Cache only; never probes | `read-compute` | no |
| `eng_adopt` | write an auditioned row to `.tee/engines.json`, which the ladder reads. Refuses a `paid = true` profile by name | `write-state` | no |

Lane in `kernel/lanes.py`: **`None`** — the `LEGEND`'s *"and the rest are
headless"* already covers it and the 2 KB instructions cap argues against
spending bytes to name it. Stdlib-only: no optional extra, no `extras.WITNESS`
row, which is both the point and enforced by the gate.

**Reuse, do not rewrite.** `senses.py::_vision_facts()` is already the
config-overrides-`ENGINES` merge `table.py` needs, and its payload is the
provenance shape. `windtunnel/engines.py` is the cached-probe pattern.
`kernel/spend.py` is the measured-vs-estimated discipline.
`benchmarks/run_m3_llm.py` and `run_r0_routing.py` already hold the fixtures, the
verifier grading and the client-brief column — import them.

## 6. Laws

1. **TEE serves no model.** Client and witness only; a test asserts the package
   opens no listening socket.
2. **The lane measures; the owner declares.** It never writes `.tee/config.toml`
   — it prints the line to paste. A45's *TEE never grants itself*, one notch on:
   TEE never configures itself either.
3. **Never start or stop anything**, and emphatically not on
   `PROTECTED_PORTS = (8080, 8090, 4000)`.
4. **Never call a paid engine** — refused by name, not gated behind consent.
   Measuring a hosted model bills the owner to learn a number the router is
   forbidden to use.
5. **Never download weights.** Acquisition stays an owner gate (doc 50 §M0).
6. **Senses come from the weights' own `config.json`, never from behaviour** —
   A49's method: the shim reroutes image requests, so through it every model
   appears to see. A model served from a content-addressed store (oMLX) yields no
   recoverable identity and gets `unverified`, stated rather than guessed.
7. **A latency number without a warm/cold label is a lie.** The ladder sorts on
   warm; the row carries both, and names the endpoint and server software,
   because a number taken behind a proxy is partly a number about the proxy.
8. **The digest never probes.** Probing is a tool the caller chooses; putting a
   network call inside a cold-session tool spends latency on every turn.
9. **A measured row can go stale too** — the failure being fixed, one layer
   down. Every row carries `measured_at`, endpoint, model id and fingerprint;
   past `stale_days` it is `stale`, and if the endpoint now serves a *different*
   model it is not stale, it is **wrong**, and those are different verdicts.
10. **The digest reports; it never scolds.** A stopped server is a fact, not a
    fault.

## 7. The token argument

`eng_reconcile` returns roughly 200 tokens. On this machine today:

```
endpoints 4 scanned / 0 answering · measured rows 0 · every chore degrading
q14b+a2  named-wrong          [llm] model="tee-coder"; :8080 serves HF ids
                              fix: model = "mlx-community/Qwen2.5-Coder-14B-Instruct-4bit"
q27b     endpoint-down        127.0.0.1:8080 silent
dsflash  declared-not-served  no shim route, no weights -> drop the row
q35b     served-not-reachable shim serves claude-qwen-35b; no profile declared
qvl      endpoint-down        127.0.0.1:8081 silent
qmax     paid                 never auditioned, never a router target
```

The naive alternative is what this session actually did: read `machine.py`,
`profiles.py`, `router.py`, `llm/tools.py`, `local_llm.py` and the head of
`chores.py` — about 1,730 lines — plus the config, the shim yaml, and a
`/v1/models` dump per endpoint. **P0 measures that exactly with
`estimate_tokens`** rather than by line arithmetic; the estimate is ≈21,000
tokens, so roughly **100×**.

**The larger saving is not the digest.** A wrong `ENGINES` row costs tokens on
every chore, forever. Today's ladder tries `dsflash` (skipped, no profile), then
`q14b` (dead by name), then `q27b` (dead endpoint), then escalates a brief to the
client — **which does the whole task in its own context.** That is precisely the
cost the local tier exists to avoid, paid on every routed chore. A correct ladder
is not an optimisation of the digest; it is the difference between the local tier
existing and not.

The third saving is a metric, not a token: §3's split is what turns
`escalation_rate` back into a signal.

## 8. Non-goals

Serving a model, in any form — no `/v1` route, no proxy, no shim · starting or
stopping any process · writing the owner's config · downloading weights ·
quant selection · eviction *management* (eviction stays disclosed, never driven)
· streaming, batching or concurrency · embeddings and tokenizers · routing by
confidence (doc 55's calibration law stands) · redirecting the client's
conversation (doc 55's scope law stands).

## 9. Open questions

1. **Does this earn a lane?** `eng_reconcile` alone does not — dropping the
   `dsflash` row, adding the missing profiles, fixing `[llm] model` and adding a
   doctor line is half a day and fixes today's outage completely. The lane earns
   its place only through the audition landing where the router reads it. **If no
   session on a machine with a live stack will spend an hour auditioning, cut
   this campaign to that config fix and do not build a lane.**
2. **May an audition load a 65 GB model?** `may_swap` says yes on 128 GB, but
   A47 measured that it evicts whatever the owner is using. Proposal: refuse
   while any job is registered, and never audition two heavy models back to back
   without stating the swap seconds.
3. **Is non-MLX conformance in scope?** It needs Ollama or llama.cpp installed,
   which is a download gate. If declined, `setup-local-llm.md`'s "works
   identically" must be softened to *MLX and LiteLLM measured; others untested*.
4. **The prefix and lane name** — `eng_` / "engines". The owner's.

## 9b. P0 answers (2026-09-07, measured on the owner's Mac)

**The shim advertises eight routes; two of them work.** `77-evidence/shim-truth.py`
asks every advertised route for six tokens and reads what comes back:

| route | `/v1/models` | asked | produced | note |
|---|---|---|---|---|
| `claude-qwen-27b` | listed | 200 | **no** | empty content, usage claims 6 tokens |
| `qwen-27b` | listed | 200 | **no** | same |
| `claude-qwen-35b` | listed | 200 | **no** | same |
| `qwen-35b` | listed | 200 | **no** | same |
| `claude-qwen-small` | listed | 500 | no | `Hosted_vllmException` — `:8082` is down, and says so |
| `claude-qwen-vl` | listed | 200 | **yes** | `'OK! 😊'` |
| `claude-qwen-max` | listed | 200 | **yes** | the paid route |

**advertised 8 | produce text 2 | 200-but-empty 4 | errored 1.** A liveness
check that reads `/v1/models` sees eight healthy engines. One that reads the
HTTP status sees six. Only one that reads the **content** is telling the truth,
and `local_llm.available()` is the first kind. Its own docstring states the
assumption the machine falsifies — *"The model may still be COLD — listed but
not loaded — which costs only latency"* — where here it costs an empty answer
recorded as a verification failure.

**The naive read is 20,840 tokens** — `machine.py` 5,711, `profiles.py` 6,473,
`router.py` 2,366, `llm/tools.py` 2,052, `local_llm.py` 2,245, the head of
`chores.py` 963, `.tee/config.toml` 274, `litellm.yaml` 756; 1,783 lines,
72,963 bytes, by TEE's own `estimate_tokens`. **And it does not answer the
question** — the empty-200 table above is in none of those files and cost live
probes.

**Two of §2's own claims are corrected by measurement.** `LADDER` is
`('q14b+a2', 'dsflash', 'q27b-bare', 'q35b')`, so `q14b+a2` sorts first at
1.74 s, not `dsflash` at 4.41 as this doc and the script said. And *"nothing is
answering at all"* was true when written and is false now. Both were
declarations of ours, outranked by a measurement, which is this campaign's own
thesis applied to its author.

**Three more defects P0 found, none of them the one it went looking for.**

1. **`doctor.check_llm` reports `ok` with no fix while chores are dead.**
   `if llm_up or vlm_up:` takes the early branch on vision alone, so a machine
   whose chore engine is down by name reports healthy. Measured live:
   `chores down at http://127.0.0.1:8080/v1 (tee-coder); vision UP` →
   `status="ok"`, `fix=None`.
2. **`save_state` silently persists nothing without `cfg["_state_dir"]`**, which
   is injected at exactly one site (`app.py:277`). A `switch()` called from a
   CLI or a test returns `{"ok": true, ...}` and changes nothing — this session
   hit it while switching profile on the owner's instruction.
3. **`switch()`'s own refusal advertises profiles that do not exist here** —
   `TEE/35B` and `TEE/DSFLASH` name profiles absent from both `BUILTIN_PROFILES`
   and the config, so typing either raises `llm_unknown_profile` whose fix line
   recommends them.

Two dead declarations worth recording: `min_chore_tokens`' only non-default row
(`q35b`, 1024) is unreachable because `q35b` is not a declared profile, and
`senses_source` — the provenance field A49 added — is **read nowhere in the
codebase**. `RESERVE_GB = 16.0` carries its own comment calling itself "a stated
placeholder until R2 measures the real constant", and `may_swap` and `may_admit`
both spend it.

**The router defect, reproduced before it is fixed.**
`server/tests/test_a76_router_unreachable.py` — five tests: three pass (every
rung attempted, the escalation recorded, a genuine verifier kill still counted
as one), and **two are strict xfails** that turn into a gate the moment P3 lands
the split. A fifth asserts the two causes are currently indistinguishable and is
marked for deletion when they are not.

## 10. Sources

All read or run 2026-09-07 on the owner's Mac: `kernel/machine.py`,
`llm/router.py`, `llm/profiles.py`, `llm/tools.py`, `kernel/local_llm.py`,
`kernel/local_vlm.py`, `senses.py`, `kernel/lanes.py`, `.tee/config.toml`,
`~/.claude/qwen-local/litellm.yaml`, and `curl` against `:4000`, `:8080`,
`:8081`, `:8082`. Prior art: research docs 49, 50, 55, 66.
