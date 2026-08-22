# Photo & Satellite Image Pipeline

*Deep-research digest, 2026-08-22. Part of the TEE research corpus — see [00-index.md](00-index.md). Grounds Phase 7 (TEE Extract).*

## Summary

Local photo/satellite preprocessing for TEE Extract is fully achievable with permissive-license, CPU-only tools: Pillow (MIT-CMU) covers EXIF/GPS/orientation, `exifread` (BSD-3) adds HEIC/RAW coverage, and ImageHash (BSD-2) gives phash dedupe at hamming <=5–10 on 64-bit hashes.

The decisive economic fact for crops and contact sheets: Claude bills images purely by rendered dimensions — `ceil(w/28) x ceil(h/28)` visual tokens (28x28 patches), capped at 1568 tokens (standard tier) or 4784 tokens / 2576 px long edge (Claude 4.7+) — so JPEG quality/bytes affect payload limits only, never tokens; a fixed-dimension contact sheet therefore caps N thumbnails at one bounded token cost, and budgeted crops are sized in pixels, not bytes. Claude never receives EXIF metadata, so local extraction is mandatory, not just an optimization.

For satellite work, web-mercator m/px = 40,075,016.686 x cos(lat) / 2^(z+8) (z19 ~0.30 m/px), smartphone GPS EXIF is only ~4.9 m accurate, and classical OpenCV (`opencv-python-headless`, Apache-2.0, ~35–61 MB wheel) plus open footprint datasets (Microsoft ODbL, Google CC-BY-4.0) beat heavy ML. If ML segmentation is wanted, MobileSAM (Apache-2.0, 9.66M params, ~3 s CPU) is the only CPU-practical choice, while FastSAM carries AGPL taint via `ultralytics`. Depth Anything V2 is CPU-feasible only in its Small variant (Apache-2.0, 24.8M params, ~0.1 s ONNX) but outputs relative (scale-ambiguous) depth — low value for dimensional conformance; recommend out of scope for v1.

## Findings

### EXIF: Pillow

Pillow 12.3.0, license MIT-CMU (SPDX), Python `>=3.10`. API: `Image.getexif()` returns an `Exif` object; GPS IFD via `exif.get_ifd(ExifTags.IFD.GPSInfo)`; the `ExifTags` module provides `TAGS` (16-bit tag id → name), `GPSTAGS` (8-bit GPS tag id → name) plus IntEnums `Base`, `GPS`, `IFD` (`IFD.Exif` = 34665), `Interop`, `LightSource`. Orientation is `Base` tag `0x0112`; `ImageOps.exif_transpose()` applies camera orientation to pixels. GPS lat/lon come back as (deg, min, sec) rationals plus `GPSLatitudeRef`/`GPSLongitudeRef` N/S/E/W — conversion to decimal degrees must be done in code. Pillow is already needed for all compositing/crop work, so it is the zero-marginal-cost EXIF option.

Source: [PyPI Pillow](https://pypi.org/project/Pillow/); [Pillow ExifTags reference](https://pillow.readthedocs.io/en/stable/reference/ExifTags.html)

### EXIF: exifread

ExifRead 3.5.1 (released 2025-08-23), BSD-3-Clause, pure Python, zero dependencies, Production/Stable. Reads TIFF, JPEG, JPEG XL, PNG, WebP, HEIC, RAW — broader format coverage than Pillow's EXIF path (notably HEIC from iPhones and camera RAW). Parses Image/Thumbnail/EXIF/GPS/Interoperability plus vendor MakerNote tags; usage: `tags = exifread.process_file(fh)`; speed knobs to skip makernotes/thumbnails. Read-only (no EXIF writing).

Source: [PyPI ExifRead](https://pypi.org/project/ExifRead/)

### EXIF: piexif

`piexif` 1.1.3, MIT license, last release July 2019 (~7 years unmaintained). Pure Python; reads AND writes EXIF (the only one of the three that writes), supports GPS IFD, insert/remove/transplant EXIF in JPEG and WebP; Python 2.7/3.5+. Fine as a write-back tool, stale for parsing modern formats (no HEIC).

Source: [PyPI piexif](https://pypi.org/project/piexif/)

### EXIF must be extracted locally — Claude never sees it

Anthropic vision docs FAQ: "No, Claude does not parse or receive any metadata from images passed to it." Therefore GPS, `DateTimeOriginal`, focal length, and orientation are invisible to the model unless TEE extracts them offline and emits them as structured text facts — this makes local EXIF extraction a hard requirement of the pipeline, not merely a token optimization.

Source: [Anthropic vision docs](https://platform.claude.com/docs/en/build-with-claude/vision.md)

### Perceptual-hash dedupe: ImageHash library

ImageHash 4.3.2 (2025-02-01), BSD 2-Clause, deps: Pillow + NumPy + SciPy (`fftpack` for phash). Algorithms: `ahash`, `phash` (DCT), `dhash`, `whash` (wavelet), `colorhash`, crop-resistant hash. Default `hash_size=8` → 64-bit hash; comparison is Hamming distance via operator overload (`hash1 - hash2`). Hashing operates on tiny grayscale downsamples (8x8 / 9x8), so per-image cost is dominated by JPEG decode+resize (milliseconds); naive O(n^2) comparison is fine for hundreds of site photos.

Source: [PyPI ImageHash](https://pypi.org/project/ImageHash/)

### Perceptual-hash thresholds (64-bit)

Consensus across dedupe literature/tools: distance 0 = identical fingerprint; 1–5 = near-duplicates (re-saves, recompression, minor edits) — safe auto-dedupe band; 6–10 = heavily edited versions, review band (the imagededup library's default `max_distance_threshold` is 10); >10 = usually visually distinct; ~14 only for aggressive-modification matching (high false-positive risk). phash is the most robust of ahash/dhash/phash to rescaling and compression. Recommended for TEE: phash with threshold <=5 for auto-collapse, 6–10 flagged as "similar burst shots".

Source: [imagededup hashing methods](https://idealo.github.io/imagededup/methods/hashing/); [cleanor.app Hamming distance reference](https://cleanor.app/reference/hamming-distance); [systemdesigner.net perceptual hashing](https://www.systemdesigner.net/technology/perceptual-hashing)

### Claude image token formula (governs all crop/sheet math)

Claude views images as 28x28-pixel patches: cost = `ceil(width/28) x ceil(height/28)` visual tokens. Two tiers:

- Standard (models before 4.7): max long edge 1568 px, max 1568 visual tokens.
- High-resolution (Claude 4.7 and later, automatic): max long edge 2576 px, max 4784 visual tokens.

Oversized images are auto-downscaled preserving aspect ratio to fit both limits (capping cost). Worked examples from docs: 200x200 = 64 tok; 1000x1000 = 1296 tok; 1092x1092 = 1521 tok; 1920x1080 = 1560 tok standard / 2691 tok high-res; 3840x2160 = 1560 standard / 4784 high-res. Derived budget table for the TEE crop server: 512x512 = 361 tok, 784x784 = 784 tok, 1092x1092 = 1521 tok, ~1932x1932 is the practical square ceiling on the high-res tier (~4761 tok).

Source: [Anthropic vision docs](https://platform.claude.com/docs/en/build-with-claude/vision.md)

### Bytes vs tokens: JPEG quality does NOT change token cost

Token cost is purely dimension-based; file bytes never enter the formula. Bytes matter only for transport limits: 10 MB max per base64 image on the Claude API (5 MB on Bedrock/Google Cloud), 32 MB per request, and latency. Anthropic explicitly warns heavy JPEG compression artifacts (especially repeated recompression) degrade model performance on text-bearing images — so TEE should serve crops at moderate quality (~q80), resized to the pixel budget, and avoid multi-pass recompression. For multiturn agent loops, base64 images are re-sent every turn; the Files API (upload once, reference `file_id`) keeps payloads small — a natural fit for TEE's extract-once model.

Source: [Anthropic vision docs](https://platform.claude.com/docs/en/build-with-claude/vision.md)

### Image count limits and the >20-image penalty

Max 8000x8000 px per image. Per request: 100 images (200k-context models) or 600 (1M-context models); but any request with >20 image blocks (counting resent history images and `tool_result` screenshots) triggers a stricter per-image dimension limit — keep every image <=2000 px per side or stay at <=20 images. This is a direct argument for contact sheets: one composited sheet replaces N image blocks and stays clear of the many-image regime.

Source: [Anthropic vision docs](https://platform.claude.com/docs/en/build-with-claude/vision.md)

### Contact sheets: evidence and correct economics

Evidence grids work: IG-VLM (arXiv 2403.18406) composites video frames into a single grid image and beats prior methods on 9 of 10 zero-shot video-QA benchmarks using an off-the-shelf VLM with no video training. Economics under Claude's patch billing: tokens scale with rendered area on BOTH paths, so a grid of cells at the same pixel size as individual images costs roughly the same tokens — the real wins are:

- (a) a fixed-dimension sheet CAPS cost at <=4784 tokens (high-res) / <=1568 (standard) no matter how many photos it holds;
- (b) it avoids the >20-image dimension penalty and per-image block overhead;
- (c) it lets the model pick which cell to request as a full-budget progressive crop.

Cell sizing: Anthropic warns accuracy degrades on images under ~200 px and requires text to stay legible; a 3x3 sheet on the high-res tier yields ~640–850 px effective cells (comfortably legible for photos); 4x4 → ~480–644 px; don't go past ~5x5 (cells approach the 200 px floor after downscale).

Source: [arXiv 2403.18406](https://arxiv.org/abs/2403.18406); [Anthropic vision docs](https://platform.claude.com/docs/en/build-with-claude/vision.md)

### Contact sheets: labeling and compositing

Anthropic's own multi-image guidance is to introduce each image with a short text label ("Image 1:", "Image 2:") so it can be referenced in prompts and follow-ups — for a single composited sheet the equivalent is burning a stable ID (e.g. `P3`, or row-col `A1`..`C3`) into each cell margin plus a text legend mapping IDs to filenames/EXIF facts. Compositing needs only Pillow: `Image.new` → `thumbnail`/`resize` → `paste` on grid → `ImageDraw.text` for cell IDs (use a solid label strip, not text over the photo, to survive downscale). No extra dependencies.

Source: [Anthropic vision docs](https://platform.claude.com/docs/en/build-with-claude/vision.md)

### Web-mercator ground resolution math

For 256-px tiles: meters/pixel = `C x cos(latitude) / 2^(zoom+8)`, with C = 40,075,016.686 m (equatorial circumference). At the equator: z15 = 4.777, z16 = 2.389, z17 = 1.194, z18 = 0.597, z19 = 0.299, z20 = 0.149, z21 = 0.0746 m/px; multiply by cos(lat) for other latitudes (e.g. at 45N, z19 ~0.211 m/px). Tile width in degrees longitude = `360/2^z`. Practical: building-scale measurement wants z19–z21 (0.07–0.30 m/px); a 10 m wall spans ~33 px at z19.

Source: [OSM wiki: Zoom levels](https://wiki.openstreetmap.org/wiki/Zoom_levels)

### Georeferencing accuracy reality check

GPS-enabled smartphones are typically accurate to ~4.9 m radius under open sky (GPS.gov figure), worse near buildings/trees — i.e., EXIF GPS error is comparable to half a house width, so GPS tags are good for locating the parcel / fetching the right satellite tile, but NOT for scaling the model. Scale should come from known dimensions: architectural drawing dims, a measured wall, or standard features (door ~0.9 m wide) — or from open footprint polygons. Pixel→meter calibration from two known points: `scale = known_distance_m / pixel_distance`.

Source: [GPS.gov accuracy archive](https://archive.gps.gov/systems/gps/performance/accuracy/) (via GPS.gov)

### opencv-python-headless

Version 5.0.0.93 (July 2026). OpenCV itself Apache-2.0; wrapper packaging MIT; bundles FFmpeg LGPLv2.1 (dynamically linked — compatible with an MIT server distribution; see `LICENSE-3RD-PARTY.txt`). Wheels 34.8–61.2 MB (manylinux x86-64 is the 61 MB end); the headless variant drops Qt/GUI deps (no `cv2.imshow`) — the correct choice for a server. Python 3.7–3.14.

Source: [PyPI opencv-python-headless](https://pypi.org/project/opencv-python-headless/)

### Classical footprint/roof-outline extraction with OpenCV

Standard recipe: convert to HSV/grayscale → bilateral filter (edge-preserving denoise) → Otsu or adaptive threshold (roofs are usually high-contrast vs vegetation/ground at z19–20) → morphological open/close → `cv2.findContours` → `cv2.approxPolyDP` (Douglas-Peucker) for polygon simplification; for rectilinear buildings, snap edges via dominant-gradient-angle quantization (arXiv 2007.05617). The literature is candid that pixel-based classical methods "struggle with noise, clutter, and variability in building appearances" — reliable when the target building is user-indicated (click/box prompt) and imagery is clean, brittle as an unattended detector. For TEE's use case (one known house, human-confirmed), classical + confirmation is adequate and zero-model-weight.

Source: [MDPI Remote Sensing 11(23):2803](https://www.mdpi.com/2072-4292/11/23/2803); [arXiv 2007.05617](https://arxiv.org/abs/2007.05617)

### Skip CV entirely: open building-footprint datasets

Microsoft Global ML Building Footprints: ~worldwide polygons, ODbL license (share-alike/attribution obligations on redistributed derived databases; using a polygon as a fact for one user's model is unproblematic), downloadable from Planetary Computer as partitioned gzip. Google Open Buildings: dual-licensed CC BY-4.0 OR ODbL v1.0 (user picks — CC BY-4.0 is the cleaner choice for an MIT project). VIDA combined Google+Microsoft dataset: ODbL. These give a ready-made georeferenced footprint polygon plus often height estimates for most structures — cheaper and more accurate than running segmentation on a tile.

Source: [OSM wiki: Microsoft Building Footprint Data](https://wiki.openstreetmap.org/wiki/Microsoft_Building_Footprint_Data); [source.coop VIDA google-microsoft-open-buildings](https://source.coop/vida/google-microsoft-open-buildings)

### SAM family: sizes, licenses, CPU practicality

- SAM 1 (`facebookresearch/segment-anything`): Apache-2.0 code+weights; ViT-B 91M params/375 MB, ViT-L 308M/1.25 GB, ViT-H 636M/2.56 GB; needs PyTorch+TorchVision, CUDA "strongly recommended" — the image-encoder pass on CPU is tens of seconds; superseded by SAM 2.
- SAM 2.1 (`facebookresearch/sam2`): Apache-2.0 (code, checkpoints, training code); checkpoints Tiny 38.9M/156 MB, Small 46M/184 MB, Base+ 80.8M/323 MB, Large 224.4M/898 MB (safetensors sizes); built for GPU video, still heavy on CPU.
- MobileSAM (`ChaoningZhang/MobileSAM`): Apache-2.0, TinyViT encoder 5M params, 9.66M total, ~3 s full inference on a Mac i5 CPU; README states it "can run on CPUs... no numerical degradation for real-world applications" — the one CPU-practical prompt-based segmenter, ~40 MB weights.
- EfficientSAM (`yformer/EfficientSAM`): Apache-2.0.
- FastSAM (`CASIA-IVA-Lab`): repo LICENSE Apache-2.0 BUT implemented on the `ultralytics` YOLOv8 package which is AGPL-3.0 — AGPL contamination risk for an MIT-licensed server; avoid.

Note all SAMs are class-agnostic (masks, not "building" labels): the pipeline is user/VLM supplies a point-or-box prompt on the roof → mask → `cv2.findContours` + `approxPolyDP` → polygon → meters via zoom-level scale.

Source: [segment-anything](https://github.com/facebookresearch/segment-anything); [sam2](https://github.com/facebookresearch/sam2); [MobileSAM](https://github.com/ChaoningZhang/MobileSAM); [EfficientSAM](https://github.com/yformer/EfficientSAM); [FastSAM](https://github.com/CASIA-IVA-Lab/FastSAM)

### Depth Anything V2: license split and CPU feasibility

Code Apache-2.0. Checkpoint licenses split by size: Small (24.8M params, ~100 MB fp32; fp16/int8 ONNX variants ~50/25 MB on onnx-community) is Apache-2.0; Base (97.5M), Large (335.3M), Giant (1.3B) are CC-BY-NC-4.0 — non-commercial, incompatible with an MIT tool in commercial use. Only Small is license-clean. CPU: ONNX Runtime benchmarks report ~0.1 s per 518x518 inference for V2-Small — fully CPU-feasible. Output is RELATIVE (scale-ambiguous) depth by default; metric-depth fine-tunes exist (Small/Base, indoor Hypersim / outdoor VKITTI2) but inherit domain limits. Verdict for TEE: single-image depth adds no reliable dimensional information (scale ambiguity defeats conformance checking); at best it hints at facade massing/roof pitch, which drawings and footprints already give. Recommend OUT OF SCOPE for Phase 7 v1; revisit only if users demand 3D-from-single-photo without drawings.

Source: [Depth-Anything-V2](https://github.com/DepthAnything/Depth-Anything-V2); [Depth-Anything-ONNX issue #26](https://github.com/fabio-sim/Depth-Anything-ONNX/issues/26); [onnx-community/depth-anything-v2-small](https://huggingface.co/onnx-community/depth-anything-v2-small)

## Recommendations for TEE

1. EXIF: use Pillow (already required for compositing; MIT-CMU) as the primary EXIF/GPS/orientation reader via `getexif().get_ifd(IFD.GPSInfo)` + `ImageOps.exif_transpose()`; add `exifread` (BSD-3) only if HEIC/RAW ingestion is in scope; skip `piexif` unless TEE needs to WRITE EXIF. Always extract EXIF locally — Claude receives zero image metadata.
2. Dedupe: ImageHash phash at default 64-bit; auto-collapse at hamming <=5, flag 6–10 as "similar shots" in the manifest (keep the sharpest via a cheap Laplacian-variance score); this runs in milliseconds per photo, pure BSD/MIT stack.
3. Build the crop/sheet server around Claude's patch formula (tokens = `ceil(w/28) x ceil(h/28)`, caps 1568/4784): express every media-serving tool parameter as a token budget and derive pixel dimensions from it; ignore JPEG bytes for cost (they only matter for the 10 MB/32 MB transport caps); serve JPEG q~80, never recompress twice.
4. Contact sheets: one labeled 3x3 or 4x4 Pillow-composited sheet (cell IDs burned into margins + text legend with per-cell EXIF facts) as the default photo-overview tool — it caps cost at <=4784 tokens regardless of photo count and dodges the >20-image 2000 px penalty; individual full-budget crops become the opt-in drill-down (progressive disclosure, matching TEE hard rules 1/5).
5. Satellite: hardcode the OSM ground-resolution formula (`C*cos(lat)/2^(z+8)`); target z19–z21 tiles; use EXIF GPS (~4.9 m error) only to locate the parcel, never to scale the model — take scale from drawing dimensions or footprint polygons.
6. Footprints: try open datasets first (Google Open Buildings under its CC BY-4.0 option preferred; Microsoft ODbL as fallback) before any pixel work; the classical `opencv-python-headless` recipe (bilateral → Otsu → `findContours` → `approxPolyDP`, optional gradient-angle rectilinear snapping) with human confirmation covers the rest with zero model weights.
7. If ML segmentation is added, make it an optional extra: MobileSAM (Apache-2.0, ~40 MB, ~3 s CPU) prompted by a user/VLM click-box, mask polygonized with OpenCV; do NOT ship FastSAM (AGPL taint via `ultralytics`) and do not bundle SAM 1/2 weights (0.4–2.6 GB, GPU-oriented).
8. Depth estimation: declare out of scope for Phase 7 v1 — relative depth is scale-ambiguous and adds nothing to dimensional conformance; if ever revisited, only Depth Anything V2-Small is license-clean (Apache-2.0) and CPU-fast (~0.1 s ONNX); Base/Large are CC-BY-NC and must not ship.
