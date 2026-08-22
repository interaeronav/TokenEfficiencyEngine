# Voxkiln setup (local 3D generation)

Voxkiln is TEE's own local image-to-3D engine (Phase 13; decisions
A26–A28) — a defect-fixed, license-clean fork of Microsoft TRELLIS.2
that runs on Apple Silicon and CUDA. When it is installed and the
machine has a capable GPU, `as_generate` uses it by default: no API
keys, no per-model fees, images never leave the machine. Hosted
Tripo/Meshy stay available as keyed fallbacks (text-to-3D, rigging).

## Install (on the Mac)

```bash
cd TokenEfficiencyEngine/voxkiln
uv venv && uv pip install -e '.[model,manifold,mcp]'
uv run voxkiln fetch-weights     # ~16 GB into the Hugging Face cache, once
uv run voxkiln doctor            # backend, weights, deps - with fixes
```

Make it visible to the TEE server by installing it into the server's
environment: `uv pip install -e ../voxkiln` from `server/` (add
`[model]` there too). `tee doctor` and `as_generate` pick it up
automatically.

## Use through TEE

```
as_generate(kind="image_to_model", prompt="<path to concept image>",
            options={"target_faces": 100000,
                     "budget": {"max_tris": 100000, "require_watertight": true},
                     "seed": 7})
```

The answer is a compact report: mesh stats, the repair log, an
accept/reject verdict with the exact fix, and a provenance manifest
(`ai_generated: true`, model revision, input hash, seed). Identical
requests hit the cache instead of the GPU.

Voxkiln is image-to-3D only. For text, render a concept image first
(lane 1) — that also gives a cheap review checkpoint before the
expensive 3D step.

## Standalone

Voxkiln also works without TEE: `voxkiln gen photo.png --json`,
`voxkiln serve` (a 4-tool MCP server). See `../voxkiln/README.md`.

## Status

Cloud-verified: repair/export/report/metrics, license lint, the ported
sparse ops (checked against dense references), the driver contract and
fakes. Still owed on the Mac (script 13.6.3): the first live GPU
generation, the stock-vs-ours eval battery, and FlexAttention tuning.
