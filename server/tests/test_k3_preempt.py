"""K3 (A42): worker reservation + backpressure. Batch never takes the
LAST worker, so an arriving interactive always finds a slot at once; a
single-worker pool still runs batch (no deadlock); the low-priority
queue is bounded with a loud refusal; and the off-switch restores
today's concurrency exactly."""

from __future__ import annotations

import threading
import time

import pytest

from tee.kernel.errors import TeeError
from tee.kernel.jobs import JobManager


def _held(gate: threading.Event, started: list[str], name: str):
    def fn():
        started.append(name)
        gate.wait(5)
        return {}

    return fn


def _wait_for(items: list[str], count: int, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline and len(items) < count:
        time.sleep(0.01)


def test_batch_never_takes_the_last_worker():
    jm = JobManager(workers=2)
    jm.configure(qos=True)
    started: list[str] = []
    gate = threading.Event()
    jm.submit("batch0", _held(gate, started, "batch0"), qos="batch")
    jm.submit("batch1", _held(gate, started, "batch1"), qos="batch")
    _wait_for(started, 1)
    time.sleep(0.2)
    assert started == ["batch0"]  # the second worker stays reserved
    done: list[str] = []
    jm.submit("chat", lambda: (done.append("chat"), {})[1], qos="interactive")
    _wait_for(done, 1)
    assert done == ["chat"]  # interactive found the reserved slot at once
    gate.set()
    _wait_for(started, 2)
    assert started == ["batch0", "batch1"]  # the freed slot serves batch again
    jm.shutdown()


def test_single_worker_still_runs_batch():
    jm = JobManager(workers=1)
    jm.configure(qos=True)
    done: list[str] = []
    jm.submit("batch", lambda: (done.append("batch"), {})[1], qos="batch")
    _wait_for(done, 1)
    assert done == ["batch"]  # reservation impossible with one worker - no deadlock
    jm.shutdown()


def test_backpressure_bounds_the_low_priority_queue():
    jm = JobManager(workers=1)
    jm.configure(qos=True, max_pending_low=2)
    gate = threading.Event()
    started: list[str] = []
    jm.submit("hold", _held(gate, started, "hold"), qos="standard")
    _wait_for(started, 1)
    jm.submit("b0", lambda: {}, qos="batch")
    jm.submit("b1", lambda: {}, qos="batch")
    with pytest.raises(TeeError) as excinfo:
        jm.submit("b2", lambda: {}, qos="batch")
    assert excinfo.value.code == "job_backpressure"
    assert "max_pending_batch" in excinfo.value.fix
    jm.submit("chat", lambda: {}, qos="interactive")  # interactive unaffected
    gate.set()
    jm.shutdown()


def test_off_switch_restores_todays_concurrency():
    jm = JobManager(workers=2)
    jm.configure(qos=False)
    started: list[str] = []
    gate = threading.Event()
    jm.submit("batch0", _held(gate, started, "batch0"), qos="batch")
    jm.submit("batch1", _held(gate, started, "batch1"), qos="batch")
    _wait_for(started, 2)
    assert sorted(started) == ["batch0", "batch1"]  # both workers run batch
    gate.set()
    jm.shutdown()
