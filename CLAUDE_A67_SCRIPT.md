# CLAUDE_A67_SCRIPT.md — Phase A67: `pc_*` point-cloud scan prep

**Status: P0–P7 COMPLETE (2026-09-03).** Design of record:
`docs/research/69-pointcloud-scan-prep.md`. User guide: `docs/pointcloud-lane.md`.
Amendments go in `docs/DECISIONS.md`, not inline here.

**Goal:** a headless `pc_*` module that turns a raw scan into scale-verified,
axis-aligned 2D tracing templates (DXF/SVG) and a decimated cloud for handoff —
while the model never sees a single point.

---

## Why this belongs in TEE

A point cloud is the purest case of the problem TEE exists to solve. One room
scan is 3–15 million XYZ triples: dumping any of it into context is instant
budget death, and no amount of model intelligence helps, because the useful
answer is always a *summary*. This is principle **P1 (diffs over dumps)**
applied to the largest payload TEE will ever touch.

**And the gap was specific, not speculative.** TEE already had the back half of
reality capture (`capture_*`, A42, all phases CLOSED). What it did not have:

1. **Any binary point-cloud reader.** `capture/tools.py:303` maps ODM's
   `odm_georeferenced_model.laz` as an artifact the lane *produces and never
   opens*.
2. **Anything that consumes the tape measurements.**
   `docs/okongo-capture-protocol.md` §1/§4 sends the owner to site with a DISTO
   and tells them to record distances. No code read them. A42 T6 is the price:
   7-DOF ICP on unreferenced video **collapsed** (scale → 0, RMS 15 µm, 1.17 M
   points in a 0.5 mm blob) and the honest fallback was to borrow scale from the
   design envelope (×6.12).
3. **RANSAC, plane fitting, in-process normal estimation** — none existed.

`pc_control_add` / `pc_control_verify` are that missing input.

It also needs **no DCC**: all of it runs in-process, so it works with Blender
closed and is testable in CI on a synthetic fixture.

---

## Corrections this build made to its own brief

Each is recorded in `docs/DECISIONS.md` with the evidence that forced it.

| Brief said | Built instead | Why |
|---|---|---|
| dep `plyfile` | **trimesh** | plyfile is **GPL-3.0-or-later** (PyPI classifier, verified 2026-09-03). TEE is MIT. Research doc 43 already banned it and `voxkiln/license_lint.py:20` enforces it; doc 43's own recorded replacement is trimesh. |
| dep `pye57` | CloudCompare's `libQE57_IO_PLUGIN` | MIT, but builds libE57Format. CloudCompare 2.13.2 is already a lane dependency and ships the reader. |
| dep `open3d` | nothing — dropped | MIT, ~400 MB, for ICP alone — and there is no ICP here. `test_a46_no_heavy_imports.py` bans exactly this shape. |
| `scipy` assumed present | **declared** in the extra | It reached `server/.venv` only transitively; a clean sync would have dropped `cKDTree` silently. |
| `pc_register`, `pc_merge` | **`pc_merge` wraps, `pc_register` never built** | `capture_register` already does ICP with a refusing RMS gate and a degeneracy guard, and `pc_merge` (second pass, 2026-09-04) calls it rather than reimplementing it. What the wrapper adds is a frame it names itself and a second opinion on the fit — see P8. |
| `pc_control_check` | **`pc_control_verify`** | "check" is a common English verb worth 3 points on a name match; `pc_control_check` outranked `ex_estimate` for "check the drawing" and cost the registry a recall slot. |
| research doc unnumbered | `69-pointcloud-scan-prep.md` | every file in `docs/research/` is `NN-slug.md`. |
| "as 3D Scanner App writes them" | read the file's own header | The name is a generalisation for whatever iPhone scanner produced the export (owner, 2026-09-03), which makes hard-coding any app's quirks wrong. `pc_open` reports the writer, SRS and point format it finds. |
| A2 "normal-histogram should beat 0.1°" | **true, but only in 3D at k ≥ 80** | A 2D estimator collapsed to 26° of error. See below. |

---

## What was measured, and what it changed

All `measured 2026-09-03`, `server/.venv`, on the appendix fixture
(`seed=7` → **279,352 points**).

**Three algorithm laws came out of measurement, not reasoning:**

1. **Floor and ceiling are equally dominant.** In a box room both horizontal
   planes have the same inlier count to within noise, so "most inliers" is a
   coin flip — and the first implementation hung the room *under its ceiling*.
   The lane collects every qualifying plane, then takes the **lowest**.
2. **Normals must be estimated in 3D.** With 12 mm noise on a 15 mm grid, a 2D
   XY neighbourhood is isotropic noise: a planarity filter kept **6 of 40,000**
   neighbourhoods and the yaw estimate collapsed to **26.35°** of error. In 3D:
   k=20 → 0.073°, k=80 → 0.040°, **k=160 → 0.004°**.
3. **Yaw comes from the full-height wall band, never the slice.** A 50 mm slice
   measured **1.289°** against a 0.5° gate. Pinned by a test so that sharing the
   two estimators cannot look like a tidy simplification.

**Two format laws, both silent failures:**

4. **trimesh writes PLY as float32.** A UTM-georeferenced cloud loses
   **250 mm** through a round trip — and ODM's output is georeferenced by
   construction. `pc_export` always origin-shifts and records the offset.
5. **LAS scale is free precision.** File size is identical across scales
   (int32 ordinates either way). The conventional `1e-3` costs 0.5 mm — a
   quarter of the ±2 mm budget — so the lane writes `1e-4` (0.05 mm, ±214 km
   of span).

**One law about reporting:** per-segment *max* residual sits at ~2.9σ and reads
as a failure. Median is the quality signal; max is reported but labelled.

**And one sample-size floor found by a failing gate:** the control snap needs
enough points to average the noise down. A 0.15 m patch (~310 points) left a
4 m baseline 2.0 mm long = **503 ppm**, failing the 500 ppm gate; 0.25 m
(~860 points) lands at 78 ppm. The radius is now adaptive on point count,
because the plane's standard error goes as σ/√n — a sparse scan needs a wider
ball than a dense one for the same accuracy.

---

## What was built

`server/src/tee/pointcloud/` — mirroring `ex_*`, in tree, on `server/.venv`.

| File | Role |
|---|---|
| `store.py` | `<project>/.tee/pointcloud`; clouds as float64 `.npy` + JSON sidecar; every mutation mints a new id and records its parent |
| `io.py` | PLY (trimesh), LAS/LAZ (laspy), E57 (CloudCompare); both format laws enforced here |
| `level.py` | RANSAC floor, SVD refit, rotate to +Z, 3D-normal wall azimuth |
| `control.py` | Baseline snap, scale solve, the drift and units-conflict verdicts |
| `slice2d.py` | Band extraction, greedy RANSAC line fit with re-selection, DXF + SVG writers |
| `report.py` | The QA sheet and its six-line verdict |
| `condition.py` | Crop regions, statistical outlier removal, voxel thinning (P8) |
| `ortho.py` | Rectified facade rasters with a burnt-in scale bar (P8) |
| `merge.py` | Frame handling and the overlap second opinion around `capture_register` (P8) |
| `tools.py` | The 14 virtual tools |

**Fourteen tools, all virtual, zero added to the always-loaded 17.**
`pc_open`, `pc_stat`, `pc_level`, `pc_control_add`, `pc_control_verify`,
`pc_scale_apply`, `pc_slice`, `pc_section`, `pc_export`, `pc_report` (P1–P7),
plus `pc_crop`, `pc_clean`, `pc_ortho`, `pc_merge` (P8).

**Trust:** every tool tabled **individually** in `trust.py::_EXPLICIT` —
deliberately **no** `("pc_", …)` family row. Same lesson the `cad_` and `trade_`
comments record: a prefix default silently admits whatever is named next, and
nearly every tool here writes a file. `pc_stat` and `pc_control_verify` are
`read-compute`; the rest are `write-artifacts`.

---

## Acceptance — measured, not asserted

| | Result | Gate |
|---|---|---|
| **A1** level | residual **0.0000°**, floor RMS **11.7 mm** | ≤ 0.05°, 12 mm ± 20% |
| **A2** yaw | **0.031°** error (k=160 estimator reaches 0.004° standalone) | ≤ 0.5° |
| **A3** slice | **4 segments**, +2.1 / −0.8 mm | ± 5 mm |
| **A4** control | **161 ppm**; corrected +1.4 / −1.3 mm | ≤ 500 ppm, ± 2 mm |
| **A5** round trip | PLY/LAS/LAZ count, bbox, colour, intensity | float tolerance |
| **A6** DXF | `$INSUNITS = 6`, segment lengths match to 1 mm | 1 mm |
| **A7** budget | **682 tokens** for the whole sequence | ≤ 2,000 |
| **A8** no dumps | no array > 64, no string > 2 KB, tested | build-failing |
| **A9** headless | whole lane runs with no DCC; E57 refuses with its install line | — |

**Benchmark:** 91,820 tokens naive → **682 TEE**, a **99.26% saving** — and the
naive arm is already flattered, reading one point in forty rather than what a
real tool would return. The lane's caps are what keep the TEE arm flat as the
cloud grows: the same five calls cost the same at 280 K points or 15 M.

Tests: `server/tests/test_pointcloud_{store,geometry,io,tools}.py` (80 tests)
plus `fixtures_pointcloud.py`. Benchmark:
`benchmarks/run_benchmarks.py::run_pointcloud_scenario`.

---

## Deliberately not built

1. **Automatic wall/opening extraction to BIM or IFC.** Deciding which points
   *are* the wall, inside a 30 mm fuzz that also contains shuttering and a
   wheelbarrow, is interpretation, not transformation. Emitting `tee-plan/1`
   facts from slice segments would light up `ex_export_ifc` and
   `bl_build_from_plan` for free, and is exactly why it needs a decision record
   rather than a quiet addition.
2. **Drawing production.** No sheets, title blocks, dimension strings. `pc_*`
   emits *templates to trace on*.
3. **Meshing / surface reconstruction.** Different problem, different phase.
4. **Photogrammetry.** That is `capture_*`'s territory.
5. **A viewer.** CloudCompare is free and better.
6. **A second ICP.** `capture_register` owns registration, gate and guard
   included. `pc_merge` (P8) calls it; it does not reimplement it.

## P8 — the second pass (CLOSED 2026-09-04)

The four tools P1–P7 deferred, landed on the proven spine. Fourteen `pc_*`
tools now; the always-loaded surface is still 17 / ~2,033 tokens.

- **`pc_crop`** — box, z range, XY polygon, or all three; `invert` drops the
  region instead. Ray casting for the polygon is twenty lines here rather than
  a shapely dependency for one call. A crop that would leave under 100 points
  refuses, because that is almost always a units error and an eleven-point
  cloud hides it until the DXF.
- **`pc_clean`** — statistical outlier removal (threshold from the cloud's own
  spacing distribution, so it needs no tuning between a room and a site) plus
  optional voxel thinning. The voxel keeps the point NEAREST its cell centroid,
  never the centroid: a returned point is something the scanner saw, and an
  averaged one across an edge floats in mid-air.
- **`pc_ortho`** — a rectified facade PNG. Scale bar and origin cross are burned
  into the pixels, not drawn beside them, because a cropped and re-pasted copy
  is what actually reaches whoever traces it.
- **`pc_merge`** — wraps `capture_register`. Both clouds are shifted by the
  datum's centroid before being written out, so the transform comes back in a
  frame this module named rather than one CloudCompare chose (a UTM cloud would
  otherwise be silently re-centred by CloudCompare's global shift). It reports
  CloudCompare's RMS **and** its own overlap measure, because those two numbers
  mean different things and only the pair is a verdict.

### What driving it on the real scan changed

Three defects the synthetic fixture could not have shown, all found by running
the tools against the 900 K-point Okongo cloud:

1. **`pc_crop` answered a question nobody asked, silently.** `z_range:
   [0.05, 2.35]` on a PLY round trip returned the top HALF of the room, because
   PLY origin-shifts and that cloud's floor is at z = −1.36. The crop was
   correct and the request was not, and the response said nothing. It now says
   `z 0.05..2.35 reaches past this cloud (z is -1.584..1.356)`.
2. **Two depths of one facade overwrote each other.** `pc_ortho` named files by
   cloud and azimuth only, so comparing a 400 mm and an 800 mm depth compared an
   image with itself. Resolution and depth are in the filename now.
3. **A point is a sample, not a pixel.** At 10 mm pixels on a cloud sampled every
   30 mm, one-pixel splats gave a 64%-white stipple — the same "looks more like a
   texture" complaint the depth rasters drew. Each point now paints its own
   measured footprint (`dot_px`, derived from spacing): coverage 64% → 92% on the
   cabinet wall, and the vertical joints read as lines.

### Measured, 2026-09-04, through the registry on the real cloud

```
pc_crop   900,000 -> 623,548 in 0.04 s
pc_clean  17,728 outliers removed (2.8%) in 0.5 s; spacing 29.9 -> 28.8 mm
pc_ortho  340 x 221 px @ 10 mm/px in 0.02 s, coverage 0.92, dot_px 3
pc_merge  two halves, one rotated 4 deg and moved 120/80/30 mm:
          ICP RMS 38.9 mm, overlap 0.408, overlap RMS 10.0 mm
          reassembled bbox 5.099 x 5.355 x 2.924 vs 5.106 x 5.355 x 2.940
```

`tee_search_tools` re-measured at 85 tools with four new cases: limit 3 still
misses exactly one of 33, limit 5 still finds all 33. Four more tools cost the
search nothing, which is the claim progressive disclosure has to keep making.

## Open

- **No real fixture is committed.** `testbeds/` is absent and there is no
  `.ply`/`.las`/`.e57` anywhere in the repo. The synthetic fixture carries the
  whole gate. One room export under 20 MB plus its tape measurements as a
  sidecar JSON would turn A7 and A9 into real-world numbers and let doc 69 §3.4
  record the writer's actual header quirks.
