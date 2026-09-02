**(a) Unsourced or contradictory claims**

1. **Licence posture is contradicted by the repo's own owner decision.** W1's OPTIONAL-ONLY / OUT-OF-PROCESS-ONLY verdicts, W4 §3 "fixtures for a commercial product", W2's IP guardrail and E3's "licence audit is load-bearing" all assume distribution. `docs/DECISIONS.md:908-918` (A45, owner verbatim *"its just for me, keep it simple"*) rules that copyleft "stops driving architecture"; `docs/DECISIONS.md:1013-1016` says fpdf2 (LGPL) is fine "and TEE is private and not distributed". A53 then reasserted "cannot ship" framing (`CLAUDE_A53_SCRIPT.md:47-61`) with no recorded owner statement on selling. No report cites A45.
2. **py-slvs: three positions.** W1 = OUT-OF-PROCESS-ONLY (GPL-3.0, no exception); E2 = "reuse `solve_sketch` as-is"; repo = already imported in-process via the `[physical]` extra (`server/pyproject.toml:44-47`; `py_slvs-1.0.6` present in `server/.venv`; `docs/DECISIONS.md:294` A21).
3. **The 140 s first import has three explanations and one measurement.** `docs/PROGRESS.md:6718-6719` says "bytecode compilation of OCP"; `docs/PROGRESS.md:7114-7115` says the cause was "torch (via MONAI) and the CadQuery stack"; W3 §10.51 measured the whole Python closure compiling in 0.51 s and calls the number unsupported. E2 fact 1 carries it as settled.
4. **"cad is NOT in TEE's venv" (E1 §4) vs "cadquery imports cleanly from server/.venv (verified)" (E2 §1).** Both true of different venvs: `server/.venv` is 3.2 GB and holds cadquery 2.8.0, `cadquery_ocp-7.9.3.1.1`, casadi, nlopt, vtk (from `uv sync --all-extras`, which `.github/workflows/ci.yml:18` also runs on every push); the Desktop bundle venv has none. Neither report says which venv it means.
5. **W4 design rule 11 ("≤6 always-loaded verbs: `cad_batch`…") contradicts Law 4 / `EXPECTED_TOOL_COUNT = 17`** (`server/tests/test_server_lint.py:82`) and collides with the `cad_` policy (`trust.py:179-182`: no family rule; `cad_scad_build/measure/probe` already tabled at `:293-295`). E2's alternative prefix `inv_*` violates W2's own "do not reuse Autodesk marks".
6. **E2 says a persistent sidecar is "a new mechanism".** Precedents exist: `server/src/tee/adapters/godot/adapter.py:70,323,357` (Popen a headless engine + socket bridge) and `server/src/tee/gateway/wire.py:1-10` (newline-delimited JSON-RPC over a spawned subprocess, deadlines on every read).
7. W3 states the local OCP runtime is "7.9.3.1"; dist-info in both `server/.venv` and `~/TEE/.tee/sidecars/cad` is `cadquery_ocp-7.9.3.1.1`.
8. W1's nlopt "effective LGPL-2.1" is inference from build flags, not a licence statement by the wheel author; W1's bd_materials "no licence" rests partly on GitHub API 404s (rate-limit-prone); W1 trap 12 admits casadi's bundled IPOPT/MUMPS were not audited.
9. W4: BenchCAD "CC-BY-4.0 data / MIT code" is sourced to the paper text only; build123d-mcp's CADGenBench gains are self-reported in its README.
10. W2 inventories Inventor **2026** help while autodesk.com sells **2027**; the Autodesk Assistant scope is contradictory across two Autodesk blogs (W2 flags it, does not resolve it).
11. Replay-law determinism: W3 fact 29 is one local run with "no documented guarantee"; nobody measured B-rep (boolean/fillet) determinism across processes, which E2/E3's fingerprint-replay design requires.
12. `physical/sketch.py` docstring says 2 free DOF, code allows 3 (`sketch.py:209`) — E2 flags it; verified real.

**(b) What a planner still does not know (with the closer)**

13. **The owner's verbatim directive, scope (parts / assemblies / drawings / sheet metal / GUI?) and commercial intent.** Nothing in `docs/PROGRESS.md`, `docs/DECISIONS.md`, `CLAUDE.md` mentions "Inventor". Closest brief: `docs/research/52-fabrication-cad-lane.md:10-17` ("Autodesk Fusion trial expiring — wants a headless CAD embedded in TEE 'just like Blender'") — uncited by all seven reports. Closer: AskUser; `sed -n 1,60p docs/research/52-fabrication-cad-lane.md`.
14. **The kernel fork is undecided and one candidate was never evaluated.** `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd` (1.1.3) exists headless with Sketcher/planegcs (DOF + conflict reporting), PartDesign, TechDraw, SheetMetal WB, TNP mitigation; `docs/setup-freecad.md:5-8` calls it "the headless vehicle"; doc 52:36-43 planned it day one. Closer: `time /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd -c "import FreeCAD,Part,Sketcher,PartDesign,TechDraw; print(FreeCAD.Version())"`; measure RSS; test `TechDraw` SVG headless (#5710) and `Sketch.solve()` return codes; test driving one long-lived freecadcmd over stdin JSON lines.
15. **Python floor.** `server/.python-version` = 3.11, `server/.venv` = 3.11.15, sidecar = 3.11.15, default `python3` = 3.14.7. W1's cp314 worries are moot for TEE but fatal if a session builds the sidecar with `python3`. Closer: `cat server/.python-version`.
16. **build123d + cadquery-ocp-novtk footprint** (absent from every venv: verified). Closer: `uv venv $SCRATCH/bd --python 3.11 && uv pip install --python $SCRATCH/bd/bin/python build123d && du -sh $SCRATCH/bd/lib && otool -L $SCRATCH/bd/lib/python3.11/site-packages/OCP/OCP.cpython-311-darwin.so | grep -c vtk` (expect 0) and `$SCRATCH/bd/bin/python -c "import importlib.metadata as m; print(m.requires('build123d'))"` (confirm no bd_materials).
17. **OCP binding coverage on the novtk wheel** for the load-bearing classes (W3 verified on the vtk wheel only). Closer: `python -c "from OCP.BRepTools import BRepTools_History; from OCP.TNaming import TNaming_Builder; from OCP.HLRBRep import HLRBRep_Algo,HLRBRep_PolyAlgo; from OCP.RWGltf import RWGltf_CafWriter; from OCP.BRepFeat import BRepFeat_MakeDPrism; from OCP.XCAFDoc import XCAFDoc_DocumentTool; from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet"`.
18. **A permissive 2D constraint solver with DOF/conflict output** was never surveyed (only GPL py-slvs/SolveSpace). Candidates to check: planegcs via freecadcmd (LGPL, out-of-process); scipy least-squares + Jacobian rank (W3 §6 pattern, BSD); `https://pypi.org/pypi/pyslvs/json` (licence unknown to me — verify). This decides W4 rule 3.
19. **Unit convention for the lane's wire ops**: metres (`physical/sketch.py:5`, `extract/plan.py:7`) vs mm (`adapters/freecad/codegen.py:9-10`, `physical/joinery.py:13`) vs unit strings (W4 rule 4). Undecided; `tee_batch` `props` is an untyped dict (`server.py:64-67`) so any can be carried.
20. **Timeout policy for long OCCT ops.** `kernel/script.py:29` MAX_SECONDS=120, `fleet/cad.py:43` BUILD_TIMEOUT=300, MCP client timeout unknown. Closer: `grep -rn "timeout" server/src/tee/server.py server/src/tee/kernel/registry.py`; decide the threshold above which a batch goes to `app.jobs.submit`.
21. **Fate of `fleet/cad.py` and the `[cad]` extra** (retire, or route `cad_measure` through the new persistent sidecar). Closer: `sed -n 200,295p server/src/tee/fleet/cad.py`; `git show 5a68fbd --stat`.
22. **Checkpoint payload for OCCT state**: replay-script (seamkiln) vs `BRepTools.Write_s` per checkpoint. Closer: build a ~100-feature part, `BRepTools.Write_s(shape, path, False, False, TopTools_FormatVersion_VERSION_3)`, record bytes and ms; `contract.py:134-145` defines the roundtrip test.
23. **Persistent sidecar protocol** to copy: `sed -n 25,140p server/src/tee/gateway/wire.py` vs `sed -n 323,380p server/src/tee/adapters/godot/adapter.py`.
24. **Fixture licences at source**: BenchCAD dataset LICENSE (locate via the data link in `https://arxiv.org/html/2605.10865v1`); `https://github.com/huggingface/cadgenbench/blob/main/LICENSE`; bd_warehouse NOTICE and CSV provenance headers (`https://raw.githubusercontent.com/gumyr/bd_warehouse/main/src/bd_warehouse/data/clearance_hole_sizes.csv`).
25. **Where the lane package lives vs the wipe trap**: seamkiln is an editable install in `server/.venv` (`_editable_impl_seamkiln.pth`) and absent from the Desktop bundle; a sidecar venv survives upgrades and `tee_purge` (`purge.py:78-88`), an editable install does not and is untracked by `extras.py` WITNESS. Not settled for a pure-Python kernel + OCCT sidecar split.
26. **GUI requirement**: A53's directive demanded a GUI (PySide6, LGPL-3.0, `seamkiln/pyproject.toml:43-45`); unknown for this lane. AskUser.
27. Machine facts for the P0 table are unrecorded in the reports: Apple M5 Max, 18 cores, 128 GB, macOS 26.6.2 (`sysctl -n hw.memsize hw.ncpu machdep.cpu.brand_string; sw_vers`).
28. Inventor 2027 What's New was not consulted; verify `https://help.autodesk.com/cloudhelp/2027/ENU/Inventor-WhatsNew/` exists before naming 2026 the parity target.

**(c) Facts load-bearing enough to probe in P0, not trust**

29. Cold vs warm import of `OCP` (novtk and vtk wheels), `build123d`, `cadquery`: `sudo purge; time python -c "import OCP"` ×2 each — decides sidecar residency/warm-up design (item 3).
30. VTK link count on the novtk `OCP.so` via `otool -L` (the vtk wheel links 9 VTK dylibs — verified on `server/.venv`).
31. That `uv pip install build123d cadquery-ocp-novtk` resolves for cp311 macOS arm64 (W1 read the index; never installed).
32. STEP: `Interface_Static.CVal_s("write.step.schema")` on this runtime (expect AP214IS, not the 8.0.1 doc's AP214CD) and an AP242DIS write→read round trip comparing volume/face count/names.
33. glTF scale: export a 10 mm cube via build123d `export_gltf` and via raw `RWGltf_CafWriter` without `SetLengthUnit`, then `tee.assets.gltf.probe` (`assets/gltf.py:127-193`) — expect `extents_m` 0.01 vs 10.
34. HLR on a filleted part: `VCompound` empty, edges in `Rg1LineVCompound`; `HLRBRep_PolyAlgo` on unmeshed input fails — both as test fixtures.
35. Determinism: `BRepMesh` hash under `InParallel=True`, and B-rep fingerprint (volume to 1e-9 + `BRepTools.Write` without triangulation) of the same feature script in two fresh processes — the replay law rests on it.
36. py-slvs licence metadata (`python -c "import importlib.metadata as m; print(m.metadata('py-slvs')['License'])"`) plus the owner's answer to item 1; if GPL is unacceptable in-process, item 18 becomes P0.
37. bd_materials absence from installed build123d 0.11.1 (`importlib.metadata.requires`) and `https://pypi.org/pypi/bd-materials/json` licence fields; pin `build123d<0.12`.
38. If cadquery is chosen at all: `python -c "import cadquery,sys; print('casadi' in sys.modules, 'nlopt' in sys.modules, 'vtkmodules' in sys.modules)"`.
39. If FreeCAD is a candidate: freecadcmd boot time, RSS, headless TechDraw SVG (#5710), SheetMetal WB import, `Sketch.solve()` DOF/conflict output (item 14).
40. RSS after `import build123d` in the sidecar (2 daemon job workers × residency; 128 GB machine, but the number still goes in the table).
41. `trimesh` in `server/.venv` is 5.0.0 (W1 cites 5.1.0) — probe `trimesh.exchange.threemf.export_3MF` if 3MF is in scope.
42. OCCT LGPL + exception obligations (ship `OCCT_LGPL_EXCEPTION.txt`, "prominent notice") are a deliverable only if item 1 answers "distribute" — decide before P0 closes.

**(d) What a fresh session would get wrong**

43. Adopt W1's isolation verdicts as law (or, conversely, A45's "private" stance and skip the gate) without asking the owner; A53 made the gate mandatory in `CLAUDE.md`.
44. Copy `seamkiln/tests/test_licences.py` believing it catches copyleft: it matches only `NON_COMMERCIAL_MARKERS` and named `BANNED` packages (`test_licences.py:28-59`); GPL py-slvs, MIT-labelled nlopt and licence-less bd_materials (empty `_licence_text`) all pass. A CAD gate needs an SPDX allowlist plus "no licence metadata = fail".
45. Name tools `cad_*` and add a `_FAMILY` row, or forget `_EXPLICIT` entries → boot crash `trust_untabled_tool` (`registry.py:86-91`); or name them `inv_*`.
46. Follow W4 rule 11 and add always-loaded tools, or touch `packaging/mcpb_manifest.json` `tools[]`.
47. `import cadquery` (casadi + VTK, 1.16 s warm) instead of build123d over `cadquery-ocp-novtk`; assume `import OCP` is VTK-free.
48. Trust `occt3d.com/dev/doc` as 7.9 — it documents 8.0.1.
49. Reuse `fleet/_cad_worker.py` as-is (one-shot, re-imports OCP per call) and miss the `gateway/wire.py` / godot precedents.
50. Reuse `physical/sketch.py` without noticing its metre contract vs the mm lane, and its GPL dependency.
51. Assume cadquery `exportGLTF` writes metres (never sets `XCAFDoc_LengthUnit`): a 10 mm part lands as 10 m in Blender.
52. Design a bytecode-precompile step or a warm-up daemon around the unmeasured 140 s.
53. Emit `Diff.created` without `upserts` → `SceneCache` blind (`kernel/adapter.py:47-52`; copy seamkiln `_record`).
54. Put the benchmark scenario in `SCENARIOS` (Blender-bridge loop) instead of `_safe(run_<lane>_scenario)` (`run_benchmarks.py:1800-1804`).
55. Copy seamkiln's test shape (no `AdapterContract`, module-level `importorskip`) and expect CI to run the lane package (`ci.yml` runs `server/` only, and installs the 1.3 GB `[cad]` stack on every push via `--all-extras`).
56. Assume the `.mcpb` carries the lane or that `tee doctor` covers it (seamkiln added no check; `check_voxkiln` is the pattern).
57. Treat FreeCAD.app's OCCT 7.8.1 and OCP's 7.9.3 as one kernel when comparing lanes.
58. Build the sidecar with default `python3` 3.14.7 (TEE is 3.11).
59. Vendor FreeCAD Fasteners/BOLTS/Wikipedia tables or FreeCAD's `ElementMap` code (LGPL) instead of the scheme; use Fusion 360 Gallery / Text2CAD / CAD-Recode (NC) as fixtures.
60. Treat W2's 2026 inventory as the target while 2027 ships, and reuse Autodesk marks (`iLogic`, `iPart`, "Inventor") in tool or product names.
61. Assume build123d Joints solve anything, `BRepFeat_MakeCylindricalHole` makes counterbores, `BRepTools_History` tracks wires/shells, or `BRepBndLib::Add` is tight.
62. Assume the CHANGELOG has 0.19.0 (stops at 0.18.0), the research index is current (stops at 48; next doc is 68), or that `docs/research/52` is superseded — it is the only recorded owner brief for "headless CAD in TEE" and A37 already answered it with FreeCAD; the new script must say why FreeCAD is or is not the kernel.