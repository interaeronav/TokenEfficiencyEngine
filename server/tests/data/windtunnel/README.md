# Wind-tunnel reader goldens

Every file here was TRANSCRIBED from a run TEE made on the real engine on
2026-09-06 (research doc 70 §3): the header row is verbatim, the data rows are
shortened or rounded. No tutorial, example or upstream file is copied into
this directory - OpenFOAM's tutorials are GPL-3 and SU2's are LGPL-2.1, and
`test_windtunnel_licences.py` scans this directory for their banners.

| file | engine | what the reader keys on |
|---|---|---|
| `coefficient_v2606.dat` | OpenFOAM v2606 `forceCoeffs` | the `# Time Cd Cd(f) ... Cs(r)` header line |
| `history_su2_840.csv` | SU2 8.4.0 with `HISTORY_OUTPUT=(ITER, WALL_TIME, RMS_RES, AERO_COEFF)` | the quoted CSV header (its first line, so no banner line inside) |
| `wing_ar10.polar` | VSPAERO 7.2.2 via OpenVSP 3.51.3 | the `Beta Mach AoA ... E ...` header row |
