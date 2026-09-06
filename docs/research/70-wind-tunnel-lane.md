# 70 — The wind-tunnel lane: OpenFOAM, SU2, OpenVSP/VSPAERO and ParaView at arm's length (2026-09-06)

Research of record for **A68** (`wt_*`). Every licence claim below was checked at its source on
2026-09-06 (URLs inline); everything tagged `measured 2026-09-06` was executed in the Linux
build container (Ubuntu 24.04.4 x86_64, 4 cores, 15 GB, no display, Python 3.11.15) through
TEE's own registry — the numbers are what `wt_*` tools returned, not what a shell script
printed. Claims carried from earlier TEE research are marked `(doc NN)`. The owner's Apple
Silicon Mac rows (M1–M7, C1–C3, S1) are **deferred to an owner session by decision** and are
listed in §8 as a checklist, never as numbers.

---

## 1. What the lane is for, and what already exists

The owner asked for OpenFOAM, SU2, the GUI wrappers (SimFlow, FreeCAD CfdOF, OpenVSP) and
ParaView "directly into TEE, headless and with GUI". Nothing of the kind existed: no CFD
code, no `OpenFOAM`/`SU2`/`ParaView` string outside prose. Doc 52 (2026-08-28) had parked
OpenFOAM — *"Revisit only for a real airflow-engineering task"* — and doc 54 dispositioned
OpenVSP as an asset SOURCE for the board lane. This request is the trigger doc 52 wrote for
itself; `docs/DECISIONS.md` reverses the ruling and quotes it.

What TEE adds that the platforms lack is what TEE exists for: **one small, budgeted loop over
all of them in which the model never sees a cell.** Every platform runs out of process; results
come back as coefficient tables, convergence verdicts and ≤ 64-row digests; pixels are opt-in;
long solves are jobs on the machine ledger. "Consolidate" is delivered by making **the case
directory the interface**: a standard OpenFOAM case or SU2 `.cfg` from any source (CfdOF, a
tutorial, a hand-made case, TEE's own writer) enters the same run → status → result → view
loop. "With GUI" is deferred by owner decision (2026-09-06, "headless only for now").

The lane copies the `pc_*` lane structurally (A67: in-server package, virtual tools, one trust
row per tool, zero always-loaded growth) and the capture lane operationally (A42: binaries at
arm's length, jobs on the ledger, streamed logs).

---

## 2. The licence audit — everything copyleft or NOSA stays a separate process

| Component | Licence (verified at source, 2026-09-06) | Reaches the lane by | Verdict |
|---|---|---|---|
| OpenFOAM (openfoam.com v2606; apt `openfoam` v1912) | GPL-3.0 — `https://www.openfoam.com/licence` | subprocess through `etc/bashrc` (Linux) or the app's `etc/openfoam` entry script (Mac) | **ENGINE, never imported, never vendored** |
| SU2 8.4.0 | LGPL-2.1 — `https://github.com/su2code/SU2/blob/master/LICENSE.md` | subprocess `SU2_CFD` (static linux64 binaries; `pysu2` is not on PyPI) | **ENGINE** |
| OpenVSP 3.51.3 / VSPAERO 7.2.2 | NASA Open Source Agreement 1.3 — `https://openvsp.org/license.shtml` | subprocess `vspscript` (AngelScript), `vspaero` beside it | **ENGINE**; the bundled Python API is recorded (§3 L8) and banned from import |
| ParaView 5.11.2 (apt) / 6.1.1 | BSD-3 — `https://www.paraview.org/license/` | subprocess `pvpython` running TEE-written scripts | **DRIVER, never `import vtk`** (docs 46/68: VTK is 600 MB of weight the kernel does not need) |
| gmsh | GPL-2.0-or-later | not in v1 (a later 3-D SU2 phase would shell out) | out of scope, graded OUT-OF-PROCESS-ONLY in doc 68 |
| FreeCAD CfdOF workbench | LGPL-3.0 — `https://github.com/jaheyns/CfdOF` | none: a CfdOF-written case is adopted as a directory; the RPC route goes through TEE's one FreeCAD bridge | **ADOPTION**, the one-bridge rule of `docs/setup-freecad.md` stands |
| SimFlow | proprietary freeware; site blocks non-browser fetches | none | **not integrable as software**; if it writes a standard OpenFOAM case, that case is adoptable (owner row S1) |
| `foamlib` | **GPL-3.0-only** (PyPI `license_expression`, 2026-09-06) | — | **BANNED** by `test_windtunnel_licences.py` |
| `PyFoam`, `fluidfoam`, `ofpp` | GPL | — | **BANNED** |
| `pyvista`, `vtk`, `classy_blocks` | MIT / BSD | — | **DROPPED on weight**, banned from import so they cannot creep back |
| `meshio` 5.3.5 | MIT (PyPI classifier) | the optional `[windtunnel]` extra | **ADOPT**, reached lazily by exactly one function (`report._export_vtu`) |
| `numpy` | BSD-3 | the same extra | **ADOPT** (the lane itself is stdlib at import) |

The gate is a test, not a note: `server/tests/test_windtunnel_licences.py` imports every lane
module in a fresh interpreter and asserts none of the banned names loaded, AST-scans every
import site, confines numpy/meshio to `report._export_vtu`, pins the extra to
`{meshio, numpy}`, checks the installed metadata licences, and scans the goldens under
`tests/data/windtunnel/` for OpenFOAM / SU2 / gmsh file banners. **No tutorial case is ever
vendored** (OpenFOAM's tutorials are GPL-3 data, the BOLTS-tables defect class): fixtures are
written by TEE's own writers, and the three goldens carry a `transcribed from a run TEE made`
line with their header verbatim and their rows shortened.

---

## 3. Measured facts (the P0 table, 2026-09-06, this container)

### 3.1 OpenFOAM: the apt package cannot report a force; openfoam.com's can

| Row | Finding |
|---|---|
| L1 apt `openfoam` 1912 | 128 MB; binaries under `/usr/bin`; **direct invocation fails** ("Could not find mandatory etc entry controlDict"): the binaries need their environment. `bash -c 'source /usr/share/openfoam/etc/bashrc; exec <app> …'` is clean; `WM_PROJECT_VERSION=v1912`. `/usr/bin/mpirun` is Open MPI 4.1.6. |
| L1 function objects | **BROKEN in the apt build**: every function object (forceCoeffs with either `libs` spelling, the tutorial's own block, residuals, `simpleFoam -postProcess`) dies at "Starting time loop" with `FOAM FATAL IO ERROR: error in IOstream "sha1"`. A case with no `functions` entry runs. `runTimeModifiable false` does not help. |
| L1b `openfoam2606-default` from dl.openfoam.com | 340 MB under `/usr/lib/openfoam/openfoam2606` (bashrc route); `WM_PROJECT_VERSION v2606` — the same version the owner's OpenFOAM.app carries. Function objects **work**: `forceCoeffs` writes `postProcessing/forceCoeffs1/0/coefficient.dat` with the header `# Time Cd Cd(f) Cd(r) Cl Cl(f) Cl(r) CmPitch CmRoll CmYaw Cs Cs(f) Cs(r)` under eleven `# key : value` lines. **Decides:** `engines.py` prefers `/usr/lib/openfoam/openfoam*` over `/usr/share/openfoam`; the setup doc's Linux line is openfoam.com's repository, not Ubuntu's package. |
| L2 the 2-D tunnel | TEE-written NACA 0012 O-mesh, 200 × 80 = 16,000 cells (growth 1.173, farfield 50 c, first cell 2.4e-5 m for y+ 1 at Re 2.05e6), kOmegaSST low-Re, 30 m/s, α 4°: **residualControl stop at 197 iterations, 17.2 s wall through the registry** (7.9 s solver time), RSS 80 MB, 1 core. Cl 0.4356 (thin airfoil 2πα = 0.4386, −0.7 %), Cd 0.01091 (Abbott & von Doenhoff 0.0095–0.0100 at Re 2–3e6: +10 %, a coarse mesh), Cm 0.0006. `k_openfoam` = **2.36 µs per cell-iteration per core**; the log grows **736 bytes per iteration**. |
| L2 defect | With `Aref = 1` the coefficients were 10× small: **a 2-D slab's reference area is chord × thickness** (0.1 m); `write_polymesh` returns the thickness and the run uses it. |
| L2 checkMesh | 16,000 cells; 1 failed check: max skewness 12.7 with **6 highly skewed faces on the trailing-edge seam** (an arc-length farfield mapping did not remove them: they are inherent to a sharp-TE O-mesh); max aspect ratio 243 (the y+ 1 cells). The solver converges regardless; the lane tolerates exactly that one failure. |
| L3 coefficient file | Read by header, never by column: the reader survives a reordered header and names a missing column (goldens + tests). |
| L4 parallel | 1 / 2 / 4 cores on the 16,000-cell case: **7.8 / 6.8 / 4.8 s** wall for 197 iterations (decomposePar + reconstructPar overhead included); the parallel results agree with serial to 1.5e-5 in Cl. **First attempt died in 1.1 s: Open MPI refuses to run as root** ("We strongly suggest that you run mpirun as a non-root user"). `runs.mpi_env` sets `OMPI_ALLOW_RUN_AS_ROOT(_CONFIRM)=1` for root only and for a parallel run only, and the run record says `mpi_root_override`. A workstation never sees it. |
| L10 log growth | 736 B per simpleFoam iteration; 119 B per SU2 history row (189 B per screen row): a 64 KB tail always holds the last residual set. |
| L11 cancel, real solver | `tee_job cancel` mid-run: `wt_status` said iteration 42 with residuals and coefficients (72 tokens); the pid was **gone 0.05 s after cancel**; job and run both `cancelled`; the 100 coefficient rows written so far read back under `allow_partial` with verdict `cancelled`; only the `0` time directory remained (writeInterval = iters). |
| L12 LLM contention | **Not possible here**: the container has no local LLM to run beside a solve. The ledger risk stays open (§9). |
| L13 the apt airFoil2D tutorial, adopted run-only | Adopted in 183 tokens: simpleFoam, SpalartAllmaras, dialect `com`, patches inlet/outlet/walls/frontAndBack, inlet U (25.75, 3.62, 0), **no forceCoeffs**, `Allrun` uses `$(getApplication)` (named, not run). checkMesh on its mesh: 10,720 cells, one failed check **"Faces not in upper triangular order"** — a matrix-ordering remark `renumberMesh` fixes, so the lane tolerates it beside the skewness one. Run without forces: 313 iterations, 5.0 orders, verdict `converged` **from residuals only, no invented number**. Run with `forces={"patches": ["walls"]}`: the function object goes into TEE's run copy; the chord is **measured from the wall patch: 35.05 m** (with lRef 1 the first attempt returned Cl 34); Aref = 35.05 × 0.05 m slab depth = 1.75 m²; **Cl 0.970, Cd 0.0294, Cm −0.0144 at α 8°**, converged, 4.8 s. The tutorial directory is untouched. |

### 3.2 SU2 8.4.0

| Row | Finding |
|---|---|
| L5 binary | `SU2-v8.4.0-linux64.zip` 30.9 MB (a nested `linux64.zip` inside), static `SU2_CFD/SU2_DEF/SU2_DOT/SU2_GEO/SU2_SOL`; no `pysu2`. GitHub's HTML/API is blocked by the proxy but release assets download. |
| L5 QuickStart on its official mesh | `inv_NACA0012.cfg` (M 0.8, α 1.25°, 10,216 elements): converged in **147 iterations, 9.85 s, RSS 41 MB**; **CL 0.328486, CD 0.021481**. `history.csv` carries only residual columns by default — the writer sets `HISTORY_OUTPUT= (ITER, WALL_TIME, RMS_RES, AERO_COEFF)`, after which the header is `Time_Iter, Outer_Iter, Inner_Iter, Time(sec), rms[Rho..RhoE], RefForce, CD, CL, CSF, CMx, CMy, CMz, CFx, CFy, CFz, CEff`. Outputs: `flow.vtu`, `surface_flow.csv` (PointID, x, y, …), `restart_flow.dat`. |
| L5b on TEE's O-mesh, through the registry | 10,000 quads, first cell 5e-3 c, farfield 50 c: **CL 0.334478, CD 0.019922 (+1.8 % / −7.3 % against the official-mesh figure), 1,279 iterations, 6.8 orders, 80 s**, verdict converged, label `indicative`. An Euler O-mesh with y+-1 spacing converges ten times slower than the coarse unstructured official mesh — the first cell is a viscous instinct Euler does not want. `k_su2` = **6.1 µs per node-iteration**. |

### 3.3 OpenVSP 3.51.3 / VSPAERO 7.2.2

| Row | Finding |
|---|---|
| L7 package | `OpenVSP-3.51.3-Ubuntu-24.04_amd64.deb` 63.6 MB; dpkg's post-install exits 127 (package "half-configured") but `/opt/OpenVSP/{vsp,vspscript,vspaero,…}` and the `/usr/local/bin` links are installed and link cleanly. |
| L7 VLM facts | The solver needs a `.vspgeom`, which `VSPAEROComputeGeometry` writes **only with `GeomSet = SET_NONE` and `ThinGeomSet = SET_ALL`**; the enum `VSPAERO_ANALYSIS_METHOD::VORTEX_LATTICE` no longer exists in 3.51.3 scripts (VLM is the default); string + double concatenation in `Print` fails — the two-argument form works. |
| L7 the AR 10 wing, through the registry | `wt_case wing=` builds the wing in-line (214 tokens); `wt_sweep` α 0/2/4/6 at M 0.1, 4 threads: **~5 s**, polar of four rows, **CL_α 4.905 /rad** vs lifting line 5.19 (AR 10, e 0.95): −5.5 %; CDi at 6° 0.00882 vs CL²/(πeAR) 0.00880: +0.3 %; e 0.95–0.96. |
| L7 exit code | **`vspscript` exits 2 after a COMPLETE sweep** (DONE printed, `.polar/.lod/.history` written). The exit code is a claim; `vsp_result` treats the DONE line and the polar as the evidence and the run record says `exit_code_overruled`. |
| L8 the Python API | `/opt/OpenVSP/python/openvsp/openvsp/_vsp.so` depends on `libpython3.12`; `import openvsp` under the repo's 3.11 venv fails (`numpy._core.multiarray failed to import`). The script route stays primary; the API is recorded and banned from import. |

### 3.4 ParaView 5.11.2 (apt) + `python3-paraview`

| Row | Finding |
|---|---|
| L6 offscreen | `--force-offscreen-rendering` with no DISPLAY **segfaults** (`vtkXRenderWindowInteractor`); **`xvfb-run -a pvpython` renders** (a 1200 × 800 PNG in 3.3 s); **`PlotOverLine → CSV` works with no display and no xvfb** (2.4 s on the converged case; U 34.9 → 33.6 m/s half a chord above the section, physically sensible). |
| L6b through the registry | `wt_probe_field` 16 samples in 83 tokens (the samples inside the body come back `null` and `outside_mesh` counts them); `wt_view pressure` 88 tokens (path, size, colour range, caption — never pixels); `wt_export csv/md` 33 tokens each. |

### 3.5 The registry loop, token costs (measured through `app.registry.call`)

```
wt_probe 55   wt_conditions 58   wt_case create 181   wt_mesh 162   wt_run 97
wt_status 21 / 72 / 87 (before the first step / mid-run / with trend)
wt_result 163   wt_probe_field 83   wt_view 88   wt_export 33   wt_case adopt 183
SU2: wt_case 179   wt_mesh 99   result 148      VSPAERO: wt_case 214   wt_sweep 96   result 293
```

### 3.6 The kernel's own law, met head-on

With the QoS law on (the default) a 15 GB container refuses every job engine: *"cfd-solve needs
4 GB and the machine can never place it (−1 GB after the 16 GB reserve)"*. `TEE_MACHINE_TOTAL_GB`
declares capacity the way the kernel's own tests do; the setup doc says so. The lane never
routes around the ledger.

---

## 4. Prior art, and why none of it is imported

- **CfdOF** (FreeCAD workbench, LGPL-3): writes a standard OpenFOAM case with an `Allrun`/`Allmesh`
  and `cfMesh`/`snappyHexMesh`; TEE adopts the directory and parses the `runApplication` lines
  into an argv sequence of known binaries. It never runs the script.
- **foamlib / PyFoam / fluidfoam**: in-process dictionary readers, all GPL. TEE writes its own
  dictionaries (a strict serialiser subset) and reads by header.
- **pyvista / vtk**: the usual post-processing path; 600 MB. TEE writes pvpython scripts.
- **OpenVSP's Python API**: NOSA, pinned to one Python minor. TEE writes AngelScript.
- **SU2's `pysu2`**: not on PyPI; TEE writes a `.cfg` with the QuickStart's verified keys.

---

## 5. What this machine has, and what the owner's Mac will need

Container: OpenFOAM v2606 (`/usr/lib/openfoam/openfoam2606`), SU2 8.4.0 (unpacked into the
session scratchpad, reached through `SU2_RUN`), OpenVSP 3.51.3 (`/opt/OpenVSP`), ParaView 5.11.2
+ xvfb, no display, root, 15 GB.

Owner's Apple Silicon Mac (facts from the sources, not measured): `brew install
gerlero/openfoam/openfoam` installs **OpenFOAM-v2606.app** whose entry script is
`/Applications/OpenFOAM-v2606.app/Contents/Resources/etc/openfoam`; `engines.py` composes
`<entry> <app> args` for it. SU2 ships a macOS zip; OpenVSP ships ARM64 bundles pinned to
Python 3.11 or 3.13; ParaView ships an arm64 dmg whose `pvpython` takes
`--force-offscreen-rendering` without xvfb.

---

## 6. TEE reuse map

| Need | Reused | Where |
|---|---|---|
| lane skeleton, digest law | `pc_*` (A67) | `windtunnel/tools.py`, `case.digest` |
| binary discovery + loud refusal on a wrong explicit path | `capture/align.py` `_binary` | `windtunnel/engines.py` |
| jobs, ledger rows, register → submit → release-on-refusal | `capture/tools.py`, `kernel/jobs.py`, `kernel/machine.py` | `ENGINES["cfd-mesh" / "cfd-solve" / "aero-panel"]` |
| cancel that kills | **new**: `JobManager.submit(..., on_cancel=)` (12 lines, its own test) | `runner.SolverRun.terminate` |
| trust table | `_EXPLICIT` rows, no family row (the `cad_/trade_/pc_` lesson) | 13 rows |
| PDF export | `pdf_compose` through `app.registry.call` (trust and the pdf extra's refusal apply) | `report._export_pdf` |
| FreeCAD RPC | `FreeCADWire.py_json`, the one bridge | `cfdof.rpc_case_path` (lazy) |

---

## 7. Defects found by building, in the order they bit

1. **A 16-character key glued to its value** — `writeCompressionoff;`; simpleFoam refused it. The serialiser now pads every key by at least one space (tested).
2. **Aref of a 2-D slab** — coefficients 10× small until Aref = chord × thickness.
3. **O-mesh cells inverted** — clockwise quad node order; the CCW order is now a method with a positive-Jacobian test.
4. **The apt build's dead function objects** — the whole coefficient path moved to openfoam.com's package; `_foam_candidates` orders it first.
5. **`Cm ≈ 5e-4` broke the verdict** — the relative stationarity test on a near-zero moment flagged a converged run `insufficient` (8.97 %); `SCALE_FLOOR` (cl 0.1 / cd 0.01 / cm 0.01) makes the test relative above the floor and absolute below it → 0.53 %, `converged`.
6. **`shutil.move` into an existing directory nests** — the wing's `.vsp3` landed one level too deep and the sweep died; the empty target is removed first.
7. **Run ids restart per case** — the run registry was keyed by `run_001` alone; two cases collided. Keyed by `case/run` now.
8. **`wt_already_running` looked only at registered processes** — a second `wt_run` on a queued job was accepted; the job manager is now the evidence (`_live_job`).
9. **A refused submission left a phantom `queued` run** — marked `refused` now.
10. **vspscript exits 2 after success** — the exit code is a claim; the outputs are the evidence.
11. **Open MPI refuses root** — `mpi_env` for root and parallel only, recorded on the run.
12. **`checkMesh` in a directory without `system/`** — every mesh directory gets the three stub files (`write_mesh_system`).
13. **The tutorial's "upper triangular order"** — tolerated beside the TE skewness; anything else still needs `force=true`.
14. **lRef 1 on a 35 m section** — Cl 34. The chord is measured from the wall patch (`patch_bbox`), and the run record says where lRef came from.
15. **A double chord division** — `omesh_for` divided the first cell by the chord and `omesh` did it again; a 1 m chord never showed it, the chord-scaling test does.
16. **`wt_probe_field` on a vector** — s + three components + magnitude at 64 samples was 929 tokens; the magnitude alone is the default (components opt-in), and samples inside the body come back `null` via `vtkValidPointMask`.

---

## 8. P0 answers

| Row | Answer |
|---|---|
| L1 | bashrc route on Linux, entry script on the Mac app; apt 1912 cannot report a force → openfoam.com's package (§3.1) |
| L2 | `k_openfoam` 2.36 µs per cell-iteration per core; ~3 kB per cell; `confirm_above_s` 300 s; `cfd-solve` 4 GB floor |
| L3 | header-driven reader, golden transcribed from v2606, reorder + missing-column tests |
| L4 | `surfaceFeatureExtract` (.com name); `foamToVTK` not needed (pvpython reads the case); `mpirun` works with the root override; **`cores > 1` ships** (7.8 → 4.8 s on 4 cores) |
| L5 | `k_su2` 6.1 µs per node-iteration; history golden; D7 case 1 reference = the official-mesh run (CL 0.328486 / CD 0.021481), TEE's O-mesh +1.8 % / −7.3 % |
| L6 | `wt_view` fix names `xvfb-run` (Linux) or the EGL/OSMesa binary; `wt_probe_field` is render-free by design |
| L7 | `.vspscript` API names verified in the shipped scripts; polar golden; `k_panel` ~6 s a sweep; D7 case 2 inside the lifting-line band |
| L8 | the Python API is not importable from 3.11 — recorded, never used |
| L9 | gmsh not measured; out of scope v1 |
| L10 | 736 B / 119 B per iteration; a 64 KB tail suffices |
| L11 | cancel kills a real simpleFoam in 0.05 s; the partial rows read back labelled |
| L12 | not possible here (no local LLM) — open |
| L13 | the tutorial adopts, runs as-is, and reports forces once `forces=` adds the function object to the run copy with a measured chord |
| M1–M7 | **owner session** (the Mac): the entry-script route, v2606 goldens, SU2 arm64 vs Rosetta, ParaView 6.1.1 offscreen, OpenVSP ARM64 paths and its Python from the 3.11 / 3.13 venvs |
| C1–C3 | **owner session**: CfdOF's headless writer through the app's interpreter and the RPC route; what a CfdOF case contains. Until then CfdOF is "write with the GUI, adopt with TEE" — the adoption parser is tested on a CfdOF-shaped fixture |
| S1 | **owner session**: SimFlow's terms from a browser; dispositioned as not-integrable software, adoptable output |
| R1–R4 | R1 lifting line: a textbook formula (Anderson §5.3–5.4), verified as a formula; R2 the SU2 QuickStart figure: measured on the official mesh 2026-09-06 (the AGARD AR-211 cross-check still owed); R3 Dennis & Chang 1970 and R4 the NASA TMR flat plate: **not verified at source** — `wt_verify` refuses them by name |
| G1 | §2 |

---

## 9. Open questions

1. **The ledger is coarse.** One registered RANS job defers every LLM swap; L12 could not be measured here. Accounting is the point, so the lane registers anyway; the owner's Mac can measure the contention.
2. **R3 / R4** need a source visit before `cylinder_re40` and `flatplate` become tests.
3. **The Foundation dialect.** `wt_fork_unsupported` refuses a TEE-written case on OpenFOAM 11+; adopted Foundation cases run as-is. Measuring the Foundation's `momentumTransport` writer is a later phase.
4. **3-D SU2** needs gmsh (GPL, out of process) — v1 routes 3-D viscous work to OpenFOAM and lifting surfaces to VSPAERO.
5. **The GUI handoff** — `wt_open`, `.pvsm` state files, a Qt panel — is the later campaign the owner deferred; the case directory, the `.foam` stub and the `.vsp3` are exactly the files those GUIs open.
