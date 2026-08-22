# TEE Research Corpus — Index & Architecture Decision Record

*Produced by a deep-research pass on 2026-08-21 (11 parallel research agents,
primary sources: official Epic/Blender/Anthropic docs, project repos, issue
trackers). These digests ground the build plan in `CLAUDE_EXECUTION_SCRIPT.md`.
Facts are version-stamped; where an installed version differs, verify
empirically and record it in `docs/PROGRESS.md`.*

## Corpus

| Doc | Covers |
|---|---|
| [01-unreal-automation-surfaces.md](01-unreal-automation-surfaces.md) | UE5 Python Editor Scripting, remote execution channel, Remote Control HTTP/WS, commandlets, Blueprint reachability, Verse/UEFN, Live Coding |
| [02-blender-automation-surfaces.md](02-blender-automation-surfaces.md) | bpy architecture (`bpy.data` vs `bpy.ops`), main-thread rules, headless/bpy-wheel modes, extensions platform, geometry nodes, OSL/GLSL, physics |
| [03-existing-mcp-bridges.md](03-existing-mcp-bridges.md) | blender-mcp, unreal-mcp family, Maya/Houdini/Unity MCPs, failure modes from issue trackers, second-generation typed-tool designs |
| [04-token-efficiency-techniques.md](04-token-efficiency-techniques.md) | Quantified token costs & mitigations: tool-definition budgets, Tool Search Tool, PTC, code-execution-with-MCP, prompt caching, context editing, image token math, scene-graph representations |
| [05-user-friction-points.md](05-user-friction-points.md) | Catalogued user complaints (version drift, token burn, setup pain, no rollback/persistence) + mitigation per point |
| [06-studio-pipeline-techniques.md](06-studio-pipeline-techniques.md) | Professional patterns: persistent daemons, Remote Control presets, Datasmith/Omniverse deltas, Flamenco/Shaman content addressing, job compilers, USD/glTF |
| [07-epic-official-unreal-mcp.md](07-epic-official-unreal-mcp.md) | Epic's UE 5.8 `ModelContextProtocol` plugin: 830 tools/52 toolsets behind 3 meta-tools, BlueprintTools graph DSL, extension APIs, measured payload costs, setup facts |
| [08-mcp-client-compatibility.md](08-mcp-client-compatibility.md) | What Claude Code/Desktop/Cursor/API connector actually honor: list_changed, resource_link, outputSchema hazards, image paths, defer_loading/PTC, lint rules |
| [09-blender-change-detection-rollback.md](09-blender-change-detection-rollback.md) | msgbus vs depsgraph handlers, `session_uid` keying, undo-push invariants (#77557), background undo (#60934), snapshot rollback |
| [10-blender-version-baseline.md](10-blender-version-baseline.md) | Blender 5.x baseline decision, 4.5→5.2 breaking-change fault lines, bpy wheel matrix, official Blender Lab MCP internals & wire protocol |
| [11-drawing-cad-extraction.md](11-drawing-cad-extraction.md) | Deterministic drawing/CAD extraction: pdfplumber, ezdxf DIMENSION ground truth, ifcopenshell, raster/OCR fallback, scale-inference ladder, license traps (PyMuPDF AGPL, CubiCasa NC) |
| [12-photo-satellite-pipeline.md](12-photo-satellite-pipeline.md) | Local photo/satellite preprocessing: EXIF/GPS, phash dedupe, token-budget-first crops & contact sheets, web-mercator math, footprint datasets & licenses |
| [13-video-pipeline.md](13-video-pipeline.md) | Zero-token video pipeline: PySceneDetect keyframes, sharpness/dedupe, imageio-ffmpeg, faster-whisper, DJI SRT telemetry, sparse-only pycolmap SfM boundary |
| [14-claude-vision-extraction.md](14-claude-vision-extraction.md) | Claude vision mechanics: patch token formula & caps, image caching, PDF handling, coordinate grounding limits, measured VLM accuracy bands, structured-output extraction |
| [15-extraction-prior-art.md](15-extraction-prior-art.md) | Prior art: docling/unstructured/marker, media MCPs, FML v3 schema precedent, Bonsai/IFC Blender handoff, content-addressed cache patterns |
| [16-extraction-channels.md](16-extraction-channels.md) | VLM extraction channels: MCP sampling post-mortem, in-band vs API-key drivers, elicitation limits, honest cost framing |
| [17-sheets-heights-roof-schema.md](17-sheets-heights-roof-schema.md) | Sheet classification (NCS metadata-first), elevation/section Z-extraction, FML height/roof schema extension before freeze |
| [18-frames-and-registration.md](18-frames-and-registration.md) | Frame registry, transforms-as-facts, site ENU hub, tier ladder, footprint-fit registration, conformance tolerance math (USIBD LOA) |
| [19-context-economics.md](19-context-economics.md) | Phase 8 grounding: app-side script lane (PTC pattern), tool-result eviction economics, columnar encodings, caption-once, the BM25 negative result |
| [20-free-asset-sources.md](20-free-asset-sources.md) | Free asset/texture/HDRI sources: APIs, license regimes, ToS traps, tier-1 backends, attribution manifest spec |
| [21-asset-plumbing.md](21-asset-plumbing.md) | Blender 5.2 asset libraries/catalogs/previews headless, remote-library JSON listings, import paths, glTF free metadata, UE 5.8 Interchange/registry, unit math |
| [22-asset-prior-art.md](22-asset-prior-art.md) | Measured prior art: ahujasid/BlenderKit/asset MCPs wire costs and bug classes, Holodeck selection pattern, steal/avoid lists |
| [23-generative-3d.md](23-generative-3d.md) | Text/image-to-3D 2026: TRELLIS.2 MIT flip, Hunyuan territory trap, hosted API pricing, mandatory cleanup pipeline, honest quality bar, USCO IP status |
| [24-texture-material-generation.md](24-texture-material-generation.md) | Image-model license floor (Z-Image/klein/SDXL), tileability, Marigold-IID photo→PBR, scene-conditioned ControlNet loop, procedural lane (Infinigen, physicallybased.info) |
| [25-context-aware-assets.md](25-context-aware-assets.md) | Context-aware skill design R1-R24: envelope scaling policy, style facts, relational placement + validators, sun-true lighting, skill packaging, render-free verification |
| [26-player-psychology.md](26-player-psychology.md) | Player motivation models validity-graded (QF GMM N=466k, Trojan Typology, SDT/PENS/BANGS), demographic anchors, encoding licensing rules |
| [27-player-routines.md](27-player-routines.md) | Retention/session percentile benchmarks by platform+genre, Weibull playtime law, cadence-based churn, live-ops norms, dark-pattern regulatory red lines |
| [28-game-ux.md](28-game-ux.md) | Validated UX practice: PXI-not-GEQ, RITE, game-feel/accessibility parameter tables, defaults-dominate evidence, enforce-vs-judge split |
| [29-market-trends.md](29-market-trends.md) | Market 2024-2026 with sourced numbers: Steam economics, genre winners/losers, UGC payouts, AI sentiment gap, small-team opportunity map |
| [30-design-logic.md](30-design-logic.md) | Frameworks standing, encodable economy/progression/pity math, level-design patterns + procgen licenses, one-pager + Cerny macro chart artifacts |
| [31-ai-design-module.md](31-ai-design-module.md) | Prior art verdicts, LLM design failure modes, LLM-proposes-formal-verifies pattern, three-layer knowledge encoding, tee-design/1 spec schema |

## Architecture decisions (ADR)

Settled by this corpus; change only with a new entry in `docs/DECISIONS.md`.

- **A1 — Server:** Python 3.11+, official `mcp` SDK, stdio primary transport.
  *Why:* every surveyed bridge that works uses it; matches Claude Code/Desktop
  expectations; Streamable HTTP optional later. (03, 08)
- **A2 — Blender baseline:** 5.1 minimum, 5.2 LTS primary, 4.5 LTS optional
  legacy tier, never 4.2 (EOL July 2026). *Why:* official add-on requires
  5.1; 5.2 is current LTS to July 2028; the 5.0/5.1/5.2 breaking-change
  clusters make older support a shim-tier concern. (10)
- **A3 — Blender transport:** act as a client of the official Blender Lab
  add-on socket (`localhost:9876`, null-delimited JSON execute protocol);
  ship a same-protocol TEE fallback add-on. *Why:* zero-install for official
  users; the official server has no extension point, but its add-on socket is
  multi-client by design. (10, 09)
- **A4 — Unreal primary:** proxy + extend Epic's official UE 5.8 MCP
  (`127.0.0.1:8000/mcp`); register TEE toolsets via the documented Python
  extension API; **no custom C++ Blueprint plugin.** *Why:* 830-tool official
  surface incl. full Blueprint K2 graph DSL makes a from-scratch bridge
  redundant; the measured token sinks (describe_toolset 74–127K chars,
  unpaginated lists) are exactly what a proxy fixes. (07)
- **A5 — Unreal fallback:** Remote Control (30010/30020) + Python remote
  execution (UDP 239.0.0.1:6766 / TCP 6776) for 5.3–5.7; commandlets for
  headless. *Why:* pluginless, documented, used by existing bridges. (01, 06)
- **A6 — Client compat floor:** no `outputSchema`; self-sufficient
  `structuredContent`; inline base64 images only (no `resource_link`); plain
  object `inputSchema`s; ≤ 40 tools, ≤ 2 KB descriptions; progressive
  disclosure via TEE meta-tools, not protocol notifications. *Why:* verified
  client-by-client failure modes, several silent. (08)
- **A7 — Security floor:** localhost binds; gated + AST-screened +
  auto-checkpointed code-exec tools; never expose DCC sockets off-machine.
  *Why:* none of the DCC-side sockets have auth; official docs say VM
  isolation is the mitigation. (10, 03)
- **A8 — Extraction license floor:** deterministic-first extraction stack
  (pdfplumber, pypdfium2, ezdxf, ifcopenshell-as-dependency, OpenCV,
  pytesseract/RapidOCR, Pillow, ImageHash, PySceneDetect, imageio-ffmpeg,
  faster-whisper; shapely/pyproj/pymap3d/rasterio for registration); CI
  lint bans PyMuPDF (AGPL), marker, ultralytics/FastSAM, CubiCasa5K and
  DeepFloorplan weights; ffmpeg/exiftool subprocess-only. Speaker
  diarization (pyannote.audio) is optional-only: MIT code but HF-gated
  models needing a user token — degrade to non-diarized, never require. *Why:* the
  floor-plan ML landscape is a licensing minefield and everything needed is
  achievable with permissive tools. (11, 12, 13, 15)
- **A9 — Extraction channel:** in-band host-model extraction is the default
  (prepared tiles + `ex_store_facts` writeback); server-side API-key driver
  optional as async jobs; MCP sampling ruled out (deprecated 2026-07-28,
  unimplemented in Claude Code/Desktop). *Why:* verified client reality;
  channel-agnostic Extractor keeps the tool surface identical. (16)
- **A10 — Fact model:** content-addressed facts keyed (media_hash,
  extractor_id, extractor_version); FML v3-derived plan schema extended
  with per-level heights + parametric roof before freeze; frame_id on every
  geometric fact; transforms as first-class facts in a single-parent tree
  anchored at site ENU; tier precedence (dimension text > drawing geometry
  > SfM > GPS prior > satellite/footprint); conflict facts ARE the
  conformance report; EPSG:3857 fetch-only. *Why:* the AEC
  written-dimensions-govern rule, REP-105/GeoPose precedent, and scan-to-BIM
  tolerance practice all converge on this shape. (17, 18, 15)

- **A11 — Script lane:** chatty tool loops run app-side as one
  `tee_script` call: an AST-whitelisted mini-Python executor over the SAME
  typed virtual tools (call/batch/facts helpers), auto-checkpointed and
  atomic, hard-bounded (calls/nodes/wall-clock), returning only the final
  result. *Why:* programmatic tool calling is the API-native shape for this
  but excludes MCP tools; simulated 86% context cut on the conformance fix
  loop and −61% session cost with eviction. Adds no capability beyond the
  typed tools, so it is not code-exec-gated. (19)
- **A12 — Context-economics floor:** adaptive columnar encoding in the
  budgeter (list-of-dicts ≥ 20 rows, ≥ 60% shared keys → cols/rows, marked);
  eviction-safe response contract + `tee_status(recap=true)` one-call
  resume (≤ 500 tokens); caption-once media pass (`kind: "caption"` facts
  gate re-attachment). Fact search stays substring-count: BM25 was
  simulated and regressed (9/10 → 7/10 at 611 facts). (19)

- **A13 — Asset backends & license hygiene:** tier-1 sources Poly Haven,
  ambientCG, Poly Pizza, Smithsonian OA (Sketchfab guarded opt-in; Fab is
  human-download-then-import only; ShareTextures/OGA/Objaverse excluded).
  Server-side asset store owns catalogs (ETag-cached), thumbnails,
  downloads and a local index — the model sees compact rows, never
  catalogs. Per-backend ASSET-license and SITE-ToS tracked separately;
  SPDX allowlist (CC0-1.0, CC-BY-4.0/3.0; SA behind a flag) failing
  CLOSED on NC/ND/unknown/GPL; TASL+SPDX attribution manifest with
  license text snapshotted at download time travels with the cache;
  cache files, never URLs. (20, 21, 22)
- **A14 — Creation lanes & generation floor:** lane 0 procedural
  (node-graphs parameterized from physicallybased.info CC0 values;
  Infinigen BSD as reference library); lane 1 local diffusion (Z-Image
  Apache / FLUX.2-klein-4B Apache / SDXL-RAIL++ tileable; Marigold-IID
  maps; diffusers in-process, ComfyUI separate-process only); lane 2
  photo-derived PBR from ingested site media (rectify → delight → maps →
  Real-ESRGAN); lane 3 generated 3D — local TRELLIS.2-4B MIT (audit
  nvdiffrast out of runtime) + hosted Tripo/Meshy behind ONE async
  adapter with server-side wait-polling and cost-confirmation-before-
  paid-call; every generated asset passes the mandatory cleanup macro
  (normalize → remesh/decimate → UV → re-bake) and carries an
  ai-generated provenance fact. Gated, clearly labeled, never default:
  FLUX-dev, SD3.5, Hunyuan (geo-restricted). Banned: MobileCLIP weights,
  pysolar, Intrinsic, InstantMesh/Zero123++, pymeshlab-in-process.
  Honest bar: set dressing on demand; hero assets curated. (23, 24)
- **A15 — Selection & context contract:** Holodeck-shaped selection — the
  model emits {description, target dims, constraints}; server-side
  retrieval ranks tags → ΔE00 palette → index-time SigLIP-2/CLIP
  embeddings and returns ≤5-row shortlists; one ≥256 px-tile contact
  sheet only as tie-breaker. Placement is a relational plan solved and
  validated server-side (Merrell terms as hard validators; code vs
  guideline severity; region-parameterized from the GPS datum);
  four-band measured-size envelope policy governs scaling; sun-true
  lighting from the GPS datum (astral/pvlib) with HDRI azimuth detected
  once and cached; verification is render-free geometry first with at
  most one budgeted render; packaged as the `context-aware-assets` skill
  (Agent Skills standard, scripts-not-prose). (25, 22, 18)

- **A16 — Design knowledge encoding:** three layers matched to content
  type — versioned reference tables for enumerable facts (benchmark
  percentile grids, genre conventions, economy archetypes, scope-cost
  weights, UX parameters; every figure carries source + as_of; estimates
  labeled), ONE `game-design` skill for judgment and procedure, and
  executable checkers run via the script lane. No fine-tune; RAG optional
  long-tail only. Instruments: PXI/miniPXI default, never GEQ
  (unvalidated); never bundle proprietary instruments or paywalled report
  tables (Feist facts-only rule; EU database right). (26, 27, 28, 31)
- **A17 — Design spec & verification contract:** the source of truth is
  the machine-verifiable `tee-design/1` spec (core_loop, economy graph,
  progression, level_macro beat chart, content_list by asset class,
  open_questions); the prose GDD is a rendered view. LLM proposes,
  formal system verifies — cost-ordered battery: design-lint → scope
  estimate → economy timestep simulation per persona → progression
  validator → bounded self-play transcript → in-engine last. Spec
  sections map 1:1 to build phases (content_list feeds the Phase 9 asset
  module; level_macro feeds blockouts). Existing GDLs rejected (VGDL
  dead/2D, Ludii NC-ND, PuzzleScript tile-only). (31, 30)
- **A18 — Evidence & ethics floor:** benchmarks encoded as percentile
  grids per platform/genre, never folk targets; UX rules split
  enforce-vs-judge (text/subtitle/contrast/photosensitivity/latency/
  remapping enforced; juice/DDA/diegesis judged, with juice capped per
  the inverted-U evidence); dark-pattern rules carry code severity
  (disclosed odds, single-conversion pricing, streak grace, no
  minor-targeted countdown pressure, reward presence never punish
  absence, binge → care not upsells) grounded in FTC/EU-CPC/Belgium/
  Australia/Brazil enforcement; AI-content defaults: disclose, keep
  invisible-infra or clearly stylized, never voice/likeness without
  consent (SAG-AFTRA 2025). (27, 28, 29)

## Headline numbers worth remembering

- Tool definitions can eat 20–40% of a 200K context (~710 tokens/tool);
  deferred loading cuts definition tokens ~85%; code-execution-with-MCP
  measured up to 98.7% total reduction. (04)
- A 1920×1080 screenshot ≈ 2,691 tokens; a budgeted ~1024×576 JPEG ≈ 777;
  geometric text assertions cost a few dozen. (04)
- Raw scene dumps stop scaling around ~120 objects; a real user burned 60% of
  a $200/mo plan in 2 hours on one donut scene without these mitigations. (04, 05)
