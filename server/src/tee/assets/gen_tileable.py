"""Born-tileable texture driver (lane 1, SDXL + circular padding).

Model: **SDXL base 1.0** (`stabilityai/stable-diffusion-xl-base-1.0`,
CreativeML Open RAIL++-M). Z-Image stays the general text->image lane;
this driver exists for one thing Z-Image cannot do: textures that wrap
seamlessly, produced by switching every spatial convolution in the UNet
and VAE to circular padding so the generation is periodic by construction
- no post-hoc seam blending, no mirrored halves.

Tileability is MEASURED, not asserted: `seam_ratio` compares the pixel
difference across the wrap seam with the image's own interior gradient.
A ratio near 1.0 means the wrap edge is statistically indistinguishable
from any interior column; the result carries the number either way and a
`tileable` verdict at a lenient threshold, so a bad run is visible in the
report instead of in the level after someone applied the material.

Same `GenDriver` protocol as the other lanes: synchronous under the hood,
`submit` runs it and `poll` returns the finished result.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
MODEL_LICENSE = "CreativeML Open RAIL++-M"
# SDXL base is not distilled: it needs real step counts. 24 is the low end
# of good; turbo-style 8 leaves visible noise.
DEFAULT_STEPS = 24
DEFAULT_SIZE = 1024
# seam_ratio at or under this counts as tileable; ratios climb well past 3
# when padding is left zeros, so the band between is deliberately generous.
SEAM_RATIO_TILEABLE = 2.0


def make_convs_circular(module: Any) -> int:
    """Switch every padded Conv2d under `module` to circular padding.

    Returns the number of convs patched. 1x1 convs (padding 0) are left
    alone - there is nothing to wrap.
    """
    import torch

    patched = 0
    for m in module.modules():
        if isinstance(m, torch.nn.Conv2d) and any(int(p) > 0 for p in m.padding):
            m.padding_mode = "circular"
            patched += 1
    return patched


def seam_ratio(image: Any) -> float:
    """Wrap-seam difference relative to the interior gradient, both axes.

    1.0 = the wrap edge looks like any other pixel column/row; large values
    mean a visible seam when tiled.
    """
    import numpy as np

    a = np.asarray(image.convert("RGB"), dtype=np.float32)
    seam = (np.abs(a[:, 0] - a[:, -1]).mean() + np.abs(a[0, :] - a[-1, :]).mean()) / 2.0
    interior = (np.abs(np.diff(a, axis=1)).mean() + np.abs(np.diff(a, axis=0)).mean()) / 2.0
    if interior == 0.0:
        return float("inf") if seam > 0 else 1.0
    return float(seam / interior)


class TileableSdxlDriver:
    id = "sdxl-tileable"
    paid = False  # electricity is not a metered API call

    def __init__(self, out_dir: Path | str, model_id: str = MODEL_ID):
        self.out_dir = Path(out_dir).expanduser()
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.model_id = model_id
        self._pipe = None
        self._device = "cpu"
        self._results: dict[str, dict[str, Any]] = {}

    # -- GenDriver ---------------------------------------------------------

    def estimate(self, kind: str, options: dict[str, Any]) -> dict[str, Any]:
        steps = int(options.get("steps", DEFAULT_STEPS))
        return {
            "cost_usd": 0.0,
            "note": f"local {self.model_id} on {self._probe_device()}, "
            f"{steps} steps, circular padding - no API charge",
            "license": MODEL_LICENSE,
        }

    def submit(self, kind: str, prompt: str, options: dict[str, Any]) -> str:
        if kind != "image":
            raise ValueError(
                f"the tileable lane generates images, not {kind!r}; "
                "3D generation needs the voxkiln or a hosted driver"
            )
        task_id = hashlib.sha256(f"{prompt}{time.time()}".encode()).hexdigest()[:12]
        started = time.monotonic()
        path, ratio = self._run(prompt, options)
        self._results[task_id] = {
            "state": "done",
            "result": {
                "files": [str(path)],
                "model": self.model_id,
                "license": MODEL_LICENSE,
                "device": self._device,
                "wall_s": round(time.monotonic() - started, 1),
                "seam_ratio": round(ratio, 3),
                "tileable": ratio <= SEAM_RATIO_TILEABLE,
            },
        }
        return task_id

    def poll(self, task_id: str) -> dict[str, Any]:
        return self._results.get(task_id, {"state": "failed", "error": "unknown task"})

    # -- internals ---------------------------------------------------------

    @staticmethod
    def _probe_device() -> str:
        from tee.assets.generation import torch_device

        return torch_device()

    def _ensure_pipe(self):
        if self._pipe is not None:
            return self._pipe
        import torch
        from diffusers import StableDiffusionXLPipeline

        from tee.assets.generation import torch_device

        self._device = torch_device()
        # same backend/dtype table as gen_local: fp16 NaNs on MPS, bf16 fine.
        dtype = {
            "mps": torch.bfloat16,
            "cuda": torch.float16,
        }.get(self._device, torch.float32)
        pipe = StableDiffusionXLPipeline.from_pretrained(
            self.model_id, torch_dtype=dtype, variant="fp16", use_safetensors=True
        )
        patched = make_convs_circular(pipe.unet) + make_convs_circular(pipe.vae)
        if patched == 0:
            raise RuntimeError(
                "no convolutions accepted circular padding - the pipeline "
                "layout changed and the outputs would NOT tile; refusing to "
                "pretend otherwise"
            )
        pipe = pipe.to(self._device)
        pipe.set_progress_bar_config(disable=True)
        self._pipe = pipe
        return pipe

    def _run(self, prompt: str, options: dict[str, Any]) -> tuple[Path, float]:
        from tee.assets.gen_local import _reject_degenerate

        pipe = self._ensure_pipe()
        steps = int(options.get("steps", DEFAULT_STEPS))
        size = int(options.get("size", DEFAULT_SIZE))
        kwargs: dict[str, Any] = {
            "prompt": prompt,
            "num_inference_steps": steps,
            "height": size,
            "width": size,
        }
        if options.get("negative_prompt") is not None:
            kwargs["negative_prompt"] = str(options["negative_prompt"])
        if options.get("seed") is not None:
            import torch

            kwargs["generator"] = torch.Generator(device="cpu").manual_seed(int(options["seed"]))
        if options.get("guidance_scale") is not None:
            kwargs["guidance_scale"] = float(options["guidance_scale"])
        image = pipe(**kwargs).images[0]
        _reject_degenerate(image, self._device)
        ratio = seam_ratio(image)
        stem = hashlib.sha256(f"tile{prompt}{steps}{size}".encode()).hexdigest()[:16]
        path = self.out_dir / f"{stem}.png"
        image.save(path)
        return path, ratio
