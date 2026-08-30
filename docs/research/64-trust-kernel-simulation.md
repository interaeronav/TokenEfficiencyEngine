# 64 — Trust-kernel integration: simulated, with failure points (2026-08-30)

Verification basis: a qmax simulation pass (Qwen-Max, 6,247 tok;
INPUT not authority — every point checked against code) fed the real
seams; direct reads this session confirming (a) chore call sites
(`chores.triage`, `chores.phrase_deviation` at capture/tools.py:473)
pass raw content with NO descriptor; (b) `shadow.record(task, actual)`
is called at the chore boundary but the descriptor omits caller/taint
today; (c) jobs run on DAEMON THREADS (jobs.py) and TEE uses NO
contextvars anywhere — so ambient propagation does NOT cross into a
worker; (d) gateway tools ARE prefixed AND fingerprint-pinned
(service.py) — the rename-to-impersonate attack is already blunted,
not open. Extends research 61/62/63; this is the "does it survive
contact" pass.

## FP-1 [HIGH, verified] Taint cannot reach the model boundary by ambience

Trigger: chore call sites take content, not a descriptor; the kernel
must infer taint from an ambient TaskDescriptor. But jobs are daemon
threads and there are zero contextvars today, so the label does not
cross the submit→worker hop — `failure_text`/`deviation_lines` arrive
at the model UNLABELLED.
Consequence: injection-bearing content reaches the local model as if
clean; the central law silently does not apply on exactly the async
paths that matter.
Fix: a `ContextVar[TaskContext]` set at `_tool()`; `jobs.submit`
SNAPSHOTS it and re-installs it inside the daemon worker (explicit
copy, since threads don't inherit it); the chore entrypoint reads it
and FAILS CLOSED (treats as tainted) when absent. One propagation
mechanism, two install points — not N call-site edits.

## FP-2 [HIGH, verified real — a hole shadow-first introduced]

Trigger: enforcement is OFF during trace collection (the scheduler
precedent, adopted uncritically). An attacker acts freely in that
window AND poisons the very traces that decide when to flip.
Consequence: the rollout period is an open door, and the flip gate is
fed attacker-shaped data.
Fix: shadow-first governs ENGINE CHOICE only, never SAFETY. High-risk
side-effecting capabilities (run-adhoc, write-config/policy,
call-paid-engine) enforce deny-by-default from day one, shadow or not;
only taint-vs-quality DENIALS are shadow-measured. Add adversarial
canary tasks to the trace set; isolate trace influence so one caller
cannot dominate the gate.

## FP-3 [HIGH, partially mitigated] Gateway descriptions are untrusted model-visible text

Trigger: a fronted backend's tool NAMES/DESCRIPTIONS (not just
results) render to the model. Verified: TEE already PREFIXES
(`fs.read` never collides with local `read`) and fingerprint-pins the
tool list — so pure rename-impersonation is already refused.
Residual: descriptions can still embed instructions, and a backend
can still claim a persuasive description.
Fix: tool descriptions from a backend are TAINTED text (data, never
instructions — the research-49 posture, extended from results to
schemas); a description is budget-trimmed and quoted, never merged
into TEE's own tool prose; collisions with a LOCAL tool name (not
just another backend) are refused, not just prefixed.

## FP-4 [HIGH] The flip gate is attacker-visible and gameable both ways

Trigger: "flip to enforcing at zero false denials" is a single scalar.
An attacker floods benign traces to force a PREMATURE flip (with blind
spots), or emits false-denial probes to block the flip FOREVER (DoS on
the security rollout itself).
Consequence: the security layer either ships blind or never ships.
Fix: the gate is not one scalar — require coverage thresholds across
capability classes, adversarial canaries passing, a weighted
denial budget, AND an explicit owner sign-off (typed phrase). Rollout
is an owner decision informed by data, never an automatic threshold a
caller can steer.

## FP-5 [MED, = research 63 #1 at graph level] Derived ids launder taint

Trigger: a chore summarizes N tainted inputs into a NEW id; taint
attaches only if the code remembers to set it.
Consequence: a "clean" derived id trusted downstream — laundering by
omission.
Fix: a `derive(parents=[...])` API is the ONLY way to mint an id from
others; it unions parent taint by construction; a directly-constructed
id defaults tainted/unknown; an audit sweep flags orphan ids with no
derivation. Make the safe path the only path.

## The pattern across all five

Every failure is the SAME shape: taint is sound in the model but leaks
at a BOUNDARY the model didn't cover — the thread hop (FP-1), the time
window (FP-2), the schema surface (FP-3), the rollout control (FP-4),
the derivation step (FP-5). The fix is always to make the safe
behavior structural at that boundary (fail-closed context, safety
outside shadow, tainted schemas, multi-signal owner-gated flip,
derive-only id minting) rather than relying on the code to remember.

## What this adds to T-1 acceptance

- a chore invoked from a daemon-thread job sees the taint label (or
  fails closed) — thread-hop fixture;
- high-risk capabilities are denied in SHADOW mode too (only quality
  denials are shadowed) — fixture;
- a backend tool description cannot collide with a LOCAL tool name and
  is treated as tainted quoted data;
- the enforcement flip requires owner typed-phrase sign-off, not a
  scalar threshold;
- a derived id unions parent taint; an orphan id reads back tainted.

## Verdict

The kernel survives the simulation, but only after five boundary
leaks are closed — none fatal, all structural, and one (FP-2) a real
hole that adopting the scheduler's shadow-first pattern would have
shipped. The daemon-thread propagation (FP-1) and the shadow-safety
split (FP-2) are the two that MUST land before any enforcement; the
rest harden it. Folded into T-1; no new campaign.
