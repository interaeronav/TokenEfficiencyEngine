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
- [x] Phase 2 — Blender adapter *(cloud 2026-08-21 for the
      headless-testable parts; closed out on the physical M5 Mac
      2026-08-22 — GUI-mode bridge validated in a real windowed
      Blender, the macOS teardown defect fixed, and the last three
      acceptance bullets executed live)*
- [x] Phase 3 — Unreal adapter *(built and accepted on the physical M5 Mac
      2026-08-22 against a live UE 5.8.1 editor: proxy over Epic's
      official MCP, batch lane, Blueprint DSL authoring with readback
      verification, text-first checks, budgeted capture, and TEE's own
      content plugin for unsandboxed editor Python. The 5.3–5.7 fallback
      tier is **n/a** — no such engine on this machine)*
- [x] Phase 4 — Cross-cutting friction killers *(cloud, 2026-08-21; doctor
      re-run on the physical machine will extend the evidence)*
- [ ] Phase 5 — Benchmarks *(Blender scenarios done in cloud: 87.7% total
      saving measured — see benchmarks/RESULTS.md; UE scenarios need the
      physical machine)*
- [x] Phase 6 — Packaging and handoff *(built in cloud, 2026-08-22:
      tee-engine wheel + clean-venv install rehearsal w/ MCP stdio
      round-trip, Blender extension zip built+validated with real
      Blender, doctor --emit fixed for installed layouts, docs set
      (quickstart, per-DCC setup, troubleshooting, security), tee-usage
      skill, v0.1.0 tagged. Physical machine still owed: UE
      content-plugin zip (Phase 3), .mcpb bundle where a client wants
      it, clean-WINDOWS-machine rehearsal)*
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
- [x] Phase 11 — TEE Physical *(built in cloud, 2026-08-22: 8 tier-2
      modeling ops live-verified watertight, py-slvs sketch_solve,
      three-tier material facts, settle/cloth/bake physics lane with
      0.00 mm measured variance floor, tier-0 CoM checks, plaus_check +
      IDS tier; 18 live + 24 unit tests. Physical machine still owed:
      UE physics/settle (SIE), fluid bake live validation, hip roof
      pending straight-skeleton lib, CoACD proxy integration,
      SANS 10400 before Okongo jurisdiction defaults)*
- [x] Phase 12 — TEE UEFN (bonus) *(built in cloud, 2026-08-22:
      digest parser+diff firewall, digest-grounded Verse lint, validated
      templates, FakeUefn adapter w/ LUF↔XYZ boundary, export_for_uefn
      (live FBX+LOD autogen verified), version-trajectory firewall
      tests, uefn skill, live Data API analytics; 26 tests + 2 live.
      Physical Windows machine still owed: live UEFN MCP proxy, compile
      lane, Scene Graph ops against Epic's toolsets)*

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

Identified 2026-08-22: **Apple M5 MacBook Pro Max, 128 GB unified
memory** (macOS, Apple Silicon). Phase 0 re-run on the physical machine
2026-08-22:

- OS / macOS version: macOS 26.6.2 (build 25G83), arm64
- Python interpreters / uv: system `/usr/bin/python3`, Homebrew
  `/opt/homebrew/bin/python3` = 3.14.7; `uv` 0.12.1 (Homebrew). The
  project venv pins **CPython 3.11.15** (uv-managed,
  `~/.local/share/uv/python/cpython-3.11.15-macos-aarch64-none`).
- Blender installs: `/Applications/Blender.app` (CLI symlink
  `/opt/homebrew/bin/blender`) = **5.2.0 LTS**, build date 2026-07-14 —
  the *same* version the cloud container validated against, so the
  Phase 2 fault-line shims need no re-derivation. User extensions dir
  `~/Library/Application Support/Blender/5.2`. Official Blender Lab MCP
  extension: **not installed**; nothing listening on `:9876`.
- Unreal installs: **UE 5.8** at `/Users/Shared/Epic Games/UE_5.8`,
  with Epic's first-party plugin present at
  `Engine/Plugins/Experimental/ModelContextProtocol/ModelContextProtocol.uplugin`.
  Launcher at `/Applications/Epic Games Launcher.app`. An existing
  project tree `OkongoSim` sits inside the engine dir;
  `~/Documents/Unreal Projects/` is empty. Nothing listening on `:8000`
  (editor not running / auto-start not yet enabled).
- Adapter tiers selected: **Blender primary** (5.2 LTS, TEE fallback
  bridge add-on — the official extension is absent here);
  **UE official tier** (5.8 + `ModelContextProtocol`, the A4 route). The
  5.3-5.7 Remote Control fallback tier has no engine on this machine and
  stays `n/a` until one is installed.

Platform split of the outstanding ledger (decided by the hardware):

- **This Mac covers:** Phase 3 Unreal adapter (UE 5.8 macOS editor +
  the first-party MCP plugin, A4 route), live-GUI Blender validation
  (Phase 2 close-out), UE benchmark scenarios (Phase 5), clean-machine
  install rehearsal on real user hardware (Phase 6 re-check + the
  v0.1.0 tag push), Whisper/audio quality spot-check (Phase 7),
  diffusion lanes 1-2 via torch **MPS** (Z-Image / SDXL-tileable /
  Marigold-IID - 128 GB unified memory is ample; CUDA-only claims in
  A14 get re-verified against MPS), hosted generation (Tripo/Meshy
  keys), [assets-embed] embeddings (CPU/MPS).
- **Still needs a Windows machine:** everything live-UEFN (editor,
  Beta Access toggles, MCP toolsets, Verse compile lane, Scene Graph
  ops against Epic's toolsets) - UEFN has no macOS build. The offline
  UEFN lanes (digest/lint/templates/export preflight) already work
  everywhere.
- **Still needs CUDA:** local TRELLIS.2-4B (nvdiffrast is
  CUDA-bound) - lane 3 local generation stays hosted-only on this Mac.

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

### 2026-08-22 — Phase 11 build (cloud)
- TEE Physical built per script 11.1–11.6: `server/src/tee/physical/`
  (py-slvs sketch_solve w/ exact-fix over/under-constrained errors;
  three-tier honesty-labeled materials on EN-cited data + the Phase 9
  CC0 render tier; settle/cloth/bake programs with sequential frame
  stepping + BlenderProc-shaped quiescence; tier-0 CoM-over-support/
  floating/penetrating checks; SimReady-style readiness gate;
  plaus_check rule engine + IRC R301.1 load-path graph + ifctester IDS
  tier; sim_fluid cost-gated as an async job) + tier-2 modeling ops in
  `adapters/blender/modeling_codegen.py` (tessellate+solidify walls/
  slabs/profiles, gable/shed/flat roofs, stairs, MANIFOLD boolean
  opening_cut with 'FAST' guarded, array_along, param_set through the
  single 5.2-shimmed set_gn_input chokepoint). 19 new virtual tools.
- Evidence: `uv run pytest` → **316 passed, 1 skipped**; `-m dcc` →
  **48 passed** (both bridge flavors). Acceptance by test: fixture wall
  with two openings builds watertight (0 non-manifold edges, probed by
  bmesh), same for slab-with-hole, profile extrude, all roof kinds,
  and the boolean cut after apply; sketch_solve closes the dimensioned
  rectangle and names the exact conflicting constraint when
  over-constrained (result 1 + failed-handle mapping), reports DOF when
  under-constrained; param_set round-trips a real GN group socket by
  identifier (verified value 2.5 read back via the 5.2 RNA API); a
  seeded floating chair and an off-center stack are caught by tier 0
  (cumulative CoM criterion); sim_settle on stacked boxes settles,
  adopts poses (box falls 1.2→0.2 m), and two rolled-back runs agree
  to a **0.00 mm variance floor** (5 mm assertion sits safely above);
  mat_assign gives the fixture wall EN 1991-cited 2400 kg/m³ with
  standard_value honesty labels, computed mass echoed, and the Bullet
  sqrt-friction caveat recorded; banned bulk sources (NIST SRD/MatWeb/
  MakeItFrom/ArcSim) fail by test if ever cited; plaus_check flags the
  seeded over-span joist (delta +1.15 m, IRC R502.3.1 cited), the 20°
  tile roof (BS 5534), and the broken load path (LOAD_PATH_BROKEN, IRC
  R301.1), while the clean fixture reports zero findings with the rule
  count and the not-an-approval disclaimer; the IDS tier validates a
  wall-name spec against a generated IFC via ifctester.
- Benchmarks (live run): settle report ~222 tokens, variance floor
  0.00 mm published in RESULTS.md alongside all prior rows reproduced.
- Data caveat recorded: joist-span worst-grade values are approximate
  pending edition verification on the physical machine (flagged in
  plaus_rules.json _meta; findings still cite table + delta only).

### 2026-08-22 — Phase 12 build (cloud)
- TEE UEFN built per script 12.1–12.7: `server/src/tee/uefn/` (digest
  parser → version-keyed facts with inherited-member resolution; digest
  diff → drift facts incl. breaking set; digest-grounded Verse lint
  with the known-drift map (<varies>→v30.00, GetPassengers→
  GetOccupants) and the error→one-line-fix table incl. the
  stale-validation false-positive class; 4 digest-validated Verse
  templates re-authored from MIT/Apache patterns; UefnAdapter contract
  + FakeUefn with Scene-Graph-first ops and the LUF↔XYZ normalization
  boundary; export preflight over the encoded Fortnite-Ready budget
  tables + the Blender export program (LOD1/2 at −50%, cm-scale FBX,
  Face smoothing) + Spec/Metal/Rough channel packing; local device
  catalog index; live Fortnite Data API analytics, TTL-cached).
  16 uefn_* tools; `uefn` skill; A24 firewall landed in code
  (use_nodes write ban in the Blender firewall + TEE's own codegen
  version-guarded, session_uid shuffle regression test, float32
  tolerance policy test, physics-backend declaration test).
- Evidence: `uv run pytest` → **341 passed, 1 skipped**; `-m dcc` →
  **50 passed**. Acceptance by test: the synthetic digest fixture
  (Epic digest text is never bundled — fixtures declare themselves
  synthetic, checked by the license-lint test) parses into classes/
  members/events with effects; the lint rejects all three seeded
  hallucination classes with exact fixes and passes the clean snippet
  with the honest NOT-a-compile boundary stated; v41→v42 diff emits
  member_removed/member_added/effects_changed drift with a breaking
  set; the export validator flags every seeded violation (over-cap
  LOD0 w/ the 400-tri cap named, missing LODs, NPOT texture, bad UCX
  prefix, unapplied transforms, unbaked procedural materials) and
  passes the conformant crate; LUF↔XYZ round-trips exactly over a
  216-point grid; the capability probe degrades offline→gated→live
  with exact remediations; live-Blender export produced a real FBX
  with 2 autogenerated LODs and left the scene clean (both bridge
  flavors); live analytics hit the real public Data API.
- This closes the queued build sequence: Phases 9, 10, 11, 12 all
  built in cloud, one session. Physical-machine ledger unchanged
  elsewhere: Phase 3 (UE), Phase 6 packaging, GUI Blender validation,
  GPU generation lanes, UE physics, live UEFN proxy.

### 2026-08-22 — Phase 6 build (cloud)
- Packaging: distribution renamed `tee-engine` (PyPI-safe; module and
  CLI stay `tee`); `make -C server dist` builds wheel + sdist + the
  Blender extension zip (built AND validated with real Blender 5.2:
  `--command extension build/validate`). Wheel audited: all 12 data
  files (assets/design/physical/uefn) ship.
- Clean-machine rehearsal (acceptance): fresh venv → pip install the
  wheel → `tee 0.1.0` → MCP stdio round-trip with a real mcp client
  against the installed binary: **16 tools listed, 68 virtual tools
  registered, tee_status ok, tee_search_tools found as_search,
  tee_call ran gd_benchmark with its source string** — the whole
  five-module registration chain works from the wheel.
- Real bug found+fixed by the rehearsal: `tee doctor --emit` assumed a
  dev checkout (uv --directory … run) and, second bug, resolved the
  venv python symlink so the emitted command became coreutils
  /usr/bin/tee. Now: dev checkout → uv-run form; installed → the
  venv's own `tee` binary; neither → `uvx --from tee-engine tee`.
  Verified emitted configs for claude-code/desktop/cursor in BOTH
  layouts.
- Docs shipped: docs/quickstart.md, setup-blender.md (3 bridge
  options), setup-unreal.md (A4 route + UEFN beta gating, honest
  physical-machine framing), troubleshooting.md (doctor-derived +
  budgeter/firewall/gate behaviors), security.md (A7 floor: never
  port-forward DCC sockets, code-exec gating, script-lane
  non-capability, data-handling posture). README rewritten with
  user-facing install, module table, measured numbers updated
  (16 tools ≈ 2,757 tokens by the canonical model_dump measure);
  server README updated; `tee-usage` skill packages the operating
  procedure (macro-first, diffs, text-before-pixels, trust-the-gates).
- Evidence: `uv run pytest` → **341 passed, 1 skipped**; ruff clean;
  `make dist` artifacts listed; rehearsal transcript above. Annotated
  tag **v0.1.0** created locally at the Phase 6 commit; the tag PUSH
  was refused (HTTP 403 - this cloud session's git credentials are
  scoped to the designated branch; tag refs are not pushable, and the
  available GitHub tooling has no release/tag API). Maintainer step on
  any full-permission checkout:
  `git tag -a v0.1.0 <phase-6 commit> -m "TEE v0.1.0" && git push origin v0.1.0`
  (or create a v0.1.0 release from that commit in the GitHub UI).

### 2026-08-22 — Phase 0 re-run on the physical machine (M5 Mac)

- Environment discovered and recorded under "Machine facts": macOS
  26.6.2 arm64, uv 0.12.1, Blender 5.2.0 LTS, UE 5.8 **with** Epic's
  `ModelContextProtocol` plugin shipped in the engine tree. Both DCCs
  the project targets are present on one machine for the first time.
- `uv sync --all-extras` built the venv on CPython 3.11.15
  (aarch64). First `uv run pytest` after a bare sync failed 24 /
  errored 17 purely on missing optional extras; after the full sync:
  **340 passed, 2 skipped, 50 deselected** in 73.66s. Nothing in the
  cloud-built code is Linux-only at the Python level.
- **New platform defect found (macOS-only, would never appear in the
  Linux cloud container):** the TEE bridge add-on's `_IOLoop.close()`
  tears the listener socket and the selector down from the *calling*
  thread while the `tee-bridge-io` thread is blocked inside
  `selectors.DefaultSelector().select(0.2)`. Linux `epoll` tolerates
  this; macOS `kqueue` raises `OSError: [Errno 9] Bad file descriptor`
  out of `kqueue.control()`. In GUI Blender `stop_gui()` runs on the
  main thread, so every add-on disable/reload on macOS would print an
  I/O-thread traceback into Blender's console. Surfaced here as
  `PytestUnhandledThreadExceptionWarning` during the suite. **Fixed
  2026-08-22** — see the Phase 2 close-out entry below.

### 2026-08-22 — Phase 2 close-out on the physical machine (M5 Mac)

- **macOS teardown defect fixed** (the "fix pending" item above).
  `_IOLoop` now carries a wake socketpair; `run()` tears its own sockets
  down in a `finally`; `close()` sets the stop event, wakes the loop,
  joins the I/O thread, and only tears down inline once that thread has
  exited. `start_gui` claims thread ownership *before* starting the
  thread so `close()` cannot race a loop that has not yet entered
  `run()`; teardown is idempotent under a lock, so `run_blocking()`'s
  close-after-run stays correct.
- **Quantified, not assumed.** A 25-run harness on this Mac, with the
  I/O thread parked in `select()`: **pre-fix 25/25 runs raised**
  `OSError(EBADF)` on the I/O thread, **fixed 0/25**. A first
  single-shot GUI attempt did *not* reproduce, because it stopped the
  bridge immediately after traffic — the one window where the thread is
  not inside `select()`. Reproduced properly by stopping while idle,
  which is what a user disabling the add-on actually does.
- **GUI-mode validation (the Phase 2 gap this machine was owed).** A
  real windowed Blender 5.2 (`background=False`), bridge served from the
  working tree:
  - batches execute through the main-thread `bpy.app.timers` pump;
    two-object batch returned a 365-byte diff-only response;
  - the **GUI-only `undo_push` path ran for the first time** — every
    prior live test was `--background`, where that branch is skipped.
    `ed.undo()` unwound exactly the batch (5 → 3 objects), the session
    survived (probe still true), `ed.redo()` restored it. This is the
    hard invariant from script step 4 (#77557) and it holds.
  - side-by-side idle-disable in real GUI Blender, Blender's own Python
    3.13: pre-fix printed `Exception in thread tee-bridge-io ...
    OSError: [Errno 9] Bad file descriptor` from `kqueue.control()`
    into the console; fixed printed nothing.
- **Live matrix restored to both flavors.** The official Blender Lab MCP
  add-on *is* installed on this machine, as an extension (package `mcp`
  under the extensions dir) rather than the cloud's source-checkout
  layout, so conftest's hardcoded path silently skipped all 25
  official-flavor tests here. `find_official_addon()` now recognises
  both shapes and globs the per-OS extension dirs;
  `TEE_BLENDER_MCP_ADDON` is now authoritative when set (a wrong
  override skips loudly instead of quietly using a different install).
- **Last three acceptance bullets executed live**
  (`tests/test_blender_acceptance.py`):
  - 100-object scene summary measured on the bytes an MCP client
    receives (in-memory `Client` → `TextContent`): **under the 500-token
    bound**, and the call is recorded in the response-size log;
  - **Blender exiting mid-session**: probe flips false, the next call
    fails in well under 30s with `adapter_unavailable` + fix hint (never
    hangs), and after relaunch on the same port a resync rebuilds the
    cache from the fresh scene — the pre-restart entity is gone;
  - **bake as an async job**: a real rigid-body world is configured
    first (without one `ptcache.bake_all` returns instantly and the test
    would be vacuous); job id returns immediately, polls to done, and
    the cube is verified to have fallen 4.0 → 1.0 m, resting on its
    half-height.
- **Shipped, not just fixed.** The zip under `releases/` was still
  0.1.1, built before the teardown fix — rebuilt and validated as
  **0.1.2** with real Blender, then exercised as an *installed*
  extension: enable → bridge starts → disable → silent. That run also
  confirmed 0.1.1's busy-port fix live (auto-start hit :9876 held by
  another Blender and reported the one-line remedy instead of breaking
  enable).
- Evidence: `uv run pytest` → **342 passed, 2 skipped**; `-m dcc` →
  **55 passed** (25 official + 25 tee + 5 new acceptance, both flavors
  live on this machine for the first time); `ruff check src tests`
  clean.
- Repo hygiene: `server/.tee/memory.json` was tracked while the suite
  appends a record to it every run, so every session began with a dirty
  tree. `.tee/` is now gitignored and untracked — it is per-machine
  runtime state.

**Still owed on this machine (not Phase 2):** Phase 3 (UE 5.8), Phase 5
UE benchmark scenarios, GPU generation lanes, live UEFN (needs Windows).

**Resolved 2026-08-22:** `ruff format --check` failed on 47 files, so
`make check` had never passed on a clean checkout. The first diagnosis
here — formatter version drift — was WRONG: `uv.lock` pinned ruff
0.16.4 as far back as the Phase 12 commit, so every cloud session ran
the same formatter. `ruff format` had simply never been run across the
tree, and every "ruff clean" in this log above means `ruff check`
alone. Tree formatted in one mechanical commit; the codegen/physics/
uefn program literals were verified byte-identical across the reformat
(string constants compared directly, plus both live suites re-run,
which execute those generated programs). `make check` now passes end to
end and the format gate stays in `make lint`.

### 2026-08-22 — Phase 3 discovery: live UE 5.8.1 MCP server (M5 Mac)

Scratch project created at `~/Documents/Unreal Projects/TeeProbe` (hand-written
BP-only `.uproject`, no modules, `ModelContextProtocol` + `AllToolsets`
enabled — `OkongoSim` inside the engine tree is an empty `Intermediate/`
leftover, not a project). Editor launched with
`-ModelContextProtocolStartServer -ModelContextProtocolPort=8000`; the
server came up with no sign-in or EULA dialog.

Engine is **5.8.1** (Changelist 56057345), not the 5.8.0 the corpus was
written against. Live-probed facts, several of which correct doc 07:

- Handshake works exactly as documented: protocol `2025-06-18`,
  `Mcp-Session-Id` returned on initialize.
- **`serverInfo.name` is EMPTY** (`{"name":"","title":"","version":""}`),
  not the `unreal-mcp` doc 07 says it "always" is. TEE must never
  identify the server by `serverInfo.name` — capability-probe instead.
- **`tools/call` answered plain JSON, not SSE.** Doc 07 states clients
  must handle SSE frames on the `tools/call` POST (with
  `Accept: application/json, text/event-stream`, which was sent). On
  5.8.1 the server chose JSON for every call measured. The connector
  must therefore handle **both** shapes and not assume either.
- Tool-search mode confirmed on: `tools/list` returns only
  `list_toolsets` / `describe_toolset` / `call_tool`, **1,719 bytes**.
- **55 toolsets** advertised, not the 52 doc 07 recorded for 5.8.0.
  *(Corrected later the same day: this line first said 67. The
  count came from a naive `- ` line filter, and toolset
  descriptions carry their own bullet lists — 12 of those were
  being counted as toolsets, and were briefly offered to the
  model as callable names. See the Phase 3.5 entry.)*
- `describe_toolset` cost, measured on this machine (inner text chars,
  tokens at 4 chars/token):
  - `BlueprintTools` — 79,713 wire bytes, 72,168 chars, **~18,042
    tokens in a single call** (doc 07 predicted ~74,300 chars: confirmed)
  - `ActorTools` — 19,204 bytes, 17,142 chars, ~4,285 tokens
  - `ProgrammaticToolset` — 3,398 bytes, 3,091 chars, ~772 tokens
  - `list_toolsets` — 13,286 bytes

  One `describe_toolset(BlueprintTools)` costs **more than six times**
  TEE's entire always-loaded 16-tool surface (~2,757 tokens). This is
  the measured justification for the A4 summarizing/caching proxy, and
  the baseline any Phase 5 UE benchmark is measured against.

### 2026-08-22 — Phase 3 build, part 1 (connector + proxy + batch lane)

Built against the live editor, not the digest. Steps 3.1–3.4 of the script
are done; 3.5 (TEE toolsets in a content plugin), 3.7 (vision/assertions)
and the Blueprint-DSL acceptance bullet are still open.

- **Connector** (`adapters/unreal/wire.py`): stdlib-only Streamable-HTTP MCP
  client — handshake, `Mcp-Session-Id`, strictly serial dispatch, per-call
  timeouts, one automatic re-handshake when a session is dropped. Parses
  **both** plain-JSON and SSE bodies rather than betting on either.
- **Catalog** (`catalog.py`): toolset names resolve by **suffix** against the
  live `list_toolsets`, never hardcoded — Epic's module paths drift between
  point builds. `describe_toolset` is fetched at most once per toolset per
  session and the raw payload never leaves the server.
- **Summarizer** (`summarize.py`): `BlueprintTools` **18,042 → 2,097 tokens
  (88.4% saved)**. The script's flat "<10% of raw" acceptance was **not met
  and was amended, not quietly missed** — see DECISIONS **A25**: the ratio
  rewards bloat in the input (`AssetTools` costs the model 4× less than
  `BlueprintTools` yet scores worse), and reaching 10% requires dropping the
  doc lines, which costs more tokens than it saves (two `ue_describe_tool`
  round-trips at ~390 tokens each already exceed the 806 tokens the docs cost
  for all 53 tools).
- **Batch lane** (`codegen.py`, `adapter.py`): one `execute_tool_script` per
  batch. Live: 3 actors spawned + configured in **one call, 3.3s, 553-char
  diff** — the "spawn + configure actors via one macro call" acceptance
  bullet.

**The load-bearing performance fact for this phase:** each in-editor
`execute_tool` costs **~0.37s**, serialized on the game thread. Batching HTTP
round-trips is therefore not sufficient — the number of *tool dispatches*
inside a script matters just as much. The first listing did 2 dispatches per
actor: 21 actors took **15.7s** and blew the 60s test timeout as the level
filled. Redesigned to TEE's own progressive-disclosure rule: listing is **one
dispatch regardless of scene size** (names fall back to the refPath's object
name, which is free), labels and transforms are detail fetched only for
entities actually asked about, and snapshots read transforms only for actors
TEE itself moved. Measured after: **list_entities 15.7s → 1.52s**, snapshot
0.67s, restore 0.99s, live suite **146s + timeout → 21.8s green**.

**Undocumented sandbox constraints found by execution** (none of them in
`get_execution_environment`'s own instructions):

- tool results are `_StrictDict`: `.get(key, default)` is rejected, only
  direct `[]` access works;
- the ops array must be embedded as JSON text parsed in-script, never as
  Python source — JSON `null` is not a Python literal and `NameError`s as
  soon as an optional field is absent;
- names guessed from the docs were wrong: it is `get_label` (not
  `get_actor_label`), and `find_actors` requires `collision_channels` on top
  of `name` and `tag`.

- Scratch project for this work: `~/Documents/Unreal Projects/TeeProbe`,
  level `/Temp/Untitled_1` (unsaved, so the test actors do not persist).
- Evidence: 17 offline + 10 live UE tests; full suite **359 passed, 2
  skipped**; `-m dcc` **65 passed** (Blender both flavors + Unreal);
  `make check` green.

### 2026-08-22 — Phase 3 build, part 2 (Blueprint authoring + ue_* surface)

- **Blueprint DSL authoring with verification Epic does not do** — the
  acceptance bullet "Blueprint function authored and compiled with
  diagnostics via graph DSL", done in one round-trip (4.3s, compile clean).
  The reason it needed more than a passthrough: **`write_graph_dsl` silently
  drops statements it cannot resolve.** Writing
  `(fn Broken () (return (NoSuch|Node|Here :A 1)))` returns success, reads
  back as `(fn Broken ())` — body gone — and
  `compile_blueprint(warnings_as_errors=True)` then reports the Blueprint
  **clean**. Every signal Epic exposes says the authoring worked while the
  function is empty; that is exactly the hallucinated-call failure this
  project exists to remove. TEE writes, reads back, and compares *structure*
  (textual comparison would false-alarm because the engine normalizes
  `Utilities|Operators|Add` to `+`), failing with the unresolved node id and
  what the graph actually holds.
- **`ue_*` surface**: 8 virtual tools behind progressive disclosure
  (`ue_toolsets`, `ue_toolset`, `ue_describe_tool`, `ue_call`,
  `ue_blueprint_function`, `ue_graph_dsl_docs`, `ue_entity_detail`, plus
  `ue_script` when code exec is enabled). `tee serve --adapter unreal` works.

**Two defects of TEE's own, found by exercising the surface:**

- `ue_toolsets` advertised **toolsets that do not exist**: descriptions in
  `list_toolsets` contain their own `- ` bullet lists and the parser counted
  them as entries (67 where there are **55**), handing the model names like
  "FX-related operations in levels or blueprints" as callable. Fixed, with a
  regression test whose fixture reproduces the interleaved bullets. The
  earlier "67 toolsets" line above is corrected in place.
- Blueprint authoring was not re-runnable (`create` raises when the asset
  exists). Now idempotent, verified live: second run reports reused
  blueprint + graph and still compiles clean.

**Third finding, in Epic's sandbox rather than TEE:** a tool failure inside
`execute_tool_script` is **not catchable** — neither `except RuntimeError`
nor `except Exception` intercepts it; the sandbox aborts the whole script and
returns the message as bare text. This contradicts
`get_execution_environment`'s own instruction that `execute_tool` "raises
RuntimeError on failure - no error checking is needed". Consequences now
baked into the design: scripts achieve idempotency by **checking** before
acting (`AssetTools.exists`, `list_graphs`), never by catching, and the
Blueprint compile runs as a **separate call** so diagnostics come back
instead of a dead script.

**Phase 3 remaining:** busy-state probe (compiling / PIE / level load) and
modal-dialog hang detection (3.2); TEE toolsets in a content plugin — PIE
start/stop and the gated editor-Python escape hatch (3.5); vision +
assertions (3.7). The 5.3–5.7 fallback tier has no engine on this machine
and stays **n/a**.

- Evidence: **364 passed, 2 skipped**; `-m dcc` **69 passed** (Blender both
  flavors + Unreal live); `make check` green.

### 2026-08-22 — Phase 3 ACCEPTED (live UE 5.8.1, M5 Mac)

Acceptance run end to end against the running editor
(`5.8.1-56057345+++UE5+Release-5.8`):

1. **spawn + configure actors via one macro call** — 3 actors, **3.3s, 152
   tokens**, short ids returned (refPaths never leave the server);
2. **Blueprint function authored and compiled with diagnostics via graph
   DSL** — compile clean, **5/5 DSL forms verified present** by readback;
3. **`describe_toolset` never forwarded raw** — worst ratio **17.1%**
   (bound: 20%), largest summary **2,396 tokens** (bound: 2,500), and no
   `refPath` / `inputSchema` text reaches the model (per DECISIONS A25);
4. **text-first evidence** — 16/18 actors in frustum in **72 tokens**;
   budgeted capture 13,434 B, 2744×1820 → 640×424;
5. **rollback** — actor set restored to the snapshot;
6. **fallback tier 5.3–5.7** — **n/a**, no such engine installed here.

**TEE content plugin** (`adapters/unreal/TeeToolset`): content-only, no C++
module to compile. Most of what the script planned for it is already shipped
by Epic on 5.8.1 (StartPIE/StopPIE/IsPIERunning, viewport capture, frustum
queries, Blueprint DSL) and the script says not to re-port those. The real
gap is **unsandboxed editor Python** — Epic's script lane cannot import
`unreal` at all — so the plugin exposes exactly that, inside a named
`ScopedEditorTransaction`. Opt-in twice: the plugin ships disabled, and TEE
refuses to call it without code exec allowed. Verified live: installing it
took the catalog 55 → 56 toolsets.

**Further doc-vs-reality corrections found by running it** (all now handled
in code, none of them in doc 07):

- object-typed parameters documented as *optional* are **required**; the
  server answers `input param "X" needs a default value` and names the
  parameter, so the catalog builds the missing value from that parameter's
  own schema and retries;
- that generic filler is **not** safe everywhere: a zero-filled
  `captureTransform` silently photographed the **world origin** instead of
  the viewport (`cameraLocation` came back 0,0,0). The capture path fetches
  `GetCameraTransform` and passes it explicitly, with a test asserting the
  image really came from the editor camera;
- `CaptureViewport` has **no resolution parameter** and returns whatever the
  viewport is (2744×1820 here), so the byte budget is enforced client-side by
  re-encoding to JPEG down a rung ladder.

- Evidence: **369 passed, 2 skipped**; `-m dcc` includes 21 live UE tests
  alongside Blender's both flavors; `make check` green.
- Scratch project: `~/Documents/Unreal Projects/TeeProbe` (plugin installed
  under its `Plugins/`, assets under `/Game/TeeProbe`).
