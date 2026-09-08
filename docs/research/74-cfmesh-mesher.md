# 74 — cfMesh in the wind-tunnel lane: TEE writes for the mesher it already runs

Design of record for **A74** (`CLAUDE_A74_SCRIPT.md` is the plan). Written 2026-09-07. Every number below was measured in this container on that date, or read at a primary source; nothing here is remembered.

## 1. What is being opened, and what it extends

The owner asked whether HELYX could be downloaded and integrated. It cannot: ENGYS' own FAQ says *"No. HELYX and ELEMENTS are only available to paying customers"*, the installers sit behind a customer portal, and there is no macOS build — so the machine that runs this lane's OpenFOAM could not run it anyway. The owner's answer to that was *"FIND an analogue alternative"*, and the analogue to the part of HELYX that matters here — `helyxHexMesh`, whose selling point is guaranteed boundary-layer coverage — turned out to be **already installed**: cfMesh ships inside the openfoam.com distribution the lane already drives.

A72 already runs it. `cartesianMesh` is in `cfdof.KNOWN_BINARIES` and in the adopted-case mesh-step allowlist (`tools.py`), so a case whose `Allrun` names it is meshed with it today. What A74 adds is the other half: **TEE writing a cfMesh case of its own**, the way it writes a `snappyHexMeshDict` now. The campaign is therefore not "add a mesher" but "write for the mesher we already run".

## 2. The measured facts

### 2.1 It is present, and it needs the wrapper

```
$ cartesianMesh -help
cartesianMesh: error while loading shared libraries: libmeshLibrary.so

$ /usr/bin/openfoam2606 cartesianMesh -help
(cfmesh)
Takes a triangulated surface and generates a cartesian mesh
Using: OpenFOAM-2606 (2606) - visit www.openfoam.com
Build: _481094f-20260618
```

The v2606 install carries 313 binaries including `cartesianMesh`, `cartesian2DMesh`, `tetMesh`, `pMesh`, `surfaceFeatureEdges`, `FMSToSurface` and `FMSToVTK`. The direct call fails because the OpenFOAM environment is not sourced; the wrapper form is the one `foam.foam_argv()` already composes for every other application, so the lane's existing invocation machinery reaches cfMesh unchanged. It advertises `-case`, `-parallel` and `-decomposeParDict` — the flags the runner already passes.

### 2.2 The comparison the campaign rests on

One geometry (NACA 0012, 24-point section, chord 0.3 m, span 0.4 m, 192 triangles), one domain (the lane's own 5/15/5-chord box, blockage 0.081 %), two layers requested on the body:

| | snappyHexMesh (the lane today) | cfMesh `cartesianMesh` |
|---|---:|---:|
| cells | 46,160 | **37,960** (−18 %) |
| mesh wall time | 12.0 s | **1.6 s** (7.5×) |
| `checkMesh` | **Mesh OK** | ✗ **fails on skewness** |
| max aspect ratio | 9.48 | **4.93** |
| max non-orthogonality | **44.2** (avg 5.14) | 52.0 (avg **2.65**) |
| max skewness | **0.70** | 5.55, twelve faces flagged |

and the row the campaign exists for, from snappy's own log:

```
patch faces        layers        overall thickness
              target   mesh     [m]       [%]
body  160      2        1.32     0.0129    41.6
```

**Two layers asked for, 1.32 achieved, 41.6 % of the requested thickness.** cfMesh publishes no equivalent number because it does not have the same problem: it creates layer cells on every boundary face first (`Adding 99484 cells to the mesh`) and refines the named patches afterwards (`Number of newly generated cells 300`). That is what "guaranteed coverage" means mechanically, and it is the whole of HELYX's meshing claim reproduced with a binary that is already on the disk.

### 2.3 The first run measured the wrong thing, and that is a fact about the dictionary

The first cfMesh arm produced **630,980 cells in 17.1 s** — worse than snappy on every count. The cause was `boundaryCellSize`, which refines at *every* boundary including the farfield box. `localRefinement { "body.*" { cellSize 0.0375; } }` is the idiom that refines only the body, and it is what the 37,960-cell row used. Recorded because the campaign's own P0 nearly concluded the opposite of the truth on a dictionary key.

### 2.4 The structural difference: cfMesh meshes a closed surface

snappyHexMesh carves a body out of a background `blockMesh`. cfMesh meshes **the volume bounded by the surface it is given**, so an external-aero case needs the domain box and the body as ONE watertight multi-solid surface:

```
domain.stl 37916 B, solids: ['farfield', 'body']
```

Each `solid` becomes a patch, which is how `"body.*"` in `localRefinement` and `patchBoundaryLayers` finds its target. This is the real work of the campaign: the lane already writes a body STL and already computes the domain box, but nothing today joins them into one surface.

### 2.5 The dictionary, from a real file

Keys verified against `tutorials/incompressible/adjointOptimisationFoam/.../system/meshDict` in the v2606 install (read for its shape, never copied — no GPL tutorial is vendored, A72 law 5):

`maxCellSize`, `surfaceFile`, `boundaryCellSize`, `boundaryCellSizeRefinementThickness`, and

```
boundaryLayers { patchBoundaryLayers { "<patch regex>" { nLayers; thicknessRatio; } } }
```

plus `localRefinement { "<patch regex>" { cellSize; } }`, which §2.3 shows is the one that matters for external aero.

### 2.6 Licence: nothing changes

cfMesh is GPL and has been distributed inside OpenFOAM.com since v1806. It is the same separate process, from the same install, under the same licence as every other binary this lane drives — so A72's law 5 ("copyleft at arm's length, nothing downloaded, nothing vendored") is satisfied by doing nothing new. There is no install step, no download, and no new row in the licence gate beyond naming it.

### 2.7 What solving on both meshes found (P2, 2026-09-07)

The campaign's acceptance, and it produced two defects before it produced a number.

**A patch is a solid.** The first attempt meshed perfectly and stopped the solver dead:

```
--> FOAM FATAL IO ERROR: Cannot find patchField entry for farfield
file: 0/p/boundaryField
```

The box had gone in as one solid named `farfield`, while every `0/` field this lane writes names blockMesh's patches. A valid mesh nothing could solve on. `physics.box_faces()` now writes the box as five solids under **blockMesh's own names** — inlet, outlet, sides, top, ground — so one set of boundary conditions serves both meshers. The mapping was fixed by computing every normal, not by reading the face order: all twelve outward, `sides` being the two y-walls as a single patch.

**cfMesh threads itself, and threaded it is not reproducible.** The same case meshed twice:

| | run 1 | run 2 | cells |
|---|---|---|---|
| `cartesianMesh`, threaded (default) | `7c260615fd23772e` | `cc2a2a95b348336a` | 38,352 both |
| `cartesianMesh`, `OMP_NUM_THREADS=1` | `c5fa100c6f08f733` | `c5fa100c6f08f733` | 38,352 both |
| `snappyHexMesh` | `b0b9f5b5b90059d8` | `b0b9f5b5b90059d8` | 46,160 both |

Two of this lane's laws need a mesh that can be identified: the mesh hash travels with every coefficient (A72 law 2), and same-mesh deltas are the first-class claim (law 3). Neither survives a mesher that answers differently each time it is asked — so `wt_mesh mesher=cfmesh` pins `OMP_NUM_THREADS=1`, costing about 25 % of a few seconds (3.4 s against 2.7 s, still 3× faster than snappy's 11 s), and `cores` is how a caller buys the speed back with the loss stated in the reply.

It shows up in the answer, which is why it matters rather than being tidiness: the spurious lift wandered 0.0013 → 0.0093 across threaded runs and then repeated to five decimals — **0.011943, 0.011940** — once the mesh was pinned.

**The comparison, on the prism at α = 0, 200 iterations, same domain and layers:**

| | snappyHexMesh | cfMesh |
|---|---:|---:|
| cells | 46,160 | 38,352 |
| mesh wall | 10.8 s | **3.7 s** |
| verdict | **stalled** (2.03 orders, at the 200-iteration cap) | **converged** (5.01 orders in 196) |
| uncertainty label | `indicative` | **`comparative`** |
| Cd | 0.43435 | 0.31464 (−27.6 %) |
| **Cl** | **0.07458** | **0.01194** |

The Cl row decides it (and P3 pushes it a further two orders — §2.8). The section is symmetric and the incidence is zero, so **lift must be zero**: every count of it is the mesh's asymmetry rather than the flow's. Neither mesher reaches zero at this refinement, and cfMesh leaves six times less of a quantity that should not exist. The convergence difference is the same story from the solver's side — the same case, budget and settings converged on one mesh and stalled on the other, which is why the verdict machinery hands back `comparative` for one and `indicative` for the other.

**What is NOT claimed.** Cd has no reference here, so −27.6 % is a difference, not an improvement; this is one geometry at one refinement; and a 0.012 spurious Cl is still not zero. What A74 law 3 asked was whether the forces move at all, and they move by more than any mesh-convergence band would excuse.

### 2.8 The twelve skew faces, and what cleared them (P3, 2026-09-07)

§2.2's one measured defect: from a plain STL, `cartesianMesh` rounds the NACA 0012's sharp trailing edge off into skew cells and `checkMesh` **fails**. cfMesh's own answer is to be told where the edges are — `surfaceFeatureEdges` rewrites the surface as an **FMS** carrying its feature edges, and the mesher then respects them. Four variants of the same case, all else equal (prism, 0.15 m base cell, 0.0375 m body cell, 2 layers), each meshed twice under `OMP_NUM_THREADS=1`, every row repeating exactly (`74-evidence/p3-2026-09-07.log`):

| surface | cells | max skewness | max aspect | `checkMesh` | mesh wall |
|---|---:|---:|---:|---|---:|
| plain STL | 38,352 | 5.5497206 | 4.95 | **FAILS** — 12 highly skew faces | 2.3 s |
| **FMS, `-angle 30`** | **36,768** | **2.0995350** | 5.31 | **passes clean** | 2.5 s + 0.4 s |
| FMS + `edgeMeshRefinement` | — | — | — | `cartesianMesh` **rc=1**, "FOAM exiting" | — |
| FMS, `-angle 45` | 36,768 | 2.2391098 | 4.74 | passes clean | 2.6 s + 0.4 s |

The feature step **costs 0.4 s and 1,584 fewer cells** and turns a failing check into a clean one. 30° is not a round number picked for looking round: 45° also passes and is measurably worse. It is also the same criterion the snappy route already uses from the other end — `surfaceFeatureExtract`'s `includedAngle 150`, and 180 − 150 = 30 — which is why the angle is a constant of the lane rather than a new caller argument (A74 law 5). Max aspect ratio goes slightly the other way (4.95 → 5.31) and is not flagged by `checkMesh` at either value; the honest reading is that the trailing-edge cells got thinner as they got straighter.

**And it did something P3 was not looking for.** Solved through the lane at α = 0, 200 iterations, the same comparison §2.7 ran:

| | §2.7 (plain STL) | P3 (feature edges) |
|---|---:|---:|
| cells | 38,352 | 36,768 |
| Cd | 0.31464 | 0.30757 |
| **Cl** (must be zero) | **0.01194** | **0.00004** |

A trailing edge the mesher rounds off asymmetrically is lift that is not there. Against snappy's 0.07458 the feature-edge mesh leaves about **1/1900th** of a quantity a symmetric section at zero incidence cannot have. That is one geometry at one refinement and it is not a claim about Cd, which still has no reference here — but it is the clearest form of A74 law 3's question, and the answer got stronger, not weaker, when the mesh was fixed for an unrelated reason.

**`edgeMeshRefinement` is not shipped.** cfMesh's own key for refining along those edges killed `cartesianMesh` with rc=1 on the very case the feature edges had just fixed, both times it was tried. The clean pass was already earned without it, so the campaign takes the pass and records the failure rather than debugging a key it does not need.

**What had to be checked, because P2 had already been bitten by it once.** An FMS is a different file format, and a format that lost the patch names would mesh perfectly and then stop `simpleFoam` dead at `Cannot find patchField entry`. It does not: the FMS names its patches in a block at the top — `6 ( inlet empty outlet empty … body empty )`, the type token being cfMesh's own — and the `constant/polyMesh/boundary` that comes out carries the same six patches, all `type wall`, exactly as from the plain STL. The live test asserts that rather than trusting it, and the fake `surfaceFeatureEdges` reproduces the format so the hermetic tier can catch a regression too.

**Reproducibility survives.** The FMS itself is byte-identical across invocations (`6fa708223fc52de48f5b2ea53b5c41742587873ce6cbad8c2ff08fba902a760a`, including one run through `-case` from a different working directory), and the mesh built from it repeats: `d766b634f6f0a6bb` twice under `OMP_NUM_THREADS=1`.

**The lesson P2 taught, learned twice.** The first version of the table above was measured **threaded**, and its 45° row moved between runs — 2.2391098, then 2.6517441 — which would have made "30 beats 45" a claim about whichever run was luckiest. P2 had already recorded that a threaded cfMesh builds a different mesh each time and pinned the lane accordingly; the probe script had not been pinned with it. It is now (`74-evidence/p3-features.py`), and the pinned 45° figure is the original 2.2391098.

**The acceptance, stated plainly.** `TOLERATED_CHECKS` was not touched. Skew is one of the two failures the lane tolerates, so a cfMesh mesh would have *run* either way — which is precisely why buying the pass with a widened tolerance would have been the wrong answer (A74 law 4). The mesh was fixed instead.

### 2.9 The 2-D route, measured and declined (P5, 2026-09-08)

§4 deferred `cartesian2DMesh` because the lane's 2-D path is TEE's own structured O-mesh and there was nothing to compare against. P5 built the comparison. The answer is a **measured no** — and the two facts it turned up on the way are worth more than the verdict.

**The surface rule INVERTS.** `cartesianMesh` meshes the volume bounded by a **closed** surface (§2.4). `cartesian2DMesh` refuses one. Four closed variants — the cell size a divisor of the domain and not, the cell larger than the slab and equal to it — all died in under a second with the same message:

```
--> FOAM FATAL ERROR: There are no cells in the mesh!
The reasons for this can be fwofold:
1. Inadequate mesh resolution.
2. You maxCellSize is a multiplier of the domain length...
```

Neither reason it names was the reason. What it wants is the 2-D outline **extruded without caps** — a ribbon, open in z — and it supplies the single cell through the thickness itself, inventing `bottomEmptyFaces` and `topEmptyFaces` to close it. Given that, the same case meshes in 1.6 s. The error message would have sent a reader to the cell size for as long as they cared to look.

**It writes every patch `empty`.** Not just the two it invents — `farfield` and `airfoil` too, and `checkMesh` then answers:

```
***Total number of faces on empty patches is not divisible by the number of
   cells in the mesh. Hence this mesh is not 1D or 2D.
```

Rewrite the two real ones (`airfoil` → `wall`, `farfield` → `patch`) and the same mesh is `Mesh OK`. This is the exact mirror of §2.7's finding that the 3-D mesher makes **every** solid-derived patch `type wall`, the farfield included. Stated once for both: **cfMesh does not assign patch types; the caller owns them.**

**The comparison** — NACA 0012, chord 1 m, 30 m/s, α = 4°, kOmegaSST, both solved here rather than quoted:

| | O-mesh (the lane's own) | cartesian, 8 layers | cartesian, 30 layers |
|---|---:|---:|---:|
| cells | 16,000 | 10,032 | 16,456 |
| mesh wall | 1.6 s | 1.5 s | 1.8 s |
| solve wall | 10.5 s | 3.9 s | 7.9 s |
| `checkMesh` | OK | OK (skew 2.56, aspect 25.9) | OK (skew 2.91, aspect 891) |
| Cl | 0.435564 | 0.427203 | 0.418769 |
| **Cd** | **0.010913** | **0.020697 (+90 %)** | **0.021972 (+101 %)** |

Cl agrees within 2–4 %. **Cd roughly doubles**, and giving the cartesian mesh a properly resolved boundary layer — 30 layers, more cells than the O-mesh, aspect ratio 891 — made it *worse*, not better. The gap does not close; it widens as the mesh is refined toward the thing it is being compared with.

**The near-wall model is not the cause, and that is a measurement rather than an argument.** The two arms differed in two ways at once: the mesh, and the wall treatment (the lane's 2-D path is low-Re by design). So the same O-mesh was solved both ways:

| | Cl | Cd |
|---|---:|---:|
| O-mesh, `low_re` | 0.436168 | 0.010896 |
| O-mesh, `wall_function` | 0.436157 | 0.010897 |

Identical to four decimals — on a y+ ≈ 1 mesh the wall functions degrade to the low-Re limit. One variable moved, and it was the mesh.

**Verdict, under A74 law 3.** A better mesh must show up in the answer. This one shows up in the answer as *worse drag on a case the lane already answers well*, for no saving that matters: the O-mesh costs 1.6 s and no external process, needs no ribbon surface, no patch-type rewrite, and is body-fitted at the wall where drag is decided. The 2-D route is **declined**, and this section is why rather than a shrug.

**What is NOT claimed.** No external reference was checked for Cd on this geometry, so "worse" means *disagrees with the lane's own verified O-mesh path by 90 %*, in the direction a coarse near-wall cell predicts, not *wrong against a wind tunnel*. One geometry, one incidence, one refinement family. And the finding is about **external aero on a thin section**: a cartesian 2-D mesh has obvious uses this case cannot speak for.

**A slip worth keeping.** The first run of that control read `Aref` from a guessed 1.0 m slab where the case record says 0.1 m, and every coefficient came out exactly 10× too small. Exactly 10× is what a guessed constant looks like, and the record was one `case.json` away.

## 3. Why the design is shaped this way

**`wt_mesh` grows a `mesher=` argument; nothing else moves.** The tool already takes `base_cell_m`, `levels` and `layers`; it gains `mesher="snappy" | "cfmesh" | "auto"`, and a `meshDict` writer sits beside the `snappyHexMeshDict` writer in `foam.py`. No new tool, no new engine row, no new capability tier — the always-loaded surface is untouched, and `wt_mesh` is already `call-engine`.

**The domain surface is built, not asked for.** The case record already carries the box (`domain: {xmin … zmax}`) and the geometry already carries the body STL. A `domain_surface()` helper writes the box as a named solid and concatenates, so the caller's arguments do not change between meshers — which is what makes `mesher="auto"` honest.

**The skewness failure was the campaign's blocker, not a footnote.** The lane's own gate (`TOLERATED_CHECKS`) treats skew as one of two tolerated `checkMesh` failures, so a cfMesh mesh would have run under that tolerance rather than on its merits. Twelve faces at the sharp trailing edge was a specific, addressable defect, and P3 fixed it with cfMesh's own answer — `surfaceFeatureEdges` → an FMS surface (§2.8) — rather than tolerating it. `feature_angle` is not a caller argument for the same reason `includedAngle` is not one on the snappy route: it is a property of the lane, not of the question being asked.

**A better mesh has to show up in the answer.** The acceptance that decides this campaign is not cell counts: it is the same case solved on both meshes with the forces compared. A mesh that covers its boundary layer and does not move Cd has not earned a `mesher=` argument.

## 4. What this campaign does not do

- **No new engine.** cfMesh is OpenFOAM's own binary, run the way the lane runs the rest.
- **No HELYX.** Customer-only, no macOS build; the disposition is recorded in `docs/DECISIONS.md` the way SimFlow's was.
- **No HiSA, no FreeCAD/CfdOF.** HiSA is a source build under an unusual licence for code (reportedly CC-BY-SA 3.0, to be read at its own `LICENSE` before any row is written); CfdOF was declined for A73 and stays declined here. Both are named in §5 as candidates, not scope.
- **No 2-D route.** `cartesian2DMesh` exists and the lane's 2-D path is a structured O-mesh that snappy never touches. P5 built the comparison rather than leaving it deferred, and **declined the route on the numbers** (§2.9): Cd roughly doubles against the O-mesh on the lane's own case, and refining the cartesian mesh toward the O-mesh's resolution widens the gap instead of closing it.

## 5. Open questions

1. ~~**Does the trailing-edge skewness survive feature edges?**~~ **Answered (§2.8): no, they clear it.** `surfaceFeatureEdges -angle 30` → FMS takes max skewness from 5.5497206 to 2.0995350 and `checkMesh` from FAILING to a clean pass, for 0.4 s. No refusal is needed and no tolerance was widened. `edgeMeshRefinement`, the other half of the plan, kills `cartesianMesh` and is not shipped.
2. ~~**Does the layer coverage move the forces?**~~ **Answered (§2.7): yes.** Cd by −27.6 %, spurious lift by 6×, and the verdict from `stalled` to `converged` on the same budget. The campaign does not close with a "no"; P4's router has a measurement to route on.
3. **Is cfMesh in the Mac's v2606 bundle too?** The same openfoam.com distribution should carry it, but that is an assumption until `wt_probe` reports it there — one line in the owner's session.
4. **HiSA's licence**, at its own repository rather than at a search result, before it is ever named as an option in a refusal.
5. ~~**Is the 2-D `cartesian2DMesh` route worth having?**~~ **Answered (§2.9): no.** Cd roughly doubles against the lane's own O-mesh on the same case, and refining the cartesian mesh toward the O-mesh's near-wall resolution widens the gap rather than closing it. The route is declined; the two facts it taught (the inverted surface rule, and that cfMesh assigns no patch types in either dimension) are kept.
