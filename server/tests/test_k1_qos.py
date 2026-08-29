"""K1 (A42): QoS as law — interactive never behind batch, aging against
starvation, admission control against the ledger — and the off-switch
restores plain FIFO exactly (the degrade-to-static promise). The meter's
queue_age_s column fills once the app installs the probe."""

from __future__ import annotations

import threading
import time

import pytest

from tee.kernel.errors import TeeError
from tee.kernel.jobs import JobManager
from tee.kernel.machine import MachineLedger


def _make(qos: bool, aging_s: float | None = None) -> tuple[JobManager, list[str], object]:
    jm = JobManager(workers=1)
    jm.configure(qos=qos, aging_s=aging_s)
    order: list[str] = []
    gate = threading.Event()

    def blocker():
        gate.wait(5)
        return {}

    jm.submit("blocker", blocker, qos="standard")
    time.sleep(0.05)  # the worker picks the blocker up
    return jm, order, gate


def _runner(order: list[str], name: str):
    def fn():
        order.append(name)
        return {}

    return fn


def _wait_for(order: list[str], count: int, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline and len(order) < count:
        time.sleep(0.01)


def test_interactive_never_behind_batch():
    jm, order, gate = _make(qos=True)
    for i in range(3):
        jm.submit(f"batch{i}", _runner(order, f"batch{i}"), qos="batch")
    jm.submit("chat", _runner(order, "interactive"), qos="interactive")
    gate.set()
    _wait_for(order, 4)
    assert order[0] == "interactive", order
    jm.shutdown()


def test_off_switch_restores_fifo():
    jm, order, gate = _make(qos=False)
    for i in range(2):
        jm.submit(f"batch{i}", _runner(order, f"batch{i}"), qos="batch")
    jm.submit("chat", _runner(order, "interactive"), qos="interactive")
    gate.set()
    _wait_for(order, 3)
    assert order == ["batch0", "batch1", "interactive"], order
    jm.shutdown()


def test_aging_prevents_starvation():
    jm, order, gate = _make(qos=True, aging_s=0.05)
    jm.submit("old-batch", _runner(order, "old-batch"), qos="batch")
    time.sleep(0.2)  # ages past interactive rank
    jm.submit("chat", _runner(order, "interactive"), qos="interactive")
    gate.set()
    _wait_for(order, 2)
    assert order[0] == "old-batch", order
    jm.shutdown()


def test_admission_refuses_never_placeable_work():
    jm = JobManager(workers=1)
    small_machine = MachineLedger(total_gb=20)  # 4 GB after reserve
    jm.configure(machine=small_machine, qos=True)
    with pytest.raises(TeeError) as excinfo:
        jm.submit("doomed", lambda: {}, qos="batch", engine="reconstruct-odm")
    assert excinfo.value.code == "job_refused_admission"
    assert "never" in excinfo.value.message
    # unknown engines and qos-off both admit (today's behavior)
    jm.submit("fine", lambda: {}, qos="batch", engine="not-in-registry")
    jm.configure(qos=False)
    jm.submit("legacy", lambda: {}, qos="batch", engine="reconstruct-odm")
    jm.shutdown()


def test_cancel_while_queued_still_skips_under_cv():
    jm, order, gate = _make(qos=True)
    victim = jm.submit("victim", _runner(order, "victim"), qos="batch")
    jm.submit("keeper", _runner(order, "keeper"), qos="batch")
    jm.cancel(victim)
    gate.set()
    _wait_for(order, 1)
    time.sleep(0.1)
    assert order == ["keeper"]
    assert jm.status(victim)["state"] == "cancelled"
    jm.shutdown()


def test_queue_ages_fill_the_meter_column(tmp_path):
    from tee.app import TeeApp
    from tee.kernel.adapter import FakeAdapter

    project = tmp_path / "proj"
    project.mkdir()
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    gate = threading.Event()
    app.jobs.submit("hold", lambda: (gate.wait(5), {})[1], qos="batch")
    time.sleep(0.05)
    app.jobs.submit("queued", lambda: {}, qos="batch")
    block = app.machine.meter_block()
    column = block["scheduler"]["queue_age_s"]
    assert isinstance(column, dict) and column["queued"] >= 1
    gate.set()
    app.shutdown()
