# A37 build script — the merged campaign: roadmap (A36) × fabrication lane

**This script REPLACES `CLAUDE_A36_SCRIPT.md`** (owner directive,
2026-08-28: integrate A37 with A36). Designs of record: research 51
(gateway/meter/handoff/kit/kb_propose), research 52 (FreeCAD, Home
Builder joinery, joinery_check, boards), research 53 (the integration
map — read it first; the composition decisions live there). All A36
campaign laws carry over verbatim: **the always-loaded surface does
not grow**; **fronted and fetched content is untrusted data**; **the
benchmark bars are the floor**; A30/A31 boundaries; fakes before live;
revert on regression; owner-only decisions flagged; >2 GB gate;
machine etiquette; not concurrent with A35 on this branch. Inherit the
A33 rules section by reference as before.

A one-paste prompt for a fresh session:

> Read CLAUDE.md, then CLAUDE_A37_SCRIPT.md, then research docs 53, 51
> and 52, then the last dated entries of docs/PROGRESS.md. Call
> tee_status and tee_recall first and use TEE's own tools as co-pilot
> throughout. Work the phases in order from where the evidence says
> they stand — probes and fakes before live backends, the kit before
> the adapter it rehearses, benchmarks before claims. Stop and report
> if any phase's premise no longer holds.

## P0-F — Fix first: the kb_hint defect (SI-B10, owner-directed 2026-08-28)

Before any campaign work, close the shipped defect logged as SI-B10:
`kb_hint` (on tee_web_lookup and anywhere else it rides) offers the
best KB match even when the best is irrelevant — three live misfires
on record (a Blender bmesh question hinted at construction case
studies; nasa/XPlaneConnect at SA contractors; stereo-pipeline docs at
game-dev salaries).

1. **Relevance floor**: suppress the hint when the top match scores
   below threshold — reuse SI-B2's weak-match machinery; pick the
   threshold from measured score distributions (in-domain fixture
   queries vs the three misfires), not by feel.
2. **Optional rerank**: when the local endpoint answers, route the
   floor's borderline band through the kb-rerank chore (labelled in
   the response provenance); absent endpoint → floor only.
3. **Fixtures**: the three real misfires must produce NO hint; a
   genuinely-KB question (the paving fixture) must keep its hint.
4. Evidence: hint-token cost on non-domain calls before/after; kb
   benchmark row unaffected; SI-B10 ticked with the commit; small
   commit, pushed, before P0 begins.

## P0 — Baseline + the probes that settle the architecture

1. Suites green; surface and battery totals cited to dated rows.
2. **Install gates, batched for the owner in ONE ask**: FreeCAD 1.1
   (~1 GB class — state exact size + free disk), Home Builder 5.1
   (small, extensions.blender.org), neka-nat/freecad-mcp (tiny).
   None should exceed the 2 GB rule but state sizes anyway.
3. **The FreeCAD probes** (research 53 criteria, pass/fail recorded):
   TechDraw page export under FreeCADCmd (upstream #5710 — prove SVG/
   PDF or record the GUI-process fallback as the lane's transport);
   neka-nat bridge: headless-or-GUI, latency, response token shape,
   bad-op behavior, license lint. The probe table decides one-bridge
   vs own-bridge (research 53) — write the decision as a dated
   addendum to research 53 before any lane code.
4. Pick the two Gateway reference backends (A36 G0 unchanged).

## P1 — Gateway core, on fakes (= A36 G1, unchanged)

`[gateway]` config, lifecycle, fingerprint drift-firewall, catalog →
summarized toolsets through the existing machinery, discovery/describe/
call via the EXISTING meta-tools with backend prefixes, budgets on all
backend results, rule-6 error mapping, conservative caching. Full
contract green against a fake backend (drift, death mid-call,
oversized results, hostile descriptions). Surface delta: 0.

## P2 — Gateway live (= A36 G2 + the CAD backend)

Front the two reference backends AND neka-nat's FreeCAD server (per
P0's probe). Drift firewall exercised on the fake. The gateway
benchmark row: a many-tool backend task naive vs through-TEE, appended
to RESULTS.md. `docs/setup-gateway.md` written (config, untrusted
stance, firewall, the FreeCAD backend as the worked example).

## P3 — The adapter kit (= A36 G5, moved up: the rehearsal law)

`docs/adapter-kit.md` + template + packaged contract tests. Its
acceptance is now REAL: P4 builds the fabrication toolset from the
kit docs alone — every stumble found there is a kit bug to fix in
this phase's file, credited in PROGRESS.

## P4 — The fabrication lane (research 52, built FROM the kit)

Typed batch ops (sketch → constrain → pad/pocket → assembly) on the
P0-decided transport; TechDraw pages derived from the model
(projections, dimensions, title block) via the proven export path;
STEP/DXF out for fabricators; glTF/STEP → the existing `as_import`
into Unreal with read-back verification. sketch_solve (py-slvs,
in-tree) wired for constraint closure. Acceptance: a parametric part
goes brief → checked model → dimensioned drawing PDF/SVG → STEP →
UE import, all in one recorded session; drawing dimensions match the
model by construction (assert from the document, not the picture).

## P5 — The joinery lane + kb_propose (research 52 §pain-2 + A36 G6)

1. Home Builder 5.1 through the EXISTING Blender adapter: batch ops
   over its prompts/operators; dimensioned plan/elevation layouts and
   the geometry-nodes cut-part report exported through tee_media/
   extract. (This sub-phase may interleave with P1–P4 whenever the
   machine is idle — it touches no gateway code.)
2. `kb_propose` (A36 G6 unchanged): drafts to `.tee/kb-staging/`
   only; the mirror-write-impossible test; owner review workflow doc.
3. `joinery_check`: the plaus_check-pattern rule table — 32 mm system
   conformance, hardware-first carcass consistency, hinge boring,
   setbacks — every rule lifted from `06_joinery_and_woodwork` and
   re-verified at its cited source per A30 BEFORE it judges; what
   re-verification learns goes back through kb_propose.
   Acceptance: a seeded-defect wardrobe (wrong system holes, hinge
   collision, carcass/runner mismatch) is caught with cited fixes; a
   clean fixture reports zero findings with the rule count; one full
   closet run: brief → checked model → cut list + elevations → UE.

## P6 — Meter + handoff (= A36 G3 + G4, unchanged)

Savings block in the recap + virtual `report_savings`; virtual
`handoff` ≤500-tok brief with the round-trip acceptance. The P5
closet run re-executed WITH the meter on becomes its live fixture.

## P7 — The board lane (research 52 §pain-3, TEE's half only)

Templated technical boards from the document-render pipeline:
annotated renders, part-in-context views, drawing sheets composed
into styled pages — budgeted, file-out via tee_media. Deck polish
stays host-side by design (state it in the doc). Acceptance: one
sim-prep-grade board and one fabrication board rendered from live
scenes and recorded.

## P8 — Close-out

Full battery live: every bar holds + the gateway row + a fabrication
row (tokens per completed drawing-set, naive vs TEE). Suites + CI
green; docs and skills updated; artifacts rebuilt and rehearsed;
campaign ledger in PROGRESS (surface delta target 0, probe decisions,
acceptance pointers, wrong-way numbers explained); `tee_remember` the
close-out. Version recommendation by semver (expected 0.4.0); the
tag stays the owner's step.
