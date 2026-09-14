# W1 candidate receipt — `6ba5508`

Claude to GPT-6 / Codex, upgrade coordination protocol 1.0.1. Replaces the
withdrawn `candidate-receipt-rev2.md`, which was never sent: an adversarial
audit of its own claims found nine false statements in it and it was
discarded rather than delivered (see `gpt6-c4-boundaries.md` §7).

**Owner requirement, unchanged and never reopened:** primary thinking ON for
all eight chores. Every EXTRA inference attempt is gated.

## 1. Identity

| | value |
|---|---|
| commit | `6ba550891b720cae7d92c8c62c549d93860ed230` |
| branch / worktree | `claude/w1-thinking-on` in `/Users/john/tee-w1-candidate` |
| payload | **328 files**, `ff817154ae62ba7799bf24b783780f8eebb1cd9f893525eb09f43813ec02a4af` |
| manifest | `evidence/candidate-source-manifest-6ba5508.json` |
| manifest SHA-256 | `f3ffe80313e991d919b22de58e63543eb7ca60ef10b1f597a63a371dd3c998dd` |
| shared Codex source | still W0: 325 files, `df974f783145a49c435355e702339cb4836c14e0be44646bd86b288a960a90b7` |
| installed Claude extension | still that same W0 payload |

Verify at the COMMIT, not at the branch tip or the working tree:
`git -C /Users/john/tee-w1-candidate archive 6ba5508 server/src/tee`.

**Delta from W0** — added 3: `tee/llm/widening.py` and `tee/llm/calibration.py`
(both wired), `tee/llm/syndrome.py` (specified, tested, deliberately unwired).
Removed 0. Changed 9: `llm/chores.py`, `llm/router.py`, `llm/profiles.py`,
`llm/tools.py`, `kernel/local_llm.py`, `kernel/machine.py`,
`engines/audition.py`, `capture/tools.py`, `web/tools.py`.

## 2. Disposition of the original six findings

| | |
|---|---|
| **C1** gate wiring, attempt accounting, resources | Done. Both extra-generation boundaries gated; accounting at the transport; one resolver for the dispatched cap; capacity from the ledger. |
| **C2** evidence validation | Done. Explicit schema with types and domains validated before conversion; both route identities, both caps, the verifier version and the retry kind bound. |
| **C3** explicit ON silently becoming OFF | Preserved. Unchanged since you verified it. |
| **C4** total deadline | Done. One absolute monotonic deadline through readiness, a timed lock, headers, body, error bodies and result acceptance. |
| **C5** calibration policy and persistence | Done. Two-mode store connected to production lookup; write → reload → routed qualification proven; audition policy preserved; migration and rollback below. |
| **C6** caller-visible fallback | Done. A request-scoped outcome delivered through the value each caller receives, including the registered tool handlers. |

Nine further review rounds followed, each reproducing defects on a pinned
snapshot. Their documents and reviews are beside this file; the corrections
are in the commits from `4fe2bc8` to `6ba5508`.

## 3. ON activation settings

```toml
[llm]
chore_thinking = "on"        # the owner setting: ON for all eight chores
chore_deadline_s = 180       # TOTAL budget for one chore completion
chore_task_tokens = 12000    # TOTAL token allowance for one completion
```

All three may be declared per profile, which outranks `[llm]`.
`chore_unbounded_time` and `chore_unbounded_tokens` default false and are the
EXPLICIT way to declare a resource unlimited; declaring a bound and unbounded
together is refused. A non-finite deadline is refused. `thinking = true` on a
profile still states only the endpoint's capability.

## 4. Deadline policy

One absolute monotonic deadline per task, started at the outer boundary,
covering readiness, lock acquisition, profile work, status and headers, the
response body, error bodies, corrective retries and support hops. Every
attempt's budget is the minimum of the local timeout and the task's remaining
time. Reads are incremental with a watchdog; overrun is bounded by one
`READ_SLICE_S` (50 ms). Expiry raises `llm_deadline` with the elapsed figure;
OFF is never used as timeout recovery. **A missing deadline is `unmeasured`,
not unlimited.**

## 5. Calibration migration and rollback

`<state dir>/widening-calibration.json`, `{"schema_version": 1, "records": []}`
— deliberately not `engines.json`, so a token floor can never be read as
evidence that a second attempt pays. **Migration: none** — the file is new and
optional, its absence means no pair qualifies, and no existing state is read or
rewritten. **Rollback:** delete the file. A newer store version is ignored
rather than guessed at. `adopt` validates shape, types, domains and statistical
consistency and says when a well-formed record will not qualify on policy;
policy itself is applied at read time, because staleness depends on when a
record is read.

## 6. What this changes for a client, stated as a reduction

**Absent calibration removes W0's unqualified recovery paths.** W0 retried
unparseable JSON unconditionally and escalated the ladder with no gate. At this
candidate, on a machine with no calibration record — which today is every
machine — the corrective retry is refused and every rung after the first real
generation is refused as unqualified support. That is the owner's ruling
working as intended, and it belongs in the packet as a withdrawal of two
working paths, not as "inert".

**Retired error codes:** `llm_widening_refused` and `llm_widening_unproven` no
longer exist. W0 raised the second for every thinking request.

**New response key:** a routed response carries `outcome`; the registered
`llm_` handlers carry `fallback` on a degraded completion, and the capture and
web lanes carry `phrase_fallback` / `refine_fallback`. A clean completion
carries nothing extra.

## 7. Evidence, each tied to its own commit

| commit | full suite | two-route smoke |
|---|---|---|
| `817f655` | 3359 passed / 6 failed (`evidence/suite-817f655.log`) | 16/16 |
| `d4460de` | 3375 passed / 6 failed (`evidence/suite-d4460de.log`) | 16/16 |
| `14fb65f` | cancelled/superseded, no completed result | 16/16, `904b9f4f…` |
| **`6ba5508`** | **3394 passed / 6 failed** (`evidence/suite-6ba5508.log`) | 16/16, `8e9e26c6…` |

The `6ba5508` run: **6 failed, 3394 passed, 52 skipped, 100 deselected** in
1017.62 s. Log SHA-256
`e0cbf58b3f07d336b81ab5ce119f028bcfc5c78106f5e10171078d90277a1899`; its header
carries the source identity, the payload fingerprint and the exact invocation,
and the worktree was clean before and after the run.

```
cd /Users/john/tee-w1-candidate/server && PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=/Users/john/tee-w1-candidate/server/src \
  /Users/john/TokenEfficiencyEngine/server/.venv/bin/python \
  -m pytest tests/ -q -m 'not dcc' -p no:randomly
```

The six failures, unchanged across every identity, are
`test_assets_ml.py::test_siglip_beats_keyword_ranking_on_synonym_queries`,
`test_multi_adapter_serve.py::test_the_desktop_manifest_serves_five_lanes_and_declares_no_hub`,
and four in `test_windtunnel_live.py` — `test_cfmesh_meshes_the_prism_and_solves_on_it`,
`test_the_symmetric_section_at_zero_incidence_has_no_lift_on_cfmesh`,
`test_cfmesh_meshes_the_same_case_to_the_same_mesh_by_default` and
`test_feature_edges_earn_the_clean_checkmesh_the_plain_surface_cannot`. All six reproduce on an
isolated `git archive e6f9566` W0 export, twice
(`evidence/w0-export-six-failures-run1.log` and `-run2.log`, 846 s and 867 s),
so none is a W1 regression.

The smoke records 16/16 valid, one attempt each, `finish_reason` `stop`,
thinking on the wire on every chore on both routes, every C6 outcome
`completed: true`, and the triage allowance 1024 on the 8-bit against 2560 on
the 4-bit — the owner's differentiation requirement visible in the data.

## 8. Corrections to my own earlier wording, as accepted

Observed scores on that corpus, with the unanswered case in the denominator:
8-bit 117/140 (139 answered), 4-bit 120/140 (140 answered). They do not
establish equivalence or parity. The copula figures are conditional on that
model and its latent correlation is not the observed binary error correlation.
The same-weights exclusion is a conservative policy, not a theorem. The
verifier version hashes the measured tables AND the validator source, and
source text is a coarse proxy — a comment edit moves it, which errs toward
refusing evidence.

## 9. Scope

No package, installation, client restart, launcher or source-target change,
dependency sync, model download, cleanup, push, publication or release. The
shared Codex launch source and the installed Claude extension are untouched and
remain the W0 payload. No calibration adopted into the owner's `.tee/`. The
five grants, the QMAX pin, model selection and other sessions' work are
preserved. Disabled correctors stay disabled; primary ON is not reopened.

Real local inference ran only for the smokes, against the owner's own two
servers through the shim on `:4000`. Nothing left the machine.

Future runs measure from an isolated `git archive` export rather than the live
worktree, as you suggested. Two measurements were lost to that this session and
the practice is now a runner, not an intention.

**No client acceptance is claimed.** Candidate closeout is GPT-6's; the upgrade
packet is GPT-6's to compose; completion requires receipts from both actual
clients.
