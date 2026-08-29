# 57 — Integrating the router (A39) with the reality-capture lane (A40) (2026-08-29)

Verification basis: research 55 (+ swap addendum) and 56 (+ DJI
addenda) as the designs of record; the A39/A40 scripts; TEE project
memory (both campaign keys verified current this session); PROGRESS
confirms neither campaign has started — clean merge conditions. This
doc adds no feature scope; it is the composition map (the research-53
precedent).

## The seams that justify one campaign

1. **One machine, two heavyweight consumers.** A39's router may swap
   51 GB models; A40's reconstructions (ODM dense, Photogrammetry
   full/raw) are themselves tens-of-GB residents for minutes-to-hours.
   Unmerged, each would guard against DCCs and voxkiln but not each
   other. Merged: ONE machine-load ledger — reconstruction jobs
   register as residents the router's memory guard respects (no swaps
   mid-reconstruction), and reconstruction launch checks model
   residency the same way. This seam alone pays for the merge.
2. **The lane is the router's first real customer.** A40's stages
   carry chore-shaped work with deterministic verifiers: capture-set
   QA (per-image caption/blur judgment via the local VLM,
   schema-checked), deviation-fact phrasing (schema + extractive
   verification), kb lookups against the Namibian playbook. Once the
   cascade (R1) is green, these route; until then they run static —
   the lane never waits on the router.
3. **Real rows beat synthetic.** A39's four-arm benchmark (R4) draws
   its mixed-difficulty set partly from the dry run's actual chores —
   the router is judged on the owner's real workload, not invented
   fixtures.
4. **The deadline rules the order.** The site visit outranks
   everything: the capture protocol (T1) and the working
   ingest/reconstruct path ship FIRST; router fake-phases interleave
   during long reconstruction jobs (the machine is busy, the session
   is not). The dry run lands before the trip regardless of router
   progress.

## Laws (union, no relaxations)

Surface LAW 2,028/17 (everything virtual); owner decides design truth
(no auto-apply); the site datum is immutable; honesty bands are
metadata-driven; applies checkpointed; TEE never calls cloud APIs;
TEE/Q pin suspends roaming; swap authority per the A39 amendment BUT
the merged machine-load ledger extends "capable" to include active
reconstruction jobs; uncalibrated confidence gates nothing; bars are
the floor; probes before lanes; the trip is never the first test.

## Phase order (the merged script's spine)

T0 installs+probes (incl. the Mini-model ask, KB rebuild) → T1 the
capture protocol (deadline deliverable) → R0 routing dataset → T2
ingest/reconstruct + the DJI-spectrum resolver → R1 cascade on fakes
+ THE GUARD SEAM (job classes join the memory guard, fixtures both
directions) → T3 georef/align → T4 deviation engine (chores route
once R1 is green) → R2 accounting (escalation + swap + job columns
in one meter) → T5 apply lanes → R3 calibration-or-static → T6 the
dry run (also R4's workload source) → R4 four-arm benchmark (routed
arm carries swap seconds AND respects the load ledger) → close-out
(expected 0.6.0).

## What merging does NOT change

Every phase's internal content stands as written in its source script
(the A37 "= unchanged" precedent): A39's R-phases and A40's V-phases
are referenced, not rewritten. The two superseded scripts stay as
design records with do-not-work banners.
