# TEE Self-Improvement Campaign (A33)

**The product's first real task: improve itself.** TEE — whose mission
is to help any AI optimize its token usage and improve its work
efficiency (A32) — is turned on its own codebase. The working session's
co-pilot is TEE itself: its memory, its knowledge tools, its benchmarks,
its own dogma. The goal is a product that is *leaner*, *executes better
and more efficiently*, is *more polished*, and moves concretely toward
*commercial readiness*.

A one-paste prompt for a fresh session:

> Read CLAUDE.md, then CLAUDE_SELF_IMPROVEMENT_SCRIPT.md, then the last
> few dated entries of docs/PROGRESS.md. Call `tee_status` and
> `tee_recall` first and use TEE's own tools as your co-pilot throughout.
> Work the campaign phases in order from where the evidence says they
> stand, with real before/after measurements for every claim. Stop and
> report if any phase's premise no longer holds.

## Standing rules (all inherited, none new)

- Branch `claude/token-efficiency-engine-5jv1dj` only; small commits,
  imperative subject, body says why; evidence into `docs/PROGRESS.md`
  before ticking anything; never assert success without output.
- The A30/A31 boundary is absolute: `knowledge-base/` grounds nothing
  until a fact is re-verified against its own cited source, and domains
  `13_*`/`14_*`/`15_*` are NEVER an API source. `docs/research/` remains
  the only corpus that can justify an engineering decision.
- CLAUDE.md's six hard rules govern every change here too. Rule zero of
  this campaign: **a change that saves tokens but regresses a measured
  benchmark row or breaks a test is not an improvement — revert it.**
- `benchmarks/` runs before AND after any change to state
  representation, tool schemas, or response shapes (CLAUDE.md testing
  rule). BENCHMARKS/RESULTS files are append-only; new rows, never
  edited history.
- Downloads over 2 GB: state free disk and ask the owner first.
- Owner-only decisions are flagged in the report, never made: pricing,
  licensing changes, renaming, repo split, publishing to any store or
  registry, deleting modules, amending the mission. Record proposals in
  the SI-4 gap list instead.
- If the TEE MCP tools are not available in the session, fall back to
  the CLI (`server/.venv/bin/tee`) and note it in PROGRESS — do not
  block on it.

## The co-pilot contract (dogfooding is the method)

Every session of this campaign:

1. Starts with `tee_status` + `tee_recall` (TEE's own memory is the
   campaign's cross-session state; `tee_remember` stores a dated note
   at session end: what moved, what's next).
2. Uses `kb_search`/`kb_read` whenever a domain fact is needed, and
   `tee_search_tools`/`tee_describe_tool` instead of reading adapter
   source to answer "what can TEE do".
3. **Logs every friction met while doing 1–2.** Any moment where TEE's
   own surface was confusing, verbose, slow, or wrong goes into
   `docs/SI_BACKLOG.md` as a numbered item with the transcript evidence.
   Dogfooding friction is this campaign's richest source of real
   improvements — treat it as data, never as an aside.

## SI-0 — Baseline ledger (nothing improves until it is measured)

1. Reproduce the current claims on this machine, recording exact
   numbers: full server + voxkiln suites; the benchmark scenario suite
   (`benchmarks/`); the always-loaded surface cost (16 tools / ~2,465
   tokens at last count); `tee doctor` on both adapters.
2. Inventory the knowledge assets the campaign may draw on, with their
   authority level stated: `docs/research/` (48 docs — engineering
   grounding), `docs/DECISIONS.md` + `docs/PROGRESS.md` (project truth),
   `knowledge-base/` via `kb_status` (38 domains — reference only, per
   A30; note which domains, if any, bear on software quality, docs
   writing, or product polish, and what re-verification would need).
3. Write the baseline as a dated PROGRESS entry: the table every later
   phase diffs against. Acceptance: every number in it came from a
   command run this session, none from memory.

## SI-1 — Leaner (tokens, dependencies, dead weight)

1. Surface audit: measure the token cost of every one of the 16 tool
   definitions and the top virtual tools; tighten descriptions that
   spend words without changing model behavior. Target: surface cost
   strictly down with zero semantic loss; prove with a before/after
   count and one unchanged-behavior benchmark run.
2. Response audit: sample real responses from each tool family
   (scene_summary, diff, batch report, kb_read, as_search rows) against
   hard rules 1–3; shave anything the client never needs. Every shave
   gets a before/after token count on the same fixture.
3. Dependency + dead-code pass: `ruff` at stricter settings, unused
   modules, import-time weight, wheel size. The fake-adapter test suite
   must stay green with identical counts (or better, with the diff
   explained).
4. Acceptance: PROGRESS entry with the ledger deltas; no benchmark row
   regressed; suites green.

## SI-2 — Executes better and more efficiently (measured hotspots)

1. Wall-time hotspots already on record, in order: voxkiln UV unwrap
   (442 s of 718 s export on the T.png row), export stats (142 s),
   repair (71 s). Profile before touching; optimize only what the
   profile confirms; re-run the affected battery rows after (append-only
   BENCHMARKS.md).
2. The research-48 follow-ups that harden claims: the full battery
   matrix (9 images × 2 pipelines × 3 seeds — long; schedule across
   sessions or ask the owner for an overnight window) and anything the
   no-delta finding's fp16 scoping opened.
3. Server-side latency: measure per-tool round-trip on live adapters;
   fix anything anomalous. New latency rows join benchmarks, never
   replace old ones.
4. Failure-path quality (hard rule 6): fault-inject each tool family
   (bad ids, missing files, dead adapter, over-budget asks) and verify
   ONE short message with the exact fix comes back; fix every
   stack-trace novel or silent degrade found. The pyannote silent-drift
   lesson (three API drifts hidden by a broad catch) is the pattern to
   hunt: every `except` that swallows detail gets a review.
5. Acceptance: profiled-before/profiled-after for every optimization;
   fault-injection table in PROGRESS; suites green.

## SI-3 — More polished (the product feel)

1. Cold-start truth test: follow `docs/` quickstart + per-DCC setup
   word-for-word in a clean venv and a fresh project; every stumble is
   a doc bug — fix the doc (or the product, if the product is what
   stumbled). The `.mcpb` required-user_config gotcha (project_root)
   must be impossible to hit without the docs having warned you.
2. Consistency pass over the whole surface: naming, parameter
   conventions, report field names, error-message voice, `--json`
   everywhere it makes sense. Propose renames as a table first (they
   are breaking); implement only the ones that don't break the
   installed 0.1.1 contract, and stage the rest for the next minor
   version.
3. The skills (`skills/`, tee-usage and friends): re-read against the
   current surface; stale instructions are polish bugs.
4. `voxkiln doctor` / `tee doctor`: every red state a user can reach
   must name its one-line fix (the gated-DINOv3 message is the
   standard to match).
5. Acceptance: a PROGRESS entry listing every polish item found →
   fixed/staged/rejected, with the cold-start rerun ending clean.

## SI-4 — Commercial readiness (audit, gap list, then the gaps)

1. Produce `docs/COMMERCIAL_READINESS.md`: an honest audit against
   what shipping to strangers requires — install paths (mcpb, wheel,
   UE zip, Blender extension) each rehearsed cold; license/attribution
   audit re-run (the runtime-tree lint + VENDOR.md check); security
   posture doc current; versioning/changelog discipline; support
   surface (issue templates, troubleshooting doc); platform matrix
   stated honestly (what is measured on macOS/MPS vs claimed);
   telemetry statement (TEE sends nothing — say so).
2. Split the gap list in two: items a session may just fix (docs, CI,
   packaging hygiene, error messages) — fix them; items that are owner
   decisions (name/trademark, pricing, store submission, repo split,
   support commitment) — write each up with a recommendation and STOP
   there.
3. Release engineering: changelog since 0.1.1, a release-candidate
   checklist, and a clean `make dist` whose artifacts pass the same
   install rehearsals that closed handoff §3. Tag nothing without the
   owner's word.
4. Acceptance: COMMERCIAL_READINESS.md exists with every claim
   evidence-linked; the fixable column is empty or in progress with
   named blockers; the owner-decision column is written up.

## SI-5 — Prove the campaign (the closing ledger)

1. Re-run everything SI-0 measured, produce the before/after table, and
   write the campaign close-out in PROGRESS: what got leaner (numbers),
   faster (numbers), more polished (list), and how far commercial
   readiness moved (gap count before/after).
2. Honesty gate: any metric that moved the wrong way is reported in the
   same table, with why, not footnoted away.
3. `tee_remember` the close-out summary so the next campaign starts
   from TEE's own memory of this one.

## Premise notes for the working session

- The Desktop-installed bundle is 0.1.1 with `project_root =
  /Users/john/TEE`; the manifest text in git is newer than the installed
  bundle (A32 wording ships with the next build).
- Named open threads that predate this campaign and belong inside it:
  the full research-48 matrix (SI-2), SANS 10400 jurisdiction wiring
  for plaus_check (SI-3 candidate, needs KB re-verification per A30),
  hip roof stays blocked on a straight-skeleton library (design
  decision — out of scope here unless the owner says otherwise).
- Sessions are resumable: PROGRESS + `tee_recall` carry the state; a
  fresh session re-reads this script and continues from the evidence,
  never from assumption.
