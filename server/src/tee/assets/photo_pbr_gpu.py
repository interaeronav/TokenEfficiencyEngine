"""Creation lane 2, GPU refinement: Marigold in place of the classical maps.

Two diffusion estimators replace the Sobel/energy heuristics behind the
same return shape as `photo_pbr.derive_maps`:

- `prs-eth/marigold-iid-appearance-v1-1` (Apache-2.0): intrinsic image
  decomposition - a delighted **albedo** plus a material stack whose
  **roughness** channel replaces the high-frequency-energy estimate.
- `prs-eth/marigold-normals-v1-1` (Apache-2.0): surface **normals** that
  replace the Sobel gradient estimate.

The albedo rides along as an extra `albedo` key - it is the "Marigold
delight" step of the lane, a base color with the photo's baked lighting
removed. Metallic stays the research-24 clamp (0.0 on masonry/paint/wood);
the appearance model does emit a metallicity channel, but overriding a
deliberate material-policy clamp with a per-pixel guess would change
behavior silently, so that stays a future, explicit option.

Everything degrades loudly: no torch/diffusers/weights -> TeeError naming
the fix, and the caller falls back to the classical path with its honesty
label intact.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

APPEARANCE_ID = "prs-eth/marigold-iid-appearance-v1-1"
NORMALS_ID = "prs-eth/marigold-normals-v1-1"
MODEL_LICENSE = "Apache-2.0"
# Marigold v1-1 checkpoints support 1-4 step inference; 4 is the quality end.
DEFAULT_STEPS = 4
DEFAULT_ENSEMBLE = 1

_PIPES: dict[str, Any] = {}


def _device_dtype():
    import torch

    from tee.assets.generation import torch_device

    device = torch_device()
    # same backend/dtype table as gen_local: fp16 NaNs on MPS, bf16 fine.
    dtype = {"mps": torch.bfloat16, "cuda": torch.float16}.get(device, torch.float32)
    return device, dtype


def _pipe(kind: str):
    """Load and memoize one Marigold pipeline ('appearance' or 'normals')."""
    if kind in _PIPES:
        return _PIPES[kind]
    try:
        from diffusers import MarigoldIntrinsicsPipeline, MarigoldNormalsPipeline
    except ImportError as exc:
        raise TeeError(
            "marigold_missing",
            "Marigold refinement needs diffusers + torch (the [assets-gen] stack).",
            fix="uv pip install diffusers torch transformers",
        ) from exc
    device, dtype = _device_dtype()
    cls = MarigoldIntrinsicsPipeline if kind == "appearance" else MarigoldNormalsPipeline
    model_id = APPEARANCE_ID if kind == "appearance" else NORMALS_ID
    try:
        pipe = cls.from_pretrained(model_id, torch_dtype=dtype)
    except Exception as exc:
        raise TeeError(
            "marigold_weights",
            f"cannot load {model_id}: {str(exc)[:120]}",
            fix=f"fetch the weights once: huggingface_hub.snapshot_download('{model_id}')",
        ) from exc
    pipe = pipe.to(device)
    pipe.set_progress_bar_config(disable=True)
    _PIPES[kind] = pipe
    return pipe


def derive_maps_marigold(
    base_color: Path,
    out_dir: Path,
    *,
    surface: str = "generic",
    steps: int = DEFAULT_STEPS,
    ensemble: int = DEFAULT_ENSEMBLE,
) -> dict[str, Any]:
    """Marigold-refined maps, same return shape as photo_pbr.derive_maps."""
    from tee.kernel.imaging import open_image

    image = open_image(base_color).convert("RGB")
    out_dir.mkdir(parents=True, exist_ok=True)

    normals = _pipe("normals")
    n_out = normals(image, num_inference_steps=steps, ensemble_size=ensemble)
    normal_img = normals.image_processor.visualize_normals(n_out.prediction)[0]
    normal_path = out_dir / (base_color.stem + "_normal_mgd.png")
    normal_img.save(normal_path)

    appearance = _pipe("appearance")
    a_out = appearance(image, num_inference_steps=steps, ensemble_size=ensemble)
    vis = appearance.image_processor.visualize_intrinsics(
        a_out.prediction, appearance.target_properties
    )[0]
    albedo_path = out_dir / (base_color.stem + "_albedo_mgd.png")
    vis["albedo"].save(albedo_path)
    rough_path = out_dir / (base_color.stem + "_rough_mgd.png")
    vis["roughness"].convert("L").save(rough_path)

    return {
        "base_color": str(base_color),
        "albedo": str(albedo_path),
        "normal": str(normal_path),
        "roughness": str(rough_path),
        "metallic": 0.0,  # masonry/paint/wood: clamp (research 24)
        "surface": surface,
        "honesty": f"measured (Marigold-IID appearance + normals, {steps}-step, "
        f"ensemble {ensemble}); metallic still the research-24 clamp",
        "license": MODEL_LICENSE,
    }
