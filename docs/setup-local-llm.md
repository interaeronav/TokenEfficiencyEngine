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
adapters = "/path/to/TokenEfficiencyEngine/benchmarks/rung1/adapters/tee-triage-a2"
```

The `adapters` line loads TEE's **tee-triage-a2** LoRA (the rung-1
"motivation pack": full trap suite green where the bare base fails
kwarg-drift). TEE passes it per-request in the OpenAI-extension
`adapters` field because mlx_lm.server's startup `--adapter-path` is
never applied to named-model requests (the server resolves its adapter
map against the already-resolved model path - server.py ~line 389,
read 2026-08-28); servers that don't know the field ignore it, and the
bare base remains fully supported (triage then answers less
conservatively - the trap suite documents the difference).
Environment form: `TEE_LOCAL_LLM_ADAPTERS=<path>`.

The 7B sibling (~4.3 GB) is the recorded fallback when the latency
ladder matters more than answer strength; the 32B
(`mlx-community/Qwen2.5-Coder-32B-Instruct-4bit`, 17 GB, with its own
`tee-triage-b1` adapter) is the qualified headroom option - it passes
every gate but measured no chore-quality win over the 14B at ~2.2x the
latency (benchmarks/RESULTS.md carries the row). All swap in behind
the same seam with no code change. Any llama.cpp / vLLM / LM Studio endpoint
works identically — the benchmarks in `benchmarks/RESULTS.md` name the
exact model they were measured against, and a different model means
your numbers differ.

## Switch profiles: TEE/Q14B ↔ TEE/Q27B (A37 P0-S)

The chore engine is switchable between **named profiles** with one chat
phrase — the user types `TEE/Q14B` or `TEE/Q27B` and the assistant calls
the virtual `llm_switch` tool (zero always-loaded cost). Builtins:
**q14b** (inherits your `[llm]` config — the adopted 14B + tee-triage-a2;
THE default on fresh config, missing state, and every failed fallback)
and **q27b** (`Qwen3.8-27B-bf16`, deliberately bare — the a2 LoRA is
14B-trained; traps pass bare at ~4–6× chore latency, 3.11–10.12 s
measured). The active choice persists in `.tee/llm-profile.json` across
restarts; `tee_status` reports it.

```toml
[llm]
managed = false                    # opt-in: TEE stops/starts owned servers

[llm.profiles.q27b]                # per-key overlay over the builtins;
url = "http://127.0.0.1:8081/v1"   # new names may be added the same way
start = "mlx_lm.server --model mlx-community/Qwen3.8-27B-bf16 --port 8081"  # managed only
port = 8081
process = "mlx_lm.server"          # owned-process pattern (managed only)
rss_gb = 55                        # memory-guard footprint
```

**Unmanaged (default)**: a switch only re-targets chores (endpoint /
model / adapters per request) and reports honestly when the endpoint is
not answering. **Managed** (`managed = true`) adds a verified
stop-before-start lifecycle with single occupancy: an in-flight chore
finishes first; the leaver's owned server is stopped and asserted gone
(pid + RSS via ps) before the target starts; a free-RAM guard and a
pressure guard (UnrealEditor/voxkiln running) refuse with the reason; a
cold load returns a `tee_job` token with the ETA while chores answer a
one-line "loading, ~Ns — retry or TEE/Q14B"; a failed start restarts
the previous profile automatically. **Ownership is only ever a pid TEE
itself started**: servers on the protected chat-stack ports
(8080/8090/4000 by default, `protected_ports` to override) are used
when they answer but never started or stopped — switching away from a
borrowed server stops nothing.

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
not. A trap failure blocks adoption outright — and did, at rung 0: the
bare base (three models tried) answered kwarg-drift traps with
intent-destroying fixes. The rung-1 **tee-triage-a2** adapter closed
the gap (full suite green, latency/quality/held-out gates passed,
2026-08-28), so `llm_triage` is registered; on a bare base without the
adapter, treat its drift-case answers with rung-0 suspicion — the trap
suite is the acceptance for any substitute model. Deterministic checkers
(lint, plaus_check, validators) stay the judges everywhere — the model
translates findings, never overrules them.

Every chore answer is schema-validated fail-closed and carries a
provenance stamp (`model: tee-coder@<revision>`, the template revision
in `tee/llm/chores.py`).

## The router (A42 R1/R2): verifier-gated cascade over the engine ladder

For chores with deterministic verifiers, `tee/llm/router.py` runs the
resident engine first, lets the chore's own verdict decide (a schema
kill or an empty result is a deterministic failure), and escalates up
the ladder — the bigger local engine is reached only when the ONE
machine-load ledger says the machine is capable (no registered
reconstruction job, footprint fits), and the final tier is a budgeted
client brief that names the failures and points at the input instead
of re-dumping it. Chores without a deterministic verifier stay static
(R3 decides calibration; uncalibrated confidence gates nothing).

**The owner outranks the router**: an explicit `TEE/Q14B`/`TEE/Q27B`
switch pins the engine and suspends roaming entirely; `TEE/AUTO`
lifts the pin.

**Honest costs (measured 2026-08-29):** a full `route()` including a
loopback fake engine walls ~0.30 ms, so the router's own bookkeeping
is sub-millisecond noise against 0.7–10 s chores. Engine swap costs on
the mlx endpoint, first-request-after-model-change minus warm:
**~1.1 s to the 14B+a2** (0.15 s warm) and **~18.0 s to the 27B bf16**
(0.47 s warm) — both far under the spec guesses (30/90 s), and cheap
enough that the measured constants flipped one greedy-policy decision
(loading the 14B beats staying on a resident 27B for a single chore).

**The merged meter**: `report_savings` carries a `routing` block —
per-engine calls/verified, escalations + rate, swap columns (explicit
/ implicit / refused, with the last refusal's honest line), job-class
occupancy, and the scheduler's columns reserved in the same schema
(`queue_age_s`, `dispatch_reason`, `shadow_delta` — filled by K1/K2,
never migrated). The `tee_status` recap shows the one-line form only
when routing actually happened.

## The kernel scheduler (A42 K0–K4): internal machinery, zero new tools

Everything TEE runs — chores, jobs, swaps, gateway calls — is a task
with an id, a QoS class and a measured cost row, and a shadow recorder
traces every dispatch (~27 µs each, ≤400 B lines, 50 MB cap) alongside
what the greedy policy would have done. On top of the traces: QoS as
law (interactive never behind batch, aging against starvation,
admission control, one worker always reserved for interactive,
backpressure on the batch queue) and greedy cost-aware dispatch —
which went LIVE only after a replay of the campaign's own traces
passed the gate declared in code, and which the mixed-load row then
justified (interactive p95 −38% for +1.4 s makespan, stated).

**The degrade-to-static promise**: the scheduler is OPTIONAL by
construction. `[scheduler] shadow/qos/dispatch = false` restores
today's exact behavior — plain FIFO, resident-first routing, no
recording — each independently, each fixtured. No TEE feature requires
the scheduler to function, the recorder's failures are swallowed, and
the owner's TEE/Q pin outranks every policy. Decisions are data:
`report_savings` shows the dispatch counters, queue ages and shadow
columns; the traces live under `.tee/shadow/`.
