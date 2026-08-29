# A39 build script — the router: AI resource management, made real

**What this builds** (owner directive, 2026-08-29): the adaptive
cloud↔local router from `docs/research/55-cloud-local-routing.md` —
the design of record; read it first. Mission context: A39 formalized
the two-pillar identity (make every exchange small; run work on the
cheapest capable engine). Inherits every standing law by reference
(A33 rules; surface LAW 2,028/17; bars incl. gateway 95.4 and
fabrication 92.4 as the floor; A30/A31; fakes first; revert on
regression; owner-only decisions; >2 GB gate; never concurrent with
another campaign).

A one-paste prompt for a fresh session:

> Read CLAUDE.md, then CLAUDE_A39_SCRIPT.md, then research doc 55,
> then the last dated entries of docs/PROGRESS.md. Call tee_status and
> tee_recall first and use TEE's own tools as co-pilot throughout.
> Work the phases in order from where the evidence says they stand —
> verifiers before confidence, calibration before gates, benchmarks
> before claims. Stop and report if any phase's premise no longer
> holds.

## Router laws (from research 55, non-negotiable)

- TEE never calls a cloud API. "Escalate to cloud" = return the task
  to the CLIENT with a budgeted brief and the named local failure.
- An explicit owner switch (TEE/Q14B / TEE/Q27B) outranks the router:
  routing happens WITHIN the owner's chosen ceiling, never above it.
- The single-occupancy law outranks routing ambition: no engine swap
  is triggered for routing (route around residency, never thrash).
- No silent hops: provenance names who did the work and what the
  verifier said; escalation rate joins report_savings.
- Uncalibrated confidence never gates anything: chores without a
  deterministic verifier stay statically routed until R3's
  calibration rows exist and pass.

## R0 — The routing dataset (measure before policy)

Assemble from what already exists (trap suites, graded fixtures,
probe tables, S0/S4 latency rows): per chore × engine (q14b+a2,
q27b-bare, client-brief) — verified quality, latency, server-side
token cost, plus input-size sensitivity on a spread of fixture sizes.
Add the mixed-difficulty chore set for the R4 benchmark (easy/medium/
hard per chore, difficulty assigned by the verifiers, not by feel).
Suites green as the entry ticket; ledger as a dated PROGRESS table.

## R1 — Verifier-gated cascade (the deterministic core)

For chores WITH deterministic verifiers (extract verification, schema
validation, lint ground truth, triage trap-style checks): local
default engine → verifier → on fail, the residency-aware ladder
(bigger local ONLY if resident → client-brief return). The
escalation brief is a budgeted TEE response: the task, the input
pointer, the local attempt's named failure — never the raw content
re-dumped. Fakes first (a fake engine that fails on cue); fixtures
for every hop incl. the never-swap rule and the owner-ceiling rule.
Acceptance: cascade contract green on fakes; live spot-run recorded.

## R2 — Accounting and visibility

report_savings gains per-engine spend and escalation rate; provenance
stamps carry engine + verifier verdict per hop; `tee_status` recap
shows the active policy in one line. Router overhead measured per
call and published next to the gateway's honest-cost paragraph.
Acceptance: fixtures + one live session whose meter output shows the
new columns.

## R3 — Calibration for the unverifiable (measured, maybe shipped)

For chores with no deterministic verifier: measure abstention/self-
rating calibration on held-out fixtures (UCCI-lesson: raw confidence
lies). Ship a confidence gate ONLY where calibration rows pass a
stated threshold; otherwise record "stays static" per chore with the
numbers. This phase is allowed to conclude "none ship" — that is a
finding, not a failure.

## R4 — The benchmark decides

The routing scenario, research-48 style: the mixed-difficulty set,
four arms — all-q14b, all-q27b, all-client, ROUTED — measuring
client tokens, wall time, verified quality, escalation rate. The
routed arm must dominate or the router reverts (the bars are the
floor; the router must EARN its complexity). Append to RESULTS.md;
the README claims only what the row shows.

## R5 — Close-out

Full battery (all bars + the routing row); suites + CI green; docs
(setup-local-llm gains the router section; the two-pillar README
paragraph gets its measured number); artifacts rebuilt + rehearsed;
campaign ledger with wrong-way numbers explained; report_savings
quoted on the closing session; `tee_remember` the close-out. Version
recommendation by semver (expected 0.6.0); the tag stays the owner's
step.
