# TEE Build Progress

Claude: read this file at session start, update it before session end.
Check items only after their acceptance criteria ran for real (paste evidence
under "Evidence log"). Record machine-specific facts under "Machine facts".

## Phase status

- [x] Bootstrap — repo scaffold, research corpus, execution script (built in
      Claude cloud session, 2026-08-21)
- [x] Phase 0 — Environment discovery *(cloud container; re-run on the
      physical machine when it joins)*
- [x] Phase 1 — Server core and token kernel *(cloud container, 2026-08-21)*
- [ ] Phase 2 — Blender adapter *(in progress in cloud: headless-testable
      parts; live-GUI validation needs the physical machine)*
- [ ] Phase 3 — Unreal adapter *(requires the physical machine — UE editor
      cannot run in the cloud container)*
- [x] Phase 4 — Cross-cutting friction killers *(cloud, 2026-08-21; doctor
      re-run on the physical machine will extend the evidence)*
- [ ] Phase 5 — Benchmarks *(Blender scenarios done in cloud: 87.7% total
      saving measured — see benchmarks/RESULTS.md; UE scenarios need the
      physical machine)*
- [ ] Phase 6 — Packaging and handoff
- [x] Phase 7 — TEE Extract: media extraction module *(built in cloud,
      2026-08-22: all lanes + store + frames + handoff + IFC export; 144
      non-DCC tests, 26 live-Blender tests, extraction benchmark 92.6%
      saving. Whisper/pyannote model quality on real site audio and
      GPU-dependent paths still deserve a physical-machine spot check)*
- [x] Phase 8 — Context economics *(researched, simulated and built in
      cloud, 2026-08-22: tee_script lane, columnar responses, recap,
      caption-once; fix-loop benchmark 63.2% saved at 3 conflicts, flat
      script cost vs linear rounds)*
- [x] Phase 9 — TEE Assets *(built in cloud, 2026-08-22: license-gated
      store + attribution, 5 source backends (live-tested against Poly
      Haven/ambientCG), four-band scale policy, 15 as_* tools, lane 0
      materials + classical photo-PBR, placement validator, sun within
      0.003° of NREL, verify battery, skill, benchmark 93.5% saved.
      Physical machine still owed: GPU lanes 1-3 live (diffusion,
      TRELLIS, hosted keys), [assets-embed] embeddings, UE import path,
      Blender library authoring/asset_listing publishing)*
- [x] Phase 10 — TEE Design *(built in cloud, 2026-08-22: tee-design/1
      spec + revision store, sourced reference tables, cost-ordered
      battery (lint/scope/economy-sim/progression/ethics + self-play
      prepare-score), 11 gd_* tools, game-design skill; 24 tests, all
      seeded-defect acceptance cases caught)*
- [ ] Phase 11 — TEE Physical *(research complete + phase scripted
      2026-08-22; build not started. Modeling ops, material facts,
      Blender physics lane and plausibility checks are cloud-buildable;
      UE physics needs the physical machine)*
- [ ] Phase 12 — TEE UEFN (bonus) *(research complete + phase scripted
      2026-08-22; build not started. Digest lane, Verse linting, export
      validator, adapter fakes and the version firewall are
      cloud-buildable; live UEFN lanes need the physical Windows
      machine with UEFN + Beta Access)*

## Machine facts

### Cloud build container (Claude Code on the web, 2026-08-21)

- OS: Linux x64 (ephemeral container; work persists only via git push)
- Python: 3.11.15 (default), 3.12, 3.13 available; `uv` installed
- Blender: 5.2.0 LTS extracted at `/home/user/blender-5.2.0-linux-x64/`
  (headless verified: `bpy OK (5, 2, 0) py 3.13.13`); official Blender MCP
  extension NOT installed; no GUI/display
- Unreal: not installed, not installable here (size + EULA + editor GUI)
- MCP Python SDK: 2.0.0 (see DECISIONS 2026-08-21 — `MCPServer` API)
- Adapter tiers: Blender primary (5.2 LTS headless); UE n/a in cloud

### Physical machine

*(filled in by Phase 0 when the repo is first opened there)*

- OS:
- Python interpreters / uv:
- Blender installs (path, version, official MCP extension present?):
- Unreal installs (path, version, ModelContextProtocol plugin present?):
- Adapter tiers selected:

## Blockers

*(none recorded)*

## Evidence log

*(paste real command output here when checking off acceptance criteria)*

### 2026-08-21 — Bootstrap
- Deep-research pass completed (11 agents, ~1.15M tokens): corpus committed
  under `docs/research/` (10 digests + index).
- Execution script authored from the corpus; architecture decisions A1–A7
  recorded in `docs/research/00-index.md`.

### 2026-08-21 — Phase 0 + Phase 1 (cloud)
- `server/` scaffolded with uv; `make check` = ruff + pytest.
- Kernel implemented: adapter contract + fake adapter, differential scene
  cache (epoch/revision stamps, net-diff merging, bounded log), response
  budgeter + per-tool size log, progressive-disclosure registry
  (search/describe/call with argument validation), checkpoint manager with
  auto-checkpoint per batch, async job manager, project memory (.tee/).
- MCP surface: 14 always-loaded tools on `mcp` SDK 2.0 `MCPServer`,
  `structured_output=False` everywhere (A6), inline-JPEG capture tool.
- Evidence: `uv run pytest` → **50 passed** (units + A6 lint suite + 6
  end-to-end in-memory MCP client scenarios); `ruff check` clean.
- Measured: full 14-tool definition surface ≈ **2,307 tokens** (budget 8K;
  wild-average is ~710 tokens/tool, so the whole surface costs ~3 tools).
- `tee serve` (stdio, fake adapter) and `tee doctor` (stub) run.

### 2026-08-21 — Phase 2 (cloud-testable parts) + adversarial review
- Blender adapter over the official Blender Lab MCP add-on wire protocol
  (verified against the real add-on source and live headless Blender 5.2);
  generic batch interpreter (N ops = 1 round-trip), `session_uid` entity
  ids, API firewall over the ten catalogued 4.x/5.x fault lines,
  snapshot/rollback, byte-budgeted JPEG capture, `bl_*` virtual tools.
- TEE bridge add-on (`adapters/blender/tee_bridge/`): same protocol,
  hardened threading (I/O thread + single persistent timers pump / blocking
  background loop), 5.1+ extension manifest, denylist guard. Live suite runs
  against BOTH bridge flavors.
- **Adversarial review workflow** (32 agents, ~2.2M tokens): 28 findings
  confirmed empirically, 0 refuted — including three majors: the mcp 2.0
  SDK dispatches tool calls concurrently on worker threads (torn state), the
  SDK pretty-prints dict returns (≈2x wire size; fixed by returning compact
  JSON strings), and mid-batch failures left the DCC and scene cache
  silently divergent (fixed: batches are atomic — auto-restore to the
  checkpoint on failure). All 28 fixed with regression tests.
- Evidence: `uv run pytest` → **85 passed**; `uv run pytest -m dcc` →
  **20 passed** (both bridge flavors, real Blender 5.2); ruff clean.
- Follow-up for next session: adversarial review round over the fix diff +
  bridge add-on; GUI-mode bridge validation needs the physical machine.

### 2026-08-21 — Phase 4 (cloud)
- **Docs search:** `bl_search_docs` / `bl_api_detail` — the API index is
  introspected from the LIVE Blender over the bridge (`bl_rna` reflection),
  version-matched by construction, cached per version on disk. Live test:
  4,000+ symbols indexed; `shade_smooth_by_angle` found with correct params.
- **Doctor:** real checks (python, uv, Blender binary+version, bridge
  socket round-trip with protocol probe, bpy wheel ABI, Unreal/Epic MCP
  endpoint), each failure with a one-line fix; `--json`; `--emit
  claude-code|claude-desktop|cursor` prints working MCP client configs.
  Evidence: all checks OK on this container with a live bridge (exit 0;
  Unreal correctly a warning).
- **Transport hardening:** oversized-frame rejection completes the
  kill-test set (bridge down / severed mid-response / garbage frame /
  oversized frame — all structured errors, never hangs); advisory
  `.tee/server.pid` notice for double-serve.
- **Tool profiles:** `.tee/config.toml` — `[tools].disabled` (hidden from
  search, calls answer `tool_disabled` naming the config), `[server]
  .allow_code_exec`, `[blender].port`; malformed config degrades with a
  warning in `tee_status`, never bricks the session.
- **Client-compat canaries:** expected-tool-count assertion (catches silent
  catalog drops), every-tool model-visible-content canary, and a real
  stdio-subprocess end-to-end test (spawn `tee serve`, initialize,
  tools/list, tool call through the SDK client).
- Evidence: `uv run pytest` → **107 passed**; `-m dcc` → **22 passed**
  (both bridge flavors); ruff clean; doctor exit 0 with bridge up.

### 2026-08-22 — Phase 7 research + script (cloud)
- Deep-research pass for TEE Extract (9 agents, ~865K tokens): corpus
  digests 11–18 committed; decisions A8–A10 recorded.
- Load-bearing findings: MCP sampling is dead (deprecated in the MCP
  2026-07-28 spec, unimplemented in Claude Code/Desktop) → in-band
  extraction is the default channel; PyMuPDF (AGPL) and all open floor-plan
  ML models (CC BY-NC / GPL) are license-banned → deterministic lane on
  pdfplumber/ezdxf/ifcopenshell/OpenCV; `ezdxf` DIMENSION.get_measurement()
  is dimensional ground truth; images bill by rendered dimensions
  (`ceil(w/28)×ceil(h/28)`, ≤4,784 tokens on the Fable/Opus-5 tier) so
  media serving is token-budget-first; VLM accuracy on drawings is ~0.95
  for text transcription but 0.40–0.55 for symbol counting → extract text,
  verify geometry deterministically; FML v3 adopted as plan-schema base but
  extended (per-level heights, parametric roof) before freeze; frames +
  transforms-as-facts with tier precedence settle cross-source conformance.
- Phase 7 written into `CLAUDE_EXECUTION_SCRIPT.md` (sections 7.1–7.8 with
  acceptance criteria); build not started.

### 2026-08-22 — Phase 7 build (cloud)
- **Store (7.1):** content-addressed fact store under `.tee/extract/`
  keyed (media_hash, extractor, version) with 2-char fanout; re-ingest of
  identical media is a no-op (verified: second ingest of the 7-file fixture
  folder reports ≥6 cached, 0 re-extracted). Evidence-tier table
  `TIER_TOLERANCE_M` with RSS tolerance math; license lint test bans
  fitz/pymupdf/marker/ultralytics imports repo-wide.
- **Plan schema + frames (7.2):** `tee-plan/1` (FML-derived, per-level
  heights, parametric roof, validation with exact-fix errors); frame
  registry with single-active-parent transform tree anchored at `site:enu`,
  Umeyama similarity fit (scale pinned when dimension_text governs,
  free-scale conflict >2% surfaces `units_conflict`), pymap3d geodetic
  datum. All covered by unit tests.
- **Document lane (7.3):** ezdxf DIMENSION ground truth + $INSUNITS
  firewall (unitless DXF → calibration question, never a guess), WALLS/
  ROOMS/DOORS layer extraction to plan facts; pdfplumber vector-sheet lane
  (dimension-string↔line pairing, least-squares scale fit, wall pairing,
  NCS sheet classifier), OCR fallback for scanned pages; fixture DXF and
  PDF plans extract to correct 8m×6m plans (walls, rooms, door, dims).
- **Image/video/audio lanes (7.4):** EXIF+GPS+phash image facts, ≤5-photo
  dedupe groups + labeled contact sheet, token-budgeted `tee_media` serving
  (crop/timestamp/page, patch-formula budget, 4,784 cap); video keyframe
  funnel (2s sampling → sharpness → phash clusters → ≤15 keyframes with
  timestamp index + frame-accurate re-fetch), DJI SRT flight paths
  downsampled to turning points; faster-whisper transcription with VAD
  (fixture: espeak-synthesized brief transcribed, "bedroom"/"budget"
  requirements recoverable), optional HF-gated diarization degrades silently.
- **VLM passes (7.5):** in-band driver (ex_prepare packet: paths, guidance
  per media type, plan-schema hint; ex_store_facts validated writeback) as
  default; optional ANTHROPIC_API_KEY ApiDriver; tile plan respects both
  the 4,784-token and 2,000-px caps.
- **Kernel wiring (7.6):** `ex_*` virtual tools via progressive disclosure;
  `tee_media` is the 15th always-loaded tool; ingest runs as async jobs;
  canaries updated (tool count, model-visible content).
- **Handoff + conformance (7.7):** plan → typed batch ops (rotated unit
  cubes, floor slabs) through the normal checkpointed batch machinery;
  build manifest maps wall ids → entity ids; `bl_check_against_plan`
  compares in the common frame with RSS(tier, tier, chain) tolerance and
  stores over-tolerance deltas as conflict facts. IFC4 export via
  ifcopenshell authoring API (real IfcWall entities, storey elevations).
- **Live acceptance (7.7):** DXF fixture plan built in real headless
  Blender via BOTH bridge flavors: 5 walls + slab, honest build conformant
  (0 conflicts); a wall deliberately moved 0.1 m yields exactly one
  conflict fact naming `plan:w1:position`, delta 0.1 m vs tolerance
  0.017 m, stored in the fact store. Found and fixed a real kernel bug en
  route: `obj.dimensions` writes/reads against a stale bound_box for
  meshes built in the same batch — batch details are now collected after
  one `view_layer.update()`, and dimension props apply scale from true
  vertex extents.
- **Benchmark (7.8):** extraction scenario added to `benchmarks/` — naive
  re-attach of the media set every session vs ingest-once + compact fact
  queries over a simulated 4-session build: **65,176 → 4,811 tokens
  (92.6% saved)**; Blender scenarios re-run and unchanged (87.7% total).
- Evidence: `uv run pytest` → **144 passed, 0 skipped**; `uv run pytest -m
  dcc` → **26 passed** (both bridge flavors, live Blender 5.2); `ruff
  check`/`format` clean; full benchmark suite re-run against live Blender.

### 2026-08-22 — Phase 8 research + build (cloud)
- **Research + simulation pass** (docs/research/19): verified current
  API-side mechanisms (programmatic tool calling excludes MCP tools →
  app-side lane; context editing makes tool results evictable — affordable
  for TEE because all state is re-derivable; deferred tool schemas validate
  the registry design). Four simulations against the real machinery; one
  deliberate negative result: a BM25 swap for fact search REGRESSED
  relevance (9/10 → 7/10 at 611 facts) — search left as is, recorded in
  A12 so it is not "improved" later without new evidence.
- **`tee_script` (A11):** AST-whitelisted, tree-walk-interpreted (never
  exec'd) script lane over the existing typed tools - call/batch/summary/
  detail/diff helpers, hard budgets (200 calls / 10k steps / 120s / 20k
  chars), atomic via auto-checkpoint per touched adapter with full rollback
  on any error, only `result` returned. 16th always-loaded tool (canaries
  updated). 28 tests: sandbox rejections (import/while/def/lambda/dunder/
  attribute/walrus/try/global), budget enforcement, rollback atomicity,
  real composition over batches.
- **Adaptive columnar encoding (A12):** list-of-dicts fields ≥ 20 rows with
  ≥ 60% shared keys rewritten to cols/rows with a decode marker, wired into
  the server pipeline before the budgeter; sub-threshold payloads
  byte-identical. End-to-end acceptance: 100-entity summary ≥ 35% smaller
  through the real MCP surface.
- **Recap (A12):** `tee_status(recap=true)` rebuilds a ≤ 500-token project
  recap from server state (scene stamps + kind counts, checkpoints, extract
  store shape, memory) — the eviction-safe one-call resume; contract stated
  in the tool description.
- **Caption-once (A12):** `ex_prepare` lists uncaptioned image stems with
  guidance to store ≤ 20-word caption facts (merge=true); captioned images
  drop out of future packets; captions searchable via ex_search. En route
  fixed a real store gap: `ex_store_facts` replaced the whole extractor
  file per call, clobbering incremental writes — added merge semantics with
  tests.
- **Benchmark (8.5):** conformance fix loop as rounds vs one tee_script
  call: script cost is FLAT (~173 tok) vs ~130 tok/conflict for rounds —
  **17.7% / 63.2% / 76.3% saved at 1 / 3 / 5 conflicts**. Published next to
  the Phase 7 numbers; the sim's 86% assumed a sketch-length script, and
  the acceptance was amended to the honest measured curve. All prior
  numbers reproduced (87.7% scenes, 92.6% extraction).
- Evidence: `uv run pytest` → **186 passed** (1 deliberate skip); `-m dcc`
  → **26 passed** (both bridge flavors, live Blender 5.2); ruff clean;
  full benchmark suite re-run against live Blender.

### 2026-08-22 — Phase 9 research + script (cloud)
- Deep-research pass for TEE Assets (6 agents, ~660K tokens): corpus
  digests 20–25 committed; decisions A13–A15 recorded.
- Load-bearing findings: the official Blender Lab MCP ships NO asset
  tools — the space is open; the popular community integration measurably
  re-fetches a 2.3 MB catalog per "search", truncates to the
  alphabetically-first 20, and spends 2–5k tokens to place one asset —
  the baseline TEE's design beats structurally; TRELLIS.2-4B went MIT
  (Dec 2025), enabling a license-clean local 3D generation lane (one
  nvdiffrast runtime audit pending); Hunyuan3D weights exclude EU/UK/SK
  including OUTPUTS — geo-labeled opt-in only; Z-Image/FLUX.2-klein give
  an Apache-2.0 local image lane; Marigold-IID is the license-clean
  photo→PBR core for the Okongo site-photo lane; MobileCLIP's MIT repo
  hides research-only weights (banned; SigLIP 2 Apache is the embedder);
  pysolar is GPL (astral/pvlib instead); Sketchfab changed owners again
  (KitBash, 2026-08-10) — guarded opt-in backend, platform risk recorded;
  Blender 5.2's remote-asset-library JSON listing (`blender -c
  asset_listing generate`) gives TEE a free queryable library index; glTF
  spec-required accessor bounds make dimension checks free pre-DCC;
  Holodeck-style server-side retrieval (59.8% human preference) sets the
  selection contract; honest quality bar stated: set dressing on demand,
  hero assets curated.
- Phase 9 written into `CLAUDE_EXECUTION_SCRIPT.md` (sections 9.1–9.7
  with acceptance criteria); build not started.

### 2026-08-22 — Phase 10 research + script (cloud)
- Deep-research pass for TEE Design (6 agents, ~560K tokens): corpus
  digests 26–31 committed; decisions A16–A18 recorded.
- Load-bearing findings: the design-expertise layer is UNCLAIMED across
  all products and engines (Aug 2026) — commercial tools stop at
  ideation/assets, platform AI at execution; every successful generation
  system pairs LLM proposals with a formal validator (GAVEL, RuleSmith,
  Roblox's playtesting agent) — TEE's module is that pairing; LLM prose
  GDDs score deceptively well, so the machine-verifiable spec is the
  source of truth and prose is a rendered view; median mobile D1 is ~22%
  (folk 30–40% targets are top-decile) — benchmarks ship as percentile
  grids with sources; regularity-of-play beats volume as a churn
  predictor; GEQ was never validated (PXI/miniPXI default); defaults
  dominate behavior (95% keep subtitles when default-on); loot-box risk
  is the randomization itself (meta-analytic r≈0.26) — dark-pattern
  rules carry code severity from live FTC/EU/Brazil/Australia
  enforcement; the evidence-backed small-team niche is 3D co-op at
  $8–25 with EA-as-the-launch; UE 5.8's first-party MCP plugin
  (extended to UEFN 2026-08-20) validates A4's proxy architecture.
- Phase 10 written into `CLAUDE_EXECUTION_SCRIPT.md` (sections 10.1–10.6
  with acceptance criteria incl. seeded-defect lint tests and an ethics
  hard-fail); build not started.

### 2026-08-22 — Parametric/procedural modeling research pass (cloud)
- Deep-research pass on parametric/procedural/precision modeling surfaces
  (typed-op vocabulary tier 2); digest returned to orchestrator (not yet a
  numbered corpus doc). Key verified facts, all smoke-tested against local
  Blender 5.2.0 LTS headless: GN modifier inputs are now real RNA
  (`md.properties.inputs.<identifier>.value` — attribute access, not
  subscript; ID-property access raises TypeError in 5.2); parameterized GN
  wall-along-path group builds and evaluates headless incl. Object-pointer
  inputs; boolean solvers are FLOAT/EXACT/MANIFOLD ('FAST' identifier gone);
  MANIFOLD wall-with-openings boolean verified manifold-clean; BMesh hole
  pattern via mathutils.geometry.tessellate_polygon + bmesh.ops.solidify
  verified (bmesh.ops has NO boolean op); node tools flag `is_tool` writable,
  tool inputs Python-assignable since 5.2; py-slvs (SolveSpace) pip wheel
  imports headless for constraint solving. License scan: Infinigen BSD-3
  (minable), Buildify free-but-proprietary graph (concepts only), CAD
  Sketcher GPL-3, archipack GPL-3, BlenderKit royalty-free (no asset
  redistribution).

### 2026-08-22 — Phase 11 research + script (cloud)
- Deep-research pass for TEE Physical (6 agents, ~670K tokens): corpus
  digests 32–37 committed; decisions A19–A21 recorded. Two agents
  verified by EXECUTION: modeling findings smoke-tested against the
  local Blender 5.2 (watertight wall patterns, MANIFOLD booleans, the
  5.2 NodesModifier API break, py-slvs headless); physics bake paths
  read at 5.2 source level (ptcache/fluid/GN bake exec synchronous;
  calculate-to-frame invoke-only; tracker landmines catalogued).
- Load-bearing findings: rigid-body stepping is strictly sequential
  frame_set with fixed substeps — deterministic same-machine, bake
  before checkpoint (memory caches persist in .blend snapshots); Epic
  caps Chaos determinism at "close, but not perfect" cross-machine and
  ships NO simulation toolset in the official MCP — TEE's settle macro
  (SIE + short-call polling + transform diff) fills a real gap and the
  editor-doesn't-tick-during-Python constraint matches TEE's cadence
  natively; static checks carry most verification value
  (CoM-over-support in pure Python; settle thresholds from BlenderProc/
  Isaac; SimReady Foundation is Apache-2.0 with a static validator to
  mirror; CoACD MIT for proxies); a CC0 backbone exists for material
  data across render/physics/engineering tiers while NIST SRD is
  statute-protected and ArcSim cloth non-profit-only — three-tier
  honesty-labeled schema exceeds SimReady's no-provenance state of the
  art; structural plausibility is legally safe as
  findings-against-cited-tables (IRC is prescriptive by design; the
  load-path graph check is anchored on R301.1's own words) and Solibri
  runs no such rules — the layer has no commercial equivalent; SANS
  10400 flagged for Okongo jurisdiction defaults.
- Phase 11 written into `CLAUDE_EXECUTION_SCRIPT.md` (sections
  11.1–11.6 with acceptance criteria incl. seeded-defect plausibility
  fixtures and a determinism variance-floor benchmark); build not
  started.

### 2026-08-22 — Phase 12 research + script (cloud)
- Deep-research pass for TEE UEFN + version trajectories (5 agents):
  corpus digests 38–42 committed; decisions A22–A24 recorded. This
  closes the queued four-pass research sequence (Phases 9–12).
- Load-bearing findings: Epic shipped its MCP inside UEFN on
  2026-08-20 (v42.00, beta — Toolset Registry + Verse compile + Scene
  Graph entities + Creative devices + Play-in-Client sessions,
  loopback 8000/mcp) and named MCP a UE6 pillar, with UE5 ending at
  5.8 and UE6 EA "end of 2027-ish" — A4's proxy-and-extend posture is
  validated as the only shape that rides the curve; the community
  bridge graveyard (uefn-verse-mcp archived three days before Epic
  shipped) buries from-scratch adapters; there is NO public Verse
  compiler, so digest-grounded symbol linting is the honest offline
  check and kills the documented hallucination classes (`<varies>`
  died in v30.00; digests are per-install, Epic-copyrighted, never
  redistributable — tests use a synthetic fixture); NO Blender→UEFN
  export tool exists despite published Fortnite-Ready budget tables
  (LOD0 caps, 3 LODs at −50%, ≤2K power-of-two textures, Spec/Metal/
  Rough packing, UCX rules) — a pure-Python validator is TEE's
  uncontested wedge; 5.8.1 disabled transaction bundling during tool
  scripts so TEE must own checkpointing; StartPIE exists in 5.8 final
  (doc 07's preview-era gap list flagged stale); Blender 5.3/6.0
  fault lines published and shim-able now (all_ids order change,
  use_nodes 6.0 hard removal, Vulkan default, @b5_3 asset naming);
  legacy Blender physics shows no deprecation signals (Phase 11 bet
  confirmed); Blender Lab's first 2026 experiment is its own Blender
  MCP server (watch lane).
- Phase 12 written into `CLAUDE_EXECUTION_SCRIPT.md` (sections
  12.1–12.7 with acceptance criteria incl. seeded-hallucination lint
  fixtures, budget-violation fixtures, LUF↔XYZ property test, and a
  license lint proving no AGPL code and no Epic digest text);
  Standing rules renumbered to section 16; build not started.

### 2026-08-22 — Phase 9 build (cloud)
- TEE Assets built per script 9.1–9.7: `server/src/tee/assets/` (license
  gate, store+TASL manifests+CREDITS renderer, http ETag/TTL catalog
  cache, 5 backends, stdlib glTF/GLB probe, local ingest, CIEDE2000 +
  k-means color, envelopes + four-band scale policy, faceted search,
  importer, lane-0 materials from the physicallybased.info CC0 snapshot
  (86 materials incl. density), generation lane w/ cost-confirm +
  server-side wait-poll, classical photo→PBR, style brief, astral sun,
  placement solver+validator, verify battery) + 15 `as_*` virtual tools;
  `import_file` op added to the Blender codegen; `assign_material` added
  to FakeAdapter reference semantics; `context-aware-assets` skill
  (SKILL.md + 4 references + 3 evals).
- Evidence: `uv run pytest` → **268 passed, 1 skipped**; `-m dcc` →
  **30 passed** incl. new live GLB import round-trip with scale applied
  (2 m cube → 0.5 scale → dims [1,1,1] read back on both bridge
  flavors); ruff clean. Live network tests (skip cleanly offline):
  Poly Haven furniture search ≤200 tokens w/ ETag-cached catalog,
  resolve names CC0 + md5-verified gltf files; ambientCG brick search.
  Acceptance checks: NC asset refused before any byte cached (by test);
  CC-BY CREDITS.md rendered; door snaps ×1.023 into the 0.9 m opening;
  0.4 m "sofa" rejected one-line; sun vs NREL SPA reference: az diff
  0.0023°, el diff 0.0030° (≤1° required); validator catches blocked
  door swing (code) + sub-760 mm corridor via erosion connectivity.
- Benchmark (live run, RESULTS.md): find-select-place 3 assets = 828
  tokens / 6 calls vs 12,767 / 25 prior-art (**93.5% saved**); all
  prior scenario numbers reproduced in the same run.
- Deviation recorded: glTF probe is stdlib (JSON chunk + node-transform
  composition), not pygltflib — script amended; no new dependency.

### 2026-08-22 — Phase 10 build (cloud)
- TEE Design built per script 10.1–10.6: `server/src/tee/design/`
  (spec.py validate/render/SpecStore with diffable revisions; tables.py
  query API; checks.py battery; tools.py 11 gd_* tools; 6 versioned
  data files — benchmarks, genres, motivations, ux_params,
  economy_archetypes, dark_patterns — every figure with source+as_of);
  `game-design` skill (SKILL.md + 2 references + 3 evals).
- Evidence: `uv run pytest` → **292 passed, 1 skipped** (24 new);
  ruff clean. Acceptance checks all by test: spec round-trips
  (validate → render → edit → re-validate, changed_sections=
  ["core_loop"]); lint catches seeded dead currency ("gems", fix names
  the two moves), missing session-end hook, sonar used-before-taught;
  economy solver flags the seeded faucet spiral (ratio 0.036 vs
  premium band 0.6–1.1) and passes the balanced fixture (ratios
  0.6–1.1 across personas); ethics HARD-fails the under-16 loot-box
  spec citing loot_box_minors severity=code with Belgium/Brazil/FTC
  jurisdictions; gd_benchmark("d7","mobile","puzzle") answers median
  4% + GameAnalytics 2026 + the top-decile folk-target warning +
  AppsFlyer genre D30; the Salvage Crew co-op brief (opportunity-map
  niche) names 3 comparables with deltas, passes the whole battery,
  and its content_list resolves against Phase 9 asset classes; pity
  hazard recomputation validates Genshin's published params and
  catches a false expected_pulls declaration.
- Bridge to build wired: content_list classes = Phase 9 ASSET_CLASSES
  (checked by test); design store lives under .tee/design/ with
  revision history.
