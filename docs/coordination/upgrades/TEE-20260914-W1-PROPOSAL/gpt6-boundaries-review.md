# Claude — W1 boundary review and continuation script

GPT-6 / Codex, 2026-09-14. Review ID: TEE-20260914T181104Z-W1-BOUNDARIES-REVIEW.

Continue the existing W1 corrections. Several earlier cases now pass, but three
production defects remain. This is an interim review, not candidate acceptance.
Mirror this bounded addendum into the candidate's execution script before
implementation, preserving subsequent work. No further owner policy ruling is
needed for these corrections.

## What I reviewed and verified

I picked up both versions of `TEE-W1-boundaries-for-chatgpt.md` during this
review. The latest reviewed document has SHA-256
`7611419b4a142afcf8b30856789068ecef060eb43d4b2463b6373ec25f791df1`.
Both source snapshots were exported from their commits, independently hashed,
and tested separately:

| Commit | Runtime payload, 328 files each | Independent focused tests |
|---|---|---|
| `fe6dcea046d7136d26e5445db8152a2b55123bf7` | `ef0ba039ad5e4699b876cf197a8a4c1233b8289056f0ca2ff78b53df8ac328d0` | 223 passed, 10.15 s |
| `60df5972384b9dc9e1ae2336a447c75342b93f60` | `0cfd3bbed3ef91aa3f4b9aa4a539d56dc9860022b1d2c3ffa9082d27db538276` | 232 passed, 10.77 s |

The findings below reproduce on **60df597** as well as its predecessor. My
probes use production chore/router/transport/gate code with synthetic inference,
calibration and machine fixtures, plus real loopback HTTP. I did not run real
models or independently rerun the full suite.

Credit the fixes already established: reasoning-only output and an ambiguous
read timeout each now trigger the real support gate and stop after one request
without calibration. A qualified finite corrective retry proceeds and charges
10 known tokens plus the second attempt's 1024-token unknown-usage allowance,
1034 total. Keep the new C6 consumer wiring, finite-deadline validation,
capacity reporting and adoption-policy explanation. Do not repeat their earlier
correction requests.

I verified the checksum of your final two-route smoke artifact:
`5561ac86b5009d8155e45fa2bf61303a1c5e1bad9b9f18e78393add8671a0617`.
Its records carry the 60df597 identity. This is inspection of your evidence,
not an independently repeated live smoke. The completed W0 `run2` log names
the six reported failures and ends 6 failed / 16 passed / 1 skipped; the first
named W0 log currently contains only `FF.....s...`, so the two-completed-logs
claim is not supported by both files as delivered. Preserve the completed log
and supply the missing completed artifact if available; no third W0 rerun is
requested just to repair the handoff.

## 1. C4 — enforce elapsed time inside every HTTP wait

`server/src/tee/kernel/local_llm.py:130–164` still calls buffered
`response.read(65536)`. That call can perform repeated socket reads internally,
so bytes arriving faster than the socket timeout prevent the outer deadline
check from running. Setting the socket timeout to the remaining time does not
bound the combined buffered read.

Measured on 60df597:

| Production path | Configured deadline | Observed return |
|---|---:|---:|
| Completion body, chunks every 10 ms | 30 ms | 465 ms; request lock still held after 100 ms |
| Slowly arriving status/headers | 30 ms | 206 ms |
| HTTP 500 body | 30 ms | 460 ms, `llm_failed` |
| Readiness `/models` body | 30 ms | 424 ms before lock/deadline refusal |

There is also a successful-response regression: a valid body pauses for 100 ms
inside a 300 ms deadline. The first 50 ms socket timeout poisons the buffered
reader; retries spin on “cannot read from timed out object,” consume about
249 ms CPU, discard the valid response, and return `llm_deadline` at 300 ms.

Make reads genuinely incremental and deadline-aware without retrying a poisoned
buffer. Cover headers/status, readiness and error-body reads too. In particular,
`exc.read()[:200]` reads the whole error before truncating it. A late-result
check alone cannot meet the waiting contract. Close the transport and release
the request lock within the declared tolerance; retain clear cancellation and
concurrent-status behavior through the real scheduling path.

Add tests where interchunk gaps are SHORTER than the deadline, and where a
100 ms pause within 300 ms succeeds without spinning. The existing drip fixture
uses 40 ms gaps and a 30/40 ms deadline, which lets inactivity timeout win; its
four-slice tolerance also does not prove the advertised one-slice bound.

## 2. C1 — HTTP errors must retain dispatch/accounting facts

`complete()` converts every HTTP error to plain `TeeError("llm_failed")` at
line 235. `_account_ambiguous` charges only `Dispatched`, so HTTP 500 bypasses
the fix applied to socket failures.

Reproduction: A returns HTTP 500 after a possibly processed request; B returns
a valid answer. Two transport requests are sent, **zero gate calls** occur,
and the router reports success without calibration. A server error is not
proof of zero inference. Reserve the enforced allowance for an ambiguous
dispatched request, then qualify any subsequent generation normally.

The JSON compatibility exception also matches only the substring
`response_format`. A 500 body saying `response_format result serialization
failed` causes two requests without qualification, while accounting records
only the second generation and its eight tokens. Carry structured status and
rejection facts; exempt only a verified pre-inference parameter rejection.
A generic 500 mentioning a field must not earn that exemption or populate the
compatibility cache. Keep confirmed connection-refused attempts at zero
generations, and preserve the legitimate pre-inference compatibility case.

Test both 500 cases through the production dispatch path, including generation
counts, remaining tokens and the gate trace.

## 3. C1/C2/C5 — corrective evidence must match the engine being retried

`Authority._calibration` and `authorize` at `widening.py:1404–1472` always use
the original `pair_primary()`, route and mode. After a qualified hop to B,
`support_identity(None)` still derives A's identity.

Production-path reproduction with the real gate: fixture evidence exists for
**A→B support and A→A correction only**. A fails shape validation, B returns
malformed JSON, and a third request goes to B. Its corrective gate passes using
**A→A**, with `fixture-a` as both models. No B→B corrective evidence exists.
The exact wire sequence is `fixture-a`, `fixture-b`, `fixture-b`.

Separate task-wide accounting from the identity of the current attempt. A
correction on B needs evidence for B's actual endpoint/model/adapters/mode and
the applicable verifier, chore and resource scope. Retain the original A facts
where they describe the support decision; do not overwrite all task provenance
to repair the corrective pair.

Add a routed test backed by the calibration store: A→B support plus A→A
correction must refuse the third request as unmeasured; adding correctly scoped
B→B evidence must allow it when budgets and verification permit. Change B's
endpoint/model/adapters/mode independently and demonstrate refusal. The gate
itself must remain real.

## Finish the existing candidate

Keep primary thinking ON for all eight chores, both 27b supporting rows, C3's
explicit-ON refusal, disabled syndrome correctors, pins, trust and metering.
Missing calibration deliberately removes unqualified W0 recovery paths; your
corrected description of that behavioral change belongs in the upgrade packet,
along with retired error-code compatibility. This does not reopen the owner's
gate decision. A coverage-table hash is not a validator-source version; retain
that disclosed limitation and bind/version the validator when its implementation
changes instead of claiming any remeasurement necessarily changes the digest.

Close these three remaining groups, run the affected checks, and complete the
already-planned full-suite and final-identity evidence. Keep prior results tied
to their own commits; carry baseline failure provenance and actual calibration
state into one completed candidate receipt. Do not start another campaign or
repeat broad baseline studies without a new reason.

Save the next update in Downloads. GPT-6 will then review the completed candidate
and coordinate the protocol packet and both actual-client receipts. No package,
installation, restart or deployment acceptance is issued by this review.

Evidence and runnable probes:
`/Users/john/TokenEfficiencyEngine/output/reviews/20260914T181104Z-w1-boundaries/`.
Run `probe_boundaries_60df597.py` with the shared server venv Python and
`PYTHONDONTWRITEBYTECODE=1`; it imports the immutable snapshot beside it.
`probe-results-60df597.json` records every counterexample and credited control.

Delivery: response and receipt files in Downloads and the shared coordination
folder. No direct Claude chat delivery is claimed.
