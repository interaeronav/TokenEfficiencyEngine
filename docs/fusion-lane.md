# The Fusion lane (A69)

Autodesk Fusion as a live TEE lane: the parametric CAD in the design you have
open, driven through `tee_batch`, `tee_scene_summary`, `tee_diff`,
`tee_checkpoint`, `tee_rollback` and `tee_capture`, with **no new
always-loaded tools**. Research doc 71 is the design of record; every API
call the lane makes is a reference-verified row in its section 3. v2 (A70)
added sketch constraints and dimensions, holes, chamfers, revolves, joints,
four more exports and the drawings route; its design is doc 71 §10.

Fusion has no headless mode and no Linux build. The lane is a **bridge
add-in** running inside Fusion plus an adapter in the server. It was built on
a hermetic shim and **verified live on Fusion 2704.1.53 (A71, 2026-09-06)**:
the smoke at the end of this page passed end to end over the FusionMcpBridge,
and every fact it measured is in `docs/research/71-fusion-live-facts.json`
(doc 71 §8.2 reads them out, §9 answers the questions the shim could not).

## Install an add-in (once) — either of two

The lane speaks to **whichever bridge add-in answers**: the TEE add-in
(`adapters/fusion/tee_bridge/TEE/`, TCP 127.0.0.1:9881) or the
**FusionMcpBridge** (`adapters/fusion/tee_bridge/FusionMcpBridge/`, HTTP
127.0.0.1:8766 — the add-in the owner's Mac already runs, auto-starting with
Fusion, and the one every live fact below was measured over). Install one:

```bash
cp -R adapters/fusion/tee_bridge/FusionMcpBridge \
  "$HOME/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/"
# restart Fusion; `tee doctor` reports "fusion-bridge: ... via the FusionMcpBridge on :8766"
```

or the TEE add-in:

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
tee serve --adapter fusion --project ~/work            # [--fusion-port 9881] [--fusion-http-port 8766]
tee serve --adapter fusion --adapter blender --project ~/work
tee doctor                                              # reports the bridge and which add-in answered
```

`.tee/config.toml` may carry `[fusion] port = 9881` and `http_port = 8766`.
`fu_probe` reports the port in use. Open (or create) a
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
| `create sketch` | `{"plane": "XY\|XZ\|YZ", "rects": [[x1,y1,x2,y2]], "circles": [[cx,cy,r]], "lines": [[x1,y1,x2,y2]], "points": [[x,y]], "constraints": [...], "dims": [...]}` | a sketch on an origin plane; every piece gets an address (below); inline `constraints` and `dims` take the shapes of the two ops below without `sketch`; the reply says how many closed profiles, constraints and dimensions it has and whether it is fully constrained |
| `create constraint` | `{"sketch": "sk1", "type": "horizontal\|vertical\|parallel\|perpendicular\|collinear\|equal\|tangent\|concentric\|coincident\|midpoint\|symmetry", "of": ["r0.bottom"]}` | one `geometricConstraints.add*` call; arity by type (coincident is a point then an entity; symmetry two entities then the line); not an entity — the sketch row counts them |
| `create dimension` | `{"sketch": "sk1", "type": "distance\|diameter\|radius\|angle", "of": ["r0.bl", "r0.br"], "orientation": "aligned\|horizontal\|vertical", "expression": "width", "text": [x,y], "driving": true}` | a sketch dimension; an entity `dim1` (parent the sketch) whose `expression` binds a user parameter — the parametric truth |
| `create extrude` | `{"sketch": "sk1", "distance": 10, "operation": "join\|cut\|intersect\|new_body\|new_component", "profile": "all"\|0}` | `setOneSideExtent` with a `DistanceExtentDefinition` (the retired `setDistanceExtent` is never used); a negative distance extrudes the other way; `new_component` also reports the `c{n}` Fusion made |
| `create revolve` | `{"sketch": "sk1", "axis": "x\|y\|z" or "sk1/r0.bottom", "angle": 360, "symmetric": false, "operation": ..., "profile": ...}` | a revolve about a root construction axis or a sketch line, through an angle in degrees |
| `create hole` | `{"body": "b1", "face": "+z", "at": [u, v] or [x, y, z], "diameter": 6.6, "depth": 10 or "through": true, "type": "simple\|counterbore\|countersink", "cbore_diameter", "cbore_depth", "csink_diameter", "csink_angle", "flip": false}` or `{"point": "sk2/p0", ...}` | a hole placed on a face at a point Fusion projects onto it, or on a sketch point; `setDistanceExtent` (not retired for holes) or through-all; `flip` reverses the direction; the feature reports `diameter_mm` and `position_mm`, and `set` on it with `expression` re-bores |
| `create fillet` | `{"body": "b1", "radius": 2, "edges": "all" or {"face": "+z"}}` | a constant-radius fillet on every edge of the body, or of one face; tangent chains on |
| `create chamfer` | `{"body": "b1", "distance": 1, "edges": "all" or {"face": "+z"}}` | an equal-distance chamfer through `createInput2` (the retired `createInput` is never used); the reply says how many edges it took |
| `create joint` | `{"one": {"component": "c1", "face": "+z"} or {"component": "c1"} or {"body": "b1", "face": "+z"}, "two": {...}, "motion": "rigid\|revolute\|slider\|cylindrical\|pin_slot\|planar\|ball", "axis": "z", "slide": "x", "angle": 0, "offset": 0, "flip": false}` | a joint between two components: geometry at the centre of a planar face of the occurrence's body, or at its origin; an entity `j1` reporting motion, the two components, angle, offset and, where the motion has them, rotation and slide |
| `create component` | `{}` | an empty named component; any other `kind` word does the same and the kind is remembered |
| `create param` | `{"value": "120 mm", "units": "mm", "comment": ""}` | a user parameter |
| `set` | `{"id": ..., "props": {"name", "expression", "suppressed", "visible", "angle", "offset", "flipped", "rotation", "slide"}}` | `expression` edits a user parameter, a dimension, an extrude's distance or a hole's diameter; `suppressed` a feature or joint; `visible` a body or sketch; on a joint `angle` (deg) and `offset` (mm) are its parameters, `flipped` its direction, `rotation` (deg) and `slide` (mm) drive a revolute / cylindrical / pin-slot or slider joint |
| `delete` | `{"id": ...}` | sketch, body, feature, component, dimension, joint or user parameter |
| `param_set` | `{"name": "width", "expression": "120 mm"}` | partkiln's verb, the same shape |
| `import_file` | `{"path": "part.step", "name": "insert"}` | STEP, IGES, SAT or f3d into the root component; meshes are not Fusion imports |

Ids are short and stable for the life of the **document** — `sk1`, `f1`,
`b1`, `c1`, `dim1`, `j1`, `param:width` — minted over Fusion's `entityToken`
and keyed by the document's `creationId`. A bridge restart or a switch to
another document renumbers; `tee_scene_summary(adapter=fusion, refresh=true)`
is the recovery, as for every lane. The key is a measured law, not a
preference: resolving a token minted in a design you have since closed
crashes Fusion (doc 71 row 54), so the lane never does.

## Addresses and faces (v2)

Sketch geometry has **addresses**, minted as it is made and kept for the
bridge's life: a rectangle's sides `r0.bottom | top | left | right` and its
corners `r0.bl | br | tl | tr` — named by where they lie, because the API
does not say in which order it returns a rectangle's lines — explicit lines
`l0` with `.start` / `.end`, circles `c0` with `.center`, points `p0`, and
`origin`. Inside the sketch op they are bare; outside it they are prefixed
`sk1/` or the op names `sketch`. A miss is one refusal listing what the
sketch does have.

A face has no id; it is named by its **outward normal** — `+z` is the top
face of a plate — the outermost planar face facing that way (or, with a
3-vector `at`, the one nearest it). A body with no such face refuses
`fusion_no_face` naming the ones it has: a cylinder has only `+z` and `-z`.
Holes, chamfer and fillet edge sets and joint geometry all use it.

What the shim models and what Fusion said: the shim solves rectangles and
circles (a dimension bound to `width` really re-sizes the plate and
everything extruded from it — Fusion agrees, and recomputes on `param_set`),
subtracts what a hole bores (Fusion agrees, and a face-placed hole bores
**into the material by default**; `flip` stays for the other way), revolves
by Pappus (Fusion agrees to the millimetre cubed) and records joints without
moving anything — **Fusion moves the second component, `two`**, onto the
first. A bare rectangle carries no constraints of its own; a dimensioned one
reads `constrained: true`. Two things the shim cannot show and the smoke did:
a rollback really restores a joined body's volume, and a join of material
already inside a body adds nothing.

One diff-reading rule the joint step taught: the kernel drops detail fields
that merely echo the op (hard rule 2), so a lone `create joint` returns its
row without `kind`, `name` or `motion` — take the id from `created`.

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
Blender rungs, at most two renders per capture, under `max_kb`. Fusion
2704.1.53 writes `.jpg` directly (measured); the `.png` fallback and its
re-encode stay for a build that refuses JPEG. The reply is a bare JPEG as on
every lane. Text first: `fu_measure` and the diffs are the evidence; pixels
are for when you need to see it.

## The `fu_*` tools (behind `tee_search_tools`)

| tool | what |
|---|---|
| `fu_probe` | bridge reachable, version, active document, design type, counts, the id map — never starts anything |
| `fu_measure {of?}` | volume mm³, area mm², mass kg, centre of mass and bbox in mm of a body, a component or the root |
| `fu_params` | every parameter: name, expression, unit, value; user or model |
| `fu_timeline` | the history with suppressed / rolled-back flags and health, and the marker |
| `fu_export {format, out, of?, into?}` | step, stl, obj, f3d, iges, sat, 3mf or usd; `into=<lane\|auto>` lands the file in a served scene lane as one checkpointed batch with a read-back verdict (an OBJ into Blender scales from Fusion's centimetres — measured live: 0.11 s, then a Blender capture in 0.05 s); step / f3d / iges / sat / usd export a component or the whole design, never a body; usd lands at `<out>.usdz` |
| `fu_drawing {out, of?, name?, sheet?, standard?, angle?, scale?, views?, dims?, hole_table?, formats?}` | a dimensioned sheet **through partkiln**: the Fusion API cannot create a drawing (doc 71 row 49), so the lane exports STEP, imports it into the served partkiln lane and writes the sheet with `pk_drawing`, every dimension read from the model; needs `--adapter partkiln`, and the import is decided as the scene write it is |
| `fu_design_stats` | one health read of the whole design: bodies, total volume and mass, the overall bbox in mm, bodies still called `Body1`, non-solid bodies, **overlapping body pairs**, feature and suppressed counts, and every timeline item Fusion marks warning or error — measured live at ~80 tokens for a two-body design, and it names a real overlap before any pixel is spent |
| `fu_search_docs {query, limit?}` | search the API of **the Fusion you are connected to** — introspected live from `adsk.core` and `adsk.fusion`, cached on disk per version, searched server-side. Measured on 2704.1.53: **13,498 symbols indexed in 0.2 s**, a cached search in 0.007 s. The cure for a hallucinated call, because it answers from this build rather than from memory |
| `fu_api_detail {path}` | one symbol in full from the live build: docstring, signature and, for a class, its members. Follows a `fu_search_docs` hit |
| `fu_execute_python {code}` | the escape hatch — registers only with `--allow-code-exec`, and the trust kernel decides it per call |

What each export declares, **measured on Fusion 2704.1.53** (A71): STEP
and f3d carry their own units (mm) and take a **component or the whole
design, never a body** — Fusion refuses one with `3 : invlid argument
geometry`, so `fu_export of=b1` on them is refused before the wire; OBJ is
written in centimetres (a 120 mm plate spans 12 units); STL carries no unit
and follows the design's default length unit, which `fu_export` **reads from
the design** at export time and declares (`mm` on this design) rather than
guesses; IGES declares MM in its global section, SAT one millimetre per unit
in its header, 3MF `unit="millimeter"` — all three declare `mm`; USD is a
**USDZ package** written at `<out>.usdz` (Fusion appends the suffix; the path
`fu_export` returns is the file that exists), one binary usdc declaring
`metersPerUnit` — a value the lane cannot read without the USD library, so
USD alone keeps `units: null`.

The index reports what the build HAS, which is not always what the reference
says is current: `setDistanceExtent` is retired (doc 71 row 8) and is still
exported by 2704.1.53. The codegen never emits it; the index never hides it.

## Beside partkiln

Fusion and partkiln share the words that matter — `sketch`, `extrude`,
`fillet`. On a server holding both, a batch with no `adapter=` goes to the
one whose application is **running**; with both live it is genuinely
ambiguous and is refused naming both (pass `adapter=`). partkiln is
headless and deterministic and owned by TEE; Fusion is your open document.

## The smoke (run where Fusion is)

`tests/test_fusion_live.py` drives every step below in one sitting and
writes `fusion-live-facts.json`; it skips unless a bridge answers and an
**empty** parametric design is active, so it can never touch your work:

```bash
cd server
# Fusion open, nothing open in it: let the harness open and close a scratch design
TEE_FUSION_SCRATCH_DESIGN=1 UV_FROZEN=1 uv run pytest -q -s -m dcc tests/test_fusion_live.py
```

A71 ran it on Fusion 2704.1.53: **2 passed in 7.8 s**, 30 facts
(`docs/research/71-fusion-live-facts.json`). By hand, the steps are:

1. Run an add-in; confirm it in the Text Commands palette (TEE add-in) or
   with `tee doctor` (FusionMcpBridge).
2. Open a parametric design. `tee serve --adapter fusion`; `fu_probe`.
3. One `tee_batch`: a 120×80 mm rectangle sketch, a 10 mm extrude, a 2 mm
   fillet. `fu_measure` should answer 96,000 mm³ before the fillet.
4. `tee_checkpoint`, a second extrude, `tee_rollback`, `tee_capture`.
5. `fu_export format=step` (the whole design or a component), and
   `format=obj into=blender` with a Blender lane served.
6. Record which image extension the capture used and the OBJ's actual unit
   in doc 71 section 3's live column *(done: `.jpg`, centimetres)*.
7. *(v2)* A rectangle with inline constraints and two distance dimensions
   bound to `width` / `height` user parameters; `param_set width`;
   `fu_measure` should follow. Note the sketch row's `constraints` count
   before you add any: it says whether `addTwoPointRectangle` added
   horizontal / vertical constraints of its own (doc 71 §9 item 7).
8. *(v2)* One through hole on `+z` (`at: [20, 20]`, Ø6.6); `fu_measure`
   should drop by π·3.3²·10 mm³ — if it does not, the hole went the other
   way and `flip: true` is the answer to §9 item 4. Then a counterbore.
9. *(v2)* A chamfer with `edges: {face: "+z"}` (four edges); a revolve of a
   rectangle about `x`.
10. *(v2)* Two `new_component` extrudes and a revolute joint about `z`
    between their faces; note which component moved (§9 item 5);
    `set j1 rotation=45`.
11. *(v2)* `fu_export` iges, sat, 3mf and usd — open each and record the
    unit it declares (§9 item 6); `fu_drawing` with a partkiln lane served.

## Not yet

Shells, sweeps, lofts, threads and tapped holes, sketch arcs and splines,
joint origins and as-built joints, motion links, rigid groups (each one more
verified row and one more emitter — v2's additions are the proof the shape
holds); drawings made by Fusion itself (its API cannot: doc 71 row 49) and
the PDF export of a drawing you have open (verified, waiting for a smoke
that can open one); CAM; document management; direct-modeling rollback;
OBJ/STL import (Fusion's ImportManager has none). Not yet seen live: a
fillet (row 11), an import into Fusion (row 18), and the TEE add-in's own
primary-thread hop — every live fact so far came through the FusionMcpBridge.
