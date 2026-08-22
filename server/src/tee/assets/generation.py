"""Creation lanes 1-3 (A14): ONE async adapter over every generator.

Design rules from the measured prior art:
- Meshy's wait-polling is the good pattern (server-side backoff poll, one
  call returns the result); Tripo's chatty per-poll round-trips are the
  bad one. TEE polls server-side inside a job - the model sees job_id and
  the final result, nothing between.
- Paid calls require an explicit cost confirmation: the first call
  returns the estimate and a confirm token requirement; only
  `confirm_cost=true` proceeds.
- Every generated asset carries an `ai-generated` provenance fact
  (generator, input hash, USCO note: pure AI output is not copyrightable
  in the US; cleanup/selection adds protectable authorship).
- Local GPU lanes (TRELLIS.2, diffusion) are import-probed and degrade to
  one actionable message on machines without a GPU stack.

Hosted drivers are thin HTTP shells (keyed via env); the Fake driver
carries the contract in tests.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Protocol

from tee.kernel.errors import TeeError

USCO_NOTE = (
    "pure AI output is not copyrightable in the US (USCO Jan 2025); "
    "human cleanup/selection adds protectable authorship"
)

_POLL_START_S = 5.0
_POLL_MAX_S = 30.0
_POLL_CAP_S = 300.0


class GenDriver(Protocol):
    id: str
    paid: bool

    def estimate(self, kind: str, options: dict[str, Any]) -> dict[str, Any]: ...

    def submit(self, kind: str, prompt: str, options: dict[str, Any]) -> str: ...

    def poll(self, task_id: str) -> dict[str, Any]:
        """{state: queued|running|done|failed, result?: {...}, error?: str}"""
        ...


class GenerationLane:
    """One adapter, N drivers; wait-polling and cost gates live here."""

    def __init__(self, drivers: dict[str, GenDriver], *, sleep=time.sleep):
        self.drivers = drivers
        self._sleep = sleep

    def generate(
        self,
        driver_id: str,
        kind: str,
        prompt: str,
        *,
        options: dict[str, Any] | None = None,
        confirm_cost: bool = False,
    ) -> dict[str, Any]:
        driver = self.drivers.get(driver_id)
        if driver is None:
            known = ", ".join(sorted(self.drivers)) or "(none configured)"
            raise TeeError(
                "unknown_generator",
                f"No generation driver '{driver_id}'.",
                fix=f"Configured: {known}. Hosted drivers need API keys "
                "(TEE_TRIPO_KEY / TEE_MESHY_KEY); local lanes need a GPU stack.",
            )
        options = options or {}
        estimate = driver.estimate(kind, options)
        if driver.paid and not confirm_cost:
            raise TeeError(
                "cost_confirmation_required",
                f"{driver_id} {kind} is a PAID call: "
                f"~{estimate.get('cost_usd', '?')} USD ({estimate.get('note', '')}).",
                fix="Re-call with confirm_cost=true to accept the charge.",
            )
        task_id = driver.submit(kind, prompt, options)
        started = time.monotonic()
        delay = _POLL_START_S
        while True:
            status = driver.poll(task_id)
            state = status.get("state")
            if state == "done":
                result = dict(status.get("result") or {})
                result["provenance"] = self._provenance(driver_id, kind, prompt)
                return {"ok": True, "task": task_id, **result}
            if state == "failed":
                raise TeeError(
                    "generation_failed",
                    f"{driver_id} {kind} failed: {status.get('error', 'no detail')}",
                    fix="Adjust the prompt/options and retry; hosted credits "
                    "are typically not consumed by failures.",
                )
            if time.monotonic() - started > _POLL_CAP_S:
                raise TeeError(
                    "generation_timeout",
                    f"{driver_id} task {task_id} still {state} after {_POLL_CAP_S:.0f}s.",
                    fix=f"Poll later with as_generate_status(task='{task_id}', "
                    f"driver='{driver_id}').",
                )
            self._sleep(delay)
            delay = min(delay * 1.6, _POLL_MAX_S)

    def status(self, driver_id: str, task_id: str) -> dict[str, Any]:
        driver = self.drivers.get(driver_id)
        if driver is None:
            raise TeeError("unknown_generator", f"No generation driver '{driver_id}'.")
        return driver.poll(task_id)

    @staticmethod
    def _provenance(driver_id: str, kind: str, prompt: str) -> dict[str, Any]:
        return {
            "kind": "ai_generated",
            "generator": driver_id,
            "task_kind": kind,
            "input_hash": hashlib.sha256(prompt.encode()).hexdigest()[:16],
            "copyright_note": USCO_NOTE,
        }


# -- driver probes ----------------------------------------------------------


# Lane 3 (TRELLIS.2) renders through nvdiffrast, which is CUDA-bound; the
# diffusion lanes are plain diffusers and run on any torch backend. Treating
# "no CUDA" as "no local generation" wrongly excluded Apple Silicon, where
# unified memory is often larger than a discrete card's VRAM.
_CUDA_ONLY_LANES = (3,)
_DIFFUSION_LANES = (1, 2)


def probe_local_gpu() -> dict[str, Any]:
    """Which local lanes can run here? One compact answer with the exact gap."""
    try:
        import torch  # type: ignore[import-not-found]
    except ImportError:
        return {
            "available": False,
            "fix": "install the [assets-gen] extra (torch, diffusers); "
            "CUDA or Apple-Silicon MPS both work for the diffusion lanes",
        }
    if torch.cuda.is_available():
        return {
            "available": True,
            "backend": "cuda",
            "device": torch.cuda.get_device_name(0),
            "vram_gb": round(torch.cuda.get_device_properties(0).total_memory / 2**30, 1),
            "lanes": list(_DIFFUSION_LANES + _CUDA_ONLY_LANES),
        }
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return {
            "available": True,
            "backend": "mps",
            "device": "Apple Silicon (MPS)",
            "lanes": list(_DIFFUSION_LANES),
            "note": "lane 3 (TRELLIS.2) needs CUDA - nvdiffrast is CUDA-bound; "
            "use a hosted 3D generator instead",
        }
    return {
        "available": False,
        "backend": "cpu",
        "fix": "torch is present but has neither a CUDA device nor MPS; "
        "diffusion on CPU is too slow to be useful here",
    }


def torch_device() -> str:
    """The device string local lanes should load onto."""
    try:
        import torch  # type: ignore[import-not-found]
    except ImportError:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def build_drivers(config: dict[str, Any] | None = None) -> dict[str, GenDriver]:
    """Hosted drivers appear only when keyed; local only when the GPU probe
    passes. Geo-restricted generators (Hunyuan local) additionally need the
    explicit config opt-in and are labeled."""
    import os

    drivers: dict[str, GenDriver] = {}
    config = config or {}
    if os.environ.get("TEE_TRIPO_KEY"):
        from tee.assets.gen_hosted import TripoDriver

        drivers["tripo"] = TripoDriver(os.environ["TEE_TRIPO_KEY"])
    if os.environ.get("TEE_MESHY_KEY"):
        from tee.assets.gen_hosted import MeshyDriver

        drivers["meshy"] = MeshyDriver(os.environ["TEE_MESHY_KEY"])
    return drivers
