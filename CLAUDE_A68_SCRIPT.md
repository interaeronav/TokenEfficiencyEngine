# CLAUDE_A68_SCRIPT.md — Phase A68: no lane is the hub

**Status: IN FLIGHT (2026-09-05).** Design of record:
`docs/research/70-lane-routing-no-hub.md`. Amendments go in `docs/DECISIONS.md`,
not inline here. Work the phases from where `docs/PROGRESS.md` says they stand.

**Owner directive:** *"Integrate better all components of TEE. The issue right now
is too much goes through Blender when there are other components that are able
to work better."* Then: *"Allow to bypass Blender if not required. Decentralize
the use of Blender or Unreal Engine."*

**Goal:** one server, N lanes, none of them the hub. The kernel routes a batch
by what it contains (entity id → create kind → op verb) and says where it went;
reads without a lane give a per-lane overview instead of defaulting; a headless
lane never touches a DCC; an export lands in a scene lane in one call only when
asked; the model is told what is served; and every number is measured before
and after in tokens per completed task.

---

## Orientation for a cold session

- `tee serve --adapter blender --adapter partkiln --adapter seamkiln` (the
  Desktop manifest since 0.21.1) holds every lane named in ONE `TeeApp`
  (`server/src/tee/cli.py::build_app`). Until A68 the FIRST listed was the
  declared default for an omitted `adapter=`, so every adapter-less call went to
  Blender.
- The always-loaded surface is 17 tools / 2,033 wire tokens; the long tail is
  virtual tools behind `tee_search_tools → tee_describe_tool → tee_call`
  (`kernel/registry.py`). Every virtual tool is tabled in `kernel/trust.py` or
  the server refuses to boot.
- Each adapter owns its batch vocabulary: `FakeAdapter` (kernel/adapter.py),
  Blender (`adapters/blender/codegen.py`, kinds at `_create`, modeling ops at
  `_MODELING_OPS`), partkiln (`_WIRE_OPS`, kinds from `partkiln.document.KINDS`
  or the sidecar's `verbs` method), seamkiln (`_WIRE_OPS` = create/set/delete/
  arrange + 24 passthrough verbs; kinds panel/seam/block), Unreal and FreeCAD
  (create/set/delete), Godot (six bridge commands, forwarded blindly).
- Checkpoints already record their lane and carry global ids (`kernel/
  checkpoints.py`). The scene cache already keeps per-kind counts.

## What was found (the finding, measured in P0)

1. **What the model is told** says TEE "drives Unreal Engine and Blender"
   (server instructions), the search examples are Blender's, `tee_batch`
   advertises only create/set/delete, the skill triggers on "Drive Blender/
   Unreal", the manifest and README name only two adapters.
2. **A bare `adapter` parameter** ships as `{"type":"string"}` with no
   description; `tee_status` names lanes but not what they are for.
3. **Nine default rules, all Blender**: `resolve_adapter`'s declared default,
   `next(iter(app.adapters), "fake")` in assets/physical/pins/capture,
   `sorted(adapters)[0]` in senses, literal `"blender"` in assets/importer,
   uefn, senses, extract/handoff. A partkiln op sent to the default lane comes
   back from Blender as a raw `ValueError` traceback with no lane hint.
   `tee_script` checkpoints Blender for every virtual call, even `pdf_compose`.
4. **Handoffs are manual file drops.** partkiln's capture refusal prescribes a
   four-step route "in a TEE served on Blender" and says "nothing in this
   session can do it" — false since the multi-adapter serve. seamkiln's
   `ops_for` emits `{"op":"create","kind":"import_file"}`, which Blender rejects
   (`import_file` is an op). Search is lane-blind and its recall fixture never
   registered `bl_*`.

## Decisions taken by the owner (2026-09-05)

- **Decentralise.** The declared default becomes opt-in
  (`tee serve --default-adapter NAME`); the Desktop manifest declares none.
  This revises the 2026-09-04 ruling "first listed is the default".
- **Route by content, declare the result.** Omitted `adapter=` + ops accepted
  by exactly one lane → run there and say so. Several lanes → the opt-in default
  if declared, else refuse naming the lanes. None → refuse naming which lane
  accepts each op.
- **Handoff:** `pk_export` / `sk_handoff` / `fc_export` gain `into=<lane>` (or
  `auto`); an export with no `into` never touches a scene. Declined: `adapter=`
  on `bl_build_from_plan` / `bl_check_against_plan` / `capture_apply`; wiring
  the `drafting/` package.
- **Surface:** lane guidance in the MCP instructions string plus a one-line
  `adapter=` description; under +100 wire tokens, measured.

## Laws

1. **No lane is the hub.** A default exists only when an operator declared it,
   and `tee_status` reports it. Law 19 stands for the explicit declaration.
2. **Route by content, refuse by name.** id beats kind beats verb; ambiguity
   names the lanes; an op no lane accepts names the lanes that would.
3. **A read never checkpoints.** Overview, locate and diff touch no snapshot.
4. **A headless lane never touches a DCC.** A DCC is used only for scene work
   or pixels, and only the one that can do it.
5. **The reply says where the state is.** Every multi-lane batch/summary/detail
   reply carries `adapter`; a routed batch says how it was routed.
6. **Measured before and after** (A46). A phase without a number did not happen.
7. **Zero new always-loaded tools**; the wire may grow under +100 tokens; the
   instructions string stays under 2 KB (Claude Code truncates past it).
8. **A scene-writing tool says which scene.** A `write-scene` virtual tool with
   no lane is a startup error, like an untabled tool.
9. **An export never imports unless told**, and then through the trust check —
   a write-artifacts tool may not exercise write-scene silently.
10. **A lane may not claim another's search vocabulary by being newer**
    (DECISIONS 2026-09-03); the recall table is re-measured, never edited.
11. **Law 17 stands:** partkiln's vocabulary is known without OCP; routing
    never waits on a warm-up job.

## Phases (each independently shippable; commit + PROGRESS entry per phase)

### P0 — script, design of record, measure before
- **0a** this script; `docs/research/70-lane-routing-no-hub.md`; a row in
  `docs/research/00-index.md`; a bullet in `CLAUDE.md`; the DECISIONS entry
  *No lane is the hub: the declared default becomes opt-in*.
- **0b** `benchmarks/run_benchmarks.py::run_routing_scenario` — ONE app
  composed like the Desktop manifest (live Blender when the bridge is up, else
  a stand-in carrying Blender's vocabulary and 0.21.1's refusal text; partkiln
  on the test `FakeKernel`; seamkiln if importable, else skipped with the
  reason). Rows: an adapter-less partkiln batch and seamkiln batch (calls and
  tokens to completion), `tee_script` calling `pdf_compose` (Blender checkpoints
  taken), `tee_scene_summary` with no adapter, the recall table over the full
  composition, wire surface tokens + instructions bytes, "render a partkiln
  part" (calls). RESULTS section `## Lane routing: no lane is the hub (A68)`,
  carried forward like every other section. *Acceptance:* the before numbers
  are in RESULTS.md and PROGRESS.

### P1 — the kernel knows its lanes
- **1a** `LaneVocab(ops, kinds, kind_optional, imports, renders, purpose)` as
  ONE optional adapter method `vocab()` (kernel/adapter.py; all seven adapters;
  the kit documents it). `TeeApp.route_batch(ops, adapter) → Route(lane, how)`
  used by `tee_batch` and `tee_script.batch`. `codegen.check_batch` gives
  Blender structured `bad_op`/`bad_kind` refusals before the wire; `run_batch`
  appends the cross-lane hint. Multi-lane batch replies carry `adapter` (and
  `routed` when the kernel decided). *Acceptance:* `tests/test_lane_routing.py`,
  `tests/test_lane_vocab.py` (each `vocab()` equals its dispatcher; partkiln's
  imports neither partkiln nor OCP), `tests/test_blender_bad_op.py`;
  single-adapter payloads byte-identical.
- **1b** `--default-adapter NAME` (validated against the served names);
  `build_app` no longer implies one; the manifest args are untouched.
  *Acceptance:* `tests/test_multi_adapter_serve.py` updated — same scenarios,
  new truth; the Desktop composition reports no `default_adapter`.
- **1c** decentralised reads: `overview()`, `locate()`, `checkpoint_all()`,
  `renderers()`; `CheckpointManager.find(ref)` with stacks keyed by served lane
  name; `tee_scene_summary` / `tee_entity_detail` / `tee_rollback` /
  `tee_checkpoint` / `tee_diff` / `tee_capture` / `tee_script` as doc 70 §4.
  *Acceptance:* `tests/test_decentralised_reads.py`; a script calling
  `pdf_compose` takes zero Blender checkpoints.
- **1d** `VirtualTool.lane` from `kernel/lanes.py` (one table: families +
  explicit rows), the startup check, `describe()` reports `lane`, search
  indexes the lane and prefers served lanes at equal score, `tee_status`
  reports each lane's purpose/ops/kinds/tool families; the search-budget
  fixture becomes the Desktop composition with sk_* and routing cases and a
  re-measured table. *Acceptance:* `tests/test_lanes_table.py`; the recall
  table holds at the recorded limit; reply < 280 tokens.
- **1e** kernel lanes stop touching DCCs: assets (`importer_lane`), physical
  (`blender_lane`), pins (`unreal`), capture (lanes derived from what is
  served), senses (one connected renderer / `blender_lane`), uefn
  (`blender_lane`), extract/handoff (`blender_lane` at call time;
  `ex_export_ifc` unconditional). *Acceptance:* no `next(iter(app.adapters`,
  `sorted(adapters)[0]` or literal `"blender"` default left in `server/src`
  (a test greps for them).

### P2 — the model is told
`lanes.instructions(app)` builds the MCP instructions from what is served
(≤ 2,048 bytes, tested on the seven-lane worst case); `tee_batch` gains one
sentence; `tee_search_tools` examples span lanes; `adapter` params get
"lane; omit=routed" (injected in the schema-slimming loop, SDK-independent);
`skills/tee-usage/SKILL.md`, the manifest text, README, quickstart,
troubleshooting and adapter-kit reframed. *Acceptance:*
`tests/test_instructions.py`; `test_server_lint` still 17 tools; the wire
delta measured by `run_surface_scenario` under +100 tokens.

### P3 — the handoff lands in-server
`kernel/handoff_import.py::land()` (resolve `into`, refuse unsupported
suffixes, trust-check write-scene, `import_file` op with the manifest's units,
read-back verdict); `pk_export into=`; `sk_handoff out=/target=/into=`;
`fc_export into=`; seamkiln `ops_for` fixed to the `import_file` OP; the
partkiln capture refusal rewritten to the two-call route; the acceptance
example uses it. *Acceptance:* `tests/test_handoff_import.py`;
`tests/test_partkiln_capture.py` rewritten honestly; "render a partkiln part"
is two calls.

### P4 — measure after, docs, release
Re-run the benchmarks; RESULTS after; PROGRESS per phase with numbers;
CHANGELOG Unreleased *One server, N lanes, no hub*; doc 70 finalised. The
version cut is the owner's call (0.22.0 if taken — behaviour changed).

## Deliberately not built
`adapter=` on the extract/capture Blender tools (they stay Blender-bound,
resolved by capability, never by position); the `drafting/` critic; a
two-block `tee_capture` reply (A6 floor); renaming the physical `param_set`
tool (the collision is resolved by routing).

## Verification
```
cd server && uv sync --extra extract --extra pdf --extra pointcloud --extra assets --extra physical
uv pip install --python .venv/bin/python -e ../seamkiln -e ../partkiln      # never [brep] here
uv run pytest -q && make lint
cd ../benchmarks && uv run --project ../server python -c "from run_benchmarks import run_routing_scenario as r; r()"
```
