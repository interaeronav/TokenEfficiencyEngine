# 74-evidence — what produced the numbers in research doc 74

Measured 2026-09-07 in the Linux build container (Ubuntu 24.04 x86_64, 4 cores,
no display) against **OpenFOAM v2606 from openfoam.com**, whose distribution
carries cfMesh. Nothing here is an upstream file: the two scripts are TEE's own
probes, and the log is their output transcribed from runs TEE made.

| file | what |
|---|---|
| `snappy-arm.py` | builds the prism through `airfoil.extrude_stl`, creates the case through `wt_case`, meshes it through `wt_mesh` (the lane exactly as it ships), and reads the layer table out of `log.snappyHexMesh` |
| `cfmesh-arm.py` | writes the domain box and the body as ONE multi-solid STL, writes a `meshDict`, and runs `cartesianMesh` then `checkMesh` through the `openfoam2606` wrapper |
| `p0-2026-09-07.log` | both arms' numbers, and the two facts about the binary: it needs the wrapper, and it announces itself as `(cfmesh)` |
| `p3-features.py` | P3: the same case meshed from the plain STL, from the FMS `surfaceFeatureEdges` writes at 30 and at 45 degrees, and with `edgeMeshRefinement` added - each twice, single-threaded |
| `p3-determinism.py` | P3: the FMS route meshed twice under `OMP_NUM_THREADS=1`, hashing `constant/polyMesh` each time |
| `p3-2026-09-07.log` | both P3 scripts' output: the failing check, the clean one, the key that kills `cartesianMesh`, and the hash repeating |

The headline the campaign exists for is in the layer table: snappy asked for two
layers on the body and got **1.32 of them at 41.6 % of the requested
thickness**, while cfMesh creates layer cells on every boundary face by
construction and reports no shortfall because coverage is not in question there.
The headline against it is one line lower: cfMesh's mesh **fails `checkMesh` on
skewness** (5.55, twelve faces) where snappy's passes at 0.70.

`cfmesh-arm.py` is kept in the state that produced BOTH cfMesh rows: the global
`boundaryCellSize` of the first run refines at the farfield walls and cost
630,980 cells, and `localRefinement` on `"body.*"` is what the 37,960-cell row
used. The wrong idiom is evidence too - it is the difference between measuring
cfMesh and measuring my first guess at its dictionary.

The log is banner-filtered the way A72's is: `cartesianMesh` prints
`Using: OpenFOAM-2606 (2606) - visit www.openfoam.com` and the URL is stripped
in the transcription, because the licence gate bans upstream banner strings in
committed evidence. It caught this file on the first run after the gate was
widened to scan every `*-evidence` directory instead of only `72-evidence` —
which is the cheapest possible demonstration that the widening was worth doing.

The two `.py` probes are kept exactly as they were RUN, not tidied to pass
`ruff` (nothing lints `docs/`, and A72's evidence scripts are the same). A
script edited after the fact is no longer the thing that produced the numbers.

