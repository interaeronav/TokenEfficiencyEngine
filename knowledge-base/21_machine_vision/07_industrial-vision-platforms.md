---
id: vision.platforms
title: Industrial vision platforms — commercial ecosystem and the open stack compared
domain: 21_machine_vision
tags: [cognex, halcon, merlic, keyence, omron, basler, pylon, national-instruments, matrox, teledyne-dalsa, opencv, scikit-image, kornia, pytorch, ultralytics, detectron2, mmdetection, lock-in, cost]
jurisdiction: global
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "MVTec HALCON", url: "https://www.mvtec.com/products/halcon", publisher: "MVTec Software GmbH", accessed: 2026-08-25}
  - {title: "Basler pylon", url: "https://www.baslerweb.com/en/software/pylon/", publisher: "Basler AG", accessed: 2026-08-25}
  - {title: "Detectron2", url: "https://github.com/facebookresearch/detectron2", publisher: "Meta AI Research / GitHub", accessed: 2026-08-25}
  - {title: "Kornia documentation", url: "https://kornia.readthedocs.io/en/latest/", publisher: "Kornia", accessed: 2026-08-25}
  - {title: "Ultralytics supported models", url: "https://docs.ultralytics.com/models/", publisher: "Ultralytics", accessed: 2026-08-25}
  - {title: "Vision Standards", url: "https://www.automate.org/vision/vision-standards/vision-standards", publisher: "A3", accessed: 2026-08-25}
related: [vision.deployment, vision.classical, vision.construction]
---

# Industrial vision platforms — commercial ecosystem and the open stack compared

**Summary.** There are three ways to build a vision system: buy a smart camera with a configuration GUI, license a machine-vision library and write an application around it, or assemble an open stack from OpenCV, PyTorch and the rest. Each is right in different circumstances, and the deciding variables are rarely technical — they are who will maintain the system in five years, whether you need a supplier to sign a support contract, and how much lock-in you can tolerate. This file surveys the commercial ecosystem (Cognex, MVTec, Keyence, Omron, Basler, National Instruments, Matrox, Teledyne DALSA), the open stack, and gives a decision framework with realistic cost bands.

> ⚠️ **Pricing note.** Every commercial vendor in this field quotes rather than lists. The bands given below are order-of-magnitude indications gathered from general industry familiarity, **not from published price lists**, and they vary by region, volume and reseller. This whole file is marked `confidence: medium` for that reason. Get a quote; do not budget from this table.

## Key facts

| Platform | Type | Licence/cost model | Lock-in |
|---|---|---|---|
| Cognex In-Sight | Smart camera + GUI (spreadsheet/EasyBuilder) | Per camera, hardware-bundled | Very high |
| Cognex VisionPro | PC library (.NET/C++) | Per-seat dev + per-runtime licence dongle | High |
| MVTec HALCON | PC library (C/C++/.NET/Python) | Per-seat dev + per-runtime, editions | High (HDevelop scripts) |
| MVTec MERLIC | Configuration-based, no coding | Per runtime | High |
| Keyence CV-X / XG / IV | Smart camera + controller | Hardware-bundled, sold with engineering support | Very high |
| Omron FH / FHV | Smart camera + controller | Hardware-bundled | Very high |
| Basler pylon | Camera SDK (free) | Free download; SDKs for C++, .NET/C#, C, Java | Low (GenTL/GenICam) |
| NI Vision (LabVIEW) | Toolkit in LabVIEW | Per-seat + runtime | High |
| Matrox Imaging Library (MIL) / MIL X | PC library | Per-seat + runtime | High |
| Teledyne DALSA Sapera / Sherlock | PC library / app | Per-seat + runtime | High |
| OpenCV | Open library | Apache-2.0 | None |
| PyTorch | Open framework | BSD-style | None |
| Ultralytics | Open + commercial | **AGPL-3.0** or paid Enterprise | Licence, not technical |
| Detectron2 | Open library | Apache-2.0 | None |

## The commercial stack

### Cognex

The largest pure-play machine-vision company and the reference point for the industry.

- **In-Sight** — self-contained smart cameras with an on-board processor, running a spreadsheet-style configuration environment (In-Sight Explorer / In-Sight Vision Suite, with the EasyBuilder guided interface for non-programmers). No PC required. The 2000/7000/8000/9000 series span from simple presence-checking to high-resolution inspection; the **In-Sight D900** is the deep-learning-capable variant, and In-Sight L38/L48 are recent additions.
- **VisionPro** — the PC-based library for .NET and C++, used when a project needs full application control, multiple cameras, complex logic or database integration. The commercial home of **PatMax**, the shape-based geometric pattern-matching tool whose robustness to rotation, scale, occlusion and lighting change is one of the two or three genuine reasons to pay Cognex money.
- **Deep Learning (formerly ViDi)** — four tools: Locate, Analyze (anomaly detection), Classify, Read. Trainable from tens to hundreds of images by a technician, not a data scientist. This is the pitch: *industrialised deep learning that a controls engineer can commission*.
- **DataMan** — barcode and Data Matrix readers, including hard direct-part-marking cases.
- **3D-A1000** and 3D displacement sensors.

**Why people buy it:** it works, the field support is real, and a plant engineer can be trained on it. **Why people regret it:** the price, and the fact that the logic lives inside a proprietary spreadsheet or a dongled runtime that nobody outside the vendor ecosystem can maintain.

### MVTec HALCON and MERLIC

**HALCON** is the deepest general-purpose machine-vision library in the market — 2D and 3D image processing plus AI in one platform, with deep learning accelerated through Intel OpenVINO and NVIDIA TensorRT, and coverage spanning blob analysis, filtering, morphology, measuring, matching, OCR, barcode/2D-code reading, 3D calibration and spatial analysis. Development happens in **HDevelop**, an interactive IDE that exports to C++, C#, Python or a runnable HDevEngine script.

HALCON's shape-based matching (`find_shape_model`, `find_scaled_shape_model`, `find_surface_model` for 3D) is the main technical rival to Cognex PatMax, and its measurement tools (`gen_measure_rectangle2`, `measure_pos`) are the reference implementation of subpixel calipers. **If you have a hard classical problem and a competent developer, HALCON will solve it faster than anything else.**

**MERLIC** is the same technology packaged for configuration rather than coding — a tool-chain builder with a built-in HMI, aimed at integrators who want a deployable application without writing software.

MVTec licenses per development seat plus per runtime, in defined editions with a published release cycle. Expect development seats in the four-to-five-figure EUR range and runtimes in the high three to four figures per machine.

### Keyence

Keyence sells an *engineering service wrapped in hardware*. The CV-X and XG series (controller plus camera heads) and the IV/IV3 series (self-contained sensors) are competent, but the differentiator is the direct sales model: an application engineer arrives, brings demonstration hardware, sets the system up on your line, and does not leave until it works. For a factory with no vision expertise and a well-defined problem, this is genuinely valuable and is why Keyence's margins are what they are.

Corresponding downsides: the highest prices in the industry, the least openness (limited scripting, closed formats), and a total dependence on the vendor relationship. Their **LJ-X8000** laser profilers and the vision-equipped measurement systems are excellent hardware.

### Omron (including Microscan/Adept heritage)

**FH** and **FHV7** series vision controllers and smart cameras, tightly integrated with Omron's PLC and robotics lines (Sysmac). The strongest argument for Omron is when the plant is already Omron: vision, motion, safety and control share one development environment and one fieldbus, which removes an entire class of integration problems.

### Basler

Primarily a **camera** manufacturer (ace, ace 2, boost, dart, blaze 3D) rather than an algorithm vendor, and the volume leader in cost-effective industrial cameras. **pylon** is their free SDK: certified drivers, camera setup tools, SDKs for C++, .NET/C#, C and Java (Android), running on Windows 10/11 64-bit, Linux x86 and ARM, macOS 11–14, and Android 8–11, with support for USB3 Vision, GigE Vision, CoaXPress 2.0, GMSL2, BCON for MIPI and blaze 3D, all through GenTL. **pypylon** provides Python bindings. Basler also sells **pylon vTools** — licensed processing blocks (barcode, OCR, 3D) for people who want some algorithm capability without a full HALCON licence.

**Basler is the low-lock-in choice**: buy the cameras, use pylon or a GenICam-neutral layer, and write the application in whatever you like.

### National Instruments Vision

The **Vision Development Module** and **Vision Builder for Automated Inspection (VBAI)** within the LabVIEW ecosystem. Strong where vision is one part of a larger test-and-measurement system with DAQ, motion and instrument control — laboratory, R&D, end-of-line test. Weaker as a standalone production-vision choice, and the LabVIEW licensing model has become a significant cost consideration.

### Matrox Imaging (now part of Zebra) and Teledyne DALSA

**Matrox Imaging Library (MIL / MIL X)** and **Design Assistant** (flowchart-based) are a long-established, capable library stack with particularly strong frame-grabber hardware heritage. **Teledyne DALSA** brings **Sapera LT** (acquisition), **Sherlock** (application builder) and **Astrocyte** (deep learning training), plus the industry's leading line-scan sensors and frame grabbers. Both are the right call in high-speed, line-scan, web-inspection territory — printing, textiles, sheet materials, and by extension **continuous timber and panel inspection**.

## The open stack

| Library | Role | Licence | Notes |
|---|---|---|---|
| **OpenCV** | The universal classical CV toolkit | Apache-2.0 | 2500+ algorithms, C++/Python/Java, CUDA and OpenCL back-ends, `opencv_contrib` for extras |
| **scikit-image** | Scientific image processing in NumPy | BSD | Cleaner API than OpenCV for research and measurement; slower; excellent morphology, segmentation and `regionprops` |
| **Kornia** | Differentiable CV in PyTorch | Apache-2.0 (see repo) | `augmentation`, `geometry`, `filters`, `enhance`, `color`, `losses`, `morphology`, `tracking`. Lets classical operations sit *inside* a network and receive gradients |
| **PyTorch** | The training framework | BSD-style | The default; near-total dominance of research |
| **timm** | Pretrained backbones | Apache-2.0 | >700 models |
| **Ultralytics** | Detection/segmentation/pose training and export | **AGPL-3.0** or Enterprise | Fastest path from data to deployed model; the licence is the catch |
| **Detectron2** | Detection/segmentation research platform | Apache-2.0 | Mask R-CNN, Cascade R-CNN, PointRend, DeepLab, DensePose, ViTDet, MViTv2, rotated boxes; last tagged release v0.6 (Nov 2021) though the repo continues to receive commits |
| **MMDetection / OpenMMLab** | Detection, segmentation, pose, OCR, tracking | Apache-2.0 | The widest model zoo of any open framework; configuration-driven; steep learning curve |
| **Hugging Face Transformers / Diffusers** | Transformer vision models | Apache-2.0 | DETR, SegFormer, Mask2Former, DPT, ViT, CLIP, OWL-ViT — a single API and hosted weights |
| **Albumentations / FiftyOne / supervision** | Augmentation, dataset inspection, post-processing utilities | MIT/Apache | FiftyOne in particular is the best open tool for *looking at* your dataset and your model's failures |
| **Aravis / Harvester** | GenICam acquisition | LGPL / Apache | Vendor-neutral camera access from Linux and Python |

**The open stack's real weakness is not capability, it is the missing 20 %:** there is no open equivalent of PatMax or `find_shape_model` with comparable robustness; the subpixel measurement tools are things you write yourself (`03`); there is no vendor to call at 03:00; and nobody will sign a support agreement. Its real strength is that in five years you can still read the source, run it on new hardware, and hire someone who knows it.

## Choosing — a decision framework

**Buy a smart camera (Cognex In-Sight, Keyence IV3, Omron FHV) when:**
- The problem is well-defined and standard (presence, code reading, simple gauging, colour verification).
- There is no software engineer on site and no appetite to acquire one.
- The line already has an integrator relationship.
- Cycle time is machine-paced and the answer is pass/fail to a PLC.
- **Realistic band: €3,000–€15,000 per station installed.**

**License a library (HALCON, VisionPro, MIL) when:**
- The problem is genuinely hard classically — high-accuracy gauging, robust matching under variation, 3D surface alignment.
- You have or can hire a developer.
- You need many cameras or complex logic under one application.
- Traceability, auditability and vendor support are contractual requirements.
- **Realistic band: €8,000–€25,000 development licence, €1,000–€6,000 per runtime, plus development time.**

**Build on the open stack when:**
- The problem is a learning problem (site imagery, defect variety, natural scenes) rather than a metrology problem.
- You have engineering capacity and intend to keep it.
- The application is novel and no vendor tool maps onto it.
- Budget is the binding constraint, or unit economics require scaling to many low-cost nodes.
- **Realistic band: hardware only (€500–€5,000 per node) plus substantial engineering time.**

**Hybrid, which is usually the right answer for a small manufacturer:** industrial cameras and lighting from Basler/Effilux/CCS (low lock-in, standards-based), acquisition through pylon or Harvester, and an application in Python/C++ on OpenCV plus a PyTorch model. You buy the hardware quality and standards compliance, and you keep the software.

## Lock-in, honestly assessed

The question to ask of any platform is: **if this vendor doubled the price or discontinued the product, what would it cost me to move?**

- **Smart cameras:** total rewrite. The logic exists only in the vendor's spreadsheet or flowchart. Highest lock-in in the industry. Mitigate by documenting the *inspection specification* — the physical setup, tolerances and decision rules — separately from the implementation.
- **Licensed libraries:** the application code is yours but every algorithm call is vendor-specific. HDevelop scripts and VisionPro tool blocks do not port. Mitigate by isolating vendor calls behind your own interface layer and keeping the business logic vendor-free.
- **Cameras and lighting:** low, provided you buy GenICam/GigE Vision/USB3 Vision compliant hardware and access it through a GenTL producer. This is the strongest practical argument for insisting on standards compliance at purchase.
- **Open stack:** none technically, but there is *maintenance* lock-in — the system depends on your team continuing to exist and to understand it. This is a real risk in a small firm and is under-weighted. Mitigate with documentation, tests and a genuinely reproducible build.
- **Ultralytics AGPL:** a specific and commonly overlooked trap. Internal use is fine; distributing a product, or arguably operating a network service, triggers the copyleft. Either buy the Enterprise licence or use an Apache/BSD-licensed model family.

## What to specify when you go to tender

1. The **inspection specification** in physical terms: feature, tolerance, cycle time, false-reject and false-accept limits, part presentation and its variation.
2. The **acceptance test**: a defined sample of parts, including known defects, with the pass criteria stated before the trial.
3. **Ownership of configuration and source**, and the right to a copy of the runtime configuration in a documented format.
4. **Support terms** and the response time for a line-down event.
5. **Spares and obsolescence**: how long will this camera, this lens and this light be available?
6. **Standards compliance** of the hardware (GenICam, GigE Vision/USB3 Vision), so cameras remain replaceable.
7. **Data ownership** for anything involving a cloud service.

## Sources

- [MVTec HALCON](https://www.mvtec.com/products/halcon) — 2D+3D plus AI, OpenVINO/TensorRT acceleration, matching/OCR/blob/measuring toolset, editions-and-licensing model.
- [Basler pylon](https://www.baslerweb.com/en/software/pylon/) — free; Windows 10/11 64-bit, Linux x86/ARM, macOS 11–14, Android 8–11; C++/.NET/C/Java SDKs; USB3 Vision, GigE Vision, CoaXPress 2.0, GMSL2, BCON for MIPI, blaze 3D via GenTL.
- [Detectron2 (GitHub)](https://github.com/facebookresearch/detectron2) — Apache-2.0; panoptic segmentation, DensePose, Cascade R-CNN, rotated boxes, PointRend, DeepLab, ViTDet, MViTv2; last tagged release v0.6, 15 Nov 2021.
- [Kornia](https://kornia.readthedocs.io/en/latest/) — differentiable CV; `augmentation`, `geometry`, `filters`, `enhance`, `color`, `losses`, `morphology`, `tracking`.
- [Ultralytics — supported models](https://docs.ultralytics.com/models/).
- [A3 Vision Standards](https://www.automate.org/vision/vision-standards/vision-standards).

## Open questions

- **All price bands in this file are indicative and unverified.** No vendor publishes list prices for HALCON, VisionPro, MIL, In-Sight or Keyence hardware. `needs-verification` — obtain quotes.
- Cognex product-family names (In-Sight 2000/7000/8000/9000, D900, L38/L48, VisionPro, PatMax, ViDi/Deep Learning, DataMan, 3D-A1000) are from general familiarity; **cognex.com returned HTTP 403 to automated fetching in this pass** and could not be confirmed.
- Keyence, Omron, Matrox and Teledyne DALSA product names likewise not fetched in this pass.
- Kornia's licence is stated as Apache-2.0 from familiarity; the documentation page fetched does not state it.
