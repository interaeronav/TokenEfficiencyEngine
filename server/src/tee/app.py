"""TeeApp: composition root wiring adapters to the kernel.

One TeeApp per server process. Holds the per-adapter scene caches and the
shared managers; the MCP tool surface in `server.py` is a thin layer over
this object, so the whole app is testable without any MCP transport.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tee.kernel.adapter import Adapter
from tee.kernel.budget import ResponseLog
from tee.kernel.checkpoints import CheckpointManager
from tee.kernel.errors import AdapterUnavailable, TeeError
from tee.kernel.jobs import JobManager
from tee.kernel.memory import ProjectMemory
from tee.kernel.registry import ToolRegistry
from tee.kernel.scene_cache import SceneCache


class TeeApp:
    def __init__(self, adapters: dict[str, Adapter], project_root: Path | str = "."):
        self.adapters = adapters
        self.caches: dict[str, SceneCache] = {name: SceneCache() for name in adapters}
        self.checkpoints = CheckpointManager()
        self.jobs = JobManager()
        self.memory = ProjectMemory(Path(project_root))
        self.registry = ToolRegistry()
        self.response_log = ResponseLog()

    # -- helpers -----------------------------------------------------------

    def adapter(self, name: str) -> Adapter:
        adapter = self.adapters.get(name)
        if adapter is None:
            known = ", ".join(sorted(self.adapters)) or "(none)"
            raise TeeError(
                "unknown_adapter",
                f"No adapter '{name}'.",
                fix=f"Configured adapters: {known}.",
            )
        if not adapter.probe():
            raise AdapterUnavailable(name)
        return adapter

    def cache(self, name: str) -> SceneCache:
        return self.caches[name]

    # -- operations shared by tools ---------------------------------------

    def run_batch(
        self, adapter_name: str, ops: list[dict[str, Any]], label: str | None = None
    ) -> dict[str, Any]:
        adapter = self.adapter(adapter_name)
        cache = self.cache(adapter_name)
        cp_label = label or f"auto:batch-r{cache.revision + 1}"
        checkpoint = self.checkpoints.create(adapter, cp_label, cache.revision)
        try:
            diff = adapter.execute(ops)
        except TeeError:
            raise
        except Exception as exc:
            raise TeeError(
                "batch_failed",
                f"Batch failed after checkpoint {checkpoint.id}: {type(exc).__name__}: {exc}",
                fix=f"Scene unchanged or roll back with tee_rollback(ref='{checkpoint.id}').",
            ) from exc
        revision = cache.apply_diff(diff, diff.upserts)
        payload: dict[str, Any] = {"ok": True, "checkpoint": checkpoint.id, **cache.stamp()}
        payload["applied"] = len(ops)
        payload.update(diff.to_payload())
        _ = revision
        return payload

    def rollback(self, adapter_name: str, ref: str) -> dict[str, Any]:
        adapter = self.adapter(adapter_name)
        cache = self.cache(adapter_name)
        cp = self.checkpoints.rollback(adapter, ref)
        cache.resync(adapter)  # continuity break + rebuild from restored state
        return {"ok": True, "restored": cp.to_payload(), **cache.stamp()}

    def status(self) -> dict[str, Any]:
        adapters = {}
        for name, adapter in self.adapters.items():
            try:
                info = adapter.info().to_payload()
            except Exception as exc:
                info = {"id": name, "connected": False, "error": str(exc)[:120]}
            info["scene"] = self.caches[name].stamp()
            adapters[name] = info
        jobs = [j for j in self.jobs.list() if j["state"] in ("queued", "running")]
        payload: dict[str, Any] = {
            "adapters": adapters,
            "active_jobs": jobs,
            "checkpoints": self.checkpoints.list()[-5:],
            "virtual_tools": len(self.registry),
        }
        alerts = {
            tool: entry["alert"]
            for tool, entry in self.response_log.report().items()
            if "alert" in entry
        }
        if alerts:
            payload["response_size_alerts"] = alerts
        return payload

    def shutdown(self) -> None:
        self.jobs.shutdown()
