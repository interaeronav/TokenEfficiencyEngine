"""Voxkiln driver: lane-3 local 3D generation as the DEFAULT generator
(decision A28; Phase 13). Wraps the voxkiln JobStore behind TEE's
GenDriver protocol - unpaid, no cost gate, image-to-model only.

voxkiln imports lazily so the TEE server never carries torch; the driver
registers only when voxkiln is installed AND its backend probe finds MPS
or CUDA (see build_drivers). Tests inject a stub store instead."""

from __future__ import annotations

from typing import Any

from tee.kernel.errors import TeeError


def voxkiln_available() -> bool:
    """Installed and able to run here (backend present)."""
    try:
        from voxkiln.engine import probe  # type: ignore[import-not-found]
    except ImportError:
        return False
    return probe().get("backend") is not None


class VoxkilnDriver:
    id = "voxkiln"
    paid = False

    def __init__(self, store=None):
        self._store = store

    def _jobs(self):
        if self._store is None:
            from voxkiln.jobs import JobStore  # type: ignore[import-not-found]

            self._store = JobStore()
        return self._store

    def estimate(self, kind: str, options: dict[str, Any]) -> dict[str, Any]:
        try:
            from voxkiln.engine import estimate  # type: ignore[import-not-found]

            est = estimate(str(options.get("pipeline_type", "1024_cascade")))
        except ImportError:
            est = {}
        return {"cost_usd": 0, "note": "local generation (voxkiln)", **est}

    def submit(self, kind: str, prompt: str, options: dict[str, Any]) -> str:
        if kind not in ("image_to_model", "text_to_model"):
            raise TeeError(
                "unsupported_kind",
                f"voxkiln generates from images, not '{kind}'.",
                fix="Pass kind='image_to_model' with prompt=<path to the "
                "concept image>; for text, render a concept image first "
                "(lane 1) - that also gives you a cheap review checkpoint.",
            )
        if kind == "text_to_model":
            raise TeeError(
                "image_required",
                "voxkiln is image-to-3D; there is no local text-to-3D lane.",
                fix="Generate or pick a concept image, then re-call with "
                "kind='image_to_model' and prompt=<image path>. Hosted "
                "text-to-3D: driver='tripo' or 'meshy' (keys required).",
            )
        options = dict(options or {})
        budget = options.pop("budget", None)
        seed = int(options.pop("seed", 0))
        params = {
            k: options[k]
            for k in ("pipeline_type", "texture_size", "target_faces", "repair_level")
            if k in options
        }
        ack = self._jobs().submit(prompt, params=params or None, budget=budget, seed=seed)
        return str(ack["job_id"])

    def poll(self, task_id: str) -> dict[str, Any]:
        q = self._jobs().query(task_id)
        state = q.get("state")
        if state == "done":
            result = {k: v for k, v in q.items() if k not in ("state", "job_id")}
            return {"state": "done", "result": result}
        if state == "failed":
            detail = q.get("message") or q.get("error") or "no detail"
            fix = q.get("fix")
            return {"state": "failed", "error": f"{detail}" + (f" (fix: {fix})" if fix else "")}
        return {"state": "running" if state == "running" else "queued"}
