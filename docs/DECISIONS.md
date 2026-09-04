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

## 2026-08-30 — A43: the pipeline lane, general by construction (owner decision)

The owner found the structural gap (SI-B15): TEE's 103 virtual tools
are scene-side, so a file-in/file-out build — his DiversionPlanner
basemap — could not be driven at all; the one op that worked,
`capture_terrain`'s `dem_diff`, worked because it is a DECLARED
headless operation. He then directed that the fix serve "other
projects and queries not just diversion planner." Research 60 is the
design of record; `CLAUDE_A43_SCRIPT.md` drives the build.

Shape: each project declares its own steps in its own tracked
`.tee/pipeline.toml` (the `[kb]`/`[pins]` precedent) — two kinds,
`produce` (artifacts → an artifact diff) and `query` (an answer →
the step's structured output, budgeted), which is what makes the lane
serve queries and not only builds. Declared inputs/outputs make steps
literal K-layer task-graph nodes, so the A42 scheduler dispatches them
with no new concepts. Laws: declared steps only, argv arrays never
shell strings, typed params landing as single inert elements, the
declaration owner-authored and project-tracked (`pipeline_init` may
draft, never authorize), answers not logs, and — the generality law —
no completion claim until a SECOND project's steps run through the
same lane unmodified. Expected 0.8.0; the owner tags.

**A43 addendum (owner challenge, 2026-08-30):** "declared steps only"
is superseded by "declared by default, ad-hoc through the owner's
gate." TEE's own `allow_code_exec` precedent applies: `[pipeline]
allow_adhoc` (default false, per project) permits `pipeline_adhoc`
from a LIVE HUMAN TURN only — refused for jobs, scheduled work,
chores, gateway-fronted calls and any fetched-provenance path, so
untrusted content still can never cause execution. An adopt flow
turns a successful ad-hoc run into a declared step (argv, inferred
inputs/outputs, measured cost) for the owner to accept. Scripted as
phase P0b.

## 2026-08-30 — A39 law amended: a paid hosted profile, pin-only (owner decision)

The owner directed Qwen-Max as an in-place chore engine, confirming he
knows it is hosted. Wired as `[llm.profiles.qmax]` in the machine-local
`.tee/config.toml` (gitignored): url = the owner's LiteLLM shim on
:4000, model = `claude-qwen-max` → Alibaba DashScope, `paid = true`.

**The law this amends, stated plainly rather than lawyered:** A39/
research 55 recorded "TEE never calls a cloud API; escalation means
returning the task to the client." Technically TEE still calls only
localhost — the shim makes the outbound call — but the effect is what
the law was protecting against: chore inputs (tracebacks, file
excerpts, KB passages, web extracts) LEAVE THE MACHINE and bill per
token. The letter survives; the intent does not. Recorded as an
amendment, not a loophole.

Guards that preserve as much of the intent as possible: qmax is never
the default (q14b stands, owner 2026-08-28); it is unmanaged, so
pinning it frees local RAM rather than consuming it and the
single-occupancy lifecycle does not apply; and it must never be an
automatic router escalation target — the router's ladder tops out at
return-to-client, which is free.

**Enforcement gap, filed as SI-B16 and not hidden:** `paid = true` is
declarative today. Nothing in code yet stops the router from selecting
a paid profile while unpinned, and the meter has no paid-call column.
Until SI-B16 lands, qmax is safe only as an explicit pin (a pin
suspends roaming by the A39 law).

## 2026-08-30 — A44: the trust kernel (owner question → architecture)

The owner asked how to integrate the pipeline's trust logic so TEE
serves MORE projects without becoming exploitable. The survey answered
it: TEE already carries four unrelated permission flags and
provenance concepts spread across eight kernel modules — it grew a
permission system without naming it, and capabilities now COMPOSE
(a fronted backend can steer a chore that could trigger a step).
Research 61 is the design of record: ONE decision point
(capability × grant × caller class, default deny), the taint law
stated once and propagated along the A42 task graph (untrusted inputs
⇒ no side-effecting capability; untaint only by live human turn),
progressive trust tiers whose read-only default is genuinely useful
(so breadth across projects costs no risk decision), `tee_trust` for
visibility, refusals that name the missing grant and the config file
actually loaded (closes SI-B17), audit logging, and a
behavior-identical retrofit of the existing flags — which finally
gives SI-B16's unenforced `paid = true` teeth. Guard against
over-engineering: TOML grants only, no policy language, no roles; if
it needs a DSL it is wrong. Built as the A43 script's new foundation
phase T-1, with the pipeline lane as its first tenant.

## 2026-08-30 — A43 working policy: defensive-intent framing + stakes-based model tiers (owner)

Fable sessions running the A43 script kept escalating to Opus 4.8. Root
cause: the work is genuinely security-sensitive AND research 60–65 read
like offensive material out of context (~30 injection/attacker/
exfiltration hits, no intent framing) — the escalation is the safeguard
working, so the goal is fewer FALSE positives, never evasion.
Integrated: a defensive-intent banner on research 60/62/63/64/65 (61
already had framing); a model-assignment law in the A43 script (fast
model for low-risk mechanical phases; careful model for the trust
kernel/taint/side-effecting phases; accept escalation there); and a
CLAUDE.md stance line. Explicitly NOT done and forbidden: disabling the
safeguard, routing around the classifier, scrubbing accurate technical
vocabulary to dodge detection, or using a local/uncensored model to
avoid review (the client-policy law binds this too). Honest labeling
and correct model choice, nothing more.

## 2026-08-30 — A45: TEE is a private tool; licence shape stops driving architecture (owner)

Asked directly, during the A45 fleet research: *"its just for me, keep it
simple."*

**What that settles.** Copyleft obligations (GPL, LGPL, AGPL) attach to
DISTRIBUTION — handing the software to someone else. A tool that runs only
on the owner's own machine and is given to nobody does not trigger them.
So the fifteen A45 resources are integrated on **engineering merit**:
in-process import where that is the cleanest and fastest, subprocess where
the tool is a CLI, HTTP where the thing is genuinely a server. Licence no
longer picks the seam.

**What this deliberately does NOT change.**

- `pyproject.toml` stays `license = { text = "MIT" }`. That is TEE's own
  code, which the owner wrote and can license as he likes. Nothing about a
  GPL dependency changes what TEE's own source is offered under while it
  is not distributed.
- Copyleft resources stay **optional extras**, never hard dependencies, and
  never vendored into the repo or the `.mcpb`. They are installed by the
  owner into his own environment. This costs nothing — it is the extras
  pattern A45 uses anyway — and it is what keeps the revisit cheap.
- Each such module carries a one-line licence note at the top. A note, not
  an architecture.

**The revisit trigger, recorded so it is not rediscovered the hard way.**
If TEE is ever published, sold, bundled for someone else, or **exposed to
other users over a network**, this decision expires and the copyleft
resources must be re-examined before that happens. The network case is
called out specifically because AGPL treats remote use as distribution —
that is the one that would bite a "just for me" tool the moment it grew a
shared endpoint.

Engineering opinion, not legal advice; the owner is the one who decides
what he does with his own software.

## 2026-08-31 — HEIC support, and what its licence actually is

TEE opened images with a bare `PIL.Image.open` in nine places across seven
modules, and Pillow ships no HEIF plugin — so every one raised
`UnidentifiedImageError` on the format the owner's iPhone shoots, while
`docs/okongo-capture-protocol.md` says photos arrive "HEIC/DNG/JPG as shot".
The extract lane was rejecting the camera it was built for.

Fixed at the root rather than per call site: `tee/kernel/imaging.py` is now
the single door (`open_image` / `save_image`), registering the HEIF plugin
once, idempotently and thread-safely, before the first open. A test walks
the AST of the whole tree and fails on any new bare `Image.open(<path>)`,
because reaching nine call sites is exactly how this became invisible.

**The licence, recorded now rather than discovered later.** `pillow-heif`'s
source is BSD-3-Clause, but its own bundled manifest says: *"License for
'pillow-heif' binary wheels: GPLv2, due to base library licenses"* (libheif
LGPLv3, plus GPLv2 codecs). Two things make this a non-issue here and both
should stay true: TEE is private and **not distributed**, so no copyleft
obligation is triggered; and it is an OPTIONAL extra the owner installs
themselves, so nothing GPL ships inside the `.mcpb`. If TEE is ever
distributed, this is the first dependency to re-examine.

## 2026-08-31 — estimated dimensions are allowed, under a named mitigation

Owner decision: the extraction discipline may estimate dimensions from
photographs where no measurement exists, **provided the accuracy can be
mitigated**. Previously the lane returned nothing, withholding a usable
number because it could not be a perfect one.

This EXTENDS the A40 law — "accuracy claims carry their source's honesty
band" — to a new source. It does not relax it. An estimate is produced only
when all three hold:

1. **A mitigation is named.** Something of known size, measured in the same
   pixels. No reference, no estimate.
2. **A band travels with it.** Reference tolerance and pixel-picking error
   propagate in quadrature into `band_mm`. An unstated tolerance is not a
   zero tolerance — it assumes 2%, so vagueness widens the band and the
   caller is never rewarded for withholding what they know.
3. **It cannot be read as measured.** The value lands in `estimated_mm`,
   never `mm`, alongside `estimated: true` / `measured: false`.

**TEE never supplies the reference's own size.** Asking a model what a
"standard door" measures is how a hallucinated 2032 mm becomes a structural
dimension — door leaves, brick courses and window modules all vary by region
and era. The caller supplies the size they know. The single exception is
ISO 216 paper, an international standard with exact millimetre sizes, which
makes an A4 sheet taped to a wall the cheapest scale reference on any site.

**The assumption that invalidates it all** is coplanarity: a scale in
mm-per-pixel holds only in the plane the reference sits in, and nothing in
the arithmetic can detect a violation. So `coplanar` must be affirmed by the
caller — a deliberate speed bump — and every result restates it, along with
the fact that a drawing or survey outranks the estimate where one exists.

Tool: `ex_estimate`, read tier via the `ex_` family prefix.

## 2026-08-31 — the PDF lane, and its licences

Owner asked for a feature to write and edit PDFs. Two libraries adopted
into a new `[pdf]` extra:

- **fpdf2 — LGPL-3.0.** Composition. Already present in the dev dependency
  group (used inline to build the AURA-X chair PDFs), now promoted to a
  real extra so a user can reach it.
- **pypdf — BSD-3-Clause.** Page surgery and overlay merging.

The LGPL matters only on distribution, and TEE is private and not
distributed — the same position recorded for pillow-heif, and the same
caveat: **if TEE is ever distributed, fpdf2 is the first dependency to
re-examine.** Neither ships inside the `.mcpb`; both arrive when the owner
installs the extra.

**In-place text rewriting is refused, deliberately.** A PDF stores
positioned glyph runs rather than paragraphs, so re-flowing them corrupts
layout in a way that opens without complaint and is silently wrong. The
lane offers `stamp` (an overlay, honestly named) and `pdf_compose` (a new
document) instead, and the refusal states the reason and both options. This
is the same principle as the A47 rule that a description is never dressed
up as sight: the tool declines what it cannot do correctly instead of
approximating it.

## 2026-08-31 — Godot joins as a headless adapter (A49)

Owner: *"integrate godot with TEE headlessy (godot is used for game
designs)"*. Godot 4.7.2, **MIT**, installed via brew cask; nothing is
vendored into TEE and nothing ships in the `.mcpb`.

**Adapter protocol, not a new tool family.** Godot honours `Adapter`, so
the always-loaded surface stays at 17 tools and the existing scene/batch/
diff/checkpoint machinery drives it. A game engine that needed its own
always-loaded tools would have cost the invariant this project is built on.

**Declarative commands, with the escape hatch behind its own door.** The
bridge accepts an enumerable op set (`add_node`, `set_props`,
`remove_node`, `save_scene`, `load_scene`) and refuses anything else by
name with the allowed list. Arbitrary GDScript is `{"type": "gd"}`, gated
on `exec-code` — the same split the trading lane uses, for the same reason:
a set of things that can be enumerated can be reasoned about.

**Rendering is refused, with the measurement behind it.** Headless Godot
cannot render under any driver tried (vulkan, opengl3, dummy all yield a
null viewport texture). `capture()` raises with that finding rather than
returning a black frame, which would look like an answer. An opt-in
`capture_windowed()` renders with a real display server and is documented
as opening a window on the owner's screen — never automatic.

**Script errors are counted rather than inferred.** A Godot game whose
`_ready` raises still exits 0. `run_scene` reports `ok` only when the exit
is clean AND no `SCRIPT ERROR` lines appeared, because the exit code alone
would pass a broken game.

## A53 — the garment lane (2026-09-01)

**Build the solver; do not adopt the paper's.** GarmentCode/PyGarment is MIT,
but GarmentCodeData drapes through a fork of NVIDIA Warp under the **NVIDIA
Source Code Licence — non-commercial**. The best-documented open garment
pipeline in the world therefore cannot ship, and copying its stack inherits
that silently. seamkiln writes its own XPBD; mainline Warp (Apache-2.0) and
C-IPC (Apache-2.0) stay available as backends.

**Anny, not SMPL — and plain `anny`, not `anny[smpl]`.** SMPL and SMPL-X are
licensed for non-commercial research; Anny is Apache-2.0 over CC0 MakeHuman
assets and spans infants to elders. The trap is inside the answer: Anny
declares `smplx` under an optional extra, so `anny[smpl]` pulls the very
licence Anny was chosen to avoid. seamkiln declares plain `anny`,
`load_topology` refuses the smplx topology by name, and the gate tests both.

**The licence law is a test, not a note.** `test_licences.py` fails the build
if `triangle`, `meshpy`, `smplx` or a non-commercial licence string enters
seamkiln's dependency closure, and the failure names the permissive
replacement. Two of its cases exist only to make the gate fail on purpose,
because a gate nobody has seen fail is a gate nobody knows is wired up.

**The solver backend was chosen by measurement, and the GPU lost.** numba on
a **four-thread** pool beats torch-MPS at every garment size (5.2 vs 13.9
ms/frame at 30k particles; 8.7 vs 20.1 at 120k) and beats Blender's own cloth
by 10–236×. More threads is slower: at 5k particles one thread beats eighteen
by 8.7×, because the fork/join barrier around each of a frame's 144 parallel
regions scales with pool size. `numba.set_num_threads` cannot fix it — it
masks threads without shrinking the barrier — so the pool is sized by an
environment variable before numba is imported.

**Compliance is relative, not the textbook alpha.** With an absolute XPBD
compliance the solver's denominator is `w_a + w_b + alpha/h²`, and a
garment's inverse masses run to ~1e4 while any physically plausible alpha
lands near 1e-6 — so every fabric rounds to inextensible. Measured: denim and
chiffon draped identically. Compliance now softens the correction relative to
the mass term, which is an honest simplification that preserves the ordering
and the ratios that matter, and the fabric card carries a `tier` flag saying
the stiffnesses are solver constants rather than measurements.

**Friction is Coulomb, not viscous drag.** Removing a fixed fraction of
tangential motion slows a slide without ever stopping one; over 2,400
substeps the surviving 65% walked the garment off the body a fraction of a
millimetre at a time. Coulomb's static regime — tangential motion within
μ×(normal correction) cancelled outright — is what lets a shoulder carry a
garment's weight.

**Two acceptance numbers, because one was gameable.** "Zero body
interpenetration" is satisfied perfectly by a garment lying on the floor, and
was. Every drape reports `contact.worn` alongside `penetration`.

**The outline is the sew line.** Seam allowance records a number rather than
replacing the outline with the mitred cut line: a mitred offset re-tags
corners by angle, so a panel's edge count changes and every seam naming a
later edge points past the end of the list. The sew line is also where sewing
happens and the length `true_up` must match; the cut line is derived, and the
DXF writer puts it on layer 1 with the sew line on layer 14, which is what
ASTM expects anyway.

**One command model, every client.** A `Session` holds the garment, every
mutation is a `Command`, and the Qt shell, a script and the TEE adapter all
drive the same one. The adapter is a translation layer, not a second
implementation; checkpoints are the command history and restore replays it.
That is what makes "save script" a fact about the design rather than an
export feature — and it is the inversion of the incumbents, whose Python API
runs inside the app on an enterprise tier.

**A rendered image, not a Qt viewport.** seamkiln already renders through
Blender; a second renderer inside the GUI would be a worse picture and a new
surface to maintain. The cost — you cannot orbit it — is stated in the
module, and a `QOpenGLWidget` viewport is named as the next step.

**The model's eye is advice.** `sk_look` renders the drape and asks the local
vision model what it sees, labelled `kind: advice`, never allowed to fail a
build. Seam closure, penetration and ease are decided by geometry in
`sk_fit`. This is A51's finding, applied before it could bite again.

## A66 — the mechanical CAD lane: `partkiln` (2026-09-02)

Owner directive, verbatim: *"create an autodesk inventor alternative that runs
headless with TEE and is optimized for ai engines"*; mid-turn *"use TEE"* and
*"TEE/QMAX"*. Plan of record `CLAUDE_A66_SCRIPT.md`; design of record research
doc 68 (P6). Rulings, each with the evidence that decided it:

**OCCT through the OCP wheel is the kernel; nothing is written from scratch and
FreeCAD is not the engine.** Measured on this Mac (2026-09-02): boolean cut +
exact volume 17 ms, fillet 13 ms, hidden-line front view 6 ms, STEP AP242
write 13 ms / read 6 ms with the volume identical, GLB 7 ms; a 100-hole plate
builds in 0.09 s as one n-ary cut and its B-rep fingerprint is identical in two
fresh processes. `freecadcmd` 1.1.3 imported its modules in 0.38 s but the
headless sketch+TechDraw probe ended "Application unexpectedly terminated";
TechDraw SVG/PDF is GUI-bound upstream (#5710); the app embeds OCCT 7.8.1. The
A37 FreeCAD adapter stays what it is.

**The kernel talks to OCP directly — never `import cadquery`, never
`build123d` in-process.** `cadquery` imports casadi (LGPL-3.0-or-later)
eagerly through its assembly solver and links nine VTK dylibs; `build123d`'s
next release adds `bd_materials`, which carries no licence at all. Both are
patterns to read, not dependencies. The production wheel is
`cadquery-ocp-novtk` in a sidecar venv; the dev venv keeps the `cadquery-ocp`
it already has (both wheels ship the top-level `OCP/` package and clobber
each other).

**Own solvers on scipy; py-slvs is a dev-time oracle only.** `py-slvs` (the
SolveSpace wheel TEE's `physical/sketch.py` uses under `[physical]`) is
GPL-3.0 with no linking exception; the kernel package is MIT and shippable
(owner, 2026-09-02: "shippable, like seamkiln"), so the 2D constraint solver
and the 6-DOF assembly solver are `scipy.optimize.least_squares` with DOF
from the Jacobian rank. TEE's own lanes keep py-slvs; partkiln never imports
it.

**The licence gate is a test with an SPDX allowlist, and OCCT is its one
named weak-copyleft exception.** Installed metadata is inconsistent (scipy,
ezdxf and trimesh carry no `License-Expression`), so the gate reads the
expression, then the Trove classifier, then a free-text alias table, and
fails only when all three are empty. `KNOWN_PAYLOADS` names both OCP wheels
as `LGPL-2.1-only WITH OCCT-exception-1.0` and the NOTICE with the
"prominent notice" the exception demands is asserted present. GPL/AGPL and
non-commercial terms are banned in-process; `fpdf2` (LGPL-3.0-only) lives in
an optional `[pdf]` extra exactly as TEE's own PDF lane does.

**Standards data comes from Apache-2.0 and BSD sources with provenance on
every file.** Clearance/tap/drill holes and ISO 4762/4014/4017/4032/7089
fastener tables from `bd_warehouse` (Apache-2.0), ISO 261 pitches from
`threadlib` (BSD-3); FreeCAD's Fasteners tables (GPL-2), BOLTS (GPL-3) and
Wikipedia tables (CC BY-SA) are never vendored; the sheet-metal K-factor
default 0.44 is declared as this kernel's choice inside the cited 0.3–0.5
range, not attributed to a source that does not state it.

**Millimetres on the wire, unit strings accepted, glTF in metres and Y-up by
the writer.** Bare numbers are the document unit and the diff says so once;
`"0.5in"`/`"90deg"` are accepted everywhere; `strict_units` is opt-in. The
GLB writer sets `XCAFDoc_LengthUnit = 0.001` AND the Z-up input coordinate
system — measured: without the first a 10 mm part is 10 m, without the second
it arrives lying on its side.

**No `pk_` family row in the trust table.** Three of the fourteen `pk_*`
tools write files and two mutate the document; every one is tabled
explicitly (the `cad_`/`trade_` rule).

**Headless first; the GUI is a later phase.** Owner, 2026-09-02. The Qt shell,
when built, is a client of `partkiln.document` exactly as seamkiln's is.

**CI gets a `kiln` job on `[brep]` and the server job stops installing the
1.3 GB `[cad]` stack** (`uv sync --all-extras --no-extra cad`, uv 0.12.5).

**Rulings learned while building (2026-09-02, P0–P3), each pinned by a test:**

- **A cut never glues.** `BRepAlgoAPI_Cut` with `SetGlue(GlueShift)` on
  intersecting tools returned the UNCUT plate with `IsDone() == True`; glue
  modes are only for fuses of touching copies and are reachable only behind
  an explicit `touching=True`. Law 11 (`pk_no_effect`) guards every boolean.
- **Counts are unique sub-shapes.** `TopExp_Explorer` visits a shared edge
  once per owning face (F5: 624 visits, 312 edges); every count on the wire
  comes from `TopExp.MapShapes_s`.
- **Histories are built by hand.** Only the boolean builders, the hole
  feature and `ShapeUpgrade_UnifySameDomain` expose `History()`; every other
  builder answers `Generated/Modified/IsDeleted` per sub-shape, and
  `BRepTools_History` is queried with `IsRemoved` (there is no `IsDeleted`).
  A filleted edge is both deleted and the parent of its fillet face, so
  `Generated` is read before `Remove`.
- **The seam is filtered, never filleted.** `dir=Z` on F1 matches five raw
  edges; OCCT accepts the cylinder seam in a fillet and generates nothing.
  Selectors exclude seams by default and say so; an edge whose `Generated`
  is empty is reported as failed for that edge.
- **The assembly solver is `dogbox`.** scipy 1.17.1 `trf` stalls on a
  rank-deficient Jacobian and MINPACK `lm` drifts along the free-rotation
  null space (θ_z = −2π, later NaN); `dogbox`'s exact Gauss–Newton step is
  the minimum-norm `lstsq`. Rotation vectors are wrapped to |θ| ≤ π because
  the left Jacobian is singular at 2π. A conflict is charged to the LATER
  constraint by incremental re-add, so its residual reads the whole 5.000
  rather than a 2.5 split.
- **The exact fit is contact, not interference.** OCCT 7.9.3's Common of a
  Ø10 pin in a Ø10 hole is empty at fuzzy 0 and stays empty under 1e-9 mm
  pose noise, so `FUZZY_MM = 0` and contact is `distance ≤ 1e-6`.
- **The K-factor default is a choice, not a citation.** 0.44 sits inside
  the cited 0.3–0.5 range; no standard fixes K; DIN 6935's `k` is a different
  quantity; production parts pass `k` or a bend table.
- **Volumes ride the wire at 3 dp** (D7 said 2): the fixture pins need the
  third place, and a diff that rounds a −34.336 mm³ fillet to −34.34 hides
  the digit the test asserts.
- **A cosmetic thread changes nothing.** It is stored on the feature and
  the fingerprint is bit-identical with and without it (Law 18).

**Rulings from the adversarial audit (P4–P5 close, 123 agents, 31 findings
confirmed and 8 killed), each pinned by a test that fails on the old code:**

- **A check that samples a grid is not a check.** `min_wall` cast its rays
  from the centre of each UV cell, so a 0.600 mm web between two holes was
  never sampled and `check_spec` PASSED it against a 1.5 mm limit. The
  measurement now samples the interior on a bounded lattice and reports the
  worst point with its coordinates. A safety check that can miss is worse
  than no check, because it is believed.
- **A failed regen leaves the document as it was.** A rebuild that threw
  part-way used to leave the document holding half-built parts with the old
  script; regen now builds into a scratch document and swaps it in only on
  success, exactly as a batch rolls back (Law 16).
- **A replay rebuilds against the units it recorded.** Regen read
  `doc.units` as it stood today, so a script written in inches replayed as
  millimetres after a `set doc units=mm`. The unit in force at each command
  is part of the command.
- **A refusal keeps the door open.** Every `pk_*` refusal added by the audit
  names the measured value, the limit it broke and the one edit that fixes
  it; a refusal that only says no was treated as a defect and rewritten.

## A67 — the point-cloud scan-prep lane: `pc_*` (2026-09-03)

Owner directive: the A67 brief (now `CLAUDE_A67_SCRIPT.md`), then mid-turn
*"use TEE"* and *"TEE/QMAX"*, then *"COMPLETE ALL PHASES WITHOUT MY INPUT"*.
Design of record research doc 69; user guide `docs/pointcloud-lane.md`.
Rulings, each with the evidence that decided it:

**`plyfile` is banned and the lane uses trimesh instead.** The brief listed
`plyfile 1.1.5` as a core dependency. PyPI's own classifier for it reads
`License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)`
(fetched 2026-09-03). TEE ships MIT. This repo had already established the fact
(research doc 43, PyPI-verified), already banned it
(`voxkiln/src/voxkiln/license_lint.py:20`), and already performed vendor surgery
on the TRELLIS.2 fork to excise it — and doc 43's own recorded replacement is
"replace `.ply` IO with trimesh or drop". It was re-verified here rather than
carried on trust, because a dependency table trusted once is trusted forever.

**`pye57` and `open3d` are dropped, and NOT on licence grounds — on weight.**
Both are MIT. `pye57` builds libE57Format, and CloudCompare 2.13.2 — already a
lane dependency — ships `libQE57_IO_PLUGIN`, so E57 is one conversion away and
refuses honestly when CloudCompare is absent. `open3d` is ~400 MB for ICP alone,
and there is no ICP in this lane; `test_a46_no_heavy_imports.py` already bans
that exact shape (vtkmodules 592 MB, torch 505 MB, OCP 225 MB). Recording the
distinction matters: calling a weight decision a licence decision would corrupt
the licence record.

**`scipy` is declared explicitly.** It imports in `server/.venv` but appears
nowhere in `server/pyproject.toml` — it arrives transitively via skfolio /
PyPortfolioOpt / scenedetect. `cKDTree` is load-bearing for normal estimation,
so a clean `uv sync` that dropped a carrier would have broken the lane silently.

**No `pc_register`, and `pc_merge` wraps rather than reimplements.**
`capture/align.py:86 register_icp()` already ICP-registers through CloudCompare
with a refusing RMS gate and a 7-DOF degeneracy guard, and A42 T6 paid for that
guard the hard way. A second registration answer that can disagree with the
first is worse than none. So `pc_merge` (second pass, 2026-09-04) calls it.
What the wrapper is allowed to add is only what the caller cannot get from the
existing tool: **a frame it names itself** — both clouds are shifted by the
datum's centroid before being written out, so a site cloud in UTM is not
silently re-centred by CloudCompare's own global shift and the returned matrix
is usable — and **a second opinion on the fit**. CloudCompare's RMS is over the
correspondences it chose; `pc_merge` also reports the fraction of each source
that landed within 50 mm of the datum and the RMS within that overlap. Measured
on the Okongo cloud split in two and one half disturbed by 4° and 145 mm: RMS
38.9 mm, overlap 0.408, overlap RMS 10.0 mm. Only the pair is a verdict — the
same 38.9 mm at 4% overlap would be two scans of different rooms.

**`pc_ortho` splats each point at its measured footprint, not one pixel.**
Asked for 10 mm pixels on a cloud sampled every 30 mm, a point-per-pixel render
is 64% white and reads as a texture rather than a surface — the same complaint
the drafting depth rasters drew from the owner. The dot width is derived from
the cloud's own median spacing (`dot_px`, capped at 9), so nothing is invented:
the sample is drawn at the size it actually represents. Coverage went 64% → 92%
on the real cabinet wall, and the vertical joints became lines.

**A crop drops the baselines it cropped away.** A crop moves no point, so at
first reading a carried measurement is still true. It is not: the *snap* is
what changed, and the usual reason to crop at all is that the snap found the
wrong face. On the Okongo run `pc_crop` handed a wrong-face reading to the very
cloud that had been made to fix it, and `pc_control_verify` then reported drift
from a number measured on geometry the cloud no longer contained. The rule is
now positional: a baseline whose two picks both survive the region test rides
along untouched; one whose pick was removed is dropped with a note telling the
caller to re-measure. This is the third time this lane has learned the same
lesson (`pc_scale_apply`'s stale baselines were the second) — **a derived
cloud may inherit a measurement only where the measurement is still true of
it.**

**`pc_control_add(horizontal=True)` measures the plan distance.** A tape across
a room is held level. The 3D distance was the only option, and on the Okongo
scan there is no single height where both faces of Room 01 are clean — the
south side is a cabinet front below 930 mm and the north side is a curtain — so
the two picks must sit at different heights and the straight distance between
them is a diagonal, 90 mm long on a 3.95 m room. Default stays 3D so nothing
silently changes; the response says which was measured.

**`pc_crop` reports when a region reaches past the cloud.** Found by driving
the lane on the real scan: `z_range: [0.05, 2.35]` returned the top half of the
Okongo bedroom, because PLY origin-shifts on write and that cloud's floor sits
at z = −1.36. The crop was correct and the request was wrong, and nothing in
the response distinguished the two. One line now does. The general rule this
records: **a tool that can answer a different question than the one asked must
say which question it answered.**

**No `("pc_", …)` family row in the trust table; every tool tabled
individually.** Same lesson the `cad_` and `trade_` comments in `trust.py`
already record: a prefix default silently admits whatever is named next, and
nearly every tool in this lane writes a file. `pc_stat` and `pc_control_verify`
are `read-compute`; the other eight are `write-artifacts`.

**`pc_control_check` was renamed `pc_control_verify`.** "check" is a common
English verb and scores 3 points on a name match, so `pc_control_check` ranked
first for the deliberately-vague query "check the drawing" and pushed
`ex_estimate` from rank 5 to rank 6 — a real recall regression caught by
`test_search_budget.py`. Four candidate names were scored against the whole
case set before choosing. A new lane does not get to claim another lane's
vocabulary just by being newer.

**The research doc is numbered.** `docs/research/69-pointcloud-scan-prep.md`,
not the unnumbered filename the brief gave: every file in that directory is
`NN-slug.md`, and `00-index.md` carries a row per doc.

**The scanner app is read, not assumed.** The brief said to digest the formats
"as 3D Scanner App actually writes them"; the owner confirmed (2026-09-03) that
this names no particular product — it is a generalisation for whatever iPhone
scanner produced the export. That makes the requirement stronger, not weaker:
with no app specified there is nothing to special-case, so `pc_open` reports the
writer, SRS and point format it actually finds in the file. The field protocol's
Polycam / RealityScan (`docs/okongo-capture-protocol.md` §3) is context for what
such exports contain, not a target the reader is built against.

Rulings learned while building, each pinned by a test:

**The floor is the LOWEST dominant horizontal plane, not the most populous
one.** In a box room the floor and ceiling have the same inlier count to within
noise, so a count-first selection is a coin flip — the first implementation
levelled onto the ceiling and hung the room underneath it. The lane now collects
every qualifying plane and takes the lowest. (`test_level_puts_the_room_above_
its_floor_not_below_its_ceiling`.)

**Normals must be estimated in 3D, and yaw must come from the full-height wall
band.** Measured: a 2D XY-neighbourhood estimator kept 6 of 40,000
neighbourhoods and returned **26.35°** of error, because 12 mm of noise on a
15 mm grid is isotropic in projection. In 3D: k=20 → 0.073°, k=80 → 0.040°,
k=160 → **0.004°**. And a 50 mm slice, as opposed to the 0.4–2.3 m band, gives
**1.289°** against a 0.5° gate — so the slice and the yaw are different queries
over different point sets, and sharing their estimator would look like a tidy
simplification and be wrong. Both pinned.

**PLY export is always origin-shifted.** trimesh writes `property float`
(float32) in every encoding. Measured error against absolute coordinates: local
0.000 mm, site-ENU 0.004 mm, **UTM 249.991 mm, ECEF 249.995 mm** — and ODM's
`odm_georeferenced_model.laz`, the artifact this lane exists partly to read, is
georeferenced by construction. The offset goes in the sidecar.

**LAS scale is 1e-4, not the conventional 1e-3.** LAS stores int32 ordinates, so
the file size is byte-identical across scales (6,800,375 B at every scale
tested). 1e-3 costs 0.5 mm of quantisation — a quarter of the ±2 mm acceptance
budget — for nothing. 1e-4 costs 0.05 mm and still addresses ±214 km.

**Fit residual is reported as median, with max labelled.** Per-segment max sits
at ~2.9σ of the noise floor: arithmetically right, and read as a failure by
everyone who sees it.

**The control snap radius is a sample-size floor, not a taste knob.** A 0.15 m
patch (~310 points) left a 4 m baseline 2.0 mm long = 503 ppm, failing the
500 ppm gate; 0.25 m (~860 points) lands at 78 ppm. The plane's standard error
goes as σ/√n, so the radius now grows until it holds enough points — a sparse
scan needs a wider ball than a dense one for the same accuracy.

**Emitting `tee-plan/1` facts from slice segments is deferred, not forgotten.**
It would light up `ex_export_ifc` and `bl_build_from_plan` for free. It is also
exactly the interpretation non-goal #1 forbids: the segments are geometry, and
calling them walls is a judgement. It needs its own decision record.

## A67 addendum — what the first real scan changed (2026-09-03)

Owner: *"Use the zipped test scan file in the Okongo Dropbox folder, and use it
to create a detailed architectural plan and 3d drawing"*. Evidence in research
doc 69 §7b; drawings in `~/Downloads/Okongo-Scan-Test/`.

**The synthetic fixture was not a sufficient gate, and this is the lesson.** One
clean rectangle has no wall thickness, no second room, no doorway and no
furniture. On the real capture (1,520,736 points, two rooms) `fit_lines`
returned **35 segments totalling 133 m of wall inside a 5 x 5 m room**, running
4 m diagonals through a bed and finding the same partition six times — while
every synthetic acceptance test stayed green. A fixture that cannot fail is not
a gate. `server/tests/fixtures_pointcloud.py` now also carries `make_two_rooms`,
with the thickness, doorway and clutter the first one lacked.

**A wall is continuous, and that is a fact about buildings, not a tuning knob.**
Runs are split at gaps over 350 mm — which is simultaneously the correct
treatment of a doorway — and must fill at least 65% of the 100 mm bins along
their own length. This alone took the real scan from 133 m to 42.9 m.

**A surface found twice is one surface; wall thickness is not.** Near-coincident
parallel runs within 80 mm are merged best-supported-first, while the two faces
of a 260 mm partition survive as the two genuine surfaces they are.

**`fit="ortho"` is a declaration by the caller, not an assumption by the lane.**
After `pc_level` removes the azimuth, every wall in a RECTILINEAR building is
axis-parallel, so the mode finds walls as spikes in the histogram of
perpendicular offsets — what a flat vertical surface actually is — and a
diagonal never becomes a candidate. It would be the wrong choice for splayed or
curved walls, which is why it is opt-in and why `fit="lines"` remains the
default. On the real scan: 20 clean surfaces, 30.7 m.

**The lane still does not produce drawings, and the deliverable respected that.**
A67 non-goal 2 stands. The three A3 sheets issued to the owner were composed by
a script OUTSIDE the lane, from the lane's geometry, under one rule stated on
every sheet: grey is measured, black is fitted.

**`pc_report` returned UNVERIFIED on the real scan, and that was the most
valuable thing it said.** No tape measurement was supplied, so every dimension
in those drawings is Apple's ARKit solution and nothing else. The verdict is not
a limitation of the lane; it is the lane doing its job.

## A67 addendum 2 — a drafting-standards critic for the drawings (2026-09-04)

Owner: *"Create a feedback loop that critics these drawings to real world
technical drafting standards and makes corrections"*. New package `drafting/`,
standalone at the repo root on the seamkiln/partkiln/voxkiln precedent.

**The critic reads the specification, not the PDF.** A finding has to be
actionable: `critique` names a field, the corrector edits that field, the sheet
is redrawn from the corrected data. Critiquing a rendered PDF would let you see
a fault and leave no handle to fix it. That is what makes the loop close.

**But a second tier was unavoidable, and the first sheet proved why.** Tier 1
passed the re-issued SK-01 with zero findings while a section cut line ran
straight through two room names. Conformance and legibility are different
properties, and collisions are a fact about the plot, not the data. Tier 2
measures drawn artists after the figure exists.

**Provenance is attached to every rule, because the source is second-hand.**
The numbers come from TEE's KB entry `arch.drawing_documentation`
(`confidence: medium`), which cites SANS 10143 through public transcriptions
and has NOT been checked against the purchased standard. Each rule therefore
carries a `firmness` of `sans10143`, `convention` or `house`. CLAUDE.md's rule
that the KB grounds nothing on its own is the reason this field exists rather
than a footnote: 15 rules are attributed, 5 are not, and the module says which.

**The corrector will not invent a value a human owns.** An unset checker prints
`— NOT SET —` in red. A drawing that looks signed off and is not is worse than
one that visibly is not, so the correction for a missing signature is to make
the absence louder, never to fill it.

**Every edit is reported.** Corrections come back as findings marked
`autofixed`, so the full list of changes made on the owner's behalf is readable
in one place. Nothing is silently improved.

Rulings the build learned, each pinned by a test:

**The critic and the corrector must share one definition of a tag.** The critic
read `SECTION A-A` as tag `A-A` while the corrector wrote `A`; two REJECT
findings survived a loop that reported itself converged. One `section_tag()`
now serves both — and its own test then caught that it split on the ASCII
hyphen only, so an en-dash title would have reproduced the same bug.

**A false positive costs more than a missed check.** Three were found and fixed
against real sheets: `Annotation.get_window_extent` includes the leader arrow,
so a 2 mm label with a 35 mm leader measured 35 mm tall; an Axes paints its own
white background, which "covered" every label inside it; and text with an
opaque backing patch is a dimension figure sitting in a break in its own
line — correct drafting, not a collision. Each would have trained the reader to
skim the findings.

**Text needs clearance, not merely non-intersection.** A caption 0,08 mm off a
soffit line reads as sitting on it, so boxes are inflated 0,6 mm before being
tested against graphics.

**On the Okongo set: 77 findings, 0 after the loop.** The two blocking ones
were real — both sections were orphans, cited on SK-02 as "cut lines shown on
SK-01" while SK-01 showed none. Ten pieces of text were below the 2,5 mm
legible minimum, some at 1,98 mm. The plan also moved from 1:25 to 1:50,
because 1:25 is an enlarged-plan scale and this is a GA plan.

## A67 addendum 3 — line clarity, on the Revit model (2026-09-04)

Owner: *"Improve clarity and legibility of lines as per industry standards and
practices and inspired by Revit"*.

**A line weight is a CATEGORY resolved against the view scale, not a
millimetre.** This is the idea worth taking from Revit, and the one the first
issue lacked: Revit stores a weight index per category and looks the printed
width up in a table whose columns are view scales, so the same wall is heavier
at 1:20 than at 1:100 with nobody editing it, and a set stays consistent
because the weight lives on the category rather than on each object.
`resolve_pen(category, scale, cut=)` implements the model; every resolved width
lands on the SANS pen set, and a test asserts that across every category and
every preferred scale. **The index-to-millimetre values are this module's own
(`firmness: house`)** — Revit's shipped table is a different set of numbers and
is deliberately not reproduced.

**Cut outranks projection, always.** Every category carries two weights and a
test asserts `cut >= projection` for all of them, which is the KB's "the cut is
black, the beyond is grey" made mechanical. The survey stipple is halftoned so
it reads as background evidence rather than competing with the drawing.

**Dash patterns are defined in PAPER millimetres**, as Revit defines them, so a
chain dash reads the same length whatever the view is scaled to.

**Poché is drawn only where the cloud proves a solid.** Filling the wall body
between two faces is the single biggest legibility gain available on a plan,
and pairing two faces into one wall is exactly the inference A67 non-goal 1
forbids guessing at. So it is not guessed: two faces are paired only when the
band between them holds almost no returns. A scanner sees both sides of a wall
and nothing inside it, so an empty band is the signature of a solid and a band
full of points is two surfaces with a gap. On the Okongo scan this produced
**one** body out of twenty faces, and that conservatism is the correct answer:
an interior-only scan never measured the outer face of the enclosing walls, so
their thickness is unknown and the sheet says so rather than drawing an assumed
230 mm.

**Corner closure extends, never truncates, and never reaches beyond 450 mm.** A
fitted face is evidence that a surface exists along its own length; stretching
one across a room to meet something far away would be drawing a wall nobody
measured.

**A body shorter than 300 mm is not drawn.** Found by a test the code failed: a
100 mm stub against a 3 m wall satisfied the overlap fraction and became a
"pier". At 1:50 that is 6 mm of paper communicating nothing.

## A67 addendum 4 — side views and a drawn axonometric (2026-09-04)

Owner: *"Do a side view and 3D as well"*. New sheets SK-03 (internal
elevations) and SK-04 (axonometric); the earlier point-cloud sheet renumbered
SK-05. New module `drafting/views3d.py`, 10 tests.

**A side view of an interior-only scan is an INTERNAL elevation, not an
exterior one.** The scan never saw the outside of the building, so there is no
honest exterior elevation to draw. Each of Room 01's four walls is instead
projected square-on with everything within 750 mm in front of it, which is
standard practice for a bathroom or kitchen elevation set and is fully
supported by the data.

**The axonometric is a drawing, not a render — and the difference is the
discipline.** Every fitted face is extruded over the vertical extent that ITS
OWN returns cover. Measured on this scan, every principal face runs floor to
ceiling with ~100% height coverage, but two do not: one starts at +0.22 and one
at +0.69. Extruding everything to 2.604 would have drawn two walls that are not
there. Heights come from the 0.7/99.3 percentiles so a single stray return
cannot decide a wall's height, and a face with under 200 returns is not drawn
at all. 20 faces became 16 solids.

**Painter's order IS the hidden-surface removal.** Opaque solids drawn back to
front occlude correctly with no visibility computation, which is why the sheet
reads with line weights rather than pixels.

**SK-04 is the interpretation; SK-05 is the evidence.** Keeping both, adjacent
and numbered in that order, is the honest presentation: the drawn axonometric
is what the fitting believes, and the point-cloud renders are what was actually
measured. Neither is offered as a substitute for the other.

**Elevations must not come out mirrored.** Looking at the two opposite walls of
a room flips the along-axis, so `elevation()` negates it for two of the four
cases and a test pins it. A mirrored elevation is a drawing that is confidently,
silently wrong.

## A67 addendum 5 — the second scan, and two bugs it exposed (2026-09-04)

Owner: *"there is a lidar obj file in the okongo dropbox folder called test2 to
refine the measurements further"*. Comparison written to
`~/Downloads/Okongo-Scan-Test/second-scan-comparison.md`.

**A second scan does not refine the dimensions; it bounds their uncertainty.**
`test2.zip` is a textured MESH — a reconstruction, not returns — captured a day
after the first, covering less of the space (8 principal faces against 12).
Registered onto scan 1 through `capture_register`, the five matched wall planes
disagree by a **median of 119 mm, worst 168 mm**, against a within-scan
floor-plane RMS of 12 mm. Those two numbers measure different things: one is
noise inside a capture, the other is ARKit drift between captures. Clear height
agrees to 63 mm, because gravity is measured by the IMU while horizontal
position is dead-reckoned.

**Repeatability is not accuracy, and no number of scans changes that.** Both
captures come from the same device and share whatever systematic scale error it
has. The drawings' verdict stays UNVERIFIED and only a tape closes it.

**The published dimensions did not move.** Re-levelling scan 1 with the
corrected algorithm shifted every named wall by ≤ 7 mm, so the sheets stand.

**Bug 1: the floor finder was picking the ceiling.** `dominant_floor`
hypothesised planes from three uniformly random points, which requires all three
to land on the same surface. In this mesh the floor is 8.5% of the sampled area
— it is under the furniture — and the ceiling is 14%, so P(three on the floor)
was about 0.06% per iteration and 400 iterations levelled the room upside down.
Three changes, each with a measured justification: seed from a point's own
NEIGHBOURHOOD so every iteration is a real surface hypothesis; require that
patch to be genuinely flat (a corner-straddling neighbourhood yields a normal
belonging to neither surface, and measured on the fixture a flat patch scores
0.28-0.38 against a corner's much higher ratio); and select the floor by
FOOTPRINT rather than by inlier count, because a floor spans its room and that
is what separates it from a table top. The old "at least half the inliers of the
biggest plane" rule failed exactly where it mattered.

**Bug 2: `capture_register` could not register a cloud onto a cloud.** It passed
one name to `-SAVE_CLOUDS FILE` while two clouds were loaded. That works when
the target is a MESH — the case A42 built and verified — and fails otherwise
with "specified 1 file names, but there are 2 clouds". CloudCompare states the
count in the message, so the lane now asks rather than guessing from file
extensions, and keeps the first name because the source is loaded first.

**A test of mine was asserting on an extreme.** `z.max()` over 279 K points with
12 mm of noise is a 4-sigma tail; the assertion was about the noise, not the
geometry. Percentiles, the same discipline `views3d` already applies to wall
heights.

## A66 gap closure and A65 P5 — rulings from what real use found (2026-09-04)

Owner directives: *"acton all the 'deliberately not being done'"*, *"build a
character for the required tests"*, *"fix the reader to use the control
piece"*. Each ruling below settled a question code could not settle for
itself, and every one was forced by measurement rather than taste.

**`holes` counts what a hole table tables.** `pk_check` returned **pass** for
a spec of four Ø10 holes on a pocket that has none, because it counted
concave cylindrical *faces*: corner radii were holes and a split bore counted
twice. The fix could have been local, but `pk_check` and `pk_drawing` giving
two different answers about one part is indefensible to anyone holding the
sheet — so the predicate moved to `brep/holes.py` and both call it. A second
implementation is exactly how they came to disagree. Consequences, each
pinned: a pocket's corner radii are not holes, a bore split across faces is
one hole, two coaxial blind holes with metal between them are two, and **a
slot's two ends are no longer two holes** — a deliberate behaviour change,
with a new `slots` rule so a slot stays checkable and a refusal that says
which rule to use.

**Overlapping sketch profiles are one region, unioned and declared.** Three
crossing closed profiles are not an inconsistent spec — they have exactly one
sane reading, the one every 2D sketcher gives — so Law 19 says default and
declare, not refuse. `assumed["overlap"]` carries it once. Law 6 governs only
the failure path: if the fuse genuinely fails, the refusal names both
profiles by sketch tag. What is now impossible is the silent wrong answer:
crossing is *detected*, so the accidental nested-or-disjoint verdict has no
code path left.

**A body's plane of symmetry is its SKELETON, not its tessellation.** The rig
loader centred on the vertex mean; a handed Kuhn decomposition puts that mean
5.0 mm off a midline the bounds and skeleton hit exactly, which
`frame_from_mesh` read as 10.0 mm of arm asymmetry on a body that has none.
It now takes the midpoint of the mapped left/right pairs, falls back to the
bounds midpoint, and keeps the **mean for z** — a body is not its own mirror
front to back, so there is no skeleton answer to take there. This moved
pinned numbers in the rig tests and they were re-pinned, because the old ones
encoded the error.

**A rig's proportions are checked against this repo's own figure, and the
code says so.** A swapped clavicle (`LeftShoulder`↔`LeftArm`) was accepted
silently, putting every sleeve's pivot on the collarbone while still swinging
plausibly. The band is derived from `seamkiln.figure` — upper arm 0.163,
forearm 0.149, thigh 0.235 of the height the mesh actually spans — and is
labelled in the source as **this repo's reference figure, NOT an
anthropometric claim**, because we have not sourced anthropometric data and
will not imply we have. The band 0.60–1.30 is deliberately wide: a clavicle
swap reads 1.43× and a twist bone halves a segment, while stylisation inside
the band is the character's business.

**A control piece outranks a declared unit.** A purchased Optitex AAMA export
declares `$INSUNITS 6` — metres — over geometry drawn in inches. Trusting the
declaration made a 36-inch dress 36 metres long with every seam still
closing. The file carried its own antidote, as pattern CAD does: a square
marked `DO NOT CUT`, labelled `10"X10"`, there so the receiving system can
check its own scale. It is now rung 2 of `_resolve_units`, above every
declaration, and **it wins** — reported loudly with both numbers and the
39.37× ratio, but not refused, because we are not uncertain: we know the
answer, and blocking work we can do correctly is the wrong failure mode. A
declaration is a claim; a measurement is evidence. A control piece is
metadata and never returns as a panel.

**The writer emits R12, and the Style System Text in Title Case.** Gerber's
parser wants R12 with no `*Model_Space`/`*Paper_Space` definitions, no TABLES
and 7-bit ASCII, so output goes through `ezdxf.addons.gerber_D6673`. We had
written R2000 to preserve `$INSUNITS`, which was backwards — real files do
not set it, and the one that did set it was wrong. On casing, two vendors
write the same keys differently: CLO ALL CAPS, Optitex Title Case. The
standard requires mixed case, so **CLO is the non-conforming writer** and
following it would propagate its mistake. We write Title Case and the reader
upper-cases before matching, so it takes either: write to the standard, read
what arrives.

**An unknown layer reports what it holds, and we do not go shopping.** No
free file from Gerber, Lectra or Optitex exists, and every substitute writes
*fewer* layers, not more (Seamly2D's AAMA export: two). Rather than treat the
ten unverified layers as procurement debt, the reader makes the first real
file anyone opens teach us: `layer 15 holds 15 TEXT across 6 pieces`, and
`strict=True` refuses rather than guessing. `observed_layers` keeps
defined-but-unwitnessed separate from unknown, which is the evidence a
`verified` flag actually needs. Nothing here may promote a guess into the
table — it caught Optitex writing sewing notes on a layer our AAMA table
calls `drill_second`, and that was **recorded, not silently rewritten**.

**A test fixture character is generated, never downloaded.** The owner's
asset folder holds only obfuscated CLO `.avt` containers; SMPL and its
relatives are non-commercial (doc 67 §2). A fixture must be deterministic,
licence-clean and CI-runnable, so the rigged humanoid is authored in code
from one number. `pygltflib` is absent and trimesh ignores glTF skins, so the
skinned glTF is written and read by hand rather than adding a dependency —
which is also the machinery a real studio file will need. Its joint names are
Mixamo's and asserted **disjoint** from seamkiln's, so the mapping layer
cannot be satisfied by accident.

## One server, several adapters, and a declared default (2026-09-04)

Owner directive: *"use TEE"*. Driving the new lanes from the model's seat on
the live Desktop server found them unreachable by construction: the manifest
served one adapter and the CLI could build only one, while `TeeApp` had taken
a `dict` of adapters all along.

**`--adapter` repeats, and the FIRST one listed is the declared default.**
SI-B6 ruled that ambiguity fails loud — a wire-visible default of `fake` once
broke every real server — and that ruling stands for an app built with
several adapters and no declared default: `resolve_adapter(None)` still
raises `adapter_required` listing the choices. But an operator who writes
`--adapter blender --adapter partkiln` has not been ambiguous; they have
declared an order. Law 19 says default and declare, so the first name is the
default and `tee_status` reports it. Blender first in the manifest keeps
every existing Desktop batch working with no `adapter=`; a batch for another
lane names it. The alternative — forcing `adapter=` on every Desktop call —
would have taxed the common case to protect against a mistake the order
already prevents.

**Serve every lane whether or not its kernel is present.** Measured: a lane
whose kernel is absent boots in 0.3 s and refuses honestly at call time
(`pk_kernel_absent`, `seamkiln_unavailable`), and the two adapters cost
0.003 s and 0.015 s to construct, the 40 s cold `import OCP` running as a
background job (Law 17). So the manifest lists all three unconditionally;
the cost on a machine without the kernels is a truthful refusal, and the
benefit on a machine with them is that the product can reach what it ships.

**An install the running server cannot see is not the server's defect.** An
editable install is a `.pth` hook `site.py` reads once at start; measured,
`importlib.invalidate_caches()` does not reveal it and a restart does. The
hint now says "then restart the server". The first theory — a stale import
cache in `_need()` — was measured wrong before it was acted on, and that
order of operations is the point.
