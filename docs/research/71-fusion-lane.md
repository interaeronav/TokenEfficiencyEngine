# 71 — The Fusion lane (A69): Autodesk Fusion as a live, first-class TEE lane

**Owner directive (2026-09-06, verbatim):** *"Create a lane dedicated to
autodesk fusion."*

Status: design of record for `CLAUDE_A69_SCRIPT.md`. Every API fact in §3
was read from Autodesk's Fusion API reference or from Autodesk's own
`FusionMCPSample` on 2026-09-06 (the URLs are in the table). **None of it
has run against a live Fusion on this machine** — Fusion has no Linux
build — so §3 separates "verified in the reference" from "measured live",
and the live column is filled by the smoke procedure in the script (P4)
on the owner's Mac. The rule in `CLAUDE.md` outranks memory: an API call
that is not in §3 does not go into the codegen.

## 1. What a Fusion lane is, and is not

Fusion is a **live, GUI-only, cloud-saved** parametric CAD application. There
is no headless Fusion, and no official local HTTP surface: code runs inside
the application as a script or an add-in, in Fusion's embedded Python, and
the API must be touched **only from the primary thread** (§3, rows 1–3).
So the lane is the Blender shape, not the partkiln shape:

- **A bridge add-in** (`adapters/fusion/tee_bridge/TEE/`) runs inside Fusion,
  listens on `127.0.0.1:9881`, and executes what TEE sends on the primary
  thread through Fusion's custom-event queue.
- **The adapter** (`server/src/tee/adapters/fusion/`) is the seven kit
  methods plus `vocab()`: a batch compiles to ONE Python script executed in
  ONE round trip (the FreeCAD precedent, `adapters/freecad/codegen.py`), the
  script prints ONE JSON diff, and the kernel supplies checkpoints, diffs,
  the compact summary, search, the trust check and routing.
- **Zero new always-loaded tools.** The `fu_*` long tail lives behind
  `tee_search_tools`; the surface stays 17 tools.

What it is not: it is not partkiln. partkiln is headless, deterministic and
owned by TEE; Fusion is the owner's open document. The two share vocabulary
(sketch, extrude, fillet) on purpose — the words mean the same thing — and
A68's router refuses an ambiguous batch naming both lanes when both are
live; §4.9 refines the router so a lane whose application is not running is
never a candidate.

## 2. Prior art, and what was taken from it

**`AutodeskFusion360/FusionMCPSample` (MIT).** Autodesk's own MCP server
add-in: a threaded HTTP server inside Fusion, a `TaskManager` that marshals
work onto the primary thread with `Application.registerCustomEvent` /
`fireCustomEvent` and a `CustomEventHandler.notify(args)` that reads
`args.additionalInfo`, and three tools — `execute_api_script`,
`get_screenshot`, `get_api_documentation`. Its marshalling code was read in
full (§3 row 3) and the same mechanism is used here. Its *posture* is the
opposite of TEE's: the model-facing tool is "run this Python". TEE fronts the
same API with typed ops and diffs, and keeps "run this Python" as
`fu_execute_python` behind `exec-code`, denied by default.

**`knowledge-base/15_software_autodesk_fusion/09_api-and-automation.md`**
(the owner's imported reference, `confidence: high`, sources cited). Used
for orientation only, per the `CLAUDE.md` rule about API prose in `13_*`,
`14_*` and `15_*`: every call it names that this lane uses was re-checked
against the reference it cites. Two of its facts survived re-checking and
matter most: **internal units are centimetres and radians**, and
`Sketch.saveAsDXF` / `Sketch.project` / `CAM.postProcess` are **retired** —
and re-checking found a third retirement the KB does not list:
`ExtrudeFeatureInput.setDistanceExtent` (retired September 2022, §3 row 8).

**TEE's own precedents.** The FreeCAD adapter (script per batch, hermetic
shim that `exec`s the generated scripts), the Blender wire (NUL-framed JSON,
`result` dict convention, per-call connections), the Godot bridge (one
request per connection, declarative payloads), partkiln's static vocabulary
(routing never waits on anything), and A68's `handoff_import.land()` (an
export lands in a scene lane only when `into=` says so).

## 3. API facts (reference-verified 2026-09-06; live column: the Mac smoke)

Base URL: `https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/`

| # | Call (as the codegen emits it) | Verified from | What the reference says | Live |
|---|---|---|---|---|
| 1 | `app.registerCustomEvent(id) -> CustomEvent` | `Application_registerCustomEvent.htm` | "intended to be primarily used to send an event from a worker thread you've created back to your add-in running in the primary thread"; null if the id is not unique | ○ |
| 2 | `app.fireCustomEvent(id, additionalInfo)` | `Application_fireCustomEvent.htm` | queues; "does not immediately result in the event handler being called" — runs when the application is idle, in the primary thread | ○ |
| 3 | `class H(adsk.core.CustomEventHandler): notify(self, args)`; `args.additionalInfo` | `CustomEventArgs.htm` + FusionMCPSample `server/task_manager.py` (read in full) | the sample subclasses `CustomEventHandler`, reads `json.loads(args.additionalInfo)`, and fires with `app.fireCustomEvent(event.eventId, json.dumps(...))` | ○ |
| 4 | `adsk.core.Application.get()`; `app.activeProduct`, `app.activeDocument`, `app.activeViewport`, `app.importManager`, `app.version`, `app.log` | `Application.htm` | activeProduct/Document/Viewport are null with no document open | ○ |
| 5 | `design = adsk.fusion.Design.cast(app.activeProduct)`; `design.rootComponent`, `.timeline`, `.userParameters`, `.allParameters`, `.exportManager`, `.designType`, `.findEntityByToken(token) -> Base[]` | `Design.htm`, `Design_findEntityByToken.htm` | designType is Direct or Parametric; findEntityByToken returns an array (a split face yields several) | ○ |
| 6 | `comp.sketches.add(comp.xYConstructionPlane)`; `comp.xZConstructionPlane`, `comp.yZConstructionPlane`, `comp.features`, `comp.bRepBodies`, `comp.occurrences`, `comp.allOccurrences`, `comp.name`, `comp.entityToken`, `comp.physicalProperties`, `comp.boundingBox` | `Component.htm` | | ○ |
| 7 | `sketch.sketchCurves.sketchLines.addTwoPointRectangle(Point3D, Point3D)`; `sketch.sketchCurves.sketchCircles.addByCenterRadius(Point3D, r_cm)`; `sketch.profiles`, `sketch.name`, `sketch.isVisible`, `sketch.entityToken`, `sketch.deleteMe()`, `sketch.timelineObject` | `SketchLines_addTwoPointRectangle.htm`, `SketchCircles_addByCenterRadius.htm`, `Sketch.htm` | radius "in centimeters"; points are Point3D in sketch space | ○ |
| 8 | `ext = comp.features.extrudeFeatures.createInput(profile, op)`; `ext.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(ValueInput), adsk.fusion.ExtentDirections.PositiveExtentDirection)`; `comp.features.extrudeFeatures.add(ext)` | `ExtrudeFeatures_createInput.htm`, `ExtrudeFeatureInput_setOneSideExtent.htm`, `DistanceExtentDefinition_create.htm` | **`setDistanceExtent` is retired (Sept 2022)**; profile may be a Profile or an ObjectCollection of profiles | ○ |
| 9 | `adsk.fusion.FeatureOperations.{Join,Cut,Intersect,NewBody,NewComponent}FeatureOperation` | `FeatureOperations.htm` | values 0,1,2,3,4 | ○ |
| 10 | `adsk.core.ValueInput.createByString("120 mm")` | `ValueInput_createByString.htm` | units in the string are respected; a unitless string takes the document's active unit — so the codegen ALWAYS writes the unit | ○ |
| 11 | `fi = comp.features.filletFeatures.createInput()`; `fi.edgeSetInputs.addConstantRadiusEdgeSet(ObjectCollection, ValueInput, isTangentChain)`; `filletFeatures.add(fi)` | `FilletFeatures_createInput.htm`, `FilletEdgeSetInputs_addConstantRadiusEdgeSet.htm` | edges may be BRepEdge/BRepFace/Feature objects; real radius values default to cm, strings carry units | ○ |
| 12 | `occ = comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())`; `occ.component.name = ...`; `occ.entityToken`, `occ.deleteMe()`, `occ.timelineObject`, `occ.bRepBodies` | `Occurrences_addNewComponent.htm`, `Occurrence.htm` | the new Component is reached through `occurrence.component` | ○ |
| 13 | `design.userParameters.add(name, ValueInput, "mm", comment) -> UserParameter`; `param.expression` (settable), `param.value` (internal cm/rad), `param.unit`, `param.name`, `param.isDeletable`, `param.deleteMe()` | `UserParameters_add.htm`, `Parameter.htm` | boolean ValueInputs unsupported; empty units = unitless | ○ |
| 14 | `body.name`, `body.volume` (cm³), `body.area` (cm²), `body.boundingBox` (min/maxPoint, cm), `body.physicalProperties` (mass kg, centerOfMass cm), `body.faces`, `body.edges`, `body.isSolid`, `body.isVisible`, `body.entityToken`, `body.deleteMe()` | `BRepBody.htm`, `PhysicalProperties.htm` | | ○ |
| 15 | `feature.name`, `feature.entityToken`, `feature.deleteMe()`, `feature.timelineObject`, `feature.isSuppressed`, `feature.bodies`, `feature.healthState`, `feature.errorOrWarningMessage`; `extrude.extentOne` distance is a ModelParameter with a settable `expression` | `Feature.htm`, `Parameter.htm` | deleteMe "works for both parametric and non-parametric features" | ○ |
| 16 | `timeline.markerPosition` (settable, 0..count), `timeline.count`, `timeline.item(i)`, `timeline.deleteAllAfterMarker()`, `timeline.moveToEnd()`; `TimelineObject.entity/name/index/isSuppressed/isRolledBack/isGroup/healthState` | `Timeline.htm`, `TimelineObject.htm` | | ○ |
| 17 | `design.exportManager.createSTEPExportOptions(filename, geometry=None)`, `createSTLExportOptions(geometry, filename)`, `createOBJExportOptions(geometry, filename)` (Oct 2022), `createFusionArchiveExportOptions(filename, geometry=None)`, `createC3MFExportOptions`, `createIGESExportOptions`, `createSATExportOptions`, `createUSDExportOptions`; `exportManager.execute(options)` | `ExportManager.htm` + the four member pages | **parameter order differs by method** (STEP/archive: filename first; STL/OBJ: geometry first) — the codegen keeps a per-format table | ○ |
| 18 | `app.importManager.createSTEPImportOptions(path)`, `createFusionArchiveImportOptions`, `createIGESImportOptions`, `createSATImportOptions`; `importManager.importToTarget2(options, component) -> ObjectCollection` | `ImportManager.htm`, `ImportManager_importToTarget2.htm` | no OBJ/STL import in the manager; importToTarget2 "cannot be used within any of the Command related events" (the bridge is not a command event) | ○ |
| 19 | `app.activeViewport.fit()`; `viewport.saveAsImageFile(filename, width, height) -> bool` | `Viewport.htm`, `Viewport_saveAsImageFile.htm` | format inferred from the extension (which extensions is NOT stated — the smoke tries `.jpg`, then `.png`); re-rendered at the requested size | ○ |
| 20 | add-in manifest keys `autodeskProduct`, `type: "addin"`, `author`, `description`, `version`, `runOnStartup`, `supportedOS`, `editEnabled`, `iconFilename` | FusionMCPSample `Fusion MCP Addin.manifest` (verbatim) | | ○ |
| 21 | `adsk.fusion.DesignTypes.DirectDesignType` (0), `.ParametricDesignType` (1) | `DesignTypes.htm` | | ○ |
| 22 | `adsk.core.Point3D.create(x, y, z)` (defaults 0.0) | `Point3D_create.htm` | | ○ |
| 23 | `adsk.core.ObjectCollection.create()`; `.add(entity)` | `ObjectCollection_create.htm` (add: the class page) | | ○ |
| 24 | `adsk.core.Matrix3D.create()` — an identity matrix | `Matrix3D_create.htm` | | ○ |
| 25 | `doc.name`, `doc.isSaved`, `doc.isModified` — read only by the lane (Law 5: `close`/`save`/`saveAs` are never called) | `Document.htm` | | ○ |
| 26 | the collection convention `.count` / `.item(i)` on Sketches, Features, BRepBodies, Occurrences, Profiles, BRepEdges, UserParameters, ParameterList | `BRepEdges.htm`, `UserParameters.htm` (read); the others are the same class family | `UserParameters.itemByName(name)` too | ○ |
| 27 | `extrude.extentOne` (gets/sets the extent) → `DistanceExtentDefinition.distance` — "the parameter controlling the distance. You can edit the distance by editing the value of the parameter object" | `ExtrudeFeature.htm`, `DistanceExtentDefinition.htm` | a `set` of `expression` on an extrude edits that parameter | ○ |
| 28 | `body.isVisible`, `sketch.isVisible` — read/write | `BRepBody_isVisible.htm`, `Sketch_isVisible.htm` | | ○ |
| 29 | `UserParameter.deleteMe()` ("only if it is a UserParameter and it is not referenced by other parameters"); `UserParameter.name` settable, must be unique | `UserParameter.htm` | | ○ |
| 30 | `STLExportOptions.unitType` (default: the design's default units), `OBJExportOptions.unitType` (default: centimetres) | `STLExportOptions.htm`, `OBJExportOptions.htm` | the enum's name was not in the page read, so v1 never SETS it: `fu_export` declares `units: cm` for obj and reads `unitType` back raw for the record | ○ |

Two facts the reference does NOT settle and the smoke must: which image
extensions `saveAsImageFile` writes (row 19), and the add-in folder on this
machine (`~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/`
per the KB, or any folder registered through Scripts and Add-Ins).

## 4. Design

### 4.1 The bridge add-in (`adapters/fusion/tee_bridge/TEE/TEE.py`, MIT)

- `run(context)`: register the custom event `tee.bridge.execute`, add the
  handler, start ONE daemon thread that binds `127.0.0.1:<port>` (default
  9881; `TEE_FUSION_PORT` env overrides) and accepts one NUL-framed JSON
  request per connection: `{"type": "execute", "code": ..., "strict_json":
  bool}` or `{"type": "ping"}`. `adsk.autoTerminate(False)` is not needed
  for an add-in (it stays resident by definition); `stop(context)` closes
  the listener and unregisters the event.
- The I/O thread never touches `adsk` beyond `fireCustomEvent`. It stores
  `(code, Event, slot)` under a uuid, fires the event with the uuid as
  `additionalInfo`, and waits on the Event (with a deadline). The handler,
  on the primary thread, pops the task, `exec`s the code in a namespace that
  carries a persistent `_tee` dict (the id map, §4.4) and a `result` dict,
  captures stdout/stderr, and sets the Event. Reply shapes are the Blender
  bridge's exactly: `{"status": "ok", "result": {...}}` /
  `{"status": "error", "message": "<traceback>"}` (+ optional stdout/stderr).
- Why exec and not declarative commands: Fusion's API IS Python, the
  primary-thread constraint makes any interpreter a queue-and-wait anyway,
  and FreeCAD's script-per-batch precedent keeps all `adsk` knowledge in the
  server's codegen where it is tested against a shim. The trust posture is
  the Blender bridge's: localhost only, not a sandbox, the escape hatch
  gated by `exec-code`.
- Not copied: the Blender bridge's `_IOLoop` is GPL-3.0-or-later (a Blender
  add-on must be); the Fusion add-in is a fresh, smaller MIT file.

### 4.2 The wire (`adapters/fusion/wire.py`)

`FusionWire(host, port, connect_timeout, call_timeout)` with `probe()` and
`execute(code, strict_json=True, timeout=None)` — the Blender wire's shape
and framing, its own codes: `fusion_unreachable` (fix: the add-in install
and start steps), `fusion_bridge_error` (the primary-thread traceback,
compacted), `fusion_bad_readback`. Per-call connections, fail fast.

### 4.3 Codegen (`adapters/fusion/codegen.py`) — one batch, one script, one JSON line

Same prelude/epilogue discipline as FreeCAD's: resolve the active design
(refuse `fusion_no_design` when `app.activeProduct` is not a Design),
apply ops in order, stop at the first failure with `{"error": {"op_index",
"message"}}`, else print `{"created", "modified", "deleted", "details"}`.
**Millimetres on the wire, centimetres inside**: every length is emitted as
`ValueInput.createByString("<n> mm")` (row 10) or divided by 10 for Point3D
sketch coordinates; every read-back multiplies cm by 10, cm² by 100, cm³ by
1000; mass stays kg. Angles are degrees on the wire (`"<n> deg"`).

| op | shape | Fusion calls (§3 rows) |
|---|---|---|
| `create sketch` | `{plane: XY\|XZ\|YZ, rects: [[x1,y1,x2,y2]...], circles: [[cx,cy,r]...]}` mm | 6, 7 |
| `create extrude` | `{sketch: id, profile: index\|"all", distance: mm, operation: join\|cut\|intersect\|new_body\|new_component}` | 8, 9, 10 |
| `create fillet` | `{body: id, radius: mm, edges: "all"}` | 11 |
| `create component` | `{}` — an empty component; also the generic fallback for any unknown kind (the kit contract's `object`), the kind kept in the component's name attribute | 12 |
| `create param` | `{value: "120 mm", units: "mm", comment}` | 13 |
| `set` | `{id, props: {name, expression (params / extrude distance), suppressed (features), visible (bodies, sketches)}}` | 13, 15 |
| `delete` | `{id}` — sketch, body, feature, occurrence, parameter | 7, 12, 13, 14, 15 |
| `param_set` | `{name, expression}` (partkiln's verb, same shape) | 13 |
| `import_file` | `{path, name}` — step/stp/f3d/igs/iges/sat into the root component | 18 |

Kinds not in v1 (named in §7): hole, chamfer, revolve, shell, sweep, loft,
sketch constraints and dimensions, joints.

### 4.4 Ids: short, prefixed, stable for the session

Fusion's stable identity is `entityToken` — long, opaque, resolvable with
`Design.findEntityByToken` (row 5). Every diff and summary row would pay for
it, so the add-in's persistent `_tee` namespace mints short ids on first
sight — `sk1`, `b1`, `f1`, `c1`, `param:width` — and keeps `id -> token`.
The listing re-derives the map (a token seen before keeps its id; a new
token gets the next id; a token that no longer resolves is dropped), so ids
are stable for the bridge's life and survive a rollback (the document is
the same document). A bridge restart renumbers; `tee_scene_summary
refresh=true` is the recovery, as for every lane.

### 4.5 Checkpoints: the timeline marker plus every parameter expression

Fusion exposes no scriptable undo. A **parametric** design has a timeline
(row 16): `snapshot()` records `{marker: timeline.markerPosition, count,
params: {name: expression for allParameters}}`; `restore()` sets the marker
back, calls `deleteAllAfterMarker()`, and re-applies every recorded
expression that still names a parameter. That restores: features, sketches,
bodies and components created after the checkpoint (deleted), and
dimensions edited since (expressions restored). It does NOT restore:
entities *deleted* after the checkpoint, or sketch geometry edited in
place — the adapter says so in `snapshot()`'s payload (`"restores":
"timeline+parameters"`) and in the lane guide. A **direct** design has no
timeline: `snapshot()` refuses `fusion_direct_design` with the fix (switch
the design to parametric, or accept no rollback).

### 4.6 Capture: the live viewport, budgeted

`viewport.fit()` then `saveAsImageFile(path, w, h)` (row 19) at the Blender
rungs (full, small, floor); the script tries `.jpg` and falls back to
`.png`, reporting which; a PNG is re-encoded to JPEG on the server (Pillow,
already a dependency of the extract extra) and the reply stays a bare
JPEG under `max_bytes` or refuses `capture_over_budget`. The viewport shows
whatever the owner has open — capture never changes the camera except
`fit()`.

### 4.7 Vocabulary (routing) and what the lane claims

```
LaneVocab(ops=("create", "set", "delete", "param_set", "import_file"),
          kinds=("sketch", "extrude", "fillet", "component", "param"),
          kind_optional=False,
          imports=("step", "stp", "f3d", "igs", "iges", "sat"),
          renders=True,
          purpose="Autodesk Fusion, live: parametric CAD in the open design; renders pixels")
```

The kinds tuple is what the lane CLAIMS for routing; the generic fallback
(any other word → a named empty component) exists for the kit contract and
is reachable with `adapter=fusion`. `test_lane_vocab.py` holds the tuple
equal to the codegen's dispatcher.

### 4.8 The `fu_*` long tail (tabled individually in `kernel/trust.py`)

| tool | capability | what |
|---|---|---|
| `fu_probe` | read-compute | bridge reachable, Fusion version, active document and design type, units, id-map size; never spawns anything |
| `fu_export` | write-artifacts | step, stl, obj, f3d, 3mf, iges, sat, usd via the ExportManager table (row 17); `of=` a body/component id or the root; `into=<lane\|auto>` lands the file through `handoff_import.land()` (units mm declared; glb is not a Fusion export, so a landing into Blender goes obj→scale from mm) |
| `fu_measure` | read-compute | volume mm³, area mm², mass kg, bbox mm, centre of mass mm for a body, a component or the root (rows 6, 14) |
| `fu_params` | read-scene | every parameter: name, expression, value (mm/deg/unitless), unit, user vs model |
| `fu_timeline` | read-scene | the history: index, name, kind, suppressed/rolled-back, health; the marker |
| `fu_execute_python` | exec-code | the escape hatch, denied unless granted; the same `result` dict convention |

Families: `("fu_", "fusion")` in `kernel/lanes.py`; no `fu_` family row in
the trust table (three writers among six — the `pk_` rule).

### 4.9 A router refinement: a lane whose application is not running is not a candidate

A68's `route_batch` intersects candidate lanes by vocabulary. Fusion is the
first lane whose vocabulary overlaps partkiln's on the words that matter
(`sketch`, `extrude`, `fillet`), so on `--adapter partkiln --adapter fusion`
every adapter-less `create sketch` would be ambiguous — even with Fusion
closed. The refinement: when several lanes take a batch and at least one of
them is connected, the disconnected ones drop out before the tie is judged
("route where the work can run"). With both live the batch is genuinely
ambiguous and refuses naming both, as A68 designed; `probe()` is only asked
when more than one lane took the batch, so the single-taker path pays
nothing. Tested in `test_lane_routing.py`.

### 4.10 CLI, config, manifest

`tee serve --adapter fusion [--fusion-port 9881]`; `.tee/config.toml`
`[fusion] port = 9881`; `ADAPTER_NAMES` gains `fusion`; `tee doctor` reports
the bridge. **The Desktop manifest is unchanged** until the lane has been
seen live (a decision, not an oversight: the manifest lists what the owner's
machine is known to serve).

## 5. Laws for this lane

1. Nothing in the codegen that is not in §3. A new call goes into the table
   with its page first.
2. Millimetres on the wire, always with the unit in the string; a read-back
   converts at the boundary, once.
3. The primary thread is the only thread that touches `adsk`; the I/O
   thread fires events and waits.
4. A checkpoint says what it restores; a refusal names the design type.
5. The owner's document is the owner's: no document is created, closed,
   saved or uploaded by the lane; exports and captures write to paths the
   caller names or the workdir.
6. Zero new always-loaded tools; every `fu_*` tool is tabled individually.
7. Nothing is claimed live until the Mac smoke ran; the shim proves the
   protocol and the codegen, not Fusion.

## 6. Phases (the script carries the acceptance)

P0 this document, the script, DECISIONS/PROGRESS. P1 the add-in and the
wire, with a protocol test that runs the add-in's framing and marshalling
against a stub executor. P2 codegen, adapter, the fake `adsk` shim that
`exec`s the generated scripts, the kit contract suite, the vocab test. P3
tools, tables, CLI, config, the router refinement, docs. P4 measured on the
shim (tokens per task against the script a model would otherwise write and
the listing it would read back), the Mac smoke procedure, PROGRESS,
CHANGELOG.

## 7. Deliberately not built (v1)

Holes, chamfers, revolves, shells, sweeps, lofts (each is one more §3 row
and one more emitter; the extrude/fillet path is the proof); sketch
constraints and dimensions (sketches are placed geometry, as in the FreeCAD
lane — parametric truth lives in user parameters and feature expressions);
joints and assemblies beyond empty components; drawings and CAM; document
management (new/open/save/close/upload — Law 5); direct-modeling rollback;
a seamkiln handoff target named `fusion`; OBJ/STL import (the ImportManager
has none, row 18); the manifest change (§4.10).

## 8. Measured

### 8.1 On the shim (P4, 2026-09-06)

`benchmarks/run_benchmarks.py::run_fusion_scenario`, recorded in
`benchmarks/RESULTS.md` under "Fusion lane: sketch, extrude, fillet, measure
(A69)". The task: a 120 × 80 × 10 mm plate with a 2 mm fillet, then its
volume and bounding box. Both arms run on `tests/fixtures_fusion.py`'s fake
`adsk`: the scripts are the ones a live Fusion receives; only the geometry
is arithmetic.

| arm | tokens | calls |
|---|---:|---:|
| naive — the model writes the Fusion API script, runs it through an execute door, reads the design back as a listing | 1,776 | 2 |
| TEE — one `tee_batch`, its diff, one `fu_measure` | 254 | 2 |
| **saved** | **85.7%** | |

The compiled batch script is 140 tokens the model never reads; the diff it
reads instead is 131. Read-back: 96,000 mm³, bbox [120, 80, 10] mm — the
number the smoke must answer before the fillet (`docs/fusion-lane.md`,
step 3). The always-loaded surface stayed at 17 tools
(`tests/test_server_lint.py`); the lane adds zero wire tokens, joining
through the Adapter protocol and six `fu_*` virtual tools. The full suite on
the P3 tree: 1,579 passed, 66 skipped, 115 deselected.

What this measures and what it does not. The naive arm's script is the one
TEE compiles, which is the fairest stand-in: a model writing it by hand
spends more tokens and, on the retired `setDistanceExtent`, sometimes gets it
wrong, so the saving is a floor on that side. It measures nothing about
Fusion itself — latency, the event hop under load, which extensions
`saveAsImageFile` writes, the OBJ's actual unit — those are the smoke's.

### 8.2 Live — the Mac smoke has not run

Every §3 row is ○ in its live column until the procedure in
`docs/fusion-lane.md` has run on the machine that has Fusion. The smoke fills
the column, answers §9, and decides the manifest (§4.10). Until then this
lane is verified against the reference and proven on the shim, and claimed
nowhere else.

## 9. Open questions for the smoke

1. Which extensions `saveAsImageFile` writes on the owner's build (jpg?
   png?) — the capture script reports which succeeded.
2. Whether `fireCustomEvent` is serviced while a modal dialog is up (the
   FreeCAD SI-B12 lesson) — the wire's call timeout is the guard, and
   `fusion_unreachable`'s fix names it.
3. The add-in folder on the owner's Mac, and whether `runOnStartup` is
   wanted (the manifest ships it `true`, as Autodesk's sample does).
