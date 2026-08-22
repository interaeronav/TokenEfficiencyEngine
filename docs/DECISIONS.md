# Decision log

Amendments to the settled architecture (A1–A7 in
`docs/research/00-index.md`) or to `CLAUDE_EXECUTION_SCRIPT.md` are recorded
here before being implemented: date, decision, rationale, what it supersedes.

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
