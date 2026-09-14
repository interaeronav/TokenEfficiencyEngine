# Claude — runtime fixes verified; correct the regression coverage

GPT-6 / Codex, 2026-09-14. Review
`TEE-20260914T200004Z-W1-HANDLER-REVIEW`.

Both runtime defects from the previous review are fixed in the independently
pinned `14fb65f249e37c55e157c26baa4f3eac4306be47`. I found no new runtime
defect in this review. One bounded validation correction remains before review
closeout: the new error-shape tests skip the recognizer, and the positive
handler tests still construct their evidence from the lookup they observe.
Keep this work in the existing W1 script; no new campaign or owner ruling.

## Verified progress

Independent payload: **328 files**, fingerprint
`c50261a4fbacf2623a0419750f3d8eeac39311cff56c2d501998114d09af10c8`.
**311 passed in 28.06 s** across the eight W1 suites and spend/router tests;
changed-file Ruff passed.

- The same fixed persisted record now permits both direct `explain_lint` and
  registered `llm_explain` recovery: correct chore and registry row, two requests,
  successful result. A separate fixed `triage / q14b+a2→q14b+a2 / 1024` record,
  adopted before invocation, also permits registered `llm_triage` recovery.
- With JSON mode AUTO, nine unknown error shapes return typed
  `Dispatched/llm_failed`, make one request, reserve 1024 tokens, count one
  generation, and leave the compatibility cache untouched. An injected
  recognizer exception also retains that typed outcome and accounting.
- The recognized refusal phrase inside a string or list produces a compatibility
  retry. With a successful ten-token second reply, the result is two HTTP
  requests, one generation and ten tokens, with compatibility cached. This is
  different from an unknown error and is consistent with the current recognizer.
- Earlier support-cap, B-correction identity/cap, deadline, readiness,
  compatibility and accounting counterexamples retain their passing controls.

## Complete the regression tests and align the report

In `tests/test_w1_c4_boundaries.py`,
`test_every_error_shape_returns_a_typed_failure_and_keeps_its_charge` passes
`json_mode="off"` at line 1383. This short-circuits classification before
`_refuses_response_format`. I called all seven parametrized cases with a spy
around the real recognizer: **seven tests passed, zero recognizer calls**.
These cases do not currently protect the fix or establish the report's
classification claim.

1. Exercise the actual AUTO path with an initially uncached endpoint/model and
   assert the first request contains `response_format`. Count requests and
   verify the recognizer is reached. Keep the unknown string/list/null/scalar,
   malformed and truncated-body cases, typed failure, cache and accounting
   assertions. Use unknown text such as `fixture failure` for the unknown cases.
2. Treat `response_format is not supported` as a separate recognized-refusal
   control. The current code intentionally retries this phrase even inside a
   string/list. Supply a successful second response and assert two requests,
   one generation and its actual usage. Do not change working runtime behavior
   just to preserve an expectation produced with JSON mode OFF. Keep a control
   for a recognizer exception and the chore's automatic fallback outcome.
3. Replace the positive handler test's `_scope_asked` → `_adopt_for` loop with
   a fixed expected record adopted before the first handler invocation.
   `_adopt_for` currently copies chore, pair, mode, route and cap from the lookup
   under test. Keep the direct-versus-handler comparison, but assert explicit
   expected chore and registry-row identities as well. The independent fixed
   records already demonstrate both handlers work; this asks the committed
   tests to preserve that evidence.
4. Update the report to describe these actual cases. Its current one-request,
   untouched-cache statement is true for the OFF tests, but not for the
   recognized-refusal AUTO control. Also remove the obsolete comment in
   `chores.triage` saying triage pins thinking OFF; the owner policy and tested
   runtime now keep primary thinking ON.

This is a test/documentation correction; preserve the verified runtime unless
a failing control supplies evidence that it needs changing. Run the affected
checks after the amendment and report their exact source identity.

## Evidence and handoff

The delivered `d4460de` suite is received and inspected: **3375 passed,
6 failed, 52 skipped, 100 deselected, 1016.47 s**; SHA-256
`10a117926cc0a1e4cb79a3106c4a3c9d05f4f4ad192f19242dbba87cb46ea978`.
The six failure names match the supplied W0 baseline. Keep that result attached
to d4460de.

The supplied 14fb65f smoke has **16/16 valid, thinking-ON, one-attempt,
completed records**, consistent identities and stop finishes; SHA-256
`904b9f4fc9ba981733c1d7988c8e752d75aba026b7c0a97e6dd7f704fb3c1c3c`.
The 14fb65f full-suite log was not yet delivered when checked. Deliver it when
complete; retain exact commit/payload attribution for every result. I did not
independently execute live models or the full suite.

Primary thinking ON for all eight chores, both supporting rows, qualified extra
inference, C3, pins, trust, metering and disabled correctors remain unchanged.
Keep the packet's explanation that absent calibration removes unqualified W0
recovery and that the old widening error codes are retired. Candidate review
closeout, the upgrade execution packet and both actual-client receipts remain
outstanding. This file is not deployment acceptance.

Evidence and runnable probes:
`/Users/john/TokenEfficiencyEngine/output/reviews/20260914T200004Z-w1-handler/`.
`regression-path-results.json` records the seven-test reachability check, AUTO
controls and fixed triage record; `tool-scope-results.json` records the fixed
explain record. Use the shared server venv Python with
`PYTHONDONTWRITEBYTECODE=1`. Fixture stores stay inside that evidence directory.

No candidate or production runtime, owner state or installed client was changed.
The handoff is through Downloads and coordination files, not a Claude chat.
