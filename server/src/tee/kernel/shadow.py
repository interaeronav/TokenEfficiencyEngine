"""K0 shadow layer (A42; research 58's K0 via the research 59 seams):
task descriptors, the graph substrate, and the shadow recorder.

From this phase on, every real dispatch — chores, jobs, swaps, gateway
calls — is recorded as a compact JSONL trace ALONGSIDE what the shadow
scheduler WOULD have done (greedy cost-aware earliest-finish over the
registry's measured tables). The deltas are the campaign's Borg-style
evidence; K2's go-live gate replays them.

Zero behavior change, by construction: the recorder is a no-op until
enabled, every failure inside it is swallowed, nothing on any dispatch
path ever reads it, and `[scheduler] shadow = false` turns it off — the
degrade-to-static law. Tasks declare inputs/outputs by ID (the graph
substrate): internal edges pass ids, never payloads.
"""

from __future__ import annotations

import contextlib
import json
import statistics
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tee.kernel.machine import ENGINES

DEFAULT_CAP_MB = 50.0


@dataclass
class TaskDescriptor:
    """One unit of work, declared by id (research 58 piece 1)."""

    id: str
    kind: str  # chore | job | swap | gateway
    qos: str = "standard"
    engine: str | None = None  # who actually ran it (None = undecided/client)
    verifier: str | None = None
    inputs: list[str] = field(default_factory=list)  # ids/pointers, never payloads
    outputs: list[str] = field(default_factory=list)

    def to_line(self) -> dict[str, Any]:
        line: dict[str, Any] = {"id": self.id, "kind": self.kind, "qos": self.qos}
        for key in ("engine", "verifier"):
            value = getattr(self, key)
            if value:
                line[key] = value
        if self.inputs:
            line["in"] = self.inputs
        if self.outputs:
            line["out"] = self.outputs
        return line


def _median(pair: Any) -> float | None:
    try:
        return round(statistics.median([float(x) for x in pair]), 2)
    except (TypeError, ValueError):
        return None


def greedy_choice(kind: str, *, engine: str | None = None, resident: str | None = None):
    """What the shadow scheduler WOULD do: greedy earliest-finish from the
    measured tables. Computed, never applied (K2 flips that, replay-gated)."""
    if kind == "chore":
        best = None
        for name, spec in ENGINES.items():
            if spec["kind"] != "llm":
                continue
            latency = _median(spec["cost"].get("latency_s")) or 0.0
            finish = latency + (0.0 if name == resident else float(spec.get("eta_s", 0)))
            if best is None or finish < best[1]:
                best = (name, finish)
        if best is None:  # pragma: no cover - registry always has llm rows
            return {"engine": None, "estimate_s": None, "reason": "no llm rows"}
        return {
            "engine": best[0],
            "estimate_s": round(best[1], 2),
            "reason": f"greedy earliest-finish, resident={resident or 'none'}",
        }
    if kind in ("job", "swap") and engine in ENGINES:
        spec = ENGINES[engine]
        estimate = _median(spec["cost"].get("wall_s")) or float(spec.get("eta_s", 0) or 0)
        return {"engine": engine, "estimate_s": estimate, "reason": "single-engine task"}
    return {"engine": engine, "estimate_s": None, "reason": "no table row"}


class ShadowRecorder:
    """Appends one compact JSONL line per dispatch. Never raises."""

    def __init__(self) -> None:
        self._dir: Path | None = None
        self._lock = threading.Lock()
        self.last_overhead_us: float | None = None

    @property
    def enabled(self) -> bool:
        return self._dir is not None

    def enable(self, directory: Path | str, cap_mb: float = DEFAULT_CAP_MB) -> None:
        with contextlib.suppress(Exception):
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            self._dir = path
            self._sweep(cap_mb)

    def disable(self) -> None:
        self._dir = None

    def record(self, task: TaskDescriptor, actual: dict[str, Any]) -> None:
        """actual: outcome + wall_s (+ anything compact the seam knows)."""
        if self._dir is None:
            return
        started = time.perf_counter()
        with contextlib.suppress(Exception):
            resident = actual.pop("_resident", None)
            shadow = greedy_choice(task.kind, engine=task.engine, resident=resident)
            delta: dict[str, Any] = {"agrees": shadow.get("engine") == task.engine}
            wall = actual.get("wall_s")
            if isinstance(wall, int | float) and shadow.get("estimate_s") is not None:
                delta["est_minus_actual_s"] = round(shadow["estimate_s"] - wall, 2)
            line = {
                "ts": round(time.time(), 2),
                "task": task.to_line(),
                "actual": actual,
                "shadow": shadow,
                "delta": delta,
            }
            day_file = self._dir / f"traces-{time.strftime('%Y%m%d')}.jsonl"
            payload = json.dumps(line, separators=(",", ":")) + "\n"
            with self._lock, day_file.open("a", encoding="utf-8") as fh:
                fh.write(payload)
            self.last_overhead_us = (time.perf_counter() - started) * 1e6

    def recent(self, n: int = 5) -> list[dict[str, Any]]:
        if self._dir is None:
            return []
        lines: list[dict[str, Any]] = []
        with contextlib.suppress(Exception):
            files = sorted(self._dir.glob("traces-*.jsonl"))
            if files:
                for raw in files[-1].read_text().splitlines()[-n:]:
                    with contextlib.suppress(json.JSONDecodeError):
                        lines.append(json.loads(raw))
        return lines

    def _sweep(self, cap_mb: float) -> None:
        files = sorted(self._dir.glob("traces-*.jsonl")) if self._dir else []
        total = sum(f.stat().st_size for f in files)
        for f in files:  # oldest first, keep today's tail
            if total <= cap_mb * 1e6:
                break
            total -= f.stat().st_size
            f.unlink(missing_ok=True)


RECORDER = ShadowRecorder()


def record(task: TaskDescriptor, actual: dict[str, Any]) -> None:
    RECORDER.record(task, actual)


def replay(trace_dirs: list[Path | str]) -> dict[str, Any]:
    """K2's go-live gate, the Borg/Firmament method over OUR traces: replay
    every recorded chore dispatch and measure agreement between what ran
    and what greedy WOULD have placed. The gate (declared here, checked by
    the caller): agreement >= 0.8, OR every disagreement is one where
    greedy's estimate beats the recorded actual (improvement, est-labeled).
    Estimate error (MAE) is published either way - the policy's honesty."""
    lines: list[dict[str, Any]] = []
    for directory in trace_dirs:
        for path in sorted(Path(directory).glob("traces-*.jsonl")):
            for raw in path.read_text(errors="replace").splitlines():
                with contextlib.suppress(json.JSONDecodeError):
                    lines.append(json.loads(raw))
    chore_lines = [ln for ln in lines if ln.get("task", {}).get("kind") == "chore"]
    agreements = 0
    errors: list[float] = []
    disagreements: list[dict[str, Any]] = []
    improvements = 0
    for line in chore_lines:
        delta = line.get("delta", {})
        if delta.get("agrees"):
            agreements += 1
        else:
            actual_wall = line.get("actual", {}).get("wall_s")
            estimate = line.get("shadow", {}).get("estimate_s")
            better = (
                isinstance(actual_wall, int | float)
                and isinstance(estimate, int | float)
                and estimate < actual_wall
            )
            improvements += 1 if better else 0
            disagreements.append(
                {
                    "task": line.get("task", {}).get("id"),
                    "ran": line.get("task", {}).get("engine"),
                    "greedy": line.get("shadow", {}).get("engine"),
                    "actual_s": actual_wall,
                    "estimate_s": estimate,
                    "greedy_better_by_estimate": better,
                }
            )
        est_gap = delta.get("est_minus_actual_s")
        if isinstance(est_gap, int | float):
            errors.append(abs(est_gap))
    total = len(chore_lines)
    agreement_rate = round(agreements / total, 3) if total else None
    passes = bool(total) and (
        (agreement_rate or 0) >= 0.8 or (bool(disagreements) and improvements == len(disagreements))
    )
    return {
        "traces": len(lines),
        "chore_dispatches": total,
        "agreement_rate": agreement_rate,
        "estimate_mae_s": round(sum(errors) / len(errors), 2) if errors else None,
        "disagreements": disagreements[:10],
        "gate": "agreement >= 0.8 OR every disagreement greedy-better-by-estimate",
        "passes": passes,
    }
