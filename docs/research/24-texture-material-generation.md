# 24 — Texture/material generation + photo→PBR (2026-08-22)

Licenses verified on HF cards/LICENSE files; commercial floor = default
lanes must be unconditionally commercial-clean.

## Image-model license reality (mid-2026)

Default-clean local models: **Z-Image family (Alibaba, Apache-2.0)** —
Turbo (8-step, 2-3 s on 16 GB), Base (LoRA/ControlNet-trainable), Edit;
**FLUX.2-klein-4B (Apache-2.0, ~13 GB)** (the klein 9B variants are NOT);
**SDXL (RAIL++, commercial-OK)** — still the tileable-texture workhorse;
Qwen-Image (Apache, heavy: fp8 16 GB). Gated only: FLUX.1/.2-dev
(**non-commercial to RUN**, outputs fine) and SD3.5 ($1M-revenue
conditional). Excluded: SANA (NC). Watch: Qwen-Image-2.0 weights,
HiDream-O1 (MIT, pixel-native). Invocation: diffusers (Apache) in-process;
ComfyUI (GPL-3) driven only as a separate process over HTTP, never
vendored.

## Tileability & PBR maps

- Circular-padding conv patch = born-tileable, **SDXL/UNet only — does not
  transfer to DiT models** (Z-Image/FLUX/Qwen); DiT route: latent/feature
  rolling or offset-half + inpaint; classical Poisson/pyramid blending for
  unstructured surfaces. Structured facades: don't tile — UV-project the
  rectified photo.
- **Marigold-IID** (in diffusers core; code Apache, weights RAIL++, <8 GB)
  is the license-clean core: appearance variant = albedo/roughness/
  metallic; lighting variant = delighting. StableDelight for speculars
  (apache tag; lineage flag). DeepBump (GPL) as subprocess-only CLI
  fallback; classical Sobel-normal/roughness-from-frequency always
  available. Real-ESRGAN (BSD-3 code+weights) for upscale — regenerate
  normals AFTER upscaling. Excluded: Intrinsic (academic-only),
  Materialize (GPL GUI, unmaintained).

## Photo→PBR (the Okongo hero lane)

Homography rectify (OpenCV, most-frontal photo per material) → Marigold
delight → seamless or UV-project → Marigold appearance maps + normal →
Real-ESRGAN. Quality: material IDENTITY correct (the actual plaster tint,
the actual roof profile); albedo/roughness are estimates under relighting;
clamp metallic=0 on masonry/paint. Above generic textures, below scans.

## Scene-conditioned generation

Headless `blender -b` depth/normal EXR passes → ControlNet-depth img2img
(xinsir union Apache for SDXL; alibaba-pai union for Z-Image; InstantX/
DiffSynth Apache for Qwen) → back-projection: **UV Project modifier**
(headless-safe; `uv.project_from_view` is NOT) → Cycles bake to flatten
multi-photo/multi-view projections into one UV texture.

## Procedural lane (zero-GPU, zero-license-risk) — stronger than expected

bpy node-graph materials parameterized from **physicallybased.info (CC0
JSON of measured PBR values)** — stops hallucinated material constants;
**Infinigen (BSD-3)** ships ~50 procedural material generators as
Python-building-node-graphs incl. the Indoors archviz set (plaster, tile,
brick, wood, fabric, metal, marble) — the best machine-readable procedural
library to mine or depend on. Excellent for plaster/concrete/asphalt/
paint; good brick/roof via Brick Texture + geometry nodes; weakest wood
close-ups. OSL is niche (CPU/OptiX-only). ambientCG CC0 API = a free
fourth micro-lane (real scans, no GPU).

## Lane design (settled in A14)

Lane 0 procedural + CC0 fetch (default, ms, no GPU); lane 1 local
diffusion (Z-Image + SDXL-tileable + Marigold maps; SDXL/GGUF on 8 GB);
lane 2 photo-derived; gated lane FLUX-dev/SD3.5 behind explicit opt-in.
