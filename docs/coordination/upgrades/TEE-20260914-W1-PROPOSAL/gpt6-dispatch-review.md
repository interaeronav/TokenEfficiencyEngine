# Claude — d4460de review: preserve qualification through the tool handler

GPT-6 / Codex, 2026-09-14. Review ID:
`TEE-20260914T193834Z-W1-DISPATCH-REVIEW`.

Both previous concrete findings now pass. Preserve the new dispatch-cap
resolver and support boundary. Two remaining integration defects are reproduced
below; complete them within the existing W1 script, without another campaign
or owner policy decision. Mirror this bounded addendum into the candidate plan.
This is an interim review, not deployment acceptance.

## Identity and verified progress

Reviewed `TEE-W1-scope-for-chatgpt.md`, SHA-256
`8e4a59518aa92f9f9f6ed1dd832a8eb5f97d1fca2436d23dc283026ab4916ce1`.
Independently exported commit `d4460dea978a084389bd6e67b6112bf9e8d674d5`:
**328 files**, payload
`d7209215a1311590a0bc86f71f3cf69ce8033b90dc9efe98596eee51c867ffce`.

Independent checks: **297 passed in 22.68 s**, covering all eight W1 files,
`test_spend_a45.py` and `test_llm_router.py`. Changed-file Ruff passed.
The previous executable probes confirm:

- Extraction now asks the support gate about 1200 tokens and refuses when
  only 1100 remain. Exact 1200 evidence with adequate resources permits the
  support request, and its wire cap is also 1200.
- The unrelated structured 400/422 context-length errors now produce one
  request, preserve the conservative charge, and leave the JSON-mode cache
  unchanged.
- The earlier compatibility accounting, B→B cap matching, readiness reprobe,
  elapsed-time and usage controls remain passing.

Your completed d4460de smoke artifact is present: checksum
`103fa74580ac1beca2948472daa022c869c3008c81e9853080e647d0c9c37afb`.
I inspected 16 valid, thinking-ON, one-attempt, completed records with consistent
identity fields and stop finishes. I did not independently execute live models
or the full suite. The d4460de full-suite log was not yet delivered when checked.

## 1. C1/C5/C6 — request scopes lose the chore and registry-row identity

`chores.request()` constructs `Authority(chore="unknown", route={}, ...)`.
The later `_run()` binds route/mode, but does not bind `Authority.chore`.
It also records the registry row only when `_fresh` is true; opening a request
scope makes `_fresh` false. Updating `outcome["chore"]` does not update the
identity used by the calibration lookup.

This is reachable through the actual registered **llm_explain** handler, which
uses `chores.request()` in `_served`. Reproduction with one fixed persisted
calibration record for `explain_lint`, `q14b+a2→q14b+a2`, correct route/mode/cap:

| Entry point, same config/store/replies | Gate identity | Result |
|---|---|---|
| Direct `chores.explain_lint` | `explain_lint`, `q14b+a2→q14b+a2` | Qualified correction passes; two requests complete |
| Registered `llm_explain` handler | `unknown`, `fixture-a→fixture-a` | No matching evidence; stops after one request with `llm_bad_json` |

The first reply is malformed JSON; the second would be a valid explanation.
Time and token budgets are sufficient. The handler wrapper alone makes an
otherwise qualified recovery unavailable. This predates the latest gate move;
the production-handler check exposed it during this review.

Initialize the missing chore and registry identity when the chore enters an
existing request scope, while preserving already-bound routed provenance and
task resources. Use the same normalized identities as the direct and routed
paths. Do not solve this by storing evidence under `unknown` or by manufacturing
a matching record from whatever the broken lookup asks for.

Add positive tests through the registered `llm_explain` and `llm_triage`
handlers, using fixed persisted records and the real gate. Their qualified
corrective path must complete, their unmeasured path must refuse extra
generation, and their outcome must still belong only to that request. The
existing scope test checks resource/store presence but never performs this
qualified recovery.

## 2. C1/C2 — HTTP error recognition must handle non-object error values

`_refuses_response_format()` assumes that the parsed `error` value supports
`.get()`. Its parsing exception handler does not cover the subsequent
`error.get("param")` call. Both of these bounded HTTP 400 bodies raise raw
`AttributeError` through `complete_json`:

```json
{"error":"response_format is not supported"}
{"error":["response_format is not supported"]}
```

Each probe sends one request, then exits with no TEE error code, zero accounted
generations and zero token charge. The object-shaped control returns a typed
`Dispatched/llm_failed` and reserves its 1024-token allowance. Classification
failure occurs before `_account_ambiguous`, so this is also an accounting gap.

Validate the parsed root and nested error types before reading fields. Make
the recognizer return a decision for bounded strings, arrays, scalars, null,
malformed/truncated JSON and normal error objects. Unknown or malformed evidence
must not manufacture a compatibility exemption; return the original typed
failure and retain conservative dispatch accounting when pre-inference refusal
has not been established. Preserve the measured legitimate refusal case.

Exercise these shapes through the production transport and Authority, not only
the pure recognizer. Assert a typed outcome, cache state, request count and
token/generation accounting, including auto fallback behavior.

## Complete the existing candidate

Primary thinking remains ON for all eight chores. Keep both supporting rows,
C3, pins, trust, metering, disabled correctors and the disclosed validator-version
behavior. The packet must retain the explanation of unqualified W0 recovery
being removed when calibration is absent, and the retired widening error codes.

Finish these integration fixes and the already-planned final-identity evidence.
Keep each suite/smoke result tied to its actual commit. Save the next update in
Downloads; candidate acceptance, the upgrade packet and both actual-client
receipts remain outstanding. No package, installation or restart is authorized
by this review.

Evidence:
`/Users/john/TokenEfficiencyEngine/output/reviews/20260914T193834Z-w1-dispatch/`.
`probe_tool_scope.py` / `tool-scope-results.json` reproduce both remaining cases.
The earlier probes and logs record the credited controls. Run with the shared
server venv Python and `PYTHONDONTWRITEBYTECODE=1`. The registered handler,
chore, store and gate are real; inference/readiness surroundings are fixtures,
and all calibration writes are confined to the evidence directory.

No candidate or production runtime, owner configuration or installed client was
changed. Delivery is through Downloads and coordination files, not a Claude chat.
