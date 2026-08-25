---
id: vision.overview
title: Machine vision — domain map, system anatomy and the industrial/academic split
domain: 21_machine_vision
tags: [machine-vision, computer-vision, deep-learning, inspection, domain-map, construction-tech]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "OpenCV camera calibration tutorial (Python)", url: "https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html", publisher: "OpenCV", accessed: 2026-08-25}
  - {title: "Ultralytics supported models", url: "https://docs.ultralytics.com/models/", publisher: "Ultralytics", accessed: 2026-08-25}
  - {title: "Vision Standards", url: "https://www.automate.org/vision/vision-standards/vision-standards", publisher: "A3 (Association for Advancing Automation)", accessed: 2026-08-25}
  - {title: "MVTec HALCON", url: "https://www.mvtec.com/products/halcon", publisher: "MVTec Software GmbH", accessed: 2026-08-25}
  - {title: "SODA: Site Object Detection dAtaset for Deep Learning in Construction", url: "https://arxiv.org/abs/2202.09554", publisher: "arXiv", accessed: 2026-08-25}
related: [vision.imaging, vision.calibration, vision.classical, vision.deep_learning, vision.construction]
---

# Machine vision — domain map, system anatomy and the industrial/academic split

**Summary.** "Machine vision" and "computer vision" name two overlapping traditions that share mathematics but almost nothing else. Industrial machine vision is an engineering discipline about controlling a scene until the measurement becomes trivial — fixed lighting, fixed optics, fixed part presentation, deterministic pass/fail, millisecond cycle times and a PLC on the other end. Academic computer vision is a research discipline about extracting meaning from images you did not control, and since 2012 it has been overwhelmingly a deep-learning discipline. This domain covers both, because the useful modern practitioner works across them: a joinery panel inspector is a classical machine-vision problem, a site-progress tracker is a deep-learning problem, and a photogrammetric as-built survey is neither. Files 01–03 are the physics-and-classical spine, 04–06 the learning-and-deployment spine, 07 the commercial ecosystem, and 08–10 the application, project and learning layers.

## Key facts

| Item | Value | File |
|---|---|---|
| Practical rule of thumb for feature detection | 3–5 pixels across the smallest feature you must *find*; 10+ pixels to *measure* it | `01` |
| Typical industrial reprojection error after good calibration | < 0.3 px RMS; < 0.1 px is achievable with telecentric optics | `02` |
| OpenCV current documented release | 4.13.0 | `03` |
| Ultralytics current YOLO generation | YOLO26 (Jan 2026), NMS-free; YOLO11 (Sep 2024) still recommended for production | `04` |
| COCO detection benchmark metric | mAP@[.50:.95], 80 classes, 118k train images | `05` |
| Jetson Orin Nano AI performance | up to 67 TOPS, 7–25 W | `06` |
| Machine vision interface standards body | A3 (GigE Vision, USB3 Vision, Camera Link, Camera Link HS); JIIA for CoaXPress; EMVA for GenICam | `06` |
| Largest open construction detection dataset (peer-reviewed) | SODA — 19,846 images, 286,201 objects, 15 classes | `08` |

## The two traditions

### Industrial machine vision (roughly 1980 → present)

The governing idea is **scene control**. If you own the lighting, the optics, the part fixture and the trigger, you can reduce a hard perception problem to a threshold and a caliper. A bottle-cap inspection running at 1,200 parts per minute does not use a neural network; it uses a backlight, a telecentric lens, a global-shutter monochrome sensor, a subpixel edge tool and a tolerance band. Its virtues are determinism, traceability, sub-millisecond latency, and the ability to state a false-reject rate to a customer in a contract.

Characteristic properties:

- **Monochrome by default.** Colour costs resolution (Bayer interpolation) and usually adds nothing when the discriminating feature is geometric.
- **The lighting is the algorithm.** Practitioners say this literally. Weeks of algorithm work routinely evaporate when someone swaps a ring light for a backlight.
- **Deterministic, auditable decisions.** In regulated manufacture (pharma, automotive safety parts, aerospace) a stochastic model that cannot explain a reject is a liability.
- **Vendor stacks.** Cognex, Keyence, MVTec, Omron, Basler, Matrox, Teledyne DALSA. Priced per seat/per camera, with GUI configuration aimed at controls engineers rather than programmers (`07`).
- **Cycle-time budgets in milliseconds** and integration to PLC/fieldbus, not to a REST API.

### Academic / modern computer vision (roughly 2012 → present)

The governing idea is **learning from data in scenes you cannot control**. AlexNet's 2012 ImageNet result began a fifteen-year displacement of hand-designed features by learned ones. The characteristic properties are the inverse of the above: colour, uncontrolled illumination, statistical rather than deterministic performance, open-source stacks (PyTorch, OpenCV, Ultralytics, Detectron2), benchmark-driven progress, and models measured in mAP and IoU rather than in false-reject parts per million.

This is the tradition that matters for construction, because a building site is the definition of an uncontrolled scene: no fixture, no repeatable lighting, weather, dust, occlusion, and a subject that changes daily by design.

### Where they meet

The interesting engineering now lives in the seam. HALCON and Cognex both ship deep-learning tools inside classical toolchains. Conversely, the best deep-learning deployments in industry are hybrids: a CNN localises the region of interest, then a classical subpixel caliper makes the actual measurement, because a network will not give you 0.02 mm and a caliper will. **A good default: use learning for *where* and *what*, use classical geometry for *how big* and *how far*.**

## Anatomy of a vision system

Every vision system, from a €400 smart camera to a drone photogrammetry pipeline, has the same seven parts. Failures are almost always in parts 1–3, and almost never in part 5, which is where inexperienced teams spend their time.

1. **Illumination.** Wavelength, geometry, intensity, and — critically — *stability over time*. Ambient light is a defect, not a resource. Covered in `01`.
2. **Optics.** Lens focal length, aperture, working distance, depth of field, distortion, and whether the lens is entocentric or telecentric. Sets your achievable measurement uncertainty before a single pixel is read. `01`.
3. **Sensor and camera.** Resolution, pixel size, shutter type, dynamic range, quantum efficiency, bit depth, interface. `01`, `06`.
4. **Trigger and synchronisation.** Hardware trigger from an encoder or proximity sensor, strobe timing, exposure window. In moving-part applications this determines motion blur, which determines everything else.
5. **Processing.** Classical pipeline (`03`), learned model (`04`), or hybrid. Runs on a smart camera, an industrial PC, an edge module or a server.
6. **Decision and output.** Pass/fail, measurement value, class label, coordinate handoff to a robot. Interfaces: digital I/O, Ethernet/IP, PROFINET, Modbus TCP, OPC UA, MQTT. `06`.
7. **Human factors.** Result logging, image archiving for failure forensics, re-teaching procedure, and who fixes it at 03:00. Systems die here more often than in the algorithm.

> ⚠️ The single most common cause of a machine-vision project failing in the field is unmanaged ambient light — sunlight through a roller door, a maintenance torch, a seasonal change in the shed's light level. Enclose the inspection station or use a strobe far brighter than ambient plus a matched bandpass filter.

## The domain map

**Physics and geometry layer.**
`01_imaging-fundamentals.md` — light, illumination geometries, lens equations, sensor properties, and the arithmetic of choosing a camera and lens for a stated field of view and tolerance. This is the file to read before buying anything.
`02_camera-calibration-and-geometry.md` — the pinhole model, intrinsics/extrinsics, distortion, checkerboard calibration in OpenCV, homography, epipolar geometry, stereo, depth sensing, photogrammetry and structure-from-motion, and what metric accuracy you may honestly claim.

**Algorithm layer.**
`03_classical-image-processing.md` — the toolkit that still solves most controlled-scene problems: colour spaces, thresholding, morphology, filtering, edges, contours, Hough, template matching, SIFT/ORB/AKAZE, optical flow, blob analysis. Runnable OpenCV Python throughout.
`04_deep-learning-vision.md` — CNN fundamentals, the architecture lineage, Vision Transformers, and the task families with current model names and where to obtain weights.

**Practice layer.**
`05_training-and-data.md` — datasets, annotation tools and formats, splits, augmentation, transfer learning, losses, metrics, imbalance, active learning, small-team MLOps.
`06_deployment-and-hardware.md` — edge vs cloud, Jetson/Coral/OpenVINO/Pi, ONNX and TensorRT, quantisation, latency budgeting, industrial camera interfaces, PLC integration, ruggedising for dust and heat.
`07_industrial-vision-platforms.md` — the commercial and open ecosystems compared on cost, capability and lock-in.

**Application layer.**
`08_construction-applications.md` — the honest state of vision in construction and joinery, application by application, with maturity, accuracy and existing products.
`09_practical-projects.md` — four fully specified project blueprints with architecture, code skeletons and data requirements.
`10_resources-and-learning.md` — a tested register of books, courses, conferences, datasets and repositories.

## Why this domain belongs in a construction knowledge base

Three distinct value routes, in descending order of maturity:

1. **Metrology and survey.** Photogrammetry and laser scanning are already routine, already accurate to stated tolerances, and already commercially supported. Scan-to-BIM, drone volumetrics for earthworks, and as-built verification are the least speculative uses of vision on a site. See `02` and `08`.
2. **Factory-side inspection.** Joinery, panel production, timber grading and CNC alignment are *manufacturing* problems that happen to serve construction. They live in a controlled shop where classical machine vision works exactly as it does in any other factory, and where an inspection cell has a computable payback. See `08` and the panel-inspector blueprint in `09`.
3. **Site understanding.** Progress monitoring, PPE compliance, exclusion-zone monitoring, material tracking. Genuinely useful, genuinely commercialised (Buildots, OpenSpace, Doxel, Disperse, viAct and others), but with performance that is statistical, dataset-dependent, and frequently over-claimed in marketing. Treat published accuracy figures as best-case. See `08`.

A fourth route — using vision to close the loop on robotic construction — remains largely research. It is flagged as such where it appears.

## Vocabulary that trips people up

- **Machine vision vs computer vision vs image processing.** Image processing transforms images into images. Computer vision extracts descriptions from images. Machine vision is computer vision plus the hardware, lighting, integration and industrial reliability requirements.
- **Resolution.** Three different things get called this: sensor pixel count (e.g. 5 MP), spatial sampling (mm per pixel), and optical resolving power (line pairs per millimetre, limited by the lens MTF and diffraction). Confusing them causes most specification errors. `01` separates them.
- **Accuracy vs repeatability vs resolution.** A system can resolve 0.01 mm, repeat to 0.02 mm and be accurate to only 0.2 mm because it was calibrated against a poor artefact. State all three.
- **Detection vs segmentation vs classification.** A classifier says "this image contains a crack". A detector says "there is a crack in this box". A segmenter says "these pixels are crack", which is the only one that lets you measure crack width. Choose by what you must *do* with the answer. `04`.
- **mAP.** A benchmark aggregate, not an operating point. You deploy at a specific confidence threshold with a specific precision and recall; mAP tells you almost nothing about how the system behaves there. `05`.

## Sources

- [OpenCV camera calibration tutorial (Python)](https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html) — OpenCV 4.13.0 documentation.
- [Ultralytics — supported models](https://docs.ultralytics.com/models/) — YOLO26/YOLO11/SAM/RT-DETR family list.
- [A3 Vision Standards](https://www.automate.org/vision/vision-standards/vision-standards) — GigE Vision, USB3 Vision, Camera Link, Camera Link HS.
- [MVTec HALCON product page](https://www.mvtec.com/products/halcon).
- [SODA: Site Object Detection dAtaset for Deep Learning in Construction (arXiv:2202.09554)](https://arxiv.org/abs/2202.09554).

## Open questions

- No open, peer-reviewed benchmark exists for *joinery-specific* defect detection; the timber-grading literature is dominated by proprietary mill systems whose accuracy claims are unverifiable from outside. Flagged throughout `08`.
- Vendor progress-monitoring accuracy claims (Buildots, Doxel, OpenSpace) are marketing figures; no independent third-party evaluation was located. Treated as `needs-verification` in `08`.

