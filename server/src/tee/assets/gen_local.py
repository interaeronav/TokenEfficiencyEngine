"""Local diffusion driver (lane 1): text -> image on the machine's own GPU.

Model: **Z-Image-Turbo** (`Tongyi-MAI/Z-Image-Turbo`, Apache-2.0, ungated) -
picked because the licence is clean for outputs as well as weights, which is
the whole reason TEE runs a licence gate over assets at all. Lane 3 (TRELLIS
image->3D) stays CUDA-only: nvdiffrast is CUDA-bound.

The driver satisfies the same `GenDriver` protocol as the hosted shells, so
the cost gate, wait-polling and provenance stamping in `GenerationLane` apply
unchanged. Generation is synchronous under the hood, which the protocol
tolerates: `submit` runs it and `poll` returns the finished result. That is
honest for a local model - there is no server-side queue to poll, and
pretending otherwise would only add latency.

The pipeline is loaded ONCE per process and kept: on Apple Silicon the load
dominates a short generation, so reloading per call would make the lane look
far more expensive than it is.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

MODEL_ID = "Tongyi-MAI/Z-Image-Turbo"
MODEL_LICENSE = "Apache-2.0"
# Turbo variants are distilled for very few steps; the default is deliberately
# low because the point of a local lane is a fast look, not a hero render.
DEFAULT_STEPS = 8
DEFAULT_SIZE = 1024


def _reject_degenerate(image: Any, device: str) -> None:
    """Refuse a uniform image instead of saving it and reporting success.

    A numerically unstable pipeline does not raise - it returns NaNs, which
    the image processor casts to a flat black frame. Without this check the
    driver happily reports state "done" with a black PNG, which is the worst
    possible failure mode: silent, plausible, and only visible to a human who
    opens the file.
    """
    low, high = image.convert("L").getextrema()
    if high > low:
        return
    raise RuntimeError(
        f"the pipeline produced a uniform image (luminance {low}) on "
        f"{device} - this is what NaNs look like after the uint8 cast, "
        "usually a dtype the backend cannot handle"
    )


class LocalDiffusionDriver:
    id = "local-diffusion"
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
            f"{steps} steps - no API charge",
            "license": MODEL_LICENSE,
        }

    def submit(self, kind: str, prompt: str, options: dict[str, Any]) -> str:
        if kind != "image":
            raise ValueError(
                f"the local diffusion lane generates images, not {kind!r}; "
                "3D generation needs a hosted driver or a CUDA machine"
            )
        task_id = hashlib.sha256(f"{prompt}{time.time()}".encode()).hexdigest()[:12]
        started = time.monotonic()
        path = self._run(prompt, options)
        self._results[task_id] = {
            "state": "done",
            "result": {
                "files": [str(path)],
                "model": self.model_id,
                "license": MODEL_LICENSE,
                "device": self._device,
                "wall_s": round(time.monotonic() - started, 1),
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
        from diffusers import DiffusionPipeline

        from tee.assets.generation import torch_device

        self._device = torch_device()
        # dtype is NOT interchangeable across backends. Measured on this model
        # (Z-Image-Turbo, 8 steps, 512px, Apple M5):
        #   float16 on MPS -> NaNs; a fully BLACK image, reported as success
        #   bfloat16 on MPS -> correct, 19 s
        #   float32  on MPS -> correct, 32 s
        # so MPS gets bfloat16, CUDA keeps fp16 (where it is well-behaved),
        # and CPU stays fp32.
        dtype = {
            "mps": torch.bfloat16,
            "cuda": torch.float16,
        }.get(self._device, torch.float32)
        pipe = DiffusionPipeline.from_pretrained(self.model_id, torch_dtype=dtype)
        pipe = pipe.to(self._device)
        pipe.set_progress_bar_config(disable=True)
        self._pipe = pipe
        return pipe

    def _run(self, prompt: str, options: dict[str, Any]) -> Path:
        pipe = self._ensure_pipe()
        steps = int(options.get("steps", DEFAULT_STEPS))
        size = int(options.get("size", DEFAULT_SIZE))
        kwargs: dict[str, Any] = {
            "prompt": prompt,
            "num_inference_steps": steps,
            "height": size,
            "width": size,
        }
        if options.get("seed") is not None:
            import torch

            kwargs["generator"] = torch.Generator(device="cpu").manual_seed(int(options["seed"]))
        if options.get("guidance_scale") is not None:
            kwargs["guidance_scale"] = float(options["guidance_scale"])
        image = pipe(**kwargs).images[0]
        _reject_degenerate(image, self._device)
        stem = hashlib.sha256(f"{prompt}{steps}{size}".encode()).hexdigest()[:16]
        path = self.out_dir / f"{stem}.png"
        image.save(path)
        return path
