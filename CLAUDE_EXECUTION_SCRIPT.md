# TEE Master Execution Script

**Current architecture build (owner, 2026-09-11):** follow
`CLAUDE_A83_SCRIPT.md` for architectural drawing correctness, professional BIM
depth and cabinet production benchmarked against Revit, Archicad, Rhino,
SketchUp and Mozaik. The owner rejected A82's example quality. A82 is accepted
on both actual clients; preserve it while developing in an isolated snapshot
and prepare a new coordinated release only after verified acceptance gates.

**Current build (owner, 2026-09-11 local / 2026-09-10 UTC):** follow
`CLAUDE_A81_SCRIPT.md` for Cline and Aider documentation automation in any
connected project, including TEE. The A79/A80 rollout is accepted by both
clients and closed. Preserve its frozen deliveries; A81 uses a new upgrade
packet. This request does not authorize an unrelated commit, push or release.

**Standing upgrade protocol (owner, 2026-09-10):** whenever Claude or Codex
initiates an extension/runtime upgrade, GPT-6 composes its coordination packet
under `docs/upgrade-coordination-protocol.md`. Deliver the appropriate artifact
or source packet to both clients from one verified payload, preserve continuity,
and require both actual-client receipts before declaring completion. This rule
applies to the packaging/update phases below, regardless of the initiating model.

**Current coordination request (2026-09-10):** follow
`CLAUDE_UPDATE_COORDINATION_SCRIPT.md` for the owner's handoff review and Claude
return receipt. The downloaded brief is reference material. This request covers
review, a Downloads delivery file and GitHub connectivity; it does not trigger
the generic commit/push or installation steps below. A78–A80 source work and
unrelated owner edits remain preserved under their recorded scope.

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

### Owner-requested Codex installation addendum (2026-09-10)

Install the existing local TEE build as a personal Codex plugin, carrying its
MCP launch configuration and usage skill. Use Codex's supported plugin CLI and
personal marketplace; preserve other client settings. Reuse the repository's
Python environment without syncing away installed extras, and serve the five
adapters in the current desktop manifest with no declared default. Verify a
real MCP initialization, tool listing and read-only status/discovery calls;
validate the plugin and confirm Codex reports it installed and enabled. Record
the local paths, evidence and new-task pickup requirement in `docs/PROGRESS.md`.
This is a local installation, not a version cut or a rerun of completed builds.

### Owner-requested Formula One design study (2026-09-10)

Use TEE as co-pilot for an original graphite, silver and electric-blue 2026
Formula One car, with a modelled cockpit, photorealistic views and PDF delivery.
Ground selected dimensional checks in the current official FIA rules. Build
the scene in an isolated Blender file, preserve existing live scenes, and
measure the model before rendering the full-resolution views. Use installed
TEE wind-tunnel engines for a documented 300 km/h study if a valid case can be
run; distinguish solver output, analytic calculations and illustrative arrows.
Do not claim FIA certification or validated aerodynamic performance from a
visual model or an unconverged solve. Deliver editable geometry, reproducible
scripts, angle and cockpit renders, and a PDF with aerodynamic graphics,
assumptions, sources and outstanding verification under `output/f1-2026/`.
Record actual evidence in PROGRESS before ending the session.

Owner addendum: include full editable concept CAD of the structure and frame,
with an exact-solid STEP assembly of the survival cell, bulkheads, crash
structures, suspension interfaces and stressed drivetrain placeholders. Include
the structure, sections, exploded views, dimensions and a component schedule in
the PDF package. Distinguish geometric completeness from unverified laminate,
load, impact, fatigue and homologation engineering; do not call a visual shell
a validated safety structure.

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

## 17. Phase 15 — Expert Knowledge Base: import, boundary, jurisdiction wiring

**Goal:** absorb the owner's 38-domain reference library (401 files,
~1.4M words, 1,811 cited sources) into the repo without letting it
contaminate TEE's own grounding — and cash the one thing in it that
closes a tracked gap: SANS 10400 / Namibian building control.

**Grounding:** the corpus's own `knowledge-base/00_meta/` (SCHEMA,
VERIFICATION register, source-register). Decision A30 settled — amend
via `docs/DECISIONS.md` only. Anti-goals: no TEE tool reads the KB at
runtime unless a step below says so; no KB search/embedding/RAG lane
(A2/A11 tool surface is unchanged — **amended by A31 / Phase 16, owner
request 2026-08-26: read-only `kb_*` query tools over the mirror are
the sanctioned runtime lane; every rule in this paragraph still binds
whatever those tools return**); no fact enters a TEE data file
without its original citation travelling with it; **no `bpy`/`unreal`
API fact is ever taken from `13_*`/`14_*`/`15_*`** (third-party prose
on a drifting API is the failure mode TEE exists to prevent); no
re-writing, summarizing or "improving" mirrored files — they are
imported verbatim, frontmatter intact.

### 15.1 Mirror (A30)

1. Verbatim copy of all 38 domains to `knowledge-base/<domain>/`,
   YAML frontmatter preserved, plus `INDEX.md` and `00_meta/`.
2. `knowledge-base/README.md` states the two-corpus boundary in the
   first screen: what this is, what it is not, what TEE actually
   consumes, and its provenance.
   Acceptance: 401/401 files present, spot-checked against the source
   listing; no file rewritten (frontmatter `id:` still parses).

### 15.2 Jurisdiction wiring — the one scope widening (A20, A30)

1. `server/src/tee/physical/` gains a `southern-africa` jurisdiction:
   SANS 10400 parts as CODE-severity rules, the Namibian building-
   control route as its own instrument (Namibia is NOT "South Africa
   with a different flag" — the KB's `03_codes_standards/00_overview`
   is explicit that the legal stacks differ; a Namibian finding cites
   the Namibian instrument).
2. Every rule added carries `source` + `clause` through to
   `plaus_rules.json`, re-checked against the citation in the KB file
   rather than trusted from it.
3. A20's contract is untouched: findings, not approvals; severity
   CODE/STD/HEUR/CONV; no sizing, no "passes", no certification.
   Unverified numbers stay flagged rather than shipped as fact.
   Acceptance: a plan checked with `jurisdiction="namibia"` returns
   findings citing Namibian/SANS clauses; the same plan under the
   default jurisdiction is unchanged; tests cover both; no rule
   without a citation.
   **DONE 2026-08-25.** Implemented as six regime profiles with
   jurisdiction-dependent SEVERITY, not merely jurisdiction-dependent
   values — because the KB establishes that SANS has no legal force in
   Namibia. Bare "namibia" deliberately does NOT resolve to a regime
   (it caps at HEUR and asks); an unknown region raises. 12 tests;
   zero always-loaded tokens added.

### 15.3 What stays reference-only

Materials/suppliers, Namibia climate + geology, walls, paving,
joinery, interiors, hydrology, machine vision, and every
non-construction domain are carried as reference text and wired into
nothing. Candidate future work (NOT promised here): material facts
into `assets/materials.py`, Namibia climate into site/sun defaults,
`25_environmental_asset_creation` read against `docs/research/`
rather than instead of it. Each would be its own decision entry with
its own verification.

### 15.4 Acceptance

Mirror complete and verbatim; README boundary stated; CLAUDE.md
carries the two-corpus rule and the DCC-domain prohibition; A29 in
`docs/DECISIONS.md`; the southern-africa jurisdiction ships with
cited rules and tests; full suite green; `docs/PROGRESS.md` updated
with evidence. The KB adds ZERO always-loaded tokens to the tool
surface — verified by the canonical tool-surface measure.

---

## 18. Standing rules (all phases)

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

## 19. Phase 14 — TEE Pins: introspectable marker actors (owner request, 2026-08-22)

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

### 14.5 Durability (`pin_export` / `pin_import`)

Pins are authored state inside a level that a project regenerates from its
data files. `pin_export` writes a stable, sorted, repo-trackable JSON of
every pin; `pin_import` replays it — markers restored, recorded assets
re-placed only where nothing is actually standing. `pin_list` reports
`missing` when the tags claim an asset the level no longer has.

---

## 20. Phase 16 — TEE KB: the Expert Knowledge Base query module (owner request, 2026-08-26)

> **DONE 2026-08-27 (cloud)** — 16.1–16.4 and 16.6 acceptance 1/2/3/5
> built and measured; see `docs/PROGRESS.md`. Prerequisite discovered and
> fixed first: the Phase 15 mirror never carried `manifest.json` /
> `AGENTS.md` and was not byte-exact (330 trailing-newline artifacts, 7
> noisy files) — completed and hash-reconciled against Dropbox before
> building on it. 16.5 is documented in `docs/setup-kb.md`; the one-line
> `[kb]` addition to OkongoSim's own `.tee/config.toml` (acceptance 4)
> is owed by the Mac session with that repo.

**Goal:** give OkongoSim (and any TEE client) sourced answers from the
owner's `12 Expert Knowledge Base` — 38 domains, 401 curated markdown
files, ~1.3M words, every claim cited or flagged — without pasting
documents into context. The sim cross-references real-world metrics
(jurisdiction, confidence, sources) through the same MCP surface that
drives the editor.

**Grounding:** the corpus's own `AGENTS.md` and `manifest.json` —
since Phase 15 both live IN-REPO at `knowledge-base/` (the mirror is the
default root; the owner's Dropbox copy, `02 Okongo Oneleiwa Project/12
Expert Knowledge Base`, remains a valid `[kb] root` override). The
manifest carries per-file id, title, domain, tags, jurisdiction, status,
confidence, words, sha256 and summary — the index source. Decision
**A31** in `docs/DECISIONS.md` settles the shape: read-only module,
manifest-indexed, progressive disclosure, flags pass through verbatim.

**Anti-goals:** no writes into the corpus (its own `validate.py` /
`rebuild.py` own that); no embeddings or new runtime dependencies; no
full-file or full-corpus dumps; no rephrasing of confidence/jurisdiction.

### 16.1 Index builder (`tee/kb/index.py`)

1. Load `<root>/manifest.json`; validate required keys; one loud, short
   error if missing or malformed (with the fix: point `[kb] root` at the
   corpus).
2. Build the index: per-file record (id, path, title, domain, tags,
   jurisdiction, status, confidence, words, sha256, summary) plus a
   domain table (slug, title, file/word counts) and corpus totals.
3. Cache to `<project>/.tee/kb/index.json` keyed on manifest `generated`
   date; rebuild on demand (`kb_status(rebuild=true)`) — never on every
   call.
4. Drift check: sha256 each indexed file, compare with the manifest.
   Any mismatch or missing file marks the index `stale` and lists the
   offenders (capped); queries still serve but carry the staleness flag,
   and the fix line says to run the corpus's `00_meta/rebuild.py`.
5. Per-file heading index (section title → byte range) parsed from the
   markdown so `kb_read` can address sections without loading whole files
   into responses.

### 16.2 Retrieval (`tee/kb/search.py`)

Deterministic keyword scoring over manifest titles, tags, summaries and
the heading index — no embeddings. Filters: `domain`, `jurisdiction`,
`confidence`, `status`. Results ranked, capped, each row carrying the
corpus's flags verbatim. Empty result returns the domain list as the
cheap next move, not silence.

### 16.3 Tools (`tee/kb/tools.py`)

Four registry tools (progressive disclosure — none on the always-loaded
surface; descriptions under 2 KB each):

- `kb_status` — corpus totals, domain table (compact), index freshness
  and drift list, configured root; `rebuild=true` rebuilds the cache.
- `kb_search` — query + filters → hit list only: id, title, domain,
  confidence, one-line summary. Default limit 8, hard cap 20.
- `kb_read` — one file by id. No section arg → section list (titles +
  sizes) plus the frontmatter flags. With section → that section only,
  token-budgeted (`max_tokens`, default 800, cap 4000). Cite the file's
  `## Sources` block alongside, truncated to fit the budget.
- `kb_facts` — the `## Key facts` blocks of matched files (query or id
  list) — the metrics lane. Confidence flag on every block; a file
  without the section says so in one line.

Every response that carries corpus content carries its confidence and
jurisdiction markers. `needs-verification` content is labelled, never
served bare.

### 16.4 Config and wiring

1. `config.py`: `[kb]` section — `root` (path to the corpus; defaults
   to the in-repo `knowledge-base/` mirror from Phase 15 when present,
   otherwise required to activate the module), optional `max_kb`
   response budget. Missing `[kb]` with no mirror → module silently
   inactive (like other extras); malformed → the standard
   degrade-with-warning path.
2. `cli.py`: `_attach_kb(app, project)` next to the other attaches;
   doctor gains a kb check (root exists, manifest readable, drift count).
3. No new dependency; stdlib + existing kernel (budget, errors, registry).

### 16.5 OkongoSim wiring

Add `[kb] root` to OkongoSim's `.tee/config.toml` (the tracked config
that already carries the pin namespace) pointing at the TEE repo's
`knowledge-base/` mirror — stable, versioned, and already on the
machine; the Dropbox corpus is the fallback root if the mirror is
absent.
TEE is the MCP surface OkongoSim sessions already use, so the tools land
with no plugin change. Document in OkongoSim's `docs/` beside
`tee-pins.md`. (Stretch, only if asked: a `kb_query` editor console
command through TeeToolset.)

### 16.6 Acceptance

1. `pytest` green: index build, drift detection, search ranking/filters,
   section reads, budget caps, flags-pass-through, malformed-manifest and
   missing-root error paths (fixture corpus, never the live Dropbox one).
2. Live against the real corpus: `kb_status` clean, one `kb_search`
   (e.g. paving specification), one `kb_read` section, one `kb_facts`,
   every response carrying confidence/jurisdiction.
3. Benchmark row in `benchmarks/RESULTS.md`: the paving-spec lookup via
   `kb_*` vs dumping `INDEX.md`/files raw.
4. OkongoSim `.tee/config.toml` carries `[kb]`, and a session driving
   the sim answers a site question from the corpus with citations.
5. Evidence in `docs/PROGRESS.md`; README module table gains the kb row.

## 21. Phase 17 — Local VLM lane: on-machine vision-to-text (owner request, 2026-08-27)

The machine now runs a local vision model (Qwen3-VL-30B on `mlx_vlm.server`,
fronted by the owner's LiteLLM shim at `127.0.0.1:4000/v1`, model id
`claude-qwen-vl`; the shim lazy-starts the vision server on first use). That
turns P3's ladder into three rungs: text checks, then a LOCAL model reads the
pixels and returns words, and only then budgeted JPEG into host context.

1. `tee/kernel/local_vlm.py`: stdlib-only OpenAI chat client —
   `available()` + `describe(image_bytes, question)`. Env overrides
   `TEE_LOCAL_VLM_URL` / `TEE_LOCAL_VLM_MODEL`. TeeError with an actionable
   fix when unreachable (P7); never a new core dependency.
2. `ue_look(question, max_kb=96)`: capture → local VLM → short answer plus
   the free camera/actor metadata. The image never enters host context, so
   the byte budget is generous where `ue_capture` defaults to 16 KB.
3. Extraction: `LocalVlmDriver` beside `ApiDriver` (same interface, zero
   cost, nothing leaves the machine); `ex_prepare` advertises both drivers.
4. Acceptance: offline unit tests (client payload/error paths, `look`
   composition, driver JSON parse) green; live `describe()` through the
   shim answers a known image correctly, lazy-start included.

### Formula One study follow-up (same owner task, 2026-09-10)

Revise the visible cockpit protection into a streamlined graphite fairing while
preserving three mounting datums and a distinct structural core. Record that
RV-HALO / PL-HALO and any aerodynamic benefit remain unverified; the existing
CFD proxy excludes this feature. Extend the CAD assembly with the halo core
and support. Expand the 300 km/h downforce report with numerical-window
statistics and pressure/shear force-balance graphics, keeping final-iteration
integrals separate from iteration-window averages. Regenerate affected views,
PDFs and editable model files before delivery.

### Formula One Fusion and video extension (owner request, 2026-09-10)

Create a separate live Autodesk Fusion document, retain the exact structural
STEP solids, import the complete visual exterior/cockpit/halo geometry with
materials, and export a local Fusion archive. Identify imported mesh geometry
and reference parameters accurately; do not imply native editable feature
history for an imported mesh. Preserve the owner's other documents.
Create a narrated 1080p MP4 demonstrating current 2026 changes, using the
existing car renders and animated technical graphics. Ground it in FIA Section
C Issue 20 and official FIA/F1 explanations; distinguish concept styling and
preliminary CFD from rules. Include captions, transcript, source record and
Fusion/video pages in the delivery package, inspect frames and verify outputs.

### TEE model-efficiency campaign (owner request, 2026-09-10)

Follow `CLAUDE_A78_SCRIPT.md` for the local-model/ChatGPT lane-driving campaign.
The AETHER concept package is the quality reference; model parity is a measured
acceptance question, never inferred from token savings or script replay.

### CADAgent integration (owner request, 2026-09-10)

Follow `CLAUDE_A79_SCRIPT.md`: research the downloaded CADAgent, then integrate
its useful local modelling operations into the existing TEE Fusion lane.

### Local machine learning and continuous improvement (owner, 2026-09-10)

Follow `CLAUDE_A80_SCRIPT.md` for TEE-wide learning, including CADAgent: local
observations, trained reliability/cost models, held-out evaluation, continuous
updates and rollback within the existing capability and model-pin boundaries.

### W0 thinking engine — external review correction round (Codex, 2026-09-13)

Codex reviewed head `73a76e1` against `claude-change-summary.md` and returned four
findings (`~/Downloads/claude-w0-review-response.md`). This is a **review handoff, not
an execution packet and not release approval**; the standing GPT-6 coordination
protocol still governs any later upgrade. No install, client restart, profile or
model-configuration change, weight download, push or release is in scope. Thinking
stays disabled by default throughout.

Work the four in order, each with its own regression:

1. **[P1] The candidate must be self-contained.** `c306138` committed
   `test_blender_lessons.py` while its subject, `adapters/blender/guidance.py`,
   stayed untracked, so a `git archive` of the head fails collection. Complete the
   dependency rather than sweeping in other sessions' work, and add a test that
   fails on any tracked module importing an untracked one. Report candidate results
   separately from working-tree results.
2. **[P2] `repair_script` must accept evidence-backed renames.** The intent-
   preservation rule demands a substring relation between the lost and kept token;
   a correct spelling repair (`tee_sttaus` → `tee_status`) has none and is rejected.
   Admit renames the supplied error evidence licenses, keep every deletion control
   failing, and **re-measure eps** for the chore afterwards.
3. **[P2] Bind token floors to the mode actually executed.** `audition()` omits
   `thinking` from its row while `matching_floors` compares the resolved profile's
   flag, so `q27b-think` discards its own floor forever. Engine *capability* is not
   request *mode*: derive one effective mode, stamp the measured row with it, look
   floors up by it, and assert the **outbound wire flag**, not the config value.
4. **[P2] Retire the universal widening claim.** `eps*q + (1-eps)*q**N` is one model
   with unstated assumptions, not the general failure probability: for the
   retry-until-N reading, `F_N = q*eps + q*(1-eps)*F_(N-1)` gives 0.34375 at
   q = eps = 0.5, N = 3 where the stated form gives 0.3125 — and the stated form
   **understates** the floor. A seeded false-accept fraction is coverage of a stated
   fault set at a stated sample count, not a population bound, and a blind verifier
   failing to catch errors does not prove thinking cannot lower per-attempt error.
   Replace the impossibility claim with an empirical adoption gate; keep the
   conservative default; supersede the old conclusions without deleting the
   evidence. Check that no downstream learning path turns schema acceptance into a
   semantic correctness label.

Return to Codex: disposition, changed files, regression evidence, remaining
limitations, and the exact tested source identity — saying plainly whether each
number came from isolated committed source or the shared working tree.

### W0 proposal correction round two — the accepted runtime is the baseline (Codex, 2026-09-13)

Codex reviewed the stage A proposal (`gpt6-packet-request.md`) against HEAD
`dd5a2a5` and returned three findings. The first inverts a decision taken in the
previous round and is the important one.

**The premise that was wrong.** Round one treated the untracked Blender
`guidance.py`/`recipes/`, Fusion CADAgent, `docagents`, `kernel/guidance.py`,
`learning/hooks|tools` and `structural` as *another session's unshipped work*,
and removed the first two from the candidate to avoid dragging a live lane into a
release. They are not unshipped: they are **already delivered and accepted** in
A84 and are running in Claude's installed runtime right now. Being untracked on
this branch is a version-control gap, not a statement about the product.
Excluding them REGRESSES the installed product, and no choice between 197 and
199 tools addresses that.

The baseline for this candidate is therefore **the accepted A84 payload**, not
this branch's HEAD. Measured: A84 `source-manifest.json` records 324 files, the
installed runtime hashes to 324 files and the same fingerprint
`0e17244…fb252f`, and the candidate carries 287 — **37 omitted**.

Work the three findings, each with evidence:

1. **[P1] Reconcile against the accepted runtime.** Produce a complete
   added/removed/changed comparison of the accepted payload against the
   candidate, data, recipes and licences included, plus any changed registration
   path that would leave a retained module unreachable. Prepare an isolated
   **cumulative** candidate that keeps every accepted capability and applies the
   reviewed W0 corrections — from the verified accepted payload plus reviewed
   changes, never by sweeping the dirty tree. Record provenance and disposition
   per difference. Any intentional removal is a deployment-scope decision for the
   coordinator and owner, and must be named as one rather than hidden by editing
   a benchmark expectation.
   Also correct the proposal's attribution of the two-tool delta: the learning
   module registers five `learn_*` tools while `kernel/guidance.py` registers
   `lane_guide` and `lane_preflight`. Trace the registration before blaming a lane.
2. **[P1] The candidate is unbuildable, and it is not an export artifact.** The
   four `test_local_mcpb_build` errors were misdiagnosed in round one. The real
   cause is `SystemExit: missing bundle input: docs/small-model-workflows.md` —
   `packaging/build_local_mcpb.py:46-51` lists it in `EXTRAS` and line 168
   refuses to build without it. It is untracked and absent. Include it, audit
   every packaging input for the same defect (the canonical usage skill
   included), re-run the build tests against the candidate's own files, and
   inspect the resulting artifact's members and normalized payload. A successful
   ZIP write is not completeness.
3. **[P2] The dependency plan describes the wrong bundle shape.** "An `.mcpb`
   install rebuilds the venv from the lock and deletes the extras" is the
   PORTABLE shape. Claude's current local Python bundle names
   `/Users/john/TokenEfficiencyEngine/server/.venv/bin/python`, puts its own
   `src` first on `sys.path` and borrows that interpreter; it provisions nothing
   and runs no `uv sync`. Our own builder says so at `build_local_mcpb.py:62-66`.
   Correct the proposal, keep the local delivery default, retain dependency
   inventory and rollback evidence, and add no blanket reinstall to a
   source-only update. Portable hazards stay conditional on choosing that shape.

Scope: proposal and candidate preparation only. No install, client restart,
source-target switch, dependency sync, weight download, push or release. Keep
existing authorizations, the model choice, the five grants and concurrent work
intact. Correction evidence stays separate from the immutable A84 receipts, and
none of it is two-client acceptance.

### W0 preparation, round three — one candidate, one identity (Codex, 2026-09-13)

Codex reviewed `92b8d97`, confirmed the three round-two fixes, and returned three
preparation items. HEAD had meanwhile advanced past the reviewed point; do not
restart the earlier rounds, incorporate them.

1. **[P1] Build isolated, with the permanent interpreter supplied.** Round two's
   receipt claimed a real delivery must be built from the shared checkout because
   the verification build named a temporary `.venv`. That is **wrong**: source
   location and runtime interpreter are independent inputs, and returning to the
   dirty checkout risks shipping unreviewed source. Build from the isolated
   candidate with `--python` naming
   `/Users/john/TokenEfficiencyEngine/server/.venv/bin/python`, then verify the
   manifest carries no temporary path, compare the whole normalized artifact
   runtime against the candidate for set AND byte equality, check resources,
   usage skill and wrapper inputs separately, and record path, byte count and
   SHA-256 without reusing a prior artifact's hash.
2. **[P2] Rewrite the proposal around ONE current candidate.** Revision 2 still
   carried a nine-commit list, called `5d188e0` HEAD, repeated the disproved
   "export artifact" explanation of the packaging errors, and kept an obsolete
   blocking-decision claim in its opening. Name the final candidate by full
   commit and complete payload fingerprint; distinguish the tested candidate from
   any later documentation-only commit; put current results first, each bound to
   the source actually tested; reconcile counts, hashes and decisions across both
   documents; and explain the benchmark's configured composition rather than
   implying its 232-tool count is interchangeable with a live 273-tool count.
3. **Complete the validation record.** Give the untracked suites, the formatting
   failure and the full-suite orphan test each an explicit disposition. Run the
   canonical suite against isolated candidate source with `PYTHONPATH` pinned and
   the prepared interpreter — no environment sync, and never `-m "not dcc"` in
   place of the project's own exclusions. Investigate the orphan failure enough to
   say harness race or product failure; **fix a confirmed defect or return a
   concrete unresolved risk — do not rerun until green or weaken the assertion.**

Scope unchanged: authorized reversible preparation only. No install, client
restart, launch-target change, dependency sync, model download, push or release.
Existing model selection, grants, project state and other sessions' work stay
protected. No client receipt is required or may be invented.

### W0 round four — the test suite was deleting live workdirs (Codex, 2026-09-13)

The most serious finding of the campaign, and it is a PRODUCT defect with a test
amplifier. Work it before any further full-suite run.

**What happens.** `server/tests/test_purge.py` calls `purge(confirm=True)` in
three tests. The `state` fixture isolates the project `.tee` tree via `tmp_path`,
but `workdirs` discovery ignores `project_root` entirely: `purge._temp_workdirs()`
globs `tee-*` directories in BOTH `tempfile.gettempdir()` and a hard-coded
`/tmp`. `workdirs` is in `DEFAULT_CATEGORIES` and `older_than_days` defaults to
**0.0**, so every matching directory qualifies however new it is. Codex's review
run lost its own export, log and verification build this way.

**The product's claim is false, in its own words.** The category description says
these directories cost "nothing - these belong to processes that have exited",
and `_temp_workdirs`'s docstring says "the processes that made them are gone, so
there is no registry to consult". Nothing establishes either. The long-lived
producers - the blender, fusion, godot and freecad adapters and
`assets/library.py` - hold their `mkdtemp` directory open for the life of a
running server.

1. **[P1] Make validation safe first.** Give the fixture ownership of discovery:
   substitute fixture-owned roots so no test can enumerate a real temp directory
   (patching `TMPDIR` alone is not enough - `/tmp` is hard-coded). Add a
   regression with a sentinel in a separate test-owned directory that must
   survive a confirmed sweep, and instrument the destructive path to fail before
   touching anything outside the allowed set. Keep the dry-run, protected-record
   and capability-preservation checks meaningful: do not delete the purge tests,
   exclude them, or merely rename the review export.
2. **[P1] Make the policy match the claim.** Ownership and inactivity must be
   established, not inferred from a prefix. Active workdirs are preserved,
   including other processes'. Unknown directories are preserved and reported as
   **unverified**, never called orphaned, and are never retroactively marked
   owned to make them removable - leaving legacy directories unreclaimed is
   acceptable. Identity checks must survive PID reuse; missing, unreadable or
   ambiguous evidence fails closed. Validate containment and symlinks, and
   re-check ownership and liveness AT DELETION TIME rather than trusting the
   dry-run listing. Do not widen purge into arbitrary path deletion. Smallest
   design the existing code supports.
3. **[P2] Structural tests exist; my claim that they do not was false.** They are
   committed on the local branch `codex/a84-reviewed-runtime` at `18666b3` -
   `test_structural.py`, `test_structural_runner_limits.py`,
   `test_structural_shutdown.py`. Recover the appropriate ones with their
   provenance, without merging that branch or overwriting current source, and
   scope native-engine checks honestly. Correct both documents: absent from this
   branch's candidate, not absent from the repository.
4. **Re-validate.** A purge source change moves the payload fingerprint: compute
   and report the new one and the new delta rather than reusing
   `397261a2…7ed22`. Focused purge and structural regressions first, then the
   canonical suite on isolated source with the prepared interpreter and pinned
   PYTHONPATH, then lint. Rebuild the verification artifact isolated with
   `--python` naming the permanent interpreter. Keep the wind-tunnel orphan race
   visible until disposed.

Never reproduce the failure by confirming a sweep of a real temp root. Every
destructive reproduction uses freshly created, fixture-owned directories only.
Do not attempt to reconstruct or remove unknown temp contents, and do not claim
recovery that has not been verified.

### W0 round four, addendum — the ownership validator itself fails open (GPT-6)

GPT-6 accepted the test isolation, the recovered structural suites, the complete
runtime payload and the local packaging approach at `47765b7`, and found the new
validator wrong in exactly the way it was written to prevent. Reproduced here
before accepting; all four hold.

1. **[P1] `state_of()` returns `reclaimable` before it validates the marker.**
   The dead-pid branch returns first, so a marker whose `started` is missing,
   empty, or not a string still admits the directory for deletion — and
   `claim()` itself writes `started: ""` whenever `_proc_start()` cannot read an
   identity, so TEE manufactures its own fail-open. Require a complete, valid
   marker BEFORE any reclaimable return: a non-empty string identity, schema
   checked, required fields present.
2. **[P1] The marker is read through a symlink.** `marker.read_text()` follows
   one, so a directory whose `.tee-workdir.json` points at an external marker is
   accepted and deleted. `purge._contained()` validates the DIRECTORY, not the
   marker. Require a regular, non-symlink marker file.
3. **[P2] A malformed pid aborts the whole purge.** `isinstance(pid, int)`
   admits `10**100`; `os.kill` then raises `OverflowError`, which is not an
   `OSError` and is not caught, so one bad marker kills discovery for every
   directory in the call. `isinstance` also admits `True`. Exclude booleans,
   validate the type, and treat an unrepresentable or otherwise undeterminable
   probe as `unverified` — never as evidence of exit. Keep the handling narrow
   enough that real defects still surface.
4. **Regressions at the deletion boundary.** Cover missing/empty/wrong-type
   `started`, a symlinked marker, oversized and boolean pids, a live owner, a
   validly exited owner, and pid reuse — through BOTH dry run and confirmed
   purge, each reported as kept with no exception and no removal. Keep the
   outside sentinel and the prefix decoy, and keep both isolation layers.
   **The existing late-claim test does not prove what it claims:** it changes
   ownership between two separate calls, which fresh enumeration catches on its
   own. Inject the change at the enumeration seam, inside ONE confirmed call,
   and assert the directory is kept with a reason.

A source fix invalidates `d792b339…`: recompute the manifest, rebuild the
artifact isolated with the permanent interpreter, and record an ABSOLUTE
artifact path with its size and hash. Reconcile both documents onto one
candidate — bind every result to the source that produced it, carry the full
commit id and fingerprint in the current identity table, replace the stale
"structural has no tests" limitation with the native-engine one, and attribute
each skip to the command that produced it. Propose a PROGRESS entry rather than
writing one: GPT-6 owns the shared ledger.

### W0 round six — the wind-tunnel process lifecycle (GPT-6, 2026-09-13)

The purge corrections are **accepted** at `7c55183`. Investigating the suite
failure I had left as an unresolved risk established three defects, all
**inherited** — the runner and status code is byte-identical to accepted A84
`18666b3`, so none is a regression from the purge work. GPT-6 reproduced each
with fixture-only, owned-child probes retained under
`output/reviews/20260913-w0-r5/`.

1. **[P1] The orphan guard can authorize signalling the wrong process.**
   `runner.orphan_check()` accepts a live process when its observed command line
   names the run directory **OR the saved `run.json` argv does** — and the saved
   argv always does. So a reused pid passes identity, and `kill_orphan()` will
   hand that unrelated pid to `kill_process_group`. The docstring claims "a
   reused pid would fail that check"; the saved-argv fallback defeats it.
   Saved arguments describe the EXPECTED process and cannot identify whoever now
   occupies a pid. Require **live** evidence — the running process's own command
   line or working directory — covering the wrapper and MPI launch shapes the
   lane really uses (`-case <run_dir>` in argv, `cwd=run_dir`), refuse to signal
   on mismatched or unreadable evidence, and revalidate at the signal boundary.
   Keep stopping a verified owned orphan working. The regression must keep the
   saved argv naming the original run while the live identity differs, and
   assert the termination function is never called.
2. **[P2] A failed stop is persisted as a completed cancellation.**
   `kill_orphan()` writes `state: cancelled`, `finished_at` and
   `killed_as_orphan: true` even when `kill_process_group` returned False, and
   stamps cancelled progress too. `SolverRun.terminate()` has the same shape: it
   sets `self.state = "cancelled"` regardless of whether the process went.
   Record an attempt or a failure distinctly from a confirmed exit, and have
   `wt_status` reconcile live process evidence even when a stale cancellation
   record would otherwise bypass the check (`tools.py:2102` gates the orphan
   probe on the record already saying `running`). Status stays read-only.
3. **[P2] A test treats cancellation state as worker completion.**
   `wait_job()` returns as soon as the public job state is cancelled, which does
   not mean the worker has stopped writing. The orphan test then reuses the same
   module-scoped case and run directory, so the previous run's finalizer can
   overwrite `progress.json` with `cancelled` after the orphan fixture is in
   place — producing exactly the `cancelled` vs `orphan` failure I reported and
   could not explain. Give the orphan scenario its own case and run directory,
   wait on real finalization rather than public state, and keep a deterministic
   barrier regression: no longer sleeps, no retries, no weakened assertion.

Also required: prove the new tests fail on the old behaviour; run targeted
regressions before the canonical suite; preserve any failure rather than
disposing of it with a later pass; use only newly created fixture directories
and owned children, with intercepted signal functions for mismatched-pid cases,
and never probe termination against the owner's real solver or session. A source
change supersedes `77bbac85…`: recompute manifest, delta, artifact and resource
comparisons, and record any tool-response or token-budget change caused by
status telling the truth.

Accepted and to be carried forward as stated limits, not re-litigated: the
marker-tampering trust assumption (ownership tracking relies on the marker
staying intact; no `lsof` dependency required) and the adapter test-directory
leak.

### W0 round seven — finish the wind-tunnel corrections through the PUBLIC CALLERS

GPT-6 accepted the saved-argv removal, the orphan test's own case and the purge
work at `f20c9ee`, and then showed that a helper-level fix does not reach the
tools that call it. The caller-level state table is the acceptance criterion, so
another helper-only patch cannot leave the same failure downstream.

1. **[P1] Substring matching still authorises the wrong run.** Both live
   evidence paths use unrestricted `in`. `run_001` therefore matches its sibling
   `run_001-copy`, by cwd and by command line, and both reach the intercepted
   termination function. Rechecking the same wrong predicate twice does not make
   it right. Compare NORMALIZED paths at component boundaries: cwd must EQUAL
   the declared run directory, and command evidence must name that exact
   directory or a file beneath it. Handle the real wrapper and `mpirun` shapes
   and paths containing spaces. Keep unreadable evidence fail-closed and keep
   the recheck before signalling. Matrix: exact cwd, exact supported command
   argument, sibling prefix, `run_100` vs `run_1000`, mismatch, unreadable, and
   identity changing between decision and signal — **zero termination calls** on
   every negative. Positive fixtures must look like real launch arguments or a
   real cwd: **a path inside a source comment must not establish ownership**,
   which is what my own positive fixture relied on.
2. **[P2] The cancellation hook announces completion and frees capacity.**
   `tools.py:1825` ignores `r.terminate()`'s return, writes the run cancelled
   and releases the machine reservation unconditionally — so a surviving solver
   keeps burning cores while the ledger says the capacity is free, and status
   shows no failure. Keep the asynchronous-request/confirmed-exit distinction:
   a failed stop keeps its run state and its reservation, surfaces through
   status, and stays stoppable; capacity is released once the owned process has
   actually gone, with the worker's finalization as backstop. Integration test
   through `app.jobs.cancel()` and `wt_status`, then a successful retry.
3. **[P2] Stop and status callers turn uncertainty or failure into "gone".**
   `_Lane._stop()` raises `wt_no_orphan` "pid … gone / Nothing to stop" whenever
   `killed` is false, contradicting the helper's own persisted
   running/stop_failed record; and status reports `dead` for
   `identity_unknown`, when known metadata is not proof of exit. Distinguish
   confirmed exit, verified survivor after a failed stop, identity mismatch and
   identity unknown. Refuse unsafe signalling without calling an unidentified
   process dead, and give the public stop response an actionable next step.
   Also **clear or historicise `stop_failed` on a confirmed later success** —
   it currently persists through a successful retry.
4. **[P2] The worker wait returns as if it succeeded on timeout.**
   `wait_worker_done()` ignores `wait_until()`, which returns `None` on timeout.
   Make a timeout raise, naming the pending worker; add a negative timeout test
   beside the barrier one; and document the lifecycle point it supports — an
   empty registry is not a completion signal for work that has not registered.
5. **Evidence corrections.** The proposal explains **seventeen** changed files
   where the total is **nineteen** (`windtunnel/runner.py`, `windtunnel/tools.py`).
   The quoted wildcard command is not the 102-pass selection — record the six
   files that produced it, and the log path. And "no measurable token change" is
   wrong: the stale-cancelled/live-orphan status goes **19 → 59 estimated tokens
   (+40)**. Measure representative normal, failed-stop and unknown-identity
   responses against the predecessor, state serialization/estimator/composition,
   and keep the truthful status even though it costs more.

Rules unchanged: fresh fixture paths and owned children, termination intercepted
on every mismatched-identity case, never a kill against the owner's real
processes, both purge isolation layers kept. Focused regressions first with
their negatives proven failing on `f20c9ee`, then the canonical isolated suite
and both lint checks; preserve and explain failures rather than rerunning.
Rebuild the artifact from the corrected isolated source with the permanent
interpreter and recompute everything — `11bb1615…` must not be reused.

### W0 round eight — real argument boundaries, and a retry that truly retires

GPT-6 accepted the packaging identity, the failed-cancel reservation fix, the
orphan stop errors, the `unverified` status, the exact-cwd comparison and the
worker-wait timeout at `36453a0`. Three corrections remain.

1. **[P1] Flattened command text still authorises termination on this Mac.**
   `pid_argv` returns None here, so the flattened-string fallback IS the
   deployment path — and it accepts whitespace or `/` after the target, which
   three probes defeat: a path inside a `python -c` source comment, an argument
   `/…/run_001/../different-run`, and an argument `/…/run_001 copy`. Each reached
   the intercepted kill. Normalizing only the SEARCHED-FOR directory does not
   normalize a candidate containing `..`, and flattened text has lost the
   argument boundaries the decision needs.
   The fix is not merely conservative: **macOS does expose real argv**, via
   `sysctl KERN_PROCARGS2`, stdlib `ctypes` only and no new dependency —
   verified on this machine. So identification by command line now requires
   REAL argv tokens (Linux `/proc`, macOS sysctl), each candidate normalized
   before comparison; the flattened string is reporting only and never identity.
   No evidence at all stays `identity_unknown` and refuses the signal, and
   `run.json` argv is never restored as evidence. Regressions for all three
   shapes must exercise the fallback path and assert **zero** termination calls,
   keeping positive cover for exact cwd, genuine solver/wrapper arguments and
   paths with spaces.
2. **[P2] A successful IN-PROCESS retry keeps the failure.** §4g fixed the
   orphan branch only. `_stop()`'s in-process branch returns straight after
   `live.terminate()`, and `SolverRun.terminate` sets `stop_failed` on failure
   and never clears it on a later success, so the store's merge carries it
   through finalization into `wt_status`. Retire it on CONFIRMED exit, in memory
   and in every persisted record status reads, and make sure worker finalization
   cannot reintroduce it through a merge. Never clear before exit is confirmed.
   The integration test must run the whole public sequence — failed cancel →
   `wt_case action=stop` retry → confirmed exit → worker finished → persisted
   and public status and released capacity — keeping the failed-stop reservation
   assertion. Killing the child in teardown and checking the ledger proves
   nothing about the retry contract.
3. **Withdraw and re-measure the response-size evidence.** My `tokens.py`
   hand-wrote both sides and never called `wt_status`, so its "+30/+53" are not
   measurements, and my claim that GPT-6 had "modelled a shorter note" is
   unsupported — their probe called the real implementation. Re-measure by
   invoking the actual `_Lane.status` from each named source export under
   identical fixtures, state the serialization and estimator honestly, and label
   any hand-written example illustrative. Also reconcile "four new error codes"
   (the W0-wide LLM/VLM set) with the two new wind-tunnel codes, naming the
   baseline for each comparison.

Scope: the two wind-tunnel source files, their tests and fixtures, and the
proposal/receipt. Prove the new regressions fail on `36453a0`. Freeze, export
clean with `PYTHONPATH` pinned and bytecode off, run the six focused files plus
any new regression file, then the default suite and both lint checks; recompute
manifest, fingerprint, delta and artifact. Do not repeat the suite once green
without a new failure to investigate.

**Disposition (GPT-6, 2026-09-13): all three closed at `e6f9566`.** Identity now
comes from real argv on both platforms, the in-process retry retires its failure
in the persisted record, and the response table is re-measured (0 / +5 / +1 /
+13) with the hand-written one and the "modelled a shorter note" claim withdrawn.
The reviewer re-ran the six focused files (119 passed, 22 skipped) and both lint
checks, rehashed the source and artifact, and found no further blocking issue.
They additionally verified that with real argv AND cwd unavailable, flattened
text containing the target path still yields `identity_unknown` and no kill.

**Remaining W0 work is documentation and handoff only.** Three prose corrections
were required and are done — the withdrawn "order of magnitude" claim, the cwd
claim narrowed to differing symlink aliases, and `stop_recovered` described as
persisted recovery metadata rather than a status field (checking that also
corrected `identity`/`pid`/`note`, which `f20c9ee` already emitted). **No runtime
change was made to make the prose true**, and none is authorised: preserve
`e6f9566` and its verified MCPB, do not rebuild an unchanged package, and do not
repeat the suite to return a handoff. Any later runtime change is a new
candidate needing its own review. GPT-6 owns the packet from here; the version
cut and whether to release remain the owner's.

**Closeout (GPT-6, 2026-09-13) at documentation commit `b756a4b`: acceptance for
packet preparation stands, no product defect and no implementation work
outstanding.** Two final wording adjustments were required, both inaccuracies in
my own correction: stale-cancelled reconciliation was already present at
`f20c9ee` (only the `unverified` state and the in-process `stop_failed` are new
relative to it), and the two retry paths do not write identical records — an
in-process retry records recovery in memory and the case store, while an orphan
retry also retires prior failure flags in `run.json` and `progress.json`. Both
verified against the source and applied. **W0 correction work is closed.** What
remains is GPT-6's packet: client inspections, frozen identities, the two
deliveries, rollback and continuity. Installation, publication and both
actual-client receipts have not occurred.

**ACCEPTED (GPT-6, 2026-09-13).** The correction review is closed at
`e6f9566` / `df974f78…a90b7` / MCPB `59de72c6…0cbb6`. No further correction
script, implementation round, package rebuild or repeat test run is assigned for
this candidate. The source is tagged locally `w0-candidate-e6f9566` so it
survives branch movement in this shared checkout. **Acceptance is for packet
preparation only** — it authorises no installation and no publication, and both
actual-client receipts remain outstanding. Do not start further W0 work from
this script; a new runtime change would be a new candidate with its own review.

### W1 — chore budgets: MEASUREMENT ONLY (GPT-6, 2026-09-14)

Revision 1 of the W1 proposal was reviewed and **not accepted**: the cap
increases and the automatic dual-mode sweep are refused on the evidence given.
No runtime change is authorised by this addendum. W0 `e6f9566` stays installed
and untouched.

**What revision 1 got wrong, verified in the installed source, not taken on
report:**

1. **Shipped chores request thinking OFF and cannot request it ON.**
   `THINKING_ALLOWED` is `frozenset()` and `_run` gates on it, raising
   `llm_widening_unproven` for any chore that asks. `wire_thinking` returns
   `requested and resolved["thinking"]`, so a profile declaring the capability
   never enables it for a chore. My helper called `local_llm.complete_json`
   directly with `thinking=True` - a **laboratory** path production cannot
   take. Every consumption figure in revision 1 describes that path.
2. **The truncation counts were inferred, never observed.** Every helper call
   used `max_tokens=8000` and I compared consumption against the caps. No run
   at the actual cap exists. "rerank is truncated on 100% of inputs" is
   unsupported; "five thinking-on generations exceeded 256 tokens" is what the
   data shows.
3. **The helper did not reproduce the chore contracts.** It bypassed validators
   and changed prompts. `refine_extract` is not a fixed 500 - it sends
   `min(2 * max_tokens, 1200)`; `phrase_deviation` takes a list of facts, not
   prose.
4. **The usage accounting was wrong.** The callback overwrote on each attempt,
   so a retry's usage replaced the first instead of aggregating.
5. **`eng_adopt` writes `engines.json`.** It does not merely print a line -
   `save_measured` persists it, and one mode would overwrite another under the
   same engine key. `_ladder` also auto-includes eligible new rows, so adding
   an alias to attach a floor can add routing attempts.

**And the project had already measured this.** `_run`'s own comment records
thinking as 2.8-4.0x the cost, indistinguishable on the three chores with real
verifiers (8/8 either way) and WORSE on the calibration chore (6/6 -> 5/6):
*"Zero chores are measured to benefit, so zero chores get it by default."*
Revision 1 argued to widen a budget for a mode that was disabled after
measurement. I had read that function and still contradicted it.

**The bounded work this addendum authorises, and nothing more:**

- Pin the INSTALLED W0 source explicitly and assert the imported module's
  origin; record the runtime fingerprint, resolved route and effective request
  mode. Fix the reproduction command - revision 1's `INSTALLED_SRC` was
  undefined and its output pointed at an ephemeral scratch directory.
- Run the five rerank fixtures through the **real public chore** at production
  prompts, budgets and validation. Record requested mode and any backend
  reasoning counts; never infer backend compliance from a request flag.
  Distinguish strict `refine='local'` diagnostics from ordinary `auto`
  fallback, and a failed refinement from a failed user task.
- One structured record per fixture AND per attempt: identities, route,
  requested mode, literal and effective cap, finish reason, content presence,
  parse/validator/task verdicts, error code, retries, aggregated token counts,
  elapsed. Unreported fields marked unknown. Reasoning text stays out of the
  handoff.
- Expand only on a REPRODUCED failure, one factor at a time. Measure both
  quantisations or limit the recommendation to the one measured.
- Return revision 2 plus a receipt: corrected conclusion, per-fixture
  evidence, an accounting self-check, and either the smallest justified patch
  design or **"no production change justified"**. Do not modify
  `THINKING_ALLOWED`, profile defaults or the production gate to run any
  comparison. GPT-6 retains the coordination ledger.

Closing W1 as an investigation with no runtime change is an acceptable and
expected outcome.

### W1 owner direction — thinking ON (2026-09-14)

John subsequently directed: **"as an owner I need thinking on"**. This takes
precedence over the preceding measurement-only disposition and earlier W0/W1
adoption rules that require demonstrated benefit before permitting thinking.
Implement explicit owner-selected thinking ON for all eight local chores,
including triage. Measurements set the budget and verify behavior; they do not
reopen the owner's choice. Keep validation and trust controls intact.

Follow `docs/coordination/reports/TEE-20260914-W1-REVIEW/owner-thinking-on-script.md`
for candidate preparation, ON/OFF calibration, accounting, deadlines, validation
and the handoff. Prepare in isolation from Codex's live source. GPT-6 coordinates
the frozen upgrade packet and both actual-client receipts under protocol 1.0.1.
The earlier factual measurement corrections remain valid. The earlier instruction
to close W1 without implementing thinking ON is superseded.

John additionally requires the supporting engine row and a gate inspired by the
quantum threshold theorem. Scope explicitly confirmed: **keep primary thinking
ON; gate extra retries and supporting-engine escalation**. Add/reconcile the
actual 27b/27b4bit engine rows while preventing duplicate automatic routing.
Use measured, scoped error-detection/recovery and cost evidence for the gate;
the quantum theorem supplies no directly transferable LLM threshold. The revised
handoff above specifies registration versus qualification, retry entry points,
calibration, proposed numerical criteria and pass/fail/unmeasured outcomes.

### W1 candidate review — enforce the requested execution contract (2026-09-14)

GPT-6 independently reviewed f559187b8f6fe97b7ddb4fdb8272b2c0640906b2,
327-file payload ccb68328dc1f0e9fbff36c84d83b3d0e8f1ebae2fbd0e6ee80be026e6d40d774.
Disposition: changes required. Primary thinking ON and supporting engine rows
remain the requirement. 170 targeted tests passed, but public-path probes
reproduced six gaps:

1. Wire the threshold gate into corrective JSON generation and router support
   dispatch; both currently make second calls without consulting it.
2. Validate gate identity, finite values, types, timestamp, scope and resource
   budgets; wrong-route, NaN, future-dated and unknown-kind records currently pass.
3. Refuse unavailable explicit thinking=True before completion instead of silently
   sending OFF; preserve the explicit OFF control.
4. Enforce the total deadline through lock waiting, transport, result acceptance
   and cancellation, and verify status responsiveness.
5. Preserve per-profile ON/deadline policy in audition and implement calibration
   persistence that retains both modes and their actual scopes.
6. Carry request-scoped fallback reasons into actual client-visible outcomes.

Follow docs/coordination/reports/TEE-20260914-W1-CANDIDATE-REVIEW/response-to-claude.md
for reproductions, acceptance checks, receipt corrections and assigned files.
Continue in the isolated candidate worktree and mirror this execution amendment
there before editing; keep shared server/src/tee and the installed extension at
W0. Return one replacement candidate and exact identity. No resolver/committee
expansion or reconsideration of the owner's primary ON choice is requested.
GPT-6 retains shared-ledger and upgrade-packet ownership; Claude remains the
default builder for the eventual local MCPB after candidate acceptance.

### W1 candidate correction — the gate was never wired (GPT-6, 2026-09-14)

Candidate `f559187` reviewed. The mode setting, chore identities, the two
supporting rows outside the ladder and the unwired pre-validation correctors
are accepted. **Six findings, all reproduced here before accepting them.**

1. **[P1] `widening.gate` has ZERO production callers.** `grep` over the whole
   payload returns comments and `widening_ceiling` - a different, older
   function. The corrective JSON retry in `local_llm` and the support hop in
   `router` both issue extra inference without consulting it. My receipt
   called the gate "registered and inert pending calibration"; it was inert
   because DISCONNECTED, which is not the same claim and is the more serious
   one. A gate with 51 passing tests and no caller is a decoration.
2. **[P1] The gate passes invalid and out-of-scope evidence.** Reproduced:
   evidence naming a different endpoint and model -> `pass`; a NaN improvement
   bound -> `pass` (NaN fails both `<= 0` and `> 0`, so both guards let it
   through); a measurement dated a year in the future -> `pass`; an
   unrecognised `kind` -> `pass`; omitted budgets -> `pass`; a malformed
   `schema_version` -> raw `ValueError`. It checks that fields EXIST, not that
   they are valid or that they describe THIS request.
3. **[P1] Explicit `thinking=True` silently sends OFF** where the profile
   declares no capability, and returns a result, so the caller cannot tell.
   `_run` guards `thinking_unavailable` only when `thinking is None`. The one
   path I did not cover is the one that breaks the owner's requirement.
4. **[P1] The deadline does not bound what it claims.** The clock starts inside
   `complete_json`, after readiness work and after `profiles.REQUEST_LOCK`.
   Reproduced: a 30 ms deadline waited 165 ms for the lock and then completed;
   with real I/O a 30 ms deadline accepted a response after 91 ms.
5. **[P2] The owner policy is lost in calibration.** `audition._candidate_cfg`
   copies `thinking` and `json_mode` and discards `chore_thinking` and
   `chore_deadline_s`, turning production ON/45 s into audition unset/none.
   And `rows[engine] = row` still cannot hold ON and OFF for one engine.
6. **[P2] Auto fallback is silent.** Ordinary completion errors return `None`
   with no reason recorded, and `LAST_DEGRADE` is a process-global dict no
   production caller reads.

Also: the receipt names two identities - section 1 `f559187`/`ccb68328`,
section 10 still `20bbe1c0`/`c3d88a9d`. One current identity throughout, which
is the rule I have been applying to everyone else.

And a better diagnosis than mine of the one failing test: `adapter_required`
because Blender AND Unreal both accept the cube batch. Not merely
"environment-dependent". Isolate it; do not weaken the assertion to get green.

**Scope: fix the execution contract. Do not reopen thinking ON. Keep the
disabled correctors disabled. No resolver, no further committee.** Return one
replacement candidate, a full manifest, the tested identity, a disposition of
all six, and the ON activation settings, deadline policy and calibration
migration/rollback for both clients.
