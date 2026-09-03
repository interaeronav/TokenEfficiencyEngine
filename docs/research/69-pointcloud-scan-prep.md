# 69 — Point-cloud scan prep: turning a raw scan into a scale-checked tracing template (2026-09-03)

Research of record for **A67** (`pc_*`). Every licence claim below was fetched from PyPI on
2026-09-03 (URLs inline); everything tagged `measured 2026-09-03` was executed on this Mac in
`server/.venv` (Python 3.11.15, numpy 2.4.6, scipy 1.17.1). Claims carried from earlier TEE
research are marked `(doc NN)`. The probe scripts that produced the numbers are reproduced in
§7 so any of this can be re-run rather than believed.

---

## 1. What the module is for, and what already exists

A room scan is 3–15 M XYZ triples. No amount of model intelligence helps, because the useful
answer is always a summary — "the floor is 2.3° off level", "that wall reads 4.017 m against
your 4.000 m tape". Points stay on disk under a `cloud_id`; every tool returns a digest.

TEE already owns the back half of this pipeline. `capture_*` (A42, all phases CLOSED) does
ingest, reconstruction, ICP registration onto the design datum, C2M deviation and the owner
decision menu. `pc_*` is the missing **front** half, and the gap is specific:

1. **No binary point-cloud reader exists in this repo.** `capture/tools.py:303` maps ODM's
   `odm_georeferenced_model.laz` as an artifact the lane *produces and never opens*. The only
   cloud parsing anywhere is ASCII, at `capture/deviate.py:57`.
2. **Nothing consumes the tape measurements.** `docs/okongo-capture-protocol.md` §1/§4 sends
   the owner to site with a DISTO and tells them to record inter-marker and wall-to-wall
   distances. No code reads them. A42 T6 is the cost of that: 7-DOF ICP on unreferenced video
   **collapsed** (scale → 0, RMS 15 µm, 1.17 M points in a 0.5 mm blob), and the honest fix was
   to prescale from the *design envelope* (×6.12) because no measured length was available.
   `pc_control_*` is that missing input.
3. **No RANSAC, no plane fitting, no in-process normal estimation** exist anywhere in the repo.
   The closest is `extract/frames.py:163` `fit_similarity` — 2D Umeyama, least-squares, **no
   outlier rejection**.

So the design rule for the whole phase: **reuse the back half, build only the front half.**
`pc_*` ships no ICP; registration stays `capture/align.py:86 register_icp()`, which already
carries a refusing RMS gate and a 7-DOF degeneracy guard.

---

## 2. The licence audit — one banned dependency, two dropped on weight

Fetched from `https://pypi.org/pypi/<name>/json`, 2026-09-03.

| Package | Version | Licence (verified) | Verdict |
|---|---|---|---|
| `laspy` | 2.7.0 | `BSD-2-Clause` (license_expression) | **ADOPT** — LAS/LAZ |
| `lazrs` | 0.8.2 | `MIT` (license_expression) | **ADOPT** — LAZ codec |
| `trimesh` | 5.1.0 | MIT | **ADOPT** — PLY; already installed |
| `ezdxf` | 1.4.4 | MIT (doc 18) | **ADOPT** — already in `[extract]` |
| `scipy` | 1.17.1 | BSD-3 | **ADOPT, and DECLARE** — see §2.1 |
| `plyfile` | 1.1.5 | **GPL-3.0-or-later** — classifier `License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)` | **BANNED** |
| `pye57` | 0.4.19 | MIT | **DROPPED** (not a licence problem) |
| `open3d` | 0.19.0 | MIT | **DROPPED** (not a licence problem) |

**`plyfile` is the finding that matters.** The A67 script's dependency table listed it as a
core dependency. TEE is MIT. This repo already established the fact (doc 43, PyPI-verified),
already banned it (`voxkiln/src/voxkiln/license_lint.py:20`), and already performed vendor
surgery to excise it from the TRELLIS.2 fork — doc 43's own recorded replacement is *"replace
`.ply` IO with trimesh or drop"*. That is exactly what this lane does. Re-verified
independently 2026-09-03 rather than carried on trust, because a dependency table that is
trusted once is trusted forever.

The two drops are **not** licence calls and the doc must not imply they are:

- **`pye57`** is MIT, but it builds `libE57Format`. CloudCompare 2.13.2 is already a lane
  dependency and ships `libQE57_IO_PLUGIN` (`measured 2026-09-03`, plugin present in
  `/Applications/CloudCompare.app/Contents/PlugIns/ccPlugins/`), so E57 is one conversion away
  and refuses honestly when CloudCompare is absent.
- **`open3d`** is MIT, ~400 MB, and would be pulled in for ICP alone — and there *is* no ICP
  here (§1). `server/tests/test_a46_no_heavy_imports.py` bans precisely this shape
  (`vtkmodules` 592 MB, `torch` 505 MB, `OCP` 225 MB). Adding a 400 MB dependency for a
  function the repo already has would invert A46's whole finding.

### 2.1 `scipy` is present by accident

`measured 2026-09-03`: `scipy 1.17.1` imports in `server/.venv` and `cKDTree` works — but
`scipy` appears **nowhere** in `server/pyproject.toml`. It arrives transitively (skfolio /
PyPortfolioOpt / scenedetect). `cKDTree` is load-bearing for normal estimation, so a clean
`uv sync` that dropped one of those carriers would silently break the lane. It is therefore
declared explicitly in the new `pointcloud` extra. This is the same class of defect as the
memory note *"TEE upgrades wipe the fleet extras"*.

---

## 3. Format facts — `measured 2026-09-03` unless noted

### 3.1 PLY through trimesh, and the georeferencing trap

trimesh writes `property float x/y/z` — **float32, in both binary and ascii encodings**. On a
local cloud that is harmless (max error 0.238 µm against float64 truth, versus 12 mm of scanner
noise). On a georeferenced cloud it is fatal, because float32 resolution is `|coord| · 2⁻²³`:

```
float32 PLY export error vs the cloud's absolute coordinates
                    origin        max err   verdict
             local (0,0,0)       0.000 mm   OK
            site-local ENU       0.004 mm   OK
        UTM 33S Okongo-ish     249.991 mm   DESTROYS THE MEASUREMENT
                      ECEF     249.995 mm   DESTROYS THE MEASUREMENT

resolution = |coord| * 2^-23:  at 100 m -> 0.012 mm
                               at  10 km -> 1.192 mm
                               at   1 Mm -> 119.209 mm
```

This is not hypothetical: ODM's `odm_georeferenced_model.laz` — the artifact §1 says the
capture lane already produces — is georeferenced by construction.

> **Law for the lane: PLY export is ALWAYS origin-shifted, and the offset is recorded in the
> sidecar.** A `pc_export` to PLY that does not subtract the centroid is a silent 250 mm error.
> LAS is immune: it stores int32 ordinates against a float64 header offset.

Timings: write 200 K points 0.006 s, read 0.001 s, 2.4 MB binary (6.7 MB ascii). Loads back as
`trimesh.PointCloud`; colours round-trip as RGBA `(N, 4)`.

### 3.2 LAS/LAZ through laspy — and why the conventional scale is wrong here

LAS stores each ordinate as `int32 · scale + offset`. The quantisation error is half a scale
unit, and **the file size does not change with scale** — the ordinates are int32 either way:

```
scale     max err     addressable span    file size (200 K pts)
0.01      5.0000 mm   +-21,474,836 m      6,800,375 B
0.001     0.5000 mm   +- 2,147,484 m      6,800,375 B
0.0001    0.0500 mm   +-   214,748 m      6,800,375 B
0.00001   0.0050 mm   +-    21,475 m      6,800,375 B
```

The industry-conventional `0.001` costs **0.5 mm** of quantisation — a quarter of the ±2 mm
budget in acceptance A4, spent for nothing. `0.0001` costs 0.05 mm and still addresses ±214 km,
which is four orders of magnitude more than any building.

> **Law for the lane: default LAS scale is `1e-4`, not the conventional `1e-3`.** Finer
> precision here is literally free, and the tolerance budget is not.

Other measured LAS facts: `point_format=3` + `version="1.4"` carries XYZ + RGB + intensity;
colours survive a round trip when scaled by 257 (LAS RGB is `uint16`); `intensity` is `uint16`
and survives exactly; LAZ via `lazrs` is **lossless** (`np.array_equal` true against the LAS
ordinates) at **2.62×** compression, 0.011 s write / 0.015 s read for 200 K points;
`laspy.open(path).header` reads the count and bbox **without loading points**, and
`chunk_iterator(n)` streams — so a 15 M-point scan never needs 15 M points of RAM.
`header.parse_crs()` returns `None` for a header written without a CRS, so a missing SRS is
detectable rather than silently assumed.

### 3.3 DXF units

`measured 2026-09-03`, confirming doc 18's table: `ezdxf.units.M` → `$INSUNITS = 6`;
`ezdxf.units.MM` → `$INSUNITS = 4`. The lane writes **metres / 6**, because the cloud is in
metres and a template traced at the wrong scale is worse than no template (acceptance A6).
Note the divergence from `partkiln/src/partkiln/sheetmetal/flat.py:618`, which writes mm / 4 —
correct for sheet metal, wrong here; the unit follows the domain, not the repo.

### 3.4 The scanner app is not assumed

The A67 script's "PLY/LAS/E57 as **3D Scanner App** actually writes them" names no particular
product — it is a generalisation for *whatever iPhone scanning app produced the export*
(owner, 2026-09-03). That is the stronger requirement, not the weaker one: with no app
specified, the lane may not hard-code any app's quirks, so `pc_open` reads the header of the
file it is given and **reports the writer, SRS and point format it finds**.

For context on what such an export tends to contain, the field protocol
(`docs/okongo-capture-protocol.md` §3) sends the operator out with **Polycam / RealityScan
Mobile**, and `knowledge-base/25_.../02_reference-and-scanning.md` records Polycam Basic
exporting *"point clouds (PLY, LAS, PTS, XYZ, DXF)"* — KB prose, so `confidence: low` and not
grounding on its own. Neither is wired into the reader. Real header quirks get recorded here
when a real export lands (see §8).

---

## 4. The algorithms, measured against the synthetic fixture

The A67 script's appendix fixture, `seed=7`, generates **279,352 points** (`measured`, matching
its stated "~280K"): a 4.000 × 3.000 × 2.700 m interior-faces box at 15 mm sampling with 12 mm
Gaussian noise, then corrupted by 2.3°/1.1° tilt, 37° yaw, a translation and a ×1.004 scale.

### 4.1 Levelling

RANSAC a near-horizontal plane (`|n_z| > 0.95`), refit least-squares (SVD) on the inliers,
rotate the normal to +Z, drop the floor to z = 0.

> **Floor and ceiling are equally dominant.** In a box room both horizontal planes have
> identical point counts, so "the plane with the most inliers" is a coin flip. The tie-break is
> **lowest median z among planes above the inlier threshold** — not inlier count alone.

`measured`: residual tilt **0.0000°** (gate ≤ 0.05°), floor-plane RMS **11.4 mm** against 12 mm
injected — both exactly reproducing the script's own reference run.

### 4.2 Yaw — the script's premise was right, but only in 3D

The script hoped a normal-histogram would beat 0.1° and told the build to keep PCA and record
why if it did not. It does beat it — but the first honest implementation *failed badly*, and
the reason is the useful finding:

```
estimator                                          yaw        error
3D normals, k=160, wall band 0.4-2.3 m         36.996 deg    0.004 deg
3D normals, k= 80                                  --        0.040 deg
3D normals, k= 40                                  --        0.068 deg
3D normals, k= 20                                  --        0.073 deg
2D PCA, same full wall band                    36.927 deg    0.073 deg
2D PCA, 50 mm slice at z = 1.2 m               35.711 deg    1.289 deg   <-- FAILS the 0.5 gate
2D normals (XY neighbourhoods), k=12           10.650 deg   26.350 deg   <-- collapses
```

Two rules fall out:

> **Normals must be estimated in 3D, not in the XY projection.** With 12 mm noise on a 15 mm
> grid, a 2D neighbourhood is isotropic noise with no line in it: a planarity filter kept **6 of
> 40,000** neighbourhoods and the estimate collapsed to 26° of error. In 3D the wall *is* a
> plane, and k ≥ 80 averages the noise down.

> **Yaw comes from the full-height wall band, never from the slice.** A 50 mm slice blows the
> ±0.5° gate by 2.6×. Yaw and section are different queries over different point sets; sharing
> an estimator between them would look like a tidy simplification and would be wrong.

For the record, the script's cited PCA reference (0.225°) is beatable at 0.073° simply by
running PCA over the whole band rather than a thin one — so the band, not the estimator, was
most of that error.

### 4.3 Slice and scale

`measured`, at z = 1.2 m, 50 mm band, orthogonal line fit: **4 segments**, interior
**4.0161 × 3.0105 m** against the fixture's scaled truth 4.0160 × 3.0120 — **+0.1 mm and
−1.5 mm** (gate ±5 mm). One 4.000 m tape baseline then yields factor **0.99598** against the
true correction 0.99602 — a **32 ppm** residual (gate 500 ppm; the script's reference run was
235 ppm) — and applying it lands **4.0000 × 2.9984 m**, i.e. **+0.00 / −1.62 mm** (gate ±2 mm).

> **Report fit residual as median and RMS, not max.** `measured`: per-segment *max* residual is
> **56–57 mm** — arithmetically correct (≈4.7σ of a 12 mm noise floor over thousands of points)
> and completely misleading to a reader. The max is reported, but labelled; the quality signal
> is the median.

Whole level + yaw pass: **0.24 s on 279,352 points**, single-threaded numpy + one `cKDTree`.

---

## 5. What this machine has

`measured 2026-09-03`.

| Thing | Fact |
|---|---|
| CloudCompare | **2.13.2**, `/Applications/CloudCompare.app/Contents/MacOS/CloudCompare` (not on PATH) |
| CC plugins present | `libQLAS_IO`, `libQE57_IO`, `libQPCL_IO`, `libQDRACO_IO`, `libQRANSAC_SD`, `libQHOUGH_NORMALS`, `libQCSF`, `libQM3C2`, `libQFACETS` |
| `server/.venv` | Python 3.11.15; numpy 2.4.6, scipy 1.17.1, ezdxf 1.4.4, trimesh 5.1.0, laspy 2.7.0, lazrs 0.8.2 |
| Always-loaded surface | 17 tools, ~2,033 tok (`test_server_lint.py`, `benchmarks/run_benchmarks.py:738`) |
| Virtual tools before A67 | 143 |
| Real scan fixture | **none in the repo** — no `.ply`/`.las`/`.laz`/`.e57` anywhere; `testbeds/` does not exist |

That CloudCompare already carries LAS, E57, RANSAC-shape-detection and Hough-normals plugins is
why §2 can drop `pye57` without losing a format, and it is worth remembering before anyone adds
a dependency for a cloud operation: check the plugin list first.

---

## 6. TEE-side reuse map

| Need | Already here — do not rebuild |
|---|---|
| ICP + refusing RMS gate + 7-DOF degeneracy guard | `server/src/tee/capture/align.py:86` `register_icp()` |
| External-binary lookup with a loud refusal naming the install | `capture/align.py:43` `_binary()` |
| Frames, site datum, similarity fit, the 2 % units-conflict rule | `extract/frames.py:163` `fit_similarity`, `scale_conflict` (doc 18) |
| Wall/plan schema — centreline `a`/`b` + thickness, metres | `extract/plan.py` `tee-plan/1` (doc A10) |
| Content-addressed store, `derived_dir(hash, lane)` | `extract/store.py:249` |
| SVG sheet composition (title block, scale bar, panels) | `boards.py` `board_compose` |
| Error shape `TeeError(code, message, fix=…)` | `kernel/errors.py` |
| Response budgeting (handlers never call it themselves) | `server.py:150`, `kernel/budget.py` |
| Accuracy ladder, tolerance bands, USIBD LOA | doc 18 §"Conformance tolerance bands" |

New code is therefore confined to: binary cloud I/O, RANSAC plane/line fitting, 3D normal
estimation, the control-baseline solver, and a native `ezdxf` writer inside `server/src/tee`
(none exists — the only DXF writers live in `partkiln`, `seamkiln` and the FreeCAD/OpenSCAD
bridges).

---

## 7. Reproducing the numbers

The probes live in the phase's scratch and are reproduced in `server/tests/fixtures_pointcloud.py`
(the fixture generator) and `server/tests/test_pointcloud_*.py` (every algorithm number in §4).
The format numbers in §3 come from a standalone script whose three sections are: a PLY/LAS/LAZ
round trip at 200 K points; a LAS scale sweep over `1e-2 … 1e-5`; and the float32 origin sweep
over local / ENU / UTM / ECEF. Any claim in this document that is not reproducible by running
those is a defect in this document.

---

## 7b. The first real scan (2026-09-03) — and what it broke

`measured 2026-09-03` on the owner's `test scan.zip` (Okongo Oneleiwa Dropbox).

**What the archive actually is.** Not a point-cloud export: a raw 3D Scanner App
2.5 capture from an `iPhone18,2` on iOS 26.6 — 1,827 frames of depth map +
confidence map + `cameraPoseARFrame`, 305 RGB frames, and one already-fused
`points.ply` of **1,520,736 coloured points** with normals. The fused cloud is
the usable input; the per-frame depth is a back-projection lane this phase does
not have and did not need. ARKit is Y-up and gravity-aligned, so `pc_open`'s
`up_axis="y"` is the whole conversion.

**The lane held up.** `pc_open` read 1.52 M ASCII-PLY points in 3.0 s for 89
tokens; `pc_level` recovered the floor at **0.0000° residual with a 12.3 mm
plane RMS over 129,247 floor points** and removed an 88.667° wall azimuth; the
z-histogram gave a textbook room signature (floor spike at 0.00, ceiling spike
at 2.60, flat wall returns between). Nine calls over a 1.5 M-point cloud cost
**506 tokens** end to end.

**The line fitter did not.** `fit_lines` returned **35 segments totalling 133 m
of wall inside a 5 x 5 m room** — 4 m diagonals run through a bed and a
wardrobe, and the same partition found six times. The synthetic fixture had
hidden every one of these failures, because one clean rectangle has no wall
thickness, no second room, no doorway and no furniture. RANSAC scores a
candidate on inlier count alone, and in a cluttered room a long diagonal catches
plenty of points by chance.

Three guards were added, each an architectural fact rather than a tuned number:

1. **A wall is continuous.** Runs are split at gaps over 350 mm — which is also
   the correct treatment of a doorway — and a run must fill at least 65% of the
   100 mm bins along its own length.
2. **A surface found twice is one surface.** Near-coincident parallel runs
   (within 80 mm) are merged, best-supported first. Wall THICKNESS survives:
   the two faces of a 260 mm partition are 260 mm apart, not 80.
3. **`fit="ortho"`, a new and explicit mode.** After `pc_level` has removed the
   azimuth, every wall in a rectilinear building is axis-parallel, so walls are
   found as **spikes in the histogram of perpendicular offsets** — which is what
   a flat vertical surface actually is — and a diagonal never becomes a
   candidate at all. It is a declaration by the caller, not an assumption by the
   lane: it would be wrong for splayed or curved walls.

Result on the same scan: **133 m -> 42.9 m** with the guards, and **20 clean
axis-parallel surfaces totalling 30.7 m** with `fit="ortho"`. Both are now
pinned by `server/tests/test_pointcloud_fit.py` against a two-room fixture that
has the thickness, doorway and clutter the first one lacked.

**The honest limit of the output.** No tape measurement was supplied, so
`pc_report` returned **UNVERIFIED — "scale is the scanner's word alone"**, which
is exactly right and is the single thing standing between these drawings and a
buildable dimension. Two wall-to-wall tape readings would close it.

## 8. Open questions

1. **ANSWERED 2026-09-03 for geometry, still open for scale.** A real capture arrived
   (§7b) and the lane ran on it end to end. What it did NOT bring is tape measurements, so
   `pc_control_*` — the part of the lane that exists precisely because A42 T6 had no measured
   length — is still unexercised on real data, and every real dimension the lane has produced
   is UNVERIFIED. Two wall-to-wall readings would close this.
2. **Which app produced any given export is deliberately not a question this lane asks.** The
   brief's "3D Scanner App" is a generalisation, so there is no app to special-case; `pc_open`
   reports the writer it reads. This becomes an open question only if some real export turns
   out to need handling the generic reader cannot give it.
3. **Should slice segments become `tee-plan/1` facts?** It would light up `ex_export_ifc` and
   `bl_build_from_plan` for free. Deliberately **out of scope for A67**: the segments are
   geometry, and calling them walls is exactly the interpretation the phase's non-goal #1
   forbids. It needs a decision record, not a quiet addition.
