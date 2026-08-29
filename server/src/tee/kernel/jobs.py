"""Async job manager (principle P8).

Long DCC operations (bakes, renders, imports) never block a tool call past
client timeouts: they are submitted here, the tool returns a job id at once,
and the model polls tee_job - a response of a few dozen tokens.

Workers are daemon threads (not a ThreadPoolExecutor): a stuck DCC call must
never block interpreter exit, and Python's executor threads are non-daemon
and joined at shutdown.
"""

from __future__ import annotations

import queue
import threading
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from tee.kernel.errors import TeeError


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
        self._queue: queue.Queue[_Job | None] = queue.Queue()
        self._fns: dict[str, Callable[[], dict[str, Any]]] = {}
        self._jobs: dict[str, _Job] = {}
        self._lock = threading.Lock()
        self._counter = 0
        self._keep_finished = keep_finished
        self._stopping = False
        self._threads = [
            threading.Thread(target=self._worker, name=f"tee-job-{i}", daemon=True)
            for i in range(workers)
        ]
        for thread in self._threads:
            thread.start()

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
            self._prune_locked()
        self._queue.put(job)
        return job.id

    def _worker(self) -> None:
        while True:
            job = self._queue.get()
            if job is None:
                return
            with self._lock:
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
                with self._lock:
                    job.finished_at = time.time()
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
        with self._lock:
            self._stopping = True
        for _ in self._threads:
            self._queue.put(None)
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
