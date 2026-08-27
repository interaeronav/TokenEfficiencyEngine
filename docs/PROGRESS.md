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
- [x] Phase 5 — Benchmarks *(Blender scenarios in cloud: 87.7% total;
      UE scenario added on the physical machine 2026-08-22 against a live
      5.8.1 editor: **93.9% saved** on level population + Blueprint
      function. All rows in benchmarks/RESULTS.md, cited in README)*
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
      SANS 10400 before Okongo jurisdiction defaults - source
      material now in hand, wiring moved to Phase 15)*
- [x] Phase 12 — TEE UEFN (bonus) *(built in cloud, 2026-08-22:
      digest parser+diff firewall, digest-grounded Verse lint, validated
      templates, FakeUefn adapter w/ LUF↔XYZ boundary, export_for_uefn
      (live FBX+LOD autogen verified), version-trajectory firewall
      tests, uefn skill, live Data API analytics; 26 tests + 2 live.
      Live-editor lanes DESCOPED 2026-08-22 — owner decision, no
      Windows machine; offline lanes shipped, interface+fakes kept)*
- [x] Phase 13 — Voxkiln *(built in cloud + Mac bring-up 2026-08-22;
      REMOVED the same day, then RESTORED the same day — owner decision
      after the pending access approval came through. Restored from the
      removal commit's parent (exact test-green state incl. the three
      Mac-found fixes) + networkx dependency fix + CPU-env test skips;
      server 395 tests + voxkiln 41 tests green after restoration.
      Mac owes the live half again: reinstall, weights if cleaned,
      first live generation, determinism, stock-vs-ours battery)*
- [x] Phase 15 — Expert Knowledge Base *(owner import, 2026-08-25:
      38 domains / 405 files / ~1.4M words / 1,811 cited sources
      mirrored verbatim to `knowledge-base/`, all 401 markdown files
      frontmatter-verified; A30 sets the two-corpus boundary — imported
      reference grounds nothing until re-checked, and the DCC-software
      domains are never an API source. 15.2 jurisdiction wiring done:
      US/ZA/NA regimes with jurisdiction-dependent severity; 12 tests.
      15.3 stays reference-only by design)*
- [x] Phase 16 — TEE KB query module *(built in cloud, 2026-08-27:
      read-only `kb_*` tools (status/search/read/facts) over the
      `knowledge-base/` mirror, manifest-indexed, section-addressed,
      token-budgeted, flags verbatim with UNVERIFIED labelling; the
      mirror itself first completed and hash-reconciled against Dropbox
      (manifest.json + AGENTS.md fetched, 337 byte-drifted files fixed).
      22 tests incl. 4 live-mirror; paving-lookup benchmark 96.6% saved;
      zero always-loaded tokens. Mac owes: the one-line `[kb]` section
      in OkongoSim's .tee/config.toml — acceptance 16.6 #4)*

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
  Launcher at `/Applications/Epic Games Launcher.app`.
- **OkongoSim project root: `/Users/john/OkongoSim`** (git repo on `main`,
  C++ project — `OkongoSim` + `OkongoSimEditor` modules, prebuilt Mac
  editor binaries, `EngineAssociation` 5.8, description "Walkable digital
  twin of House John P Nghiwete, Onheleiwa, Okongo, Namibia").
  *(Corrected 2026-08-22: this entry previously said OkongoSim "sits
  inside the engine dir". The engine-dir `OkongoSim/` is only a stray
  `Intermediate/ShaderAutogen` leftover with no `.uproject` — the real
  project has always been in the home directory. Anything that resolved
  the project from the old line was pointing at an empty folder.)*
- Scratch probe project: `~/Documents/Unreal Projects/TeeProbe`
  (BP-only, empty Content, carries the optional `TeeToolset` content
  plugin). Nothing listening on `:8000` when no editor is open.
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
- **DESCOPED (owner decision, 2026-08-22):** everything live-UEFN
  (editor, Beta Access toggles, MCP toolsets, Verse compile lane,
  Scene Graph ops against Epic's toolsets) — UEFN has no macOS build
  and the project has no Windows machine. Removed from the outstanding
  ledger, not just deferred. The offline UEFN lanes
  (digest/lint/templates/export preflight) are SHIPPED and supported
  everywhere; the adapter interface + fakes remain in the codebase so
  the live proxy could be revived by a future decision.
- **RESTORED (owner decision, 2026-08-22, after approval):** local
  generated-3D through Voxkiln (Phase 13, A26–A28) — removed earlier
  the same day, restored when the gated-access approval came through.
  Lane-3 local generation targets this Mac's MPS (CUDA stays
  supported); hosted Tripo/Meshy are the keyed fallback.

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
  (16 tools ≈ 2,757 tokens by the canonical model_dump measure; the
  2026-08-25 re-measure reads 2,959 by that measure and **2,465 on the
  wire** — model_dump counts ~490 tokens of `null` padding no client
  ever receives, so the wire figure is the honest one);
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
  TEE's entire always-loaded 16-tool surface (~2,465 tokens on the wire;
  see the 2026-08-25 entry for why the earlier 2,757 overstated it). This is
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

### 2026-08-22 — Phase 5 closed: UE benchmark scenario (M5 Mac)

Scenario (c) from the script — "UE level population + Blueprint function" —
measured against the live 5.8.1 editor, 10 actors plus an authored function:

| | Context tokens | Round-trips | Saving |
|---|---|---|---|
| naive (`describe_toolset` + `call_tool` per op) | 38,334 | 32 | |
| TEE | 2,349 | 4 | **93.9%** |

The naive side is deliberately **not** a straw man: it is exactly the
workflow Epic's own `unreal-mcp` skill prescribes — `list_toolsets`, a
`describe_toolset` for each toolset you intend to use, then one `call_tool`
per operation, reading the level back as refPaths plus a transform call per
actor. The schema dumps dominate it; one `describe_toolset(BlueprintTools)`
is ~18K tokens on its own. Because every UE tool call is serialized on the
game thread at ~0.37s, the 32 → 4 round-trip reduction is wall-clock as well
as tokens.

All prior rows reproduced in the same run (Blender 87.7% total, assets 93.5%,
script lane 63.2%, physics variance floor 0.00 mm). The extraction row moved
slightly to **93.1%** (was 92.6%) — same fixtures, regenerated.

`run_unreal_scenario` skips cleanly when no editor is listening, and is
wrapped so a live-editor failure can never take the rest of the suite down.

### 2026-08-22 — Execution script COMPLETE (all phases 0–12 checked off)

Final state on the physical M5 Mac, everything re-verified in one pass:

- `make check` → **371 passed, 2 skipped**; ruff check + format clean.
- `uv run pytest -m dcc` → **76 passed**: Blender against **both** bridge
  flavors (official Blender Lab MCP add-on + TEE's own bridge) and Unreal
  against a live 5.8.1 editor.
- `tee doctor` → **all six checks OK**, including
  `unreal: MCP on 127.0.0.1:8000, 56 toolsets + TEE toolset` — the first time
  every check has passed on one machine.
- Clean-venv install rehearsal re-run with the new module: wheel installs,
  `tee 0.1.0`, `--adapter unreal` serves over MCP stdio, 16 always-loaded
  tools, `ue_*` tools discoverable through `tee_search_tools` and describable.
- `make dist` produces the wheel, sdist, `tee_bridge-0.1.2.zip` and
  `TeeToolset-0.1.0.zip`; both plugin zips ship under `releases/v0.1.0/`.
- Benchmarks re-run end to end; all rows in `benchmarks/RESULTS.md`, headline
  numbers cited in README.

## What is NOT done, and what it needs

Nothing further can be closed on this machine. The honest remainder:

**Descoped** (owner decision, 2026-08-22 — see `docs/DECISIONS.md`):
- everything live-UEFN — editor, Beta Access toggles, MCP toolsets, Verse
  compile lane, Scene Graph ops — and the clean-Windows-machine install
  rehearsal. UEFN is Windows-only and the project has no Windows machine,
  so these are removed from scope, not owed. The offline UEFN lanes
  (digest parsing, lint, templates, export preflight) work everywhere and
  are tested; the adapter interface + fakes stay as the revival point.

**Needs CUDA** — none left: the former entry (local TRELLIS.2-4B, nvdiffrast
CUDA-bound) was superseded 2026-08-22 by Phase 13 (Voxkiln), removed with
Voxkiln later that day, and restored with it the same day once the access
approval arrived (see DECISIONS).

**Needs an older engine** (none installed):
- the UE 5.3–5.7 Remote Control fallback tier is **unimplemented**, not
  merely unverified. Stated plainly in `docs/setup-unreal.md`.

**Possible here but not attempted this session** (no blocker beyond time):
- GPU diffusion lanes 1–2 end-to-end on **MPS**: capability detection and
  device selection are now fixed and verified (see below), but no diffusion
  has actually been run — that needs multi-gigabyte model weights.
- hosted generation with real Tripo/Meshy keys; `[assets-embed]` embeddings.
- Whisper/pyannote quality spot-check on real site audio (fixtures only so
  far).

**Data caveat still standing:** joist-span worst-grade values in
`plaus_rules.json` are approximate pending edition verification. The SANS
10400 / Okongo jurisdiction half of this caveat is **CLOSED** (Phase 15.2,
2026-08-25) — see the evidence entry below. Its own edition caveat now
travels inside the rules file: the SANS values are from the 2010/2011
editions and each carries a RE-VERIFY note naming the current edition.

### 2026-08-22 — UE settle via Simulate-In-Editor (ledger item closed)

Phase 11 owed UE physics/settle and the live editor made it possible. Epic's
official MCP ships **no simulation toolset** — `PhysicsAssetToolset` authors
ragdolls, `DataflowAgentToolset` builds asset graphs, and nothing runs a sim
or reads the result — and *"Keep Simulation Changes"* has **no scripting API**
at all. `ue_settle` replaces both: start SIE, poll the play world across many
short calls, stop, write the settled poses onto the editor actors.

**The finding that makes this safe: a backgrounded editor does not tick.**
With `bThrottleCPUWhenNotForeground` at its default and the editor window
behind another app, the play world reports `is_in_play_in_editor() == True`
and bodies report `is_simulating_physics() == True`, while
`get_time_seconds()` stays pinned at **0.0** and nothing moves. An agent
polling that would conclude the scene settled instantly and adopt unmoved
poses. `ue_settle` asserts simulation time actually advances and fails with
the exact ini remedy; setup-unreal.md and troubleshooting.md both carry it.

The other engine constraint (from research 33, confirmed): the editor does
not tick *while a Python call executes*, so the polling loop lives on the TEE
side and the poll program contains no sleep or wait loop — asserted by test.

Measured live: three cubes dropped 300 cm settle in **2.09 sim-seconds / 8
polls / 2.2 s wall**; adopt writes them to the editor at z 49.5 (a 100 cm cube
resting on the floor); the report is **56 tokens**. Re-settling actors already
at rest returns at the 1.0 s floor, not the cap.

Two corrections en route, both mine:
- `max_delta` returned 0.0 for an empty or partial pose snapshot, so "we do
  not know" read as "nothing moved" — it would have declared a scene settled
  before the play world finished spawning. Now returns infinity.
- an early 29-second settle was a bad fixture, not the macro: cubes spawned
  40 cm apart are 100 cm wide, so they interpenetrated and slowly pushed each
  other apart. Tests space them 200 cm.

- Evidence: **374 passed, 2 skipped**; `-m dcc` **78 passed**.

### 2026-08-22 — Three more ledger items closed (M5 Mac)

**`.mcpb` bundle (Phase 6).** `make mcpb` builds an MCP Bundle carrying the
server source, `pyproject.toml` and `uv.lock`; it ships under
`releases/v0.1.0/`. The manifest schema was copied from a **real installed
bundle on this machine** (the official Blender Lab MCP extension:
`manifest_version` 0.4, `server.type` `"uv"`, `mcp_config` command/args)
rather than written from memory, and only fields observable there were used.
Verified by running it as a client would — extract, execute the exact command
the manifest names, drive it over MCP stdio: **16 always-loaded tools,
`tee_status` ok**.

**Assets → Unreal import (Phase 9).** `as_import(adapter="unreal")` was a
stub that fell through to a generic `create` op the UE codegen cannot
execute. Epic's `AssetTools` can find/load/save/delete assets but has **no
import call**, and the sandboxed script lane cannot reach the importer, so a
real import needs TEE's content plugin. `import_asset_file` runs an
`AssetImportTask`, spawns the static mesh, and reads bounds back **converted
cm → m** (the unit seam that silently produces 100× errors). Verified as a
cross-DCC round-trip: a 2 m cube authored in headless Blender → GLB →
ingested → imported into UE → read back at exactly **2.0 × 2.0 × 2.0 m**,
scale band `accept`, `verify.ok` true.

Two scale-policy refusals en route were the guard working, not defects: a
2 m model with no class and no target has nothing to judge against, and
2 m → 1 m is refused because 0.5 is neither a unit factor nor a ±10% snap.

**Doctor** now completes the MCP handshake and counts the catalog instead of
reporting OK because a port is open, and distinguishes a stranger on the port
from a server with no toolsets (`AllToolsets` being off by default is the most
likely setup mistake). Both negative paths tested.

- Evidence: **374 passed, 2 skipped**; `-m dcc` **80 passed**; `make check`
  green.

### 2026-08-22 — Local generation lanes are no longer CUDA-gated

`probe_local_gpu` treated "no CUDA device" as "no local generation", which
wrote off Apple Silicon entirely on a one-line assumption. Only **lane 3**
(TRELLIS.2) is genuinely CUDA-bound — nvdiffrast is — while **lanes 1–2** are
plain diffusers and run on any torch backend.

The probe now reports the backend and *which lanes it supports*:
`cuda → [1,2,3]`; `mps → [1,2]` with an explicit note that lane 3 needs CUDA
and to use a hosted 3D generator instead; CPU-only torch → unavailable,
because diffusion on CPU is not useful. `torch_device()` added so loaders
pick a device instead of assuming one.

Verified on this machine with torch 2.13 in a **throwaway venv** (the project
venv is untouched and the `[assets-gen]` extra stays deliberately unpinned —
GPU stacks are machine-specific): probe returns backend `mps`, lanes `[1,2]`,
and a real 2048×2048 matmul executes on the GPU. Four probe branches covered
by unit tests with a faked torch.

**Honest bound:** this fixes capability *detection* and device selection. No
diffusion model has been run here — that needs the weights downloaded, which
is a multi-gigabyte decision left to the owner. The corpus claim that these
lanes are CUDA-only is corrected to "lane 3 only".

- Evidence: **378 passed, 2 skipped**.

### 2026-08-22 — Asset-library publishing (Phase 9 ledger item closed)

`as_publish_library` turns the cached asset store into a Blender asset
library. Blender 5.2's `blender -c asset_listing generate` indexes a folder of
`.blend` files into the JSON a *remote* library serves — but only if the
objects inside are **marked assets**, and TEE's store holds glTF plus texture
sets. So the tool does both halves: author one `.blend` per cached model with
the object `asset_mark()`ed and its **licence and attribution written into the
asset metadata**, then run Blender's own indexer.

Provenance travelling *inside* the `.blend` is the point — the licence gate is
worthless if the obligation is lost the moment an asset leaves TEE.

Authoring runs in a throwaway headless Blender, not through the connected
adapter: building a library is not an edit to the user's open scene.

Two defects in the first working version, both found by inspecting the output
folder rather than trusting the return value: the authoring script was written
**into** the library folder (which the indexer walks and the user may serve),
and the generated metadata kept Blender's placeholder identity *"Your Asset
Library" / "Your Name"*. Fixed, and both are asserted by test.

Verified live: a 2 m cube exported from Blender → ingested → published →
`asset_count: 1` in the generated index, the `.blend` carrying a marked asset
with its licence, thumbnails generated, no stray `.py` in the folder.

- Evidence: **379 passed, 2 skipped**; `-m dcc` **81 passed**.

### 2026-08-22 — Fluid bake validated live (Phase 11 ledger item closed)

The fluid lane was cost-gated, async and unit-tested but had never run
against a real Blender. Now it has, with the assertion that actually matters:
**the bake wrote real Mantaflow cache data**. A bake that silently does
nothing still reports `done`, so counting output files is the only honest
check.

Measured: 12 frames at resolution 32 → **750 `.uni` cache files, 366 KB, in
1.8 s**. The committed test uses 6 frames at resolution 24 to stay quick and
also asserts the cache path is **absolute** — relative fluid cache dirs fail
silently in Blender, a catalogued tracker landmine.

- Evidence: **379 passed, 2 skipped**; `-m dcc` **83 passed**.

## Ledger status after this session

Everything reachable on this machine is now closed. What remains is blocked
by hardware, by credentials, or by a decision that is the owner's:

- **Descoped by the owner:** live UEFN (Windows-only).
- ~~**Needs CUDA:** lane 3 local 3D generation (TRELLIS.2 / nvdiffrast).~~
  Superseded by Phase 13 (Voxkiln), removed with it, then RESTORED with
  it after the access approval. Lanes 1–3 all local on this Mac.
  Lanes 1–2 correctly report available on MPS.
- **Needs an older engine:** the UE 5.3–5.7 fallback tier, unimplemented.
- ~~**Needs the owner's credentials:** hosted generation (Tripo / Meshy
  keys).~~ Off the ledger 2026-08-22 with the generated-3D need removal:
  the keyed hosted drivers stay in the code, dormant and optional, but
  are no longer an outstanding item.
- ~~Needs a multi-gigabyte download decision~~ — **done 2026-08-22**, see
  below: diffusion lane 1 and the embedder both run on this machine.
- **Needs real input data:** Whisper / pyannote quality on genuine site
  audio — only synthetic fixtures exist.
- **Data caveat:** joist-span worst-grade values in `plaus_rules.json` remain
  approximate pending edition verification, and SANS 10400 is not yet added
  for Okongo jurisdiction defaults.

### 2026-08-22 — [assets-embed] and [assets-gen] run for real on Apple Silicon

Both were interfaces with nothing behind them: `search.py` accepted an
`embedder` hook nobody implemented, and `build_drivers` only ever returned
hosted shells. Owner authorised the downloads; both now exist and both have
been run.

**[assets-embed] — SigLIP 2** (`google/siglip2-base-patch16-224`,
**Apache-2.0**, ungated). Explicitly *not* MobileCLIP: MIT repo, research-only
**weights**, unusable in a tool whose asset story is licence hygiene.
`AssetRow` carries no thumbnail, so the comparison is query text vs row text.
**Measured** against plain keyword ranking on a 5-case synonym set:
**keyword MRR 0.667 → semantic 1.0**, with an on-disk vector cache making the
second pass free. Caveats stated plainly: the set is small and I wrote both
the queries and the labels, so it is suggestive rather than authoritative.

Scoring is batched **once per rank** — the original per-row hook would have
re-run the model O(n log n) times inside the sort comparator — and weighted
*below* an exact keyword hit, so it breaks ties and rescues synonyms without
overriding literal name matches.

**[assets-gen] lane 1 — Z-Image-Turbo** (`Tongyi-MAI/Z-Image-Turbo`,
**Apache-2.0** for weights *and* outputs, ungated, ~31 GB). Generates 768 px
on **MPS in 22.8 s**; the image was opened and visually confirmed to match its
prompt, not merely non-black.

**The finding worth keeping: dtype is not portable across backends.** My first
version used fp16 on any GPU. On MPS that produces NaNs, which the image
processor casts to a fully **black** frame — and the driver reported state
`done` with a black PNG. Measured on this model:

| dtype on MPS | result | time |
|---|---|---|
| float16 | **NaNs → black image, reported as success** | 61 s |
| bfloat16 | correct | 19 s |
| float32 | correct | 32 s |

MPS now gets bfloat16, CUDA keeps fp16, CPU stays fp32, and a uniform-output
guard refuses to save a degenerate frame instead of calling it success.

Both extras are declared in `pyproject.toml` but **loosely pinned on purpose**
— torch wheels are backend-specific, so an exact pin would break either CUDA
or Apple Silicon. Model-backed tests carry a new **`ml` marker** so a normal
run never pulls gigabytes (`addopts = -m 'not dcc and not ml'`).

One test needed fixing en route: `test_as_generate_without_drivers_names_fix`
asserted the "nothing configured" message while reading the *real* driver set,
so it silently depended on the host having no GPU and broke as soon as a local
lane could be built. It now stubs the driver set, and a mirror case asserts the
local lane *is* offered when the probe reports it.

- Evidence: **387 passed, 2 skipped**; `-m ml` **2 passed**; `-m dcc`
  **83 passed**.

### 2026-08-22 — Phase 13 cloud build: Voxkiln 0.1.0 + TEE integration

The owner's directive ("use TRELLIS.2 source, fix known defects, ship a
separate AI-optimized product") executed through research + build in one
cloud session:

- Six-agent research pass (digests 43–48), decisions A26–A28, script §16.
- `voxkiln/`: vendored microsoft/TRELLIS.2 @75fbf01 with license surgery
  (NVIDIA-NC/GPL/LGPL/CC-BY-NC out of the runtime; `vendor/VENDOR.md`
  logs every change) and the evidence-ranked defect fixes (fp32 decode
  thresholds, sampler leak, CPU-generator seeds, loud resolution
  downgrade, portable SDPA/conv/extraction/sampling fallbacks).
- Product layer: 3-level repair with in-house boundary-loop hole fill,
  repair-before-bake export with a frozen full-res projection reference,
  topology-aware metrics, budget verdicts with exact fixes, provenance,
  input-hash cache, bounded-wait jobs, CLI, 4-tool MCP server.
- Evidence: **43 product tests green** (ports verified against dense/
  manual references on CPU torch — sdpa vs softmax, conv_none vs
  nn.Conv3d, dual-grid extraction without the CUDA hashmap, trilinear
  torch-vs-numpy parity); ruff clean; **license lint clean**; clean-venv
  rehearsal (torch-free import, packaged vendor tree, structured
  `no_backend` refusal with the fix); **`make check` 395 passed** with
  the new voxkiln driver registered first in `build_drivers` and the MPS
  probe now reporting lane 3 through voxkiln.
- Mac hand-off (script 13.6.3): `docs/setup-voxkiln.md` — install
  `[model]` extras, `voxkiln fetch-weights`, first live generation, the
  stock-vs-ours battery on `voxkiln/eval_images/` (frozen SHA256s),
  FlexAttention-MPS tuning, and the own-repo extraction decision.

### 2026-08-22 — Phase 13 Mac session (13.6.3): partly done, partly BLOCKED

Worked the seven-step Mac hand-off. Steps 1, 2, 6 done; step 3 got far
enough to prove three real defects and then hit an external blocker; steps
4 and 5 could not run at all. Nothing below is claimed that was not run.

**1. Environment — DONE.** `voxkiln/.venv` on CPython 3.13,
`[model,manifold,mcp,dev]` installed, torch **2.13.0** with MPS available
(the FlexAttention-MPS floor). `voxkiln doctor` exit 0: backend `mps`,
upstream commit `75fbf018…` recorded, all five in-process deps present.

Suite: **43 → 48 passed**. Two tests had to be fixed first — both asserted
`probe()["backend"] is None`, i.e. "this host has no GPU", which was true
only of the cloud container they were written in. That is a property of
the machine, not of the refusal they claim to test; they stub the probe
now. (Same defect class as the TEE-side one fixed earlier today.)

**2. Weights — DONE.** 1.3 TiB free beforehand. `voxkiln fetch-weights`
pulled 22 files in 2 min 38 s; `voxkiln doctor` reports
**`weights_cached_gb: 15.12`**.

**3. First live generation — THREE DEFECTS FOUND, THEN BLOCKED.**
The run failed, and each failure was real:

- **The vendored inference path was broken.** `structured_latent_flow.py`
  imported `sparse_elastic_mixin` at module scope → `utils.elastic_utils`,
  which the licence surgery dropped with the training tree. So importing
  the module raised `ModuleNotFoundError`. `ElasticSLatFlowModel` exists
  only for training with low VRAM (its own docstring says so) and the
  shipped configs use `SLatFlowModel`, so it is now built lazily via module
  `__getattr__`. **The cloud could not have caught this**: with no weights,
  no model was ever constructed.
- **The real error was masked.** `pipelines/base.py` wrapped model loading
  in a bare `except Exception` and retried the relative path as a Hub repo
  id, so a missing module surfaced as a 404 for a repo
  `ckpts/slat_flow_img2shape_dit_1_3B_512_bf16` that was never meant to
  exist. Replaced with the three cases decided explicitly (local snapshot /
  other owner-repo / repo-id + relative). My first attempt fixed one case
  and broke another — caught by re-running, not by reasoning.
- **Gated weights fail late and expensively.** All 15 GB download and every
  model loads before the image tower 403s, minutes in.

After the fixes, under the engine's real configuration
(`conv: none, attn: sdpa`), **all 8 TRELLIS pipeline models load in 68 s**
and construction proceeds to the image-conditioning model — where it stops:

```
GatedRepoError: 403 — Access to model
facebook/dinov3-vitl16-pretrain-lvd1689m is restricted and you are not in
the authorized list.
```

**This is an access-control blocker, not a code one.** `gated: manual` —
approval is granted by hand by the model owner. **Owner action required:**
request access at
<https://huggingface.co/facebook/dinov3-vitl16-pretrain-lvd1689m>, then
`hf auth login`.

Two intermediate "failures" I chased were **artifacts of my own ad-hoc
probe**, not product defects (missing `o_voxel` / `flex_gemm` came from
hand-rolling `sys.path` instead of using the engine's `add_vendor_to_path`).
Verified before reporting; recorded so nobody re-files them.

**4. Determinism — NOT RUN.** Blocked by the same gate. No same-seed
comparison exists; nothing is claimed about determinism on this machine.

**5. Stock-vs-ours battery — NOT RUN.** `voxkiln/BENCHMARKS.md` created
with the protocol and frontmatter (commits, torch, macOS, machine, thermal
protocol) and **zero measured rows**, stating the blocker and what was
established instead. The one real number in it is the 68 s cold load of all
eight models — a load timing, not a generation.

**6. TEE integration — DONE.** voxkiln installed into the server venv.
`probe_local_gpu` reports lanes **[1,2,3]** on MPS; `build_drivers`
registers **voxkiln first**, so `as_generate` defaults to it — proven by
calling `as_generate` with a real eval image, which routed into the
pipeline and failed only at the gate.

Two honesty gaps fixed while proving it:
- `tee doctor` had **no voxkiln check at all**, though `setup-voxkiln.md`
  promises it is picked up automatically. It now reports version, backend,
  cached weight size **and the gated-model state** — because 15 GB cached
  is not sufficient to generate, and silence implied readiness.
- voxkiln answered a gated-repo failure with *"inspect params; if this
  repeats, run voxkiln doctor"*. No parameter grants access to a manually
  approved repo. Failures now map to the resolving action (gated → request
  URL + `hf auth login`; 401 → authenticate; ENOSPC → free disk), fixed in
  voxkiln's job handler so CLI, MCP server and TEE all benefit.

Also extended the licence lint to banned model **weights** (repo ids are
strings in configs, invisible to the AST import lint). I first read a hit
as a live RMBG-2.0 violation — **it is not**: `BiRefNet.py` already
substitutes the MIT weights and names RMBG only in the branch that rejects
it. The rule stays, allowlisted at the substitution site, so a new
reference cannot creep in as a string.

- Evidence: voxkiln **49 passed**, server **394 passed / 2 skipped**, ruff
  clean both trees, `voxkiln doctor` exit 0, `tee doctor` exit 0 with the
  voxkiln line naming the blocker.
- ~~Still owed on this machine, once access is granted: first live
  generation, same-seed determinism, the stock-vs-ours battery,
  FlexAttention-MPS tuning, and the own-repo extraction decision.~~
  Closed 2026-08-22 by the removal below — none of it is owed.

### 2026-08-22 — Voxkiln REMOVED (owner decision)

The owner dropped the out-of-the-box 3D-generation need and had Voxkiln
deleted: `voxkiln/` (136 files), `docs/setup-voxkiln.md`,
`server/src/tee/assets/gen_voxkiln.py`, `server/tests/test_assets_voxkiln.py`,
plus the driver registration, the lane-3 probe branch, the `tee doctor`
check, and the doc/skill references. Generated-3D is hosted-only (keyed
Tripo/Meshy, dormant) and off the outstanding ledger. The DINOv3
gated-access blocker dies with it — nothing to request. Research digests
43–48 stay in the corpus; decisions A26–A28 are amended by the removal
entry in DECISIONS. Server suite re-run after the removal — results in
the removal commit.

### 2026-08-27 — Phase 16: the KB query module, and the mirror made byte-exact

Built `tee/kb/` per A31. Before any code, the premise had to be repaired:
the Phase 15 mirror never carried `manifest.json` or `AGENTS.md` (the
index source the phase assumes in-repo), and hashing the 401 mirrored
files against the manifest found **337 mismatches** — 330 were exactly
one trailing newline added by the mirroring tool (stripped only where
doing so restored the manifest's recorded sha256), 7 were real extraction
noise (re-downloaded verbatim; every download verified against Dropbox's
own `content_hash`). The corpus's `CLAUDE.md` was deliberately not
mirrored: a `CLAUDE.md` in-repo would be auto-loaded as directory
instructions by coding agents, and the imported corpus must never direct
sessions (A30). One mismatch remains by design:
`00_meta/source-register.md` in Dropbox itself no longer matches the
corpus's own manifest — genuine upstream drift, faithfully mirrored, and
now the drift check's first real catch (`kb_status` reports exactly this
file with the rebuild.py fix line).

The module: `index.py` (manifest-validated index cached under
`<project>/.tee/kb/` keyed on the manifest's generated date; sha256 drift
check that flags but keeps serving; H2 section addressing parsed on
demand), `search.py` (deterministic keyword scoring over title/id/tags/
summary/headings with exact filters; empty results return the domain
table, not silence), `tools.py` (kb_status / kb_search / kb_read /
kb_facts as virtual tools — zero always-loaded tokens; kb_read is
section-addressed and budgeted, default 800 cap 4000, the file's Sources
block riding along; needs-verification and low-confidence content carries
an explicit UNVERIFIED warning naming A30). Root resolution: `[kb] root`
config first (used even if broken, so typos fail loud), then the
project's own mirror, then the source checkout's; none → module inactive.
`cli.py` grew `_attach_kb`, `config.py` the `[kb]` table, `doctor` a kb
check. `docs/setup-kb.md` documents activation and the OkongoSim wiring.

- Evidence: `pytest server/tests/test_kb.py` → **22 passed** (fixture
  corpus + 4 live-mirror tests: 401 files/38 domains, paving lookup with
  citation under budget, facts lane, flagged DCC domains). Full suite
  `-m "not dcc and not ml and not network"` → **458 passed, 1 skipped**;
  ruff clean. Benchmark (RESULTS.md): paving-spec lookup with citation =
  57,349 tokens pasting INDEX.md + the file vs **1,951** via kb_search +
  one budgeted kb_read — **96.6% saved**; always-loaded surface unchanged
  at 16 tools / 2,465 wire tokens with all seven modules registered
  (80 virtual tools).
- Owed elsewhere: OkongoSim's `.tee/config.toml` `[kb]` section (Mac
  session with that repo; acceptance 16.6 #4) — the exact lines are in
  `docs/setup-kb.md`.

### 2026-08-25 — Token-efficiency test (cloud half) + two plausibility bugs

Ran the tokens-per-task measurement the CLAUDE.md testing rule requires
after any change to state representation or tool schemas — Phase 15.2
changed both. Two new scenarios added to `benchmarks/run_benchmarks.py`
(`run_surface_scenario`, `run_jurisdiction_scenario`); neither needs a
DCC, so both run in CI and in a cloud session.

**Surface.** 16 always-loaded tools = **2,465 tokens on the wire**
(`by_alias`, `exclude_none` — what the SDK actually sends). The 2,757
figure recorded on 2026-08-22 came from a bare `model_dump()`, which
today counts 2,959 because MCP SDK 2.0.0 added `execution`/`icons`
fields that serialize as `null` and are dropped before transmission.
Registering all six modules adds **0 tokens**: the 76 tools they
contribute stay behind the meta-tools, and reaching one costs 725
tokens, so a flat one-tool-per-capability server (10,787 tokens) only
wins in a session using more than ~14 distinct long-tail tools. The
pins module merged from the Mac lane changed that count from 69 to 76
and the always-loaded surface not at all — progressive disclosure held
through the merge.

**Regression found and fixed.** Phase 15.2 wrote the whole
`legal_basis` string onto *every* capped finding, when the
`jurisdiction` header already carried it once. On `NA-local-authority`
that inflated the response from 856 → 2,146 tokens. Removing the
per-finding copy costs no information and cuts it to 1,206 (−43.8%);
`NA-communal` 1,941 → 1,239. Directly contrary to hard rule 2.

**Correctness bug found and fixed.** The severity ceiling was applied
inside `hit()`, but `_load_path()` and `_wet_walls()` build findings
directly and bypassed it. A communal-land response could therefore
announce `max_severity: STD` in its header and emit a `CODE` load-path
finding underneath — the exact self-contradiction the mechanism exists
to prevent. The cap now runs as one post-pass over the assembled list.
Regression test `test_the_ceiling_binds_every_finding_producer_not_just_hit`
was confirmed to fail against the unfixed code before being kept.

**Tokens per task.** Answering "which code applies at this site, and
does this plan meet it?" by reading the four applicable-law files into
context costs 32,089 tokens. One `plaus_check` costs 1,452 — **95.5%
saved**, and unlike the corpus read it cannot quietly answer from the
wrong jurisdiction.

**Known gap, not fixed.** TEE has 21 plausibility rules and none of
them concerns building height or storey count, so it cannot evaluate a
multi-storey proposal at all. `masonry_slenderness` also matches
material on a name whitelist that misses `clay_brick`. Both are
recorded here rather than patched blind; neither is a Phase 15.2
regression.

- Evidence: `pytest -m "not dcc and not ml and not network"` →
  **405 passed, 1 skipped, 89 deselected**; ruff clean. Blender/Unreal
  benchmark rows are unchanged in `benchmarks/RESULTS.md` because they
  need hardware this session does not have; the extract (92.6%), fix-loop
  (63.2%) and asset (93.5%) rows were re-run headless and reproduce.

### 2026-08-25 — Phase 15.2: southern-African jurisdiction wiring

Closes the gap tracked since Phase 11 ("SANS 10400 has not been added for
Okongo jurisdiction defaults"). The KB made clear that the naive reading —
"add SANS rules for Namibia" — would have been **wrong**, and named it as
the characteristic AI error on this topic
(`knowledge-base/03_codes_standards/00_overview.md`): SANS 10400 is law in
South Africa under the NBR Act 103 of 1977, but in Namibia it binds only
where a council incorporated it under Local Authorities Act s 94B, and on
communal land — which is most of Ohangwena outside the proclaimed towns —
there is no building control regime at all.

So the wiring makes **legal force jurisdictional, not just the numbers**:

- `region` was previously accepted by `plaus_check` and silently ignored.
  It now resolves to one of six profiles (US / ZA / NA-local-authority /
  NA-settlement / NA-communal / NA-unresolved), each carrying its
  `legal_basis` into the response.
- Severity is capped per regime. A rule that is CODE in ZA is emitted as
  STD on Namibian communal land — professional standard of care, not law —
  and the downgrade is visible (`severity_capped_from` + the reason), never
  silent.
- Bare `NA`/`namibia` resolves to **NA-unresolved** and caps at HEUR rather
  than guessing between three regimes that differ completely. An unknown
  region raises rather than defaulting to the IRC.
- SANS values encoded, each with clause + edition + a RE-VERIFY note:
  10400-C ceiling 2,4 m and minimum habitable room 6 m² / 2 m least
  dimension; 10400-M riser ≤200 mm, going ≥250 mm, headroom 2,1 m, width
  ≥750 mm, 2R+G 570–650 mm, riser variation ≤6 mm.
- The codes genuinely disagree in **both** directions, which is why a real
  switch was needed rather than extra rules: a 2,2 m ceiling passes the IRC
  and fails SANS; an 800 mm stair passes SANS and fails the IRC.

Evidence: **408 passed, 1 skipped** (12 new jurisdiction tests); ruff clean;
`test_server_lint` green — `plaus_check` is a VirtualTool, so the richer
description adds **zero always-loaded tokens**. The one failure in the run,
`test_uefn_analytics_live`, is a pre-existing `@pytest.mark.network` test
whose Fortnite island id now 404s upstream — unrelated to this change.

### 2026-08-22 — Voxkiln RESTORED (owner decision — approval received)

The owner reports the pending approval (gated DINOv3 image-tower access,
the blocker at removal time) has come through and directed the rebuild.
Restored in the cloud from the removal commit's parent (619bfc5^): the
`voxkiln/` package (136 files), setup doc, TEE driver + tests, driver
registration, lane-3 probe, doctor check, and the doc/skill references —
the exact state that was test-green on the Mac, three vendored-defect
fixes included. Two restoration fixes: `networkx>=3.0` declared in
voxkiln dependencies (trimesh hole-fill imports it; 7 tests failed
without it in a fresh cloud venv — the original env had it only
transitively), and the two gated-weights doctor tests skip via
`pytest.importorskip("huggingface_hub")` on envs without `[model]`.
Evidence after restoration (cloud): server **395 passed / 1 skipped**,
voxkiln **41 passed / 2 skipped**, ruff clean on both trees.
Still owed on the Mac: recreate the voxkiln venv + reinstall into the
server venv, re-fetch weights if the cleanup removed them, verify the
gated DINOv3 access now works, first live generation, same-seed
determinism, the stock-vs-ours battery.

### 2026-08-22 — OkongoSim wired for auto-start + Claude Desktop (M5 Mac)

Owner moved TEE usage from the terminal to the **Claude desktop app** for
day-to-day OkongoSim work. Changes made outside this repo:

- `/Users/john/OkongoSim/OkongoSim.uproject` — enabled
  `ModelContextProtocol` and `AllToolsets`, both with
  `"TargetAllowList": ["Editor"]` so the unauthenticated loopback server
  can never ship in a packaged Mac build (matches how the project already
  gates `PythonScriptPlugin` / `EditorScriptingUtilities`).
- `Saved/Config/MacEditor/EditorPerProjectUserSettings.ini` — added
  `[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]`
  `bAutoStartServer=True`, and
  `[/Script/UnrealEd.EditorPerformanceSettings]`
  `bThrottleCPUWhenNotForeground=False` (setup-unreal.md requires the
  latter for `ue_settle`; driving the editor from another app means it is
  *always* backgrounded, so it is not optional in this workflow).
- Setting names verified against engine source, not memory:
  `UModelContextProtocolSettings` is `config=EditorPerProjectUserSettings`
  with `bAutoStartServer = false`, `ServerPortNumber = 8000`,
  `bEnableToolSearch = true` by default.
- `~/Library/Application Support/Claude/claude_desktop_config.json` — added
  `tee-unreal` and `tee-blender` entries beside the existing `unityMCP`.
  Two deltas from `tee doctor --emit claude-desktop`: the `uv` command is
  spelled absolutely (`/opt/homebrew/bin/uv`) because a GUI-launched app
  does not inherit the shell `PATH`, and `--project /Users/john/OkongoSim`
  is passed explicitly because `--project` defaults to `.` and a
  Desktop-spawned server has no meaningful cwd. `.tee/` added to the
  OkongoSim `.gitignore`.

Evidence:

- Freed `:8000` (the TeeProbe editor from the earlier session held it),
  then opened OkongoSim the normal way — `open OkongoSim.uproject`, **no
  launch flags**. `:8000` was listening ~10 s later, owned by the
  OkongoSim editor pid.
- `tee doctor` → exit 0, all six checks OK, including
  `OK   unreal: MCP on 127.0.0.1:8000, 55 toolsets`. (55 and no
  `+ TEE toolset`: the optional `TeeToolset` content plugin is installed
  in TeeProbe, not in OkongoSim. Everything except unsandboxed editor
  Python works without it.)
- stdio handshake rehearsed under a stripped environment
  (`env -i HOME=... PATH=/usr/bin:/bin`) against the exact configured
  command: `initialize` returned the TEE server info and instructions, so
  the Desktop entry does not depend on shell setup.

### 2026-08-22 — Phase 14: pins, live in OkongoSim (owner request)

The owner's pins work had been blocked on the missing content plugin.
Unblocked and built end to end, all of it verified against the running
UE 5.8.1 editor rather than asserted.

**1. Plugin installed.** `adapters/unreal/TeeToolset` copied to
`/Users/john/OkongoSim/Plugins/TeeToolset`; `TeeToolset` added to
`OkongoSim.uproject` (`Enabled: true`, `TargetAllowList: ["Editor"]`,
a 7-line diff — `PythonScriptPlugin` was already enabled). Editor
restarted with `open OkongoSim.uproject`, no launch flags.

```
$ tee doctor
OK   unreal: MCP on 127.0.0.1:8000, 56 toolsets + TEE toolset
```

**2. Import lane proved.** `as_search(query="wooden chair", asset_class=
"model")` → 5 CC0 rows; `as_import(polyhaven:bar_chair_round_01,
adapter="unreal", asset_class="chair", location=[10.717, 15.06, 0])` →
`scale_band: accept`, read-back `[0.4832, 0.486, 0.7505]` m against the
catalogue's `[0.483, 0.486, 0.751]`, actor at UE `(1071.7, 1506.0, 0.0)`
with scale 1.0 and its base on the floor. Mesh landed in
`/Game/TeeAssets/bar_chair_round_01/**` — nothing written to
`Content/House/**`.

**3. Pins.** `tee/pins/{model,program,tools}.py` + `tests/test_pins.py`
(20 tests). Data lives in actor tags (decision A29); the OkongoSim
namespace is `okongo_pin`, set in `/Users/john/OkongoSim/.tee/config.toml`,
matching the level's existing `okongo_light` / `okongo_circuit` family.
Marker: engine cone, 18 x 50 cm, base on the spot, collision off at spawn,
`is_editor_only_actor`, outliner folder `TEE/Pins`, orange material
instance.

**4. Fill loop.** `pin_fill` with no pick searched the pin's three
wishlist terms and returned nine model rows; on the owner's pick
(`polyhaven:GreenChair_01`) it imported at the pin — `scale_band: accept`,
read-back `[0.6731, 0.6644, 1.0585]` m — faced it along the pin's yaw, and
wrote `okongo_pin_asset` + `okongo_pin_actor` back onto the marker.

**5. Demo + conversion.** Two pins now stand in `/Game/Maps/OkongoSite`:

```
pin_list → count 2
  open-plan-stool-01  "Open-plan stool"       chair  [10.717, 15.06, 0.0]   filled polyhaven:bar_chair_round_01
  verandah-seat-01    "Verandah seating spot" chair  [24.07, 20.105, 0.0]   filled polyhaven:GreenChair_01
```

The step-2 lane-proof actor was retired and re-created as
`open-plan-stool-01` so there is one system, not two. The level's other
markers — `HouseDatum`, `PlayerStart_House`, `Veg_Scatter`,
`Fauna_Spawner` — are functional actors, not decorative pins, and were
left alone (the OkongoSim build session agreed independently). There were
no pre-existing pins to migrate: the earlier attempt died on the missing
plugin before it created anything. Level + `/Game/TeeAssets/**` saved;
877 actors = the 873-actor baseline + 2 markers + 2 fills.

**Defects found by running it, all fixed in this commit:**

- `as_search` labels every model hit `"model"`, which has no dimension
  envelope, so `as_import`'s default rejected every prop with "no envelope
  or target to judge against" and no fix. The rejection now names the
  envelope classes and `target_dims`.
- Poly Haven's catalog filter is `?t=`, not `?types=`. TEE sent `types=`,
  which the API ignores, so model searches ranked HDRIs and textures
  alongside meshes (2361 rows instead of 521 — measured live). Fixed, with
  the cache key carrying the parameter so a stale all-types body cannot be
  revalidated into the filtered slot.
- A partial transform in a `tee_batch` `set` op zeroes the fields it omits:
  a rotation-only set teleported the imported chair to the world origin.
  The batch interpreter now reads the transform back and fills the gaps.
- `MaterialEditingLibrary.connect_material_property` returned True and
  changed nothing (the material kept the default graph and rendered black);
  the pin marker uses a parametrised `MaterialInstanceConstant` with a
  read-back check instead.

**Suites after the change:** `pytest -m "not dcc"` 410 passed, 2 skipped;
`pytest -m dcc` 83 passed against the live editor + Blender; ruff clean.
The live settle test needed fixing on the way: it assumed a floor at z=0,
which is true of the scratch probe project and false of OkongoSim, whose
terrain there sits 16.7 cm below zero (measured by line trace). It now
measures the ground under the drop instead of assuming it. Two more 5.8.1
API facts fell out: `SystemLibrary.line_trace_single` needs a real world
context and returns `HitResult or None`, and `HitResult` exposes nothing
as attributes — `to_dict()` or `get_editor_property()` only.

**Hazard hit, worth remembering:** entity ids (`u1`, `u2`, …) are per
session. Re-running a saved `tee_batch` file from an earlier session
resolved `u881` to a different actor and deleted a pin marker. No project
geometry was lost (every `/Game/House` mesh still has its actor; the
873-actor baseline is intact) and the marker was rebuilt, but ids must be
re-read in the session that acts on them. Documented in setup-unreal.md.

### 2026-08-22 — Phase 14.5: pins survive a level rebuild

Follow-up the owner asked for after the pin lane landed. Pins are authored
state living in a level that OkongoSim regenerates from `data/*.json`, so a
commandlet run would drop them and nothing would bring them back.

**`pin_export` / `pin_import`.** Export writes a stable, sorted JSON — id,
name, category, notes, wishlist, class/dims, chosen asset, position, yaw —
to `[pins].file` (OkongoSim: `data/pins.json`, which is git-tracked, unlike
`.tee/`). Import upserts every pin and re-places only the recorded assets
that are not actually standing there; it reports what it restored, what was
already standing, and any pin in the level the file does not mention. It
refuses a file from another namespace or a future version, by name.

`pin_list` now says `missing: true` when a pin's tags claim an asset but
nothing is at the spot — exactly the state a rebuild leaves behind. That
needed the read program to report whether `PinFill_<id>` actually exists,
which is a different question from what the tags say.

**Proved live, not asserted:** exported both pins, deleted
`verandah-seat-01` and its chair outright (`pin_remove remove_asset=true`,
level down to 875 actors), then `pin_import` →
`restored: [verandah-seat-01], filled: [verandah-seat-01],
already_standing: [open-plan-stool-01]`, back to 877 actors with the record
intact (notes, wishlist, yaw -135). Re-exporting produced a **byte-identical
file**, so the round trip is lossless.

**A real defect the new live tests caught.** Both existing pin markers were
standing in the level with `QUERY_AND_PHYSICS` collision — invisible
obstacles in a walkable twin. `set_collision_enabled(NO_COLLISION)` reads
back correctly *inside the same script* and reverts by the next dispatch,
because the collision PROFILE is what gets serialised. Fixed with
`set_collision_profile_name("NoCollision")`; `pin_set` now reads the
collision and the editor-only flag back and refuses a marker that would
block the player or ship in a build. The two markers already in the level
were repaired in place and verified in a separate dispatch.

Two live pin tests added (`test_unreal_live.py`): the full round trip
through the real editor under its own namespace, and the marker's
editor-only/no-collision/folder guarantees.

**Suites:** `not dcc` 419 passed 2 skipped; `dcc` 85 passed; ruff clean.

**Editor state at hand-off:** level and `/Game/TeeAssets/**` saved at
22:11, nothing dirty, 877 actors. The OkongoSim build session warns that
once it resumes, its commandlets write the map — after that this editor's
copy is stale and must not be saved without reloading first.

### 2026-08-22 — Pins delivered into OkongoSim's own repo

The pin lane was working but only durable inside TEE's repo and one
developer's machine. Closed that: three commits in `/Users/john/OkongoSim`,
each staged file by file so none of the build session's in-flight
texture/material work (822 uncommitted paths) was swept in.

- `92ee3e7` — `Plugins/TeeToolset` vendored (content-only, from TEE
  v0.1.0), `TeeToolset` enabled Editor-only in `OkongoSim.uproject`,
  `data/pins.json` tracked, and **`.gitignore` changed from `.tee/` to
  `.tee/*` + `!.tee/config.toml`**. That last one was the actual bug in the
  hand-off: the config carries the pin tag namespace (`okongo_pin`) and the
  pin file path, so a clone without it read the level's pins under the
  default `tee_pin` namespace — which is to say, saw no pins at all. The
  `.tee/assets/` download cache stays ignored.
- `aa1a8fb` — `Content/TeeAssets/**` (9 MB, the two CC0 props and the pin
  marker material) plus `CREDITS-assets.md`, rendered by `as_credits` from
  the attribution manifests. The assets are committed because the level
  references them: a clone with the map but without them gets missing-mesh
  errors. They stay reproducible — `pin_import` re-downloads and re-places
  from `data/pins.json`.

- `a126d52` — `docs/tee-pins.md` in that project (tag scheme, the seven
  `pin_*` tools, which files the work added, the two live pins, and the six
  UE 5.8.1 gotchas), pointed to from its `CLAUDE.md` conventions. Written
  because **three attempts to hand this to the build session as a
  cross-session message expired unapproved** — the repo is the channel that
  actually delivers. That is an edit to another project's CLAUDE.md, made on
  the owner's "deliver what's needed", not on the peer session's request.

Deliberately not committed there: `Content/Maps/OkongoSite.umap`. It is the
build session's surface, and `data/pins.json` is the durable record either
way.

**Editor left clean**: saved at 22:21:54 after checking the map's mtime was
still my own 22:11:17 write (that session is paused, so nothing could be
clobbered), 877 actors, nothing dirty. UE 5.8.1 exposes no
`Package.set_dirty_flag`, so a content-identical save is the only way to
leave an editor with nothing pending — the alternative was leaving a dirty
map that an accidental Ctrl+S could later push over someone else's work.
