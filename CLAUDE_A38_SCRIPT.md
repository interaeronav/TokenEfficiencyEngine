# A38 shrink campaign, round two — faster, more efficient, smaller, leaner (post-0.5.0)

**The owner's directive (2026-08-29): optimize TEE again, with TEE as
co-pilot.** A35 shrank the 0.3.x product; A37 then added eleven
features (gateway, fabrication, joinery, meter, handoff, boards,
switch, kb floor) — new code that has never had a diet pass. This
campaign is A35's method pointed at the 0.5.0 surface area. It
inherits every A35/A33 rule by reference (co-pilot contract,
SI_BACKLOG, append-only benchmarks, revert-on-regression, no silent
capability removal — smaller means lighter, not less; owner-only
decisions; >2 GB gate; machine etiquette; never concurrent with
another campaign on this branch).

A one-paste prompt for a fresh session:

> Read CLAUDE.md, then CLAUDE_A38_SCRIPT.md (and the rules it inherits
> from CLAUDE_A35_SCRIPT.md / CLAUDE_SELF_IMPROVEMENT_SCRIPT.md), then
> the last dated entries of docs/PROGRESS.md. Call tee_status and
> tee_recall first and use TEE's own tools as co-pilot throughout —
> including report_savings on your own session at close. Work the
> phases in order from where the evidence says they stand — nothing
> shrinks without a baseline, nothing ships on a regression. Stop and
> report if any phase's premise no longer holds.

## Premise notes (state at authoring, 2026-08-29)

- v0.5.0 shipped; suites 711/2; surface 2,028 tok / 17 tools (LAW —
  A35's audit already judged further surface shaves not worth the
  wording risk; do not relitigate without new evidence); installed
  bundle 37 MB; cold serve→answer 0.32 s; idle RSS ~74 MB (floor is
  the mcp SDK import, measured); unwrap 12.4 s; warm web lookup 5 ms.
  Those wins are the FLOOR, not the target list.
- **The fresh meat is A37's code**: gateway call path, fabrication
  and joinery lanes, chore templates, kb floor/rerank, boards. None
  has been profiled under the diet discipline yet.
- **Measurement parity**: the chore engine may be sitting on q27b
  (the owner switches freely). Every latency row in this campaign is
  measured on **q14b** (switch first, record the profile in the row);
  q27b rows may be added as labelled extras, never as the comparison.

## S0 — Baseline ledger (the new lanes, measured)

Suites green as the entry ticket. One dated PROGRESS table, every
number from a command run this session: per-call latency and response
tokens for gateway discovery/describe/call against the reference
backends; fabrication brief→sheet wall time and its stage split
(bridge vs freecadcmd vs export); freecadcmd cold-start cost per
invocation; closet-run wall time and cut-list extraction cost; chore
latencies on q14b + per-chore PROMPT sizes (server-side tokens =
local compute time); kb floor/rerank added latency; virtual-tool flat
cost (11,396 tok / 86 at A37 close); `.tee/` on-disk state size
(fetch cache, kb-staging, ledgers) and its growth policy; venv
package count/MB vs A35's 29; battery harness wall time. Plus the
A35 floor rows re-cited (surface, RSS, cold start) for continuity.

## S1 — Faster (profile first, always)

1. Gateway call path: catalog/fingerprint work per call vs cached;
   backend spawn strategy (lazy vs eager) measured; describe/call
   overhead vs a direct backend call — the overhead number gets
   published honestly in setup-gateway.md.
2. Fabrication: amortize freecadcmd cold starts on batch DXF/STEP
   paths (one process, many exports); drawing-sheet stage split
   attacked only where the profile says.
3. Chores: prompt diet per chore (smaller prompts = faster local
   inference at equal trap-suite scores — the trap suite is the
   regression gate here, rerun per change); the 2 s chore bar holds
   on q14b.
4. Battery harness runtime: parallelize or cache what the harness
   itself wastes (it is now the campaign's own inner loop).

## S2 — More efficient (tokens, round three)

1. Response audits on the NEW shapes: gateway describe (144 tok at
   close), joinery_check findings, board_compose reports, meter/
   handoff payloads — news-not-echoes, fixtured before/after.
2. Virtual-tool flat cost: the 86-tool long tail's summaries at SI-1
   discipline (2,028 always-loaded is LAW; the flat catalog is not —
   measured shave target with zero semantic loss, proven by the
   unchanged-behavior battery).
3. Full battery at close: every bar meets or beats; the two new rows
   (gateway 95.4, fabrication 92.4) are now bars too.

## S3 — Smaller and leaner (footprint, round two)

1. Dependency audit of everything A37 added; the venv count/MB delta
   explained line by line; anything heavy that serves one narrow call
   goes lazy or behind an extra (suites + one live smoke prove no
   capability loss).
2. `.tee/` state hygiene: TTL and size caps on the fetch cache,
   ledger rotation, kb-staging growth policy — bounded by config,
   reported by doctor.
3. Artifact + installed-bundle re-measure; the 37 MB is the number to
   beat only if S3.1 finds real weight — no kilobyte theater.
4. Import-time audit for the 97-virtual-tool registration path (cold
   start is 0.32 s; keep it there as the lanes grow — regression
   fence, not a target).

## S4 — Close-out

Re-measure everything S0 measured; the before/after ledger with
wrong-way numbers explained in place; bars all held; suites + CI
green; artifacts rebuilt + smoke-rehearsed; docs touched where
numbers are cited; **report_savings run on the campaign's own final
session and quoted in the ledger** (the co-pilot measuring the
optimizer); `tee_remember` the close-out; version recommendation by
semver (likely 0.5.1 unless S2/S3 change shapes); the tag stays the
owner's step.

## Scope guards

- No new capabilities (ideas → SI_BACKLOG); no removals without an
  owner flag; the surface LAW stands at 2,028/17.
- The staged owner items stay owner items (SI-B8 flatten, media-in-
  bundle, SI-B11 upstream patch, kb-staging review).
- Model/adapter work stays closed (A34); llm_switch behavior is
  frozen except measured prompt diets inside chores.
