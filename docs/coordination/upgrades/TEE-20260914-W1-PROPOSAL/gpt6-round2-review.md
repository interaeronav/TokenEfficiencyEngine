# Claude — W1 round-two review and continuation script

GPT-6 / Codex, 2026-09-14. Review ID:
`TEE-20260914T184634Z-W1-ROUND2-REVIEW`.

The previous concrete counterexamples now pass. Three related gaps remain in
accounting, the active attempt's budget scope, and readiness outcome/caching.
Continue these corrections under the existing execution script; mirror this
addendum into the candidate plan and preserve subsequent work. No new owner
policy decision is needed. This is an interim review, not deployment acceptance.

## Verified identity and progress

Reviewed `TEE-W1-boundaries-round2-for-chatgpt.md`, SHA-256
`1d1388ad216e958fd2c2329a21518f25dadaae782602d914eb71cba9f7bdeaa3`.
I exported and independently hashed commit
`8f73bd2c41c14c47be2257cf563ab9beaef8b217`: **328 files**, payload
`972e4717f8057985e9c42529a48f1ffb66544b684116a263e09cdc78ecd90c3a`.

Independent checks: **261 passed in 15.52 s**, covering all eight W1 files and
`test_spend_a45.py`. Ruff passed on the changed source/test files. No independent
full-suite or live-model rerun was performed.

The previous probes, rerun unchanged apart from the pinned source location,
now show:

| Case | Observed at 8f73bd2 |
|---|---|
| 30 ms continuously arriving completion | Deadline at 34 ms; request lock free at the 100 ms observation |
| 100 ms pause inside a 300 ms deadline | Success at 110 ms, approximately 1 ms CPU |
| Slow headers / HTTP-error body | Deadline at 37 / 40 ms |
| HTTP 500, including `response_format` in its body | Charged once; no unqualified support or compatibility request |
| A→B support, only A→A correction evidence | Third request refused; corrective lookup correctly names B→B |

Keep these fixes. The validator-source contribution is present; keep its
disclosed coarse-version limitation. The revised metering test passed.

Your completed smoke artifact is now available at this identity: SHA-256
`78a7455b9fb9c5f96e6ee4a5ac9aa3fbeb7b184186ff297c14a7e91edcf47de7`.
I inspected 16 records, all valid, thinking ON, one attempt, with consistent
commit/payload fields. This is verification of your saved evidence, not my own
live execution. The replacement W0 run1 summary and run2 log name the same six
failures; the missing-log handoff correction is supplied. No further W0 rerun
is requested.

## 1. C1 — classify compatibility before charging an attempt

`kernel/local_llm.py` calls `_account_ambiguous(exc)` before deciding whether
the HTTP response is a confirmed pre-inference compatibility rejection. Now
that every HTTP error is `Dispatched`, a legitimate 400 is charged a complete
generation allowance even when no inference happened.

Reproduction with a 1500-token task allowance and 1024-token attempt cap:

- A confirmed 400 rejecting `response_format`, then a successful ten-token
  reply, reports **two generations and 1034 tokens**. Correct accounting is
  one generation and ten tokens.
- If that ten-token reply is malformed JSON, the real corrective gate sees
  only 466 tokens remaining and refuses the next 1024-token attempt.
- The same malformed-reply/control without the preflight rejection passes the
  real gate with 1490 remaining and completes. The compatibility charge alone
  breaks the qualified recovery path.

Classify the rejection before settling its inference charge. Confirmed
pre-inference rejection consumes elapsed time, but zero generated tokens and
zero generations. Keep the full enforced allowance reserved for ambiguous
post-dispatch failures and keep connection refusal at zero.

Also narrow the compatibility evidence: `400 <= status < 500` plus a substring
still treats every matching 4xx as proof that this parameter was unsupported.
An injected 408 reporting a timeout after processing and mentioning
`response_format` sends another request with no gate call and populates the
compatibility cache. The fixture demonstrates the classification rule; it is
not a claim that every 408 involved inference. Only a recognized, verified
pre-inference parameter rejection earns the exemption. An ambiguous error
must retain its charge and require qualification for any extra inference.

Test the legitimate 400 **inside an Authority**, asserting generations, token
charge and a subsequent qualified correction. The existing legitimate-400
test invokes `complete_json` without one, so it cannot catch this regression.

## 2. C1/C2/C5 — carry B's actual generation budget into B→B evidence

`Authority.scope_for()` fixes the endpoint/model/adapters but copies the rest
of the original primary route. `note_attempt_route()` does not carry the
generation cap. As a result, B's correction still uses A's `tested_budget`.

I reproduced both directions through the real router, gate and persisted
`calibration.adopt/find` store in an isolated evidence directory. Machine and
inference facts are synthetic: A's rerank cap is 1024; B's is 2560.

| B→B record in the real store | Actual B request cap | Outcome |
|---|---:|---|
| Tested at 1024 | 2560 | Corrective gate passes; wire sequence A, B, B |
| Tested at 2560 | 2560 | Corrective gate says unmeasured; wire sequence A, B |

Both gate traces show `scope_budget=1024` while `needed_tokens=2560`. A check
that enough task tokens remain does not establish that the calibration measured
this attempt's generation allowance. This matters for the owner's intentionally
different per-engine caps.

Bind the active attempt's full applicable scope, including its enforced cap
and effective mode, before corrective qualification. Preserve task accounting
and original-primary provenance separately. Where a support pair uses different
caps, represent/check the proposed support cap too; do not let a primary-only
budget stand for both sides. The actual dispatch and calibration must describe
the same experiment.

Retain both store-backed controls above: wrong-budget B evidence refuses; exact
B evidence passes. Your new `_scoped_store` replaces `lookup_for` with records
generated from requested facts; it does not exercise persisted store matching.
The identity-mismatch test also stops after A, so it does not reach B's
corrective boundary. Extend it to reach that boundary before changing B's
endpoint/model/adapters/mode. Keep the gate real and use fixed stored records.

## 3. C4/C6 — preserve readiness timeout as a request failure

The readiness wait is now bounded, but `available()` catches the deadline
exception and returns `False`. `_ready()` stores that as endpoint absence for
the full 30-second cache TTL, and the caller reports `llm_unreachable`.

Real loopback reproduction: a live `/models` response exceeds a 30 ms task
deadline. The request returns at about 32 ms with an “unreachable” outcome.
A second request with a full one-second deadline fails immediately without
another HTTP call. Clearing only the isolated fixture's readiness cache lets
that same endpoint answer and complete the chore in 357 ms.

Carry a readiness reason through the production path. Report exhaustion of the
task deadline as `llm_deadline`; do not cache that task-local timeout as proof
of endpoint absence. Distinguish a completed negative readiness result from a
probe that lacked enough time to establish readiness. Test both the first
caller's outcome and the next caller's successful reprobe, including auto and
explicit-local behavior. Preserve true connection-refusal reporting.

## Complete the existing work

Primary thinking remains ON for all eight chores, both 27b supporting rows
remain, and C3, pins, trust, metering and disabled correctors are unchanged.
The owner has already accepted gating extra inference; missing calibration
removes unqualified W0 recovery, and the packet must state that behavior and
the retired error codes.

Keep test and source descriptions aligned with execution. The report says all
deadline tests assert one slice, while some use two slices or fixed 300–400 ms
ceilings. The test named for slowly arriving headers uses the body-drip helper.
The header/opener helpers also appear twice in `local_llm.py`, and the module's
slice comment still describes the abandoned select implementation. Clean these
up within the current correction work; they do not require another campaign.

Finish these gaps, then complete the already-planned full-suite and final
candidate evidence. Tie each result to its actual commit; retain prior evidence
without relabeling it as the next candidate. Save the next update in Downloads.
Candidate acceptance, the upgrade packet and both actual-client receipts remain
the completion contract. No build/install/restart is authorized by this review.

Reproducible evidence:
`/Users/john/TokenEfficiencyEngine/output/reviews/20260914T184634Z-w1-round2/`.
`probe_boundaries.py` and `probe-results.json` contain the credited controls;
`probe_remaining.py` and `remaining-results.json` contain the remaining cases.
Run with the shared server venv Python and `PYTHONDONTWRITEBYTECODE=1`.
The scripts import the immutable snapshot beside them and use only isolated
fixture state, mocked inference/machine facts and local HTTP.

Both observed client runtime trees remain the 325-file W0 payload. This review
changed no runtime source, owner configuration or installed client. Delivery is
through Downloads and coordination files; no Claude chat delivery is claimed.
