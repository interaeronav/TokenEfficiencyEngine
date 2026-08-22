"""TeeApp: composition root wiring adapters to the kernel.

One TeeApp per server process. Holds the per-adapter scene caches and the
shared managers; the MCP tool surface in `server.py` is a thin layer over
this object, so the whole app is testable without any MCP transport.

Concurrency: the mcp SDK dispatches every tool call on its own worker
thread. Kernel state (caches, checkpoints, response log) is not internally
locked, and the DCC bridges are serial by nature, so `app.lock` serializes
all tool bodies - the same discipline Epic's official MCP server enforces
(its tools run serially on the game thread; parallel dispatch deadlocks).
Jobs run outside the lock; their DCC calls queue on the bridge socket.
"""

from __future__ import annotations

import contextlib
import threading
from pathlib import Path
from typing import Any

from tee.config import ProjectConfig
from tee.kernel.adapter import Adapter
from tee.kernel.budget import ResponseLog
from tee.kernel.checkpoints import CheckpointManager
from tee.kernel.errors import AdapterUnavailable, TeeError
from tee.kernel.jobs import JobManager
from tee.kernel.memory import ProjectMemory
from tee.kernel.registry import ToolRegistry
from tee.kernel.scene_cache import SceneCache


class TeeApp:
    def __init__(
        self,
        adapters: dict[str, Adapter],
        project_root: Path | str = ".",
        *,
        allow_code_exec: bool = False,
    ):
        self.adapters = adapters
        self.caches: dict[str, SceneCache] = {name: SceneCache() for name in adapters}
        self.checkpoints = CheckpointManager()
        self.jobs = JobManager()
        self.memory = ProjectMemory(Path(project_root))
        self.registry = ToolRegistry()
        self.response_log = ResponseLog()
        self.config = ProjectConfig.load(project_root)
        self.registry.disabled = set(self.config.disabled_tools)
        # an explicit CLI flag enables; otherwise the project config decides
        self.allow_code_exec = allow_code_exec or bool(self.config.allow_code_exec)
        self.lock = threading.RLock()
        # installed by the extract module: (source, region, timestamp, budget)
        # -> (jpeg bytes, info) for the kernel tee_media tool
        self.media_view = None

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
            raise AdapterUnavailable(name, hint=self._busy_hint())
        return adapter

    def cache(self, name: str) -> SceneCache:
        return self.caches[name]

    def warm(self, name: str) -> None:
        """Establish a cache baseline from the DCC on first contact, so diff
        stamps handed to the model are never computed against a cold cache
        (a cold (0,0) stamp would otherwise yield silently-wrong deltas)."""
        cache = self.caches.get(name)
        adapter = self.adapters.get(name)
        if cache is None or adapter is None:
            return
        if cache.revision == 0 and not cache.entities and adapter.probe():
            cache.resync(adapter)

    # -- operations shared by tools ---------------------------------------

    def run_batch(
        self, adapter_name: str, ops: list[dict[str, Any]], label: str | None = None
    ) -> dict[str, Any]:
        adapter = self.adapter(adapter_name)
        self.warm(adapter_name)
        cache = self.cache(adapter_name)
        cp_label = label or f"auto:batch-r{cache.revision + 1}"
        checkpoint = self.checkpoints.create(adapter, cp_label, cache.revision)
        try:
            diff = adapter.execute(ops)
        except Exception as exc:
            # Make the failure atomic: a batch that failed mid-way must not
            # leave the DCC and the cache silently divergent.
            try:
                adapter.restore(checkpoint.payload)
                outcome = f"rolled back to checkpoint {checkpoint.id}; no ops were kept"
            except Exception:
                self.cache(adapter_name).invalidate()
                outcome = (
                    "rollback also failed - state may be partially applied; "
                    "run tee_scene_summary(refresh=true)"
                )
            if isinstance(exc, TeeError):
                fix = f"{exc.fix} Batch {outcome}." if exc.fix else f"Batch {outcome}."
                raise TeeError(exc.code, exc.message, fix=fix) from exc
            raise TeeError(
                "batch_failed",
                f"Batch failed: {type(exc).__name__}: {exc}",
                fix=f"Batch {outcome}.",
            ) from exc
        cache.apply_diff(diff, diff.upserts)
        payload: dict[str, Any] = {"ok": True, "checkpoint": checkpoint.id, **cache.stamp()}
        payload["applied"] = len(ops)
        payload.update(diff.to_payload())
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
                self.warm(name)
                info = adapter.info().to_payload()
            except Exception as exc:
                info = {"id": name, "connected": False, "error": str(exc)[:120]}
            if not info.get("connected"):
                busy = self._busy_hint()
                if busy:
                    info["note"] = busy
            info["scene"] = self.caches[name].stamp()
            adapters[name] = info
        jobs = [j for j in self.jobs.list() if j["state"] in ("queued", "running")]
        payload: dict[str, Any] = {
            "adapters": adapters,
            "active_jobs": jobs,
            "checkpoints": self.checkpoints.list()[-5:],
            "virtual_tools": len(self.registry),
            "code_exec_enabled": self.allow_code_exec,
        }
        if self.registry.disabled:
            payload["disabled_tools"] = sorted(self.registry.disabled)
        if self.config.warning:
            payload["config_warning"] = self.config.warning
        alerts = {
            tool: entry["alert"]
            for tool, entry in self.response_log.report().items()
            if "alert" in entry
        }
        if alerts:
            payload["response_size_alerts"] = alerts
        return payload

    def _busy_hint(self) -> str | None:
        """The serial bridge looks 'down' while a long job holds it."""
        active = [j for j in self.jobs.list() if j["state"] == "running"]
        if active:
            names = ", ".join(f"{j['job']} ({j['label']})" for j in active[:3])
            return f"the bridge may be busy with a running job: {names}"
        return None

    def shutdown(self) -> None:
        self.jobs.shutdown()
        for adapter in self.adapters.values():
            with contextlib.suppress(Exception):
                self.checkpoints.discard_all(adapter)
            close = getattr(adapter, "close", None)
            if close is not None:
                with contextlib.suppress(Exception):
                    close()
