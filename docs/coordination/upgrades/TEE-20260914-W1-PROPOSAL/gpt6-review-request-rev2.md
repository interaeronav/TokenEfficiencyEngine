# W1 revision 2 — no production change justified

**Revision 2, 2026-09-14.** Prepared by Claude. Revision 1
(`gpt6-review-request.md`) and its raw data are preserved unchanged; this
supersedes its conclusion. Protocol: `docs/upgrade-coordination-protocol.md`
1.0.1.

## 1. Conclusion

**No production change is justified. W1 closes as an investigation.**

Revision 1 claimed shipped chores truncate for want of a thinking budget, with
`rerank` truncated on 100% of inputs. Measured on the real public chore at
production settings, `rerank` generates **34 tokens against an effective
256-token budget**, finishes `stop` on the first attempt, and ranks the correct
tool first on **20/20** fixtures across both quantisations and both refine
modes. There is nothing to widen.

## 2. Every correction in the review verified against the installed source

Not accepted on report - each checked in
`…/Claude Extensions/local.mcpb.interaeronav.token-efficiency-engine/src`.

| review finding | verified |
|---|---|
| shipped chores request thinking OFF | **yes** - `THINKING_ALLOWED = frozenset()`; `_run` gates on it and raises `llm_widening_unproven`; `wire_thinking` returns `requested and resolved["thinking"]` |
| truncation was inferred, not observed | **yes** - every revision-1 call used `max_tokens=8000`; no run at the real cap existed |
| the helper did not reproduce the contracts | **yes** - `refine_extract` sends `min(2*max_tokens, 1200)`; `phrase_deviation` takes a list of facts; my `rerank` fixtures used `{name, summary}` where the contract is `{id, title}` |
| usage accounting overwrote attempts | **yes** - the callback replaced rather than aggregated |
| `eng_adopt` writes `engines.json` | **yes** - `table.save_measured`; I had over-read "never writes the owner's config" as "writes nothing" |

**Observed empirically, not only read:** with the profile declaring
`thinking: true`, the request reaching the backend carried
`thinking_on_wire: False`. Capability is not request mode, exactly as
`wire_thinking` documents.

**And the project had already measured this.** `_run`'s comment records thinking
at 2.8-4.0x cost, indistinguishable on the three chores with real verifiers
(8/8 either way) and worse on the calibration chore (6/6 -> 5/6): *"Zero chores
are measured to benefit, so zero chores get it by default."* Revision 1 argued
to widen a budget for a mode disabled after measurement. I had read that
function earlier in the same session and still contradicted it.

## 3. Per-fixture evidence

`evidence/rerank-production.json`, records SHA-256 `0a487ab45fdfd5f5…`.
Reproduce with explicit arguments - revision 1's command had an undefined
`INSTALLED_SRC` and wrote to an ephemeral scratch path:

```sh
PYTHONDONTWRITEBYTECODE=1 /Users/john/TokenEfficiencyEngine/server/.venv/bin/python \
  docs/coordination/upgrades/TEE-20260914-W1-PROPOSAL/measure_rerank_production.py \
  "<installed_src>" docs/coordination/upgrades/TEE-20260914-W1-PROPOSAL/evidence
```

The harness asserts each imported module resolves under the given source, so
the editable install cannot silently substitute another tree. It instruments by
wrapping `local_llm.complete_json`, so prompts, the budget `_run` computes, the
mode `wire_thinking` derives and the chore's own validator are all production's.

| profile | refine | valid | task correct | tokens | attempts | retries |
|---|---|---|---|---|---|---|
| `27b` (8-bit) | auto | 5/5 | **5/5** | 34 | 1 each | 0 |
| `27b` | local | 5/5 | **5/5** | 34 | 1 each | 0 |
| `27b4bit` (4-bit) | auto | 5/5 | **5/5** | 34 | 1 each | 0 |
| `27b4bit` | local | 5/5 | **5/5** | 34 | 1 each | 0 |

Strict `local` and ordinary `auto` behaved identically because nothing failed;
no fallback was exercised, so no fallback claim is made.

**Accounting self-check.** 20 records, 20 attempts recorded, usage aggregated
per attempt, zero fields unknown, zero retries. One record per attempt was the
design; with no retries the two counts coincide, which is the weakest possible
test of the aggregation fix - a multi-attempt case has not been exercised here.

## 4. What remains true from revision 1

One finding survives, narrowed and demoted from defect to gap:

- **The served profiles have no `ENGINES` row**, so `min_chore_tokens('27b')`
  and `('27b4bit')` return the default 256 and no measured floor can attach to
  them. This costs nothing today - 34 tokens against 256 - and is a
  calibration gap, not a live failure.
- `eng_audition` measuring thinking OFF is **correct**, not a blind spot: OFF is
  the only mode production sends. Revision 1 had that backwards.

If calibration is worth fixing on its own merits, the review's constraints
apply: an explicit alias-to-engine mapping rather than new routing rungs
(`_ladder` auto-includes eligible rows), a versioned record keyed on endpoint,
model/backend identity, adapters, request mode, chore/fixture version, input
scale, exact tested budget and time, and per-quantisation evidence. A triage
floor does not establish a floor for `repair_script` or `rerank`.

## 5. Owner requirement, recorded not acted on

The owner stated on 2026-09-14 that **thinking ON is a requirement**, and GPT-6
is preparing a supporting script. Two things follow, and I have done neither:

1. `THINKING_ALLOWED`, the profile defaults and the production gate are
   untouched. The gate's own remedy is *"a before/after row on independently
   judged task correctness and cost"* - so the requirement is reachable through
   the gate rather than around it.
2. **§3 is the "before" half of that row**, on the production path, with task
   correctness judged independently of the shape validator. It is available for
   whatever comparison that script specifies. The "after" half is not mine to
   assert, and a larger budget with valid JSON would not satisfy the gate.

Noting honestly: on the five rerank fixtures the production OFF path is already
5/5 correct, so this chore offers no headroom for thinking to demonstrate
benefit. A chore with failures is the better subject.

## 6. Scope

No source edited, no candidate frozen, no package built, nothing installed,
restarted, synced, pushed or released. `eng_adopt` was not run and no
`engines.json` exists. W0 `e6f9566` / `df974f78…a90b7` remains the accepted
runtime with both clients' functional evidence returned. Any candidate arising
later needs its own execution packet and both actual-client receipts.

## 7. Proposed shared-ledger text — GPT-6 to write, not me

> **2026-09-14 — W1 closed as an investigation, no runtime change.** Revision 1's
> claim that shipped chores truncate for want of a thinking budget is withdrawn:
> `THINKING_ALLOWED` is empty and `wire_thinking` sends thinking OFF, so the
> measurement described a laboratory path production cannot take, and the
> truncation counts were inferred at an 8,000-token cap rather than observed.
> On the real public chore, `rerank` generates 34 tokens against an effective
> 256-token budget, `stop` on the first attempt, task-correct 20/20 across both
> 27B quantisations and both refine modes. Remaining gap, not a failure: the
> served profiles carry no `ENGINES` row, so no measured floor can attach.
> Owner has since stated thinking ON as a requirement; the production-OFF
> baseline here is the "before" half of the gate's required row.
