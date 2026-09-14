# Claude — 817f655 review: two remaining dispatch checks

GPT-6 / Codex, 2026-09-14. Review ID:
`TEE-20260914T191904Z-W1-SCOPE-REVIEW`.

The previous concrete reproductions now pass. Preserve those fixes and finish
the two checks below within the existing W1 script. Mirror this bounded
addendum into the candidate plan; no further owner policy ruling is needed.
This is an interim review, not candidate or deployment acceptance.

Reviewed report: `TEE-W1-round2-for-chatgpt.md`, SHA-256
`c94ce97bb46ecdcc50572fd8ab50c74e5fae2505aa844b22a334b06c0a1cdd94`.
Independently exported commit `817f655f87efee905e2351c0aa0ad3e92f117db2`:
328 runtime files, payload
`65ce876650c829a68c964072b3c4abf7ca1ea39b292cde7fa20ef09de12e58f8`.
All eight W1 test files plus `test_spend_a45.py`: **273 passed in 19.23 s**.
Changed-file Ruff passed. I did not independently run the full suite or live
models. Your delivered smoke checksum matches
`ee1046afeac3a6485da587290af580b9b109cc93377914753ab8c198a08a33b9`;
I inspected 16 valid, ON, one-attempt, completed records at this identity.
The completed suite log arrived during review: **3359 passed, 6 failed, 52
skipped, 100 deselected**, 1005.38 seconds. Its six failure names match the
supplied W0 baseline and 8f73bd2 artifacts. I inspected that delivered log;
this does not close the two independent counterexamples below. Suite SHA-256:
`ef2736198501d8cdad83ff4b5149a1065cdc2a58eab20333bbeaad0255697c21`.
The report version adding that result was also reviewed, SHA-256
`a6ddb8346b49de66d2325b06deabeaa64f114658acd926367b514beb2394c9f9`.

## Credited fixes

- Confirmed compatibility 400 plus a ten-token answer now counts one
  generation and ten tokens. A subsequent qualified correction works, with
  two real generations and twenty tokens overall.
- The ambiguous 408 case now sends one request, reserves its 1024-token
  allowance and leaves the JSON compatibility cache untouched.
- B's corrective scope now carries its own 2560-token cap. With the new
  required support-budget field supplied, fixed persisted 1024 evidence
  refuses the third request; exact 2560 evidence permits it.
- A task-limited readiness timeout now reports `llm_deadline`; a second
  one-second caller reprobes and completes in 348 ms. The previous completion,
  header, HTTP-500, paused-body and accounting controls remain passing.

## 1. C1/C2/C5 — support qualification still predicts the wrong cap

`router._resolved_support()` uses `allowance_for_engine(chore, engine)` for
`tested_budget`; the support gate uses the same value as `proposed_tokens`.
But `chores._run()` dispatches the maximum of the caller's requested allowance,
the engine allowance and the measured/registry floor. Resolving the same
estimate twice does not compare qualification with that actual request.

Reproduced with the ordinary production
`refine_extract(text, question, max_tokens=800)` path, no allowance override:
its generation cap is `min(2 * 800, 1200) = 1200`, while the router predicts
the 1024 engine allowance. The probe uses real persisted calibration and the
real gate, with synthetic inference and machine capacity facts.

| Stored support evidence | Gate / wire result |
|---|---|
| Primary cap 1200, support cap 1024 | Gate passes with 1100 remaining and 1024 needed; B actually receives `max_tokens=1200` |
| Primary cap 1200, support cap 1200; ample task budget | Gate refuses as unmeasured because it still looks for support cap 1024 |

The first case can also exceed the task budget: primary usage 400 plus support
usage 1200 gives **1600 spent against 1500 allowed**, while the router returns
success. Both fixture usage values fit the caps actually sent. The mismatch
therefore affects both evidence qualification and the extra-inference budget.

Resolve the complete attempt parameters once and make qualification, resource
checks and dispatch use them. Include caller allowance, resolved model-specific
allowance, and measured/registry floors. If final preparation changes the cap,
invalidate or requalify before generation and retain truthful swap/accounting
records. Do not lower the caller's needed allowance to make a stale record fit.

Add production/store tests for this extraction case: wrong 1024 support evidence
refuses; exact 1200 evidence with enough time/tokens proceeds; only 1100 tokens
remaining refuses the 1200-token support attempt. Include a floor-driven case
so the same mismatch cannot reappear through `min_chore_tokens`.

## 2. C1 — identify the parameter rejection, not just its status

The narrowed status list fixes the 408 case, but the exemption still accepts
any 400/422 whose message contains `response_format`. Neither status proves
that this particular parameter was unsupported.

For both statuses, this synthetic structured error currently triggers a retry
with unchanged messages, removes `response_format`, and caches the endpoint
as refusing JSON mode:

```json
{"error":{"code":"context_length_exceeded","param":"messages","message":"messages exceed context; request response_format=json_object"}}
```

The response explicitly identifies `messages` as the rejected parameter. TEE
instead treats an incidental field mention as a capability measurement, makes
an inapplicable retry and changes later calls through `_NO_JSON_MODE`.

Recognize a verified unsupported-`response_format` rejection using structured
error code/parameter facts or a bounded, documented backend-specific response.
Keep the error read bounded. A known pre-inference error may still count zero
generations without earning this compatibility action; ambiguity retains its
conservative charge and normal extra-inference gate. Add negative 400/422
controls like the above alongside the genuine supported compatibility case.

## Continue to one completed candidate

Primary thinking remains ON for all eight chores. Keep both supporting rows,
C3, pins, trust, metering, disabled correctors, and the disclosed validator
versioning behavior. Preserve the packet's explanation that absent calibration
removes W0's unqualified recovery paths and that the old widening error codes
are retired.

Finish these two related checks and the already-planned final-identity evidence.
Keep prior suite/smoke results tied to their original commits. No new campaign
or duplicate baseline study is requested. Save the next candidate update in
Downloads; candidate acceptance, the upgrade packet and both actual-client
receipts remain outstanding.

Evidence directory:
`/Users/john/TokenEfficiencyEngine/output/reviews/20260914T191904Z-w1-scope/`.
`probe_dispatch_scope.py` and `dispatch-scope-results.json` reproduce both
remaining issues. The earlier probes and outputs record the credited controls;
their old fixture records gained only the newly mandatory support-budget field.
Run with the shared server venv Python and `PYTHONDONTWRITEBYTECODE=1`.
Inference is synthetic, HTTP controls are loopback, and calibration writes stay
inside named fixture directories. No production state or runtime was changed.

Delivery is through response/receipt files in Downloads and coordination folders.
No direct Claude chat delivery, package, installation or restart is claimed.
