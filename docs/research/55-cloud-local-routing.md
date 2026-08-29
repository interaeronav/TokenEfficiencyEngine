# 55 — AI resource management: routing work between cloud and local intelligence (2026-08-29)

Verification basis: open-web survey 2026-08-29 (sources inline; the
freshest primary read performed through `tee_web_lookup`); TEE's own
measured data (chore latency/trap/graded rows, probe tables, the
switch lifecycle); the owner's mission observation, verbatim: "the
mission and objective of TEE is slowly becoming an AI resource
management between cloud ai and local ai."

## The observation, tested against the evidence

True, with one correction. Since A34, every major feature has been a
placement decision: web pages, images and audio processed locally
into ~500-token briefs; tracebacks triaged and searches reranked by a
local engine at zero API cost; llm_switch as verified memory
management of local models; report_savings as the accounting; the
gateway as rationing of the client's scarce context. The correction:
the ORIGINAL pillar still carries half the product — the 90%+ DCC
savings involve no local AI at all. The honest identity is **two
pillars**: (1) make every exchange small; (2) run work on the
cheapest capable engine. Recorded as A39.

## What the field knows (2026 state of the art)

- **Cascades work.** Cheap-model-first with confidence-gated
  escalation: FrugalGPT reported up to 98% cost reduction preserving
  accuracy; RouteLLM's learned routers ~85% cost cut at 95% of the
  strong model's quality.
- **The freshest result** (read via tee_web_lookup, arXiv 2606.27457,
  June 2026): a two-stage cluster→route→escalate cascade retains
  **97–99% of the strongest model's accuracy**, tuned by one
  interpretable budget hyperparameter, and — the load-bearing line —
  "requires only task-correctness labels."
- **Calibration is the hard part**: UCCI-class work exists precisely
  because raw model confidence lies; calibrated error probabilities
  are what make cost-optimal cascades safe.

## Why TEE is unusually well placed

1. **TEE has real correctness labels, not vibes.** The chores already
   ship deterministic verifiers: extractive-by-verification (string
   check), schema validation, the trap suites, lint ground truth.
   Verify-then-escalate beats confidence-guessing wherever a verifier
   exists — TEE can run the literature's cascade with its strongest
   known signal class.
2. **The cloud tier costs TEE nothing to "call."** TEE never holds
   cloud API keys. Escalation in TEE's shape = handing the task BACK
   to the client model with a compact prepared brief — the client IS
   the cloud engine, and it only spends tokens on the cases the local
   tier provably failed. The cascade's expensive tier is the
   conversation itself.
3. **The engine pool and its physics are already managed**: q14b/q27b
   profiles, single-occupancy lifecycle, residency awareness — the
   router must respect switch costs (a 51 GB swap is never worth one
   chore) and the memory guard, all already built and tested.

## The design in one paragraph

A router policy over (chore, input size, engines-and-residency,
verifier availability): local-default engine first; deterministic
verifier gates the result; on failure, escalate along the ladder —
bigger local engine ONLY if resident (never thrash the swap for one
task), else return-to-client with the compact brief and the failure
named. Every hop recorded in provenance (who did the work, what the
verifier said) and in report_savings (per-engine spend, escalation
rate). Where no deterministic verifier exists, no silent confidence
guessing: measured calibration first (abstention-rate fixtures), and
until calibrated, those chores stay statically routed. One
interpretable budget knob, per the 2606.27457 lesson.

## Risks and their gates

- **Miscalibrated confidence** → deterministic verifiers first;
  uncalibrated chores stay static; calibration measured before any
  confidence gate ships.
- **The router burning what it saves** → routing overhead measured
  per call and published (the gateway-overhead precedent); the
  escalation brief is budgeted like every TEE response.
- **Swap thrashing** → residency-aware ladder; the single-occupancy
  law outranks routing ambition.
- **Silent quality drift** → escalation rate joins the meter; a
  rising rate is a visible alarm, not a hidden cost.
- **Scope** → the router routes CHORES (server-side work). It never
  redirects the client's own conversation, never calls cloud APIs,
  and never overrides an explicit TEE/Q switch (owner intent wins).

## Verdict

Formalize the two-pillar mission (A39) and build the router as the
next campaign: TEE has the labels, the engine pool, the accounting,
and the escalation tier (the client) already in place — the field's
97–99%-at-fraction-of-cost results were achieved with weaker signals
than TEE's verifiers. Benchmark shape: mixed-difficulty chore set,
four arms (all-14B, all-27B, all-client, routed), tokens + wall +
verified quality.

Sources: arXiv 2606.27457 (Cluster, Route, Escalate — read via
tee_web_lookup), RouteLLM and FrugalGPT results as surveyed in the
2026 routing literature (neuraltrust.ai/blog/llm-model-routing,
truefoundry.com/blog/llm-routing-cost-quality-aware-model-selection),
arXiv 2605.18796 (UCCI, calibrated cascade routing).
