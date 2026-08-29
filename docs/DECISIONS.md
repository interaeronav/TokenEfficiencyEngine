# Decision log

Amendments to the settled architecture (A1–A7 in
`docs/research/00-index.md`) or to `CLAUDE_EXECUTION_SCRIPT.md` are recorded
here before being implemented: date, decision, rationale, what it supersedes.

## 2026-08-25 — Expert Knowledge Base imported; TEE scope amended (A30)

The owner directed that the full "12 Expert Knowledge Base" from the
Okongo Oneleiwa Project Dropbox — 38 domains, 401 files, ~1.4M words,
1,811 cited sources — be integrated into this repository as sourced
reference data (all 38 domains, not just the construction-adjacent
ones). It is mirrored verbatim under `knowledge-base/`, frontmatter
intact. This amends TEE's scope as follows.

**A30 — two corpora, one authority rule.** TEE now carries reference
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

**Implemented 2026-08-25 (Phase 15.2).** The first fact lifted out of the
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

## 2026-08-22 — A29: pins are actor tags, not a sidecar file (owner request)

Owner request: markers that stand where something should eventually go,
each carrying its own record — id, display name, category, notes, and a
wishlist of what belongs there — readable back without clicking, and
fillable from the free asset sources.

Decision A29: **the storage is the DCC's own actor tags.** One marker tag
plus `<namespace>_<field>:<value>` pairs on a small editor-only marker
actor. Rejected alternatives: a JSON sidecar in the repo (drifts from the
level the moment anyone moves a marker in the editor, and a level reload
cannot repair it) and a custom Blueprint actor class (needs a C++ or BP
asset in every host project, and Epic's toolsets cannot read custom
properties back).

Consequences:
- Pins are Unreal-only for now; the lane fails loud on other adapters
  rather than pretending. Blender's object custom properties are the
  obvious port when it is asked for.
- Reading and writing tags needs unsandboxed editor Python (Epic's
  toolsets expose no Tags access), so the pin lane requires TEE's content
  plugin and `--allow-code-exec` — the same gate as `ue_editor_python`.
- The tag prefix is per-project config (`[pins] namespace`), so pins join
  a project's existing tag family instead of inventing a second one. In
  OkongoSim that is `okongo_pin`, beside `okongo_light` / `okongo_circuit`.
- Pin markers are `is_editor_only_actor` with collision off: an authoring
  aid must never ship inside, or obstruct, the walkable build.
- What fills a pin is found by the label convention `PinFill_<id>`, not by
  the pin's own record, so a re-created marker cannot leave two props
  stacked on one spot.
- Pins are authored state inside a GENERATED artifact: OkongoSim's level is
  rebuilt from `data/*.json` by commandlets. `pin_export` / `pin_import`
  therefore snapshot the pins to a repo-tracked JSON and replay it. This does
  not make the file a second source of truth — the level's tags stay
  authoritative and an export is a snapshot of them; import is explicit, never
  a background sync.

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
written, and was deliberately not adopted because doing it costs the user
tokens.

## 2026-08-26 — A31: the Expert Knowledge Base is a read-only TEE module (owner request)

Owner request: integrate the `12 Expert Knowledge Base` corpus with TEE so
OkongoSim sessions can query it — cross-referencing the sim against sourced
construction knowledge without re-pasting documents into context. (Between
the request and this record, the parallel session imported the corpus
in-repo as `knowledge-base/` under A30 — so this module reads that mirror
by default, not the Dropbox original.)

Decision A31: **the KB joins TEE as a read-only query module (`tee/kb/`),
indexed from the corpus's own `manifest.json`, never written to by TEE.**
This is the runtime lane A30's phase deliberately left closed — it is
sanctioned here on the owner's request, and every A30 rule (two-corpus
authority boundary, citation travels with any lifted fact, DCC-software
domains are never an API source, flags pass through verbatim) binds
whatever these tools return.

- **Read-only, by construction.** The corpus maintains itself with its own
  `00_meta/validate.py` / `00_meta/rebuild.py`; TEE exposes query tools
  only. A write lane would create a second author of a corpus whose value
  is its citation discipline.
- **`manifest.json` is the index source, not a tree walk.** Every file
  entry already carries id, title, domain, tags, jurisdiction, status,
  confidence, words, sha256 and a summary — exactly the hit-list fields a
  token-efficient search needs. The built index caches to `<project>/.tee/
  kb/` (per-project, like other TEE state), keyed on the manifest's
  generated date + per-file sha256s.
- **Drift fails loud and cheap.** With the in-repo mirror (the default
  root) drift is a git event, not a silent one; with a Dropbox root the
  sync can move files under the index. Either way, if a file's sha256 no
  longer matches the manifest, `kb_status` and every query say so in one
  line with the fix (re-run the corpus's `rebuild.py`, or pull the
  mirror), instead of serving stale facts silently.
- **Progressive disclosure, as always.** No `kb_*` tool joins the
  always-loaded surface; the four tools (`kb_status`, `kb_search`,
  `kb_read`, `kb_facts`) register as virtual tools reachable through
  `tee_search_tools` — zero tokens until asked for.
- **The corpus's own flags pass through verbatim.** Confidence
  (high/medium/low), `needs-verification` status and jurisdiction markers
  (`**[NA]**` / `**[ZA]**`) appear on every hit and every returned
  section; TEE never upgrades, drops or rephrases them. The corpus's
  AGENTS.md rules (cite sources, never blend NA/ZA regimes, never present
  unverified figures as fact) are the module's contract.
- **Budgets everywhere.** `kb_search` returns hit lists only (id, title,
  domain, confidence, one-line summary); `kb_read` is section-addressed
  and token-budgeted (never a whole 1.3M-word corpus, never a whole file
  by default); `kb_facts` returns only `## Key facts` blocks — the lane
  for the owner's metrics cross-referencing.
- **No embeddings, no new runtime dependency.** Retrieval is deterministic
  keyword scoring over manifest titles/tags/summaries plus in-file heading
  indexes. The corpus is curated and small enough (401 files) that this
  beats a vector store on both tokens and reproducibility.

Consequences: config grows a `[kb]` section (`root` defaults to the
in-repo `knowledge-base/` mirror from A30's phase; an explicit path —
e.g. the owner's Dropbox original — overrides it; optional `max_kb`
response budget); `cli.py` grows `_attach_kb`; OkongoSim's
`.tee/config.toml` points `root` at the mirror so the pin-namespace
config and the KB config live in the same tracked file. The Blender side
gets the tools for free through the same MCP surface.

**Implemented 2026-08-27 (Phase 16).** As decided, with three findings
from the build:

- **The mirror was missing the manifest, and was not byte-exact.** A30's
  mirror never carried `manifest.json` / `AGENTS.md` (the index source
  this module assumes in-repo), and 337 of 401 mirrored files hashed
  differently from the manifest — 330 by exactly one trailing newline
  added by the mirroring tool, 7 by real extraction noise. Completed the
  mirror from Dropbox (hash-verified against Dropbox's own
  `content_hash`), stripped the newline only where doing so restored the
  manifest's exact sha256, and re-downloaded the 7 verbatim. The corpus's
  own `CLAUDE.md` was deliberately NOT mirrored: identical in size to
  `AGENTS.md`, and a `CLAUDE.md` inside this repo would be auto-loaded as
  directory instructions by coding agents — the imported corpus must
  never direct sessions (A30).
- **One genuine upstream drift, kept.** `00_meta/source-register.md` in
  Dropbox no longer matches what the corpus's own manifest recorded for
  it (regeneration ordering, most likely). The mirror carries the live
  file faithfully; `kb_status` reports exactly this one file as drifted
  with the rebuild.py fix line — the drift check's first real catch.
- **Config `max_tokens`, not `max_kb`.** The per-response budget knob
  landed as `[kb] max_tokens` (the same unit every tool argument uses)
  rather than the `max_kb` name floated above.

Measured (benchmarks/RESULTS.md): the paving-spec lookup with a citation
is 57,349 tokens by pasting INDEX.md + the file, 1,951 by
`kb_search` + one budgeted `kb_read` — 96.6% saved; the 4 `kb_*` tools
add zero always-loaded tokens (surface still 16 tools / 2,465).

## 2026-08-27 — A32: the mission broadens to any AI's token efficiency (owner decision)

The owner directed that TEE's stated mission and purpose no longer be
defined by Unreal Engine and Blender: the product exists **to help any
AI optimize its token usage and improve its work efficiency**. The two
DCCs become what they already are in the architecture — the first two
shipped adapters and the proving ground where every pattern is
implemented and measured — rather than the definition of the product.

Rationale: the kernel was tool-agnostic before this decision named it.
The state model (epoch/revision + diffs), checkpointed batching,
token-budgeted responses, progressive tool disclosure, project memory
(`tee_recall`/`tee_remember`), the extraction store, and the KB query
module none of them contain a DCC assumption; the DCC knowledge lives
entirely in the adapters. The six hard rules in CLAUDE.md were written
as general dogma from day one.

What changes: the mission statements only — README headline/intro,
CLAUDE.md "What this project is", `server/pyproject.toml` description,
and the `.mcpb` manifest description text (source-only; it ships with
whatever bundle is built next — no rebuild or version bump for a
wording change). Future integration proposals are judged exactly like
the existing ones: by measured tokens per completed task.

What does NOT change: the six hard rules; the adapter-first
architecture; the shipped 16-tool surface; and — deliberately — the
scope of every measured claim. 87.7% (Blender), 93.9% (UE), 96.6% (KB)
were measured on specific scenarios against specific baselines and stay
labelled that way; "helps any AI" is the mission, not a benchmark row.
No new runtime capability is added by this decision.

## 2026-08-27 — A33: first real task — TEE improves TEE (owner decision)

The owner set the product's first real task: turn TEE on its own
codebase, with TEE itself as the working session's co-pilot, and make
the product leaner, better- and more-efficiently-executing, more
polished, and concretely closer to commercial readiness — drawing on
all the knowledge the project carries.

Recorded shape: the campaign is driven by
`CLAUDE_SELF_IMPROVEMENT_SCRIPT.md` (root, sibling to the build
script), phases SI-0 baseline → SI-1 leaner → SI-2 execution/efficiency
→ SI-3 polish → SI-4 commercial readiness → SI-5 closing ledger.
Method: dogfooding — sessions run on TEE's own memory (`tee_recall`/
`tee_remember`), retrieval (`kb_*`), and discovery tools, and every
friction met while doing so is logged to `docs/SI_BACKLOG.md` as
improvement input. Nothing improves without a before/after measurement;
regressions revert; BENCHMARKS/RESULTS stay append-only.

Knowledge boundaries restated, not relaxed: `docs/research/` grounds
engineering decisions; `knowledge-base/` participates per A30/A31 only
(reference until re-verified at its cited source; `13_*`/`14_*`/`15_*`
never an API source). Owner-only calls (pricing, naming, store
submission, repo split, module deletion, mission changes) are written
up in the SI-4 gap list and stopped on, never made in-session.

## 2026-08-28 — A34: build web_lookup + the TEE-native code model (owner decision)

The owner directed the build of both researched capabilities: the
budgeted multimodal web_lookup (research 49, incl. the mitigation
section as hard requirements) and the TEE-native small LLM with a
dense code-and-debugging root (research 50 + addendum). Driven by
`CLAUDE_A34_SCRIPT.md` (root): Track W (fixtures → guarded fetcher →
extractor → tool + benchmark → media arms) and Track M (adoption
research → client seam → chore templates → benchmark verdicts →
LoRA gate → close-out). The research docs are the design of record;
the script is order + acceptance. Benchmarks decide every adoption;
the base-model download passes the owner gate; local endpoints stay
optional with proven degradation. Shortlist seeded from the
2026-08-28 open-research pass (Qwen coder 7B/14B Apache-2.0,
Ministral 3 dense Apache-2.0, DeepSeek-R1 distill MIT), final choice
made and license-linted at adoption day.

## 2026-08-28 — A35: the shrink campaign (owner decision)

The owner directed a second self-improvement campaign: TEE improves
itself into a **smaller, faster, more efficient package**, with TEE as
co-pilot, by the A33 method. Driven by `CLAUDE_A35_SCRIPT.md` (root):
P0 baseline ledger → P1 smaller (dependency/footprint diet — the
98 MB installed venv is the real target, not the sub-MB zips) → P2
faster (cold-start-to-first-answer, profiled per-tool latency, the
UV-unwrap hotspot) → P3 tokens round two (surface 2,028 baseline,
response leftovers, full battery bars hold) → P4 close-out ledger.
Scope guards: no new capabilities, no silent capability removal
("smaller" means lighter, not less), the research-48 matrix remainder
and all model/LoRA work stay out of scope. Regressions revert; the
benchmark bars are the floor.

## 2026-08-28 — A36: build the research-51 roadmap (owner decision)

The owner directed the build of all five recommended features from
research 51: F1 TEE Gateway (front any MCP server through TEE's
existing meta-tools — the UE-proxy pattern generalized, with a
fingerprint drift-firewall and the research-49 untrusted-content
posture applied to backend catalogs and results), F2 savings meter
(recap block + virtual report_savings, estimates labelled), F3
handoff pack (virtual tool, ≤500-tok portable brief), F4 adapter kit
(docs + template + contract tests, rehearsed cold), F5 kb_propose
(drafts to .tee/kb-staging only; the A31 mirror stays untouchable by
construction). F6 diagnostics stays staged. Driven by
`CLAUDE_A36_SCRIPT.md`; campaign law: the always-loaded surface does
not grow — any exception is an owner decision measured in tokens.
Not concurrent with A35 on the branch; whichever runs second
re-baselines. Benchmark bars are the floor; version recommendation
at close by semver (expected 0.4.0).

## 2026-08-28 — A37: the fabrication lane, merged with A36 (owner decision)

The owner directed building the research-52 fabrication lane AND its
integration with the A36 roadmap build into ONE campaign, driven by
`CLAUDE_A37_SCRIPT.md` (which supersedes `CLAUDE_A36_SCRIPT.md`;
research 53 is the integration map). The seams that justify merging:
the Gateway fronts the existing neka-nat FreeCAD MCP server so TEE's
own fabrication toolset stays thin (one-bridge rule, settled by a P0
probe with recorded pass/fail criteria — TechDraw-headless proof
included); the adapter kit is rehearsed by building the REAL
fabrication toolset from its docs alone; joinery_check lifts KB facts
through A30 re-verification and returns what it learns via
kb_propose; meter and handoff ride the fabrication sessions as live
fixtures. All A36 laws carry over (zero surface growth, untrusted
fronted content, bars as the floor). Home Builder 5.1 lands through
the EXISTING Blender adapter. A35 remains separate and never
concurrent. Expected close at 0.4.0; the owner tags.

**A37 addendum (owner, 2026-08-28):** the SI-B10 kb_hint fix (relevance
floor + optional local rerank, fixtured on the three recorded
misfires) is consolidated into the A37 script as phase P0-F — fixed
first, before campaign work begins.

**A37 addendum 2 (owner, 2026-08-28):** local-model switch profiles
consolidated into the A37 script as phase P0-S (after the kb_hint
fix, before campaign P0): `[llm] profiles` (q14b = 14B+a2 default,
q27b = 27B bare), virtual `llm_switch` with persisted choice, probed
availability, tradeoff-echoing reports, and the documented chat
phrase `TEE/Q14B` / `TEE/Q27B`. Serving stays the endpoint's job —
TEE refuses with the start command, never manages model processes.

**A37 addendum 3 (owner, 2026-08-28):** the P0-S model switch gains
two hard requirements — (1) single occupancy: managed stop-before-
start lifecycle (config-opt-in, owner's machine), old process
verifiably gone with RSS released before the new one starts, chat-
stack processes out of bounds, memory-pressure guard; (2) continuity:
the switch never stalls the conversation — synchronous stop, job-
token loading with ETA, one-line not-ready answers, in-flight chores
finish first, failed starts fall back automatically. q14b restated as
THE default (boot, missing state, and fallback-of-last-resort).

## 2026-08-29 — A38: shrink round two, post-0.5.0 (owner decision)

The owner directed a second optimization campaign with TEE as
co-pilot: faster, more efficient, smaller, leaner. Driven by
`CLAUDE_A38_SCRIPT.md` — A35's baseline→profile→diet→ledger method
pointed at the code A37 added (gateway call path, fabrication and
joinery lanes, chore prompts, kb floor, boards, virtual-tool flat
catalog, .tee state hygiene). Laws: A35's floor rows and every
benchmark bar (incl. the two new rows) are the floor; the 2,028/17
surface LAW stands; latency rows measured on q14b for parity; no new
capabilities, no silent removals; report_savings quoted on the
campaign's own closing session. Expected 0.5.1 unless shapes change;
the owner tags.

## 2026-08-29 — A39: the two-pillar mission, and the router build (owner decision)

The owner named what the product has become: "AI resource management
between cloud AI and local AI." Formalized as the two-pillar mission —
(1) make every exchange small; (2) run work on the cheapest capable
engine — refining A32, not replacing it: the protocol pillar still
carries the DCC savings with no local AI involved. Identity surfaces
reworded (README, CLAUDE.md, pyproject, mcpb long_description —
source-only, ships with the next bundle); measured claims stay scoped,
as with A32.

The build half: the adaptive router per research 55 (grounded in the
2026 cascade literature — 97–99%-of-strong-model results on
task-correctness labels, which TEE's deterministic verifiers supply
natively). Driven by `CLAUDE_A39_SCRIPT.md`. Router laws recorded:
TEE never calls a cloud API (escalation = budgeted return-to-client);
the owner's explicit switch is a ceiling the router never exceeds;
single-occupancy outranks routing (no swap thrash); no silent hops
(provenance + escalation rate in the meter); uncalibrated confidence
gates nothing. The R4 four-arm benchmark decides adoption — the
router earns its complexity or reverts. Expected 0.6.0; owner tags.

**A39 addendum (owner, 2026-08-29):** swap authority — the router may
trigger managed engine swaps (51 GB included) whenever the existing
memory guard says the hardware is capable. Single occupancy
unchanged; economic justification + anti-thrash hysteresis required
and metered; an explicit TEE/Q pin suspends roaming; the routed
benchmark arm carries its swap seconds in its own wall time.

## 2026-08-29 — A40: the Okongo reality-capture lane (owner decision)

The owner directed integrating Meshroom, CloudCompare and QGIS so the
next Okongo site visit (iPhone 17 Pro Max structure photos + drone
imagery) flows through TEE into as-built truth: updated architectural
drawings, refreshed UE landscape and house, and Blender work as
needed. Research 56 is the design of record; `CLAUDE_A40_SCRIPT.md`
drives the build. The honest hardware substitution is recorded there:
Meshroom is CUDA-blocked on Apple Silicon (kept as a pluggable
CUDA-box slot, never faked); the shipping engines are Apple
PhotogrammetrySession (structures, native), ODM (drone mapping,
arm64-probed), CloudCompare (registration + cloud-to-mesh deviation —
the lane's product), and QGIS via qgis_process + the gateway-fronted
MCP plugin. Laws: TEE reports deviations, the owner decides design
truth; the site datum is immutable; accuracy claims carry their
source's honesty band; every apply is checkpointed. The pre-visit
deliverables outrank all else: the capture-protocol doc (V1) and the
full dry run on existing site imagery (V6) — the trip must not be the
first test.

**A40 addendum (owner, 2026-08-29):** engines confirmed; the aircraft
is a DJI Mini. Encoded: rolling-shutter correction with the
model+mode-matched readout constant (mode pinned protocol-wide),
planned grid missions via Litchi/Dronelink with manual fallback,
stills only, SRT logs into the extract lane; PhotogrammetrySession
optimization defined as the measured quality-ladder rows on this
machine (preview = on-site validation, full/raw = finals), jobs +
provenance throughout. The owner's exact Mini model is recorded at
V0 start.

## 2026-08-29 — A41: router and reality capture merged into one campaign (owner decision)

The owner directed all proposed changes integrated into one script.
`CLAUDE_A41_SCRIPT.md` supersedes the A39 and A40 scripts (banners
added; phase content referenced unchanged — the A37 precedent).
Research 57 records the seams that justify the merge: ONE
machine-load ledger (reconstruction jobs are residents the router's
memory guard respects, and vice versa — the guard fixture runs both
directions); the capture lane's verifier-carrying chores are the
router's first real customers (static until R1 is green — the lane
never waits); the dry run's actual chores feed the four-arm
benchmark's mixed-difficulty set (real workload, not synthetic); and
the site-visit deadline rules the order — protocol and
ingest/reconstruct ship before router ambition, with router
fake-phases interleaving during long reconstruction jobs. Laws are
the union with zero relaxations. Expected 0.6.0; the owner tags.

## 2026-08-29 — A42: the kernel scheduler, merged into the grand campaign (owner decision)

The owner directed the research-58 kernel scheduler built AND
integrated with A41 into one script. `CLAUDE_A42_SCRIPT.md`
supersedes the A41 script (banner added; the reference chain A42 →
A41 → A39/A40 is the record). Research 59 maps the merge and its
prize: the shadow recorder lands the moment the load ledger exists
(K0, straight after R1), so the entire remaining campaign — chores,
reconstructions, gateway calls, the dry run — accumulates as REAL
workload traces; the dispatch policy goes live only after replaying
that recorded reality (the Borg/Omega/Firmament methodology), and
K4's mixed-load row judges it win-or-revert. Seams shipped once:
registry-form engine descriptors from R1, one meter schema with
scheduler columns reserved, QoS tags as annotations before they
become law. Two release gates: Gate A after T6+R4 (trip-ready,
recommend 0.6.0) and the final close (recommend 0.7.0). Scheduler
laws recorded: degrade-to-static always, shadow before live, greedy
before clever, zero new always-loaded tools. The site-visit deadline
still rules the order.
