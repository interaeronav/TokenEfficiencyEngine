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
