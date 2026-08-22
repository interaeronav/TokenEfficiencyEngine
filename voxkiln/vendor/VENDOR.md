# Vendored code provenance

Everything under this directory derives from **microsoft/TRELLIS.2**
(https://github.com/microsoft/TRELLIS.2, MIT — see
`LICENSE.microsoft-trellis2`), vendored as a hard fork at:

    UPSTREAM_COMMIT = 75fbf0183001ed9876c8dbb35de6b68552ee08bd

Fork strategy per decision A26 (`docs/DECISIONS.md` in the TEE repo):
upstream is near-dormant (11 commits ever, no external PRs merged), so a
vendored fork with recorded provenance beats a patch overlay. Upstream sync
is a periodic chore: `git diff` this tree against the recorded commit.

`trellis2/modules/sparse/conv/conv_none.py` additionally derives from
**shivampkumar/trellis-mac** (https://github.com/shivampkumar/trellis-mac,
MIT, commit d58628f4f5b9c3de8274cb110074154f4b31cef2), with the neighbor
build vectorized.

## Removed relative to upstream (and why)

- `trellis2/trainers/`, `trellis2/datasets/`, most of `trellis2/utils/` —
  training-only (lpips, tensorboard, dist).
- `trellis2/renderers/`, `trellis2/utils/render_utils.py` — import
  nvdiffrast / nvdiffrec_render (**NVIDIA non-commercial licenses**);
  preview rendering is out of product scope (text over pixels).
- `trellis2/pipelines/trellis2_texturing.py` — retexture-only pipeline with
  module-level cumesh/nvdiffrast imports; restorable later with the same
  surgery.
- `trellis2/modules/sparse/attention/windowed_attn.py` — no shipped config
  uses it (`attn_mode` is always `'full'`).
- `trellis2/utils/mesh_utils.py`, `o_voxel/io/ply.py` — import plyfile
  (**GPLv3+**).
- `o_voxel/postprocess.py` — the tainted export pipeline (nvdiffrast bake,
  cumesh/cubvh BVH). Its replacement is `voxkiln.export`, which keeps its
  two structural ideas (repair-then-freeze full-res reference; staged
  simplify) on a license-clean CPU stack.
- `o-voxel/third_party/eigen` — empty submodule in a shallow clone; the
  CUDA extension build (`o-voxel/setup.py`) needs it fetched
  (MPL-2.0, header-only).

## Changed relative to upstream (all marked with "voxkiln" comments)

- easydict (LGPL-3.0) replaced by a local attribute-dict in
  `pipelines/samplers/flow_euler.py` and `o_voxel/rasterize.py`.
- `pipelines/rembg/BiRefNet.py`: device taken from the model (was
  hard-coded CUDA); NC-licensed weight ids are refused (see file).
- `modules/image_feature_extractor.py`: device from the model, not
  `.cuda()`.
- `modules/sparse/config.py` + `attention/full_attn.py`: new `sdpa`
  attention backend — exact per-sequence SDPA (portable: MPS/CPU/CUDA),
  replacing nothing on CUDA (flash_attn/xformers stay default there).
- `modules/sparse/conv/conv_none.py`: new pure-PyTorch submanifold conv
  backend (`SPARSE_CONV_BACKEND=none`), vectorized neighbor build.
- `representations/mesh/base.py`: cumesh/flex_gemm now optional —
  `fill_holes` defers to voxkiln repair (recorded via
  `fill_holes_deferred`), `simplify` falls back to fast-simplification,
  `query_attrs` falls back to an exact portable sparse-trilinear sampler.
- `models/sc_vaes/sparse_unet_vae.py` + `fdg_vae.py`: **fp32 at every hard
  decode threshold** (defect fix, research 44 / upstream issue #169).
- `pipelines/samplers/flow_euler.py`: per-step prediction lists no longer
  retained (the measured batch-generation memory leak, upstream #63).
- `pipelines/trellis2_image_to_3d.py`: CPU noise generator for
  cross-device seed determinism; cascade loop-guard `<= 1024`; resolution
  downgrade recorded in `last_run_report`; device-aware cache clearing.
- `o_voxel/convert/flexible_dual_grid.py`: mesh extraction runs without
  the CUDA hashmap via a sorted-key searchsorted lookup (exact, any
  device); `_C` import optional.
- `o_voxel/__init__.py`, `o_voxel/io/__init__.py`: lazy imports so the
  package imports cleanly with no compiled extension present.
