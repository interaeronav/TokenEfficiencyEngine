# 70 — No lane is the hub: content-routed lanes for a multi-adapter TEE (A68)

*Design of record for `CLAUDE_A68_SCRIPT.md`. Written 2026-09-05 from three code
audits of the working tree at `a985f08` (dispatch, component inventory, and the
model-facing text); every claim below cites the line it was read from. The
"measured before" table is filled by P0b and the "measured after" table by P4.*

## 1. The finding

**Owner:** *"too much goes through Blender when there are other components that
are able to work better"*, then *"allow to bypass Blender if not required.
Decentralize the use of Blender or Unreal Engine."*

Since 0.21.1 one `tee serve` holds blender + partkiln + seamkiln (the Desktop
manifest) and the first listed is the declared default for an omitted
`adapter=`. The lanes are reachable; nothing steers work to them. The pull
toward Blender is structural and sits in four layers.

### 1.1 What the model is told
- `server/src/tee/server.py:201-209` — the MCP `instructions`: *"Token
  Efficiency Engine: drives Unreal Engine and Blender with minimal tokens…"*.
  Research doc 08 (line 162) records that Claude Code indexes exactly tool names
  plus server instructions when tools are deferred, so this is the one sentence
  a deferring host reads.
- `server.py:106-110` — `tee_search_tools`' worked examples are *'blender
  material'*, *'bake physics'*.
- `server.py:63-69` — `tee_batch` advertises `create | set | delete` only; the
  partkiln and seamkiln vocabularies are invisible.
- `skills/tee-usage/SKILL.md:3` — the trigger line is *"Drive Blender/Unreal
  through the TEE MCP server"*; lines 38-50 list every lane except `pk_`, `sk_`,
  `pc_`.
- `packaging/mcpb_manifest.json:6-7`, `README.md:13,80-83,126-137`,
  `docs/quickstart.md:3-5,71-73` — "Blender and Unreal Engine adapters
  included"; the modules table stops at kb.

### 1.2 A bare `adapter` parameter
Every `adapter` parameter ships as `{"type":"string"}`: no description, no
enum (`server.py` signatures; `_slim_schema` 171-194 strips titles only).
`tests/test_server_lint.py:107-113` forbids a wire *default* (SI-B6) — not a
description. Only `tee_status` names adapters, and `AdapterInfo`
(`kernel/adapter.py:80-96`) has no purpose field, so it says "partkiln:
connected", never "partkiln: mechanical CAD".

### 1.3 Nine default rules, all Blender; no op→lane knowledge in the kernel
| site | rule |
|---|---|
| `app.py:261-285` `resolve_adapter` | explicit → declared default (= first `--adapter`, `cli.py:123`) → sole → `adapter_required` |
| `assets/tools.py:29-32`, `physical/tools.py:33-36`, `pins/tools.py:52-55`, `capture/tools.py:690` | `next(iter(app.adapters), "fake")` |
| `senses.py:367,607` | `sorted(adapters)[0]` — alphabetical |
| `assets/importer.py:135`, `uefn/tools.py:111`, `senses.py:437`, `extract/handoff.py:113,160-161` | the literal `"blender"` |

`run_batch` (`app.py:326-381`) hands ops to `adapter.execute`; the contract
says *"unknown ops raise"* (`kernel/adapter.py:20`) and nothing in `kernel/`
knows which lane accepts what. A partkiln op sent to the default lane reaches
Blender's codegen and raises a raw `ValueError` (`adapters/blender/codegen.py:274`),
returned as `blender_error` plus a compacted traceback (`adapters/blender/
adapter.py:210-217`) whose fix says "roll back with tee_rollback" — no lane
hint. When Blender is *down*, `app.adapter()` (`app.py:298-306`) does name the
other lanes: better guidance on the failure path than on the success path.
`tee_script` (`kernel/script.py:437-440`) runs `_guard(default_adapter)` for
every `call()`, so `pdf_compose` costs a full `.blend` save.

### 1.4 Handoffs are manual file drops
- partkiln's `capture()` (`adapters/partkiln/adapter.py:418-449`) refuses with a
  four-step route — `pk_export` → `as_ingest` → `as_import` → `tee_capture` —
  "in a TEE served on Blender", and says *"a TEE served on partkiln holds only
  that adapter, so nothing in this session can do it for you"*. False since the
  multi-adapter serve; `tests/test_partkiln_capture.py` pins the text.
- seamkiln's `ops_for` (`seamkiln/src/seamkiln/handoff.py:300-316`) emits
  `{"op":"create","kind":"import_file"}`; Blender's `import_file` is an *op*
  (`codegen.py:255`) and `_create` rejects the kind (`codegen.py:132`).
  `seamkiln/tests/test_handoff.py:97` pins the wrong shape.
- `fc_export` writes a file; nothing imports it. `ex_export_ifc` — an offline
  IFC writer — is registered only when Blender is served (`cli.py:341`).
- Search is lane-blind: hits are `{name, summary}` (`kernel/registry.py:181-184`),
  ties break alphabetically (`bl_` < `pc_` < `pk_` < `sk_`), `describe()` omits
  tags, and the recall fixture (`tests/test_search_budget.py:99-107`) never
  registered `bl_*`/`hb_*`, so the measured table was never taken on the
  registry a Desktop server serves. No benchmark composes more than one lane.

## 2. Decisions (owner, 2026-09-05)

1. **Decentralise.** The declared default becomes opt-in
   (`--default-adapter NAME`); the Desktop manifest declares none. This revises
   the 2026-09-04 ruling: content routing makes the common case unambiguous,
   so the tax SI-B6 feared — `adapter=` on every call — no longer exists.
2. **Route by content, declare the result**: one accepting lane → run there
   and say so; several → the declared default if any, else refuse naming them;
   none → refuse naming which lane accepts each op.
3. **Handoff:** `pk_export` / `sk_handoff` / `fc_export` gain `into=`; an
   export with no `into` never touches a scene. Declined: `adapter=` on the
   extract/capture Blender tools; wiring `drafting/`.
4. **Surface:** instructions string + a one-line `adapter=` description; under
   +100 wire tokens, measured.
5. **Shape:** this doc, `CLAUDE_A68_SCRIPT.md`, DECISIONS / PROGRESS /
   CHANGELOG, one commit per phase.

## 3. Measured before (P0b)

`benchmarks/run_benchmarks.py::run_routing_scenario` on the tree at `ce3e13f`:
ONE app composed like the Desktop manifest — blender as a stand-in that speaks
exactly codegen's vocabulary and answers 0.21.1's refusal, partkiln on the
suite's `FakeKernel`, seamkiln real — every call through the real MCP layer.
A row completes its task the way a model that knows nothing about lanes
would: no `adapter=`; if the refusal names the lane, retry with it; if not,
ask `tee_status`, then retry.

| task | calls | tokens | what happened |
|---|---|---|---|
| partkiln batch, adapter omitted | 3 | 731 | refused `blender_error`; no lane in the fix; asked `tee_status`; retried |
| seamkiln batch, adapter omitted | 3 | 562 | same |
| `tee_script` calling `kb_status` | 1 | 586 | **1 Blender checkpoint** for an adapter-agnostic tool |
| `tee_scene_summary`, adapter omitted | 1 | 26 | Blender's rows, not the server's lanes |
| render a partkiln part | 4 | 477 | `pk_export`, `as_ingest`, `as_import`, `tee_capture` |

Surface 17 tools / 2,033 wire tokens; instructions 433 B; 173 virtual tools;
`default_adapter: blender`. Search recall over the FULL composition — limit 3:
29/33, **5: 32/33**, 8: 33/33, 10: 33/33. The table in `test_search_budget.py`
was taken on an 85-tool fixture and says 33/33 at 5; on the registry a
Desktop server serves, "size from an image" ranks `ex_estimate` sixth,
behind `bl_build_from_plan`, `pdf_compose`, `sk_body`, `board_compose` and
`cad_scad_build`. Also found: the suite's `FakeKernel` wrote nine bytes of
text for a GLB, so the manual render route could not be measured until it
wrote a real minimal one.

## 4. Design

### 4.1 One optional adapter method: `vocab() -> LaneVocab`
`LaneVocab(ops, kinds, kind_optional, imports, renders, purpose)` in
`kernel/adapter.py`. An adapter that does not implement it claims everything
(`ops=None, kinds=None`), which on a multi-lane server surfaces as an honest
`adapter_required` until it does — the kit documents the eighth, optional
method. `purpose` lives here rather than on `AdapterInfo` because `info()` is a
wire trip on Blender and must be known when the DCC is down.

| lane | ops | create kinds | kind optional | imports | renders |
|---|---|---|---|---|---|
| fake | create, set, assign_material, delete | any | yes | – | yes |
| blender | create, set, delete, assign_material, import_file + the 8 modeling ops | cube, plane, uv_sphere, ico_sphere, cylinder, cone, torus, monkey, empty, light, camera (`codegen.py:113-132`) | yes — codegen defaults to cube | glb, gltf, obj, fbx | yes |
| partkiln | `_WIRE_OPS` (`adapters/partkiln/adapter.py:61`) | a closed tuple, refreshed from the kernel's `verbs` answer once warm | no | – | no (text first) |
| seamkiln | `_WIRE_OPS` (`adapters/seamkiln/adapter.py:431`) | panel, seam, block | no | – | only with a garment arranged and Blender available |
| unreal | create, set, delete | any | yes | glb, gltf, fbx, obj (`import_asset_file`) | yes |
| freecad | create, set, delete | any | yes | – | yes |
| godot | add_node, set_props, remove_node, save_scene, load_scene, run_scene (`adapters/godot/tee_bridge/bridge.gd:171-230`) | any | yes | – | no (dummy rasterizer) |

Law 17 holds: partkiln's vocabulary is a static tuple in the adapter, asserted
equal to `partkiln.document.KINDS` by a test that runs where partkiln imports;
the kernel's own answer replaces it only after the warm-up job lands.

### 4.2 The batch router — `TeeApp.route_batch(ops, adapter) -> Route(lane, how)`
Explicit `adapter=` → as today. One served lane → it (single-adapter payloads
stay byte-identical). Otherwise, per op, a candidate set:
- **(a) by id** — any op carrying `id` → the lanes whose `SceneCache` holds it
  (connected lanes are warmed first; none → `unknown_entity` naming the lanes
  searched);
- **(b) by kind** — `create` → the lanes whose kinds contain `kind`; an omitted
  kind matches lanes with `kind_optional`;
- **(c) by verb** — everything else → the lanes whose `ops` contain it.

Intersect over the batch. One lane → `Route(lane, "id"|"kind"|"op")`. Several
with the declared default among them → `Route(default, "default")`. Several
without → `adapter_required` naming them. An op no lane accepts →
`op_not_in_lane` listing, per op, the lanes that would and each lane's
vocabulary (a refusal path, so its cost is paid only on error). Ops that fit
different lanes → `batch_spans_lanes` ("a batch is one lane's checkpoint").

`param_set` (a Blender modeling op AND a partkiln verb) and `export` (partkiln
AND seamkiln) resolve by id, kind or the batch's intersection, or refuse
honestly — never by position.

Replies: `run_batch` adds `"adapter": lane` whenever more than one lane is
served; the router adds `"routed": "by kind; pass adapter= to pin"` when it
decided. Blender pre-validates a batch (`codegen.check_batch`) before the wire
so an unknown op or kind is a structured `bad_op` / `bad_kind`, and `run_batch`
appends "Lanes that accept it: partkiln (pass adapter=partkiln)" when another
served lane claims the op — the kernel adds the hint, no adapter knows the
others.

### 4.3 The declared default becomes opt-in
`tee serve --default-adapter NAME` declares one (validated against the served
names, reported by `tee_status`). `--adapter` order no longer implies it. The
manifest lists blender, partkiln, seamkiln and declares none.

### 4.4 Decentralised reads (multi-lane server, no `adapter=`, no default)
| tool | behaviour |
|---|---|
| `tee_scene_summary` | `overview()` — `{lanes: {name: {connected, entities, kinds, epoch, revision}}}`, no rows; the note says how to get rows |
| `tee_entity_detail(id)` | `locate(id)` across caches; the reply carries `adapter`; none → `unknown_entity` naming lanes searched; several → `entity_ambiguous` |
| `tee_rollback(ref)` | `CheckpointManager.find(ref)` — ids are global (`checkpoints.py:51`) and each checkpoint records its lane; stacks keyed by served lane name (two fakes no longer share one); a label in several lanes → `checkpoint_ambiguous` |
| `tee_checkpoint(label)` | `checkpoint_all()` — every connected lane whose cache holds state; `{checkpoints: {lane: cpN}, skipped: [...]}` |
| `tee_diff` | `adapter_required` — stamps are per lane, and the reply the stamp came from carries `adapter` |
| `tee_capture` | the one connected lane whose vocab renders; none → `capture_no_renderer`; several → `capture_ambiguous`; the reply stays a bare image (A6) |
| `tee_script` | `batch()` routes and guards that lane; `summary()` is the overview; `call()` guards only the tool's own lane; reads and agnostic tools never checkpoint |
| `tee_status` | `lanes: {name: "<purpose> · ops N · kinds … · tools …"}`; `default_adapter` only when declared |

### 4.5 The lane table — `kernel/lanes.py`
One table, like `trust.py`: families `bl_`/`hb_`/`sim_` → blender, `ue_`/`pin_`
→ unreal, `fc_` → freecad, `pk_` → partkiln, `sk_` → seamkiln; explicit rows for
the tier-2 modeling ops, `sense_camera`, `export_for_uefn` (blender), the tools
that route by their own `adapter=` (`as_import`, `as_place`, `as_material`,
`as_photo_material`, `as_sun`, `mat_assign`, `capture_apply`, `sense_viewport`,
`sense_frame`), and `uefn_place_device` / `uefn_entity_batch` (they write
through their own proxy; the label names the scene without being a served
adapter). `VirtualTool.lane` is resolved at registration; a `write-scene` tool
with no lane is a startup error. `as_sheet` is tabled `write-scene`
(`trust.py:257`) but writes a contact-sheet image: its row becomes
`write-artifacts` (both baseline; nothing is granted). Search indexes the lane
name last and prefers served lanes at equal score.

### 4.6 Kernel lanes stop touching DCCs
Every positional or literal default in §1.3 is replaced: assets route by the
`import_file` capability (`importer_lane`), physical/uefn/senses/extract resolve
*the served Blender* by capability (`blender_lane`, refusing
`blender_not_served`), pins name `unreal`, capture derives its lanes from what
is served, `ex_export_ifc` registers unconditionally.

### 4.7 The handoff lands in-server — `kernel/handoff_import.py::land()`
Resolves `into` (a lane, or `auto` → the one served lane that imports that
suffix); refuses `handoff_import_unsupported` (Blender + step → export glb);
checks `write-scene` through the trust kernel because the calling tool is
write-artifacts; emits `{"op":"import_file","path","name","props":{"scale"}}`
with scale from the manifest's units for non-self-describing formats and 1.0
for glTF (the double-convert trap both handoff modules document); runs
`app.run_batch(lane, …)`; reuses the asset importer's read-back verdict.
Callers: `pk_export into=`, `sk_handoff out= target= into=`, `fc_export into=`.
The partkiln capture refusal becomes the two-call route.

### 4.8 The model is told
`lanes.instructions(app)` builds the MCP instructions from what is served: one
server, the lanes with purpose, "none is the default unless declared", the
`adapter=` rule, the prefix legend, "headless lanes never need Blender or
Unreal; a scene lane only for scene work, pixels only through a lane that
renders", and when to search the long tail — under 2,048 bytes on the
seven-lane worst case. `tee_batch` gains one sentence; the search examples
span lanes; `adapter` params say "lane; omit = routed". Skill, manifest,
README, quickstart, troubleshooting and adapter-kit are reframed from
"a Blender/Unreal MCP" to "lanes".

## 5. What does not change
SI-B6's loud refusal on undeclared ambiguity; Law 19 for an explicit
declaration; `bl_build_from_plan` / `bl_check_against_plan` / `capture_apply`
stay Blender-bound; `drafting/` stays unwired (a recorded gap); the taint law;
the 17-tool surface; the search-vocabulary ruling.

## 6. Risks, and how each is checked
- `Annotated`/`Field` behaviour on mcp 2.0.0 could not be verified offline →
  the `adapter` description is injected in the existing schema-slimming loop.
- Blender pre-validation must keep the `-m dcc` live suite green.
- seamkiln / OCP absent in CI → static vocabularies, `importorskip`, the test
  `FakeKernel`.
- The recall corpus grows from 85 to ~180 tools; the table is re-measured and
  fixed only by naming or tagging the new cases' own tools.
- Checkpoint keying by lane name touches `discard_all` / `list` callers.
- Warming every connected lane for id routing costs one `list_entities` per
  cold lane, once per session.

## 7. Measured after (P4)

*Filled by P4.*
