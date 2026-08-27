---
id: vision.projects
title: Four worked project blueprints — from site photos to a joinery panel gauge
domain: 21_machine_vision
tags: [project-blueprint, change-detection, ppe-detection, jetson, photogrammetry, colmap, panel-inspection, tolerance-budget, runnable-code]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "COLMAP documentation", url: "https://colmap.github.io/", publisher: "COLMAP", accessed: 2026-08-25}
  - {title: "Ultralytics — detection dataset format", url: "https://docs.ultralytics.com/datasets/detect/", publisher: "Ultralytics", accessed: 2026-08-25}
  - {title: "OpenCV camera calibration tutorial", url: "https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html", publisher: "OpenCV 4.13.0", accessed: 2026-08-25}
  - {title: "NVIDIA Jetson Modules", url: "https://developer.nvidia.com/embedded/jetson-modules", publisher: "NVIDIA", accessed: 2026-08-25}
  - {title: "SODA construction dataset", url: "https://arxiv.org/abs/2202.09554", publisher: "arXiv", accessed: 2026-08-25}
related: [vision.classical, vision.calibration, vision.deep_learning, vision.deployment, vision.construction]
---

# Four worked project blueprints

**Summary.** Four projects a competent developer could implement, each specified far enough to start work on Monday: architecture, data requirements, code skeletons, acceptance criteria and the failure modes to expect. They are deliberately spread across the difficulty range — (a) a site progress classifier and change detector needing no labelled data to start; (b) a PPE detection pipeline on a Jetson; (c) photogrammetric as-built capture from phone photos with a real accuracy assessment; (d) a joinery panel dimension inspector with a stated tolerance budget. All code is a skeleton, not a product: it is complete enough to run and deliberately omits logging, error handling and configuration management.

---

## Project A — Site progress photo classifier and change detector

**Goal.** Given a stream of site photographs from repeated positions, (1) reject unusable images, (2) group them by viewpoint, (3) highlight what changed since the last visit, and (4) optionally classify the construction stage of each viewpoint.

**Why start here.** Stages 1–3 need **no labelled data at all**. Stage 4 needs only a few hundred labels.

### Architecture

```
photos/ ─► [1 quality gate] ─► [2 viewpoint clustering] ─► [3 registration + change] ─► report
                                        │
                                        └─► [4 stage classifier (optional, supervised)]
```

### Data requirements

- 200+ photos per viewpoint over time, ideally from marked positions (spray a cross on the slab, or fix a phone holder).
- For stage 4: 50–150 labelled images per stage class per viewpoint type. Classes for a superstructure: `formwork`, `rebar_placed`, `poured`, `stripped`, `blockwork`, `plastered`, `first_fix`, `finished`.
- EXIF preserved — timestamp and, where available, GPS.

### Code

```python
# --- 1. Quality gate -----------------------------------------------------
import cv2 as cv, numpy as np

def quality(path, blur_min=80.0, dark=40, bright=215):
    img = cv.imread(path)
    if img is None:
        return False, "unreadable"
    g = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    fm = cv.Laplacian(g, cv.CV_64F).var()          # variance of Laplacian
    mu = g.mean()
    if fm < blur_min:      return False, f"blurry ({fm:.0f})"
    if mu < dark:          return False, "underexposed"
    if mu > bright:        return False, "overexposed"
    return True, "ok"
```

`blur_min` must be calibrated on your own camera — run the gate over 200 known-good and known-bad images and pick the separating value.

```python
# --- 2. Viewpoint clustering with a self-supervised embedding ------------
import torch, timm, numpy as np
from PIL import Image
from sklearn.cluster import DBSCAN

dev   = "cuda" if torch.cuda.is_available() else "cpu"
model = timm.create_model("vit_small_patch14_dinov2.lvd142m",
                          pretrained=True, num_classes=0).eval().to(dev)
cfg   = timm.data.resolve_model_data_config(model)
tf    = timm.data.create_transform(**cfg, is_training=False)

@torch.no_grad()
def embed(paths, bs=16):
    out = []
    for i in range(0, len(paths), bs):
        batch = torch.stack([tf(Image.open(p).convert("RGB"))
                             for p in paths[i:i+bs]]).to(dev)
        f = model(batch)
        out.append(torch.nn.functional.normalize(f, dim=1).cpu().numpy())
    return np.concatenate(out)

E   = embed(good_paths)
lab = DBSCAN(eps=0.35, min_samples=3, metric="cosine").fit_predict(E)
# lab == -1 are one-off shots; every other label is a recurring viewpoint
```

```python
# --- 3. Registration and change detection --------------------------------
def register(ref_bgr, new_bgr, min_inliers=25):
    """Align new -> ref with an AKAZE + RANSAC homography."""
    a, b = (cv.cvtColor(x, cv.COLOR_BGR2GRAY) for x in (ref_bgr, new_bgr))
    det  = cv.AKAZE_create()
    k1, d1 = det.detectAndCompute(a, None)
    k2, d2 = det.detectAndCompute(b, None)
    if d1 is None or d2 is None:
        return None, 0
    bf = cv.BFMatcher(cv.NORM_HAMMING)
    good = [m for m, n in bf.knnMatch(d2, d1, k=2) if m.distance < 0.75*n.distance]
    if len(good) < min_inliers:
        return None, len(good)
    src = np.float32([k2[m.queryIdx].pt for m in good]).reshape(-1,1,2)
    dst = np.float32([k1[m.trainIdx].pt for m in good]).reshape(-1,1,2)
    H, mask = cv.findHomography(src, dst, cv.RANSAC, 4.0)
    if H is None:
        return None, len(good)
    return cv.warpPerspective(new_bgr, H, (ref_bgr.shape[1], ref_bgr.shape[0])), int(mask.sum())

def change_map(ref_bgr, aligned_bgr, min_area_frac=0.0008):
    """Illumination-normalised difference -> change regions."""
    cl = cv.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    a  = cl.apply(cv.cvtColor(ref_bgr,     cv.COLOR_BGR2GRAY))
    b  = cl.apply(cv.cvtColor(aligned_bgr, cv.COLOR_BGR2GRAY))
    a  = cv.GaussianBlur(a, (7,7), 0); b = cv.GaussianBlur(b, (7,7), 0)
    d  = cv.absdiff(a, b)
    _, m = cv.threshold(d, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
    k = cv.getStructuringElement(cv.MORPH_ELLIPSE, (9,9))
    m = cv.morphologyEx(m, cv.MORPH_OPEN,  k)
    m = cv.morphologyEx(m, cv.MORPH_CLOSE, k)
    min_area = min_area_frac * m.size
    cnts, _ = cv.findContours(m, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    return [cv.boundingRect(c) for c in cnts if cv.contourArea(c) > min_area], m
```

```python
# --- 4. Optional stage classifier ----------------------------------------
# Freeze the DINOv2 backbone, train a logistic head on ~100 images/class.
from sklearn.linear_model import LogisticRegression
clf = LogisticRegression(max_iter=2000, C=1.0, class_weight="balanced")
clf.fit(embed(train_paths), train_labels)          # X is (N, 384) for ViT-S/14
print("val acc:", clf.score(embed(val_paths), val_labels))
```

### Acceptance criteria

- Quality gate rejects > 90 % of genuinely unusable images with < 5 % false rejects on a hand-labelled set of 200.
- Viewpoint clustering produces clusters a human agrees with on 90 % of images.
- Change detection: on 30 manually annotated before/after pairs, ≥ 80 % of real changes produce a flagged region and ≤ 3 spurious regions per image.
- Stage classifier ≥ 85 % top-1 on a **temporally held-out** test month.

### Failure modes to expect

Parallax defeats a single homography whenever the camera position (not just orientation) moves — that is the dominant cause of spurious change regions. Mitigate by fixing the capture position, by masking the near foreground, or by moving to a full 3D approach (Project C). Sun/shadow movement is the second cause; CLAHE helps, capture at a consistent time of day helps more.

---

## Project B — PPE / hard-hat detection on a Jetson

**Goal.** A fixed camera at a site gate or a work zone detects people and flags anyone without a hard hat, running entirely on the edge, writing events to a local database and raising an alert.

### Architecture

```
IP camera (RTSP) ─► GStreamer/NVDEC ─► preprocess (GPU) ─► YOLO11s TensorRT FP16
        │                                                          │
        └──────────────────────────────────────────► ByteTrack ────┤
                                                                   ▼
                                          temporal vote → event → SQLite + MQTT alert
                                                                   │
                                       1 % of frames + all events ─┴─► labelling pool
```

**Hardware.** Jetson **Orin Nano 8 GB** (up to 67 TOPS, 7–25 W) for one to two 1080p streams; **Orin NX 16 GB** (up to 157 TOPS) for four to six. IP67 enclosure with a sun shield, PoE camera with a global-shutter or good rolling-shutter sensor, 4G/LTE or site Wi-Fi backhaul, mesh VPN for remote access.

**Camera siting is the whole ballgame.** Mount so that a person at the far end of the monitored area is at least **120 pixels tall**, angled 20–35° below horizontal so heads are seen from above-front rather than in silhouette, avoiding a view directly into the morning or evening sun.

### Data requirements

| Item | Target |
|---|---|
| Images from **your** cameras | 3,000–6,000 |
| Instances per class | ≥ 1,500 person, ≥ 800 hardhat, ≥ 400 no-hardhat |
| Background-only images | 10–20 % of the set |
| Conditions covered | dawn/midday/dusk, sun/cloud/rain, dust, backlit, all helmet colours in use |
| Public bootstrap | SODA (19,846 images, 286,201 objects, 15 classes) and Roboflow Universe hard-hat sets — **for pretraining only**, then fine-tune on your own data |

Classes: `person`, `hardhat`, `no-hardhat`, `vest`, `no-vest`. Modelling `no-hardhat` as an explicit class beats inferring it from the absence of a `hardhat` box, because absence is also what occlusion looks like.

### Code

```python
# --- train ---------------------------------------------------------------
from ultralytics import YOLO
m = YOLO("yolo11s.pt")
m.train(data="ppe.yaml", epochs=150, imgsz=960, batch=16, device=0,
        optimizer="AdamW", lr0=0.001, warmup_epochs=3,
        close_mosaic=10, patience=25,
        hsv_h=0.010, hsv_s=0.6, hsv_v=0.5,     # site light varies hugely
        degrees=5, translate=0.1, scale=0.5, fliplr=0.5, flipud=0.0,
        project="runs/ppe", name="v1")

# --- export on the Jetson itself ----------------------------------------
YOLO("runs/ppe/v1/weights/best.pt").export(format="engine", imgsz=960, half=True)
```

```python
# --- runtime -------------------------------------------------------------
import collections, sqlite3, time
import cv2 as cv
from ultralytics import YOLO

model = YOLO("best.engine", task="detect")
NAMES = {0:"person", 1:"hardhat", 2:"no-hardhat", 3:"vest", 4:"no-vest"}

RTSP = ("rtspsrc location=rtsp://user:pw@10.0.0.20/stream latency=100 ! "
        "rtph264depay ! h264parse ! nvv4l2decoder ! "
        "nvvidconv ! video/x-raw,format=BGRx ! videoconvert ! "
        "video/x-raw,format=BGR ! appsink drop=1 max-buffers=2")
cap = cv.VideoCapture(RTSP, cv.CAP_GSTREAMER)

VOTE_N, VOTE_K, COOLDOWN = 15, 10, 60.0        # K of N frames, then cooldown
hist   = collections.defaultdict(lambda: collections.deque(maxlen=VOTE_N))
last   = {}
db = sqlite3.connect("events.db")
db.execute("CREATE TABLE IF NOT EXISTS ev(ts REAL, tid INT, kind TEXT, conf REAL)")

while True:
    ok, frame = cap.read()
    if not ok:
        time.sleep(0.2); continue

    res = model.track(frame, persist=True, tracker="bytetrack.yaml",
                      conf=0.35, iou=0.5, imgsz=960, verbose=False)[0]
    if res.boxes.id is None:
        continue

    for box, cid, tid, cf in zip(res.boxes.xyxy.cpu().numpy(),
                                 res.boxes.cls.int().cpu().numpy(),
                                 res.boxes.id.int().cpu().numpy(),
                                 res.boxes.conf.cpu().numpy()):
        name = NAMES[int(cid)]
        if name not in ("hardhat", "no-hardhat"):
            continue
        hist[int(tid)].append(name)

        h = hist[int(tid)]
        if len(h) == VOTE_N and sum(x == "no-hardhat" for x in h) >= VOTE_K:
            now = time.time()
            if now - last.get(int(tid), 0) > COOLDOWN:
                last[int(tid)] = now
                db.execute("INSERT INTO ev VALUES (?,?,?,?)",
                           (now, int(tid), "no-hardhat", float(cf)))
                db.commit()
                cv.imwrite(f"events/{int(now)}_{int(tid)}.jpg", frame)
                # publish MQTT / call webhook here
```

**The temporal vote is not optional.** A single-frame decision on a moving person produces a stream of false alarms; requiring 10 of 15 consecutive frames on a tracked identity, plus a cooldown, converts a noisy detector into a usable alerting system. This single mechanism typically cuts false alarms by an order of magnitude.

### Acceptance criteria

- ≥ 90 % recall and ≥ 85 % precision on **event level** (not frame level) over a held-out week from the same camera.
- End-to-end p99 latency < 500 ms from frame capture to event write.
- Sustained ≥ 12 FPS at 960 px on the target Jetson **after 4 hours of thermal soak in the enclosure**.
- Zero unrecovered crashes over a 14-day soak test.

### Failure modes and governance

Small subjects, back-lighting at dawn and dusk, occlusion by plant, helmets carried in hand, and non-worker members of the public. Expect to re-train quarterly with mined hard negatives (`05`).

> ⚠️ Before deployment, resolve with the workforce and with legal advice: the lawful basis for processing images of identifiable workers, retention periods, who may view events, and an explicit statement that the system is a management-information tool and **not** a safety control. **[ZA]** POPIA obligations apply. **[NA]** Confirm current Namibian data-protection law status. Deploying worker-monitoring vision without prior consultation reliably produces industrial-relations damage that exceeds any safety benefit.

---

## Project C — Photogrammetric as-built capture from phone photos

**Goal.** Reconstruct a building or room from ordinary phone photographs, scaled to real metres, with a **measured and reported** accuracy rather than an assumed one.

### Architecture

```
capture protocol ─► COLMAP feature_extractor ─► matcher ─► mapper (sparse SfM)
                                                            │
                             scale from control ◄───────────┤
                                                            ▼
                    image_undistorter ─► patch_match_stereo ─► stereo_fusion ─► .ply
                                                            │
                                       accuracy report ◄────┴─ check-point comparison
```

### Data requirements and capture protocol

- **150–400 photos** for a room; 400–1,200 for a small building exterior.
- **70–80 % overlap** between consecutive frames. Move in small steps; do not pivot on the spot for a 3D reconstruction (pure rotation gives no parallax and no geometry).
- **Lock exposure and focus** on the phone. Autofocus changes the intrinsics between frames and forces per-image self-calibration, which weakens the solve.
- Shoot in **even light** — overcast outside, lights on and blinds closed inside. Avoid hard shadow boundaries, which move and break matching.
- Include **oblique as well as square-on** views of each surface; add a second loop at a different height.
- **Scale reference is mandatory.** Place at least **three** scale bars or coded targets of measured length, distributed through the volume — not all in one corner. A 1 m aluminium bar with printed ArUco markers at each end, measured with a steel tape or a total station, is sufficient and costs nothing.
- **Check points:** measure at least **8 additional distances** (wall-to-wall, floor-to-ceiling, opening widths) with a laser distance meter, and **exclude them from the scaling**. These are what you report accuracy against.

### Code

```bash
#!/usr/bin/env bash
set -euo pipefail
P=$(pwd)
colmap feature_extractor \
  --database_path "$P/db.db" --image_path "$P/images" \
  --ImageReader.single_camera 1 \
  --ImageReader.camera_model OPENCV \
  --SiftExtraction.max_image_size 3200

colmap exhaustive_matcher --database_path "$P/db.db"      # <500 images
# colmap vocab_tree_matcher --database_path "$P/db.db" \
#        --VocabTreeMatching.vocab_tree_path vocab_tree.bin   # larger sets

mkdir -p "$P/sparse"
colmap mapper --database_path "$P/db.db" --image_path "$P/images" \
              --output_path "$P/sparse"

colmap image_undistorter --image_path "$P/images" \
  --input_path "$P/sparse/0" --output_path "$P/dense" --output_type COLMAP
colmap patch_match_stereo --workspace_path "$P/dense" \
  --PatchMatchStereo.geom_consistency true
colmap stereo_fusion --workspace_path "$P/dense" \
  --output_path "$P/dense/fused.ply"

colmap model_converter --input_path "$P/sparse/0" \
  --output_path "$P/sparse/0_txt" --output_type TXT
```

```python
# --- scale the reconstruction and report accuracy ------------------------
import numpy as np, pycolmap

rec = pycolmap.Reconstruction("sparse/0")

def dist(p3d_a, p3d_b):
    return float(np.linalg.norm(rec.points3D[p3d_a].xyz - rec.points3D[p3d_b].xyz))

# (a) SCALE — from measured scale bars only
scale_bars = [(id_a1, id_b1, 1.000), (id_a2, id_b2, 1.000), (id_a3, id_b3, 0.500)]
ratios = [true_m / dist(a, b) for a, b, true_m in scale_bars]
s = float(np.median(ratios))
print(f"scale = {s:.6f} m/unit   spread = {np.std(ratios)/np.mean(ratios)*100:.2f} %")

# (b) ACCURACY — on check points EXCLUDED from (a)
check = [(id_c1, id_d1, 3.214), (id_c2, id_d2, 2.487)]   # laser-measured metres
errs = np.array([s*dist(a, b) - true_m for a, b, true_m in check])
print(f"n={len(errs)}  mean bias {errs.mean()*1000:+.1f} mm  "
      f"RMSE {np.sqrt((errs**2).mean())*1000:.1f} mm  "
      f"max |e| {np.abs(errs).max()*1000:.1f} mm")
```

### Acceptance criteria

- ≥ 95 % of input images registered by the mapper.
- Mean reprojection error < 1.0 px.
- Scale-bar ratio spread < 0.5 %.
- **Check-point RMSE < 15 mm over a 6 m room**, reported alongside n, the bias and the maximum error. Anything reported without check points withheld from the solve is not an accuracy statement.

### Failure modes

Textureless white walls (fix: project a pattern with a cheap laser or torch through a gobo, or accept mesh gaps); repetitive facades and tiling (fix: add wide-baseline frames and rely on geometric verification); rolling-shutter distortion while walking (fix: pause for each shot, or model rolling shutter); glass and mirrors (unfixable — mask them out); drift on a long corridor without loop closure (fix: return to the start and re-shoot the first few frames).

**Do not present a photogrammetric model as a survey deliverable without the accuracy report.** The whole professional distinction between a nice 3D model and a survey is that sentence.

---

## Project D — Joinery panel dimension inspector

**Goal.** Measure length, width, diagonal (squareness) and edge straightness of finished panels up to 1200 × 600 mm to **± 0.3 mm**, at a rate of one panel per 10 seconds, using classical CV with no machine learning.

### Architecture

```
              ┌──── camera 1 ─┐  ┌──── camera 2 ─┐
   backlight  │   telecentric │  │  telecentric  │   ← rigid steel frame,
   panel  ────┼───────────────┼──┼───────────────┼──   4 corner stations
              └──── camera 3 ─┘  └──── camera 4 ─┘
                            │
       trigger (photoeye) ──┴─► industrial PC (OpenVINO/OpenCV)
                                        │
                                pass/fail + measurement → Modbus TCP → PLC
                                        │
                                   SQLite + label printer
```

### Physical design (from `01`)

- Four cameras, each viewing one corner over a ~60 × 50 mm field through a **0.14× telecentric lens**, **backlit** from below with a diffuse red (625 nm) LED panel and a matched bandpass filter on each lens.
- 5 MP global-shutter monochrome sensors (2448 × 2048, 3.45 µm).
- **Sampling: 60 mm / 2448 px = 0.0245 mm/px.**
- Panel supported on a flat platen with hold-downs; frame in welded and stress-relieved steel; cameras on kinematic mounts.
- A **calibration artefact** — a dimensionally certified panel or a set of gauge blocks — checked at the start of every shift.

### Tolerance budget

The requirement is ± 0.3 mm. Combining independent contributions in quadrature:

| Source | Contribution (1σ, mm) | Reasoning |
|---|---|---|
| Subpixel edge location | 0.010 | 0.0245 mm/px ÷ 5 (conservative subpixel factor), two edges |
| Camera pixel/lens residual after calibration | 0.020 | Telecentric, calibrated, low distortion |
| Calibration artefact uncertainty | 0.050 | Certified panel at ± 0.05 mm |
| Frame thermal expansion | 0.144 | 1.2 m steel × 12 µm/m/°C × 10 °C swing |
| Panel support / bow / hold-down | 0.100 | Realistic for a 16 mm panel on a flat platen |
| Panel edge quality (edgeband, chipping) | 0.080 | The physical edge is not a mathematical line |
| Repeatability of part placement | 0.030 | Telecentric optics largely remove this |
| **RSS total (1σ)** | **≈ 0.20 mm** | |
| **Expanded, k = 2 (≈95 %)** | **≈ 0.40 mm** | |

> ⚠️ **Read the budget honestly: at k = 2 this design does *not* meet ± 0.3 mm.** It meets ± 0.3 mm at roughly 1.5σ (≈87 % confidence). To reach ± 0.3 mm at k = 2 you must attack the two dominant terms — **thermal** and **panel support**. Options: control the workshop temperature to ± 3 °C (thermal term falls to 0.043 mm); build the frame from Invar or add a temperature sensor and a compensation coefficient; improve the platen flatness and vacuum-hold the panel. With shop temperature controlled to ± 3 °C and improved support (0.05 mm), the RSS falls to ≈ 0.12 mm and k = 2 gives ± 0.24 mm. **This is the entire value of writing the budget: it tells you to spend money on the frame and the room, not on cameras.**

### Code

```python
import cv2 as cv, numpy as np, sqlite3, time
from pymodbus.client import ModbusTcpClient

MM_PER_PX = {1: 0.024510, 2: 0.024498, 3: 0.024503, 4: 0.024515}  # per-camera
NOMINAL   = {"length": 1200.0, "width": 600.0}
TOL       = 0.30

def corner_point(img, cam_id):
    """Locate the panel corner in one backlit view, to subpixel accuracy.

    Backlit: panel is DARK, background is BRIGHT. Fit a line to each of the two
    visible edges by subpixel profiles, then intersect them.
    """
    blur = cv.GaussianBlur(img, (5, 5), 0)
    _, bw = cv.threshold(blur, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)
    bw = cv.morphologyEx(bw, cv.MORPH_OPEN,
                         cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5)))
    cnts, _ = cv.findContours(bw, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    c = max(cnts, key=cv.contourArea)

    # coarse corner from the rotated bounding box, then refine each edge
    box = cv.boxPoints(cv.minAreaRect(c)).astype(np.float32)
    lines = []
    for axis in (0, 1):                       # the two edges meeting at the corner
        pts = sample_edge_subpixel(blur, c, axis)   # see below
        vx, vy, x0, y0 = cv.fitLine(pts, cv.DIST_HUBER, 0, 0.01, 0.01).ravel()
        lines.append((vx, vy, x0, y0))
    return intersect(*lines), lines

def sample_edge_subpixel(gray, contour, axis, n=200, half=8):
    """Sample intensity profiles normal to a nominally straight edge and
    return subpixel edge positions. `half` = profile half-length in pixels."""
    pts = []
    sel = contour[:, 0, :]
    idx = np.linspace(0, len(sel) - 1, n).astype(int)
    for i in idx:
        x, y = sel[i]
        if axis == 0:                                  # vertical edge: scan in x
            prof = gray[y, max(x-half,0):x+half].astype(np.float64)
            if len(prof) < 2*half: continue
            pts.append([max(x-half,0) + subpixel_edge_1d(prof), y])
        else:                                          # horizontal edge: scan in y
            prof = gray[max(y-half,0):y+half, x].astype(np.float64)
            if len(prof) < 2*half: continue
            pts.append([x, max(y-half,0) + subpixel_edge_1d(prof)])
    return np.array(pts, np.float32)

def subpixel_edge_1d(profile):
    g = np.gradient(profile)
    i = int(np.argmax(np.abs(g)))
    if i == 0 or i >= len(g) - 1: return float(i)
    a, b, c = abs(g[i-1]), abs(g[i]), abs(g[i+1])
    den = a - 2*b + c
    return i + (0.0 if den == 0 else 0.5*(a - c)/den)

def intersect(l1, l2):
    (vx1, vy1, x1, y1), (vx2, vy2, x2, y2) = l1, l2
    A = np.array([[vx1, -vx2], [vy1, -vy2]])
    b = np.array([x2 - x1, y2 - y1])
    t = np.linalg.solve(A, b)
    return np.array([x1 + t[0]*vx1, y1 + t[0]*vy1])

# --- frame calibration: corner positions in a shared frame coordinate system
FRAME = np.load("frame_calibration.npz")     # per-camera R,t into frame mm
def to_frame_mm(pt_px, cam_id):
    return FRAME[f"A{cam_id}"] @ np.append(pt_px * MM_PER_PX[cam_id], 1.0)

def inspect(images):
    P = {cid: to_frame_mm(corner_point(img, cid)[0], cid)
         for cid, img in images.items()}
    length = np.linalg.norm(P[1] - P[2])
    width  = np.linalg.norm(P[1] - P[4])
    d1     = np.linalg.norm(P[1] - P[3])
    d2     = np.linalg.norm(P[2] - P[4])
    return {"length": length, "width": width,
            "diag_diff": abs(d1 - d2),
            "pass": (abs(length - NOMINAL["length"]) <= TOL and
                     abs(width  - NOMINAL["width"])  <= TOL and
                     abs(d1 - d2) <= 2*TOL)}

plc = ModbusTcpClient("192.168.1.50", port=502)
def report(r):
    plc.write_coil(0, bool(r["pass"]), slave=1)
    plc.write_registers(100, [int(r["length"]*100), int(r["width"]*100),
                              int(r["diag_diff"]*100)], slave=1)
```

### Shift-start verification routine

```python
def verify_with_artefact(cert_length, cert_width, n=10):
    """Measure the certified artefact n times. Fail the cell if bias or
    repeatability exceed limits — catches drift, dust and knocks."""
    L = [inspect(grab_all())["length"] for _ in range(n)]
    bias, sd = np.mean(L) - cert_length, np.std(L, ddof=1)
    ok = abs(bias) <= 0.10 and sd <= 0.05
    print(f"bias {bias:+.3f} mm  sd {sd:.3f} mm  -> {'OK' if ok else 'LOCK OUT'}")
    return ok
```

### Acceptance criteria

- **Gauge R&R study** (10 panels × 3 operators × 3 repeats): repeatability + reproducibility consuming < 20 % of the ± 0.3 mm tolerance band.
- Bias against the certified artefact < 0.10 mm, stable over a shift.
- Cycle time < 10 s per panel including handling.
- Correct pass/fail on a set of 20 deliberately out-of-tolerance panels made to known deviations of 0.2, 0.4, 0.6 and 1.0 mm.

### Failure modes

MDF dust on the front windows (scheduled cleaning plus the shift-start verification catches it); dark edgebanding against a dark background (backlight makes this a non-issue, which is why backlight was specified); panel bow lifting a corner off the platen (hold-downs, and reject on an out-of-range corner height); thermal drift through the day (the shift-start check catches gross drift, temperature compensation catches the rest); and gloss-black high-pressure laminate creating a specular reflection of the backlight around the edge (add a matt shroud).

---

## Sources

- [COLMAP](https://colmap.github.io/) — SfM and MVS pipeline, CLI stages used in Project C.
- [Ultralytics — detection dataset format](https://docs.ultralytics.com/datasets/detect/) — YOLO label and YAML structure used in Project B.
- [OpenCV — camera calibration](https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html) — calibration functions underlying Projects C and D.
- [NVIDIA Jetson Modules](https://developer.nvidia.com/embedded/jetson-modules) — Orin Nano 67 TOPS / 7–25 W, Orin NX 157 TOPS.
- [SODA construction dataset (arXiv:2202.09554)](https://arxiv.org/abs/2202.09554) — bootstrap data for Project B.

## Open questions

- **All code here is a skeleton and has not been executed.** In particular Project D assumes a `frame_calibration.npz` produced by a frame-level calibration procedure that is described but not implemented, and Project C's `pycolmap` point-ID lookups assume you have identified your scale-bar targets in the reconstruction (in practice, use coded ArUco targets and `cv.aruco` detection to automate this).
- The tolerance budget in Project D uses **assumed** values for platen flatness, panel bow and edge quality. These must be measured on real panels before the design is committed.
- Steel thermal expansion is taken as 12 µm/m/°C — verify against the actual alloy.
- Accuracy and recall targets in the acceptance criteria are proposed engineering targets, not measured results.
