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

The Cl row decides it. The section is symmetric and the incidence is zero, so **lift must be zero**: every count of it is the mesh's asymmetry rather than the flow's. Neither mesher reaches zero at this refinement, and cfMesh leaves six times less of a quantity that should not exist. The convergence difference is the same story from the solver's side — the same case, budget and settings converged on one mesh and stalled on the other, which is why the verdict machinery hands back `comparative` for one and `indicative` for the other.

**What is NOT claimed.** Cd has no reference here, so −27.6 % is a difference, not an improvement; this is one geometry at one refinement; and a 0.012 spurious Cl is still not zero. What A74 law 3 asked was whether the forces move at all, and they move by more than any mesh-convergence band would excuse.

## 3. Why the design is shaped this way

**`wt_mesh` grows a `mesher=` argument; nothing else moves.** The tool already takes `base_cell_m`, `levels` and `layers`; it gains `mesher="snappy" | "cfmesh" | "auto"`, and a `meshDict` writer sits beside the `snappyHexMeshDict` writer in `foam.py`. No new tool, no new engine row, no new capability tier — the always-loaded surface is untouched, and `wt_mesh` is already `call-engine`.

**The domain surface is built, not asked for.** The case record already carries the box (`domain: {xmin … zmax}`) and the geometry already carries the body STL. A `domain_surface()` helper writes the box as a named solid and concatenates, so the caller's arguments do not change between meshers — which is what makes `mesher="auto"` honest.

**The skewness failure is the campaign's blocker, not a footnote.** The lane's own gate (`TOLERATED_CHECKS`) treats skew as one of two tolerated `checkMesh` failures, so a cfMesh mesh would run today only under that tolerance. Twelve faces at the sharp trailing edge is a specific, addressable defect — cfMesh's own answer is feature edges (`surfaceFeatureEdges` → an FMS surface, `edgeMeshRefinement`) — and P3 exists to fix it rather than to tolerate it.

**A better mesh has to show up in the answer.** The acceptance that decides this campaign is not cell counts: it is the same case solved on both meshes with the forces compared. A mesh that covers its boundary layer and does not move Cd has not earned a `mesher=` argument.

## 4. What this campaign does not do

- **No new engine.** cfMesh is OpenFOAM's own binary, run the way the lane runs the rest.
- **No HELYX.** Customer-only, no macOS build; the disposition is recorded in `docs/DECISIONS.md` the way SimFlow's was.
- **No HiSA, no FreeCAD/CfdOF.** HiSA is a source build under an unusual licence for code (reportedly CC-BY-SA 3.0, to be read at its own `LICENSE` before any row is written); CfdOF was declined for A73 and stays declined here. Both are named in §5 as candidates, not scope.
- **No 2-D route yet.** `cartesian2DMesh` exists and the lane's 2-D path is a structured O-mesh that snappy never touches, so there is nothing to compare against; deferred.

## 5. Open questions

1. **Does the trailing-edge skewness survive feature edges?** The twelve faces are the campaign's one measured defect. If `surfaceFeatureEdges` + FMS does not clear them, the honest outcome is `mesher="cfmesh"` shipping with a documented refusal for sharp sections rather than a silent tolerance.
2. ~~**Does the layer coverage move the forces?**~~ **Answered (§2.7): yes.** Cd by −27.6 %, spurious lift by 6×, and the verdict from `stalled` to `converged` on the same budget. The campaign does not close with a "no"; P4's router has a measurement to route on.
3. **Is cfMesh in the Mac's v2606 bundle too?** The same openfoam.com distribution should carry it, but that is an assumption until `wt_probe` reports it there — one line in the owner's session.
4. **HiSA's licence**, at its own repository rather than at a search result, before it is ever named as an option in a refusal.
