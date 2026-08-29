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
        "eta_s": 30,
        "qos_default": "interactive",
        "cost": {"latency_s": [0.74, 1.74], "measured": "R0 2026-08-29"},
    },
    "q27b-bare": {
        "kind": "llm",
        "profile": "q27b",
        "capability": ["chores"],
        "footprint_gb": 55.0,  # 43.7 measured R0 2026-08-29
        "eta_s": 90,
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
    "reconstruct-odm": {
        "kind": "job",
        "capability": ["drone-sets"],
        "footprint_gb": 16.0,  # the colima VM allocation
        "qos_default": "batch",
        "cost": {"wall_s": [210, 310], "measured": "T0/T2 live runs 2026-08-29"},
    },
}


def _total_ram_gb() -> float:
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

    def register_job(self, key: str, engine: str) -> dict[str, Any]:
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
            "footprint_gb": float(spec["footprint_gb"]),
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
