# CLAUDE_A69_SCRIPT.md — the Fusion lane: Autodesk Fusion as a live TEE lane

**Owner directive (2026-09-06, verbatim):** *"Create a lane dedicated to
autodesk fusion."* Research doc 71 is the design of record; this is the plan
of record. Written for a cold session.

## Orientation

- Repo root `TokenEfficiencyEngine/`, code in `server/`; branch
  `claude/tee-component-integration-iflsyq` (the A68 PR #1 branch — the
  owner asked for this lane while that PR was open, and pushes stay on the
  designated branch). Read `docs/PROGRESS.md` first; real output into it per
  phase; one commit per phase.
- Suite: `cd server && UV_FROZEN=1 uv run pytest -q` (addopts exclude
  dcc/ml/network/llm), `make lint`. Surface invariant: **17 always-loaded
  tools**; A68 left the Desktop composition at 2,129 wire tokens.
- **Fusion has no Linux build and none is on this machine.** Everything is
  built on a hermetic shim (`server/tests/fixtures_fusion.py`) that `exec`s
  the generated scripts, exactly as the FreeCAD lane is; the live half is
  `-m dcc` and the Mac smoke in P4. Nothing is claimed live before it ran.
- Ports: Blender 9876/9877, FreeCAD 9875, Godot 9879 → **Fusion 9881**.

## Verified facts (doc 71 §3 — build ON these, and add a row before using anything else)

1. The API is touched only from the primary thread; a worker thread
   reaches it with `registerCustomEvent` / `fireCustomEvent(id, info)` and a
   `CustomEventHandler.notify(args)` reading `args.additionalInfo` —
   Autodesk's own `FusionMCPSample` add-in does exactly this (its
   `task_manager.py` was read in full).
2. Internal units are centimetres and radians. `ValueInput.createByString`
   respects units in the string and applies the document's active unit to a
   unitless one — so every length the codegen emits carries `mm`.
3. `ExtrudeFeatureInput.setDistanceExtent` is RETIRED (Sept 2022); the
   current call is `setOneSideExtent(DistanceExtentDefinition.create(v),
   ExtentDirections.PositiveExtentDirection)`.
4. Export options differ in parameter order by format: STEP and the Fusion
   archive take `(filename, geometry=None)`; STL and OBJ take `(geometry,
   filename)`. The ImportManager imports STEP/IGES/SAT/f3d, never OBJ/STL.
5. The timeline is the rollback mechanism: `markerPosition` is settable,
   `deleteAllAfterMarker()` exists, `Parameter.expression` is settable,
   `Design.allParameters` lists every parameter. There is no scriptable
   undo. A direct-modeling design has no timeline.
6. `entityToken` + `Design.findEntityByToken(token)` are the stable identity;
   tokens are long, so the bridge mints short ids and keeps the map.
7. `Viewport.saveAsImageFile(filename, w, h)` infers the format from the
   extension; the reference does not say which — the smoke finds out.

## Laws

Doc 71 §5, plus the inherited ones: measured before/after; Rule 6 refusals;
zero new always-loaded tools; every `fu_*` tool tabled individually; the
add-in binds 127.0.0.1 only and is MIT (the Blender bridge's GPL loop is
not copied); the owner's document is never created, saved, closed or
uploaded by the lane.

## P0 — design of record, script, decisions (one commit)

`docs/research/71-fusion-lane.md` (+ index row), this script, a DECISIONS
entry ("A live GUI lane on an owner document: what the Fusion lane may and
may not do"), the PROGRESS section opened, the `CLAUDE.md` bullet.

## P1 — the add-in bridge and the wire (one commit)

- `adapters/fusion/tee_bridge/TEE/TEE.py` + `TEE.manifest`: a daemon I/O
  thread, one NUL-framed JSON request per connection (`execute` / `ping`),
  a uuid-keyed task table, `fireCustomEvent` per request, the handler
  `exec`s on the primary thread in a namespace carrying the persistent
  `_tee` dict and a `result` dict, stdout/stderr captured, reply shapes
  identical to the Blender bridge. `run()` / `stop()` per the manifest.
  Everything that is not `adsk` lives in importable functions so a test can
  drive the framing and the marshalling with a stub executor and a fake
  event queue.
- `server/src/tee/adapters/fusion/wire.py`: `FusionWire` (probe, execute)
  with its own refusal codes and the install fix.
- *Acceptance:* `tests/test_fusion_bridge.py` — the add-in module imports
  without `adsk`; a socket round trip against the real listener with a stub
  executor answers ok/error/ping; a malformed frame gets a structured
  error; the primary-thread handler runs the queued task and the waiting
  thread gets the reply; `FusionWire` speaks to it.

## P2 — codegen, adapter, shim, contract (one commit)

- `codegen.py`: `compile_batch(ops)` → one script (doc 71 §4.3 table);
  `LIST_CODE`, `probe`/`measure`/`params`/`timeline`/`export`/`capture`/
  `snapshot`/`restore` programs; `KINDS`, `OPS`, `IMPORT_SUFFIXES`,
  `EXPORT_FORMATS` constants the vocab and tools reuse; every length in mm
  with the unit written; read-backs converted once.
- `adapter.py`: `FusionAdapter(wire)` — the seven kit methods + `vocab()`;
  `info()` (version through the wire, cached); checkpoints per §4.5 with
  the payload saying what it restores and the direct-design refusal;
  capture per §4.6.
- `tests/fixtures_fusion.py`: a fake `adsk` package (core + fusion) that
  the generated scripts run against: sketches with rectangles/circles and
  profiles, extrudes producing bodies with volume/bbox arithmetic, fillets,
  components, parameters, a timeline with marker/deleteAllAfterMarker,
  export/import managers writing/reading files, a viewport that writes a
  tiny JPEG/PNG; `FakeFusionWire` execs scripts with the shim in
  `sys.modules`.
- *Acceptance:* `tests/test_fusion_adapter.py` runs `AdapterContract` plus:
  mm↔cm at every boundary (a 120×80×10 mm extrude reads back 96,000 mm³
  and a [120, 80, 10] bbox), rollback deletes what came after and restores
  expressions, the direct-design refusal, the retired call never appears in
  a generated script, a generic kind lands as a named component,
  `test_lane_vocab.py` holds `vocab()` equal to `codegen.KINDS`/`OPS`.

## P3 — tools, tables, CLI, routing, docs (one commit)

- `tools.py`: `fu_probe`, `fu_export` (with `into=` through
  `handoff_import.land`), `fu_measure`, `fu_params`, `fu_timeline`,
  `fu_execute_python` (exec-code); trust rows individually; `("fu_",
  "fusion")` in `kernel/lanes.py`.
- `cli.py`: `_fusion_lane(host, port)`, `fusion` in `ADAPTER_NAMES`,
  `--fusion-port`; `config.py` `[fusion] port`; `doctor` reports the bridge.
- `app.route_batch`: connected candidates win over disconnected ones when
  several lanes take a batch (doc 71 §4.9), with tests.
- Docs: `docs/fusion-lane.md` (install, serve, the ops, checkpoints'
  honest limit, exports, the smoke), README scope/modules rows, quickstart
  and troubleshooting rows, the search-vocabulary cases for `fu_*`.
- *Acceptance:* `tests/test_fusion_tools.py`, `test_lanes_table.py`,
  `test_lane_routing.py` (the connected-lane rule), `test_search_budget.py`
  re-measured if a case is added, full suite and lint green.

## P4 — measure, record, push (one commit)

- `benchmarks/run_benchmarks.py::run_fusion_scenario` on the shim: the TEE
  arm (one batch: sketch + extrude + fillet, its diff, one `fu_measure`)
  against what a model does without the lane (write the Fusion script
  itself and read the listing back) — tokens and calls; a RESULTS section.
- The Mac smoke, written out so the owner can run it cold:
  1. copy `adapters/fusion/tee_bridge/TEE/` into Fusion's AddIns folder (or
     register the folder in Scripts and Add-Ins), run it, confirm
     `TEE bridge listening on 127.0.0.1:9881` in the Text Commands palette;
  2. open a parametric design; `tee serve --adapter fusion`; `fu_probe`;
  3. one `tee_batch` (a 120×80 mm rectangle sketch, a 10 mm extrude, a 2 mm
     fillet), `fu_measure` (expect 96,000 mm³ before the fillet),
     `tee_checkpoint`, a second extrude, `tee_rollback`, `tee_capture`;
  4. `fu_export format=step` and `format=obj into=blender` if a Blender
     lane is served;
  and the table in doc 71 §3 gets its live column from the output.
- PROGRESS per phase with the numbers; CHANGELOG Unreleased; doc 71 §8.

## Verification

```
cd server
UV_FROZEN=1 uv run pytest -q tests/test_fusion_bridge.py tests/test_fusion_adapter.py \
  tests/test_fusion_tools.py tests/test_lane_vocab.py tests/test_lanes_table.py \
  tests/test_lane_routing.py tests/test_trust_kernel.py tests/test_server_lint.py
UV_FROZEN=1 uv run pytest -q
UV_FROZEN=1 make lint
cd ../benchmarks && UV_FROZEN=1 uv run --project ../server python -c \
  "from run_benchmarks import run_fusion_scenario as r; print(r())"
# on the Mac, with Fusion open and the add-in running:
UV_FROZEN=1 uv run pytest -q -m dcc tests/test_fusion_live.py
```
