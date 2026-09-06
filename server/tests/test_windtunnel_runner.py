"""A72 P1: one solver process, owned end to end.

`tee_job cancel` used to be cooperative only; a cancelled two-hour
simpleFoam would have kept four cores busy. The runner kills the process
GROUP and the kernel's on_cancel hook is what invokes it - both are measured
here with a sleeping child: the pid is gone within two seconds, `run.json`
and `progress.json` say so, and a solver whose server died is found again
(`orphan_check`) by pid AND command line before any signal is sent.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from tee.kernel.jobs import JobManager
from tee.windtunnel import runner
from tee.windtunnel.runner import RunSpec, SolverRun

SLEEPER = [sys.executable, "-c", "import time, sys\nprint('Time = 1', flush=True)\ntime.sleep(30)"]


def _spec(tmp_path: Path, argv=None, **kw) -> RunSpec:
    base = {
        "run_id": "run_001",
        "case_id": "wt_test",
        "engine": "openfoam",
        "argv": argv or SLEEPER,
        "cwd": tmp_path / "run",
        "log_name": "log.simpleFoam",
        "timeout_s": 30.0,
    }
    base.update(kw)
    return RunSpec(**base)


def test_run_streams_a_log_and_writes_run_json_before_the_first_byte(tmp_path):
    run = SolverRun(_spec(tmp_path, argv=[sys.executable, "-c", "print('End')"]))
    res = run.run()
    assert res["rc"] == 0 and res["state"] == "done" and res["wall_s"] >= 0
    assert (tmp_path / "run" / "log.simpleFoam").read_text().strip() == "End"
    rj = runner.read_json(tmp_path / "run" / "run.json")
    assert rj["pid"] > 0 and rj["state"] == "done" and rj["argv"][0] == sys.executable
    prog = runner.read_json(tmp_path / "run" / "progress.json")
    assert prog["state"] == "done" and prog["rc"] == 0 and "wall_s" in prog


def test_a_failing_process_is_error_and_a_progress_parser_that_raises_never_kills_the_reader(
    tmp_path,
):
    def bad_parser(_cwd, _tail):
        raise RuntimeError("parser bug")

    run = SolverRun(
        _spec(tmp_path, argv=[sys.executable, "-c", "import sys; sys.exit(3)"]),
        progress_fn=bad_parser,
    )
    res = run.run()
    assert res["state"] == "error" and res["rc"] == 3
    assert "parser bug" in runner.read_json(tmp_path / "run" / "progress.json")["progress_error"]


def test_progress_fn_output_lands_in_progress_json(tmp_path):
    run = SolverRun(_spec(tmp_path), progress_fn=lambda _cwd, tail: {"iter": tail.count("Time =")})
    run.start()
    try:
        deadline = time.time() + 5
        while time.time() < deadline:
            prog = runner.read_json(run.progress_path) or {}
            if prog.get("iter") == 1:
                break
            time.sleep(0.1)
        assert prog.get("iter") == 1 and prog["state"] == "running" and prog["pid"] == run.proc.pid
    finally:
        run.terminate()
        run.wait()


def test_terminate_kills_the_process_group_within_two_seconds(tmp_path):
    """The child spawns its own grandchild; SIGTERM to the parent alone would
    strand it (mpirun and the OpenFOAM entry script both fork)."""
    child = (
        "import subprocess, sys, time\n"
        "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        "print('CHILD', p.pid, flush=True)\n"
        "time.sleep(60)\n"
    )
    run = SolverRun(_spec(tmp_path, argv=[sys.executable, "-c", child]))
    run.start()
    deadline = time.time() + 5
    grandchild = None
    while time.time() < deadline and grandchild is None:
        for line in (tmp_path / "run" / "log.simpleFoam").read_text().splitlines():
            if line.startswith("CHILD"):
                grandchild = int(line.split()[1])
        time.sleep(0.05)
    assert grandchild and runner.pid_alive(grandchild)
    t0 = time.time()
    assert run.terminate() is True
    rc = run.wait()
    assert time.time() - t0 < 2.0
    assert rc != 0 and run.state == "cancelled" and not runner.pid_alive(run.proc.pid)
    deadline = time.time() + 2
    while time.time() < deadline and runner.pid_alive(grandchild):
        time.sleep(0.05)
    assert not runner.pid_alive(grandchild)
    assert runner.read_json(tmp_path / "run" / "run.json")["state"] == "cancelled"


def test_timeout_terminates_and_says_so(tmp_path):
    run = SolverRun(_spec(tmp_path, timeout_s=0.5))
    res = run.run()
    assert res["state"] == "timeout" and not runner.pid_alive(run.proc.pid)


def test_orphan_check_matches_pid_and_command_line_before_any_signal(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    assert runner.orphan_check(run_dir) == {"known": False, "alive": False}
    # a live process whose command line names the run directory
    proc = subprocess.Popen(
        [sys.executable, "-c", f"import time; time.sleep(30)  # {run_dir}"], start_new_session=True
    )
    try:
        runner.atomic_write_json(
            run_dir / "run.json", {"pid": proc.pid, "argv": ["x", str(run_dir)], "state": "running"}
        )
        info = runner.orphan_check(run_dir)
        assert info["alive"] is True and info["pid_reused"] is False and info["pid"] == proc.pid
        killed = runner.kill_orphan(run_dir)
        assert killed["killed"] is True
        proc.wait(timeout=5)
        assert not runner.pid_alive(proc.pid)
        assert runner.read_json(run_dir / "run.json")["killed_as_orphan"] is True
        assert runner.read_json(run_dir / "progress.json")["state"] == "cancelled"
    finally:
        if proc.poll() is None:
            proc.kill()
    # the pid of a process that is not ours (this interpreter) with an argv that never named the run
    runner.atomic_write_json(
        run_dir / "run.json", {"pid": os.getpid(), "argv": ["something-else"], "state": "running"}
    )
    info = runner.orphan_check(run_dir)
    assert info["alive"] is False and info["pid_reused"] is True
    assert runner.kill_orphan(run_dir)["killed"] is False  # never signals a reused pid
    assert runner.pid_alive(os.getpid())


def test_tail_reads_only_the_last_bytes(tmp_path):
    p = tmp_path / "big.log"
    p.write_bytes(b"x" * 100_000 + b"\nlast line\n")
    tail = runner.tail_text(p, 64)
    assert tail.endswith("last line\n") and len(tail) == 64
    assert runner.tail_text(tmp_path / "missing.log") == ""


def test_registry_keys_runs_per_case_so_run_001_twice_is_two_runs(tmp_path):
    a = SolverRun(_spec(tmp_path, case_id="wt_a"))
    b = SolverRun(_spec(tmp_path, case_id="wt_b"))
    runner.RUNS.clear()
    runner.register(a)
    runner.register(b)
    assert len(runner.RUNS) == 2
    assert runner.live_run_for_case("wt_a") is None  # queued, not running
    a.state = "running"
    assert runner.live_run_for_case("wt_a") is a and runner.live_run_for_case("wt_b") is None
    runner.forget("wt_a", "run_001")
    assert runner.live_run_for_case("wt_a") is None and len(runner.RUNS) == 1
    runner.RUNS.clear()


def test_the_kernel_on_cancel_hook_kills_a_running_solver(tmp_path):
    """The twelve-line kernel change: `submit(..., on_cancel=)` is invoked
    once, outside the lock, for a RUNNING job - and only then."""
    jobs = JobManager(workers=2)
    started = threading.Event()
    run = SolverRun(_spec(tmp_path))
    calls: list[str] = []

    def worker():
        run.start()
        started.set()
        run.wait()
        return {"state": run.state}

    def on_cancel():
        calls.append("hook")
        run.terminate()

    try:
        job = jobs.submit("solve", worker, on_cancel=on_cancel)
        assert started.wait(5)
        t0 = time.time()
        status = jobs.cancel(job)
        assert status["state"] == "cancelled" and calls == ["hook"]
        deadline = time.time() + 5
        while time.time() < deadline and runner.pid_alive(run.proc.pid):
            time.sleep(0.05)
        assert not runner.pid_alive(run.proc.pid) and time.time() - t0 < 2.5
        # a queued job's hook is dropped, never called
        gate = threading.Event()
        blockers = [jobs.submit(f"b{i}", lambda: (gate.wait(5), {})[1]) for i in range(2)]
        queued = jobs.submit("q", lambda: {}, on_cancel=lambda: calls.append("queued-hook"))
        jobs.cancel(queued)
        gate.set()
        for b in blockers:
            deadline = time.time() + 5
            while time.time() < deadline and jobs.status(b)["state"] != "done":
                time.sleep(0.02)
        assert calls == ["hook"]
        # a hook that raises never breaks cancel
        started.clear()
        run2 = SolverRun(_spec(tmp_path, run_id="run_002"))

        def worker2():
            run2.start()
            started.set()
            run2.wait()
            return {}

        def bad_hook():
            raise RuntimeError("boom")

        job2 = jobs.submit("solve2", worker2, on_cancel=bad_hook)
        assert started.wait(5)
        assert jobs.cancel(job2)["state"] == "cancelled"
        run2.terminate()
        run2.wait()
    finally:
        if run.proc and run.proc.poll() is None:
            run.terminate()
        jobs.shutdown()


@pytest.mark.parametrize("reason", ["cancelled", "timeout"])
def test_terminate_reason_decides_the_state_word(tmp_path, reason):
    run = SolverRun(_spec(tmp_path, run_id=f"run_{reason}"))
    run.start()
    run.terminate(reason=reason)
    run.wait()
    assert run.state == ("cancelled" if reason == "cancelled" else "error")
