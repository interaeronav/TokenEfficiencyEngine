# The wind-tunnel lane (`wt_*`)

Runs OpenFOAM, SU2 and OpenVSP/VSPAERO from one budgeted loop, reads the
answer back through ParaView's `pvpython` — and the model never sees a cell.

Design of record: `docs/research/72-wind-tunnel-lane.md`. Plan of record:
`CLAUDE_A72_SCRIPT.md`. Install: `docs/setup-windtunnel.md`.

## What it is for

A CFD case is a directory of dictionaries, a mesh of ten thousand to ten
million cells, a solver log that grows 736 bytes per iteration and a
coefficient file that grows one row per step. None of that belongs in a
model's context. The useful answer is always a summary — *Cl 0.436, Cd 0.0109,
converged in 197 iterations, comparative not absolute* — so the case stays on
disk under a `case_id`, every long solve is a job, and every tool returns a
digest: no array over 64 elements, no string over 2 KB, and every number
travels with its engine, version, mesh hash, convergence verdict and
uncertainty label.

The whole loop below costs about **2,800 tokens** on the benchmark batch
(a swept wing plus a solved section). Reading what a model must otherwise read
— the dictionaries, three tails of the log, the coefficient file, the checkMesh
report, the script and the polar — costs **19,100**, and grows with every
iteration.

## Install

```bash
cd server && uv sync --extra windtunnel      # meshio + numpy, used by wt_export format=vtu only
```

The engines are separate installs and separate processes (OpenFOAM GPL-3, SU2
LGPL-2.1, OpenVSP NOSA-1.3, ParaView BSD-3); `docs/setup-windtunnel.md` has
the per-platform lines and `wt_probe` names whatever is missing with its
install line. The lane downloads nothing.

## The loop

```
wt_probe → wt_conditions → wt_case (create | adopt) → wt_mesh → wt_run / wt_sweep
                                                                     ↓ tee_job
                              wt_export ← wt_view ← wt_probe_field ← wt_result ← wt_status
```

1. **`wt_probe`** — which engines this machine has, by version probe. An absent
   engine comes back with its install line, size and the date it was verified.
2. **`wt_conditions`** — ISA atmosphere at an altitude, then Reynolds number,
   Mach and dynamic pressure for a speed OR a Mach number and a reference length.
3. **`wt_case action=create`** — from `naca="2412"`, a Selig `dat=`, an `stl=`
   body (a `pk_export format=stl` part works), a `wing={span, root_chord, …}`
   built by OpenVSP, or a `geom=` from `wt_geom`. The fidelity ladder picks the
   cheapest capable engine and **says why**: panel (VSPAERO, seconds) → Euler
   (SU2, minutes) → RANS (OpenFOAM below Mach 0.3, SU2 above). Override with
   `fidelity=`; the label will say `not-predictive` if the ladder disagrees.
4. **`wt_case action=adopt path=`** — a standard OpenFOAM case directory (CfdOF,
   a tutorial, a hand-made case), an SU2 `.cfg` with its mesh beside it, or an
   OpenVSP `.vsp3`. Copied, never mutated; its `Allrun` is parsed for the
   binaries it names and never executed.
5. **`wt_mesh`** — a structured O-mesh for a 2-D section (seconds, written as
   OpenFOAM `polyMesh` or SU2 `.su2` by TEE itself) or `blockMesh` +
   `snappyHexMesh` around a 3-D body (a job). Returns the checkMesh digest.
6. **`wt_run`** — the solve, as a job: poll `tee_job`, watch `wt_status`,
   `tee_job action=cancel` **kills the solver** (a real simpleFoam was gone in
   0.05 s). Above the measured cost threshold it asks once for
   `confirm_cost=true` with the estimate. `cores=` runs in parallel.
7. **`wt_status`** — where the run is in a few dozen tokens: iteration, last
   residuals, last lift/drag with trend, ETA — and `orphan` if the server was
   restarted under a live solver (`wt_case action=stop` kills it after checking
   the pid still runs that case).
8. **`wt_result`** — Cl, Cd, Cm, L/D with the verdict (`converged`, `stalled`,
   `oscillating`, `diverged`, `insufficient`, `cancelled`) and the uncertainty
   label (`comparative`, `indicative`, `not-predictive`, each with its citation).
   `compare_to=` gives same-mesh deltas in drag counts. A diverged run refuses
   to quote a number; `allow_partial=true` returns the last finite values,
   labelled.
9. **`wt_sweep`** — an angle-of-attack list as ONE job: a VSPAERO polar in
   seconds, or sequential OpenFOAM/SU2 runs. At most 64 points.
10. **`wt_probe_field`** — numbers from the flow: a line of at most 64 samples
    (velocity magnitude by default, `components=true` for x/y/z), or the
    statistics of a field on a slice, through `pvpython` with no rendering.
    Samples inside the body come back `null`.
11. **`wt_view`** — `pressure | velocity | cp | mesh | residuals` rendered to a
    PNG on disk, returning its path, size and colour range, never pixels. Look
    at it with `tee_media` if you must.
12. **`wt_export`** — `json | csv | md | pdf | foam | vtu | pipeline`. The PDF
    goes through the pdf lane; `.foam` is the stub ParaView opens; `vtu` needs
    the extra.
13. **`wt_verify`** — the validation battery against references verified at
    their source: `wing_liftslope` (lifting line, a textbook formula) and
    `naca0012_euler` (the SU2 QuickStart figure measured on its official mesh)
    run; `cylinder_re40` and `flatplate` refuse until their references have been
    checked at source.

## Handing a case to a window (A73)

```
wt_open case_id=wt_1a2b3c4d5e                    # writes the state, prints the command
wt_open case_id=wt_1a2b3c4d5e launch=true        # ... and opens ParaView here
wt_open case_id=wt_1a2b3c4d5e app=openvsp        # the .vsp3 instead
```

It always prepares and only sometimes opens. What it writes is a ParaView state
file beside what it opens, in one of two kinds: `full` carries a coloured
surface, a scalar bar and a camera and needs a display to WRITE (a render view
without one segfaults); `pipeline` is the reader alone, an eighth of the size,
and writes anywhere. Omit `kind` to take the best the machine can do and read
back which it wrote; ask for `full` where nothing can render and it refuses
rather than downgrading you silently.

Either kind opens the case at its **last time step** — the solution, not the
initial field. That took a second measurement to get right: `SaveState` carries
the animation scene's time and not the view's, so a state that set only the
view reloaded at t=0, coloured and framed exactly like the answer (doc 73
§2.10).

A case with only a mesh can be opened — that is the point of looking before you
solve — and `view=mesh` is the preset for it. The panel over the same lane is
`docs/windtunnel-gui.md`.

## Rules that bite

- **A declaration is a claim; a measurement is evidence.** `vspscript` exits 2
  after a complete sweep, so the polar and its DONE line decide, not the exit
  code. An adopted case's chord is measured from its wall patch, not assumed:
  `lRef = 1` on the apt tutorial's 35 m section returned Cl 34.
- **No bare coefficient.** Every result carries `engine`, `engine_version`,
  `mesh_hash`, `verdict` and `uncertainty`. RANS on attached cruise flow is
  trustworthy for deltas on the same mesh to a few drag counts and is
  ±1–3 % absolute at best (the Drag Prediction Workshops); separated flow,
  buffet and CLmax are `not-predictive`.
- **The verdict has a floor.** A relative stationarity test on Cm ≈ 5e-4 is
  meaningless, so below 0.1 (Cl), 0.01 (Cd, Cm) the test is absolute:
  one drag count of scatter is quiet, one is not.
- **A mesh checkMesh flags needs `force=true`**, except the two failures a
  solver runs through: a few skewed faces on a sharp trailing-edge seam, and
  "faces not in upper triangular order".
- **An adopted case runs as-is.** Its own solver, its own dictionaries, its own
  dialect. If it integrates no forces, the run reports a residual-only verdict;
  `forces={"patches": ["walls"]}` adds a `forceCoeffs` entry to TEE's run copy
  (never to the adopted copy, never to the source).
- **One live run per case.** A second `wt_run` names the job that is live.
- **TEE never grants itself.** The engines are found in `[windtunnel]` config,
  the known install locations, then PATH; a wrong explicit path refuses loudly.

## Refusals you will meet

| code | when | fix it names |
|---|---|---|
| `wt_openfoam_missing`, `wt_su2_missing`, `wt_openvsp_missing`, `wt_pvpython_missing` | an engine is absent | the install line, size, date |
| `wt_bad_config` | `[windtunnel]` names a path that is not the engine | fix the path or drop the key |
| `wt_fork_unsupported` | a TEE-written case on a Foundation OpenFOAM | install openfoam.com's build, or adopt a case written for it |
| `wt_cost_confirmation_required` | estimate > 300 s, > 8 GB or > 2 M cells | `confirm_cost=true`, with the estimate |
| `wt_already_running` | a live run on the case | wait, cancel, or `wt_case action=stop` |
| `wt_mesh_unhealthy` | checkMesh failed something the solver would not survive | re-mesh, or `force=true` |
| `wt_diverged` | the residuals climbed back or a coefficient went non-finite | the usual three causes; `allow_partial=true` |
| `wt_solver_failed` | the solver exited with an error | its last lines and the log path |
| `wt_blockage` | a body fills more than 10 % of the tunnel cross-section | the domain or `refs=` |
| `wt_reference_unverified` | a verification case whose reference is not yet checked at source | the source to visit |
| `wt_render_failed` | `pvpython` cannot render here | `xvfb-run`, or ParaView's EGL/OSMesa binary |
| `wt_extra_missing` | `format=vtu` without the extra | `uv sync --extra windtunnel` |
| `wt_no_display` | `wt_open launch=true` where no window can open, or a state with a view where nothing can render | the command to run where you are sitting, or `kind=pipeline` |
| `wt_paraview_missing` | the state is written but the application is absent | the install, and the state's own path |
| `wt_no_geometry` | `wt_open app=openvsp` on a case with no `.vsp3` | `wt_geom` |

## Licences

OpenFOAM (GPL-3), SU2 (LGPL-2.1), OpenVSP/VSPAERO (NASA Open Source Agreement
1.3) and gmsh (GPL-2+) are separate processes, never imported, never vendored;
ParaView (BSD-3) is driven through `pvpython`, never a `vtk` import. `foamlib`
(GPL-3.0-only), `PyFoam`, `fluidfoam`, `vtk`, `pyvista` and the OpenVSP Python
bundle are banned by `server/tests/test_windtunnel_licences.py`. The only
in-process helpers are `meshio` (MIT) and numpy, inside the optional extra and
reached by one function. No tutorial case is copied into the tree.

## Measured (2026-09-06, Linux container, 4 cores; the Mac rows are an owner-session checklist in the script)

| what | number |
|---|---|
| NACA 0012, 16,000-cell O-mesh, simpleFoam kOmegaSST, 30 m/s, 4° | 197 iterations, 17 s through the registry; Cl 0.4356, Cd 0.0109 |
| the same on 1 / 2 / 4 cores | 7.8 / 6.8 / 4.8 s of solver time |
| cancel mid-run | the pid gone 0.05 s after `tee_job cancel` |
| SU2 Euler NACA 0012, M 0.8, 1.25°, TEE's 10,000-quad O-mesh | 1,279 iterations, 80 s; CL +1.8 % / CD −7.3 % against the QuickStart figure on its official mesh |
| VSPAERO AR 10 wing, four angles | ~5 s; CL_α 4.905 /rad, −5.5 % from lifting line |
| the apt `airFoil2D` tutorial, adopted | 313 iterations, 4.8 s; Cl 0.970 at 8° once the chord (35.05 m) is measured from the mesh |
| token cost per call | probe 55 · case 181 · mesh 162 · run 97 · status 21–87 · result 163 · probe_field 83 · view 88 · export 33 |
| the benchmark batch (fakes) | TEE 2,796 tokens / 15 calls vs naive 19,145 / 16: 85 % saved |

## What it does not do

No renderer of its own: `wt_open` hands the case to ParaView or OpenVSP and the
panel shows numbers, because ParaView is the viewer (A67). No FreeCAD/CfdOF
handoff — declined for A73, so a CfdOF case is still adopted headlessly rather
than opened. No adjoint or shape optimisation, no 3-D SU2 meshing (gmsh), no
transient, multiphase or compressible OpenFOAM, no downloads, no Windows.
SimFlow is not integrable as software; a case it writes is adoptable.
