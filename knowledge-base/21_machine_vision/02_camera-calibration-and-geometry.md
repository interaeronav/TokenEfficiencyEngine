---
id: vision.calibration
title: Camera calibration and multi-view geometry
domain: 21_machine_vision
tags: [calibration, pinhole, intrinsics, distortion, homography, epipolar, stereo, disparity, depth-camera, lidar, photogrammetry, sfm, colmap, gsd]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Camera Calibration (OpenCV-Python tutorial)", url: "https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html", publisher: "OpenCV 4.13.0", accessed: 2026-08-25}
  - {title: "Epipolar Geometry (OpenCV-Python tutorial)", url: "https://docs.opencv.org/4.x/da/de9/tutorial_py_epipolar_geometry.html", publisher: "OpenCV", accessed: 2026-08-25}
  - {title: "Ground sample distance", url: "https://en.wikipedia.org/wiki/Ground_sample_distance", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "COLMAP — Structure-from-Motion and Multi-View Stereo", url: "https://colmap.github.io/", publisher: "COLMAP", accessed: 2026-08-25}
related: [vision.imaging, vision.classical, vision.construction, vision.projects]
unit_system: SI
---

# Camera calibration and multi-view geometry

**Summary.** Calibration is the step that converts a camera from a picture-taking device into a measuring instrument. This file develops the pinhole model, the intrinsic and extrinsic parameters, the Brown–Conrady distortion model, and the practical checkerboard procedure in OpenCV, then builds upward through homography, epipolar geometry, stereo disparity, active depth sensing (structured light, ToF, LiDAR) and finally structure-from-motion photogrammetry. It closes with an honest statement of what metric accuracy each method delivers, because the gap between demo accuracy and field accuracy is where most survey and as-built projects fail.

## Key facts

| Item | Value |
|---|---|
| Pinhole projection | `s·[u v 1]ᵀ = K · [R t] · [X Y Z 1]ᵀ` (see body) |
| Intrinsic matrix `K` | `[[fx, 0, cx], [0, fy, cy], [0, 0, 1]]` — units: pixels |
| Distortion vector (OpenCV) | `(k1, k2, p1, p2, k3[, k4, k5, k6, s1..s4, τx, τy])` |
| Good calibration RMS reprojection error | < 0.3 px typical; < 0.1 px with telecentric/metrology optics |
| Minimum checkerboard views | 10 in theory; **20–30 in practice**, well spread in pose and depth |
| Stereo depth | `Z = f·B / d` (`f` px, `B` baseline, `d` disparity px) |
| Stereo depth error | `ΔZ = Z² · Δd / (f·B)` — grows with the **square** of range |
| Ground sample distance (nadir) | `GSD = H · p / f` |
| Typical drone photogrammetry accuracy | ~1–3 × GSD horizontal, ~2–5 × GSD vertical, **with good ground control** |
| Terrestrial laser scanner range noise | ~1–3 mm at 10–50 m (survey-grade instruments) |
| COLMAP licence | New BSD (with a documented dependency caveat) |

## The pinhole camera model

A world point `X = (X, Y, Z)` in some world frame maps to a pixel `(u, v)`:

```
s · [u, v, 1]ᵀ  =  K · [R | t] · [X, Y, Z, 1]ᵀ
```

- `[R | t]` are the **extrinsics**: a 3×3 rotation and 3×1 translation putting the world frame into the camera frame. Six degrees of freedom. They describe *where the camera is*.
- `K` is the **intrinsic matrix**, describing the camera itself:

```
K = [ fx   0   cx ]
    [  0  fy   cy ]
    [  0   0    1 ]
```

`fx = f / px_width` and `fy = f / px_height` — focal length expressed in pixels. `fx ≠ fy` only for non-square pixels or anamorphic optics; in practice their ratio is a useful sanity check (it should be within a fraction of a percent of 1.0). `(cx, cy)` is the principal point, nominally the image centre but typically offset by a few to a few tens of pixels. A skew term `s` exists in the general model and is essentially always zero for digital sensors.

- `s` (the leading scalar) is the projective depth. **This is why a single image cannot measure distance**: scale is unrecoverable without an additional constraint — a known object size, a known plane, a second view, or an active depth measurement.

### Distortion

The pinhole model is exact for an ideal lens. Real lenses need the Brown–Conrady correction, applied to *normalised* coordinates `(x, y) = ((u−cx)/fx, (v−cy)/fy)` with `r² = x² + y²`:

```
radial:      x_d = x (1 + k1 r² + k2 r⁴ + k3 r⁶)
tangential:  x_d += 2 p1 x y + p2 (r² + 2x²)
             y_d += p1 (r² + 2y²) + 2 p2 x y
```

**Radial** terms model the symmetric barrel/pincushion behaviour and dominate. **Tangential** terms model the sensor not being exactly perpendicular to the optical axis (decentring); they are usually small and are sometimes fixed to zero for stability. OpenCV also offers a rational model (`k4, k5, k6`) for very wide lenses and a thin-prism/tilted-sensor model.

> ⚠️ Fitting more distortion coefficients than your data supports is a classic error. With fewer than ~20 well-distributed views, `k3` will absorb noise and your undistortion will be worse at the corners than with a 2-coefficient fit. Use `cv.CALIB_FIX_K3` unless you have a genuinely wide lens and plenty of data.

## Checkerboard calibration with OpenCV

The standard Zhang planar-target method. The tutorial functions are `findChessboardCorners`, `cornerSubPix`, `calibrateCamera`, `getOptimalNewCameraMatrix`, `undistort` and `projectPoints`.

```python
import glob
import numpy as np
import cv2 as cv

# --- target definition -------------------------------------------------
COLS, ROWS = 9, 6          # INNER corner counts, not squares
SQUARE_MM  = 25.0          # measured with calipers, not "as ordered"

objp = np.zeros((ROWS * COLS, 3), np.float32)
objp[:, :2] = np.mgrid[0:COLS, 0:ROWS].T.reshape(-1, 2) * SQUARE_MM

objpoints, imgpoints = [], []
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

paths = sorted(glob.glob("calib/*.png"))
for p in paths:
    img  = cv.imread(p)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    ok, corners = cv.findChessboardCorners(
        gray, (COLS, ROWS),
        flags=cv.CALIB_CB_ADAPTIVE_THRESH | cv.CALIB_CB_NORMALIZE_IMAGE)
    if not ok:
        print("no board:", p); continue
    corners = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
    objpoints.append(objp)
    imgpoints.append(corners)

h, w = gray.shape[:2]
rms, K, dist, rvecs, tvecs = cv.calibrateCamera(
    objpoints, imgpoints, (w, h), None, None,
    flags=cv.CALIB_FIX_K3)

print(f"RMS reprojection error: {rms:.4f} px  over {len(objpoints)} views")
print("K =\n", K)
print("dist =", dist.ravel())

# --- per-view error: find the bad boards --------------------------------
for i, p in enumerate(paths[:len(objpoints)]):
    proj, _ = cv.projectPoints(objpoints[i], rvecs[i], tvecs[i], K, dist)
    err = cv.norm(imgpoints[i], proj, cv.NORM_L2) / len(proj)
    print(f"{p}: {err:.4f} px")

# --- undistort ----------------------------------------------------------
newK, roi = cv.getOptimalNewCameraMatrix(K, dist, (w, h), alpha=0)
mapx, mapy = cv.initUndistortRectifyMap(K, dist, None, newK, (w, h), cv.CV_16SC2)
undist = cv.remap(cv.imread(paths[0]), mapx, mapy, cv.INTER_LINEAR)
cv.imwrite("undistorted.png", undist)

np.savez("calib.npz", K=K, dist=dist, newK=newK, rms=rms)
```

**Procedure that actually produces a good calibration:**

1. Use a **rigid, flat** target. A checkerboard printed on paper and taped to a wall is a leading cause of bad calibrations. Buy or make an aluminium- or glass-backed target; measure the square pitch.
2. Use an **asymmetric** grid dimension (e.g. 9 × 6, not 8 × 8) so orientation is unambiguous.
3. Capture 20–30 views. Fill the frame; **critically, include views where the board occupies the corners**, since that is where distortion lives.
4. **Tilt the board** 20–45° in several directions. A stack of fronto-parallel views is degenerate — focal length and distance become unseparable and `fx` will be wrong even with a beautiful RMS.
5. Vary the depth across the working range.
6. Lock focus and aperture. **Any change to focus changes `f`, `cx`, `cy` and the distortion.** Tape the focus ring.
7. Check the per-view errors and delete the worst boards (motion blur, glare) — then recalibrate.
8. Sanity-check `fx` against the physical prediction: `fx = f_mm / pixel_pitch_mm`. A 12 mm lens on 3.45 µm pixels should give `fx ≈ 3478`. If calibration returns 2900, something is wrong.

**Alternatives to the checkerboard.** ChArUco boards (`cv.aruco`) tolerate partial occlusion and give better corner localisation; circle grids (`findCirclesGrid`) with asymmetric patterns are used where the target may be defocused. For metrology, a **coded photogrammetric target field** with certified scale bars is the professional route.

## Homography — the single-plane special case

If all points lie on a plane, the mapping between two views is a 3×3 homography `H`, with 8 degrees of freedom:

```python
H, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC, ransacReprojThreshold=3.0)
warped  = cv.warpPerspective(img, H, (out_w, out_h))
```

This is the workhorse for: rectifying a photograph of a flat panel, door, wall or drawing into a metric top-down view; stitching panoramas when the camera only rotates; registering successive site photos taken from a marked position; and mapping a camera view into floor coordinates for an exclusion-zone monitor (`08`).

**Metric use:** photograph a flat surface with four known control points (corners of a calibration square, survey targets, or a known-size object), compute `H` to a metric grid, and you have a plane-rectified image with a known mm/px. This is the cheapest honest measurement in the whole field — a phone photo of a wall with a 1 m scale bar in frame, rectified, will give you crack positions to a few millimetres.

## Epipolar geometry and stereo

For two views of a rigid scene, corresponding points `x` and `x'` satisfy the epipolar constraint:

```
x'ᵀ F x = 0          (pixel coordinates, F = fundamental matrix, rank 2, 7 DoF)
x'ᵀ E x = 0          (normalised coordinates, E = K'ᵀ F K = [t]× R, 5 DoF)
```

`F` maps a point in one image to a **line** (the epiline) in the other. All epilines pass through the epipole, the projection of the other camera's centre. OpenCV: `cv.findFundamentalMat`, `cv.findEssentialMat`, `cv.recoverPose`, `cv.computeCorrespondEpilines`.

### Calibrated stereo

```python
# Calibrate each camera individually first, then:
flags = cv.CALIB_FIX_INTRINSIC
rms, K1, d1, K2, d2, R, T, E, F = cv.stereoCalibrate(
    objpoints, imgpoints_l, imgpoints_r, K1, d1, K2, d2,
    (w, h), flags=flags, criteria=criteria)

R1, R2, P1, P2, Q, roi1, roi2 = cv.stereoRectify(
    K1, d1, K2, d2, (w, h), R, T, alpha=0)

m1x, m1y = cv.initUndistortRectifyMap(K1, d1, R1, P1, (w, h), cv.CV_16SC2)
m2x, m2y = cv.initUndistortRectifyMap(K2, d2, R2, P2, (w, h), cv.CV_16SC2)

rl = cv.remap(imgL, m1x, m1y, cv.INTER_LINEAR)
rr = cv.remap(imgR, m2x, m2y, cv.INTER_LINEAR)

stereo = cv.StereoSGBM_create(
    minDisparity=0, numDisparities=16*10, blockSize=5,
    P1=8*3*5**2, P2=32*3*5**2, uniquenessRatio=10,
    speckleWindowSize=100, speckleRange=2, mode=cv.STEREO_SGBM_MODE_SGBM_3WAY)

disp = stereo.compute(rl, rr).astype(np.float32) / 16.0
points3d = cv.reprojectImageTo3D(disp, Q)     # metric, same units as SQUARE_MM
```

After rectification, corresponding points lie on the same image row, so matching is a 1D search. Depth follows from

```
Z = f · B / d
```

with `f` in pixels, `B` the baseline in metres and `d` the disparity in pixels. Differentiating:

```
ΔZ = Z² · Δd / (f · B)
```

**This quadratic term is the central fact of stereo.** A stereo rig with `f = 1000 px`, `B = 0.12 m` and 0.25 px disparity precision gives ΔZ ≈ 5 mm at 1.5 m, but ≈ 21 mm at 3 m and ≈ 130 mm at 7.5 m. Stereo is excellent close-in and useless at range unless you lengthen the baseline proportionally.

Stereo also fails on **textureless surfaces** — a plain white plasterboard wall, a melamine panel, a clear sky — because there is nothing to match. This is exactly why active projection exists.

## Active depth sensing

**Structured light.** Project a known pattern and triangulate its deformation.
- *Laser-line profilers* (Keyence LJ-X8000, LMI Gocator, Photoneo PhoXi, Cognex 3D-A1000) sweep a line across the part or the part past the line. Z-repeatability from sub-micron to tens of microns depending on the field. The industrial standard for weld-bead, solder-paste and surface-profile inspection, and for timber board profiling.
- *Coded/phase-shift* projectors (grey codes plus phase-shifted sinusoids) capture a whole area at once in tens of milliseconds. Intel RealSense D4xx series uses a cheap IR dot projector to add texture for its stereo pair — a "semi-active" design.

**Time-of-flight (ToF).** Measures the round-trip time of a modulated IR pulse per pixel. Range 0.5–10 m, depth noise typically several millimetres to a few centimetres, immune to texture, poor on dark or specular surfaces, and vulnerable to multipath (a corner reads deeper than it is). Microsoft Azure Kinect DK (discontinued but widespread), the LiDAR sensor in iPhone/iPad Pro, and various industrial ToF cameras.

**LiDAR.** Scanning rangefinders. Two families matter here:
- *Terrestrial laser scanners* (Leica RTC360/BLK360, Faro Focus, Trimble X7, NavVis) — survey instruments, range noise of a few millimetres at tens of metres, millions of points per second, registered by targets or cloud-to-cloud. This is the Scan-to-BIM workhorse (`08`).
- *Mobile/SLAM scanners* (GeoSLAM/FARO Orbis, Leica BLK2GO, NavVis VLX) trade absolute accuracy (typically 1–3 cm after drift correction) for capture speed — a whole floor in minutes rather than a day.

## Photogrammetry and structure-from-motion

SfM recovers camera poses *and* sparse 3D structure from an unordered image set: feature detection and matching → geometric verification → incremental (or global) bundle adjustment. Multi-view stereo (MVS) then densifies it into a point cloud or mesh.

**COLMAP** is the reference open implementation: robust incremental SfM plus PatchMatch-stereo MVS, GUI and CLI, new-BSD licensed. Minimal pipeline:

```bash
colmap feature_extractor   --database_path db.db --image_path images/ \
                           --ImageReader.single_camera 1
colmap exhaustive_matcher  --database_path db.db
mkdir -p sparse && colmap mapper --database_path db.db --image_path images/ \
                                 --output_path sparse
colmap image_undistorter   --image_path images/ --input_path sparse/0 \
                           --output_path dense --output_type COLMAP
colmap patch_match_stereo  --workspace_path dense
colmap stereo_fusion       --workspace_path dense --output_path dense/fused.ply
```

Alternatives: **OpenMVG + OpenMVS** (modular, permissive licences), **Meshroom/AliceVision** (GUI, free), **Agisoft Metashape** and **Pix4Dmapper/RealityCapture** commercially, plus **NeRF/3D Gaussian Splatting** pipelines (nerfstudio, gsplat) which produce beautiful novel views but are *not* currently metrology tools — their geometry is a by-product, not a guaranteed measurement.

### Scale, and the thing everyone forgets

**SfM output has no scale.** Recovering metric dimensions requires one of:
1. **Ground control points (GCPs)** surveyed by GNSS/total station and identified in the imagery — the professional standard;
2. **Scale bars** of certified length placed in the scene — the standard for small-object and close-range work;
3. **RTK/PPK GNSS on the drone**, giving direct camera-station geotags at centimetre accuracy;
4. Known camera baseline from a rigid stereo rig.

Consumer geotags from a non-RTK drone are metres-accurate and give you *georeferencing*, not *accuracy*.

### Ground sample distance and expected accuracy

```
GSD = H · p / f
```

`H` = height above ground, `p` = pixel pitch, `f` = focal length, consistent units. Example: a 20 MP drone camera with 2.4 µm pixels and an 8.8 mm lens at 60 m gives `GSD = 60000 mm × 0.0024 / 8.8 = 16.4 mm/px`.

Rules of thumb widely used in the survey industry (and to be validated on every job, not assumed):

- **Horizontal accuracy ≈ 1–3 × GSD**, with adequate GCP distribution.
- **Vertical accuracy ≈ 2–5 × GSD** — always worse, because vertical is the weak axis of a nadir block.
- Add 60–80 % forward and 60–70 % side overlap; drop below that and the bundle weakens abruptly.
- Add **oblique** imagery (15–30° off nadir) or a cross-hatch flight to break the "doming" systematic error that afflicts nadir-only blocks with self-calibrating cameras.

> ⚠️ Never state a photogrammetric accuracy without stating (a) the GSD, (b) the number and distribution of GCPs, (c) the check-point RMSE on points **withheld from the adjustment**. A reported RMSE on control points used in the solve is a measure of the fit, not of the accuracy.

### Metric accuracy expectations, honestly stated

| Method | Typical achievable accuracy | Conditions |
|---|---|---|
| Plane-rectified single photo with scale bar | 2–10 mm over a 2–3 m wall | Flat surface, good control points |
| Phone-photo SfM of a room, scale bar | 5–20 mm | 100+ images, good texture, careful capture |
| Drone photogrammetry, 60 m AGL, RTK + GCPs | 20–50 mm H, 40–80 mm V | ~16 mm GSD, 5+ GCPs, checked |
| Terrestrial laser scan, registered | 3–10 mm over a building | Survey-grade instrument, target registration |
| SLAM-based mobile scanner | 10–30 mm | Loop closure achieved |
| Calibrated stereo rig at 1.5 m | 3–8 mm in Z | Textured surface, 100+ mm baseline |
| Industrial structured-light profiler | 1–50 µm in Z | Small field, fixtured part |
| Uncalibrated phone photo, no scale | **No metric claim is possible** | |

## Sources

- [OpenCV — Camera Calibration (Python tutorial), v4.13.0](https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html) — function names, `criteria=(EPS+MAX_ITER, 30, 0.001)`, reprojection-error method.
- [OpenCV — Epipolar Geometry](https://docs.opencv.org/4.x/da/de9/tutorial_py_epipolar_geometry.html) — `findFundamentalMat`, `computeCorrespondEpilines`, F maps a point to an epiline.
- [Wikipedia — Ground sample distance](https://en.wikipedia.org/wiki/Ground_sample_distance) — `GSD = slant range × pixel size / focal length`; worked example 1000 m / 2.9 µm / 600 mm → 1.21 cm/px.
- [COLMAP](https://colmap.github.io/) — incremental SfM + PatchMatch MVS, free and open source.

## Open questions

- The "1–3 × GSD horizontal, 2–5 × GSD vertical" heuristic is industry folklore repeated across vendor literature; no single authoritative primary source was fetched for it. Marked `needs-verification` — verify against ASPRS Positional Accuracy Standards for Digital Geospatial Data before contractual use.
- Specific instrument noise figures (Leica RTC360, Faro Focus, Intel RealSense) are stated from general familiarity, not from datasheets fetched in this pass.
- COLMAP's exact licence text (new BSD, with historical caveats around SiftGPU) should be confirmed on the repository before redistribution.
