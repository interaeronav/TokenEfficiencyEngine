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
asserts summarized size < 10% of raw); fallback tier smoke-tested on an older
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

## 11. Standing rules (all phases)

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
