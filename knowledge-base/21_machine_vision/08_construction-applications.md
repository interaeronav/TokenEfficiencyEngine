---
id: vision.construction
title: Vision in construction and joinery — applications, maturity and honest accuracy
domain: 21_machine_vision
tags: [construction-tech, progress-monitoring, 4d-bim, ppe-detection, crack-detection, rebar-counting, scan-to-bim, photogrammetry, drone-survey, timber-grading, cnc-vision, panel-inspection, joinery-qc]
jurisdiction: global
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "SODA: Site Object Detection dAtaset for Deep Learning in Construction", url: "https://arxiv.org/abs/2202.09554", publisher: "arXiv", accessed: 2026-08-25}
  - {title: "SDNET2018: A concrete crack image dataset for machine learning applications", url: "https://digitalcommons.usu.edu/all_datasets/48/", publisher: "Utah State University", accessed: 2026-08-25}
  - {title: "OpenSpace", url: "https://www.openspace.ai/", publisher: "OpenSpace Labs", accessed: 2026-08-25}
  - {title: "Buildots", url: "https://www.buildots.com/", publisher: "Buildots", accessed: 2026-08-25}
  - {title: "Disperse", url: "https://www.disperse.io/", publisher: "Disperse", accessed: 2026-08-25}
  - {title: "viAct", url: "https://www.viact.ai/", publisher: "viAct", accessed: 2026-08-25}
  - {title: "MiCROTEC", url: "https://www.microtec.com/", publisher: "MiCROTEC", accessed: 2026-08-25}
  - {title: "COLMAP", url: "https://colmap.github.io/", publisher: "COLMAP", accessed: 2026-08-25}
related: [vision.calibration, vision.deep_learning, vision.projects, joinery.overview]
---

# Vision in construction and joinery — applications, maturity and honest accuracy

**Summary.** This file assesses fifteen specific applications of vision in construction, surveying and joinery. For each: what it actually does, its maturity, realistic accuracy, the commercial products that exist today, and what it would take to build. The organising honesty is that these applications are not equally real. **Photogrammetry, laser scanning and mill-floor timber scanning are mature, quantified and commercially routine. Site progress monitoring and safety monitoring are commercially available but statistically soft and heavily over-claimed. Autonomous defect judgement is mostly research.** Maturity is graded on a five-point scale: **[R] research**, **[E] emerging pilot**, **[C] commercially available**, **[M] mature/routine**, **[S] standard practice**.

## Key facts

| Item | Value | Source |
|---|---|---|
| SODA construction dataset | 19,846 images, 286,201 objects, 15 classes (workers, materials, machines, layout); YOLOv3/v4 max 81.47 % mAP | arXiv:2202.09554 |
| SDNET2018 concrete crack dataset | >56,000 images of 256×256 px from 230 16 MP originals; bridge decks (54), walls (72), pavements (104); cracks 0.06–25 mm | Utah State University |
| OpenSpace scale claim | 77 billion ft² captured, 95,000+ projects, 132 countries | OpenSpace (vendor) |
| Disperse tracking claim | up to 670 components tracked; 360° capture by trained scanners | Disperse (vendor) |
| Buildots claim | delays reduced "by up to 50 %" (2–3 months typical) | Buildots (vendor) |
| viAct claim | "95 % less accidents" | viAct (vendor) |
| MiCROTEC scanner families | Goldeneye Transverse (transverse multi-sensor quality scanner), Logeye (multi-sensor real-shape and quality log scanner), Woodeye (hardwood multi-sensor quality scanner) | MiCROTEC |

> ⚠️ Every figure in the four vendor rows above is **marketing material**, self-reported, and not independently evaluated. No peer-reviewed third-party assessment of any commercial construction progress-monitoring or safety-monitoring product was located in this research pass. Treat them as claims, cite them as claims, and demand a site trial with your own acceptance criteria before purchase.

---

## 1. Progress monitoring from site photos — **[C]**

**What it does.** Capture the site regularly (360° camera on a hard hat walked along a route, fixed cameras, phone photos, or a drone). Localise each image against a floor plan or BIM model. Classify the state of each element or zone — not started / in progress / complete — and report progress against schedule.

**Realistic accuracy.** For coarse element-level states in an interior fit-out with good, repeatable capture, published academic work and vendor claims converge on roughly 80–90 % correct state classification, degrading sharply with occlusion, clutter and unusual sequences. It works far better on repetitive residential and commercial fit-out (many identical rooms, well-defined trade sequence) than on one-off structures.

**Products today.** **OpenSpace** (360° walk capture, drones, smartphones; Photo Documentation, BIM coordination, progress tracking, "AI Agents & APIs"), **Buildots** (managed capture services, links BIM + schedule + site data + workforce), **Disperse** (trained scanners doing 360° capture, tracking up to 670 components), **Doxel**, **StructionSite** (merged into DroneDeploy), **Reconstruct**.

**What it takes to build.** The image capture and storage are easy. The hard parts are (a) **localisation** — knowing where each photo was taken, to within a metre and a few degrees, which requires either visual SLAM against a prior model, fiducials on site, or good BIM-image registration; and (b) the **element ontology** — mapping "this pixel region" to "this IfcWall". Realistically 6–18 months of a small team, and the capture discipline is a larger operational problem than the algorithm.

**Honest verdict.** Buy, do not build, unless progress monitoring *is* your product. The value delivered is mostly the *disciplined visual record* — which settles disputes and removes site visits — rather than the AI progress percentage.

## 2. Change detection between site photo sets — **[E]**

**What it does.** Compare imagery from the same viewpoint on two dates and highlight what changed. Simpler and more robust than full progress classification.

**Realistic accuracy.** With a genuinely fixed camera, near-perfect after illumination normalisation. With hand-held repeat photography, the alignment problem dominates: homography or feature-based registration handles small viewpoint shifts, but parallax on a 3D scene defeats a single homography. Expect a usable "attention map" rather than a measurement.

**What it takes to build.** Weeks, not months. Register with SIFT/AKAZE + RANSAC homography (`03`), normalise illumination with CLAHE or histogram matching, difference, threshold, morphologically clean, and report blobs above an area threshold. Blueprint (a) in `09` covers this.

**Honest verdict.** The best value-per-effort item in this entire list for a small contractor. It requires no labelled data.

## 3. 4D BIM comparison / as-planned vs as-built — **[E]**

**What it does.** Register a point cloud or reconstructed geometry against the BIM model, and check whether each element is present, absent, or displaced.

**Realistic accuracy.** *Presence* detection of large elements (walls, columns, slabs, ducts) is reliable at around 90 %+ given a good registered scan. *Deviation measurement* is as accurate as the scan (`02`): 3–10 mm from a terrestrial laser scanner, 10–30 mm from a SLAM scanner, 20–50 mm from drone photogrammetry. Registration to the model is the weak link — a 20 mm registration error masquerades as a 20 mm build deviation.

**Products today.** Autodesk **ReCap** + Navisworks clash workflows, **ClearEdge3D Verity** (specifically built for as-built verification against model), **Trimble RealWorks**, **Faro As-Built**, **Leica Cyclone**, plus the progress-monitoring platforms above.

**What it takes to build.** Do not build the geometry engine. Build the *workflow*: capture standard, registration procedure, tolerance definitions per element class, and a report format the site team will read. That is where the value is and where the vendors are weakest.

## 4. Safety monitoring — PPE detection — **[C]**

**What it does.** Detect people, then classify whether each is wearing a hard hat, high-visibility vest, harness, gloves, mask, or safety boots.

**Realistic accuracy.** Hard hat detection on a well-framed subject at 100+ pixels of body height is genuinely reliable — typically 90–95 % recall in good conditions with a fine-tuned detector. It falls apart on: small subjects (a worker 40 px tall at the far end of a slab), back-lit silhouettes, occlusion by plant and scaffold, rain and dust, a helmet carried rather than worn, and — critically — the confusion between "no hard hat" and "hard hat not visible from this angle". Boots and gloves are much harder than helmets and vests. **Reported mAP figures of 90 %+ in the literature are almost always on curated, well-framed datasets and do not transfer to a fixed CCTV view of a working site.**

**Products today.** **viAct** (PPE non-compliance, danger-zone intrusion, work-at-height, confined space, plus environmental and fleet modules), **Intenseye**, **Protex AI**, **Smartvid.io/Newmetrix**, **Voxel**, plus PPE modules inside most VMS platforms (Milestone, Genetec) and inside the progress-monitoring vendors.

**Datasets.** SODA (19,846 images, 286,201 objects, 15 classes across workers, materials, machines and layout — reported max 81.47 % mAP with YOLOv3/v4), plus various hard-hat datasets on Roboflow Universe of highly variable label quality.

**What it takes to build.** This is the most approachable "real" deep-learning construction project: a YOLO11/YOLO26 detector fine-tuned on a few thousand site-specific images, running on a Jetson at the camera. Blueprint (b) in `09`. Budget 2–4 months for a working pilot, and expect the *deployment* problems (camera siting, network, alerting, and above all the industrial-relations question of monitoring workers) to be larger than the model problems.

> ⚠️ **A PPE camera is a management-information tool, never a safety device.** It must not be relied upon in place of supervision, induction, permits-to-work or physical safeguarding. It also creates a workforce-surveillance issue with legal and industrial-relations consequences that must be resolved with the workforce before deployment, not after. **[NA]/[ZA]** Personal information processing obligations apply (POPIA in South Africa; Namibia's Data Protection Bill status should be checked before deployment).

## 5. Exclusion zones and proximity detection — **[C]**

**What it does.** Define a polygon in the camera view (or a 3D volume) and alarm when a person enters it, or when a person and a machine come within a set distance.

**Realistic accuracy.** Person detection is the easy part. The hard part is **turning image coordinates into ground coordinates**: a homography from the camera to the ground plane (`02`) is accurate for feet on a flat floor and wrong for anything else. Expect 0.3–1 m ground-position error from a single camera at 10–20 m, worse on slopes and at the frame edges.

**Products today.** viAct, Protex AI, plus radar/UWB/RFID proximity systems, which are more reliable than vision for the plant-worker case and are the standard answer for reversing plant.

**What it takes to build.** Person detector + tracker (ByteTrack/BoT-SORT) + ground homography + zone logic. A few weeks on top of a working detector. **Prefer UWB/RFID for anything genuinely safety-critical.**

## 6. Crack and defect detection in concrete — **[C for images, E for measurement]**

**What it does.** Find cracks, spalls, delamination, honeycombing, efflorescence and rust staining in photographs of concrete, and — the harder task — measure crack widths.

**Realistic accuracy.** *Detection* of cracks above roughly 0.3 mm at a suitable GSD is a solved segmentation problem: a U-Net trained on a few thousand patches will exceed 90 % IoU on clean surfaces. *Measurement* requires an absolute scale and enough pixels: to measure a 0.2 mm crack to ± 0.05 mm you need roughly 0.02–0.05 mm/px, which means a close-up photograph with a scale bar, not a drone image. **SDNET2018** — over 56,000 256×256 px images derived from 230 16 MP originals of bridge decks, walls and pavements, covering cracks from 0.06 mm to 25 mm, deliberately including shadows, scaling, holes and rough texture — is the standard open benchmark and its inclusion of confounders is the reason it is worth using.

**Products today.** **Dronedeploy/Skydio** inspection workflows, **Nexxis/Cyberhawk** and other inspection-service firms, **Fugro**, plus dedicated tools from bridge-management vendors. Structural assessment remains a human engineering judgement everywhere.

**What it takes to build.** A U-Net on SDNET2018 plus your own images is a two-week project (`03`, `05`). Turning it into a defensible measurement requires the calibration discipline of `02` and an agreed capture protocol. **The engineering judgement — is this crack structurally significant? — is not a vision problem and must not be presented as one.**

## 7. Rebar counting and spacing verification — **[E]**

**What it does.** From a photograph of a reinforcement mat before pour, count bars, measure spacing, and check against the schedule.

**Realistic accuracy.** Counting bars in a clean, well-lit, roughly planar mat photographed near-perpendicular: 90–97 % with a detector plus a geometric consistency check. Real conditions — overlapping mats, chairs and spacers, mud, standing water, shadow, oblique viewpoint, congested column starter bars — degrade this badly. **Spacing measurement needs the plane-rectification of `02`**; without a scale reference in frame it is not a measurement at all.

**What it takes to build.** Two viable approaches: (i) classical — rectify with a homography from four known points, then Hough lines plus periodicity analysis to count and space; (ii) learned — a detector on bar ends or bar segments plus line fitting. Combining them is better than either. **This is a genuinely good candidate for a small in-house build**, because the payoff (a signed pre-pour record) is concrete and the scene is more constrained than most site imagery.

## 8. Material and delivery tracking — **[E]**

**What it does.** Recognise deliveries arriving at the gate, count and identify materials, read delivery-note text, tally pallets or brick packs, verify against orders.

**Realistic accuracy.** *Reading a delivery note* with a modern vision-language model is now very good and is the highest-value, lowest-effort component. *Counting stacked items* (bricks in a pack, boards in a bundle) is a classical counting problem that works well from a square-on view and fails from an oblique one. *Identifying material types* generically is unreliable.

**What it takes to build.** Start with the delivery note, not the pixels: a phone photo of the note, a VLM reading it into structured fields, and reconciliation with the order. Weeks, and it delivers most of the value.

## 9. As-built verification by photogrammetry and laser scanning (Scan-to-BIM) — **[M]**

**What it does.** Capture the built condition as a point cloud, register it to a coordinate system, and either verify the design model against it or model new geometry from it.

**Realistic accuracy.** See `02`. Terrestrial laser scanning gives 3–10 mm over a building; SLAM/mobile scanning 10–30 mm; drone photogrammetry 20–50 mm horizontal at ~16 mm GSD with proper ground control; phone-photo SfM 5–20 mm over a room with a scale bar.

**Products today.** Hardware: Leica (RTC360, BLK360, BLK2GO), Faro (Focus, Orbis), Trimble (X7, X9), NavVis (VLX), Matterport. Software: Autodesk ReCap/Revit, Leica Cyclone, Trimble RealWorks, Faro As-Built, ClearEdge3D EdgeWise/Verity, PointCab. Photogrammetry: Agisoft Metashape, Pix4D, RealityCapture, and the open COLMAP / OpenMVG+OpenMVS / Meshroom stack.

**What it takes to build.** Nothing — buy it. **The differentiator a construction firm can build is the workflow and the QA**: a documented capture standard, an accuracy-verification procedure using independent check points, and a deliverable specification (LOD/LOIN) agreed with the client. That is a knowledge product, not a software product, and it is where most Scan-to-BIM deliverables currently fail.

**Automatic modelling from point cloud to IFC remains [R/E].** Planar surfaces, pipes and structural members are extracted reasonably well; anything requiring semantic judgement is not. Expect substantial manual modelling.

## 10. Drone survey and volumetrics — **[S]**

**What it does.** Fly a photogrammetric block, produce an orthomosaic, DSM and point cloud, and compute stockpile volumes, cut/fill and earthworks progress.

**Realistic accuracy.** With RTK/PPK and adequate ground control at ~60 m AGL: 20–50 mm horizontal, 40–80 mm vertical (see the GSD discussion in `02`). Stockpile volumes are typically quoted at 1–3 % of volume, dominated by the toe-definition and base-surface assumptions rather than by the photogrammetry.

**Products today.** DJI hardware (Mavic 3 Enterprise, Matrice series), Propeller, DroneDeploy, Pix4D, Agisoft, Trimble Stratus, senseFly/AgEagle.

**Regulatory. [NA]** Namibian commercial UAS operation is regulated by the Namibia Civil Aviation Authority; **[ZA]** South African operations require an RPAS Operator Certificate and a Remote Pilot Licence under SACAA Part 101. Both must be confirmed against current regulations before any commercial flight — see the `18_namibia_context` domain and verify directly with the regulator.

**Honest verdict.** Fully mature. There is no reason to build anything here beyond the QA workflow.

## 11. Brick, block and unit counting — **[E]**

**What it does.** Count masonry units in a wall from a photograph — for progress measurement, payment verification, or material reconciliation.

**Realistic accuracy.** On a plane-rectified, well-lit, un-rendered wall with visible mortar joints, a classical approach works well: rectify by homography, detect the two dominant joint orientations, apply anisotropic morphology (a horizontal kernel for bed joints, vertical for perpends), and count cells. 95 %+ on clean brickwork; substantially worse on rough blockwork, wet walls, partially rendered surfaces, and anything with shadows across the face.

**What it takes to build.** A week or two, no training data required, using only the techniques in `03`. This is an excellent first classical-CV project and directly connects to the `16_walls_and_boundaries` domain. Blueprint-adjacent.

## 12. Timber grading and defect scanning in mills — **[M]**

**What it does.** Scan sawn timber or logs continuously and detect knots, splits, wane, rot, resin pockets, grain deviation and density variation, then optimise cross-cutting and ripping to maximise value yield.

**Realistic accuracy.** This is the most mature and most quantified vision application in the whole timber chain — a solved industrial problem operating at production line speeds for decades. Multi-sensor scanners combine colour cameras, laser triangulation for shape, the **tracheid effect** (laser light scattering anisotropically along the grain, which reveals local grain angle and hence knot influence), X-ray for internal density, and full **X-ray CT** on logs for internal defect mapping before the first saw cut.

**Products today.** **MiCROTEC** is the dominant name, with **Goldeneye Transverse** (high-precision transverse multi-sensor quality scanner), **Logeye** (multi-sensor real-shape and quality scanner for logs) and **Woodeye** (multi-sensor quality scanner for hardwood), plus CT log scanning. Competitors and adjacent suppliers include **Weinig/LuxScan**, **USNR**, **Finscan** and **Limab**.

**What it takes to build.** Do not. This is a mature capital-equipment market with decades of accumulated species- and defect-specific tuning. The relevant knowledge for a joinery business is *how to specify and buy* scanning, and how to use the resulting grade data commercially.

**Relevance to joinery.** Understanding that the timber you buy has already been machine-graded — and on what basis — changes how you specify and price it. It also sets a realistic bar: any in-house defect-detection ambition should be measured against what a Woodeye already does.

## 13. CNC vision alignment and nesting optimisation — **[C]**

**What it does.** A camera on or near a CNC router or beam saw locates the actual position and orientation of the workpiece (or of grain, figure, veneer join lines, or existing features) and adjusts the toolpath accordingly.

**Realistic accuracy.** With a calibrated camera and a fixed working distance, 0.05–0.2 mm positional accuracy is achievable — comparable to the machine's own positioning tolerance, which is what matters. Registration to printed fiducials or drilled datum holes is more robust than registration to the workpiece edge.

**Products today.** Vision registration is standard on digital cutting tables (**Zünd**, **Esko Kongsberg**, **Blackman & White**) for sheet materials, and is offered as an option on woodworking CNC from **Homag**, **Biesse**, **SCM** and **Felder/Format-4** — usually branded as camera-assisted nesting, label reading, or grain-matched cutting. **AiO/Shaper Origin** is the interesting small-shop case: a hand-held router that uses vision on a tape-based fiducial to hold position to a fraction of a millimetre.

**What it takes to build.** For a small shop: an industrial camera on a rigid mount, a checkerboard calibration (`02`), a homography to machine coordinates, ArUco or printed-target detection, and a G-code offset. This is genuinely achievable in-house in a few weeks and gives a real productivity gain when working with pre-printed, pre-veneered or figured material. **The hardest part is the mechanical mounting and repeatability, not the vision.**

## 14. Edge, dimension and surface inspection in joinery — **[E in-house, C via vendors]**

**What it does.** After the beam saw and edgebander: verify panel dimensions and squareness, check edgeband adhesion, glue-line quality, colour and finish match, and detect surface defects (scratches, dents, tear-out, glue squeeze-out, sanding marks).

**Realistic accuracy.**
- **Dimensions:** with backlit telecentric corner cameras on a rigid frame, ± 0.1–0.2 mm is achievable over a 1200 mm panel; the limit is thermal and mechanical, not optical (see the worked example in `01` and the blueprint in `09`).
- **Squareness:** measure the diagonals; a 0.2 mm diagonal difference on a 600 × 400 panel corresponds to a squareness deviation well inside normal shop tolerance.
- **Edgeband defects:** low-angle dark-field illumination reveals lifting and glue lines superbly; a simple threshold along the edge band catches most faults.
- **Surface defects:** the right formulation is **anomaly detection** (train on good panels only — PatchCore/PaDiM on MVTec AD-style data), not defect classification, because you will never collect enough examples of every defect type.
- **Colour match:** measure in CIELAB and specify in ΔE (`03`), not RGB.

**Products today.** No affordable turnkey product exists for a small joinery shop. Large panel producers use web-inspection systems from ISRA VISION, Baumer Inspection, or Teledyne DALSA-based integrations. Homag and Biesse offer line-integrated quality modules on high-end machinery.

**What it takes to build.** This is the single best in-house vision opportunity for a joinery business, because the scene is controllable, the payback is measurable (rework and remake cost per panel), and the classical toolkit is sufficient. Blueprint (d) in `09` gives a full design with a tolerance budget.

## 15. Quality control on panel and component production — **[E]**

**What it does.** Verify that the correct panel arrived at the correct station: read the barcode/label, confirm dimensions and drilling pattern against the cutting list, and confirm hardware presence (hinge cups, shelf pins, dowels, connectors).

**Realistic accuracy.** Barcode reading is a solved problem (`04`). Drilling-pattern verification against the 32 mm system is straightforward classical template work: rectify the panel face, locate holes by circular Hough or blob analysis, and compare hole positions and diameters against the expected pattern. 99 %+ with controlled lighting. Hardware presence checking is equally tractable.

**What it takes to build.** Weeks. **This is the highest-ROI, lowest-risk vision project in a joinery shop** — it catches the single most expensive error class (a wrongly drilled or wrongly sized panel discovered at installation rather than at the machine) with very little technology.

---

## Summary table

| # | Application | Maturity | Typical accuracy | Build in-house? |
|---|---|---|---|---|
| 1 | Site progress monitoring | **[C]** | ~80–90 % element state, degrading with clutter | No — buy |
| 2 | Photo change detection | **[E]** | Good with fixed camera; attention-map only otherwise | **Yes** — days |
| 3 | 4D BIM as-built comparison | **[E]** | Presence ~90 %; deviation = scan accuracy | Workflow only |
| 4 | PPE detection | **[C]** | 90–95 % recall on well-framed subjects; much worse in the wild | **Yes** — months |
| 5 | Exclusion zones | **[C]** | 0.3–1 m ground position from one camera | Partly; prefer UWB for safety |
| 6 | Concrete crack detection | **[C]** / **[E]** measurement | >90 % IoU detection; measurement needs 0.02–0.05 mm/px | **Yes** — weeks |
| 7 | Rebar counting | **[E]** | 90–97 % in good conditions | **Yes** — good candidate |
| 8 | Material/delivery tracking | **[E]** | Note-reading excellent; counting view-dependent | **Yes** — start with the note |
| 9 | Scan-to-BIM as-built | **[M]** | 3–10 mm TLS; 10–30 mm SLAM; 20–50 mm drone | No — buy; build the QA |
| 10 | Drone survey/volumetrics | **[S]** | 20–50 mm H, 40–80 mm V; volumes 1–3 % | No |
| 11 | Brick/block counting | **[E]** | 95 %+ on clean rectified brickwork | **Yes** — weeks, classical |
| 12 | Timber grading/scanning | **[M]** | Production-rate, decades mature | **No** — buy |
| 13 | CNC vision alignment | **[C]** | 0.05–0.2 mm | **Yes** — weeks |
| 14 | Joinery dimension/surface QC | **[E]** | ± 0.1–0.2 mm dimensional | **Yes** — best opportunity |
| 15 | Panel/component verification | **[E]** | 99 %+ on drilling patterns and codes | **Yes** — highest ROI |

## Sources

- [SODA: Site Object Detection dAtaset for Deep Learning in Construction (arXiv:2202.09554)](https://arxiv.org/abs/2202.09554) — 19,846 images, 286,201 objects, 15 classes, 81.47 % max mAP with YOLOv3/v4.
- [SDNET2018 (Utah State University)](https://digitalcommons.usu.edu/all_datasets/48/) — >56,000 256×256 px images from 230 16 MP originals; bridge decks/walls/pavements; cracks 0.06–25 mm; Maguire, Dorafshan & Thomas, May 2018.
- [OpenSpace](https://www.openspace.ai/) — 360°/drone/smartphone capture, BIM coordination, progress tracking; 77 bn ft², 95,000+ projects, 132 countries (vendor claims).
- [Buildots](https://www.buildots.com/) — managed capture, BIM + schedule + site data; "delays reduced by up to 50 %" (vendor claim).
- [Disperse](https://www.disperse.io/) — 360° capture by trained scanners; "up to 670 components" tracked (vendor claim).
- [viAct](https://www.viact.ai/) — PPE detection, danger zone, work at height, confined space modules; "95 % less accidents" (vendor claim, no accuracy figures published).
- [MiCROTEC](https://www.microtec.com/) — Goldeneye Transverse, Logeye, Woodeye scanner families.
- [COLMAP](https://colmap.github.io/).

## Open questions

- **All vendor performance claims cited here are self-reported marketing.** No independent evaluation of OpenSpace, Buildots, Disperse, Doxel or viAct accuracy was located. `needs-verification`.
- Accuracy bands for PPE detection, rebar counting, brick counting and crack detection are **practitioner estimates synthesised from general familiarity with the literature**, not from specific cited studies. They should be treated as planning figures and validated on site data before any contractual commitment.
- MiCROTEC technology details (X-ray CT, tracheid effect, laser triangulation) and competitor names (Weinig/LuxScan, USNR, Finscan, Limab) are from general familiarity; the fetched page confirmed only the three product family names.
- Cognex/Homag/Biesse/Zünd CNC vision feature names are unverified in this pass.
- **[NA]** Namibian UAS regulations and data-protection law status must be verified directly with the NCAA and against current Namibian legislation before any commercial deployment.
