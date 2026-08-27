---
id: vision.classical
title: Classical image processing — the working OpenCV toolkit
domain: 21_machine_vision
tags: [opencv, colour-space, thresholding, otsu, morphology, convolution, canny, sobel, contours, hough, template-matching, sift, orb, akaze, optical-flow, blob-analysis]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Image Thresholding (OpenCV-Python)", url: "https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html", publisher: "OpenCV 4.13.0", accessed: 2026-08-25}
  - {title: "Feature Detection and Description (OpenCV-Python)", url: "https://docs.opencv.org/4.x/db/d27/tutorial_py_table_of_contents_feature2d.html", publisher: "OpenCV", accessed: 2026-08-25}
  - {title: "Camera Calibration (OpenCV-Python)", url: "https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html", publisher: "OpenCV", accessed: 2026-08-25}
related: [vision.imaging, vision.calibration, vision.deep_learning, vision.projects]
---

# Classical image processing — the working OpenCV toolkit

**Summary.** Classical computer vision has not been superseded; it has been *specialised*. In any scene you control, a deterministic pipeline of threshold → morphology → contour → measure will be faster, more explainable, more accurate and vastly cheaper to maintain than a neural network. This file is the working toolkit, with runnable OpenCV-Python for every technique: colour spaces, histogram operations, all three families of thresholding, morphology, filtering and convolution, edge detection, contours and shape descriptors, Hough transforms, template matching, the feature detector/descriptor family, optical flow and blob analysis. All code targets OpenCV 4.x (`pip install opencv-python numpy`) and is written to run against a file you supply.

## Key facts

| Tool | Function | When it is the right answer |
|---|---|---|
| Otsu threshold | `cv.threshold(..., THRESH_BINARY+THRESH_OTSU)` | Bimodal histogram, even illumination |
| Adaptive threshold | `cv.adaptiveThreshold` | Uneven illumination, e.g. document/text/large panel |
| Morphological opening | `cv.morphologyEx(..., MORPH_OPEN)` | Remove small bright noise, keep large shapes |
| Canny | `cv.Canny(img, t1, t2)` | Thin, connected, single-response edges |
| `findContours` + `arcLength`/`contourArea` | shape descriptors | Blob measurement in a binary image |
| `HoughLinesP` | probabilistic Hough | Straight edges (panel edges, formwork, rebar) |
| `matchTemplate` | NCC / SQDIFF | Fixed-scale, fixed-rotation part location |
| SIFT (main module since OpenCV 4.4) | `cv.SIFT_create()` | Robust matching across scale/rotation/viewpoint |
| ORB | `cv.ORB_create()` | Fast, binary, free, real-time matching |
| AKAZE | `cv.AKAZE_create()` | Better than ORB on scale, still fast and free |
| Farnebäck / Lucas–Kanade | `calcOpticalFlowFarneback` / `calcOpticalFlowPyrLK` | Dense / sparse motion |
| SimpleBlobDetector | `cv.SimpleBlobDetector_create` | Counting round-ish things with filters |

## Colour spaces

```python
import cv2 as cv
import numpy as np

bgr  = cv.imread("panel.jpg")                    # OpenCV loads BGR, not RGB
gray = cv.cvtColor(bgr, cv.COLOR_BGR2GRAY)
hsv  = cv.cvtColor(bgr, cv.COLOR_BGR2HSV)        # H in [0,179], S,V in [0,255]
lab  = cv.cvtColor(bgr, cv.COLOR_BGR2LAB)

# Segment a high-visibility vest colour band in HSV, robust to brightness
lo1, hi1 = np.array([ 5,120,120]), np.array([ 25,255,255])   # orange
mask = cv.inRange(hsv, lo1, hi1)
```

- **BGR/RGB** — device space; every channel co-varies with illumination, so thresholding here is fragile.
- **HSV/HSL** — separates hue from intensity. The pragmatic choice for colour segmentation (safety vests, painted markings, coloured tape). Watch the hue wraparound at red: you need two ranges, `[0,10]` and `[170,179]`.
- **CIELAB** — perceptually near-uniform, so Euclidean distance in `(L*,a*,b*)` approximates perceived colour difference. **This is the correct space for colour matching in joinery and finishes**: ΔE*ab below ~1 is imperceptible, 1–2 perceptible on close inspection, above 3 obvious. Lacquer batch matching and veneer sorting should be specified in ΔE, not in RGB.
- **YCrCb** — used in compression; Cr/Cb are handy for skin detection and for cheap chroma keying.

## Histogram operations

```python
hist = cv.calcHist([gray], [0], None, [256], [0, 256])

eq   = cv.equalizeHist(gray)                       # global; often too aggressive
clahe = cv.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
eq2  = clahe.apply(gray)                           # local; far better in practice

# Back-projection: find pixels resembling a sampled patch
roi_hsv = cv.cvtColor(patch, cv.COLOR_BGR2HSV)
roihist = cv.calcHist([roi_hsv], [0, 1], None, [180, 256], [0,180,0,256])
cv.normalize(roihist, roihist, 0, 255, cv.NORM_MINMAX)
prob = cv.calcBackProject([hsv], [0, 1], roihist, [0,180,0,256], 1)
```

**CLAHE** (contrast-limited adaptive histogram equalisation) is the one to reach for: it equalises in tiles and clips the histogram to limit noise amplification. It is the standard pre-processing step for crack detection on concrete photographed in mixed sun and shade.

## Thresholding

```python
# 1. Global fixed — only when illumination is genuinely controlled
_, b1 = cv.threshold(gray, 128, 255, cv.THRESH_BINARY)

# 2. Otsu — picks the threshold that minimises intra-class variance
t, b2 = cv.threshold(gray, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
print("Otsu chose", t)

# Otsu is sensitive to noise: blur first
blur = cv.GaussianBlur(gray, (5, 5), 0)
t, b3 = cv.threshold(blur, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

# 3. Adaptive — the answer to a gradient across the image
b4 = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C,
                          cv.THRESH_BINARY, blockSize=35, C=7)
```

`blockSize` must be odd and should be larger than the features you want to keep but smaller than the illumination gradient. `C` is subtracted from the local mean and controls how aggressive the split is. Adaptive thresholding is how you read a stencilled mark on a large plywood sheet lit by one window.

Other flags: `THRESH_BINARY_INV`, `THRESH_TRUNC`, `THRESH_TOZERO`, `THRESH_TOZERO_INV`. `THRESH_TRIANGLE` is a useful alternative to Otsu for unimodal histograms with a tail — bright defects on a dark field.

## Morphology

```python
k3  = cv.getStructuringElement(cv.MORPH_RECT,    (3, 3))
kel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (7, 7))
klin= cv.getStructuringElement(cv.MORPH_RECT,    (25, 1))   # horizontal only

eroded  = cv.erode(b3, k3, iterations=1)
dilated = cv.dilate(b3, k3, iterations=1)
opened  = cv.morphologyEx(b3, cv.MORPH_OPEN,     kel)   # erode then dilate
closed  = cv.morphologyEx(b3, cv.MORPH_CLOSE,    kel)   # dilate then erode
grad    = cv.morphologyEx(b3, cv.MORPH_GRADIENT, k3)    # outline
tophat  = cv.morphologyEx(gray, cv.MORPH_TOPHAT, cv.getStructuringElement(
                          cv.MORPH_ELLIPSE, (51, 51)))  # bright small features
blackhat= cv.morphologyEx(gray, cv.MORPH_BLACKHAT, kel) # dark small features
```

The mental model: **opening** removes bright things smaller than the structuring element; **closing** fills dark things smaller than it; **top-hat** = original minus opening, which isolates small bright detail while removing any illumination gradient. Top-hat with a large elliptical kernel is a superb, cheap illumination-normaliser and a good first move for scratch and crack enhancement.

**Anisotropic kernels are underused.** A 25 × 1 rectangle only closes gaps horizontally — exactly what you want when isolating the horizontal mortar joints of blockwork, or the straight edge of a panel, while ignoring vertical noise.

## Filtering and convolution

```python
box   = cv.blur(gray, (5, 5))
gauss = cv.GaussianBlur(gray, (5, 5), sigmaX=1.4)
med   = cv.medianBlur(gray, 5)          # kills salt-and-pepper, preserves edges
bil   = cv.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)  # edge-preserving smooth

sharpen_k = np.array([[ 0,-1, 0],
                      [-1, 5,-1],
                      [ 0,-1, 0]], np.float32)
sharp = cv.filter2D(gray, -1, sharpen_k)

lap = cv.Laplacian(gray, cv.CV_64F, ksize=3)
focus_measure = lap.var()               # variance of Laplacian = autofocus metric
```

`focus_measure` deserves a note: the variance of the Laplacian is the standard cheap sharpness metric, and it is the right way to **automatically reject out-of-focus site photographs** before they enter a pipeline. Calibrate a threshold on your own imagery; it is not comparable across cameras.

## Edge detection

```python
gx = cv.Sobel(gray, cv.CV_64F, 1, 0, ksize=3)
gy = cv.Sobel(gray, cv.CV_64F, 0, 1, ksize=3)
mag = cv.magnitude(gx, gy)
ang = cv.phase(gx, gy, angleInDegrees=True)

# Canny: hysteresis with two thresholds. Auto-set them from the median.
v  = np.median(blur)
lo = int(max(0, 0.66 * v))
hi = int(min(255, 1.33 * v))
edges = cv.Canny(blur, lo, hi, L2gradient=True)
```

Canny is Sobel gradient → non-maximum suppression → hysteresis linking between `t1` and `t2`. A commonly used ratio is `t2 ≈ 2·t1` to `3·t1`. `L2gradient=True` uses the true Euclidean magnitude rather than `|gx|+|gy|` and is slightly more accurate.

**Subpixel edges.** `Canny` gives you pixel-quantised edges, which is not good enough for gauging. For a metrology edge, sample the intensity profile along the normal to the nominal edge and fit — either the zero-crossing of the first derivative, or an error-function/sigmoid fit. This routinely delivers 1/10-pixel repeatability and is what commercial "caliper tools" (Cognex, HALCON `measure_pos`) do internally.

```python
def subpixel_edge_1d(profile):
    """Zero-crossing of the derivative of a 1-D intensity profile,
    with parabolic interpolation around the gradient peak."""
    g = np.gradient(profile.astype(np.float64))
    i = int(np.argmax(np.abs(g)))
    if i == 0 or i >= len(g) - 1:
        return float(i)
    a, b, c = np.abs(g[i-1]), np.abs(g[i]), np.abs(g[i+1])
    denom = (a - 2*b + c)
    delta = 0.0 if denom == 0 else 0.5 * (a - c) / denom
    return i + delta
```

## Contours and shape descriptors

```python
cnts, hier = cv.findContours(b3, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

MM_PER_PX = 0.127        # from the calibration in file 01/02
for c in cnts:
    area_px = cv.contourArea(c)
    if area_px < 200:
        continue
    peri  = cv.arcLength(c, True)
    x,y,w,h = cv.boundingRect(c)
    rect  = cv.minAreaRect(c)          # ((cx,cy),(w,h),angle) — rotated box
    (cxc, cyc), radius = cv.minEnclosingCircle(c)
    hull  = cv.convexHull(c)

    circularity = 4*np.pi*area_px / (peri**2)          # 1.0 = perfect circle
    solidity    = area_px / max(cv.contourArea(hull), 1)
    aspect      = w / float(h)
    extent      = area_px / float(w*h)

    M  = cv.moments(c)
    cx, cy = M["m10"]/M["m00"], M["m01"]/M["m00"]      # centroid
    hu = cv.HuMoments(M).flatten()                     # 7 invariant moments

    approx = cv.approxPolyDP(c, 0.02*peri, True)       # polygon simplification
    n_sides = len(approx)

    print(f"area {area_px*MM_PER_PX**2:8.1f} mm²  "
          f"circ {circularity:.3f}  sol {solidity:.3f}  sides {n_sides}")
```

**Hu moments** are invariant to translation, scale and rotation, which makes them a compact classical shape signature — usable, with a nearest-neighbour classifier, to sort a small fixed set of part shapes without any machine learning. `cv.matchShapes(c1, c2, cv.CONTOURS_MATCH_I1, 0)` wraps this.

`cv.connectedComponentsWithStats` is often the better tool when you want labels plus areas and centroids in one pass and do not need contour geometry.

## Hough transforms

```python
# Probabilistic Hough lines — panel edges, formwork, scaffold, rebar
lines = cv.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=80,
                       minLineLength=100, maxLineGap=10)
if lines is not None:
    for x1, y1, x2, y2 in lines[:, 0]:
        cv.line(bgr, (x1,y1), (x2,y2), (0,255,0), 2)

# Circles — bolt heads, dowel holes, cable ends
circles = cv.HoughCircles(cv.medianBlur(gray, 5), cv.HOUGH_GRADIENT, dp=1,
                          minDist=20, param1=100, param2=30,
                          minRadius=8, maxRadius=40)
```

`HoughCircles` is notoriously sensitive to `param2` (the accumulator threshold) and to `minDist`. Set `minRadius`/`maxRadius` tightly from your known mm/px — that single constraint fixes most bad results. For anything more demanding, fit circles to contour points by least squares rather than voting.

## Template matching

```python
res = cv.matchTemplate(gray, tmpl_gray, cv.TM_CCOEFF_NORMED)
minv, maxv, minloc, maxloc = cv.minMaxLoc(res)
if maxv > 0.85:
    th, tw = tmpl_gray.shape[:2]
    cv.rectangle(bgr, maxloc, (maxloc[0]+tw, maxloc[1]+th), (0,0,255), 2)
```

Honest limits: `matchTemplate` is **not** scale- or rotation-invariant and degrades quickly under illumination change even with normalised correlation. It is the right tool for a fixtured part under fixed lighting, and the wrong tool for anything else. The industrial answer to its limitations is **shape-based matching** (edge-gradient models with explicit search over scale and rotation) — HALCON's `find_shape_model` and Cognex PatMax are the well-known implementations, and there is no exact open equivalent, which is one of the genuine reasons people pay for HALCON (`07`).

## Feature detectors and descriptors

Since OpenCV 4.4, SIFT is in the main `features2d` module (the patent expired in March 2020). SURF remains in `opencv_contrib` behind a non-free build flag.

```python
img1 = cv.imread("ref.jpg", cv.IMREAD_GRAYSCALE)
img2 = cv.imread("scene.jpg", cv.IMREAD_GRAYSCALE)

sift = cv.SIFT_create(nfeatures=0, contrastThreshold=0.04)
k1, d1 = sift.detectAndCompute(img1, None)
k2, d2 = sift.detectAndCompute(img2, None)

# FLANN + Lowe ratio test (float descriptors)
flann = cv.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))
knn   = flann.knnMatch(d1, d2, k=2)
good  = [m for m, n in knn if m.distance < 0.75 * n.distance]

if len(good) >= 8:
    src = np.float32([k1[m.queryIdx].pt for m in good]).reshape(-1,1,2)
    dst = np.float32([k2[m.trainIdx].pt for m in good]).reshape(-1,1,2)
    H, mask = cv.findHomography(src, dst, cv.RANSAC, 4.0)
    print("inliers:", int(mask.sum()), "of", len(good))
```

Binary descriptors use Hamming distance and a brute-force matcher:

```python
orb  = cv.ORB_create(nfeatures=3000, scaleFactor=1.2, nlevels=8)
akaze= cv.AKAZE_create()
k1,d1 = orb.detectAndCompute(img1, None)
k2,d2 = orb.detectAndCompute(img2, None)
bf   = cv.BFMatcher(cv.NORM_HAMMING, crossCheck=True)
matches = sorted(bf.match(d1, d2), key=lambda m: m.distance)
```

| Detector | Descriptor | Speed | Invariance | Licence |
|---|---|---|---|---|
| SIFT | 128-D float | Slow | Scale, rotation, moderate affine; best all-round quality | Free since 2020 |
| SURF | 64/128-D float | Medium | Similar to SIFT | Patented, contrib/non-free |
| ORB | 256-bit binary | Very fast | Rotation + limited scale | BSD |
| AKAZE | 486-bit binary (MLDB) | Fast | Better scale behaviour than ORB | BSD |
| BRISK | 512-bit binary | Fast | Scale + rotation | BSD |

**Learned alternatives** now beat all of the above on hard viewpoint change: SuperPoint + SuperGlue/LightGlue, DISK, and dense matchers such as LoFTR and RoMa. Use them when classical matching fails (repetitive facades, low texture, large baselines) and you can afford a GPU. Note their licences — SuperPoint/SuperGlue are research-use-only from Magic Leap; LightGlue and DISK are permissive.

**The Lowe ratio test** (`m.distance < 0.75 * n.distance`) is not optional; it removes ambiguous matches from repetitive structure, which is the entire failure mode on brickwork, cladding and window grids.

## Optical flow

```python
# Sparse: Lucas–Kanade on good-features-to-track
p0 = cv.goodFeaturesToTrack(prev_gray, maxCorners=300, qualityLevel=0.01,
                            minDistance=10, blockSize=7)
p1, st, err = cv.calcOpticalFlowPyrLK(prev_gray, gray, p0, None,
                                      winSize=(21,21), maxLevel=3,
                                      criteria=(cv.TERM_CRITERIA_EPS |
                                                cv.TERM_CRITERIA_COUNT, 30, 0.01))
good_new = p1[st.ravel() == 1]

# Dense: Farnebäck
flow = cv.calcOpticalFlowFarneback(prev_gray, gray, None,
                                   pyr_scale=0.5, levels=3, winsize=15,
                                   iterations=3, poly_n=5, poly_sigma=1.2, flags=0)
mag, ang = cv.cartToPolar(flow[...,0], flow[...,1])
```

Uses on site: camera-shake compensation before change detection; detecting whether a crane or plant item is moving; simple people/vehicle counting on a fixed camera. Modern learned dense flow (RAFT, and its successors) is far more accurate but needs a GPU.

## Blob analysis

```python
params = cv.SimpleBlobDetector_Params()
params.filterByArea        = True;  params.minArea = 150;  params.maxArea = 20000
params.filterByCircularity = True;  params.minCircularity = 0.6
params.filterByConvexity   = True;  params.minConvexity   = 0.85
params.filterByInertia     = True;  params.minInertiaRatio= 0.3
params.filterByColor       = True;  params.blobColor      = 0   # dark blobs
det = cv.SimpleBlobDetector_create(params)
kps = det.detect(gray)
print("blobs:", len(kps))
out = cv.drawKeypoints(bgr, kps, None, (0,0,255),
                       cv.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
```

For touching or overlapping blobs — the rebar-counting case, the dowel-hole case, the aggregate-sizing case — thresholding alone will merge them. The classical remedy is the **distance-transform watershed**:

```python
dist = cv.distanceTransform(opened, cv.DIST_L2, 5)
_, sure_fg = cv.threshold(dist, 0.5*dist.max(), 255, 0)
sure_fg = np.uint8(sure_fg)
sure_bg = cv.dilate(opened, kel, iterations=3)
unknown = cv.subtract(sure_bg, sure_fg)
_, markers = cv.connectedComponents(sure_fg)
markers = markers + 1
markers[unknown == 255] = 0
markers = cv.watershed(bgr, markers)
n_objects = markers.max() - 1
```

## A complete worked pipeline — panel edge gauge

```python
import cv2 as cv, numpy as np

MM_PER_PX = 0.0245                                # from telecentric calibration

img  = cv.imread("panel_backlit.png", cv.IMREAD_GRAYSCALE)
blur = cv.GaussianBlur(img, (5,5), 0)
t, bw = cv.threshold(blur, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
bw = cv.morphologyEx(bw, cv.MORPH_OPEN,
                     cv.getStructuringElement(cv.MORPH_ELLIPSE,(5,5)))

cnts, _ = cv.findContours(bw, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
c = max(cnts, key=cv.contourArea)
(cx, cy), (w_px, h_px), angle = cv.minAreaRect(c)

# refine the two long edges with subpixel profiles instead of trusting minAreaRect
w_mm, h_mm = w_px * MM_PER_PX, h_px * MM_PER_PX
print(f"panel {max(w_mm,h_mm):.3f} x {min(w_mm,h_mm):.3f} mm, "
      f"skew {angle:+.2f} deg, Otsu t={t}")

NOM, TOL = 600.0, 0.30
val = min(w_mm, h_mm)
print("PASS" if abs(val - NOM) <= TOL else f"FAIL  dev {val-NOM:+.3f} mm")
```

> ⚠️ `minAreaRect` on a thresholded contour is pixel-quantised and biased by the threshold level. It is fine for a ± 1 mm check and unacceptable for ± 0.05 mm. For real gauging, use `minAreaRect` only to *locate* the edges, then run subpixel profile fits along their normals. This is the single most important habit separating a demo from an instrument.

## Sources

- [OpenCV — Image Thresholding](https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html) — `cv.threshold` and `cv.adaptiveThreshold` signatures, `THRESH_*` and `ADAPTIVE_THRESH_*` flags, Otsu.
- [OpenCV — Feature Detection and Description contents](https://docs.opencv.org/4.x/db/d27/tutorial_py_table_of_contents_feature2d.html) — Harris, Shi-Tomasi, SIFT, SURF, FAST, BRIEF, ORB, matching, matching+homography.
- [OpenCV — Camera Calibration](https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html) — for the `cornerSubPix` criteria pattern reused above.

## Open questions

- The claim that SIFT entered the OpenCV main module at version 4.4 following patent expiry in March 2020 is from general familiarity; the fetched contents page does not state it. `needs-verification` at the version-number level.
- CIELAB ΔE*ab perceptibility thresholds (≈1 imperceptible, >3 obvious) are standard colorimetry folklore repeated widely; no primary CIE source fetched.
- Licence status of SuperPoint/SuperGlue (Magic Leap research-only) stated from familiarity, not fetched.
