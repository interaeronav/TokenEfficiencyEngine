# CLAUDE_A74_SCRIPT.md — cfMesh in the wind-tunnel lane

Plan of record for **A74**. Research doc **74** is the design of record; `docs/research/74-evidence/` holds what produced its numbers. Opened 2026-09-07 on the owner's instruction, after the answer to *"can you download and integrate helyx"* turned out to be *"no, and the part of it you want is already installed"*.

## Orientation for a cold session

The wind-tunnel lane (A72, `wt_*`) meshes 3-D bodies with **snappyHexMesh** and 2-D sections with its own structured O-mesh. snappy's weak point is measured, not folklore: on the lane's own prism it delivered **1.32 of 2 requested boundary layers, at 41.6 % of the requested thickness** (doc 74 §2.2, from snappy's own log table). That shortfall is the thing HELYX advertises against — and **cfMesh**, whose `cartesianMesh` creates layer cells on every boundary face by construction, is already inside the openfoam.com v2606 distribution this lane drives. Nothing to install, nothing to download, no new licence.

A72 already RUNS it: `cartesianMesh` is in `cfdof.KNOWN_BINARIES` and in the adopted-case mesh-step allowlist, so a case whose `Allrun` names it is meshed with it today. This campaign writes the other half — TEE composing a cfMesh case of its own.

Read first: doc 74 (all five sections), then `foam.py`'s `write_snappy_dicts`/`default_sequence` and `tools.py`'s `mesh()`. The dictionary keys are in doc 74 §2.5 and were read off a real v2606 file; do not invent one.

## Measured facts (2026-09-07, this container — build ON them)

1. **`cartesianMesh` needs the wrapper.** Direct: `error while loading shared libraries: libmeshLibrary.so`. Through `/usr/bin/openfoam2606 cartesianMesh`: it answers, announcing `(cfmesh)`, `Using: OpenFOAM-2606`, `Build: _481094f-20260618`. `foam.foam_argv()` already composes exactly that form.
2. **The comparison** (same prism, same domain, 2 layers asked): snappy **46,160 cells / 12.0 s / `Mesh OK` / skew 0.70 / layers 1.32 of 2 at 41.6 %**; cfMesh **37,960 cells / 1.6 s / skew 5.55 with twelve faces flagged (`checkMesh` FAILS) / aspect 4.93 / non-orth avg 2.65**.
3. **The first cfMesh run measured the wrong thing:** 630,980 cells in 17.1 s, because `boundaryCellSize` refines at the farfield too. `localRefinement { "body.*" { cellSize … } }` is the idiom. A dictionary key nearly inverted the campaign's conclusion.
4. **cfMesh meshes the volume bounded by a closed surface**, so external aero needs the domain box AND the body as one multi-solid STL (`solids: ['farfield', 'body']`, each solid becoming a patch). snappy's background `blockMesh` has no equivalent step.
5. **Licence: nothing new.** cfMesh is GPL, distributed inside OpenFOAM.com since v1806 — the same process, install and posture as every binary the lane already drives.
6. **The lane's gate would refuse it today.** `checkMesh` fails on skewness, and skew is one of the two `TOLERATED_CHECKS`, so a cfMesh mesh would run only under that tolerance. P3 is about earning a clean pass, not widening the tolerance.

## Prior art in this repo (copy these, do not reinvent)

- `foam.py` — the dictionary writers, `foam_argv()`, the header-driven readers, `write_mesh_system()` (the `system/` stubs `checkMesh` insists on).
- `tools.py::_Lane.mesh` — the snappy path: job submission, `checkMesh` parsing, `wt_mesh_unhealthy`, the `kind` field in the result.
- `airfoil.extrude_stl` / `physics.write_stl_ascii` — the body STL, and `write_stl_ascii(name=…)` is what makes a multi-solid file possible.
- `case.py` — the case record already carries `domain: {xmin … zmax}`; the box needs no new arithmetic.
- `fixtures_windtunnel.py` — `fake-foam/*` dispatches on `argv[0]`; a `cartesianMesh` arm goes there so P1 is hermetic.
- A72's `p0-measure.sh` and A73's `mac-check.sh` for the shape of an owner-session probe — **and for the trap both of them fell into**: `$?` after a pipe is the pipe's status, and a payload proving a call happened is not evidence it succeeded.

## Design of record (doc 74 carries the reasoning)

`wt_mesh` grows **`mesher="snappy" | "cfmesh" | "auto"`**. A `write_cfmesh_dicts()` sits beside the snappy writer in `foam.py`; a `domain_surface()` helper joins the case's box and body STL into one multi-solid surface; the runner, the job, the ledger row and the `checkMesh` gate are untouched. No new tool, no new engine row, no new capability, no change to the always-loaded surface.

## Phases

- **P0** — the measurements above, doc 74, this script, the DECISIONS ruling, `74-evidence/`. **Done 2026-09-07**; the evidence directory holds both arms' scripts and their output.
- **P1** — `write_cfmesh_dicts()`, `domain_surface()`, `mesher=` on `wt_mesh`, the fake `cartesianMesh` arm, hermetic tests per refusal. *Acceptance:* the whole path exercised with no real binary; byte-stable dictionaries; the surface's solids named and asserted; surface still 17 tools.
- **P2** — the `cfd` tier: mesh the prism both ways, then **solve on both and compare the forces**. **Done 2026-09-07** (doc 74 §2.7): the forces move — Cd −27.6 %, spurious lift 6× smaller, `converged` against `stalled` on the same budget — so the argument is earned and P4 has a measurement to route on.
- **P3** — the twelve skew faces at the trailing edge: `surfaceFeatureEdges` → FMS, `edgeMeshRefinement`. **Done 2026-09-07** (doc 74 §2.8): the FMS route at 30° takes max skewness 5.5497206 → 2.0995350 and `checkMesh` from FAILING to a clean pass, for 0.4 s and 1,584 fewer cells, with `TOLERATED_CHECKS` untouched. `edgeMeshRefinement` kills `cartesianMesh` (rc=1) and is not shipped. It also took the spurious lift from 0.01194 to **0.00004**.
- **P4** — `mesher="auto"` (the router's rule, from P2's numbers), the benchmark scenario, `docs/windtunnel-lane.md`, `docs/setup-windtunnel.md`, the CLAUDE.md bullet, CHANGELOG, PROGRESS, version. **Done 2026-09-07**: `auto` is the DEFAULT and picks cfMesh wherever the install carries it, saying so in the mesh row (`chose`); `wt_probe` reports `cfmesh` in the `openfoam` row; `wt_cfmesh_absent` refuses by name on a build without it. The benchmark batch is unmoved and was not re-run to pretend otherwise — its OpenFOAM arm is the 2-D O-mesh case, which no 3-D mesher touches. Shipped as **0.29.0** (0.26.0 was reserved for A74 and 0.28.0 cut for it; A76 pushed that number first, so the campaign took the next free one).
- **P5** — the 2-D route, on the owner's word after P4 closed: does `cartesian2DMesh` earn a place beside the lane's own O-mesh? **Done 2026-09-08** (doc 74 §2.9): **no, and measured**. Cd 0.0207 against the O-mesh's 0.0109 on the same case at α = 4°, and 0.0220 with a properly resolved boundary layer that costs more cells than the O-mesh — the gap widens as the cartesian mesh is refined toward it. A control on the SAME O-mesh rules out the near-wall model (low-Re and wall functions agree to four decimals). Two facts kept: the surface rule INVERTS (the 2-D mesher refuses a closed surface and wants a ribbon, open in z), and cfMesh assigns no patch types in either dimension — 3-D makes every solid a `wall`, 2-D makes every patch `empty`, and the caller owns them. No code shipped; nothing to version.

## Laws

1. **Nothing is installed and nothing is downloaded.** cfMesh is already here; if it is absent on a machine, `wt_mesh mesher=cfmesh` refuses by name and says the OpenFOAM install is the answer.
2. **The dictionary is read, never remembered** — doc 74 §2.5 keys came off a real file, and §2.3 is what guessing one costs.
3. **A better mesh must show up in the answer**, or the campaign closes with a measured "no".
4. **Never widen `TOLERATED_CHECKS` to make a mesh pass.** Fix the mesh or refuse the geometry.
5. **The caller's arguments do not change between meshers**, which is what makes `auto` honest.
6. Zero always-loaded tools; no new `wt_*` name; no family row.

## Outcome

**The campaign closed with a measured yes.** cfMesh meshes the lane's prism in 4.1 s against 11.1 s, in 36,768 cells against 46,160, converges where snappy stalls on the same 200-iteration budget, and leaves Cl **0.00004** where snappy leaves 0.07458 on a symmetric section at zero incidence. Law 3 asked whether a better mesh shows up in the answer; it shows up in the one number on the sheet whose true value is known.

Zero always-loaded tools added, no new `wt_*` name, no family row, no new engine, no new licence, `TOLERATED_CHECKS` untouched.

## Amendments learned while building (the script is amended, not improvised around)

- **P2 defect 1 — a patch is a solid.** The box went in as one `farfield` solid; the mesh was perfect and `simpleFoam` stopped at `Cannot find patchField entry for farfield`, because every `0/` field names blockMesh's patches. `physics.box_faces()` writes the box as inlet/outlet/sides/top/ground, verified by computing each normal rather than trusting the face order.
- **P2 defect 2 — cfMesh is not reproducible when threaded.** Same case, two runs, same 38,352 cells, different mesh hashes (`7c26…`, `cc2a…`); `OMP_NUM_THREADS=1` gives `c5fa…` twice for ~25 % more wall time. The lane pins the single-threaded route because the mesh hash travels with every coefficient and same-mesh deltas are first-class, and `cores` is how a caller buys the speed back — with the loss named in the reply. It reaches the answer: spurious Cl wandered 0.0013 → 0.0093 threaded, then repeated at 0.011943 / 0.011940 pinned.
- **P2 fake correction.** Real `cartesianMesh` gives EVERY patch made from a solid `type wall`, the farfield included — read out of the `polyMesh/boundary` it wrote. The fake had been inventing the tidier `patch`/`wall` split, and a fake kinder than the tool it stands in for is how a lane ships a defect that only appears on real engines.
- **P3 amendment — the feature angle is not a caller argument.** The plan said "`surfaceFeatureEdges` → FMS, `edgeMeshRefinement`" without saying who chooses the angle. Law 5 answers it: snappy's own `includedAngle 150` is the same criterion from the other end (180 − 150 = 30) and is not an argument either, so 30° is a constant of the lane (`runs.FEATURE_ANGLE_DEG`), reported in the mesh row because it changes the mesh. 45° was measured too and is worse.
- **P3 amendment — the same threading lesson, in the probe this time.** The first four-variant table was measured threaded and its 45° row moved between runs (2.2391098 → 2.6517441). P2 had already pinned the LANE; the evidence script had not been pinned with it. Both are now, and every row of `74-evidence/p3-2026-09-07.log` repeats exactly.

- **P4 amendment — the `auto` rule does not hedge, because hedging was unmeasured.** The obvious rule was "a body that is not watertight goes to snappy", cfMesh needing a closed surface. It was measured instead of assumed: a four-triangle hole and then a hole several cells across, both meshers, same case. Both closed the hole, both stayed `checkMesh`-clean, cfMesh's cell count barely moved (36,768 → 36,863). With no arm of the campaign measuring snappy ahead on a 3-D body, a watertightness branch would have been exactly the guess-with-a-name the script's own comment warns about. The one branch that IS measured is whether `cartesianMesh` exists on the machine.
- **P4 amendment — the probe reads three answers by key.** cfMesh detection rides along in the OpenFOAM version probe rather than adding a process. The old reader was positional, and `command -v mpirun` prints NOTHING on a machine without MPI: a third question would have been read as the second. Keys now.

- **P4 defect, found by CI — a hermetic suite is only hermetic on the machine you ran it on.** One assertion in `test_windtunnel_cfmesh.py` called the OpenFOAM finder with an EMPTY config, which searches the real install locations. It passed on this container (v2606 present) and failed on the runner (none), in the file whose own docstring reads *"the cfMesh writer, with no cfMesh"*. The finder takes a config for exactly this reason: the fixtures' fake install is one argument away. `test_server_lint.py` now fails any hermetic test that calls `find_*({})` or `probe({})` **without blinding the machine first** — the one legitimate shape, which `test_windtunnel_readers.py` already uses to assert the absent-engine refusal, and which the first draft of the guard flagged as a defect. The failure was reproduced locally before the fix was trusted: blind `_foam_candidates()` and `shutil.which` and this container raises CI's error verbatim.
- **And the machine-reading line had been hiding a second defect.** With the assertion pointed at the FIXTURE, it failed again: `_without_cfmesh(tmp_path)` laid its fakes out in the same directory the `app` fixture uses and then deleted `cartesianMesh` from it — gutting the install the first app was still using. Nobody could see it while the last assertion was reading the real v2606 instead. It gets its own directory now. A test that passes for the wrong reason is not a passing test; it is a covered-up one.

- **P2 threshold lesson.** The symmetry test was first written `abs(cl) < 0.01`, from the first threaded run's 0.0013. With the mesh pinned the true figure is 0.0119, so the original bound had been measuring whichever run happened to be luckiest. The assertion is now a ratio against snappy's 0.0746, with a loose absolute band as a nonsense guard.

