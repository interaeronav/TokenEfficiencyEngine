# The Fusion lane (A69)

Autodesk Fusion as a live TEE lane: the parametric CAD in the design you have
open, driven through `tee_batch`, `tee_scene_summary`, `tee_diff`,
`tee_checkpoint`, `tee_rollback` and `tee_capture`, with **no new
always-loaded tools**. Research doc 71 is the design of record; every API
call the lane makes is a reference-verified row in its section 3.

Fusion has no headless mode and no Linux build. The lane is a **bridge
add-in** running inside Fusion plus an adapter in the server, and it was
built and tested on a hermetic shim — the live half is the smoke at the end
of this page, run on the machine that has Fusion.

## Install the add-in (once)

1. `adapters/fusion/tee_bridge/TEE/` is the add-in: `TEE.py` and
   `TEE.manifest`. Copy the folder into Fusion's add-ins folder
   (macOS: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/`;
   Windows: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\`), or in
   Fusion open **Utilities → Add-Ins → Scripts and Add-Ins** and use the
   green **+** to point at the folder where it lives in this repo.
2. Select **TEE** in the Add-Ins tab and **Run** (it is marked *Run on
   Startup*). The Text Commands palette (`Shift+S` opens Scripts and Add-Ins;
   the palette is under Utilities) logs `TEE bridge listening on
   127.0.0.1:9881`. `TEE_FUSION_PORT` in Fusion's environment moves it.
3. The add-in binds **127.0.0.1 only** and, like the Blender bridge, is not
   a sandbox: it executes what TEE sends. TEE's typed batches are the
   default path; arbitrary code reaches it only through `fu_execute_python`,
   which is `exec-code` and denied unless the project grants it.

## Serve

```bash
tee serve --adapter fusion --project ~/work            # [--fusion-port 9881]
tee serve --adapter fusion --adapter blender --project ~/work
tee doctor                                              # reports the bridge
```

`.tee/config.toml` may carry `[fusion] port = 9881`. Open (or create) a
design in Fusion first: the lane works in the **active design** and never
creates, saves, closes or uploads a document. `fu_probe` answers whether the
bridge is up, which document is active and whether the design is
parametric.

## Units: millimetres on the wire, always with the unit

Fusion's internal units are centimetres and radians, and a unitless
expression takes the *document's* active unit, which TEE cannot know. So
every length TEE sends carries `mm` in the string (`"10 mm"`), sketch points
are converted to centimetres, and every read-back is converted once at the
boundary: `volume_mm3`, `bbox_mm`, `area_mm2`, `distance_mm`; mass stays in
kilograms.

## The typed ops (`tee_batch`)

| op | shape (mm) | what Fusion does |
|---|---|---|
| `create sketch` | `{"plane": "XY\|XZ\|YZ", "rects": [[x1,y1,x2,y2]], "circles": [[cx,cy,r]]}` | a sketch on an origin plane with rectangles and circles; the reply says how many closed profiles it has |
| `create extrude` | `{"sketch": "sk1", "distance": 10, "operation": "join\|cut\|intersect\|new_body\|new_component", "profile": "all"\|0}` | `setOneSideExtent` with a `DistanceExtentDefinition` (the retired `setDistanceExtent` is never used); a negative distance extrudes the other way |
| `create fillet` | `{"body": "b1", "radius": 2}` | a constant-radius fillet on every edge of the body, tangent chains on |
| `create component` | `{}` | an empty named component; any other `kind` word does the same and the kind is remembered |
| `create param` | `{"value": "120 mm", "units": "mm", "comment": ""}` | a user parameter |
| `set` | `{"id": ..., "props": {"name", "expression", "suppressed", "visible"}}` | `expression` edits a user parameter or an extrude's distance; `suppressed` a feature; `visible` a body or sketch |
| `delete` | `{"id": ...}` | sketch, body, feature, component or user parameter |
| `param_set` | `{"name": "width", "expression": "120 mm"}` | partkiln's verb, the same shape |
| `import_file` | `{"path": "part.step", "name": "insert"}` | STEP, IGES, SAT or f3d into the root component; meshes are not Fusion imports |

Ids are short and stable for the bridge's life — `sk1`, `f1`, `b1`, `c1`,
`param:width` — minted over Fusion's `entityToken`. A bridge restart
renumbers; `tee_scene_summary(adapter=fusion, refresh=true)` is the
recovery, as for every lane.

A malformed op is refused before anything crosses the wire (`bad_op`,
`bad_kind`, naming the shape); Fusion's own failure comes back as one
refusal naming the op index and Fusion's message, and nothing after it ran.

## Checkpoints: what a rollback restores, and what it cannot

Fusion has no scriptable undo. A checkpoint is the **timeline marker plus
every parameter expression**; a rollback sets the marker back, deletes
everything created after it (features, sketches, bodies, components) and
puts the recorded expressions back. It does **not** restore entities you
deleted after the checkpoint, sketch geometry edited in place, or user
parameters added since — the checkpoint payload says so. A
**direct-modeling** design has no timeline: `tee_checkpoint` refuses
`fusion_direct_design` with the fix (Design Settings → Capture Design
History).

## Pixels

`tee_capture adapter=fusion` fits the live viewport and saves it at the
Blender rungs, at most two renders per capture, under `max_kb`. Fusion writes
the format its build supports — the add-in tries `.jpg` and falls back to
`.png`, which the server re-encodes — and the reply is a bare JPEG as on
every lane. Text first: `fu_measure` and the diffs are the evidence; pixels
are for when you need to see it.

## The `fu_*` tools (behind `tee_search_tools`)

| tool | what |
|---|---|
| `fu_probe` | bridge reachable, version, active document, design type, counts, the id map — never starts anything |
| `fu_measure {of?}` | volume mm³, area mm², mass kg, centre of mass and bbox in mm of a body, a component or the root |
| `fu_params` | every parameter: name, expression, unit, value; user or model |
| `fu_timeline` | the history with suppressed / rolled-back flags and health, and the marker |
| `fu_export {format, out, of?, into?}` | step, stl, obj or f3d; `into=<lane\|auto>` lands the file in a served scene lane as one checkpointed batch with a read-back verdict (an OBJ into Blender scales from Fusion's centimetres) |
| `fu_execute_python {code}` | the escape hatch — registers only with `--allow-code-exec`, and the trust kernel decides it per call |

STEP and f3d declare their units; OBJ is written in Fusion's default of
centimetres; STL takes the design's default units, so `fu_export` declares
none for it rather than guess.

## Beside partkiln

Fusion and partkiln share the words that matter — `sketch`, `extrude`,
`fillet`. On a server holding both, a batch with no `adapter=` goes to the
one whose application is **running**; with both live it is genuinely
ambiguous and is refused naming both (pass `adapter=`). partkiln is
headless and deterministic and owned by TEE; Fusion is your open document.

## The smoke (run where Fusion is)

1. Run the add-in; confirm the listening line in the Text Commands palette.
2. Open a parametric design. `tee serve --adapter fusion`; `fu_probe`.
3. One `tee_batch`: a 120×80 mm rectangle sketch, a 10 mm extrude, a 2 mm
   fillet. `fu_measure` should answer 96,000 mm³ before the fillet.
4. `tee_checkpoint`, a second extrude, `tee_rollback`, `tee_capture`.
5. `fu_export format=step`, and `format=obj into=blender` with a Blender
   lane served.
6. Record which image extension the capture used and the OBJ's actual unit
   in doc 71 section 3's live column.

## Not in v1

Holes, chamfers, revolves, shells, sweeps, lofts; sketch constraints and
dimensions (sketches are placed geometry, as in the FreeCAD lane —
parametric truth lives in user parameters and feature expressions); joints;
drawings and CAM; document management; direct-modeling rollback; OBJ/STL
import (Fusion's ImportManager has none). Each is one more verified row and
one more emitter.
