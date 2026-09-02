I have everything needed. Report follows.

---

# TASK E1 — Integration map for a new TEE adapter lane (seamkiln as template)

## 1. `server/src/tee/app.py` — always-loaded registration of adapter tools

- `TeeApp.__init__` ends with a fixed block of `register_*` calls: `server/src/tee/app.py:189-211`.
  - `register_session_tools(self)` :193, `register_trust_tools(self)` :194, `register_fleet_tools(self)` :201, `register_board_tools(self)` :202.
  - **The lane hook**: `server/src/tee/app.py:204-211`
    ```python
    # A53 P4: seamkiln's garment lane. Registration is metadata only -
    # seamkiln itself is never imported until a tool is called, so an
    # environment without it costs nothing at startup and every entry
    # point refuses with the install command rather than an ImportError
    # halfway through a batch.
    from tee.adapters.seamkiln.tools import register_seamkiln_tools

    register_seamkiln_tools(self)
    ```
  - Note: this is UNCONDITIONAL — it runs for every adapter (`--adapter fake` too). The `sk_*` virtual tools exist in the registry even when seamkiln is absent; calling one refuses. Confirmed as designed behaviour in `docs/PROGRESS.md:9242-9246`.
- **"metadata only, never import the kernel until called" is enforced in three places, not one:**
  1. `server/src/tee/adapters/seamkiln/tools.py:1-41` — the module imports only `typing`, `TeeError`, `VirtualTool`. Every handler is a closure defined inside `register_seamkiln_tools` (`tools.py:43`) whose **first statement is `_need()`** (`tools.py:36-40`), which does `import seamkiln` and raises `TeeError("seamkiln_unavailable", INSTALL_HINT, fix=INSTALL_HINT)`. All `from seamkiln...` imports are *inside* the handler bodies (e.g. `tools.py:47`, `:73`, `:106`).
  2. `server/src/tee/adapters/seamkiln/adapter.py:37-43` (`_need_seamkiln()`), plus lazy session construction at `adapter.py:52` (`self._session = None  # built lazily`) and `adapter.py:55-63` (`@property session` imports `seamkiln.session.Session` only on first use). `info()` (`adapter.py:96-121`) reports `version="absent", connected=False` instead of raising.
  3. `tools.py:23-34` `_adapter(app)` finds the live `SeamkilnAdapter` by `isinstance` scan of `app.adapters` and refuses with `seamkiln_not_served` + `Start with 'tee serve --adapter seamkiln'` if none is attached.
- Adapter resolution helpers a lane inherits for free: `TeeApp.resolve_adapter` `app.py:238-252` (omitted `adapter=` resolves when exactly one is configured), `TeeApp.adapter` `app.py:254-266` (calls `adapter.probe()`, raises `AdapterUnavailable`).
- Extras bookkeeping happens before registration: `app.py:122-136` (`_extras.remember(_state, today=...)`, `_probe.bind_state_dir(_state)`), wrapped in a bare `except Exception: pass` so "bookkeeping must never stop the server booting".

## 2. `server/src/tee/cli.py` — builder, `--adapter`, `_attach_*` chain

- `_build_seamkiln_app`: `server/src/tee/cli.py:47-57`
  ```python
  def _build_seamkiln_app(project: str, allow_code_exec: bool):
      """seamkiln needs no bridge and no running application - the garment
      kernel is a library, so the adapter is live the moment it is built."""
      from tee.adapters.seamkiln import SeamkilnAdapter
      from tee.app import TeeApp

      adapter = SeamkilnAdapter(project)
      return TeeApp(
          {"seamkiln": adapter}, project_root=Path(project), allow_code_exec=allow_code_exec
      )
  ```
  Contrast the wired lanes: `_build_blender_app` :20-32 and `_build_unreal_app` :35-44 also call `register_<name>_tools(app, adapter)`; `_build_freecad_app` :178-189; `_build_godot_app` :59-68 additionally calls `adapter.ensure_bridge(...)`. seamkiln registers **nothing** here because `app.py:211` already did it.
- **There is no argparse `choices=`.** `--adapter` is a free-form string: `cli.py:332-334`
  ```python
  serve.add_argument(
      "--adapter", default="fake", help="adapter to serve (fake|blender|unreal|godot|seamkiln)"
  )
  ```
  Dispatch is an if/elif chain in `cmd_serve`: `cli.py:232-253` (`fake` :232, `blender` :234, `unreal` :238, `freecad` :242, `seamkiln` :244, `godot` :246), with an `else` that prints to stderr and returns 2: `cli.py:249-252` — `"adapter '…' is not recognised; available: fake, blender, unreal, freecad, godot, seamkiln"`. **Three string lists must be updated for a new lane**: the `--adapter` help (:333), the error message (:250), and the docstring of `serve_command`/`emit_config` path in doctor (`doctor.py:594-630`, which takes `adapter: str = "blender"`).
- The `_attach_*` chain, run for every adapter after the build: `cli.py:255-269` — `_attach_extract` (:71, with `with_handoff=args.adapter == "blender"`), `_attach_assets` (:109), `_attach_capture` (:101), `_attach_pipeline` (:86), `_attach_pins` (:117, no-ops unless `"unreal" in app.adapters` — `cli.py:120`), `_attach_design` (:155), `_attach_senses` (:144), `_attach_pdf` (:134), `_attach_purge` (:127), `_attach_physical` (:162), `_attach_uefn` (:170), `_attach_kb` (:191), `_attach_llm` (:199), `_attach_web` (:207), `_attach_gateway` (:215).
  A new lane needs **no** `_attach_*` of its own if it follows seamkiln (registration in `app.py`); it needs one only if the lane must be conditional on config/project state (the `_attach_pins` pattern).
- Advisory single-instance PID notice `cli.py:272-297`; `server.run()` on stdio + `app.shutdown()` `cli.py:270-284`.

## 3. `server/src/tee/kernel/trust.py` — the full trust table

File: 690 lines. Structure, in order:

| element | lines | content |
|---|---|---|
| `READ_TIER` | :46-70 | `read-scene, read-state, read-session, read-kb, read-extract, read-assets, read-design, read-uefn, read-compute, read-medimg, read-bi` — open by default, fails OPEN when config is broken |
| `SIDE_EFFECTING` | :72-97 | `fetch-web, write-scene, write-state, write-artifacts, write-config, write-policy, call-engine, call-paid-engine, switch-engine, front-backend, run-declared-step, run-adhoc, exec-code, call-service, place-order` |
| `CAPABILITIES` | :99 | `READ_TIER | SIDE_EFFECTING` |
| `NEVER_GRANTABLE` | :106 | `frozenset({"place-order"})` — a config line naming it cannot parse |
| `HIGH_RISK` | :112-121 | `run-adhoc, exec-code, write-config, write-policy, call-paid-engine, place-order` |
| `TAINT_ENFORCED` | :131 | `HIGH_RISK | {"run-declared-step", "fetch-web"}` |
| `TAINT_SOURCES` | :137-147 | `fetch-web, front-backend, read-kb, read-extract, call-paid-engine, call-service, read-bi` |
| `CALLER_CLASSES` | :151-153 | `live-turn, chore, job, scheduled, gateway-fronted, content-derived` |
| `_FAMILY` (prefix rules) | :164-192 | tuple of `(prefix, capability)` |
| `_EXPLICIT` (per-tool) | :193-363 | dict, ~180 entries; explicit wins over family |
| `capability_for()` | :365-382 | |
| `PROFILES` / `profile_covering` | :403-436 | `readonly`, `build`, `workstation`, `workstation+paid` |
| `Grants` / `from_config` | :439-511 | |
| `GrantsWatcher` | :514-551 | mtime-based hot reload, one `stat()` per decision |
| `BASELINE` | :553-563 | `READ_TIER + write-scene, write-state, write-artifacts, call-engine, switch-engine, fetch-web` |
| `Decision` | :566-604 | `raise_if_denied`, `fix()` |
| `check()` | :607-690 | the one decision |

**`_FAMILY` in full (`trust.py:164-192`):**
```python
("kb_", "read-kb"), ("ex_", "read-extract"), ("as_", "read-assets"),
("gd_", "read-design"),
("sk_", "read-scene"),   # A53: seamkiln garment queries      <- line 169
("uefn_", "read-uefn"), ("sim_", "write-scene"), ("capture_", "call-engine"),
("llm_", "call-engine"), ("plaus_", "read-scene"), ("mat_", "read-scene"),
("solve_", "read-compute"), ("quant_", "read-compute"),
("med_", "read-medimg"), ("bi_", "read-bi"), ("svc_", "call-service"),
```

**The `cad_` comment, verbatim (`trust.py:179-182`):**
```
    # DELIBERATELY NO ("cad_", ...) ENTRY either. A cad tool that BUILDS
    # writes a file; one that MEASURES does not. A single prefix default
    # would have given the writer the open read tier. Tabled individually
    # below, same lesson as trade_.
```
Immediately followed by (`trust.py:183-188`):
```
    # DELIBERATELY NO ("trade_", ...) ENTRY. A prefix default would let a
    # future tool called trade_place_order inherit the OPEN read tier just
    # by being named. Every trading tool is tabled INDIVIDUALLY in
    # _EXPLICIT, so an untabled trade_* name is a startup error - which is
    # the point: the kernel refuses to boot rather than quietly permit.
```
The existing `cad_*` explicit entries are `trust.py:292-295`:
```python
# A45 P2e: CAD. Build writes an artifact; measure and probe do not.
"cad_scad_build": "write-artifacts",
"cad_measure": "read-compute",
"cad_probe": "read-compute",
```
**This is the single most load-bearing constraint for a new mechanical-CAD lane**: a `cad_`-prefixed lane gets *no* family default; every new tool must be added to `_EXPLICIT` by hand or the server will not boot. A differently-prefixed lane may add a family rule, but the same "a builder writes a file" argument applies.

seamkiln's explicit exceptions to its own `sk_` family default (`trust.py:248-253`):
```python
"sk_plot": "write-artifacts",
"sk_techpack": "write-artifacts",
"sk_materials": "write-artifacts",  # its export/import actions touch files
"sk_interchange": "write-artifacts",
"sk_handoff": "write-artifacts",   # A65: writes a bundle for another application
```
(The other nine `sk_*` tools ride the `read-scene` family default.)

**`capability_for()` on an untabled tool (`trust.py:365-382`):** explicit lookup first, then prefix scan, else
```python
raise TeeError(
    "trust_untabled_tool",
    f"Tool '{tool_name}' has no capability in the trust table.",
    fix="Add it to _EXPLICIT (or a family) in kernel/trust.py - the "
    "table is the single review surface; an untabled tool cannot ship.",
)
```
This is raised at **registration**, not at call time: `ToolRegistry.register` `server/src/tee/kernel/registry.py:86-91` resolves `tool.capability = trust.capability_for(tool.name)` when the VirtualTool leaves it `None`, so an untabled tool is a **startup crash**. `register` also rejects non-object schemas (:97) and `required` keys absent from `properties` (:100-105). The runtime check is `ToolRegistry._trust` `registry.py:216-226` invoked from `ToolRegistry.call` `registry.py:196-214`, which also applies `TAINT_SOURCES` after the handler returns (`registry.py:212-213`).

## 4. `server/src/tee/kernel/extras.py` — extras declaration/doctoring, and why `cad` is exempt

- Module docstring `extras.py:1-21` is the "upgrade wipes extras" statement of record: Claude Desktop provisions with `uv sync`, "**every upgrade deletes them**. Measured three times running: 0.9.0 -> 0.10.0, 0.11.0, and 0.12.0, each dropping the venv from ~1.1 GB back to 34 MB."
- `STATE_FILE = "extras-seen.json"` :29 (lives at `<project>/.tee/extras-seen.json`).
- `WITNESS` :34-42 — group → **one leaf import** that proves the group runs, "not the distribution name": `solve→highspy, quant→skfolio, medimg→pydicom, extract→ezdxf, pdf→fpdf, assets→imagehash, cad→cadquery`.
- **The `cad` exemption, verbatim (`extras.py:44-46`):**
  ```python
  # `cad` moved to a sidecar in A46 P1b and is NOT expected in TEE's own venv,
  # so its absence is normal and must never be reported as a loss.
  NOT_IN_TEE_VENV = frozenset({"cad"})
  ```
  `present()` :53-65 skips any group in `NOT_IN_TEE_VENV` before `find_spec`, so `cad` is never recorded and therefore never appears in `lost()`.
- `remember()` :80-96 (never forgets a group on its own — the last-seen date is the evidence), `lost()` :98-103, `loss_note()` :105-114 (the sentence that turns "never installed" into "an upgrade ate it").
- Consumer: `server/src/tee/fleet/probe.py:63-86` `need(module, group, what=)` prefixes the `TeeError` with `loss_note(...)`; its `EXTRAS` table `probe.py:28-49` has the `cad` row: `("cad", "CadQuery (OpenSCAD is a separate app: brew install --cask openscad)", "uv pip install 'tee-engine[cad]'")`. `probe.have()` :88+ is a non-importing presence check. `bind_state_dir` :57-59 is called from `app.py:134`.
- The sidecar interpreter path is hardcoded: `server/src/tee/fleet/cad.py:206` — `SIDECAR_PY = Path.home() / "TEE" / ".tee" / "sidecars" / "cad" / "bin" / "python"`, with an out-of-process worker `server/src/tee/fleet/_cad_worker.py`. **A new OCCT lane that wants in-venv cadquery diverges from this**: cadquery is presently reached via subprocess sidecar, not imported into TEE's venv.
- Doctor surface: `check_extras()` `server/src/tee/doctor.py:449-481`, whose OK line appends `" (cad lives in its own sidecar by design)"` (:480) and whose fix uses `sys.executable` verbatim (:470-474).

## 5. `kernel/scene_cache.py` + `kernel/checkpoints.py`

**`scene_cache.py` (174 lines).** What `list_entities()` feeds:
- `SceneCache.resync(adapter)` :36-42 builds `entities = {e.id: e for e in adapter.list_entities()}`, bumps `epoch` **and** `revision`, clears `_log`. Called by `TeeApp.warm()` `app.py:274-281` on first contact (cold `(0,0)` stamps would yield silently-wrong deltas) and by `TeeApp.rollback` `app.py:346`.
- `apply_diff(diff, upserts, source="agent")` :44-54 consumes `Diff.upserts` — the created/modified `Entity` objects — writing them into `entities`, popping `diff.deleted`, `revision += 1`, appending a `_LogEntry`. `_LOG_LIMIT = 200` :17.
- **`Diff.upserts` is kernel-internal and never serialized** — `kernel/adapter.py:47-52` docstring; `Diff.to_payload()` :64-75 emits only `created/modified/deleted/details/notes`. So an adapter that appends to `created` without a matching `upserts` entry leaves the cache blind: seamkiln does both together (`adapters/seamkiln/adapter.py:_record`, e.g. :456-460, :467-473).
- `Entity` `kernel/adapter.py:24-44`: `id, name, kind, parent, summary`; **"`summary` holds small scalar facts only (bounds, counts, kind-specific flags) - never geometry."** `concise()` :33-38 (id/name/kind/parent), `detailed()` :40-44 (+summary).
- seamkiln's `list_entities()` `adapters/seamkiln/adapter.py:123-206` is the model to copy: panels (area, perimeter, edge/mark/internal counts, bbox, allowance), seams (a/b/gather/mismatch), one `garment` roll-up, plus zippers/buttons/locks/body. The in-code lesson at :186-189: *"A55-A58 state was invisible here … Everything a batch can change is an entity, or a diff cannot name it."*
- **`tee_diff` and `(epoch, revision)`**: `diff_since(epoch, revision)` :67-95 returns `resync_required` (never a wrong delta) in three cases — epoch mismatch ("scene history was rewritten (rollback/reload)"), `revision > self.revision`, or the log window pruned ("diff history pruned; too far behind"). Otherwise `_merge_log` :134-174 folds the window with net semantics (created-then-deleted cancels; deleted-then-recreated collapses to modified) and stamps the payload; `user_edits: True` is added when any log entry has `source == "user"`. `stamp()` :64-65 returns `{"epoch", "revision"}`. Wire tool: `server.py:312-320` `tee_diff(epoch, revision, adapter=None)`.
- `summary()` :97-129 does filter (`kind`, `name_contains`) → page (`limit`/`offset`) → per-kind counts → `truncated` hint naming the narrowing parameter.

**`checkpoints.py` (113 lines).** `_KEEP = 20` per adapter :19. `CheckpointManager.create(adapter, label, revision)` :46-63 calls `adapter.snapshot(label)` and stores it as an opaque payload; eviction beyond `_KEEP` calls `_discard` :105-113, which invokes the adapter's **optional** `discard_snapshot(payload)` hook if present. `rollback(adapter, ref)` :65-87 matches by id **or newest with that label**, calls `adapter.restore(cp.payload)`, and drops every later checkpoint.

**Snapshot payload constraints** (`kernel/adapter.py:113-114`: *"Opaque checkpoint payload (kept small or spilled to disk by the adapter)"*): seamkiln's `snapshot()` `adapters/seamkiln/adapter.py:213-234` writes `{"script": session.script(), "fingerprint": session.fingerprint()}` to `<project>/.tee/seamkiln/<label>-<epoch>-<ms>.json` and **returns only `{label, path, epoch, commands}`** — the payload held in memory is four scalars. `restore()` :236-256 **replays the command script** (`Session.replay(data["script"])`) rather than deserialising state — *"A checkpoint that rebuilds by running the same commands cannot restore a state the commands could not produce, which is a stronger guarantee than any schema"* — and raises `seamkiln_checkpoint_missing` naming `tee_purge` if the file is gone.

Batch/checkpoint orchestration a lane inherits: `TeeApp.run_batch` `app.py:285-340` — auto checkpoint `auto:batch-r{rev+1}` (:301-302), `adapter.execute(ops)` inside try, on any exception `adapter.restore(cp.payload)` for atomicity with a `fix` naming the outcome (:307-327), then `cache.apply_diff(diff, diff.upserts)` (:333) and payload `{"ok", epoch, revision, "checkpoint", "applied", **diff.to_payload()}` (:334-339). `checkpoint=False` is the script-lane path (:293-299).

## 6. `kernel/jobs.py` — the `tee_job` submit pattern

- `JobManager.submit(label, fn, *, qos="standard", engine=None) -> str` `jobs.py:107-165`. Returns a job id `job{N}` immediately. Two admission gates run under the lock: K1 ledger admission `machine.may_admit(engine)` → `TeeError("job_refused_admission", ...)` (:118-127) and K3 backpressure for `qos` rank ≥ 2 (`batch`/`maintenance`) capped at `_max_pending_low = 8` → `TeeError("job_backpressure", ...)` (:128-138). Both only when `qos` is enabled.
- `QOS_RANK = {"interactive": 0, "standard": 1, "batch": 2, "maintenance": 3}` :26; `DEFAULT_AGING_S = 120.0` :27. `configure(machine=, qos=, aging_s=, max_pending_low=)` :80-105, wired from `app.py:173-178` off `[scheduler]` config (`qos` default `True`, `shadow` default `True`).
- Taint propagation across the thread hop `jobs.py:150-160`: `trustctx.taint()` is snapshotted and re-installed in the worker with the caller **downgraded** to `"job"` (or `"scheduled"` when `qos == "maintenance"`), "because the human who submitted this is not present while it runs".
- Workers are **daemon threads** (2 by default, `JobManager(workers=2, keep_finished=50)` :57), never a ThreadPoolExecutor: "a stuck DCC call must never block interpreter exit" (:6-9, `shutdown()` :270-274 sets `_stopping` and does **not** join).
- Polling: `status(job_id)` :242-253 → `_Job.to_payload()` :43-55 = `{job, label, state}` + `qos` only when non-default + `elapsed_s` while queued/running + `result`/`error`. `cancel(job_id)` :254-265 (queued = skipped; running = cooperative, result dropped). Wire tool: `server.py:343-350` `tee_job(job_id, cancel=False)`.
- **No timeout is enforced by the manager** — the timeout lives in the submitted callable. Canonical call site: `server/src/tee/physical/tools.py:153-161`
  ```python
  job = app.jobs.submit(
      "sim_fluid",
      lambda: physics_mod.run_program(app, adapter_name, program, timeout=3600),
  )
  return {"job": job, "note": "poll with tee_job; bake is synchronous in Blender - the bridge is busy until it finishes"}
  ```
  Other call sites: `capture/tools.py:390`, `:439`; `adapters/blender/tools.py:182`; `extract/tools.py:179`, `:428`; `pipeline/tools.py:398`; `llm/profiles.py:512`.
- Completion is recorded to the shadow trace `jobs.py:227-233` (`shadow.TaskDescriptor(id, kind="job", qos, engine)` + `{outcome, wall_s}`). Finished jobs pruned past `keep_finished` `_prune_locked` :276-283.
- **seamkiln uses none of this** — its drape runs synchronously inside `tee_batch`. A CAD lane with long solves/meshing should submit instead.

## 7. `kernel/budget.py` — response budgeting/truncation

- `DEFAULT_MAX_TOKENS = 20_000` :19, `CHARS_PER_TOKEN = 3.5` :20 (matches the compact-JSON wire format), `_SCALAR_STR_LIMIT = 300` :21.
- `estimate_tokens(obj)` :26-33 — `len(compact json)/3.5`, floor 1.
- `columnarize(payload, min_rows=20, min_shared=0.6)` :35-80 — rewrites top-level list-of-dicts to `{"cols": [...], "rows": [[...]]}` with a top-level `"columnar"` marker; bails when `len(set().union(*value)) > 2*len(cols)` (too heterogeneous). Measured 42% smaller at 100 homogeneous rows.
- `enforce_budget(payload, *, max_tokens, narrow_hint)` :83-131 — halves the largest collection field (`_largest_collection` :133-145 scores by serialized cost, list **or** dict) up to 64 times, accumulating one cumulative `"truncated"` notice naming what was dropped plus the narrowing parameter; if still over, falls back to a **scalar skeleton** (:118-131) that preserves strings ≤300 chars, numbers, bools and `None` — "checkpoint ids and scene stamps must survive".
- Applied uniformly at the MCP boundary by the `_tool` decorator `server/src/tee/server.py:151-152`: `result = columnarize(result); result = enforce_budget(result)`, then `json.dumps(..., separators=(",",":"))` :161-163. Per-tool overrides exist (`tee_status` recap at `max_tokens=500`, `server.py:238-241`; `tee_media` budget clamped to `[50, 4784]`, `server.py:386`).
- Adjacent lint guard: `server/tests/test_server_lint.py:20` `MAX_DESCRIPTION_BYTES = 2_048` per tool, and a total-definition-token budget assertion at :70-75.

## 8. `kernel/script.py` — what `tee_script` can do against an adapter

- Budgets: `MAX_CALLS = 200` :27, `MAX_STEPS = 10_000` :28, `MAX_SECONDS = 120.0` :29, `MAX_SOURCE_CHARS = 20_000` :30.
- `validate_script` :136+ AST-whitelists (`_ALLOWED_STMT` :32-41 — no `while`, no `def`/`lambda`; `_ALLOWED_EXPR` :42-88 — no imports, **no attribute access**, no underscore names) and the code is **interpreted by a tree-walker, never `exec()`'d** (:11-16). `_SAFE_BUILTINS` :106+ (`len, min, max, sum, abs, round, sorted, range, enumerate, …`).
- `run_script(app, code, default_adapter)` :408-497 exposes exactly **five** functions (`env` :465-472): `call(name, args)` :437-440 → `app.registry.call` (so **every virtual tool of the lane, including `sk_*`, is reachable**); `batch(ops, adapter, label)` :442-447 → `app.run_batch(..., checkpoint=adapter not in touched)`; `summary(adapter, **kwargs)` :449-452; `detail(entity_id, adapter)` :454-459; `diff(epoch, revision, adapter)` :461-463.
- Atomicity: `_guard(adapter_name)` :425-435 takes one `auto:script` checkpoint per adapter on first touch (skipped if `adapter.probe()` is False); any uncaught error triggers `_rollback_all` :499-514, whose failure path calls `cache.invalidate()` and tells the caller to `run tee_scene_summary(refresh=true)`.
- Return payload :488-497 — only `result`, `calls_made`, `steps`, plus `checkpoints`/`scene` stamps for touched adapters. Intermediate tool outputs never leave the server.
- `tee_script` carries capability `exec-code` in the trust table (`trust.py:236`) but the docstring is explicit it "adds no capability, it removes round-trips (and is therefore not gated by allow_code_exec)" (:6-9). Wire handler `server.py:397-419` also attaches an LLM `repair` draft on refusal.
- **Implication for a new lane**: `probe()` must be cheap and non-hanging (`kernel/adapter.py:104-106`), because the script lane calls it before checkpointing. seamkiln's `probe()` `adapters/seamkiln/adapter.py:114-119` is just `import seamkiln`.

## 9. `server/src/tee/doctor.py` — what a lane adds to doctor

- `run_checks(bridge_port)` `doctor.py:562-578` is a flat list of 14 checks: `check_python, check_uv, check_blender_binary, check_blender_bridge, check_bpy_wheel_abi, check_unreal, check_voxkiln, check_kb, check_web, check_state, check_extras, check_senses, check_rooted, check_llm`.
- **seamkiln added NOTHING to doctor** — `grep -n "seamkiln" server/src/tee/doctor.py` returns zero hits. That is a gap, not a pattern: the sibling self-contained package voxkiln DID add one.
- The precedent to copy is `check_voxkiln()` `doctor.py:254-299`: try-import the package (`ImportError` → `Check(name, "warn", "not installed - …", fix="pip install …(see docs/setup-voxkiln.md)")`), then call the package's **own** `doctor()` and translate its report into warn/ok with a copy-pasteable `fix` — backend present? weights cached? gated weights accessible? A CAD lane's equivalent questions: is OCCT importable, is it the sidecar or the venv, which kernel version.
- `Check` is rendered by `render(checks)` :633+ (`OK/WARN/FAIL`, non-zero exit only for `status == "fail" and required`), and JSON-emitted via `cmd_doctor` `cli.py:299-313`.
- `emit_config(client, *, adapter="blender", port=...)` :612-630 and `serve_command(*, adapter="blender", port=...)` :594-609 build the client config line; `_dev_checkout()` :588-591 picks `uv --directory … run tee` vs the installed `tee` binary. A lane that wants `tee doctor --emit claude-desktop` to produce its serve line must thread the adapter name through here (nothing currently passes a non-default `adapter=` from the CLI).

## 10. `packaging/mcpb_manifest.json` + `server/Makefile` — bundling, and the trap

- `packaging/mcpb_manifest.json`: `manifest_version "0.4"`, `version "0.19.0"`, `server.type "uv"`, `entry_point "src/tee/cli.py"`, and `mcp_config.args` hardcodes `["run","--directory","${__dirname}","--no-dev","tee","serve","--adapter","blender","--project","${user_config.project_root}"]`. The `tools` array lists **exactly the 17 always-loaded tools** by name+description — a new always-loaded tool would have to be added here (a virtual-tool lane must not touch it). `keywords` and `user_config.project_root` (default `${HOME}/TEE`) also live here. **`grep seamkiln packaging/` → nothing.**
- `server/Makefile`: `dist:` :10-19 = `uv build` + Blender extension build + UE plugin zip + `$(MAKE) mcpb`. `mcpb:` :22-46 copies **only** `../packaging/mcpb_manifest.json → manifest.json`, `icon.png`, `pyproject.toml`, `uv.lock`, `../README.md`, and `cp -R src build/mcpb/src` (:33), then zips to `dist/tee-engine-$(TEE_SERVER_VERSION).mcpb` (:36). `TEE_SERVER_VERSION ?= 0.19.0` :8. Line :26-32 appends `[tool.uv] default-groups = []` to the bundle's pyproject to drop the dev group (+58 MB measured).
- **seamkiln is NOT bundled.** Only `server/src` ships; the repo-root `seamkiln/` package is not copied and is not a declared dependency (`grep seamkiln server/pyproject.toml` → nothing). Install line: `docs/seamkiln-lane.md:11` —
  ```bash
  uv pip install -e seamkiln            # the kernel
  tee serve --adapter seamkiln --project ~/patterns
  ```
  Consequence, recorded at `docs/PROGRESS.md:9242-9246`: `sk_blocks` called from the installed bundle **refuses** ("seamkiln absent, as expected") — "the designed behaviour, not a defect".
- **The "upgrade wipes extras" trap** is printed by the `mcpb` target itself, `server/Makefile:38-46`:
  > `REMINDER: installing this wipes the fleet extras from the Desktop venv - Desktop provisions with 'uv sync', which rebuilds from the lock and drops anything installed on top.`
  followed by the restore command against `~/Library/Application Support/Claude/Claude Extensions/local.mcpb.interaeronav.token-efficiency-engine/.venv/bin/python` for `medimg quant solve extract pdf`, and :46 — `"See docs/setup-fleet.md. 'cad' is excluded on purpose (sidecar)."`
  A `-e seamkiln`-style editable install is wiped by the same mechanism and is **not** covered by `extras.py` (which only tracks `WITNESS` groups) — a new lane installed the same way inherits the same silent loss with no `loss_note`.
- The `cad` extra itself: `server/pyproject.toml:97-104` — `cad = ["cadquery>=2.8.0"]`, with the comment "~1.3 GB installed and ~140 s on FIRST import while it compiles bytecode; 1.1 s warm. OpenSCAD is NOT here: it is GPL-2.0-or-later and is run as a separate program … never linked."

## 11. `benchmarks/run_benchmarks.py` — adding a scenario, landing in RESULTS.md

- `SCENARIOS = [...]` `benchmarks/run_benchmarks.py:316-321` is **only** the four Blender-bridge scenarios driven by the naive-vs-tee loop at :1748-1787. A lane scenario is **not** added there.
- The actual pattern (four edits):
  1. `def run_<lane>_scenario() -> dict | None` — try/except `ImportError` returning `None` with a printed skip (seamkiln: :1231-1302; follow-up :1305+). Body: `TeeApp({"<lane>": <Lane>Adapter(root)}, project_root=root)` :1252-1254, run the TEE arm (`adapter.execute(batch)` + `app.registry.call("sk_fit", {})`), build the naive arm from raw geometry (`pattern_dump` / `mesh_dump` :1274-1281), `estimate_tokens` both, `app.shutdown()`, return a dict of ints/floats.
  2. Call it through `_safe`: `:1800-1801` `seamkiln_row = _safe(run_seamkiln_scenario)`. `_safe(fn)` :1815-1826 — *"A live-editor scenario must never take the whole benchmark down"* — catches every `Exception`, prints `f"{fn.__name__}: skipped (…)"`, returns `None`, and always `_stage(...)`-times. (`_timed` :1809-1813 is the non-catching variant used for the always-available scenarios.)
  3. Thread the row into `write_results(...)` :1802-1804 and its signature :1869-1872 (keyword-only, defaulting to `None`).
  4. Emit a section: `:2121-2126` `if seamkiln_row is not None: lines += _seamkiln_section(seamkiln_row)`, with `_seamkiln_section` :2196-2219 and `_seamkiln_followup_section` :2222-2246 returning markdown line lists (`| arm | tokens | calls |` table + a saved-% row). `_carry_forward(header)` :1828+ preserves a previously-measured section when the scenario skips.
- **The surface scenario that asserts 17 tools**: `run_surface_scenario()` :738-828. It builds a `TeeApp({"fake": FakeAdapter()})` twice — bare (:773-775) and with every module registered (`register_extract_tools`, `register_asset_tools`, `register_design_tools`, `register_physical_tools`, `register_pin_tools`, `register_uefn_tools`, `register_kb_tools`, :777-785) — lists tools through a real MCP client (`listed(app)` :763-771 with `wire_kw = dict(by_alias=True, mode="json", exclude_none=True)` :760, because a bare `model_dump()` counts ~490 tokens of null padding no client sees), and returns `{n_tools, wire_tokens, model_dump_tokens, added_by_modules, n_virtual_tools, flat_server_tokens, reach_one_tool, saving}` :805-814. It **measures** rather than asserts; the hard assertions live in tests:
  - `server/tests/test_server_lint.py:82` `EXPECTED_TOOL_COUNT = 17` and :85-88 `assert len(tools) == EXPECTED_TOOL_COUNT`; plus `test_tool_names_are_prefixed_and_stable` :77-80 (every always-loaded name starts `tee_`).
  - `server/tests/test_seamkiln_adapter.py:169-178` `test_the_surface_does_not_move` — `assert len(_DESC) == 17`, `assert not any(name.startswith("sk_") for name in _DESC)`, and the `sk_*` set is a subset of `app.registry.names()`; repeated at :248-251.
  - `_DESC` itself is `server/src/tee/server.py:30` (the 17-entry description dict).
- Note `benchmarks/run_benchmarks.py` **is** linted: `server/Makefile:53` `uv run ruff check src tests ../benchmarks` (added after SI-B20), and `# noqa: E501` lines in embedded source strings must not be reflowed by hand.

## 12. The commit that added the seamkiln adapter

`git log --oneline -- server/src/tee/adapters/seamkiln | tail -3` →
```
43ef554 A53 P6: evidence, interop, ship - and A53 is complete
46ae829 A53 P5: the GUI is a client of the core, and the script is not an export
c33432e A53 P4: a whole garment product joins TEE, and the surface does not move
```
First commit: **`c33432eb5f3b6bf89487a27dfec482073fe55c5f`**, 2026-09-01, "A53 P4: a whole garment product joins TEE, and the surface does not move" — headline: *"17 always-loaded tools / 2033 tok before A53; 17 tools / 2033 tok after… The virtual catalogue went 112 to 118."*

`git show --stat c33432e` — **14 files**:

| file | ± | role |
|---|---|---|
| `server/src/tee/adapters/seamkiln/__init__.py` | +5 | new — re-exports `SeamkilnAdapter` |
| `server/src/tee/adapters/seamkiln/adapter.py` | +660 | new — the Adapter protocol impl |
| `server/src/tee/adapters/seamkiln/tools.py` | +314 | new — 6 `sk_*` VirtualTools |
| `server/tests/test_seamkiln_adapter.py` | +193 | new — incl. the 17-tool assertion |
| `server/src/tee/app.py` | +9 | the `register_seamkiln_tools` block |
| `server/src/tee/cli.py` | +18/- | `_build_seamkiln_app` + dispatch + help/error strings |
| `server/src/tee/kernel/trust.py` | +4 | `("sk_", "read-scene")` family + 2 write-artifacts entries |
| `benchmarks/run_benchmarks.py` | +108 | scenario + `_safe` wiring + RESULTS section |
| `benchmarks/RESULTS.md` | 27 ± | the generated evidence |
| `docs/PROGRESS.md` | +66 | the P4 entry |
| `seamkiln/src/seamkiln/pattern/allowance.py` | 42 ± | the sew-line-vs-cut-line P1 bug the adapter exposed |
| `seamkiln/src/seamkiln/pattern/dxf.py` | 13 ± | cut line → layer 1, sew line → layer 14 |
| `seamkiln/src/seamkiln/drape/garment.py` | +7 | |
| `seamkiln/tests/test_pattern.py` | 26 ± | |

Not in this commit but added by the A53 P6 / A65 follow-ups: `docs/seamkiln-lane.md`, `server/tests/test_seamkiln_translate.py`, `server/tests/test_seamkiln_materials_render.py`, and eight more `sk_*` tools (14 total today: `sk_blocks` `tools.py:338`, `sk_fabrics` :366, `sk_fit` :385, `sk_plot` :400, `sk_interchange` :425, `sk_body` :454, `sk_techpack` :481, `sk_look` :503, `sk_room` :523, `sk_materials` :563, `sk_hardware` :664, `sk_avatar` :742, `sk_touch` :810, `sk_handoff` :862).

---

# Checklist for a new lane (`<lane>` = package name, `<px>_` = tool prefix)

## Files to ADD

| path | content |
|---|---|
| `<lane>/` (repo root) | self-contained package: `pyproject.toml`, `src/<lane>/`, `tests/`, `README.md`, `examples/`, `uv.lock` — precedent `seamkiln/`, `voxkiln/`. NOT a dependency of `server/pyproject.toml`. |
| `<lane>/src/<lane>/session.py` | the `Session` + `Command` + `Session.replay(script)` + `fingerprint()` core, if you want the seamkiln checkpoint-is-the-script property |
| `server/src/tee/adapters/<lane>/__init__.py` | 5 lines: `from …adapter import <Lane>Adapter; __all__ = [...]` |
| `server/src/tee/adapters/<lane>/adapter.py` | `info/probe/list_entities/execute/snapshot/restore/capture` (+ optional `discard_snapshot`); module-level `INSTALL_HINT` + `_need_<lane>()`; lazy `session` property; a `_translate()` wire-op → command table and a `_record()` command-result → `Diff` table (`created/modified/deleted/details/notes` **and** `upserts`) |
| `server/src/tee/adapters/<lane>/tools.py` | `register_<lane>_tools(app)`; module imports only `typing`/`TeeError`/`VirtualTool`; every handler starts with `_need()`; `_adapter(app)` isinstance scan |
| `server/tests/test_<lane>_adapter.py` | `importorskip("<lane>")`; must include `assert len(_DESC) == 17` and `assert not any(n.startswith("<px>_") for n in _DESC)` |
| `docs/<lane>-lane.md` | the install line (`uv pip install -e <lane>`) + the serve line + the verb table |

## Files to MODIFY

| file:line | change |
|---|---|
| `server/src/tee/app.py:211` (after) | add `from tee.adapters.<lane>.tools import register_<lane>_tools` + call, with the "metadata only, never imported until called" comment |
| `server/src/tee/cli.py:~58` | add `_build_<lane>_app(project, allow_code_exec)` |
| `server/src/tee/cli.py:248` | add `elif args.adapter == "<lane>":` branch |
| `server/src/tee/cli.py:250-251` | add `<lane>` to the "available:" error string |
| `server/src/tee/cli.py:333` | add `<lane>` to the `--adapter` help string (there is no `choices=` to update) |
| `server/src/tee/cli.py:255-269` | only if the lane needs a conditional `_attach_<lane>` (the `_attach_pins` pattern) |
| `server/src/tee/kernel/trust.py:164-192` | add `("<px>_", "read-scene")` to `_FAMILY` — **or deliberately omit it** and table every tool, which is the documented rule for `cad_`/`trade_` (`trust.py:179-188`). Any `cad_*` tool MUST go in `_EXPLICIT`. |
| `server/src/tee/kernel/trust.py:193-363` | one `_EXPLICIT` entry per tool that writes a file (`write-artifacts`), stores state (`write-state`), or mutates (`write-scene`) — otherwise registration crashes the server at startup (`registry.py:86-91` → `trust_untabled_tool`) |
| `server/src/tee/kernel/extras.py:34-46` | only if the lane ships as a pip extra: add a `WITNESS` leaf-import row, and add to `NOT_IN_TEE_VENV` if it lives in a sidecar |
| `server/src/tee/fleet/probe.py:28-49` | matching `EXTRAS` row (extra name, what it brings, install line) if extra-based |
| `server/pyproject.toml:19+` | the `[project.optional-dependencies]` group if extra-based (`cad` already exists at :102-104) |
| `server/src/tee/doctor.py:254-299` (pattern) | add `check_<lane>()` modelled on `check_voxkiln` |
| `server/src/tee/doctor.py:562-578` | add it to the `run_checks` list |
| `benchmarks/run_benchmarks.py:~1231` | add `run_<lane>_scenario()` returning `dict | None` |
| `benchmarks/run_benchmarks.py:1800` | `<lane>_row = _safe(run_<lane>_scenario)` |
| `benchmarks/run_benchmarks.py:1802-1804, 1869-1872` | thread the row into `write_results(...)` and its signature |
| `benchmarks/run_benchmarks.py:~2121, ~2196` | `if <lane>_row is not None: lines += _<lane>_section(row)` + the section builder |
| `server/Makefile:8` / `packaging/mcpb_manifest.json:"version"` | bump `TEE_SERVER_VERSION` and manifest `version` together |
| `docs/PROGRESS.md`, `docs/DECISIONS.md`, `CHANGELOG.md` | the lane entry + every licence call |

## Files to explicitly NOT touch

- `packaging/mcpb_manifest.json` `tools[]` — the 17-entry array is the always-loaded surface invariant (~2,033 tok); a virtual-tool lane adds zero entries.
- `server/src/tee/server.py:30` `_DESC` — same invariant, guarded by `test_server_lint.py:82` (`EXPECTED_TOOL_COUNT = 17`) and `test_seamkiln_adapter.py:173`.
- `server/Makefile:22-36` `mcpb:` — the lane package is installed separately, not bundled; the `:38-46` REMINDER already covers the wipe-on-upgrade trap that will also eat an editable lane install.