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

## 10. Standing rules (all phases)

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
