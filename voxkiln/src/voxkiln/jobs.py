"""The job model (decision A28): submit -> ONE bounded wait -> compact
report. Polling happens server-side in a worker thread; the caller never
loops. Cache is checked before any engine work."""

from __future__ import annotations

import hashlib
import queue
import threading
import time
import traceback
import uuid
from pathlib import Path
from typing import Any

from voxkiln import cache as cache_mod
from voxkiln import engine as engine_mod
from voxkiln import report as report_mod

DEFAULT_PARAMS = {
    "pipeline_type": "1024_cascade",
    "texture_size": 1024,
    "target_faces": 500_000,
    "repair_level": "fast",
}


class Job:
    def __init__(self, job_id: str, request: dict[str, Any]):
        self.id = job_id
        self.request = request
        self.state = "queued"
        self.report: dict[str, Any] | None = None
        self.error: dict[str, Any] | None = None
        self.done = threading.Event()


class JobStore:
    """One worker thread, FIFO queue, in-process. The Mac deployment moves
    the engine into a worker *process* with a heartbeat (script 13.3.3);
    the job contract is identical either way."""

    def __init__(self, engine=None, out_dir: str | Path = "voxkiln_out", use_cache: bool = True):
        self.engine = engine
        self.out_dir = Path(out_dir)
        self.use_cache = use_cache
        self.jobs: dict[str, Job] = {}
        self._queue: queue.Queue[Job] = queue.Queue()
        self._worker: threading.Thread | None = None
        self._lock = threading.Lock()

    # -- public API (the four calls) ------------------------------------

    def submit(
        self,
        image_path: str | Path,
        params: dict[str, Any] | None = None,
        budget: dict[str, Any] | None = None,
        seed: int = 0,
    ) -> dict[str, Any]:
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"input image not found: {image_path}")
        report_mod.validate_budget(budget)
        merged = {**DEFAULT_PARAMS, **(params or {})}
        image_sha = hashlib.sha256(image_path.read_bytes()).hexdigest()
        key = cache_mod.request_key(
            image_sha, {**merged, "seed": seed}, getattr(self.engine, "revision", None)
        )

        if self.use_cache:
            cached = cache_mod.get(key)
            if cached is not None:
                job = Job(f"vk-{uuid.uuid4().hex[:8]}", {})
                job.state = "done"
                job.report = cached
                job.done.set()
                self.jobs[job.id] = job
                return {
                    "job_id": job.id,
                    "cache_hit": True,
                    **engine_mod.estimate(merged["pipeline_type"]),
                }

        engine = self._require_engine()
        job = Job(
            f"vk-{uuid.uuid4().hex[:8]}",
            {
                "image_path": image_path,
                "image_sha256": image_sha,
                "params": merged,
                "budget": budget,
                "seed": seed,
                "cache_key": key,
            },
        )
        self.jobs[job.id] = job
        self._queue.put(job)
        self._ensure_worker(engine)
        est = engine_mod.estimate(merged["pipeline_type"])
        est["queue_position"] = self._queue.qsize()
        return {"job_id": job.id, "cache_hit": False, **est}

    def wait(self, job_id: str, timeout_s: float = 900.0) -> dict[str, Any]:
        job = self._get(job_id)
        if not job.done.wait(timeout=timeout_s):
            return {
                "job_id": job.id,
                "state": job.state,
                "timeout": True,
                "fix": f"still {job.state}; call wait('{job.id}') again to resume",
            }
        if job.error is not None:
            return {"job_id": job.id, "state": "failed", **job.error}
        return {"job_id": job.id, "state": "done", **job.report}

    def generate(
        self,
        image_path: str | Path,
        params: dict[str, Any] | None = None,
        budget: dict[str, Any] | None = None,
        seed: int = 0,
        timeout_s: float = 900.0,
    ) -> dict[str, Any]:
        """submit + wait: the one call agents use."""
        ack = self.submit(image_path, params=params, budget=budget, seed=seed)
        return self.wait(ack["job_id"], timeout_s=timeout_s)

    def query(self, job_id: str) -> dict[str, Any]:
        job = self._get(job_id)
        out: dict[str, Any] = {"job_id": job.id, "state": job.state}
        if job.report is not None:
            out.update(job.report)
        if job.error is not None:
            out.update(job.error)
        return out

    # -- internals -------------------------------------------------------

    def _require_engine(self):
        if self.engine is None:
            engine_mod.require_backend()  # raises the structured refusal
            self.engine = engine_mod.Engine()
        return self.engine

    def _get(self, job_id: str) -> Job:
        job = self.jobs.get(job_id)
        if job is None:
            raise KeyError(f"unknown job '{job_id}'")
        return job

    def _ensure_worker(self, engine) -> None:
        with self._lock:
            if self._worker is None or not self._worker.is_alive():
                self._worker = threading.Thread(target=self._run, args=(engine,), daemon=True)
                self._worker.start()

    def _run(self, engine) -> None:
        while True:
            try:
                job = self._queue.get(timeout=1.0)
            except queue.Empty:
                return
            job.state = "running"
            try:
                job.report = self._execute(engine, job)
                job.state = "done"
            except engine_mod.EngineUnavailable as exc:
                job.error = exc.payload
                job.state = "failed"
            except Exception as exc:  # fail loud and cheap, no stack novel
                job.error = {
                    "error": "generation_failed",
                    "message": f"{type(exc).__name__}: {exc}",
                    "fix": _fix_for(exc),
                    "trace_tail": traceback.format_exc().strip().splitlines()[-3:],
                }
                job.state = "failed"
            finally:
                job.done.set()

    def _execute(self, engine, job: Job) -> dict[str, Any]:
        from PIL import Image

        from voxkiln.export import export_glb

        req = job.request
        params = req["params"]
        timings: dict[str, float] = {}

        t0 = time.monotonic()
        image = Image.open(req["image_path"])
        raw = engine.generate(image, seed=req["seed"], params=params)
        timings.update(raw.get("timings", {}))

        self.out_dir.mkdir(parents=True, exist_ok=True)
        asset_id = job.id
        glb_path = self.out_dir / f"{asset_id}.glb"
        t1 = time.monotonic()
        export_report = export_glb(
            raw["vertices"],
            raw["faces"],
            raw["voxel"],
            str(glb_path),
            texture_size=params["texture_size"],
            target_faces=params["target_faces"],
            repair_level=params["repair_level"],
        )
        timings["export_s"] = time.monotonic() - t1
        timings["total_s"] = time.monotonic() - t0

        stats = export_report["stats"]
        stats["texture_size"] = export_report["export"]["texture_size"]
        prov = report_mod.provenance(
            input_image_sha256=req["image_sha256"],
            seed=req["seed"],
            params=params,
            model_revision=getattr(engine, "revision", None),
        )
        notices = list(raw.get("notices", []))
        if "texture_size_clamped" in export_report["export"]:
            c = export_report["export"]["texture_size_clamped"]
            notices.append(f"texture clamped {c['requested']} -> {c['actual']}: {c['reason']}")
        rep = report_mod.build_report(
            asset_id=asset_id,
            files={"glb": str(glb_path)},
            stats=stats,
            repairs=export_report["repairs"],
            budget=req["budget"],
            prov=prov,
            timings=timings,
            notices=notices or None,
        )
        rep["mesh_hash"] = report_mod.mesh_content_hash(raw["vertices"], raw["faces"])
        rep["export"] = {"alpha_mode": export_report["export"]["alpha_mode"]}
        if self.use_cache:
            cache_mod.put(req["cache_key"], rep)
        return rep


def _fix_for(exc: BaseException) -> str:
    """Map a failure to the action that actually resolves it.

    "inspect params" is useless advice for a gated download: no parameter the
    caller can change will grant access. The gated case is the one every new
    machine hits, so it gets named explicitly.
    """
    text = f"{type(exc).__name__}: {exc}"
    if "gated repo" in text.lower() or "GatedRepoError" in text:
        import voxkiln

        return (
            f"the image-conditioning model is gated: request access at "
            f"https://huggingface.co/{voxkiln.IMAGE_COND_REPO} (approved "
            f"manually by the owner), then `hf auth login`. "
            f"`voxkiln doctor` reports this before a run."
        )
    if "401" in text or "Unauthorized" in text:
        return "authenticate with `hf auth login` (or set HF_TOKEN)"
    if "No space left" in text or "OSError: [Errno 28]" in text:
        return "free disk space; weights and outputs need ~20 GB"
    return "inspect params; if this repeats, run voxkiln doctor"
