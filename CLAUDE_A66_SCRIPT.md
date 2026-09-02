# CLAUDE_A66_SCRIPT.md — `partkiln`: a headless, AI-native mechanical CAD kernel + TEE lane

**Owner directive (2026-09-02, verbatim):** *"create an autodesk inventor alternative that
runs headless with TEE and is optimized for ai engines"* — and mid-turn: *"use TEE"*,
*"TEE/QMAX"* (TEE's own tools are the co-pilot; the `qmax` chore profile is pinned).

Written for a fresh session with no memory of the one that researched it. Every licence,
platform and OCCT claim below was verified on 2026-09-02 (seven discovery reports, three
design drafts judged, and three adversarial verifiers against the installed OCP and the
tree); `docs/research/68-mechanical-cad-lane.md` (written in P6 from that evidence) is the
design of record. Build ON these facts; do not re-litigate them. Campaign **A66**; server
**0.19.0 → 0.20.0**. Phases are independently shippable: stopping at a phase boundary must
leave the tree green and the feature honest about what it does not do.

## Orientation for a cold session

- Repo `/Users/john/TokenEfficiencyEngine`, TEE code in `server/`. Branch
  `claude/token-efficiency-engine-5jv1dj` ONLY. Read `docs/PROGRESS.md` first (the A66
  entries are at its tail); real command output into it per phase; commit + push per item.
- Suites: `uv run --project server python -m pytest server/tests -q` → **1,224 passed /
  17 skipped / 97 dcc-deselected** at A66's start; `cd seamkiln && PYTHONPATH=src uv run
  --project ../server python -m pytest -q tests/` → 260 / 8 (~7 min, background);
  `make lint` from `server/` (lints `src tests ../benchmarks`) exit 0. The partkiln suite:
  `cd partkiln && PYTHONPATH=src uv run --project ../server python -m pytest -q tests/`.
- Surface invariant: **17 always-loaded tools = 2,033 tok** (`surface:` line of
  `uv run --project server python benchmarks/run_benchmarks.py`;
  `test_server_lint.py:82 EXPECTED_TOOL_COUNT = 17`). **A66 adds ZERO always-loaded tools.**
- Interpreters: `server/.venv/bin/python` = 3.11.15 (has OCP); the Claude Desktop extension
  venv = 3.13.9 with NO OCP; default `python3` = 3.14.7 — never build anything with it.
- Upgrade trap: every `.mcpb` install wipes the extension venv's extras AND any editable
  install; the sidecar venv under `~/TEE/.tee/sidecars/` survives both the wipe and
  `tee_purge`. Restore the fleet extras with the command in `CLAUDE_A53_SCRIPT.md`.
- New code lives in **`partkiln/`** at repo root (own `pyproject.toml`, tests, examples —
  the `seamkiln/`/`voxkiln/` precedent); the adapter in `server/src/tee/adapters/partkiln/`.
- Co-pilot: `tee_web_lookup` (qmax) re-checks any licence/API fact before it lands in a
  file; `cad_measure` (fleet) is the cross-kernel read-back; `tee_batch` on the new adapter
  is the "use it, don't just test it" evidence. `knowledge-base/` grounds nothing.
- The session-scratchpad evidence (discovery reports, design drafts, refuter verdicts,
  probe scripts) is copied under `docs/research/68-evidence/` in P6.

## Context

The owner asked (2026-09-02): *"create an autodesk inventor alternative that runs headless
with TEE and is optimized for ai engines"*, then *"use TEE"* / *"TEE/QMAX"* (TEE's own tools
are the co-pilot; the `qmax` chore profile is pinned).

TEE already did this once for garments: `seamkiln/` (A53/A65) is a Marvelous Designer-class
kernel whose headless surface is the primary surface, whose script is the product, and which
joins TEE through the `Adapter` protocol with zero new always-loaded tools. This plan builds the
mechanical-CAD equivalent the same way: a self-contained kernel package `partkiln/` at repo
root on OCCT (already installed via the OCP wheel) + a TEE adapter under
`server/src/tee/adapters/partkiln/`, with the Inventor core loop as the parity target:

```
sketch (constrained, dimensioned) -> features (extrude/revolve/sweep/loft/hole/fillet/chamfer/
shell/draft/pattern/mirror) -> part (feature tree + parameters) -> assembly (mates, joints, DOF,
interference, BOM) -> drawing (HLR views, dimensions READ BACK from the model, hole table, parts
list) -> export (STEP AP242/IGES/BREP/STL/3MF/OBJ/GLB/DXF/SVG/PDF) -> hand off to Blender/Unreal
```

"Optimized for AI engines" = TEE's dogma applied to CAD: one batch per task, compact state and
diffs (never a mesh dump), every mutation answers with mass properties, text over pixels, stable
NAMED topology (never explorer indices), refusals that name the fix, deterministic replay.

Why not FreeCAD as the engine (doc 52's question, answered): `freecadcmd` 1.1.3 boots in 0.38 s /
67 MB but the headless sketch+TechDraw probe ended "Application unexpectedly terminated";
TechDraw SVG/PDF is GUI-bound (#5710); it embeds OCCT 7.8.1; Sketcher constraints are integer-
indexed (the documented LLM failure mode). FreeCAD stays the A37 `fc_*` adapter.

## Decisions taken by the owner (2026-09-02)

1. **Licence posture: shippable, like seamkiln.** `partkiln` is MIT; permissive-only in-process;
   OCCT (LGPL-2.1-only + OCCT exception 1.0, reached through the Apache-2.0 OCP wheel,
   dynamically linked, NOTICE shipped) is the one weak-copyleft dependency; GPL never in-process
   (`py-slvs` is GPL-3.0; `cadquery` drags casadi LGPL-3 + nine VTK dylibs) — so the lane writes
   its own scipy sketch and assembly solvers. Enforced by a licence-gate test.
2. **Headless-first; GUI later** (a PySide6 client of the same core, A53 Law 3), named as a gap.
3. **Name `partkiln`, prefix `pk_`** (verified absent from `_FAMILY`/`_EXPLICIT` in
   `kernel/trust.py`; no Autodesk marks anywhere in shipped names).
4. **Scope v1: parts + assemblies + drawings + exports; sheet metal (flat-first) last (P5b).**
   Coil/helix and modelled threads = later (L1); ISO 286 fits = later (L2, no permissive data
   source found); FEA/CAM/tube & pipe/harness/frame generator/presentations out.

## Measured facts (2026-09-02, this Mac — build ON them; re-verified by three refuters)

Machine: Apple M5 Max, 18 cores, 128 GB, macOS 26.6.2. Interpreters: `server/.venv` = 3.11.15
(has `cadquery-ocp 7.9.3.1.1`, `cadquery 2.8.0`, `py-slvs`, ezdxf/trimesh/scipy/numpy/fpdf2);
`~/TEE/.tee/sidecars/cad/bin/python` = 3.11.15 (same OCP wheel); the **Claude Desktop extension
venv is Python 3.13.9 with NO `OCP`** (`cad_probe` through the live TEE confirms cadquery absent);
default `python3` = 3.14.7 — never build anything with it. `cadquery-ocp-novtk`, `build123d`,
`lib3mf` are absent everywhere.

| Fact (OCP direct, no cadquery) | Number |
| --- | --- |
| `import OCP` warm | 0.28–1.2 s (`vtkmodules` not loaded; the .so links 9 VTK dylibs) |
| box 100×60×10 − Ø10: cut + exact `BRepGProp` volume | 17 ms; 59 214.602 mm³ = the arithmetic |
| fillet 8 edges r2 / HLR front / STEP AP242 write+read / mesh+STL / GLB | 13 ms / 6 ms / 13+6 ms (volume identical) / 4 ms watertight / 7 ms |
| 100-hole plate (220×220×12): 100 sequential cuts | 0.46 s; 106 faces; **312 unique edges** (`TopExp.MapShapes_s`; the explorer count 624 double-counts shared edges) |
| same plate as ONE n-ary `BRepAlgoAPI_Cut` (`SetArguments`/`SetTools`, NO glue) | **0.09 s**, identical topology and volume. `SetGlue(GlueShift)` returned the UNCUT plate with `IsDone() == True` — glue is only for touching copies (pattern fuses), never for intersecting cuts |
| B-rep fingerprint (sorted rounded per-face area+centroid) in two fresh processes | identical → replay determinism holds across processes |
| `BRepTools.Write_s` VERSION_3 no-tri checkpoint | 81 KB, 1.4–3 ms write, 1 ms read, volume identical |
| tessellation SHA-256 serial vs `InParallel=True` (0.05 / 0.3 mm) | identical (undocumented — pinned by test) |
| glTF: `XCAFDoc_DocumentTool.SetLengthUnit_s(doc, 0.001)` + `SetMergeFaces(True)` | plate reads back [0.22, 0.22, 0.012] m, one geometry — but **unrotated**: the writer applies NO Z-up→Y-up rotation unless `ChangeCoordinateSystemConverter().SetInputCoordinateSystem(RWMesh_CoordinateSystem_Zup)` is set; with it F1 reads `extents_m [0.1, 0.01, 0.06]` / `dims_zup_m [0.1, 0.06, 0.01]` |
| STEP schema on this runtime | `CVal_s("write.step.schema")` is `''` until `STEPControl_Controller.Init_s()`, then `AP214IS`; `SetCVal_s("AP242DIS")` must precede the writer's FIRST `Transfer` (schema is captured then); `Model(True)` only resets a reused `STEPControl_Writer`; `STEPCAFControl_Writer` has no `Model` — use `ChangeWriter().Model(True)`; only `AP203/AP214CD/AP214DIS/AP214IS/AP242DIS` are accepted |
| HLR F1 (`Hide()` called; visible = V+Rg1LineV+OutLineV, hidden = H+Rg1LineH+OutLineH) | front `gp_Dir(0,-1,0)`: V 4 \| H 9 + OutLineH 1; top `(0,0,-1)`: 5 \| 5; right `(1,0,0)`: 4 \| H 10 + OutLineH 2. All-15-edges-filleted F1 r1 front: V 9, Rg1LineV 17 \| H 14, Rg1LineH 19, OutLineH 3 — `VCompound` is NOT empty on F1; it was empty on W3's 12-hole/96-fillet plate (that plate is the trap fixture) |
| history API | `BRepTools_History` binds `Generated/Modified/IsRemoved/Merge/AddGenerated/AddModified/Remove` (no `IsDeleted`); `History()` exists only on `BRepAlgoAPI_*`, `BRepFeat_MakeCylindricalHole`, `ShapeUpgrade_UnifySameDomain`; every other builder (`MakePrism/MakeRevol/MakeFillet/MakeChamfer/DraftAngle/MakePipeShell/ThruSections/MakeThickSolid/MakeDPrism/Transform`) has per-sub-shape `Generated(s)/Modified(s)/IsDeleted(s)` only; supported types vertex/edge/face/solid |
| taper | `LocOpe_DPrism(face, height, angle)` for a new body (height measured along the drafted wall; +3° on 100×60×10 → 59 085.191 mm³, 6 faces; −3° → 60 756.864, 10 faces incl. 4 conical corners); `BRepFeat_MakeDPrism` only for join/cut on an existing body |
| F1 `dir=Z` edges | FIVE raw (4 corners + the cylinder seam); OCCT silently ignores the seam in a fillet (`Generated(seam)` empty) |
| cancellation | none from Python: `Message_ProgressIndicator` is abstract with no trampoline; the sidecar deadline + kill/respawn is the ONLY guard |
| MCP timeouts | no server-side timeout; `kernel/script.py` MAX_SECONDS=120; server tests die at 60 s (`pytest-timeout`) |
| fixture arithmetic (Python 3.11, re-derived by two judges) | F1 area 15 357.080 mm²; fillet r2 ×4 vertical −34.336 (7→11 faces); chamfer 2×45° −80.000; counterbore Ø11×6 −98.96; countersink 90° Ø12 on Ø10 −16.76 extra; edit Ø10→Ø12 −345.575 → 58 869.027; section x=50 = 500 mm². F2 44 916.967 (13 faces after `UnifySameDomain`, 33 edges; t=8 → 58 403.27; t=4 → 30 790.66; mirror 89 833.933 / 17). F3 49 480.084 / 7 faces; section 2 700; keyway −611.9. F4 shell 15 552 / 11; draft 30 352.2. F5 520 481.421; disc 24 543.693 / 9. F6 30 429.204 / 3 141.593; Ø11 pin interference 329.867; cubes 400.000 @ (19.5,10,10); Ø9.9 clearance 0.050; steel 238.869 g / 24.662 g. F7 BA 4.524 (K 0.44), 4.398 (0.4), 4.712 (0.5); flat 76.524; bend zone 377.0. F8 1 060 faces, Σ 5 204 814.21. W1 bracket 91 158.6 mm³ / 715.6 g |

Licences (W1 audit + `tee_web_lookup` on PyPI JSON): OCCT LGPL-2.1-only + exception (text quoted in
the W1 report); cadquery-ocp / -novtk / -proxy Apache-2.0 (both OCP wheels ship the top-level
`OCP/` package — co-installing novtk into `server/.venv` clobbers the VTK wheel); cadquery
Apache-2.0 but eager casadi (LGPL-3.0+); build123d Apache-2.0 (pin `<0.12`: `bd_materials` has no
licence); py-slvs / SolveSpace GPL-3.0 no exception; fpdf2 LGPL-3.0-only; ezdxf/trimesh MIT;
numpy/scipy BSD; lib3mf BSD-2; bd_warehouse CSVs Apache-2.0 and threadlib BSD-3 are the clean
standards data; FreeCAD Fasteners GPL-2, BOLTS GPL-3, Wikipedia CC-BY-SA are never vendored.
Installed metadata is inconsistent (scipy/ezdxf/trimesh carry no `License-Expression`) — the gate
must map classifiers and free text (see P0b). Inventor (W2, 2026 help; 2027 ships): Windows-only
COM; headless = Apprentice (free, read-only) | Inventor Server inside the Vault Job Processor
(licence-bound) | Design Automation cloud ($3 per 12 processing minutes, 900 s default cap); no
macOS; no Autodesk-published Inventor MCP (third-party COM wrappers on Windows; the 2027 in-app
Assistant speaks MCP but "does not yet create or modify geometry"); $2,585/yr.

## Design of record

### D1. Package layout — `/Users/john/TokenEfficiencyEngine/partkiln/`

```
partkiln/  pyproject.toml  README.md  NOTICE  uv.lock  fixtures/F1..F8.json  examples/  tests/
  src/partkiln/
    __init__.py      __version__; imports nothing from OCP or tee
    units.py         "12mm"|"0.5in"|"3/8in"|12 -> mm; "90deg"|"1.5rad" -> deg; unknown suffix refuses naming accepted ones
    params.py        named params + AST-whitelisted expression evaluator (+ - * / ^ () unit suffixes, other params); no eval/sympy
    document.py      Command(op,args) frozen; Document(parts, assemblies, drawings, params, history); apply() = the ONLY mutator;
                     script()/replay(script, overrides=)/fingerprint(); closed _VERBS dict; regen(from_index)
    sketch/          model.py (entities TAGGED at creation, constraints by tag, driving|driven dims), solver.py (scipy least_squares;
                     DOF = n_params - rank(J), raw; status ok|under|over|conflict; conflicting[] leave-one-out; redundant[]), profile.py
    brep/            ALL OCP imports live here, lazily: shapes.py, history.py (hand-built BRepTools_History per feature: AddGenerated/
                     AddModified/Remove from algo.Generated/Modified/IsDeleted per sub-shape; Merge() with boolean + UnifySameDomain
                     histories; query IsRemoved), mesh.py (absolute deflection, sha256)
    features/        base.py + extrude revolve sweep loft hole fillet chamfer shell draft pattern mirror boolean split workplane
    naming.py        "<feature>.<role>[.<seg>|[k]]"; geometric fingerprint fallback; selector grammar; seam edges excluded by default;
                     resolve(): history -> fingerprint -> refuse with 3 nearest candidates
    assembly/        model.py (Component pose, grounded; Mate; Joint), solver.py (scipy; DOF = 6·n_free − rank(J)), interference.py,
                     clearance.py, bom.py
    drawing/         hlr.py (union of the three visible / three hidden compounds), views.py (base/projected/section/detail/aux; first/
                     third table; ISO -> first, ANSI -> third), dims.py (values READ from named sub-shapes), svg.py (own writer, native
                     arcs, Béziers via GeomConvert_BSplineCurveToBezierCurve), dxf.py (ezdxf real DIMENSION, $INSUNITS=4), pdf.py ([pdf])
    sheetmetal/      flat.py (Flat outline + Bend(line, angle, r, K)), fold.py derives the solid; BA = A·π/180·(R + K·T)
    exchange/        step.py iges.py brep.py stl.py obj.py(trimesh) threemf.py(trimesh; lib3mf optional) gltf.py (XCAF + LengthUnit
                     0.001 + Zup input CS + MergeFaces)
    checks/          validity.py mass.py wall.py (IntCurvesFace ray cast) spec.py ({pass, violations:[{rule,got,limit,fix}]})
    data/            clearance_holes.csv tap_holes.csv drill_sizes.csv iso4762.csv iso4014_4017.csv iso4032.csv iso7089.csv
                     iso261_pitch.csv materials.json manifest.json (source, licence, retrieved per file; loader refuses without all three)
    handoff.py       seamkiln's Target table; SOURCE = (partkiln, Z-up, right, 0.001 m); GLB needs no transform BECAUSE the writer rotates
    client.py        KernelClient Protocol + LocalKernel (in-process Document)
    worker.py        `python -m partkiln.worker`: persistent NDJSON loop over one Document; imports nothing from tee; fd-swaps stdout
```

`pyproject.toml`: MIT; `requires-python >=3.11,<3.15`; core `numpy scipy ezdxf trimesh`; extras
`brep = ["cadquery-ocp-novtk>=7.9.3,<8.0"]` (accept an already-present `cadquery-ocp` by
`find_spec("OCP")` — never co-install), `pdf = ["fpdf2>=2.8.8"]` (LGPL, optional; NOT named `sheet`),
`threemf = ["lib3mf>=2.4"]`, `dev`; BANNED comment block (cadquery, py-slvs, python-solvespace,
casadi, nlopt, pythonocc-core, bd_materials, gmsh, calculix, build123d in-process) with
replacements. Markers `slow`, `dcc`, `brep`. `NOTICE`: OCCT LGPL-2.1 + exception prominent notice,
bd_warehouse Apache-2.0, threadlib BSD-3.

### D2. Process model — one Protocol, two kernels, a warm job

`KernelClient` (`partkiln/client.py`; TEE imports it under `TYPE_CHECKING`, else `Any`):
`probe() info() warm()->dict apply(commands)->{results,diff} entities() detail(id) query(sel)
measure(spec) check(spec) export(spec) script() fingerprint() snapshot(label,dir) restore(payload)
discard(payload) shutdown()`.

- **`LocalKernel`** when `importlib.util.find_spec("OCP")` succeeds in the server interpreter (the
  repo dev venv). `find_spec` only — no import at probe. No cancellation exists in this mode, so
  `job: true` work still runs through `SidecarKernel` even in the dev venv (or is documented
  uncancellable).
- **`SidecarKernel`** (`server/src/tee/adapters/partkiln/wire.py`, copied from
  `gateway/wire.py:32-225`: `Popen(bufsize=0)`, newline-JSON, `_read_message(deadline)` with
  `select()` 1 s ticks and the non-JSON-line skip, `_dead()` closing then naming exit code + log).
  Spawns `~/TEE/.tee/sidecars/partkiln/bin/python -m partkiln.worker` (the `fleet/cad.py:206`
  discovery; overridable by `[partkiln] python` in `.tee/config.toml` — which needs a `partkiln`
  field in `server/src/tee/config.py`, see touch list). Persistent for the server's life; one lock,
  one request in flight. Request `{"id","method","params"}`; reply `{"id","result"|"error":{code,
  message,fix},"meta":{rss_mb,wall_ms}}` (meta never reaches the model); first line
  `{"event":"ready","occt":"7.9.3","import_s":…,"rss_mb":…}`. **This is the production route**: the
  extension venv (3.13.9) has no OCP and is wiped on every upgrade; the sidecar venv survives the
  wipe and `tee_purge` (`purge.py:78-88`). Doctor prints both interpreters' versions.
- **Warm-up (Law 17):** `_build_partkiln_app` submits `app.jobs.submit("partkiln_warm",
  kernel.warm, qos="interactive")` in BOTH modes; `warm()` returns `{"import_s", "rss_mb"}`.
  `probe()` = alive or importable, never waits. `execute()` waits `READY_GRACE_S = 2.0` then
  refuses `pk_warming` with the job id and the measured import time. **`list_entities()` and
  `snapshot()` answer from the in-process command mirror while warming** (`run_batch` calls
  `warm()` → `list_entities()` and then `checkpoints.create` → `snapshot()` BEFORE `execute()`,
  `app.py:300-304`); `snapshot()` then returns `brep: false` and restore replays.
- **Deadlines:** `[partkiln] batch_timeout_s = 60` (under MAX_SECONDS=120). `pk_export`,
  `pk_drawing`, `pk_script replay`, interference over > 20 pairs accept `job: true`. `MAX_BATCH_S`
  is predicted from P0 per-op-class wall times; a batch predicted over it refuses `pk_too_long`
  naming the job route. There is no per-op guard inside a running OCCT op.
- **Death is cheap:** history mirrored in-process; a dead worker is respawned and the script
  replayed (0.09–0.46 s per 100 cuts), noted in the diff; `rss_cap_mb = 4096` → planned restart.
- `fleet/cad.py cad_measure` keeps its one-shot sidecar in v1 (routing through `pk_measure` = gap).

### D3. Checkpoints — the script is the state, the B-rep is a cache

`snapshot(label)` → `<project>/.tee/partkiln/<label>-<epoch>-<ms>.json` = `{script, fingerprint,
names}` + one `.brep` per part (`BRepTools.Write_s(shape, path, False, False,
TopTools_FormatVersion_VERSION_3)`); returns scalars `{label, path, epoch, commands, fingerprint,
brep}`. `restore()`: reload the script → if every `.brep` exists, read shapes (1 ms), install
names, recompute `fingerprint()`; mismatch or missing → full `Document.replay` (the seamkiln law);
missing json → `pk_checkpoint_missing` naming `tee_purge`. `discard_snapshot()` unlinks both
(`checkpoints.py:105-113` hook). Fingerprint = sha256 of sorted per-part (name, round(volume,6),
sorted per-face (surface type, round(area,3), round(centroid,3))) + poses 1e-6 + per-view counts.

### D4. Units and exchange

Kernel and wire in **mm / deg** (the fabrication-lane convention; STEP `write.step.unit=MM`).
Unit-suffixed strings accepted everywhere a length/angle is; bare numbers = document unit with
`assumed` echoed once; `set doc strict_units=true` makes bare numbers a refusal.

| Format | Mechanism | Trap pinned by a test |
| --- | --- | --- |
| STEP AP242 (default) / AP214 / AP203 | `STEPControl_Controller.Init_s()` → `SetCVal_s("write.step.schema","AP242DIS")` BEFORE the first `Transfer` → `STEPCAFControl_Writer` (name/colour/layer modes; `ChangeWriter().Model(True)` if reused) → assert `FILE_SCHEMA` contains `AP242` | Transfer-then-SetCVal stays AP214 (negative test) |
| IGES | `IGESControl_Writer` under the one lock (not thread-safe) | — |
| BREP | `BRepTools.Write_s` VERSION_3, no triangulation | — |
| STL | `BRepMesh_IncrementalMesh(shape, defl, False, 0.5, True)` + `StlAPI_Writer` | build123d's `tolerance` is RELATIVE; ours is absolute |
| OBJ / 3MF | trimesh (`export_3MF` writes `unit="millimeter"`); lib3mf optional | `OCP.RWObj` unbound |
| GLB | XCAF doc + `SetLengthUnit_s(doc, 0.001)` + `ChangeCoordinateSystemConverter().SetInputCoordinateSystem(RWMesh_CoordinateSystem_Zup)` + `SetMergeFaces(True)`; read back through `tee.assets.gltf.probe(Path)` | two negatives: no LengthUnit → [100,60,10]; no input CS → unrotated [0.1,0.06,0.01] |
| DXF / SVG / PDF | ezdxf real `DIMENSION`s (`$INSUNITS=4`); own SVG writer with native arcs; fpdf2 in `[pdf]` | HLR compounds (D6) |
| Import STEP/IGES/BREP | `STEPCAFControl_Reader` → parts with names; sub-shapes fingerprint-named | — |
| Out | DWG (libredwg GPL), USDz (A53 Gap 1), Parasolid/SAT/JT, `.ipt/.iam/.idw` | — |

### D5. Wire vocabulary for `tee_batch` (closed, enumerable; unknown op/kind → `pk_bad_op` listing every verb)

Every op takes `name` (≤ 24 chars `[a-z0-9_]`; omitted → `<kind><n>`); children of multi-instance
ops are `h.1, h.2 …`. A param name or expression (`"W/2 - 5mm"`) is legal wherever a length is.
Required in **bold**; defaults echoed in `details[id].assumed`.

| op / kind | props | assumed |
| --- | --- | --- |
| `param_set` | **`{name: value…}`** (create-or-set; expressions) | — |
| `set doc` | `units`, `standard ISO\|ANSI\|DIN`, `angle first\|third`, `strict_units` | doc defaults echoed once per session |
| `create part` | `name`, `material` | material none |
| `create sketch` | **`plane`** (`XY\|XZ\|YZ\|plane:<n>\|on:"<face ref>"`), **`profile`**: `{rect:[w,h],at,tag}` `{circle:d}` `{slot:[len,w],angle}` `{polygon:n,d}` `{poly:[[x,y]…],tags}` `{arc:{from,to,r\|center}}`; `constraints:[{c, on\|a\|b}]` (coincident collinear concentric fix parallel perpendicular horizontal vertical equal tangent symmetric smooth); `dims:[{d:len\|dist\|angle\|dia\|rad, on\|a\|b, value, driven}]` | `at [0,0]`, `angle 0` |
| `create extrude` | **`sketch`**, **`distance`** or `to:"<face>"`/`"through"`, `direction +\|-\|both`, `mode new\|join\|cut\|intersect`, `taper` | `+`; `new` if part empty else `join`; taper 0 |
| `create revolve` / `sweep` / `loft` | **`sketch`**,**`axis`**,`angle` / **`profile`**,**`path`**,`frenet` / **`sections`**,`ruled`; `mode` | 360 / false / false |
| `create hole` | **`on`** (face ref), **`at`** `[[x,y]…]` in the face frame; one of **`dia`** / `std:"M6 clearance normal\|close\|loose"` / `std:"M6 tap"`; `depth through\|<len>`; `seat:{kind:counterbore\|countersink\|spotface, dia, depth\|angle}`; `thread:"M6"` (cosmetic) | depth through; std source echoed |
| `create fillet` / `chamfer` | **`edges`**, **`r`** or `[r1,r2]` / **`d`** or `[d1,d2]` or `{d,angle}` | none — refuses if missing (design intent) |
| `create shell` / `draft` | **`faces`**,**`t`**,`direction` / **`faces`**,**`angle`**,**`neutral`** | in |
| `create pattern` / `mirror` | **`of`**, `kind rect` **`dx,nx`**,`dy,ny` / `circ` **`axis,n`**,`angle` / `sketch` **`points`**; `suppress:[i]` / **`of`**,**`plane`** | 360 |
| `create combine` / `split` / `plane\|axis\|point` | **`bodies`**,**`mode`** / **`body`**,**`plane\|face`** / `offset\|through\|angle\|normal_at\|midplane` | — |
| `create component` / `mate` / `joint` | **`part`**,`at`,`rot`,`grounded` / **`kind mate\|flush\|angle\|tangent\|insert`**,**`a`**,**`b`**,`offset` / **`kind rigid\|revolute\|slider\|cylindrical\|planar\|ball`**,**`a`**,**`b`**,`offset`,`limits` | first component grounded; no `fit` in v1 |
| `create drawing` | **`of`**, `sheet A4L..A0L\|ANSI_B`, `standard`, `angle`, `scale`, `views:[{name,dir front\|top\|right\|iso\|section:<plane>\|detail:{of,r}\|aux:<face>}]`, `dims:[{name,view,kind extent\|dist\|dia\|rad\|angle\|chamfer\|ordinate\|baseline,axis,of\|a,b}]`, `hole_table`, `parts_list`, `title` | angle follows the standard (ISO→first, ANSI→third); 1:1 |
| `create sheet` (P5b) | **`t`**, **`width`**, **`flanges:[{len,angle,r,dir}]`**, `k`, `holes`, `relief` | k 0.44 (declared, see P5b); r = t |
| `set` / `delete` | `id`,`props` (any creation prop, `suppressed`, `material`, `name`) / `id`, `cascade` | delete refuses naming dependents unless cascade |
| `export` | **`format`**, **`out`**, `of`, `schema`, `tol`, `target blender\|unreal\|godot`, `job` | AP242; 0.05 mm |
| `check` | `spec`, `strict` | strict → refuse on violation |

`create object` (the contract's generic kind) is accepted as a BOM virtual component so the packaged
`AdapterContract` runs on the fake. Reads (measure/BOM/tree/standards) are `pk_*` tools.

### D6. Names and selectors

Roles per kind, materialised from the hand-built merged history (D1 `brep/history.py`): after
fuse/cut the kernel applies `ShapeUpgrade_UnifySameDomain(unifyEdges, unifyFaces)` and merges its
history (the face-count pins assume it). `extrude.start/.end/.side.<segtag>`;
`revolve.outer/.inner/.cap.a/.b`; `hole.wall/.bottom/.seat`; `fillet.face[i]`; `shell.inner[i]`;
imported bodies `import.face[k]` (fingerprint only). Fingerprint per sub-shape = (surface/curve
type, area/length, centroid/midpoint, normal) rounded 1e-3 mm. **Selectors** are declarative strings
evaluated at regen and materialised to names in the diff: `"<feature|part>:faces(<f>)"` /
`":edges(<f>)"` with filters `normal=+Z`, `dir=Z`, `of=<role>`, `loop=outer|inner`, `type=plane|cyl|
cone|sphere|torus|bspline`, `r=`, `len>`, `area>`, `convex|concave`, `nearest=[x,y,z]`,
`created_by=`, `not()`. **Seam edges are excluded by default** (`BRep_Tool.IsClosed_s(e, f)` on any
ancestor face) and reported (`seam edges excluded: 1`). Cardinality is declared by the consuming
field (`on` = 1, `edges` = many): 0 → `pk_ref_empty`, >1 where 1 → `pk_ref_ambiguous` with
candidates; `details[id].resolved` echoes `{"plate:edges(dir=Z)": 4}`. A fillet/chamfer edge whose
`Generated(edge)` is empty is reported `failed` for that edge (Law 11), never silently accepted.
Resolution after regen: history → fingerprint (Δ ≤ 1e-3) → `pk_ref_stale` naming the history event
("removed by hole h"), the nearest candidate with its Δ mm, and the selector form that would survive.

### D7. Entity model and diff contents

Ids `<prefix>:<name>`; `kind` is the feature kind; concise rows ~20 tok; a 12-feature part ~300 tok.
Everything a batch can change is an entity, and every created/modified entity reaches `Diff.upserts`.

| id | kind | summary (scalars only; `tee_entity_detail` adds) |
| --- | --- | --- |
| `doc` | doc | units, angle, standard, parts, components, features, drawings, fingerprint, script_commands |
| `param:W` / `plane:XY` | param / datum | value, unit, expr, used_by / origin, normal |
| `sk:base` | sketch | plane, entities, constraints, dof, status, conflicts, area_mm2, used_by |
| `feat:plate` | extrude/fillet/hole/… | status, params, refs, volume_mm3, delta_mm3, faces, edges, roles, downstream, suppressed |
| `part:bracket` | body | volume_mm3, area_mm2, bbox_mm, com_mm, solids, faces, edges (unique), valid, material, mass_g, fingerprint |
| `cmp:` / `mate:` / `jt:` / `asm` | component / mate / joint / assembly | part, grounded, pose / kind, a, b, dof_removed / components, dof, interference, residual |
| `dwg:` / `vw:` / `dim:` | drawing / view / dimension | sheet, standard, angle, files / dir, visible_edges, hidden_edges / kind, refs, value_mm, projected_mm, agree |
| `sheet:` / `export:` | sheet / export | t, k, bends, flat_mm, ba_total_mm / format, bytes, units, declares_units, roundtrip |

Per-op `details` (volumes 2 dp, lengths 3 dp): any feature `{status, volume_mm3, delta_mm3, bbox_mm,
faces, edges, solids, assumed, resolved, names (≤ 8)}`; cut/hole/combine `+ no_effect` (refuses,
Law 11); `set`/`param_set` `{changed:[{feature, delta_mm3, faces}], unchanged:n, failed:[…],
volume_mm3, fingerprint}`; sketch `{entities, constraints, dof, status, conflicts, redundant,
closed, area_mm2, frame}`; one `details.asm` per batch `{components, dof, grounded, residual,
interference:[{a,b,mm3,centroid}], clearance_mm, contacts}`; view `{visible_edges, hidden_edges}`;
dimension `{value_mm, projected_mm, agree}`; export `{path, bytes, format, units, roundtrip,
watertight, triangles}`; check `{verdict, violations:[{rule, got, limit, fix}]}`. `notes`: one line
per material fact. No `ms` on the wire.

### D8. Assume/needs and refusals

Defaults declared once (`assumed`). A self-contradictory spec raises ONE `pk_spec_conflict` whose
`fix` is a numbered `needs:` list (≤ 3, each with options) collected across the batch; a required
field with no safe default (`fillet.r`) refuses `pk_needs`. `run_batch` appends "Batch rolled back to
checkpoint …". Codes: `pk_bad_op pk_kernel_absent pk_not_served pk_warming pk_too_long
pk_plane_missing pk_plane_mismatch pk_unit_unknown pk_unit_kind pk_unitless pk_ref_unknown
pk_ref_stale pk_ref_ambiguous pk_ref_empty pk_no_effect pk_sketch_overconstrained pk_sketch_open
pk_spec_conflict pk_needs pk_part_ambiguous pk_delete_blocked pk_op_failed pk_checkpoint_missing
pk_capture_text_first` — each message names the geometry (frame origin/normal, bbox, history cause,
nearest candidate + Δ mm, `NbFaultyContours` + the edge + the face height) and the exact fix.

### D9. Virtual tools (14; each an explicit `_EXPLICIT` row; **no `_FAMILY` row** — the `cad_`/`trade_` rule at `trust.py:179-188`)

| tool | capability | first line |
| --- | --- | --- |
| `pk_probe` | read-compute | Kernel health: OCCT/OCP version, mode (in-process\|sidecar\|absent), warm state, formats, licence notices. |
| `pk_verbs` | read-scene | The batch vocabulary for parts, assemblies, drawings, sheet metal — one example op per kind. |
| `pk_lint` | read-compute | Pre-flight a batch without the kernel: schema, units, unresolvable refs, predicted sketch DOF, structured needs. |
| `pk_query` | read-scene | Resolve a selector to names with sub-shape facts; the feature tree as text; changes since a revision. |
| `pk_measure` | read-compute | Numbers not pixels: mass, clearance, interference, min wall, section area, face inventory — live document or a STEP/BREP/STL path. |
| `pk_check` | read-compute | Verify a spec: bbox, hole dia/count, min wall, watertight, volume/mass bands, zero interference, DOF → verdict + violations with the fix. |
| `pk_standards` | read-compute | Clearance/tap/drill for a bolt (ISO 273/262 via bd_warehouse), ISO 4762/4014/4017/4032/7089 — with source and licence. |
| `pk_materials` | read-compute | Material cards (density, E, yield) with an honesty tier per value. Pure lookup — assignment is `set part material=` in a batch. |
| `pk_bom` | read-scene | Bill of materials: structured or parts-only, qty, material, mass, standard designations. |
| `pk_drawing` | write-artifacts | Write a dimensioned sheet to SVG/DXF/PDF: views, sections, dims read back from the model, hole table, parts list, title block. |
| `pk_export` | write-artifacts | STEP AP242/214/203, IGES, BREP, STL, OBJ, 3MF, GLB, DXF with a handoff manifest (units, up axis) for Blender/Unreal/Godot; round-trip verified. |
| `pk_flat` | write-artifacts | Sheet-metal flat pattern: BA/BD per bend (K or bend table), flat extents, bend lines; DXF layers OUTLINE/BEND_UP/BEND_DOWN/HOLES. |
| `pk_import` | write-scene | Import STEP/IGES/BREP as a base body with fingerprint-named faces; reports units, solids, validity. |
| `pk_script` | write-scene | The document as a replayable script: dump, replay (job when long), replay with param overrides (the part family), compare fingerprints. |

Tags singular AND plural (words ≤ 2 chars drop — `M6` never scores; tags match by substring).
Ranking pins (top-3): "extrude a sketch"/"add a fillet"/"mate two parts" → `pk_verbs`; "drawing
with dimensions" → `pk_drawing`; "export STEP" and "hand off part to blender" → `pk_export`; "bill
of materials" → `pk_bom`; "sheet metal flat pattern" → `pk_flat`; "clearance hole for M6 bolt" →
`pk_standards`; "assembly interference check" → `pk_measure`.

## Laws

A53's ten stand verbatim ("garment" read as "part"): measured before and after; the licence gate is
a test; the GUI is a client of the core; zero new always-loaded tools; diffs over snapshots, text
over pixels; a refusal names its reason and the fix; determinism is a feature; the model's eye is
advice; feature parity, not container parity; the metric is tokens per completed part task. From
A65: 14 (the line you changed last), 17 (a self-describing format is left alone), 19 (use it, don't
just test it). New for this lane:

11. **A boolean that changes no topology is a failed boolean** — `pk_no_effect` unless `allow_no_effect`.
12. **A bare number is millimetres/degrees, and the diff says so once**; `strict_units` is opt-in.
13. **A sub-shape is addressed by name, never by index.** History → fingerprint → refuse with candidates.
14. **An edit reports its blast radius**: every downstream feature `changed/unchanged/failed` with Δvolume.
15. **A drawing dimension is read back from the model, never typed.**
16. **The checkpoint is the script; the B-rep is a cache.** A failed batch never advances state.
17. **Cold import never blocks a call** (A46): warm-up is a job; a call during warm-up refuses with the job id.
18. **Cosmetic is cosmetic**: a thread note that moves volume or fingerprint is a bug.
19. **Ask only when the spec is inconsistent; otherwise default and declare.** One `needs:` list per batch.
20. **Counts are unique sub-shapes** (`TopExp.MapShapes_s`), never explorer visits.

## Phases (each independently shippable; commit + PROGRESS entry per item)

**Step 0 — housekeeping.** `git status` shows uncommitted A65 follow-up work in `seamkiln/`
(dressing/solve/figure, examples incl. `_blender_body.py`, three tests, PROGRESS, the lane doc).
Commit it under its own subject before P0a. A66 never touches `seamkiln/`.

### P0 — measure, then gate (commit P0a/b/c separately)

**P0a — the measurement table** (scratchpad, `uv venv --python 3.11`; every cell into PROGRESS):

| # | What | Expected / decides |
| --- | --- | --- |
| 1 | Cold `import OCP` on a FRESH novtk venv and a fresh vtk venv (a fresh venv is the cold code-signature case), warm ×3 | novtk ≤ 10 s cold, 0.3–1.2 s warm; NOT 140 s; decides whether the warm job alone suffices |
| 2 | `du -sh` novtk site-packages; `otool -L OCP.*.so \| grep -c vtk` | ≈ 250–300 MB vs 1.4 GB; **0** VTK dylibs → the CI `kiln` job cost |
| 3 | `unzip -l` both wheels `\| grep -c 'OCP/'` | both ship `OCP/` → co-install hazard recorded; `[brep]` accepts either by `find_spec` |
| 4 | Binding coverage on novtk (the 26-class one-liner incl. `LocOpe_DPrism`, `HLRBRep_HLRToShape`, `RWMesh_CoordinateSystem`) | all import (the vtk-wheel result must transfer) |
| 5 | Prototype 60-line NDJSON worker: spawn→`ready`, first and 100th `measure` | first = row 1 + ~50 ms; steady ≤ 2 ms |
| 6 | RSS after import and after F5 | recorded (2 job workers × residency) |
| 7 | F5: 100 sequential cuts vs one n-ary cut (NO glue), `SetRunParallel` | 0.46 s vs ≈ 0.09 s; 520 481.421; 106 faces; 312 unique edges; glue-mode negative pinned (uncut plate, IsDone True) |
| 8 | HLR per compound under NAMED projectors on F1 and on W3's 12-hole/96-fillet plate; exact vs PolyAlgo on 530 faces | F1 front V 4 \| H 9 + OutLineH 1 etc.; the 96-fillet plate has `VCompound` empty; exact ≈ 0.1–0.2 s |
| 9 | STEP: `CVal_s` before/after `Init_s`; AP242DIS set before Transfer → `FILE_SCHEMA` AP242; Transfer-then-set stays AP214; names round-trip | `'' → AP214IS → AP242DIS` |
| 10 | F8 import via `STEPCAFControl_Reader` | ≤ 1 s; 10 products; Σ 5 204 814.21 |
| 11 | BRepMesh SHA-256 serial vs 3× parallel at 0.05/0.3 | identical (pinned) |
| 12 | B-rep fingerprint of F2 and F6 in two fresh processes | identical |
| 13 | GLB of F1 with LengthUnit + Zup input CS, and both negatives, through `tee.assets.gltf.probe(Path)` | `[0.1, 0.01, 0.06]` / `[100, 60, 10]` / `[0.1, 0.06, 0.01]` |
| 14 | BREP checkpoint vs replay for F5 | 81 KB / ≤ 5 ms / ≤ 2 ms vs ≤ 0.5 s |
| 15 | History on F1 fillet via `MakeFillet.Generated/Modified` per sub-shape | end face → 1 modified; each vertical edge → 1 fillet face; the seam → 0 |
| 16 | Own scipy sketch solver vs `py_slvs` driven DIRECTLY in mm (dev-only oracle from `server/.venv`, never a partkiln dep) on 20 anchored sketches | coordinates ≤ 1e-6 mm or the measured floor recorded; DOF equal on 20/20 |
| 17 | Per-op-class wall times (extrude, hole ×1/×100, fillet ×8/×96, boolean, HLR, STEP write/read, GLB) | the basis of `MAX_BATCH_S` and the `job` threshold |
| 18 | Fixture provenance: read the HF dataset-card `license:` for BenchCAD and `huggingface/cadgenbench-data` via `tee_web_lookup`/browser | recorded in `fixtures/third_party/ATTRIBUTION.md` before ANY third-party file lands; until then F1–F8 only |

**P0b — the licence gate** `partkiln/tests/test_licences.py`: seamkiln's `BANNED` dict (reason +
replacement: py-slvs, python-solvespace, cadquery, casadi, nlopt, pythonocc-core, bd_materials, gmsh,
calculix) + `NON_COMMERCIAL_MARKERS` PLUS an SPDX **allowlist** `{MIT, BSD-2/3-Clause, Apache-2.0,
ISC, PSF-2.0, 0BSD, Zlib, CC0-1.0}` (no MPL — Law 2 stays literally true) over the transitive
closure of core + `[brep]`, with `_spdx_of(dist)` = `License-Expression` → Trove classifier map →
free-text alias table (`"The MIT License (MIT)"`, `"BSD"`, `"Apache Public License 2.0"` …), failing
only when all three are empty; `AND/OR/WITH` parsed with `packaging.licenses.
canonicalize_license_expression`, every AND operand allowlisted. `KNOWN_PAYLOADS` keyed on BOTH
`cadquery-ocp` and `cadquery-ocp-novtk` = `("LGPL-2.1-only WITH OCCT-exception-1.0", url, date)`;
`cadquery-ocp-proxy` allowlisted; the live carrier resolved via `packages_distributions()["OCP"]`
and asserted in `KNOWN_PAYLOADS`; a declared-but-uninstalled extra dependency `pytest.skip`s naming
the extra, a missing core dependency FAILS; `NOTICE` asserted present naming OCCT unconditionally;
`[pdf]` (fpdf2) allowed only in its extra; deliberate failures parametrised over py-slvs, cadquery,
casadi, a licence-less fake, an `LGPL-3.0-only` fake in core, plus classifier-only BSD must PASS
and free-text "GNU Lesser General Public License v3" must FAIL; `test_import_hygiene` (`import
partkiln` never loads `tee cadquery casadi vtkmodules py_slvs fpdf OCP`);
`test_data_files_carry_provenance` (every CSV/JSON card: `source`, `licence`, `retrieved`; none
cites Fasteners/BOLTS/Wikipedia tables); `BANNED_DATASETS` (Fusion 360 Gallery, Text2CAD, CAD-Recode,
GenCAD-Code) scanned over `fixtures/`; `test_no_autodesk_marks_in_shipped_names` with an
enumerated `MARKS` list (`autodesk inventor forge fusion vault nastran anycad ilogic ipart
iassembly ifeature imate apprentice "content center" "design accelerator"`) matched as whole tokens
over the package name, tool names, verbs, entity kinds, VirtualTool descriptions/tags, pyproject
name/description and `data/manifest.json` — **not docs**.

**P0c — the FreeCAD-not-kernel ruling** pasted into PROGRESS + DECISIONS (crash output, 0.38 s /
67 MB, OCCT 7.8.1, index constraints).

*Acceptance:* every cell of the 18-row table filled; warm `import OCP` ≤ 1.5 s; cold ≤ 30 s or the
sidecar design re-justified in writing; novtk links 0 VTK dylibs; all classes bound; spawn→ready ≤
warm + 0.5 s; GLB F1 reads `[0.1, 0.01, 0.06]`; mesh hash identical ×3; fingerprints identical ×2;
solver oracle agrees 20/20; the gate fails on all intruders and passes the tree.

### P1 — document, units, params, sketch (no OCCT)

*Acceptance:* unanchored 100×60 rectangle (4 lines, H/V/equal + 2 dims) → `dof=2`; after `fix p1` →
`dof=0`, solved to 1e-6 mm; minus one distance → `dof=1, status=under`; a conflicting 61 mm →
`status=conflict` naming both dims; a duplicated horizontal → `redundant` names it; 40-entity /
60-constraint sketch < 50 ms; `"0.5in"` → 12.7; bare `12` → 12 mm with `assumed` once; `"12 mils"`
refuses naming accepted suffixes; `"W/2 - 5mm"` evaluates, `__import__` refuses;
`Document.replay(script).fingerprint()` equals the original on 20 random command sequences;
`replay(script, overrides={"t": "8mm"})` differs; `import partkiln` with OCP absent succeeds.

### P2 — the part kernel (features, naming, checks, exchange)

*Acceptance* (warm, this Mac; numbers from the EXPECTED table): F1 ≤ 30 ms, 59 214.602 to 1e-6; F5
via n-ary cut ≤ 0.2 s, 520 481.421, 106 faces, 312 edges; fillet `plate:edges(dir=Z)` → resolved 4,
`seam edges excluded: 1`, −34.336, faces 7→11; chamfer −80.000; F2 44 916.967 / 13 faces; F3
49 480.084 / 7; sweep 3 715.7 ± 0.5; loft 28 000; F4 shell 15 552 / draft 30 352.2; counterbore
−98.96; countersink −16.76 beyond the Ø10; taper +3° via `LocOpe_DPrism` 59 085.191 / 6 faces with `height="along_wall"`
(the default `vertical` semantic gives 59 165.138 with z max 10.000) and
−3° 60 756.864 / 10 faces; keyway −611.9 ± 0.1; mirror 89 833.933 / 17; circular 24 543.693 / 9;
suppress 3 → 97; cosmetic thread leaves the fingerprint bit-identical; **edit impact**: Ø10→Ø12 →
`changed:[hole1 −345.575]`, `fillet1 unchanged`, part 58 869.027; editing F2's `t` regenerates every
downstream feature with no silent re-target (face-reorder test resolves through fingerprint or
refuses with 3 candidates); a cut that removes nothing → `pk_no_effect`; fillet r=12 on F1's top-
front edge (10 mm plate) refuses naming the edge and `NbFaultyContours=1`; draft on a torus face
refuses naming the type; STEP AP242 round trip volume 1e-9 relative + names + `FILE_SCHEMA`; IGES
1e-6; STL watertight, bytes identical on repeat; OBJ/3MF reload within 0.1 %; GLB `[0.1, 0.01, 0.06]`
plus both negatives; BREP checkpoint ≤ 5 ms / restore ≤ 2 ms, replay fallback when the file is
deleted; `check_wall` finds a 1.2 mm wall under a 2 mm limit; fingerprint identical in two fresh
processes; 12 deliberate-failure tests each one `CommandError` naming feature + fix.

### P3 — assemblies

*Acceptance:* F6 block + pin: joint kinds → DOF **0 / 1 / 1 / 2 / 3 / 3**; insert + mate solves the
pin to (20, 20, 20) ± 1e-6, residual < 1e-9, ≤ 200 ms; remove one mate → `dof=1` named per component;
rigid + contradictory 5 mm offset → `over_constrained:["mate2"]`, residual 5.000; Ø11 pin
interference **329.867 mm³** + centroid; two 20 mm cubes at x=0/19 → 400.000 @ (19.5, 10, 10); Ø10 in
Ø10 → 0 with `contact: true` (`SetFuzzyValue` policy documented); Ø9.9 → clearance 0.050; 4-pin
pattern → BOM parts-only `[{block,1},{pin,4}]`, steel 238.869 g / 24.662 g, total 337.517 g; `create
object` lands as a BOM virtual component; plate + 4× ISO 4762 M6 from `data/` solves ≤ 200 ms.

### P4 — the TEE adapter (`server/src/tee/adapters/partkiln/`; pull forward after P2 if the co-pilot needs it)

Seven methods per `kernel/adapter.py`: `info()` (`extra={mode, state, occt, parts, assemblies,
drawings, commands}`), `probe()` (never waits), `list_entities()` (D7, from the mirror while
warming), `execute()` (pure `_translate(op, index)` → one `apply(commands)` round trip; `_record`
writes `created/modified/deleted/details/notes` AND `upserts`), `snapshot/restore/discard_snapshot`
(D3), `capture()` refuses honestly in v1 (`pk_capture_text_first` naming `pk_drawing` SVG,
`pk_measure`, `tee_entity_detail`; P6 adds opt-in JPEG through Blender). `_need()` refuses only when
BOTH routes are absent; the hint names both — dev venv `uv pip install --python
server/.venv/bin/python -e partkiln` (NO `[brep]`: OCP is already there and novtk would clobber it);
production `uv venv --python 3.11 ~/TEE/.tee/sidecars/partkiln && uv pip install --python
~/TEE/.tee/sidecars/partkiln/bin/python -e <repo>/partkiln[brep]`. `tools.py` registers the 14 tools
(module imports only `typing`/`TeeError`/`VirtualTool`; every handler starts `_need()` then
`_adapter(app)`). `pk_lint` and the assume/needs protocol land here.

*Acceptance:* `surface: 17 always-loaded tools = 2033 tok on the wire` (± 10) and
`test_always_loaded_surface_delta_is_zero`; `tee_scene_summary` on the 12-feature bracket ≤ 400 tok;
the W1 batch returns ONE diff naming every created id with volume/faces, `assumed` once, `resolved`
counts; a failed 3rd op rolls back and the fingerprint equals the pre-batch one; `pk_no_effect`
refuses the batch; `pk_lint` catches a bad unit, a stale ref and a spec conflict with the kernel
never called (spy); checkpoint/rollback round-trips through the `.brep` fast path AND through replay;
a sidecar killed mid-session respawns and replays to an identical fingerprint; `pk_warming` measured
on a cold sidecar (`@pytest.mark.timeout(300)`, `-m dcc`; the default suite spawns a warm sidecar
from `sys.executable`); `snapshot()` during warming returns `brep: false`; all 14 tools tabled
(startup boots), `capability_for("pk_drawing") == "write-artifacts"`, `capability_for("pk_script")
== "write-scene"`, no `pk_` in `_FAMILY`; 10 ranking pins top-3; `TestPartkilnAdapterContract` green
on `FakeKernel` with no OCCT; `test_partkiln_translate.py` green with no kernel;
`benchmarks/RESULTS.md` section "draft a bracket, drill it, draw it, export STEP" with both naive
bounds and the edit row; server suite ≥ 1,224 passed; `make lint` clean.

### P5 — drawings (P5a) and sheet metal flat-first (P5b)

*P5a acceptance:* F1 front/top/right per-compound counts as measured (front V 4 | H 9 + OutLineH 1;
top 5 | 5; right 4 | H 10 + OutLineH 2), HLR ≤ 30 ms per view; the 96-fillet plate front view is
non-empty although `VCompound` is empty (the trap fixture); on all-filleted F1 `visible_union >
len(VCompound)`; third angle places top ABOVE front, first below, the default follows the standard;
section at x=50 hatch area 500.000, F3 longitudinal 2 700.000, counterbored F1 section reads seat
depth 6.000; detail 2:1 reports scale 2 and Ø10.000; dims read back: extents 100.000 / 60.000,
Ø10.000, R2, angular 3.000° on the draft, baseline 20…200 on F5, ordinate identical; hole table 100
rows; F2 note `4× Ø6.6 THRU (M6 clearance, ISO 273 medium)`; `dimension.agree == true` on every dim;
SVG parses and a 100 mm line is 100 user units, hidden lines dashed and counted; DXF `$INSUNITS=4`,
`DIMENSION.get_measurement()` = 100.0 / 60.0 / 10.0; PDF (`[pdf]`) A3 landscape mediabox
1190.55 × 841.89 pt via pypdf with title-block text extractable; parts list 2 rows + 2 balloons on F6.

*P5b acceptance:* F7 (T=2, R=2, K=0.44, 90°, outside legs 50/30, W=40): `ba_mm` **4.524**, `bd_mm`
3.476, flat length **76.524**, bend-zone volume 377.0 (K-independent, and the test says so); K
parametrised → 4.398 at 0.4, 4.712 at 0.5; folded − flat volume reported with the explaining note;
`pk_flat` DXF layers `OUTLINE/BEND_UP/BEND_DOWN/HOLES`, `$INSUNITS=4`; **K = 0.44 is declared as this
kernel's default choice inside the typical 0.3–0.5 range** (BA/OSSB/BD formula cited to Wikipedia
"Bending (metalworking)" CC BY-SA 4.0 citing Industrial Press 1994 — a formula citation, no table
copied; no standard fixes K; pass `k` or a bend table for production parts); DIN 6935 `k` named as a
different quantity.

### P6 — evidence, interop, ship

Handoff bundles (Blender via `import_file`; Unreal via the content plugin with m→cm; Godot/others
"drop-in" refusals per `handoff.ops_for`), capture-through-Blender opt-in, `docs/partkiln-lane.md`,
`docs/setup-partkiln.md`, `docs/research/68-mechanical-cad-lane.md` (doc 67's section shape, from
the seven discovery reports in the session scratchpad), `docs/research/00-index.md` row, DECISIONS
`## A66 — the mechanical CAD lane (2026-09-02)` (OCCT LGPL+exception; cadquery excluded for casadi/
VTK; py-slvs GPL → own solver; casadi → scipy; fpdf2 optional; bd_warehouse/threadlib data; FreeCAD-
not-kernel; CI split; mm on the wire; K default), CHANGELOG **0.19.0 (missing today) AND 0.20.0**,
`CLAUDE.md` bullet, PROGRESS close-out with the before/after table and numbered gaps (1 GUI; 2
`cad_measure` routing; 3 capture; 4 CI cost; 5 coil/threads; 6 ISO 286 fits; 7 `pdf_compose` vector
block), version bump ×3, `make mcpb`, clean-unzip verify, the acceptance session recorded verbatim.

*Acceptance:* bundle lines verbatim — `handshake: {'name': 'tee', 'version': '0.20.0'}`,
`always-loaded tools: 17`, `search 'extrude a sketch' reaches pk_*: True`, `pk_probe from the bundle
-> REFUSED (kernel absent, as expected)` or `mode: sidecar`; `tee doctor` shows `partkiln` OK naming
mode + OCCT + both interpreter versions; Blender receives the bracket GLB upright with `verify.ok`
(read-back XYZ unsorted); the ten-step session green with every number matching; **Suites at close**
line with both counts; surface unchanged.

## TEE touch list

**ADD**

| path | content |
| --- | --- |
| `partkiln/` (repo root) | D1 in full; `NOTICE`; `fixtures/F1..F8.json`; `tests/expected.py` (ONE `EXPECTED` table); `examples/{bracket,shaft_housing,sheet_bracket,acceptance}/` with `--probe` |
| `server/src/tee/adapters/partkiln/__init__.py` | `from .adapter import PartkilnAdapter; __all__` |
| `server/src/tee/adapters/partkiln/adapter.py` | seven methods; `INSTALL_HINT`; `_need_partkiln()`; lazy kernel; `_translate`/`_WIRE_OPS`/`_PASSTHROUGH`; `_record` with `upserts`; D3 checkpoints; `discard_snapshot` |
| `server/src/tee/adapters/partkiln/wire.py` | `SidecarKernel` (from `gateway/wire.py:32-225`); imports nothing from partkiln |
| `server/src/tee/adapters/partkiln/tools.py` | `register_partkiln_tools(app)`; 14 `VirtualTool`s; `_need()`; `_adapter(app)` |
| `server/tests/fixtures_partkiln.py` | `FakeKernel` implementing `KernelClient` with analytic geometry (no OCCT) — the `fixtures_freecad.py` pattern |
| `server/tests/test_partkiln_adapter.py` | `class TestPartkilnAdapterContract(AdapterContract)` over `FakeKernel` + trust assertions + 10 ranking pins + `assert len(_DESC) == 17` + no `pk_` in `_DESC` + upserts-for-every-created + atomicity |
| `server/tests/test_partkiln_translate.py` | no kernel: `_translate`, ids, units, refusals, verb completeness vs `partkiln.document.VERBS` when importable |
| `server/tests/test_partkiln_live.py` | `importorskip("OCP")`: real `LocalKernel` + a warm `SidecarKernel` from `sys.executable`; cold spawn and Blender/FreeCAD read-back under `-m dcc` with `@pytest.mark.timeout(300)` |
| `docs/partkiln-lane.md`, `docs/setup-partkiln.md`, `docs/research/68-mechanical-cad-lane.md` | house forms of `docs/seamkiln-lane.md`, `docs/setup-freecad.md`, doc 67 |

**MODIFY**

| file:line | change |
| --- | --- |
| `server/src/tee/app.py:211` (after) | `from tee.adapters.partkiln.tools import register_partkiln_tools; register_partkiln_tools(self)` with the metadata-only comment |
| `server/src/tee/cli.py:57` (after `_build_seamkiln_app`) | `_build_partkiln_app(project, allow_code_exec)`: build the adapter, submit the warm job |
| `server/src/tee/cli.py:247` (after godot) / `:250-251` / `:333` | `elif args.adapter == "partkiln":` / error string / `--adapter` help |
| `server/src/tee/config.py:60-77` + `load()` | `partkiln: dict[str, Any] = field(default_factory=dict)` + `data.get("partkiln", {})` (mirrors `scheduler` :161-164) for `python` and `batch_timeout_s` — `ProjectConfig` drops unknown tables silently |
| `server/src/tee/kernel/trust.py:193-363` | 14 `_EXPLICIT` rows under `# A66: partkiln. Three write files, two mutate the document; tabled individually (the cad_/trade_ rule).` — **no `_FAMILY` row** |
| `server/src/tee/doctor.py:254-299` (pattern) + `:562-578` | `check_partkiln()`: kernel importable? sidecar python + version (and the server's own `sys.version`)? mode; OCCT version; last `warm.json`; add to `run_checks` |
| `benchmarks/run_benchmarks.py:~1231` / `:1800` / `:1802-1804, 1869-1872` / `:~2121, ~2196` | `run_partkiln_scenario()` + the follow-up edit scenario; `_safe(...)`; `write_results` kw; `_partkiln_section` |
| `benchmarks/RESULTS.md` | `## Mechanical CAD: sketch → features → drawing → STEP (A66)` |
| `.github/workflows/ci.yml` | add job `kiln` (`working-directory: partkiln`, `uv sync --extra brep --extra dev`, ruff, `pytest -q -m "not slow"`); server job `uv sync --all-extras --no-extra cad` (uv 0.12.5 supports it) + cache — recorded in DECISIONS |
| `server/Makefile:8` / `packaging/mcpb_manifest.json:5` / `server/pyproject.toml:4` | 0.20.0, together |
| `CHANGELOG.md`, `docs/PROGRESS.md`, `docs/DECISIONS.md`, `docs/research/00-index.md`, `CLAUDE.md` | per the E3 formats (0.19.0 retroactive + 0.20.0) |

**NOT touched:** `packaging/mcpb_manifest.json tools[]`, `server/src/tee/server.py:30 _DESC`,
`server/Makefile mcpb:`, `server/src/tee/pdf.py` (PDF stays inside `partkiln[pdf]`),
`server/src/tee/kernel/extras.py` (the lane is not a `tee-engine` extra — note in DECISIONS),
`server/src/tee/physical/sketch.py` (stays on py-slvs under `[physical]` for TEE's own lanes), `seamkiln/`.

## Verification

**Test layout.** Tier 0 kernel (`partkiln/tests/`, no TEE, < 90 s): `test_licences.py`,
`test_units.py`, `test_params.py`, `test_document.py`, `test_sketch.py`, `test_features.py` (one
function per EXPECTED number), `test_naming.py`, `test_assembly.py`, `test_drawing.py`,
`test_export.py`, `test_checks.py`, `test_fixtures.py` (F1–F8 from `fixtures/*.json` against ONE
`EXPECTED` table), `test_worker.py`, `test_examples.py` (`--probe`), `test_import_hygiene.py`;
OCP-backed modules `pytest.importorskip("OCP", reason="partkiln[brep] not installed")`. Tier 1
`test_determinism.py`: F2/F5/F6 in two subprocesses → identical fingerprints; mesh SHA-256 serial
vs parallel; STL/GLB bytes identical on repeat. Tiers 3–5 in `server/tests/` (touch list). Tier 6
live `-m dcc`. Commands: `cd partkiln && PYTHONPATH=src uv run --project ../server python -m pytest -q
tests/`; `uv run --project server python -m pytest server/tests -q`; `make lint` from `server/`
(also `ruff check partkiln/`).

**Fixtures** (own-built, licence-clean, each a command script so it is also a replay test):

| Id | Part (mm) | Pinned numbers |
| --- | --- | --- |
| F1 plate | 100×60×10, Ø10 at (50,30); variants fillet r2 ×4 vertical, chamfer 2×45°, counterbore Ø11×6, countersink 90° Ø12, edit Ø10→Ø12 | V 59 214.602; faces 7; edges 15; area 15 357.080; COM (50,30,5); fillet −34.336 → 11 faces; chamfer −80.000; cbore −98.96; csink −16.76; edit −345.575 → 58 869.027; section x=50 = 500; HLR per compound as measured; GLB `[0.1, 0.01, 0.06]` + two negatives |
| F2 bracket | base 80×60×6, upright 80×34×6 on y∈[0,6], inner fillet r6, 4× Ø6.6 at (20,30)(60,30)(20,50)(60,50) | V 44 916.967; faces 13 (unified); edges 33; t=8 → 58 403.27; t=4 → 30 790.66; mirror 89 833.933 / 17; STEP round trip identical |
| F3 shaft | revolve Ø20×50 / Ø30×30 / Ø20×40; cosmetic M20×2.5×30; keyway 6×3.5×30 | V 49 480.084; faces 7; thread → fingerprint identical; section 2 700; keyway −611.9 |
| F4 housing | 60×40×30 shell 2 (top removed); draft box 40×40×20 at 3° | 15 552 / 11 faces; 30 352.2 |
| F5 pattern plate | 220×220×12, 10×10 Ø8 pitch 20 from (20,20); disc Ø80×5, 6×Ø5 PCD 60 | 520 481.421; 106 faces; 312 edges; n-ary ≈ 0.09 s; disc 24 543.693 / 9; hole table 100 |
| F6 pin-block | block 40×40×20 Ø10 through; pin Ø10×40; Ø11/Ø9.9; 4-pin pattern; two cubes at x=0/19 | 30 429.204; 3 141.593; DOF 0/1/1/2/3/3; pin at (20,20,20); 329.867; 0.050; 400.000 @ (19.5,10,10); 238.869 g / 24.662 g |
| F7 sheet | T2 R2 K0.44 90°, legs 50/30, W40 | BA 4.524; flat 76.524; bend zone 377.0 |
| F8 import | 10× F5 in a 2×5 grid, AP242 with names | 1 060 faces; 10 products; Σ 5 204 814.21 |

Secondary fixtures (BenchCAD, CADGenBench edit cases for the edit-impact invariant) only after P0a
row 18 records their dataset-card licences in `fixtures/third_party/ATTRIBUTION.md`. `materials.json`
cards are `{value, unit, source, honesty}`: ρ 7850 kg/m³ and E 210 000 N/mm² for structural steel
from EN 1993-1-1 §3.2.6, ReH 275 (t ≤ 16) from EN 10025-2, DC01 from EN 10130, 100Cr6 ρ 7.81 with
honesty `datasheet`; the loader refuses a card without `source`.

**The recorded acceptance session** (P6; `partkiln/examples/acceptance/run_tee.py` =
`test_partkiln_live.py -m dcc`), public surface only: (1) `run_batch("partkiln", F2 ops)` → one
diff, `details["part:bracket"].volume_mm3 == 44916.967`, `faces == 13`; (2) `set param t=8mm` →
`changed` lists plate/upright/holes, `fillet1 unchanged`, 58 403.27; `tee_diff` names the part;
(3) `tee_checkpoint` → `tee_rollback` → 44 916.967; the checkpoint replays in a subprocess to the same
fingerprint; (4) `pk_drawing` A3 SVG/DXF/PDF → DXF `get_measurement()` 80.0 / 60.0 / 6.6; PDF
mediabox A3; text contains `Ø6.6` and `ISO 273`; (5) `pk_export` STEP/GLB/STL/3MF → manifest units
per format; (6) cross-kernel: `cad_measure(bracket.step)` → 44 916.967 ± 1e-6 (OCCT 7.9.3) and, if
the FreeCAD bridge is up, the A37 adapter (OCCT 7.8.1) ± 1e-6; (7) Blender `as_ingest` → `as_import`
→ `verify.ok`, read-back XYZ [0.08, 0.06, 0.04] unsorted, one 640-px `tee_capture` as advice, last;
(8) Unreal if up: cm [8, 6, 4]; (9) F6 through the same door → `pk_measure(what=asm)` DOF 2,
interference 0 + contact, `pk_bom` 2 rows; Ø11 → 329.867; (10) tokens and wall clock summed into
`benchmarks/RESULTS.md`. A number that needed hand-editing is a defect, never a widened tolerance.

**Benchmark design.** TEE arm = the W1 batch + diff + one `pk_check` (≈ 1 280 tok, 2 calls —
measured in P4). Naive arms, both named: (a) face/edge inventory + 3 screenshots + SVG ≈ 13 650 tok /
6 calls; (b) STEP text ≈ 26 800 tok. Follow-up row: `param_set T=12mm` → naive re-reads everything
(~13k) vs the ~90-tok `changed` list. Sections end "Surface unchanged: 17 tools."

## Worked example W1 — mounting bracket → STEP + drawing (12 ops, the benchmark batch)

```json
[{"op":"param_set","props":{"W":"120mm","H":"80mm","T":"10mm","PX":"100mm","PY":"50mm"}},
 {"op":"create","kind":"part","name":"bracket","props":{"material":"steel_s275"}},
 {"op":"create","kind":"sketch","name":"base","props":{"plane":"XY","profile":[{"rect":["W","H"],"tag":"outer"}]}},
 {"op":"create","kind":"extrude","name":"plate","props":{"sketch":"base","distance":"T"}},
 {"op":"create","kind":"fillet","name":"f1","props":{"edges":"plate:edges(dir=Z)","r":"5mm"}},
 {"op":"create","kind":"hole","name":"h","props":{"on":"plate.end","at":[["-PX/2","-PY/2"],["PX/2","-PY/2"],["-PX/2","PY/2"],["PX/2","PY/2"]],"std":"M6 clearance normal"}},
 {"op":"create","kind":"sketch","name":"slot_sk","props":{"plane":"on:plate.end","profile":[{"slot":[40,8],"tag":"slot"}]}},
 {"op":"create","kind":"extrude","name":"slot","props":{"sketch":"slot_sk","distance":"through","mode":"cut"}},
 {"op":"create","kind":"chamfer","name":"c1","props":{"edges":"plate:edges(of=end, loop=outer)","d":"1mm"}},
 {"op":"create","kind":"drawing","name":"sheet1","props":{"of":"bracket","sheet":"A4L","views":[{"name":"top","dir":"top"},{"name":"front","dir":"front"}],
   "dims":[{"name":"d1","view":"top","kind":"extent","axis":"X"},{"name":"d2","view":"top","kind":"extent","axis":"Y"},{"name":"d3","view":"top","kind":"dia","of":"h.1","count":4},
           {"name":"d4","view":"top","kind":"dist","a":"h.1","b":"h.2","axis":"X"},{"name":"d5","view":"top","kind":"dist","a":"h.1","b":"h.3","axis":"Y"},{"name":"d6","view":"front","kind":"extent","axis":"Y"}],"title":{"part":"BRACKET-001","rev":"A"}}},
 {"op":"export","props":{"format":"step","out":"out/bracket.step"}},
 {"op":"export","props":{"format":"pdf","of":"sheet1","out":"out/bracket.pdf"}}]
```

Expected diff highlights: `feat:plate {volume_mm3:96000, faces:6}`; `feat:f1 {delta_mm3:-214.6,
faces:10, resolved:{"plate:edges(dir=Z)":4}}`; `feat:h {delta_mm3:-1368.48, faces:14, assumed:
{depth:"through", dia:"6.6mm from ISO 273 normal (bd_warehouse, Apache-2.0)"}}`; `feat:slot
{delta_mm3:-3062.65}`; `feat:c1 {delta_mm3:-195.7, faces:26, resolved:{…:8}}`; `part:bracket
{volume_mm3:91158.6, bbox_mm:[120,80,10], valid:true, mass_g:715.6}`; `dwg:sheet1 {dimensions:
{d1:120.0, d2:80.0, d3:"4× Ø6.6", d4:100.0, d5:50.0, d6:10.0}, projected_agree:true, assumed:{standard:
"ISO", angle:"first"}}`; `export:bracket.step {schema:"AP242", roundtrip:{volume_ok:true}}`. Follow-up
`[{"op":"param_set","props":{"T":"12mm"}}]` → `details.doc = {changed:[plate,f1,h,slot,c1,sheet1],
unchanged:0, failed:[], volume_mm3:109429.4}` (~90 tok).

W2 (shaft in a housing on a bearing ring, 18 ops: parts housing/shaft/brg6204, hole `seat` Ø47×14
and `bore` Ø25 through, components, `insert` mate + `rigid` + `revolute` joints, `check`) expects
`asm {components:3, dof:1, interference:[], clearance_mm:{"shaft-housing.bore":2.5}}`, BOM housing
1 254.9 g / shaft 246.6 g / ring 155.4 g at 7.81 (honesty `stand-in`). W3 (sheet L-bracket, 2 ops:
`create sheet` T2 W50 flanges 60 + 40@90° r2, two M5 clearance holes; `export dxf of brk.flat`)
expects `ba_mm 4.524, bd_mm 3.476, flat_mm [96.524, 50]`, folded − flat = +18.8 mm³ with the note.

## Risk register (each judged/refuted defect is closed by a row)

| Risk | Mitigation / test |
| --- | --- |
| Cold first import blocks a call | P0 row 1; warm job at boot; `pk_warming`; sidecar resident; `snapshot()`/`list_entities()` from the mirror while warming |
| novtk clobbers `server/.venv`'s OCP | dev hint installs `-e partkiln` WITHOUT `[brep]`; `[brep]` only in the sidecar venv; P0 row 3 |
| Sidecar dies / OCCT segfault; no Python-side cancellation | history mirrored; respawn + replay; `_dead()` names exit + log; wire deadline 60 s; `MAX_BATCH_S` prediction; `job: true` always via `SidecarKernel` |
| Topological naming after edits | hand-built histories + fingerprint fallback + fail-loud with candidates; seam edges excluded; `changed/unchanged/failed` on every edit; face-reorder test |
| STEP written as AP214 despite the setting | `Init_s()` → set schema BEFORE the first `Transfer`; `ChangeWriter().Model(True)` on reuse; `FILE_SCHEMA` asserted + the ordering negative |
| glTF wrong scale or wrong up axis | `SetLengthUnit_s(0.001)` + `SetInputCoordinateSystem(Zup)`; two negative fixtures; STL/OBJ manifests say "declares nothing" |
| HLR draws nothing on filleted parts / counts guessed | union of the three visible compounds; the 96-fillet plate fixture; per-compound counts under named projectors, never guessed |
| Glue-mode boolean returns the uncut shape with `IsDone()` | no glue on cuts; glue only for pattern fuses of touching copies; Law 11 on every boolean |
| Explorer counts double shared edges | `TopExp.MapShapes_s` everywhere; F1 15 / F2 33 / F5 312 pinned |
| Wrong acceptance arithmetic | every number re-derived (this plan's table); ONE `EXPECTED` table; BA parametrised at K 0.4/0.44/0.5 |
| Licence drift (Apache metadata over LGPL payload, unlicensed bd_materials, mislabelled nlopt, GPL py-slvs by habit, inconsistent metadata) | SPDX allowlist with the three-source `_spdx_of` + `KNOWN_PAYLOADS` (both OCP wheels) + no-metadata=fail + intruders + pass/fail fakes; own scipy solvers; py-slvs dev-only oracle |
| Autodesk marks in shipped names | enumerated `MARKS` whole-token test over identifiers and shipped strings, not docs |
| ISO 286 fits with no permissive source | `fit` out of v1 |
| Untabled `pk_*` crashes startup / a writer inherits the read tier | 14 explicit rows, no family; `pk_script`/`pk_import` write-scene; `pk_materials` pure lookup |
| `sympy`/`eval` on model-supplied expressions | AST-whitelisted evaluator; `__import__` refusal test |
| Server tests killed at 60 s | cold-spawn tests `@pytest.mark.timeout(300)` under `-m dcc`; default suite warm only |
| `[partkiln]` config silently dropped | `ProjectConfig.partkiln` field + `load()` block (touch list) |
| Wrong Python builds the sidecar; the extension runtime is 3.13.9 | every documented line pins `--python 3.11`; `check_partkiln` prints both interpreters |
| `.mcpb` upgrade wipes an editable install | sidecar venv survives; doctor says which mode is live; `_need()` names both routes |
| CI cost (1.3 GB `[cad]` per push already) | `kiln` job on `[brep]` (≈ 250 MB, P0 row 2); server job `--no-extra cad`; cache |
| Cross-platform fingerprints (Linux CI vs arm64) | rounded fingerprints; golden volumes at 1e-6 relative; byte identity within one platform only |
| Third-party fixture provenance unverified | P0 row 18 gates any third-party file; F1–F8 carry the suite until then |
| Scope creep toward the whole ribbon | closed `_VERBS`; doc 68 parity matrix marks each row v1/L1/L2/out with its number |

## Out of scope (say no in writing)

FEA/stress/modal, CAM/toolpaths, tube & pipe, cable & harness, frame generator, design accelerators,
mould/plastic features, T-spline/freeform, direct edit, model states beyond suppression,
simplify/shrinkwrap, presentations, 3D PDF/DWF/DWG, USDz (A53 Gap 1), proprietary imports
(Parasolid/SAT/JT/CATIA/NX/SW/Creo/Rhino/IFC), `.ipt/.iam/.idw/.ipn/.ide` in any direction, Autodesk
marks in names, ISO 286 fits (L2), coil/helix and modelled threads (L1), cloud collaboration, a
renderer of our own (Blender renders), the GUI (later, a client of the core), and matching
Inventor's speed before P0's numbers exist.

## Deliverables that make this a campaign (per the E3 checklist)

`CLAUDE_A66_SCRIPT.md` (this plan in the A53 skeleton) + the `CLAUDE.md` bullet; research doc 68 +
index row; DECISIONS A66 entry; PROGRESS entries per phase with pasted output and the closing
`**Suites at close:** partkiln N passed / M skipped; server N passed / M skipped; lint clean.
Surface unchanged: 17 tools / 2,033 tok.`; CHANGELOG 0.19.0 + 0.20.0; `docs/partkiln-lane.md` +
`docs/setup-partkiln.md`; `benchmarks/RESULTS.md` section; version bump ×3 + bundle + clean-unzip
verify. Discovery reports and probe scripts from this session live in the scratchpad
(`…/scratchpad/reports/*.md`, `…/scratchpad/design/*.md`, `…/scratchpad/probe/`) and should be
copied into doc 68's evidence before the scratchpad expires.
