# Decision log

Amendments to the settled architecture (A1–A7 in
`docs/research/00-index.md`) or to `CLAUDE_EXECUTION_SCRIPT.md` are recorded
here before being implemented: date, decision, rationale, what it supersedes.

## 2026-08-25 — Expert Knowledge Base imported; TEE scope amended (A29)

The owner directed that the full "12 Expert Knowledge Base" from the
Okongo Oneleiwa Project Dropbox — 38 domains, 401 files, ~1.4M words,
1,811 cited sources — be integrated into this repository as sourced
reference data (all 38 domains, not just the construction-adjacent
ones). It is mirrored verbatim under `knowledge-base/`, frontmatter
intact. This amends TEE's scope as follows.

**A29 — two corpora, one authority rule.** TEE now carries reference
material it did not author or verify. The boundary is absolute and is
the point of this decision:

- `docs/research/` remains TEE's OWN grounding: written by this
  project's research passes, verified against primary sources at the
  time, cited per finding, and the only corpus that may justify an
  engineering decision (`docs/DECISIONS.md` cites it, not the KB).
- `knowledge-base/` is IMPORTED reference: authoritative for nothing
  in TEE until a specific fact is lifted out, re-checked against its
  own cited source, and wired in with that citation recorded. Its
  `confidence:` and `status: needs-verification` frontmatter markers
  are load-bearing — a `low`/`needs-verification` file is an open
  question, not a fact.
- **Hard rule, DCC domains:** `13_software_unreal_engine`,
  `14_software_blender`, `15_software_autodesk_fusion` are third-party
  prose about the exact APIs TEE exists to keep models from
  hallucinating. They are NEVER a source for a `bpy`/`unreal` call.
  API facts come from the live version probe, local docs, or a smoke
  test — the CLAUDE.md rule is unchanged and now explicitly outranks
  anything in the KB.

**Scope widened (one item, deliberate):** the plausibility checker's
jurisdiction coverage extends from IRC/US + generic to include
southern Africa — SANS 10400 and the Namibian building-control route,
sourced from `knowledge-base/03_codes_standards/`. This closes the gap
tracked since Phase 11 ("SANS 10400 has not been added for Okongo
jurisdiction defaults"). A20's findings-not-approvals contract is
unchanged: the checker flags against cited clauses with CODE/STD/
HEUR/CONV severity, it never approves, sizes, or certifies, and a
Namibian finding cites the Namibian instrument rather than assuming
the South African one applies.

**Scope explicitly NOT widened:** TEE does not become a knowledge
management or retrieval product. No KB search tool, no embedding
index, no RAG lane is promised by this decision — the always-loaded
tool surface is unchanged (A2/A11 progressive disclosure still
governs). Any future retrieval over the KB is a separate, measured
decision. The non-construction domains (aviation, medical, finance,
health, semiconductors, and the rest) are carried as the owner's
reference library and wired into nothing.

**Provenance obligation:** the corpus keeps its own
`00_meta/source-register.md` (1,811 URLs) and `00_meta/VERIFICATION.md`.
Anything TEE lifts from it carries the original citation through to
TEE's own data files, so a rule in `plaus_rules.json` remains
traceable to the instrument it came from, not merely to "the KB".

**Implemented 2026-08-25 (Phase 14.2).** The first fact lifted out of the
corpus reversed the obvious design. The naive reading — "give Namibia the
SANS rules" — is precisely the error the KB names as characteristic of AI
agents on this topic: SANS 10400 is law in South Africa only. In Namibia it
binds solely where a local authority incorporated it under LAA s 94B, and on
communal land there is no building control at all. So the jurisdiction layer
varies **legal force**, not just numbers: `max_severity` per regime, with
CODE capped to STD wherever no code has been adopted and the downgrade
stated in the finding (`severity_capped_from` + reason). Bare "NA" resolves
to NA-unresolved rather than guessing between three materially different
regimes, and an unknown region raises instead of quietly falling back to the
IRC. Every encoded SANS value carries clause + edition + a RE-VERIFY note,
honouring the provenance obligation above and the corpus's own warning that
SANS text is sold, not published, and changes between editions.

## 2026-08-22 — Voxkiln RESTORED (owner decision — approval received)

The owner reports the pending approval has come through (the gated
DINOv3 image-tower access was the blocker at removal time) and directed
that Voxkiln be rebuilt and reinstalled. Restored from git history at
the removal commit's parent (619bfc5^) — the exact test-green state,
including the three Mac-found vendored-defect fixes — rather than
rebuilt from scratch. Two fixes landed during restoration: `networkx`
declared as a runtime dependency (trimesh's hole-fill needs it; the
original env had it only transitively), and the two gated-weights
doctor tests now skip cleanly on environments without the `[model]`
extra (split-execution rule). This amends the same-day removal entry
below; A26–A28 are in force again. TEE integration (driver-first
registration, lane-3 probe, doctor check) is restored with it;
generated-3D is local-first once more, hosted Tripo/Meshy the keyed
fallback. The Mac owes the live half again: reinstall, weights if
cleaned, first live generation, determinism, the stock-vs-ours battery.

## 2026-08-22 — Voxkiln removed; the out-of-the-box 3D-generation need is dropped (owner decision)

Hours after the Phase 13 build and its Mac bring-up, the owner removed
the requirement that TEE can generate 3D models out of the box and had
Voxkiln deleted from the repository: the `voxkiln/` package, its setup
doc, the TEE `gen_voxkiln` driver + tests, the lane-3 probe branch, and
the `tee doctor` check. This amends A26–A28 (below): they remain the
record of what was decided and built, but nothing in them is owed.

What remains: generated-3D is hosted-only through the pre-existing keyed
Tripo/Meshy drivers (dormant without keys, cost-gated, no longer an
outstanding item); asset needs are covered by the curated library
sources and the procedural lane. The research corpus (digests 43–48)
stays as knowledge. Revival point: git history at the removal commit's
parent — the product was test-green there, with live generation still
blocked on gated DINOv3 access at the moment of removal.

## 2026-08-22 — Phase 13 (Voxkiln: TRELLIS.2-derived generation product) researched; decisions A26–A28

Owner decision: "set the project to use trellis.2 source code for this
task, deep research and improve it to cover known defects and integrate
it as a separate product that is optimized for ai." A six-agent
deep-research pass (docs/research/43–48) grounded it against the actual
source (microsoft/trellis.2 @75fbf01, trellis-mac @d58628f,
stableprojectorz @d5d38f1, ~170 upstream issues). New settled decisions
in `docs/research/00-index.md`:

- **A26 — product shape & fork strategy:** separate product (working
  name Voxkiln; "TRELLIS" excluded from the name — MIT grants no
  trademark rights), vendored hard fork pinned to upstream 75fbf01
  (upstream dormant: 11 commits ever, zero external PRs merged),
  weights via pinned HF snapshot_download (never vendored), license
  surgery removes NVIDIA-non-commercial (nvdiffrast, nvdiffrec_render,
  cubvh), GPL (plyfile), LGPL (easydict) from the runtime and replaces
  CC-BY-NC RMBG-2.0 weights; DINOv3 accepted with attribution terms.
  Lives in the TEE monorepo as a self-contained package for now;
  own-repo extraction is a recorded physical-machine step.
- **A27 — defect-fix + quality contract:** evidence-ranked fix list
  (fp32 decode thresholds, CPU boundary-loop hole fill,
  repair-before-bake with frozen full-res reference surface, staged
  simplification, DC cap, memory discipline, GLB alpha fix, honest
  resolution-downgrade reporting, per-stage seeded generators);
  MIT/BSD/Apache-only in-process repair stack
  (trimesh/manifold3d/fast-simplification/xatlas); topology-aware eval
  battery — weightless exact-count CI fixtures + a stock-vs-ours Mac
  battery; improvement claims exist only as results-file rows.
- **A28 — AI-first interface + platform posture:** one bounded
  generate call (server-side wait, poll loops banned), compact machine
  report + budget verdict + provenance (`ai_generated: true`), ≤4 MCP
  tools, input-hash cache, structured refusal over hangs; Apple
  Silicon first-class (FlexAttention-MPS, vendored+pinned Metal stack,
  full-residency on 128 GB, watchdog/thermal telemetry, worker
  process); CUDA first-class; TEE consumes it as the default
  GenDriver with hosted Tripo/Meshy demoted to keyed fallback.

Load-bearing evidence: the license taint is confined to pre/post
processing — all five neural stages are MIT code + MIT weights, so a
commercial-clean fork needs no retraining (43); the worst geometry
defects trace to hard fp16 logit thresholds and a crash-prone CUDA
mesh library, both fixable in Python (44); textures do not exist until
export, so repair-before-bake is free texture correctness (46); the
Mac port's fidelity loss came from discarding the full-res bake
reference, not from decimation itself (46); Tripo's own docstring
instructs the model to poll ("you MUST repeatedly call the
get_task_status tool") — the interface vacuum is real (47); upstream
is dormant and unresponsive, which both forces the vendored fork and
de-risks it (48); nothing released Jan–Aug 2026 beats TRELLIS.2-4B on
open license + quality, so the base holds (48).

Supersedes: A14's "TRELLIS.2 local (CUDA)" lane and the A14/PROGRESS
"Still needs CUDA: local TRELLIS.2" ledger item — the product targets
MPS + CUDA, so local generation is now IN scope for the Mac. Amends
A22's export lane consumer list (Voxkiln output feeds the same
cleanup/import path).

## 2026-08-22 — Live UEFN editor integration descoped (owner decision)

UEFN runs on Windows only and the project's physical machine is a Mac
(M5 MacBook Pro Max) — there is no Windows machine and none is planned.
The owner removed the live-editor lanes from scope: the live UEFN proxy
(script 12.3's live half), the compile-in-editor Verse path, Scene
Graph operations against Epic's toolsets, live playtest sessions, and
the clean-Windows-machine install rehearsal. This amends A22 (its "thin
capability-probed proxy of Epic's UEFN toolsets" item) and A23's
live-editor items; it is a removal from the outstanding ledger, not a
deferral.

What stays, unchanged and fully supported everywhere: the offline UEFN
lanes — Verse digest facts + digest-grounded linting, the template
corpus, `export_for_uefn` preflight, the Fortnite Data API analytics
lane, and the `uefn` skill. The adapter interface + FakeUefn fakes stay
in the codebase as the revival point should a Windows machine ever
join; `uefn_status` reports the mode honestly (offline, never "live").

## 2026-08-22 — Phase 12 (TEE UEFN + trajectory firewall) researched; decisions A22–A24

A five-agent deep-research pass (docs/research/38–42) grounded the
bonus module: Fortnite/UEFN + Verse, anticipating upcoming Unreal and
Blender versions. New settled decisions:

- **A22 — UEFN module shape:** docs+codegen core (local Verse digest
  ingestion → version-keyed API facts + digest-diff firewall;
  MIT/Apache-seeded template corpus, compile-checked via Epic's UEFN
  MCP when an editor is live, digest-symbol-linted offline) + a thin
  capability-probed proxy of Epic's UEFN toolsets (typed
  batch/diff/checkpoint, server-side LUF↔XYZ fix, local device-catalog
  index) + a Blender `export_for_uefn` op (budget validator, LOD
  autogen, bake + channel packing, exact-fix report — no such tool
  exists) + a `uefn` skill. AGPL reference-only; publish stays
  human-gated, never promised.
- **A23 — UE trajectory posture:** 5.8.1 as long-lived baseline; TEE
  owns checkpointing (5.8.1 disabled transaction bundling in tool
  scripts); toolset probing keyed on catalog/schema hashes; stable IDs
  abstracted over Actor refPath vs Scene Graph entity;
  Scene-Graph-first UEFN vocabulary with devices as an
  eventually-legacy family; one interface over UE + UEFN adapters for
  the UE6 merge.
- **A24 — Blender 5.3/6.0 firewall:** `use_nodes` writes banned now;
  session_uid shuffle test; per-version asset listings (`@b5_3`);
  Vulkan probe + OpenGL fallback; `set_gn_input()` chokepoint +
  enum pre-flight; float32 tolerances; physics ops declare
  `backend: legacy | gn_physics`.

Load-bearing evidence: Epic shipped its MCP inside UEFN (v42.00,
2026-08-20, beta — five toolsets incl. Verse compile and Scene Graph)
and named MCP a UE6 pillar, validating A4's proxy-and-extend posture as
the only one that rides the curve; the community bridge graveyard
(uefn-verse-mcp archived three days before Epic shipped) buries the
from-scratch adapter option; there is no public Verse compiler, so
digest-grounded symbol linting is the only authoritative-adjacent
offline check and kills the dominant hallucination class (`<varies>`
died in v30.00; digests are per-install and non-redistributable); no
Blender→UEFN export tool exists despite published Fortnite-Ready budget
tables — a pure-Python validator is TEE's uncontested wedge; Blender
5.3/6.0 fault lines (all_ids order, `use_nodes` removal, Vulkan
default) are published and shim-able now; legacy physics shows no
deprecation signals, confirming Phase 11's bet.

## 2026-08-22 — Phase 11 (TEE Physical) researched; decisions A19–A21

A six-agent deep-research pass (docs/research/32–37) grounded the
physics, material-science and modeling module; two agents verified
findings by execution (local Blender 5.2 smoke tests; source-level
reading of 5.2 bake paths). New settled decisions:

- **A19 — physics surface & determinism contract:** legacy Blender
  RB/cloth as primary ops with bake-before-checkpoint; UE settle via
  SIE + short-call cadence; static-first verification ladder
  (CoM-over-support → settle → mechanism sweep); same-machine
  determinism only, tolerance assertions above a measured variance
  floor; honest fact wording ("rest-stable", never "structurally
  sound").
- **A20 — material facts & plausibility floor:** three-tier
  honesty-labeled material schema on a CC0 backbone with UsdPhysics
  vocabulary; structural checks are findings-not-approvals with
  CODE/STD/HEUR/CONV severity and the IRC R301.1 load-path
  reachability graph; no sizing, no "passes" state.
- **A21 — modeling tier-2 ops:** wall/slab/roof/stairs/opening/array/
  param_set/sketch_solve compiled to verified BMesh patterns or
  socket-identifier-addressed GN groups; MANIFOLD boolean default;
  py-slvs server-side constraint solving; Geometry Script/PCG as the
  UE compile targets.

Load-bearing evidence: 5.2 removed NodesModifier ID-properties (shim
entry) and the legacy 'FAST' boolean identifier; ptcache/fluid/GN bake
exec paths are synchronous headless (source-verified) while
calculate-to-frame is invoke-only; Epic caps Chaos determinism at
"close, but not perfect" cross-machine and ships no MCP simulation
toolset (TEE's settle macro fills the gap); NIST SRD is
statute-protected against bulk copying; the flagging-vs-sizing line
keeps plausibility checks clear of engineering practice.

## 2026-08-22 — Phase 10 (TEE Design) researched; decisions A16–A18

A six-agent deep-research pass (docs/research/26–31) grounded the expert
game design module on real user routines, experiences, profiles, trends
and logic. Three new settled decisions in `docs/research/00-index.md`:

- **A16 — knowledge encoding:** reference tables (sourced, versioned) +
  one game-design skill + executable checkers; no fine-tune, RAG
  long-tail only; PXI-not-GEQ; facts-only licensing rule.
- **A17 — spec & verification:** machine-verifiable `tee-design/1` spec
  as source of truth (prose GDD = rendered view); LLM-proposes-
  formal-verifies battery from design-lint to bounded self-play; spec
  sections feed the build phases directly.
- **A18 — evidence & ethics floor:** percentile benchmarks over folk
  targets; enforce-vs-judge UX split; code-severity dark-pattern rules
  from live enforcement actions; AI-content consent/disclosure defaults.

Load-bearing evidence: the design-expertise layer is unclaimed across
all products and engines (Aug 2026); every successful generation system
pairs the LLM with a formal validator; LLM prose GDDs score deceptively
well (the argument for spec-as-source-of-truth); median mobile D1 is
~22%, not the folk 30-40% (top-decile numbers); GEQ was never validated;
the randomization in loot boxes — not spending — is the measured risk
factor; and UE 5.8's first-party MCP plugin (extended to UEFN
2026-08-20) validates A4's proxy bet.

## 2026-08-22 — Phase 9 (TEE Assets) researched; decisions A13–A15

A six-agent deep-research pass (docs/research/20–25) grounded the asset
management + creation module. Three new settled decisions in
`docs/research/00-index.md`:

- **A13 — asset backends & license hygiene:** tier-1 = Poly Haven /
  ambientCG / Poly Pizza / Smithsonian (Sketchfab guarded; Fab
  human-only); server-side store owns catalogs/thumbnails/downloads;
  SPDX allowlist failing closed on NC/ND/unknown; attribution manifests
  with license snapshots travel with the cache.
- **A14 — creation lanes & generation floor:** procedural (measured
  values, Infinigen) → local diffusion (Z-Image/klein/SDXL + Marigold) →
  photo-derived PBR → generated 3D (TRELLIS.2 local, Tripo/Meshy hosted
  behind one wait-polling adapter with cost confirmation); mandatory
  cleanup macro; gated lanes labeled; honest bar stated ("set dressing
  on demand, hero assets curated").
- **A15 — selection & context contract:** Holodeck-shaped server-side
  retrieval with ≤5-row shortlists; relational placement plans validated
  against cited clearance/code rules; four-band scale-envelope policy;
  GPS-true sun; render-free verification, one budgeted render max;
  shipped as the `context-aware-assets` skill.

Load-bearing evidence: the official Blender Lab MCP has no asset tools
(space open); the popular community integration measurably re-fetches a
2.3 MB catalog per search and truncates alphabetically; TRELLIS.2's MIT
release (Dec 2025) makes a clean local 3D lane possible; MobileCLIP's
MIT repo hides research-only weights; Sketchfab changed owners again
(KitBash, 2026-08-10) — platform risk is a design input.

## 2026-08-22 — Phase 8 (context economics) added; decisions A11–A12

A research + simulation pass (docs/research/19) measured where the
remaining per-session spend lives after Phase 7. Two new settled decisions
in `docs/research/00-index.md`:

- **A11 — script lane:** `tee_script` runs bounded, AST-whitelisted
  mini-Python over the existing typed virtual tools, atomic under one
  auto-checkpoint, returning only the final result — the app-side
  equivalent of programmatic tool calling (which excludes MCP tools).
  Simulated: −86% context on the conformance fix loop; −61% session cost
  combined with tool-result eviction.
- **A12 — context-economics floor:** adaptive columnar responses (≥ 20
  homogeneous rows), eviction-safe contract + `tee_status(recap=true)`,
  caption-once media facts. Explicit non-decision: fact search stays
  substring-count — a simulated BM25 swap regressed relevance (9/10 →
  7/10 at 611 facts); recorded so it is not "improved" later without new
  evidence.

## 2026-08-22 — Phase 7 (TEE Extract) added; decisions A8–A10

A deep-research pass (9 agents, docs/research/11–18) grounded the media
extraction module. Three new settled decisions recorded in
`docs/research/00-index.md`:

- **A8 — extraction license floor:** deterministic-first stack (pdfplumber,
  pypdfium2, ezdxf, ifcopenshell-as-dependency, OpenCV headless,
  pytesseract/RapidOCR, Pillow, exifread, ImageHash, PySceneDetect,
  imageio-ffmpeg, faster-whisper, optional pycolmap/MobileSAM; shapely,
  pyproj, pymap3d, rasterio for registration). Hard bans enforced by CI
  lint: PyMuPDF (AGPL), marker, ultralytics/FastSAM, CubiCasa5K and
  DeepFloorplan weights, Depth Anything Base/Large. ffmpeg/exiftool via
  subprocess only. Audio is a first-class modality: Claude has no audio
  input, so local transcription (faster-whisper) is the only channel;
  pyannote diarization is optional (MIT code, HF-gated models requiring a
  user token) and degrades silently to non-diarized transcription.
- **A9 — extraction channel:** MCP sampling is dead (deprecated in the MCP
  2026-07-28 spec, unimplemented in Claude Code/Desktop) — the default VLM
  extraction driver is in-band (host model + `ex_store_facts` writeback);
  an opt-in server-side API-key driver (messages.parse + Batches + Files
  API) runs as async jobs. One Extractor interface, two drivers.
- **A10 — fact model:** content-addressed fact store keyed
  (media_hash, extractor_id, extractor_version); FML v3-derived plan schema
  extended with per-level heights and a parametric roof before freeze;
  every geometric fact carries a frame_id; transforms are first-class facts
  in a single-parent tree anchored at site ENU; tier precedence with
  written-dimensions-govern; conflict facts are the conformance report.

## 2026-08-21 — Build on MCP Python SDK 2.0 (`MCPServer` API)

The research corpus and decision A1 referenced the 1.x SDK's `FastMCP` class.
The current SDK on PyPI is `mcp` 2.0, which renames it to
`mcp.server.mcpserver.MCPServer` (same decorator style), adds an explicit
`structured_output=False` switch (a direct implementation of A6's
no-outputSchema rule), and ships an in-memory `Client(server)` used by the
test suite. Substance of A1 unchanged: official SDK, stdio primary. Pinned
`mcp>=2.0,<3`.

## 2026-08-22 — A25: the UE toolset-summary acceptance is an absolute token
budget, not a 10%-of-raw ratio

Phase 3 step 3's acceptance says the test must assert "summarized size < 10%
of raw" for `describe_toolset`. Measured against the live UE 5.8.1 server on
the M5 Mac, TEE's summarizer lands at **11.6–17.1%** with one-line docs kept,
and **7.2–10.0%** with signatures only.

The ratio is the wrong gate, for two reasons the measurements make plain:

1. **It rewards bloat in the input.** `AssetTools` summarizes to 561 tokens
   and scores 17.1%; `BlueprintTools` summarizes to 2,097 tokens and scores
   11.6%. The toolset that costs the model four times less scores worse,
   purely because Epic's raw payload for it carries less boilerplate to strip.
   A ratio measures Epic's verbosity, not TEE's efficiency.
2. **Hitting 10% would cost more tokens than it saves.** The only way there
   is to drop the one-line doc summaries (2,097 → 1,291 tokens on
   `BlueprintTools`, 11.6% → 7.2%). But without a doc line the model cannot
   tell `find_nodes` from `find_node_types` without calling
   `ue_describe_tool`, and each of those round-trips returns a full schema
   (~390 tokens for one `BlueprintTools` tool). Two such lookups already
   exceed the 806 tokens the docs cost for all 53 tools. Optimizing the
   published ratio would make real sessions more expensive - the exact
   failure the project's core metric exists to prevent.

**Decision.** Keep one-line docs on by default; keep a `docs=False` mode for
callers that genuinely want the floor. The acceptance becomes:

- no raw `describe_toolset` payload is ever returned to the model (unchanged
  in spirit, and the point of the original bullet), AND
- the summary of the largest toolset stays **under 2,500 tokens** (measured:
  2,097 for `BlueprintTools`, against 18,042 raw = **88.4% saved**), AND
- the summary is **under 20% of raw** on every toolset, with signatures-only
  mode under 10%.

Recorded rather than silently met: the original bullet is achievable as
written, and was deliberately not adopted because doing so costs the user
tokens.
