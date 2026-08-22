# Video Pipeline

*Deep-research digest, 2026-08-22. Part of the TEE research corpus — see [00-index.md](00-index.md). Grounds Phase 7 (TEE Extract).*

## Summary

A fully local, zero-token video pipeline for TEE Extract is practical with permissively-licensed, pip-installable parts: PySceneDetect (BSD-3, bundles OpenCV) or raw ffmpeg `select='gt(scene,T)'` (T ≈ 0.3–0.5) for keyframes, `cv2.Laplacian(gray, cv2.CV_64F).var()` for sharpness filtering, and ImageHash (BSD-2) `phash`/`dhash` Hamming-distance dedupe. ffmpeg itself is pip-deliverable via `imageio-ffmpeg` (BSD-2 wrapper, ~20–31 MB bundled static binary) or `static-ffmpeg` (MIT, lazy-downloads ffmpeg 8.0 plus ffprobe); note that ffmpeg binaries built with libx264 are GPL, so invoke via subprocess only, never link.

For audio, `faster-whisper` (MIT, pip install, CTranslate2) is the clear CPU winner: small/int8 transcribes 13 minutes of audio in 1m42s (~7.6x realtime, 51 s batched) on an i7-12700K, with tiny/base several times faster still.

SfM is real but heavy: `pycolmap` (BSD-3, pip wheels for Linux/macOS/Windows, CUDA optional) makes COLMAP callable from Python 3.10–3.14, and its cameras/images/points3D output imports into Blender via the Photogrammetry Importer addon. But CPU-only dense reconstruction is slow and Meshroom needs CUDA for depth maps — so sparse-only pose recovery as an optional async job is the defensible v1 boundary.

DJI drones write per-second GPS telemetry (`[latitude:]` `[longitude:]` `[rel_alt:/abs_alt:]` `[iso:]` `[shutter:]`) as sidecar `.SRT` files or embedded subtitle streams extractable with `ffmpeg -map 0:s:0`, giving flight paths nearly for free. A timestamp index (keyframe time → `ffmpeg -ss` fast-and-frame-accurate re-fetch, accurate since ffmpeg 2.1) closes the loop for on-demand frame access without re-billing the video.

## Findings

### ffmpeg scene detection — `select` filter syntax

Canonical command:

```
ffmpeg -i input.mp4 -vf "select='gt(scene,0.4)',showinfo" -fps_mode vfr out_%04d.png
```

The `scene` variable is a 0–1 inter-frame difference score computed by the `select` filter. Community-documented threshold bands:

- 0.1–0.3 — high sensitivity (subtle transitions / fast camera motion, many frames)
- 0.4–0.5 — standard for hard cuts
- 0.6–0.7 — only massive changes

For handheld walkthrough / drone footage (continuous motion, no hard cuts), low thresholds around 0.2–0.3 are needed — or use fixed-interval sampling instead. `showinfo` prints `pts_time` for each selected frame (needed to build the timestamp index). Caveat: `select`'s scene score is NOT on the same scale as the newer `scdet` filter's `lavfi.scd.score` — thresholds are not interchangeable.

Source: [ffmpeg-cookbook.com scene detect](https://ffmpeg-cookbook.com/en/articles/scene-detect/) ; [bogotobogo ffmpeg thumbnails](https://www.bogotobogo.com/FFMpeg/ffmpeg_thumbnails_select_scene_iframe.php) ; [GDELT blog on ffmpeg scene detection](https://blog.gdeltproject.org/using-ffmpegs-scene-detection-to-generate-a-visual-shot-summary-of-television-news/)

### ffmpeg fast I-frame-only extraction

For a cheap first pass, extract only I-frames: `-vf "select='eq(pict_type,I)'"` — or use the input option `-skip_frame nokey`, which decodes only keyframes and is much faster since inter frames are never decoded. Typical H.264 GOP puts I-frames every 1–10 s, so this yields a bounded thumbnail set for long walkthroughs without full-decode scene scoring.

Source: [bogotobogo ffmpeg thumbnails](https://www.bogotobogo.com/FFMpeg/ffmpeg_thumbnails_select_scene_iframe.php)

### PySceneDetect — license, version, install, API

BSD-3-Clause. v0.7.1 (released 2026-07-21/22). `pip install scenedetect` (bundles `opencv-python` by default); variants `scenedetect-headless` (server, `opencv-python-headless`) and `scenedetect-core` (library only) exist. Requires Python >= 3.10. Three-line API:

```python
from scenedetect import detect, AdaptiveDetector, split_video_ffmpeg
scene_list = detect('video.mp4', AdaptiveDetector())
```

Returns `(start, end)` `FrameTimecode` pairs. The CLI also has save-images and CSV stats output.

Source: [PyPI scenedetect](https://pypi.org/project/scenedetect/) ; [scenedetect.com](https://www.scenedetect.com/)

### PySceneDetect — detector taxonomy

- `ContentDetector`: HSV-space adjacent-frame difference vs a fixed threshold (default 27.0), weighted hue/sat/luma/edge components, `luma_only` option; best for hard cuts.
- `AdaptiveDetector`: two-pass — `ContentDetector` scores then a rolling-average ratio (default adaptive threshold 3.0, `window_width` 2); explicitly designed to suppress false positives from camera motion — the right default for site-walkthrough/drone video.
- `ThresholdDetector`: mean pixel intensity for fades (default 12, `fade_bias`).
- `HashDetector`: DCT perceptual hash distance (default 0.395 normalized Hamming, size 16); robust to compression artifacts and fastest in benchmarks.
- `HistogramDetector`: Y-channel YUV histogram diff (default 0.05, 256 bins).

All support `min_scene_len` (default 15 frames; accepts `"0.6s"`-style strings).

Source: [PySceneDetect detector docs](https://www.scenedetect.com/docs/latest/api/detectors.html)

### PySceneDetect — accuracy/speed benchmark

Official benchmark (frame-exact 1:1 matching):

- BBC Planet Earth long-form — `AdaptiveDetector` F1 91.59% @ 36.12 s/video; `ContentDetector` 86.69% @ 37.02 s; `HashDetector` 83.10% @ 25.51 s (fastest).
- AutoShot short-form — Adaptive 73.86% @ 3.52 s; Content 69.26% @ 4.80 s; Hash 64.84% @ 4.14 s.
- ClipShots hard cuts — Content 55.84%; Adaptive 55.75%.

Hardware is not disclosed, so treat these as relative speeds; processing is roughly real-time-or-faster on desktop CPU for SD analysis (PySceneDetect internally downscales frames before scoring).

Source: [PySceneDetect benchmark README](https://github.com/Breakthrough/PySceneDetect/blob/main/benchmark/README.md)

### Sharpness filtering — variance of Laplacian

Standard blur/sharpness metric: `score = cv2.Laplacian(grayscale_img, cv2.CV_64F).var()`; higher = sharper (more edge energy). `CV_64F` is needed so negative second-derivative responses aren't clipped. There is no universal threshold — PyImageSearch's canonical article uses 100 as a starting point but stresses it is domain/tuning-dependent; resolution and downscaling change the score, so compare at a fixed working resolution. For keyframe pipelines the robust pattern is relative selection: within each detected scene/time bucket, keep the max-variance frame rather than applying an absolute cutoff — this handles motion blur in walkthrough video without calibration. Cost is one grayscale convolution per candidate frame (milliseconds at thumbnail resolution).

Source: [PyImageSearch blur detection](https://pyimagesearch.com/2015/09/07/blur-detection-with-opencv/) ; [TheAILearner variance-of-Laplacian](https://theailearner.com/2021/10/30/blur-detection-using-the-variance-of-the-laplacian-method/)

### Keyframe dedupe — ImageHash

ImageHash 4.3.2 (2025-02-01), BSD-2-Clause, `pip install ImageHash`; deps PIL/Pillow, numpy, scipy (`scipy.fftpack` for phash). Algorithms: `average_hash`, `phash` (DCT), `dhash` (gradient), `whash` (wavelet), `colorhash`, crop-resistant hash. Comparison is operator overload: `hash1 - hash2` = Hamming distance in bits. Default `hash_size=8` gives 64-bit hashes; the docs' guidance is to threshold the distance (`hash1 - hash2 < threshold`) — community practice for 64-bit phash/dhash near-duplicate detection is distance <= 5–10 (0 = identical); larger `hash_size` increases sensitivity. For drone orbits (same building from rotating viewpoints), dhash/phash dedupe collapses slow-orbit redundancy well; hashing thumbnails is sub-millisecond per frame.

Source: [PyPI ImageHash](https://pypi.org/project/ImageHash/)

### pip-installable ffmpeg — imageio-ffmpeg

imageio-ffmpeg 0.6.0 (2025-01-16), BSD-2-Clause wrapper, Python >= 3.9. Platform wheels EMBED a static ffmpeg executable: Windows x64 31.2 MB, Linux x64 29.5 MB, Linux aarch64 25.6 MB, macOS arm64 21.1 MB, macOS Intel 24.9 MB. `get_ffmpeg_exe()` resolves in order: `IMAGEIO_FFMPEG_EXE` env var → bundled binary → conda ffmpeg → system ffmpeg (so users can supply their own build). Also provides `read_frames()`/`write_frames()` generators and `count_frames_and_secs()`. Binaries come from the imageio-binaries repo; their exact configure flags/license are NOT documented on PyPI or in the repo tree — unverified, but typical static builds include libx264, which makes the binary GPL. No ffprobe is bundled.

Source: [PyPI imageio-ffmpeg](https://pypi.org/project/imageio-ffmpeg/) ; [GitHub imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) ; [imageio-binaries ffmpeg tree](https://github.com/imageio/imageio-binaries/tree/master/ffmpeg)

### pip-installable ffmpeg — static-ffmpeg

static-ffmpeg 3.0 (2026-01-16), MIT (package code). Installs BOTH ffmpeg and ffprobe ("all plugins and codecs" builds, currently ffmpeg 8.0) for win32/x64, macOS Intel+ARM, Linux x64+arm64. Lazy download: binaries are fetched on first use when `add_paths()` is called (blocks until downloaded) — smaller install, but requires network on first run, which matters for offline-first TEE deployments (imageio-ffmpeg's in-wheel binary avoids this). Bundled binary licenses are not stated on PyPI (sources at github.com/zackees/ffmpeg_bins); "all codecs" implies GPL components.

Source: [PyPI static-ffmpeg](https://pypi.org/project/static-ffmpeg/)

### ffmpeg licensing rules (for TEE's MIT posture)

FFmpeg core is LGPL 2.1+; compiling with `--enable-gpl` (needed for libx264/x265) makes the binary GPL 2+, and `--enable-nonfree` makes it unredistributable. Practical consequence: an MIT server may safely EXECUTE a GPL ffmpeg binary as a subprocess (separate process, no linking) — this is exactly what imageio-ffmpeg, static-ffmpeg, and PySceneDetect's `split_video_ffmpeg` do — but TEE should not statically or dynamically link `libav*` GPL builds, and if it REDISTRIBUTES ffmpeg binaries it inherits GPL source-offer/attribution obligations. Cleanest path: depend on imageio-ffmpeg/static-ffmpeg (they do the redistribution) or instruct users to `apt`/`brew install ffmpeg`.

Source: [ffmpeg.org/legal.html](https://ffmpeg.org/legal.html)

### CPU transcription — faster-whisper (recommended)

MIT, `pip install faster-whisper`, Python >= 3.9, CTranslate2 backend, NO system ffmpeg required (uses PyAV's bundled ffmpeg libs). Official CPU benchmark (13 min audio, small model, 8 threads, i7-12700K, beam 5):

| Implementation | Time | Memory |
|---|---|---|
| openai/whisper fp32 | 6m58s | 2335 MB |
| whisper.cpp fp32 | 2m05s | 1049 MB |
| whisper.cpp OpenVINO | 1m45s | 1642 MB |
| faster-whisper fp32 | 2m37s | 2257 MB |
| faster-whisper int8 | 1m42s | 1477 MB |
| faster-whisper int8 batch=8 | 51s | 3608 MB |

Computed realtime factors for small on that CPU: openai ~1.9x, whisper.cpp ~6.2x, faster-whisper int8 ~7.6x, batched int8 ~15.3x. tiny/base are several times faster again (OpenAI lists tiny ~10x and base ~7x relative speed vs large's 1x), so tiny/base int8 comfortably exceed 20x realtime on desktop CPU. Integrated Silero VAD (`vad_filter=True`) skips non-speech — important for walkthrough videos that are mostly ambient noise. Word-level timestamps are supported.

Source: [faster-whisper README benchmark tables](https://github.com/SYSTRAN/faster-whisper)

### CPU transcription — whisper.cpp and openai-whisper

whisper.cpp: MIT, plain C/C++. Model files: tiny 75 MiB / ~273 MB RAM, base 142 MiB / ~388 MB, small 466 MiB / ~852 MB, medium 1.5 GiB / ~2.1 GB, large 2.9 GiB / ~3.9 GB; integer quantization (e.g. `Q5_0`) shrinks further. No official pip package — Python access via pywhispercpp 1.5.0 (MIT, `pip install pywhispercpp`, wheels for Win/macOS-arm64/manylinux/musllinux, Py3.9–3.14, segment+token timestamps). Fastest CPU path on the official benchmark only with OpenVINO; CoreML gives >3x encoder speedup on Apple Silicon.

openai-whisper: MIT, `pip install -U openai-whisper`, REQUIRES system ffmpeg, pulls PyTorch (heavy dep), slowest CPU option (fp32 only). Model table: tiny 39M params, base 74M, small 244M, medium 769M, large 1550M, turbo 809M (~8x relative speed); `.en` variants are better for English at tiny/base sizes. Verdict: openai-whisper is dominated on CPU by both alternatives.

Source: [whisper.cpp](https://github.com/ggml-org/whisper.cpp) ; [openai/whisper](https://github.com/openai/whisper) ; [PyPI pywhispercpp](https://pypi.org/project/pywhispercpp/)

### SfM — COLMAP / pycolmap

COLMAP: BSD-3-Clause; runs on Linux/macOS/Windows; CUDA optional (recommended; also HIP/ROCm). Feature extraction/matching run on CPU with `--FeatureMatching.use_gpu 0` but are "significantly slower for large datasets"; incremental mapping dominates runtime (70–90% of total per third-party benchmarks).

pycolmap 4.1.1 (2026-07-17), BSD-3, `pip install pycolmap`, wheels for manylinux x86-64/macOS arm64/Windows x64, Py3.10–3.14, separate `pycolmap-cuda12` wheel (Linux only). Whole pipeline in 4 calls: `extract_features` → `match_exhaustive` (use `match_sequential` for video frames — exhaustive is O(N²)) → `incremental_mapping` → `maps[0].write()`. No authoritative published CPU wall-clock for 50–200 frames exists; expect tens of minutes for sparse CPU-only at that scale (sequential matching), with dense MVS on CPU impractically slow — treat sparse poses + sparse points as the CPU deliverable. Output: cameras/images/points3D as `.bin` or `.txt` (plus rigs/frames in COLMAP 3.12+); `model_converter` exports PLY, NVM, Bundler.

Source: [COLMAP install](https://colmap.github.io/install.html) ; [PyPI pycolmap](https://pypi.org/project/pycolmap/) ; [COLMAP output format](https://colmap.github.io/format.html) ; [COLMAP FAQ](https://colmap.github.io/faq.html)

### SfM — Meshroom and OpenSfM

Meshroom/AliceVision: MPL-2.0, prebuilt binaries for Windows/Linux, no pip. The DepthMap (dense) node is CUDA-only — official binaries are built with CUDA 12, compute capability >= 5.0; without an NVIDIA GPU only the low-quality "Draft Meshing" pipeline works (sparse-based meshing, no depth maps). GUI-first and heavyweight — a poor fit for a headless Python 3.11 server.

OpenSfM (Mapillary): BSD-2, but the repo now carries a notice that it is "no longer under active development" pointing to a successor fork; C++ extension build (Ceres etc.) is high-friction, no wheels.

Verdict: pycolmap is the only pip-clean, permissive, maintained option.

Source: [Meshroom](https://github.com/alicevision/Meshroom) ; [Meshroom CUDA FAQ](https://meshroom-manual.readthedocs.io/en/latest/faq/needs-cuda/needs-cuda.html) ; [Meshroom Draft Meshing wiki](https://github.com/alicevision/Meshroom/wiki/Draft-Meshing) ; [OpenSfM](https://github.com/mapillary/OpenSfM)

### SfM → Blender import path

Blender-Addon-Photogrammetry-Importer (current fork: CMartinRamos/SBCV-Blender-Addon-Photogrammetry-Importer) imports COLMAP model folders (BIN and TXT), workspaces, NVM, and PLY — plus Meshroom, OpenSfM, OpenMVG, Open3D, and VisualSFM formats — creating camera poses (optionally as an animated camera with background images) and the point cloud in the scene. It has a scriptable Python API, so TEE's Blender adapter can drive the import headlessly. Alternative without the addon: parse `cameras.txt`/`images.txt` (quaternion + translation per image) directly and create Blender cameras via `bpy` — the text format is simple and documented.

Source: [Photogrammetry Importer docs](https://blender-photogrammetry-importer.readthedocs.io/) ; [SBCV fork](https://github.com/CMartinRamos/SBCV-Blender-Addon-Photogrammetry-Importer) ; [COLMAP format](https://colmap.github.io/format.html)

### DJI drone telemetry — SRT format

When "Video Subtitles/Video Captions" is enabled pre-flight, DJI drones record telemetry either as a sidecar `.SRT` next to the `.MP4` (`DJI_0001.MP4` + `DJI_0001.SRT`) or as an embedded subtitle stream in the container. Standard SubRip blocks, one per second of video, e.g.:

```
1
00:00:00,000 --> 00:00:01,000
[latitude: -33.865143] [longitude: 151.209900]
[rel_alt: 42.300 abs_alt: 78.110] [iso: 100] [shutter: 1/240]
```

Fields include latitude/longitude, `rel_alt` (above takeoff), `abs_alt` (MSL), `iso`, `shutter`, `fnum`, `focal_len`. Field names vary by model/firmware (older drones use a `GPS(lon,lat,alt)` layout; some newer models log per-frame rather than per-second), so the parser needs a couple of regex variants. Parsing is trivially implementable in-house (regex over SRT blocks) — no heavyweight dependency needed.

Source: [Swyvl: mapping DJI drone video GPS](https://swyvl.io/blog/how-to-map-dji-drone-video-gps/) ; [DJI Telemetry Overlay SRT viewer](https://djitelemetryoverlay.com/srt-viewer/) ; [srt-to-gpx](https://github.com/arru/srt-to-gpx)

### DJI telemetry — extraction commands and existing Python tooling

Embedded track: probe with `ffprobe -v error -select_streams s -show_entries stream=index,codec_name -of json input.MP4`, then demux with `ffmpeg -i input.MP4 -map 0:s:0 out.srt` (the telemetry subtitle is typically `mov_text`; e.g. Mini 4K and the Air series embed it). Newer models additionally carry proprietary `djmd`/`dbgi` DATA streams (flight/debug metadata) that survive only in MKV remuxes — not needed when the SRT/subtitle telemetry is present.

Existing OSS: dji-drone-metadata-embedder 2.11.0 (2026-08-20), MIT, Python >= 3.10, pip-installable — parses DJI SRT telemetry and exports GPX/CSV/GeoJSON/KML/CoT/HTML maps; tested on Mini 3/4 Pro, Mini 5 Pro, Air 3/3S, Avata 2/360, Mavic 3 Enterprise, Matrice 300; depends on ffmpeg (+ optional ExifTool). Useful as a reference implementation or optional dependency; the core parse is small enough to vendor as a regex parser.

Source: [dji-drone-metadata-embedder](https://github.com/CallMarcus/dji-drone-metadata-embedder) ; [PyPI dji-drone-metadata-embedder](https://pypi.org/project/dji-drone-metadata-embedder/) ; [Mux: extracting subtitles with ffmpeg](https://www.mux.com/articles/extracting-subtitles-and-captions-from-video-files-with-ffmpeg)

### Timestamped extraction index — ffmpeg `-ss` semantics

Since ffmpeg 2.1, `-ss` BEFORE `-i` (input seeking) is both fast AND frame-accurate when re-encoding: it seeks by index to the keyframe before the target, then decodes and discards frames up to the exact timestamp. `-noaccurate_seek` restores the legacy keyframe-snap behavior. `-ss` AFTER `-i` (output seeking) decodes from the start — slow, with no accuracy benefit in modern ffmpeg. With `-c copy`, accuracy is always keyframe-bounded regardless of `-ss` placement (cuts snap to keyframes), so stream-copy is unsuitable for exact-frame fetches. Therefore the on-demand single-frame fetch is:

```
ffmpeg -ss <t> -i video.mp4 -frames:v 1 -q:v 2 out.jpg
```

— near-instant even deep into long files. Index pattern: at extract time, record for each kept keyframe `{frame_id, pts_time (from showinfo or PySceneDetect FrameTimecode), scene_id, sharpness_score, phash, file path}`; the model then references frames by id/timestamp, and any tool can re-materialize the exact frame later from the source video at zero storage cost beyond the index row.

Source: [ffmpeg-micro on -ss seeking](https://www.ffmpeg-micro.com/blog/ffmpeg-ss-t-to-seeking) ; [TechEarl: ffmpeg trim/cut](https://techearl.com/ffmpeg-trim-cut-video)

## Recommendations for TEE

1. Keyframe stack for v1: PySceneDetect (BSD-3, pip, Py >= 3.10) with `AdaptiveDetector` (motion-tolerant, best F1 in official benchmarks) as the scene segmenter; within each scene pick the sharpest frame by max `cv2.Laplacian(gray, CV_64F).var()` (relative selection, no absolute threshold to tune); dedupe survivors with ImageHash phash/dhash at Hamming distance <= 8 on 64-bit hashes. For continuous-motion walkthrough/drone footage where "scenes" barely exist, add a fallback sampler: 1 frame every N seconds (N ≈ 2–5) followed by the same sharpness+dedupe funnel — this matters more than cut detection for the driving use case.
2. Ship ffmpeg via imageio-ffmpeg (binary inside the wheel — works offline, aligns with TEE's local-first constraint) and call `get_ffmpeg_exe()` with subprocess; fall back to system ffmpeg via its built-in resolution order. Do not link `libav*`; document that the bundled binary is GPL-built (subprocess use keeps the MIT server clean). Use static-ffmpeg only if ffprobe is needed and network-on-first-run is acceptable, or ship a tiny ffprobe-free probe using imageio-ffmpeg's `count_frames_and_secs()`.
3. Audio: use faster-whisper (MIT, pip, no system ffmpeg) with `model='base'` or `'small'`, `compute_type='int8'`, `vad_filter=True` as the default CPU transcriber (~7.6x realtime for small/int8 on an i7; tiny/base much faster). Emit segment-level timestamps into the same extraction index as keyframes so narration ("this is the north wall") is time-aligned with imagery. Skip openai-whisper entirely (PyTorch dep, ~4x slower); consider pywhispercpp only if the CTranslate2 wheel is unavailable on a target platform.
4. SfM: declare full reconstruction OUT of scope for v1 core, but expose an OPTIONAL async job built on pycolmap (BSD-3, pip wheels, Py3.10–3.14, CUDA optional) limited to SPARSE output: `extract_features` → `match_sequential` (never exhaustive for video) → `incremental_mapping`, capped at ~100–200 keyframes. Deliverable = camera poses + sparse points (cameras/images/points3D), imported to Blender via the Photogrammetry Importer addon or a small `bpy` parser of the documented text format. Reject Meshroom (CUDA-only dense, GUI-first, MPL-2.0) and OpenSfM (unmaintained repo notice, painful C++ build). Be explicit in docs that CPU-only runs take tens of minutes and dense/MVS requires the `pycolmap-cuda12` wheel — this is why it's an async job, not an inline tool call.
5. DJI telemetry: implement a ~50-line regex SRT parser in-house (handle bracketed `[latitude:]`/`[longitude:]` and legacy `GPS(...)` layouts) rather than adding a dependency; auto-discover sidecar `.SRT` next to the video and fall back to ffprobe-detect + `ffmpeg -map 0:s:0` demux of embedded tracks. Emit the flight path as a compact polyline of `(t, lat, lon, rel_alt, abs_alt)` downsampled to turning points — this georegisters drone keyframes against satellite imagery for the site-model use case at near-zero cost. Keep dji-drone-metadata-embedder (MIT) as a reference implementation, not a dependency.
6. Extraction index schema: one JSON/SQLite table per video with `{frame_id, pts_time, scene_id, sharpness, phash, thumb_path, (lat, lon, alt if telemetry), nearest transcript segment}`. On-demand full-res re-fetch tool: `ffmpeg -ss <pts_time> -i src -frames:v 1 out.jpg` (input seeking; fast and frame-accurate since ffmpeg 2.1; never use `-c copy` for frame fetches — keyframe-bounded). This makes the model's default view a few hundred tokens of index rows, with any pixel data strictly opt-in per TEE hard rules 1 and 4.
