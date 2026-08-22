# Voxkiln

AI-first local image-to-3D generation, built on
[Microsoft TRELLIS.2](https://github.com/microsoft/TRELLIS.2) (MIT).
Give it one image; get back a repaired, textured GLB **and a compact
machine report** — mesh statistics, a log of every defect fixed, an
accept/reject verdict against your budget with the exact fix, and a full
provenance manifest. Built for AI agents first: one call, one answer,
no polling loops, no screenshots.

Part of the TokenEfficiencyEngine project (see `../docs/DECISIONS.md`,
decisions A26–A28, and `../docs/research/43`–`48` for the evidence
behind every design choice). Structured as a self-contained package so
it can move to its own repository without surgery.

## What it fixes over stock TRELLIS.2

- **fp32 decode thresholds** — kills the fp16 "hair spike" and
  platform-dependent hole-scatter defect classes (upstream issue #169).
- **Repair before bake** — holes are filled on the CPU (no crash-prone
  CUDA mesh library), *before* texturing, so fill geometry gets textures
  for free; the full-res repaired surface is kept as the bake's
  projection reference (the fidelity the Mac port lost).
- **License-clean runtime** — NVIDIA-non-commercial (nvdiffrast,
  nvdiffrec, cubvh), GPL (plyfile) and LGPL (easydict) code is out of
  the import path; the CC-BY-NC RMBG-2.0 weights are replaced with MIT
  BiRefNet. See `vendor/VENDOR.md` for every change.
- **Runs on Apple Silicon** — portable SDPA sparse attention (exact, not
  the padded approximation), pure-PyTorch sparse conv, device-neutral
  mesh extraction. CUDA stays first-class.
- **Deterministic by contract** — CPU noise generator per seed, mesh
  content hash in every report, memory-leak fix for batch generation.
- **Honest degradation** — no capable GPU → a one-line structured
  refusal naming the fix, never a hang or a stack trace.

## Install

```bash
uv tool install voxkiln            # CLI + repair/report stack (no torch)
pip install 'voxkiln[model]'       # + the neural pipeline (torch etc.)
voxkiln fetch-weights              # ~16 GB into the HF cache, once
voxkiln doctor                     # what can run here, with fixes
```

## Use

```bash
voxkiln gen photo.png --seed 7 --max-tris 100000 --watertight --out assets/
```

Exit code 0 = generated *and* within budget. The JSON report on stdout
carries stats, repairs, verdict, provenance, timings.

As an MCP server (4 tools: `gen3d_generate`, `gen3d_wait`,
`gen3d_query`, `gen3d_status`):

```bash
voxkiln serve
```

Python:

```python
from voxkiln.jobs import JobStore
report = JobStore().generate("photo.png", budget={"max_tris": 100_000})
```

## Attribution

Built on Microsoft TRELLIS.2 (MIT) — vendored at a pinned commit under
`vendor/`, all changes documented in `vendor/VENDOR.md`. The portable
sparse-conv backend derives from shivampkumar/trellis-mac (MIT). Image
conditioning uses DINOv3 — "Built with DINOv3"; weights are fetched
gated from Meta's Hugging Face repo under the DINOv3 license.
