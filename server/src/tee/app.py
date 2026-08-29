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
import math
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


def _values_match(requested: Any, actual: Any) -> bool:
    """Echo test with float tolerance: a DCC rounding a requested 1.0 to
    1.0000000149 is still an echo, not drift worth reporting."""
    if isinstance(requested, (int, float)) and isinstance(actual, (int, float)):
        return math.isclose(float(requested), float(actual), rel_tol=1e-5, abs_tol=1e-5)
    if isinstance(requested, list) and isinstance(actual, list):
        return len(requested) == len(actual) and all(
            _values_match(r, a) for r, a in zip(requested, actual, strict=True)
        )
    return bool(requested == actual)


def _trim_batch_echoes(
    ops: list[dict[str, Any]],
    payload: dict[str, Any],
    prior: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Batch reports carry drift, not echoes (hard rule 2).

    A detail field that exactly matches what the op requested says nothing -
    drop it. For modified entities, a field whose value is unchanged from the
    pre-batch cache state is a re-report, not news - drop it too. Everything
    else (measured dims, adapter renames, computed side effects) stays.
    Created ids remain addressable via a compact names map. `created` is
    op-ordered: all three adapters build it by sequential append, and batches
    are atomic, so create op N maps to created[N]. The full post-op state
    still reaches the scene cache - this trims only the client payload."""
    details = payload.get("details")
    if not isinstance(details, dict):
        return
    requested: dict[str, dict[str, Any]] = {}
    created_list = payload.get("created") or []
    creator_ops = [op for op in ops if op.get("op") not in ("set", "delete")]
    if len(creator_ops) == len(created_list):
        # every creator op (create, import_file, ...) yielded exactly one
        # entity, in op order - map request to id; otherwise skip the
        # request mapping and rely on the prior-state rule alone
        for op, eid in zip(creator_ops, created_list, strict=False):
            req = dict(op.get("props") or {})
            for key in ("name", "kind"):
                if key in op:
                    req[key] = op[key]
            requested[eid] = req
    for op in ops:
        if op.get("op") == "set" and op.get("id") is not None:
            requested.setdefault(str(op["id"]), {}).update(op.get("props") or {})
    names: dict[str, str] = {}
    for eid in payload.get("created") or []:
        det = details.get(eid)
        if isinstance(det, dict) and isinstance(det.get("name"), str):
            names[eid] = det["name"]
    for eid, det in list(details.items()):
        if not isinstance(det, dict):
            continue
        req = requested.get(eid, {})
        was = (prior or {}).get(eid, {})
        for field in list(det):
            if (
                field == "id"
                or (field == "name" and eid in names)
                or (field in req and _values_match(req[field], det[field]))
                or (field in was and _values_match(was[field], det[field]))
            ):
                del det[field]
        if not det:
            del details[eid]
    if not details:
        payload.pop("details", None)
    if names:
        payload["names"] = names


class TeeApp:
    def __init__(
        self,
        adapters: dict[str, Adapter],
        project_root: Path | str = ".",
        *,
        allow_code_exec: bool = False,
    ):
        from tee.kernel.machine import MachineLedger

        self.adapters = adapters
        self.caches: dict[str, SceneCache] = {name: SceneCache() for name in adapters}
        self.checkpoints = CheckpointManager()
        self.jobs = JobManager()
        self.machine = MachineLedger()  # the ONE machine-load ledger (A42 R1)
        self.project_root = Path(project_root)
        self.memory = ProjectMemory(Path(project_root))
        self.registry = ToolRegistry()
        self.response_log = ResponseLog()
        self.config = ProjectConfig.load(project_root)
        self.registry.disabled = set(self.config.disabled_tools)
        # K0 shadow recorder: on by default, zero behavior change; the
        # degrade-to-static law - [scheduler] shadow = false turns it off.
        from tee.kernel import shadow

        scheduler_cfg = dict(self.config.scheduler or {})
        if scheduler_cfg.get("shadow", True):
            shadow.RECORDER.enable(
                Path(project_root) / ".tee" / "shadow",
                cap_mb=float(scheduler_cfg.get("cap_mb", shadow.DEFAULT_CAP_MB)),
            )
        # K1: QoS as law (admission + rank + aging) - [scheduler] qos = false
        # restores plain FIFO, the degrade-to-static promise.
        self.jobs.configure(
            machine=self.machine,
            qos=bool(scheduler_cfg.get("qos", True)),
            aging_s=scheduler_cfg.get("aging_s"),
        )
        self.machine.set_queue_probe(self.jobs.queue_ages)
        # an explicit CLI flag enables; otherwise the project config decides
        self.allow_code_exec = allow_code_exec or bool(self.config.allow_code_exec)
        self.lock = threading.RLock()
        # installed by the extract module: (source, region, timestamp, budget)
        # -> (jpeg bytes, info) for the kernel tee_media tool
        self.media_view = None
        # installed by the extract module: () -> compact store recap dict
        self.extract_recap = None
        self._web = None  # lazy WebLookupService (A34)
        self.gateway = None  # GatewayService when [gateway] backends exist (A37)
        from tee.boards import register_board_tools
        from tee.kernel.meter import register_session_tools

        register_session_tools(self)  # report_savings + handoff (A37 P6)
        register_board_tools(self)  # board_compose (A37 P7)

    @property
    def llm_cfg(self) -> dict:
        """[llm] config enriched with the state dir the switch profiles
        persist into (A37 P0-S) - the one dict every chore consumer gets."""
        cfg = dict(self.config.llm or {})
        cfg["_state_dir"] = str(self.project_root / ".tee")
        return cfg

    @property
    def web(self):
        """The web-lookup service, built on first use from [web] config."""
        if self._web is None:
            from tee.web.tools import WebLookupService

            self._web = WebLookupService(
                self.project_root,
                config=self.config.web,
                llm=self.llm_cfg,
                registry=self.registry,
            )
        return self._web

    # -- helpers -----------------------------------------------------------

    def resolve_adapter(self, name: str | None) -> str:
        """Resolve an omitted adapter= to the sole configured adapter.

        Real deployments serve one adapter, so omitting the argument must
        just work there (SI-B6: a wire-visible default of 'fake' failed on
        every non-test server and taxed each call with an explicit
        adapter=). Ambiguity fails loud with the configured choices."""
        if name is not None:
            return name
        if len(self.adapters) == 1:
            return next(iter(self.adapters))
        known = ", ".join(sorted(self.adapters)) or "(none)"
        raise TeeError(
            "adapter_required",
            "Several adapters are configured; pass adapter=.",
            fix=f"Configured adapters: {known}.",
        )

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
        self,
        adapter_name: str,
        ops: list[dict[str, Any]],
        label: str | None = None,
        *,
        checkpoint: bool = True,
    ) -> dict[str, Any]:
        """checkpoint=False is for callers that already hold an enclosing
        checkpoint and roll back on any raise (the script lane): the inner
        checkpoint+restore is then redundant work - on UE it doubled the
        cost of every scripted batch (A35 P2, two extra game-thread
        dispatches per batch)."""
        adapter = self.adapter(adapter_name)
        self.warm(adapter_name)
        cache = self.cache(adapter_name)
        cp_label = label or f"auto:batch-r{cache.revision + 1}"
        cp = self.checkpoints.create(adapter, cp_label, cache.revision) if checkpoint else None
        try:
            diff = adapter.execute(ops)
        except Exception as exc:
            # Make the failure atomic: a batch that failed mid-way must not
            # leave the DCC and the cache silently divergent.
            if cp is None:
                outcome = "is restored by the enclosing script checkpoint"
            else:
                try:
                    adapter.restore(cp.payload)
                    outcome = f"rolled back to checkpoint {cp.id}; no ops were kept"
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
        prior: dict[str, dict[str, Any]] = {}
        for eid in diff.modified:
            ent = cache.get(eid)
            if ent is not None:
                prior[eid] = ent.detailed()
        cache.apply_diff(diff, diff.upserts)
        payload: dict[str, Any] = {"ok": True, **cache.stamp()}
        if cp is not None:
            payload["checkpoint"] = cp.id
        payload["applied"] = len(ops)
        payload.update(diff.to_payload())
        _trim_batch_echoes(ops, payload, prior)
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
        from tee.llm import profiles

        payload: dict[str, Any] = {
            "adapters": adapters,
            "active_jobs": jobs,
            "checkpoints": self.checkpoints.list()[-5:],
            "virtual_tools": len(self.registry),
            "code_exec_enabled": self.allow_code_exec,
            "llm_profile": profiles.status_line(self.llm_cfg),
        }
        if self.registry.disabled:
            payload["disabled_tools"] = sorted(self.registry.disabled)
        if self.gateway is not None:
            payload["gateway"] = self.gateway.status()
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

    def recap(self) -> dict[str, Any]:
        """Eviction-safe resume (Phase 8, A12): a compact project recap
        rebuilt entirely from server-side state - scene stamps and kind
        counts, recent checkpoints, extract store shape, memory - so a host
        that evicted old tool results catches up with one call."""
        adapters: dict[str, Any] = {}
        for name, cache in self.caches.items():
            kinds: dict[str, int] = {}
            for entity in cache.entities.values():
                kinds[entity.kind] = kinds.get(entity.kind, 0) + 1
            adapters[name] = {**cache.stamp(), "entities": len(cache.entities)}
            if kinds:
                adapters[name]["kinds"] = kinds
        out: dict[str, Any] = {"adapters": adapters}
        checkpoints = self.checkpoints.list()[-3:]
        if checkpoints:
            out["checkpoints"] = checkpoints
        memory = self.memory.preamble()
        if memory.get("facts") or memory.get("notes"):
            out["memory"] = memory
        if self.extract_recap is not None:
            with contextlib.suppress(Exception):
                out["extract"] = self.extract_recap()
        active = [j for j in self.jobs.list() if j["state"] in ("queued", "running")]
        if active:
            out["active_jobs"] = active
        from tee.kernel.meter import savings_block

        block = savings_block(self.response_log.ledger())
        if block:
            out["savings"] = block
        meter = self.machine.meter_block()
        if meter["routed_tasks"] or meter["jobs"]["active"]:
            swaps = meter["swaps"]["implicit"] + meter["swaps"]["explicit"]
            line = (
                f"{meter['routed_tasks']} routed / {meter['escalations']} escalated, "
                f"{swaps} swaps ({meter['swaps']['refused']} refused)"
            )
            with contextlib.suppress(Exception):
                from tee.llm import profiles

                if profiles.load_state(self.llm_cfg).get("pinned"):
                    line += ", pinned"
            out["router"] = line
        return out

    def _busy_hint(self) -> str | None:
        """The serial bridge looks 'down' while a long job holds it."""
        active = [j for j in self.jobs.list() if j["state"] == "running"]
        if active:
            names = ", ".join(f"{j['job']} ({j['label']})" for j in active[:3])
            return f"the bridge may be busy with a running job: {names}"
        return None

    def shutdown(self) -> None:
        from tee.kernel import shadow

        shadow.RECORDER.disable()
        self.jobs.shutdown()
        if self.gateway is not None:
            with contextlib.suppress(Exception):
                self.gateway.shutdown()
        for adapter in self.adapters.values():
            with contextlib.suppress(Exception):
                self.checkpoints.discard_all(adapter)
            close = getattr(adapter, "close", None)
            if close is not None:
                with contextlib.suppress(Exception):
                    close()
