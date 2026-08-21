"""Async job manager (principle P8).

Long DCC operations (bakes, renders, imports) never block a tool call past
client timeouts: they are submitted here, the tool returns a job id at once,
and the model polls tee_job_status - a response of a few dozen tokens.
"""

from __future__ import annotations

import threading
import time
import traceback
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
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
    future: Future | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"job": self.id, "label": self.label, "state": self.state}
        if self.state in ("queued", "running"):
            payload["elapsed_s"] = round(time.time() - self.submitted_at, 1)
        if self.result is not None:
            payload["result"] = self.result
        if self.error is not None:
            payload["error"] = self.error
        return payload


class JobManager:
    def __init__(self, workers: int = 2, keep_finished: int = 50):
        self._executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="tee-job")
        self._jobs: dict[str, _Job] = {}
        self._lock = threading.Lock()
        self._counter = 0
        self._keep_finished = keep_finished

    def submit(self, label: str, fn: Callable[[], dict[str, Any]]) -> str:
        with self._lock:
            self._counter += 1
            job = _Job(
                id=f"job{self._counter}",
                label=label,
                state="queued",
                submitted_at=time.time(),
            )
            self._jobs[job.id] = job
            self._prune_locked()

        def run() -> None:
            with self._lock:
                if job.state == "cancelled":
                    return
                job.state = "running"
            try:
                result = fn()
                with self._lock:
                    if job.state != "cancelled":
                        job.state = "done"
                        job.result = result
            except TeeError as exc:
                with self._lock:
                    job.state = "error"
                    fix = f" Fix: {exc.fix}" if exc.fix else ""
                    job.error = f"{exc.code}: {exc.message}{fix}"
            except Exception as exc:
                with self._lock:
                    job.state = "error"
                    job.error = _summarize_exception(exc)
            finally:
                with self._lock:
                    job.finished_at = time.time()

        job.future = self._executor.submit(run)
        return job.id

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
            if job.state == "queued":
                job.state = "cancelled"
                if job.future is not None:
                    job.future.cancel()
            elif job.state == "running":
                # Cooperative only: DCC-side operations decide their own
                # cancellation points; we mark intent.
                job.state = "cancelled"
            return job.to_payload()

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            return [j.to_payload() for j in self._jobs.values()]

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _prune_locked(self) -> None:
        finished = [j for j in self._jobs.values() if j.state in ("done", "error", "cancelled")]
        excess = len(finished) - self._keep_finished
        for job in finished[:excess]:
            del self._jobs[job.id]


def _summarize_exception(exc: Exception, limit: int = 300) -> str:
    last = traceback.format_exception_only(type(exc), exc)[-1].strip()
    return last[:limit]
