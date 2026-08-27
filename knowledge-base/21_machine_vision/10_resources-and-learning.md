---
id: vision.resources
title: Machine vision resources — books, courses, conferences, datasets and repositories
domain: 21_machine_vision
tags: [textbooks, szeliski, hartley-zisserman, goodfellow, cs231n, cvpr, iccv, eccv, neurips, coco, imagenet, open-images, mvtec-ad, datasets, repositories, learning-path]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Computer Vision: Algorithms and Applications, 2nd ed.", url: "https://szeliski.org/Book/", publisher: "Richard Szeliski", accessed: 2026-08-25}
  - {title: "Deep Learning", url: "https://www.deeplearningbook.org/", publisher: "Goodfellow, Bengio & Courville / MIT Press", accessed: 2026-08-25}
  - {title: "CS231n: Deep Learning for Computer Vision", url: "https://cs231n.stanford.edu/", publisher: "Stanford University", accessed: 2026-08-25}
  - {title: "First Principles of Computer Vision", url: "https://fpcv.cs.columbia.edu/", publisher: "Columbia University / Shree Nayar", accessed: 2026-08-25}
  - {title: "CVF Open Access", url: "https://openaccess.thecvf.com/menu", publisher: "Computer Vision Foundation", accessed: 2026-08-25}
  - {title: "Open Images Dataset V7", url: "https://storage.googleapis.com/openimages/web/index.html", publisher: "Google", accessed: 2026-08-25}
  - {title: "MVTec AD", url: "https://www.mvtec.com/company/research/datasets/mvtec-ad", publisher: "MVTec Software GmbH", accessed: 2026-08-25}
  - {title: "SODA construction dataset", url: "https://arxiv.org/abs/2202.09554", publisher: "arXiv", accessed: 2026-08-25}
  - {title: "SDNET2018", url: "https://digitalcommons.usu.edu/all_datasets/48/", publisher: "Utah State University", accessed: 2026-08-25}
related: [vision.overview, vision.deep_learning, vision.training]
---

# Machine vision resources — books, courses, conferences, datasets and repositories

**Summary.** A tested register. Every link here was fetched on the access date unless explicitly noted as unverified in Open questions. It is organised as a learning path rather than an alphabetical list: the canonical textbooks first, then courses, then the venues where new work appears, then datasets, then the repositories you will actually clone. A suggested reading order is given at the end for someone starting from zero and wanting to reach competence in a construction or manufacturing context.

## Key facts

| Resource | Detail |
|---|---|
| Szeliski, *Computer Vision: Algorithms and Applications* | 2nd edition; free PDF via szeliski.org/Book |
| Goodfellow, Bengio & Courville, *Deep Learning* | MIT Press 2016; complete HTML free at deeplearningbook.org |
| Stanford CS231n | Spring 2026 offering; notes public at cs231n.github.io |
| First Principles of Computer Vision | Shree Nayar, Columbia; free video lecture series, 6 modules |
| CVF Open Access | CVPR 2013–2024, ICCV 2013/15/17/19/23, WACV 2020–2024, all free PDFs |
| Open Images V7 | 61.4 M image-level labels / 20,638 classes; 15,851,536 boxes / 600 classes; 2,785,498 instance masks / 350 classes; 675,155 localised narratives |
| MVTec AD | >5,000 images, 15 object and texture categories, pixel-precise anomaly annotations, **CC BY-NC-SA 4.0** |
| SODA | 19,846 construction images, 286,201 objects, 15 classes |
| SDNET2018 | >56,000 concrete crack sub-images, 0.06–25 mm cracks |

## Textbooks

**Richard Szeliski — *Computer Vision: Algorithms and Applications*, 2nd edition.**
[szeliski.org/Book](https://szeliski.org/Book/). **The single best starting point** and the closest thing the field has to a standard reference. Covers image formation, image processing, model fitting, structure from motion, dense correspondence, segmentation, recognition and deep learning in one coherent volume, with a bias toward what actually works. **A free PDF is made available from the author's site for personal use** — the site asks that you link to it rather than rehost the file. Read chapters 2 (image formation), 3 (image processing), 6 (recognition/model fitting), 11 (structure from motion) and 12 (depth estimation) before anything else.

**Hartley & Zisserman — *Multiple View Geometry in Computer Vision*, 2nd edition, Cambridge University Press, 2004.**
The definitive treatment of projective geometry, the fundamental and essential matrices, camera calibration, triangulation and bundle adjustment. Rigorous and mathematically demanding; you consult it rather than read it. If you are doing photogrammetry, stereo or any metrology, you will end up here. Sample chapters and MATLAB code have historically been hosted at the VGG page at Oxford.

**Forsyth & Ponce — *Computer Vision: A Modern Approach*, 2nd edition, Pearson, 2011.**
Broader and gentler than Hartley & Zisserman, stronger than Szeliski on the physics of imaging (radiometry, colour, texture, shading) and on classical statistical recognition. Predates the deep-learning era, which makes the first half more useful than the second.

**Goodfellow, Bengio & Courville — *Deep Learning*, MIT Press, 2016.**
[deeplearningbook.org](https://www.deeplearningbook.org/). The complete text is free online and will remain so. Part I (linear algebra, probability, numerical computation) and Part II (deep networks, regularisation, optimisation, CNNs) are the theoretical foundation. Now dated on architectures — it predates transformers entirely — but the fundamentals have not changed.

**Prince — *Understanding Deep Learning*, MIT Press, 2023.**
A modern, free-PDF alternative to Goodfellow that does cover transformers, diffusion models and graph networks, with unusually good figures. Increasingly the better first deep-learning book. *(Link unverified in this pass — see Open questions.)*

**Practical, non-canonical but useful:** *Programming Computer Vision with Python* (Solem), *Learning OpenCV* (Kaehler & Bradski) for the C++ API, and *Deep Learning for Coders with fastai and PyTorch* (Howard & Gugger) for a top-down applied route.

## Courses

**Stanford CS231n — Deep Learning for Computer Vision.**
[cs231n.stanford.edu](https://cs231n.stanford.edu/), notes at [cs231n.github.io](https://cs231n.github.io/). Currently offered Spring 2026. The lecture notes are public and are, on their own, one of the best free resources in the field — particularly the backpropagation, convolutional network and optimisation notes. Recordings from previous years are on YouTube; current-term video is restricted to enrolled students. **Do the assignments.** Implementing backprop from scratch once is worth ten courses watched passively.

**First Principles of Computer Vision — Shree Nayar, Columbia.**
[fpcv.cs.columbia.edu](https://fpcv.cs.columbia.edu/). A free video lecture series assuming no prior knowledge, in six modules: **Imaging** (image formation, sensing, binary images, image processing), **Features** (edge and boundary detection, SIFT, image stitching, face detection), **Reconstruction I** (radiometry, photometric stereo, shape, depth, active illumination), **Reconstruction II** (camera calibration, stereo, optical flow, structure from motion), and **Perception** (tracking, segmentation, appearance matching, neural networks). **This is the best free treatment of the *physics* half of the subject** — the material that file `01` of this domain compresses — and it is the natural complement to CS231n's focus on learning.

**Others worth knowing:** the University of Michigan's *Deep Learning for Computer Vision* (Justin Johnson, a CS231n descendant with public videos); Andrej Karpathy's *Neural Networks: Zero to Hero* for building intuition from first principles; fast.ai's *Practical Deep Learning for Coders*; and the OpenCV Bootcamp / OpenCV University courses for tool-level fluency.

## Conferences and where new work appears

Computer vision publishes primarily at conferences, not journals, and the proceedings are open access.

- **CVPR** — Conference on Computer Vision and Pattern Recognition. Annual, June, the largest and most influential venue.
- **ICCV** — International Conference on Computer Vision. Biennial (odd years), October.
- **ECCV** — European Conference on Computer Vision. Biennial (even years), autumn. Proceedings via Springer LNCS rather than CVF.
- **WACV** — Winter Conference on Applications of Computer Vision. Applications-focused; **often more relevant to industrial practitioners than CVPR**.
- **NeurIPS**, **ICML**, **ICLR** — general machine learning; much foundational vision work (ViT, DETR, diffusion) appears here.
- **BMVC**, **3DV**, **ICRA**/**IROS** (robotics vision), **ISARC** (International Symposium on Automation and Robotics in Construction — **the construction-specific venue**), and the journal *Automation in Construction* (Elsevier, paywalled) for construction applications.

**[CVF Open Access](https://openaccess.thecvf.com/menu)** hosts free PDFs of CVPR (2013–2024), ICCV (2013, 2015, 2017, 2019, 2023) and WACV (2020–2024) proceedings, as camera-ready versions with links to arXiv where available.

**arXiv cs.CV** ([arxiv.org/list/cs.CV/recent](https://arxiv.org/list/cs.CV/recent)) is where everything appears first, typically months before the conference. **Hugging Face Papers** ([huggingface.co/papers](https://huggingface.co/papers)) is now the best-curated daily filter over it, with linked model weights and demos.

## Datasets

### General-purpose

| Dataset | Scale | Task | Notes |
|---|---|---|---|
| **ImageNet / ILSVRC** | 1.28 M train images, 1,000 classes (ILSVRC subset); ~14 M in the full WordNet-structured set | Classification | The pretraining default. Registration required |
| **COCO** | ~118 k train / 5 k val images, 80 classes, boxes + instance masks + keypoints + captions | Detection, segmentation, pose, captioning | The detection benchmark. `pycocotools` is the evaluation reference |
| **Open Images V7** | 61.4 M image-level labels over 20,638 classes; 15,851,536 boxes over 600 classes; 2,785,498 instance masks over 350 classes; 3,284,280 relationship annotations; 675,155 localised narratives; 66,391,027 point-level annotations | Everything | The largest general set; annotation quality is more variable than COCO's |
| **Objects365, LVIS** | Large-vocabulary detection | Detection | LVIS is the long-tail benchmark |
| **ADE20K, Cityscapes, Mapillary Vistas** | Semantic segmentation | Scenes / driving | Cityscapes is the urban-scene reference |
| **KITTI, nuScenes, Waymo Open** | Driving, multi-sensor | Detection, tracking, depth, LiDAR | The multi-modal geometry benchmarks |
| **MegaDepth, ETH3D, Tanks and Temples, DTU** | Multi-view stereo and SfM | Reconstruction | ETH3D and Tanks and Temples are the standard MVS accuracy benchmarks |

### Industrial inspection

- **[MVTec AD](https://www.mvtec.com/company/research/datasets/mvtec-ad)** — over 5,000 high-resolution images across fifteen object and texture categories, with defect-free training images, anomalous test images, and pixel-precise anomaly annotations. The standard benchmark for **unsupervised anomaly detection in industrial inspection**, which is the correct formulation for most joinery and panel QC (`05`, `08`). **Licensed CC BY-NC-SA 4.0 — non-commercial use only.** MVTec also publishes **MVTec AD 2** and **MVTec 3D-AD**.
- **VisA**, **BTAD**, **MPDD**, **Real-IAD** — further anomaly-detection benchmarks with different licence terms.
- **DAGM 2007** — the classic weakly-supervised surface-defect set.

### Construction-specific

- **[SODA](https://arxiv.org/abs/2202.09554)** — Site Object Detection dAtaset: 19,846 annotated images with 286,201 objects across 15 classes (workers, materials, machines, layout), from multiple sites under varying conditions. Reported maximum 81.47 % mAP with YOLOv3/v4. The best-documented open construction detection set.
- **[SDNET2018](https://digitalcommons.usu.edu/all_datasets/48/)** — over 56,000 256 × 256 px sub-images from 230 16 MP originals of bridge decks (54), walls (72) and pavements (104), labelled cracked/uncracked, with cracks from 0.06 mm to 25 mm and deliberate confounders (shadows, surface roughness, scaling, holes). Maguire, Dorafshan & Thomas, Utah State University, 2018.
- **ACID** (Alberta Construction Image Dataset) — construction equipment detection.
- **CHV / Pictor-v3 / GDUT-HWD** — hard-hat and PPE detection sets of varying quality.
- **Roboflow Universe** ([universe.roboflow.com](https://universe.roboflow.com/)) — thousands of user-contributed construction, PPE and rebar datasets. **Highly variable label quality; always inspect before use** — many are re-uploads of each other with degraded annotations.
- **Structured3D, Matterport3D, ScanNet, 2D-3D-S** — indoor 3D scene understanding, relevant to Scan-to-BIM research.

> ⚠️ **Check the licence of every dataset before commercial use.** MVTec AD is non-commercial. ImageNet has a research-only term. Many Roboflow Universe sets have no clear provenance at all. A model trained on a non-commercially-licensed dataset is a contractual problem waiting to be discovered.

## Repositories and documentation

**Core libraries**
- [OpenCV documentation](https://docs.opencv.org/4.x/) — the 4.x tutorials are genuinely good; the Python tutorials are the fastest way to learn the API. Repo: `opencv/opencv`, `opencv/opencv_contrib`.
- [PyTorch](https://pytorch.org/docs/stable/index.html) and [torchvision](https://pytorch.org/vision/stable/index.html).
- [scikit-image](https://scikit-image.org/docs/stable/) — excellent gallery of worked examples; `regionprops` is worth knowing.
- [Kornia](https://kornia.readthedocs.io/) — differentiable CV in PyTorch.
- [timm](https://huggingface.co/docs/timm/index) — >700 pretrained backbones.

**Model zoos and training frameworks**
- [Ultralytics docs](https://docs.ultralytics.com/) — YOLO26, YOLO11, RT-DETR, SAM/SAM 2/SAM 3, YOLO-World, YOLOE. **AGPL-3.0** — check before shipping.
- [Detectron2](https://github.com/facebookresearch/detectron2) — Apache-2.0.
- [MMDetection / OpenMMLab](https://github.com/open-mmlab/mmdetection) — Apache-2.0, the widest open model zoo.
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/index) — DETR, SegFormer, Mask2Former, DPT, OWL-ViT, CLIP under one API.
- [segmentation_models.pytorch](https://github.com/qubvel-org/segmentation_models.pytorch) — U-Net and friends with any timm encoder.

**Geometry and 3D**
- [COLMAP](https://colmap.github.io/) — the SfM/MVS reference.
- [OpenMVG](https://github.com/openMVG/openMVG) and [OpenMVS](https://github.com/cdcseacave/openMVS) — modular, permissively licensed.
- [AliceVision / Meshroom](https://alicevision.org/) — GUI photogrammetry.
- [Open3D](https://www.open3d.org/) — point cloud processing, registration, visualisation. The practical toolkit for Scan-to-BIM work.
- [PDAL](https://pdal.io/) and [CloudCompare](https://www.cloudcompare.org/) — point cloud pipelines and interactive comparison; CloudCompare's cloud-to-cloud and cloud-to-mesh distance tools are the standard way to *show* an as-built deviation.
- [nerfstudio](https://docs.nerf.studio/) — NeRF and 3D Gaussian Splatting. Visualisation, not metrology (`02`).

**Data and evaluation**
- [CVAT](https://www.cvat.ai/), [Label Studio](https://labelstud.io/), [Roboflow](https://roboflow.com/).
- [FiftyOne](https://docs.voxel51.com/) — **the most under-used tool in applied vision.** It lets you browse a dataset, sort by model confidence, find annotation errors, find near-duplicates and visualise failure cases. Install it on day one of any project.
- [Albumentations](https://albumentations.ai/docs/), [supervision](https://github.com/roboflow/supervision) (annotation, tracking and zone utilities that save real time).

**Acquisition and edge**
- [Basler pylon / pypylon](https://www.baslerweb.com/en/software/pylon/), [Aravis](https://github.com/AravisProject/aravis), [Harvester](https://github.com/genicam/harvesters).
- [NVIDIA Jetson](https://developer.nvidia.com/embedded/jetson-modules), [DeepStream SDK](https://developer.nvidia.com/deepstream-sdk), [TensorRT](https://developer.nvidia.com/tensorrt).
- [OpenVINO](https://docs.openvino.ai/), [ONNX Runtime](https://onnxruntime.ai/).

## A suggested path from zero

1. **Weeks 1–3 — the physics.** First Principles of Computer Vision, Imaging and Features modules. Szeliski chapters 2 and 3. Work through file `01` of this domain and do both worked examples with your own numbers.
2. **Weeks 4–6 — the classical toolkit.** OpenCV Python tutorials end to end. Build the brick-counting project from `08` §11 — it needs no data and teaches thresholding, morphology, homography and Hough in one go.
3. **Weeks 7–9 — geometry.** First Principles Reconstruction I and II. Calibrate a real camera with a real checkerboard until you get under 0.3 px RMS. Then run COLMAP on a room and produce the accuracy report from Project C in `09`. **This is the exercise that separates people who can measure from people who cannot.**
4. **Weeks 10–14 — deep learning.** CS231n notes and assignments. Then fine-tune a YOLO11n on a small dataset you annotate yourself in CVAT — 300 images is enough to learn every step and every mistake.
5. **Weeks 15–20 — deployment.** Export to ONNX and TensorRT, run it on a Jetson or a Pi with an accelerator, measure real latency under thermal load, and integrate the output with something physical.
6. **Continuing.** Follow arXiv cs.CV via Hugging Face Papers weekly; read CVF Open Access papers when a topic becomes relevant; and — the highest-value habit — **look at your own failure cases in FiftyOne every week**.

## Sources

- [Richard Szeliski — Computer Vision: Algorithms and Applications (2nd ed.)](https://szeliski.org/Book/) — 2nd edition; PDF available from the site for personal use.
- [Deep Learning (Goodfellow, Bengio, Courville)](https://www.deeplearningbook.org/) — MIT Press 2016, complete HTML free.
- [Stanford CS231n](https://cs231n.stanford.edu/) — Spring 2026 offering; public notes at cs231n.github.io.
- [First Principles of Computer Vision](https://fpcv.cs.columbia.edu/) — Shree Nayar, Columbia; six modules, free video.
- [CVF Open Access](https://openaccess.thecvf.com/menu) — CVPR 2013–2024, ICCV 2013/15/17/19/23, WACV 2020–2024.
- [Open Images V7](https://storage.googleapis.com/openimages/web/index.html) — 61.4 M labels / 20,638 classes; 15,851,536 boxes / 600 classes; 2,785,498 masks / 350 classes; 675,155 localised narratives; 66,391,027 point labels.
- [MVTec AD](https://www.mvtec.com/company/research/datasets/mvtec-ad) — >5,000 images, 15 categories, pixel-precise annotations, CC BY-NC-SA 4.0; MVTec AD 2 and MVTec 3D-AD also published.
- [SODA (arXiv:2202.09554)](https://arxiv.org/abs/2202.09554).
- [SDNET2018 (Utah State University)](https://digitalcommons.usu.edu/all_datasets/48/).

## Open questions

- **The Hartley & Zisserman page at `robots.ox.ac.uk/~vgg/hzbook/` is disallowed to automated fetching** (robots.txt) and could not be verified in this pass. The book details (2nd edition, Cambridge University Press, 2004) are from general familiarity. `needs-verification`.
- **Szeliski's exact free-PDF URL was not captured**: the book's landing page was fetched and confirms a 2nd edition with drafts distributed for personal use, but the direct PDF link is served from a download page that is robots-disallowed. Navigate from szeliski.org/Book rather than deep-linking.
- **Simon Prince, *Understanding Deep Learning* (MIT Press, 2023)** is recommended from familiarity; its site was not fetched. `needs-verification`.
- **Forsyth & Ponce** edition/year (2nd, Pearson, 2011) not verified in this pass.
- **paperswithcode.com** was historically the standard benchmark-and-code index; its current operational status could not be confirmed in this pass (the fetch returned research summaries rather than a recognisable homepage). Prefer Hugging Face Papers and CVF Open Access as primary routes, and verify Papers with Code's status before relying on it.
- COCO and ImageNet figures quoted here are standard and widely repeated but were not re-verified against cocodataset.org / image-net.org in this pass.
