# 44 — TRELLIS.2 defect corpus (2026-08-22)

Sources: local clones (upstream @75fbf01, trellis-mac @d58628f,
stableprojectorz @d5d38f1); microsoft/TRELLIS.2 GitHub issues (~170 walked);
HF discussions; ComfyUI-Trellis2 troubleshooting wiki. Fixability classes:
[pure-python] / [kernel] / [model]. Reddit was unfetchable; Reddit-only
claims are cited via the fork README that references them.

## P0 — Geometry correctness defects

- **Hard-threshold logit instability → scattered surface holes / missing triangles.** The decoder makes hard binary decisions at `subdiv.feats > 0` (child-voxel creation, `trellis2/models/sc_vaes/sparse_unet_vae.py:63`) and intersection logits `h.feats[..., 3:6] > 0` (quad emission, `trellis2/models/sc_vaes/fdg_vae.py:101`). Logits within ~±0.001 of zero flip per-platform: a ROCm port measured ~220K boundary edges pre-fill (tens of thousands of micro-defects); "Globally biasing the decisions positive (bias += 0.1) halves the defect count but visibly changes the generation… applying the same shift only at decode time has no effect." Evidence: https://github.com/microsoft/TRELLIS.2/issues/169 (no maintainer response). Mitigable [pure-python] (decision margins, fp32 accumulation); a true fix is training-time margin regularization [model].
- **fp16 rounding at the same thresholds → "vertical lines"/hair-spike stray quads** (same root cause, same-platform variant). StableProjectorz fix: cast decoder output to fp32 before extraction — "fp16 rounding near zero creates stray quads that appear as vertical line/hair artifacts in the mesh" (stableprojectorz `trellis2/pipelines/trellis2_image_to_3d.py`, decode_shape_slat Step 3; credit to visualbruno per the fork README, citing reddit.com/r/StableDiffusion/comments/1r197yy). Fix exists, [pure-python].
- **Raw decoder mesh has holes; correctness depends on `cumesh.fill_holes` post-hoc.** Upstream calls fill_holes 4× (`trellis2/pipelines/trellis2_image_to_3d.py:474`; `o-voxel/o_voxel/postprocess.py:110,144,157`, `max_hole_perimeter=3e-2`). trellis-mac disables it entirely ("Metal port segfaults on decoder-sized meshes… Output meshes may have small holes", README.md:150); stableprojectorz also stripped all fill_holes calls from its pipeline (grep: zero call sites) with no reported quality collapse — suggesting holes are small and a CPU/robust hole-filler suffices. [pure-python] vs upstream's [kernel] CuMesh.
- **Messy internal structures**: junk geometry generated under clothing/skin ("a character wearing a tshirt - but there is a messy body structure built underneath", skull outlines, interior faces on fingers). https://github.com/microsoft/TRELLIS.2/issues/25. [model]; mitigable downstream by voxel-connectivity/visibility culling.
- **Stray triangles, hairs, non-manifold edges, degenerate faces in the remesh branch.** Upstream's remesh path skips the cleanup loop the non-remesh branch has; the fork adds `remove_duplicate_faces/repair_non_manifold_edges/remove_small_connected_components/unify_face_orientations` after remesh plus zero-area-face removal ("degenerate (zero-area) faces that cause xatlas normal assertion failures", stableprojectorz `o-voxel/o_voxel/postprocess.py`). [pure-python].
- **Fine detail / text loss**: meshes "Distort letters heavily, Randomize strokes and edges, Lose sharp corners and inner cut-outs" even from clean input (issues/57). Staircase artifacts after VAE roundtrip at 512 (issues/127). [model].
- **Silent resolution downgrade**: the cascade quantizes HR coords and drops resolution in 128-steps until tokens < `max_num_tokens` (default 49152) — "Due to the limited number of tokens, the resolution is reduced" (`trellis2/pipelines/trellis2_image_to_3d.py:328-339`). Loop-guard bug: breaks only at `hr_resolution == 1024`; the fork corrects to `<= 1024`. [pure-python].

## Texture / material defects

- **Alpha lost on GLB export**: texture alpha is baked but export hardcodes `alpha_mode='OPAQUE'` and passes uint8 `baseColorFactor` where trimesh expects float RGBA (`o-voxel/o_voxel/postprocess.py:285,298,302`; README:174 documents manual re-wiring). Fix known (BLEND + float32 factor): issues/91 (closed). [pure-python].
- **4K texture indistinguishable from 2K** (issues/33, no response). Root cause from the bake code: texels are trilinear samples of the voxel `attr_volume` at grid resolution (postprocess.py:259-266), so texture detail is bounded by O-Voxel resolution, not `texture_size`. [model] (attr resolution) / [pure-python] (stop advertising 4K, or add 2D up-detailing).
- **Seams / bake artifacts**: UV charts from cumesh cone-clustering; seam count vs distortion controlled by `mesh_cluster_threshold_cone_half_angle_rad` (postprocess.py:53, default 90°); UV-boundary gaps patched by `cv2.inpaint` TELEA dilation "to prevent black seams" (postprocess.py:288-293). Community guidance: 45-60° = more charts/seams, 90-120° = fewer (deepwiki.com/visualbruno/ComfyUI-Trellis2/6-troubleshooting-and-faq). [pure-python].
- **Black/reflective spots on bright objects**: "weird black spots on the texture" despite correct topology; image level/contrast tweaks only reduce them (issues/162). Root cause UNVERIFIED (plausibly metallic-channel misprediction). [model], mitigable via metallic clamp/despeckle post-pass.
- **Bake quality on Mac fallback paths**: the grid_sample fallback "can leave mild ring artifacts on curved surfaces"; the KDTree baker's "coverage near UV chart boundaries is slightly softer" (trellis-mac README.md:146,157). [kernel] (Metal) or [pure-python].

## Export & postprocess defects

- **GLB extraction failures at high res**: 1536 extraction fails "WARNING TOO BIG (stack overflow)" at ~18 GB VRAM (issues/13); the HF demo's extraction fails on large meshes (issues/8). nvdiffrast hard cap 2^24 triangles — `mesh.simplify(16777216) # nvdiffrast limit` (example.py:26). [pure-python] (pre-simplify / cap DC res).
- **Pathological remesh waste**: narrow-band dual contouring at full grid res — "At 1024 DC produces ~41M faces only to simplify to ~200K (99.5% waste). At 512 DC produces ~10M — still 50x the target — saving ~2-3GB VRAM" (fork comment + `dc_resolution = min(resolution, 512)` cap, stableprojectorz postprocess.py). Explains "GLB extraction time is too long (maximum 50mins)" vs <1 min generation (issues/44). [pure-python].
- **Data toolkit segfault**: `textured_mesh_to_volumetric_attr` C++ segfaults intermittently on valid Objaverse GLBs (~3M voxels @1024³), even single-worker (issues/30). [kernel/C++].

## Memory / OOM behavior

- Baseline: 24 GB VRAM minimum, A100/H100-verified, Linux-only (README:59-60); `low_vram` defaults True (trellis2_image_to_3d.py:107) and swaps whole models CPU↔GPU per stage.
- **OOM on an A100 80GB with low_vram disabled** running stock example.py (issues/55, unanswered) — peaks are pathological, not model-size-bound.
- **Quantified peaks (fork analysis, 1024³, 10.7M voxels, fp16)**: decoder skip-connection ~935 MB; a full-tensor norm2 doubles 1310 MB feats to a 2620 MB peak "that leaves ~1.3GB of dead fragments in the CUDA reserved pool"; conv neighbor_map 1.16 GB coexisting with 1.37 GB feats; im2col fragmentation keeps ~4 GB reserved with ~500 MB allocated (stableprojectorz `sparse_unet_vae.py`, `conv_flex_gemm.py` comments). All fixed in the fork via chunked norm/MLP/skip (200K-1M row chunks), CPU-bounce defragmentation, 64MB-capped chunked im2col, CPU accumulation of large outputs, `_LazyCudaSubs` one-at-a-time skip loading — result: "fit better into 8GB gpus, even with 1024³ voxels" (fork README). All [pure-python].
- **Batch-generation VRAM leak**: "clear linear increase" over 300 runs despite `empty_cache()` (issues/63). Two evidenced retention mechanisms the fork fixes: (1) the sampler returns `pred_x_t`/`pred_x_0` lists holding every step's tensor (`trellis2/pipelines/samplers/flow_euler.py:119-124`; fork drops them); (2) neighbor-map `_spatial_cache` dicts accumulate on SparseTensors (fork clears them at 6+ points). [pure-python].
- The MPS port peaks ~18 GB unified at the 512 pipeline (trellis-mac README.md:142); M5/128 GB has ample headroom even for 1024+.

## Speed

- Upstream H100: 3 s (512³) / 17 s (1024³) / 60 s (1536³) generation (README:23-29) — but consumer GPUs report minutes (RTX 3090, issues/11; 4090 "stuck", issues/93) and postprocess dominates wall-clock (issues/44).
- trellis-mac M4 Pro (512): total 5m13s cold; sparse-structure sampling 80 s = biggest chunk, "sparse attention is not fused: the SDPA-padded wrapper… is the single largest remaining bottleneck"; pipeline load 103 s; pure-Python dual-grid→mesh ~8 s (README:124-151). Padded-SDPA implementation: `patches/mps_compat.py:45-97` (zero-pads variable-length seqs to max len). Fused varlen attention on Metal = [kernel]; FlexAttention/block-diagonal SDPA = [pure-python].
- The pure-PyTorch sparse conv fallback is "~10x slower than CUDA flex_gemm" (trellis-mac issues/1); pedronaugusto's mtlgemm fixes took the decoder path 38 s→27 s (README:140).
- Thermal throttling on Apple Silicon: identical run 3.5 min→36 min after sustained load (README:159) — the build must expose per-stage timing to disambiguate.
- Gradio/UI starvation: GPU-bound sampling loops starve the event loop causing timeouts; the fork's fix is `sleep(0)` GIL yields per step + the pipeline moved to a separate process (stableprojectorz `pipeline_worker.py:2`). [pure-python].

## Input sensitivity

- **Background removal is load-bearing**: with the background left in, "severe artifacts and missing geometry (holes)"; clean with rembg; Hunyuan3D 2.1 handles the same image (issues/65). [model]; mitigation = always-on robust matting.
- Preprocessing depends on two gated/nonfree models: DINOv3 (Meta gated license) and RMBG-2.0 (CC BY-NC, commercial license required) (trellis-mac README.md:167-168). Runtime load failures are a top install complaint (issues #38, #153, #161; HF discussion #9 "wrong link to BirefNet model in the config"); both forks vendor local-model redirects. Upstream's DINOv2 class still does runtime `torch.hub.load` (image_feature_extractor.py:16).
- Certain viewpoints fail (#35); input/mesh correspondence questions (#86); multi-image conditioning (community add-on) is "surprisingly worse than with single-image inputs" (issues/103) — TRELLIS.2 is single-image by design (#10). Issue #56 "hair problem" is image-only, gist UNVERIFIED.

## Determinism

- Seeding is a single `torch.manual_seed(seed)` (default 42) covering all three flow stages (trellis2_image_to_3d.py:493,538); no `use_deterministic_algorithms`, no per-stage generators. Same-machine repeatability plausible but UNVERIFIED by any primary source.
- Cross-platform/backend determinism is definitively broken at the logit thresholds (#169: CUDA vs ROCm flips; fork: fp16 vs fp32 flips). Expect same-seed geometry to differ across CUDA/MPS/ROCm and across attention backends. [pure-python] to stabilize decode; bitwise parity unattainable [model].

## Platform & dependency failures

- Windows unsupported upstream (README:59, issues #4, #68); Triton absent on Windows → the fork forces `Algorithm.EXPLICIT_GEMM` ("bypasses the 'kernels.triton' error", pipeline_worker.py:36-41) and ships prebuilt whls + `/bigobj` MSVC flags.
- flash-attn requires sm≥80; V100 hits "No autotune configuration found" in flex_gemm Triton (#12); the fork auto-selects xformers when sm<80; upstream's sparse-attn whitelist has no native SDPA option (patched in by trellis-mac, mps_compat.py:29-43). Blackwell/CUDA-13 build breakage (#19; working 5090/WSL guide #143); aarch64 install fails (#131); DGX Spark (#32); cuDNN init (#154); flex_gemm autotuner/version mismatch (#98).
- MPS gaps: `aten::segment_reduce` unimplemented → needs `PYTORCH_ENABLE_MPS_FALLBACK=1` (trellis-mac issues/5); the macOS GPU watchdog kills long Metal dispatches mid-decode → silent empty mesh, surfacing later as "BVH needs at least 8 triangles, got 0" (trellis-mac issues/8); Metal cumesh segfaults on ~400K-vertex meshes (mps_compat.py:236-265); Metal BVH "unstable on 800K+ face inputs" → pre-simplify to ~200K faces before bake (README.md:120,152).
- Multi-GPU training crashes (#88, #90, #95, #164) and slow start (#87) — training-side only. One report of the ss-decoder checkpoint emitting all-negative logits → zero voxels (issues/160) — single report, UNVERIFIED as a general defect.
- bf16 checkpoints fail on pre-Ampere GPUs; the fork converts all weights/cond bf16→fp16 "for widest GPU compatibility" (`_convert_bf16_to_fp16_if_needed`) — note this conversion is exactly what triggers the fp16 threshold artifact unless decode is done in fp32.
- Licensing exposure for a product: nvdiffrast/nvdiffrec are non-MIT (upstream README:316-320; the commercial-use question is unanswered in #22); RMBG-2.0 non-commercial; DINOv3 gated.

## Implications for the build (ranked fix-list)

1. **Decode in fp32 at every hard threshold** (subdiv, intersection, sigmoid offsets) + a configurable decision margin — kills the vertical-line class and most cross-platform hole scatter; fixes proven in stableprojectorz. [pure-python]
2. **Replace cumesh-dependent hole filling with a robust CPU hole-filler** (small-perimeter fill post-decode) so geometry correctness never rides on a crash-prone CUDA/Metal lib. [pure-python]
3. **Deterministic-by-contract pipeline**: per-stage generators, fp32 decode, pinned backend, documented same-device reproducibility; surface a content-hash of the mesh for agent verification. [pure-python]
4. **Adopt the fork's VRAM discipline wholesale** (chunked norm/MLP/im2col, CPU accumulation, `_spatial_cache` clearing, sampler pred-list removal, lazy subs) — also the batch-leak fix; on M5 unified memory it mostly buys stability, not capacity. [pure-python]
5. **Cap DC remesh resolution (≤512) and pre-simplify before UV/bake**; remove the 41M-face detour — turns 50-min extractions into seconds-to-minutes. Add degenerate-face + non-manifold cleanup after remesh. [pure-python]
6. **Fix GLB export**: alphaMode from actual alpha stats (BLEND/MASK when alpha < 1), float baseColorFactor; emit an agent-readable manifest (counts, holes, watertightness, material channels). [pure-python]
7. **Clamp texture_size to what attr-volume resolution supports** (≤2K at ≤1024³); document why. [pure-python]
8. **Bundle/replace gated preprocessors**: swap RMBG-2.0 (CC BY-NC) for a commercially clean matting model; vendor DINOv3 loading with an offline path; always background-remove (defect #65 makes it non-optional). [pure-python + licensing]
9. **MPS path**: block-diagonal/FlexAttention SDPA to replace padded SDPA (biggest speed win, the 80 s stage); chunk Metal dispatches below the watchdog budget; hard post-decode sanity checks (non-empty mesh, min triangle count) instead of silent empties. [pure-python → later kernel]
10. **Interior-geometry culling pass** (connected-component visibility from exterior) to mitigate #25; despeckle the metallic channel to mitigate #162. [pure-python mitigation of model defects]
11. **Run generation in a worker process with heartbeat** (fork pattern) so the MCP server never blocks or times out during GPU-bound loops; export per-stage timings (also disambiguates Apple thermal throttling). [pure-python]
12. Accept as model-inherent, document for agents: text/fine-detail loss (#57), single-image-only conditioning (#103), silent token-cap resolution downgrade (make it loud), staircase VAE floor (#127).
