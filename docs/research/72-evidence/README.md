# 72-evidence — what produced the numbers in research doc 72

Every file here was produced in the Linux build container on 2026-09-06
(Ubuntu 24.04.4 x86_64, 4 cores, 15 GB, root, no display) with OpenFOAM v2606
from dl.openfoam.com, SU2 8.4.0 linux64, OpenVSP 3.51.3 and ParaView 5.11.2 +
xvfb. Nothing here is an upstream file: the logs are pytest and TEE output, the
scripts are TEE's own drivers, and `test_windtunnel_licences.py` scans this
directory for OpenFOAM / SU2 / gmsh file banners.

| file | what |
|---|---|
| `p0-rows.json` | the P0 measurement table, one key per row (L1–L13, plus the registry-loop token costs and the ledger law) |
| `cfd-tier-2026-09-06.log` | `pytest -m cfd tests/test_windtunnel_live.py`: 9 passed in 3:46 on the real engines |
| `L4-parallel.log` | 1 / 2 / 4 cores on the 16,000-cell case after the root-MPI override (7.8 / 6.8 / 4.8 s) |
| `L11-cancel-L13-adopt-first-pass.log` | the first pass: parallel dying under Open MPI's root refusal, a real cancel in 0.05 s, the tutorial refused on "upper triangular order" |
| `L13-adopt-with-measured-chord.log` | the apt airFoil2D tutorial adopted and run with `forces=` once the chord is measured from the wall patch (Cl 0.970 at 8°) |
| `smoke_registry.py` | the first end-to-end loop through the registry on the real engines |
| `p0-measure.sh` | the P0b Mac measurement script (script §M): probes every engine where the Mac installs put it, runs the L2/L4/L5/L7/L13 rows on the Mac engines with `RUN_SOLVES=1`, and writes a banner-filtered `p0b-mac-<date>.log` here for the commit; prints, never asserts |
| `l2_tunnel.py`, `l5_su2_omesh.py`, `l4_only.py`, `l13_forces.py` | the P0 drivers (run from `server/` with `uv run --no-sync python`) |
