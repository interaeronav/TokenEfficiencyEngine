---
id: vision.deep_learning
title: Deep learning for vision — architectures, task families and current models
domain: 21_machine_vision
tags: [cnn, resnet, efficientnet, vision-transformer, yolo, detr, rt-detr, unet, mask-rcnn, sam, pose-estimation, depth-anything, ocr, foundation-models]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Ultralytics supported models", url: "https://docs.ultralytics.com/models/", publisher: "Ultralytics", accessed: 2026-08-25}
  - {title: "YOLO26", url: "https://docs.ultralytics.com/models/yolo26/", publisher: "Ultralytics", accessed: 2026-08-25}
  - {title: "YOLO11", url: "https://docs.ultralytics.com/models/yolo11/", publisher: "Ultralytics", accessed: 2026-08-25}
  - {title: "RT-DETR", url: "https://docs.ultralytics.com/models/rtdetr/", publisher: "Ultralytics", accessed: 2026-08-25}
  - {title: "SAM 3: Segment Anything with Concepts", url: "https://github.com/facebookresearch/sam3", publisher: "Meta AI / GitHub", accessed: 2026-08-25}
  - {title: "Depth Anything V2", url: "https://github.com/DepthAnything/Depth-Anything-V2", publisher: "GitHub", accessed: 2026-08-25}
  - {title: "timm documentation", url: "https://huggingface.co/docs/timm/index", publisher: "Hugging Face", accessed: 2026-08-25}
related: [vision.classical, vision.training, vision.deployment, vision.construction]
---

# Deep learning for vision — architectures, task families and current models

**Summary.** Since 2012 the dominant approach to uncontrolled-scene vision has been learned representations. This file covers the mechanics that matter (convolution, pooling, residual connections, attention), the architecture lineage from LeNet to Vision Transformers, and then the six task families you will actually deploy — classification, detection, segmentation, pose, depth and OCR — each with named current-generation models, their performance figures where verified, licences, and where to obtain weights. The emphasis throughout is on choosing the smallest model that meets the requirement, because a YOLO11n at 40 % mAP running at 100 FPS on a Jetson solves more real problems than a 57 % model that needs a datacentre.

## Key facts

| Model | Task | Figure | Source |
|---|---|---|---|
| YOLO26n / s / m / l / x | Detection | COCO mAP 40.9 / 48.6 / 53.1 / 55.0 / 57.5; T4 TensorRT 1.7 / 2.5 / 4.7 / 6.2 / 11.8 ms | Ultralytics, Jan 2026 |
| YOLO11n / s / m / l / x | Detection | COCO mAP 39.5 / 47.0 / 51.5 / 53.4 / 54.7; 2.6 / 9.4 / 20.1 / 25.3 / 56.9 M params | Ultralytics, Sep 2024 |
| RT-DETR-L / X | Detection | 53.0 / 54.8 AP on COCO val2017; 114 / 74 FPS on T4 | Ultralytics; arXiv:2304.08069 |
| SAM 3 | Promptable concept segmentation | 848 M params; 54.1 cgF1 on SA-Co/Gold (human 74.0) | Meta, GitHub |
| Depth Anything V2 | Monocular depth | S 24.8 M / B 97.5 M / L 335.3 M params | GitHub, Jun 2024 |
| timm | Pretrained backbones | > 700 models | Hugging Face |

## CNN fundamentals

**Convolution.** A small learned kernel slides over the input, computing a weighted sum at every position. Three properties make it right for images: *local connectivity* (nearby pixels are related), *weight sharing* (an edge detector is useful everywhere, so learn it once), and *translation equivariance* (shifting the input shifts the output). Output size for input `W`, kernel `k`, padding `p`, stride `s`: `(W − k + 2p)/s + 1`.

**Receptive field.** The region of the input that influences one output unit. It grows linearly with depth for stride-1 convolutions and multiplicatively with pooling/striding. **If the receptive field of your final feature map is smaller than the object you need to recognise, no amount of training will fix it** — this is the real reason small-object detection needs multi-scale features.

**Pooling and striding.** Max-pool or stride-2 convolutions reduce spatial dimensions, expanding the receptive field and cutting compute. Modern architectures increasingly use strided convolutions instead of pooling.

**Batch normalisation** normalises activations per mini-batch, which stabilises and accelerates training and permits much higher learning rates. Its descendants — LayerNorm, GroupNorm — matter when batch sizes are tiny (as in detection or segmentation on large images). **GroupNorm is the pragmatic choice when your batch size is 2.**

**Activations.** ReLU is the default; GELU and SiLU/Swish dominate in transformers and modern detectors.

**Loss and optimisation.** Cross-entropy for classification, various regression and matching losses for detection (`05`). SGD with momentum still wins some benchmarks; AdamW is the practical default. Learning-rate warmup plus cosine decay is the standard schedule.

## The architecture lineage

**LeNet-5 (LeCun, 1998).** Two conv layers, two pooling layers, fully connected head. Read cheques. Established the template.

**AlexNet (2012).** Eight layers, ReLU, dropout, GPU training, aggressive augmentation. Won ImageNet by a margin that ended the hand-crafted-feature era.

**VGG (2014).** Depth via stacks of 3×3 convolutions only. Elegant, enormously parameter-heavy (VGG-16 ≈ 138 M params). Still used as a perceptual-loss feature extractor.

**Inception / GoogLeNet (2014).** Parallel multi-scale branches in one block, 1×1 convolutions as cheap channel mixers/reducers.

**ResNet (2015).** The residual connection `y = F(x) + x` made networks of 50, 101 and 152 layers trainable by giving gradients an identity path. **This is the single most consequential architectural idea in the field** and appears in essentially everything since, transformers included. ResNet-50 remains the default backbone for comparisons.

**DenseNet, ResNeXt, SE-Net (2016–17).** Refinements: dense connectivity, grouped convolutions, channel attention ("squeeze-and-excitation").

**MobileNet v1–v3, ShuffleNet (2017–19).** Depthwise-separable convolutions cut the multiply-accumulate cost by roughly `1/k² + 1/C`. The foundation of edge vision.

**EfficientNet (2019) / EfficientNetV2 (2021).** Compound scaling — scale depth, width and input resolution together by a fixed ratio rather than one at a time. Delivered ImageNet accuracy at far fewer FLOPs; V2 fixed the training-speed regression with fused MBConv blocks and progressive resizing.

**Vision Transformer (ViT, 2020).** Split the image into 16×16 patches, linearly embed them, add positional encodings, and run a standard transformer encoder. No convolution at all. Beats CNNs *given enough data* (JFT-300M scale); underperforms them on small datasets, because it lacks the convolutional inductive bias. DeiT showed distillation and heavy augmentation could train ViTs on ImageNet-1k alone.

**Swin Transformer (2021).** Windowed attention with shifted windows, giving hierarchical multi-scale features at linear rather than quadratic cost. The transformer that actually works as a detection/segmentation backbone.

**ConvNeXt (2022).** A ResNet modernised with transformer-era design choices (large kernels, LayerNorm, GELU, inverted bottlenecks). Matched Swin, and made the point that much of the transformer advantage was training recipe rather than attention.

**Self-supervised backbones (2021– ).** MAE (masked autoencoding), DINOv2 and DINOv3 (self-distillation). **DINOv2/v3 features are the pragmatic default when you have many unlabelled images and few labelled ones** — a frozen DINO backbone plus a linear probe is often a startlingly strong baseline for a niche industrial classification task. Weights on Hugging Face.

**CLIP and open-vocabulary models (2021– ).** Image and text encoders trained on 400 M web pairs into a shared embedding space, giving zero-shot classification by comparing an image embedding to text prompts. This spawned open-vocabulary detection (OWL-ViT, Grounding DINO, YOLO-World, YOLOE) and open-vocabulary segmentation (SAM 3). For a construction application, being able to write "person without a hard hat" instead of labelling 5,000 images is genuinely transformative — with the caveat that zero-shot performance on domain-specific classes is markedly below a fine-tuned specialist model.

## Task family 1 — classification

One label (or a set of labels) per image. Use it when the question is "which of N states is this?" — e.g. is this site photo showing bare slab / formwork / rebar placed / concrete poured; is this timber board grade A/B/C.

```python
import timm, torch
model = timm.create_model("convnext_tiny.fb_in22k_ft_in1k",
                          pretrained=True, num_classes=5)
cfg   = timm.data.resolve_model_data_config(model)
tf    = timm.data.create_transform(**cfg, is_training=False)
```

`timm` carries over 700 pretrained models and is the correct place to get a backbone. Practical defaults: **ConvNeXt-Tiny or EfficientNetV2-S** for server-side, **MobileNetV3 / EfficientNet-Lite / MobileViT** for edge, **DINOv2 ViT-S/14 frozen + linear head** when data is scarce.

## Task family 2 — object detection

Boxes plus class labels. Three lineages:

**Two-stage (R-CNN → Fast → Faster R-CNN → Mask R-CNN).** A region proposal network suggests candidate boxes, a second head classifies and refines them. Slower, historically more accurate on small objects, still the reference in Detectron2 and MMDetection.

**One-stage anchor/anchor-free (SSD, RetinaNet, FCOS, YOLO).** Predict boxes directly on a dense grid. RetinaNet introduced **focal loss** to fix the extreme foreground/background imbalance this creates.

**Transformer / set-prediction (DETR → Deformable DETR → DINO-DETR → RT-DETR).** DETR (2020) reframed detection as direct set prediction with bipartite Hungarian matching, removing anchors *and* NMS. Original DETR converged very slowly; Deformable DETR and DINO fixed that. **RT-DETR** (Baidu, arXiv:2304.08069) made the approach real-time with an efficient hybrid encoder — RT-DETR-L reaches 53.0 AP on COCO val2017 at 114 FPS on a T4, RT-DETR-X 54.8 AP at 74 FPS.

### The YOLO family, as of 2026

Ultralytics currently supports YOLOv3, v5, v6, v7, v8, v9, v10, YOLO11, YOLO12 and **YOLO26**, plus RT-DETR, YOLO-NAS, YOLO-World and YOLOE. The two that matter for new work:

- **YOLO11** (Sep 2024) — the conservative production choice, very widely deployed, well documented, plenty of community weights. YOLO11m reaches 51.5 mAP with 22 % fewer parameters than YOLOv8m.
- **YOLO26** (Jan 2026) — native end-to-end **NMS-free** inference via a one-to-one head, Distribution Focal Loss removed to simplify the detection head, MuSGD optimiser, Progressive Loss and STAL for small objects. Ultralytics claims up to 43 % faster CPU ONNX inference for the nano variant. Covers detection, instance and semantic segmentation, depth, classification, pose and oriented bounding boxes.

```python
from ultralytics import YOLO

model = YOLO("yolo11n.pt")               # or "yolo26n.pt"
results = model.train(data="ppe.yaml", epochs=100, imgsz=640,
                      batch=16, device=0, patience=20)
metrics = model.val()
print(metrics.box.map, metrics.box.map50)

model.export(format="engine", half=True) # TensorRT for Jetson (file 06)
```

> ⚠️ **Licensing.** Ultralytics YOLO (v5, v8, 11, 26) is AGPL-3.0. Using it in a product you distribute — or arguably in a network-accessible service — obliges you to release your source under the same terms unless you buy an Ultralytics Enterprise Licence. This is the most commonly overlooked commercial risk in applied vision. Permissive alternatives: **RT-DETR** (Apache-2.0 via PaddlePaddle/Ultralytics-independent implementations), **Detectron2** (Apache-2.0), **MMDetection** (Apache-2.0), **YOLOX** (Apache-2.0), **torchvision** detection models (BSD).

**Oriented bounding boxes (OBB)** deserve a mention for construction: a rotated box fits a length of rebar, a stack of timber, or a ceiling tile far better than an axis-aligned one. YOLO11-obb and YOLO26-obb support this natively (trained on DOTA).

## Task family 3 — segmentation

**Semantic segmentation** labels every pixel with a class. **Instance segmentation** additionally separates individual objects. **Panoptic** unifies both.

- **U-Net (2015)** — encoder–decoder with skip connections. Small, trainable on a few hundred images, still the best default for binary defect segmentation (cracks, spalls, stains, delamination). `segmentation_models_pytorch` gives U-Net with any timm backbone in three lines.
- **DeepLabv3+** — atrous/dilated convolutions and spatial pyramid pooling for multi-scale context. In torchvision.
- **Mask R-CNN (2017)** — Faster R-CNN plus a per-RoI mask branch and RoIAlign. Reference instance segmenter; Detectron2.
- **SegFormer, Mask2Former** — transformer segmenters; Mask2Former unifies semantic, instance and panoptic under one masked-attention architecture.
- **YOLO11-seg / YOLO26-seg** — fast instance segmentation, real-time on edge hardware.

### The SAM lineage

**SAM** (Segment Anything, 2023) introduced promptable segmentation: click a point or draw a box and get a mask, zero-shot, on essentially anything. **SAM 2** (2024) extended this to video with a memory mechanism, giving object tracking through occlusion. **SAM 3** is a unified foundation model for promptable segmentation in images and video that adds *promptable concept segmentation* — give it a short text phrase or exemplars and it exhaustively segments every instance of that open-vocabulary concept. It has 848 M parameters (a DETR-based detector and a transformer encoder–decoder tracker sharing a vision encoder), was trained via a data engine covering over 4 million unique concepts, and scores 54.1 cgF1 on the SA-Co/Gold benchmark against a human baseline of 74.0. **SAM 3.1 Object Multiplex** (March 2026) added shared-memory multi-object tracking. Released under the "SAM License" — check it before commercial use.

**The practical use of SAM in a construction workflow is annotation, not inference.** Click-to-mask cuts polygon annotation time by roughly an order of magnitude; CVAT, Label Studio and Roboflow all integrate SAM-family models for this (`05`).

## Task family 4 — pose estimation

Keypoint localisation on a skeleton. Two paradigms: **top-down** (detect person, then find keypoints in each crop — more accurate, cost scales with person count) and **bottom-up** (find all keypoints, then group them — constant cost, better in crowds).

- **OpenPose** — the historical reference, bottom-up, part affinity fields. Non-commercial licence.
- **HRNet** — maintains high-resolution representations throughout; the accuracy reference.
- **YOLO11-pose / YOLO26-pose** — real-time, COCO 17-keypoint, easy to fine-tune.
- **MediaPipe Pose / BlazePose** — Google, runs on a phone CPU, 33 keypoints, Apache-2.0.
- **RTMPose / MMPose** — strong open-source real-time option, Apache-2.0.

Construction relevance: ergonomic risk assessment (awkward lifting postures), fall detection, and — more reliably — determining *whether a detected person is on a ladder, bending, or working at height*, which turns a crude person detector into a useful safety signal.

## Task family 5 — monocular depth estimation

Predict per-pixel depth from a single image. Two flavours: **relative/affine-invariant depth** (correct up to unknown scale and shift — good for visualisation, occlusion ordering, segmentation priors) and **metric depth** (actual metres — needs known intrinsics or a fine-tuned metric head).

- **MiDaS** (Intel/ISL) — the model that made robust cross-dataset relative depth practical, trained on a mix of datasets with a scale-and-shift-invariant loss. DPT variants added transformer backbones.
- **Depth Anything V2** (June 2024) — a foundation model for monocular depth with markedly better fine detail than V1. Small 24.8 M, Base 97.5 M, Large 335.3 M parameters. **Licences differ by size: the Small model is Apache-2.0; Base/Large are CC-BY-NC-4.0** — so the commercially usable one is the Small model. Metric-depth variants based on Small and Base were released in June 2024. Related releases: *Prompt Depth Anything* (Dec 2024) for 4K metric depth guided by low-resolution LiDAR, and *Video Depth Anything* (Jan 2025) for temporally consistent depth over long videos.
- **UniDepth, Metric3D, ZoeDepth** — metric-depth-focused alternatives.

> ⚠️ Do not use monocular depth for survey or dimensional work. Even metric variants carry errors of several percent of range and are not traceable to any standard. Use them for scene understanding, occlusion reasoning and visual effects — and use photogrammetry, stereo or LiDAR (`02`) when a number has to be defensible.

## Task family 6 — OCR and text/code reading

Two sub-problems: **detection** (where is the text) and **recognition** (what does it say).

- **Tesseract** — the classical open engine. Adequate on clean documents, poor on scene text.
- **EasyOCR, PaddleOCR, docTR** — modern deep pipelines. **PaddleOCR** is generally the strongest open option for multilingual scene text and has a very small mobile variant.
- **Detection backbones:** DBNet, CRAFT, EAST. **Recognition:** CRNN + CTC, TrOCR (transformer), PARSeq.
- **VLM-based reading (2024– ).** General vision-language models now read documents, drawings and photographs of labels with impressive robustness and no training. For low-volume, high-variability reading — a delivery note photographed on site, a stamp on a steel section, a handwritten site diary — a VLM is often the correct engineering choice over a bespoke OCR pipeline.
- **Industrial code reading** (1D barcode, Data Matrix, QR) is a *solved, non-deep-learning* problem: use ZXing/zbar open source, or Cognex/Keyence/HALCON readers for the hard direct-part-marking cases. Do not train a network for this.

## Choosing a model — the decision that saves the project

1. **Can you control the scene?** Yes → try classical first (`03`). Most factory-side joinery problems are here.
2. **Is the question "where" or "how big"?** "How big" → detect with a network, measure with calibrated geometry.
3. **How many labelled examples can you actually get?** Under ~200 per class → use a frozen foundation backbone (DINOv2, CLIP) with a small head, or a promptable model (SAM 3, Grounding DINO), not a from-scratch detector.
4. **What is the latency and power budget?** Fix this before choosing the model (`06`). It usually forces a nano/small variant, which then forces higher input resolution or tighter cropping to keep small objects detectable.
5. **What licence can you ship?** AGPL YOLO is fine for internal tooling and a liability in a product.

## Sources

- [Ultralytics — supported models](https://docs.ultralytics.com/models/)
- [Ultralytics — YOLO26](https://docs.ultralytics.com/models/yolo26/) — Jan 2026, NMS-free, DFL removed, MuSGD/Progressive Loss/STAL, variant mAP and T4 latency table.
- [Ultralytics — YOLO11](https://docs.ultralytics.com/models/yolo11/) — Sep 2024, params/FLOPs/mAP/latency table.
- [Ultralytics — RT-DETR](https://docs.ultralytics.com/models/rtdetr/) — Baidu, arXiv:2304.08069, RT-DETR-L 53.0 AP @ 114 FPS T4, RT-DETR-X 54.8 AP @ 74 FPS; RTDETRv2 arXiv:2407.17140.
- [facebookresearch/sam3](https://github.com/facebookresearch/sam3) — 848 M params, promptable concept segmentation, 54.1 cgF1 SA-Co/Gold, SAM 3.1 Object Multiplex (27 Mar 2026), SAM License.
- [DepthAnything/Depth-Anything-V2](https://github.com/DepthAnything/Depth-Anything-V2) — 14 Jun 2024; S 24.8 M (Apache-2.0), B 97.5 M / L 335.3 M (CC-BY-NC-4.0); metric variants 22 Jun 2024.
- [timm documentation](https://huggingface.co/docs/timm/index) — >700 pretrained models.

## Open questions

- Ultralytics AGPL-3.0 licensing is stated from general familiarity and the widely reported terms; the licence file was **not** fetched in this pass. Verify directly before any commercial deployment. `needs-verification`.
- Parameter counts for historical architectures (VGG-16 ≈ 138 M) and ImageNet dataset scales are from familiarity, not fetched.
- DINOv3 is referenced as an existing successor to DINOv2; its release details were not verified in this pass.
