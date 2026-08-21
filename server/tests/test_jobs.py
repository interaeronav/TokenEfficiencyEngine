import threading
import time

import pytest

from tee.kernel.errors import TeeError
from tee.kernel.jobs import JobManager


@pytest.fixture()
def jobs():
    mgr = JobManager(workers=2)
    yield mgr
    mgr.shutdown()


def wait_for(jobs, job_id, state, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = jobs.status(job_id)
        if status["state"] == state:
            return status
        time.sleep(0.01)
    raise AssertionError(f"job {job_id} never reached {state}: {jobs.status(job_id)}")


def test_submit_and_finish(jobs):
    job_id = jobs.submit("quick", lambda: {"answer": 42})
    status = wait_for(jobs, job_id, "done")
    assert status["result"] == {"answer": 42}


def test_running_job_reports_elapsed(jobs):
    gate = threading.Event()
    job_id = jobs.submit("slow", lambda: (gate.wait(5), {"ok": True})[1])
    status = wait_for(jobs, job_id, "running")
    assert "elapsed_s" in status
    gate.set()
    wait_for(jobs, job_id, "done")


def test_tee_error_in_job_keeps_fix_hint(jobs):
    def boom():
        raise TeeError("bake_failed", "No fluid domain.", fix="Add a domain object first.")

    job_id = jobs.submit("bake", boom)
    status = wait_for(jobs, job_id, "error")
    assert "bake_failed" in status["error"]
    assert "Add a domain" in status["error"]


def test_unexpected_exception_is_summarized_not_traceback(jobs):
    def boom():
        raise RuntimeError("kaboom " * 200)

    job_id = jobs.submit("bad", boom)
    status = wait_for(jobs, job_id, "error")
    assert len(status["error"]) <= 300
    assert "Traceback" not in status["error"]


def test_cancel_queued_job(jobs):
    gate = threading.Event()
    # occupy both workers
    blockers = [jobs.submit(f"block{i}", lambda: (gate.wait(5), {})[1]) for i in range(2)]
    queued = jobs.submit("queued", lambda: {})
    status = jobs.cancel(queued)
    assert status["state"] == "cancelled"
    gate.set()
    for b in blockers:
        wait_for(jobs, b, "done")
    assert jobs.status(queued)["state"] == "cancelled"


def test_unknown_job_error(jobs):
    with pytest.raises(TeeError) as err:
        jobs.status("job999")
    assert err.value.code == "unknown_job"


def test_prune_does_not_evict_below_retention(jobs):
    # regression: negative-excess slice used to evict at half the cap
    mgr = JobManager(workers=2, keep_finished=10)
    try:
        ids = [mgr.submit(f"j{i}", lambda: {}) for i in range(8)]
        for job_id in ids:
            wait_for(mgr, job_id, "done")
        mgr.submit("trigger-prune", lambda: {})
        for job_id in ids:  # all 8 finished jobs must still be queryable
            assert mgr.status(job_id)["state"] == "done"
    finally:
        mgr.shutdown()


def test_cancelled_job_stays_cancelled_when_fn_raises(jobs):
    import threading as _threading

    entered = _threading.Event()
    proceed = _threading.Event()

    def fn():
        entered.set()
        proceed.wait(5)
        raise RuntimeError("late failure")

    job_id = jobs.submit("doomed", fn)
    entered.wait(5)
    jobs.cancel(job_id)
    proceed.set()
    deadline = time.time() + 5
    while time.time() < deadline and jobs.status(job_id).get("elapsed_s") is not None:
        time.sleep(0.01)
    assert jobs.status(job_id)["state"] == "cancelled"
    assert "error" not in jobs.status(job_id)


def test_shutdown_does_not_wait_for_running_jobs():
    gate = threading.Event()
    mgr = JobManager(workers=1)
    mgr.submit("stuck", lambda: (gate.wait(30), {})[1])
    start = time.time()
    mgr.shutdown()
    assert time.time() - start < 1.0  # returns immediately, daemon threads
    gate.set()
