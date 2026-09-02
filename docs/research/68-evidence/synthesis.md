# CLAUDE_A66_SCRIPT.md — `<kiln>`: a headless, AI-native mechanical CAD kernel + TEE lane

**Owner directive (2026-09-02, verbatim):** *"create an autodesk inventor alternative that runs headless with TEE and is optimized for ai engines"* — and mid-turn: *"use TEE"*, *"TEE/QMAX"* (TEE's own tools are the co-pilot; the qmax chore profile is pinned).

Written for a fresh session with no memory of the one that researched it. **`docs/research/68-mechanical-cad-lane.md` (to be written in P6 from the seven discovery reports) is the design of record**; every licence, platform and OCCT claim below was verified on 2026-09-02 and re-verified against the tree while this plan was synthesised. Build ON these facts; do not re-litigate them. Placeholders: package **`<kiln>`** (a *kiln word, owner picks — see Decisions), tool prefix **`<px>_`** (2–3 letters, not `cad_`/`sk_`/`fc_`; verified absent from `_FAMILY` and `_EXPLICIT`). Campaign **A66**; server **0.19.0 → 0.20.0**.

## Orientation for a cold session

- Repo `/Users/john/TokenEfficiencyEngine`, TEE code in `server/`. Branch `claude/token-efficiency-engine-5jv1dj` ONLY. Read `docs/PROGRESS.md` first; real command output into it per phase; commit + push per item.
- **The tree is not clean.** `git status` shows staged, uncommitted A65 follow-up work in `seamkiln/` (drape/dressing/solve, figure.py, examples incl. new `seamkiln/examples/_blender_body.py`, three tests) plus `docs/PROGRESS.md` and `docs/seamkiln-lane.md`. Commit that under its own subject before P0a. **A66 never touches `seamkiln/`.**
- Suites: `uv run --project server python -m pytest server/tests -q` → **1,224 passed / 17 skipped / 97 dcc-deselected**; `cd seamkiln && PYTHONPATH=src uv run --project ../server python -m pytest -q tests/` → 260 / 8 (~7 min, background); `make lint` from `server/` (lints `src tests ../benchmarks`) exit 0.
- Surface invariant: **17 always-loaded tools = 2,033 tok** (`surface:` line of `uv run --project server python benchmarks/run_benchmarks.py`; `test_server_lint.py:82 EXPECTED_TOOL_COUNT = 17`; `test_gateway.py:168`). **A66 adds ZERO always-loaded tools.**
- Interpreters: `server/.venv/bin/python` = 3.11.15; `~/TEE/.tee/sidecars/cad/bin/python` = 3.11.15; default `python3` = **3.14.7 — never build anything with it** (cadquery-ocp caps `<3.15`, py-slvs has no cp314).
- Where OCCT lives today (verified): `server/.venv` has `cadquery-ocp 7.9.3.1.1` (the VTK wheel; `import OCP` 0.29 s warm, `vtkmodules` NOT loaded); the sidecar `cad` venv has the same; the **Claude Desktop extension venv has NO `OCP`** (`find_spec("OCP") is None`). `cadquery-ocp-novtk`, `build123d`, `lib3mf` are absent everywhere.
- Upgrade trap: every `.mcpb` install wipes the extension venv's extras AND any editable install; the sidecar venv under `~/TEE/.tee/sidecars/` survives both the wipe and `tee_purge` (`purge.py:78-88` classifies `sidecars` as a capability).
- New code lives in **`<kiln>/`** at repo root (own `pyproject.toml`, tests, examples — the `seamkiln/`/`voxkiln/` precedent); the adapter in `server/src/tee/adapters/<kiln>/`.
- Co-pilot: `tee_web_lookup` (qmax) re-checks any licence/API fact before it lands in a file; `cad_measure` (fleet, OCCT in-process or sidecar) is the cross-kernel read-back; `tee_batch` on the new adapter is the "use it, don't just test it" evidence. `knowledge-base/` grounds nothing (its `15_*` Fusion prose is the failure mode CLAUDE.md names).
- **Why FreeCAD is not the kernel** (doc 52's question, `docs/research/52-fabrication-cad-lane.md:10-17`, answered): `freecadcmd` 1.1.3 boots in 0.38 s / 67 MB but the headless sketch+TechDraw probe ended "Application unexpectedly terminated"; TechDraw SVG/PDF is GUI-bound (#5710); it embeds OCCT **7.8.1** not 7.9.3; Sketcher constraints are integer-indexed (the documented LLM failure mode). OCP direct does every core op in ms with exact mass properties. FreeCAD stays the A37 adapter (`fc_*`).
- Provenance of this plan: three drafts (kernel / surface / parity) were judged; the kernel plan is the spine (process model, checkpoints, phases), the surface plan's wire vocabulary, assume/needs protocol, pre-flight and refusal table are grafted into §D5–D8 and P4, the parity plan's matrix, fixtures F1–F8, Tier-2 licence gate, P0 rows and acceptance session are grafted into P0/P2/P3/P5 and Verification. Every judged defect is fixed here (listed in the risk register).
- Phases are independently shippable. Stopping at a phase boundary must leave the tree green and the feature honest about what it does not do.

## Measured facts (2026-09-02, this machine — build ON them)

1. Apple M5 Max, 18 cores, 128 GB, macOS 26.6.2; `server/.venv` Python 3.11.15.
2. OCP direct (no cadquery): box − Ø10 cut + exact `BRepGProp` volume **17 ms** (59,214.602 mm³ = arithmetic); fillet 8 edges **13 ms**; `HLRBRep_Algo` front view **6 ms → 8 visible / 9 hidden edges** on F1; STEP AP242 write 13 ms / read 6 ms, volume round-trips exactly; `BRepMesh` + STL 4 ms, watertight; GLB 7 ms.
3. 100 sequential Ø8 cuts on a 220×220×12 plate: **0.46 s**, 106 faces / 624 edges, 520,481.421 mm³; B-rep fingerprint (sorted rounded per-face area+centroid) **identical in two fresh processes**; `BRepTools.Write_s` VERSION_3 no-tri checkpoint **81 KB, 1.4–3 ms write, 1 ms read**, volume identical.
4. glTF: `XCAFDoc_DocumentTool.SetLengthUnit_s(doc, 0.001)` + `RWGltf_CafWriter.SetMergeFaces(True)` → the plate reads back as **[0.22, 0.22, 0.012] m, one geometry**; without `LengthUnit` a 10 mm part is 10 m (cadquery's bug).
5. STEP on this runtime (verified now): `Interface_Static.CVal_s("write.step.schema")` is `''` until `STEPControl_Controller.Init_s()`, then `AP214IS`; `SetCVal_s(..., "AP242DIS")` → True, and `STEPControl_Writer.Model(True)` must follow or the file stays AP214.
6. `OSD_Timer` and `Message_ProgressRange` ARE bound; `OCP.RWObj`/`RWPly` are NOT (OBJ via trimesh). `BRepFeat_MakeCylindricalHole` has no counterbore/countersink (primitives + boolean, as build123d). `BRepTools_History` tracks vertex/edge/face/solid only.
7. HLR on filleted parts: `VCompound` can be **EMPTY**; visible lines live in `Rg1LineVCompound`/`OutLineVCompound`. Sections = half-space prism cut then HLR (TechDraw's method).
8. Tessellation SHA-256 identical serial vs `InParallel=True` at 0.05/0.3 mm (undocumented; measured once — pinned by test, never assumed).
9. The "140 s first import" in PROGRESS is **unmeasured cold native page-in** (code-signature validation of ~1 GB ad-hoc-signed Mach-O ≈ 10 s), not bytecode (compiling the whole closure: 0.51 s). P0 measures it.
10. `cadquery-ocp` and `cadquery-ocp-novtk` BOTH ship the top-level `OCP/` package → **co-installing novtk into `server/.venv` clobbers the VTK wheel** (judge-verified, 403 RECORD entries; P0a re-verifies).
11. Licences (W1): OCCT LGPL-2.1-only + OCCT exception 1.0 ("prominent notice"); cadquery-ocp/-novtk/-proxy Apache-2.0; cadquery Apache-2.0 but eagerly imports casadi (LGPL-3.0+) + nine VTK dylibs; build123d Apache-2.0 (pin `<0.12`: bd_materials is unlicensed); **py-slvs GPL-3.0, no exception**; fpdf2 LGPL-3.0-only; ezdxf/trimesh MIT; numpy/scipy BSD; lib3mf BSD-2; nlopt wheel effectively LGPL-2.1+; bd_warehouse CSVs Apache-2.0 and threadlib BSD-3 are the clean standards data; FreeCAD Fasteners GPL-2, BOLTS GPL-3, Wikipedia CC-BY-SA never vendored.
12. Inventor parity target (W2): sketch (12 constraints, normal/driven dims, parameters) → features (extrude/revolve/sweep/loft/coil; fillet/chamfer/hole with seats/thread cosmetic/draft/shell/split/combine; patterns; work features; table-driven families) → assembly (mate/flush/angle/tangent/insert; joints rigid/rotational/slider/cylindrical/planar/ball; DOF; interference; BOM) → drawings (base/projected/section/detail/aux; general/baseline/ordinate; hole tables; parts list; ISO/ANSI/DIN first/third) → sheet metal → export (STEP/IGES/STL/OBJ/glTF/DXF/PDF; no 3MF). Inventor: Windows-only COM, headless = read-only Apprentice or $3/12 min cloud, no macOS, no MCP; $2,585/yr.
13. TEE seams (verified today): `app.py:204-211` metadata-only registration; `cli.py:47-57` `_build_seamkiln_app`, `:244-247` elif chain, `:250-251` error string, `:333` help; `trust.py:164-192` `_FAMILY`, `:179-188` the cad_/trade_ rule, `:293-295` cad_ rows; `run_batch` calls `checkpoints.create` (→ `adapter.snapshot`) BEFORE `adapter.execute` (`app.py:301-304`); `checkpoints.py:105-113` `discard_snapshot` hook; `fleet/cad.py:206` `SIDECAR_PY`; `gateway/wire.py` NDJSON `Popen(bufsize=0)`, `select()` 1 s ticks, `_dead()` naming exit code; `kernel/script.py:29 MAX_SECONDS=120`; MCP calls have no server-side timeout; CI = one `server` job with `uv sync --all-extras`.
14. Closed-form fixture numbers recomputed with Python 3.11 (all pinned in §V3): F1 59,214.602 / 15,357.080 mm² / −34.336 / −80.000 / −345.575 → 58,869.027; F2 44,916.967 (t=8: 58,403.27; t=4: 30,790.66; mirror 89,833.933); F3 49,480.084 (keyway −611.9); F4 15,552 / 30,352.2; F5 520,481.421 / disc 24,543.693; F6 30,429.204 / 3,141.593 / 329.867 / 400.000 / 0.050 / 238.869 g / 24.662 g; F7 BA **4.524** at K=0.44 (4.398 at 0.4, 4.712 at 0.5), flat 76.524, bend zone 9.425·W; counterbore Ø11×6 on Ø10 = **98.96**; countersink 90° Ø12 on Ø10 = frustum 95.29, **extra 16.76**; sweep 3,715.7; loft 28,000; F8 5,204,814.21.

## Laws

1. **Measured before and after.** A phase without a number did not happen. P0's table freezes the process model; the winner is a number.
2. **The licence minefield is enforced by a test, not by memory** (P0b): SPDX allowlist over the closure, no-metadata = fail, OCCT the ONE named weak-copyleft exception.
3. **The GUI is a client of the headless core** (later phase; `import <kiln>` must work with no Qt and no OCCT).
4. **Zero new always-loaded TEE tools.** `tee_batch`/`tee_scene_summary`/`tee_diff`/checkpoints drive parts; the long tail is `<px>_*` virtual tools, **each tabled explicitly, no family row**.
5. **Diffs over snapshots, text over pixels.** Every mutation answers with mass properties (volume, Δvolume, bbox, faces/edges/solids); a mesh or a picture is opt-in.
6. **A refusal names its reason and the fix** — CADDesigner's (cause, location, correction) triple is house style; every refusal that rolled the batch back says so.
7. **Determinism is a feature.** Same script → same fingerprint, in two processes; checked on every restore.
8. **The model's eye is advice, not measurement.** No VLM decides whether a hole exists; `BRepGProp` does.
9. **Feature parity, not container parity.** Open interchange only; no `.ipt/.iam/.idw`; no Autodesk marks in shipped names (a test).
10. The metric is **tokens per completed part task**, measured in `benchmarks/`.
11. **A boolean that changes no topology is a failed boolean.** `delta_mm3 == 0` and counts unchanged → `<px>_no_effect` refusal unless `allow_no_effect: true`.
12. **A bare number is millimetres/degrees, and the diff says so once.** Unit-suffixed strings (`"0.5in"`, `"90deg"`) are accepted at the boundary; defaults are echoed in `assumed`; `doc.strict_units` makes bare numbers a refusal for callers who want KCL discipline. (Replaces the parity draft's bare-float refusal, which contradicted the facts pack and taxed every number.)
13. **A sub-shape is addressed by name, never by index.** History first, fingerprint second, otherwise refuse with the three nearest candidates. Explorer indices never leave the kernel.
14. **An edit reports its blast radius.** Every downstream feature is re-evaluated and listed `changed/unchanged/failed` with Δvolume — BenchCAD's 64 % silent corruption becomes a diff line.
15. **A drawing dimension is read back from the model, never typed** (the FreeCAD 0.0 lesson; DXF `DIMENSION.get_measurement()` is a test).
16. **The checkpoint is the script; the B-rep is a cache.** A restore that cannot verify its cache replays. A failed batch never advances state.
17. **Cold import never blocks a call** (A46). Warm-up is a job; a call during warm-up refuses with the job id.
18. **Cosmetic is cosmetic.** A thread note that moves volume or fingerprint is a bug.
19. **Ask only when the spec is inconsistent; otherwise default and declare.** One `needs:` list per batch, never a guess, never an interview.
20. **Use it, don't just test it** (A65 law 19): P6's recorded session runs through the public surface only, and a number that needed hand-editing is a defect, not a widened tolerance.

## Design of record

### D1. Package layout — `/Users/john/TokenEfficiencyEngine/<kiln>/`

```
<kiln>/  pyproject.toml  README.md  NOTICE  uv.lock
  src/<kiln>/
    __init__.py       __version__; imports nothing from OCP or tee
    units.py          "12mm"|"0.5in"|"3/8in"|12 -> mm; "90deg"|"1.5rad"|90 -> deg; unknown suffix refuses naming accepted ones
    params.py         named params + AST-whitelisted expression evaluator (+ - * / ^ () unit suffixes other params); no eval, no sympy
    document.py       Command(op,args) frozen; Document(parts, assemblies, drawings, params, history); apply()=the ONLY mutator;
                      script()/replay(script, overrides=)/fingerprint(); _VERBS closed dict; VERBS tuple; regen(from_index)
    sketch/model.py   Sketch(plane|on_face, entities tagged at creation, construction flag), Constraint(kind, refs by TAG), Dimension(driving|driven, expr)
    sketch/solver.py  scipy least_squares; DOF = n_params - rank(J) (raw; unanchored rect with H/V = 2, after fix p1 = 0);
                      status ok|under|over|conflict; conflicting[] (leave-one-out), redundant[] (row dependence); presets rect/circle/slot/polygon/poly
    sketch/profile.py closed-loop detection -> OCCT wires/faces (lazy OCP import)
    brep/             ALL OCP imports live here, lazily: shapes.py (prism/revol/pipe/thru_sections, BRepGProp, BRepBndLib.AddOptimal,
                      BRepCheck_Analyzer, ShapeUpgrade_UnifySameDomain), history.py (BRepTools_History merge per feature), mesh.py (absolute deflection, sha256)
    features/         base.py (Feature id/op/args/status/shape/history/names; downstream deltas), extrude revolve sweep loft coil(L1) hole fillet
                      chamfer shell draft pattern mirror boolean split workplane noeffect
    naming.py         "<feature>.<role>[.<seg>|[k]]"; fingerprint fallback; selector grammar; resolve(): name -> fingerprint -> refuse w/ 3 nearest
    assembly/         model.py (Component pose, grounded; Mate; Joint), solver.py (scipy; DOF = 6n_free - rank(J)), interference.py, clearance.py, bom.py
    drawing/          hlr.py (VCompound+Rg1LineV+OutLineV / HCompound+OutLineH), views.py (base/projected/section/detail/aux; first/third table),
                      dims.py (values READ from named sub-shapes; baseline/ordinate; hole table), svg.py (own writer, native arcs, Bezier via
                      GeomConvert_BSplineCurveToBezierCurve), dxf.py (ezdxf, real DIMENSION, $INSUNITS=4), pdf.py ([pdf] fpdf2: page A4..A0, title block)
    sheetmetal/       flat.py (Flat outline + Bend(line, angle, r, K)), fold.py derives the solid; BA = A(pi/180)(R + K*T), K default 0.44 (cited)
    exchange/         step.py iges.py brep.py stl.py obj.py(trimesh) threemf.py(trimesh; lib3mf optional) gltf.py (XCAF + LengthUnit 0.001 + MergeFaces)
    checks/           validity.py mass.py wall.py (IntCurvesFace ray cast) spec.py (agentcad check-spec -> {pass, violations:[{rule,got,limit,fix}]})
    data/             clearance_holes.csv tap_holes.csv drill_sizes.csv iso4762.csv iso4014_4017.csv iso4032.csv iso7089.csv iso261_pitch.csv
                      materials.json manifest.json (source, licence, retrieved per file; loader refuses without all three)
    handoff.py        seamkiln's Target table; SOURCE=(<kiln>, Z-up, right, 0.001 m); glTF identity; STL/OBJ manifest says "declares nothing"
    client.py         KernelClient Protocol + LocalKernel (in-process Document)
    worker.py         `python -m <kiln>.worker`: persistent NDJSON loop over one Document; imports nothing from tee; fd-swaps stdout around OCCT calls
  tests/  fixtures/F1..F8.json  examples/{bracket,shaft_housing,sheet_bracket}/  (python -m examples.<x> all --out DIR | --probe)
```

`pyproject.toml`: `license = MIT`, `requires-python >=3.11,<3.15`; core `numpy scipy ezdxf trimesh`; extras `brep = ["cadquery-ocp-novtk>=7.9.3,<8.0"]`, `pdf = ["fpdf2>=2.8.8"]` (LGPL, optional only — NOT `[sheet]`, which collides with sheet metal), `threemf = ["lib3mf>=2.4"]`, `dev = ["pytest","ruff"]`; the BANNED comment block (cadquery, py-slvs/python-solvespace, casadi, nlopt, pythonocc-core, bd_materials, gmsh, calculix, build123d in-process) with replacements. `[tool.pytest.ini_options] pythonpath=["src"]`, markers `slow`, `dcc`, `brep`. `NOTICE` carries the OCCT LGPL-2.1 + exception prominent notice, bd_warehouse Apache-2.0, threadlib BSD-3.

### D2. Process model — one Protocol, two kernels, a warm job

`KernelClient` (`<kiln>/client.py`; TEE imports it under `TYPE_CHECKING`, else `Any` — one copy): `probe() info() warm() apply(commands)->{results,diff} entities() detail(id) query(sel) measure(spec) check(spec) export(spec) script() fingerprint() snapshot(label,dir) restore(payload) discard(payload) shutdown()`.

- **`LocalKernel`** when `importlib.util.find_spec("OCP")` succeeds in the server interpreter (repo dev venv). `find_spec` only — no import at probe.
- **`SidecarKernel`** (`server/src/tee/adapters/<kiln>/wire.py`, copied from `gateway/wire.py`: `Popen(bufsize=0)`, newline-JSON, `_read_message(deadline)` with `select()` 1 s ticks, `_dead()` naming exit code + `<project>/.tee/<kiln>/worker.log`). Spawns `SIDECAR_PY = ~/TEE/.tee/sidecars/<kiln>/bin/python -m <kiln>.worker` (the `fleet/cad.py:206` discovery; `[<kiln>] python` in `.tee/config.toml` overrides). **Persistent** for the server's life; one `threading.Lock`, one request in flight (job threads queue). Request `{"id","method","params"}`; reply `{"id","result"|"error":{code,message,fix},"meta":{rss_mb,wall_ms}}` (meta never reaches the model); first line `{"event":"ready","occt":"7.9.3","kiln":..,"import_s":..,"rss_mb":..}`. Worker fd-swaps stdout (`_cad_worker.py:63-77`) so native chatter cannot corrupt the stream. **This is the production route**: the extension venv has no OCP and never will (extras are wiped).
- **Warm-up (law 17):** `_build_<kiln>_app` submits `app.jobs.submit("<kiln>_warm", kernel.warm, qos="interactive")` in BOTH modes. `probe()` = "process alive or OCP importable", never waits. `execute()` waits `READY_GRACE_S = 2.0` then refuses `<px>_warming` with `fix="poll tee_job <id>; warm import measured <P0 number>"`. **`snapshot()` during warming degrades to script-only** (no `.brep` spill, payload `brep: false`) because `run_batch` snapshots before it executes (`app.py:301-304`).
- **Deadlines:** `[<kiln>] batch_timeout_s = 60` (under `MAX_SECONDS=120`); `<px>_export`, `<px>_drawing`, `<px>_script replay`, interference over > 20 pairs accept `job: true` → `app.jobs.submit`. There is **no per-op guard inside a running OCCT boolean**; `Message_ProgressRange` is the bound cancellation hook for `BRepAlgoAPI_*` and is wired in only if P0 row 17 shows an op class above 10 s. `MAX_BATCH_S` is predicted from P0 row 17 per-op-class wall times; a batch predicted over it refuses `<px>_too_long` naming the job route.
- **Death is cheap:** the adapter mirrors the command history in-process; a dead worker is respawned and the script replayed (0.46 s / 100 cuts), noted in the diff. `rss_cap_mb = 4096` exceeded between batches → planned restart + replay, noted.
- `fleet/cad.py cad_measure` keeps its one-shot sidecar in v1; routing it through `<px>_measure` is P6 gap 2.

### D3. Checkpoints — the script is the state, the B-rep is a cache

`snapshot(label)` → `<project>/.tee/<kiln>/<label>-<epoch>-<ms>.json` = `{script, fingerprint, names:{name->fingerprint tuple}}` + one `.brep` per part via `BRepTools.Write_s(shape, path, False, False, TopTools_FormatVersion_VERSION_3)`; returns `{label, path, epoch, commands, fingerprint, brep}` (scalars only). `restore(payload)`: reload script → if every `.brep` exists, read shapes (1 ms), install names, recompute `fingerprint()`; **mismatch or missing file → full `Document.replay`** (the seamkiln law); missing json → `<px>_checkpoint_missing` naming `tee_purge`. `discard_snapshot(payload)` unlinks both (the `checkpoints.py:105-113` hook). Fingerprint = sha256 of sorted per-part (name, round(volume,6), sorted per-face (surface type, round(area,3), round(centroid,3))) + poses rounded 1e-6 + per-view (visible, hidden) counts; 16 hex.

### D4. Units and exchange

Kernel and wire in **mm / deg** (fabrication-lane convention; STEP `write.step.unit=MM`). Strings with suffixes accepted everywhere a length/angle is; `doc.units`/`doc.strict_units` settable via `set doc`. Export units: STEP/IGES declare mm; **glTF metres** via `SetLengthUnit_s(doc, 0.001)`; STL/OBJ declare nothing (manifest says so); DXF `$INSUNITS=4`; 3MF `unit="millimeter"`.

| Format | Mechanism | Verified trap |
|---|---|---|
| STEP AP242 (default) / AP214 / AP203 | `STEPControl_Controller.Init_s()` → `SetCVal_s("write.step.schema","AP242DIS")` → `STEPCAFControl_Writer` (name/colour/layer modes) → `Model(True)`; assert `FILE_SCHEMA` contains `AP242` | schema reads `''` before init; file stays AP214 without `Model(True)` |
| IGES | `IGESControl_Writer` (not thread-safe: under the one lock) | — |
| BREP | `BRepTools.Write_s` VERSION_3, no triangulation | — |
| STL | `BRepMesh_IncrementalMesh(defl, relative=False, 0.5, InParallel=True)` + `StlAPI_Writer` | build123d's `tolerance` is RELATIVE |
| OBJ / 3MF | trimesh (`export_3MF` exists in trimesh 5.0.0); lib3mf optional | `OCP.RWObj` unbound |
| GLB | XCAF doc + `SetLengthUnit_s(doc, 0.001)` + `RWGltf_CafWriter.SetMergeFaces(True)`; read back through `tee.assets.gltf.probe` | mm-as-metres without LengthUnit (negative fixture) |
| DXF / SVG / PDF | ezdxf real `DIMENSION`s; own SVG writer with native arcs; fpdf2 in `[pdf]` | HLR `VCompound` empty on fillets |
| Import STEP/IGES/BREP | `STEPCAFControl_Reader` → parts with names; sub-shapes fingerprint-named only | — |
| Out | DWG (libredwg GPL), USDz (A53 Gap 1), Parasolid/SAT/JT, `.ipt/.iam/.idw` | — |

### D5. Wire vocabulary for `tee_batch` (closed, enumerable; unknown op/kind → `<px>_bad_op` listing every verb)

Numbers: bare = doc unit; strings carry units; a param name or expression (`"W/2 - 5mm"`) is legal wherever a length is. Every op takes `name` (≤ 24 chars `[a-z0-9_]`; omitted → `<kind><n>`, echoed in `created`); multi-instance children are `h.1, h.2 …`. Required **bold**; defaults echoed in `details[id].assumed`.

| op / kind | props | assumed |
|---|---|---|
| `param_set` | **`{name: value…}`** (create-or-set; expressions) | — |
| `set doc` | `units in\|mm`, `standard ISO\|ANSI\|DIN`, `angle first\|third`, `strict_units` | first batch echoes doc defaults once |
| `create part` | `name`, `material` | material none (mass only when set) |
| `create sketch` | **`plane`** (`XY\|XZ\|YZ\|plane:<n>` or `on:"<face ref>"`), **`profile`**: `{rect:[w,h],at,tag}` `{circle:d,at,tag}` `{slot:[len,w],at,angle,tag}` `{polygon:n,d,at}` `{poly:[[x,y]…],closed,tags}` `{arc:{from,to,r\|center}}`; `constraints:[{c, on\|a\|b}]` (coincident collinear concentric fix parallel perpendicular horizontal vertical equal tangent symmetric smooth); `dims:[{d:len\|dist\|angle\|dia\|rad, on\|a\|b, value, driven}]` | `at [0,0]`, `angle 0` |
| `create extrude` | **`sketch`**, **`distance`** or `to:"<face>"`/`"through"`, `direction +\|-\|both`, `mode new\|join\|cut\|intersect`, `taper` | `+`; `new` if part empty else `join`; taper 0 |
| `create revolve` | **`sketch`**, **`axis`** (`X\|Y\|Z\|"<edge ref>"\|[[p],[d]]`), `angle`, `mode` | angle 360 |
| `create sweep` / `loft` | **`profile`**,**`path`**,`frenet` / **`sections`**,`ruled`; `mode` | frenet false; ruled false |
| `create hole` | **`on`** (face ref), **`at`** `[[x,y]…]` in the face frame or `at_edges`; one of **`dia`** / `std:"M6 clearance normal\|close\|loose"` / `std:"M6 tap"`; `depth through\|<len>`; `seat:{kind:counterbore\|countersink\|spotface, dia, depth\|angle}` or `seat:"M6 socket head"`; `thread:"M6"` (cosmetic) | depth through; std source echoed |
| `create fillet` / `chamfer` | **`edges`**, **`r`** or `r:[r1,r2]` / **`d`** or `d:[d1,d2]` or `{d,angle}` | — (design intent: refuses if missing) |
| `create shell` / `draft` | **`faces`**,**`t`**,`direction in\|out` / **`faces`**,**`angle`**,**`neutral`** | in; pull = neutral normal |
| `create pattern` / `mirror` | **`of`**, `kind rect` **`dx,nx`**,`dy,ny` / `circ` **`axis,n`**,`angle` / `sketch` **`points`**; `suppress:[i]` / **`of`**,**`plane`** | angle 360 |
| `create combine` / `split` | **`bodies`**,**`mode`**,`keep_tool` / **`body`**,**`plane\|face`**,`keep` | false; both |
| `create plane\|axis\|point` | `offset:{from,distance}` / `through:[refs]` / `angle:{about,deg}` / `normal_at:{face,at}` / `midplane:[a,b]` | — |
| `create component` | **`part`**, `at`, `rot`, `grounded`, `qty` | first component grounded; identity pose |
| `create mate` | **`kind mate\|flush\|angle\|tangent\|insert`**, **`a`**, **`b`**, `offset\|angle`, `flip` | — |
| `create joint` | **`kind rigid\|revolute\|slider\|cylindrical\|planar\|ball`**, **`a`**, **`b`** (`cmp.feature.role`), `offset`, `limits` (no `fit` in v1 — ISO 286 data has no permissive source) | offset 0 |
| `create drawing` / `view` / `dimension` | **`of`**, `sheet A4L..A0L\|ANSI_B`, `standard`, `angle`, `scale`, `views:[{name,dir front\|top\|right\|iso\|section:<plane>\|detail:{of,r}\|aux:<face>}]`, `dims:[{name,view,kind extent\|dist\|dia\|rad\|angle\|chamfer\|ordinate\|baseline,axis,of\|a,b}]`, `hole_table`, `parts_list`, `title:{…}` | ISO→first angle, ANSI→third (projection follows the standard); 1:1; auto layout |
| `create sheet` (P5b) | **`t`**, **`width`**, **`flanges:[{len,angle,r,dir}]`**, `k`, `holes`, `relief` | k 0.44 cited; r = t |
| `set` / `delete` | `id`,`props` (any creation prop, `suppressed`, `material`, `name`) / `id`, `cascade` | delete refuses naming dependents unless cascade |
| `export` | **`format step\|iges\|brep\|stl\|obj\|3mf\|glb\|dxf\|svg\|pdf`**, **`out`**, `of`, `schema`, `tol`, `target blender\|unreal\|godot`, `job` | AP242; 0.05 mm; the one body |
| `check` | `spec`, `strict` | strict → refuse on violation |

`create object` (the contract's generic kind) is accepted as a BOM virtual component so the packaged suite runs on the fake. Reads (measure/BOM/explain/standards) are `<px>_*` tools, not batch ops.

### D6. Names and selectors

Roles per kind, materialised from merged `BRepTools_History` (`Generated/Modified/IsDeleted`; after fuse/cut the kernel applies `ShapeUpgrade_UnifySameDomain(unifyEdges, unifyFaces)` and merges ITS history too — the face-count pins assume it): `extrude.start/.end/.side.<segtag>`; `revolve.outer/.inner/.cap.a/.b`; `hole.wall/.bottom/.seat`; `fillet.face[i]`; `sweep/loft.start/.end/.side[i]`; `shell.inner[i]`; imported bodies `import.face[k]` (fingerprint only). Fingerprint per sub-shape = (surface/curve type, area/length, centroid/midpoint, normal) rounded 1e-3 mm. **Selectors** are declarative strings evaluated at regen and materialised to names in the diff: `"<feature|part>:faces(<f>)"` / `":edges(<f>)"`, filters `normal=+Z`, `dir=Z`, `of=<role>`, `loop=outer|inner`, `type=plane|cyl|cone|sphere|torus|bspline`, `r=`, `len>`, `area>`, `convex|concave`, `nearest=[x,y,z]`, `created_by=`, `not()`. Cardinality is declared by the consuming field (`on` = 1, `edges` = many): 0 → `<px>_ref_empty`, >1 where 1 → `<px>_ref_ambiguous` with candidates; `details[id].resolved` echoes `{"plate:edges(dir=Z)": 4}` and the names when ≤ 6. Resolution after regen: history → fingerprint (Δ ≤ 1e-3) → `<px>_ref_stale` naming the history event ("deleted by hole h"), the nearest candidate with its Δ mm, and the selector form that would survive. Never a silent re-target.

### D7. Entity model and diff contents

Ids `<prefix>:<name>`; `kind` is the feature kind (so `kind=fillet` filters); concise rows ~20 tok, a 12-feature part ~300 tok. **Everything a batch can change is an entity** (the A65 lesson), and every created/modified entity reaches `Diff.upserts` or `SceneCache` goes blind.

| id | kind | parent | summary (tee_entity_detail adds; never geometry) |
|---|---|---|---|
| `doc` | doc | — | units, angle, standard, parts, components, features, drawings, exports, fingerprint, script_commands |
| `param:W` | param | — | value, unit, expr, used_by |
| `plane:XY` | datum | part | origin, normal, x |
| `sk:base` | sketch | part | plane, entities, constraints, dof, status, conflicts, area_mm2, used_by |
| `feat:plate` | extrude/fillet/hole/… | part | status, params (scalars), refs, volume_mm3, delta_mm3, faces, edges, roles, downstream, suppressed |
| `part:bracket` | body | — | volume_mm3, area_mm2, bbox_mm, com_mm, solids, faces, edges, valid, material, mass_g, fingerprint |
| `cmp:shaft` / `mate:m1` / `jt:spin` / `asm` | component / mate / joint / assembly | asm | part, grounded, pose / kind, a, b, dof_removed / components, dof, grounded, interference, residual |
| `dwg:sheet1` / `vw:sheet1.front` / `dim:sheet1.d1` | drawing / view / dimension | — / dwg / vw | sheet, standard, angle, scale, views, dims, files / dir, scale, visible_edges, hidden_edges / kind, refs, value_mm, projected_mm, agree |
| `sheet:brk` | sheet | — | t, k, bends, flat_mm, folded_bbox_mm, ba_total_mm |
| `export:<path>` | export | — | format, bytes, units, declares_units, roundtrip |

Per-op `details` (rounded: volumes 2 dp, lengths 3 dp; requested props trimmed by `_trim_batch_echoes`, so details are measured drift only): any feature `{status, volume_mm3, delta_mm3, bbox_mm, faces, edges, solids, assumed, resolved, names (≤ 8, rest counted)}`; cut/hole/combine `+ no_effect` (refuses, law 11); `set`/`param_set` `{changed:[{feature, delta_mm3, faces}], unchanged:n, failed:[{feature, code}], volume_mm3, fingerprint}`; sketch `{entities, constraints, dof, status, conflicts, redundant, closed, area_mm2, frame}`; component/mate/joint `{dof_removed, pose}` + one `details.asm` per batch `{components, dof, grounded, residual, interference:[{a,b,mm3,centroid}], clearance_mm, contacts}`; view `{visible_edges, hidden_edges, scale}`; dimension `{value_mm, projected_mm, agree}`; export `{path, bytes, format, units, roundtrip:{volume_ok, faces_ok}, watertight, triangles}`; check `{verdict, violations:[{rule, got, limit, fix}]}`. `notes`: one line per material fact (`"h: Ø6.6 = ISO 273 normal for M6 (bd_warehouse, Apache-2.0)"`). No `ms` on the wire.

### D8. Assume/needs and the refusal table

Defaults are declared once (`assumed`), doc defaults only on a session's first batch. A self-contradictory spec raises ONE `<px>_spec_conflict` whose `fix` is a numbered `needs:` list (≤ 3, each with options) collected across the whole batch; a required field with a safe default is assumed and said; one with no safe default (`fillet.r`) refuses `<px>_needs`. `run_batch` appends "Batch rolled back to checkpoint …".

| code | when → message shape |
|---|---|
| `<px>_bad_op` / `<px>_kernel_absent` / `<px>_not_served` / `<px>_warming` / `<px>_too_long` | vocabulary / install line / `tee serve --adapter <kiln>` / job id + measured import / job route |
| `<px>_plane_missing` / `<px>_plane_mismatch` | lists planar faces now / frame origin+normal and the face bbox the profile exceeds |
| `<px>_unit_unknown` / `<px>_unit_kind` / `<px>_unitless` | accepted suffixes / "90mm on an angle" / only under `strict_units` |
| `<px>_ref_unknown` / `_stale` / `_ambiguous` / `_empty` | nearest names / history cause + nearest Δ + surviving selector / candidates / "matched 0 of 76; drop len>200 (max 120)" |
| `<px>_no_effect` | "removed 0 mm³, faces 18→18; tool outside bbox [..]; check at/plane or allow_no_effect" |
| `<px>_sketch_overconstrained` / `_open` | conflicting dim names + "mark driven" / gap mm between named ends + the coincident to add |
| `<px>_spec_conflict` / `<px>_needs` / `<px>_part_ambiguous` / `<px>_delete_blocked` | needs list / "r is design intent" / "add part:" / dependents + cascade |
| `<px>_op_failed` | "fillet f1 r=12: NbFaultyContours=1 on plate.side.s1 (face height 10) → r ≤ 5, or fewer edges" |
| `<px>_checkpoint_missing` | names `tee_purge`; replay from `<px>_script` if a script was saved |

### D9. Virtual tools (14; every one in `_EXPLICIT`; **deliberately no `_FAMILY` row** — the `cad_`/`trade_` rule at `trust.py:179-188`, because five of these write files and two mutate the document)

| tool | capability | first line (≤ 150 chars; search pays it per hit) |
|---|---|---|
| `<px>_probe` | read-compute | Kernel health: OCCT/OCP version, mode (in-process\|sidecar\|absent), warm state, formats, licence notices. |
| `<px>_verbs` | read-scene | The batch vocabulary for parts, assemblies, drawings, sheet metal — one example op per kind. |
| `<px>_lint` | read-compute | Pre-flight a batch without the kernel: schema, units, unresolvable refs, predicted sketch DOF, structured `needs`. |
| `<px>_query` | read-scene | Resolve a selector to names with sub-shape facts; the feature tree as text (`what=tree`); changes since a revision. |
| `<px>_measure` | read-compute | Numbers not pixels: mass with density, clearance, interference, min wall, section area, face inventory (`what=faces`), on the live document or a STEP/BREP/STL path. |
| `<px>_check` | read-compute | Verify a spec: bbox, hole dia/count, min wall, watertight, volume/mass bands, zero interference, DOF → verdict + violations with the fix. |
| `<px>_standards` | read-compute | Clearance/tap/drill for a bolt (ISO 273/262 via bd_warehouse), ISO 4762/4014/4017/4032/7089 — with source and licence. |
| `<px>_materials` | read-compute | Material cards (density, E, yield) with an honesty tier per value. Pure lookup — assignment is `set part material=` in a batch. |
| `<px>_bom` | read-scene | Bill of materials: structured or parts-only, qty, material, mass, standard designations. |
| `<px>_drawing` | write-artifacts | Write a dimensioned sheet to SVG/DXF/PDF: views, sections, dims read back from the model, hole table, parts list, title block. |
| `<px>_export` | write-artifacts | STEP AP242/214/203, IGES, BREP, STL, OBJ, 3MF, GLB, DXF with a handoff manifest (units, up axis) for Blender/Unreal/Godot; round-trip verified. |
| `<px>_flat` | write-artifacts | Sheet-metal flat pattern: BA/BD per bend (K or bend table), flat extents, bend lines; DXF layers OUTLINE/BEND_UP/BEND_DOWN/HOLES. |
| `<px>_import` | write-scene | Import STEP/IGES/BREP as a base body with fingerprint-named faces; reports units, solids, validity. |
| `<px>_script` | write-scene | The document as a replayable script: dump, replay (job when long), replay with param overrides (the part family), compare fingerprints. |

Tags singular AND plural (words ≤ 2 chars drop — `M6` never scores). Ranking pins (top-3): "extrude a sketch"→`_verbs`, "add a fillet"→`_verbs`, "mate two parts"→`_verbs`, "drawing with dimensions"→`_drawing`, "export STEP"→`_export`, "bill of materials"→`_bom`, "sheet metal flat pattern"→`_flat`, "clearance hole for M6 bolt"→`_standards`, "assembly interference check"→`_measure`, "hand off part to blender"→`_export`.

## P0 — measure, then gate (commit P0a/b/c separately)

**P0a — the measurement table** (all in the scratchpad, `uv venv --python 3.11`; every cell into PROGRESS). Reuse `probe/brep_probe.py`.

| # | What | Expected / decides |
|---|---|---|
| 1 | Cold `import OCP` on a FRESH novtk venv and a fresh vtk venv (a fresh venv is a cold code-signature measurement; `sudo purge` ×2 only if the owner is present), warm ×3 | novtk ≤ 10 s cold, 0.3–1.2 s warm; **not 140 s**; decides whether a warm-up job alone suffices |
| 2 | `du -sh` novtk site-packages; `otool -L OCP.cpython-311-darwin.so \| grep -c vtk` | ≈ 250–300 MB vs 1.4 GB; **0** VTK dylibs → CI cost of the `kiln` job |
| 3 | `unzip -l` both wheels `\| grep -c '^.*OCP/'` | both ship top-level `OCP/` → the co-install hazard recorded; `[brep]` must accept either wheel by `find_spec` |
| 4 | Binding coverage on novtk, 26 classes: `BRepTools_History TNaming_Builder HLRBRep_Algo HLRBRep_PolyAlgo RWGltf_CafWriter BRepFeat_MakeDPrism XCAFDoc_DocumentTool BRepFilletAPI_MakeFillet/_MakeChamfer BRepOffsetAPI_DraftAngle/_MakePipeShell/_ThruSections/_MakeThickSolid BRepAlgoAPI_Splitter STEPCAFControl_Writer/_Reader IntCurvesFace_ShapeIntersector BRepClass3d_SolidClassifier GeomConvert_BSplineCurveToBezierCurve ShapeUpgrade_UnifySameDomain OSD_Timer Message_ProgressRange BRepExtrema_DistShapeShape BRepBndLib IGESControl_Writer StlAPI_Writer` | all import (vtk-wheel result must transfer) |
| 5 | Prototype 60-line NDJSON worker: spawn→`ready`, first and 100th `measure` | first = row 1 + ~50 ms; steady ≤ 2 ms |
| 6 | RSS after import and after F5 | record (2 job workers × residency) |
| 7 | F5: 100 sequential cuts vs ONE n-ary `BRepAlgoAPI_Cut` (`SetGlue`, `SimplifyResult`) | sequential 0.46 s; n-ary expected < 0.2 s; same volume; **edge count recorded** (624 was sequential) |
| 8 | HLR on 530 faces (5×F5): exact vs PolyAlgo; per-compound counts on F1 and on all-filleted F1 | exact ≈ 0.1–0.2 s; F1 front **8 vis / 9 hid**; filleted `VCompound` empty, `Rg1LineV` non-empty |
| 9 | STEP: `CVal_s` before/after `Init_s`; AP242DIS + `Model(True)` write → `FILE_SCHEMA` contains AP242; read back names + volume | `'' → AP214IS → AP242DIS`; names round-trip |
| 10 | F8 import via `STEPCAFControl_Reader` | ≤ 1 s; 10 products; Σ 5,204,814.21 |
| 11 | BRepMesh SHA-256 serial vs 3× parallel at 0.05/0.3 | identical (pinned by test) |
| 12 | B-rep fingerprint of F2 (fillet) and F6 (assembly) in two fresh processes | identical |
| 13 | glTF 10 mm cube with/without `SetLengthUnit_s` through `tee.assets.gltf.probe` | `[0.01…]` vs `[10…]`; Y-up |
| 14 | BREP checkpoint vs replay for F5 | 81 KB / ≤ 5 ms / ≤ 2 ms vs 0.46 s |
| 15 | `BRepTools_History` on F1 fillet: `Modified(extrude1.end)`, `Generated(side edge)` | end face → 1 modified; each vertical edge → 1 fillet face |
| 16 | Own scipy sketch solver vs py-slvs (dev-only oracle from `server/.venv`'s `[physical]`, never a `<kiln>` dep) on 20 sketches, anchored | coordinates ≤ 1e-6 mm; DOF equal on all 20 after anchoring (py-slvs counts rotation, `physical/sketch.py:209`) — settles the convention in writing |
| 17 | Per-op-class wall times (extrude, hole ×1/×100, fillet ×8/×96, boolean, HLR, STEP write/read, GLB) | the basis of `MAX_BATCH_S` and the `job` threshold |

**P0b — the licence gate** `<kiln>/tests/test_licences.py`: seamkiln's `BANNED` dict (reason + replacement: py-slvs, python-solvespace, cadquery, casadi, nlopt, pythonocc-core, bd_materials, gmsh, calculix) + `NON_COMMERCIAL_MARKERS` PLUS: SPDX **allowlist** `{MIT, BSD-2/3-Clause, Apache-2.0, ISC, PSF-2.0, 0BSD, Zlib, CC0-1.0, MPL-2.0 (weak copyleft, file-scoped, in-process OK — A53's CDT precedent)}` over the transitive closure of core + `[brep]`; `KNOWN_PAYLOADS = {"cadquery-ocp-novtk": ("LGPL-2.1-only WITH OCCT-exception-1.0", url, "2026-09-02")}` — the ONE named exception, with `NOTICE` asserted present and naming OCCT; `VERIFIED_IN_REPO` for `anytree`/`ocpsvg` if ever declared; **no licence metadata = fail**; `[pdf]` (fpdf2) allowed only in its extra, never in the core closure; deliberate failures parametrised over py-slvs, cadquery, casadi, a licence-less fake, an `LGPL-3.0-only` fake in core; `test_import_hygiene` (`import <kiln>` never loads `tee cadquery casadi vtkmodules py_slvs fpdf OCP`); `test_data_files_carry_provenance` (every CSV: `source`, `licence`, `retrieved`; none cites Fasteners/BOLTS/Wikipedia); `BANNED_DATASETS` (Fusion 360 Gallery, Text2CAD, CAD-Recode, GenCAD-Code) scanned over `fixtures/`; `test_no_autodesk_marks_in_shipped_names` scoped to tool names, entity kinds, verbs, VirtualTool descriptions/tags, pyproject name/description — **not docs** (doc 68 must name the incumbent).

**P0c — the FreeCAD-not-kernel ruling**: paste the freecadcmd crash output, 0.38 s / 67 MB, OCCT 7.8.1, index constraints into PROGRESS + DECISIONS.

*Acceptance:* every cell of the 17-row table filled; warm `import OCP` ≤ 1.5 s; cold ≤ 30 s or the sidecar design re-justified in writing; novtk links 0 VTK dylibs; all 26 classes bound; spawn→ready ≤ warm + 0.5 s; GLB 10 mm cube reads 0.010 m; mesh hash identical ×3; fingerprints identical ×2 for F2 and F6; solver oracle agrees on 20/20; the gate fails on all 5 intruders and passes the tree.

## P1 — document, units, params, sketch (no OCCT)

`document.py`, `units.py`, `params.py`, `sketch/model.py`, `sketch/solver.py`, presets. *Acceptance:* unanchored 100×60 rectangle (4 lines, H/V/equal/2 dims) → `dof=2`; after `fix p1` → `dof=0`, solved to 1e-6 mm; minus one distance → `dof=1, status=under`; plus a conflicting 61 mm → `status=conflict`, `conflicting` names both dims; duplicated horizontal → `redundant` names it; 40-entity/60-constraint sketch < 50 ms; `"0.5in"` → 12.7; bare `12` → 12 mm with `assumed` once; `"12 mils"` refuses naming accepted suffixes; `"W/2 - 5mm"` evaluates, `__import__` in an expression refuses; `Document.replay(script).fingerprint()` equals the original on 20 random command sequences; `replay(script, overrides={"t": "8mm"})` yields a different fingerprint; `import <kiln>` with OCP absent succeeds; tests: no OCP, no network.

## P2 — the part kernel (features, naming, checks, exchange)

*Acceptance* (this Mac, warm; numbers from §V3 EXPECTED): F1 build ≤ 30 ms, volume 59,214.602 to 1e-6; F5 via n-ary cut ≤ P0 row 7 time, 520,481.421, faces 106; fillet 4 named edges (`plate:edges(dir=Z)`) → −34.336, faces 7→11; chamfer → −80.000; F2 44,916.967, faces 13; F3 revolve 49,480.084, faces 7; sweep 3,715.7 ± 0.5; loft 28,000; F4 shell 15,552 / draft 30,352.2; counterbore +98.96 removed; countersink +16.76 beyond the Ø10 hole; taper extrude via `BRepFeat_MakeDPrism`; workplane keyway −611.9 ± 0.1; mirror 89,833.933 faces 17; circular 24,543.693 faces 9; suppress 3 instances → count 97; cosmetic thread leaves the fingerprint bit-identical; **edit-impact**: Ø10→Ø12 → `changed:[hole1 −345.575]`, `fillet1 unchanged`, part 58,869.027; editing F2's `t` regenerates every downstream feature and no selector silently re-targets (face-reorder test: names resolve through fingerprint, else refuse with 3 candidates); a cut that removes nothing → `no_effect` refusal; fillet r=12 on F1's top-front edge (plate 10 thick) refuses naming the edge and the face height; draft on a torus face refuses naming the type; STEP AP242 round trip volume 1e-9 relative + names; IGES 1e-6; STL watertight, bytes identical on repeat; OBJ/3MF reload within 0.1 %; GLB extents_m [0.1, 0.06, 0.01] and the **negative fixture [100, 60, 10]**; BREP checkpoint ≤ 5 ms / restore ≤ 2 ms fingerprint equal, replay fallback when the file is deleted; `check_wall` finds a 1.2 mm wall under a 2 mm limit; spec check `{pass, violations[{rule,got,limit,fix}]}`; fingerprint identical in two fresh processes; 12 deliberate-failure tests each one `CommandError` naming feature + fix.

## P3 — assemblies

*Acceptance:* F6 block + pin: joint kinds in turn → DOF **0 / 1 / 1 / 2 / 3 / 3**; insert + mate solves the pin to (20, 20, 20) ± 1e-6, residual < 1e-9, ≤ 200 ms; remove one mate → `dof=1` named per component; rigid + contradictory 5 mm offset → `over_constrained:["mate2"]`, residual 5.000; Ø11 pin interference **329.867 mm³** + centroid; two 20 mm cubes at x=0/19 → 400.000 at (19.5, 10, 10); Ø10 pin in Ø10 hole → 0 with `contact: true` (`SetFuzzyValue` policy documented); Ø9.9 → clearance 0.050; 4-pin pattern → BOM parts-only `[{block,1},{pin,4}]`, steel 7.85: 238.869 g / 24.662 g, total 337.517 g; `create object` lands as a BOM virtual component; plate + 4× ISO 4762 M6 from `data/` solves ≤ 200 ms; replay fingerprint stable.

## P4 — the TEE adapter (`server/src/tee/adapters/<kiln>/`; pull forward after P2 if the co-pilot needs it)

Seven methods per `kernel/adapter.py`: `info()` (`extra={mode, state, occt, parts, assemblies, drawings, commands}`), `probe()` (never waits), `list_entities()` (§D7 — everything a batch can change), `execute()` (pure `_translate(op, index)` → one `apply(commands)` round trip; `_record` writes `created/modified/deleted/details/notes` AND `upserts`), `snapshot/restore/discard_snapshot` (§D3), `capture()` **refuses honestly in v1** (`<px>_capture_text_first` naming `<px>_drawing` SVG as the picture, `<px>_measure`, `tee_entity_detail`); P6 adds opt-in JPEG through Blender. `_need()` refuses only when BOTH routes are absent (`find_spec("<kiln>")` fails AND `SIDECAR_PY` missing); hint names both routes — **dev venv: `uv pip install --python server/.venv/bin/python -e <kiln>` (NO `[brep]`: OCP is already there and novtk would clobber it)**; production: `uv venv --python 3.11 ~/TEE/.tee/sidecars/<kiln> && uv pip install --python ~/TEE/.tee/sidecars/<kiln>/bin/python -e <repo>/<kiln>[brep]`. `tools.py` registers the 14 tools (module imports only `typing`/`TeeError`/`VirtualTool`; every handler starts `_need()` then `_adapter(app)`). `<px>_lint` and the assume/needs protocol land here (§D8).

*Acceptance:* `surface: 17 always-loaded tools = 2033 tok on the wire` (± 10) and `test_always_loaded_surface_delta_is_zero`; `tee_scene_summary` on the 12-feature bracket ≤ 400 tok; the §W1 batch returns ONE diff naming every created id with volume/faces, `assumed` present once, `resolved` counts present; a failed 3rd op rolls back and the fingerprint equals the pre-batch one; `no_effect` refuses the batch; `<px>_lint` catches a bad unit, a stale ref and a spec conflict with the kernel never called (asserted by a spy); checkpoint/rollback round-trips through the `.brep` fast path AND through replay (file deleted); sidecar killed mid-session respawns and replays with an identical fingerprint; `<px>_warming` measured on a cold sidecar; `snapshot()` during warming returns `brep: false` and restores by replay; all 14 tools tabled (startup boots), `capability_for("<px>_drawing") == "write-artifacts"`, `capability_for("<px>_script") == "write-scene"`, no `<px>_` in `_FAMILY`; 10 ranking pins top-3; `Test<Kiln>AdapterContract` green on `FakeKernel` with no OCCT; `test_<kiln>_translate.py` green with no kernel; `benchmarks/RESULTS.md` section "draft a bracket, drill it, draw it, export STEP" with both naive bounds and the edit row (§V5); server suite ≥ 1,224 passed; `make lint` clean.

## P5 — drawings (P5a) and sheet metal flat-first (P5b)

*P5a acceptance:* F1 front/top/right third-angle: HLR ≤ 30 ms per view; F1 front **8 visible / 9 hidden** (measured, pinned per compound from P0 row 8); all-filleted F1 front view non-empty (the `VCompound` trap as a test); third angle places top ABOVE front, first angle below, and the default follows the standard (ISO → first); section at x=50 hatch area 500.000, F3 longitudinal 2,700.000, counterbored F1 section reads seat depth 6.000; detail 2:1 reports scale 2 and Ø10.000; dims read back from the model: extents 100.000 / 60.000, Ø10.000, R2, angular 3.000° on the draft, baseline 20…200 on F5, ordinate identical; hole table 100 rows all Ø8.000 at the pattern coordinates; F2 note `4× Ø6.6 THRU (M6 clearance, ISO 273 medium)`; `dimension.value_mm == projected_mm` (`agree: true`) on every dim; SVG parses and a 100 mm line is 100 user units, hidden lines dashed and counted; DXF `$INSUNITS=4`, `DIMENSION.get_measurement()` = 100.0 / 60.0 / 10.0, ezdxf re-reads the same entity counts; PDF (`[pdf]`) A3 landscape mediabox **1190.55 × 841.89 pt** via pypdf with title-block fields as extractable text; parts list 2 rows + 2 balloons on F6.

*P5b acceptance:* F7 (T=2, R=2, K=0.44, 90°, outside legs 50/30, W=40): `ba_mm` **4.524**, `bd_mm` 3.476, flat length **76.524**, bend-zone volume 377.0 (= 9.425·40, K-independent and the test says so); the formula parametrised at K=0.4 → 4.398 and K=0.5 → 4.712; folded − flat volume reported (`+18.8 mm³` on the 50-wide L-bracket of §W3) with the note that explains it; `<px>_flat` DXF layers `OUTLINE/BEND_UP/BEND_DOWN/HOLES`, `$INSUNITS=4`; K default cited (Industrial Press 1994 via Wikipedia CC-BY-SA — a formula citation, no table copied); DIN 6935 `k` named as a different quantity.

## P6 — evidence, interop, ship

Handoff bundles (Blender via `import_file`, Unreal via the content plugin with m→cm, Godot/others "drop-in" refusals per `handoff.ops_for`), capture-through-Blender opt-in (two-rung size ladder, refuse over budget), `docs/<kiln>-lane.md`, `docs/setup-<kiln>.md`, `docs/research/68-mechanical-cad-lane.md` (doc 67's section shape: parity target, licence minefield, OCCT facts, what this machine has, TEE reuse map, defects found, P0 answers), `docs/research/00-index.md` row, DECISIONS (`## A66 — the mechanical CAD lane`: OCCT LGPL+exception, cadquery excluded for casadi/VTK, py-slvs GPL → own solver, casadi → scipy, fpdf2 optional, bd_warehouse/threadlib data, FreeCAD-not-kernel, CI split, mm on the wire), CHANGELOG **0.19.0 (missing today) AND 0.20.0**, `CLAUDE.md` bullet, PROGRESS close-out with the before/after table and numbered gaps (1 GUI; 2 `cad_measure` routing; 3 capture; 4 CI cost; 5 coil/threads L1; 6 ISO 286 fits), version bump ×3, `make mcpb`, clean-unzip verify, the §V4 acceptance session recorded verbatim.

*Acceptance:* bundle lines verbatim — `handshake: {'name': 'tee', 'version': '0.20.0'}`, `always-loaded tools: 17`, `search 'extrude a sketch' reaches <px>_*: True`, `<px>_probe from the bundle -> REFUSED (kernel absent, as expected)` or, with the sidecar built, `mode: sidecar`; `tee doctor` shows `<kiln>` OK naming mode + OCCT + sidecar interpreter version; Blender receives the bracket GLB at 0.120 m long upright via `tee_batch import_file` with `verify.ok`; the ten-step session green with every number matching; **Suites at close** line with both counts; surface unchanged.

## TEE touch list

**ADD**

| path | content |
|---|---|
| `<kiln>/` (repo root) | §D1 in full; `uv.lock`; `NOTICE`; `fixtures/F1..F8.json`; `tests/expected.py` (ONE `EXPECTED` table) |
| `server/src/tee/adapters/<kiln>/__init__.py` | `from .adapter import <Kiln>Adapter; __all__` |
| `server/src/tee/adapters/<kiln>/adapter.py` | seven methods; `INSTALL_HINT`; `_need_<kiln>()`; lazy kernel; `_translate`/`_WIRE_OPS`/`_PASSTHROUGH`; `_record` with `upserts`; checkpoints (§D3); `discard_snapshot` |
| `server/src/tee/adapters/<kiln>/wire.py` | `SidecarKernel` (copied from `gateway/wire.py:70-227`); no `<kiln>` import |
| `server/src/tee/adapters/<kiln>/tools.py` | `register_<kiln>_tools(app)`; 14 `VirtualTool`s; `_need()`; `_adapter(app)` |
| `server/tests/fixtures_<kiln>.py` | `FakeKernel` implementing `KernelClient` with analytic geometry (boxes/cylinders by arithmetic, no OCCT) — the `fixtures_freecad.py` pattern |
| `server/tests/test_<kiln>_adapter.py` | `class Test<Kiln>AdapterContract(AdapterContract)` over `FakeKernel` + trust assertions + 10 ranking pins + `assert len(_DESC) == 17` + `not any(n.startswith("<px>_") for n in _DESC)` + upserts-for-every-created + atomicity |
| `server/tests/test_<kiln>_translate.py` | no kernel: `_translate`, ids, units, refusals, verb completeness vs `<kiln>.document.VERBS` when importable |
| `server/tests/test_<kiln>_live.py` | `importorskip("OCP")`: real `LocalKernel` + real `SidecarKernel` spawned from `sys.executable`; `-m dcc` for the Blender/FreeCAD read-back |
| `docs/<kiln>-lane.md`, `docs/setup-<kiln>.md`, `docs/research/68-mechanical-cad-lane.md` | house forms of `docs/seamkiln-lane.md`, `docs/setup-freecad.md`, doc 67 |

**MODIFY**

| file:line | change |
|---|---|
| `server/src/tee/app.py:211` (after) | `from tee.adapters.<kiln>.tools import register_<kiln>_tools; register_<kiln>_tools(self)` with the metadata-only comment |
| `server/src/tee/cli.py:57` (after `_build_seamkiln_app`) | `_build_<kiln>_app(project, allow_code_exec)`: build adapter, submit the warm job |
| `server/src/tee/cli.py:247` (after godot) / `:250-251` / `:333` | `elif args.adapter == "<kiln>":` / error string / `--adapter` help |
| `server/src/tee/kernel/trust.py:193-363` | 14 `_EXPLICIT` rows under `# A66: <kiln>. Five write files, two mutate the document; tabled individually (the cad_/trade_ rule).` — **no `_FAMILY` row** |
| `server/src/tee/doctor.py:254-299` (pattern) + `:562-578` | `check_<kiln>()`: kernel importable? sidecar python + version? mode; OCCT version; last `warm.json` import time; add to `run_checks` |
| `server/src/tee/purge.py:78-88` | text only: the `sidecars` glob already protects `~/TEE/.tee/sidecars/<kiln>` |
| `server/src/tee/kernel/extras.py` | NOT extended (the lane is not a `tee-engine` extra); note in DECISIONS |
| `benchmarks/run_benchmarks.py:~1231` / `:1800` / `:1802-1804, 1869-1872` / `:~2121, ~2196` | `run_<kiln>_scenario()` + follow-up edit scenario; `_safe(...)`; `write_results` kw; `_<kiln>_section` |
| `benchmarks/RESULTS.md` | `## Mechanical CAD: sketch → features → drawing → STEP (A66)` |
| `.github/workflows/ci.yml` | add job `kiln` (`working-directory: <kiln>`, `uv sync --extra brep --extra dev`, ruff, `pytest -q -m "not slow"`); server job `uv sync --all-extras --no-extra cad` (uv 0.12.5 supports it) + `enable-cache: true` — an explicit choice recorded in DECISIONS; Linux-vs-macOS fingerprints are a volume-tolerance test, not a byte test |
| `server/Makefile:8` / `packaging/mcpb_manifest.json:5` / `server/pyproject.toml:3` | 0.20.0, together |
| `CHANGELOG.md` | 0.19.0 (retroactive) + 0.20.0 |
| `docs/PROGRESS.md`, `docs/DECISIONS.md`, `docs/research/00-index.md`, `CLAUDE.md` | per E3 formats |

**NOT touched:** `packaging/mcpb_manifest.json tools[]`, `server/src/tee/server.py:30 _DESC`, `server/Makefile mcpb:`, `server/src/tee/pdf.py` (PDF stays inside `<kiln>[pdf]`; widening `pdf_compose` with a vector block is a later numbered option), `seamkiln/`.

## Verification

### V1. Test layout

Tier 0 kernel (`<kiln>/tests/`, no TEE, < 90 s): `test_licences.py` (P0b) · `test_units.py` · `test_params.py` · `test_document.py` (replay, overrides, fingerprint) · `test_sketch.py` · `test_features.py` (one function per §V3 number) · `test_naming.py` · `test_assembly.py` · `test_drawing.py` · `test_export.py` · `test_checks.py` · `test_fixtures.py` (F1–F8 from `fixtures/*.json` against ONE `EXPECTED` table) · `test_worker.py` (spawn in the same venv) · `test_examples.py` (`--probe` only) · `test_import_hygiene.py`. OCP-backed modules `pytest.importorskip("OCP", reason="<kiln>[brep] not installed")`. Tier 1 `test_determinism.py`: F2/F5/F6 in two subprocesses → identical fingerprints; `replay().fingerprint()` equal; mesh SHA-256 serial vs parallel; STL/GLB bytes identical on repeat. Tier 3–5 in `server/tests/` (touch list). Tier 6 live `-m dcc`.

### V2. P0 measurement table — §P0a (17 rows), every cell into PROGRESS before P1 starts.

### V3. Fixtures and the EXPECTED table (own-built, licence-clean; scripts so every fixture is a replay test)

| Id | Part (mm) | Pinned numbers |
|---|---|---|
| F1 plate | 100×60×10, Ø10 at (50,30); variants fillet r2 ×4 vertical, chamfer 2×45°, counterbore Ø11×6, countersink 90° Ø12, edit Ø10→Ø12 | V 59,214.602; faces 7; area 15,357.080; COM (50,30,5); fillet −34.336 → faces 11; chamfer −80.000; cbore −98.96; csink −16.76; edit −345.575 → 58,869.027; section x=50 = 500; front HLR 8/9; GLB [0.1,0.06,0.01]; negative GLB [100,60,10]; driven diagonal 116.619 → 125.300 at width 110 |
| F2 bracket | base 80×60×6, upright 80×34×6 on y∈[0,6], inner fillet r6, 4× Ø6.6 at (20,30)(60,30)(20,50)(60,50) | V 44,916.967; faces 13 (unified); t=8 → 58,403.27; t=4 → 30,790.66; mirror → 89,833.933 faces 17; STEP round trip identical |
| F3 shaft | revolve Ø20×50 / Ø30×30 / Ø20×40; cosmetic M20×2.5×30; keyway 6×3.5×30 from a plane tangent to Ø30 | V 49,480.084; faces 7; thread → fingerprint identical; section 2,700; keyway −611.9 |
| F4 housing | 60×40×30 shell 2 top removed; draft box 40×40×20 at 3° | 15,552 faces 11; 30,352.2 |
| F5 pattern plate | 220×220×12, 10×10 Ø8 pitch 20 from (20,20); disc Ø80×5, 6×Ø5 PCD 60 | 520,481.421; faces 106; edges per P0 row 7; disc 24,543.693 faces 9; hole table 100 |
| F6 pin-block | block 40×40×20 Ø10 through; pin Ø10×40; Ø11/Ø9.9 variants; 4-pin pattern; two cubes at x=0/19 | 30,429.204; 3,141.593; DOF 0/1/1/2/3/3; pin at (20,20,20); 329.867; 0.050; 400.000 @ (19.5,10,10); 238.869 g / 24.662 g |
| F7 sheet | T2 R2 K0.44 90°, legs 50/30, W40 | BA 4.524; flat 76.524; bend zone 377.0 |
| F8 import | 10× F5 in a 2×5 grid, AP242 with names | 1,060 faces; 10 products; Σ 5,204,814.21 |

Secondary: BenchCAD (CC-BY-4.0 data, attribution file under `fixtures/third_party/`) — 3 ISO-bound families as STEP goldens for `spec_check`; CADGenBench (ODC-BY) — its 32 edit fixtures drive the edit-impact invariant only (features off the dependency path keep their fingerprint: the 64 % measured as 0 %).

### V4. The recorded acceptance session (P6; `<kiln>/examples/acceptance/run_tee.py` = `test_<kiln>_live.py -m dcc`), public surface only

1. `run_batch("<kiln>", [F2 as ops])` → one diff; `details["part:bracket"].volume_mm3 == 44916.967`, `faces == 13`; batch + diff tokens recorded.
2. `run_batch(set param t=8mm)` → `changed` lists plate/upright/holes, `fillet1 unchanged`, volume 58,403.27; `tee_diff(epoch, rev)` → `modified == ["part:bracket", …]`.
3. `tee_checkpoint` → `tee_rollback` → 44,916.967; the checkpoint file replays in a subprocess to the same fingerprint.
4. `<px>_drawing(views=[front, top, section, iso], dims=[extent_x, extent_y, hole_dia], hole_table, sheet=A3, formats=[svg,dxf,pdf])` → DXF `get_measurement()` 80.0 / 60.0 / 6.6; PDF mediabox A3; text contains `Ø6.6` and `ISO 273`.
5. `<px>_export(formats=[step, glb, stl, 3mf])` → manifest units per format (`glb: metres`, `stl/obj: none declared`).
6. Cross-kernel: `cad_measure(path=bracket.step)` → 44,916.967 ± 1e-6 relative (OCCT 7.9.3); FreeCAD bridge up → import through the A37 adapter (OCCT 7.8.1) ± 1e-6.
7. Blender: `as_ingest` → `as_import(target_dims=[0.08,0.06,0.04])` → `verify.ok`, read_back sorted [0.04, 0.06, 0.08]; `tee_scene_summary("blender")` lists it; one 640-px `tee_capture` as advice, last.
8. Unreal (if up): read-back in cm [4, 6, 8].
9. F6: components + cylindrical joint → `<px>_measure(what=asm)` DOF 2, interference 0 + contact, `<px>_bom` 2 rows; swap Ø11 → 329.867 with centroid.
10. Sum tokens (`estimate_tokens` over every request/response) and wall clock into `benchmarks/RESULTS.md`.

### V5. Benchmark design

`run_<kiln>_scenario()` (the `run_seamkiln_scenario` six-step shape): TEE arm = §W1 batch + diff + one `<px>_check` (≈ 640 + 520 + 120 ≈ 1,280 tok, 2 calls — estimates, measured in P4). Naive arms, both reported and named: (a) face/edge inventory + 3 screenshots + SVG read ≈ 13,650 tok / 6 calls (lower bound); (b) STEP text ≈ 26,800 tok. Second scenario = §W2 + `<px>_bom`. Follow-up row: `param_set T=12mm` → naive re-reads everything (~13k) vs the ~90-tok `changed` list (the A65 per-frame shape). Sections end "Surface unchanged: 17 tools."

## Worked batches with expected diffs

### W1. Mounting bracket → STEP + drawing (12 ops)

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

Expected diff (faces exact; edges pinned by P2 measurement):

```json
{"ok":true,"epoch":1,"revision":1,"checkpoint":"cp1","applied":12,
 "created":["param:W","param:H","param:T","param:PX","param:PY","part:bracket","sk:base","feat:plate","feat:f1","feat:h","sk:slot_sk","feat:slot","feat:c1","dwg:sheet1","export:bracket.step","export:bracket.pdf"],
 "details":{
  "doc":{"assumed":{"units":"mm","angle":"deg","standard":"ISO","drawing_angle":"first"}},
  "sk:base":{"entities":4,"constraints":6,"dof":0,"closed":true,"area_mm2":9600,"frame":{"origin":[0,0,0],"normal":"+Z"}},
  "feat:plate":{"volume_mm3":96000,"delta_mm3":96000,"bbox_mm":[120,80,10],"faces":6,"solids":1,"assumed":{"direction":"+","mode":"new"},"names":["plate.start","plate.end","plate.side.outer[0..3]"]},
  "feat:f1":{"volume_mm3":95785.4,"delta_mm3":-214.6,"faces":10,"resolved":{"plate:edges(dir=Z)":4}},
  "feat:h":{"volume_mm3":94416.92,"delta_mm3":-1368.48,"faces":14,"dia_mm":6.6,"assumed":{"depth":"through","dia":"6.6mm from ISO 273 normal (bd_warehouse, Apache-2.0)"},"names":["h.1.wall","h.2.wall","h.3.wall","h.4.wall"]},
  "sk:slot_sk":{"entities":4,"constraints":5,"dof":0,"closed":true,"area_mm2":306.27,"frame":{"origin":[0,0,10],"normal":"+Z","x":"+X"}},
  "feat:slot":{"volume_mm3":91354.27,"delta_mm3":-3062.65,"faces":18,"assumed":{"direction":"-"}},
  "feat:c1":{"volume_mm3":91158.6,"delta_mm3":-195.7,"faces":26,"resolved":{"plate:edges(of=end, loop=outer)":8}},
  "part:bracket":{"volume_mm3":91158.6,"bbox_mm":[120,80,10],"valid":true,"mass_g":715.6,"fingerprint":"9c1e…"},
  "dwg:sheet1":{"views":2,"dims":6,"assumed":{"scale":"1:1","standard":"ISO","angle":"first"},"dimensions":{"d1":120.0,"d2":80.0,"d3":"4× Ø6.6","d4":100.0,"d5":50.0,"d6":10.0},"projected_agree":true},
  "export:bracket.step":{"path":"out/bracket.step","schema":"AP242","units":"mm","roundtrip":{"volume_ok":true,"faces_ok":true}},
  "export:bracket.pdf":{"path":"out/bracket.pdf","pages":1}},
 "notes":["h: Ø6.6 = ISO 273 normal for M6 (bd_warehouse, Apache-2.0)","bracket: 715.6 g at 7.85 g/cm³ (steel_s275, standard_value)"]}
```

Follow-up `[{"op":"param_set","props":{"T":"12mm"}}]` → `details.doc = {"changed":["feat:plate","feat:f1","feat:h","feat:slot","feat:c1","dwg:sheet1"],"unchanged":0,"failed":[],"volume_mm3":109429.4,"fingerprint":"a7…"}` (~90 tok).

### W2. Shaft in a housing on a bearing → joints, DOF, interference, BOM (18 ops)

```json
[{"op":"create","kind":"part","name":"housing","props":{"material":"steel_s275"}},
 {"op":"create","kind":"sketch","name":"hsk","props":{"part":"housing","plane":"XY","profile":[{"rect":[80,80]}]}},
 {"op":"create","kind":"extrude","name":"block","props":{"part":"housing","sketch":"hsk","distance":"30mm"}},
 {"op":"create","kind":"hole","name":"seat","props":{"part":"housing","on":"block.end","at":[[0,0]],"dia":"47mm","depth":"14mm"}},
 {"op":"create","kind":"hole","name":"bore","props":{"part":"housing","on":"seat.bottom","at":[[0,0]],"dia":"25mm","depth":"through"}},
 {"op":"create","kind":"part","name":"shaft","props":{"material":"steel_s275"}},
 {"op":"create","kind":"sketch","name":"ssk","props":{"part":"shaft","plane":"XY","profile":[{"circle":20}]}},
 {"op":"create","kind":"extrude","name":"pin","props":{"part":"shaft","sketch":"ssk","distance":"100mm"}},
 {"op":"create","kind":"part","name":"brg6204","props":{"material":"steel_100cr6"}},
 {"op":"create","kind":"sketch","name":"bsk","props":{"part":"brg6204","plane":"XY","profile":[{"circle":47,"tag":"od"},{"circle":20,"tag":"id"}]}},
 {"op":"create","kind":"extrude","name":"ring","props":{"part":"brg6204","sketch":"bsk","distance":"14mm"}},
 {"op":"create","kind":"component","name":"housing","props":{"part":"housing","grounded":true}},
 {"op":"create","kind":"component","name":"bearing","props":{"part":"brg6204"}},
 {"op":"create","kind":"component","name":"shaft","props":{"part":"shaft"}},
 {"op":"create","kind":"mate","name":"m_seat","props":{"kind":"insert","a":"bearing.ring.start","b":"housing.seat.bottom"}},
 {"op":"create","kind":"joint","name":"lock","props":{"kind":"rigid","a":"bearing.ring.side.od","b":"housing.seat.wall"}},
 {"op":"create","kind":"joint","name":"spin","props":{"kind":"revolute","a":"shaft.pin.side","b":"bearing.ring.side.id","offset":"-43mm"}},
 {"op":"check","props":{"spec":{"interference_mm3":0,"dof":1}}}]
```

Expected highlights: `feat:block {volume_mm3:192000, faces:6}`; `feat:seat {volume_mm3:167710.78, delta_mm3:-24289.22, faces:8, names:["seat.wall","seat.bottom"]}`; `feat:bore {volume_mm3:159856.79, delta_mm3:-7853.98, faces:9, assumed:{depth:"through"}}`; `feat:pin {volume_mm3:31415.93, faces:3}`; `feat:ring {volume_mm3:19890.99, faces:4, names:["ring.start","ring.end","ring.side.od","ring.side.id"]}`; `mate:m_seat {dof_removed:5, pose:{"cmp:bearing":{at:[0,0,16],rot:[0,0,0]}}}`; `jt:lock {dof_removed:1}`; `jt:spin {dof_removed:5, pose:{"cmp:shaft":{at:[0,0,-27]}}}`; `asm {components:3, grounded:["housing"], dof:1, residual:2e-10, interference:[], clearance_mm:{"shaft-housing.bore":2.5}, contacts:[["shaft","bearing",0.0],["bearing","housing",0.0]]}`; `check {verdict:"pass"}`; notes `"asm: 1 DOF = shaft spin about jt:spin (12 movable − rank 11)"`, `"brg6204: stand-in solid ring 19,891.0 mm³ (156.1 g); a real 6204 is ~106 g — <px>_standards carries the envelope, not the internals"`. `<px>_bom {}` → rows housing 1,254.9 g, shaft 246.6 g, brg6204 156.1 g (honesty `stand-in`), total 1,657.6 g, `view: parts-only` (~130 tok).

### W3. Sheet-metal L-bracket → flat pattern (P5b; 2 ops)

```json
[{"op":"create","kind":"sheet","name":"brk","props":{"t":"2mm","width":"50mm","material":"steel_dc01",
   "flanges":[{"len":"60mm"},{"len":"40mm","angle":"90deg","r":"2mm","dir":"up"}],
   "holes":[{"flange":0,"at":[[15,-15],[15,15]],"std":"M5 clearance normal"}]}},
 {"op":"export","props":{"format":"dxf","of":"brk.flat","out":"out/brk_flat.dxf"}}]
```

Expected: `"sheet:brk":{"t":2,"k":0.44,"assumed":{"k":"0.44 (typical 0.3–0.5; BA = A·π/180·(R + K·T), Industrial Press 1994 via Wikipedia CC-BY-SA)","relief":"none"},"bends":[{"angle":90,"r":2,"ba_mm":4.524,"bd_mm":3.476,"ossb_mm":4.0}],"flat_mm":[96.524,50],"flat_volume_mm3":9557.4,"folded_volume_mm3":9576.2,"folded_bbox_mm":[60,50,40],"holes":{"h.1":5.5,"h.2":5.5},"mass_g":75.2}`; note `"folded − flat = +18.8 mm³: the bend zone is an annular sector (471.2), the flat strip is BA×T×W (452.4) — the K-factor's whole effect, kept visible"`; export `{"layers":["OUTLINE","BEND_UP","HOLES"],"units":"mm ($INSUNITS=4)"}`.

## Risk register (each judged defect is closed by a row)

| Risk | Mitigation / test |
|---|---|
| Cold first import blocks a call | P0 row 1 measures; warm job at boot; `<px>_warming` with job id; sidecar resident; `snapshot()` degrades to script-only while warming |
| novtk clobbers `server/.venv`'s OCP (both wheels ship `OCP/`) | dev hint installs `-e <kiln>` WITHOUT `[brep]`; `[brep]` only in the sidecar venv; P0 row 3 |
| Sidecar dies / OCCT segfault on a boolean | history mirrored; respawn + replay; `_dead()` names exit + log; failed batch → auto-checkpoint restore |
| No per-op cancellation inside OCCT | wire deadline 60 s + kill/respawn; `MAX_BATCH_S` from P0 row 17; `Message_ProgressRange` hook if any class > 10 s |
| Topological naming after edits | history-derived roles + fingerprint fallback + fail-loud with candidates; `changed/unchanged/failed` in every edit diff; face-reorder test; unify-same-domain history merged |
| STEP written as AP214 despite the setting | `Init_s()` → `SetCVal_s` → `Model(True)`; `FILE_SCHEMA` asserted |
| glTF mm-as-metres | `SetLengthUnit_s(doc, 0.001)`; negative fixture keeps the trap visible; STL/OBJ manifests say "declares nothing" |
| HLR draws nothing on filleted parts | union of the three visible compounds; filleted-F1 fixture non-empty; PolyAlgo opt-in after whole-shape mesh |
| Wrong acceptance arithmetic (BA 4.71 at K=0.4; DOF −3; countersink 95.82; ring 19,892.6) | every number recomputed with Python 3.11 in this plan (§Measured facts 14); ONE `EXPECTED` table; parametrised BA at K=0.4/0.44/0.5 |
| Fillet refusal fixture that succeeds (r6 on a 10 mm plate) | r=12 on the top-front edge; refusal asserted with `NbFaultyContours` naming the edge |
| Edge-count pin measured on the wrong mechanism (624 sequential) | edges pinned from P0 row 7 under n-ary + `SimplifyResult` |
| Licence drift (unlicensed bd_materials, mislabelled nlopt, Apache-over-LGPL payload, GPL py-slvs by habit) | SPDX allowlist + `KNOWN_PAYLOADS` + no-metadata=fail + intruders; own scipy solvers; py-slvs dev-only oracle |
| Autodesk marks in shipped names / docs test tripping on legitimate prose | test scoped to identifiers and shipped strings, not docs |
| ISO 286 fits with no permissive source | `fit` out of v1; L2 derives from ISO 286-1 formulas with citation or stays out |
| Untabled `<px>_*` crashes startup / a writer inherits the read tier via a family | 14 explicit rows, no family; test asserts each capability; `<px>_script` is write-scene (its replay mutates), `<px>_materials` is pure lookup |
| sympy/eval on model-supplied expressions | AST-whitelisted evaluator; `__import__` refusal test |
| Bare-float refusal taxing every number (parity draft) | mm default + `assumed` once + opt-in `strict_units` |
| MCP client timeouts on exports/HLR/big interference | `job: true` routes; bbox prefilter on pairs; `<px>_too_long` prediction |
| Memory growth over a long session | `rss_mb` in every reply's meta; cap → planned restart + replay |
| Wrong Python builds the sidecar | every documented line pins `--python 3.11`; `check_<kiln>` reports the interpreter |
| `.mcpb` upgrade wipes an editable install | sidecar venv survives; doctor says which mode is live; `_need()` names both routes |
| CI cost (1.3 GB `[cad]` per push already) | `kiln` job on `[brep]` (novtk ≈ 250 MB, P0 row 2); server job `--no-extra cad`; cache |
| Cross-platform fingerprints (Linux CI vs arm64) | rounded fingerprints; golden volumes at 1e-6 relative; byte identity only within one platform |
| Scope creep toward Inventor's whole ribbon | closed `_VERBS`; doc 68 parity matrix marks each row v1/L1/L2/out with its number |
| A picture wanted where text was offered | `<px>_drawing` SVG is the picture; Blender JPEG opt-in in P6 |

## Decisions the owner must confirm (design proceeds under the marked assumption; none blocks P0)

1. **Licence posture** — assumed A53's: MIT kernel, permissive in-process, OCCT LGPL-2.1+exception the one weak-copyleft dependency (NOTICE shipped), GPL only out-of-process or absent (so py-slvs is a dev-only oracle even though `physical/sketch.py` links it under `[physical]`). A45's "just for me" stance would let py-slvs in-process — say so and the gate's BANNED row for it becomes a WARN.
2. **GUI** — assumed a later optional phase: PySide6 client of `Document` under `[gui]`, never required by a test, not in v1.
3. **Name and prefix** — `<kiln>` is a *kiln word (`voxkiln`, `seamkiln` precedent); candidates `forgekiln`/`fg_`, `ironkiln`/`ik_`, `boltkiln`/`bk_`; the prefix must not be `cad_` (fleet), `sk_`, `fc_`, and must not read as an Autodesk mark. Find-and-replace once chosen.
4. **Scope v1** — assumed parts + assemblies + drawings + exports (P1–P5a), sheet metal flat-first as P5b, coil/helix and threads-as-geometry L1, ISO 286 fits L2; FEA/CAM/tube & pipe/harness/frame generator out.
5. **CI extension** — assumed yes: a `kiln` job on `[brep]` and `--no-extra cad` on the server job (recorded in DECISIONS).
6. **`cad_measure` fate** — assumed unchanged in v1 (P6 gap 2 names the routing option).

## Out of scope (say no to these in writing)

FEA/stress/modal, CAM/toolpaths, tube & pipe, cable & harness, frame generator, design accelerators (gears/belts/cams/shaft calculators), mould/plastic features, T-spline/freeform, direct edit, model states beyond suppression, simplify/shrinkwrap, presentations/exploded animations, 3D PDF/DWF/DWG, USDz (until a permissive USD path is measured — A53 Gap 1), proprietary imports (Parasolid/SAT/JT/CATIA/NX/SW/Creo/Rhino/IFC), `.ipt/.iam/.idw/.ipn/.ide` in any direction, Autodesk marks in names, cloud collaboration/multi-user, a renderer of our own (Blender renders), the GUI (later, a client of the core), and matching Inventor's speed before P0's numbers exist.