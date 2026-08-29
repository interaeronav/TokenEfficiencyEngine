"""Async job manager (principle P8).

Long DCC operations (bakes, renders, imports) never block a tool call past
client timeouts: they are submitted here, the tool returns a job id at once,
and the model polls tee_job - a response of a few dozen tokens.

Workers are daemon threads (not a ThreadPoolExecutor): a stuck DCC call must
never block interpreter exit, and Python's executor threads are non-daemon
and joined at shutdown.
"""

from __future__ import annotations

import threading
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from tee.kernel.errors import TeeError

# K1 (A42): QoS rank order - interactive never behind batch. LAW only when
# configured on; off = plain FIFO, today's behavior (degrade-to-static).
QOS_RANK = {"interactive": 0, "standard": 1, "batch": 2, "maintenance": 3}
DEFAULT_AGING_S = 120.0  # a queued job gains one rank per aged interval


@dataclass
class _Job:
    id: str
    label: str
    state: str  # queued | running | done | error | cancelled
    submitted_at: float
    finished_at: float | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    # QoS is a LABEL for now (A42 seam 3): interactive|standard|batch|maintenance.
    qos: str = "standard"
    # Registry engine name when the submitter knows it (shadow-trace food).
    engine: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"job": self.id, "label": self.label, "state": self.state}
        if self.qos != "standard":  # labels only where they differ - budget discipline
            payload["qos"] = self.qos
        if self.state in ("queued", "running"):
            payload["elapsed_s"] = round(time.time() - self.submitted_at, 1)
        if self.result is not None:
            payload["result"] = self.result
        if self.error is not None:
            payload["error"] = self.error
        return payload


class JobManager:
    def __init__(self, workers: int = 2, keep_finished: int = 50):
        self._pending: list[_Job] = []
        self._fns: dict[str, Callable[[], dict[str, Any]]] = {}
        self._jobs: dict[str, _Job] = {}
        self._lock = threading.Lock()
        self._cv = threading.Condition(self._lock)
        self._counter = 0
        self._keep_finished = keep_finished
        self._stopping = False
        # K1/K3 knobs, set by configure(); defaults = today's behavior
        self._qos_enabled = False
        self._aging_s = DEFAULT_AGING_S
        self._machine = None
        self._workers = workers
        self._max_pending_low = 8  # K3 backpressure cap for batch/maintenance
        self._threads = [
            threading.Thread(target=self._worker, name=f"tee-job-{i}", daemon=True)
            for i in range(workers)
        ]
        for thread in self._threads:
            thread.start()

    def configure(
        self,
        *,
        machine=None,
        qos: bool | None = None,
        aging_s: float | None = None,
        max_pending_low: int | None = None,
    ) -> None:
        """K1/K3 wiring: ledger admission, the qos law switch, aging, and
        the backpressure cap for low-priority pending work."""
        with self._lock:
            if machine is not None:
                self._machine = machine
            if qos is not None:
                self._qos_enabled = bool(qos)
            if aging_s is not None:
                self._aging_s = max(0.01, float(aging_s))
            if max_pending_low is not None:
                self._max_pending_low = max(1, int(max_pending_low))

    def queue_ages(self) -> dict[str, Any]:
        """The meter's queue_age_s column (K1 fills what R2 reserved)."""
        with self._lock:
            now = time.time()
            ages = [now - job.submitted_at for job in self._pending]
        return {"queued": len(ages), "max_s": round(max(ages), 1) if ages else 0.0}

    def submit(
        self,
        label: str,
        fn: Callable[[], dict[str, Any]],
        *,
        qos: str = "standard",
        engine: str | None = None,
    ) -> str:
        with self._lock:
            if self._stopping:
                raise TeeError("shutting_down", "The server is shutting down.")
            if self._qos_enabled and self._machine is not None and engine:
                # K1 admission control: never accept work the ledger can
                # never place - refuse at the door with the honest line.
                admitted, reason = self._machine.may_admit(engine)
                if not admitted:
                    raise TeeError(
                        "job_refused_admission",
                        f"Admission refused for '{label}': {reason}",
                        fix="Shrink the work or raise the machine; the queue "
                        "never holds doomed jobs.",
                    )
            if self._qos_enabled and QOS_RANK.get(qos, 1) >= 2:
                # K3 backpressure: bounded low-priority queue, refused loudly
                pending_low = sum(1 for j in self._pending if QOS_RANK.get(j.qos, 1) >= 2)
                if pending_low >= self._max_pending_low:
                    raise TeeError(
                        "job_backpressure",
                        f"{pending_low} {qos}-class jobs already queued "
                        f"(cap {self._max_pending_low}).",
                        fix="Wait for the queue to drain, or raise "
                        "[scheduler] max_pending_batch deliberately.",
                    )
            self._counter += 1
            job = _Job(
                id=f"job{self._counter}",
                label=label,
                state="queued",
                submitted_at=time.time(),
                qos=qos,
                engine=engine,
            )
            self._jobs[job.id] = job
            self._fns[job.id] = fn
            self._pending.append(job)
            self._prune_locked()
            self._cv.notify()
        return job.id

    def _select_locked(self) -> _Job | None:
        """K1 selection: rank by QoS with aging so batch never starves;
        K3 reservation: batch/maintenance never take the LAST worker (so
        an arriving interactive always finds a slot; with one worker the
        reservation is impossible and batch still runs). qos off = plain
        FIFO, exactly today's order."""
        if not self._pending:
            return None
        if not self._qos_enabled:
            return self._pending.pop(0)
        now = time.time()

        def key(job: _Job) -> tuple[int, float]:
            rank = QOS_RANK.get(job.qos, 1)
            aged = int((now - job.submitted_at) // self._aging_s)
            return (max(0, rank - aged), job.submitted_at)

        running_low = sum(
            1 for j in self._jobs.values() if j.state == "running" and QOS_RANK.get(j.qos, 1) >= 2
        )
        reserve = self._workers > 1 and running_low >= self._workers - 1
        for job in sorted(self._pending, key=key):
            if reserve and QOS_RANK.get(job.qos, 1) >= 2:
                continue  # the last free worker is reserved for interactive
            self._pending.remove(job)
            return job
        return None

    def _worker(self) -> None:
        while True:
            with self._cv:
                job = None
                while not self._stopping:
                    job = self._select_locked()
                    if job is not None:
                        break
                    # nothing selectable (empty, or reserved for interactive):
                    # sleep until a submit or a completion wakes us
                    self._cv.wait(timeout=1.0)
                if job is None:
                    return  # stopping with nothing selectable
                fn = self._fns.pop(job.id, None)
                if job.state != "queued" or fn is None:
                    continue  # cancelled while queued
                job.state = "running"
            run_started = time.time()
            try:
                result = fn()
                with self._lock:
                    if job.state == "running":
                        job.state = "done"
                        job.result = result
            except TeeError as exc:
                fix = f" Fix: {exc.fix}" if exc.fix else ""
                with self._lock:
                    if job.state == "running":  # a cancel wins over a late error
                        job.state = "error"
                        job.error = f"{exc.code}: {exc.message}{fix}"
            except Exception as exc:
                with self._lock:
                    if job.state == "running":
                        job.state = "error"
                        job.error = _summarize_exception(exc)
            finally:
                with self._cv:
                    job.finished_at = time.time()
                    self._cv.notify_all()  # a completion frees a reserved slot
                from tee.kernel import shadow

                shadow.record(
                    shadow.TaskDescriptor(id=job.id, kind="job", qos=job.qos, engine=job.engine),
                    {"outcome": job.state, "wall_s": round(job.finished_at - run_started, 1)},
                )

    def status(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                known = ", ".join(list(self._jobs)[-5:]) or "(none)"
                raise TeeError(
                    "unknown_job",
                    f"No job '{job_id}'.",
                    fix=f"Recent jobs: {known}.",
                )
            return job.to_payload()

    def cancel(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise TeeError("unknown_job", f"No job '{job_id}'.")
            if job.state in ("queued", "running"):
                # Queued: the worker will skip it. Running: cooperative only -
                # the DCC-side operation finishes but its result is dropped.
                job.state = "cancelled"
                self._fns.pop(job_id, None)
            return job.to_payload()

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            return [j.to_payload() for j in self._jobs.values()]

    def shutdown(self) -> None:
        with self._cv:
            self._stopping = True
            self._cv.notify_all()
        # daemon threads: no join - a stuck DCC call must not block exit

    def _prune_locked(self) -> None:
        finished = [j for j in self._jobs.values() if j.state in ("done", "error", "cancelled")]
        excess = len(finished) - self._keep_finished
        if excess > 0:
            for job in finished[:excess]:
                del self._jobs[job.id]
                self._fns.pop(job.id, None)


def _summarize_exception(exc: Exception, limit: int = 300) -> str:
    last = traceback.format_exception_only(type(exc), exc)[-1].strip()
    return last[:limit]
