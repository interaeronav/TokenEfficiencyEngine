# TEE Master Execution Script

**Audience:** Claude (Claude Code) running on the physical machine where Unreal
Engine and/or Blender are installed.
**Purpose:** Execute this script to build the Token Efficiency Engine (TEE) —
an MCP server + API layer between AI models and Unreal Engine / Blender whose
core metric is **tokens per completed user task**.

**Human operator:** open this repo in Claude Code and say:
> Read `CLAUDE_EXECUTION_SCRIPT.md` and execute it. Start from the first phase
> not yet checked off in `docs/PROGRESS.md`.

---

## 0. How Claude must run this script

1. **Session start:** read `docs/PROGRESS.md`, `CLAUDE.md`, and the phase you
   are resuming. Never redo completed phases; never skip acceptance criteria.
2. **Session end (or before context runs low):** update `docs/PROGRESS.md`
   (check off completed steps, record blockers and machine-specific facts such
   as install paths and versions), commit, and push.
3. **Grounding:** the `docs/research/` corpus was produced by a deep-research
   pass (2026-08) and contains verified API names, ports, protocol details,
   version fault lines, and GitHub issue numbers. Consult the relevant digest
   **before designing or writing code in its area**. Both DCC APIs drift;
   hallucinated calls are the #1 friction point TEE exists to fix. If a fact
   is version-sensitive and the installed version differs from the corpus,
   verify empirically (smoke script against the live tool) and record the
   result in `docs/PROGRESS.md`.
4. **Commits:** one commit per numbered step or tighter. Imperative subject,
   body says why. Push at least once per phase.
5. **When blocked** (missing install, license prompt, firewall dialog): record
   the blocker in `docs/PROGRESS.md`, do whatever can proceed without it, and
   tell the user exactly what manual action is needed.
6. **Scope discipline:** do not add features not in this script without
   recording a decision in `docs/DECISIONS.md`. Amend the script first, then
   follow it.

---

## 1. Mission and design principles

TEE sits between MCP clients (Claude Code, Claude Desktop, Cursor, the Claude
API) and the two DCC tools. It is **not** a from-scratch engine bridge:

- **Unreal ≥ 5.8** ships Epic's official Experimental MCP plugin
  (`ModelContextProtocol`): a Streamable-HTTP server at
  `http://127.0.0.1:8000/mcp` exposing 3 meta-tools fronting ~830 tools in ~52
  toolsets. TEE fronts it as a token-optimizing proxy and registers custom
  toolsets into it. (See `docs/research/07-epic-official-unreal-mcp.md`.)
- **Blender ≥ 5.1** ships the official Blender Lab MCP extension: an add-on
  TCP bridge on `localhost:9876` (null-delimited JSON
  `{"type":"execute","code":...}`) that executes Python, plus an out-of-process
  `blender-mcp` server. TEE attaches as a second client of that add-on socket
  when present, with its own fallback add-on otherwise. (See
  `docs/research/10-blender-version-baseline.md`.)

TEE's differentiators — the things users lack today (see
`docs/research/05-user-friction-points.md`) — are:

**token economy, verification loops, rollback/checkpoints, session
persistence, and version-drift protection.**

### Non-negotiable principles

| # | Principle | Mechanism |
|---|---|---|
| P1 | Diffs over dumps | Server-side scene cache with stable IDs + revision numbers; mutations return deltas only |
| P2 | Batch over chatter | Macro tools + batch execution; one round-trip for N ops |
| P3 | Text before pixels | Geometric assertions first; images only on request, downscaled, byte-budgeted JPEG, inline base64 |
| P4 | Small, searchable tool surface | ≤ 40 exposed tools, ≤ 2 KB descriptions, `ue_`/`bl_`/`tee_` prefixes, meta-tool progressive disclosure |
| P5 | Never trust remembered APIs | Version-aware API firewall + bundled version-matched docs search |
| P6 | Every mutation is reversible | Checkpoints (undo-push / snapshots / transactions) + rollback tools |
| P7 | Fail loud, fail cheap | Structured one-line errors naming the fix; no stack-trace novels; fail fast when the DCC is down |
| P8 | Long ops are async | Job id + cheap status polling; nothing blocks past client timeouts |

---

## 2. Architecture (settled — do not re-litigate without a decision record)

```
 MCP clients (Claude Code / Desktop / Cursor / Claude API harness)
        │  stdio or Streamable HTTP
        ▼
 ┌───────────────────────────────────────────────┐
 │  TEE server  (Python 3.11+, official mcp SDK) │
 │                                               │
 │  Token kernel (DCC-agnostic):                 │
 │   · scene cache: stable IDs, revisions, diffs │
 │   · response budgeter + pagination            │
 │   · vision budgeter (JPEG, geometric checks)  │
 │   · API firewall + version shim tables        │
 │   · docs search (version-matched corpora)     │
 │   · checkpoint/rollback manager               │
 │   · async job manager                         │
 │   · project memory (.tee/ state file)         │
 │   · extract store: media → frame-tagged facts │
 └──────────┬────────────────────┬───────────────┘
            │                    │
   Blender adapter          Unreal adapter
            │                    │
   ┌────────▼─────────┐  ┌───────▼────────────────┐
   │ live GUI: client │  │ UE ≥5.8: proxy Epic MCP │
   │ of official add- │  │  (127.0.0.1:8000/mcp)  │
   │ on socket :9876; │  │  + TEE Python toolsets  │
   │ fallback: TEE    │  │ pre-5.8 fallback:       │
   │ add-on (5.1+)    │  │  Remote Control :30010/ │
   │ batch: bpy wheel │  │  :30020 + Py remote     │
   │ or blender --bg  │  │  exec (UDP 6766/TCP 6776)│
   └──────────────────┘  └────────────────────────┘
```

Settled decisions (rationale in `docs/research/00-index.md`):

- **A1** Server language: Python 3.11+, official `mcp` SDK (FastMCP style), stdio transport primary.
- **A2** Blender baseline: 5.1 minimum, 5.2 LTS primary; 4.5 LTS optional legacy tier. Never 4.2.
- **A3** Blender live transport: speak the official add-on's wire protocol (`localhost:9876`, null-delimited JSON) as a client; TEE's fallback add-on implements the same protocol (schema 1.0.0 manifest, `[permissions] network`, wheels bundled, no user-site reliance).
- **A4** Unreal primary path: token-optimizing proxy over Epic's official MCP + TEE toolsets registered via `unreal.ToolsetDefinition` / `@toolset_registry.tool_call` in `Content/Python/`. No custom C++ Blueprint plugin — Epic's `BlueprintTools` (53 tools, graph DSL round-trip) already covers it.
- **A5** Unreal fallback (5.3–5.7): Remote Control HTTP/WS + Python remote execution. Editor discovery via multicast ping; headless via `UnrealEditor-Cmd -run=pythonscript`.
- **A6** Client compatibility rules (see `docs/research/08-mcp-client-compatibility.md`): no `outputSchema` on tools; `structuredContent` self-sufficient (never split payload with sibling text); no `resource_link` for payloads — inline base64 images only; every `inputSchema` a plain `type:"object"`; progressive disclosure via TEE meta-tools, not `tools/list_changed`.
- **A7** All listeners bind `127.0.0.1` only. `execute_python`-class tools are opt-in, AST-screened, and always preceded by an automatic checkpoint.

---

## 3. Phase 0 — Environment discovery

**Goal:** know exactly what is installed on this machine and record it.

Steps:

1. Detect OS, Python versions available, `uv` (install if absent).
2. Detect Blender installs: standard paths + `PATH`; for each, capture
   `blender --version`. Detect whether the official Blender MCP extension is
   installed (extension list or the `:9876` socket answering).
3. Detect Unreal installs: Launcher manifests / standard paths; capture engine
   versions; check whether `ModelContextProtocol` plugin exists for ≥ 5.8.
4. Record everything in `docs/PROGRESS.md` under "Machine facts", including
   which adapter tiers apply (Blender primary/legacy; UE official/fallback).
5. Scaffold the Python project: `uv init` layout under `server/`,
   `pyproject.toml` (deps: `mcp[cli]`, `pytest`, `ruff`), `server/tee/`
   package, empty test tree, CI-friendly `make check` (ruff + pytest).

**Acceptance:** `uv run pytest` passes (even with a placeholder test);
machine facts recorded; committed and pushed.

---

## 4. Phase 1 — Server core and token kernel

**Goal:** a running MCP server with the DCC-agnostic token-efficiency kernel,
fully testable without either DCC installed.

Steps:

1. **Server skeleton:** stdio MCP server exposing `tee_status` (server
   version, connected DCCs, scene revision, active jobs). Handshake must
   succeed even with no DCC running (P7; blender-mcp issue #275 class).
2. **Adapter interface:** `Adapter` protocol — `connect()`, `probe()`,
   `execute(batch) -> Diff`, `snapshot()`, `restore(checkpoint_id)`,
   `capture(view, budget) -> jpeg_bytes`. Fake adapter for tests.
3. **Scene cache:** stable-ID object table (DCC-native stable keys:
   Blender `session_uid`, UE object paths), monotonic revision counter,
   `diff(rev) -> {created, modified, deleted, user_edits}`. Full-dump spill to
   disk file + path summary, never inline (P1).
4. **Response budgeter:** every read tool takes `limit`/`offset`/`filter` and
   `response_format: concise|detailed`; hard cap ~20K tokens per response with
   a truncation notice that names the narrowing parameter (P7).
5. **Meta-tools (progressive disclosure, client-agnostic):**
   `tee_search_tools(query)`, `tee_describe_tool(name)`, `tee_call(name, args)`.
   Always-loaded surface ≤ 15 tools; long tail behind `tee_call`.
6. **Checkpoint manager:** generic checkpoint registry (label, adapter,
   payload); `tee_checkpoint`, `tee_rollback(id_or_label)` tools.
7. **Async jobs:** `JobManager` with submit/status/cancel; `tee_job_status`.
8. **Project memory:** `.tee/memory.json` per project (scene fingerprint,
   naming conventions, engine/DCC versions, done/todo log); loaded into a
   ≤ 500-token preamble via `tee_recall` (fixes "re-describe the scene every
   session").
9. **Tools/list lint (test):** assert every tool schema is a plain object
   schema, no `outputSchema`, descriptions ≤ 2 KB, total always-loaded
   definition budget ≤ ~8K tokens. This test is release-gating (A6).

**Acceptance:** `make check` green; an MCP Inspector (or scripted stdio
client) session shows handshake, `tee_status`, meta-tools, checkpoints and
jobs working against the fake adapter; tool-lint test enforced.

---

## 5. Phase 2 — Blender adapter

**Goal:** drive a live Blender session and a headless batch backend through
the kernel. Ground every API in `docs/research/02`, `09`, `10` — the 5.x fault
lines are catalogued there (geometry-nodes RNA move in 5.2, `scene['cycles']`
removal in 5.0, EEVEE id flip, GPencil→Annotation renames, Action API, etc.).

Steps:

1. **Wire client:** implement the official add-on protocol (null-delimited
   JSON over `localhost:9876`, `strict_json` handling, multi-client aware,
   reconnect with state resync). Probe-and-degrade: official add-on present →
   use it; else instruct user to install TEE's fallback add-on.
2. **Fallback add-on (extension):** manifest `schema_version 1.0.0`,
   `blender_version_min 5.1.0`, `[permissions] network`; socket thread only
   parses and enqueues; **one persistent `bpy.app.timers` pump drains the
   queue on the main thread** (never touch `bpy` from a worker thread; never
   one timer per command).
3. **Change detection:** two-channel — `bpy.msgbus.subscribe_rna` for
   attributed RNA edits + `@persistent depsgraph_update_post` marking
   `session_uid`s dirty (flags only, no diffing inside the handler); timer
   does poll-and-hash against the cache. `undo_post`/`redo_post`/`load_post`
   = cache-epoch invalidation + msgbus re-registration.
4. **Checkpoints:** GUI mode — every mutation batch ends with
   `bpy.ops.ed.undo_push(message='TEE: <batch-id>')` (hard invariant: without
   it, datablock add/remove crashes the user's next Ctrl+Z — #77557);
   rollback via `undo_history`. Batch mode — Zstd `save_as_mainfile(copy=True,
   compress=True)` snapshots + `open_mainfile` restore.
5. **Version shim + API firewall:** shim table keyed on `bpy.app.version` for
   the 10 catalogued fault lines; pre-exec validation (AST + `hasattr`
   against the live runtime) returning one-line fix hints from the
   version-diff table instead of tracebacks.
6. **Macro tools (`bl_` prefix):** scene summary, object detail,
   create/transform/parent, PBR material assign, geometry-nodes setup
   (server-side socket-identifier resolution — the model addresses inputs by
   name), OSL shader compile-with-errors, physics setup + **async** bakes,
   render-to-path; plus gated `bl_execute_python` (auto-checkpoint first).
   Prefer `bpy.data`/`bmesh` paths over `bpy.ops`; where `bpy.ops` is
   unavoidable, pre-validate context with `temp_override` server-side.
7. **Batch backend:** version-matched `bpy` wheel envs via `uv` (cp311/4.5 vs
   cp313/5.x — one interpreter cannot span 5.0→5.1) or `blender --background
   --python`, with `--python-exit-code`, factory-startup, evaluated-depsgraph
   fetches.
8. **Vision:** viewport JPEG capture, default ≤ 16 KB / ~1024×576, ROI crop
   param; geometric assertion tools (bbox overlap/clipping, watertight, poly
   count, camera-frustum containment) so the model checks text before pixels.

**Acceptance:** with Blender 5.x running, a scripted session: build a small
scene via macro tools → diff responses only; kill and restart Blender
mid-session → reconnect and resync; rollback restores prior state; API
firewall converts a known-stale call (e.g. `use_auto_smooth`) into a one-line
hint; bake runs as an async job. All response sizes logged; scene summary
< 500 tokens on a 100-object scene.

---

## 6. Phase 3 — Unreal adapter

**Goal:** UE ≥ 5.8 proxy over Epic's official MCP + TEE toolsets; fallback for
5.3–5.7. Ground every step in `docs/research/01` and `07`.

Steps:

1. **Connector:** Streamable-HTTP client for `http://127.0.0.1:8000/mcp`
   (protocol 2025-06-18, `Mcp-Session-Id`, Accept `application/json` +
   `text/event-stream`). Setup doc/doctor: enable `ModelContextProtocol` +
   `AllToolsets` plugins, auto-start via
   `[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]
   bAutoStartServer=True`. Discover toolset names at runtime by suffix match —
   never hardcode full module paths (they drift across 5.8 point builds).
2. **Serialization discipline:** strict serial dispatch (Epic's server runs
   tools serially on the game thread; parallel calls deadlock), per-call
   timeouts, busy-state probe (compiling / PIE / level load) before dispatch,
   modal-dialog hang detection surfaced as a structured error.
3. **Token proxy wins (in measured order):** cache + summarize
   `describe_toolset` payloads (~74–127K chars each raw) into compressed
   per-tool signatures with lazy full-schema expansion; dedupe `refPath`
   boilerplate; paginate unpaginated list results client-side; strip
   full-schema error responses down to the offending field.
4. **Batching:** route TEE macros through Epic's
   `ProgrammaticToolset.execute_tool_script` (sandboxed Python, one
   round-trip); cache `get_execution_environment` once per session.
5. **TEE toolsets (Python, in a content plugin):** only the verified 5.8
   gaps — PIE start/stop, unsandboxed editor-Python escape hatch (gated,
   checkpointed via `unreal.ScopedEditorTransaction`), plus workflow macros
   (e.g. atomic define-Blueprint-function-from-spec with node-id-keyed
   diagnostics). Do not re-port what Epic already ships.
6. **Fallback tier (5.3–5.7):** Remote Control HTTP `/remote/batch` +
   presets + WebSocket change subscription for the diff cache; Python remote
   execution channel for scripting; headless commandlet path for CI-style
   jobs. Same `ue_` tool schemas; capability-probe decides the backend.
7. **Vision + assertions:** viewport screenshot via Epic tools, budgeted like
   Blender's; text-first checks (actor bounds, counts, camera frustum).

**Acceptance:** scripted session against a live 5.8 editor: spawn + configure
actors via one macro call; Blueprint function authored and compiled with
diagnostics via graph DSL; `describe_toolset` never forwarded raw (test
asserts the raw payload never reaches the model, the largest toolset's
summary stays under 2,500 tokens, and every summary is under 20% of raw —
amended from a flat <10% ratio; see DECISIONS A25 for the measurements and
why the ratio was the wrong gate); fallback tier smoke-tested on an older
engine if present, else marked `n/a` in PROGRESS.

---

## 7. Phase 4 — Cross-cutting friction killers

**Goal:** the mitigation layer for every catalogued friction cluster
(`docs/research/05`).

1. **Docs search:** bundle/index version-matched API references (Blender RST,
   UE Python stubs + toolset docs); `tee_search_docs(query, version)` so the
   model looks up signatures instead of guessing.
2. **Doctor:** `tee doctor` CLI — checks installs, plugins/extensions
   enabled, ports listening, socket round-trip, wheel ABI match; one-line
   fixes for each failure (setup friction dominates every issue tracker).
3. **Transport hardening:** length-framed/null-framed parsing everywhere,
   partial-JSON impossible by construction, auto-reconnect + resync,
   single-instance lock.
4. **Tool profiles:** per-project enable/disable lists in `.tee/config.toml`
   (users explicitly ask for hard tool disables).
5. **Client-compat test matrix:** automated stdio harness asserting observed
   tool count and model-visible content for each release (the failure modes
   are silent — A6 hazards).

**Acceptance:** doctor passes on this machine; kill-tests (DCC down, socket
severed mid-response, oversized result) all return structured errors, never
hangs; compat lint green.

---

## 8. Phase 5 — Benchmarks: prove the token savings

**Goal:** quantified tokens-per-task, before/after.

1. Scenario suite in `benchmarks/`: (a) Blender donut-class modelling task,
   (b) 100-object scene interrogation, (c) UE level population + Blueprint
   function, (d) material/shader authoring, (e) sim bake + verify.
2. Harness runs each scenario through (i) naive baseline (raw
   `execute_python` + full-state responses, PNG screenshots) and (ii) TEE
   (macros, diffs, assertions, budgeted JPEG); count tokens with the
   Claude `count_tokens` API (free) + logged response sizes.
3. Report `benchmarks/RESULTS.md`: tokens per task, round-trips per task,
   failure/retry counts. Regression-gate: median read-tool response ≤ 2K
   tokens; suite must not regress > 10% between releases.

**Acceptance:** results published; TEE beats baseline on every scenario;
numbers cited in README.

---

## 9. Phase 6 — Packaging and handoff

1. Install paths: `uvx`/pip package for the server; Blender extension zip;
   UE content-plugin zip; client configs generated by `tee doctor --emit
   <client>` for Claude Code / Desktop / Cursor (`.mcpb` bundle where
   supported).
2. Docs: quickstart per client, per-DCC setup, troubleshooting from doctor
   checks, security notes (localhost-only, code-exec gating, no auth on DCC
   sockets — never port-forward them).
3. Claude Code plugin/skill: ship TEE usage know-how as a skill (when to use
   which tool, macro-first policy) rather than system-prompt stuffing.
4. Final `docs/PROGRESS.md` sweep; tag `v0.1.0`.

**Acceptance:** clean-machine install rehearsal (or documented dry-run),
README quickstart verified end-to-end, tag pushed.

---

## 10. Phase 7 — TEE Extract: the media extraction module

**Goal:** source materials (architectural drawings, CAD/BIM files, photos,
satellite imagery, video, audio) are converted into compact, frame-tagged,
content-addressed **facts** exactly once, so raw media stops being re-billed
in the model's context. Driving use case: drawings + satellite + site
photos/video → a dimensionally-conformant 3D house in Blender.

**Grounding:** `docs/research/11`–`18` (deep-research pass, 2026-08-22).
Decisions A8–A10 in `docs/research/00-index.md` are settled — amend via
`docs/DECISIONS.md` only. The honest cost claim (research 16): *zero token
cost* applies to local deterministic preprocessing only; VLM passes cost
either off-session dollars (API-key driver) or a one-time in-session spend
(in-band driver), amortized by the fact store — media enters a model context
exactly once, later sessions query facts at ~2 orders of magnitude fewer
tokens.

### 7.1 Extract kernel and fact store

1. `server/src/tee/extract/` package + `.tee/extract/` store: facts keyed by
   `(source_media_hash, extractor_id, extractor_version)` with a 2-char
   fanout layout (DVC pattern); a derived-data cache in the Unreal-DDC sense
   — same drawing arriving twice extracts once.
2. Fact schema: every geometric fact carries `frame_id`, `tier`,
   `confidence`, and provenance (source hash, extractor, model if VLM).
   Plan facts use the **FML v3-derived schema** (walls as centerline `a`/`b`
   + thickness, openings parameterized by `t` along the wall, rooms as
   polygons) **extended before freeze** with per-level heights
   (`elevation_z`, `floor_to_floor`, `ceiling_height`, aligned to
   `Pset_BuildingStoreyCommon`), opening sill/head heights, and a parametric
   roof object (IfcRoofTypeEnum subset, `pitch`, ridge/eave lines,
   overhang). Nullable-but-present fields keep cache keys stable (research
   17). **Schema freeze gate:** only after the frame registry, transform
   table, and Z-extension land.
3. `ex_*` virtual tools in the registry: `ex_ingest` (async via JobManager),
   `ex_sources` (paged listing), `ex_search` (text search over facts),
   `ex_facts(source)`, `ex_view(source, region|timestamp, token_budget)`,
   `ex_store_facts` (schema-validated writeback, see 7.5).
4. Dependencies as a `tee[extract]` extra. **License floor (A8):** banned
   imports enforced by a CI lint — `fitz`/PyMuPDF (AGPL), `marker`,
   `ultralytics`/FastSAM (AGPL); no CubiCasa5K/DeepFloorplan weights (CC
   BY-NC / GPL); `ffmpeg` and `exiftool` via subprocess only, never linked.

**Acceptance:** ingest of a mixed folder produces deduped, content-addressed
sources; facts round-trip through `ex_search`/`ex_facts`; the license lint is
release-gating; re-ingest of identical media is a no-op.

### 7.2 Documents & CAD lane (deterministic first)

1. **Sheet classifier as step 1** (research 17): tier 1 metadata — NCS sheet
   numbers (A-1xx plan / A-2xx elevation / A-3xx section / A-5xx detail) +
   title-block OCR + cover-sheet index; tier 2 fallback — one cheap VLM call
   on a thumbnail. Route to plan/elevation/section extractors or skip.
2. **DXF** (`ezdxf`, MIT): LWPOLYLINE walls (`get_points`, bulge handling,
   OCS→WCS), `DIMENSION.get_measurement()` as ground-truth dimensional
   facts (prefer measured over text overrides), `$INSUNITS` with the
   unitless-fallback question; DWG only via the optional `odafc` adapter.
3. **Vector PDF** (`pdfplumber`, MIT): vector-vs-scanned per-page classifier
   (chars/images coverage test) emitted as a fact; lines/rects/words with
   coordinates; dimension-string regex + nearest-parallel-line association →
   (text value, segment length) pairs; **scale-inference ladder** —
   least-squares fit over dimension pairs > title-block scale × paper size >
   `$INSUNITS` > one calibration question — scale stored as a fact with
   method + confidence.
4. **IFC** (`ifcopenshell` as pip dependency, LGPL): IfcWall/IfcSpace/
   IfcDoor/IfcWindow with world placements — the highest fact tier.
5. **Raster fallback:** `pypdfium2` render at ~300 dpi → `pytesseract`
   (RapidOCR optional extra for rotated text; word boxes + confidence,
   whitelisted dimension charset) → classical OpenCV wall-mask heuristics
   (reimplemented, never GPL code). No neural floor-plan models in core; a
   plugin seam for users who accept other licenses.

**Acceptance:** fixture DXF and vector-PDF plans extract walls, openings,
rooms and dimensions into the plan schema with correct scale; source-format
tier recorded (IFC > DXF > vector PDF > raster); unitless DXF triggers the
calibration path.

### 7.3 Image lane (photos + satellite)

1. Local EXIF/GPS/orientation via Pillow (`getexif().get_ifd(GPSInfo)`,
   `exif_transpose`) — mandatory, Claude never receives EXIF; `exifread`
   only if HEIC/RAW is in scope.
2. `ImageHash` phash dedupe: auto-collapse at Hamming ≤ 5, flag 6–10 as
   similar (keep the sharpest by Laplacian variance).
3. **Token-budget-first media serving** (research 12/14): images bill at
   `ceil(w/28) × ceil(h/28)` tokens by *rendered dimensions* (bytes are
   transport-only) — every serving parameter is a token budget, pixel sizes
   derived from it; pre-resize locally per the official `resized_size()`
   algorithm so the API never resizes silently.
4. Labeled contact sheets (3×3 / 4×4, cell IDs burned in + per-cell EXIF
   legend) as the default overview — ≤ 4,784 tokens regardless of photo
   count; individual budgeted crops are the drill-down.
5. Satellite: ground resolution `= 40,075,016.686 × cos(lat) / 2^(z+8)`
   m/px (target z19–z21); EXIF GPS (~5 m error) locates the parcel, never
   scales the model. Footprint references from Google Open Buildings (CC BY
   4.0 preferred) or OSM/Overture/Microsoft (ODbL) — fetched at runtime,
   cached with a license+provenance tag, never redistributed. OpenCV
   contour tracing as the no-dataset fallback; MobileSAM as an optional
   Apache-2.0 extra. Depth estimation: out of scope for v1.

**Acceptance:** a 20-photo set collapses to deduped sources with GPS facts;
a contact sheet + two crops cost < 7K tokens total (measured); satellite
tile + footprint yields an outline polygon with meters-per-pixel recorded.

### 7.4 Video & audio lane

1. Keyframes: PySceneDetect `AdaptiveDetector` + an every-N-seconds fallback
   sampler for continuous walkthrough/drone footage (the driving case);
   sharpest frame per scene via `cv2.Laplacian(...).var()`; phash dedupe at
   Hamming ≤ 8.
2. `ffmpeg` via `imageio-ffmpeg` (bundled static binary, subprocess only —
   GPL binary is fine over subprocess, document it).
3. Extraction index per video: `{frame_id, pts_time, scene_id, sharpness,
   phash, thumb_path, (lat, lon, alt), nearest transcript segment}` — the
   model's default view is a few hundred tokens of index rows; on-demand
   frame fetch by `ffmpeg -ss <pts> -i src -frames:v 1` (input seeking).
4. DJI telemetry: in-house ~50-line SRT regex parser (sidecar `.SRT` +
   embedded `-map 0:s:0` demux), flight path downsampled to turning points.
5. SfM: **sparse-only optional async job** on `pycolmap` (sequential
   matching, ≤ 200 keyframes, poses + sparse points); dense reconstruction
   out of scope; CPU runtimes documented as tens of minutes.
6. **Audio is a first-class modality, not a video afterthought.** Claude has
   no audio input — local transcription is the *only* channel for audio
   content, not an optimization. Standalone audio ingest (`.wav`, `.mp3`,
   `.m4a`, `.ogg` — voice memos, client briefings, recorded site notes)
   shares the video pipeline's transcription stage: `ffmpeg` demux/resample
   to 16 kHz mono → `faster-whisper` (MIT) `base`/`small` int8 with VAD,
   emitting segment-level timestamps and detected language as facts.
7. Transcript facts are searchable via `ex_search` and time-aligned with
   keyframes when the source is a video ("this is the north wall" links to
   the frame showing it). A cheap in-band text pass turns briefing
   transcripts into structured **requirement facts** ("4 bedrooms",
   "master faces east", "budget ceiling …") in the same store, tiered as
   stated-requirement evidence.
8. Speaker diarization (who said what — client vs. architect) is an
   **optional gated extra**: `pyannote.audio` code is MIT but its pretrained
   models are gated on Hugging Face behind free-but-mandatory terms
   acceptance and a user-supplied `HF_TOKEN`; a missing/expired token must
   degrade silently to non-diarized transcription (never fail the ingest),
   and the gating caveat is documented. Not part of core acceptance.

**Acceptance:** fixture walkthrough video → ≤ 15 keyframes + contact sheet +
timestamp index; a frame re-fetch by timestamp works; DJI SRT fixture yields
a flight-path fact; a standalone audio memo fixture transcribes to
time-stamped segment facts findable via `ex_search`, and the requirements
pass extracts at least one structured requirement fact from it.

### 7.5 VLM extraction passes (the only tokens this module spends)

1. **Channel decision (A9, research 16):** MCP sampling is dead (deprecated
   in MCP 2026-07-28, unimplemented in Claude Code/Desktop) — do not build
   on it. Default driver: **in-band** — TEE serves prepared tiles/sheets and
   extraction prompts; the host model reads media (its own Read tool where
   available), extracts against the frozen per-media-type schema, and writes
   back via `ex_store_facts` (schema-validated tool *input*, consistent with
   A6). Never return image bytes as MCP tool results beyond the budgeted
   `ex_view` crops.
2. Optional **API-key driver**: when `ANTHROPIC_API_KEY` is present in the
   server env, an async `ex_extract` job uses `messages.parse` +
   `output_config` json_schema, `count_tokens` preflight, the Files API, the
   Batch API (−50%) and `cache_control`. Absent a key, silently degrade to
   in-band; reflect the active driver in `tee_status`. One `Extractor`
   interface, two drivers, same fact store.
3. Tiling: pre-resize per the official patch algorithm, ≤ 4,784 tokens/tile,
   ≤ 2,000 px per side, `oversized_image: 'error'` on coordinate-bearing
   images; pair every tile with locally-extracted text (vector text or OCR)
   in the same prompt.
4. **Play to measured VLM strengths** (research 14/17): transcription of
   dimension strings/level markers/pitch triangles (~0.95 accuracy) — yes;
   counting symbols or measuring pixels (0.40–0.55) — no, verify those with
   deterministic CV or flag for human review. Returned pixel coordinates
   are approximate: verify against OCR/vector text; crop-and-re-ask for
   fine targets.
5. Elevation/section pass extracts the Z facts (levels, plate/ridge heights,
   pitch) that plans cannot provide; fusion joins on level index, facade
   orientation, grid lines and callouts (e.g. `3/A-301`).

**Acceptance:** a raster plan fixture extracts to schema-valid facts via the
in-band flow (integration-tested through the real MCP client); dimension
strings cross-check against OCR; the API-key driver is exercised when a key
is configured, skipped cleanly otherwise.

### 7.6 Frames and registration (A10, research 18)

1. Frame registry: `frame_id` on every geometric fact — drawing paper/model
   space, raster pixel, SfM reconstruction, geographic CRS, `site:{id}:enu`,
   `blender:{scene}:world`; axis conventions recorded per frame.
2. Transforms are first-class facts: `{from_frame, to_frame, type, params
   (flat row-major, STAC convention), method, residual, accuracy_m, tier}`;
   REP-105-style single-parent tree anchored at the site ENU hub
   (`pymap3d`); derived facts cite their transform chain, so re-registration
   invalidates only derived layers.
3. Drawing→geo: footprint from the plan vs reference footprint —
   `minimum_rotated_rectangle` init, constrained similarity fit (scale
   pinned by declared units; free-scale deviation > 2% ⇒ units-conflict
   fact, never a silent recalibration); store IoU + Hausdorff fit quality.
4. Tier ladder (drawing dimension text > drawing geometry > SfM > GPS prior
   > satellite/footprint); a transform never raises a fact above its
   weakest source; EPSG:3857 is fetch-only — the conformance layer rejects
   it; EXIF/DJI vertical channel is a lower tier than horizontal.

**Acceptance:** fixture site registers drawing + satellite + photo frames
into one tree; composed chains re-express plan facts in site ENU within the
declared accuracy; the >2% scale-deviation case produces a units-conflict
fact.

### 7.7 Conformance and Blender handoff

1. **Handoff tier 1:** plan facts → IFC authored offline via `ifcopenshell`
   (IfcWall axis + body, IfcRelVoidsElement/IfcRelFillsElement openings,
   IfcBuildingStorey elevations, IfcRoof) → imported through Bonsai
   (Blender 4.0–5.x) for semantic BIM entities and quantities.
2. **Handoff tier 2 (no add-ons):** `bl_build_from_plan` — wall centerlines
   → mesh extrusion/solidify through the existing batch machinery; the
   FloorplanToBlender3d pattern driven from semantic JSON, checkpointed and
   diff-tracked like any batch. Blender scene ≡ site ENU (datum at origin,
   meters, Z-up, BlenderGIS-style scene properties).
3. **Conformance:** `bl_check_against_plan` — compare built geometry to plan
   facts in the common frame; effective tolerance = RSS of both facts' tier
   tolerances + `accuracy_m` of every transform on both chains; tolerance
   classes default to USIBD LOA bands (±25/±12/±6 mm). Above tolerance:
   tier precedence decides (written dimension governs — the AEC "do not
   scale" rule); systematic residuals demote and refit the *transform*, not
   the facts. Every over-tolerance case is a first-class **conflict fact**
   `{fact_a, fact_b, delta_m, tolerance_m, winner, disposition}` — the
   conflict facts ARE the conformance report. Z-conformance = cross-sheet
   consistency of stated dimensions.

**Acceptance:** fixture plan builds a watertight multi-room shell in live
Blender via both tiers; a deliberately mis-built wall yields exactly one
conflict fact naming the delta; the conformance report costs < 500 tokens.

### 7.8 Fixtures, tests and the extraction benchmark

1. Synthetic fixtures generated in-repo (no licensing risk): an
   `ezdxf`-authored DXF plan with real DIMENSION entities; a vector-PDF plan;
   Blender-rendered "site photos" and a walkthrough "video" of a known
   house model; a hand-written DJI-format SRT; a synthesized speech clip
   for the audio lane (`espeak-ng` subprocess where available, else a tiny
   committed WAV) reading a scripted client brief.
2. Unit tests per lane (no DCC needed); live `-m dcc` tests for handoff and
   conformance; the in-band extraction flow tested through the real MCP
   client.
3. `benchmarks/` gains an extraction scenario: naive (media re-billed in
   context each turn) vs TEE Extract (ingest once, facts thereafter),
   measured over a simulated multi-session build — cite the research-16
   amortization math and verify it empirically.

**Acceptance:** full suite green; extraction benchmark published in
`benchmarks/RESULTS.md`; `docs/PROGRESS.md` updated with measured numbers.

---

## 11. Phase 8 — Context economics: script lane, columnar responses, recap

**Goal:** cut the *per-turn context* cost of an already-TEE-optimized session.
Phase 7 stopped media re-billing; Phase 8 attacks the remaining spend: chatty
tool loops whose intermediate results live forever in the transcript, and
list-heavy responses that repeat their keys. Target (simulated 2026-08-22,
Fable-5 rates with caching): **-61% session cost** on a 120-turn build
(script lane + eviction), on top of Phase 7's savings.

**Grounding:** `docs/research/19` (API-mechanism research + simulation pass,
2026-08-22). Decisions A11–A12 in `docs/research/00-index.md` are settled —
amend via `docs/DECISIONS.md` only. Key facts: programmatic tool calling is
the API-native pattern for keeping intermediate tool results out of model
context but is incompatible with MCP tools, so TEE implements the pattern
app-side; context editing (`clear_tool_uses`) makes old tool results
evictable, which TEE can afford uniquely because all state is re-derivable
from the scene cache and fact store; a naive BM25 swap for fact search was
simulated and REGRESSED (7/10 vs 9/10 at 611 facts) — the search stays as
is (A12).

### 8.1 `tee_script` — the app-side script lane (A11)

1. `kernel/script.py`: an AST-whitelisted mini-Python executor. Allowed:
   literals, assignments, arithmetic/comparison/boolean ops, `if`/`for`
   (bounded), list/dict literals and indexing, calls to an injected helper
   namespace only — `call(name, args)` (virtual tools), `batch(adapter,
   ops)`, `facts(source, kind=)`, `summary(adapter)`, `diff(adapter, epoch,
   revision)`, plus `len/min/max/sum/round/abs/sorted/range/enumerate`.
   Forbidden by construction: `import`, attribute access on results beyond
   plain subscripts, dunder names, `while`, comprehension-free lambdas,
   `exec`/`eval`. Hard bounds: ≤ 200 tool calls, ≤ 10k interpreted nodes,
   ≤ 120 s wall clock — exceeding any raises one short `TeeError`.
2. Atomicity: the script runs under one auto-checkpoint per touched adapter;
   any uncaught error rolls every touched adapter back (same contract as a
   failed batch). The response carries only the script's `result` variable
   plus `{checkpoint, calls_made, epoch/revision per touched adapter}` —
   intermediate tool results NEVER enter the response.
3. `tee_script` joins the always-loaded surface (16th tool; update both
   canaries). It is NOT gated by `allow_code_exec` — it can only invoke the
   same typed tools the model could call anyway; the sandbox adds no new
   capability, it removes round-trips.

**Acceptance:** the Phase-7 conformance fix loop (check → fix N walls →
recheck) runs as one `tee_script` call with only the final report in the
response. The script's context cost is FLAT in loop length while
round-based cost grows linearly — measured: 17.7% saved at 1 conflict,
63.2% at 3, 76.3% at 5, approaching 100% asymptotically (the sim's 86%
figure assumed a sketch-length script; the real ~110-token script code is
a fixed cost that amortizes). Accept at ≥ 60% on the 3-conflict fixture
loop. Sandbox tests prove `import`, dunder access, `while`, unbounded
loops and over-cap call counts each fail with one short error and leave
the scene rolled back.

### 8.2 Adaptive columnar encoding (A12)

1. `kernel/budget.py` gains `columnarize(payload, min_rows=20)`: any
   list-of-dicts field with ≥ `min_rows` rows sharing ≥ 60% of their keys is
   rewritten `[{...}, ...]` → `{"cols": [...], "rows": [[...], ...]}`; the
   field name is recorded in a top-level `"columnar": [field, ...]` marker
   so the model can decode. Small or heterogeneous lists are untouched
   (simulated: 42% smaller at 100 rows, ~1% at 11 heterogeneous facts —
   the threshold is the point).
2. Wired into the server `_tool` pipeline before `enforce_budget`, so
   trimming operates on the already-compact form.

**Acceptance:** a 100-entity `tee_scene_summary` response measures ≥ 35%
smaller than the row-of-objects form; sub-threshold payloads are
byte-identical to today; the canary suite still passes on all 16 tools.

### 8.3 Recap — eviction-safe resume (A12)

1. `tee_status` gains `recap: boolean`. With it, the response adds a
   `recap` object rebuilt entirely from server-side state: per-adapter scene
   stamp + entity counts by kind, last 3 checkpoints, extract sources with
   fact-kind counts, unresolved conflict count, and project-memory
   highlights. Budget: ≤ 500 estimated tokens, enforced.
2. Contract note in the tool description: every TEE response is re-derivable
   (scene cache / fact store / checkpoints), so hosts that evict old tool
   results lose nothing — `tee_status(recap=true)` is the one-call catch-up.

**Acceptance:** recap present, ≤ 500 tokens on a project with 100+ entities
and a full extract store, and sufficient to resume: a fresh in-memory client
session given only the recap can find and call the right next tool without
re-listing the scene.

### 8.4 Caption-once media pass (A12)

1. `ex_prepare` packets list `uncaptioned` keyframe/photo-group ids and
   instruct the host model to store `{kind: "caption", ref, text ≤ 20
   words}` facts alongside its normal pass; media with existing caption
   facts are excluded from `prepared_images`, so a captioned keyframe is
   never re-attached by default (re-view stays available via `tee_media`).
2. Captions are plain facts: searchable via `ex_search`, no schema change.

**Acceptance:** a stored caption removes its keyframe from the next
`ex_prepare` packet and is findable via `ex_search`; arithmetic in the tool
description states the break-even honestly (one avoided re-view of a
1568-capped frame ≈ 2,200 tokens vs ~30 for the caption).

### 8.5 Benchmark

Add a fix-loop measurement to the extraction benchmark scenario: the same
3-wall repair executed as individual tool rounds vs one `tee_script` call,
published in `benchmarks/RESULTS.md` next to the Phase 7 numbers.

**Acceptance:** full suite green (unit + dcc); benchmark re-run against live
Blender and published; `docs/PROGRESS.md` updated with measured numbers.

---

## 12. Phase 9 — TEE Assets: management, acquisition, and creation

**Goal:** finding, selecting, and creating scene assets stops being the
drag it is everywhere else. Free assets become one cheap typed query away
(license-safe by construction); asset creation is a laddered set of lanes
from zero-GPU procedural materials to photo-derived PBR and generated 3D;
selection, scaling, placement, and lighting are scene-based and
context-aware, driven by the facts TEE already extracted (plan dimensions,
site photos, GPS, brief). The measured prior-art baseline to beat: the
popular community integration spends 2-5k tokens to find and place ONE
asset, re-fetches a 2.3 MB catalog per search, and lets NC-licensed assets
into commercial projects unchecked.

**Grounding:** `docs/research/20`–`25` (six-agent deep-research pass,
2026-08-22). Decisions A13–A15 in `docs/research/00-index.md` are settled —
amend via `docs/DECISIONS.md` only. Honest quality claim, stated up front
and in tool descriptions: generation delivers *set dressing on demand* —
good mid-ground props and photo-true materials; hero assets are curated,
not generated (research 23). Photographic fidelity comes from the
photo-derived material lane and real scanned CC0 assets, not from
text-to-3D.

### 9.1 Asset store, source registry, license hygiene (A13)

1. `server/src/tee/assets/` package. `AssetStore` reuses the ExtractStore
   patterns (content-addressed cache under `.tee/assets/`, 2-char fanout):
   cached FILES keyed by hash (never URLs — Sketchfab's expire in 300 s),
   a local metadata index (name, tags, license SPDX, tri count, real
   dimensions, source, thumbnail phash), and per-asset **attribution
   manifests** (TASL + SPDX + license text snapshot + retrieved_at + file
   hash + modifications + pre-rendered credit line) with a `CREDITS.md`
   renderer.
2. Source registry (`sources` module): per-backend adapters for Poly Haven
   (no-auth; unique User-Agent; "Powered by Poly Haven" credit in docs),
   ambientCG (cache-first), Poly Pizza (key; license-filtered), Smithsonian
   (key; CC0-flag gated), Sketchfab (opt-in; OAuth; guarded). Each backend
   declares BOTH its asset-license regime and its site-ToS constraints.
   Catalogs are fetched server-side with ETag/if-modified caching — the
   2.3 MB-per-search prior-art failure is structurally impossible.
3. License gate: SPDX allowlist (`CC0-1.0`, `CC-BY-4.0`, `CC-BY-3.0`;
   `CC-BY-SA-*` behind a config flag) failing CLOSED on NC/ND/unknown/
   proprietary/GPL. A test proves an NC asset cannot enter the cache.
4. Local library ingest: `as_ingest` indexes the user's own asset folders
   (glTF/GLB header probe — tri counts and exact extents from the JSON
   chunk with node-transform composition, stdlib only, no DCC and no
   extra dependency; map-set regex for texture packs; thumbnails rendered
   once, phashed).

### 9.2 Search and selection (A15)

1. `as_search`: one faceted query (keywords + class + license + max_tris +
   real-dimension range) over all enabled backends + the local index;
   compact rows (id, name, license, tris, dims_m, source) ≤ 5 per class by
   default. The Holodeck contract: the model states WHAT it needs
   (description, target dims, constraints); ranking happens server-side —
   tags first, ΔE00 palette-vs-style-brief second, thumbnail embeddings
   third (SigLIP-2 Apache or CLIP MIT, computed at index time, cached by
   thumbnail hash; optional `[assets-embed]` extra, CPU-only).
2. `as_sheet`: one labeled contact sheet of the shortlist (tiles ≥ 256 px,
   reusing the extract contact-sheet machinery) as the tie-breaker view;
   `tee_media` serves individual budgeted previews. Never per-candidate
   inline images by default.

### 9.3 Import and library plumbing (research 21)

1. `as_import`: download (or reuse — BlenderKit's `asset_in_scene` lesson:
   check cache and scene before any network) → glTF-first probe →
   **four-band scale policy** against the semantic-class envelope tables
   (accept / silent power-of-ten fix recorded as a fact / snap-to-catalogue
   ±10% / reject with one line) → import through the NORMAL typed batch
   machinery (checkpointed, diff-reported) → idempotent PBR wiring →
   read-back verification (the rotation-mode no-op lesson). Fit-to-plan:
   a door asset auto-scales into a 0.9 m plan opening; uniform-only unless
   the asset declares `stretch_axes`.
2. Blender library authoring, fully headless: `asset_mark` + metadata +
   catalogs (cats.txt written directly — no API exists), previews
   (synchronous in `--background` since 3.6; custom 256 px render +
   `lib_id_load_custom_preview` as the universal path), self-contained
   `libraries.write` per asset, then `blender -c asset_listing generate`
   so TEE gets Blender's own queryable remote-library JSON index for free
   (and can serve it to human users' Asset Browsers).
3. UE 5.8 (physical machine): Interchange `import_asset` +
   `wait_until_all_tasks_done` (async trap), `AssetImportTask` fallback
   for commandlets; Asset Registry tag queries (Triangles/LODs) instead
   of loading assets; FBX stays on the legacy importer; Fab is
   human-download-then-import (a Launcher-export TCP listener in the
   Blender adapter is the one automatable seam).

### 9.4 Creation lanes (A14)

1. **Lane 0 — procedural (default, zero-GPU, zero tokens at rest):**
   `as_material` builds Principled node graphs parameterized from the
   physicallybased.info CC0 dataset (measured albedo/roughness/IOR — no
   hallucinated constants); Infinigen (BSD-3) generators as the reference
   library for the hard ones. Emitted as typed batch ops.
2. **Lane 1 — local diffusion (`[assets-gen]` extra, GPU-gated):**
   Z-Image family (Apache) general; SDXL + circular padding for
   born-tileable textures; Marigold-IID for PBR map estimation; diffusers
   in-process, ComfyUI only ever as a separate process. Scene-conditioned:
   headless depth/normal EXR render → ControlNet-depth img2img →
   UV Project modifier + Cycles bake back onto geometry.
3. **Lane 2 — photo-derived PBR (the Okongo lane):** rectify (homography,
   most-frontal ingested photo) → Marigold delight → seamless-or-
   UV-project → maps → Real-ESRGAN; metallic clamped to 0 on masonry/
   paint. Facades of a specific building use projection, not tiling.
4. **Lane 3 — generated 3D:** local TRELLIS.2-4B (MIT; nvdiffrast/
   nvdiffrec audited OUT of the runtime path before the lane is declared
   clean) and hosted Tripo/Meshy behind ONE async-job adapter with
   Meshy-style server-side wait-polling (backoff, hard cap, one result)
   and **cost confirmation before any paid call**. Every generated mesh
   passes the mandatory cleanup macro (normalize scale/orientation/pivot →
   Quadriflow/decimate to budget → Smart UV → Cycles re-bake → export)
   and carries an `ai-generated` provenance fact (generator, input hash,
   USCO copyright note).
5. Gated lanes (config opt-in, clearly labeled, never default): FLUX-dev
   (non-commercial runtime), SD3.5 (revenue-conditional), Hunyuan3D local
   (geo-restricted license — geo-labeled).

### 9.5 Context awareness (A15)

1. `style_brief` fact auto-derived at ingest: CIELAB k-means palette from
   site photos (color NAMES are the in-context form), style terms and
   materials from the caption pass, avoid-list from the audio brief.
2. Placement: the model emits a relational plan (anchor + wall-segment id
   + offset + relations, ~10 tokens/object); `as_place` solves and
   validates against the machine-readable rule table (clearances,
   circulation corridor, door swings, work triangle; `code` vs `guideline`
   severity — guideline rows relaxable with a note, code rows never;
   region-parameterized from the GPS datum).
3. Lighting: sun azimuth/elevation from the GPS datum + date/time (astral
   default, pvlib SPA precision; NEVER pysolar — GPL); drives Blender
   sun/Nishita sky and UE directional light through the adapters; HDRI
   picked from Poly Haven by elevation band + weather, its in-image sun
   azimuth detected once (brightest pixel) and cached as a fact.

### 9.6 The `context-aware-assets` skill

Packaged per the Agent Skills standard (spec-portable frontmatter;
SKILL.md < 500 lines; reference files one level deep with TOCs; scripts
executed, never read): the 7-step checklist (brief → search → fit → plan →
validate → apply → verify) with exact tool invocations for the fragile
steps and judgment room for selection/grouping; reference tables =
dimension envelopes, clearance rules, source-license matrix; 3+ evals
authored before the skill is polished (furnish the fixture bedroom; the
kitchen work-triangle trap; reject the 0.4 m "sofa").

### 9.7 Verification and benchmark

1. Render-free battery after every apply: scale sanity vs envelopes, BVH
   collision (≤ 5 mm contact tolerated), support raycast, clearance/
   corridor checks, code checks through the conformance machinery,
   texture-palette ΔE00 vs the brief — one compact violations+fixes
   report. At most ONE budgeted render per task (~768×512), gated on
   geometric pass + a genuinely visual question.
2. `benchmarks/` gains an asset scenario: find-select-place N assets via
   TEE vs the measured prior-art flow (catalog dumps + per-candidate
   previews + polling chatter), published in RESULTS.md.

**Acceptance:** live `as_search` against Poly Haven answers a furniture
query in ≤ 200 response tokens with the catalog ETag-cached server-side;
an NC-licensed asset is refused from the cache by test; the attribution
manifest renders a correct CREDITS.md for a CC-BY asset; a door asset
auto-scales into the fixture plan's 0.9 m opening and a 0.4 m "sofa" is
rejected with one line; sun az/el for the fixture GPS datum matches the
NOAA reference within 1°; the placement validator catches a blocked
door swing and a sub-760 mm corridor; full suite green; benchmark
published. DCC/network-marked tests skip cleanly offline.

---

## 13. Phase 10 — TEE Design: the expert game design module

**Goal:** an AI agent designs games from evidence — real player routines,
validated experience research, motivation profiles, current market data,
and formal design logic — and emits a machine-verifiable spec that TEE's
build phases (assets, adapters) consume directly. The field gap is
verified: no product or engine encodes a design-expertise layer as of
2026-08; every successful generation system pairs the LLM with a formal
validator. TEE's design module IS that pairing.

**Grounding:** `docs/research/26`–`31` (six-agent deep-research pass,
2026-08-22). Decisions A16–A18 settled — amend via `docs/DECISIONS.md`
only. Anti-goals, stated up front: no folk benchmarks (percentile grids
with sources or nothing); no prose-first GDDs (they read deceptively
well); no dark patterns (code-severity rules from live enforcement); no
homogenized designs (differentiation is forced, not hoped for).

### 10.1 Design knowledge base (A16)

1. `server/src/tee/design/` package. Reference tables as versioned data
   files (every figure: value + source + as_of + verification grade;
   estimates labeled): retention/session percentile grids by platform and
   genre; genre convention templates (session shape, loop cadence,
   camera/control norms); motivation model (12-dimension vector,
   published aggregate findings); market opportunity map with dates; UX
   parameter table (text/subtitle/contrast/flash/latency/FOV minima);
   economy archetypes; scope-cost weights per asset class; live-ops
   cadence norms; the dark-pattern rulebook (rule + jurisdiction +
   severity `code`/`guideline`).
2. Licensing enforced in review: aggregate findings and paraphrased
   constructs only; no proprietary instruments (PENS), no unvalidated
   ones (GEQ — PXI/miniPXI is the default), no bulk report extraction
   (EU database right), no content-farm numbers.

### 10.2 The design spec: `tee-design/1` (A17)

Versioned JSON schema with stable IDs; the SOURCE OF TRUTH for a game
design. Sections, each independently checkable and consumable:
`meta` (audience profile as motivation vector, platform, price point,
market position vs named comparables), `core_loop` (verbs, loop steps
with target durations, failure state, session-end hook), `economy`
(typed faucet/sink/converter graph with rates and caps), `progression`
(unlock and difficulty tables, teach-test-compose ordering), `level_macro`
(Cerny-style beat chart: spaces × mechanics/exotics/intensity),
`content_list` (assets by class + count + reuse — feeds the scope
estimator and Phase 9's asset search directly), `routine` (daily/weekly/
season loops with reset conventions and streak-grace rules),
`accessibility` (the enforce-table checklist state), `open_questions`.
`gd_render` emits the prose one-pager and pitch view FROM the spec,
never the reverse. Validation errors name the exact fix (P7).

### 10.3 Verification battery (A17)

Deterministic checkers (design/checks.py, callable individually and via
the script lane), cost-ordered:
1. **Design lint** — the novelty: core loop undefined; loop lacks a
   failure state; currency with no sink; no session-end hook; mechanic
   introduced but never composed; difficulty spike before its mechanic
   is taught; content list missing a class the level_macro references;
   audience/monetization contradictions (e.g. competitive core aimed at
   35+ without age-tolerant depth).
2. **Scope estimate** — content_list × asset-class weights → effort
   bands; flags scope/team mismatches.
3. **Economy simulation** — discrete-time source/sink solver run per
   player persona (motivation-vector-derived play patterns); flags
   unbounded inflation, dead currencies, sink/faucet imbalance beyond
   archetype bands.
4. **Progression validator** — monotonicity, smoothness,
   time-to-next-unlock bounds, teach-test-compose ordering; pity/gacha
   hazard-function checks where present (with the A18 ethics gates).
5. **Ethics/dark-pattern check** — the code-severity rulebook; `code`
   rows are hard failures the model cannot relax.
6. **Bounded self-play** — one budgeted transcript of the model playing
   the spec turn-by-turn ("is there a decision loop at all") — the only
   token-spending checker, run last.

### 10.4 The `game-design` skill (A16)

Agent Skills standard (<500 lines; references one level deep; scripts
executed, not read). The judgment layer: design-pass order (audience →
market position → core loop → economy → progression → level macro →
content → routine → verify), when to challenge the user's premise,
anti-pattern catalog, and DIFFERENTIATION FORCING — every design names
3 comparables from the market tables and states its delta; a novelty
check against genre convention templates counters LLM homogenization.
Enforce-vs-judge split from research 28 encoded as instructions: the
parameter tables are enforced by checkers; juice (inverted-U, capped),
DDA visibility, HUD diegesis, difficulty-curve shape are judged with
cited heuristics. Evals authored before polish (3+ scenarios: a
scoped co-op brief hits the opportunity map; an economy with a dead
currency is caught; a dark-pattern monetization ask is refused with the
rule citation).

### 10.5 Bridge to build

`content_list` entries carry asset classes compatible with Phase 9's
search/creation lanes; `level_macro` rows drive blockout batches through
the existing typed ops; the spec lives in the fact store (content-
addressed, diffable — design REVISIONS are diffs, not new documents).
UE/UEFN targets consume the same spec (the Phase 12 research pass covers
the UEFN/Verse surface; UE 5.8's first-party MCP plugin, extended to
UEFN 2026-08-20, is the anticipated route).

### 10.6 Acceptance

Full suite green. `tee-design/1` round-trips (validate → render → edit →
re-validate). The lint catches each seeded defect class in a fixture
spec (dead currency, missing session-end hook, taught-after-tested
mechanic) with one-line fixes. The economy solver flags a seeded
inflation spiral and passes a balanced fixture. The ethics check hard-
fails a seeded under-16 loot-box spec citing the rule and jurisdiction.
Percentile tables answer "what is good D7 for mobile puzzle" with the
grid value + source + year, never a folk target. A skill eval produces a
spec for a small-team 3D co-op brief that names 3 comparables, passes
all checkers, and its content_list resolves against Phase 9 asset
classes. `docs/PROGRESS.md` updated with evidence.

---

## 14. Phase 11 — TEE Physical: physics, material science, modeling

**Goal:** the modeled world obeys physics and dimensions, cheaply. Three
capabilities: a physics lane whose simulations are checkpoint-safe,
deterministic-where-promised, and report compact facts; a material fact
store whose values are measured or honestly labeled, spanning render,
physics, and engineering tiers; and a tier-2 modeling vocabulary that
builds real architectural elements (walls with openings, slabs, roofs,
stairs) as parameterized, verifiable constructions instead of prop boxes.

**Grounding:** `docs/research/32`–`37` (six-agent pass, 2026-08-22; two
agents verified by execution against local Blender 5.2 and 5.2 sources).
Decisions A19–A21 settled — amend via `docs/DECISIONS.md` only.
Anti-goals: no physics theater (facts say "rest-stable under settle",
never "structurally sound"); no unlabeled property values; no member
sizing or "passes" verdicts in plausibility checks (findings only —
the flagging-vs-approving line is the legal design input).

### 11.1 Modeling tier-2 ops (A21)

1. Typed ops `wall_with_openings`, `slab`, `roof`, `stairs`,
   `opening_cut`, `array_along`, `profile_extrude`, `param_set` — each
   compiling to the verified BMesh pattern (tessellate_polygon +
   solidify; watertight by test) or a TEE-owned geometry-node group
   addressed by socket identifier only. Boolean policy: MANIFOLD solver
   default with over-penetrating manifold cutters, EXACT fallback,
   'FAST' guarded out. Live modifier form is the default; `apply` is an
   explicit checkpointed op; exports use glTF `export_apply`.
2. Shim-table entries from the research: 5.2 NodesModifier RNA input
   API (`properties.inputs.<id>.value` — ID-property access raises),
   boolean solver identifier change, `gpu.init()` for background.
3. `sketch_solve`: server-side py-slvs constraint solving
   (distance/angle/parallel/equal) closes dimensioned 2D plans before
   extrusion — no DCC involved; feeds wall/slab ops. Plan-extracted
   walls (Phase 7) upgrade from prop boxes to wall_with_openings.
4. Parameter schemas mined from Infinigen (BSD-3); UE compile targets:
   Geometry Script (Python-scriptable) and parameterized pre-built PCG
   graphs (physical machine).

### 11.2 Material facts (A20)

1. `materials/` reference data: three tiers per material — render
   (Principled/UE params), physics (density, friction pair, restitution),
   engineering (strength/moduli/thermal where relevant) — every leaf
   value carrying source + license + as_of + honesty label (measured |
   standard_value | typical_range | derived | game_plausible) and
   per-engine caveats (Bullet multiplies friction — √μ note; UE g/cm³).
2. Bulk imports from CC0/CC-BY sources only (physicallybased.info,
   refractiveindex.info, RGL-EPFL, Wikidata; Eurocode numeric values as
   cited facts). Banned by test: NIST SRD bulk, MatWeb/MakeItFrom
   tables, ArcSim cloth data. UsdPhysics is the parameter vocabulary.
3. `mat_assign` wires all applicable tiers at once: render nodes,
   rigid-body/physical-material params, and an engineering fact for the
   plausibility checker; Blender mass via volume × density.

### 11.3 Physics lane (A19)

1. Blender: `sim_drop` / `sim_settle` (sequential frame stepping,
   early-out on transform-delta convergence, optional freeze),
   `sim_cloth_drape` (embedded 5.2 preset table), cost-gated `sim_fluid`
   (ALL cache, absolute directory, res ≤ 64 default), `sim_bake_all`
   (checkpoint prep — memory caches persist in .blend snapshots).
   Reports: resting poses, settled flag, AABB/max displacement,
   solver_result, cache status, wall time — never per-frame data.
   Tracker landmines encoded (bake before background renders; never
   pip-bpy; invoke-only calculate-to-frame avoided).
2. UE (physical machine): `physics.settle` — SIE + short-call polling +
   all-asleep stop + transform diff (replaces the API-less "Keep
   Simulation Changes"); physical-material ops echo computed mass;
   ragdoll and Dataflow fracture proxied through the official MCP
   toolsets; functional tests generated and run headless
   (`-game -NullRHI`) as the sanctioned sim-verification route.
3. Determinism contract in tool descriptions: reproducible on this
   machine and build with pinned stepping; not across builds; fluids
   approximate. Assertions tolerance-based above a measured variance
   floor (add the variance-floor measurement to benchmarks/).

### 11.4 Verification ladder (A19/A20)

1. Tier 0 (always-on, ms): existing battery + CoM-over-support-polygon
   with stability margin (cumulative for stacks) — floating /
   penetrating / unsupported_com facts.
2. Tier 1 (opt-in, s): settle test with CoACD (MIT) proxies cached per
   asset hash; BlenderProc-style quiescence; compact delta report;
   optional adopt-settled-poses repair.
3. Tier 2: swept-range mechanism checks over joint limits (door swings
   sampled statically); dynamic hinge sim on request only.
4. Sim-readiness gate for Phase 9 imports: simple collision present,
   complexity mode, physical material, mass sane — SimReady-style
   requirements emitting conflict facts with callable fixes.

### 11.5 Structural plausibility (A20)

1. `plaus_check`: rule engine over plan facts + modeled geometry with
   CODE/STD/HEUR/CONV severity (CODE never relaxable). Rule sets from
   research 35: span envelopes (worst-case table columns — zero false
   positives), header/lintel existence and bearing, masonry
   slenderness, footing rules, roof pitch minima per covering, stairs,
   ceiling heights, head-height geometry, wet-wall conventions.
2. The load-path graph check (IRC R301.1 anchor): support-graph
   reachability to foundations; missing headers; cantilever ratios;
   stacking offsets; point loads to posts to footings.
3. Output contract: findings with source + edition + jurisdiction +
   exact delta; never a member size; never a "passes" state — "no
   plausibility conflicts detected (N rules evaluated)". The disclaimer
   text ships in the tool description and docs. Region-parameterized;
   SANS 10400 researched before Okongo jurisdiction defaults.
4. Data-completeness tier via IDS + ifctester on the exported IFC.

### 11.6 Acceptance

Full suite green. The fixture plan builds via wall_with_openings with
watertight results (0 non-manifold edges, by test). sketch_solve closes
an over/under-constrained fixture with exact-fix errors. A seeded
floating chair and an unsupported-CoM stack are caught by Tier 0; a
settle test on the furnished fixture room returns a compact report and
adopted poses within thresholds; determinism: two settle runs on this
machine agree within the measured variance floor. mat_assign gives the
fixture wall EN-cited density and the renderer honest labels; a banned
bulk-source import fails by test. plaus_check flags a seeded
over-span joist citing the table, a tile roof below 30°, and a broken
load path; the clean fixture reports zero findings with the rule count.
Benchmarks gain the variance-floor measurement and a settle-cost row.
`docs/PROGRESS.md` updated with evidence.

---

## 15. Phase 12 — TEE UEFN: Fortnite, Verse, and the road to UE6/Blender 6

**Goal:** ride the platform curve instead of being broken by it. Four
capabilities: a Verse lane that makes codegen digest-grounded (the
hallucination classes documented in 39 become lint failures, not
runtime surprises); a UEFN adapter that wraps Epic's own MCP toolsets
in TEE's token contract; the Blender→UEFN export lane nobody has
built; and the version-trajectory firewall that encodes the announced
UE6 / Blender 5.3–6.0 fault lines as tests and shims now.

**Grounding:** `docs/research/38`–`42` (five-agent pass, 2026-08-22).
Decisions A22–A24 settled — amend via `docs/DECISIONS.md` only.
Anti-goals: no from-scratch UEFN bridge (the graveyard is documented);
no digest redistribution (Epic-copyrighted — parse the user's local
install); no AGPL code reuse (reference only); no closed-loop publish
promise (cook/memory/publish/moderation are human-gated); no claim of
full Verse type/effect checking offline (symbol/signature linting is
the honest boundary).

**Scope amendment (2026-08-22, owner decision):** the LIVE-editor lanes
(12.3's live proxy, the compile-in-editor path, Scene Graph ops against
Epic's toolsets, live playtest sessions) are REMOVED from scope — UEFN
is Windows-only and the project has no Windows machine. The offline
lanes (12.1, 12.2 offline validation, 12.4, 12.5, 12.6) are shipped and
remain supported; the adapter interface + fakes stay in the codebase as
the revival point if a Windows machine ever joins.

### 12.1 Verse digest facts lane (A22)

1. Digest parser for `*.digest.verse` files (plain Verse declarations:
   modules, classes, members, effect specifiers, `listenable` events)
   → version-keyed API facts in the docs-search lane. Digests load
   from the user's install (`%LOCALAPPDATA%\UnrealEditorFortnite\
   Saved\VerseProject\...` + per-project `Assets.digest.verse`);
   tests use a small SYNTHETIC digest fixture, never Epic's text.
2. Digest diffing between versions emits drift facts (added/removed/
   renamed members, changed effects) — the firewall rows for the
   23.20 / 30.00 / 42.00 class of breaks.
3. Bundle verselang/book (CC0) chapters as the offline language
   reference, with a per-target-version mask for unreleased features
   (live variables, `dictates`/`predicts`).

### 12.2 Verse codegen + validation ladder (A22)

1. Template corpus seeded from MIT/Apache sources only (uefncentral
   examples MIT, OsirionGG Apache-2.0), keyed to digest version:
   device subscription, `weak_map` + `<persistable>` persistence,
   Scene Graph component, UI canvas, sync/race patterns.
2. Offline validator: every identifier, member access, effect
   specifier and event subscription in emitted Verse is checked
   against the loaded digest — catches stale-API hallucinations
   (`<varies>`, `GetPassengers`, invented device methods) without
   claiming type checking.
3. Compiler-error → one-line-fix mapping (fail loud and cheap),
   including the stale-validation false-positive class; live compile
   lane through Epic's MCP Verse toolset when an editor is present.

### 12.3 UEFN adapter as capability-probed proxy (A22, A23)

1. Adapter interface + fakes now; the live proxy lands with/after the
   UE 5.8 proxy (same `127.0.0.1:8000/mcp` shape, shared plumbing).
   Capability probe detects editor presence, Beta-Access state
   (missing toggles → remediation message), and the toolset catalog
   keyed on (version, catalog hash, schema hash).
2. Typed wrappers over Epic's toolsets under TEE's batch/diff/
   checkpoint contract; server-side LUF↔XYZ normalization (known bug
   class, property-tested round-trip); device catalog answered from a
   local index — Epic's lists are never forwarded raw.
3. Scene-Graph-first vocabulary: entity/component CRUD is the primary
   op family (the UE6 object model); Creative devices wrap as a
   parallel, eventually-legacy family. Stable IDs abstract over Actor
   refPath (UE5) vs Scene Graph entity (UEFN/UE6).
4. Session lane: Play-in-Client launch/stop, hot Verse push, compact
   client-log extraction. Publish/cook/memory: report-only guidance,
   never automated.

### 12.4 Blender `export_for_uefn` op (A22)

1. Pure-Python preflight validator over the encoded Fortnite-Ready
   budget tables (LOD0 tri caps by asset class, three-LOD presence,
   power-of-two ≤2K textures, material-section count, `UCX_` naming
   and ≤10-mesh cap, applied transforms, 1uu=1cm scale, pivot) —
   compact report with the exact fix per violation.
2. The op: LOD1/LOD2 autogeneration at −50% steps, procedural-shader
   baking, Spec=R/Metal=G/Rough=B channel packing, FBX export config
   (Face smoothing, cm scale). Optional auto-import via UEFN Python
   when a live editor is present (physical machine).
3. Optional compact analytics tool on the public Fortnite Data API
   (minutes played / per-player; unauthenticated).

### 12.5 Version-trajectory firewall (A23, A24)

1. Blender rows, with a test each: `use_nodes` write ban in codegen;
   session_uid shuffle regression test (`all_ids` order change);
   Phase 9 listing generator emits per-version entries with min/max
   windows (`@b5_3`); GPU backend probe + `--gpu-backend opengl`
   fallback; `set_gn_input()` chokepoint + enum-translation
   pre-flight; float32 tolerance policy (1e-5, never hash floats);
   Phase 11 ops carry `backend: legacy | gn_physics`.
2. UE rows: 5.8.1 treated as long-lived baseline; TEE-owned
   checkpointing asserted in the proxy (transaction bundling is off
   in tool scripts); re-probe the 5.8-final MCP gap list before
   building fillers (StartPIE exists; doc 07's list is preview-era);
   toolset probing keys recorded per hotfix.
3. One interface over UE and UEFN adapters so the UE6 merge
   (~end-2027) is an implementation swap, not a redesign. Watch
   lanes, revisit at Blender 5.3 beta / UE6 EA: `wm.undo_stack` diff
   bracketing, Jolt node, XPBD schemas, UMG toolset, Blender Lab MCP.

### 12.6 `uefn` skill

Judgment content per A15/A16 packaging: budget interpretation and
memory triage procedure, device-vs-Verse-vs-SceneGraph choice, genre/
economy context from 38 (single-genre rule, engagement-payout
formula), Verse idioms (failure contexts, effect selection,
structured concurrency), the honest automation boundary (what is
drivable vs human-only).

### 12.7 Acceptance

Full suite green, no DCC or UEFN needed: the synthetic digest fixture
parses into API facts; the symbol linter rejects seeded hallucinations
(`<varies>` effect, a removed member, an invented device method) with
exact-fix messages and passes a clean snippet; digest diff between two
fixture versions emits the expected drift facts; the export validator
flags each seeded budget violation (over-cap LOD0, missing LOD, non-
power-of-two texture, bad UCX name, unapplied scale) with the exact
fix and passes a conformant fixture; LUF↔XYZ normalization round-trips
by property test; the capability probe degrades cleanly with no editor
(clear remediation, no crash); license lint proves no AGPL-derived
code and no Epic digest text in the repo. Live-editor lanes (compile
loop, Scene Graph ops, sessions, auto-import) are interface-complete
with fakes and DESCOPED per the 2026-08-22 amendment above.
`docs/PROGRESS.md` updated with evidence.

---

## 16. Phase 13 — Voxkiln: the TRELLIS.2-derived generation product

**RESTORED (owner decision, 2026-08-22, after approval):** the
pending access approval came through and the owner directed the
rebuild; Voxkiln was restored from the removal commit's parent, plus
a networkx dependency fix and CPU-env test skips. The removal record
below stands as history. Phase 13 is in force again; the Mac owes
the live half (weights if cleaned, live generation, determinism,
battery).

**REMOVED (owner decision, 2026-08-22, same day):** the owner removed
the out-of-the-box 3D-generation requirement and had Voxkiln deleted
from the repository — the `voxkiln/` package, its setup doc, the TEE
driver and tests. The phase text below stays as the record of what was
built (it ran live on the M5 Mac before removal; see PROGRESS evidence
log); the research corpus (43–48) stays as knowledge. Generated-3D in
TEE is hosted-only (keyed Tripo/Meshy, dormant) and OFF the outstanding
ledger. Revival point: git history at the removal commit's parent, plus
decisions A26–A28 as amended in `docs/DECISIONS.md`.

**Goal:** owner decision 2026-08-22 — take Microsoft's TRELLIS.2 source
(MIT, code + weights), fix its known defects, and ship it as a SEPARATE
PRODUCT whose primary user is an AI agent; TEE consumes it as the
default generated-3D lane. Working name **Voxkiln** (rename is cheap;
"TRELLIS" must stay out of the name).

**Grounding:** `docs/research/43`–`48` (six-agent pass, 2026-08-22).
Decisions A26–A28 settled — amend via `docs/DECISIONS.md` only.
Anti-goals: no NVIDIA-non-commercial, GPL, or LGPL code in the runtime
import path (nvdiffrast, nvdiffrec_render, cubvh, plyfile, easydict);
no CC-BY-NC weights (RMBG-2.0); no vendored model weights (pinned HF
snapshot_download only); no model-driven poll loops anywhere in the
interface; no renders as evidence; no retraining (defect fixes are
decode/postprocess-side); no bitwise cross-device determinism claims.

### 13.1 Vendored fork + license surgery (A26)

1. Vendor microsoft/trellis.2 @75fbf01 into `voxkiln/` as a
   self-contained package (`voxkiln/vendor/trellis2`, `.../o_voxel`),
   Microsoft copyright + MIT text retained, `UPSTREAM_COMMIT` recorded
   and printed by `voxkiln doctor`. Drop training/data_toolkit and
   windowed-attention code (no shipped config uses it).
2. Import-chain surgery first: lazy-import `postprocess`/`io` out of
   `o_voxel/__init__`, cumesh/flex_gemm out of
   `representations/mesh/base.py`; replace easydict (~50-line MIT
   attrdict) and plyfile (trimesh IO); excise nvdiffrec_render.
   Acceptance: `import voxkiln` succeeds on a clean CPU-only venv and
   a license lint over the runtime tree finds only
   MIT/BSD/Apache/HPND (+ the vendored MPL-2.0 Eigen headers,
   build-time only).
3. Preprocessing without taint: RGBA inputs bypass matting (upstream
   path exists); non-alpha inputs use MIT BiRefNet weights
   (ZhengPeng7), never RMBG-2.0; DINOv3 fetched gated from HF with
   "Built with DINOv3" attribution in README + report provenance.

### 13.2 Defect-fix layer (A27; evidence in research 44)

1. fp32 at every hard decode threshold (subdiv, quad-emission logits)
   + configurable decision margin; per-stage `torch.Generator` seed
   plumbing replacing global `manual_seed`; mesh content-hash in every
   report.
2. Export pipeline rebuilt (`voxkiln/export.py`) in the
   repair-before-bake order: repair (full res) → freeze full-res
   reference (BVH/KD-tree) → staged simplify (3x → target, re-clean
   between) → xatlas UV → CPU bake (numpy UV rasterizer + cKDTree IDW
   over the voxel attr volume) → TELEA seam inpaint → normals → GLB
   with correct alphaMode (BLEND/MASK from alpha stats) and float
   baseColorFactor. DC remesh capped at 512. texture_size clamped to
   what attr resolution supports, with the clamp reported.
3. `voxkiln/repair.py`: levels fast (dedup/degenerate/components/
   winding + in-house boundary-loop fill, 3e-2 perimeter default) /
   manifold (manifold3d Merge + validation) / rebuild (manifold3d SDF
   level_set, pre-UV only). In-process deps exactly:
   trimesh, manifold3d, fast-simplification, xatlas, numpy, scipy,
   opencv. Escalation: structured handoff to TEE's Blender lane.
4. Memory discipline from stableprojectorz: chunked norm/MLP/im2col,
   sampler pred-list drop, spatial-cache clearing (also the batch-leak
   fix); silent resolution downgrade becomes a reported field.

### 13.3 Backends (A28; research 45)

1. Device abstraction `cuda | mps` (no string-patching): the ~20
   hard-coded `.cuda()` sites route through one helper; CUDA path kept
   working (flash_attn/xformers/flex_gemm as upstream).
2. MPS path: sparse varlen attention via FlexAttention-MPS
   (torch ≥2.13) with SDPA fallback; sparse conv + grid_sample via
   vendored, pinned mtlgemm (fallback: pure-PyTorch gather-scatter);
   `o_voxel._C` hash kernels replaced with `torch.unique`/
   `searchsorted` equivalents; pure-Python dual-grid mesh extraction
   (trellis-mac lineage) as the portable baseline.
3. Residency mode: no low_vram on ≥32 GB unified memory — all models
   stay loaded; worker process + heartbeat so the server never blocks;
   GPU-watchdog empty-output detection and thermal-throttle timing
   are structured errors with fixes.

### 13.4 AI-first surface (A28; research 47)

1. Python API: `submit/wait/generate/query`. CLI: `voxkiln gen
   input.png --seed N --max-tris N --watertight --json` (exit code =
   verdict), `jobs`, `show`, `doctor`, `fetch-weights`.
2. MCP server, exactly 4 tools: `gen3d_generate` (bounded wait,
   checkpoint token on timeout), `gen3d_wait`, `gen3d_query`,
   `gen3d_status`. Everything else lives in the params dict.
3. The report: `{asset_id, files, stats{tris, verts, watertight,
   bbox_m, materials, uv_coverage}, repairs[], verdict{accepted,
   violations[{rule, got, limit, fix}]}, provenance{generator,
   generator_version, upstream_commit, model_repo, model_revision,
   input_image_sha256, seed, params, ai_generated: true}, timings,
   peak_mem}`. Budget in → accept/reject + exact fix out, one message.
4. Input-hash cache (sha256(image)+params+model revision) checked
   before any GPU work; submit ack carries est_seconds /
   est_peak_mem_gb / queue position; no capable backend → structured
   refusal naming the hosted fallback.

### 13.5 Eval harness (A27; research 48)

1. CI (weightless): synthetic seeded-defect fixtures (holed sphere,
   non-manifold fin, degenerate slivers, watertight-interpenetrating
   concat) with exact-count assertions; the metric module doubles as
   the product's report code. Metrics: watertightness, boundary
   loops, non-manifold edges, degenerates, per-component Euler, UV
   overlap %, texel-density CV, silhouette IoU (CPU raycast).
2. Mac battery: upstream-canonical example images + owner photos
   (frozen SHA256s), seeds {0,42,1234}, `512` + `1024_cascade`,
   topology-expectation tags; stock-vs-ours deltas appended to
   `voxkiln/BENCHMARKS.md` (frontmatter: commits, torch, macOS,
   machine, thermal state). Determinism measured (same-seed ×3),
   never assumed.

### 13.6 TEE integration + handoff

1. TEE gains a `voxkiln` GenDriver (unpaid, local) registered FIRST in
   `build_drivers()` when the product import-probes clean —
   `as_generate` therefore defaults to it; Tripo/Meshy stay as keyed
   fallbacks. `probe_local_gpu` learns MPS. Fake driver mirrors the
   report contract for tests.
2. Generated assets flow into the existing as_import cleanup +
   provenance path; the Voxkiln provenance manifest satisfies the
   Phase 9 attribution rules (`ai-generated` flag + generator + input
   hash).
3. Mac-session steps recorded in PROGRESS: install `[voxkiln]` extras,
   fetch weights, run the live battery stock-vs-ours, tune
   FlexAttention, decide own-repo extraction.

### 13.7 Acceptance

Cloud: clean-venv `import voxkiln` (CPU-only) passes; license lint
proves the runtime tree MIT/BSD/Apache-clean (no nvdiffrast/
nvdiffrec/cubvh/plyfile/easydict imports reachable, no RMBG-2.0
reference); repair/export/report/metric suites green on the seeded
fixtures with exact counts; MCP surface serves 4 tools over stdio with
the report schema; TEE's as_generate routes to the voxkiln driver by
default with the fakes; cache hit returns without invoking the
pipeline; structured refusal fires on a GPU-less box. Mac: the live
battery runs stock-vs-ours and PROGRESS gets the numbers.
`docs/PROGRESS.md` updated with evidence.

---

## 17. Standing rules (all phases)

- **Measure before optimizing:** log every tool's response size from day one;
  alert when a median exceeds 2K tokens.
- **Prompt-cache-friendly by construction:** deterministic tool ordering,
  frozen descriptions, volatile state (revisions, timestamps) never in tool
  definitions.
- **Security floor:** localhost binds only; code-exec tools opt-in + AST
  screen + auto-checkpoint; respect `bpy.app.online_access`; never expose DCC
  sockets beyond the machine; mirror the official weak-sandbox denylist
  (`wm.quit_blender`, `wm.read_factory_settings`, `sys.exit`).
- **Version drift watch:** shim tables keyed on version tuples
  (`bpy.app.version`, engine version); Blender 5.3 lands Nov 2026 and 6.0
  (Nov 2027) removes today's deprecations — new fault lines go into the shim
  table with a test each.
- **Honest reporting:** acceptance criteria are checked by running the
  commands, not by asserting success in prose. Paste real output into
  `docs/PROGRESS.md` when checking off a phase.

---

## 18. Phase 14 — TEE Pins: introspectable marker actors (owner request, 2026-08-22)

**Goal:** the owner asked for pins in OkongoSim — a small marker actor
standing where something should eventually go, carrying its own record so
it can be asked about ("list the pins", "what is pin market-03") and
filled from the free asset sources without clicking anything in the
editor. Decision **A29** in `docs/DECISIONS.md` settles the storage: the
DCC's own actor tags, not a sidecar file.

**Grounding:** the live editor. Every Unreal claim in this phase was
verified against UE 5.8.1 on the M5 Mac, not against memory.

### 14.1 Tag encoding (`tee/pins/model.py`)

- One marker tag (`<ns>`), then `<ns>_<field>:<value>` for id, name, cat,
  note, wish, class, dims, asset, actor. Values split on the FIRST colon,
  so an asset key (`polyhaven:GreenChair_01`) round-trips.
- Ids are lowercase slugs, enforced: Unreal compares FName tags
  case-insensitively, so `Market-03` and `market-03` would silently be one
  pin.
- `|` separates list entries inside one tag and is rejected in free text.
- Upsert semantics: fields not mentioned keep their value; an explicit
  empty clears one.

### 14.2 Editor programs (`tee/pins/program.py`)

One dispatch each: read all pins, upsert one, remove one, clear a fill.
The marker is the engine cone, scaled to 18 x 50 cm, base ON the spot,
collision off AT SPAWN, `is_editor_only_actor` true, outliner folder
`TEE/Pins`, and an orange instance of the engine's basic-shape material.

### 14.3 Tools (`tee/pins/tools.py`)

`pin_set`, `pin_list`, `pin_show`, `pin_fill`, `pin_remove` — registry
tools (progressive disclosure), Unreal-only, refusing other adapters with
the reason. `pin_fill` with no pick searches the pin's wishlist and
returns a shortlist; with `pick=` it imports at the pin through the normal
`as_import` machinery, applies the pin's yaw, and records the chosen key
back onto the pin.

### 14.4 Acceptance

Live on OkongoSim: a pin created, read back through `pin_show`/`pin_list`,
filled from Poly Haven on the owner's pick, before/after captures, and the
level saved. Evidence in `docs/PROGRESS.md`.
