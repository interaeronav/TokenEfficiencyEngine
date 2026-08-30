"""ONE machine-load ledger + registry-form engine facts (A42 R1, seams 1+3).

Research 58's K-layer registry schema, authored NOW so the K-phases
inherit rows instead of migrating them: every engine carries capability,
measured cost references, footprint and a default QoS class. QoS classes
are LABELS at this stage (seam 3) - K1 turns them into law.

The ledger is the single arbiter of heavyweight residency (the A41 guard
seam): reconstruction jobs register here, a routed engine swap is refused
with the honest line while any registered job runs, and a job launch can
ask what is resident. Capability math is deterministic bookkeeping
(total RAM - reserve - registered jobs vs the target footprint);
measured swap-cost constants arrive in R2, not here.
"""

from __future__ import annotations

import os
import threading
from typing import Any

from tee.kernel.errors import TeeError

QOS = ("interactive", "standard", "batch", "maintenance")

# The client stack + OS headroom the machine always keeps. A stated
# placeholder until R2 measures the real constant.
RESERVE_GB = 16.0

# name -> registry-form facts. "profile" binds an llm row to its switch
# profile; footprints are spec values with the measured number cited.
ENGINES: dict[str, dict[str, Any]] = {
    "q14b+a2": {
        "kind": "llm",
        "profile": "q14b",
        "capability": ["chores"],
        "footprint_gb": 9.0,  # 8.0 measured R0 2026-08-29
        "eta_s": 1.1,  # measured swap cost R2 2026-08-29 (spec said 30)
        "qos_default": "interactive",
        "cost": {"latency_s": [0.74, 1.74], "measured": "R0 2026-08-29"},
    },
    "q27b-bare": {
        "kind": "llm",
        "profile": "q27b",
        "capability": ["chores"],
        "footprint_gb": 55.0,  # 43.7 measured R0 2026-08-29
        "eta_s": 18.0,  # measured swap cost R2 2026-08-29 (spec said 90)
        "qos_default": "interactive",
        "cost": {"latency_s": [3.07, 9.69], "measured": "R0 2026-08-29"},
    },
    "client": {
        "kind": "client",
        "capability": ["everything"],
        "footprint_gb": 0.0,
        "qos_default": "interactive",
        "cost": {"tokens": "input grows unbounded by any window (R0)"},
    },
    "reconstruct-photogrammetry": {
        "kind": "job",
        "capability": ["structure-sets"],
        "footprint_gb": 1.0,  # 0.88 peak measured T0 2026-08-29
        "qos_default": "batch",
        "cost": {"wall_s": [6, 18], "measured": "T0 ladder, 36-view fixture"},
    },
    "pipeline-step": {
        "kind": "job",
        "capability": ["declared-steps"],
        "footprint_gb": 2.0,  # default; a declaration's own cost hint overrides
        "qos_default": "batch",
        "cost": {"wall_s": "declared per step (A43 P1)"},
    },
    "reconstruct-odm": {
        "kind": "job",
        "capability": ["drone-sets"],
        "footprint_gb": 16.0,  # the colima VM allocation
        "qos_default": "batch",
        "cost": {"wall_s": [210, 310], "measured": "T0/T2 live runs 2026-08-29"},
    },
}


def _total_ram_gb() -> float:
    # TEE_MACHINE_TOTAL_GB declares capacity where the host's physical
    # RAM is not the truth: CI runners, containers/VMs (the colima ODM
    # allocation), and hermetic tests. Unset -> the host's real memory.
    declared = os.environ.get("TEE_MACHINE_TOTAL_GB")
    if declared:
        try:
            return float(declared)
        except ValueError:
            raise TeeError(
                "machine_bad_capacity",
                f"TEE_MACHINE_TOTAL_GB={declared!r} is not a number.",
                fix="Set it to the machine's usable RAM in GB, e.g. 128.",
            ) from None
    try:
        return os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") / 1e9
    except (ValueError, OSError):  # pragma: no cover - exotic platforms
        return 8.0


class MachineLedger:
    """The one ledger. Register long-running work; ask before swapping."""

    def __init__(self, total_gb: float | None = None):
        self.total_gb = float(total_gb if total_gb is not None else _total_ram_gb())
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        # the merged meter's routing counters (A42 R2, seam 2)
        self._tasks = 0
        self._escalations = 0
        self._routes: dict[str, dict[str, int]] = {}
        self._swaps = {"explicit": 0, "implicit": 0, "refused": 0, "seconds_known": 0.0}
        self._last_refusal: str | None = None
        self._queue_probe = None  # installed by the app (K1): () -> {queued, max_s}
        self._dispatch = {"static": 0, "greedy": 0, "pinned": 0}
        self._last_dispatch: str | None = None

    def register_job(
        self, key: str, engine: str, footprint_gb: float | None = None
    ) -> dict[str, Any]:
        spec = ENGINES.get(engine)
        if spec is None or spec["kind"] != "job":
            known = sorted(n for n, s in ENGINES.items() if s["kind"] == "job")
            raise TeeError(
                "machine_unknown_engine",
                f"'{engine}' is not a registered job engine.",
                fix=f"Job engines: {', '.join(known)}.",
            )
        row = {
            "key": str(key),
            "engine": engine,
            "footprint_gb": float(
                footprint_gb if footprint_gb is not None else spec["footprint_gb"]
            ),
            "qos": str(spec["qos_default"]),
        }
        with self._lock:
            self._jobs[row["key"]] = row
        return dict(row)

    def release_job(self, key: str) -> None:
        with self._lock:
            self._jobs.pop(str(key), None)

    def active_jobs(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(row) for row in self._jobs.values()]

    def jobs_footprint_gb(self) -> float:
        with self._lock:
            return sum(row["footprint_gb"] for row in self._jobs.values())

    def may_swap(self, engine: str) -> tuple[bool, str]:
        """May the machine take on `engine`'s footprint right now?

        Single occupancy means the current resident leaves first, so the
        question is target vs (total - reserve - registered jobs)."""
        spec = ENGINES.get(engine)
        if spec is None:
            return False, f"unknown engine '{engine}' - not in the registry"
        active = self.active_jobs()
        if active:
            held = ", ".join(f"{row['key']} ({row['engine']}, {row['qos']})" for row in active)
            return False, (
                f"swap deferred: {len(active)} registered job(s) hold the machine - {held}"
            )
        target = float(spec["footprint_gb"])
        available = self.total_gb - RESERVE_GB
        if target > available:
            return False, (
                f"{engine} needs {target:.0f} GB; {available:.0f} GB available "
                f"({self.total_gb:.0f} total - {RESERVE_GB:.0f} reserve)"
            )
        return True, f"capable: {target:.0f} GB fits in {available:.0f} GB available"

    def may_admit(self, engine: str) -> tuple[bool, str]:
        """K1 admission: refuse only work the machine can NEVER place -
        queueing behind current residents stays legal."""
        spec = ENGINES.get(engine)
        if spec is None:
            return True, "no registry row - admitted"
        target = float(spec["footprint_gb"])
        available = self.total_gb - RESERVE_GB
        if target > available:
            return False, (
                f"{engine} needs {target:.0f} GB and the machine can never "
                f"place it ({available:.0f} GB after the {RESERVE_GB:.0f} GB reserve)"
            )
        return True, "placeable"

    def set_queue_probe(self, probe) -> None:
        self._queue_probe = probe

    # -- the merged meter (A42 R2; ONE meter, seam 2) ----------------------

    def record_task(self) -> None:
        with self._lock:
            self._tasks += 1

    def record_route(self, engine: str, verified: bool) -> None:
        with self._lock:
            row = self._routes.setdefault(engine, {"calls": 0, "verified": 0})
            row["calls"] += 1
            if verified:
                row["verified"] += 1

    def record_escalation(self) -> None:
        with self._lock:
            self._escalations += 1

    def record_dispatch(self, mode: str, reason: str) -> None:
        with self._lock:
            self._dispatch[mode] = self._dispatch.get(mode, 0) + 1
            self._last_dispatch = reason

    def record_swap(
        self, *, implicit: bool = False, refused: str | None = None, seconds: float | None = None
    ) -> None:
        with self._lock:
            if refused is not None:
                self._swaps["refused"] += 1
                self._last_refusal = refused
                return
            self._swaps["implicit" if implicit else "explicit"] += 1
            if seconds is not None:
                self._swaps["seconds_known"] += float(seconds)

    def meter_block(self) -> dict[str, Any]:
        """Escalation, swap and job-class columns TOGETHER, with the
        scheduler's columns reserved in the same schema (research 59
        seam 2 - no later migration)."""
        with self._lock:
            block: dict[str, Any] = {
                "routed_tasks": self._tasks,
                "engines": {name: dict(row) for name, row in self._routes.items()},
                "escalations": self._escalations,
                "escalation_rate": round(self._escalations / self._tasks, 3)
                if self._tasks
                else 0.0,
                "swaps": {
                    key: (round(value, 1) if isinstance(value, float) else value)
                    for key, value in self._swaps.items()
                },
                "jobs": {
                    "active": len(self._jobs),
                    "batch_footprint_gb": round(
                        sum(row["footprint_gb"] for row in self._jobs.values()), 1
                    ),
                },
                "scheduler": {
                    "queue_age_s": (self._queue_probe() if self._queue_probe else "reserved (K1)"),
                    "dispatch_reason": (
                        {"last": self._last_dispatch, **self._dispatch}
                        if self._last_dispatch
                        else "reserved (K2)"
                    ),
                    "shadow_delta": "reserved (K2; recorder live since K0)",
                },
            }
            if self._last_refusal:
                block["swaps"]["last_refusal"] = self._last_refusal
            return block
