I have what I need. Writing the report.

# TASK E2 — Reuse map for a mechanical/parametric CAD lane

All paths relative to `/Users/john/TokenEfficiencyEngine`.

---

## 1. `fleet/cad.py` + `fleet/_cad_worker.py` — the OCCT sidecar

**Three tools, registered as virtual (zero always-loaded cost)** at `server/src/tee/fleet/tools.py:453` (`cad_scad_build`), `:497` (`cad_measure`), `:507` (`cad_probe`); handlers are lazy-import closures at `tools.py:122-136` (`from tee.fleet import cad` *inside* the function — this is the A46 P2b no-blocking-import pattern). Trust capabilities tabled at `server/src/tee/kernel/trust.py:293-295` (`write-artifacts` / `read-compute` / `read-compute`) — **a tool the trust table does not know fails at server startup** (`kernel/registry.py:37-42`).

| Tool | What it does | Key file:line |
|---|---|---|
| `cad_scad_build` | Runs the OpenSCAD **binary** (`shutil.which("openscad")`, `cad.py:52`) as a subprocess, exports stl/binstl/asciistl/3mf/off/amf/dxf/svg/csg (`cad.py:41`), returns `{ok, format, path, bytes, wall_s, facets, volumes, warnings}` — never geometry. Parameters go only through OpenSCAD customizer JSON `-p/-P` with identifier-validated names and scalar-only values (`cad.py:68-99`, `142-146`). | `cad.py:102-192` |
| `cad_measure` | Binary STL measured **in TEE with zero dependencies** by signed-tetrahedron volume + cross-product area + bbox (`cad.py:322-384`). STEP/STP/BREP go to CadQuery in-process if importable, else the sidecar (`cad.py:215-294`). Returns volume/area/bbox/valid/engine/wall_s, all rounded to 6dp. | `cad.py:297-319` |
| `cad_probe` | OpenSCAD presence+version, cadquery `probe_rows`, formats, install fix lines. | `cad.py:387-409` |

### The sidecar interpreter pattern

- **Location**: `SIDECAR_PY = Path.home() / "TEE" / ".tee" / "sidecars" / "cad" / "bin" / "python"` (`cad.py:206`); overridable per call via `spec["cad_python"]` (`cad.py:209-212`).
- **Spawn**: `subprocess.run([str(py), str(worker)], input=json.dumps({"path": ...}), capture_output=True, text=True, timeout=BUILD_TIMEOUT)` where `worker = Path(__file__).parent / "_cad_worker.py"` (`cad.py:254-262`). `BUILD_TIMEOUT = 300.0` (`cad.py:43`) is shared by OpenSCAD builds and sidecar calls.
- **Contract**: "*JSON on stdin, exactly one JSON object on stdout. Native chatter is swallowed at the descriptor level so it can never corrupt that*" (`_cad_worker.py:21-23`). The fd swap is `os.dup(1)` → `os.dup2(tmp.fileno(), 1)` → restore (`_cad_worker.py:63-77`). The worker "**deliberately imports nothing from `tee`**, so the parent can invoke it by path from any environment" (`_cad_worker.py:19-20`). Same shape as `fleet/_cpsat_worker.py` (which exists because ortools and highspy each bundle `libhighs` and import order decides which resolves — `_cpsat_worker.py:1-22`).
- **Why it exists** (`_cad_worker.py:4-12`): vtkmodules 592 MB + OCP 225 MB + casadi 159 MB + llvmlite 129 MB = **1.1 GB for volume, area, bbox and validity**.
- **First-import cost**: `CadQuery FIRST import : 140 s <- the problem` (`CLAUDE_A46_SCRIPT.md:36`); `docs/setup-fleet.md:166` — "*CadQuery is ~1.3 GB and its **first** import takes ~140 s while Python compiles OCP's bytecode. Warm imports are ~1.1 s.*" Rebuild cost after purge: `~150 s, needs network` (`server/src/tee/purge.py:81`); `purge.py:78-88` classifies `sidecars` as "*a CAPABILITY, not garbage*" and excludes it from `DEFAULT_CATEGORIES`.

### **Can the sidecar host a whole CAD session? No — not as written.**

It is strictly **request/response, one shot per call**: `subprocess.run(...)` blocks, the worker's `main()` does `json.loads(sys.stdin.read())` → one `sys.stdout.write(json.dumps(result))` → `return 0` (`_cad_worker.py:56-79`), and `_measure()` re-imports `cadquery` on every invocation (`_cad_worker.py:34`). **Every call would pay the OCP import** (140 s cold, ~1.1 s warm-page-cache). A feature-tree CAD lane needs a **persistent** sidecar (long-lived process, newline-delimited JSON request/response loop, handle-keyed shape registry), which is a new mechanism — but the fd-swallowing, no-`tee`-imports, JSON-line contract, and `_sidecar_python()` discovery are all directly copyable. Note: `cadquery 2.8.0` + `OCP` import cleanly from `server/.venv` today (verified), so in-process is available in the dev env and `_measure_step` already prefers it (`cad.py:217`, reporting `"where": "in-process"` vs `"sidecar"`).

---

## 2. `adapters/freecad/` — typed ops, batch→one-script, dimension read-back, checkpoints

**Seven kit methods** per `docs/adapter-kit.md:41-88`: `info / probe / list_entities / execute / snapshot / restore / capture`. FreeCAD implements all of them in `adapter.py:38-191`.

### Typed op shapes (`codegen.py`)
- `PRIMITIVES = {"box": "Part::Box", "cylinder": "Part::Cylinder", "sphere": "Part::Sphere", "cone": "Part::Cone", "part": "App::Part"}` (`codegen.py:28-34`); `KNOWN_KINDS = (*PRIMITIVES, "sketch", "pad", "pocket")` (`:35`). Props are raw FreeCAD attribute names; `"at"` is special-cased to `Placement.Base` (`codegen.py:87-89`, and again for `set` at `:246-248`).
- `sketch`: `{plane: XY|XZ|YZ, points, lines, constraints}` → `Sketcher::SketchObject` + `Part.LineSegment` per line at **final solved coordinates** (`codegen.py:154-187`). Plane→Placement rotations are hard-coded at `:167-174`.
- `pad`: `{sketch: id, length: mm}` → `Part::Extrusion` with `DirMode='Normal'; Solid=True; LengthFwd=length`, base hidden (`codegen.py:190-207`).
- `pocket`: `{sketch: id, target: id, depth: mm}` → a tool `Part::Extrusion` (`LengthFwd=depth; LengthRev=1.0`) plus `Part::Cut` of `target` (`codegen.py:210-230`).
- Any other alnum word → `App::FeaturePython` with dynamic typed properties and a `tee_kind` string (`codegen.py:125-151`) — the generic metadata/assembly/jig carrier.

### Batch-compiles-to-one-script
`compile_batch(doc, ops)` (`codegen.py:233-276`) emits `_OP_ERROR` class + `_PRELUDE` + per-op body + `_EPILOGUE`. "*One tee_batch compiles to ONE Python script executed in ONE bridge round trip … applies ops in order, recomputes ONCE, and prints a single JSON diff; the first failing op prints a JSON error and stops*" (`codegen.py:3-7`). The diff details harvested per created/modified object are `Length/Width/Height/Radius/LengthFwd` + `faces` + `volume_mm3` (`codegen.py:41-49`); `LIST_CODE` (`codegen.py:279-301`) does the same for `list_entities` plus rounded `Placement.Base`. Wire: `FreeCADWire.py_json` runs code that prints one JSON line and parses the last `{`/`[` line (`wire.py:121-135`); XML-RPC to `127.0.0.1:9875` with a real socket timeout (`wire.py:17`, `25-34`, default `timeout_s=60.0`).

### The drawing dimension read-back lesson
`adapters/freecad/tools.py:75-79`: "*A dimension created in the same dispatch as its view binds before the view's projection exists and **CACHES 0.0** (verified live on 1.1.3: dispatch1 = 0.0, plain dispatch2 = 0.0, dispatch2 after touch+recompute = the true value). The read-back is therefore a second call that touches the dims first.*" `_READBACK_CODE` (`tools.py:80-93`) does `d.touch()` for every dim → `doc.recompute()` → `d.getRawValue()`. Two-call sequence at `tools.py:131-150`. `ExtentX`/`ExtentY` use `TechDraw.makeExtentDim(view, [], 0|1)` so **no edge refs need guessing** (`tools.py:59-62`). SVG/PDF export is GUI-bound (upstream #5710) via `TechDrawGui.exportPageAsSvg/Pdf`; DXF via `TechDraw.writeDXFPage` works headless (`tools.py:267-286`).

### Checkpoint via saveCopy
`snapshot()` sanitises the label to `[A-Za-z0-9_]{,40}`, writes `<spill>/<label>.FCStd` via `FreeCAD.getDocument(doc).saveCopy(path)` (`adapter.py:142-147`); spill dir is `tempfile.mkdtemp(prefix="tee-freecad-cp-")` per session (`adapter.py:137-140`). `restore()` closes the doc, `openDocument(path)`, `recompute()` (`adapter.py:149-164`); missing file → `freecad_checkpoint_gone` with "*The spill dir is per-session; roll back within the session.*"

### Sketch-solved-before-DCC wiring
`adapter._prepare()` intercepts `op=="create" and kind=="sketch"`, calls `tee.physical.sketch.solve_sketch`, and injects `props["_solved_points"]` (`adapter.py:114-133`). Rationale at `adapter.py:7-10`: "*closure is by construction, never by hoping a DCC solver converges from guesses.*"

---

## 3. `physical/` — sketch solver, rule tables, materials

### `sketch_solve` (`physical/sketch.py`)
- Entry: `solve_sketch(sketch) -> {"ok": True, "points": {id: [x, y]}, "dof": n, "under_constrained"?: str}` (`sketch.py:32`, return at `:207-216`); helper `polygon_from(solved, order)` (`sketch.py:219-224`).
- **Contract units: "all lengths meters, angles degrees"** (`sketch.py:5`) — but the FreeCAD adapter feeds it millimetres as bare numbers and notes "*the solver is unit-agnostic*" (`adapter.py:7-8`). **This unit contradiction is the single sharpest trap for a new CAD lane.**
- Constraint kinds: `distance, horizontal, vertical, angle, parallel, perpendicular, equal_length, coincident` (`sketch.py:120-178`). Points may be `fixed: true` → they go in the base group and are returned verbatim (`sketch.py:72-80`, `199-202`).
- DOF policy: `free_allowance = 0 if anchored else 3  # translation x2 + rotation` (`sketch.py:209`). Docstring at `:20` says "*2 DOF … is normal*" — inconsistent with the code's 3; minor, but a copier should read the code.
- Failure taxonomy: `_RESULT = {0: "ok", 1: "inconsistent", 2: "didnt_converge", 3: "too_many_unknowns"}` (`sketch.py:29`); over-constrained names the offending constraints by `[index] kind` label (`sketch.py:98`, `179`, `183-190`).
- **Dependency**: `py_slvs` (the SolveSpace wheel), lazy-imported with a rule-6 error `physical_extra_missing` → `uv sync --extra physical` (`sketch.py:34-40`). Declared as `py-slvs>=1.0.6` in the **`[physical]` extra** alongside `ifctester` (`server/pyproject.toml:44-47`).
- Registered as VirtualTool `sketch_solve` at `physical/tools.py:295-309`.
- Tests: `server/tests/test_physical_core.py:16-88` — `RECT` fixture (4 points / 4 lines / 6 constraints), closure asserted to `abs=1e-4` (`:40-46`), over-constrained names the kind and the fix (`:49-62`), under-constrained reports DOF (`:65-73`), `polygon_from` (`:76-81`), unknown point ref (`:84-88`).

### `physical/plaus.py` — rule-table + severity pattern
- Posture (`plaus.py:1-7`): "*findings, never approvals … FLAGGING against cited prescriptive tables restates the code; APPROVING or SIZING would be engineering practice. So: findings carry source + severity + the exact delta; there is no member sizing and no 'passes' state*."
- Severities: `_SEVERITY_ORDER = ("CONV", "HEUR", "STD", "CODE")` (`plaus.py:86`) — CONV < HEUR < STD < CODE, and a jurisdiction profile's `max_severity` **caps** what any rule may claim, visibly (`severity_capped_from`, `jurisdiction.legal_basis` stated once per response, `plaus.py:24-27`).
- Data: `physical/data/plaus_rules.json` (14 KB), 22 rules + `_meta` + `_jurisdiction_profiles`. Each rule = `{severity, source, <threshold fields>, finding}` (+ optional `rule_set`, `by_jurisdiction` overlay). `_resolved_table()` folds `by_jurisdiction[rule_set]` onto the base and drops foreign rule-sets (`plaus.py:134-148`). Loaded once via `@cache rules()` from `importlib.resources` (`plaus.py:151-154`).
- Dispatch: one `elif cls == ...` arm per element class with an inline `hit(rule_key, element_id, detail, severity=?, source=?)` closure (`plaus.py:168-178`, arms from `:184`). Not-in-table inputs degrade to `severity="CONV"` + "*not checkable*" rather than silence (`plaus.py:190-197`).
- Family-match lesson: `_is_masonry` (`plaus.py:78-83`) — "*the exact-name check silently skipped 'clay_brick' and 'concrete_block' walls (a 60 m clay_brick wall sailed through slenderness)*".
- Unknown region raises rather than defaults (`plaus.py:115-131`).

### `physical/materials.py` + `data/materials_eng.json`
Three tiers per material, **every leaf carries `value / unit / source / honesty`**, honesty ∈ `{measured, standard_value, typical_range, derived, game_plausible}` (`materials_eng.json` `_meta.tiers`). Top-level material fields: `aliases[]`, `physics{density, friction, restitution}`, `engineering{...}`, `render_ref`. Seven materials: `concrete_c25, steel_s275, timber_c24, brick_masonry, glass_soda, gypsum_board, soil_firm`.

Sample row (`concrete_c25`):
```
aliases: ["concrete","rc concrete"]
physics.density     2400 kg/m3   src "EN 1991-1-1 Table A.1 (reinforced 2500)"  honesty standard_value
physics.friction    0.7  -       src "concrete-on-concrete typical"             honesty typical_range
physics.restitution 0.1  -       src "convention"                               honesty game_plausible
engineering.fck     25 MPa       src "EN 206 / EC2 C25/30 characteristic cylinder" honesty standard_value
engineering.E       31 GPa       src "EC2 Table 3.1 Ecm for C25/30"             honesty standard_value
render_ref: "Concrete"
```
API: `find(query)` alias/substring lookup (`materials.py:33-47`), `facts(query)` returns all tiers + `engine_caveats` (`:50-67`), `assign_ops(entity_id, query, volume_m3=)` → typed ops + a `material_fact` payload carrying per-leaf `sources` and `honesty` maps, `friction_body_sqrt`, and `mass_kg = volume × density` (`:79-134`). `banned_bulk_sources`: NIST SRD (15 USC 290e), MatWeb, MakeItFrom, ArcSim cloth data — `materials.py:29-30`, data at `_meta.banned_bulk_sources`. Range values are reduced to the midpoint with the range recorded in `density_note` (`materials.py:70-76`).

### `physical/joinery.py` — rule-check pattern, tightest template for a mech-CAD checker
`RULES: dict[str, dict[str, str]]` where each entry is `{severity: "ERROR"|"WARN", source: <citation>, verified: <A30 re-verification stamp>}` (`joinery.py:24-67`). `hit()` copies `severity/source/verified` onto every finding (`joinery.py:78-90`). Return shape (`joinery.py:264-273`): `{ok: not errors, findings, not_evaluated, rules_total, rules_evaluated, note}`. **Data-honesty rule** (`joinery.py:9-11`): "*a rule whose input the model simply does not carry … answers `not_evaluated` with the reason — silence is never conformance.*" Units: "*millimetres throughout (the lane convention)*" (`joinery.py:13`).

---

## 4. `pdf.py` — the `pdf_compose` lane

- `BLOCK_KINDS = ("heading", "paragraph", "image", "table", "page_break", "spacer")` (`pdf.py:32`). **No vector/line/path/SVG block kind exists.**
- Page geometry is **hardcoded A4 portrait**: `PAGE_W_MM = 210.0`, `MARGIN_MM = 15.0`, `CONTENT_W_MM = 180.0` (`pdf.py:35-37`); `FPDF(format="A4", unit="mm")` (`pdf.py:232`). No page-size or landscape parameter — a drawing-sheet lane must add one.
- **No title block.** The only chrome is an optional page-number footer installed before the first `add_page` (`pdf.py:271-282`) and PDF outline bookmarks per heading via `doc.start_section` (`pdf.py:306-307`). Metadata setters: title/author/subject/keywords/creator (`pdf.py:254-267`).
- Images are re-encoded to JPEG (`_jpeg_bytes`, `pdf.py:191`) and clamped to `CONTENT_W_MM` (`pdf.py:328-330`). Tables are equal-width bordered `cell()` grids (`pdf.py:336-355`).
- Returns a summary, never the file (`pdf.py:360-368`).
- **fpdf2 CAN draw vectors and embed SVG — TEE just doesn't use it yet.** Verified in `server/.venv` (fpdf2 **2.8.8**, pinned `fpdf2>=2.8.8` in the `[pdf]` extra, `pyproject.toml:81-84`): `FPDF` exposes `line, dashed_line, set_dash_pattern, rect, polygon, polyline, circle, arc, solid_arc, regular_polygon, new_path, draw_path, drawing_context, set_draw_color, set_line_width`; and `fpdf.svg` provides `SVGObject`, `PaintedPath`, `ClippingPath`, `GradientPaint`, `SVGImage`. **So a drawing-sheet lane can add a `vector`/`svg` block kind with no new dependency** — and `fc_drawing` already produces SVG pages that could be embedded directly.
- The hard-won Unicode fact is here: `TYPOGRAPHIC_FALLBACK` (`pdf.py:59-88`) after "*curly quotes and em dashes … FPDFUnicodeEncodingException … One smart quote destroyed a whole report*" (`pdf.py:44-51`); fonts are resolved from system dirs, never vendored (`pdf.py:90-100`, `103-124`).

---

## 5. `assets/` — the GLB → engine path, and the seamkiln handoff pattern

### `as_ingest` (`assets/ingest.py`)
`ingest_directory(store, directory)` indexes `.gltf/.glb` by probing the **JSON header only, no DCC** (`ingest.py:3-5`, `44`): `gltf.probe(path)` walks the node tree with TRS matrices and returns triangle count + world-space extents (`assets/gltf.py:127-193`, `extents_m` at `:193`). Loose textures are grouped into material sets by a map-role suffix regex (`ingest.py:22-31`). Local assets carry `license: 'local'` and skip the SPDX gate (`ingest.py:5-7`).

### `as_import` (`assets/importer.py:129-276`) — the six-step pipeline worth copying wholesale
1. **Scene-reuse check** — same `asset_key` already placed → report it (`:142-150`, note emitted at `:274-275`).
2. cache-or-download (`ensure_cached`, `:153`).
3. measure (`:156`).
4. **scale policy** (`:160-181`).
5. typed batch, per-adapter: blender gets `{"op": "import_file", "path", "name", "props"}` (`:198`); **unreal bypasses the typed batch** because "*Epic's AssetTools cannot import at all, and the sandboxed script lane cannot reach the importer, so this runs through TEE's content plugin*" with a **hand-made checkpoint to keep the same rollback guarantee** and an explicit **m → cm conversion** `[v * 100.0 for v in location]` (`:199-221`).
6. **read-back verification**: expected `measured × scale` vs the DCC's reported `dimensions`/`dims_m`, sorted-axis compared, `_max_deviation ≤ _VERIFY_TOLERANCE`, failure note "*check units/axis of the source asset*" (`:236-255`).

**Scale bands** (`assets/envelopes.py:1-14`): `accept` → `fix` (a power-of-ten or inch factor applied **and recorded as a fact**; "*unit-boundary bugs are the #1 import failure*") → `snap` (±10 % of target/catalogue, uniform scale = geometric mean of constrained-axis ratios) → `reject` (one line, measured vs expected). `_UNIT_FACTORS` at `:23-32` covers mm/cm/dm/×10/authored-cm/authored-mm/inches/authored-inches. `_SNAP_TOLERANCE = 0.10`, `_ACCEPT_SLACK = 1.02` ("*envelopes are bands, not gauges*"). Non-uniform scale is forbidden for rigid classes. A `reject` with no envelope and no target raises with "*Nothing to judge scale against … Pass asset_class= one of {...}, or target_dims=[x, y, z] in metres*" (`importer.py:163-180`).

**Blender import helper**: `adapters/blender/codegen.py:170-198` `_import_file(op)` — dispatches gltf/glb → `bpy.ops.import_scene.gltf`, obj → `bpy.ops.wm.obj_import`, fbx → `bpy.ops.import_scene.fbx`; diffs `session_uid` before/after, parents multiple roots under a synthetic empty anchor, and raises on zero new objects. `_apply_props` (`:202+`) notes that `obj.dimensions` writes scale from a **stale** `bound_box` for meshes built in the same batch, so it derives scale from real vertex extents instead (`:211-215`).

### `seamkiln/src/seamkiln/handoff.py` — "hand a mesh over in its units and axis"
`Target(name, up, handed, unit_m, prefers, driven_by_tee, note)` (`handoff.py:51-61`), table at `:64-93`:

| target | up | handed | unit_m | prefers | driven | note |
|---|---|---|---|---|---|---|
| blender | Z | right | 1.0 | glb | yes | TEE adapter: `import_file` op |
| unreal | Z | left | 0.01 | glb | yes | `import_asset_file`; needs TEE content plugin |
| godot | Y | right | 1.0 | glb | **no** | bridge `add_node` can only instantiate an allowed CLASS; drop the .glb in `res://` |
| maya | Y | right | 0.01 | obj | no | default working units cm |
| zbrush | Y | right | 1.0 | obj | no | unitless; GoZ rescales to canvas |
| houdini | Y | right | 1.0 | obj | no | |
| marvelous | Y | right | 0.001 | obj | no | works in mm |

`SOURCE = Target("seamkiln", "Y", "right", 1.0, ...)` (`:98`). `transform_for(target, fmt)` (`:100-117`) **returns identity for glb/gltf/usd** and only builds the +Y→+Z rotation, handedness flip and `SOURCE.unit_m / target.unit_m` scale for self-describing-less formats. `Bundle.summary()` reports `up`, `units: "1 unit = X m"`, `transform`, `driven_by_tee`, `note` (`:128-142`). `ops_for(bundle)` **refuses rather than guesses** for undriven targets (`:286-298`): "*emitting one that does not exist would fail inside the DCC instead of here, which is the expensive place to find out.*"

---

## 6. `extract/` — DXF and IFC readers

`extract/documents.py` — "*DXF via ezdxf (`DIMENSION.get_measurement()` is dimensional ground truth)*" (`:3`). `ezdxf>=1.4.4` sits in the **`[extract]` extra** (`pyproject.toml:21`); extras gate at `kernel/extras.py:38` (`"extract": "ezdxf"`).

Reusable pieces for reading drawings:
- `INSUNITS_TO_M` map (`documents.py:25`) `{1: 0.0254in, 2: 0.3048ft, 4: 0.001mm, 5: 0.01cm, 6: 1.0m, 7: 1000.0km, 10: 0.9144yd, 14: 0.1dm}`; `$INSUNITS=0` **records a question fact instead of guessing**, then assumes 1 unit = 1 mm with `confidence: "assumed"` (`:97-108`).
- `extract_dxf(path, frame)` (`:76-196`): units fact → `msp.query("DIMENSION")` → `dim.get_measurement()` × scale, with `dimtype & 7` and layer (`:112-127`) → LWPOLYLINE on `*WALL*` layers become centerline walls (using `const_width` as thickness), `*ROOM*` closed polylines become room polygons (`:143-176`) → TEXT/MTEXT point-in-polygon room naming (`:178-189`) → openings from POINT/INSERT on `DOOR*`/`WINDOW*` layers, snapped to the nearest wall as parametric `t` (`_openings_from_layers`, `:199-235`).
- `parse_dimension_text` (`:56-70`): `'4200'/'4200 mm'/'4.2 m'` → metres; **bare numbers ≥ 100 read as mm by drawing convention, smaller bare numbers are ambiguous → None**.
- `classify_sheet` (`:43-53`): NCS sheet-number digit first (`_NCS_CLASS = {1: plan, 2: elevation, 3: section, 5: detail}`), then title keywords, then `"unknown"` — never a guess.
- Plan schema `tee-plan/1` (`extract/plan.py:18-34`), `validate_plan` (`:52+`) — "*Units are always meters in a drawing model frame*" (`plan.py:7-8`).
- `extract/ifc.py:18-…` `export_ifc(plan, out_path, project_name)` — real IfcWall + body representation + storey elevations via `ifcopenshell.api.run`, "*API shapes verified empirically against ifcopenshell 0.8.5*" (`ifc.py:5`). Write-side only; there is **no IFC reader** in-tree.

**Note**: `seamkiln` itself depends on `ezdxf>=1.4` directly (`seamkiln/pyproject.toml:27`) — precedent for a root package carrying its own DXF I/O rather than reaching into `tee.extract`.

---

## 7. `benchmarks/run_benchmarks.py` — the scenario template

- `estimate_tokens` is imported from the server (`run_benchmarks.py:43` → `server/src/tee/kernel/budget.py:26-32`): `max(1, int(len(json.dumps(obj, separators=(",",":"), default=str, ensure_ascii=False)) / 3.5))`, `CHARS_PER_TOKEN = 3.5` (`budget.py:20`) — "*matching the wire format, which is also compact JSON*" (`budget.py:4-5`).
- `run_seamkiln_scenario()` (`:1231-1302`) and `run_seamkiln_followup_scenario()` (`:1305-1409`). Both follow the same six-step shape:
  1. `try: import <package>; from tee.adapters.<x> import <X>Adapter / except ImportError: print("... skipped"); return None` (`:1244-1250`) — an absent optional package skips, never fails the suite.
  2. temp root + `TeeApp({"<name>": Adapter(root)}, project_root=root)` (`:1252-1254`).
  3. one declarative `batch` list of typed ops (`:1256-1260`, `:1326-1344`).
  4. TEE arm: `tee_tokens = estimate_tokens(batch) + estimate_tokens(diff.to_payload()) + estimate_tokens(<one virtual-tool result>)`; `tee_calls = 2  # one tee_batch, one tee_call(...)` (`:1266-1269`).
  5. **Naive arm built from the SAME state, as geometry** — every panel outline + the full point/triangle dump; the follow-up scenario multiplies a per-frame point dump by the animation frame count "*because without a diff, 'did the coat stay on' IS the vertex list*" (`:1366-1387`). `naive_calls = 1 + len(panels) [+ frames + 1]`.
  6. `saving = 100.0 * (1 - tee_tokens / naive_tokens)`; returns a flat dict of counts + `saving` + `wall_s` + a couple of domain facts (`:1290-1302`).
- Wired in at `:1800-1804` via `_safe(...)`; report sections at `:2196` / `:2222`, which restate the invariant: "*The always-loaded surface is unchanged at 17 tools*" (`:2216`), "*Surface unchanged: 17 tools.*" (`:2245`).
- The invariant is **enforced by test**, not by prose: `server/tests/test_gateway.py:168` `test_always_loaded_surface_delta_is_zero` (lists tools over a real MCP client with and without the adapter) and `server/tests/test_seamkiln_adapter.py:173,251` `assert len(_DESC) == 17, "the always-loaded surface moved"`. The 2,033-tok figure: `docs/seamkiln-lane.md:15-16`, `docs/PROGRESS.md:9062-9066`, `CLAUDE_A65_SCRIPT.md:28`.

---

## 8. `knowledge-base/` — 38 domains; mechanical coverage is thin

`ls knowledge-base` → `00_meta, 01_architecture, 02_building_construction, 03_codes_standards, 04_masters_and_practice, 05_companies_and_industry, 06_joinery_and_woodwork, 07_materials_and_suppliers, 08_glass_and_facades, 09_equipment_manufacturers, 10_media_awards_competitions, 11_logistics_remote_areas, 12_hr_construction, 13_software_unreal_engine, 14_software_blender, 15_software_autodesk_fusion, 16_walls_and_boundaries, 17_paving_and_roads, 18_namibia_context, 19_interior_design, 20_furnishing_industry, 21_machine_vision, 22_psychology_and_education, 23_cartography_and_mapping, 24_hydrology_arid, 25_environmental_asset_creation, 26_computer_engineering, 27_semiconductors_and_chip_design, 28_graphic_and_game_design, 29_aerospace_engineering, 30_space_science_and_propulsion, 31_aviation_industry, 32_aviation_weather, 33_social_engineering_defence, 34_medical_field, 35_health_and_fitness, 36_finance_careers, 37_alibaba_and_qwen` + `AGENTS.md, INDEX.md, README.md, manifest.json`.

Relevant to a mechanical CAD lane, one file each with frontmatter:

| Need | File | id / status / confidence |
|---|---|---|
| **Sketching + constraints** (the closest thing to a spec for the lane) | `15_software_autodesk_fusion/02_sketching-and-constraints.md` | `fusion.sketching` · stable · **medium** · updated 2026-08-25 |
| **Feature tree, timeline, parameters** | `15_software_autodesk_fusion/03_modelling-and-parameters.md` | `fusion.modelling` · stable · **medium** |
| **Assemblies, components, joints, interference** | `15_software_autodesk_fusion/04_assemblies-and-joints.md` | `fusion.assemblies` · stable · **medium** |
| **Machining / CAM / post / G-code** | `15_software_autodesk_fusion/06_cam-and-manufacturing.md` | `fusion.cam` · stable · **medium** (`applies_to` notes `CAM.postProcess` and `postProcessAll` are RETIRED) |
| **Shop drawings, sheets, dimensions, parts lists, DXF/PDF** | `15_software_autodesk_fusion/07_drawings-and-documentation.md` | `fusion.drawings` · stable · **medium** · jurisdiction `southern-africa`; "*Drawing API is PDF-export only*" |
| **Formats / interop / competitive positioning** | `15_software_autodesk_fusion/10_interoperability-and-alternatives.md` | `fusion.alternatives` · stable · **medium** (tags: step, iges, dxf, dwg, stl, 3mf, obj, usd, solidworks, onshape, rhino, freecad, shapr3d) |
| **Fasteners / hardware (cabinet-grade, not machine-grade)** | `06_joinery_and_woodwork/07_hardware-systems.md` | `joinery.hardware` · stable · **high** — Blum/Hettich/Grass load ratings and drilling patterns |
| **Hinge standards** | `06_joinery_and_woodwork/11_european-hinge-standards.md` | `joinery.hinge_standards` · **draft** · medium · updated 2026-08-29 (EN 15570 / EN 15828) |
| **Materials: steel, sheet metal, fixings** | `07_materials_and_suppliers/04_steel-and-reinforcement.md` | `materials.steel_reinforcement` · stable · **high** · jurisdiction `southern-africa` (SANS 50025 / EN 10025 S355JR, galvanising, fastener/corrosion classes) |
| **Metals & alloys for structures** | `29_aerospace_engineering/04_structures-and-materials.md` | `aerospace.structures` · stable · **high** (2024/7075 Al, Ti-6Al-4V, CFRP, fatigue/damage-tolerance) |
| **Manufacturing processes (machining, sheet metal, fastening)** | `29_aerospace_engineering/06_aerospace-manufacturing.md` | `aerospace.manufacturing` · stable · **medium** (AS9100, Nadcap, traceability) |
| **CAD→mesh→engine tessellation/units** | `25_environmental_asset_creation/07_hard-surface-and-fusion-workflow.md` | `envasset.hardsurface_fusion` · stable · **medium** · `unit_system: SI` |
| **Codes/standards register pattern** | `03_codes_standards/03_key-sans-standards-register.md` | domain is SANS/NBR-centric, building not mechanical |

**Gaps confirmed by grep across the whole KB**: no file matches GD&T / geometric dimensioning / ISO 2768 / ISO 286 / limits-and-fits (only one incidental hit in `16_walls_and_boundaries/06_contemporary-wall-design.md`); no metric-thread / ISO 898 / property-class-8.8 fastener coverage; no bend-allowance / K-factor sheet-metal coverage; no weld-symbol / fillet-weld coverage. **A mechanical CAD lane must author these domains itself.**

The KB's own posture, which the lane must honour (`knowledge-base/AGENTS.md:20`): "*a **knowledge source, not a decision authority***"; confidence `medium` = "*usable for orientation; verify before acting on it*" (`AGENTS.md:29`); systematically weak on prices, paywalled standards text, and labour rates (`AGENTS.md:37-43`). The in-tree precedent for how to consume it is `physical/joinery.py:4-7` — rules lifted from the KB were **re-verified at the cited source before judging anything**, and the verification stamp travels with every finding.

---

## 9. `seamkiln/session.py` + `pattern/model.py` — the feature-tree document design to copy

### Command / Session / replay / fingerprint
- **Thesis** (`session.py:1-18`): "*a Session holds the garment, every mutation is a Command, and every Command is recorded. The Qt shell builds Commands from clicks. The TEE adapter builds the same Commands from a batch … there is no path through the interface that a script cannot take. Nothing here imports Qt, and nothing here imports TEE.*"
- `Command` — `@dataclass(frozen=True, slots=True)` of `{op: str, args: dict}` (`:37-54`). `from_dict` tolerates the TEE wire shape by folding `props` into `args` (`:49-54`), so **one command model serves both the GUI and the MCP batch**.
- `Session` — a mutable dataclass of *slots for the model plus every derived side product* (pattern, body, sdf, garment, drape, colours, fur, lace, animation, locks, zippers, buttons, handoffs, arrangement, frame, avatar, gait, live) + `history: list[Command]` (`:57-88`). The comment at `:70-72` is the design rule: side products live "*on the session so an export or a render can reach them without the caller keeping a second copy that can drift*".
- `script()` → `{"seamkiln_script": SCRIPT_VERSION, "name", "commands": [...]}` (`:92-98`); `save_script` (`:100-103`).
- `replay(script)` → classmethod, **version-checked with a refusal** (`:106-120`): "*The replay law: same script in, same garment out — checked by fingerprint, not by eye.*"
- `fingerprint()` (`:122-137`) — sha256 over `name` + per-panel `id` + `np.round(outline, 6).tobytes()` + `np.round(drape.points, 6)`, truncated to 16 hex chars. **Rounding before hashing is what makes it stable across platforms.**
- `apply(command)` (`:149-160`) — "*The ONLY way state changes*": look up `_VERBS[op]`, unknown op lists every accepted verb, run the handler, **then** append to history.
- `summary()` (`:162-177`) — "*Compact state. Never geometry — hard rule 1, in the core itself.*"
- `_VERBS` (`:1304-1334`), 29 verbs, exported as `VERBS = tuple(sorted(_VERBS))` (`:1336`). Locking: `_guard(session, scope, doing)` (`:183-193`) — "*Locks are set by a command, so they survive a replay and a locked script produces the same garment twice.*" Non-determinism is resolved **and recorded**: `_arrangement_choice` (`:388-405`) — "*'auto' picks by body kind, and the pick is RECORDED so a replay makes it*". Interactive drags are deliberately *not* recorded per-frame: "*a two-second drag is a hundred frames of nothing anybody wants replayed*" (`:1125`).

**For a CAD document**: `Command` ≡ a feature-tree node; `history` ≡ the tree; `replay` ≡ rebuild-from-features; `fingerprint` ≡ the regression oracle for "did this refactor change any geometry"; `_VERBS` ≡ the closed, enumerable op set (no "run arbitrary Python" door — `adapters/seamkiln/adapter.py:9-12`).

### Stable ids (`pattern/model.py`)
- The core decision (`model.py:1-10`): "*An **edge** is not stored — it is *derived* as the run of boundary vertices between two consecutive turn points … it means an edge cannot disagree with the outline it belongs to. The cost is that edge ids move when corners move, so `Panel.edge_ids()` is stable exactly as long as the corner count is, and `Seam` records the corner count it was made against to say so out loud.*" **This is the topological-naming problem, named and priced — exactly the problem a mechanical CAD kernel faces with faces/edges after a feature edit.**
- `EdgeRef(panel, edge, t0=0.0, t1=1.0)` frozen+slots (`:50-65`), rendered as `panel#edge[t0:t1]`; the `t0/t1` span "*make segment-to-segment and N:1 seams expressible*".
- `Panel` (`:107-179`): `id, outline, name, internals, marks, seam_allowance_mm, meta`; `__post_init__` normalises to CCW and drops an implicitly-repeated closing vertex (`_close_implicitly`, `:88-104` — "*a seam that measures 0.0 mm and matches anything*"). `corner_indices()` = vertices with `VertexKind.TURN` (`:140-141`); `edges()` returns runs and treats a corner-less boundary (a circle) as **one** edge rather than an error (`:143-159`); `edge_ids()` → `f"{self.id}#{k}"` (`:161-162`); `edge_run` raises with the valid range (`:164-173`).
- `Seam` (`:182-203`) auto-ids as `f"{a}~{b}"`; `gather` "*is not a fudge factor for a drafting mistake: `true_up` measures against it, so an unintended mismatch stays visible*".
- `Pattern` (`:215-…`): `panel(id)` raises listing every known id (`:224-229`); `summary()` — "*Never the vertex list: TEE's first hard rule. Detail is opt-in.*" (`:235-239`).

---

## 10. `seamkiln/materials.py` — the tier-flag card design

- Thesis (`materials.py:8-12`): "*The tier flag travels through every one of those doors. A card imported from a file arrives with whatever tier it claims; a card *derived* from a KES-F or fabric-kit test may claim `measured` and must name its report. **Nothing here promotes a card's tier on its own, because that is how a solver constant ends up on a spec sheet as a measurement.***"
- `Tier(StrEnum) = {MEASURED = "measured", PLAUSIBLE = "plausible"}` (`pattern/fabric.py:57-59`); `Fabric` is `frozen=True, slots=True` with `tier: Tier = Tier.PLAUSIBLE`, `source: str = ""`, `notes: str = ""` (`fabric.py:62-87`) — **plausible is the default; measured must be earned.**
- Render properties ride on the card but are labelled non-physical everywhere (`fabric.py:88-93`): "*the solver never reads them*". Mirrored in `library()`'s row where `roughness` carries the inline comment `# render only, not physical` (`materials.py:90`).
- `LIMITS` (`materials.py:38-45`) — plausibility ranges per field (`gsm 5–2000`, `thickness_mm 0.01–8`, `bend_warp/weft 0.05–5000 mN·mm`, `friction 0.02–1.2`, `roughness 0–1`): "*A 'fabric' at 5,000 g/m2 is a mistake, not a material, and catching it at the door beats discovering it as a solver that will not converge.*"
- `validate(card)` (`:52-68`) names the offending field and suggests the likely cause ("*a common cause is a card written in different units*"), and enforces the tier rule: "*tier 'measured' needs a `source` naming the test report. A card that claims a measurement without one is a solver constant wearing a lab coat.*"
- `CATEGORIES` maps **use**, not spec — "*what a cloth is FOR, which is how a designer looks for one — not by GSM*" (`:24-33`). `library(category=None, tier=None)` filters the way a designer filters (`:71-94`).
- `add()` refuses to shadow a bundled card silently (`:104-116`): "*two cloths with one name is how a tech pack ends up describing the wrong cloth.*"
- Packaging precedent: `seamkiln/pyproject.toml:9-28` — a licence comment block naming the **banned** dependencies and their permissive replacements, enforced by `tests/test_licences.py` which "*fails the build rather than trusting anyone to remember this list*".

---

# The reuse table

| Need in the CAD lane | Existing code | file:line | How to reuse |
|---|---|---|---|
| BREP kernel out-of-process | `_cad_worker.py` / `_cpsat_worker.py` | `server/src/tee/fleet/_cad_worker.py:56-79`; `_cpsat_worker.py:1-22` | Copy the contract shape (stdin JSON → one stdout JSON line, fd-level chatter swallowing, zero `tee` imports). **Convert to a persistent loop** — the current one-shot pays the OCP import per call. |
| Sidecar venv discovery + install fix | `cad.py` | `fleet/cad.py:206-212`, `:244-253` | Reuse `SIDECAR_PY` + `spec["cad_python"]` override verbatim; keep the "not garbage, a capability" purge classification (`purge.py:78-88`). |
| Geometry read-back without a DCC | `cad.measure` | `fleet/cad.py:297-384` | `cad_measure` already answers volume/area/bbox/valid for STEP/BREP/STL. Call it for verification instead of re-implementing. |
| 2D constraint solving | `solve_sketch` | `physical/sketch.py:32-216` | Reuse as-is for the sketch layer. Fix/settle the m-vs-mm contract first (`sketch.py:5` says metres, `freecad/adapter.py:7` feeds mm). Depends on `py-slvs`, **`[physical]` extra** (`pyproject.toml:44-47`). |
| Solve-before-DCC wiring | `FreeCADAdapter._prepare` | `adapters/freecad/adapter.py:114-133` | Same interception point for `kind == "sketch"`; inject solved coords into props. |
| Typed op vocabulary | freecad `codegen` | `adapters/freecad/codegen.py:28-35`, `77-230` | Copy `create/set/delete` + `box/cylinder/sphere/cone/sketch/pad/pocket` + the generic-kind escape hatch; extend with revolve/loft/sweep/fillet/chamfer/pattern/mirror. |
| Batch → one script → one diff | `compile_batch` | `adapters/freecad/codegen.py:233-276` | Same prelude/epilogue/`_OpError` structure; one recompute; diff details capped to scalars + `faces` + `volume_mm3`. |
| Checkpoint / rollback | `snapshot`/`restore` | `adapters/freecad/adapter.py:137-164` | Session-scoped spill dir + native save-copy. For an in-process kernel, serialise the command history instead (see `Session.script`). |
| Feature tree / document / replay | `seamkiln.Session` | `seamkiln/src/seamkiln/session.py:37-177`, `1304-1336` | `Command(op, args)` + `history` + `script()`/`replay()` + closed `_VERBS` table = the feature tree. `from_dict` already accepts TEE's `props` wire shape. |
| Regression oracle | `Session.fingerprint` | `seamkiln/session.py:122-137` | Round to 6dp then sha256 the tessellation/topology; assert identical after replay. |
| Stable topological ids | `Panel.edge_ids` / `EdgeRef` / `Seam` | `seamkiln/pattern/model.py:1-10`, `50-65`, `161-162`, `182-203` | Adopt the "derive, don't store; record what the id was made against" policy for faces/edges after a feature edit. |
| Rule-check engine (GD&T, DFM, fastener, sheet-metal) | `joinery.check` / `plaus.check` | `physical/joinery.py:24-90`, `264-273`; `physical/plaus.py:151-178` | Copy `RULES` (severity + source + verified stamp) and the `hit()` closure; keep `not_evaluated` + `rules_total`/`rules_evaluated`; use JSON rule data + `@cache` loader for anything big (`plaus.py:151-154`). |
| Severity ladder + jurisdiction capping | `plaus` | `physical/plaus.py:74-131`, `134-148` | `CONV < HEUR < STD < CODE` with a visible cap generalises to "manufacturer datasheet < trade practice < ISO standard < contractual spec". |
| Material cards with honesty flags | `physical/materials.py` + `materials_eng.json`; `seamkiln/materials.py` | `physical/materials.py:50-134`; `seamkiln/materials.py:38-116`; `pattern/fabric.py:57-93` | Per-leaf `value/unit/source/honesty`; `Tier.PLAUSIBLE` default, `MEASURED` requires `source`; `LIMITS` range gate at the door; render props labelled non-physical; `banned_bulk_sources` list. |
| Drawing sheet output | `fc_drawing` + `pdf_compose` | `adapters/freecad/tools.py:33-163`; `pdf.py:220-382` | Reuse the read-back law and `ExtentX/Y`. **`pdf_compose` needs a new `vector`/`svg` block + page-size/landscape + a title block** — fpdf2 2.8.8 already ships `draw_path/line/polygon/rect/dashed_line` and `fpdf.svg.SVGObject`, so no new dependency. |
| Reading incoming drawings | `extract_dxf` | `extract/documents.py:25`, `56-70`, `76-196` | `INSUNITS_TO_M`, `get_measurement()` as ground truth, the record-a-question-instead-of-guessing pattern, `parse_dimension_text`'s ≥100→mm convention. |
| BIM/IFC write | `export_ifc` | `extract/ifc.py:18+` | Only a writer exists; a mechanical lane wanting STEP AP242 / IFC read must add it. |
| Mesh handoff to Blender/Unreal/Godot | `handoff.TARGETS` / `transform_for` / `ops_for` | `seamkiln/handoff.py:51-117`, `286-298` | Copy the target table (up/handed/unit_m/prefers/driven_by_tee) and the **identity-for-glTF** rule; refuse rather than guess for undriven targets. |
| Import verification / scale bands | `import_asset` + `envelopes` | `assets/importer.py:129-276`; `assets/envelopes.py:1-35`, `67-130` | Four-band policy + recorded scale-fix facts + read-back deviation check. Add a `mechanical_part` dimension envelope class. |
| GLB probe without a DCC | `gltf.probe` | `assets/gltf.py:127-193` | Triangle count + world-space extents from the JSON header, for cheap verification. |
| Blender import op | `_import_file` | `adapters/blender/codegen.py:170-198` | Reuse verbatim; note the stale-`bound_box` warning at `:211-215`. |
| Zero-always-loaded-tool registration | `VirtualTool` + lazy handlers | `kernel/registry.py:30-57`; `fleet/tools.py:122-136`; `adapters/seamkiln/adapter.py:1-17` | Prefix every tool (`mc_*` / `inv_*`), register via `app.registry.register`, lazy-import inside the handler, table the capability in `kernel/trust.py`. |
| Benchmark scenario | seamkiln scenarios | `benchmarks/run_benchmarks.py:1231-1409`; `kernel/budget.py:26-32` | Copy the six-step shape verbatim; naive arm = the geometry a model must read without compact state. |
| Surface invariant enforcement | tests | `server/tests/test_gateway.py:168`; `test_seamkiln_adapter.py:173,251` | Add the same `len(_DESC) == 17` assertion for the new adapter. |
| Self-contained root package | `seamkiln/`, `voxkiln/` | `seamkiln/pyproject.toml:1-40` | Own `pyproject.toml`, permissive-only deps with the **banned list written down** and a `test_licences.py` gate. |

---

# Facts learned the hard way (quoted; a CAD lane must not relearn them)

**Sidecars and imports**
1. "`CadQuery FIRST import : 140 s <- the problem`" — `CLAUDE_A46_SCRIPT.md:36`; warm ≈1.1 s (`docs/setup-fleet.md:166`). Rebuild after purge is "~150 s, needs network" (`purge.py:81`).
2. "installing `cadquery` to read one number out of a STEP file brought … **1.1 GB** for volume, area, bounding box and validity" — `_cad_worker.py:4-12`.
3. "no tool call may block on a first import. A cold `med_` or `cad_` call paid 60–140 s of bytecode compilation and timed out." — `CLAUDE_A46_SCRIPT.md:139`.
4. "Native chatter is swallowed at the descriptor level so it can never corrupt that." — `_cad_worker.py:21-23`.
5. "Deliberately imports nothing from `tee`, so the parent can invoke it by path from any environment." — `_cad_worker.py:19-20`.
6. "`ortools` and `highspy` each bundle their own build of HiGHS … **Import ORDER decides it** … a server whose correctness depends on which tool was called first is not correct." — `_cpsat_worker.py:3-13`.

**Security / licensing**
7. "**`-D` is never exposed, and that is a security decision.** OpenSCAD's `-D` does not set a scalar: it *prepends arbitrary statements* to the script. A caller-supplied `-D` is code execution on the owner's machine wearing the costume of a parameter." — `fleet/cad.py:13-18`.
8. OpenSCAD "is GPL-2.0-or-later, so it is driven as a SUBPROCESS through its documented command line — never linked, never imported." — `fleet/cad.py:5-9`.
9. "Every dependency here is permissive ON PURPOSE, and the ones that are NOT here matter more than the ones that are … the gate in `tests/test_licences.py` … fails the build rather than trusting anyone to remember this list." — `seamkiln/pyproject.toml:9-12`.

**FreeCAD / drawings**
10. "A dimension created in the same dispatch as its view binds before the view's projection exists and **CACHES 0.0** (verified live on 1.1.3 …). The read-back is therefore a second call that touches the dims first." — `adapters/freecad/tools.py:75-79`.
11. "API notes (**verified live on 1.1.3 by the P4 smoke, not from memory**) … PartDesign bodies are deliberately NOT used in v1 — Part-workbench objects have the stabler scripting surface; recorded as a limitation with the upgrade path." — `adapters/freecad/codegen.py:14-19`.
12. "page SVG/PDF is GUI-bound, #5710" — `adapters/freecad/tools.py:6-8`; `docs/setup-freecad.md:5-7`.
13. "Connected but never answered: the GUI thread is not dispatching (SI-B12 — typically a startup modal such as document recovery)." — `adapters/freecad/wire.py:49-50`.
14. "FreeCAD sanitises/deduplicates names" — the returned document name must be adopted, not assumed — `adapters/freecad/adapter.py:69`.

**Sketching / geometry**
15. "sketch geometry arrives SOLVED … so scripts place final coordinates and **never lean on FreeCAD's solver converging from guesses**." — `adapters/freecad/codegen.py:11-12`.
16. "2 DOF — the rigid-body translation — is normal for an unanchored sketch and solves fine." — `physical/sketch.py:19-20` (the code allows 3; `sketch.py:209`).
17. "An outline is closed implicitly here … Curve constructors that end where they began (and DXF, which stores closed polylines both ways) hand over an explicit ring, and the repeat shows up downstream as **a zero-length final edge: a seam that measures 0.0 mm and matches anything**. Normalised once, on the way in." — `seamkiln/pattern/model.py:88-97`.
18. "an edge cannot disagree with the outline it belongs to. The cost is that edge ids move when corners move … and `Seam` records the corner count it was made against **to say so out loud**." — `seamkiln/pattern/model.py:5-9`.
19. "`gather` … is not a fudge factor for a drafting mistake: `true_up` measures against it, so an unintended mismatch stays visible." — `seamkiln/pattern/model.py:186-189`.

**Units and axes**
20. "glTF (.glb) **DEFINES its own**: +Y up, right-handed, metres … a GLB needs NO transform from us — and applying one would double-convert. This is the trap this module exists to avoid, and it was checked in a real Blender 5.2 rather than assumed." With the wrong transform: "lying on its face through the floor. **It would have looked like a bug in Blender's importer.**" — `seamkiln/handoff.py:14-31`.
21. "OBJ defines NOTHING. No units, no axis, no handedness. Every application guesses, which is why this is where the pain actually is." — `seamkiln/handoff.py:32-35`.
22. "a silent power-of-ten or inch-factor correction … applied and RECORDED as a fact (**unit-boundary bugs are the #1 import failure**)" — `assets/envelopes.py:5-7`.
23. "`obj.dimensions` writes scale from the `bound_box`, which is **stale for meshes built this same batch** — derive scale from real vertex extents" — `adapters/blender/codegen.py:211-213`.
24. "DXF has `$INSUNITS=0` (unitless)" → record the question with `confidence: "assumed"` rather than guess — `extract/documents.py:98-107`.
25. "bare numbers >= 100 read as mm (drawing convention), smaller bare numbers are ambiguous -> None" — `extract/documents.py:57-58`.
26. Millimetres are the fabrication-lane convention end to end (`adapters/freecad/codegen.py:9-10`, `physical/joinery.py:13`); metres are the plan/asset-lane convention (`extract/plan.py:7`, `physical/sketch.py:5`). **The boundary between them is where bugs live.**

**Honesty / posture**
27. "FLAGGING against cited prescriptive tables restates the code … APPROVING or SIZING would be engineering practice. So: findings carry source + severity + the exact delta; there is **no member sizing and no 'passes' state**." — `physical/plaus.py:3-7`.
28. "a rule whose input the model simply does not carry … answers `not_evaluated` with the reason — **silence is never conformance**." — `physical/joinery.py:9-11`.
29. "every rule was lifted from the KB's … domain and **RE-VERIFIED at its cited source** … BEFORE it judges anything (the verification state is stamped on each rule and travels with every finding)." — `physical/joinery.py:4-7`.
30. "the exact-name check silently skipped 'clay_brick' and 'concrete_block' walls (**a 60 m clay_brick wall sailed through slenderness**)" — `physical/plaus.py:79-81`.
31. "repeating it per finding cost **2.5x the payload** for no added information" — `physical/plaus.py:26-27`.
32. "tier 'measured' needs a `source` naming the test report. A card that claims a measurement without one is **a solver constant wearing a lab coat**." — `seamkiln/materials.py:64-66`.
33. "Nothing here promotes a card's tier on its own, because that is how a solver constant ends up on a spec sheet as a measurement." — `seamkiln/materials.py:10-12`.
34. "A 'fabric' at 5,000 g/m2 is a mistake, not a material, and catching it at the door beats discovering it as a solver that will not converge." — `seamkiln/materials.py:36-37`.
35. "two cloths with one name is how a tech pack ends up describing the wrong cloth." — `seamkiln/materials.py:110-111`.
36. "Bullet MULTIPLIES the two bodies' friction coefficients — to realize pair coefficient mu, set each body to sqrt(mu)"; "UE physical materials take density in g/cm^3 and apply a mass power fudge; echo computed mass back after assignment" — `materials_eng.json` `_meta.engine_caveats`.

**Token / surface discipline**
37. "a build answers with facets, volume, bounding box and the output path — never geometry. A mesh is a file reference; that is the whole point of writing it to disk." — `fleet/cad.py:20-22`.
38. "Compact state. **Never geometry — hard rule 1, in the core itself.**" — `seamkiln/session.py:163`; "Never the vertex list: TEE's first hard rule. Detail is opt-in." — `seamkiln/pattern/model.py:238`.
39. "without a diff, 'did the coat stay on' IS the vertex list" — `benchmarks/run_benchmarks.py:1366-1367`.
40. "Operations are DECLARATIVE and enumerable, the trade-rule lesson from A49 … **There is no 'run arbitrary Python' door here**; the escape hatch is seamkiln's own library, reached by a caller who already has code execution." — `adapters/seamkiln/adapter.py:9-12`.
41. "a new tool cannot silently escape the check, because **the server refuses to boot** until someone tables it." — `kernel/registry.py:37-42`.
42. "Search results pay this per hit; authors drift toward paragraph-long 'first lines', so the cap — not the author — holds the search row price." — `kernel/registry.py:46-50`.
43. "Refuses rather than guesses … emitting one that does not exist would fail inside the DCC instead of here, **which is the expensive place to find out**." — `seamkiln/handoff.py:70-72`.

**PDF**
44. "curly quotes and em dashes … `FPDFUnicodeEncodingException` … The damaging half is not CJK; it is the quotes and dashes that appear in almost any text a model writes … **One smart quote destroyed a whole report.**" — `pdf.py:44-51`.
45. "A PDF does not store paragraphs — it stores positioned glyph runs, often split mid-word … the failure mode is silent: a document that opens fine and is subtly wrong." — `pdf.py:14-19`.
46. "No font is vendored into the repo: Arial Unicode is Apple-licensed and redistribution is not TEE's to grant." — `pdf.py:90-93`.

**Determinism**
47. "'auto' picks by body kind, and the pick is RECORDED so a replay makes it." — `seamkiln/session.py:389`.
48. "Locks are set by a command, so they survive a replay and a locked script produces the same garment twice." — `seamkiln/session.py:184-185`.
49. "a two-second drag is a hundred frames of nothing anybody wants replayed" — `seamkiln/session.py:1125`.