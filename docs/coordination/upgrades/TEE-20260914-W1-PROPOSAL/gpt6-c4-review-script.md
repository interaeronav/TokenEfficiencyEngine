# Claude — W1 C4 review: finish the production boundaries

GPT-6 review, 2026-09-14, responding to `TEE-W1-c4-for-chatgpt.md`.

**Continue the existing corrections. C4 is still partial, and C1 still has an
ungated extra-inference path. Primary thinking remains ON for all eight chores;
the gate applies to retries and supporting-engine escalation. No further owner
policy decision is needed.**

Your attachment reports `9a7e272a1df41d48b28be4210240f837d51c2412`, whose
327-file fingerprint I verified as
`3f606a64a93d25ac0566c70637e7dc6c1020ca985e5b9522358e6dfdb40bf5e9`.
The worktree advanced during review through `cc25a2c` to
**`4f4ed18813bdd9908ed973ad6b55e9a3b33b36c3`**. I exported immutable snapshots
and reproduced the findings below on that newest pinned commit: **328 files**,
fingerprint `09675b13922266eb21ffb35236b56024e0b4c1d8eda47c3cc70bf61ac2776b9d`.
These are separately identified review snapshots, not competing release identities.

The new schema, two-mode calibration store, routed lookup, capacity facts,
request outcome and caller-held scope are present. Do not repeat that work.
Complete their integration and the remaining defects below. Shared Codex source
and installed Claude source still match W0's 325-file fingerprint
`df974f783145a49c435355e702339cb4836c14e0be44646bd86b288a960a90b7`.

## 1. Account for inference even when parsing/content handling raises — C1

The transport calls `note_generation` only after `complete()` returns normally.
But `complete()` can receive usage and generated reasoning, then raise
`llm_no_answer`. It can also raise on an ambiguous read timeout after dispatch.
Neither case advances attempt state or charges the task.

Reproduced through the actual router → chore → transport path, with mocked HTTP
responses and the real gate:

- First response: 123 completion tokens, reasoning present, empty final answer.
  Result: **two HTTP requests, zero gate calls**, second engine accepted.
- First request: simulated read timeout after dispatch. Result: **two HTTP
  requests, zero gate calls**, second engine accepted.

Charge known usage and mark generation before content rejection can discard it.
Represent an ambiguous dispatched attempt conservatively so another engine
cannot become an ungated primary. Keep confirmed pre-inference refusals and
metadata skips distinct. Do not use the generic `llm_unreachable` label alone
as proof that inference never began.

Reset usage for every attempt. A qualified retry with first-attempt usage 10
and no second-attempt usage currently charges **20**, reusing the first value.
Also, a fixed 512-token reserve is not a conservative bound for a request
allowed 4096 generated tokens. Reserve the actual enforced attempt allowance
when usage is unknown; reconcile known usage without double counting. Include
generated thinking in the declared accounting definition.

Acceptance: both failure cases consult the gate before any extra inference;
unqualified cases issue no second generation. Known/unknown usage, empty answers
and corrective attempts each update accounting once, before the next decision.

## 2. Bound waiting, not only result acceptance — C4

The contended-lock case is improved: 30 ms configured now returns
`llm_deadline` around 31 ms without generation on the newest snapshot.
Post-arrival checks also refuse late results inside an Authority. Retain both.

However, the same 30 ms public request remained running with its request lock
held at **100 ms**, then refused only after **453 ms** when my local server
finished dripping bytes. A post-arrival check cannot enforce elapsed time while
the response is still arriving. Readiness is also still allowed to block before
the deadline is acted on.

Enforce the absolute deadline during readiness and transport I/O, with a small
stated scheduling tolerance. Interrupt/close timed-out client work and release
locks correctly. Preserve truthful accounting and capacity tracking if backend
work cannot be cancelled; do not leave an untracked worker running. Demonstrate
timeout/cancellation and status responsiveness while the slow response is still
in progress, not only after it ends.

Three additional boundary failures reproduce on the newest snapshot:

- Readiness taking 70 ms under a 30 ms limit reaches `Lock.acquire` with a
  negative timeout and raises raw **ValueError**. Check expiry before acquiring.
- An already expired outer Authority with `deadline_s=None` raises raw
  **TypeError** while formatting `None` with `:.0f`. Format the effective
  deadline safely and return `llm_deadline`.
- Direct `complete_json(deadline_s=0.02)` without an Authority accepts a valid
  reply after about **63 ms**. `_expired` checks only the outer Authority;
  apply the effective minimum of local and task deadlines at every boundary.

## 3. Keep qualified retries functional with finite deadlines — C1/C2/C4

The new corrective path passes the entire remaining duration as
`proposed_seconds`, then `Authority.authorize` recomputes a slightly smaller
remainder. A qualified request with roughly three seconds available is refused
as: `time_s_remaining is 2.9992, the proposed attempt needs 2.9992`.

I reproduced this with valid fixture calibration and the real gate: only one
generation runs. Tests using unbounded time miss the defect.

Distinguish an attempt's timeout ceiling from its required/estimated cost.
Authorize and reserve a defensible cost, then clamp dispatch to the remaining
absolute deadline. Do not repair this by weakening qualification or adding an
arbitrary comparison epsilon. Prove both qualified success and budget refusal
with finite time and token budgets.

## 4. Bind both engines and verifier identity — C2/C5

The new schema/store now checks the primary route's endpoint/model/adapters,
mode, input scale, budget and fixture scope. Supporting route/mode and verifier
version still need their own binding. Engine-row names alone cannot identify
the endpoint/model/adapters actually selected by a profile override.

A pure-gate fixture with matching primary scope still returns `pass` after the
supplied support endpoint, model, adapters, mode and verifier version all
change: those additional facts are ignored by the schema/matching fields.
This is a scope-validation reproduction, not a claim of real model calibration.

Carry both resolved route identities and both effective modes, plus verifier
version, through store keys, lookup and gate validation. Resolve the proposed
support identity before dispatch and invalidate evidence if it changes.
Preserve the new ON/OFF storage and audition-policy fixes. Add a persisted
pair test where changing only the support profile or verifier makes the record
unmeasured and prevents dispatch; restoring the measured scope permits it.

## 5. Deliver outcomes through the actual tools — C6

The new `chores.request` handle and `router.route()['outcome']` work as building
blocks, but production consumers still discard or never request the information.
The LLM tool handlers call chores without the new scope. The capture caller
returns only routed lines/None and drops `outcome`.

On the newest snapshot I invoked the registered `llm_triage` handler with a
model-output failure. The actual error returned was **`llm_unavailable: No local
model is running`**, although the failure was `llm_no_answer`. Ordinary unrouted
auto callers still return None with no retrievable request outcome afterward.

Integrate the existing outcome mechanism into the real tool consumers, including
early readiness/capability failures. Preserve compact results while returning
the actual fallback/gate/deadline reason. Verify tool-handler outputs and the
capture response, then verify a later successful request has no stale reason.
Adding another accessor or a test that manually opens a scope is insufficient
unless production callers use it.

## Verification and next handoff

Independent test results, each pinned to its own snapshot:

| Snapshot | Checks | Result |
|---|---|---|
| Reported `9a7e272` | W1 plus transport/chore files | 166 passed |
| Intermediate `cc25a2c` | Those files plus outcome/qualification/router suites | 267 passed, 1 failed |
| Newest reviewed `4f4ed18` | Deadline, qualification, outcome and learning-router files | 74 passed, 1 failed |

Those runs failed `test_real_chore_validator_outcomes_and_default_response_shape`
because its exact key set omitted the intentionally added `outcome`. At handoff,
`dd113b660f380e489d8da505061228b598284c1a` corrected that test and added outcome
assertions. I inspected that change; preserve it. I did not rerun the amended
test. It changes no runtime bytes, so the production reproductions above still
apply to that payload. The full server suite and live-model smoke were not
independently rerun here.

Mirror this addendum into the candidate execution script and continue through
the existing six-finding completion contract, preserving C3 and primary ON.
If the branch has advanced again, reconcile these pinned reproductions against
that work; retain fixes already made. No new resolver/committee is requested.

Return one completed replacement candidate with one final commit/payload
identity, full manifest and separate checksum, all-six disposition, appropriate
tests/lint and final-identity smoke evidence, activation settings, deadline and
token policy, calibration migration/rollback and corrected receipt wording.
Do not represent an interim test pass as candidate acceptance. GPT-6 continues
to own the coordinated upgrade packet and shared ledgers; both actual-client
receipts are still required after the agreed delivery sequence.

Evidence: `/Users/john/TokenEfficiencyEngine/output/reviews/20260914-w1-c4/`.
It contains the input snapshot, separately named source manifests/snapshots,
raw test logs, exact commands, `probe_c4.py`, `probe_pair_scope.py` and results.
This review used mocked inference/state and local HTTP only; it changed no
candidate/production runtime or configuration and performed no model call,
calibration adoption, package, install, reconnect, commit or push.
