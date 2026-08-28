# A35 shrink campaign — smaller, faster, more efficient

**The owner's directive (2026-08-28): use TEE to improve itself again —
into a smaller, faster, more efficient package.** Same method as A33:
measured baseline, targeted passes, closing ledger, TEE as co-pilot,
regressions revert. This script inherits every standing rule of
`CLAUDE_SELF_IMPROVEMENT_SCRIPT.md` (co-pilot contract, SI_BACKLOG
friction logging, A30 boundaries, append-only benchmarks, owner-only
decisions, >2 GB gate, machine etiquette) — read that script's rules
section first; they are not repeated here.

A one-paste prompt for a fresh session:

> Read CLAUDE.md, then CLAUDE_A35_SCRIPT.md (and the rules section of
> CLAUDE_SELF_IMPROVEMENT_SCRIPT.md it inherits), then the last dated
> entries of docs/PROGRESS.md. Call tee_status and tee_recall first and
> use TEE's own tools as co-pilot throughout. Work the phases in order
> from where the evidence says they stand — nothing shrinks without a
> baseline, nothing ships on a regression. Stop and report if any
> phase's premise no longer holds.

## Premise notes (measured 2026-08-28, the day this was authored)

- The shipped artifacts are already small: mcpb 566 KB, wheel 362 KB,
  sdist 603 KB. **Do not chase kilobytes in zips** — the weight lives
  elsewhere. Honest targets, in order: the installed Desktop extension
  footprint (**98 MB** venv), startup-to-first-answer, per-tool
  latency, the one remaining big compute hotspot (voxkiln UV unwrap),
  and tokens (surface 2,028 compact / 17 tools; scenes 90.3%; fix-loop
  47.9%).
- Bare `import tee` is already 0.01 s — lazy imports work; measure the
  real thing instead (serve → initialize → first tool answer).
- The installed co-pilot needed pdfplumber+imagehash added by hand —
  a packaging smell worth root-causing in P1 (extras that the bundle's
  jobs need should install with the bundle, or degrade with a rule-6
  line, never require manual uv surgery).

## P0 — Baseline ledger (nothing shrinks until it is measured)

One dated PROGRESS table, every number from a command run this session:
artifact sizes; installed-extension MB and its dependency inventory
(`uv pip list` in the extension venv — name the ten heaviest with MB);
dependency count per extra in pyproject; cold `tee serve` →
`initialize` → first `tee_status` answer wall time (the Desktop UX
number); idle RSS; p50 latency per always-loaded tool against live
adapters where they run; surface tokens (compact, the B4-canonical
measure); current benchmark totals reproduced or cited to their dated
rows. Suites green as the entry ticket.

## P1 — Smaller (the package and what it drags in)

1. Dependency audit, per extra: what each dependency costs in MB and
   imports, what actually uses it, what is dead or replaceable by
   stdlib at equal behavior. Heavy deps that serve one narrow call
   move behind extras or lazy paths. Every removal: suites green +
   the capability's fixture still passes (or the removal is flagged
   as an owner decision — capability changes are never silent).
2. The installed-extension footprint: rebuild from the diet, measure
   the venv delta, and fix the pdfplumber/imagehash smell (bundle
   installs what its declared jobs need, or refuses with the fix).
3. Vendored/data audit: anything shipped that no runtime path reads.
   Acceptance: MB and dep-count deltas in the ledger; zero behavior
   change proven by the full suite + one live-adapter smoke.

## P2 — Faster (start, answer, compute)

1. Cold-start: profile `tee serve` to first answer; defer anything
   not needed for `initialize`/`tools/list`; re-measure. Target:
   strictly down, no half-initialized states (fail loud stays).
2. Per-tool latency: from P0's table, fix what profiling confirms is
   anomalous — never optimize unprofiled code.
3. The compute hotspot: voxkiln UV unwrap (last measured dominating
   export at ~440 s on the T.png row). Profile first; candidate levers
   are xatlas parameters, chart pre-reduction, and parallel packing —
   grounded in `docs/research/46`–`48`, changes measured on the
   frozen battery fixtures, rows appended to voxkiln/BENCHMARKS.md.
   The determinism contract holds (same-seed hash re-verified after).
4. RSS: idle and under a batch; trim what profiling attributes.
   Acceptance: before/after per item, appended rows, suites green.

## P3 — More efficient (tokens, round two)

1. Surface pass on the 17 tools + top virtual tools at SI-1 discipline
   (2,028 baseline; strictly down with zero semantic loss, proven by
   an unchanged-behavior benchmark run).
2. Response audit round two on the fixtures that moved least in A33
   (fix-loop rounds arm, scene_summary paging, web_lookup quote
   framing) — news-not-echoes leftovers.
3. Re-run the standard benchmark battery live; every total meets or
   beats its bar (scenes 90.3%, extraction 93.1%, assets 94.0%, UE
   93.9%, kb 96.7%, web 95.3%); wrong-way rows revert or are explained
   in place.
   Acceptance: appended rows; the bars hold.

## P4 — Close-out

The before/after ledger against P0 (MB, ms, tokens, benchmark totals —
wrong-way numbers in the same table with their why); docs touched where
numbers are cited (README surface/benchmark lines); `tee_remember` the
close-out; owner-decision list (version bump — recommend by semver from
what actually changed; anything staged as breaking). Suites + CI green;
artifacts rebuilt and smoke-rehearsed; tagging stays the owner's step.

## Scope guards

- This campaign does NOT add capabilities. New ideas → SI_BACKLOG.
- No capability, adapter, extra, or tool is removed without an owner
  flag — "smaller" means lighter, not less.
- The research-48 matrix remainder (other seeds / 1024_cascade,
  ~5–8 h) is NOT in scope unless the owner asks; only the UV-unwrap
  hotspot itself is.
- LoRA/model work is out of scope (A34 closed it; the adapter and
  engine stay untouched here).
