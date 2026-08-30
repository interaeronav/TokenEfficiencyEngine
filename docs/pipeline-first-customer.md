# A43 P4 — the pipeline lane on DiversionPlanner-BaseMap

Recorded 2026-08-30 against the real project: the owner's own builder, his
own flags out of `docs/EA-FULL-CELL-RUNBOOK.md`, his own mamba `terrain`
environment. Nothing here is staged and nothing is a fixture.

The declaration lives in that project's `.tee/pipeline.toml` and is
hash-pinned in `.tee/pipeline.pin`. TEE did not write either file, and
edits to the declaration stop the lane until the change has been read.

Total wall clock for everything below: **0.6 s**, against a project whose
real cell build is tens of gigabytes and hours. That gap is the point -
the lane makes the cheap thing cheap to ask for, and leaves the expensive
thing something you have to name.

## 1. What does this project declare?   [~37 tokens]
_One sentence in chat -> pipeline_list. Names and kinds, not a file dump._
```json
{
 "steps": [
  "selftest (query)",
  "verify (query)",
  "plan (produce)",
  "build_cell (produce)",
  "blunder_stats (query)"
 ],
 "approved": true
}
```

## 2. "plan the basemap for N51W001"   [~135 tokens]
_The whole builder runs end to end - scope, geocells, footprints, sources, policy gate - and answers with what it WROTE, not what it printed._
```json
{
 "step": "plan",
 "kind": "produce",
 "exit": 0,
 "provenance": {
  "step": "plan",
  "argv_hash": "c85566df4689",
  "inputs_hash": "b0738d554ffe6c8b",
  "started": "2026-08-30 18:45:42",
  "wall_s": 0.22
 },
 "artifacts": {
  "created": [
   {
    "path": "build_plan/plan.json",
    "size": 2078,
    "hash": "93584381d3709f51"
   },
   {
    "path": "build_plan/manifest.json",
    "size": 710,
    "hash": "ebc5849cc049ae80"
   },
   {
    "path": "build_plan/NOTICE.txt",
    "size": 1925,
    "hash": "ffc38ee00860b5ea"
   }
  ]
 }
}
```

## 3. "do it again"   [~34 tokens]
_Nothing changed, so nothing runs._
```json
{
 "target": "plan",
 "ran": [],
 "skipped": [
  {
   "step": "plan",
   "reason": "fresh"
  }
 ],
 "answer": "all fresh - nothing to do"
}
```

## 4. "run the self-test"   [~84 tokens]
```json
{
 "step": "selftest",
 "kind": "query",
 "exit": 0,
 "provenance": {
  "step": "selftest",
  "argv_hash": "72aaa668f7f2",
  "inputs_hash": "4c3693c792e32372",
  "started": "2026-08-30 18:45:43",
  "wall_s": 0.06
 },
 "format": "text",
 "answer": "self-test OK — CRC-32Q, Table A8-1 grading, Area 2 geometry, policy gate, determinism"
}
```

## 5. "run the self-test" (again)   [~81 tokens]
_The same question, answered from the record for free._
```json
{
 "target": "selftest",
 "ran": [],
 "skipped": [
  {
   "step": "selftest",
   "reason": "fresh"
  }
 ],
 "answer": "self-test OK — CRC-32Q, Table A8-1 grading, Area 2 geometry, policy gate, determinism",
 "format": "text",
 "answered_at": "2026-08-30 18:45:43",
 "answer_is": "cached from the last run; inputs unchanged"
}
```

## 6. "plan cell rm -rf /"
_The value never reaches argv._
```
pipeline_bad_param: step 'plan': 'cell' does not match ^[NS][0-9]{2}[EW][0-9]{3}$.
fix: Got 'rm -rf /' - the declaration constrains this value deliberately.
```

## 7. The same step from an unattended job (clean)   [~81 tokens]
_Allowed, and that is the point of declaring a step: bounded work is safe to automate._
```json
{
 "target": "selftest",
 "ran": [],
 "skipped": [
  {
   "step": "selftest",
   "reason": "fresh"
  }
 ],
 "answer": "self-test OK — CRC-32Q, Table A8-1 grading, Area 2 geometry, policy gate, determinism",
 "format": "text",
 "answered_at": "2026-08-30 18:45:43",
 "answer_is": "cached from the last run; inputs unchanged"
}
```

## 8. ...but the same job after reading a web page
_Untrusted content can never cause execution._
```
trust_denied: pipeline_run: a job task carrying untrusted content may not invoke 'run-declared-step'
fix: This task carries untrusted content (fetch-web:docs.example). Untrusted content can never cause a side effect. Re-run the step yourself in a live turn if you have read the content and intend it.
```

## 9. "just run this command for me"
_This project never opted in to ad-hoc commands._
```
trust_denied: pipeline_adhoc: 'run-adhoc' is not granted for this project (default deny)
fix: Add 'run-adhoc' to [trust] grants in /Users/john/DiversionPlanner-BaseMap/.tee/config.toml - that is the config file this server actually loaded (SI-B17).
```

## 10. The meter   [~14 tokens]
_total wall for this whole exchange: 0.6s_
```json
{
 "steps_run": 2,
 "skipped_fresh": 3,
 "wall_s": 0.3
}
```


## What this cost, and what it caught

Every answer above is under 140 tokens. The largest is the artifact diff,
which is also the one carrying the most information: three declared
outputs, their sizes and their hashes. The builder's own stdout for that
run is ten lines of scope and geocell counts; none of it is in the answer,
because none of it is what was asked.

Two real defects surfaced from running this against a real project rather
than a fixture, and both are fixed with tests:

* **A bad param was accepted whenever the step happened to be fresh.**
  Freshness was checked before the value was, so `cell = "rm -rf /"`
  returned "all fresh - nothing to do" - a success-shaped reply to a
  request that was never valid. The target's params are now validated
  before anything else looks at them.
* **A tainted job could start a declared build.** The taint law fired but
  landed in the shadow band, because enforcement reused the HIGH_RISK set
  and that set does not contain `run-declared-step` or `fetch-web`. A
  taint denial is a safety denial by definition, so execution, egress and
  policy now refuse immediately whatever the rollout stage. On this
  project the step in question downloads tens of gigabytes.

A third thing was not a defect but a gap: a **query step that succeeded
was skipped as "fresh" and answered nothing**, because a query has no
artifact on disk to be fresh about. Its answer is now recorded with the
run, so asking the same unchanged question again is answered for free
instead of re-run - which on `verify` is 134 seconds saved for the same
sentence.

## The finding the owner should see

`verify` does not pass. One artefact fails:

```
FAIL corrupt: validation/rebuild_diff.json
1 artefact(s) failed verification
```

That is the project's own verifier reporting on the project's own build,
not TEE's judgement of it. It took 134 seconds to learn, and it is now the
cached answer to the question until `build/manifest.json` changes.
