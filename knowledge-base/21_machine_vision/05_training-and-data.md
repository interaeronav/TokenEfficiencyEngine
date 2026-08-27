---
id: vision.training
title: Training and data — datasets, annotation, augmentation, metrics and small-team MLOps
domain: 21_machine_vision
tags: [dataset, annotation, cvat, label-studio, roboflow, coco, yolo-format, pascal-voc, augmentation, albumentations, transfer-learning, loss-functions, map, iou, class-imbalance, active-learning, mlops]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "CVAT", url: "https://www.cvat.ai/", publisher: "CVAT.ai", accessed: 2026-08-25}
  - {title: "Label Studio documentation", url: "https://labelstud.io/guide/", publisher: "HumanSignal", accessed: 2026-08-25}
  - {title: "Object Detection Datasets Overview (YOLO format)", url: "https://docs.ultralytics.com/datasets/detect/", publisher: "Ultralytics", accessed: 2026-08-25}
  - {title: "Albumentations documentation", url: "https://albumentations.ai/docs/", publisher: "Albumentations", accessed: 2026-08-25}
  - {title: "COCO — Common Objects in Context", url: "https://cocodataset.org/#format-data", publisher: "COCO Consortium", accessed: 2026-08-25}
related: [vision.deep_learning, vision.deployment, vision.construction]
---

# Training and data — datasets, annotation, augmentation, metrics and small-team MLOps

**Summary.** Model architecture is now a solved, commoditised choice; data is where projects are won and lost. This file covers how to construct a dataset that will actually generalise, the annotation tools and interchange formats you will meet, the discipline of splitting data correctly, augmentation that helps versus augmentation that lies, transfer learning and fine-tuning recipes, the loss functions and metrics you must be able to interpret, the diagnosis of overfitting and class imbalance, active learning, and the minimum viable MLOps for a team of two to five people. Worked examples use construction and joinery data because those are the honest hard cases: few labels, extreme class imbalance, and a distribution that shifts every week.

## Key facts

| Item | Value |
|---|---|
| YOLO label format | one row per object: `class x_center y_center width height`, all normalised 0–1, class zero-indexed |
| COCO bbox format | `[x_min, y_min, width, height]` in **absolute pixels** |
| Pascal VOC bbox format | XML, `[xmin, ymin, xmax, ymax]` in **absolute pixels** |
| Standard split | 70/15/15 or 80/10/10 train/val/test — but **split by scene, not by image** |
| IoU | `area(∩) / area(∪)`; detection TP threshold usually 0.5 |
| COCO mAP | mean AP over IoU thresholds 0.50:0.05:0.95 and over classes |
| CVAT export formats | 19 formats including Pascal VOC, YOLO, COCO, Cityscapes, KITTI |
| CVAT Online pricing | Free tier; Solo ~$33/mo ($23 annual); Team from ~$66/mo; Enterprise from ~$12,000/yr |
| Rule of thumb, fine-tuning a detector | ≥ 150–300 instances **per class**, ≥ 1,500 images, for a usable first model |

## Dataset construction

The dataset defines the operating envelope. A model will not work outside the conditions represented in its training data, and it will fail *confidently*, which is worse than failing loudly.

**Enumerate the axes of variation before capturing anything.** For a site PPE detector these are: time of day and sun angle; weather; camera height and angle; distance to subject (which sets the pixel height of a person); occlusion by plant, scaffold and other workers; helmet colours and brands; high-vis in different states of filth; season; and the specific sites themselves. Sample deliberately across each axis rather than shooting 3,000 frames of one Tuesday morning.

**Negatives are data.** Images with no positive instances teach the model what the background looks like and cut false positives sharply. For detection, budget **10–20 % background-only images**. In YOLO format these simply have no `.txt` file.

**Hard negatives are the most valuable data you own.** The traffic cone that reads as a person, the orange bucket that reads as a hard hat, the timber offcut that reads as a defect. Mine these from production failures and add them to the training set — this single loop drives more improvement than any architecture change.

**Label definition documents beat label counts.** Write a one-page rulebook before annotation begins: what counts as an instance, how to handle partial occlusion (label if > 30 % visible?), truncation at frame edges, the minimum size to label, and the treatment of ambiguous cases. Then have two annotators label the same 100 images and measure agreement. Inter-annotator IoU below ~0.7 means your class definition, not your model, is the problem.

**Dataset size, honestly.** A single-class detector on a visually distinctive object in a controlled scene can work at 300–500 labelled images. A multi-class site detector needs thousands. A defect segmenter for a rare defect may need active learning (below) because you cannot collect enough positives by random sampling. Starting from a strong pretrained backbone changes these numbers by roughly an order of magnitude in your favour.

## Annotation tools

| Tool | Model | Strengths | Watch out for |
|---|---|---|---|
| **CVAT** | Open-source community edition, self-hostable; CVAT Online SaaS | Video interpolation, 3D cuboids and point clouds, skeletons, 19 export formats, SAM-assisted masks | Self-hosting is a real ops job (Docker Compose, Postgres, Redis, storage) |
| **Label Studio** | Community (open source) + Enterprise | Widest data-type coverage (image, text, audio, video, time series), ML backend for pre-annotation, very flexible config XML | Image-heavy workflows are less slick than CVAT's |
| **Roboflow** | Commercial SaaS with a free tier | Fastest path from photos to a trained model; automatic format conversion, augmentation, hosted inference, Roboflow Universe public datasets | Vendor lock-in on the pipeline; check data-ownership and privacy terms before uploading client site imagery |
| **Labelme** | Open source, MIT | Trivial to install, good for small polygon jobs | No team features, no video |
| **Supervisely, V7, Scale, SuperAnnotate** | Commercial | Managed workforces, QA workflows, enterprise features | Cost |

**Use model-assisted annotation from day one.** The workflow that works: label 100 images by hand → train a weak model → run it over the next 500 → correct its output rather than drawing from scratch. Correction is roughly 3–5× faster than drawing. Add SAM/SAM 3 click-to-mask for segmentation and the gain for polygons is closer to 10×. Both CVAT and Label Studio support attaching a model backend for exactly this.

> ⚠️ Site photography frequently contains identifiable workers, vehicle registrations, and client-confidential information. Before uploading to any SaaS annotation platform, confirm the contractual position on data processing and, where the workforce is identifiable, the lawful basis for processing (GDPR/POPIA equivalents). Face and plate blurring at ingest is cheap insurance and rarely harms model performance for PPE or progress tasks.

## Annotation formats

**YOLO** — one `.txt` per image, alongside an `images/`+`labels/` tree, plus a dataset YAML:

```
dataset_root/
├── images/train/img1.jpg …   ├── images/val/…
└── labels/train/img1.txt …   └── labels/val/…
```

```
# img1.txt   class  x_center y_center  width  height   (all normalised 0–1)
0 0.5 0.4 0.3 0.6
2 0.7 0.3 0.15 0.2
```

```yaml
# ppe.yaml
path: /data/ppe
train: images/train
val: images/val
test: images/test
names:
  0: person
  1: hardhat
  2: no-hardhat
  3: vest
```

**COCO** — a single JSON with top-level `info`, `licenses`, `images`, `annotations`, `categories`. Each detection annotation carries `id`, `image_id`, `category_id`, `bbox` as `[x, y, width, height]` in absolute pixels, `area`, `iscrowd`, and `segmentation` (polygon list or RLE). The de facto interchange format and the one the evaluation tooling (`pycocotools`) expects.

**Pascal VOC** — one XML per image with `<object><bndbox><xmin><ymin><xmax><ymax>`. Legacy but still widely emitted.

Conversion is a solved problem: `fiftyone`, `pylabel`, `Roboflow`, CVAT's exporter, or twenty lines of Python. **The one trap: bbox conventions.** YOLO is centre+size normalised, COCO is corner+size absolute, VOC is corner+corner absolute. Off-by-a-convention bugs produce boxes that look "almost right" and destroy mAP silently.

```python
def coco_to_yolo(bbox, img_w, img_h):
    x, y, w, h = bbox                       # COCO: absolute x_min,y_min,w,h
    return ((x + w/2)/img_w, (y + h/2)/img_h, w/img_w, h/img_h)
```

## Splitting data

**Split by scene, not by frame.** If you extract 30 frames from one video and shuffle them across train and val, near-duplicate images end up on both sides and your validation score becomes meaningless — typically inflated by 10–25 mAP points. Group by site, by day, by camera position, by production batch, and split at the group level. `sklearn.model_selection.GroupShuffleSplit` exists for this.

**Hold out a test set you touch once.** Validation is used continually for early stopping and hyperparameter choice, so it is contaminated by the end of a project. A properly quarantined test set — ideally from a *different site or a later time period* — is the only honest estimate of deployment performance.

**Temporal splits are the realistic ones for construction.** Train on January–March, validate on April, test on May. This measures what you actually care about: does the model survive the distribution shift of a project moving from substructure to superstructure?

## Augmentation

Augmentation synthesises plausible variation you failed to capture. **Albumentations** is the default library: fast, supports images, masks, bounding boxes, oriented boxes, keypoints, video and volumetric data, and integrates with PyTorch, TensorFlow/Keras and JAX.

```python
import albumentations as A

train_tf = A.Compose([
    A.RandomResizedCrop(size=(640, 640), scale=(0.5, 1.0), p=1.0),
    A.HorizontalFlip(p=0.5),
    A.RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.3, p=0.7),
    A.HueSaturationValue(hue_shift_limit=8, sat_shift_limit=25, p=0.4),
    A.OneOf([A.MotionBlur(blur_limit=7), A.GaussianBlur(blur_limit=7)], p=0.3),
    A.ImageCompression(quality_range=(45, 95), p=0.3),
    A.RandomShadow(p=0.2),
    A.RandomSunFlare(src_radius=120, p=0.1),
    A.CoarseDropout(p=0.2),
], bbox_params=A.BboxParams(format="yolo", label_fields=["class_labels"],
                            min_visibility=0.3))

out = train_tf(image=img, bboxes=boxes, class_labels=labels)
```

**Choose augmentations that match real variation.**
- Site imagery: brightness/contrast, shadow, sun flare, motion blur, JPEG compression, rain/fog, and scale variation. **Do not** use vertical flip — gravity is a real prior; a person is never upside-down.
- Aerial/drone imagery: full rotation *is* valid, because there is no canonical up.
- Joinery/panel inspection under controlled light: heavy photometric augmentation actively hurts, because it destroys the lighting invariance you paid for. Use small geometric jitter only.
- Colour-discriminating tasks (grading by colour, finish matching): **do not** use hue shift. You will train the model to ignore the signal.

**Mosaic and MixUp** (built into the YOLO training pipelines) paste four images into one, giving strong scale and context variation. Ultralytics disables mosaic for the final ~10 epochs (`close_mosaic`) because it distorts the box distribution near convergence. **Copy-paste** augmentation for instance segmentation — pasting rare-class instances into other images — is the single most effective trick for rare-defect classes.

**Synthetic data** deserves a mention for construction: rendering a BIM model in Blender or Unreal with domain randomisation (materials, lighting, camera pose) generates perfectly labelled images for free. It works well for geometric tasks (element presence, pose) and poorly for appearance tasks (weathering, dirt, defects) without domain-adaptation effort.

## Transfer learning and fine-tuning

Almost never train from scratch. The standard recipe:

1. **Start from ImageNet/COCO-pretrained weights** (or a self-supervised backbone such as DINOv2 when your domain is far from natural images).
2. **Freeze early layers initially** if you have very little data (< 1,000 images). Early convolutions encode edges and textures that transfer perfectly. Unfreeze progressively.
3. **Use discriminative learning rates**: backbone at 0.1× the head's rate.
4. **Warmup** for 3–5 epochs, then **cosine decay**.
5. **AdamW** with weight decay ≈ 0.01–0.05 as default; SGD+momentum 0.9 when reproducing published detector recipes.
6. **Early stopping** on the validation metric you actually care about, with patience of 15–30 epochs.
7. **Domain-adaptive pretraining** when you have lots of unlabelled in-domain images: continue self-supervised pretraining on them before fine-tuning. Cheap and effective for site imagery.

```python
from ultralytics import YOLO
m = YOLO("yolo11s.pt")
m.train(data="ppe.yaml", epochs=150, imgsz=960, batch=16,
        optimizer="AdamW", lr0=0.001, lrf=0.01, warmup_epochs=3,
        freeze=10,                 # freeze first 10 modules
        close_mosaic=10, patience=25, device=0,
        project="runs/ppe", name="v3_960px")
```

Note `imgsz=960` rather than 640: on site imagery, workers are frequently 40–60 px tall, and **input resolution is usually a bigger lever than model size for small-object performance**.

## Loss functions

| Task | Loss | Notes |
|---|---|---|
| Multi-class classification | Cross-entropy, often with label smoothing 0.1 | Smoothing improves calibration |
| Multi-label classification | Binary cross-entropy per class | Classes not mutually exclusive |
| Heavy class imbalance | **Focal loss** `−α(1−p)^γ log p`, γ=2 | Down-weights easy examples; the fix RetinaNet introduced |
| Box regression | **CIoU / DIoU / GIoU** | Directly optimise overlap; far better than L1/L2 on coordinates |
| Segmentation, balanced | Cross-entropy | |
| Segmentation, thin/rare structures (cracks!) | **Dice loss**, or Dice + BCE | Cross-entropy alone lets the model predict all-background and score 99 % |
| Metric learning / retrieval | Triplet, contrastive, ArcFace | For "is this the same panel?" style tasks |
| Depth | Scale-and-shift-invariant loss, SILog | |

## Metrics — and how to be honest about them

**Confusion matrix** first, always. From it:

- **Precision** = TP/(TP+FP) — of what I flagged, how much was right.
- **Recall** = TP/(TP+FN) — of what existed, how much did I find.
- **F1** = harmonic mean.
- **Specificity** = TN/(TN+FP).

**Choose the operating point by cost.** For a safety application (missing an unhelmeted worker), recall dominates and you accept false alarms — until alarm fatigue makes operators ignore the system, which is a real and frequently fatal failure mode. For an automated reject on a joinery line, a false reject costs a good panel and a false accept costs a customer complaint; the ratio of those costs sets the threshold, not a default of 0.5.

**IoU** = `area(∩)/area(∪)`. A detection is a true positive if IoU with a ground-truth box of the same class exceeds a threshold, conventionally 0.5.

**AP and mAP.** Average Precision is the area under the precision–recall curve for one class. **mAP@0.5** averages AP across classes at IoU 0.5 (the Pascal VOC convention). **mAP@[.50:.95]** — the COCO primary metric — averages over ten IoU thresholds from 0.50 to 0.95 in steps of 0.05, and is much stricter because it rewards precise localisation.

> ⚠️ mAP is a benchmark aggregate and is nearly useless as an operational specification. It integrates over confidence thresholds you will never deploy at, and over IoU thresholds that may be irrelevant to your task (does a crack detector care about IoU 0.9?). **Report precision and recall at your actual deployed threshold, on your quarantined test set, per class.** Then report mAP for comparability.

**Segmentation metrics:** mean IoU (mIoU) per class, Dice coefficient, boundary F-score. For crack width measurement, the meaningful metric is the error in millimetres against a calibrated reference — not IoU.

**Calibration.** Neural networks are systematically overconfident. If your workflow routes "confidence > 0.9" straight through and sends the rest to a human, you need the confidence to *mean* something. Check with a reliability diagram and Expected Calibration Error; fix with temperature scaling on the validation set. Cheap, and it makes human-in-the-loop workflows sane.

## Overfitting and class imbalance

**Diagnosis.** Training loss falling while validation loss rises is overfitting. Both flat and high is underfitting or a broken pipeline. **Always visualise a batch of augmented training images with their labels drawn on** before believing any loss curve — a large fraction of "the model won't learn" problems are label-format bugs visible in ten seconds.

**Remedies, in order of effect:** more and more varied data → stronger augmentation → transfer learning from a better backbone → regularisation (weight decay, dropout, stochastic depth) → smaller model → early stopping.

**Class imbalance** is the norm in inspection: 10,000 good panels for every defect. Approaches:
1. **Reframe as anomaly detection.** Train only on good examples and flag deviation. PatchCore, PaDiM and SPADE (all benchmarked on **MVTec AD**) do this well and need *no* defect examples. **This is very often the right answer for a joinery or panel line** and is under-used.
2. **Oversample the minority / undersample the majority**, or use a weighted sampler.
3. **Class-weighted or focal loss.**
4. **Copy-paste augmentation** of rare instances.
5. **Two-stage cascade:** a cheap high-recall classical filter, then a model on the survivors.

## Active learning

When labelling is the bottleneck — always — spend the labelling budget on informative images rather than random ones.

```python
# Uncertainty sampling loop
# 1. Train on the labelled pool L.
# 2. Predict on unlabelled pool U.
# 3. Score each image by informativeness.
# 4. Send the top-k to annotation. Repeat.

def informativeness(dets):
    """Detection uncertainty: prefer images with boxes near the decision
    boundary and images with disagreement between augmented views."""
    if len(dets) == 0:
        return 0.5                      # empty predictions are ambiguous
    conf = np.array([d.conf for d in dets])
    return float(np.mean(1.0 - np.abs(2*conf - 1.0)))   # peaks at conf 0.5
```

Better strategies combine **uncertainty** with **diversity** (cluster embeddings, sample across clusters so you do not label 200 near-identical frames) and **coverage** (core-set selection). Simplest effective version for a small team: run the current model over a week of site photos, sort by mean uncertainty, label the top 200, retrain. Three cycles of this typically beats labelling 2,000 random images.

## Minimum viable MLOps for a small team

You do not need Kubeflow. You need reproducibility and the ability to answer "which model is in production and what was it trained on?"

1. **Version the data.** `DVC` or `git-lfs` for the annotation files plus content-addressed image storage (S3/MinIO). At minimum, every dataset is an immutable, dated, hashed snapshot. Never mutate a dataset in place.
2. **Version the config.** Every training run is fully described by a YAML in git. No notebook-only runs.
3. **Track experiments.** MLflow (self-hosted, open) or Weights & Biases (SaaS, generous free tier). Log config, metrics, the confusion matrix, and a grid of failure images. The failure grid is the artefact you will actually look at.
4. **Register models.** A model registry entry records: run id, dataset hash, git commit, metrics on the quarantined test set, the export artefacts (ONNX/TensorRT), and an approval flag.
5. **Test the model like code.** A pytest suite that runs the exported model over a fixed set of ~50 "golden" images and asserts on per-image outputs, plus asserts on aggregate precision/recall floors. This catches export bugs (quantisation, preprocessing mismatch, colour-channel order) which are far more common than training bugs.
6. **Monitor in production.** Log input statistics (brightness, blur, detection counts per hour) and alert on drift. Sample 1 % of production images back into the labelling pool. Without this loop the model degrades silently as the site changes.
7. **Keep a rollback.** The previous model artefact and the ability to switch in under five minutes.

**Preprocessing parity is the number one deployment bug.** The training pipeline resizes with one interpolation and normalises with one set of means; the C++ inference wrapper does something subtly different; accuracy drops 15 points and nobody knows why. Serialise the preprocessing spec with the model and assert it in the golden-image test.

## Sources

- [CVAT](https://www.cvat.ai/) — annotation types incl. point clouds/3D cuboids/skeletons; 19 export formats incl. Pascal VOC, YOLO, COCO, Cityscapes, KITTI; pricing tiers.
- [Label Studio guide](https://labelstud.io/guide/) — Community and Enterprise editions, ML backend integration and pre-annotation import.
- [Ultralytics — detection dataset format](https://docs.ultralytics.com/datasets/detect/) — `class x_center y_center width height` normalised 0–1, dataset YAML keys, directory layout, "no .txt needed for background images".
- [Albumentations](https://albumentations.ai/docs/) — target-aware support for masks, bounding boxes, oriented boxes, keypoints, video and 3D; framework integrations.
- [COCO dataset](https://cocodataset.org/#format-data).

## Open questions

- The COCO JSON field list given here (`info/licenses/images/annotations/categories`; `bbox = [x, y, w, h]` absolute; `area`, `iscrowd`, `segmentation`) is standard and correct to the best of my knowledge, but the fetched page returned only navigation content — **not directly verified in this pass**. `needs-verification`.
- CVAT Online pricing figures were read from the vendor site on the access date and change frequently.
- The "≥ 150–300 instances per class" heuristic is practitioner folklore (it appears in Ultralytics and Roboflow guidance) rather than a research result.
